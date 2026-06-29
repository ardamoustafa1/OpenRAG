#!/bin/bash

# Default configurations for Qwen2.5-72B Instruct or similar large models
MODEL_ID=${MODEL_ID:-"Qwen/Qwen2.5-72B-Instruct"}
SERVED_MODEL_NAME=${SERVED_MODEL_NAME:-"openai/Qwen2.5-72B-Instruct"}
TENSOR_PARALLEL_SIZE=${TENSOR_PARALLEL_SIZE:-2} # Assumes 2 GPUs for 72B quantized

echo "Starting vLLM serving model $MODEL_ID with Tensor Parallel Size $TENSOR_PARALLEL_SIZE"

# Start the vLLM server
# - --enable-prefix-caching: greatly speeds up multi-turn chat with the same system prompt
# - --quantization: auto-detects AWQ/GPTQ if the model supports it
# - --gpu-memory-utilization: 0.9 (leave 10% for PagedAttention cache and OS)

exec python3 -m vllm.entrypoints.openai.api_server \
    --model $MODEL_ID \
    --served-model-name $SERVED_MODEL_NAME \
    --tensor-parallel-size $TENSOR_PARALLEL_SIZE \
    --enable-prefix-caching \
    --gpu-memory-utilization 0.90 \
    --max-model-len 4096 \
    --host 0.0.0.0 \
    --port 8000
