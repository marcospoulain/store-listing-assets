---
name: google-play-store-assets
description: En un agente de código (Claude Code, Codex, Antigravity): lee la marca del repo y genera los recursos gráficos de Google Play (ícono, gráfico de funciones, screenshots, banner TV) en medidas oficiales.
---

# Recursos gráficos de Google Play desde el código

Esta skill corre **dentro de un agente de código, en la carpeta del proyecto** (Claude Code, Codex, Antigravity u otro que lea `SKILL.md`). El usuario da órdenes cortas como:

- "hazme el ícono de Play"
- "hazme el gráfico de funciones" / "el feature graphic"
- "hazme los screenshots de teléfono" / "de tablet" / "de Wear OS"
- "el banner de TV"
- "los textos de la ficha" / "la descripción breve"
- "hazme el kit completo de Google Play"

El agente debe: **(1) leer el repo y extraer la marca, (2) detectar qué tipos de dispositivo soporta la app, (3) armar los prompts, (4) generar el arte con el motor disponible, (5) capturar las pantallas reales, (6) componer los archivos finales en la medida exacta, (7) validarlos con `scripts/validate.py`**. Todo queda en `playstore-assets/` dentro del repo, con una copia opcional en la estructura de `fastlane supply`.

Habla con el usuario en su idioma. Los prompts al generador van en **inglés**; los textos visibles (leyendas, textos alternativos, descripción breve) van en el idioma de la ficha (por defecto el idioma principal de la app, p. ej. `es-419`).

Archivos de apoyo de esta skill (rutas relativas a la carpeta de la skill):
- `references/specs.md` — tabla completa de especificaciones oficiales y reglas de contenido.
- `scripts/compose.mjs` — renderiza una plantilla HTML a PNG/JPEG en píxeles exactos (Playwright).
- `scripts/validate.py` — valida medidas, relación de aspecto, canal alfa, formato y peso según el tipo de recurso.
- `templates/` — plantillas HTML de ícono, gráfico de funciones, screenshot de teléfono, screenshot de pantalla grande y banner de TV.

Copia `scripts/` y `templates/` a `playstore-assets/` del proyecto antes de usarlos.

---

## 0. Mapa de órdenes

| Orden del usuario | Código | Salida final |
|---|---|---|
| "ícono" | `ICON` | `final/icon-512.png` |
| "gráfico de funciones", "feature graphic", "banner de la ficha" | `FEATURE` | `final/feature-graphic-1024x500.png` |
| "screenshots", "capturas" (sin más) | `SHOTS_PHONE` | `final/phone/01.png …` |
| "screenshots de tablet" | `SHOTS_TABLET` | `final/tablet-7/…`, `final/tablet-10/…` |
| "screenshots de Chromebook" | `SHOTS_CHROMEBOOK` | `final/chromebook/…` |
| "Wear OS", "reloj" | `SHOTS_WEAR` | `final/wear/…` |
| "TV", "Android TV" | `TV` | `final/tv-banner-1280x720.png` + `final/tv/…` |
| "Automotive", "auto" | `SHOTS_AUTO` | `final/automotive/portrait-…`, `landscape-…` |
| "XR" | `SHOTS_XR` | `final/xr/…` |
| "textos", "descripción breve", "alt text" | `TEXT` | `final/listing-text.<locale>.md` |
| "todo", "kit completo" | `KIT` | ICON + FEATURE + SHOTS de cada dispositivo soportado + TEXT |

---

## 1. Especificaciones oficiales (Google Play Console Help, art. 9866151, y Android Developers, nov 2026)

Resumen operativo. El detalle completo está en `references/specs.md`. Los **requisitos** son obligatorios (incumplirlos puede causar el rechazo, la eliminación o la suspensión de la ficha). Las **recomendaciones** no bloquean la publicación, pero ignorarlas limita la promoción.

