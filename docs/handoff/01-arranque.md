# Arranque de un proyecto nuevo

Qué decidir antes de escribir una línea, qué pasa el día 1, en qué orden se construye, qué
revisar antes de publicar y qué dejar al cerrar. Es lectura obligatoria, junto con
[skills](02-skills.md) y [sync y reglas](03-sync-y-reglas.md).

## Lo esencial

- **El día 1 es `/nube-skills:kickoff`.** Deja la instalación vinculada y verificada, git con
  `.nuvem` protegido desde el primer commit, este handoff en `.docs/handoff/` y
  `.claude/CLAUDE.md`. VZ arrancó sin él y `.nuvem` terminó en el primer commit.
- **Antes de tocar nada hay cuatro decisiones con el dueño de la tienda:**
  - si la instalación es productiva o borrador, verificado con `theme list`;
  - quién pushea: el dev, con `theme watch` en su terminal; el agente nunca;
  - si se forkea;
  - cuál es la fuente de diseño.
- **Lo que depende del Admin se releva el primer día:** envío con costo, cuotas sin interés,
  menús, cupones, scopes. Sin eso hay piezas que no se dibujan, y parece un bug del tema.
- **Orden de construcción:** ui-kit → header, footer y card de producto → páginas, de la más
  simple a la más compleja. La ficha y el carrito, hacia el final.
- **En sesiones paralelas va una sesión por página,** con un archivo de estado común y un
  encabezado por pieza en los archivos compartidos.
- **Antes de publicar:** dependencias del Admin resueltas, assets del sitio anterior
  re-subidos y el gate de `publish`.
- **Al cerrar,** todo queda en el repo: el diseño, la versión de Node y las advertencias en el
  `CLAUDE.md`. Se entrega una guía para el comerciante, y lo genérico vuelve a nube-skills.

## La máquina del dev (una sola vez)

| Qué | Para qué |
|---|---|
| Plugin **nube-skills**, verificado con `/hooks` | Las skills, el kickoff y el hook del sync gate. Cómo se instala y por qué no se copian las skills al repo: [skills](02-skills.md) |
| **MCP de chrome-devtools** | Medir en la tienda en vez de en una réplica ([verificación y QA](15-verificacion-y-qa.md)) |
| **MCP de Figma**, si el diseño está en Figma | `get_design_context`, `get_metadata` ([diseño y ui-kit](04-diseno-y-ui-kit.md)) |
| CLI **`tiendanube`**, nunca `nuvemshop` | `nuvemshop` manda `region=br` al autorizar. Puede haber dos CLIs en el PATH ([modelo y CLI](05-modelo-y-cli.md)) |
| Node, y la versión del `.nvmrc` si el proyecto lo trae | El CLI declara Node 24.15+ y corre con 22.22 ([modelo y CLI](05-modelo-y-cli.md)) |
| `python3` | Los scripts del plugin (`sync-check.py`, `audit-i18n.py`, `tn-api.py`) son stdlib |
| `gh` | El repo privado del proyecto en la org |

## Antes de escribir una línea: las decisiones con el dueño

1. **¿La instalación es productiva o borrador?** Se verifica con `tiendanube theme list`, no
   con lo que diga un README ni lo que se recuerde. En los dos proyectos donde pasó, nadie se
   enteró:
   - En MC, el "borrador" pasó a productivo a mitad del desarrollo, y la documentación siguió
     diciendo lo contrario *[MC 2026-08-24]*.
   - En GG se publicó el borrador entre dos sesiones, y la segunda le dijo al dev "quedó en el
     borrador" cuando ya era producción *[GG 2026-09-25]*.

   Cómo se compara contra la productiva antes de `publish`: [sync y reglas](03-sync-y-reglas.md).
