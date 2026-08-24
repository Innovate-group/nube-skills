#!/usr/bin/env python3
"""Sync gate determinista: hook de Claude Code para nube-skills.

Una skill se carga cuando el modelo decide que es relevante, y sus reglas se
pueden saltear. Este hook no: corre en TODA escritura, sin importar qué skills
haya cargadas.

Bloquea escribir en la capa que el comerciante edita desde el editor de la
tienda (`templates/**`, `config/settings_data.json`) cuando no hay un
`tiendanube theme pull` reciente, y bloquea `theme push` en la misma condición.
Escribir con una copia vieja pisa las settings del comerciante y, al pushear,
BORRA las secciones que él agregó (`theme push` sincroniza eliminaciones).

Modos:
  --gate    PreToolUse  (Write|Edit|MultiEdit|NotebookEdit y Bash)
  --stamp   PostToolUse (Bash): registra los `theme pull` que salieron bien

Principios:
  - **Inerte fuera de un tema de Tienda Nube.** Si el archivo no está dentro de
    una instalación bajada con el CLI, no dice nada.
  - **Fail-open.** Cualquier error interno = permitir. Un hook roto no puede
    bloquear el trabajo en todos los proyectos.
  - **Rápido.** Solo filesystem: ni git, ni red, ni subprocesos.
"""
import json
import os
import re
import sys
import time
from pathlib import Path

WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
DEFAULT_MAX_AGE_MIN = 15
# La doc lista `tool_input.path` para Write/Edit, pero sus propios ejemplos usan
# `file_path`: probamos las variantes en vez de apostar a una (si no encontramos
# la ruta, el gate se abre y no protege nada).
PATH_KEYS = ("file_path", "notebook_path", "path", "filePath")


def load_helpers():
    """Trae la clasificación de capas y la frescura del pull desde la skill."""
    import importlib.util

    target = (Path(__file__).resolve().parent.parent / "skills" /
              "nube-skills-themes" / "scripts" / "sync-check.py")
    spec = importlib.util.spec_from_file_location("nube_sync_check", target)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def allow():
    """Silencio = seguir adelante."""
    sys.exit(0)


def deny(reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }}))
    sys.exit(0)


def ask(reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "ask",
        "permissionDecisionReason": reason,
    }}))
    sys.exit(0)


def gate_message(what, age_min, age_src, theme):
    cuando = (f"el último `tiendanube theme pull` conocido fue hace ~{age_min} min "
              f"(según {age_src})" if age_min is not None
              else "no hay registro de ningún `tiendanube theme pull` en este tema")
    return (
        f"BLOQUEADO por el sync gate de nube-skills.\n\n"
        f"{what}\n"
        f"Tema: {theme}\n"
        f"Estado: {cuando}.\n\n"
        f"El comerciante edita `templates/**` y `config/settings_data.json` desde el editor "
        f"de la tienda. Escribir con una copia local vieja le pisa las settings y, al pushear, "
        f"le BORRA las secciones que agregó — `theme push` sincroniza eliminaciones. No hay deshacer.\n\n"
        f"Corré el gate (Paso 0.5 de la skill nube-skills-themes) y después reintentá:\n"
        f"  1. `git status --porcelain` — si hay cambios sin commitear, commiteá o stasheá "
        f"ANTES del pull (`theme pull` sobrescribe los archivos locales).\n"
        f"  2. `git pull --ff-only` — si el repo tiene remoto.\n"
        f"  3. `tiendanube theme pull` — trae lo que guardó el comerciante. Si hay un "
        f"`theme watch` corriendo, cortalo antes.\n"
        f"  4. `git diff` — lo que aparezca y no lo hayas escrito vos ES del comerciante: "
        f"commitealo aparte (`chore: sync cambios del comerciante`) antes de editar encima. "
        f"Si toca lo mismo que ibas a cambiar, mostrale los dos valores al dev y esperá su "
        f"decisión: el valor del comerciante gana por default.\n\n"
        f"No busques otra vía para escribir el archivo (ni Bash, ni otra herramienta): el "
        f"bloqueo protege datos de un tercero. Si el pull ya lo corrió el dev en su terminal, "
        f"registralo con `sync-check.py <tema> --stamp`. Saltear el gate es decisión del dev, "
        f"no tuya: él setea NUBE_SKIP_SYNC_GATE=1 si lo necesita."
    )


