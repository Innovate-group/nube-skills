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
- Links de Figma: boceto **desktop**, boceto **mobile** y **ui-kit**. El ui-kit es obligatorio para las skills de desarrollo (`nube-skills-section` lo usa siempre); si todavía no existe, dejalo anotado como pendiente en el CLAUDE.md.
- ¿Instalación nueva o ya existe una en la tienda? Recordá el límite: **máximo 2 instalaciones por tienda** (1 productiva + 1 borrador).
- ¿Crear también un repo privado en GitHub (org `Innovate-group`) y pushear? (opcional)

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

## 5. CLAUDE.md del proyecto

Creá `CLAUDE.md` en la raíz con este template completado (es la memoria compartida del proyecto — las skills del plugin lo leen):

```markdown
# <Cliente> — Tema Tienda Nube (sectionable)

- **Tema base:** ipanema — versión y estado de fork en `manifest.json`
- **Installation ID:** <id> (<productiva | borrador>)
- **Preview:** correr `tiendanube theme preview` (URL con `?theme_installation_id=<id>`)
- **Figma boceto:** <link desktop> · <link mobile>
- **UI-kit:** <link>  ← lo usa nube-skills-section; no borrar esta línea
- **Dev loop:** `tiendanube theme watch` (auto-push + navegador con reload)
- **Regla de fork:** sin fork solo son editables `templates/**`, `custom/**` y
  `config/settings_data.json` — `theme push` omite el resto en silencio.
```

Sumá al template cualquier dato propio del cliente que el dev te haya dado (idiomas/locales requeridos, integraciones, fechas).

## 6. Repo en GitHub (solo si el dev lo pidió en el paso 1)

```bash
gh repo create Innovate-group/<cliente>-theme --private --source . --push
```

## 7. Cierre y verificación

1. `tiendanube theme current` → confirma el directorio vinculado a la instalación correcta.
2. `ls` → estructura completa del tema (blocks/, config/, layouts/, sections/, snippets/, static/, templates/, locales/ o translations/, custom/, manifest.json).
3. `git check-ignore .nuvem` → protegido.
4. Mostrale al dev el resumen final: instalación creada/vinculada, cómo abrir la preview, y los próximos pasos — levantar `tiendanube theme watch` y arrancar la primera sección pasándole a Claude el nodo de Figma (dispara `nube-skills-section`).
