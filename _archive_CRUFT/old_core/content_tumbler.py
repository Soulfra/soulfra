#!/usr/bin/env python3
"""
Content Tumbler - The Insane System That Connects Everything

This is the VISION you described:
- Multi-port Ollama → Generate variations
- GitHub Faucet → Gate access by tier
- Unified Generator → SHA-256 → UPC → QR codes
- Projects System → Auto-generate announcements
- Domains → Deploy to GitHub Pages
- Affiliates → Track who generated what

Like CringeProof chapters but for EVERYTHING - one page at a time,
generated across multiple AI models, scored, deployed automatically.

A slot machine that spins:
  [llama3] [mistral] [codellama] [llama3-wild]
     ↓         ↓          ↓            ↓
  Technical Creative    Code      Experimental
     ↓         ↓          ↓            ↓
  Pick best → SHA-256 → UPC → QR → GitHub Pages

Usage:
    from content_tumbler import ContentTumbler

    tumbler = ContentTumbler()

    # Generate CringeProof announcement across all ports
    result = tumbler.spin(
        project_slug='cringeproof',
        content_type='announcement',
        user_id=1  # Gated by GitHub faucet tier
    )

    # Returns best variation + all tracking codes
"""

import sys
from pathlib import Path
from database import get_db
from multi_port_ollama import MultiPortOllama
from typing import Dict, List, Optional
import hashlib
import json
from datetime import datetime

# Try to import unified generator components
try:
    from unified_generator import generate_upc_from_hash
    from vanity_qr import create_and_save_vanity_qr, generate_short_code
    GENERATOR_AVAILABLE = True
except ImportError:
    GENERATOR_AVAILABLE = False
    print("⚠️  Unified generator not available - tumbler will work without UPC/QR generation")

# Try to import GitHub faucet for tier checking
try:
    from github_faucet import GitHubFaucet
    FAUCET_AVAILABLE = True
except ImportError:
    FAUCET_AVAILABLE = False
    print("⚠️  GitHub faucet not available - tumbler will work without tier gating")


# =============================================================================
# CONTENT TUMBLER CLASS
# =============================================================================

