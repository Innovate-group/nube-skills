# Plantillas de página y plantillas alternativas

Qué plantillas trae el tema, cómo se crea una alternativa y se la hace rutear, el límite de
peso de un JSON de plantilla y el patrón "Draft" para tener colecciones y páginas en borrador.
Qué es un JSON template y quién lo edita está en [Modelo sectionable y CLI](05-modelo-y-cli.md);
cómo tocarlo sin pisar al comerciante, en [Sync y reglas](03-sync-y-reglas.md).

## Lo esencial

- Las plantillas alternativas (`templates/pages/<tipo>.<Nombre visible>.json`) **sí rutean** en
  `category`, `page` y `product`, pero **solo si se asignan desde el Admin**. Crear el archivo no
  alcanza.
- Para saber qué plantilla está ruteando, leé los ids de las sections de `#MainContent`. Comparar
  el contenido no sirve.
- 🔥 **Un JSON de plantilla tiene un límite de peso, entre ~24 KB y 32 KB, y `theme watch` lo
  calla.** Si una plantilla no aparece en el Admin y no hay error, mirá el tamaño del archivo.
- Los textos largos (legales, T&C) no van en un setting: salen del CMS (`page.content`) o de un
  metacampo.
- Los nombres con espacios suben bien desde el disco; con acentos, sin probar: evitalos.
- Una página sin publicar da 404, incluso en la preview, y la API no asigna plantillas.
- No hay borradores de colección ni de página: el patrón "Draft" lo resuelve con una plantilla
  alternativa cuya primera section es un gate. Es UX de borrador, no control de acceso.

## Las plantillas del tema

`templates/pages/` de una instalación Ipanema trae `home`, `product`, `category`, `search`,
`cart`, `contact`, `page`, `blog`, `blog-post`, `404`, `password`, y `account/` (login, register,
orders, order, addresses, address, info, newpass, reset). La 1.2.x suma
`account/subscription-address.json`, para las suscripciones
([Modelo sectionable y CLI](05-modelo-y-cli.md)).

- ⚠️ **`page.json`, la plantilla default de página, puede traer contenido del comerciante.** En
  VZ tenía un borrador suyo y había clones (`page.Contacto.json`). **Toda página sin plantilla
  propia muestra `page.json`**: antes de construir una página nueva, mirá qué hay ahí. [VZ]
- ⚠️ **Una plantilla que baja del servidor puede referenciar una section que tu repo no tiene.**
  Pasó en la tienda de Uruguay de MC: `templates/pages/account/subscription-address.json` pedía
  `main-account-subscription-address`, que vino con el Ipanema 1.2.2 de fábrica y no estaba en el
  fork del que se clonó el repo. [MC]
- ✅ **El `search.json` del tema base usa `page-header` más la barra lateral de filtros,** no el
  layout de la colección. Para que la búsqueda se vea como la colección se suma `search` al
  `enabled_on` de la toolbar de la colección y el título sale de `query`. [MC 2026-09-18]

## Plantillas alternativas

La convención es **`templates/pages/<tipo>.<Nombre visible>.json`**. El nombre del archivo lleva
el nombre que se ve en el editor.

| Tipo | ¿Rutea? | Medido |
|---|---|---|
| `category` | ✅ | [MC 2026-08-21] |
| `page` | ✅ | [MC 2026-08-25] |
| `product` | ✅ | [MC 2026-08-28] |

🔥 **El handoff original afirmó TRES VECES que las de `page` no ruteaban, y era falso.** Las
pruebas eran válidas y la conclusión no: en esos casos **la plantilla no estaba asignada a la
página desde el Admin**. Crear el archivo no alcanza: **hay que asignarla desde el Admin**, y eso
lo hace el comerciante o el dev, no el código. [MC]

**El test para saber qué plantilla está ruteando.** Comparar el contenido no sirve cuando dos
plantillas comparten sections:

```js
[...document.querySelector('#MainContent').children].map(s => s.dataset.sectionId)
// ['heading','page_content','mi_section']  → está renderizando page.json
// ['mi_section']                           → rutea la plantilla propia
```

El test general de "¿la plataforma lee este archivo?": **invertir el `order` de la alternativa**
y ver si el HTML lo refleja.

- ⚠️ **El editor clona la plantilla con TODOS los settings de la default**, incluidos los que ya
  estén configurados. A partir de ahí las dos evolucionan por separado: **si la default cambia,
  la alternativa no se entera** y hay que re-sincronizarla a mano. [MC]
- ⚠️ **Para traer al repo una plantilla que creó el comerciante desde el editor:** `theme pull` a
  un temporal y copiar el archivo ([Sync y reglas](03-sync-y-reglas.md)). [MC]
- **Una alternativa puede usar la misma section que la default y diferir solo en settings.** En
  GG, la ficha "Mosaico" es la section de la ficha default con 6 settings distintos: no hizo
  falta una section nueva. [GG]
- **Con plantillas alternativas, no dupliques la elección con selectores en los settings.** En MC
  convivían plantillas por colección y settings `featured_grid_category_N` que elegían lo mismo:
  se pisaban sin síntoma, y los selectores se sacaron. [MC]
- **N páginas con una sola section.** El centro de ayuda de VZ son 8 páginas, cada una con su
  plantilla (`page.Preguntas Frecuentes.json`, `page.Compras.json`, …) y la misma section. La
  navegación entre ellas es un menú del Admin que la section lee con un setting `menu`
  ([Schema y traducciones](06-schema-y-traducciones.md)). [VZ]
