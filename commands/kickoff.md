---
description: Arranca un proyecto nuevo de tema sectionable de Tienda Nube (Ipanema, Fork Workflow) — instalación, pull, git y CLAUDE.md del proyecto
argument-hint: [nombre-del-cliente]
disable-model-invocation: true
---

Arrancá un proyecto nuevo de tema sectionable de Tienda Nube. Cliente: $ARGUMENTS

Seguí estos pasos en orden. El contexto técnico (CLI, Fork Workflow, estructura del tema) está en la skill `nube-skills-themes` — consultala ante cualquier duda y **no inventes comandos del CLI** (no existen `theme dev`, `theme check` ni `theme serve`).

## 1. Datos del proyecto

Preguntale al dev todo lo que falte, en una sola tanda:

- Nombre del cliente (si no vino como argumento).
- Carpeta destino del proyecto (si ya estás parado en ella, confirmalo).
- **Los nodos del ui-kit** (ver abajo). Es lo único de diseño que se pide en el kickoff.
- ¿Instalación nueva o ya existe una en la tienda? Recordá el límite: **máximo 2 instalaciones por tienda** (1 productiva + 1 borrador).
- ¿Crear también un repo privado en GitHub (org `Innovate-group`) y pushear? (opcional)

**No pidas los bocetos de las páginas.** Los diseños de home, producto, categoría y demás se van pasando **sección a sección** durante el desarrollo, cuando el dev invoca `nube-skills-section` con el nodo puntual. Pedirlos ahora no sirve de nada.

### Los nodos del ui-kit

El ui-kit **no es un boceto**: es el sistema visual, y vive repartido en varios nodos de Figma. Pedile al dev el link ("Copy link to selection") de cada uno de los que existan:

| Nodo | Para qué lo usan las skills |
|---|---|
| **Colores / paleta** | Mapear cada color del diseño a su token con nombre en vez de copiar el hex suelto |
| **Tipografías / escala** | Familias, pesos y tamaños con nombre; evita inventar una escala por sección |
| **Botones** | Variantes y estados (primario, secundario, hover, disabled) |
| **Formularios / inputs** | Campos, labels, mensajes de error |
| **Cards / product card** | La pieza que más se repite en un ecommerce |
| **Iconografía** | Set de íconos y su tamaño base |
| **Espaciados / grid** | Escala de espaciado, ancho de contenedor y columnas |

Reglas al pedirlos:
- Si el ui-kit está todo en **una sola página** de Figma, alcanza con el link de esa página, pero anotá igual qué contiene.
- Si **falta** alguno, anotalo como pendiente en el `CLAUDE.md` en vez de inventarlo: cuando aparezca, se agrega.
- Si el proyecto **no tiene ui-kit**, decilo explícito: el sistema visual pasa a ser el del propio tema (`layouts/resources/style-tokens.tpl` + `config/settings_schema.json`) y las secciones se van a construir contra esos tokens.

## 2. Prerrequisitos

1. `tiendanube --version` — si falla: `npm install -g @tiendanube/cli` (requiere Node 24.15+).
2. Autenticación: `tiendanube theme authorize` — es **interactivo**: abre el navegador, el dev se loguea en la tienda y pega el token en la terminal. Genera el archivo `.nuvem` en el directorio; ese archivo contiene credenciales y **jamás se commitea**.

## 3. Instalación del tema

- **Nueva:** `tiendanube theme create --base-theme ipanema --title "<Cliente> — Rediseño"` (hoy `ipanema` es el único base-theme válido).
- **Existente:** `tiendanube theme list` y elegí con el dev cuál usar.
- **Descargar y vincular:** `tiendanube theme pull --theme-id <ID>` — baja el tema completo, vincula el directorio a esa instalación y genera `manifest.json` (archivo local, nunca se sube).
- **NO hagas `theme fork` en el kickoff.** El fork se decide recién cuando el desarrollo exige tocar código core (el triage de `nube-skills-section` lo detecta). Además `theme fork` figura "Próximamente" en la doc oficial — puede devolver solo un aviso.

## 4. Git

