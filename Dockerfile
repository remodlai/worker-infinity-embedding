# Build from the infinity base
FROM ghcr.io/remodlai/infinity-qwen3:latest

ENV HF_HOME=/runpod-volume

# Install uv
RUN pip install uv

# Install python dependencies for the worker
COPY requirements.txt /requirements.txt
RUN uv pip install -r /requirements.txt --system

# Copy models into the image for fast cold starts
# These will be copied to volume on first run if volume is available
COPY models/hub/models--Qwen--Qwen3-Embedding-0.6B /models/Qwen3-Embedding-0.6B
COPY models/hub/models--Qwen--Qwen3-Reranker-0.6B /models/Qwen3-Reranker-0.6B

# Add src files
ADD src .

# Add test input
COPY test_input.json /test_input.json

# Expose the RunPod serverless port
EXPOSE 8000

# Use ENTRYPOINT and CMD as recommended by RunPod
ENTRYPOINT ["python", "-u"]
CMD ["/startup.py"]