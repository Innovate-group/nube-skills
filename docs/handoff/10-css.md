# CSS: pelear con el tema base

El CSS de Ipanema son tres hojas grandes que ya definen casi todo. Un estilo propio casi nunca
se escribe sobre una página en blanco: pisa una regla que alguien más escribió con otra
especificidad, en otra hoja y a veces con un `style` inline que pone el JS de la plataforma.
Este capítulo junta lo que eso costó en tres proyectos.

Los tokens del kit (colores, tipografías, espaciados) y cómo se decide qué valor manda están
en [diseño y ui-kit](04-diseno-y-ui-kit.md). Los slots vacíos del nubesdk, que también
rompen gaps, están en [plataforma](08-plataforma.md).

## Lo esencial

- **El orden de carga decide a igual especificidad.** `style-critical.css` y
  `style-utilities.css` van inline en el `<head>` y `style-async.css` carga después: gana la
  que carga última. Antes de pisar una regla, **buscá en qué hoja vive**.
- **Al restilar un componente del base, anulá la regla vieja entera**, no solo lo que querés
  cambiar: `min-width`, `margin` y `opacity` siguen vivos y le ganan a tu `width`. Si el cambio
  es de padding o de tamaño en un `.btn-*`, editá la regla original.
- **Contra un `style` inline que escribe la plataforma no hay especificidad que valga:** ahí
  `!important` es la respuesta correcta, no un parche. Contra un inline de Twig
  (`header.tpl`, `footer.tpl`, el padding de varias sections), pasá el valor a una custom
  property.
- **Ipanema no tiene tablet.** Salta de mobile (≤ 767) al layout de 1440. El rango que falta es
  `@media (min-width: 768px) and (max-width: 1023.98px)`.
- **Un elemento tiene un solo `transform`.** Dos reglas que lo usan se pisan, no se suman. Y se
  anima `transform`, nunca `bottom` (cuenta como CLS).
- **Los márgenes del base se suman al `gap`,** y los hijos vacíos también reclaman su `gap`.
  Se resetea sobre los hijos directos, de una sola vez.
- 🚫 **Nunca resolver layout con márgenes o paddings negativos** (regla del dev), salvo la
  excepción documentada más abajo.

## Las hojas y el orden de carga

| Archivo | Tamaño de ejemplo | Cuándo carga |
|---|---|---|
| `style-critical.css` | ~350 KB en MC, ~115 KB en GG | inline en el `<head>` |
| `style-utilities.css` | ~32 KB | inline, **después** de critical |
| `style-async.css` | ~235 KB | asincrónico (`media="print" onload`) |

Los tamaños cambian con la variante y la versión de Ipanema: medí los de tu instalación.

- ⚠️ **`style-utilities.css` carga después que critical:** con la misma especificidad gana la
  utilidad. `.grid { gap: var(--spacing-base) }` le gana a un `.mi-clase { gap: 8px }`. La
  salida es sumar una clase más al selector, no `!important`. [MC]
- 🔥 **`style-async.css` carga después que las dos.** Un override de igual especificidad escrito
  en critical pierde contra una regla que vive en async. Rompió dos veces en GG antes de que se
  entendiera. [GG] [VZ 2026-09-23]
- ⚠️ **`style-critical.css` tiene un bloque "Async hiders"** que esconde cosas con
  `display: none` hasta que carga async. `.account-form-container` es una de ellas: sacarla del
  markup deja el formulario invisible. [MC]
- **Async hiders propios.** Si el CSS de un contenedor vive en async, conviene arrancarlo con
  `visibility: hidden` desde critical, como hace el base. Así no aparece sin estilo durante la
  carga (`.vz-account`, `.vz-contact`). [VZ 2026-09-24]

## Restilar un componente del base

### 🔥 Anular la regla vieja entera

El tema base define la caja con `min-width`, `margin`, `opacity` y márgenes del contenedor.
Una regla nueva que solo pone `width` y `height` deja todo lo demás vivo.

