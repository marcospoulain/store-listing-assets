#!/usr/bin/env python3
"""Validate and fit store listing images for the App Store and Google Play.

Usage:
  validate.py check <dir> [--store apple|google-play]
  validate.py fit <kind> <input> <output>      flatten alpha, center-crop and resize to the kind's size
  validate.py kinds                            list the kinds `fit` accepts
  validate.py safe-area <image> [output]       preview with the App Store safe area drawn on top

`check` infers the store from the path (.../apple/... or .../google-play/...) and
the asset type from the folder or file name:
  apple:        icon*, header*, search*, universal*, iphone*/, ipad*/, mac/, watch/, tv/, vision/
  google-play:  icon*, feature-graphic*, tv-banner*, phone/, tablet-7/, tablet-10/, chromebook/,
                foldable/, wear/, tv/, automotive/, xr/   (fastlane supply folder names also work)

Specs: see references/apple-specs.md and references/google-play-specs.md.
Requires Pillow: pip install pillow
"""
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:
    sys.exit("Pillow is missing: pip install pillow   (or: python3 -m pip install --user pillow)")

Image.MAX_IMAGE_PIXELS = None
EXTS = {".png", ".jpg", ".jpeg"}
errors, warnings = [], []


def err(f, msg):
    errors.append(f"ERROR  {f}: {msg}")


def warn(f, msg):
    warnings.append(f"WARN   {f}: {msg}")


def both(sizes):
    return set(sizes) | {(h, w) for w, h in sizes}


# ---------- Apple ----------
A_IPHONE = both([(1320, 2868), (1290, 2796), (1260, 2736), (1284, 2778), (1242, 2688), (1206, 2622), (1179, 2556),
                 (1170, 2532), (1125, 2436), (1080, 2340), (1242, 2208), (750, 1334), (640, 1136), (640, 1096),
                 (640, 960), (640, 920), (1398, 2034), (2007, 2853)])
A_IPAD = both([(2064, 2752), (2048, 2732), (1668, 2420), (1668, 2388), (1640, 2360), (1488, 2266), (1512, 2316),
               (1668, 2224), (1536, 2048), (1536, 2008), (768, 1024), (768, 1004)])
A_MAC = {(2880, 1800), (2560, 1600), (1440, 900), (1280, 800)}
A_WATCH = {(422, 514), (410, 502), (416, 496), (396, 484), (368, 448), (312, 390)}
A_TV = {(3840, 2160), (1920, 1080)}
A_VISION = {(3840, 2160)}
A_SCREEN_SETS = {"iphone": A_IPHONE, "ipad": A_IPAD, "mac": A_MAC, "watch": A_WATCH, "tv": A_TV, "vision": A_VISION}
A_PREFERRED = {"iphone": "1320x2868", "ipad": "2064x2752", "mac": "2880x1800", "watch": "422x514", "tv": "3840x2160", "vision": "3840x2160"}
# asset -> (canvas, safe area (x, y, w, h))
A_SAFE = {
    "header": ((3840, 1646), (1097, 493, 1646, 661)),
    "search": ((3840, 2560), (836, 765, 2168, 1030)),
    "universal": ((5244, 2950), (1921, 660, 1402, 962)),
}

# ---------- Google Play ----------
G_SCREEN_TYPES = ["phone", "tablet-7", "tablet-10", "chromebook", "foldable", "wear", "tv", "automotive", "xr"]
G_ALIASES = {"phonescreenshots": "phone", "seveninchscreenshots": "tablet-7", "teninchscreenshots": "tablet-10",
             "tvscreenshots": "tv", "wearscreenshots": "wear"}

