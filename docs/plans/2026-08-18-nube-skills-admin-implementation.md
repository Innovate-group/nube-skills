# `nube-skills-admin` — Plan de implementación

> **For agentic workers:** ejecutar tarea por tarea (subagente por tarea, o inline con checkpoints). Los pasos usan checkboxes (`- [ ]`).

**Goal:** Publicar en el plugin `nube-skills` una skill experta en el backoffice de Tienda Nube que sepa qué se puede y qué no, y que ejecute CRUD por API con dry-run, backup y confirmación explícita.

**Architecture:** Una skill con progressive disclosure: `SKILL.md` lleva el flujo (capacidades → triage → escritura segura), cuatro `references/` llevan el conocimiento denso, y un `scripts/tn-api.py` (stdlib only) ejecuta contra la API con rate limit, paginación correcta, dry-run y backup. Ejecución híbrida: MCP oficial donde alcanza, script para el resto.

**Tech Stack:** Markdown; Python 3 stdlib (`urllib`, `json`, `argparse`, `http.server` para los tests).

## Global Constraints

- Contenido en **español**; frontmatter solo `name` + `description`, entre **comillas dobles**, ≤1024 caracteres.
- Versión de API por defecto: **`2025-03`** (nunca `v1` como default).
- Repo **público**: jamás commitear tokens, `store_id` reales, nombres de clientes ni URLs de tiendas.
- El script es **stdlib only** (sin `requests` ni dependencias).
- Directorio de trabajo: `/Users/tonchi/Desktop/Innovate/nube-skills`.
- Fuente documental ya descargada: `/private/tmp/claude-501/-Users-tonchi--claude/607adf32-d54a-4a60-bcdf-39742f7caae9/scratchpad/docs/` (58 `.txt` de `tiendanube.github.io/api-documentation`). Si el scratchpad no existe, re-descargar con `curl` desde `https://tiendanube.github.io/api-documentation/...` (ese host **no** tiene Cloudflare; `tiendanube.dev` sí y devuelve 403).
- Antes de cada commit: `python3 scripts/validate.py` debe pasar.
- Trailer en todos los commits: línea en blanco + `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.
- **Marcar la incertidumbre, no taparla.** Donde la doc oficial no define un comportamiento, el contenido debe decirlo explícitamente y proponer cómo verificarlo en una tienda demo, en vez de afirmar. Ver "Incógnitas conocidas" abajo.

## Incógnitas conocidas (documentarlas como tales)

Dos comportamientos de alto impacto que la doc oficial **no** define:

1. **¿`PUT /products/{id}` parcial preserva variantes e imágenes no enviadas?** La doc de verbos dice que `PUT` es reemplazo, pero un comentario de código en `longvie-management-app` afirma lo contrario por experiencia: *"El PUT de TN hace merge, así que mandar solo `{tags}` no toca otros campos"*. Lo que **sí** está confirmado es que `categories: []` borra las categorías. Documentar: la evidencia práctica apunta a merge, la doc no lo garantiza, y la verificación es un `PUT` de un solo campo sobre un producto de tienda demo comparando el `GET` previo y posterior.
2. **¿Hay endpoint REST público del motor nativo de promociones?** El MCP oficial expone `create_promotion`/`update_promotion`/`delete_promotion`, pero la REST pública solo documenta la Discounts API de callbacks. Documentar como brecha conocida: si hace falta CRUD de promociones nativas, la vía comprobada es el MCP oficial.

---

### Task 1: `scripts/tn-api.py` — cliente HTTP con rate limit, paginación y dry-run

**Files:**
- Create: `skills/nube-skills-admin/scripts/tn-api.py`
- Test (temporal, se borra al final): fixture en `/private/tmp/claude-501/-Users-tonchi--claude/607adf32-d54a-4a60-bcdf-39742f7caae9/scratchpad/tn-api-fixture/`

**Interfaces:**
- Produces: la CLI que documenta `references/ejecucion.md` (Task 5) y usa `SKILL.md` (Task 6). Contrato exacto:

```
python3 tn-api.py <METHOD> <PATH> [opciones]

  METHOD   GET | POST | PUT | PATCH | DELETE
  PATH     ruta relativa al store, sin barra inicial: "products", "products/123/variants"

