# Límites de la plataforma y Admin API

Qué no se puede hacer en un tema Ipanema, para no prometerlo en una estimación. Qué sí se puede
con una app propia o de terceros. Y las trampas de la Admin API que se midieron en los proyectos.

## Lo esencial

- **Antes de estimar una feature del boceto, mirá la tabla de abajo.** Favoritos, aviso de stock,
  login social, nota en el carrito, adjuntos en el contacto: cada uno tiene un estado medido.
- **Dos cosas que el handoff viejo daba por imposibles sí se pueden.** La wishlist se hace en el
  tema; hace falta una app propia solo si se quiere multi-dispositivo. El "Avisame cuando haya
  stock" lo cubre la app stocknube.
- **El token del CLI (`.nuvem`) también sirve para la Admin API, con scopes acotados:** no tiene
  acceso a clientes. Se decodifica dentro de un script y nunca se imprime.
- **Los scopes de una app quedan congelados en el token.** Agregar uno en el Partners Portal no
  alcanza: hay que volver a autorizar.
- 🔥 **Crear o publicar páginas por API las suma al menú principal de la tienda en vivo**, y no hay
  API de menús para sacarlas.
- **Las escrituras de la API reemplazan más de lo que parece** (el `PUT` de tags reemplaza el set
  entero), **y las lecturas son más lentas de lo que parece** (`variants`).
- Lo que no se puede, se dice al estimar. Lo que depende de un dato del Admin, se le dice al
  comerciante.

## Lo que no se puede, y lo que cambió

Todo esto se intentó. La tabla del handoff viejo va actualizada.

