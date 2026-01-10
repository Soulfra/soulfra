#!/usr/bin/env python3
"""
Soulfra Graph - Knowledge Graph and Word Map Builder

Build knowledge graphs from blog posts showing how ideas connect.
Pure Python stdlib only - no networkx or graph libraries.

Features:
- Extract keywords from posts (TF-IDF)
- Find related posts by similarity
- Build knowledge graph (posts → keywords → connections)
- Generate word maps (vocabulary evolution over time)
- Export as HTML visualization

Usage:
    from soulfra_graph import GraphBuilder

    builder = GraphBuilder(db_manager)
    builder.build_graph()
    builder.export_html('graph.html')
"""

import re
import math
import json
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Optional, Any, Set
from datetime import datetime


# ==============================================================================
# KEYWORD EXTRACTION
# ==============================================================================

class KeywordExtractor:
    """Extract keywords using TF-IDF"""

    def __init__(self):
        self.stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this',
            'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
            'your', 'their', 'our', 'my', 'its', 'his', 'her', 'who', 'what',
            'when', 'where', 'why', 'how', 'about', 'into', 'through', 'during',
            'before', 'after', 'above', 'below', 'up', 'down', 'out', 'off', 'over',
            'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when',
            'where', 'why', 'how', 'all', 'both', 'each', 'few', 'more', 'most',
            'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same',
            'so', 'than', 'too', 'very', 'can', 'just', 'don', 'now'
        }

    def tokenize(self, text: str) -> List[str]:
        """Tokenize text into words"""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Extract words (3+ letters)
        words = re.findall(r'\b[a-z]{3,}\b', text.lower())
        # Remove stopwords
        return [w for w in words if w not in self.stopwords]

    def calculate_tf(self, words: List[str]) -> Dict[str, float]:
        """Calculate term frequency"""
        counts = Counter(words)
        total = len(words) if words else 1
        return {word: count / total for word, count in counts.items()}

    def calculate_idf(self, documents: List[List[str]]) -> Dict[str, float]:
        """Calculate inverse document frequency"""
        total_docs = len(documents)
        if total_docs == 0:
            return {}

        # Count documents containing each word
        word_doc_count = Counter()
        for doc_words in documents:
            unique_words = set(doc_words)
            word_doc_count.update(unique_words)

        # Calculate IDF
        idf = {}
        for word, doc_count in word_doc_count.items():
            idf[word] = math.log(total_docs / doc_count)

        return idf

    def extract_keywords(self, text: str, idf: Dict[str, float], top_n: int = 10) -> List[Tuple[str, float]]:
        """
        Extract top keywords from text using TF-IDF

        Args:
            text: Text to analyze
            idf: Pre-calculated IDF scores
            top_n: Number of keywords to extract

        Returns:
            List of (keyword, tfidf_score) tuples
        """
        words = self.tokenize(text)
        tf = self.calculate_tf(words)

        # Calculate TF-IDF
        tfidf = {}
        for word, tf_score in tf.items():
            if word in idf:
                tfidf[word] = tf_score * idf[word]

        # Sort by score and return top N
        sorted_keywords = sorted(tfidf.items(), key=lambda x: x[1], reverse=True)
        return sorted_keywords[:top_n]


# ==============================================================================
# SIMILARITY CALCULATION
# ==============================================================================

def calculate_jaccard_similarity(keywords1: List[str], keywords2: List[str]) -> float:
    """
    Calculate Jaccard similarity between two keyword lists

    Jaccard = |intersection| / |union|
    """
    set1 = set(keywords1)
    set2 = set(keywords2)

    intersection = len(set1 & set2)
    union = len(set1 | set2)

    if union == 0:
        return 0.0

    return intersection / union


