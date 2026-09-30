# Twig de Tienda Nube

El motor de plantillas de Tienda Nube se parece a Twig pero no es Twig estándar, y casi todos
sus errores son silenciosos. Qué inputs llegan desde el editor está en
[Schema y traducciones](06-schema-y-traducciones.md). Cómo verificar antes de guardar está en
[Verificación y QA](15-verificacion-y-qa.md).

## Lo esencial

- 🔥 **Un error de runtime deja la section VACÍA,** sin mensaje en la página, en la consola ni
  en el push. En un snippet que cuelga del layout, el mismo error es un **500 en todo el
  sitio**.
- **Solo formas con precedente.** Antes de usar un filtro, una función o una forma de
  argumento, verificá que ya aparezca en el tema, o en otro tema del disco, en una línea que
  seguro se ejecuta.
- 🔥 **Comentarios:** nunca un `{# #}` adentro de una etiqueta `{% %}`, y nunca un comentario
  adentro de otro. El chequeo de balance de tags no ve ninguno de los dos casos.
- **Los valores engañan:** `| default()` trata el 0 y el `false` como vacíos, `product.tags`
  son objetos, `in` sobre un string busca un substring, `option.id` es un nombre y
  `variation.id` es un índice.
- **Los `null` tiran la section:** un `for` sobre `null`, un método sobre un objeto que no
  existe en esa plantilla, una división por cero, un include a un archivo que no existe.
- **`{% include %}` sin `only` le pasa al snippet todo el contexto del que lo llama.** Un
  `{% set %}` con el mismo nombre que una variable del snippet la pisa sin ningún error.
- **Metacampos:** acceso literal con punto, protegido con `| default()`. Nunca `attribute()`,
  nunca un subíndice.

## La regla número uno: solo formas con precedente

🔥 **Caso fundacional:** `replace({'{year}': x})` con un hash, una forma perfectamente válida
en Twig estándar, voló el footer completo. El tema usa `replace(buscar, reemplazo)` con **dos
argumentos** en sus 98 apariciones, y esa es la única forma que acepta *[MC, antes de 2026-09-03]*. Otro
tema lo volvió a pagar: un `| replace({'{1}': x})` adentro de un embed mató el pie del drawer
de filtros *[GG]*.

**Antes de usar un filtro, una función o una forma de argumento, verificá que ya aparezca en
el tema:**

```bash
grep -rn "| miFiltro" --include="*.tpl" .
```

Si no tiene precedente, no lo uses. Tres corolarios:

1. **Verificá el precedente de la FORMA DEL ARGUMENTO,** no solo el nombre del filtro.
2. **Un precedente en una línea que puede no ejecutarse, detrás de condiciones, no es
   precedente:** nadie comprobó que corra. Ejemplo: `merge([{ … }])` aparece en
   `blocks/timer-products.tpl` del base, pero en la rama que arma los productos de ejemplo del
   editor.
3. ✅ **El precedente también puede estar en OTROS temas del disco.** El estudio tiene decenas
   de temas de Tienda Nube de otros clientes. Un `grep -rl "loQueBusco" <carpeta-de-temas>/*/
   --include="*.tpl"` cuesta un comando, y destrabó la lectura de metacampos después de tres
   vueltas fallidas: dos temas ya la tenían resuelta y corriendo en producción
   *[MC, antes de 2026-09-03]*.

### Estrenar una forma sin riesgo

- **Una auto-prueba temporal en una section de una página que no sea crítica.** Nunca la ficha
  ni el carrito:

  ```twig
  {# prueba: '{"k":"vale"}' | json_decode → debería imprimir "vale" #}
  <!-- probe: {{ ('{"k":"vale"}' | json_decode).k | default('FALLA') }} -->
  ```

  Si la section desaparece, el filtro no existe. Si imprime el valor, existe. Después se borra
  la sonda.
- Criterio: **una expresión que no pudiste verificar va detrás de un toggle opt-in con default
  `false`.** Con el toggle apagado, Twig no evalúa esa rama, así que no puede romper nada
  mientras nadie lo prenda *[GG]*.