| Pedido | Estado |
|---|---|
| **Favoritos / wishlist** | ✅ **Se puede en el tema** *[MC 2026-09-10]*. La plataforma no tiene flujo nativo, pero se resuelve entero en el storefront: la lista va en `localStorage` con lápidas (`removed_at`) y gana la última escritura; al tocar el corazón se captura el `outerHTML` de la card, saneado; y la ficha emite su propia card en un `<template>` como respaldo para otro dispositivo. Para multi-dispositivo y métricas (ranking, conversión) hace falta una app propia como espejo opcional ([apps propias](16-multipais-apps-integraciones.md)). El JS está en [JavaScript](11-javascript.md) |
| **"Avisame cuando haya stock"** | ✅ **Lo cubre una app de terceros, stocknube** *[MC 2026-09-11]*. El tema dibuja un control propio (un sobre al lado del talle agotado) y le pasa el click al botón de la app. El contenedor de la app se corre fuera de pantalla y nunca va a `display: none`, porque eso le mata el `<dialog>` ([plataforma](08-plataforma.md)). Integración propia sin app sigue sin existir |
| **Login social (Google / Facebook / Apple)** | 🚫 La plataforma no expone OAuth de esos proveedores al storefront. Lo más parecido es `store_has_passwordless_login` (código por mail), que es otra cosa y **reemplaza el formulario entero** |
| **Elegir UN producto desde el editor** | 🚫 No hay `setting_type` de producto único: solo `product_list`, y se toma `\| first`. Reconfirmado *[MC 2026-09-07]*: un `product_id` pasado por `\| get_products` sobre un string hizo desaparecer la section ([Twig](07-twig.md)) |
| **Metacampos de producto desde el panel** | 🚫 Medido *[MC, antes de 2026-09-03]*: `product.metafields` devuelve `{}`. No hay interfaz: se cargan por API (`POST /metafields`, `owner_resource: Product`) o con una app. `product.custom_fields` **no existe** |
| **`extra[key]` en el registro de cliente** | 🚫 🔥 **La documentación oficial está mal.** Medido con un alta real *[MC 2026-08-28]*: el POST del registro manda `extra[compra_asistida]`, el cliente se crea y `extra` queda `{}`. `PUT /customers/{id}` con `extra` responde 200 y lo ignora; `POST /customers` con `extra` sí lo guarda, así que es de escritura única al crear por API. Un custom field de `customers` tampoco se renderiza en el form de registro. La salida fue un endpoint propio que escribe un **custom field** ([apps propias](16-multipais-apps-integraciones.md)) |
| **Campo de nota / instrucciones en el carrito** | 🚫 El POST del carrito no tiene ningún campo de nota documentado. Un `name` inventado hace que el comprador escriba algo que se pierde en silencio |
| **Adjuntar un archivo en el formulario de contacto** | 🚫 La ruta de contacto acepta `name`, `phone`, `email`, `message`, `product` y `type`, nada más, y no acepta `multipart`. La salida es subir el archivo a un servicio propio y mandar la URL dentro del mensaje ([servicio de archivos](16-multipais-apps-integraciones.md)) |
| **Registrar una clave nueva en `config/sections.txt`** | 🚫 Probado con el tema publicado *[MC, antes de 2026-09-03]*: el Admin siguió listando solo las 5 del tema base. Además, *[GG 2026-09-23]* "Organizar productos → Destacar" lista las claves del tema **publicado**: mientras Ipanema es borrador, sus claves `timer_offers` y `featured` no se pueden cargar desde el Admin, y leer los archivos de un tema legacy por API da `422 THEME_NOT_SECTIONABLE` |
| **Tags de cliente** | 🚫 El único `tags` de la API es el de Location |
| **El precio de cada variante en la card** | 🚫 No hay `variant.price` con precedente en Twig, así que una card por color no puede mostrar el precio de ese color. Las formas de `variant` con precedente son `id`, `image`, `option1/2/3` y `stock` *[MC]* |
| **Una galería por color** | 🚫 No hay relación variante→galería: `variant.image` es una sola foto, y nunca viene vacía ([producto](09-producto-carrito-busqueda.md)). Un carrusel por color funciona solo con alts escritos a mano ([patrones](14-patrones.md)) |
| **Forzar un precio o un "regalo a elección"** | 🚫 El tema no fija precios. La promoción de regalo por umbral la agrega la plataforma sola; un regalo a elección solo se hace cargando un producto a $0 *[MC]* |
| **Saber barato si un producto ajeno está disponible** | 🚫 Medido *[MC 2026-09-08]*: un `HEAD` a un producto despublicado responde **200** con la página de 404 adentro. El `GET` de la página pesa ~790 KB y tarda ~1,4 s. `/search` pesa ~359 KB e ignora el `limit`. `category.products` trae `has_stock` pero topea en 12, así que la ausencia de un handle solo prueba algo si la lista trae menos de 12 |
| **Escribir el orden manual de una categoría por API** | 🚫 Medido *[MC 2026-09-04]*: el recurso Category no tiene campo de orden, y nueve rutas candidatas de reorder dan 404. Se **lee** con `GET /products?category_id=X&sort_by=user`. El workaround está en "Admin API" (re-insertar) |
| **Categorías o tags en el blog** | 🚫 Medido *[VZ 2026-09-24]*: la Blog API `2025-03` expone título, resumen, SEO, handle, contenido y portada; ni categorías ni tags. VZ las escribió entre corchetes al principio del título (`[Lectura] Título`) y las parsea el tema; el título SEO se carga sin corchetes, porque de ahí salen el `<title>`, el `og:title` y el `headline` |
| **Crear o editar menús por API** | 🚫 No hay API de menús *[VZ 2026-09-24]*: se crean y se ordenan a mano en Tienda online › Menús |
| **Buscar un pedido por número + e-mail, sin sesión** | 🚫 No existe una búsqueda pública *[VZ 2026-09-24]*. Con sesión, el tema lista los pedidos de la cuenta; sin sesión, VZ manda una consulta por la ruta de contacto |
| **Videos en la biblioteca de medios** | 🚫 La biblioteca no guarda videos, y `video_url` solo acepta YouTube/Vimeo: un `.mp4` va en un setting de texto ([schema](06-schema-y-traducciones.md)) |
| **Una lista "Más vendidos"** | 🚫 El Admin solo ofrece las listas de `sections.txt` (Destacados, Novedades, Ofertas…). Si la lista elegida está vacía, la section no se dibuja y parece que no estuviera *[VZ 2026-09-24]* |
| **Instagram sin token** | 🚫 La section de Ipanema sale con placeholders *[VZ 2026-09-24]* |
| **Buscar con varias palabras o por "ámbitos"** | 🚫 Medido *[GG 2026-09-25]*: el buscador ignora las palabras de más, con "en" devuelve 0, y una categoría no acepta `?q=`. No hay forma honesta de ofrecer "buscar en esta categoría" |
| **Una cuenta de prueba por API con el token del CLI** | 🚫 `GET /customers` da 403 (`Missing required scope: read_customers`) *[VZ 2026-09-24]*. El QA de las páginas de cuenta logueada necesita credenciales reales del dev, y el registro tiene reCAPTCHA |

