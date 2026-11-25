#!/usr/bin/env python3
"""Compose one day's world-news digest image (1024x1024 PNG).

Data-driven: a day spec (date line + stories) renders a broadsheet-style
front page — masthead with the date, one lead panel, a 2x2 grid, and a
bottom strip. All art is flat vector shapes drawn with PIL; all text is
rendered from TTF so nothing can garble. Deterministic: same spec, same
bytes.
"""
import json
import sys
from PIL import Image, ImageDraw, ImageFont

W = H = 1024
MARGIN = 28
PAPER = (250, 247, 240)
INK = (18, 18, 20)
RED = (178, 30, 32)
GRAY = (92, 92, 96)

FONT_DIR = "/usr/share/fonts/truetype"
SERIF_B = f"{FONT_DIR}/liberation/LiberationSerif-Bold.ttf"
SANS_B = f"{FONT_DIR}/liberation/LiberationSans-Bold.ttf"
SANS_R = f"{FONT_DIR}/liberation/LiberationSans-Regular.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


def text_w(draw, s, f):
    return draw.textlength(s, font=f)


def fit_font(draw, s, path, start, min_size, max_w):
    size = start
    while size > min_size:
        f = font(path, size)
        if text_w(draw, s, f) <= max_w:
            return f
        size -= 2
    return font(path, min_size)


def wrap(draw, s, f, max_w):
    words, lines, cur = s.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if text_w(draw, t, f) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_lines(draw, lines, x, y, f, fill, leading):
    for ln in lines:
        draw.text((x, y), ln, font=f, fill=fill)
        y += leading
    return y


# ---------- panel illustrations (flat shapes, box = x0,y0,x1,y1) ----------

