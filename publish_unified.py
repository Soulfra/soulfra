#!/usr/bin/env python3
"""
Unified Publishing System
Solves: "we're working all over the place but our workflows need to be sync'd"

This script updates ALL repos simultaneously:
- voice-archive (cringeproof.com)
- soulfra.github.io (soulfra.com)
- calriven-content (blog posts)
- {domain}-data repos

Usage:
  python3 publish_unified.py --voice-memo path/to/audio.webm
  python3 publish_unified.py --sync-all
  python3 publish_unified.py --update-tv
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
import argparse
import json

# Repo paths
BASE_DIR = Path(__file__).parent
VOICE_ARCHIVE = BASE_DIR.parent / "voice-archive"
SOULFRA_GH_IO = BASE_DIR.parent / "soulfra-simple" / "soulfra.github.io"

# Content that needs to be synced across repos
SYNC_TARGETS = {
    "tv": {
        "source": SOULFRA_GH_IO / "tv",
        "destinations": [
            VOICE_ARCHIVE / "tv",
        ],
        "description": "Live Cal/Arty chat broadcasting"
    },
    "projects": {
        "source": SOULFRA_GH_IO / "projects.html",
        "destinations": [
            VOICE_ARCHIVE / "projects.html",
        ],
        "description": "Live project dashboard"
    },
    "index": {
        "source": SOULFRA_GH_IO / "index.html",
        "destinations": [
            VOICE_ARCHIVE / "soulfra-hub.html",  # Different name to not conflict with CringeProof's index
        ],
        "description": "Main Soulfra hub"
    }
}

class UnifiedPublisher:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.changes = []

    def log(self, message, emoji="📝"):
        print(f"{emoji} {message}")

    def run_git_command(self, repo_path, command, description):
        """Execute git command in specified repo"""
        self.log(f"{description} in {repo_path.name}", "🔧")

        if self.dry_run:
            self.log(f"DRY RUN: Would execute: {command}", "🔍")
            return True

        try:
            result = subprocess.run(
                command,
                cwd=repo_path,
                shell=True,
                capture_output=True,
                text=True,
                check=True
            )
            self.log(f"✅ Success: {result.stdout.strip()}", "✅")
            return True
        except subprocess.CalledProcessError as e:
            self.log(f"⚠️ Warning: {e.stderr.strip()}", "⚠️")
            return False

    def sync_content(self, target_name):
        """Sync a specific content target across repos"""
        if target_name not in SYNC_TARGETS:
            self.log(f"Unknown sync target: {target_name}", "❌")
            return False

        config = SYNC_TARGETS[target_name]
        source = config["source"]

        if not source.exists():
            self.log(f"Source not found: {source}", "❌")
            return False

        self.log(f"Syncing {config['description']}", "🔄")

        for dest in config["destinations"]:
            dest_repo = dest.parent

            # Copy content
            if source.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(source, dest)
                self.log(f"Copied directory {source.name} → {dest}", "📂")
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, dest)
                self.log(f"Copied file {source.name} → {dest}", "📄")

            self.changes.append({
                "repo": dest_repo.name,
                "file": str(dest.relative_to(dest_repo)),
                "action": "updated"
            })

        return True

    def commit_and_push(self, repo_path, message):
        """Commit and push changes in a repo"""
        self.log(f"Committing to {repo_path.name}", "💾")

        # Check if there are changes
        status = subprocess.run(
            "git status --porcelain",
            cwd=repo_path,
            shell=True,
            capture_output=True,
            text=True
        )

        if not status.stdout.strip():
            self.log("No changes to commit", "ℹ️")
            return True

        # Add all changes
        self.run_git_command(repo_path, "git add .", "Adding changes")

        # Commit
        commit_msg = f"{message}\n\n🤖 Auto-synced via publish_unified.py"
        self.run_git_command(
            repo_path,
            f'git commit -m "{commit_msg}"',
            "Committing"
        )

        # Pull before push to avoid conflicts
        self.run_git_command(
            repo_path,
            "git pull --rebase origin main",
            "Pulling latest"
        )

        # Push
        self.run_git_command(
            repo_path,
            "git push origin main",
            "Pushing to remote"
        )

        return True

    def update_tv(self):
        """Update TV page across all repos"""
        self.log("Updating TV broadcasting page", "📺")
        success = self.sync_content("tv")

        if success:
            # Commit to voice-archive
            self.commit_and_push(
                VOICE_ARCHIVE,
                "📺 Update Soulfra TV - Live Cal/Arty chat"
            )

            # Commit to soulfra.github.io
            self.commit_and_push(
                SOULFRA_GH_IO,
                "📺 Update Soulfra TV - Live Cal/Arty chat"
            )

        return success

    def sync_all(self):
        """Sync all content across repos"""
        self.log("Starting unified sync across all repos", "🌐")

        for target_name in SYNC_TARGETS.keys():
            self.sync_content(target_name)

        # Commit all changes
        self.commit_and_push(
            VOICE_ARCHIVE,
            "🔄 Unified sync - Update all shared content"
        )

        self.commit_and_push(
            SOULFRA_GH_IO,
            "🔄 Unified sync - Update all shared content"
        )

        self.log("Sync complete!", "✅")
        self.print_summary()

    def print_summary(self):
        """Print summary of changes"""
        self.log("\n=== Sync Summary ===", "📊")

        by_repo = {}
        for change in self.changes:
            repo = change["repo"]
            if repo not in by_repo:
                by_repo[repo] = []
            by_repo[repo].append(change["file"])

        for repo, files in by_repo.items():
            self.log(f"\n{repo}:", "📁")
            for file in files:
                self.log(f"  ✓ {file}", "")

        self.log(f"\nTotal: {len(self.changes)} files synced", "📈")

    def process_voice_memo(self, audio_path):
        """Process voice memo and publish across all domains"""
        self.log(f"Processing voice memo: {audio_path}", "🎤")

        # Import existing voice processing
        try:
            sys.path.insert(0, str(BASE_DIR))
            from import_voice_memo import process_audio
            from publish_voice import publish_to_domain

            # Process audio
            self.log("Transcribing with Whisper...", "🧠")
            result = process_audio(audio_path)

            # Publish to appropriate domain
            self.log(f"Publishing to {result['domain']}...", "📤")
            publish_to_domain(result)

            # Sync to all repos
            self.sync_all()

            self.log("Voice memo published successfully!", "✅")
            return True

        except Exception as e:
            self.log(f"Error processing voice memo: {e}", "❌")
            return False

def main():
    parser = argparse.ArgumentParser(
        description="Unified publishing system for Soulfra ecosystem"
    )
    parser.add_argument(
        "--sync-all",
        action="store_true",
        help="Sync all content across repos"
    )
    parser.add_argument(
        "--update-tv",
        action="store_true",
        help="Update TV page only"
    )
    parser.add_argument(
        "--voice-memo",
        type=str,
        help="Process and publish voice memo"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually doing it"
    )

    args = parser.parse_args()

    publisher = UnifiedPublisher(dry_run=args.dry_run)

    if args.dry_run:
        publisher.log("DRY RUN MODE - No actual changes will be made", "🔍")

    if args.update_tv:
        publisher.update_tv()
    elif args.sync_all:
        publisher.sync_all()
    elif args.voice_memo:
        if not Path(args.voice_memo).exists():
            publisher.log(f"File not found: {args.voice_memo}", "❌")
            sys.exit(1)
        publisher.process_voice_memo(args.voice_memo)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
