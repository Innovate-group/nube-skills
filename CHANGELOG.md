# Changelog

## 1.5.0 — 2026-09-30

- **El handoff de Ipanema pasa a vivir en el plugin.** [`docs/handoff/`](docs/handoff/README.md) junta lo aprendido en María Cher (con sus tiendas de Chile y Uruguay), Garçon García y VZ. El `HANDOFF-IPANEMA.md` que se venía copiando a mano entre proyectos quedó congelado el 2026-09-03, y lo aprendido después vivía repartido en el `CLAUDE.md` de cada proyecto. Ahora son 16 capítulos por tema (arranque, skills, sync y reglas, diseño y ui-kit, CLI, schema, Twig, plataforma, producto y carrito, CSS, JS, plantillas, límites y Admin API, patrones, verificación, multi-país) más plantillas del `CLAUDE.md` del proyecto, del `ui-kit.md` y de una skill de ui-kit por proyecto. Lectura obligatoria: `README` + `01`–`03`.
- **`/nube-skills:kickoff` copia el handoff al proyecto** (`.docs/handoff/`, desde `${CLAUDE_PLUGIN_ROOT}`) y arma `.claude/CLAUDE.md` desde la plantilla. La copia es una foto del día del kickoff: no se edita ni se refresca, y los proyectos que ya arrancaron no la reciben.
- **El kickoff se alinea con la práctica:** pide la fuente de diseño (Figma, prototipo HTML o ninguna), quién pushea, si se forkea, locales, tiendas hermanas y dominio; usa `tiendanube` y nunca `nuvemshop` (manda `region=br`); crea el `.gitignore` antes de bajar nada; corre `theme list` primero y `theme pull -y`, y verifica que el pull bajó completo; el fork lo corre el dev (ya no figura "Próximamente"); registra líneas de base (schemas, faltantes de i18n, archivos en el servidor); hace dos commits (tema base y documentación), y el agente ya no levanta `theme watch`. El `CLAUDE.md` deja de ir en la raíz.
- `validate.py` chequea que los links del handoff apunten a archivos que existen y que toda ruta `${CLAUDE_PLUGIN_ROOT}/…` de un comando exista en el repo.
- Las skills y el hook no cambian: sus problemas conocidos quedan documentados en `docs/handoff/02-skills.md`, cada uno con cómo esquivarlo.

## 1.4.0 — 2026-08-24

- **El sync gate deja de ser una instrucción y pasa a ser un hook.** La v1.3.0 documentaba el gate en las skills, y eso no alcanzó: una skill se carga solo cuando el modelo la considera relevante, y sus reglas se pueden saltear — con el resultado de JSONs editados antes del pull y settings del comerciante pisadas. Ahora `hooks/hooks.json` + `hooks/sync-gate.py` lo aplican en **toda** escritura, sin depender de qué skills haya en contexto.
- Qué hace el hook: **`deny`** en `Write`/`Edit`/`NotebookEdit` sobre `templates/**` y `config/settings_data.json`, y en `Bash` con `theme push`, cuando no hay un `theme pull` registrado en los últimos 15 minutos — el mensaje de bloqueo le dicta a la IA los 4 pasos del gate; **`ask`** en `theme publish` (reemplaza la instalación productiva entera); y registra el pull después de cada `theme pull` exitoso.
- El registro del pull vive en un marcador por tema (`~/.cache/nube-skills/`, fuera del repo del cliente) y **no** en el mtime de `manifest.json`: push y watch también tocan ese archivo, así que su fecha no prueba que hubo un pull. `sync-check.py <tema> --stamp` registra un pull hecho a mano en otra terminal.
- Diseñado para no molestar donde no corresponde: **inerte** fuera de un tema de Tienda Nube (exige `.nuvem` o un `manifest.json` que parsee y tenga campos del CLI, así un manifest de PWA o de extensión no dispara nada), **fail-open** ante cualquier error interno, solo bloquea la capa compartida con el comerciante (nunca `sections/`, `blocks/`, `snippets/`, `static/`), ~35 ms por invocación y sin red.
- Escapes en manos del dev, no del modelo: `NUBE_SKIP_SYNC_GATE=1` desactiva el gate y `NUBE_SYNC_MAX_AGE_MIN` cambia la ventana.
- `validate.py` ahora valida `hooks/hooks.json` (estructura y que los scripts que invoca existan): un hook mal configurado no falla ruidosamente, simplemente no corre, y ese es el modo de falla más caro.
- Requiere actualizar el plugin y **reiniciar la sesión** (o `/reload-plugins`); verificalo con `/hooks`. La instalación vía `npx skills add` copia skills, no hooks.

## 1.3.0 — 2026-08-21

- **Sync gate: nadie escribe un archivo del tema sin sincronizar antes.** El comerciante edita `templates/**` y `config/settings_data.json` desde el editor de la tienda mientras el equipo trabaja, y `theme push` **sincroniza eliminaciones**: escribir con una copia local vieja no solo pisa sus valores, borra de la tienda las secciones que él agregó — sin confirmación y sin deshacer. `nube-skills-themes` gana el **Paso 0.5** con el gate (commit/stash → `git pull --ff-only` → `tiendanube theme pull` → leer el diff), la tabla de propiedad compartida de cada archivo y la **regla dura #8**.
- Nueva referencia [`sync-and-conflicts.md`](skills/nube-skills-themes/references/sync-and-conflicts.md): cómo leer el diff que trae un pull, cómo reconciliar un conflicto (el valor del comerciante gana por default; los conflictos de JSON template no se resuelven a ojo), el **gate extra antes de `theme publish`** (publicar un borrador reemplaza la productiva entera, incluido lo que el comerciante configuró desde que se clonó) y los casos borde: sin git, con `theme watch` corriendo, sin fork, dos instalaciones, FTP legado.
- Nuevo script `sync-check.py` (Python 3, stdlib): verifica lo determinista del gate — instalación del Fork workflow, antigüedad del último `theme pull`, estado de git (sin commitear / commits pendientes del remoto), `theme watch` activo, `forked`, y en qué capa cae cada archivo a tocar. Exit 0/1/2, `--json` para usarlo desde un hook.
- El gate queda enganchado en las skills que escriben: `nube-skills-section` (prerrequisito y re-pull antes de tocar el JSON template), `nube-skills-qa` (antes de la primera corrección: el QA se hace contra el remoto, no contra tu copia), `nube-skills-i18n` (`theme pull` sobrescribe los locales). `/nube-skills:kickoff` deja la regla escrita en el `CLAUDE.md` del proyecto, para que la respete cualquier IA y cualquier dev.
- `nube-skills-admin`: el mismo criterio del lado de la API — el diff y el backup se calculan contra un `GET` tomado en el momento, no contra una lectura vieja. El comerciante también edita desde el panel.

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
