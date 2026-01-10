# Ollama Setup Guide

**Ollama is optional** - Soulfra works perfectly without it! But if you want AI features, here's how to set it up properly.

---

## 🚀 Quick Setup (5 minutes)

```bash
# Terminal 1: Start Ollama server
ollama serve

# Terminal 2: Start Soulfra
python3 app.py

# Browser: Try AI features
# Visit: http://localhost:5001/playground
```

---

## 📥 Installation

### macOS / Linux:
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model (required!)
ollama pull llama2

# Verify installation
ollama list
```

### Windows:
1. Download from https://ollama.com/download
2. Run installer
3. Open PowerShell:
   ```powershell
   ollama pull llama2
   ollama list
   ```

---

## ✅ Verify It's Working

### Test 1: Check if Ollama is running
```bash
# Should show model info if working
curl http://localhost:11434/api/tags
```

### Test 2: Generate test response
```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama2",
  "prompt": "Hello!",
  "stream": false
}'
```

### Test 3: Run integration tests
```bash
python3 test_integration.py
# Should show: ✓ [PASS] Ollama connectivity
```

---

## 🎮 Using Ollama in Soulfra

### 1. **Playground Chat** (Easiest)
1. Visit http://localhost:5001/playground
2. Click "Live Chat" tab
3. Type a message and press Send
4. **If you see "Ollama: Not Connected"**:
   - Check Terminal 1: Is `ollama serve` still running?
   - Run: `lsof -i :11434` (should show ollama process)
   - Restart: Kill ollama, run `ollama serve` again

### 2. **Post Feedback** (Admin only)
1. Create/view any post
2. Click "Get AI Feedback" button (admin only)
3. Choose:
   - **Preview Feedback**: See AI responses without posting
   - **Get & Post as Comments**: Automatically post AI comments
4. **If it fails**:
   - Check browser console (F12) for errors
   - Verify ollama is running: `curl http://localhost:11434/api/tags`

### 3. **Terminal Chat** (For learning)
```bash
python3 ollama_chat.py

# Chat about anything!
# Your conversations are saved to database
# Convert to blog posts: python3 compile_chats.py
```

---

## 🐛 Troubleshooting

### Problem: "Ollama: Not Connected" in playground

**Check 1: Is Ollama running?**
```bash
lsof -i :11434
# Should show: ollama (process running on port 11434)
```

**Check 2: Is a model installed?**
```bash
ollama list
# Should show: llama2 or similar
```

**Check 3: Can you reach Ollama?**
```bash
curl http://localhost:11434/api/tags
# Should return JSON with model list
```

**Fix:**
```bash
# Kill any stuck processes
pkill ollama

# Restart Ollama
ollama serve

# In another terminal, pull model if missing
ollama pull llama2
```

---

### Problem: "Ollama not responding" in terminal chat

**Symptoms:**
- `python3 ollama_chat.py` shows "Error calling Ollama"
- Timeout errors

**Fix:**
1. Check Ollama is running: `ps aux | grep ollama`
2. Test manually: `ollama run llama2 "Hello"`
3. If that works, try chat again
4. If still failing, increase timeout in `ollama_chat.py` line 112:
   ```python
   response = urllib.request.urlopen(req, timeout=120)  # Was 60
   ```

---

### Problem: Port 11434 already in use

**Symptoms:**
```
Error: listen tcp 127.0.0.1:11434: bind: address already in use
```

**Fix:**
```bash
# Find what's using the port
lsof -i :11434

# Kill it
kill -9 <PID>

# Or kill all ollama processes
pkill -9 ollama

# Restart
ollama serve
```

---

### Problem: Models take forever to download

**Tip:** Start with smaller models first!

```bash
# Smaller, faster (1.5GB)
ollama pull phi

# Medium (4.1GB)
ollama pull llama2

# Large, best quality (40GB+)
ollama pull llama3

# Check download progress
ollama list
```

---

## 🎯 Which Model Should I Use?

| Model | Size | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| `phi` | 1.5GB | ⚡⚡⚡ | ⭐⭐ | Testing, quick experiments |
| `llama2` | 4.1GB | ⚡⚡ | ⭐⭐⭐ | **Recommended for Soulfra** |
| `llama3` | 8GB | ⚡ | ⭐⭐⭐⭐ | Better quality, slower |
| `mistral` | 7GB | ⚡⚡ | ⭐⭐⭐⭐ | Good balance |

**Recommendation:** Start with `llama2` - it's the best balance of speed/quality for blog AI features.

---

## 📊 Performance Tips

### Make Ollama Faster:

1. **Use GPU if available:**
   ```bash
   # macOS: Automatically uses Metal (Apple Silicon)
   # Linux: Install CUDA/ROCm for NVIDIA/AMD GPUs
   # Check: ollama will log "Using GPU" on start
   ```

2. **Reduce context window:**
   In `app.py` line 348, change:
   ```python
   'num_ctx': 2048,  # Was 4096 - smaller = faster
   ```

3. **Use smaller models:**
   Replace `llama2` with `phi` in `app.py`:
   ```python
   'model': 'phi',  # Was 'llama2'
   ```

---

## 🔐 Security Notes

- Ollama runs **locally only** (127.0.0.1:11434)
- No data sent to external servers
- Your conversations stay on your machine
- Safe for private/sensitive content

**To expose Ollama to network** (not recommended):
```bash
OLLAMA_HOST=0.0.0.0:11434 ollama serve
# Warning: This allows anyone on your network to use your Ollama!
```

---

## 📚 Advanced: Multiple Models

Run different AI personalities with different models:

```python
# In app.py, line 345 (Ollama personas):
PERSONAS = {
    'calriven': {'model': 'llama2'},      # Technical expert
    'deathtodata': {'model': 'mistral'},  # Privacy advocate
    'theauditor': {'model': 'phi'},       # Fast validator
    'soulfra': {'model': 'llama3'},       # Best quality
}
```

Pull all models:
```bash
ollama pull llama2
ollama pull mistral
ollama pull phi
ollama pull llama3
```

---

## ✅ Checklist: AI Features Working

Run through this checklist:

- [ ] `ollama serve` is running in terminal
- [ ] `ollama list` shows at least one model
- [ ] `curl http://localhost:11434/api/tags` returns JSON
- [ ] Playground → Live Chat shows "🟢 Ollama: Connected"
- [ ] Can send a test message and get response
- [ ] `python3 test_integration.py` shows Ollama pass

**All checked?** You're ready to use AI features! 🎉

---

## 🆘 Still Having Issues?

1. **Check Ollama logs:**
   - Ollama prints errors to terminal where you ran `ollama serve`
   - Look for error messages

2. **Check Soulfra logs:**
   - Flask prints errors to terminal where you ran `python3 app.py`
   - Look for "Ollama" related errors

3. **Test manually:**
   ```bash
   ollama run llama2 "Write a haiku about code"
   ```
   - If this works, problem is in Soulfra integration
   - If this fails, problem is with Ollama itself

4. **Restart everything:**
   ```bash
   pkill ollama
   pkill -f "python3 app.py"
   sleep 2
   ollama serve &
   python3 app.py
   ```

---

## 🎓 Learning More

- **Ollama Docs**: https://github.com/ollama/ollama/blob/main/docs
- **Model Library**: https://ollama.com/library
- **API Reference**: https://github.com/ollama/ollama/blob/main/docs/api.md

---

**Remember:** Ollama is **optional** - Soulfra works great without it! Only set it up if you want the AI features.
