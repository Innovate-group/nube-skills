# Verificación y QA

Qué se chequea antes de guardar, cómo se mide en la tienda real (y no en una réplica), cómo
se compara contra el diseño, y las técnicas que en estos proyectos evitaron conclusiones
falsas.

## Lo esencial

- **El sistema falla en silencio.** Una section que no renderiza, un push que omite archivos,
  una hoja CSS que la plataforma no puede construir: nada de eso da error. La única defensa
  es correr los chequeos que ven cada cosa y medir en la tienda.
- **Los chequeos van antes de guardar.** Con `theme watch` prendido, guardar es publicar. Hay
  que revisar cuatro cosas:
  - que los schemas parseen;
  - los comentarios de Twig;
  - `node --check`;
  - los comentarios de CSS.

  El chequeo de balance da falso verde justo en los casos más caros.
- **Se mide en la tienda, no en una réplica.** Se usa el MCP de chrome-devtools con
  `emulate`. Si otra sesión tiene tomado el MCP, se usa un Chrome headless con perfil propio y
  un user agent normal. Nunca un Chrome visible lanzado desde el shell.
- **Nada se declara "sin verificar en vivo" sin revisar antes tres cosas:** si la tienda está
  en modo contraseña, si el cambio ya está publicado y si sirve la preview sin login.
- **El QA es numérico.** El boceto y la preview se miden en el mismo navegador, con los mismos
  viewports, usando `getBoundingClientRect`. Cada diferencia se clasifica como código,
  contenido de la tienda o configuración del Admin.
- **Se verifica en los dos sentidos:** cero falsos positivos sobre el catálogo entero, y el
  caso positivo sobre el caso real.
- **Una explicación plausible no es un hallazgo** hasta que sobrevive a la medición.
  Lighthouse, por ejemplo, contamina los requests de la página.

## Chequeos locales, sobre todo archivo tocado

Todo esto se puede comprobar sin la tienda. **Se corre sobre todos los archivos tocados, antes
de guardar** si hay un `theme watch` prendido: guardar publica, así que hay que validar antes.
El patrón para eso (copia → chequeo → `mv`) está en [sync y reglas](03-sync-y-reglas.md).

```bash
# 1 · Cada {% schema %} parsea como JSON
python3 - <<'PY'
import re, json, glob
for f in glob.glob('sections/*.tpl') + glob.glob('blocks/*.tpl'):
    m = re.search(r'\{%\s*schema\s*%\}(.*?)\{%\s*endschema\s*%\}', open(f).read(), re.S)
    if not m: continue
    try: json.loads(m.group(1))
    except Exception as e: print('SCHEMA ROTO', f, e)
PY

# 2 · Tags Twig balanceados (ignorando comentarios)
# 3 · ⚠️ Comentario de Twig adentro de una etiqueta {% %}   ← el chequeo 2 NO lo ve
# 4 · ⚠️ Comentarios de Twig anidados                       ← ninguno de los otros lo ve
#     (los scripts de 3 y 4 están en 07-twig.md, junto a la trampa que detectan)

# 5 · Toda clave t: existe en todos los locales
#     audit-i18n.py de nube-skills-i18n (cómo invocarlo, en 02-skills.md)

# 6 · JS
node --check static/js/store.js

# 7 · CSS: balance de llaves Y de comentarios (el de comentarios, abajo)
```

⚠️ **Los chequeos 3 y 4 fueron los que más caro salieron, y ninguno de los otros los detecta.**
El chequeo de balance da un **falso verde**, porque arranca borrando los comentarios. Las
trampas y sus scripts están en [Twig](07-twig.md).

**Corolario:** cuando un chequeo normaliza el input antes de mirarlo, no puede encontrar
errores en lo que normalizó.

### 🔥 Un comentario de CSS mal cerrado tira la hoja entera

*[MC 2026-09-15]* Un comentario de CSS citaba la ruta de los JSON de plantilla con un glob:
`templates`, doble asterisco, `/*.json`. Ese asterisco seguido de barra **es el cierre del
comentario**, así que todo lo que venía después pasó a ser CSS vivo.

