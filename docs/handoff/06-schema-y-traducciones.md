# Schema, settings y traducciones

Qué puede editar el comerciante (el `{% schema %}` de cada section y block, y
`config/settings_schema.json`) y en qué idioma lo ve (`translations/`). Lo que el Twig hace
con esos valores está en [Twig](07-twig.md). Cómo no pisar lo que el comerciante guardó desde
el editor está en [Sync y reglas](03-sync-y-reglas.md).

## Lo esencial

- El `{% schema %}` es **JSON puro** y cada input lleva **dos claves**: `"type": "setting"` y
  `"setting_type": "<tipo>"`. No es el formato de Shopify.
- **No te apoyes en el default de una section que ya está guardada.** Lo que tiene que verse
  va con un fallback en Twig o escrito en el JSON de la página. Hay mediciones que
  contradicen la regla en casos puntuales (❓, más abajo, con cómo re-medirlo), pero ninguna
  alcanza para confiar en el default.
- **Los defaults de un bloque sí llegan, y a todas las instancias ya guardadas** apenas se
  sube el cambio. Nunca pongas un default de texto de relleno.
- **Un setting que cambia de significado necesita un id nuevo.** Al renombrar el `type` de una
  section no se tocan ni el id de la instancia ni los ids de los settings: si no, lo guardado
  se pierde en silencio.
- `product_list` va en un **bloque de configuración**. En la section está medido de las dos
  maneras (❓, con cómo re-medirlo más abajo). Devuelve como mucho 12 productos, y su `id` es un string.
- **Toda clave `t:` va en los 7 locales.** Si falta en alguno, el editor muestra el `t:`
  crudo, y lo mismo pasa con un namespace inventado.
- **`es` y `es_AR` no son lo mismo** (tuteo contra voseo). La auditoría mira el registro, no
  solo que la clave exista.

## Anatomía del `{% schema %}`

Cada `sections/*.tpl` y `blocks/*.tpl` termina con un bloque `{% schema %}…{% endschema %}`
que es **JSON puro**. La forma real es esta:

```json
{% schema %}
{
  "name": "t:names.media_banner",
  "icon": "pictureIcon",
  "class": "section-media-banner",
  "max_blocks": 15,
  "enabled_on": { "page_templates": ["category", "search", "home", "page", "product"] },
  "blocks": [ { "type": "collection-list-item" } ],
  "settings": [
    { "type": "header", "content": "t:names.multimedia" },
    {
      "type": "setting",
      "setting_type": "select",
      "id": "media_type",
      "label": "t:settings.media_type",
      "info": "t:info.media_type",
      "options": [
        { "value": "image", "label": "t:options.media_image" },
        { "value": "video", "label": "t:options.media_video" }
      ],
      "default": "image"
    },
    {
      "type": "setting",
      "setting_type": "image_picker",
      "id": "image",
      "label": "t:settings.image",
      "visible_if": "{{ section.settings.media_type == 'image' }}"
    }
  ],
  "presets": [
    {
      "name": "t:names.media_banner",
      "category": "t:categories.media",
      "settings": { "media_type": "image", "content_width": 600 },
      "blocks": [ { "type": "collection-list-item" }, { "type": "collection-list-item" } ]
    }
  ]
}
{% endschema %}
```

- ⚠️ **Ojo con la doble clave: `"type": "setting"` + `"setting_type": "<tipo>"`.** El `type`
  de cada ítem es `setting` o `header`, y el tipo del input va en `setting_type`. Funciona
  distinto que en otros ecosistemas, así que es fácil equivocarse.
- `"type": "header"` es un separador visual con `content`. ⚠️ **En el editor, un setting
  pertenece al `header` que tiene arriba.** Si metés un header nuevo en el medio, se lleva a
  su grupo los settings de abajo: "Posición de la imagen" terminó colgando del grupo "Video"
  *[MC 2026-09-11]*.
- Un schema roto no da error en el push. El chequeo de que cada `{% schema %}` parsee como
  JSON está en [Verificación y QA](15-verificacion-y-qa.md).

## Tipos de setting

### Los que se usan en un tema real

Censo de un tema Ipanema 1.0.0 con ~66 sections y ~67 blocks *[MC, antes de 2026-09-03]*:

