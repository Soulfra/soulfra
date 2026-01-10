# Soulfra Launcher Guide

**All the ways to run Soulfra - from desktop icon to production server**

---

## Understanding How It Works

**Soulfra is a Python web application**, just like ReadTheDocs, Django, or any Flask-based platform.

### The Stack (How Python Becomes a Website)

```
┌─────────────────────────────────────┐
│   Your Code (app.py)                │  ← Python Flask application
├─────────────────────────────────────┤
│   Flask Framework                    │  ← Converts Python → HTTP server
├─────────────────────────────────────┤
│   Server (Flask dev / gunicorn)     │  ← Runs the Flask app
├─────────────────────────────────────┤
│   Reverse Proxy (nginx, optional)   │  ← Routes traffic, serves static files
└─────────────────────────────────────┘
           ↓
    http://localhost:5001
```

**This is exactly how ReadTheDocs, Heroku, Render, etc. work!**

When you run `python3 app.py`, your Python code BECOMES a web server listening on port 5001.

---

## Method 1: Shell Script (Easiest)

**For**: Mac/Linux daily use

### Usage

```bash
# Make executable (first time only)
chmod +x start_soulfra.sh

# Double-click in file manager
# OR run from terminal:
./start_soulfra.sh
```

### What it does

1. Checks Python is installed
2. Checks database exists
3. Kills any previous instance on port 5001
4. Starts `python3 app.py`
5. Opens browser to http://localhost:5001
6. Shows pretty colored output

### When to use

- **Development**: Quick testing
- **Daily use**: Personal blog
- **Learning**: First time setup

---

## Method 2: Windows Batch File

**For**: Windows users

### Usage

```
Double-click: start_soulfra.bat
```

### What it does

Same as shell script, but for Windows:
- Checks Python installation
- Creates .env if needed
- Stops previous instances
- Starts server

### When to use

- Windows development
- Non-technical Windows users
- Quick local testing

---

## Method 3: Python GUI Launcher (Cross-Platform)

**For**: Non-technical users, visual interface

### Usage

```bash
python3 launcher.py
```

### Features

- ✅ **GUI window** with Start/Stop buttons
- ✅ **Live server logs** in the window
- ✅ **Status indicator** (green = running, gray = stopped)
- ✅ **Open Browser** button
- ✅ **Cross-platform** (Mac, Windows, Linux)

### Screenshot

```
╔═══════════════════════════════════════════════╗
║            SOULFRA                           ║
║   AI-Powered Ghost Writing Platform          ║
╠═══════════════════════════════════════════════╣
║ Status: 🟢 Server running                    ║
║ URL: http://localhost:5001 (click to open)   ║
║                                               ║
║ [▶ Start] [⏹ Stop] [🌐 Open Browser]        ║
║                                               ║
║ Server Logs:                                  ║
║ ┌───────────────────────────────────────────┐ ║
║ │ ✓ Python 3.11.5                           │ ║
║ │ ✓ Server started successfully!            │ ║
║ │ → URL: http://localhost:5001              │ ║
║ │ ✅ Loaded 4 neural networks              │ ║
║ └───────────────────────────────────────────┘ ║
╚═══════════════════════════════════════════════╝
```

### When to use

- Non-technical users
- Want visual feedback
- Need to start/stop frequently
- Distributing to non-developers

---

## Method 4: System Service (Production)

**For**: Production servers, always-running deployments

### Setup (Linux/Mac)

```bash
# 1. Edit soulfra.service
nano soulfra.service
# Change paths:
#   User=youruser
#   WorkingDirectory=/path/to/soulfra-simple

# 2. Create log directory
sudo mkdir -p /var/log/soulfra
sudo chown youruser:youruser /var/log/soulfra

# 3. Install service
sudo cp soulfra.service /etc/systemd/system/
sudo systemctl daemon-reload

# 4. Enable (start on boot)
sudo systemctl enable soulfra

# 5. Start service
sudo systemctl start soulfra

# 6. Check status
sudo systemctl status soulfra
```

### Managing the Service

