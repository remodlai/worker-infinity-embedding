#!/bin/bash
set -e

echo "Building Qwen3 Reranker container with model included..."

# Build from the parent directory to include both model and source
docker build \
  -f worker-qwen3-reranker/Dockerfile \
  -t ghcr.io/remodlai/worker-qwen3-reranker:latest \
  -t ghcr.io/remodlai/worker-qwen3-reranker:qwen3 \
  .

echo "Build complete!"
echo "To push: docker push ghcr.io/remodlai/worker-qwen3-reranker:latest"