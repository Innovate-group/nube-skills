# Modelo sectionable y CLI

Cómo está armado un tema Ipanema y cómo se mueve entre tu disco y la tienda con el CLI de Tienda
Nube (Fork Workflow). El **protocolo** para escribir sin pisar al comerciante está en
[Sync y reglas](03-sync-y-reglas.md). Este capítulo cubre la mecánica: qué hace cada comando,
qué sube, qué baja y en qué miente.

## Lo esencial

- Ipanema es el único tema base sectionable y el único que admite el Fork Workflow. **No es un
  solo árbol:** hay variantes (*Clothing*, *Clothing-2*) y versiones (1.0.0, 1.2.x). Medí el de
  tu instalación en vez de copiar números de otro proyecto.
- Siempre el binario **`tiendanube`, nunca `nuvemshop`**: `nuvemshop theme authorize` manda
  `region=br` y deja una tienda de LATAM en la pantalla equivocada.
- Sin fork, `theme push` deja afuera todo el código del tema (con el CLI 2.1.0, además, sin
  avisar). El fork hoy funciona, pese a que la documentación oficial lo marca "Próximamente".
- **El CLI miente en las dos direcciones:** el pull puede bajar el tema incompleto y decir
  `Download completed.`, y el resumen del push no refleja lo que hizo. Contá los archivos antes
  de creerle a un diff.
- 🔥 Con el CLI 2.3.1, **`theme pull` borra los archivos locales antes de descargar**. Con
  `theme watch` prendido en la misma carpeta, un GET que falla termina borrando la instalación
  ([Sync y reglas](03-sync-y-reglas.md), incidente del 2026-09-23).
- `theme diff --detailed` es la lectura segura del servidor: solo GET, no escribe nada. Los JSON
  del servidor vienen minificados, así que se comparan parseados.
- La preview sin login es `?preview_theme_installation_id=<id>`: responde sin sesión y muestra
  lo **guardado** en el editor.

## El modelo: contenido, estructura y render

El modelo desacopla contenido de estructura:

| Pieza | Define | Archivo |
|---|---|---|
| **JSON template** | **QUÉ** se muestra: qué sections, en qué orden, con qué settings y blocks | `templates/pages/*.json`, `templates/layout/*.json` |
| **`{% schema %}`** | **QUÉ PUEDE EDITAR** el comerciante: inputs, defaults, `visible_if`, presets, blocks aceptados | al final de cada `sections/*.tpl` y `blocks/*.tpl` |
| **`.tpl`** | **CÓMO** se renderiza | `sections/`, `blocks/`, `snippets/` |

Cualquier otro tema de Tienda Nube va por FTP (legado), con `snipplets/`, `settings.txt` y otro
conjunto de reglas. No mezcles las dos cosas ni las skills de una con las de la otra.

Pipeline de render:

```
layouts/layout.tpl
  <head>  → fuentes, style-tokens.tpl, CSS crítico inline
  <body>
    {% layout_template 'header' %}          ← templates/layout/header.json
    <main id="MainContent">
      {{ page_template_content }}           ← templates/pages/<página>.json
        └── sections/<tipo>.tpl   lee section.settings.* y section.blocks
              └── blocks/<tipo>.tpl  lee block.settings.*
                    └── {% include 'snippets/…' %}   (sin schema, no editables)
    </main>
    {% layout_template 'footer' %}          ← templates/layout/footer.json
    modales (carrito drawer, popup promocional), notificaciones, scripts
```

### Estructura de carpetas de una instalación

```
tema/
├── blocks/               ← código: bloques con schema
├── config/
│   ├── settings_schema.json   ← código: schema de settings GLOBALES
│   ├── settings_data.json     ← personalización: valores guardados por el comerciante
│   └── sections.txt           ← colecciones automáticas (primary/new/sale/timer_offers/featured)
├── layouts/
│   ├── layout.tpl
│   └── resources/
│       ├── icons-sprite.tpl   ← sprite SVG inline (acá se agregan íconos nuevos)
│       └── style-tokens.tpl   ← custom properties CSS emitidas desde settings
├── sections/
├── snippets/             ← partials SIN schema (cart/, product/, forms/, shipping/, header/…)
├── static/
│   ├── css/{style-critical,style-utilities,style-async}.css
│   ├── js/{store.js, libraries.js.tpl, libraries-standalone.js}
│   ├── fonts/, images/
│   └── checkout.scss.tpl      ← branding del checkout
├── templates/
│   ├── pages/            ← personalización: home.json, product.json, …, y account/
│   └── layout/           ← personalización: header.json, footer.json
├── translations/         ← código: <locale>.json + <locale>.schema.json
├── custom/               ← personalización: archivos libres del dev (puede no existir)
└── manifest.json         ← solo local, nunca se pushea
```

