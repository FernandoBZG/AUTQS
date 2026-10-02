@echo off
title AUTQS - Assistente de IA para TQS V25
echo ================================================================
echo    AUTQS - INICIANDO INTERFACE DE CHAT INTELIGENTE PARA TQS
echo ================================================================
echo.
echo Abrindo servidor Streamlit no navegador padrao...
echo Pressione Ctrl+C para encerrar o servidor.
echo.

setlocal
set "PYTHONPATH=%~dp0;%PYTHONPATH%"

:: 1. Tenta o launcher oficial do Windows (py -3-64)
py -3-64 -c "exit(0)" 2>nul
if %ERRORLEVEL% equ 0 (
    py -3-64 -m streamlit run src\ui\chat_app.py --server.port 8501
    goto :eof
)

:: 2. Tenta Python 64 bits no Program Files
if exist "%ProgramFiles%\Python311\python.exe" (
    "%ProgramFiles%\Python311\python.exe" -m streamlit run src\ui\chat_app.py --server.port 8501
    goto :eof
)
if exist "%ProgramFiles%\Python312\python.exe" (
    "%ProgramFiles%\Python312\python.exe" -m streamlit run src\ui\chat_app.py --server.port 8501
    goto :eof
)
if exist "%ProgramFiles%\Python313\python.exe" (
    "%ProgramFiles%\Python313\python.exe" -m streamlit run src\ui\chat_app.py --server.port 8501
    goto :eof
)

:: 3. Tenta Python 64 bits no AppData do usuario atual
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" -m streamlit run src\ui\chat_app.py --server.port 8501
    goto :eof
)
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" -m streamlit run src\ui\chat_app.py --server.port 8501
    goto :eof
)
if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" -m streamlit run src\ui\chat_app.py --server.port 8501
    goto :eof
)

:: 4. Fallback padrao
python -m streamlit run src\ui\chat_app.py --server.port 8501
endlocal