## Dónde castiga un error

- 🔥 **En un snippet del layout, el castigo no es una section vacía: es un 500 en todo el
  sitio.**
  - `snippets/cart/cart-modal.tpl` se incluye desde `layouts/layout.tpl`, y un
    `[id] | get_products` ahí tiró **500 en todas las páginas** en cuanto el setting tuvo valor
    *[MC, antes de 2026-09-03]*.
  - Un include desde `layout.tpl` a un archivo que no existe también da 500 en todo el sitio.
    Así se cayó un borrador entero en el incidente del pull con `watch` (ver
    [Sync y reglas](03-sync-y-reglas.md)) *[GG 2026-09-23]*.
  - **Nunca estrenes un filtro u objeto desconocido en un snippet que cuelgue del layout.**
    Probalo primero en una section de una página que no sea crítica.
- ⚠️ **La regla vale igual para el código de diagnóstico,** que es donde más fácil se olvida.
  Tres volcados (`product.metafields | json_encode`, entre otros) metidos **dentro de
  comentarios HTML** rompieron la ficha de producto productiva *[MC, antes de 2026-09-03]*. **Un
  comentario HTML no protege nada: la expresión se evalúa igual.**
- **El síntoma que hay que reconocer:** si una section desaparece entera del DOM (ni siquiera
  queda el wrapper `.ns-section`, o `#MainContent` sale vacío), es un **error fatal de Twig**,
  no CSS ni una guarda de la section. La plataforma bufferea la section y descarta todo, así
  que **poner sondas adentro no sirve**: solo sirve bisecar borrando código.
- 🔥 **Tres atajos para no gastar ciclos de bisección** (una section caída costó cinco ciclos de
  push) *[GG 2026-09-18]*:
  - si el editor lista la section, el schema está bien y el error es de render;
  - si otra section dibuja cards de producto sin problema (la página 404 trae una), la cadena
    de la card queda descartada;
  - un push, un cambio.

## Comentarios: dos trampas que 500ean

**1 · Nunca un `{# … #}` ADENTRO de una etiqueta `{% … %}`.** Twig tokeniza los comentarios a
nivel de plantilla, no de expresión, así que un comentario entre dos claves del hash de un
`{% embed 'x' with { … } %}` es un **error de sintaxis**. Pasó en un snippet del layout, con
`watch` corriendo: 500 en toda la tienda, publicado al instante *[MC, antes de 2026-09-03]*.

Lo grave es que **el chequeo local de balance de tags dio verde**, porque arranca con
`re.sub(r'\{#.*?#\}', '', src)` y borra justo el comentario que rompe. Hace falta un chequeo
aparte:

```python
for m in re.finditer(r'\{%.*?%\}', src, re.S):
    if '{#' in m.group(0): print('ROTO en la línea', src[:m.start()].count('\n') + 1)
```

El comentario va **antes** de la etiqueta. Si hay que explicar un valor del hash, se saca a un
`{% set %}` arriba y en el hash queda la variable sola.

**2 · Los comentarios NO SE ANIDAN.** El `{#` de apertura se cierra en el **primer** `#}` que
aparece, así que un `{# … #}` citado dentro de otro comentario parte el bloque, y **todo lo
que sigue pasa a ser código vivo**. Pasó en un comentario de cabecera que traía un ejemplo de
uso: dejó un `{% endblock %}` y un `{% endembed %}` sueltos, la section **no renderizaba
nada**, y se llevó puestas dos páginas. Hicieron falta seis ciclos de bisección para
encontrarlo *[MC, antes de 2026-09-03]*.

- ⚠️ **La variante leve:** un comentario que solo *menciona* `{#` o `#}` no rompió el render,
  pero **imprimió el resto del comentario en el HTML de todas las páginas** *[MC 2026-08-24]*.

**Regla: nunca escribas `{#` ni `#}` adentro de un comentario, ni siquiera citándolos.**

```python
i = 0
while (a := src.find('{#', i)) >= 0:
    b = src.find('#}', a + 2)
    if b < 0 or '{#' in src[a+2:b]: print('ROTO en la línea', src[:a].count('\n') + 1)
    i = b + 2
```

