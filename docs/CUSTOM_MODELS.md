# 🧠 Integrating Custom LLMs

OpenRAG uses **LiteLLM** as an orchestration proxy. This means the backend code is agnostic to the LLM provider. LiteLLM translates the standard OpenAI API format into the format required by 100+ different providers (Ollama, vLLM, Anthropic, Azure, Cohere, etc.).

## 1. Local Models via Ollama (CPU/Mac)

By default, OpenRAG ships with Ollama configured.

To download and use a new model (e.g., `llama3`):
```bash
# Pull the model into the Ollama container
docker compose exec ollama ollama run llama3
```

Then edit `infra/litellm/config.yaml`:
```yaml
model_list:
  - model_name: llama3
    litellm_params:
      model: ollama/llama3
      api_base: http://ollama:11434
```
Restart LiteLLM: `docker compose restart litellm`.

## 2. High-Performance Local Inference via vLLM (GPU)

For production workloads with NVIDIA GPUs, use `vLLM` instead of Ollama. It offers 10x the throughput via PagedAttention.

1. Ensure the `vllm` service in `docker-compose.yml` is enabled (uncomment the `gpu` profile or run with `--profile gpu`).
2. Edit `infra/vllm/Dockerfile` to set your desired HuggingFace model (e.g., `meta-llama/Meta-Llama-3-8B-Instruct`).
3. Add the model to `infra/litellm/config.yaml`:
```yaml
model_list:
  - model_name: llama3-gpu
    litellm_params:
      model: openai/meta-llama/Meta-Llama-3-8B-Instruct
      api_base: http://vllm:8000/v1
```

## 3. External Cloud Providers (Not On-Premise)

If data privacy rules allow it, you can route specific tenants or fallbacks to cloud providers.

### OpenAI
```yaml
model_list:
  - model_name: gpt-4o
    litellm_params:
      model: gpt-4o
      api_key: os.environ/OPENAI_API_KEY
```
*(Remember to add `OPENAI_API_KEY` to the `.env` file!)*

### Azure OpenAI
```yaml
model_list:
  - model_name: azure-gpt-4
    litellm_params:
      model: azure/gpt-4
      api_base: https://my-endpoint.openai.azure.com/
      api_key: os.environ/AZURE_API_KEY
      api_version: "2024-02-15-preview"
```

## Selecting the Model in OpenRAG

Once configured in LiteLLM, models will automatically appear in the OpenRAG Admin UI under **Settings > Models**. You can assign default models per tenant or allow users to choose from a dropdown in the chat interface.