def main():
    if os.environ.get("NUBE_SKIP_SYNC_GATE", "").strip().lower() in ("1", "true", "yes", "on"):
        allow()

    mode = "--stamp" if "--stamp" in sys.argv else "--gate"
    data = json.load(sys.stdin)
    tool = data.get("tool_name") or ""
    tin = data.get("tool_input") or {}
    cwd = data.get("cwd") or os.getcwd()
    h = load_helpers()

    try:
        max_age = int(os.environ.get("NUBE_SYNC_MAX_AGE_MIN", DEFAULT_MAX_AGE_MIN))
    except ValueError:
        max_age = DEFAULT_MAX_AGE_MIN

    # --- PostToolUse: registrar el pull que acabó de correr bien -----------
    if mode == "--stamp":
        if tool != "Bash":
            allow()
        cmd = str(tin.get("command") or "")
        if not re.search(r"\btheme\s+pull\b", cmd):
            allow()
        resp = data.get("tool_response")
        if isinstance(resp, dict):
            for key in ("exit_code", "exitCode", "returncode", "status"):
                val = resp.get(key)
                if isinstance(val, int) and val != 0:
                    allow()          # el pull falló: no registrar nada
            if resp.get("is_error") or resp.get("isError"):
                allow()
        theme = h.find_theme_root(cwd)
        if theme is None:
            allow()
        # Corroboración: un pull exitoso reescribe manifest.json. Si no se movió,
        # no hubo pull (comando fallido, --help, dry-run mental) y no se registra:
        # es preferible un bloqueo de más que un permiso falso.
        man = Path(theme) / "manifest.json"
        if not man.is_file():
            allow()
        if (time.time() - man.stat().st_mtime) > 300:
            allow()
        h.stamp_pull(theme)
        allow()

    # --- PreToolUse: Bash (push / publish) ---------------------------------
    if tool == "Bash":
        cmd = str(tin.get("command") or "")
        theme = h.find_theme_root(cwd)
        if theme is None:
            allow()
        if re.search(r"\btheme\s+publish\b", cmd):
            ask("`theme publish` reemplaza el tema productivo de la tienda. Si venís "
                "trabajando en un borrador, todo lo que el comerciante configuró en la "
                "instalación productiva desde que se clonó se pierde de una sola vez. "
                "Confirmá con el dev que se comparó contra la productiva "
                "(`nube-skills-themes` → references/sync-and-conflicts.md §7).")
        if not re.search(r"\btheme\s+push\b", cmd):
            allow()
        age_min, age_src = h.sync_age_minutes(theme)
        if age_min is not None and age_min <= max_age and age_src == "marcador de pull":
            allow()
        deny(gate_message("Comando: `theme push` (sube y sincroniza ELIMINACIONES).",
                          age_min, age_src, theme))

    # --- PreToolUse: escrituras -------------------------------------------
    if tool not in WRITE_TOOLS:
        allow()
    target = next((tin[k] for k in PATH_KEYS if isinstance(tin.get(k), str) and tin[k]), None)
    if not target:
        allow()
    theme = h.find_theme_root(target)
    if theme is None:
        allow()                        # no es un tema de Tienda Nube: hook inerte
    try:
        rel = Path(target).expanduser().resolve().relative_to(theme)
    except (OSError, ValueError):
        allow()
    layer, _ = h.classify(rel)
    if layer != "compartida":
        allow()                        # solo se bloquea la capa del comerciante
    age_min, age_src = h.sync_age_minutes(theme)
    if age_min is not None and age_min <= max_age and age_src == "marcador de pull":
        allow()
    deny(gate_message(f"Archivo: {rel} — capa compartida con el comerciante.",
                      age_min, age_src, theme))


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except BaseException:              # fail-open: nunca bloquear por un error propio
        sys.exit(0)
