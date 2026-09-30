# JavaScript: `store.js`, la API `LS` y Swiper

El JS de un tema Ipanema convive con el de la plataforma: el bundle `linkedstore-v2` (la API
`LS`, los formularios, el carrito por AJAX, los carruseles de las cards) corre en la misma página
y escucha en el mismo `document`. Casi todos los bugs caros de JS salieron de pisarse con él. Este
capítulo junta lo que se aprendió sobre esa convivencia, sobre Swiper y sobre performance.

Cómo medir en la tienda con chrome-devtools (y por qué no armar un harness local) está en
[verificación y QA](15-verificacion-y-qa.md). Lo que el JS privado hace con la card, el carrito y
los formularios está en [producto, carrito y búsqueda](09-producto-carrito-busqueda.md) y en
[plataforma](08-plataforma.md).

## Lo esencial

- **`LS` es global y no tiene documentación completa.** Sus eventos disparan también en la carga
  inicial (hay que filtrar por `event.isTrusted`), y `LS.formatToCurrency` espera unidades mientras
  el DOM trae centavos.
- 🔥 **Swiper escribe el ancho de cada slide inline.** El `update()` diferido con dos rAF no alcanza
  al cambiar de layout: hay que escribir ancho y posición de forma sincrónica y en lote.
- 🔥 **`LS.getUrlParams()` no convierte `+` en espacio,** y el título de búsqueda pasa a decir
  `remera+daria`. Se arregla con un script inline en el `<head>`, antes que el bundle.
- **Reusar el camino del tema en vez de reimplementarlo:** el quick add setea el `<select>` oculto
  que ya trae la card y clickea su botón.
- **Lo que la plataforma no re-renderiza se refresca a mano:** `MutationObserver` sobre lo que ella
  sí escribe, o re-pedir la página y extraer el bloque.
- **Para un render oculto, `<template>` y no `display: none`:** lo oculto sigue alcanzable y los
  inits lo marcan.
- **Performance:** `product-image.tpl` no pasa `sizes` y el costo de `{% paginate %}` es lineal por
  producto. Los dos se miden antes de tocar.

## `store.js` y las librerías

`static/js/store.js` es **vanilla JS**, organizado en decenas de funciones `initXxx()` llamadas
desde un init general. No hay build step. Además están `libraries.js.tpl` y
`libraries-standalone.js` (swiper, fancybox, lazysizes). El tamaño depende del proyecto y crece con
él: en MC pasó de ~7.600 a 9.623 líneas; en GG, de 3.752 a 5.086. [MC] [GG]

- ⚠️ **No cuelgues una función independiente adentro de un `init` que corta temprano.** En MC,
  `paintSwatch` vivía dentro de `initProductPurchaseBar` y no corría con la barra apagada. [MC]
- ⚠️ **Cuando JS y Twig calculan la misma clave, los reemplazos tienen que ser idénticos, uno a
  uno.** Si el `colorHandle` de JS y la cadena de `| replace` de `item.tpl` divergen, la card y la
  ficha eligen fotos distintas para el mismo color. [MC]
- **Separá conmutar el estado de publicar la medida.** Un
  `if (next === floating) return` impedía actualizar el alto de la barra. Publicá la medida en cada
  sync, de forma idempotente y con caché. [MC 2026-09-07]
- **Métricas compartidas en `:root`** (`--gg-header-*`), sin un segundo listener de scroll: el que
  ya existe publica y los demás leen la variable. [GG]

## La API `LS` de la plataforma

Global, sin documentación completa. Lo que apareció en los proyectos:

| | |
|---|---|
| `LS.changeVariant` | cambia la variante; el tema engancha con `LS.registerOnChangeVariant` |
| `LS.search` | pega a `/search/?q=…&limit=…&snipplet=search-results.tpl` |
| `LS.urlAddParam`, `LS.paramsToUrl`, `LS.getUrlParams` | armado y lectura de URLs de filtros (ver abajo) |
| `LS.formatToCurrency` | ⚠️ espera **unidades**; los `data-priceraw` / `data-pricemin` del DOM vienen en **centavos** |
| `LS.newsletter`, `LS.homePopup`, `LS.freeShippingProgress`, `LS.productItemSlider` | helpers que a veces conviene reemplazar |

