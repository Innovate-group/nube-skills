# Tiendanube CLI y Fork Workflow

Referencia del **Tiendanube CLI** (`@tiendanube/cli`), la herramienta oficial de línea de comandos para el desarrollo de temas sectionable de Tiendanube. Cubre el **Fork workflow**: autenticación mediante bearer token contra la API REST de Tiendanube, sincronización de archivos (pull, push, watch) y gestión completa del ciclo de vida de instalaciones de tema (crear, clonar, fork, publicar, previsualizar, eliminar).

**Importante:** el Fork workflow actualmente solo admite el tema **Ipanema**. Para cualquier otro tema, usá el Flujo FTP (legado). No existe un comando `theme dev` — el ciclo de desarrollo se hace con `theme watch`.

## Tabla de contenidos

1. [Instalación y requisitos](#1-instalación-y-requisitos)
2. [Autenticación](#2-autenticación)
3. [El modelo Fork](#3-el-modelo-fork)
4. [Ciclo de vida de instalaciones](#4-ciclo-de-vida-de-instalaciones)
5. [Desarrollo: pull, push, watch](#5-desarrollo-pull-push-watch)
6. [manifest.json](#6-manifestjson)
7. [Fork Workflow vs FTP legado](#7-fork-workflow-vs-ftp-legado)
8. [Rate limits y troubleshooting](#8-rate-limits-y-troubleshooting)

---

## 1. Instalación y requisitos

| Requisito | Detalles |
|---|---|
| **Node.js 24.15+** | Descargá Node.js desde nodejs.org si todavía no lo tenés |
| **npm** | Viene con Node.js |

Instalá el CLI de forma global:

```bash
npm install -g @tiendanube/cli
```

Verificá la instalación:

```bash
tiendanube --version
```

Podés usar tanto `tiendanube` como `nuvemshop` — los dos comandos son idénticos. Toda esta referencia usa `tiendanube`; reemplazalo por `nuvemshop` si preferís ese binario.

---

## 2. Autenticación

### theme authorize (interactivo)

Ejecutá `theme authorize` para conectar el CLI con tu tienda. Abre tu navegador predeterminado, iniciás sesión, copiás el token de la página y lo pegás de vuelta en la terminal:

```bash
tiendanube theme authorize
```

Una vez que aceptás, el navegador muestra tu token de acceso a la API Pública; copialo y pegalo en el prompt `Paste your token:` de la terminal. El CLI decodifica el token, obtiene la URL de tu tienda desde la API Pública, escribe un archivo `.nuvem` en tu directorio de trabajo y verifica la conexión. El token es una **cadena Base64 completa** que codifica tanto el `store_id` como el `access_token` — no es el token de acceso bruto de la API.

### Opciones de theme authorize

| Opción | Descripción |
|---|---|
| `--token <token>` | Token Base64 de la página de autorización; omite el navegador y el prompt |
| `-y` | Omite el aviso de directorio no vacío |
| `-v` | Activa el log HTTP detallado |

### Archivo de configuración .nuvem

`theme authorize` crea un archivo `.nuvem` en tu directorio de trabajo. Contiene información sensible — incluido tu token de acceso — y no debe subirse al control de versiones. **Agregalo a tu `.gitignore`.** (Ver también la sección 7: cada directorio queda vinculado a un único workflow.)

### Modo no interactivo (scripts y CI)

Para scripts y CI, pasá el token directamente con `--token` para omitir el navegador y el prompt:

```bash
tiendanube theme authorize --token TU_TOKEN -y
```

### Token por comando (uso en CI)

Todos los comandos `theme` aceptan la opción `--token <token>`, lo que permite ejecutar cualquier comando sin antes ejecutar `theme authorize`. Útil para pipelines de CI que solo necesitan ejecutar un único comando:

```bash
tiendanube theme pull --theme-id 12345 --token TU_TOKEN
tiendanube theme push --token TU_TOKEN
tiendanube theme create --base-theme ipanema --title "CI Tema" --token TU_TOKEN
```

El token debe ser la misma **cadena Base64 completa** mostrada en la página de autorización. Cuando se pasa `--token`, anula cualquier credencial guardada en `.nuvem` solo para esa ejecución — no se escribe nada en disco.

---

## 3. El modelo Fork

Una instalación del tema Ipanema separa el **código del tema** de las **personalizaciones**. El código del tema es el núcleo — layouts, templates de sección, bloques, estilos y scripts. Las personalizaciones son las partes que varían por tienda — qué secciones aparecen en cada página, sus configuraciones y cualquier archivo personalizado.

Árbol de archivos de una instalación descargada:

```
mi-tema/
├── blocks/            ← Código del tema: templates de bloque (.tpl)
├── config/
│   ├── settings_schema.json   ← Código del tema: define las configuraciones disponibles
│   └── settings_data.json     ← Personalización: valores guardados por el comerciante
├── layouts/           ← Código del tema: estructura HTML principal
├── locales/           ← Código del tema: archivos de traducción
├── sections/          ← Código del tema: templates de sección (.tpl)
├── snippets/          ← Código del tema: partials compartidos (.tpl)
├── static/            ← Código del tema: CSS, JS, assets
├── templates/         ← Personalización: templates de página (.json)
└── custom/            ← Personalización: archivos agregados por el desarrollador
```

### Qué es editable sin fork

De forma predeterminada, una instalación **sin fork protege el código del tema** y solo permite modificar la capa de personalización:

| Permitido sin fork | Qué contiene |
|---|---|
| `templates/**` | Templates de página (`.json`) — definen qué secciones aparecen en cada página, su orden y sus configuraciones |
| `custom/**` | Archivos personalizados agregados por el desarrollador |
| `config/settings_data.json` | Los valores de configuración guardados por el comerciante |

Sin fork podés reorganizar secciones en una página, cambiar configuraciones o agregar archivos personalizados — pero no podés tocar los templates `.tpl`, los estilos, los scripts ni ningún otro archivo del núcleo. **`theme push` omite de forma silenciosa** los archivos fuera de las rutas permitidas: no falla, simplemente no los envía.

**Hacer fork** elimina esta restricción. Una vez hecho el fork, el CLI permite enviar **cualquier archivo** del tema — incluyendo layouts, secciones, bloques, snippets, assets estáticos y el schema de configuraciones.

### Cuándo hacer fork

**No hagas fork** si solo necesitás:

- Cambiar qué secciones aparecen en una página (editar `templates/*.json`)
- Ajustar configuraciones de sección (editar `templates/*.json` o `config/settings_data.json`)
- Agregar archivos personalizados (agregar archivos en `custom/`)

Este es el camino más seguro — la instalación se mantiene compatible con futuras actualizaciones del tema.

**Hacé fork** cuando necesités:

- Editar la lógica HTML/Twig de una sección (`sections/*.tpl`)
- Modificar templates de bloque (`blocks/*.tpl`)
- Cambiar la estructura del layout (`layouts/layout.tpl`)
- Actualizar estilos o scripts (`static/`)
- Agregar o modificar traducciones (`locales/`)
- Cambiar el schema de configuraciones (`config/settings_schema.json`)

### Propiedades del fork

- Hacer fork es una **operación irreversible sobre la propia instalación**: una instalación con fork no vuelve a ser sin fork en el lugar. Hacer fork de una instalación que ya tiene fork es una operación sin efecto.
- `theme unfork` **no modifica la instalación de origen**: crea una **nueva instalación** (borrador) que mantiene tus templates y configuraciones (`templates/`, `custom/`, `config/settings_data.json`) pero descarta el código del tema con fork, reactivando las actualizaciones automáticas del tema de Tiendanube.
- Solo los **temas basados en secciones** (como Ipanema) pueden tener fork. La API rechaza las solicitudes de fork para temas no seccionables.

> **Próximamente:** el fork de instalaciones figura como "llegando próximamente" en la documentación oficial. Por ahora, ejecutar `tiendanube theme fork` devuelve un aviso de que el fork todavía no está liberado. Mientras tanto, todo el resto del flujo (crear, descargar, enviar, monitorear, publicar) está disponible, y la personalización se hace a través de la capa de personalización (`templates/`, `custom/` y `config/settings_data.json`).

---

## 4. Ciclo de vida de instalaciones

Una **instalación de tema** es una instancia de un tema con alcance de tienda — una copia de trabajo con sus propios archivos, configuraciones y estado. La tienda tiene una instalación **productiva** (activa) y puede tener una segunda que sirve como borrador o experimento.

**Límite: máximo dos instalaciones por tienda** en cualquier momento (una productiva + una borrador). Si alcanzaste el límite, eliminá primero una instalación no productiva para liberar el espacio.

Ciclo de vida:

```
crear → descargar → enviar/monitorear → fork (opcional) → publicar → eliminar
```

No existe un comando `checkout` separado: `theme pull --theme-id <id>` guarda el ID de la instalación en `.nuvem`, y los comandos posteriores (`theme push`, `theme watch`, `theme publish/fork/clone/delete/preview`) toman esa instalación como destino cuando se omite `--theme-id`. Verificá a qué instalación está vinculado el directorio actual con `tiendanube theme current`.

### Flags comunes

| Flag | Descripción |
|---|---|
| `--theme-id <id>` | Apunta a una instalación específica (por defecto, la vinculada al directorio en `.nuvem`) |
| `--published` | Usa el tema publicado de la tienda en lugar de `--theme-id` o `.nuvem` |
| `--json` | Muestra la salida en JSON en lugar de una tabla |
| `--token <token>` | Token de autenticación Base64 (uso en CI, ver sección 2) |
| `-y` | Omite los prompts de confirmación |
| `-v` | Activa la salida detallada |

### Matriz de flags por comando

| Comando | `--theme-id` | `--published` | `--json` | `--token` | `-y` | `-v` | Específicas |
|---|---|---|---|---|---|---|---|
| `theme list` | — | — | Sí | Sí | — | Sí | — |
| `theme create` | — | — | Sí | Sí | — | Sí | `--base-theme <name>` (oblig.), `--title <name>` (oblig.) |
| `theme clone` | Sí | Sí | Sí | Sí | Sí | Sí | `--title <title>` |
| `theme fork` | Sí | Sí | Sí | Sí | Sí | Sí | — |
| `theme unfork` | Sí | Sí | Sí | Sí | Sí | Sí | `--title <title>` |
| `theme publish` | Sí | — | Sí | Sí | Sí | Sí | — |
| `theme preview` | Sí | Sí | — | Sí | — | — | — |
| `theme performance` | Sí | Sí | Sí | Sí | — | — | `--device <both\|mobile\|desktop>`, `--detailed` |
| `theme delete` | Sí | — | Sí | Sí | Sí | Sí | — |

### theme list

Listá todas las instalaciones de la tienda:

```bash
tiendanube theme list
tiendanube theme list --json
```

La salida muestra ID, título, versión del tema, si es productiva (activa), si tiene fork y si está archivada. La columna `archived` marca instalaciones antiguas guardadas que ya no están en uso activo.

### theme create

Creá una nueva instalación a partir de un código de tema base:

```bash
tiendanube theme create --base-theme ipanema --title "Mi Tema"
```

Crea una instalación basada en los archivos y configuraciones predeterminados del tema base. **El único valor admitido para `--base-theme` es `ipanema`** (el soporte para temas adicionales está planeado). `--base-theme` y `--title` son obligatorios.

### theme clone

`tiendanube theme clone` crea una copia idéntica de una instalación existente. A diferencia de **crear** (que parte de los valores predeterminados del tema base), **clonar** duplica una instalación existente — incluyendo modificaciones de archivos, cambios de configuraciones y personalizaciones. Útil para experimentar sin afectar el trabajo actual. El título por defecto de la copia es `<origen> (copy)`.

### theme fork

`tiendanube theme fork` hace fork de la instalación para desbloquear el acceso completo a los archivos (ver sección 3). Recordá: irreversible in-place, sin efecto si ya tiene fork, y hoy devuelve un aviso de "Próximamente".

### theme unfork

`tiendanube theme unfork` revierte el fork generando un nuevo borrador **sin fork**. No modifica la instalación de origen: crea una nueva instalación que conserva la capa de personalización y descarta el código con fork, reactivando las actualizaciones automáticas del tema base. El título por defecto es `<origen> (unforked)`.

### theme publish

`tiendanube theme publish` convierte la instalación en el tema **productivo** (activo) de la tienda, visible para todos los visitantes. La instalación que era productiva se degrada — sigue existiendo, pero ya no está activa. Publicar reemplaza el tema activo actual: **probá siempre con una previsualización antes de publicar**.

### theme preview

Obtené una URL de previsualización sin hacer activa la instalación:

```bash
tiendanube theme preview
```

Genera una URL con el formato:

```
https://tutienda.mitiendanube.com?theme_installation_id=ID_DE_INSTALACION
```

La previsualización solo es visible para vos — no afecta lo que ven los visitantes.

### theme performance

Ejecutá un informe de performance con Lighthouse sobre la versión actual del tema:

```bash
tiendanube theme performance
tiendanube theme performance --device mobile
tiendanube theme performance --detailed
tiendanube theme performance --json
```

Corre una auditoría de Lighthouse contra la URL de previsualización de la instalación en uso e imprime un informe por dispositivo — **mobile y desktop** por defecto — con el puntaje general y las métricas clave (First Contentful Paint, Speed Index, Largest Contentful Paint, Total Blocking Time, Cumulative Layout Shift, Time to Interactive). Usa el Chromium incluido con el CLI, corre en modo headless y puede tardar uno o dos minutos.

- Con `--detailed`, lista además los cambios recomendados de Lighthouse (oportunidades y diagnósticos que fallaron, de mayor a menor impacto, con ejemplos concretos).
- Con `--json`, los resultados se organizan por dispositivo en `results.mobile` y `results.desktop`.
- Requiere la `store_url` guardada en `.nuvem`; si falta, ejecutá `theme authorize` de nuevo.

### theme delete

`tiendanube theme delete` elimina una instalación de tema. Eliminar una instalación es **permanente y no se puede deshacer**. No se puede eliminar la instalación productiva actual.

---

## 5. Desarrollo: pull, push, watch

Antes de usar estos comandos, ejecutá `theme authorize` para conectar el CLI con la tienda.

### theme pull

Descargá todos los archivos de tema de una instalación al directorio de trabajo local:

```bash
tiendanube theme pull
tiendanube theme pull --theme-id ID_DEL_TEMA
```

El CLI obtiene cada archivo de la instalación y lo escribe en el directorio actual preservando la estructura de carpetas del tema (ver árbol en sección 3), y genera además un `manifest.json` local (sección 6). Tras un pull exitoso con `--theme-id`, el ID queda guardado en `.nuvem` y vincula el directorio a esa instalación.

Flags: `--theme-id <id>`, `--published`, `--token <token>`, `-y`, `-v`.

**La descarga sobrescribe los archivos locales.** Si tenés cambios sin commitear, hacé commit o stash antes de descargar.

### theme push

Enviá los archivos de tema locales a la instalación:

```bash
tiendanube theme push
```

El CLI lee cada archivo local, determina su formato según la extensión y lo envía:

| Extensión | Formato de envío |
|---|---|
| `.json` | Analizado y enviado como JSON |
| `.tpl`, `.css`, `.js`, `.svg` | Enviado como texto |
| Todo lo demás | Enviado como binario codificado en Base64 |

**Envío incremental (smart push):** antes de enviar, el CLI compara cada archivo local con su versión remota y solo envía los que cambiaron. Los archivos sin cambios se reportan como omitidos y no generan solicitud — acelera los envíos y reduce el consumo de rate limits. El CLI también **sincroniza las eliminaciones**: los archivos que existen en la instalación remota pero no en el directorio local se eliminan de la instalación durante el push.

Para forzar el envío de **todos** los archivos sin comparación con el remoto:

```bash
tiendanube theme push --force
```

**Qué se envía** — todos los archivos del directorio de trabajo, con estas exclusiones:

- **Rutas que empiezan con punto** — archivos y directorios que empiezan con `.` (como `.nuvem`, `.git`, `.vscode`) siempre se omiten
- **`manifest.json`** — el manifiesto local nunca se envía
- **Rutas restringidas por fork** — si la instalación no tiene fork, solo se pueden enviar `custom/`, `templates/` y `config/settings_data.json`; el resto se omite **de forma silenciosa** (ver sección 3)

Los archivos vacíos (cero bytes) no son exclusiones — generan un error de envío por archivo, y el push general se reporta como fallido.

Flags: `--theme-id <id>`, `--published`, `--force`, `--token <token>`, `-y`, `-v`.

### theme watch (dev loop)

Monitoreá los archivos locales y enviá los cambios automáticamente al guardar:

```bash
tiendanube theme watch
```

Cuando guardás un archivo, se envía a la instalación de inmediato; cuando eliminás un archivo localmente, también se elimina de la instalación. Aplican las mismas reglas de envío y restricciones de fork de `theme push` — watch no envía archivos que push omitiría.

**Recarga del navegador:** de forma predeterminada, el CLI abre una ventana de navegador controlada por Puppeteer que muestra la tienda con el parámetro de previsualización `?theme_installation_id=<id>` (la instalación en la que trabajás, no la productiva). Después de cada push o eliminación exitosa, la página se recarga automáticamente. Usá `--no-browser` para omitirlo (Puppeteer puede necesitar descargar Chromium en la primera ejecución).

Flags: `--theme-id <id>`, `--published`, `--no-browser`, `--token <token>`, `-v`.

### Flujo de desarrollo típico

1. **Crear o clonar** una instalación: `tiendanube theme create --base-theme ipanema --title "Mi Tema"` o `tiendanube theme clone`
2. **Descargar** los archivos (vincula el directorio): `tiendanube theme pull --theme-id ID`
3. **Hacer fork** si necesitás editar el código del tema: `tiendanube theme fork`
4. **Iniciar el modo watch**: `tiendanube theme watch`
5. **Editar** templates, secciones y configuraciones — los cambios se sincronizan automáticamente
6. **Previsualizar** con el navegador de auto-recarga, o generar un link: `tiendanube theme preview`
7. **Publicar** cuando esté listo: `tiendanube theme publish`

---

## 6. manifest.json

Tras `theme pull`, el CLI genera un archivo `manifest.json` en el directorio de trabajo con metadatos sobre la instalación:

```json
{
  "theme": "ipanema",
  "theme_version": "1.0.0",
  "forked": false,
  "revision_token": "<REVISION_TOKEN>",
  "installation_id": "4541834"
}
```

| Campo | Significado |
|---|---|
| `theme` | Código del tema base de la instalación |
| `theme_version` | Versión del tema base descargada |
| `forked` | Si la instalación tiene fork |
| `revision_token` | Revisión de la que provienen los archivos locales |
| `installation_id` | ID de la instalación de origen |

Este archivo es **solo local** — nunca se envía en push ni watch. Sirve para rastrear de qué instalación y revisión provienen los archivos locales.

---

## 7. Fork Workflow vs FTP legado

El CLI admite dos formas de sincronizar archivos de tema:

| Funcionalidad | FTP (legado) | Fork |
|---|---|---|
| Descargar / Enviar / Monitorear | Sí | Sí |
| Gestión de instalaciones | No | Sí |
| Fork / Clonar / Publicar | No | Sí |
| URLs de previsualización | No | Sí |
| Autenticación | Credenciales FTP | Bearer token |
| Soporte de temas | Todos los temas | Solo Ipanema |

| Flujo de trabajo | Ideal para |
|---|---|
| **Fork** | Tema Ipanema — gestión completa de instalaciones, autenticación mediante bearer token |
| **FTP (legado)** | Todos los demás temas — sincronización simple de archivos vía FTP |

**Un directorio de trabajo queda vinculado a un único flujo de trabajo.** Los comandos de tema del Fork workflow no se ejecutan en un directorio configurado para FTP, y viceversa. Para cambiar de workflow, usá otro directorio.

---

## 8. Rate limits y troubleshooting

### Rate limits

- La API de Tiendanube aplica límites de solicitudes. Si el CLI recibe una respuesta `429 Too Many Requests`, **espera automáticamente y reintenta** — no hace falta manejarlo a mano.
- Durante operaciones en lote como `theme push` (que sube archivos en paralelo), el CLI **limita la concurrencia a 2 subidas simultáneas** para mantenerse dentro de los límites de la API.
- El smart push reduce el consumo de rate limits al omitir archivos sin cambios; evitá `--force` salvo que necesites re-enviar todo.

### Problemas frecuentes

| Síntoma | Causa y solución |
|---|---|
| El push "funciona" pero un archivo del núcleo no cambia en la tienda | La instalación no tiene fork: los archivos fuera de `templates/**`, `custom/**` y `config/settings_data.json` se omiten silenciosamente. Hacé fork primero |
| No se puede crear una instalación nueva | Límite de **dos instalaciones por tienda** alcanzado. Eliminá una instalación no productiva con `theme delete` |
| El push falla con error en un archivo | Archivos de cero bytes generan error de envío por archivo y el push general se reporta como fallido. Eliminá o completá el archivo vacío |
| `theme performance` no encuentra la URL de la tienda | Falta la `store_url` en `.nuvem`. Ejecutá `theme authorize` de nuevo |
| `theme watch` demora o falla al abrir el navegador | Puppeteer puede necesitar descargar Chromium en la primera ejecución. Usá `--no-browser` y probá manualmente con la URL de preview |
| Los comandos de tema no corren en el directorio | El directorio está vinculado al otro workflow (FTP vs Fork). Usá un directorio por workflow |
| `theme delete` rechaza la operación | No se puede eliminar la instalación productiva actual. Publicá otra instalación primero |
| `theme fork` devuelve un aviso en lugar de hacer fork | El fork figura como "Próximamente" y todavía no está liberado. Trabajá sobre la capa de personalización mientras tanto |
| Cambios locales perdidos tras un pull | `theme pull` sobrescribe los archivos locales. Hacé commit o stash antes de descargar |
