#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "[1/3] Gerando gráficos..."
python3 tools/gen_gfx.py

echo "[2/3] Convertendo para SNES (superfamiconv)..."
superfamiconv palette -i gfx/title.png -d gfx/title.pal -M snes -P 1 -C 16 --color-zero '#0c0a12'
superfamiconv tiles   -i gfx/title.png -p gfx/title.pal -d gfx/title.chr -M snes -B 4 -D -F
superfamiconv map     -i gfx/title.png -p gfx/title.pal -t gfx/title.chr -d gfx/title.map -M snes -B 4 -F --map-width 32 --map-height 8

# -R: mantém índice 0 = transparente (sem remapear cores)
superfamiconv palette -i gfx/font.png -d gfx/font.pal -M snes -P 1 -C 16 -S -R --color-zero '#000000'
superfamiconv tiles   -i gfx/font.png -p gfx/font.pal -d gfx/font.chr -M snes -B 4 -D -F -S -R

echo "[3/3] Montando ROM (xkas)..."
cp modelo.smc jogo.smc
xkas main.asm jogo.smc

echo "ROM gerada: jogo.smc"
