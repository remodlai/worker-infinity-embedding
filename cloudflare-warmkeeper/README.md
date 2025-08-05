# LexIQ Vectors Warmkeeper

A Cloudflare Worker that keeps LexIQ Vectors services warm to maintain sub-200ms response times.

## Overview

This worker prevents cold starts on RunPod serverless endpoints by sending periodic requests that mimic real-world usage patterns. It runs on a cron schedule and provides API endpoints for manual control.

## Features

- **Automated Warming**: Runs every 4 minutes via Cloudflare cron trigger
- **Randomized Patterns**: Mimics natural traffic with random delays and query variations
- **Individual Service Control**: Start/stop warming for embedding and reranking services independently
- **Performance Tracking**: Monitors average response times using weighted averages
- **Manual Triggers**: API endpoints for on-demand warming
- **KV State Management**: Persists configuration across worker restarts

## Setup

### 1. Create KV Namespace

```bash
wrangler kv:namespace create "WARMKEEPER_KV"
```

Update `wrangler.toml` with the generated namespace ID.

### 2. Set Secrets

```bash
wrangler secret put RUNPOD_API_KEY
# Enter your RunPod API key when prompted
```

### 3. Deploy

```bash
npm install
wrangler deploy
```

## API Endpoints

All endpoints are accessed through the Zuplo API Gateway at `https://api.lexiq.dev`.

### Embedding Service Control

```bash
# Start warmkeeper for embedding service
POST /api/utilities/serverless/embedding/start

# Stop warmkeeper for embedding service  
POST /api/utilities/serverless/embedding/stop

# Get embedding service status
GET /api/utilities/serverless/embedding/status
```

### Reranker Service Control

```bash
# Start warmkeeper for reranker service
POST /api/utilities/serverless/rerank/start

# Stop warmkeeper for reranker service
POST /api/utilities/serverless/rerank/stop

# Get reranker service status
GET /api/utilities/serverless/rerank/status
```

### Example Responses

#### Status Response
```json
{
  "service": "embedding",
  "warmkeeper": {
    "active": true,
    "lastRun": "2025-01-05T10:30:00Z",
    "nextRun": "2025-01-05T10:34:00Z"
  },
  "endpoint": "https://api.runpod.ai/v2/ejt982twe0i4dw/runsync",
  "avgResponseTime": 145.5,
  "timestamp": "2025-01-05T10:31:00Z"
}
```

## How It Works

### Warming Strategy

1. **Scheduled Execution**: Cron trigger runs every 4 minutes
2. **Service Check**: Only warms services marked as active in KV storage
3. **Random Order**: Services are warmed in random order
4. **Natural Delays**: 5-15 second random delays between requests
5. **Query Variation**: Uses rotating sample queries to avoid detection
6. **Skip Logic**: 10% chance to skip each service per cycle

### Sample Data

The worker uses realistic queries and documents:
- 10 different query patterns covering common use cases
- 10 document samples for reranking tests
- Randomized selection on each request

### Performance Tracking

- Response times tracked using exponential weighted moving average
- 80% weight on historical average, 20% on new measurement
- Persisted in KV storage for monitoring

## Cost Analysis

Assuming both services active 24/7:
- Requests per day: ~720 (360 per service)
- Average execution time: 150ms
- Total compute time: ~108 seconds/day
- Estimated cost: ~$0.45/month

## Monitoring

View logs in real-time:
```bash
wrangler tail
```

Check cron execution history in Cloudflare dashboard:
1. Go to Workers & Pages
2. Select `lexiq-vectors-warmkeeper`
3. View "Triggers" tab for cron history

## Development

```bash
# Local development (without cron triggers)
npm run dev

# Deploy to production
npm run deploy

# View logs
npm run tail
```

## Configuration

Edit `wrangler.toml` to adjust:
- Cron schedule (default: `*/4 * * * *`)
- Endpoint URLs
- Environment variables

## Integration with Zuplo

The worker integrates with Zuplo API Gateway which:
1. Handles authentication
2. Routes requests to the appropriate worker endpoints
3. Provides OpenAPI documentation
4. Manages rate limiting and security

## Troubleshooting

### Services Not Warming
1. Check service status via API
2. Verify RUNPOD_API_KEY is set correctly
3. Check worker logs for errors

### High Response Times
1. Services may be scaling up
2. Check RunPod dashboard for worker health
3. Consider increasing warmup frequency

### KV Errors
1. Ensure KV namespace is properly bound
2. Check namespace ID in wrangler.toml
3. Verify KV has sufficient storage