2. **¿Quién pushea?** El dev, con `theme watch` corriendo en su terminal. Desde el 2026-08-21 la
   regla del equipo es que **el agente nunca corre `theme push`, `theme watch`,
   `theme publish` ni `theme fork`** *[MC 2026-08-21]*. Con watch prendido, cada archivo que se
   guarda se publica, así que los chequeos van **antes** de guardar
   ([sync y reglas](03-sync-y-reglas.md)).
3. **¿Se forkea?** Sin fork, el push deja afuera todo el código del tema. La documentación
   oficial marca el fork como "Próximamente", pero funcionó en los tres proyectos:
   - MC ya estaba forkeado al hacer el kickoff;
   - GG se forkeó al día siguiente *[GG 2026-09-15]*;
   - VZ, el primer día *[VZ 2026-09-23]*.

   El detalle está en [modelo y CLI](05-modelo-y-cli.md).
4. **¿Cuál es la fuente de diseño?** Nodos de Figma (MC), un prototipo HTML de Claude Design (GG
   y VZ) o nada. Las skills asumen Figma; las otras dos vías se trabajan como explica
   [diseño y ui-kit](04-diseno-y-ui-kit.md).
5. **Locales y tiendas hermanas.** Qué locales hacen falta y si el cliente tiene tiendas en otros
   países: en MC eran tres tiendas independientes, con un repo de tema cada una *[MC 2026-09-22]*.
   Ver [multi-país, apps e integraciones](16-multipais-apps-integraciones.md) y, para el locale
   de referencia de cada tienda, [schema y traducciones](06-schema-y-traducciones.md).
6. **¿Hay dominio propio, o lo va a haber?** Cuando la tienda pasa a su dominio, el subdominio
   `*.mitiendanube.com` puede pasar a 410 y la preview cambia de host
   ([modelo y CLI](05-modelo-y-cli.md)). También rompe URLs y assets (ver "Antes de publicar").
7. **Lo que depende del Admin**, antes de medir nada:
   - Un medio de envío con costo. Sin él, `store.has_shipping` da falso y el calculador de envío
     no aparece *[VZ 2026-09-24]*.
   - Cuotas sin interés. Sin ellas, el tema base esconde las cuotas en la card y las cards
     quedan más bajas que el diseño *[VZ 2026-09-24]*.
   - Los menús del Admin. No hay API de menús, así que se cargan a mano.
   - Los cupones que anuncia el diseño.
   - Los scopes del token de cualquier app propia, que quedan congelados al autorizar.

   El detalle de cada uno está en [límites y Admin API](13-limites-y-admin-api.md) y en
   [producto, carrito y búsqueda](09-producto-carrito-busqueda.md).

## Día 1: `/nube-skills:kickoff`

El kickoff solo corre si el dev lo invoca. Crea la instalación o se vincula a una existente, y
deja el proyecto listo para la primera sección. Estos son sus diez pasos y el porqué de cada uno:

