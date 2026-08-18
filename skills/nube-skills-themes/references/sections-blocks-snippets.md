# Sections, Blocks y Snippets

Referencia para crear y modificar los tres tipos de archivo `.tpl` de un tema sectionable de Tienda Nube. Sections y blocks son editables por el comerciante y llevan `{% schema %}`; los snippets son partials internos sin schema.

## Tabla de contenidos

1. [Sections](#1-sections) — anatomía, nomenclatura (`main-`), patrón de settings y bloques, ejemplo completo `sections/video.tpl`, claves del schema, `visible_if` / `header` / `header_toggle`
2. [Blocks](#2-blocks) — anatomía y `block_attributes`, tipos de bloque aceptados, genéricos vs. específicos, bloques anidados, `group.tpl`, `code.tpl`, claves del schema
3. [Snippets](#3-snippets) — regla de decisión, subcarpetas por dominio, inclusión y parámetros, `snippets/image.tpl`, prefijo underscore (regla dura)

## 1. SECTIONS

### Anatomía

Una sección es un archivo `.tpl` autocontenido que renderiza como una unidad de ancho completo en una página. Estructurá todo archivo de sección en dos mitades: markup Twig arriba, y un bloque `{% schema %}` JSON al final que declara qué puede configurar el comerciante.

### Nomenclatura

Guardá las secciones en `sections/`. Usá el prefijo `main-` solo para el contenido principal de un tipo de página específico (`main-product.tpl`, `main-cart.tpl`, `main-blog.tpl`, …): esas secciones no se reutilizan en otro lado. Todo el resto — `hero.tpl`, `banners.tpl`, `video.tpl`, `testimonials.tpl`, `custom.tpl`, … — es una sección de uso general que cualquier page template puede referenciar.

### Leyendo settings y bloques

Usá el patrón canónico: asigná `section.settings` a una variable local y recorré `section.blocks` derivando el archivo a incluir desde `block.type`:

```twig
{% set settings = section.settings %}
{% set format   = settings.format %}
{% set has_blocks = section.blocks | length > 0 %}

{% for block in section.blocks %}
  {% include 'blocks/' ~ block.type ~ '.tpl' with { block: block } %}
{% endfor %}
```

Dos detalles que importan en la práctica:

- `section.blocks` ya viene en el orden elegido por el comerciante (desde `block_order` en el JSON template).
- El archivo `.tpl` a incluir se deriva de `block.type`, así que agregar un tipo de bloque nuevo al schema de una sección ya alcanza para que renderice. No mantengas una cadena separada de `if/elseif` por tipo.

### Ejemplo real y completo: sections/video.tpl

Una sección de video de fondo con bloques de contenido flotantes. Este es el archivo real, schema incluido, mostrando settings que se leen entre sí (`visible_if`), un divisor `header`, íconos por setting, y un toggle que colapsa su propio grupo:

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

### Claves del schema de sección

| Clave | Qué hace |
|---|---|
| `name` | Nombre de la sección en el editor (una clave `t:`). |
| `icon` | Ícono mostrado junto al nombre en el editor. |
| `wrapper` | Elemento HTML usado como wrapper de la sección. Por default es `section` — poné `header`/`footer` para secciones usadas dentro de un Layout Template. |
| `class` | Clase(s) CSS agregadas al wrapper. |
| `static` | Si es `true`, el comerciante no puede quitar la sección. |
| `limit` | Cantidad máxima de veces que esta sección puede aparecer en una página. |
| `add_section_order` | Posición sugerida (base 1) al agregar esta sección desde el selector — números más bajos aparecen primero. |
| `max_blocks` | Cantidad máxima de bloques que el comerciante puede agregar. Omitilo para no tener límite. |
| `enabled_on` | Restringe dónde se puede usar la sección: `page_templates` (`"all"` o un array como `["home", "product"]`) y/o `layout_templates` (`["header", "footer"]`). |
| `blocks` | Tipos de bloque que esta sección acepta — ver [tipos de bloque aceptados](#tipos-de-bloque-aceptados). |
| `settings` | Definiciones de setting y divisores `header`. |
| `presets` | Configuración por default (settings + bloques iniciales) aplicada cuando el comerciante agrega la sección. |
| `default` | Alternativa a `presets` para secciones que siempre renderizan un conjunto fijo de bloques (usado por `footer`). |

### Settings: visible_if, header y header_toggle

- `visible_if` toma una expresión Twig en un string (p. ej. `"{{ section.settings.video_type == 'autoplay' }}"` o `"{{ section.settings.show_overlay }}"`): el setting solo se muestra en el editor cuando la expresión es verdadera. Usalo para settings que dependen del valor de otro setting.
- `{ "type": "header", "content": "t:..." }` inserta un divisor con título que agrupa visualmente los settings que le siguen.
- `header_toggle: true` en un setting `toggle` lo convierte en el interruptor del grupo: colapsa/expande su propio grupo de settings en el panel.

## 2. BLOCKS

### Anatomía y block_attributes

Un bloque es un componente reutilizable que renderiza dentro de una sección (o dentro de otro bloque). Seguí la misma estructura de dos mitades que las secciones — markup Twig, después un `{% schema %}` — pero leé los settings desde `block.settings.*` en vez de `section.settings.*`:

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

**Regla obligatoria:** aplicá `{{ block | block_attributes }}` en el elemento raíz de todo bloque. Ese filtro imprime los atributos de datos que el editor usa para identificar y resaltar el bloque en el preview — sin él, el comerciante no puede seleccionar el bloque para editarlo.

### Tipos de bloque aceptados

Una sección (o un bloque padre) declara qué tipos de bloque acepta en la clave `blocks` de su schema, de tres formas:

```json
"blocks": [
  { "type": "banner" },              // exactamente este tipo
  { "tags": ["general"] },           // cualquier bloque con la tag "general"
  { "type": "@theme" }               // cualquier tipo de bloque definido en cualquier parte del diseño
]
```

Un bloque entra al grupo `"general"` marcándose con esa tag en su propio schema:

```json
{% schema %}
{
  "name": "t:names.heading",
  "tags": ["general"],
  "settings": [ ... ]
}
{% endschema %}
```

### Bloques genéricos vs. específicos

Los bloques genéricos (`heading.tpl`, `text.tpl`, `image.tpl`, `button.tpl`, `group.tpl`, `code.tpl`, …) llevan la tag `"general"`, así que cualquier sección que acepte esa tag los suma automáticamente. Los bloques específicos de sección (`slide.tpl`, `banner.tpl`, `header-logo.tpl`, …) no llevan tag — solo son usables donde una sección liste su `type` exacto.

### Bloques anidados

Los bloques pueden contener otros bloques, y el schema de un bloque puede definir sus tipos de bloque hijos **inline**, sin un archivo `.tpl` separado para cada uno. De `blocks/product-info.tpl` (resumido):

```json
{% schema %}
{
  "name": "t:names.purchase_info",
  "limit": 1,
  "blocks": [
    { "tags": ["general"] },
    {
      "type": "description",
      "name": "t:names.product_description",
      "limit": 1,
      "deletable": false,
      "settings": [
        { "type": "setting", "setting_type": "toggle", "id": "show_title", "label": "t:settings.show_title", "default": true }
      ]
    },
    {
      "type": "purchase-info",
      "name": "t:names.icon_text",
      "limit": 2,
      "blocks": [
        { "type": "icon-text-item", "limit": 6 }
      ],
      "settings": [ ... ]
    }
  ]
}
{% endschema %}
```

`product-info` acepta cualquier bloque con tag `"general"`, más dos tipos que define inline: `description` (bloqueado con `"deletable": false` — el comerciante puede configurarlo pero no quitarlo) y `purchase-info`, que a su vez anida hasta 6 bloques `icon-text-item`. Recorré los hijos con `block.blocks`, mismo patrón que en las secciones:

```twig
{% for child_block in block.blocks %}
  {% include 'blocks/' ~ child_block.type ~ '.tpl' with { block: child_block } %}
{% endfor %}
```

Decidí caso por caso si un tipo anidado se define inline o como su propio archivo: las definiciones inline tienen sentido para una variante que solo aparece anidada dentro de un único padre (como `description` arriba); un archivo `.tpl` independiente con su propio schema tiene sentido cuando el tipo de bloque también es usable en otro lado (como `icon-text-item`).

### group.tpl — el contenedor genérico

`group` es el único bloque genérico construido específicamente para contener otros bloques: renderiza un contenedor flex y recorre `block.blocks` con el patrón de arriba. En la práctica es donde terminan anidados la mayoría de los bloques marcados `"general"` (agrupando un heading, un text y un button juntos, por ejemplo).

### code.tpl — inyección de HTML/CSS/JS

`code` permite al comerciante inyectar HTML, CSS y JavaScript libre desde el editor. Usa `setting_type: "custom_code"`, que abre un editor de código en el panel, y renderiza el contenido con `| raw` (sin escapar) — el comerciante es responsable de lo que inyecta. El límite es de **50.000 caracteres** por bloque. Lleva tag `"general"`, así que cualquier sección que acepte esa tag lo incluye automáticamente.

### Claves del schema de block

| Clave | Qué hace |
|---|---|
| `name` | Nombre del bloque en el editor. |
| `tags` | Marca este bloque como disponible para cualquier sección (o bloque) que acepte esa tag. |
| `icon` | Ícono mostrado junto al nombre en el editor. |
| `limit` | Cantidad máxima de instancias de este bloque dentro de su padre. |
| `deletable` | Si es `false`, el comerciante puede configurar pero no quitar el bloque (usado para hijos obligatorios definidos inline). |
| `blocks` | Tipos de bloque hijo que este bloque acepta — mismas tres formas que la clave `blocks` de una sección. |
| `settings` | Definiciones de setting. |
| `presets` | Configuración por default aplicada cuando el bloque se agrega directamente (no vía preset de un padre). |

## 3. SNIPPETS

### Regla de decisión: snippet vs. section/block

Un snippet es un partial reutilizable **sin schema**. No es editable desde el editor y no aparece como una sección o bloque que el comerciante pueda agregar — existe solo para evitar duplicar markup y lógica en el diseño.

La regla práctica: si el comerciante debería poder agregar, quitar o reordenar algo desde el editor, hacelo sección o bloque. Si es plomería que siempre está presente cuando quien lo llama renderiza — una calculadora de envío, el total del carrito, un campo de formulario — hacelo snippet.

| Snippets (lógica de experiencia de compra) | Sections/Blocks (identidad de marca, editable por el comerciante) |
|---|---|
| Calculadora de envío | Banner hero |
| Total y resumen del carrito | Slideshow de imágenes |
| Formulario y variantes del producto | Testimonios |
| Formularios de login/registro | Accordion de FAQ |
| Breadcrumbs | Suscripción a newsletter |

### Organización en subcarpetas

Guardá los snippets en `snippets/`, agrupados por dominio:

```
snippets/
├── cart/            # Ítems de línea, modal/drawer, totales, cross-selling
├── payments/        # Cuotas, métodos de pago, bancos
├── product/         # Formulario del producto, variantes, galería de imágenes, video
├── product-list/    # Card de la grilla, filtros, paginación
├── forms/           # Inputs, selects, login/registro, reCAPTCHA
├── shipping/        # Calculadora, opciones, retiro en sucursal
├── header/          # Formulario de búsqueda, nav mobile, selector de idioma
├── footer/          # Links legales, logos de pago/envío
├── navigation/      # Paneles de navegación, menú hamburguesa
├── social/          # Botones de compartir, chat de WhatsApp
├── promotions/       # Tablas de descuento, mensajes de regalo
├── subscriptions/    # Planes de suscripción, precio, alertas
├── modals/           # Modal de quick-shop, wrapper de modal genérico
├── structured-data/  # JSON-LD para SEO
└── icon.tpl, image.tpl, card.tpl, breadcrumbs.tpl, notification.tpl, …  (raíz, cross-domain)
```

### Inclusión y paso de parámetros

```twig
{% include 'snippets/notification.tpl' with { type: 'add_to_cart' } %}
```

Pasá los parámetros con el objeto `with { ... }`: un snippet no tiene acceso implícito a las variables del scope desde donde se incluyó, solo a lo que se le pasa explícitamente (más los globales de la plataforma como `product`, `cart`, `settings`, `store`).

### snippets/image.tpl — imagen responsiva

`snippets/image.tpl` es el punto de entrada único del diseño para toda imagen responsiva — fotos de producto, imágenes de categoría, imágenes de posts de blog y valores de `image_picker` del editor pasan todos por ahí; renderiza como `<picture>` con AVIF/WebP cuando hay srcsets disponibles. Documenta sus propios parámetros en un comentario `{# #}` al inicio — copiá esa convención en cualquier snippet con más de uno o dos inputs:

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

{% set default_image_url =
  product_image ? image_src | product_image_url('large') :
  category_image ? image_src | category_image_url('large') :
  image_src
%}
{# ...resuelve srcset, lazy-loading, y el markup de <picture>/<img> a partir de ahí... #}
```

Quien lo llama pasa solo lo que necesita:

```twig
{% include 'snippets/image.tpl' with {
  image_src: product.featured_image,
  product_image: true,
  image_alt: product.name,
  image_thumbs: ['small', 'medium', 'large']
} %}
```

### Snippets con prefijo underscore (regla dura)

Los snippets con prefijo underscore (`_cart-item.tpl`, `_shipping-options.tpl`, `_product-grid.tpl`) son archivos que **el backend espera con ese nombre y ubicación exactos**. No los renombres ni los muevas a otra carpeta — la plataforma los busca por convención para renderizar funcionalidad específica.
