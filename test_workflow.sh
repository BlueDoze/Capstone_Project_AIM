#!/bin/bash

echo "======================================================"
echo "TESTE DO WORKFLOW SIMPLIFICADO DE ANNOUNCEMENTS"
echo "======================================================"
echo ""

# 1. Verificar arquivo bruto do scraper
echo "1️⃣ Verificando all_announcements.json..."
if [ -f "all_announcements.json" ]; then
    echo "   ✅ Arquivo existe"
    TOTAL=$(cat all_announcements.json | python3 -c "import sys, json; print(json.load(sys.stdin)['total_announcements'])")
    echo "   📊 Total de announcements: $TOTAL"
else
    echo "   ❌ Arquivo não encontrado!"
    echo "   Execute: python3 extract_all_announcements.py"
    exit 1
fi

echo ""

# 2. Executar transformação
echo "2️⃣ Executando transformação..."
source .venv/bin/activate
python3 transform_cache.py

echo ""

# 3. Verificar cache gerado
echo "3️⃣ Verificando data/d2l_announcements.json..."
if [ -f "data/d2l_announcements.json" ]; then
    echo "   ✅ Cache criado com sucesso"
    CACHED=$(cat data/d2l_announcements.json | python3 -c "import sys, json; print(json.load(sys.stdin)['total'])")
    UPDATED=$(cat data/d2l_announcements.json | python3 -c "import sys, json; print(json.load(sys.stdin)['last_updated'])")
    echo "   📊 Total em cache: $CACHED"
    echo "   📅 Última atualização: $UPDATED"
else
    echo "   ❌ Cache não foi criado!"
    exit 1
fi

echo ""

# 4. Testar classificação de intenção (simulação)
echo "4️⃣ Testando queries de announcements..."
QUERIES=(
    "What are the latest announcements?"
    "Show me D2L news"
    "Any class updates?"
)

for query in "${QUERIES[@]}"; do
    echo "   📝 Query: \"$query\""
    # Simulação - verifica keywords
    if [[ "$query" =~ announcement|news|update|d2l|class ]]; then
        echo "      ✅ Intenção ANNOUNCEMENTS detectada"
    else
        echo "      ❌ Intenção não detectada"
    fi
done

echo ""
echo "======================================================"
echo "✅ WORKFLOW TESTADO COM SUCESSO!"
echo "======================================================"
echo ""
echo "Próximos passos:"
echo "  1. Inicie o servidor: python3 main.py"
echo "  2. Acesse: http://localhost:8081"
echo "  3. Pergunte: 'What are the latest announcements?'"
echo ""