| Recurso | Medida | Formato | Reglas clave |
|---|---|---|---|
| **Ícono** | **512 × 512 px** | **PNG de 32 bits**, sRGB, **≤ 1024 KB** | Cuadrado completo: **sin esquinas redondeadas** (Play aplica una máscara con radio del 30 %) y **sin sombra paralela** (Play la agrega). Fondo opaco a sangre con el color de marca. Logos con forma propia: dentro de la retícula de keylines (≈ 384 px centrados). Sin insignias ni texto de ranking, precio, categoría o promociones. |
| **Gráfico de funciones** (feature graphic) | **1024 × 500 px** | **JPEG o PNG de 24 bits (sin alfa)** | Obligatorio en la práctica: es la portada del video y se usa en colecciones grandes y anuncios. Punto focal **centrado**: logo, nombre, eslogan y UI clave fuera de los bordes, que se recortan. Colores vivos; **evita el blanco puro, el negro y el gris oscuro**, que se funden con el fondo de Play. No repitas el ícono tal cual. **Sin imágenes de dispositivos**, sin logos de terceros y sin insignias de tiendas. Texto alternativo ≤ 140 caracteres. |
| **Screenshots (general)** | lados de **320 a 3840 px**; **lado largo ≤ 2 × lado corto** | **JPEG o PNG de 24 bits (sin alfa)** | **Hasta 8 por tipo de dispositivo**, y **mínimo 2** en total para publicar. |
| Screenshots de teléfono (para promoción) | **mín. 4**, **1080 × 1920 (9:16)** vertical o **1920 × 1080 (16:9)** horizontal, ≥ 1080 px | igual | Juegos: mín. 3, todos horizontales o todos verticales, con gameplay real. **Recomendado: 1440 × 2560.** |
| Tablets 7"/10" y Chromebook (pantallas grandes) | **mín. 4**, lados de **1080 a 7680 px**, **16:9 o 9:16** | igual | **Sin texto que no sea parte de la experiencia de la app** (nada de leyendas de marketing). **Recomendado: 2560 × 1440** horizontal. |
| Wear OS (apps y watch faces) | **1:1, mín. 384 × 384** | igual | Solo la UI de la app: **sin marco, sin texto extra, sin gráficos, sin fondos**, sin transparencia ni máscara. Mín. 1 que refleje la versión actual. Recomendado mostrar Tiles. En watch faces personalizables, muestra varias opciones. |
| Android TV | screenshot obligatorio (usa **1920 × 1080**) + **banner 1280 × 720** | JPEG o PNG de 24 bits | Ambos son obligatorios para publicar en TV y solo se ven en dispositivos TV. |
| Android Automotive OS | **mín. 2 verticales de 800 × 1280** y **2 horizontales de 1024 × 768** | igual | Obligatorio fuera de las categorías "vehículo estacionado". UI genérica del sistema (emuladores *Automotive (1024p landscape)* y *Automotive Portrait*), nada de UI de fabricantes. |
| Android XR | **4 a 8**, **8:5**, recomendado **3840 × 2400** (mín. 1920 × 1200), **≤ 8 MB** | PNG o JPEG | Videos XR opcionales vía YouTube. |
| Video de vista previa | URL de YouTube | — | Público u oculto, sin anuncios ni monetización, sin restricción de edad, insertable. Muestra el uso real (≥ 80 % del video) en los primeros 10 s. Solo se reproducen automáticamente los primeros 30 s. **Esta skill no genera video**: solo puede proponer un guion. |
| Descripción breve | **≤ 80 caracteres** | texto | Ver §8. |

### Reglas de contenido para TODO recurso gráfico

- **Prohibido** afirmar ranking, premios, precio o promociones ("el mejor", "N.º 1", "nuevo", "descuento", "gratis") y **prohibidas las llamadas a la acción** ("descarga ya", "juega ahora").
- **Sin imágenes de dispositivos**: a diferencia de muchas fichas del App Store, en Play **no se usan marcos de teléfono**. La UI va sola, con esquinas redondeadas sobre el fondo de marca.
- Sin logos ni marcas de terceros sin permiso, y sin íconos ni insignias de Google Play ni de otras tiendas.
- **Leyendas ≤ 20 % del área de la imagen.** Evita la letra chica y los fondos recargados.
- Muestra la app o el juego **real**. Se permiten screenshots estilizados que dividen la UI en varias imágenes, pero **las 3 primeras deben priorizar la UI**.
- **Barra de estado limpia**: sin operador ni notificaciones, y con señal, batería y Wi-Fi llenas.
- Imágenes nítidas y sin estirar ni pixelar, con la rotación correcta.
- **Localiza** las leyendas y los textos de marca por idioma y mercado. La UI de un juego no necesita localizarse, pero las leyendas sí.
- **Texto alternativo** para cada screenshot y para el gráfico de funciones: ≤ 140 caracteres, sin "foto de" ni "imagen de".