FIT = {
    "apple-icon": (1024, 1024), "apple-iphone": (1320, 2868), "apple-ipad": (2064, 2752), "apple-mac": (2880, 1800),
    "apple-tv": (3840, 2160), "apple-vision": (3840, 2160), "apple-header": (3840, 1646),
    "apple-search": (3840, 2560), "apple-universal": (5244, 2950),
    "gp-icon": (512, 512), "gp-feature-graphic": (1024, 500), "gp-tv-banner": (1280, 720),
    "gp-phone": (1440, 2560), "gp-phone-landscape": (2560, 1440), "gp-tablet": (2560, 1440),
    "gp-tablet-portrait": (1440, 2560), "gp-tv": (1920, 1080), "gp-automotive-portrait": (800, 1280),
    "gp-automotive-landscape": (1024, 768), "gp-xr": (3840, 2400),
    "gp-wear": "square, at least 384x384", "flatten": "keep the size, only remove alpha",
}


def has_alpha(img):
    return img.mode in ("RGBA", "LA", "PA") or (img.mode == "P" and "transparency" in img.info)


def fully_opaque(img):
    return not has_alpha(img) or img.convert("RGBA").getchannel("A").getextrema()[0] == 255


def ratio_is(w, h, a, b, tol=0.01):
    return abs((w / h) - (a / b)) <= (a / b) * tol


def no_alpha(f, img):
    if has_alpha(img):
        err(f, f"has an alpha channel (mode {img.mode}); must be JPEG or 24-bit PNG. Fix with: validate.py fit flatten")


def store_of(path: Path, forced):
    if forced:
        return forced
    parts = [p.lower() for p in path.resolve().parts]
    for p in reversed(parts):
        if p in ("apple", "app-store", "appstore", "ios", "appstore-assets"):
            return "apple"
        if p in ("google-play", "googleplay", "play", "play-store", "playstore", "android", "playstore-assets"):
            return "google-play"
    return None


def classify_apple(rel):
    name = rel.name.lower()
    dirs = [p.lower() for p in rel.parts[:-1]]
    for d in reversed(dirs):
        for key in A_SCREEN_SETS:
            if d.startswith(key) or (key == "vision" and d.startswith("visionpro")) or (key == "tv" and d in ("appletv", "apple-tv")):
                return key
        if d in ("applewatch", "apple-watch"):
            return "watch"
    for key in ("icon", "header", "search", "universal"):
        if name.startswith(key):
            return key
    return None


def classify_google(rel):
    s = rel.as_posix().lower()
    name = rel.stem.lower()
    dirs = [p.lower() for p in rel.parts[:-1]]
    if "feature" in name or "featuregraphic" in s:
        return "feature-graphic"
    if "tv-banner" in name or "tvbanner" in name:
        return "tv-banner"
    if name.startswith("icon"):
        return "icon"
    for d in reversed(dirs):
        for t in ["tablet-7", "tablet-10", "chromebook", "foldable", "wear", "automotive", "xr", "phone", "tv"]:
            if d == t or d.startswith(t):
                return t
        if d in G_ALIASES:
            return G_ALIASES[d]
        if d.startswith("tablet"):
            return "tablet-10"
    return None


def open_image(f, rel):
    try:
        img = Image.open(f)
        img.load()
    except Exception as e:  # noqa: BLE001
        err(rel, f"cannot be opened ({e})")
        return None
    if img.format not in ("PNG", "JPEG"):
        err(rel, f"format {img.format}; only PNG or JPEG are accepted")
    return img


