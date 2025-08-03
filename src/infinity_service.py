"""
Infinity Service
Orchestrates embedding and reranking requests between model servers
"""

import os
import httpx
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Service URLs
EMBEDDING_SERVICE_URL = os.getenv("EMBEDDING_SERVICE_URL", "http://embedding:8001")
RERANKER_SERVICE_URL = os.getenv("RERANKER_SERVICE_URL", "http://reranker:8002")

# HTTP client
client = httpx.AsyncClient(timeout=30.0)

class EmbeddingRequest(BaseModel):
    texts: List[str]
    model: Optional[str] = "Qwen/Qwen3-Embedding-0.6B"

class RerankRequest(BaseModel):
    query: str
    documents: List[str]
    model: Optional[str] = "Qwen/Qwen3-Reranker-0.6B"
    top_k: int = 10

@app.on_event("startup")
async def startup():
    logger.info("Infinity service starting...")
    # Wait for model services to be ready
    await wait_for_services()

@app.on_event("shutdown")
async def shutdown():
    await client.aclose()

async def wait_for_services():
    """Wait for model services to be healthy"""
    services = [
        (EMBEDDING_SERVICE_URL, "embedding"),
        (RERANKER_SERVICE_URL, "reranker")
    ]
    
    for url, name in services:
        retries = 30
        while retries > 0:
            try:
                response = await client.get(f"{url}/health")
                if response.status_code == 200:
                    logger.info(f"{name} service is ready")
                    break
            except Exception as e:
                logger.warning(f"Waiting for {name} service... ({retries} retries left)")
                retries -= 1
                await asyncio.sleep(2)
        
        if retries == 0:
            raise RuntimeError(f"{name} service failed to start")

@app.get("/health")
async def health():
    return {"status": "healthy", "services": {
        "embedding": EMBEDDING_SERVICE_URL,
        "reranker": RERANKER_SERVICE_URL
    }}

@app.get("/v1/models")
async def list_models():
    return {
        "data": [
            {"id": "Qwen/Qwen3-Embedding-0.6B", "type": "embedding"},
            {"id": "Qwen/Qwen3-Reranker-0.6B", "type": "reranker"}
        ]
    }

@app.post("/v1/embeddings")
async def create_embeddings(request: EmbeddingRequest):
    try:
        # Forward to embedding service
        response = await client.post(
            f"{EMBEDDING_SERVICE_URL}/embed",
            json={"texts": request.texts}
        )
        response.raise_for_status()
        
        result = response.json()
        
        # Format response like OpenAI
        return {
            "data": [
                {"embedding": emb, "index": i}
                for i, emb in enumerate(result["embeddings"])
            ],
            "model": request.model,
            "usage": {
                "prompt_tokens": sum(len(text.split()) for text in request.texts) * 2,
                "total_tokens": sum(len(text.split()) for text in request.texts) * 2
            }
        }
    
    except Exception as e:
        logger.error(f"Embedding error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/rerank")
async def rerank(request: RerankRequest):
    try:
        # Forward to reranker service
        response = await client.post(
            f"{RERANKER_SERVICE_URL}/rerank",
            json={
                "query": request.query,
                "documents": request.documents,
                "top_k": request.top_k
            }
        )
        response.raise_for_status()
        
        result = response.json()
        
        return {
            "results": result["results"],
            "model": request.model
        }
    
    except Exception as e:
        logger.error(f"Reranking error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)