| tipo | usos | notas |
|---|---|---|
| `range` | 448 | ⚠️ se lee con `??`, no con `\| default()` (ver [Twig](07-twig.md)) |
| `toggle` | 203 | |
| `color` | 143 | |
| `radio` | 104 | |
| `text` | 100 | |
| `select` | 75 | |
| `image_picker` | 66 | guarda `@media-lib:<uuid>` o una URL |
| `url` | 42 | ⚠️ puede devolver una ruta relativa **o** absoluta |
| `date` / `time` | 26 / 26 | strings `YYYY-MM-DD` y `HH:MM` |
| `richtext` / `inline_richtext` | 20 / 7 | |
| `text_alignment` / `alignment` | 18 / 15 | |
| `product_list` | 7 | ver la sección de abajo |
| `heading_select`, `number`, `menu`, `font_picker`, `video_url`, `icon_picker`, `custom_code`, `checkbox`, `button_preview`, `menu_item`, `label_preview`, `custom_css` | 1–6 | existen aunque la documentación de referencia no los liste |

### Lo que conviene saber de cada uno

- 🚫 **No existe un `setting_type` de UN producto.** El único que tiene que ver con productos
  es `product_list`, que ofrece elegir una lista o una categoría y no acepta ninguna clave que
  lo limite a uno. El workaround es tomar `| first` y explicarlo en el `info` del setting
  *[MC]*. Pedir un `product_id` y resolverlo con `| get_products` tampoco funciona: la section
  desaparece (ver [Twig](07-twig.md)).
- 🚫 **Tampoco hay un `setting_type` de colección.** Para elegir una categoría a nivel section
  se usa un `url` (el selector de enlaces, con precedente en sections: el `category_link` de
  `product-grid-banner`), que después se busca en el árbol de categorías *[MC 2026-08-27]*.
  Detalles:
  - Conviene aceptar un id, un nombre o una URL.
  - ⚠️ Compará por URL solo si el valor contiene `/`. Si no, un nombre corto como "Tops"
    matchea por substring contra cualquier URL.
  - El árbol hay que recorrerlo hasta el tercer nivel. Por qué `categories` no alcanza está en
    [Producto, carrito y búsqueda](09-producto-carrito-busqueda.md).
  - Si no hay match, el bloque se dibuja igual.
- ⚠️ **`video_url` es para YouTube y Vimeo, y guarda un objeto** (`.id`, `.type`) que arma la
  plataforma cuando el comerciante guarda desde el editor.
  - Para un `.mp4` va un setting `text` o `url`: con un archivo directo, el objeto de
    `video_url` queda vacío *[MC 2026-09-11]*.
  - Por el mismo motivo, un metacampo o un JSON de texto no puede cargar un link de YouTube o
    Vimeo: solo un `.mp4` o una imagen *[MC 2026-09-11]*.
  - La biblioteca de medios no sirve para subir videos *[VZ 2026-09-24]*, así que el video de
    una pieza nueva va como URL.
- ⚠️ **Un `image_picker` puede devolver un video.** Ipanema contempla el caso:
  `resolve_media` informa el tipo, y `blocks/media-stack-item.tpl` dibuja un `<video>` en vez
  de un `<img>` roto. Un renderizador propio tiene que hacer lo mismo *[MC 2026-09-11]*. El
  patrón completo del renderizador está en [Patrones](14-patrones.md).
- ⚠️ **No hay precedente de un `range` con `step` decimal.** Para 10,5 / 21 / 27 % se usó un
  `select` *[VZ 2026-09-24]*.
- ⚠️ **El setting `menu` lee un menú del Admin.** El handle va con **guion bajo**
  (`centro_de_ayuda`), no con guion. El ítem activo es `item.current` (o
  `item.url == page.url`). No hay API de menús: el menú se crea a mano en el Admin
  *[VZ 2026-09-24]*.
- Un `icon_picker` puede reusar las claves `t:options.icon_*` de otro picker. Para ofrecer
  "sin ícono" hace falta una clave `options.icon_none` en los 7 locales *[MC 2026-09-16]*.
