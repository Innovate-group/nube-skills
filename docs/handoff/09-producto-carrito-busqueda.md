# Producto, carrito y búsqueda

Lo que la plataforma hace con variantes, stock, fotos, la card de producto, la ficha, el
carrito, la búsqueda y los filtros. Es donde el tema tiene más contrato con el JS privado de
Tienda Nube, y donde un error cuesta ventas. Cada sección se puede leer sola. Lo general del
DOM inyectado (wrappers, slots, formularios, `?snipplet=`) está en
[Lo que la plataforma inyecta](08-plataforma.md). Las formas de Twig para leer estos objetos,
en [Twig](07-twig.md). La API `LS` y Swiper, en [JavaScript](11-javascript.md).

## Lo esencial

- Las variantes llegan con reglas que no son las obvias: las opciones vienen en orden
  alfabético, `option.id` es el nombre de la opción, y `variant.stock` en `null` significa
  stock infinito.
- "Sin foto" no es `null`: la plataforma sirve un placeholder `no-photo`, y `variant.image`
  nunca viene vacío.
- Las colecciones y la búsqueda no tratan igual el stock. `category.products` trae solo los
  productos directos y topea en 12.
- La card y la ficha dependen de hooks que el JS privado busca por clase y por posición:
  `data-item-slider-id` único, `js-offer-*`, `#product-shipping-container`,
  `input[type=submit].js-addtocart`.
- La plataforma re-renderiza por AJAX la lista del carrito **y** los totales. Las filas de
  `cart-totals.tpl` son hooks: se ocultan, nunca se sacan.
- Un precio comparativo menor que el de venta rompe tres renders del tema base. Hace falta un
  único criterio de oferta, igual en Twig y en JS.
- El video de producto (Cloudflare Stream) se factura por minuto entregado: un reproductor
  duplicado e invisible cuesta plata.

## Variantes

- ⚠️ **Las opciones de variante llegan en orden ALFABÉTICO** (`L, M, S, XS`) [MC]. Se reordenan
  en Twig con una escala, no en JS, para que salgan bien desde el primer pintado. Lo que no está
  en la escala va al final, y los talles numéricos no se tocan. Cada snippet que dibuja
  opciones tiene su propio loop: si no se ordenan en todos, algunos quedan alfabéticos (en MC,
  el quick add, el cross-sell del carrito y un kit).
- ⚠️ **El orden de `product.variations` (color primero, talle después, o al revés) lo decide el
  Admin.** Se reordena con CSS (`[data-variation-kind="color"] { order: -1 }`), no cambiando el
  `for`, porque `loop.index` arma el `id` y el `for` de los selects. El costo es que la
  tabulación queda en el orden del DOM [MC].
- ✅ **El `option.id` de una variante ES su nombre** (`"NUMERO 36"`, `"L"`, hasta `"-"`)
  [MC 2026-09-09]. De él dependen el `value` del POST, `data-option-id` y la comparación contra
  `option0/1/2` de `data-variants`. Al "limpiar" un talle se toca solo el rótulo visible, nunca
  el id: si cambia, los chips quedan deshabilitados sin error. Lo mismo pasa con
  `data-filter-value` en los filtros. Las consecuencias en Twig (`variation.id` es un índice y
  el 0 es falsy) están en [Twig](07-twig.md).
- ⚠️ **La raíz de la ficha trae `data-variants`**, con `id`, `option0/1/2` e `image` por
  variante. Ese `image` es el mismo media id del `data-image` de cada slide de la galería. Con
  eso se resuelve la variante inicial desde el DOM. Los ids de opción son únicos en toda la
  tienda [MC].
- ⚠️ **`changeVariantButton` mueve `selected` solo si el click nace en el botón.** Si se elige
  desde el select, el botón de desktop queda marcado con la variante vieja: hace falta un sync
  aparte [MC].
- ⚠️ **`noStockVariants` recalcula `btn-variant-no-stock` en cada cambio de variante.** Esa
  clase trae un `:after` con una diagonal. Todo lo que dependa del stock de una opción se
  dibuja siempre y lo revela la clase, no un `{% if %}` de Twig [MC].
