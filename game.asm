;==============================================================================
; game.asm — Super Bomba: reset, NMI, menu e tela de opções
;==============================================================================
; WRAM:
;   $00 = menu_sel (0..2)
;   $01 = joy_prev ($4218 normalizado)
;   $02 = joy_now  ($4218: UDLR, Start, B — 1=pressionado)
;   $14 = joy_now_hi (A em $02 bit7; reservado)
;   $15 = joy_prev_hi
;   $03 = nmi_flag
;   $04 = joy_pressed (borda $4218)
;   $16 = joy_pressed_hi (borda A)
;   $05 = draw option / temp
;   $06 = draw Y
;   $07 = draw X
;   $08 = oam offset
;   $09 = sprite attr
;   $0A = tile temp
;   $0B,$0C = temp
;   $0E = screen (0=menu, 1=opções, 2=fase intro)
;   $17 = fase_intro_frame (contador de frames)
;   $0F = opt_row (0=vidas, 1=dificuldade, 2=sair)
;   $10 = lives_idx (0=10, 1=50, 2=100)
;   $11 = diff_idx  (0=fácil, 1=normal, 2=difícil)
;   $12 = joy_prev B/Start ($4218 normalizado)
;   $13 = joy_now B/Start
;   $18 = borda B/Start
;   $0200..$041F = OAM mirror
;==============================================================================

org $008000

irq:
    RTI

nmi:
    PHP
    REP #$30
    PHA
    PHX
    PHY

    SEP #$20
    REP #$10

; DMA OAM $7E0200 -> $2104
    STZ $2102
    STZ $2103
    STZ $4300
    LDA #$04
    STA $4301
    LDX.w #$0200
    STX $4302
    LDA #$7E
    STA $4304
    LDX.w #$0220
    STX $4305
    LDA #$01
    STA $420B

    LDA $0E
    CMP #$02
    BEQ nmi_phase_colors
    JSR ApplySelectionColors
    BRA nmi_colors_done
nmi_phase_colors:
    JSR ApplyPhaseIntroColors
nmi_colors_done:

wait_joy:
    LDA $4212
    LSR A
    BCS wait_joy

; Canal 1 — Mesen / Programador Hobbista: eixos e A em $4219
    LDA $4219
    STA $02

; B e Start em $4218 (active-low do hardware)
    LDA $4218
    EOR #$FF
    AND #$90
    STA $13

    LDA #$01
    STA $03

    REP #$30
    PLY
    PLX
    PLA
    PLP
    RTI


reset:
    SEI
    CLC
    XCE
    REP #$30
    LDX #$1FFF
    TXS
    LDA #$0000
    TCD

    SEP #$20
    LDA #$00
    PHA
    PLB

    JSL init

    STZ $00
    STZ $01
    STZ $12
    STZ $02
    STZ $13
    STZ $03
    STZ $0E
    STZ $0F

; padrões: 50 vidas, dificuldade normal
    LDA #$01
    STA $10
    STA $11

    JSR SetupMenuScreen

    CLI
    LDA #$81
    STA $4200

MainLoop:
    LDA $03
    BEQ MainLoop
    STZ $03

    LDA $0E
    BEQ MainLoop_menu
    CMP #$01
    BEQ MainLoop_options
    JSR UpdatePhaseIntro
    BRA MainLoop

MainLoop_menu:
    JSR UpdateMenu
    BRA MainLoop

MainLoop_options:
    JSR UpdateOptions
    BRA MainLoop


;==============================================================================
SetupMenuScreen:
    PHP
    SEP #$20

    STZ $00
    STZ $0E
    JSR BuildMenuOAM
    JSR ApplySelectionColors

    LDA #$11
    STA $212C

    LDA #$0F
    STA $2100

    PLP
    RTS


;==============================================================================
SetupOptionsScreen:
    PHP
    SEP #$20

    LDA #$01
    STA $0E
    STZ $0F
    JSR BuildOptionsOAM

    PLP
    RTS


;==============================================================================
SetupPhaseIntro:
    PHP
    SEP #$20

    LDA #$02
    STA $0E
    STZ $17

; fundo amarelo (CGRAM color 0 = $7FE0)
    STZ $2121
    LDA #$E0
    STA $2122
    LDA #$7F
    STA $2122

; texto legível: preto na pal0 índice 1
    LDA #$81
    STA $2121
    STZ $2122
    STZ $2122

    JSR BuildPhaseIntroOAM

