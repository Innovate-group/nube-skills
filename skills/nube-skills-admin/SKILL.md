---
name: nube-skills-admin
description: "Expert on the TiendaNube/Nuvemshop admin backoffice and Admin API (2025-03). Use for anything about managing a store's data — products, variants, stock and prices, categories, orders, customers, coupons, promotions, metafields, custom fields, fulfillment and shipping, webhooks, pages — whether the question is 'can TiendaNube do X?', 'how do I bulk-update this?', or building an app against the API. Triages what is possible via API, what needs TiendaNube's manual approval, what is admin-panel-only, and what is impossible; executes reads freely and writes only with dry-run, backup and explicit confirmation. Triggers: backoffice, panel de tienda nube, API de tienda nube, actualizar productos masivo, stock, precios, pedidos, cupones, metafields, webhooks, se puede hacer X en tiendanube. NOT for theme/storefront work (use nube-skills-themes) and NOT for Shopify."
---

# Backoffice y Admin API de Tienda Nube

Cubre el lado de la administración de una tienda: catálogo, stock y precios, órdenes, clientes, cupones, metafields, logística, webhooks y contenido — tanto para **responder qué se puede** antes de prometerle algo a un cliente, como para **operar** una tienda real y para **construir** apps contra la API.

El storefront (temas, secciones, Liquid/Twig, traducciones del tema) es territorio de `nube-skills-themes` y sus skills hermanas: si el pedido es visual, derivá ahí.

Versión de API por defecto: **`2025-03`**. Nunca `v1` en desarrollo nuevo — la doc oficial declara que `v1` no recibe features nuevas después de ese release.

## Los tres usos, un solo flujo

El pedido entra por una de tres puertas, y las tres pasan por el mismo Paso 1:

| Llega como | Se ve así | Qué necesita |
|---|---|---|
| **Consultoría** | "¿se puede hacer X en Tienda Nube?", "¿cuánto sale automatizar Y?" | Paso 1 (triage) y nada más. **No hace falta token.** La respuesta correcta es el cajón + la fuente + la alternativa |
| **Operación** | "actualizá los precios de esta lista", "cargá estos 200 productos", "corregí el stock" | Paso 0 → Paso 1 → Paso 2 con el protocolo de escritura completo |
| **Construcción** | "estoy armando una app que sincroniza X", "¿qué scopes pido?", "¿cómo pagino esto?" | Paso 1 para validar que el diseño es posible, y `references/api-map.md` para los límites duros que van a definir la arquitectura |

En los tres casos la falla más cara es la misma: **afirmar que algo se puede sin haberlo verificado**. Ante la duda, el triage antes que la promesa.

## Paso 0 — Capacidades reales de ESTA tienda

Nunca respondas ni ejecutes sobre "Tienda Nube en general": el comportamiento correcto depende del plan y de las features de la tienda concreta.

**1. Identificá la vía de acceso.** Hay tres, en orden de preferencia:

| Vía | Cuándo | Qué habilita |
|---|---|---|
| **MCP oficial** conectado (`admin-mcp.tiendanube.com/mcp`) | Consulta puntual o cambio chico sobre catálogo | Productos, categorías, cupones, promociones nativas; órdenes y clientes solo lectura |
| **Token propio** de una app instalada | Lotes, escrituras riesgosas, o cualquier recurso fuera del catálogo | Todo lo que la API expone, con `--dry-run` y `--backup` |
| **Solo admin web** | No hay token ni MCP | La skill sigue siendo útil: triage + guía por el panel |

Para **conseguir** ese token propio, la vía más simple es la **Aplicación a medida**: el propio comerciante la crea desde su admin (*Aplicaciones a medida → Crear*), elige scopes y obtiene el token, sin cuenta de partner, sin OAuth y sin homologación. Tiene gate por plan (AR: Escala o Evolución · BR: Escala o Next) y **el token se muestra una sola vez**. Una app a medida por integración, para poder revocarlas por separado; agregar scopes obliga a reinstalar y emite token nuevo. Si el plan no la habilita, la vía es una app de partner con link de instalación privado, que funciona en cualquier plan.

