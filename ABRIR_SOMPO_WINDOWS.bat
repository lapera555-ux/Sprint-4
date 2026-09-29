@echo off
setlocal
cd /d "%~dp0sompo_mvp"
if errorlevel 1 goto fail
call "INICIAR_WINDOWS.bat"
exit /b %errorlevel%
:fail
echo Erro: extraia o ZIP completo antes de executar.
pause
exit /b 2
