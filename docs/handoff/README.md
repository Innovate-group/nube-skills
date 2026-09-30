# Handoff de Ipanema

Todo lo aprendido construyendo temas **sectionable** de Tienda Nube sobre **Ipanema** con el
**Fork Workflow** del CLI. Sale de tres proyectos reales, en tiendas productivas, entre agosto
y septiembre de 2026:

- **María Cher**, con sus tiendas de Argentina, Chile y Uruguay;
- **Garçon García**;
- **VZ**.

Es para el dev y para las sesiones de Claude que arrancan un tema nuevo o lo retoman.

## Esto es una foto

- **La copia de `.docs/handoff/` de un proyecto** la hizo `/nube-skills:kickoff` el día que el
  proyecto arrancó. **No se edita ni se actualiza.**
- **La versión canónica vive en el plugin nube-skills,** en `docs/handoff/`, y cambia con cada
  release.
- **Lo propio del proyecto** va en `.claude/CLAUDE.md` y en `.docs/`. **Lo genérico** que se
  aprenda vuelve a nube-skills, para el próximo proyecto ([arranque](01-arranque.md), "Cierre
  y traspaso").

## Cómo leerlo

- **Obligatorio antes de escribir la primera línea:** [01 · arranque](01-arranque.md),
  [02 · skills](02-skills.md) y [03 · sync y reglas](03-sync-y-reglas.md).
- **El resto, por tema,** cuando toques esa parte del tema. Cada capítulo abre con "Lo
  esencial" y después va al detalle.
- **Cada hecho vive en un solo capítulo;** los demás lo linkean.

## Índice

| Capítulo | Qué tiene | Cuándo leerlo |
|---|---|---|
| [01 · Arranque](01-arranque.md) | Las decisiones con el dueño, el kickoff paso a paso, el orden de construcción, las sesiones paralelas, qué revisar antes de publicar, el cierre y el traspaso | Antes de empezar un proyecto |
| [02 · Skills](02-skills.md) | Cada pieza del plugin en la práctica: cuándo se dispara, qué pide, qué escribe. El hook del sync gate. Los problemas conocidos y cómo esquivarlos | Antes de empezar, y cada vez que una skill no hace lo esperado |
| [03 · Sync y reglas](03-sync-y-reglas.md) | El protocolo de sync tal como se practica, `theme watch`, el incidente del 2026-09-23, el gate de `publish`, las reglas del equipo y los commits | Antes de la primera escritura de cada tarea |
| [04 · Diseño y ui-kit](04-diseno-y-ui-kit.md) | Figma, HTML de Claude Design o nada. El ui-kit con sus anomalías, la skill de proyecto y la tabla de bocetos | Al arrancar el ui-kit y ante cada sección nueva |
| [05 · Modelo y CLI](05-modelo-y-cli.md) | El modelo sectionable, la estructura, el Fork Workflow, los comandos del CLI y sus mentiras, la preview sin login, las instalaciones | Al instalar, y ante cualquier comportamiento raro del CLI |
| [06 · Schema y traducciones](06-schema-y-traducciones.md) | `{% schema %}`, los `setting_type` reales, los defaults que no llegan, `product_list`, los locales y el registro | Al escribir o cambiar un schema o una clave `t:` |
| [07 · Twig](07-twig.md) | Solo formas con precedente, los errores que vacían una section o dan 500, los comentarios, `default` y `??`, los metacampos, la tabla de filtros | Antes de escribir Twig |
| [08 · Plataforma](08-plataforma.md) | Lo que la plataforma inyecta y mueve en el DOM, el JS privado, los formularios y el captcha, `?snipplet=`, las URLs y la caché | Cuando algo del DOM no se explica mirando el código |
| [09 · Producto, carrito y búsqueda](09-producto-carrito-busqueda.md) | Variantes, stock, fotos, la card, la ficha, el carrito, la búsqueda, los filtros y el video de producto | Antes de tocar la card, la ficha o el carrito |
| [10 · CSS](10-css.md) | El orden de carga, cómo pelear con el tema base, el rango tablet, `transform`, `gap`, container queries | Antes de escribir CSS |
| [11 · JavaScript](11-javascript.md) | `store.js`, la API `LS`, Swiper, los refrescos que la plataforma no hace, la performance | Antes de escribir JS |
| [12 · Plantillas](12-plantillas.md) | Las plantillas alternativas y cómo rutean, el límite de peso del JSON, los nombres de archivo, el patrón Draft | Al crear una página o una plantilla alternativa |
| [13 · Límites y Admin API](13-limites-y-admin-api.md) | Lo que no se puede, lo que sí con una app, y las trampas de la Admin API | Antes de estimar una feature, y antes de escribir por API |
| [14 · Patrones](14-patrones.md) | Los patrones que conviene copiar: el diagnóstico por comentario, la visibilidad, el renderizador de media, los filtros fail-open y más | Al diseñar una pieza nueva |
| [15 · Verificación y QA](15-verificacion-y-qa.md) | Los chequeos locales antes de guardar, cómo medir en la tienda y el QA contra el diseño | Antes de guardar, y antes de entregar |
| [16 · Multi-país, apps e integraciones](16-multipais-apps-integraciones.md) | Tiendas en varios países, la app de gestión, las apps de terceros, el servicio de archivos, la CI de las apps | Si el cliente tiene más de una tienda, una app propia o apps de terceros |
| [Plantilla · `CLAUDE.md`](plantillas/CLAUDE.md) | El `.claude/CLAUDE.md` del proyecto, con marcadores `«…»` | La completa el kickoff |
| [Plantilla · `ui-kit.md`](plantillas/ui-kit.md) | El esqueleto de `.docs/ui-kit.md`: fuentes, anomalías, tokens, remapeo del base | Al documentar el ui-kit |
| [Plantilla · skill de ui-kit](plantillas/ui-kit-skill/SKILL.md) | El esqueleto de la skill de proyecto `<cliente>-ui-kit` | Al terminar el ui-kit, para `.claude/skills/<cliente>-ui-kit/` |

## Marcas y fuentes

| Marca | Significa |
|---|---|
| ✅ | Medido contra la tienda o contra el código de la plataforma. Siempre lleva proyecto y fecha |
| ⚠️ | Una trampa que ya costó tiempo |
| 🔥 | Rompió algo en producción |
| 🚫 | No se puede, o no hay que hacerlo |
| ❓ | Medido distinto en dos proyectos. Siempre lleva cómo re-medirlo |
| (sin marca) | Criterio |

**Las etiquetas de fuente dicen de qué proyecto sale cada cosa y cuándo se midió:**
- `[MC 2026-09-17]` es María Cher (Argentina, y sus tiendas de Chile y Uruguay cuando se
  aclara).
- `[GG …]` es Garçon García y `[VZ …]` es VZ.
- **`[MC, antes de 2026-09-03]`** marca lo que viene del handoff original sin una fecha propia. Quiere
  decir "medido en María Cher hasta el 2026-09-03", que es la fecha en que se generó ese
  handoff.

**Versiones de lo medido:**
- Ipanema, de la 1.0.0 a la 1.2.2, que varía según la tienda ([modelo y CLI](05-modelo-y-cli.md));
- `@tiendanube/cli`, de la 2.1.0 a la 2.3.1.

Si tu instalación es de otra versión, medí antes de confiar en una cifra.

## Lo que no es

- **No es la documentación oficial de Tienda Nube.** Varias cosas de acá la contradicen,
  porque se midieron en vivo. Cuando pasa, está dicho explícitamente.
- **No es un curso de Twig, CSS ni JS.** Solo trae lo que en Tienda Nube funciona distinto de lo
  esperado.
- **No reemplaza al `CLAUDE.md` del proyecto,** que guarda lo propio de cada cliente.

## Los errores que más caros salieron

| # | Qué | Costo | Dónde |
|---|---|---|---|
| 1 | Un `{# #}` adentro de un `{% %}`, en un snippet del layout y con `watch` corriendo *[MC 2026-08-24]* | 500 en toda la tienda, publicado al instante. El chequeo local dio verde | [Twig](07-twig.md) |
| 2 | Un comentario de Twig anidado en la cabecera de un snippet *[MC, antes de 2026-09-03]* | Dos páginas de cuenta renderizaban NADA, sin ningún error visible. Seis ciclos de bisección | [Twig](07-twig.md) |
| 3 | Un `push` con un `templates/*.json` viejo *[MC, antes de 2026-09-03]* | Cuatro pérdidas de configuración: banners de la home, URLs del header, un logo y un bloque del footer. Se recuperaron por suerte | [Sync y reglas](03-sync-y-reglas.md) |
| 4 | `attribute()` sobre `product.metafields` *[MC, antes de 2026-09-03]* | La section desaparecía entera del DOM. Cuatro ciclos de bisección, con un síntoma idéntico al de "no hay datos" | [Twig](07-twig.md) |
| 5 | Volcados de diagnóstico dentro de comentarios HTML, en la ficha productiva *[MC, antes de 2026-09-03]* | Rompió la ficha: un comentario HTML no evita que se evalúe la expresión | [Twig](07-twig.md), [patrones](14-patrones.md) |
| 6 | Un `theme pull` con `theme watch` prendido en la misma carpeta *[GG 2026-09-23]* | El CLI borró los archivos locales, el GET falló y watch replicó los borrados. El borrador dio 500 en todas las páginas y 93 archivos no volvieron a subir | [Sync y reglas](03-sync-y-reglas.md) |
| 7 | Una ruta con `**/` dentro de un comentario CSS *[MC 2026-09-15]* | La plataforma no pudo construir la hoja: el `<link>` salió con `href=""` y se cayeron todos los estilos async. El chequeo de llaves dio OK | [Verificación y QA](15-verificacion-y-qa.md) |
| 8 | Una edición por script que truncó 406 líneas de CSS *[MC 2026-09]* | La verificación "por números" se había hecho antes de la edición, así que se entregó una página rota | [Verificación y QA](15-verificacion-y-qa.md) |
| 9 | Clonar el tema a otro país con los endpoints de la app de la tienda original *[MC 2026-09-22]* | Un host equivocado no falla: escribe datos de clientes en la tienda de otro país | [Multi-país, apps e integraciones](16-multipais-apps-integraciones.md) |

Los nueve tienen la misma forma: **el sistema falla en silencio.** No hay error en la consola
ni en el push, y en varios de los casos el chequeo local dio verde. La única defensa real es
no estrenar formas sin precedente, correr los chequeos que ven cada cosa **antes de guardar** y
**medir en la tienda**.
