@echo off
echo Use make.sh no Linux (gera graficos + ROM).
echo Montagem rapida (assume gfx/ ja gerado):
copy /Y modelo.smc jogo.smc
xkas main.asm jogo.smc
echo ROM gerada: jogo.smc
pause
