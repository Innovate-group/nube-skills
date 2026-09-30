# Diseño: el handoff de Ipanema vive en el plugin y el kickoff lo instala

**Fecha:** 2026-09-30 · **Estado:** en revisión

## Contexto y objetivo

El handoff de Ipanema (`HANDOFF-IPANEMA.md`) se generó el 2026-09-03 a partir de María Cher y
de ahí viajó copiado a mano: primero a Garçon García y después, el 2026-09-23, a VZ. Por el
camino aprendió casi nada:

- el de VZ difiere del original en dos párrafos;
- el de Garçon García es idéntico al de María Cher;
- todo lo que se aprendió en Garçon García quedó en su `CLAUDE.md` y nunca volvió al handoff;
- María Cher siguió aprendiendo después del 3/9 (70 commits más, y el `CLAUDE.md` pasó de
  378 KB a 571 KB) sin que el handoff se enterara.

El objetivo tiene dos partes:

1. **Un handoff nuevo** con todo lo aprendido en los tres proyectos. Además de lo técnico,
   cubre **cómo se usan las skills** del plugin en la práctica y **qué hacer primero** en un
   proyecto nuevo.
2. **Que llegue solo a cada proyecto nuevo.** La fuente canónica vive versionada en este
   repo y `/nube-skills:kickoff` la copia al proyecto, sin pasos manuales.

### Qué pidió el dev y qué se supuso

Lo que pidió:

- Analizar María Cher y VZ, y también Garçon García (se sumó durante la charla), y generar
  un handoff con todo lo aprendido. La base es el handoff de VZ, más cómo se usan las skills
  y qué hacer primero en un proyecto nuevo.
- Que viva en nube-skills, versionado.
- No copiarlo a mano: lo copia el kickoff.
- Que sea **exclusivo de proyectos nuevos**: la copia es una foto del día del kickoff, no se
  refresca y no llega a los proyectos en curso.
- Que el kickoff se **alinee** con el handoff, no que solo lo copie.

Lo que se supuso y nadie corrigió:

- Lo leen tanto devs como sesiones de Claude.
- Voz genérica, en español rioplatense, con las marcas del handoff actual.
- Para los proyectos nuevos reemplaza al `HANDOFF-IPANEMA.md`.

### Criterios de éxito

1. Leyendo `README` + `01`–`03` (~60 KB), un dev o una sesión de Claude que arranca un tema
   sabe:
   - qué decidir con el dueño de la tienda;
   - qué pasa el día 1;
   - cómo invocar cada skill y cuáles fallan;
   - el protocolo de sync tal como se practica.
2. Para cada área técnica (Twig, CSS, carrito, CLI…) hay **un archivo que se lee solo**.
3. Del handoff viejo no se pierde nada salvo lo que se corrige, y cada corrección es
   explícita.
4. `/nube-skills:kickoff` deja el proyecto con `.docs/handoff/`, `.claude/CLAUDE.md`, las
   líneas de base y dos commits, sin ninguna copia a mano.
5. En ningún archivo aparecen datos sensibles: tokens, contraseñas, ids de tienda o de
   instalación, emails.

## Hallazgos que definen el diseño

Se relevaron siete fuentes:

- el `CLAUDE.md` de María Cher, 9.237 líneas, en tres partes;
- sus 70 commits posteriores al 3/9;
- sus 33 memorias, los temas hermanos de Chile y Uruguay y las tres apps de gestión;
- todo Garçon García: `CLAUDE.md`, `.docs/`, 37 commits y el incidente del 23/9;
- todo VZ: `CLAUDE.md`, el `ui-kit.md` de 133 KB, 21 commits y sus memorias;
- los transcripts de 54 sesiones, para ver cómo se usaron las skills.

Lo que salió de ahí y define el diseño:

- **Volumen.** Lo nuevo junto con el handoff viejo pasa los 250 KB. En un solo archivo nadie
  lo lee entero, y una sesión de Claude paga ~65k tokens cada vez que lo abre. **Por eso se
  parte en archivos.**
- **Las skills en la práctica** (esto es lo que el `02-skills.md` tiene que contar):
  - `nube-skills-themes` no se cargó ni una vez en 54 sesiones.
  - En los proyectos conviven la copia local (`.agents/skills` + symlinks) y la del plugin.
    Salen duplicadas en el listado y muchas veces sin descripción.
  - Cuando el modelo invoca por su cuenta, elige la copia local (27 de 27 en VZ). En el caso
    de `themes` esa copia es la v1.3.0: no menciona el hook y su `sync-check.py` no tiene
    `--stamp`.
  - 146 de 146 pulls del agente se hicieron a un directorio temporal, no sobre el proyecto
    como prescribe el gate.
  - El hook dio falsos positivos: matchea el texto `theme push` en cualquier comando, resuelve
    por el cwd de la sesión y bloquea archivos nuevos. Y no ve las escrituras por Bash.
