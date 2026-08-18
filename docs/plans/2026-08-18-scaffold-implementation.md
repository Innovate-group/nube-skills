# nube-skills — Plan de implementación: scaffold + migración + publicación

> **For agentic workers:** ejecutar tarea por tarea (subagente por tarea, o inline con checkpoints). Los pasos usan checkboxes (`- [ ]`) para tracking.

**Goal:** Dejar publicado `Innovate-group/nube-skills` (repo público) como plugin de Claude Code instalable por dos canales, con la skill `tiendanube-sectionable-themes` migrada como primera pieza del catálogo.

**Architecture:** Monorepo dual-canal: `skills/` en la raíz (escaneado por plugins de Claude Code y por el CLI de skills.sh) + `.claude-plugin/{plugin.json, marketplace.json}` (source `./`). Validación por script stdlib-only + GitHub Action.

**Tech Stack:** Git/GitHub (`gh` CLI), Python 3 stdlib (validador), GitHub Actions, Claude Code plugins, `npx skills` (vercel-labs/skills).

## Global Constraints

- Repo público desde el primer push: **nunca** commitear nombres de clientes, tokens, URLs internas ni el archivo `.nuvem`.
- Contenido en español; frontmatter de skills: solo `name` + `description` (description SIEMPRE entre comillas dobles — contiene `:`), máx. 1024 caracteres.
- Nombre del plugin y del marketplace: `nube-skills`. Org: `Innovate-group`. Versión inicial: `0.1.0`.
- Directorio de trabajo: `/Users/tonchi/Desktop/Innovate/nube-skills` (repo git ya inicializado en `main`, contiene `docs/plans/`).
- La copia personal `~/.claude/skills/tiendanube-sectionable-themes` NO se borra hasta que la instalación del plugin esté verificada (Tarea 7).

---

### Task 1: Manifiestos del plugin y .gitignore

**Files:**
- Create: `.claude-plugin/plugin.json`
- Create: `.claude-plugin/marketplace.json`
- Create: `.gitignore`

**Interfaces:**
- Produces: `plugin.json` con `name: "nube-skills"` y `version: "0.1.0"` (la Tarea 3 valida su JSON; el README de la Tarea 5 referencia el nombre `nube-skills@nube-skills`).

- [ ] **Step 1: Crear `.claude-plugin/plugin.json`**

```json
{
  "name": "nube-skills",
  "version": "0.1.0",
  "description": "Skills y comandos de Claude Code para el desarrollo y mantenimiento de temas sectionable de Tienda Nube (Ipanema, Fork Workflow)",
  "author": { "name": "Innovate Group" }
}
```

- [ ] **Step 2: Crear `.claude-plugin/marketplace.json`**

```json
{
  "name": "nube-skills",
  "owner": { "name": "Innovate Group" },
  "plugins": [
    {
      "name": "nube-skills",
      "source": "./",
      "description": "Skills y comandos para temas sectionable de Tienda Nube (Ipanema, Fork Workflow)"
    }
  ]
}
```

- [ ] **Step 3: Crear `.gitignore`**

```
.DS_Store
__pycache__/
*.pyc
```

- [ ] **Step 4: Verificar que ambos JSON parsean**

Run: `python3 -m json.tool .claude-plugin/plugin.json > /dev/null && python3 -m json.tool .claude-plugin/marketplace.json > /dev/null && echo JSON-OK`
Expected: `JSON-OK`

- [ ] **Step 5: Commit**

```bash
git add .claude-plugin .gitignore
git commit -m "feat: manifiestos de plugin y marketplace (nube-skills v0.1.0)"
```

---

### Task 2: Migrar la skill `tiendanube-sectionable-themes`

**Files:**
- Create: `skills/tiendanube-sectionable-themes/SKILL.md` (copia de `~/.claude/skills/tiendanube-sectionable-themes/SKILL.md`)
- Create: `skills/tiendanube-sectionable-themes/references/` (5 archivos .md, copia del mismo origen)

**Interfaces:**
- Produces: `skills/<nombre>/SKILL.md` — el layout que la Tarea 3 valida y que ambos canales de instalación escanean.

- [ ] **Step 1: Copiar la skill completa**

Run: `cp -R /Users/tonchi/.claude/skills/tiendanube-sectionable-themes /Users/tonchi/Desktop/Innovate/nube-skills/skills/`

- [ ] **Step 2: Verificar la copia (6 archivos, mismo contenido)**

Run: `find skills/tiendanube-sectionable-themes -type f | sort && diff -r /Users/tonchi/.claude/skills/tiendanube-sectionable-themes skills/tiendanube-sectionable-themes && echo COPIA-OK`
Expected: 6 rutas (SKILL.md + 5 references) y `COPIA-OK` (diff sin salida).