| Paso | Qué hace | Por qué |
|---|---|---|
| 1 · Datos | Pide todo en una sola tanda: cliente, carpeta, fuente de diseño, instalación nueva o existente, quién pushea, fork, locales, tiendas hermanas, dominio y repo en GitHub. **No** pide los bocetos de las páginas | Los bocetos se pasan sección a sección, cuando se invoca `nube-skills-section` |
| 2 · Prerrequisitos | `nvm use` si hay `.nvmrc`, y `tiendanube --version`. El `theme authorize` lo corre **el dev** con `! tiendanube theme authorize` | Es interactivo. Si el navegador tiene la sesión de otra tienda, hay que usar incógnito o `--token` ([modelo y CLI](05-modelo-y-cli.md)) |
| 3 · Git antes de bajar nada | `git init -b main`, `.gitignore` con `.nuvem` y `git check-ignore .nuvem` | `.nuvem` es una credencial. VZ arrancó con `/init` y sin `.gitignore`, `.nuvem` entró al primer commit y hubo que reescribir el historial antes de crear el remoto *[VZ 2026-09-23]* |
| 4 · Instalación | `theme list` primero. Después `create` o elegir una, `theme pull --theme-id <ID> -y`, y verificar con el conteo de archivos y `theme diff`. El fork lo corre el dev, y después se repiten el pull y la verificación | Sin `-y` el pull falla en modo no interactivo. Además, el pull puede bajar el tema incompleto y decir `Download completed.` *[MC 2026-08-24]*. El fork puede traer una versión más nueva del base: GG pasó de Ipanema 1 a 1.2.0 *[GG 2026-09-15]* |
| 5 · Copia del handoff | `cp -R` de este handoff a `.docs/handoff/`, verificando que la cantidad de archivos coincida | Es una foto del día: no se edita ([README](README.md)) |
| 6 · `.claude/CLAUDE.md` | Lo arma desde la [plantilla](plantillas/CLAUDE.md), con la tabla de instalaciones, la preview sin login, las reglas, el protocolo de sync y las tablas `## UI-kit` y `## Bocetos por sección` | Va en una carpeta con punto para que no viaje al CDN del tema. Tiene que ser liviano ([diseño y ui-kit](04-diseno-y-ui-kit.md)). Las dos tablas son contrato con las skills |
| 7 · Líneas de base | Cuántos schemas parsean, cuántas claves de traducción faltan y cuántos archivos hay en el servidor | Para que nadie confunda lo heredado con una regresión. El base de VZ ya traía 19 claves faltantes de fábrica *[VZ 2026-09-23]* |
| 8 · Dos commits | Primero el tema tal cual se bajó, con el `.gitignore`; después la documentación | Contra el commit base se compara cada pull que venga: sin git no hay forma de saber qué cambió el comerciante ([sync y reglas](03-sync-y-reglas.md)) |
| 9 · GitHub | El repo privado, solo si `git log --all -- .nuvem` da vacío | Un remoto con la credencial en el historial la expone para siempre |
| 10 · Cierre | `theme current`, `git check-ignore .nuvem`, el conteo de la copia, y el resumen con los próximos pasos | El dev levanta `theme watch` **en su terminal**. Desde ese momento, guardar es publicar |

Después del kickoff, el estado del servidor ya no se lee con un pull sobre la carpeta del
proyecto. Se lee con un pull a un temporal o con `theme diff`
([sync y reglas](03-sync-y-reglas.md)).

### Heredar del proyecto anterior

- **Diffeá el base nuevo contra el pull inicial del proyecto anterior** para saber qué trampas
  siguen valiendo ([modelo y CLI](05-modelo-y-cli.md)). VZ lo hizo contra GG y heredó sus
  trampas medidas *[VZ 2026-09-23]*.
- **No copies las skills desde otro repo.** VZ copió de MC una copia local vieja de
  `nube-skills-themes` *[VZ 2026-09-23]*. Las skills vienen del plugin
  ([skills](02-skills.md)).

## Semana 1: el orden que menos dolió

1. **Ui-kit primero:** los tokens en `layouts/resources/style-tokens.tpl` con el remapeo de los
   tokens del base, `.docs/ui-kit.md` con las anomalías y la skill de proyecto
   `<cliente>-ui-kit` ([diseño y ui-kit](04-diseno-y-ui-kit.md)). Todo lo demás cuelga de ahí.
   En VZ quedó implementado la misma tarde del kickoff *[VZ 2026-09-23]*.
2. **Header, footer y card de producto después.** Son globales, los usa todo el sitio y sus
   settings viven en `config/settings_schema.json`, no en una section.
3. **Recién ahí las páginas,** de la más simple a la más compleja. La ficha de producto y el
   carrito son las que más contrato tienen con la plataforma y las que más caro salen si se
   rompen ([producto, carrito y búsqueda](09-producto-carrito-busqueda.md)).

   Matiz: en VZ la ficha fue la tercera página, en paralelo con la home, sin costo
   documentado *[VZ 2026-09-24]*. El orden es una recomendación, no una regla.

