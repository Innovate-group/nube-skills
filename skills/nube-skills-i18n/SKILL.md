---
name: nube-skills-i18n
description: "Audit and complete translations in TiendaNube sectionable themes (Ipanema base). Use when adding, auditing or fixing translation keys in a section-based TiendaNube theme: schema keys (t:names.*, t:settings.*, t:options.*, t:defaults.*, t:info.*, t:content.*, t:categories.*) used inside {% schema %} blocks, JSON templates or config/settings_schema.json, and storefront strings used with the | t filter; when the editor shows a raw 't:something' string instead of a label; when a key exists in one locale but is missing in others; or when adding a new locale. Triggers: traducciones, translations, locales, clave t:, filtro | t, falta traducción, texto sin traducir, aparece t: en el editor, i18n tienda nube, agregar idioma. NOT for Shopify themes (locales/*.json Shopify format) and NOT for classic TiendaNube themes (config/translations.txt — use tiendanube-theme-config)."
---

# Traducciones (temas sectionable de Tienda Nube)

Audita y completa las traducciones de un tema sectionable. El problema real que resuelve: una clave definida en `es.schema.json` pero **olvidada** en el resto de los locales — el editor muestra el string `t:` crudo al comerciante, y nadie se entera hasta que alguien abre el editor en otro idioma.

Contexto completo del sistema en `nube-skills-themes` → `references/schema-settings-i18n.md` (sección 6).

## Los dos sistemas — no confundirlos nunca

En la misma carpeta conviven dos sistemas **independientes**, para públicos distintos:

| Archivo | Público | Se usa con | Forma de las claves |
|---|---|---|---|
| `<locale>.json` | El comprador (storefront) | `{{ 'cart.add_to_cart' \| t }}` al renderizar la página | **Anidadas**: `{"cart": {"add_to_cart": "..."}}` |
| `<locale>.schema.json` | El comerciante (editor) | `"label": "t:settings.format"` en `{% schema %}`, `config/settings_schema.json` y JSON templates | **Planas por namespace**: `{"settings": {"format": "..."}}` |

Los dos locales son **independientes**: el `.json` se resuelve con el locale activo del comprador y el `.schema.json` con el locale del admin del comerciante. Un comerciante editando en portugués puede estar configurando una tienda que atiende en español — nada conecta a los dos más allá de vivir en la misma carpeta.

Namespaces válidos en `.schema.json` — la clave completa es `t:<namespace>.<ruta>`:

| Namespace | Qué contiene |
|---|---|
| `names` | Nombres de sections, blocks, presets y paneles; títulos de los divisores `header` |
| `settings` | Labels de cada setting |
| `options` | Labels de las opciones de `select`, `radio` y `alignment` |
| `defaults` | Textos por defecto (`"default": "t:defaults.heading"`), incluidos los de los presets en JSON templates |
| `info` | Textos de ayuda de la clave `info` de un setting |
| `content` | Texto de los `paragraph` y de algunos `header` |
| `categories` | Categorías de presets en el selector de secciones del editor |

La ruta después del namespace puede tener más de un nivel (`t:defaults.slide.heading`): definila con la misma anidación que ya usa el diseño.

**Regla dura:** una clave `t:` jamás va en `<locale>.json`, y una clave del filtro `| t` jamás va en `<locale>.schema.json`. Es el error más frecuente y el más difícil de detectar después.

### Fallback de locale — resuelve el archivo, no la clave

Cuando la plataforma pide un locale (por ejemplo `pt_BR`) busca el archivo disponible más cercano, en este orden:

1. `pt_BR.json` — coincidencia exacta.
2. `pt.json` — coincidencia solo de idioma.
3. `pt.default.json` — el default regional de ese idioma.

Mismo fallback para los `.schema.json`. Por eso un diseño entrega un default regional por idioma y agrega archivos de país (`es_AR`, `es_MX`, …) solo cuando el texto realmente difiere.

**El fallback es de archivo, no de clave:** una vez resuelto el archivo, una clave que falta ahí no se busca en otro locale. En el editor eso se ve como el string `t:` crudo; en el storefront, el texto no resuelve al idioma esperado. Eso es exactamente lo que audita esta skill.

