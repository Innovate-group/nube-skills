# Lo que la plataforma inyecta y hace por su cuenta

Tienda Nube no solo renderiza tu Twig. Le agrega wrappers y atributos, deja puntos de
extensión en todas partes, mueve nodos al abrir modales, corre JS privado que escribe estilos
inline y reconoce formularios por listas blancas de selectores. Nada de esto está en la
documentación, y explica la mitad de los bugs raros. Este capítulo cubre lo general. Lo
específico de variantes, card, ficha, carrito y búsqueda está en
[Producto, carrito y búsqueda](09-producto-carrito-busqueda.md).

## Lo esencial

- El wrapper `.ns-section` y lo que emite `block_attributes` son contrato de la plataforma.
  Desde JS se engancha por `data-section-type` y `data-block-id`, y el raíz de un bloque nunca
  lleva un `id` propio.
- Hay slots `js-nubesdk-slot` vacíos en todas partes, y cada uno reclama su `gap`. La regla
  global es `.js-nubesdk-slot:empty { display: none }`.
- La plataforma mueve los modales a `<body>` al abrirlos. El CSS del contenido de un modal va
  colgado de una clase del propio panel, nunca de su contenedor original.
- Los formularios se reconocen por listas blancas de selectores y por piezas fijas
  (`#contact-form`, `/winnie-pooh`). Un `data-store` inventado deja el form sin captcha, y el
  backend lo rechaza siempre.
- El JS privado maneja componentes con clases `*-private` y escribe estilos inline. Eso no se
  gana con especificidad: se diseña alrededor.
- `?snipplet=` renderiza un snippet suelto con `settings` vacío, y responde distinto según el
  header `X-Requested-With`.
- La plataforma responde 200 a URLs inventadas y sirve HTML cacheado ignorando el query. Antes
  de dar un render por roto, mirá la URL y el header `x-cache`.

## El wrapper de cada section

```html
<section class="ns-section <lo que declare el class del schema>"
         id="ns-section-<section-id>"
         data-section-type="<tipo>"
         data-section-id="<id>">
```

- ✅ **El `class` del schema llega al wrapper aunque incluya el token `section`**
  [MC 2026-08-21]. Esto corrige lo que el equipo creía antes: las clases `.section-*` de las
  sections del tema base **están vivas**. No las trates como muertas sin mirar el DOM. Para una
  section nueva conviene un `class` de un solo token: no existe ninguna regla `.section {}` en
  el tema [MC].
- ⚠️ **`m-0` en el `class` del schema es una trampa.** Es `margin: 0 !important` y le gana a
  cualquier margen que el tema quiera ponerle al wrapper. Rompió el header transparente durante
  días, porque mataba el margen negativo con el que el hero sube por detrás del header
  [MC, antes de 2026-09-03].
- **Desde JS, `[data-section-type="<tipo>"]`.** Es el contrato explícito de la plataforma y no
  depende de lo que declare cada schema.
- **"La primera section de la página":** desde CSS, `#MainContent > .ns-section:first-child`.
  ⚠️ `body:has(.marca)` aplica esté donde esté la section; si una regla vale solo para la
  primera, va `#MainContent > .ns-section:first-child .marca` [MC].
- ⚠️ **Arriba del header hay dos elementos:** una `section.section-announcement-bar` de 0px y
  después el `div.adbar` real. `querySelector('[data-section-type]')` agarra el vacío [MC].
- ⚠️ **La home ya trae un `<h1>` oculto en `blocks/header-logo.tpl`.** Los títulos del hero van
  en `<h2>` [VZ]. Cómo mudar el `<h1>` de `page-header` a otra section está en
  [Patrones](14-patrones.md).
- Una section que no dibuja nada deja igual su wrapper `.ns-section`, en alto 0. Si desaparece
  hasta el wrapper, es un error fatal de Twig (ver [Twig](07-twig.md)).

## `block_attributes` ya emite un `id`

