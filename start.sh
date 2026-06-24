#!/bin/bash
cd "$(dirname "$0")"

# Lê o idioma do JSON de forma limpa usando awk/grep nativo
LANG_CODE="EN-US"
if [ -f "LANG.json" ]; then
    DETECTED=$(grep -o '"current_language": *"[^"]*"' LANG.json | cut -d'"' -f4)
    if [ ! -z "$DETECTED" ]; then LANG_CODE=$DETECTED; fi
fi

case $LANG_CODE in
    "PT-BR"|"PT-PT") MSG="Iniciando Servidor...";;
    "ES-ES"|"ES-US") MSG="Iniciando Servidor...";;
    "RU-RU") MSG="Запуск сервера...";;
    *) MSG="Starting Server...";;
esac

echo "========================================="
echo "   $MSG   "
echo "========================================="

if [ -d "venv" ]; then
    source venv/bin/activate
fi
python3 app.py
