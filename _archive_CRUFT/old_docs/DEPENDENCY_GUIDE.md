# 📦 Dependency Management - Where Packages Go

## The Problem

You asked: **"how many fucking node modules and other shit do we have installed all over? where is a place we can install all of that safely on a mac?"**

This guide shows you EXACTLY where packages go and how to manage them properly.

## Summary (TL;DR)

```
✅ Homebrew packages    → /opt/homebrew/           (system-wide tools)
✅ Python packages      → ./venv/                  (project-only)
✅ Node packages        → ./node_modules/          (if needed)
❌ Global Python        → /usr/local/lib/python3/  (AVOID!)
```

## Current State

### Good News: No Node.js Bloat!
```bash
# You have NO node_modules directory
ls -la node_modules/
# ls: node_modules/: No such file or directory

# This is GOOD! No 400MB+ of JavaScript dependencies
```

### Bad News: 200+ Global Python Packages
```bash
pip3 list | wc -l
# 200+ packages installed globally!

# These should be in a virtual environment instead
```

## Where Packages Go on macOS

### 1. Homebrew (System-Wide Tools)

**Location:** `/opt/homebrew/` (Apple Silicon) or `/usr/local/` (Intel)

**What goes here:**
- Command-line tools: `caddy`, `git`, `curl`
- Languages: `python3`, `node`, `go`
- Databases: `sqlite`, `postgresql`
- System utilities: `htop`, `tree`, `jq`

**Install commands:**
```bash
brew install caddy        # Reverse proxy
brew install python3      # Python runtime
brew install node         # Node.js (if needed)
brew install tree         # Directory viewer
```

**Check what's installed:**
```bash
brew list
# caddy
# python@3.12
# git
# curl
# ... (100+ packages)
```

**Check package location:**
```bash
which caddy
# /opt/homebrew/bin/caddy

which python3
# /opt/homebrew/bin/python3
```

### 2. Python Virtual Environment (Project-Only)

**Location:** `./venv/` (inside your project)

**What goes here:**
- Flask, Gunicorn (web server)
- SQLAlchemy (database ORM)
- Requests (HTTP client)
- Pillow (image processing)
- ALL project-specific Python packages

**Setup:**
```bash
# Create virtual environment
cd ~/Desktop/roommate-chat/soulfra-simple
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install packages (they go in ./venv/, not globally!)
pip install flask gunicorn pillow requests

# Generate requirements.txt
pip freeze > requirements.txt

# Deactivate when done
deactivate
```

**Benefits:**
- ✅ Isolated from other projects
- ✅ No version conflicts
- ✅ Easy to recreate: `pip install -r requirements.txt`
- ✅ No global pollution

### 3. Node.js (If Ever Needed)

**Location:** `./node_modules/` (inside your project)

**What goes here (if you add frontend tools):**
- Tailwind CSS (styling)
- PostCSS (CSS processing)
- Live reload tools

**Setup (only if needed):**
```bash
# Initialize package.json
npm init -y

# Install packages (they go in ./node_modules/)
npm install tailwindcss postcss autoprefixer

# Packages are now in ./node_modules/ (can be 400MB!)
```

**IMPORTANT:** You don't need this yet! Your project uses plain HTML/CSS.

## What's Installed Now

### Homebrew Packages (System-Wide)
```bash
# Check installed tools
brew list

# Key packages you have:
caddy            # Reverse proxy
python@3.12      # Python runtime
git              # Version control
curl             # HTTP requests
sqlite           # Database CLI
```

### Python Packages (Currently Global - SHOULD BE IN VENV!)
```bash
# Check what's installed globally
pip3 list

# Some key packages you have:
Flask==3.0.0
gunicorn==21.2.0
requests==2.31.0
pillow==10.1.0
# ... 200+ more!
```

**Problem:** These are installed globally, not in a virtual environment.

**Fix:** Create venv and reinstall packages there (see below).

## How to Fix: Move to Virtual Environment

### Step 1: Create requirements.txt from Global Packages
```bash
# Export current global packages
pip3 freeze > requirements-global.txt

# Review what you actually need
cat requirements-global.txt
```

### Step 2: Create Virtual Environment
```bash
cd ~/Desktop/roommate-chat/soulfra-simple
python3 -m venv venv

# Activate it
source venv/bin/activate

# Your prompt changes to show (venv)
(venv) matthewmauer@Matts-MacBook-Pro soulfra-simple %
```

### Step 3: Install Only What You Need
```bash
# Core dependencies
pip install flask gunicorn pillow requests

# Optional: Install from requirements.txt
pip install -r requirements-global.txt

# Generate clean requirements.txt
pip freeze > requirements.txt
```

### Step 4: Test Your App
```bash
# Flask should still work
python3 app.py

# Visit: http://localhost:5001
```

### Step 5: Update Scripts to Use venv
```bash
# Add to start script
echo 'source venv/bin/activate' >> start.sh
echo 'python3 app.py' >> start.sh
chmod +x start.sh

# Now just run:
./start.sh
```

