# store-listing-assets

**[Español](#español) · [English](#english)**

Una skill para agentes de código (Claude Code, Codex, Antigravity, Cursor, Gemini CLI y cualquiera que lea `SKILL.md`) que genera las imágenes que piden el **App Store** y **Google Play**: el agente lee tu código, compila la app, levanta simuladores de iOS o emuladores de Android, captura las pantallas reales y entrega los archivos en las medidas oficiales, ya validados.

An agent skill that produces the images the **App Store** and **Google Play** ask for: the agent reads your code, builds the app, boots iOS simulators or Android emulators, captures the real screens and delivers validated files at the official sizes.

---

## Español

### Qué hace

Dentro de la carpeta de tu app, pídele al agente:

```text
hazme los screenshots para el App Store y Google Play
hazme el ícono de Play y el gráfico de funciones
hazme la cabecera del App Store
hazme el kit completo de las tiendas
```

El agente:

1. **Detecta el proyecto**: framework (iOS nativo, Android nativo, Flutter, React Native / Expo, Kotlin Multiplatform, Capacitor, web / PWA), tiendas, y qué dispositivos soporta la app (iPhone, iPad, Mac, Apple Watch, Apple TV, Vision Pro; teléfono, tablet, Chromebook, Wear OS, Android TV, Automotive, XR).
2. **Arma un plan** con las pantallas a capturar, los titulares y las medidas, y te lo muestra.
3. **Extrae la marca** del código: nombre, colores, tipografías, logo y textos.
4. **Captura la app real**: compila, arranca el simulador o emulador correcto para cada tipo de dispositivo, limpia la barra de estado, navega a cada pantalla (deep links, Maestro, tests existentes o las herramientas del propio agente) y toma la captura. Si no hay simulador disponible, usa la versión web en un navegador con el viewport del dispositivo.
5. **Genera el arte de marca** (ícono, gráfico de funciones, cabecera) desde tu logo, con el generador de imágenes del agente o una API, o con código.
6. **Compone** cada archivo en píxeles exactos, con tu fuente y tus colores.
7. **Valida** medidas, relación de aspecto, canal alfa, formato, peso y cantidades según las reglas de cada tienda.

Todo queda en `store-assets/final/apple/` y `store-assets/final/google-play/`, listo para subir.

La interfaz **nunca se inventa ni se genera con IA**: las dos tiendas exigen capturas de la app real.

### Qué genera

| Tienda | Recursos |
|---|---|
| Apple App Store | Screenshots de iPhone 6.9" (1320×2868), iPad 13" (2064×2752), Mac, Apple Watch, Apple TV y Vision Pro · ícono 1024×1024 · cabecera 3840×1646 · imagen de búsqueda 3840×2560 · recurso universal 5244×2950 |
| Google Play | Screenshots de teléfono (1440×2560), tablet 7"/10" y Chromebook (2560×1440), Wear OS, Android TV, Automotive y XR · ícono 512×512 · gráfico de funciones 1024×500 · banner de TV 1280×720 · descripción breve y textos alternativos |

### Instalación

Con el CLI de [skills](https://skills.sh) (detecta tu agente):

```bash
npx skills add marcospoulain/store-listing-assets
```

Como plugin de Claude Code:

```text
/plugin marketplace add marcospoulain/store-listing-assets
/plugin install store-listing-assets@store-listing-assets
```

O a mano: copia la carpeta `skills/store-listing-assets/` al directorio de skills de tu agente.

```bash
git clone https://github.com/marcospoulain/store-listing-assets
cp -r store-listing-assets/skills/store-listing-assets ~/.claude/skills/     # Claude Code (todos tus proyectos)
cp -r store-listing-assets/skills/store-listing-assets ~/.codex/skills/      # Codex
cp -r store-listing-assets/skills/store-listing-assets .agents/skills/       # dentro de un proyecto, para otros agentes
```

Para Antigravity, Cursor, Gemini CLI u otros, usa la carpeta de skills que indique su documentación.

### Requisitos

| Para | Necesitas |
|---|---|
| Capturas de iOS / iPadOS / watchOS / tvOS / visionOS | macOS con Xcode |
| Capturas de Android | Android SDK: `platform-tools`, `emulator` y una imagen de sistema (o un dispositivo por USB) |
| Capturas web y composición | Node 18+ y Playwright: `npm i -D playwright && npx playwright install chromium` |
| Validación | Python 3 y Pillow: `pip install pillow` |
| Opcional | [Maestro](https://maestro.dev) para navegar la app, fastlane para subir |

El agente te avisa qué falta y te pide permiso antes de descargar simuladores, generar imágenes de pago o tocar el código de tu app.

### Especificaciones

Las medidas se verificaron contra las páginas oficiales en noviembre de 2026 y están en [`references/apple-specs.md`](skills/store-listing-assets/references/apple-specs.md) y [`references/google-play-specs.md`](skills/store-listing-assets/references/google-play-specs.md), con los enlaces a las fuentes. Las tiendas las cambian: revísalas antes de publicar. Si encuentras una desactualizada, abre un issue o un PR.

---

## English

### What it does

Inside your app's folder, ask your agent:

```text
make the screenshots for the App Store and Google Play
make the Play icon and the feature graphic
make the App Store product page header
make the full store listing kit
```

The agent then:

1. **Detects the project**: framework (native iOS, native Android, Flutter, React Native / Expo, Kotlin Multiplatform, Capacitor, web / PWA), target stores, and the device types the app supports.
2. **Plans** the screens to capture, captions and sizes, and shows you the plan.
3. **Extracts the brand** from the code: name, colors, fonts, logo, copy.
4. **Captures the real app**: builds it, boots the right simulator or emulator per device type, cleans the status bar, navigates to each screen (deep links, Maestro, existing tests, or the agent's own tools) and takes the capture. Falls back to a browser at device viewports for web builds.
5. **Makes the brand art** (icon, feature graphic, header) from your logo, the agent's image tool or an API, or in code.
6. **Composes** every file at exact pixels with your font and colors.
7. **Validates** size, aspect ratio, alpha, format, weight and counts against each store's rules.

Output lands in `store-assets/final/apple/` and `store-assets/final/google-play/`. The UI is never mocked or AI-generated.

### Install

```bash
npx skills add marcospoulain/store-listing-assets
```

Claude Code plugin:

```text
/plugin marketplace add marcospoulain/store-listing-assets
/plugin install store-listing-assets@store-listing-assets
```

Or copy `skills/store-listing-assets/` into your agent's skills directory (`~/.claude/skills/`, `~/.codex/skills/`, a project's `.agents/skills/`, …).

### Requirements

- iOS-family captures: macOS with Xcode.
- Android captures: Android SDK with `platform-tools`, `emulator` and a system image, or a USB device.
- Web captures and composition: Node 18+ and Playwright.
- Validation: Python 3 with Pillow.

### What is inside

```
skills/store-listing-assets/
  SKILL.md                     workflow the agent follows
  references/                  store specs, brand extraction, capture guides (iOS, Android, web), art prompts
  scripts/
    detect_project.py          framework, stores, device types, ids, available tools → JSON
    ios_sim.py                 boot / create the right simulator, clean status bar, deep link, screenshot
    android_emu.py             boot / create the right AVD, demo mode, deep link, UI dump, screenshot
    capture_web.mjs            headless browser capture at store device viewports
    compose.mjs                HTML template → exact-size PNG / JPEG without alpha
    validate.py                check both stores' rules, fit images, App Store safe-area preview
  templates/                   screenshot, banner, icon
```

The scripts are plain CLIs and can be used without an agent; each prints its usage with `--help`.

## License

[MIT](LICENSE)
