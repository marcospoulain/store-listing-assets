# Capturing real screens on Apple simulators

Requires macOS with Xcode (`xcrun simctl`). On Linux or Windows there is no iOS simulator: use the web route (`capture-web.md`) if the app has a web build, or ask the user for captures.

`S` below is `python3 SKILL_DIR/scripts/ios_sim.py`.

## 1. Boot the right device

```bash
S list                 # devices available, grouped by class, with the one it would pick
UDID=$(S boot iphone)  # iphone | ipad | watch | tv | vision
```

`boot` picks an installed simulator whose native resolution is an accepted App Store size (newest Pro Max for `iphone`, iPad Pro 13-inch for `ipad`, Apple Watch Ultra for `watch`, Apple TV 4K, Apple Vision Pro), boots it, waits until it is ready and prints the UDID. If none exists it creates one from the newest installed runtime. If the runtime itself is missing it prints the command to download it (`xcodebuild -downloadPlatform iOS`, several GB — ask the user first).

If your agent has its own iOS Simulator tool, attach it to this UDID so the user can watch and so you can tap; the script and the tool can be used on the same device.

## 2. Build and install the app for the simulator

Read the project's own scripts first (`package.json` scripts, `Makefile`, `fastlane/Fastfile`, README) and use them if they exist. Otherwise:

| Stack | Build + install on simulator `$UDID` |
|---|---|
| Native (Xcode) | `xcodebuild -workspace X.xcworkspace -scheme App -configuration Debug -destination "platform=iOS Simulator,id=$UDID" -derivedDataPath store-assets/.build build` (use `-project X.xcodeproj` if there is no workspace; list schemes with `xcodebuild -list`). Then `xcrun simctl install $UDID store-assets/.build/Build/Products/Debug-iphonesimulator/App.app` |
| Expo | `npx expo run:ios --device $UDID` (does a prebuild; with a dev client the dev menu can appear — prefer `--configuration Release`). Expo Go also works for a pure-JS app: `npx expo start --ios` |
| React Native CLI | `npx react-native run-ios --udid $UDID --mode Release` |
| Flutter | `flutter run -d $UDID` (debug only on simulators — set `debugShowCheckedModeBanner: false`), or `flutter build ios --simulator` then `simctl install` the `build/ios/iphonesimulator/Runner.app` |
| Kotlin Multiplatform | the `iosApp` Xcode project, as native |
| Capacitor / Ionic | `npx cap sync ios`, then the `ios/App` workspace as native |

Launch: `xcrun simctl launch $UDID <bundle.id>` (bundle id from `detect_project.py`). Add `store-assets/.build/` to `.gitignore`.

Release-like builds matter: debug overlays, the React Native dev menu, Flutter's debug banner and "Running in Expo Go" bars must not appear in a screenshot.

watchOS, tvOS, visionOS: same `xcodebuild` with `-destination "platform=watchOS Simulator,id=…"` / `tvOS Simulator` / `visionOS Simulator` and the matching scheme.

## 3. Make the device presentable

```bash
S statusbar $UDID                 # 9:41, full signal, Wi-Fi, 100 % battery
S appearance $UDID light          # or dark, matching brand.json
```

Language and region are per launch:

```bash
xcrun simctl launch $UDID <bundle.id> -AppleLanguages "(es)" -AppleLocale es_CL
```

Grant permissions up front so no system dialog appears: `xcrun simctl privacy $UDID grant all <bundle.id>` (or a single service: `photos`, `location`, `camera`, `contacts`, `calendar`, `microphone`). Notification prompts cannot be pre-granted this way; dismiss them through navigation or avoid triggering them.

Seed data: `xcrun simctl addmedia $UDID photo.jpg` for the photo library, `xcrun simctl location $UDID set <lat>,<lon>` for location, `xcrun simctl push $UDID <bundle.id> payload.json` for a notification.

## 4. Reach each screen and capture

```bash
S openurl $UDID "myapp://documents/123"          # deep link or universal link
S shot $UDID store-assets/screens/iphone/01.png   # waits briefly, captures at native resolution, prints WxH
```

`simctl` cannot tap. To navigate beyond deep links, use the first that applies:

1. **Existing UI tests / fastlane snapshot** — `bundle exec fastlane snapshot` writes to `fastlane/screenshots/`. Copy from there.
2. **Your agent's simulator tool** (tap, swipe, type) if the session has one.
3. **Maestro** (`brew install maestro`, ask first): write `store-assets/flows/screens.yaml`

   ```yaml
   appId: com.example.app
   ---
   - launchApp: { clearState: false }
   - tapOn: "Documentos"
   - takeScreenshot: store-assets/screens/iphone/02
   - tapOn: { id: "add_button" }
   - takeScreenshot: store-assets/screens/iphone/03
   ```

   and run `maestro --device $UDID test store-assets/flows/screens.yaml`. Find tappable labels and ids with `maestro hierarchy`.
4. **A screenshot UI test you add** (XCUITest with `XCUIScreen.main.screenshot()` / `XCTAttachment`, or Flutter `integration_test` with `binding.takeScreenshot`) — this adds a test file to the repo: ask first.
5. **A launch argument** the app reads in debug builds to open a screen with demo data (`simctl launch $UDID <bundle.id> -storeScreenshot documents`). Edits app code: ask first.

Simulator captures are PNGs with an alpha channel, which the App Store rejects. Every capture goes through `compose.mjs` or `validate.py fit apple-iphone` (or `fit flatten`) before it lands in `final/`.

After each capture, look at the image. Wait for network content and animations to finish before capturing (`S shot --delay 2`).

iPad: repeat with `S boot ipad` — do not upscale iPhone captures. Capture landscape only if the app is landscape-first.

## 5. Mac apps

Build and run the app (`xcodebuild -scheme App -destination "platform=macOS" build`, then `open` the `.app`). Resize the window to 1440 × 900 points and capture just that window:

```bash
osascript -e 'tell application "System Events" to tell process "App" to set size of window 1 to {1440, 900}'
screencapture -o -l "$(osascript -e 'tell application "App" to id of window 1')" store-assets/screens/mac/01.png
```

`screencapture` needs Screen Recording permission for the terminal or agent app; if it produces a blank image, tell the user to grant it in System Settings → Privacy & Security. On a Retina display the capture is 2880 × 1800. Then `validate.py fit apple-mac` to guarantee the exact size, or compose it on a backdrop.

## 6. Clean up

```bash
S statusbar-clear $UDID
S shutdown $UDID        # only devices you booted
```
