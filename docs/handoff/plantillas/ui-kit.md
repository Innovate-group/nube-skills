# UI-kit de «cliente»

Referencia completa del sistema visual: valores, anomalías y por qué. La skill de proyecto
`«cliente»-ui-kit` dice **cómo usarlo**; este archivo guarda el detalle. Se lee por sección,
no entero.

## Fuentes y cuál manda

| Fuente | Rol |
|---|---|
| «design system / nodos del ui-kit» | tokens con nombre |
| «boceto / prototipo» | cómo se ve cada pieza, desktop y mobile |
| «notas de diseño» | qué ajustar, construir o verificar por sección |

Un valor que la fuente de tokens nombra sale del token. Lo que no define se mide en el boceto.
Si se contradicen, se anota como anomalía y se pregunta: no se resuelve por cuenta propia.

## Anomalías

Contradicciones entre fuentes, valores fuera de paleta, fuentes que no están en el font
picker. Van numeradas para poder citarlas desde el `CLAUDE.md` y el código. Cada una lleva su
decisión provisoria hasta que diseño la confirme, y la fecha en que se resolvió.

| # | Qué | Decisión | Estado |
|---|---|---|---|
| A1 | «…» | «…» | abierta |

## Colores

| Token | Valor | Uso | Origen |
|---|---|---|---|

## Tipografía

## Botones

## Formularios

## Card de producto

## Iconografía

## Espaciados, grilla y breakpoints

## Animaciones

## Remapeo de los tokens del tema base

Qué token de Ipanema pasa a qué valor del kit, al final de `layouts/resources/style-tokens.tpl`
(`--border-radius`, `--transition-*`, `--gutter-container`, `--spacing-section`,
`--h1`…`--h6`, los colores semánticos). Remapearlos corrige cientos de reglas del base sin
tocarlas.

| Token del base | Valor del kit | Por qué |
|---|---|---|

## Verificado en vivo

Lo medido en la preview contra la fuente, con fecha.
