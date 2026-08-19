#!/usr/bin/env python3
"""Cliente HTTP para la Admin API de Tienda Nube / Nuvemshop.

Solo biblioteca estándar (sin `requests`). Resuelve las cuatro cosas que la
API obliga a hacer bien y que a mano se hacen mal:

  1. Rate limit real (leaky bucket, 2 req/s por par tienda-app). El espaciado
     entre requests se persiste en un archivo temporal, así que también se
     respeta entre invocaciones sucesivas del script.
  2. Paginación correcta: Tienda Nube *clampea* `per_page` en silencio y
     devuelve **404** al pedir una página más allá de la última (no un array
     vacío). El corte es por "página más corta que la página 1" o por ese 404.
  3. Escritura segura: `--dry-run` imprime el request sin ejecutarlo y
     `--backup` guarda el estado actual del recurso antes de tocarlo (si el
     backup falla, la escritura se aborta).
  4. Errores traducidos a causas reales (402 = tienda o app impaga, 403 =
     feature no habilitada para el plan, 415 = falta Content-Type, ...).

Uso:
    python3 tn-api.py <METHOD> <PATH> [opciones]

Exit codes:
    0  OK
    1  error de la API (4xx/5xx tras reintentos, o backup imposible)
    2  error de uso (falta credencial, argumentos inválidos)

El token NUNCA se imprime completo: siempre enmascarado a los últimos 4
caracteres.
"""

import argparse
import hashlib
import json
import os
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib import error as urlerror
from urllib import parse as urlparse
from urllib import request as urlrequest

EXIT_OK = 0
EXIT_API = 1
EXIT_USAGE = 2

DEFAULT_BASE_URL = "https://api.tiendanube.com"
DEFAULT_API_VERSION = "2025-03"
DEFAULT_PER_PAGE = 100
MAX_PER_PAGE = 200
DEFAULT_MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30

WRITE_METHODS = ("POST", "PUT", "PATCH", "DELETE")
BODY_METHODS = ("POST", "PUT", "PATCH")
METHODS = ("GET",) + WRITE_METHODS

# Sufijos de acción: no son GET-eables, se backupea el recurso padre.
ACTION_SUFFIXES = ("cancel", "close", "open", "confirm")

# Espaciado mínimo entre requests: 2 req/s (drenaje del leaky bucket).
MIN_INTERVAL = 0.5
# Si quedan menos de estas requests en el bucket, esperar el reset.
REMAINING_FLOOR = 5
# Tope de sueño para no colgarse ante un header de reset absurdo.
MAX_SLEEP = 60.0

EPILOG = """\
Ejemplos:

  # leer un recurso
  python3 tn-api.py GET products/123

  # recorrer una colección entera (respeta el clamp de per_page y el 404 final)
  python3 tn-api.py GET products --paginate --param published=true --json

  # ver qué haría una escritura, sin ejecutarla
  python3 tn-api.py PUT products/123 --data '{"name":"Remera"}' --dry-run

  # escribir con red de seguridad (si el GET previo falla, no escribe)
  python3 tn-api.py PATCH products/123 --data-file cambio.json --backup bk.json

Credenciales (flag o variable de entorno):
  --store-id     TN_STORE_ID
  --token        TN_ACCESS_TOKEN
  --user-agent   TN_USER_AGENT     ej: "Innovate Group (dev@ejemplo.com)"

El User-Agent es obligatorio: sin ese header la API responde 400.

Notas:
  * El espaciado de 2 req/s se guarda en un archivo temporal por (base_url,
    store_id) para que también aplique entre corridas seguidas del script.
    Se puede desactivar con TN_THROTTLE_STATE=off (no recomendado).
  * --backup hace un GET del mismo path antes de escribir. Si el path termina
    en /cancel, /close, /open o /confirm, backupea el recurso padre. En un
    POST a una colección, el backup guarda la primera página de esa colección.
  * --dry-run solo aplica a POST/PUT/PATCH/DELETE; en GET se ignora con aviso.
"""


class UsageError(Exception):
    """Error de uso: argumentos o credenciales."""


class ApiError(Exception):
    """Respuesta de error de la API, ya traducida a lenguaje accionable."""

    def __init__(self, status, url, payload, raw_text):
        self.status = status
        self.url = url
        self.payload = payload
        self.raw_text = raw_text
        super().__init__(explain_status(status, payload, raw_text))


# --------------------------------------------------------------------------
# Utilidades
# --------------------------------------------------------------------------

