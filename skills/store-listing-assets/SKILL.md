---
name: store-listing-assets
description: Generate the images the Apple App Store and Google Play require for a store listing — real screenshots per device type, app icon, feature graphic, product page header, TV banner — at the official pixel sizes, by reading the project's code, building the app, booting iOS simulators / Android emulators (or a browser for web apps), capturing the real UI, composing and validating the final files. Use when the user asks for store screenshots, "capturas de la tienda", "screenshots para App Store / Google Play", app icon, feature graphic, "gráfico de funciones", "cabecera del App Store", listing assets, or "el kit completo" for a mobile, tablet, watch, TV or desktop app.
---

# Store listing assets from the code

You are inside the user's app repository. Produce the graphic assets for its App Store and/or Google Play listing: read the code, run the real app on simulators/emulators, capture the real screens, compose them at the exact official sizes, validate, and hand over files ready to upload.

Talk to the user in their language. Text that appears inside images (captions, titles) is written in the listing's language (default: the app's primary locale). Prompts sent to image generators are in English.

`SKILL_DIR` below means the folder that contains this file. Run its scripts in place; never copy them into the user's repo. Everything you produce goes in `store-assets/` at the repo root.

## Requests → assets

| User asks for | Apple App Store | Google Play |
|---|---|---|
| screenshots / capturas | iPhone 6.9" (+ iPad 13" if the app runs on iPad, + Mac / Watch / TV / Vision if targeted) | phone (+ tablet 7"/10", Chromebook, Wear OS, TV, Automotive, XR if supported) |
| icon / ícono | 1024×1024 PNG, no alpha | 512×512 32-bit PNG |
| header / cabecera, search image, universal | 3840×1646 · 3840×2560 · 5244×2950 | — |
| feature graphic / gráfico de funciones | — | 1024×500 |
| TV banner | — | 1280×720 |
| listing text / textos | — (only if asked: subtitle, promo text) | short description ≤ 80 chars, alt texts ≤ 140 |
| full kit / kit completo | everything above that applies | everything above that applies |

If the user names no store, produce for every store the project ships to (step 1 tells you). Exact sizes, counts and content rules live in `references/apple-specs.md` and `references/google-play-specs.md` — read the one(s) you need before composing. Stores change these specs; if the user quotes different numbers or the reference looks stale, check the official URLs listed at the top of each reference.

## Workflow

### 1. Detect the project

```bash
python3 SKILL_DIR/scripts/detect_project.py .
```

It prints JSON: framework(s) (native iOS, native Android, Flutter, React Native / Expo, Kotlin Multiplatform, Capacitor, web), target stores, device types the app supports on each store, bundle id / application id, existing automation you can reuse (fastlane snapshot / screengrab, Maestro flows, UI tests, Playwright), and which tools this machine has (Xcode `simctl`, `adb`, Android emulator, Maestro, Playwright, Pillow). Treat it as a first pass: open the files it cites and correct anything it got wrong.

### 2. Plan, then confirm once

Write `store-assets/plan.md` and show the user a short summary:

- stores and device types, with the exact output size for each;
- the 4–8 screens to capture (route / screen name, what state and demo data it shows, caption, alt text). Pick the screens that show the app's value, most important first. On Play the first three must be UI-forward;
- how you will reach each screen (see step 4) and how you will get past login, if any;
- the art engine for icon / banners (step 5) and how many paid generations it implies.

Proceed without waiting when the request is one small asset and nothing is ambiguous. Wait for a "yes" before: a batch of paid image generations, creating simulators or downloading system images (several GB), or adding any code to the app (demo-data hooks, test files).

### 3. Extract the brand → `store-assets/brand.json`

Read name, colors, fonts, logo, tone and benefit copy from the code — never invent them. Where to look per framework, and the `brand.json` schema, are in `references/brand-extraction.md`. Reuse an existing `brand.json` (also legacy `appstore-assets/` or `playstore-assets/`) and update it if the code changed.

### 4. Capture the real screens

Both stores require screenshots of the real app. **Never draw, mock or AI-generate the UI.** Captures go to `store-assets/screens/<device>/NN.png`.

Pick the first route that works, per platform:

