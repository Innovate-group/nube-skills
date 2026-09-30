# Las skills del plugin, en la práctica

Qué trae el plugin **nube-skills**, cómo se instala, cómo se dispara cada pieza en la práctica
(no solo cómo dice su descripción) y qué falla hoy, con la forma de esquivarlo. Las cifras de uso
salen de los transcripts de 54 sesiones de María Cher y VZ, relevados el 2026-09-30.

## Lo esencial

- **Instalá el plugin, no las skills sueltas.** Trae las skills, el comando `/nube-skills:kickoff`
  y el hook `sync-gate`. Verificá con `/hooks`. No instales las skills en el repo del tema con
  `npx skills add`: salen duplicadas y el modelo termina usando la copia vieja.
- **Día 1: `/nube-skills:kickoff`.** Solo corre si lo invocás ([Arranque](01-arranque.md)).
- 🚫 **`nube-skills-themes` no se carga sola:** 0 veces en 54 sesiones. Invocala con
  `/nube-skills:nube-skills-themes` cuando la necesites; el `CLAUDE.md` del proyecto ya trae sus
  reglas principales.
- `nube-skills-section` se dispara sola cuando pasás el link del diseño. `nube-skills-qa` e
  `nube-skills-i18n` casi nunca: invocá la de QA y corré el script de i18n directo.
- **El hook bloquea** escribir `templates/**` o `config/settings_data.json`, y todo
  `theme push`, si no hay un pull registrado en los últimos 15 minutos. El pull a un temporal se
  registra a mano con `--stamp`. Tiene falsos positivos y no ve las escrituras por Bash.