🔥 `{{ block | block_attributes }}` emite `id="ns-block-<block.id>"`, `data-block-id` y
`data-block-type`. **No se le puede agregar un `id` propio al mismo elemento**: el navegador se
queda con el primero y descarta el resto [MC, antes de 2026-09-03].

Costó un bug entero. Un panel de pestañas con `block_attributes` **y** un `id` propio salía
con el id de la plataforma, mientras el `aria-controls` del botón apuntaba al inventado. Al
cambiar de pestaña no se mostraba ninguna, con los `aria-selected` cambiando bien y sin error
en consola.

Para referenciar el raíz de un bloque: desde JS, **`data-block-id`**; desde `aria-controls`,
que necesita un id real, **`ns-block-<block.id>`**.

## Los slots del nubesdk

- ⚠️ **La plataforma deja un `<div class="js-nubesdk-slot">` por cada punto de extensión**,
  tenga o no una app enganchada. Hay 10 en el formulario de producto, 4 en la card y 4 en el
  registro; en el carrito los conteos no coinciden (ver
  [Producto, carrito y búsqueda](09-producto-carrito-busqueda.md)). Aunque midan 0 de alto,
  **cada uno es un hijo más**: en un flex o un grid con `gap` reclama su separación completa.
  En la columna de info de la ficha eran 64px de aire fantasma que no se explican mirando el
  CSS [MC, antes de 2026-09-03].
- La solución global:

  ```css
  .js-nubesdk-slot:empty { display: none }
  ```

  ⚠️ El `:empty` no es decorativo: oculta el slot **solo mientras está vacío**, así que si una
  app inyecta contenido, vuelve a aparecer solo. Con un `display: none` a secas se rompe
  cualquier app instalada.
- ⚠️ **En el carrito `:empty` no matchea**, porque ahí los slots vienen con saltos de línea
  adentro. Va `:not(:has(*))` [MC, antes de 2026-09-03].
- 🚫 **`:not(:has(*))` no detecta un wrapper de section vacío.** La plataforma le inyecta sus
  slots a **todos** los wrappers, dibuje o no la section, así que un wrapper "vacío" tiene 2
  hijos elemento. Para distinguirlo hay que cruzar el `data-section-type` con una clase
  marcadora que la section emita solo cuando dibuja de verdad [MC, antes de 2026-09-03].
- ⚠️ **Los slots ya traen `transform: translateX(-50%)` inline desde el servidor.** Cualquier
  saneado de HTML que busque transforms los va a encontrar [MC 2026-09-10]. Pasar el
  contenedor a `display: contents` no ahorra el gap de los slots, lo multiplica (ver
  [CSS](10-css.md)).

## La plataforma mueve nodos y crea capas

- ⚠️ **Al abrir un modal, lo mueve a `<body>`.** Su contenedor original deja de ser su ancestro
  justo cuando el panel se ve, y cualquier regla CSS colgada de ese contenedor queda muerta.
  Costó medio día de "el CSS está bien y no aplica". El estilo del contenido de un modal va
  colgado de una clase **del propio panel**, que viaja con él [MC, antes de 2026-09-03].
- **Ídem para los paneles que el tema mueve a `<body>`,** como el quick add de la card en
  mobile: los sliders tienen `transform` en el wrapper, y un `position: fixed` adentro se
  anclaría al slider en vez de a la ventana [MC].
- ⚠️ **Los paneles de nivel 2 de un modal también se mudan a `<body>` por su cuenta.** Una
  custom property escrita inline en el modal no les llega: las constantes que comparten van en
  `:root` [MC 2026-09-09].
- **`modal-visible` lo pone la plataforma en el panel abierto y también en `<body>`.** Sirve de
  gancho sin JS: `body.modal-visible` alcanza a todos los modales [MC].
