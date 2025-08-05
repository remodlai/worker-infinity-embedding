# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a RunPod serverless worker that provides high-throughput text embedding and reranking services using the Infinity engine. It exposes both OpenAI-compatible and standard RunPod APIs for embedding generation and document reranking. 

Currently configured to use **Qwen3-4B models** with a forked version of infinity-emb that includes Qwen3 support.

## Key Architecture Components

- **Handler Layer** (`src/handler.py`): Main entry point that routes requests to either OpenAI-compatible endpoints or standard embedding/reranking endpoints
- **Embedding Service** (`src/embedding_service.py`): Core service managing the Infinity engine array for concurrent model processing
- **Configuration** (`src/config.py`): Environment-based configuration with validation and defaults
- **Utilities** (`src/utils.py`): Response formatting and error handling utilities

## Development Commands

### Local Development with Docker

```bash
# Build and run with docker-compose (includes GPU support)
docker-compose up --build

# Build image using docker-bake
docker buildx bake -f docker-bake.hcl
```

### Testing

```bash
# Run with test input (when container is running)
# The container will automatically process test_input.json on startup if no API server flag is provided
docker-compose up --build
```

### Deployment

```bash
# Build and push to GitHub Container Registry (requires authentication)
# First login: echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
./deploy.sh

# Or manually build for RunPod platform
docker buildx build --platform linux/amd64 -t ghcr.io/remodlai/worker-infinity-embedding:qwen3 --push .
```

## Configuration

All configuration is done through environment variables:

- `MODEL_NAMES` (required): Semicolon-separated list of HuggingFace model IDs
- `BATCH_SIZES`: Per-model batch sizes (default: 32)
- `BACKEND`: Inference engine - torch, optimum, or ctranslate2 (default: torch)
- `DTYPES`: Model precision - auto, fp16, fp8 (default: auto)
- `INFINITY_QUEUE_SIZE`: Max queue size (default: 48000)
- `RUNPOD_MAX_CONCURRENCY`: Max concurrent requests (default: 300)

## API Endpoints

The service supports two API styles:

1. **OpenAI-compatible**: `/openai/v1/models`, `/openai/v1/embeddings`
2. **Standard RunPod**: `/runsync` with appropriate input payloads

## Key Implementation Details

- Uses `infinity-emb` library with async engine array for concurrent processing
- Supports multiple models loaded simultaneously with independent configurations
- Implements both embedding generation and document reranking
- Error responses follow OpenAI error format for compatibility
- Graceful startup error handling with clear error messages
- **Model Persistence**: On first run, models are copied from container to RunPod volume (rtjix2riw9). Subsequent runs use models from volume to avoid re-downloading
- Models included in container: Qwen3-Embedding-0.6B and Qwen3-Reranker-0.6B

## Development Guidelines

- You must have me run docker build commands

## Performance Optimization

- **Worker Warm-keeping**: RunPod serverless workers have a ~5 minute timeout. To maintain sub-200ms response times, implement a randomized warm-keeping strategy:
  - Schedule requests every 3-5 minutes with random delays (180-300 seconds)
  - Vary request content slightly (different queries)
  - Randomize request order between services
  - Cost: ~$0.45/month for 24/7 warm workers
  - Benefit: 100x faster response times (200ms vs 15-20s cold start)