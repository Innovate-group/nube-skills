---
name: nube-skills-qa
description: "Visual QA of a TiendaNube sectionable theme against its design reference (Figma node or design canvas artboard), on desktop and mobile. Use when the user asks to review, check or compare an implemented section against the mockup ('revisá cómo quedó', 'compará con el Figma', 'QA de la home', '¿está fiel al diseño?', 'chequeá mobile'), or before publishing a theme. Drives the theme preview URL with the Chrome DevTools MCP, captures both viewports, reads computed styles to compare numbers instead of eyeballing pixels, checks interactive states, and reports prioritized findings — separating implementation bugs from merchant-configurable settings and from real store content. Triggers: QA visual, comparar con el diseño, revisar sección, fidelidad al boceto, chequear mobile, antes de publicar tema tienda nube. NOT for performance audits (use tiendanube theme performance) and NOT for Shopify themes."
---

# QA visual (temas sectionable de Tienda Nube)

Compara lo implementado contra la referencia de diseño, en **desktop y mobile**, y devuelve hallazgos priorizados. Es la continuación de `nube-skills-section`: esa skill cierra su Paso 5 con un checklist estructural de 9 ítems (schema que parsea, claves `t:` completas, `block_attributes`, nada hardcodeado, límites sin fork, `order`/`block_order`, settings de padding, estados declarados, toggle interno). **No lo repitas acá:** esta skill arranca donde ese checklist termina — la fidelidad visual fina.

Tampoco cubre performance: `tiendanube theme performance` ya corre Lighthouse contra la URL de preview, en mobile y desktop. No corras `lighthouse_audit` ni traces de performance desde acá.

## La distinción que define esta skill

En un tema settings-first, **no toda diferencia visual es un bug de código**. Clasificá antes de reportar:

| Tipo | Cómo se reconoce | Dónde se arregla |
|---|---|---|
| **Bug de implementación** | El CSS/markup no puede producir el diseño con ningún valor de setting (grilla mal armada, falta un estado, tipografía equivocada) | El `.tpl` / CSS de la section o block |
| **Setting mal configurado** | El código soporta el valor correcto pero el JSON template tiene otro (padding en 24 donde el diseño pide 48) | El JSON template — o el editor, si lo puso el comerciante |
| **Diferencia de contenido** | Textos, precios, fotos o cantidad de productos distintos del mockup | **No es un hallazgo.** La preview trae datos reales; el diseño trae ejemplos |

Ante la duda entre bug y setting, mirá el `{% schema %}`: si el valor del diseño es alcanzable con un setting existente, es configuración. Reportar contenido real como error es la forma más rápida de que el dev deje de confiar en el reporte.

## Paso 0 — Prerrequisitos

1. **Tema sectionable** (Paso 0 de `nube-skills-themes`).
2. **URL de preview:** `tiendanube theme preview` la imprime, con la forma `https://<tienda>.mitiendanube.com?theme_installation_id=<id>`. Acepta `--theme-id <id>` para apuntar a otra instalación y `--published` para la productiva. También podés armar la URL con el `installation_id` de `manifest.json`. Solo la ves vos; no afecta a los visitantes.
3. **La preview refleja lo último:** si `forked: false` en `manifest.json`, `push` y `watch` solo suben `templates/**`, `custom/**` y `config/settings_data.json`; `sections/`, `blocks/`, `snippets/`, `layouts/`, `static/`, las traducciones y `config/settings_schema.json` se omiten **en silencio** — podrías estar auditando una versión vieja del código. Verificalo antes de reportar nada.
4. **MCP de Chrome DevTools** disponible. Si `theme watch` abrió su propio navegador, ese no es necesariamente el que maneja el MCP: para evitar confusión, corré `theme watch --no-browser` y manejá la navegación desde acá.
5. **Referencia de diseño:** buscala primero en la tabla `## Bocetos por sección` del `CLAUDE.md` — `nube-skills-section` anota ahí el nodo de cada sección que construye. Si no está, pedile al dev el nodo de Figma (desktop y mobile) o el link del canvas si se construyó sin boceto, y **sumalo a esa tabla**. Sin referencia no hay QA visual.
6. **Alcance y estados:** ¿una sección, una página o el tema entero? ¿Qué estados interactivos declaró el dev al construirla? El reporte cambia de tamaño y de foco.

## Paso 1 — Capturar los dos viewports

Fijá el viewport con `emulate`, **no** con `resize_page`: `resize_page` solo recibe `width` y `height` (redimensiona la ventana), mientras que el `viewport` de `emulate` también emula device pixel ratio y touch. Sin eso las media queries de `pointer: coarse` / `hover: none` evalúan mal y vas a reportar diferencias que no existen.