Dónde van estos chequeos en la rutina de verificación está en
[Verificación y QA](15-verificacion-y-qa.md).

## Valores que no son lo que parecen

### `| default()` trata el 0 y el `false` como vacíos

`{{ settings.x | default(7) }}` devuelve **7 cuando `settings.x` es 0**: el filtro usa el test
`empty`, y en Twig el `0` es vacío igual que el `null`.

- Para cualquier setting numérico donde el 0 sea un valor real (`padding: 0`, `gap: 0`,
  `delay: 0`, `opacity: 0`, una frecuencia de "cada 0 días") va **`settings.x ?? 7`**. Tiene
  precedente: `{% set overlay = layout.overlay ?? true %}` en `snippets/modals/modal.tpl`.
- ⚠️ **Lo mismo rompe los toggles cuyo default es `true`:** un `false` guardado cuenta como
  vacío y lo vuelve a prender. La forma correcta, tomada de `sections/footer.tpl`, es
  `{% set menus_open_mobile = section.settings.menus_open_mobile ?? true %}` *[MC 2026-09-11]*.
  Al revés, un toggle con default `false` no lleva `?? true`.
- ⚠️ **`??` solo cae al default cuando el valor es `null`.** Un `section.settings.show_coupon ?? true`
  no rescató un default de schema que no llegaba, porque el valor no llegaba como `null`
  *[MC 2026-08-27]*. Sirve para el 0, el `false` y las claves ausentes, no como remedio del
  "default que no llega" (ver [Schema y traducciones](06-schema-y-traducciones.md)).
- Para strings y para números donde el 0 no es válido, `| default()` está bien.

### Los tipos de la plataforma

- 🔥 **`product.tags` devuelve OBJETOS, no strings.** `tag starts with 'x'` y `'x' in tag` dan
  `false` sin error. Los filtros castean solos y los operadores no, así que hay que castear
  antes de comparar: `(tag ~ '') starts with 'order-'`. Conviene sospechar lo mismo de
  cualquier colección de la plataforma ✅ *[MC 2026-09-14]*.
- 🔥 **`in` sobre un STRING busca un substring; `in` sobre un ARRAY busca pertenencia.** Con
  `option.name in variant_label`, la "L" matcheaba adentro de "CELESTE" y el carrito mostraba
  un talle que el comprador no había elegido. Se compara por partes y por igualdad, o con `in`
  contra un array. Nunca con `in` sobre un string compuesto ✅ *[MC 2026-09-17]*. El formato
  real de ese rótulo está en [Producto, carrito y búsqueda](09-producto-carrito-busqueda.md).
- ⚠️ **`option.id` es el NOMBRE de la opción** (`"CRUDO"`, `"L"`, hasta `"-"`), **y
  `variation.id` es el ÍNDICE** (0, 1…) ✅ *[MC 2026-09-09]* ✅ *[GG 2026-09-24]*.
  - `variation.id == 0` es falsy: nunca `{% if variation.id %}`.
  - 🔥 Del `option.id` dependen el `value` del POST, los `data-option` y la comparación contra
    `data-variants`. Se limpia solo el rótulo visible; si cambia el id, los chips quedan
    deshabilitados sin error *[MC 2026-09-10]*.
- ⚠️ **El `id` que guarda un `product_list` es un string** y `category.id` es un número: se
  normalizan los dos lados con `~ ''` (ver [Schema y traducciones](06-schema-y-traducciones.md)).
  Contra un hash propio, `attribute(map, option.id ~ '')` tiene precedente *[MC]*.
- ⚠️ **Twig no ve la query string.** `category.url` sale absoluta y sin query *[MC 2026-09-15]*,
  y `product.url` también sale absoluta *[MC 2026-09-10]*.
- Criterio: `customer.email` es el único identificador de cliente con el que conviene contar en
  Twig. `customer.id` no está documentado *[MC 2026-09-10]*.

## Nulls y excepciones

