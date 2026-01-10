#!/usr/bin/env python3
"""
Dev Assistant - AI-Powered Development Orchestrator

Routes requests intelligently:
1. Ollama (local, fast, unlimited) - for quick iterations
2. Claude API - for complex reasoning when stuck
3. OpenAI API - fallback for specific tasks

Usage:
    python3 dev-assistant.py "write a function to parse JSON"
    python3 dev-assistant.py --review-code app.py
    python3 dev-assistant.py --generate-template blog-post
"""

import sys
import json
import subprocess
import requests
from pathlib import Path
from typing import Optional, Dict, Any
import os
from datetime import datetime

# Configuration
OLLAMA_HOST = "http://localhost:11434"
OLLAMA_MODEL = "llama2"  # Change to your preferred model

CLAUDE_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Cost tracking
USAGE_LOG = Path("dev-assistant-usage.json")


class AIOrchestrator:
    """Intelligent routing between local Ollama and cloud APIs"""

    def __init__(self):
        self.usage = self._load_usage()

    def _load_usage(self) -> Dict:
        """Load usage statistics"""
        if USAGE_LOG.exists():
            return json.loads(USAGE_LOG.read_text())
        return {
            "ollama_requests": 0,
            "claude_requests": 0,
            "openai_requests": 0,
            "last_updated": str(datetime.now())
        }

    def _save_usage(self):
        """Save usage statistics"""
        self.usage["last_updated"] = str(datetime.now())
        USAGE_LOG.write_text(json.dumps(self.usage, indent=2))

    def query_ollama(self, prompt: str, model: str = OLLAMA_MODEL) -> Optional[str]:
        """Try Ollama first (local, fast, free)"""
        try:
            response = requests.post(
                f"{OLLAMA_HOST}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )

            if response.ok:
                result = response.json()
                self.usage["ollama_requests"] += 1
                self._save_usage()
                return result.get("response", "")

            return None

        except (requests.RequestException, Exception) as e:
            print(f"⚠️  Ollama unavailable: {e}")
            return None

    def query_claude(self, prompt: str) -> Optional[str]:
        """Fallback to Claude API for complex reasoning"""
        if not CLAUDE_API_KEY:
            print("⚠️  Claude API key not set (ANTHROPIC_API_KEY)")
            return None

        try:
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "anthropic-version": "2023-06-01",
                    "x-api-key": CLAUDE_API_KEY,
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-3-5-sonnet-20241022",
                    "max_tokens": 4096,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ]
                },
                timeout=60
            )

            if response.ok:
                result = response.json()
                self.usage["claude_requests"] += 1
                self._save_usage()
                return result["content"][0]["text"]

            print(f"⚠️  Claude API error: {response.status_code}")
            return None

        except Exception as e:
            print(f"⚠️  Claude API failed: {e}")
            return None

    def query_openai(self, prompt: str) -> Optional[str]:
        """Fallback to OpenAI API"""
        if not OPENAI_API_KEY:
            print("⚠️  OpenAI API key not set (OPENAI_API_KEY)")
            return None

        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ]
                },
                timeout=60
            )

            if response.ok:
                result = response.json()
                self.usage["openai_requests"] += 1
                self._save_usage()
                return result["choices"][0]["message"]["content"]

            print(f"⚠️  OpenAI API error: {response.status_code}")
            return None

        except Exception as e:
            print(f"⚠️  OpenAI API failed: {e}")
            return None

    def ask(self, prompt: str, prefer_local: bool = True) -> str:
        """
        Smart routing: Try Ollama first, fall back to APIs

        Args:
            prompt: The question/task
            prefer_local: If True, tries Ollama first

        Returns:
            AI response
        """
        print(f"💬 Query: {prompt[:80]}...")

        # Strategy 1: Try Ollama (local, fast)
        if prefer_local:
            print("🔄 Trying Ollama (local)...")
            response = self.query_ollama(prompt)
            if response:
                print("✅ Ollama responded")
                return response

        # Strategy 2: Try Claude (best reasoning)
        print("🔄 Trying Claude API...")
        response = self.query_claude(prompt)
        if response:
            print("✅ Claude responded")
            return response

        # Strategy 3: Try OpenAI (fallback)
        print("🔄 Trying OpenAI API...")
        response = self.query_openai(prompt)
        if response:
            print("✅ OpenAI responded")
            return response

        return "❌ All AI services unavailable"

    def show_usage(self):
        """Display usage statistics"""
        print("\n📊 AI Assistant Usage")
        print("=" * 50)
        print(f"Ollama (local):  {self.usage['ollama_requests']} requests")
        print(f"Claude API:      {self.usage['claude_requests']} requests")
        print(f"OpenAI API:      {self.usage['openai_requests']} requests")
        print(f"Last updated:    {self.usage['last_updated']}")
        print("=" * 50)


def main():
    """CLI interface"""
    if len(sys.argv) < 2:
        print("Usage: python3 dev-assistant.py <prompt>")
        print("       python3 dev-assistant.py --usage")
        sys.exit(1)

    orchestrator = AIOrchestrator()

    if sys.argv[1] == "--usage":
        orchestrator.show_usage()
        return

    prompt = " ".join(sys.argv[1:])
    response = orchestrator.ask(prompt)

    print("\n" + "=" * 80)
    print(response)
    print("=" * 80)


if __name__ == "__main__":
    main()
