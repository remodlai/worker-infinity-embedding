export interface Env {
  EMBEDDING_ENDPOINT: string;
  RERANKER_ENDPOINT: string;
  RUNPOD_API_KEY: string;
  WARMKEEPER_KV: KVNamespace;
}

// Sample queries that mimic real-world usage
const SAMPLE_QUERIES = [
  "What are the best practices for microservices architecture?",
  "How to implement authentication in a web application?",
  "Explain the differences between SQL and NoSQL databases",
  "What is machine learning and how does it work?",
  "How to optimize website performance for better SEO?",
  "What are the key principles of REST API design?",
  "How to handle errors in JavaScript applications?",
  "What is containerization and why use Docker?",
  "Explain event-driven architecture patterns",
  "How to implement caching strategies in web applications?"
];

const SAMPLE_DOCUMENTS = [
  "Microservices architecture involves breaking down applications into small, independent services that communicate via APIs.",
  "Authentication can be implemented using JWT tokens, OAuth, or session-based approaches depending on your needs.",
  "SQL databases use structured schemas and ACID properties, while NoSQL offers flexibility and horizontal scaling.",
  "Machine learning enables computers to learn from data without explicit programming, using algorithms to find patterns.",
  "Website performance optimization includes minifying assets, using CDNs, lazy loading, and optimizing images.",
  "REST APIs should be stateless, use proper HTTP methods, have consistent naming, and include proper error handling.",
  "Error handling in JavaScript involves try-catch blocks, Promise rejection handling, and global error handlers.",
  "Docker containerization packages applications with dependencies, ensuring consistency across different environments.",
  "Event-driven architecture uses events to trigger actions between decoupled services, improving scalability.",
  "Caching strategies include browser caching, CDN caching, application-level caching, and database query caching."
];

// Helper to add random delay between requests
const randomDelay = () => Math.floor(Math.random() * 10000) + 5000; // 5-15 seconds

// Helper to get random items from arrays
const getRandomItem = <T>(array: T[]): T => array[Math.floor(Math.random() * array.length)];
const getRandomItems = <T>(array: T[], count: number): T[] => {
  const shuffled = [...array].sort(() => 0.5 - Math.random());
  return shuffled.slice(0, count);
};

async function warmEmbeddingService(env: Env): Promise<void> {
  const query = getRandomItem(SAMPLE_QUERIES);
  
  try {
    const response = await fetch(env.EMBEDDING_ENDPOINT, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${env.RUNPOD_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        input: {
          openai_route: "/openai/v1/embeddings",
          openai_input: {
            model: "Qwen3-Embedding-0.6B",
            input: query,
            extra_body: {
              prompt_type: "query"
            }
          }
        }
      }),
    });

    if (!response.ok) {
      console.error(`Embedding warmup failed: ${response.status} ${response.statusText}`);
    } else {
      console.log(`Embedding service warmed with query: "${query.substring(0, 50)}..."`);
    }
  } catch (error) {
    console.error('Failed to warm embedding service:', error);
  }
}

async function warmRerankerService(env: Env): Promise<void> {
  const query = getRandomItem(SAMPLE_QUERIES);
  const documents = getRandomItems(SAMPLE_DOCUMENTS, 3);
  
  try {
    const response = await fetch(env.RERANKER_ENDPOINT, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${env.RUNPOD_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        input: {
          openai_route: "/v1/rerank",
          openai_input: {
            query: query,
            documents: documents,
            return_documents: false,
            top_k: 2
          }
        }
      }),
    });

    if (!response.ok) {
      console.error(`Reranker warmup failed: ${response.status} ${response.statusText}`);
    } else {
      console.log(`Reranker service warmed with query: "${query.substring(0, 50)}..."`);
    }
  } catch (error) {
    console.error('Failed to warm reranker service:', error);
  }
}