- Criterio: en un textarea con varios valores, el separador es `;`, nunca un salto de línea.
  No está verificado que el motor interprete `"\n"` *[GG]*.
- Criterio: si un `select` puede contradecir al contenido (un `media_type` que dice "video"
  sin ningún video cargado), sacalo y que mande la presencia del dato. Las claves huérfanas
  que quedan en los JSON guardados son inofensivas *[MC 2026-09-11]*.

## `product_list`

- **El patrón que funciona siempre es un bloque de configuración.** Es un bloque que lleva el
  `product_list`, y la section lo busca por tipo para leerle los settings. Es lo que hace
  `sections/product-list.tpl` del tema base con su bloque `products`, y lo que se generalizó en
  VZ: un solo bloque sirve de fuente de productos para varias sections *[VZ 2026-09-24]*. El
  patrón completo está en [Patrones](14-patrones.md).
- ❓ **A nivel section está medido de las dos maneras.** Abajo, cómo re-medirlo.
  - En un Ipanema 1.0.0, un `product_list` declarado en el schema de la section llegó con
    `kind` e `id` bien, pero con `.products` **vacío** (`| length` = 0) y sin ningún error. La
    section se dibujaba como si no hubiera productos *[MC 2026-09-04]*.
  - En un Ipanema 1.2.0, `sections/lookbook.tpl` declara `products_source` en los settings de
    la section, lee `section.settings.products_source.products` y la home publicada dibuja
    cuatro productos reales *[GG 2026-09-30]*.
  - Puede ser la diferencia de versión o una prueba mal armada.
  - **Cómo re-medirlo:** en una section de una página no crítica, declarar un `product_list`
    en la section y otro en un bloque, apuntarlos a la misma categoría, e imprimir los dos
    `| length` en un comentario HTML de diagnóstico. Anotar la versión de Ipanema de
    `manifest.json`.
  - Mientras tanto, si la section necesita el `product_list`, que tenga una segunda vía: el
    `id` crudo buscado en el árbol de categorías, con el diagnóstico diciendo por cuál de las
    dos resolvió *[MC 2026-09-07]*.
- A nivel **global** (`settings.*`) tampoco está verificado que hidrate `.products`. Hubo que
  agregar la misma segunda vía: buscar la categoría por su `id` crudo dentro de `categories`
  y sus hijas *[MC]*.
- ✅ **Devuelve como máximo 12 productos**, aunque la categoría tenga más. Una categoría con 25
  en el storefront resolvió 12 *[MC, antes de 2026-09-03]*.
- ⚠️ **El valor que guarda el picker es `{"kind": "category"|"collection", "id": "…"}`, con el
  `id` como string.** `category.id` llega como número, así que para compararlos hay que
  normalizar los dos lados con `~ ''`. Sin eso no matchea nunca, y no hay error.
- ⚠️ **No tiene default de schema: lo elige el comerciante.** Con el picker vacío la pieza no
  dibuja nada. Hay que decirlo en el `info` del setting y en el diagnóstico (por ejemplo
  `from=none wanted=none`) *[MC]*.
- ⚠️ **Puede resolver 0 productos para una categoría que en el storefront muestra uno,** sin
  ningún error *[MC]*.
- Las colecciones automáticas (Destacados, Novedades, Ofertas) tienen sus propias
  particularidades. Están en [Producto, carrito y búsqueda](09-producto-carrito-busqueda.md).

## Defaults: cuáles llegan y cuáles no

- 🔥 **El default declarado en el `{% schema %}` de una SECTION no llega a
  `section.settings` si la section ya está guardada en el JSON de la página** con
  `"settings": {}` o con settings parciales. Se verificó muchas veces: settings nuevas que
  salían vacías, toggles que llegaban falsy, textos que no se dibujaban *[MC, antes de 2026-09-03]*.
