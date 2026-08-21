---
name: nube-skills-section
description: "Build sections, blocks and components for TiendaNube sectionable themes (Ipanema base), from a Figma design or from scratch. Use when the user provides a Figma link or node ('implementá esta sección del boceto', 'pasá este diseño a código') OR asks for a new section/block/component without any mockup ('necesito una sección de X', 'creá un bloque de Y') while working on a TiendaNube section-based theme: extracts the design via the Figma MCP — or drafts one first with the design skill when there is no mockup — triages whether to configure/restyle an existing section or build a custom one, and generates the .tpl with {% schema %}, settings-first values, translations in all locales, and registration in the page's JSON template. Triggers: figma to section, nodo de figma, crear sección/bloque/componente tienda nube, design-to-code, Ipanema. NOT for Shopify themes (.liquid) and NOT for classic TiendaNube .tpl themes (snipplets/, settings.txt — use the legacy tiendanube-* skills)."
---

# Diseño → Section (temas sectionable de Tienda Nube)

Convierte un diseño en desktop + mobile —un nodo de Figma, o un mockup dibujado con la skill `design` cuando el dev no tiene boceto— en código de un tema sectionable de Tienda Nube. No genera siempre una section nueva: primero hace **triage** para decidir la intervención mínima (configurar lo existente → re-estilizar → extender → custom). Filosofía **settings-first**: todo lo que el comerciante pueda querer editar (textos, imágenes, colores, espaciados) va a settings del schema con defaults sacados del diseño — nunca hardcodeado.

Esta skill asume el contexto de `nube-skills-themes` (anatomía de sections/blocks/snippets, schema, reglas duras). Si no está cargada, leé sus referencias antes de generar código — en particular `sections-blocks-snippets.md` y `schema-settings-i18n.md`.

## Paso 0 — Prerrequisitos (verificar SIEMPRE antes de empezar)

1. **Tema sectionable:** confirmá que el proyecto es un tema nuevo de Tienda Nube (detección del Paso 0 de `nube-skills-themes`). Si es un tema clásico o Shopify, detenete y derivá.
2. **Herramienta de diseño disponible:** con boceto (Vía A), las herramientas `get_design_context` / `get_screenshot` del MCP oficial de Figma deben estar activas — si no lo están, avisá que hay que conectarlo. Sin boceto (Vía B), el MCP no hace falta: lo que tiene que estar disponible es la skill `design`.
3. **Estado de fork:** leé `forked` en `manifest.json`. Es la restricción que gobierna el triage:
   - `forked: true` → todas las ramas del triage disponibles.
   - `forked: false` → **solo la rama A (Configurar)** produce cambios deployables: sin fork solo son editables `templates/**`, `custom/**` y `config/settings_data.json` — `theme push` omite silenciosamente todo lo demás (`sections/`, `blocks/`, `snippets/`, `layouts/`, `static/`, las traducciones y `config/settings_schema.json`). Si el diseño exige B/C/D, avisale al dev que necesita `theme fork` antes de continuar (y que el comando figura "Próximamente" en la doc — verificar disponibilidad real).
4. **Inputs de diseño:** pedí los links de Figma de la sección en **desktop y mobile** ("Copy link to selection" — la URL contiene el `node-id`). Si solo hay un breakpoint, avisá que el responsive va a seguir las convenciones del proyecto y continuá. **Si el dev no tiene boceto**, no improvises el diseño mientras escribís código: seguí la Vía B del Paso 1.
5. **UI-kit del proyecto (SIEMPRE):** antes de generar cualquier componente o section, ubicá el ui-kit. **No es un solo boceto: es un conjunto de nodos** (colores, tipografías, botones, formularios, cards, iconografía, espaciados/grid), y vive en la tabla **`## UI-kit`** del `CLAUDE.md` del proyecto — ahí lo deja `/nube-skills:kickoff`.
   - **Leé solo los nodos que esta sección necesita**, no los siete: para un hero alcanza con colores, tipografías y botones. Cargar todo el ui-kit en cada sección es desperdicio de contexto.
   - Si un nodo figura como `pendiente`, seguí sin él y avisale al dev qué quedó sin respaldo del sistema.
   - Si **no hay tabla** de UI-kit (proyecto que no arrancó con el kickoff), preguntale al dev por los nodos y **escribí la tabla en el `CLAUDE.md`** para no volver a preguntar. Si el proyecto no tiene `CLAUDE.md`, guardalo en tu memoria persistente.
   - Si el proyecto **no tiene ui-kit** en Figma, el sistema visual son los tokens del tema (`layouts/resources/style-tokens.tpl` + `config/settings_schema.json`): construí contra esos.
