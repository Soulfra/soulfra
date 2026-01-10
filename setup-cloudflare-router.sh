#!/bin/bash
# Setup Cloudflare Workers Router
# Your own router between domains and backends - no third-party dependencies

echo "🌐 Setting up Cloudflare Workers Router..."
echo ""
echo "This creates YOUR router at: https://api.cringeproof.com"
echo "It routes traffic from anywhere to your MacBook backend."
echo ""

# Check if wrangler is installed
if ! command -v wrangler &> /dev/null; then
    echo "📦 Installing Cloudflare Wrangler CLI..."
    npm install -g wrangler
fi

# Login to Cloudflare
echo "🔐 Logging into Cloudflare..."
echo "(This will open a browser window)"
wrangler login

# Create worker directory
mkdir -p cloudflare-router
cd cloudflare-router

# Create wrangler.toml config
cat > wrangler.toml <<'EOF'
name = "cringeproof-api-router"
main = "worker.js"
compatibility_date = "2024-01-01"

# Routes
routes = [
  { pattern = "api.cringeproof.com/*", zone_name = "cringeproof.com" }
]

# Environment variables
[vars]
BACKEND_URL = "https://your-tunnel-url.trycloudflare.com"
EOF

# Create worker.js
cat > worker.js <<'EOF'
/**
 * CringeProof API Router
 *
 * Routes traffic from api.cringeproof.com to your MacBook backend.
 * This is YOUR router - you control the code.
 *
 * Features:
 * - CORS handling
 * - Request logging
 * - Auth middleware (optional)
 * - Rate limiting (optional)
 * - Caching (optional)
 */

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // Log request
    console.log(`[Router] ${request.method} ${url.pathname}`);

    // Handle CORS preflight
    if (request.method === 'OPTIONS') {
      return handleCORS();
    }

    // Get backend URL from environment
    const backendURL = env.BACKEND_URL || 'http://localhost:5001';

    // Build proxied request
    const proxyURL = backendURL + url.pathname + url.search;

    // Forward request to backend
    const proxyRequest = new Request(proxyURL, {
      method: request.method,
      headers: request.headers,
      body: request.body
    });

    try {
      // Send to backend
      const response = await fetch(proxyRequest);

      // Add CORS headers to response
      const corsResponse = new Response(response.body, response);
      corsResponse.headers.set('Access-Control-Allow-Origin', '*');
      corsResponse.headers.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
      corsResponse.headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization');

      return corsResponse;

    } catch (error) {
      console.error('[Router] Backend error:', error);

      return new Response(JSON.stringify({
        error: 'Backend unavailable',
        message: error.message
      }), {
        status: 502,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        }
      });
    }
  }
};

function handleCORS() {
  return new Response(null, {
    status: 204,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      'Access-Control-Max-Age': '86400'
    }
  });
}
EOF

echo ""
echo "✅ Cloudflare Worker created!"
echo ""
echo "📝 Next steps:"
echo ""
echo "1. Update backend URL in wrangler.toml:"
echo "   • Get your tunnel URL: cloudflared tunnel --url https://localhost:5001"
echo "   • Edit cloudflare-router/wrangler.toml"
echo "   • Replace BACKEND_URL with your tunnel URL"
echo ""
echo "2. Deploy worker:"
echo "   cd cloudflare-router"
echo "   wrangler deploy"
echo ""
echo "3. Configure DNS:"
echo "   • Go to Cloudflare dashboard → cringeproof.com → DNS"
echo "   • Add CNAME record: api.cringeproof.com → cringeproof-api-router.workers.dev"
echo ""
echo "4. Test:"
echo "   curl https://api.cringeproof.com/status"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "You now have YOUR OWN ROUTER!"
echo ""
echo "Traffic flow:"
echo "  iPhone → api.cringeproof.com → Cloudflare Worker → Tunnel → MacBook"
echo "                                        ↑"
echo "                                 YOUR ROUTER CODE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
