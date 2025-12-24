hf auth login --token your_huggingface_token_here

python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Meta-Llama-3-8B-Instruct \
    --dtype bfloat16 \
    --api-key secret-agri-token \
    --port 8000 \
    --gpu-memory-utilization 0.4