| Target | Route | Read |
|---|---|---|
| iPhone, iPad, Apple Watch, Apple TV, Vision Pro | Xcode simulators via `scripts/ios_sim.py` (macOS only) | `references/capture-ios.md` |
| Android phone, tablet, Wear OS, TV, Automotive, XR | Android emulators or a connected device via `scripts/android_emu.py` (macOS, Linux, Windows) | `references/capture-android.md` |
| Web app, PWA, Expo web, Flutter web — or a fallback when no simulator is available | headless browser at device viewports via `scripts/capture_web.mjs` | `references/capture-web.md` |
| Mac app | run the app and capture its window | `references/capture-ios.md` (Mac section) |

Each reference covers: building for the simulator per framework, booting the right device, clean status bar, locale and dark mode, navigating to each screen, and capture. In short:

```bash
# iOS — boots (or creates) the device whose native resolution is an accepted App Store size
python3 SKILL_DIR/scripts/ios_sim.py boot iphone          # prints the UDID; also: ipad, watch, tv, vision
python3 SKILL_DIR/scripts/ios_sim.py statusbar <UDID>     # 9:41, full bars, full battery
python3 SKILL_DIR/scripts/ios_sim.py shot <UDID> store-assets/screens/iphone/01.png

# Android — boots (or creates) an AVD of the right class
python3 SKILL_DIR/scripts/android_emu.py boot phone        # prints the serial; also: tablet, wear, tv, automotive, xr
python3 SKILL_DIR/scripts/android_emu.py demo-on <SERIAL>  # clean status bar (SystemUI demo mode)
python3 SKILL_DIR/scripts/android_emu.py shot <SERIAL> store-assets/screens/phone/01.png

# Web
node SKILL_DIR/scripts/capture_web.mjs http://localhost:3000/route store-assets/screens/iphone/01.png --device iphone-6.9
```

Reaching each screen, in order of preference:

1. **Automation the repo already has** — fastlane `snapshot` / `screengrab`, Maestro flows, XCUITest / Espresso / Compose screenshot tests, Flutter `integration_test`, Detox, Playwright. Run it and collect the images.
2. **Deep links and routes** — `ios_sim.py openurl`, `android_emu.py deeplink`, a URL for web. Find them in the router / navigation graph / URL scheme / intent filters.
3. **Your own simulator or browser tools**, if this agent session has them (an iOS Simulator tool, computer use, a browser tool): tap through the app and screenshot.
4. **A Maestro flow you write** at `store-assets/flows/screens.yaml` (works on iOS simulators and Android emulators; one `takeScreenshot` per screen). On Android you can also tap with `adb shell input` using coordinates from `android_emu.py ui <SERIAL>`.
5. **A debug-only hook** (launch argument or env var that opens a given screen with demo data). This edits the app's code: propose it, get a yes, keep it behind a debug flag.

Look at every capture after taking it. Redo any that show a loading spinner, an empty state, a permission dialog, a keyboard covering the content, a debug banner, lorem ipsum, or real personal data. Use realistic demo data. If a login wall blocks you, ask the user for a demo account or a seed/mock mode — never type the user's real credentials and never create accounts on a production backend.

If no simulator, emulator or web build is possible on this machine, say exactly what is missing (the scripts print the install command) and ask the user to drop captures into `store-assets/screens/<device>/`; then continue from step 5.

### 5. Brand art (icon, header, feature graphic, banners, screenshot backdrops)

Prefer existing brand assets: if the repo has a vector logo or an adaptive icon, compose the icon from it instead of generating a new one. Otherwise use, in order: the agent's own image tool → an image API whose key is already in the environment → art built in code (SVG / CSS gradients and shapes from the brand). Engines, prompt templates and rules are in `references/art-generation.md`. Generated art never contains text or UI; titles are added in step 6 with the brand's real font.

### 6. Compose at exact pixels

```bash
node SKILL_DIR/scripts/compose.mjs SKILL_DIR/templates/screenshot.html \
  store-assets/final/google-play/phone/01.png 1440 2560 \
  --var SCREEN=store-assets/screens/phone/01.png \
  --var CAPTION="Tus documentos siempre a mano" \
  --var PRIMARY=#0B5FFF --var SECONDARY=#6C2BD9 --var FOREGROUND=#FFFFFF \
  --var FONT=assets/fonts/Inter-Bold.ttf
```

`compose.mjs` fills `{{PLACEHOLDERS}}` in a template, renders it with headless Chromium at the exact size, and writes PNG without alpha (or `--rgba` for the Play icon, `.jpg` for JPEG). File paths in `--var` are relative to the repo root. Needs Playwright: `npm i -D playwright && npx playwright install chromium` (ask before adding a dev dependency; a global install also works).