- 🔥 **Un `for` sobre `null` vacía el render entero, sin rastro.** Pasó con la card y con el
  layout. Todo `for` sobre datos de la plataforma que pueden faltar va con `| default([])`:
  `product.tags`, `cart.items` con el carrito vacío, `item.product.category`,
  `product.variants` *[MC 2026-08-28]*.
- 🔥 **Llamar a un método sobre un objeto que no existe en esa plantilla vacía la section.**
  Pasó con `category.subcategories(false)` en `/search`, sin ningún error. Leer una
  **propiedad** sí es seguro: `sort-by.tpl` hace `category.sort_method` en `/search` y
  funciona. El método va detrás de `template == 'category'` *[MC 2026-09-18]*.
- ⚠️ **Dividir por cero tira la section** (el motor corre sobre PHP 8). Si una setting numérica
  puede valer 0 y se usa como divisor, se topea en 1 antes de dividir. Si no, se cae la card o
  la columna de la ficha sin ningún síntoma. Lo mismo vale para `+ 0` o `| round` sobre un
  string escrito a mano. Se anotó como preventivo, no llegó a pasar *[MC 2026-09-16]*.
- ⚠️ **Una variable que no existe puede tirar una excepción.** Una variable que quedaba sin
  setear con un toggle apagado, en un snippet del layout, es un 500 en todo el sitio. Regla:
  toda variable que se lea después se inicializa **afuera** del `if` *[MC]*.

## Scoping: `include`, `embed` y `for`

### `{% include %}` sin `only` filtra todo el contexto

En Ipanema los includes van **sin `only`**, así que el snippet incluido ve **todas las variables
`{% set %}` del archivo que lo llama.** Si una comparte nombre con una que el snippet consume,
la pisa, y no hay error: el snippet toma otra rama y sale mal renderizado.

- **Caso:** un `{% set image_height = … %}` local le ganó al de `snippets/image.tpl`, que decide
  si ya conoce las dimensiones con `{% if not image_width and not image_height %}`. Resultado:
  el `<img>` salía **sin `src`** *[MC, antes de 2026-09-03]*.
- **Antes de nombrar un `{% set %}` en un archivo que incluye snippets,** listá los
  identificadores que esos snippets leen:

  ```bash
  grep -o "\bimage_[a-z_]*\b" snippets/image.tpl | sort -u
  ```

  El prefijo `image_*` es el más peligroso, porque lo consume `image.tpl` y lo incluye medio
  tema.
- 🔥 **Nunca llames `settings` a una variable local.** Sombrea el global, y la card pierde
  cuotas, muestras de color y quick shop sin ningún error *[GG]*. Por lo mismo, un parámetro de
  `{% embed %}` no se llama `settings`.
- ⚠️ **Tampoco uses nombres que la plataforma ya usa.** Un parámetro `variant` choca con la
  variante del producto: se compara contra un objeto y el snippet cae a otra rama (se renombró
  a `coupon_variant`) *[MC]*. Y `snippets/icon.tpl` escribe el tamaño inline si le llega un
  `size`, aunque sea heredado: hay que pasarle `size: null` explícito *[MC 2026-09-16]*.
- ⚠️ **Un parámetro `null` de `{% embed %}` pisa la variable del que llama en todo el bloque.**
  Con `icon_name: null` (para que el snippet no dibujara su ícono), la fila cayó al ícono del
  tema base. La salida es guardar el valor del que llama en otra variable **antes** del embed
  *[MC 2026-08-28]*.
- ⚠️ **Hay snippets que usan variables que heredan y no definen.**
  `payments/payments-details.tpl` itera `installments_info` sin definirla: la hereda de
  `product-form.tpl`. Incluido desde otro lado, abre vacío y sin error *[MC]*.
- ⚠️ **Al incluir un block desde una section, pasale todo lo que lee del contexto,** aunque
  vaya en `null` *[GG]*.

### Los acumuladores se declaran ANTES del `for`

Twig cierra cada `for` con `array_intersect_key($context, $_parent) + $_parent`: **una variable
creada adentro del loop se descarta al salir**, y una que ya existía conserva el valor
modificado.

