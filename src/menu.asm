;==============================================================================
; src/menu.asm — menus principal e opções
;==============================================================================
; WRAM (compartilhada):
;   $00 cursor  $01/$02 joy  $03 nmi_flag  $04 pressed
;   $0B menu_mode  $0C lives  $0D diff
;   $0E/$0F/$10 joy low
;   $0200 OAM mirror
;==============================================================================

SetupMenuScreen:
    PHP
    SEP #$20

    STZ $00
    JSR RebuildCurrentMenu
    JSR ApplySelectionColors

    LDA #$11
    STA $212C
    LDA #$0F
    STA $2100

    PLP
    RTS


RebuildCurrentMenu:
    LDA $0B
    BNE RebuildCurrentMenu_opt
    JMP BuildMainMenuOAM
RebuildCurrentMenu_opt:
    JMP BuildOptionsMenuOAM


;==============================================================================
UpdateMenu:
    PHP
    SEP #$20

; edge detect high + low
    LDA $02
    EOR $01
    AND $02
    STA $04
    LDA $02
    STA $01

    LDA $0E
    EOR $0F
    AND $0E
    STA $10
    LDA $0E
    STA $0F

    LDA $0B
    BNE UpdateMenu_options
    JSR UpdateMainMenu
    BRA UpdateMenu_done
UpdateMenu_options:
    JSR UpdateOptionsMenu
UpdateMenu_done:
    PLP
    RTS


;------------------------------------------------------------------------------
UpdateMainMenu:
    LDA $04
    BIT #$08
    BEQ UpdateMainMenu_down
    LDA $00
    BNE UpdateMainMenu_dec
    LDA #$02
    STA $00
    BRA UpdateMainMenu_redraw
UpdateMainMenu_dec:
    DEC $00
    BRA UpdateMainMenu_redraw

UpdateMainMenu_down:
    LDA $04
    BIT #$04
    BEQ UpdateMainMenu_confirm
    LDA $00
    CMP #$02
    BCC UpdateMainMenu_inc
    STZ $00
    BRA UpdateMainMenu_redraw
UpdateMainMenu_inc:
    INC $00
    BRA UpdateMainMenu_redraw

UpdateMainMenu_confirm:
; A ou Start abre Opções
    LDA $10
    BIT #$80
    BNE UpdateMainMenu_do_confirm
    LDA $04
    BIT #$10
    BEQ UpdateMainMenu_end
UpdateMainMenu_do_confirm:
    LDA $00
    CMP #$02
    BNE UpdateMainMenu_end
    LDA #$01
    STA $0B
    STZ $00
    JSR RebuildCurrentMenu
UpdateMainMenu_end:
    RTS

UpdateMainMenu_redraw:
    JSR BuildMainMenuOAM
    RTS


;------------------------------------------------------------------------------
UpdateOptionsMenu:
; B volta ao principal
    LDA $04
    BIT #$80
    BEQ UpdateOptionsMenu_up
    JMP ExitOptionsMenu

UpdateOptionsMenu_up:
    LDA $04
    BIT #$08
    BEQ UpdateOptionsMenu_down
    LDA $00
    BNE UpdateOptionsMenu_dec
    LDA #$02
    STA $00
    BRA UpdateOptionsMenu_redraw
UpdateOptionsMenu_dec:
    DEC $00
    BRA UpdateOptionsMenu_redraw

UpdateOptionsMenu_down:
    LDA $04
    BIT #$04
    BEQ UpdateOptionsMenu_left
    LDA $00
    CMP #$02
    BCC UpdateOptionsMenu_inc
    STZ $00
    BRA UpdateOptionsMenu_redraw
UpdateOptionsMenu_inc:
    INC $00
    BRA UpdateOptionsMenu_redraw

UpdateOptionsMenu_left:
    LDA $04
    BIT #$02
    BEQ UpdateOptionsMenu_right
    JSR OptionsChangeLeft
    BRA UpdateOptionsMenu_redraw

