# Diseño: `nube-skills-admin` — experto en el backoffice de Tienda Nube

**Fecha:** 2026-08-18 · **Estado:** aprobado

## Contexto y objetivo

El plugin `nube-skills` (v1.0.0) cubre el **storefront**: temas sectionable, secciones desde Figma, traducciones y QA visual. Falta el otro lado del negocio: el **backoffice** — productos, órdenes, clientes, cupones, envíos, metafields.

Innovate Group necesita una pieza que sirva por igual para tres usos (el usuario los ponderó iguales):
1. **Operar** tiendas de clientes (cargas y actualizaciones masivas, correcciones).
2. **Responder** qué se puede y qué no antes de prometerle algo a un cliente.
3. **Construir** apps e integraciones contra la API sin adivinar.

Acceso a las tiendas: mixto — a veces hay una app propia instalada (token disponible), a veces solo acceso al admin web. Escala: 1-5 tiendas activas en simultáneo.

## Hallazgo que define la arquitectura

**Ya existe un MCP oficial de administración de Tiendanube**: `https://admin-mcp.tiendanube.com/mcp` (Brasil: `admin-mcp.nuvemshop.com.br`), 28 herramientas, OAuth con Dynamic Client Registration, una conexión por tienda.

- **Cubre:** productos (CRUD, bulk stock/precio ≤50, visibilidad, bulk delete ≤20), categorías, cupones, promociones nativas, lectura de órdenes y clientes, métodos de pago y envío.
- **No cubre:** fulfillment y tracking, metafields, custom fields, locations/multi-inventario, draft orders, webhooks, scripts, páginas y blog, email templates, price tables B2B, abandoned checkouts, transacciones, y **toda escritura sobre pedidos**.

Conclusión: no se construye un MCP propio. El valor diferencial es **criterio** (qué se puede, qué no, qué es peligroso) más **alcance** en lo que el MCP oficial no toca.

## Decisiones aprobadas

- **Forma:** una skill, `nube-skills-admin`, dentro del repo público `nube-skills` (no un agente, no un MCP propio).
- **Ejecución híbrida:** MCP oficial donde ya resuelve bien; scripts propios para el resto.
- **Escritura:** masiva permitida, siempre con dry-run + backup + confirmación explícita. `DELETE` fuera salvo pedido expreso.
- **Degradación con gracia:** sin token ni MCP, la skill sigue siendo experta y guía por el admin web.
- **Versión de API:** `2025-03` (la doc oficial declara que `v1` no recibe features nuevas).

## Arquitectura de la skill

### Paso 0 — Contexto y capacidades reales
Identificar tienda y vía de acceso (MCP conectado / token propio / solo admin web), y correr `GET /store` para leer `plan_name` y `features`. Cambia el comportamiento correcto: con `inventory-levels` el stock va por `inventory_levels` y no por `variant.stock`; en plan Next el rate limit es ×10 y la Labels API está disponible; una tienda impaga devuelve `402` en toda la API.

### Paso 1 — Triage de factibilidad (el corazón)
Clasificar todo pedido antes de tocar nada:

| Cajón | Significa | Ejemplos |
|---|---|---|
| ✅ Por API | Se hace y se automatiza | Productos, categorías, cupones, clientes, metafields, páginas |
| ⚠️ Con aprobación de TN | Se puede, pidiendo permiso primero | Shipping carriers, payment providers, business rules, Labels API (plan Next), scripts `onload` |
| 🖐️ Solo admin web | Existe en el panel, no en la API | Config de tienda, impuestos, zonas de envío, usuarios y permisos, reportes, reembolsos, editar una orden |
| ❌ No se puede | Ni API ni panel | Import CSV masivo por API, facturas (no hay Invoice API), descancelar una orden |

### Paso 2 — Ejecución con protocolo de escritura segura
Lectura libre. Escritura en cinco tiempos: **dry-run** → **diff registro por registro** → **backup de valores actuales a archivo** (única forma de revertir: la API no tiene deshacer) → **confirmación explícita** → **ejecución** con control de rate limit y reporte de aplicados/fallidos.

### Guardarraíles duros (aplicados automáticamente)
- `PATCH` en vez de `PUT` para variantes: el `PUT` de colección **reemplaza todo** y matchea por combinación de `values`, no por `id` — renombrar un talle borra la variante con su stock y sus metafields.
- Nunca mandar `categories: []` en un `PUT /products/{id}`: deja el producto sin categoría (omitir el campo ≠ mandarlo vacío).
- `POST /orders/{id}/cancel` siempre con `restock` y `email` explícitos: es irreversible y ambos defaults son "hacer algo".
- `DELETE` fuera del alcance salvo pedido expreso.

## Estructura

```
skills/nube-skills-admin/
├── SKILL.md                        # flujo, triage, protocolo, guardarraíles
├── references/
│   ├── api-map.md                  # recursos, operaciones, límites, scopes, versionado
│   ├── no-se-puede.md              # mapa de gaps de la plataforma (consultoría)
│   ├── operaciones-peligrosas.md   # trampas destructivas y antídotos
│   └── ejecucion.md                # MCP oficial vs scripts, auth, rate limit, paginación, errores
└── scripts/
    └── tn-api.py                   # cliente con rate limit, paginación correcta y dry-run
```

## Datos técnicos que la implementación debe respetar

Verificados contra la doc oficial (`tiendanube.github.io/api-documentation`) y contra los proyectos propios de la agencia:

- **Auth:** OAuth solo `authorization_code`; el `code` expira en 5 min; **los access tokens no expiran**. Header `User-Agent` **obligatorio** (sin él → `400`). Cambiar scopes obliga a reinstalar en cada tienda.
- **Rate limit:** leaky bucket, 40 de burst, drena a **2 req/s** por par (tienda, app); ×10 en planes Next/Evolution. Headers `x-rate-limit-*`. Al exceder, las requests **se pierden, no se encolan**.
- **Paginación:** `per_page` máx 200, default 30. TN **clampea `per_page`** silenciosamente y devuelve **404 al pedir una página más allá de la última** (no un array vacío). Patrón probado en los proyectos de la agencia: `per_page=100` cortando por página corta.
- **Tope duro:** `GET /orders` corta en 10.000 items por query — particionar con `created_at_min/max`.
- **Caps:** 100.000 productos/tienda · 1000 categorías · 1000 variantes/producto · 250 imágenes/producto · 50 variantes en `PATCH /products/stock-price` · 30 ids en `?ids=`.
- **Errores:** `402` = tienda impaga (API suspendida) · `403` = feature no habilitada para el plan · `409` = conflicto · `415` = falta `Content-Type`.
- **Scripts:** se crean en el Partner Portal, **no por API**; `POST /scripts` solo asocia scripts no auto-instalables.
- **i18n:** `name`, `description`, `handle` y `seo_*` son objetos por idioma; un string plano se aplica a todos.
- **Webhooks:** HMAC en el header `x-linkedstore-hmac-sha256`; sin garantía de orden y con duplicados posibles → el handler debe ser idempotente.

## Fuera de alcance (YAGNI)

- MCP propio (el oficial ya cubre el núcleo del catálogo).
- Comando slash: la skill se dispara sola al hablar del backoffice.
- Gestión de credenciales multi-tienda: con 1-5 tiendas activas, el flujo existente alcanza.
