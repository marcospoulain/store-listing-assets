# Extracting the brand from the repo

Write `store-assets/brand.json` from what the code says. Record where each value came from in `sources` so the user can check it. Ask only when something cannot be deduced or two sources conflict (for example a marketing site and the app using different palettes — the app wins by default).

## Where to look

**Name and copy**

- iOS: `Info.plist` (`CFBundleDisplayName`, `CFBundleName`), `InfoPlist.strings`, `Localizable.strings` / `.xcstrings`.
- Android: `res/values/strings.xml` (`app_name`), `android:label` in `AndroidManifest.xml`, `values-<lang>/strings.xml`.
- Expo / React Native: `app.json` / `app.config.*` (`name`, `slug`), `package.json`.
- Flutter: `pubspec.yaml`, `lib/l10n/*.arb`.
- Web: `<title>`, `manifest.json` / `manifest.webmanifest`, landing page copy.
- Anything already written for the stores: `fastlane/metadata/<locale>/name.txt`, `subtitle.txt`, `description.txt`, `fastlane/metadata/android/<locale>/title.txt`, `short_description.txt`, `full_description.txt`; also `README.md`.
- Benefit copy for captions: onboarding screens, empty states, paywall, i18n files, landing page.

**Colors**

- iOS: `Assets.xcassets/AccentColor.colorset/Contents.json`, other `*.colorset`, `Color` / `UIColor` extensions.
- Android: `res/values/colors.xml`, `themes.xml` (`colorPrimary`, `colorSecondary`), `values-night/`; Compose `ui/theme/Color.kt`, `Theme.kt` (`lightColorScheme(primary = …)`); adaptive icon background `@color/ic_launcher_background`.
- Expo / React Native: `theme/`, `constants/Colors.ts`, `tailwind.config.*` (NativeWind), `app.json` (`splash.backgroundColor`, `android.adaptiveIcon.backgroundColor`).
- Flutter: `ThemeData`, `ColorScheme.fromSeed(seedColor: …)`.
- Web: `tailwind.config.*`, CSS variables (`:root { --primary … }`, Tailwind v4 `@theme`), shadcn `components.json`, `theme.ts`, `theme_color` in the web manifest.

**Typography**: font files (`.ttf`, `.otf`, `.woff2`) in `assets/fonts/`, `res/font/`, `public/fonts/`; `UIAppFonts` in `Info.plist`; `expo-font` / `useFonts`; `fonts:` in `pubspec.yaml`; `next/font`, `@font-face`. `compose.mjs` needs a local font file; if the app uses a system font (SF Pro, Roboto), leave `fonts.files` empty and the templates fall back to the system UI font.

**Logo and current icon**: `Assets.xcassets/AppIcon.appiconset/` (or a `.icon` bundle), `res/mipmap-*/ic_launcher*`, `res/drawable/ic_launcher_foreground.xml`, `assets/icon.png`, `assets/adaptive-icon.png`, `public/logo.svg`, `favicon.*`. Prefer vectors.

**Visual style**: corner radii, shadows, illustration style, mascot, whether dark mode is the default — read the main screen and the core components.

**Key screens**: the router / navigation graph (Expo Router `app/`, React Navigation, `NavHost`, `GoRouter`, SwiftUI `NavigationStack` / `TabView`, storyboards, Next.js `app/`). Choose 4–8 that show the value of the app; skip settings, login and legal screens.

## `brand.json`

```json
{
  "appName": "",
  "tagline": "",
  "oneLiner": "what the app does, in one sentence",
  "audience": "",
  "tone": "",
  "locale": "es-419",
  "locales": ["es-419", "en-US"],
  "isGame": false,
  "colors": { "primary": "#", "secondary": "#", "accent": "#", "background": "#", "foreground": "#" },
  "darkModeDefault": false,
  "fonts": { "heading": "", "body": "", "files": ["path/to/font.ttf"] },
  "logo": "path",
  "currentIcon": "path",
  "visualStyle": "",
  "heroElement": "the one object or symbol that stands for the app",
  "stores": {
    "apple": { "bundleId": "", "devices": ["iphone", "ipad"] },
    "googlePlay": { "applicationId": "", "devices": ["phone", "tablet"] }
  },
  "screens": [
    { "id": "01", "name": "Home", "route": "/", "howToReach": "deeplink myapp://home", "state": "3 documents, one expiring soon",
      "caption": "", "subcaption": "", "altText": "" }
  ],
  "sources": ["app.json → name", "constants/Colors.ts → primary"]
}
```

`foreground` is the text color used over `primary` / `secondary` in captions: make sure it contrasts (white on saturated colors, near-black on pastel ones).

Captions: at most about six words, benefit first, in the listing language, no claims ("best", "#1", "free", "new") and no calls to action. Alt texts describe what the screen shows, ≤ 140 characters, without "image of".

When the listing has several locales, the captures and captions are redone per locale (launch the app in that language — see the capture references) into `final/<store>/<locale>/…` only if the user asks for localized sets; otherwise produce the primary locale.
