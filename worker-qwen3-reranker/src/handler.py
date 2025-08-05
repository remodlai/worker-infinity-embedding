import runpod
import asyncio
import logging
import os
from typing import Any, Dict

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure model path
if os.path.exists("/models/Qwen3-Reranker-0.6B"):
    os.environ["MODEL_NAME"] = "/models/Qwen3-Reranker-0.6B"
    logger.info("Using containerized model at /models/Qwen3-Reranker-0.6B")
else:
    # Fall back to HuggingFace model ID
    os.environ["MODEL_NAME"] = "Qwen/Qwen3-Reranker-0.6B"
    logger.info("Model will be downloaded from HuggingFace")

# Import after setting environment
from reranker_service import Qwen3RerankerService

# Initialize service
try:
    logger.info("Initializing reranker service...")
    reranker_service = Qwen3RerankerService()
    logger.info("Reranker service initialized successfully")
except Exception as e:
    import sys
    import traceback
    sys.stderr.write(f"\nStartup failed: {e}\n")
    sys.stderr.write(f"Traceback:\n{traceback.format_exc()}\n")
    sys.exit(1)


def handler(job: Dict[str, Any]) -> Dict[str, Any]:
    """Handle RunPod job requests"""
    try:
        job_input = job["input"]
        
        # Check if this is an OpenAI-compatible route
        if job_input.get("openai_route"):
            route = job_input.get("openai_route")
            
            if route == "/v1/rerank":
                # Handle reranking request
                rerank_input = job_input.get("openai_input", {})
                
                # Validate required fields
                if not rerank_input.get("query"):
                    return {
                        "error": {
                            "message": "Missing required field: query",
                            "type": "invalid_request_error"
                        }
                    }
                
                if not rerank_input.get("documents"):
                    return {
                        "error": {
                            "message": "Missing required field: documents",
                            "type": "invalid_request_error"
                        }
                    }
                
                # Extract parameters
                query = rerank_input["query"]
                documents = rerank_input["documents"]
                instruction = rerank_input.get("extra_body", {}).get("instruction")
                return_documents = rerank_input.get("return_documents", True)
                top_k = rerank_input.get("top_k")
                
                # Perform reranking
                result = reranker_service.rerank(
                    query=query,
                    documents=documents,
                    instruction=instruction,
                    return_documents=return_documents,
                    top_k=top_k
                )
                
                return result
                
            elif route == "/v1/models":
                # Return available models
                return {
                    "object": "list",
                    "data": [{
                        "id": "Qwen3-Reranker-0.6B",
                        "object": "model",
                        "created": 1754341335,
                        "owned_by": "qwen"
                    }]
                }
            else:
                return {
                    "error": {
                        "message": f"Unknown route: {route}",
                        "type": "invalid_request_error"
                    }
                }
        
        # Handle standard reranking request (non-OpenAI format)
        else:
            # Extract parameters
            query = job_input.get("query")
            documents = job_input.get("documents", job_input.get("docs"))
            instruction = job_input.get("instruction")
            return_documents = job_input.get("return_documents", job_input.get("return_docs", True))
            top_k = job_input.get("top_k")
            
            # Validate
            if not query:
                return {"error": "Missing required field: query"}
            if not documents:
                return {"error": "Missing required field: documents or docs"}
            
            # Perform reranking
            result = reranker_service.rerank(
                query=query,
                documents=documents,
                instruction=instruction,
                return_documents=return_documents,
                top_k=top_k
            )
            
            return result
            
    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        return {
            "error": {
                "message": str(e),
                "type": "internal_error"
            }
        }




# For local testing
if __name__ == "__main__":
    # Test with sample data
    test_job = {
        "input": {
            "query": "What product has the best warranty?",
            "documents": [
                "Product A comes with a comprehensive 2-year warranty covering all parts and labor",
                "Product B includes a lifetime warranty but only covers manufacturing defects",
                "Product C has a 90-day limited warranty with no coverage for wear and tear",
                "Product D offers extended warranty options up to 5 years for additional cost",
                "Product E provides 1-year standard warranty with free shipping for repairs"
            ],
            "return_documents": True,
            "top_k": 3
        }
    }
    
    print("Testing reranker with sample data...")
    result = handler(test_job)
    
    import json
    print(json.dumps(result, indent=2))
    
    # If running in RunPod, start the serverless handler
    if os.environ.get("RUNPOD_POD_ID"):
        runpod.serverless.start({
            "handler": handler,
            "concurrency_modifier": lambda x: reranker_service.config.runpod_max_concurrency
        })