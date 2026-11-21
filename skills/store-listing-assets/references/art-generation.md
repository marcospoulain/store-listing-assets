# Brand art: engines and prompts

Art is needed for the icon (when the repo has no usable logo), the Play feature graphic, the TV banner, the App Store header / search / universal images, and optional screenshot backdrops. Screenshots themselves are never generated.

## Choosing an engine

Use the first that applies:

1. **Existing brand assets.** A vector logo, an adaptive icon foreground + background, or illustrations in the repo. Compose directly with the templates; this matches the shipped app best and costs nothing.
2. **The agent's own image generation tool**, if this session has one. Pass the logo or current icon as a reference image when the tool accepts one.
3. **An image API whose key is already in the environment.** Check that the variable exists without printing it (`[ -n "$OPENAI_API_KEY" ]`):
   - `OPENAI_API_KEY` → OpenAI Images API.
   - `GEMINI_API_KEY` / `GOOGLE_API_KEY` → Gemini image generation.
   - `REPLICATE_API_TOKEN`, `FAL_KEY` → hosted image models.
   Model names change often: look up the provider's current image model in its documentation instead of assuming one. Never write a key to a file, a command line that gets logged, or the chat.
4. **Art built in code.** SVG or HTML/CSS made from the brand's colors, gradients, shapes and logo, rendered by `compose.mjs`. Always available, and for icons and feature graphics it is often the most on-brand result.

Paid generation: for one image, go ahead. Before a batch, tell the user how many images and which engine, and wait for a yes.

Generators do not return exact sizes. Ask for the nearest aspect ratio, save to `store-assets/raw/`, and let the template crop to the exact canvas (`background-size: cover`). If the art is much smaller than the canvas (the App Store universal image is 5244 px wide), upscale it first or prefer code-built art, which is resolution-independent.

Save each prompt you use in `store-assets/prompts/<asset>.md`.

## Rules for every prompt

- Opaque: `solid opaque background, no transparency`.
- **No text in the generated image.** Titles and captions are added in composition with the brand's real font, so they are sharp, correctly spelled and localizable.
- No UI, no device mockups, no third-party logos, no copyrighted characters, no real people.
- Subject centered with generous margins; edges hold only background that can be cropped.
- One shared style block across the whole kit so the assets look like a family.

**Style block** (fill from `brand.json`):

```
[visualStyle], color palette [primary] [secondary] [accent] on [background], [lighting that fits the tone], [tone] mood, clean composition, high detail, professional app store marketing art, solid opaque background, no transparency
```

## Prompts

**Icon** (both stores; 1:1)

```
App icon artwork for "[appName]", [oneLiner]. Single central symbol: [heroElement], built from a few bold simple filled shapes, centered with generous padding. Background: smooth gradient [primary] to [secondary], full-bleed square, edge to edge. [STYLE BLOCK]. Flat square, no rounded corners, no mask, no border, no drop shadow outside the artwork, no text, no letters, no badges, no photo, no UI, no device.
```

If a current icon exists, ask whether to redesign it or only re-export it at store size. For Play, a logo with its own shape sits inside the centered 75 % keyline area (`SYMBOL_SIZE=75`); illustrated art goes full bleed (`SYMBOL_SIZE=100`).

**Google Play feature graphic** (ask for about 2:1)

```
Wide promotional banner for "[appName]", [oneLiner]. Shows the experience: [scene that expresses the core value or context of use]. Focal point centered in the middle 60 %; only soft background near the edges. Bright vivid [primary] / [accent] palette, no pure white, black or dark gray background. Extends the brand of the app icon without copying the icon. [STYLE BLOCK]. No text, no device mockups, no phones, no third-party logos, no store badges.
```

**Android TV banner** (16:9)

```
Android TV app banner artwork for "[appName]": [heroElement], strong contrast, readable from across a room, centered composition, no small details. [STYLE BLOCK]. No text, no device, no badges.
```

Add the app name in composition, large.

**App Store product page header** (21:9)

```
Ultra-wide cinematic key art for "[appName]", [oneLiner]. [heroElement] centered; everything important inside the central 40 % of the width and height; the rest is calm, extendable background. [STYLE BLOCK]. No text, no logos, no watermark, no devices.
```

**App Store search image** (3:2)

```
App Store search result artwork for "[appName]". One bold, instantly readable subject: [heroElement], large and centered, strong contrast against [background], legible at thumbnail size. [STYLE BLOCK]. Minimal background, no small details, no text, no third-party logos.
```

**App Store universal asset** (16:9, cropped to both of the above)

```
Key art for "[appName]" that will be cropped to 21:9 and to 3:2. [heroElement] and every key element tightly grouped horizontally centered and slightly above the vertical center, within the middle 25 % of the width; wide margins of soft extendable background on all sides. [STYLE BLOCK]. No text, no logos, no devices.
```

Check all three with `validate.py safe-area`.

**Screenshot backdrop** (optional; portrait for phones, 3:4 for iPad, 16:10 for Mac)

```
Abstract brand backdrop for an app screenshot of "[appName]", part of a consistent set. Subtle [decorative element tied to this screen's benefit] near the edges, calm empty center where a real app screenshot will be placed, calm top band for a caption. [STYLE BLOCK], background tone [color for this screen]. No text, no fake UI, no phone, no logos.
```

A plain two-color gradient from the brand (the template's default when `BG` is not set) is often cleaner than a generated backdrop. Do not use backdrops for Play tablet, Chromebook, Wear OS, TV, Automotive or XR screenshots.
