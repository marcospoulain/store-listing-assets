# Google Play — asset specifications

Official sources (checked November 2026 — re-check before relying on a number that matters):

- Play Console Help, "Add preview assets to showcase your app": https://support.google.com/googleplay/android-developer/answer/9866151
- Google Play icon design specifications: https://developer.android.com/distribute/google-play/resources/icon-design-specifications

**Requirements** are mandatory: breaking them can get the listing rejected or removed. **Recommendations** do not block publishing, but ignoring them limits where Play promotes the app.

## What to produce

| Asset | Output of this skill | Format | Requirement |
|---|---|---|---|
| Icon | **512 × 512** | 32-bit PNG (RGBA, fully opaque), sRGB, ≤ 1024 KB | exact |
| Feature graphic | **1024 × 500** | JPEG or 24-bit PNG, no alpha | exact |
| Phone screenshots | **1440 × 2560** (9:16) or 2560 × 1440 | JPEG or 24-bit PNG, no alpha, ≤ 8 MB | 2–8; each side 320–3840 px; long side ≤ 2.3 × short side |
| Tablet 7" / 10", Chromebook | **2560 × 1440** (16:9) or 1440 × 2560 | same | at least 4 if provided; each side 1080–7680 px; 16:9 or 9:16 |
| Foldable | native capture | same, ≤ 8 MB | 3–8; each side 960–3840 px |
| Wear OS | native 1:1 capture, ≥ **384 × 384** | same | at least 1; UI only |
| Android TV screenshots | **1920 × 1080** | same | at least 1 to publish on TV |
| Android TV banner | **1280 × 720** | JPEG or 24-bit PNG, no alpha | required to publish on TV |
| Android Automotive OS | **800 × 1280** portrait and **1024 × 768** landscape | same | if provided: at least 2 of each |
| Android XR | **3840 × 2400** (8:5; min 1920 × 1200) | PNG or JPEG, ≤ 8 MB | 4–8 |

Up to 8 screenshots per device type. At least 2 screenshots in total are needed to publish.

**Promotion eligibility** (needed to appear in Play's recommendation formats):

- Apps: at least 4 screenshots, minimum 1080 px, 9:16 portrait (≥ 1080 × 1920) or 16:9 landscape (≥ 1920 × 1080).
- Games: at least 3 landscape 16:9 (≥ 1920 × 1080) or 3 portrait 9:16 (≥ 1080 × 1920), showing real gameplay.

That is why phone screenshots are composed on a 9:16 canvas: native captures of modern phones (for example 1080 × 2400, 20:9) are taller than 9:16, and iPhone captures (1320 × 2868) are taller still — never reuse them as-is.

## Icon

- Full square. **Do not round the corners or apply a mask**: Play masks dynamically with a radius of 30 % of the icon size.
- **No drop shadow** on the asset: Play adds it. Shading and lighting inside the artwork are fine.
- Full-bleed opaque background in the brand color. A transparent background shows Play's UI color through it.
- Logos with their own shape sit on the keyline grid (about 384 px centered, 75 %) rather than stretched to the edges. Illustrated artwork goes full bleed.
- No badges or text suggesting ranking, price, Play categories or programs.
- If the app has an adaptive icon (`res/mipmap-anydpi-v26/ic_launcher.xml`), compose the Play icon from its foreground over its background so both match.

## Feature graphic

- Used as the cover of the preview video, in large app collections and in ads.
- Show the experience: the core value, context or story. Extend the icon's brand instead of repeating the icon.
- Keep the focal point, logo, name and tagline **centered**; the edges get cropped. Only background near the edges.
- Vivid colors. Avoid pure white, black and dark gray, which blend with Play's background.
- No device imagery, no third-party trademarks, no Google Play or other store badges, no fine detail.
- Alt text: 140 characters or fewer, not starting with "photo of" / "image of".

## Screenshot content rules

- Show the real app or game, focused on its main features. Stylized sets that spread the UI across images are allowed; the **first three must prioritize the UI**.
- Captions only if needed, **at most 20 % of the image**, no small print, no busy backgrounds.
- **Banned in any graphic**: ranking, award, testimonial, price or promotion claims ("Best", "#1", "Top", "New", "Discount", "Sale", "Free", "Million downloads") and calls to action ("Download now", "Install now", "Play now", "Try now").
- **No device imagery** (frames go out of date) and no people touching a device unless the core use is off-device.
- **Clean status bar**: no carrier, no notifications; battery, Wi-Fi and signal full. `android_emu.py demo-on` does this.
- Sharp, correctly rotated, not stretched or pixelated.
- No third-party logos without permission; no store badges.
- Localize captions and brand text per language. A game's UI does not need localizing; added captions do.
- Alt text for each screenshot: ≤ 140 characters, no "photo of" / "image of".

Per device type:

- **Tablets and Chromebook**: exclude text that is not part of the app experience — no marketing captions. Capture on a real tablet layout, not a stretched phone.
- **Wear OS**: only the app's interface. No device frame, no added text, graphics or background, no transparency, no circular mask. At least one must reflect the current version; showing Tiles is recommended. Watch faces: show more than one option if customizable.
- **Android TV**: screenshot and banner are both required and are shown only on TV devices. The banner is the app's "icon" on TV: it normally carries the app name, readable from across a room.
- **Android Automotive OS**: required unless the app is in a parked category. Generic system UI only — capture with the generic system image and the emulator profiles *Automotive (1024p landscape)* and *Automotive Portrait*, never an OEM's UI.

## Short description and other text

- Short description: **80 characters max**. Plain language, main purpose, what makes it distinct. Do not repeat the screenshot captions.
- Period only if there are several sentences. No emojis, emoticons, special characters, repeated punctuation, line breaks, ★/☆, or all-caps for emphasis (acronyms are fine; © ® ™ allowed).
- Same banned claims and calls to action as for graphics; no keyword stuffing.
- Title (30 characters) and full description (4000) have their own limits in Play Console.
- Deliver `final/google-play/listing-text.<locale>.md` with the short description and every alt text, each with its character count.

## Preview video (not produced by this skill)

A YouTube URL of a single video (not a playlist, no timecode parameters): public or unlisted, ads off, not age-restricted, embeddable. Real use in the first 10 seconds, at least 80 % in-app footage, only the first 30 seconds autoplay (muted). Highly recommended for games. On request, write a 30-second script.

## fastlane supply layout (optional)

`fastlane/metadata/android/<locale>/images/`: `icon.png`, `featureGraphic.png`, `tvBanner.png`, `phoneScreenshots/1.png …`, `sevenInchScreenshots/`, `tenInchScreenshots/`, `tvScreenshots/`, `wearScreenshots/`. The short description goes in `fastlane/metadata/android/<locale>/short_description.txt`.

## Marketing licence

By publishing, the developer licenses Google to use listing assets for promotion. The user can untick "External marketing" in the store settings to limit promotion outside Play.
