#!/usr/bin/env python3
"""Chequea si es seguro escribir archivos de un tema sectionable de Tienda Nube.

El comerciante edita `templates/**` y `config/settings_data.json` desde el editor
de la tienda. Escribir sobre una copia local vieja y pushear no solo pisa esos
cambios: `theme push` sincroniza eliminaciones, así que borra lo que él agregó.
Este script verifica lo determinista del gate previo a escribir:

  - que el directorio sea una instalación bajada con el CLI (Fork workflow),
  - la antigüedad del último `theme pull` (mtime de manifest.json),
  - el estado de git (repo, archivos sin commitear, commits pendientes del remoto),
  - si hay un `theme watch` corriendo (hay que cortarlo antes de pullear),
  - el estado de `forked`,
  - y en qué capa cae cada archivo que se está por tocar (--files).

No corre el pull ni lee el diff: dice si podés escribir y, si no, qué falta.

Uso:
  python3 sync-check.py [ruta-del-tema] [--files a b c] [--max-age MIN]
                        [--no-fetch] [--json]

Exit codes: 0 = podés escribir · 1 = falta sincronizar · 2 = error de uso.
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# Capas de propiedad de los archivos del tema. El orden importa: primer match gana.
LAYERS = [
    ("templates/", "compartida", "el comerciante la edita desde el editor"),
    ("config/settings_data.json", "compartida", "el comerciante la edita desde el editor"),
    ("config/settings_schema.json", "codigo", "código del tema (git + updates del tema base)"),
    ("sections/", "codigo", "código del tema (git + updates del tema base)"),
    ("blocks/", "codigo", "código del tema (git + updates del tema base)"),
    ("snippets/", "codigo", "código del tema (git + updates del tema base)"),
    ("layouts/", "codigo", "código del tema (git + updates del tema base)"),
    ("static/", "codigo", "código del tema (git + updates del tema base)"),
    ("translations/", "codigo", "código del tema (git + updates del tema base)"),
    ("locales/", "codigo", "código del tema (git + updates del tema base)"),
    ("custom/", "dev", "solo devs (git)"),
    ("manifest.json", "local", "local, lo regenera el CLI en cada pull"),
    (".nuvem", "local", "local y secreto: nunca se commitea"),
]


def run(cmd, cwd, timeout=20):
    """Corre un comando y devuelve (ok, stdout). Nunca levanta excepción."""
    try:
        p = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True,
                           timeout=timeout)
        return p.returncode == 0, (p.stdout or "").strip()
    except (OSError, subprocess.SubprocessError):
        return False, ""


def classify(rel_path):
    norm = str(rel_path).lstrip("./").replace(os.sep, "/")
    for prefix, layer, why in LAYERS:
        if norm == prefix or (prefix.endswith("/") and norm.startswith(prefix)):
            return layer, why
    return "desconocida", "no es una ruta conocida del tema"


def git_state(theme, do_fetch):
    st = {"is_repo": False, "branch": None, "dirty": [], "has_remote": False,
          "behind": 0, "ahead": 0, "fetch_ok": None}
    ok, top = run(["git", "rev-parse", "--show-toplevel"], theme)
    if not ok or not top:
        return st
    st["is_repo"] = True
    st["root"] = top
    _, st["branch"] = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], theme)
    ok, out = run(["git", "status", "--porcelain", "--", "."], theme)
    if ok and out:
        st["dirty"] = out.splitlines()
    ok, upstream = run(["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], theme)
    if not ok or not upstream:
        return st
    st["has_remote"] = True
    st["upstream"] = upstream
    if do_fetch:
        st["fetch_ok"], _ = run(["git", "fetch", "--quiet"], theme, timeout=60)
    ok, counts = run(["git", "rev-list", "--left-right", "--count", "@{u}...HEAD"], theme)
    if ok and counts:
        parts = counts.split()
        if len(parts) == 2 and all(p.isdigit() for p in parts):
            st["behind"], st["ahead"] = int(parts[0]), int(parts[1])
    return st


def watch_running(theme):
    """True si parece haber un `theme watch` activo (best effort)."""
    ok, out = run(["ps", "ax", "-o", "command="], theme, timeout=10)
    if not ok:
        return None
    for line in out.splitlines():
        low = " ".join(line.lower().split())
        if "sync-check" in low:
            continue
        if "theme watch" in low and ("tiendanube" in low or "nuvemshop" in low):
            return True
    return False


def main():
    ap = argparse.ArgumentParser(
        description="Chequea si es seguro escribir archivos de un tema sectionable de Tienda Nube.")
    ap.add_argument("theme", nargs="?", default=".", help="ruta del tema (default: directorio actual)")
    ap.add_argument("--files", nargs="*", default=[],
                    help="archivos que se van a escribir, para clasificar su capa")
    ap.add_argument("--max-age", type=int, default=30,
                    help="minutos de antigüedad tolerada del último theme pull (default 30)")
    ap.add_argument("--no-fetch", action="store_true", help="no correr git fetch")
    ap.add_argument("--json", action="store_true", dest="as_json", help="salida JSON")
    args = ap.parse_args()

    theme = Path(args.theme).expanduser().resolve()
    if not theme.is_dir():
        print(f"ERROR: {theme} no existe o no es un directorio", file=sys.stderr)
        return 2

    manifest_path = theme / "manifest.json"
    nuvem_path = theme / ".nuvem"
    if not manifest_path.is_file() and not nuvem_path.is_file():
        print(f"ERROR: {theme} no parece una instalación del Fork workflow "
              f"(no hay manifest.json ni .nuvem). Corré `tiendanube theme pull --theme-id <id>` "
              f"en la carpeta del tema, o confirmá que el proyecto no es un tema clásico/FTP.",
              file=sys.stderr)
        return 2

    report = {"theme": str(theme), "blockers": [], "warnings": [], "commands": []}
    need = {"init": False, "commit": False, "gitpull": False}

    # --- instalación -------------------------------------------------------
    manifest = {}
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            report["warnings"].append(f"manifest.json ilegible ({exc}): no se puede verificar el pull")
    report["installation_id"] = manifest.get("installation_id")
    report["forked"] = manifest.get("forked")
    report["theme_version"] = manifest.get("theme_version")
    rev = manifest.get("revision_token")
    report["revision_token"] = (rev[:12] + "…") if isinstance(rev, str) and len(rev) > 12 else rev

    # --- frescura del último pull ------------------------------------------
    age_min = None
    if manifest_path.is_file():
        age_min = int((time.time() - manifest_path.stat().st_mtime) // 60)
    report["last_pull_minutes"] = age_min
    if age_min is None:
        report["blockers"].append("no hay manifest.json: no se sabe de qué revisión viene esta copia")
    elif age_min > args.max_age:
        report["blockers"].append(
            f"el último `theme pull` fue hace ~{age_min} min (umbral {args.max_age}): "
            f"la tienda puede haber cambiado")

    # --- git ---------------------------------------------------------------
    g = git_state(theme, do_fetch=not args.no_fetch)
    report["git"] = g
    if not g["is_repo"]:
        report["blockers"].append(
            "el proyecto no es un repo git: sin git el pull sobrescribe sin dejar rastro "
            "y no hay forma de ver qué cambió el comerciante")
        need["init"] = True
    else:
        if g["dirty"]:
            report["blockers"].append(
                f"hay {len(g['dirty'])} archivo(s) sin commitear y `theme pull` los sobrescribe")
            need["commit"] = True
        if g["has_remote"]:
            if g.get("fetch_ok") is False:
                report["warnings"].append("`git fetch` falló (¿sin red?): el conteo de commits pendientes puede estar viejo")
            if g["behind"]:
                report["blockers"].append(f"faltan {g['behind']} commit(s) del remoto de git")
                need["gitpull"] = True
        else:
            report["warnings"].append("el repo no tiene upstream configurado: el paso de `git pull` no aplica")

    # --- watch -------------------------------------------------------------
    w = watch_running(theme)
    report["watch_running"] = w
    if w:
        report["warnings"].append(
            "parece haber un `theme watch` corriendo: cortalo antes de pullear "
            "(el watcher re-pushea lo que escriba el pull y replica eliminaciones)")

    # --- archivos objetivo -------------------------------------------------
    targets = []
    for f in args.files:
        p = Path(f)
        try:
            rel = p.resolve().relative_to(theme) if p.is_absolute() else Path(f)
        except ValueError:
            rel = Path(f)
        layer, why = classify(rel)
        targets.append({"path": str(rel), "layer": layer, "why": why})
    report["targets"] = targets

    shared = [t for t in targets if t["layer"] == "compartida"]
    code = [t for t in targets if t["layer"] == "codigo"]
    if shared:
        report["warnings"].append(
            f"{len(shared)} archivo(s) de propiedad compartida con el comerciante: "
            f"pulleá incluso si ya lo hiciste hace poco, y commiteá lo que traiga antes de editar")
    if code and report["forked"] is False:
        report["warnings"].append(
            "`forked: false` y vas a tocar código del tema: `theme push` va a omitir esos "
            "archivos en silencio (hace falta `tiendanube theme fork`)")
    unknown = [t["path"] for t in targets if t["layer"] == "desconocida"]
    if unknown:
        report["warnings"].append(f"rutas no reconocidas como parte del tema: {', '.join(unknown)}")

    # Orden canónico del gate: primero proteger lo local, después traer lo remoto.
    if report["blockers"]:
        cmds = []
        if need["init"]:
            cmds.append('git init -b main && printf ".nuvem\\n" >> .gitignore '
                        '&& git add -A && git commit -m "chore: estado inicial del tema"')
        if need["commit"]:
            cmds.append('git add -A && git commit -m "wip: <qué>"   # o: git stash')
        if need["gitpull"]:
            cmds.append("git pull --ff-only")
        if w:
            cmds.append("# cortá el `theme watch` antes de seguir")
        cmds.append("tiendanube theme pull")
        cmds.append("git status && git diff    # lo que aparezca y no escribiste vos ES del comerciante")
        report["commands"] = cmds
    report["verdict"] = "PULL REQUERIDO" if report["blockers"] else "OK PARA ESCRIBIR"

    if args.as_json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 1 if report["blockers"] else 0

    # --- salida legible ----------------------------------------------------
    print(f"Tema: {theme}")
    inst = report["installation_id"] or "?"
    fork_txt = {True: "con fork", False: "sin fork", None: "fork desconocido"}[report["forked"]]
    age_txt = f"hace ~{age_min} min" if age_min is not None else "desconocido"
    print(f"Instalación {inst} · {fork_txt} · tema {report['theme_version'] or '?'} "
          f"· revisión {report['revision_token'] or '?'}")
    print(f"Último `theme pull`: {age_txt}")
    if g["is_repo"]:
        rama = g["branch"] or "?"
        est = "limpio" if not g["dirty"] else f"{len(g['dirty'])} sin commitear"
        rem = f"behind {g['behind']} / ahead {g['ahead']}" if g["has_remote"] else "sin upstream"
        print(f"Git: rama {rama} · {est} · {rem}")
        for line in g["dirty"][:10]:
            print(f"     {line}")
        if len(g["dirty"]) > 10:
            print(f"     … y {len(g['dirty']) - 10} más")
    else:
        print("Git: el proyecto no es un repo")
    if w:
        print("Watch: hay un `theme watch` corriendo")
    for t in targets:
        print(f"Objetivo: {t['path']} → capa {t['layer']} ({t['why']})")

    if report["warnings"]:
        print("\nAvisos:")
        for x in report["warnings"]:
            print(f"  ! {x}")
    if report["blockers"]:
        print("\nBloqueantes:")
        for x in report["blockers"]:
            print(f"  ✗ {x}")
        print("\nCorré, en este orden:")
        for c in report["commands"]:
            print(f"  $ {c}")
        print("\nVEREDICTO: PULL REQUERIDO — no escribas todavía.")
        return 1

    print("\nVEREDICTO: OK PARA ESCRIBIR — la copia local está sincronizada.")
    print("Igual revisá `git diff` después del próximo pull: el editor del comerciante no avisa.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