; só sprites (sem tilemap do título)
    LDA #$10
    STA $212C

    LDA #$0F
    STA $2100

    PLP
    RTS


BuildPhaseIntroOAM:
    PHP
    SEP #$20
    JSR ClearOAM

    LDA #112
    STA $06
    LDA #104
    STA $07
    LDA #$20
    STA $09
    LDX.w #StrFase1
    JSR DrawString

    PLP
    RTS


UpdatePhaseIntro:
    PHP
    SEP #$20

    INC $17
    LDA $17
    CMP #240
    BCC UpdatePhaseIntro_done
    JSR ClearOAM

UpdatePhaseIntro_done:
    PLP
    RTS


;==============================================================================
ReadJoyPressed:
    PHP
    SEP #$20
; $4219: borda com AND $02 (formato Mesen / tutorial)
    LDA $02
    EOR $01
    AND $02
    STA $04
    LDA $02
    STA $01

; $4218: borda B / Start
    LDA $13
    EOR $12
    AND $13
    STA $18
    LDA $13
    STA $12

    STZ $16
    PLP
    RTS


;==============================================================================
UpdateMenu:
    PHP
    SEP #$20
    JSR ReadJoyPressed

    LDA $04
    BIT #$08
    BEQ UpdateMenu_check_down
    LDA $00
    BNE UpdateMenu_dec
    LDA #$02
    STA $00
    BRA UpdateMenu_rebuild
UpdateMenu_dec:
    DEC $00
    BRA UpdateMenu_rebuild

UpdateMenu_check_down:
    LDA $04
    BIT #$04
    BEQ UpdateMenu_check_confirm
    LDA $00
    CMP #$02
    BCC UpdateMenu_inc
    STZ $00
    BRA UpdateMenu_rebuild
UpdateMenu_inc:
    INC $00

UpdateMenu_rebuild:
    JSR BuildMenuOAM

UpdateMenu_check_confirm:
; A (bit7 de $4219)
    LDA $04
    BIT #$80
    BEQ UpdateMenu_done
    LDA $00
    BEQ UpdateMenu_start_1p
    CMP #$02
    BNE UpdateMenu_done
    JSR SetupOptionsScreen
    BRA UpdateMenu_done

UpdateMenu_start_1p:
    JSR SetupPhaseIntro

UpdateMenu_done:
    PLP
    RTS


;==============================================================================
UpdateOptions:
    PHP
    SEP #$20
    JSR ReadJoyPressed

; B = voltar (vem de $4218, não confundir com A)
    LDA $18
    BIT #$80
    BEQ UpdateOptions_no_back
    JSR ExitOptions
    PLP
    RTS

UpdateOptions_no_back:
    LDA $04
    BIT #$08
    BEQ UpdateOptions_check_down
    LDA $0F
    BNE UpdateOptions_up_dec
    LDA #$02
    STA $0F
    BRA UpdateOptions_rebuild
UpdateOptions_up_dec:
    DEC $0F
    BRA UpdateOptions_rebuild

UpdateOptions_check_down:
    LDA $04
    BIT #$04
    BEQ UpdateOptions_check_lr
    LDA $0F
    CMP #$02
    BCC UpdateOptions_down_inc
    STZ $0F
    BRA UpdateOptions_rebuild
UpdateOptions_down_inc:
    INC $0F

UpdateOptions_rebuild:
    JSR BuildOptionsOAM
    BRA UpdateOptions_check_confirm

UpdateOptions_check_lr:
    LDA $0F
    CMP #$02
    BEQ UpdateOptions_check_confirm

    LDA $04
    BIT #$02
    BNE UpdateOptions_left
    LDA $04
    BIT #$01
    BEQ UpdateOptions_check_confirm

; direita
    LDA $0F
    BEQ UpdateOptions_life_right
    JSR OptCycleDiffRight
    BRA UpdateOptions_rebuild

UpdateOptions_left:
    LDA $0F
    BEQ UpdateOptions_life_left
    JSR OptCycleDiffLeft
    BRA UpdateOptions_rebuild

UpdateOptions_life_right:
    JSR OptCycleLifeRight
    BRA UpdateOptions_rebuild

UpdateOptions_life_left:
    JSR OptCycleLifeLeft
    BRA UpdateOptions_rebuild

UpdateOptions_check_confirm:
; A na linha SAIR ($4219 bit7)
    LDA $04
    BIT #$80
    BEQ UpdateOptions_done
    LDA $0F
    CMP #$02
    BNE UpdateOptions_done
    JSR ExitOptions