- Los scripts se llaman **con una ruta sin versión**, que no se rompe en el próximo release.
- Al final: [los problemas conocidos del plugin](#problemas-conocidos-del-plugin-y-cómo-esquivarlos),
  cada uno con cómo seguir.

## Instalación y actualización

```
/plugin marketplace add Innovate-group/nube-skills
/plugin install nube-skills@nube-skills
```

Para actualizar, cuando se anuncie un release:

```bash
claude plugin marketplace update nube-skills
claude plugin update nube-skills@nube-skills
```

Después reiniciá la sesión (o `/reload-plugins`) y confirmá con `/hooks` que aparecen el
`PreToolUse` (`Write|Edit|MultiEdit|NotebookEdit|Bash`) y el `PostToolUse` (`Bash`) de
nube-skills. Si no aparecen: revisá que el plugin esté habilitado, que ningún `settings.json`
tenga `disableAllHooks: true` y que el `.zshrc` o `.bashrc` no imprima nada fuera de una shell
interactiva (esa salida se mezcla con el JSON del hook y lo invalida).

### No instales las skills en el repo del tema

`npx skills add` copia las skills al proyecto (`.agents/skills/`, con symlinks en
`.claude/skills/` y un `skills-lock.json`). En MC y VZ convivieron esas copias con las del plugin,
y salió mal [relevado 2026-09-30]:

- **Salen duplicadas en el listado de skills, y muchas veces sin descripción.** En 13 de 16
  sesiones de VZ las dos copias de `nube-skills-themes` aparecían solo con el nombre. Sin
  descripción, el modelo no puede reconocer cuándo usarlas.
- **Cuando el modelo invoca solo, elige la copia local:** 27 de 27 cargas en VZ. La del plugin
  solo se usó cuando el dev tipeó el comando con el namespace.
- **Las copias se desfasan.** La `nube-skills-themes` copiada era la v1.3.0: no menciona el hook,
  y su `sync-check.py` no tiene `--stamp` y usa otro criterio que el hook (la fecha de
  `manifest.json` con 30 minutos de tolerancia, contra un marcador de 15). Los dos se pueden
  contradecir: el script dice "podés escribir" y el hook bloquea. En VZ las skills se copiaron del
  repo de MC en vez de instalarse, y así llegó la versión vieja [VZ 2026-09-23].
- El kickoff y el hook existen **solo** en el plugin.

**Qué hacer:** en Claude Code, solo el plugin. `npx skills add` queda para quien use otro agente
(Cursor, Codex), sabiendo que no trae ni hook ni kickoff. En un proyecto que ya tiene las copias
locales, sacarlas es decisión del dev; mientras estén, invocá la del plugin por su nombre con
namespace (`/nube-skills:nube-skills-…`). Las skills propias del proyecto (como la de ui-kit) sí
van en `.claude/skills/` del repo.

## Las piezas, una por una

### `/nube-skills:kickoff`

- **Para qué:** arrancar un proyecto nuevo. Crea o vincula la instalación de Ipanema, la baja
  verificando que vino completa, arma git con `.nuvem` protegido, copia este handoff a
  `.docs/handoff/` y escribe `.claude/CLAUDE.md` desde la [plantilla](plantillas/CLAUDE.md).
- **Cómo se dispara:** solo a mano (`disable-model-invocation: true`), con
  `/nube-skills:kickoff <cliente>`. Viene solo con el plugin.
- **Qué te pide, en una tanda:** cliente y carpeta; la fuente de diseño (nodos de Figma del
  ui-kit, prototipo HTML o ninguna); instalación nueva o existente; quién pushea; si se forkea;
  locales, tiendas hermanas y dominio propio; si querés repo en GitHub.
- **Qué deja:** `.gitignore`, `.docs/handoff/`, `.claude/CLAUDE.md` con las líneas de base
  (schemas, faltantes de i18n, archivos en el servidor) y dos commits (el tema base y la
  documentación). El `authorize` y el `fork` los corre el dev.
- **En la práctica:** el kickoff anterior al 1.5.0 no se usó en VZ, que arrancó con `/init`, y
  `.nuvem` terminó en el primer commit [VZ 2026-09-23]. Paso a paso y por qué, en
  [Arranque](01-arranque.md).

### `nube-skills-themes`

- **Para qué:** el contexto del modelo sectionable (CLI, Fork Workflow, schema, arquitectura) y
  el sync gate.
- **Cómo se dispara:** según su descripción, sola. En la práctica **nunca**: 0 cargas en 54
  sesiones [relevado 2026-09-30]. Invocala con `/nube-skills:nube-skills-themes`.
- **Qué escribe:** nada. Trae `sync-check.py` (ver [Scripts](#scripts)).
- ⚠️ **Tiene partes desactualizadas** respecto de este handoff: el fork "Próximamente", el pull
  sobre el proyecto, `nuvemshop` idéntico, plantillas alternativas "no implementar" y otras (ver
  la lista de problemas al final). Donde difieren, vale lo medido en este handoff.

### `nube-skills-section`

- **Para qué:** convertir un diseño en sections y blocks, con triage de intervención mínima
  (configurar, re-estilizar, extender o construir custom) y criterio settings-first.
- **Cómo se dispara:**
  - sola, al pasar el diseño: en VZ se cargó 11 veces ante pedidos como *"Comencemos con el
    desarrollo de la <página>: <URL del prototipo> … pixel perfect … configurable"*
    [VZ 2026-09-24];
  - a mano: en MC el dev la invocaba con `/nube-skills:nube-skills-section` más
    *"Implement this design from Figma. @<link desktop> / @<link mobile>"* [MC].
- **Qué necesita:** los links de desktop y mobile (con `node-id` si es Figma), la tabla
  `## UI-kit` del `CLAUDE.md`, que el tema esté forkeado, y dos respuestas: los estados
  interactivos y si la section lleva el toggle de visibilidad interna.
- **Qué escribe:** `sections/*.tpl` y `blocks/*.tpl` con su `{% schema %}` (siempre con los
  cuatro paddings: arriba y abajo, desktop y mobile), las claves en todos los locales, la entrada
  en el JSON de la página (re-sincronizando antes) y la fila en `## Bocetos por sección`.
- **Requiere:** el MCP de Figma. Sin boceto, la skill `design` (no está en todas las máquinas).
- ⚠️ **No tiene una vía para prototipos HTML**, y su último paso asume que el agente corre
  `theme push` o `watch`. El método para HTML está en [Diseño y ui-kit](04-diseno-y-ui-kit.md); el
  push lo hace el dev ([Sync y reglas](03-sync-y-reglas.md)).

### `nube-skills-qa`

- **Para qué:** QA visual numérico contra la referencia de diseño, en desktop y mobile,
  separando bugs de código, settings mal configurados y contenido real de la tienda.
- **Cómo se dispara:** sola con frases como *"revisá cómo quedó"*, *"compará con el Figma"* o
  *"QA de la home"*; a mano, con `/nube-skills:nube-skills-qa`. En la práctica se cargó una sola
  vez, en VZ [VZ 2026-09-24].
- **Qué necesita:** la URL de preview, la referencia en `## Bocetos por sección`, el alcance y los
  estados, y la contraseña si la tienda está en modo contraseña.
- **Requiere:** el MCP de chrome-devtools, con el viewport fijado por `emulate`, no por
  `resize_page` (en MC se usó `resize_page` 81 veces contra la indicación de la skill).
- ⚠️ Arma la preview con `?theme_installation_id=`; usá la
  [preview sin login](05-modelo-y-cli.md). El método de QA que funcionó a mano está en
  [Verificación y QA](15-verificacion-y-qa.md).

### `nube-skills-i18n`

- **Para qué:** auditar y completar claves de traducción, distinguiendo `t:` (editor,
  `*.schema.json`) de `| t` (storefront, `*.json`).
- **Cómo se dispara:** como skill no se cargó nunca, pero su script corrió 85 veces porque el
  `CLAUDE.md` del proyecto lo lista [relevado 2026-09-30]. **Corré el script directo**.
- ⚠️ **No audita el registro** (voseo o tuteo, talle o talla): solo que la clave exista. Ver
  [Schema y traducciones](06-schema-y-traducciones.md).

### `nube-skills-admin`

- **Para qué:** el backoffice y la Admin API (`2025-03`): triage de qué se puede, lecturas libres
  y escrituras en cinco tiempos (dry-run, diff, backup, confirmación y ejecución).
- **Cómo se dispara:** sola, ante pedidos como *"Creá por API las páginas que necesites"* (dos
  veces en VZ) [VZ 2026-09-24].
- **Qué necesita:** el MCP oficial de Tienda Nube o las variables `TN_STORE_ID`,
  `TN_ACCESS_TOKEN` y `TN_USER_AGENT`. En VZ se usó el token de `.nuvem`: cómo, con qué límites y
  sin imprimirlo, en [Límites y Admin API](13-limites-y-admin-api.md).
- **Qué escribe:** backups antes de cada escritura y el reporte de aplicados, fallidos y
  pendientes.

### La skill de proyecto `<cliente>-ui-kit`

No es del plugin: es un patrón que surgió en VZ y vive en `.claude/skills/` del repo. Se cargó
sola en las 13 sesiones de construcción de VZ, justamente porque su descripción dice cuándo
usarla [VZ 2026-09-24]. Qué contiene y por qué existe, en
[Diseño y ui-kit](04-diseno-y-ui-kit.md); el esqueleto, en
[`plantillas/ui-kit-skill/SKILL.md`](plantillas/ui-kit-skill/SKILL.md).

## Scripts

Dentro del caché del plugin la ruta lleva la versión, y una ruta fija se rompe en el próximo
release (le pasó al `CLAUDE.md` de VZ). Resolvela en el momento:

```bash
NS="$(ls -d ~/.claude/plugins/cache/nube-skills/nube-skills/*/ | sort -V | tail -1)"

# sync-check: ¿es seguro escribir? (pull registrado, git, watch, fork, capa de cada archivo)
python3 "${NS}skills/nube-skills-themes/scripts/sync-check.py" . --files templates/pages/home.json
python3 "${NS}skills/nube-skills-themes/scripts/sync-check.py" . --stamp   # registrar un pull hecho a mano
#   opciones: --max-age MIN, --no-fetch, --json · exit 0 = podés escribir, 1 = falta sincronizar,
#   2 = la carpeta no es un tema del Fork Workflow

# audit-i18n: claves faltantes, huérfanas y mezcladas entre los locales
python3 "${NS}skills/nube-skills-i18n/scripts/audit-i18n.py" .            # --json para máquina
#   exit 0 = sin faltantes, 1 = faltantes o archivo ilegible, 2 = error de uso

# tn-api: cliente de la Admin API con rate limit y paginación
python3 "${NS}skills/nube-skills-admin/scripts/tn-api.py" GET products --paginate --param published=true --json
python3 "${NS}skills/nube-skills-admin/scripts/tn-api.py" PATCH products/<id>/variants --data-file cambio.json --dry-run
#   --backup <archivo> guarda el estado actual antes de escribir · exit 0 = OK, 1 = error de la API, 2 = uso
```

## El hook `sync-gate`

Corre en toda escritura y en todo Bash, sin depender de qué skills estén cargadas. Es la única
defensa del modo de falla de [Sync y reglas](03-sync-y-reglas.md) que no depende de que alguien se
acuerde.

- **Bloquea (`deny`)** escribir `templates/**` y `config/settings_data.json`, y cualquier Bash con
  `theme push`, si no hay un pull registrado en los últimos 15 minutos. El mensaje de bloqueo dice
  qué pasos correr.
- **Pide confirmación (`ask`)** ante cualquier `theme publish`.
- **Registra el pull** después de un `theme pull` que salió bien, en un marcador por tema en
  `~/.cache/nube-skills/`, fuera del repo. Lo corrobora con que `manifest.json` se haya reescrito
  en los últimos 5 minutos.
- **Es inerte** fuera de un tema de Tienda Nube y **deja pasar** ante cualquier error interno.
  Nunca bloquea `sections/`, `blocks/`, `snippets/` ni `static/`.
- **Los escapes son del dev, no del agente:** `NUBE_SKIP_SYNC_GATE=1` lo apaga y
  `NUBE_SYNC_MAX_AGE_MIN` cambia la ventana.

### Cómo se usa con el pull a un temporal

El hook registra el pull **en la carpeta donde corrió**. Como en la práctica el pull va a un
temporal (y nunca sobre el proyecto si hay watch), el marcador queda en el temporal: 108 de los 112
marcadores de una máquina eran de temporales [relevado 2026-09-30]. Después de comparar, se
registra en el proyecto con `sync-check.py . --stamp` ([Sync y reglas](03-sync-y-reglas.md)).

⚠️ El `--stamp` lo corre el propio modelo y el hook le cree. **Que el hook no bloquee no prueba que
estés sincronizado**: el criterio sigue siendo tuyo.

### Falsos positivos conocidos, y cómo seguir

| Qué pasa | Cómo seguir |
|---|---|
| El texto `theme push` en **cualquier** parte de un comando lo bloquea: un mensaje de commit que lo menciona [VZ 2026-09-23], un `theme push --help` [MC 2026-09-25] | reformular el mensaje; para ver procesos, `grep "cli.js theme"` en vez de nombrar el comando |
| `theme publish` escrito dentro de un heredoc pide confirmación [MC] | rechazar la confirmación: no hubo publish |
| Para Bash, el tema se resuelve por el **cwd de la sesión**, no por el `cd` del comando: un push a un repo hermano quedó bloqueado contra el marcador del repo de la sesión [MC 2026-09-25] | el push lo corre el dev desde la carpeta de ese repo ([Multi-país](16-multipais-apps-integraciones.md)) |
| Bloquea **crear** una plantilla nueva, aunque un archivo nuevo no pisa nada [MC 2026-09-10] | pull a un temporal para confirmar que el comerciante no la creó desde el Admin, y `--stamp` |

### Lo que no ve

- **Las escrituras por Bash** (un `python3` con `json.dump`, `cp`, `sed`): en MC hubo unas 27 sobre
  la capa del comerciante contra 14 por Write o Edit [relevado 2026-09-30]. Escribí esa capa con
  Write o Edit, así el hook la ve, y nunca por Bash para esquivarlo.
- **Lo que sube `theme watch`**: con watch prendido cada guardado es un push, y el hook no se
  entera ([Sync y reglas](03-sync-y-reglas.md)).
- **El pull a un temporal y `theme diff`** no cuentan como sync hasta que corrés `--stamp`.

## Uso real, en cifras

Relevado el 2026-09-30 sobre los transcripts de MC (38 sesiones, 21/8 a 28/9) y VZ (16 sesiones,
23/9 a 29/9):

| | María Cher | VZ |
|---|---|---|
| `/nube-skills:kickoff` | usado (la sesión no quedó, sí el commit) | 0 (arrancó con `/init`) |
| `nube-skills-themes` | 0 | 0 |
| `nube-skills-section` | 1 sola + 3 a mano | 11 sola |
| `nube-skills-qa` | 0 | 1 |
| `nube-skills-i18n` (skill / script) | 0 / 9 | 0 / 76 |
| `nube-skills-admin` (skill / `tn-api.py`) | 0 / 4 | 2 / 12 |
| skill de ui-kit del proyecto | — | 13 |
| bloqueos del hook (legítimos / falsos) | 2 / 2 | 1 / 1 |
| pulls del agente (todos a un temporal) | 57 | 89 |
| `theme diff` | 5 | 11 |
| pushes del agente | 0 | 0 |
| llamadas al MCP de chrome-devtools / de Figma | ~1.340 / 48 | ~460 / 0 |

Lo que dice la tabla: el trabajo real pasó por `section`, por los scripts y por el MCP de
chrome-devtools; `themes` y `qa` casi no se usaron como skills, y el sync se hizo siempre contra
un temporal.

## Problemas conocidos del plugin y cómo esquivarlos

Pendientes para una versión futura del plugin. Mientras tanto:

**Hook**
- Matchea el texto `theme push` en cualquier comando → reformular (tabla de arriba).
- Resuelve Bash por el cwd de la sesión → el push de un repo hermano lo corre el dev desde ese
  repo.
- Bloquea archivos nuevos → confirmar en un temporal que no existen en el servidor y `--stamp`.
- No ve escrituras por Bash → escribir la capa del comerciante solo con Write o Edit.
- No reconoce el pull a un temporal ni `theme diff` → `--stamp` después de comparar.

**`nube-skills-themes`**
- Dice que el fork está "Próximamente" → funciona ([Modelo y CLI](05-modelo-y-cli.md)).
- Prescribe `theme pull` sobre el proyecto y no advierte sobre watch → seguí el protocolo de
  [Sync y reglas](03-sync-y-reglas.md).
- Documenta `installation_id` en `manifest.json` → el campo real es `theme_id`
  ([Modelo y CLI](05-modelo-y-cli.md)).
- No conoce `theme diff` → existe en el CLI 2.3.1 y es solo lectura.
- Dice que no se implementen plantillas alternativas → rutean ([Plantillas](12-plantillas.md)).
- Dice que `nuvemshop` es idéntico a `tiendanube` → no: manda `region=br`.
- Su referencia de sync sugiere `git add -A && git commit -m "wip"` → contra las reglas del
  equipo: stagear por archivo.

**`nube-skills-section`**
- No tiene vía para el HTML de Claude Design → [Diseño y ui-kit](04-diseno-y-ui-kit.md).
- Asume que el agente corre `push` o `watch` → los corre el dev.

**`nube-skills-qa`**
- Usa `?theme_installation_id=` → la preview sin login, `?preview_theme_installation_id=`.

**`nube-skills-i18n`**
- No audita el registro → revisarlo a mano ([Schema y traducciones](06-schema-y-traducciones.md)).

**`nube-skills-admin`**
- No menciona el token de `.nuvem`, y `fields=features` da 422 →
  [Límites y Admin API](13-limites-y-admin-api.md).

**En general**
- Las copias locales duplicadas y sin descripción → solo el plugin (arriba).
- La skill `design` no está garantizada en todas las máquinas (apareció en las sesiones de MC y en
  ninguna de VZ) → las alternativas sin boceto, en [Diseño y ui-kit](04-diseno-y-ui-kit.md).
