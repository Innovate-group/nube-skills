# Varias tiendas, apps propias e integraciones

Lo que aparece cuando el tema no está solo: un cliente con una tienda por país, una app de
gestión propia que cubre lo que el tema no puede, y apps de terceros o servicios externos que se
enganchan al storefront. Casi todo sale de María Cher, que opera tres tiendas (Argentina, Chile y
Uruguay) con una app de gestión en cada una.

## Lo esencial

- **Un cliente con tiendas en varios países son varias tiendas Tienda Nube independientes:** un
  repo de tema por país, y una app de gestión por país si la hay.
- 🔥 **Clonar el tema a otro país clona los endpoints propios y la configuración de la tienda de
  origen.** Es lo primero que se revisa: un host equivocado no falla, escribe datos de clientes en
  la tienda equivocada.
- **Los cambios se portan con `git format-patch` + `git apply`, nunca con un `cp` masivo**, y se
  verifican tienda por tienda con un pull a un temporal.
- **Una app de gestión resuelve lo que el tema no puede.** Escribe datos que el tema lee sin
  depender de nada en runtime (tags, metacampos, custom fields, el orden de las categorías) y
  expone pocas rutas públicas para las acciones del comprador.
- **El tema llama a la app con URLs configurables y degrada sin romper** si la app está caída.
- **Un `git push` exitoso de la app no es un deploy exitoso:** hay que esperar la CI y mirar el
  resultado.
- **Una app de terceros se integra escondiendo su control y disparándolo desde uno propio.** Nunca
  con `display: none` en su contenedor.

## Un cliente con tiendas en varios países

### Cómo queda armado

María Cher tiene **tres tiendas independientes**, cada una **productiva y sin borrador**, y
**cada una con su propio repo de tema** *[MC 2026-09-22]*:

- Chile y Uruguay se clonaron del repo argentino y comparten historia hasta un commit común.
- Cada una tiene un commit de adaptación que solo reapunta la identidad: los endpoints, el locale
  de referencia y el `CLAUDE.md`.
- Los cambios posteriores se portan desde Argentina, citando el commit de origen en el mensaje
  ("Mismo cambio que `<sha>`").
- **El código del tema es idéntico entre países, y ya es country-aware:** `store.afip` solo se
  completa en tiendas argentinas, y la ayuda de código postal del calculador de envío solo aparece
  para Brasil, Argentina y México. Lo que difiere entre países es la configuración (los templates
  y `settings_data.json`), que es del comerciante y vive en cada servidor.
- Ipanema puede tener una versión distinta en cada tienda (en MC: 1.0.0, 1.2.1 y 1.2.2), con
  archivos de fábrica distintos ([CLI y modelo](05-modelo-y-cli.md)).

### La identidad se lee del servidor, no se deduce

Antes de tocar un hermano: `theme list`, `theme current`, un pull a un temporal, el `<html lang>`
de la tienda y su moneda *[MC 2026-09-22]*.

- ✅ **El locale de referencia se mide en cada tienda** *[MC 2026-09-22]*. Chile sirve `es-CL` y
  CLP, así que la referencia es `es_CL`. Uruguay sirve `es-AR` porque **no existe `es_UY`**, así
  que queda `es_AR`, cuyo voseo coincide con el uruguayo. El detalle de traducciones está en
  [schema y traducciones](06-schema-y-traducciones.md).
- ⚠️ **Uruguay tenía la moneda en ARS** *[MC 2026-09-22]*. Pasar a UYU cambia también los
  separadores de miles y de decimales. Es configuración del Admin: se confirma antes de abrir.
- ⚠️ **Chile y Uruguay son productivas sin borrador**, con 2 instalaciones contando la legacy: no
  se puede crear ninguna más, y la única red es git.

### 🔥 Clonar el tema clona los endpoints

✅ *[MC 2026-09-22]* En los hermanos recién clonados, la wishlist (enganchada desde `layout.tpl`,
o sea en todas las páginas), el flag de compra asistida y la subida del CV **posteaban a la app
argentina**. La app resuelve la tienda como "la primera instalada" si no le llega un `store_id`, y
el tema no lo manda: **un host equivocado no falla, escribe datos de clientes en la tienda
equivocada**.

**Es lo primero que se revisa al clonar:** buscar los hosts de las apps propias en `layouts/`,
`sections/`, `snippets/`, `static/js/` y en los `default` de los settings `url`. Los endpoints
propios suelen ir como setting con un `| default('https://…')` en Twig, que es cómodo y justo por
eso es la trampa número uno al clonar.

### 🔥 Clonar el tema clona la configuración de la tienda de origen

✅ *[MC 2026-09-22]* Con los templates y `settings_data.json` viaja el contenido local del país de
origen:

- el sello Data Fiscal de AFIP;
- términos y políticas con C.U.I.T., cuando Chile y Uruguay usan RUT;
- el botón de arrepentimiento, que es una obligación de la ley argentina;
- los locales físicos del país de origen;
- links al subdominio viejo, que ya no responde;
- assets en el almacenamiento de la otra tienda, que responden 200, así que la dependencia no se
  nota;
- las referencias `@media-lib:<uuid>`, que son de la biblioteca de la otra tienda y en la nueva no
  existen.

Si la configuración ya está subida (el caso de Chile), es del comerciante: se corrige desde el
editor. Si el servidor está virgen (el caso de Uruguay), se corrige en el repo antes de la primera
subida.

### La primera subida sobre un Ipanema de fábrica más nuevo

✅ *[MC 2026-09-22]* En Uruguay, antes de la primera subida, diferían 129 archivos entre el repo
y el servidor: 97 estaban solo en el repo y 11 solo en el servidor, porque la instalación de
fábrica era una versión más nueva de Ipanema. **Hay que decidir qué pasa con esos 11 antes del
push**, porque el push sincroniza eliminaciones ([sync](03-sync-y-reglas.md)). Uno de ellos era
una plantilla de cuenta que referencia una section que el repo no tenía.

### Portar cambios entre países

- **`git format-patch -1 <sha>` y `git apply` en el hermano.** El conflicto sirve de alarma: si el
  patch toca líneas propias del país, falla en vez de pisarlas.
- 🔥 **Un `cp` masivo pisa las líneas propias de cada país** (en MC: `layout.tpl`, el registro, la
  página de empleo y `store.js`, que tienen el endpoint del país) **y dispara la ráfaga que
  `theme watch` saltea.** ✅ *[MC 2026-09-28]*: se copiaron 22 archivos en loop a los dos
  hermanos; Uruguay subió 21 y Chile 20, sin ningún aviso. Los que faltaron se re-guardaron de a
  uno ([CLI y modelo](05-modelo-y-cli.md)).
- **Después de portar, un pull a un temporal por tienda**, comparando cada archivo de
  `git diff --name-only`.
- **Antes de subir a una productiva sin borrador**, el chequeo que se usó en Chile y Uruguay
  *[MC 2026-09-25]*:
  1. pull a un temporal dos veces, contando archivos;
  2. comparar los JSON parseados;
  3. traer al repo lo que está solo en el servidor o difiere, en un commit
     `chore: sync cambios del comerciante`.
- ⚠️ **El hook `sync-gate` resuelve el `theme push` por el cwd de la sesión** *[MC 2026-09-25]*.
  Desde una sesión abierta en el repo argentino, un push a Chile o Uruguay queda bloqueado aunque
  el pull del hermano esté hecho. No se esquiva registrando un pull en el repo equivocado: el push
  de cada hermano lo corre el dev desde la carpeta de ese hermano ([skills](02-skills.md)).
- **Las mediciones heredadas se avisan.** El `CLAUDE.md` de cada hermano abre diciendo que todo lo
  marcado como medido se midió en otra tienda y sobre otra versión, y que los ids, handles y `@media-lib`
  son del catálogo de origen. Es un buen modelo para copiar.

## La app de gestión del estudio

### Qué es

Una app embebida en el Admin de la tienda, que corre en infraestructura del estudio *[MC]*:
Express + TypeScript, React + Vite + Nimbus, Postgres con Prisma y el almacenamiento del servicio
de archivos del estudio. Hay **un deployment por tienda**, con su repo, su servidor, su base, su
app y su dominio.

- **Tienda Nube sigue siendo la fuente de verdad.** La app escribe tags, metacampos y custom
  fields; no guarda una copia paralela del catálogo.
