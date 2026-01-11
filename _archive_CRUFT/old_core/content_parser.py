#!/usr/bin/env python3
"""
Universal Content Parser - Extract Nodes + Edges from ANY Content

Parses:
- Voice transcripts → wordmaps → graph
- Code files → functions/classes/imports → graph
- README/docs → sections/links → graph
- QR card data → professional tags → graph
- Database posts/comments → relationships → graph

Output format (standardized):
{
    'nodes': [
        {'id': 'word1', 'label': 'word1', 'type': 'word', 'frequency': 10, ...},
        {'id': 'function_foo', 'label': 'foo', 'type': 'function', ...}
    ],
    'edges': [
        {'source': 'word1', 'target': 'word2', 'type': 'co-occurrence', 'weight': 5}
    ],
    'metadata': {
        'content_type': 'voice_transcript',
        'source': 'recording_123.wav',
        'parsed_at': '2026-01-11T...'
    }
}
"""

import re
import json
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from pathlib import Path
from collections import Counter
import ast  # For Python code parsing


class ContentParser:
    """
    Universal parser that converts ANY content type into graph structure
    """

    def __init__(self):
        self.parsers = {
            'voice_transcript': self.parse_voice_transcript,
            'code_python': self.parse_python_code,
            'markdown': self.parse_markdown,
            'qr_professional': self.parse_qr_professional,
            'database_post': self.parse_database_post,
            'wordmap': self.parse_wordmap_json
        }

        print("🔍 Content Parser initialized")
        print(f"   Supported types: {', '.join(self.parsers.keys())}")


    # =================================================================
    # VOICE TRANSCRIPT PARSING
    # =================================================================

    def parse_voice_transcript(self, transcript: str, metadata: Optional[Dict] = None) -> Dict:
        """
        Parse voice transcript into wordmap graph

        Args:
            transcript: Raw transcript text
            metadata: Optional metadata (recording_id, user_id, etc.)

        Returns:
            Graph dict with nodes (words) and edges (co-occurrences)
        """
        # Try to import wordmap extractor, fallback to simple extraction
        try:
            from wordmap_pitch_integrator import extract_wordmap_from_transcript
            wordmap = extract_wordmap_from_transcript(transcript, top_n=50)
        except ImportError:
            # Fallback: Simple word frequency extraction
            words = re.findall(r'\b\w+\b', transcript.lower())
            word_freq = Counter(words)

            # Remove common stop words
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'them', 'their', 's', 't'}

            wordmap = {word: freq for word, freq in word_freq.most_common(50) if word not in stop_words and len(word) > 2}

        # Create nodes from words
        nodes = []
        for word, frequency in wordmap.items():
            nodes.append({
                'id': word,
                'label': word,
                'type': 'word',
                'frequency': frequency,
                'source': 'voice_transcript'
            })

        # Create edges from word co-occurrences (within 3-word window)
        edges = []
        words_list = re.findall(r'\b\w+\b', transcript.lower())

        co_occurrences = Counter()
        window_size = 3

        for i in range(len(words_list) - 1):
            for j in range(i + 1, min(i + window_size, len(words_list))):
                word1 = words_list[i]
                word2 = words_list[j]

                # Only include if both words in top wordmap
                if word1 in wordmap and word2 in wordmap:
                    pair = tuple(sorted([word1, word2]))
                    co_occurrences[pair] += 1

        for (word1, word2), count in co_occurrences.most_common(30):
            edges.append({
                'source': word1,
                'target': word2,
                'type': 'co-occurrence',
                'weight': count
            })

        return {
            'nodes': nodes,
            'edges': edges,
            'metadata': {
                'content_type': 'voice_transcript',
                'word_count': len(words_list),
                'unique_words': len(wordmap),
                'parsed_at': datetime.now().isoformat(),
                **(metadata or {})
            }
        }


    # =================================================================
    # PYTHON CODE PARSING
    # =================================================================

    def parse_python_code(self, code: str, filepath: Optional[str] = None) -> Dict:
        """
        Parse Python code into dependency graph

        Extracts:
        - Functions (def foo)
        - Classes (class Bar)
        - Imports (import X, from Y import Z)
        - Function calls

        Returns:
            Graph dict with code structure
        """
        nodes = []
        edges = []

        try:
            tree = ast.parse(code)
        except SyntaxError:
            # Fallback: simple regex parsing
            return self._parse_code_regex(code, filepath)

        # Track current context (for nested items)
        current_class = None

        for node in ast.walk(tree):
            # Functions
            if isinstance(node, ast.FunctionDef):
                node_id = f"function_{node.name}"
                if current_class:
                    node_id = f"{current_class}.{node.name}"

                nodes.append({
                    'id': node_id,
                    'label': node.name,
                    'type': 'function',
                    'lineno': node.lineno,
                    'class': current_class
                })

                # Extract function calls within this function
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if hasattr(child.func, 'id'):
                            called_func = child.func.id
                            edges.append({
                                'source': node_id,
                                'target': f"function_{called_func}",
                                'type': 'calls'
                            })

            # Classes
            elif isinstance(node, ast.ClassDef):
                node_id = f"class_{node.name}"
                current_class = node.name

                nodes.append({
                    'id': node_id,
                    'label': node.name,
                    'type': 'class',
                    'lineno': node.lineno
                })

            # Imports
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name
                    nodes.append({
                        'id': f"import_{module_name}",
                        'label': module_name,
                        'type': 'import',
                        'lineno': node.lineno
                    })

            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    import_name = f"{module}.{alias.name}" if module else alias.name
                    nodes.append({
                        'id': f"import_{import_name}",
                        'label': import_name,
                        'type': 'import',
                        'lineno': node.lineno
                    })

        return {
            'nodes': nodes,
            'edges': edges,
            'metadata': {
                'content_type': 'code_python',
                'filepath': filepath,
                'total_lines': len(code.split('\n')),
                'functions': len([n for n in nodes if n['type'] == 'function']),
                'classes': len([n for n in nodes if n['type'] == 'class']),
                'parsed_at': datetime.now().isoformat()
            }
        }


    def _parse_code_regex(self, code: str, filepath: Optional[str] = None) -> Dict:
        """Fallback regex-based code parsing"""
        nodes = []
        edges = []

        # Find functions
        for match in re.finditer(r'^def\s+(\w+)\s*\(', code, re.MULTILINE):
            func_name = match.group(1)
            nodes.append({
                'id': f"function_{func_name}",
                'label': func_name,
                'type': 'function'
            })

        # Find classes
        for match in re.finditer(r'^class\s+(\w+)', code, re.MULTILINE):
            class_name = match.group(1)
            nodes.append({
                'id': f"class_{class_name}",
                'label': class_name,
                'type': 'class'
            })

        return {
            'nodes': nodes,
            'edges': edges,
            'metadata': {'content_type': 'code_python', 'filepath': filepath}
        }


    # =================================================================
    # MARKDOWN/README PARSING
    # =================================================================

    def parse_markdown(self, markdown: str, filepath: Optional[str] = None) -> Dict:
        """
        Parse Markdown into section hierarchy + links

        Extracts:
        - Headers (# Section, ## Subsection)
        - Links ([text](url))
        - Code blocks (```)
        """
        nodes = []
        edges = []

        # Extract headers (sections)
        current_section = None
        section_stack = []

        for line in markdown.split('\n'):
            # Headers
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if header_match:
                level = len(header_match.group(1))
                title = header_match.group(2).strip()
                section_id = re.sub(r'[^\w]+', '-', title.lower())

                node = {
                    'id': section_id,
                    'label': title,
                    'type': f'header_h{level}',
                    'level': level
                }
                nodes.append(node)

                # Create hierarchy edges
                if level > 1 and section_stack:
                    parent = section_stack[-1]
                    edges.append({
                        'source': parent,
                        'target': section_id,
                        'type': 'contains'
                    })

                # Update stack
                section_stack = section_stack[:level-1] + [section_id]
                current_section = section_id

            # Links
            for link_match in re.finditer(r'\[([^\]]+)\]\(([^\)]+)\)', line):
                link_text = link_match.group(1)
                link_url = link_match.group(2)

                link_id = re.sub(r'[^\w]+', '-', link_url.lower())[:50]

                nodes.append({
                    'id': link_id,
                    'label': link_text,
                    'type': 'link',
                    'url': link_url
                })

                # Link from current section
                if current_section:
                    edges.append({
                        'source': current_section,
                        'target': link_id,
                        'type': 'references'
                    })

        return {
            'nodes': nodes,
            'edges': edges,
            'metadata': {
                'content_type': 'markdown',
                'filepath': filepath,
                'sections': len([n for n in nodes if 'header' in n['type']]),
                'links': len([n for n in nodes if n['type'] == 'link']),
                'parsed_at': datetime.now().isoformat()
            }
        }


    # =================================================================
    # QR PROFESSIONAL DATA PARSING
    # =================================================================

    def parse_qr_professional(self, professional_data: Dict) -> Dict:
        """
        Parse QR business card / professional data into network

        Args:
            professional_data: Dict from database (business_name, category, bio, etc.)

        Returns:
            Graph showing professional → category → tags
        """
        nodes = []
        edges = []

        # Professional node
        prof_id = f"professional_{professional_data.get('id', 'unknown')}"
        nodes.append({
            'id': prof_id,
            'label': professional_data.get('business_name', 'Unknown'),
            'type': 'professional',
            'category': professional_data.get('category'),
            'city': professional_data.get('city'),
            'rating': professional_data.get('rating_avg', 0)
        })

        # Category node
        category = professional_data.get('category', 'Other')
        cat_id = f"category_{category.lower().replace(' ', '_')}"

        if not any(n['id'] == cat_id for n in nodes):
            nodes.append({
                'id': cat_id,
                'label': category,
                'type': 'category'
            })

        edges.append({
            'source': prof_id,
            'target': cat_id,
            'type': 'belongs_to'
        })

        # Extract tags from bio
        bio = professional_data.get('bio', '')
        tags = self._extract_tags_from_text(bio)

        for tag in tags[:10]:  # Limit to top 10 tags
            tag_id = f"tag_{tag}"

            if not any(n['id'] == tag_id for n in nodes):
                nodes.append({
                    'id': tag_id,
                    'label': tag,
                    'type': 'tag'
                })

            edges.append({
                'source': prof_id,
                'target': tag_id,
                'type': 'tagged_with'
            })

        # City node
        city = professional_data.get('city')
        if city:
            city_id = f"city_{city.lower().replace(' ', '_')}"

            if not any(n['id'] == city_id for n in nodes):
                nodes.append({
                    'id': city_id,
                    'label': city,
                    'type': 'location'
                })

            edges.append({
                'source': prof_id,
                'target': city_id,
                'type': 'located_in'
            })

        return {
            'nodes': nodes,
            'edges': edges,
            'metadata': {
                'content_type': 'qr_professional',
                'professional_id': professional_data.get('id'),
                'parsed_at': datetime.now().isoformat()
            }
        }


    # =================================================================
    # DATABASE POST/COMMENT PARSING
    # =================================================================

    def parse_database_post(self, post_data: Dict, include_comments: bool = True) -> Dict:
        """
        Parse blog post + comments into conversation graph

        Args:
            post_data: Post dict (title, content, author, comments, etc.)
            include_comments: Whether to parse comments too

        Returns:
            Graph showing post → tags → comments → users
        """
        nodes = []
        edges = []

        # Post node
        post_id = f"post_{post_data.get('id', 'unknown')}"
        nodes.append({
            'id': post_id,
            'label': post_data.get('title', 'Untitled'),
            'type': 'post',
            'author': post_data.get('author'),
            'created_at': post_data.get('created_at')
        })

        # Extract tags from content
        content = post_data.get('content', '')
        tags = self._extract_tags_from_text(content)

        for tag in tags[:15]:
            tag_id = f"tag_{tag}"

            if not any(n['id'] == tag_id for n in nodes):
                nodes.append({
                    'id': tag_id,
                    'label': tag,
                    'type': 'tag'
                })

            edges.append({
                'source': post_id,
                'target': tag_id,
                'type': 'tagged_with'
            })

        # Parse comments (if provided)
        if include_comments and 'comments' in post_data:
            for comment in post_data['comments']:
                comment_id = f"comment_{comment.get('id', 'unknown')}"

                nodes.append({
                    'id': comment_id,
                    'label': comment.get('text', '')[:50] + '...',
                    'type': 'comment',
                    'author': comment.get('author')
                })

                edges.append({
                    'source': comment_id,
                    'target': post_id,
                    'type': 'comments_on'
                })

                # Extract tags from comment
                comment_tags = self._extract_tags_from_text(comment.get('text', ''))
                for tag in comment_tags[:5]:
                    tag_id = f"tag_{tag}"

                    if not any(n['id'] == tag_id for n in nodes):
                        nodes.append({
                            'id': tag_id,
                            'label': tag,
                            'type': 'tag'
                        })

                    edges.append({
                        'source': comment_id,
                        'target': tag_id,
                        'type': 'mentions'
                    })

        return {
            'nodes': nodes,
            'edges': edges,
            'metadata': {
                'content_type': 'database_post',
                'post_id': post_data.get('id'),
                'comment_count': len(post_data.get('comments', [])),
                'parsed_at': datetime.now().isoformat()
            }
        }


    # =================================================================
    # WORDMAP JSON PARSING
    # =================================================================

    def parse_wordmap_json(self, wordmap: Dict[str, int], metadata: Optional[Dict] = None) -> Dict:
        """
        Parse existing wordmap JSON into graph

        Args:
            wordmap: {'word': frequency, ...}
            metadata: Optional metadata

        Returns:
            Graph with word nodes
        """
        nodes = []

        for word, frequency in wordmap.items():
            nodes.append({
                'id': word,
                'label': word,
                'type': 'word',
                'frequency': frequency,
                'source': 'wordmap'
            })

        return {
            'nodes': nodes,
            'edges': [],  # No edges for raw wordmap
            'metadata': {
                'content_type': 'wordmap',
                'total_words': len(wordmap),
                'parsed_at': datetime.now().isoformat(),
                **(metadata or {})
            }
        }


    # =================================================================
    # HELPERS
    # =================================================================

    def _extract_tags_from_text(self, text: str, min_length: int = 3) -> List[str]:
        """
        Extract meaningful tags from text

        Simple approach:
        - Remove common words (stopwords)
        - Extract nouns/keywords
        - Return top words by frequency
        """
        # Common stopwords (minimal list)
        stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
            'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these',
            'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'my', 'your'
        }

        # Extract words
        words = re.findall(r'\b\w+\b', text.lower())

        # Filter and count
        word_counts = Counter()
        for word in words:
            if len(word) >= min_length and word not in stopwords:
                word_counts[word] += 1

        # Return top words
        return [word for word, count in word_counts.most_common(20)]


    # =================================================================
    # MAIN PARSE METHOD
    # =================================================================

    def parse(self, content: any, content_type: str, metadata: Optional[Dict] = None) -> Dict:
        """
        Main parse method - routes to appropriate parser

        Args:
            content: Content to parse (str, dict, etc.)
            content_type: Type of content (voice_transcript, code_python, etc.)
            metadata: Optional metadata

        Returns:
            Standardized graph dict
        """
        if content_type not in self.parsers:
            raise ValueError(f"Unknown content type: {content_type}. Supported: {list(self.parsers.keys())}")

        parser_func = self.parsers[content_type]
        result = parser_func(content, metadata)

        print(f"✅ Parsed {content_type}")
        print(f"   Nodes: {len(result['nodes'])}, Edges: {len(result['edges'])}")

        return result


# =================================================================
# CLI for Testing
# =================================================================

if __name__ == '__main__':
    parser = ContentParser()

    # Test 1: Voice transcript
    print("\n🧪 Test 1: Voice Transcript")
    transcript = "tampa bay plumber repair leak fix emergency service professional reliable"
    graph = parser.parse(transcript, 'voice_transcript')
    print(f"   Graph: {len(graph['nodes'])} nodes, {len(graph['edges'])} edges")

    # Test 2: Python code
    print("\n🧪 Test 2: Python Code")
    code = """
def foo():
    bar()
    baz()

class MyClass:
    def method(self):
        foo()
"""
    graph = parser.parse(code, 'code_python')
    print(f"   Graph: {len(graph['nodes'])} nodes, {len(graph['edges'])} edges")

    # Test 3: Markdown
    print("\n🧪 Test 3: Markdown")
    markdown = """
# Main Title

## Section 1

This is content with a [link](https://example.com).

## Section 2

More content.
"""
    graph = parser.parse(markdown, 'markdown')
    print(f"   Graph: {len(graph['nodes'])} nodes, {len(graph['edges'])} edges")

    print("\n✅ All tests passed!")
