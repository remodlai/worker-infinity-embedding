#!/bin/bash

# Build and deploy script for RunPod worker-infinity-embedding with Qwen3 support

# Configuration for GitHub Container Registry
GITHUB_ORG="remodlai"
REGISTRY="ghcr.io"
IMAGE_NAME="worker-infinity-embedding"
VERSION="1.0.0-qwen3"

# Full image path
IMAGE_PATH="${REGISTRY}/${GITHUB_ORG}/${IMAGE_NAME}"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Building Docker image for Qwen3 embedding worker...${NC}"
echo -e "${YELLOW}Registry: ${REGISTRY}${NC}"
echo -e "${YELLOW}Image: ${IMAGE_PATH}:${VERSION}${NC}"

# Check if logged in to GitHub Container Registry (optional check)
echo -e "${YELLOW}Proceeding with build... Make sure you're logged in to ${REGISTRY}${NC}"

# Build the image for linux/amd64 platform (required for RunPod)
docker buildx build \
  --platform linux/amd64 \
  -t "${IMAGE_PATH}:${VERSION}" \
  -t "${IMAGE_PATH}:latest" \
  --push \
  .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Build and push completed successfully!${NC}"
    echo ""
    echo "Deployment information for RunPod:"
    echo "================================="
    echo "Docker Image: ${IMAGE_PATH}:${VERSION}"
    echo ""
    echo "To make the image public (if needed):"
    echo "  Go to: https://github.com/orgs/${GITHUB_ORG}/packages/container/${IMAGE_NAME}/settings"
    echo "  Change visibility to 'Public'"
    echo ""
    echo "Required Environment Variables for RunPod:"
    echo "  MODEL_NAMES=Qwen/Qwen3-Embedding-4B;Qwen/Qwen3-Reranker-4B"
    echo "  HF_HOME=/runpod-volume"
    echo "  TRANSFORMERS_CACHE=/runpod-volume/huggingface"
    echo "  HF_DATASETS_CACHE=/runpod-volume/huggingface/datasets"
    echo ""
    echo "Network Volume Configuration:"
    echo "  Volume ID: rtjix2riw9"
    echo "  Mount Path: /runpod-volume"
    echo ""
    echo "Optional Configuration:"
    echo "  BATCH_SIZES=32;32"
    echo "  BACKEND=torch"
    echo "  DTYPES=auto;auto"
    echo "  INFINITY_QUEUE_SIZE=48000"
    echo "  RUNPOD_MAX_CONCURRENCY=300"
else
    echo -e "${RED}Build failed!${NC}"
    exit 1
fi