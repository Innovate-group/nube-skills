---
name: «cliente»-ui-kit
description: "Sistema visual de «cliente» para este tema de Tienda Nube (Ipanema). Usar ANTES de escribir o revisar CSS, markup o defaults de schema de cualquier section, block, snippet o componente de «cliente» — colores, tipografía, botones, inputs, card de producto, íconos, espaciados, breakpoints, animaciones — para usar los tokens y las clases del kit en vez de valores sueltos o defaults de Ipanema. Triggers: «cliente», ui kit, design system, tokens, paleta, tipografía, botón, input, maquetar sección."
---

# UI-kit de «cliente»

El sistema visual ya está implementado en el tema. Esta skill dice **cómo usarlo** al construir
o corregir cualquier pieza. La referencia completa está en **`.docs/ui-kit.md`**: leé ahí solo
la sección que tu componente necesite.

## Fuentes y cuál manda

«qué fuente da los tokens, cuál da las piezas y cuál da el alcance; qué hacer si se contradicen»

## Reglas que no se negocian

1. Nunca un hex, un `ease`, un radio ni una `font-family` sueltos: todo sale de `--«prefijo»-*`
   o de los tokens del base que el kit ya remapeó.
2. «breakpoint del kit, curva única, hover, tipografía, íconos…»

## Tokens de uso diario

| Para | Token |
|---|---|

## Componentes que ya existen: reusalos, no los rehagas

| Necesitás | Usá |
|---|---|

Esta tabla crece con cada página construida.

## Dónde se escribe

- **Tokens nuevos** → `layouts/resources/style-tokens.tpl`, § «cliente», y una fila en
  `.docs/ui-kit.md`.
- **Estilos de componente** → junto a la regla que pisan. `style-async.css` carga después que
  `style-critical.css`: antes de pisar algo, buscá en qué hoja vive.

## Antes de dar por terminada una pieza

- [ ] Ningún valor suelto: `grep -nE '#[0-9a-fA-F]{3,6}\b|\bease\b|border-radius: *[1-9]|font-family' <archivos>`.
- [ ] Mobile y desktop medidos contra la fuente en la preview.
- [ ] Toda decisión sobre algo que la fuente no define, anotada en `.docs/ui-kit.md`.
- [ ] La fila de la sección en `## Bocetos por sección` del `CLAUDE.md`.
- [ ] Si se cerró una anomalía, actualizada acá y en `.docs/ui-kit.md`.