- ⚠️ **`initProductListVariantHandler` busca la card con `querySelector('[data-product-id]')`**,
  o sea siempre la primera del documento. Con varias cards del mismo producto, cambiar un talle
  en una le cambia la foto a otra. `data-quickshop-id` es el selector con el que
  `LS.changeVariant` se acota a una card [MC]. Con cards duplicadas por color, partir del
  elemento del evento (ver [JavaScript](11-javascript.md)).
- ⚠️ **Una muestra de color con `js-variation-option` o `js-color-variant` engancha el cambio de
  variante de la plataforma.** Como la plataforma escucha en el mismo `document`,
  `stopPropagation` no alcanza (haría falta `stopImmediatePropagation` y depender del orden de
  registro). Si la muestra no debe cambiar la variante, no le pongas esos hooks [MC].
- 🔥 **`item.short_variant_name` tiene el formato real `(CELESTE, M)`**, con paréntesis y coma,
  no ` / ` ✅ [MC 2026-09-17]. Las opciones llegan en orden alfabético, y un talle con una coma
  adentro (`Numero35,5`) rompe el split: tiene que caer a un respaldo. El bug que dejó el
  rótulo del carrito con un talle que no se eligió fue un `in` sobre ese string (ver
  [Twig](07-twig.md)).
- Cuándo dispara `LS.registerOnChangeVariant` y por qué `LS.changeVariant` no corre al cargar la
  ficha, en [JavaScript](11-javascript.md).

## Stock

- ✅ **`variant.stock` en `null` significa stock infinito** (el control de stock apagado), no
  cero. "Se muestra" es `stock is null or stock > 0` [MC 2026-09-28].
- ✅ **Las dos lecturas de stock de la plataforma pueden no coincidir** [MC 2026-09-28].
  `data-variants` (sale de `product.variants_object_reduced`) mostró talles en 0 que
  `variant.stock` en Twig veía con stock. Pasarse a `variants_object_reduced` desde Twig no
  tiene precedente.
- 🔥 **Las colecciones no listan los productos agotados enteros; la búsqueda sí** ✅
  [MC 2026-09-28]. También los devuelven `product_list`, `category.products`,
  `complementary_product_list` y `| get_products`. Y el relleno de `related-products` del tema
  base completa con agotados a propósito (`related_products_without_stock`). En la tienda de
  Uruguay, 7 de 20 resultados de una búsqueda estaban agotados.
- ✅ **El filtro de color de la plataforma ya excluye el color agotado**: `?Color=Army` no trae
  productos cuyo Army está en 0. Y un producto con todo el stock en 0 no se lista en las
  colecciones (0 de 302) [MC 2026-09-11].
- Cómo filtrar en el tema sin esconder de más (fail-open, filtrar la lista antes del loop) está
  en [Patrones](14-patrones.md). Por qué no se puede saber barato si un producto ajeno está
  disponible, en [Límites y Admin API](13-limites-y-admin-api.md).

## Fotos

- 🔥 **`featured_image` NUNCA es `null`** ✅ [MC 2026-09-21]. Sin foto, la plataforma devuelve
  su placeholder `no-photo` de 1×1, servido desde `/assets/stores/img/`, así que
  `{% if not product.featured_image %}` no atrapa ningún caso. La detección usa dos señales: la
  ruta completa `/assets/stores/img/no-photo` (no la palabra suelta, porque el comerciante
  puede subir un `no-photo-algo.jpg`) o las dimensiones 1×1. Se combinan de forma que ante la
  duda la card se dibuje:

  ```twig
  {% set has_photo = photo and '/assets/stores/img/no-photo' not in url
     and not (photo.dimensions['width'] == 1 and photo.dimensions['height'] == 1) %}
  ```

- ✅ **Otra señal del mismo placeholder: `product.featured_image.id ?? 0` da 0**, mientras que
  `images_count` no da 0 [GG 2026-09-25].
