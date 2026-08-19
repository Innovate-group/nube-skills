# Lo que la API de Tienda Nube no permite

Mapa de límites de la plataforma para el **triage de factibilidad**: antes de prometerle algo a un cliente o escribir código, ubicar el pedido en un cajón.

| Cajón | Significa |
|---|---|
| 🖐️ **Solo admin web** | Existe en el panel, pero no hay endpoint. Se hace a mano o se guía al cliente. |
| ⚠️ **Con condición previa** | Se puede, pero no por el camino estable: Tienda Nube tiene que habilitarlo antes (formulario, mail o plan — sección 7), o vive solo en el canal `unstable`, que puede cambiar o desaparecer sin aviso. |
| ❌ **No se puede** | No existe ni en la API ni en el panel. Solo queda un rodeo, o nada. |

**Reglas de uso:**

- Todo lo de acá está verificado contra la doc oficial `tiendanube.github.io/api-documentation`, versión **2025-03**, al **2026-08-18**. La plataforma cambia: ante una duda de alto impacto, re-verificar antes de comprometerse.
- Donde la doc **no** define un comportamiento, este documento lo dice explícitamente (marcado como *incierto*). No completar el hueco con suposiciones.
- Lo que existe **solo en el canal `unstable`** está marcado como tal: sirve para no decir "no se puede", pero **no se cotiza como estable** — puede cambiar o desaparecer sin aviso.
- Si un endpoint no está ni acá ni en [`api-map.md`](api-map.md), **asumir que no existe**. Inventar un endpoint plausible es el error más caro de esta skill.

## Tabla de contenidos

