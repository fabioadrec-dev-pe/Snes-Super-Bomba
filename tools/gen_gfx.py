#!/usr/bin/env python3
"""Gera título rochoso e folha de fonte 8x8 para Super Bomba."""

from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
GFX = ROOT / "gfx"
GFX.mkdir(exist_ok=True)

FONT_CHARS = (
    " !\"#$%&'()*+,-./"
    "0123456789:;<=>?"
    "@ABCDEFGHIJKLMNO"
    "PQRSTUVWXYZ[\\]^_"
    "ÇÕÁÉÍÓÚÂÊÔÃ"
)


def hash_noise(x: int, y: int, seed: int = 0) -> float:
    n = (x * 374761393 + y * 668265263 + seed * 982451653) & 0xFFFFFFFF
    n = (n ^ (n >> 13)) * 1274126177
    return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0


def fbm(x: float, y: float, seed: int) -> float:
    v = 0.0
    a = 0.5
    f = 1.0
    for i in range(5):
        v += a * hash_noise(int(x * f), int(y * f), seed + i * 17)
        a *= 0.5
        f *= 2.05
    return v


def rock_color(u: float, v: float, seed: int) -> tuple[int, int, int]:
    n = fbm(u, v, seed)
    strata = 0.5 + 0.5 * math.sin(v * 0.22 + n * 3.5)
    crack = abs(math.sin(u * 0.41 + n * 5.0) * math.cos(v * 0.33 + n * 2.2))
    shade = 48 + int(n * 110) + int(strata * 28) - int(crack * 40)
    r = max(0, min(255, shade + 28))
    g = max(0, min(255, shade + 4))
    b = max(0, min(255, shade - 26))
    if n > 0.72:
        r = min(255, r + 50)
        g = min(255, g + 42)
        b = min(255, b + 28)
    if crack > 0.85:
        r = max(0, r - 45)
        g = max(0, g - 45)
        b = max(0, b - 40)
    return r, g, b