El `viewport` de `emulate` es un string con la forma `<ancho>x<alto>x<dpr>[,mobile][,touch][,landscape]` — el DPR no es opcional:

| Viewport | Parámetro de `emulate` |
|---|---|
| Desktop | `viewport: "1440x900x2"` (o el ancho del artboard desktop) |
| Mobile | `viewport: "390x844x3,mobile,touch"` (o el del artboard mobile) |

`emulate` aplica a la **página seleccionada**: si abrís otra pestaña, volvé a fijarle el viewport.

Reducí el ruido antes de capturar:

- Congelá animaciones y transiciones con el `initScript` de `navigate_page`: es un **script JS** que corre en cada documento nuevo antes que cualquier script de la página, y solo toma efecto **a partir de esa navegación** — si la página ya está abierta, pasalo junto con `type: "reload"` (o `type: "url"`) para que aplique. Dos capturas de una sección con animación de entrada nunca son iguales.

  ```js
  () => {
    const css = '*,*::before,*::after{animation:none!important;transition:none!important;scroll-behavior:auto!important}';
    document.addEventListener('DOMContentLoaded', () => {
      const style = document.createElement('style');
      style.textContent = css;
      document.head.appendChild(style);
    });
  }
  ```

- Esperá a que carguen imágenes y fuentes antes de disparar la captura: un `<picture>` a medio resolver produce hallazgos falsos. `evaluate_script` acepta funciones `async`, así que sirve `async () => { await document.fonts.ready; return [...document.images].every(i => i.complete); }`. Si esperás por un texto puntual, `wait_for` recibe una lista de strings.
- Scrolleá hasta la sección si está debajo del fold.

Con `take_screenshot`: sin `filePath` la imagen viene inline y podés compararla vos; con `filePath` (absoluto o relativo al directorio de trabajo) se guarda a disco en vez de adjuntarse a la respuesta — útil si vas a armar un reporte con las capturas. Para la página entera, `fullPage: true`; para una sección puntual, `take_snapshot` primero y después `take_screenshot` con el `uid` del elemento — `uid` y `fullPage` son incompatibles.

Traé la referencia del **mismo** breakpoint y compará siempre desktop contra desktop y mobile contra mobile.

## Paso 2 — Comparar por dimensiones

De lo estructural a lo fino: un problema de layout explica muchas diferencias menores aguas abajo.

| # | Dimensión | Qué mirar |
|---|---|---|
| 1 | **Layout** | Orden y jerarquía, columnas/grilla, alineación, ancho del contenedor, qué se apila u oculta en mobile |
| 2 | **Espaciado** | Padding vertical de la sección (`padding_top`, `padding_bottom`, `padding_top_mobile`, `padding_bottom_mobile`, o los nombres que use el proyecto — ej. `vertical_padding` en Ipanema), gaps, márgenes internos |
| 3 | **Tipografía** | Familia, peso, tamaño, interlineado, mayúsculas, truncados |
| 4 | **Color** | Fondos, textos, bordes; contrastá contra los tokens del ui-kit, no solo contra el píxel |
| 5 | **Imágenes y media** | Relación de aspecto, `object-fit`, radios, carga responsive |
| 6 | **Estados interactivos** | Los que el dev declaró al construir la sección: hover, focus, activo, abierto/cerrado y animaciones (para las animaciones, capturá sin el freeze del Paso 1) |
| 7 | **Responsive intermedio** | Un ancho ~768px para detectar layouts que se rompen entre los dos breakpoints definidos |

### QA numérico (el diferencial)

No estimes píxeles sobre una captura: leé los valores reales. Con `take_snapshot` obtenés el `uid` del elemento (usá siempre el snapshot más reciente) y con `evaluate_script` leés sus estilos computados: `args` es una lista de uids y la herramienta los resuelve a los elementos que recibe la función, en ese orden.

```js
(el) => {
  const s = getComputedStyle(el);
  return { pt: s.paddingTop, pb: s.paddingBottom, fs: s.fontSize,
           lh: s.lineHeight, fw: s.fontWeight, color: s.color,
           bg: s.backgroundColor, radius: s.borderRadius };
}
```

Compará esos números contra los valores de la referencia **y contra los defaults del `{% schema %}`** — así distinguís al instante un bug de CSS de un setting con otro valor. Con el padding no repitas el checklist de `nube-skills-section` (que las 4 settings existan y el CSS las aplique): lo que verificás acá es que el valor **renderizado** en cada viewport coincida con el del diseño.

### Estados interactivos