Por cada sección:
- invocar `nube-skills-section` con la referencia de desktop y de mobile ([skills](02-skills.md));
- sincronizar antes de tocar el JSON de la página ([sync y reglas](03-sync-y-reglas.md));
- agregar la fila en `## Bocetos por sección`;
- medir en la preview ([verificación y QA](15-verificacion-y-qa.md)).

### Sesiones paralelas

VZ se construyó con dos sesiones a la vez, una en la home y otra en la ficha *[VZ 2026-09-24]*.
GG, con tres (home, colección y ficha) sobre el mismo árbol *[GG 2026-09-15]*. Lo que funcionó:

- **Una sesión por página** y un **archivo de estado común** que todas leen al arrancar. En GG
  era `ESTADO-REDISEÑO.md`, con este contenido:
  - el arranque obligatorio;
  - el estado del tema;
  - lo que ya está hecho ("no rehacer");
  - los pendientes transversales;
  - las contradicciones ya resueltas ("no volver a discutir");
  - cómo verificar.

  ⚠️ Se desactualiza mientras las sesiones avanzan: el de GG decía "son 10 puntos" cuando ya
  eran 34 *[GG 2026-09-25]*.
- **Handoffs por página** para arrancar cada sesión. Los de GG tenían esta estructura:
  - "antes de nada";
  - el diseño de referencia;
  - el punto de partida medido;
  - qué pide el diseño, con números;
  - el triage;
  - el enganche con las piezas compartidas;
  - las trampas propias;
  - una *definition of done*.

  ⚠️ El de la ficha daba por construir piezas que otra sesión ya había hecho: **re-inventariar
  antes de construir** *[GG 2026-09-18]*.
- **Un encabezado por pieza en los archivos compartidos:** secciones con nombre en el CSS y una
  función por pieza en `store.js`. Es lo que deja editar sin pisarse y después agrupar los
  commits por página. Las reglas de edición y de commits están en
  [sync y reglas](03-sync-y-reglas.md).
- El MCP de chrome-devtools lo toma la primera sesión que lo abre. Qué hacer desde las demás:
  [verificación y QA](15-verificacion-y-qa.md).

## Antes de publicar

### Lo que depende del Admin

El checklist de VZ, que casi todo proyecto repite *[VZ 2026-09-24]*:

- [ ] Existen los cupones que anuncia el diseño.
- [ ] Están creados los menús que usa el tema y elegidos en el editor. Las páginas creadas por
      API aparecen en el menú principal y hay que sacarlas a mano
      ([límites y Admin API](13-limites-y-admin-api.md)).
- [ ] Están cargadas las URLs de las redes.
- [ ] Hay cuotas sin interés configuradas y un medio de envío con costo.
- [ ] Los assets que hoy viven en el servidor de prototipos del estudio (un video del hero, por
      ejemplo) están re-hosteados.
- [ ] La API key de Google Maps está restringida por referrer, con todos los hosts
      ([multi-país, apps e integraciones](16-multipais-apps-integraciones.md)).
- [ ] Los posts del blog tienen título SEO propio.
- [ ] Las páginas están publicadas y cada una tiene asignada su plantilla desde el Admin
      ([plantillas](12-plantillas.md)).
- [ ] Están cargados los productos complementarios y alternativos, y los metacampos que lee
      la ficha.
- [ ] El límite de subida del servicio de archivos del estudio alcanza para los archivos del
      formulario ([multi-país, apps e integraciones](16-multipais-apps-integraciones.md)).
- [ ] El copy de canales de contacto y WhatsApp está confirmado con el cliente.

### Pasar a dominio propio o migrar de plataforma

- 🔥 **Los assets que apuntaban al sitio anterior dan 404 apenas el dominio pasa a Tienda
  Nube.** El sello Data Fiscal de AFIP apuntaba al Magento viejo y medía 0×0. Hay que re-subir
  esos assets a la biblioteca de la tienda *[MC 2026-09-17]*.
