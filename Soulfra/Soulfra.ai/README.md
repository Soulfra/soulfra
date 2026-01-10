# Soulfra.ai - AI Chat Interface

**Purpose:** Chat interface connecting to Ollama AI

## What This Does

Flask app that:
1. Validates session tokens from soulfraapi.com
2. Provides chat interface
3. Connects to Ollama for AI responses
4. Displays conversation history

## Flow

```
User redirected from soulfraapi.com
    ↓
GET /?session=TOKEN
    ↓
Validate token with soulfraapi.com
    ↓
Show chat interface
    ↓
User sends messages → Ollama responds
```

## Installation

```bash
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/soulfra/Soulfra.ai
pip3 install -r requirements.txt
```

## Running Locally

```bash
# Make sure Ollama is running
ollama serve

# Start soulfra.ai
python3 app.py
```

Runs on: http://localhost:5003

## Testing Flow

1. Start all three services:

   **Terminal 1: soulfra.com (static site)**
   ```bash
   cd ../Soulfra.com
   python3 -m http.server 8001
   ```

   **Terminal 2: soulfraapi.com (API)**
   ```bash
   cd ../Soulfraapi.com
   python3 app.py
   ```

   **Terminal 3: soulfra.ai (chat)**
   ```bash
   cd ../Soulfra.ai
   python3 app.py
   ```

   **Terminal 4: Ollama**
   ```bash
   ollama serve
   ```

2. Test manually:
   ```bash
   # Simulate QR scan
   curl -L http://localhost:5002/qr-signup?ref=test
   # Returns redirect to: http://localhost:5003/?session=TOKEN

   # Copy the URL and paste in browser
   # Should show chat interface
   ```

## Environment Variables

```bash
# Ollama URL (default: http://127.0.0.1:11434)
export OLLAMA_URL=http://127.0.0.1:11434

# Soulfraapi.com URL for session validation (default: http://localhost:5002)
export SOULFRA_API_URL=http://localhost:5002

# Ollama model to use (default: llama3.2)
export OLLAMA_MODEL=llama3.2

# Port (default: 5003)
export PORT=5003
```

## API Endpoints

### `GET /`
Main chat interface

**Query params:**
- `session` (required): Session token from soulfraapi.com

**Response:**
- HTML chat interface if valid session
- Error page if invalid/missing session

### `POST /api/chat`
Send message to Ollama

**Body:**
```json
{
  "message": "What is Soulfra?",
  "session": "SESSION_TOKEN"
}
```

**Response:**
```json
{
  "reply": "Soulfra is a private AI platform...",
  "model": "llama3.2",
  "tokens": 150
}
```

### `GET /health`
Health check

**Response:**
```json
{
  "status": "healthy",
  "service": "soulfra.ai",
  "ollama": "running"
}
```

## Chat Interface

**Features:**
- Clean, modern UI
- Mobile-responsive
- Shows username from session
- Typing indicator while AI thinks
- Auto-scrolls to latest message
- Enter key to send message

**Screenshot:**
```
┌─────────────────────────────────────┐
│ 🧠 Soulfra.ai        👤 CoolSoul456 │
├─────────────────────────────────────┤
│                                     │
│  You:                               │
│  ┌──────────────────────────┐      │
│  │ What is Soulfra?         │      │
│  └──────────────────────────┘      │
│                                     │
│                              AI:    │
│      ┌──────────────────────────┐  │
│      │ Soulfra is a private AI  │  │
│      │ platform that runs on    │  │
│      │ your own device...       │  │
│      └──────────────────────────┘  │
│                                     │
├─────────────────────────────────────┤
│ [Type your message...     ] [Send] │
└─────────────────────────────────────┘
```

## Deployment

### Option 1: Run on Laptop

```bash
# Expose to local network
python3 app.py
# Available at http://192.168.x.x:5003
```

### Option 2: Deploy to DigitalOcean

```bash
# Same droplet as soulfraapi.com, different port
# OR separate droplet ($5/month)

# SSH in
git clone <your-repo>
cd soulfra/Soulfra.ai
pip3 install -r requirements.txt

# Install Ollama on server
curl https://ollama.ai/install.sh | sh
ollama pull llama3.2

# Run with production settings
export SOULFRA_API_URL=https://soulfraapi.com
export PORT=5003
python3 app.py

# Point DNS: soulfra.ai → droplet IP
```

## Ollama Models

**Recommended models:**
- `llama3.2` (3B) - Fast, works on any device
- `llama3.2:1b` (1B) - Ultra-fast, minimal resources
- `phi3:mini` (3.8B) - Good quality, fast
- `mistral` (7B) - Better quality, needs more RAM

**Pull model:**
```bash
ollama pull llama3.2
```

**List available models:**
```bash
ollama list
```

## Integration

**soulfraapi.com → soulfra.ai:**
- Redirects with `?session=TOKEN` after account creation

**soulfra.ai → soulfraapi.com:**
- Calls `/validate-session` to verify every chat request

**soulfra.ai → Ollama:**
- Calls Ollama HTTP API for AI responses
- Passes user message + system prompt
- Returns AI response to chat interface

## Security

- Session tokens validated on every request
- No client-side token storage (passed via URL)
- Sessions expire after 24 hours
- Ollama runs locally (no external API calls)
- No tracking or analytics

## Troubleshooting

### "Ollama Offline"
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve

# Pull model if needed
ollama pull llama3.2
```

### "Invalid Session"
- Session token may have expired (24-hour default)
- Scan QR code again to create new account

### "Connection Error to soulfraapi.com"
- Make sure soulfraapi.com is running on port 5002
- Check SOULFRA_API_URL environment variable
