FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC
ENV PYTHONUNBUFFERED=1
ENV HF_HOME=/runpod-volume

# Install Python 3.11 and other dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3-pip \
    git \
    wget \
    && ln -sf /usr/bin/python3.11 /usr/bin/python3 \
    && ln -sf /usr/bin/python3.11 /usr/bin/python \
    && ln -sf /usr/bin/pip3 /usr/bin/pip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster package installation
RUN pip install uv

# Set working directory
WORKDIR /

# Install Python dependencies
COPY worker-qwen3-reranker/requirements.txt /requirements.txt
RUN uv pip install -r /requirements.txt --system

# Copy the pre-downloaded model
# Note: When building, use parent directory as context: docker build -f worker-qwen3-reranker/Dockerfile .
COPY models/hub/models--Qwen--Qwen3-Reranker-0.6B /models/Qwen3-Reranker-0.6B

# Copy source code
COPY worker-qwen3-reranker/src/ /

# Expose port for local testing (optional)
EXPOSE 8000

# Run the handler
CMD ["python", "-u", "/handler.py"]