class ContentTumbler:
    """
    The wild content generation system that connects EVERYTHING

    Think of this as a slot machine where:
    - Each reel = different Ollama port/model
    - Pull the lever = generate content variations
    - Winning combo = best response gets deployed
    - Payout = SHA-256, UPC, QR codes, GitHub Pages deployment
    """

    def __init__(self):
        self.ollama = MultiPortOllama()
        self.faucet = GitHubFaucet() if FAUCET_AVAILABLE else None

    def check_user_tier(self, user_id: int) -> int:
        """
        Check user's access tier from GitHub faucet

        Args:
            user_id: User ID

        Returns:
            Tier level (0-4)
        """
        if not self.faucet:
            return 0  # Default tier if faucet not available

        db = get_db()

        # Get user's API key
        api_key = db.execute('''
            SELECT * FROM api_keys WHERE user_id = ?
        ''', (user_id,)).fetchone()

        db.close()

        if not api_key:
            return 0

        # Tier is stored in api_key metadata
        try:
            metadata = json.loads(api_key['metadata']) if api_key.get('metadata') else {}
            return metadata.get('tier', 0)
        except:
            return 0

    def get_allowed_ports_for_tier(self, tier: int) -> List[int]:
        """
        Get ports user can access based on tier

        Tier 0: Port 11434 only (single model)
        Tier 1: Ports 11434, 11435 (2 models)
        Tier 2: Ports 11434, 11435, 11436 (3 models)
        Tier 3+: All ports (4 models) - FULL TUMBLER!

        Args:
            tier: User tier (0-4)

        Returns:
            List of allowed port numbers
        """
        port_tiers = {
            0: [11434],
            1: [11434, 11435],
            2: [11434, 11435, 11436],
            3: [11434, 11435, 11436, 11437],
            4: [11434, 11435, 11436, 11437]
        }

        return port_tiers.get(tier, [11434])

    def generate_prompt_for_project(self, project_slug: str,
                                    content_type: str) -> str:
        """
        Generate AI prompt based on project and content type

        Args:
            project_slug: Project slug (e.g., 'cringeproof')
            content_type: Type of content ('announcement', 'blog_post', 'readme', etc.)

        Returns:
            Formatted prompt string
        """
        db = get_db()

        # Get project details
        project = db.execute('''
            SELECT * FROM projects WHERE slug = ?
        ''', (project_slug,)).fetchone()

        db.close()

        if not project:
            return f"Write a {content_type} for a project called {project_slug}"

        # Build context-aware prompt
        prompts = {
            'announcement': f"""Write a compelling announcement for {project['name']}.

Project: {project['name']}
Tagline: {project['tagline']}
Domain: {project['primary_domain']}
GitHub: {project['github_owner']}/{project['github_repo']}

The announcement should:
- Explain what the project is
- Why it's interesting
- How people can contribute
- How they earn ownership (Year 1 build phase)
- Link to GitHub repo

Keep it under 300 words. Use markdown formatting.""",

            'readme': f"""Write a README.md for {project['name']}.

Project: {project['name']}
Tagline: {project['tagline']}

Include:
- ## What is {project['name']}?
- ## Features
- ## How to Contribute
- ## Ownership Model
- ## Installation
- ## Usage

Use markdown, code blocks, and badges.""",

            'blog_post': f"""Write a blog post announcing {project['name']}.

Project: {project['name']}
Tagline: {project['tagline']}

Write in first person, explain:
- Why I built this
- What makes it unique
- How the collaborative ownership model works
- Call to action to contribute

Make it personal and engaging, 400-600 words."""
        }

        return prompts.get(content_type, f"Write a {content_type} for {project['name']}")

    def spin(self, project_slug: str,
            content_type: str = 'announcement',
            user_id: Optional[int] = None,
            custom_prompt: Optional[str] = None) -> Dict:
        """
        SPIN THE TUMBLER!

        This is the main function - generates content across multiple
        Ollama ports, picks the best one, generates all tracking codes.

        Args:
            project_slug: Project to generate for
            content_type: Type of content
            user_id: User ID (for tier gating)
            custom_prompt: Override auto-generated prompt

        Returns:
            Dict with best_result, all_results, tracking_codes, etc.
        """
        print(f"\n🎰 SPINNING THE TUMBLER FOR: {project_slug}\n")

        # Check user tier
        tier = 0
        if user_id:
            tier = self.check_user_tier(user_id)
            print(f"User Tier: {tier}")

        # Get allowed ports
        allowed_ports = self.get_allowed_ports_for_tier(tier)
        print(f"Allowed Ports: {allowed_ports}")

        # Check which ports are alive
        port_status = self.ollama.check_all_ports()
        alive_ports = [p for p in allowed_ports if port_status.get(p)]

        if not alive_ports:
            return {
                "success": False,
                "error": "No Ollama ports available",
                "tier": tier,
                "allowed_ports": allowed_ports
            }

        print(f"Active Ports: {alive_ports}\n")

        # Generate prompt
        prompt = custom_prompt or self.generate_prompt_for_project(project_slug, content_type)
        print(f"Prompt:\n{prompt[:200]}...\n")

        # SPIN THE TUMBLER - generate on all ports in parallel
        print("🎰 Generating across all ports...\n")
        results = self.ollama.generate_parallel(prompt, ports=alive_ports)

        # Pick best result
        best = self.ollama.pick_best(results)

        if not best or best.get("error"):
            return {
                "success": False,
                "error": "All ports failed",
                "results": results
            }

        print(f"✅ Winner: Port {best['port']} ({best['name']}) - Score: {best['score']:.1f}/100\n")

        # Generate tracking codes
        tracking = self._generate_tracking_codes(
            content=best['response'],
            project_slug=project_slug,
            content_type=content_type
        )

        # Save to database
        tumble_id = self._save_tumble_result(
            project_slug=project_slug,
            content_type=content_type,
            best_result=best,
            all_results=results,
            tracking_codes=tracking,
            user_id=user_id
        )

        return {
            "success": True,
            "tumble_id": tumble_id,
            "project_slug": project_slug,
            "content_type": content_type,
            "tier": tier,
            "ports_used": alive_ports,
            "best_result": best,
            "all_results": results,
            "tracking_codes": tracking,
            "comparison_report": self.ollama.compare_results(results)
        }

    def _generate_tracking_codes(self, content: str,
                                 project_slug: str,
                                 content_type: str) -> Dict:
        """
        Generate SHA-256 → UPC → QR tracking codes

        Args:
            content: Generated content
            project_slug: Project slug
            content_type: Content type

        Returns:
            Dict with sha256, upc, qr_code_url, etc.
        """
        # Generate SHA-256 hash
        sha256 = hashlib.sha256(content.encode()).hexdigest()

        tracking = {
            "sha256": sha256,
            "content_length": len(content)
        }

        # Generate UPC if generator available
        if GENERATOR_AVAILABLE:
            try:
                upc = generate_upc_from_hash(sha256, content_type)
                tracking["upc"] = upc

                # Generate QR code
                qr_short_code = generate_short_code()
                qr_url = f"https://{project_slug}.com/tumble/{qr_short_code}"

                # This would save QR to database
                # qr_id = create_and_save_vanity_qr(qr_url, short_code=qr_short_code)

                tracking["qr_code"] = qr_short_code
                tracking["qr_url"] = qr_url

            except Exception as e:
                tracking["generator_error"] = str(e)

        return tracking

    def _save_tumble_result(self, project_slug: str,
                           content_type: str,
                           best_result: Dict,
                           all_results: List[Dict],
                           tracking_codes: Dict,
                           user_id: Optional[int] = None) -> int:
        """
        Save tumble result to database

        Creates a record of:
        - What was generated
        - Which ports were used
        - Scores for each variation
        - Tracking codes
        - Who generated it

        Args:
            project_slug: Project slug
            content_type: Content type
            best_result: Best generation result
            all_results: All results from all ports
            tracking_codes: SHA-256, UPC, QR codes
            user_id: User who ran the tumble

        Returns:
            Tumble ID
        """
        db = get_db()

        # Get project ID
        project = db.execute('''
            SELECT id FROM projects WHERE slug = ?
        ''', (project_slug,)).fetchone()

        project_id = project['id'] if project else None

        # Insert tumble record
        cursor = db.execute('''
            INSERT INTO content_tumbles
            (project_id, project_slug, content_type, user_id,
             best_port, best_model, best_score, best_content,
             tracking_codes, all_results, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        ''', (
            project_id,
            project_slug,
            content_type,
            user_id,
            best_result.get('port'),
            best_result.get('model'),
            best_result.get('score'),
            best_result.get('response'),
            json.dumps(tracking_codes),
            json.dumps(all_results)
        ))

        tumble_id = cursor.lastrowid
        db.commit()
        db.close()

        return tumble_id


