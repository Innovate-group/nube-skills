---
name: nube-skills-themes
description: "Expert skill for TiendaNube/Nuvemshop NEW section-based themes (Fork Workflow, Ipanema base theme). Use when creating or modifying sections, blocks, snippets, JSON page templates, inline {% schema %} blocks, config/settings_schema.json, JSON translations, or when using the Tiendanube CLI (theme authorize/pull/push/watch/fork/publish/preview). Also defines the mandatory sync gate before writing any theme file (git pull + tiendanube theme pull + diff), since the merchant edits templates/** and config/settings_data.json from the store editor and push syncs deletions. Triggers: sectionable, tema seccionable, Ipanema, Fork Workflow, tiendanube CLI, {% schema %}, block_attributes, JSON template, theme watch, .nuvem, manifest.json, pull antes de editar, pisar cambios del comerciante, sincronizar el tema. NOT for classic/legacy TiendaNube themes (config/settings.txt, snipplets/ — use tiendanube-theme-config or tiendanube-objects) and NOT for Shopify themes (.liquid — use shopify-liquid skills)."
---

# Tiendanube Sectionable Themes

## 1. Overview

Cubre el modelo NUEVO de temas de Tienda Nube: "diseños basados en secciones" (sectionable), donde las páginas se componen con JSON templates que referencian sections y blocks `.tpl` (Twig 2.x) con schema inline, y el desarrollo se hace vía CLI `@tiendanube/cli` (Fork Workflow). Hoy el único tema base disponible es **Ipanema**. Esta skill cubre SOLO esa generación — no el modelo clásico `.tpl` + `config/*.txt` + FTP.

## 2. Paso 0 — Detectar la generación del tema (SIEMPRE PRIMERO)

Antes de tocar cualquier archivo, listá la raíz del proyecto (`ls` sobre raíz y `config/`) y clasificá con esta tabla:

| Marcador | Tema NUEVO (esta skill) | Tema CLÁSICO TN | Tema Shopify |
|---|---|---|---|
| Config | `config/settings_schema.json` + `config/settings_data.json` | `config/settings.txt` (marcador más fuerte), `defaults.txt`, `translations.txt`, `sections.txt` | `config/settings_schema.json` (formato Shopify: array de secciones con `settings`) |
| Partials | `snippets/` (sin "l") | `snipplets/` (con "l") | `snippets/` con archivos `.liquid` |
| Templates | `templates/pages/*.json` + `templates/layout/header.json\|footer.json` | `.tpl` en raíz del tema, layout típico `<repo>/theme/` | `templates/*.liquid\|*.json`, `layout/theme.liquid` |
| Schema inline | `{% schema %}` al final de `.tpl` en `sections/` y `blocks/` | Sin schema inline | `{% schema %}` dentro de `.liquid` |
| Tooling | `.nuvem`, `manifest.json` (CLI) | FTP, sin manifest | `shopify.theme.toml`, `.shopify/` |
| Traducciones | `translations/` (o `locales/`) con `<locale>.json` + `<locale>.schema.json` | `config/translations.txt` | `locales/*.json` formato Shopify |

**Salidas posibles:**

1. **Tema NUEVO** (`.tpl` con `{% schema %}` + JSON templates + `snippets/`): continuá con esta skill.
2. **Tema CLÁSICO TN** (`config/settings.txt` + `snipplets/`): **detenete y NO apliques nada de esta skill.** Derivá a las skills legacy: `tiendanube-theme-config` (settings/config), `tiendanube-objects` (objetos y filtros `.tpl`), `tiendanube-bootstrap-frontend` (UI/Bootstrap 4), `tiendanube-javascript-api` (carrito/LS/store.js), `tiendanube-landing-pages` (landings por handle).
3. **Tema Shopify** (`.liquid`, `layout/` singular, `locales/` formato Shopify): derivá a las skills `shopify-liquid` / `shopify-*`.

**Regla anti-falso-positivo:** `settings_schema.json` también existe en temas Shopify — **nunca clasifiques por ese archivo solo**. Confirmá siempre con al menos otro marcador (extensión `.tpl` vs `.liquid`, `snippets/` vs `snipplets/`, presencia de `.nuvem`).

## 3. Paso 0.5 — Sync antes de escribir (SIEMPRE antes de la primera escritura)

