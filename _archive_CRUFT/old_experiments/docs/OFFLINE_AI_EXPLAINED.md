# Offline AI System - Complete Guide

## 🎯 The Vision

Build a **complete AI system** that works **100% offline**, with **full database logging**, and **analytics** - all from scratch using first principles.

**No external APIs. No internet required. Full control.**

## What We Built

### 1. **neural_proxy.py** - Our Own AI API

An OpenAI-compatible API server that routes requests to:
- Our 7 trained neural networks (classification)
- Ollama (local text generation)
- Logs everything to database

**Why?**
- External APIs are expensive ($$$)
- Require internet connection
- Send your data to their servers
- Rate limited
- Vendor lock-in

**Our solution:**
- FREE (local models)
- Works offline
- Data stays local
- No rate limits
- Full control

### 2. **ai_analytics.py** - Analytics & Graphs

Generates insights from logged AI queries:
- Usage patterns (most common queries)
- Model performance (latency, tokens)
- Knowledge graphs (query relationships)
- Pure HTML/SVG graphs (no matplotlib!)

**Why?**
- Every AI query is valuable data
- Pattern analysis reveals insights
- Performance tracking
- Cost tracking (if using paid APIs)
- Knowledge graph potential

### 3. **prove_offline_ai.py** - End-to-End Demo

Demonstrates the complete system working:
- Neural classification
- Ollama generation
- Database logging
- Analytics generation
- HTML report export

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Your Application                         │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│            Neural Proxy API (neural_proxy.py)                │
│                 OpenAI-Compatible Format                      │
│            POST /v1/completions {"model": "..."}              │
└─────┬─────────────────────────────────────────────────┬─────┘
      │                                                   │
      │                                                   │
      ▼                                                   ▼
┌──────────────────────┐                   ┌──────────────────────┐
│  Our Neural Networks │                   │  Ollama (Local LLM)  │
│  7 Trained Models    │                   │  llama2, mistral, etc│
│  - Technical         │                   │  Text Generation     │
│  - Privacy           │                   │  100% Offline        │
│  - Validation        │                   │                      │
│  Classification      │                   │                      │
└──────────┬───────────┘                   └────────┬─────────────┘
           │                                        │
           └────────────────┬───────────────────────┘
                            │
                            ▼
            ┌───────────────────────────────┐
            │    SQLite Database            │
            │  ai_requests                  │
            │  ai_responses                 │
            │  ai_interactions              │
            │  (Knowledge Graph)            │
            └───────────────┬───────────────┘
                            │
                            ▼
            ┌───────────────────────────────┐
            │   Analytics (ai_analytics.py) │
            │   - Usage patterns            │
            │   - Performance metrics       │
            │   - Knowledge graph           │
            │   - HTML/SVG graphs           │
            └───────────────────────────────┘