Dos cosas que existen pero funcionan distinto de lo esperado (la búsqueda por SKU solo con el
código completo, y `category.products` que trae solo los productos directos) están en
[producto, carrito y búsqueda](09-producto-carrito-busqueda.md).

## Admin API: lo medido

Lo que sigue complementa a la skill `nube-skills-admin` (guardarraíles, dry-run, backup y
confirmación antes de escribir): son las trampas que aparecieron usándola en proyectos reales.
Cómo se invoca la skill: [skills](02-skills.md).

### El token del CLI sirve, con límites

- ✅ **`.nuvem` es un JSON en base64**, y su `theme-api.publicApiToken` junto con
  `theme-api.storeId` funcionan como token de la Admin API *[VZ 2026-09-24]*:
  - responden `200`: `GET /store`, `/products`, `/categories`, la Blog API completa (crear, `PUT`,
    `DELETE`, `/posts/media`, `/posts/thumbnail` como multipart con `curl -F`) y Pages;
  - `GET /store?fields=features` da `422` (campo no permitido para este token);
  - `GET /customers` da `403`.
- **Cómo usarlo:** decodificarlo adentro de un script, para que el token nunca aparezca en la
  terminal ni en el transcript. Se le pasa a `tn-api.py` de `nube-skills-admin` por
  `TN_ACCESS_TOKEN`. En la máquina no hay variables `TN_*` cargadas.
- 🚫 **Nunca un token en `permissions.allow` de un `settings.json`**, ni en un comando que quede
  escrito. Pasó: un `curl` con el token de la Admin API quedó en texto plano en los permisos
  permitidos. Se borra y se rota el token.
- ⚠️ **Es una escritura sobre la tienda viva, no sobre el borrador del tema.** Las páginas, los
  posts y los productos que se crean por API los ve también el tema publicado.

### Los scopes quedan congelados en el token

✅ Agregar `read_orders` a una app en el Partners Portal no cambia los tokens que ya se emitieron:
la API siguió respondiendo `403 Missing required scope: read_orders` *[MC 2026-09-10]*. Para que
el scope nuevo llegue, el comerciante vuelve a autorizar la app en
`https://www.tiendanube.com/apps/<app_id>/authorize`.

### Pages API

- ✅ Medido *[VZ 2026-09-24]*:
  - el listado solo responde con `per_page` menor que 20; con más, da `400`;
  - `POST /pages` necesita
    `{"page": {"publish": true, "i18n": {"es_AR": {"title", "content", "seo_handle", "seo_title", "seo_description"}}}}`;
  - con `"es"` como clave falla con "El título no puede estar vacío", y la respuesta vuelve con la
    clave `es`;
  - `PUT /pages/{id}` con solo `{"publish": true}` da `500`; con el cuerpo `page.i18n.es_AR`
    completo (reenviando título y contenido actuales) funciona y publica;
  - una página sin publicar da 404, incluso en la preview del tema;
  - el objeto página no tiene campo de plantilla: la plantilla alternativa se asigna a mano en el
    Admin ([plantillas](12-plantillas.md)).
- 🔥 **Crear o publicar páginas las suma al menú principal** *[VZ 2026-09-24]*. Después de crear
  6 páginas por API y de que el dev les asignara plantilla, todas aparecieron en el menú
  `navigation`, que alimenta el menú lateral del header, las columnas del footer y **la tienda en
  vivo**. No hay API de menús: hay que avisarle al dev **antes** de crear páginas, para que saque
  los ítems a mano en Tienda online › Menús.

### Blog API

✅ Medido *[VZ 2026-09-24]*:

- **El autor del post es el `User-Agent` de quien lo crea.** VZ creó los posts con
  `User-Agent: VZ` para que el autor fuera la marca; con el mail del dev en el User-Agent, el
  autor era el mail.
- **La plataforma le agrega al handle los últimos 12 caracteres del id del post**, aunque la API
  reciba otro handle. Cambiar el título con un `PUT` que mantiene el `handle` no cambia el handle.
- **El listado se ordena por fecha de creación.** Un `PUT` con `published=true` re-publica y cambia
  `published_at`, pero el orden no se mueve. La plataforma sirve 12 posts por página.
- **La portada no se redimensiona:** el CDN del blog sirve la misma URL en todo el `srcset`. Se
  sube ya en el tamaño final (VZ: 2000 px, JPEG al 84).

### Productos