## Paso 0 — Terreno

1. **Tema sectionable:** confirmalo con el Paso 0 de `nube-skills-themes`. Si es un tema clásico (`config/translations.txt`), detenete y derivá a `tiendanube-theme-config`.
2. **Carpeta:** `ls translations/ 2>/dev/null || ls locales/` — el nombre varía según cómo se bajó el tema. Usá la que exista; no crees la otra ni renombres.
3. **Inventario de locales:** anotá qué pares `<locale>.json` / `<locale>.schema.json` existen. Un locale con un solo archivo del par es ya un hallazgo.
4. **Fork:** leé `forked` en `manifest.json`. Sin fork lo único editable es `templates/**`, `custom/**` y `config/settings_data.json`; la carpeta de traducciones es código del tema, así que **las traducciones no se suben**: `theme push` y `theme watch` las omiten en silencio, sin error. Avisalo antes de editar, o el dev va a creer que deployó algo que nunca subió. Ojo con el caso mixto: un `t:` nuevo escrito en un JSON template **sí** sube (`templates/**` está permitido) pero su definición en el `.schema.json` no — el comerciante termina viendo el `t:` crudo. Sin fork, el trabajo queda local hasta que se haga `tiendanube theme fork` — comando que figura como "Próximamente" en la doc y hoy puede devolver solo un aviso, así que verificá su disponibilidad real antes de prometer un deploy.

## Paso 1 — Auditar

Corré el script incluido (Python 3, determinista, sin dependencias). Vive en `scripts/audit-i18n.py` **relativo a esta skill** (no al tema): `<carpeta-de-esta-skill>` es el directorio donde está este SKILL.md. El único argumento posicional es la ruta del tema a auditar, y es opcional — por defecto usa el directorio actual:

```bash
python3 <carpeta-de-esta-skill>/scripts/audit-i18n.py <ruta-del-tema>
python3 <carpeta-de-esta-skill>/scripts/audit-i18n.py <ruta-del-tema> --json
```

Compara las claves **usadas en el código** contra las **definidas en cada archivo de locale** y reporta, por archivo, las que faltan. Junto a cada faltante imprime dónde se usa (hasta 3 archivos). Marca `⚠ definida en el archivo del OTRO sistema` cuando esa clave faltante sí existe en el archivo hermano del mismo locale — el síntoma de haberla puesto en el sistema equivocado. Lista además las huérfanas (definidas y no usadas) y los archivos de locale ilegibles (no se pueden leer, JSON inválido, o raíz que no es un objeto). `--json` emite el mismo informe como JSON, para procesarlo.

Toma la carpeta de traducciones del propio tema: busca `translations/` y después `locales/`; si existen las dos, audita `translations/` y avisa.

Exit codes: **0** = sin faltantes · **1** = hay faltantes o algún archivo de locale es ilegible · **2** = error de uso (la ruta del tema no existe o no hay carpeta de traducciones). Las huérfanas no afectan el exit code.

Qué mira, si necesitás replicarlo a mano:

| Tipo | Dónde busca | Patrón |
|---|---|---|
| Schema (`t:`) | `sections/**/*.tpl`, `blocks/**/*.tpl`, `config/settings_schema.json`, `templates/**/*.json` | cualquier string `"t:<namespace>.<ruta>"` del archivo (no solo dentro de `{% schema %}`) |
| Storefront (`\| t`) | cualquier `**/*.tpl` del tema | `'<ruta.con.puntos>' \| t`, con comillas simples o dobles |

El script no reemplaza el criterio: revisá su reporte antes de actuar. Dos límites conocidos que explican casi todos sus falsos hallazgos:

- **Claves dinámicas** (`{{ 'cart.' ~ tipo | t }}`) no se resuelven: la clave real va a aparecer como huérfana. Antes de tocar una huérfana, buscala como substring en el código.
- **Código comentado cuenta como uso**: una clave que solo vive en un bloque comentado se reporta como usada.

## Paso 2 — Interpretar los hallazgos

