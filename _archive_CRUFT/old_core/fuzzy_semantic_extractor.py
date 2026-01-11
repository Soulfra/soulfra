#!/usr/bin/env python3
"""
Fuzzy Semantic Extractor - Extract Word Relationships Beyond Co-occurrence

Extracts semantic relationships using multiple methods:
1. Ollama (local LLM) - Query for is-a, has-a, used-for relationships
2. WordNet (NLTK) - Linguistic database for hypernyms, synonyms, etc.
3. Wikipedia (fallback) - Contextual definitions

Used by voice_to_graph_demo.ipynb and content_parser.py to add
semantic depth to wordmaps.
"""

import json
import requests
from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict
import re


class FuzzySemanticExtractor:
    """
    Extract semantic relationships between words

    Methods:
    - Ollama: Query local LLM for relationships
    - WordNet: Use linguistic database (requires NLTK)
    - Wikipedia: Extract from definitions
    - Builtin: Hardcoded common relationships (fallback)
    """

    def __init__(self,
                 ollama_url: str = 'http://localhost:11434',
                 use_wordnet: bool = True,
                 use_wikipedia: bool = True,
                 cache_relationships: bool = True):
        """
        Initialize semantic extractor

        Args:
            ollama_url: URL for Ollama API
            use_wordnet: Whether to use NLTK WordNet
            use_wikipedia: Whether to use Wikipedia API
            cache_relationships: Cache extracted relationships
        """
        self.ollama_url = ollama_url
        self.use_wordnet = use_wordnet
        self.use_wikipedia = use_wikipedia
        self.cache_relationships = cache_relationships

        # Relationship cache
        self.relationship_cache: Dict[str, Dict] = {}

        # Check if WordNet available
        self.wordnet_available = False
        if use_wordnet:
            try:
                import nltk
                from nltk.corpus import wordnet
                self.wordnet = wordnet
                self.wordnet_available = True
                print("✅ WordNet available")
            except ImportError:
                print("⚠️ WordNet not available (install nltk and run nltk.download('wordnet'))")

        # Check if Ollama available
        self.ollama_available = False
        try:
            response = requests.get(f"{ollama_url}/api/tags", timeout=2)
            if response.status_code == 200:
                self.ollama_available = True
                print("✅ Ollama available")
        except:
            print("⚠️ Ollama not available (run 'ollama serve')")


    def extract_relationships(self,
                             word: str,
                             context_words: Optional[List[str]] = None,
                             methods: List[str] = ['ollama', 'wordnet', 'wikipedia', 'builtin']) -> Dict:
        """
        Extract all semantic relationships for a word

        Args:
            word: Target word
            context_words: Optional context from transcript (helps disambiguation)
            methods: Which extraction methods to use

        Returns:
            Dict with relationship types and related words:
            {
                'is_a': ['bird', 'animal'],
                'part_of': ['flock'],
                'has_attribute': ['green', 'yellow', 'small'],
                'used_for': ['pet', 'companion'],
                'related_to': ['budgie', 'cage', 'seed'],
                'synonyms': ['budgerigar', 'budgie'],
                'hypernyms': ['bird', 'animal'],
                'hyponyms': ['green_parakeet'],
            }
        """
        # Check cache
        if self.cache_relationships and word in self.relationship_cache:
            return self.relationship_cache[word]

        relationships = defaultdict(list)

        # Try each method
        for method in methods:
            if method == 'ollama' and self.ollama_available:
                try:
                    ollama_rels = self._extract_ollama(word, context_words)
                    self._merge_relationships(relationships, ollama_rels)
                except Exception as e:
                    print(f"⚠️ Ollama extraction failed for '{word}': {e}")

            elif method == 'wordnet' and self.wordnet_available:
                try:
                    wordnet_rels = self._extract_wordnet(word)
                    self._merge_relationships(relationships, wordnet_rels)
                except Exception as e:
                    print(f"⚠️ WordNet extraction failed for '{word}': {e}")

            elif method == 'wikipedia' and self.use_wikipedia:
                try:
                    wiki_rels = self._extract_wikipedia(word)
                    self._merge_relationships(relationships, wiki_rels)
                except Exception as e:
                    print(f"⚠️ Wikipedia extraction failed for '{word}': {e}")

            elif method == 'builtin':
                builtin_rels = self._extract_builtin(word)
                self._merge_relationships(relationships, builtin_rels)

        # Convert defaultdict to regular dict
        result = {k: list(set(v)) for k, v in relationships.items() if v}

        # Cache result
        if self.cache_relationships:
            self.relationship_cache[word] = result

        return result


    def _extract_ollama(self, word: str, context_words: Optional[List[str]] = None) -> Dict:
        """
        Extract relationships using Ollama local LLM

        Prompt Ollama to identify:
        - is_a (hypernyms): what category does this belong to?
        - has_attribute (properties): what describes this?
        - used_for (purpose): what is this used for?
        - related_to (associations): what is related?
        """
        context_hint = ""
        if context_words:
            context_hint = f"\n\nContext words: {', '.join(context_words[:10])}"

        prompt = f"""Extract semantic relationships for the word: {word}{context_hint}

Return ONLY a JSON object with these keys (leave empty arrays if no relationships):
{{
  "is_a": ["category1", "category2"],
  "has_attribute": ["property1", "property2"],
  "used_for": ["purpose1", "purpose2"],
  "related_to": ["related1", "related2"]
}}

Example for "parakeet":
{{
  "is_a": ["bird", "animal", "pet"],
  "has_attribute": ["small", "colorful", "intelligent"],
  "used_for": ["companionship", "entertainment"],
  "related_to": ["cage", "seed", "budgie"]
}}

Now extract for: {word}"""

        response = requests.post(
            f"{self.ollama_url}/api/generate",
            json={
                'model': 'llama2',  # or whatever model is available
                'prompt': prompt,
                'stream': False,
                'options': {
                    'temperature': 0.3,  # Low temperature for consistent extraction
                    'num_predict': 200
                }
            },
            timeout=10
        )

        if response.status_code != 200:
            return {}

        result = response.json()
        response_text = result.get('response', '')

        # Extract JSON from response
        try:
            # Find JSON object in response
            json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
            if json_match:
                relationships = json.loads(json_match.group(0))
                return relationships
        except json.JSONDecodeError:
            pass

        return {}


    def _extract_wordnet(self, word: str) -> Dict:
        """
        Extract relationships using NLTK WordNet

        WordNet provides:
        - Synsets (synonym sets)
        - Hypernyms (is-a: dog → animal)
        - Hyponyms (subtypes: animal → dog)
        - Meronyms (part-of: car → wheel)
        - Holonyms (has-part: wheel → car)
        """
        if not self.wordnet_available:
            return {}

        relationships = defaultdict(list)

        # Get all synsets for word
        synsets = self.wordnet.synsets(word)

        if not synsets:
            return {}

        # Use first synset (most common meaning)
        synset = synsets[0]

        # Synonyms (from synset lemmas)
        for lemma in synset.lemmas():
            synonym = lemma.name().replace('_', ' ')
            if synonym.lower() != word.lower():
                relationships['synonyms'].append(synonym)

        # Hypernyms (is-a relationships)
        for hypernym in synset.hypernyms():
            for lemma in hypernym.lemmas():
                relationships['is_a'].append(lemma.name().replace('_', ' '))

        # Hyponyms (subtype relationships)
        for hyponym in synset.hyponyms():
            for lemma in hyponym.lemmas():
                relationships['hyponyms'].append(lemma.name().replace('_', ' '))

        # Meronyms (part-of relationships)
        for meronym in synset.part_meronyms():
            for lemma in meronym.lemmas():
                relationships['part_of'].append(lemma.name().replace('_', ' '))

        # Holonyms (has-part relationships)
        for holonym in synset.part_holonyms():
            for lemma in holonym.lemmas():
                relationships['has_part'].append(lemma.name().replace('_', ' '))

        # Definition parsing (extract key terms)
        definition = synset.definition()
        # Extract capitalized words and noun phrases as related concepts
        related_terms = re.findall(r'\b[A-Z][a-z]+\b', definition)
        relationships['related_to'].extend(related_terms)

        return dict(relationships)


    def _extract_wikipedia(self, word: str) -> Dict:
        """
        Extract relationships from Wikipedia definition

        Parse Wikipedia summary to find:
        - "X is a Y" → is_a relationship
        - "X has Y" → has_attribute
        - "used for Y" → used_for
        """
        relationships = defaultdict(list)

        try:
            # Fetch Wikipedia summary
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{word}"
            response = requests.get(url, timeout=5)

            if response.status_code != 200:
                return {}

            data = response.json()
            extract = data.get('extract', '')

            if not extract:
                return {}

            # Parse "X is a Y" patterns
            is_a_patterns = [
                rf'{word} is an? ([^,.]+)',
                rf'{word} refers to an? ([^,.]+)',
                r'is an? ([^,.]+)',
            ]

            for pattern in is_a_patterns:
                matches = re.findall(pattern, extract, re.IGNORECASE)
                for match in matches:
                    # Clean up and add
                    category = match.strip().lower()
                    # Extract first 1-3 words
                    category_words = category.split()[:3]
                    if category_words:
                        relationships['is_a'].append(' '.join(category_words))

            # Parse "has X" or "with X" patterns
            has_patterns = [
                r'has ([a-z]+ [a-z]+)',
                r'with ([a-z]+ [a-z]+)',
            ]

            for pattern in has_patterns:
                matches = re.findall(pattern, extract, re.IGNORECASE)
                for match in matches:
                    relationships['has_attribute'].append(match.strip().lower())

            # Parse "used for X" patterns
            used_patterns = [
                r'used for ([^,.]+)',
                r'used to ([^,.]+)',
            ]

            for pattern in used_patterns:
                matches = re.findall(pattern, extract, re.IGNORECASE)
                for match in matches:
                    relationships['used_for'].append(match.strip().lower())

        except Exception as e:
            print(f"⚠️ Wikipedia parsing error: {e}")

        return dict(relationships)


    def _extract_builtin(self, word: str) -> Dict:
        """
        Builtin hardcoded relationships for common words

        Fallback when other methods fail
        """
        # Common relationships for demo words
        builtin_relationships = {
            'parakeet': {
                'is_a': ['bird', 'animal', 'pet'],
                'has_attribute': ['small', 'colorful', 'intelligent', 'green', 'yellow'],
                'used_for': ['companionship', 'entertainment'],
                'related_to': ['budgie', 'cage', 'seed', 'australia'],
                'synonyms': ['budgerigar', 'budgie']
            },
            'bird': {
                'is_a': ['animal', 'vertebrate'],
                'has_attribute': ['feather', 'wings', 'beak'],
                'related_to': ['fly', 'nest', 'egg']
            },
            'pet': {
                'is_a': ['animal', 'companion'],
                'related_to': ['dog', 'cat', 'bird', 'care']
            },
            'intelligent': {
                'is_a': ['quality', 'trait'],
                'synonyms': ['smart', 'clever', 'bright'],
                'related_to': ['brain', 'learning', 'problem-solving']
            },
            'green': {
                'is_a': ['color'],
                'related_to': ['nature', 'plant', 'grass']
            },
            'australia': {
                'is_a': ['country', 'continent'],
                'related_to': ['sydney', 'kangaroo', 'outback']
            },
            # Tampa Bay words
            'tampa': {
                'is_a': ['city', 'location'],
                'related_to': ['florida', 'clearwater', 'st-petersburg', 'bay']
            },
            'plumber': {
                'is_a': ['professional', 'tradesperson'],
                'related_to': ['pipe', 'water', 'repair', 'service'],
                'used_for': ['fixing-leaks', 'installation']
            },
            'electrician': {
                'is_a': ['professional', 'tradesperson'],
                'related_to': ['electrical', 'wiring', 'repair', 'service'],
                'used_for': ['electrical-work', 'installation']
            },
        }

        return builtin_relationships.get(word.lower(), {})


    def _merge_relationships(self, target: Dict, source: Dict) -> None:
        """
        Merge source relationships into target (in-place)

        Deduplicates and combines relationship lists
        """
        for rel_type, related_words in source.items():
            if isinstance(related_words, list):
                target[rel_type].extend(related_words)


    def create_semantic_edges(self,
                             word: str,
                             relationships: Dict) -> List[Dict]:
        """
        Convert relationships dict to graph edges

        Args:
            word: Source word
            relationships: Output from extract_relationships()

        Returns:
            List of edge dicts: [{'source': 'parakeet', 'target': 'bird', 'type': 'is_a', ...}]
        """
        edges = []

        for rel_type, related_words in relationships.items():
            for related_word in related_words:
                edges.append({
                    'source': word,
                    'target': related_word,
                    'type': rel_type,
                    'weight': 1,
                    'semantic': True
                })

        return edges


    def extract_graph_semantics(self,
                                nodes: List[Dict],
                                max_words: int = 20) -> Tuple[List[Dict], List[Dict]]:
        """
        Extract semantic relationships for all nodes in a graph

        Args:
            nodes: List of node dicts (must have 'id' field)
            max_words: Max words to extract semantics for (performance)

        Returns:
            (semantic_nodes, semantic_edges) tuple
        """
        semantic_nodes = []
        semantic_edges = []

        # Track which semantic nodes we've added
        added_semantic_nodes = set()

        # Sort nodes by frequency (if available) and take top N
        sorted_nodes = sorted(
            nodes,
            key=lambda n: n.get('frequency', 0),
            reverse=True
        )[:max_words]

        for node in sorted_nodes:
            word = node['id']

            # Extract relationships
            relationships = self.extract_relationships(word)

            if not relationships:
                continue

            # Create semantic edges
            edges = self.create_semantic_edges(word, relationships)
            semantic_edges.extend(edges)

            # Create semantic nodes (for related words not in original graph)
            for edge in edges:
                related_word = edge['target']

                # Check if this word is already in original nodes or semantic nodes
                if related_word in added_semantic_nodes:
                    continue

                if any(n['id'] == related_word for n in nodes):
                    continue

                # Add new semantic node
                semantic_nodes.append({
                    'id': related_word,
                    'label': related_word,
                    'type': 'semantic',
                    'frequency': 0,
                    'source': 'fuzzy_semantic'
                })
                added_semantic_nodes.add(related_word)

        return semantic_nodes, semantic_edges