```bash
# Start
sudo systemctl start soulfra

# Stop
sudo systemctl stop soulfra

# Restart
sudo systemctl restart soulfra

# View logs
sudo journalctl -u soulfra -f

# Check status
sudo systemctl status soulfra
```

### What it does

- ✅ **Runs on boot** - Starts automatically when server boots
- ✅ **Auto-restart** - Restarts if it crashes
- ✅ **Logging** - Logs to systemd journal
- ✅ **Production-ready** - Uses gunicorn with 4 workers
- ✅ **Resource limits** - Memory/CPU limits configured
- ✅ **Security hardening** - Sandboxing enabled

### When to use

- **Production servers** (VPS, AWS, etc.)
- **24/7 availability** required
- **Team/client websites**
- **Business deployments**

---

## Method 5: Docker Desktop (Containerized)

**For**: Consistent environments, easy deployment

### Usage

```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# View logs
docker-compose logs -f

# Restart
docker-compose restart
```

### What it includes

- ✅ Soulfra web app
- ✅ Ollama AI (for local inference)
- ✅ Persistent storage (database, uploads)
- ✅ Health checks
- ✅ Auto-restart on failure

### When to use

- Want consistent environment
- Multiple deployments
- Kubernetes/cloud deployment
- Team development

---

## Method 6: GitHub Auto-Deployment

**For**: Continuous deployment, team workflows

### Setup

1. **Add secrets to GitHub**:
   - Go to repo Settings → Secrets and variables → Actions
   - Add secrets:
     - `SERVER_HOST`: your-server.com
     - `SERVER_USER`: youruser
     - `SERVER_SSH_KEY`: (paste private SSH key)
     - `SERVER_PORT`: 22
     - `SLACK_WEBHOOK`: (optional, for notifications)

2. **Setup server**:
```bash
# On your server
cd /var/www/soulfra-simple
git remote add origin https://github.com/yourusername/soulfra
sudo systemctl enable soulfra
```

3. **Deploy**:
```bash
# On your local machine
git add .
git commit -m "Update content"
git push origin main

# GitHub Actions automatically:
# - Pulls code to server
# - Installs dependencies
# - Runs migrations
# - Restarts service
# ✅ Website updates in ~30 seconds
```

### What it does

Every time you push to GitHub:
1. Code pushed to GitHub
2. GitHub Actions triggers
3. Connects to your server via SSH
4. Pulls latest code
5. Installs dependencies
6. Runs database migrations
7. Restarts server
8. Sends Slack notification

### When to use

- Team development
- Multiple contributors
- Want automated deployments
- Professional workflows

---

## Method 7: Desktop Icon (Linux)

**For**: Linux desktop users

### Setup

```bash
# 1. Edit Soulfra.desktop
nano Soulfra.desktop
# Change paths:
#   Icon=/path/to/soulfra-simple/icon.png
#   Exec=/path/to/soulfra-simple/start_soulfra.sh

# 2. Install
cp Soulfra.desktop ~/.local/share/applications/
chmod +x ~/.local/share/applications/Soulfra.desktop

# 3. Update desktop database
update-desktop-database ~/.local/share/applications/
```

### Usage

- Find "Soulfra" in application menu
- Pin to dock/favorites
- Right-click for actions:
  - Open GUI Launcher
  - Open in Browser
  - Stop Server

### When to use

- Linux desktop
- Want app menu integration
- Daily use application

---

## Comparison Table

| Method | Skill Level | Use Case | Auto-Start | Always Running | GUI |
|--------|-------------|----------|------------|----------------|-----|
| **Shell Script** | Beginner | Dev/Testing | No | No | No |
| **Batch File** | Beginner | Windows Dev | No | No | No |
| **GUI Launcher** | Beginner | Non-tech users | No | No | ✓ |
| **System Service** | Intermediate | Production | ✓ | ✓ | No |
| **Docker** | Intermediate | Containers | No | ✓ | No |
| **GitHub Actions** | Intermediate | Auto-deploy | On push | N/A | No |
| **Desktop Icon** | Beginner | Linux daily use | No | No | No |

---

## How This Relates to Other Platforms

### vs ReadTheDocs

