#!/usr/bin/env python3
"""Auditoría de traducciones de un tema sectionable de Tienda Nube.

Un tema tiene DOS sistemas de traducción independientes dentro de la misma
carpeta (`translations/` o `locales/`):

  1. <locale>.json         -> strings de storefront (comprador).
                              Claves ANIDADAS, se usan con `{{ 'a.b' | t }}`.
  2. <locale>.schema.json  -> labels del editor (comerciante).
                              Objetos PLANOS por namespace, se usan como
                              claves `t:` dentro de los `{% schema %}`.

El script recolecta las claves USADAS en el código, las DEFINIDAS en cada
archivo de locale, y reporta las FALTANTES (usadas pero no definidas en ese
archivo) y las HUÉRFANAS (definidas y no usadas en ningún lado).

Uso:
    python3 audit-i18n.py [ruta-del-tema] [--json]

Exit codes:
    0  sin faltantes
    1  hay faltantes (o algún archivo de locale ilegible)
    2  error de uso (la ruta no existe / no hay carpeta de traducciones)
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

TRANSLATION_DIRS = ("translations", "locales")

# Namespaces planos válidos de los archivos *.schema.json (informativo).
SCHEMA_NAMESPACES = ("names", "settings", "options", "defaults", "info", "content", "categories")

# Claves de schema: el string completo es "t:<ruta.con.puntos>".
TKEY_RE = re.compile(r"""(['"])\s*t:([A-Za-z0-9_][A-Za-z0-9_.\-]*)\s*\1""")

# Claves de storefront: '<ruta.con.puntos>' | t   (comillas simples o dobles).
FILTER_RE = re.compile(r"""(['"])([A-Za-z0-9_][A-Za-z0-9_.\-]*)\1\s*\|\s*t(?![A-Za-z0-9_])""")

SKIP_DIRS = {".git", ".svn", "node_modules", ".idea", ".vscode", "__pycache__", "dist", "build"}

MAX_LOCATIONS = 3


# --------------------------------------------------------------------------- io

def read_text(path):
    """Lee un archivo de texto tolerando encoding roto. Devuelve (texto, error)."""
    try:
        return path.read_text(encoding="utf-8"), None
    except UnicodeDecodeError:
        try:
            return path.read_text(encoding="utf-8", errors="replace"), None
        except OSError as exc:
            return None, str(exc)
    except OSError as exc:
        return None, str(exc)


def walk_files(root, suffixes):
    """Recorre `root` devolviendo archivos con alguno de los sufijos dados."""
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and not d.startswith("."))
        for name in sorted(filenames):
            if any(name.endswith(s) for s in suffixes):
                out.append(Path(dirpath) / name)
    return out


# ------------------------------------------------------------------- recolección

def collect_used(theme):
    """Devuelve (schema_keys, storefront_keys) como dict clave -> [archivos]."""
    schema_keys = {}
    storefront_keys = {}

    def add(bucket, key, path):
        bucket.setdefault(key, set()).add(rel(theme, path))

    # --- claves de schema (t:) -------------------------------------------------
    schema_sources = []
    for sub in ("sections", "blocks"):
        d = theme / sub
        if d.is_dir():
            schema_sources += walk_files(d, (".tpl",))
    settings_schema = theme / "config" / "settings_schema.json"
    if settings_schema.is_file():
        schema_sources.append(settings_schema)
    templates = theme / "templates"
    if templates.is_dir():
        schema_sources += walk_files(templates, (".json",))

    for path in schema_sources:
        text, _ = read_text(path)
        if text is None:
            continue
        for _, key in TKEY_RE.findall(text):
            add(schema_keys, key, path)

    # --- claves de storefront (| t) --------------------------------------------
    for path in walk_files(theme, (".tpl",)):
        text, _ = read_text(path)
        if text is None:
            continue
        for _, key in FILTER_RE.findall(text):
            add(storefront_keys, key, path)

    return schema_keys, storefront_keys


def rel(theme, path):
    try:
        return str(Path(path).relative_to(theme))
    except ValueError:
        return str(path)


def flatten(obj, prefix=""):
    """Aplana un dict anidado a un set de rutas con puntos hacia cada hoja."""
    keys = set()
    for k, v in obj.items():
        path = f"{prefix}{k}"
        if isinstance(v, dict):
            if v:
                keys |= flatten(v, path + ".")
            else:
                keys.add(path)
        else:
            keys.add(path)
    return keys


def load_locale_file(path):
    """Devuelve (set_de_claves, error|None) para un archivo de locale."""
    text, err = read_text(path)
    if text is None:
        return set(), f"no se pudo leer: {err}"
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return set(), f"JSON inválido (línea {exc.lineno}, columna {exc.colno}): {exc.msg}"
    if not isinstance(data, dict):
        return set(), "el archivo raíz debe ser un objeto JSON"
    return flatten(data), None


def find_translations_dir(theme):
    """Devuelve (Path|None, [otras_encontradas])."""
    found = [theme / name for name in TRANSLATION_DIRS if (theme / name).is_dir()]
    if not found:
        return None, []
    return found[0], [str(p.name) for p in found[1:]]


# ---------------------------------------------------------------------- auditoría

def audit(theme, tdir):
    used_schema, used_storefront = collect_used(theme)
    used_schema_set = set(used_schema)
    used_storefront_set = set(used_storefront)

    files = []
    for path in sorted(tdir.glob("*.json")):
        name = path.name
        if name.endswith(".schema.json"):
            kind, locale = "schema", name[: -len(".schema.json")]
        else:
            kind, locale = "storefront", name[: -len(".json")]
        defined, error = load_locale_file(path)
        files.append({
            "file": rel(theme, path),
            "name": name,
            "kind": kind,
            "locale": locale,
            "defined": defined,
            "error": error,
        })

    # Índice por locale para detectar claves puestas en el sistema equivocado.
    by_locale = {}
    for f in files:
        by_locale.setdefault(f["locale"], {})[f["kind"]] = f

    for f in files:
        if f["error"]:
            f["missing"], f["misplaced"], f["orphans"] = [], [], []
            continue
        used = used_schema_set if f["kind"] == "schema" else used_storefront_set
        missing = sorted(used - f["defined"])
        other_kind = "storefront" if f["kind"] == "schema" else "schema"
        sibling = by_locale.get(f["locale"], {}).get(other_kind)
        sib_defined = sibling["defined"] if sibling and not sibling["error"] else set()
        f["missing"] = missing
        f["misplaced"] = sorted(k for k in missing if k in sib_defined)
        f["orphans"] = sorted(f["defined"] - used)

    return {
        "files": files,
        "used_schema": used_schema,
        "used_storefront": used_storefront,
    }


# ------------------------------------------------------------------------ salida

def locations(used_map, key):
    return sorted(used_map.get(key, ()))


def print_report(theme, tdir, extra_dirs, result):
    files = result["files"]
    used_schema, used_storefront = result["used_schema"], result["used_storefront"]
    locales = sorted({f["locale"] for f in files})
    missing_total = sum(len(f["missing"]) for f in files)
    orphan_total = sum(len(f["orphans"]) for f in files)
    broken = [f for f in files if f["error"]]

    print(f"Auditoría i18n — {theme}")
    print(f"Carpeta de traducciones: {rel(theme, tdir)}/  "
          f"({len(files)} archivo(s), {len(locales)} locale(s): {', '.join(locales) or '—'})")
    if extra_dirs:
        print(f"  aviso: también existe {', '.join(extra_dirs)}/ — se auditó solo {tdir.name}/")
    if not files:
        print(f"  aviso: {rel(theme, tdir)}/ no contiene ningún archivo .json de locale")
    print(f"Claves usadas: {len(used_schema)} de schema (t:) · "
          f"{len(used_storefront)} de storefront (| t)")
    print()

    if broken:
        print(f"ARCHIVOS ILEGIBLES ({len(broken)})")
        for f in broken:
            print(f"  ✗ {f['file']}: {f['error']}")
        print()

    print(f"FALTANTES — usadas en el código y no definidas ({missing_total})")
    if not missing_total:
        print("  ✓ ninguna")
    for f in files:
        if not f["missing"]:
            continue
        used_map = used_schema if f["kind"] == "schema" else used_storefront
        print(f"  {f['file']}  [{f['kind']}]  ({len(f['missing'])})")
        for key in f["missing"]:
            locs = locations(used_map, key)
            shown = ", ".join(locs[:MAX_LOCATIONS])
            if len(locs) > MAX_LOCATIONS:
                shown += f", +{len(locs) - MAX_LOCATIONS} más"
            flag = "  ⚠ definida en el archivo del OTRO sistema" if key in f["misplaced"] else ""
            print(f"    - {key}{flag}")
            print(f"        usada en: {shown}")
    print()

    print(f"HUÉRFANAS — definidas y no usadas ({orphan_total}) · informativas, no se borran")
    if not orphan_total:
        print("  ✓ ninguna")
    for f in files:
        if not f["orphans"]:
            continue
        print(f"  {f['file']}  ({len(f['orphans'])})")
        print(f"    {', '.join(f['orphans'])}")
    print()

    print("RESUMEN")
    print(f"  locales: {len(locales)}  ·  archivos de locale: {len(files)}")
    print(f"  claves usadas: schema {len(used_schema)} · storefront {len(used_storefront)}")
    print(f"  faltantes: {missing_total}  ·  huérfanas: {orphan_total}  "
          f"·  archivos ilegibles: {len(broken)}")


def json_report(theme, tdir, extra_dirs, result):
    files = result["files"]
    used_schema, used_storefront = result["used_schema"], result["used_storefront"]
    locales = sorted({f["locale"] for f in files})
    missing_total = sum(len(f["missing"]) for f in files)
    orphan_total = sum(len(f["orphans"]) for f in files)
    broken = [f for f in files if f["error"]]
    return {
        "theme": str(theme),
        "translations_dir": rel(theme, tdir),
        "other_translation_dirs": extra_dirs,
        "locales": locales,
        "used": {
            "schema": {k: sorted(v) for k, v in sorted(used_schema.items())},
            "storefront": {k: sorted(v) for k, v in sorted(used_storefront.items())},
        },
        "files": [
            {
                "file": f["file"],
                "locale": f["locale"],
                "kind": f["kind"],
                "error": f["error"],
                "defined_count": len(f["defined"]),
                "missing": f["missing"],
                "misplaced": f["misplaced"],
                "orphans": f["orphans"],
            }
            for f in files
        ],
        "summary": {
            "locales": len(locales),
            "locale_files": len(files),
            "used_schema": len(used_schema),
            "used_storefront": len(used_storefront),
            "missing_total": missing_total,
            "orphans_total": orphan_total,
            "unreadable_files": len(broken),
        },
    }


# -------------------------------------------------------------------------- main

def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Audita las traducciones (t: y | t) de un tema sectionable de Tienda Nube.")
    parser.add_argument("theme", nargs="?", default=".", help="ruta del tema (default: directorio actual)")
    parser.add_argument("--json", action="store_true", dest="as_json",
                        help="salida en JSON en vez de texto legible")
    args = parser.parse_args(argv)

    theme = Path(args.theme).expanduser().resolve()
    if not theme.is_dir():
        print(f"error: la ruta del tema no existe o no es un directorio: {theme}", file=sys.stderr)
        return 2

    tdir, extra = find_translations_dir(theme)
    if tdir is None:
        print(f"error: no se encontró carpeta de traducciones en {theme} "
              f"(se buscó: {', '.join(d + '/' for d in TRANSLATION_DIRS)})", file=sys.stderr)
        return 2

    result = audit(theme, tdir)
    if args.as_json:
        print(json.dumps(json_report(theme, tdir, extra, result), ensure_ascii=False, indent=2))
    else:
        print_report(theme, tdir, extra, result)

    missing_total = sum(len(f["missing"]) for f in result["files"])
    broken = sum(1 for f in result["files"] if f["error"])
    return 1 if (missing_total or broken) else 0


if __name__ == "__main__":
    sys.exit(main())