**2. Leé las capacidades de la tienda** antes de cualquier operación no trivial:

```bash
# desde la carpeta de esta skill
python3 scripts/tn-api.py GET store --param fields=name,plan_name,features
```

Qué cambia según lo que devuelva:

- **`features` incluye `inventory-levels`** → el stock ya **no** se escribe en `variant.stock`, va por `variant.inventory_levels[]` con `location_id` explícito. Escribir en `variant.stock` con multi-location vuelca todo el total en la primera location.
- **`features` incluye `fulfillment-orders`** → despachar por `/orders/{id}/fulfillment-orders/{fid}`; los endpoints legacy (`/orders/{id}/fulfill`, `/pack`, `/fulfillments`) impactan **solo en el primer** fulfillment order.
- **`features` incluye `fulfillment_order_label_api`** → Labels API disponible (hoy solo plan Next). Sin la feature, todo endpoint de Labels responde `403`.
- **Plan Next / Evolution** → rate limit ×10 (20 req/s). Ojo: el script siempre espacia a 2 req/s, no se adapta.
- **`402` en cualquier request** → tienda o app impaga: la API entera está suspendida, y los webhooks y scripts también. No es un problema técnico: frená y avisá que hay que regularizar el pago.

La doc **no publica la lista completa** de valores de `features` ni qué feature trae cada plan: leé el array real de la tienda, no lo asumas.

**3. Confirmá contra qué tienda estás operando.** El mismo `GET /store` devuelve `name`: decilo en voz alta antes de cualquier lote. Un token por tienda, y el `store_id` es el `user_id` que devolvió el intercambio del `code` de OAuth. Las credenciales van por variables de entorno (`TN_STORE_ID`, `TN_ACCESS_TOKEN`, `TN_USER_AGENT`), nunca en el repo ni en la conversación.

**Si no hay ninguna de las tres vías, no te bloquees.** Sin token y sin MCP la skill sigue sirviendo: cambia el brazo, no el criterio. Hacé el triage igual —la mitad de los pedidos que "no se pueden por API" tampoco se pueden en el panel, y eso hay que decirlo antes de mandar a nadie a buscar un botón— y después guiá por el admin web **por resultado, no por click** (el panel cambia de layout seguido). Si el pedido es un lote de más de ~50 registros, algo repetitivo o algo que necesita rollback, la recomendación es conseguir el token: se paga en el primer lote.

## Paso 1 — Triage de factibilidad

**Antes de prometer, cotizar o escribir una línea de código, ubicá el pedido en un cajón y comunicalo.** Es el paso que más valor aporta y el que más caro sale saltearse.

| Cajón | Significa | Ejemplos |
|---|---|---|
| ✅ **Por API** | Se hace y se automatiza | Crear/editar productos y variantes · stock y precios masivos (`PATCH /products/stock-price`, ≤50 variantes) · categorías · cupones (CRUD completo) · clientes · metafields y custom fields · páginas y blog · editar los email templates (8 tipos fijos: no se crean ni se borran) |
| ⚠️ **Con condición previa** | Se puede, pero no por el camino estable: hace falta permiso de TN, o vive en el canal `unstable` (que puede cambiar o desaparecer sin aviso) | Shipping API (formulario) · Payments API (mail a partners) · Business Rules y App Proxy (soporte) · scripts con evento `onload` (mail a `api@`) · Labels API (plan Next + feature) · **editar un pedido** y **reembolso parcial** con `POST /orders/{id}/edit` (`unstable`) |
| 🖐️ **Solo admin web** | Existe en el panel, no en la API | Configuración de tienda (nombre, idiomas, monedas, dominios, tema) · impuestos · zonas y costos de envío nativos · medios de pago nativos · usuarios y permisos · reportes · kits |
| ❌ **No se puede** | Ni API ni panel, o directamente no existe | Import/export CSV por API · Invoice API (workaround: metafields `nfe`) · descancelar un pedido · borrar un pedido · editar un draft order (no hay `PUT`) · crear carritos · API de temas · analytics |