- ❓ **Hay dos mediciones que no encajan con esa regla** (cómo re-medirlo, al final de este
  punto):
  - el default de un setting `color` **sí llegó** a una section registrada sin esa clave en el
    JSON. El panel salió con el color del default, y para "sin fondo" hubo que guardar
    `transparent` en el JSON, como hace Ipanema *[VZ 2026-09-24]*;
  - un setting **global** declarado en `settings_schema.json` y no guardado desde el editor
    llegó con el default del schema *[VZ 2026-09-24]*. El día anterior, en el mismo proyecto,
    se había escrito lo contrario *[VZ 2026-09-23]*.

  Puede depender del tipo de setting, o de si la clave falta del todo o la section tiene
  `"settings": {}`. **Cómo re-medirlo:** sumar a una section ya guardada un setting de cada
  tipo (`color`, `text`, `range`, `toggle`) con un default distinguible, e imprimirlos en un
  comentario HTML. Probar las dos variantes del JSON: sin la clave y con `"settings": {}`.
- **Lo que tiene que verse no depende del default.** Hay dos caminos:
  1. **Un fallback en Twig**: `| default('…')` para strings, `?? valor` para números y toggles
     (el porqué está en [Twig](07-twig.md)). No toca ningún archivo del comerciante, y es lo
     que se prefirió en MC *[MC 2026-09-21]*.
  2. **Escribirlo en el `templates/pages/*.json`**, o en `config/settings_data.json` si es
     global, pasando antes por el gate de [Sync y reglas](03-sync-y-reglas.md).
- ✅ **Los defaults de un BLOQUE sí llegan a `block.settings`** *[MC, antes de 2026-09-03]*. Eso tiene dos
  caras:
  - 🔥 un `"default": "t:defaults.faq_item.answer"` en un bloque hizo salir en una tienda
    **productiva** el texto *"Escribí acá la respuesta a la pregunta."* en 9 filas. **Nunca
    pongas defaults de texto de relleno en bloques** *[MC, antes de 2026-09-03]*;
  - ⚠️ **un setting nuevo en un bloque cambia todas las instancias ya guardadas apenas se sube,**
    porque ningún JSON tiene todavía esa clave. Un `show_shadow` con default apagado le sacó el
    degradado a un banner que ya existía *[MC 2026-09-25]*. Se puede usar a favor: un
    `show_payments_link` nuevo arrancó apagado en todas las fichas sin tocar `product.json`
    *[MC 2026-09-17]*.
- ⚠️ **El valor guardado le gana al default también en las listas de opciones.** Al volver a
  ofrecer la opción de 3 columnas hubo que escribir `"2,3,1"` en las cuatro plantillas de
  categoría. Sin eso, el botón no aparecía *[MC 2026-09-11]*.

## Hacer evolucionar un schema sin romper lo guardado

- ⚠️ **Si cambia el significado de un setting, usá un id nuevo.** Los valores viejos que
  guardó el servidor le ganan al default nuevo y rompen el layout sin ningún síntoma. En MC,
  un `horizontal_padding: 0` y un `vertical_padding: 80` guardados obligaron a crear
  `content_inset` y `media_width` *[MC]*.
- ⚠️ **Al renombrar el `type` de una section, no toques el id de la instancia ni los ids de
  los settings.** Si renombrás `faq_landing`, `question` o `answer`, se pierde la
  configuración guardada en el servidor. Las etiquetas sí se pueden cambiar *[MC 2026-08-25]*.
- **Si partís un setting en mobile y desktop, el nuevo toma como default el valor de
  desktop:** `horizontal_padding_mobile ?? horizontal_padding`. Va `??` porque el 0 es un
  valor real. Así, donde nadie lo cargó, el render no cambia *[MC 2026-09-11]*.
- ⚠️ **Antes de sacar un setting, fijate si está guardado en `templates/**/*.json`.** Si no
  está, borrarlo no deja una clave huérfana y no hay que tocar ningún JSON *[MC 2026-09-11]*.
  - Al sacarlo de verdad, van también sus claves en los 7 locales, el `<style>` que lo usaba
    y las notas.
  - Si es una opción que el cliente puede volver a pedir, **no** borres sus traducciones.
- ⚠️ **El editor carga los schemas al abrirse.** Después de subir un setting nuevo, hay que
  recargar el editor: si alguien guarda con el estado viejo en memoria, puede borrar la clave
  nueva *[GG 2026-09-23]*.
- ⚠️ **Las sections del tema base con `deletable: false` se deshabilitan, no se borran**
  *[VZ 2026-09-24]*.

## `visible_if`, `enabled_on`, `class`, `icon` y `presets`