UpdateOptions_done:
    PLP
    RTS


ExitOptions:
    STZ $0E
    LDA #$02
    STA $00
    JSR BuildMenuOAM
    RTS


;==============================================================================
; Valida $10 conforme dificuldade em $11
;==============================================================================
ValidateLife:
    PHP
    SEP #$20
    LDA $11
    CMP #$02
    BEQ ValidateLife_hard
    CMP #$01
    BEQ ValidateLife_normal
    PLP
    RTS

ValidateLife_normal:
    LDA $10
    CMP #$02
    BCC ValidateLife_done
    LDA #$01
    STA $10
ValidateLife_done:
    PLP
    RTS

ValidateLife_hard:
    STZ $10
    PLP
    RTS


; A = índice de vida; CLC=válido SEC=inválido (não usar PHP — chamada aninhada)
LifeIdxValid:
    CMP #$00
    BEQ LifeIdxValid_ok
    CMP #$01
    BNE LifeIdxValid_is100
    LDA $11
    CMP #$02
    BEQ LifeIdxValid_bad
    BRA LifeIdxValid_ok

LifeIdxValid_is100:
    LDA $11
    BEQ LifeIdxValid_ok
LifeIdxValid_bad:
    SEC
    RTS

LifeIdxValid_ok:
    CLC
    RTS


OptCycleLifeRight:
    PHP
    SEP #$20
    LDA $10
    STA $0C
OptCycleLifeRight_loop:
    INC A
    CMP #$03
    BCC OptCycleLifeRight_chk
    LDA #$00
OptCycleLifeRight_chk:
    PHA
    JSR LifeIdxValid
    PLA
    BCC OptCycleLifeRight_store
    CMP $0C
    BEQ OptCycleLifeRight_store
    BRA OptCycleLifeRight_loop
OptCycleLifeRight_store:
    STA $10
    PLP
    RTS


OptCycleLifeLeft:
    PHP
    SEP #$20
    LDA $10
    STA $0C
OptCycleLifeLeft_loop:
    DEC A
    CMP #$FF
    BNE OptCycleLifeLeft_chk
    LDA #$02
OptCycleLifeLeft_chk:
    PHA
    JSR LifeIdxValid
    PLA
    BCC OptCycleLifeLeft_store
    CMP $0C
    BEQ OptCycleLifeLeft_store
    BRA OptCycleLifeLeft_loop
OptCycleLifeLeft_store:
    STA $10
    PLP
    RTS


OptCycleDiffRight:
    PHP
    SEP #$20
    LDA $11
    INC A
    CMP #$03
    BCC OptCycleDiffRight_wrap
    LDA #$00
OptCycleDiffRight_wrap:
    STA $11
    JSR ValidateLife
    PLP
    RTS


OptCycleDiffLeft:
    PHP
    SEP #$20
    LDA $11
    BEQ OptCycleDiffLeft_wrap
    DEC A
    BRA OptCycleDiffLeft_store
OptCycleDiffLeft_wrap:
    LDA #$02
OptCycleDiffLeft_store:
    STA $11
    JSR ValidateLife
    PLP
    RTS


;==============================================================================
ApplySelectionColors:
    PHP
    SEP #$20

    STZ $2121
    LDA #$08
    STA $2122
    LDA #$04
    STA $2122

    LDA #$91
    STA $2121
    LDA #$1F
    STA $2122
    STZ $2122

    LDA #$A1
    STA $2121
    LDA #$FF
    STA $2122
    LDA #$03
    STA $2122

    LDA #$B1
    STA $2121
    LDA #$E0
    STA $2122
    LDA #$03
    STA $2122

    LDA #$81
    STA $2121
    LDA #$FF
    STA $2122
    LDA #$7F
    STA $2122

; pal4 cinza (opções indisponíveis)
    LDA #$C1
    STA $2121
    LDA #$10
    STA $2122
    LDA #$42
    STA $2122

    PLP
    RTS


ApplyPhaseIntroColors:
    PHP
    SEP #$20

; mantém fundo amarelo
    STZ $2121
    LDA #$E0
    STA $2122
    LDA #$7F
    STA $2122

; texto: preto ou em fade (pal0 índice 1)
    LDA #$81
    STA $2121
    LDA $17
    CMP #180
    BCC ApplyPhaseIntro_black
    CMP #240
    BCS ApplyPhaseIntro_yellow
    SEC
    SBC #180
    LSR A
    LSR A
    TAX
    LDA PhaseFadeLow,X
    STA $2122
    LDA PhaseFadeHigh,X
    STA $2122
    PLP
    RTS