Cómo se comunica un cajón que no es ✅ (detalle y respuesta modelo en `references/no-se-puede.md` §10):

1. **Nombrar el cajón primero**, antes de cualquier explicación.
2. **Citar la fuente**, no la intuición ("la doc de `PUT /orders/{id}` dice que solo acepta `owner_note` y `status`"). Si la doc no lo define, **decilo** y proponé cómo verificarlo en una tienda demo.
3. **Ofrecer la alternativa real** en la misma frase: el rodeo por API, el paso manual en el panel, o el trámite con su costo de tiempo.
4. **No prometer plazos** de las aprobaciones del cajón ⚠️: dependen de Tienda Nube.

Forma de una respuesta bien armada, para copiar la estructura:

> "Editar el precio de una línea de un pedido ya cerrado: ⚠️ **se puede, pero solo en el canal `unstable`**. En `2025-03` estable, `PUT /orders/{id}` acepta únicamente `owner_note` y `status`. En `unstable`, `POST /orders/{id}/edit` agrega, modifica y quita ítems, y con `auto_partial_refund: true` es el único modo en que una app que no es de pagos devuelve plata. Dos condiciones: solo mientras **todos** los fulfillment orders estén en `unpacked`, y `unstable` puede cambiar sin aviso. Opciones: lo edita alguien en el panel, o se asume la dependencia de `unstable` con plan de contingencia."

Los campos exactos del `edit` (`fulfillment_order_id` y `modify_stock` por ítem, `quantity: 0` para quitar) y el carácter asincrónico del reembolso están en `references/no-se-puede.md` §1.

Casos límite frecuentes: los **cupones** (CRUD completo) resuelven la mayoría de los pedidos que llegan como "promociones"; las **promociones nativas** solo tienen vía comprobada por el MCP oficial, no por REST pública; y como el merchant también edita pedidos desde el panel, para enterarse hay que escuchar el webhook `order/edited` y releer la orden, no alcanza con `order/paid`.

**Cómo resolver un pedido que no está en la tabla**, en este orden:

1. Buscá el recurso en `references/api-map.md` §3. Si está con la operación que hace falta → ✅.
2. Si no está, buscá el caso en `references/no-se-puede.md` — está organizado por área y cada fila trae el porqué y la alternativa.
3. Si no aparece en ninguno de los dos, **tratalo como inexistente** y decilo así: *"no está documentado; si es de alto impacto, lo verifico contra la doc oficial / en una tienda demo antes de comprometerlo"*. Inventar un endpoint plausible por analogía con Shopify es el error más caro de esta skill.

Y una distinción que hay que hacer siempre antes de rediseñar nada: **un `402` masivo no es un límite de la plataforma**, es una tienda o una app impaga. La respuesta correcta es avisar del pago pendiente, no buscar otro camino técnico.

**Si el pedido cae en ⚠️ por aprobación**, tratalo en el plan como **dependencia externa sin plazo garantizado**: el reloj del proyecto no arranca hasta que llega la habilitación, y es lo que más veces desarma un cronograma. Para pedirla bien, mandá `APP_ID`, nombre de la app, para qué tienda(s) y el caso de uso concreto (el destinatario de cada trámite está en `references/no-se-puede.md` §7). **Si cae en ⚠️ por `unstable`**, la dependencia no es de plazo sino de estabilidad: decíselo al cliente por escrito antes de cerrar el alcance y dejá previsto el fallback manual por panel.

**Alerta de planificación para cualquier cosa que dependa de scripts inyectados:** la doc confirma migración obligatoria a **NubeSDK para scripts de checkout**. Además circula —por comunicación a partners, **no** presente en la doc pública— que desde el **30/08/2026** las apps que inyectan scripts sin NubeSDK no reciben instalaciones nuevas y desde el **30/10/2026** empieza la desinstalación progresiva, alcanzando también a apps privadas con `write_scripts`. Verificalo con Partner Support antes de citárselo a un cliente, pero **no diseñes features nuevas sobre `POST /scripts` sin plan de migración**.

