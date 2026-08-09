#!/usr/bin/env python3
"""
Gera sprites 16x16 (4 tiles 8x8) para Super Bomba.
Estilo Super Bomberman SNES, porém mais detalhado/realista.

Jogador 1: terno | Jogador 2: cientista | Inimigos: abrasileirados
Saída em gfx/chars/ e gfx/anim/ — não integra ao game.asm.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
GFX = ROOT / "gfx"
CHARS = GFX / "chars"
ANIM = GFX / "anim"

FRAME_W = 16
FRAME_H = 16
ATLAS_COLS = 16  # frames por linha no atlas mestre

# ---------------------------------------------------------------------------
# Paletas (índice 0 = transparente)
# ---------------------------------------------------------------------------

Palette = List[Tuple[int, int, int]]


def pal(
    skin: str,
    hair: str,
    main: str,
    main_hi: str,
    accent: str,
    accent2: str,
    dark: str,
    shoe: str,
    extra: str = "#000000",
) -> Palette:
    def hx(s: str) -> Tuple[int, int, int]:
        s = s.lstrip("#")
        return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))

    return [
        (0, 0, 0),  # 0 transparent (PIL index 0)
        hx(skin),
        hx(hair),
        hx(main),
        hx(main_hi),
        hx(accent),
        hx(accent2),
        hx(dark),
        hx(shoe),
        hx(extra),
    ]


PAL_P1 = pal(
    skin="#E8B890",
    hair="#2A2220",
    main="#1A2848",      # terno
    main_hi="#3A5078",
    accent="#F0F0F0",    # camisa
    accent2="#C02030",   # gravata
    dark="#101820",
    shoe="#1A1A1A",
    extra="#8A9098",     # relógio/prata
)

PAL_P2 = pal(
    skin="#E8B890",
    hair="#6A4030",
    main="#F4F4EE",      # jaleco
    main_hi="#D8D8D0",
    accent="#40A060",    # camisa
    accent2="#40C0E0",   # óculos
    dark="#3A3A50",
    shoe="#2A2A30",
    extra="#808890",     # caneta/metal
)

PAL_EN_CAIPIRA = pal(
    skin="#D8A070",
    hair="#4A3020",
    main="#D8B060",      # chapéu
    main_hi="#F0D080",
    accent="#E08040",    # camisa
    accent2="#2060A0",   # bermuda
    dark="#8A5030",
    shoe="#F0E8C0",      # chinelo
    extra="#6A4020",
)

PAL_EN_CARNAVAL = pal(
    skin="#E8B080",
    hair="#1A1A1A",
    main="#E04080",      # rosa carnaval
    main_hi="#FF80B0",
    accent="#FFD700",    # dourado
    accent2="#40C040",   # verde
    dark="#802060",
    shoe="#FFD700",
    extra="#8040C0",     # roxo
)

PAL_EN_TORCEDOR = pal(
    skin="#D8A070",
    hair="#2A2018",
    main="#009739",      # verde
    main_hi="#00B848",
    accent="#FFCC00",    # amarelo
    accent2="#F0F0F0",   # shorts
    dark="#006020",
    shoe="#1A1A1A",
    extra="#C02020",     # vermelho detalhe
)

PAL_ITEMS = [
    (0, 0, 0),
    (40, 40, 48),       # bomb body
    (80, 80, 96),       # bomb highlight
    (200, 40, 40),      # fuse / red
    (255, 200, 60),    # flame yellow
    (255, 120, 20),    # flame orange
    (255, 60, 20),     # flame red
    (200, 200, 220),   # smoke
    (160, 160, 180),   # smoke dark
    (60, 180, 255),    # powerup blue
    (255, 80, 80),     # powerup red
    (80, 220, 100),    # powerup green
    (255, 220, 60),    # powerup yellow
    (180, 100, 255),   # powerup purple
    (255, 255, 255),   # white
    (40, 40, 40),      # black
]

# ---------------------------------------------------------------------------
# Canvas de sprite
# ---------------------------------------------------------------------------

@dataclass
class Frame:
    name: str
    pixels: Dict[Tuple[int, int], int]


class SpriteCanvas:
    def __init__(self) -> None:
        self.px: Dict[Tuple[int, int], int] = {}

    def clear(self) -> None:
        self.px.clear()

    def set(self, x: int, y: int, c: int) -> None:
        if 0 <= x < FRAME_W and 0 <= y < FRAME_H and c > 0:
            self.px[(x, y)] = c

    def fill(self, x0: int, y0: int, x1: int, y1: int, c: int) -> None:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.set(x, y, c)

    def hline(self, x0: int, x1: int, y: int, c: int) -> None:
        for x in range(x0, x1 + 1):
            self.set(x, y, c)

    def vline(self, x: int, y0: int, y1: int, c: int) -> None:
        for y in range(y0, y1 + 1):
            self.set(x, y, c)

    def rect(self, x0: int, y0: int, w: int, h: int, c: int) -> None:
        self.fill(x0, y0, x0 + w - 1, y0 + h - 1, c)

    def copy(self) -> Frame:
        return Frame("", dict(self.px))

    def blit_frame(self, frame: Frame, ox: int = 0, oy: int = 0) -> None:
        for (x, y), c in frame.pixels.items():
            self.set(x + ox, y + oy, c)


# Índices de cor comuns
SK, HR, MN, MH, AC, AC2, DK, SH, EX = 1, 2, 3, 4, 5, 6, 7, 8, 9

Dir = str  # D U L R


# ---------------------------------------------------------------------------
# Desenho base — jogador 1 (terno)
# ---------------------------------------------------------------------------

def draw_p1_head(c: SpriteCanvas, d: Dir, y_off: int = 0) -> None:
    y = 1 + y_off
    if d == "D":
        c.fill(5, y, 10, y + 4, SK)
        c.fill(6, y, 9, y + 1, HR)
        c.set(6, y + 2, DK)
        c.set(9, y + 2, DK)
        c.set(7, y + 3, DK)
        c.set(8, y + 3, DK)
    elif d == "U":
        c.fill(5, y, 10, y + 4, HR)
        c.fill(6, y + 3, 9, y + 4, SK)
    elif d == "L":
        c.fill(4, y, 8, y + 4, SK)
        c.fill(4, y, 7, y + 2, HR)
        c.set(5, y + 3, DK)
        c.set(6, y + 2, DK)
    else:  # R
        c.fill(7, y, 11, y + 4, SK)
        c.fill(8, y, 11, y + 2, HR)
        c.set(9, y + 3, DK)
        c.set(8, y + 2, DK)


def draw_p1_torso(c: SpriteCanvas, d: Dir, y_off: int = 0) -> None:
    y = 5 + y_off
    if d in ("D", "U"):
        c.fill(5, y, 10, y + 4, MN)
        c.fill(6, y, 9, y + 1, MH)
        if d == "D":
            c.fill(7, y + 1, 8, y + 3, AC)  # camisa
            c.fill(7, y + 2, 8, y + 3, AC2)  # gravata
            c.set(6, y + 2, EX)  # relógio
    elif d == "L":
        c.fill(3, y, 8, y + 4, MN)
        c.fill(3, y, 6, y + 2, MH)
        c.fill(6, y + 1, 7, y + 3, AC)
    else:
        c.fill(7, y, 12, y + 4, MN)
        c.fill(9, y, 12, y + 2, MH)
        c.fill(8, y + 1, 9, y + 3, AC)


def draw_p1_legs(c: SpriteCanvas, d: Dir, step: int, y_off: int = 0) -> None:
    y = 9 + y_off
    if step == 0:
        c.fill(6, y, 7, y + 4, MN)
        c.fill(8, y, 9, y + 4, MN)
        c.fill(6, y + 4, 7, y + 5, SH)
        c.fill(8, y + 4, 9, y + 5, SH)
    elif step == 1:
        c.fill(5, y, 6, y + 3, MN)
        c.fill(8, y + 1, 9, y + 5, MN)
        c.fill(5, y + 3, 6, y + 4, SH)
        c.fill(8, y + 5, 9, y + 6, SH)
    else:
        c.fill(8, y, 9, y + 3, MN)
        c.fill(5, y + 1, 6, y + 5, MN)
        c.fill(8, y + 3, 9, y + 4, SH)
        c.fill(5, y + 5, 6, y + 6, SH)


def draw_p1_arms_idle(c: SpriteCanvas, d: Dir, y_off: int = 0) -> None:
    y = 6 + y_off
    if d == "D":
        c.fill(4, y, 4, y + 2, MN)
        c.fill(11, y, 11, y + 2, MN)
    elif d == "U":
        c.fill(4, y, 4, y + 2, MN)
        c.fill(11, y, 11, y + 2, MN)
    elif d == "L":
        c.fill(2, y, 3, y + 2, MN)
        c.fill(7, y + 1, 8, y + 3, MN)
    else:
        c.fill(12, y, 13, y + 2, MN)
        c.fill(7, y + 1, 8, y + 3, MN)


def draw_p1_place_bomb(c: SpriteCanvas, d: Dir, phase: int) -> None:
    """phase 0=parado, 1=abaixando, 2=bomba no chão."""
    y_off = 1 if phase >= 1 else 0
    draw_p1_head(c, d, y_off)
    draw_p1_torso(c, d, y_off)
    if phase == 0:
        draw_p1_legs(c, d, 0, y_off)
        draw_p1_arms_idle(c, d, y_off)
    elif phase == 1:
        draw_p1_legs(c, d, 0, y_off + 1)
        y = 7 + y_off
        if d == "D":
            c.fill(5, y, 6, y + 2, MN)
            c.fill(9, y, 10, y + 2, MN)
            c.fill(7, y + 2, 8, y + 3, SK)
        elif d == "L":
            c.fill(1, y, 3, y + 2, MN)
            c.fill(6, y + 1, 7, y + 3, SK)
        elif d == "R":
            c.fill(12, y, 14, y + 2, MN)
            c.fill(8, y + 1, 9, y + 3, SK)
        else:
            draw_p1_arms_idle(c, d, y_off)
    else:
        draw_p1_legs(c, d, 0, y_off + 1)
        y = 7 + y_off
        if d == "D":
            c.fill(5, y + 1, 6, y + 2, MN)
            c.fill(9, y + 1, 10, y + 2, MN)
            c.fill(7, y + 2, 8, y + 3, SK)
            c.fill(7, 13, 8, 14, DK)  # bomba
            c.fill(7, 12, 8, 12, AC2)
        elif d == "L":
            c.fill(1, y, 2, y + 2, MN)
            c.fill(5, y + 2, 6, y + 3, SK)
            c.fill(3, 13, 4, 14, DK)
        elif d == "R":
            c.fill(13, y, 14, y + 2, MN)
            c.fill(9, y + 2, 10, y + 3, SK)
            c.fill(11, 13, 12, 14, DK)
        else:
            c.fill(7, 13, 8, 14, DK)


def draw_p1_carry(c: SpriteCanvas, d: Dir, step: int) -> None:
    draw_p1_head(c, d)
    draw_p1_torso(c, d)
    draw_p1_legs(c, d, step)
    y = 5
    # bomba acima da cabeça
    c.fill(6, 0, 9, 1, DK)
    c.fill(7, 0, 8, 0, AC2)
    if d == "D":
        c.fill(4, y, 5, y + 2, MN)
        c.fill(10, y, 11, y + 2, MN)
        c.fill(5, y - 1, 6, y, MN)
        c.fill(9, y - 1, 10, y, MN)
    elif d == "L":
        c.fill(2, y - 1, 4, y + 1, MN)
        c.fill(6, y - 2, 8, y, MN)
    elif d == "R":
        c.fill(11, y - 1, 13, y + 1, MN)
        c.fill(7, y - 2, 9, y, MN)
    else:
        c.fill(4, y, 5, y + 1, MN)
        c.fill(10, y, 11, y + 1, MN)


def draw_p1_die(c: SpriteCanvas, phase: int) -> None:
    if phase < 3:
        d = "D"
        draw_p1_head(c, d, phase)
        draw_p1_torso(c, d, phase)
        draw_p1_legs(c, d, 0, phase)
    elif phase == 3:
        c.fill(4, 8, 11, 12, MN)
        c.fill(5, 6, 10, 9, SK)
        c.fill(3, 12, 12, 14, MN)
    elif phase == 4:
        c.fill(2, 10, 13, 14, MN)
        c.fill(4, 8, 11, 11, SK)
    else:
        # espírito / estrelas
        for x, y in [(3, 4), (11, 3), (7, 7), (5, 10), (10, 9)]:
            c.fill(x, y, x + 1, y + 1, AC)
            c.set(x, y + 1, MH)


def draw_p1_win(c: SpriteCanvas, phase: int) -> None:
    jump = {0: 0, 1: -2, 2: -1}[phase]
    draw_p1_head(c, "D", jump)
    draw_p1_torso(c, "D", jump)
    draw_p1_legs(c, "D", phase % 2, jump)
    if phase >= 1:
        c.fill(3, 4 + jump, 4, 6 + jump, MN)
        c.fill(11, 4 + jump, 12, 6 + jump, MN)
    if phase == 2:
        c.fill(5, 0, 6, 1, AC2)
        c.fill(9, 0, 10, 1, AC2)


def make_p1_frame(kind: str, d: Dir, sub: int) -> Frame:
    c = SpriteCanvas()
    if kind == "idle":
        draw_p1_head(c, d)
        draw_p1_torso(c, d)
        draw_p1_legs(c, d, 0)
        draw_p1_arms_idle(c, d)
    elif kind == "walk":
        draw_p1_head(c, d, sub % 2)
        draw_p1_torso(c, d, sub % 2)
        draw_p1_legs(c, d, sub)
        draw_p1_arms_idle(c, d, sub % 2)
    elif kind == "place":
        draw_p1_place_bomb(c, d, sub)
    elif kind == "carry":
        draw_p1_carry(c, d, sub)
    elif kind == "die":
        draw_p1_die(c, sub)
    elif kind == "win":
        draw_p1_win(c, sub)
    f = c.copy()
    f.name = f"p1_{kind}_{d}_{sub}"
    return f


# ---------------------------------------------------------------------------
# Jogador 2 — cientista
# ---------------------------------------------------------------------------

def draw_p2_head(c: SpriteCanvas, d: Dir, y_off: int = 0) -> None:
    y = 1 + y_off
    if d == "D":
        c.fill(5, y, 10, y + 4, SK)
        c.fill(5, y, 10, y + 2, HR)  # cabelo bagunçado
        c.set(5, y + 1, HR)
        c.set(10, y + 1, HR)
        c.fill(6, y + 2, 9, y + 2, AC2)  # óculos
        c.set(6, y + 3, DK)
        c.set(9, y + 3, DK)
    elif d == "U":
        c.fill(5, y, 10, y + 4, HR)
        c.fill(6, y + 3, 9, y + 4, SK)
    elif d == "L":
        c.fill(4, y, 8, y + 4, SK)
        c.fill(4, y, 7, y + 2, HR)
        c.fill(6, y + 2, 8, y + 2, AC2)
        c.set(5, y + 3, DK)
    else:
        c.fill(7, y, 11, y + 4, SK)
        c.fill(8, y, 11, y + 2, HR)
        c.fill(7, y + 2, 9, y + 2, AC2)
        c.set(9, y + 3, DK)


def draw_p2_torso(c: SpriteCanvas, d: Dir, y_off: int = 0) -> None:
    y = 5 + y_off
    if d in ("D", "U"):
        c.fill(4, y, 11, y + 5, MN)  # jaleco mais largo
        c.fill(5, y, 10, y + 1, MH)
        if d == "D":
            c.fill(6, y + 2, 9, y + 3, AC)  # camisa
            c.set(4, y + 3, EX)  # caneta no bolso
            c.set(11, y + 4, EX)
    elif d == "L":
        c.fill(3, y, 8, y + 5, MN)
        c.fill(3, y, 6, y + 2, MH)
        c.fill(6, y + 2, 7, y + 4, AC)
    else:
        c.fill(7, y, 12, y + 5, MN)
        c.fill(9, y, 12, y + 2, MH)
        c.fill(8, y + 2, 9, y + 4, AC)


def draw_p2_legs(c: SpriteCanvas, d: Dir, step: int, y_off: int = 0) -> None:
    y = 10 + y_off
    if step == 0:
        c.fill(6, y, 7, y + 3, DK)
        c.fill(8, y, 9, y + 3, DK)
        c.fill(6, y + 3, 7, y + 4, SH)
        c.fill(8, y + 3, 9, y + 4, SH)
    elif step == 1:
        c.fill(5, y, 6, y + 2, DK)
        c.fill(8, y + 1, 9, y + 4, DK)
        c.fill(5, y + 2, 6, y + 3, SH)
        c.fill(8, y + 4, 9, y + 5, SH)
    else:
        c.fill(8, y, 9, y + 2, DK)
        c.fill(5, y + 1, 6, y + 4, DK)
        c.fill(8, y + 2, 9, y + 3, SH)
        c.fill(5, y + 4, 6, y + 5, SH)


def draw_p2_arms_idle(c: SpriteCanvas, d: Dir, y_off: int = 0) -> None:
    y = 6 + y_off
    if d == "D":
        c.fill(3, y, 3, y + 3, MN)
        c.fill(12, y, 12, y + 3, MN)
    elif d == "L":
        c.fill(1, y, 2, y + 3, MN)
        c.fill(7, y + 1, 8, y + 3, MN)
    elif d == "R":
        c.fill(13, y, 14, y + 3, MN)
        c.fill(7, y + 1, 8, y + 3, MN)
    else:
        c.fill(3, y, 3, y + 2, MN)
        c.fill(12, y, 12, y + 2, MN)


def draw_p2_place_bomb(c: SpriteCanvas, d: Dir, phase: int) -> None:
    y_off = 1 if phase >= 1 else 0
    draw_p2_head(c, d, y_off)
    draw_p2_torso(c, d, y_off)
    if phase < 2:
        draw_p2_legs(c, d, 0, y_off)
    else:
        draw_p2_legs(c, d, 0, y_off + 1)
    if phase == 1:
        y = 7 + y_off
        if d == "D":
            c.fill(4, y, 5, y + 2, MN)
            c.fill(10, y, 11, y + 2, MN)
        elif d == "L":
            c.fill(0, y, 2, y + 2, MN)
        elif d == "R":
            c.fill(13, y, 15, y + 2, MN)
    elif phase == 2:
        c.fill(7, 13, 8, 14, DK)
        c.fill(7, 12, 8, 12, AC)


def draw_p2_carry(c: SpriteCanvas, d: Dir, step: int) -> None:
    draw_p2_head(c, d)
    draw_p2_torso(c, d)
    draw_p2_legs(c, d, step)
    c.fill(6, 0, 9, 1, DK)
    c.fill(7, 0, 8, 0, AC2)
    y = 5
    if d == "D":
        c.fill(3, y, 4, y + 2, MN)
        c.fill(11, y, 12, y + 2, MN)
        c.fill(4, y - 1, 5, y, MN)
        c.fill(10, y - 1, 11, y, MN)
    elif d == "L":
        c.fill(1, y, 3, y + 1, MN)
        c.fill(5, y - 2, 7, y, MN)
    elif d == "R":
        c.fill(12, y, 14, y + 1, MN)
        c.fill(8, y - 2, 10, y, MN)


def draw_p2_die(c: SpriteCanvas, phase: int) -> None:
    if phase < 3:
        draw_p2_head(c, "D", phase)
        draw_p2_torso(c, "D", phase)
        draw_p2_legs(c, "D", 0, phase)
        if phase >= 1:
            c.fill(6, 2, 9, 2, AC2)  # óculos caídos
    elif phase == 3:
        c.fill(3, 9, 12, 13, MN)
        c.fill(5, 7, 10, 10, SK)
    elif phase == 4:
        c.fill(2, 11, 13, 14, MN)
    else:
        for x, y in [(4, 5), (10, 4), (7, 8)]:
            c.fill(x, y, x + 1, y + 1, AC2)


def draw_p2_win(c: SpriteCanvas, phase: int) -> None:
    jump = {0: 0, 1: -2, 2: -1}[phase]
    draw_p2_head(c, "D", jump)
    draw_p2_torso(c, "D", jump)
    draw_p2_legs(c, "D", phase % 2, jump)
    if phase >= 1:
        c.fill(2, 3 + jump, 3, 6 + jump, MN)
        c.fill(12, 3 + jump, 13, 6 + jump, MN)
    if phase == 2:
        c.set(5, 0, EX)
        c.set(10, 0, EX)


def make_p2_frame(kind: str, d: Dir, sub: int) -> Frame:
    c = SpriteCanvas()
    if kind == "idle":
        draw_p2_head(c, d)
        draw_p2_torso(c, d)
        draw_p2_legs(c, d, 0)
        draw_p2_arms_idle(c, d)
    elif kind == "walk":
        draw_p2_head(c, d, sub % 2)
        draw_p2_torso(c, d, sub % 2)
        draw_p2_legs(c, d, sub)
        draw_p2_arms_idle(c, d, sub % 2)
    elif kind == "place":
        draw_p2_place_bomb(c, d, sub)
    elif kind == "carry":
        draw_p2_carry(c, d, sub)
    elif kind == "die":
        draw_p2_die(c, sub)
    elif kind == "win":
        draw_p2_win(c, sub)
    f = c.copy()
    f.name = f"p2_{kind}_{d}_{sub}"
    return f


# ---------------------------------------------------------------------------
# Inimigos abrasileirados
# ---------------------------------------------------------------------------

def draw_en_caipira(c: SpriteCanvas, d: Dir, step: int, dying: int = 0) -> None:
  if dying >= 2:
    c.fill(3, 10, 12, 14, AC2)
    c.fill(5, 8, 10, 10, SK)
    return
  if dying == 1:
    c.fill(4, 9, 11, 12, AC2)
    draw_en_caipira(c, d, 0)
    return
  y_off = step % 2
  # chapéu de palha
  c.fill(4, 0, 11, 2, MN)
  c.fill(5, 0, 10, 1, MH)
  y = 2 + y_off
  c.fill(5, y, 10, y + 3, SK)
  c.fill(4, y, 6, y + 1, HR)
  if d == "D":
    c.set(6, y + 2, DK)
    c.set(9, y + 2, DK)
  c.fill(5, y + 3, 10, y + 6, AC)  # camisa
  c.fill(4, y + 6, 11, y + 9, AC2)  # bermuda
  if step == 0:
    c.fill(5, y + 9, 6, y + 11, SH)
    c.fill(9, y + 9, 10, y + 11, SH)
  else:
    c.fill(4, y + 9, 5, y + 12, SH)
    c.fill(10, y + 8, 11, y + 11, SH)


def draw_en_carnaval(c: SpriteCanvas, d: Dir, step: int, dying: int = 0) -> None:
  if dying >= 2:
    c.fill(2, 10, 13, 14, EX)
    c.fill(5, 7, 10, 9, SK)
    return
  if dying == 1:
    c.fill(3, 9, 12, 12, MN)
    draw_en_carnaval(c, d, 0)
    return
  y = 1 + step % 2
  # cocar / penas
  c.set(3, y, AC)
  c.set(12, y, AC2)
  c.set(4, y - 1, EX)
  c.set(11, y - 1, MN)
  c.fill(5, y, 10, y + 3, SK)
  if d == "D":
    c.fill(6, y + 1, 9, y + 2, MN)  # máscara
    c.set(6, y + 2, DK)
    c.set(9, y + 2, DK)
  c.fill(4, y + 3, 11, y + 7, MN)
  c.fill(5, y + 4, 10, y + 6, AC)
  c.fill(3, y + 3, 4, y + 5, EX)
  c.fill(11, y + 3, 12, y + 5, AC2)
  if step == 0:
    c.fill(5, y + 7, 6, y + 11, AC2)
    c.fill(9, y + 7, 10, y + 11, AC2)
  else:
    c.fill(4, y + 7, 5, y + 12, AC2)
    c.fill(10, y + 6, 11, y + 11, AC2)


def draw_en_torcedor(c: SpriteCanvas, d: Dir, step: int, dying: int = 0) -> None:
  if dying >= 2:
    c.fill(3, 11, 12, 14, MN)
    c.fill(5, 9, 10, 11, SK)
    return
  if dying == 1:
    c.fill(4, 10, 11, 13, MN)
    draw_en_torcedor(c, d, 0)
    return
  y = 2 + step % 2
  c.fill(5, y, 10, y + 3, SK)
  c.fill(5, y, 10, y + 1, HR)
  if d == "D":
    c.set(6, y + 1, DK)
    c.set(9, y + 1, DK)
    c.fill(7, y + 2, 8, y + 2, DK)  # boca gritando
  c.fill(4, y + 3, 11, y + 7, MN)  # camisa verde
  c.fill(5, y + 3, 10, y + 4, MH)
  c.fill(4, y + 4, 5, y + 6, AC)  # amarelo lateral
  c.fill(10, y + 4, 11, y + 6, AC)
  c.fill(10, y + 3, 11, y + 4, EX)  # número
  c.fill(5, y + 7, 10, y + 9, AC2)  # shorts
  if step == 0:
    c.fill(5, y + 9, 6, y + 11, SH)
    c.fill(9, y + 9, 10, y + 11, SH)
  else:
    c.fill(4, y + 9, 5, y + 12, SH)
    c.fill(10, y + 8, 11, y + 11, SH)


def make_enemy_frame(en_id: int, kind: str, d: Dir, sub: int) -> Frame:
    c = SpriteCanvas()
    drawers = [draw_en_caipira, draw_en_carnaval, draw_en_torcedor]
    draw = drawers[en_id]
    prefix = ["caipira", "carnaval", "torcedor"][en_id]
    if kind == "idle":
        draw(c, d, 0)
    elif kind == "walk":
        draw(c, d, sub)
    elif kind == "die":
        draw(c, d, 0, sub)
    f = c.copy()
    f.name = f"en_{prefix}_{kind}_{d}_{sub}"
    return f


# ---------------------------------------------------------------------------
# Itens: bomba, explosão, power-ups, efeitos
# ---------------------------------------------------------------------------

def draw_bomb(c: SpriteCanvas, phase: int) -> None:
    pulse = phase % 3
    r = 5 + (pulse == 1)
    cx, cy = 8, 9
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r + 1:
                c.set(cx + dx, cy + dy, 1)
    c.fill(cx - 1, cy - 2, cx + 1, cy - 1, 2)
    if pulse >= 1:
        c.set(cx, cy - 3, 3)
        c.set(cx, cy - 4, 4)
    if pulse == 2:
        c.set(cx - 1, cy - 4, 5)
        c.set(cx + 1, cy - 4, 6)


def draw_explosion_part(c: SpriteCanvas, part: str, phase: int) -> None:
    """part: C H V L R U D"""
    colors = [5, 6, 7, 4, 3]
    col = colors[min(phase, 4)]
    cx, cy = 8, 8
    if part == "C":
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                if abs(dx) + abs(dy) <= 4 + phase:
                    c.set(cx + dx, cy + dy, col)
    elif part == "H":
        c.fill(2, 6, 13, 10, col)
        c.fill(0, 7, 15, 9, col - 1 if col > 1 else 1)
    elif part == "V":
        c.fill(6, 2, 9, 13, col)
        c.fill(7, 0, 8, 15, col - 1 if col > 1 else 1)
    elif part == "L":
        c.fill(2, 6, 8, 10, col)
        c.fill(0, 7, 6, 9, col)
    elif part == "R":
        c.fill(8, 6, 14, 10, col)
        c.fill(10, 7, 15, 9, col)
    elif part == "U":
        c.fill(6, 2, 9, 8, col)
        c.fill(7, 0, 8, 6, col)
    elif part == "D":
        c.fill(6, 8, 9, 14, col)
        c.fill(7, 10, 8, 15, col)


def draw_powerup(c: SpriteCanvas, kind: str, phase: int) -> None:
    glow = phase % 2
    cx, cy = 8, 8
    base = 9 + (glow * 0)  # index into PAL_ITEMS
    mapping = {
        "fire": (11, 5),
        "bomb": (1, 2),
        "speed": (12, 13),
        "glove": (14, 15),
        "invincible": (12, 13),
        "exit": (10, 15),
        "skull": (15, 11),
    }
    a, b = mapping[kind]
    c.fill(cx - 3, cy - 3, cx + 3, cy + 3, a)
    c.fill(cx - 2, cy - 2, cx + 2, cy + 2, b)
    if kind == "fire":
        c.fill(cx - 1, cy - 4, cx + 1, cy - 2, 5)
    elif kind == "bomb":
        c.set(cx, cy - 4, 3)
    elif kind == "speed":
        c.fill(cx + 1, cy - 2, cx + 3, cy, 13)
    elif kind == "glove":
        c.fill(cx - 3, cy, cx - 1, cy + 2, 15)
    elif kind == "invincible":
        c.fill(cx - 1, cy - 3, cx + 1, cy + 1, 15)
    elif kind == "exit":
        c.fill(cx - 2, cy - 1, cx + 2, cy + 2, 15)
        c.set(cx, cy - 2, 12)
    elif kind == "skull":
        c.set(cx - 1, cy - 1, 15)
        c.set(cx + 1, cy - 1, 15)
        c.fill(cx - 1, cy, cx + 1, cy + 1, 15)


def draw_smoke(c: SpriteCanvas, phase: int) -> None:
    cx, cy = 8, 8
    r = 2 + phase
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r:
                c.set(cx + dx, cy + dy, 7 + (phase % 2))


def draw_flame_fade(c: SpriteCanvas, phase: int) -> None:
    col = 5 - phase
    if col < 1:
        col = 1
    c.fill(5, 5, 10, 10, col)
    c.fill(6, 6, 9, 9, col + 1 if col < 6 else col)


def make_item_frame(kind: str, sub: int) -> Frame:
    c = SpriteCanvas()
    if kind == "bomb":
        draw_bomb(c, sub)
    elif kind.startswith("expl_"):
        part = kind.split("_")[1]
        draw_explosion_part(c, part, sub)
    elif kind.startswith("pow_"):
        pk = kind.split("_")[1]
        draw_powerup(c, pk, sub)
    elif kind == "smoke":
        draw_smoke(c, sub)
    elif kind == "flame_fade":
        draw_flame_fade(c, sub)
    f = c.copy()
    f.name = f"{kind}_{sub}"
    return f


# ---------------------------------------------------------------------------
# Geração de atlas e manifest
# ---------------------------------------------------------------------------

DIRS = ["D", "U", "L", "R"]


def build_player_frames(maker: Callable, prefix: str) -> List[Frame]:
    frames: List[Frame] = []
    for d in DIRS:
        frames.append(maker("idle", d, 0))
    for d in DIRS:
        for s in range(3):
            frames.append(maker("walk", d, s))
    for d in DIRS:
        for s in range(3):
            frames.append(maker("place", d, s))
    for d in DIRS:
        for s in range(3):
            frames.append(maker("carry", d, s))
    for s in range(6):
        frames.append(maker("die", "D", s))
    for s in range(3):
        frames.append(maker("win", "D", s))
    return frames


def build_enemy_frames(en_id: int) -> List[Frame]:
    prefix = ["caipira", "carnaval", "torcedor"][en_id]
    frames: List[Frame] = []
    for d in DIRS:
        frames.append(make_enemy_frame(en_id, "idle", d, 0))
    for d in DIRS:
        for s in range(2):
            frames.append(make_enemy_frame(en_id, "walk", d, s))
    for s in range(2):
        frames.append(make_enemy_frame(en_id, "die", "D", s))
    return frames


def build_item_frames() -> List[Frame]:
    frames: List[Frame] = []
    for s in range(3):
        frames.append(make_item_frame("bomb", s))
    for part in ["C", "H", "V", "L", "R", "U", "D"]:
        for s in range(3):
            frames.append(make_item_frame(f"expl_{part}", s))
    for pk in ["fire", "bomb", "speed", "glove", "invincible", "exit", "skull"]:
        for s in range(2):
            frames.append(make_item_frame(f"pow_{pk}", s))
    for s in range(4):
        frames.append(make_item_frame("smoke", s))
    for s in range(3):
        frames.append(make_item_frame("flame_fade", s))
    return frames


def frame_to_image(frame: Frame, palette: Palette) -> Image.Image:
    img = Image.new("P", (FRAME_W, FRAME_H), 0)
    pal_flat: List[int] = []
    for r, g, b in palette:
        pal_flat.extend([r, g, b])
    while len(pal_flat) < 256 * 3:
        pal_flat.extend([0, 0, 0])
    img.putpalette(pal_flat)
    px = img.load()
    for (x, y), c in frame.pixels.items():
        px[x, y] = c
    return img


def build_atlas(frames: List[Frame], palette: Palette, cols: int = ATLAS_COLS) -> Image.Image:
    rows = (len(frames) + cols - 1) // cols
    w = cols * FRAME_W
    h = rows * FRAME_H
    atlas = Image.new("P", (w, h), 0)
    pal_flat: List[int] = []
    for r, g, b in palette:
        pal_flat.extend([r, g, b])
    while len(pal_flat) < 256 * 3:
        pal_flat.extend([0, 0, 0])
    atlas.putpalette(pal_flat)
    for i, fr in enumerate(frames):
        tile = frame_to_image(fr, palette)
        col = i % cols
        row = i // cols
        atlas.paste(tile, (col * FRAME_W, row * FRAME_H))
    return atlas


def write_frames_inc(path: Path, frames: List[Frame], prefix: str) -> None:
    lines = [
        f"; Frames — {prefix}",
        f"!{prefix}_FRAME_COUNT = {len(frames)}",
        f"!{prefix}_TILES_PER_FRAME = 4",
        "",
    ]
    for i, fr in enumerate(frames):
        tile_base = i * 2  # 16x16 = 2 colunas de tiles 8x8
        safe = fr.name.replace(" ", "_")
        lines.append(f"!FR_{safe} = {tile_base}  ; frame {i}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_master_manifest(path: Path, sections: List[Tuple[str, List[Frame], int]]) -> None:
    lines = [
        "; Atlas mestre gfx/anim/anim.png",
        "; 16x16 sprites, 4 tiles 8x8 por frame",
        "",
    ]
    offset = 0
    for name, frames, _ in sections:
        lines.append(f"; --- {name} ({len(frames)} frames) ---")
        for i, fr in enumerate(frames):
            tile_base = (offset + i) * 2
            safe = fr.name.replace(" ", "_")
            lines.append(f"!FR_{safe} = {tile_base}")
        offset += len(frames)
        lines.append("")
    lines.append(f"!ANIM_FRAME_COUNT = {offset}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_preview_sheet(
    frames: List[Frame],
    palette: Palette,
    path: Path,
    labels: List[Tuple[str, int, int]],
) -> None:
    """labels: (nome, índice início, quantidade)"""
    row_h = FRAME_H + 12
    w = max(sum(n * FRAME_W for _, _, n in labels), FRAME_W)
    h = row_h * len(labels)
    img = Image.new("RGB", (w, h), (24, 24, 32))
    from PIL import ImageDraw, ImageFont

    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    for row, (label, start, count) in enumerate(labels):
        y = row * row_h + 10
        draw.text((2, row * row_h), label, fill=(200, 200, 210), font=font)
        for i in range(count):
            if start + i >= len(frames):
                break
            tile = frame_to_image(frames[start + i], palette).convert("RGB")
            img.paste(tile, (i * FRAME_W, y))
    img.save(path)


def player_preview_labels() -> List[Tuple[str, int, int]]:
    base = 0
    rows: List[Tuple[str, int, int]] = []
    rows.append(("idle D U L R", base, 4))
    base += 4
    for d in DIRS:
        rows.append((f"walk {d}", base, 3))
        base += 3
    for d in DIRS:
        rows.append((f"place bomb {d}", base, 3))
        base += 3
    for d in DIRS:
        rows.append((f"carry {d}", base, 3))
        base += 3
    rows.append(("die", base, 6))
    base += 6
    rows.append(("win", base, 3))
    return rows


def enemy_preview_labels() -> List[Tuple[str, int, int]]:
    rows: List[Tuple[str, int, int]] = [("idle D U L R", 0, 4)]
    base = 4
    for d in DIRS:
        rows.append((f"walk {d}", base, 2))
        base += 2
    rows.append(("die", base, 2))
    return rows


def write_readme(path: Path, sections: List[Tuple[str, List[Frame], int]]) -> None:
    total = sum(len(f) for _, f, _ in sections)
    lines = [
        "# Sprites e animações — Super Bomba",
        "",
        "Gerados por `tools/gen_chars.py`. **Não integrados ao game.asm.**",
        "",
        "## Personagens",
        "",
        "| Pasta | Descrição | Frames |",
        "|-------|-----------|--------|",
        "| `p1/` | Jogador 1 — terno executivo | 49 |",
        "| `p2/` | Jogador 2 — cientista (jaleco, óculos) | 49 |",
        "| `enemies/caipira/` | Inimigo caipira (chapéu, bermuda, chinelo) | 14 |",
        "| `enemies/carnaval/` | Inimigo carnaval (penas, máscara, cores) | 14 |",
        "| `enemies/torcedor/` | Inimigo torcedor (verde/amarelo) | 14 |",
        "",
        "## Animações por jogador",
        "",
        "- **idle** — 4 direções (D, U, L, R)",
        "- **walk** — 3 frames × 4 direções",
        "- **place** — colocar bomba, 3 fases × 4 direções",
        "- **carry** — carregar bomba, 3 frames × 4 direções",
        "- **die** — 6 frames",
        "- **win** — 3 frames (celebração)",
        "",
        "## Itens (`gfx/anim/`)",
        "",
        "- Bomba (3 frames pulsando)",
        "- Explosão — centro, horizontal, vertical, L/R/U/D (3 fases cada)",
        "- Power-ups — fogo, bomba, velocidade, luva, invencível, saída, caveira",
        "- Fumaça (4) e fade de chama (3)",
        "",
        f"**Total no atlas mestre:** {total} frames (16×16 px)",
        "",
        "## Paletas SNES",
        "",
        "Cada grupo usa 1 subpaleta (16 cores, índice 0 transparente).",
        "Converter com `superfamiconv` quando integrar ao jogo.",
        "",
        "## Regenerar",
        "",
        "```bash",
        "python3 tools/gen_chars.py",
        "```",
        "",
        "## Previews",
        "",
        "Cada pasta tem `preview.png` com as animações etiquetadas.",
        "Atlas mestre: `gfx/anim/anim.png` | itens: `gfx/anim/items_preview.png`.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    CHARS.mkdir(parents=True, exist_ok=True)
    ANIM.mkdir(parents=True, exist_ok=True)

    p1_frames = build_player_frames(make_p1_frame, "p1")
    p2_frames = build_player_frames(make_p2_frame, "p2")
    en0 = build_enemy_frames(0)
    en1 = build_enemy_frames(1)
    en2 = build_enemy_frames(2)
    items = build_item_frames()

    # Atlases individuais
    p1_dir = CHARS / "p1"
    p2_dir = CHARS / "p2"
    p1_dir.mkdir(exist_ok=True)
    p2_dir.mkdir(exist_ok=True)

    build_atlas(p1_frames, PAL_P1).save(p1_dir / "atlas.png")
    write_frames_inc(p1_dir / "frames.inc", p1_frames, "P1")
    write_preview_sheet(p1_frames, PAL_P1, p1_dir / "preview.png", player_preview_labels())

    build_atlas(p2_frames, PAL_P2).save(p2_dir / "atlas.png")
    write_frames_inc(p2_dir / "frames.inc", p2_frames, "P2")
    write_preview_sheet(p2_frames, PAL_P2, p2_dir / "preview.png", player_preview_labels())

    en_base = CHARS / "enemies"
    for name, frames, pal in [
        ("caipira", en0, PAL_EN_CAIPIRA),
        ("carnaval", en1, PAL_EN_CARNAVAL),
        ("torcedor", en2, PAL_EN_TORCEDOR),
    ]:
        d = en_base / name
        d.mkdir(parents=True, exist_ok=True)
        build_atlas(frames, pal).save(d / "atlas.png")
        write_frames_inc(d / "frames.inc", frames, f"EN_{name.upper()}")
        write_preview_sheet(frames, pal, d / "preview.png", enemy_preview_labels())

    build_atlas(items, PAL_ITEMS).save(ANIM / "items.png")
    write_frames_inc(ANIM / "items.inc", items, "ITEMS")
    item_labels = [
        ("bomb", 0, 3),
        ("explosion", 3, 21),
        ("powerups", 24, 14),
        ("smoke", 38, 4),
        ("flame fade", 42, 3),
    ]
    write_preview_sheet(items, PAL_ITEMS, ANIM / "items_preview.png", item_labels)

    sections: List[Tuple[str, List[Frame], int]] = [
        ("p1", p1_frames, 0),
        ("p2", p2_frames, 0),
        ("en_caipira", en0, 0),
        ("en_carnaval", en1, 0),
        ("en_torcedor", en2, 0),
        ("items", items, 0),
    ]
    all_frames: List[Frame] = []
    for _, frs, _ in sections:
        all_frames.extend(frs)

    master = Image.new(
        "RGB",
        (ATLAS_COLS * FRAME_W, ((len(all_frames) + ATLAS_COLS - 1) // ATLAS_COLS) * FRAME_H),
        (32, 32, 40),
    )
    for i, fr in enumerate(all_frames):
        if i < len(p1_frames):
            pal = PAL_P1
        elif i < len(p1_frames) + len(p2_frames):
            pal = PAL_P2
        elif i < len(p1_frames) + len(p2_frames) + len(en0):
            pal = PAL_EN_CAIPIRA
        elif i < len(p1_frames) + len(p2_frames) + len(en0) + len(en1):
            pal = PAL_EN_CARNAVAL
        elif i < len(p1_frames) + len(p2_frames) + len(en0) + len(en1) + len(en2):
            pal = PAL_EN_TORCEDOR
        else:
            pal = PAL_ITEMS
        tile = frame_to_image(fr, pal).convert("RGB")
        col = i % ATLAS_COLS
        row = i // ATLAS_COLS
        master.paste(tile, (col * FRAME_W, row * FRAME_H))
    master.save(ANIM / "anim.png")

    write_master_manifest(ANIM / "frames.inc", sections)
    write_readme(CHARS / "README.md", sections)

    print(f"p1 frames: {len(p1_frames)}")
    print(f"p2 frames: {len(p2_frames)}")
    print(f"enemies: {len(en0) + len(en1) + len(en2)}")
    print(f"items: {len(items)}")
    print(f"total: {len(all_frames)}")
    print(f"wrote {ANIM / 'anim.png'}")


if __name__ == "__main__":
    main()