- **El kickoff contradice a la práctica.**
  - Escribe el `CLAUDE.md` en la raíz.
  - Pullea sin `-y` y no cuenta archivos.
  - Dice que `theme fork` está "Próximamente".
  - Cierra con "levantá `theme watch`".
  - Solo contempla Figma.
  - VZ no lo usó: arrancó con `/init`, y `.nuvem` terminó en el primer commit.
- **Cómo funcionan los plugins, verificado:**
  - `${CLAUDE_PLUGIN_ROOT}` se expande en el markdown de un comando;
  - `docs/` viaja al caché del plugin (`~/.claude/plugins/cache/nube-skills/nube-skills/<versión>/docs/`);
  - sin subir `version`, `claude plugin update` no vuelve a bajar nada;
  - existe `claude --plugin-dir <ruta>` para probar un plugin local.
- **Las skills no dependen de que el CLAUDE.md esté en la raíz.** Hablan de "el `CLAUDE.md`
  del proyecto", y VZ funciona con `.claude/CLAUDE.md`.

## Decisiones aprobadas

1. El handoff se **parte en archivos** en `docs/handoff/`, en vez de un solo archivo.
2. **La copia la hace el kickoff**, con un paso escrito en `kickoff.md` que usa
   `${CLAUDE_PLUGIN_ROOT}`. No hay script de scaffolding ni hook de `SessionStart`: el hook
   copiaría el handoff también en los proyectos en curso.
3. **El kickoff se alinea con el handoff.** Todo paso que el handoff corrige se corrige
   también en el kickoff.
4. **Sin refresco.** La copia del proyecto es una foto y no existe ningún comando para
   actualizarla.
5. **Versión 1.5.0**, porque cambia el comportamiento del kickoff.
6. **Las skills y el hook no se tocan.** Sus fallas quedan documentadas en `02-skills.md`,
   cada una con la forma de esquivarla, y como pendientes del plugin.
7. **El repo es público, y los nombres de los clientes quedan** (decisión del dev del
   2026-09-30). Aun así no entran tokens, contraseñas, ids de tienda, instalación o app,
   emails ni datos de clientes finales. Tampoco las URLs de servicios internos del estudio
   (el servidor de prototipos, nubefiles), que se describen de forma genérica: el endpoint
   de nubefiles acepta subidas sin token.

---

## Parte 1 · El handoff

### Estructura

```
docs/handoff/
├── README.md                        índice, cómo leer, marcas, los errores más caros, "esto es una foto"
├── 01-arranque.md                   decisiones con el dueño, día 1, orden de trabajo, publicar, cierre y traspaso
├── 02-skills.md                     cada pieza del plugin en la práctica, el hook, problemas conocidos
├── 03-sync-y-reglas.md              protocolo real, watch, incidente del 23/9, reglas del equipo, commits
├── 04-diseno-y-ui-kit.md            Figma / HTML de Claude Design / sin boceto; ui-kit.md + skill de proyecto
├── 05-modelo-y-cli.md               modelo sectionable, estructura, Fork Workflow, CLI
├── 06-schema-y-traducciones.md
├── 07-twig.md
├── 08-plataforma.md                 DOM inyectado, JS privado, formularios y captcha, ?snipplet=, SEO, caché
├── 09-producto-carrito-busqueda.md  variantes, stock, fotos, card, ficha, carrito, búsqueda, filtros, video
├── 10-css.md
├── 11-javascript.md
├── 12-plantillas.md
├── 13-limites-y-admin-api.md        lo que no se puede, lo que sí con una app, trampas de la Admin API
├── 14-patrones.md
├── 15-verificacion-y-qa.md          chequeos locales, medir en la tienda, QA
├── 16-multipais-apps-integraciones.md
└── plantillas/
    ├── CLAUDE.md                    el CLAUDE.md del proyecto: lo usa el kickoff
    ├── ui-kit.md                    esqueleto del documento de ui-kit con anomalías
    └── ui-kit-skill/SKILL.md        esqueleto de la skill de proyecto `<cliente>-ui-kit`
```

`README` + `01`–`03` son la lectura obligatoria; `04`–`16` se consultan por tema. Cada hecho
vive en **un solo** archivo y los demás lo linkean.

### Contenido por archivo

**`README.md`**
- Qué es, para quién y en qué orden se lee, con una tabla-índice: archivo, qué tiene y
  cuándo leerlo.
- Las marcas:
  - ✅ medido, siempre con proyecto y fecha;
  - ⚠️ trampa;
  - 🔥 rompió algo en producción;
  - 🚫 no se puede, o no hay que hacerlo;
  - ❓ medido distinto en dos proyectos, con cómo re-medirlo;
  - sin marca: criterio.
- De dónde sale:
  - María Cher `[MC]`, Garçon García `[GG]` y VZ `[VZ]`, entre agosto y septiembre de 2026;
  - Ipanema 1.0.0, 1.2.0 y 1.2.2;
  - CLI 2.1.0 a 2.3.1.