```

## How It Works

### Step 1: Request Comes In

Your app makes a request:
```python
POST http://localhost:8080/v1/completions
{
  "model": "neural-classify",
  "prompt": "This code is well-written and follows best practices"
}
```

### Step 2: Router Decides

Neural Proxy routes based on model prefix:
- `neural-*` → Our neural networks
- `ollama-*` → Ollama local LLM
- Other → Neural networks (default)

### Step 3: Processing

**Neural Networks:**
- Load model from database
- Run classification algorithm
- Return result (e.g., "technical", 80% confidence)

**Ollama:**
- Call local Ollama server (http://localhost:11434)
- Generate text using llama2/mistral/etc
- Return generated text

### Step 4: Logging

Everything logged to database:
- Request ID (unique)
- Model used
- Full prompt
- Response text
- Latency (ms)
- Token counts
- Timestamp

### Step 5: Response

OpenAI-compatible response:
```json
{
  "id": "req_abc123",
  "model": "neural-classify",
  "choices": [{
    "text": "technical",
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 1,
    "total_tokens": 11
  }
}
```

### Step 6: Analytics

Later, analyze all logged queries:
```bash
python3 ai_analytics.py --all
```

Generates:
- Usage statistics
- Performance metrics
- Knowledge graph
- HTML report with SVG graphs

## Database Schema

### ai_requests
```sql
CREATE TABLE ai_requests (
    id INTEGER PRIMARY KEY,
    request_id TEXT UNIQUE NOT NULL,
    model TEXT NOT NULL,
    prompt TEXT NOT NULL,
    max_tokens INTEGER,
    temperature REAL,
    user_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT
)
```

### ai_responses
```sql
CREATE TABLE ai_responses (
    id INTEGER PRIMARY KEY,
    request_id TEXT NOT NULL,
    response_text TEXT NOT NULL,
    finish_reason TEXT,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    latency_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (request_id) REFERENCES ai_requests(request_id)
)
```

### ai_interactions
```sql
CREATE TABLE ai_interactions (
    id INTEGER PRIMARY KEY,
    request_id TEXT NOT NULL,
    interaction_type TEXT,
    source_entity TEXT,
    target_entity TEXT,
    relationship TEXT,
    confidence REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (request_id) REFERENCES ai_requests(request_id)
)
```

## Quick Start

### 1. Install Ollama (Optional)

```bash
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama2

# Windows
# Download from https://ollama.com/download
```

### 2. Start Ollama (Optional)

```bash
# Terminal 1
ollama serve
```

### 3. Initialize Database

```bash
python3 neural_proxy.py --init
```

### 4. Test Classification

```bash
python3 prove_offline_ai.py --test-classification
```

Output:
```
Testing Neural Classification:

Python code to sort a list
  → technical (70%)

Privacy policy for user data
  → privacy (80%)

Validation test for login form
  → validation (75%)
```

### 5. Run Full Demo

```bash
python3 prove_offline_ai.py --demo
```

This will:
1. Initialize database
2. Run classification tests
3. Test Ollama generation (if available)
4. Show database logging
5. Generate analytics
6. Export HTML report

### 6. Start API Server (Optional)

```bash
# Terminal 2
python3 neural_proxy.py --serve
```

Now you can make API requests:

```bash
curl -X POST http://localhost:8080/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "neural-classify",
    "prompt": "This is a test prompt"
  }'
```

### 7. View Analytics

```bash
python3 ai_analytics.py --all
```

Or export HTML report:

```bash
python3 ai_analytics.py --export my_report.html
open my_report.html
```

## Use Cases

### 1. Offline Development

Test AI features without internet:
- No API keys needed
- Unlimited requests
- Fast iteration
- Privacy guaranteed

### 2. Experimentation

Try different prompts and see what works:
- Log everything to database
- Analyze patterns
- Optimize prompts
- A/B testing

### 3. Cost Tracking

If you later switch to paid APIs:
- Track token usage
- Estimate costs
- Optimize for efficiency
- Compare models

### 4. Knowledge Graph

Build relationships from queries:
- See what users ask about
- Find related topics
- Build recommendation engine
- Content generation ideas

### 5. Migration Path

Easy to migrate between backends:
- Start with Ollama (free, offline)
- Move to our neural networks (faster)
- Eventually use external APIs (GPT-4, Claude)
- All use same API format!

## Code Examples

### Python Client

```python
import json
import urllib.request

def call_ai(prompt, model='neural-classify'):
    url = 'http://localhost:8080/v1/completions'

    payload = {
        'model': model,
        'prompt': prompt,
        'max_tokens': 100
    }

    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=data,
        headers={'Content-Type': 'application/json'}
    )

    response = urllib.request.urlopen(req)
    return json.loads(response.read().decode('utf-8'))

# Test it
result = call_ai("Classify this text")
print(result['choices'][0]['text'])
```

### JavaScript Client

```javascript
async function callAI(prompt, model = 'neural-classify') {
  const response = await fetch('http://localhost:8080/v1/completions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: model,
      prompt: prompt,
      max_tokens: 100
    })
  });

  return await response.json();
}

// Test it
const result = await callAI("Classify this text");
console.log(result.choices[0].text);
```

### Curl

```bash
# Classification
curl -X POST http://localhost:8080/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "neural-classify",
    "prompt": "This code is well-written"
  }'

# Text generation (requires Ollama)
curl -X POST http://localhost:8080/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "ollama-llama2",
    "prompt": "Write a haiku about Python",
    "max_tokens": 50
  }'
