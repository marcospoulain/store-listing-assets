---
name: app-store-image-prompts
description: En un agente de código (Claude Code, Codex, Antigravity): lee la marca del repo y genera los recursos del App Store (ícono, cabecera, búsqueda, universal, screenshots) en medidas oficiales.
---

# Recursos del App Store desde el código

Esta skill corre **dentro de un agente de código, en la carpeta del proyecto** (Claude Code, Codex, Antigravity u otro que lea SKILL.md). El usuario da órdenes cortas como:

- "hazme la cabecera"
- "hazme los screenshots de iPhone"
- "genera el ícono"
- "la imagen de búsqueda" / "la universal"
- "hazme el kit completo del App Store"

El agente debe: **(1) leer el repo y extraer la marca, (2) armar los prompts, (3) generar las imágenes con el motor disponible, (4) capturar las pantallas reales de la app, (5) componer los archivos finales en la medida exacta, (6) validarlos**. Todo queda en `appstore-assets/` dentro del repo.

Habla con el usuario en su idioma. Los prompts al generador van en **inglés**; los textos visibles (titulares) van en el idioma de la ficha (por defecto, el idioma principal de la app).

> Para Google Play existe la skill hermana `google-play-store-assets`. Ambas comparten el formato de `brand.json`. El script `compose.mjs` de esa skill (`../google-play-store-assets/scripts/compose.mjs`) sirve también aquí y ya quita el canal alfa.

---

## 0. Mapa de órdenes

| Orden del usuario | Código | Salida final |
|---|---|---|
| "ícono" | `ICON` | `final/icon-1024.png` |
| "cabecera", "header" | `HEADER` | `final/header-3840x1646.png` |
| "búsqueda", "search" | `SEARCH` | `final/search-3840x2560.png` |
| "universal" | `UNIVERSAL` | `final/universal-5244x2950.png` |
| "screenshots", "capturas" | `SHOTS` | `final/iphone-6.9/01.png …` (más iPad/Mac si aplica) |
| "todo", "kit completo" | `KIT` | todo lo anterior |

Si la app corre en iPad (`UIDeviceFamily`/`TARGETED_DEVICE_FAMILY` incluye 2, o `supportsTablet: true` en Expo), los screenshots de iPad 13" son **obligatorios**: genéralos también.

---

## 1. Especificaciones oficiales (Apple, App Store Connect Help + HIG, nov 2026)

Regla común: **JPEG/JPG o PNG, sin canal alfa ni transparencias.**

| Recurso | Medida exacta | Relación | Formato | Notas |
|---|---|---|---|---|
| ICON iOS/iPadOS/macOS | 1024 × 1024 | 1:1 | PNG | Cuadrado, **sin esquinas redondeadas**; sRGB o Display P3. visionOS: 1024×1024 (circular). watchOS: 1088×1088 (circular). tvOS: 800×480 |
| HEADER | 3840 × 1646 | 21:9 | JPEG/PNG | Cabecera de la página del producto (iOS/iPadOS 27, oct 2026) |
| SEARCH | de 1920×1280 a 3840×2560 → usar **3840 × 2560** | 3:2 | JPEG/PNG | Se ve chica: motivo grande y alto contraste |
| UNIVERSAL | 5244 × 2950 | 16:9 | **solo PNG** | Sirve para cabecera y búsqueda. Se recorta a 21:9 y a 3:2, así que todo lo importante va centrado (zona segura ≈ 3500 × 2000 centrada) |
| SHOTS iPhone 6.9" | 1320 × 2868 (o 1290 × 2796 / 1260 × 2736) | vertical | JPEG/PNG | Obligatorio el tamaño grande o el mediano (1206 × 2622 / 1179 × 2556). De 1 a 10 por tamaño |
| SHOTS iPad 13" | 2064 × 2752 (o 2048 × 2732) | vertical | JPEG/PNG | Obligatorio si corre en iPad |
| SHOTS Mac | 2880 × 1800 (16:10; o 2560×1600, 1440×900, 1280×800) | horizontal | JPEG/PNG | |
| SHOTS Apple TV / Vision Pro | 3840 × 2160 | horizontal | JPEG/PNG | |
| SHOTS Watch | 422 × 514 (Ultra) o 416 × 496 (Series 10–12) | — | JPEG/PNG | |

En horizontal se invierten las medidas. Si la UI es igual en todos los tamaños, basta con el más grande requerido: App Store Connect lo escala.

