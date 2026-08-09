# Super Bomba

Clone simplificado de Super Bomberman para SNES, no estilo das aulas do
[Programador Hobbista](https://www.youtube.com/@ProgramadorHobbista).

## Aula atual — Menu principal

Nesta etapa o jogo mostra o **menu**:

- Título bitmap rochoso **SUPER BOMBA** (BG1, tiles 4bpp)
- Fonte do jogo montada em **tiles de BG** (`VRAM $2000`) e **sprites** (`VRAM $4000`)
- Opções com sprites da fonte:
  1. `1 JOGADOR` → seleção **vermelha**
  2. `2 JOGADORES` → seleção **amarela**
  3. `OPÇÕES` → seleção **verde**

Controles (controle 1):

**Menu principal**
- Cima / Baixo — mudar opção
- **A** em OPÇÕES — abrir configurações

**Tela de Opções**
- Cima / Baixo — mudar seção (Vidas / Dificuldade / Sair)
- Esquerda / Direita — mudar valor
- **A** em Sair — voltar ao menu
- **B** — voltar ao menu

Por enquanto, selecionar cada opção só muda a cor do texto/cursor
(vermelho, amarelo, verde). Ainda não entra no jogo.

### Tela de Opções

```
> VIDAS   10   50   100
> NÍVEL:  FÁCIL  NORMAL  DIFÍCIL
> SAIR
```

Padrões: **50** vidas, nível **NORMAL**.

| Seção | Controles | Valores |
|-------|-----------|---------|
| **Vidas** | ← → | 10, 50, 100 |
| **Dificuldade** | ← → | Fácil, Normal, Difícil |
| **Sair** | A / Start / B | Volta ao menu |

**Padrões:** 50 vidas, dificuldade Normal.

**Restrições de vidas por dificuldade:**

| Dificuldade | Vidas disponíveis |
|-------------|-------------------|
| Fácil | 10, 50, 100 |
| Normal | 10, 50 |
| Difícil | 10 |

Valores indisponíveis aparecem em cinza. Ao mudar a dificuldade, a vida
é ajustada automaticamente se necessário.

## Build (Linux)

```bash
unzip modelo.zip
./make.sh
```

Gera `jogo.smc`. Abra no **Mesen**.

Dependências: `xkas`, `python3` + Pillow, `superfamiconv`.

## Arquivos

| Arquivo | Função |
|---------|--------|
| `main.asm` | Entrada / includes |
| `header.asm` | Header LoROM + vetores |
| `init.asm` | Init PPU, DMA de gráficos |
| `game.asm` | Reset, NMI, lógica do menu |
| `fontmap.asm` | Mapa caractere → tile |
| `gfx/` | PNG, `.chr`, `.map`, `.pal` |
| `tools/gen_gfx.py` | Gera título e fonte |

## Layout de VRAM

```
$0000  tiles do título (BG1)
$2000  tiles da fonte (BG, para uso futuro / HUD)
$4000  tiles da fonte (sprites do menu)
$7000  tilemap BG1
```
