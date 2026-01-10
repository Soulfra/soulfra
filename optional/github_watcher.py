#!/usr/bin/env python3
"""
GitHub Watcher - Monitor repos, scrape changes, trigger email automation

NO LIBRARIES. Pure Python standard library only.
Bun/Zig/pot/zzz programming style - build everything from scratch.

What it does:
1. Watch your GitHub repos for changes (poll GitHub API)
2. Scrape new content (commits, issues, PRs)
3. Trigger email automation (send updates via email network)
4. Log everything to local database
5. Run as daemon process (always watching)

Usage:
    python3 github_watcher.py --repos "Soulfra/soulfra,Soulfra/customer-discovery" --interval 60
"""

import os
import sys
import json
import time
import sqlite3
import hashlib
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import argparse

# ==============================================================================
# CONFIG - NO .env file, use environment variables
# ==============================================================================

class Config:
    """Configuration from environment variables"""

    # GitHub
    GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
    GITHUB_API_URL = 'https://api.github.com'

    # Email (for notifications)
    SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
    EMAIL_USER = os.environ.get('EMAIL_USER', '')
    EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD', '')

    # Watcher settings
    POLL_INTERVAL = 60  # seconds
    DATABASE_PATH = 'github_watcher.db'

    # Logging
    LOG_FILE = 'github_watcher.log'


# ==============================================================================
# HTTP CLIENT - NO requests library
# ==============================================================================

class HTTPClient:
    """Minimal HTTP client using urllib only"""

    @staticmethod
    def get(url: str, headers: Dict = None) -> Dict:
        """HTTP GET request"""
        req = Request(url)

        # Add headers
        if headers:
            for key, value in headers.items():
                req.add_header(key, value)

        try:
            with urlopen(req, timeout=10) as response:
                data = response.read().decode('utf-8')
                return json.loads(data)
        except (URLError, HTTPError) as e:
            print(f"HTTP Error: {e}")
            return {}

    @staticmethod
    def post(url: str, data: Dict, headers: Dict = None) -> Dict:
        """HTTP POST request"""
        req = Request(url, data=json.dumps(data).encode('utf-8'), method='POST')

        req.add_header('Content-Type', 'application/json')
        if headers:
            for key, value in headers.items():
                req.add_header(key, value)

        try:
            with urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode('utf-8'))
        except (URLError, HTTPError) as e:
            print(f"HTTP Error: {e}")
            return {}


# ==============================================================================
# DATABASE - SQLite, NO ORMs
# ==============================================================================