- 🔥 **`variant.image` nunca viene vacío**: a una variante sin foto propia le devuelve la
  principal ✅ [GG 2026-09-24].
- ✅ **Cada variante tiene UNA sola imagen relacionada (`variant.image`)** [MC 2026-08-25]. Los
  `product.images[].alt` que genera la plataforma son SEO automático, con sufijos que rotan
  ("… - comprar online", "… en internet"), y **nunca traen el color**. El que sí lo trae es
  `variant.image.alt` ("Buzo X (S, Blanco)"). Un carrusel de fotos por color solo funciona con
  alts escritos a mano desde el Admin. La convención de alt que usó GG está en
  [Patrones](14-patrones.md).
- ⚠️ **`option.custom_data` trae el hex que el comerciante le puso a la opción en el Admin.** La
  plataforma tiene además su propio diccionario de colores, en
  `product_filter.values[].color_hexa` (cuando `color_type == 'insta_color'`). Pero ese existe
  solo en colección y búsqueda, no cubre todos los nombres (12 de 14 en MC) y son colores web
  genéricos: sirve para sembrar un diccionario propio, no como fuente [MC].
- Cómo emite `snippets/image.tpl` las dimensiones y por qué el CDN da 403 sin referer, en
  [Lo que la plataforma inyecta](08-plataforma.md).

## Card de producto

### El carrusel de fotos de la card

- ✅ **Cómo lee el DOM `initializeProductItemSlider`** (bundle `linkedstore-v2`)
  [MC 2026-09-18]:
  - lee `data-initial-slides`, `data-images-count` y los `index` de `data-append-images`;
  - clona el `<img>` del **último** slide para armar los que agrega, así que un slide de video
    tiene que ir primero, y esos atributos hay que corregirlos a mano;
  - `item-slider.tpl` itera `product.images`, que no incluye los videos;
  - el carrusel de la card solo existe en `template == 'category'` o `'search'`
    (`show_image_slider` en `item.tpl`).
- ⚠️ **El bundle usa Swiper 5** (clases `swiper-container-*`), y la guarda de inicialización es
  `hasAttribute("data-slider-observed") || observe()` [MC 2026-09-10]. Las cards se
  inicializan por scroll: recién cargada la página, `el.swiper` es `undefined`.
- ⚠️ **`data-item-slider-id` tiene que ser único por card.** `initializeProductItemSlider` lo
  usa como clave de `window.itemProductSliders` y lo concatena en los selectores de flechas y
  paginación. Con ids repetidos se inicializa una sola card, y las flechas de la segunda mueven
  la primera [MC].
- ⚠️ **`LS.productItemSlider`** [MC]:
  - arma el carrusel con `slidesPerView: 1`, `spaceBetween: 0` y sin loop, así que el
    translate es `−índice × ancho`;
  - no acepta opciones de Swiper, solo `pagination_type` (no se puede pasar `roundLengths`);
  - los bullets `-dynamic` reciben `style="left: …"` inline: hay que ponerles
    `position: static` y sumar una clase para ganar especificidad.
- ⚠️ **`LS.productItemSlider` pelea con la imagen de hover** [MC]. Si hay un
  `.js-product-item-secondary-image-private` en desktop, borra el segundo slide (y las flechas,
  si el producto tiene 2 fotos). Si la imagen secundaria no existe pero queda la clase
  `js-product-item-private-with-secondary-images`, igual agrega
  `product-item-secondary-images-loaded`, y la card queda **en blanco al hacer hover**. La clase
  y la imagen se sacan juntas.
- Por qué Swiper deja asomar la foto siguiente al cambiar de columnas (escribe el ancho inline),
  en [JavaScript](11-javascript.md).

### Nombre, precio y badges de la card

- ⚠️ **La plataforma no reescribe `.js-item-name` de la card al cambiar de variante**; el del
  quickshop, sí [MC].