ApplyPhaseIntro_black:
    STZ $2122
    STZ $2122
    PLP
    RTS

ApplyPhaseIntro_yellow:
    LDA #$E0
    STA $2122
    LDA #$7F
    STA $2122
    PLP
    RTS


PhaseFadeLow:
    db $00,$10,$20,$30,$40,$50,$60,$70,$80,$90,$A0,$B0,$C0,$D0,$E0
PhaseFadeHigh:
    db $00,$08,$10,$18,$20,$28,$30,$38,$40,$48,$50,$58,$60,$68,$70,$7F


;==============================================================================
ClearOAM:
    PHP
    SEP #$20
    REP #$10
    LDX.w #$0000
ClearOAM_hide:
    STZ $0200,X
    LDA #$E0
    STA $0201,X
    STZ $0202,X
    STZ $0203,X
    INX
    INX
    INX
    INX
    CPX.w #$0200
    BCC ClearOAM_hide
    LDX.w #$0000
ClearOAM_hide_hi:
    STZ $0400,X
    INX
    CPX.w #$0020
    BCC ClearOAM_hide_hi
    STZ $08
    PLP
    RTS


;==============================================================================
; Desenha string em X (ponteiro), attr em $09
;==============================================================================
DrawString:
    PHP
    SEP #$20
    REP #$10

DrawString_loop:
    LDA $0000,X
    CMP #$FF
    BEQ DrawString_done
    STA $0A

    PHX
    LDA $08
    TAX
    LDA $07
    STA $0200,X
    LDA $06
    STA $0201,X
    LDA $0A
    STA $0202,X
    LDA $09
    STA $0203,X
    PLX

    LDA $07
    CLC
    ADC #$08
    STA $07
    LDA $08
    CLC
    ADC #$04
    STA $08
    INX
    BRA DrawString_loop

DrawString_done:
    PLP
    RTS


;==============================================================================
BuildMenuOAM:
    PHP
    SEP #$20
    JSR ClearOAM

    LDA #$00
    STA $05
    LDA #120
    STA $06
    LDA #88
    STA $07
    LDX.w #Str1P
    JSR DrawMenuString

    LDA #$01
    STA $05
    LDA #144
    STA $06
    LDA #80
    STA $07
    LDX.w #Str2P
    JSR DrawMenuString

    LDA #$02
    STA $05
    LDA #168
    STA $06
    LDA #104
    STA $07
    LDX.w #StrOpt
    JSR DrawMenuString

    JSR DrawMainCursor

    PLP
    RTS


DrawMenuString:
    PHP
    SEP #$20
    LDA $05
    ASL A
    ASL A
    ASL A
    ASL A
    ASL A
    ASL A
    STA $08
    LDA #$20
    STA $09
    LDA $05
    CMP $00
    BNE DrawMenuString_go
    LDA $05
    INC A
    ASL A
    AND #$0E
    ORA #$20
    STA $09
DrawMenuString_go:
    JSR DrawString
    PLP
    RTS


DrawMainCursor:
    PHP
    SEP #$20
    LDA #64
    STA $02F0
    LDA $00
    STA $0B
    ASL A
    ASL A
    ASL A
    STA $0C
    LDA $0B
    ASL A
    ASL A
    ASL A
    ASL A
    CLC
    ADC $0C
    CLC
    ADC #120
    STA $02F1
    LDA #30
    STA $02F2
    LDA $00
    INC A
    ASL A
    AND #$0E
    ORA #$20
    STA $02F3
    PLP
    RTS


;==============================================================================
BuildOptionsOAM:
    PHP
    SEP #$20
    JSR ClearOAM

;--- linha 0: VIDAS  10  50  100
    LDA #120
    STA $06
    LDA #64
    STA $07
    LDA $0F
    BNE BuildOptionsOAM_l0_idle
    LDA #$22
    BRA BuildOptionsOAM_l0_attr
BuildOptionsOAM_l0_idle:
    LDA #$20
BuildOptionsOAM_l0_attr:
    STA $09
    LDX.w #StrVidas
    JSR DrawString

    LDA #120
    STA $06
    LDA #120
    STA $07
    LDA #$00
    JSR GetLifeAttr
    LDX.w #Str10
    JSR DrawString

    LDA #120
    STA $06
    LDA #152
    STA $07
    LDA #$01
    JSR GetLifeAttr
    LDX.w #Str50
    JSR DrawString

    LDA #120
    STA $06
    LDA #184
    STA $07
    LDA #$02
    JSR GetLifeAttr
    LDX.w #Str100
    JSR DrawString

