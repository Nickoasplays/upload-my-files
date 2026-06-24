#!/bin/bash
# Navega até a pasta onde o script está guardado
cd "$(dirname "$0")"

echo "========================================="
echo "   Iniciando Servidor Compartilhado...  "
echo "========================================="

# Verifica se o ambiente virtual existe, senão ativa o python direto
if [ -d "venv" ]; then
    echo "[+] Ativando ambiente virtual (venv)..."
    source venv/bin/activate
fi

# Executa o servidor
python3 app.py

# Se o servidor fechar ou der erro, o terminal não fecha na hora
echo ""
echo "Servidor encerrado. Pressione Enter para fechar esta janela."
read