- **Esto es una foto.** La copia de `.docs/handoff/` del proyecto no se edita. Lo propio del
  proyecto va en `.claude/CLAUDE.md` y `.docs/`; lo genérico se lleva a nube-skills para el
  próximo proyecto (es la lección de Garçon García).
- Lo que no es: la documentación oficial, que el handoff contradice donde se midió otra cosa.
- El apéndice del handoff viejo, "Los errores que más caros salieron", actualizado con los
  nuevos:
  - el incidente del pull con watch;
  - el glob en un comentario CSS;
  - el script que truncó 406 líneas;
  - los endpoints clonados a otro país.

**`01-arranque.md`**
- **Máquina del dev, una vez:**
  - plugin instalado y verificado con `/hooks`;
  - chrome-devtools MCP, y el de Figma si hay Figma;
  - CLI `tiendanube` (nunca `nuvemshop`);
  - Node y `.nvmrc`, `python3` y `gh`.
- **Decisiones con el dueño, antes de escribir nada:**
  - si la instalación es productiva o borrador: verificarlo con `theme list`, no con un
    README (en MC y en GG un borrador pasó a productivo sin aviso);
  - quién pushea;
  - si se forkea;
  - cuál es la fuente de diseño;
  - locales y tiendas hermanas;
  - dominio propio;
  - dependencias del Admin: envío con costo, cuotas sin interés, menús, cupones y scopes del
    token.
- **Día 1 = `/nube-skills:kickoff`.** Qué hace cada paso y por qué. Qué pasa si no se usa: en
  VZ, `.nuvem` terminó en el primer commit.
- **Semana 1, en orden:**
  1. el ui-kit (→ `04`);
  2. lo global: header, footer y card de producto;
  3. las páginas, de la más simple a la más compleja.

  La ficha y el carrito van al final porque son las que más contrato tienen con la
  plataforma. Matiz: en VZ la ficha fue la tercera página, sin costo.
- **Sesiones paralelas:**
  - una sesión por página;
  - encabezados por pieza en los archivos compartidos;
  - un `ESTADO` común para todas (patrón de GG);
  - ediciones puntuales, nunca un Write entero desde una lectura vieja.
- **Antes de publicar:**
  - el checklist de dependencias del Admin (el de VZ);
  - el gate de `publish` (→ `03`).
- **Cierre y traspaso:**
  - qué tiene que quedar en el repo: el diseño completo (GG perdió el bundle), `.nvmrc`, y
    las advertencias escritas en el `CLAUDE.md` y no solo en el handoff;
  - la guía para el comerciante, con la estructura de la de GG;
  - devolver lo aprendido a nube-skills.

**`02-skills.md`**
- **Instalación:**
  - en Claude Code, solo el plugin. **No** instalar las skills en el proyecto con
    `npx skills add`: salen duplicadas, sin descripción, y el modelo elige la copia vieja;
  - `npx skills add` solo para otros agentes (Cursor, Codex), sabiendo que no trae ni hook ni
    kickoff;
  - verificar con `/hooks`.
- **Una tabla por pieza** (kickoff, `themes`, `section`, `qa`, `i18n`, `admin`, hook):
  - para qué sirve;
  - **cómo se dispara en la práctica**, con la frase o el slash. `themes` no se carga sola:
    hay que invocarla con `/nube-skills:nube-skills-themes`, o confiar en que el `CLAUDE.md`
    trae sus reglas;
  - qué necesita del dev;
  - qué escribe;
  - qué requiere: MCPs, la skill `design`.
- **Scripts con ruta sin versión:**
  `ls -d ~/.claude/plugins/cache/nube-skills/nube-skills/*/ | sort -V | tail -1`.
- **El hook:**
  - qué bloquea, cómo se registra un pull (`--stamp`) y qué escapes tiene (son del dev);
  - sus falsos positivos conocidos, cada uno con cómo seguir;
  - lo que no ve: las escrituras por Bash y lo que sube `watch`.
- **El patrón de skill de proyecto `<cliente>-ui-kit`** (VZ): qué contiene y por qué existe.
- **Uso real, en cifras:** qué se usó, cuánto, y qué no se usó nunca.
- **Problemas conocidos del plugin y cómo esquivarlos.** Es la lista de pendientes del
  plugin (ver al final).

**`03-sync-y-reglas.md`**
- **El modo de falla**, con sus casos reales:
  - MC: 4 pérdidas y 2 que casi pasan;
  - GG: el incidente del 23/9;
  - VZ: el gate atrapando cambios del editor.
