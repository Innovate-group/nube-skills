# nube-skills

Skills y comandos de [Claude Code](https://claude.com/claude-code) para el desarrollo y mantenimiento de temas **sectionable** de [Tienda Nube](https://tiendanube.dev) (tema base Ipanema, Fork Workflow). Mantenido por [Innovate Group](https://github.com/Innovate-group).

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

## Catálogo

| Pieza | Tipo | Estado | Descripción |
|---|---|---|---|
| `tiendanube-sectionable-themes` | skill | ✅ disponible | Contexto completo del modelo sectionable: arquitectura, sections/blocks/snippets, schema, CLI y Fork Workflow, con detección automática de generación de tema (nuevo / clásico / Shopify). |
| `tiendanube-figma-section` | skill | 🔜 en camino | De un nodo de Figma (desktop + mobile) a una section/block de Ipanema: triage re-estilizar vs. custom, `.tpl` + `{% schema %}` + traducciones + JSON template. |
| `/nube-skills:kickoff` | comando | 🔜 en camino | Arranque de un cliente nuevo: instalación Ipanema con el CLI, pull, git y checklist. |
| `tiendanube-i18n` | skill | 🔜 en camino | Auditoría y alta de claves de traducción en todos los locales. |
| `tiendanube-theme-qa` | skill | 🔜 en camino | QA visual de la implementación contra el boceto de Figma (desktop y mobile). |

## Requisitos

- Los flujos de CLI asumen [`@tiendanube/cli`](https://tiendanube.dev/themes/developer-tools/cli/overview) (Node 24.15+) y el Fork Workflow (hoy disponible solo para Ipanema).
- La skill de Figma requiere el [MCP oficial de Figma](https://developers.figma.com) conectado.

## Desarrollo

Cada skill vive en `skills/<nombre>/SKILL.md`. Antes de commitear: `python3 scripts/validate.py`. El CI valida lo mismo en cada push.

## Licencia

[MIT](LICENSE)
