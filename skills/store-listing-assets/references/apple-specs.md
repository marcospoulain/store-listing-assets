# Apple App Store — asset specifications

Official sources (checked November 2026 — re-check before relying on a number that matters):

- Screenshot specifications: https://developer.apple.com/help/app-store-connect/reference/screenshot-specifications
- Creative assets specifications (header, search, universal, In-App Events): https://developer.apple.com/help/app-store-connect/reference/app-information/creative-assets-specifications
- App preview (video) specifications: https://developer.apple.com/help/app-store-connect/reference/app-information/app-preview-specifications
- HIG, App icons: https://developer.apple.com/design/human-interface-guidelines/app-icons
- App Review Guidelines 2.3 (accurate metadata): https://developer.apple.com/app-store/review/guidelines/#accurate-metadata

## Rules for every image

- `.png`, `.jpg` or `.jpeg`. **No alpha channel, no transparency.**
- 1 to 10 screenshots per device size and per localization.
- If the UI is the same across device sizes, upload only the highest required resolution; App Store Connect scales it down for the smaller ones.
- Screenshots must show the app in use (guideline 2.3.3), not only title art, a login page or a splash screen. Added captions and backdrops are fine. Do not show Apple hardware renders, Apple logos, other platforms' names, prices, or content that is not in the app.
- Landscape sets use the same numbers swapped.

## Screenshots — what to produce

Default output of this skill (native resolution of the simulator `ios_sim.py boot` picks):

| Device set | Output size (portrait) | Simulator | Required when |
|---|---|---|---|
| iPhone 6.9" | **1320 × 2868** (also accepted: 1290 × 2796, 1260 × 2736) | iPhone 16 / 17 Pro Max | always for an iPhone app (one large iPhone set covers the smaller ones) |
| iPad 13" | **2064 × 2752** (also 2048 × 2732) | iPad Pro 13-inch (M4 / M5) | the app runs on iPad (`TARGETED_DEVICE_FAMILY` contains 2, `UIDeviceFamily` contains 2, Expo `ios.supportsTablet: true`) |
| Mac | **2880 × 1800** (also 2560 × 1600, 1440 × 900, 1280 × 800 — all 16:10) | the Mac itself | Mac app (native, Catalyst, or "Designed for iPad" opted in to Mac listing) |
| Apple Watch | **422 × 514** (Ultra 3) · 410 × 502 (Ultra / Ultra 2) · 416 × 496 (Series 10–12) · 396 × 484 (Series 7–9) · 368 × 448 (Series 4–6, SE) · 312 × 390 (Series 3) | Apple Watch Ultra / Series | watchOS app. Use one size consistently across all localizations |
| Apple TV | **3840 × 2160** or 1920 × 1080 | Apple TV 4K | tvOS app |
| Apple Vision Pro | **3840 × 2160** | Apple Vision Pro | visionOS app |

Other accepted iPhone sizes, if the user wants a dedicated set for a smaller display:

| Display | Portrait sizes |
|---|---|
| 6.5" (Face ID, large) | 1284 × 2778, 1242 × 2688 |
| 6.3" / 6.1" (Dynamic Island, medium) | 1206 × 2622, 1179 × 2556 |
| 6.1" / 5.8" (Face ID, medium) | 1170 × 2532, 1125 × 2436, 1080 × 2340 |
| 5.5" (Home button) | 1242 × 2208 |
| 4.7" (Home button) | 750 × 1334 |

Other accepted iPad sizes: 11" — 1668 × 2420, 1668 × 2388, 1640 × 2360, 1488 × 2266; 10.5" — 1668 × 2224; 9.7" — 1536 × 2048.

Apple's page lists which sets are mandatory and which fall back to another; that part changes with new hardware (for example, sets for folding iPhones were added in late 2026 as optional). When the user is about to submit, open the screenshot specifications page and confirm the required sets.

Apple Watch, Apple TV and Vision Pro screenshots are the plain capture — do not add captions or backdrops unless the user asks.

## Icon

- App Store icon: **1024 × 1024 PNG**, square, **no rounded corners** (the system applies the mask), no alpha, sRGB or Display P3.
- Other platforms: visionOS 1024 × 1024 (shown circular, layered), watchOS 1088 × 1088 (shown circular), tvOS a layered landscape image stack. The HIG page could not be machine-read when this file was last checked, so open it and confirm the sizes before producing a watchOS / tvOS / visionOS icon.
- Design (HIG): one simple, centered concept made of a few bold shapes on a solid or gradient background. No text other than an essential brand letter, no photos, no UI screenshots, no Apple hardware. Do not bake in shadows, gloss or bevels — the system adds its own material effects.
- Dark / tinted / clear variants are produced by the system, or authored by the user as layers in Icon Composer. That is a manual Xcode step: mention it, do not simulate it.
- The icon in the binary (`AppIcon.appiconset` / `.icon` file) is what ships. The 1024 file this skill makes is the marketing icon; if the user also wants it in the app, replace the asset in the asset catalog only when they ask.

## Product page header, search image, universal asset

| Asset | Size | Ratio | Format | Safe area (keep logo, subject, any text inside) |
|---|---|---|---|---|
| Product page header | **3840 × 1646** | 21:9 | PNG | 1646 × 661, top-left at (1097, 493) |
| Search results image | 1920 × 1280 to **3840 × 2560** | 3:2 | PNG or JPEG | at 3840 × 2560: 2168 × 1030, top-left at (836, 765) |
| Universal asset (one file used for both) | **5244 × 2950** | 16:9 | **PNG only** | 1402 × 962, top-left at (1921, 660) |

- No alpha. The area outside the safe area is cropped or covered by UI depending on the device, so it holds only extendable background.
- Header and search safe areas are centered. The universal safe area is horizontally centered but sits **above** the vertical center (its middle is at 39 % of the height): with `templates/banner.html` pass `SAFE_W=26 SAFE_H=32 SHIFT_Y=-11.3`.
- The search image is shown small: one large, high-contrast subject.
- `validate.py safe-area <file>` writes a preview with the safe area drawn on top.
- Header and search also accept video (`.mov`, `.m4v`, `.mp4`, 30 or 60 fps, 5–30 s). This skill does not produce video.

## In-App Events (only if asked)

Event card: 16:9, 1920 × 1080 to 3840 × 2160. Event details: 9:16, 1080 × 1920 to 2160 × 3840. PNG or JPEG.

## fastlane deliver layout (optional)

`fastlane/screenshots/<locale>/` (for example `es-MX`, `en-US`), any file names; deliver sorts them alphabetically and assigns the device set from the pixel size. Name files `01_iphone69_home.png`, `02_…` to keep the order.