Caso medido en MC: una muestra de color que tenía que ser 10 × 10 con gap 4 renderizaba
**16 × 10, con 12px de separación y al 80% de opacidad**, porque el tema traía
`min-width: var(--spacing-3)`, `margin-right: var(--spacing-2)` y `opacity: 0.8`. **Un
`min-width` le gana siempre a un `width` menor:** es un mínimo contra un deseado, y no hay
especificidad que lo arregle. [MC 2026-08-25]

⚠️ Y ojo con los tokens: **`--spacing-3` son 16px**, no 12 (`--spacing-3: var(--spacing-base)`).
Medí en el navegador, no deduzcas del nombre. [MC 2026-08-25]

### Clases y reglas propias

- **Un componente propio no reusa las clases del nativo.** Las reglas del tema con más
  especificidad (`.pdp .product-installment`, 0,2,0) le ganan a tu `var(--color)`. Usá un
  prefijo de clase propio. [MC 2026-09-16]
- ⚠️ **Para cambiar el padding o el tipo de `.btn-primary`, editá la regla original.** Un
  override escrito al final le ganaría también a `.btn-small` y a `.btn-medium`, que dependen
  de que la regla base sea la más débil. [VZ 2026-09-23]
- ✅ **El alto de los botones sale del `.btn` del base:** con `line-height: 18px` da 52px
  (17 + 18 + 17). Con `line-height: normal` daría 47. [VZ 2026-09-23]
- ⚠️ **Un `<button>` del tema sale en Arial,** porque el reset no le pone
  `font-family: inherit`. [GG 2026-09-25]
- ⚠️ **Un valor declarado le gana siempre a uno heredado.** Un `color` fijo dejó un ícono
  negro sobre el header transparente, que funciona por
  `var(--header-utilities-foreground, inherit)`. Si una pieza tiene que tomar el color de su
  contexto, no le declares uno. [MC 2026-09-10]

### Remapear los tokens del base

**Redefinir los tokens del base al final de `layouts/resources/style-tokens.tpl` corrige cientos
de reglas sin tocarlas.** En VZ se remapearon `--border-radius: 0`, `--transition-*` con la curva
del kit, `--gutter-container`, `--spacing-section`, `--h1` a `--h6` y los semánticos
(`--success`, `--danger`). Así las piezas del base que no se restilaron igual quedan dentro del
sistema visual. Dónde se documenta cada remapeo y por qué:
[diseño y ui-kit](04-diseno-y-ui-kit.md). [VZ 2026-09-23]

### Tokens que no existen o que no escalan

- ✅ **`--h3-line-height` no existe entre los tokens:** el interlineado cae a `normal` (en MC,
  37 en vez de 30). Y `--h3` salta a la escala de desktop arriba de 768, aunque el contenedor
  mida lo mismo en todos los breakpoints: un drawer de ancho fijo necesita la escala mobile
  explícita. [MC 2026-08-27]
- 🔥 **Un token del comerciante puede dejar un componente esencial inservible.** En GG, el
  comerciante puso `--main-background` en `transparent` desde el editor: los modales quedaron
  transparentes, y además se armaron valores inválidos con `--main-background-opacity-*`. Los
  componentes esenciales (modales, drawers, el carrito) llevan fondo propio. [GG 2026-09-25]

### Resets y reglas del base que muerden

Hay reglas del base que conviene conocer antes de construir encima:

- 🔥 **`style-critical.css` declara `p { font-size: var(--font-base); line-height: 1.375em }`.**
  Todo párrafo de un richtext sale a `--font-base`, no al tamaño de su contenedor. En VZ, un
  párrafo de 19px se dibujaba a 13 (42.9px de alto contra 94). En todo contenedor de texto con
  tamaño propio: [MC] [VZ 2026-09-24]

  ```css
  .mi-richtext p, .mi-richtext li { font-size: inherit; line-height: inherit; }
  ```

- **`.user-content`** devuelve los márgenes del navegador y pone `margin-bottom: 8px` a cada
  `li`. [MC]