- Para una section que vive en su propia plantilla con un respaldo en `page.json` mientras se
  confirma el ruteo, ver [Patrones](14-patrones.md).

### Nombres de archivo

- ✅ **Los nombres con espacios suben bien desde el disco.** En VZ se subieron más de ocho
  `page.<Nombre>.json` con espacios (`page.Nuestra Historia.json`, `page.Trabaja con
  nosotros.json`), y rutearon una vez asignados en el Admin. [VZ 2026-09-24]
- ⚠️ **Sin acentos en el nombre de una plantilla que subís desde el disco.** Las plantillas
  acentuadas que funcionaron en MC nacieron **en el editor**, nunca se subieron desde el disco, y
  en VZ se siguieron evitando. No está probado que un nombre con tilde suba bien por el CLI y no
  vale arriesgar la vuelta. [MC] [VZ]

### Páginas del CMS y plantillas

- ✅ **Una página sin publicar da 404, incluso en la preview.** Si armás la plantilla de una
  página que el comerciante todavía no publicó, no la vas a poder ver. [VZ 2026-09-24]
- ✅ **El objeto página de la Admin API no tiene campo de plantilla.** Crear la página por API no
  la asigna: la plantilla se elige a mano en el Admin. Y crear páginas por API tiene un efecto
  lateral sobre el menú principal ([Límites y Admin API](13-limites-y-admin-api.md)).
  [VZ 2026-09-24]

## 🔥 El JSON de plantilla tiene un límite de peso, y `theme watch` lo calla

- ✅ Un `templates/pages/page.Terminos y condiciones.json` de **32.425 bytes**, con el texto legal
  metido en un setting, **nunca subió**: el archivo no aparecía en el servidor, el Admin no
  listaba la plantilla y **no hubo ni un error**. Reemplazando el texto por 50 caracteres, el
  archivo quedó en 2.771 bytes y **subió al instante**. [MC 2026-08-25]
- ✅ **Un `home.json` de 23.967 bytes subió por `watch`** y se verificó en el servidor. El límite
  queda entre ~24 KB (sube) y 32 KB (no sube). El valor exacto no se buscó. [GG 2026-09-23]

**Regla práctica: si una plantilla no aparece en el Admin y no hay error, mirá el tamaño del
JSON antes que cualquier otra cosa.**

**La salida correcta** para textos largos no es esquivar el límite: es que el contenido salga del
**CMS** (`page.content`, que el comerciante edita desde Páginas en el Admin) o de un metacampo.
Un texto legal lo tiene que poder editar el cliente sin tocar el tema. En VZ los términos y
condiciones del centro de ayuda son un bloque que dibuja `page.content`. [VZ]

## Conservar el formato de cada JSON

- **Conservá la indentación que ya tiene cada JSON de plantilla.** No es la misma en todos los
  archivos (en GG `product.json` va con indent 1): reindentarlo convierte el diff en un cambio de
  archivo entero y esconde lo que cambió de verdad. [GG]
- El servidor y el editor guardan los JSON minificados, así que un pull los trae en una línea y
  la comparación se hace parseada ([Modelo sectionable y CLI](05-modelo-y-cli.md)).
- Un conflicto de git en un JSON template no se resuelve a mano: son archivos que genera un
  editor ([Sync y reglas](03-sync-y-reglas.md)).

## El patrón "Draft": colecciones y páginas en borrador

Tienda Nube **no tiene borradores de colección ni de página**: desactivarlas da 404 y el equipo no
puede revisarlas en el storefront. MC lo resolvió con plantillas alternativas
(`category.Draft.json`, `page.Draft.json`) cuya **primera section** es un gate que:

- si el visitante es interno (email de un dominio del equipo, o el customizador vía `is_preview`),
  muestra el contenido más un aviso fijo de "esto es un borrador";
- si no, **redirige a la home** (script inline, con un `meta refresh` de respaldo) y el CSS
  esconde las sections hermanas con `#MainContent:has(.mi-gate-lock)` para que no haya flash.

Decisiones que valen para cualquier gate parecido:

- **Va PRIMERA en el `order`,** para que el redirect corra antes de que se parsee el contenido.
- **Sin settings ni presets:** así no aparece en la galería del editor y no hay toggle que la
  apague. Vive solo escrita en el JSON de las plantillas.
- ⚠️ **Es UX de borrador, NO control de acceso:** el HTML de las sections hermanas igual viaja en
  la respuesta (Twig no puede dejar de renderizar una hermana). Nada confidencial ahí.

✅ **Correcciones al gate, medidas después de armarlo:** [MC 2026-09-04]

- el `<script>` del redirect va **antes** que el markup del gate;
- el cartel de respaldo va `hidden`, y se revela con un `<style>` dentro de `<noscript>` o con un
  `setTimeout` de 8 s;
- el `meta refresh` va **dentro del `<noscript>`**: suelto corre también con JS y reinicia la
  navegación;
- queda un blanco corto e inevitable, con el header ya pintado.

Dos efectos laterales:

- ⚠️ **Un gate primero en el `order` rompe "la primera section de la página".** El header
  transparente de MC decidía mirando la primera section, y con el gate adelante dejó de
  funcionar: hubo que saltear el tipo del gate en el JS y sumar una variante del CSS que sube el
  hero por detrás del header. [MC]
- ⚠️ **La preview con `?theme_installation_id=` no es el customizador.** Ahí `is_preview` es
  falso, así que la lógica "interna" del gate pide login aunque estés mirando desde el Admin.
  [MC]