```twig
{% set card_index = 0 %}
{% for product in products %}
  {% set card_index = card_index + 1 %}
{% endfor %}
```

- ⚠️ **En `{% for x in lista if cond %}`, `loop.index` cuenta las iteraciones que pasaron el
  filtro,** no la posición real en la lista. Si hace falta la posición, el `if` va adentro del
  `for` y el contador se declara antes ✅ *[MC 2026-09-08]*.
- ⚠️ **Filtrá la lista ANTES del loop, no salteando ítems adentro.** Si el separador lo escribe
  el ítem anterior, usá `loop.last` y no un flag del dato (`crumb.last`). Y si no sobrevive
  ningún ítem, volvé a la lista original: un JSON-LD con una coma colgando es inválido
  *[MC 2026-09-17]*. Filtrar la lista de cada section antes de contar es un patrón completo,
  en [Patrones](14-patrones.md).
- 🔥 **Un banner intercalado en la grilla falló dos veces,** primero con un `for` sobre
  `section.blocks` dentro del loop de productos, y después con `grid_banners[loop.index]` sobre
  un hash vacío. La salida fue una section aparte *[GG 2026-09-18]*.

### Factorizar: qué se puede compartir entre archivos

- ⚠️ **Un `{% include %}` abre un scope propio y sus `{% set %}` no vuelven.** Y los macros del
  tema se usan **solo con `_self`**, en el mismo archivo: importar un macro de otro archivo no
  tiene precedente. Cuando dos archivos necesitan el mismo cálculo (resolver el hex de un color,
  una categoría desde un metacampo), **hay que duplicarlo y anotarlo** *[MC, antes de 2026-09-03]*.
- ✅ **Un include sí puede "devolver" un STRING.** El snippet lo imprime con un protocolo de
  separadores, y el que lo llama lo captura con un `set` de bloque. Corrige el "no se puede
  factorizar" del handoff viejo *[VZ 2026-09-24]*:

  ```twig
  {% set vzb_parsed %}{% include 'snippets/blog/vz-post-tags.tpl' %}{% endset %}
  {% set vzb_parsed_tags = vzb_parsed | trim | split(']') | first %}
  ```

  El snippet imprime `Lectura|Rituales]Título`. En otro tema se había anotado que capturar con
  `{% set %}…{% endset %}` no tenía precedente *[MC]*: la medición de VZ es posterior.
- Lo que **sí** se puede compartir es *markup con un hueco*, con `{% embed %}` + `{% block %}`:

  ```twig
  {% embed 'snippets/account-split.tpl' with { current: 'login', … } %}
    {% block account_form %} … {% endblock %}
  {% endembed %}
  ```

## Metacampos

- 🔥 **`attribute()` sobre `product.metafields` BORRA la section entera.** Para leer un
  metacampo cuyo nombre viene de un setting, da tentación armar el acceso en runtime, pero
  `attribute(product.metafields, ns)` **hace desaparecer la section del DOM, wrapper incluido,
  sin ningún error visible**. Costó cuatro ciclos de bisección, porque el síntoma es idéntico al
  de "no hay productos" *[MC, antes de 2026-09-03]*.
- 🚫 **El subíndice tampoco.** `product.metafields[ns]` es un acceso de *array* y `metafields`
  es un **objeto** de la plataforma: nunca tira error y **siempre devuelve null**. Es la peor
  combinación, porque el `| default()` tapa el null y la pieza cae en silencio a su respaldo.
- ✅ **La forma que funciona es el acceso LITERAL con punto, protegido con `| default()`.** El
  valor se usa directo: es un string, no hace falta `.value` *[MC, antes de 2026-09-03]*:

  ```twig
  {% set value = product.metafields.pdp.cuidados_detalles | default('') %}
  ```

  El `default` no es cosmético: es lo que evita la excepción cuando el producto no tiene ese
  metacampo, porque el filtro sobre una **expresión simple** se compila con un test de
  definido en vez de evaluar el acceso a secas. Por eso a `attribute()` no se lo rescata
  envolviéndolo: sobre una **llamada a función**, el filtro evalúa el argumento primero.