6. **Sync antes de escribir (el último chequeo, pegado a la primera escritura):** corré el gate del Paso 0.5 de `nube-skills-themes` — commit/stash → `git pull --ff-only` → `tiendanube theme pull` → `git diff`. El comerciante edita `templates/**` y `config/settings_data.json` desde el editor mientras vos trabajás, y `theme push` sincroniza eliminaciones: registrar la sección con un JSON template viejo **borra de la tienda las secciones que él agregó**. Si el pull trae cambios sobre lo que ibas a tocar, mostrale los dos valores al dev antes de decidir. Chequeo determinista: `python3 <carpeta-de-nube-skills-themes>/scripts/sync-check.py . --files templates/pages/<página>.json`.
7. **Preguntas obligatorias al dev** (por sección, antes de generar):
   - ¿La sección tiene **estados interactivos** (hover, focus, activo, abierto/cerrado, animaciones)? Ninguna referencia estática los muestra —ni un screenshot de Figma ni un artboard—: si los hay, pedí los nodos o variantes de Figma de esos estados (Vía A) o una descripción escrita de cada uno (Vía B), y anotalos antes de codear.
   - ¿Querés agregar el **toggle de visibilidad interna**? (setting booleano para que la sección solo la vean usuarios logueados con email `@innovategroup` — sirve para revisar secciones en producción sin exponerlas a compradores).

## Paso 1 — Obtener el diseño

Dos vías según lo que tenga el dev. **Vía A** (lo normal): hay boceto de Figma. **Vía B**: no hay boceto — se diseña primero y se codea después.

### Vía A — Extraer el nodo de Figma

Por cada nodo (desktop y mobile):

1. `get_screenshot` → referencia visual del resultado esperado.
2. `get_design_context` → estructura, estilos y contenido reales del nodo. Si el archivo usa variables/design tokens, `get_variable_defs` para ver los valores con nombre.
3. Contrastá los estilos del nodo contra el **ui-kit** (Paso 0.5): si un color, tipografía o componente está definido en el ui-kit, ese valor con nombre manda sobre el valor suelto del nodo — el componente generado debe reutilizar el sistema, no clonar píxeles.

### Vía B — Sin boceto: diseñar primero con la skill `design`

Cuando el dev no tiene diseño (pasa poco, pero pasa), **no arranques a codear a ojo**: primero se acuerda el diseño visualmente y recién después se genera el código.