## Paso 2 — Ejecutar

**Lectura: libre.** Paginar, filtrar y reportar no requiere confirmación. Usá `--paginate` y presupuestá el tiempo (2 req/s: 5.000 productos ≈ 25 s; 20.000 órdenes particionadas por fecha ≈ 100 s). Tres cosas que rompen recorridos silenciosamente:

- **`GET /orders` corta en 10.000 ítems por query.** Particionar con `created_at_min` / `created_at_max`, nunca traer "todo el histórico" de una.
- **Tienda Nube clampea `per_page` sin avisar.** Por eso el corte de un recorrido se compara contra el tamaño real de la página 1, no contra el `per_page` pedido — el script ya lo hace.
- **Un `404` al paginar es fin de colección**, no un error (solo si `page > 1`; en la página 1 sí es ruta inexistente).

**Escritura: cinco tiempos, siempre, sin excepción.** La Admin API **no tiene deshacer ni papelera**.

1. **Dry-run** — `--dry-run` imprime método, URL, headers (token enmascarado) y body sin tocar la red.
2. **Diff registro por registro** — mostrar valor actual → valor nuevo. Si son 300 registros, mostrar el patrón, el conteo y una muestra representativa, más los casos raros completos.
3. **Backup a archivo** — `--backup PATH` hace el `GET` previo y guarda el estado actual. Si ese `GET` falla, **la escritura se aborta** (exit 1): sin red de seguridad no se escribe.
4. **Confirmación explícita del dev** — decir cuántos registros se tocan, qué campos y qué es irreversible. **Frenar y esperar respuesta.** Un "dale" a un plan de 5 registros no autoriza 500.
5. **Ejecución con reporte** — respetando el rate limit, y cerrando con **aplicados / fallidos / pendientes** y la ruta del backup.

Elegí el brazo ejecutor según `references/ejecucion.md` §1: MCP oficial para consultas y cambios chicos de catálogo, script `tn-api.py` para lotes, escrituras riesgosas y todo lo que el MCP no cubre (fulfillment, metafields, locations, webhooks, draft orders, páginas, escritura sobre pedidos). El MCP tiene topes propios que obligan a partir un lote (50 variantes en bulk de stock/precio, 20 productos en bulk de visibilidad); partirlo a mano en la conversación es peor que hacerlo con el script.

```bash
# 1+2: ver qué haría, sin ejecutar
python3 scripts/tn-api.py PATCH products/123/variants --data-file cambio.json --dry-run

# 3+5: backup previo y ejecución (tras confirmación explícita)
python3 scripts/tn-api.py PATCH products/123/variants --data-file cambio.json --backup backups/123.json
```

Para un cambio masivo de catálogo, elegí el endpoint antes de armar el lote:

| Qué se cambia | Endpoint | Tope por request |
|---|---|---|
| Solo precio y/o stock, de muchas variantes de muchos productos | `PATCH /products/stock-price` | **50 variantes** contando todo el batch (`422` si te pasás) |
| Cualquier otro campo de variantes de **un** producto | `PATCH /products/{id}/variants` | Peso del payload, no cantidad fija |
| Campos del producto (nombre, descripción, SEO, categorías) | `PUT /products/{id}` | Uno por request — hace merge: omitir un campo es seguro, mandarlo vacío borra |
| Leer el estado previo de muchos productos por id | `GET /products?ids=` | **30 ids** por request |

Ante un error a mitad de un lote: **no relanzar el lote entero**. Identificar qué ids se aplicaron, rehacer el diff contra el estado actual y correr solo el resto. `PATCH /products/stock-price` devuelve `success` **por variante**: un lote puede quedar aplicado a medias, así que leé el resultado registro por registro en vez de asumir que un `200` significa que entró todo.

El reporte de cierre de cualquier lote tiene tres números y una ruta, y no se omite aunque haya salido todo bien:

