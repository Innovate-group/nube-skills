# Handoff en el plugin + kickoff que lo instala — Plan de implementación

> **Para agentes:** ejecutar tarea por tarea, con un subagente por tarea (herramienta Agent)
> o inline con un checkpoint al final de cada una. Los pasos usan checkboxes (`- [ ]`). Las
> tareas 4 a 9 son independientes entre sí y pueden correr en paralelo.

**Goal:** Publicar en nube-skills 1.5.0 un handoff de Ipanema partido por tema, con todo lo
aprendido en María Cher, Garçon García y VZ, y un `/nube-skills:kickoff` que lo copie a cada
proyecto nuevo y arme `.claude/CLAUDE.md` desde una plantilla.

**Architecture:** El handoff es markdown en `docs/handoff/`: 16 capítulos, un README-índice y
tres plantillas. El kickoff lo copia con `${CLAUDE_PLUGIN_ROOT}`, que Claude Code expande en
el cuerpo de un comando. `validate.py` suma dos chequeos que corren en la CI: links del
handoff y rutas `${CLAUDE_PLUGIN_ROOT}/…` de los comandos. Un checker de contenido que vive
en el scratchpad (no se versiona) valida cada capítulo mientras se escribe.

**Tech Stack:** Markdown; Python 3 stdlib (`validate.py` y el checker); Claude Code plugins
(`commands/`, `${CLAUDE_PLUGIN_ROOT}`, `claude --plugin-dir`).

**Spec:** [`2026-09-30-handoff-y-kickoff-design.md`](2026-09-30-handoff-y-kickoff-design.md).
Leelo antes de cualquier tarea: define la estructura, las reglas editoriales y la tabla de
resolución de contradicciones.

## Global Constraints

- Directorio de trabajo: `/Users/tonchi/Desktop/Innovate/nube-skills`.
- `SCRATCH=/private/tmp/claude-501/-Users-tonchi-Desktop-Innovate-nube-skills/a71dff5f-b6ae-4c53-8c45-a76a040c7994/scratchpad`.
- **Commits: ninguno sin pedido explícito del dev.** Ninguna tarea commitea. La Task 16
  propone la agrupación y espera la orden. Los commits dentro de repos de prueba en
  `$SCRATCH` sí se permiten, porque son descartables.
- `python3 scripts/validate.py` tiene que pasar al final de toda tarea que toque el repo. En
  las tareas 4 a 11 puede fallar **solo** por links a capítulos que todavía no existen.
- **Idioma y voz:** español rioplatense, voz genérica ("en un tema Ipanema…"). Los casos
  concretos van como ejemplo con su fuente: `[MC 2026-09-17]`, `[GG 2026-09-23]`,
  `[VZ 2026-09-24]`. MC es María Cher (Argentina, más sus temas de Chile y Uruguay), GG es
  Garçon García y VZ es VZ.
- **Marcas:**
  - ✅ medido, **siempre** con `[proyecto fecha]`;
  - ⚠️ trampa;
  - 🔥 rompió algo en producción;
  - 🚫 no se puede, o no hay que hacerlo;
  - ❓ medido distinto en dos proyectos, **siempre** con cómo re-medirlo;
  - sin marca: criterio.
- **Formato de cada capítulo:**
  - la primera línea es `# Título`;
  - después va `## Lo esencial`, con 5 a 7 viñetas;
  - el resto, secciones `##` por tema;
  - snippets de código cortos, y solo cuando la regla es una forma de código.
- **Cada hecho vive en un solo capítulo.** Los demás lo linkean al archivo, sin ancla
  (`[Twig](07-twig.md)`) y nombrando la sección en el texto.
- **El repo es público.** Los nombres de clientes van (decisión del 2026-09-30). **Nunca van:**
  - tokens, contraseñas ni ids de tienda, instalación o app;
  - emails ni datos de clientes finales;
  - URLs de servicios internos del estudio: el servidor de prototipos se nombra "el servidor
    de prototipos del estudio" y nubefiles, "el servicio de archivos del estudio".
- **Las cifras que dependen de la instalación** (cantidad de archivos, líneas de
  `store.js`) aparecen como ejemplo, nunca como el valor esperado.
- **Solo lo que se puede rastrear.** Todo lo que se escribe sale de:
  - el handoff viejo: `/Users/tonchi/Desktop/Innovate/vz-tiendanube-theme/.docs/HANDOFF-IPANEMA.md`;
  - los siete análisis en `$SCRATCH/reports/`: `mc-claude-1.md`, `mc-claude-2.md`,
    `mc-claude-3-commits.md`, `mc-memorias-hermanos-apps.md`, `garcon-garcia.md`, `vz.md` y
    `skills-uso-real.md`. Casi todos están organizados por sección del handoff viejo (`§N`)
    y cada hallazgo cita su fuente;
  - las fuentes originales, para verificar lo dudoso:
    - `/Users/tonchi/Desktop/Innovate/maria-cher-tiendanube-theme/CLAUDE.md`;
    - `/Users/tonchi/Desktop/Innovate/garcon-garcia-theme/CLAUDE.md` y su `.docs/`;
    - `/Users/tonchi/Desktop/Innovate/vz-tiendanube-theme/.claude/CLAUDE.md` y `.docs/ui-kit.md`;
    - las memorias en `~/.claude/projects/-Users-tonchi-Desktop-Innovate-{maria-cher,garcon-garcia,vz}-tiendanube-theme/memory/`
      (el de GG es `…-garcon-garcia-theme/memory/`).

  Si `$SCRATCH/reports/` no existe, se trabaja directo sobre las fuentes originales.
- **Contradicciones:** se aplica la tabla "Resolución de contradicciones" del spec. Si
  aparece una nueva, gana la medición más reciente; si no se puede decidir, va con ❓.
- **No se copian estos errores de las fuentes** (la lista está en el spec, "Reglas
  editoriales"):
  - `theme push --force -v` para depurar;
  - el precedente de `replace({...})` en `breadcrumbs.tpl` de GG;
  - el diagnóstico de `.js-ship-free-min` de GG;
  - "los patches entran limpio";
  - "el `es` neutro está en voseo";
  - "el preview no toma el `settings_data.json` que sube el CLI";
  - el bloque `look-products`.
- **Solo lectura sobre los proyectos de clientes.** Nada de CLI de tiendanube, git que
  escriba ni navegadores sobre ellos.

---

### Task 1: `validate.py` — links del handoff y rutas de los comandos

**Files:**
- Modify: `scripts/validate.py` (insertar antes de `if errors:`, hoy en la línea ~99)
- Test: fixture descartable en `$SCRATCH/validate-fixture/`

**Interfaces:**
- Produces: dos chequeos nuevos que corren en toda validación. Los mensajes de error tienen
  este formato exacto:
  - `docs/handoff/<archivo>: link roto <destino>`
  - `commands/<archivo>: ruta inexistente ${CLAUDE_PLUGIN_ROOT}/<ruta>`

  Los archivos de `docs/handoff/plantillas/` se saltean, porque sus links son relativos al
  lugar donde se van a copiar.

- [ ] **Step 1: Armar el fixture con dos errores y un falso positivo que no debe saltar**

````bash
SCRATCH=/private/tmp/claude-501/-Users-tonchi-Desktop-Innovate-nube-skills/a71dff5f-b6ae-4c53-8c45-a76a040c7994/scratchpad
F=$SCRATCH/validate-fixture
rm -rf "$F" && mkdir -p "$F" && cp -R /Users/tonchi/Desktop/Innovate/nube-skills/{.claude-plugin,hooks,skills,scripts,commands} "$F"/
mkdir -p "$F/docs/handoff/plantillas"
cat > "$F/docs/handoff/README.md" <<'MD'
# Prueba
[existe](01-a.md) · [roto](no-existe.md) · [externo](https://example.com) · [ancla](#x)
`arr[0](b)` en código inline no es un link.
```js
fn[0](otra)
```
MD
echo "# A" > "$F/docs/handoff/01-a.md"
echo "[relativo al destino](../.docs/handoff/README.md)" > "$F/docs/handoff/plantillas/CLAUDE.md"
printf 'Leé ${CLAUDE_PLUGIN_ROOT}/docs/handoff/README.md y ${CLAUDE_PLUGIN_ROOT}/docs/handoff/nada.md.\n' > "$F/commands/probe.md"
````

- [ ] **Step 2: Correr la versión actual y confirmar que no ve nada**

Run: `python3 "$F/scripts/validate.py"`
Expected: `OK: 5 skill(s) válidas y manifiestos correctos`. Prueba que hoy esos errores pasan
sin que nadie se entere.

- [ ] **Step 3: Implementar los dos chequeos en `scripts/validate.py`**, justo antes de `if errors:`:

```python
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
```

- [ ] **Step 4: Correr la versión nueva sobre el fixture y ver exactamente los dos errores**

Run: `cp /Users/tonchi/Desktop/Innovate/nube-skills/scripts/validate.py "$F/scripts/" && python3 "$F/scripts/validate.py"; echo "exit $?"`

Expected:
```
VALIDACIÓN FALLÓ:
  ✗ docs/handoff/README.md: link roto no-existe.md
  ✗ commands/probe.md: ruta inexistente ${CLAUDE_PLUGIN_ROOT}/docs/handoff/nada.md
exit 1
```

No tienen que aparecer `b`, `otra` ni nada de `plantillas/`.

- [ ] **Step 5: Arreglar el fixture y confirmar que queda en verde**

Run: `echo "# N" > "$F/docs/handoff/no-existe.md" && echo "# N" > "$F/docs/handoff/nada.md" && python3 "$F/scripts/validate.py"`
Expected: `OK: 5 skill(s) válidas y manifiestos correctos`

- [ ] **Step 6: Correr la validación sobre el repo real**

Run: `cd /Users/tonchi/Desktop/Innovate/nube-skills && python3 scripts/validate.py`
Expected: `OK: 5 skill(s) válidas y manifiestos correctos`. Todavía no hay `docs/handoff/` y
`kickoff.md` no usa `${CLAUDE_PLUGIN_ROOT}`.

- [ ] **Step 7: Actualizar el docstring de `validate.py`**

Agregar a la lista de "Chequea:" del docstring: `los links relativos de docs/handoff/ (sin
plantillas/) y que las rutas ${CLAUDE_PLUGIN_ROOT}/... citadas en commands/*.md existan`.

---

### Task 2: Checker de contenido del handoff (scratchpad, no se versiona)

**Files:**
- Create: `$SCRATCH/check_handoff.py`

**Interfaces:**
- Produces: `python3 $SCRATCH/check_handoff.py <docs/handoff> [--files A.md B.md] [--mapping]`.
  - Exit 0 = sin errores, aunque puede haber avisos. Exit 1 = hay errores.
  - La última línea siempre es `<N> errores, <M> avisos`.
  - Lo usan las tareas 4 a 12.

- [ ] **Step 1: Escribir el checker**

```python
#!/usr/bin/env python3
"""Chequeos de contenido del handoff de nube-skills (herramienta de trabajo: no se versiona).

Uso:
  python3 check_handoff.py <docs/handoff> [--files 07-twig.md 10-css.md] [--mapping]

Errores (exit 1): datos sensibles, capítulo sin título '# ' o sin '## Lo esencial',
marcadores TODO/TBD/FIXME y, con --mapping, frases ancla que no aparecen en su capítulo.
Avisos: ✅ sin [proyecto fecha], ❓ sin cómo re-medir, cadenas largas tipo token.
Los valores sensibles se leen de las fuentes en runtime y NUNCA se imprimen.
"""
import argparse
import base64
import json
import re
import sys
from pathlib import Path

INNOVATE = Path("/Users/tonchi/Desktop/Innovate")
PROJECTS = ["maria-cher-tiendanube-theme", "mariacher-tiendanube-theme-chile",
            "mariacher-tiendanube-theme-uruguay", "garcon-garcia-theme",
            "vz-tiendanube-theme"]
MEMORIES = Path.home() / ".claude" / "projects"

# (regex, capítulo): frases del handoff viejo y de lo nuevo que tienen que terminar en el
# capítulo que les asignó el spec. Si una falta, se perdió algo en la redistribución.
MAPPING = [
    (r"Download completed", "05-modelo-y-cli.md"),
    (r"revision_token", "05-modelo-y-cli.md"),
    (r"unfork", "05-modelo-y-cli.md"),
    (r"region=br", "05-modelo-y-cli.md"),
    (r"preview_theme_installation_id", "05-modelo-y-cli.md"),
    (r"eliminaciones", "03-sync-y-reglas.md"),
    (r"push --force", "03-sync-y-reglas.md"),
    (r"theme diff", "03-sync-y-reglas.md"),
    (r"--stamp", "03-sync-y-reglas.md"),
    (r"2026-09-23", "03-sync-y-reglas.md"),
    (r"git add -A", "03-sync-y-reglas.md"),
    (r"setting_type", "06-schema-y-traducciones.md"),
    (r"visible_if", "06-schema-y-traducciones.md"),
    (r"es_AR", "06-schema-y-traducciones.md"),
    (r"json_decode", "07-twig.md"),
    (r"attribute\(", "07-twig.md"),
    (r"next_video", "07-twig.md"),
    (r"loop\.index", "07-twig.md"),
    (r"js-nubesdk-slot", "08-plataforma.md"),
    (r"block_attributes", "08-plataforma.md"),
    (r"g-recaptcha", "08-plataforma.md"),
    (r"X-Requested-With", "08-plataforma.md"),
    (r"_cart-item\.tpl", "09-producto-carrito-busqueda.md"),
    (r"js-ajax-cart-list", "09-producto-carrito-busqueda.md"),
    (r"no-photo", "09-producto-carrito-busqueda.md"),
    (r"details-content", "10-css.md"),
    (r"scrollbar-width", "10-css.md"),
    (r"1023", "10-css.md"),
    (r"slidePrev", "11-javascript.md"),
    (r"homePopup", "11-javascript.md"),
    (r"getUrlParams", "11-javascript.md"),
    (r"Draft", "12-plantillas.md"),
    (r"32 KB|32\.425", "12-plantillas.md"),
    (r"extra\[", "13-limites-y-admin-api.md"),
    (r"stocknube", "13-limites-y-admin-api.md"),
    (r"[Ww]ishlist", "13-limites-y-admin-api.md"),
    (r"section-visibility", "14-patrones.md"),
    (r"node --check", "15-verificacion-y-qa.md"),
    (r"harness", "15-verificacion-y-qa.md"),
    (r"format-patch", "16-multipais-apps-integraciones.md"),
    (r"renderVals", "04-diseno-y-ui-kit.md"),
    (r"[Bb]ocetos por secci", "04-diseno-y-ui-kit.md"),
    (r"nube-skills-themes", "02-skills.md"),
    (r"/hooks", "02-skills.md"),
    (r"theme authorize", "01-arranque.md"),
    (r"kickoff", "01-arranque.md"),
    (r"más caros", "README.md"),
]

ALWAYS_BAD = [
    (r"\b\d{7,9}\b", "número de 7 a 9 dígitos (¿id de tienda, instalación o app?)"),
    (r"[\w.+-]+@[\w-]+\.[a-z]{2,}", "email"),
    (r"https?://[^\s)`]*innovategroup", "URL de un servicio interno del estudio"),
    (r"publicApiToken\s*[:=]", "valor del token del CLI"),
]
PLACEHOLDERS = r"\b(TODO|TBD|FIXME)\b"
TOKENISH = r"\b[A-Za-z0-9+/_-]{32,}={0,2}"
PROV = r"\[(MC|GG|VZ)[^\]]*\d{4}-\d{2}"
REMEASURE = r"re-?medi|cómo medir|para medir|medirlo"