- ✅ **La CLAVE sí puede ser dinámica si se recorre un namespace literal.**
  `{% for key, value in product.metafields.pdp %}` lista todas las claves del namespace con su
  valor (un string), y un namespace que el producto no tiene se recorre vacío, sin error, con
  `product.metafields.otro | default([])` *[VZ 2026-09-24]*. Lo usa `blocks/product-accordion.tpl`
  para resolver `[namespace.key]` dentro de un texto:

  ```twig
  {% for mf_key, mf_value in product.metafields.pdp | default([]) %}
  ```

  🚫 Recorrer `product.metafields` entero, para tener el namespace dinámico, **tira la section**
  igual que `attribute()`.
- **El costo:** el namespace no puede ser configurable. Hay que escribir una cascada de accesos
  literales por namespace conocido (`pdp`, `custom`) y agregar uno nuevo a mano.
- Criterio, por censo, sin medir: **`product.metafields` no llega en un listado.** En los
  temas del estudio, todos sus usos están en la ficha de producto. Y `category.metafields` no
  existe *[MC 2026-09-14]*. Cómo se cargan los metacampos (no hay interfaz en el panel) está en
  [Límites y Admin API](13-limites-y-admin-api.md).
- ⚠️ **`attribute()` sí funciona sobre hashes de Twig que armás vos.** Hay que recordar que las
  claves de un hash van como **string** (`'pos5'`): con una clave numérica, `attribute()` no
  encuentra nada, y no hay error.

## Media y video de producto

- 🔥 **`media.next_video` es el que CREA el token que devuelve `media.uid`.** Si leés `uid`
  antes que `next_video`, da vacío. `media.render` mete ese uid en el `id` del iframe, así que
  las cards salían con `id="video-"` repetido y los iframes se cruzaban. Hay que leer
  `next_video` a una variable antes del render: `product-video-item.tpl` del base funciona solo
  por el orden de sus líneas ✅ *[MC 2026-09-18]*.
- ✅ **Un video de la galería no expone ningún texto.** Se probaron unas 25 propiedades (`alt`,
  `name`, `filename`, `title`…) y todas vienen vacías *[MC 2026-09-18]*.
  - `resolve_media` sobre su `uid` o su `id` devuelve NULL.
  - Lo que sí expone: `id`, `position`, `dimensions`, `thumbnail`, `render`, `next_video` e
    `isImage`/`isVideo`.
  - Cualquier dato del video (el color, por ejemplo) va en una etiqueta del producto.
  - `product.images` no incluye los videos.

  Las imágenes, en cambio, sí traen el alt SEO automático (ver
  [Producto, carrito y búsqueda](09-producto-carrito-busqueda.md)).

## Comparar URLs y parsear strings

- ✅ **Las URLs se comparan por el handle, el último tramo:**
  `url | trim('/') | split('/') | last`, que tiene precedente en `product-variants.tpl`
  *[MC 2026-09-17]*. 🔥 Con "una URL contiene a la otra", la categoría madre, que se recorre
  primero, se roba el match de todas sus hijas. Contra una página se compara con
  `page.handle` *[MC]*.
- ⚠️ **Un `slice` de string no tiene precedente.** Para parsear un `clave=valor`, la forma usada
  es `split('=')` + `slice(1) | join('=')` **sobre el array**, que sí lo tiene. Con separador `:`
  y un valor que es una URL, `| last` rompe con el `:` de `https://` (devolvía `//x.png`): va la
  misma técnica, `split(':')` + `slice(1) | join(':')` *[MC 2026-09-04]*.
- Para distinguir un hex de una URL alcanza con `starts with 'http'` *[MC 2026-09-04]*.
- Criterio: **ordenar por una clave calculada sin `| sort`, con selección por rondas.** Se
  elige el más cercano, se lo saca del conjunto y se repite N veces. `| abs` se reemplaza con
  un ternario. Para ordenar strings, padding fijo (`001000`) y comparación como string
  *[MC 2026-09-14]*.
