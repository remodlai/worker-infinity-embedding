import runpod
from utils import create_error_response
from typing import Any
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Run startup configuration
logger.info("Starting RunPod worker...")

# Check transformers version
try:
    import transformers
    logger.info(f"Transformers version: {transformers.__version__}")
except ImportError:
    logger.error("Transformers not installed!")

# Configure model paths
os.environ["MODEL_NAMES"] = "/models/Qwen3-Embedding-0.6B;/models/Qwen3-Reranker-0.6B"
logger.info("Using Qwen3 embedding and reranker models from container for optimal performance")

# Set HF_HOME if volume is mounted
if os.path.exists("/runpod-volume"):
    os.environ['HF_HOME'] = "/runpod-volume"
    logger.info("Set HF_HOME to /runpod-volume for model cache")

# Import embedding service after configuration
from embedding_service import EmbeddingService

# Gracefully catch configuration errors (e.g. missing env vars) so the user sees
# a clean message instead of a full Python traceback when the container starts.
try:
    logger.info("Initializing embedding service...")
    embedding_service = EmbeddingService()
    logger.info("Embedding service initialized successfully")
except Exception as e:  # noqa: BLE001  (intercept everything on startup)
    import sys
    import traceback

    sys.stderr.write(f"\nstartup failed: {e}\n")
    sys.stderr.write(f"Traceback:\n{traceback.format_exc()}\n")
    sys.exit(1)


async def async_generator_handler(job: dict[str, Any]):
    """Handle the requests and embedding/rerank them asynchronously."""
    job_input = job["input"]
    if job_input.get("openai_route"):
        openai_route, openai_input = job_input.get("openai_route"), job_input.get(
            "openai_input"
        )

        if openai_route and openai_route == "/v1/models":
            call_fn, kwargs = embedding_service.route_openai_models, {}
        elif openai_route and openai_route == "/v1/embeddings":
            model_name = openai_input.get("model")
            if not openai_input:
                return create_error_response("Missing input").model_dump()
            if not model_name:
                return create_error_response(
                    "Did not specify model in openai_input"
                ).model_dump()
            # Extract instruction parameters from extra_body if present
            extra_body = openai_input.get("extra_body", {})
            instruction = extra_body.get("instruction")
            prompt_type = extra_body.get("prompt_type")
            
            call_fn, kwargs = embedding_service.route_openai_get_embeddings, {
                "embedding_input": openai_input.get("input"),
                "model_name": model_name,
                "instruction": instruction,
                "prompt_type": prompt_type,
                "return_as_list": True,
            }
        else:
            return create_error_response(
                f"Invalid OpenAI Route: {openai_route}"
            ).model_dump()
    else:
        # handle the request for reranking
        if job_input.get("query"):
            call_fn, kwargs = embedding_service.infinity_rerank, {
                "query": job_input.get("query"),
                "docs": job_input.get("docs"),
                "return_docs": job_input.get("return_docs"),
                "model_name": job_input.get("model"),
            }
        elif job_input.get("input"):
            call_fn, kwargs = embedding_service.route_openai_get_embeddings, {
                "embedding_input": job_input.get("input"),
                "model_name": job_input.get("model"),
                "instruction": job_input.get("instruction"),
                "prompt_type": job_input.get("prompt_type"),
            }
        else:
            return create_error_response(f"Invalid input: {job}").model_dump()
    try:
        out = await call_fn(**kwargs)
        return out
    except Exception as e:
        return create_error_response(str(e)).model_dump()


if __name__ == "__main__":
    logger.info("Starting RunPod serverless handler...")
    
    try:
        runpod.serverless.start(
            {
                "handler": async_generator_handler,
                "concurrency_modifier": lambda x: embedding_service.config.runpod_max_concurrency,
            }
        )
    except Exception as e:
        logger.error(f"Failed to start RunPod serverless: {e}")
        import traceback
        traceback.print_exc()
        raise