- ⚠️ **La badge de descuento se renderiza SIEMPRE, oculta.** Lleva los hooks `js-offer-label` y
  `js-offer-percentage`: si solo se dibuja cuando hay oferta, al elegir una variante en oferta
  no aparece nunca [MC]. En el carrito va **adentro** de `cart-compare-price-container`, que es
  lo que la plataforma muestra y esconde; afuera se quedaba un "-20%" viejo.
- ⚠️ **El JS privado escribe `display` inline sobre el badge "sin stock" de la card.** Se esconde
  el contenedor o no se renderiza [MC].
- Sanear el HTML de una card para reusarlo, el quick add que reusa el form oculto y los links
  dentro del `<a>` de la card están en [JavaScript](11-javascript.md) y en
  [Patrones](14-patrones.md).

## Ficha de producto

### Precio, descuento y cuotas

- 🔥 **Los hooks de descuento son inconsistentes** [MC]. `changeVariant` hace
  `find('.js-offer-label')` (plural: las muestra todas) pero `findOne('.js-offer-percentage')`
  (singular: actualiza solo la primera). Si se duplica la badge de `item-badges.tpl` en la ficha,
  salen dos badges con porcentajes distintos. Encima, las dos plantillas lo calculan distinto:
  `item-badges.tpl` usa `product.promotional_price_percentage`, que incluye las promociones, y
  `product-form.tpl` usa `(compare_at_price - price) / compare_at_price`. En la ficha, los call
  sites pasan `include_discount: false` y queda una sola fuente de verdad. En VZ también se
  encontró que el `store.js` del base solo actualizaba el primer `.js-offer-percentage` [VZ].
- 🔥 **Un precio comparativo MENOR que el de venta rompe tres renders del tema base** [MC]:
  - aparece "0% OFF", porque `| round` de un valor indefinido da 0;
  - aparece "--14%", porque el porcentaje negativo es truthy y el markup le suma un `-` fijo;
  - el comparativo sale tachado arriba del precio.

  La solución es un único criterio: está en oferta solo si el comparativo es **mayor** que el
  precio. Va en `has_price_discount`, en `discount_percentage_value > 0` y en el
  `hasRealDiscount` de `changeVariant`, en Twig y en JS por igual.
- ⚠️ **En el tema base, `is-on-sale` lo ponía solo el JS.** Un producto en oferta cargaba con el
  precio en negro hasta que se tocaba una variante. Se pone desde Twig [MC].
- ⚠️ **`installments.tpl` esconde las cuotas en Argentina si la tienda no tiene cuotas sin
  interés.** Las cards quedan 20 o 21px más bajas que el diseño: es un dato del Admin, no un
  bug [VZ].
- ⚠️ **El copy "Hasta N cuotas" no sale de `product.get_max_installments` de forma coherente**
  con la línea de cuotas; en MC se hizo configurable [MC]. Cómo reemplazar el componente de
  cuotas nativo sin esconderlo está en [Patrones](14-patrones.md).
- ⚠️ **El JS privado escribe `display` inline sobre `#btn-installments`** [MC].

### El formulario de producto es contrato

- ⚠️ **`#product-shipping-container` es un id único.** Si hay que moverlo, se mueve el wrapper
  completo [GG] [VZ].
- ⚠️ **`changeVariant()` busca dentro de `#single-product` y pisa cualquier `.js-price-display`
  que haya adentro**, incluidas las cards de un cross-sell dentro de la ficha [VZ].
- ⚠️ **`initAddToCart()` toma el PRIMER `.js-addtocart`, y busca `input[type=submit].js-addtocart`.**
  No lo cambies por un `<button>`. Un cross-sell con su propio botón va después del bloque de
  compra y por el camino `js-cross-selling-*` [GG] [VZ]. Al CTA del checkout, en cambio, sí se
  lo puede pasar a `<button>` (ver "Checkout y cupón", más abajo).
- ⚠️ **El placeholder "Agregando…" recibe inline el ancho del botón más 20px** y desborda si el
  botón está en una fila. Se resuelve con `!important` [VZ].
- `product-form.tpl` también lo usan `featured-product` y el quickshop, que no pasan tus
  parámetros nuevos: cómo agregarlos sin romperlos, en [Patrones](14-patrones.md).

