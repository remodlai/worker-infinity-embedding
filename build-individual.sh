#!/bin/bash

# Build and push each image individually

echo "Building embedding model container..."
docker buildx build --platform linux/amd64 \
  -f Dockerfile.embedding \
  -t ghcr.io/remodlai/qwen3-embedding-models:0.6B \
  --push .

echo "Building reranker model container..."
docker buildx build --platform linux/amd64 \
  -f Dockerfile.reranker \
  -t ghcr.io/remodlai/qwen3-reranker-models:0.6B \
  --push .

echo "Building infinity container..."
docker buildx build --platform linux/amd64 \
  -f Dockerfile.infinity \
  -t ghcr.io/remodlai/infinity-qwen3:latest \
  --build-context embedding-models=docker-image://ghcr.io/remodlai/qwen3-embedding-models:0.6B \
  --build-context reranker-models=docker-image://ghcr.io/remodlai/qwen3-reranker-models:0.6B \
  --push .

echo "Building worker container..."
docker buildx build --platform linux/amd64 \
  -f Dockerfile \
  -t ghcr.io/remodlai/worker-infinity-embedding:qwen3-0.6B \
  --build-context infinity=docker-image://ghcr.io/remodlai/infinity-qwen3:latest \
  --push .

echo "All builds complete!"