- ⚠️ **Las URLs absolutas al subdominio `*.mitiendanube.com` guardadas en
  `config/settings_data.json` se rompen,** porque el subdominio pasa a 410. En los settings van
  rutas relativas *[MC 2026-09-17]*.
- Si el tema se clonó de otra tienda, también arrastra su contenido local: textos legales,
  locales físicos, `@media-lib` de otra biblioteca. Ver
  [multi-país, apps e integraciones](16-multipais-apps-integraciones.md).

### El gate de `publish`

Publicar reemplaza la productiva entera, incluido lo que el comerciante configuró ahí. Antes de
publicar, se compara el borrador contra la productiva y se pide confirmación de todo lo que se
va a perder ([sync y reglas](03-sync-y-reglas.md)).

## Cierre y traspaso

### Qué tiene que quedar en el repo

GG cambió de dev a mitad del proyecto. El traspaso fue el repo (el `CLAUDE.md` y `.docs/`), y lo
que no estaba ahí se perdió *[GG 2026-09-23]*:

- **El diseño completo.** El bundle de diseño se citaba en todos los documentos, pero no estaba
  en el repo ni en la máquina del dev nuevo, que tuvo que trabajar contra los prototipos
  publicados.
- **La versión de Node.** El `.nvmrc` pedía una versión que no estaba instalada, y `nvm use`
  fallaba.
- **Las advertencias, en el `CLAUDE.md` del proyecto,** no solo en el handoff. La de "nunca
  `theme pull` con `watch` prendido" estaba en el handoff y no en el `CLAUDE.md`. El incidente
  pasó cincuenta minutos después de que el dev nuevo levantara el watch
  ([sync y reglas](03-sync-y-reglas.md)).
- **El estado real:** cuál instalación es la productiva, qué quedó a medio hacer y qué está sin
  commitear.

### La guía para el comerciante

GG le entregó al comerciante una guía del Admin y del editor (markdown y HTML), con esta
estructura *[GG 2026-09-25]*:

1. **Las dos pantallas:** el Administrador es el dato, el Editor es la puesta en escena. Una
   regla de oro para saber en cuál se cambia cada cosa.
2. **Un mapa rápido "quiero cambiar…"** → dónde se hace.
3. **Un recorrido por zona** (header, home, colección, ficha, carrito, footer), con las rutas
   exactas del editor y en el vocabulario del comerciante, no en el del tema.
4. **Avisos del estado actual:** qué está en un valor provisorio y qué datos son de ejemplo.
5. **Lo que se administra solo desde el Admin.**
6. **Un checklist de carga pendiente,** ordenado por lo que más se nota en la tienda. Si se
   puede, con datos accionables, por ejemplo la lista de productos a corregir con el link al
   Admin de cada uno.
7. **Tamaños de imagen recomendados.**
8. **Qué no tocar.**
9. **Cómo reportar un problema.**

Se actualiza en el mismo commit que cada feature que cambia algo del editor. ⚠️ Si no, envejece:
la de GG seguía diciendo "hoy en borrador" después de la publicación *[GG 2026-09-25]*.

### Devolver lo aprendido a nube-skills

Todo lo que se aprendió en GG quedó en su `CLAUDE.md` y nunca volvió al handoff. VZ tuvo que ir a
leer ese `CLAUDE.md` para conocer sus trampas *[VZ 2026-09-23]*. Al cerrar un proyecto, o
cuando se mide algo que vale para cualquier tema Ipanema:

- **Lo genérico va a nube-skills,** al capítulo de `docs/handoff/` que le corresponde, con su
  marca y su `[proyecto fecha]`. Así lo recibe el próximo proyecto en su kickoff.
- **Lo propio del cliente queda en su `.claude/CLAUDE.md` y en `.docs/`.** La copia de
  `.docs/handoff/` del proyecto no se edita.
