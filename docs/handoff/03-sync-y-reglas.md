# Sync y reglas del equipo

Cómo escribir en un tema Ipanema sin pisar lo que el comerciante configura desde el editor, y
las reglas de trabajo que salieron de romperlo. La **mecánica** del CLI (qué hace cada comando,
qué sube, qué baja y en qué miente) está en [Modelo y CLI](05-modelo-y-cli.md). Acá va el
**protocolo**: qué correr, en qué orden y por qué.

## Lo esencial

- La instalación es **una copia viva de la tienda de otra persona**. `templates/**` y
  `config/settings_data.json` los escribe el editor de la tienda, y `theme push` sincroniza
  eliminaciones: escribir sobre una copia vieja no pisa sus cambios, **los borra**.
- Antes de tocar un JSON del comerciante: `git status` (y `git pull --ff-only`) → ¿hay `watch`? → estado del servidor
  (pull a un temporal o `theme diff`) → comparar los JSON parseados → commitear aparte lo que
  cambió el comerciante → registrar el sync con `--stamp`.
- 🔥 **Nunca `theme pull` sobre la carpeta del proyecto con `theme watch` prendido.** El pull
  borra antes de descargar y watch replica los borrados en la tienda: así se cayó un borrador
  entero el 2026-09-23.
- Con watch prendido, **guardar es publicar**. Se valida antes de guardar: copia → chequeo →
  `mv`.
- El agente **nunca** corre `theme push`, `theme watch`, `theme publish` ni `theme fork`.
  Commits, pushes de git, ramas y deshacer: solo a pedido. Nunca `git add -A`.
- Antes de `publish`, comparar contra la productiva. Un borrador puede pasar a productivo sin
  que nadie avise: se verifica con `theme list`, no con lo que dice un README.
- Antes que escribir un archivo del comerciante, un fallback en Twig (`| default`, `?? true`).

## El modo de falla

El comerciante entra al editor cuando quiere: agrega una section al home, cambia un color,
reordena bloques, sube un logo. Cada una de esas acciones escribe archivos reales de la
instalación (`templates/**`, `config/settings_data.json`) que **solo existen ahí**, no en tu
repo. Si editás sobre una copia vieja y pusheás, pasan tres cosas, todas en silencio:

1. se **pisan** los valores que guardó después de tu último pull;
2. se **borran las sections que agregó**, porque el push sincroniza eliminaciones
   ([Modelo y CLI](05-modelo-y-cli.md));
3. **no hay deshacer**: el CLI no versiona. La única red es tu git, y solo si el estado remoto
   pasó por él.

Casos reales:

- 🔥 **Cuatro pérdidas en María Cher** [MC]: el `home.json` con una secuencia de banners, el
  `header.json` con tres URLs institucionales, el `logo_transparent` que el dev acababa de subir
  y un bloque de sello del footer con su link. Las cuatro se recuperaron desde un pull a un
  temporal hecho minutos antes: pura suerte.
- ⚠️ **Dos que casi pasan.** El repo tenía `page.Locales.json` con 6 locales y el servidor con
  17: un push se llevaba 11 [MC 2026-09-14]. En otra corrida, el `header.json` del repo tenía
  tres URLs apuntando a `/` [MC 2026-09-15].
- ✅ **El gate funcionando.** A los cinco días de arrancar, el pull trajo lo que el comerciante
  había editado (FAQ nuevas en tres páginas, la lista completa de locales, contacto, menús y
  créditos del footer, anuncios, el orden y las ocultas de la home, `page.json`). Se commiteó
  aparte antes de editar encima [VZ 2026-09-29].

## El protocolo, tal como se practica

Antes de la **primera escritura** sobre un JSON del comerciante, en cada tarea:

```bash
git status --porcelain                        # 1 · algo sin commitear → commit o stash
git pull --ff-only                            #     y los cambios de otros devs, si el repo tiene remoto
ps -Ao pid,command | grep "cli.js theme"      # 2 · ¿hay watch? y en qué carpeta:
lsof -a -p <pid> -d cwd                       #     lsof sobre el pid que apareció
# 3 · estado del servidor, SIN tocar la carpeta del proyecto:
TMP="$(mktemp -d)" && cp .nuvem manifest.json "$TMP"/ && (cd "$TMP" && tiendanube theme pull -y)
#     o, solo lectura: tiendanube theme diff --detailed
# 4 · contar archivos y comparar los JSON parseados (abajo)
# 5 · lo que cambió el comerciante se trae al repo y se commitea aparte
# 6 · registrar el sync para el hook del plugin
SC="$(ls -d ~/.claude/plugins/cache/nube-skills/nube-skills/*/ | sort -V | tail -1)skills/nube-skills-themes/scripts/sync-check.py"
python3 "$SC" . --stamp
```