Reglas de diseño del ícono (HIG):
- Concepto simple, con pocas formas sólidas superpuestas, contenido centrado y fondo sólido o degradado.
- **Sin texto** (salvo una letra de marca esencial), sin fotos, sin capturas de UI y sin réplicas de hardware Apple.
- Sin sombras, brillos ni biseles propios: el sistema aplica Liquid Glass.
- En watchOS, nada de fondo negro.
- Las variantes dark/clear/tinted las genera el sistema. Para un control fino, el usuario puede armar capas en Icon Composer; es un paso manual en Xcode, así que avísalo y no lo simules.

Si el usuario indica otras medidas o pasó tiempo, verifica en `developer.apple.com/help/app-store-connect/reference/app-information/creative-assets-specifications` y `.../screenshot-specifications`.

---

## 2. Extraer la marca del repo

Antes de generar nada, inspecciona el proyecto y escribe `appstore-assets/brand.json`. Si ya existe (o existe `playstore-assets/brand.json`), reutilízalo y actualízalo si el código cambió.

Dónde buscar según el stack:

- **Nombre y descripción:** `package.json` (`name`, `description`), `app.json`/`app.config.*` (`name` de Expo), `Info.plist` (`CFBundleDisplayName`), `pubspec.yaml`, `README.md`, y `fastlane/metadata/*/name.txt`, `subtitle.txt` y `description.txt`.
- **Colores:**
  - Web/Next/React: `tailwind.config.*` (`theme.extend.colors`), CSS con variables (`globals.css`, `:root { --primary … }`, `@theme` de Tailwind v4), `components.json` de shadcn y `theme.ts`.
  - React Native/Expo: `theme/`, `constants/Colors.ts` y `app.json` (`splash.backgroundColor`).
  - Flutter: `ThemeData` y `ColorScheme.fromSeed(seedColor: …)`.
  - iOS nativo: `Assets.xcassets/AccentColor.colorset/Contents.json`, otros `*.colorset` y extensiones `Color`/`UIColor` en Swift.
- **Tipografía:** `next/font`, `@font-face`, `expo-font`, las fuentes de `pubspec.yaml` y los archivos `.ttf/.otf`.
- **Logo / ícono actual:** `public/logo.svg`, `favicon.*`, `assets/icon.png` y `Assets.xcassets/AppIcon.appiconset/`.
- **Estilo visual:** radios, sombras, ilustraciones, mascota y modo oscuro por defecto.
- **Textos y beneficios:** landing, onboarding, i18n y metadata de fastlane. De aquí salen los titulares de los screenshots.
- **Pantallas clave:** las rutas o screens principales. Elige de 4 a 6 que muestren el valor de la app.

Formato de `brand.json`:

```json
{
  "appName": "", "tagline": "", "oneLiner": "", "audience": "", "tone": "", "locale": "es-CL",
  "colors": { "primary": "#", "secondary": "#", "accent": "#", "background": "#", "foreground": "#" },
  "fonts": { "heading": "", "body": "", "files": [] },
  "logo": "", "currentIcon": "", "visualStyle": "", "heroElement": "",
  "screens": [ { "id": "01", "route": "/", "headline": "", "subhead": "" } ],
  "platforms": ["iphone", "ipad"],
  "sources": []
}
```

Muestra al usuario un resumen de 4 a 6 líneas y sigue. Pregunta solo si falta algo que no se pueda deducir o si hay marcas en conflicto.

---

## 3. Elegir el motor de generación

1. **La herramienta nativa de imágenes del agente** (Antigravity, Codex, etc., si la sesión la tiene), con el logo como referencia si se puede.
2. **Una API por variable de entorno** (comprueba que exista sin imprimir su valor):
   - `OPENAI_API_KEY` → OpenAI Images (`POST https://api.openai.com/v1/images/generations`, con el modelo de imagen vigente, p. ej. `gpt-image-1`; tamaños 1024x1024, 1536x1024 o 1024x1536; respuesta `b64_json`).
   - `GEMINI_API_KEY` / `GOOGLE_API_KEY` → el modelo de imagen de Gemini vigente vía `generateContent` (`inlineData`).
   - `REPLICATE_API_TOKEN` → Flux u otro modelo.
   Nunca escribas claves en archivos ni en logs.
3. **Sin generador:** arte 100 % con código (SVG/HTML con los degradados y formas de la marca).

Antes de un lote (`KIT`), di cuántas imágenes vas a generar y con qué motor, y espera un "sí". La medida exacta se logra en la composición (§6).

---

## 4. Prompts (se rellenan desde `brand.json`)