- **El daño no fue una regla muerta: fue la hoja entera.**
  - `style-async.css` quedó con una apertura de comentario más que cierres.
  - La plataforma no pudo construir el asset y `static_url` devolvió un string vacío.
  - El `<link rel="stylesheet">` salió con `href=""`.
  - Se cayeron **todos** los estilos async del sitio.

  El diff parecía inofensivo: dos declaraciones aditivas.
- **El balance de llaves da OK igual**, porque las llaves siguen emparejadas. Hay que recorrer
  los comentarios como lo hace el parser, sobre **todos** los `.css` tocados:

```python
import sys
s = open(sys.argv[1], encoding='utf-8').read()
i, roto = 0, None
while (a := s.find('/*', i)) >= 0:
    b = s.find('*/', a + 2)
    if b < 0: roto = s[:a].count('\n') + 1; break
    i = b + 2
print(s.count('/*'), s.count('*/'), 'ROTO en la línea' if roto else 'OK', roto or '')
```

- **La regla:** en un comentario de CSS no van rutas con glob, ni expresiones regulares, ni
  nada que pueda contener asterisco y barra. Se escribe en prosa: "los JSON de plantilla".
- **Cómo se diagnostica desde la tienda**, que es lo que lo resolvió en tres minutos: mirar los
  `<link rel="stylesheet">` del `<head>`. Un `href=""` significa que ese archivo no existe como
  asset en el servidor, casi siempre porque no se pudo procesar. El síntoma es el mismo para
  cualquier `.css` o `.js` que quede sintácticamente roto.

### 🔥 Después de editar por script, comparar las líneas

*[MC 2026-09-10]* Una edición por script del tipo `s[:i] + nuevo` truncó 406 líneas de CSS.
La "verificación midiendo números" se había hecho antes de esa edición, así que la página rota
llegó igual.

- **La regla:** después de cada edición por script, comparar la cantidad de líneas del
  archivo, antes y después, y sacar una captura de la página.

```bash
git diff --numstat -- static/css/style-critical.css   # líneas agregadas y borradas: ¿cuadra con lo que querías?
wc -l static/css/style-critical.css                   # contra el conteo de antes de la edición
```

## Medir en la tienda, no en una réplica

✅ Es una corrección explícita del dev *[MC 2026-08-31]*: *"no crees un html para revisarlo.
revisalo directamente desde la tienda!"*. Venía después de que se armara un harness local que
copiaba `style-critical.css` y replicaba a mano el comportamiento de `store.js`.

- **Por qué:**
  - una réplica solo prueba lo que uno puso en la réplica;
  - el markup real lo emite Twig con datos reales;
  - el CSS real trae cientos de KB de reglas del tema base que muerden por especificidad y
    por orden de archivo;
  - la plataforma inyecta lo suyo: los slots del nubesdk, el widget del captcha, los modales.

  Todos los bugs caros de estos proyectos salieron de esa capa, y una réplica no la tiene. En
  GG pasó lo mismo: el harness de una card promocional dio verde, y en vivo no andaba *[GG]*.

### Con el MCP de chrome-devtools

- **Se usa `emulate` con el viewport completo** (`"1440x900x2"` y `"390x844x3,mobile,touch"`),
  para que el DPR y el touch evalúen bien las media queries. Así lo pide `nube-skills-qa`, que
  prohíbe `resize_page`. En la práctica, en MC se usó `resize_page` 81 veces contra 28 de
  `emulate`. En VZ, con la skill cargada, fueron 66 `emulate` contra 2 `resize_page`
  (relevado el 2026-09-30).
- **Patrones que funcionaron** *[MC]*:
  - `evaluate_script` con `requestAnimationFrame` o `setTimeout` para muestrear estados;
  - escuchar `transitionrun`, `transitionend` y `transitioncancel` para saber si una
    transición corre de verdad;
  - congelar una animación a mitad de camino y sacarle una captura:

```js
panel.getAnimations().forEach(a => { a.pause(); a.currentTime = 150 })
```