### Envío en la ficha

- ⚠️ **Con solo el medio de envío "A convenir", `store.has_shipping` da falso y el calculador no
  aparece.** Se diagnostica con `POST /envio/` (`cep`, `variant_id`, `quantity`) [VZ].
- ⚠️ **La barra de envío gratis en la ficha**: `.js-fulfillment-info` se esconde con el carrito
  vacío, así que ahí va `force_visible: true`. Y `LS` solo completa el monto "te faltan $X"
  cerca del umbral y con decimales: lo calcula el tema [GG].

### Video de producto (Cloudflare Stream)

- 🔥 **El video de la galería tiene cinco trampas juntas** ✅ [MC 2026-09-16]:
  - el tema base le da una caja 16:9 a todo el ancho;
  - el `data-src` trae `autoplay=true` pero le falta `muted`, y sin `muted` no arranca;
  - `setupNativeVideoPlayers` le saca `autoplay` al `allow` al tocar play;
  - `media.render` emite inline el `padding-top: 177.77%` y el `width`, `height` y `top` del
    iframe, y el JS le saca `.embed-responsive-16by9` al dar play;
  - la copia para fancybox, `.js-product-video-modal`, también lleva la clase
    `.product-video`. Sin selectores por hijo directo se reproduce un **segundo video
    invisible, que se factura**.
- ✅ **`object-fit` sobre un iframe no hace nada** [MC 2026-09-18]. Para un "cover" se
  dimensiona la caja del iframe con la relación del archivo (`media.dimensions`), con
  `min-width` y `min-height` al 100%, centrada con translate y recortada por el contenedor. Un
  iframe adentro de un `<a>` se come el click: `pointer-events: none`.
- ⚠️ **Stream factura por minuto entregado** [MC 2026-09-16]: el `src` queda vacío hasta que el
  video entra en pantalla, se hace `pause()` al salir, y eso se repite en el `afterLoaded` del
  scroll infinito. `letterboxColor` va con un color concreto: `transparent` no sirve.
- El orden en que se leen `media.next_video` y `media.uid`, y que un video no expone ningún
  texto, están en [Twig](07-twig.md).
- ⚠️ **Los embeds de YouTube y Vimeo de las sections los manejan `initVideoBlocks` y los hooks
  `js-video-block` del tema base.** Le escriben el `src` a la miniatura (resolviendo Vimeo por
  oEmbed), así que el `<img>` tiene que existir siempre, con el gif de 1×1 [MC]. Qué guarda un
  setting `video_url`, en [Schema y traducciones](06-schema-y-traducciones.md).

## Carrito

### Qué re-renderiza la plataforma por AJAX y qué no

- ⚠️ **`snippets/cart/_cart-item.tpl` tiene el prefijo underscore a propósito**: el backend lo
  busca con ese nombre exacto para re-renderizar la lista por AJAX. No se renombra ni se le
  sacan los hooks `js-` [MC, antes de 2026-09-03].
- ⚠️ **Al agregar por AJAX, la plataforma reemplaza `.js-ajax-cart-list`.** Cualquier bloque del
  drawer que viva afuera (el contador del título, los sugeridos, la bolsa de regalo) se queda
  con el render inicial hasta la próxima navegación. Se resuelve con un `MutationObserver` o
  re-pidiendo la página y extrayendo el bloque (ver [JavaScript](11-javascript.md))
  [MC, antes de 2026-09-03].
- 🔥 **También re-renderiza los TOTALES, y con otro anidado** ✅ [MC 2026-08-27]. Una regla que
  esconde por hijo directo (`>`) deja de matchear y se cuelan filas. Va una segunda pasada que
  nombra las filas por clase, a cualquier profundidad.
- ⚠️ **El ítem re-renderizado puede venir sin `item.product.variations`.** Todo lo que dependa de
  eso, como la muestra de color, necesita un respaldo [MC].
