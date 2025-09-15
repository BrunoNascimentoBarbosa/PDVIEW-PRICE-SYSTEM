#!/bin/bash

echo "========================================"
echo "   PDVIEW - Iniciando no Orange Pi"
echo "========================================"

# Verifica se Node.js está instalado
if ! command -v node &> /dev/null; then
    echo "❌ Node.js não encontrado!"
    echo "Instale com: sudo apt-get install nodejs"
    exit 1
fi

# Mata processos anteriores na porta 3000
echo "🔧 Verificando porta 3000..."
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Porta 3000 em uso, encerrando processo anterior..."
    kill $(lsof -Pi :3000 -sTCP:LISTEN -t) 2>/dev/null
    sleep 2
fi

# Inicia servidor de preços (Node.js)
echo "🚀 Iniciando servidor de preços na porta 3000..."
node save-price.js &
PRICE_PID=$!

sleep 2

# Verifica se o servidor de preços iniciou
if ! lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "❌ Erro ao iniciar servidor de preços!"
    exit 1
fi

echo "✅ Servidor de preços rodando (PID: $PRICE_PID)"

# Inicia servidor HTTP principal
echo "🚀 Iniciando servidor HTTP na porta 8000..."
python3 -m http.server 8000 --bind 0.0.0.0 &
HTTP_PID=$!

sleep 2

# Mostra informações de acesso
echo ""
echo "========================================"
echo "✅ SERVIDORES INICIADOS COM SUCESSO!"
echo "========================================"

# Obtém IP local
IP=$(hostname -I | awk '{print $1}')

echo ""
echo "📱 ACESSO LOCAL:"
echo "   http://localhost:8000/play.html"
echo ""
echo "📱 ACESSO NA REDE (TV/Painel):"
echo "   http://$IP:8000/play.html"
echo ""
echo "⚙️  CONFIGURAR PREÇOS:"
echo "   http://$IP:8000/"
echo ""
echo "========================================"
echo "Para parar: Ctrl+C"
echo "========================================"

# Função para encerrar servidores ao pressionar Ctrl+C
cleanup() {
    echo ""
    echo "🛑 Encerrando servidores..."
    kill $PRICE_PID 2>/dev/null
    kill $HTTP_PID 2>/dev/null
    echo "✅ Servidores encerrados"
    exit 0
}

trap cleanup INT

# Mantém script rodando
while true; do
    # Verifica se os servidores ainda estão rodando
    if ! kill -0 $PRICE_PID 2>/dev/null; then
        echo "⚠️  Servidor de preços parou! Reiniciando..."
        node save-price.js &
        PRICE_PID=$!
    fi

    if ! kill -0 $HTTP_PID 2>/dev/null; then
        echo "⚠️  Servidor HTTP parou! Reiniciando..."
        python3 -m http.server 8000 --bind 0.0.0.0 &
        HTTP_PID=$!
    fi

    sleep 10
done