El tema no es solo tuyo: **el comerciante edita la tienda desde el editor mientras vos trabajás**, y eso escribe archivos reales de la instalación. Si editás sobre una copia local vieja y pusheás, no solo pisás sus valores — `theme push` **sincroniza eliminaciones**, así que las secciones que él agregó y tu copia no tiene **se borran de la tienda**. No hay deshacer: el CLI no versiona, la única red de seguridad es git.

| Archivo | Quién más lo escribe | Qué se pierde si escribís con copia vieja |
|---|---|---|
| `templates/pages/*.json`, `templates/layout/*.json` | El comerciante desde el editor: qué secciones hay, su `order`, sus settings | Su configuración y las secciones que agregó |
| `config/settings_data.json` | El comerciante desde el editor: colores, tipografías, logo | La identidad visual guardada de la tienda |
| `config/settings_schema.json`, `sections/`, `blocks/`, `snippets/`, `layouts/`, `static/`, `translations/` \| `locales/` | Otros devs (git) y las actualizaciones del tema base | Commits de un compañero o una actualización de Ipanema |

Ojo con la ironía del fork: **sin fork lo único que podés pushear es justo lo que el comerciante también edita** (`templates/**` y `config/settings_data.json`). La falta de fork no protege nada acá.

**El gate, antes de la primera escritura de cada tarea:**

```bash
git status --porcelain    # 1. ¿algo sin commitear? → commit o stash: `theme pull` SOBRESCRIBE
git pull --ff-only        # 2. commits de otros devs (si el repo tiene remoto)
tiendanube theme pull     # 3. estado real de la tienda = lo que guardó el comerciante
git status && git diff    # 4. lo que apareció y no escribiste vos ES del comerciante
```

Los pasos 1 y 3 son las dos caras del mismo riesgo: el 1 evita que **el pull** borre tu trabajo, el 3 evita que **el push** borre el del comerciante. Ninguno de los dos avisa.

Todo lo que el paso 4 muestre en `templates/**` o `config/settings_data.json` y no hayas escrito vos se commitea **aparte** (`chore: sync cambios del comerciante`) antes de editar encima: así tu diff queda limpio y el suyo, trazable. **Si el pull trae un cambio sobre lo mismo que ibas a tocar, no mergees a ojo:** el valor que guardó el comerciante gana por default — mostrale los dos valores al dev y esperá la decisión.

Se repite el gate, aunque ya lo hayas corrido en la sesión, antes de tocar `templates/**` o `config/settings_data.json`, si pasó un rato largo (~30 min), tras una pausa, y **siempre** antes de `theme push --force` y de `theme publish` (publicar un borrador reemplaza la instalación productiva entera: ver la referencia).

Chequeo determinista de todo lo verificable (git, frescura del último pull, fork, `theme watch` corriendo, capa de cada archivo a tocar):

```bash
python3 <carpeta-de-esta-skill>/scripts/sync-check.py . --files templates/pages/home.json
```

Exit **0** = podés escribir · **1** = falta sincronizar (imprime los comandos en orden) · **2** = el directorio no es una instalación del Fork workflow. El script no corre el pull ni lee el diff por vos: eso es criterio.

Protocolo completo, cómo leer el diff, reconciliación de conflictos, gate antes de publicar y casos borde: [references/sync-and-conflicts.md](references/sync-and-conflicts.md).

## 4. Arquitectura en una pantalla

```
theme/
├── blocks/                       # Bloques reutilizables con schema (se usan dentro de sections)
├── config/
│   ├── settings_schema.json      # Schema de settings globales del diseño
│   └── settings_data.json        # Valores guardados de los settings globales
├── layouts/
│   ├── layout.tpl                # Wrapper HTML principal (head, header, content, footer)
│   └── resources/
│       ├── icons-sprite.tpl      # Sprite SVG inline
│       └── style-tokens.tpl      # Custom properties CSS (fuentes, colores)
├── sections/                     # Sections de página con schema (header, footer, hero, banners, ...)
├── snippets/                     # Partials sin schema (cart/, payments/, product/, forms/, ...)
├── static/
│   ├── css/
│   │   ├── style-critical.css    # CSS crítico inlinado en <head>
│   │   ├── style-utilities.css   # Clases utilitarias inlinadas en <head>
│   │   └── style-async.css       # CSS no crítico, carga asincrónica
│   ├── js/
│   │   ├── store.js              # Lógica client-side del diseño (vanilla JS)
│   │   ├── libraries-standalone.js
│   │   └── libraries.js.tpl
│   └── checkout.scss.tpl         # Estilos de branding para el checkout
├── templates/
│   ├── pages/                    # Templates de página (home.json, product.json, ...)
│   │   └── account/              # Páginas de cuenta (login, register, orders, ...)
│   └── layout/                   # Templates de layout (header.json, footer.json)
└── translations/
    ├── <locale>.json             # Strings del storefront (orientados al comprador)
    └── <locale>.schema.json      # Labels del editor (orientados al usuario)
```