- 🔥 **Ningún overlay puede vivir dentro del header** [GG 2026-09-18]. El header tiene
  `z-index: 1000`, que crea un contexto de apilado; un ancestro tiene `transform`; e
  `initStickyHeader` observa `<html>`. El overlay se muda a `<body>` en su init, y nada escribe
  clases en `<html>`.
- 🔥 **Un `<dialog>` del top layer no se renderiza si un ancestro está en `display: none`.**
  `open` da `true` y el tamaño, 0×0. Medido: abre en 0×0 contra 500×273 corrido fuera de
  pantalla ✅ [MC 2026-09-11]. Para esconder el wrapper de un widget de tercero que abre un
  `<dialog>`, corrélo fuera de pantalla (`position: absolute; left: -9999px`). No sirve el
  sr-only, porque su `white-space: nowrap` se hereda y el `clip` recorta, y tampoco
  `pointer-events: none`, que también se hereda.
- ⚠️ **Las apps de terceros inyectan su UI por JS, después de la carga.** Su contenedor no
  viene en el HTML del servidor. Se lo espera con un `MutationObserver` que se desconecta al
  encontrarlo y marca, por ejemplo, `<html data-stock-notify="ready">` [MC 2026-09-11]. Cómo
  integrar o neutralizar una app está en
  [Multi-país, apps e integraciones](16-multipais-apps-integraciones.md).

## JS privado: clases `*-private` y estilos inline

El bundle de la plataforma (`linkedstore-v2`) maneja componentes a los que el tema solo pone
clases. No se leen en el código del tema: hay que saber que existen.

- 🔥 **El acordeón del footer es JS privado (`.js-accordion-private-content`)** ✅
  [MC 2026-09-11]. Debajo de 768px escribe `style="display:none"` inline unos 2ms después del
  `DOMContentLoaded`, **una sola vez**, y no lo repite al redimensionar. Su toggle lee el DOM y
  no guarda estado propio. Para que arranque abierto: un `MutationObserver` de una sola vez
  más un timeout de 3s. Nada de `!important`, que mataría el toggle.
- **`js-apply-filter-private`** aplica el filtro y navega apenas se tilda [MC].
- **`js-modal-open-private` + `data-target="#installments-modal"`** está sobre
  `.js-product-payments-container`, así que la línea de cuotas entera abre el modal aunque le
  saques el `<a>` [MC].
- **Sin un `js-modal-close-private`, un modal no se cierra** [MC].
- ⚠️ **`js-hide-footer-while-scrolling` deja el pie en `display: none`** mientras el scroll
  infinito de la colección carga. El pie se mide en una ficha o en una landing, no en una
  colección [MC].

**Estilos inline que escribe el JS de la plataforma.** Contra ellos no hay especificidad que
valga (la regla de CSS está en [CSS](10-css.md)); el detalle de cada uno, en
[Producto, carrito y búsqueda](09-producto-carrito-busqueda.md):

- el cupón del carrito (`.js-coupon-body`);
- la barra de envío gratis y la `transition` de `LS.freeShippingProgress`;
- el `padding-bottom` de relación de aspecto que emite `item-image.tpl`;
- el badge "sin stock" de la card y `#btn-installments`;
- `.js-empty-ajax-cart`;
- los bullets `-dynamic` del slider de la card;
- el placeholder "Agregando…" del botón de compra.

⚠️ **La plataforma escribe `display: none` de dos formas, con espacio y sin espacio.** Un
selector `[style*=…]` tiene que contemplar las dos [MC].

Cuando el JS de la plataforma muestra algo con `display` inline, suele ser mejor **no
renderizarlo** que esconderlo por CSS, confirmando antes que ese JS tenga guarda de `null`
(`findOne` + `if (el)`). El patrón está en [Patrones](14-patrones.md).

## Formularios

### El captcha se engancha por lista blanca de selectores