- [ ] **Step 3: Commit**

```bash
git add skills/
git commit -m "feat: migra la skill tiendanube-sectionable-themes como primera pieza del catálogo"
```

---

### Task 3: Validador `scripts/validate.py`

**Files:**
- Create: `scripts/validate.py`

**Interfaces:**
- Consumes: layout `skills/*/SKILL.md` (Tarea 2) y `.claude-plugin/*.json` (Tarea 1).
- Produces: exit code 0 (OK) / 1 (falla) con detalle por stderr-stdout — lo consume el workflow de la Tarea 4.

- [ ] **Step 1: Escribir `scripts/validate.py`** (stdlib only, sin pyyaml)

```python
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

if errors:
    print("VALIDACIÓN FALLÓ:")
    for e in errors:
        print(f"  ✗ {e}")
    sys.exit(1)

print(f"OK: {len(skill_dirs)} skill(s) válidas y manifiestos correctos")
```

- [ ] **Step 2: Correrlo sobre el repo (caso feliz)**

Run: `python3 scripts/validate.py`
Expected: `OK: 1 skill(s) válidas y manifiestos correctos` y exit 0.

- [ ] **Step 3: Verificar que detecta fallas (caso roto, en /tmp, sin tocar el repo)**

```bash
cp -R . /tmp/nube-skills-broken && rm /tmp/nube-skills-broken/skills/tiendanube-sectionable-themes/references/cli-workflow.md
python3 /tmp/nube-skills-broken/scripts/validate.py; echo "exit=$?"
rm -rf /tmp/nube-skills-broken
```

Expected: `VALIDACIÓN FALLÓ:` con `referencia rota references/cli-workflow.md` y `exit=1`.

- [ ] **Step 4: Commit**

```bash
git add scripts/validate.py
git commit -m "feat: validador de estructura de skills y manifiestos (stdlib only)"
```

---

### Task 4: GitHub Action de validación

**Files:**
- Create: `.github/workflows/validate.yml`

**Interfaces:**
- Consumes: `scripts/validate.py` (exit code).

- [ ] **Step 1: Crear `.github/workflows/validate.yml`**

```yaml
name: Validate skills

on:
  push:
    branches: [main]
  pull_request:

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Validar skills y manifiestos
        run: python3 scripts/validate.py
```

- [ ] **Step 2: Lint local del YAML**

Run: `python3 -c "import yaml,sys; yaml.safe_load(open('.github/workflows/validate.yml')); print('YAML-OK')" 2>/dev/null || npx --yes yaml-lint .github/workflows/validate.yml 2>/dev/null || echo "verificar YAML a ojo"`
Expected: `YAML-OK` (o verificación manual si no hay pyyaml local — el Action real se verifica en la Tarea 6 Step 3).

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/validate.yml
git commit -m "ci: valida skills y manifiestos en cada push y PR"
```

---

### Task 5: README, LICENSE y CHANGELOG

**Files:**
- Create: `README.md`
- Create: `LICENSE`
- Create: `CHANGELOG.md`

- [ ] **Step 1: Crear `README.md`**

```markdown
# nube-skills