- ✅ **Pedir `variants` es el cuello de botella, y no por el peso** *[MC 2026-08-28]*. Con 200
  productos por página:

  | Pedido | Tiempo | Peso |
  |---|---|---|
  | sin `variants` | 0,65–0,75 s | 36 KB |
  | con `variants.stock,variants.sku` | 16,4–18,0 s | 248 KB |
  | con `variants` completo | 20,7–21,4 s | 8,6 MB |

  Pedir solo dos campos de `variants` baja el payload 35 veces y no mejora el tiempo: es costo del
  servidor. Por eso `fields=` no alcanza. Un listado no pide `variants`, y el stock de las filas
  visibles se trae en una segunda pasada con `ids=…`.
- ✅ **`q=` busca por nombre y por SKU, no por id** *[MC 2026-08-28]*: `q=<id>` devuelve 0. Una
  búsqueda numérica tiene que disparar además un `GET /products/{id}`.
- ⚠️ **Una categoría con un múltiplo exacto de 100 productos** da 404 `"Last page is N"` en la
  página siguiente *[MC 2026-09-15]*. `tn-api.py` tolera ese 404 como fin de colección.
- ⚠️ **`PUT /products/{id}` con `tags` reemplaza el set completo** *[MC 2026-09-14]*. Para agregar
  o sacar un tag hay que leer el producto inmediatamente antes (read-modify-write), o se pisan los
  tags que puso otro. Y el buscador indexa los tags por palabra completa: un prefijo común en
  tags internos (`order-…`) le trae medio catálogo a quien busque esa palabra
  ([producto, carrito y búsqueda](09-producto-carrito-busqueda.md)).
- ⚠️ **`categories: []` deja el producto sin categoría** (omitir el campo no es lo mismo que
  mandarlo vacío). La app de gestión de MC, para sacar un producto cuya única categoría es la que
  está reordenando, lo estaciona un instante en una categoría oculta propia *[MC 2026-09-04]*.

### El orden manual de una categoría: re-insertar

✅ Medido *[MC 2026-09-04]*: **la posición en `sort_by=user` es el orden de inserción en la
categoría.** Un producto que se saca y se vuelve a poner queda último, así que re-insertando en
secuencia se materializa cualquier orden.

- ⚠️ Es comportamiento **observado, no documentado**: Tienda Nube no lo promete y puede cambiar sin
  aviso.
- ⚠️ **La categoría tiene que estar en "orden manual" en el panel** (Productos → Organizar). El
  criterio de orden (manual, más vendidos, precio) es una setting del panel que **no está en la
  API**: si la categoría está en "más vendidos", el orden se guarda y el storefront lo ignora.
  *[MC 2026-09-04]*: el primer "publiqué y no se ve" era exactamente esto. Para comprobarlo desde
  el storefront: `?sort_by=user`.

### Metacampos y custom fields

- ⚠️ **Vaciar un metacampo lo borra.** Tienda Nube no guarda valores vacíos: "sin valor" es "sin
  metacampo" *[MC]*.
- ⚠️ **`GET /customers/custom-fields/{id}/owners` sigue listando clientes borrados** *[MC]*: dos
  ids de la lista devolvían 404 en `GET /customers/{id}`. Si el listado se usa para algo
  operativo, hay que cruzarlo contra el cliente.
- Cómo lee el tema los metacampos (acceso literal, recorrer un namespace) está en [Twig](07-twig.md).

### Business Rules privadas: el dominio `logistic`

Para un cliente con muchos depósitos que quería una sola cotización de envío, Tienda Nube habilitó
el dominio **privado** `logistic` de Business Rules: en cada checkout le hace un `POST` a la app
con el carrito y el stock por location, y la app responde desde dónde sale cada ítem *[MC]*. Tres
trampas, las tres silenciosas:

- ⚠️ **El callback tiene 800 ms para responder.** Si tarda de más o responde algo inválido, Tienda
  Nube usa su materialización default: el checkout nunca se bloquea, pero el envío sale partido.
- ⚠️ **`event` va en singular al registrarlo** (`{ url, event: "logistic/materialize" }`). Los
  dominios públicos usan `events` en plural. Con la clave equivocada, el `PUT` se acepta y no llega
  nada nunca.
- ⚠️ **La respuesta lleva `detail.unmaterialized` siempre, aunque vaya vacío.** No estaba en la
  documentación: se descubrió probando. Sin ese campo la respuesta es inválida en cada checkout, y
  el síntoma es justo el que se quería evitar.
