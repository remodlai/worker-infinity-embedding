#!/bin/bash

# Two-stage build script for infinity-emb with Qwen3 support

# Configuration
GITHUB_ORG="remodlai"
REGISTRY="ghcr.io"
BASE_IMAGE_NAME="infinity-qwen3-base"
WORKER_IMAGE_NAME="worker-infinity-embedding"
VERSION="2.0.0-qwen3"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Two-Stage Build Process ===${NC}"

# Stage 1: Build and test the base infinity image
echo -e "\n${GREEN}Stage 1: Building base infinity-emb image...${NC}"
docker buildx build \
  --platform linux/amd64 \
  -t "${REGISTRY}/${GITHUB_ORG}/${BASE_IMAGE_NAME}:${VERSION}" \
  -t "${REGISTRY}/${GITHUB_ORG}/${BASE_IMAGE_NAME}:latest" \
  -f Dockerfile.infinity-base \
  .

if [ $? -ne 0 ]; then
    echo -e "${RED}Base image build failed!${NC}"
    exit 1
fi

# Test the base image locally
echo -e "\n${YELLOW}Testing base image...${NC}"
docker run --rm "${REGISTRY}/${GITHUB_ORG}/${BASE_IMAGE_NAME}:${VERSION}"

if [ $? -ne 0 ]; then
    echo -e "${RED}Base image test failed!${NC}"
    exit 1
fi

echo -e "${GREEN}Base image test passed!${NC}"

# Push base image
echo -e "\n${YELLOW}Pushing base image to registry...${NC}"
docker push "${REGISTRY}/${GITHUB_ORG}/${BASE_IMAGE_NAME}:${VERSION}"
docker push "${REGISTRY}/${GITHUB_ORG}/${BASE_IMAGE_NAME}:latest"

if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to push base image!${NC}"
    exit 1
fi

# Stage 2: Build the RunPod worker image
echo -e "\n${GREEN}Stage 2: Building RunPod worker image...${NC}"
docker buildx build \
  --platform linux/amd64 \
  --build-arg BASE_IMAGE="${REGISTRY}/${GITHUB_ORG}/${BASE_IMAGE_NAME}:${VERSION}" \
  -t "${REGISTRY}/${GITHUB_ORG}/${WORKER_IMAGE_NAME}:${VERSION}" \
  -t "${REGISTRY}/${GITHUB_ORG}/${WORKER_IMAGE_NAME}:latest" \
  -f Dockerfile.runpod \
  .

if [ $? -ne 0 ]; then
    echo -e "${RED}Worker image build failed!${NC}"
    exit 1
fi

# Push worker image
echo -e "\n${YELLOW}Pushing worker image to registry...${NC}"
docker push "${REGISTRY}/${GITHUB_ORG}/${WORKER_IMAGE_NAME}:${VERSION}"
docker push "${REGISTRY}/${GITHUB_ORG}/${WORKER_IMAGE_NAME}:latest"

if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}=== Build Complete! ===${NC}"
    echo ""
    echo "Images created:"
    echo "  Base: ${REGISTRY}/${GITHUB_ORG}/${BASE_IMAGE_NAME}:${VERSION}"
    echo "  Worker: ${REGISTRY}/${GITHUB_ORG}/${WORKER_IMAGE_NAME}:${VERSION}"
    echo ""
    echo "RunPod Deployment:"
    echo "  Image: ${REGISTRY}/${GITHUB_ORG}/${WORKER_IMAGE_NAME}:${VERSION}"
    echo "  Port: 8000"
    echo ""
    echo "Required Environment Variables:"
    echo "  MODEL_NAMES=Qwen/Qwen3-Embedding-4B;Qwen/Qwen3-Reranker-4B"
    echo "  HF_HOME=/runpod-volume"
    echo "  TRANSFORMERS_CACHE=/runpod-volume/huggingface"
    echo "  HF_DATASETS_CACHE=/runpod-volume/huggingface/datasets"
    echo ""
    echo "Network Volume Configuration:"
    echo "  Volume ID: rtjix2riw9"
    echo "  Mount Path: /runpod-volume"
else
    echo -e "${RED}Failed to push worker image!${NC}"
    exit 1
fi