- **`.breadcrumbs`** trae `padding: 16px 0` y `opacity: .8`. [MC]
- **`.account-form-container`** (en async) trae `width: 40%` y `margin-bottom`. [MC]
- **`.btn-tertiary`** trae `padding: 14px 28px`, y con `button_tertiary_style: 'underlined'` emite
  `text-decoration` en vez de un borde. [MC]
- **`.grid-1 .product-item`** es una grilla `1fr 1fr`: una card horizontal. [MC]
- **`.product-price-compare`** tiene `width: 100%`. [MC]
- **`.products-grid-empty-message`** va centrado y todo lo demás a la izquierda. [MC]
- ⚠️ **Las utilidades `d-*` de Bootstrap traen `!important`, y `d-md-none` / `d-none d-md-block`
  cortan en 768.** Chocan con cualquier breakpoint propio (860 en VZ y en GG). En piezas nuevas,
  la visibilidad por breakpoint va con clases propias. [MC] [VZ 2026-09-24]
- **Hay reglas "de desktop" sin scope en el base** (por ejemplo sobre `.nav-item`), y
  `.search-container` es `position: relative`. [GG]
- **`.btn-variant-color` no da forma de círculo.** [GG]
- **`.icon-inline` trae `vertical-align: -.125em`,** que descoloca el SVG dentro de un flex. Y
  `.progress-bar-icon` no define ni ancho ni alto. [MC]
- **El tema base topa las fotos en `max-height: 1200px`** en dos lugares. Con una card ancha eso
  achata la imagen y cambia su relación real, sin ningún error. [MC]
- **Un `<a>` sin `href` y un `<select>` con `appearance: none` necesitan `cursor: pointer`.** [MC]

### 🐛 Roto en el tema base

- **`.promotional-modal-image-link` no tiene ninguna regla:** mide 0 × 0 y el link del popup no
  se puede clickear. Pasa igual en VZ. [MC]
- **`.password-section-layout { flex-grow: 1 }` nunca funcionó,** porque su padre `.ns-section` es
  un bloque. Y el `<label for="password">` apunta a un id que no existe. [MC 2026-09-16]
- ✅ **El precio comparativo lleva `opacity: .8`.** Un `#606060` queda en un `#808080` efectivo,
  3,94:1 contra el fondo, por debajo de AA. [MC 2026-09-17]

## Estilos inline: de la plataforma y de Twig

- **Contra un `style` inline que escribe el JS de la plataforma, `!important` es la respuesta
  correcta.** Pasa con el cupón del carrito (`display: none` inline), con la barra de envío
  gratis y con los `padding-bottom` de relación de aspecto que `item-image.tpl` emite inline.
  Qué escribe inline cada pieza está en [producto, carrito y búsqueda](09-producto-carrito-busqueda.md). [MC]
- 🔥 **El `style` inline de `header.tpl` y `footer.tpl` le gana a cualquier media query.** Si un
  valor tiene que cambiar por breakpoint, se pasa a una custom property y el inline solo la
  define. [GG]
- ⚠️ **Varias sections del base escriben el padding inline,** así que no hay override por
  breakpoint posible: se migra a custom properties a medida que se tocan. [MC]
- ⚠️ **Las custom properties que la section emite inline se pisan con `!important`** (se pisa la
  variable, no la propiedad que la usa). Por ejemplo `--pdp-media-width`, que sale de
  `sections/main-product.tpl`: pisando la variable, el cambio vale también en la plantilla
  `split`, donde la info se calcula con `calc(100% - var(...))`. [MC 2026-09-08]
- **`hidden` lo pisa cualquier `display` de autor.** `.mi-clase { display: flex }` anula el
  atributo. Hay que reponerlo: `.mi-clase[hidden] { display: none }`. [MC]

## Tablet (768–1023): el rango que el tema no tiene

✅ **Ipanema salta de mobile (≤ 767) al layout diseñado para 1440, sin nada en el medio.** A 820
(iPad vertical) todas las secciones aplican columnas, splits e insets pensados para el doble de
ancho. El síntoma es siempre "se ve apretado", y en MC hubo dos casos de scroll horizontal.
[MC 2026-09-08]

