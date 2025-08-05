# LexIQ Vectors

**Production-Ready Text Embeddings & Reranking API by Remodl AI**

<p align="center">
  <img src="https://img.shields.io/badge/Platform-LexIQ-blue" alt="Platform">
  <img src="https://img.shields.io/badge/Models-Qwen3-green" alt="Models">
  <img src="https://img.shields.io/badge/API-OpenAI%20Compatible-orange" alt="API">
</p>

---

## Overview

LexIQ Vectors is a high-performance text embedding and reranking service developed by Remodl AI, Inc. It provides state-of-the-art multilingual text embeddings and document reranking through an OpenAI-compatible API, powered by Qwen3 models optimized for search and retrieval tasks.

### Key Features

- **🚀 Ultra-Fast Performance**: Sub-200ms response times when warm
- **🌐 100+ Languages**: Full multilingual support out of the box
- **🔍 Instruction-Aware**: Boost search quality by 1-5% with custom instructions
- **🔄 OpenAI Compatible**: Drop-in replacement for OpenAI embeddings
- **📊 Advanced Reranking**: Optimize search results with state-of-the-art reranking
- **🏗️ Enterprise Ready**: Built on RunPod serverless infrastructure for scale

---

## Tech Stack

- **Models**: Qwen3-Embedding-0.6B & Qwen3-Reranker-0.6B
- **Infrastructure**: RunPod Serverless GPU Workers
- **Engine**: Infinity (high-throughput inference)
- **API**: OpenAI-compatible REST endpoints
- **Container**: Docker with CUDA 12.4.1 support

---

## API Endpoints

### Production Base URL
```
https://api.lexiq.dev
```

### Available Endpoints

- `POST /openai/v1/models` - List available models
- `POST /openai/v1/embeddings` - Generate embeddings
- `POST /openai/v1/rerank` - Rerank documents

---

## Quick Start

### Using OpenAI SDK

```python
from openai import OpenAI

# Initialize client
client = OpenAI(
    api_key="your-lexiq-api-key",
    base_url="https://api.lexiq.dev/openai"
)

# Generate embeddings
response = client.embeddings.create(
    model="Qwen3-Embedding-0.6B",
    input="What is machine learning?",
    extra_body={
        "prompt_type": "query"  # Optimize for search queries
    }
)

embedding = response.data[0].embedding
```

### Using Requests

```python
import requests

# Generate embeddings
response = requests.post(
    "https://api.lexiq.dev/openai/v1/embeddings",
    headers={
        "Authorization": "Bearer your-lexiq-api-key",
        "Content-Type": "application/json"
    },
    json={
        "model": "Qwen3-Embedding-0.6B",
        "input": "What is machine learning?",
        "extra_body": {
            "prompt_type": "query"
        }
    }
)

embedding = response.json()["data"][0]["embedding"]
```

---

## Advanced Usage

### Instruction-Aware Embeddings

Improve search quality by using different instructions for queries vs documents:

#### For Search Queries
```python
# Using built-in optimization
embedding = client.embeddings.create(
    model="Qwen3-Embedding-0.6B",
    input="How to implement neural networks?",
    extra_body={
        "prompt_type": "query"
    }
)

# Or with custom instruction
embedding = client.embeddings.create(
    model="Qwen3-Embedding-0.6B",
    input="How to implement neural networks?",
    extra_body={
        "instruction": "Represent this programming question for finding code examples"
    }
)
```

#### For Documents
```python
# Documents typically don't need instructions
embedding = client.embeddings.create(
    model="Qwen3-Embedding-0.6B",
    input="Neural networks are a fundamental component of deep learning..."
)
```

### Document Reranking

Optimize search results by reranking documents based on relevance:

```python
# Rerank documents with default instruction
response = requests.post(
    "https://api.lexiq.dev/openai/v1/rerank",
    headers={
        "Authorization": "Bearer your-lexiq-api-key",
        "Content-Type": "application/json"
    },
    json={
        "query": "What product has the best warranty?",
        "documents": [
            "Product A: 2-year comprehensive warranty",
            "Product B: Lifetime limited warranty", 
            "Product C: 90-day warranty",
            "Product D: 5-year extended warranty available"
        ],
        "return_documents": True,
        "top_k": 3
    }
)

# Or with custom instruction
response = requests.post(
    "https://api.lexiq.dev/openai/v1/rerank",
    headers={
        "Authorization": "Bearer your-lexiq-api-key",
        "Content-Type": "application/json"
    },
    json={
        "query": "What product has the best warranty?",
        "documents": [...],
        "extra_body": {
            "instruction": "Find products with the longest warranty duration and best coverage terms"
        },
        "return_documents": True,
        "top_k": 3
    }
)

# Results are sorted by relevance score
for result in response.json()["results"]:
    print(f"Score: {result['score']:.3f} - {result['document']}")
```

---

## Performance

### Response Times
- **Cold Start**: 10-15 seconds (model loading)
- **Warm Requests**: 100-200ms (embeddings), 130-180ms (reranking)
- **Throughput**: Up to 300 concurrent requests

### Model Specifications
- **Embedding Dimensions**: 1024
- **Max Sequence Length**: 32,768 tokens
- **Batch Processing**: Optimized for batches up to 32

---

## Best Practices

### 1. Use Appropriate Instructions
- **Search Queries**: Always use `prompt_type: "query"` or custom search instructions
- **Documents**: Use raw text without instructions for best results
- **Domain-Specific**: Create custom instructions for specialized use cases

### 2. Batch Processing
```python
# Process multiple texts in one request
embeddings = client.embeddings.create(
    model="Qwen3-Embedding-0.6B",
    input=[
        "First document",
        "Second document",
        "Third document"
    ]
)
```

### 3. Combine Embedding + Reranking
```python
# Step 1: Embed query
query_embedding = client.embeddings.create(
    model="Qwen3-Embedding-0.6B",
    input="user search query",
    extra_body={"prompt_type": "query"}
)

# Step 2: Vector search in your database
candidates = vector_db.search(query_embedding, top_k=100)

# Step 3: Rerank top candidates
reranked = requests.post(
    "https://api.lexiq.dev/openai/v1/rerank",
    headers={"Authorization": "Bearer your-key"},
    json={
        "query": "user search query",
        "documents": candidates,
        "top_k": 10
    }
)
```

---

## Custom Instructions Examples

### Academic Search
```python
extra_body={
    "instruction": "Represent this query for finding academic research papers"
}
```

### Code Search
```python
extra_body={
    "instruction": "Represent this query for finding code implementations and examples"
}
```

### Product Search
```python
extra_body={
    "instruction": "Represent this query for e-commerce product search"
}
```

### FAQ/Support
```python
extra_body={
    "instruction": "Represent this question for finding answers in documentation"
}
```

---

## Error Handling

All errors follow the OpenAI error format:

```json
{
  "error": {
    "message": "Model not found",
    "type": "invalid_request_error",
    "code": "model_not_found"
  }
}
```

Common error types:
- `invalid_request_error` - Invalid parameters
- `authentication_error` - Invalid API key
- `rate_limit_error` - Too many requests
- `internal_error` - Server error

---

## Support

- **Documentation**: https://docs.lexiq.dev
- **API Status**: https://status.lexiq.dev
- **Support**: support@remodlai.com

---

## About Remodl AI

Remodl AI, Inc. is dedicated to building production-ready AI infrastructure that scales. LexIQ Vectors is part of the LexIQ platform, providing enterprise-grade AI capabilities for modern applications.

---

<p align="center">
  <i>Built with ❤️ by Remodl AI, Inc.</i>
</p>