## Directory Structure After Setup

```
soulfra-simple/
├── venv/                          ← Python packages go here!
│   ├── bin/
│   │   ├── python3                ← venv Python
│   │   ├── flask                  ← venv Flask
│   │   └── gunicorn               ← venv Gunicorn
│   └── lib/
│       └── python3.12/
│           └── site-packages/     ← All packages here
│               ├── flask/
│               ├── requests/
│               └── pillow/
│
├── app.py                         ← Your Flask app
├── requirements.txt               ← Package list
├── .gitignore                     ← Ignores venv/
└── soulfra.db                     ← Your database
```

## Package Management Commands

### Virtual Environment
```bash
# Create venv
python3 -m venv venv

# Activate venv (do this before installing packages!)
source venv/bin/activate

# Deactivate venv
deactivate

# Delete venv (if you mess up)
rm -rf venv/
```

### Installing Packages
```bash
# ALWAYS activate venv first!
source venv/bin/activate

# Install single package
pip install flask

# Install multiple packages
pip install flask gunicorn pillow requests

# Install from requirements.txt
pip install -r requirements.txt

# Upgrade a package
pip install --upgrade flask

# Uninstall a package
pip uninstall flask
```

### Managing requirements.txt
```bash
# Generate from current venv
pip freeze > requirements.txt

# Install from requirements.txt
pip install -r requirements.txt

# Check what's installed
pip list

# Check outdated packages
pip list --outdated
```

### Homebrew
```bash
# Install system tool
brew install caddy

# Upgrade tool
brew upgrade caddy

# Uninstall tool
brew uninstall caddy

# List installed
brew list

# Search for package
brew search python

# Update Homebrew itself
brew update
```

## Where NOT to Install Packages

### ❌ Global Python (Avoid!)
```bash
# DON'T DO THIS (unless you have a good reason)
pip3 install flask

# This installs to: /opt/homebrew/lib/python3.12/site-packages/
# Problem: Version conflicts between projects
```

### ❌ System Python (Very Bad!)
```bash
# NEVER DO THIS
sudo pip install flask

# This modifies system Python
# Can break macOS tools that depend on Python
```

### ❌ Random Directories
```bash
# DON'T DO THIS
pip install --target=/tmp/packages flask

# Packages go in random places
# Impossible to track or manage
```

## How to Check Where Packages Are

### Check Python Location
```bash
# Global Python
which python3
# /opt/homebrew/bin/python3

# Virtual environment Python (when activated)
source venv/bin/activate
which python3
# /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/venv/bin/python3
```

### Check Package Location
```bash
# Show where a package is installed
pip show flask

# Output:
# Location: /Users/.../venv/lib/python3.12/site-packages
```

### Check All Package Locations
```bash
# List all site-packages directories
python3 -m site
```

## Cleanup: Remove Global Packages (Advanced)

**Warning:** Only do this if you're sure you don't need them for other projects.

```bash
# List global packages
pip3 list

# Uninstall global packages (one by one)
pip3 uninstall flask
pip3 uninstall gunicorn

# OR: Uninstall all at once (DANGEROUS!)
pip3 freeze | xargs pip3 uninstall -y
```

**Better approach:** Just ignore global packages and use venv for all projects.

## Quick Reference

| Task | Command |
|------|---------|
| Create venv | `python3 -m venv venv` |
| Activate venv | `source venv/bin/activate` |
| Deactivate venv | `deactivate` |
| Install package | `pip install flask` |
| Save dependencies | `pip freeze > requirements.txt` |
| Install dependencies | `pip install -r requirements.txt` |
| List packages | `pip list` |
| Install system tool | `brew install caddy` |
| List Homebrew packages | `brew list` |

## Your Questions Answered

### Q: "how many fucking node modules and other shit do we have installed all over?"

**A:** Good news! You have **ZERO node_modules**. No JavaScript bloat.

### Q: "where is a place we can install all of that safely on a mac?"

**A:**
- **System tools** → Homebrew (`/opt/homebrew/`)
- **Python packages** → Virtual environment (`./venv/`)
- **Node packages** → Project directory (`./node_modules/`) - only if needed

### Q: "where is homebrew lab?"

**A:** `/opt/homebrew/` on Apple Silicon Macs (M1/M2/M3)
- Binaries: `/opt/homebrew/bin/`
- Libraries: `/opt/homebrew/lib/`
- Installed packages: `/opt/homebrew/Cellar/`

## Next Steps

1. **Create virtual environment:**
   ```bash
   cd ~/Desktop/roommate-chat/soulfra-simple
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install flask gunicorn pillow requests
   pip freeze > requirements.txt
   ```

3. **Test app:**
   ```bash
   python3 app.py
   # Visit: http://localhost:5001
   ```

4. **Always activate venv before working:**
   ```bash
   source venv/bin/activate
   ```

5. **Add to .gitignore** (already done!):
   ```
   venv/
   ```

Now your project is clean, isolated, and easy to manage! 🎉