Opciones:
  --store-id ID        (o env TN_STORE_ID)      requerido
  --token TOKEN        (o env TN_ACCESS_TOKEN)  requerido
  --user-agent UA      (o env TN_USER_AGENT)    requerido — la API devuelve 400 sin él
  --base-url URL       default https://api.tiendanube.com
  --api-version V      default 2025-03
  --param K=V          repetible; querystring
  --data JSON          body inline
  --data-file PATH     body desde archivo (excluyente con --data)
  --paginate           recorre todas las páginas y devuelve un array único
  --per-page N         default 100 (máx 200)
  --dry-run            no ejecuta escrituras: imprime el request que haría
  --backup PATH        antes de escribir, GET del recurso y guarda el estado actual
  --json               salida JSON pura (sin encabezados legibles)
  --max-retries N      default 3 (429 y 5xx)
```

Exit codes: `0` OK · `1` error de la API (4xx/5xx tras reintentos) · `2` error de uso (falta credencial, argumentos inválidos).

- [x] **Step 1: Escribir el script**

Requisitos de comportamiento que el código debe cumplir:

1. **Headers en toda request:** `Authentication: bearer <token>`, `User-Agent: <ua>`, `Content-Type: application/json; charset=utf-8` (en POST/PUT/PATCH), `Accept: application/json`.
   *(La doc oficial muestra `Authorization: Bearer` en páginas nuevas y `Authentication: bearer` en las viejas; los proyectos de la agencia usan `Authentication: bearer` y funcionan. Mandar ese, y ante un 401 reintentar una vez con `Authorization: Bearer` informando el cambio por stderr.)*
2. **URL:** `{base_url}/{api_version}/{store_id}/{path}`.
3. **Rate limit:** leaky bucket de 2 req/s — antes de cada request, dormir lo necesario para que no haya más de 2 requests por segundo (guardar timestamps). Tras cada respuesta, leer `x-rate-limit-remaining`; si es `< 5`, dormir lo que indique `x-rate-limit-reset` (viene en **milisegundos**).
4. **429:** dormir `x-rate-limit-reset` ms (o 1s si falta el header) y reintentar hasta `--max-retries`.
5. **5xx:** backoff exponencial (1s, 2s, 4s) hasta `--max-retries`.
6. **Paginación (`--paginate`):** `page=1..N` con `per_page` (default 100). Cortar cuando: la respuesta trae **menos ítems que los realmente devueltos en la primera página** (TN **clampea `per_page`** sin avisar, así que el corte se compara contra el tamaño de la página 1, no contra el `per_page` pedido), **o** la API devuelve **404** (TN devuelve 404 al pedir una página más allá de la última, no un array vacío) — ese 404 **no es error**, es fin de la colección.
7. **Envelopes:** si el JSON es un objeto con `results` (`{"pages": {"results": [...]}}` o `{"results": [...]}`), extraer el array al paginar. Si es un array, usarlo tal cual.
8. **`--dry-run`:** solo aplica a métodos de escritura (POST/PUT/PATCH/DELETE). Imprime método, URL completa, headers (con el token **enmascarado**) y body, y sale con 0 **sin ejecutar**. En GET, `--dry-run` se ignora con un aviso.
9. **`--backup PATH`:** antes de una escritura, hace `GET` del mismo path (sin el sufijo de acción) y guarda la respuesta en `PATH` como JSON con `{"fetched_at": <iso>, "method": <m>, "url": <u>, "body": <estado actual>}`. Si el GET falla, **abortar la escritura** con exit 1 (no se escribe sin red de seguridad). Si el path no es "GET-eable" (termina en `/cancel`, `/close`, `/open`, `/confirm`), backupear el recurso padre.
10. **Errores con mensaje accionable** — mapear y explicar: `400` (falta `User-Agent` o JSON inválido), `401` (token inválido), `402` (**tienda o app impaga: la API está suspendida**), `403` (feature no habilitada para el plan de la tienda), `404`, `409` (conflicto), `415` (falta `Content-Type`), `422` (validación; imprimir `description` y los errores por campo del formato legacy `{"campo": ["mensaje"]}`), `429`, `5xx`.
11. Nunca imprimir el token completo (enmascarar dejando los últimos 4 caracteres).

- [x] **Step 2: Escribir el fixture de prueba**

Un `fixture_server.py` con `http.server` en el scratchpad que simule los comportamientos reales de la API:
- `GET /2025-03/1/products?page=1&per_page=100` → 100 items; `page=2` → 40 items; `page=3` → **404** (fin de colección).
- Un endpoint que **clampea**: pedir `per_page=200` devuelve 100 items.
- `GET /2025-03/1/ratelimited` → primera llamada `429` con `x-rate-limit-reset: 300`, segunda `200`.
- `GET /2025-03/1/flaky` → dos `500` seguidos y después `200`.
- `GET /2025-03/1/suspended` → `402`.
- `GET /2025-03/1/noagent` → `400` si falta el header `User-Agent`.
- `GET /2025-03/1/pages` → `{"pages": {"results": [...]}}` (envelope v2).
- `PUT /2025-03/1/products/5` → eco del body recibido; `GET /2025-03/1/products/5` → estado actual (para probar `--backup`).

- [x] **Step 3: Correr los casos y verificar**

Levantar el fixture y correr, verificando cada resultado:

| Caso | Comando | Esperado |
|---|---|---|
| Paginación completa | `GET products --paginate` | 140 items, sin error por el 404 de la página 3 |
| Clamp de `per_page` | `GET products --paginate --per-page 200` | no corta en la página 1; llega a 140 |
| 429 con reintento | `GET ratelimited` | 200 tras dormir ~300ms, exit 0 |
| 5xx con backoff | `GET flaky` | 200 al tercer intento, exit 0 |
| Tienda impaga | `GET suspended` | mensaje explícito de tienda/app impaga, exit 1 |
| Falta User-Agent | `GET noagent` sin `--user-agent` | error de uso, exit 2 (el script exige UA antes de salir a la red) |
| Envelope v2 | `GET pages --paginate` | extrae `pages.results` |
| Dry-run | `PUT products/5 --data '{"name":"X"}' --dry-run` | imprime el request con token enmascarado, **no** ejecuta, exit 0 |
| Backup | `PUT products/5 --data '{"name":"X"}' --backup /tmp/bk.json` | `/tmp/bk.json` tiene el estado previo y la escritura se ejecuta |
| Backup imposible | `PUT products/999 --data '{}' --backup /tmp/bk2.json` (404 en el GET) | **aborta sin escribir**, exit 1 |
| Rate limit | 6 GETs seguidos | tardan ≥2.5s en total (2 req/s) |
| Token enmascarado | cualquier salida | el token completo no aparece nunca |

Ajustar el script hasta que los 12 casos pasen. Al terminar, **borrar el fixture**.

- [x] **Step 4: Commit**

```bash
git add skills/nube-skills-admin/scripts/tn-api.py
git commit -m "feat(admin): cliente tn-api.py con rate limit, paginación y dry-run"
```

---

### Task 2: `references/api-map.md`

**Files:**
- Create: `skills/nube-skills-admin/references/api-map.md` (~350-420 líneas)

**Interfaces:**
- Consumes: nada.
- Produces: la referencia que `SKILL.md` (Task 6) enlaza para "necesito saber qué endpoints existen y con qué límites".

- [x] **Step 1: Escribir el archivo**

Fuentes (en el scratchpad de docs): `resources.txt`, `resources__product.txt`, `resources__product_variant.txt`, `resources__category.txt`, `resources__order.txt`, `resources__customer.txt`, `resources__coupon.txt`, `resources__store.txt`, `resources__webhook.txt`, `authentication.txt`, `versioning.txt`, `CHANGELOG.txt`, más los de fulfillment/locations/metafields/custom-fields/pages/blog/email-templates.

Contenido, con tabla de contenidos al inicio:
1. **Base y versionado** — `{base_url}/{version}/{store_id}/...`; versiones válidas `v1`, `2025-03`, `unstable`; usar `2025-03` (v1 no recibe features nuevas); dominios LATAM vs BR.
2. **Autenticación** — OAuth solo `authorization_code`, code expira en 5 min, tokens **no expiran**, `user_id` = `store_id`; header `User-Agent` obligatorio; app "Para Tus Clientes" = app privada sin homologación; cambiar scopes obliga a reinstalar.
3. **Tabla de recursos** — por recurso: operaciones soportadas y particularidades (catálogo, ventas, logística, plataforma/contenido), tal como quedó relevado.
4. **Límites duros** — rate limit (40 burst / 2 req/s por par tienda-app, ×10 en Next/Evolution, headers `x-rate-limit-*`, las requests excedidas **se pierden**), paginación (`per_page` máx 200, default 30, clamp silencioso, 404 al exceder la última página), tope de 10.000 items en `GET /orders`, y los caps de cantidad (100.000 productos, 1000 categorías, 1000 variantes, 250 imágenes, 50 variantes en `PATCH stock-price`, 30 ids en `?ids=`).
5. **Scopes** — tabla completa con la regla de que write implica read y las herencias (`read_locations` requiere shipping o products; `*_fulfillment_orders` requiere `*_orders`).
6. **Errores** — formatos (moderno `{code,message,description}` y legacy por campo) y tabla de códigos con su causa real.
7. **Feature detection** — `GET /store` → `plan_name` y `features` (`inventory-levels`, `fulfillment-orders`, `fulfillment_order_label_api`) y qué cambia cada uno.

- [x] **Step 2: Validar y commitear**

```bash
python3 scripts/validate.py
git add skills/nube-skills-admin/references/api-map.md
git commit -m "docs(admin): referencia del mapa de la API"
```

---

### Task 3: `references/no-se-puede.md`

**Files:**
- Create: `skills/nube-skills-admin/references/no-se-puede.md` (~200-260 líneas)

**Interfaces:**
- Produces: la referencia que sostiene el **triage de factibilidad** del Paso 1 de `SKILL.md`. Es el archivo de mayor valor para consultoría.

- [x] **Step 1: Escribir el archivo**

Fuentes: `resources__order.txt`, `resources__store.txt`, `resources__script.txt`, `resources__kit.txt`, `resources__cart.txt`, `resources__customer.txt`, `guides__*.txt`, más el barrido de namespaces inexistentes.

Estructura: una sección por área, cada limitación con **qué se pide**, **por qué no se puede** (cita o referencia a la doc) y **la alternativa real** (admin web, otro endpoint, o nada).

1. **Órdenes** — `PUT /orders/{id}` solo acepta `owner_note` y `status`; no se editan ítems, cantidades, precios, totales, descuentos, direcciones, cliente ni `gateway` (read-only); **no hay API de reembolsos** (solo apps de pago vía `refund_url`); no hay API de edición (solo lectura del changelog en `/history/editions`); `cancel` es terminal y `/open` solo revierte un `close`; no hay endpoint "pagar orden".
2. **Configuración de tienda** — `GET /store` es el único endpoint: cero escritura (nombre, idiomas, monedas, dominios, tema, datos fiscales). Sin namespace para impuestos, zonas de envío nativas ni métodos de pago nativos.
3. **Usuarios, permisos, reportes** — no existe API de staff/roles/permisos ni de analytics; las métricas se reconstruyen paginando `/orders` (con el tope de 10.000).
4. **Temas** — no hay Admin API de temas; es un sistema aparte (ver la skill `nube-skills-themes`).
5. **Promociones nativas** — la REST pública solo ofrece la Discounts API de **callbacks** (partner, respuesta en <800 ms, whitelist de IPs); no es un CRUD. *(El MCP oficial sí expone create/update/delete de promociones.)*
6. **Otros gaps** — sin Invoice API (workaround: metafields con namespace `nfe`); sin import/export CSV; carritos no se crean ni se les agregan ítems; draft orders no tienen PUT; clientes con pedidos no se borran; kits read-only; sales channels solo lectura.
7. **Detrás de aprobación manual** (no es "no se puede", es "pedí permiso") — tabla: Shipping API (formulario), Payments API (mail a partners), Business Rules (soporte), App Proxy (soporte), scripts `onload` (mail a api@), Labels API (plan Next), nueva Product API multi-inventario (contactar).
8. **Scripts** — se crean en el Partner Portal, no por API; `POST/PUT/DELETE` solo asocian scripts no auto-instalables, y el evento `onload` requiere aprobación.
9. **Deadline NubeSDK** (afecta la planificación, no solo el "no se puede") — desde el **30/08/2026** las apps que inyectan scripts sin NubeSDK no reciben instalaciones nuevas, y desde el **30/10/2026** empieza la desinstalación progresiva. **Aplica también a apps privadas con `write_scripts`**, así que toca a las apps propias de la agencia.

- [x] **Step 2: Validar y commitear**

```bash
python3 scripts/validate.py
git add skills/nube-skills-admin/references/no-se-puede.md
git commit -m "docs(admin): mapa de lo que la API no permite"
```

---

### Task 4: `references/operaciones-peligrosas.md`

**Files:**
- Create: `skills/nube-skills-admin/references/operaciones-peligrosas.md` (~150-200 líneas)

**Interfaces:**
- Produces: los guardarraíles que `SKILL.md` aplica automáticamente.

- [x] **Step 1: Escribir el archivo**

Cada entrada con: **operación**, **qué destruye**, **por qué pasa** y **antídoto concreto**.

Nivel rojo:
1. `PUT /products/{id}/variants` (colección) — reemplaza todo y matchea por combinación de `values`, **no por `id`**: toda variante cuya combinación no venga en el body **se borra** (con su stock por location y sus metafields). Renombrar un talle = borrar y recrear. **Antídoto: usar siempre `PATCH`**, que actualiza por `id` y nunca crea ni borra.
2. `PUT /products/{id}` con `categories: []` — deja el producto sin categoría. **Antídoto: omitir el campo** (omitir ≠ mandar vacío).
3. `DELETE` de productos, categorías (cascada a subcategorías), metafields, custom fields, cupones, webhooks, locations — sin papelera. **Antídoto: fuera de alcance salvo pedido expreso, y backup previo obligatorio.**
4. `DELETE /plans/{id}` (billing) — borra suscripciones y cargos impagos.

Nivel naranja:
5. `POST /orders/{id}/cancel` — irreversible; `restock` y `email` son `true` por default. **Antídoto: mandarlos siempre explícitos y confirmarlos con el dev.**
6. `PATCH /products/stock-price` — 50 variantes por request, sin rollback. **Antídoto: dry-run + backup + lotes chicos.**
7. `PATCH` de fulfillment order a `DISPATCHED` con `notify_customer: true` — dispara mail al comprador.
8. Cambiar scopes de la app — invalida tokens y obliga a reinstalar en cada tienda.

Nivel amarillo (trampas silenciosas, no destructivas por sí solas):
9. **`stock: ""` (string vacío) = stock infinito.** Un bug de serialización que mande `""` en vez de `0` desactiva el control de stock del producto sin error visible. Ojo además con las **dos codificaciones** según endpoint (`""` en producto/variante, `null` en `POST /variants/stock` con `action: replace`); `stock_management` es read-only.
10. **Órdenes creadas por API no reservan stock** salvo que el inventory behavior sea `claim`.
11. **Webhooks sin garantía de orden y con entregas duplicadas** (timeout 3 s, hasta 16 reintentos en 48 h) → todo handler debe ser **idempotente**.
12. **Desinstalar una app promocional borra sus promociones permanentemente.**

Más: **efecto de desinstalar la app** (se borran shipping carriers, payment providers, webhooks y scripts creados por la app; el resto queda) y las **protecciones que sí existen** (`DELETE /customers/{id}` falla con 422 si el cliente tiene órdenes; la doc oficial recomienda **desactivar en vez de borrar** cupones con `valid=false` y promociones con `published=false`).

Cerrar con la sección **"Incógnitas"**: el comportamiento de `PUT /products/{id}` parcial (ver "Incógnitas conocidas" del encabezado de este plan) — la evidencia práctica del equipo dice merge, la doc dice reemplazo, `categories: []` sí borra. Redactarlo como incertidumbre con su método de verificación en tienda demo, nunca como afirmación.

- [x] **Step 2: Validar y commitear**

```bash
python3 scripts/validate.py
git add skills/nube-skills-admin/references/operaciones-peligrosas.md
git commit -m "docs(admin): operaciones destructivas y sus antídotos"
```

---

### Task 5: `references/ejecucion.md`

**Files:**
- Create: `skills/nube-skills-admin/references/ejecucion.md` (~220-280 líneas)

**Interfaces:**
- Consumes: el contrato exacto de `scripts/tn-api.py` (Task 1) — leer el `--help` del script y documentarlo sin inventar flags.

- [x] **Step 1: Escribir el archivo**

1. **Elegir el brazo ejecutor** — tabla de decisión: qué resuelve el **MCP oficial** (`https://admin-mcp.tiendanube.com/mcp`, Brasil `admin-mcp.nuvemshop.com.br`; 28 tools: productos incluido bulk stock/precio ≤50 y visibilidad ≤20, categorías, cupones, promociones, lectura de órdenes y clientes, métodos de pago y envío) y qué **solo** se puede con el script (fulfillment y tracking, metafields, custom fields, locations/multi-inventario, draft orders, webhooks, páginas, blog, email templates, price tables, abandoned checkouts, escritura sobre pedidos).
2. **Conectar el MCP oficial** — OAuth con Dynamic Client Registration; **una conexión = una tienda**; scopes que declara.
3. **Credenciales para el script** — de dónde sale el token (app propia tipo "Para Tus Clientes", tokens que no expiran); variables `TN_STORE_ID`, `TN_ACCESS_TOKEN`, `TN_USER_AGENT`; **nunca** commitear ni imprimir tokens.
4. **Uso del script** — el contrato completo (métodos, path sin barra inicial, todas las opciones, exit codes) y recetas: leer un recurso paginado, escritura con dry-run y backup, lote con rate limit.
5. **Paginación y rate limit en la práctica** — por qué el corte es por página corta comparada contra la página 1 (clamp) y por qué un 404 al paginar significa fin de colección; cuánto tarda realmente un recorrido de N productos a 2 req/s (y ×10 en Next/Evolution).
6. **Errores** — tabla de códigos con la acción recomendada para cada uno (en especial `402` tienda impaga y `403` feature no habilitada).
7. **Sin acceso a API** — cómo trabajar guiando por el admin web cuando no hay token ni MCP.

