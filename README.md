# nube-skills

Skills y comandos de [Claude Code](https://claude.com/claude-code) para [Tienda Nube](https://tiendanube.dev): desarrollo y mantenimiento de temas **sectionable** (tema base Ipanema, Fork Workflow) y operación del **backoffice** vía Admin API. Mantenido por [Innovate Group](https://github.com/Innovate-group).

## Instalación

**Como plugin de Claude Code** (skills + comandos):

```
/plugin marketplace add Innovate-group/nube-skills
/plugin install nube-skills@nube-skills
```

**Solo las skills**, con el [CLI de skills.sh](https://skills.sh) (funciona en Claude Code, Cursor, Codex y 70+ agentes):

```bash
npx skills add Innovate-group/nube-skills
```

**Actualizar a la última versión** (cuando se anuncie un release):

```bash
claude plugin marketplace update nube-skills
claude plugin update nube-skills@nube-skills
```

(reiniciar la sesión para que aplique; vía skills.sh: `npx skills update`)

## Catálogo

| Pieza | Tipo | Estado | Descripción |
|---|---|---|---|
| `nube-skills-themes` | skill | ✅ disponible | Contexto completo del modelo sectionable: arquitectura, sections/blocks/snippets, schema, CLI y Fork Workflow, con detección automática de generación de tema (nuevo / clásico / Shopify). Define el **sync gate**: nadie escribe un archivo del tema sin pullear antes. |
| `nube-skills-section` | skill | ✅ disponible | Construye sections, blocks y componentes: de un nodo de Figma (desktop + mobile) o, sin boceto, dibujando primero un mockup con la skill `design`. Hace triage (configurar / re-estilizar / extender / custom), es settings-first, y genera `.tpl` + `{% schema %}` + traducciones + registro en el JSON template. |
| `/nube-skills:kickoff` | comando | ✅ disponible | Arranque de un cliente nuevo: instalación Ipanema con el CLI, pull verificado, git con `.nuvem` protegido, el handoff de nube-skills en `.docs/handoff/` y `.claude/CLAUDE.md` del proyecto (con el ui-kit que usan las demás skills). |
| `nube-skills-i18n` | skill | ✅ disponible | Auditoría y alta de claves de traducción: detecta las usadas en el código que faltan en algún locale (el `t:` crudo que aparece en el editor), distingue los dos sistemas (`t:` de schema vs `\| t` de storefront) e incluye un script determinista de auditoría. |
| `nube-skills-admin` | skill | ✅ disponible | Experto en el backoffice y la Admin API: hace triage de qué se puede por API, qué necesita aprobación de Tienda Nube, qué es solo del panel y qué es imposible; ejecuta lecturas libres y escrituras con dry-run, backup y confirmación explícita. Incluye un cliente HTTP con rate limit y paginación correctos. |
| `nube-skills-qa` | skill | ✅ disponible | QA visual contra el diseño en desktop y mobile: maneja la preview con el MCP de Chrome DevTools, compara estilos computados (no píxeles a ojo), revisa estados interactivos y reporta hallazgos priorizados separando bugs de código, settings mal configurados y contenido real de la tienda. |

| `sync-gate` | hook | ✅ disponible | Enforcement determinista del sync gate: bloquea escrituras sobre `templates/**` y `config/settings_data.json` (y `theme push`) sin un `theme pull` reciente, y pide confirmación en `theme publish`. Corre siempre, sin depender de qué skills estén cargadas. |

Convención de nombres: toda skill del catálogo se llama `nube-skills-<qué-hace>`; los comandos llevan el namespace del plugin (`/nube-skills:<comando>`).

## Cómo se encadenan

Un rediseño típico recorre las piezas en este orden. Salvo el kickoff, no hace falta invocarlas: se disparan solas según lo que estés haciendo.

1. **Arranque** — `/nube-skills:kickoff` crea o vincula la instalación de Ipanema, la baja verificando que vino completa, prepara git, copia el handoff a `.docs/handoff/` y escribe `.claude/CLAUDE.md` con la fuente de diseño (Figma, prototipo HTML o ninguna) y el ui-kit.
2. **Desarrollo** — le pasás a Claude el nodo de Figma de una sección y `nube-skills-section` decide la intervención mínima (configurar lo que ya existe o construir algo nuevo) y genera el código. Sin boceto, dibuja primero un mockup. `nube-skills-themes` le da el contexto del modelo sectionable a todo lo demás.
3. **Traducciones** — `nube-skills-i18n` audita que ninguna clave quede a medias entre locales.
4. **Revisión** — `nube-skills-qa` compara lo implementado contra el diseño en desktop y mobile antes de publicar.

En los cuatro pasos aplica la misma regla, definida en `nube-skills-themes`: **antes de escribir cualquier archivo del tema se sincroniza** (commit/stash → `git pull` → `tiendanube theme pull` → leer el diff). El comerciante edita `templates/**` y `config/settings_data.json` desde el editor de la tienda mientras el equipo trabaja, y `theme push` sincroniza eliminaciones: escribir con una copia vieja no le pisa los cambios, se los borra. La parte verificable la chequea `skills/nube-skills-themes/scripts/sync-check.py`.

## El handoff

[`docs/handoff/`](docs/handoff/README.md) junta lo aprendido construyendo temas Ipanema reales — María Cher (con sus tiendas de Chile y Uruguay), Garçon García y VZ, entre agosto y septiembre de 2026: qué decidir y qué correr el día 1, cómo se usan estas skills en la práctica y sus problemas conocidos, el protocolo de sync tal como se practica, y las trampas medidas de Twig, CSS, JS, la plataforma y el CLI. Lectura obligatoria: `README` + `01`–`03`; el resto se consulta por tema.

`/nube-skills:kickoff` lo copia a `.docs/handoff/` de cada proyecto nuevo. La copia es una foto del día del kickoff: no se edita ni se actualiza, y los proyectos que ya arrancaron no la reciben. Lo genérico que se aprenda en un proyecto vuelve acá, para el siguiente.

## El sync gate no depende de que la IA se acuerde

Una skill se carga cuando el modelo decide que es relevante, y sus reglas se pueden saltear. Por eso el plugin incluye un **hook** (`hooks/`) que lo hace determinista: corre en toda escritura, sin importar qué skills estén cargadas.

| Qué hace | Cuándo |
|---|---|
| **Bloquea** (`deny`) escribir en `templates/**` y `config/settings_data.json` | Cuando no hay un `tiendanube theme pull` registrado en los últimos 15 minutos. El mensaje de bloqueo le dicta a la IA los 4 pasos del gate |
| **Bloquea** `tiendanube theme push` | Misma condición: es el comando que sincroniza eliminaciones |
| **Pide confirmación** (`ask`) en `tiendanube theme publish` | Siempre: publicar un borrador reemplaza la instalación productiva entera |
| **Registra** el pull | Después de cada `theme pull` exitoso (corroborado contra el mtime de `manifest.json`) |

Detalles de diseño, por si hay que auditarlo:

- **Inerte fuera de un tema de Tienda Nube.** Sube por el árbol buscando `.nuvem` o un `manifest.json` que *parsee y tenga campos del CLI* (`installation_id` / `revision_token`), así un `manifest.json` de PWA o de extensión no activa nada.
- **Fail-open.** Cualquier error interno permite la operación: un hook roto no puede bloquear el trabajo en todos los proyectos.
- **Solo la capa compartida.** Escribir `sections/`, `blocks/`, `snippets/` o `static/` no se bloquea nunca.
- **Rápido** (~35 ms) y sin red: solo filesystem.
- **Escapes, para el dev, no para la IA:** `NUBE_SKIP_SYNC_GATE=1` desactiva el gate; `NUBE_SYNC_MAX_AGE_MIN` cambia la ventana de 15 min; `sync-check.py <tema> --stamp` registra un pull hecho a mano en otra terminal.

**Requisitos y verificación** (el hook viene solo por el plugin — la instalación con `npx skills add` copia skills, no hooks):

```
claude plugin marketplace update nube-skills
claude plugin update nube-skills@nube-skills
```

Reiniciá la sesión (o `/reload-plugins`) y confirmá con `/hooks` que aparecen `PreToolUse` y `PostToolUse` de nube-skills. Si no aparecen: revisá que el plugin esté habilitado, que no haya `disableAllHooks: true` en ningún settings, y que el `.zshrc`/`.bashrc` no imprima nada sin condicionar a shell interactiva (esa salida se mezcla con el JSON del hook y lo invalida).

Para desactivarlo del todo, deshabilitá el plugin o exportá `NUBE_SKIP_SYNC_GATE=1` en tu entorno.

## Requisitos

- Los flujos de CLI asumen [`@tiendanube/cli`](https://tiendanube.dev/themes/developer-tools/cli/overview) (declara Node 24.15+; corre con Node 22.22) y el Fork Workflow (hoy disponible solo para Ipanema).
- La skill de Figma requiere el [MCP oficial de Figma](https://developers.figma.com) conectado.

## Desarrollo

Cada skill vive en `skills/<nombre>/SKILL.md`. Antes de commitear: `python3 scripts/validate.py`. El CI valida lo mismo en cada push.

## Licencia

[MIT](LICENSE)