def load_font(size: int) -> ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def make_title() -> Image.Image:
    w, h = 256, 64
    bg = (8, 6, 14)
    img = Image.new("RGB", (w, h), bg)
    px = img.load()

    for y in range(h):
        for x in range(w):
            n = hash_noise(x, y, 9)
            px[x, y] = (6 + int(n * 16), 5 + int(n * 12), 12 + int(n * 20))

    font = load_font(26)
    font_inner = load_font(22)

    def draw_line(text: str, top: int) -> Image.Image:
        """Máscara da linha com letras separadas + contorno interno escuro."""
        line = Image.new("L", (w, h), 0)
        inner = Image.new("L", (w, h), 0)
        draw = ImageDraw.Draw(line)
        draw_i = ImageDraw.Draw(inner)

        # largura total com espaçamento entre letras
        spacing = 3
        widths = []
        for ch in text:
            bbox = draw.textbbox((0, 0), ch, font=font)
            widths.append(bbox[2] - bbox[0])
        total = sum(widths) + spacing * (len(text) - 1)
        x = (w - total) // 2

        for ch, cw in zip(text, widths):
            bbox = draw.textbbox((0, 0), ch, font=font)
            ox = x - bbox[0]
            oy = top - bbox[1]
            # contorno externo
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    if dx * dx + dy * dy <= 5:
                        draw.text((ox + dx, oy + dy), ch, font=font, fill=200)
            draw.text((ox, oy), ch, font=font, fill=255)
            # núcleo interno (gera fenda escura entre face e borda)
            ib = draw_i.textbbox((0, 0), ch, font=font_inner)
            ix = x + (cw - (ib[2] - ib[0])) // 2 - ib[0]
            iy = top + 2 - ib[1]
            draw_i.text((ix, iy), ch, font=font_inner, fill=255)
            x += cw + spacing

        return line, inner

    mask = Image.new("L", (w, h), 0)
    inner_mask = Image.new("L", (w, h), 0)
    crack_mask = Image.new("L", (w, h), 0)

    for text, top in [("SUPER", 4), ("BOMBA", 34)]:
        line, inner = draw_line(text, top)
        mp = line.load()
        ip = inner.load()
        mpx = mask.load()
        ipx = inner_mask.load()
        for y in range(h):
            for x in range(w):
                if mp[x, y] > mpx[x, y]:
                    mpx[x, y] = mp[x, y]
                if ip[x, y] > ipx[x, y]:
                    ipx[x, y] = ip[x, y]

    # fendas = área da letra menos o núcleo interno (contorno interno)
    mpx = mask.load()
    ipx = inner_mask.load()
    cpx = crack_mask.load()
    for y in range(h):
        for x in range(w):
            if mpx[x, y] > 40 and ipx[x, y] < 80:
                cpx[x, y] = 255

    mask = mask.filter(ImageFilter.MaxFilter(3))
    crack_mask = crack_mask.filter(ImageFilter.MaxFilter(3))
    mpx = mask.load()
    cpx = crack_mask.load()

    # sombra projetada
    for y in range(h):
        for x in range(w):
            if x >= 3 and y >= 3 and mpx[x - 3, y - 3] > 50:
                r, g, b = px[x, y]
                px[x, y] = (r // 4, g // 4, b // 4)

    crack_rgb = (18, 12, 8)
    for y in range(h):
        for x in range(w):
            a = mpx[x, y]
            if a < 18:
                continue
            if cpx[x, y] > 120:
                px[x, y] = crack_rgb
                continue
            base = rock_color(x * 1.35, y * 1.55, 3)
            edge = 0
            if x > 0 and mpx[x - 1, y] < 40:
                edge += 40
            if y > 0 and mpx[x, y - 1] < 40:
                edge += 55
            if x + 1 < w and mpx[x + 1, y] < 40:
                edge -= 30
            if y + 1 < h and mpx[x, y + 1] < 40:
                edge -= 40
            lit = tuple(max(0, min(255, c + edge)) for c in base)
            t = min(1.0, a / 235.0)
            bgc = px[x, y]
            px[x, y] = tuple(int(bgc[i] * (1 - t) + lit[i] * t) for i in range(3))

    rng = random.Random(42)
    for _ in range(220):
        x = rng.randint(0, w - 1)
        y = rng.randint(0, h - 1)
        if mpx[x, y] > 130 and cpx[x, y] < 40 and hash_noise(x, y, 21) > 0.82:
            r, g, b = px[x, y]
            px[x, y] = (max(0, r - 18), min(255, g + 22), max(0, b - 8))

    return img


# Glifos 8x8 manuais (menu + acentos PT-BR)
MANUAL = {
    " ": [],
    ">": [(2, 1), (3, 2), (4, 3), (3, 4), (2, 5), (3, 3)],
    "1": [(3, 1), (2, 2), (3, 2), (3, 3), (3, 4), (3, 5), (2, 6), (3, 6), (4, 6)],
    "2": [
        (2, 1), (3, 1), (4, 1), (5, 2), (4, 3), (3, 4), (2, 5),
        (2, 6), (3, 6), (4, 6), (5, 6),
    ],
    "A": [
        (3, 1), (2, 2), (4, 2), (2, 3), (4, 3), (1, 4), (2, 4), (3, 4), (4, 4), (5, 4),
        (1, 5), (5, 5), (1, 6), (5, 6),
    ],
    "D": [
        (1, 1), (2, 1), (3, 1), (4, 1), (1, 2), (5, 2), (1, 3), (5, 3),
        (1, 4), (5, 4), (1, 5), (5, 5), (1, 6), (2, 6), (3, 6), (4, 6),
    ],
    "E": [
        (1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (1, 2), (1, 3), (2, 3), (3, 3), (4, 3),
        (1, 4), (1, 5), (1, 6), (2, 6), (3, 6), (4, 6), (5, 6),
    ],
    "G": [
        (2, 1), (3, 1), (4, 1), (1, 2), (1, 3), (1, 4), (3, 4), (4, 4), (5, 4),
        (1, 5), (5, 5), (2, 6), (3, 6), (4, 6),
    ],
    "J": [
        (4, 1), (4, 2), (4, 3), (4, 4), (1, 5), (4, 5), (2, 6), (3, 6),
    ],
    "O": [
        (2, 1), (3, 1), (4, 1), (1, 2), (5, 2), (1, 3), (5, 3),
        (1, 4), (5, 4), (1, 5), (5, 5), (2, 6), (3, 6), (4, 6),
    ],
    "P": [
        (1, 1), (2, 1), (3, 1), (4, 1), (1, 2), (5, 2), (1, 3), (2, 3), (3, 3), (4, 3),
        (1, 4), (1, 5), (1, 6),
    ],
    "R": [
        (1, 1), (2, 1), (3, 1), (4, 1), (1, 2), (5, 2), (1, 3), (2, 3), (3, 3), (4, 3),
        (1, 4), (3, 4), (1, 5), (4, 5), (1, 6), (5, 6),
    ],
    "S": [
        (2, 1), (3, 1), (4, 1), (5, 1), (1, 2), (1, 3), (2, 3), (3, 3), (4, 3),
        (5, 4), (5, 5), (1, 6), (2, 6), (3, 6), (4, 6),
    ],
    "Ç": [
        (2, 1), (3, 1), (4, 1), (1, 2), (1, 3), (1, 4), (1, 5),
        (2, 6), (3, 6), (4, 6), (3, 7), (2, 7),
    ],
    "Õ": [
        (2, 0), (4, 0), (3, 1),
        (2, 2), (3, 2), (4, 2), (1, 3), (5, 3), (1, 4), (5, 4),
        (1, 5), (5, 5), (2, 6), (3, 6), (4, 6),
    ],
}


def make_letter_pixels(ch: str) -> set[tuple[int, int]]:
    if ch in MANUAL:
        return set(MANUAL[ch])

    img = Image.new("L", (8, 8), 0)
    draw = ImageDraw.Draw(img)
    font = load_font(8)
    bbox = draw.textbbox((0, 0), ch, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = max(0, (8 - tw) // 2 - bbox[0])
    y = max(0, (8 - th) // 2 - bbox[1] - 1)
    draw.text((x, y), ch, font=font, fill=255)
    sp = img.load()
    pts = set()
    for yy in range(8):
        for xx in range(8):
            if sp[xx, yy] > 100:
                pts.add((xx, yy))
    return pts


def make_font_sheet() -> Image.Image:
    """Folha indexada: cor 0 = transparente, cor 1 = branco."""
    cols = 16
    rows = (len(FONT_CHARS) + cols - 1) // cols
    sheet = Image.new("P", (cols * 8, rows * 8), 0)
    sheet.putpalette([0, 0, 0, 255, 255, 255] + [0] * (254 * 3))
    px = sheet.load()
    for i, ch in enumerate(FONT_CHARS):
        pts = make_letter_pixels(ch)
        cx = (i % cols) * 8
        cy = (i // cols) * 8
        for x, y in pts:
            if 0 <= x < 8 and 0 <= y < 8:
                px[cx + x, cy + y] = 1
    return sheet


def write_font_map_asm(path: Path) -> None:
    lines = [
        "; Mapa caractere -> indice de tile da fonte",
        "FontCharCount:",
        f"db {len(FONT_CHARS)}",
        "",
        "FontCharset:",
    ]
    for ch in FONT_CHARS:
        code = ord(ch) if ord(ch) < 256 else 0
        safe = ch if ch not in ('"', "\\") else "."
        lines.append(f"db ${code:02X} ; {safe}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def quantize_snes(img: Image.Image, colors: int = 15) -> Image.Image:
    """Quantiza para caber em 1 subpaleta SNES (cor 0 reservada ao fundo)."""
    bg = (8, 6, 14)
    # força pixels quase-pretos para o backdrop
    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            if r + g + b < 40:
                px[x, y] = bg
    pal = img.quantize(colors=colors, method=Image.Quantize.MEDIANCUT)
    return pal.convert("RGB")


def main() -> None:
    title = quantize_snes(make_title(), colors=15)
    title.save(GFX / "title.png")

    font = make_font_sheet()
    font.save(GFX / "font.png")

    write_font_map_asm(ROOT / "fontmap.asm")
    print(f"chars={len(FONT_CHARS)}")
    print(f"wrote {GFX / 'title.png'}")
    print(f"wrote {GFX / 'font.png'}")


if __name__ == "__main__":
    main()