### Variantes

- ⚠️ **`LS.registerOnChangeVariant` dispara también en la resolución inicial de la página,** con
  `change` sintéticos sobre los selects. Un flag de "hubo interacción" a secas se prende solo: hay
  que filtrar por `event.isTrusted`. [MC]
- ⚠️ **`LS.changeVariant` no dispara en la ficha de producto al cargar** (en la grilla sí). Si algo
  tiene que resolverse con la variante inicial (por ejemplo, entrar con `?variant=<id>`), se lee
  del DOM (`data-variants`, en [producto](09-producto-carrito-busqueda.md)) o de Twig
  (`product.default_options`, en [Twig](07-twig.md)). [MC]
- ⚠️ **`LS` recalcula la variante leyendo todos los selects en cada `change`.** Al setear dos (color y
  talle), el color va primero y el último `change` tiene que encontrar la selección completa. Las
  opciones se buscan por `data-variation-id`, no "el primer select". Para saber si una variante
  cubre las opciones, se compara contra `option0/1/2` sin mirar la posición: los ids de opción son
  únicos en toda la tienda (y son el nombre de la opción, ver [Twig](07-twig.md)). [MC]

### Precios y montos

- ✅ **Formato de montos en JS:** `toFixed(2)` **antes** de `toLocaleString` (con
  `minimumFractionDigits: 2` el máximo queda en 3 y sale "9.666,667"), y después se sacan los `,00`,
  porque el `| money` de Twig los omite. Si no, la línea pasa de `$12.250` a `$12.250,00` al cambiar
  de variante. [MC 2026-09-16]
- ⚠️ **`LS.formatToCurrency` agrega un espacio** después del símbolo ("$ 11.714,88"). [VZ 2026-09-24]
- ⚠️ **El `data-product-price` que escribe el cambio de variante pierde un punto de miles.** Para
  calcular sobre el precio vigente, leé el texto de `.js-price-display`. [VZ 2026-09-24]
- **Cuotas propias en JS:** el monto es `variant.price_number / N`, junto a la actualización del
  precio, y la visibilidad se sincroniza con `installmentsToUse[0] <= 1`, que es el criterio del
  componente nativo. [MC 2026-09-16]

### 🔥 `LS.homePopup` escribe su cookie al cargar, no al mostrar

El `setTimeout` que muestra el popup y el `cookieService.set` están en el mismo tick: si el
visitante navega antes de que venza la demora, la cookie ya está escrita y **el popup queda
bloqueado todo el período sin haberse visto una sola vez**. En MC se resolvió sacando el helper y
manejando el timeout y la cookie en el tema (escribiéndola **después** de abrir), pero siguiendo
emitiendo el `CustomEvent` `homePopup.released`, que algunas apps escuchan. [MC]

Cuándo no sale el popup (iframes, la página de contraseña) está en [plataforma](08-plataforma.md).

### URLs de búsqueda y filtros

- 🔥 **`LS.getUrlParams()` hace `decodeURIComponent` y no convierte `+` en espacio.** Al volver a
  encodear queda `%2B`, y el título de la búsqueda dice "remera+daria" apenas el visitante filtra o
  scrollea. En Twig no tiene arreglo (ahí ya no se distingue `c++`), y tiene que ir **inline en el
  `<head>`**, porque el bundle lee la querystring antes que `store.js`: [MC 2026-09-18]

  ```js
  var s = location.search; if (!s || s.indexOf('+') < 0) return;
  var n = s.slice(1).split('&').map(function (p) { var e = p.indexOf('=');
    return e < 0 ? p : p.slice(0, e + 1) + p.slice(e + 1).replace(/\+/g, '%20'); }).join('&');
  history.replaceState(history.state, '', location.pathname + '?' + n + location.hash);
  ```