- ⚠️ **`js-visible-on-cart-filled` es el hook con el que la plataforma revela bloques cuando el
  carrito se llena por AJAX, pero solo si el elemento ya está en el DOM.** Un bloque detrás de
  `{% if cart.items %}` no aparece hasta recargar [MC, antes de 2026-09-03].
- ⚠️ **`.js-empty-ajax-cart` es el contenedor del carrito vacío que la plataforma muestra u
  oculta**, escribiéndole `display` inline. Su markup se renderiza siempre [MC] [GG].
- ✅ **La URL del carrito es `/comprar/`, no `/carrito/`** [GG 2026-09-23].
- ⚠️ **En `/comprar/`, quitar el último producto recarga la página**, y el estado abierto del
  cupón lo maneja la plataforma en la sesión [VZ].

### Los totales

- 🔥 **Las filas de `cart-totals.tpl` NO se sacan del DOM** ✅ [MC 2026-08-27]. Total, precio sin
  impuestos, promociones, descuento del cupón, costo de envío, cuotas: son los hooks que el JS
  privado actualiza y con los que calcula el total, y sacarlos rompe el carrito en silencio. Se
  ocultan por CSS con una regla en negativo, para que una fila nueva del tema base aparezca
  oculta en vez de colarse:

  ```css
  .cart-subtotals-container > *:not(.cart-totals-subtotal) { display: none }
  ```

- ⚠️ **`js-free-shipping-achieved` es la marca que Twig escribe en la fila del total cuando
  `cart.free_shipping.cart_has_free_shipping`.** Se alcanza con `:has()` desde el ancestro común.
  La clase `cart-totals-promotions` la llevan tanto el contenedor como las filas de cupón:
  cuidado con `:last-child` [MC 2026-08-27].
- ⚠️ **El global `shipping_calculator_cart_page` tiene que quedar prendido aunque la calculadora
  se esconda**: es lo que hace existir la fila "Envío" del desglose [MC].