🔥 `GoogleRecaptchaWidget` y `AjaxContactForm` no miran el formulario: matchean contra listas
de selectores hardcodeadas en el bundle. **Un `data-store` inventado deja el form sin captcha y
el backend rechaza el alta siempre**, con un mensaje que parece de validación ("Necesitamos tu
email…") [MC, antes de 2026-09-03].

Las listas, leídas del bundle `linkedstore-v2`:

| Formulario | Selectores que la plataforma reconoce |
|---|---|
| Popup de newsletter | `form[id='news-popup-form']`, `#news-popup-form-container form`, `form.js-news-form`, `#newsletter-popup form`, `form[data-store='newsletter-form-popup']` |
| Newsletter genérico | `form[data-store='newsletter-form']`, `form[data-store='home-newsletter-form']`, `.js-newsletter form`, `.newsletter-footer form`, `.js-newsletter-footer form`, `#newsletter form` |
| Contacto | `form[data-store='contact-form']`, `form[id='contact-form']`, `form.contact-form`, `form.formulario_contacto`, `#contact-form form`, `.contacto form` |
| Login / registro | `data-store="account-login"` / `"account-register"` |
| Nueva contraseña | `#resetpass-form`: `ResetPassForm` le monta el captcha [VZ] |

### Dónde va el widget y cuánto ocupa

- ⚠️ **La plataforma decide dónde va el widget.** Borra el `<div class="g-recaptcha">` de tu
  plantilla y crea el suyo con `submit.parentNode.insertBefore(widget, submit)`, o sea siempre
  adentro del contenedor del botón de enviar. Hay que contemplarlo en el layout:
  `flex-wrap: wrap` más `flex: 0 0 100%; order: -1` sobre `.g-recaptcha` funciona bien
  [MC, antes de 2026-09-03].
- ⚠️ **El reCAPTCHA mide 304px fijos** y desborda cualquier contenedor más angosto [MC].
- ✅ **El reCAPTCHA v2 del `ContactForm` deja el botón deshabilitado hasta resolverlo y suma
  unos 92px arriba del submit** (78 más el gap) [VZ 2026-09-24]. Pasa en todo form que reuse
  `#contact-form` o `data-store="contact-form"`, como un seguimiento de pedido o un envío de
  CV: ese estado se diseña.
- ⚠️ **reCAPTCHA Enterprise por encima de la cuota gratuita hace fallar intentos**, y en MC
  nunca se pudo probar un envío exitoso. Es configuración de la tienda, no del tema [MC].

### El formulario de contacto

- ⚠️ **El `ContactForm` hace `preventDefault()`, resuelve el captcha y después llama a
  `form.submit()` nativo**, que ya no vuelve a disparar el evento. No se puede combinar con
  nada que necesite ver el submit, y un listener propio de `submit` corre **antes**: su
  modificación del value sí viaja [MC, antes de 2026-09-03].
- **Piezas fijas del contrato** [MC]: `#contact-form`, `action="/winnie-pooh"`,
  `js-winnie-pooh-form`, el honeypot y `name="contact"` en el submit.
  - La ruta de una **página** también procesa el POST.
  - Un `action` propio se respeta si no es `/winnie-pooh`, y el captcha se inyecta igual por
    `data-store`.
  - Para cancelaciones (botón de arrepentimiento): `is_order_cancellation`,
    `?order_cancellation_without_id=true` y el hidden `type=order_cancellation`.
- **Los campos que el endpoint no acepta van sin `name`**, así el navegador no los envía. Un
  listener de `submit` los rotula y los concatena al `message`; tiene que ser idempotente,
  porque el submit se repite si falla el captcha [MC]. En VZ lo extra (motivo, puesto, URL de
  un CV) viaja dentro de `message` con un hidden que toma el `name="message"`, y la
  confirmación usa `sessionStorage`, porque la plataforma no devuelve lo enviado [VZ].
- ⚠️ **Para frenar el submit** (un archivo obligatorio, una validación propia), el listener va
  **en captura** sobre `document`, con `stopPropagation`: el `ContactForm` escucha el submit
  por su cuenta. Un `required` en un file oculto traba el submit con "An invalid form control
  is not focusable", y un `type=hidden` queda excluido de la validación [MC]. La validación en
  captura está en [JavaScript](11-javascript.md).
- La ruta de contacto no acepta archivos. Qué campos sí acepta y la salida para adjuntos están
  en [Límites y Admin API](13-limites-y-admin-api.md).

### El newsletter

- 🔥 **El newsletter del footer postea a la URL actual y vuelve con el MISMO objeto
  `contact`.** El `{% if contact %}` pelado del tema base hace que el formulario de contacto de
  esa página dibuje su propio aviso. La guarda es `contact.type != 'newsletter'` [MC].
- **`ajax_submit: true` es solo del popup**; el newsletter del footer recarga la página [MC].
- ✅ **El opt-in al newsletter no viaja en el POST del registro**: no hay `accepts_marketing`.
  Hacen falta dos POST [MC 2026-08-24]:
  1. un form hermano dentro de `.js-newsletter` (la única entrada libre de
     `NEWSLETTER_FORM_SELECTORS`), apuntado a un iframe oculto;
  2. recién después, el registro con `requestSubmit()` y no `submit()`, con un timeout de 2,5s
     para que el alta no quede rehén del primero.

### La cuenta

- ⚠️ **Detalles del login y el registro** [MC]:
  - con la validación de email obligatoria, después del alta no hay sesión;
  - los custom fields de `customers` no se renderizan en el formulario de registro;
  - el backend valida la confirmación de contraseña (`result.errors.password == 'confirmation'`);
  - con el login sin contraseña (passwordless) prendido, al form clásico se llega con
    `?fallback=1`;
  - estos hooks del login son contrato: `js-account-input`, `js-password-toggle`,
    `js-recaptcha-button`, `js-form-spinner`, `js-account-validation-*`,
    `js-too-many-attempts`, `js-login-general-error`.
- ✅ **Los ids de los campos pueden chocar con los `<symbol>` del sprite de íconos** (`email`,
  `phone`): el `<label for>` termina apuntando al ícono. Usá ids propios, como `login-email`
  [VZ 2026-09-24].
- ⚠️ **Un `role="status"` que ya está en el HTML al cargar no se anuncia.** Hay que mover el
  foco (`tabindex="-1"`, `focus({ preventScroll: true })` y después `scrollIntoView`) al
  primero **visible**, el que tiene `offsetParent !== null` [MC]. Ojo: en un elemento
  `position: fixed`, `offsetParent` es siempre `null` (ver [JavaScript](11-javascript.md)).
- Qué no existe (login social, `extra[key]` en el registro) está en
  [Límites y Admin API](13-limites-y-admin-api.md).

### El popup promocional

- ⚠️ **El popup no sale dentro de ningún iframe** (`window.parent !== window`), o sea ni en el
  customizador ni en el Brand Editor, y tampoco en `template == 'password'` [MC].
- ⚠️ **`AjaxContactForm` corta si la cookie `newsletter-popup` está marcada** [MC].
- ⚠️ **`.modal form` estira cualquier form de un modal a `height: 100%`** [MC].
- La trampa de la cookie de `LS.homePopup`, que se escribe al cargar y no al mostrar, está en
  [JavaScript](11-javascript.md).

## `?snipplet=`: renderizar un snippet suelto

`?snipplet=<archivo>.tpl` renderiza un snippet suelto; así funciona el buscador AJAX.

- ⚠️ **Ese render corre con `settings` VACÍO**: ni las claves propias ni las del tema base. Todo
  lo que dependa de un setting hay que resolverlo del lado que sí lo tiene y pasarlo por CSS o
  por atributos [MC, antes de 2026-09-03]. Consecuencias medidas [MC]:
  - las cuotas no salen en el buscador desplegable;
  - `?? true` gana siempre ahí, así que un toggle no se puede apagar en ese render;
  - un bloque que hay que refrescar no se puede pedir por `?snipplet=`: se pide la página
    entera (ver [JavaScript](11-javascript.md));
  - las cards del buscador pierden la relación de aspecto (ver
    [Producto, carrito y búsqueda](09-producto-carrito-busqueda.md)).
- 🔥 **Solo responde como snippet con el header `X-Requested-With: XMLHttpRequest`** ✅
  [GG 2026-09-25]. Sin él devuelve la página de búsqueda entera (unos 570 KB). Con él devuelve
  JSON `{count, html}`, donde `count` es el total real. El snippet recibe páginas de 12, y el
  `limit` se ignora. En GG el plan B del panel funcionó en silencio durante una semana, sin que
  nadie notara que el camino principal fallaba.
- El mismo header cambia lo que devuelve una página normal: para re-pedir una página entera y
  extraerle un bloque, se pide **sin** `X-Requested-With`, porque con él la plataforma puede
  devolver un parcial [MC].

## URLs, SEO y caché

- 🔥 **Cualquier segundo tramo inventado bajo una categoría que existe responde 200** ✅
  [MC 2026-09-17]. La plataforma sirve la categoría madre con sus productos, y el último crumb
  sale como `breadcrumbs.<segmento>` sin traducir, en las migas **y en el JSON-LD
  `BreadcrumbList`**, que Google indexa. Se filtran las migas que empiezan con `breadcrumbs.`.
  El 200 no lo puede arreglar el tema: el camino es el canonical. Un `'clave' | t` con una
  clave inexistente devuelve la clave tal cual (ver
  [Schema y traducciones](06-schema-y-traducciones.md)).
- ⚠️ **Cada card emite su propio `Product` en el ld+json.** Una ficha trae 14 o 15 por los
  relacionados, que además se barajan en cada request [MC].
- ⚠️ **El HTML de algunas páginas viene del caché del servidor (`x-cache: hit`), y la clave
  ignora el query**: ni `?cb=`, ni `?theme_installation_id=`, ni `no-cache` lo saltean. Un push
  sí lo invalida. Antes de dar un render por roto, mirá ese header [MC]. Cómo medir sin caer en
  esto está en [Verificación y QA](15-verificacion-y-qa.md).
- Con dominio propio, el subdominio `*.mitiendanube.com` puede pasar a 410 (ver
  [Modelo y CLI](05-modelo-y-cli.md)).

## Imágenes y CDN

- ⚠️ **`snippets/image.tpl` emite `width`, `height` y `aspect-ratio` inline para las fotos de la
  biblioteca**, así que no hay salto de layout. Con una URL externa no hay dimensiones y sí hay
  salto. El snippet acepta `@media-lib:` y URLs externas [MC].
- ⚠️ **El CDN de imágenes responde 403 sin el referer de la tienda.** Para bajar fotos hace falta
  `-e https://<tienda>.mitiendanube.com/` en el curl [MC].
- ⚠️ **La portada de un post del blog no se redimensiona**: es la misma URL en todo el
  `srcset`. Conviene subirla a 2000px en JPEG 84 [VZ].
- `sizes`, lazysizes y el peso de las imágenes de la card y la galería están en
  [JavaScript](11-javascript.md). El tope de `max-height: 1200px` del tema base, en
  [CSS](10-css.md).

## Lo que depende del país de la tienda

- ✅ **El código base ya es country-aware** [MC 2026-09-22]: `store.afip` solo se completa en
  tiendas argentinas (lo usa `footer-legal.tpl`), y la ayuda de código postal del calculador
  de envío solo aparece para `['BR','AR','MX']`.
- El locale de referencia, la moneda y lo que arrastra clonar un tema a otro país están en
  [Schema y traducciones](06-schema-y-traducciones.md) y en
  [Multi-país, apps e integraciones](16-multipais-apps-integraciones.md).
