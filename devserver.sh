#!/bin/bash
source .venv/bin/activate

# Mostra o IP local para acesso mobile
LOCAL_IP=$(hostname -I | awk '{print $1}')
PORT=${PORT:-8081}

echo "=========================================="
echo "🚀 Servidor Flask iniciando..."
echo "=========================================="
echo "📱 Para acessar no celular, use:"
echo "   http://$LOCAL_IP:$PORT"
echo "=========================================="
echo ""

python3 -u main.py