**Pipeline de render:** `layouts/layout.tpl` (shell HTML) → `{% layout_template 'header' %}` renderiza `templates/layout/header.json` → `{{ page_template_content }}` renderiza el page template JSON activo (`templates/pages/*.json`) → cada entrada de `sections` incluye su `.tpl` de `sections/` → cada section itera sus blocks (`blocks/*.tpl`) → sections y blocks incluyen snippets (`snippets/**.tpl`).

```twig
<main id="MainContent" class="main-content main-container" role="main">
  {{ page_template_content }}
</main>
```

```twig
{% layout_template 'header' %}
{# ... contenido de página ... #}
{% layout_template 'footer' %}
```

Los settings globales de `config/` son accesibles desde cualquier `.tpl` vía `settings.*`:

```twig
{{ settings.background_color }}
{{ settings.font_headings }}
```

Ojo: `templates/layout/` (JSON de header/footer) y `layouts/layout.tpl` (shell HTML) son carpetas distintas con nombre parecido — no las confundas.

## 5. Workflow de desarrollo (CLI)

Requisitos: Node ≥ 24.15 y `npm i -g @tiendanube/cli`. Primero autorizá el CLI con la tienda: `tiendanube theme authorize` — guarda un token Base64 en `.nuvem` (**gitignorealo, nunca lo commitees**). Máximo **2 instalaciones de tema por tienda**.

Ciclo típico:

1. **Crear o clonar** una instalación: `tiendanube theme create --base-theme ipanema --title "Mi Tema"` o `tiendanube theme clone`
2. **Descargar** (vincula el directorio a esa instalación): `tiendanube theme pull --theme-id ID`
3. **Hacer fork** si necesitás editar el código del tema: `tiendanube theme fork`
4. **Iniciar el modo watch**: `tiendanube theme watch`
5. **Editar** templates, secciones y configuraciones — los cambios se sincronizan automáticamente
6. **Previsualizar** con el navegador que se recarga automáticamente, o generar un link: `tiendanube theme preview`
7. **Publicar** cuando esté listo: `tiendanube theme publish`

Tras el pull, el CLI genera `manifest.json` (solo local, nunca se envía):

```json
{
  "theme": "ipanema",
  "theme_version": "1.0.0",
  "forked": false,
  "revision_token": "<REVISION_TOKEN>",
  "installation_id": "4541834"
}
```

> **⚠️ Callout fork / no-fork — verificar ANTES de editar código.**
> Leé `forked` en `manifest.json`. Si la instalación **no tiene fork**, solo son editables `custom/**`, `templates/**` y `config/settings_data.json`; `theme push`/`theme watch` **omiten silenciosamente** todo lo demás (sections, blocks, snippets, layouts, static, schema) — sin error, simplemente no se sube. Si vas a tocar código core, hacé `tiendanube theme fork` primero. Nota: `theme fork` figura como "Próximamente" en la doc — hoy puede devolver solo un aviso; verificá el estado real antes de prometer ediciones core.

Detalles de `push`/`watch`: push incremental (solo envía archivos cambiados; `--force` envía todo), sincroniza eliminaciones (lo que no existe local se borra del remoto), excluye rutas que empiezan con `.` y `manifest.json`, y los archivos vacíos (0 bytes) hacen fallar el push. `watch` abre un navegador Puppeteer con `?theme_installation_id=<id>` que recarga tras cada push (`--no-browser` para omitirlo). **No existe `tiendanube theme dev`** — el dev loop es `theme watch`. Comandos disponibles: `theme list/create/current/clone/fork/unfork/publish/preview/performance/delete/pull/push/watch/authorize`. Detalle completo de opciones y CI en [references/cli-workflow.md](references/cli-workflow.md).

