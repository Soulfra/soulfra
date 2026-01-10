# Flask Restart Guide

## The Problem You Were Having

You had **16+ Flask processes** running simultaneously, all fighting for port 5001. This caused:
- ❌ API works "sometimes" (inconsistent behavior)
- ❌ Crashes with exit code 137
- ❌ Different processes loading different versions of code
- ❌ Complete chaos

## The Solution

**Use the restart script** - It kills everything cleanly and starts ONE process:

```bash
./restart_flask.sh
```

## What The Script Does

1. **Kills ALL Flask processes** (`pkill -9 -f "python3 app.py"`)
2. **Waits for ports to free up** (sleep 3)
3. **Force-clears port 5001** (`lsof -ti:5001 | xargs kill -9`)
4. **Starts ONE clean Flask instance**
5. **Verifies it started** (curl test)
6. **Shows you the PID** (so you can kill it later)

## How To Use

### Start Flask (Clean)
```bash
./restart_flask.sh
```

### Stop Flask
```bash
# Option 1: Use the PID shown when you started it
kill 58612  # (your PID will be different)

# Option 2: Kill all Flask processes
pkill -f "python3 app.py"
```

### Check If Flask Is Running
```bash
lsof -i:5001
```

### Test The Comment API
```bash
# Get comments for post 1
curl http://192.168.1.87:5001/api/comments/1

# Post a comment
curl -X POST http://192.168.1.87:5001/api/comments \
  -H "Content-Type: application/json" \
  -d '{"post_id": 1, "content": "Test comment"}'
```

## Why This Works

- **Single source of truth**: ONE Flask process = ONE version of code loaded
- **No race conditions**: No multiple processes fighting for the same port
- **Clean startup**: Kills zombies from previous failed starts
- **Predictable behavior**: API always works the same way

## The URLs You Care About

After running the restart script, these will work **consistently**:

- **Local**: http://localhost:5001
- **LAN**: http://192.168.1.87:5001
- **Comments API**: http://192.168.1.87:5001/api/comments/1
- **GitHub Pages Site**: https://soulfra.github.io/soulfra/

## For GitHub Pages Comments

The static blog posts on GitHub Pages now have a JavaScript widget that calls:
- `GET /api/comments/<post_id>` - Load comments
- `POST /api/comments` - Submit comment

**Important**: Flask must be running on your laptop for comments to work on the live site.

## Pro Tip

Don't run `python3 app.py` directly multiple times. Always use `./restart_flask.sh` to avoid creating duplicate processes.
