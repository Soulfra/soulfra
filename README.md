# Soulfra

Your keys. Your identity. Period.

**Category**: Identity & Security

## Deployment

This site is deployed to GitHub Pages.

Domain: https://soulfra.com

## Architecture

- **Static Site**: GitHub Pages (free)
- **API Server**: api.soulfra.com (shared)
- **Database**: SQLite on API server

## Build

Generated from Soulfra multi-site generator:
```bash
python3 export_static.py --brand soulfra
```