```

## Extending the System

### Add New Neural Network

1. Train your model (see `pure_neural_network.py`)
2. Insert into database:
```sql
INSERT INTO neural_networks (model_name, description, accuracy)
VALUES ('my_custom_classifier', 'My custom classification', 0.85);
```
3. Add classification logic to `neural_proxy.py`:
```python
def _classify_custom(text: str) -> Dict:
    # Your classification logic
    return {'classification': 'custom', 'confidence': 0.8}
```

### Add New Ollama Model

1. Pull the model:
```bash
ollama pull mistral
```

2. Use it:
```bash
curl -X POST http://localhost:8080/v1/completions \
  -d '{"model": "ollama-mistral", "prompt": "..."}'
```

### Add External API

Modify `neural_proxy.py` to route to external APIs:

```python
elif model.startswith('openai'):
    # Route to OpenAI API
    result = call_openai(prompt)

elif model.startswith('anthropic'):
    # Route to Anthropic API
    result = call_anthropic(prompt)
```

All still logged to database! Compare performance/cost across providers.

## Performance

### Neural Networks
- Latency: ~10-50ms
- Throughput: 100+ req/sec
- Cost: FREE
- Offline: ✅

### Ollama (llama2)
- Latency: ~500-2000ms
- Throughput: 1-5 req/sec
- Cost: FREE
- Offline: ✅

### OpenAI API (for comparison)
- Latency: ~500-1500ms
- Throughput: Variable (rate limits)
- Cost: $$$
- Offline: ❌

## Analytics Examples

### Usage Patterns

```
📊 USAGE PATTERNS

Total Requests: 127

Requests by Model:
  neural-classify                 89 (70.1%)
  ollama-llama2                   32 (25.2%)
  neural-privacy                   6 (4.7%)

Most Common Prompts:
   15x Classify this blog post...
   12x What is the capital of...
    8x Write a function to...
```

### Performance Metrics

```
⚡ PERFORMANCE METRICS

Average Latency (ms):
  neural-classify                  23.45 ms
  ollama-llama2                 1245.67 ms
  neural-privacy                   18.23 ms

Token Usage:
  neural-classify
    Prompt tokens:          1234
    Completion tokens:        89
    Total tokens:           1323
```

### Knowledge Graph

```
🕸️ KNOWLEDGE GRAPH

Top Keywords:
  classification         45
  function              32
  privacy               28
  database              25

Keyword Co-occurrences:
  classification+function           12
  privacy+database                   8
  function+python                    7
```

## Philosophy

### Zero Dependencies
- Python stdlib only (urllib, json, sqlite3)
- No pip packages required
- No npm packages
- Pure first principles

### First Principles Approach
- Understand OpenAI API format
- Build our own version
- Log to database
- Generate insights
- No "magic" - understand everything

### Data Ownership
- All data stays local
- SQLite database
- No external services
- Full control
- Privacy guaranteed

### Incremental Enhancement
- Start simple (neural networks)
- Add Ollama (local LLM)
- Eventually add external APIs
- Same interface throughout
- Easy migration

## Troubleshooting

### Ollama Not Available

That's okay! The system works without it:
- Neural networks still work
- Database logging still works
- Analytics still work
- Just can't do text generation

To enable Ollama:
```bash
# Install
curl -fsSL https://ollama.com/install.sh | sh

# Pull model
ollama pull llama2

# Start server
ollama serve
```

### API Server Port in Use

Change the port:
```bash
python3 neural_proxy.py --serve --port 8081
```

### Database Locked

Close any open connections:
```bash
pkill -f "python3 neural_proxy.py"
```

## Next Steps

1. **Integrate with Your App**
   - Replace external AI calls with our API
   - Enjoy offline capability
   - Track all usage in database

2. **Train Better Models**
   - Use logged queries as training data
   - Improve classification accuracy
   - Add more neural networks

3. **Build Knowledge Graph**
   - Analyze query relationships
   - Find patterns
   - Auto-generate content ideas

4. **Optimize Performance**
   - Cache common queries
   - Batch requests
   - Use faster models

5. **Add More Backends**
   - Fine-tune Ollama models
   - Train custom LLMs
   - Integrate other AI services

---

**TL;DR:** We built our own AI API that works 100% offline, logs everything to database, and generates analytics. Uses Python stdlib + SQLite + our neural networks + Ollama (optional). No external dependencies. Complete control.