- **Para una captura estable,** se congelan las animaciones con el `initScript` de
  `navigate_page`, como hace `nube-skills-qa`.
- ⚠️ **El estado del módulo persiste entre scripts.** Una variable de `store.js` puede quedar
  apuntando a un elemento de una prueba anterior, y el click siguiente hacer lo contrario de lo
  esperado. El resultado parece un bug del arreglo. **Hay que recargar la página entre
  mediciones** *[MC]*.
- ⚠️ **El MCP de Chrome no puede engancharse al navegador que abre `theme watch`.**
- **La preview se mide con su URL sin login.** El parámetro y sus límites están en
  [modelo y CLI](05-modelo-y-cli.md). Uno importa acá: los pedidos AJAX y la paginación de la
  preview los responde el tema publicado, no el borrador.
- ✅ **La preview agrega una barra de 52px arriba de todo.** El header queda en `top: 52px`,
  así que hay que restar esa barra al medir posiciones contra el boceto *[VZ 2026-09-24]*.

### Si el MCP está tomado por otra sesión

El error es *"The browser is already running for …/chrome-profile"*. **Todas las sesiones de
Claude Code de la máquina comparten ese perfil**, así que el navegador puede ser de otra
sesión o del propio dev.

- 🔥 **No hay que matar ese Chrome sin mirar de quién es.** *[GG 2026-09-23]* Se mató el Chrome
  que coincidía con el perfil del MCP, y era el de otra sesión viva: se cerraron su navegador
  y sus páginas. Antes de matar nada, hay que recorrer la cadena de procesos padre
  (`ps -o pid,ppid,lstart,command -p <pid>` hasta el proceso `claude`) y compararla con la
  propia (`$PPID`). Si no es tuyo, se deja.
- 🔥 **Nunca levantar un Chrome visible desde el shell.** *[MC 2026-09-10]* Pasó dos veces:
  1. macOS le reasignó el *responsible process* a la app lanzada desde el shell;
  2. le revocó a Claude Code el acceso a `~/Desktop`, `~/Documents` y `~/Downloads`;
  3. el repo entero quedó ilegible: `Operation not permitted`, y
     `fatal: Unable to read current working directory`.

  No es el sandbox, y no se recupera solo. Hay que volver a otorgar el acceso en Ajustes →
  Privacidad y seguridad → Archivos y carpetas, **y reiniciar Claude Code**, así que se pierde
  la sesión entera.
- **Lo que sí funcionó: Chrome headless con perfil propio** *[GG 2026-09-23]* *[VZ 2026-09-24]*.
  Se maneja por CDP con el `WebSocket` nativo de Node 22, o con `puppeteer-core` instalado en
  el scratchpad. Aun así:
  - avisarle al dev antes de lanzarlo;
  - guardar los hallazgos a medida que salen en `~/.claude/projects/<proyecto>/`, que sigue
    accesible si se cae el acceso a Desktop *[MC 2026-09-10]*.

```js
// npm i puppeteer-core@23 en el scratchpad
const b = await puppeteer.launch({
  executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  headless: true, userDataDir: '<scratchpad>/chrome-profile' });
const p = await b.newPage();
await p.setUserAgent((await b.userAgent()).replace('HeadlessChrome', 'Chrome'));
```

- ✅ **El user agent tiene que ser uno normal.** Con el de headless por defecto, la tienda
  responde `POST /comprar/` con un 403, el tema lo muestra como `out_of_stock` y el agregar al
  carrito no funciona nunca *[VZ 2026-09-24]*.
- ❓ **El `IntersectionObserver` en headless: hay que re-medirlo.** Las dos fuentes no
  coinciden:
  - MC midió que con `--headless=new` no dispara (`visibilityState` queda en `"hidden"`) y
    los carruseles de las cards nunca se inicializan, y concluyó que hacía falta un Chrome
    visible *[MC 2026-09-10]*;
  - VZ midió con puppeteer headless "con todos los reveals ya disparados", y esos reveals
    dependen del `IntersectionObserver`, pero no documentó cómo los disparó *[VZ 2026-09-24]*.

  Cómo re-medirlo: en la misma página, correr en headless y en el MCP
  `[document.visibilityState, await new Promise(r => new IntersectionObserver(e => r(e[0].isIntersecting)).observe(document.querySelector('#MainContent')))]`
  y comparar. Si en headless da `hidden` o nunca resuelve, lo que dependa del observer (lazy,
  reveals, carruseles de card) se mide en el MCP.
