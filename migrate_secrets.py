#!/usr/bin/env python3
"""
Secrets Migration Script
Helps migrate from .env file to GitHub Secrets for production deployment.
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


class SecretsMigrator:
    """Migrates secrets from .env to GitHub Secrets"""

    # Required secrets for production
    REQUIRED_SECRETS = {
        'STRIPE_LIVE_PUBLISHABLE_KEY': {
            'pattern': r'^pk_live_[a-zA-Z0-9]{24,}$',
            'help': 'Get from https://dashboard.stripe.com/apikeys',
            'example': 'pk_live_51H...',
            'test_value': 'pk_test_'
        },
        'STRIPE_LIVE_SECRET_KEY': {
            'pattern': r'^sk_live_[a-zA-Z0-9]{24,}$',
            'help': 'Get from https://dashboard.stripe.com/apikeys (keep secret!)',
            'example': 'sk_live_51H...',
            'test_value': 'sk_test_'
        },
        'STRIPE_WEBHOOK_SECRET': {
            'pattern': r'^whsec_[a-zA-Z0-9]{32,}$',
            'help': 'Get from https://dashboard.stripe.com/webhooks',
            'example': 'whsec_abc123...',
            'test_value': 'whsec_test_'
        },
        'JWT_SECRET': {
            'pattern': r'^[a-zA-Z0-9]{32,}$',
            'help': 'Generate with: openssl rand -hex 32',
            'example': 'a1b2c3d4e5f6...',
            'test_value': 'soulfra-2026'
        }
    }

    # Optional secrets for Phase 3
    OPTIONAL_SECRETS = {
        'TWILIO_ACCOUNT_SID': {
            'pattern': r'^AC[a-zA-Z0-9]{32}$',
            'help': 'Get from https://console.twilio.com',
            'example': 'ACxxxxx...'
        },
        'TWILIO_AUTH_TOKEN': {
            'pattern': r'^[a-zA-Z0-9]{32}$',
            'help': 'Get from https://console.twilio.com',
            'example': 'abc123...'
        },
        'TWILIO_PHONE_NUMBER': {
            'pattern': r'^\+1[0-9]{10}$',
            'help': 'Your Twilio phone number',
            'example': '+15551234567'
        },
        'SENDGRID_API_KEY': {
            'pattern': r'^SG\.[a-zA-Z0-9_-]{22}\.[a-zA-Z0-9_-]{43}$',
            'help': 'Get from https://app.sendgrid.com/settings/api_keys',
            'example': 'SG.xxxxx...'
        }
    }

    def __init__(self):
        self.env_file = Path('.env')
        self.env_example = Path('.env.example')
        self.current_secrets: Dict[str, str] = {}
        self.issues: List[str] = []

    def load_env_file(self) -> Dict[str, str]:
        """Load secrets from .env file"""
        secrets = {}

        if not self.env_file.exists():
            print(f"{YELLOW}⚠️  .env file not found{RESET}")
            return secrets

        print(f"{BLUE}📖 Reading .env file...{RESET}")

        with open(self.env_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()

                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue

                # Parse KEY=VALUE
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")

                    if key and value:
                        secrets[key] = value

        print(f"{GREEN}✅ Loaded {len(secrets)} secrets from .env{RESET}\n")
        return secrets

    def validate_secret(self, key: str, value: str, config: dict) -> Tuple[bool, str]:
        """Validate a secret value against pattern"""

        # Check if test value
        test_value = config.get('test_value', '')
        if test_value and value.startswith(test_value):
            return False, f"Using TEST key (starts with {test_value})"

        # Check pattern
        pattern = config.get('pattern')
        if pattern and not re.match(pattern, value):
            return False, "Invalid format"

        return True, "Valid"

    def check_secrets(self) -> None:
        """Check all required secrets"""

        self.current_secrets = self.load_env_file()

        print(f"{BLUE}🔍 Checking Required Secrets...{RESET}\n")

        for key, config in self.REQUIRED_SECRETS.items():
            value = self.current_secrets.get(key)

            if not value:
                print(f"{RED}❌ {key}: MISSING{RESET}")
                print(f"   Help: {config['help']}")
                print(f"   Example: {config['example']}\n")
                self.issues.append(f"{key} is missing")

            else:
                is_valid, message = self.validate_secret(key, value, config)

                if is_valid:
                    # Mask the value for display
                    masked = value[:8] + '...' if len(value) > 8 else '***'
                    print(f"{GREEN}✅ {key}: {masked} ({message}){RESET}")
                else:
                    print(f"{RED}❌ {key}: {message}{RESET}")
                    print(f"   Current: {value[:20]}...")
                    print(f"   Help: {config['help']}")
                    print(f"   Example: {config['example']}\n")
                    self.issues.append(f"{key} is {message}")

        print(f"\n{BLUE}📋 Checking Optional Secrets...{RESET}\n")

        for key, config in self.OPTIONAL_SECRETS.items():
            value = self.current_secrets.get(key)

            if not value:
                print(f"{YELLOW}⚪ {key}: Not configured (optional){RESET}")
            else:
                is_valid, message = self.validate_secret(key, value, config)
                if is_valid:
                    masked = value[:8] + '...' if len(value) > 8 else '***'
                    print(f"{GREEN}✅ {key}: {masked} ({message}){RESET}")
                else:
                    print(f"{YELLOW}⚠️  {key}: {message}{RESET}")

    def generate_github_commands(self) -> None:
        """Generate GitHub CLI commands to add secrets"""

        print(f"\n{BLUE}📝 GitHub Secrets Setup Commands{RESET}\n")
        print(f"Run these commands to add secrets to GitHub:\n")

        # Required secrets
        print(f"# Required secrets")
        for key in self.REQUIRED_SECRETS.keys():
            value = self.current_secrets.get(key, '<YOUR_VALUE_HERE>')
            print(f"gh secret set {key} -b '{value}'")

        print(f"\n# Optional secrets (if configured)")
        for key in self.OPTIONAL_SECRETS.keys():
            if key in self.current_secrets:
                value = self.current_secrets[key]
                print(f"gh secret set {key} -b '{value}'")

        print(f"\n{YELLOW}💡 Tip: Install GitHub CLI: https://cli.github.com{RESET}")
        print(f"{YELLOW}💡 Or add manually at: https://github.com/YOUR_USERNAME/YOUR_REPO/settings/secrets/actions{RESET}\n")

    def generate_env_example(self) -> None:
        """Generate .env.example file"""

        print(f"\n{BLUE}📄 Generating .env.example...{RESET}")

        content = """# Soulfra Gateway - Environment Variables
