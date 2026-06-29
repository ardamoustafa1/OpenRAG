# Use the official vLLM image
FROM vllm/vllm-openai:latest

WORKDIR /app

# Copy the startup script
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# The model path or HF hub ID is passed as an env var or cmd arg
# Expose vLLM port
EXPOSE 8000

ENTRYPOINT ["/app/start.sh"]