class Database:
    """Simple SQLite database for storing watch data"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Create tables if not exist"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Repos being watched
        c.execute('''
            CREATE TABLE IF NOT EXISTS watched_repos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner TEXT NOT NULL,
                repo TEXT NOT NULL,
                last_checked TIMESTAMP,
                last_commit_sha TEXT,
                UNIQUE(owner, repo)
            )
        ''')

        # Events detected
        c.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                repo_id INTEGER,
                event_type TEXT,
                event_data TEXT,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notified INTEGER DEFAULT 0,
                FOREIGN KEY(repo_id) REFERENCES watched_repos(id)
            )
        ''')

        # Email queue
        c.execute('''
            CREATE TABLE IF NOT EXISTS email_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipient TEXT,
                subject TEXT,
                body TEXT,
                sent INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def add_repo(self, owner: str, repo: str):
        """Add repo to watch list"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('''
            INSERT OR IGNORE INTO watched_repos (owner, repo, last_checked)
            VALUES (?, ?, datetime('now'))
        ''', (owner, repo))

        conn.commit()
        conn.close()

    def get_repos(self) -> List[Dict]:
        """Get all watched repos"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('SELECT * FROM watched_repos')
        rows = c.fetchall()
        conn.close()

        repos = []
        for row in rows:
            repos.append({
                'id': row[0],
                'owner': row[1],
                'repo': row[2],
                'last_checked': row[3],
                'last_commit_sha': row[4]
            })
        return repos

    def update_repo(self, repo_id: int, last_commit_sha: str):
        """Update repo last checked info"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('''
            UPDATE watched_repos
            SET last_checked = datetime('now'), last_commit_sha = ?
            WHERE id = ?
        ''', (last_commit_sha, repo_id))

        conn.commit()
        conn.close()

    def add_event(self, repo_id: int, event_type: str, event_data: Dict):
        """Log an event"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('''
            INSERT INTO events (repo_id, event_type, event_data)
            VALUES (?, ?, ?)
        ''', (repo_id, event_type, json.dumps(event_data)))

        conn.commit()
        conn.close()

    def queue_email(self, recipient: str, subject: str, body: str):
        """Add email to queue"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('''
            INSERT INTO email_queue (recipient, subject, body)
            VALUES (?, ?, ?)
        ''', (recipient, subject, body))

        conn.commit()
        conn.close()


# ==============================================================================
# GITHUB API CLIENT - NO PyGithub library
# ==============================================================================

class GitHubAPI:
    """Minimal GitHub API client"""

    def __init__(self, token: str):
        self.token = token
        self.base_url = Config.GITHUB_API_URL
        self.client = HTTPClient()

    def _headers(self) -> Dict:
        """Standard headers for GitHub API"""
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Soulfra-GitHub-Watcher/1.0'
        }
        if self.token:
            headers['Authorization'] = f'token {self.token}'
        return headers

    def get_latest_commit(self, owner: str, repo: str) -> Optional[Dict]:
        """Get latest commit from main/master branch"""
        url = f'{self.base_url}/repos/{owner}/{repo}/commits'
        commits = self.client.get(url, headers=self._headers())

        if commits and len(commits) > 0:
            return commits[0]
        return None

    def get_repo_events(self, owner: str, repo: str) -> List[Dict]:
        """Get recent events for repo"""
        url = f'{self.base_url}/repos/{owner}/{repo}/events'
        return self.client.get(url, headers=self._headers())

    def get_repo_info(self, owner: str, repo: str) -> Dict:
        """Get repo metadata"""
        url = f'{self.base_url}/repos/{owner}/{repo}'
        return self.client.get(url, headers=self._headers())


# ==============================================================================
# EMAIL SENDER - NO external SMTP libraries beyond smtplib
# ==============================================================================

class EmailSender:
    """Send emails via SMTP"""

    def __init__(self):
        self.server = Config.SMTP_SERVER
        self.port = Config.SMTP_PORT
        self.user = Config.EMAIL_USER
        self.password = Config.EMAIL_PASSWORD

    def send(self, recipient: str, subject: str, body: str):
        """Send email"""
        if not self.user or not self.password:
            print("⚠️  Email credentials not configured")
            return False

        msg = MIMEMultipart()
        msg['From'] = self.user
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        try:
            smtp = smtplib.SMTP(self.server, self.port)
            smtp.starttls()
            smtp.login(self.user, self.password)
            smtp.send_message(msg)
            smtp.quit()
            print(f"✅ Email sent to {recipient}")
            return True
        except Exception as e:
            print(f"❌ Email failed: {e}")
            return False


# ==============================================================================
# GITHUB WATCHER - Main watching logic
# ==============================================================================

class GitHubWatcher:
    """Watch GitHub repos for changes"""

    def __init__(self, repos: List[str], interval: int = 60):
        self.repos = repos  # List like ["owner/repo", "owner2/repo2"]
        self.interval = interval
        self.db = Database(Config.DATABASE_PATH)
        self.github = GitHubAPI(Config.GITHUB_TOKEN)
        self.emailer = EmailSender()

        # Add repos to database
        for repo in self.repos:
            owner, repo_name = repo.split('/')
            self.db.add_repo(owner, repo_name)

    def check_repo(self, repo_data: Dict):
        """Check single repo for changes"""
        owner = repo_data['owner']
        repo = repo_data['repo']
        repo_id = repo_data['id']
        last_commit_sha = repo_data['last_commit_sha']

        print(f"🔍 Checking {owner}/{repo}...")

        # Get latest commit
        latest_commit = self.github.get_latest_commit(owner, repo)

        if not latest_commit:
            print(f"  ⚠️  No commits found")
            return

        current_sha = latest_commit['sha']

        # Compare with last known commit
        if last_commit_sha != current_sha:
            print(f"  🆕 New commit detected: {current_sha[:7]}")

            # Log event
            event_data = {
                'sha': current_sha,
                'message': latest_commit['commit']['message'],
                'author': latest_commit['commit']['author']['name'],
                'url': latest_commit['html_url']
            }
            self.db.add_event(repo_id, 'new_commit', event_data)

            # Queue notification email
            subject = f"New commit to {owner}/{repo}"
            body = f"""
New commit detected:

SHA: {current_sha[:7]}
Author: {event_data['author']}
Message: {event_data['message']}
URL: {event_data['url']}

-- Soulfra GitHub Watcher
"""
            self.db.queue_email(Config.EMAIL_USER, subject, body)

            # Update database
            self.db.update_repo(repo_id, current_sha)
        else:
            print(f"  ✅ No changes (still at {current_sha[:7]})")

    def run(self):
        """Main watching loop"""
        print(f"🚀 GitHub Watcher started")
        print(f"   Watching {len(self.repos)} repos")
        print(f"   Polling interval: {self.interval}s")
        print(f"   Database: {Config.DATABASE_PATH}")
        print()

        while True:
            try:
                repos = self.db.get_repos()

                for repo in repos:
                    self.check_repo(repo)
                    time.sleep(1)  # Rate limit between repos

                print(f"\n⏰ Waiting {self.interval}s until next check...")
                time.sleep(self.interval)

            except KeyboardInterrupt:
                print("\n\n🛑 Watcher stopped by user")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                time.sleep(self.interval)


# ==============================================================================
# CLI INTERFACE
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(description='Watch GitHub repos for changes')
    parser.add_argument('--repos', required=True, help='Comma-separated list of repos (owner/repo,owner2/repo2)')
    parser.add_argument('--interval', type=int, default=60, help='Polling interval in seconds')

    args = parser.parse_args()

    repos = [r.strip() for r in args.repos.split(',')]

    watcher = GitHubWatcher(repos, args.interval)
    watcher.run()


if __name__ == '__main__':
    main()