⚠️ **`translations/` vs `locales/`.** La documentación de arquitectura dice `translations/` y la
del CLI dice `locales/`. **Mirá cuál existe en el proyecto antes de crear un archivo.** En los
tres proyectos fue `translations/`.

⚠️ **No existe carpeta `custom/`** en una instalación forkeada que nunca la usó. Con fork no hace
falta: las personalizaciones van directo en las carpetas del tema.

## Ipanema no es un solo árbol

- ✅ **Cada instalación puede traer otra versión y otra variante del base.** En los tres
  proyectos aparecieron cinco combinaciones: 1.0.0 (MC Argentina), 1.2.1 (MC Chile), 1.2.2 de
  fábrica (MC Uruguay), *Clothing* 1 → 1.2.0 (GG) y 1.2.2 *Clothing-2* (VZ). [MC 2026-09-22]
- ✅ **La 1.2.x trae suscripciones** (`blocks/label.tpl`, `sections/main-account-subscription-address.tpl`,
  `snippets/subscriptions/*`, `templates/pages/account/subscription-address.json`), que un fork
  hecho desde 1.0.0 no tiene. [MC 2026-09-22] [GG 2026-09-15]
- ⚠️ **Los tamaños cambian mucho entre variantes.** Como ejemplo: `store.js` tenía unas 3.750
  líneas en GG y 7.600 en MC al 2026-09-03 (9.600 a fin de mes); `style-critical.css` pesaba
  ~115 KB en GG y ~350 KB en MC. **Nunca uses la cifra de otro proyecto como valor esperado.**
  [GG] [MC]
- **Diffeá tu base contra el pull inicial del proyecto anterior** para saber qué trampas
  heredás. VZ lo hizo contra GG: el `layout.tpl` era igual y las diferencias eran pocas líneas de
  CSS y de `store.js` más los snippets de suscripciones, así que las trampas de GG aplicaban.
  [VZ]

## Requisitos y binarios

| | |
|---|---|
| Node.js | La doc pide **≥ 24.15**. El CLI 2.1.0 y el 2.3.1 corrieron bien con Node 22.22.3. Si aparece un error raro del CLI, actualizá Node antes de investigar otra cosa. Si el proyecto trae `.nvmrc`, `nvm use` primero: si esa versión no está instalada, falla (en GG salió con exit 3) |
| Instalación | `npm i -g @tiendanube/cli` |
| Binarios | `tiendanube` y `nuvemshop`, **que no son iguales** (ver abajo) |

- ✅ El CLI 2.3.1 declara `engines >=24.15` y corre con Node 22.22.3. [VZ 2026-09-23]
- 🔥 **`tiendanube` y `nuvemshop` no son idénticos: el nombre del binario decide la región del
  `authorize`.** `nuvemshop theme authorize` manda `region=br` y deja una tienda de LATAM en la
  pantalla equivocada. Usá siempre `tiendanube`. [GG 2026-09-14] [VZ 2026-09-23]
- ⚠️ **Puede haber más de un CLI en el `PATH`.** En GG el legacy `tiendanubecli` 1.3.0 (el de
  FTP) aparecía primero; en VZ había dos `tiendanube` 2.3.1 (el de `~/.local/bin` y el de nvm).
  Corré `which -a tiendanube` y `tiendanube --version` antes de nada. [GG] [VZ]

## Autenticación

```bash
tiendanube theme authorize                      # interactivo: abre el navegador
tiendanube theme authorize --token <TOKEN> -y   # CI / no interactivo
```

- El token es la **cadena Base64 completa** de la página de autorización, **no** el access
  token pelado.
- Escribe `.nuvem` en el directorio de trabajo. **`.nuvem` va al `.gitignore` sí o sí:** es una
  credencial. `.nuvem` es un JSON en base64 con los datos de `theme-api` (la tienda, el token y
  el id de la instalación). Ese token también sirve para la Admin API: cómo usarlo sin
  imprimirlo, en [Límites y Admin API](13-limites-y-admin-api.md).