## 6. Patrones canónicos

### 6.1 Section con schema y loop de blocks

Toda section es un `.tpl` en `sections/` con dos mitades: markup Twig arriba, `{% schema %}` al final. Los blocks se incluyen derivando el archivo de `block.type` — agregar un tipo al schema alcanza para que renderice, sin cadenas `if/elseif`. `section.blocks` ya viene ordenado según `block_order`. Ejemplo real (`sections/video.tpl`):

```twig
{% set settings = section.settings %}
{% set video_url = settings.video_url %}
{% set show_overlay = settings.show_overlay %}

<div class="video-section" data-section-id="{{ section.id }}">
  {% if video_url.id %}
    {# ...renderiza el player de video... #}
  {% endif %}

  {% if section.blocks %}
    <div class="media-content">
      {% for block in section.blocks %}
        {% include 'blocks/' ~ block.type ~ '.tpl' with { block: block } %}
      {% endfor %}
    </div>
  {% endif %}
</div>

{% schema %}
{
  "name": "t:names.video",
  "icon": "VideoIcon",
  "add_section_order": 4,
  "class": "section section-video",
  "blocks": [
    { "tags": ["general"] }
  ],
  "settings": [
    {
      "type": "setting",
      "setting_type": "video_url",
      "id": "video_url",
      "label": "t:settings.video_url",
      "icon": "VideoIcon"
    },
    {
      "type": "setting",
      "setting_type": "url",
      "id": "link",
      "label": "t:settings.link",
      "visible_if": "{{ section.settings.video_type == 'autoplay' }}"
    },
    { "type": "header", "content": "t:names.video_properties" },
    {
      "type": "setting",
      "setting_type": "select",
      "id": "video_type",
      "label": "t:settings.video_type",
      "options": [
        { "value": "autoplay", "label": "t:options.autoplay" },
        { "value": "manual", "label": "t:options.manual" }
      ],
      "default": "autoplay"
    },
    { "type": "header", "content": "t:names.colors" },
    {
      "type": "setting",
      "setting_type": "toggle",
      "id": "show_overlay",
      "label": "t:names.transparent_background",
      "default": false,
      "info": "t:settings.add_overlay",
      "header_toggle": true
    },
    {
      "type": "setting",
      "setting_type": "color",
      "id": "overlay_color",
      "label": "t:settings.color",
      "default": "#000000",
      "visible_if": "{{ section.settings.show_overlay }}"
    }
  ],
  "presets": [
    {
      "name": "t:names.video",
      "category": "t:categories.media",
      "settings": { "vertical_padding": 32 },
      "blocks": [
        { "type": "heading", "settings": { "title": "t:defaults.video.heading" } },
        { "type": "button",  "settings": { "label": "t:defaults.video.button" } }
      ]
    }
  ]
}
{% endschema %}
```

### 6.2 Block con `block_attributes` en la raíz

Los blocks leen `block.settings.*` (no `section.settings.*`) y **el elemento raíz DEBE llevar `{{ block | block_attributes }}`** — imprime los data-attributes que el editor usa para seleccionar y resaltar el bloque en el preview; sin él, el comerciante no puede editarlo.

```twig
{% set settings = block.settings %}

{% if settings.text %}
  <div
    class="heading-block {{ settings.size }}"
    {{ block | block_attributes }}
    data-store="heading-block-{{ block.id }}"
  >
    {{ settings.text | raw }}
  </div>
{% endif %}
```

Una section (o block padre) declara qué tipos de bloque acepta de tres formas:

```json
"blocks": [
  { "type": "banner" },              // exactamente este tipo
  { "tags": ["general"] },           // cualquier bloque con la tag "general"
  { "type": "@theme" }               // cualquier tipo de bloque definido en cualquier parte del diseño
]
```

Un block entra al grupo `"general"` declarando `"tags": ["general"]` en su propio schema. Los blocks anidados iteran `block.blocks` con el mismo patrón de include; los tipos hijos pueden definirse inline en el schema del padre (con `deletable: false` para hijos obligatorios) o como `.tpl` propio si se reutilizan — ver [references/sections-blocks-snippets.md](references/sections-blocks-snippets.md).