def art_riyadh(d, w, h):
    # dusk bands
    d.rectangle([0, 0, w, h], fill=(38, 44, 74))
    d.rectangle([0, h * 2 // 3, w, h], fill=(214, 116, 52))
    # skyline silhouette
    base = h
    towers = [(0.02, 0.42), (0.12, 0.62), (0.24, 0.5), (0.36, 0.88), (0.47, 0.58),
              (0.58, 0.7), (0.70, 0.45), (0.80, 0.66), (0.90, 0.4)]
    bw = w / 10.5
    for fx, fh in towers:
        tx = fx * w
        th = fh * h * 0.92
        d.rectangle([tx, base - th, tx + bw, base], fill=(10, 10, 14))
    # the tallest tower (index 3) gets the blast near its top, kept inside
    tx = 0.36 * w + bw / 2
    ty = base - 0.88 * h * 0.92
    for r, col in ((30, (255, 122, 26)), (20, (255, 178, 44)), (11, (255, 226, 130))):
        d.ellipse([tx - r, ty - r, tx + r, ty + r], fill=col)
    # smoke drifting right, inside the frame
    for dx, dy, r in ((36, -16, 13), (62, -26, 17), (92, -34, 21)):
        d.ellipse([tx + dx - r, ty + dy - r, tx + dx + r, ty + dy + r], fill=(120, 118, 122))


def art_sea(d, w, h):
    d.rectangle([0, 0, w, h], fill=(168, 205, 224))             # sky
    sea_y = h // 3
    d.rectangle([0, sea_y, w, h], fill=(16, 84, 116))           # sea
    # warship silhouette, centred, scaled to the box
    wx, wy = w * 0.10, sea_y + (h - sea_y) * 0.16
    ww = w * 0.80
    d.polygon([(wx, wy), (wx + ww, wy), (wx + ww * 0.86, wy + h * 0.13),
               (wx + ww * 0.10, wy + h * 0.13)], fill=(34, 40, 48))
    d.rectangle([wx + ww * 0.34, wy - h * 0.15, wx + ww * 0.62, wy], fill=(34, 40, 48))
    d.rectangle([wx + ww * 0.44, wy - h * 0.26, wx + ww * 0.52, wy - h * 0.15], fill=(34, 40, 48))
    # blast at the bow
    bx, by = wx + ww * 0.94, wy - h * 0.02
    for r, col in ((15, (255, 122, 26)), (10, (255, 190, 60)), (5, (255, 232, 150))):
        d.ellipse([bx - r, by - r, bx + r, by + r], fill=col)
    # two drone boats below with wakes
    for fx, fy in ((0.22, 0.62), (0.52, 0.82)):
        bxx, byy = w * fx, sea_y + (h - sea_y) * fy
        d.polygon([(bxx - w * 0.20, byy + 5), (bxx - w * 0.02, byy - 2),
                   (bxx - w * 0.05, byy + 6)], fill=(235, 240, 244))
        d.polygon([(bxx, byy - 6), (bxx + w * 0.13, byy), (bxx, byy + 6)], fill=(22, 26, 32))


def art_china(d, w, h):
    x0, y0, x1, y1 = 0, 0, w, h
    d.rectangle([0, 0, w, h], fill=(158, 24, 30))
    cx, cy = w // 2, int(h * 0.44)
    # gold star
    import math
    pts = []
    R, r2 = (y1 - y0) * 0.30, (y1 - y0) * 0.125
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rad = R if i % 2 == 0 else r2
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    d.polygon(pts, fill=(245, 197, 66))
    # magnifier over the star's lower right = an investigation
    mx, my, mr = cx + R * 0.62, cy + R * 0.55, R * 0.52
    d.ellipse([mx - mr, my - mr, mx + mr, my + mr], outline=(250, 247, 240), width=10)
    d.line([mx + mr * 0.7, my + mr * 0.7, mx + mr * 1.45, my + mr * 1.45],
           fill=(250, 247, 240), width=13)


def art_chip(d, w, h):
    x0, y0, x1, y1 = 0, 0, w, h
    d.rectangle([0, 0, w, h], fill=(14, 20, 16))
    # chip
    cw = (x1 - x0) * 0.30
    cx0, cy0 = x0 + (x1 - x0) * 0.08, y0 + (y1 - y0) * 0.22
    d.rectangle([cx0, cy0, cx0 + cw, cy0 + cw], fill=(28, 148, 74), outline=(120, 230, 160), width=4)
    for i in range(4):
        px = cx0 + cw * (0.18 + 0.21 * i)
        d.line([px, cy0 - 14, px, cy0], fill=(120, 230, 160), width=5)
        d.line([px, cy0 + cw, px, cy0 + cw + 14], fill=(120, 230, 160), width=5)
    d.rectangle([cx0 + cw * 0.28, cy0 + cw * 0.28, cx0 + cw * 0.72, cy0 + cw * 0.72],
                outline=(220, 255, 230), width=4)
    # falling chart
    gx0, gy0 = cx0 + cw + (x1 - x0) * 0.07, y0 + (y1 - y0) * 0.16
    gx1, gy1 = x1 - (x1 - x0) * 0.05, y1 - (y1 - y0) * 0.14
    pts = [(gx0, gy0), (gx0 + (gx1 - gx0) * 0.3, gy0 + (gy1 - gy0) * 0.18),
           (gx0 + (gx1 - gx0) * 0.55, gy0 + (gy1 - gy0) * 0.10),
           (gx0 + (gx1 - gx0) * 0.8, gy0 + (gy1 - gy0) * 0.55), (gx1, gy1)]
    d.line(pts, fill=(238, 64, 54), width=9, joint="curve")
    ax, ay = pts[-1]
    d.polygon([(ax, ay), (ax - 26, ay - 4), (ax - 6, ay - 24)], fill=(238, 64, 54))


def art_rocket(d, w, h):
    x0, y0, x1, y1 = 0, 0, w, h
    d.rectangle([0, 0, w, h], fill=(10, 16, 48))
    for i in range(28):  # deterministic star field
        sx = x0 + ((i * 137) % max(1, (x1 - x0 - 12))) + 6
        sy = y0 + ((i * 89) % max(1, (y1 - y0 - 12))) + 6
        d.ellipse([sx, sy, sx + 3, sy + 3], fill=(230, 236, 255))
    # earth curve
    d.ellipse([x0 - (x1 - x0) * 0.3, y1 - (y1 - y0) * 0.34,
               x1 + (x1 - x0) * 0.3, y1 + (y1 - y0) * 0.55], fill=(38, 92, 168))
    # rocket, centre, angled up
    cx, cy = (x0 + x1) // 2, y0 + (y1 - y0) * 0.46
    rw, rh = (x1 - x0) * 0.13, (y1 - y0) * 0.52
    d.polygon([(cx, cy - rh / 2), (cx + rw / 2, cy - rh * 0.08), (cx + rw / 2, cy + rh / 2),
               (cx - rw / 2, cy + rh / 2), (cx - rw / 2, cy - rh * 0.08)], fill=(238, 240, 244))
    d.ellipse([cx - rw * 0.16, cy - rh * 0.26, cx + rw * 0.16, cy - rh * 0.02], fill=(70, 130, 200))
    d.polygon([(cx - rw / 2, cy + rh * 0.22), (cx - rw * 1.05, cy + rh * 0.52),
               (cx - rw / 2, cy + rh * 0.52)], fill=(200, 44, 44))
    d.polygon([(cx + rw / 2, cy + rh * 0.22), (cx + rw * 1.05, cy + rh * 0.52),
               (cx + rw / 2, cy + rh * 0.52)], fill=(200, 44, 44))
    for r, col in ((30, (255, 150, 40)), (19, (255, 196, 64)), (11, (255, 236, 170))):
        d.ellipse([cx - r, cy + rh / 2 - r * 0.4, cx + r, cy + rh / 2 + r * 1.5], fill=col)


def art_tanker(d, w, h):
    # night sky over the strait, sea below
    d.rectangle([0, 0, w, h], fill=(14, 22, 46))
    sea_y = h * 0.52
    d.rectangle([0, sea_y, w, h], fill=(16, 62, 92))
    # tanker: long hull at the waterline, bridge tower aft
    hx0, hx1 = w * 0.06, w * 0.94
    hy = sea_y + (h - sea_y) * 0.30
    d.polygon([(hx0, hy), (hx1, hy), (hx1 - w * 0.05, hy + h * 0.16),
               (hx0 + w * 0.04, hy + h * 0.16)], fill=(18, 22, 28))
    d.rectangle([hx1 - w * 0.17, hy - h * 0.22, hx1 - w * 0.05, hy], fill=(210, 214, 220))
    d.rectangle([hx1 - w * 0.15, hy - h * 0.30, hx1 - w * 0.07, hy - h * 0.22], fill=(150, 156, 164))
    # funnel
    d.rectangle([hx0 + w * 0.10, hy - h * 0.16, hx0 + w * 0.16, hy], fill=(178, 30, 32))
    # blast amidships
    bx, by = w * 0.48, hy - h * 0.05
    for r, col in ((30, (255, 122, 26)), (20, (255, 178, 44)), (11, (255, 226, 130))):
        d.ellipse([bx - r, by - r, bx + r, by + r], fill=col)
    # smoke drifting right, inside the frame
    for dx, dy, r in ((38, -18, 13), (64, -28, 17), (94, -36, 20)):
        d.ellipse([bx + dx - r, by + dy - r, bx + dx + r, by + dy + r], fill=(120, 118, 122))
    # a naval mine at the waterline, fore of the blast
    mx, my = w * 0.24, hy + h * 0.10
    d.ellipse([mx - 9, my - 9, mx + 9, my + 9], fill=(10, 10, 14))
    for dx, dy in ((-12, 0), (12, 0), (0, -12), (0, 12), (-8, -8), (8, -8), (-8, 8), (8, 8)):
        d.line([mx, my, mx + dx, my + dy], fill=(10, 10, 14), width=3)


ART = {"riyadh": art_riyadh, "sea": art_sea, "china": art_china,
       "chip": art_chip, "rocket": art_rocket, "tanker": art_tanker}


def paste_art(img, name, box):
    """Render one illustration on its own layer and paste it clipped to box."""
    x0, y0, x1, y1 = box
    layer = Image.new("RGB", (x1 - x0, y1 - y0), (255, 255, 255))
    ART[name](ImageDraw.Draw(layer), x1 - x0, y1 - y0)
    img.paste(layer, (x0, y0))


def panel(d, box, story, art_h_ratio=0.46, head_size=31, sub_size=21, img=None):
    x0, y0, x1, y1 = box
    d.rectangle(box, fill=(255, 255, 255), outline=INK, width=3)
    art_h = int((y1 - y0) * art_h_ratio)
    paste_art(img, story["art"], (x0 + 3, y0 + 3, x1 - 3, y0 + art_h))
    tx, ty = x0 + 16, y0 + art_h + 12
    f_head = fit_font(d, story["headline"], SANS_B, head_size, 20, x1 - x0 - 32)
    lines = wrap(d, story["headline"], f_head, x1 - x0 - 32)[:3]
    ty = draw_lines(d, lines, tx, ty, f_head, INK, int(f_head.size * 1.12))
    f_sub = font(SANS_R, sub_size)
    sub = wrap(d, story["sub"], f_sub, x1 - x0 - 32)[:2]
    draw_lines(d, sub, tx, ty + 4, f_sub, GRAY, int(sub_size * 1.25))


def panel_h(d, box, story, art_w=148, head_size=26, sub_size=19, img=None):
    """Horizontal cell: art as a left column, headline + sub to its right."""
    x0, y0, x1, y1 = box
    d.rectangle(box, fill=(255, 255, 255), outline=INK, width=3)
    paste_art(img, story["art"], (x0 + 3, y0 + 3, x0 + art_w, y1 - 3))
    tx = x0 + art_w + 14
    tw = x1 - tx - 12
    f_tag = font(SANS_B, 17)
    d.text((tx, y0 + 10), story.get("tag", ""), font=f_tag, fill=RED)
    f_head = fit_font(d, story["headline"], SANS_B, head_size, 19, tw)
    lines = wrap(d, story["headline"], f_head, tw)[:3]
    ty = draw_lines(d, lines, tx, y0 + 34, f_head, INK, int(f_head.size * 1.14))
    f_sub = font(SANS_R, sub_size)
    sub = wrap(d, story["sub"], f_sub, tw)[:2]
    draw_lines(d, sub, tx, ty + 3, f_sub, GRAY, int(sub_size * 1.22))


def compose(spec):
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    # masthead
    f_kick = font(SANS_B, 25)
    kick = spec["kicker"]
    d.text(((W - text_w(d, kick, f_kick)) / 2, 22), kick, font=f_kick, fill=GRAY)
    f_date = fit_font(d, spec["date_line"], SERIF_B, 66, 40, W - 2 * MARGIN)
    d.text(((W - text_w(d, spec["date_line"], f_date)) / 2, 54),
           spec["date_line"], font=f_date, fill=INK)
    d.rectangle([MARGIN, 138, W - MARGIN, 144], fill=RED)
    d.rectangle([MARGIN, 150, W - MARGIN, 153], fill=INK)
    # lead panel
    lead = spec["stories"][0]
    panel(d, (MARGIN, 166, W - MARGIN, 478), lead, art_h_ratio=0.50, head_size=43, sub_size=24, img=img)
    # 2x2 grid of horizontal cells
    gx, gy = MARGIN, 492
    cw, chh = (W - 2 * MARGIN - 14) // 2, 160
    for i, story in enumerate(spec["stories"][1:5]):
        px = gx + (i % 2) * (cw + 14)
        py = gy + (i // 2) * (chh + 14)
        panel_h(d, (px, py, px + cw, py + chh), story, img=img)
    # bottom strip: sixth story wide + brief line
    by = gy + 2 * chh + 14
    fifth = spec["stories"][5]
    d.rectangle([MARGIN, by, W - MARGIN, by + 78], fill=INK)
    f_tag = font(SANS_B, 24)
    tag_w = text_w(d, fifth["tag"], f_tag)
    d.text((MARGIN + 18, by + (78 - 24) // 2), fifth["tag"], font=f_tag, fill=(255, 196, 64))
    hx = MARGIN + 18 + tag_w + 14
    f5 = fit_font(d, fifth["headline"], SANS_B, 30, 20, W - MARGIN - hx - 12)
    d.text((hx, by + (78 - f5.size) // 2), fifth["headline"], font=f5,
           fill=(255, 255, 255))
    f_brief = fit_font(d, spec["brief"], SANS_R, 21, 16, W - 2 * MARGIN)
    d.text((MARGIN, by + 92), spec["brief"], font=f_brief, fill=GRAY)
    return img


def main():
    spec = json.load(open(sys.argv[1]))
    img = compose(spec)
    img.save(sys.argv[2], format="PNG", optimize=True)
    print("wrote", sys.argv[2])


if __name__ == "__main__":
    main()
