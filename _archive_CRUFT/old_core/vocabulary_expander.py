#!/usr/bin/env python3
"""
Vocabulary Expander - Controlled Knowledge Fetching

Start with YOUR words, expand contextually when needed.

Strategy:
1. Base vocabulary: Your 263 StPetePros words
2. Expand on-demand: Fetch definitions only when encountering unknown context
3. Sources: Wikipedia, Python dictionary, WordNet, news APIs
4. Store expansions: Build local knowledge graph

This is like:
- Just-in-time compilation (fetch knowledge when needed, not all upfront)
- Lazy loading (only expand vocabulary if required)
- Controlled hallucination (LLM can only use known + fetched words)
"""

import json
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import urllib.request
import urllib.parse
from database import get_db


class VocabularyExpander:
    """
    Expand vocabulary contextually from external sources

    Keeps track of:
    - Base vocabulary (your 263 words)
    - Expanded vocabulary (fetched definitions)
    - Source metadata (where each word came from)
    - Usage frequency (which expansions are most useful)
    """

    def __init__(self, base_vocab_path: str = 'stpetepros-wordlist.txt'):
        """
        Initialize expander with base vocabulary

        Args:
            base_vocab_path: Path to your core wordlist
        """
        self.base_vocab = self._load_base_vocab(base_vocab_path)
        self.expanded_vocab = {}  # {word: {definition, source, fetched_at, usage_count}}
        self.expansion_history = []

        print(f"🌱 Initialized Vocabulary Expander")
        print(f"   Base vocabulary: {len(self.base_vocab)} words")


    def _load_base_vocab(self, filepath: str) -> set:
        """Load base vocabulary from wordlist file"""
        words = set()

        if not Path(filepath).exists():
            print(f"⚠️ Base vocab not found: {filepath}")
            return words

        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip().lower()

                # Skip comments and empty lines
                if line.startswith('#') or not line:
                    continue

                words.add(line)

        return words


    def is_in_vocab(self, word: str) -> bool:
        """Check if word is in base or expanded vocabulary"""
        word = word.lower()
        return word in self.base_vocab or word in self.expanded_vocab


    def fetch_wikipedia_definition(self, word: str, timeout: int = 5) -> Optional[Dict]:
        """
        Fetch word definition from Wikipedia API

        Uses Wikipedia's REST API (no auth required)

        Args:
            word: Word to look up
            timeout: Request timeout in seconds

        Returns:
            Dict with definition data or None
        """
        try:
            # Wikipedia API endpoint
            base_url = "https://en.wikipedia.org/api/rest_v1/page/summary/"
            url = base_url + urllib.parse.quote(word)

            # Fetch page summary
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'SoulfraPlatform/1.0 (Educational Project)')

            with urllib.request.urlopen(req, timeout=timeout) as response:
                data = json.loads(response.read().decode('utf-8'))

                # Extract key info
                definition = {
                    'word': word,
                    'title': data.get('title', word),
                    'definition': data.get('extract', ''),
                    'description': data.get('description', ''),
                    'url': data.get('content_urls', {}).get('desktop', {}).get('page', ''),
                    'source': 'wikipedia',
                    'fetched_at': datetime.now().isoformat()
                }

                print(f"📖 Fetched Wikipedia: {word}")
                return definition

        except Exception as e:
            print(f"⚠️ Wikipedia fetch failed for '{word}': {e}")
            return None


    def fetch_python_dictionary(self, word: str) -> Optional[Dict]:
        """
        Use Python's built-in words/definitions (fallback)

        For common English words, provides basic definitions

        Args:
            word: Word to define

        Returns:
            Dict with definition or None
        """
        # This is a simple fallback - you could integrate WordNet or other
        # dictionary APIs here (like Merriam-Webster, Oxford, etc.)

        # For now, just provide word metadata
        definition = {
            'word': word,
            'title': word.capitalize(),
            'definition': f"A word related to: {word}",
            'description': 'English word',
            'source': 'builtin',
            'fetched_at': datetime.now().isoformat()
        }

        return definition


    def fetch_news_context(self, word: str, timeout: int = 5) -> Optional[Dict]:
        """
        Fetch recent news mentions (optional - requires API key)

        You could integrate:
        - NewsAPI.org (free tier: 100 requests/day)
        - Google News RSS
        - Reddit API

        Args:
            word: Word to search for
            timeout: Request timeout

        Returns:
            Dict with news context or None
        """
        # TODO: Implement news API integration
        # For now, return placeholder
        print(f"📰 News context not yet implemented for '{word}'")
        return None


    def expand_word(self, word: str, sources: List[str] = ['wikipedia', 'builtin']) -> Optional[Dict]:
        """
        Expand vocabulary by fetching word definition

        Args:
            word: Word to expand
            sources: Which sources to try (in order)

        Returns:
            Definition dict or None
        """
        word = word.lower()

        # Check if already in base vocab
        if word in self.base_vocab:
            print(f"✓ '{word}' already in base vocabulary")
            return None

        # Check if already expanded
        if word in self.expanded_vocab:
            self.expanded_vocab[word]['usage_count'] += 1
            print(f"✓ '{word}' already expanded (usage: {self.expanded_vocab[word]['usage_count']})")
            return self.expanded_vocab[word]

        # Try each source in order
        definition = None

        for source in sources:
            if source == 'wikipedia':
                definition = self.fetch_wikipedia_definition(word)
            elif source == 'builtin':
                definition = self.fetch_python_dictionary(word)
            elif source == 'news':
                definition = self.fetch_news_context(word)

            if definition:
                break

        if definition:
            # Add usage tracking
            definition['usage_count'] = 1
            definition['expansion_source'] = source

            # Store in expanded vocab
            self.expanded_vocab[word] = definition

            # Track expansion event
            self.expansion_history.append({
                'word': word,
                'source': source,
                'timestamp': datetime.now().isoformat()
            })

            print(f"✅ Expanded vocabulary: {word} (from {source})")

            return definition

        print(f"❌ Could not expand '{word}' from any source")
        return None


    def batch_expand(self, words: List[str], sources: List[str] = ['wikipedia', 'builtin']) -> Dict[str, Optional[Dict]]:
        """
        Expand multiple words at once

        Args:
            words: List of words to expand
            sources: Which sources to try

        Returns:
            Dict mapping word → definition (or None if failed)
        """
        results = {}

        print(f"\n🔍 Batch expanding {len(words)} words...")

        for word in words:
            results[word] = self.expand_word(word, sources=sources)

        successful = sum(1 for v in results.values() if v is not None)
        print(f"\n✅ Successfully expanded {successful}/{len(words)} words")

        return results


    def get_related_words(self, word: str, max_results: int = 5) -> List[str]:
        """
        Find related words from expanded definitions

        Uses simple keyword matching in definitions

        Args:
            word: Source word
            max_results: Max related words to return

        Returns:
            List of related words
        """
        word = word.lower()

        # Get definition
        definition = self.expanded_vocab.get(word)
        if not definition:
            return []

        # Extract keywords from definition
        text = definition.get('definition', '') + ' ' + definition.get('description', '')
        text = text.lower()

        # Find words from vocab that appear in definition
        related = []

        for vocab_word in list(self.base_vocab) + list(self.expanded_vocab.keys()):
            if vocab_word == word:
                continue

            if vocab_word in text:
                related.append(vocab_word)

        return related[:max_results]


    def get_expansion_stats(self) -> Dict:
        """Get statistics about vocabulary expansion"""
        return {
            'base_vocab_size': len(self.base_vocab),
            'expanded_vocab_size': len(self.expanded_vocab),
            'total_vocab_size': len(self.base_vocab) + len(self.expanded_vocab),
            'total_expansions': len(self.expansion_history),
            'sources_used': list(set(e['source'] for e in self.expansion_history)),
            'most_used_expansions': sorted(
                [(word, data['usage_count']) for word, data in self.expanded_vocab.items()],
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }


    def save_expanded_vocab(self, filepath: str = 'data/expanded_vocabulary.json'):
        """Save expanded vocabulary to disk"""
        data = {
            'base_vocab': list(self.base_vocab),
            'expanded_vocab': self.expanded_vocab,
            'expansion_history': self.expansion_history,
            'stats': self.get_expansion_stats(),
            'saved_at': datetime.now().isoformat()
        }

        Path(filepath).parent.mkdir(exist_ok=True)

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"💾 Saved expanded vocabulary to {filepath}")


    @classmethod
    def load_expanded_vocab(cls, filepath: str = 'data/expanded_vocabulary.json') -> 'VocabularyExpander':
        """Load previously expanded vocabulary from disk"""
        with open(filepath, 'r') as f:
            data = json.load(f)

        # Create instance
        expander = cls()

        # Restore data
        expander.base_vocab = set(data['base_vocab'])
        expander.expanded_vocab = data['expanded_vocab']
        expander.expansion_history = data['expansion_history']

        print(f"📂 Loaded expanded vocabulary from {filepath}")
        print(f"   Saved: {data['saved_at']}")
        print(f"   Total vocab: {data['stats']['total_vocab_size']} words")

        return expander


    def build_knowledge_graph(self) -> Dict:
        """
        Build knowledge graph from expanded vocabulary

        Creates graph structure:
        - Nodes: Words (base + expanded)
        - Edges: Relationships (appears in definition, related concepts)

        Returns:
            Graph dict {nodes: [...], edges: [...]}
        """
        nodes = []
        edges = []

        # Add base vocab nodes
        for word in self.base_vocab:
            nodes.append({
                'id': word,
                'label': word,
                'type': 'base',
                'group': 'base_vocab'
            })

        # Add expanded vocab nodes
        for word, data in self.expanded_vocab.items():
            nodes.append({
                'id': word,
                'label': word,
                'type': 'expanded',
                'group': data['source'],
                'definition': data.get('definition', '')[:200],  # Truncate
                'usage_count': data.get('usage_count', 0)
            })

            # Create edges to related words
            related = self.get_related_words(word, max_results=5)
            for related_word in related:
                edges.append({
                    'source': word,
                    'target': related_word,
                    'type': 'related'
                })

        print(f"🕸️ Built knowledge graph")
        print(f"   Nodes: {len(nodes)}")
        print(f"   Edges: {len(edges)}")

        return {
            'nodes': nodes,
            'edges': edges,
            'stats': self.get_expansion_stats()
        }


