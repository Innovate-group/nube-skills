#!/usr/bin/env python3
"""Valida la estructura del repo nube-skills.

Chequea: manifiestos JSON de .claude-plugin/, y para cada skills/<dir>:
SKILL.md presente, frontmatter con name (== carpeta) y description (<=1024),
y que toda referencia markdown a references/ exista.
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

if errors:
    print("VALIDACIÓN FALLÓ:")
    for e in errors:
        print(f"  ✗ {e}")
    sys.exit(1)

print(f"OK: {len(skill_dirs)} skill(s) válidas y manifiestos correctos")