- **El protocolo tal como se practica:**
  1. `git status`.
  2. ¿Hay `watch` corriendo? `ps` + `lsof` para saber en qué carpeta.
  3. El estado del servidor: pull a un temporal (copiando `.nuvem` y `manifest.json`, con
     `-y`) o `theme diff --detailed`. **Nunca `theme pull` sobre el proyecto con `watch`
     prendido.**
  4. Contar archivos y comparar los JSON parseados.
  5. Traer lo que cambió el comerciante y commitearlo aparte.
  6. `--stamp`.

  Alcance: solo antes de tocar los JSON que se van a modificar; un archivo nuevo no necesita
  gate, pero el hook lo bloquea igual.
- **Editar un JSON del comerciante con `watch` prendido,** en cuatro tiempos (GG).
- **Preferir un fallback en Twig** (`| default`, `??`) antes que escribir archivos del
  comerciante (MC).
- Del handoff viejo: cómo leer el diff, cómo reconciliar un conflicto y el gate antes de
  `publish`, más el borrador que pasa a productivo sin avisar.
- **El incidente del 2026-09-23**, contado entero: qué pasó, cómo se recuperó y qué regla
  quedó.
- **Con `watch`, todo lo que se guarda se publica:**
  - validar antes de guardar (copia → chequeo → `mv`);
  - orden de guardado;
  - las ráfagas hacen que `watch` saltee archivos.
- **Reglas del equipo:**
  - nunca `push`, `watch`, `publish` ni `fork`;
  - ramas solo con permiso;
  - commits solo a pedido, y deshacer también se pide;
  - nunca `git add -A`;
  - no esconder contenido del comerciante, salvo pedido documentado;
  - toda section nueva, con contenido real y visible;
  - los tokens nunca se imprimen ni se guardan en permisos.
- **Commits:**
  - los de sync van aparte;
  - uno por página, con `hash-object` y la base del diff fija;
  - nunca un commit que quede roto por sí solo;
  - el trabajo de otra sesión, rotulado como tal.

**`04-diseno-y-ui-kit.md`**
- **La fuente de diseño es la autoridad.** Tres matices:
  - un nodo de pantalla que dibuja un *estado* no le gana al default del componente;
  - un pedido explícito del dev o del cliente gana, y se documenta como divergencia;
  - los typos del diseño no se copian.
- **Tres vías:**
  - **Figma:** `get_design_context`, `get_metadata` y los nodos del ui-kit.
  - **HTML de Claude Design:** `curl` al scratchpad, `renderVals()`, las expresiones
    `m ? mobile : desktop`, anclas del DS en vez de nodos, y sus trampas.
  - **Sin diseño:** la skill `design`, un brief escrito, o marcar "estado deducido".
- **El ui-kit:**
  - un `ui-kit.md` con anomalías numeradas;
  - tokens en `style-tokens.tpl` más el remapeo de los tokens del base;
  - la skill de proyecto;
  - la tabla de bocetos con columna "Código".

**`05-modelo-y-cli.md`**
- Del handoff viejo: §1 y §2.
- Lo nuevo:
  - `nuvemshop` ≠ `tiendanube`;
  - dos CLIs en el PATH;
  - `theme diff`;
  - la preview sin login y sus límites;
  - leer un archivo remoto por la API;
  - el servidor devuelve JSON minificados, y `{}` pasa a `[]`;
  - el pull borra antes de descargar;
  - el sync por lista blanca (❓);
  - los tokens vencen;
  - `themeId` en `.nuvem`;
  - Ipanema tiene variantes y versiones;
  - `"theme": null`;
  - el subdominio pasa a 410;
  - el hash del CDN rota.

**`06-schema-y-traducciones.md`**
- Del handoff viejo: §4 y §5.
- Lo nuevo:
  - un id nuevo cuando cambia el significado de un setting;
  - los defaults de bloque cambian las instancias existentes;
  - el `header` se lleva los settings de abajo;
  - `video_url` guarda un objeto;
  - `select` en vez de `range` decimal;
  - setting `menu`;
  - `deletable: false`;
  - el locale de referencia se mide por tienda;
  - auditar el registro (voseo/tuteo), no solo que la clave exista.

**`07-twig.md`**
- Del handoff viejo: §6.
- Lo nuevo:
  - un `for` sobre `null` vacía el render;
  - dividir por cero;
  - `in` sobre un string es substring;
  - `product.tags` son objetos;
  - `loop.index` en un `for` filtrado;
  - `option.id` vs `variation.id`;
  - llamar un método sobre un objeto ausente;
  - `media.next_video`;
  - `settings` como nombre local;
  - los `null` de un embed;
  - un include que devuelve un string;
  - la tabla de formas con y sin precedente, ampliada.

**`08-plataforma.md`**
- Del handoff viejo: la parte general de §7.
- Lo nuevo:
  - el acordeón privado del footer;
  - `modal-visible`;
  - los nodos que la plataforma mueve;
  - el contrato del formulario de contacto;
  - el newsletter del footer, que devuelve el mismo `contact`;
  - `role="status"`;
  - `?snipplet=` con `X-Requested-With`;
  - los tramos de URL inventados que dan 200;
  - `x-cache`;
  - los ids que chocan con el sprite;
  - el `<dialog>` de apps de terceros.