```
Aplicados: 187 · Fallidos: 3 (ids 4412, 4419, 4501 — 422 precio inválido) · Pendientes: 0
Backup: backups/precios-2026-08-18/
```

### Si lo que se construye es una app

Cuatro decisiones que se toman al principio y son caras de revertir:

- **Los scopes se piden completos de entrada.** Un scope de `write` implica su `read`, y hay herencias automáticas (`read_products` o `*_shipping` traen `read_locations`; `read_orders` trae `read_fulfillment_orders`). Tabla completa en `references/api-map.md` §5.
- **Agregar un scope después obliga a que el merchant vuelva a autorizar**, y ese token nuevo invalida el anterior (documentado para las aplicaciones a medida; **[incierto]** en apps de partner — `references/api-map.md` §2): planificalo como una reinstalación coordinada tienda por tienda, refrescando los tokens guardados en el mismo momento.
- **Los access tokens no expiran** (no hay refresh token): se invalidan solo al generar uno nuevo o si el merchant desinstala. Si dejó de andar, hay que reinstalar.
- **Desinstalar la app borra lo que la app creó**: shipping carriers, payment providers, webhooks y scripts. Productos, categorías, metafields y custom fields quedan. Reinstalar **no** los restaura: hay que recrearlos sin duplicar.

## Guardarraíles (aplicalos sin que te los pidan)

Resumen accionable; el porqué y el antídoto de cada operación están en `references/operaciones-peligrosas.md`, y el detalle de los campos por idioma en `references/api-map.md` §2.

| Regla | Por qué |
|---|---|
| **`PATCH`, nunca `PUT`, para la colección de variantes** | El `PUT` de colección reemplaza todo y matchea por combinación de `values`, **no por `id`**: toda variante que no venga en el body se borra con su stock y sus custom fields. Renombrar un talle = borrar y recrear |
| **Nunca mandar `categories: []`** en `PUT /products/{id}` | Deja el producto sin categoría. **Omitir el campo ≠ mandarlo vacío** |
| **Nunca mandar un body parcial** a `PUT /{entidad}/{id}/custom-fields/values` | Sobrescribe: lo que no venga se desasocia. `GET` → merge en memoria → set completo |
| **`POST /orders/{id}/cancel` con `restock` y `email` explícitos** | Ambos son `true` por default: cancelar "en silencio" manda mail real al comprador y mueve inventario. Es irreversible |
| **`notify_customer: false`** en `PATCH` de fulfillment order salvo que notificar sea el pedido | El default del campo es `false`, pero los ejemplos de la doc lo muestran en `true`: copiar el ejemplo notifica |
| **`DELETE` fuera de alcance** salvo pedido expreso y por escrito | No hay restauración documentada para ningún recurso. Preferir lo reversible: producto → `visibility: "hidden"`; cupón → `valid: false` (la doc no confirma que sea escribible: verificar en demo) |
| **Lotes chicos y espaciados** | Bucket de 40 que drena a 2 req/s por par (tienda, app); el exceso **se encola mientras el bucket tenga lugar** y recién ahí empieza el `429` (50 de golpe = 40 encoladas + 10 perdidas). En variantes el costo es el peso del payload: ante `429`, mandar menos variantes por request, no esperar más |
| **`stock` entero ≥ 0** validado antes de mandar | `stock: ""` (o `null` en `POST /products/{id}/variants/stock` con `action: replace`) es **stock infinito**, sin error visible |
| **El precio se escribe en la variante, nunca en el producto** | Todo producto tiene al menos una variante aunque el panel no la muestre. Mandar `price` en `PUT /products/{id}` **no hace nada y no devuelve error**: el precio va en `PUT /products/{pid}/variants/{vid}`. Falla silenciosa clásica de un lote de precios |
| **`price` es el precio tachado; `promotional_price` es lo que paga el cliente** | Está invertido respecto de Shopify, y `compare_at_price` no existe acá. Confundirlos publica el precio de oferta como precio de lista (y al revés) en todo el catálogo tocado. `promotional_price: null` = sin oferta; `price: null` en una variante = "consultar precio", no gratis |
| **Nunca `published` y `visibility` juntos** | `422` y ese producto queda sin actualizar mientras el resto del lote sí |
| **Handlers de webhook idempotentes** | Sin garantía de orden y con entregas duplicadas; timeout de 3 s, hasta 16 reintentos en 48 h |
| **`name`, `description`, `handle` y `seo_*` son objetos por idioma** | Un string plano se aplica a **todos** los idiomas de la tienda. En una tienda multi-idioma eso pisa la traducción sin avisar |
| **Órdenes creadas por API no reservan stock** salvo `inventory_behaviour: claim` | El default es `bypass`: el inventario queda inflado y la tienda sobrevende |

