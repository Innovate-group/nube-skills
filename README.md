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

**Actualizar a la última versión** (cuando se anuncie un release):

```bash
claude plugin marketplace update nube-skills
claude plugin update nube-skills@nube-skills
```

(reiniciar la sesión para que aplique; vía skills.sh: `npx skills update`)

## Catálogo

| Pieza | Tipo | Estado | Descripción |
|---|---|---|---|
| `nube-skills-themes` | skill | ✅ disponible | Contexto completo del modelo sectionable: arquitectura, sections/blocks/snippets, schema, CLI y Fork Workflow, con detección automática de generación de tema (nuevo / clásico / Shopify). |
| `nube-skills-figma-section` | skill | ✅ disponible | De un nodo de Figma (desktop + mobile) a código del tema: triage (configurar / re-estilizar / extender / custom), settings-first, `.tpl` + `{% schema %}` + traducciones + registro en el JSON template. |
| `/nube-skills:kickoff` | comando | ✅ disponible | Arranque de un cliente nuevo: instalación Ipanema con el CLI, pull, git con `.nuvem` protegido, y `CLAUDE.md` del proyecto (con el ui-kit que usan las demás skills). |
| `nube-skills-i18n` | skill | 🔜 en camino | Auditoría y alta de claves de traducción en todos los locales. |
| `nube-skills-qa` | skill | 🔜 en camino | QA visual de la implementación contra el boceto de Figma (desktop y mobile). |

Convención de nombres: toda skill del catálogo se llama `nube-skills-<qué-hace>`; los comandos llevan el namespace del plugin (`/nube-skills:<comando>`).

## Requisitos

- Los flujos de CLI asumen [`@tiendanube/cli`](https://tiendanube.dev/themes/developer-tools/cli/overview) (Node 24.15+) y el Fork Workflow (hoy disponible solo para Ipanema).
- La skill de Figma requiere el [MCP oficial de Figma](https://developers.figma.com) conectado.

## Desarrollo

Cada skill vive en `skills/<nombre>/SKILL.md`. Antes de commitear: `python3 scripts/validate.py`. El CI valida lo mismo en cada push.

## Licencia

[MIT](LICENSE)
