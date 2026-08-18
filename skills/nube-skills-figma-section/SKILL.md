---
name: nube-skills-figma-section
description: "Convert Figma designs into TiendaNube sectionable theme code (Ipanema base). Use when the user provides a Figma link or node (figma.com URL, 'este nodo', 'implementá esta sección del boceto', 'pasá este diseño a código', 'maquetá esto') while working on a TiendaNube section-based theme: extracts the design via the Figma MCP, triages whether to configure/restyle an existing section or build a custom one, and generates the section/block .tpl with {% schema %}, settings-first values, translations in all locales, and registration in the page's JSON template. Triggers: figma to section, nodo de figma, diseño de figma, design-to-code tienda nube, figma.com URL + tema sectionable/Ipanema. Requires the official Figma MCP connected. NOT for Shopify themes (.liquid) and NOT for classic TiendaNube .tpl themes (snipplets/, settings.txt — use the legacy tiendanube-* skills)."
---

# Figma → Section (temas sectionable de Tienda Nube)

Convierte un nodo de Figma (desktop + mobile) en código de un tema sectionable de Tienda Nube. No genera siempre una section nueva: primero hace **triage** para decidir la intervención mínima (configurar lo existente → re-estilizar → extender → custom). Filosofía **settings-first**: todo lo que el comerciante pueda querer editar (textos, imágenes, colores, espaciados) va a settings del schema con defaults sacados del Figma — nunca hardcodeado.

Esta skill asume el contexto de `nube-skills-themes` (anatomía de sections/blocks/snippets, schema, reglas duras). Si no está cargada, leé sus referencias antes de generar código — en particular `sections-blocks-snippets.md` y `schema-settings-i18n.md`.

## Paso 0 — Prerrequisitos (verificar SIEMPRE antes de empezar)

1. **Tema sectionable:** confirmá que el proyecto es un tema nuevo de Tienda Nube (detección del Paso 0 de `nube-skills-themes`). Si es un tema clásico o Shopify, detenete y derivá.
2. **MCP de Figma conectado:** las herramientas `get_design_context` / `get_screenshot` deben estar disponibles. Si no, avisá que hay que conectar el MCP oficial de Figma.
3. **Estado de fork:** leé `forked` en `manifest.json`. Es la restricción que gobierna el triage:
   - `forked: true` → todas las ramas del triage disponibles.
   - `forked: false` → **solo la rama A (Configurar)** produce cambios deployables: sin fork solo son editables `templates/**`, `custom/**` y `config/settings_data.json` — `theme push` omite silenciosamente todo lo demás (`sections/`, `blocks/`, `snippets/`, `layouts/`, `static/`, las traducciones y `config/settings_schema.json`). Si el diseño exige B/C/D, avisale al dev que necesita `theme fork` antes de continuar (y que el comando figura "Próximamente" en la doc — verificar disponibilidad real).
4. **Inputs de diseño:** pedí los links de Figma de la sección en **desktop y mobile** ("Copy link to selection" — la URL contiene el `node-id`). Si solo hay un breakpoint, avisá que el responsive va a seguir las convenciones del proyecto y continuá.
5. **UI-kit del proyecto (SIEMPRE):** antes de generar cualquier componente o section, localizá el ui-kit del rediseño (el archivo/página de Figma con colores, tipografías y componentes base). Buscá su link en el `CLAUDE.md` del proyecto o en tu memoria persistente; si no lo encontrás, **preguntale al dev dónde está y guardalo para no volver a preguntarlo** — preferentemente en el `CLAUDE.md` del proyecto (lo comparte todo el equipo), o en tu memoria si el proyecto no tiene `CLAUDE.md`.
6. **Preguntas obligatorias al dev** (por sección, antes de generar):
   - ¿La sección tiene **estados interactivos** (hover, focus, activo, abierto/cerrado, animaciones)? Los screenshots estáticos no los muestran: si los hay, pedí los nodos o variantes de Figma de esos estados, o una descripción de cada uno.
   - ¿Querés agregar el **toggle de visibilidad interna**? (setting booleano para que la sección solo la vean usuarios logueados con email `@innovategroup` — sirve para revisar secciones en producción sin exponerlas a compradores).

## Paso 1 — Extraer el diseño

Por cada nodo (desktop y mobile):

1. `get_screenshot` → referencia visual del resultado esperado.
2. `get_design_context` → estructura, estilos y contenido reales del nodo. Si el archivo usa variables/design tokens, `get_variable_defs` para ver los valores con nombre.
3. Contrastá los estilos del nodo contra el **ui-kit** (Paso 0.5): si un color, tipografía o componente está definido en el ui-kit, ese valor con nombre manda sobre el valor suelto del nodo — el componente generado debe reutilizar el sistema, no clonar píxeles.

Con ambos breakpoints, armá el análisis en tres capas antes de escribir código:

| Capa | Qué identificar |
|---|---|
| **Estructura** | Contenedor, grillas, elementos repetidos (→ candidatos a blocks), jerarquía de contenido, diferencias de layout desktop vs mobile |
| **Contenido editable** | Títulos, textos, imágenes, CTAs, links — TODO esto será un setting |
| **Estilo** | Colores, tipografías, espaciados, bordes, radios — mapear contra los tokens/settings globales del tema antes de decidir valores propios |

## Paso 2 — Triage (la decisión central)

Antes de decidir, inventariá el proyecto real:

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

### Mapeo Figma → settings

Regla de oro: **ningún texto, imagen o color del Figma se hardcodea**. Cada valor va a un setting con el valor del Figma como `default`:

| En el Figma | Setting | Notas |
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
- **CSS y responsive:** antes de escribir CSS, mirá cómo lo hacen 2-3 sections existentes del proyecto (dónde vive el CSS, convención de clases, breakpoints, uso de custom properties de `style-tokens.tpl`) y replicá ese patrón. El breakpoint mobile sale del nodo mobile del Figma. Si el valor existe como token del tema, usá el token — no su valor absoluto copiado.
- **Settings de espaciado (OBLIGATORIAS en toda section generada):** 4 settings `range` de padding — `padding_top`, `padding_bottom`, `padding_top_mobile`, `padding_bottom_mobile` — con `unit` px y defaults medidos del Figma (desktop y mobile respectivamente). Si el proyecto ya trae una convención de nombres para el espaciado (ej. `vertical_padding` en sections de Ipanema), respetá esos nombres y completá lo que falte hasta cubrir top/bottom × desktop/mobile.
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

Los valores en español salen del Figma; para los demás locales traducí con criterio comercial (es/es_AR/es_MX/pt según el proyecto).

## Paso 4 — Registrar en la página

1. **Preset:** el `{% schema %}` de toda section nueva lleva `presets` con settings y blocks iniciales (los valores del Figma) — así el comerciante puede agregarla desde el editor.
2. **JSON template:** agregá la entrada en `templates/pages/<página>.json` — `sections` con un id descriptivo, sus `settings`, sus `blocks` con `block_order`, y el id en el `order` de la página en la posición que indica el boceto. Si la página destino no es obvia por el contexto, preguntá cuál es antes de tocar el JSON.
3. Si la rama fue A, este paso ES todo el trabajo: configurar la entrada del JSON con los settings que reproducen el diseño.

## Paso 5 — Verificar

1. Si `theme watch` está corriendo, los cambios ya se pushearon; si no, `tiendanube theme push` y abrí la preview (`tiendanube theme preview`).
2. Compará la preview contra los screenshots del Paso 1 — desktop Y mobile.
3. Checklist mínimo antes de dar por terminada la section:
   - [ ] El JSON del `{% schema %}` parsea (sin comas colgantes ni comentarios).
   - [ ] Toda clave `t:` existe en TODOS los `*.schema.json` del proyecto.
   - [ ] Todo block tiene `block_attributes` en su elemento raíz.
   - [ ] Ningún texto/imagen/color hardcodeado que debiera ser setting.
   - [ ] Sin fork: confirmá que NO editaste archivos que push omite (si la rama fue B/C/D con `forked: false`, algo salió mal en el triage).
   - [ ] La entrada del JSON template respeta `order`/`block_order` del boceto.
   - [ ] Las 4 settings de padding (top/bottom × desktop/mobile) existen y el CSS las aplica.
   - [ ] Los estados interactivos declarados por el dev (hover, etc.) están implementados.
   - [ ] Si se pidió el toggle interno: probado logueado con email `@innovategroup` (se ve) y como visitante anónimo (no se ve).

## Reglas duras

Aplican las 7 reglas duras de `nube-skills-themes` (block_attributes, snippets `_`, slots nubesdk/data-store, claves t: completas, precios en centavos, `.tpl`, límites sin fork). Propias de esta skill:

1. **Settings-first sin excepciones de contenido:** textos, imágenes y CTAs jamás hardcodeados en el `.tpl`.
2. **Imágenes solo vía `snippets/image.tpl`** — nunca un `<img>` crudo con la URL exportada de Figma.
3. **Tokens antes que valores absolutos:** si el color/tipografía/espaciado existe como token o setting global, referencialo; copiá el valor del Figma solo cuando es único de esta section.
4. **No inventes claves de schema:** solo las documentadas en las referencias de `nube-skills-themes`.
5. **Triage antes que código:** nunca arranques por la rama D sin haber revisado el inventario del proyecto.

## Qué NO hace esta skill

- QA visual exhaustivo contra el Figma (diferencias finas de espaciado/tipografía) → será `nube-skills-qa`.
- Arranque de proyecto/instalación → será `/nube-skills:kickoff`.
- Escribir EN Figma (generar diseños) — solo lee.
