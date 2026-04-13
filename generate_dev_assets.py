"""
generate_dev_assets.py — run once to create all dummy images for Phase 2 dev/testing.

Generates:
  static/splash/splash_1.png  …  splash_8.png   — placeholder state backgrounds
  static/dev/llama_1.png      …  llama_4.png    — dummy "captured" session photos
  static/dev/llama_dance_0.png, llama_dance_1.png — two-frame home-screen sprite

Run with:  python generate_dev_assets.py
"""

import os
import random
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
SPLASH_DIR  = os.path.join(BASE_DIR, "static", "splash")
DEV_DIR     = os.path.join(BASE_DIR, "static", "dev")
FONT_PATH   = os.path.join(BASE_DIR, "static", "fonts", "PressStart2P-Regular.ttf")

os.makedirs(SPLASH_DIR, exist_ok=True)
os.makedirs(DEV_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Splash backgrounds  (800×600, 4:3)
# ---------------------------------------------------------------------------
SPLASH_STATES = [
    (1, "HOME",        "#0a1628", "#f0e040"),  # navy   / yellow
    (2, "POSE",        "#1a0808", "#e03030"),  # crimson / red
    (3, "PHOTO 1",     "#081a08", "#40e040"),  # forest  / green
    (4, "PHOTO 2",     "#1a1808", "#e0e040"),  # olive   / yellow
    (5, "PHOTO 3",     "#08081a", "#4040e0"),  # indigo  / blue
    (6, "PHOTO 4",     "#081a1a", "#40e0e0"),  # teal    / cyan
    (7, "PROCESSING",  "#140814", "#c040e0"),  # purple  / magenta
    (8, "ALL DONE",    "#0a0f0a", "#f0e040"),  # dark    / yellow
]

W, H = 800, 600
BORDER = 16   # pixel-block border thickness


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def draw_pixel_border(draw, w, h, color, thickness):
    """Draw a blocky rectangular border made of square blocks."""
    block = thickness
    # Top and bottom rows
    for x in range(0, w, block):
        draw.rectangle([x, 0, x + block - 1, block - 1], fill=color)
        draw.rectangle([x, h - block, x + block - 1, h - 1], fill=color)
    # Left and right columns (skip corners already drawn)
    for y in range(block, h - block, block):
        draw.rectangle([0, y, block - 1, y + block - 1], fill=color)
        draw.rectangle([w - block, y, w - 1, y + block - 1], fill=color)


def make_splash(index, label, bg_hex, accent_hex):
    bg     = hex_to_rgb(bg_hex)
    accent = hex_to_rgb(accent_hex)
    dim    = tuple(max(0, c - 20) for c in bg)

    img  = Image.new("RGB", (W, H), bg)
    draw = ImageDraw.Draw(img)

    # Subtle scanline pattern — every other row slightly darker
    for y in range(0, H, 2):
        draw.line([(0, y), (W, y)], fill=dim)

    # Pixel border
    draw_pixel_border(draw, W, H, accent, BORDER)

    # State number badge — top-left
    badge_size = 48
    draw.rectangle([BORDER, BORDER, BORDER + badge_size, BORDER + badge_size],
                   fill=accent)
    try:
        num_font = ImageFont.truetype(FONT_PATH, 20)
        draw.text((BORDER + 8, BORDER + 14), str(index), font=num_font,
                  fill=bg)
    except Exception:
        pass

    # Main label — centred
    try:
        font_size = 40 if len(label) <= 8 else 28
        font = ImageFont.truetype(FONT_PATH, font_size)
        bbox = draw.textbbox((0, 0), label, font=font)
        tw   = bbox[2] - bbox[0]
        th   = bbox[3] - bbox[1]
        tx   = (W - tw) // 2
        ty   = (H - th) // 2

        # Drop shadow (2 px offset, pure black)
        draw.text((tx + 4, ty + 4), label, font=font, fill=(0, 0, 0))
        draw.text((tx, ty), label, font=font, fill=accent)
    except Exception:
        pass

    path = os.path.join(SPLASH_DIR, "splash_{}.png".format(index))
    img.save(path)
    print("  wrote", path)


print("Generating splash backgrounds…")
for args in SPLASH_STATES:
    make_splash(*args)

# ---------------------------------------------------------------------------
# Llama family photos  (400×300, 4:3)
# Each llama is pixel-art drawn with Pillow on a simple landscape background.
# ---------------------------------------------------------------------------

# Palette per llama
LLAMA_PALETTES = [
    {   # 1 — classic tan
        "sky":  "#5080c0", "ground": "#5a8030",
        "fur":  "#c8a460", "shade":  "#8c6830", "light": "#e8c880",
        "eye":  "#281808", "label": "LLAMA 1",
    },
    {   # 2 — white/cream
        "sky":  "#80a0d0", "ground": "#488028",
        "fur":  "#e8e0d0", "shade":  "#b0a890", "light": "#ffffff",
        "eye":  "#281808", "label": "LLAMA 2",
    },
    {   # 3 — chocolate brown
        "sky":  "#4060a0", "ground": "#386020",
        "fur":  "#703820", "shade":  "#401808", "light": "#985040",
        "eye":  "#180808", "label": "LLAMA 3",
    },
    {   # 4 — grey
        "sky":  "#607090", "ground": "#485828",
        "fur":  "#909090", "shade":  "#606060", "light": "#c0c0c0",
        "eye":  "#181818", "label": "LLAMA 4",
    },
]

# Llama body defined as (col_offset, row_offset, width, height, part)
# All coordinates relative to a 40×56 bounding box, scaled to fit the image.
# We'll draw at pixel scale, then the background fills the rest.

def draw_llama(draw, ox, oy, scale, pal):
    """
    Draw a pixel-art llama at origin (ox, oy) with the given pixel scale.
    The llama fits in a ~40×56 pixel block (before scaling).
    """
    fur   = hex_to_rgb(pal["fur"])
    shade = hex_to_rgb(pal["shade"])
    light = hex_to_rgb(pal["light"])
    eye   = hex_to_rgb(pal["eye"])

    def rect(c, r, w, h, color):
        x0 = ox + c * scale
        y0 = oy + r * scale
        draw.rectangle([x0, y0, x0 + w * scale - 1, y0 + h * scale - 1],
                       fill=color)

    # Ears
    rect(14, 0, 2, 3, shade)
    rect(20, 0, 2, 3, shade)
    # Head
    rect(12, 2, 12, 9, fur)
    rect(13, 3, 10, 7, light)
    # Eyes
    rect(14, 5, 2, 2, eye)
    rect(20, 5, 2, 2, eye)
    # Nose
    rect(16, 9, 4, 2, shade)
    # Neck
    rect(15, 11, 6, 9, fur)
    rect(16, 12, 4, 7, light)
    # Body
    rect(8, 19, 20, 14, fur)
    rect(9, 20, 18, 12, light)
    rect(8, 27, 20, 6, shade)   # belly shading
    # Tail
    rect(27, 19, 3, 5, shade)
    rect(28, 20, 2, 3, light)
    # Front legs
    rect(11, 33, 4, 14, fur)
    rect(12, 34, 2, 12, light)
    rect(16, 33, 4, 14, fur)
    rect(17, 34, 2, 12, light)
    # Hooves (front)
    rect(11, 46, 4, 2, shade)
    rect(16, 46, 4, 2, shade)
    # Back legs
    rect(20, 33, 4, 14, fur)
    rect(21, 34, 2, 12, light)
    rect(25, 33, 4, 14, fur)
    rect(26, 34, 2, 12, light)
    # Hooves (back)
    rect(20, 46, 4, 2, shade)
    rect(25, 46, 4, 2, shade)


def make_llama_photo(index, pal):
    PW, PH = 400, 300
    img  = Image.new("RGB", (PW, PH), hex_to_rgb(pal["sky"]))
    draw = ImageDraw.Draw(img)

    # Ground
    ground_y = PH * 2 // 3
    draw.rectangle([0, ground_y, PW, PH], fill=hex_to_rgb(pal["ground"]))

    # Simple pixel-art grass tufts
    grass = hex_to_rgb(pal["ground"])
    darker_grass = tuple(max(0, c - 30) for c in grass)
    rng = random.Random(index * 42)
    for _ in range(20):
        gx = rng.randint(0, PW - 10)
        gy = ground_y - rng.randint(2, 6)
        draw.rectangle([gx, gy, gx + 3, ground_y + 2], fill=darker_grass)

    # Clouds — blocky rectangles
    cloud = (220, 230, 240)
    for cx, cy in [(60, 40), (180, 70), (300, 35), (360, 80)]:
        draw.rectangle([cx, cy, cx + 40, cy + 14], fill=cloud)
        draw.rectangle([cx + 8, cy - 8, cx + 32, cy], fill=cloud)

    # Llama — scale 4, centred horizontally, sitting on ground line
    scale  = 4
    llama_w = 36 * scale   # approx pixel width of llama art
    llama_h = 48 * scale   # approx pixel height
    lx = (PW - llama_w) // 2 - 10
    ly = ground_y - llama_h + 8
    draw_llama(draw, lx, ly, scale, pal)

    # Label — bottom-right corner
    try:
        font = ImageFont.truetype(FONT_PATH, 12)
        draw.text((PW - 110, PH - 24), pal["label"], font=font,
                  fill=(255, 255, 255))
    except Exception:
        pass

    path = os.path.join(DEV_DIR, "llama_{}.png".format(index))
    img.save(path)
    print("  wrote", path)


print("Generating llama family photos…")
for i, pal in enumerate(LLAMA_PALETTES, start=1):
    make_llama_photo(i, pal)

# ---------------------------------------------------------------------------
# Llama dance frames  (32×32 pixel sprite, displayed scaled-up in CSS)
# Frame 0 — standing.  Frame 1 — arms/legs raised.
# ---------------------------------------------------------------------------

SPRITE_SIZE = 32

# Colour indices
BG   = (0,   0,   0,   0)   # transparent (RGBA)
FUR  = (196, 164,  96, 255)
DARK = (140, 100,  50, 255)
LITE = (220, 196, 140, 255)
EYE  = ( 40,  20,   8, 255)
NOSE = (160, 110,  60, 255)

def make_sprite(pixels):
    """
    Build a 32×32 RGBA image from a list of 32 strings, each 32 chars.
    Char codes:
      '.' = transparent
      'F' = FUR
      'D' = DARK
      'L' = LITE
      'E' = EYE
      'N' = NOSE
    """
    img  = Image.new("RGBA", (SPRITE_SIZE, SPRITE_SIZE), BG)
    draw = ImageDraw.Draw(img)
    lut  = {'.': BG, 'F': FUR, 'D': DARK, 'L': LITE, 'E': EYE, 'N': NOSE}
    for y, row in enumerate(pixels):
        for x, ch in enumerate(row):
            color = lut.get(ch, BG)
            if color != BG:
                draw.point((x, y), fill=color)
    return img


# Frame 0 — llama standing, legs down
FRAME_0_PIXELS = [
    "..............DD................",  # 0  ears
    "..............DD................",  # 1
    "............FFFFFF..............",  # 2  head top
    "...........FFFFFFFF.............",  # 3
    "...........FFLLLLLF.............",  # 4
    "...........FFLEELFF.............",  # 5  eyes
    "...........FFFLLLFFF............",  # 6
    "............FNNNNFF.............",  # 7  nose
    "............FFFFFFFF............",  # 8
    ".............FFFFFF.............",  # 9
    ".............FFFFFF.............",  # 10 neck
    "..............FFFF..............",  # 11
    "..............FFFF..............",  # 12
    "..............FFFF..............",  # 13
    ".........FFFFFFFFFFFFFF.........",  # 14 body
    "........FFFFFFFFFFFFFFFF........",  # 15
    "........FFLLLLLLLLLLLLFF........",  # 16
    "........FFLLLLLLLLLLLLFF........",  # 17
    "........FFLLLLLLLLLLLLFF........",  # 18
    "........FFDDDDDDDDDDDDF.........",  # 19 belly shade
    "........FFFFFFFFFFFFFFFF........",  # 20
    ".........FFFFFFFFFFFFFF.........",  # 21
    "..........FF....FF....FF........",  # 22 legs split
    "..........FF....FF....FF........",  # 23
    "..........FF....FF....FF........",  # 24
    "..........FF....FF....FF........",  # 25
    "..........FF....FF....FF........",  # 26
    "..........DD....DD....DD........",  # 27 hooves
    "................................",  # 28
    "................................",  # 29
    "................................",  # 30
    "................................",  # 31
]

# Frame 1 — dancing: front legs raised, slight body tilt
FRAME_1_PIXELS = [
    "..............DD................",  # 0  ears
    "..............DD................",  # 1
    "............FFFFFF..............",  # 2  head (same)
    "...........FFFFFFFF.............",  # 3
    "...........FFLLLLLF.............",  # 4
    "...........FFLEELFF.............",  # 5
    "...........FFFLLLFFF............",  # 6
    "............FNNNNFF.............",  # 7
    "............FFFFFFFF............",  # 8
    ".............FFFFFF.............",  # 9
    ".............FFFFFF.............",  # 10 neck
    "..............FFFF..............",  # 11
    "..............FFFF..............",  # 12
    "..............FFFF..............",  # 13
    ".........FFFFFFFFFFFFFF.........",  # 14 body
    "........FFFFFFFFFFFFFFFF........",  # 15
    "........FFLLLLLLLLLLLLFF........",  # 16
    "........FFLLLLLLLLLLLLFF........",  # 17
    "........FFLLLLLLLLLLLLFF........",  # 18
    "........FFDDDDDDDDDDDDF.........",  # 19
    "........FFFFFFFFFFFFFFFF........",  # 20
    ".........FFFFFFFFFFFFFF.........",  # 21
    "......FFFF....FF....FF..........",  # 22 front legs raised sideways
    ".....FF.......FF....FF..........",  # 23
    "....FF........FF....FF..........",  # 24
    "..DDF.........FF....FF..........",  # 25 hoof at top of raised leg
    "..............FF....FF..........",  # 26
    "..............DD....DD..........",  # 27 hooves (back legs only)
    "................................",  # 28
    "................................",  # 29
    "................................",  # 30
    "................................",  # 31
]


print("Generating llama dance frames…")
for frame_idx, pixels in enumerate([FRAME_0_PIXELS, FRAME_1_PIXELS]):
    sprite = make_sprite(pixels)
    path   = os.path.join(DEV_DIR, "llama_dance_{}.png".format(frame_idx))
    sprite.save(path)
    print("  wrote", path)

print("\nAll dev assets generated.")
print("Run 'python app.py' to start the dev server.")
