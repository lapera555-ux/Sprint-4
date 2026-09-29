@echo off
setlocal
cd /d "%~dp0sompo_mvp"
if errorlevel 1 goto fail
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -m scripts.attach_original_sources
) else (
  py -3 -m scripts.attach_original_sources
)
if errorlevel 1 goto fail
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -m scripts.check_agro_final
) else (
  py -3 -m scripts.check_agro_final
)
if errorlevel 1 goto fail
echo.
echo Fontes originais reunidas e validacao estrita concluida.
pause
exit /b 0
:fail
echo.
echo ERRO: nenhum dado ficticio foi criado. Confira os ZIPs originais.
pause
exit /b 2