> ⚠️ **No reutilices los screenshots del iPhone tal cual.** Las medidas del iPhone 6.9" (1320 × 2868) superan la relación 2:1, igual que las capturas nativas de la mayoría de los Android modernos (p. ej. 1080 × 2400, 20:9). Siempre compónlos en un lienzo de **9:16**.

Si el usuario cita otras medidas o pasó tiempo, verifica en `support.google.com/googleplay/android-developer/answer/9866151` y `developer.android.com/distribute/google-play/resources/icon-design-specifications`.

---

## 2. Extraer la marca del repo

Antes de generar nada, inspecciona el proyecto y escribe `playstore-assets/brand.json`. Si existe `appstore-assets/brand.json` (de la skill del App Store), **reutilízalo** como base para que ambas tiendas compartan identidad.

Dónde buscar:

- **Nombre:** `res/values/strings.xml` (`app_name`), el `android:label` del `AndroidManifest.xml`, `app.json`/`app.config.*` (Expo), `pubspec.yaml`, `package.json`, y `fastlane/metadata/android/<locale>/title.txt`.
- **Descripciones existentes:** `fastlane/metadata/android/<locale>/short_description.txt` y `full_description.txt`, el `README.md` y la landing page.
- **Colores:**
  - Android nativo: `res/values/colors.xml`, `themes.xml` (`colorPrimary`, `colorSecondary`) y `values-night/`.
  - Jetpack Compose: `ui/theme/Color.kt` y `Theme.kt` (`lightColorScheme(primary = …)`).
  - Ícono adaptativo: `res/mipmap-anydpi-v26/ic_launcher.xml`, con `@color/ic_launcher_background` y el drawable de `foreground` (excelente fuente para el ícono de Play).
  - Web/React/Next: `tailwind.config.*`, variables CSS (`:root`, `@theme`), shadcn `components.json`, `theme.ts`.
  - React Native/Expo: `theme/`, `constants/Colors.ts`, `app.json` (`android.adaptiveIcon.backgroundColor`, `splash.backgroundColor`).
  - Flutter: `ThemeData` y `ColorScheme.fromSeed(seedColor: …)`.
- **Tipografía:** `res/font/`, `FontFamily` en Compose, `next/font`, `@font-face`, `expo-font` y las fuentes de `pubspec.yaml`.
- **Logo / ícono actual:** `res/mipmap-*/ic_launcher*.png` o `.webp`, `ic_launcher_foreground.xml` (vector), `assets/icon.png`, `public/logo.svg` y `fastlane/metadata/android/<locale>/images/icon.png`.
- **Estilo visual:** Material 3 o personalizado, radios, ilustraciones, mascota y modo oscuro por defecto (mira los componentes principales y la pantalla de inicio).
- **Textos de beneficios:** onboarding, `strings.xml` por idioma (`values-es/`, `values-b+es+419/`), los archivos i18n y la landing.
- **Pantallas clave:** `NavHost`/rutas de Compose, Activities y Fragments principales, Expo Router o React Navigation. Elige de 4 a 8 que muestren el valor de la app.

### Detectar los tipos de dispositivo soportados

| Señal en el código | Dispositivo |
|---|---|
| App de teléfono normal | Teléfono (siempre) |
| Sin `screenOrientation` fijo, layouts `sw600dp`/`w840dp`, `WindowSizeClass`, o `supportsTablet` en Expo | Tablets 7"/10" y Chromebook (recomendado, ayuda a la promoción en pantallas grandes) |
| `<uses-feature android:name="android.hardware.type.watch"/>`, módulo `wear`, dependencias `androidx.wear` | Wear OS |
| `android.software.leanback`, categoría `LEANBACK_LAUNCHER`, `android:banner` | Android TV |
| `android.hardware.type.automotive`, `automotive_app_desc.xml`, `androidx.car.app` | Android Automotive OS |
| Dependencias `androidx.xr`, features XR en el manifest | Android XR |