| Template | Use for | Key vars |
|---|---|---|
| `templates/screenshot.html` | any screenshot: caption + real capture on a brand backdrop. Omit `CAPTION` for a capture-only image | `SCREEN`, `CAPTION`, `SUBCAPTION`, `BG`, `PRIMARY`, `SECONDARY`, `FOREGROUND`, `FONT`, `FRAME` (`none` or `bezel`), `UI_SCALE` |
| `templates/banner.html` | Play feature graphic, TV banner, App Store header / search / universal | `BG`, `LOGO`, `TITLE`, `SUBTITLE`, `SAFE_W`, `SAFE_H`, `SHIFT_Y`, `LAYOUT`, colors, `FONT` |
| `templates/icon.html` | store icon from a symbol or logo | `SYMBOL`, `SYMBOL_SIZE`, `PRIMARY`, `SECONDARY` |

Copy a template into `store-assets/templates/` and edit it when the brand needs a different layout — keep the canvas size and the rules below.

Rules that differ between stores (details in the spec references):

- **Google Play**: no device frames (`FRAME=none`); captions ≤ 20 % of the image; no ranking / price / promo claims and no calls to action; tablet and Chromebook screenshots carry no marketing text; Wear OS, Automotive and XR are the raw UI only, resized with `validate.py fit`; phone canvas is 9:16 even though captures are taller.
- **App Store**: screenshots show the app in use; a generic bezel is fine (`FRAME=bezel`) but never Apple hardware imagery or logos; a capture at native simulator resolution is a valid final file once its alpha channel is removed (`validate.py fit apple-iphone`); header / search / universal keep everything important inside the safe area (the universal one is off-center: see the spec reference).
- **Both**: no alpha in screenshots and banners, no third-party logos, no store badges, clean status bar.

A raw capture that already has an accepted size can be the final file: `python3 SKILL_DIR/scripts/validate.py fit <kind> <in> <out>` flattens alpha and center-crops/resizes to the target (`validate.py kinds` lists them).

### 7. Validate, look, deliver

```bash
python3 SKILL_DIR/scripts/validate.py check store-assets/final
python3 SKILL_DIR/scripts/validate.py safe-area store-assets/final/apple/header-3840x1646.png   # overlay preview
```

`check` verifies size, aspect ratio, alpha, format, file weight and per-device counts for both stores (needs Pillow: `pip install pillow`). Fix every `ERROR`; `WARN` lines are recommendations. Then open at least one image of each kind and check what a script cannot: captions are spelled right and fit, nothing important is clipped, the UI is the real app, the set looks consistent.

Clean up: `ios_sim.py statusbar-clear <UDID>`, `android_emu.py demo-off <SERIAL>`, shut down simulators you booted, stop dev servers you started.

Report in a few lines: the files in `store-assets/final/` and the validator result, which device each capture came from, the art engine used, where each brand value came from, and what is left for the user (uploading to App Store Connect / Play Console, pasting alt texts, anything you could not capture and why). If the project uses fastlane, offer to copy the files into `fastlane/screenshots/<locale>/` (deliver) and `fastlane/metadata/android/<locale>/images/` (supply) — layout in the spec references.

## Output layout

```
store-assets/
  brand.json   plan.md
  screens/<device>/NN.png        # raw real captures
  raw/                           # generated art, unprocessed
  prompts/                       # prompts used, for reproducibility
  templates/  flows/             # only if you customized a template / wrote a Maestro flow
  final/
    apple/        icon-1024.png  header-3840x1646.png  search-3840x2560.png  universal-5244x2950.png
                  iphone-6.9/01.png …  ipad-13/  mac/  watch/  tv/  vision/
    google-play/  icon-512.png  feature-graphic-1024x500.png  tv-banner-1280x720.png
                  phone/01.png …  tablet-7/  tablet-10/  chromebook/  wear/  tv/  automotive/  xr/
                  listing-text.<locale>.md
```

Suggest adding `store-assets/raw/` to `.gitignore`.

## Guardrails

- Never print, log or write API keys; only check that an environment variable exists.
- Do not change the app's source, dependencies or signing to get a screenshot without the user's yes. Never commit or push on your own.
- Do not erase or reset simulators / emulators you did not create, and do not uninstall the user's apps from them.
- Captions and listing text: no "best", "#1", "free", "new", "sale", no "download now". These get listings rejected on Play and are risky on the App Store.
- If you cannot run tools at all (no shell), still deliver: the plan, the prompts, and the exact commands for the user to run.
