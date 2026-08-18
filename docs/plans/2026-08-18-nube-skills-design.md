# Diseño: nube-skills — skills y comandos de Claude Code para temas nuevos de Tienda Nube

**Fecha:** 2026-08-18 · **Estado:** aprobado · **Catálogo completo en v1.0.0** (las 5 piezas publicadas)

## Contexto y objetivo

Innovate Group desarrolla y mantiene temas de Tienda Nube. Con el nuevo modelo sectionable (tema base Ipanema, Fork Workflow vía `@tiendanube/cli`), todos los rediseños de clientes nuevos parten de Ipanema. El flujo típico: boceto Figma desktop + mobile por cliente; el dev pasa el nodo Figma de cada sección/componente al agente, que desarrolla vía MCP.

Objetivo: un repo público en GitHub (`Innovate-group/nube-skills`) con skills y comandos de Claude Code que agilicen el desarrollo y mantenimiento de estos proyectos, instalable como plugin (estilo obra/superpowers) y descubrible en skills.sh.

## Decisiones aprobadas

- **Arquitectura:** monorepo dual-canal. Un repo = un plugin de Claude Code con muchas skills. `skills/` en la raíz es escaneado tanto por el sistema de plugins como por el CLI de skills.sh (`npx skills add`) — sin duplicación (patrón verificado en obra/superpowers, que sirve ambos canales desde un repo).
- **Nombre:** `nube-skills` (org `Innovate-group`). Namespace de comandos: `/nube-skills:<comando>`.
- **Visibilidad:** público desde el día uno. Contenido escrito para público: sin nombres de clientes, tokens ni URLs internas.
- **Idioma:** español (comunidad Tienda Nube = LatAm; la doc oficial está en es-AR). Descriptions de frontmatter con triggers bilingües.
- **Rediseños mixtos:** la skill Figma→section hace triage por nodo: re-estilizar/configurar una section de Ipanema cuando alcanza, crear section/block custom cuando el diseño difiere estructuralmente.
- **Convención de nombres (agregada 2026-08-18):** toda skill del catálogo se llama `nube-skills-<qué-hace>` (ej. `nube-skills-themes`); los comandos usan el namespace del plugin (`/nube-skills:<comando>`).

## Layout del repo

```
Innovate-group/nube-skills/
├── .claude-plugin/
│   ├── plugin.json          # name: nube-skills, version, description
│   └── marketplace.json     # marketplace propio, un plugin, source: "./"
├── skills/
│   └── <nombre>/SKILL.md (+ references/)
├── commands/
│   └── <comando>.md         # solo llega por el canal plugin
├── scripts/
│   └── validate.py          # validación de frontmatter/estructura (adaptado de skill-creator)
├── .github/workflows/
│   └── validate.yml         # CI: valida todas las skills en cada push
├── docs/plans/              # documentos de diseño y planes
├── CHANGELOG.md
├── README.md                # español: qué es, catálogo, instalación por ambos canales
└── LICENSE                  # MIT
```

## Instalación (README)

```bash
# Equipo (plugin: skills + comandos + futuros hooks)
/plugin marketplace add Innovate-group/nube-skills
/plugin install nube-skills@nube-skills

# Comunidad (skills solamente; así se siembra el índice de skills.sh)
npx skills add Innovate-group/nube-skills
```

## Catálogo inicial y orden de construcción

| Orden | Pieza | Tipo | Descripción |
|---|---|---|---|
| 1 | `nube-skills-themes` | skill (ya construida) | Fundación de contexto: modelo sectionable, Fork Workflow, detección de generación de tema, referencias de la doc oficial. Migra desde `~/.claude/skills/tiendanube-sectionable-themes` (renombrada). Las demás piezas la referencian en vez de duplicar doc. |
| 2 | `nube-skills-section` | skill (core) | Input: nodo(s) Figma desktop+mobile. Extrae design context y screenshot vía MCP de Figma; **triage** (¿re-estilizar section de Ipanema o crear custom?); genera section/block `.tpl` con `{% schema %}`, claves `t:` en todos los locales, entrada en el JSON template. Aplica las reglas duras de la skill 1. |
| 3 | `/nube-skills:kickoff` | comando | Arranque de cliente: `theme create --base-theme ipanema` o clone, `pull`, git init con `.gitignore` correcto (`.nuvem`), CLAUDE.md del proyecto, checklist inicial. |
| 4 | `nube-skills-i18n` | skill | Audita y completa traducciones: claves `t:` y `\| t` usadas pero faltantes en algún `<locale>.json` / `<locale>.schema.json`; alta en todos los locales respetando fallback. |
| 5 | `nube-skills-qa` | skill | QA visual: preview del tema (`?theme_installation_id`) + screenshots desktop/mobile con MCP de Chrome DevTools, comparación contra los nodos Figma, reporte de diferencias (adapta el enfoque de design-compare al flujo TN). |

Excluido a propósito (YAGNI): comando de deploy/publish, skill de performance (`theme performance` ya existe en el CLI), wrapper de comando para la pieza 2.

## Flujo de trabajo del repo

1. Una pieza a la vez; commits directos a `main` mientras el equipo sea chico (PRs cuando contribuyan otros).
2. Antes de commitear: `scripts/validate.py` + prueba local real (instalar la skill y verificar que dispara).
3. CI en GitHub Actions valida frontmatter y estructura de todas las skills en cada push.
4. Cada pieza nueva = bump semver menor en `plugin.json` + entrada en `CHANGELOG.md`. El equipo actualiza con `/plugin update`.
5. skills.sh: sin submission — el repo aparece por telemetría del CLI. Al publicar: auto-instalación con `npx skills add` para sembrar el índice + topics del repo (`tiendanube`, `claude-code`, `agent-skills`).

## Migración

- Al instalar el plugin, borrar la copia personal `~/.claude/skills/tiendanube-sectionable-themes` (quedaría duplicada) — vale para todo el equipo que instaló por zip.
- El `.skill` distribuido a mano queda legacy; el canal oficial pasa a ser el repo.

## Convenciones de contenido

- Skills en español, frontmatter solo `name` + `description` (triggers bilingües + anti-triggers explícitos).
- Referencias con tabla de contenidos; SKILL.md < 500 líneas; progressive disclosure.
- Nunca datos internos de la agencia ni de clientes.