# =============================================================================
# DATABASE SCHEMA
# =============================================================================

def create_tumbler_tables():
    """Create database tables for content tumbler"""
    db = get_db()

    db.execute('''
        CREATE TABLE IF NOT EXISTS content_tumbles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            project_slug TEXT NOT NULL,
            content_type TEXT NOT NULL,
            user_id INTEGER,
            best_port INTEGER,
            best_model TEXT,
            best_score REAL,
            best_content TEXT,
            tracking_codes TEXT,
            all_results TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )
    ''')

    db.commit()
    db.close()

    print("✅ Tumbler tables created")


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Content Tumbler - Spin the AI slot machine!')
    parser.add_argument('command', choices=['setup', 'spin', 'list'],
                       help='Command to run')
    parser.add_argument('--project', help='Project slug')
    parser.add_argument('--type', default='announcement',
                       help='Content type (announcement, readme, blog_post)')
    parser.add_argument('--user-id', type=int, help='User ID for tier gating')

    args = parser.parse_args()

    if args.command == 'setup':
        create_tumbler_tables()
        return 0

    if args.command == 'spin':
        if not args.project:
            print("❌ --project required")
            return 1

        tumbler = ContentTumbler()
        result = tumbler.spin(
            project_slug=args.project,
            content_type=args.type,
            user_id=args.user_id
        )

        if result['success']:
            print("\n" + "="*70)
            print("🎉 TUMBLE COMPLETE!")
            print("="*70)
            print(f"\nTumble ID: {result['tumble_id']}")
            print(f"Project: {result['project_slug']}")
            print(f"Type: {result['content_type']}")
            print(f"Tier: {result['tier']}")
            print(f"Ports Used: {result['ports_used']}")
            print(f"\nBest Result:")
            print(f"  Port: {result['best_result']['port']} ({result['best_result']['name']})")
            print(f"  Model: {result['best_result']['model']}")
            print(f"  Score: {result['best_result']['score']:.1f}/100")
            print(f"\nTracking Codes:")
            for key, value in result['tracking_codes'].items():
                print(f"  {key}: {value}")
            print(f"\nGenerated Content:\n")
            print(result['best_result']['response'])
            print("\n" + "="*70)

        else:
            print(f"❌ Tumble failed: {result.get('error')}")
            return 1

    if args.command == 'list':
        db = get_db()
        tumbles = db.execute('''
            SELECT * FROM content_tumbles
            ORDER BY created_at DESC
            LIMIT 10
        ''').fetchall()
        db.close()

        print("\n📋 Recent Tumbles:\n")
        for tumble in tumbles:
            print(f"[{tumble['id']}] {tumble['project_slug']} - {tumble['content_type']}")
            print(f"    Port {tumble['best_port']} ({tumble['best_model']}) - Score: {tumble['best_score']:.1f}")
            print(f"    {tumble['created_at']}")
            print()

    return 0


if __name__ == '__main__':
    sys.exit(main())
