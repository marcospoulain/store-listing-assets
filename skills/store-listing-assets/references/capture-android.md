# Capturing real screens on Android emulators and devices

Works on macOS, Linux and Windows. Needs the Android SDK: `platform-tools` (`adb`) and, for emulators, the `emulator` package plus a system image. A phone or tablet connected over USB with debugging enabled works too and needs no emulator.

`A` below is `python3 SKILL_DIR/scripts/android_emu.py`.

## 1. Boot the right device

```bash
A list                    # SDK location, AVDs grouped by class, connected devices
SERIAL=$(A boot phone)    # phone | tablet | wear | tv | automotive | automotive-portrait | xr | foldable
```

`boot` reuses an AVD of that class if one exists (already running or not), otherwise creates one from an installed system image, starts it and waits for boot to complete, then prints the adb serial. When the SDK lacks the emulator or a system image it prints the exact `sdkmanager` commands; those download 1–2 GB each, so ask the user before running them.

| Class | Device profile | System image tag | Capture size |
|---|---|---|---|
| phone | Pixel (e.g. `pixel_9`) | `google_apis` | 1080 × 2424 → compose on 1440 × 2560 |
| tablet | `pixel_tablet` | `google_apis` | 2560 × 1600 → compose on 2560 × 1440 |
| foldable | `pixel_9_pro_fold` | `google_apis` | native |
| wear | `wearos_large_round` | `android-wear` | 454 × 454 (1:1) |
| tv | `tv_1080p` | `google-tv` / `android-tv` | 1920 × 1080 |
| automotive | `automotive_1024p_landscape` | `android-automotive` | 1024 × 768 |
| automotive-portrait | `automotive_portrait` | `android-automotive` | 800 × 1280 |
| xr | XR headset profile | `android-xr` | fit to 3840 × 2400 |

Chromebook screenshots: capture on the tablet AVD in landscape (or a desktop AVD if installed); Play applies the same large-screen rules. A tablet capture must show the tablet layout — if the app only stretches the phone UI, tell the user rather than hiding it.

Use `google_apis` images rather than `google_apis_playstore` when you need `adb root`-style freedom; either works for screenshots.

## 2. Build and install

Read the project's own scripts first. Otherwise:

| Stack | Build + install on `$SERIAL` |
|---|---|
| Native (Gradle) | `./gradlew :app:assembleDebug` then `adb -s $SERIAL install -r app/build/outputs/apk/debug/app-debug.apk` (pick the flavor the user ships; list tasks with `./gradlew tasks --all`) |
| Expo | `npx expo run:android --device` (prebuild) — prefer `--variant release` if signing is configured for debug keystore; Expo Go also works for pure-JS apps |
| React Native CLI | `npx react-native run-android --mode release --deviceId $SERIAL` (falls back to debug if release signing is missing: then shake-menu and redbox must not be visible) |
| Flutter | `flutter build apk --debug` + `adb install`, or `flutter run -d $SERIAL --release` |
| Kotlin Multiplatform | the `androidApp` / `composeApp` module, as native |
| Capacitor / Ionic | `npx cap sync android`, then `android/` as native |
| Wear / TV / Automotive modules | the matching Gradle module (`:wear:assembleDebug`, …) installed on that emulator |

Launch: `adb -s $SERIAL shell monkey -p <application.id> -c android.intent.category.LAUNCHER 1` (use `LEANBACK_LAUNCHER` on TV).

## 3. Make the device presentable

```bash
A demo-on $SERIAL        # SystemUI demo mode: 12:00, full Wi-Fi and signal, full battery, no notifications
adb -s $SERIAL shell cmd uimode night no                      # or yes, matching brand.json
adb -s $SERIAL shell cmd locale set-app-locales <application.id> --locales es-419   # Android 13+
adb -s $SERIAL shell settings put system font_scale 1.0
```

Demo mode is a phone/tablet SystemUI feature; on Wear OS, TV and Automotive images it may do nothing, which is fine because those have no phone status bar.

Grant runtime permissions so no dialog appears: `adb -s $SERIAL shell pm grant <application.id> android.permission.POST_NOTIFICATIONS` (and `CAMERA`, `ACCESS_FINE_LOCATION`, …), or install with `adb install -g`.

Seed data: `adb push photo.jpg /sdcard/Pictures/` then trigger a media scan; `adb emu geo fix <lon> <lat>` for location.

## 4. Reach each screen and capture

```bash
A deeplink $SERIAL "myapp://documents/123" <application.id>   # VIEW intent
A shot $SERIAL store-assets/screens/phone/01.png               # waits briefly, captures, prints WxH
```

Navigating beyond deep links, first that applies:

1. **Existing automation** — `bundle exec fastlane screengrab`, Maestro flows, Espresso / Compose screenshot tests, Flutter `integration_test`.
2. **Start an Activity directly** when it is exported: `adb shell am start -n <application.id>/.ui.DetailActivity --es id 123`.
3. **Tap by coordinates from the view hierarchy**:

   ```bash
   A ui $SERIAL                      # lists visible elements: text / content-desc / resource-id and center x,y
   adb -s $SERIAL shell input tap 540 1210
   adb -s $SERIAL shell input text "Chile"
   adb -s $SERIAL shell input swipe 540 1800 540 600 300
   adb -s $SERIAL shell input keyevent KEYCODE_BACK
   ```

   Re-run `A ui` after each step; coordinates change between screens. Compose apps expose text and content descriptions; resource ids only with `testTagsAsResourceId`.
4. **Maestro** — the same `store-assets/flows/screens.yaml` as on iOS, run with `maestro --device $SERIAL test …`.
5. **Your agent's own device or computer-use tools**, if the session has them.
6. **A debug-only intent extra or screenshot test you add** — edits the repo: ask first.

Hide the keyboard before capturing (`input keyevent KEYCODE_BACK` once if it is open), wait for content to load (`A shot --delay 2`), and look at each image.

Landscape captures (tablet, Chromebook, games):

```bash
adb -s $SERIAL shell settings put system accelerometer_rotation 0
adb -s $SERIAL shell settings put system user_rotation 1     # 0 portrait, 1 landscape
```

## 5. From capture to final

- Phone: compose on a 9:16 canvas with `templates/screenshot.html` (`FRAME=none`). The capture is taller than 9:16, so it is shown whole inside the canvas, never stretched.
- Tablet / Chromebook: `validate.py fit gp-tablet` crops 16:10 to 16:9 from the center. If that would cut a top or bottom bar, compose with `templates/screenshot.html` and no caption instead, which letterboxes on a flat brand color.
- Wear OS: `validate.py fit gp-wear` (center square, no mask, no background).
- TV: the 1920 × 1080 capture as-is (`fit gp-tv` to strip alpha).
- Automotive: `fit gp-automotive-landscape` / `fit gp-automotive-portrait`.
- XR: `fit gp-xr`.

## 6. Clean up

```bash
A demo-off $SERIAL
A stop $SERIAL          # only emulators you started
```