- ❓ **Agregar al carrito desde la sesión de medición.** MC no pudo disparar el alta de
  ninguna forma (submit, `fetch`, endpoints) *[MC]*. VZ encontró después que con el user agent
  de headless `POST /comprar/` responde 403 *[VZ 2026-09-24]*. Puede ser la misma causa. Para
  re-medirlo, se repite el alta con un user agent normal.
- ⚠️ **Loguearse en modo contraseña por CDP.** La cookie de sesión es HttpOnly: no se puede
  trasplantar desde curl. El login se hace **desde adentro de la página**, con
  `fetch('/password/', {method: 'POST', credentials: 'same-origin'})` *[MC 2026-09-08]*.
- ⚠️ **`captureBeyondViewport` con un `clip` alto compone mal si hay header sticky.** Para
  juzgar cómo se ve, conviene hacer `scrollTo` y capturar el viewport *[MC 2026-09-08]*.
- ✅ **Se puede probar JS sin subirlo.** En un Chrome headless se intercepta por CDP el
  `…/installations/<id>/static/js/store-*.js` y se sirve la copia local *[GG 2026-09-25]*.

### Inyectar markup para medir estados que la tienda no tiene

- **Si no hay una instancia real o el cambio no está publicado,** se inyectan en la página
  real el CSS y el JS extraídos de los propios archivos, o un bloque con sus clases, y se
  mide ahí *[MC]*.
- ⚠️ **Eso prueba el CSS, no el Twig.** En VZ, la cuenta logueada se midió inyectando el markup
  de la section con los datos del boceto, y el Twig de las páginas con sesión quedó sin verse
  renderizado *[VZ 2026-09-24]*. Para verlo hace falta una cuenta de prueba real: el token del
  CLI no tiene permiso sobre clientes y el registro tiene captcha (ver
  [límites](13-limites-y-admin-api.md)).

### 🔥 Lighthouse contamina los requests

*[MC 2026-09-17]* `lighthouse_audit` navega por su cuenta. Un `list_network_requests` corrido
después devuelve los requests de **esa** navegación, no los de la carga que hiciste vos. En MC
parecía que cada foto de la ficha se bajaba dos veces (1024 y 3840 px, ~1,4 MB de más), y se
reportó así en un informe al cliente. Era falso: en una carga limpia baja una sola copia.

- **Cómo medir bytes de imagen de verdad:**
  - usar un contexto aislado (`new_page` con `isolatedContext`) y `navigate_page` con
    `ignoreCache: true`. Ojo: los contextos aislados **comparten la caché HTTP**, así que una
    imagen ya pedida da `transferSize: 0`;
  - ⚠️ Chrome **reutiliza un candidato más grande del `srcset`** si ya lo tiene en caché. Para
    comparar qué elegiría con otro `sizes`, hay que agregarle un cache-buster a cada URL del
    `srcset`;
  - el dato honesto es `img.currentSrc` (qué candidato eligió) contra
    `img.getBoundingClientRect().width * devicePixelRatio` (qué necesitaba).
- **La regla:** una explicación plausible sobre el rendimiento no es un hallazgo hasta que
  sobrevive a la medición. Antes de escribirla en un informe, hay que reproducirla en una carga
  limpia que no venga después de una corrida de Lighthouse.
- `tiendanube theme performance` ya corre Lighthouse mobile y desktop sobre la preview (ver
  [modelo y CLI](05-modelo-y-cli.md)). `nube-skills-qa` no lo duplica.

## Antes de declarar "sin verificar en vivo"

En MC, media documentación siguió diciendo "sin verificar en vivo" mucho después de que la
tienda ya respondía 200. Antes de dar por imposible una verificación:

- ✅ **Comprobar el modo contraseña, cada vez y en los dos sentidos.** Va y viene: en MC estuvo
  apagado el 2026-08-31, prendido el 2026-09-04 y apagado desde el 2026-09-17 *[MC 2026-09-17]*.
  Se comprueba en dos segundos:

```bash
curl -s -o /dev/null -w "%{http_code} %{url_effective}\n" -L https://<dominio>/
```

  Si termina en `/password/`, se mide logueado: la contraseña la da el dev y no se escribe en
  ningún archivo versionado. La preview **no** saltea el modo contraseña, y `/password/` no
  sirve para medir: está cacheada del lado del servidor y el footer va detrás de
  `{% if not password_page %}` *[MC 2026-09-08]*.
- ✅ **Comprobar si el cambio ya está publicado.** Con el `theme watch` del dev prendido, lo que
  se guarda en el working tree puede estar en la tienda a los segundos sin que el agente haya
  pusheado nada. En MC se entregaron tres cambios como "sin verificar" y los tres ya estaban
  arriba *[MC 2026-09-17]*. Alcanza con dos `curl`:
  - el HTML de la página: ¿salió el markup nuevo?;
  - el asset del CDN, que cambia de nombre en cada subida
    (`style-critical-<hash>.min.css`, `…/static/js/store-<hash>.js`): se baja y se busca el
    símbolo nuevo.

  El hash tarda unos segundos en rotar ([modelo y CLI](05-modelo-y-cli.md)). Nada de esto
  habilita a pushear: medir es lectura.
- ✅ **Comprobar que el dominio sirve este tema.** Con dominio propio, el subdominio viejo puede
  responder 410 (ver [modelo y CLI](05-modelo-y-cli.md)). Y un dominio puede seguir sirviendo
  otro sitio: en MC, los dominios de Chile y Uruguay todavía servían la plataforma anterior.
  Para saberlo, se busca `data-section-type` o `installations/<id>` en el HTML
  *[MC 2026-09-22]*.
- **Antes de dar un render por roto, mirar el header `x-cache`.** Algunas páginas salen de la
  caché del servidor y la clave ignora el query string (ver [plataforma](08-plataforma.md)).
- **Qué no se puede medir:**
  - las sections deshabilitadas o vacías, que miden 0 de alto *[MC]*;
  - el pie en la página de colección, que queda oculto mientras corre el scroll infinito. Se
    mide en una ficha o en una landing (ver [plataforma](08-plataforma.md));
  - las páginas logueadas, sin una cuenta de prueba real *[VZ 2026-09-24]*.

  Lo que no se pudo verificar se dice así, con el motivo.

## QA visual contra el diseño

`nube-skills-qa` hace QA numérico con estilos computados, en desktop y mobile, y separa los
bugs de código de los settings mal configurados y del contenido real de la tienda. Cómo se
invoca está en [skills](02-skills.md). En la práctica casi no se usó: una vez en VZ y ninguna
en MC, contra unas 1.800 llamadas al MCP de chrome-devtools. El QA se hizo a mano (relevado el
2026-09-30), y este es el método que funcionó.

- ✅ **El boceto y la preview se miden en el mismo navegador, con los mismos viewports**
  *[VZ 2026-09-24]*:
  - 1440×900 y 390×844, más 768, 1024 y 1280 cuando la pieza cambia de layout en el medio;
  - las cajas con `getBoundingClientRect`, al décimo de píxel;
  - restando la barra de 52px de la preview;
  - con los reveals ya disparados;
  - si el texto real difiere del boceto, se inyecta el del boceto para comparar la geometría.
- ✅ **Pixel-diff contra el prototipo:** en GG se llegó a una diferencia de 0 en 1440 y en 390
  *[GG 2026-09-25]*.
- ✅ **Si el dev lo pide, también se hace QA en tablet 820×1180** (iPad vertical), verificando
  pieza por pieza que 1440 y mobile quedan intactos *[MC 2026-09-08]*. El rango tablet de
  Ipanema está en [CSS](10-css.md).
