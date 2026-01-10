#!/usr/bin/env python3
"""
Ollama Documentation Q&A

Ask questions about Soulfra documentation using Ollama AI.
Searches docs for relevant content and provides AI-powered answers.

Usage:
    python3 ollama_docs_qa.py "How do I test QR login?"
    python3 ollama_docs_qa.py --interactive
    python3 ollama_docs_qa.py --model llama3.2 "What is Magic Publish?"
"""

import re
import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Optional
import urllib.request
import urllib.error
import argparse


class DocsQA:
    """Q&A system for documentation using Ollama"""

    def __init__(self, docs_dir: str = ".", ollama_url: str = "http://localhost:11434", model: str = "llama3.2"):
        self.docs_dir = Path(docs_dir)
        self.ollama_url = ollama_url
        self.model = model
        self.docs_content: Dict[str, str] = {}

    def load_docs(self) -> int:
        """
        Load all markdown documentation into memory
        Returns number of docs loaded
        """
        count = 0

        for md_file in self.docs_dir.glob("*.md"):
            # Skip README (too generic)
            if md_file.name.lower() == 'readme.md':
                continue

            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.docs_content[md_file.name] = content
                    count += 1
            except Exception as e:
                print(f"Error loading {md_file.name}: {e}", file=sys.stderr)

        return count

    def search_docs(self, query: str, max_results: int = 3) -> List[Dict[str, str]]:
        """
        Search documentation for relevant content
        Returns list of matching docs with context
        """
        results = []
        query_lower = query.lower()

        for filename, content in self.docs_content.items():
            lines = content.split('\n')
            matches = []

            # Search for query in content
            for i, line in enumerate(lines):
                if query_lower in line.lower():
                    # Get context (5 lines before and after)
                    context_start = max(0, i - 5)
                    context_end = min(len(lines), i + 6)
                    context = '\n'.join(lines[context_start:context_end])

                    matches.append({
                        'line_number': i + 1,
                        'context': context
                    })

            if matches:
                # Build context from all matches (limit to avoid too much text)
                combined_context = "\n\n".join([m['context'] for m in matches[:3]])

                results.append({
                    'filename': filename,
                    'match_count': len(matches),
                    'context': combined_context
                })

        # Sort by match count (most relevant first)
        results.sort(key=lambda x: x['match_count'], reverse=True)

        return results[:max_results]

    def check_ollama(self) -> bool:
        """
        Check if Ollama is running and accessible
        """
        try:
            url = f"{self.ollama_url}/api/tags"
            req = urllib.request.Request(url)

            with urllib.request.urlopen(req, timeout=2) as response:
                data = json.loads(response.read().decode('utf-8'))
                # Check if our model is available
                models = [m['name'] for m in data.get('models', [])]
                return any(self.model in m for m in models)

        except Exception:
            return False

    def ask_ollama(self, question: str, context: str = "") -> Optional[str]:
        """
        Ask Ollama a question with documentation context
        Returns answer or None if error
        """
        try:
            url = f"{self.ollama_url}/api/generate"

            # Build prompt with context
            prompt = f"""You are a helpful documentation assistant for the Soulfra project.

The Soulfra project is a multi-domain Flask application with:
- QR code authentication
- Ollama AI integration
- GitHub Pages static site generation
- Multi-tenant brand theming
- Content creation studio
- Automation workflows

Documentation context:
{context}

User question: {question}

Provide a concise, helpful answer based on the documentation context. Include specific examples or code snippets if relevant."""

            data = {
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }

            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )

            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get('response', '')

        except urllib.error.URLError as e:
            print(f"❌ Error connecting to Ollama: {e}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            return None

    def answer_question(self, question: str, verbose: bool = False) -> Optional[str]:
        """
        Answer a question using search + Ollama
        Returns answer or None
        """
        # Search for relevant docs
        if verbose:
            print(f"🔍 Searching documentation for: '{question}'...")

        search_results = self.search_docs(question)

        if not search_results:
            print("⚠️  No relevant documentation found.")
            return None

        if verbose:
            print(f"📚 Found {len(search_results)} relevant documents:")
            for result in search_results:
                print(f"   • {result['filename']} ({result['match_count']} matches)")
            print()

        # Build context from search results
        context = ""
        for result in search_results:
            context += f"\n\n--- From {result['filename']} ---\n"
            context += result['context']

        # Ask Ollama
        if verbose:
            print(f"🤖 Asking Ollama ({self.model})...\n")

        answer = self.ask_ollama(question, context)

        if answer and verbose:
            print(f"\n📖 Sources:")
            for result in search_results:
                print(f"   • {result['filename']}")

        return answer

    def interactive_mode(self):
        """
        Interactive Q&A session
        """
        print("\n" + "="*60)
        print("🤖 SOULFRA DOCUMENTATION Q&A (Interactive Mode)")
        print("="*60)
        print(f"Model: {self.model}")
        print(f"Docs loaded: {len(self.docs_content)}")
        print("\nType your questions (or 'quit' to exit)")
        print("="*60 + "\n")

        while True:
            try:
                question = input("❓ Question: ").strip()

                if not question:
                    continue

                if question.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Goodbye!")
                    break

                print()
                answer = self.answer_question(question, verbose=True)

                if answer:
                    print(f"\n💡 Answer:\n{answer}\n")
                    print("-"*60 + "\n")
                else:
                    print("❌ Could not generate an answer.\n")

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}\n", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="Ask questions about Soulfra documentation using Ollama",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "How do I test QR login?"
  %(prog)s --interactive
  %(prog)s --model llama3.2 "What ports do the Flask apps use?"
  %(prog)s --docs-dir /path/to/docs "How does Magic Publish work?"
        """
    )

    parser.add_argument(
        'question',
        type=str,
        nargs='?',
        help='Question to ask about the documentation'
    )

    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Start interactive Q&A session'
    )

    parser.add_argument(
        '--model', '-m',
        type=str,
        default='llama3.2',
        help='Ollama model to use (default: llama3.2)'
    )

    parser.add_argument(
        '--ollama-url',
        type=str,
        default='http://localhost:11434',
        help='Ollama server URL (default: http://localhost:11434)'
    )

    parser.add_argument(
        '--docs-dir',
        type=str,
        default='.',
        help='Directory containing markdown docs (default: current directory)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed information'
    )

    args = parser.parse_args()

    # Must provide either question or --interactive
    if not args.question and not args.interactive:
        parser.print_help()
        sys.exit(1)

    # Create Q&A system
    qa = DocsQA(
        docs_dir=args.docs_dir,
        ollama_url=args.ollama_url,
        model=args.model
    )

    # Load documentation
    if args.verbose:
        print(f"📖 Loading documentation from {qa.docs_dir}...")

    doc_count = qa.load_docs()

    if doc_count == 0:
        print("❌ No documentation files found!", file=sys.stderr)
        sys.exit(1)

    if args.verbose:
        print(f"✅ Loaded {doc_count} documentation files\n")

    # Check Ollama availability
    if args.verbose:
        print(f"🔌 Checking Ollama at {qa.ollama_url}...")

    if not qa.check_ollama():
        print(f"❌ Ollama not available at {qa.ollama_url}", file=sys.stderr)
        print(f"   Make sure Ollama is running: ollama serve", file=sys.stderr)
        print(f"   And model is pulled: ollama pull {args.model}", file=sys.stderr)
        sys.exit(1)

    if args.verbose:
        print(f"✅ Ollama is running with model: {args.model}\n")

    # Interactive or single question mode
    if args.interactive:
        qa.interactive_mode()
    else:
        answer = qa.answer_question(args.question, verbose=args.verbose)

        if answer:
            if not args.verbose:
                # In non-verbose mode, just print the answer
                print(answer)
        else:
            sys.exit(1)


if __name__ == '__main__':
    main()