- ⚠️ **Un producto a $0 tiene `display_price` en falso** (la plataforma lo trata como "consultar
  precio"), así que filtrar por `display_price` descarta justo los productos de regalo.
  `item.is_gift` es solo el regalo por umbral que agrega la plataforma: un producto a $0 no es
  `is_gift` [MC].

### Envío gratis y regalos

- ⚠️ **Los tres wordings de la barra de envío gratis** (`.success`, `.amount` y `.condition`)
  nacen con `display: none` hasta que corre el JS privado. Conviene un respaldo en CSS [MC].
- ✅ **`LS.freeShippingProgress` llena `.js-ship-free-dif` solo en la rama `.amount`**, cuando lo
  que falta es como mucho el 50% del subtotal. En `.condition`, el monto queda vacío
  [MC 2026-08-28].
- ⚠️ **Más detalles de la barra** [MC]:
  - su `animateTo` es una cadena de `setTimeout` que lee `style.width`, así que el elemento no se
    puede compartir con otro progreso;
  - `LS.updateFreeShippingBar` escribe `display` inline con jQuery;
  - `visibility_condition: has_free_shipping_bar_available` la esconde cuando
    `cart.free_shipping.min_price_free_shipping.min_price_raw` es 0. Es falta de configuración de
    la tienda, no un bug. Test de consola:
    `getComputedStyle(document.querySelector('.js-ship-free-rest')).display`.
- 🔥 **`gift-promotion-progress.tpl` se dibuja apenas la tienda tiene una promoción de regalo en
  el Admin** (`store.get_gift_promotion_progress()`), sin ninguna setting del tema, y trae el
  `.box` gris y el rojo de acento ✅ [MC 2026-08-27]. Rompía el pie del drawer. Conviene ponerlo
  detrás de un toggle y estilarlo, sin borrar el include.

### Los modales de la plataforma al agregar al carrito

- ⚠️ **Al agregar, la plataforma puede abrir sus propios modales** (`#js-cross-selling-modal`,
  `#related-products-notification`) según lo que el comerciante haya configurado en el Admin.
  Se apagan desde el tema si el diseño ya ofrece esos productos [MC, antes de 2026-09-03].
- ✅ **Apagarlos cambia qué otra notificación aparece** [MC 2026-08-28]. La plataforma mostraba
  el toast en vez del drawer justamente porque había cross-selling
  (`cartOpenType === 'show_cart' && !shouldShowCrossSellingModal`). Sin esos modales manda el
  `cart_open_type` del Admin; si se prefiere el toast, se cambia ahí.

### El drawer: `modal.tpl`

- ⚠️ **`dock_desktop` va con el string `'right'` o `'left'`, no con `true`** [MC]. Con `true` la
  clase sale `modal-md-docked-`, sin lado, y en desktop el drawer aparece de golpe. Además, el
  `right: -100%` del tema anima sobre todo el ancho de la ventana: el drawer se mueve con un
  `translateX` propio.
- ⚠️ **Con `form: true`, `modal.tpl` envuelve **todo** el contenido en el `<form>` del carrito.** Los
  forms de alta tienen que vivir afuera (ver [Patrones](14-patrones.md)). Sin un
  `js-modal-close-private` el modal no se cierra, y el parámetro `custom_header` reemplaza la
  fila de título y cierre por un `{% block modal_head %}` [MC].

### Checkout y cupón

- ⚠️ **Para el CTA del checkout, la plataforma mira `name="go_to_checkout"` e
  `id="go-to-checkout"`.** El `value` del `<input>` es solo el rótulo, así que se lo puede pasar
  a `<button type="submit">` (por ejemplo, para meter un ícono) manteniendo esos dos atributos
  [MC]. Un cambio arriesgado en el camino al checkout va detrás de un toggle que vuelve al markup
  del base (ver [Patrones](14-patrones.md)).
- ⚠️ **El JS privado le escribe `display: none` inline a `.js-coupon-body` por esa sola clase**:
  lo trata como un acordeón aunque el markup no lleve `js-accordion-private-content` [MC].

### ❓ Cuántos slots del nubesdk hay en el carrito (y cómo re-medirlo)

El handoff de MC contó 7 `js-nubesdk-slot` en el carrito drawer [MC, antes de 2026-09-03]; una
nota posterior del mismo proyecto cuenta 4 [MC]. Puede depender de la versión de Ipanema o de
las apps instaladas. Para re-medirlo: con el drawer abierto en la preview, contar con
chrome-devtools los `.js-nubesdk-slot` que haya adentro del panel, y anotar la versión del tema
y las apps de la tienda. La regla para ocultarlos no cambia (`:not(:has(*))`, ver
[Lo que la plataforma inyecta](08-plataforma.md)).

## Búsqueda

- ✅ **El buscador encuentra por SKU, pero solo con el código COMPLETO y exacto**
  [MC, antes de 2026-09-03]. Medido con SKUs reales: el completo devuelve 1 resultado (sin
  distinguir mayúsculas); cualquier prefijo o parcial devuelve 0. Mientras el comprador tipea, el
  drawer se ve vacío hasta el último carácter.
- ✅ **La búsqueda devuelve productos REPETIDOS entre páginas**: 4 en común entre la página 1 y la
  2 con `limit=20`. Es el orden por relevancia, así que el scroll infinito dibuja duplicados. En
  la colección no pasa [MC 2026-09-18].
- ⚠️ **El motor no encuentra por nombre de categoría**: una búsqueda por el nombre exacto de una
  categoría existente dio 0 resultados [MC]. Lo que el buscador ignora (palabras de más, `?q=` en
  una categoría) está en [Límites y Admin API](13-limites-y-admin-api.md).
- ✅ **El buscador indexa las etiquetas del producto por palabra completa**: un prefijo común en
  las etiquetas (como `order-`) le trae medio catálogo a quien busque "order" [MC 2026-09-14].
- 🚫 **Las sugerencias del buscador las inyecta la plataforma** en `.js-search-form-suggestions`,
  enganchándose a `js-search-form` y `js-search-input`, y no admiten muestras de color. Un panel
  de búsqueda propio no puede llevar esos hooks [GG].
- ⚠️ **El buscador base no tiene estado "sin resultados".** `initSearchTrigger` pone
  `search-drawer-empty`, pero no hay CSS ni markup detrás [MC].
- ✅ **Las cards del buscador pierden la relación de aspecto** [MC 2026-08-28]. Como el render de
  `?snipplet=` corre sin `product_aspect_ratio`, `item-image.tpl` escribe el `padding-bottom` del
  alto real de cada foto: en la misma fila salían cards de 349, 256 y 234px. El arreglo:
  - resolver la relación en el drawer con el mismo mapa de `item-image.tpl`
    (`{square: 100, horizontal: 75, vertical: 133.333, portrait: 150}`);
  - emitir `--search-card-ratio` y una clase en un ancestro del HTML que llega por AJAX;
  - sumar el gancho `.product-item-image-ratio` a `item-image.tpl`, con `!important` y
    `object-fit: cover`.
- ⚠️ **`products_count` lo da el servidor.** Si el tema filtra (agotados, sin foto), "Mostrando N
  resultados" puede quedar por encima de lo que se dibuja, y el lote del scroll infinito puede
  traer menos de 20. Es inherente a filtrar en el tema [MC].
- ✅ **El `search.json` del tema base usa `page-header` más la barra lateral de filtros**
  [MC 2026-09-18]. En MC se lo unificó con la colección sumando `search` al `enabled_on` de la
  toolbar, con el título armado desde `query`. Llamar a `category.subcategories(false)` en la
  búsqueda vacía la section (ver [Twig](07-twig.md)).

## Colecciones y filtros

- ⚠️ **`category.products` trae SOLO los productos directos** [MC, antes de 2026-09-03]. Una
  colección devolvió 6 por ahí mientras su contador decía 16, que incluye a las hijas. Una
  categoría madre, justo la que un comerciante elegiría, muestra dos o tres productos sueltos si
  no se completa con las subcategorías (el patrón está en [Patrones](14-patrones.md)).
- ⚠️ **`category.products` también topea en 12**, igual que `product_list` [MC 2026-09-08]. La
  ausencia de un producto en la lista solo prueba algo si la lista trae menos de 12.
- ⚠️ **`categories` trae solo el primer nivel.** El segundo se saca con `subcategories(false)`, y
  una categoría de tercer nivel (Mujer › Accesorios › Bolsas) exige recorrer tres [MC].
- ⚠️ **Las colecciones automáticas (Destacados, Novedades, Ofertas: `primary`, `new`, `sale`) no
  están en el árbol de `categories`.** Un camino que busca por id crudo no las encuentra, y como
  no tienen página, tampoco hay "ver todos" [MC].
- ✅ **Una categoría ordenada por "más vendidos" no respeta ningún orden manual**; se prueba con
  `?sort_by=user`. Y `/productos/` resuelve `category.id = 0` [MC 2026-09-14]. Lo que la Admin API
  no deja hacer con el orden, en [Límites y Admin API](13-limites-y-admin-api.md).
- ✅ **Los filtros aplicados** [MC 2026-08-25]: `product_filter.values[].selected` trae los valores
  elegidos ya resueltos por el servidor, y `product_filter.key` es el nombre de la variación. El
  valor del filtro llega **normalizado a Title case** ("Negro"), mientras `option.name` llega tal
  cual está en el Admin ("NEGRO"): se compara con `| trim | lower`.
- ✅ **El drawer de filtros borra solo sus propias claves, reordena los valores alfabéticamente, y
  el navegador manda `%7C` en vez de `|`.** Para saber qué está activo, se compara como conjunto
  y como subconjunto, no como string [MC 2026-09-15].
- 🔥 **Con 0 resultados, la guarda `products and has_filters_enabled` sacaba el drawer de
  filtros**, y el visitante quedaba atrapado sin poder desfiltrar ✅ [MC 2026-09-17]. La condición
  pasa a ser `(products or has_applied_filters)`.
- El contrato para armar a mano la URL de filtros y las trampas de `LS.getUrlParams` y
  `LS.paramsToUrl`, en [JavaScript](11-javascript.md).