**`09-producto-carrito-busqueda.md`**
- Lo que el handoff viejo tenía de producto y carrito en §7 y §9.
- Lo nuevo:
  - variantes, stock y "sin foto" (el placeholder `no-photo`);
  - fotos por color;
  - la card y el carrusel de la card;
  - los hooks de descuento y el comparativo invertido;
  - el contrato del form de producto;
  - el carrito: totales por AJAX, envío gratis, regalo, CTA;
  - búsqueda y filtros;
  - video de producto (Cloudflare Stream).

**`10-css.md`**
- Del handoff viejo: §8.
- Lo nuevo:
  - el rango tablet 768–1023;
  - `p { font-size }` del base;
  - `async` gana a igual especificidad;
  - editar la regla original de `.btn-*`;
  - un solo `transform` por elemento;
  - `aspect-ratio` con `stretch`;
  - container queries;
  - el `grid-column` negativo del header;
  - `display: contents` y los slots;
  - fondo propio en los modales.

**`11-javascript.md`**
- Del handoff viejo: §9 (lo que es de medición va a `15`).
- Lo nuevo:
  - Swiper escribe el ancho inline;
  - `LS.getUrlParams` y el `+`;
  - `mpage`;
  - sanear HTML clonado;
  - `<template>` vs `display: none`;
  - SVG `className`;
  - formato de montos;
  - performance de imágenes y de `paginate`.

**`12-plantillas.md`**
- Del handoff viejo: §10.
- Lo nuevo:
  - el límite de peso de un JSON, entre 24 y 32 KB;
  - los espacios en el nombre, que sí funcionan;
  - una página sin publicar da 404;
  - `page.json` como plantilla heredada;
  - las mejoras del gate Draft;
  - N páginas con una sola section.

**`13-limites-y-admin-api.md`**
- Del handoff viejo: §11, actualizado (wishlist y aviso de stock).
- Lo nuevo de la Admin API:
  - el token del CLI sirve para la Admin API;
  - los scopes quedan congelados en el token;
  - Pages, Blog y menús;
  - `PUT` de tags reemplaza el set completo;
  - `variants` es lento;
  - orden manual de categoría;
  - custom fields.

**`14-patrones.md`**
- Del handoff viejo: §12.
- Lo nuevo:
  - renderizador de media como superconjunto;
  - reemplazar un componente nativo sin esconderlo;
  - un marcador en el texto del comerciante;
  - filtros fail-open;
  - filtrar la lista antes del loop;
  - parámetros aditivos en snippets compartidos;
  - bloque de configuración;
  - link en toda la card;
  - barra de compra flotante;
  - campos del diagnóstico por comentario.

**`15-verificacion-y-qa.md`**
- Del handoff viejo: §13 y lo de medición de §9.
- Lo nuevo:
  - el chequeo de comentarios CSS;
  - diff de líneas después de editar por script;
  - medir en la tienda: MCP primero; si está tomado, headless con perfil propio y user agent
    normal, nunca Chrome visible desde el shell (TCC), y el `IntersectionObserver` en
    headless (❓);
  - Lighthouse contamina los requests;
  - la barra de 52px de la preview;
  - boceto y preview en el mismo navegador;
  - verificar en los dos sentidos;
  - "¿ya está publicado?".

**`16-multipais-apps-integraciones.md`**
- Tiendas por país: un repo por país, portar con `format-patch`, clonar arrastra endpoints,
  configuración y `@media-lib`.
- La arquitectura tema + app de gestión.
- Apps de terceros: stocknube, la neutralización de otra wishlist, Google Maps.
- Subida de archivos (nubefiles).
- CI y deploy de las apps.

**`plantillas/CLAUDE.md`**, en el orden en que la llena el kickoff:
- identificación del cliente;
- ⚠️ por qué vive en `.claude/`;
- tabla de instalaciones (salida de `theme list`);
- preview sin login;
- entorno;
- reglas del equipo;
- protocolo de sync (resumen, linkea a `.docs/handoff/03-sync-y-reglas.md`);
- comandos de verificación con líneas de base;
- `## UI-kit` (Figma, anclas de HTML o "sin ui-kit");
- `## Bocetos por sección`, vacía y con columnas Sección · Desktop · Mobile · Código;
- `## Skills del proyecto`;
- de qué versión del plugin vino el handoff.

Los encabezados `## UI-kit` y `## Bocetos por sección` son contrato con `nube-skills-section`
y `nube-skills-qa`: no se renombran.

**`plantillas/ui-kit.md`** y **`plantillas/ui-kit-skill/SKILL.md`**: esqueletos del patrón de
VZ, con fuentes y cuál manda, tokens, anomalías, componentes existentes, dónde se escribe
cada cosa y un checklist de cierre.

### Adónde va cada sección del handoff viejo