- ✅ **Cada diferencia se clasifica como código, contenido real o configuración del Admin**
  *[VZ 2026-09-24]*. Ejemplos de la revisión final de la home de VZ:
  - las cards salían 21px más bajas porque la tienda no tenía cuotas sin interés configuradas
    (configuración del Admin);
  - seis fotos seguían con placeholder porque no estaban en la biblioteca (contenido).

  El contenido real de la tienda no es un hallazgo de código, pero se lista para el dev.
- **Hay diferencias que no son bugs:** por ejemplo, el redondeo de las métricas de la fuente
  entre el boceto y la preview (ver [diseño y ui-kit](04-diseno-y-ui-kit.md)).
- ⚠️ **Para verificar un link de búsqueda, se cuentan los `.js-item-name` del listado,** no los
  links a productos: el header y el panel de búsqueda traen los suyos y dan un falso positivo
  *[VZ 2026-09-24]*.
- ✅ **El barrido exhaustivo, cuando el cambio es transversal:** en GG se usó el sitemap (77
  fichas publicadas y 58 que daban 404) y se revisaron 602 cards *[GG 2026-09-24]*.

## Técnicas que evitaron conclusiones falsas

- ✅ **Verificar en los dos sentidos.** Un filtro del tema (por ejemplo, "no mostrar productos
  sin foto") se prueba así *[MC 2026-09-21]*:
  - sobre el catálogo completo: 0 escondidos de 1.346 cards, cero falsos positivos;
  - sobre un HTML capturado con el caso real: esconde exactamente esa card de 33.
- ✅ **Barrer todas las páginas del listado, antes y después, con una tabla de conteos:** cards,
  productos, falsos positivos, entidades `Product` del `ld+json`. En MC, 562 cards pasaron a
  356 y los 302 productos siguieron con al menos una card *[MC 2026-09-11]*.
- ✅ **Forzar un valor y ver que cambie solo esa pieza.** En MC, al cambiar la cantidad para
  ver que el monto de cuotas se recalculaba, cambió esa card y las vecinas quedaron con su
  monto *[MC 2026-09-16]*.
- **Probar en dos pasos cuando la prueba toca datos reales** *[MC 2026-09-14]*:
  1. primero con datos simulados desde Twig, sin escribir el catálogo;
  2. después con datos reales por API, verificando y restaurando, y confirmando que las
     etiquetas ajenas quedaron intactas.
- **Antes de atribuirle un bug al cambio, probar si ya estaba:** se restaura la versión de
  `HEAD` y se mide *[MC]*.
- **Listar las ramas sin probar** ("sin probar: el toggle apagado") y las superficies que no se
  verificaron en vivo, con el motivo *[MC 2026-09-16]*.
- **Si el caso real desaparece a mitad de la tarea,** se verifica sobre un HTML capturado antes
  y se dice que el estado es recurrente. En MC, mientras se trabajaba, el comerciante les cargó
  las fotos a los productos que no tenían *[MC 2026-09-21]*.
- **Un saneado se valida contra el HTML prístino del servidor** (`fetch` + `DOMParser`), no
  contra una expectativa *[MC 2026-09-10]*.
- **Un assert que no puede fallar es peor que no tener assert** *[MC 2026-09-10]*.
- **Medir y no deducir.**
  - La primera versión de una nota sobre el mapa de locales afirmaba al revés cuál era el
    host que fallaba *[MC 2026-09-18]*.
  - "Verificado midiendo números", sin captura, dejó pasar una página rota
    *[MC 2026-09-10]*.

  Siempre, captura.
- **Si un bug no se reproduce,** se le deja al dev un one-liner de consola que distinga "llegó
  vacío del servidor" de "se vació en el cliente" *[MC]*.
- ⚠️ **Un plan B silencioso tapa las fallas.** En GG, el respaldo del panel de búsqueda funcionó
  en silencio del 2026-09-18 al 2026-09-25 mientras el camino principal fallaba. Todo respaldo
  tiene que dejar rastro *[GG 2026-09-25]*. El rastro por excelencia, el diagnóstico por
  comentario HTML, está en [patrones](14-patrones.md).
