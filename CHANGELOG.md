# Changelog

## 1.2.0 — 2026-08-19

- `/nube-skills:kickoff` ya no pide los bocetos de las páginas: esos se pasan **sección a sección** durante el desarrollo. Ahora pide lo único que sí se necesita desde el arranque, **los nodos del ui-kit** — que no es un boceto sino un conjunto de nodos (colores, tipografías, botones, formularios, cards, iconografía, espaciados/grid).
- El `CLAUDE.md` del proyecto pasa a tener dos tablas: `## UI-kit` (los nodos del sistema visual, con `pendiente` para los que falten) y `## Bocetos por sección` (arranca vacía y se llena a medida que se construye).
- `nube-skills-section` lee la tabla de UI-kit y carga **solo los nodos que la sección necesita**, en vez de todo el ui-kit cada vez; al terminar, anota el boceto usado en la tabla de bocetos.
- `nube-skills-qa` toma su referencia de esa misma tabla en lugar de pedirla siempre.

## 1.1.0 — 2026-08-19

- Nueva skill `nube-skills-admin`: experto en el backoffice y la Admin API (`2025-03`). Aporta lo que ninguna fuente tiene junto — el mapa de **qué no se puede** (pedidos casi inmutables, sin API de reembolsos ni de configuración de tienda, sin usuarios ni reportes), los **guardarraíles** de las operaciones destructivas (el `PUT` de variantes que borra las ausentes, `categories: []`, `cancel` con restock y mail por default) y un **protocolo de escritura** en cinco tiempos: dry-run, diff, backup, confirmación y ejecución con control de rate limit.
- Ejecución híbrida: usa el **MCP oficial** de Tienda Nube donde ya resuelve, y `scripts/tn-api.py` (stdlib, con rate limit de 2 req/s y paginación que tolera el 404 de fin de colección) para todo lo que el MCP no expone.
- El catálogo pasa a cubrir los dos lados del negocio: storefront (temas) y backoffice.

## 1.0.0 — 2026-08-18

- Nueva skill `nube-skills-qa`: QA visual contra el diseño en desktop y mobile. Maneja la preview del tema con el MCP de Chrome DevTools (`emulate` para que DPR y touch evalúen bien las media queries), hace **QA numérico** leyendo estilos computados en vez de estimar píxeles, verifica estados interactivos con hover real y el toggle de visibilidad interna con contextos aislados, y reporta hallazgos priorizados distinguiendo bugs de código, settings mal configurados y contenido real de la tienda. No duplica performance (`theme performance` ya corre Lighthouse).
- **Catálogo completo**: las 5 piezas del diseño original están publicadas.

## 0.7.0 — 2026-08-18

- Nueva skill `nube-skills-i18n`: audita y completa traducciones. Distingue los dos sistemas independientes (claves `t:` del editor en `<locale>.schema.json` vs strings del comprador con `| t` en `<locale>.json`), detecta claves usadas en el código que faltan en algún locale, reporta huérfanas y pares de locale incompletos, y avisa cuando el proyecto no tiene fork (las traducciones no se pushean). Incluye `scripts/audit-i18n.py`, determinista y sin dependencias.

## 0.6.0 — 2026-08-18

- Renombrada `nube-skills-figma-section` → **`nube-skills-section`**: la skill construye sections con o sin boceto de Figma, así que el nombre ya no la ata a Figma. Mismo contenido; referencias actualizadas en el comando `kickoff` y en el README.

## 0.5.0 — 2026-08-18

- `nube-skills-figma-section`: nueva **Vía B** para cuando el dev no tiene boceto — en vez de codear a ojo, invoca la skill `design` para dibujar los artboards desktop y mobile con el ui-kit y los tokens reales del proyecto, los valida con el dev y recién entonces sigue el flujo normal (triage → código). La skill ahora también dispara ante pedidos sin diseño ("necesito una sección de X").

## 0.4.1 — 2026-08-18

- `/nube-skills:kickoff` lleva `disable-model-invocation: true`: al estar unificados comandos y skills, sin esto el modelo podría auto-invocarlo. El kickoff crea instalaciones en la tienda y repos, así que corre solo por pedido explícito del dev.

## 0.4.0 — 2026-08-18

- Nuevo comando `/nube-skills:kickoff`: arranque de un proyecto de cliente — instalación Ipanema con el CLI (create/list + pull), git con `.nuvem` protegido, `CLAUDE.md` del proyecto con los links de Figma y el ui-kit (que las demás skills leen), y repo privado opcional en GitHub. No hace fork: eso lo decide el triage de `nube-skills-figma-section`.
- README: instrucciones de actualización del plugin.

## 0.3.0 — 2026-08-18

- Nueva skill `nube-skills-figma-section`: convierte nodos de Figma (desktop + mobile) en código del tema con triage de intervención mínima (configurar / re-estilizar / extender / custom), filosofía settings-first, traducciones en todos los locales y registro en el JSON template. Requiere el MCP oficial de Figma.
- Convenciones incluidas en la skill: chequeo obligatorio del ui-kit del proyecto (se pregunta y persiste su ubicación), settings de padding top/bottom para desktop y mobile en toda section generada, pregunta por estados interactivos (hover, etc.) y toggle opcional de visibilidad interna para usuarios `@innovategroup`.

## 0.2.0 — 2026-08-18

- Convención de nombres del catálogo: toda skill pasa a llamarse `nube-skills-<qué-hace>`.
- Renombrada `tiendanube-sectionable-themes` → `nube-skills-themes` (mismo contenido).

## 0.1.0 — 2026-08-18

- Scaffold del monorepo dual-canal (plugin de Claude Code + compatible con `npx skills add`).
- Primera skill del catálogo: `tiendanube-sectionable-themes` (modelo sectionable, Fork Workflow, detección de generación de tema).
- Validador de estructura (`scripts/validate.py`) y CI en GitHub Actions.
