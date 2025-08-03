"""
Embedding Model Server
Serves Qwen3-Embedding-0.6B model via FastAPI
"""

import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import torch
from transformers import AutoModel, AutoTokenizer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Model configuration
MODEL_PATH = "/models/Qwen3-Embedding-0.6B"
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load model on startup
model = None
tokenizer = None

@app.on_event("startup")
async def load_model():
    global model, tokenizer
    logger.info(f"Loading embedding model from {MODEL_PATH}")
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
        model = AutoModel.from_pretrained(MODEL_PATH).to(device)
        model.eval()
        logger.info(f"Model loaded successfully on {device}")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

class EmbeddingRequest(BaseModel):
    texts: List[str]

class EmbeddingResponse(BaseModel):
    embeddings: List[List[float]]

@app.get("/health")
async def health():
    return {"status": "healthy", "model": "Qwen3-Embedding-0.6B", "device": str(device)}

@app.post("/embed")
async def embed(request: EmbeddingRequest):
    if not model:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        with torch.no_grad():
            # Tokenize inputs
            inputs = tokenizer(
                request.texts,
                padding=True,
                truncation=True,
                return_tensors="pt"
            ).to(device)
            
            # Generate embeddings
            outputs = model(**inputs)
            embeddings = outputs.last_hidden_state.mean(dim=1)  # Mean pooling
            
            # Convert to list
            embeddings_list = embeddings.cpu().numpy().tolist()
            
        return EmbeddingResponse(embeddings=embeddings_list)
    
    except Exception as e:
        logger.error(f"Embedding error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)