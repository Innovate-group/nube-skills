# Patrones que conviene copiar

Soluciones que funcionaron en producción y que conviene usar desde el primer día, en vez de
reinventarlas después del segundo caso. Las trampas que las motivaron están en los capítulos de
cada área: [Twig](07-twig.md), [plataforma](08-plataforma.md),
[producto y carrito](09-producto-carrito-busqueda.md), [CSS](10-css.md) y
[JavaScript](11-javascript.md).

## Lo esencial

- **El diagnóstico por comentario HTML es el recurso que más vueltas ahorró.** Va sin guarda,
  distingue los casos que se confunden entre sí y nunca vuelca objetos de la plataforma.
- **Reemplazar un componente nativo es no renderizarlo**, detrás de un toggle que lo devuelve.
  Nunca esconderlo por CSS.
- **Filtrar la lista de cada section antes de `has_products`, `slice` o cualquier contador**, y
  siempre fail-open: un filtro del tema nunca hace desaparecer lo que el backend puso.
- **Extender los snippets compartidos con parámetros aditivos**, cuyo default es el
  comportamiento anterior, y verificar los demás lugares que los llaman.
- **Settings en un bloque de configuración y variantes de estilo como setting**, antes que
  sections nuevas.
- **Un solo renderizador de media y un solo wrapper de visibilidad**, reusados en todo el tema.
- **Mientras el rediseño es borrador, no se tocan los datos de la tienda** que usa también el tema
  publicado: se resuelve con un setting con fallback.

## Visibilidad y diagnóstico

### El wrapper de visibilidad (`snippets/section-visibility.tpl`)

Visibilidad interna (solo el equipo) y programación por fecha y hora, en **un solo lugar**, que
se aplica envolviendo el render *[MC]*:

```twig
{% embed 'snippets/section-visibility.tpl' with {
  visibility: section.settings,
  customer_email: customer ? customer.email : '',
  is_preview_mode: is_preview,
  store_country: store.country,
} %}
  {% block visible_content %}
    {# ...toda la section... #}
  {% endblock %}
{% endembed %}
```

- En el schema van 6 settings: `internal_only`, `schedule_enabled`, `visible_from_date/_time` y
  `visible_until_date/_time`. Un **bloque** también puede llevarlos, así cada fila tiene su propia
  programación ([schema](06-schema-y-traducciones.md)).
- Es `{% embed %}` y no `{% include %}` a propósito: cuando la section no corresponde, no se
  renderiza nada de su markup, ni un div vacío que aporte su `gap`.
- ⚠️ En el editor (`is_preview`) la section siempre se muestra, para poder configurarla.
- ⚠️ Las fechas del editor se interpretan como hora local de la tienda, con un offset fijo por
  país. No contempla horario de verano, igual que el timer del tema base.
- ⚠️ **No se usa en la página de contraseña ni en las landings institucionales** *[MC]*: una
  programación mal cargada dejaría la tienda sin puerta.
- Las sections del tema base no traen visibilidad: se migran a medida que se tocan.

### 🌟 El diagnóstico por comentario HTML

Cuando una pieza depende de resolver algo (una categoría, un producto, un metacampo, un JSON),
**emitir un comentario HTML con el estado de esa resolución**:

```html
<!-- gift-bag: enabled=1 from=none wanted=123 found=0 picked=none cats=12|34|56 -->
<!-- collection-tabs: [Colección] kind=category id=123 productos=12 · filled=2 -->
<!-- pdp-category-source: metacampo=pdp.categoria origen=fija valor=/x/ resuelta=123 productos=6 -->
```

Se lee con "Ver código fuente", buscando el prefijo. Reglas para que funcione:

- **Va SIN guarda:** tiene que imprimir también cuando la pieza no dibuja nada, que es justo
  cuando más falta hace.
- **Distingue los casos que se confunden:** `from=none` (no resolvió), `found>0 picked=none`
  (resolvió pero sin stock) y `picked=<id>` (todo bien, lo que falla es CSS).