def calculate_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors

    cosine = (A · B) / (||A|| * ||B||)
    """
    if len(vec1) != len(vec2):
        return 0.0

    # Dot product
    dot_product = sum(a * b for a, b in zip(vec1, vec2))

    # Magnitudes
    magnitude1 = math.sqrt(sum(a ** 2 for a in vec1))
    magnitude2 = math.sqrt(sum(b ** 2 for b in vec2))

    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0

    return dot_product / (magnitude1 * magnitude2)


# ==============================================================================
# KNOWLEDGE GRAPH BUILDER
# ==============================================================================

class GraphBuilder:
    """Build knowledge graph from blog posts"""

    def __init__(self, db_manager):
        """
        Initialize graph builder

        Args:
            db_manager: DatabaseManager instance from soulfra_local
        """
        self.db = db_manager
        self.extractor = KeywordExtractor()
        self.graph: Dict[str, Any] = {
            'nodes': [],  # Posts
            'edges': [],  # Connections
            'keywords': {}  # Keyword → posts mapping
        }

    def build_graph(self, min_tier: int = 1, min_similarity: float = 0.2) -> Dict[str, Any]:
        """
        Build knowledge graph from posts

        Args:
            min_tier: Minimum tier of posts to include
            min_similarity: Minimum similarity threshold for connections

        Returns:
            Graph statistics
        """
        # Get posts
        posts = self.db.get_posts_by_tier(min_tier)

        if len(posts) < 2:
            return {'error': 'Need at least 2 posts to build graph'}

        print(f"📊 Building knowledge graph from {len(posts)} posts...")

        # Extract keywords from all posts
        all_doc_words = []
        post_keywords = {}

        for post in posts:
            words = self.extractor.tokenize(post['content'])
            all_doc_words.append(words)
            post_keywords[post['id']] = words

        # Calculate IDF
        idf = self.extractor.calculate_idf(all_doc_words)

        # Extract top keywords for each post
        post_top_keywords = {}
        keyword_posts = defaultdict(list)

        for post in posts:
            keywords = self.extractor.extract_keywords(post['content'], idf, top_n=5)
            post_top_keywords[post['id']] = [kw for kw, score in keywords]

            # Build keyword → posts mapping
            for keyword, score in keywords:
                keyword_posts[keyword].append({
                    'post_id': post['id'],
                    'title': post['title'],
                    'score': score
                })

        # Create nodes (posts)
        for post in posts:
            self.graph['nodes'].append({
                'id': post['id'],
                'title': post['title'],
                'slug': post['slug'],
                'tier': post['tier'],
                'keywords': post_top_keywords.get(post['id'], []),
                'created_at': post['created_at']
            })

        # Create edges (connections)
        for i, post1 in enumerate(posts):
            for post2 in posts[i + 1:]:
                # Calculate similarity
                keywords1 = post_keywords[post1['id']]
                keywords2 = post_keywords[post2['id']]
                similarity = calculate_jaccard_similarity(keywords1, keywords2)

                if similarity >= min_similarity:
                    # Find shared keywords
                    shared_keywords = list(set(post_top_keywords[post1['id']]) & set(post_top_keywords[post2['id']]))

                    self.graph['edges'].append({
                        'from': post1['id'],
                        'to': post2['id'],
                        'similarity': similarity,
                        'shared_keywords': shared_keywords
                    })

        # Store keyword → posts mapping
        self.graph['keywords'] = {
            keyword: posts_list
            for keyword, posts_list in keyword_posts.items()
        }

        print(f"✅ Graph built successfully!")
        print(f"   Nodes (posts): {len(self.graph['nodes'])}")
        print(f"   Edges (connections): {len(self.graph['edges'])}")
        print(f"   Unique keywords: {len(self.graph['keywords'])}")

        # Save to database
        self._save_graph()

        return {
            'nodes': len(self.graph['nodes']),
            'edges': len(self.graph['edges']),
            'keywords': len(self.graph['keywords']),
            'avg_connections': len(self.graph['edges']) / len(self.graph['nodes']) if self.graph['nodes'] else 0
        }

    def find_related_posts(self, post_id: int, limit: int = 5) -> List[Dict]:
        """
        Find posts related to given post

        Args:
            post_id: Post ID to find relations for
            limit: Maximum number of related posts

        Returns:
            List of related posts with similarity scores
        """
        related = []

        for edge in self.graph['edges']:
            if edge['from'] == post_id:
                related.append({
                    'post_id': edge['to'],
                    'similarity': edge['similarity'],
                    'shared_keywords': edge['shared_keywords']
                })
            elif edge['to'] == post_id:
                related.append({
                    'post_id': edge['from'],
                    'similarity': edge['similarity'],
                    'shared_keywords': edge['shared_keywords']
                })

        # Sort by similarity
        related.sort(key=lambda x: x['similarity'], reverse=True)

        return related[:limit]

    def get_word_map(self) -> Dict[str, List[Dict]]:
        """
        Get word map showing keyword usage across posts

        Returns:
            Dictionary mapping keywords to posts
        """
        return self.graph['keywords']

    def export_html(self, output_path: str):
        """
        Export knowledge graph as interactive HTML visualization

        Args:
            output_path: Path to save HTML file
        """
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Knowledge Graph - Soulfra Local</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #1a1a1a;
            color: #e0e0e0;
        }}
        h1 {{ color: #4ECDC4; }}
        h2 {{ color: #FF6B6B; margin-top: 40px; }}
        .node {{
            background: #2c2c2c;
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #4ECDC4;
            border-radius: 4px;
        }}
        .node-title {{ font-weight: bold; color: #4ECDC4; }}
        .keywords {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 10px;
        }}
        .keyword {{
            background: #3a3a3a;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 14px;
            color: #95E1D3;
        }}
        .connection {{
            background: #2c2c2c;
            padding: 10px;
            margin: 5px 0;
            border-left: 3px solid #FF6B6B;
            border-radius: 4px;
            font-size: 14px;
        }}
        .similarity {{
            color: #FF6B6B;
            font-weight: bold;
        }}
        .stats {{
            background: #2c2c2c;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .stat-item {{
            display: inline-block;
            margin-right: 30px;
        }}
        .stat-value {{
            font-size: 32px;
            font-weight: bold;
            color: #4ECDC4;
        }}
        .stat-label {{
            font-size: 14px;
            color: #888;
        }}
    </style>
</head>
<body>
    <h1>🗺️ Knowledge Graph</h1>

    <div class="stats">
        <div class="stat-item">
            <div class="stat-value">{len(self.graph['nodes'])}</div>
            <div class="stat-label">Posts</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">{len(self.graph['edges'])}</div>
            <div class="stat-label">Connections</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">{len(self.graph['keywords'])}</div>
            <div class="stat-label">Unique Keywords</div>
        </div>
    </div>

    <h2>📝 Posts & Keywords</h2>
'''

        # Add nodes
        for node in self.graph['nodes']:
            keywords_html = ''.join(f'<span class="keyword">{kw}</span>' for kw in node['keywords'])
            html += f'''
    <div class="node">
        <div class="node-title">{node['title']}</div>
        <div class="keywords">{keywords_html}</div>
    </div>
'''

        # Add connections
        html += '<h2>🔗 Connections</h2>'
        for edge in self.graph['edges'][:50]:  # Limit to 50 connections
            # Find node titles
            from_node = next((n for n in self.graph['nodes'] if n['id'] == edge['from']), None)
            to_node = next((n for n in self.graph['nodes'] if n['id'] == edge['to']), None)

            if from_node and to_node:
                shared = ', '.join(edge['shared_keywords'])
                html += f'''
    <div class="connection">
        <strong>{from_node['title']}</strong> ↔ <strong>{to_node['title']}</strong>
        <span class="similarity">({edge['similarity']:.1%} similar)</span>
        <br>
        Shared keywords: {shared}
    </div>
'''

        html += '''
</body>
</html>
'''

        # Write to file
        with open(output_path, 'w') as f:
            f.write(html)

        print(f"✅ Exported graph to {output_path}")

    def _save_graph(self):
        """Save graph to database"""
        cursor = self.db.conn.cursor()

        # Save each edge to database
        for edge in self.graph['edges']:
            cursor.execute('''
                INSERT OR REPLACE INTO knowledge_graph
                (post_id_1, post_id_2, similarity, shared_keywords)
                VALUES (?, ?, ?, ?)
            ''', (
                edge['from'],
                edge['to'],
                edge['similarity'],
                json.dumps(edge['shared_keywords'])
            ))

        self.db.conn.commit()


if __name__ == '__main__':
    print("🗺️ Soulfra Graph - Knowledge Graph Builder")
    print("Import this module into soulfra_local.py to build knowledge graphs")
    print("\nExample usage:")
    print("  from soulfra_graph import GraphBuilder")
    print("  builder = GraphBuilder(db_manager)")
    print("  builder.build_graph()")
    print("  builder.export_html('graph.html')")
