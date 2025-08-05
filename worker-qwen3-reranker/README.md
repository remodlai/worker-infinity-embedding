# LexIQ Vectors - Reranker Service

**Advanced Document Reranking for LexIQ Platform by Remodl AI**

<p align="center">
  <img src="https://img.shields.io/badge/Platform-LexIQ-blue" alt="Platform">
  <img src="https://img.shields.io/badge/Model-Qwen3--Reranker-green" alt="Model">
  <img src="https://img.shields.io/badge/API-OpenAI%20Compatible-orange" alt="API">
</p>

---

## Overview

The LexIQ Vectors Reranker is a high-performance document reranking service that optimizes search results using the state-of-the-art Qwen3-Reranker-0.6B model. Built by Remodl AI, Inc., it seamlessly integrates with the LexIQ platform to provide enterprise-grade search result optimization.

### Key Features

- **⚡ Lightning Fast**: 130-180ms reranking latency when warm
- **🎯 High Accuracy**: State-of-the-art reranking quality (MTEB-R: 65.80)
- **🌐 Multilingual**: Supports 100+ languages out of the box
- **📝 Instruction-Aware**: Custom instructions for domain-specific ranking
- **🔄 OpenAI Compatible**: Seamless integration with existing workflows
- **🚀 GPU Optimized**: CUDA acceleration with optional Flash Attention 2

---

## Production Endpoint

### Base URL
```
https://api.lexiq.dev
```

### Reranking Endpoint
```
POST /openai/v1/rerank
```

---

## Quick Start

### Using Python Requests

```python
import requests

response = requests.post(
    "https://api.lexiq.dev/openai/v1/rerank",
    headers={
        "Authorization": "Bearer your-lexiq-api-key",
        "Content-Type": "application/json"
    },
    json={
        "query": "What product has the best warranty?",
        "documents": [
            "Product A: 2-year comprehensive warranty covering all parts",
            "Product B: Lifetime limited warranty on manufacturing defects",
            "Product C: 90-day warranty with no coverage extensions",
            "Product D: 5-year extended warranty options available",
            "Product E: 1-year warranty with free shipping for repairs"
        ],
        "return_documents": True,
        "top_k": 3
    }
)

# Display ranked results
for result in response.json()["results"]:
    print(f"Score: {result['score']:.3f} - {result['document']}")
```

### Expected Output
```
Score: 0.996 - Product D: 5-year extended warranty options available
Score: 0.979 - Product E: 1-year warranty with free shipping for repairs
Score: 0.944 - Product A: 2-year comprehensive warranty covering all parts
```

---

## Advanced Usage

### Custom Instructions

Optimize reranking for specific domains:

```python
# E-commerce product search
response = requests.post(
    "https://api.lexiq.dev/openai/v1/rerank",
    headers={"Authorization": "Bearer your-key"},
    json={
        "query": "gaming laptop with good cooling",
        "documents": product_descriptions,
        "extra_body": {
            "instruction": "Focus on gaming performance and thermal management features"
        },
        "top_k": 10
    }
)

# Academic paper search
response = requests.post(
    "https://api.lexiq.dev/openai/v1/rerank",
    headers={"Authorization": "Bearer your-key"},
    json={
        "query": "transformer architectures in NLP",
        "documents": paper_abstracts,
        "extra_body": {
            "instruction": "Prioritize recent research papers with novel contributions"
        },
        "top_k": 20
    }
)
```

### Integration with LexIQ Embeddings

Complete search pipeline example:

```python
from openai import OpenAI
import requests

# Initialize embedding client
embed_client = OpenAI(
    api_key="your-lexiq-api-key",
    base_url="https://api.lexiq.dev/openai"
)

# Step 1: Embed the query
query = "best practices for microservices architecture"
query_embedding = embed_client.embeddings.create(
    model="Qwen3-Embedding-0.6B",
    input=query,
    extra_body={"prompt_type": "query"}
).data[0].embedding

# Step 2: Vector search (your database)
candidates = vector_db.search(
    vector=query_embedding,
    top_k=100  # Get more candidates for reranking
)

# Step 3: Rerank the results
reranked = requests.post(
    "https://api.lexiq.dev/openai/v1/rerank",
    headers={"Authorization": "Bearer your-key"},
    json={
        "query": query,
        "documents": [doc.text for doc in candidates],
        "top_k": 10,
        "return_documents": True
    }
)

# Step 4: Return optimized results
final_results = reranked.json()["results"]
```

