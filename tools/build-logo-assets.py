#!/usr/bin/env python3
"""Build the Fox & Fable web logo assets from the original artwork.

Source: docs/brand-reference/fox-and-fable-logo-original.png (copper fine-line fox,
charcoal serif wordmark, on off-white #FCFAF6).

Method: the off-white background is keyed out with a local "un-multiply": each pixel's
alpha is its darkness relative to the darkest stroke core nearby, and its colour is
solved from  pixel = alpha * ink + (1 - alpha) * background.  This keeps the hair-thin
anti-aliased lines (and the fox's brown-to-copper gradient) intact on any background.
Downscaling is done in premultiplied space; small sizes get a slight optical stroke
boost so the lines don't break up.

Needs: pip install pillow numpy scipy      Run from the site root:  python3 tools/build-logo-assets.py
"""
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "docs/brand-reference/fox-and-fable-logo-original.png"
OUT = ROOT / "assets/logo"
BG = np.array([252, 250, 246], float)          # sampled from the artwork's background
CREAM = (252, 250, 246)                          # og/icon background = artwork background
PARCHMENT = np.array([243, 238, 228], float)     # site --c-parchment (footer light lines)
LIGHT_COPPER = np.array([222, 166, 124], float)  # copper lifted for the charcoal footer
NOISE = 11.0
BURN = np.array([77, 52, 32], float)             # "burned into oak" brown used on wood panels

# Crop boxes in source pixels (x0, y0, x1, y1), measured from the artwork.
BOX = {
    "lockup":  (130, 296, 1130, 1032),   # fox + wordmark + descriptor + rule + tagline
    "primary": (130, 296, 1130, 848),    # fox + wordmark
    "fox":     (476, 296, 768, 704),     # fox only
}


def key(rgb):
    d = (BG - rgb).sum(2)
    core = ndimage.maximum_filter(d, size=11)
    core = np.maximum(core, 140.0)
    a = np.clip((d - NOISE) / (core - NOISE), 0, 1)   # background grain is <= ~9 darkness units
    with np.errstate(divide="ignore", invalid="ignore"):
        ink = BG - (BG - rgb) / np.maximum(a, 1e-3)[..., None]
    ink = np.clip(np.nan_to_num(ink), 0, 255)
    # Smooth colour field so later dilation/resizing never pulls in undefined colour.
    w = ndimage.gaussian_filter(a, 3) + 1e-6
    fill = np.stack([ndimage.gaussian_filter(a * ink[..., c], 3) / w for c in range(3)], -1)
    ink = np.where(a[..., None] > 0.05, ink, fill)
    return a, ink


def is_copper(ink, a):
    warm = (ink[..., 0] - ink[..., 2]) / np.maximum(BG.sum() - ink.sum(2), 1)
    return warm > 0.14


def resize(a, ink, box, width, boost=0.0):
    x0, y0, x1, y1 = box
    a = a[y0:y1, x0:x1].copy(); ink = ink[y0:y1, x0:x1]
    scale = width / (x1 - x0)
    if boost > 0:   # optical stroke boost in source px, for small renders
        a = np.maximum(a, ndimage.grey_dilation(a, size=(3, 3)) * boost)
    h = round((y1 - y0) * scale)
    def r(ch):
        return np.asarray(Image.fromarray(ch.astype(np.float32), "F").resize((width, h), Image.LANCZOS))
    A = np.clip(r(a), 0, 1)
    P = [r(a * ink[..., c]) for c in range(3)]
    C = np.stack([p / np.maximum(A, 1e-4) for p in P], -1)
    return A, np.clip(C, 0, 255)


def rgba(A, C, gamma=1.0):
    A = np.clip(A, 0, 1) ** gamma
    return Image.fromarray(np.dstack([C, A * 255]).round().astype(np.uint8), "RGBA")


def save(img, name, webp=True):
    img.save(OUT / f"{name}.png", optimize=True)
    if webp:
        img.save(OUT / f"{name}.webp", lossless=True, quality=100, method=6)
    print(name, img.size)