El hover real de CSS solo se dispara con input del navegador: usá la herramienta `hover`, que requiere el `uid` del elemento (un `dispatchEvent` desde JS **no** activa `:hover`). El flujo es `take_snapshot` → tomar el `uid` → `hover` → `take_screenshot`. Para focus, `evaluate_script` con `function: "(el) => el.focus()"` y ese `uid` en `args`.

Si la sección tiene el toggle de visibilidad interna (id `internal_only`), probá los dos casos en paralelo: `new_page` con un `isolatedContext` con nombre crea la pestaña en un contexto de navegador aislado (cookies y storage separados), así tenés en una la sesión de un cliente logueado con email `@innovategroup` (debe verse) y en otra la visita anónima (no debe verse). Las herramientas actúan sobre la página seleccionada: cambiá de una a otra con `list_pages` + `select_page`, y refijá el viewport con `emulate` en cada una.

Revisá también `list_console_messages` con `types: ["error"]`: un JS roto puede explicar por qué algo no se ve como el diseño. Lista los mensajes desde la última navegación — si recargaste para aplicar el `initScript`, usá `includePreservedMessages: true` para ver también los anteriores.

## Paso 3 — Reportar

Una tabla ordenada por severidad, lo más grave arriba. Formato por fila: estado, qué difiere, y el detalle como **"esperado X, hay Y"** con dónde se arregla.

| Severidad | Criterio |
|---|---|
| **Alta** | Rompe el layout, hace ilegible el contenido, o afecta la compra (CTA tapado, precio ilegible) |
| **Media** | Se nota a simple vista comparando con el diseño |
| **Baja** | Detalle fino que solo aparece midiendo (2px, un radio de borde) |

Por cada hallazgo: **qué** difiere, **dónde** (sección/elemento + viewport), **esperado vs actual** con números cuando los tengas, **el tipo** (bug / setting / contenido) y **el archivo o setting** donde se corrige. Indicá también lo que está bien: "tipografía OK en ambos viewports" es información útil. Cerrá con un veredicto de una línea: listo para mostrar / listo con ajustes menores / requiere correcciones antes de publicar.

Si el dev quiere una comparación visual interactiva (swipe entre diseño e implementación), existe la skill `design-compare` para eso; no la reimplementes.

## Paso 4 — Corregir y re-verificar (si el dev lo pide)

**Antes de la primera corrección, corré el gate del Paso 0.5 de `nube-skills-themes`** (commit/stash → `git pull --ff-only` → `tiendanube theme pull` → `git diff`). El QA se hizo contra la preview, que es el estado **remoto**: tu copia local puede ser más vieja que eso. Si el comerciante configuró algo desde el editor mientras revisabas, "arreglar" settings sobre la copia vieja se lo borra — y `theme push` sincroniza eliminaciones, así que también se van las secciones que él agregó. Si el pull trae cambios, re-mirá los hallazgos: alguno puede haber dejado de existir.

1. **Bugs** → corregilos con las convenciones de `nube-skills-section` (settings-first, tokens antes que valores sueltos). Tocar `sections/`, `blocks/`, `snippets/` o `static/` exige `forked: true`: sin fork el push omite esos archivos en silencio y la preview no va a cambiar — avisá que hace falta `tiendanube theme fork` (hoy figura "Próximamente" en la doc) en vez de dar el arreglo por hecho.
2. **Settings** → ajustá el JSON template; si lo configuró el comerciante desde el editor, no lo pises: avisalo. El `git diff` del gate es lo que te dice cuál valor es suyo — sin ese pull no podés distinguir "el dev puso 24" de "el comerciante puso 24".
3. **Re-capturá** los puntos corregidos y mirá la vista completa de nuevo: un arreglo de CSS puede mover otra cosa.

## Reglas duras

1. **Nunca reportes contenido real como diferencia** (productos, precios, fotos y textos de la tienda no son el mockup).
2. **`emulate`, no `resize_page`**, para que las media queries de touch y DPR evalúen bien.
3. **Compará siempre el mismo breakpoint** contra su equivalente.
4. **Distinguí bug de setting** antes de proponer un arreglo: cambiar CSS para compensar un setting mal puesto empeora el código.
5. **No toques código durante el Paso 3:** primero el reporte completo, después las correcciones.
6. **Ninguna corrección sin sincronizar antes** (gate del Paso 0.5 de `nube-skills-themes`): auditás contra el remoto, así que corregir sobre una copia local vieja es la forma más directa de borrar lo que el comerciante configuró mientras hacías el QA.
7. **No corras auditorías de performance** desde esta skill — `tiendanube theme performance` ya las cubre.
8. **No rehagas el checklist estructural de `nube-skills-section`** (schema, claves `t:`, `block_attributes`, existencia de settings): acá se audita lo que se ve renderizado.