- Todos los comandos aceptan `--token` por invocación; con `--token` no se escribe nada a disco.
  ⚠️ Por eso un pull con `--token` deja la carpeta **sin** `.nuvem`, y sin `.nuvem` no corren
  `list`, `current`, `preview` ni `watch`. [GG]
- ⚠️ **Si el navegador tiene abierta la sesión de otra tienda**, el authorize la toma. Abrí la
  URL de autorización en una ventana de incógnito y usá `--token`. [GG]
- ⚠️ **Los tokens de `.nuvem` vencen.** `theme list` y `theme pull` empiezan a responder 401 y
  el dev tiene que volver a correr `theme authorize`. [MC 2026-09-25]
- 🔥 **El id de la instalación que usa el CLI vive en `.nuvem` (`theme-api.themeId`), no en
  `manifest.json`.** Sin ese campo, `theme current` dice *"No theme id saved for the current
  folder"* aunque el manifest esté bien, y el CLI sugiere `theme pull --theme-id`, que sobre la
  carpeta del proyecto pisa el trabajo local. En un proyecto existente se arregla escribiendo
  `themeId` en `.nuvem`; `theme pull --theme-id` solo sirve para vincular una carpeta vacía.
  [MC 2026-09-22]
- **Un directorio queda vinculado a un único workflow.** Los comandos del Fork Workflow no corren
  en un directorio configurado para FTP, y viceversa.

## El modelo Fork: qué se puede tocar

Sin fork, la instalación **protege el código del tema** y solo deja subir la capa de
personalización:

| Sin fork se puede pushear | Sin fork NO se puede |
|---|---|
| `templates/**` | `sections/`, `blocks/`, `snippets/`, `layouts/`, `static/` |
| `custom/**` | `translations/` \| `locales/` |
| `config/settings_data.json` | `config/settings_schema.json` |

- 🔥 **Con el CLI 2.1.0, `theme push` omite los archivos no permitidos EN SILENCIO.** No falla,
  no avisa: reporta éxito y no sube nada. Si tocaste un `.tpl` y en la tienda no cambia nada,
  lo primero que hay que mirar es `manifest.json → "forked"`. [MC]
- ❓ **El CLI 2.3.1 avisa y saltea `custom/`.** En el código (`dist/cli.js`) el push imprime
  "Skipped (not forked, but has changes)" y descarta `custom/` con "push is not yet supported".
  Está leído en el código, no medido. Para re-medirlo: en una instalación sin fork, tocá un
  `.tpl` y corré `tiendanube theme diff --detailed` y después el push, y fijate si aparece el
  aviso. [GG 2026-09-23]
- ⚠️ **La falta de fork no te protege, al contrario.** Lo único que podés subir sin fork
  (`templates/**` y `settings_data.json`) es justo lo único que **también edita el comerciante
  desde el editor**. El modo de falla más caro no requiere fork
  ([Sync y reglas](03-sync-y-reglas.md)).

Propiedades del fork:

- Es **irreversible in-place**. Forkear una instalación ya forkeada es un no-op.
- `theme unfork` **no modifica la instalación de origen**: crea una **instalación nueva**
  (borrador) que conserva `templates/`, `custom/` y `settings_data.json`, descarta el código
  forkeado y reactiva las actualizaciones automáticas del tema base.
- Solo los temas sectionable pueden forkearse.
- ✅ **El fork funciona, aunque la documentación oficial lo marque "Próximamente".** MC ya estaba
  forkeado al arrancar, GG forkeó el 2026-09-15 y el dev de VZ forkeó el primer día.
  [VZ 2026-09-23] [GG 2026-09-15]
- ⚠️ **El fork puede traer una versión más nueva del base.** En GG el mismo sync pasó Ipanema 1 a
  1.2.0; no quedó claro si fue el fork o una actualización automática previa. Después de forkear,
  volvé a pullear y a contar los archivos. [GG 2026-09-15]
- El fork lo corre el dev, no el agente ([Sync y reglas](03-sync-y-reglas.md), reglas del
  equipo).

## Instalaciones

```
create → pull → push/watch → fork → publish → delete
```

- ⚠️ **Máximo 2 instalaciones por tienda** (1 productiva + 1 borrador), **y una legacy cuenta.**
  Si el límite está alcanzado, `theme create` y `theme clone` fallan y hay que borrar una no
  productiva primero. El límite se puede exceder por herencia: MC tenía 3 contando la legacy y
  GG tenía 4 (dos legacy, Ipanema y un backup). En VZ, con la legacy productiva, quedó 2 de 2:
  sin instalación de backup, la única red es git. [MC] [GG] [VZ 2026-09-23]