def flat(a, ink, colour_for):
    """Replace colours: copper strokes -> one colour, charcoal strokes -> another."""
    cop = ndimage.binary_dilation(is_copper(ink, a) & (a > 0.25), iterations=2)
    return np.where(cop[..., None], colour_for[0], colour_for[1])


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rgb = np.asarray(Image.open(SRC).convert("RGB")).astype(float)
    a, ink = key(rgb)

    # (a) full lockup, full colour, transparent: hero + anywhere large
    for w in (480, 960):
        A, C = resize(a, ink, BOX["lockup"], w, boost=0.35 if w < 600 else 0)
        save(rgba(A, C, 0.9 if w < 600 else 1.0), f"lockup-{w}")

    # footer: fox + wordmark in light lines for the charcoal footer
    light = flat(a, ink, (LIGHT_COPPER, PARCHMENT))
    for w in (300, 600):
        A, C = resize(a, light, BOX["primary"], w, boost=0.6 if w < 400 else 0.3)
        save(rgba(A, C, 0.8), f"primary-light-{w}")

    # (b) header fox mark (beside the live-text wordmark), 1x/2x by height
    fw, fh = BOX["fox"][2] - BOX["fox"][0], BOX["fox"][3] - BOX["fox"][1]
    for hpx, boost, g in ((52, 0.8, 0.7), (104, 0.5, 0.8), (156, 0.3, 0.9)):
        A, C = resize(a, ink, BOX["fox"], round(fw * hpx / fh), boost=boost)
        save(rgba(A, C, g), f"fox-{hpx}")

    # brand stamp on the oak board: fox "burned" in dark brown
    burn = np.broadcast_to(BURN, ink.shape)
    for w in (110, 220):
        A, C = resize(a, burn, BOX["fox"], w, boost=0.6)
        save(rgba(A, C, 0.8), f"fox-burn-{w}")

    # (c) favicons: copper fox on a cream rounded tile, bolder strokes for tiny sizes
    def tile(size, radius_frac, pad_frac, boost, gamma):
        inner = round(size * (1 - 2 * pad_frac))
        A, C = resize(a, ink, BOX["fox"], round(fw * inner / fh), boost=boost)
        fox = rgba(A, C, gamma)
        t = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        mask = Image.new("L", (size, size), 0)
        from PIL import ImageDraw
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1], radius=round(size * radius_frac), fill=255)
        t.paste(Image.new("RGBA", (size, size), CREAM + (255,)), (0, 0), mask)
        t.alpha_composite(fox, ((size - fox.width) // 2, (size - fox.height) // 2))
        return t
    ico = []
    for s in (16, 32, 48):
        im = tile(s, 0.2, 0.06, 1.0, 0.55); ico.append(im)
    ico[1].save(ROOT / "assets/favicon-32.png", optimize=True)
    ico[2].save(ROOT / "assets/favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)], append_images=ico[:2])
    # apple-touch must be opaque (iOS adds its own corner mask)
    at = Image.new("RGB", (180, 180), CREAM)
    A, C = resize(a, ink, BOX["fox"], round(fw * 140 / fh), boost=0.5)
    f = rgba(A, C, 0.8); at.paste(f, ((180 - f.width) // 2, 20), f)
    at.save(ROOT / "assets/apple-touch-icon.png", optimize=True)
    for s in (192, 512):
        im = Image.new("RGB", (s, s), CREAM)
        A, C = resize(a, ink, BOX["fox"], round(fw * s * 0.74 / fh), boost=0.4 if s < 300 else 0)
        f = rgba(A, C, 0.85 if s < 300 else 1.0); im.paste(f, ((s - f.width) // 2, (s - f.height) // 2), f)
        im.save(ROOT / f"assets/icon-{s}.png", optimize=True)

    # (d) Open Graph 1200x630 on the artwork's cream
    og = Image.new("RGB", (1200, 630), CREAM)
    A, C = resize(a, ink, BOX["lockup"], 760)
    f = rgba(A, C); og.paste(f, ((1200 - f.width) // 2, (630 - f.height) // 2), f)
    og.save(ROOT / "assets/og-image.png", optimize=True)
    print("og", og.size, "lockup on og", f.size)


if __name__ == "__main__":
    main()
