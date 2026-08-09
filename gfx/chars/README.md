# Sprites e animações — Super Bomba

Gerados por `tools/gen_chars.py`. **Não integrados ao game.asm.**

## Personagens

| Pasta | Descrição | Frames |
|-------|-----------|--------|
| `p1/` | Jogador 1 — terno executivo | 49 |
| `p2/` | Jogador 2 — cientista (jaleco, óculos) | 49 |
| `enemies/caipira/` | Inimigo caipira (chapéu, bermuda, chinelo) | 14 |
| `enemies/carnaval/` | Inimigo carnaval (penas, máscara, cores) | 14 |
| `enemies/torcedor/` | Inimigo torcedor (verde/amarelo) | 14 |

## Animações por jogador

- **idle** — 4 direções (D, U, L, R)
- **walk** — 3 frames × 4 direções
- **place** — colocar bomba, 3 fases × 4 direções
- **carry** — carregar bomba, 3 frames × 4 direções
- **die** — 6 frames
- **win** — 3 frames (celebração)

## Itens (`gfx/anim/`)

- Bomba (3 frames pulsando)
- Explosão — centro, horizontal, vertical, L/R/U/D (3 fases cada)
- Power-ups — fogo, bomba, velocidade, luva, invencível, saída, caveira
- Fumaça (4) e fade de chama (3)

**Total no atlas mestre:** 185 frames (16×16 px)

## Paletas SNES

Cada grupo usa 1 subpaleta (16 cores, índice 0 transparente).
Converter com `superfamiconv` quando integrar ao jogo.

## Regenerar

```bash
python3 tools/gen_chars.py
```

## Previews

Cada pasta tem `preview.png` com as animações etiquetadas.
Atlas mestre: `gfx/anim/anim.png` | itens: `gfx/anim/items_preview.png`.
