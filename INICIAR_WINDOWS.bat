@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    py -3 -m venv .venv
    if errorlevel 1 goto fail
)
call ".venv\Scripts\activate.bat"
python -m pip install -r requirements.txt
if errorlevel 1 goto fail
echo Conferindo e restaurando os arquivos cientificos originais, se necessario...
python -m scripts.prepare_packaged_sources
if errorlevel 1 goto fail
python -m scripts.ensure_runtime
if errorlevel 1 goto fail
python -m streamlit run app.py
if errorlevel 1 goto fail
exit /b 0
:fail
echo ERRO: revise a mensagem acima. Nenhum resultado foi inventado.
pause
exit /b 1