- **Instrumenta cada término de la guarda** *[MC]*. Es lo único que distingue "no hay datos" de
  "la guarda apagó el render".
- **Campos que resultaron útiles** *[MC]*: `origen=metacampo|etiqueta|fija|ninguna`,
  `json=ok|INVALIDO`, `resuelto=[…]`, `recibidos` / `escondidos` / `dibujados`, y `precios=min..max`.
  El rango de precios del conjunto cerró un reporte de "recomienda productos caros": no había nada
  en esa franja.
- **Los campos caros se calculan solo cuando la búsqueda falló** (por ejemplo, recorrer el árbol
  de categorías para listar los ids que sí existen), así el camino feliz no cuesta nada.
- ⚠️ **Nada de volcados de objetos de la plataforma.** Un comentario HTML no protege la evaluación:
  `{{ product.metafields | json_encode }}` adentro de un comentario rompe la página igual
  ([Twig](07-twig.md)).
- **Un prefijo por pieza** (`toolbar-filtros:`, `search-terms:`, `draft-gate:`), para encontrarlo
  con un buscar.

## Componentes nativos

### Reemplazar un componente nativo sin esconderlo

Un toggle global elige qué se incluye: el componente propio o el nativo *[MC 2026-09-16]*.
Apagándolo, vuelve el nativo sin tocar código.

- **No se renderiza el nativo; no se lo esconde por CSS.** El JS de la plataforma suele
  escribirle `display` inline (`changeVariant` lo hace con las cuotas), y eso le gana a cualquier
  regla. Antes de sacar un nativo, confirmá que el JS que lo toca tenga guarda de null
  (`findOne` + `if (el)`).
- **El propio se dibuja con la misma condición que el nativo.** Por ejemplo, las cuotas:
  `product.show_installments and product.display_price and product.get_max_installments.installment > 1`.
- **Prefijo de clase propio**, sin reusar las clases del nativo: las reglas del tema con más
  especificidad le ganarían a tus variables ([CSS](10-css.md)).
- **En el camino al checkout, un cambio arriesgado va detrás de un toggle** que vuelve al markup
  del tema base. Si el checkout falla, es el primer switch.

### Parámetros aditivos en snippets compartidos

🔥 **Un parámetro nuevo en un snippet compartido tiene que preservar el comportamiento viejo con
su default** *[MC]*. `product-form.tpl`, `product-image.tpl` y `modal.tpl` también los usan
`featured-product` y el quickshop, que no pasan el parámetro. El default del **setting** puede ser
el nuevo; el del **parámetro** del snippet, no.

Ejemplos que se hicieron así: `render_structured_data`, `force_image_slider`,
`carousel_view_all_url`, `extra_item_classes` en `item.tpl` (para marcar cards desde Twig). Al
terminar, verificá que los demás lugares que llaman al snippet no cambian: mismas clases en el
HTML.

### Dibujar bloques en otro punto del DOM

Los bloques se le pasan a un snippet por parámetro (`promo_blocks`) y se saltean en el loop
principal *[MC]*. Para agrupar bloques del mismo tipo con su propio `gap`, sin márgenes negativos,
va un contenedor con un segundo `for`. El costo: `block_order` ya no puede intercalarlos.

## Settings y bloques

- **Bloque de configuración.** Un bloque que solo lleva settings (por ejemplo un `product_list`) y
  que la section busca por tipo para leérselos. Es lo que hace `sections/product-list.tpl` con su
  bloque `products`, y lo que se generalizó en VZ: `product-rail-products` es la fuente de
  productos de varias sections *[VZ 2026-09-24]*. `product_list` solo es confiable como setting
  de bloque ([schema](06-schema-y-traducciones.md)).
- **Bloque espejo con los mismos ids.** `product-rail-banner` declara los mismos ids de settings
  que `product-grid-banner`, así lo dibuja el mismo snippet sin duplicar markup *[VZ 2026-09-29]*.
- **Variantes de estilo como setting, antes que sections nuevas.** Un `select` de estilo en una
  section existente, con default igual al comportamiento anterior, y se verifica que las otras
  páginas no cambian *[VZ 2026-09-24]*. Así la página "Nuestra Historia" salió casi entera de
  sections que ya existían.