- **Es mono-tienda:** resuelve "la primera tienda instalada". Por eso **el endpoint que tiene
  configurado el tema es el que decide adónde van los datos** (ver "Clonar el tema clona los
  endpoints").

### Qué resuelve para el tema

- **El espejo de la wishlist** *[MC 2026-09-10]*. Con sesión, un `/sync` por carga, donde gana la
  última escritura, con lápidas, y ante empate gana el remoto. Anónimo, solo un contador de
  demanda con un identificador hasheado. Además mide ranking y conversión; la conversión necesita
  el scope `read_orders` ([límites](13-limites-y-admin-api.md)). La parte del tema está en
  [JavaScript](11-javascript.md).
- **Un flag de cliente en un custom field** *[MC 2026-08-28]*, porque `extra` se descarta
  ([límites](13-limites-y-admin-api.md)). Tiene dos modos:
  - por email, solo si el cliente se creó hace menos de 15 minutos: justo después del alta, y
    como la tienda exige validar el email, no hay sesión;
  - por `customer_id` + email, con sesión.

  La ventana es lo que evita que alguien marque a cualquiera con un mail ajeno.
- **La subida pública de PDF desde formularios** *[MC]*:
  - valida por los bytes (`%PDF-`), no por la extensión;
  - la key la genera el servidor, así el cliente no elige ni nombre ni ruta;
  - fuerza `Content-Disposition: attachment`;
  - tiene rate limit.
- **Metacampos `pdp.*`**, cucardas y familias por tags (`badge-*`, familias de color), y el orden
  visual de las categorías, por re-inserción ([límites](13-limites-y-admin-api.md)).
- **El despacho centralizado** con Business Rules privadas, solo en Argentina
  ([límites](13-limites-y-admin-api.md)).

### Cómo se conecta con el tema

- **Los datos de catálogo van por tags y metacampos**, que el tema lee sin depender de la app en
  runtime. Se eligieron tags en vez de un widget justamente para no depender del servidor de la
  app. Por endpoint van **solo las acciones del comprador**.
- **URLs configurables:** un setting global (el tema lo emite como `data-*` en el `<html>`) y
  settings de section.
- **Todo aditivo y en `try/catch`:** `fetch` con `credentials: 'omit'` y sin `X-Requested-With`.
  Vacío o caído no rompe nada (`if (!endpoint) return`, `{% if … and endpoint %}`).
- ⚠️ **Un payload mal armado vuelve `200 {"items":[]}` y se descarta en silencio** *[MC 2026-09-10]*.
  La verificación es que la respuesta traiga los ítems, no el 200.
- ⚠️ `product.url` de Twig viene **absoluta**, y la API de la wishlist solo acepta rutas que
  empiezan con `/` *[MC]*.
- **Las rutas públicas de escritura tienen rate limit en memoria**, y un test de allowlist falla
  si aparece una ruta pública nueva *[MC]*. Ojo: si la app pasa a varios workers, el tope real se
  multiplica por la cantidad de workers.
- **El orden de despliegue app ↔ tema** *[MC 2026-09]*. Cuando el tema y la app comparten un número
  (en MC, el tamaño del lote de la grilla), el de la app nunca puede superar al del tema. Al
  subirlo se publica primero el tema; al bajarlo, primero la app, con su deploy verificado antes
  de tocar el tema.

## CI y deploy de las apps

- 🔥 **Verificar la CI después de pushear** *[MC 2026-09-17]*. Un `git push` exitoso no es un
  deploy exitoso. Se espera la corrida y se lee el resultado:

  ```bash
  until [ "$(gh run view <id> --json status --jq .status)" = completed ]; do sleep 20; done
  gh run view <id> --json conclusion --jq .conclusion
  gh run view <id> --log-failed   # si falló
  ```

  Mejor todavía, verificar el artefacto servido. Ojo: el JS deployado tiene otro hash que el build
  local, porque el servidor le inlinea su `.env`.
- 🔥 **Un servidor de 1,9 GB sin swap** *[MC 2026-09-17]*. El `vite build` hizo que el kernel
  matara el job por memoria (exit 137). El runner self-hosted quedó `failed`/`offline`, porque es
  la víctima preferida del OOM killer, y los deploys siguientes se acumularon en `queued` mientras
  la app seguía respondiendo, lo que engaña. El diagnóstico:
  - `gh run list`;
  - `gh api repos/<org>/<repo>/actions/runners`;
  - `sudo systemctl start 'actions.runner.*'`;
  - `journalctl -k | grep -i killed`.

  Se agregaron 2 GB de swap. El arreglo de fondo, pendiente, es compilar en la CI y subir el
  `dist` como artefacto.
- 🔥 **La CI tiene que hacer exactamente lo mismo que el deploy** *[MC 2026-09-04]*:
  - `yarn workspace frontend build` (tsc + vite): `vite build` solo se saltea el type-check;
  - un `prisma generate` explícito, porque `ts-node` type-checkea al arrancar y un modelo nuevo
    sin generar da crash-loop y 502;
  - `concurrency` con `cancel-in-progress: false`.
- **Runner self-hosted:** un label por país, para que un push no despliegue en el servidor de otro,
  y el repo tiene que ser privado *[MC]*.
- ✅ **Los baches del provisioning**, medidos al levantar la app de Chile *[MC 2026-09-22]*:
  - una instancia micro no alcanza: hace falta una small más 4 GB de swap;
  - `gh` no está en los repos de Ubuntu: va con `snap install gh --classic`, y `gh auth` como el
    usuario del sistema, sin sudo;
  - sin `CLIENT_EMAIL`, todo endpoint responde 500;
  - si `SECRET_KEY` no es igual al `CLIENT_SECRET`, todo request embebido da 401.
- ⚠️ **nginx saca el prefijo `/api/`** *[MC]*. El Admin Link y los callbacks terminan en `/api`,
  pero la ruta de Express no lo lleva. Si sale mal, el síntoma es que nada funciona y no hay un
  solo error visible.
- **Los backups de la base van a un disco local**, no al bucket, porque el bucket es de lectura
  pública y el dump tiene el access token de la tienda *[MC]*.
- **Una ruta que recibe archivos por multipart necesita `client_max_body_size` en nginx** *[MC]*.
  El script de provisioning lo escribe, pero en un servidor ya provisionado hay que aplicarlo a
  mano. Es la misma trampa que tiene el servicio de archivos (ver abajo).

## Apps de terceros

### Esconder su control y dispararlo desde uno propio

✅ Así se integró stocknube *[MC 2026-09-11]*:

- **Esperar la inyección.** Las apps inyectan por JS: su contenedor no viene en el HTML del
  servidor. Se usa un `MutationObserver` que se desconecta al encontrarlo y marca
  `<html data-…="ready">`, o se delega en `document` y se busca el botón de la app recién en el
  momento del click.
- **Elegir primero la variante**, dejando que el click burbujee, porque la app rotula su aviso con
  la variante elegida. Después se espera su señal, hasta 1,5 s.
- **En mobile, si el diseño no tiene chips de talle, se deja el botón de la app.**
- 🔥 **El contenedor de la app se corre fuera de pantalla** (`position: absolute; left: -9999px`),
  nunca `display: none`: un `<dialog>` del top layer con un ancestro oculto abre en 0×0
  ([plataforma](08-plataforma.md)).

### Neutralizar una app que compite

Cuando el tema reemplaza una función que ya tenía una app instalada (en MC, otra app de wishlist)
*[MC 2026-09]*:

- `display: none !important`, **nunca `pointer-events: none`**: la app se dibujaba en el mismo
  lugar que el corazón propio, su glifo quedaba encima y le robaba el click;
- barrer sus elementos por prefijo de id (`[id^=…]`) destapó un widget flotante de la app que
  estaba visible en producción;
- si la app reescribe su propio `innerHTML`, se envuelve su global en vez de pelear con el DOM.

### Google Maps

- 🔥 ✅ **La allowlist de la key por referrer se evalúa contra el host de cada visita**
  *[MC 2026-09-18]*. El dominio sin `www`, el `www` y el `*.mitiendanube.com` son entradas
  distintas. Si falta el host canónico, el mapa se rompe para la mayoría de las visitas, y de
  forma determinista según la URL. Desde el shell no se puede leer la allowlist: se la pide al
  dueño de la key.
- ⚠️ **Un rechazo de la key no llega al `.catch`.** El aviso es `window.gm_authFailure`, que hay
  que definir **antes** de inyectar el script, encadenando el handler que hubiera.
- ⚠️ **Sin `v=`, el SDK va por el canal weekly**, y `google.maps.Marker` está deprecado.
- ✅ **Sin Map ID** *[VZ 2026-09-24]*: `AdvancedMarkerElement` exige un Map ID, así que los pines
  van con un `OverlayView` propio, con `loading=async` + `importLibrary`. Si `gm_authFailure`
  salta, el respaldo es un iframe de Google Maps sin clave. La key queda en el HTML: se restringe
  por referrer.

## El servicio de archivos del estudio

Para formularios del storefront que necesitan un archivo (un CV, un comprobante), porque la ruta
de contacto de la plataforma no acepta adjuntos ([límites](13-limites-y-admin-api.md)). La URL del
endpoint no va en este documento, porque el repo es público y el endpoint acepta subidas sin
token: está en el repo del servicio y en el `CLAUDE.md` del proyecto que lo usa.

✅ Medido *[VZ 2026-09-24]*:

- **No usa token: identifica la tienda por el header `Origin`.** La app del servicio tiene que
  estar instalada en esa tienda.
- **Un archivo por pedido, en el campo multipart `file`.** La extensión y el MIME tienen que
  coincidir exactamente: jpg o png hasta 3 MB, pdf hasta 10 MB.
- **Responde `201` con `url`, `key`, `name`, `size` y `contentType`.** Límites: 10 por minuto por
  IP y 60 por hora por tienda (429).
- 🔥 **El nginx de producción corta en 1 MB.** Un archivo de 900 KB entra y uno de 1,1 MB recibe
  un 413 de nginx **sin headers CORS**, que el navegador ve como un error de red y no como un 413.
  Falta `client_max_body_size`. Verificarlo con `curl` antes de asumir que se arregló.
- La ruta de contacto no lleva archivos, así que **la URL devuelta viaja dentro del mensaje**
  ([plataforma](08-plataforma.md)).
