#!/bin/bash
# Abre o Radar de Preços no navegador. No Mac: dê dois cliques neste arquivo.
# Na primeira vez cria o ambiente (.venv) e instala as dependências.

cd "$(dirname "$0")" || exit 1

if [ ! -x .venv/bin/python ]; then
    echo "Primeira execução: criando ambiente (.venv)..."
    python3 -m venv .venv || { echo "Instale o Python 3.11+ (python.org) e tente de novo."; read -r; exit 1; }
fi
if ! .venv/bin/python -c "import streamlit, httpx, selectolax, dotenv, pandas" 2>/dev/null; then
    echo "Instalando dependências (alguns minutos)..."
    .venv/bin/python -m pip install -q --upgrade pip
    .venv/bin/python -m pip install -q -r requirements.txt || { echo "Falha ao instalar dependências."; read -r; exit 1; }
fi
[ -f .env ] || cp .env.example .env

PORTA=8501
if curl -s "http://localhost:$PORTA" >/dev/null; then
    echo "O Radar já está rodando; abrindo o navegador."
    open "http://localhost:$PORTA"
    exit 0
fi

# abre o navegador assim que o servidor responder
( for _ in $(seq 60); do curl -s "http://localhost:$PORTA" >/dev/null && open "http://localhost:$PORTA" && break; sleep 1; done ) &

echo "Radar de Preços rodando em http://localhost:$PORTA"
echo "Para encerrar, feche esta janela ou aperte Ctrl+C."
exec .venv/bin/python -m streamlit run app.py --server.headless true --server.port "$PORTA" \
    --server.address localhost --browser.gatherUsageStats false