El rango es **`@media (min-width: 768px) and (max-width: 1023.98px)`**, y tiene precedente: el
tema base ya lo usa en los swipers de testimonios, `carousel-slider` y `banners-slider`
(`768: Math.min(cols, 3)` → `1024: cols`, en `store.js`). Lo que falta es aplicarlo al resto.
Las reglas que salieron de hacerlo en MC:

- ⚠️ **Las reglas van anidadas** dentro del `@media (min-width: 768px)` que ya existe, o con el
  `min-width` explícito. Un `max-width: 1023.98px` suelto se lleva puesto a mobile.
- ⚠️ **`min(var(--cols), 3)` y no un 3 fijo:** si el comerciante configuró 2 columnas, tablet no
  puede mostrar más que desktop.
- ⚠️ **Las variables inline de la section, con `!important`** (ver arriba).
- ⚠️ **No le fijes un porcentaje a una columna `flex: 1 1 0` con gap.** En la ficha, la columna de
  info toma lo que sobra descontando el `column-gap` de 32: fijarle un porcentaje la hace sumar
  100% + gap y mete 32px de scroll horizontal. Medido.
- ⚠️ **El orden dentro del archivo decide.** Casi todos los overrides de tablet tienen la misma
  especificidad que la regla de desktop que pisan, así que van **después**. Puestos antes quedan
  muertos.
- ⚠️ **`initCollectionToolbar` solo conoce dos breakpoints** (desktop y mobile): a este ancho el
  botón de 4 columnas dibuja lo mismo que el de 3. Distinguirlos pide un breakpoint más en el JS,
  no otra regla de CSS.

Verificación: después de cada pieza, confirmar que 1440 y mobile quedaron intactos, pieza por
pieza. El QA de tablet se hace en 820 × 1180 ([verificación y QA](15-verificacion-y-qa.md)).

Si el kit tiene su propio breakpoint (860 en VZ y en GG), convive con el 768 del base: las piezas
nuevas usan el del kit, las del base siguen con el suyo, y la trampa es `d-md-none` (arriba).

## Gap, márgenes y hijos que no se ven

### ⚠️ Los márgenes del tema base se suman al `gap`

Si pasás un contenedor a flex o grid con `gap`, los márgenes que el tema ya les pone a los hijos
no desaparecen: se suman. En la columna de la ficha de MC eso era casi el doble de aire que el
boceto, sin ningún síntoma que lo explicara. En la grilla de productos, un `margin-bottom: 16px`
en `.product-item` se sumaba al `row-gap` y la separación real era 48 en vez de 32. [MC]

Se anula de una sola vez sobre los hijos directos (`.pdp .product-purchase > *`), no persiguiendo
clase por clase. ⚠️ Ese reset conviene que lleve **`min-width: 0`**: un ítem de flex arranca en
`min-width: auto` y no baja de su tamaño mínimo de contenido. [MC]

### Hijos vacíos que igual cuentan

- **En un flex con `gap`, los snippets opcionales se incluyen sin div envoltorio.** Un contenedor
  vacío igual es un hijo y reclama su separación. Si hace falta un ancla, va con
  `display: contents`. [MC]
- ⚠️ **Un slot escondido en flujo normal igual ocupa lugar.** Con foto y video superpuestos, los
  dos van posicionados como capas. Y las reglas del tema que nombran solo `img` (y los
  `:not(:has(img))` de "sin foto") tienen que nombrar también `video` y el embed. [MC 2026-09-11]
- ⚠️ **Dos `<picture>` que se alternan con `d-none` / `d-md-none` sobre el `<img>`:** el escondido
  igual ocupa su lugar y empuja al otro (medido: 485px de hueco). Van absolutos y superpuestos.
  [MC]
- **Separadores como `border-top` del bloque siguiente, no como `border-bottom` del anterior.**
  Cuál es el último visible no se sabe ni desde Twig ni con `:last-child` cuando los bloques son
  hermanos de distinto padre. [MC]
- Los `js-nubesdk-slot` vacíos que la plataforma inyecta en toda section también se llevan su
  `gap`: la regla global está en [plataforma](08-plataforma.md).

