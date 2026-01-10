# 📦 How to Publish Soulfra to PyPI (pip install soulfra)

**Created:** January 2, 2026
**Purpose:** Step-by-step guide to publish your package so users can `pip install soulfra`

---

## 🎯 What This Achieves

After publishing, users worldwide can install your package:
```bash
pip install soulfra
# or
pip3 install soulfra
```

And use it:
```python
from soulfra import SoulfraClient
client = SoulfraClient()
```

Or via CLI:
```bash
soulfra --help
soul-commit -m "My commit"
soul-log
```

---

## ✅ Pre-Publish Checklist

### You Already Have:
- [x] `pyproject.toml` (package configuration)
- [x] Package name: `soulfra` version `0.1.0`
- [x] Core dependencies listed
- [x] CLI entry points defined
- [x] MIT license specified

### What You Need to Add/Check:

1. **Create PyPI Account**
   - [ ] Visit: https://pypi.org/account/register/
   - [ ] Verify email
   - [ ] Enable 2FA (recommended)
   - [ ] Save credentials

2. **Create API Token** (instead of password)
   - [ ] Visit: https://pypi.org/manage/account/token/
   - [ ] Click "Add API token"
   - [ ] Name: `soulfra-upload`
   - [ ] Scope: "Entire account" (or specific to "soulfra" after first upload)
   - [ ] **SAVE THIS TOKEN** - you'll only see it once!
   - [ ] Format: `pypi-AgEIcHlwaS5vcmc...` (starts with `pypi-`)

3. **README.md** (Package description)
   - [ ] Create/update README.md with:
     - What Soulfra does
     - Installation instructions
     - Quick start example
     - Features list
     - License

4. **Package Structure** (needs fixing)
   - [ ] Currently your code is in root directory (`app.py`, etc.)
   - [ ] Need to organize into `soulfra/` directory
   - [ ] See "Package Structure" section below

---

## 📁 Package Structure (What Needs Reorganizing)

### Current Structure (Not Ready):
```
soulfra-simple/
├── app.py              ❌ In wrong place
├── qr_auth.py          ❌ In wrong place
├── device_auth.py      ❌ In wrong place
├── pyproject.toml      ✅ Correct
└── README.md           ✅ Correct
```

### Target Structure (Ready for PyPI):
```
soulfra-simple/
├── pyproject.toml           ✅ Package config
├── README.md                ✅ Description
├── LICENSE                  ✅ MIT license file
├── soulfra/                 📦 Package directory
│   ├── __init__.py          ✅ Package entry point
│   ├── client.py            ✅ Main client class
│   ├── auth/                📁 Authentication module
│   │   ├── __init__.py
│   │   ├── qr_auth.py       (move from root)
│   │   └── device_auth.py   (move from root)
│   ├── api/                 📁 API module
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── cli/                 📁 CLI commands
│   │   ├── __init__.py
│   │   ├── main.py          (soulfra command)
│   │   └── git.py           (soul-commit, soul-log)
│   └── templates/           📁 Flask templates
│       └── *.html
├── tests/                   📁 Test suite
│   ├── __init__.py
│   ├── test_auth.py
│   └── test_api.py
└── dist/                    📁 Built packages (auto-generated)
    ├── soulfra-0.1.0.tar.gz
    └── soulfra-0.1.0-py3-none-any.whl
```

---

## 🔧 Step-by-Step Publishing Guide

### Step 1: Install Build Tools
```bash
# Install/upgrade build tools
pip3 install --upgrade pip setuptools wheel build twine

# Verify installation
python3 -m build --version
twine --version
```

### Step 2: Organize Package Structure (IMPORTANT!)

**Option A: Quick & Dirty (Test Publishing)**
```bash
# Create minimal package structure
mkdir -p soulfra
touch soulfra/__init__.py

# Create simple client in soulfra/__init__.py
cat > soulfra/__init__.py << 'EOF'
"""
Soulfra - Self-documenting development platform
"""

__version__ = "0.1.0"

class SoulfraClient:
    """Main client for Soulfra API"""
    def __init__(self, api_key=None):
        self.api_key = api_key

    def hello(self):
        return "Hello from Soulfra!"

# For backwards compatibility
from soulfra.client import SoulfraClient

__all__ = ['SoulfraClient']
EOF
```

**Option B: Full Structure (Production Ready)**
```bash
# Create directory structure
mkdir -p soulfra/{auth,api,cli}
touch soulfra/__init__.py
touch soulfra/{auth,api,cli}/__init__.py

# Move existing files
mv qr_auth.py soulfra/auth/
mv device_auth.py soulfra/auth/
# ... move other relevant files

# Create CLI entry points
# (See "Creating CLI Commands" section below)
```

### Step 3: Create/Update README.md
```bash
cat > README.md << 'EOF'
# Soulfra

Self-documenting development platform with soul-based identity tracking.

## Installation

```bash
pip install soulfra
```

## Quick Start

```python
from soulfra import SoulfraClient