- ⚠️ **`LS.paramsToUrl` descarta `results_only`, `page` y `limit`, pero no `mpage`** (el parámetro
  con el que la plataforma restaura los lotes del scroll infinito), y el drawer de filtros tampoco lo
  borra. Filtrar después de haber scrolleado restaura N lotes de más: medido con `mpage=3`, 2 pedidos
  extra, 167 KB y 2,5s, y `mpage` crece con el scroll. No rompe nada visible (los lotes llevan el
  filtro): es un costo. En MC quedó pendiente. [MC]
- **El contrato para armar a mano una URL de filtros:** un parámetro por clave, con los valores
  unidos por `|` y ordenados; `min_price`, `max_price` y `sort_by` sueltos; las subcategorías son
  páginas, no valores de filtro. Cómo se comporta el drawer de filtros de la plataforma está en
  [producto, carrito y búsqueda](09-producto-carrito-busqueda.md). [MC]

## Swiper

### Las tres trampas del handoff original

1. **`createSwiper` difiere el `new Swiper()` con un `setTimeout(0)`.** Justo después de inicializar
   la galería, `container.swiper` todavía es `undefined`. Cualquier `slideTo` inmediato se pierde en
   silencio: hay que hacerlo también en el callback. [MC]
2. **Al cambiar el layout hay que llamar a `update()`.** Swiper cachea el ancho al inicializarse y
   no se entera solo (no hay resize de ventana de por medio). Con **dos `requestAnimationFrame`**:
   recién en el segundo la grilla ya reflowó con las clases nuevas. ⚠️ Los carruseles de las cards
   **se inicializan por scroll**, así que recién cargada la página `el.swiper` es `undefined` y
   parece que no existieran. **Esto solo no alcanza: ver la trampa siguiente.** [MC]
3. 🐛 **`slidePrev()` se va al primer slide con columnas de ancho fraccionario.** Medido: el
   contenedor mide 334.25, `swiper.size` (de `clientWidth`, entero) da 334, el `snapGrid` queda
   `[0, 334, 668, 1002]` y el translate aplicado es `-335 · -670 · -1005`. `slidePrev()` busca el
   translate en el `snapGrid` con un `indexOf` **exacto**, no lo encuentra y cae a su default
   `prevIndex = 0`. `slideNext()` no se entera porque no consulta el snapGrid. Se arregla
   interceptando el click y haciendo `slideTo(activeIndex - 1)`. ⚠️ **El gesto táctil no está
   afectado:** `onTouchEnd` compara **rangos** contra `slidesGrid`, no por igualdad. [MC]

### 🔥 Swiper escribe el ancho de cada slide inline (corrige la trampa 2)

**Swiper le escribe a cada `.swiper-slide` su ancho en px inline**, y contra un inline no hay CSS que
valga. Al cambiar la vista de columnas de la colección, la card toma su ancho nuevo al instante (es
`grid-template-columns`), pero el slide se queda con el viejo: el slide activo no llena su caja y
por el borde derecho asoma la foto siguiente. [MC 2026-09-16]

✅ Medido en MC, de 4 a 3 columnas: al click, la caja pasa a 448.3 y el slide sigue en `335px`
(asoman 114.3px), y así se queda hasta el segundo rAF, **372ms después**, porque ese frame recalcula
los grids internos de todos los carruseles. No es el parpadeo de un frame. [MC 2026-09-16]

El arreglo:

- **escribir el ancho y la posición (`-índice × ancho`) de forma sincrónica y en lote** antes de
  devolver el control, así el navegador no pinta un frame con la medida vieja. El `update()` sigue
  diferido, porque hace otra cosa y es lo que cuesta caro;
- **primero todas las lecturas y después todas las escrituras.** Un `update()` por carrusel alterna
  lectura y escritura y fuerza un layout por vuelta: con 45 carruseles costaba **329ms**. En lote son
  **10ms**;
- leer el ancho **por card**, porque con filas alternadas conviven dos anchos;
- saltear los carruseles que todavía no se inicializaron.

Descartados por medición: `width: 100% !important` en el slide (se fue a 1005px) y hacer el
`update()` sincrónico (arregla el glitch, pero bloquea el click un tercio de segundo).
[MC 2026-09-16]