def mask_token(token):
    """Devuelve el token enmascarado; nunca se imprime completo."""
    if not token:
        return "(sin token)"
    tail = token[-4:] if len(token) > 4 else ""
    return "****" + tail


def warn(msg):
    print("aviso: " + msg, file=sys.stderr)


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def parse_int_header(headers, name):
    if headers is None:
        return None
    raw = headers.get(name)
    if raw is None:
        return None
    try:
        return int(str(raw).strip())
    except (TypeError, ValueError):
        return None


def extract_items(payload):
    """Devuelve la lista de ítems de una respuesta de colección.

    Formatos contemplados: array plano, `{"results": [...]}` y el envelope
    v2 `{"<recurso>": {"results": [...]}}` (por ejemplo `pages`).
    Si no hay lista reconocible, devuelve None.
    """
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        results = payload.get("results")
        if isinstance(results, list):
            return results
        for value in payload.values():
            if isinstance(value, dict) and isinstance(value.get("results"), list):
                return value["results"]
    return None


def explain_status(status, payload, raw_text):
    """Traduce un código HTTP a una causa concreta de la API de Tienda Nube."""
    causas = {
        400: ("Bad Request — falta el header User-Agent o el JSON del body es "
              "inválido."),
        401: ("Unauthorized — el access token es inválido, fue revocado o la "
              "app se desinstaló de la tienda."),
        402: ("Payment Required — la tienda o la app están impagas: la API "
              "está SUSPENDIDA y devuelve 402 en todos los endpoints hasta "
              "regularizar el pago. No es un problema del request."),
        403: ("Forbidden — la operación no está habilitada para esta tienda: "
              "falta el scope en la app, o la feature no está en el plan "
              "(verificá `features` en GET /store)."),
        404: ("Not Found — no existe el recurso, o la ruta/versión de API es "
              "incorrecta. Al paginar, un 404 significa fin de la colección."),
        409: ("Conflict — el recurso está en un estado que no admite esta "
              "operación, o ya existe un recurso equivalente."),
        415: ("Unsupported Media Type — falta el header "
              "'Content-Type: application/json; charset=utf-8'."),
        422: "Unprocessable Entity — la API rechazó los datos enviados.",
        429: ("Too Many Requests — se superó el rate limit (2 req/s por par "
              "tienda-app, ×10 en planes Next/Evolution) y se agotaron los "
              "reintentos. Las requests excedidas se pierden, no se encolan."),
    }
    if status in causas:
        base = causas[status]
    elif 500 <= status < 600:
        base = ("Error del lado de Tienda Nube (%d). Se agotaron los "
                "reintentos; reintentar más tarde." % status)
    else:
        base = "La API respondió %d." % status

    detalle = format_error_payload(payload, raw_text)
    return "HTTP %d — %s%s" % (status, base, detalle)


def format_error_payload(payload, raw_text):
    """Formatea el cuerpo del error en sus dos formatos posibles.

    Moderno: {"code": .., "message": .., "description": ..}
    Legacy por campo: {"campo": ["mensaje", ...]}
    """
    if payload is None:
        texto = (raw_text or "").strip()
        return "\n  respuesta: " + texto[:500] if texto else ""

    lineas = []
    if isinstance(payload, dict):
        for clave in ("code", "message", "description", "error"):
            if clave in payload and not isinstance(payload[clave], (dict, list)):
                lineas.append("  %s: %s" % (clave, payload[clave]))
        campos = []
        for clave, valor in payload.items():
            if clave in ("code", "message", "description", "error"):
                continue
            if isinstance(valor, list):
                campos.append("  %s: %s" % (clave, "; ".join(str(v) for v in valor)))
            elif isinstance(valor, str):
                campos.append("  %s: %s" % (clave, valor))
        if campos:
            lineas.append("  errores por campo:")
            lineas.extend("  " + c for c in campos)
    if not lineas:
        lineas.append("  " + json.dumps(payload, ensure_ascii=False)[:500])
    return "\n" + "\n".join(lineas)


# --------------------------------------------------------------------------
# Rate limit
# --------------------------------------------------------------------------