| Handoff viejo | Va a |
|---|---|
| §1 Qué es Ipanema · §2 CLI | `05` |
| §3 Protocolo de sync | `03` |
| §4 Schema · §5 Traducciones | `06` |
| §6 Twig | `07` |
| §7 Lo que inyecta la plataforma | `08` (general) + `09` (producto y carrito) |
| §8 CSS | `10` |
| §9 JavaScript | `11` + `15` (la parte de medir con chrome-devtools) |
| §10 Plantillas | `12` |
| §11 Lo que NO se puede | `13` |
| §12 Patrones | `14` |
| §13 Verificación | `15` |
| §14 Setup recomendado | `01` + `04` + `plantillas/` |
| §15 Día 1 | `01` (y el kickoff) |
| Apéndice: los cinco errores | `README` (ampliado) |

### Reglas editoriales

- **Voz genérica:** "en un tema Ipanema…". Los casos concretos van como ejemplo con su
  fuente entre corchetes, por ejemplo *[MC 2026-09-17]*.
- **Todo ✅ lleva proyecto y fecha.** Sin fecha no es ✅.
- **Cada archivo abre con "Lo esencial"** (5–7 viñetas) y sigue con el detalle agrupado por
  tema. Los snippets de código son cortos y solo cuando la regla es una forma de código.
- **Las cifras que dependen de la instalación** (344 archivos, 7.600 líneas de `store.js`)
  aparecen como ejemplo, nunca como el valor esperado.
- **Sin datos sensibles:**
  - ni tokens, ni contraseñas, ni ids de tienda o de instalación, ni emails;
  - tampoco datos de clientes finales;
  - los dominios de clientes solo si hacen falta para entender el caso.
- **La fuente de verdad son las fuentes.** Un hallazgo que no se puede rastrear hasta un
  archivo, un commit o una memoria de los tres proyectos no entra.
- **Errores de las fuentes que no se copian:**
  - una memoria de MC propone `theme push --force -v` para depurar;
  - un supuesto precedente de `replace({...})` en `breadcrumbs.tpl` de GG, que no existe;
  - el diagnóstico de `.js-ship-free-min` de GG, que es dudoso;
  - "los patches entran limpio", que es falso;
  - "el `es` neutro está en voseo", también falso;
  - "el preview no toma el `settings_data.json` que sube el CLI", que probablemente fue una
    clave escrita fuera de `"settings"`;
  - el bloque `look-products` de shop-the-look, que no existe.

### Resolución de contradicciones

Gana la medición más nueva. Si dos proyectos midieron distinto y no se puede decidir, va con
❓ y con cómo re-medirlo.

| Tema | Handoff viejo | Ahora | Marca |
|---|---|---|---|
| Wishlist | 🚫 | Se puede en el tema: `localStorage` + la card capturada. Multi-dispositivo y métricas necesitan una app propia | ✅ MC |
| Avisame cuando haya stock | 🚫 | Lo cubre la app stocknube, integrada desde el tema | ✅ MC |
| `nuvemshop` / `tiendanube` | idénticos | `nuvemshop` manda `region=br` | ✅ GG · VZ |
| Preview | curl = publicado, necesita sesión | `?preview_theme_installation_id=` responde 200 sin sesión y lee lo guardado; no se propaga a AJAX ni a la paginación | ✅ GG · VZ |
| Gate, paso 3 | `theme pull` en el proyecto | Con `watch`, nunca: pull a temporal o `theme diff`, y después `--stamp` | 🔥 GG |
| Qué sube el push | todo lo que no empieza con punto | 2.3.1 sincroniza por lista blanca de carpetas (leído en el código). La documentación va igual en carpetas con punto | ❓ |
| `product_list` en una section | 🔥 `.products` vacío | GG lo midió funcionando (1.2.0) y MC vacío (1.0.0). Patrón seguro: el bloque | ❓ |
| Defaults del schema | no llegan a `section.settings` | Un `color` sí llegó (VZ). La regla se mantiene para lo que tiene que verse, y se prefiere el fallback en Twig | ❓ |
| CLAUDE.md | que crezca (378 KB, "el activo más valioso") | Liviano en `.claude/` y el detalle en `.docs/`. Los 571 KB de MC se inyectan en cada sesión | criterio |
| Autoridad del diseño | el Figma | La fuente de diseño, con los tres matices de `04` | criterio |
| Márgenes negativos | nunca | La regla se mantiene. Excepción decidida por el dev: el full-bleed de una celda de grilla | ⚠️ MC |
| Swiper `update()` con dos rAF | la solución | No alcanza: quedan 372 ms de glitch. Hay que escribir ancho y posición de forma sincrónica | ✅ MC |
| Límite de peso de un JSON de plantilla | entre 8 y 32 KB | Entre 24 y 32 KB | ✅ GG |
| Nombres de plantilla | sin acentos | Con espacios funcionan desde el disco; con acentos, sin probar | ✅ VZ |
| Factorizar lógica que devuelve un valor | no se puede | Un include puede devolver un string con `set … endset` | ✅ VZ |
| `product.variants` / `default_options` | sin uso | Se usan, con formas acotadas | ✅ MC |
| Medir con Chrome propio | — | MCP primero. Si está tomado: headless con perfil propio y user agent normal. Nunca Chrome visible desde el shell (TCC) | ❓ `IntersectionObserver` en headless |
| Orden de trabajo | ficha y carrito al final | Se mantiene. VZ hizo la ficha tercera sin costo | matiz |
| Slots del nubesdk en el carrito | 7 | MC anotó 4 | ❓ |
| El hook | "bloquea la escritura" | También bloquea `theme push`, pide confirmación en `publish` y resuelve por el cwd de la sesión | actualización |
| Ramas | nunca sin permiso | Se mantiene. GG trabajó en `feature/design` con PR: la regla es de permiso, no de que no haya ramas | aclaración |

