@echo off
cd /d "%~dp0"
title Local File Sharing Server

:: Fallback de mensagem simples e internacionalizada
echo =========================================
echo    Starting Local File Sharing Server...
echo =========================================

if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

python app.py
pause