1. **Juntá el contexto** antes de invocar nada: qué sección es y qué debe comunicar, contenido real o de ejemplo (títulos, textos, imágenes, CTAs), en qué página va y en qué lugar, y referencias que le gusten al dev. Adelantá acá el inventario del Paso 2 (`ls sections/ blocks/`): si una section existente ya cubre el pedido, el mockup parte de ella en vez de inventar una estructura nueva que después haya que codear de cero.
2. **Tomá el sistema visual del proyecto** — es lo que hace que el mockup no salga genérico: el **ui-kit** (Paso 0, ítem 5) y, si el tema ya está bajado, los tokens reales (`layouts/resources/style-tokens.tpl`, `config/settings_schema.json`) y 2-3 sections ya construidas. La skill `design` no lee Figma: esos colores, tipografías y espaciados se los pasás vos escritos en el prompt.
3. **Invocá la skill `design`** con ese contexto, pidiendo **dos artboards en un mismo canvas: desktop y mobile**, con los valores del ui-kit/tokens — no con una paleta inventada. Vos dibujás el draft; el dev lo revisa en el Artifact publicado y, si su cuenta tiene el guardado habilitado, ajusta los elementos ahí mismo y publica una versión nueva; si no, solo lo ve o lo exporta y te devuelve los cambios. Esa skill solo **crea** o re-siembra un canvas: si hay que rehacerlo de raíz, invocala de nuevo con el contexto corregido.
4. **Con el mockup aprobado, seguí el flujo normal desde el Paso 2**, usando los artboards como referencia en lugar del nodo de Figma: dan estructura, jerarquía, valores y la imagen contra la que comparás en el Paso 5. Si el dev guardó cambios en el canvas, la versión publicada manda sobre tu `.dc.html` local — leela antes de codear. **El artboard no es código de producción:** no copies su HTML/CSS al `.tpl` — el markup, las clases y el CSS se escriben con las convenciones del tema (Paso 3).
5. **Dejá registro:** guardá el link del canvas en el `CLAUDE.md` del proyecto junto a los links de Figma. Si después el diseñador hace el boceto "oficial" en Figma, ese pasa a ser la fuente de verdad.

Si la skill `design` no está disponible en el entorno del dev, pedile una descripción escrita de la sección (estructura, contenido y referencias) y confirmá con él la estructura propuesta **antes** de escribir código.

### Análisis previo al código (ambas vías)

Con los dos breakpoints resueltos, armá el análisis en tres capas antes de escribir código:

| Capa | Qué identificar |
|---|---|
| **Estructura** | Contenedor, grillas, elementos repetidos (→ candidatos a blocks), jerarquía de contenido, diferencias de layout desktop vs mobile |
| **Contenido editable** | Títulos, textos, imágenes, CTAs, links — TODO esto será un setting |
| **Estilo** | Colores, tipografías, espaciados, bordes, radios — mapear contra los tokens/settings globales del tema antes de decidir valores propios |

## Paso 2 — Triage (la decisión central)

Aplica a las dos vías. Antes de decidir, inventariá el proyecto real (si venís de la Vía B ya lo hiciste — repasá lo que encontraste):

```bash
ls sections/ blocks/
```

y leé el `{% schema %}` de las 2-3 sections candidatas más parecidas al diseño (su `name`, sus `settings`, qué `blocks` aceptan). Después elegí **la rama más baja que satisfaga el diseño** — menos código nuevo = menos mantenimiento:

| Rama | Cuándo | Qué se toca | ¿Requiere fork? |
|---|---|---|---|
| **A — Configurar** | Una section existente ya logra el diseño con sus settings | `templates/pages/*.json` (+ `config/settings_data.json`) | No |
| **B — Re-estilizar** | Misma estructura, distinta piel (colores, tipografías, espaciados) | Tokens/defaults globales (`config/settings_schema.json`, `layouts/resources/style-tokens.tpl`) y/o CSS en `static/` | Sí |
| **C — Extender** | Una section existente casi alcanza: le faltan settings o un tipo de block | El `.tpl` y `{% schema %}` de esa section; blocks nuevos en `blocks/` | Sí |
| **D — Custom** | Estructura nueva que ninguna section cubre | Section nueva en `sections/` (+ blocks propios si hace falta) | Sí |

Criterios rápidos: si el diseño solo cambia contenido y orden → A. Si cambia la estética global (aplica a varias secciones) → B, sobre tokens, no sobre una section puntual. Si hay un elemento repetido nuevo dentro de una section conocida → C. Solo si la estructura no existe → D.

**Comunicá la decisión antes de generar:** "esto se resuelve con la rama X porque..." — si el dev esperaba otra cosa, es el momento de corregir.

## Paso 3 — Generar (settings-first)

### Mapeo diseño → settings

Regla de oro: **ningún texto, imagen o color del diseño se hardcodea** (venga del nodo de Figma o del artboard). Cada valor va a un setting con el valor del diseño como `default`:

| En el diseño | Setting | Notas |
|---|---|---|
| Título / texto corto | `text` | Default con clave `t:defaults.<section>.<campo>` |
| Párrafo con formato | `richtext` | Ídem |
| Imagen / ilustración | `image_picker` | Render SIEMPRE vía `snippets/image.tpl` (responsive AVIF/WebP); el valor se resuelve con `resolve_media` |
| Botón / CTA | `url` + `text` (label) | Label con default `t:` |
| Color puntual | `color` | Si coincide con un color global del tema → `default_setting: "<id-global>"` en lugar de duplicar el hex |
| Espaciado / tamaño variable | `range` | Con `min`/`max`/`step`/`unit` razonables |
| Variante de layout (2-3 opciones) | `select` o `radio` | Opciones con labels `t:options.*` |
| Alineación | `text_alignment` / `alignment` | `alignment` genera también `settings.<id>_vertical` |

La sintaxis exacta de cada `setting_type` está en `nube-skills-themes` → `references/schema-settings-i18n.md`. Es la de Tienda Nube (`{"type": "setting", "setting_type": ...}`), no la de Shopify.

### Estructura y código

- Elementos repetidos del diseño (cards, slides, logos, features) → **blocks**, no markup duplicado. La section los itera con `{% include 'blocks/' ~ block.type ~ '.tpl' with { block: block } %}`. Si el proyecto ya tiene blocks genéricos que sirven (heading, text, button, image), aceptalos por `{ "tags": ["general"] }` en lugar de crear duplicados.
- Todo block nuevo: `{{ block | block_attributes }}` en el elemento raíz — sin excepción.
- Anatomía de la section (markup arriba, `{% schema %}` al final, `{% set settings = section.settings %}`): seguí el patrón canónico de `nube-skills-themes` y el estilo de las sections existentes del proyecto.
- **CSS y responsive:** antes de escribir CSS, mirá cómo lo hacen 2-3 sections existentes del proyecto (dónde vive el CSS, convención de clases, breakpoints, uso de custom properties de `style-tokens.tpl`) y replicá ese patrón. El layout mobile sale de la referencia mobile (nodo de Figma o artboard), pero el breakpoint en sí es el del proyecto. Si el valor existe como token del tema, usá el token — no su valor absoluto copiado.
- **Settings de espaciado (OBLIGATORIAS en toda section generada):** 4 settings `range` de padding — `padding_top`, `padding_bottom`, `padding_top_mobile`, `padding_bottom_mobile` — con `unit` px y defaults medidos de la referencia (desktop y mobile respectivamente). Si el proyecto ya trae una convención de nombres para el espaciado (ej. `vertical_padding` en sections de Ipanema), respetá esos nombres y completá lo que falte hasta cubrir top/bottom × desktop/mobile.
- **Toggle de visibilidad interna (solo si el dev lo pidió en el Paso 0):** setting `toggle` (no `checkbox`, que está marcado legacy) con id `internal_only`, `default: false`, label `t:` explicando su función. El render completo de la section se envuelve en:

  ```twig
  {% if not section.settings.internal_only or (customer and '@innovategroup' in customer.email) %}
    {# ...toda la section... #}
  {% endif %}
  ```

- Nombre de archivo: descriptivo y en el idioma de las sections existentes del proyecto (ej. `sections/logos-marquee.tpl`). No usar prefijo `main-` salvo que sea el contenido principal de un tipo de página.

### Traducciones

Por cada clave `t:` nueva (names, settings, options, defaults, info):

1. Listá los locales del proyecto (`ls translations/ || ls locales/` — la carpeta varía según cómo bajó el tema).
2. Agregá la clave en **TODOS** los `<locale>.schema.json`. Una clave faltante se muestra cruda en el editor.
3. Textos visibles para el comprador que no sean settings → `<locale>.json` + filtro `| t`.

Los valores en español salen del diseño; para los demás locales traducí con criterio comercial (es/es_AR/es_MX/pt según el proyecto).

## Paso 4 — Registrar en la página