def secret_values():
    """Tokens, ids y la contraseña conocida, leídos de las fuentes. Nunca se imprimen."""
    vals = set()
    for name in PROJECTS:
        root = INNOVATE / name
        nuvem = root / ".nuvem"
        if nuvem.is_file():
            try:
                api = json.loads(base64.b64decode(nuvem.read_text().strip())).get("theme-api", {})
                vals.update(str(api[k]) for k in ("publicApiToken", "storeId", "themeId") if api.get(k))
            except (ValueError, OSError):
                pass
        manifest = root / "manifest.json"
        if manifest.is_file():
            try:
                tid = json.loads(manifest.read_text()).get("theme_id")
                if tid:
                    vals.add(str(tid))
            except (ValueError, OSError):
                pass
    for mem in MEMORIES.glob("*/memory/contrasena*.md"):
        for v in re.findall(r"`([A-Za-z0-9]{8,})`", mem.read_text(encoding="utf-8")):
            if re.search(r"\d", v) and re.search(r"[A-Za-z]", v):
                vals.add(v)
    return sorted(v for v in vals if len(v) >= 6)


def blocks(text):
    """Cada viñeta o párrafo es un bloque (una viñeta puede ocupar varias líneas)."""
    out, cur = [], []
    for line in text.splitlines():
        if (re.match(r"^\s*([-*]|\d+\.)\s", line) or not line.strip()) and cur:
            out.append("\n".join(cur))
            cur = []
        if line.strip():
            cur.append(line)
    if cur:
        out.append("\n".join(cur))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("handoff")
    ap.add_argument("--files", nargs="*")
    ap.add_argument("--mapping", action="store_true")
    a = ap.parse_args()
    root = Path(a.handoff).resolve()
    targets = [root / f for f in a.files] if a.files else sorted(root.rglob("*.md"))
    errors, warns = [], []
    secrets = secret_values()
    for p in targets:
        rel = p.relative_to(root)
        if not p.is_file():
            errors.append(f"{rel}: no existe")
            continue
        text = p.read_text(encoding="utf-8")
        lines = text.splitlines()
        for i, line in enumerate(lines, 1):
            for n, s in enumerate(secrets, 1):
                if s in line:
                    errors.append(f"{rel}:{i}: valor sensible #{n} de las fuentes")
            for rx, why in ALWAYS_BAD:
                if re.search(rx, line):
                    errors.append(f"{rel}:{i}: {why}")
            if re.search(TOKENISH, line):
                warns.append(f"{rel}:{i}: cadena larga tipo token o hash, revisar")
        if "plantillas" in rel.parts:
            continue  # llevan marcadores «…» y no son capítulos
        if not lines or not lines[0].startswith("# "):
            errors.append(f"{rel}: la primera línea no es un título '# '")
        if p.name != "README.md" and "## Lo esencial" not in text:
            errors.append(f"{rel}: falta '## Lo esencial'")
        for i, line in enumerate(lines, 1):
            if re.search(PLACEHOLDERS, line):
                errors.append(f"{rel}:{i}: marcador pendiente")
        for b in blocks(re.sub(r"```.*?```", "", text, flags=re.S)):
            if b.lstrip().startswith("|"):
                continue
            first = b.splitlines()[0][:80]
            if "✅" in b and not re.search(PROV, b):
                warns.append(f"{rel}: ✅ sin [proyecto fecha]: {first}")
            if "❓" in b and not re.search(REMEASURE, b):
                warns.append(f"{rel}: ❓ sin cómo re-medir: {first}")
    if a.mapping:
        names = {p.name for p in targets}
        for rx, fname in MAPPING:
            if a.files and fname not in names:
                continue
            f = root / fname
            if not f.is_file() or not re.search(rx, f.read_text(encoding="utf-8")):
                errors.append(f"mapeo: /{rx}/ no aparece en {fname}")
    for w in warns:
        print("  ⚠", w)
    for e in errors:
        print("  ✗", e)
    print(f"{len(errors)} errores, {len(warns)} avisos")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Probarlo contra un capítulo falso con cada tipo de error**

```bash
T=$SCRATCH/checker-test && rm -rf "$T" && mkdir -p "$T"
cat > "$T/07-twig.md" <<'MD'
Sin título.
- ✅ Medido sin fuente.
- ❓ Dudoso sin nada más.
- TODO completar. Store 1234567. Mail dev@example.com.
MD
python3 $SCRATCH/check_handoff.py "$T" --files 07-twig.md --mapping; echo "exit $?"
```

Expected: exit 1, con estos errores:
- `la primera línea no es un título`
- `falta '## Lo esencial'`
- `marcador pendiente`
- `número de 7 a 9 dígitos`
- `email`
- `mapeo: /json_decode/ no aparece en 07-twig.md` (y el resto de los mapeos de `07-twig.md`)

Y dos avisos: `✅ sin [proyecto fecha]` y `❓ sin cómo re-medir`.

- [ ] **Step 3: Confirmar que las fuentes aportan valores sensibles, sin imprimirlos**

Run: `python3 -c "import importlib.util,sys; s=importlib.util.spec_from_file_location('c','$SCRATCH/check_handoff.py'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); print(len(m.secret_values()), 'valores sensibles cargados')"`

Expected: un número **mayor que 0**. Tiene que haber como mínimo los tokens y los ids de los
`.nuvem` de los cinco temas.

---

### Task 3: Plantillas (CLAUDE.md del proyecto, ui-kit.md, skill de ui-kit)

**Files:**
- Create: `docs/handoff/plantillas/CLAUDE.md`
- Create: `docs/handoff/plantillas/ui-kit.md`
- Create: `docs/handoff/plantillas/ui-kit-skill/SKILL.md`

**Interfaces:**
- Produces:
  - la plantilla que usa el kickoff (Task 13, paso 6). Los marcadores van entre `«` y `»`,
    que no chocan con Twig (`{{ }}`) ni con HTML (`< >`). Un `CLAUDE.md` completo no contiene
    `«`;
  - los encabezados `## UI-kit` y `## Bocetos por sección` exactos, que son contrato con
    `nube-skills-section` y `nube-skills-qa`;
  - las tres plantillas, que las citan `01-arranque.md` y `04-diseno-y-ui-kit.md`.

- [ ] **Step 1: Escribir `docs/handoff/plantillas/CLAUDE.md`**

````markdown
# «Cliente» — Tema Tienda Nube (Ipanema, sectionable)

Tema de «cliente», construido sobre **Ipanema**, el tema base sectionable de Tienda Nube, con
el **Fork Workflow** del CLI. No hay build, lint ni tests: el tema es Twig + CSS + JS que la
plataforma sirve tal cual.

El contexto técnico está en **[`.docs/handoff/`](../.docs/handoff/README.md)**, copiado de
nube-skills «versión-del-plugin» el «fecha-del-kickoff». Esa copia no se edita: acá va solo
lo propio de este proyecto, y lo genérico que se aprenda vuelve a nube-skills.

⚠️ **Este archivo vive en `.claude/CLAUDE.md` a propósito.** La documentación del proyecto va
en carpetas con punto (`.claude/`, `.docs/`) para que ninguna versión del CLI la suba al CDN
del tema.

## Estado de la instalación (medido el «fecha-del-kickoff»)

Tienda: «url-de-la-tienda» · instalación vinculada: **«id-de-la-instalación»**
(`tiendanube theme current`).

| id | título | base | prod | fork |
|---|---|---|---|---|
| «una fila por instalación, de `tiendanube theme list`» | | | | |

- **Preview sin login:** `«https://dominio»/?preview_theme_installation_id=«id-de-la-instalación»`.
  Responde sin sesión y muestra lo **guardado** en el editor, no lo elegido sin guardar.
- **Quién pushea:** «el dev, con `tiendanube theme watch` en su terminal». Con watch
  prendido, **cada archivo que se guarda se publica** en la instalación.
- **Fork:** «sí, desde el AAAA-MM-DD | pendiente | no».
- **Locales:** «…» · **Tiendas hermanas:** «ninguna | país → repo» · **Dominio propio:** «…»

## Entorno

- CLI «salida de `tiendanube --version`» con Node «versión». Siempre **`tiendanube`, nunca
  `nuvemshop`**: `nuvemshop` manda `region=br` al autorizar.
- `.nuvem` es la credencial del CLI: nunca se commitea ni se imprime.

## Reglas del equipo

- 🚫 El agente nunca corre `theme push`, `theme watch`, `theme publish` ni `theme fork`.
- 🚫 Nunca crear una rama de git sin permiso explícito.
- 🚫 Cada commit y cada push se piden explícitamente, y deshacer también.
- 🚫 Nunca `git add -A`: se stagea por archivo.
- 🚫 No esconder con un `{% if %}` contenido que cargó el comerciante: se diseña ese estado.
- ✅ Toda section nueva se registra en el JSON de su página con contenido real y visible.
- 🔥 Twig de Tienda Nube: solo formas con precedente en el tema (`.docs/handoff/07-twig.md`).

## Protocolo de sync (antes de tocar un JSON del comerciante)

`templates/**` y `config/settings_data.json` los edita el comerciante desde el editor, y
`theme push` sincroniza eliminaciones. Detalle en `.docs/handoff/03-sync-y-reglas.md`.

```bash
git status --porcelain                      # 1 · algo sin commitear → commit o stash
ps -Ao pid,command | grep "cli.js theme"    # 2 · ¿hay watch? → nunca theme pull en esta carpeta
# 3 · estado del servidor: pull a un temporal (copiando .nuvem + manifest.json, con -y)
#     o `tiendanube theme diff --detailed`; comparar los JSON parseados
# 4 · lo que cambió el comerciante se commitea aparte, antes de editar encima
SC="$(ls -d ~/.claude/plugins/cache/nube-skills/nube-skills/*/ | sort -V | tail -1)skills/nube-skills-themes/scripts/sync-check.py"
python3 "$SC" . --stamp                     # 5 · registrar el sync para el hook del plugin
```

## Comandos de verificación

```bash
# cada {% schema %} parsea como JSON (línea de base «fecha-del-kickoff»: «N» OK, 0 rotos)
python3 - <<'PY'
import re, json, glob
for f in glob.glob('sections/*.tpl') + glob.glob('blocks/*.tpl'):
    m = re.search(r'\{%\s*schema\s*%\}(.*?)\{%\s*endschema\s*%\}', open(f).read(), re.S)
    if not m: continue
    try: json.loads(m.group(1))
    except Exception as e: print('SCHEMA ROTO', f, e)
PY

node --check static/js/store.js

# traducciones (línea de base: «N» faltantes heredadas de Ipanema, no son regresiones)
python3 "$(ls -d ~/.claude/plugins/cache/nube-skills/nube-skills/*/ | sort -V | tail -1)skills/nube-skills-i18n/scripts/audit-i18n.py" .
```

Archivos en el servidor al arrancar: **«N»**, sin contar `manifest.json`. Los chequeos de
comentarios Twig y de comentarios CSS están en `.docs/handoff/15-verificacion-y-qa.md`.

## Fuentes de diseño

«Figma: archivo y página del ui-kit | Prototipo HTML: URL del prototipo y del design system |
Sin diseño: el sistema visual son los tokens del tema»

## UI-kit

Sistema visual del rediseño. **`nube-skills-section` lee esta tabla en cada sección que
construye**: no borrarla ni renombrar el encabezado.

| Nodo | Link | Resumen |
|---|---|---|
| Colores / paleta | «link, ancla o `pendiente`» | |
| Tipografías / escala | «link, ancla o `pendiente`» | |
| Botones | «link, ancla o `pendiente`» | |
| Formularios / inputs | «link, ancla o `pendiente`» | |
| Cards / product card | «link, ancla o `pendiente`» | |
| Iconografía | «link, ancla o `pendiente`» | |
| Espaciados / grid | «link, ancla o `pendiente`» | |

