# Capturing a web build at device viewports

Use this for web apps and PWAs (including ones shipped to Play as a Trusted Web Activity or wrapped with Capacitor), for Expo web and Flutter web builds of a mobile app, and as a fallback when no simulator or emulator can run on this machine.

A web capture of a native app is a fallback, not an equivalent: native navigation bars, fonts and platform widgets can differ. Say so in the final report when you used it for a native app, and prefer the simulator routes when they are available.

## 1. Serve the app

Use the project's own script (`npm run dev`, `npm run build && npm run start`, `npx expo start --web`, `flutter run -d web-server --web-port 8080`). Prefer a production build: dev overlays, HMR badges and framework error toasts must not appear. Start it in the background, wait until the port answers, and stop it when you finish.

## 2. Capture

```bash
node SKILL_DIR/scripts/capture_web.mjs <url> <out.png> --device <preset> [options]
```

| Preset | Viewport @ scale | Output | For |
|---|---|---|---|
| `iphone-6.9` | 440 × 956 @3 | 1320 × 2868 | App Store iPhone |
| `ipad-13` | 1032 × 1376 @2 | 2064 × 2752 | App Store iPad |
| `mac` | 1440 × 900 @2 | 2880 × 1800 | Mac App Store |
| `android-phone` | 412 × 915 @3.5 | 1442 × 3203 | Play phone (compose on 9:16) |
| `android-tablet` | 1280 × 720 @2 | 2560 × 1440 | Play tablet / Chromebook (final size) |
| `android-tablet-portrait` | 720 × 1280 @2 | 1440 × 2560 | Play tablet portrait |
| `tv` | 1920 × 1080 @1 | 1920 × 1080 | TV |

Options:

- `--dark` — `prefers-color-scheme: dark`.
- `--locale es-CL` — browser locale and `Accept-Language`.
- `--wait <ms>` — extra settle time after network idle (default 800).
- `--wait-for "<css selector>"` — wait until that element is visible.
- `--click "<css selector>"` — click before capturing; repeatable, runs in order.
- `--hide "<css selector>"` — hide elements (cookie banners, dev badges, chat widgets); repeatable.
- `--storage state.json` — a Playwright storage state, to start logged in with a demo account.
- `--landscape` — swap width and height of the preset.
- `--full-page` — capture the whole scroll height (rarely right for a store screenshot).

Mobile presets emulate touch and a mobile user agent so responsive and PWA code paths behave as on a phone.

For flows that need typing or several steps, write a short Playwright script instead (log in with a demo account, save `storageState`, then use `--storage`). If your agent has a browser tool, you can drive the page with it and still use this script for the final pixel-exact capture.

## 3. What a browser capture lacks

There is no OS status bar. That is acceptable on both stores. Do not paint a fake one. With `templates/screenshot.html` the capture sits in a rounded card, so the missing bar is not noticeable; for a full-bleed look, pass the capture as-is.