- **Setting de texto `Etiqueta=destino`**, donde el destino es un id, un nombre o una URL *[MC]*.
  Una entrada sin `=` sigue haciendo lo de antes, así una lista vieja no cambia sola.

## Fuentes de datos por producto

- **Categoría por producto, sin app:** una cascada **metacampo → etiqueta `clave=valor` → categoría
  fija de la section** *[MC]*. La etiqueta es lo único que el comerciante puede cargar a mano desde
  el panel; la clave es configurable. Si la fuente es una categoría, el producto actual se saca
  de su propia lista.
- **Completar `category.products` con las subcategorías directas**, deduplicando por id, solo si
  los productos propios no alcanzan a llenar el carrusel *[MC]*. `category.products` trae solo los
  productos directos ([producto](09-producto-carrito-busqueda.md)).
- **Un metacampo de texto con un JSON que pisa settings clave por clave** *[MC]*. Lo que el JSON no
  trae cae a la setting, y el diagnóstico dice `json=INVALIDO` cuando no parsea. La app que lo
  escribe omite las claves vacías en vez de mandarlas en blanco. No se mezcla con otra fuente que
  ya tenga su propio mecanismo.
- **Los datos de catálogo van en tags y metacampos que el tema lee sin depender de nada en
  runtime** (`badge-<ubicación>=<valor>`, familias, `pdp.*`); por un endpoint van solo las acciones
  del comprador ([apps propias](16-multipais-apps-integraciones.md)).

## Listas y cards

- **Filtros del tema fail-open** *[MC 2026-09-21]*. Si nada matchea, o la lista auxiliar quedó
  vacía, no se esconde nada. Un filtro del tema (agotados, sin foto) nunca debe hacer desaparecer
  un producto que el backend puso.
- 🔥 **Filtrar la LISTA de cada section antes de `has_products`, `slice` y los contadores, no en
  `item.tpl`** *[MC 2026-09-28]*. Si no, quedan huecos, flechas y wrappers de más, y el contador de
  cards se corre (ubica los banners por posición y el `fetchpriority` del LCP). Si una pieza aparea
  datos (el punto de un shop-the-look con su producto), se descarta el par.
- **El `ld+json` una vez por producto**, con un flag declarado antes del loop: con cards filtradas,
  `loop.first` puede no dibujarse *[MC]*.
- **Una card por color (desglose).** La expansión va en la section de la grilla, con un `for`
  interno sobre `[null]` cuando no hay desglose y un contador propio de cards que reemplaza a
  `loop.index` *[MC]*.
- **Un orden que la grilla tiene que respetar se resuelve en Twig, no con `order` de CSS**:
  `nth-child` ignora `order`, y los banners, las filas alternadas y el `fetchpriority` son
  posicionales *[MC]*.
- **Rank espaciado** (1000, 2000, …): mover un ítem es una sola escritura *[MC]*.
- **Variantes de card según las columnas que elige el comprador: CSS sobre `.grid-N`**, nunca un
  setting *[MC]*. Se esconden los contenedores, no las piezas, así una pieza nueva aparece
  escondida.

### Links dentro de la card, y la card entera como link

- ⚠️ **Un link anidado dentro del `<a>` de la card no existe**: el parser parte la card en dos
  *[MC]*. Se usa `<span role="link" tabindex="0" data-href>` con un handler delegado en `document`.
  Lo mismo con un `<button>` adentro de un `<a>`, que va como hermano.
- ✅ **Link en toda la card o el slide** *[VZ 2026-09-29]*. Un `<a>` vacío que la cubre, entre el
  degradado y los controles. El contenido lleva `pointer-events: none`, el botón pasa a `<span>` y
  se ilumina con `~` desde el hover o el foco del link, y solo el link del slide activo es
  tabulable.