Muestra al usuario un resumen de 4 a 6 líneas: nombre, paleta, tipografía, estilo, dispositivos detectados y las pantallas con sus leyendas. Después sigue. Pregunta solo si falta algo que no se pueda deducir o si hay marcas en conflicto.

Formato de `brand.json` (el mismo de la skill del App Store, más los campos de Play):

```json
{
  "appName": "",
  "tagline": "",
  "oneLiner": "qué hace la app en una frase",
  "audience": "",
  "tone": "",
  "locale": "es-419",
  "isGame": false,
  "colors": { "primary": "#", "secondary": "#", "accent": "#", "background": "#", "foreground": "#" },
  "fonts": { "heading": "", "body": "", "files": ["ruta/a/fuente.ttf"] },
  "logo": "",
  "currentIcon": "",
  "visualStyle": "",
  "heroElement": "",
  "devices": ["phone", "tablet", "chromebook", "wear", "tv", "automotive", "xr"],
  "screens": [ { "id": "01", "route": "", "caption": "", "altText": "" } ],
  "sources": ["archivo → dato"]
}
```

---

## 3. Elegir el motor de generación

Usa el primero disponible:

1. **La herramienta nativa de imágenes del agente** (p. ej. la de Antigravity o Codex, si la sesión la tiene). Pásale el logo o el ícono actual como referencia si lo permite.
2. **Una API por variable de entorno** (comprueba que exista sin imprimir su valor):
   - `OPENAI_API_KEY` → OpenAI Images (`POST https://api.openai.com/v1/images/generations`, con el modelo de imagen vigente, p. ej. `gpt-image-1`; tamaños 1024x1024, 1536x1024 o 1024x1536; respuesta `b64_json`).
   - `GEMINI_API_KEY` / `GOOGLE_API_KEY` → el modelo de imagen de Gemini vigente vía `generateContent` (la imagen vuelve en `inlineData`).
   - `REPLICATE_API_TOKEN` → Flux u otro modelo de imagen.
   Si falla por el nombre del modelo, consulta la documentación del proveedor. Nunca escribas claves en archivos ni en logs.
3. **Sin generador:** crea el arte **100 % con código** (SVG/HTML con los degradados, las formas y el logo de la marca). Es válido, y para el ícono y el gráfico de funciones suele quedar más fiel a la marca.

Generar imágenes cuesta dinero: antes de un lote (p. ej. `KIT`), di cuántas imágenes vas a pedir y con qué motor, y espera un "sí". Para una sola imagen, procede.

Los generadores no entregan medidas exactas: genera en la relación más cercana. **La medida exacta se logra en la composición (§6).**

---

## 4. Prompts (se rellenan desde `brand.json`)

Guarda cada prompt en `playstore-assets/prompts/<recurso>.md`.

**STYLE BLOCK**, común a todo el kit:
```
[visualStyle], color palette [primary] [secondary] [accent], vivid saturated colors, [lighting acorde al tono], [tone] mood, clean composition, high detail, professional store marketing art, solid opaque background, no transparency
```

**ICON (512, cuadrado a sangre)**
```
App icon artwork for "[appName]", [oneLiner]. Single central symbol: [heroElement], bold simple shapes, centered, with internal lighting/shading inside the artwork only. Full-bleed opaque background in [primary] (or gradient [primary]→[secondary]) covering the entire square edge to edge. [STYLE BLOCK]. Square 1:1, no rounded corners, no mask, no drop shadow outside the artwork, no border, no text, no badges, no ranking or price symbols.
```
- Si el logo tiene una forma crítica, colócalo dentro de un círculo o cuadrado de ≈ 384 px centrado (las keylines) sobre el fondo a sangre. No lo estires hasta los bordes.
- Si existe un ícono adaptativo (`ic_launcher_foreground` + background), prefiere **componerlo directamente** con código (foreground sobre el color de fondo, a 512 px) antes que generar uno nuevo. Así coincide con el ícono del launcher.