### `display: contents` para subir hijos un nivel

Cuando un elemento tiene que participar del flex o grid del abuelo (porque `order` solo reordena
**hermanos**, y un hijo no puede salirse de la celda de su padre), la salida es
`display: contents` en el intermedio. En MC se usó cuatro veces: `.product-content` en la ficha,
`.cart-item-info-container` en el carrito, `.stl-content` en shop-the-look y el slot del
cross-sell. [MC]

- ⚠️ Al volverse `contents`, ese elemento **deja de generar caja y se lleva su `gap`, su `margin` y
  su padding**: hay que reponerlos en el padre o en los hijos.
- ⚠️ Un elemento con `display: contents` **no es alcanzable por `.padre > *`**. Sus hijos son
  ítems de flex a efectos del layout, pero **nietos** en el DOM.
- 🔥 **`display: contents` multiplica el `gap` de los slots vacíos en vez de ahorrarlo:** los hijos
  vacíos del intermedio pasan a ser hijos del flex del abuelo, cada uno con su separación.
  [GG 2026-09-23]

## Flex y grid: medidas que engañan

### ⚠️ `flex: 1 1 0` no da mitad y mitad cuando hay padding

Con `flex-basis: 0` la base es el tamaño **interno** del ítem y el padding se suma encima: la
columna con más padding termina más ancha. Medido en MC: **793 contra 633** en un viewport
de 1425. **`box-sizing: border-box` no lo arregla**, porque ya lo son los dos. [MC]

La forma que funciona es **`flex: 0 0 50%` + `width: 50%`**, que mete el padding adentro del 50%
(verificado en 713/713). **Excepción:** si los dos ítems tienen **exactamente el mismo padding**,
`flex: 1 1 0` sí funciona, porque se desnivelan por igual.

Lo mismo con `grid` contra `flex` en una fila de dos CTA: con flex, el padding es un piso que
`flex-basis: 0` no puede bajar, así que dos botones de distinto padding quedan de distinto ancho.
`grid-template-columns: 1fr 1fr` calcula las columnas sin importar el contenido. [MC]

### Más trampas de flex

- ⚠️ **`flex: 1 1 0` en un flex en columna fija el alto en 0** y el elemento desaparece. [MC]
- ⚠️ **Un hijo con `overflow-x: auto` y `flex-basis: auto` igual suma su ancho de contenido,** y el
  flex envuelve antes de encoger. La salida es `flex: 1 1 0` en ese hijo. [MC]
- ⚠️ **Con `align-items: center` o `flex-start`, los hijos no se estiran:** hace falta
  `width: 100%` explícito. [MC]
- ⚠️ **Un `column-gap` porcentual del tema base sí aplica a flex** (`column-gap: 15%`). [MC]

### Pasar de flex a grid, o de grid a columna

- ⚠️ **Al pasar de flex a grid, `align-items` y `justify-content` siguen vivos.** Reescribilos, y
  fijá la columna con `minmax(0, 1fr)`. Para apilar media y texto, una celda con
  `grid-area: stack` (los dos hijos en la misma área), no `position: absolute`. [MC]
- ⚠️ **Al pasar una caja del base de grid a `flex-direction: column`, reescribí `align-items`.** El
  `center` heredado pasa a centrar en horizontal, los hijos dejan de estirarse y el `ellipsis` se
  queda sin ancho contra el cual recortar. Cómo traducir un `items-start` de Figma está en
  [diseño y ui-kit](04-diseno-y-ui-kit.md). [MC]
- ⚠️ **En una grilla de 1 columna, `span 2` crea una columna implícita** y las cards caen a 65px.
  Usá `grid-column: 1 / -1`. [MC]
- **El ancho de dos columnas lo pone la columna fija:**
  `grid-template-columns: minmax(0, 1fr) var(--panel-width)`, no un porcentaje. [MC]
- **`grid-auto-flow: dense`** para que una card ancha no deje huecos en la grilla. [VZ 2026-09-24]

### 🔥 El `grid-column` negativo del header

