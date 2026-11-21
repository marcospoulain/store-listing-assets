#!/usr/bin/env python3
"""Validador de recursos gráficos de Google Play.

Uso:
  python3 validate.py <carpeta_final>               # valida todo lo que haya dentro
  python3 validate.py --fit <tipo> <entrada> <salida>  # ajusta una imagen a la medida del tipo

El tipo de cada archivo se deduce de su carpeta o de su nombre:
  icon, feature-graphic, tv-banner, phone, tablet-7, tablet-10, chromebook,
  wear, tv, automotive, xr

Tipos admitidos por --fit:
  icon, feature-graphic, tv-banner, wear, tv, automotive-portrait,
  automotive-landscape, xr, phone, tablet

Especificaciones: Google Play Console Help, art. 9866151, y Android Developers
(icon design specifications), revisadas en noviembre de 2026.
Requiere Pillow: pip install pillow
"""
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    sys.exit("Falta Pillow: pip install pillow  (o pip install --user pillow)")

EXTS = {".png", ".jpg", ".jpeg"}
SCREEN_TYPES = ["phone", "tablet-7", "tablet-10", "chromebook", "wear", "tv", "automotive", "xr"]

errors, warnings = [], []


def err(f, msg):
    errors.append(f"ERROR  {f}: {msg}")


def warn(f, msg):
    warnings.append(f"AVISO  {f}: {msg}")


def classify(path: Path, root: Path):
    rel = path.relative_to(root).as_posix().lower()
    name = path.stem.lower()
    if "feature" in rel or "featuregraphic" in rel:
        return "feature-graphic"
    if "tv-banner" in rel or "tvbanner" in rel:
        return "tv-banner"
    if name.startswith("icon") or rel.startswith("icon"):
        return "icon"
    parts = rel.split("/")
    for t in ["tablet-7", "tablet-10", "chromebook", "wear", "automotive", "xr", "phone", "tv"]:
        if any(p == t or p.startswith(t) for p in parts[:-1]):
            return t
    aliases = {
        "phonescreenshots": "phone", "seveninchscreenshots": "tablet-7",
        "teninchscreenshots": "tablet-10", "tvscreenshots": "tv", "wearscreenshots": "wear",
    }
    for p in parts[:-1]:
        if p in aliases:
            return aliases[p]
    return None


def ratio_is(w, h, a, b, tol=0.01):
    return abs((w / h) - (a / b)) <= (a / b) * tol


def has_alpha(img):
    return img.mode in ("RGBA", "LA", "PA") or (img.mode == "P" and "transparency" in img.info)


def fully_opaque(img):
    if not has_alpha(img):
        return True
    a = img.convert("RGBA").getchannel("A")
    return a.getextrema()[0] == 255


def check_no_alpha(f, img):
    if has_alpha(img):
        err(f, f"tiene canal alfa (modo {img.mode}); debe ser JPEG o PNG de 24 bits sin alfa")


def check_screenshot_general(f, w, h, lo=320, hi=3840):
    if min(w, h) < lo or max(w, h) > hi:
        err(f, f"{w}x{h}: cada lado debe medir entre {lo} y {hi} px")
    if max(w, h) > 2 * min(w, h):
        err(f, f"{w}x{h}: el lado largo supera el doble del lado corto (máx. 2:1)")