UpdateOptionsMenu_right:
    LDA $04
    BIT #$01
    BEQ UpdateOptionsMenu_confirm
    JSR OptionsChangeRight
    BRA UpdateOptionsMenu_redraw

UpdateOptionsMenu_confirm:
    LDA $10
    BIT #$80
    BNE UpdateOptionsMenu_do_confirm
    LDA $04
    BIT #$10
    BEQ UpdateOptionsMenu_end
UpdateOptionsMenu_do_confirm:
    LDA $00
    CMP #$02
    BNE UpdateOptionsMenu_end
    JMP ExitOptionsMenu

UpdateOptionsMenu_redraw:
    JSR BuildOptionsMenuOAM
UpdateOptionsMenu_end:
    RTS


ExitOptionsMenu:
    STZ $0B
    STZ $00
    JSR BuildMainMenuOAM
    RTS


;------------------------------------------------------------------------------
; Esquerda/direita na linha atual
OptionsChangeLeft:
    LDA $00
    BEQ OptionsChangeLeft_lives
    CMP #$01
    BEQ OptionsChangeLeft_diff
    RTS

OptionsChangeLeft_lives:
    LDA $0D
    CMP #$02
    BEQ OptionsChangeLeft_rts       ; difícil: só 10
    CMP #$01
    BEQ OptionsChangeLeft_lives_n
; fácil: 0<-1<-2<-0
    LDA $0C
    BNE OptionsChangeLeft_lives_dec
    LDA #$02
    STA $0C
    RTS
OptionsChangeLeft_lives_dec:
    DEC $0C
OptionsChangeLeft_rts:
    RTS

OptionsChangeLeft_lives_n:
; normal: 0<->1
    LDA $0C
    EOR #$01
    STA $0C
    RTS

OptionsChangeLeft_diff:
    LDA $0D
    BNE OptionsChangeLeft_diff_dec
    LDA #$02
    STA $0D
    JSR ClampLivesToDiff
    RTS
OptionsChangeLeft_diff_dec:
    DEC $0D
    JSR ClampLivesToDiff
    RTS


OptionsChangeRight:
    LDA $00
    BEQ OptionsChangeRight_lives
    CMP #$01
    BEQ OptionsChangeRight_diff
    RTS

OptionsChangeRight_lives:
    LDA $0D
    CMP #$02
    BEQ OptionsChangeRight_rts      ; difícil: travado em 10
    CMP #$01
    BEQ OptionsChangeRight_lives_n
; fácil
    LDA $0C
    CMP #$02
    BCC OptionsChangeRight_lives_inc
    STZ $0C
    RTS
OptionsChangeRight_lives_inc:
    INC $0C
OptionsChangeRight_rts:
    RTS

OptionsChangeRight_lives_n:
    LDA $0C
    EOR #$01
    STA $0C
    RTS

OptionsChangeRight_diff:
    LDA $0D
    CMP #$02
    BCC OptionsChangeRight_diff_inc
    STZ $0D
    JSR ClampLivesToDiff
    RTS
OptionsChangeRight_diff_inc:
    INC $0D
    JSR ClampLivesToDiff
    RTS


; Fácil = livre; Normal = max 50; Difícil = só 10
ClampLivesToDiff:
    LDA $0D
    CMP #$02
    BEQ ClampLivesToDiff_hard
    CMP #$01
    BEQ ClampLivesToDiff_normal
    RTS
ClampLivesToDiff_hard:
    STZ $0C
    RTS
ClampLivesToDiff_normal:
    LDA $0C
    CMP #$02
    BCC ClampLivesToDiff_rts
    LDA #$01
    STA $0C
ClampLivesToDiff_rts:
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

; pal4 cinza (valores bloqueados) @ $C1
    LDA #$C1
    STA $2121
    LDA #$10
    STA $2122
    LDA #$42
    STA $2122            ; ~cinza

    LDA #$81
    STA $2121
    LDA #$FF
    STA $2122
    LDA #$7F
    STA $2122

    PLP
    RTS