# =============================================================================
# CLI for Testing
# =============================================================================

if __name__ == '__main__':
    import sys

    # Initialize expander
    expander = VocabularyExpander('stpetepros-wordlist.txt')

    # Test words to expand
    test_words = [
        'database',  # Technical term
        'cryptocurrency',  # Fintech term
        'plumbing',  # Already in base vocab
        'blockchain',  # Tech buzzword
        'tampa'  # Geographic
    ]

    print(f"\n🧪 Testing vocabulary expansion...")

    # Expand words
    results = expander.batch_expand(test_words, sources=['wikipedia', 'builtin'])

    # Show results
    print(f"\n📊 Expansion Results:")
    for word, definition in results.items():
        if definition:
            print(f"\n✅ {word}:")
            print(f"   Definition: {definition['definition'][:100]}...")
            print(f"   Source: {definition['source']}")

            # Show related words
            related = expander.get_related_words(word)
            if related:
                print(f"   Related: {', '.join(related)}")
        else:
            print(f"\n❌ {word}: (already in base vocab or failed)")

    # Show stats
    stats = expander.get_expansion_stats()
    print(f"\n📈 Vocabulary Stats:")
    print(f"   Base: {stats['base_vocab_size']} words")
    print(f"   Expanded: {stats['expanded_vocab_size']} words")
    print(f"   Total: {stats['total_vocab_size']} words")

    # Build knowledge graph
    graph = expander.build_knowledge_graph()
    print(f"\n🕸️ Knowledge Graph:")
    print(f"   Nodes: {len(graph['nodes'])}")
    print(f"   Edges: {len(graph['edges'])}")

    # Save
    expander.save_expanded_vocab('data/expanded_vocabulary.json')

    print(f"\n✅ Done!")