### 6.3 Snippet con parámetros documentados en comentario cabecera

Un snippet es un partial **sin schema** (no editable desde el editor). No hereda el scope del caller: solo recibe lo que se le pasa con `with { ... }` más los globales de plataforma (`product`, `cart`, `settings`, `store`). Documentá el contrato de parámetros en un comentario al inicio — convención de `snippets/image.tpl`:

```twig
{#
  Image
  Componente unificado de imagen responsiva. Punto de entrada único: image_src.
  Soporta imágenes de producto, categoría, post, valores de image_picker del
  editor de diseño, y URLs externas. Renderiza como <picture> con AVIF/WebP
  cuando hay srcsets disponibles.

  Uso:
    image_src      - La imagen a mostrar (objeto de imagen, referencia de media, o URL).
    product_image  - true si image_src es un objeto de imagen de producto.
    category_image - true si image_src es un objeto de imagen de categoría.
    image_thumbs   - Array de tamaños de thumb para srcset, o false para deshabilitar srcset.
#}
```

El caller pasa solo lo que necesita:

```twig
{% include 'snippets/image.tpl' with {
  image_src: product.featured_image,
  product_image: true,
  image_alt: product.name,
  image_thumbs: ['small', 'medium', 'large']
} %}
```

### 6.4 Page template JSON (`sections` / `order` / `block_order`)

Toda página se define en `templates/pages/*.json`: diccionario `sections` (ids arbitrarios), array `order` para el orden de render, y `block_order` dentro de cada padre. `type` = nombre del archivo en `sections/` o `blocks/` sin `.tpl`. Los valores `t:` en `settings` se resuelven desde `*.schema.json`. Fragmento de `templates/pages/home.json`:

```json
{
  "sections": {
    "slideshow": {
      "type": "slideshow",
      "settings": {
        "section_width": "full",
        "height": 400,
        "autoplay": true
      },
      "blocks": {
        "slide_1": {
          "type": "slide",
          "blocks": {
            "heading": {
              "type": "heading",
              "settings": { "text": "t:defaults.slide.heading", "size": "h1" }
            },
            "text": {
              "type": "text",
              "settings": { "text": "t:defaults.slide.description" }
            },
            "button": {
              "type": "button",
              "settings": { "label": "t:defaults.slide.button" }
            }
          },
          "block_order": ["heading", "text", "button"]
        }
      },
      "block_order": ["slide_1"]
    }
  },
  "order": ["slideshow"]
}
```

### 6.5 Layout template (`header.json` + `wrapper: header` en el schema)

`templates/layout/header.json` y `footer.json` renderizan en TODAS las páginas vía `{% layout_template 'header'|'footer' %}` desde `layouts/layout.tpl`. Mismo formato JSON que un page template, con dos claves extra en la raíz:

```json
{
  "type": "header",
  "name": "Header",
  "sections": { "...": "..." },
  "order": ["..."]
}
```

Las sections usadas acá son `.tpl` comunes de `sections/` con dos particularidades de schema: `"wrapper": "header"` (o `"footer"`) para que el elemento wrapper no sea `<section>`, y `enabled_on.layout_templates` (ej. `["header"]`) para restringir dónde pueden usarse. Una section puede venir `"disabled": true` por default (existe en el JSON con settings guardados pero no renderiza hasta que el comerciante la active). Hoy existen exactamente estos dos layout templates — no se puede declarar un tercero.

## 7. Schema quick reference

Claves de nivel section: `name` (t:), `icon`, `wrapper`, `class`, `static` (no removible), `limit`, `add_section_order`, `max_blocks`, `enabled_on` (`page_templates`: `"all"` o array; `layout_templates`: array), `blocks`, `settings`, `presets`, `default` (alternativa a presets para sets fijos de blocks, ej. footer).

Claves de nivel block: `name`, `tags`, `icon`, `limit`, `deletable`, `blocks` (hijos, mismas 3 formas), `settings`, `presets`.

Cada setting: `{"type": "setting", "setting_type": "<tipo>", "id", "label": "t:...", "default"}` — sintaxis propia TN, ≠ Shopify. Claves opcionales: `info`, `icon`, `visible_if` (expresión Twig como string), `header_toggle`, `options` (para select), `default_setting`. Divisores: `{ "type": "header", "content": "t:..." }`. Lista completa de `setting_type` y claves en [references/schema-settings-i18n.md](references/schema-settings-i18n.md).