**FEATURE GRAPHIC (1024 × 500)**
```
Wide promotional banner for "[appName]", [oneLiner]. Shows the experience: [escena que expresa el valor central, contexto de uso o historia]. Focal point and key imagery centered in the middle 60%; only soft background elements near the edges. Bright vivid [primary]/[accent] palette, avoid pure white, black or dark gray backgrounds. Extends the brand of the icon without copying the icon. [STYLE BLOCK]. No text, no device mockups, no phones, no third-party logos, no store badges. Aspect ratio ≈ 2.05:1.
```
El nombre o el eslogan (opcional y corto) se agregan en la composición, centrados, sin llamadas a la acción.

**SCREENSHOT — fondo por pantalla (teléfono, 9:16)**
```
Vertical backdrop for a Google Play screenshot of "[appName]", screen [N] of a consistent set. Abstract brand background with [elemento decorativo ligado al beneficio] around the edges; large calm center area where a real app UI capture will be placed; top band calm for a short caption. [STYLE BLOCK], background tone [color de esa pantalla]. No text, no device, no phone frame, no fake UI, no logos. Portrait 9:16.
```
- **Tablet y Chromebook (16:9):** solo fondo sutil o color plano y **ninguna leyenda**. La UI ocupa casi todo el lienzo.
- **Wear, Automotive y TV:** **no se genera fondo**. Va solo la captura real de la UI (en Wear, sin fondo ni texto).

**TV BANNER (1280 × 720)**
```
Android TV app banner for "[appName]": brand artwork with [heroElement], designed to read from across a room, strong contrast, centered composition. [STYLE BLOCK]. 16:9, no small details, no device, no badges.
```
El nombre de la app suele ir en el banner de TV: agrégalo en la composición con la fuente de la marca, grande y centrado.

Primero define el set en `prompts/screenshots.md`:

| # | Pantalla real | Leyenda (≤ ~6 palabras, sin CTA ni claims) | Texto alternativo (≤ 140) |
|---|---|---|---|
| 01 | [ruta/screen] | "Tus documentos siempre a mano" | "Pantalla principal con la lista de documentos del vehículo" |

Las 3 primeras deben mostrar la UI de forma prominente.

---

## 5. Capturar las pantallas reales

Las políticas de Play exigen mostrar la app real: **nunca inventes la UI con el generador.** Para obtener las capturas, en orden de preferencia:

1. Capturas que el usuario ya tenga en `playstore-assets/screens/`.
2. **Emulador o dispositivo Android con `adb`** (funciona en macOS, Linux y Windows):
   ```bash
   # Barra de estado limpia (modo demo de SystemUI)
   adb shell settings put global sysui_demo_allowed 1
   adb shell am broadcast -a com.android.systemui.demo -e command enter
   adb shell am broadcast -a com.android.systemui.demo -e command clock -e hhmm 1200
   adb shell am broadcast -a com.android.systemui.demo -e command battery -e level 100 -e plugged false
   adb shell am broadcast -a com.android.systemui.demo -e command network -e wifi show -e level 4
   adb shell am broadcast -a com.android.systemui.demo -e command network -e mobile show -e level 4 -e datatype none
   adb shell am broadcast -a com.android.systemui.demo -e command notifications -e visible false

   # Captura
   adb exec-out screencap -p > playstore-assets/screens/phone-01.png

   # Al terminar
   adb shell am broadcast -a com.android.systemui.demo -e command exit
   ```
   Perfiles de emulador recomendados (crearlos con `avdmanager` o Android Studio):
   - Teléfono: Pixel moderno.
   - Tablet: Pixel Tablet o un perfil de 10".
   - Wear: Wear OS Large Round / Small Round.
   - TV: Android TV 1080p.
   - Automotive: **Automotive (1024p landscape)** y **Automotive Portrait**, con la imagen genérica del sistema.
3. **Si la app tiene versión web** (PWA, Expo web, Flutter web): captura con Playwright y un viewport de teléfono (p. ej. 412×915 @ `deviceScaleFactor` 3.5 → 1442×3203). Compón luego en 9:16.