class Throttle:
    """Espaciador de requests a 2 por segundo.

    Guarda el timestamp de la última request en un archivo temporal para que
    el límite también se respete entre invocaciones sucesivas del script (el
    bucket de la API es por par tienda-app, no por proceso). El nombre del
    archivo es un hash: no expone el store_id.
    """

    def __init__(self, key, min_interval=MIN_INTERVAL):
        self.min_interval = min_interval
        self.last = 0.0
        self.path = None
        if os.environ.get("TN_THROTTLE_STATE", "").lower() not in ("off", "0", "no"):
            digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
            self.path = Path(tempfile.gettempdir()) / ("tn-api-throttle-%s.json" % digest)

    def _read_last(self):
        if self.path is None:
            return self.last
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return max(float(data.get("last", 0.0)), self.last)
        except (OSError, ValueError, TypeError):
            return self.last

    def _write_last(self, value):
        self.last = value
        if self.path is None:
            return
        try:
            self.path.write_text(json.dumps({"last": value}), encoding="utf-8")
        except OSError:
            pass

    def wait(self):
        last = self._read_last()
        espera = self.min_interval - (time.time() - last)
        if espera > 0:
            time.sleep(min(espera, MAX_SLEEP))
        self._write_last(time.time())

    def sleep(self, segundos, motivo):
        segundos = max(0.0, min(float(segundos), MAX_SLEEP))
        if segundos > 0:
            warn("esperando %.2fs (%s)" % (segundos, motivo))
            time.sleep(segundos)
        self._write_last(time.time())


# --------------------------------------------------------------------------
# Cliente
# --------------------------------------------------------------------------

class Response:
    def __init__(self, status, headers, payload, raw_text, url):
        self.status = status
        self.headers = headers
        self.payload = payload
        self.raw_text = raw_text
        self.url = url


