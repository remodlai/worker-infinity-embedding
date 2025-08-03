"""
Reranker Model Server
Serves Qwen3-Reranker-0.6B model via FastAPI
"""

import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Tuple
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Model configuration
MODEL_PATH = "/models/Qwen3-Reranker-0.6B"
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load model on startup
model = None
tokenizer = None

@app.on_event("startup")
async def load_model():
    global model, tokenizer
    logger.info(f"Loading reranker model from {MODEL_PATH}")
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
        model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH).to(device)
        model.eval()
        logger.info(f"Model loaded successfully on {device}")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

class RerankRequest(BaseModel):
    query: str
    documents: List[str]
    top_k: int = 10

class RerankResponse(BaseModel):
    results: List[Tuple[int, float]]  # (index, score) pairs

@app.get("/health")
async def health():
    return {"status": "healthy", "model": "Qwen3-Reranker-0.6B", "device": str(device)}

@app.post("/rerank")
async def rerank(request: RerankRequest):
    if not model:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        scores = []
        
        with torch.no_grad():
            # Score each document against the query
            for i, doc in enumerate(request.documents):
                inputs = tokenizer(
                    request.query,
                    doc,
                    return_tensors="pt",
                    padding=True,
                    truncation=True,
                    max_length=512
                ).to(device)
                
                outputs = model(**inputs)
                score = outputs.logits[0].item()  # Get relevance score
                scores.append((i, score))
        
        # Sort by score descending and return top_k
        scores.sort(key=lambda x: x[1], reverse=True)
        top_results = scores[:request.top_k]
        
        return RerankResponse(results=top_results)
    
    except Exception as e:
        logger.error(f"Reranking error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)