Usa datos de demo realistas (nada de "lorem ipsum" ni datos personales reales) y oculta los banners de depuración (`debugShowCheckedModeBanner: false`, etc.).

---

## 6. Componer los archivos finales en la medida exacta

Usa `scripts/compose.mjs`, que renderiza HTML con Playwright a píxeles exactos. Así el texto sale nítido, con la fuente real de la marca. Si falta Playwright: `npm i -D playwright && npx playwright install chromium`.

```bash
node playstore-assets/scripts/compose.mjs <plantilla.html> <salida.png|.jpg> <ancho> <alto> [--rgba]
```

El script quita el canal alfa por defecto (PNG de 24 bits o JPEG). Usa `--rgba` solo para el ícono, que debe ser **PNG de 32 bits**: el script lo guarda en RGBA, pero 100 % opaco.

Plantillas incluidas en `templates/`. Cópialas, cambia los marcadores `{{…}}` y ajusta las rutas:

| Plantilla | Uso | Medida |
|---|---|---|
| `icon.html` | Ícono: fondo a sangre + símbolo/logo (vector o PNG) | 512 × 512 `--rgba` |
| `feature-graphic.html` | Arte de fondo + nombre/eslogan opcional centrado | 1024 × 500 |
| `phone-screenshot.html` | Fondo + leyenda (banda ≤ 18 % del alto) + captura real con esquinas redondeadas, **sin marco de dispositivo** | 1440 × 2560 (o 1080 × 1920) |
| `large-screen-screenshot.html` | Captura real de tablet/Chromebook sobre un color plano, **sin leyenda** | 2560 × 1440 |
| `tv-banner.html` | Arte + nombre de la app | 1280 × 720 |

Para Wear OS, Automotive y XR, **no compongas**: usa la captura real y solo ajusta la medida si hace falta (recorte centrado 1:1 en Wear, mín. 384 × 384, sin máscara circular ni fondo transparente):

```bash
python3 playstore-assets/scripts/validate.py --fit wear screens/wear-01.png final/wear/01.png
python3 playstore-assets/scripts/validate.py --fit automotive-portrait screens/auto-p-01.png final/automotive/portrait-01.png
```

Ejemplos:
```bash
node playstore-assets/scripts/compose.mjs playstore-assets/templates/icon.html playstore-assets/final/icon-512.png 512 512 --rgba
node playstore-assets/scripts/compose.mjs playstore-assets/templates/feature-graphic.html playstore-assets/final/feature-graphic-1024x500.png 1024 500
node playstore-assets/scripts/compose.mjs playstore-assets/templates/phone-01.html playstore-assets/final/phone/01.png 1440 2560
node playstore-assets/scripts/compose.mjs playstore-assets/templates/tablet-01.html playstore-assets/final/tablet-10/01.png 2560 1440
node playstore-assets/scripts/compose.mjs playstore-assets/templates/tv-banner.html playstore-assets/final/tv-banner-1280x720.png 1280 720
```

Si el arte generado es chico, súbelo de escala primero (Real-ESRGAN u otro upscaler disponible) o usa SVG.

---

## 7. Validar

```bash
python3 playstore-assets/scripts/validate.py playstore-assets/final
```

El script detecta el tipo de recurso por la carpeta o el nombre del archivo (`icon`, `feature-graphic`, `phone`, `tablet-7`, `tablet-10`, `chromebook`, `wear`, `tv-banner`, `tv`, `automotive`, `xr`) y revisa:
- medidas exactas o rangos, y relación de aspecto (incluido **lado largo ≤ 2 × lado corto**);
- canal alfa (prohibido salvo en el ícono, que debe ser RGBA opaco);
- formato y peso (ícono ≤ 1024 KB, XR ≤ 8 MB);
- cantidades por tipo de dispositivo (máx. 8; mín. 4 en teléfono para promoción, 4 en pantallas grandes, 4 en XR, 2 + 2 en Automotive).