class Client:
    def __init__(self, base_url, api_version, store_id, token, user_agent,
                 max_retries=DEFAULT_MAX_RETRIES, timeout=DEFAULT_TIMEOUT):
        self.base_url = base_url.rstrip("/")
        self.api_version = api_version.strip("/")
        self.store_id = str(store_id)
        self.token = token
        self.user_agent = user_agent
        self.max_retries = max_retries
        self.timeout = timeout
        # La doc oficial muestra 'Authorization: Bearer' en las páginas nuevas
        # y 'Authentication: bearer' en las viejas. Se manda el segundo (es el
        # que funciona en los proyectos propios) y ante un 401 se reintenta una
        # vez con el primero.
        self.auth_header = "Authentication"
        self.auth_prefix = "bearer"
        self.auth_fallback_usado = False
        self.throttle = Throttle("%s|%s|%s" % (self.base_url, self.api_version, self.store_id))

    # -- construcción ------------------------------------------------------

    def build_url(self, path, params=None):
        path = path.lstrip("/")
        url = "%s/%s/%s/%s" % (self.base_url, self.api_version, self.store_id, path)
        if params:
            url += "?" + urlparse.urlencode(params, doseq=True)
        return url

    def build_headers(self, method, con_body):
        headers = {
            self.auth_header: "%s %s" % (self.auth_prefix, self.token),
            "User-Agent": self.user_agent,
            "Accept": "application/json",
        }
        if method in BODY_METHODS or con_body:
            headers["Content-Type"] = "application/json; charset=utf-8"
        return headers

    def masked_headers(self, method, con_body):
        headers = self.build_headers(method, con_body)
        headers[self.auth_header] = "%s %s" % (self.auth_prefix, mask_token(self.token))
        return headers

    # -- ejecución ---------------------------------------------------------

    def _perform(self, method, url, body_bytes):
        """Una sola request. Devuelve (status, headers, texto) o lanza URLError."""
        headers = self.build_headers(method, body_bytes is not None)
        data = body_bytes
        if data is None and method in BODY_METHODS:
            # PUT/POST sin body: Content-Length 0 explícito.
            data = b""
        req = urlrequest.Request(url, data=data, headers=headers, method=method)
        try:
            with urlrequest.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read()
                return resp.getcode(), resp.headers, raw.decode("utf-8", "replace")
        except urlerror.HTTPError as exc:
            raw = exc.read()
            return exc.code, exc.headers, raw.decode("utf-8", "replace")

    def _respect_remaining(self, headers):
        """Si el bucket está por vaciarse, esperar el reset (viene en ms)."""
        remaining = parse_int_header(headers, "x-rate-limit-remaining")
        if remaining is not None and remaining < REMAINING_FLOOR:
            reset_ms = parse_int_header(headers, "x-rate-limit-reset") or 1000
            self.throttle.sleep(reset_ms / 1000.0,
                                "quedan %d requests en el bucket" % remaining)

    def request(self, method, path, params=None, body_bytes=None, url=None):
        """Request con rate limit, reintentos y traducción de errores."""
        url = url or self.build_url(path, params)
        intento = 0
        while True:
            self.throttle.wait()
            try:
                status, headers, texto = self._perform(method, url, body_bytes)
            except urlerror.URLError as exc:
                if intento < self.max_retries:
                    espera = 2 ** intento
                    warn("error de red (%s); reintento %d/%d en %ds"
                         % (exc.reason, intento + 1, self.max_retries, espera))
                    self.throttle.sleep(espera, "reintento de red")
                    intento += 1
                    continue
                raise ApiError(0, url, None, "error de red: %s" % exc.reason)

            if status != 429:
                # En un 429 la espera la maneja el propio reintento.
                self._respect_remaining(headers)
            payload = None
            if texto:
                try:
                    payload = json.loads(texto)
                except ValueError:
                    payload = None

            if status == 401 and not self.auth_fallback_usado:
                self.auth_fallback_usado = True
                self.auth_header = "Authorization"
                self.auth_prefix = "Bearer"
                warn("401 con 'Authentication: bearer'; reintentando una vez "
                     "con 'Authorization: Bearer'")
                continue

            if status == 429:
                if intento < self.max_retries:
                    reset_ms = parse_int_header(headers, "x-rate-limit-reset") or 1000
                    self.throttle.sleep(reset_ms / 1000.0, "429 rate limit")
                    intento += 1
                    continue
                raise ApiError(status, url, payload, texto)

            if 500 <= status < 600:
                if intento < self.max_retries:
                    espera = 2 ** intento
                    self.throttle.sleep(espera, "HTTP %d, backoff" % status)
                    intento += 1
                    continue
                raise ApiError(status, url, payload, texto)

            if status >= 400:
                raise ApiError(status, url, payload, texto)

            return Response(status, headers, payload, texto, url)

    # -- paginación --------------------------------------------------------

    def paginate(self, path, params=None, per_page=DEFAULT_PER_PAGE):
        """Recorre la colección entera y devuelve (items, paginas_leidas).

        Corte: una página con menos ítems que la PRIMERA (la API clampea
        `per_page` sin avisar, así que la referencia es el tamaño real de la
        página 1, no el `per_page` pedido) o un 404 (fin de la colección).
        """
        items = []
        base_params = dict(params or {})
        base_params.pop("page", None)
        base_params["per_page"] = per_page
        tam_pagina_1 = None
        pagina = 1
        while True:
            consulta = dict(base_params)
            consulta["page"] = pagina
            try:
                resp = self.request("GET", path, params=consulta)
            except ApiError as exc:
                if exc.status == 404 and pagina > 1:
                    # TN devuelve 404 al pedir una página más allá de la
                    # última: no es un error, es el fin de la colección.
                    break
                raise
            actuales = extract_items(resp.payload)
            if actuales is None:
                raise UsageError(
                    "la respuesta de %s no es una colección paginable "
                    "(no es un array ni trae 'results')" % resp.url)
            items.extend(actuales)
            if tam_pagina_1 is None:
                tam_pagina_1 = len(actuales)
                if tam_pagina_1 == 0:
                    break
            if len(actuales) < tam_pagina_1:
                break
            pagina += 1
        return items, pagina


# --------------------------------------------------------------------------
# Backup
# --------------------------------------------------------------------------

def backup_path_for(path):
    """Path GET-eable para backupear una escritura.

    Los sufijos de acción (/cancel, /close, /open, /confirm) no se pueden
    GETear: se backupea el recurso padre.
    """
    limpio = path.strip("/")
    partes = limpio.split("/")
    if partes and partes[-1].lower() in ACTION_SUFFIXES:
        partes = partes[:-1]
    return "/".join(partes)