# =================================================================
# CLI for Testing
# =================================================================

if __name__ == '__main__':
    print("🧪 Testing Fuzzy Semantic Extractor\n")

    extractor = FuzzySemanticExtractor()

    # Test 1: Extract relationships for "parakeet"
    print("Test 1: Extract relationships for 'parakeet'")
    print("=" * 60)

    relationships = extractor.extract_relationships('parakeet')

    for rel_type, related_words in relationships.items():
        print(f"\n{rel_type}:")
        for word in related_words[:5]:  # Show first 5
            print(f"  - {word}")

    # Test 2: Create semantic edges
    print("\n\nTest 2: Create semantic edges")
    print("=" * 60)

    edges = extractor.create_semantic_edges('parakeet', relationships)

    for edge in edges[:10]:  # Show first 10
        print(f"  {edge['source']} --[{edge['type']}]→ {edge['target']}")

    # Test 3: Extract for Tampa Bay words
    print("\n\nTest 3: Tampa Bay professional words")
    print("=" * 60)

    tampa_words = ['tampa', 'plumber', 'electrician']

    for word in tampa_words:
        rels = extractor.extract_relationships(word)
        print(f"\n{word}:")
        if 'is_a' in rels:
            print(f"  is_a: {', '.join(rels['is_a'][:3])}")
        if 'related_to' in rels:
            print(f"  related_to: {', '.join(rels['related_to'][:3])}")

    print("\n✅ All tests complete!")
    print(f"\n📊 Stats:")
    print(f"   Ollama available: {extractor.ollama_available}")
    print(f"   WordNet available: {extractor.wordnet_available}")
    print(f"   Cached relationships: {len(extractor.relationship_cache)}")