## Bocetos por sección

Se completa sobre la marcha: cada sección construida anota su referencia de diseño y el código
que la implementa. `nube-skills-qa` la usa para el QA visual: no renombrar el encabezado.

| Sección | Desktop | Mobile | Código |
|---|---|---|---|

## Skills del proyecto

Vienen del plugin **nube-skills**: no se instalan en el repo. Cómo se usa cada una, con sus
problemas conocidos: `.docs/handoff/02-skills.md`.

| Skill | Para qué |
|---|---|
| `nube-skills-themes` | CLI, Fork Workflow, sync, arquitectura. No se carga sola: `/nube-skills:nube-skills-themes` |
| `nube-skills-section` | construir sections y blocks desde el diseño o sin boceto |
| `nube-skills-qa` | QA visual contra la referencia de diseño |
| `nube-skills-i18n` | auditar y completar traducciones |
| `nube-skills-admin` | datos de la tienda por la Admin API |
````

- [ ] **Step 2: Escribir `docs/handoff/plantillas/ui-kit.md`**

````markdown
# UI-kit de «cliente»

Referencia completa del sistema visual: valores, anomalías y por qué. La skill de proyecto
`«cliente»-ui-kit` dice **cómo usarlo**; este archivo guarda el detalle. Se lee por sección,
no entero.

## Fuentes y cuál manda

| Fuente | Rol |
|---|---|
| «design system / nodos del ui-kit» | tokens con nombre |
| «boceto / prototipo» | cómo se ve cada pieza, desktop y mobile |
| «notas de diseño» | qué ajustar, construir o verificar por sección |

Un valor que la fuente de tokens nombra sale del token. Lo que no define se mide en el boceto.
Si se contradicen, se anota como anomalía y se pregunta: no se resuelve por cuenta propia.

## Anomalías

Contradicciones entre fuentes, valores fuera de paleta, fuentes que no están en el font
picker. Van numeradas para poder citarlas desde el `CLAUDE.md` y el código. Cada una lleva su
decisión provisoria hasta que diseño la confirme, y la fecha en que se resolvió.

| # | Qué | Decisión | Estado |
|---|---|---|---|
| A1 | «…» | «…» | abierta |

## Colores

| Token | Valor | Uso | Origen |
|---|---|---|---|

## Tipografía

## Botones

## Formularios

## Card de producto

## Iconografía

## Espaciados, grilla y breakpoints

## Animaciones

## Remapeo de los tokens del tema base

Qué token de Ipanema pasa a qué valor del kit, al final de `layouts/resources/style-tokens.tpl`
(`--border-radius`, `--transition-*`, `--gutter-container`, `--spacing-section`,
`--h1`…`--h6`, los colores semánticos). Remapearlos corrige cientos de reglas del base sin
tocarlas.

| Token del base | Valor del kit | Por qué |
|---|---|---|

## Verificado en vivo

Lo medido en la preview contra la fuente, con fecha.
````

- [ ] **Step 3: Escribir `docs/handoff/plantillas/ui-kit-skill/SKILL.md`**

````markdown
---
name: «cliente»-ui-kit
description: "Sistema visual de «cliente» para este tema de Tienda Nube (Ipanema). Usar ANTES de escribir o revisar CSS, markup o defaults de schema de cualquier section, block, snippet o componente de «cliente» — colores, tipografía, botones, inputs, card de producto, íconos, espaciados, breakpoints, animaciones — para usar los tokens y las clases del kit en vez de valores sueltos o defaults de Ipanema. Triggers: «cliente», ui kit, design system, tokens, paleta, tipografía, botón, input, maquetar sección."
---

# UI-kit de «cliente»

El sistema visual ya está implementado en el tema. Esta skill dice **cómo usarlo** al construir
o corregir cualquier pieza. La referencia completa está en **`.docs/ui-kit.md`**: leé ahí solo
la sección que tu componente necesite.

## Fuentes y cuál manda

«qué fuente da los tokens, cuál da las piezas y cuál da el alcance; qué hacer si se contradicen»

## Reglas que no se negocian

1. Nunca un hex, un `ease`, un radio ni una `font-family` sueltos: todo sale de `--«prefijo»-*`
   o de los tokens del base que el kit ya remapeó.
2. «breakpoint del kit, curva única, hover, tipografía, íconos…»

## Tokens de uso diario

| Para | Token |
|---|---|

## Componentes que ya existen: reusalos, no los rehagas

| Necesitás | Usá |
|---|---|

Esta tabla crece con cada página construida.

## Dónde se escribe

- **Tokens nuevos** → `layouts/resources/style-tokens.tpl`, § «cliente», y una fila en
  `.docs/ui-kit.md`.
- **Estilos de componente** → junto a la regla que pisan. `style-async.css` carga después que
  `style-critical.css`: antes de pisar algo, buscá en qué hoja vive.

## Antes de dar por terminada una pieza

- [ ] Ningún valor suelto: `grep -nE '#[0-9a-fA-F]{3,6}\b|\bease\b|border-radius: *[1-9]|font-family' <archivos>`.
- [ ] Mobile y desktop medidos contra la fuente en la preview.
- [ ] Toda decisión sobre algo que la fuente no define, anotada en `.docs/ui-kit.md`.
- [ ] La fila de la sección en `## Bocetos por sección` del `CLAUDE.md`.
- [ ] Si se cerró una anomalía, actualizada acá y en `.docs/ui-kit.md`.
````

- [ ] **Step 4: Verificar**

Run: `python3 $SCRATCH/check_handoff.py docs/handoff --files plantillas/CLAUDE.md plantillas/ui-kit.md plantillas/ui-kit-skill/SKILL.md && python3 scripts/validate.py`

Expected:
- el checker: `0 errores`. A las plantillas solo se les aplica el chequeo de datos sensibles;
- `validate.py`: `OK: …`, porque se saltea `plantillas/`;
- además, `grep -c '«' docs/handoff/plantillas/CLAUDE.md` tiene que dar más que 0 (los
  marcadores están).

---

### Task 4: Capítulos `05-modelo-y-cli.md` y `12-plantillas.md`

**Files:**
- Create: `docs/handoff/05-modelo-y-cli.md`
- Create: `docs/handoff/12-plantillas.md`

