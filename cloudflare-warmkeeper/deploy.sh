#!/bin/bash

# Cloudflare Warmkeeper Deployment Script

echo "🚀 Deploying LexIQ Vectors Warmkeeper to Cloudflare..."

# Check if we're in the right directory
if [ ! -f "wrangler.toml" ]; then
    echo "❌ Error: wrangler.toml not found. Please run from the cloudflare-warmkeeper directory."
    exit 1
fi

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Check if RUNPOD_API_KEY is set
echo ""
echo "🔑 Setting up RUNPOD_API_KEY secret..."
echo "You'll be prompted to enter your RunPod API key."
echo "Get your API key from: https://www.runpod.io/console/user/settings"
echo ""

wrangler secret put RUNPOD_API_KEY

# Deploy the worker
echo ""
echo "🚀 Deploying worker..."
wrangler deploy

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 View your worker at: https://dash.cloudflare.com/"
echo "📝 Check logs with: wrangler tail"
echo ""
echo "🔧 The warmkeeper will run automatically every 4 minutes."
echo "    You can also trigger it manually via the API endpoints."