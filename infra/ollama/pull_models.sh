#!/bin/bash
# Script to wait for Ollama to be ready and pull required models

echo "Waiting for Ollama service to start..."

# Wait until Ollama API responds
until curl -s -f http://ollama:11434/api/tags > /dev/null; do
    echo "Ollama not ready yet. Retrying in 5 seconds..."
    sleep 5
done

echo "Ollama is ready. Pulling models..."

# List of models to pull
MODELS=(
    "llama3.3"
    "phi-4"
    "nomic-embed-text"
    "bge-m3"
    "deepseek-coder-v2"
)

for MODEL in "${MODELS[@]}"; do
    echo "Pulling $MODEL..."
    curl -X POST http://ollama:11434/api/pull -d "{\"name\": \"$MODEL\"}"
done

echo "All models pulled successfully!"
