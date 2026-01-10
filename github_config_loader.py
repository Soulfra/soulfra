#!/usr/bin/env python3
"""
GitHub Config Loader - Load domain configuration from GitHub README.md

Each domain (soulfra, calriven, deathtodata, cringeproof) reads its config
from github.com/Soulfra/{domain}/README.md

Config format (YAML frontmatter in markdown):
```markdown
---
domain:
  primary: soulfra.com
  fallback: soulfra.github.io
  dns: CNAME

content_sources:
  - github.com/Soulfra/calriven/posts
  - github.com/Soulfra/deathtodata/data

ai_training:
  transcripts: /transcripts/*.md
  comments: /comments/*.json
  ideas: /ideas/*.txt

routing:
  calriven: blog
  deathtodata: data
  cringeproof: filter
---

# Soulfra Domain

Main hub for all Soulfra brands...
```

Usage:
    python3 github_config_loader.py load soulfra
    python3 github_config_loader.py load calriven
    python3 github_config_loader.py sync-all
"""

import requests
import yaml
import re
from database import get_db
from datetime import datetime, timezone
import json


class GitHubConfigLoader:
    """
    Load domain configuration from GitHub README.md files
    """

    def __init__(self, org="Soulfra"):
        self.org = org
        self.base_url = f"https://raw.githubusercontent.com/{org}"

    def fetch_readme(self, repo_name, branch="main"):
        """
        Fetch README.md from GitHub repo

        Args:
            repo_name (str): Repository name (e.g., "soulfra.github.io")
            branch (str): Branch name (default: "main")

        Returns:
            str: README.md content
        """
        url = f"{self.base_url}/{repo_name}/{branch}/README.md"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to fetch {url}: {e}")
            return None

    def parse_config(self, readme_content):
        """
        Parse YAML frontmatter from README.md

        Args:
            readme_content (str): Full README.md content

        Returns:
            dict: Parsed configuration
        """
        if not readme_content:
            return {}

        # Extract YAML frontmatter (between --- delimiters)
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', readme_content, re.DOTALL)

        if not frontmatter_match:
            print("⚠️  No YAML frontmatter found in README.md")
            return {}

        yaml_content = frontmatter_match.group(1)

        try:
            config = yaml.safe_load(yaml_content)
            return config
        except yaml.YAMLError as e:
            print(f"❌ Failed to parse YAML: {e}")
            return {}

    def load_domain_config(self, domain_name):
        """
        Load configuration for a specific domain

        Args:
            domain_name (str): Domain name (e.g., "soulfra", "calriven")

        Returns:
            dict: Domain configuration
        """
        # Map domain names to repo names
        repo_map = {
            "soulfra": "soulfra.github.io",
            "calriven": "calriven",
            "deathtodata": "deathtodata",
            "cringeproof": "cringeproof"
        }

        repo_name = repo_map.get(domain_name, domain_name)

        print(f"\n{'='*60}")
        print(f"Loading config for: {domain_name}")
        print(f"Repository: github.com/{self.org}/{repo_name}")
        print(f"{'='*60}\n")

        # Fetch README
        readme = self.fetch_readme(repo_name)

        if not readme:
            print(f"❌ Failed to load config for {domain_name}")
            return {}

        # Parse config
        config = self.parse_config(readme)

        if not config:
            print(f"⚠️  No config found for {domain_name}")
            return {}

        print(f"✅ Config loaded for {domain_name}")
        print(json.dumps(config, indent=2))

        return config

    def save_config_to_db(self, domain_name, config):
        """
        Save loaded config to database

        Args:
            domain_name (str): Domain name
            config (dict): Configuration dict

        Returns:
            int: Number of rows updated
        """
        db = get_db()

        # Create domain_configs table if doesn't exist
        db.execute('''
            CREATE TABLE IF NOT EXISTS domain_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain_name TEXT UNIQUE NOT NULL,
                config TEXT NOT NULL,
                loaded_at TEXT NOT NULL,
                repo_url TEXT
            )
        ''')

        loaded_at = datetime.now(timezone.utc).isoformat()
        repo_url = f"https://github.com/{self.org}/{domain_name}"
        config_json = json.dumps(config)

        # Upsert config
        db.execute('''
            INSERT INTO domain_configs (domain_name, config, loaded_at, repo_url)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(domain_name) DO UPDATE SET
                config = excluded.config,
                loaded_at = excluded.loaded_at
        ''', (domain_name, config_json, loaded_at, repo_url))

        db.commit()

        print(f"✅ Config saved to database for {domain_name}")

        return 1

    def get_config_from_db(self, domain_name):
        """
        Get cached config from database

        Args:
            domain_name (str): Domain name

        Returns:
            dict: Config dict or None
        """
        db = get_db()

        row = db.execute('''
            SELECT config, loaded_at FROM domain_configs
            WHERE domain_name = ?
        ''', (domain_name,)).fetchone()

        if not row:
            return None

        config = json.loads(row['config'])
        loaded_at = row['loaded_at']

        print(f"✅ Config loaded from database (cached at {loaded_at})")

        return config

    def sync_all_domains(self):
        """
        Sync configs for all domains from GitHub

        Returns:
            dict: Results for each domain
        """
        domains = ["soulfra", "calriven", "deathtodata", "cringeproof"]
        results = {}

        print(f"\n{'='*60}")
        print(f"SYNCING ALL DOMAIN CONFIGS FROM GITHUB")
        print(f"{'='*60}\n")

        for domain in domains:
            config = self.load_domain_config(domain)
            if config:
                self.save_config_to_db(domain, config)
                results[domain] = "success"
            else:
                results[domain] = "failed"

        print(f"\n{'='*60}")
        print(f"SYNC COMPLETE")
        print(f"{'='*60}")

        for domain, status in results.items():
            icon = "✅" if status == "success" else "❌"
            print(f"{icon} {domain}: {status}")

        return results