---

## Parte 2 · El kickoff

`commands/kickoff.md` sigue siendo una lista de pasos para Claude, con
`disable-model-invocation: true`. Se actualiza la `description` del frontmatter.

1. **Datos, en una sola tanda:**
   - cliente y carpeta;
   - **fuente de diseño:**
     - Figma: los 7 nodos del ui-kit, o `pendiente` los que falten;
     - prototipo HTML: la URL del prototipo y la del design system;
     - sin diseño: los tokens del tema;
   - instalación nueva o existente. El límite es 2 por tienda, **y la legacy cuenta**;
   - **quién pushea.** Por default, el dev, con `theme watch` en su terminal; el agente nunca
     corre `push`, `watch`, `publish` ni `fork`;
   - **si se forkea;**
   - **locales requeridos, tiendas hermanas en otros países y dominio propio;**
   - repo en GitHub, opcional.
2. **Prerrequisitos:**
   - `tiendanube --version`, **nunca `nuvemshop`**;
   - `nvm use` si hay `.nvmrc`. El CLI declara Node 24.15, pero corre con 22.22;
   - **`! tiendanube theme authorize` lo corre el dev.** Si el navegador tiene la sesión de
     otra tienda: incógnito y `--token`.
3. **Git antes de bajar nada:** `git init -b main`, `.gitignore` (`.nuvem`, `.DS_Store`,
   `node_modules/`) y `git check-ignore .nuvem`.
4. **Instalación:**
   - **`theme list` primero, siempre;**
   - `create`, o elegir una existente;
   - **`theme pull --theme-id <ID> -y`;**
   - **verificar que el pull bajó completo:** contar archivos y correr `theme diff`, que no
     tiene que mostrar nada que esté solo en el servidor. Si el CLI no tiene `theme diff`, un
     segundo pull a un temporal y comparar conteos. Se deja escrito que es el único pull sobre
     la carpeta del proyecto, porque todavía no hay `watch`;
   - si se decidió forkear, **lo corre el dev** y se verifica `"forked": true`. Sale el
     "Próximamente".
5. **Copia del handoff:** `mkdir -p .docs && cp -R "${CLAUDE_PLUGIN_ROOT}/docs/handoff" .docs/handoff`.
   Se verifica que la cantidad de archivos sea igual a la del plugin. La copia no se edita.
6. **`.claude/CLAUDE.md` desde `.docs/handoff/plantillas/CLAUDE.md`,** completado con los datos
   del paso 1, la salida de `theme list`, la URL de preview sin login y la versión del plugin
   (se lee de `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json`). Todo marcador de la
   plantilla se reemplaza o se deja como `pendiente`, nunca vacío.
7. **Líneas de base,** anotadas en el `CLAUDE.md`:
   - cuántos schemas parsean;
   - faltantes de `audit-i18n.py`, heredados de Ipanema;
   - cantidad de archivos en el servidor.
8. **Dos commits:**
   1. el tema tal cual se bajó, más el `.gitignore` (así el commit base ya protege `.nuvem`):
      `chore: kickoff <cliente> — tema base ipanema (installation <ID>)`;
   2. la documentación (`.claude/` y `.docs/`): `docs: CLAUDE.md del proyecto y handoff de nube-skills <versión>`.
9. **GitHub**, si se pidió: solo después de confirmar que `git log --all -- .nuvem` da vacío.
10. **Cierre:**
    - `theme current`;
    - `git check-ignore .nuvem`;
    - el conteo de la copia del handoff.

    Y los próximos pasos para el dev:
    - forkear, si quedó pendiente;
    - levantar `theme watch` **en su propia terminal**;
    - primera tarea: el ui-kit (`.docs/handoff/04-diseno-y-ui-kit.md`);
    - leer `.docs/handoff/README.md`.

**Qué sale del kickoff:**
- el template del `CLAUDE.md` escrito dentro de `kickoff.md`, que pasa a la plantilla;
- "levantá `theme watch`" como paso del agente;
- el "Próximamente" del fork;
- el `ls` que buscaba `locales/` y `custom/`.

