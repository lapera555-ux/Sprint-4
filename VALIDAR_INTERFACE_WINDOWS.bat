@echo off
setlocal
cd /d "%~dp0sompo_mvp"
if errorlevel 1 goto fail
if not exist ".venv\Scripts\python.exe" (
 echo Primeiro execute ABRIR_SOMPO_WINDOWS.bat para instalar o ambiente.
 pause
 exit /b 1
)
".venv\Scripts\python.exe" -m pytest tests -q
if errorlevel 1 goto fail
".venv\Scripts\python.exe" -m scripts.check_db
if errorlevel 1 goto fail
".venv\Scripts\python.exe" -m scripts.check_agro_final --structural-only
if errorlevel 1 goto fail
echo.
echo Verificacoes locais concluidas. Para os hashes cientificos completos, anexe os ZIPs oficiais.
pause
exit /b 0
:fail
echo.
echo Falha na verificacao. Consulte o erro acima.
pause
exit /b 2