def create_example_readme():
    """
    Create example README.md with config frontmatter

    Returns:
        str: Example README content
    """
    example = """---
domain:
  primary: soulfra.com
  fallback: soulfra.github.io
  dns: CNAME

content_sources:
  - github.com/Soulfra/calriven/posts
  - github.com/Soulfra/deathtodata/data

ai_training:
  transcripts: /transcripts/*.md
  comments: /comments/*.json
  ideas: /ideas/*.txt

routing:
  calriven: blog
  deathtodata: data
  cringeproof: filter

pagerank:
  enabled: true
  recalculate: daily
  factors:
    incoming_links: 0.4
    external_refs: 0.3
    views: 0.2
    freshness: 0.1

matching:
  enabled: true
  confidence_threshold: 0.80
  gap_sources:
    - /work/gaps.csv
    - /work/trends.json
---

# Soulfra - Voice-Powered Publishing Platform

Main hub for all Soulfra brands.

## Features

- Voice → Cal → Blog automation
- PageRank with logarithmic decay
- Multi-domain routing
- AI idea matching

## Domains

- **Soulfra**: Hub (Python/Flask)
- **Calriven**: Blog (Markdown)
- **DeathToData**: Data (JSON/API)
- **Cringeproof**: Filtering (Real-time)

## Usage

Visit [soulfra.github.io](https://soulfra.github.io) to get started.
"""

    return example


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 github_config_loader.py load <domain>")
        print("  python3 github_config_loader.py sync-all")
        print("  python3 github_config_loader.py example")
        print("  python3 github_config_loader.py cached <domain>")
        sys.exit(1)

    command = sys.argv[1]
    loader = GitHubConfigLoader()

    if command == "load":
        if len(sys.argv) < 3:
            print("Usage: python3 github_config_loader.py load <domain>")
            sys.exit(1)

        domain = sys.argv[2]
        config = loader.load_domain_config(domain)

        if config:
            loader.save_config_to_db(domain, config)

    elif command == "sync-all":
        results = loader.sync_all_domains()

    elif command == "example":
        print("Example README.md with config:")
        print(create_example_readme())

    elif command == "cached":
        if len(sys.argv) < 3:
            print("Usage: python3 github_config_loader.py cached <domain>")
            sys.exit(1)

        domain = sys.argv[2]
        config = loader.get_config_from_db(domain)

        if config:
            print(json.dumps(config, indent=2))
        else:
            print(f"❌ No cached config for {domain}")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
