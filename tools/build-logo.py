#!/usr/bin/env python3
"""
Builds the Fox & Fable badge logo SVGs.

The ring, fox head, rule and house are hand-drawn SVG geometry (below).
Only the lettering is generated: glyph outlines are pulled from the
self-hosted, SIL OFL-licensed fonts (Cormorant Garamond, Inter) so the
logo is a pure vector with no font dependency.

Usage:  pip install fonttools brotli && python3 tools/build-logo.py
"""
import math, pathlib
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

ROOT = pathlib.Path(__file__).resolve().parent.parent
FONTS = ROOT / "assets" / "fonts"
INK = "#2B2A28"

def load(name, wght):
    f = TTFont(FONTS / name)
    return instantiateVariableFont(f, {"wght": wght}) if "fvar" in f else f

def text_path(font, s, cap_top, baseline, x0, x1):
    """Outline `s` so its caps span cap_top..baseline and its ink spans x0..x1."""
    upm = font["head"].unitsPerEm
    cap = font["OS/2"].sCapHeight or 0.7 * upm
    scale = (baseline - cap_top) / cap
    gs, cmap, hmtx = font.getGlyphSet(), font.getBestCmap(), font["hmtx"]
    names = [cmap[ord(c)] for c in s]
    adv = [hmtx[n][0] * scale for n in names]
    lsb0 = hmtx[names[0]][1] * scale
    last = names[-1]
    from fontTools.pens.boundsPen import BoundsPen
    bp = BoundsPen(gs); gs[last].draw(bp)
    rsb_last = (hmtx[last][0] - bp.bounds[2]) * scale if bp.bounds else 0
    natural = sum(adv) - lsb0 - rsb_last
    track = ((x1 - x0) - natural) / (len(s) - 1)
    pen = SVGPathPen(gs)
    x = x0 - lsb0
    for n, a in zip(names, adv):
        gs[n].draw(TransformPen(pen, (scale, 0, 0, -scale, x, baseline)))
        x += a + track
    import re
    return re.sub(r"-?\d+\.\d+", lambda m: r2(round(float(m.group()), 1)), pen.getCommands())

def r2(v): return f"{v:.2f}".rstrip("0").rstrip(".")

def arc(cx, cy, r, a0, a1):
    """Clockwise arc from angle a0 to a1 (degrees, 0 = top)."""
    p = lambda a: (cx + r * math.sin(math.radians(a)), cy - r * math.cos(math.radians(a)))
    (xa, ya), (xb, yb) = p(a0), p(a1)
    sweep = (a1 - a0) % 360
    return f"M{r2(xa)} {r2(ya)}A{r} {r} 0 {1 if sweep > 180 else 0} 1 {r2(xb)} {r2(yb)}"

# --- Hand-drawn geometry (fox drawn on a 640-unit grid) -------------------
FOX = """
  <path d="M96 46Q68 160 128 296L70 404L128 430L88 456C136 532 230 592 296 600Q320 606 344 600C410 592 504 532 552 456L512 430L570 404L512 296Q572 160 544 46L392 182Q320 168 248 182Z"/>
  <path d="M122 105Q142 160 128 216L119 212M518 105Q498 160 512 216L521 212"/>
  <path d="M160 372Q212 354 262 390Q232 426 194 410Q178 398 186 380M480 372Q428 354 378 390Q408 426 446 410Q462 398 454 380"/>
  <path d="M238 341L251 348M402 341L389 348"/>
  <path d="M258 404C272 452 280 500 294 544M382 404C368 452 360 500 346 544"/>
  <path d="M290 552Q320 540 350 552Q348 584 320 592Q292 584 290 552Z" fill="currentColor"/>
  <circle cx="226" cy="392" r="7" fill="currentColor" stroke="none"/>
  <circle cx="414" cy="392" r="7" fill="currentColor" stroke="none"/>"""

def fox_group(stroke):
    return (f'<g fill="none" stroke="currentColor" stroke-width="{stroke}" '
            f'stroke-linejoin="round" stroke-linecap="round">{FOX}\n</g>')

# House drawn on a 560 x 488 grid (sits on and breaks the bottom of the ring)
HOUSE = """
  <path d="M58 240L285 50L514 240M92 226L285 70L480 226"/>
  <path d="M96 232V440M478 232V440"/>
  <rect x="250" y="136" width="74" height="74"/>
  <path d="M287 136V210M250 173H324"/>
  <path d="M150 270V440M420 270V440M118 402H456M156 322H414"/>
  <path d="M170 318Q172 294 205 294Q236 294 236 318M248 316Q246 300 268 302H400Q414 302 412 316"/>"""

def badge_inner(title_d, tag1_d, tag2_d):
    ring = " ".join(arc(250, 250, 216, a, b) for a, b in [(280, 80), (106, 163), (197, 254)])
    return f"""<path d="{ring}" fill="none" stroke="currentColor" stroke-width="5.5" stroke-linecap="round"/>
<g transform="translate(171 69) scale(.25)">{fox_group(13)}</g>
<path d="{title_d}"/>
<rect x="215" y="311.5" width="74" height="3" rx="1.5"/>
<path d="{tag1_d}"/>
<path d="{tag2_d}"/>
<g transform="translate(181 389) scale(.25)" fill="none" stroke="currentColor" stroke-width="17" stroke-linejoin="round" stroke-linecap="square">{HOUSE}
</g>"""

def main():
    serif = load("cormorant-garamond-latin.woff2", 600)
    sans = load("inter-latin.woff2", 500)
    title = text_path(serif, "FOX & FABLE", 241, 284, 18, 491)
    tag1 = text_path(sans, "CUSTOM SPACES", 342, 355, 140, 363)
    tag2 = text_path(sans, "BUILT TO INSPIRE", 372, 385, 131, 373)
    inner = badge_inner(title, tag1, tag2)

    (ROOT / "assets" / "logo-badge.svg").write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 18 500 490" color="{INK}" fill="currentColor" '
        f'role="img" aria-labelledby="t"><title id="t">Fox &amp; Fable: Custom Spaces Built to Inspire</title>\n{inner}\n</svg>\n')

    (ROOT / "assets" / "logo-mark.svg").write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="30 20 580 600" color="{INK}" role="img" aria-labelledby="t">'
        f'<title id="t">Fox &amp; Fable fox mark</title>\n{fox_group(22)}\n</svg>\n')

    # Favicon / touch icon: cream fox on charcoal, heavier strokes for small sizes
    icon = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
            f'<rect width="64" height="64" rx="14" fill="{INK}"/>'
            f'<g transform="translate(8.6 7.8) scale(.073)" color="#F3EEE4">{fox_group(38)}</g></svg>\n')
    (ROOT / "assets" / "favicon.svg").write_text(icon)

    # Sprite symbols for inline use in index.html (inherit CSS color)
    (ROOT / "tools" / "sprite.svg.txt").write_text(
        f'    <symbol id="logo-badge" viewBox="0 18 500 490">\n{inner}\n    </symbol>\n'
        f'    <symbol id="fox-mark" viewBox="30 20 580 600">\n{fox_group(22)}\n    </symbol>\n')

    og = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 630">'
          f'<rect width="1200" height="630" fill="#F3EEE4"/>'
          f'<rect x="24" y="24" width="1152" height="582" fill="none" stroke="#B07A45" stroke-width="2"/>'
          f'<g transform="translate(330 70) scale(1.0)" color="{INK}" fill="currentColor">{inner}</g></svg>\n')
    (ROOT / "assets" / "og-image.svg").write_text(og)
    print("logo SVGs written")

if __name__ == "__main__":
    main()