- [x] **Step 2: Verificar que el documento coincide con el script**

Run: `python3 skills/nube-skills-admin/scripts/tn-api.py --help`
Contrastar una por una las opciones documentadas contra la salida real. Corregir el documento (no el script) ante cualquier diferencia.

- [x] **Step 3: Validar y commitear**

```bash
python3 scripts/validate.py
git add skills/nube-skills-admin/references/ejecucion.md
git commit -m "docs(admin): guía de ejecución (MCP oficial vs script)"
```

---

### Task 6: `SKILL.md`

**Files:**
- Create: `skills/nube-skills-admin/SKILL.md` (~180-240 líneas)

**Interfaces:**
- Consumes: los 4 references (Tasks 2-5) y el contrato del script (Task 1).

- [x] **Step 1: Escribir el frontmatter**

```yaml
---
name: nube-skills-admin
description: "Expert on the TiendaNube/Nuvemshop admin backoffice and Admin API (2025-03). Use for anything about managing a store's data — products, variants, stock and prices, categories, orders, customers, coupons, promotions, metafields, custom fields, fulfillment and shipping, webhooks, pages — whether the question is 'can TiendaNube do X?', 'how do I bulk-update this?', or building an app against the API. Triages what is possible via API, what needs TiendaNube's manual approval, what is admin-panel-only, and what is impossible; executes reads freely and writes only with dry-run, backup and explicit confirmation. Triggers: backoffice, panel de tienda nube, API de tienda nube, actualizar productos masivo, stock, precios, pedidos, cupones, metafields, webhooks, se puede hacer X en tiendanube. NOT for theme/storefront work (use nube-skills-themes) and NOT for Shopify."
---
```

