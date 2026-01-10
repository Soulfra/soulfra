"""
Template Variable System

Centralized template variables that get replaced on deployment.
Handles all `example.com`, `${VARIABLE}`, and config placeholders.

**Usage:**

1. Define variables here
2. Run formatter on deployment:
   ```bash
   python3 format_templates.py \
     --base-domain soulfra.com \
     --github-pages soulfra.github.io/voice-archive \
     --api-endpoint https://api.soulfra.com
   ```

3. Formatter replaces all `${VAR}` with actual values

**Example:**

Before:
```
BASE_URL = "${BASE_DOMAIN}"
```

After:
```
BASE_URL = "soulfra.com"
```
"""

# ==============================================================================
# DEPLOYMENT VARIABLES (replaced by format_templates.py)
# ==============================================================================

TEMPLATE_VARS = {
    # ===== Domains =====
    'BASE_DOMAIN': '${BASE_DOMAIN}',                    # soulfra.com
    'API_DOMAIN': '${API_DOMAIN}',                      # api.soulfra.com
    'AUTH_DOMAIN': '${AUTH_DOMAIN}',                    # auth.soulfra.com
    'AI_DOMAIN': '${AI_DOMAIN}',                        # ai.soulfra.com

    # ===== GitHub Pages =====
    'GITHUB_PAGES_URL': '${GITHUB_PAGES_URL}',          # soulfra.github.io/voice-archive
    'GITHUB_REPO': '${GITHUB_REPO}',                    # Soulfra/voice-archive
    'GITHUB_USERNAME': '${GITHUB_USERNAME}',            # Soulfra

    # ===== Voice Archive =====
    'VOICE_ARCHIVE_URL': '${VOICE_ARCHIVE_URL}',        # soulfra.github.io/voice-archive
    'VOICE_EMAIL': '${VOICE_EMAIL}',                    # voice@soulfra.com

    # ===== API Endpoints =====
    'API_ENDPOINT': '${API_ENDPOINT}',                  # https://api.soulfra.com
    'WEBHOOK_ENDPOINT': '${WEBHOOK_ENDPOINT}',          # https://api.soulfra.com/webhook
    'OLLAMA_HOST': '${OLLAMA_HOST}',                    # http://localhost:11434

    # ===== Database =====
    'DATABASE_PATH': '${DATABASE_PATH}',                # soulfra.db
    'DATABASE_VERSION': '${DATABASE_VERSION}',          # 2

    # ===== Email =====
    'SMTP_HOST': '${SMTP_HOST}',                        # smtp.sendgrid.net
    'SMTP_PORT': '${SMTP_PORT}',                        # 587
    'FROM_EMAIL': '${FROM_EMAIL}',                      # noreply@soulfra.com

    # ===== Secrets (DO NOT commit .env) =====
    'GITHUB_TOKEN': '${GITHUB_TOKEN}',                  # Set in .env
    'SENDGRID_API_KEY': '${SENDGRID_API_KEY}',          # Set in .env
    'SECRET_KEY': '${SECRET_KEY}',                      # Set in .env
    'ADMIN_PASSWORD': '${ADMIN_PASSWORD}',              # Set in .env
    'WEBHOOK_SECRET': '${WEBHOOK_SECRET}',              # Set in .env

    # ===== Faucet Settings =====
    'FAUCET_ENABLED': '${FAUCET_ENABLED}',              # true/false
    'QR_FAUCET_LIMIT': '${QR_FAUCET_LIMIT}',            # 10 per day
    'VOICE_FAUCET_LIMIT': '${VOICE_FAUCET_LIMIT}',      # 5 per day

    # ===== Deployment =====
    'ENVIRONMENT': '${ENVIRONMENT}',                    # production/development/localhost
    'PORT': '${PORT}',                                  # 5001
    'DEBUG': '${DEBUG}',                                # true/false
}

# ==============================================================================
# DEFAULT VALUES (for localhost/development)
# ==============================================================================

DEFAULT_VALUES = {
    # Domains
    'BASE_DOMAIN': 'localhost:5001',
    'API_DOMAIN': 'localhost:5001',
    'AUTH_DOMAIN': 'localhost:5002',
    'AI_DOMAIN': 'localhost:5003',

    # GitHub Pages
    'GITHUB_PAGES_URL': 'soulfra.github.io/voice-archive',
    'GITHUB_REPO': 'Soulfra/voice-archive',
    'GITHUB_USERNAME': 'Soulfra',

    # Voice Archive
    'VOICE_ARCHIVE_URL': 'https://soulfra.github.io/voice-archive',
    'VOICE_EMAIL': 'voice@soulfra.com',

    # API Endpoints
    'API_ENDPOINT': 'http://localhost:5001/api',
    'WEBHOOK_ENDPOINT': 'http://localhost:5001/webhook',
    'OLLAMA_HOST': 'http://localhost:11434',

    # Database
    'DATABASE_PATH': 'soulfra.db',
    'DATABASE_VERSION': '2',

    # Email
    'SMTP_HOST': 'smtp.sendgrid.net',
    'SMTP_PORT': '587',
    'FROM_EMAIL': 'noreply@localhost',

    # Secrets (use .env file!)
    'GITHUB_TOKEN': 'set-in-env-file',
    'SENDGRID_API_KEY': 'set-in-env-file',
    'SECRET_KEY': 'dev-secret-key-change-in-production',
    'ADMIN_PASSWORD': 'soulfra2025',
    'WEBHOOK_SECRET': 'change-me-in-production',

    # Faucet Settings
    'FAUCET_ENABLED': 'true',
    'QR_FAUCET_LIMIT': '10',
    'VOICE_FAUCET_LIMIT': '5',

    # Deployment
    'ENVIRONMENT': 'development',
    'PORT': '5001',
    'DEBUG': 'true',
}

# ==============================================================================
# PRODUCTION VALUES (example - NEVER commit real secrets!)
# ==============================================================================

PRODUCTION_EXAMPLE = {
    'BASE_DOMAIN': 'soulfra.com',
    'API_DOMAIN': 'api.soulfra.com',
    'AUTH_DOMAIN': 'auth.soulfra.com',
    'AI_DOMAIN': 'ai.soulfra.com',

    'GITHUB_PAGES_URL': 'https://soulfra.github.io/voice-archive',
    'VOICE_ARCHIVE_URL': 'https://soulfra.github.io/voice-archive',
    'VOICE_EMAIL': 'voice@soulfra.com',

    'API_ENDPOINT': 'https://api.soulfra.com',
    'WEBHOOK_ENDPOINT': 'https://api.soulfra.com/webhook',

    'ENVIRONMENT': 'production',
    'PORT': '5001',
    'DEBUG': 'false',

    # Secrets - NEVER COMMIT THESE!
    'GITHUB_TOKEN': 'ghp_REAL_TOKEN_FROM_ENV',
    'SENDGRID_API_KEY': 'SG.REAL_KEY_FROM_ENV',
    'SECRET_KEY': 'RANDOM_SECURE_KEY_FROM_ENV',
    'ADMIN_PASSWORD': 'STRONG_PASSWORD_FROM_ENV',
    'WEBHOOK_SECRET': 'RANDOM_WEBHOOK_SECRET_FROM_ENV',
}
