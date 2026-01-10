# Ollama Setup (Simple Instructions)

**Ollama = Local AI running on your computer. Zero API costs.**

**Model name `llama2` is CORRECT** - that's the actual model name, not a family name.

---

## Quick Install (3 Commands)

```bash
# 1. Install Ollama
curl https://ollama.ai/install.sh | sh

# 2. Download llama2 model (3.8GB)
ollama pull llama2

# 3. Start Ollama server
ollama serve
```

**That's it!** Ollama is now running at `http://localhost:11434`.

---

## Test It Works

```bash
# Terminal 1: Ollama serve (keep running)
ollama serve

# Terminal 2: Test Ollama
curl http://localhost:11434/api/tags

# Expected output:
# {"models":[{"name":"llama2:latest",...}]}
```

**✅ If you see JSON with models**, Ollama is working!

---

## Model Names (What's Correct)

| Model Name | Size | Speed | Quality |
|------------|------|-------|---------|
| `llama2` | 3.8GB | Medium | Good |
| `tinyllama` | 637MB | Fast | OK |
| `mistral` | 4.1GB | Medium | Better |
| `codellama` | 3.8GB | Medium | Code-focused |

**`llama2` is the default and works fine** for cringeproof quiz AI responses.

**NOT a family name** - it's the actual model you download with `ollama pull llama2`.

---

## How It's Used in Soulfra

### File: `ollama_discussion.py`

```python
def call_ollama(self, prompt):
    """Call Ollama API with persona system prompt"""
    request_data = {
        'model': 'llama2',  # ← This is correct!
        'prompt': full_prompt,
        'system': persona_config['system_prompt'],
        'stream': False
    }

    response = urllib.request.urlopen(req, timeout=60)
    result = json.loads(response.read())
    return result.get('response')
```

**Where it's used**:
- Brand discussions (`/brand/discuss/<brand>`)
- AI personas (CalRiven, Soulfra, DeathToData, TheAuditor)
- Cringeproof quiz AI friend assignment (future feature)

---

## Check If Ollama Is Running

```bash
# Option 1: curl
curl http://localhost:11434/api/tags

# Option 2: ps
ps aux | grep ollama

# Option 3: lsof
lsof -i :11434
```

---

## Start Ollama (Different Ways)

### Option 1: Foreground (Terminal stays open)

```bash
ollama serve
# Ctrl+C to stop
```

### Option 2: Background (Terminal can close)

```bash
ollama serve > /tmp/ollama.log 2>&1 &
# Check logs: tail -f /tmp/ollama.log
```

### Option 3: Use test_with_friends.sh

```bash
./test_with_friends.sh
# Automatically starts Ollama + Flask
```

---

## Test AI Response

```bash
# Make sure Ollama is running first
ollama serve &

# Test simple prompt
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama2",
    "prompt": "Explain QR codes in one sentence",
    "stream": false
  }'

# Expected: JSON with AI response
```

---

## Where llama2 Model Gets Stored

```bash
# macOS
~/.ollama/models/

# Linux
~/.ollama/models/

# Check size
du -sh ~/.ollama/models/
# Expected: ~4GB
```

---

## Common Issues

### Issue 1: "Ollama not found"

**Error**: `ollama: command not found`

**Fix**:
```bash
# Install Ollama
curl https://ollama.ai/install.sh | sh

# Or manually download from https://ollama.ai/download
```

### Issue 2: "Model not found"

**Error**: `Error: model 'llama2' not found`

**Fix**:
```bash
# Download the model
ollama pull llama2

# List installed models
ollama list
```

### Issue 3: "Connection refused"

**Error**: `Error: Ollama not running`

**Fix**:
```bash
# Start Ollama
ollama serve

# Or check if it's already running:
ps aux | grep ollama
```

### Issue 4: "Port 11434 already in use"

**Error**: `Error: listen tcp 127.0.0.1:11434: bind: address already in use`

**Cause**: Ollama is already running

**Fix**:
```bash
# Find existing Ollama process
ps aux | grep ollama

# Kill it
killall ollama

# Restart
ollama serve
```

---

## Upgrade to Faster/Better Models (Optional)

### TinyLlama (Faster, Smaller)

```bash
# Download
ollama pull tinyllama

# Use in ollama_discussion.py:
# Change line 232 from 'llama2' to 'tinyllama'
```

**Pros**: 6x smaller, 3x faster
**Cons**: Lower quality responses

### Mistral (Better Quality)

```bash
# Download
ollama pull mistral

# Use in ollama_discussion.py:
# Change line 232 from 'llama2' to 'mistral'
```

**Pros**: Better quality, more coherent
**Cons**: Slightly larger (4.1GB)

---

## Do I Need Ollama?

**For Friends/Family Testing**: **OPTIONAL**

**What works WITHOUT Ollama**:
- ✅ QR code generation
- ✅ QR code scanning
- ✅ Database counters
- ✅ Quiz interface
- ✅ Keyring unlocks
- ✅ Mobile responsive UI

**What needs Ollama**:
- ❌ Brand discussions (`/brand/discuss/<brand>`)
- ❌ AI persona responses (CalRiven, Soulfra, etc.)
- ❌ AI-generated quiz questions (if implemented)

**Recommendation**: Skip Ollama for now, test QR + quiz first.

---

## Ollama vs Claude vs GPT

| Feature | Ollama (llama2) | Claude API | GPT API |
|---------|----------------|------------|---------|
| **Cost** | Free | $0.01/request | $0.01/request |
| **Speed** | Medium (local) | Fast (API) | Fast (API) |
| **Privacy** | 100% local | Cloud | Cloud |
| **Setup** | Download 4GB | API key | API key |
| **Quality** | Good | Excellent | Excellent |

**For OSS/localhost testing**: **Use Ollama** (free, local, private)
**For production**: Consider Claude/GPT API (better quality)

---

## Summary

**Install Ollama**:
```bash
curl https://ollama.ai/install.sh | sh
ollama pull llama2
ollama serve
```

**Check it works**:
```bash
curl http://localhost:11434/api/tags
```

**Model name `llama2` is CORRECT** - not a family name, it's the actual model.

**Do you need it?** Optional for friends/family testing. QR codes and quiz work without it.

---

**Related Docs**:
- `LOCALHOST_TESTING_GUIDE.md` - Testing without Ollama
- `ollama_discussion.py` - How Ollama is used in code
- `WHAT_ACTUALLY_WORKS.md` - Which features need Ollama