El header del base ubica íconos con posiciones negativas: `.head-row.logo-md-center .header-cart`
lleva `grid-column: -2` y `.utilities-language-desktop`, `grid-column: -3`. **`-2` es la última
pista declarada y se recalcula con cada `grid-template-columns`.** En MC, sumar un ícono al header
produjo solapes (la bolsa dibujada encima del ícono de cuenta), y declarar una columna de más dejó
una pista vacía de 40px. **Hay que declarar exactamente las columnas que se usan.** La misma regla
está en VZ. [MC 2026-09-10] [MC 2026-09-14]

- ⚠️ **Un `margin` shorthand pisa al long-hand declarado antes en el mismo bloque.** Salió en el
  mismo arreglo del header. [MC 2026-09-10]

### Container queries

- ✅ **`container-type: inline-size` en la card + `clamp(min, Xcqw, max)`** hace que una pieza (la
  badge) escale con la card y no con el viewport. Tres cuidados: [MC 2026-09-08]
  - acotarlo a donde haya un contenedor, porque sin él `cqw` cae al viewport;
  - envolverlo en `@supports (container-type: inline-size)`, porque un `var()` que sustituye un
    valor inválido deja la propiedad en `unset` y **no cae a la declaración anterior** (Safari ≤ 15);
  - `container-type` convierte a la card en contexto de apilado y en ancestro de posicionamiento.
- ✅ **`cqw` también sostiene el ancho de las cards** cuando al lado de un carrusel se agrega una
  columna fija (el banner fijo del carrusel de productos). [VZ 2026-09-29]

## `aspect-ratio`, porcentajes y medidas

- ✅ **`aspect-ratio` se calcula desde el eje que ya está definido.** Con `align-self: stretch` la
  fila fija el alto, así que calcula el **ancho** y desborda: 387px en una columna de 334. Para
  usarlo como piso: apagarlo y poner un `::before` con `padding-top` en %, en la misma celda
  (`grid-area: stack`). [MC 2026-09-16]
- ⚠️ **`aspect-ratio` sobre una caja con `overflow: hidden` recorta el texto en silencio.** Va en la
  celda. Con `display: grid` en la celda, su único hijo se estira sin `height: 100%`. [MC]
- ⚠️ **Un `%` en `translateX` se resuelve contra el propio elemento; en `left`, contra el
  contenedor.** [MC]
- ⚠️ **`scrollWidth − clientWidth` nunca da 0 con anchos fraccionarios:** para saber si un track
  desborda, compará con `<= 1`. [MC]
- ⚠️ **Un iframe no tiene alto intrínseco.** Necesita una caja posicionada que lo llene o un
  `aspect-ratio` en flujo. Cómo recortar un video embebido está en
  [producto, carrito y búsqueda](09-producto-carrito-busqueda.md). [MC]
- **Un `%` guardado en una custom property se resuelve según la propiedad donde se usa,** no donde
  se declaró: el patrón y el truco del `padding-top` están en [patrones](14-patrones.md).

## `transform` y animación

- 🔥 **Un elemento tiene un solo `transform`.** Dos reglas con `translateY` se pisan, no se suman.
  En MC, el botón de WhatsApp tenía que subir por la barra de compra **y** por otro elemento: hay
  que sumarlos en una sola declaración. [MC 2026-09-17]

  ```css
  transform: translateY(calc(-1 * (var(--pdp-bar-height, 0px) + var(--mc-whatsapp-lift, 0px))));
  ```

- 🔥 **Animar `transform` pisa el centrado que el tema resuelve con `transform`.** Un zoom en hover
  sobre un elemento centrado con `translateX(-50%)` lo descentró: hay que reescribir la cadena
  entera, `translateX(-50%) scale(1.05)`. [GG]