---

## Parte 3 · Versión, README, CHANGELOG y `validate.py`

- **Versión 1.5.0** en `.claude-plugin/plugin.json`. `marketplace.json` no declara versión.
- **README:**
  - la fila del kickoff en el catálogo;
  - el paso 1 de "Cómo se encadenan";
  - una sección nueva, "El handoff": qué es, dónde vive, que se copia solo en el kickoff y
    que no se refresca en los proyectos en curso.
- **CHANGELOG:** la entrada 1.5.0 con el porqué, en el estilo de las anteriores.
- **`validate.py`**, dos chequeos nuevos (la CI ya lo corre en cada push):
  1. todo link relativo de un `.md` dentro de `docs/handoff/` apunta a un archivo que existe;
  2. toda ruta `${CLAUDE_PLUGIN_ROOT}/…` citada en `commands/*.md` existe en el repo.

## Verificación

**El handoff:**
- un grep de datos sensibles: los ids de tienda e instalación de los tres proyectos,
  contraseñas, `publicApiToken`, cadenas largas en base64 y emails. Tiene que dar cero;
- `validate.py` en verde, con los links incluidos;
- la tabla de "Adónde va cada sección del handoff viejo", recorrida ítem por ítem contra los
  archivos nuevos;
- cada ✅ con proyecto y fecha, y cada ❓ con cómo re-medirlo.

**El kickoff, en seco** (sin tocar ninguna tienda):
- en un directorio temporal se corren los pasos 3, 5, 6 y 8, con `CLAUDE_PLUGIN_ROOT`
  apuntando al repo;
- se verifica:
  - que la cantidad de archivos copiados coincida;
  - que `git check-ignore .nuvem` funcione;
  - que el `CLAUDE.md` quede en `.claude/` sin marcadores sin llenar;
  - que los dos commits tengan lo que dicen;
- con `claude --plugin-dir <repo>`, verificar que `/nube-skills:kickoff` aparece y que
  `${CLAUDE_PLUGIN_ROOT}` se expande. Se aborta antes de cualquier paso que use el CLI.

**En el primer proyecto real,** lo que no se puede probar en seco:
- `authorize`, `list`, `create`, `pull -y` con conteo, `fork` y `theme current`;
- que la copia del handoff salga desde el plugin instalado, no desde un repo local.

## Fuera de alcance

- El hook y las skills (`themes`, `section`, `qa`, `i18n`, `admin`).
- Las copias locales de las skills en los proyectos en curso.
- Refrescar el handoff en los proyectos que ya arrancaron.
- Reemplazar los `HANDOFF-IPANEMA.md` de VZ y de Garçon García.
- Los problemas de seguridad detectados durante el análisis: el token en
  `~/.claude/settings.json` y la contraseña en una memoria de MC. Se le avisaron al dev y no
  se tocan acá.

## Pendientes del plugin

Van documentados en `02-skills.md` como problemas conocidos, cada uno con la forma de
esquivarlo.

- **Hook:**
  - la regex de `theme push` matchea el texto de cualquier comando: mensajes de commit,
    `--help`, `grep`;
  - resuelve por el cwd de la sesión y no por el `cd` del comando;
  - bloquea archivos nuevos;
  - no ve las escrituras por Bash;
  - no reconoce el pull a temporal ni `theme diff` como sync.
- **`nube-skills-themes`:**
  - dice que el fork está "Próximamente";
  - prescribe el pull en el proyecto y no advierte sobre `watch`;
  - documenta `installation_id` en `manifest.json`;
  - no conoce `theme diff`;
  - dice "no implementes plantillas alternativas";
  - dice que `nuvemshop` es idéntico.
- **`nube-skills-section`:** no tiene una vía para el HTML de Claude Design, y asume que el
  agente corre `push` o `watch`.
- **`nube-skills-qa`:** usa `?theme_installation_id=` en vez de la preview sin login.
- **`nube-skills-i18n`:** no audita el registro (voseo/tuteo).
- **`nube-skills-admin`:** no menciona el token de `.nuvem`; `fields=features` da 422.
- **Skills en general:** las copias locales duplicadas y sin descripción; la skill `design`
  no está garantizada en todas las máquinas.

## Riesgos

- **Hechos duplicados entre archivos.** Cada hecho vive en un archivo y los demás lo linkean.
  Se revisa en la pasada final.
- **La copia del proyecto envejece.** Es a propósito (decisión del dev). El README dice
  dónde está la versión canónica.
- **Que un agente redactor mezcle o invente.** Solo se escribe lo que sale de las fuentes; si
  dos fuentes se contradicen, va ❓; y hay una pasada final de revisión con los chequeos de
  arriba.
- **Que `${CLAUDE_PLUGIN_ROOT}` no se expanda.** Está documentado y se prueba con
  `--plugin-dir` antes del release.
