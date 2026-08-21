# Sync antes de escribir (y cómo reconciliar conflictos)

Protocolo para no pisar el trabajo del comerciante ni el de otro dev al escribir archivos de un tema sectionable. Cubre el **gate** previo a la primera escritura, cómo leer el diff que trae un `theme pull`, cómo reconciliar un conflicto, el gate extra antes de `theme publish`, y los casos borde (sin git, con `theme watch` corriendo, sin fork).

## Tabla de contenidos

1. [El modo de falla](#1-el-modo-de-falla)
2. [Quién escribe qué](#2-quién-escribe-qué)
3. [El gate](#3-el-gate)
4. [Cuándo se corre](#4-cuándo-se-corre)
5. [Leer el diff del pull](#5-leer-el-diff-del-pull)
6. [Reconciliar un conflicto](#6-reconciliar-un-conflicto)
7. [El gate antes de publicar](#7-el-gate-antes-de-publicar)
8. [El script sync-check.py](#8-el-script-sync-checkpy)
9. [Anti-patrones](#9-anti-patrones)
10. [Casos borde](#10-casos-borde)

---

## 1. El modo de falla

La instalación de un tema es **una copia viva de la tienda de otra persona**. El comerciante entra al editor cuando quiere: agrega una sección al home, cambia un color global, reordena bloques. Cada una de esas acciones escribe archivos reales de la instalación (`templates/**`, `config/settings_data.json`).

Tu copia local viene de un `theme pull` que pasó **en algún momento**. Si editás sobre esa copia y pusheás, pasan tres cosas, todas silenciosas:

1. **Se pisan los valores** que el comerciante guardó después de tu último pull.
2. **Se borran las secciones que él agregó**: `theme push` sincroniza eliminaciones — los archivos y entradas que existen en el remoto y no en tu copia se eliminan de la instalación. Tu `templates/pages/home.json` viejo reemplaza el suyo nuevo, y las secciones que él sumó desaparecen del sitio.
3. **No hay deshacer.** El CLI no versiona: la única red de seguridad es tu repo git, y solo si el estado remoto pasó por él.

El mismo mecanismo aplica entre devs: el commit de un compañero que ya está en el remoto de git, o una actualización del tema base Ipanema que ya está en la instalación, se pierden igual.

Regla base: **una escritura sobre una copia que no acabás de sincronizar es una escritura a ciegas.**

## 2. Quién escribe qué

| Archivo / carpeta | Quién más lo escribe | Qué se pierde si escribís con copia vieja |
|---|---|---|
| `templates/pages/*.json` | El comerciante desde el editor: qué secciones tiene la página, su `order`, sus settings, sus blocks | Su configuración y las secciones que agregó |
| `templates/layout/header.json`, `footer.json` | Ídem, para header y footer de todas las páginas | Ídem, con impacto en el sitio entero |
| `config/settings_data.json` | El comerciante desde el editor: colores, tipografías, logo y todo setting global | La identidad visual guardada de la tienda |
| `config/settings_schema.json`, `sections/`, `blocks/`, `snippets/`, `layouts/`, `static/`, `translations/` \| `locales/` | Otros devs vía git; las actualizaciones del tema base (en instalaciones sin fork) | Commits de un compañero o una actualización de Ipanema |
| `custom/**` | Solo devs | Commits de un compañero |
| `manifest.json` | El CLI, en cada `theme pull` | Nada: es local y nunca se pushea |
| `.nuvem` | El CLI, en `theme authorize` / `theme pull --theme-id` | Nada, y **nunca se commitea** (contiene el token) |

Las dos primeras filas son las críticas: son de **propiedad compartida** con el comerciante y son, justamente, las únicas que se pueden pushear sin fork. El caso más común de pérdida de trabajo no requiere fork ni permisos especiales.

## 3. El gate

Antes de la **primera escritura de cada tarea**, en la carpeta del tema:

```bash
# 1. ¿Tenés trabajo sin commitear? theme pull SOBRESCRIBE los archivos locales.
git status --porcelain
# → si hay algo: git add -A && git commit -m "wip: <qué>"   (o git stash)

# 2. Cambios de otros devs (solo si el repo tiene remoto)
git pull --ff-only

# 3. Estado real de la tienda = todo lo que el comerciante haya guardado
tiendanube theme pull

# 4. Leé qué trajo el pull. Lo que aparezca y no lo hayas escrito vos ES del comerciante.
git status
git diff
```

Los pasos 1 y 3 son las dos caras del mismo riesgo: el paso 1 evita que **el pull** te borre tu trabajo, el paso 3 evita que **el push** borre el del comerciante. Ninguno de los dos avisa.

Si el paso 4 muestra cambios en `templates/**` o `config/settings_data.json` que no escribiste vos, **commitealos aparte antes de editar encima**:

```bash
git add templates config/settings_data.json
git commit -m "chore: sync cambios del comerciante (installation <id>)"
```

Así tu diff de trabajo queda limpio, el cambio del comerciante queda trazable con fecha, y si más adelante hay que decidir qué valor gana, los dos están en la historia.

Recién ahí: editá.

## 4. Cuándo se corre

**Siempre:**

- Antes de la primera escritura de cada tarea, sea un `.tpl`, un JSON template o un locale.
- Antes de tocar `templates/**` o `config/settings_data.json`, aunque ya hayas corrido el gate en esta sesión: son los archivos que el comerciante edita en vivo.
- Antes de `tiendanube theme push --force` — `--force` saltea la comparación con el remoto y manda todo, así que es la forma más rápida de pisar la tienda entera.
- Antes de `tiendanube theme publish` (ver §7).

**Repetilo, aunque ya lo hayas corrido, si:**

- Pasó un rato largo desde el último pull (más de ~30 minutos de trabajo, o una pausa de la sesión).
- El dev estuvo mostrándole la tienda al comerciante, o hubo una reunión de por medio.
- El comerciante tiene acceso al editor y el proyecto está en marcha (asumí que sí, salvo que el dev diga lo contrario).
- Vas a retomar una tarea de ayer.

**No hace falta** para leer, auditar o correr QA: el gate protege escrituras. Una lectura sobre copia vieja da un diagnóstico viejo, no destruye nada — pero si de ese diagnóstico salen correcciones, corré el gate antes de la primera.

## 5. Leer el diff del pull

Después del paso 3, `git diff` es el único lugar donde se ve, con precisión, qué hizo el otro lado. Cómo interpretarlo:

| Lo que ves en el diff | Quién lo hizo | Qué hacer |
|---|---|---|
| Una entrada nueva en `sections` + su id en `order` de un `templates/pages/*.json` | El comerciante agregó una sección desde el editor | **No la toques.** Commiteála y trabajá alrededor. Si tu cambio implica reordenar, preguntá dónde va la nueva |
| Cambios de valores dentro de `settings` de una section existente | El comerciante configuró esa sección | Su valor gana sobre el default que ibas a poner (§6) |
| `config/settings_data.json` con colores/tipografías distintos | El comerciante ajustó la identidad visual | Nunca lo reviertas "para que coincida con el diseño": avisale al dev que el comerciante cambió los globales |
| Cambios en `sections/`, `blocks/`, `snippets/`, `static/`, `layouts/` | En instalación **sin fork**: una actualización del tema base. Con fork: otro dev pusheó desde otra máquina | Sin fork es una actualización de Ipanema: no la revientes con tu versión vieja. Con fork, coordiná con el equipo antes de escribir |
| Solo `manifest.json` (`revision_token`) | El CLI, por el pull mismo | Ruido esperable. Commitealo con el resto |

Si el pull **no trajo nada**, el mensaje es igual de útil: la tienda está como la dejaste y podés escribir tranquilo.

## 6. Reconciliar un conflicto

Un conflicto real es que tu cambio y el del comerciante toquen **el mismo setting de la misma section**. Reglas:

1. **El valor guardado por el comerciante gana por default.** Es su tienda y lo eligió después de tu último pull. Ese valor no se revierte sin que alguien lo decida explícitamente.
2. **No mergees a ojo.** Mostrale al dev los dos valores —"el diseño pide `48`, el comerciante guardó `24`"— y esperá la decisión. Elegir por tu cuenta es cambiar la tienda sin que nadie lo pida.
3. **Si el conflicto es de estructura** (él agregó una section donde tu diseño pone otra), la decisión es del dev con el comerciante: no borres ni reordenes por tu cuenta.
4. **Un conflicto de git en un JSON template o en `settings_data.json` no lo resolvés vos.** Son archivos generados por un editor: un merge manual mal hecho rompe el JSON o mezcla estados que nunca existieron. Mostralo y frená.
5. **Nunca resuelvas nada con `theme push --force`.** No resuelve: reemplaza.

Excepción legítima a la regla 1: el dev pide explícitamente restaurar los valores del diseño porque el comerciante "toqueteó" el editor. Ahí se hace, pero **con el estado del comerciante ya commiteado antes** (§3), para poder volver.

## 7. El gate antes de publicar

`theme publish` convierte tu instalación en la productiva. Si venías trabajando en un **borrador** clonado hace días, todo lo que el comerciante configuró en la instalación productiva desde entonces **no está en tu borrador**: publicar lo reemplaza de una sola vez. Es el momento más destructivo del ciclo, y el gate normal no lo cubre — tu borrador puede estar perfectamente sincronizado consigo mismo.

Antes de publicar:

1. `tiendanube theme list` → confirmá cuál instalación es la productiva y cuál la tuya. Si son la misma, alcanza el gate de §3.
2. Si son distintas, comparalo contra la productiva antes de publicar. Como `.nuvem` es **por directorio** y todos los comandos aceptan `--published`, se puede bajar la productiva a una carpeta aparte y diffear:

   ```bash
   mkdir -p /tmp/tn-prod-check && cp .nuvem /tmp/tn-prod-check/
   cd /tmp/tn-prod-check && tiendanube theme pull --published -y && cd -
   diff -ru /tmp/tn-prod-check/templates templates
   diff -u  /tmp/tn-prod-check/config/settings_data.json config/settings_data.json
   ```

   Receta armada con flags documentados (`--published`, `-y`, `.nuvem` por directorio) — confirmá la salida la primera vez que la corras en un proyecto, y si el CLI se niega a operar en ese directorio, pedile al dev que haga la comparación por el panel.
3. Todo lo que aparezca en la productiva y no en tu borrador es trabajo del comerciante que la publicación va a borrar: listalo y **pedí confirmación explícita** antes de publicar. No es una decisión técnica.

## 8. El script sync-check.py

Los chequeos deterministas del gate están en `scripts/sync-check.py` (Python 3, stdlib, relativo a **esta skill**, no al tema):

```bash
python3 <carpeta-de-esta-skill>/scripts/sync-check.py <ruta-del-tema> \
  --files templates/pages/home.json sections/hero.tpl
```

Verifica, sobre el tema indicado (por defecto el directorio actual): que sea una instalación bajada con el CLI, la **antigüedad del último `theme pull`** (mtime de `manifest.json`), el estado de git (repo, archivos sin commitear, commits pendientes del remoto tras un `git fetch`), si hay un `theme watch` corriendo, el estado de `forked`, y en qué **capa** cae cada archivo de `--files` (compartida con el comerciante / código del tema / solo dev). Cierra con un veredicto y los comandos exactos a correr.

- Exit **0** = podés escribir · **1** = falta sincronizar (imprime qué y cómo) · **2** = error de uso (la ruta no es un tema del Fork workflow).
- `--json` emite el mismo informe estructurado, para usarlo desde un hook o un script.
- `--max-age <minutos>` cambia el umbral de frescura del pull (default 30). `--no-fetch` evita el `git fetch` si no hay red.

El script **no reemplaza el gate**: no corre el pull por vos ni lee el diff. Dice si podés escribir y, si no, qué falta.

## 9. Anti-patrones

| Anti-patrón | Por qué duele |
|---|---|
| `theme push --force` sin pull previo | Manda todo sin comparar: reemplaza la instalación con tu copia vieja, incluidas las eliminaciones |
| `theme pull` con cambios sin commitear | El otro lado del mismo error: el pull sobrescribe y perdés tu trabajo, sin confirmación |
| Editar `config/settings_data.json` a mano para "dejar el diseño como el boceto" | Ese archivo es el estado del editor del comerciante. Los defaults del diseño van en el `{% schema %}` / `settings_schema.json`, no ahí |
| Asumir que "el comerciante no toca nada" | Es su tienda y el editor es para eso. La suposición se paga con su trabajo |
| Correr el gate una vez al empezar el día | El editor no espera. Se corre por tarea, y de nuevo antes de tocar `templates/**` |
| Resolver un conflicto de JSON template a ojo | Genera un estado que nunca existió en la tienda, y el JSON roto no se ve hasta que el editor falla |
| Trabajar sin git para "ir rápido" | Sin git no hay diff: no podés saber qué cambió el comerciante ni volver atrás (§10) |

## 10. Casos borde

**El proyecto no tiene git.** No hay red de seguridad: el pull sobrescribe sin dejar rastro y no hay forma de ver qué cambió el comerciante. Antes de escribir nada: `git init -b main`, `.gitignore` con `.nuvem`, y commit del estado actual (el comando `/nube-skills:kickoff` deja esto listo). No es burocracia: es lo que hace visible el trabajo del otro lado.

**El repo no tiene remoto.** El paso 2 del gate no aplica; los pasos 1, 3 y 4 siguen siendo obligatorios. El comerciante no vive en el remoto de git, vive en la instalación.

**`theme watch` está corriendo.** Cortalo antes del pull. Con el watcher activo, los archivos que escriba el pull disparan pushes automáticos y el orden de los eventos deja de ser predecible; peor, si el pull borra localmente un archivo, watch replica la eliminación en la tienda. Pull con watch apagado, revisá el diff, y recién después levantá `theme watch` de nuevo.

**Instalación sin fork (`"forked": false`).** El push solo manda `templates/**`, `custom/**` y `config/settings_data.json`. Los dos primeros de esos son justamente los compartidos con el comerciante: **la falta de fork no te protege, al contrario**, lo único que podés pushear es lo único que él también edita. Los cambios en código del tema se omiten en silencio (ver `cli-workflow.md` §3).

**Dos instalaciones (productiva + borrador).** Verificá con `tiendanube theme current` a cuál está vinculado el directorio antes de pullear o pushear. El riesgo cambia de forma: si trabajás en el borrador, el comerciante probablemente esté editando la productiva → el problema no aparece en tus pushes, aparece de golpe en el `publish` (§7).

**Directorio con FTP legado.** El Fork workflow y el FTP no conviven en la misma carpeta y los comandos `theme` del Fork workflow no corren ahí. Si el proyecto es FTP, este protocolo no aplica tal cual: no hay `theme pull`, y la sincronización con lo que el comerciante haya cambiado se hace por FTP contra el servidor. Confirmá primero en qué workflow estás.

**El pull falla o el CLI no está disponible.** No escribas "mientras tanto" en `templates/**` ni en `config/settings_data.json`: sin poder verificar el estado remoto, cualquier push posterior es a ciegas. Avisale al dev y, si hay que avanzar, trabajá en una rama de git sobre archivos de código del tema (que el comerciante no edita) y dejá la capa de personalización para cuando se pueda sincronizar.