def check_apple(f, kind, rel):
    img = open_image(f, rel)
    if img is None:
        return
    w, h = img.size
    no_alpha(rel, img)
    if kind == "icon":
        if (w, h) != (1024, 1024):
            err(rel, f"{w}x{h}; the App Store icon must be 1024x1024")
        if img.format != "PNG":
            err(rel, "the App Store icon must be PNG")
        rgb = img.convert("RGB")
        corners = {rgb.getpixel(p) for p in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]}
        if len(corners) == 1 and corners <= {(255, 255, 255), (0, 0, 0)} and rgb.getpixel((w // 2, 2)) not in corners:
            warn(rel, "corners look rounded or masked; deliver a full square, the system applies the mask")
    elif kind in ("header", "universal"):
        canvas = A_SAFE[kind][0]
        if (w, h) != canvas:
            err(rel, f"{w}x{h}; the {kind} image must be {canvas[0]}x{canvas[1]}")
        if img.format != "PNG":
            err(rel, f"the {kind} image must be PNG")
    elif kind == "search":
        if not ratio_is(w, h, 3, 2, 0.002) or not (1920 <= w <= 3840):
            err(rel, f"{w}x{h}; the search image must be 3:2, from 1920x1280 to 3840x2560")
    else:
        if (w, h) not in A_SCREEN_SETS[kind]:
            err(rel, f"{w}x{h} is not an accepted {kind} screenshot size (use {A_PREFERRED[kind]}; see references/apple-specs.md)")


def check_google(f, kind, rel):
    img = open_image(f, rel)
    if img is None:
        return
    w, h = img.size
    size_kb = f.stat().st_size / 1024
    lo, hi = min(w, h), max(w, h)

    if kind == "icon":
        if (w, h) != (512, 512):
            err(rel, f"{w}x{h}; the Play icon must be 512x512")
        if img.format != "PNG":
            err(rel, "the Play icon must be a 32-bit PNG")
        elif img.mode != "RGBA":
            err(rel, f"mode {img.mode}; the Play icon must be a 32-bit PNG (RGBA). Fix with: validate.py fit gp-icon")
        if size_kb > 1024:
            err(rel, f"{size_kb:.0f} KB; maximum is 1024 KB")
        if not fully_opaque(img):
            warn(rel, "has transparent pixels; Play shows its own background behind them. Use an opaque full-bleed background")
        return
    no_alpha(rel, img)
    if kind == "feature-graphic":
        if (w, h) != (1024, 500):
            err(rel, f"{w}x{h}; the feature graphic must be 1024x500")
        gray = img.convert("L")
        mean = sum(i * c for i, c in enumerate(gray.histogram())) / (w * h)
        if mean > 240 or mean < 25:
            warn(rel, "mostly near-white or near-black; Play recommends vivid colors that do not blend with its background")
    elif kind == "tv-banner":
        if (w, h) != (1280, 720):
            err(rel, f"{w}x{h}; the TV banner must be 1280x720")
    elif kind in ("phone", "tv", "foldable"):
        floor = 960 if kind == "foldable" else 320
        if lo < floor or hi > 3840:
            err(rel, f"{w}x{h}: each side must be between {floor} and 3840 px")
        if kind != "foldable" and hi > 2.3 * lo:
            err(rel, f"{w}x{h}: the long side is more than 2.3x the short side")
        if size_kb > 8 * 1024:
            err(rel, f"{size_kb / 1024:.1f} MB; maximum is 8 MB")
        if kind == "phone":
            if lo < 1080:
                warn(rel, f"{w}x{h}: under 1080 px, not eligible for Play's promotion formats")
            if not (ratio_is(w, h, 9, 16) or ratio_is(w, h, 16, 9)):
                warn(rel, f"{w}x{h}: promotion formats need 9:16 portrait or 16:9 landscape")
        if kind == "tv" and not ratio_is(w, h, 16, 9):
            warn(rel, f"{w}x{h}: TV screenshots should be 16:9 (1920x1080)")
    elif kind in ("tablet-7", "tablet-10", "chromebook"):
        if lo < 1080 or hi > 7680:
            err(rel, f"{w}x{h}: large-screen screenshots need each side between 1080 and 7680 px")
        if not (ratio_is(w, h, 16, 9) or ratio_is(w, h, 9, 16)):
            err(rel, f"{w}x{h}: large-screen screenshots must be 16:9 or 9:16")
    elif kind == "wear":
        if w != h:
            err(rel, f"{w}x{h}: Wear OS screenshots must be 1:1")
        if lo < 384:
            err(rel, f"{w}x{h}: Wear OS screenshots must be at least 384x384")
    elif kind == "automotive":
        if (w, h) not in ((800, 1280), (1024, 768)):
            err(rel, f"{w}x{h}: Automotive uses 800x1280 (portrait) or 1024x768 (landscape)")
    elif kind == "xr":
        if not ratio_is(w, h, 8, 5):
            err(rel, f"{w}x{h}: Android XR screenshots must be 8:5")
        if w < 1920 or h < 1200:
            err(rel, f"{w}x{h}: Android XR needs at least 1920x1200 (3840x2400 recommended)")
        if size_kb > 8 * 1024:
            err(rel, f"{size_kb / 1024:.1f} MB; maximum is 8 MB")


def check(root: Path, forced_store):
    files = [p for p in sorted(root.rglob("*")) if p.suffix.lower() in EXTS and p.is_file()]
    if not files:
        sys.exit(f"No images in {root}")
    counts = {"apple": {}, "google-play": {}}
    kinds = {"apple": set(), "google-play": set()}
    auto = {"portrait": 0, "landscape": 0}
    for f in files:
        rel = f.relative_to(root)
        store = store_of(f, forced_store)
        if store is None:
            warn(rel, "cannot tell which store this is for (put it under apple/ or google-play/, or pass --store); skipped")
            continue
        kind = (classify_apple if store == "apple" else classify_google)(rel)
        if kind is None:
            warn(rel, "cannot tell the asset type from its folder or name; skipped")
            continue
        kinds[store].add(kind)
        if store == "apple":
            check_apple(f, kind, rel)
            if kind in A_SCREEN_SETS:
                # count per folder: each device size / locale folder is its own set
                key = rel.parent.as_posix()
                counts["apple"][key] = counts["apple"].get(key, 0) + 1
        else:
            check_google(f, kind, rel)
            if kind in G_SCREEN_TYPES:
                counts["google-play"][kind] = counts["google-play"].get(kind, 0) + 1
                if kind == "automotive":
                    with Image.open(f) as im:
                        auto["portrait" if im.size[1] > im.size[0] else "landscape"] += 1

    for folder, n in counts["apple"].items():
        if n > 10:
            err(folder + "/", f"{n} screenshots; the App Store accepts at most 10 per device size")
    if kinds["apple"]:
        if not any(k.startswith("iphone") or k in ("ipad", "mac", "tv", "vision", "watch") for k in kinds["apple"]):
            warn("apple", "no screenshots found; at least one per supported device size is required")

    g = counts["google-play"]
    if kinds["google-play"]:
        for t, n in g.items():
            if n > 8:
                err(f"google-play {t}/", f"{n} screenshots; maximum is 8 per device type")
        if sum(g.values()) < 2:
            err("google-play", f"{sum(g.values())} screenshots; at least 2 are needed to publish")
        if 0 < g.get("phone", 0) < 4:
            warn("google-play phone/", f"{g['phone']} screenshots; 4 or more (>= 1080 px) are needed for promotion formats")
        for t in ("tablet-7", "tablet-10", "chromebook"):
            if 0 < g.get(t, 0) < 4:
                warn(f"google-play {t}/", f"{g[t]} screenshots; large screens call for at least 4")
        if 0 < g.get("foldable", 0) < 3:
            err("google-play foldable/", f"{g['foldable']} screenshots; foldables need 3 to 8")
        if 0 < g.get("xr", 0) < 4:
            err("google-play xr/", f"{g['xr']} screenshots; Android XR needs 4 to 8")
        if g.get("automotive") and (auto["portrait"] < 2 or auto["landscape"] < 2):
            err("google-play automotive/", f"{auto['portrait']} portrait and {auto['landscape']} landscape; at least 2 of each are required")
        if "icon" not in kinds["google-play"]:
            warn("google-play", "no 512x512 icon found (required to publish)")
        if "feature-graphic" not in kinds["google-play"]:
            warn("google-play", "no 1024x500 feature graphic found")
        if g.get("tv") and "tv-banner" not in kinds["google-play"]:
            err("google-play", "TV screenshots present but the 1280x720 TV banner is missing (required on TV)")

    print(f"Checked {len(files)} files.")
    for store in ("apple", "google-play"):
        if kinds[store]:
            shots = ", ".join(f"{k}={v}" for k, v in counts[store].items()) or "none"
            other = ", ".join(sorted(k for k in kinds[store] if k in ("icon", "header", "search", "universal", "feature-graphic", "tv-banner"))) or "none"
            print(f"  {store}: screenshots {shots}; other assets: {other}")
    for line in errors + warnings:
        print(line)
    print(f"\nResult: {len(errors)} errors, {len(warnings)} warnings")
    sys.exit(1 if errors else 0)


def fit(kind, src, dst):
    if kind not in FIT:
        sys.exit(f"Unknown kind '{kind}'. Run: validate.py kinds")
    img = Image.open(src)
    img.load()
    if has_alpha(img):
        bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
        bg.alpha_composite(img.convert("RGBA"))
        img = bg
    img = img.convert("RGB")
    if kind == "gp-wear":
        s = min(img.size)
        left, top = (img.width - s) // 2, (img.height - s) // 2
        img = img.crop((left, top, left + s, top + s))
        if s < 384:
            img = img.resize((384, 384), Image.LANCZOS)
    elif kind != "flatten":
        tw, th = FIT[kind]
        scale = max(tw / img.width, th / img.height)
        if scale != 1:
            img = img.resize((max(tw, round(img.width * scale)), max(th, round(img.height * scale))), Image.LANCZOS)
        left, top = (img.width - tw) // 2, (img.height - th) // 2
        img = img.crop((left, top, left + tw, top + th))
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    if kind == "gp-icon":
        img = img.convert("RGBA")  # 32-bit PNG, fully opaque
        img.save(dst, "PNG", optimize=True)
    elif str(dst).lower().endswith((".jpg", ".jpeg")):
        img.save(dst, "JPEG", quality=95)
    else:
        img.save(dst, "PNG", optimize=True)
    print(f"OK {dst} {img.size[0]}x{img.size[1]} {img.mode}")


def safe_area(src, dst=None):
    src = Path(src)
    img = Image.open(src).convert("RGB")
    w, h = img.size
    kind = None
    for k, (canvas, _) in A_SAFE.items():
        if (w, h) == canvas or (k == "search" and ratio_is(w, h, 3, 2, 0.002)):
            kind = k
    if not kind:
        sys.exit(f"{w}x{h} is not a header (3840x1646), search (3:2) or universal (5244x2950) image")
    (cw, _), (x, y, sw, sh) = A_SAFE[kind]
    k = w / cw
    box = [round(x * k), round(y * k), round((x + sw) * k), round((y + sh) * k)]
    dim = Image.new("RGB", img.size, (0, 0, 0))
    out = Image.blend(img, dim, 0.55)
    out.paste(img.crop(box), box[:2])
    ImageDraw.Draw(out).rectangle(box, outline=(255, 64, 64), width=max(4, w // 500))
    if out.width > 1920:
        out = out.resize((1920, round(out.height * 1920 / out.width)), Image.LANCZOS)
    if dst is None:
        parts = list(src.parts)
        if "final" in parts:
            parts[len(parts) - 1 - parts[::-1].index("final")] = "preview"
            dst = Path(*parts).with_name(src.stem + "-safe-area.png")
        else:
            dst = src.with_name(src.stem + "-safe-area-preview.png")
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    out.save(dst, "PNG")
    print(f"OK {dst}  ({kind}: everything important must sit inside the bright rectangle)")


if __name__ == "__main__":
    a = sys.argv[1:]
    store = None
    if "--store" in a:
        i = a.index("--store")
        store = a[i + 1]
        a = a[:i] + a[i + 2:]
    if len(a) == 2 and a[0] == "check":
        check(Path(a[1]), store)
    elif len(a) == 4 and a[0] == "fit":
        fit(a[1], a[2], a[3])
    elif a == ["kinds"]:
        for k, v in FIT.items():
            print(f"  {k:26} {v if isinstance(v, str) else f'{v[0]}x{v[1]}'}")
    elif len(a) in (2, 3) and a[0] == "safe-area":
        safe_area(*a[1:])
    else:
        print(__doc__)
        sys.exit(2)