Guárdalos en `appstore-assets/prompts/<recurso>.md`.

Reglas para todo prompt:
- **Opaco**: `solid opaque background, no transparency`.
- Sin logos de terceros, personajes con copyright, personas reales ni réplicas de hardware Apple.
- Composición centrada y con márgenes de seguridad.
- El mismo STYLE BLOCK en todo el kit.
- **Sin texto en la imagen generada**: los titulares se ponen en la composición, con la fuente real de la marca.

**STYLE BLOCK**:
```
[visualStyle], color palette [primary] [secondary] [accent] on [background], [lighting acorde al tono], [tone] mood, clean composition, high detail, professional App Store marketing art, solid opaque background, no transparency
```

**ICON**
```
App icon artwork for "[appName]", [oneLiner]. Single central symbol: [heroElement] built from simple bold filled overlapping shapes, centered with generous padding. Background: smooth gradient [primary]→[secondary], full-bleed square. [STYLE BLOCK]. Flat square, no rounded corners, no mask, no text, no letters, no photo, no UI, no device, no drop shadow, no border. 1:1.
```
Negativo: `text, letters, watermark, rounded corners, frame, border, transparent background, photo, smartphone, apple logo`. Si existe `currentIcon`, pregunta si se rediseña o solo se reexporta a 1024 sin alfa.

**HEADER (21:9)**
```
Ultra-wide cinematic banner for the App Store product page of "[appName]", [oneLiner]. Scene: [heroElement] center or center-left, calm empty area on the [left/right] for headline text. [STYLE BLOCK]. Main subject inside the central 80%, nothing important near edges, no text, no logos, no watermark. 21:9.
```

**SEARCH (3:2)**
```
App Store search result artwork for "[appName]". One bold instantly readable hero: [heroElement] large and centered, strong contrast against [background]. Readable at thumbnail size. [STYLE BLOCK]. Minimal background, no small details, no text, no third-party logos. 3:2.
```

**UNIVERSAL (16:9)**
```
Key art for "[appName]" that will be cropped to both 21:9 and 3:2. [heroElement] and all key elements tightly centered in the middle 65%; outer margins only soft extendable background. [STYLE BLOCK]. No text, no logos. 16:9.
```

**SHOTS — fondo por pantalla** (la UI NO se genera)
```
Vertical App Store screenshot background for "[appName]", screen [N] of a consistent set. Abstract brand backdrop with [elemento decorativo ligado al beneficio] around the edges, center area kept calm (a real app screenshot will be placed there) and top 25% clean for a headline. [STYLE BLOCK], background tone [color de esa pantalla]. No text, no fake UI, no phone, no logos. Portrait 9:19.5.
```
Para iPad, `portrait 3:4`; para Mac, `landscape 16:10`. Antes, define el set como tabla (`#`, pantalla real, titular, subtítulo) en `prompts/shots.md`.

---

## 5. Capturar las pantallas reales (solo SHOTS)

App Review (guía 2.3) exige mostrar la app real en uso: **nunca inventes la interfaz con el generador.** Para obtener las capturas:

1. Usa las que el usuario ya tenga en `appstore-assets/screens/`.
2. **Simulador** (requiere macOS):
   ```bash
   xcrun simctl status_bar booted override --time 9:41 --batteryState charged --batteryLevel 100 --wifiBars 3 --cellularBars 4
   xcrun simctl io booted screenshot appstore-assets/screens/iphone-01.png
   ```
   Si el agente corre en Linux o Windows, pide las capturas al usuario o usa la opción 3.
3. **Versión web** (Next, PWA, Expo web), con Playwright usando estos viewports:
   - iPhone 6.9": 440×956 @3 → 1320×2868
   - iPhone 6.7": 430×932 @3 → 1290×2796
   - iPad 13": 1032×1376 @2 → 2064×2752
   - Mac: 1440×900 @2 → 2880×1800

Usa datos de demo realistas y oculta los banners de desarrollo.

---

## 6. Componer en la medida exacta

Usa HTML + CSS renderizado con Playwright al tamaño exacto. Si la skill `google-play-store-assets` está instalada, usa su `scripts/compose.mjs`, que ya quita el alfa. Si no, crea `appstore-assets/compose.mjs`:

```js
import { chromium } from 'playwright';
import path from 'node:path';
// uso: node compose.mjs <plantilla.html> <salida.png|.jpg> <ancho> <alto>
const [, , html, out, w, h] = process.argv;
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: +w, height: +h }, deviceScaleFactor: 1 });
await page.goto('file://' + path.resolve(html));
await page.evaluate(() => document.fonts.ready);
const jpg = /\.jpe?g$/i.test(out);
await page.screenshot({ path: out, type: jpg ? 'jpeg' : 'png', quality: jpg ? 95 : undefined });
await browser.close();
```