Corrige todo lo que salga `ERROR`; los `AVISO` son recomendaciones. Además, revisa **visualmente** al menos una imagen de cada tipo:
- leyendas ≤ 20 % del área y sin claims ni CTA;
- sin marcos de dispositivo;
- foco centrado en el gráfico de funciones;
- colores que no se funden con el fondo de Play;
- leyendas sin faltas de ortografía.

---

## 8. Textos de la ficha (`TEXT`)

Genera `final/listing-text.<locale>.md` con:

- **Descripción breve (≤ 80 caracteres):**
  - Resume el propósito principal en lenguaje simple y destaca qué la hace única.
  - Sin jerga y sin repetir los mensajes de los screenshots ni del gráfico de funciones.
  - Sin "el mejor", "N.º 1", "nuevo", "gratis", "descuento", sin llamadas a la acción y sin relleno de palabras clave.
  - Formato: punto final solo si hay varias oraciones. Se permiten letras, puntos, comas, "&" y caracteres propios del idioma (¿ ¡ ñ). **Sin emojis, sin ★/☆, sin signos repetidos, sin saltos de línea y sin mayúsculas sostenidas** (se permiten siglas y © ® ™).
  - Cuenta los caracteres y muestra el conteo.
- **Texto alternativo** del gráfico de funciones y de cada screenshot (≤ 140, sin "foto de"/"imagen de"), con su conteo.
- (Opcional) un **guion de video de vista previa** de 30 s: uso real en los primeros 10 s, ≥ 80 % de experiencia en la app, leyendas legibles sin claims, apto para verse sin sonido.

El título (30 caracteres) y la descripción completa (4000) tienen límites propios en Play Console. Confírmalos ahí si el usuario los pide.

---

## 9. Estructura y entrega

```
playstore-assets/
  brand.json
  prompts/
  raw/              # arte generado sin procesar
  screens/          # capturas reales
  templates/        # copias editadas de las plantillas
  scripts/          # compose.mjs, validate.py
  final/
    icon-512.png
    feature-graphic-1024x500.png
    phone/01.png … 08.png
    tablet-7/  tablet-10/  chromebook/
    wear/  tv/  tv-banner-1280x720.png
    automotive/  xr/
    listing-text.es-419.md
```

**Opcional (fastlane supply):** si el proyecto usa fastlane o el usuario lo pide, copia también los archivos a
`fastlane/metadata/android/<locale>/images/` con estos nombres: `icon.png`, `featureGraphic.png`, `tvBanner.png`, `phoneScreenshots/1.png…`, `sevenInchScreenshots/`, `tenInchScreenshots/`, `tvScreenshots/` y `wearScreenshots/`. Copia también `short_description.txt`. Así `fastlane supply` sube todo de una vez.

Sugiere agregar `playstore-assets/raw/` al `.gitignore` si pesa mucho. Al terminar, informa en pocas líneas:
- qué quedó en `final/` y el resultado del validador;
- qué motor se usó;
- de qué archivos salió cada dato de marca;
- qué queda manual: subir los recursos a Play Console, pegar los textos alternativos, el video de YouTube y, si aplica, desmarcar "Marketing externo".

Si el agente no puede generar imágenes ni ejecutar código, entrega los prompts de `prompts/` listos para pegar en un generador externo, junto con los comandos de composición y validación.

## Ejemplos

- "hazme el ícono de Play" → reutiliza el ícono adaptativo si existe; si no, genera arte a sangre → `icon.html` → `final/icon-512.png` (RGBA opaco, ≤ 1024 KB) → valida.
- "hazme el feature graphic" → prompt FEATURE → arte ≈ 2:1 → `feature-graphic.html` con foco centrado → 1024 × 500 sin alfa → valida y escribe el texto alternativo.
- "hazme los screenshots" → detecta los dispositivos → captura real con `adb` y barra limpia → teléfono 1440 × 2560 con leyendas cortas (≥ 4 para promoción), tablets 2560 × 1440 sin leyendas, Wear 1:1 solo UI → valida → textos alternativos.
- "el kit completo de Google Play" → resume la marca y los dispositivos, anuncia cuántas imágenes se generarán y con qué motor, espera la confirmación → ICON, FEATURE, SHOTS por dispositivo, TV si aplica, TEXT, y la copia opcional a fastlane.