### Más sobre Swiper

- **El bundle de la plataforma trae Swiper 5** (clases `swiper-container-*`). [MC 2026-09-10]
- **Esconder slides con `display: none` sí funciona:** al remedir, Swiper saltea los ocultos.
  Pero **nunca uses `order` de CSS en un carrusel activo**: Swiper calcula sus translates por orden
  del DOM y se desincroniza. Para anular Swiper sin desinicializarlo, el patrón está en
  [patrones](14-patrones.md). [MC]
- **Interceptar un click antes que Swiper:** listener en **captura** sobre `document` con
  `stopPropagation`, más `preventDefault` si el botón vive adentro del `<a>` de la card. [MC]
- Cómo el carrusel de la card (`initializeProductItemSlider`, `LS.productItemSlider`) lee el DOM y
  choca con la imagen de hover está en [producto, carrito y búsqueda](09-producto-carrito-busqueda.md).

### `touch-action` va al revés según quién scrollea

| Carrusel | Qué necesita |
|---|---|
| **Swiper** (JS maneja el eje horizontal) | `touch-action: pan-y`, obligatorio: si no, el navegador se queda con el gesto y Swiper recibe los eventos pero nunca traslada |
| **Scroller nativo** (`overflow-x: auto`) | **sin `touch-action`**: un `pan-y` le saca justo el gesto que tiene que atender |

## Carruseles nativos y acordeones

Dos helpers que en MC se extrajeron tarde, después del segundo caso, y que conviene tener desde el
principio. [MC]

- **`bindScroller(track, prev, next)`**, para carruseles nativos: avanza de a una card con
  `scrollBy`, se deshabilita al llegar al borde y pone una clase `is-static` cuando el track no
  desborda. ⚠️ **Necesita un `ResizeObserver`:** si el track arranca dentro de un `display: none` (un
  drawer, una pestaña oculta) mide 0, y las dos flechas quedarían deshabilitadas para siempre.
- ⚠️ **`scrollIntoView` dentro de un track mueve también el scroll de la página.** Para llevar una
  card a la vista, `track.scrollTo({ left })`. [MC]
- **`bindAccordionDetails(details, content)`**, para la transición de alto de un `<details>` con la
  Web Animations API (`height: auto` no es interpolable). Detalles que no son opcionales:
  - al abrir, el `open` se pone **antes** de medir; al cerrar, se saca **después** de animar;
  - hace falta una clase `is-closing`, porque mientras se cierra el atributo `open` sigue puesto (si
    no, la flecha se queda girada);
  - **soltar los handlers antes del `cancel()`**, porque el evento de cancelación no es sincrónico;
  - el hijo de un `<details>` es `content-box` aunque el sitio sea `border-box`: por qué y cómo
    compensarlo está en [CSS](10-css.md) (`::details-content`).
- **Alternativa sin JS de medición:** un acordeón con `grid-template-rows` (de `0fr` a `1fr`) más un
  fundido. Sirve cuando no hace falta el alto exacto frame a frame. [VZ 2026-09-24]

## Header, paneles y medidas

- ⚠️ **Header que se esconde al bajar:** al subir hay que sacar la clase. El `initStickyHeader` del
  base la sacaba recién en `scrollY == originalTop` y dejaba un hueco blanco. En el arreglo de MC,
  `lastScrollY` se actualiza solo al pasar el umbral de 10px, a propósito. [MC 2026-08-26]
- ⚠️ **Ejemplo de MC: un header transparente decidido por lista blanca.** El `initTransparentHeader`
  propio de MC decide con `heroTypes` qué primera section cuenta como hero. Un `slideshow` agregado
  desde el editor no estaba en la lista y el header dejó de ser transparente sin que cambiara el
  código: sumar un tipo de banner nuevo es agregarlo ahí. [MC 2026-09-28]
- ⚠️ **`body:has(.marca)` aplica esté donde esté la section.** Si solo vale cuando es la primera:
  `#MainContent > .ns-section:first-child .marca`. [MC]
