# Ejecución: MCP oficial, script propio o admin web

Cómo se ejecuta realmente una operación sobre una tienda: con qué brazo, con qué credenciales, con qué
protocolo y qué hacer cuando la API responde mal.

> Regla transversal: **lectura libre, escritura en cinco tiempos** — dry-run → diff registro por
> registro → backup a archivo → confirmación explícita del dev → ejecución. La API no tiene deshacer.

## Tabla de contenidos

1. [Elegir el brazo ejecutor](#1-elegir-el-brazo-ejecutor)
2. [Conectar el MCP oficial](#2-conectar-el-mcp-oficial)
3. [Credenciales para el script](#3-credenciales-para-el-script)
4. [Uso del script `tn-api.py`](#4-uso-del-script-tn-apipy)
5. [Paginación y rate limit en la práctica](#5-paginación-y-rate-limit-en-la-práctica)
6. [Errores y qué hacer con cada uno](#6-errores-y-qué-hacer-con-cada-uno)
7. [Sin acceso a API](#7-sin-acceso-a-api)

---

## 1. Elegir el brazo ejecutor

Hay tres brazos y se eligen en este orden: **MCP oficial** (si está conectado y cubre el recurso) →
**script `tn-api.py`** (si hay token) → **guía por el admin web** (si no hay ninguna de las dos).

| Área | MCP oficial | Script `tn-api.py` |
|---|---|---|
| Productos, variantes, stock y precios | ✅ CRUD, bulk de stock/precio (≤50 variantes) y de visibilidad (≤20) | ✅ todo, y sin los topes de la tool |
| Categorías | ✅ | ✅ |
| Cupones | ✅ | ✅ |
| Promociones **nativas** | ✅ create / update / delete | ❌ **no hay REST pública** (ver [`no-se-puede.md`](no-se-puede.md) §5) |
| Órdenes | 👁️ solo lectura | ✅ lectura + `PUT` (`owner_note`, `status`), `close`/`open`/`cancel` |
| Clientes | 👁️ solo lectura | ✅ |
| Métodos de pago y de envío | 👁️ solo lectura | ✅ (los de app; los nativos no se tocan por API) |
| Fulfillment orders, tracking, Labels API | ❌ | ✅ |
| Metafields y custom fields | ❌ | ✅ |
| Locations y multi-inventario | ❌ | ✅ |
| Draft orders, abandoned checkouts, transacciones | ❌ | ✅ |
| Webhooks, scripts | ❌ | ✅ |
| Páginas, blog, email templates, price tables B2B | ❌ | ✅ |

Criterio corto:

- **Consulta puntual o cambio chico sobre catálogo** → MCP oficial: es más rápido y no pide token.
- **Cualquier lote, cualquier escritura riesgosa, o algo fuera del catálogo** → script: es el único
  brazo con `--dry-run`, `--backup` y control de rate limit propio.
- **Promociones nativas** → MCP oficial, es la única vía comprobada.

---

## 2. Conectar el MCP oficial

| Dato | Valor |
|---|---|
| Endpoint (LATAM) | `https://admin-mcp.tiendanube.com/mcp` |
| Endpoint (Brasil) | `https://admin-mcp.nuvemshop.com.br/mcp` |
| Autenticación | OAuth con **Dynamic Client Registration** (no hay que crear app en el Partner Portal) |
| Alcance | **Una conexión = una tienda.** Para operar dos tiendas hacen falta dos conexiones |
| Herramientas | ~28 tools al relevamiento de 2026-08 |

Quién autoriza es el **merchant**, con su usuario del panel: los permisos de la conexión son los de
ese usuario, no los de una app instalada.

> **[incierto]** Nada de este bloque está en `tiendanube.github.io/api-documentation` — el MCP no se
> documenta ahí. Sale del relevamiento propio de agosto 2026. Antes de prometer que el MCP resuelve
> algo, **listar las tools de la conexión activa y confirmarlo**; el inventario de la sección 1 es una
> foto, no un contrato.

Dos límites que sí conviene recordar porque cambian el diseño de un lote: el bulk de stock/precio
corta en **50 variantes** por llamada y el de visibilidad en **20 productos**. Un lote más grande se
parte, y partirlo a mano en la conversación es peor que hacerlo con el script.

---

## 3. Credenciales para el script

El token sale de una **app propia instalada en la tienda del cliente** (la modalidad de *installation
link*, sin publicación en la App Store). El flujo completo está en
[`api-map.md` §2](api-map.md#2-autenticación). Tres cosas que importan acá:

- **Los access tokens no expiran.** Se invalidan solo al generar uno nuevo o si el merchant
  desinstala la app. No hay refresh token: si el token dejó de andar, hay que reinstalar.
- **Cambiar los scopes de la app obliga a reinstalarla en cada tienda.** Pedir de entrada los scopes
  que el proyecto va a necesitar.
- El `user_id` que devuelve el intercambio del `code` **es el `store_id`**.

Variables de entorno que lee el script:

```bash
export TN_STORE_ID="123456"                       # el user_id del token
export TN_ACCESS_TOKEN="..."                      # nunca en el repo, nunca en el chat
export TN_USER_AGENT="Innovate Group (dev@ejemplo.com)"
```

Reglas duras de manejo:

1. **Nunca** commitear un token, un `store_id` real ni un nombre de cliente a este repo (es público).
2. **Nunca** pegar el token en la conversación ni en un log. El script lo enmascara siempre a los
   últimos 4 caracteres; el descuido está del lado humano.
3. El `User-Agent` es **obligatorio**: sin ese header la API devuelve `400`. Debe llevar nombre de la
   app y un mail o URL de contacto.
4. Un token por tienda. Antes de un lote, confirmar contra qué tienda se está operando con
   `GET store` y leer el `name`.

---

## 4. Uso del script `tn-api.py`

Ruta: `skills/nube-skills-admin/scripts/tn-api.py`. Python 3, solo biblioteca estándar.

```
python3 tn-api.py <METHOD> <PATH> [opciones]

  METHOD   GET | POST | PUT | PATCH | DELETE
  PATH     ruta relativa al store, sin barra inicial: 'products', 'products/123/variants'
```

La URL final es `{base_url}/{api_version}/{store_id}/{path}`.

### Opciones

| Opción | Default | Para qué |
|---|---|---|
| `--store-id STORE_ID` | env `TN_STORE_ID` | id de la tienda |
| `--token TOKEN` | env `TN_ACCESS_TOKEN` | access token |
| `--user-agent USER_AGENT` | env `TN_USER_AGENT` | header `User-Agent`; obligatorio |
| `--base-url BASE_URL` | `https://api.tiendanube.com` | Brasil: `https://api.nuvemshop.com.br` |
| `--api-version API_VERSION` | `2025-03` | nunca `v1` en desarrollo nuevo |
| `--param K=V` | — | parámetro de querystring; **repetible** |
| `--data JSON` | — | body inline |
| `--data-file PATH` | — | body desde archivo (**excluyente** con `--data`) |
| `--paginate` | — | recorre todas las páginas y devuelve un array único |
| `--per-page N` | `100` | máx 200 |
| `--dry-run` | — | no ejecuta escrituras: imprime el request que haría |
| `--backup PATH` | — | antes de escribir, `GET` del recurso y guarda el estado actual |
| `--json` | — | salida JSON pura (sin encabezados legibles) |
| `--max-retries N` | `3` | reintentos de `429` y `5xx` |

Exit codes (están en el docstring del script, no en el `--help`): **`0`** OK · **`1`** error de la API
(4xx/5xx tras reintentos, **o backup imposible**) · **`2`** error de uso (falta una credencial,
argumentos inválidos, `--paginate` sobre algo que no es una colección).

### Comportamientos que conviene conocer antes de usarlo

- `--dry-run` **solo aplica a POST/PUT/PATCH/DELETE**; en `GET` se ignora con un aviso por stderr.
  Corta antes de tocar la red: no hace ninguna request.
- `--backup` también es solo para escrituras (en `GET` se ignora con aviso). Si el `GET` previo falla,
  **la escritura se aborta con exit 1**: sin red de seguridad no se escribe.
- Si el path termina en `/cancel`, `/close`, `/open` o `/confirm` —no son GET-eables— el backup toma
  el **recurso padre**. En un `POST` a una colección, guarda la **primera página** de esa colección.
- El archivo de backup es un JSON con `fetched_at`, `method`, `url`, `source_url` y `body` (el estado
  previo).
- `--paginate` solo vale para `GET`; con otro método es error de uso (exit 2).
- `--per-page` mayor a 200 **no es error**: avisa y lo baja a 200.
- Ante un `401`, reintenta **una vez** cambiando `Authentication: bearer` por `Authorization: Bearer`
  y lo avisa por stderr. Si vuelve a fallar, el token es el problema.
- El espaciado de 2 req/s se persiste en un archivo temporal por tienda (el nombre es un hash: no
  expone el `store_id`), así que **también se respeta entre corridas seguidas**. Se puede desactivar
  con `TN_THROTTLE_STATE=off` — no hacerlo salvo contra un fixture local.
- `--base-url` también acepta la variable `TN_BASE_URL` (está en el código, no en el `--help`).

### Recetas

**Leer una colección entera:**

```bash
python3 tn-api.py GET products --paginate --param published=true --json > productos.json
```

**Ver qué haría una escritura, sin ejecutarla:**

```bash
python3 tn-api.py PUT products/123 --data '{"name":"Remera"}' --dry-run
```

Imprime método, URL, headers (con el token enmascarado) y body, y sale con 0.

**Escribir con red de seguridad:**

```bash
python3 tn-api.py PATCH products/123/variants \
  --data-file cambio.json \
  --backup backups/producto-123-antes.json
```

Primero guarda el estado actual; si ese `GET` falla, no escribe nada.

**Lote:** un archivo de body por registro, y un loop que corta al primer error.

```bash
for f in cambios/*.json; do
  id=$(basename "$f" .json)
  python3 tn-api.py PATCH "products/$id" --data-file "$f" --backup "backups/$id.json" --json \
    || { echo "FALLÓ $id"; break; }
done
```

El script ya espacia las requests: **no agregar `sleep` propio**. Sí conviene registrar qué ids se
aplicaron para poder retomar el lote donde se cortó.

---

## 5. Paginación y rate limit en la práctica

**Por qué el corte de página es contra la página 1.** Tienda Nube **clampea `per_page` en silencio**:
se puede pedir 200 y recibir 100 sin ningún aviso. Si el corte fuera "página con menos ítems que el
`per_page` pedido", el recorrido terminaría en la primera página y devolvería datos incompletos sin
error. Por eso el script mide el tamaño **real** de la página 1 y corta cuando una página trae menos
que esa.

**Por qué un `404` al paginar no es un error.** Al pedir una página más allá de la última, la API
devuelve `404` en vez de un array vacío. Eso ocurre cuando el total es múltiplo exacto del tamaño de
página. El script lo trata como fin de colección **solo si `page > 1`**; un `404` en la primera página
sí es un error real (recurso o ruta inexistente).

**Cuánto tarda de verdad.** El bucket drena a **2 req/s** por par (tienda, app):

| Operación | Requests | Tiempo aprox. |
|---|---|---|
| Leer 5.000 productos (`--paginate`, `per_page=100`) | ~51 | ~25 s |
| Leer 20.000 órdenes particionadas por fecha | ~201 | ~100 s |
| Actualizar 500 productos con `--backup` (GET + escritura c/u) | 1.000 | ~8 min |
| Actualizar 2.000 variantes por `PATCH /products/stock-price` (50 por request) | 40 | ~20 s |

Dos advertencias sobre esos números:

- En planes **Next / Evolution** el límite real es ×10 (20 req/s), pero **el script siempre espacia a
  2 req/s**: no lee el plan ni se adapta. Un lote grande en una tienda Next va a tardar 10 veces más
  de lo que la tienda aguantaría. Es una limitación conocida del script, no de la API.
- Las requests que exceden el bucket **se pierden, no se encolan**. Por eso el patrón correcto ante un
  `429` es dormir lo que indica `x-rate-limit-reset` (viene en **milisegundos**) y reintentar, que es
  lo que el script hace hasta `--max-retries`.

Para lotes de variantes, el límite no se cuenta en requests sino en **peso del payload** (weighted
token bucket): ante `429` repetidos, **mandar menos variantes por request** en vez de esperar más.

---

## 6. Errores y qué hacer con cada uno

| Código | Qué pasó | Acción |
|---|---|---|
| `400` | Falta el `User-Agent`, o el JSON del body es inválido | Exportar `TN_USER_AGENT`; validar el body. El script exige el UA antes de salir a la red (exit 2) |
| `401` | Token inválido, revocado, o app desinstalada | El script ya reintentó con el otro header de auth: reinstalar la app / regenerar el token |
| `402` | **Tienda o app impagas: la API entera está suspendida** | No es un problema técnico ni del request. Frenar, avisar al merchant que regularice. También se cortan webhooks y scripts |
| `403` | Feature no habilitada para el plan, scope faltante, o app sin habilitación de Partner Support | `GET store` y mirar `plan_name` y `features`. Si es un trámite (Shipping, Payments, Business Rules, Labels), ver [`no-se-puede.md` §7](no-se-puede.md) |
| `404` | Recurso o ruta inexistente — **o** fin de colección si es `page > 1` | Verificar path y versión de API. Al paginar, el script ya lo distingue |
| `409` | Conflicto de estado o recurso duplicado | Leer el array `errors` del body y resolver antes de reintentar |
| `415` | Falta `Content-Type` | El script lo manda solo; si aparece, es que la request no salió por el script |
| `422` | Validación, tope de la tienda alcanzado, o combinación prohibida | Leer `description` **y** los errores por campo del formato legacy. **No reintentar sin cambiar el payload** |
| `429` | Rate limit | El script reintenta solo. Si se agota: achicar el lote (y el batch de variantes) |
| `5xx` | Problema del lado de Tienda Nube | Backoff automático (1s, 2s, 4s). Si persiste, reintentar más tarde: no es del request |

Ante un error a mitad de un lote: **no relanzar el lote entero**. Identificar qué ids se aplicaron,
rehacer el diff sobre el estado actual y correr solo el resto.

---

## 7. Sin acceso a API

Sin token y sin MCP, la skill sigue sirviendo: cambia el brazo, no el criterio. El aporte es el
triage ([`no-se-puede.md`](no-se-puede.md)) más una guía precisa de qué hacer en el panel.

- **Primero, el triage igual.** Decir el cajón (✅ / ⚠️ / 🖐️ / ❌) antes de mandar a nadie a buscar un
  botón que no existe. La mitad de los pedidos que "no se pueden por API" tampoco se pueden en el
  panel, y eso hay que decirlo antes.
- **Instrucciones por resultado, no por click.** El panel cambia de layout seguido; describir el
  objetivo ("editar el pedido para cambiar la cantidad de una línea", "importar el catálogo con el
  importador de productos") y no una secuencia exacta de menús que puede ya no existir.
- **Cargas masivas:** el panel tiene importador de productos por planilla; por API **no hay import ni
  export CSV**. Para un cambio masivo sin token, la vía es exportar del panel, editar la planilla y
  reimportar — con backup del archivo exportado antes de tocarlo.
- **Lo que sí conviene resolver por API igual** — pedirle al cliente que instale la app propia y
  entregar el token — es todo lote de más de ~50 registros, todo lo repetitivo (sincronizaciones) y
  todo lo que necesite rollback. El costo de conseguir el token se paga en el primer lote.
- **Cuando el pedido pasa por el panel, el registro es responsabilidad nuestra:** anotar qué se
  cambió, sobre qué registros y cuándo. El panel no deja un log de actividad consultable por API
  (`GET /orders/{id}/history/editions` es lo más cercano, y solo para órdenes).