- **Una instalación de backup sin fork**, si entra en el límite, sirve de red y de referencia del
  base sin rediseño. En GG se usó durante una caída del borrador. [GG 2026-09-23]
- ⚠️ **El borrador puede pasar a productivo sin que la documentación se entere.** Pasó en MC y en
  GG. Verificalo siempre con `theme list`, no con lo que dice el README o el `CLAUDE.md`. [MC]
  [GG 2026-09-25]

| Comando | Qué hace |
|---|---|
| `theme list` | id, título, versión, `prod`, `forked`, `archived` |
| `theme create --base-theme ipanema --title "X"` | nueva desde los defaults del tema base. **`ipanema` es el único valor válido** |
| `theme clone` | copia idéntica de una existente, con sus modificaciones y settings |
| `theme fork` / `theme unfork` | ver arriba |
| `theme publish` | la vuelve **productiva** y reemplaza la activa |
| `theme preview` | la URL de preview (ver "Preview", abajo) |
| `theme performance` | Lighthouse mobile + desktop sobre la preview (`--detailed`, `--json`) |
| `theme diff` | qué cambiaría un push. Solo lectura (ver "Leer el servidor") |
| `theme delete` | **permanente**. No se puede borrar la productiva |
| `theme current` | a qué instalación está vinculado ESTE directorio |

**No hay comando `checkout`.** `theme pull --theme-id <id>` vincula el directorio y los comandos
siguientes usan ese id por defecto (queda en `.nuvem`, ver "Autenticación").

🚫 **Comandos que NO existen** y que da tentación inventar: `theme dev`, `theme check`,
`theme serve`. El dev loop es `theme watch`. ✅ **`theme diff` sí existe** en el CLI 2.3.1,
aunque las referencias viejas no lo nombren. [GG 2026-09-23] [VZ 2026-09-23]

## pull / push / watch

```bash
tiendanube theme pull                 # baja el tema entero al directorio actual (SOBRESCRIBE)
tiendanube theme pull -y              # igual, en modo no interactivo (sin -y falla)
tiendanube theme pull --published     # baja la instalación productiva, sea cual sea
tiendanube theme push                 # smart push: solo lo que cambió
tiendanube theme push --force         # manda todo sin comparar
tiendanube theme watch                # push automático en cada guardado + navegador con reload
tiendanube theme watch --no-browser   # sin Puppeteer
```

- ⚠️ **En modo no interactivo `theme pull` exige `-y`/`--yes`**: sin eso falla con
  "Destructive operation requires confirmation". [MC] [VZ]

### Qué sube el push

- **Todo lo que empiece con punto** (`.git`, `.nuvem`, `.claude`, `.docs`, `.vscode`…) no se
  sube nunca.
- `manifest.json` no se sube nunca.
- Las rutas restringidas por fork, si no hay fork (ver arriba).
- ❓ **La raíz del repo (`README.md`, `CLAUDE.md`, `docs/`).** Con el CLI 2.1.0 se documentó que
  todo lo que no empieza con punto se subía, incluidos esos archivos [MC]. En el CLI 2.3.1 el
  sync opera por **lista blanca**: solo `blocks config custom layouts sections snippets static
  templates translations manifest.json`. El pull del incidente del 2026-09-23 borró exactamente
  esas carpetas y dejó intactos el `CLAUDE.md` y el handoff de la raíz. Leído en el código y
  consistente con lo observado, pero la subida no está medida. **Para re-medirlo**: con un `.md`
  en la raíz, corré `tiendanube theme diff --detailed` y fijate si lo lista como archivo a crear.
  Mientras tanto, la documentación va en carpetas con punto (`.claude/`, `.docs/`): así no viaja
  con ninguna versión del CLI. [GG 2026-09-23]
- ⚠️ **El push sincroniza ELIMINACIONES.** Un archivo que existe en la instalación y no en tu
  copia local **se borra de la instalación**. Esto es lo que convierte un `templates/*.json`
  desactualizado en pérdida de datos ([Sync y reglas](03-sync-y-reglas.md)).
- ⚠️ Un archivo de **cero bytes** hace fallar el push entero, con un error por archivo.

### Qué hace el pull