def hacer_backup(client, destino, method, url_escritura, path):
    """GET del estado actual antes de escribir. Devuelve True si se guardó.

    Si el GET falla, la escritura NO debe ejecutarse: la API no tiene deshacer
    y el backup es la única forma de revertir.
    """
    path_get = backup_path_for(path)
    resp = client.request("GET", path_get)
    contenido = {
        "fetched_at": now_iso(),
        "method": method,
        "url": url_escritura,
        "source_url": resp.url,
        "body": resp.payload if resp.payload is not None else resp.raw_text,
    }
    destino_path = Path(destino)
    if destino_path.parent and str(destino_path.parent) not in ("", "."):
        destino_path.parent.mkdir(parents=True, exist_ok=True)
    destino_path.write_text(
        json.dumps(contenido, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return resp


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def parse_args(argv):
    p = argparse.ArgumentParser(
        prog="tn-api.py",
        description=("Cliente de la Admin API de Tienda Nube/Nuvemshop con "
                     "rate limit, paginación correcta, dry-run y backup."),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=EPILOG)
    p.add_argument("method", metavar="METHOD",
                   help="GET | POST | PUT | PATCH | DELETE")
    p.add_argument("path", metavar="PATH",
                   help="ruta relativa al store, sin barra inicial: "
                        "'products', 'products/123/variants'")
    p.add_argument("--store-id", default=os.environ.get("TN_STORE_ID"),
                   help="id de la tienda (o env TN_STORE_ID)")
    p.add_argument("--token", default=os.environ.get("TN_ACCESS_TOKEN"),
                   help="access token (o env TN_ACCESS_TOKEN)")
    p.add_argument("--user-agent", default=os.environ.get("TN_USER_AGENT"),
                   help="header User-Agent (o env TN_USER_AGENT); "
                        "obligatorio: sin él la API devuelve 400")
    p.add_argument("--base-url", default=os.environ.get("TN_BASE_URL", DEFAULT_BASE_URL),
                   help="default %s" % DEFAULT_BASE_URL)
    p.add_argument("--api-version", default=DEFAULT_API_VERSION,
                   help="default %s" % DEFAULT_API_VERSION)
    p.add_argument("--param", action="append", default=[], metavar="K=V",
                   help="parámetro de querystring; repetible")
    p.add_argument("--data", metavar="JSON", help="body inline")
    p.add_argument("--data-file", metavar="PATH",
                   help="body desde archivo (excluyente con --data)")
    p.add_argument("--paginate", action="store_true",
                   help="recorre todas las páginas y devuelve un array único")
    p.add_argument("--per-page", type=int, default=DEFAULT_PER_PAGE, metavar="N",
                   help="default %d (máx %d)" % (DEFAULT_PER_PAGE, MAX_PER_PAGE))
    p.add_argument("--dry-run", action="store_true",
                   help="no ejecuta escrituras: imprime el request que haría")
    p.add_argument("--backup", metavar="PATH",
                   help="antes de escribir, GET del recurso y guarda el estado actual")
    p.add_argument("--json", action="store_true", dest="json_out",
                   help="salida JSON pura (sin encabezados legibles)")
    p.add_argument("--max-retries", type=int, default=DEFAULT_MAX_RETRIES, metavar="N",
                   help="default %d (429 y 5xx)" % DEFAULT_MAX_RETRIES)
    return p.parse_args(argv)


def validar(args):
    """Valida argumentos y credenciales. Lanza UsageError."""
    args.method = args.method.upper()
    if args.method not in METHODS:
        raise UsageError("método inválido '%s'; usar uno de: %s"
                         % (args.method, ", ".join(METHODS)))
    if not args.store_id:
        raise UsageError("falta el store id: pasá --store-id o exportá TN_STORE_ID")
    if not args.token:
        raise UsageError("falta el access token: pasá --token o exportá TN_ACCESS_TOKEN")
    if not args.user_agent:
        raise UsageError("falta el User-Agent: pasá --user-agent o exportá "
                         "TN_USER_AGENT (sin ese header la API devuelve 400)")
    if args.data and args.data_file:
        raise UsageError("--data y --data-file son excluyentes")
    if args.paginate and args.method != "GET":
        raise UsageError("--paginate solo aplica a GET")
    if args.max_retries < 0:
        raise UsageError("--max-retries no puede ser negativo")
    if args.per_page < 1:
        raise UsageError("--per-page debe ser >= 1")
    if args.per_page > MAX_PER_PAGE:
        warn("--per-page %d supera el máximo de la API (%d); se usa %d"
             % (args.per_page, MAX_PER_PAGE, MAX_PER_PAGE))
        args.per_page = MAX_PER_PAGE
    if args.backup and args.method not in WRITE_METHODS:
        warn("--backup solo aplica a escrituras; se ignora en %s" % args.method)
        args.backup = None
    if args.dry_run and args.method not in WRITE_METHODS:
        warn("--dry-run solo aplica a escrituras (POST/PUT/PATCH/DELETE); "
             "se ignora en %s" % args.method)
        args.dry_run = False

    params = {}
    for item in args.param:
        if "=" not in item:
            raise UsageError("--param espera K=V, recibí '%s'" % item)
        clave, valor = item.split("=", 1)
        clave = clave.strip()
        if not clave:
            raise UsageError("--param con clave vacía: '%s'" % item)
        params[clave] = valor
    args.params = params

    crudo = None
    if args.data:
        crudo = args.data
    elif args.data_file:
        try:
            crudo = Path(args.data_file).read_text(encoding="utf-8")
        except OSError as exc:
            raise UsageError("no puedo leer --data-file %s: %s" % (args.data_file, exc))
    if crudo is not None:
        try:
            args.body = json.loads(crudo)
        except ValueError as exc:
            raise UsageError("el body no es JSON válido: %s" % exc)
    else:
        args.body = None
    return args


def imprimir_dry_run(client, args, url, body_bytes):
    headers = client.masked_headers(args.method, body_bytes is not None)
    if args.json_out:
        salida = {
            "dry_run": True,
            "method": args.method,
            "url": url,
            "headers": headers,
            "body": args.body,
            "backup": args.backup,
        }
        print(json.dumps(salida, ensure_ascii=False, indent=2))
        return
    print("DRY-RUN — no se ejecutó ninguna escritura")
    print("%s %s" % (args.method, url))
    print("Headers:")
    for clave in sorted(headers):
        print("  %s: %s" % (clave, headers[clave]))
    if args.body is not None:
        print("Body:")
        print(json.dumps(args.body, ensure_ascii=False, indent=2))
    else:
        print("Body: (vacío)")
    if args.backup:
        print("Backup: se guardaría el estado actual en %s" % args.backup)


def imprimir_respuesta(args, status, url, payload, raw_text, extra=None):
    if args.json_out:
        if payload is None:
            print(raw_text or "null")
        else:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    print("%s %s -> %s" % (args.method, url, status))
    if extra:
        print(extra)
    if payload is None:
        if raw_text:
            print(raw_text)
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def run(argv):
    args = validar(parse_args(argv))
    client = Client(
        base_url=args.base_url,
        api_version=args.api_version,
        store_id=args.store_id,
        token=args.token,
        user_agent=args.user_agent,
        max_retries=args.max_retries,
    )
    path = args.path.lstrip("/")
    body_bytes = None
    if args.body is not None:
        body_bytes = json.dumps(args.body, ensure_ascii=False).encode("utf-8")

    # --- dry-run: se corta antes de tocar la red ---
    if args.dry_run:
        url = client.build_url(path, args.params)
        imprimir_dry_run(client, args, url, body_bytes)
        return EXIT_OK

    # --- lectura paginada ---
    if args.paginate:
        items, paginas = client.paginate(path, params=args.params, per_page=args.per_page)
        if args.json_out:
            print(json.dumps(items, ensure_ascii=False, indent=2))
        else:
            print("GET %s (paginado) -> %d ítems en %d página(s)"
                  % (client.build_url(path), len(items), paginas))
            print(json.dumps(items, ensure_ascii=False, indent=2))
        return EXIT_OK

    # --- backup previo a la escritura ---
    if args.backup and args.method in WRITE_METHODS:
        url_escritura = client.build_url(path, args.params)
        try:
            hacer_backup(client, args.backup, args.method, url_escritura, path)
        except ApiError as exc:
            print("ERROR: no se pudo hacer el backup previo (%s)." % exc,
                  file=sys.stderr)
            print("La escritura se ABORTA: la API no tiene deshacer y sin "
                  "backup no hay forma de revertir.", file=sys.stderr)
            return EXIT_API
        except OSError as exc:
            print("ERROR: no se pudo escribir el backup en %s: %s"
                  % (args.backup, exc), file=sys.stderr)
            print("La escritura se ABORTA.", file=sys.stderr)
            return EXIT_API
        if not args.json_out:
            print("Backup del estado actual guardado en %s" % args.backup)

    resp = client.request(args.method, path, params=args.params, body_bytes=body_bytes)
    imprimir_respuesta(args, resp.status, resp.url, resp.payload, resp.raw_text)
    return EXIT_OK


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        return run(argv)
    except UsageError as exc:
        print("ERROR de uso: %s" % exc, file=sys.stderr)
        return EXIT_USAGE
    except ApiError as exc:
        print("ERROR: %s" % exc, file=sys.stderr)
        return EXIT_API
    except KeyboardInterrupt:
        print("interrumpido", file=sys.stderr)
        return EXIT_API


if __name__ == "__main__":
    sys.exit(main())