client = SoulfraClient(api_key="your-api-key")
print(client.hello())
```

## Features

- 🔐 Multiple authentication methods (username/password, QR codes, device fingerprinting)
- 🤖 Ollama AI integration for content generation
- 📱 Multi-device support (phone ↔ laptop ↔ web)
- 🔑 QR code authentication and management
- 📊 Token usage tracking
- 🚀 Automated publishing workflows

## CLI Commands

```bash
soulfra --help
soul-commit -m "Your commit message"
soul-log
```

## Documentation

Full documentation: https://docs.soulfra.com

## License

MIT License - see LICENSE file
EOF
```

### Step 4: Create LICENSE File
```bash
cat > LICENSE << 'EOF'
MIT License

Copyright (c) 2026 CalRiven

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF
```

### Step 5: Build the Package
```bash
# Clean old builds (if any)
rm -rf dist/ build/ *.egg-info soulfra.egg-info

# Build the package
python3 -m build

# Output:
# Successfully built soulfra-0.1.0.tar.gz and soulfra-0.1.0-py3-none-any.whl
```

**What you should see:**
```
dist/
├── soulfra-0.1.0.tar.gz              (source distribution)
└── soulfra-0.1.0-py3-none-any.whl    (wheel distribution)
```

### Step 6: Test Locally (BEFORE Publishing!)
```bash
# Create test virtual environment
python3 -m venv test-env
source test-env/bin/activate

# Install your package locally
pip install dist/soulfra-0.1.0-py3-none-any.whl

# Test it works
python3 -c "from soulfra import SoulfraClient; print(SoulfraClient().hello())"
# Expected: "Hello from Soulfra!"

# Test CLI (if configured)
soulfra --help

# Deactivate when done
deactivate
```

### Step 7: Upload to TestPyPI (Practice Run)
```bash
# Upload to TEST PyPI first (safer!)
twine upload --repository testpypi dist/*

# You'll be prompted:
# Enter your API token when prompted for password
# Username: __token__
# Password: pypi-AgEIcHlwaS5vcmc... (your API token)

# Or configure credentials (see below)
```

### Step 8: Test Install from TestPyPI
```bash
# Create new test environment
python3 -m venv test-install
source test-install/bin/activate

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ soulfra

# Test it
python3 -c "from soulfra import SoulfraClient; print(SoulfraClient().hello())"

# Deactivate
deactivate
```

### Step 9: Upload to Real PyPI (PRODUCTION!)
```bash
# Once tested, upload to REAL PyPI
twine upload dist/*

# Enter credentials (same as TestPyPI but different token)
# Username: __token__
# Password: pypi-... (your PyPI API token)

# Success!
# Your package is now live at: https://pypi.org/project/soulfra/
```

### Step 10: Test Real Installation
```bash
# ANYONE can now install:
pip install soulfra

# Or with pip3:
pip3 install soulfra
```

---

## 🔑 Configuring PyPI Credentials (Easier)

Instead of entering token every time, configure it:

**Create `~/.pypirc`:**
```bash
cat > ~/.pypirc << 'EOF'
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR_REAL_PYPI_TOKEN_HERE

[testpypi]
username = __token__
password = pypi-YOUR_TEST_PYPI_TOKEN_HERE
repository = https://test.pypi.org/legacy/
EOF

# Secure the file
chmod 600 ~/.pypirc
```

Now `twine upload` will use stored credentials automatically!

---

## 🚀 Updating Your Package (Future Releases)

### For Bug Fixes (0.1.0 → 0.1.1):
```bash
# 1. Update version in pyproject.toml
sed -i '' 's/version = "0.1.0"/version = "0.1.1"/' pyproject.toml

# 2. Update __version__ in soulfra/__init__.py
sed -i '' 's/__version__ = "0.1.0"/__version__ = "0.1.1"/' soulfra/__init__.py

# 3. Rebuild
rm -rf dist/ build/ *.egg-info
python3 -m build

# 4. Upload
twine upload dist/*
```

### For New Features (0.1.0 → 0.2.0):
```bash
# Same process, but increment minor version
sed -i '' 's/version = "0.1.0"/version = "0.2.0"/' pyproject.toml
```

### For Breaking Changes (0.1.0 → 1.0.0):
```bash
# Same process, but increment major version
sed -i '' 's/version = "0.1.0"/version = "1.0.0"/' pyproject.toml
```

---

## 🛠️ Creating CLI Commands

Your `pyproject.toml` expects these CLI entry points:
```toml
[project.scripts]
soulfra = "soulfra_cli:main"
soul-commit = "soul_git:soul_commit_cli"
soul-log = "soul_git:soul_log_cli"
```

**Create `soulfra/cli/__init__.py`:**
```python
"""CLI commands for Soulfra"""

def main():
    """Main CLI entry point"""
    import sys
    print("Soulfra CLI v0.1.0")
    print("Usage: soulfra [command]")
    print("\nCommands:")
    print("  help     - Show this help")
    print("  version  - Show version")
    print("  init     - Initialize Soulfra project")

    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "version":
            print("0.1.0")
        elif command == "init":
            print("Initializing Soulfra project...")
        else:
            print(f"Unknown command: {command}")

def soul_commit_cli():
    """soul-commit CLI entry point"""
    import sys
    print("Soul Commit")
    if "-m" in sys.argv:
        idx = sys.argv.index("-m")
        message = sys.argv[idx + 1] if len(sys.argv) > idx + 1 else ""
        print(f"Committing with message: {message}")
    else:
        print("Usage: soul-commit -m 'message'")

def soul_log_cli():
    """soul-log CLI entry point"""
    print("Soul Log - Showing recent activity")
```