### `visible_if`

Revela settings de forma condicional, con una expresión Twig entre llaves:

```json
"visible_if": "{{ section.settings.media_type == 'video' and section.settings.use_mobile_video }}"
```

Para "este setting tiene valor" alcanza con la truthiness pelada:
`"{{ settings.badge_rule_1_text }}"`. Es el patrón para revelar N slots de a uno.

### `enabled_on` / `disabled_on`

```json
"enabled_on": { "page_templates": ["category", "search", "home", "page", "product"] }
```

Sin `enabled_on`, la section se puede usar en cualquier plantilla. Eso permitió reutilizar
`recommended-products` en la página del carrito sin tocar una línea de código *[MC]*.

### `class`, `icon` y `presets`

- `class` se suma al wrapper que emite la plataforma. Qué llega al DOM, y la trampa de `m-0`,
  está en [Plataforma](08-plataforma.md). Criterio: en una section nueva, `class` de un solo
  token *[MC]*.
- `icon` es el ícono en la galería del editor (`pictureIcon`, `ColorPaletteIcon`…).
- **Sin `presets`, la section no aparece en la galería.** Sirve para tener una section que
  solo exista escrita en un JSON: se usó para un gate de borrador que no se tiene que poder
  apagar desde el editor (ver [Plantillas](12-plantillas.md)).

## Contratos de los bloques del tema base

- 🔥 **En `blocks/heading.tpl`, `custom_font_size` se ignora salvo que `size` valga
  `"custom"`.** Todos los títulos de un `home.json` salían con el tamaño equivocado por eso
  *[GG 2026-09-16]*.
- ⚠️ **El loop de `blocks/product-info.tpl` enumera los tipos de bloque que dibuja.** Un
  bloque nuevo va en el schema **y** en ese loop *[GG]*. Además, la definición de
  `description` está repetida dentro del mismo schema: un setting nuevo del bloque de
  descripción va en los dos lugares *[VZ 2026-09-24]*.
- Criterio: **una section no puede leer los settings de un bloque de otro template.** Por
  ejemplo, los del carrito lateral viven en el header. O se sube el setting a global, o se
  copia *[VZ 2026-09-24]*.
- Un bloque también puede llevar los seis settings del wrapper de visibilidad, y así cada fila
  tiene su propia programación. Al pasar settings sueltos a bloques repetibles, los valores
  guardados se migraron a un bloque en las plantillas *[MC 2026-08-27]*. El wrapper está en
  [Patrones](14-patrones.md).

## Settings globales

- `config/settings_schema.json` declara los globales, `config/settings_data.json` guarda los
  valores y `layouts/resources/style-tokens.tpl` los convierte en custom properties de CSS.
- `settings_data.json` es el estado del editor del comerciante, no código. Los defaults del
  diseño van en el schema, y lo que tiene que verse va con un fallback en Twig (ver "Defaults"
  arriba). Antes de tocarlo hay que pasar por el gate de [Sync y reglas](03-sync-y-reglas.md).
- ⚠️ **El editor descarta de `settings_data.json` todo lo que esté fuera de `"settings"`.** Las
  claves escritas en la raíz del JSON desaparecen la próxima vez que el comerciante guarda
  *[VZ 2026-09-29]*.
- Qué pasa con un global que no está guardado: ver el ❓ de "Defaults", con cómo re-medirlo.

## Traducciones

### Dos sistemas, dos archivos por locale

| Archivo | Para quién | Claves | Cómo se usan |
|---|---|---|---|
| `<locale>.json` | el **comprador** (storefront) | anidadas: `product.add_to_cart`, `cart.checkout` | `{{ 'a.b' \| t }}` |
| `<locale>.schema.json` | el **comerciante** (editor) | planas: `names.*`, `settings.*`, `info.*`, `options.*`, `defaults.*`, `categories.*` | `t:` en los schemas |

⚠️ La carpeta puede llamarse `translations/` o `locales/`: mirá cuál existe antes de crear un
archivo (detalle en [modelo y CLI](05-modelo-y-cli.md)).

