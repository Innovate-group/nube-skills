# Schema, Global Settings y Traducciones

Referencia del sistema de settings de los temas sectionable de Tienda Nube: los tipos de setting disponibles en el `{% schema %}` de sections y blocks, las claves condicionales y de herencia, los settings globales del diseño (`config/settings_schema.json` / `settings_data.json`), los dos sistemas de traducción de `translations/`, y los puntos de extensión para apps.

> **IMPORTANTE**: la sintaxis de schema es la propia de Tienda Nube — cada input es un objeto `{ "type": "setting", "setting_type": "<tipo>", ... }`. NO usar la sintaxis de Shopify (`{ "type": "text", ... }`) ni mezclar claves de ambas plataformas.

## Tabla de contenidos

1. [Estructura base de todo setting](#1-estructura-base-de-todo-setting)
2. [Referencia de setting_type](#2-referencia-de-setting_type)
3. [Claves a nivel setting](#3-claves-a-nivel-setting)
4. [No-inputs de layout del panel](#4-no-inputs-de-layout-del-panel)
5. [Global settings](#5-global-settings)
6. [Traducciones](#6-traducciones)
7. [Integración con apps](#7-integración-con-apps)

## 1. Estructura base de todo setting

Cada section y block declara su schema al final del archivo `.tpl`, entre `{% schema %}` y `{% endschema %}`. El array `settings` del schema determina la forma del panel de settings en el editor. Todos los settings siguen esta estructura base:

```json
{
  "type": "setting",
  "setting_type": "<type>",
  "id": "<unique_id>",
  "label": "t:settings.<key>",
  "default": "<value>"
}
```

Reglas del panel: los settings se renderizan en el orden en que se declaran; las entradas `header` dividen el panel en grupos con título (ej. **Diseño**, **Colores**, **Layout**, **Mobile**); `visible_if` / `disabled_if` en settings individuales permiten mostrar o deshabilitar un setting según el valor de otro; el `label` (y todo string visible del schema) usa una clave `t:` — ver [Traducciones](#6-traducciones).

## 2. Referencia de setting_type

### `text`
Texto de una sola línea.
```json
{ "type": "setting", "setting_type": "text", "id": "heading", "label": "t:settings.<key>", "default": "t:defaults.heading" }
```

### `number`
Input numérico libre (sin slider). Preferir `range` cuando haya min/max conocidos.
```json
{ "type": "setting", "setting_type": "number", "id": "quantity", "label": "t:settings.<key>" }
```

### `richtext`
Texto enriquecido con formato inline.
```json
{ "type": "setting", "setting_type": "richtext", "id": "text", "label": "t:settings.<key>" }
```

### `html`
Editor de HTML crudo.
```json
{ "type": "setting", "setting_type": "html", "id": "custom_html", "label": "t:settings.<key>" }
```

### `custom_css`
Editor de CSS crudo — usado en el setting global "CSS personalizado" del diseño (el panel global **Advanced CSS** expone un único setting de este tipo: CSS que el comerciante puede agregar sin editar archivos del diseño).
```json
{ "type": "setting", "setting_type": "custom_css", "id": "custom_css", "label": "t:settings.<key>" }
```

### `url`
Selector de enlace.
```json
{ "type": "setting", "setting_type": "url", "id": "link", "label": "t:settings.<key>" }
```

### `video_url`
Selector de URL de video (YouTube/Vimeo). El valor NO es un string: resuelve en un objeto con `.id`, `.type` (proveedor) y `.thumbnail`. Puede llevar `icon`.
```json
{ "type": "setting", "setting_type": "video_url", "id": "video", "label": "t:settings.<key>" }
```

### `select`
Dropdown — ideal para muchas opciones. Cada opción es `{ "value": ..., "label": "t:options.<key>" }`:
```json
{
  "type": "setting",
  "setting_type": "select",
  "id": "size",
  "label": "t:settings.size",
  "options": [
    { "value": "h1", "label": "t:options.heading_1" },
    { "value": "h2", "label": "t:options.heading_2" }
  ],
  "default": "h4"
}
```

### `radio`
Selección visual única — ideal para 2 a 4 opciones. Las opciones pueden llevar un `icon` para un selector visual (ej.: dirección: fila/columna).
```json
{
  "type": "setting",
  "setting_type": "radio",
  "id": "width",
  "label": "t:settings.section_width",
  "options": [
    { "value": "fit",  "label": "t:options.fit" },
    { "value": "fill", "label": "t:options.fill" }
  ],
  "default": "fill"
}
```

### `toggle`
Switch on/off. Agregar `"header_toggle": true` para que colapse/expanda el resto de su grupo `header` en vez de solo alternar un valor: un `toggle` con `"header_toggle": true` renderiza junto a su `header` anterior, y su valor controla la visibilidad de los settings que siguen — combinado con `visible_if`, apagar el toggle oculta esos settings del panel. Usado para bloques de funcionalidad opcional como "Overlay" en la sección de Video, donde apagar el overlay oculta los settings de color/opacidad del overlay:
```json
{ "type": "setting", "setting_type": "toggle", "id": "show_overlay", "label": "t:names.transparent_background", "default": false, "header_toggle": true },
{ "type": "setting", "setting_type": "color", "id": "overlay_color", "visible_if": "{{ section.settings.show_overlay }}" }
```

### `checkbox`
On/off heredado (legacy) — preferir `toggle` en settings nuevos.
```json
{ "type": "setting", "setting_type": "checkbox", "id": "show_border", "label": "t:settings.<key>", "default": false }
```

### `range`
Slider numérico con `min`, `max`, `step` y `unit`. Puede llevar su propio `icon`.
```json
{
  "type": "setting",
  "setting_type": "range",
  "id": "mobile_font_size",
  "label": "t:settings.mobile_font_size",
  "min": 12,
  "max": 48,
  "step": 1,
  "unit": "px",
  "default": 16
}
```

### `color`
Selector de color. Usar `default_setting` para heredar un color global en vez de fijar un default propio:
```json
{
  "type": "setting",
  "setting_type": "color",
  "id": "custom_background_color",
  "label": "t:settings.background",
  "default_setting": "button_background_color"
}
```

### `image_picker`
Carga de imagen. Los valores guardados usan referencias `@media-lib:` a la biblioteca de medios de la tienda; en el `.tpl` se resuelven con el filtro `resolve_media` a un objeto de media con la propiedad `sourceUrl` (`{% set media = image_src | resolve_media %}` → `{{ media.sourceUrl }}`).
```json
{ "type": "setting", "setting_type": "image_picker", "id": "image", "label": "t:settings.<key>" }
```

### `font_picker`
Selector de familia tipográfica, desde la lista de opciones de Google Fonts del diseño.
```json
{ "type": "setting", "setting_type": "font_picker", "id": "heading_font", "label": "t:settings.<key>" }
```

### `text_alignment`
Alineación izquierda / centro / derecha.
```json
{ "type": "setting", "setting_type": "text_alignment", "id": "text_alignment", "label": "t:settings.<key>", "default": "center" }
```

### `alignment`
Grilla de alineación 2D. A diferencia de todo otro tipo de setting, `alignment` empaqueta dos listas de opciones independientes en una sola entrada — horizontal (`options`/`default`) y vertical (`vertical_options`/`vertical_default`):
```json
{
  "type": "setting",
  "setting_type": "alignment",
  "id": "alignment",
  "label": "t:settings.alignment",
  "options": [
    { "value": "start", "label": "t:options.left" },
    { "value": "center", "label": "t:options.center" },
    { "value": "end", "label": "t:options.right" }
  ],
  "default": "center",
  "vertical_options": [
    { "value": "top", "label": "t:options.top" },
    { "value": "center", "label": "t:options.center" },
    { "value": "bottom", "label": "t:options.bottom" }
  ],
  "vertical_default": "center"
}
```

En el archivo `.tpl`, leer los dos ejes por separado — `section.settings.alignment` para el horizontal, `section.settings.alignment_vertical` para el vertical (el sufijo `_vertical` se agrega automáticamente; NO declarar un segundo setting para eso).

### `button_preview` / `label_preview`
Preview no editable del estilo de botón/label configurado en otro lugar del mismo panel — usado en los settings globales para mostrar el resultado de los paneles Buttons/Labels antes de sus settings de color individuales. El panel global **Buttons** usa `button_preview` para mostrar un ejemplo en vivo del estilo de botón que producen los propios settings de color del panel.
```json
{ "type": "setting", "setting_type": "button_preview", "id": "button_preview" }
```

### `custom_code`
Editor de código en el panel — lo usa el block `code` para que el comerciante inyecte HTML, CSS y JavaScript libre desde el editor. El contenido se renderiza con `| raw` (sin escapar; el comerciante es responsable de lo que inyecta) y el límite es de 50.000 caracteres por bloque.
```json
{ "type": "setting", "setting_type": "custom_code", "id": "custom_code", "label": "t:settings.<key>" }
```

## 3. Claves a nivel setting

| Clave | Qué hace |
|---|---|
| `default_setting` | Hereda el valor por defecto desde un setting global en `config/settings_schema.json`. Ejemplo: `"default_setting": "button_background_color"`. |
| `visible_if` | Muestra el setting condicionalmente según el valor de otro setting. Ejemplo: `"visible_if": "{{ block.settings.mobile_font_size }}"`. |
| `disabled_if` | Deshabilita el setting condicionalmente sin ocultarlo. |
| `info` | Texto de ayuda mostrado debajo del label del setting — para un matiz que no entra en el label. Ejemplo: `"info": "t:info.video_cover_image"`. |
| `icon` | Ícono mostrado junto al label del setting (en `range`, opciones de `radio`, `video_url`, …) — distinto del `icon` de nivel de section/block, que rotula el panel entero. |
| `tags` | En un block: lo marca como disponible para cualquier section que acepte ese tag. |

`visible_if` y `disabled_if` reciben una expresión Twig en string que referencia otro setting del mismo alcance — ej. `"{{ section.settings.mobile_font_size }}"` en una section, `"{{ block.settings.mobile_font_size }}"` en un block, o `"{{ section.settings.show_overlay }}"` para evaluar el valor de un toggle. Ejemplo de array de settings con divisores y visibilidad condicional:

```json
"settings": [
  { "type": "header", "content": "t:names.design" },
  {
    "type": "setting",
    "setting_type": "radio",
    "id": "width",
    "label": "t:settings.section_width",
    "options": [
      { "value": "fit",  "label": "t:options.fit" },
      { "value": "fill", "label": "t:options.fill" }
    ],
    "default": "fill"
  },
  { "type": "header", "content": "t:names.text_settings" },
  {
    "type": "setting",
    "setting_type": "select",
    "id": "size",
    "label": "t:settings.size",
    "options": [
      { "value": "h1", "label": "t:options.heading_1" },
      { "value": "h2", "label": "t:options.heading_2" }
    ],
    "default": "h4"
  },
  {
    "type": "setting",
    "setting_type": "range",
    "id": "mobile_font_size",
    "label": "t:settings.mobile_font_size",
    "min": 12,
    "max": 48,
    "step": 1,
    "unit": "px",
    "default": 16
  },
  {
    "type": "setting",
    "setting_type": "select",
    "id": "mobile_size_override",
    "label": "t:settings.mobile_size_override",
    "visible_if": "{{ section.settings.mobile_font_size }}",
    "options": [ ... ],
    "default": "h4"
  }
]
```

## 4. No-inputs de layout del panel

Las entradas `header` y `paragraph` no son inputs — son recursos de layout en el panel de settings:

```json
{ "type": "header", "content": "t:names.design" },
{ "type": "paragraph", "content": "t:content.page_width_description" }
```

`header` renderiza un divisor con título que agrupa los settings que siguen; `paragraph` renderiza un bloque de texto explicativo simple (usado, por ejemplo, arriba de los settings globales de Page Width y Primary Button, para explicar qué afectan antes de que el comerciante los toque).

## 5. Global settings

Los settings de section y block tienen alcance en una instancia — una única sección de video, un único bloque de heading. Los **global settings** son del diseño entero: logo, colores, tipografía, estilo de botones, comportamiento del carrito — todo lo que debería mantenerse consistente en toda página. Viven en exactamente dos archivos:

```
config/
├── settings_schema.json   # Schema — qué paneles existen y qué contiene cada uno
└── settings_data.json     # Valores guardados — las respuestas actuales de esta tienda
```

`settings_schema.json` viene con el código del diseño y define el formato del área "Configuración del diseño" en el editor. `settings_data.json` guarda los valores que el comerciante configuró para ese formato — es dato de runtime de una tienda específica, no forma parte del código versionado del diseño (una instalación nueva del diseño arranca con un `settings_data.json` vacío o por default, generado por la plataforma). Por eso el comerciante puede editar sus valores sin necesidad de un fork del tema.

> **ADVERTENCIA**: `settings_schema.json` comparte nombre con un archivo de Shopify, pero el formato es distinto — nunca asumir formato Shopify. Aquí es un array de paneles cuyos settings son objetos `{ "type": "setting", "setting_type": ... }`.

### Formato de un panel
`settings_schema.json` es un **array de paneles**. Cada panel usa el mismo formato de array `settings` que una section o block — incluyendo divisores `header` y `paragraph` — más algunas claves de nivel de panel:

```json
{
  "name": "t:names.colors",
  "icon": "ColorPaletteIcon",
  "group": "t:names.brand",
  "settings": [
    { "type": "header", "content": "t:content.main_colors" },
    { "type": "setting", "setting_type": "color", "id": "background_color", "label": "t:settings.background", "default": "#FFFFFF" },
    { "type": "setting", "setting_type": "color", "id": "text_color", "label": "t:settings.text", "default": "#3F3D38" },
    { "type": "setting", "setting_type": "color", "id": "accent_color", "label": "t:settings.accent_color", "info": "t:info.accent_color" }
  ]
}
```

| Clave | Qué hace |
|---|---|
| `name` | Nombre del panel mostrado en el sidebar del editor (una clave `t:`). |
| `icon` | Ícono junto al nombre del panel. |
| `group` | Anida este panel bajo una categoría colapsable. Todo panel que comparte un valor de `group` aparece junto; los paneles sin ese valor quedan en el nivel superior. |
| `settings` | Mismas definiciones de setting y divisores que una section o block. |

### Una lista real de paneles
Ipanema declara hoy 11 paneles en 2 grupos — útil como referencia del *tipo* de cosa que pertenece al alcance global, aunque la lista exacta es contenido del diseño, no un requisito de la plataforma:

| Grupo | Paneles |
|---|---|
| Brand | Colors, Typography, Buttons, Labels, Page Width |
| Advanced Settings | Browser Tab, Promotional Popup, Product Card, Product Form, Cart, Advanced CSS |

Algunos paneles usan tipos de setting que solo tienen sentido en ese alcance: **Buttons** usa `button_preview`; **Advanced CSS** expone un único setting `custom_css`.

### Leyendo settings globales
Cualquier archivo `.tpl` — un layout, una section, un block, o un snippet — los lee de la misma forma, vía `settings.<id>`:

```twig
{% if settings.logo_height_desktop %}
  <img style="max-height: {{ settings.logo_height_desktop }}px" ... />
{% endif %}
```

Este es el único namespace de settings al que los snippets *sí* tienen acceso, aunque no tengan schema propio.

### Heredando un default global
Un setting de section o block puede apuntar a uno global en vez de fijar su propio default, para arrancar ya igual al color elegido por la marca sin forzar al comerciante a configurarlo dos veces:

```json
{
  "type": "setting",
  "setting_type": "color",
  "id": "text_color",
  "label": "t:settings.text",
  "default_setting": "text_color"
}
```

## 6. Traducciones

Todo texto que muestra un diseño seccionable viene de `translations/` — nunca hardcodeado directo en un archivo `.tpl`. Hay **dos sistemas de traducción independientes** en esa misma carpeta, para dos públicos distintos:

```
translations/
├── en.json            # Strings de storefront — mostrados al comprador
├── en.schema.json      # Labels de editor — mostrados al comerciante, en el editor
├── es.json
├── es.schema.json
├── es_AR.json / es_AR.schema.json
├── es_CL.json / es_CL.schema.json
├── es_CO.json / es_CO.schema.json
├── es_MX.json / es_MX.schema.json
├── pt.default.json
└── pt.default.schema.json
```

| Archivo | Resuelve para | Se resuelve cuando | Se usa vía |
|---|---|---|---|
| `<locale>.json` | El comprador, en el storefront | Render de la página, usando el locale activo de la tienda | `{{ 'cart.add_to_cart' \| t }}` |
| `<locale>.schema.json` | El comerciante, en el editor | Render del editor, usando el locale del admin del comerciante | Claves `t:` dentro de `{% schema %}` |

Estos pueden ser — y generalmente son — locales distintos al mismo tiempo: un comerciante brasileño editando en portugués puede estar personalizando una tienda cuyo storefront atiende en español a compradores argentinos. Nada conecta a los dos más allá de existir en la misma carpeta `translations/`.

### Strings de storefront — filtro `| t`
Claves anidadas, ruta con puntos:

```json
// translations/es.json
{
  "cart": {
    "add_to_cart": "Agregar al carrito",
    "empty": "Tu carrito está vacío"
  }
}
```

```twig
{{ 'cart.add_to_cart' | t }}
```

El filtro busca la ruta de clave con puntos al momento de renderizar el storefront, contra el archivo de locale que corresponde al locale activo del comprador.

### Labels de editor — claves `t:`
Las traducciones de schema son objetos planos, organizados por espacio de nombres en vez de anidados por funcionalidad:

```json
// translations/es.schema.json
{
  "names":      { "logo": "Logo", "heading": "Encabezado", "button": "Botón" },
  "settings":   { "background": "Fondo", "format": "Formato" },
  "options":    { "grid": "Grilla", "slider": "Slider" },
  "defaults":   { "heading": "Tu título aquí", "button": "Hacé clic" },
  "info":       { "accent_color": "Se usa en botones secundarios y enlaces destacados." },
  "content":    { "main_colors": "Colores principales" },
  "categories": { "basic": "Básico", "media": "Multimedia" }
}
```

```json
// dentro de un bloque {% schema %}
{ "label": "t:settings.format", "default": "t:defaults.heading" }
```

Las claves `t:` pueden aparecer en cualquier lugar del schema que acepte un string — `name`, `label`, `default`, `info`, `content` de `header`/`paragraph`, `label` de opciones — y se resuelven cuando se renderiza la propia UI del editor, no en el render del storefront. Por eso un JSON template puede pre-llenar el texto de un preset con `"text": "t:defaults.slide.heading"` y que ya aparezca traducido en el momento en que el comerciante agrega ese preset, en cualquier locale en el que esté editando.

> **ADVERTENCIA**: agregar un setting nuevo con `"label": "t:settings.mi_clave_nueva"` solo funciona una vez que `mi_clave_nueva` exista en el namespace `settings` de **todos** los archivos `*.schema.json` que soporta el diseño — una clave faltante cae en el fallback de mostrar el string `t:` crudo en el editor.

### Fallback de locale
Ninguno de los dos tipos de archivo exige una traducción para toda variante de locale posible. Cuando la plataforma pide un locale (digamos, `pt_BR`), resuelve el archivo disponible más cercano, en este orden:

1. `translations/pt_BR.json` — coincidencia exacta.
2. `translations/pt.json` — coincidencia solo de idioma.
3. `translations/<idioma>.default.json` — el default regional de ese idioma.

El mismo fallback se aplica a los archivos `.schema.json`. En la práctica, esto significa que un diseño entrega un default regional por idioma (`pt.default.json`) y solo agrega un archivo específico de país (`es_AR.json`, `es_MX.json`, …) cuando el texto realmente necesita ser distinto — no un archivo por país desde el principio.

## 7. Integración con apps

El diseño expone dos mecanismos para que las apps puedan inyectar contenido o adjuntar comportamiento sin necesidad de modificar el código del diseño: **Nube SDK slots** y **puntos de anclaje `data-store`**.

> **REGLA DURA**: no eliminar ni renombrar ninguno de estos puntos — las apps de terceros dependen de ellos, y su remoción silencia integraciones instaladas.

### Nube SDK slots
El Nube SDK permite a las apps renderizar contenido en **slots** — puntos de anclaje nombrados dentro del storefront. Cuando ninguna app apunta a un slot, no se renderiza nada; cuando una o más apps lo apuntan, su contenido se inyecta en ese punto. Los slots se declaran en los archivos `.tpl` con el componente `nubesdk-slot`:

```twig
{{ component('nubesdk-slot', { type: "after_product_detail_price" }) }}
```

El diseño incluye slots en los puntos clave de la experiencia de compra: alrededor del nombre, precio y botón de agregar al carrito en la página de producto; en la grilla de productos; en el carrito; y en el layout general (antes/después del header, footer y contenido principal).

**Slots de sección (automáticos)**: además de los slots que el diseño declara explícitamente, la plataforma emite automáticamente un par de slots (`before_dynamic_section` / `after_dynamic_section`) alrededor de cada sección dinámica, pasando `section_type`, `section_id` y `section_index` para que las apps puedan acotarse a una sección específica. No se necesita agregar nada en el diseño para los slots de sección — el backend renderer los inyecta automáticamente.

### Puntos de anclaje data-store
Los atributos `data-store` son puntos de anclaje estables en el DOM pensados para las apps que todavía no usan el Nube SDK. Permiten encontrar y manipular elementos bien conocidos — el botón de agregar al carrito, el precio, ítems del carrito, formularios de cuenta, etc. — con selectores CSS.

```html
<h1 data-store="product-name-{{ product.id }}">{{ product.name }}</h1>
<input type="submit" data-store="product-buy-button" data-component="product.add-to-cart" ... />
```

Los blocks agregados desde el editor también exponen un `data-store` para que las apps puedan apuntar instancias individuales:

```html
<div class="heading-block ..." {{ block | block_attributes }} data-store="heading-block-{{ block.id }}">
```

La tabla completa de atributos `data-store` disponibles en el storefront está en la referencia de Store Utilities de la documentación de Tienda Nube ("Puntos de anclaje para aplicaciones") — aplica tanto a diseños clásicos como a diseños basados en secciones.
