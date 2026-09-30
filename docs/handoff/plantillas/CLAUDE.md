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