**Cómo se escribe un producto sin romper lo que no tocás.** `PUT /products/{id}` **hace merge de los campos omitidos** — la doc lo dice explícitamente para la categoría ("si querés mantener la categoría actual, debés incluir el `category_id` o bien **omitir** el campo"), y el ejemplo canónico devuelve el array `variants` intacto. Lo destructivo es mandar la colección **vacía** (`categories: []` borra) y `PUT /products/{id}/variants`, la colección de variantes, que sí es reemplazo total. Regla práctica: omití lo que no cambiás, nunca lo mandes vacío.

## Navegación de referencias

| Leé | Cuando |
|---|---|
| [`references/api-map.md`](references/api-map.md) | Necesitás saber **qué endpoint existe** y con qué límites: base y versionado, autenticación OAuth y headers, tabla de recursos por área (catálogo, ventas, logística, plataforma), rate limit, paginación, caps de cantidad, scopes y sus herencias, formatos de error y feature detection |
| [`references/no-se-puede.md`](references/no-se-puede.md) | Estás en el **Paso 1**: qué no permite la plataforma y cuál es la alternativa real — órdenes, configuración de tienda, usuarios y reportes, temas, promociones nativas, gaps sueltos, lo que está detrás de aprobación manual, scripts y el deadline de NubeSDK |
| [`references/operaciones-peligrosas.md`](references/operaciones-peligrosas.md) | Vas a **escribir**: catálogo por nivel de riesgo (rojo / naranja / amarillo) con qué destruye cada operación, por qué se dispara sin querer y su antídoto; efecto de desinstalar la app; protecciones que sí existen |
| [`references/ejecucion.md`](references/ejecucion.md) | Estás en el **Paso 2**: elegir entre MCP oficial, script `tn-api.py` o admin web; conectar el MCP; credenciales y variables de entorno; contrato completo del script con recetas; paginación y rate limit en la práctica; tabla de errores accionables; cómo trabajar sin acceso a API |

El script vive en `scripts/tn-api.py` **relativo a esta skill** (no al proyecto del usuario): Python 3, solo biblioteca estándar, sin dependencias.

## Reglas duras

1. **Nunca prometer sin pasar por el triage.** Cajón primero (✅ / ⚠️ / 🖐️ / ❌), después la explicación. Vale igual para una respuesta de consultoría que para un plan de implementación.
2. **Nunca escribir sin dry-run + backup + confirmación explícita.** Los tres, en ese orden, cada vez. "Es un solo campo" no es una excepción.
3. **Nunca imprimir ni commitear tokens, `store_id` reales, nombres de clientes ni URLs de tiendas.** Este repo es público. El script enmascara el token; el descuido está del lado humano.
4. **Usar `2025-03`.** `v1` solo para diagnosticar una integración vieja que ya existe, nunca como default.
5. **Verificar `features` de la tienda antes de tocar stock, inventario o fulfillment.** Sin ese `GET /store`, la escritura correcta es indistinguible de la que rompe el reparto de inventario.
6. **No inventar endpoints.** Si una ruta no está en `references/api-map.md` ni en la doc oficial, **no existe** — no la deduzcas por analogía con Shopify. Ante un comportamiento que la doc no define, decilo como incierto y proponé la verificación en una tienda demo; no lo afirmes.
