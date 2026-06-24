@echo off
:: Navega para a pasta do script
cd /d "%~dp0"

title Servidor de Compartilhamento Local

echo =========================================
echo    Iniciando Servidor Compartilhado...
echo =========================================

:: Verifica se a venv do Windows existe
if exist venv\Scripts\activate.bat (
    echo [+] Ativando ambiente virtual ^(venv^)...
    call venv\Scripts\activate.bat
)

:: Roda o Python no Windows
python app.py

echo.
echo Servidor encerrado.
pause