## 8. Reglas duras

1. **`{{ block | block_attributes }}` en el elemento raíz de TODO block** — sin él, el bloque no es seleccionable en el editor.
2. **No renombres ni muevas los snippets con prefijo `_`** (`_cart-item.tpl`, `_shipping-options.tpl`, `_product-grid.tpl`): el backend los busca con ese nombre y ubicación exactos.
3. **No borres los slots `nubesdk`** (`component('nubesdk-slot')`) **ni los atributos `data-store`** — los usan las apps y el JS de plataforma.
4. **Todo label del editor usa claves `t:`** resueltas en TODOS los `translations/*.schema.json` — nunca strings hardcodeados en un schema.
5. **Los precios se manejan en centavos** — dividí/formateá al mostrar, nunca asumas unidades.
6. **La extensión es `.tpl`, nunca `.twig`** — aunque el contenido sea Twig 2.x.
7. **Sin fork (`"forked": false` en `manifest.json`), NO edites fuera de `templates/**`, `custom/**` y `config/settings_data.json`** — el push omite el resto en silencio y vas a creer que deployaste algo que no subió.
8. **Nunca escribas con una copia sin sincronizar** — antes de la primera escritura de cada tarea corré el gate del Paso 0.5 (commit/stash → `git pull` → `tiendanube theme pull` → leer el diff). El comerciante edita `templates/**` y `config/settings_data.json` desde el editor y `theme push` sincroniza eliminaciones: una copia vieja no solo pisa sus cambios, **los borra**, sin confirmación y sin deshacer.

## 9. Navegación de referencias (progressive disclosure)

| Leé | Cuando |
|---|---|
| [references/sync-and-conflicts.md](references/sync-and-conflicts.md) | vas a **escribir** archivos del tema, el comerciante tiene acceso al editor, el pull trajo cambios que no escribiste vos, vas a publicar un borrador, o hay que reconciliar un conflicto |
| [references/cli-workflow.md](references/cli-workflow.md) | vas a correr/automatizar el CLI, hacer deploy, forks, CI, o un push no sube archivos |
| [references/theme-architecture.md](references/theme-architecture.md) | vas a tocar JSON templates, páginas, layouts, o necesitás ubicar un archivo |
| [references/sections-blocks-snippets.md](references/sections-blocks-snippets.md) | vas a crear/modificar sections, blocks o snippets (la tarea más frecuente) |
| [references/schema-settings-i18n.md](references/schema-settings-i18n.md) | necesitás un `setting_type` puntual, settings globales, traducciones o integración de apps |
| [references/twig-objects-filters.md](references/twig-objects-filters.md) | tenés dudas de objetos (`section`, `block`, `product`, ...), filtros o sintaxis Twig |

## 10. Discrepancias y edge cases

- **`translations/` vs `locales/`:** la doc de arquitectura usa `translations/`; la doc del CLI muestra `locales/` en el árbol del pull. **Mirá qué carpeta existe en el proyecto real y usá esa** — no renombres ninguna.
- **`snippets/` vs `snipplets/`:** sin "l" = tema nuevo; con "l" (`snipplets`) = tema clásico. Si ves `snipplets/`, estás en el modelo clásico → volvé al Paso 0 y derivá.
- **No inventes comandos por analogía con Shopify CLI:** no existe `tiendanube theme dev`, ni `theme check`, ni `theme serve`. El dev loop es `theme watch`. Usá solo los comandos listados en la sección 5.
- **`theme fork` figura "Próximamente":** hoy puede devolver solo un aviso. Si el fork no está disponible, limitate a las rutas editables sin fork y avisá la restricción.
- **Templates personalizados por página/producto/categoría:** funcionalidad en evolución — la asignación vive en el Admin, no en el código del diseño. No intentes implementarla con archivos de template ad hoc.
- **Fallback de locale:** el resolver busca `pt_BR.json` → `pt.json` → `<lang>.default.json` (ej. `pt.default.json`); mismo fallback para `.schema.json`. Distribuí un default regional y agregá archivos por país solo cuando el copy difiera.