;==============================================================================
ClearOAMMirror:
    PHP
    SEP #$20
    REP #$10
    LDX.w #$0000
ClearOAMMirror_loop:
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
    BCC ClearOAMMirror_loop
    LDX.w #$0000
ClearOAMMirror_hi:
    STZ $0400,X
    INX
    CPX.w #$0020
    BCC ClearOAMMirror_hi
    PLP
    RTS


;==============================================================================
BuildMainMenuOAM:
    PHP
    SEP #$20
    REP #$10
    JSR ClearOAMMirror

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
    LDA #88
    STA $07
    LDX.w #Str2P
    JSR DrawMenuString

    LDA #$02
    STA $05
    LDA #168
    STA $06
    LDA #88
    STA $07
    LDX.w #StrOpt
    JSR DrawMenuString

    JSR DrawCursor
    PLP
    RTS


;==============================================================================
; Opções:
;   linha 0: VIDAS: 10 50 100   (cinza = bloqueada pela dificuldade)
;   linha 1: DIFICULDADE: valor
;   linha 2: SAIR
;==============================================================================
BuildOptionsMenuOAM:
    PHP
    SEP #$20
    REP #$10
    JSR ClearOAMMirror

; --- linha 0: VIDAS:
    LDA #$00
    STA $05
    LDA #112
    STA $06
    LDA #40
    STA $07
    LDX.w #StrVidas
    JSR DrawMenuString

; valores 10 / 50 / 100 a partir de X=120
    LDA #120
    STA $07
    LDA #$00
    STA $0A              ; life index being drawn
    JSR DrawLifeChoice
    LDA #152
    STA $07
    LDA #$01
    STA $0A
    JSR DrawLifeChoice
    LDA #184
    STA $07
    LDA #$02
    STA $0A
    JSR DrawLifeChoice

; --- linha 1: DIFICULDADE: xxx
    LDA #$01
    STA $05
    LDA #136
    STA $06
    LDA #40
    STA $07
    LDX.w #StrDificuldade
    JSR DrawMenuString

    LDA #144
    STA $07
    LDA $0D
    ASL A
    TAX
    LDA DiffStrTable,X
    STA $12
    LDA DiffStrTable+1,X
    STA $13
    LDX $12
    JSR DrawMenuStringContinue

; --- linha 2: SAIR
    LDA #$02
    STA $05
    LDA #160
    STA $06
    LDA #40
    STA $07
    LDX.w #StrSair
    JSR DrawMenuString

    JSR DrawCursorOptions
    PLP
    RTS


; $0A = índice da vida (0/1/2), $07=X, $06=Y, usa slots OAM 48+
DrawLifeChoice:
    PHP
    SEP #$20
    REP #$10

; attr: selecionada=cor da linha0; bloqueada=cinza pal4; senão branco
    LDA #$20             ; branco pal0
    STA $09

    LDA $0A
    CMP $0C
    BNE DrawLifeChoice_lockcheck
; valor atual
    LDA $00
    CMP #$00
    BNE DrawLifeChoice_cur_white
    LDA #$22             ; vermelho (linha 0 selecionada)
    STA $09
    BRA DrawLifeChoice_draw
DrawLifeChoice_cur_white:
    LDA #$20
    STA $09
    BRA DrawLifeChoice_draw

DrawLifeChoice_lockcheck:
    JSR IsLifeAllowed
    BCS DrawLifeChoice_draw
    LDA #$28             ; pal4 cinza (ppp=100 -> <<1 = 8)
    STA $09

DrawLifeChoice_draw:
; oam base: 48*4 + life_idx*16 = 192 + idx*16
    LDA $0A
    ASL A
    ASL A
    ASL A
    ASL A
    CLC
    ADC #192
    STA $08

    LDA $0A
    ASL A
    TAX
    LDA LivesStrTable,X
    STA $12
    LDA LivesStrTable+1,X
    STA $13
    LDX $12