1. [Órdenes](#1-órdenes)
2. [Configuración de tienda](#2-configuración-de-tienda)
3. [Usuarios, permisos y reportes](#3-usuarios-permisos-y-reportes)
4. [Temas](#4-temas)
5. [Promociones nativas](#5-promociones-nativas)
6. [Otros gaps](#6-otros-gaps)
7. [Detrás de aprobación manual](#7-detrás-de-aprobación-manual)
8. [Scripts](#8-scripts)
9. [Deadline NubeSDK](#9-deadline-nubesdk)
10. [Cómo comunicar un "no se puede"](#10-cómo-comunicar-un-no-se-puede)

---

## 1. Órdenes

Es el área donde más se sobreestima la API. **En la versión estable `2025-03`, la orden creada es casi inmutable**: la doc de `PUT /orders/{id}` dice literalmente *"Change an Order's attributes (just owner_note for now) and/or update an Order's status"*. Ese "just owner_note for now" es todo el margen de escritura que hay en estable. La excepción vive en el canal `unstable` y está descrita abajo de la tabla: `POST /orders/{id}/edit`.

| Se pide | Por qué no se puede | Alternativa real |
|---|---|---|
| Editar ítems, cantidades o precios de un pedido | En `2025-03`, `PUT /orders/{id}` solo acepta `owner_note` y `status`, y de la edición de pedidos la API estable expone únicamente su **lectura**: `GET /orders/{id}/history/editions` | En el canal `unstable` **sí se puede**: `POST /orders/{id}/edit` (ver abajo, con sus restricciones). En estable: 🖐️ editar en el admin, o cancelar y crear una orden nueva con `POST /orders` (número nuevo, sin transacción asociada) |
| Cambiar dirección de envío, datos de facturación o el cliente del pedido | Mismo motivo: no son campos escribibles del `PUT` | 🖐️ Admin web |
| Cambiar el medio de pago de un pedido | `gateway`: *"The internal value is read-only and cannot be set via the API"*. `gateway_id` y `gateway_name` están marcados `[Read-only]` | 🖐️ Admin web |
| Reembolsar (total o parcial) | En `2025-03` no hay endpoint para **pedir** un reembolso. El flujo documentado es al revés: **el merchant lo pide desde el panel** y Tienda Nube hace `POST` al `info.refund_url` que la app de pagos declaró al crear la Transaction | Dos vías: (a) canal `unstable`, `POST /orders/{id}/edit` con `auto_partial_refund: true` — **la única forma en que una app que no es de pagos devuelve dinero** (ver abajo); (b) **app de pagos propia**: contesta `202 Accepted` y, cuando el reembolso se concreta, lo **reporta** con un Transaction Event de tipo `refund` (`POST /orders/{order_id}/transactions/{transaction_id}/events`). Si ninguna aplica: 🖐️ admin web + reembolso por fuera |
| "Marcar el pedido como pagado" | *"In fact, there is no action to pay an order. Orders are paid when sending a Transaction with status success"* | Ser app de pagos y crear la Transaction; si no, 🖐️ admin web |
| Descancelar un pedido | `POST /orders/{id}/open` está documentado como *"Re-open a closed Order"* — revierte un `close`, no un `cancel`. No hay endpoint para revertir `cancelled` | ❌ Crear un pedido nuevo. *Incierto:* la doc no define qué transiciones de `status` acepta el `PUT`; **no experimentar en producción** |
| Emitir o guardar la factura / NFe | *"We currently do not offer an Invoice API"* | Metafields sobre la orden (`GET /metafields/orders?owner_id=…&namespace=nfe&key=list`), con el valor como **string JSON** de la lista de comprobantes (`key`, `link`, `fulfillment_order_id`). **Usar el formato de la doc tal cual** para que otras apps puedan leerlo. Guarda el dato, no emite el comprobante |
| Borrar un pedido | ❌ No hay `DELETE /orders/{id}` en la doc: los endpoints del recurso son listar, obtener, crear, actualizar (limitado), historiales, suscripciones, cerrar, reabrir y cancelar | Cancelar con `POST /orders/{id}/cancel` (irreversible) |
| Que un pedido creado por API descuente stock | Depende del `inventory_behaviour`: con `claim` reserva, con `bypass` no — y **`bypass` es el default**, así que por omisión no descuenta | Mandarlo explícitamente al crear la orden y verificar el resultado |
| Que el merchant vea qué procesador cobró un pedido creado por API | Las órdenes creadas por API no leen la Transaction asociada | La doc recomienda crear la orden como pagada y volcar `external_id` / `external_url` en `owner_note` |

### La excepción: `POST /orders/{id}/edit` (canal `unstable`)

El "no se puede editar pedidos" es cierto en `2025-03` y **falso en `unstable`**: ahí el endpoint existe, está documentado y edita líneas de verdad.

| Qué permite | Detalle |
|---|---|
| Agregar, modificar y quitar productos | `quantity: 0` quita la línea. **Cada ítem necesita `fulfillment_order_id` y `modify_stock`** (si el stock se devuelve o no) |
| Descuentos | Se pueden **quitar** los que haya; agregar, **solo** los de tipo `coupon` |
| Devolver dinero | `auto_partial_refund: true`. Es **la única forma en que una app que no es de pagos reembolsa** |
| Flags de control | `skip_shipping_requote` (no recotizar el envío), `notify_customer`, `reason` |

- **Restricción dura:** solo funciona mientras **todos** los fulfillment orders del pedido estén en `unpacked`. Con uno solo empacado, no hay edición: ahí vuelve a valer la tabla de arriba.
- **El reembolso es asincrónico:** la respuesta trae `auto_partial_refund_status` ∈ `success | skipped | failed`, pero el resultado firme se confirma con el webhook `order/updated`. No dar por devuelta la plata con el 200 del `edit`.
- **No cubre** dirección de envío, datos de facturación, cliente ni medio de pago: para eso sigue siendo 🖐️ admin web.
- **Advertencia obligatoria al cotizar:** `unstable` es un canal sin garantías — puede cambiar de contrato o desaparecer sin aviso. Si se construye sobre esto, va aislado detrás de una capa propia, con monitoreo, y con el riesgo dicho por escrito al cliente. No presentarlo como ✅ "por API" pleno.

**Cerca pero distinto:** `POST /orders/{id}/cancel` sí existe, es irreversible y sus parámetros `email` y `restock` son `true` por default → ver [`operaciones-peligrosas.md`](operaciones-peligrosas.md).

**Detalle que rompe integraciones contables:** aunque la API no permita editar pedidos, **el merchant sí los edita desde el panel**, y esas ediciones cambian el total sin tocar la transacción asociada. La doc lo dice en `total_paid_by_customer`: puede no coincidir con el `total` ni con la transacción, y sube o baja según las ediciones. Para enterarse hay que escuchar el webhook `order/edited` y releer la orden; no alcanza con `order/paid`.

---

## 2. Configuración de tienda

**El recurso Store tiene un solo endpoint: `GET /store`.** No hay `POST`, `PUT`, `PATCH` ni `DELETE`. Todo lo que devuelve es de lectura.

| Se pide | Por qué no se puede | Alternativa real |
|---|---|---|
| Cambiar nombre, descripción, mails o redes de la tienda | Solo `GET /store` | 🖐️ Admin web |
| Activar/desactivar idiomas o cambiar monedas | `languages` y `main_currency` son lectura | 🖐️ Admin web |
| Agregar o cambiar dominios | `domains` y `original_domain` son lectura | 🖐️ Admin web |
| Cambiar el tema activo | `current_theme` es lectura | 🖐️ Admin web (ver sección 4) |
| Editar datos fiscales del negocio (`business_id`, `business_name`, `business_address`) | Lectura | 🖐️ Admin web |
| Forzar o soltar la creación de cuenta en el checkout (`customer_accounts`) | Lectura | 🖐️ Admin web |
| Configurar impuestos | ❌ No existe recurso de impuestos. En toda la doc, `tax` aparece solo como dato de app de pagos o de checkout (`plus_tax` en Payment Provider, `payment_provider_tax_id` en Transaction, el documento fiscal del comprador en Business Rules), nunca como configuración de la tienda | 🖐️ Admin web |
| Configurar zonas, costos o reglas de envío nativas | ❌ No hay escritura. `shipping-carrier` sirve para que **una app de envíos publique sus propias opciones**, no para tocar las zonas nativas del panel. **Leer sí se puede**: `GET /shipping_carriers/options` (scope `read_shipping`) lista **todos** los carriers de la tienda, nativos incluidos, con sus códigos reales — pero no expone zonas ni tarifas | 🖐️ Admin web para configurar, o ⚠️ construir una Shipping App (sección 7). Para saber qué medios de envío tiene activos la tienda, alcanza con la lectura |
| Activar/configurar medios de pago nativos | `GET /payment-options` es **solo lectura** de lo ya activo en el checkout; `payment-provider` es para apps de pago | 🖐️ Admin web, o ⚠️ Payments App (sección 7) |
| Personalizar el checkout | ❌ No hay API de configuración de checkout. Solo hay puntos de extensión para apps de pago (`checkout_js_url`) y NubeSDK | ⚠️/🖐️ según el caso |

**No confundir "no se puede" con "la tienda está suspendida".** Si la tienda no renovó su suscripción (o la app tiene un cargo impago), *toda* la API responde `402 Payment Required`, los scripts dejan de incluirse y los webhooks no se disparan. Se recupera solo cuando se paga. Ante un `402` masivo, la respuesta correcta no es rediseñar la integración: es avisar del pago pendiente.

---

## 3. Usuarios, permisos y reportes

La API está pensada para **datos de la tienda**, no para administrarla como organización: no hay ningún recurso de usuarios ni de inteligencia de negocio.

| Se pide | Por qué no se puede | Alternativa real |
|---|---|---|
| Crear usuarios del panel, asignar roles o permisos | ❌ No existe recurso de staff/usuarios/roles en la API | 🖐️ Admin web |
| Auditar quién hizo qué en el panel | ❌ No hay log de actividad expuesto. Lo más cercano es `GET /orders/{id}/history/editions` y `/history/values`, acotado a una orden | 🖐️ Admin web |
| Traer los reportes o métricas del panel | ❌ No hay API de analytics ni de reportes | Reconstruir paginando `GET /orders` |
| Reconstruir métricas de ventas por API | Se puede, con dos límites duros: **una query devuelve como máximo 10.000 items** (*"Query results are limited to 10.000 items"*) y el rate limit es un leaky bucket de 40 requests que drena a **2 req/s** por tienda-app (×10 en planes Next/Evolution) | Particionar con `created_at_min` / `created_at_max` (la propia doc recomienda "import by period"), `per_page=100`, y presupuestar el tiempo: 10.000 pedidos ≈ 100 requests ≈ 50 s de red en un plan estándar |
| Exportar un reporte a CSV/Excel | ❌ No hay endpoint de export | 🖐️ Descargar del panel |

---

## 4. Temas

**No hay Admin API de temas.** En toda la doc de recursos, lo único relacionado es `current_theme` dentro de `GET /store` (lectura) y los selectores HTML que menciona la doc de Scripts.

| Se pide | Por qué no se puede | Alternativa real |
|---|---|---|
| Leer o editar plantillas, snippets o settings del tema | ❌ No existe recurso Theme en la Admin API | Es otro sistema (CLI de temas + Partner Portal) → skill **`nube-skills-themes`** |
| Publicar/cambiar el tema activo | `current_theme` es lectura | 🖐️ Admin web |
| Inyectar HTML/JS en el storefront desde la Admin API | ❌ No por Admin API | Scripts de app (sección 8) o NubeSDK, con sus condiciones |

**Brecha conocida (no es API pública soportada):** el CLI de temas habla con una API de *theme-installations* **no documentada** — `GET/POST /v1/{store_id}/theme-installations` y `…/{id}/publish|fork|clone|unfork|file-hashes|files`. Aplica **solo a temas Ipanema**, con un máximo de **2 instalaciones por tienda**, y **el token sale de la autenticación del CLI, no de un scope OAuth**: no hay forma soportada de usarla desde una app ni de pedirle permiso al merchant. Sirve para entender que el CLI puede hacer cosas que la Admin API no expone; el camino real sigue siendo la skill **`nube-skills-themes`**. No ofrecerla como integración.

---

## 5. Promociones nativas

Esto genera confusión constante: **la "Discounts API" pública no es un CRUD de las promociones del panel**, es un mecanismo de *callbacks* para apps de promociones.

- El partner registra una **callback URL**; Tienda Nube le manda el estado del carrito **en cada cambio** y la app responde con *comandos* de aplicar/quitar descuento.
- **Timeout de 800 ms** para responder. Si la app no responde a tiempo, el carrito queda sin cambios; si responde algo que no cumple la especificación, la plataforma **quita todos los descuentos aplicados** ("we will try to protect the merchant from money losses instead of getting a new sale").
- Seguridad hoy: Tienda Nube comparte una **lista de IPs para whitelist (WAF)** y el partner es responsable de bloquear cualquier otra conexión. La firma de cada request con un token secreto está en la doc bajo **"Upcoming changes"** — todavía no es el mecanismo vigente, no diseñar la seguridad asumiéndola.
- `POST /promotions` **sí existe**: registra en la tienda las promociones **de tu app** (es lo que habilita el tráfico de callbacks) y `GET /promotions` lista las no borradas creadas por tu app. Ninguno toca las promociones nativas del panel. `PUT /discounts/callbacks` solo cambia la URL del callback: **borrarla no se puede**.
- Si el merchant **desinstala la app de promociones, todas sus promociones se borran permanentemente** y deja de llegar tráfico de carrito.
- La doc aclara que **multimoneda no está soportado** en esta API: no recomendarla en tiendas con esa feature.
- Si el partner deja de responder o responde tarde, **se quitan las promociones registradas en updates anteriores**: la disponibilidad del servicio del partner es parte del producto, no un detalle de infra.
- Si una promoción deja de existir o se desactiva, **es responsabilidad del partner quitar el descuento del carrito**; si no, el carrito lo sigue aplicando y el merchant pierde plata.

**Brecha conocida (marcada como tal):** el MCP oficial de administración expone `create_promotion` / `update_promotion` / `delete_promotion` sobre las promociones nativas; la REST pública **no** tiene ese CRUD nativo — su `POST /promotions` pertenece al mecanismo de apps partner descrito arriba y su contrato exacto la doc lo delega a un `Openapi.yml` externo (**[incierto]** sin ese archivo no se puede afirmar el payload). Si el pedido es "crear promociones nativas por API", la vía comprobada es el **MCP oficial** (ver [`ejecucion.md`](ejecucion.md)).

**Lo que sí resuelve la mayoría de los pedidos reales:** los **cupones** tienen CRUD completo (`/coupons`).

---

## 6. Otros gaps

Límites sueltos que aparecen a mitad de una implementación y hacen replanificar. Todos verificados en la doc del recurso correspondiente.

| Se pide | Por qué no se puede | Alternativa real |
|---|---|---|
| API de facturación electrónica | *"We currently do not offer an Invoice API"* | Metafields namespace `nfe` (sección 1) |
| Importar/exportar catálogo por CSV | ❌ No hay endpoint de import/export en la doc | Recorrer por API producto por producto, o 🖐️ usar el importador del panel |
| Crear un carrito o agregarle ítems por API | El recurso Cart solo tiene `GET /carts/{id}`, `DELETE /carts/{id}/line-items/{id}` y `DELETE /carts/{id}/coupons/{id}`. Además, un carrito ya convertido (o en proceso de conversión) a orden **deja de ser accesible** | Draft Orders: `POST /draft_orders` + `POST /draft_orders/{id}/confirm` |
| Editar un draft order | Solo hay listar, obtener, crear, confirmar y borrar. **No hay `PUT`** | Borrar y volver a crear |
| Borrar un cliente con pedidos | Documentado: *"It's not possible to delete customers with associated orders"* → `422` con `"Cannot delete a customer with orders"` | Actualizar/anonimizar con `PUT /customers/{id}`; para bajas legales, el flujo LGPD |
| Loguear un cliente, manejar su sesión o resetear su contraseña | ❌ No hay endpoint de login/sesión ni de reset de password, y `PUT /customers/{id}` no acepta `password` | **En el alta sí**: `POST /customers` acepta `password` y `send_email_invite: true` (crea la cuenta con clave y manda el mail de invitación). Para identificar al cliente ya logueado en el storefront, ⚠️ App Proxy (sección 7): firma HMAC sobre `X-Store-Id + X-Customer-Id + X-Request-Id` concatenados **sin separador** |
| Crear o modificar kits (bundles) | *"This is a read-only resource. Kits are managed through the store's admin panel"*. Además solo admiten componentes de un producto de **una sola variante** | 🖐️ Admin web |
| Crear o borrar plantillas de email | Solo `GET /email-templates`, `GET /email-templates/{id}` y `PUT /email-templates/{id}`, sobre **8 tipos fijos** (`orderconfirmation`, `ordershipped`, `ordercancelled`, `ordercaptured`, `abandonedcheckoutrecover`, `customer_activate_account`, `customer_reset_password`, `customer_welcome_account`) | Editar las existentes (asunto, texto y HTML por idioma) |
| Recuperar carritos abandonados viejos | *"it is not possible to fetch abandoned checkouts from over 30 days ago"* y se borran a los 90 días. Solo se pueden leer y crear un cupón asociado | Sincronizar seguido; no diseñar procesos que dependan de histórico largo |
| Gestionar canales de venta | ❌ No existe recurso de sales channels. `channels` es solo un **filtro de lectura** en `GET /orders` (`form`, `store`, `api`, `meli`, `pos`) | 🖐️ Admin web / app del canal |
| Guardar metafields en cualquier recurso | Los metafields **solo** se asocian a `Product`, `Product_Variant`, `Category`, `Page`, `Order` y `Customer`. No hay metafields de tienda, cupón, location ni fulfillment order | Guardarlo del lado de la app, o colgarlo de una de las 6 entidades soportadas |
| Poner un cliente en dos listas de precios (B2B) | *"A customer can only be associated with one price table at a time"*: si un cliente del payload ya está asociado, **falla el lote entero** con `409 Conflict` | Desasociar primero (`DELETE /products/price-tables/{id}/customers/{customerId}`) y después asociar a la nueva |
| Registrar una app, cambiar sus scopes o consultar su ID por API | ❌ El alta de la app y sus permisos viven en el Partner Portal. Lo único que la API expone a nivel app son los endpoints de Billing (`POST /plans`, `/subscriptions`, `/charges`), bajo autenticación *Partner-Action* con URL `…/{version}/apps/{app_id}/…` — o sea que el `app_id` es un dato de entrada, no algo que se consulte | 🖐️ Partner Portal |

---

## 7. Detrás de aprobación manual

No es "no se puede": es **"pedí permiso primero"**. Al cotizar, tratarlo como dependencia externa **sin plazo garantizado**.

| Capacidad | Cómo se habilita (según la doc) |
|---|---|
| **Shipping API** (crear shipping carriers y opciones) | Crear la app en el Partner Portal y completar el formulario que indica la doc (`forms.gle/oqP1BrtwMzNb7xCM9`) para que el Platform Team dé acceso a los endpoints de shipping. Consultas: `partners@nuvemshop.com.br` / `partners@tiendanube.com` |
| **Payments API** (payment providers) | Crear la app y pedirle al Partner Support Team (`partners@nuvemshop.com.br` / `partners@tiendanube.com`) que habilite la app para las Payments APIs |
| **Business Rules** (filtrar envíos/pagos/locations en el checkout) | Crear la app y pedirle al Partner Support Team que la habilite |
| **App Proxy** (servir contenido propio bajo el dominio de la tienda) | Escribir a `parceiros@nuvemshop.com.br` / `socios@tiendanube.com` para que lo configuren |
| **Scripts con evento `onload`** | Mail previo a `api@nuvemshop.com.br` explicando la funcionalidad y el motivo, con `APP_ID` y `APP_NAME` en el asunto. Sin aprobación, el script se crea como `onfirstinteraction`. No hace falta si el script corre **solo** en el checkout |
| **Labels API** (etiquetas de envío) | Gated por la feature `fulfillment_order_label_api`, que hoy se otorga solo en plan **Next**; sin ella todo endpoint de Labels devuelve `403` (ver [`api-map.md` §3 y §7](api-map.md#7-feature-detection)). Antes de cotizarla, mirar `features` en `GET /store`; la doc de Shipping Carrier solo la nombra de refilón (el `callback_labels_url` *"is used by the Labels API for asynchronous label generation"*), así que el trámite concreto se confirma con Partner Support |
| **Nueva Fulfillment Events API con multi-inventario** | *"currently being rolled out to every merchant... Please contact us to activate this new version in your stores if needed"* (doc de Shipping Carrier). Para la nueva Product API con multi-inventario la doc **no** enuncia un trámite equivalente: la guía de multi-inventario describe el cambio de comportamiento, no una habilitación |
| **Disputes API** | Solo tiene sentido para apps de pago: requiere scope `write_payments` y filtra por el `app_id` del token |

**Cómo pedirlo bien** (aplica a todas las filas): mandar el `APP_ID`, el nombre de la app, para qué tienda(s) y el caso de uso concreto. Y avisarle al cliente que el reloj del proyecto no arranca hasta que llega la habilitación: es la dependencia externa que más veces desarma un cronograma.

---

## 8. Scripts

**Los scripts no se crean por API.** Se crean en el **Partner Portal** (Apps → detalle de la app → *Create script*) y la app tiene que haber sido registrada con el permiso `scripts`; sin ese permiso, la sección de Scripts ni siquiera aparece en el portal.

| Se pide | Realidad |
|---|---|
| "Subir un script a la tienda por API" | ❌ El código del script se sube como archivo/versión en el portal (o se apunta a una URL con *Development mode* en tiendas demo) |
| `POST /scripts` | Solo **asocia** a una tienda un script ya creado y marcado como **no auto-instalable**, mandando `script_id` y `query_params`. Es también el consentimiento del partner para que ese script cargue en esa tienda |
| Scripts auto-instalables | Se activan solos en cada tienda que instala la app: no requieren llamada a la API |
| Elegir cuándo carga | `onfirstinteraction` (default, recomendado) u `onload` (⚠️ requiere aprobación, sección 7) |
| Dónde corre | Páginas de tienda/producto y checkout. **No** reemplaza al tema: para storefront de verdad, ver `nube-skills-themes` |
| Probar cambios sin desplegar | *Development mode* permite apuntar el script a una URL local o de CDN, pero **solo carga en tiendas demo** que tengan la app instalada |
| Depender del tema | La doc es explícita: *"The script should not depend on any JavaScript available in the store's theme. Not even jQuery"* (hay un helper `useJquery`, que garantiza que jQuery exista, no su versión) |
| Al desinstalar la app | El script deja de cargarse (y la doc de Webhooks/Discounts aclara que otros recursos creados por la app también se van) |

---

## 9. Deadline NubeSDK

Afecta la **planificación**, no solo el "se puede / no se puede": hay apps propias en juego.

- **Confirmado en la doc** (Scripts → Checkout Page): *"Mandatory migration for Checkout scripts by 10/30. If your application uses scripts in the Checkout, you must migrate them to the new SDK to ensure they continue working after that date."* Es decir: **scripts de checkout sin NubeSDK dejan de funcionar**.
- **Dato de la comunicación a partners, no presente en la doc mirrored — verificar antes de citárselo a un cliente:** desde el **30/08/2026** las apps que inyectan scripts sin NubeSDK no reciben instalaciones nuevas, y desde el **30/10/2026** empieza la desinstalación progresiva. La fecha `10/30` de la doc es consistente con la segunda, pero la doc pública no enuncia la primera.
- **Alcance reportado:** también aplicaría a **apps privadas / "Para tus clientes" con `write_scripts`**, no solo a apps públicas del App Store. La doc pública no lo detalla → tratar como probable y confirmarlo con el Partner Support antes de planificar sobre eso.
- **Qué hacer ahora:** inventariar qué apps propias inyectan scripts, empezar por las de checkout, y no diseñar features nuevas sobre `POST /scripts` sin plan de migración.

---

## 10. Cómo comunicar un "no se puede"

1. **Nombrar el cajón antes de nada:** ✅ por API · ⚠️ con condición previa (aprobación de TN o canal `unstable`) · 🖐️ solo admin web · ❌ no se puede. Nunca prometer sin haber pasado por acá.
2. **Citar la fuente**, no la intuición: "la doc de `PUT /orders/{id}` dice que solo acepta `owner_note` y `status`". Si no hay fuente, decir *"la doc no lo define"* y proponer cómo verificarlo en una tienda demo.
3. **Ofrecer la alternativa real** en la misma frase: el rodeo por API, el paso manual en el panel, o el trámite de habilitación con su costo de tiempo.
4. **No prometer plazos** de las aprobaciones de la sección 7: dependen de Tienda Nube.
5. **Dejar registrada la fecha de verificación.** Si la respuesta se apoya en algo que la doc no define, decirlo y proponer la prueba en tienda demo en vez de afirmarlo.

**Respuesta modelo:**

> "Editar el precio de una línea de un pedido: ⚠️ **se puede, pero solo en el canal `unstable`**. En la API estable (`2025-03`) es 🖐️ admin web — `PUT /orders/{id}` acepta únicamente `owner_note` y `status`, y de la edición de pedidos solo deja **leer** el historial (`GET /orders/{id}/history/editions`). La vía por API es `POST /orders/{id}/edit` (con `auto_partial_refund` si además hay que devolver plata), pero exige que **todos** los fulfillment orders estén en `unpacked` y ese canal puede cambiar sin aviso: si la tomamos, va con esa advertencia por escrito. Si no, lo edita alguien en el panel, o se cancela el pedido y se crea uno nuevo por API, con número nuevo y sin la transacción original asociada."