**Update `pyproject.toml` to point to correct modules:**
```toml
[project.scripts]
soulfra = "soulfra.cli:main"
soul-commit = "soulfra.cli:soul_commit_cli"
soul-log = "soulfra.cli:soul_log_cli"
```

---

## 📊 Common Issues & Solutions

### Issue 1: "Package not found" during import
**Cause:** Missing `__init__.py` files
**Fix:**
```bash
find soulfra -type d -exec touch {}/__init__.py \;
```

### Issue 2: "Module not found" for CLI commands
**Cause:** Entry points misconfigured in pyproject.toml
**Fix:** Check that module paths match actual file structure

### Issue 3: "Version already exists" on upload
**Cause:** Can't re-upload same version to PyPI
**Fix:** Increment version number in pyproject.toml

### Issue 4: Upload fails with 403 Forbidden
**Cause:** Invalid API token or wrong permissions
**Fix:**
- Check token is correct
- Ensure token has upload permissions
- Try creating new token

### Issue 5: Package installs but imports fail
**Cause:** Files not included in package
**Fix:** Update `pyproject.toml`:
```toml
[tool.setuptools]
packages = ["soulfra", "soulfra.auth", "soulfra.api", "soulfra.cli"]
```

---

## 🎯 Quick Publishing Checklist

Use this for every release:

- [ ] Update version in `pyproject.toml`
- [ ] Update `__version__` in `soulfra/__init__.py`
- [ ] Update `README.md` with changes
- [ ] Run tests (if you have them): `pytest`
- [ ] Clean old builds: `rm -rf dist/ build/ *.egg-info`
- [ ] Build: `python3 -m build`
- [ ] Test locally: `pip install dist/*.whl` in venv
- [ ] Upload to TestPyPI: `twine upload --repository testpypi dist/*`
- [ ] Test from TestPyPI: `pip install --index-url https://test.pypi.org/simple/ soulfra`
- [ ] If all good, upload to real PyPI: `twine upload dist/*`
- [ ] Verify on PyPI: https://pypi.org/project/soulfra/
- [ ] Test real install: `pip install soulfra` in fresh venv
- [ ] Create git tag: `git tag v0.1.0 && git push --tags`

---

## 🌟 After Publishing

### Tell the World:
1. **Update GitHub README** with installation badge:
   ```markdown
   [![PyPI version](https://badge.fury.io/py/soulfra.svg)](https://badge.fury.io/py/soulfra)
   ```

2. **Create GitHub Release**:
   - Visit: https://github.com/calriven/soulfra/releases/new
   - Tag: `v0.1.0`
   - Title: `Soulfra 0.1.0 - Initial Release`
   - Description: Changelog

3. **Social Media** (optional):
   - Tweet about it
   - Post on Reddit (r/Python, r/learnpython)
   - Hacker News

4. **Documentation Site**:
   - Deploy docs to https://docs.soulfra.com
   - Add "Installation" section

---

## 📚 Example: Minimal Working Package

Here's the ABSOLUTE MINIMUM to publish:

**Structure:**
```
soulfra-simple/
├── pyproject.toml          (already have)
├── README.md               (create)
├── LICENSE                 (create)
└── soulfra/
    └── __init__.py         (create)
```

**soulfra/__init__.py:**
```python
"""Soulfra - Self-documenting development platform"""
__version__ = "0.1.0"

class SoulfraClient:
    def __init__(self, api_key=None):
        self.api_key = api_key

    def hello(self):
        return f"Soulfra v{__version__}"
```

**Build & Publish:**
```bash
python3 -m build
twine upload dist/*
```

**Done!** Users can now `pip install soulfra`

---

## 🎓 Resources

- **PyPI Official Guide**: https://packaging.python.org/tutorials/packaging-projects/
- **Twine Docs**: https://twine.readthedocs.io/
- **Semantic Versioning**: https://semver.org/
- **Python Packaging**: https://packaging.python.org/

---

## 🚨 IMPORTANT Security Notes

1. **Never commit API tokens** to git
2. **Use API tokens, not passwords** for uploads
3. **Secure ~/.pypirc**: `chmod 600 ~/.pypirc`
4. **Use 2FA** on your PyPI account
5. **Test on TestPyPI first** before real PyPI
6. **Can't delete from PyPI** - only hide old versions
7. **Can't reuse version numbers** - must increment for every upload

---

**Bottom Line:**
Your package is ALMOST ready to publish. You just need to:
1. Organize files into `soulfra/` directory structure
2. Create simple `__init__.py`
3. Run `python3 -m build`
4. Upload with `twine upload dist/*`

Start with the minimal version, get it working, then expand later!