- 🔥 **`offsetParent` es siempre `null` en un elemento `position: fixed`** (como `.modal`), así que no
  sirve para saber si un modal está visible. El test correcto es `.modal-visible` o el `display`
  inline. [GG]
- ⚠️ **Abrir un panel en el mismo frame en que se lo mueve a `<body>` mata la transición.** Van dos
  `requestAnimationFrame` antes de poner el estado abierto. [MC]
- **`display: none` no impide un `.click()` programático.** [MC]

## Eventos

- ⚠️ **Un handler de jQuery delegado por `mouseover` no se dispara con
  `dispatchEvent(new MouseEvent('mouseenter'))`.** Hay bugs que solo aparecen con un mouse de
  verdad. [MC]
- **El hover que cambia una imagen consulta `(hover: hover) and (min-width: 768px)` en cada
  evento,** no una vez al enganchar. [MC]
- 🔥 **Con varias cards del mismo producto en la página (una por color), `data-product-id` no
  identifica una card.** Hay que partir del elemento del evento y subir hasta su card. [GG]
- **Validación propia de un formulario de la plataforma:** en fase de captura sobre `window`, antes
  de que corra el `ContactForm`. Lo que ese formulario hace y qué acepta está en
  [plataforma](08-plataforma.md). [VZ 2026-09-24]
- **Para saber de dónde vino un alta al carrito** (por ejemplo, desde adentro del carrito), una
  bandera de módulo que se consume en el callback, con un `setTimeout` de 5s como respaldo. El form
  oculto vive fuera del modal, así que el DOM no lo dice. [MC]

## Reusar el camino del tema

- **Quick add sin reimplementar el alta:** se setea el `<select>` del form oculto que ya trae la card
  y se clickea su `.js-addtocart`. Así corre el camino del tema y de la plataforma, con sus
  validaciones y sus modales. [MC]
- Cuando el tema necesita un dato que la plataforma ya calcula (stock por opción, precio de la
  variante), leelo de donde ella lo escribe antes de recalcularlo. Qué atributos trae cada pieza:
  [producto, carrito y búsqueda](09-producto-carrito-busqueda.md).

## Refrescar lo que la plataforma no re-renderiza

Al agregar por AJAX, la plataforma reemplaza solo ciertas piezas del carrito (el detalle está en
[producto, carrito y búsqueda](09-producto-carrito-busqueda.md)). Todo lo demás se queda con el
render inicial hasta la próxima navegación. Dos salidas:

- **La señal de "cambió el carrito":** un `MutationObserver` sobre las escrituras de la plataforma en
  su barra de envío gratis, y como respaldo otro sobre el badge del header, que cubre la tienda sin
  umbral de envío gratis. [MC]
- ✅ **Re-pedir la página y extraer el bloque.** Detalles que salieron al hacerlo en MC: [MC 2026-08-28]
  - pedir la página **sin** el header `X-Requested-With` (con él, la plataforma puede devolver un
    parcial);
  - debounce de ~400ms;
  - las anclas tienen que existir aunque el bloque salga vacío, y los forms de alta asociados se
    reemplazan junto con el bloque;
  - el guard de re-cableado va sobre el elemento que se reemplaza, no sobre el contenedor fijo;
  - los listeners delegados en el drawer sobreviven;
  - lazysizes 5.2.2 levanta solo las imágenes insertadas, porque tiene su propio `MutationObserver`.

### Cards por AJAX y HTML clonado

- ✅ **Cards pedidas por AJAX en vez de renderizadas en el header.** En VZ, cada card del tema pesa
  ~15 KB; renderizar las del buscador y del menú en el header sumaba ~100 KB por bloque a **cada**
  página. Se piden cuando el panel se abre. [VZ 2026-09-23]
- ⚠️ **Para reusar el HTML de una card ya inicializada, hay que sanearlo:** [MC 2026-09-10]
  - una keep-list de clases `swiper-*`, no una regex;
  - sacar `data-slider-observed` y `data-quick-add-ready`, y vaciar los bullets generados;
  - borrar estilos inline **solo** en los elementos que toca Swiper (el `padding-bottom` de la
    relación de aspecto es inline de Twig y tiene que quedar);
  - el assert correcto es `/translate3d/`, porque los `js-nubesdk-slot` ya traen transforms inline
    desde el servidor.