Skills y comandos de [Claude Code](https://claude.com/claude-code) para el desarrollo y mantenimiento de temas **sectionable** de [Tienda Nube](https://tiendanube.dev) (tema base Ipanema, Fork Workflow). Mantenido por [Innovate Group](https://github.com/Innovate-group).

## Instalación

**Como plugin de Claude Code** (skills + comandos):

```
/plugin marketplace add Innovate-group/nube-skills
/plugin install nube-skills@nube-skills
```

**Solo las skills**, con el [CLI de skills.sh](https://skills.sh) (funciona en Claude Code, Cursor, Codex y 70+ agentes):

```bash
npx skills add Innovate-group/nube-skills
```

## Catálogo

| Pieza | Tipo | Estado | Descripción |
|---|---|---|---|
| `tiendanube-sectionable-themes` | skill | ✅ disponible | Contexto completo del modelo sectionable: arquitectura, sections/blocks/snippets, schema, CLI y Fork Workflow, con detección automática de generación de tema (nuevo / clásico / Shopify). |
| `tiendanube-figma-section` | skill | 🔜 en camino | De un nodo de Figma (desktop + mobile) a una section/block de Ipanema: triage re-estilizar vs. custom, `.tpl` + `{% schema %}` + traducciones + JSON template. |
| `/nube-skills:kickoff` | comando | 🔜 en camino | Arranque de un cliente nuevo: instalación Ipanema con el CLI, pull, git y checklist. |
| `tiendanube-i18n` | skill | 🔜 en camino | Auditoría y alta de claves de traducción en todos los locales. |
| `tiendanube-theme-qa` | skill | 🔜 en camino | QA visual de la implementación contra el boceto de Figma (desktop y mobile). |

## Requisitos

- Los flujos de CLI asumen [`@tiendanube/cli`](https://tiendanube.dev/themes/developer-tools/cli/overview) (Node 24.15+) y el Fork Workflow (hoy disponible solo para Ipanema).
- La skill de Figma requiere el [MCP oficial de Figma](https://developers.figma.com) conectado.

## Desarrollo

Cada skill vive en `skills/<nombre>/SKILL.md`. Antes de commitear: `python3 scripts/validate.py`. El CI valida lo mismo en cada push.

## Licencia

[MIT](LICENSE)
```

- [ ] **Step 2: Crear `LICENSE`** (MIT, texto estándar completo con `Copyright (c) 2026 Innovate Group` en la línea de copyright)

- [ ] **Step 3: Crear `CHANGELOG.md`**

```markdown
# Changelog

## 0.1.0 — 2026-08-18

- Scaffold del monorepo dual-canal (plugin de Claude Code + compatible con `npx skills add`).
- Primera skill del catálogo: `tiendanube-sectionable-themes` (modelo sectionable, Fork Workflow, detección de generación de tema).
- Validador de estructura (`scripts/validate.py`) y CI en GitHub Actions.
```

- [ ] **Step 4: Validar y commitear**

Run: `python3 scripts/validate.py`
Expected: `OK: 1 skill(s) válidas y manifiestos correctos`

```bash
git add README.md LICENSE CHANGELOG.md
git commit -m "docs: README (instalación dual-canal y catálogo), licencia MIT y changelog 0.1.0"
```

---

### Task 6: Crear el repo público en GitHub y push

**Files:**
- (sin archivos nuevos — publicación)

- [ ] **Step 1: Crear el repo en la org y pushear** ⚠️ *Acción pública e irreversible en la práctica — confirmar con el usuario antes de ejecutar.*

```bash
cd /Users/tonchi/Desktop/Innovate/nube-skills
gh repo create Innovate-group/nube-skills --public --source . --push \
  --description "Skills y comandos de Claude Code para temas sectionable de Tienda Nube (Ipanema, Fork Workflow)"
```

Expected: URL `https://github.com/Innovate-group/nube-skills` y push de `main` exitoso.

- [ ] **Step 2: Agregar topics para descubribilidad**

```bash
gh repo edit Innovate-group/nube-skills --add-topic tiendanube --add-topic claude-code --add-topic agent-skills --add-topic nuvemshop
```

- [ ] **Step 3: Verificar que el Action corrió verde**

Run: `gh run list --repo Innovate-group/nube-skills --limit 1`
Expected: workflow `Validate skills` con estado `completed success` (esperar ~1 min si está `in_progress`).

---

### Task 7: Verificar los dos canales de instalación

- [ ] **Step 1: Canal skills.sh — listar sin instalar**

Run: `npx --yes skills add Innovate-group/nube-skills --list`
Expected: lista que incluye `tiendanube-sectionable-themes`. (Esto NO siembra el índice todavía; la instalación real de un miembro del equipo lo hará.)

- [ ] **Step 2: Canal plugin — instalación real (interactivo, lo hace el usuario)**

En una sesión interactiva de Claude Code:
```
/plugin marketplace add Innovate-group/nube-skills
/plugin install nube-skills@nube-skills
```
Expected: el plugin instala sin errores y la skill `tiendanube-sectionable-themes` aparece disponible en una sesión nueva.

- [ ] **Step 3: Smoke test de disparo**

En un proyecto cualquiera, pedir: *"creá una section hero para un tema sectionable de Tienda Nube"*.
Expected: se invoca la skill del plugin y su Paso 0 de detección se ejecuta primero.

---

### Task 8: Limpieza post-verificación (solo tras Task 7 OK)

- [ ] **Step 1: Borrar la copia personal duplicada**

Run: `rm -rf /Users/tonchi/.claude/skills/tiendanube-sectionable-themes`
(La versión canónica pasa a ser la del plugin.)

- [ ] **Step 2: Avisar al equipo**

Mensaje al equipo: quien instaló la skill por zip (`~/.claude/skills/tiendanube-sectionable-themes`) debe borrarla e instalar el plugin con los dos comandos del README. El `.skill` del Escritorio queda obsoleto.

- [ ] **Step 3: Commit final del plan actualizado (checkboxes marcados)**

```bash
git add docs/plans/
git commit -m "docs: plan de scaffold ejecutado"
```
