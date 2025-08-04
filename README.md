![Infinity Embedding Worker Banner](https://cpjrphpz3t5wbwfe.public.blob.vercel-storage.com/worker-infinity-embedding_banner-9n86vTARpwknMZYnXHAUr7xJisiWXs.jpeg)

---

High-throughput, OpenAI-compatible text embedding & reranker powered by [Infinity](https://github.com/michaelfeil/infinity) with **Qwen3** models

**Now with instruction-aware embeddings for improved search performance!**

---

[![RunPod](https://api.runpod.io/badge/runpod-workers/worker-infinity-embedding)](https://www.runpod.io/console/hub/runpod-workers/worker-infinity-embedding)

---

1. [Quickstart](#quickstart)
2. [Endpoint Configuration](#endpoint-configuration)
3. [API Specification](#api-specification)
   1. [List Models](#list-models)
   2. [Create Embeddings](#create-embeddings)
   3. [Rerank Documents](#rerank-documents)
4. [Usage](#usage)
5. [Further Documentation](#further-documentation)
6. [Acknowledgements](#acknowledgements)

---

## Quickstart

1. 🐳 **Use our image** – `ghcr.io/remodlai/worker-infinity-embedding:qwen3-0.6B-unified-v6`
2. 🔧 **Configure** – Pre-configured with Qwen3-Embedding-0.6B and Qwen3-Reranker-0.6B
3. 🚀 **Deploy** – create a [RunPod Serverless endpoint](https://docs.runpod.io/serverless/endpoints/manage-endpoints)
4. 🧪 **Call the API** – follow the examples in the [Usage](#usage) section

---

## Pre-configured Models

This worker comes pre-configured with:
- **Qwen3-Embedding-0.6B**: State-of-the-art multilingual embeddings (1024 dimensions)
- **Qwen3-Reranker-0.6B**: High-quality reranking model for search result optimization

Both models support over 100 languages and have been optimized for search and retrieval tasks.

## Endpoint Configuration

All behaviour is controlled through environment variables:

| Variable                 | Required | Default | Description                                                                                                      |
| ------------------------ | -------- | ------- | ---------------------------------------------------------------------------------------------------------------- |
| `MODEL_NAMES`            | **Yes**  | —       | One or more Hugging-Face model IDs. Separate multiple IDs with a semicolon.<br>Example: `BAAI/bge-small-en-v1.5` |
| `BATCH_SIZES`            | No       | `32`    | Per-model batch size; semicolon-separated list matching `MODEL_NAMES`.                                           |
| `BACKEND`                | No       | `torch` | Inference engine for _all_ models: `torch`, `optimum`, or `ctranslate2`.                                         |
| `DTYPES`                 | No       | `auto`  | Precision per model (`auto`, `fp16`, `fp8`). Semicolon-separated, must match `MODEL_NAMES`.                      |
| `INFINITY_QUEUE_SIZE`    | No       | `48000` | Max items queueable inside the Infinity engine.                                                                  |
| `RUNPOD_MAX_CONCURRENCY` | No       | `300`   | Max concurrent requests the RunPod wrapper will accept.                                                          |

---

## API Specification

Two flavours, one schema.

- **OpenAI-compatible** – drop-in replacement for `/v1/models`, `/v1/embeddings`, so you can use this endpoint instead of the API from OpenAI by replacing the base url with the URL of your endpoint: `https://api.runpod.ai/v2/<ENDPOINT_ID>/openai/v1` and use your [API key from RunPod](https://docs.runpod.io/get-started/api-keys) instead of the one from OpenAI
- **Standard RunPod** – call `/run` or `/runsync` with a JSON body under the `input` key.  
  Base URL: `https://api.runpod.ai/v2/<ENDPOINT_ID>`

Except for transport (path + wrapper object) the JSON you send/receive is identical. The tables below describe the shared payload.

### List Models

| Method | Path                | Body                                            |
| ------ | ------------------- | ----------------------------------------------- |
| `GET`  | `/openai/v1/models` | –                                               |
| `POST` | `/runsync`          | `{ "input": { "openai_route": "/v1/models" } }` |

#### Response

```jsonc
{
  "data": [
    { "id": "BAAI/bge-small-en-v1.5", "stats": {} },
    { "id": "intfloat/e5-large-v2", "stats": {} }
  ]
}
```

---

### Create Embeddings

#### Request Fields (shared)

| Field   | Type                | Required | Description                                       |
| ------- | ------------------- | -------- | ------------------------------------------------- |
| `model` | string              | **Yes**  | One of the IDs supplied via `MODEL_NAMES`.        |
| `input` | string &#124; array | **Yes**  | A single text string _or_ list of texts to embed. |
| `instruction` | string         | No       | Custom instruction to prepend (for instruction-aware models) |
| `prompt_type` | string         | No       | Use built-in prompts: `"query"` or `"document"` |

**Note:** For OpenAI-compatible endpoints, pass `instruction` and `prompt_type` inside `extra_body`.

OpenAI route vs. Standard:

| Flavour  | Method | Path             | Body                                          |
| -------- | ------ | ---------------- | --------------------------------------------- |
| OpenAI   | `POST` | `/v1/embeddings` | `{ "model": "…", "input": "…" }`              |
| Standard | `POST` | `/runsync`       | `{ "input": { "model": "…", "input": "…" } }` |

#### Response (both flavours)

```jsonc
{
  "object": "list",
  "model": "BAAI/bge-small-en-v1.5",
  "data": [
    { "object": "embedding", "embedding": [0.01, -0.02 /* … */], "index": 0 }
  ],
  "usage": { "prompt_tokens": 2, "total_tokens": 2 }
}
```

---

### Rerank Documents (Standard only)

| Field         | Type   | Required | Description                                                       |
| ------------- | ------ | -------- | ----------------------------------------------------------------- |
| `model`       | string | **Yes**  | Any deployed reranker model                                       |
| `query`       | string | **Yes**  | The search/query text                                             |
| `docs`        | array  | **Yes**  | List of documents to rerank                                       |
| `return_docs` | bool   | No       | If `true`, return the documents in ranked order (default `false`) |

Call pattern

```http
POST /runsync
Content-Type: application/json

{
  "input": {
    "model": "BAAI/bge-reranker-large",
    "query": "Which product has warranty coverage?",
    "docs": [
      "Product A comes with a 2-year warranty",
      "Product B is available in red and blue colors",
      "All electronics include a standard 1-year warranty"
    ],
    "return_docs": true
  }
}
```

Response contains either `scores` or the full `docs` list, depending on `return_docs`.

---

## Instruction-Aware Embeddings (Qwen3)

Qwen3 models support instruction-aware embeddings that can improve search performance by 1-5%. Use different instructions for queries vs documents:

### For Search Queries
```json
{
  "instruction": "Given a web search query, retrieve relevant passages that answer the query",
  "prompt_type": "query"
}
```

### For Documents
Documents typically don't need instructions (use raw text for best results).

### Custom Instructions
You can provide task-specific instructions:
- **Academic Search**: "Represent this query for finding research papers"
- **Code Search**: "Represent this query for finding code examples"
- **FAQ Search**: "Represent this question for finding answers in documentation"

## Usage

Below are minimal `curl` snippets so you can copy-paste from any machine.

> Replace `<ENDPOINT_ID>` with your endpoint ID and `<API_KEY>` with a [RunPod API key](https://docs.runpod.io/get-started/api-keys).

### OpenAI-Compatible Calls

```bash
# List models
curl -H "Authorization: Bearer <API_KEY>" \
     https://api.runpod.ai/v2/<ENDPOINT_ID>/openai/v1/models

# Create embeddings (basic)
curl -X POST \
  -H "Authorization: Bearer <API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"model":"/models/Qwen3-Embedding-0.6B","input":"Hello world"}' \
  https://api.runpod.ai/v2/<ENDPOINT_ID>/openai/v1/embeddings

# Create embeddings with instruction (for search queries)
curl -X POST \
  -H "Authorization: Bearer <API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "model":"/models/Qwen3-Embedding-0.6B",
    "input":"What is machine learning?",
    "extra_body":{
      "prompt_type":"query"
    }
  }' \
  https://api.runpod.ai/v2/<ENDPOINT_ID>/openai/v1/embeddings
```

### Standard RunPod Calls

```bash
# Create embeddings (basic)
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"input":{"model":"/models/Qwen3-Embedding-0.6B","input":"Hello world"}}' \
  https://api.runpod.ai/v2/<ENDPOINT_ID>/runsync

# Create embeddings with instruction
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "input":{
      "model":"/models/Qwen3-Embedding-0.6B",
      "input":"What is machine learning?",
      "instruction":"Given a web search query, retrieve relevant passages that answer the query"
    }
  }' \
  https://api.runpod.ai/v2/<ENDPOINT_ID>/runsync

# Rerank
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "input":{
      "model":"/models/Qwen3-Reranker-0.6B",
      "query":"Which product has warranty coverage?",
      "docs":[
        "Product A comes with a 2-year warranty",
        "Product B is available in red and blue colors",
        "All electronics include a standard 1-year warranty"
      ],
      "return_docs":true
    }
  }' \
  https://api.runpod.ai/v2/<ENDPOINT_ID>/runsync
```

---

## Further Documentation

- **[Infinity Engine](https://github.com/michaelfeil/infinity)** – how the ultra-fast backend works.
- **[RunPod Docs](https://docs.runpod.io/)** – serverless concepts, limits, and API reference.

---

## Acknowledgements

Special thanks to [Michael Feil](https://github.com/michaelfeil) for creating the Infinity engine and for his ongoing support of this project.