| Hallazgo | Qué significa | Qué hacer |
|---|---|---|
| **Faltante** (usada, no definida en ese archivo de locale) | Nadie la resuelve por fallback: el editor muestra el `t:` crudo al comerciante, o el storefront no resuelve el texto a ese idioma | Darla de alta en ese locale (Paso 3). Es el hallazgo que hay que resolver siempre |
| **Faltante en TODOS los locales** | La clave se escribió en el código y nunca se definió | Darla de alta en todos; verificá que el namespace sea el correcto |
| **Faltante marcada `⚠ definida en el archivo del OTRO sistema`** | Los dos sistemas están mezclados: la clave se definió en el `.json` cuando iba en el `.schema.json`, o al revés | Movela al archivo que corresponde en todos los locales — no la dupliques en los dos |
| **Huérfana** (definida, no usada) | Sobró de una section borrada o el código cambió el nombre de la clave | **No la borres por tu cuenta**: informala y preguntá. Puede estar usada desde un JSON template del comerciante o desde código que no escaneaste |
| **Par incompleto** (falta el `.json` o el `.schema.json` de un locale) | Ese locale cae en el archivo más cercano (idioma base o `<idioma>.default`) sin avisar | Reportalo; crear el archivo faltante es decisión del dev |
| **Archivo ilegible** (JSON inválido o raíz que no es un objeto) | No se pudo auditar: sus faltantes y huérfanas quedan sin calcular | Arreglá el JSON y volvé a correr la auditoría antes de sacar conclusiones |

## Paso 3 — Completar

Por cada clave faltante:

1. **Elegí el archivo correcto** según el sistema (tabla de "Los dos sistemas"). Ante la duda, mirá cómo se usa la clave en el código: con `t:` → `.schema.json`; con `| t` → `.json`.
2. **Respetá la forma:** agrupada por namespace en `.schema.json` (con la anidación que ya use el diseño si la ruta tiene más de un nivel); anidada por ruta en `.json`.
3. **Dala de alta en TODOS los locales** que tengan ese tipo de archivo. Una clave a medias es exactamente el bug que esta skill existe para evitar.
4. **Traducí con criterio comercial**, no literal: el texto del editor lo lee el comerciante (claro y corto), el del storefront lo lee el comprador (tono de la tienda). Para locales de países del mismo idioma (`es_AR`, `es_MX`), adaptá modismos solo si el original los tiene; si no, mismo texto.
5. **Mantené el orden alfabético** dentro de cada namespace si el archivo ya lo respeta, y no reordenes lo que no tocás — los diffs limpios importan.

Si el dev pide **agregar un locale nuevo**: creá el par completo (`.json` y `.schema.json`) con TODAS las claves usadas, tomando como fuente el locale más completo. Recordá el fallback de archivo (exacto → idioma → `<idioma>.default`): agregar `es_CL.json` solo tiene sentido si el texto realmente difiere del default de español; si no, dejá que el fallback trabaje.

## Paso 4 — Verificar

1. Todos los JSON parsean, en la carpeta que exista: `for f in translations/*.json locales/*.json; do [ -f "$f" ] || continue; python3 -m json.tool "$f" > /dev/null || echo "ROTO: $f"; done`
2. Re-corré `audit-i18n.py` → debe dar exit 0. Un exit 1 con solo huérfanas es imposible: si sigue en 1, quedan faltantes o un archivo ilegible.
3. Si el tema está corriendo con `theme watch`, abrí la preview y el editor para confirmar que no queda ningún `t:` crudo visible.
4. Sin fork, recordale al dev que estos cambios **no se subieron**: quedaron solo en local.

## Reglas duras

1. **Nunca mezcles los dos sistemas** (`t:` ↔ `| t`): archivos distintos, formas distintas.
2. **Nunca dejes una clave a medias:** o está en todos los locales de su tipo, o no está.
3. **No borres huérfanas sin confirmación explícita** del dev.
4. **No renombres ni muevas la carpeta** (`translations/` vs `locales/`): usá la que el proyecto tenga.
5. **No hardcodees texto en un `.tpl`** para "resolver" una traducción faltante — el texto visible siempre sale de los archivos de traducción.