Contarla: debe ser ≤1024 caracteres. Si excede, recortar los ejemplos de triggers, nunca las exclusiones.

- [x] **Step 2: Escribir el cuerpo**

1. **Overview** (3 líneas) — qué cubre; que el storefront es territorio de `nube-skills-themes`.
2. **Paso 0 — Capacidades reales de ESTA tienda.** Identificar tienda y vía de acceso (MCP oficial conectado / token propio / solo admin web) y correr `GET /store` para leer `plan_name` y `features`. Qué cambia: `inventory-levels` (el stock va por `inventory_levels`, no por `variant.stock`), plan Next (rate limit ×10, Labels API), tienda impaga (`402` en toda la API). Sin acceso a API, la skill sigue siendo útil: guía por el admin web.
3. **Paso 1 — Triage de factibilidad**, con la tabla de 4 cajones (✅ por API · ⚠️ con aprobación de TN · 🖐️ solo admin web · ❌ no se puede) y 3-4 ejemplos por cajón. Regla: **comunicar el cajón antes de prometer o ejecutar nada**; detalle completo en `references/no-se-puede.md`.
4. **Paso 2 — Ejecutar.** Lectura libre. Escritura en cinco tiempos: dry-run → diff registro por registro → backup a archivo → confirmación explícita del dev → ejecución con rate limit y reporte de aplicados/fallidos. Elegir brazo (MCP oficial vs script) según `references/ejecucion.md`.
5. **Guardarraíles** (resumen accionable, detalle en `references/operaciones-peligrosas.md`): `PATCH` y no `PUT` para variantes; nunca `categories: []`; `cancel` con `restock` y `email` explícitos; `DELETE` fuera salvo pedido expreso; lotes chicos por el rate limit.
6. **Navegación de referencias** — tabla "leé X cuando Y" con los 4 archivos.
7. **Reglas duras** — (1) nunca prometer sin pasar por el triage; (2) nunca escribir sin dry-run + backup + confirmación; (3) nunca imprimir ni commitear tokens; (4) usar `2025-03`, no `v1`; (5) verificar `features` de la tienda antes de tocar stock; (6) no inventar endpoints — si no está en `api-map.md`, no existe.