- **Forms de alta fuera de cualquier `<form>` contenedor** (el `modal.tpl` del carrito, la página
  del carrito), como hermanos ocultos, con un puente por `data-*` y no por `closest('form')` *[MC]*.
  Ningún control dentro del carrito es `submit`, salvo el checkout.

### Cucardas, muestras de color y fotos por color

- **Cucardas desde etiquetas del producto:** `badge-<ubicación>=<valor>` *[MC]*. Si el valor
  arranca con `http`, se dibuja como imagen. Las reglas por texto se emiten como custom properties
  inline, que le ganan al token del tipo.
- **Diccionario de muestras en un setting global** con pares `Nombre:valor`, donde el valor es un
  hex o una URL de imagen *[MC]*. Hex e imagen van en variables separadas (`background-color`
  contra `background-image`): un valor en la propiedad equivocada se descarta en silencio. Una
  coma adentro de la URL rompe el par.
- **Diccionario de colores mientras la tienda no cargue `custom_data`** *[GG]*. El tema pinta la
  muestra con `option.custom_data`, que es un dato de la tienda compartido con el tema publicado.
  Un toggle más un mapa (`NOMBRE | #HEX;`) lo resuelven en el tema; `custom_data` tiene prioridad,
  así que el día que la tienda cargue los colores se apaga el toggle y no hay nada que desmontar.
- **Convención de alt `NOMBRE#COLOR#N`** *[GG 2026-09-23]*. Filtra la galería de la ficha por el
  color elegido (el primer render ya sale filtrado desde Twig y respeta `?variant=`) y define qué
  es "foto propia" de un color. Una foto sin `#` o un video se ven siempre, y un color sin fotos
  propias muestra la galería completa. Es la respuesta a que `variant.image` nunca viene vacío
  ([producto](09-producto-carrito-busqueda.md)).

## Medios

### Un solo renderizador de media

Un snippet que es un **superconjunto de `image.tpl`** y resuelve en este orden:
**mp4 > embed > video de la biblioteca > imagen** *[MC 2026-09-11]*.

- Se incluye sin `with`, para heredar los parámetros, y sus variables locales llevan un prefijo
  propio (el include hereda el contexto: [Twig](07-twig.md)).
- **Manda la presencia del dato.** No hay un select `media_type` que pueda contradecir al
  contenido.
- **El slot mobile no cae al video de desktop**, con la misma convención que `use_mobile_image`:
  evita bajar dos veces el archivo.
- **La regla de los cuatro medios** *[VZ 2026-09-24]*: por pedido del dev, en VZ toda pieza con
  foto o video lleva imagen y video, cada uno para desktop y mobile, aunque el boceto muestre solo
  una foto. El video gana y la imagen queda como portada. Lo resuelve `snippets/vz-media.tpl`,
  que dibuja una capa por breakpoint si difieren, y el JS le pone el `src` al video recién al
  entrar en pantalla. Es un patrón copiable; la obligación es de ese proyecto.

### El scroller nativo en vez de Swiper

Para un carrusel donde el boceto pide "scroll libre con la card siguiente asomando", el CSS ya lo
hace: `overflow-x: auto` + `scroll-snap`, con flechas que llaman a `scrollBy`. Swiper no aporta
nada ahí y trae sus trampas ([JavaScript](11-javascript.md)). El ancho de card va con una fórmula
fluida, nunca fija:

```
(100% − gap × (columnas − 1) − asomo) / columnas
```

Un ancho fijo entra en el artboard de 1440 y rompe en 1280.

**Swiper inerte por CSS** (`transform: none !important`, `display: contents` en el slide) en vez
de desinicializarlo, cuando de él cuelgan fancybox y las miniaturas *[MC]*. Con Swiper inerte, y
solo así, es seguro usar `order`.

### 🔥 Un `%` se resuelve según la PROPIEDAD donde se usa

Una custom property es texto sin unidad resuelta. Un `100%` pensado como ancho, guardado en una
variable y usado dentro de `height`, pasa a ser un porcentaje **de la altura**. Medido: un overlay
dio 344 px en vez de 672.