**ReadTheDocs**:
```
Sphinx (Python) → Flask → gunicorn → nginx → Web
```

**Soulfra**:
```
Flask (Python) → Flask/gunicorn → nginx → Web
```

**Same architecture!**

### vs Heroku

**Heroku**:
- You push code
- Heroku detects Python/requirements.txt
- Runs gunicorn automatically
- Assigns URL

**Soulfra + GitHub Actions**:
- You push code
- GitHub Actions detects push
- Deploys to your server
- You control the URL

**Same workflow, but you own the server!**

### vs Ghost (the blogging platform)

**Ghost**:
- Node.js application
- Runs as system service
- nginx reverse proxy

**Soulfra**:
- Python application
- Runs as system service (soulfra.service)
- nginx reverse proxy (optional)

**Same deployment model!**

---

## Recommended Setup by Use Case

### Personal Blog (Local)
```bash
# Use: GUI Launcher
python3 launcher.py
```
- Easy visual interface
- Start/stop with buttons
- Perfect for writing posts locally

### Personal Blog (Hosted)
```bash
# Use: System Service
sudo systemctl enable soulfra
sudo systemctl start soulfra
```
- Always running
- Survives reboots
- Professional setup

### Team/Agency (Multiple Clients)
```bash
# Use: Docker + GitHub Actions
docker-compose up -d        # Local development
git push origin main        # Auto-deploy to staging/production
```
- Consistent environments
- Automated deployments
- Easy to scale

### Distribution to Non-Tech Users
```bash
# Use: GUI Launcher or Desktop Icon
python3 launcher.py    # Cross-platform GUI
# OR
# Package as Electron app (future enhancement)
```
- No terminal needed
- Visual feedback
- One-click start

---

## Troubleshooting

### "Port 5001 already in use"

**Shell script**:
```bash
./start_soulfra.sh  # Automatically kills previous instance
```

**Manual**:
```bash
# Find process
lsof -i :5001

# Kill it
kill -9 PID
```

### "Python not found"

**Install Python**:
- Mac: `brew install python3`
- Linux: `sudo apt install python3`
- Windows: https://www.python.org/downloads/

### "Module not found"

**Install dependencies**:
```bash
pip3 install -r requirements.txt
```

### Service won't start

**Check logs**:
```bash
sudo journalctl -u soulfra -f
```

**Common issues**:
- Wrong paths in soulfra.service
- Permissions (needs write access to database)
- Port already in use

### GitHub Actions failing

**Check secrets**:
- SERVER_HOST, SERVER_USER, SERVER_SSH_KEY must be set
- SSH key must be private key (not public)
- Server must allow SSH connections

**Debug**:
- Go to Actions tab in GitHub
- Click failed workflow
- Read error messages

---

## Next Steps

1. **Try GUI Launcher**: `python3 launcher.py`
2. **Set up auto-deploy**: Configure GitHub Actions
3. **Production deployment**: Install systemd service
4. **Add to application menu**: Install desktop file

---

## Files Created

- `start_soulfra.sh` - Shell launcher (Mac/Linux)
- `start_soulfra.bat` - Batch launcher (Windows)
- `launcher.py` - GUI launcher (all platforms)
- `soulfra.service` - systemd service (Linux)
- `.github/workflows/deploy.yml` - GitHub Actions auto-deploy
- `Soulfra.desktop` - Desktop icon (Linux)
- `docker-compose.yml` - Docker deployment (already exists)

---

## The Big Picture

All these methods are just **different ways to start the same Python application**:

```python
# This is what they all do:
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001)
```

**The composition**:
1. Your code (Python) → Flask (HTTP server)
2. Flask → gunicorn (production server)
3. gunicorn → nginx (reverse proxy)
4. nginx → Internet (domain + SSL)

**It composes all the way up!**

Just like:
- Linux composes system calls → kernel → hardware
- Docker composes containers → images → registries
- Git composes commits → branches → remotes

**Soulfra composes**: Python → Web → Production → Auto-Deploy

---

**Now you can run Soulfra anywhere, anytime, any way you want!** 🚀
