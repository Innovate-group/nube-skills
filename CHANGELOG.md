# Changelog

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