Para "alto = ancho × relación" se usa el truco del **`padding-top`** en un `::before`, donde un
porcentaje sí se resuelve contra el **ancho** del contenedor.

## Elementos flotantes

- ✅ **Barra de compra mobile que "flota hasta aterrizar": `fixed` + un placeholder**
  *[MC 2026-09-07]*.
  - 🚫 `sticky`: el bloque es el primer hijo de su contenedor y no tiene recorrido.
  - 🚫 Un `translateY` por frame: llega siempre un frame tarde y se ve a los saltos.
  - Si los altos difieren, el umbral compara el borde **superior**
    (`rect.top + altoComprimido > innerHeight`).
  - El alto comprimido se mide poniendo y sacando la clase de forma sincrónica.
  - El alto del placeholder se fija antes de despegar, y el lugar natural se lee del placeholder.
  - Un hijo `fixed` sale del flex, así que el `gap` no se descuadra.
- **Botón flotante que esquiva a otro elemento** (el botón de WhatsApp que sube cuando aparece la
  barra de compra) *[MC]*:
  - calcular contra la posición de **reposo**, no contra el rect actual, que ya incluye el
    transform y oscila;
  - chequear también el solapamiento horizontal;
  - recorrer los hijos y saltear los que miden 0;
  - cachear el `bottom` y releerlo en el resize;
  - topear el desplazamiento en el 35% del viewport.

## Páginas

### El `<h1>` y `page-header`

Varias pantallas mudaron el `<h1>` de la section `page-header` a la section principal. Al hacerlo
hay que **llevarse el `data-store="page-title"`** (es lo que usa la plataforma) y sacar
`page-header` del JSON de esa página; si no, quedan dos `<h1>`. Ojo en la home: el bloque del logo
ya trae un `<h1>` oculto, así que los títulos del hero van en `<h2>` *[VZ 2026-09-24]*.

### Una section nueva en su plantilla propia

Mientras no está confirmado que la plantilla alternativa rutea, la section vive en su plantilla
propia **y** con un respaldo en `page.json` filtrado por el handle de la página
(`url | trim('/') | split('/') | last` contra `page.handle`) *[MC]*. Las hermanas se esconden con
`:has()`. El respaldo se borra cuando se confirma el ruteo, porque deja dos `<h1>`. Cómo saber
qué plantilla rutea: [plantillas](12-plantillas.md).

### Un kit de landings reutilizable

Antes de crear una section para una página institucional, mirá si alcanza con las que ya existen
y una variante de estilo *[VZ 2026-09-24]*. En VZ, "Nuestra Historia" salió de:

- la portada del hero con el estilo "De página interna";
- `text-statement` para la intro y la cita;
- `split-image-text`;
- `text-columns` para la línea de tiempo, las figuras y las cifras;
- `editorial-cards` con el estilo "Pasos";
- `image-tiles` con el diseño "Mosaico";
- `wide-banner` con el estilo "Velo parejo";
- un encabezado centrado con antetítulo, como snippet.

### Otras piezas chicas

- **Cuenta regresiva con la lógica de fechas de `timer-offers`** (regex, `| date('U')`, zona por
  país) y el atributo `hidden` fuera del período *[VZ 2026-09-24]*.
- **Copiar al portapapeles** con `navigator.clipboard` y un `<textarea>` de respaldo *[VZ]*.

## Datos de la tienda compartidos con el tema publicado

Mientras el rediseño es un borrador, **no se tocan los datos de la tienda que usa también el
tema productivo**: se resuelven en el tema, con un setting y un fallback *[GG 2026-09-23]*. El
logo del Administrador, los colores por variante (`custom_data`), los menús y las asignaciones de
`sections.txt` son de la tienda, no del tema.

Un ejemplo: en GG, el diseño pinta el logo de blanco con `filter: brightness(0) invert(1)`, que
exige un PNG con fondo transparente, y el logo del Administrador era RGB con fondo blanco. En vez
de reemplazarlo en el Administrador, el bloque del logo ganó un `image_picker` propio y, vacío,
renderiza un PNG de fallback en `static/`.
