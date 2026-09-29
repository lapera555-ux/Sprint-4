@echo off
setlocal
cd /d "%~dp0sompo_mvp"
if not exist ".venv\Scripts\python.exe" (
  echo Ambiente Python nao encontrado. Primeiro execute ABRIR_SOMPO_WINDOWS.bat.
  pause
  exit /b 1
)
echo [0/3] Conferindo arquivos originais do pacote...
.venv\Scripts\python.exe -m scripts.prepare_packaged_sources
if errorlevel 1 goto fail
echo [1/3] Testes automatizados...
.venv\Scripts\python.exe -m pytest tests -q
if errorlevel 1 goto fail
echo [2/3] Banco SQLite...
.venv\Scripts\python.exe -m scripts.check_db
if errorlevel 1 goto fail
echo [3/3] Verificacao estrita de fontes cientificas (requer os ZIPs originais)...
.venv\Scripts\python.exe -m scripts.check_agro_final
if errorlevel 1 goto fail
echo.
echo VALIDACOES CONCLUIDAS. Verifique as ressalvas de origem declarada.
pause
exit /b 0
:fail
echo.
echo VALIDACAO INTERROMPIDA. Se usar a edicao leve, rode ANEXAR_FONTES_ORIGINAIS_WINDOWS.bat primeiro.
pause
exit /b 2
