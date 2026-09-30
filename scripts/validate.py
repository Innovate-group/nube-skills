#!/usr/bin/env python3
"""Valida la estructura del repo nube-skills.

Chequea: manifiestos JSON de .claude-plugin/, la config de hooks/hooks.json
(estructura y que los scripts que invoca existan), y para cada skills/<dir>:
SKILL.md presente, frontmatter con name (== carpeta) y description (<=1024),
que toda referencia markdown a references/ exista y que los scripts citados
en el SKILL.md existan. Además, los links relativos de docs/handoff/ (sin
plantillas/) y que las rutas ${CLAUDE_PLUGIN_ROOT}/... citadas en
commands/*.md existan.
Exit 0 si todo OK; exit 1 con listado de errores si no.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
errors = []


def check(cond, msg):
    if not cond:
        errors.append(msg)


for rel in (".claude-plugin/plugin.json", ".claude-plugin/marketplace.json"):
    path = ROOT / rel
    check(path.is_file(), f"falta {rel}")
    if path.is_file():
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{rel}: JSON inválido ({exc})")

# hooks/hooks.json: un error acá no rompe nada visiblemente — el hook
# simplemente no corre, que es el modo de falla más caro de todos.
hooks_json = ROOT / "hooks" / "hooks.json"
if hooks_json.is_file():
    try:
        conf = json.loads(hooks_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        conf = None
        errors.append(f"hooks/hooks.json: JSON inválido ({exc})")
    if isinstance(conf, dict):
        check("hooks" in conf, "hooks/hooks.json: falta la clave raíz 'hooks'")
        for event, entries in (conf.get("hooks") or {}).items():
            check(isinstance(entries, list), f"hooks/hooks.json: {event} no es una lista")
            for entry in entries if isinstance(entries, list) else []:
                check(bool(entry.get("matcher")), f"hooks/hooks.json: {event} sin matcher")
                inner = entry.get("hooks")
                check(isinstance(inner, list) and len(inner) > 0,
                      f"hooks/hooks.json: {event} sin array 'hooks'")
                for hook in inner if isinstance(inner, list) else []:
                    check(hook.get("type") == "command",
                          f"hooks/hooks.json: {event} con type != command")
                    cmd = hook.get("command", "")
                    for script in re.findall(r"\$\{CLAUDE_PLUGIN_ROOT\}/([\w./-]+)", cmd):
                        check((ROOT / script).is_file(),
                              f"hooks/hooks.json: el comando apunta a {script}, que no existe")
    elif conf is not None:
        errors.append("hooks/hooks.json: la raíz no es un objeto")

skills_dir = ROOT / "skills"
check(skills_dir.is_dir(), "falta el directorio skills/")
skill_dirs = sorted(d for d in skills_dir.iterdir() if d.is_dir()) if skills_dir.is_dir() else []
check(len(skill_dirs) > 0, "skills/ no contiene ninguna skill")

for d in skill_dirs:
    md = d / "SKILL.md"
    if not md.is_file():
        errors.append(f"skills/{d.name}: falta SKILL.md")
        continue
    text = md.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        errors.append(f"skills/{d.name}: SKILL.md sin frontmatter YAML")
        continue
    fm = m.group(1)
    name = re.search(r"^name:\s*(\S+)\s*$", fm, re.M)
    desc = re.search(r"^description:\s*(.+)$", fm, re.M)
    check(bool(name), f"skills/{d.name}: frontmatter sin name")
    check(bool(desc), f"skills/{d.name}: frontmatter sin description")
    if name:
        check(name.group(1) == d.name,
              f"skills/{d.name}: name '{name.group(1)}' no coincide con la carpeta")
    if desc:
        check(len(desc.group(1)) <= 1024,
              f"skills/{d.name}: description supera 1024 caracteres")
    for ref in re.findall(r"\]\((references/[^)]+)\)", text):
        check((d / ref).is_file(), f"skills/{d.name}: referencia rota {ref}")
    # Scripts mencionados: se resuelven contra esta skill, salvo que la mención
    # apunte explícitamente a la carpeta de otra (<carpeta-de-nube-skills-x>/).
    for owner, script in set(re.findall(r"(?:<carpeta-de-([\w-]+)>/)?(scripts/[\w./-]+\.py)", text)):
        base = d if owner in ("", "esta-skill", d.name) else skills_dir / owner
        check((base / script).is_file(),
              f"skills/{d.name}: script inexistente {base.name}/{script}")

# docs/handoff/: un link roto en el índice no da ningún error visible, solo deja al
# lector sin el capítulo. Se chequean los links relativos a otros archivos (las anclas
# no). Las plantillas se saltean: sus links son relativos al proyecto donde se copian.
handoff_dir = ROOT / "docs" / "handoff"
if handoff_dir.is_dir():
    for md in sorted(handoff_dir.rglob("*.md")):
        if "plantillas" in md.relative_to(handoff_dir).parts:
            continue
        text = md.read_text(encoding="utf-8")
        text = re.sub(r"```.*?```", "", text, flags=re.S)  # bloques de código
        text = re.sub(r"`[^`\n]*`", "", text)  # código inline
        for target in re.findall(r"\]\(([^)\s]+)\)", text):
            if target.startswith("#") or re.match(r"^[a-z][a-z0-9+.-]*:", target):
                continue  # ancla del mismo archivo o URL externa (https:, mailto:)
            path = target.split("#", 1)[0]
            check((md.parent / path).exists(),
                  f"{md.relative_to(ROOT)}: link roto {target}")

# commands/*.md: una ruta ${CLAUDE_PLUGIN_ROOT}/... que no existe recién falla cuando un
# dev corre el comando en un proyecto de verdad.
commands_dir = ROOT / "commands"
for cmd in sorted(commands_dir.glob("*.md")) if commands_dir.is_dir() else []:
    text = cmd.read_text(encoding="utf-8")
    for rel in sorted(set(re.findall(r"\$\{CLAUDE_PLUGIN_ROOT\}/([\w./-]+)", text))):
        rel = rel.rstrip(".")
        check((ROOT / rel).exists(),
              f"commands/{cmd.name}: ruta inexistente ${{CLAUDE_PLUGIN_ROOT}}/{rel}")

if errors:
    print("VALIDACIÓN FALLÓ:")
    for e in errors:
        print(f"  ✗ {e}")
    sys.exit(1)

print(f"OK: {len(skill_dirs)} skill(s) válidas y manifiestos correctos")