DrawLifeChoice_loop:
    LDA $0000,X
    CMP #$FF
    BEQ DrawLifeChoice_done
    STA $14
    PHX
    LDA $08
    TAX
    LDA $07
    STA $0200,X
    LDA $06
    STA $0201,X
    LDA $14
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
    BRA DrawLifeChoice_loop
DrawLifeChoice_done:
    PLP
    RTS


; carry set = permitido para $0A dado $0D
IsLifeAllowed:
    LDA $0D
    CMP #$02
    BEQ IsLifeAllowed_hard
    CMP #$01
    BEQ IsLifeAllowed_normal
    SEC                    ; fácil: tudo
    RTS
IsLifeAllowed_hard:
    LDA $0A
    CMP #$00
    BEQ IsLifeAllowed_yes
    CLC
    RTS
IsLifeAllowed_normal:
    LDA $0A
    CMP #$02
    BCS IsLifeAllowed_no
IsLifeAllowed_yes:
    SEC
    RTS
IsLifeAllowed_no:
    CLC
    RTS


; Desenha valor da dificuldade em slots fixos (offset 160), sem colidir com SAIR
DrawMenuStringContinue:
    PHP
    SEP #$20
    REP #$10

    LDA #160
    STA $08

    LDA #$20
    STA $09
    LDA $05
    CMP $00
    BNE DrawMenuStringContinue_loop
    LDA $05
    INC A
    ASL A
    AND #$0E
    ORA #$20
    STA $09

DrawMenuStringContinue_loop:
    LDA $0000,X
    CMP #$FF
    BEQ DrawMenuStringContinue_done
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
    BRA DrawMenuStringContinue_loop
DrawMenuStringContinue_done:
    PLP
    RTS


; X = ponteiro string ($FF = fim); $05=row para cor/slots
DrawMenuString:
    PHP
    SEP #$20
    REP #$10

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
    BNE DrawMenuString_loop
    LDA $05
    INC A
    ASL A
    AND #$0E
    ORA #$20
    STA $09

DrawMenuString_loop:
    LDA $0000,X
    CMP #$FF
    BEQ DrawMenuString_done
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
    BRA DrawMenuString_loop

DrawMenuString_done:
    PLP
    RTS


DrawCursor:
    PHP
    SEP #$20
    LDA #72
    STA $02F0
    LDA $00
    STA $0A
    ASL A
    CLC
    ADC $0A
    ASL A
    ASL A
    ASL A
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


; cursor opções: Y = 112 + sel*24, X = 24
DrawCursorOptions:
    PHP
    SEP #$20
    LDA #24
    STA $02F0
    LDA $00
    STA $0A
    ASL A
    CLC
    ADC $0A
    ASL A
    ASL A
    ASL A
    CLC
    ADC #112
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
; Strings (índices de tile da fonte)
;==============================================================================
Str1P:
    db 17,0,42,47,39,33,36,47,50
    db $FF

Str2P:
    db 18,0,42,47,39,33,36,47,50,37,51
    db $FF

StrOpt:
    db 47,48,64,65,37,51
    db $FF

; "VIDAS:"
StrVidas:
    db 54,41,36,33,51,26
    db $FF

; "DIFICULDADE:"
StrDificuldade:
    db 36,41,38,41,35,53,44,36,33,36,37,26
    db $FF

StrSair:
    db 51,33,41,50
    db $FF

StrLives10:
    db 17,16
    db $FF
StrLives50:
    db 21,16
    db $FF
StrLives100:
    db 17,16,16
    db $FF

; "FÁCIL"
StrEasy:
    db 38,66,35,41,44
    db $FF
; "NORMAL"
StrNormal:
    db 46,47,50,45,33,44
    db $FF
; "DIFÍCIL"
StrHard:
    db 36,41,38,68,35,41,44
    db $FF

LivesStrTable:
    dw StrLives10, StrLives50, StrLives100

DiffStrTable:
    dw StrEasy, StrNormal, StrHard