Este paso escribe **el archivo que el comerciante edita desde el editor**. Si desde el gate del Paso 0 pasó un rato, o el dev estuvo mostrándole la tienda, **re-pulleá antes de tocar el JSON** (`tiendanube theme pull` + `git diff`) y quedate con las secciones que él haya agregado: no las borres del `order` para "dejarlo como el diseño".

1. **Preset:** el `{% schema %}` de toda section nueva lleva `presets` con settings y blocks iniciales (los valores del diseño) — así el comerciante puede agregarla desde el editor.
2. **JSON template:** agregá la entrada en `templates/pages/<página>.json` — `sections` con un id descriptivo, sus `settings`, sus `blocks` con `block_order`, y el id en el `order` de la página en la posición que indica el diseño. Si la página destino no es obvia por el contexto, preguntá cuál es antes de tocar el JSON.
3. Si la rama fue A, este paso ES todo el trabajo: configurar la entrada del JSON con los settings que reproducen el diseño.
4. **Dejá rastro del diseño:** agregá la fila de esta sección a la tabla `## Bocetos por sección` del `CLAUDE.md` (nombre de la sección + nodo desktop + nodo mobile, o el link del canvas si fue Vía B). Así queda trazable qué diseño originó qué código — y es lo que `nube-skills-qa` va a usar como referencia para el QA visual. Si la tabla no existe, creala.

## Paso 5 — Verificar

1. Si `theme watch` está corriendo, los cambios ya se pushearon; si no, `tiendanube theme push` y abrí la preview (`tiendanube theme preview`).
2. Compará la preview contra la referencia del Paso 1 — desktop Y mobile: los screenshots del nodo en Vía A, los artboards del canvas en Vía B.
3. Checklist mínimo antes de dar por terminada la section:
   - [ ] El JSON del `{% schema %}` parsea (sin comas colgantes ni comentarios).
   - [ ] Toda clave `t:` existe en TODOS los `*.schema.json` del proyecto.
   - [ ] Todo block tiene `block_attributes` en su elemento raíz.
   - [ ] Ningún texto/imagen/color hardcodeado que debiera ser setting.
   - [ ] Sin fork: confirmá que NO editaste archivos que push omite (si la rama fue B/C/D con `forked: false`, algo salió mal en el triage).
   - [ ] La entrada del JSON template respeta `order`/`block_order` del diseño **y conserva las secciones que ya estaban** (ninguna entrada del comerciante quedó fuera del `order`).
   - [ ] Las 4 settings de padding (top/bottom × desktop/mobile) existen y el CSS las aplica.
   - [ ] Los estados interactivos declarados por el dev (hover, etc.) están implementados.
   - [ ] Si se pidió el toggle interno: probado logueado con email `@innovategroup` (se ve) y como visitante anónimo (no se ve).

## Reglas duras

Aplican las 8 reglas duras de `nube-skills-themes` (block_attributes, snippets `_`, slots nubesdk/data-store, claves t: completas, precios en centavos, `.tpl`, límites sin fork, **sync antes de escribir**). Propias de esta skill:

1. **Settings-first sin excepciones de contenido:** textos, imágenes y CTAs jamás hardcodeados en el `.tpl`.
2. **Imágenes solo vía `snippets/image.tpl`** — nunca un `<img>` crudo con la URL exportada de Figma ni con la imagen embebida del artboard.
3. **Tokens antes que valores absolutos:** si el color/tipografía/espaciado existe como token o setting global, referencialo; copiá el valor del diseño solo cuando es único de esta section.
4. **No inventes claves de schema:** solo las documentadas en las referencias de `nube-skills-themes`.
5. **Triage antes que código:** nunca arranques por la rama D sin haber revisado el inventario del proyecto.

## Qué NO hace esta skill

- QA visual exhaustivo contra el diseño (diferencias finas de espaciado/tipografía) → será `nube-skills-qa`.
- Arranque de proyecto/instalación → será `/nube-skills:kickoff`.
- Escribir EN Figma — de Figma solo lee. Cuando no hay boceto, el mockup se dibuja en un canvas aparte con la skill `design` (Vía B), que tampoco escribe en Figma ni genera código de producción.