def check_file(f: Path, kind: str, root: Path):
    rel = f.relative_to(root)
    size_kb = f.stat().st_size / 1024
    try:
        img = Image.open(f)
        img.load()
    except Exception as e:  # noqa: BLE001
        err(rel, f"no se puede abrir ({e})")
        return
    w, h = img.size
    fmt = img.format

    if fmt not in ("PNG", "JPEG"):
        err(rel, f"formato {fmt}; se acepta PNG o JPEG")

    if kind == "icon":
        if (w, h) != (512, 512):
            err(rel, f"{w}x{h}; el ícono debe ser 512x512")
        if fmt != "PNG":
            err(rel, "el ícono debe ser PNG de 32 bits")
        elif img.mode != "RGBA":
            err(rel, f"modo {img.mode}; el ícono debe ser PNG de 32 bits (RGBA). Usa --fit icon")
        if size_kb > 1024:
            err(rel, f"pesa {size_kb:.0f} KB; máximo 1024 KB")
        if not fully_opaque(img):
            warn(rel, "tiene píxeles transparentes; Play mostrará su fondo detrás. Usa un fondo opaco a sangre")
        rgb = img.convert("RGB")
        corners = [rgb.getpixel(p) for p in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]]
        center = rgb.getpixel((w // 2, 2))
        if all(c == corners[0] for c in corners) and corners[0] != center and corners[0] in [(255, 255, 255), (0, 0, 0)]:
            warn(rel, "las esquinas parecen redondeadas o enmascaradas; entrega un cuadrado completo a sangre")
        return

    if kind == "feature-graphic":
        if (w, h) != (1024, 500):
            err(rel, f"{w}x{h}; el gráfico de funciones debe ser 1024x500")
        check_no_alpha(rel, img)
        gray = img.convert("L")
        lo, hi = gray.getextrema()
        mean = sum(i * c for i, c in enumerate(gray.histogram())) / (w * h)
        if mean > 240 or mean < 25:
            warn(rel, "el fondo predominante es casi blanco o casi negro; Play recomienda colores vivos")
        return

    if kind == "tv-banner":
        if (w, h) != (1280, 720):
            err(rel, f"{w}x{h}; el banner de TV debe ser 1280x720")
        check_no_alpha(rel, img)
        return

    # Screenshots
    check_no_alpha(rel, img)
    if kind == "phone":
        check_screenshot_general(rel, w, h)
        if min(w, h) < 1080:
            warn(rel, f"{w}x{h}: menos de 1080 px; no califica para formatos de promoción")
        if not (ratio_is(w, h, 9, 16) or ratio_is(w, h, 16, 9)):
            warn(rel, f"{w}x{h}: para promoción se requiere 9:16 vertical o 16:9 horizontal")
    elif kind in ("tablet-7", "tablet-10", "chromebook"):
        if min(w, h) < 1080 or max(w, h) > 7680:
            err(rel, f"{w}x{h}: en pantallas grandes cada lado debe medir entre 1080 y 7680 px")
        if not (ratio_is(w, h, 16, 9) or ratio_is(w, h, 9, 16)):
            err(rel, f"{w}x{h}: las pantallas grandes requieren 16:9 o 9:16")
    elif kind == "wear":
        if w != h:
            err(rel, f"{w}x{h}: Wear OS requiere 1:1")
        if min(w, h) < 384:
            err(rel, f"{w}x{h}: Wear OS requiere al menos 384x384")
    elif kind == "tv":
        check_screenshot_general(rel, w, h)
        if not ratio_is(w, h, 16, 9):
            warn(rel, f"{w}x{h}: para TV se recomienda 16:9 (1920x1080)")
    elif kind == "automotive":
        if (w, h) not in ((800, 1280), (1024, 768)):
            err(rel, f"{w}x{h}: Automotive usa 800x1280 (vertical) o 1024x768 (horizontal)")
    elif kind == "xr":
        if not ratio_is(w, h, 8, 5):
            err(rel, f"{w}x{h}: Android XR requiere 8:5")
        if w < 1920 or h < 1200:
            err(rel, f"{w}x{h}: Android XR requiere al menos 1920x1200 (recomendado 3840x2400)")
        if size_kb > 8 * 1024:
            err(rel, f"pesa {size_kb / 1024:.1f} MB; máximo 8 MB")


def validate(root: Path):
    files = [p for p in sorted(root.rglob("*")) if p.suffix.lower() in EXTS and p.is_file()]
    if not files:
        sys.exit(f"No hay imágenes en {root}")
    counts = {t: 0 for t in SCREEN_TYPES}
    auto = {"portrait": 0, "landscape": 0}
    for f in files:
        kind = classify(f, root)
        if kind is None:
            warn(f.relative_to(root), "no se pudo deducir el tipo (usa carpetas phone/, tablet-10/, wear/…); se omite")
            continue
        check_file(f, kind, root)
        if kind in counts:
            counts[kind] += 1
            if kind == "automotive":
                with Image.open(f) as im:
                    auto["portrait" if im.size[1] > im.size[0] else "landscape"] += 1

    total = sum(counts.values())
    for t, n in counts.items():
        if n > 8:
            err(t + "/", f"{n} screenshots; máximo 8 por tipo de dispositivo")
    if total < 2:
        err("screenshots", f"hay {total}; se necesitan al menos 2 para publicar")
    if 0 < counts["phone"] < 4:
        warn("phone/", f"{counts['phone']} screenshots; se necesitan al menos 4 (≥1080 px) para formatos de promoción")
    for t in ("tablet-7", "tablet-10", "chromebook"):
        if 0 < counts[t] < 4:
            warn(t + "/", f"{counts[t]} screenshots; en pantallas grandes se indican al menos 4")
    if 0 < counts["xr"] < 4:
        err("xr/", f"{counts['xr']} screenshots; Android XR requiere de 4 a 8")
    if counts["automotive"] and (auto["portrait"] < 2 or auto["landscape"] < 2):
        err("automotive/", f"{auto['portrait']} verticales y {auto['landscape']} horizontales; se requieren al menos 2 de cada uno")
    if not any(classify(f, root) == "icon" for f in files):
        warn("icon", "no se encontró el ícono 512x512 (obligatorio para publicar)")
    if not any(classify(f, root) == "feature-graphic" for f in files):
        warn("feature-graphic", "no se encontró el gráfico de funciones 1024x500")
    if counts["tv"] and not any(classify(f, root) == "tv-banner" for f in files):
        err("tv-banner", "hay screenshots de TV pero falta el banner 1280x720 (obligatorio en TV)")

    print(f"Revisados {len(files)} archivos. Screenshots por tipo: " +
          ", ".join(f"{k}={v}" for k, v in counts.items() if v))
    for line in errors + warnings:
        print(line)
    print(f"\nResultado: {len(errors)} errores, {len(warnings)} avisos")
    sys.exit(1 if errors else 0)


FIT = {
    "icon": (512, 512),
    "feature-graphic": (1024, 500),
    "tv-banner": (1280, 720),
    "tv": (1920, 1080),
    "automotive-portrait": (800, 1280),
    "automotive-landscape": (1024, 768),
    "xr": (3840, 2400),
    "phone": (1440, 2560),
    "tablet": (2560, 1440),
}


def fit(kind, src, dst):
    img = Image.open(src)
    img.load()
    if has_alpha(img):
        bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
        bg.alpha_composite(img.convert("RGBA"))
        img = bg
    img = img.convert("RGB")
    if kind == "wear":
        s = min(img.size)
        left, top = (img.width - s) // 2, (img.height - s) // 2
        img = img.crop((left, top, left + s, top + s))
        if s < 384:
            img = img.resize((384, 384), Image.LANCZOS)
    else:
        if kind not in FIT:
            sys.exit(f"Tipo desconocido para --fit: {kind}. Opciones: wear, {', '.join(FIT)}")
        tw, th = FIT[kind]
        scale = max(tw / img.width, th / img.height)
        img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
        left, top = (img.width - tw) // 2, (img.height - th) // 2
        img = img.crop((left, top, left + tw, top + th))
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    if kind == "icon":
        img = img.convert("RGBA")  # PNG de 32 bits, 100 % opaco
        img.save(dst, "PNG", optimize=True)
    elif str(dst).lower().endswith((".jpg", ".jpeg")):
        img.save(dst, "JPEG", quality=95)
    else:
        img.save(dst, "PNG", optimize=True)
    print(f"OK {dst} {img.size[0]}x{img.size[1]} {img.mode}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) == 4 and a[0] == "--fit":
        fit(a[1], a[2], a[3])
    elif len(a) == 1:
        validate(Path(a[0]))
    else:
        print(__doc__)
        sys.exit(2)
