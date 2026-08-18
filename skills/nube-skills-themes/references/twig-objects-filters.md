# Twig, Objetos y Filtros

Referencia del motor de templates, los objetos de plataforma y los filtros disponibles en los diseños sectionable de Tienda Nube.

## Tabla de contenidos

1. [Twig 2.x en Tienda Nube](#1-twig-2x-en-tienda-nube)
2. [Objetos del modelo sectionable: section, block y settings](#2-objetos-del-modelo-sectionable-section-block-y-settings)
3. [Objetos globales](#3-objetos-globales)
4. [Globales de contexto](#4-globales-de-contexto)
5. [Filtros y métodos](#5-filtros-y-métodos)
6. [Filtros específicos del modelo sectionable](#6-filtros-específicos-del-modelo-sectionable)
7. [Tags y funciones de plataforma](#7-tags-y-funciones-de-plataforma)

---

## 1. Twig 2.x en Tienda Nube

Twig es un motor de plantillas basado en PHP. El backend genera datos (productos, settings, información de la tienda) y los expone a través de objetos y variables que se consumen en el frontend con sintaxis Twig.

**Todos los archivos que terminan en `.tpl` soportan Twig** — incluidos templates HTML, hojas de estilo CSS y archivos JavaScript templados (por ejemplo `checkout.scss.tpl`, `libraries.js.tpl`). Para operaciones matemáticas, manipulación de cadenas y filtros incorporados (`date`, `length`, `upper`, `lower`, `join`, `split`, `trim`), consultá la documentación oficial de Twig 2.x.

### Delimitadores

| Delimitador | Propósito | Ejemplo |
|---|---|---|
| `{{ ... }}` | Mostrar una expresión | `{{ product.name }}` |
| `{% ... %}` | Ejecutar sentencias (bucles, condicionales, includes) | `{% if product.display_price %}` |
| `{# ... #}` | Comentarios (no se renderizan en la salida) | `{# Esto es un comentario #}` |

El pipe `|` aplica un **filtro** al valor:

```twig
{{ store.name }}
{{ product.price | money }}
{{ 'cart.add_to_cart' | t }}
```

### Variables con set

Almacená valores o condiciones complejas con `{% set %}`, por ejemplo `{% set show_banner = settings.banner_show and settings.banner_image %}`, y usalas luego en condicionales.

### Condicionales

Usá `{% if %}` / `{% elseif %}` / `{% else %}`, combinando condiciones con `and`, `or` y paréntesis:

```twig
{% if product.has_stock %}
    <button>{{ 'cart.add_to_cart' | t }}</button>
{% else %}
    <button disabled>{{ 'cart.out_of_stock' | t }}</button>
{% endif %}
```

### Condicionales por página con la variable global template

Usá la variable `template` para cargar recursos solo en páginas específicas:

```twig
{% if template == 'product' %}
    {% if settings.show_product_fb_comment_box %}
        {{ fb_js }}
    {% endif %}
    {{ pin_js }}
{% endif %}
```

### Bucles y la variable loop

```twig
<ul class="footer-menu">
    {% for item in menus[settings.footer_menu] %}
        <li class="footer-menu-item">
            <a href="{{ item.url }}" {% if item.url | is_external %}target="_blank" rel="noopener noreferrer"{% endif %}>
                {{ item.name }}
            </a>
        </li>
    {% endfor %}
</ul>
```

Dentro de un bloque `for`, la variable `loop` provee metadatos de iteración:

| Propiedad | Descripción |
|---|---|
| `loop.index` | Iteración actual (1-indexado) |
| `loop.index0` | Iteración actual (0-indexado) |
| `loop.first` | `true` en la primera iteración |
| `loop.last` | `true` en la última iteración |
| `loop.length` | Cantidad total de ítems |

### Twig en CSS

Usá settings de la tienda dentro de hojas de estilo — así se implementan colores, fuentes y opciones de layout personalizables:

```css
.btn-primary {
    background-color: {{ settings.primary_color }};
    color: {{ settings.text_color }};
}
```

También funcionan los condicionales: `{% if settings.theme_variant == 'squared' %} ... {% endif %}` alrededor de reglas CSS completas.

### Twig en JavaScript

Inyectá cadenas traducidas y valores dinámicos en JavaScript:

```javascript
if (!variant.available) {
    button.val('{{ 'cart.out_of_stock' | t }}');
    button.addClass('nostock');
    button.attr('disabled', 'disabled');
}
```

### Incluir snippets: las tres formas

Los snippets son componentes `.tpl` reutilizables almacenados en la carpeta `snippets/`.

> **Nota terminológica**: en los Diseños Clásicos la carpeta y la tag se llaman `snipplets` (con L). En diseños sectionable se usa `snippets` (sin L).

#### {% snippet %}

El método más simple — incluye un snippet **sin parámetros**. La ruta es relativa a la carpeta `snippets/` de forma automática:

```twig
{% if settings.ad_bar and settings.ad_text %}
    {% snippet "header/header-advertising.tpl" %}
{% endif %}
```

#### {% include %}

Include estándar de Twig — permite pasar parámetros con la palabra clave `with`. La ruta debe comenzar desde `snippets/`:

```twig
{% include "snippets/notification.tpl" with {order_notification: true, add_to_cart: true} %}
```

Dentro del snippet, usá las variables pasadas como condicionales (`{% if order_notification %}...{% endif %}`). Llamá al mismo snippet varias veces con distintos parámetros para renderizar variantes en diferentes ubicaciones. El patrón también sirve para iconos SVG con clases CSS personalizables:

```twig
{% include "snippets/svg/search.tpl" with {svg_custom_class: "icon-inline svg-icon-text"} %}
```

#### {% embed %}

El método más potente — funciona como `include` pero agrega **sobreescritura de bloques**. Los `{% block %}` definen "slots" en el snippet que se completan con contenido personalizado al embeber. Por ejemplo, un componente de select reutilizable (`snippets/forms/form-select.tpl`) define dentro de su `<select>` el slot `{% block select_options %}{% endblock select_options %}`. Al embeber, completá el slot:

```twig
{% embed "snippets/forms/form-select.tpl" with {select_label: false, select_custom_class: 'js-sort-by'} %}
    {% block select_options %}
        <option value="1">{{ 'sort.price_low_to_high' | t }}</option>
        <option value="2">{{ 'sort.price_high_to_low' | t }}</option>
        <option value="3">{{ 'sort.newest' | t }}</option>
    {% endblock select_options %}
{% endembed %}
```

Para texto estático en parámetros de `include`/`embed`, usá el filtro `t`: `select_label_name: 'product.size' | t,`. Para texto dinámico, usá concatenación con `~`: `select_label_name: '' ~ variation.name ~ '',` o `select_id: 'variation_' ~ loop.index,`.

#### Comparación

| Característica | `{% snippet %}` | `{% include %}` | `{% embed %}` |
|---|---|---|---|
| Pasar parámetros | No | Sí (`with`) | Sí (`with`) |
| Sobreescritura de bloques | No | No | Sí |
| Prefijo de ruta | Auto `snippets/` | Manual `snippets/` | Manual `snippets/` |
| Mejor para | Includes simples | Componentes parametrizados | Componentes con slots de contenido |

---

## 2. Objetos del modelo sectionable: section, block y settings

Estos objetos son **nuevos del modelo sectionable** y no existen con esta forma en los Diseños Clásicos.

### section

Representa la instancia de la sección actual que se está renderizando. Cada sección es un archivo `.tpl` dentro de `sections/` que se invoca desde un JSON template.

| Propiedad | Tipo | Descripción |
|---|---|---|
| `section.id` | string | Identificador único de la instancia de sección |
| `section.index` | integer | Posición de la sección en la página (**base 0**, útil para decisiones de carga prioritaria) |
| `section.settings` | object | Valores de configuración definidos en el `{% schema %}` de la sección |
| `section.blocks` | array | Arreglo **ordenado** de objetos `block` en el orden definido por el comerciante (`block_order` ya aplicado) |

```twig
{% set settings = section.settings %}
{% set is_priority = section.index <= 1 %}

<div data-section-id="{{ section.id }}">
  {% for block in section.blocks %}
    {% include 'blocks/' ~ block.type ~ '.tpl' with { block: block } %}
  {% endfor %}
</div>
```

> En los Diseños Clásicos, `section` representa una sección de productos destacados definida en `sections.txt`, con propiedades `.id`, `.name`, `.description` y `.products`. No confundir con este objeto.

### block

Representa un bloque dentro de una sección. Los bloques son los componentes individuales que los comerciantes agregan, reordenan y configuran desde el editor.

| Propiedad | Tipo | Descripción |
|---|---|---|
| `block.id` | string | Identificador único de la instancia del bloque |
| `block.type` | string | Tipo de bloque (corresponde al **nombre del archivo `.tpl`** y la declaración en el schema) |
| `block.settings` | object | Valores de configuración definidos en el `{% schema %}` del bloque |
| `block.blocks` | array | Bloques hijos (para estructuras anidadas como `group.tpl`) |

```twig
{% set settings = block.settings %}

<div class="heading-block" {{ block | block_attributes }}>
  {{ settings.text | raw }}
</div>
```

Bloques anidados:

```twig
{% for child_block in block.blocks %}
  {% include 'blocks/' ~ child_block.type ~ '.tpl' with { block: child_block } %}
{% endfor %}
```

### settings en tres niveles

| Nivel | Se define en | Se accede como |
|---|---|---|
| Global | `config/settings_schema.json` | `settings.<id>` en cualquier template |
| Sección | `{% schema %}` de cada sección | `section.settings.<id>` |
| Bloque | `{% schema %}` de cada bloque | `block.settings.<id>` |

```twig
{% if settings.ajax_cart %}<div data-ajax-cart="true">...</div>{% endif %}
{% set full_width = section.settings.section_width == 'full' %}
{% set icon = block.settings.cart_icon | default('bag') %}
```

> En los Diseños Clásicos los settings se definen en `settings.txt` con otra sintaxis, pero el patrón de acceso (`settings.X`) es el mismo.

---

## 3. Objetos globales

Cada objeto tiene atributos accesibles con notación de punto. Se usan para mostrar valores (`{{ store.name }}`) o en sentencias (`{% if store.has_accounts %}`).

### store

Representa la tienda y su configuración global. Disponible en todas las páginas.

| Propiedad | Tipo / Descripción |
|---|---|
| `store.name` / `store.url` | string — Nombre y URL de la tienda |
| `store.logo` | string — URL del logo. Acepta parámetro de tamaño: `store.logo('medium')` |
| `store.phone` / `store.email` | string — Teléfono / email de la tienda |
| `store.address` | string — Dirección física |
| `store.contact_intro` | string — Información adicional para la página de contacto |
| `store.blog` | string — URL del blog |
| `store.twitter` / `store.twitter_user` | string — URL del perfil / nombre de usuario de Twitter |
| `store.facebook` / `store.instagram` / `store.whatsapp` / `store.tiktok` / `store.youtube` / `store.pinterest` | string — URLs de redes sociales |
| `store.country` | string — Código de país ISO 3166-1 (`AR`, `BR`, `MX`, etc.) |
| `store.currency` | string — Código de moneda ISO 4217 (`ARS`, `BRL`, `MXN`, etc.) |
| `store.live_chat` | string — Código de integración del servicio de chat online |
| `store.business_id` / `store.business_name` | string — Identificador / nombre de la empresa (solo Brasil) |
| `store.analytics_account` | string — ID de cuenta de Google Analytics |
| `store.domain` | string — Dominio asignado (`store.mitiendanube.com`) |
| `store.has_custom_domain` | boolean — `true` si tiene dominio propio |
| `store.has_accounts` | boolean — `true` si admite cuentas de clientes |
| `store.is_catalog` | boolean — `true` si es solo catálogo (sin compras) |
| `store.has_shipping` | boolean — `true` si tiene métodos de envío activados |
| `store.branches` | boolean — `true` si tiene locales físicos activados |
| `store.products_url` / `store.cart_url` / `store.contact_url` / `store.search_url` | string — URLs de páginas de la tienda |
| `store.shipping_calculator_url` | string — URL para cálculos de costos de envío |
| `store.checkout_url` | string — URL de la página de checkout |
| `store.customer_home_url` / `_register_url` / `_login_url` / `_logout_url` / `_reset_password_url` | string — URLs de cuenta del cliente |
| `store.customer_order_url` / `_info_url` / `_addresses_url` / `_address_url` / `_new_address_url` / `_main_address_url` | string — URLs de órdenes y direcciones del cliente |
| `store.customer_accounts` | string — `'optional'` si se permite checkout como invitado, `'mandatory'` si se requiere cuenta |

Usalo en renderizado condicional según la configuración de la tienda, por ejemplo `{% if store.country == 'BR' %}` o `{% if store.is_catalog %}`.

### product

Disponible en páginas de detalle de producto y dentro de loops de productos. **Los precios llegan en centavos** (`10000` = $100.00).

| Propiedad | Tipo / Descripción |
|---|---|
| `product.id` / `product.name` / `product.brand` | string — ID, nombre y marca |
| `product.price` | string — Precio en centavos. Si `compare_at_price` está definido, este es el precio promocional |
| `product.compare_at_price` | string — Precio original en centavos, o `false` si no hay precio de comparación |
| `product.display_price` | boolean — `true` si el producto tiene un precio para mostrar |
| `product.min_price` / `product.max_price` | string — Precio mínimo/máximo entre variantes (centavos); `null` si ninguna tiene precio |
| `product.canonical_url` / `product.social_url` | string — URL canónica / URL para compartir en redes |
| `product.description` | string — Descripción (HTML) |
| `product.stock` / `product.stock_control` | string / boolean — Stock actual / `true` si el stock lo administra la plataforma |
| `product.weight` / `product.weight_unit` | string — Peso / unidad (actualmente siempre `KG`) |
| `product.sku` / `product.tags` / `product.currency` | string / array / string — SKU, etiquetas, moneda ISO 4217 |
| `product.images` / `product.images_count` | array / string — Objetos `product_image` y cantidad |
| `product.featured_image` / `product.other_images` | object / array — Imagen principal / todas menos la primera |
| `product.default_options` | array — Nombres de opciones de la variante por defecto |
| `product.variations` | array — Objetos `variation` (propiedades del producto) |
| `product.variants_object` | array — Todos los objetos de variante con detalles completos |
| `product.installments` | string — Cantidad máxima de cuotas (solo Brasil) |
| `product.category` | object — Objeto `category` más cercano |
| `product.seo_title` / `product.seo_description` / `product.handle` | string — Título/descripción SEO y slug |
| `product.promotional_offer` | boolean — `true` si tiene promociones activas |
| `product.free_shipping` | boolean — `true` si tiene marcado envío gratis |
| `product.requires_shipping` | boolean — `true` si requiere envío físico (`false` para digitales/servicios) |
| `product.media` / `product.media_count` | array / integer — Ítems de media (imágenes y videos) y cantidad |
| `product.video_url` | string — URL de video externo (YouTube/Vimeo) si está configurado |
| `product.selected_or_first_available_variant` | object — Variante seleccionada actualmente, o primera disponible |
| `product.payment_methods_config` | object — Configuración de métodos de pago del producto |
| `product.installments_info_from_any_variant` | object — Info de cuotas desde cualquier variante que la tenga |

#### promotional_offer

Cuando `product.promotional_offer` es `true`:

| Propiedad | Tipo / Descripción |
|---|---|
| `product.promotional_offer.script.is_percentage_off` | boolean — `true` para descuentos porcentuales |
| `product.promotional_offer.parameters.percent * 100` | string — Porcentaje de descuento |
| `product.promotional_offer.script.is_discount_for_quantity` | boolean — `true` para descuentos por cantidad ("comprá 3+, obtenés 20% off") |
| `product.promotional_offer.selected_threshold.discount_decimal_percentage * 100` | string — Porcentaje de descuento por cantidad |

#### product_image

`id` (string), `name` (nombre de archivo), `alt` (texto alternativo), `position` (1-indexado; la posición 1 es la imagen principal).

#### variation y variation_option

`variation` representa una propiedad del producto ("Talle", "Color"): `id`, `name`, `options` (array de `variation_option`). Cada `variation_option` tiene `id` y `name` (por ejemplo "S", "Rojo").

#### product_variant

Una combinación única de opciones:

| Propiedad | Tipo / Descripción |
|---|---|
| `name` / `option1` / `option2` / `option3` / `options` | string / array — Nombre y valores de opciones |
| `price` / `compare_at_price` | string — Precio y precio original en centavos |
| `display_price` | boolean — `true` si tiene precio para mostrar |
| `currency` / `sku` / `weight` / `weight_unit` | string — Moneda, SKU, peso y unidad |
| `stock` / `stock_control` / `available` | string / boolean / boolean — Stock, control de stock, disponibilidad |

#### variants_object

`product.variants_object` provee cadenas de precio formateadas para consumo en JavaScript:

| Propiedad | Tipo / Descripción |
|---|---|
| `price_short` / `price_long` | string — Precio con símbolo (`$100`) / con símbolo y código ISO (`$100 ARS`) |
| `compare_at_price_short` / `compare_at_price_long` | string — Precio original en ambos formatos |
| `stock` / `sku` | string — Stock y SKU de la variante |
| `available` | boolean — `true` si tiene stock |
| `contact` | boolean — `true` si es un producto de contacto |
| `option0` / `option1` / `option2` | string — Valores de la primera/segunda/tercera opción |

### cart

Disponible en la página del carrito y como objeto global. **Los montos están en centavos.**

| Propiedad | Tipo / Descripción |
|---|---|
| `cart.items` / `cart.items_count` | array / string — Ítems del carrito y cantidad total |
| `cart.total` | string — Total del carrito **en centavos** |
| `cart.shipping_cost` | string — Costo de envío en centavos |
| `cart.subtotal_without_taxes` | string — Subtotal sin impuestos, en centavos |
| `cart.free_shipping` | object — Estado y umbrales de envío gratis |
| `cart.free_shipping.cart_has_free_shipping` | boolean — `true` si el carrito califica para envío gratis |
| `cart.free_shipping.min_price_free_shipping` | object — Umbral de precio mínimo para envío gratis |
| `cart.checkout_enabled` | boolean — `true` si el checkout está habilitado para este carrito |

### customer

Disponible cuando un cliente está autenticado: `customer.name`, `customer.email`, `customer.phone` (string), `customer.addresses` (array de direcciones), `customer.orders` (array de órdenes), `customer.default_address` (object).

### category

| Propiedad | Tipo / Descripción |
|---|---|
| `category.id` / `category.name` / `category.description` / `category.url` | string — Datos básicos |
| `category.parent` | object — Objeto `category` padre |
| `category.subcategories` | array — Objetos `category` hijos |
| `category.images` | array — Objetos de imagen de categoría |
| `category.active` | boolean — `true` si la URL actual es la de esta categoría |
| `category.top` | object — `category` de nivel superior en la jerarquía |
| `category.products` / `category.products_count` | array / string — Productos y cantidad |
| `category.seo_title` / `category.seo_description` / `category.handle` | string — SEO y slug |

### pages (paginación)

Estado de la página actual en un listado de categoría o resultados de búsqueda.

| Propiedad | Tipo / Descripción |
|---|---|
| `pages.previous` / `pages.next` | string — URL de la página anterior / siguiente |
| `pages.current` | string — Número de página actual |
| `pages.amount` | string — Cantidad total de páginas |
| `pages.numbers` | array — Objetos de página; cada ítem tiene `number` (string), `url` (string) y `selected` (boolean, `true` si es la página actual) |

### language y languages

`language` representa uno de los idiomas habilitados: `id` (string), `code` (código ISO 639-1 + país ISO 3166-1: `es_AR`, `pt_BR`), `name` (string), `active` (boolean, `true` si es el idioma activo) y `country` (código de país ISO 3166-1). `languages` es el arreglo de todos los idiomas disponibles — iteralo para construir un selector de idioma, mostrando solo si `languages | length > 1` y marcando el activo con `lang.active`.

### menus y navigation_item

`menus` es un diccionario de menús de navegación indexados por ID de menú. Cada menú es un arreglo de ítems de navegación:

```twig
{% set menu_links = menus[settings.footer_menu] %}
{% for item in menu_links %}
  <a href="{{ item.url }}">{{ item.name }}</a>
{% endfor %}
```

Cada `navigation_item`: `name` (string), `url` (string), `subitems` (array de `navigation_item` hijos), `current` (boolean, `true` si la página actual coincide con su URL).

### breadcrumb

Cada ítem de `breadcrumbs`: `name` (etiqueta), `url` (URL) y `last` (boolean, `true` si es el último breadcrumb).

### Opciones de shipping

Disponibles dentro del loop de opciones de envío en `shipping_options.tpl`:

| Propiedad | Tipo / Descripción |
|---|---|
| `option.name` | string — Nombre completo con tiempo de entrega |
| `option.short_name` | string — Solo el nombre (sin tiempo de entrega) |
| `option.time` | string — Tiempo de entrega ("5 días hábiles") |
| `option.date` | string — Fecha exacta de entrega ("Llega el lunes 03/15") |
| `option.show_price` | boolean — `true` si la opción tiene costo |
| `option.cost` | string — Costo incluyendo moneda y decimales |
| `option.cost.value` | string — Costo sin moneda ni decimales |
| `option.old_cost.value` | string — Costo anterior antes del envío gratis (solo envío gratis) |
| `option.method` | string — Método de entrega: `branch` para retiro en local, `table` para envío personalizado |

---

## 4. Globales de contexto

Variables disponibles en todas las páginas:

| Variable | Tipo / Descripción |
|---|---|
| `template` | string — Nombre del template actual: `home`, `product`, `category`, `cart`, `search`, `page`, `contact`, `404`, `password` |
| `page_template_content` | string — Contenido renderizado del template de página (usado en layouts) |
| `breadcrumbs` | array — Objetos breadcrumb para la página actual |
| `html_lang` | string — Valor del atributo HTML `lang` para el idioma actual |
| `back_to_admin` | string — Renderiza la barra de "volver al administrador" en modo preview |
| `is_order_cancellation` | boolean — `true` en la página de cancelación de orden |
| `afip` | string — Datos fiscales de AFIP (solo Argentina) |
| `fb_js` | string — JavaScript de comentarios de Facebook (**solo Diseños Clásicos**) |
| `pin_js` | string — JavaScript del botón de compartir de Pinterest (**solo Diseños Clásicos**) |

---

## 5. Filtros y métodos

Los filtros se aplican con el operador pipe `|` y se pueden encadenar para construir salidas complejas: `{{ 'css/style-critical.css' | static_url | css_tag }}` resuelve la ruta a una URL de CDN y la envuelve en una etiqueta `<link rel="stylesheet">`.

### Referencia de filtros

| Filtro | Ejemplo | Descripción |
|---|---|---|
| `raw` | `{{ settings.css_code \| raw }}` | Muestra el valor sin el escapado de Twig. **Solo con contenido de confianza** (settings, datos de plataforma); nunca con datos enviados por usuarios |
| `t` | `{{ 'general.add_to_cart' \| t }}` | Busca una clave de traducción (claves con puntos) en `translations/<locale>.json` y devuelve el texto del idioma actual. Interpolación: `{{ 'password.email_sent' \| t \| replace('{1}', email) }}` |
| `money` | `{{ product.price \| money }}` | Formatea un número como moneda con el formato de la tienda (decimales y símbolo). **Los precios llegan en centavos** |
| `static_url` | `{{ 'css/style-critical.css' \| static_url }}` | Resuelve una ruta relativa a `static/` en una URL completa de CDN |
| `css_tag` | `{{ 'css/style-critical.css' \| static_url \| css_tag }}` | Envuelve una URL en `<link rel="stylesheet">` |
| `script_tag` | `{{ '//cdn.example.com/lib.min.js' \| script_tag(true) }}` | Envuelve una URL en `<script>`. Pasá `true` para hacerla `async` |
| `img_tag` | `{{ 'placeholder-product.png' \| static_url \| img_tag }}` | Envuelve una URL en `<img>`. Acepta alt y atributos: `img_tag(store.name, {class: 'logo-img transition-soft-slow'})` |
| `a_tag` | `{{ 'general.my_account' \| t \| a_tag(store.customer_home_url, '', 'nav-accounts-link') }}` | Envuelve contenido en `<a>`. Parámetros: URL, título, clase CSS |
| `product_image_url` | `{{ image \| product_image_url('huge') }}` | URL de una imagen de producto en un tamaño. Tamaños: `tiny`, `small`, `medium`, `large`, `huge`, `original`, `1080p` |
| `settings_image_url` | `{{ section.settings.banner_image \| settings_image_url('1080p') }}` | URL de una imagen de un setting del diseño (definida vía `image_picker` en el schema). Mismos tamaños que `product_image_url` |
| `category_image_url` | `{{ image_name \| category_image_url('large') }}` | URL de una imagen de categoría. Mismos tamaños que `product_image_url` |
| `has_custom_image` | `{% if "seal_img.jpg" \| has_custom_image %}` | Verifica si una imagen fue subida en el personalizador del diseño |
| `is_external` | `{% if item.url \| is_external %}target="_blank"{% endif %}` | Verifica si un enlace de menú apunta a una URL externa |
| `take` | `{% set search_suggestions = products \| take(6) %}` | Limita una colección a una cantidad de ítems |
| `shuffle` | `{% set related_products = products \| take(4) \| shuffle %}` | Reordena aleatoriamente una colección |
| `highlight` | `{{ product.name \| highlight(query) }}` | Envuelve el texto coincidente en `<strong>` (resultados de búsqueda) |
| `format_address` | `{{ address \| format_address }}` | Formatea un objeto de dirección como dirección completa multilínea |
| `format_address_short` | `{{ customer.default_address \| format_address_short }}` | Formatea una dirección abreviada en una línea |
| `json_encode` | `<div data-variants="{{ product.variants_object \| json_encode }}">` | Codifica un valor como string JSON |
| `static_inline` | `{{ 'css/style-critical.css' \| static_url \| static_inline }}` | Inserta el contenido de un archivo estático directamente en la página (inlinea CSS crítico) |
| `payment_new_logo` | `{% set img_url = payment_method \| payment_new_logo %}` | URL del logo de un método de pago |
| `add_param` | `{{ product.url \| add_param('variant', product.selected_or_first_available_variant.id) }}` | Agrega un parámetro de consulta a una URL |
| `sanitize` | `{% set method_clean = method \| sanitize %}` | Sanitiza un string para uso seguro en atributos HTML e IDs |

> En los Diseños Clásicos el filtro de traducción se llama `translate` y las traducciones se definen en `translations.txt` usando strings literales como claves. En sectionable, `t` usa claves con puntos.

### google_fonts_url

Genera una URL de Google Fonts con los pesos especificados a partir de las fuentes seleccionadas en la personalización del diseño; mostrá el resultado sin escapar con `raw`:

```css
@import url('{{ [settings.font_headings, settings.font_rest] | google_fonts_url('300, 400, 700') | raw }}');
```

### Patrones de encadenamiento comunes

```twig
{{ store.logo | img_tag | a_tag(store.url) }}
{{ product.featured_image | product_image_url('large') | img_tag(product.name) }}
{{ store.logo('medium') | img_tag(store.name, {class: 'logo-img transition-soft-slow'}) | a_tag(store.url) }}
```

---

## 6. Filtros específicos del modelo sectionable

### block_attributes

Genera los atributos de datos que el editor necesita para identificar y resaltar un bloque en la vista previa. **Es obligatorio aplicarlo al elemento raíz de cada template de bloque** — sin él, el editor no puede seleccionar el bloque:

```twig
<div class="heading-block" {{ block | block_attributes }}>
  {{ block.settings.text | raw }}
</div>
```

### resolve_media

Resuelve un valor de setting `image_picker` (que comienza con `@media-lib:`) en un objeto de media con una propiedad `sourceUrl`:

```twig
{% set media = image_src | resolve_media %}
<img src="{{ media.sourceUrl }}" />
```

---

## 7. Tags y funciones de plataforma

Tags y funciones propias de la plataforma en los templates de diseños sectionable:

| Tag / función | Uso |
|---|---|
| `{% schema %} ... {% endschema %}` | Declara la configuración (settings y bloques aceptados) de una sección o bloque; sus valores se leen vía `section.settings` / `block.settings` |
| `{% layout_template 'header' %}` / `{% layout_template 'footer' %}` | Renderiza las partes `header` / `footer` del layout (layout templates) |
| `{{ page_template_content }}` | Renderiza el JSON template de la página actual (`templates/pages/<page>.json`) |
| `{{ component('head-tags') }}` | Renderiza los meta tags de la plataforma en el `<head>` (charset, viewport, canonical, tags OG) |
| `{{ component('nubesdk-slot', { type: "..." }) }}` | Punto de extensión para apps que se integran vía NubeSDK |
| `{% platform_head_content %}` / `{% platform_body_content %}` | Tags inyectados por el backend (scripts de tracking, feature flags); el diseño no controla qué se renderiza acá |

Además, `{% snippet %}`, `{% include %}` y `{% embed %}` (sección 1) son las tags de composición de templates, y los filtros `block_attributes` y `resolve_media` (sección 6) completan el contrato entre el diseño y el editor de secciones.
