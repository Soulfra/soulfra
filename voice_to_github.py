#!/usr/bin/env python3
"""
Voice to GitHub Issue Converter

Converts voice memo transcripts into structured GitHub issues using Ollama for idea extraction.

Usage:
    python3 voice_to_github.py recording.m4a
    python3 voice_to_github.py recording.m4a --labels feature,ui
    python3 voice_to_github.py recording.m4a --dry-run

Environment Variables:
    GITHUB_TOKEN_FOR_ISSUES - GitHub personal access token with repo scope
    GITHUB_REPO - Repository name (e.g., "username/soulfra-simple")
"""

import os
import sys
import json
import argparse
from typing import Dict, List
import requests
from pathlib import Path

# Import voice processing modules
try:
    from voice_memo_dissector import VoiceMemoDissector
except ImportError:
    print("⚠️  voice_memo_dissector.py not found")
    sys.exit(1)


class VoiceToGitHub:
    """
    Convert voice memos to GitHub issues
    """

    def __init__(self, github_token: str = None, repo: str = None):
        """
        Initialize voice-to-GitHub converter

        Args:
            github_token: GitHub personal access token
            repo: Repository name (username/repo)
        """
        self.github_token = github_token or os.environ.get('GITHUB_TOKEN_FOR_ISSUES')
        self.repo = repo or os.environ.get('GITHUB_REPO', 'your-username/soulfra-simple')

        if not self.github_token:
            raise ValueError("GITHUB_TOKEN_FOR_ISSUES environment variable not set")

        self.api_base = 'https://api.github.com'
        self.headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }

        # Domain-specific label mapping
        self.domain_labels = {
            'stpetepros': 'stpetepros',
            'cringeproof': 'cringeproof',
            'calriven': 'calriven',
            'soulfra': 'core',
        }

        # Keyword-based auto-labeling
        self.keyword_labels = {
            'feature': ['feature', 'add', 'new', 'create'],
            'bug': ['bug', 'fix', 'broken', 'error', 'issue'],
            'idea': ['idea', 'maybe', 'consider', 'thinking'],
            'urgent': ['urgent', 'asap', 'immediately', 'critical'],
            'deploy-now': ['deploy', 'push live', 'go live'],
        }

    def process_voice_memo(self, audio_path: str) -> Dict:
        """
        Process voice memo and extract structured ideas

        Args:
            audio_path: Path to audio file

        Returns:
            Dict with transcript, ideas, domain, etc.
        """
        print(f"🎤 Processing voice memo: {audio_path}")

        # Use existing voice_memo_dissector
        dissector = VoiceMemoDissector()

        # Transcribe audio
        transcript = dissector.transcribe_audio(audio_path)

        if not transcript:
            raise ValueError("Failed to transcribe audio")

        print(f"📝 Transcript ({len(transcript)} chars)")

        # Extract ideas using Ollama
        ideas = dissector.extract_ideas_from_transcript(transcript)

        print(f"🧠 Extracted {len(ideas.get('ideas', []))} ideas")

        # Detect domain from transcript
        domain = self._detect_domain(transcript)

        return {
            'transcript': transcript,
            'ideas': ideas,
            'domain': domain,
            'audio_file': Path(audio_path).name
        }

    def _detect_domain(self, text: str) -> str:
        """
        Detect which domain this voice memo is about

        Args:
            text: Transcript text

        Returns:
            Domain slug (e.g., 'stpetepros')
        """
        text_lower = text.lower()

        domain_keywords = {
            'stpetepros': ['stpetepros', 'st pete pros', 'professional', 'plumber', 'electrician'],
            'cringeproof': ['cringeproof', 'cringe proof', 'voice idea', 'storytelling'],
            'calriven': ['calriven', 'real estate', 'property', 'housing'],
            'soulfra': ['soulfra', 'auth', 'login', 'master'],
        }

        for domain, keywords in domain_keywords.items():
            if any(kw in text_lower for kw in keywords):
                return domain

        return 'soulfra'  # Default

    def _detect_labels(self, text: str) -> List[str]:
        """
        Detect labels based on keywords in transcript

        Args:
            text: Transcript text

        Returns:
            List of label names
        """
        text_lower = text.lower()
        labels = []

        for label, keywords in self.keyword_labels.items():
            if any(kw in text_lower for kw in keywords):
                labels.append(label)

        return labels

    def create_github_issue(self, voice_data: Dict, custom_labels: List[str] = None, dry_run: bool = False) -> Dict:
        """
        Create GitHub issue from voice memo data

        Args:
            voice_data: Processed voice memo data
            custom_labels: Optional custom labels
            dry_run: If True, don't actually create issue

        Returns:
            GitHub issue response
        """
        transcript = voice_data['transcript']
        ideas = voice_data.get('ideas', {})
        domain = voice_data.get('domain', 'soulfra')
        audio_file = voice_data.get('audio_file', 'unknown.m4a')

        # Extract title from first idea or first 50 chars of transcript
        if ideas.get('ideas') and len(ideas['ideas']) > 0:
            title = ideas['ideas'][0].get('title', transcript[:50])
        else:
            title = transcript[:50] + "..."

        # Auto-detect labels
        auto_labels = self._detect_labels(transcript)

        # Add domain label
        if domain in self.domain_labels:
            auto_labels.append(self.domain_labels[domain])

        # Merge with custom labels
        all_labels = list(set(auto_labels + (custom_labels or [])))

        # Format issue body
        body = self._format_issue_body(transcript, ideas, domain, audio_file)

        # Create issue payload
        payload = {
            'title': title,
            'body': body,
            'labels': all_labels
        }

        if dry_run:
            print("\n📋 DRY RUN - Would create issue:")
            print(f"   Title: {title}")
            print(f"   Labels: {', '.join(all_labels)}")
            print(f"\n{body[:200]}...")
            return payload

        # Create issue via GitHub API
        url = f"{self.api_base}/repos/{self.repo}/issues"

        print(f"\n✅ Creating GitHub issue...")
        print(f"   Title: {title}")
        print(f"   Labels: {', '.join(all_labels)}")

        response = requests.post(url, headers=self.headers, json=payload)

        if response.status_code == 201:
            issue = response.json()
            print(f"\n🎉 Issue created: {issue['html_url']}")
            print(f"   Issue #{issue['number']}: {issue['title']}")
            return issue
        else:
            print(f"\n❌ Failed to create issue")
            print(f"   Status: {response.status_code}")
            print(f"   Error: {response.text}")
            raise Exception(f"GitHub API error: {response.status_code}")

    def _format_issue_body(self, transcript: str, ideas: Dict, domain: str, audio_file: str) -> str:
        """
        Format GitHub issue body in markdown

        Args:
            transcript: Voice transcript
            ideas: Extracted ideas
            domain: Domain slug
            audio_file: Audio filename

        Returns:
            Formatted markdown
        """
        body = f"""## Voice Memo Details

**Source:** Voice Memo - {audio_file}
**Domain:** {domain}
**Transcript Length:** {len(transcript)} characters

---

## Transcript

{transcript}

---

## Extracted Ideas

"""

        # Add extracted ideas
        if ideas.get('ideas'):
            for idx, idea in enumerate(ideas['ideas'], 1):
                body += f"\n### Idea {idx}: {idea.get('title', 'Untitled')}\n\n"
                body += f"{idea.get('description', '')}\n\n"

                if idea.get('action_items'):
                    body += "**Action Items:**\n"
                    for item in idea['action_items']:
                        body += f"- [ ] {item}\n"
                    body += "\n"
        else:
            body += "*No structured ideas extracted. See transcript above.*\n\n"

        # Add footer
        body += "\n---\n\n"
        body += "🎤 *Generated from voice memo by [Soulfra Voice Workflow](https://github.com/your-username/soulfra-simple)*\n"

        return body


def main():
    """
    CLI entry point
    """
    parser = argparse.ArgumentParser(description='Convert voice memo to GitHub issue')
    parser.add_argument('audio_file', help='Path to audio file (m4a, mp3, wav)')
    parser.add_argument('--labels', help='Comma-separated custom labels', default='')
    parser.add_argument('--dry-run', action='store_true', help='Preview without creating issue')
    parser.add_argument('--token', help='GitHub personal access token')
    parser.add_argument('--repo', help='Repository name (username/repo)')

    args = parser.parse_args()

    # Parse custom labels
    custom_labels = [l.strip() for l in args.labels.split(',') if l.strip()]

    try:
        # Initialize converter
        converter = VoiceToGitHub(github_token=args.token, repo=args.repo)

        # Process voice memo
        voice_data = converter.process_voice_memo(args.audio_file)

        # Create GitHub issue
        converter.create_github_issue(voice_data, custom_labels=custom_labels, dry_run=args.dry_run)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