1. `git init -b main` (si la carpeta no es ya un repo).
2. Crear `.gitignore` con al menos:

```
.nuvem
.DS_Store
node_modules/
```

3. Verificar que el token quedó protegido: `git check-ignore .nuvem` debe devolver la ruta.
4. Commit inicial: `chore: kickoff <cliente> — tema base ipanema (installation <ID>)`.

Este commit no es burocracia: es la red de seguridad del proyecto. Es lo que hace que, en el próximo `tiendanube theme pull`, el `git diff` muestre **qué cambió el comerciante desde el editor** — sin git, el pull sobrescribe sin dejar rastro y no hay forma de saberlo.

## 5. CLAUDE.md del proyecto

Creá `CLAUDE.md` en la raíz con este template completado (es la memoria compartida del proyecto — las skills del plugin lo leen):

```markdown
# <Cliente> — Tema Tienda Nube (sectionable)

- **Tema base:** ipanema — versión y estado de fork en `manifest.json`
- **Installation ID:** <id> (<productiva | borrador>)
- **Preview:** correr `tiendanube theme preview` (URL con `?theme_installation_id=<id>`)
- **Dev loop:** `tiendanube theme watch` (auto-push + navegador con reload)
- **Regla de fork:** sin fork solo son editables `templates/**`, `custom/**` y
  `config/settings_data.json` — `theme push` omite el resto en silencio.
- **Sync antes de escribir (aplica a cualquier IA y a cualquier dev):** el comerciante
  edita `templates/**` y `config/settings_data.json` desde el editor de la tienda.
  Antes de la primera escritura de cada tarea: commit/stash → `git pull --ff-only` →
  `tiendanube theme pull` → `git diff`. Lo que traiga el pull y no lo hayas escrito vos
  es suyo: commitealo aparte antes de editar encima. `theme push` sincroniza
  eliminaciones, así que una copia vieja no pisa sus cambios: **los borra**.

## UI-kit

Sistema visual del rediseño. **`nube-skills-section` lee esta tabla en cada sección
que construye** — no borrarla ni renombrar el encabezado.

| Nodo | Link |
|---|---|
| Colores / paleta | <link o `pendiente`> |
| Tipografías / escala | <link o `pendiente`> |
| Botones | <link o `pendiente`> |
| Formularios / inputs | <link o `pendiente`> |
| Cards / product card | <link o `pendiente`> |
| Iconografía | <link o `pendiente`> |
| Espaciados / grid | <link o `pendiente`> |

## Bocetos por sección

Se completan **sobre la marcha**: cada vez que se construye una sección, anotá acá
su nodo, así queda trazable qué diseño originó qué código.

| Sección | Desktop | Mobile |
|---|---|---|
| (vacío al arrancar) | | |
```

Reglas al completarlo:
- Poné `pendiente` en los nodos del ui-kit que todavía no existan — nunca inventes un link.
- Si el proyecto no tiene ui-kit en Figma, reemplazá esa tabla por una línea que lo diga y aclare que el sistema visual son los tokens del tema (`layouts/resources/style-tokens.tpl` + `config/settings_schema.json`).
- La tabla de bocetos arranca **vacía**: se llena sección por sección durante el desarrollo.
- Sumá cualquier dato propio del cliente que el dev te haya dado (idiomas/locales requeridos, integraciones, fechas).

## 6. Repo en GitHub (solo si el dev lo pidió en el paso 1)

```bash
gh repo create Innovate-group/<cliente>-theme --private --source . --push
```

## 7. Cierre y verificación

1. `tiendanube theme current` → confirma el directorio vinculado a la instalación correcta.
2. `ls` → estructura completa del tema (blocks/, config/, layouts/, sections/, snippets/, static/, templates/, locales/ o translations/, custom/, manifest.json).
3. `git check-ignore .nuvem` → protegido.
4. Mostrale al dev el resumen final: instalación creada/vinculada, cómo abrir la preview, y los próximos pasos — levantar `tiendanube theme watch` y arrancar la primera sección pasándole a Claude el nodo de Figma (dispara `nube-skills-section`).