**1 · Git limpio y al día.** Si el repo tiene remoto y trabaja más de un dev, `git pull --ff-only` trae lo de los demás antes que lo del servidor. El pull del tema sobrescribe, y con el CLI 2.3.1 además borra antes de descargar
([Modelo y CLI](05-modelo-y-cli.md)). Los pasos 1 y 3 son las dos caras del mismo riesgo: **el 1
evita que el pull te borre a vos, el 3 evita que el push borre al comerciante.** Ninguno de los
dos avisa. Si hace falta un respaldo más fuerte que un commit, antes del pull:
`git diff HEAD > backup.patch` y una copia de lo que no está commiteado; se restaura con
`git restore --worktree .` [GG 2026-09-15].

**2 · ¿Hay watch?** Con `ps` alcanza para saber si hay un `theme watch` corriendo; con `lsof`
sabés **en qué carpeta** corre [GG 2026-09-23]. Si corre en la carpeta del proyecto, el pull no
se hace ahí bajo ninguna circunstancia. **No lo cortes por tu cuenta**: es el proceso del dev.
Este paso se agregó después del incidente del 2026-09-23: la advertencia ya estaba escrita y no
alcanzó ([El incidente](#el-incidente-del-2026-09-23) más abajo).

**3 · El estado del servidor.** Un `theme pull` a un **directorio temporal** (copiando ahí
`.nuvem` y `manifest.json`, con `-y`) es la lectura completa y la que se usó siempre en la
práctica: 146 de 146 pulls del agente en MC y VZ fueron a un temporal [relevado 2026-09-30]. Para
saber solo qué cambiaría un push, `theme diff --detailed`, que es solo lectura. Las dos formas,
y la lectura directa de un archivo por la API, están en [Modelo y CLI](05-modelo-y-cli.md).

⚠️ **El `cwd` del shell persiste entre comandos.** Si quedaste parado en el temporal,
`diff -rq . $TMP` compara ese directorio consigo mismo y da **vacío**: un falso OK que ya pasó
[MC]. Subshell (`( cd "$TMP" && … )`), rutas absolutas o `git -C` en cada comando.

**4 · Contar y comparar parseado.** El pull puede bajar el tema incompleto y decir
`Download completed.`: primero se cuentan los archivos contra el total del servidor anotado en el
`CLAUDE.md` ([Modelo y CLI](05-modelo-y-cli.md)). Después, como el servidor devuelve los JSON
minificados, se comparan **parseados**, no como texto:

```bash
python3 - "$TMP" <<'PY'
import json, sys, pathlib
tmp = pathlib.Path(sys.argv[1])
for f in sorted(tmp.glob('templates/**/*.json')) + [tmp / 'config/settings_data.json']:
    rel = f.relative_to(tmp)
    if not rel.exists():
        print('SOLO EN EL SERVIDOR', rel); continue
    if json.loads(f.read_text()) != json.loads(rel.read_text()):
        print('DIFIERE', rel)
PY
```

"Solo en el servidor" y "difiere" **siempre** valen. "Solo en el proyecto" puede ser un pull que
vino corto: no lo tomes como "no está en el servidor".

**5 · Traer lo del comerciante y commitearlo aparte**, antes de editar encima. Se copia desde el
temporal conservando la indentación que ya tiene el archivo en el repo (el del servidor viene
minificado) [GG 2026-09-23]:

```bash
git add templates config/settings_data.json
git commit -m "chore: sync cambios del comerciante (installation <id>)"
```

**6 · `--stamp`.** El hook del plugin registra el pull **donde corrió**, o sea en el temporal, no
en el proyecto. Después de comparar, se registra a mano en el proyecto con `sync-check.py
--stamp` para que el hook deje escribir ([Skills](02-skills.md)).

### Cuándo correrlo

- **Antes de tocar un JSON del comerciante que vas a modificar.** El dev lo acotó así: *"no hagas
  pull de ningún .json a menos que los tengas que modificar. Crea page.Locales.json sin miedo"*
  [MC 2026-08-27]. Crear un archivo nuevo no necesita el gate, pero conviene confirmar en el
  temporal que el comerciante no lo creó desde el Admin. El hook lo bloquea igual
  ([Skills](02-skills.md)).
- **Por tarea, no por día.** Y de nuevo si pasaron más de ~30 minutos, hubo una reunión o una
  demo, o retomás una tarea de ayer.
- **Para leer o auditar no hace falta.** El gate protege escrituras.

## Editar un JSON del comerciante con watch prendido

Con watch corriendo, cada guardado del archivo se sube en el acto. La forma que evitó pisar siete
cambios del comerciante en un `home.json` [GG 2026-09-23]:

1. bajar el remoto (pull a un temporal, o la lectura directa por la API de
   [Modelo y CLI](05-modelo-y-cli.md));
2. escribir en local **el remoto más tu clave**, nada más;
3. justo antes de guardar, volver a bajar el remoto y **abortar si cambió**;
4. después de guardar, leer el servidor y verificar que quedó "idéntico más tu clave".

Para commitear por separado sin que watch suba versiones intermedias, se stagean blobs sin tocar
el working tree (ver [Commits](#commits) más abajo).

## Antes que escribir un archivo del comerciante: un fallback en Twig

La práctica que terminó quedando en MC: si un valor tiene que verse, **el default real va en el
Twig**, no en `settings_data.json` ni en `templates/**` [MC 2026-09-21].

- Un setting global declarado solo en `config/settings_schema.json` (que es código y el gate no
  cubre) se lee con `settings.x | default('…')`.
- Un toggle que tiene que arrancar prendido se lee con `?? true`, no con `| default(true)`: el
  `default` trata el `false` guardado como vacío.
- Si igual hay que escribir un archivo del comerciante: pull a un temporal, comparar byte a byte
  y **editar sobre la versión del servidor** [MC 2026-09-16].

Cuándo llegan y cuándo no los defaults del schema, en
[Schema y traducciones](06-schema-y-traducciones.md).

## Leer el diff del pull

| Lo que ves | Quién lo hizo | Qué hacer |
|---|---|---|
| Entrada nueva en `sections` + su id en `order` de un `pages/*.json` | el comerciante agregó una section | **no la toques**: commiteala y trabajá alrededor |
| Valores distintos dentro de `settings` de una section | la configuró él | su valor gana sobre tu default |
| `settings_data.json` con otros colores o tipografías | ajustó la identidad visual | nunca lo reviertas "para que coincida con el diseño": avisá |
| Cambios en `sections/`, `blocks/`, `static/`, `layouts/` | **sin fork**: una actualización de Ipanema. **Con fork**: otro dev | sin fork, no la revientes con tu versión vieja |
| El archivo entero cambiado, pero parseado es igual | el servidor lo minificó | ruido: comparar parseado ([Modelo y CLI](05-modelo-y-cli.md)) |
| Claves que estaban en la raíz de `settings_data.json` desaparecieron | el editor descarta lo que no está dentro de `"settings"` | escribirlas dentro de `"settings"` |
| Solo `manifest.json` (`revision_token`) | el propio pull | ruido esperable |
| `"disabled": true` a nivel de section | el toggle "ocultar sección" del editor | es decisión de quien lo tocó: se respeta |

## Reconciliar un conflicto

1. **El valor guardado por el comerciante gana por default.** Es su tienda y lo eligió después de
   tu último pull.
2. **No mergees a ojo.** Mostrá los dos valores ("el diseño pide 48, el comerciante guardó 24") y
   esperá la decisión.
3. **Un conflicto de git en un JSON template no lo resolvés vos.** Son archivos generados por un
   editor: un merge manual mezcla estados que nunca existieron.
4. **Nunca resuelvas nada con `push --force`.** No resuelve: reemplaza la instalación con tu
   copia, eliminaciones incluidas.

## Publicar

`publish` es el momento más destructivo del ciclo, y el gate normal **no lo cubre**: tu borrador
puede estar sincronizado consigo mismo mientras el comerciante configuraba la productiva.

```bash
tiendanube theme list                       # ¿cuál es la productiva? ¿es la mía?
P="$(mktemp -d)" && cp .nuvem "$P"/ && (cd "$P" && tiendanube theme pull --published -y)
diff -ru "$P/templates" templates
diff -u  "$P/config/settings_data.json" config/settings_data.json
```

Todo lo que aparezca en la productiva y no en tu borrador es trabajo que la publicación va a
borrar: **listalo y pedí confirmación explícita.** No es una decisión técnica. El hook del plugin
pide confirmación ante cualquier `theme publish` ([Skills](02-skills.md)), y lo que hay que
resolver en el Admin antes de publicar está en [Arranque](01-arranque.md).

🔥 **Un borrador puede pasar a productivo sin que nadie se entere.** En MC la instalación
"borrador" se publicó a mitad de camino y la documentación siguió diciendo borrador [MC]. En GG
se publicó entre el 23 y el 25 de septiembre, y una sesión le dijo al dev "quedó en el borrador"
cuando ya era producción; nadie corrió el gate de publish [GG 2026-09-25]. **Verificalo con
`theme list` al empezar cada sesión**, no con lo que dice el `CLAUDE.md`.

## El incidente del 2026-09-23

Lo que pasó en GG el día que el proyecto cambió de manos, en hora de Argentina
[GG 2026-09-23]:

- **09:55** — el dev deja `theme watch` corriendo en la carpeta del proyecto.
- **10:44** — el agente corre el gate tal como estaba escrito: `theme pull --yes` sobre esa
  carpeta. El CLI 2.3.1 borra los 340 archivos sincronizados y el GET falla con un 500, dos veces.
  El agente restaura con `git restore`, dos veces.
- Para entonces watch ya había mandado los borrados a la instalación. La re-subida (en paralelo y
  sin reintentos) dejó **93 archivos afuera**. `layout.tpl` incluía cuatro de ellos: **500 en
  todo el borrador.**
- El agente siguió trabajando convencido de que no había subido nada, hasta que el dev avisó, a
  las 10:52.

**Cómo se recuperó:**

1. se leyó el código del CLI (`dist/cli.js`) para entender qué había hecho el pull;
2. `theme diff --detailed` (solo lectura) y comparación de los JSON parseados;
3. se cortó el watch;
4. se trajeron a local los `home.json` y `product.json` que había guardado el editor;
5. se confirmó con el diff que el push iba a **agregar 93, no borrar nada** y reescribir 34
   idénticos;
6. el dev corrió el push, a las 11:10;
7. verificación: 200 en home, ficha, categoría, búsqueda y `/comprar/`, y un diff sin faltantes.

**La regla que quedó:** con watch prendido nunca hay pull en esa carpeta; el sync pasa por un pull
a un temporal o por `theme diff`. Reiniciar watch es seguro, porque no sincroniza nada al
arrancar ([Modelo y CLI](05-modelo-y-cli.md)).

**La lección:** estaba escrito en dos lugares, en el handoff y en el mensaje de bloqueo del hook, y
aun así pasó. Una advertencia escrita no reemplaza a un chequeo que se corre: por eso el paso 2
del protocolo (`ps` + `lsof`) va antes de todo pull. VZ lo incorporó ese mismo día
[VZ 2026-09-23].

## Con watch prendido, guardar es publicar

- 🔥 **Lo que guardás está en vivo, código incluido.** En MC, `style-critical.css` y
  `product-image.tpl` salieron a la tienda productiva sin que el agente corriera ningún comando:
  se detectó porque cambió el hash del CSS en el CDN [MC 2026-09-17]. Con watch prendido, "el
  agente nunca pushea" no protege nada: cada escritura es un push. Decíselo al dev en cada
  entrega [GG].
- **Validar antes de guardar: copia → chequeo → `mv`.** Se edita una copia fuera del tema, se
  chequea y recién ahí se mueve, así watch nunca sube un archivo roto [MC 2026-09-10]:

  ```bash
  C="${TMPDIR:-/tmp}/store.check.js"
  cp static/js/store.js "$C"                          # editar la copia, no el original
  node --check "$C" && mv "$C" static/js/store.js
  ```

  Para Twig (sobre todo un snippet que cuelga del layout) se corren sobre la copia los chequeos
  de [Verificación y QA](15-verificacion-y-qa.md). Para JS, además, se puede probar la versión
  nueva en la página real antes de copiarla [GG 2026-09-25].
- **El orden de guardado importa:** traducciones → CSS → snippet → schema. Un `{% if %}` sin
  cerrar en un guardado intermedio llegó a subir [GG 2026-09-24].
- **Nada de copiar muchos archivos de golpe:** watch saltea archivos en ráfaga
  ([Modelo y CLI](05-modelo-y-cli.md)). Se guardan de a uno y se verifica con un pull a un
  temporal.
- 🔥 **Nunca `git checkout` de otra rama con watch prendido.** El checkout reescribe el working
  tree y watch pushea eso a la tienda: se van en vivo versiones viejas [MC].
- Después de cada subida del dev, refrescar el `revision_token` ([Modelo y CLI](05-modelo-y-cli.md)).
- La cara buena: con el watch del dev prendido, **lo que escribiste se puede medir en vivo** sin
  correr nada. Decí siempre contra qué se midió y qué queda por subir
  ([Verificación y QA](15-verificacion-y-qa.md)).

## Anti-patrones

| Anti-patrón | Por qué duele |
|---|---|
| `theme pull` sobre el proyecto con watch prendido | el pull borra antes de descargar y watch replica los borrados en la tienda (el incidente de arriba) |
| `push --force` sin pull previo | reemplaza la instalación con tu copia vieja, eliminaciones incluidas |
| `theme pull` con cambios sin commitear | la otra cara del mismo error: perdés tu trabajo, sin confirmación |
| Editar `settings_data.json` "para dejar el diseño como el boceto" | es el estado del editor del comerciante. Los defaults del diseño van en el schema o en un fallback de Twig |
| Asumir que "el comerciante no toca nada" | es su tienda y el editor es para eso |
| Correr el gate una vez al empezar el día | se corre **por tarea** |
| `theme watch` + `git checkout` de otra rama | el checkout reescribe el working tree y watch lo publica |
| El agente usando `NUBE_SKIP_SYNC_GATE=1`, o escribiendo un JSON del comerciante por Bash para que el hook no lo vea | el escape es del dev, y el bloqueo protege datos de alguien que no está en la conversación. Pasó: un JSON de plantilla escrito así por Bash [MC 2026-09-15] |
| Seguir la sugerencia del CLI de `theme pull --theme-id` en un proyecto que ya tiene trabajo | pisa el trabajo local. Si falta el id, se escribe `themeId` en `.nuvem` ([Modelo y CLI](05-modelo-y-cli.md)) |

## Reglas duras del equipo

Estas reglas van escritas en el `CLAUDE.md` de cada proyecto (la
[plantilla](plantillas/CLAUDE.md) ya las trae) y conviene tenerlas además como memorias sueltas,
linkeadas entre sí: no son documentación del tema, son cómo se trabaja.

- 🚫 **El agente nunca ejecuta `theme push`, `theme watch`, `theme publish` ni `theme fork`.** Los
  cambios quedan en el working tree y los sube el dev dueño de la tienda, porque el push sube todo,
  no solo lo que tocaste. *"recuerda que no tienes que hacer push de nada. yo tengo el watch
  prendido"* [MC 2026-09-10]. El fork se sumó a la lista en VZ [VZ 2026-09-23].
- 🚫 **Nunca crear una rama de git sin permiso explícito.** En GG se trabajó en una rama
  `feature/design` con PR, con permiso: la regla es de permiso, no de que no haya ramas. Ojo que el
  resumen de la sesión decía `main` y confundió al dev en pleno incidente [GG 2026-09-23]. Para
  mover `main` sin tocar el working tree (seguro con watch prendido): `git branch -f main
  <rama-al-día>`, solo si es fast-forward. Si aparece una rama ajena, se ofrece mergearla y no se
  borra [MC].
- 🚫 **Cada commit y cada push de git se piden explícitamente.** *"nunca hagas commit sin que yo
  te lo pida. es una regla general"* [VZ 2026-09-24]. Un "hacé commit y push" vale para ese
  momento, no queda abierto. **Deshacer también se pide** (`revert`, `reset`, un force-push): ante
  la duda, preguntar; dudar y resolver actuando es el error [MC 2026-09-18].
- 🚫 **Nunca `git add -A`.** Se stagea por archivo, y solo lo propio: puede haber otra sesión o
  el dev trabajando sobre el mismo árbol.
- 🚫 **No esconder contenido que cargó el comerciante.** Si un banner sin foto se ve mal, se
  **diseña ese estado** (oscurecer el fondo, reforzar el degradado), no se agrega un `{% if %}` que
  lo haga desaparecer. Pasó dos veces y las dos estuvo mal [MC].

  | | Qué hacer |
  |---|---|
  | texto que **inventó el tema** (un `default` de schema, un placeholder, lorem) | sacarlo, siempre |
  | contenido que **cargó el comerciante**, aunque esté a medio completar | mostrarlo, y diseñar ese estado |

  Matiz: esconder es válido **si lo pide el dev o el cliente**, y queda documentado con la forma
  de hacerlo volver (en GG, los productos sin fotos en el buscador y los colores sin stock o sin
  foto) [GG].
- **Toda section nueva se registra en el JSON de su página con contenido y visible**: settings
  cargadas con copy real de la marca (nunca lorem), fotos de la biblioteca (`@media-lib:<uuid>`,
  se copian de los `templates/pages/*.json` existentes), URLs reales, sin `disabled`. Una section
  registrada vacía no se dibuja, por las guardas de "sin contenido no renderizo", y el dev no
  tiene nada que revisar [MC].
- 🚫 **Los tokens nunca se imprimen ni se guardan en un comando que quede escrito**, tampoco en
  `permissions.allow` ([Límites y Admin API](13-limites-y-admin-api.md)).
- **Al terminar una tarea:** listar los archivos modificados y decir qué hay para subir. Si un
  template del repo quedó viejo respecto del servidor, avisarlo en vez de pisarlo. Y decir qué
  copy propuso el agente, para que el cliente lo ajuste [MC].

## Commits

- **Los cambios del editor van en su propio commit, y primero**; el commit de documentación va
  último [GG].
- **Un commit por página o feature**, con los archivos compartidos partidos por sección: CSS por
  sus encabezados de pieza, `store.js` por función, las traducciones según qué archivo usa cada
  clave [VZ 2026-09-24]. Cada contenido intermedio se arma a mano y se stagea sin tocar el working
  tree (que además evita que watch suba versiones intermedias [GG 2026-09-23]):

  ```bash
  # el contenido intermedio se arma en un archivo fuera del tema
  blob=$(git hash-object -w "${TMPDIR:-/tmp}/intermedio/style-critical.css")
  git update-index --cacheinfo 100644,"$blob",static/css/style-critical.css
  ```

  ⚠️ **Fijá la base del diff en el commit de partida.** Recalcular `git diff HEAD` después de cada
  commit re-alinea bloques de CSS parecidos y mete secciones en el commit equivocado: pasó una vez
  y hubo que rehacerlos [VZ 2026-09-24]. La condición previa es que cada pieza tenga su encabezado
  en los archivos compartidos.
- **Nunca un commit que quede roto por sí solo**: CSS y JS que referencian markup nuevo van en el
  mismo commit que ese markup [MC].
- **El trabajo en curso de otra sesión se commitea aparte**, descripto por su diff y rotulado "no
  lo escribí ni lo verifiqué" [MC].
- Commits periódicos de sync del editor (`chore: pull de la config del editor`), que dejan
  explícito que la versión del servidor manda [MC].

## Sesiones paralelas

Es común trabajar el mismo tema con varias sesiones de Claude a la vez, una por página
[VZ 2026-09-24]. Chocan en `style-critical.css`, `style-async.css`, `store.js`, las traducciones y
el `CLAUDE.md`.

- **Ediciones quirúrgicas sobre un anclaje único.** Nunca leer un archivo compartido, editarlo en
  memoria y escribirlo entero: una escritura completa desde una lectura vieja borra el trabajo de
  la otra sesión. En MC aparecieron 11 archivos modificados a mitad de sesión que no eran propios
  [MC 2026-09-18].
- **Verificar que cada diff sea propio antes de commitear.** En GG aparecieron hunks ajenos en el
  mismo archivo, una sesión cerró el Chrome de otra, y un prompt de otro proyecto cayó en esta
  [GG 2026-09-23].
- El navegador del MCP de chrome-devtools lo toma la primera sesión: qué hacer desde las otras,
  en [Verificación y QA](15-verificacion-y-qa.md). Cómo organizar las sesiones (un `ESTADO` común,
  encabezados por pieza), en [Arranque](01-arranque.md).
