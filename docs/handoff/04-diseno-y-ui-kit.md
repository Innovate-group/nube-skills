# Diseño y ui-kit

Cómo se pasa la fuente de diseño a código en un tema Ipanema: quién manda cuando dos cosas
dicen distinto, las tres vías que aparecieron en la práctica (Figma, prototipo HTML de Claude
Design, sin boceto), y cómo se implementa y se documenta el ui-kit antes de construir la
primera section.

## Lo esencial

- **La fuente de diseño manda sobre el tema base.** Si el diseño define un valor, no se deja
  el default de Ipanema con el argumento de que "no está tokenizado": se mide sobre la fuente.
  Hay tres matices:
  - un estado dibujado en una pantalla no le gana al componente;
  - un pedido explícito del dev o del cliente gana, y queda documentado;
  - los typos no se copian.
- **Cada proyecto llega con una de tres vías:**
  - nodos de Figma (MC);
  - prototipos HTML de Claude Design (GG y VZ);
  - nada: un brief escrito o la skill `design`.

  Las skills del plugin asumen Figma. La vía HTML se trabaja a mano, con `curl` y `grep`.
- **El ui-kit va antes que la primera section.** Son tres piezas:
  - `.docs/ui-kit.md`, con las anomalías numeradas;
  - los tokens en `style-tokens.tpl`, con el remapeo de los tokens del base;
  - una skill de proyecto `<cliente>-ui-kit`.
- **Toda contradicción entre fuentes se numera como anomalía**, con una decisión provisoria.
  No se resuelve por cuenta propia.
- **Las tablas `## UI-kit` y `## Bocetos por sección` del `CLAUDE.md` son contrato** con
  `nube-skills-section` y `nube-skills-qa`. Cada sección construida suma su fila, con la
  referencia desktop, la mobile y el código que la implementa.
- **El `CLAUDE.md` queda liviano y el detalle va a `.docs/`.** El de MC llegó a 571 KB y se
  inyecta entero en cada sesión.

## Quién manda

### La fuente de diseño manda sobre el tema base

✅ Es una corrección explícita del dev *[MC 2026-08-20]*. En el kickoff de MC se dejaron
valores del tema base sin tocar porque el ui-kit no los tenía tokenizados: el color de fondo
del footer, el color de un link destacado, el radio de los botones, los tamaños tipográficos.
Se reportaron como "pendientes de definición del diseño". El dev lo corrigió: eso es dejar los
defaults de Ipanema pisando el diseño.

- **Si un valor no aparece como variable de Figma, se mide sobre el nodo.**
  - `get_design_context` devuelve el CSS de referencia: radios, paddings, tamaños.
  - `get_metadata` da la estructura.
  - `download_assets` baja logos e íconos como SVG.

  Las variables de Figma son solo una capa; el nodo tiene el resto. Recién si el nodo tampoco
  lo define, se pregunta.
- **Si dos tokens de la fuente se contradicen** (por ejemplo, dos escalas de grises), se
  resuelve mirando cuál se usa de verdad en el diseño, no eligiendo por criterio propio
  *[MC 2026-08-20]*.
- **El principio es el mismo con cualquier fuente.** En GG y VZ la herramienta fue otra
  (prototipos HTML, ver abajo), pero la regla no cambió: medir sobre la fuente antes que
  dejar el valor del base.
- **Con un pedido de pixel perfect, la pieza gana sobre el token.** En VZ, cuando el design
  system y el boceto se contradecían, el boceto ganó en casi todas las anomalías: A1, A4, A5,
  A10, A12, A13 y A15–A21 *[VZ 2026-09-24]*.

### Tres matices

1. **Un estado no le gana al componente.** A veces el nodo de una pantalla pinta un estado del
   componente: por ejemplo `#1B1B1B`, que es el *pressed* del botón. En ese caso gana el
   default del componente en el ui-kit (`#000000`), para no terminar con un negro distinto en
   un solo botón *[MC]*.