- [x] **Step 3: Verificar enlaces y tamaño**

Run:
```bash
grep -o 'references/[a-z-]*\.md' skills/nube-skills-admin/SKILL.md | sort -u
wc -l skills/nube-skills-admin/SKILL.md
```
Expected: los 4 nombres exactos (`api-map.md`, `no-se-puede.md`, `operaciones-peligrosas.md`, `ejecucion.md`) y menos de 500 líneas.

- [x] **Step 4: Validar y commitear**

Run: `python3 scripts/validate.py`
Expected: `OK: 5 skill(s) válidas y manifiestos correctos`

```bash
git add skills/nube-skills-admin/SKILL.md
git commit -m "feat(admin): SKILL.md con triage de factibilidad y protocolo de escritura"
```

---

### Task 7: Release 1.1.0

**Files:**
- Modify: `README.md` (tabla del catálogo + sección "Cómo se encadenan")
- Modify: `CHANGELOG.md`
- Modify: `.claude-plugin/plugin.json` (`version` → `1.1.0`)

- [ ] **Step 1: README** — agregar la fila del catálogo:

```markdown
| `nube-skills-admin` | skill | ✅ disponible | Experto en el backoffice y la Admin API: triage de qué se puede por API, qué necesita aprobación de TiendaNube, qué es solo del panel y qué es imposible; ejecuta lecturas libres y escrituras con dry-run, backup y confirmación. |
```