- `{{- … -}}` saca los espacios de alrededor, por ejemplo para que un salto de línea no se
  cuele antes de un `:` *[MC]*.

## Formas con y sin precedente

Estado por proyecto. "Con precedente" quiere decir que corre en un tema real, no que esté
documentado.

| Forma | Estado | Fuente |
|---|---|---|
| `replace(a, b)` con dos argumentos | ✅ con precedente | MC |
| `{% for x in y if cond %}` | ✅ con precedente (ojo con `loop.index`) | MC |
| `{% for i in 1..N %}` | ✅ con precedente | GG |
| `\| json_decode` | ✅ verificado en otro tema + auto-prueba en vivo | MC |
| `\| json_encode`, `\| date('U')`, `matches` con regex | ✅ con precedente | MC |
| `\| trim`, `\| lower`, `\| split`, `\| last`, `\| first`, `\| length`, `\| join`, `\| slice` sobre arrays | ✅ con precedente | MC |
| `\| flatten_categories_by_id`, `\| add_param`, `\| block_attributes`, `\| static_url` | ✅ con precedente | MC |
| `\| setting_url` | ✅ solo sobre el valor de un setting, nunca sobre un literal | MC 2026-09-14 |
| `\| merge([obj])` para juntar objetos de la plataforma en un array | ✅ con precedente. Como valor de un hash, sin verificar: arrays paralelos | MC 2026-09-14 |
| `attribute(hash_propio, clave ~ '')` | ✅ con precedente | MC |
| `{% set x %}{% include … %}{% endset %}` | ✅ medido en VZ | VZ 2026-09-24 |
| `product.default_options[variation.id]` | ✅ funciona y ya refleja el `?variant=` de la URL | MC 2026-09-10 |
| `product.variants` con `\| default([])`; de cada variante, `id`, `image`, `option1/2/3`, `stock` | ✅ se usa (corrige al handoff viejo, que lo daba por no verificable) | MC 2026-09-11 |
| `product.variations`, `variation.options \| length` | ✅ con precedente | MC |
| `complementary_product_list`, `product.metafields.related_products.alternative_product_ids \| get_products` | ✅ con precedente en Ipanema 1.2.2 | VZ 2026-09-24 |
| `product.maxPaymentDiscount`, `order.order_status_url`, `settings.payments`, `store.has_shipping`, `store_has_passwordless_login`, `page.content` | ✅ con precedente en Ipanema 1.2.2 | VZ 2026-09-24 |
| `has_applied_filters`, `has_products`, `query`, `parent_category`, `sections.primary`, `store.whatsapp`, `\| payment_new_logo` | ✅ con precedente (`has_products` da falso en una tienda vacía con productos de ejemplo) | MC |
| `category.subcategories(false)` | ⚠️ solo en `template == 'category'` | MC 2026-09-18 |
| `merge([{ … }])`: un array literal de hashes | ⚠️ precedente débil: solo en la rama del editor de `timer-products.tpl` | MC |
| `replace({...})` con un hash | 🚫 rompe | MC · GG |
| `\| filter(...)`, `\| sort`, `\| abs`, `\| url_encode` (en JS va `encodeURIComponent`), `\| upper` (va `text-transform`) | 🚫 sin precedente | MC |
| `\| get_products` sobre un array literal o sobre un string | 🚫 la section desaparece. El único uso con precedente es el de `alternative_product_ids` | MC 2026-09-07 |
| `\| product_image_url` sobre un hash de Twig | 🚫 sin precedente | MC |
| `replace` con regex | 🚫 sin verificar | MC |
| `slice` de un string | 🚫 sin precedente: `split` + `slice` + `join` sobre el array | MC |
| `attribute(product.metafields, …)`, `product.metafields[ns]`, recorrer `product.metafields` entero | 🚫 tira la section o devuelve null | MC · VZ |
| `product.custom_fields`, `category.metafields` | 🚫 no existen | MC |
| `product.price_without_taxes` | ⚠️ depende de que la tienda lo active: se calcula en el tema, precio ÷ (1 + IVA) | VZ 2026-09-24 |