- ✅ **Para un render oculto, `<template>` y no `display: none`.** Medido en A/B: las imágenes no
  cargan en ninguno de los dos casos, pero lo oculto con `display: none` sigue alcanzable, y los
  inits le escriben marcas (`data-quick-add-ready`) que lo dejan muerto cuando se lo clona. [MC 2026-09-10]
- ⚠️ **`localStorage` topeado por bytes, no por cantidad.** Una card capturada pesa 51 a 96 KB (casi
  todo es el `data-variants`). Y la caché va en claves separadas de la lista, para que llenarla no se
  lleve los datos. [MC 2026-09-10]
- ⚠️ **`response.json()` lleva su propio `catch`.** Un 502 devuelve HTML, y el `SyntaxError`
  terminaría en la pantalla del comprador. [MC]

## SVG y markup que el parser rompe

- ✅ **En un SVG, `el.className` es un `SVGAnimatedString` de solo lectura:** asignarle no hace nada
  y no tira error. Va `setAttribute('class', …)`. [MC 2026-09-10]
- ⚠️ **Un `<use>` clona el símbolo en un shadow tree:** no se le puede cambiar desde afuera el `fill`
  a un path que declara `fill="none"`. Para un ícono con dos estados (corazón vacío y lleno) hacen
  falta dos símbolos. [MC 2026-09-10]
- ⚠️ **`<button>` adentro de `<a>` es HTML inválido y el parser parte la card en dos:** el botón va
  como hermano del `<a>`. Y el `aria-label="{{ product.name }}"` que el tema base pone en el `<a>` de
  la card le borra al lector de pantalla el precio y las cuotas. Links dentro de la card:
  [patrones](14-patrones.md). [MC 2026-09-17]

## Video y mapas

- **Video lazy:** el `src` del video queda en `data-src` y el JS se lo pone al entrar en pantalla,
  reproduciendo solo la capa visible (desktop o mobile) y pausando al salir. Si se inserta contenido
  por JS, se vuelve a llamar al init sobre ese contenedor. Por qué importa con Cloudflare Stream
  (factura por minuto): [producto, carrito y búsqueda](09-producto-carrito-busqueda.md). [VZ 2026-09-24]
- **Google Maps sin Map ID:** `AdvancedMarkerElement` exige un Map ID, así que en VZ los pines son un
  `OverlayView` propio, cargado con `loading=async` + `importLibrary`, y un iframe sin clave como
  respaldo vía `gm_authFailure`. La restricción de la key por host y el manejo de su error están en
  [multi-país, apps e integraciones](16-multipais-apps-integraciones.md). [VZ 2026-09-24]

## Performance

- ✅ **`product-image.tpl` nunca pasa `sizes`,** así que el navegador asume 100vw y baja la copia
  de 1920px. En la galería de MC, 1461 KB bajaron a 224 KB en desktop con el `sizes` correcto.
  `item-image.tpl` tiene `50vw` fijo; con `image_data_sizes: 'auto'` (lazysizes calcula el ancho
  real), 38 de 40 fotos de la grilla bajaron a la copia de 1024. Las dos cosas están igual en VZ.
  [MC 2026-09-17]
- ✅ **El `sizes` fijo de `item-image.tpl` tiene una ventaja:** cambiar la vista de columnas no vuelve
  a bajar imágenes. [MC 2026-09-16]
- ✅ **El costo de `{% paginate by %}` es lineal por producto:** ~0,24s de render y ~8 KB gzip cada
  uno. 60 productos por página fueron 7 MB de HTML y ~15s; 20 son 2,1 MB. En MC el lote de la PLP se
  subió a 60 y se bajó a 20 al día siguiente. [MC 2026-09-15] [MC 2026-09-16]
- Cómo no contaminar la medición de red con Lighthouse, y cómo leer qué imagen bajó de verdad
  (`currentSrc`), está en [verificación y QA](15-verificacion-y-qa.md).
