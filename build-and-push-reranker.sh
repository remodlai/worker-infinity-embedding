#!/bin/bash
set -e

# Generate version tag with timestamp
VERSION="v$(date +%Y%m%d-%H%M%S)"

echo "Building and pushing multi-platform Qwen3 Reranker container..."
echo "Version: $VERSION"

# Build for both linux/amd64 and linux/arm64
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -f worker-qwen3-reranker/Dockerfile \
  -t ghcr.io/remodlai/worker-qwen3-reranker:latest \
  -t ghcr.io/remodlai/worker-qwen3-reranker:qwen3 \
  -t ghcr.io/remodlai/worker-qwen3-reranker:$VERSION \
  --push \
  .

echo "Multi-platform build and push complete!"
echo "Use this image in RunPod: ghcr.io/remodlai/worker-qwen3-reranker:$VERSION"