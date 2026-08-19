# Mapa de la Admin API de Tienda Nube / Nuvemshop

Referencia de qué existe, con qué límites y bajo qué permisos. Todo lo que está acá sale de la
documentación oficial (`tiendanube.github.io/api-documentation`, versión `2025-03`). Lo que **no**
está documentado y sí sabemos por experiencia va marcado como **[observado]**; lo que directamente
no se puede afirmar va marcado como **[incierto]**.

> Regla dura: si un endpoint no aparece en este documento, tratalo como inexistente hasta
> comprobarlo contra la doc oficial. No inventes rutas por analogía con Shopify.

## Tabla de contenidos

1. [Base y versionado](#1-base-y-versionado)
2. [Autenticación](#2-autenticación)
3. [Tabla de recursos](#3-tabla-de-recursos)
4. [Límites duros](#4-límites-duros)
5. [Scopes](#5-scopes)
6. [Errores](#6-errores)
7. [Feature detection](#7-feature-detection)

---

## 1. Base y versionado

Toda URL tiene la forma:

```
{base_url}/{api_version}/{store_id}/{recurso}
```

| Región | `base_url` |
|---|---|
| Argentina, México y resto de LATAM | `https://api.tiendanube.com` |
| Brasil | `https://api.nuvemshop.com.br` |

Solo SSL. Ejemplo: `https://api.tiendanube.com/2025-03/123456/products`.

Los dominios de OAuth y del panel siguen la misma dualidad: cualquier URL bajo `tiendanube.com`
tiene su equivalente idéntica bajo `nuvemshop.com.br`.

### Versiones

| Versión | Estado | Cuándo usarla |
|---|---|---|
| `2025-03` | Estable, la que corresponde a esta doc | **Default de la skill.** Siempre esta. |
| `v1` | Estable heredada (más de 10 años de uso) | Solo integraciones viejas que todavía no migraron |
| `unstable` | Pre-release: acá aterrizan las features nuevas antes de estabilizarse | Solo para probar algo que no salió aún |

Datos del versionado que importan para decidir:

- El esquema es **date-based** (`YYYY-MM`). Una versión estable solo recibe bug fixes, parches de
  seguridad y mantenimiento; no recibe cambios experimentales.
- **`v1` no recibe features nuevas después del release `2025-03`.** Está textual en la doc: *"No new
  features will be introduced directly into the v1 stable release after the 2025-03 release"*.
- Tiendanube declara que **todavía no hay política de sunset** para las versiones estables. O sea:
  `v1` no tiene fecha de muerte publicada, pero tampoco futuro.
- El plan es una release estable por año, coordinada y anunciada.

**Consecuencia práctica:** para cualquier desarrollo nuevo, `2025-03`. Si un cliente tiene una
integración en `v1`, migrarla es deuda técnica con fecha abierta, no una urgencia — pero cualquier
feature nueva que pida va a estar solo en `2025-03` o `unstable`.

---

## 2. Autenticación

OAuth 2 en una forma restringida:

- **Único grant type soportado: `authorization_code`.** No hay client credentials, no hay refresh
  token, no hay password grant.
- El **`code` expira en 5 minutos**.
- **Los access tokens no expiran.** Solo se invalidan al obtener uno nuevo o si el merchant
  desinstala la app.
- Junto al token viene un **`user_id` que es el `store_id`**. Es el que va en la URL de todas las
  requests. Algunas respuestas lo devuelven como `store_id`.

### Flujo

1. El merchant instala la app desde su admin, o entra a `https://www.tiendanube.com/apps/{app_id}/authorize`.
2. Acepta los scopes (si ya los aceptó, se saltea).
3. Redirect a la *redirect URL* de la app con `?code=...&state=...`.
4. `POST https://www.tiendanube.com/apps/authorize/token` con `client_id`, `client_secret`,
   `grant_type=authorization_code` y `code` **en el body JSON**, nunca como query params (es el error
   más común documentado).

Respuesta: `{ "access_token": ..., "token_type": "bearer", "scope": "...", "user_id": "789" }`.

### Headers obligatorios

| Header | Cuándo | Detalle |
|---|---|---|
| `Authorization: Bearer {token}` **o** `Authentication: bearer {token}` | Siempre | **[verificado]** Los dos funcionan, en `v1` y en `2025-03`: se probaron seis variantes contra la API real y todas llegaron a la validación del token. Incluso la palabra del scheme es opcional y su capitalización es indistinta. Usá `Authorization: Bearer`, que es lo que muestra la doc de `2025-03`, y **no implementes fallback al otro header**: es código muerto. |
| `User-Agent: MiApp (mail@dominio)` | **Siempre** | Sin este header la API responde **`400 Bad Request`**. Debe llevar nombre de la app y un mail o URL de contacto. **[verificado]** El chequeo corre **después** de la autenticación: sin `User-Agent` y con token inválido la respuesta es `401`, no `400`. El `400` recién aparece con un token válido, así que un problema de `User-Agent` no se puede debuggear con un token malo. |
| `Content-Type: application/json; charset=utf-8` | POST / PUT / PATCH | Sin él, **`415 Unsupported Media Type`**. |

### Internacionalización

`name`, `description`, `handle` y los `values` de variantes son **objetos por idioma**
(`{"es": "...", "pt": "..."}`), incluso si la tienda tiene un solo idioma activo. En Page y Kit
también lo son `seo_title` y `seo_description`; en Product la doc los muestra como string plano. Al
escribir se puede mandar el objeto completo o **un string plano, que se aplica a todos los
idiomas**. El idioma principal de la tienda viene en el header de respuesta **`x-main-language`**:
leelo en vez de hardcodear `es`, porque en una tienda que solo tiene `pt` la clave `es` devuelve
`null` y el código se queda con campos vacíos sin ningún error.

### Tipo de app

- **Aplicación a medida**: el propio merchant la crea desde su admin (*Aplicaciones a medida →
  Crear*), elige los scopes y **obtiene el token en el momento**. Sin cuenta de partner, sin flujo
  OAuth y sin homologación — es el camino más corto para operar sobre la tienda de un cliente. Lo que
  hay que saber antes de prometerlo:
  - **Está gateado por plan**: en Argentina, Escala y Evolución; en Brasil, Escala y Next. En un plan
    menor la opción directamente no aparece en el admin.
  - El token **se muestra una sola vez**. Si se pierde, hay que reinstalar y se emite uno nuevo.
  - Recomendación oficial: **una app por integración** (ERP, BI, middleware) para poder revocar una
    sin cortar las demás.
  - **Agregar o editar permisos exige reinstalar la app**, y eso emite token nuevo.
- **App pública**: publicada en la App Store, pasa por homologación de Tiendanube.
- **App por link de instalación**: cualquier merchant la instala con el link aunque no esté
  publicada. No pasó por revisión técnica. Es la vía habitual para las apps propias de agencia y **la
  única cuando la tienda no llega al plan que habilita las aplicaciones a medida** (el link funciona
  en cualquier plan). *(En el Partner Portal esta modalidad aparece etiquetada como app "para tus
  clientes"; **[incierto]** la doc pública no usa ese nombre, solo describe el mecanismo del
  installation link.)*
- Reinstalar una app ya instalada **solo regenera el token**: no hay que recrear recursos (crearlos
  de nuevo genera duplicados en la tienda).
- **[incierto]** *"Cambiar los scopes obliga a reinstalar en cada tienda"*, **en apps de partner**
  (en las aplicaciones a medida está documentado que sí). La doc solo afirma que el token se invalida
  al pedir uno nuevo o al desinstalar. Lo consistente con eso es que un scope agregado no aparece en
  tokens ya emitidos y hace falta que el merchant vuelva a aceptar permisos. Verificable: agregar un
  scope en el Partner Portal y hacer un `GET` al recurso nuevo con el token viejo de una tienda demo.

---

## 3. Tabla de recursos

Rutas relativas a `{base_url}/{api_version}/{store_id}/`.

### Catálogo

| Recurso | Operaciones | Particularidades |
|---|---|---|
| Product | `GET /products` · `GET /products/{id}` · `GET /products/sku/{sku}` · `POST /products` · `PUT /products/{id}` · `DELETE /products/{id}` · `PATCH /products/stock-price` | `GET /products/sku/{sku}` devuelve el **primer** producto cuya variante tenga ese SKU. Filtros ricos: `q`, `ids`, `category_id`, `published`/`visibility`, `min_stock`/`max_stock`, `has_promotional_price`, `created_at_*`, `updated_at_*`, `sort_by`, `fields`. Valores de `sort_by`: `user`, `price-ascending`/`cost-ascending`, `price-descending`/`cost-descending`, `alpha-ascending`/`name-ascending`, `alpha-descending`/`name-descending`, `created-at-ascending`, `created-at-descending`, `best-selling` (ojo con el alias raro: los `cost-*` ordenan por **precio**, no por costo). `visibility` (`visible`/`unlisted`/`hidden`) y `published` **no se pueden mandar juntos** (`422`). Si el producto no tiene variantes propias, precio y stock viven en una variante "virtual": se editan con `PUT /products/{id}/variants/{id}`. **`PUT /products/{id}` hace merge**: omitir un campo lo preserva, mandarlo vacío lo borra (`categories: []` deja el producto sin categoría). **No** borra variantes al omitirlas — el reemplazo total es solo del `PUT` de la **colección** `/products/{id}/variants` (ver [`operaciones-peligrosas.md` §1 y §3](operaciones-peligrosas.md#nivel-rojo--destruyen-datos-en-la-misma-request)). |
| Product Variant | `GET`/`POST` `/products/{id}/variants` · `GET`/`PUT`/`DELETE` `/products/{id}/variants/{vid}` · **`PUT /products/{id}/variants`** (colección) · **`PATCH /products/{id}/variants`** (colección) · `POST /products/{id}/variants/stock` | El `PUT` de colección **reemplaza toda la colección** y matchea **por combinación de `values`, no por `id`**: lo que no venga en el body se borra. El `PATCH` de colección exige `id` en cada elemento y **nunca crea ni borra**. `POST .../variants/stock` acepta `action: replace\|variation` y `value` (en `replace`, `null` = stock infinito). |
| Product Image | `GET`/`POST` `/products/{id}/images` · `GET`/`PUT`/`DELETE` `/products/{id}/images/{image_id}` | Para productos con muchas imágenes, la doc recomienda crear el producto con ≤9 y cargar el resto por este endpoint. |
| Category | `GET /categories` · `GET /categories/{id}` · `POST` · `PUT /categories/{id}` · `DELETE /categories/{id}` | Árbol: `parent` y `subcategories`. Campos i18n. |
| Kit | `GET /kits/{id}` | **Read-only.** Se administran desde el panel. Solo productos de una sola variante pueden ser componentes. El precio es la suma de los precios de lista de los componentes con `discount_percent` aplicado sobre ese total; `kit_stock` es el mínimo que habilitan los componentes (`null` = infinito). |
| Product Price Tables (B2B) | `POST`/`GET`/`PUT` `/products/price-tables[/{id}]` · sub-recursos `/categories`, `/product-variants`, `/customers` (`PUT`/`GET`/`DELETE`) · `POST /products/price-tables/{id}/approve-customers` | Disponible en `unstable`, `v1` y `2025-03` con el mismo contrato. Precedencia: excepción de variante > excepción de categoría > `default_discount`. Paginación propia y chica (ver §4). |
| Metafields | `GET /metafields/{owner_resource}` · `GET /metafields/{id}` · `POST` · `PUT /metafields/{id}` · `DELETE /metafields/{id}` | Solo estos owners: `Product`, `Product_Variant`, `Category`, `Page`, `Order`, `Customer`. Clave = `namespace` + `key`. `value` es siempre string. Es el mecanismo oficial para datos que la plataforma no modela (por ejemplo, facturas NFe con `namespace: nfe`). |
| Custom Fields | Por entidad (`products`, `products/variants`, `categories`, `orders`, `customers`): `POST`/`GET`/`PUT`/`DELETE` `/{entidad}/custom-fields[/{id}]` · `PUT /{entidad}/{id}/custom-fields/values` · `GET /{entidad}/{id}/custom-fields` · `GET /{entidad}/custom-fields/{id}/owners` | La definición y los valores son endpoints distintos: primero se crea el campo, después se le asignan valores por recurso. `read_only: true` impide que el merchant lo edite desde el panel. |

### Ventas

| Recurso | Operaciones | Particularidades |
|---|---|---|
| Order | `GET /orders` · `GET /orders/{id}` · `GET /orders/{id}/history/values` · `GET /orders/{id}/history/editions` · `GET /orders/{id}/subscriptions` · `POST /orders/` · **`PUT /orders/{id}`** · `POST /orders/{id}/close` · `POST /orders/{id}/open` · `POST /orders/{id}/cancel` | **`PUT` solo acepta `owner_note` y `status`** ("just `owner_note` for now", textual). `cancel` toma `reason` (`customer`/`inventory`/`fraud`/`other`), `email` y `restock`, ambos con **default `true`**. No existe acción "pagar orden": una orden queda paga cuando se crea una Transaction con status `success`. `aggregates=fulfillment_orders,custom_fields` enriquece la respuesta. **Editar líneas y reembolsar parcialmente no existe en `2025-03`: solo en el canal `unstable`, con `POST /orders/{id}/edit` (+ `auto_partial_refund: true`)** — requiere todos los fulfillment orders en `unpacked` y `unstable` puede cambiar o desaparecer sin aviso, así que no se cotiza como estable. Detalle completo en [`no-se-puede.md` §1](no-se-puede.md#1-órdenes). |
| Draft Order | `GET /draft_orders` · `GET /draft_orders/{id}` · `POST /draft_orders` · `POST /draft_orders/{id}/confirm` · `DELETE /draft_orders/{id}` | **No hay `PUT`**: no se edita un draft order creado. |
| Cart | `GET /carts/{id}` · `DELETE /carts/{id}/line-items/{id}` · `DELETE /carts/{id}/coupons/{id}` | Solo carritos todavía modificables: los convertidos a orden o los que arrancaron un checkout de redirect ya no son accesibles. No hay creación ni alta de ítems. |
| Abandoned Checkout | `GET /checkouts` · `GET /checkouts/{checkout_id}` · `POST /checkouts/{cart_id}/coupon` | Se crea cuando el comprador llega al **segundo paso** del checkout. Accesibles 30 días; borrados a los 90. |
| Customer | `GET /customers` · `GET /customers/{id}` · `POST` · `PUT /customers/{id}` · `DELETE /customers/{id}` | `DELETE` falla con **`422`** si el cliente tiene órdenes asociadas. |
| Coupon | `GET /coupons` · `GET /coupons/{id}` · `POST` · `PUT /coupons/{id}` · `DELETE /coupons/{id}` | Tipos: `percentage`, `absolute`, `shipping`. Campo `valid` para activar/desactivar sin borrar — **[incierto]** que sea escribible por `PUT` (la doc de `PUT /coupons/{id}` no enumera propiedades): verificar en demo antes de usarlo como alternativa reversible al `DELETE`. Filtros por `status`, `limitation_type`, `term_type`, `discount_type`. |
| Transaction | `GET`/`POST` `/orders/{order_id}/transactions[/{tid}]` · `POST /orders/{order_id}/transactions/{tid}/events` | **Uso exclusivo de apps de pago.** Una transaction por método de pago de la orden. |
| Dispute | `POST /orders/{oid}/transactions/{tid}/disputes` · `GET`/`PUT` `/orders/{oid}/transactions/{tid}/disputes/{did}` | Chargebacks reportados por partners de pago; **cuelgan de la transaction, no hay `/disputes` de primer nivel**. Requiere `write_payments` y solo se ven las creadas por la propia app. Estados: `needs_response`, `documentation_sent`, `insured`, `under_review`, `won`, `lost`, con transiciones válidas definidas. |
| Discounts (promociones de app) | Callbacks `PUT /discounts/callbacks` · `POST /promotions` · `GET /promotions` | Es la API de **promociones creadas por apps partner**, no un CRUD del motor nativo de promociones del panel. `GET /promotions` lista las promociones no borradas **creadas por tu app** en esa tienda. El detalle del contrato la doc lo delega a un `Openapi.yml` externo → **[incierto]** sin ese archivo no se puede afirmar el payload exacto. La URL del callback **no se puede borrar**, solo modificar. **[incierto]** si hace falta habilitación previa: a diferencia de Payments, Shipping y Business Rules, su página **no** declara gate de Partner Support, pero tampoco existe un scope `read_discounts`/`write_discounts` en ninguna parte de la doc. No tratar "se puede construir sin permiso" como un hecho. Verificable: `POST /promotions` con el token de una app sin habilitar en una tienda demo y mirar si vuelve `403`; si vuelve, tramitarla con `socios@tiendanube.com` / `parceiros@nuvemshop.com.br`. |

### Logística e inventario

| Recurso | Operaciones | Particularidades |
|---|---|---|
| Location | `GET /locations` · `GET /locations/{id}` · `POST` · `PUT /locations/{id}` · `DELETE /locations/{id}` · `GET /locations/{id}/inventory-levels` · `PATCH /locations/priorities` · `PATCH /locations/{id}/chosen-as-default` | `priority`: menor valor = mayor prioridad al asignar stock en checkout. `tags` (`online`/`offline`) definen para qué canal sirve el depósito. `inventory-levels` devuelve envelope `{total, page, per_page, results}`. |
| Fulfillment Order | `GET /orders/{oid}/fulfillment-orders` · `GET`/`PATCH`/`DELETE` `/orders/{oid}/fulfillment-orders/{fid}` · tracking events: `POST`/`GET` `.../tracking-events`, `GET`/`PUT`/`DELETE` `.../tracking-events/{teid}` | El `PATCH` es el que mueve estado, tracking, destino, destinatario, envío y location asignada. Una orden ya despachada no acepta cambios de destino, envío ni destinatario. |
| Labels API | `POST /fulfillment-orders/labels` · `PATCH /fulfillment-orders/{fid}/labels/{lid}` · `PATCH /fulfillment-orders/labels/status` · `POST /fulfillment-orders/{fid}/labels/{lid}/download` | **Gated por feature** `fulfillment_order_label_api`, hoy solo en plan Next. Sin la feature, `403`. Es asincrónica: la etiqueta la genera la app de carrier vía `callback_labels_url`. |
| Fulfillment (legacy) | `GET`/`POST` `/orders/{oid}/fulfillments` · `GET`/`DELETE` `/orders/{oid}/fulfillments/{id}` | Compatibilidad hacia atrás: si la tienda tiene varias locations, un cambio mandado acá **se aplica solo al primer fulfillment order**, que puede ser el equivocado. |
| Shipping Carrier | `GET`/`POST` `/shipping_carriers` · `GET`/`PUT`/`DELETE` `/shipping_carriers/{id}` · `GET`/`POST` `/shipping_carriers/{cid}/options` · `GET`/`PUT`/`DELETE` `/shipping_carriers/{cid}/options/{oid}` | **No está habilitado por default**: hay que crear la app en el Partner Portal y completar un formulario para que el equipo de plataforma habilite los endpoints. |

### Plataforma y contenido

| Recurso | Operaciones | Particularidades |
|---|---|---|
| Store | **`GET /store`** | Único endpoint. **Cero escritura**: nombre, idiomas, monedas, dominios, tema y datos fiscales son solo lectura por API. Acepta `fields`. |
| Page | `GET /pages` · `GET /pages/{id}` · `POST /pages` · `PUT /pages/{id}` · `DELETE /pages/{id}` | Desde `2025-03`. Respuesta de lista con envelope `{"pages": {"results": [...], "total", "page", "perPage", "lastPage"}}` — distinto del array plano del resto. Una page siempre está publicada. |
| Blog | `GET /blogs` · `GET`/`POST` `/blogs/{bid}/posts` · `GET`/`PUT`/`DELETE` `/blogs/{bid}/posts/{pid}` · `PATCH .../publish` · `PATCH .../unpublish` · `POST /blogs/{bid}/posts/media` · `POST /blogs/{bid}/posts/thumbnail` | Requiere los permisos "Read Content" y "Edit Content" activados en el Partner Panel. Los `blog_id`/`post_id` son UUID; subir una imagen solo devuelve la URL, hay que insertarla después en el `content` del post. |
| Email Templates | `GET /email-templates` · `GET /email-templates/{id}` · `PUT /email-templates/{id}` | Desde `2025-03`. Tipos: `abandonedcheckoutrecover`, `customer_activate_account`, `customer_reset_password`, `customer_welcome_account`, `ordercancelled`, `ordercaptured`, `orderconfirmation`, `ordershipped`. Subject y cuerpo son objetos i18n. |
| Script | `GET /scripts` · `GET /scripts/{id}` · `POST` · `PUT /scripts/{id}` · `DELETE /scripts/{id}` | El script y sus versiones se **definen en el Partner Portal**; estos endpoints ya no registran scripts, solo manejan la **asociación script↔tienda** y únicamente para los marcados como no auto-instalables. El evento de carga es `onfirstinteraction` (default) u `onload` (este último requiere aprobación previa de Tiendanube). Al desinstalar la app el script deja de cargarse. |
| Webhook | `GET /webhooks` · `GET /webhooks/{id}` · `POST` · `PUT /webhooks/{id}` · `DELETE /webhooks/{id}` | URL debe ser HTTPS y no puede apuntar a localhost ni a dominios tiendanube/nuvemshop. Firma HMAC-SHA256 en `x-linkedstore-hmac-sha256`. Eventos por categoría: App (`uninstalled`/`suspended`/`resumed`); Category, Customer, Product, Location, Order Custom Field y Product Variant Custom Field (`created`/`updated`/`deleted`); Domain, Subscription y Fulfillment (solo `updated`); Product Variant (solo `custom_fields_updated`); Order (`created`/`updated`/`paid`/`packed`/`fulfilled`/`cancelled`/`custom_fields_updated`/`edited`/`pending`/`voided`/`unpacked`); Fulfillment Order (`status_updated`/`label_status_updated`/`tracking_event_created`/`tracking_event_updated`/`tracking_event_deleted`). |
| Payment Provider / Payment Option | `GET /payment_providers` · `POST /payment_providers` · `GET`/`PUT`/`DELETE` `/payment/providers/{id}` · `GET /payment-options` | **Uso exclusivo de apps de pago** y requiere que Partner Support habilite la app para las Payments APIs. |
| Business Rules | `PUT /business_rules/integrations/{dominio}` (registra el callback) | Dominios y scopes: `payments` (`read_payment_options` + `read_payments`), `shipping` (`read_shipping`), `location` (`read_locations`), `cart` (sin scope). Requiere que el equipo de Partner Support habilite la app. |
| App Proxy | Ruta `/apps/{prefijo}/...` en el storefront | Se configura pidiéndolo a Tiendanube (`socios@tiendanube.com` / `parceiros@nuvemshop.com.br`). Firma HMAC en `X-Linkedstore-HMAC-SHA256` sobre `X-Store-Id` + `X-Customer-Id` + `X-Request-Id`. |
| Billing (partner) | `POST /plans` · `PATCH /plans/{id}` · `DELETE /plans/{id}` · `GET`/`PATCH` `/concepts/{code}/services/{sid}/subscriptions` · `POST /services/{sid}/charges` | Es facturación **de la app al merchant**, no de la tienda a sus clientes. Los tres endpoints de `/plans` **no cuelgan de `{store_id}`**: usan autenticación *partner-action* sobre `{base_url}/{api_version}/apps/{app_id}/plans`, con el client secret como token. |

---

## 4. Límites duros

### Rate limit general

- **Leaky bucket**: bucket de **40 requests**, drenaje de **2 requests por segundo**.
- Se mide **por par (tienda, app)** — no por app global ni por IP.
- **×10 en tiendas Next / Evolución** (bucket 400, drenaje 20 req/s). **[incierto]** qué planes lo
  reciben hoy: la doc dice "Next o Evolución", pero la grilla comercial cambió (en Brasil se venden
  Começo / Essencial / Impulso / Escala / Next y "Evolução" quedó como legacy) y no está documentado
  si el Escala actual entra en el multiplicador. Verificable: `GET /store?fields=plan_name` y leer el
  header `x-rate-limit-limit` de esa misma respuesta — 400 en vez de 40 significa que la tienda tiene
  el ×10. Para certeza contractual, confirmarlo con `socios@tiendanube.com` /
  `parceiros@nuvemshop.com.br`.
- Headers de respuesta: `x-rate-limit-limit` (tamaño del bucket), `x-rate-limit-remaining`
  (cuánto falta para llenarlo) y `x-rate-limit-reset` (**milisegundos** para vaciarlo del todo).
- **El exceso se encola mientras quede lugar en el bucket; recién se pierde cuando el bucket está
  lleno.** Ejemplos de la doc: 20 requests de golpe se encolan y tardan ~10 s en drenar; a 4 req/s
  sostenidos el bucket se llena en ~20 s y **recién ahí** empiezan los `429`; 50 de golpe = 40
  encoladas y **10 perdidas**.
- **No existe header `Retry-After`** ni body documentado del `429`. El backoff se calcula **solo** a
  partir de `x-rate-limit-reset`: no busques otra señal, no hay.
- El limitador cuenta **requests, no bytes**: `fields` y `aggregates` bajan el ancho de banda y evitan
  N+1, pero **no reducen el costo de rate limit**. Pedir menos campos no te deja ir más rápido.
- Referencia de tiempo: recorrer 5.000 productos de a 100 por página son 50 requests ≈ 25 segundos a
  2 req/s (≈ 2,5 s con el ×10).

### Rate limit específico de variantes

Los endpoints de actualización de variantes usan un **Weighted Token Bucket** que corre **aparte del
limitador general**: el costo no es "una request", es el **peso del payload**. Pesan más la cantidad
de variantes, las traducciones incluidas y los inventory levels. Los costos por campo y el tamaño de
ese bucket **no están publicados**.

Consecuencia contraintuitiva y fácil de diagnosticar mal: **agrandar el lote puede dar `429` aun
yendo muy por debajo de 2 req/s**. Por eso, ante `429` en updates masivos de variantes la
recomendación oficial es **mandar menos variantes por request**, no esperar más entre requests.

### Paginación

- **Las listas no vienen paginadas por default**: hay que mandar `page` (1-based). Sin parámetros, la
  API devuelve **hasta 30 resultados**.
- `per_page` **hasta 200** en la mayoría de las colecciones.
- Headers útiles: `x-total-count` con el total y `Link` con `rel="next" | "prev" | "first" | "last"`.
  La doc pide **usar las URLs del header `Link`** en vez de construirlas a mano.
- Hay recursos con paginación propia y mucho más chica:

  | Endpoint | Default | Máximo |
  |---|---|---|
  | `GET /products/price-tables` | 10 | 10 |
  | `GET /products/price-tables/customers/{id}` | 10 | 10 |
  | `GET /products/price-tables/{id}/categories` · `/product-variants` · `/customers` | 50 | 50 |
  | `GET /locations/{id}/inventory-levels` | **1** | no documentado |

- **[observado]** Dos comportamientos que la doc **no** describe y que hay que codear igual:
  1. **Clamp silencioso de `per_page`**: pedir 200 puede devolver menos por página sin ningún aviso.
     Por eso el corte de un recorrido se compara contra **el tamaño real de la página 1**, nunca
     contra el `per_page` pedido.
  2. **`404` al pedir una página más allá de la última** (en vez de un array vacío). Ese `404` **no
     es un error**: es el fin de la colección.

  Verificable en tienda demo: pedir `per_page=200` y contar los ítems devueltos; después pedir
  `page=999` y mirar el status.

### Topes de consulta y de cantidad

| Límite | Valor | Dónde |
|---|---|---|
| Resultados totales de una query de órdenes | **10.000 ítems** | `GET /orders`; excederlo devuelve error. Particionar con `created_at_min`/`created_at_max`. |
| Productos por tienda | **100.000** | `422` — *"Store has reached maximum limit of 100000 allowed products"* |
| Categorías por tienda | **1.000** | `422` — *"Store has reached maximum limit of 1000 allowed categories"* |
| Variantes por producto | **1.000** | `422` — *"Product is not allowed to have more than 1000 variants"* |
| Atributos por producto | **3** | Definen las combinaciones de variantes |
| Imágenes por producto | **250** | `422` — *"Product is not allowed to have more than 250 images"* |
| Imágenes recomendadas en `POST /products` | **9** | Recomendación oficial; el resto por `POST /products/{id}/images` |
| Variantes por `PATCH /products/stock-price` | **50** | Contando todos los productos del batch; excederlo da `422` *"Too many variants sent for update"* |
| IDs en `?ids=` | **30** | `GET /products` |
| `seo_title` | 70 caracteres | Producto |
| `seo_description` | 320 caracteres | Producto |
| `PATCH /fulfillment-orders/labels/status` | **200 fulfillment orders** por request, **1 a 10 etiquetas** por fulfillment order (únicas) | Labels API |
| Clientes por `PUT /products/price-tables/{id}/customers` | **10.000** | Si alguno ya está asociado a otra price table, falla el batch entero con `409` |
| Disputes por tienda + orden + transaction | **3** | Dispute API |
| Antigüedad de abandoned checkouts | 30 días accesibles · borrado total a los 90 · el carrito se puede crear hasta 6 h después del abandono | Abandoned Checkout |

### Webhooks

- Timeout de **3 segundos** esperando un `2XX` (las páginas de webhooks de Fulfillment Order y de
  Location dicen **10 segundos**; asumir el más chico).
- Reintentos: uno inmediato, después ~5, ~10 y ~15 minutos, y luego backoff exponencial (×1,4)
  dentro de las **48 horas**, hasta **16 intentos**.
- **Sin garantía de orden** y con **entregas duplicadas posibles** (sistema distribuido). Todo handler
  tiene que ser **idempotente**.
- Con la tienda o la app impaga, los webhooks **no se disparan** (igual que la API: `402`).

---

## 5. Scopes

Regla base: **pedir un scope de `write` implica el `read` correspondiente**. Y los webhooks solo se
pueden registrar para recursos cuyo scope fue otorgado.

| Scope | Habilita |
|---|---|
| `read_content` / `write_content` | Page (y contenido de Blog, que además pide los permisos "Read Content" y "Edit Content" en el Partner Panel) |
| `read_email_templates` / `write_email_templates` | Email Templates |
| `read_products` / `write_products` | Product, Product Variant, Product Image, Category |
| `read_customers` / `write_customers` | Customer |
| `read_orders` / `write_orders` | Order, Cart, Abandoned Checkout |
| `read_draft_orders` / `write_draft_orders` | Draft Order |
| `read_coupons` / `write_coupons` | Coupon |
| `read_shipping` / `write_shipping` | Shipping Carrier y sus options |
| `read_locations` / `write_locations` | Location (`read` para GET, `write` para POST/PUT/DELETE) |
| `read_fulfillment_orders` / `write_fulfillment_orders` | Endpoints con prefijo `/orders/{oid}/fulfillment-orders` y sus webhooks |
| `read_payments` / `write_payments` | Payment Provider, Transaction, Dispute (apps de pago) |
| `read_payment_options` | Dominio `payments` de Business Rules (junto con `read_payments`) |
| `write_scripts` | Script |

### Herencias automáticas

- Una app que ya tenga **`read_shipping`, `write_shipping`, `read_products` o `write_products`**
  recibe **`read_locations`** automáticamente en el token de todos los merchants.
- Una app con **`read_orders`** recibe **`read_fulfillment_orders`** automáticamente; ídem
  `write_orders` → `write_fulfillment_orders`.

### Multi-inventory ready

Una app que usa alguno de estos scopes —`read_products`, `write_products`, `read_orders`,
`write_orders`, `read_draft_orders`, `write_draft_orders`, `read_shipping`, `write_shipping`— queda
alcanzada por el proyecto multi-inventario y necesita ser declarada *multi inventory ready*: o bien
no usar ninguno de esos scopes, o bien pasar la aprobación automática (no haber usado endpoints ni
parámetros deprecados en los últimos 14 días) y, si Tiendanube lo decide, una aprobación manual.

---

## 6. Errores

### Tres formas de error conviviendo

**Legacy**, validación campo por campo, sin `code` ni `message`:

```json
{ "name": ["can't be blank"] }
```

**Envelope moderno**, el de los endpoints nuevos:

```json
{ "code": 422, "message": "Unprocessable Entity", "description": "Validation error" }
```

**Híbrido**: el envelope **y** las claves de campo en el mismo nivel. Es la forma más común en los
`422` recientes y la que rompe los handlers que asumen una u otra:

```json
{ "code": 422, "message": "Unprocessable Entity", "description": "Validation error", "price": ["The price must be a number."] }
```

El `409` de price tables suma un array `errors` con los ítems en conflicto. Y el error de parseo de
JSON (`400`) tiene forma propia, distinta de las tres:

```json
{ "error": "Problems parsing JSON" }
```

Un cliente robusto tiene que cubrir las tres formas más la del parseo: leer `description` si está,
**y además** recorrer las claves que no sean `code`/`message`/`description`/`error` tratando cada una
como un campo con su lista de mensajes. Leer solo `description` pierde el detalle del híbrido.

### Tabla de códigos

| Código | Causa real | Qué hacer |
|---|---|---|
| `400` | Falta el header **`User-Agent`**, o el JSON del body es inválido | Agregar el `User-Agent`; validar el body antes de mandar. **[verificado]** el chequeo del `User-Agent` corre **después** de la auth: si el token no sirve vas a ver `401` aunque también falte el UA |
| `401` | Token inválido, revocado o desinstalado, o directamente ausente | Reinstalar la app / regenerar el token. **[verificado]** el header de auth **no** es la causa: `Authorization: Bearer` y `Authentication: bearer` funcionan los dos. Distinguí por el mensaje: *"Required access token is missing"* = no mandaste token · *"Invalid access token"* = el token no sirve |
| `402` | **Tienda impaga o app con precio recurrente impago: la API entera queda suspendida.** También se cortan scripts y webhooks | No es un error técnico: avisar al merchant que regularice. Suscribirse a `app/suspended` y `app/resumed` para saber cuándo volver a sincronizar (ojo: esos webhooks **no** se disparan cuando la app se queda sin días gratis) |
| `403` | Feature no habilitada para el plan de la tienda (caso típico: Labels API sin `fulfillment_order_label_api`), o app sin habilitación de Partner Support (Shipping, Payments, Business Rules) | Verificar `features` en `GET /store`; si es de habilitación, tramitarla |
| `404` | Recurso inexistente · versión inválida en la URL · página más allá de la última al paginar **[observado]** | Distinguir por contexto: en un recorrido paginado es fin de colección, no error; si la versión de la URL está mal, el body trae la lista de válidas (`v1, 2025-03, unstable`). **[verificado]** nunca hay `404` por problemas de autenticación — eso siempre es `401` |
| `409` | Conflicto de estado (ej.: clientes ya asociados a otra price table) | Leer el array `errors` y resolver el conflicto antes de reintentar |
| `415` | Falta el header `Content-Type` en POST/PUT/PATCH | Mandar `application/json; charset=utf-8` |
| `422` | Validación: campo faltante o inválido, tope de la tienda alcanzado, combinación prohibida (`published` + `visibility`), borrar un cliente con órdenes | Leer `description` **y** los campos del formato legacy; no reintentar sin cambiar el payload |
| `429` | Rate limit excedido (bucket lleno, o payload demasiado pesado en updates de variantes) | Dormir lo que indica `x-rate-limit-reset` (ms) y reintentar — **no hay `Retry-After`**: ese header de reset es la única señal; en variantes, **achicar el batch** |
| `5xx` | `500` app caída, `502`/`503`/`504` infraestructura | Responsabilidad del cliente reintentar más tarde, con backoff |

---

## 7. Feature detection

`GET /store` es el punto de entrada obligatorio antes de cualquier operación no trivial. Dos campos
deciden el comportamiento correcto:

- **`plan_name`** — nombre del plan de la tienda.
- **`features`** — array de strings con las features de API habilitadas.

### Features documentadas y qué cambian

| Feature | Qué implica |
|---|---|
| `inventory-levels` | El stock deja de vivir en `variant.stock` y pasa a `variant.inventory_levels[]`, con un `stock` por `location_id`. `variant.stock` sigue existiendo por compatibilidad reflejando el total, pero **escribir ahí ya no es correcto**. Para stock infinito hay que mandar una entrada por cada location activa. |
| `fulfillment-orders` | La orden se despacha por fulfillment orders (uno por envío/location). Los endpoints legacy `/orders/{id}/fulfillments` siguen andando pero **impactan solo en el primer fulfillment order** — riesgo real de asignar un tracking al envío equivocado. |
| `fulfillment_order_label_api` | Habilita la Labels API. Hoy **solo se otorga a tiendas en plan Next**. Sin ella, todo endpoint de Labels devuelve `403`. |

### Qué cambia el plan

- **Next / Evolución**: el rate limit se multiplica por **10** (bucket 400, 20 req/s). **[incierto]**
  cómo se mapea eso a la grilla comercial vigente — ver §4 para el detalle y el método de comprobación.
- **Next**: es el plan al que hoy se le concede `fulfillment_order_label_api`.
- **Escala y Evolución (AR) · Escala y Next (BR)**: son los planes que habilitan las **aplicaciones a
  medida**, o sea el token directo desde el admin del merchant (§2). En planes menores, la única vía
  es la app de partner con link de instalación.

### Incertidumbres marcadas

- **[incierto]** La doc **no publica la lista completa** de valores posibles de `features`. Los tres de
  arriba son los únicos que aparecen documentados (dos en el ejemplo de `GET /store`, el tercero en la
  Labels API). Ante una tienda concreta, **leer el array real** y no asumir.
- **[incierto]** Tampoco hay tabla oficial de "qué feature trae cada plan". Lo único afirmado es la
  relación Next ↔ `fulfillment_order_label_api` y el multiplicador ×10 del rate limit en
  Next/Evolución — y este último ya no se puede mapear con certeza a los planes que se venden hoy.
- **Método de verificación** para cualquiera de las dos: `GET /store?fields=plan_name,features` sobre
  la tienda demo y sobre la tienda del cliente, y comparar.