export default {
  // Scheduled handler - runs on cron schedule
  async scheduled(event: ScheduledEvent, env: Env, ctx: ExecutionContext): Promise<void> {
    console.log(`Warmkeeper triggered at ${new Date(event.scheduledTime).toISOString()}`);
    
    // Check which services are active
    const embeddingConfig = await env.WARMKEEPER_KV.get('config:embedding', 'json') || { active: true };
    const rerankerConfig = await env.WARMKEEPER_KV.get('config:rerank', 'json') || { active: true };
    
    const activeServices = [];
    if (embeddingConfig.active) activeServices.push('embedding');
    if (rerankerConfig.active) activeServices.push('rerank');
    
    if (activeServices.length === 0) {
      console.log('No services active for warming');
      return;
    }
    
    // Update response times helper
    const updateResponseTime = async (service: string, responseTime: number) => {
      const config = await env.WARMKEEPER_KV.get(`config:${service}`, 'json') || {};
      const avgTime = config.avgResponseTime || responseTime;
      const newAvg = (avgTime * 0.8) + (responseTime * 0.2); // Weighted average
      
      await env.WARMKEEPER_KV.put(`config:${service}`, JSON.stringify({
        ...config,
        avgResponseTime: newAvg,
        lastRun: new Date().toISOString()
      }));
    };
    
    // Warm services in random order
    const shuffled = activeServices.sort(() => 0.5 - Math.random());
    
    for (const service of shuffled) {
      const startTime = Date.now();
      
      if (service === 'embedding') {
        await warmEmbeddingService(env);
        await updateResponseTime('embedding', Date.now() - startTime);
      } else if (service === 'rerank') {
        await warmRerankerService(env);
        await updateResponseTime('rerank', Date.now() - startTime);
      }
      
      // Random delay between services
      if (shuffled.indexOf(service) < shuffled.length - 1) {
        await new Promise(resolve => setTimeout(resolve, randomDelay()));
      }
    }
    
    // Sometimes skip one service (10% chance each) - but only if both are active
    if (activeServices.length === 2) {
      const skipChance = Math.random();
      if (skipChance < 0.1) {
        console.log('Randomly skipping embedding warmup this cycle');
      } else if (skipChance < 0.2) {
        console.log('Randomly skipping reranker warmup this cycle');
      }
    }
  },

  // HTTP handler - for manual triggering or status checks
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    const pathname = url.pathname;
    
    // Helper to get service config from KV
    const getServiceConfig = async (service: string) => {
      const config = await env.WARMKEEPER_KV.get(`config:${service}`, 'json') || {
        active: true,
        lastRun: null,
        avgResponseTime: null
      };
      return config;
    };
    
    // Helper to set service config in KV
    const setServiceConfig = async (service: string, config: any) => {
      await env.WARMKEEPER_KV.put(`config:${service}`, JSON.stringify(config));
    };
    
    // Embedding service endpoints
    if (pathname === '/api/utilities/serverless/embedding/start' && request.method === 'POST') {
      await setServiceConfig('embedding', { ...await getServiceConfig('embedding'), active: true });
      
      // Trigger warmup immediately
      ctx.waitUntil(warmEmbeddingService(env));
      
      return new Response(JSON.stringify({
        status: 'started',
        service: 'embedding',
        message: 'Warmkeeper started for embedding service',
        timestamp: new Date().toISOString()
      }), {
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    if (pathname === '/api/utilities/serverless/embedding/stop' && request.method === 'POST') {
      await setServiceConfig('embedding', { ...await getServiceConfig('embedding'), active: false });
      
      return new Response(JSON.stringify({
        status: 'stopped',
        service: 'embedding',
        message: 'Warmkeeper stopped for embedding service',
        timestamp: new Date().toISOString()
      }), {
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    if (pathname === '/api/utilities/serverless/embedding/status' && request.method === 'GET') {
      const config = await getServiceConfig('embedding');
      
      return new Response(JSON.stringify({
        service: 'embedding',
        warmkeeper: {
          active: config.active,
          lastRun: config.lastRun,
          nextRun: config.active ? new Date(Date.now() + 4 * 60 * 1000).toISOString() : null
        },
        endpoint: env.EMBEDDING_ENDPOINT,
        avgResponseTime: config.avgResponseTime,
        timestamp: new Date().toISOString()
      }), {
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    // Reranker service endpoints
    if (pathname === '/api/utilities/serverless/rerank/start' && request.method === 'POST') {
      await setServiceConfig('rerank', { ...await getServiceConfig('rerank'), active: true });
      
      // Trigger warmup immediately
      ctx.waitUntil(warmRerankerService(env));
      
      return new Response(JSON.stringify({
        status: 'started',
        service: 'rerank',
        message: 'Warmkeeper started for reranker service',
        timestamp: new Date().toISOString()
      }), {
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    if (pathname === '/api/utilities/serverless/rerank/stop' && request.method === 'POST') {
      await setServiceConfig('rerank', { ...await getServiceConfig('rerank'), active: false });
      
      return new Response(JSON.stringify({
        status: 'stopped',
        service: 'rerank',
        message: 'Warmkeeper stopped for reranker service',
        timestamp: new Date().toISOString()
      }), {
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    if (pathname === '/api/utilities/serverless/rerank/status' && request.method === 'GET') {
      const config = await getServiceConfig('rerank');
      
      return new Response(JSON.stringify({
        service: 'rerank',
        warmkeeper: {
          active: config.active,
          lastRun: config.lastRun,
          nextRun: config.active ? new Date(Date.now() + 4 * 60 * 1000).toISOString() : null
        },
        endpoint: env.RERANKER_ENDPOINT,
        avgResponseTime: config.avgResponseTime,
        timestamp: new Date().toISOString()
      }), {
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    return new Response('Not Found', { status: 404 });
  },
};