---

## API Reference

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | The search query to rank documents against |
| `documents` | array[string] | Yes | List of documents to rerank (max 1000) |
| `return_documents` | boolean | No | If true, include documents in response (default: false) |
| `top_k` | integer | No | Number of top results to return (default: all) |
| `extra_body.instruction` | string | No | Custom instruction for domain-specific ranking |

### Response Format

```json
{
  "results": [
    {
      "index": 3,
      "score": 0.996,
      "document": "Product D: 5-year extended warranty options available"
    },
    {
      "index": 4,
      "score": 0.979,
      "document": "Product E: 1-year warranty with free shipping for repairs"
    }
  ],
  "model": "Qwen3-Reranker-0.6B",
  "query": "What product has the best warranty?"
}
```

---

## Performance Optimization

### Batch Processing

Process multiple queries efficiently:

```python
# Rerank multiple queries in parallel
import asyncio
import aiohttp

async def rerank_query(session, query, documents):
    async with session.post(
        "https://api.lexiq.dev/openai/v1/rerank",
        headers={"Authorization": "Bearer your-key"},
        json={
            "query": query,
            "documents": documents,
            "top_k": 10
        }
    ) as response:
        return await response.json()

async def batch_rerank(queries_and_docs):
    async with aiohttp.ClientSession() as session:
        tasks = [
            rerank_query(session, q, d) 
            for q, d in queries_and_docs
        ]
        return await asyncio.gather(*tasks)

# Usage
results = asyncio.run(batch_rerank([
    ("query1", ["doc1", "doc2", "doc3"]),
    ("query2", ["doc4", "doc5", "doc6"]),
]))
```

### Keep Workers Warm

For consistent sub-200ms performance:

```python
# Simple warm-keeping script
import time
import random
import requests

def keep_warm():
    while True:
        # Random delay 3-5 minutes
        delay = random.randint(180, 300)
        
        # Simple rerank request
        requests.post(
            "https://api.lexiq.dev/openai/v1/rerank",
            headers={"Authorization": "Bearer your-key"},
            json={
                "query": "test query",
                "documents": ["doc1", "doc2"],
                "top_k": 1
            }
        )
        
        time.sleep(delay)
```

---

## Technical Details

### How It Works

1. **Instruction Formatting**: Combines instruction, query, and document into Qwen3's specific format
2. **Yes/No Prediction**: Model predicts if each document answers the query
3. **Score Calculation**: Compares "yes" vs "no" token logits to generate relevance scores
4. **Ranking**: Documents sorted by score in descending order

### Model Specifications

- **Architecture**: Qwen3 Causal Language Model
- **Parameters**: 0.6B
- **Context Length**: 32,768 tokens
- **Languages**: 100+ supported
- **Precision**: FP16 (configurable)

### Infrastructure

- **GPU**: NVIDIA RTX 4090 or better
- **Memory**: 2-3GB GPU memory required
- **Runtime**: RunPod Serverless Workers
- **Container**: Docker with CUDA 12.4.1

---

## Error Handling

All errors follow OpenAI's error format:

```json
{
  "error": {
    "message": "Missing required field: query",
    "type": "invalid_request_error",
    "code": "missing_field"
  }
}
```

### Common Errors

| Error Type | Description | Solution |
|------------|-------------|----------|
| `invalid_request_error` | Missing or invalid parameters | Check request format |
| `authentication_error` | Invalid API key | Verify your LexIQ API key |
| `rate_limit_error` | Too many requests | Implement exponential backoff |
| `internal_error` | Server error | Retry with backoff |

---

## Support

- **Documentation**: https://docs.lexiq.dev/vectors/reranking
- **API Status**: https://status.lexiq.dev
- **Support**: support@remodlai.com
- **Issues**: https://github.com/remodlai/lexiq-vectors/issues

---

## About Remodl AI

Remodl AI, Inc. is building the next generation of AI infrastructure. LexIQ Vectors Reranker is part of our commitment to providing production-ready, scalable AI services that developers can rely on.

---

<p align="center">
  <i>Built with ❤️ by Remodl AI, Inc.</i>
</p>