Plantilla de screenshot (`appstore-assets/templates/shot-01.html`):

```html
<!doctype html><html><head><style>
@font-face { font-family: Brand; src: url('../../RUTA/FUENTE.ttf'); }
html,body { margin:0; width:100%; height:100%; }
body { background: url('../raw/shot-01-bg.png') center/cover, linear-gradient(160deg, PRIMARY, SECONDARY);
       font-family: Brand, system-ui, sans-serif; color: FOREGROUND; display:flex; flex-direction:column; align-items:center; }
h1 { font-size: 7.5vw; line-height:1.05; text-align:center; margin: 9vh 7vw 1.5vh; font-weight:800; }
p  { font-size: 3.6vw; opacity:.85; text-align:center; margin: 0 9vw 4vh; }
.device { width: 78vw; aspect-ratio: 1320/2868; border-radius: 9vw; overflow:hidden;
          box-shadow: 0 4vw 10vw rgba(0,0,0,.25); border: 1.6vw solid #111; }
.device img { width:100%; height:100%; object-fit:cover; display:block; }
</style></head><body>
<h1>TITULAR</h1><p>SUBTITULO</p>
<div class="device"><img src="../screens/iphone-01.png"></div>
</body></html>
```

El marco es genérico (un rectángulo redondeado oscuro), sin logos ni réplica de hardware Apple. Para HEADER, SEARCH, UNIVERSAL e ICON, la plantilla es el arte generado con `cover` (o el SVG de marca), con un titular opcional dentro de la zona segura.

```bash
node compose.mjs templates/shot-01.html final/iphone-6.9/01.png 1320 2868
node compose.mjs templates/header.html final/header-3840x1646.png 3840 1646
node compose.mjs templates/search.html final/search-3840x2560.png 3840 2560
node compose.mjs templates/universal.html final/universal-5244x2950.png 5244 2950
node compose.mjs templates/icon.html final/icon-1024.png 1024 1024
```

Quita el alfa si usaste el script mínimo:
```bash
magick in.png -background "#FFFFFF" -alpha remove -alpha off out.png
# o con Pillow
python3 -c "import sys;from PIL import Image;[Image.open(f).convert('RGB').save(f) for f in sys.argv[1:]]" appstore-assets/final/*.png appstore-assets/final/*/*.png
```

Si el arte es chico para 3840 o 5244 px, súbelo de escala (Real-ESRGAN u otro upscaler) o usa SVG.

---

## 7. Validar

```bash
find appstore-assets/final -type f \( -name '*.png' -o -name '*.jpg' \) -exec magick identify -format "%f %wx%h %[channels]\n" {} \;
```
El resultado debe decir `srgb` (3 canales), nunca `srgba`. Comprueba además:
- que el universal sea PNG;
- que el sujeto quede en la zona segura (genera recortes de prueba a 21:9 y 3:2 en `preview/`);
- que la UI sea real, que los titulares no tengan faltas y que el estilo sea consistente;
- que no haya marcas de terceros.

Mira al menos una imagen de cada tipo.

---

## 8. Estructura y entrega

```
appstore-assets/
  brand.json  prompts/  raw/  screens/  templates/  compose.mjs  preview/
  final/
    icon-1024.png  header-3840x1646.png  search-3840x2560.png  universal-5244x2950.png
    iphone-6.9/01.png …  ipad-13/01.png …
```

Sugiere agregar `appstore-assets/raw/` al `.gitignore`. Al terminar, informa:
- los archivos generados;
- el motor usado;
- de dónde salió la marca;
- los pasos manuales: subir a App Store Connect e Icon Composer, si se quiere.

Si el agente no puede generar ni ejecutar, entrega los prompts listos para pegar y los comandos.

## Ejemplos

- "hazme la cabecera" → `brand.json` → prompt HEADER → arte 21:9 → plantilla → `final/header-3840x1646.png` sin alfa → validar.
- "hazme los screenshots" → elegir de 4 a 6 pantallas y titulares → capturas reales → fondos → composición a 1320×2868 (+ iPad 2064×2752 si aplica) → validar.
- "el kit completo" → resumir la marca, anunciar el lote y esperar el "sí" → ICON, HEADER, SEARCH, UNIVERSAL y SHOTS.
