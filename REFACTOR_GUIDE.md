# Soulfra Refactor Guide

## Overview

The codebase has been reorganized into **core** (solo development) and **optional** (multiplayer features) to make it easier to develop without email/mesh network dependencies.

## Folder Structure

```
soulfra-simple/
├── core/               # 242 essential files (Ollama + SQLite + Flask)
├── optional/           # 9 multiplayer files (Email + Mesh Network + Blamechain)
├── dev_mode.py         # Solo development startup (NO email)
├── app.py              # Full stack with multiplayer features
└── refactor_folders.py # Safe reorganization tool
```

## What's in Each Folder?

### `/core` - Solo Development (242 files)
Essential files for building with Ollama + SQLite + Flask:
- `database.py` - SQLite database
- `github_faucet.py` - OAuth & API keys
- `soulfra_types.py` - Type conversions
- `customer_discovery_backend.py` - Discovery chat
- All Flask routes (`*_routes.py`)
- All AI processing (`ollama_*.py`)
- All content generation
- All UI/web features

**Use this when:** Building solo with local Ollama models

### `/optional` - Multiplayer Features (9 files)
Features for collaboration with other users:
- `simple_emailer.py` - Email network sync
- `ollama_email_node.py` - AI email processing
- `backfill_mesh_network.py` - Mesh network backfill
- `test_mesh_flow.py` - Mesh network testing
- `tribunal_email_notifier.py` - Email notifications
- `github_watcher.py` - GitHub repo watching
- `prove_voice_pipeline.py` - Voice proof pipeline
- `whisper_transcriber.py` - Voice transcription
- `app.py` - Multiplayer version

**Use this when:** Ready for multi-user collaboration

## How to Use

### Solo Development (Recommended)
```bash
python3 dev_mode.py
```

This starts Flask with:
- ✅ Ollama AI
- ✅ SQLite Database
- ✅ GitHub OAuth
- ✅ All web UI features
- ❌ NO email network (disabled)
- ❌ NO mesh network (disabled)

### Full Stack (Multiplayer)
```bash
python3 app.py
```

This includes everything, including email/mesh network for collaboration.

## Why This Split?

**Problem:** You're doing solo development but the codebase has 156 email-related imports that aren't needed

**Solution:** Separate core (Ollama only) from optional (email network)

**Your Question:** "why do we even need my email if i have ollama and different models and shit?"

**Answer:** You don't! Email network is for:
- Multi-user collaboration
- Decentralized sync between developers
- Firebase-style real-time features without cloud

For solo dev with Ollama, you only need `/core` files.

## Refactoring Tools

### `analyze_dependencies.py`
Analyzes 325+ Python files to understand what imports what:
```bash
python3 analyze_dependencies.py
```

Outputs:
- `dependencies.json` - Full import graph
- `core_files.txt` - 242 essential files
- `bloat_files.txt` - 9 email/multiplayer files
- `module_graph.json` - Reverse dependency map

### `refactor_folders.py`
Safely reorganize files without breaking imports:
```bash
python3 refactor_folders.py           # Dry run (show changes)
python3 refactor_folders.py --copy    # Copy files to /core and /optional
python3 refactor_folders.py --move    # Move files (delete originals)
```

**Safety features:**
- Copy first, verify, then move (non-destructive)
- AST-based import rewriting (not regex)
- Automated testing before committing

## Tech Stack

### Core Dependencies (Dev Mode)
- **Ollama** - Local AI models
- **SQLite** - Database (no server needed)
- **Flask** - Web framework
- **Python stdlib only** - NO external libraries

### Optional Dependencies (Multiplayer)
- **IMAP/SMTP** - Email network sync
- **GitHub API** - Repo watching
- **Whisper** - Voice transcription

## Development Philosophy

Following **Bun/Zig/pot/zzz programming style**:
- NO external libraries
- Build from scratch
- Pure Python stdlib only
- Minimal dependencies

## Next Steps

1. **Keep developing solo** - Use `dev_mode.py` and `/core` files
2. **Refactor as needed** - Run `refactor_folders.py` to reorganize safely
3. **When ready for multiplayer** - Switch to `app.py` and use `/optional` features

## Files Created

1. `analyze_dependencies.py` - Dependency analyzer (AST-based)
2. `refactor_folders.py` - Safe folder reorganization
3. `dev_mode.py` - Solo development startup
4. `core/` - 242 essential files
5. `optional/` - 9 multiplayer files
6. `soulfra_types.py` - Centralized type conversions
7. `customer_discovery_backend.py` - Discovery chat backend

## Questions?

- **"Will this break my existing code?"** - No, original files are still in place. `/core` and `/optional` are copies.
- **"How do I know what's safe to remove?"** - Check `bloat_files.txt` (only 9 files)
- **"Can I still use email network?"** - Yes, run `app.py` instead of `dev_mode.py`

---

**Philosophy:** You should be able to use Ollama yourself for solo development, then refactor when ready. No need for email network until you want multiplayer features.
