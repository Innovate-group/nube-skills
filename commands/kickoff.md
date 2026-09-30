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