Los locales de un Ipanema son `pt` (el default del tema base, con nombre `pt.default.json`),
`es`, `es_AR`, `es_CL`, `es_CO`, `es_MX` y `en`. Son 7 locales, es decir 14 archivos. En un
tema grande, del orden de ~650 claves de storefront y ~1330 de schema **por locale**
*[MC, antes de 2026-09-03]*.

### Claves que faltan

- ⚠️ **Una clave `t:` que falta en algún locale hace que el editor muestre el `t:` crudo.**
  Toda clave nueva va en los 7 locales.
- 🔥 **Un namespace `t:` inventado (`t:look.*`, `t:stl.*`) tampoco da error: sale crudo.** En
  un proyecto llegó a haber 503 claves × 7 locales sin cargar *[GG 2026-09-17]*.
- ⚠️ **En el storefront, `'clave' | t` con una clave que no existe devuelve la clave tal
  cual.** Es lo que se ve, por ejemplo, en las migas de una URL inventada (ver
  [Plataforma](08-plataforma.md)) *[MC 2026-09-17]*.
- **La auditoría es un script, no una revisión a ojo:**
  `audit-i18n.py` de la skill `nube-skills-i18n`. Cruza las claves `t:` de cada schema contra
  los `*.schema.json`, y las `| t` de sections y snippets contra los `*.json`. Cómo correrlo
  está en [Skills](02-skills.md).
  - ✅ Un Ipanema 1.2.2 sin tocar ya trae 19 claves faltantes: vienen de fábrica y no son
    regresiones *[VZ 2026-09-23]*. Por eso se anota la línea de base el día 1 (ver
    [Arranque](01-arranque.md)).

### El registro importa tanto como la clave

- ⚠️ **`es` y `es_AR` no son lo mismo, y el tema los diferencia a propósito:** voseo en `es_AR`
  ("Ingresá tu correo", "¿Tenés dudas?") y tuteo en `es`, "cuotas" en `es_AR` contra "meses" en
  `es`. `pt` a veces toma otra decisión de producto: su `add_to_cart` es "Comprar", y el
  impuesto no se llama IVA en Brasil *[MC, antes de 2026-09-03]*.
- ✅ **Las claves nuevas se copian con el registro equivocado.** En un tema, las claves del
  estudio se copiaron en voseo a todos los `es_*`: `product_item.choose_size` dice "Elegí un
  talle" en `es`, `es_CL`, `es_CO` y `es_MX`. Solo uno de los temas por país lo corrigió
  *[MC 2026-09-30]*. La auditoría tiene que mirar el registro (tuteo o voseo, talle o talla),
  no solo que la clave exista.
- ✅ **El locale de referencia se mide en cada tienda,** mirando `<html lang>` y la moneda
  *[MC 2026-09-22]*:
  - una tienda que sirve `es-CL` toma como referencia `es_CL` (tuteo);
  - una tienda que sirve `es-AR` toma `es_AR`, aunque sea de otro país. No existe `es_UY`, y el
    voseo de `es_AR` coincide con el uruguayo.

  Lo demás de las tiendas por país está en
  [Multi-país, apps e integraciones](16-multipais-apps-integraciones.md).

### Cambiar textos

- ⚠️ **Cambiar una clave de storefront afecta a **todo** el sitio,** no solo a la pantalla que
  estás mirando. `forms.email.placeholder` aparece en el login, el registro, el contacto, el
  newsletter y el popup. Al entregar, decí en qué pantallas se ve el cambio *[MC, antes de 2026-09-03]*.
- Criterio: **un texto configurable pisa a la traducción, no la reemplaza.** El setting de texto
  arranca vacío y, mientras siga vacío, se usa la clave `| t`, que sigue cambiando con el idioma
  *[MC 2026-09-16]*. Para copy compartido entre páginas, lo mismo con un setting global y la
  clave de storefront como respaldo, sin escribir `settings_data.json` *[VZ 2026-09-24]*.
- Criterio: **el singular necesita claves propias.** Si no, sale "1 productos" *[GG 2026-09-19]*.
- Criterio: **ordenar o reformatear los 14 archivos de locale genera un diff enorme** (en un
  proyecto, +6108/−4512). Va en un commit propio, separado de cualquier cambio de contenido
  *[GG 2026-09-19]*.
