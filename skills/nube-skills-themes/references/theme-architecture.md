# Arquitectura de un tema sectionable

Referencia de la arquitectura de los diseños sectionable (basados en secciones y bloques) de Tiendanube: qué archivo cumple qué rol, cómo fluye el renderizado y qué formato tiene cada pieza.

## Tabla de contenidos

1. [El modelo sectionable en 10 líneas](#1-el-modelo-sectionable-en-10-líneas)
2. [Estructura de carpetas](#2-estructura-de-carpetas)
3. [layouts/layout.tpl: anatomía](#3-layoutslayouttpl-anatomía)
4. [Formato JSON de templates](#4-formato-json-de-templates)
5. [Catálogo de page templates](#5-catálogo-de-page-templates)
6. [Layout templates: header.json y footer.json](#6-layout-templates-headerjson-y-footerjson)
7. [custom/ y static/](#7-custom-y-static)

---

## 1. El modelo sectionable en 10 líneas

Los diseños sectionable componen las páginas a partir de **secciones** y **bloques** que el usuario reorganiza desde el editor, en lugar de fijar la estructura en templates `.tpl` estáticos. El modelo desacopla contenido de estructura:

- El **JSON template** (`templates/pages/*.json`, `templates/layout/*.json`) define **QUÉ** se muestra: qué sections aparecen, en qué orden, con qué settings y qué blocks contienen.
- El **schema** (`{% schema %}…{% endschema %}` al final de cada section y block) define **QUÉ PUEDE EDITAR** el usuario: tipos de input, defaults, visibilidad condicional, presets y qué blocks acepta cada padre. Es la pieza de mayor impacto: la experiencia de edición depende de qué tan rico esté el schema.
- Los archivos **`.tpl`** de sections y blocks definen **CÓMO** se renderiza. Los **snippets** son fragmentos sin schema para lógica de experiencia de compra (carrito, pagos, envíos, formularios, variantes, filtros): reutilizables pero no editables desde el editor.

Pipeline de render:

```
templates/pages/<página>.json
  └── declara qué sections aparecen y sus settings
        └── sections/<tipo>.tpl lee section.settings.* y section.blocks
              └── blocks/<tipo>.tpl lee block.settings.* (y opcionalmente block.blocks)
                    └── puede incluir snippets/<...>.tpl para lógica de compra

layouts/layout.tpl envuelve todo:
  <head> → fuentes, CSS crítico, tokens de estilo
  <body>
    {% layout_template 'header' %}    ← templates/layout/header.json
    <main>{{ page_template_content }}</main>   ← templates/pages/<página>.json
    {% layout_template 'footer' %}    ← templates/layout/footer.json
    modales, notificaciones, scripts
```

**Ipanema** es actualmente el único diseño basado en secciones disponible como base.

---

## 2. Estructura de carpetas

Árbol completo de un diseño sectionable:

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

> **⚠️ Nota sobre instalaciones reales:** la documentación de estructura muestra la carpeta `translations/`, pero la documentación del CLI muestra `locales/` en instalaciones descargadas. Mirá qué carpeta existe en el proyecto real antes de crear o editar archivos de traducción. Además, las instalaciones bajadas por CLI traen dos elementos extra que no aparecen en el árbol de arriba: una carpeta `custom/` y un archivo `manifest.json` (ver [sección 7](#7-custom-y-static)).

### config/

Settings de alcance global del diseño (colores, tipografía, defaults de header/footer, …). Solo dos archivos: `settings_schema.json` (schema de settings globales: favicon, colores, tipografía, botones, header, footer, product card, carrito, checkout) y `settings_data.json` (valores guardados). Accesibles desde cualquier `.tpl` vía `settings.*`:

```twig
{{ settings.background_color }}
{{ settings.font_headings }}
```

### sections/

Unidades de ancho completo, agrupadas en familias:

- **Layout** — `header.tpl`, `footer.tpl`, `announcement-bar.tpl`: compartidas en todas las páginas.
- **Contenido principal** — `main-product.tpl`, `main-cart.tpl`, `main-products-grid.tpl`, `main-blog.tpl`, …: contenido central de un tipo de página específico; el prefijo `main-` indica que no son reutilizables entre páginas.
- **Marketing / marca** — `hero.tpl`, `banners.tpl`, `slideshow.tpl`, `video.tpl`, `image-with-text.tpl`, `testimonials.tpl`, `featured-brands.tpl`, `newsletter.tpl`, `rich-text.tpl`, `faq.tpl`, `timer-offers.tpl`.
- **Producto** — `product-list.tpl`, `featured-product.tpl`, `related-products.tpl`, `product-description.tpl`.

Cada archivo de section termina con un bloque `{% schema %}`. El nombre que aparece en el editor proviene del campo `name` del schema (una clave `t:`).

### blocks/

Componentes con schema renderizados dentro de sections. Dos categorías: **genéricos** (`heading.tpl`, `text.tpl`, `image.tpl`, `button.tpl`, `video.tpl`, `menu.tpl`, `group.tpl`, `accordion.tpl`, `code.tpl`) usables en cualquier section que los acepte, y **específicos de una section**: slideshow/banners (`slide.tpl`, `carousel-slide.tpl`, `banner.tpl`), producto (`product-media.tpl`, `product-info.tpl`, `purchase-info.tpl`, `products.tpl`, `description.tpl`, `product-recommendations.tpl`), categorías/marcas (`category-nav.tpl`, `category-item.tpl`, `brand-group.tpl`, `brand-logo.tpl`), FAQ/testimonios/icon-text (`faq-group.tpl`, `faq-list.tpl`, `faq-item.tpl`, `testimonial-group.tpl`, `testimonial.tpl`, `icon-text-group.tpl`, `icon-text-item.tpl`), header/footer (`header-logo.tpl`, `header-navigation.tpl`, `header-utilities.tpl`, `footer-institutional.tpl`, `footer-menu.tpl`, `footer-newsletter.tpl`) y formularios/utilidades (`newsletter-form.tpl`, `announcement.tpl`, `payment-icons.tpl`). Cada archivo de block también termina con un `{% schema %}`.

### snippets/

Fragmentos sin schema, organizados por dominio de experiencia de compra:

- `cart/` — ítems del carrito, modal/drawer, totales, fulfillment, cross-selling.
- `payments/` — cuotas, medios de pago, bancos, detalle de pago.
- `product/` — formulario de producto, variantes, galería de imágenes, video, cantidad, detalle de pago.
- `product-list/` — card de grilla, filtros (precio, propiedades, categoría), paginación, orden.
- `forms/` — inputs, selects, dropdowns, formularios de login/registro, reCAPTCHA.
- `shipping/` — calculadora de envío, opciones, sucursales, progreso de envío gratis.
- `header/` — formulario de búsqueda, navegación mobile, selector de idioma.
- `navigation/` — paneles de navegación, menú hamburguesa.
- `footer/` — links legales, info de claim, logos de medios de pago y envío.
- `social/` — botones de share, links de contacto, chat de WhatsApp.
- `subscriptions/` — planes de suscripción, precio, alertas.
- `promotions/` — labels de promoción, mensajes de regalo, tablas de descuento.
- `placeholders/` — skeleton loaders. · `modals/` — quick-shop, wrapper de modal genérico.
- *(raíz)* — `icon.tpl`, `image.tpl`, `card.tpl`, `breadcrumbs.tpl`, `labels.tpl`, `notification.tpl`.

Se incluyen con `{% include 'snippets/<path>.tpl' %}`, opcionalmente con contexto: `{% include 'snippets/notification.tpl' with { type: 'add_to_cart' } %}`.

### translations/

Dos tipos de archivos de locale: `<locale>.json` (ej. `en.json`, `es.json`, `pt.default.json`) con strings del storefront para el comprador, y `<locale>.schema.json` (ej. `en.schema.json`, `es.schema.json`) con labels del editor para el usuario. Locales disponibles: `en`, `es`, `es_AR`, `es_CL`, `es_CO`, `es_MX`, `pt.default`.

**Fallback de locale** — al solicitar un locale (por ejemplo `pt_BR`), el resolver busca en este orden:

1. `translations/pt_BR.json` — coincidencia exacta.
2. `translations/pt.json` — coincidencia solo por idioma.
3. `translations/<anything>.default.json` — el default regional para ese idioma (ej. `translations/pt.default.json`).

El mismo fallback aplica a los archivos `.schema.json`: distribuí un único default regional y agregá archivos por país solo cuando el copy necesita diferenciarse.

---

## 3. layouts/layout.tpl: anatomía

El layout es el shell HTML dentro del cual se renderiza toda página. Un diseño sectionable tiene exactamente uno — `layouts/layout.tpl` — más la carpeta `layouts/resources/` con los assets que inyecta inline: `icons-sprite.tpl` (sprite de `<symbol>` SVG) y `style-tokens.tpl` (propiedades personalizadas de CSS — fuentes, colores — como `<style>` inline). Ver el árbol de la [sección 2](#2-estructura-de-carpetas).

El layout hace cinco cosas, en orden: renderiza el `<head>`, abre el `<body>`, renderiza la región del header, inyecta el contenido de la página activa, renderiza la región del footer, y por último carga el JavaScript. Versión resumida y comentada del archivo real:

```twig
<!DOCTYPE html>
<html lang="{{ html_lang }}">
  <head>
    {{ component('head-tags') }}

    {# Style tokens: fuentes + propiedades personalizadas de CSS, inline como <style> #}
    <style>
      {% include 'layouts/resources/style-tokens.tpl' %}
    </style>

    {# CSS crítico + utilitario inline; CSS async postergado con el truco media="print" #}
    {{ 'css/style-critical.css' | static_url | static_inline }}
    {{ 'css/style-utilities.css' | static_url | static_inline }}
    <link rel="stylesheet" href="{{ 'css/style-async.css' | static_url }}" media="print" onload="this.media='all'">

    {# CSS del comerciante, desde una configuración global #}
    {% if settings.css_code %}
      <style id="custom-theme-css">{{ settings.css_code | raw }}</style>
    {% endif %}

    {% platform_head_content %}
  </head>

  <body class="template-{{ template | replace('.', '-') }}">
    {{ component('nubesdk-slot', { type: "before_main_content" }) }}
    {% include 'layouts/resources/icons-sprite.tpl' %}

    {% if template != 'password' %}
      <header class="js-header header">
        {% layout_template 'header' %}
      </header>
      {{ component('nubesdk-slot', { type: "after_header" }) }}
    {% endif %}

    <main id="MainContent" class="main-content main-container" role="main">
      {{ page_template_content }}
    </main>

    {% layout_template 'footer' %}

    {# Partials globales que renderizan en toda página excepto la de contraseña: modal del carrito, quick-shop, WhatsApp, popup promocional #}
    {% if template != 'password' %}
      {% include 'snippets/cart/cart-modal.tpl' %}
      {% include 'snippets/social/whatsapp-chat.tpl' %}
    {% endif %}

    {{ 'js/libraries-standalone.js' | static_url | script_tag }}
    <script>
      LS.ready.then(function() {
        {% include "static/js/libraries.js.tpl" %}
        var script = document.createElement('script');
        script.src = '{{ "js/store.js" | static_url }}';
        document.body.appendChild(script);
      });
    </script>

    {% platform_body_content %}
  </body>
</html>
```

| Llamada | Qué renderiza |
|---|---|
| `component('head-tags')` | Meta tags de la plataforma (charset, viewport, canonical, tags OG/Twitter). |
| `component('nubesdk-slot', { type: "..." })` | Punto de extensión de Nube SDK donde las apps pueden renderizar contenido. |
| `{% layout_template 'header' %}` / `{% layout_template 'footer' %}` | Renderizan los layout templates de header y footer — `templates/layout/header.json` y `footer.json`. |
| `{{ page_template_content }}` | Renderiza el JSON template de la página actual — `templates/pages/<page>.json`. |
| Filtro `static_inline` | Inserta el contenido de un asset estático directamente en el HTML (usado para el CSS crítico/utilitario, para evitar una request bloqueante). |
| `platform_head_content` / `platform_body_content` | Tags inyectados por el backend (scripts de tracking, feature flags) — el diseño no controla qué renderiza acá. |

`template` es un string provisto por la plataforma (`home`, `product`, `category`, `password`, …) — la misma variable de identificación que usan los diseños clásicos para condicionales por template, todavía disponible en diseños sectionable para casos que el `enabled_on` de una sección no puede expresar.

**Un solo layout.** Los diseños sectionable no soportan layouts alternativos: no existe un `layouts/checkout.tpl` ni un override de layout por template. Toda página, incluida la de contraseña/mantenimiento, se renderiza a través de este único `layout.tpl`, ramificándose internamente con `{% if template != 'password' %}` donde el comportamiento necesita diferir (por ejemplo, ocultando el header/footer en la página de contraseña).

---

## 4. Formato JSON de templates

Toda página se define con un JSON template: declara qué secciones renderizan, en qué orden, con qué settings precargados y qué bloques contienen. Las dos subcarpetas de `templates/` (`pages/` y `layout/`) usan exactamente el mismo formato — lo que cambia es solo dónde se renderiza el resultado. Estructura:

```json
{
  "sections": {
    "<section-id>": {
      "type": "<nombre del archivo en sections/>",
      "settings": { ... },
      "blocks": {
        "<block-id>": {
          "type": "<nombre del archivo en blocks/>",
          "settings": { ... },
          "blocks": { ... },
          "block_order": [ ... ]
        }
      },
      "block_order": [ "<block-id>", ... ]
    }
  },
  "order": [ "<section-id>", ... ]
}
```

| Clave | Qué hace |
|---|---|
| `sections` | Diccionario de secciones con un id arbitrario como clave. |
| `order` | Array que define el orden de renderizado de las secciones. |
| `type` | Nombre del archivo en `sections/` o `blocks/` (sin la extensión `.tpl`). |
| `settings` | Valores precargados para los settings declarados en el schema. |
| `blocks` | Diccionario de bloques hijos, con la misma estructura recursiva. |
| `block_order` | Array que controla el orden de renderizado de los bloques dentro de su padre. |

Los bloques anidan recursivamente: en `templates/pages/home.json`, por ejemplo, la section `slideshow` contiene un block `slide` que a su vez contiene `heading`, `text` y `button`, cada nivel con su propio `block_order`. El `header.json` de la [sección 6](#6-layout-templates-headerjson-y-footerjson) es un ejemplo real completo del formato.

Los valores de setting pueden ser claves `t:` resueltas desde los archivos `*.schema.json` de traducciones, de modo que los defaults del template aparezcan en el idioma del comerciante en el editor:

```json
"settings": {
  "text": "t:defaults.slide.heading",
  "label": "t:defaults.slide.button"
}
```

**Roadmap — templates personalizados.** Hoy ya es posible editar los templates default de Producto y Categoría desde el editor. Se está avanzando hacia que el comerciante pueda crear templates personalizados además de los default y asignarlos a una Página, Producto o Categoría específica desde el Admin de Tiendanube. La asignación vive en el Admin, no en el código del diseño.

---

## 5. Catálogo de page templates

Un archivo JSON por tipo de página en `templates/pages/`. El archivo define las secciones default; el comerciante las personaliza desde el editor.

| Archivo | Página | Secciones típicas |
|---|---|---|
| `home.json` | Página de inicio | `slideshow`, `banners`, `featured-product`, `instagram-feed`, `newsletter` |
| `product.json` | Detalle de producto | `main-product` (con bloques `product-media`, `product-info`), `related-products` |
| `category.json` | Categoría / listado de productos | `main-products-grid`, `category-hero` |
| `cart.json` | Carrito de compras | `main-cart` |
| `search.json` | Resultados de búsqueda | `main-products-grid` (mismo renderizado que categoría, distinta fuente de datos) |
| `blog.json` | Listado del blog | `main-blog` |
| `blog-post.json` | Post del blog | `main-blog-post` |
| `page.json` | Página genérica del comerciante | `main-page`, `rich-text` |
| `contact.json` | Formulario de contacto | `main-contact` |
| `password.json` | Tienda en mantenimiento | `password-logo` — la única página que se renderiza sin el header/footer de layout templates |
| `404.json` | No encontrado | `main-404` |

**Un template por tipo, no por recurso:** `page.json` es el template para **toda** página personalizada creada por el comerciante (Sobre Nosotros, FAQ, Política de Envíos, …) — hay un único template compartido, no un archivo JSON por página. El contenido propio de la página (título, cuerpo) viene del registro de página del comerciante, no del template. Es un mecanismo distinto al roadmap de asignar un template propio a un producto o página puntual (sección 4).

**Páginas de cuenta** — `templates/pages/account/` guarda el área de cuenta del cliente, un archivo por pantalla: `login.json` (inicio de sesión), `register.json` (registro), `reset.json` (solicitar link de restablecimiento de contraseña), `newpass.json` (definir nueva contraseña), `info.json` (editar información personal), `addresses.json` (lista de direcciones), `address.json` (agregar/editar una dirección), `orders.json` (historial de pedidos) y `order.json` (detalle y seguimiento de un pedido). Renderizan igual que cualquier otro page template — vía `{{ page_template_content }}` — solo que en `/login`, `/addresses`, etc.

---

## 6. Layout templates: header.json y footer.json

Los layout templates renderizan en toda página, sin importar qué page template esté activo. Hoy hay exactamente dos: header y footer.

**No confundir con `layouts/`:** `templates/layout/` y `layouts/layout.tpl` son dos carpetas distintas con nombre parecido. `layouts/layout.tpl` es el shell HTML; `templates/layout/*.json` es el contenido de secciones que se renderiza *dentro* de las regiones de header y footer de ese shell.

```
templates/
└── layout/
    ├── header.json    # Renderizado por {% layout_template 'header' %} en layouts/layout.tpl
    └── footer.json     # Renderizado por {% layout_template 'footer' %} en layouts/layout.tpl
```

Usan exactamente el mismo formato JSON que un page template — diccionario `sections` más array `order` — con dos claves extra en el nivel raíz, `type` y `name`, que identifican el template para el editor. Header real, resumido de `templates/layout/header.json` — una barra de anuncios más el header en sí:

```json
{
  "type": "header",
  "name": "Header",
  "sections": {
    "announcement": {
      "type": "announcement-bar",
      "disabled": true,
      "settings": {
        "animation": "slider",
        "section_width": "page",
        "background_color": "#000000",
        "text_color": "#FFFFFF"
      },
      "blocks": {
        "announcement_1": { "type": "announcement", "settings": { "text": "Envíos a todo el país" } },
        "announcement_2": { "type": "announcement", "settings": { "text": "Hasta 12 cuotas" } }
      },
      "block_order": ["announcement_1", "announcement_2"]
    },
    "header": {
      "type": "header",
      "settings": {
        "logo_position_desktop": "center",
        "section_width": "full",
        "background_color": "#FFFFFF"
      },
      "blocks": {
        "logo": { "type": "header-logo", "settings": { "height": 50 } },
        "utilities": { "type": "header-utilities", "settings": { "format": "icons", "cart_icon": "bag" } },
        "navigation": { "type": "header-navigation", "settings": { "menu": "navigation" } }
      },
      "block_order": ["logo", "utilities", "navigation"]
    }
  },
  "order": ["announcement", "header"]
}
```

`footer.json` sigue el mismo formato: `"type": "footer"`, `"name": "Footer"`, y una section `footer` con bloques como `footer-institutional`, `footer-menu` y `footer-newsletter`.

Detalles importantes:

- Una sección acá puede estar `"disabled": true` por default — existe en el JSON y mantiene sus configuraciones guardadas, pero no renderiza hasta que el comerciante la reactive.
- La sección `header` no es un slot fijo: el logo, las utilities y la navegación son **bloques** que el comerciante puede reordenar o quitar, igual que en cualquier otra sección.
- `announcement-bar` y `header` son archivos `.tpl` de sección comunes, con una restricción `enabled_on.layout_templates` en su schema — nada en ellos es estructuralmente especial más allá de vivir en este archivo en vez de un page template.
- No se puede declarar una tercera región (una `aside`, por ejemplo): Ipanema entrega exactamente estos dos layout templates y no existe mecanismo para agregar otro. Para contenido compartido fuera del header/footer, renderizalo directo desde `layouts/layout.tpl`, o como una sección dentro de los page templates que lo necesiten.
- Los comerciantes editan header y footer desde la misma interfaz del editor que cualquier página; los cambios se guardan de vuelta en estos dos archivos, exactamente igual que editar un page template.

---

## 7. custom/ y static/

**`static/`** — assets compilados del tema, referenciados desde `layouts/layout.tpl`:

| Archivo | Qué hace |
|---|---|
| `css/style-critical.css` | CSS above-the-fold, inlinado en `<head>`. |
| `css/style-utilities.css` | Clases utilitarias, inlinadas en `<head>`. |
| `css/style-async.css` | CSS below-the-fold, cargado de forma asincrónica. |
| `js/libraries-standalone.js` | Librerías de terceros empaquetadas (Swiper, lazysizes, …). |
| `js/libraries.js.tpl` | Loader con template para librerías adicionales y configuración. |
| `js/store.js` | Lógica client-side del diseño (vanilla JS). |
| `checkout.scss.tpl` | Estilos de branding para el checkout. |

**`custom/`** — no aparece en la documentación de estructura del tema, pero las instalaciones descargadas con el CLI la traen junto con un `manifest.json` en la raíz. Es la carpeta destinada a las personalizaciones propias del proyecto, separadas del código del tema base: poné ahí los archivos propios y dejá `static/` para los assets compilados del tema. Verificá su contenido y convenciones en el proyecto real antes de agregar archivos.