- 🔥 **En el CLI 2.3.1, `theme pull` primero borra y después descarga.** Borra todas las
  entradas sincronizadas del directorio (`removeThemeEntries` en `dist/cli.js`) y recién después
  baja. Si el GET falla imprime `GET theme files failed (HTTP 500)` y la carpeta queda vacía.
  `manifest.json` se reescribe al final, así que su fecha de modificación es la señal de un pull
  que terminó. Con `theme watch` prendido en esa carpeta, cada borrado se replica en la
  instalación: así se cayó un borrador entero. [GG 2026-09-23] [VZ 2026-09-23]
- ⚠️ **Con el CLI 2.1.0, un pull sobre el proyecto no borraba lo que no bajaba.** Y un
  `git status` limpio no prueba que el pull no haya escrito: puede haber escrito lo mismo, así
  que hay que mirar las fechas de modificación. [MC 2026-08-24]

### Qué hace watch

- 🔥 **Con watch prendido, todo lo que se guarda se publica**, código incluido: un error de Twig
  en `layouts/` es un 500 en toda la instalación en el mismo segundo. Qué hacer al respecto, en
  [Sync y reglas](03-sync-y-reglas.md).
- ✅ **`watch` arranca con `ignoreInitial: true`:** reiniciarlo no sincroniza nada de lo que
  cambió mientras estuvo apagado. [GG 2026-09-23]
- 🔥 **`watch` re-sube en paralelo y sin reintentos.** Después de restaurar desde git los 340
  archivos del incidente, 93 no volvieron a subir. [GG 2026-09-23]
- ✅ **`watch` saltea archivos cuando cambian muchos juntos.** Un `cp` en loop de 22 archivos
  subió 21 en una tienda y 20 en otra, sin ningún aviso. Se arregla tocando los archivos de a uno
  (unos 12 s entre cada uno) y confirmando con un pull a un temporal. [MC 2026-09-28]
- ⚠️ **El navegador que abre `theme watch` no es alcanzable por el MCP de Chrome.** Medí sobre la
  URL de preview ([Verificación y QA](15-verificacion-y-qa.md)).

## `manifest.json`

```json
{ "theme": "ipanema", "theme_version": "1.0.0", "forked": true,
  "revision_token": "<hash>", "theme_id": <id> }
```

- Solo local, nunca se pushea. El `revision_token` es la revisión de la que vienen los archivos
  locales. **Si después de un pull el token sigue igual, el pull no terminó.**
- ✅ **`"theme"` puede venir en `null`** (el CLI copia el valor de la instalación, que puede ser
  nulo), y antes del fork `theme_version` puede ser `"1"`. No sirve para detectar si el tema es
  Ipanema. [MC 2026-09-22] [VZ 2026-09-23]
- **Después de cada subida del dev, refrescá el `revision_token`** con un pull a un temporal y
  commitealo aparte (`chore: refrescar el revision_token`). Con el token viejo, el resumen del
  push miente todavía más. [MC]
- `manifest.json` **sí** se versiona en git, y va a aparecer modificado seguido porque su
  `revision_token` cambia en cada push ([Arranque](01-arranque.md)).

## 🔥 El CLI miente, en las dos direcciones

**1 · El resumen del `push` no refleja lo que pasó.** Con el CLI 2.1.0 reportó `0 to create`
mientras creaba dos archivos, y `0 to update` tanto con cambios sin subir como con cambios ya
subidos: el mismo mensaje significa las dos cosas. Causa probable: el diff se calcula contra un
listado remoto viejo y el `revision_token` local no se actualiza solo. [MC]

**2 · El `pull` puede bajar el tema INCOMPLETO y decir `Download completed.`** ✅ Medido con tres
corridas el mismo día, en temporales limpios. [MC 2026-08-24]

| corrida | archivos bajados | salida | exit code |
|---|---|---|---|
| 11:11 | 305 de 344 | `Download completed.` | 0 |
| 11:12 | 305 de 344 | `Download completed.` | 0 |
| 11:23 | **344 de 344** | `Download completed.` | 0 |

Es **intermitente**, no determinista: las dos corridas cortas omitieron exactamente el mismo set
(diff vacío entre sí), lo que lleva a concluir mal que "el CLI siempre omite esos archivos". Doce
minutos después bajó todo. Del lado del dev el síntoma es un **500** en la consola del pull: el
CLI descarta esos requests en silencio y sigue. En GG un pull bajó 201 de 314 archivos y borró
archivos clave del working tree. [GG 2026-09-15]

**Consecuencia práctica: contar los archivos antes de creerle a un diff.**

```bash
find "$TMP" -type f ! -name '.nuvem' | wc -l    # tiene que dar el total esperado
```