# DO NOT commit this file with real values!
# Copy to .env and fill in real values

# ===== STRIPE (Required) =====
# Get from: https://dashboard.stripe.com/apikeys

# Stripe Publishable Key (starts with pk_live_)
STRIPE_LIVE_PUBLISHABLE_KEY=pk_live_YOUR_KEY_HERE

# Stripe Secret Key (starts with sk_live_) - KEEP SECRET!
STRIPE_LIVE_SECRET_KEY=sk_live_YOUR_KEY_HERE

# Stripe Webhook Secret (starts with whsec_)
# Get from: https://dashboard.stripe.com/webhooks
STRIPE_WEBHOOK_SECRET=whsec_YOUR_SECRET_HERE

# ===== AUTHENTICATION (Required) =====
# Generate with: openssl rand -hex 32
JWT_SECRET=YOUR_RANDOM_SECRET_HERE

# ===== TWILIO (Optional - for SMS in Phase 3) =====
# Get from: https://console.twilio.com
# TWILIO_ACCOUNT_SID=ACxxxxx
# TWILIO_AUTH_TOKEN=xxxxx
# TWILIO_PHONE_NUMBER=+15551234567

# ===== SENDGRID (Optional - for email in Phase 3) =====
# Get from: https://app.sendgrid.com/settings/api_keys
# SENDGRID_API_KEY=SG.xxxxx

# ===== DEVELOPMENT =====
FLASK_ENV=production
PORT=5001
"""

        with open(self.env_example, 'w') as f:
            f.write(content)

        print(f"{GREEN}✅ Created .env.example{RESET}")

    def show_summary(self) -> None:
        """Show migration summary"""

        print(f"\n{'='*60}")
        print(f"{BLUE}📊 Migration Summary{RESET}")
        print(f"{'='*60}\n")

        if not self.issues:
            print(f"{GREEN}✅ All required secrets are configured and valid!{RESET}")
            print(f"{GREEN}✅ Ready to migrate to GitHub Secrets{RESET}\n")
        else:
            print(f"{RED}❌ Found {len(self.issues)} issue(s):{RESET}\n")
            for issue in self.issues:
                print(f"   - {issue}")
            print(f"\n{YELLOW}⚠️  Fix these issues before migrating to production{RESET}\n")

        print(f"{BLUE}Next Steps:{RESET}\n")
        print(f"1. Fix any issues listed above")
        print(f"2. Get real Stripe keys from https://dashboard.stripe.com")
        print(f"3. Run the GitHub CLI commands shown above")
        print(f"4. Or add secrets manually at:")
        print(f"   https://github.com/Soulfra/soulfra/settings/secrets/actions")
        print(f"5. Deploy to GitHub Pages")
        print(f"6. Configure DNS (see DNS_SETUP_GITHUB_PAGES.md)\n")

    def run(self) -> None:
        """Run the migration process"""

        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}  🔐 Soulfra Gateway - Secrets Migration{RESET}")
        print(f"{BLUE}{'='*60}{RESET}\n")

        # Check secrets
        self.check_secrets()

        # Generate GitHub commands
        self.generate_github_commands()

        # Generate .env.example
        self.generate_env_example()

        # Show summary
        self.show_summary()

        # Return exit code
        return 0 if not self.issues else 1


def main():
    """Main entry point"""

    migrator = SecretsMigrator()
    exit_code = migrator.run()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
