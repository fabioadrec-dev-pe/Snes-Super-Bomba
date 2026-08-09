;==============================================================================
; init.asm — inicialização da PPU e upload de gráficos (bank $01)
;==============================================================================
org $018000

init:
    PHP
    SEP #$20
    REP #$10

;-------------- forced blank
    LDA #$80
    STA $2100

;-------------- zera registradores PPU usados
    STZ $2101
    STZ $2102
    STZ $2103
    STZ $2105
    STZ $2106
    STZ $2107
    STZ $2108
    STZ $2109
    STZ $210A
    STZ $210B
    STZ $210C
    STZ $210D
    STZ $210D
    STZ $210E
    STZ $210E
    STZ $210F
    STZ $210F
    STZ $2110
    STZ $2110
    STZ $2111
    STZ $2111
    STZ $2112
    STZ $2112
    STZ $2113
    STZ $2113
    STZ $2114
    STZ $2114
    STZ $2123
    STZ $2124
    STZ $2125
    STZ $2126
    STZ $2127
    STZ $2128
    STZ $2129
    STZ $212A
    STZ $212B
    STZ $212C
    STZ $212D
    STZ $212E
    STZ $212F
    STZ $2130
    STZ $2131
    STZ $2132
    STZ $2133

    STZ $4200
    STZ $420B
    STZ $420C

;-------------- Mode 1
    LDA #$01
    STA $2105

;-------------- BG1 map $7000, tiles $0000
    LDA #$70
    STA $2107
    STZ $210B

;-------------- sprites base $4000, 8x8/16x16
    LDA #$02
    STA $2101

;-------------- zera CGRAM
    STZ $2121
    LDX #$0100
init_clear_cgram:
    STZ $2122
    STZ $2122
    DEX
    BNE init_clear_cgram

;-------------- zera VRAM
    LDA #$80
    STA $2115
    LDX #$0000
    STX $2116
    LDX #$4000
init_clear_vram:
    STZ $2118
    STZ $2119
    DEX
    BNE init_clear_vram

;-------------- zera OAM
    STZ $2102
    STZ $2103
    LDX #$0080
init_clear_oam:
    STZ $2104            ; X
    LDA #$E0
    STA $2104            ; Y
    STZ $2104            ; tile
    STZ $2104            ; attr
    DEX
    BNE init_clear_oam
    LDX #$0020
init_clear_oam_hi:
    STZ $2104
    DEX
    BNE init_clear_oam_hi

;-------------- zera WRAM do jogo
    LDX #$0000
init_clear_wram:
    STZ $00,X
    INX
    CPX #$0500
    BNE init_clear_wram

    JSR LoadGraphics

    PLP
    RTL


;==============================================================================
LoadGraphics:
    PHP
    SEP #$20
    REP #$10

; paleta título -> CGRAM $00
    STZ $2121
    LDA.b #TitlePal>>16
    STA $4304
    LDX.w #TitlePal
    STX $4302
    STZ $4300
    LDA #$22
    STA $4301
    LDX.w #$0020
    STX $4305
    LDA #$01
    STA $420B

; paleta fonte -> sprite pal 0 (CGRAM $80)
    LDA #$80
    STA $2121
    LDA.b #FontPal>>16
    STA $4304
    LDX.w #FontPal
    STX $4302
    STZ $4300
    LDA #$22
    STA $4301
    LDX.w #$0020
    STX $4305
    LDA #$01
    STA $420B

    JSR BuildSpriteColorPalettes

; título tiles -> VRAM $0000
    LDA #$80
    STA $2115
    LDX.w #$0000
    STX $2116
    LDA.b #TitleCHR>>16
    STA $4304
    LDX.w #TitleCHR
    STX $4302
    LDA #$01
    STA $4300
    LDA #$18
    STA $4301
    LDX.w #$2000
    STX $4305
    LDA #$01
    STA $420B

; fonte BG -> VRAM $2000 (tiles 256+)
    LDX.w #$2000
    STX $2116
    LDA.b #FontCHR>>16
    STA $4304
    LDX.w #FontCHR
    STX $4302
    LDA #$01
    STA $4300
    LDA #$18
    STA $4301
    LDX.w #$0A00
    STX $4305
    LDA #$01
    STA $420B

; fonte sprites -> VRAM $4000
    LDX.w #$4000
    STX $2116
    LDA.b #FontCHR>>16
    STA $4304
    LDX.w #FontCHR
    STX $4302
    LDA #$01
    STA $4300
    LDA #$18
    STA $4301
    LDX.w #$0A00
    STX $4305
    LDA #$01
    STA $420B

; tilemap título -> BG1 $7000
    LDX.w #$7000
    STX $2116
    LDA.b #TitleMAP>>16
    STA $4304
    LDX.w #TitleMAP
    STX $4302
    LDA #$01
    STA $4300
    LDA #$18
    STA $4301
    LDX.w #$0200
    STX $4305
    LDA #$01
    STA $420B

; limpa resto do map
    LDX.w #$7100
    STX $2116
    LDX.w #$0300
LoadGraphics_clear_map:
    STZ $2118
    STZ $2119
    DEX
    BNE LoadGraphics_clear_map

    PLP
    RTS


BuildSpriteColorPalettes:
    PHP
    SEP #$20

; branco na pal0 índice 1
    LDA #$81
    STA $2121
    LDA #$FF
    STA $2122
    LDA #$7F
    STA $2122

; pal1 vermelho
    LDA #$90
    STA $2121
    STZ $2122
    STZ $2122
    LDA #$1F
    STA $2122
    STZ $2122

; pal2 amarelo
    LDA #$A0
    STA $2121
    STZ $2122
    STZ $2122
    LDA #$FF
    STA $2122
    LDA #$03
    STA $2122

; pal3 verde
    LDA #$B0
    STA $2121
    STZ $2122
    STZ $2122
    LDA #$E0
    STA $2122
    LDA #$03
    STA $2122

    PLP
    RTS