El total esperado es **por instalación**: se mide al arrancar y se anota en el `CLAUDE.md` del
proyecto. Al leer el diff de un pull corto:

- **"solo está en el proyecto" NO significa "no está en el servidor"**: puede ser pérdida del
  pull;
- lo que **siempre** vale es lo contrario: **"Only in $TMP"** (el servidor tiene algo que el repo
  no) y los archivos que **difieren**.

## Leer el servidor sin escribir nada

- ✅ **`theme diff` es solo lectura** (pide la instalación y los hashes de sus archivos). Muestra
  qué cambiaría un push. Opciones: `--detailed`, `--json`, `--published`. [GG 2026-09-23]
- ✅ **El servidor guarda y devuelve los JSON minificados.** Por eso `theme diff` marca como
  "Modified" templates que son idénticos: hay que compararlos **parseados**, no como texto.
  `"settings": {}` y `"settings": []` son lo mismo. [GG 2026-09-23] [MC 2026-09-25]
- ✅ **Después de un push, la plataforma normaliza `"settings": {}` a `[]`.** Es cosmético:
  traelo al repo para que local y servidor queden idénticos. [MC 2026-09-25]
- ✅ **El editor también minifica, y descarta de `settings_data.json` lo que no esté adentro de
  `"settings"`.** Claves escritas en la raíz del JSON desaparecieron en el siguiente guardado del
  comerciante. [VZ 2026-09-29]
- ✅ **Se puede leer un archivo remoto directo por la API**, con el token de `.nuvem`:
  `GET https://api.nuvemshop.com.br/v1/<tienda>/theme-installations/<id>/files/<ruta>?parse-json=false`
  con el header `Authentication: bearer <token>`. Devuelve `{content: "<json>"}`. Sirve para mirar
  un solo archivo sin pullear. [GG 2026-09-23]
- La forma más completa sigue siendo un `theme pull` a un **directorio temporal** (copiando ahí
  `.nuvem` y `manifest.json`). El procedimiento está en [Sync y reglas](03-sync-y-reglas.md).

## Preview

- ✅ **Preview sin login:** `https://<dominio>/?preview_theme_installation_id=<id>` responde 200
  sin sesión, así que sirve para `curl`, Chrome DevTools y headless. En GG se usó con
  `storefront=core` adelante: `?storefront=core&preview_theme_installation_id=<id>`. Muestra lo
  **guardado** en el editor, no lo elegido sin guardar. [VZ 2026-09-23] [GG 2026-09-23]
- ⚠️ **`?theme_installation_id=<id>` (el que devuelve `theme preview`) necesita la sesión del
  admin.** Sin sesión, GG vio para siempre la pantalla "Estamos configurando…" y un `curl`
  devuelve el tema **publicado**. Esto corrige lo que se creía: el preview por `curl` no devuelve
  necesariamente el publicado, depende del parámetro. [GG]
- ⚠️ **El parámetro de preview no se propaga solo.** Un `fetch` a `?page=2` sin reenviar los
  parámetros trae el tema publicado, y los pedidos AJAX de la preview los puede responder el
  publicado. [VZ 2026-09-24] [GG]
- ⚠️ **Con dominio propio, el subdominio viejo puede morir.** `<tienda>.mitiendanube.com` pasó a
  responder **410 Gone**: no es una caída, el subdominio ya no existe, y la preview pasa al
  dominio propio. Al revés también engaña: un dominio propio puede seguir sirviendo la plataforma
  anterior. Para saber si un dominio sirve el tema, buscá `data-section-type` o
  `installations/<id>` en el HTML. [MC 2026-09-17]
- La barra que agrega la preview, el modo contraseña y cómo medir, en
  [Verificación y QA](15-verificacion-y-qa.md).

## CDN y caché de assets

- ✅ **Los assets se sirven con un hash en el nombre** (`…/themes/ipanema/<archivo>-<hash>.min.css`).
  Después de subir, el hash rota en unos 50 segundos, y la home puede seguir cacheada un rato
  más. [GG 2026-09-25]
- ⚠️ **Verificar en vivo justo después de subir puede mostrar los assets viejos.** Antes de dar
  un cambio por roto, confirmá que el hash del asset ya cambió. [MC 2026-09-11]

## Rate limits

El CLI reintenta solo ante un `429` y limita a **2 subidas concurrentes**. El smart push ahorra
cuota: evitá `--force` salvo que haga falta re-enviar todo.