2. **Un pedido explícito del dev o del cliente gana, y se documenta como divergencia.** En MC,
   por ejemplo:
   - los gaps del menú drawer;
   - un escalón de tipografía;
   - un nodo de 3 columnas que dejó de aplicar.

   Hay que anotar de quién es cada pedido ("Pedido del dev", "Pedido del cliente", "Decisión
   del dev"), con la cita textual y la fecha. Las vueltas atrás también se anotan, explícitas:
   "es la vuelta atrás de la decisión del 2026-08-26" *[MC]*.
3. **Los typos del diseño no se copian.** El Figma de MC decía "Añadír" *[MC]*. La excepción
   son los **textos legales**: se copian verbatim, con typos incluidos, y no se persigue la
   diferencia de renglones entre el diseño y el navegador (1,4 % en MC) *[MC]*.

Y una regla de traducción: **se reproduce el resultado, no la propiedad.** Un `items-start` de
Figma sobre un texto de ancho fijo se traduce a `stretch` en CSS, porque eso es lo que da la
misma caja *[MC]*.

## Vía 1 · Figma

- **Herramientas del MCP de Figma:**
  - `get_screenshot` para ver la pieza;
  - `get_design_context` para el CSS de referencia;
  - `get_metadata` para la estructura;
  - `get_variable_defs` para los tokens;
  - `download_assets` para logos e íconos.
- **Los nodos del ui-kit son siete:** colores, tipografías, botones, formularios, cards,
  iconografía y espaciados/grid. Los pide el kickoff y se anotan en la tabla `## UI-kit` del
  `CLAUDE.md`. `nube-skills-section` lee esa tabla y carga **solo los nodos que necesita cada
  sección**, no el ui-kit entero.
- **Si el Figma se actualiza,** hay que usar el nodo que dibuja las filas en cuestión y
  anotarlo como "nodo de referencia actualizado" *[MC]*.
- ⚠️ **No se planifica UI sin el nodo.** En MC, un plan escrito sin boceto adivinó mal (4
  columnas, un CTA inventado) y hubo que reescribirlo contra los nodos reales
  *[MC 2026-09-10]*.

## Vía 2 · Prototipo HTML de Claude Design

GG y VZ no tuvieron Figma. El diseño llegó como prototipos navegables en HTML de Claude Design
(archivos `.dc.html`), publicados en el servidor de prototipos del estudio. Venía junto con un
design system en el mismo formato y con notas para el dev: un `.docx` en VZ; en GG, un README,
un documento de cambios y una guía de estilos. **Las skills del plugin no tienen esta vía**:
`nube-skills-section` espera un nodo de Figma o un boceto que dibuje ella misma. Lo que sigue
es lo que funcionó a mano.

### Cómo se sacan los valores

- ✅ **Los valores están en el script al pie de cada `.dc.html`, no en el CSS**
  *[VZ 2026-09-23]*. Se baja el archivo con `curl` al scratchpad y se busca ahí:
  - los tokens del design system están en `renderVals()` (en VZ: `NEU`, `ACC`, `SEM`,
    `cssVars`, `typeScale`, `spacings`, `anims`, `headerSpecs`);
  - los de cada pieza del boceto tienen nombre propio (`heroH`, `pdpCols`, `railCard`…);
  - desktop y mobile vienen en la misma expresión, `m ? mobile : desktop`, con
    `m = innerWidth < 860`. Hay que buscar la variable, no adivinarla desde el render.
- **En la tabla de bocetos, los nodos de Figma se reemplazan por esos nombres y por las anclas
  del design system** (`…#colores`, `…#botones`). Así la referencia de cada sección se puede
  volver a encontrar.
- **El HTML trae cosas que Figma no da:**
  - duraciones y curvas de las animaciones;
  - disparadores de scroll (en VZ, el header pasa a sólido con `scrollY > 40`);
  - flags de estado.

  Con eso se contestaron varias preguntas de las notas de diseño sin preguntarle a nadie. Por
  ejemplo, que no había mega menú, o que Instagram venía apagada por default
  (`showInstagram: false`) y por lo tanto no había que construirla *[VZ 2026-09-24]*.
- **Los íconos se copian del SVG inline del boceto.** Los logos solo existían en PNG
  *[VZ 2026-09-23]*.
- **Las notas de diseño** de VZ están organizadas en AJUSTAR / CONSTRUIR / VERIFICAR por
  sección. Si no hay pandoc, se leen con `python3` + `zipfile` extrayendo
  `word/document.xml`. Muchos de los VERIFICAR se contestan leyendo el fuente del prototipo
  *[VZ 2026-09-23]*.
- Cómo se mide el boceto contra la preview está en
  [verificación y QA](15-verificacion-y-qa.md).

### Prioridad entre fuentes

- **Cada fuente tiene su rol** *[VZ 2026-09-23]*:
  - un valor que el design system nombra sale del token;
  - lo que no define (el tamaño de un título puntual, mobile, un estado) se mide en el
    boceto;
  - las notas dicen qué entra y qué no.

  Si dos fuentes se contradicen, se abre una anomalía con decisión provisoria (ver abajo).
- **Las contradicciones ya resueltas se escriben como tales, para no volver a discutirlas**
  *[GG]*. En GG:
  - el breakpoint era 860 según el README y 900 según la guía de estilos, y ganó el que
    describe el comportamiento implementado;
  - el orden de la home lo define el prototipo, no el README;
  - un banner que describía el README no existía en el prototipo, así que no se construyó.

### Trampas del prototipo HTML

- ⚠️ **El prototipo tiene sus propios bugs.** En VZ, al `<div>` de una pieza le faltaba el
  cierre, así que su borde caía al final de la columna. Se replicó el efecto visual (una sola
  línea, arriba) y se dejó la otra línea como opción *[VZ 2026-09-24]*.
- 🔥 **Su CSS global también pinta.** El `a:hover` global del boceto de VZ ponía taupe a
  todo link que no fijara su color. Un "Ver todo" había quedado en otro color y hubo que
  corregirlo *[VZ 2026-09-24]*.
- ⚠️ **Sus `<button>` no heredan `font-family` ni `line-height`.** Además, con estilos
  idénticos, Chrome redondea distinto el `line-height: normal` en el boceto y en la preview
  (0,5–1px), incluso en un iframe en blanco. Esa diferencia no se corrige desde el CSS del
  tema *[VZ 2026-09-23]*.
- ⚠️ **Algunas páginas viven en otro archivo, con otra estructura.** En VZ, la página de
  locales usaba otra plantilla y la librería Leaflet, y hubo que replicar la piel de esa
  librería (anomalía A22) *[VZ 2026-09-24]*.
- ⚠️ **Los assets del boceto no son de la tienda.**
  - El video del hero de VZ apuntaba al servidor de prototipos: hay que subirlo a un hosting
    propio antes de publicar.
  - Las fotos que no están en la biblioteca de medios quedan como placeholder.

  *[VZ 2026-09-24]*
- **El copy del boceto es de relleno.** Se reemplaza por copy de la marca, y de paso se
  corrige el registro: "Ingresa" pasa a "Ingresá" *[VZ 2026-09-24]*. Si el boceto promete
  algo que la plataforma no tiene (un aviso de reposición, favoritos), revisar
  [límites](13-limites-y-admin-api.md) antes de construirlo.
- **Las herramientas del boceto no se construyen.** La "Guía de páginas" que se abre con la
  tecla G o el comentador son parte del prototipo, no del sitio *[VZ 2026-09-23]*.
- ⚠️ **Los breakpoints pueden no coincidir entre archivos.** En VZ, la página del design
  system conmuta en 900 y el boceto en 860 (A3). En GG, el README decía 860 y la guía 900.
- **Grises fuera de la paleta:** el design system de VZ tenía ~14, más otros en el boceto. Se
  usa el token más cercano. Si ese gris se repite en más de una pieza, se promueve a token en
  los dos archivos (A6) *[VZ 2026-09-23]*.

## Vía 3 · Sin boceto

- **`nube-skills-section` tiene una "Vía B":** dibuja primero los artboards con la skill
  `design`. Esa skill **no está garantizada** en todas las máquinas: en los transcripts de VZ
  no aparece ni una vez (relevado el 2026-09-30). Antes de contar con ella, hay que confirmar
  que está instalada.
- **Si no hay boceto, la referencia es el pedido escrito o una captura del dev,** y así se
  anota en la tabla de bocetos ("sin nodo propio — mismo componente") *[MC]*.
- **Todo estado que el diseño no dibuja y hubo que inventar se marca como "estado deducido —
  no hay nodo"** *[MC]*.
- **Antes de construir, se confirma qué es lo que el dev nombra.** En MC, el "box shadow
  interno" que pedía el dev era en realidad un degradado (scrim) *[MC]*.
- **Las páginas sin boceto se extrapolan desde el marco y las piezas que ya existen.** En VZ
  así salieron el registro, recuperar y nueva contraseña, los datos de la cuenta y la página
  del carrito. Cada una documenta de qué pieza se extrapoló *[VZ 2026-09-24]*.

## El ui-kit, antes de la primera section

Todo lo demás cuelga del ui-kit: tipografías, colores, botones, espaciados. El orden completo
de la primera semana está en [arranque](01-arranque.md).

### 1 · `.docs/ui-kit.md`

Es el documento de referencia del sistema visual: valores, anomalías y el porqué de cada
decisión. El esqueleto está en [`plantillas/ui-kit.md`](plantillas/ui-kit.md).

- **Qué contiene:**
  - las fuentes y cuál manda;
  - los tokens por familia: colores, tipografía, botones, formularios, card, iconografía,
    espaciados y breakpoints, animaciones;
  - las anomalías;
  - el remapeo de los tokens del base;
  - una sección por pieza o por página con lo medido en vivo y su fecha;
  - dónde vive cada cosa en el código.
- **Las anomalías se documentan una sola vez y se numeran (A1, A2…)** para poder citarlas
  desde el `CLAUDE.md` y desde el código. Entran tres tipos: tokens que se contradicen entre
  sí, valores fuera de paleta y fuentes que no están en el font picker del tema. MC cerró con
  6 anomalías abiertas; VZ llegó a A22.
- **Cada anomalía lleva su decisión provisoria.** Se aplica para poder avanzar, pero queda
  marcada para confirmar con diseño. Cuando se resuelve, se actualiza con la fecha
  *[VZ 2026-09-24]*.
- **Se lee por sección, no entero.** En VZ el archivo llegó a 133 KB.

### 2 · Los tokens en el tema

- **Dónde se declaran los tokens nuevos:** en `layouts/resources/style-tokens.tpl`, en una
  sección propia del kit. Los valores mobile van en el `:root` y los de desktop en el media
  query que le sigue *[VZ 2026-09-23]*. Cada token nuevo lleva su fila en `.docs/ui-kit.md`.
- ✅ **Al final de `style-tokens.tpl` se remapean los tokens de Ipanema a los valores del kit**
  *[VZ 2026-09-23]*: radio, transiciones, márgenes, escala de títulos y colores semánticos.
  Corrige cientos de reglas del base sin tocarlas. Qué tokens y por qué: [CSS](10-css.md),
  sección "Remapear los tokens del base".
- **Los settings globales siguen su cadena:** `config/settings_schema.json` los declara,
  `config/settings_data.json` guarda los valores y `style-tokens.tpl` los convierte en custom
  properties de CSS.
  - Los defaults del diseño van en el schema.
  - `settings_data.json` es la capa del comerciante: escribirlo pasa por el
    [protocolo de sync](03-sync-y-reglas.md).
  - Cómo llegan (o no) los defaults a `settings.*` está en
    [schema y traducciones](06-schema-y-traducciones.md).
- **Los estilos de componente del kit van junto a la regla del base que pisan.** Primero hay
  que fijarse en qué hoja vive esa regla: `style-async.css` carga después que
  `style-critical.css`. El detalle del orden de carga está en [CSS](10-css.md).

### 3 · La skill de proyecto `<cliente>-ui-kit`

Es un patrón que surgió en VZ y vale para cualquier proyecto con un sistema visual propio. El
esqueleto está en [`plantillas/ui-kit-skill/SKILL.md`](plantillas/ui-kit-skill/SKILL.md), y en
el proyecto vive en `.claude/skills/<cliente>-ui-kit/`, no en el plugin.

- **Qué contiene** (la de VZ):
  - las fuentes y cuál manda;
  - las reglas que no se negocian (en VZ eran 8: ningún hex, `ease` ni radio sueltos, una
    sola curva, hover por color y nunca por opacidad, tipografía única, íconos de trazo, una
    cucarda por card, breakpoint 860);
  - los tokens de uso diario;
  - una tabla "necesitás X → usá Y" con los componentes que ya existen, que crece con cada
    página construida;
  - dónde se escribe cada cosa;
  - un checklist de cierre con un `grep` de valores sueltos.
- ✅ **Por qué existe.** Varias sesiones construían páginas en paralelo y cada una tenía que
  usar el kit sin leer los 133 KB de `ui-kit.md`. Su descripción dice "usar ANTES de escribir
  o revisar CSS, markup o defaults de schema", y por eso se cargó sola en las 13 sesiones de
  construcción de VZ *[VZ 2026-09-24]*. `nube-skills-themes`, en cambio, no se cargó sola
  nunca (ver [skills](02-skills.md)).
- ⚠️ **Se desactualiza respecto del doc.** En VZ la skill seguía diciendo:
  - "A1–A19", cuando el doc ya llegaba a A22;
  - "máximo una cucarda por card", cuando la anomalía A5 ya se había actualizado a dos;
  - "sumador de 52", cuando en la ficha era de 54.

  Por eso, al cerrar una anomalía se actualizan las dos cosas en el mismo cambio.

### 4 · Las tablas del `CLAUDE.md`

- **Las tablas `## UI-kit` y `## Bocetos por sección` son contrato.** `nube-skills-section`
  lee `## UI-kit` en cada sección que construye, y `nube-skills-qa` toma su referencia de
  `## Bocetos por sección`. Los encabezados no se renombran.
- **Sin una tabla de bocetos por section, seis semanas después nadie sabe contra qué
  comparar.** Se completa sobre la marcha: cada sección construida anota su fila.
- **La columna "Código" es la que más sirve.** MC anotaba solo los ids de nodo, con la clave
  del archivo de Figma arriba de la tabla. VZ agregó los nombres del prototipo, las anclas y
  una columna con los archivos que implementan cada sección. Esa columna es la que le deja a
  la sesión siguiente encontrar el código sin buscar. La
  [plantilla del `CLAUDE.md`](plantillas/CLAUDE.md) ya la trae.

## Dónde se documenta el diseño

El handoff anterior recomendaba un `CLAUDE.md` que creciera con el proyecto, con una sección
por pieza del tema. En MC llegó a 378 KB y se lo llamó "el activo más valioso". **El contenido
que proponía sigue valiendo. Lo que cambia es dónde se guarda.**

- ⚠️ **El `CLAUDE.md` se inyecta entero en cada sesión.** El de MC terminó en 571 KB y 9.237
  líneas *[MC 2026-09-28]*. VZ mantuvo el suyo en 35 KB (estado, reglas y contratos) y llevó
  el detalle por pieza a `.docs/ui-kit.md`, que tiene una sección por página con lo medido
  *[VZ 2026-09-29]*.
- **La regla:** `.claude/CLAUDE.md` liviano, desde la [plantilla](plantillas/CLAUDE.md), y el
  detalle en `.docs/`. Cómo se arma el día 1 está en [arranque](01-arranque.md).
- **Qué registrar de cada pieza:**
  - la referencia de diseño, desktop y mobile;
  - las decisiones que no son obvias, y por qué;
  - lo que se descartó y por qué no vuelve (es lo que más tiempo ahorra, porque evita
    re-intentar). Lo descartado se marca con 🚫 y no se borra;
  - las divergencias del diseño, explícitas, incluida la única medida que no quedó pixel
    perfect si la hay;
  - lo que se midió en vivo, con fecha;
  - los estados deducidos;
  - de quién fue cada pedido.
- **Las afirmaciones viejas se corrigen en el lugar y con fecha** ("aunque esta nota lo dijo
  hasta el 2026-08-28…"), en vez de borrarlas en silencio *[MC]*. Si un hecho cambia, se
  corrigen todos los lugares que afirmaban lo viejo.
- **La fuente de diseño tiene que quedar accesible desde el repo:** los links, y el bundle si
  lo hay. En GG, el bundle de diseño se referenciaba en todos los documentos pero no estaba en
  el repo, y el dev que tomó el proyecto trabajó solo con los prototipos publicados. Cómo
  dejar el proyecto listo para otro dev está en [arranque](01-arranque.md).