**Interfaces:**
- Consumes: el spec ("Contenido por archivo", "Reglas editoriales", "Resolución de
  contradicciones"), el handoff viejo y los reportes (ver Global Constraints).
- Produces: los dos capítulos. Otros los linkean por nombre de archivo.

- [ ] **Step 1: Confirmar que el checker falla**

Run: `python3 $SCRATCH/check_handoff.py docs/handoff --files 05-modelo-y-cli.md 12-plantillas.md --mapping`
Expected: exit 1, con `05-modelo-y-cli.md: no existe` y `12-plantillas.md: no existe`.

- [ ] **Step 2: Reunir el material**

- Del handoff viejo: §1 (líneas 37–104), §2 (106–270) y §10 (1152–1232).
- De cada reporte en `$SCRATCH/reports/`: los hallazgos de `§1`, `§2`, `§10`, y los "NUEVA"
  sobre CLI, instalaciones, dominio y plantillas.
- En `garcon-garcia.md`: §2 (lista blanca del sync, el pull que borra antes de descargar,
  `theme diff`, lectura directa por API, dos CLIs en el PATH).
- En `vz.md`: §2 (CLI 2.3.1, `nuvemshop`, la preview).
- En `mc-memorias-hermanos-apps.md`: §2 (`themeId` en `.nuvem`, tokens que vencen, `watch` que
  saltea archivos, JSON minificados).

- [ ] **Step 3: Escribir `05-modelo-y-cli.md`**

Contenido, según el spec:
- Del handoff viejo, todo §1 y §2.
- Lo nuevo:
  - `nuvemshop` ≠ `tiendanube` (`region=br`);
  - dos CLIs en el PATH y `nvm use`;
  - `theme diff --detailed/--json/--published`;
  - la preview sin login (`?preview_theme_installation_id=`, más `storefront=core` en GG), y
    que no se propaga a AJAX ni a la paginación;
  - leer un archivo remoto por la API;
  - el servidor devuelve JSON minificados, y `{}` pasa a `[]`;
  - el pull 2.3.1 borra antes de descargar;
  - el sync por lista blanca (❓: leído en el código, no medido);
  - los tokens de `.nuvem` vencen;
  - `themeId` en `.nuvem`;
  - Ipanema tiene variantes y versiones (1.0.0, 1.2.0, 1.2.2, suscripciones);
  - `"theme": null` en `manifest.json`;
  - el límite de instalaciones (la legacy cuenta; GG tiene 4);
  - el subdominio pasa a 410 con dominio propio;
  - el hash del CDN rota en ~50 s;
  - `watch` arranca con `ignoreInitial`, re-sube sin reintentos y saltea archivos en ráfaga.
- Corregido: "`tiendanube` y `nuvemshop` son idénticos" y "el preview por curl devuelve el
  publicado".
- El protocolo de sync **no** va acá (va en `03`): se linkea.

- [ ] **Step 4: Escribir `12-plantillas.md`**

Contenido:
- Del handoff viejo, todo §10.
- Lo nuevo:
  - el límite de peso de un JSON queda entre 24 y 32 KB (✅ GG);
  - los espacios en el nombre funcionan desde el disco (✅ VZ); los acentos, sin probar;
  - una página sin publicar da 404 incluso en la preview, y la API no asigna plantilla;
  - `page.json` como plantilla heredada (el borrador del comerciante);
  - las mejoras del gate Draft: script primero, cartel `hidden`, `meta refresh` dentro de
    `<noscript>`;
  - el gate Draft rompe "la primera section" del header transparente;
  - `is_preview` es falso en la preview;
  - N páginas con una sola section y un menú del Admin (el centro de ayuda de VZ);
  - con plantillas alternativas, no duplicar la elección con selectores en settings;
  - conservar la indentación de cada JSON.

- [ ] **Step 5: Verificar**

Run: `python3 $SCRATCH/check_handoff.py docs/handoff --files 05-modelo-y-cli.md 12-plantillas.md --mapping`
Expected: `0 errores`. Revisar cada aviso y corregir los `✅` sin fuente y los `❓` sin cómo
re-medir.

- [ ] **Step 6: Cobertura contra el handoff viejo**

Recorrer cada `###` de los §1, §2 y §10 del handoff viejo y confirmar que su contenido está
en el capítulo, o que el spec lo marca como corregido. Anotar en el resumen de la tarea
cualquier cosa que se haya dejado afuera a propósito, con el motivo.

---

### Task 5: Capítulos `06-schema-y-traducciones.md` y `07-twig.md`

**Files:**
- Create: `docs/handoff/06-schema-y-traducciones.md`
- Create: `docs/handoff/07-twig.md`

**Interfaces:**
- Consumes: el spec, el handoff viejo y los reportes.
- Produces: los dos capítulos. `07-twig.md` es el que citan la plantilla del `CLAUDE.md` y el
  `03`.

- [ ] **Step 1: Confirmar que el checker falla**

Run: `python3 $SCRATCH/check_handoff.py docs/handoff --files 06-schema-y-traducciones.md 07-twig.md --mapping`
Expected: exit 1, con `no existe` para los dos.

- [ ] **Step 2: Reunir el material**

- Del handoff viejo: §4 (427–562), §5 (565–590) y §6 (593–795).
- De todos los reportes: los hallazgos de `§4`, `§5` y `§6`.
- Ojo, `mc-claude-3-commits.md` §3 incluye la contradicción de `product_list` / `look-products`.

- [ ] **Step 3: Escribir `06-schema-y-traducciones.md`**

Contenido:
- Del handoff viejo, §4 y §5.
- Lo nuevo:
  - un id nuevo cuando cambia el significado de un setting;
  - los defaults de bloque cambian las instancias ya guardadas, a favor y en contra;
  - el valor guardado también gana en las listas de opciones;
  - al partir un setting en mobile/desktop, `x_mobile ?? x`;
  - no hay `setting_type` de colección (se usa `url` + categorías y sus hijas);
  - los 6 settings de visibilidad también en bloques;
  - el `header` se lleva los settings de abajo;
  - renombrar un `type` sin tocar los ids;
  - `video_url` guarda un objeto (para un mp4 va `text`/`url`);
  - `image_picker` puede traer un video;
  - `product_list` no tiene default, y puede resolver 0;
  - `select` en lugar de `range` con `step` decimal;
  - setting `menu`, con el handle con guion bajo;
  - `deletable: false`;
  - un bloque de configuración con los mismos ids que otro;
  - `custom_font_size` solo con `size == "custom"`;
  - el loop de `product-info.tpl` enumera tipos;
  - recargar el editor después de subir un setting;
  - un toggle opt-in para una expresión no verificada;
  - `;` como separador en un textarea;
  - la clave que falta devuelve la clave tal cual;
  - el locale de referencia se mide por tienda (`es_CL` sí, `es_UY` no existe);
  - auditar el registro (voseo/tuteo), no solo que la clave exista;
  - un namespace `t:` inventado sale crudo;
  - ordenar los locales va en su propio commit.
- ❓ en dos puntos: `product_list` a nivel section (MC vacío en 1.0.0, GG funcionando en
  1.2.0) y los defaults que "no llegan" (un `color` sí llegó en VZ). Cada uno con cómo
  re-medirlo.

- [ ] **Step 4: Escribir `07-twig.md`**

Contenido:
- Del handoff viejo, todo §6, con la tabla de formas con y sin precedente ampliada.
- Lo nuevo:
  - un `for` sobre `null` vacía el render (`| default([])`);
  - dividir por cero tira la section (PHP 8);
  - `in` sobre un string es substring;
  - `product.tags` son objetos (`~ ''`);
  - `loop.index` en un `for` filtrado;
  - `option.id` es el nombre y `variation.id` el índice;
  - llamar un método sobre un objeto que no existe en esa plantilla;
  - `media.next_video` acuña el `uid`;
  - un video no expone texto;
  - una variable local llamada `settings`;
  - un parámetro `null` de un embed;
  - nombres de parámetro que ya usa la plataforma (`variant`, `size`);
  - variables que un snippet hereda y no define;
  - inicializar afuera del `if`;
  - un include faltante en el layout = 500;
  - comparar URLs por handle;
  - filtrar antes del loop;
  - `{{- -}}`;
  - `{% for i in 1..N %}`;
  - un include que "devuelve" un string con `set … endset` (corrige "no se puede factorizar");
  - `merge([obj])` y arrays paralelos;
  - `product.default_options` y `product.variants`, que se usan (corrige la tabla vieja);
  - `| get_products` sobre un string también tira la section;
  - `| upper`, `| sort`, `| url_encode` y `set/endset` sin precedente;
  - `setting_url`;
  - `?? true` no rescata valores que no son `null`.

- [ ] **Step 5: Verificar**

Run: `python3 $SCRATCH/check_handoff.py docs/handoff --files 06-schema-y-traducciones.md 07-twig.md --mapping`
Expected: `0 errores`. Revisar los avisos.

- [ ] **Step 6: Cobertura contra el handoff viejo**

Recorrer cada `###` de los §4, §5 y §6 del handoff viejo y confirmar que su contenido está en
el capítulo, o que está corregido según el spec. Anotar lo que quedó afuera y por qué.

---

### Task 6: Capítulos `08-plataforma.md` y `09-producto-carrito-busqueda.md`

**Files:**
- Create: `docs/handoff/08-plataforma.md`
- Create: `docs/handoff/09-producto-carrito-busqueda.md`

**Interfaces:**
- Consumes: el spec, el handoff viejo y los reportes.
- Produces: los dos capítulos.

- [ ] **Step 1: Confirmar que el checker falla**

Run: `python3 $SCRATCH/check_handoff.py docs/handoff --files 08-plataforma.md 09-producto-carrito-busqueda.md --mapping`
Expected: exit 1, con `no existe` para los dos.

- [ ] **Step 2: Reunir el material**

- Del handoff viejo: §7 (797–920), más las partes de producto y carrito de §9 (1044–1149).
- De todos los reportes, los hallazgos de `§7`. Lo más denso de producto, card, carrito y
  stock está en `mc-claude-2.md`.
- De `mc-claude-1.md`: la "NUEVA: Video de producto (Cloudflare Stream)" y la "NUEVA: SEO y
  URLs".

- [ ] **Step 3: Escribir `08-plataforma.md`** (lo general, lo que no es producto ni carrito)

Contenido:
- Del handoff viejo: el wrapper de section, el `class` del schema, `block_attributes`, los
  slots del nubesdk, la plataforma que mueve nodos, formularios y captcha, `?snipplet=` y los
  modales de la plataforma.
- Lo nuevo:
  - el acordeón privado del footer;
  - `js-apply-filter-private` y `js-modal-open-private`;
  - `modal-visible` en el panel y en `<body>`;
  - los paneles de nivel 2 que se mudan a `<body>`;
  - dos elementos arriba del header;
  - `js-hide-footer-while-scrolling`;
  - el contrato del formulario de contacto (`/winnie-pooh`, honeypot, cancelaciones);
  - campos sin `name` que viajan en el `message`;
  - frenar el submit en captura;
  - el opt-in al newsletter en dos POST;
  - los detalles de la cuenta (validación de email, custom fields que no se renderizan,
    passwordless con `?fallback=1`, los hooks del login);
  - `#resetpass-form`;
  - el newsletter del footer, que devuelve el mismo `contact`;
  - el reCAPTCHA v2 que deshabilita el botón y suma ~92px;
  - un `role="status"` que no se anuncia;
  - ids que chocan con el sprite;
  - `?snipplet=` solo con `X-Requested-With` y `settings` vacío;
  - tramos de URL inventados que dan 200 y migas crudas;
  - `x-cache: hit` ignora el query;
  - el CDN de imágenes da 403 sin referer;
  - el `<h1>` oculto del logo;
  - el popup (iframes, cookie, `.modal form`);
  - el `<dialog>` de una app que muere con `display: none`;
  - las apps que inyectan por JS;
  - `store.afip` y el país.

- [ ] **Step 4: Escribir `09-producto-carrito-busqueda.md`**

Contenido:
- Del handoff viejo: `_cart-item.tpl`, `js-ajax-cart-list`, `js-visible-on-cart-filled` y la
  búsqueda por SKU.
- Variantes y stock:
  - opciones en orden alfabético;
  - `product.variations` en el orden del Admin;
  - `changeVariantButton` y `noStockVariants`;
  - `data-variants`;
  - `variant.stock` null significa infinito;
  - dos lecturas de stock que no coinciden;
  - las colecciones no listan agotados, la búsqueda sí;
  - el filtro de color excluye el agotado.
- Fotos:
  - `featured_image` nunca es null (el placeholder `no-photo`);
  - `variant.image` nunca viene vacío;
  - los alts automáticos no traen el color;
  - `option.custom_data`;
  - los filtros vienen en Title case.
- La card:
  - `initializeProductItemSlider`, clonando el último slide;
  - `data-item-slider-id` único;
  - `LS.productItemSlider` contra la imagen de hover;
  - `data-quickshop-id`;
  - `js-variation-option`;
  - `.js-item-name`;
  - el carrusel de la card solo en category/search.
- La ficha:
  - los hooks de descuento inconsistentes;
  - el comparativo menor que el precio;
  - `is-on-sale` desde Twig;
  - el contrato del form de producto (`#product-shipping-container`, `#single-product`,
    `initAddToCart` con `input[type=submit]`);
  - el placeholder "Agregando…";
  - `installments.tpl`;
  - `store.has_shipping`;
  - la barra de envío gratis en la ficha.
- El carrito:
  - los totales re-renderizados por AJAX;
  - las filas de `cart-totals.tpl`, que no se sacan;
  - los 3 wordings de envío gratis y `LS.freeShippingProgress`;
  - `gift-promotion-progress`;
  - los modales al agregar;
  - `.js-empty-ajax-cart`;
  - `modal.tpl` (`dock_desktop`, `form: true`);
  - el CTA `go_to_checkout`;
  - `.js-coupon-body`;
  - `shipping_calculator_cart_page`;
  - un producto a $0 y `is_gift`;
  - `short_variant_name`;
  - quitar el último ítem recarga `/comprar/`.
- Búsqueda y filtros:
  - productos repetidos entre páginas;
  - no encuentra por nombre de categoría;
  - `products_count`;
  - el drawer de filtros (`%7C`, orden alfabético);
  - `category.products` solo trae los directos, y `categories` solo el primer nivel;
  - las colecciones automáticas no están en el árbol.
- Video de producto (Cloudflare Stream): `muted`, el duplicado invisible que se factura,
  `object-fit` sobre un iframe, pausar fuera de pantalla.
- ❓ la cantidad de slots en el carrito (7 contra 4), con cómo contarlos.

- [ ] **Step 5: Verificar**

Run: `python3 $SCRATCH/check_handoff.py docs/handoff --files 08-plataforma.md 09-producto-carrito-busqueda.md --mapping`
Expected: `0 errores`. Revisar los avisos.

- [ ] **Step 6: Cobertura contra el handoff viejo**

Recorrer cada `###` del §7 viejo (y lo de producto y carrito del §9) y confirmar que está en
alguno de los dos capítulos. Anotar lo que quedó afuera y por qué.

---

### Task 7: Capítulos `10-css.md` y `11-javascript.md`

**Files:**
- Create: `docs/handoff/10-css.md`
- Create: `docs/handoff/11-javascript.md`

**Interfaces:**
- Consumes: el spec, el handoff viejo y los reportes.
- Produces: los dos capítulos. Lo de medir con chrome-devtools del §9 viejo **no** va acá: va
  en `15` (Task 9).

- [ ] **Step 1: Confirmar que el checker falla**

Run: `python3 $SCRATCH/check_handoff.py docs/handoff --files 10-css.md 11-javascript.md --mapping`
Expected: exit 1, con `no existe` para los dos.

- [ ] **Step 2: Reunir el material**

- Del handoff viejo: §8 (923–1041) y §9 (1044–1149, salvo "No armes un harness" y la
  medición).
- De todos los reportes, los hallazgos de `§8` y `§9`, y la "NUEVA: Tablet 768–1023" de
  `mc-claude-1.md`.

- [ ] **Step 3: Escribir `10-css.md`**

Contenido:
- Del handoff viejo, todo §8. La regla de los márgenes negativos se mantiene, con la
  excepción decidida por el dev en MC: el full-bleed de una celda de grilla.
- Lo nuevo:
  - el rango tablet 768–1023.98 y sus reglas;
  - el orden de carga: `async` gana a igual especificidad (no solo utilities contra critical);
  - `p { font-size: var(--font-base) }` del base: `inherit` en los richtext;
  - editar la regla original de `.btn-*`;
  - remapear los tokens del base (se linkea a `04`);
  - "async hiders" propios;
  - un solo `transform` por elemento;
  - animar `transform` y no `bottom` (CLS);
  - `ResizeObserver` no ve `transform`;
  - bloquear el scroll con un drawer abierto;
  - un `#id` dentro de `:has()`;
  - `visibility`;
  - `aspect-ratio` con `stretch` y con `overflow: hidden`;
  - de flex a grid y de grid a columna;
  - `span 2` en una grilla de una columna;
  - `flex: 1 1 0` en columna;
  - `overflow-x: visible` sin desborde;
  - un iframe no tiene alto intrínseco;
  - slots escondidos que ocupan lugar;
  - `.icon-inline`;
  - un prefijo de clase propio;
  - `em` para íconos;
  - separadores como `border-top`;
  - los snippets opcionales sin div envoltorio;
  - `white-space: pre`;
  - los `<input>` no se autodimensionan;
  - `minmax(0,1fr)` para la columna fija;
  - `--h3-line-height` no existe;
  - `column-gap` porcentual;
  - container queries y sus tres cuidados;
  - el `grid-column` negativo del header;
  - un valor declarado le gana a uno heredado;
  - el `%` en `translateX` contra `left`;
  - `scrollWidth` con fracciones;
  - `box-shadow: inset` para los trazos de Figma;
  - dos `<picture>` alternados;
  - el padding inline de las sections del base;
  - dos sections en una fila;
  - el shorthand de `margin`;
  - el contraste del comparativo (`opacity .8`);
  - `-webkit-user-drag`;
  - `isolation: isolate`;
  - `text-decoration` para subrayar;
  - el alto de `.btn` (`line-height`);
  - `color-mix`;
  - `display: contents` multiplica el gap de los slots vacíos;
  - un `<button>` en Arial;
  - `--main-background: transparent` y el fondo propio de los modales;
  - componentes del carrito en una columna angosta;
  - `d-md-none` es `!important` y corta en 768;
  - `.user-content`, `.breadcrumbs`, `.account-form-container`, `.btn-tertiary`;
  - lo roto del base (`.promotional-modal-image-link`, `.password-section-layout`).

- [ ] **Step 4: Escribir `11-javascript.md`**

Contenido:
- Del handoff viejo, §9 (store.js, la API `LS`, las tres trampas de Swiper, `touch-action`,
  `bindScroller`, `bindAccordionDetails`).
- Lo nuevo:
  - Swiper escribe el ancho inline, y el `update()` con dos rAF no alcanza (corrige el viejo);
  - el bundle es Swiper 5;
  - `LS.getUrlParams` y el `+`, con el script inline en el `<head>`;
  - `LS.paramsToUrl` y `mpage`;
  - el contrato de la URL de filtros;
  - el header que se esconde al bajar;
  - `initTransparentHeader` y su lista blanca;
  - `body:has()` contra la primera section;
  - claves idénticas en JS y en Twig;
  - separar conmutar de publicar la medida;
  - no colgar una función de un init que corta temprano;
  - formato de montos (`toFixed` antes de `toLocaleString`, sacar los `,00`);
  - `LS.formatToCurrency` con espacio;
  - `data-product-price` pierde un punto;
  - `LS` lee todos los selects;
  - el quick add que reusa el form oculto;
  - dos rAF antes de abrir un panel recién movido;
  - `mouseover` delegado de jQuery;
  - un listener en captura antes que Swiper;
  - `(hover: hover)` en cada evento;
  - refrescar un bloque re-pidiendo la página;
  - la señal de "cambió el carrito";
  - una bandera de origen del alta;
  - JS de cuotas;
  - sanear HTML clonado (`/translate3d/`);
  - `<template>` contra `display: none`;
  - SVG `className` y `<use>`;
  - `scrollIntoView` dentro de un track;
  - `<button>` dentro de `<a>`;
  - `response.json()` con su propio `catch`;
  - `localStorage` topeado por bytes;
  - `sizes` de las imágenes (1461 → 224 KB);
  - el costo lineal de `paginate`;
  - cards por AJAX en vez de renderizarlas en el header;
  - validación en captura sobre `window`;
  - video lazy;
  - Google Maps sin Map ID (se linkea a `16` por la key);
  - `offsetParent` en un `position: fixed`;
  - con cards duplicadas por color, partir del elemento del evento.

- [ ] **Step 5: Verificar**

Run: `python3 $SCRATCH/check_handoff.py docs/handoff --files 10-css.md 11-javascript.md --mapping`
Expected: `0 errores`. Revisar los avisos.

- [ ] **Step 6: Cobertura contra el handoff viejo**

Recorrer cada `###` y cada viñeta de "Otras reglas" de §8 y §9 y confirmar que están, o que
se mudaron a `15`. Anotar lo que quedó afuera y por qué.

---

### Task 8: Capítulos `13-limites-y-admin-api.md`, `14-patrones.md` y `16-multipais-apps-integraciones.md`

**Files:**
- Create: `docs/handoff/13-limites-y-admin-api.md`
- Create: `docs/handoff/14-patrones.md`
- Create: `docs/handoff/16-multipais-apps-integraciones.md`

**Interfaces:**
- Consumes: el spec, el handoff viejo y los reportes.
- Produces: los tres capítulos.

- [ ] **Step 1: Confirmar que el checker falla**

Run: `python3 $SCRATCH/check_handoff.py docs/handoff --files 13-limites-y-admin-api.md 14-patrones.md 16-multipais-apps-integraciones.md --mapping`
Expected: exit 1, con `no existe` para los tres.

- [ ] **Step 2: Reunir el material**

- Del handoff viejo: §11 (1235–1262) y §12 (1265–1346).
- De los reportes:
  - los hallazgos de `§11` y `§12`;
  - de `mc-memorias-hermanos-apps.md`, las "NUEVA: un cliente con tiendas en varios países",
    "NUEVA: app de gestión", "NUEVA: apps de terceros" y el punto 5 (la arquitectura);
  - de `vz.md`, las "NUEVA · Admin API con el token de `.nuvem`" y "NUEVA · Archivos desde el
    storefront";
  - de `mc-claude-3-commits.md`, "NUEVA: Apps de terceros e integraciones externas".

- [ ] **Step 3: Escribir `13-limites-y-admin-api.md`**

Contenido:
- La tabla del §11 viejo, actualizada:
  - la wishlist **se puede**: en el tema, con `localStorage` y la card capturada;
    multi-dispositivo y métricas, con una app propia;
  - "Avisame cuando haya stock" lo cubre stocknube;
  - UN producto: reconfirmado que no.
- Lo nuevo que no se puede:
  - `variant.price` sin precedente;
  - fotos por color sin relación variante→galería;
  - el tema no fuerza precios;
  - no hay forma barata de saber si un producto ajeno está disponible;
  - el orden manual de una categoría no se escribe por API (se reinserta);
  - las categorías y tags del blog;
  - la API de menús;
  - la búsqueda de pedidos por número + email;
  - clientes con el token del CLI (403);
  - videos en la biblioteca de medios;
  - la lista "Más vendidos";
  - Instagram sin token;
  - el buscador ignora las palabras de más;
  - "Organizar productos → Destacar" lee el tema publicado.
- La Admin API:
  - el token de `.nuvem` sirve (se decodifica dentro de un script, nunca se imprime);
  - los scopes quedan congelados en el token;
  - Pages API (`es_AR`, `per_page < 20`, el `PUT` completo);
  - Blog API (el autor es el User-Agent, el handle, el orden);
  - 🔥 crear páginas las suma al menú principal;
  - el `PUT` de tags reemplaza el set completo;
  - `variants` es lento;
  - `q=`;
  - el 404 al final de la paginación;
  - vaciar un metacampo lo borra;
  - custom fields (los owners borrados);
  - `fields=features` da 422;
  - Business Rules `logistic` (800 ms, `detail.unmaterialized`).
- Ningún id, token ni `app_id`.

- [ ] **Step 4: Escribir `14-patrones.md`**

Contenido:
- Del handoff viejo, todo §12: el wrapper de visibilidad, el diagnóstico por comentario HTML,
  el scroller nativo, el `%` según la propiedad y el `<h1>`.
- Lo nuevo:
  - los campos del diagnóstico por comentario (`origen=`, `json=`, `recibidos/escondidos/dibujados`, `precios=`);
  - instrumentar cada término de la guarda;
  - un renderizador de media como superconjunto de `image.tpl`, y la regla de los cuatro
    medios como ejemplo de VZ;
  - reemplazar un componente nativo sin esconderlo;
  - el texto del comerciante con marcador `#XXX`;
  - categoría por producto en cascada (metacampo → etiqueta → fija);
  - completar con las subcategorías;
  - un metacampo con un JSON que pisa settings;
  - filtros fail-open;
  - filtrar la lista de cada section antes de `has_products`;
  - `ld+json` una vez por producto;
  - una card por color;
  - links dentro del `<a>` de la card;
  - forms de alta fuera del `<form>`;
  - un toggle para volver al nativo en el camino al checkout;
  - badges por etiqueta;
  - el diccionario de muestras;
  - la barra de compra flotante con placeholder;
  - un botón flotante que esquiva a otro;
  - parámetros aditivos en snippets compartidos;
  - dibujar bloques en otro punto del DOM;
  - `extra_item_classes`;
  - variantes de card por `.grid-N`;
  - Swiper inerte por CSS;
  - setting `Etiqueta=destino`;
  - el bloque de configuración con ids espejados;
  - variantes de estilo como setting antes que sections nuevas;
  - link en toda la card;
  - rank espaciado;
  - el orden en Twig y no con `order`;
  - una section en su plantilla con respaldo filtrado por handle;
  - no usar el wrapper de visibilidad en password ni en landings;
  - el kit de landings (VZ) como ejemplo;
  - countdown;
  - `vzCopyText` como patrón de copiar al portapapeles;
  - el diccionario de colores y la convención de alt `NOMBRE#COLOR#N` (GG);
  - el logo por `image_picker` con fallback;
  - no tocar datos de la tienda mientras hay un borrador (GG).

- [ ] **Step 5: Escribir `16-multipais-apps-integraciones.md`**

Contenido:
- **Tiendas por país:**
  - un repo por país, clonado;
  - identidad leída del servidor;
  - clonar arrastra los endpoints (lo primero que se revisa) y la configuración (`@media-lib`,
    textos legales, locales, assets);
  - la primera subida sobre un Ipanema de fábrica más nuevo;
  - portar con `git format-patch` + `git apply`, y no con `cp`;
  - verificar por tienda;
  - cada hermano lo pushea el dev desde su propio cwd;
  - las mediciones heredadas se avisan en el `CLAUDE.md` del hermano.
- **La arquitectura tema + app de gestión** (el párrafo del punto 5 de
  `mc-memorias-hermanos-apps.md`, en genérico):
  - qué resuelve: wishlist, flag de cliente, subida de PDF, metacampos, badges y familias,
    orden de categorías;
  - cómo se conecta: settings `url`, `credentials: 'omit'`, degradar sin romper;
  - el orden de despliegue app ↔ tema;
  - los datos de catálogo por tags y metacampos, y las acciones del comprador por endpoint.
- **CI y deploy de las apps:**
  - verificar la CI después de pushear;
  - un EC2 sin swap y el OOM del `vite build`;
  - la CI hace lo mismo que el deploy;
  - un label de runner por país;
  - los cuatro baches del provisioning;
  - nginx saca el prefijo `/api/`.
- **Apps de terceros:**
  - esconder su control y dispararlo desde uno propio;
  - neutralizar una app que compite (`display: none !important`, envolver su global);
  - stocknube;
  - Google Maps (la allowlist por host, `gm_authFailure` antes de inyectar, el canal weekly,
    `Marker` deprecado, `OverlayView` sin Map ID).
- **El servicio de archivos del estudio** (nubefiles, sin URL):
  - identifica la tienda por el `Origin`;
  - el límite de nginx de 1 MB da un error de red sin CORS;
  - la ruta de contacto no lleva archivos, así que la URL viaja en el mensaje.

- [ ] **Step 6: Verificar**

Run: `python3 $SCRATCH/check_handoff.py docs/handoff --files 13-limites-y-admin-api.md 14-patrones.md 16-multipais-apps-integraciones.md --mapping`
Expected: `0 errores`. Revisar los avisos. Ojo con los ids y los dominios de las apps de
gestión y del servicio de archivos.

- [ ] **Step 7: Cobertura contra el handoff viejo**

Recorrer cada fila de la tabla del §11 viejo y cada `###` del §12 y confirmar que están, o
que están corregidos. Anotar lo que quedó afuera y por qué.

---

### Task 9: Capítulos `04-diseno-y-ui-kit.md` y `15-verificacion-y-qa.md`

**Files:**
- Create: `docs/handoff/04-diseno-y-ui-kit.md`
- Create: `docs/handoff/15-verificacion-y-qa.md`

**Interfaces:**
- Consumes:
  - el spec, el handoff viejo y los reportes;
  - las plantillas de la Task 3: `04` linkea `plantillas/ui-kit.md` y
    `plantillas/ui-kit-skill/SKILL.md`.
- Produces: los dos capítulos.

- [ ] **Step 1: Confirmar que el checker falla**

Run: `python3 $SCRATCH/check_handoff.py docs/handoff --files 04-diseno-y-ui-kit.md 15-verificacion-y-qa.md --mapping`
Expected: exit 1, con `no existe` para los dos.

- [ ] **Step 2: Reunir el material**

- Del handoff viejo: §13 (1349–1386), §14.2, §14.5, §14.6 y §14.7 (1398–1427), y de §9 "No
  armes un harness" (1123–1148).
- De los reportes:
  - de `vz.md`, "NUEVA · Diseño desde HTML de Claude Design", §13 y el punto 4 (la skill de
    proyecto, las anomalías);
  - de `garcon-garcia.md`, §9 (la preview, CDP, el perfil compartido) y la contradicción 8;
  - de `mc-claude-1.md`, §13 y el punto D (proceso con Figma);
  - de `mc-memorias-hermanos-apps.md`, §13 (Lighthouse, headless, TCC, "¿ya está publicado?");
  - de `skills-uso-real.md`, el punto 21 (QA en la práctica).

- [ ] **Step 3: Escribir `04-diseno-y-ui-kit.md`**

Contenido:
- **La fuente de diseño es la autoridad** (corrige "El Figma es la autoridad"). Tres matices:
  - un nodo de pantalla que dibuja un estado no le gana al default del componente;
  - un pedido explícito del dev o del cliente gana y se documenta como divergencia;
  - los typos no se copian (y los textos legales se copian verbatim).
- **Vía Figma:**
  - `get_design_context`, `get_metadata`, `get_variable_defs`;
  - los nodos del ui-kit;
  - medir sobre el nodo antes de declarar "sin tokenizar";
  - `items-start` se traduce a `stretch`;
  - el nodo actualizado cuando cambia el Figma.
- **Vía HTML de Claude Design:**
  - `curl` al scratchpad, `renderVals()`, `m ? mobile : desktop`, valores con nombre;
  - las anclas del DS en la tabla de bocetos;
  - el HTML trae duraciones, curvas y disparadores que Figma no da;
  - los íconos, del SVG inline;
  - la prioridad DS contra boceto;
  - las trampas:
    - bugs del boceto;
    - el `a:hover` global;
    - botones sin `font-family`;
    - páginas en otro archivo;
    - assets en el servidor de prototipos del estudio;
    - copy de relleno;
    - herramientas del boceto que no se construyen;
    - breakpoints distintos;
    - grises fuera de paleta.
- **Sin diseño:** la skill `design` (no está garantizada), un brief escrito o una captura del
  dev, y "estado deducido".
- **El ui-kit primero:**
  - `ui-kit.md` con anomalías numeradas y fechadas (→ `plantillas/ui-kit.md`);
  - tokens en `style-tokens.tpl` con el remapeo de los tokens del base (→ `10`);
  - la skill de proyecto `<cliente>-ui-kit` (→ `plantillas/ui-kit-skill/SKILL.md`): qué
    contiene, por qué existe (sesiones paralelas) y que se desactualiza respecto del doc;
  - la tabla `## Bocetos por sección` con columna "Código" (contrato con `nube-skills-qa`);
  - registrar quién pidió cada cosa.

- [ ] **Step 4: Escribir `15-verificacion-y-qa.md`**

Contenido:
- Del handoff viejo, todo §13 (schemas, balance de tags, comentario dentro de una etiqueta,
  comentarios anidados, `t:` en los 7 locales, `node --check`, llaves del CSS) y el corolario.
- Lo nuevo:
  - el chequeo de comentarios CSS: el snippet de `mc-memorias-hermanos-apps.md` §8 (un glob
    rompe la hoja);
  - diff de cantidad de líneas después de editar por script (406 líneas truncadas);
  - un assert que no puede fallar;
  - verificar en los dos sentidos;
  - barrer todas las páginas antes y después;
  - forzar un valor y ver que cambie solo esa card;
  - probar en dos pasos (simulado y real, y restaurar);
  - comprobar que un bug es preexistente restaurando HEAD;
  - listar las ramas sin probar.
- Medir en la tienda (del §9 viejo, "No armes un harness"):
  - chrome-devtools MCP con `emulate` (no `resize_page`);
  - si el MCP está tomado: headless con `userDataDir` propio y un user agent normal (con el
    UA de headless, `POST /comprar/` da 403);
  - nunca levantar Chrome visible desde el shell, porque macOS le revoca a Claude Code el
    acceso a `~/Desktop`;
  - el perfil del MCP es compartido: no matar procesos ajenos;
  - ❓ el `IntersectionObserver` en headless (MC dice que no dispara; VZ midió con reveals),
    con cómo re-medirlo;
  - el estado del módulo persiste: recargar entre mediciones;
  - Lighthouse contamina `list_network_requests`, y el `srcset` en caché;
  - `x-cache`;
  - la barra de 52px de la preview;
  - la preview no se propaga;
  - el modo contraseña va y viene, y la preview no lo saltea;
  - `/password/` está cacheada;
  - "¿ya está publicado?": dos curl, el HTML y el asset con hash;
  - el hash del CDN rota;
  - medir el boceto y la preview en el mismo navegador (viewports 1440×900 y 390×844,
    `getBoundingClientRect`);
  - clasificar cada diferencia como código, contenido o Admin;
  - inyectar markup sirve para el CSS, no prueba el Twig;
  - en `/comprar`, contar `js-item-name` y no los links;
  - probar JS sin subirlo, interceptando `store.js` por CDP.
- QA en la práctica: `nube-skills-qa` casi no se usó; lo que sí funcionó (se linkea a `02`).

- [ ] **Step 5: Verificar**

Run: `python3 $SCRATCH/check_handoff.py docs/handoff --files 04-diseno-y-ui-kit.md 15-verificacion-y-qa.md --mapping`
Expected: `0 errores`. Revisar los avisos. Ninguna URL del servidor de prototipos.

- [ ] **Step 6: Cobertura contra el handoff viejo**

Confirmar que los 7 chequeos del §13 viejo, §14.2, §14.5, §14.6, §14.7 y "No armes un harness"
están en alguno de los dos capítulos. Anotar lo que quedó afuera y por qué.

---

### Task 10: Capítulos `02-skills.md` y `03-sync-y-reglas.md`

**Files:**
- Create: `docs/handoff/02-skills.md`
- Create: `docs/handoff/03-sync-y-reglas.md`

**Interfaces:**
- Consumes: el spec, el handoff viejo, los reportes y los capítulos `05`, `07` y `15` (se
  linkean).
- Produces: la lectura obligatoria sobre skills y sync. La plantilla del `CLAUDE.md` y el
  kickoff los citan por nombre.

- [ ] **Step 1: Confirmar que el checker falla**

Run: `python3 $SCRATCH/check_handoff.py docs/handoff --files 02-skills.md 03-sync-y-reglas.md --mapping`
Expected: exit 1, con `no existe` para los dos.

- [ ] **Step 2: Reunir el material**

- Del handoff viejo: §3 (272–424) y §14.3/§14.4 (1407–1414).
- De los reportes:
  - `skills-uso-real.md` entero;
  - de `garcon-garcia.md`, §3, "NUEVA: Incidente 2026-09-23" y el punto 4 (commits);
  - de `vz.md`, §3 y el punto 4 (sesiones paralelas, agrupación de commits);
  - de `mc-memorias-hermanos-apps.md`, §3 y el punto 4;
  - de `mc-claude-3-commits.md`, §3 y el punto 4.
- Las piezas del plugin: `commands/kickoff.md` (versión nueva, Task 13), `hooks/sync-gate.py`
  y `skills/*/SKILL.md`.

- [ ] **Step 3: Escribir `02-skills.md`**

Contenido:
- **Instalación:**
  - en Claude Code, solo el plugin, con los comandos de instalar y actualizar del README;
  - verificar con `/hooks`;
  - **no** `npx skills add` en el repo del tema: salen duplicadas y sin descripción, el modelo
    elige la copia local (27 de 27 en VZ), y la de `themes` era la v1.3.0, sin `--stamp`;
  - `npx skills add` solo para otros agentes, sin hook ni kickoff.
- **Una tabla por pieza** (kickoff, `nube-skills-themes`, `-section`, `-qa`, `-i18n`,
  `-admin`, hook `sync-gate`):
  - para qué sirve;
  - cómo se dispara en la práctica, con la frase o el slash. `themes` no se cargó nunca en 54
    sesiones: hay que invocarla con `/nube-skills:nube-skills-themes`;
  - qué necesita del dev;
  - qué escribe;
  - qué requiere: Figma MCP, chrome-devtools MCP, la skill `design`, el MCP de Tiendanube o las
    variables `TN_*`.
- **Scripts con ruta sin versión:**
  `$(ls -d ~/.claude/plugins/cache/nube-skills/nube-skills/*/ | sort -V | tail -1)skills/<skill>/scripts/<script>`,
  con los comandos exactos de `sync-check.py` (`--files`, `--stamp`, `--json`, exit 0/1/2),
  `audit-i18n.py` y `tn-api.py` (`--paginate`, `--dry-run`, `--backup`).
- **El hook:**
  - qué bloquea (`deny` en templates/settings_data y en `theme push`; `ask` en `publish`);
  - el marcador en `~/.cache/nube-skills` con su ventana de 15 minutos;
  - cómo registrar un pull a temporal (`--stamp`);
  - los escapes, que son del dev (`NUBE_SKIP_SYNC_GATE`, `NUBE_SYNC_MAX_AGE_MIN`);
  - los falsos positivos, cada uno con cómo seguir: el texto `theme push` en cualquier
    comando, el cwd de la sesión, los archivos nuevos;
  - lo que no ve: las escrituras por Bash y lo que sube `watch`;
  - "que no bloquee no prueba que estés sincronizado".
- **La skill de proyecto `<cliente>-ui-kit`:** el patrón y por qué se carga sola (se linkea a
  `04`).
- **Uso real en cifras:** la tabla de `skills-uso-real.md` §4, resumida.
- **Problemas conocidos del plugin y cómo esquivarlos:** la lista "Pendientes del plugin" del
  spec, cada uno con su workaround.

- [ ] **Step 4: Escribir `03-sync-y-reglas.md`**

Contenido:
- **El modo de falla** (del handoff viejo) con los casos reales: las 4 pérdidas de MC más las
  2 que casi pasan (`page.Locales.json`, `header.json`), y el gate de VZ atrapando cambios del
  editor.
- **El protocolo tal como se practica:**
  1. `git status --porcelain`.
  2. ¿Hay watch? `ps -Ao pid,command | grep "cli.js theme"` + `lsof -a -p <pid> -d cwd`.
  3. El estado del servidor: pull a un temporal (copiando `.nuvem` + `manifest.json`, con
     `-y`) o `theme diff --detailed`. **Nunca `theme pull` sobre el proyecto con watch.**
  4. Contar archivos y comparar los JSON parseados.
  5. Traer lo del comerciante y commitearlo aparte.
  6. `--stamp`.

  Alcance: los JSON que se van a modificar. Un archivo nuevo no necesita gate, pero el hook lo
  bloquea igual.
- **Editar un JSON del comerciante con watch prendido, en cuatro tiempos (GG):** bajar el
  remoto, escribir el remoto más tu clave, re-bajarlo justo antes y abortar si cambió, y
  verificar después.
- **Preferir un fallback en Twig antes que escribir archivos del comerciante (MC).** Si hay
  que escribirlos, se editan sobre la versión del servidor.
- **Del handoff viejo:** leer el diff, reconciliar un conflicto, el gate antes de `publish`,
  leer el servidor sin riesgo, el cwd que persiste, los anti-patrones.
- **El borrador que pasa a productivo sin avisar (MC y GG):** verificarlo con `theme list`.
- **El incidente del 2026-09-23 contado entero:** la línea de tiempo, la recuperación y la
  regla que quedó. Y la lección: estaba escrito en dos lugares y aun así pasó.
- **Con watch, todo lo que se guarda se publica:**
  - validar antes de guardar (copia → `node --check` → `mv`);
  - el orden de guardado (traducciones → CSS → snippet → schema);
  - las ráfagas hacen que watch saltee archivos (tocar de a uno y verificar);
  - reiniciar watch no sincroniza nada;
  - cambiar de rama con watch prendido;
  - el revision token después de cada subida.
- **Reglas del equipo:**
  - las del handoff viejo;
  - deshacer también se pide;
  - "no esconder" con su matiz (se puede si el dev o el cliente lo pide, documentado);
  - los tokens nunca se imprimen ni se guardan en `permissions.allow`;
  - listar al terminar qué hay para subir.
- **Commits:**
  - los de sync van aparte y primero;
  - agrupar por página con `git hash-object -w` + `git update-index --cacheinfo`, fijando la
    base del diff;
  - nunca un commit roto por sí solo;
  - el trabajo de otra sesión, rotulado;
  - el commit de docs, al final;
  - mover `main` sin tocar el working tree (`git branch -f`) y por qué es seguro con watch.
- **Sesiones paralelas:** ediciones quirúrgicas, nunca un Write entero desde una lectura
  vieja, y verificar que cada diff sea propio.

- [ ] **Step 5: Verificar**

Run: `python3 $SCRATCH/check_handoff.py docs/handoff --files 02-skills.md 03-sync-y-reglas.md --mapping`
Expected: `0 errores`. Revisar los avisos.

- [ ] **Step 6: Cobertura contra el handoff viejo**

Recorrer cada `###` del §3 viejo y §14.3/§14.4 y confirmar que están. Anotar lo que quedó
afuera y por qué.

---

### Task 11: `01-arranque.md` y `README.md`

**Files:**
- Create: `docs/handoff/01-arranque.md`
- Create: `docs/handoff/README.md`

**Interfaces:**
- Consumes: todos los capítulos anteriores (el README los indexa y `01` los linkea), el
  kickoff nuevo (Task 13: `01` describe sus pasos; si la Task 13 todavía no está hecha, se
  usa la Parte 2 del spec) y las plantillas.
- Produces: la entrada al handoff. El kickoff cita `README.md` y `01-arranque.md`.

- [ ] **Step 1: Confirmar que el checker falla**

Run: `python3 $SCRATCH/check_handoff.py docs/handoff --files 01-arranque.md README.md --mapping`
Expected: exit 1, con `no existe` para los dos.

- [ ] **Step 2: Escribir `01-arranque.md`**

Contenido, según el spec:
- **Máquina del dev, una vez:** plugin + `/hooks`, los MCPs, `tiendanube` (nunca
  `nuvemshop`), Node / `.nvmrc`, `python3`, `gh`.
- **Decisiones con el dueño:** productiva o borrador (con `theme list`), quién pushea, fork,
  fuente de diseño, locales y tiendas hermanas, dominio propio, dependencias del Admin.
- **Día 1 = `/nube-skills:kickoff`:**
  - los 10 pasos, uno por uno, con su porqué;
  - qué pasó cuando no se usó (VZ: `.nuvem` en el primer commit);
  - el `theme authorize` que corre el dev.
- **Heredar del proyecto anterior:** diffear el base contra el pull inicial del proyecto
  previo para saber qué trampas aplican (VZ contra GG).
- **Semana 1, en orden:**
  - ui-kit (→ `04`), globales y páginas;
  - ficha y carrito al final, con el matiz de VZ;
  - sesiones paralelas con un `ESTADO` común (patrón de GG);
  - encabezados por pieza en los archivos compartidos.
- **Antes de publicar:** el checklist de dependencias del Admin (el de `vz.md`, "NUEVA ·
  Checklist") y el gate de `publish` (→ `03`).
- **Cierre y traspaso:**
  - qué dejar en el repo (el diseño completo, `.nvmrc`, las advertencias en el `CLAUDE.md`);
  - la guía para el comerciante, con la estructura de la guía de GG (punto 4 de
    `garcon-garcia.md`);
  - `ESTADO` y handoffs por página, y cómo se desactualizan;
  - devolver lo aprendido a nube-skills.

- [ ] **Step 3: Escribir `README.md`**

Contenido:
- Qué es y para quién.
- **Esto es una foto:** la copia de `.docs/handoff/` del proyecto no se edita; la versión
  canónica vive en nube-skills (`docs/handoff/`); lo genérico vuelve ahí.
- El orden de lectura: `01`–`03` son obligatorios.
- Una tabla-índice con **los 16 capítulos y las 3 plantillas, cada uno con su link**: archivo,
  qué tiene y cuándo leerlo.
- Las marcas y las etiquetas de fuente (MC con AR/CL/UY, GG, VZ; ago–sep 2026; Ipanema
  1.0.0/1.2.0/1.2.2; CLI 2.1.0–2.3.1).
- Lo que no es.
- **"Los errores que más caros salieron":** los 5 del apéndice viejo, más:
  - el pull con watch del 2026-09-23;
  - el glob en un comentario CSS;
  - el script que truncó 406 líneas;
  - los endpoints clonados a otro país.

  Todos con la misma moraleja: el sistema falla en silencio.

- [ ] **Step 4: Verificar el handoff completo**

Run: `python3 $SCRATCH/check_handoff.py docs/handoff --mapping && python3 scripts/validate.py`

Expected:
- el checker: `0 errores` sobre todos los archivos, con todos los mapeos;
- `validate.py`: `OK: …`, sin ningún link roto.

---

### Task 12: Revisión cruzada del handoff

**Files:**
- Modify: cualquier archivo de `docs/handoff/` que la revisión encuentre mal.

**Interfaces:**
- Consumes: el handoff completo (tareas 3 a 11).
- Produces: el handoff listo para el release.

- [ ] **Step 1: Contradicciones del spec, una por una**

Para cada fila de "Resolución de contradicciones" del spec, abrir el capítulo que le toca y
confirmar que dice lo de la columna "Ahora", con su marca.

| Fila | Capítulo | Qué buscar |
|---|---|---|
| Wishlist, aviso de stock | `13` | Ya no son 🚫 |
| `nuvemshop`, preview | `05` | `region=br`, `preview_theme_installation_id` |
| Gate, paso 3 | `03` | Nunca un pull con watch; temporal / `theme diff` / `--stamp` |
| Qué sube el push | `05` | ❓ con la lista blanca y cómo medirlo |
| `product_list` en section, defaults | `06` | ❓ con cómo re-medirlo |
| CLAUDE.md | `01` + `04` | Liviano en `.claude/`, el detalle en `.docs/` |
| Autoridad del diseño | `04` | Los tres matices |
| Márgenes negativos | `10` | La regla, más la excepción de MC |
| Swiper `update()` | `11` | Corregido |
| Peso del JSON, nombres | `12` | 24–32 KB; espacios sí |
| Factorizar un valor, `variants` / `default_options` | `07` | Corregido |
| Medir con Chrome propio | `15` | ❓ `IntersectionObserver` |
| Orden de trabajo | `01` | El matiz de VZ |
| Slots del carrito | `09` | ❓ |
| El hook | `02` | Push, publish, cwd |
| Ramas | `03` | Aclarado que la regla es de permiso |

- [ ] **Step 2: Hechos duplicados**

Run:
```bash
for t in next_video region=br no-photo js-nubesdk-slot getUrlParams '\-\-stamp' format-patch renderVals; do
  printf '%-20s' "$t"; grep -l -- "$t" docs/handoff/*.md | xargs -n1 basename | tr '\n' ' '; echo; done
```

Expected: cada término explicado en **un** capítulo. Si aparece en más de uno, en los demás
tiene que ser una mención corta con link, no la explicación repetida. Corregir lo que no
cumpla.

- [ ] **Step 3: Tamaños**

Run: `wc -c docs/handoff/*.md docs/handoff/plantillas/*.md docs/handoff/plantillas/*/*.md | sort -n`
Expected:
- `README` + `01` + `02` + `03` suman menos de ~70 KB;
- ningún capítulo pasa los ~45 KB. Si alguno pasa, partirlo por tema, con un link desde el
  índice.

- [ ] **Step 4: Chequeo final**

Run: `python3 $SCRATCH/check_handoff.py docs/handoff --mapping && python3 scripts/validate.py`
Expected: `0 errores` y `OK: …`. Los avisos que queden están revisados uno por uno.

---

### Task 13: `commands/kickoff.md` alineado y con la copia del handoff

**Files:**
- Modify: `commands/kickoff.md` (se reemplaza entero)

**Interfaces:**
- Consumes:
  - `docs/handoff/plantillas/CLAUDE.md` (Task 3);
  - `docs/handoff/README.md`, `01-arranque.md`, `03-sync-y-reglas.md`, `04-diseno-y-ui-kit.md`
    y `05-modelo-y-cli.md` (por nombre);
  - `skills/nube-skills-i18n/scripts/audit-i18n.py`;
  - `.claude-plugin/plugin.json`.
- Produces: el comando `/nube-skills:kickoff`. `validate.py` verifica sus rutas
  `${CLAUDE_PLUGIN_ROOT}/…`.

- [ ] **Step 1: Confirmar que el chequeo de rutas atrapa una ruta rota**

Sobre el fixture de la Task 1, sin tocar el kickoff real. Si el fixture no existe, rehacer
los steps 1 y 5 de la Task 1.

Run: `F=$SCRATCH/validate-fixture && cp scripts/validate.py "$F/scripts/" && sed 's|^Arrancá un proyecto|Leé ${CLAUDE_PLUGIN_ROOT}/docs/handoff/falta-a-proposito.md. Arrancá un proyecto|' commands/kickoff.md > "$F/commands/kickoff.md" && python3 "$F/scripts/validate.py"`

Expected: `✗ commands/kickoff.md: ruta inexistente ${CLAUDE_PLUGIN_ROOT}/docs/handoff/falta-a-proposito.md`.

- [ ] **Step 2: Reemplazar `commands/kickoff.md` entero por:**

````markdown
---
description: Arranca un proyecto nuevo de tema sectionable de Tienda Nube (Ipanema, Fork Workflow) — instalación, pull verificado, git con .nuvem protegido, el handoff de nube-skills en .docs/handoff/ y .claude/CLAUDE.md del proyecto
argument-hint: [nombre-del-cliente]
disable-model-invocation: true
---

Arrancá un proyecto nuevo de tema sectionable de Tienda Nube. Cliente: $ARGUMENTS

Seguí estos pasos en orden. El contexto técnico está en el handoff de nube-skills, que este
comando copia al proyecto en el paso 5: `${CLAUDE_PLUGIN_ROOT}/docs/handoff/README.md`. Para
el día 1, `01-arranque.md`; para el CLI, `05-modelo-y-cli.md`; para el sync,
`03-sync-y-reglas.md`. **No inventes comandos del CLI**: no existen `theme dev`,
`theme check` ni `theme serve`.

Dos reglas valen desde el primer comando:

- El agente **nunca** corre `tiendanube theme push`, `theme watch`, `theme publish` ni
  `theme fork`. Los corre el dev, en su terminal o con `!`.
- Siempre el binario `tiendanube`, **nunca `nuvemshop`**: al autorizar, `nuvemshop` manda
  `region=br` y deja una tienda de LATAM en la pantalla equivocada.

## 1. Datos del proyecto

Preguntale al dev todo lo que falte, en una sola tanda:

- Nombre del cliente (si no vino como argumento) y carpeta destino (si ya estás parado en
  ella, confirmalo).
- **La fuente de diseño.** Una de tres:
  - **Figma:** el link ("Copy link to selection") de cada nodo del ui-kit que exista (tabla
    de abajo). Los que falten quedan `pendiente`.
  - **Prototipo HTML** (Claude Design u otro): la URL del prototipo y la del design system.
  - **Sin diseño:** el sistema visual pasan a ser los tokens del tema
    (`layouts/resources/style-tokens.tpl` + `config/settings_schema.json`).
- ¿Instalación nueva o una que ya existe? El límite es **2 instalaciones por tienda, y una
  legacy (un tema viejo por FTP) cuenta**. Con 2, `theme create` falla.
- **¿Quién pushea?** Por default, el dev, con `tiendanube theme watch` en su terminal. Con
  watch prendido, cada archivo que se guarda se publica.
- **¿Se forkea?** Sin fork solo se suben `templates/**`, `custom/**` y
  `config/settings_data.json`. El push omite en silencio `sections/`, `blocks/`, `snippets/`,
  `layouts/`, `static/` y `translations/`. Hoy el fork funciona.
- Locales requeridos, tiendas hermanas en otros países y si la tienda usa dominio propio. Con
  dominio propio, el subdominio `*.mitiendanube.com` puede pasar a responder 410.
- ¿Crear también un repo privado en GitHub (org `Innovate-group`)? Es opcional.

**No pidas los bocetos de las páginas.** Se pasan sección a sección durante el desarrollo,
cuando el dev invoca `nube-skills-section`.

### Los nodos del ui-kit (si la fuente es Figma)

| Nodo | Para qué lo usan las skills |
|---|---|
| **Colores / paleta** | Mapear cada color del diseño a su token con nombre en vez de copiar el hex suelto |
| **Tipografías / escala** | Familias, pesos y tamaños con nombre; evita inventar una escala por sección |
| **Botones** | Variantes y estados (primario, secundario, hover, disabled) |
| **Formularios / inputs** | Campos, labels, mensajes de error |
| **Cards / product card** | La pieza que más se repite en un ecommerce |
| **Iconografía** | Set de íconos y su tamaño base |
| **Espaciados / grid** | Escala de espaciado, ancho de contenedor y columnas |

Si el ui-kit está todo en una sola página de Figma, alcanza con el link de esa página, pero
anotá igual qué contiene. Nunca inventes un link. Si la fuente es un prototipo HTML, en vez
de nodos se anotan las anclas del design system (por ejemplo `…#colores`). Cómo se sacan los
valores de ese HTML está en `04-diseno-y-ui-kit.md` del handoff.

## 2. Prerrequisitos

1. Si la carpeta tiene `.nvmrc`, corré `nvm use`. Después, `tiendanube --version`. Si falla,
   `npm install -g @tiendanube/cli`. El CLI declara Node 24.15+, pero corre con Node 22.22.
2. Pedile al dev que corra `! tiendanube theme authorize`. Es interactivo: abre el navegador
   y pide pegar el token. Si el navegador tiene abierta la sesión de otra tienda, que lo abra
   en incógnito o use `tiendanube theme authorize --token <TOKEN> -y`. El comando genera
   `.nuvem`, que es una credencial y **jamás se commitea**.

## 3. Git, antes de bajar nada

1. `git init -b main`, si la carpeta no es ya un repo.
2. Creá un `.gitignore` con al menos:

```
.nuvem
.DS_Store
node_modules/
```

3. `git check-ignore .nuvem` tiene que devolver la ruta. Si no la devuelve, no sigas.

## 4. Instalación del tema

1. `tiendanube theme list`. Mirá cuántas instalaciones hay, cuál es la productiva, cuáles son
   legacy y cuáles están forkeadas. Guardá la salida para el paso 6.
2. **Nueva:** `tiendanube theme create --base-theme ipanema --title "<Cliente> | Desarrollo"`.
   `ipanema` es el único base-theme válido. **Existente:** elegí con el dev cuál usar.
3. `tiendanube theme pull --theme-id <ID> -y`. Baja el tema, vincula la carpeta (el id queda
   en `.nuvem`) y genera `manifest.json`. Sin `-y`, en modo no interactivo falla. **Es el
   único pull que se hace sobre la carpeta del proyecto**, porque todavía no hay
   `theme watch`. De acá en adelante, el estado del servidor se lee con un pull a un temporal
   o con `theme diff`, como explica `03-sync-y-reglas.md` del handoff.
4. **Verificá que bajó completo.** El CLI puede decir `Download completed.` habiendo bajado
   solo una parte.
   - `find . -type f -not -path './.*' -not -name manifest.json | wc -l`: anotá el número.
   - `tiendanube theme diff --detailed` no tiene que mostrar nada que esté solo en el
     servidor. Si lo hay, repetí el pull.
   - Si el CLI no tiene `theme diff`, hacé un segundo pull a un directorio temporal (copiando
     `.nuvem` y `manifest.json`) y compará los conteos.
5. **Fork**, si se decidió forkear: pedile al dev que corra `! tiendanube theme fork`.
   Después repetí el pull (4.3) y la verificación (4.4), porque el fork puede traer una versión
   más nueva del tema base. Confirmá en `manifest.json` que dice `"forked": true`. Si no quedó
   forkeado, avisale: todo push de `.tpl`, CSS o JS se va a omitir en silencio.

## 5. El handoff de nube-skills

Si `.docs/handoff/` ya existe, pará y preguntale al dev: este comando es para proyectos
nuevos. Si no existe:

```bash
mkdir -p .docs
cp -R "${CLAUDE_PLUGIN_ROOT}/docs/handoff" .docs/handoff
find "${CLAUDE_PLUGIN_ROOT}/docs/handoff" -type f | wc -l
find .docs/handoff -type f | wc -l
```

Los dos conteos tienen que coincidir. La copia es una foto del handoff a la fecha de hoy y
**no se edita**. Lo propio del proyecto va en `.claude/CLAUDE.md` y en `.docs/`; lo genérico
que se aprenda se lleva a nube-skills.

## 6. `.claude/CLAUDE.md` del proyecto

Leé `.docs/handoff/plantillas/CLAUDE.md` y escribí `.claude/CLAUDE.md` completándolo con:

- los datos del paso 1;
- la salida de `theme list` del paso 4.1, una fila por instalación;
- la URL de preview sin login: `https://<dominio>/?preview_theme_installation_id=<ID>`;
- la versión del plugin: `python3 -c "import json; print(json.load(open('${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json'))['version'])"`;
- `## UI-kit` según la fuente de diseño. Si no hay diseño, reemplazá la tabla por una línea
  que diga que el sistema visual son los tokens del tema;
- `## Bocetos por sección` vacía: se llena sección por sección durante el desarrollo.

Cada marcador `«…»` se reemplaza por su valor o por `pendiente`. Al terminar,
`grep -n '«' .claude/CLAUDE.md` no tiene que devolver nada. **No crees un `CLAUDE.md` en la
raíz**: la documentación va en carpetas con punto, así ninguna versión del CLI la sube al CDN
del tema.

## 7. Líneas de base

```bash
python3 - <<'PY'
import re, json, glob
ok = bad = 0
for f in glob.glob('sections/*.tpl') + glob.glob('blocks/*.tpl'):
    m = re.search(r'\{%\s*schema\s*%\}(.*?)\{%\s*endschema\s*%\}', open(f).read(), re.S)
    if not m: continue
    try: json.loads(m.group(1)); ok += 1
    except Exception as e: bad += 1; print('SCHEMA ROTO', f, e)
print(ok, 'schemas OK,', bad, 'rotos')
PY
python3 "${CLAUDE_PLUGIN_ROOT}/skills/nube-skills-i18n/scripts/audit-i18n.py" .
```

`audit-i18n.py` sale con código 1 si encuentra claves faltantes. Es esperable: el tema base ya
trae algunas y no son regresiones. Anotá en `.claude/CLAUDE.md`, sección "Comandos de
verificación":

- cuántos schemas parsean;
- cuántas claves faltan;
- el conteo de archivos del paso 4.4.

## 8. Commits

1. El tema tal cual se bajó, más el `.gitignore`:

```bash
git add .gitignore manifest.json $(ls -d blocks config custom layouts locales sections snippets static templates translations 2>/dev/null)
git commit -m "chore: kickoff <cliente> — tema base ipanema (installation <ID>)"
```

2. `git status --porcelain` tiene que mostrar solo `.claude/` y `.docs/`. `.nuvem` no aparece,
   porque está ignorado.
3. La documentación:

```bash
git add .claude/CLAUDE.md .docs/handoff
git commit -m "docs: CLAUDE.md del proyecto y handoff de nube-skills <versión>"
```

4. `git log --all -- .nuvem` tiene que dar vacío.

## 9. Repo en GitHub (solo si el dev lo pidió en el paso 1)

Solo si `git log --all -- .nuvem` dio vacío:

```bash
gh repo create Innovate-group/<cliente>-theme --private --source . --push
```

## 10. Cierre

1. `tiendanube theme current`: la carpeta tiene que estar vinculada a la instalación correcta.
2. `git check-ignore .nuvem`: tiene que estar protegido.
3. El conteo del paso 5 tiene que coincidir.
4. Mostrale al dev el resumen: la instalación (id, productiva o borrador, forkeada o no), la
   URL de preview, las líneas de base y los próximos pasos:
   - si el fork quedó pendiente, correrlo (`! tiendanube theme fork`) y repetir el pull del
     paso 4;
   - levantar `tiendanube theme watch` **en su propia terminal** (el agente nunca lo corre);
   - primera tarea, el ui-kit: `.docs/handoff/04-diseno-y-ui-kit.md`;
   - leer `.docs/handoff/README.md` y `01-arranque.md`.
````

- [ ] **Step 3: Validar**

Run: `python3 scripts/validate.py`
Expected: `OK: …`. Las rutas que se chequean son `docs/handoff/README.md`, `docs/handoff`,
`.claude-plugin/plugin.json` y `skills/nube-skills-i18n/scripts/audit-i18n.py`, y todas
existen.

- [ ] **Step 4: Nada del kickoff viejo que el spec saca**

Run: `grep -nE 'Próximamente|theme watch. y arrancar la primera|Creá .CLAUDE.md. en la raíz|locales/ o translations/' commands/kickoff.md`
Expected: sin resultados.

---

### Task 14: Prueba en seco del kickoff y expansión de `${CLAUDE_PLUGIN_ROOT}`

**Files:**
- Test: `$SCRATCH/kickoff-dry/` (repo descartable) y `$SCRATCH/plugin-probe/` (copia del
  plugin con un comando de prueba)

**Interfaces:**
- Consumes: el kickoff (Task 13), el handoff (tareas 3 a 12) y la plantilla (Task 3).
- Produces: la evidencia de que los pasos 3, 5, 6, 7 y 8 del kickoff funcionan, y de que
  `${CLAUDE_PLUGIN_ROOT}` se expande.

- [ ] **Step 1: Simular un tema recién bajado, con una credencial falsa**

```bash
D=$SCRATCH/kickoff-dry && rm -rf "$D" && mkdir -p "$D" && cd "$D"
cp -R /Users/tonchi/Desktop/Innovate/vz-tiendanube-theme/{blocks,config,layouts,sections,snippets,static,templates,translations,manifest.json} .
echo 'credencial-falsa' > .nuvem
export CLAUDE_PLUGIN_ROOT=/Users/tonchi/Desktop/Innovate/nube-skills
```

Nunca copiar el `.nuvem` real de ningún proyecto.

- [ ] **Step 2: Pasos 3 y 5 del kickoff**

```bash
git init -b main -q && printf '.nuvem\n.DS_Store\nnode_modules/\n' > .gitignore && git check-ignore .nuvem
mkdir -p .docs && cp -R "${CLAUDE_PLUGIN_ROOT}/docs/handoff" .docs/handoff
[ "$(find "${CLAUDE_PLUGIN_ROOT}/docs/handoff" -type f | wc -l)" = "$(find .docs/handoff -type f | wc -l)" ] && echo COPIA-OK
```

Expected: `.nuvem` y después `COPIA-OK`.

- [ ] **Step 3: Paso 6: completar la plantilla y verificar que no queden marcadores**

```bash
mkdir -p .claude
python3 - <<'PY'
import re
t = open('.docs/handoff/plantillas/CLAUDE.md', encoding='utf-8').read()
open('.claude/CLAUDE.md', 'w', encoding='utf-8').write(re.sub(r'«[^»]*»', 'valor-de-prueba', t))
PY
grep -c '«' .claude/CLAUDE.md; ls CLAUDE.md 2>&1 | head -1
```

Expected:
- `0`;
- `ls: CLAUDE.md: No such file or directory` (no hay CLAUDE.md en la raíz);
- además, `grep -c '^## UI-kit$\|^## Bocetos por sección$' .claude/CLAUDE.md` da `2`.

- [ ] **Step 4: Paso 7: líneas de base**

Run: `python3 "${CLAUDE_PLUGIN_ROOT}/skills/nube-skills-i18n/scripts/audit-i18n.py" . > "$SCRATCH/i18n.txt"; echo "exit $?"; tail -3 "$SCRATCH/i18n.txt"`
Expected: un resumen de faltantes y exit 0 o 1, sin traceback. Correr también el snippet de
schemas del paso 7 del kickoff: tiene que imprimir `<N> schemas OK, 0 rotos`.

- [ ] **Step 5: Paso 8: los dos commits**

```bash
git add .gitignore manifest.json $(ls -d blocks config custom layouts locales sections snippets static templates translations 2>/dev/null)
git -c user.email=dry@run -c user.name=dry commit -qm "chore: kickoff prueba — tema base ipanema (installation 0)"
git status --porcelain
git add .claude/CLAUDE.md .docs/handoff
git -c user.email=dry@run -c user.name=dry commit -qm "docs: CLAUDE.md del proyecto y handoff de nube-skills 1.5.0"
git log --oneline; git log --all -- .nuvem | wc -l
```

Expected:
- después del primer commit, `git status --porcelain` muestra solo `?? .claude/` y `?? .docs/`;
- `git log` tiene 2 commits;
- el último comando da `0`.

- [ ] **Step 6: Que `${CLAUDE_PLUGIN_ROOT}` se expanda en un comando de plugin**

```bash
P=$SCRATCH/plugin-probe && rm -rf "$P" && cp -R /Users/tonchi/Desktop/Innovate/nube-skills "$P" && rm -rf "$P/.git"
python3 - "$P" <<'PY'
import json, sys, pathlib
p = pathlib.Path(sys.argv[1]) / '.claude-plugin' / 'plugin.json'
d = json.loads(p.read_text()); d['name'] = 'nube-skills-dev'; p.write_text(json.dumps(d, indent=2))
PY
printf -- '---\ndescription: prueba de expansión\n---\nRespondé únicamente con esta línea, sin nada más: RUTA=${CLAUDE_PLUGIN_ROOT}/docs/handoff/README.md\n' > "$P/commands/probe.md"
cd $SCRATCH && claude -p "/nube-skills-dev:probe" --plugin-dir "$P"
```

Expected: una línea `RUTA=<ruta absoluta>/docs/handoff/README.md`, donde `<ruta absoluta>` es
el directorio del plugin (el de `$P` o su copia en caché), **no** el texto literal
`${CLAUDE_PLUGIN_ROOT}`. Si sale el literal, parar: el kickoff no funcionaría y hay que
revisar la documentación de plugins antes de seguir.

- [ ] **Step 7: Limpiar**

Run: `rm -rf "$SCRATCH/kickoff-dry" "$SCRATCH/plugin-probe" "$SCRATCH/validate-fixture" "$SCRATCH/checker-test"`

---

### Task 15: Versión 1.5.0, README y CHANGELOG

**Files:**
- Modify: `.claude-plugin/plugin.json` (`"version": "1.4.0"` → `"1.5.0"`)
- Modify: `README.md` (la fila del kickoff, el paso 1 de "Cómo se encadenan", una sección
  nueva y "Requisitos")
- Modify: `CHANGELOG.md` (entrada nueva arriba de `## 1.4.0`)

**Interfaces:**
- Consumes: todo lo anterior.
- Produces: el release. Sin la versión nueva, `claude plugin update` no baja nada.

- [ ] **Step 1: `.claude-plugin/plugin.json`**

Cambiar `"version": "1.4.0"` por `"version": "1.5.0"`. `marketplace.json` no declara versión:
no se toca.

- [ ] **Step 2: README, la fila del kickoff en el catálogo**

Reemplazar la descripción de la fila `/nube-skills:kickoff` por:
`Arranque de un cliente nuevo: instalación Ipanema con el CLI, pull verificado, git con .nuvem protegido, el handoff de nube-skills en .docs/handoff/ y .claude/CLAUDE.md del proyecto (con el ui-kit que usan las demás skills).`

- [ ] **Step 3: README, el paso 1 de "Cómo se encadenan"**

Reemplazar por:
`1. **Arranque** — /nube-skills:kickoff crea o vincula la instalación de Ipanema, la baja verificando que vino completa, prepara git, copia el handoff a .docs/handoff/ y escribe .claude/CLAUDE.md con la fuente de diseño (Figma, prototipo HTML o ninguna) y el ui-kit.`
(Mantener el formato de código con backticks que usa el README.)

- [ ] **Step 4: README, la sección nueva "El handoff"**, justo después de "Cómo se encadenan"

```markdown
## El handoff

[`docs/handoff/`](docs/handoff/README.md) junta lo aprendido construyendo temas Ipanema reales — María Cher (con sus tiendas de Chile y Uruguay), Garçon García y VZ, entre agosto y septiembre de 2026: qué decidir y qué correr el día 1, cómo se usan estas skills en la práctica y sus problemas conocidos, el protocolo de sync tal como se practica, y las trampas medidas de Twig, CSS, JS, la plataforma y el CLI. Lectura obligatoria: `README` + `01`–`03`; el resto se consulta por tema.

`/nube-skills:kickoff` lo copia a `.docs/handoff/` de cada proyecto nuevo. La copia es una foto del día del kickoff: no se edita ni se actualiza, y los proyectos que ya arrancaron no la reciben. Lo genérico que se aprenda en un proyecto vuelve acá, para el siguiente.
```

- [ ] **Step 5: README, "Requisitos"**

Reemplazar `(Node 24.15+)` por `(declara Node 24.15+; corre con Node 22.22)`.

- [ ] **Step 6: CHANGELOG**, entrada nueva arriba de `## 1.4.0 — 2026-08-24`

```markdown
## 1.5.0 — 2026-09-30

- **El handoff de Ipanema pasa a vivir en el plugin.** [`docs/handoff/`](docs/handoff/README.md) junta lo aprendido en María Cher (con sus tiendas de Chile y Uruguay), Garçon García y VZ. El `HANDOFF-IPANEMA.md` que se venía copiando a mano entre proyectos quedó congelado el 2026-09-03, y lo aprendido después vivía repartido en el `CLAUDE.md` de cada proyecto. Ahora son 16 capítulos por tema (arranque, skills, sync y reglas, diseño y ui-kit, CLI, schema, Twig, plataforma, producto y carrito, CSS, JS, plantillas, límites y Admin API, patrones, verificación, multi-país) más plantillas del `CLAUDE.md` del proyecto, del `ui-kit.md` y de una skill de ui-kit por proyecto. Lectura obligatoria: `README` + `01`–`03`.
- **`/nube-skills:kickoff` copia el handoff al proyecto** (`.docs/handoff/`, desde `${CLAUDE_PLUGIN_ROOT}`) y arma `.claude/CLAUDE.md` desde la plantilla. La copia es una foto del día del kickoff: no se edita ni se refresca, y los proyectos que ya arrancaron no la reciben.
- **El kickoff se alinea con la práctica:** pide la fuente de diseño (Figma, prototipo HTML o ninguna), quién pushea, si se forkea, locales, tiendas hermanas y dominio; usa `tiendanube` y nunca `nuvemshop` (manda `region=br`); crea el `.gitignore` antes de bajar nada; corre `theme list` primero y `theme pull -y`, y verifica que el pull bajó completo; el fork lo corre el dev (ya no figura "Próximamente"); registra líneas de base (schemas, faltantes de i18n, archivos en el servidor); hace dos commits (tema base y documentación), y el agente ya no levanta `theme watch`. El `CLAUDE.md` deja de ir en la raíz.
- `validate.py` chequea que los links del handoff apunten a archivos que existen y que toda ruta `${CLAUDE_PLUGIN_ROOT}/…` de un comando exista en el repo.
- Las skills y el hook no cambian: sus problemas conocidos quedan documentados en `docs/handoff/02-skills.md`, cada uno con cómo esquivarlo.
```

- [ ] **Step 7: Validar**

Run: `python3 scripts/validate.py && grep -n '"version"' .claude-plugin/plugin.json && head -3 CHANGELOG.md`
Expected: `OK: …`, `"version": "1.5.0"` y `## 1.5.0 — 2026-09-30` en la línea 3.

---

### Task 16: Cierre: estado final y propuesta de commits

**Files:** ninguno.

- [ ] **Step 1: Estado final**

Run: `cd /Users/tonchi/Desktop/Innovate/nube-skills && python3 scripts/validate.py && python3 $SCRATCH/check_handoff.py docs/handoff --mapping && git status --short`

Expected: `OK: …`, `0 errores`, y `git status` con esto y nada más:
- `scripts/validate.py`, `commands/kickoff.md`, `.claude-plugin/plugin.json`, `README.md` y
  `CHANGELOG.md` modificados;
- `docs/handoff/` y los dos archivos de `docs/plans/` nuevos.

- [ ] **Step 2: Proponer los commits al dev y esperar la orden** (no ejecutar)

Propuesta:
1. `feat(validate): links del handoff y rutas ${CLAUDE_PLUGIN_ROOT} de los comandos`: `scripts/validate.py`.
2. `docs: handoff de Ipanema en el plugin`: `docs/handoff/`.
3. `feat(kickoff): copia el handoff y arma .claude/CLAUDE.md desde la plantilla`: `commands/kickoff.md`.
4. `chore: v1.5.0`: `.claude-plugin/plugin.json`, `README.md`, `CHANGELOG.md` y los dos
   archivos de `docs/plans/`.

Recordarle también al dev el checklist del spec para el **primer proyecto real**: `authorize`, `list`, `create`, `pull -y` con conteo, `fork`, `theme current`, y que la copia del handoff salga desde el plugin instalado.

Cada uno con el trailer de co-autoría que indique la sesión. Push a `origin main` solo si el
dev lo pide. Después del push, y también solo si el dev lo pide, verificar la CI con
`gh run list --limit 1`.
