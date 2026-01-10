#!/usr/bin/env python3
"""
Unified Tribunal Deployment Script

Connects: Laptop Flask → Tribunal Verdicts → Email Notifications → GitHub Pages

What It Does:
1. Scans database for new/updated tribunal verdicts
2. Sends email notifications to participants (Gmail SMTP)
3. Generates static HTML pages for tribunal cases
4. Exports to output/[domain]/ folders
5. Git commits and pushes to your GitHub repos
6. Makes tribunal cases live on GitHub Pages

Usage:
    python3 deploy_tribunal_to_github.py
    python3 deploy_tribunal_to_github.py --send-emails-only
    python3 deploy_tribunal_to_github.py --publish-only
"""

import sqlite3
import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path
from tribunal_email_notifier import TribunalEmailNotifier
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DB_PATH = 'soulfra.db'
OUTPUT_DIR = 'output'
DOMAINS_FILE = 'domains.txt'


class TribunalGitHubDeployer:
    """Deploy tribunal cases to email + GitHub Pages"""

    def __init__(self):
        self.db = sqlite3.connect(DB_PATH)
        self.db.row_factory = sqlite3.Row
        self.email_notifier = TribunalEmailNotifier()
        self.base_url = os.getenv('BASE_URL', 'http://192.168.1.87:5001')

    def get_pending_verdicts(self):
        """Get tribunal verdicts that haven't been published yet"""
        return self.db.execute('''
            SELECT
                ks.id,
                ks.user_id,
                ks.verdict,
                ks.reasoning,
                ks.transcription,
                ks.submitted_at,
                ks.judged_at,
                u.username,
                u.email
            FROM kangaroo_submissions ks
            JOIN users u ON ks.user_id = u.id
            WHERE ks.verdict IS NOT NULL
            AND ks.judged_at IS NOT NULL
            ORDER BY ks.judged_at DESC
        ''').fetchall()

    def get_tribunal_participants(self, submission_id):
        """Get email addresses of all participants in a tribunal case"""
        # Get submitter email
        submitter = self.db.execute('''
            SELECT u.email
            FROM kangaroo_submissions ks
            JOIN users u ON ks.user_id = u.id
            WHERE ks.id = ?
        ''', (submission_id,)).fetchone()

        emails = []
        if submitter and submitter['email']:
            emails.append(submitter['email'])

        # TODO: Add logic to get other participants (message sender/receiver)
        # For now, just return submitter
        return list(set(emails))  # Remove duplicates

    def send_verdict_emails(self, submission_id):
        """Send email notifications for a tribunal verdict"""
        participants = self.get_tribunal_participants(submission_id)

        if not participants:
            print(f"⚠️  No email addresses found for submission {submission_id}")
            return {'success': False, 'error': 'No recipients'}

        print(f"📧 Sending tribunal verdict #{submission_id} to {len(participants)} participant(s)...")
        result = self.email_notifier.send_verdict_notification(submission_id, participants)

        if result['success']:
            print(f"✅ Email sent successfully to {result['sent']} recipient(s)")
            if result.get('failed'):
                print(f"⚠️  Failed to send to: {result['failed']}")
        else:
            print(f"❌ Email failed: {result.get('error')}")

        return result

    def generate_tribunal_html(self, submission):
        """Generate static HTML page for a tribunal case"""
        submission_id = submission['id']
        verdict = submission['verdict']
        reasoning = submission['reasoning'] or 'See full transcript below'
        transcription = submission['transcription'] or 'No transcript available'
        username = submission['username']
        submitted_at = submission['submitted_at']
        judged_at = submission['judged_at']

        # Parse transcription if it's JSON
        try:
            debate_data = json.loads(transcription)
            is_json = True
        except (json.JSONDecodeError, TypeError):
            debate_data = None
            is_json = False

        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tribunal Case #{submission_id} - {verdict}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            border-radius: 12px;
            margin-bottom: 30px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        .verdict-card {{
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        .verdict-badge {{
            display: inline-block;
            padding: 10px 20px;
            border-radius: 25px;
            font-weight: bold;
            text-transform: uppercase;
            font-size: 1.2em;
            margin: 10px 0;
        }}
        .verdict-GUILTY {{ background: #e74c3c; color: white; }}
        .verdict-INNOCENT {{ background: #2ecc71; color: white; }}
        .verdict-NO_CONSENSUS {{ background: #95a5a6; color: white; }}
        .verdict-MONITORING_RECOMMENDED {{ background: #f39c12; color: white; }}
        .verdict-REQUIRES_MORE_DATA {{ background: #3498db; color: white; }}
        .personas {{
            display: grid;
            gap: 20px;
            margin: 30px 0;
        }}
        .persona {{
            background: white;
            padding: 25px;
            border-radius: 12px;
            border-left: 5px solid;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .persona-calriven {{ border-left-color: #3498db; }}
        .persona-soulfra {{ border-left-color: #2ecc71; }}
        .persona-deathtodata {{ border-left-color: #e74c3c; }}
        .persona h3 {{
            margin-bottom: 10px;
            font-size: 1.5em;
        }}
        .transcript {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            white-space: pre-wrap;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            max-height: 600px;
            overflow-y: auto;
        }}
        .metadata {{
            background: #ecf0f1;
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
            font-size: 0.9em;
        }}
        .metadata strong {{
            display: inline-block;
            width: 120px;
        }}
        .footer {{
            text-align: center;
            padding: 30px;
            color: #7f8c8d;
            font-size: 0.9em;
        }}
        .footer a {{
            color: #3498db;
            text-decoration: none;
        }}
        .footer a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚖️ Tribunal Case #{submission_id}</h1>
            <p>3-Way AI Debate System</p>
        </div>

        <div class="verdict-card">
            <h2>Final Verdict</h2>
            <div class="verdict-badge verdict-{verdict}">{verdict}</div>
            <p style="margin-top: 20px;"><strong>Reasoning:</strong> {reasoning}</p>
        </div>

        <div class="personas">
            <div class="persona persona-calriven">
                <h3>🤖 CalRiven (Logic)</h3>
                <p><strong>Philosophy:</strong> Truth through reason and data</p>
                <p><strong>Role:</strong> Logical Prosecutor</p>
                <p>Analyzes cases from an efficiency and analytical reasoning perspective.</p>
            </div>

            <div class="persona persona-soulfra">
                <h3>⚖️ Soulfra (Balance)</h3>
                <p><strong>Philosophy:</strong> Balance between logic and emotion</p>
                <p><strong>Role:</strong> Impartial Judge</p>
                <p>Weighs fairness and seeks truth between both sides.</p>
            </div>

            <div class="persona persona-deathtodata">
                <h3>🔥 DeathToData (Rebellion)</h3>
                <p><strong>Philosophy:</strong> Individual autonomy over authority</p>
                <p><strong>Role:</strong> Rebellious Defender</p>
                <p>Challenges authority and defends individual freedom.</p>
            </div>
        </div>

        <div class="verdict-card">
            <h2>Full Transcript</h2>
            <div class="transcript">{transcription}</div>
        </div>

        <div class="metadata">
            <p><strong>Submitted by:</strong> {username}</p>
            <p><strong>Submitted at:</strong> {submitted_at}</p>
            <p><strong>Judged at:</strong> {judged_at or 'Processing'}</p>
            <p><strong>Case ID:</strong> {submission_id}</p>
        </div>

        <div class="footer">
            <p><strong>About the Soulfra Tribunal</strong></p>
            <p>The Tribunal is a 3-way AI debate system where CalRiven (logic), Soulfra (balance),
            and DeathToData (rebellion) analyze cases from different philosophical perspectives.</p>
            <p style="margin-top: 15px;">
                <a href="{self.base_url}/cringeproof">Play CringeProof</a> to get assigned your own AI persona!
            </p>
            <p style="margin-top: 10px; font-size: 0.8em;">
                Powered by <a href="{self.base_url}">Soulfra</a> |
                Built with Blamechain Edit Tracking
            </p>
        </div>
    </div>
</body>
</html>
'''
        return html

    def export_to_domains(self, submission):
        """Export tribunal case HTML to all configured domains"""
        submission_id = submission['id']
        html = self.generate_tribunal_html(submission)

        # Get list of domains
        domains = []
        if os.path.exists(DOMAINS_FILE):
            with open(DOMAINS_FILE, 'r') as f:
                domains = [line.strip() for line in f if line.strip()]

        if not domains:
            print("⚠️  No domains configured in domains.txt")
            # Export to default output directory
            domains = ['tribunal']

        exported_count = 0
        for domain in domains:
            # Create output directory structure
            domain_dir = Path(OUTPUT_DIR) / domain / 'tribunal'
            domain_dir.mkdir(parents=True, exist_ok=True)

            # Write HTML file
            output_file = domain_dir / f'case-{submission_id}.html'
            output_file.write_text(html)
            print(f"✅ Exported to {output_file}")
            exported_count += 1

            # Create index page listing all cases
            self.create_tribunal_index(domain)

        return exported_count

    def create_tribunal_index(self, domain):
        """Create index page listing all tribunal cases for a domain"""
        domain_dir = Path(OUTPUT_DIR) / domain / 'tribunal'

        # Get all verdicts
        verdicts = self.get_pending_verdicts()

        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Soulfra Tribunal - All Cases</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            border-radius: 12px;
            margin-bottom: 30px;
            text-align: center;
        }}
        .case-list {{
            display: grid;
            gap: 20px;
        }}
        .case-card {{
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-left: 5px solid #3498db;
        }}
        .case-card:hover {{
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            transform: translateY(-2px);
            transition: all 0.3s;
        }}
        .verdict-badge {{
            display: inline-block;
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 0.85em;
            font-weight: bold;
            text-transform: uppercase;
        }}
        .verdict-GUILTY {{ background: #e74c3c; color: white; }}
        .verdict-INNOCENT {{ background: #2ecc71; color: white; }}
        .verdict-NO_CONSENSUS {{ background: #95a5a6; color: white; }}
        .verdict-MONITORING_RECOMMENDED {{ background: #f39c12; color: white; }}
        .verdict-REQUIRES_MORE_DATA {{ background: #3498db; color: white; }}
        a {{
            color: #3498db;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚖️ Soulfra Tribunal</h1>
            <p>3-Way AI Debate System - All Cases</p>
        </div>

        <div class="case-list">
'''

        for verdict in verdicts:
            html += f'''
            <div class="case-card">
                <h3>Case #{verdict['id']}: {verdict['username']}</h3>
                <p><span class="verdict-badge verdict-{verdict['verdict']}">{verdict['verdict']}</span></p>
                <p>{verdict['reasoning'] or 'See full case details'}</p>
                <p><strong>Decided:</strong> {verdict['judged_at'] or 'Processing'}</p>
                <p><a href="case-{verdict['id']}.html">View Full Debate →</a></p>
            </div>
'''

        html += '''
        </div>
    </div>
</body>
</html>
'''

        index_file = domain_dir / 'index.html'
        index_file.write_text(html)
        print(f"✅ Created index at {index_file}")

    def git_push_to_repos(self, domain):
        """Git commit and push to GitHub repo for domain"""
        domain_dir = Path(OUTPUT_DIR) / domain

        if not domain_dir.exists():
            print(f"⚠️  Domain directory {domain_dir} doesn't exist")
            return False

        try:
            # Check if it's a git repo
            result = subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                cwd=domain_dir,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                print(f"⚠️  {domain_dir} is not a git repository")
                print(f"   Initialize with: cd {domain_dir} && git init && git remote add origin <repo-url>")
                return False

            # Git add
            subprocess.run(['git', 'add', '.'], cwd=domain_dir, check=True)

            # Git commit
            commit_msg = f"Update tribunal cases - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            subprocess.run(
                ['git', 'commit', '-m', commit_msg],
                cwd=domain_dir,
                capture_output=True
            )

            # Git push
            push_result = subprocess.run(
                ['git', 'push', 'origin', 'main'],
                cwd=domain_dir,
                capture_output=True,
                text=True
            )

            if push_result.returncode == 0:
                print(f"✅ Pushed to GitHub for {domain}")
                return True
            else:
                print(f"⚠️  Git push failed for {domain}: {push_result.stderr}")
                return False

        except subprocess.CalledProcessError as e:
            print(f"❌ Git operation failed: {e}")
            return False

    def deploy_all(self, send_emails=True, publish_to_github=True):
        """Full deployment: emails + static HTML + GitHub push"""
        print("🚀 Starting Tribunal Deployment\n")
        print("=" * 60)

        verdicts = self.get_pending_verdicts()

        if not verdicts:
            print("ℹ️  No tribunal verdicts found in database")
            return

        print(f"📋 Found {len(verdicts)} tribunal case(s)\n")

        for verdict in verdicts:
            submission_id = verdict['id']
            print(f"\n--- Case #{submission_id} ({verdict['verdict']}) ---")

            # Step 1: Send email notifications
            if send_emails:
                self.send_verdict_emails(submission_id)

            # Step 2: Generate static HTML
            exported = self.export_to_domains(verdict)
            print(f"📄 Exported to {exported} domain(s)")

        # Step 3: Push to GitHub
        if publish_to_github:
            print("\n📤 Publishing to GitHub...\n")
            domains = []
            if os.path.exists(DOMAINS_FILE):
                with open(DOMAINS_FILE, 'r') as f:
                    domains = [line.strip() for line in f if line.strip()]
            else:
                domains = ['tribunal']

            for domain in domains:
                self.git_push_to_repos(domain)

        print("\n" + "=" * 60)
        print("✅ Deployment complete!\n")
        print(f"🌐 Tribunal cases are now live on your GitHub Pages")
        print(f"📧 Email notifications sent to participants")
        print(f"📂 Static files in: {OUTPUT_DIR}/")

    def close(self):
        """Close database connection"""
        self.db.close()


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Deploy Soulfra Tribunal to Email + GitHub Pages'
    )
    parser.add_argument(
        '--send-emails-only',
        action='store_true',
        help='Only send email notifications (no GitHub publish)'
    )
    parser.add_argument(
        '--publish-only',
        action='store_true',
        help='Only publish to GitHub (no emails)'
    )

    args = parser.parse_args()

    deployer = TribunalGitHubDeployer()

    try:
        if args.send_emails_only:
            deployer.deploy_all(send_emails=True, publish_to_github=False)
        elif args.publish_only:
            deployer.deploy_all(send_emails=False, publish_to_github=True)
        else:
            deployer.deploy_all(send_emails=True, publish_to_github=True)
    finally:
        deployer.close()


if __name__ == '__main__':
    main()