Y sumar una línea al final de "Cómo se encadenan": que el backoffice es transversal — se usa en cualquier momento del proyecto, no en un paso fijo.

- [ ] **Step 2: CHANGELOG** — nueva entrada `## 1.1.0 — 2026-08-18` describiendo la skill, el triage de 4 cajones, el protocolo de escritura y el script.

- [ ] **Step 3: Bump de versión** en `.claude-plugin/plugin.json` a `1.1.0`.

- [ ] **Step 4: Validar, commitear y pushear**

```bash
python3 scripts/validate.py
git add -A
git commit -m "feat: nueva skill nube-skills-admin (v1.1.0)"
git push
```

- [ ] **Step 5: Verificar CI**

Run: `gh run list --repo Innovate-group/nube-skills --limit 1`
Expected: `Validate skills` en `completed success`.

- [ ] **Step 6: Actualizar el plugin instalado**

```bash
claude plugin marketplace update nube-skills
claude plugin update nube-skills@nube-skills
```
Expected: `updated from 1.0.0 to 1.1.0`.

---

## Verificación end-to-end

Con el plugin actualizado, en una sesión nueva:

1. **Consultoría (sin tocar nada):** preguntar *"¿se puede editar el precio de una línea de un pedido ya creado en TiendaNube?"* → debe disparar la skill y responder **🖐️ solo admin web / ❌ no por API** (`PUT /orders` solo acepta `owner_note` y `status`), sin inventar un endpoint.
2. **Triage con aprobación:** *"¿puedo generar etiquetas de envío por API?"* → **⚠️ requiere plan Next y la feature `fulfillment_order_label_api`**.
3. **Ejecución en seco:** con credenciales de una tienda demo, pedir una actualización masiva de precios → debe hacer dry-run, mostrar el diff y **frenar a esperar confirmación**, sin escribir.
4. **Guardarraíl:** pedir explícitamente actualizar variantes con `PUT` → debe corregir a `PATCH` y explicar por qué.