;--- linha 1: NÍVEL:  FÁCIL  NORMAL  DIFÍCIL
    LDA #144
    STA $06
    LDA #40
    STA $07
    LDA $0F
    CMP #$01
    BNE BuildOptionsOAM_l1_idle
    LDA #$24
    BRA BuildOptionsOAM_l1_attr
BuildOptionsOAM_l1_idle:
    LDA #$20
BuildOptionsOAM_l1_attr:
    STA $09
    LDX.w #StrNivel
    JSR DrawString

    LDA #144
    STA $06
    LDA #96
    STA $07
    LDA #$00
    JSR GetDiffAttr
    LDX.w #StrFacil
    JSR DrawString

    LDA #144
    STA $06
    LDA #144
    STA $07
    LDA #$01
    JSR GetDiffAttr
    LDX.w #StrNormal
    JSR DrawString

    LDA #144
    STA $06
    LDA #200
    STA $07
    LDA #$02
    JSR GetDiffAttr
    LDX.w #StrDificil
    JSR DrawString

;--- linha 2: SAIR
    LDA #168
    STA $06
    LDA #112
    STA $07
    LDA $0F
    CMP #$02
    BNE BuildOptionsOAM_l2_idle
    LDA #$26
    BRA BuildOptionsOAM_l2_attr
BuildOptionsOAM_l2_idle:
    LDA #$20
BuildOptionsOAM_l2_attr:
    STA $09
    LDX.w #StrSair
    JSR DrawString

    JSR DrawOptionsCursor

    PLP
    RTS


; A = índice de vida (0..2); define $09
GetLifeAttr:
    PHP
    SEP #$20
    STA $0A
    LDA $0A
    JSR LifeIdxValid
    BCS GetLifeAttr_gray
    LDA $0A
    CMP $10
    BNE GetLifeAttr_idle
    LDA #$22
    STA $09
    PLP
    RTS
GetLifeAttr_idle:
    LDA #$20
    STA $09
    PLP
    RTS
GetLifeAttr_gray:
    LDA #$28
    STA $09
    PLP
    RTS


; A = índice de dificuldade (0..2); define $09
GetDiffAttr:
    PHP
    SEP #$20
    STA $0A
    LDA $0A
    CMP $11
    BNE GetDiffAttr_idle
    LDA #$24
    STA $09
    PLP
    RTS
GetDiffAttr_idle:
    LDA #$20
    STA $09
    PLP
    RTS


DrawOptionsCursor:
    PHP
    SEP #$20
    LDA #48
    STA $02F0
    LDA $0F
    STA $0B
    ASL A
    ASL A
    ASL A
    STA $0C
    LDA $0B
    ASL A
    ASL A
    ASL A
    ASL A
    CLC
    ADC $0C
    CLC
    ADC #120
    STA $02F1
    LDA #30
    STA $02F2
    LDA $0F
    INC A
    ASL A
    AND #$0E
    ORA #$20
    STA $02F3
    PLP
    RTS


StrFase1:
    db 38,33,51,37,0,17
    db $FF

;--- Menu principal ---
Str1P:
    db 17,0,42,47,39,33,36,47,50
    db $FF
Str2P:
    db 18,0,42,47,39,33,36,47,50,37,51
    db $FF
StrOpt:
    db 47,48,64,65,37,51
    db $FF

;--- Opções ---
; "VIDAS"
StrVidas:
    db 54,41,36,33,51
    db $FF
; "NÍVEL:"
StrNivel:
    db 46,68,54,37,44,26
    db $FF
Str10:
    db 17,16
    db $FF
Str50:
    db 21,16
    db $FF
Str100:
    db 17,16,16
    db $FF
StrFacil:
    db 38,66,35,41,44
    db $FF
StrNormal:
    db 46,47,50,45,33,44
    db $FF
StrDificil:
    db 36,41,38,68,35,41,44
    db $FF
StrSair:
    db 51,33,41,50
    db $FF


;==============================================================================
; Gráficos
;==============================================================================
org $00B000
TitleCHR:
    incbin gfx/title.chr

org $00D000
FontCHR:
    incbin gfx/font.chr

org $00DA00
TitleMAP:
    incbin gfx/title.map

TitlePal:
    incbin gfx/title.pal

FontPal:
    incbin gfx/font.pal

incsrc fontmap.asm