- ✅ **Animá con `transform`, no con `bottom`.** Animar `bottom` es layout: en MC el botón de
  WhatsApp costó 0,0498 de CLS, de los 0,05 que tenía la página ("non-composited animation:
  bottom"). [MC 2026-09-17]
- ✅ **`ResizeObserver` no se entera de un `transform`.** Si una medida visible depende de algo que
  se mueve con transform (el header que se esconde), se sincroniza en el scroll (con rAF) y en
  `transitionend`; hacen falta las dos, porque sin `transitionend` queda la medida de un frame
  intermedio. En MC se publican dos variables, `--header-height` (el alto del bloque) y
  `--header-visible-height` (el borde visible, topeado en 0 si el header no es sticky), con el
  fallback `var(--header-visible-height, var(--header-height, 0px))`. [MC 2026-09-09]
- ✅ **Fundido de slides:** si el slide entero lleva `opacity`, arma su propio contexto de apilado y
  el texto queda debajo del degradado. Fondo y contenido se funden por separado, dentro de un
  contenedor con `isolation: isolate`. [VZ 2026-09-24]
- **Las opacidades del boceto van con `color-mix`,** no con un color de relleno aproximado. [VZ]
- **Color opaco en el gradiente y la transparencia con `opacity`,** porque el tema solo sabe
  concatenar el alfa en hexa. Y un hex y una URL de imagen van en variables separadas
  (`background-color` contra `background-image`): un valor en la propiedad equivocada se descarta
  en silencio. [MC]

## Bloquear el scroll, overlays y visibilidad

- ✅ **Bloquear el scroll con un drawer abierto:** [MC 2026-09-11]
  - `html:has(<gancho>.modal-visible) { overflow: hidden }`, en `html` y no en `body`, porque el
    viewport toma el overflow de la raíz;
  - `overscroll-behavior: contain` en los paneles, porque `none` en `html`/`body` no frena el
    encadenamiento desde un hijo. Las listas largas de un drawer llevan su propio `max-height` con
    `overscroll-behavior: contain`;
  - `scrollbar-gutter: stable` en `html`, para evitar el salto de ~15px al esconder la barra (no
    anda en Safari < 18.2).
- 🔥 **Ningún overlay puede vivir dentro del header.** El header tiene `z-index: 1000` (crea un
  contexto de apilado) y un ancestro con `transform`, así que un `position: fixed` adentro se ancla
  al header y no a la ventana. El overlay se muda a `<body>` en su init, y nada escribe clases en
  `<html>`, que es lo que observa `initStickyHeader`. [GG 2026-09-18]
- **Un `#id` adentro de `:has()` suma especificidad de id** y gana sin `!important`. La regla que
  lo revierte tiene que repetirlo. [MC]
- ⚠️ **`:has()` matchea aunque el elemento esté oculto.** Si solo tiene que valer en un breakpoint,
  acotalo con un media query explícito. [MC]
- ⚠️ **Si escondés con `visibility` para conservar el alto, revertí con la misma propiedad.** [MC]
- **`overflow-x: clip` y no `overflow: hidden`** cuando hay que contener un desborde horizontal:
  `clip` no crea un contenedor de scroll, así que **no rompe el `position: sticky`** de los
  ancestros. [MC]
- ⚠️ **Sin desborde, el track va con `overflow-x: visible`, no `auto`.** Un contenedor scrolleable
  de 0px igual atrapa el gesto en el celular. [MC]
- ⚠️ **Esconder con `display: none` el contenedor de una app de terceros le mata el `<dialog>`:** el
  caso y la salida están en [plataforma](08-plataforma.md).

### 🔥 `::details-content` rompe el reset de `box-sizing`

Chrome interpone el pseudo-elemento **`::details-content`** entre un `<details>` y su contenido. El
reset clásico `*, ::after, ::before { box-sizing: inherit }` **no matchea pseudo-elementos**, así
que el pseudo queda en `content-box` y el contenido hereda de ahí: **el hijo de un `<details>` es
`content-box` aunque todo el sitio sea `border-box`.** [MC 2026-08-25]

✅ Medido en Chrome 151: `getComputedStyle(details).boxSizing` da `border-box` y el del hijo,
`content-box`. [MC 2026-08-25]

**Dónde muerde:** al animar el alto de un acordeón. `scrollHeight` incluye el padding, pero
`height` solo lo incluye si el elemento es `border-box`, así que `height: scrollHeight` deja el
elemento tan alto como el padding de más. Sumado a que **`height: 0` no comprime el padding**, un
acordeón con `padding-top: 16px` **salta 16px al arrancar y otros 16 al terminar**.

La solución: leer el `boxSizing` computado en cada corrida, descontar el padding cuando es
`content-box`, **interpolar los paddings verticales junto con el alto** y medir con
`getBoundingClientRect()` (no con `scrollHeight`, que redondea a entero). El helper completo está
en [JavaScript](11-javascript.md).

### 🔥 `scrollbar-width` anula los `::-webkit-scrollbar`

Con `scrollbar-width: thin` puesto "para cubrir Firefox", Chrome **descarta los pseudo-elementos
enteros** y usa sus ~11px. Una barra de 2px diseñada con `::-webkit-scrollbar` nunca se dibujaba.
Es un trade-off, no un bug: o el detalle en Chrome y Safari, o el ancho estable en Firefox. [MC]

Por lo mismo, **`scrollbar-gutter: stable` no reserva nada sobre un scroller** que dibuja su barra
con los pseudo-elementos sin `scrollbar-width`. Sobre `html`, con barras clásicas, sí reserva el
canal (es el caso del bloqueo de scroll de arriba). [MC]

## Imágenes, carruseles y arrastre

- ✅ **Carrusel que se arrastra con el mouse:** sin `-webkit-user-drag: none` en los links y las
  fotos (y el `dragstart` cancelado, para Firefox), el drag & drop nativo del navegador gana con un
  `pointercancel` y el carrusel no se mueve. [VZ 2026-09-24]
- Para un carrusel que sangra hasta el borde, el inset va en el contenedor de scroll (ver la regla
  de márgenes negativos, abajo). El scroller nativo completo está en [patrones](14-patrones.md).
- Los `sizes` de las imágenes y cuánto se descarga por breakpoint están en
  [JavaScript](11-javascript.md), sección de performance.

## Texto, íconos y formularios

- **Subrayado con `text-decoration` + `text-underline-offset`, no con `border-bottom`.** El base pone
  algunos `.btn-link` en `display: block` y el borde cruzaba todo el ancho. [VZ 2026-09-23]
- **Si el mismo componente se dibuja a distintos cuerpos, íconos y gaps van en `em`.** [MC]
- **`white-space: pre` mantiene los espacios dobles del Figma; `nowrap` los colapsa.** [MC]
- ⚠️ **Un `<input>` no se autodimensiona.** Un nodo dibujado para la cantidad "1" recorta el "12": hay
  que dejarle margen a propósito. [MC]
- **Un trazo que Figma dibuja por dentro va como `box-shadow: inset`, no como `border`:** el borde
  suma 2px y hace saltar la caja al abrirse. [MC]
- ⚠️ **`line-height: normal` redondea distinto según la fuente:** con una fuente de sistema
  (Helvetica Neue en VZ), boceto y preview difieren 0,5 a 1px incluso en un iframe en blanco. No se
  persigue: se documenta. [VZ]

## Márgenes negativos: la regla y su excepción

🚫 **Nunca resolver layout con márgenes o paddings negativos.** Es regla dura del dev. Para un
carrusel que sangra hasta el borde: el padre **no lleva padding horizontal** (lo lleva cada bloque
que no scrollea), y el contenedor de scroll ocupa todo el ancho con su inset como `padding-left`
**propio**, más `scroll-padding-left`. Así la primera card arranca en el inset y, al deslizar, el
contenido llega al borde sin un canal fijo. [MC]

⚠️ **Excepción aceptada en MC: el full-bleed de una celda de grilla.** Un banner que es una **celda**
de la grilla de productos no se puede sacar del contenedor que tiene el padding, que es lo que la
regla pide. Ahí el "de borde a borde" es un margen negativo **exactamente igual al inset que publica
la section** (`--products-grid-padding-x`), así que no puede abrir scroll horizontal. Fuera de ese
caso, la regla vale. [MC 2026-09-11]
