# Operaciones peligrosas y sus antídotos

Catálogo de escrituras que destruyen datos en Tiendanube/Nuvemshop, por qué se disparan sin querer y cómo evitarlas. **La Admin API no tiene deshacer ni papelera**: lo único que revierte una escritura es el backup que se haya tomado antes.

Regla transversal antes de cualquier escritura: `GET` del recurso → guardar el estado en un archivo → dry-run → confirmación explícita del dev → ejecutar.

## Tabla de contenidos

1. [Nivel rojo — destruyen datos en la misma request](#nivel-rojo--destruyen-datos-en-la-misma-request)
2. [Nivel naranja — irreversibles o con efecto hacia afuera](#nivel-naranja--irreversibles-o-con-efecto-hacia-afuera)
3. [Nivel amarillo — trampas silenciosas](#nivel-amarillo--trampas-silenciosas)
4. [Efecto de desinstalar la app](#efecto-de-desinstalar-la-app)
5. [Protecciones que sí existen](#protecciones-que-sí-existen)
6. [Incógnitas](#incógnitas)

---

## Nivel rojo — destruyen datos en la misma request

### 1. `PUT /products/{id}/variants` (la colección completa)

- **Qué destruye:** toda variante que no venga en el body, con su stock por location, su SKU y sus custom fields asociados.
- **Por qué pasa:** la doc lo dice explícito: *"all the variants sent in the request will be the current and only variants for the Product"* y cada variante se identifica **por su combinación de `values`, no por `id`**. Renombrar un talle (`"L"` → `"Large"`) no renombra: crea una variante nueva y borra la vieja. Un script que arma el body desde una fuente parcial (un CSV con 3 de 8 talles) borra las otras 5.
- **Antídoto:** usar **`PATCH /products/{id}/variants`**, que exige `id` por variante, solo actualiza y **no crea ni borra**. El `PUT` de colección se reserva para cuando el objetivo declarado *es* reemplazar todo el set, con backup del `GET` previo.
- **Ojo con el mito inverso:** el riesgo vive **solo** en este endpoint. `PUT /products/{id}` (el producto) **no** borra las variantes al omitirlas: el ejemplo canónico de la doc hace `PUT` con `{categories, id, published}` y la respuesta 200 devuelve el array `variants` intacto. Para campos omitidos, el `PUT` del producto **mergea**.

### 2. `PUT /products/{product_id}/custom-fields/values`

- **Qué destruye:** según la FAQ oficial ese endpoint **sobrescribe** los custom fields asociados al producto, así que lo que no venga en el body queda fuera.
- **Por qué pasa:** un body armado solo con el campo que se quiere tocar. (La misma FAQ documenta `value: null` como la forma de desasociar un campo puntual, lo que deja abierto cuánto borra realmente un body parcial; hasta verificarlo en demo, asumir la lectura destructiva.)
- **Antídoto:** `GET` de los valores actuales, mergear en memoria y mandar el set completo. Nunca mandar un body parcial.

### 3. `PUT /products/{id}` con `categories`

- **Qué destruye:** la categorización del producto. Con `categories: []` queda huérfano y desaparece de la navegación del storefront; con una lista parcial pierde las categorías que no vinieron, porque el campo **reemplaza, no agrega**.
- **Por qué pasa:** dos motivos. (a) Documentado: *"if the product has an associated category, and the categories field is sent empty, the product ends up without a category"* — y los serializadores que mandan todos los campos del modelo emiten `[]` cuando la lista viene vacía en origen. (b) **El campo es asimétrico:** se escribe como array de IDs enteros (`{"categories": [1234, 4567]}`) pero el `GET` lo devuelve como array de objetos completos (`[{id, name, handle, parent, subcategories, ...}]`). Un read-modify-write ingenuo reinyecta los objetos tal cual los leyó y rompe.
- **Antídoto:** **omitir el campo** cuando no se toca (omitir es seguro, el `PUT` mergea; omitir ≠ mandar vacío). Si hay que modificar, extraer los enteros del `GET` previo (`[c["id"] for c in producto["categories"]]`), aplicar el alta o la baja sobre esa lista y mandar el set completo de IDs.

### 4. `DELETE` de cualquier recurso — sin papelera

- **Qué destruye:** el recurso, en forma definitiva. Tienen `DELETE` documentado: productos, variantes, imágenes de producto, categorías, clientes, cupones, metafields, custom fields (de producto, variante, categoría, cliente y orden), webhooks, scripts, locations, shipping carriers y sus opciones, payment providers, draft orders, fulfillment orders y sus tracking events, ítems y cupones de carrito.
- **Por qué pasa:** una limpieza "de prueba" contra la tienda productiva, o un loop que borra por filtro mal armado. No hay endpoint de restauración documentado para ninguno.
- **Antídoto:** `DELETE` **fuera de alcance salvo pedido expreso y por escrito**; backup previo obligatorio del recurso completo; ejecutar de a uno y verificar; preferir la alternativa reversible cuando existe (producto → `visibility: "hidden"`; cupón → ver [Protecciones](#protecciones-que-sí-existen)).

### 5. `DELETE /plans/{id}` (Billing, autenticación partner-action)

- **Qué destruye:** documentado textual: borra **todas las suscripciones a ese plan** y **todos los cargos creados pero aún no pagados o en espera de pago**.
- **Por qué pasa:** se confunde "dar de baja un plan del catálogo" con "borrar el plan". Es facturación de la app propia, no datos de la tienda: el daño es a la cobranza.
- **Antídoto:** no ejecutarlo desde esta skill. Si el pedido es dejar de ofrecer un plan, verificar primero con el equipo qué suscripciones y cargos pendientes existen.

---

## Nivel naranja — irreversibles o con efecto hacia afuera

### 6. `POST /orders/{id}/cancel`

- **Qué destruye:** el estado de la orden (pasa a `cancelled`). No existe endpoint documentado para descancelar: los únicos movimientos de estado documentados son `close`, `open` (reabre una orden **cerrada**) y `cancel`.
- **Por qué pasa:** los dos parámetros con efecto lateral tienen **default `true`**: `restock` (devuelve el stock) y `email` (le avisa al comprador). Cancelar "en silencio para probar" manda mail real al cliente y mueve inventario.
- **Antídoto:** mandar siempre `restock` y `email` **explícitos** en el body, más `reason` (`customer`, `inventory`, `fraud`, `other`), y confirmar ambos valores con el dev antes de ejecutar. Nunca cancelar en lote.

### 7. `PATCH /products/stock-price`

- **Qué destruye:** precios y stock de hasta 50 variantes por request, sin rollback. La respuesta trae `success` **por variante**: un lote puede quedar aplicado a medias.
- **Por qué pasa:** es el endpoint de actualización masiva, y con 51 variantes devuelve `422 "Too many variants sent for update"` — el reintento manual descontrolado termina duplicando escrituras.
- **Antídoto:** backup del estado previo de todas las variantes del lote; dry-run con diff registro por registro; lotes de ≤50 (la doc recomienda lotes **más chicos** si aparecen 429); leer el `success` de cada variante y reportar aplicados/fallidos.

### 8. `PATCH` de fulfillment order con `tracking_info.notify_customer: true`

- **Qué destruye:** nada en datos, pero **dispara un mail al comprador** que no se puede retirar. Además: con `status: "DELIVERED"` la fulfillment order queda marcada como cumplida (`fulfilled_at`), y una ya despachada no admite cambios de destino, envío ni destinatario.
- **Por qué pasa:** el campo es obligatorio en `FulfillmentOrderTrackingInfoInput`, su default es `false`, y los ejemplos de la doc lo muestran en `true` — copiar el ejemplo notifica.
- **Antídoto:** en pruebas y backfills, `notify_customer: false` explícito. Poner `true` solo cuando el pedido es justamente notificar, y avisando cuántos compradores van a recibir mail.

### 9. Escrituras masivas contra el rate limit

- **Qué destruye:** la integridad del lote. El exceso **se encola** mientras el bucket (40) tenga lugar, y lo que no entra se pierde con `429`: mandar 50 de golpe deja **40 encoladas y 10 perdidas**. Queda una actualización parcial sin registro de qué entró.
- **Por qué pasa:** leaky bucket de 40 de burst que drena a **2 req/s** por par (tienda, app); ×10 en planes Next/Evolution. Un `for` sin throttle se pasa en el ítem 41.
- **Antídoto:** ejecutar siempre con el cliente que respeta 2 req/s y reintenta los `429` (`scripts/tn-api.py`), y cerrar con un reporte explícito de aplicados/fallidos.
- **No hay red de contención para el reintento:** la API **no tiene idempotency key ni header de request-id**. Una request que cortó por timeout pudo haberse aplicado igual, y reintentarla a ciegas duplica la escritura. La reejecución segura se resuelve del lado propio: registrar cada recurso escrito (con su id) antes de reintentar, y hacer que el script pueda retomar desde ahí.

### 10. Cambiar los scopes de la app

- **Qué destruye:** el acceso, no los datos. La doc dice que los access tokens **no expiran** y que se invalidan *"only after you get a new one, or if the user uninstalls your app"*; los scopes se otorgan en la autorización, así que un token viejo sigue teniendo los scopes viejos y el nuevo scope recién llega cuando el merchant vuelve a autorizar — y ese nuevo token invalida el anterior.
- **Por qué pasa:** se agrega un scope pensando que aplica retroactivamente a las tiendas ya instaladas.
- **Antídoto:** planificar el cambio de scopes como una **reinstalación por tienda**, coordinada con cada cliente, y refrescar los tokens guardados en el mismo momento.

---

## Nivel amarillo — trampas silenciosas

### 11. `stock: ""` es **stock infinito**

- **Qué rompe:** desactiva el control de stock de la variante. Sin error: la tienda vende sin límite.
- **Por qué pasa:** son **dos codificaciones distintas según el endpoint**: `""` (string vacío) en producto/variante e `inventory_levels`, y `null` en `POST /products/{id}/variants/stock` con `action: "replace"`. Un bug de serialización que emita `""` en vez de `0` pasa la validación. `stock_management` **no se puede escribir**: lo setea Tiendanube según el stock (`false` = infinito).
- **Antídoto:** validar el payload antes de mandar (`stock` debe ser entero ≥ 0 salvo que el pedido sea explícitamente stock infinito); comparar el `stock_management` del `GET` posterior.

### 12. `variant.stock` en tiendas con múltiples locations

- **Qué rompe:** el reparto del inventario. Con multi-location activo, `variant.stock` **lee el total de todas las locations** pero al escribir solo *"we'll update the first inventory_level for that variant"*. Un read-modify-write vuelca todo el total en la primera location.
- **Por qué pasa:** el campo sigue existiendo por compatibilidad y las integraciones viejas lo siguen usando.
- **Y mandar los dos no es un seguro:** si el body trae `stock` **e** `inventory_levels` a la vez, el `stock` de nivel superior **se ignora en silencio** (gana `inventory_levels`). El "por las dudas mando ambos" no avisa cuál quedó.
- **Antídoto:** chequear `features` en `GET /store`; con `inventory-levels` escribir siempre por `inventory_levels` con `location_id` explícito.

### 13. `PATCH /products/stock-price` sin `location_id`

- **Qué rompe:** el stock termina en la location equivocada: *"If no location_id is sent to it, like the rest of the endpoints, the first location will be used"*. Un `location_id` inexistente devuelve `422` (eso sí avisa); omitirlo, no.
- **Antídoto:** en tiendas multi-location, `location_id` explícito en cada `inventory_levels`, tomado de `GET /locations`.

### 14. Mandar `published` y `visibility` juntos

- **Qué rompe:** la request entera falla con `422 "Cannot send both 'published' and 'visibility'"` (vigente desde el 2026-07-28). En un lote, ese producto queda sin actualizar mientras el resto sí.
- **Por qué pasa:** `published` es el campo legacy derivado de `visibility`; los payloads copiados de un `GET` traen los dos.
- **Antídoto:** mandar uno solo — `visibility` (`visible` / `unlisted` / `hidden`) para distinguir oculto de no-listado.

### 15. Las órdenes creadas por API no reservan stock

- **Qué rompe:** el inventario queda inflado y la tienda sobrevende. Documentado: `inventory_behaviour` default **`bypass`** (no reclama inventario); solo `claim` reserva, y puede impedir la creación de la orden si no alcanza.
- **Antídoto:** al crear órdenes por API, definir `inventory_behaviour` a conciencia y avisarle al cliente cuál se usó.

### 16. Webhooks sin orden garantizado y con duplicados

- **Qué rompe:** el estado del sistema que consume los eventos (dobles fulfillments, dobles mails, contadores inflados).
- **Por qué pasa:** la doc lo declara: sistema distribuido, sin garantía de orden de procesamiento, y mensajes que pueden llegar varias veces. Timeout de **3 segundos** esperando un 2XX, con reintentos (uno inmediato, luego ~5, 10 y 15 minutos, después backoff ×1,4 dentro de 48 h, **hasta 16 intentos**).
- **Antídoto:** todo handler **idempotente**, deduplicando por el evento lógico y **no** por el cuerpo — la doc avisa que dos mensajes de cuerpo idéntico pueden ser eventos distintos y que un reintento llega con el cuerpo cambiado (trae el contador de reintentos). Además: responder 2XX rápido y procesar asincrónico, y verificar el HMAC `x-linkedstore-hmac-sha256`.

### 17. Endpoints legacy de fulfillment en tiendas multi-location

- **Qué rompe:** se marca como despachada la fulfillment order equivocada. Documentado: los endpoints viejos aplican el cambio **solo a la primera** fulfillment order de la orden.
- **Antídoto:** usar `/orders/{id}/fulfillment-orders/{id}/...` y elegir la fulfillment order por su id.

### 18. Desinstalar una app de promociones

- **Qué destruye:** *"When a promotions app is uninstalled, we will permanently remove all the promotions created for that store"*, y el proceso es asincrónico (puede haber demora). Además, la callback URL de Discounts **no se puede borrar** una vez registrada.
- **Antídoto:** avisarlo antes de cualquier desinstalación; exportar las promociones (`GET /promotions`) como respaldo, sabiendo que recrearlas es trabajo manual.

### 19. Escribir `price` (o `stock`, o `sku`) en el producto y no en la variante

- **Qué rompe:** nada cambia, y el script reporta éxito. Un producto **sin variantes visibles igual tiene una variante interna**: ahí viven el precio, el stock y el SKU. `PUT /products/{id}` con `price` devuelve `200` y **se ignora en silencio**.
- **Por qué pasa:** las lecturas muestran el precio a nivel producto, así que parece escribible. No hay error, no hay warning.
- **Antídoto:** escribir siempre en la variante — `PUT /products/{pid}/variants/{vid}` o `PATCH /products/stock-price` — tomando el `vid` del `GET` del producto. Cerrar con un `GET` de verificación: si el valor no cambió, el write fue al lugar equivocado.

### 20. `price` y `promotional_price` están invertidos respecto de Shopify

- **Qué rompe:** el precio de venta de todo el catálogo. `price` es el precio que se muestra **tachado** y `promotional_price` es **lo que efectivamente paga el cliente**. Un port de código Shopify que escribe el precio final en `price` **le sube el precio a la tienda entera**, sin error. `compare_at_price` **no existe** en esta API.
- **Por qué pasa:** el nombre `price` sugiere "precio de venta" y todo el ecosistema Shopify refuerza esa lectura.
- **Además:** `promotional_price: null` = sin oferta, pero **`price: null` en una variante significa "consultar precio"** — el storefront abre un contacto en vez del checkout, no es ni gratis ni "sin precio". Y los precios **se leen como string** (`"10.00"`) y **se escriben como número**: el tipado tiene que tolerar ambas formas y los diffs no pueden comparar string contra float.
- **Antídoto:** dry-run con las dos columnas (`price` y `promotional_price`) antes y después. Si el pedido es "poner en oferta a X", va `promotional_price: X` dejando `price` como está.

### 21. `parent: 0` en categorías raíz y `subcategories` de solo lectura

- **Qué rompe:** el árbol de categorías. La doc dice que una categoría raíz tiene `parent: null`, pero **v1 devuelve `0`**: un `if parent is None` clasifica mal las raíces y un recorrido que "corrige" la jerarquía reparenta ramas enteras.
- **Y `subcategories` es de solo lectura:** mandarlo en un `PUT` no arma nada. La jerarquía se define seteando `parent` en el **hijo**.
- **Antídoto:** tratar `parent in (None, 0)` como raíz; para mover una categoría, `PUT` sobre el hijo con su nuevo `parent`, nunca sobre el padre.

### 22. Buscar por SKU para después escribir

- **Qué rompe:** se escribe sobre el producto equivocado. **El SKU no es único**: la API no valida duplicados (no hay `422`) y `GET /products/sku/{sku}` devuelve *"el primer producto"* que matchea.
- **Antídoto:** no usar el SKU como clave de escritura. Resolver a `id` una vez, guardarlo y trabajar con el `id`. Antes de un backfill por SKU, listar todos los matches y frenar si hay repetidos.

### 23. `products.id` no entra en un int32

- **Qué rompe:** el id se trunca o desborda, y la escritura cae en otro recurso o falla con un `404` desconcertante. Los ids de producto **ya superan el rango de int32**.
- **Antídoto:** int64 / bigint en todo el pipeline — modelos, columnas de la base y cualquier planilla intermedia — y serializar los ids como enteros de 64 bits o como string.

### 24. Imágenes: campos excluyentes, límites duros y re-render silencioso

- **Qué rompe:** la imagen no queda como se subió, o el `422` apunta al campo equivocado. `src` (URL que Tiendanube descarga) y `attachment` (base64) + `filename` son **excluyentes**; si falta el input, el `422` culpa a `src` aunque el plan fuera usar `attachment`.
- **Límites:** <10 MB por imagen, formatos `.gif .jpg .png .webp`, **máx 250 por producto** y **≤9 inline** al crear el producto.
- **Re-render:** un **WebP se convierte a JPEG a 1024** — un pipeline de thumbnails que espera el archivo original recibe otro formato y otras dimensiones.
- **Antídoto:** crear el producto con pocas imágenes y sumar el resto con `POST /products/{id}/images`; no derivar thumbnails asumiendo el formato subido; validar tamaño y cantidad antes de mandar, porque el `DELETE` de imagen sí es definitivo.

---

## Efecto de desinstalar la app

Al desinstalar, Tiendanube **borra automáticamente** los recursos creados por esa app: **shipping carriers, payment providers, webhooks y scripts**. *"All other resources created will remain in the store"* — productos, categorías, metafields y custom fields sobreviven. Sumado a lo anterior: las promociones de una app de Discounts sí se borran, y el access token queda invalidado.

Consecuencia operativa: reinstalar **no** restaura webhooks ni carriers; hay que recrearlos, y hacerlo sin duplicar (la doc recomienda `GET` del recurso antes de crearlo, porque reinstalar sobre una app ya instalada solo debería regenerar el token).

## Protecciones que sí existen

- **Clientes con órdenes no se borran:** `DELETE /customers/{id}` devuelve `422 "Cannot delete a customer with orders"`.
- **Locations con stock no se borran:** el `DELETE` exige que la location no tenga inventory levels asignados y que no sea la default.
- **Custom fields ajenos no se borran:** el `DELETE` solo alcanza los creados por la propia app; los del merchant o de otra app quedan.
- **`PATCH` de variantes valida antes de tocar:** si una variante no existe, no pertenece al producto o repite combinación de `values`, devuelve `422` con los ids que fallaron (el ejemplo de la doc muestra `duplicate_variant_ids`) y no aplica ningún cambio.
- **`stock_management` es de solo lectura:** no se puede desactivar el control de stock "por accidente" escribiendo ese campo.
- **Variantes con `values` mal armados no entran:** la cantidad de `values` de cada variante debe igualar la cantidad de `attributes` del producto; si no, `422 "The values has the wrong number of elements"` y no se crea nada. Agregar un atributo al producto obliga a mandar el `values` extra en **todas** las variantes.
- **Alternativas reversibles al borrado:** productos → `visibility: "hidden"` (o `"unlisted"`) en vez de `DELETE`; categorías → `visibility: "hidden"`; scripts y webhooks → recrearlos es barato, pero el `DELETE` sigue siendo definitivo.

## Incógnitas

Lo que la documentación oficial **no** define y no hay que afirmar:

1. **¿`DELETE /categories/{id}` arrastra las subcategorías?** La categoría tiene `parent` y `subcategories`, pero la doc no dice qué pasa con los hijos ni con los productos asociados al borrar. **Verificar en demo** con un árbol de tres niveles antes de borrar nada en producción.
2. **¿El borrado de cupones es reversible?** El recurso expone `deleted_at` (*"Date when the coupon was deleted"*), lo que sugiere borrado lógico, pero no hay endpoint documentado para restaurar. `valid` figura como parámetro escribible en `POST /coupons` y el listado filtra por `?status=activated|deactivated`, aunque la doc de `PUT /coupons/{id}` no enumera propiedades. **Verificar en demo** si `PUT` con `valid: false` desactiva el cupón; hasta entonces, tratar el `DELETE` como definitivo.
3. **¿Hay CRUD REST del motor nativo de promociones?** La REST pública solo documenta la Discounts API de callbacks (promociones **de la app partner**). El MCP oficial expone `create_promotion` / `update_promotion` / `delete_promotion`: esa es la vía a usar si hace falta CRUD de promociones nativas, aunque no hay REST pública equivalente que documente su comportamiento. No inventar endpoints `/promotions` fuera del contexto de Discounts (ahí `GET /promotions` existe, pero solo lista las creadas **por la propia app**).
