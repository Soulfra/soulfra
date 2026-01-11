#!/usr/bin/env python3
"""
Wordmap to Graph Converter - Bridge Between Existing Systems

Converts:
- User wordmaps (from user_wordmap_engine.py) → Graph nodes/edges
- Domain wordmaps (from domain_wordmap_aggregator.py) → Graph nodes/edges
- CringeProof wall posts → Voice wordmaps → Graph
- StPetePros professionals → Tags → Graph

This is the GLUE that connects your existing wordmap system to the new canvas visualization.
"""

import json
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from database import get_db
from collections import Counter


class WordmapToGraph:
    """
    Convert wordmap data into graph structure for visualization

    Takes wordmaps from database and converts to nodes + edges
    that canvas_visualizer.py can render
    """

    def __init__(self):
        print("🔗 Wordmap-to-Graph Bridge initialized")


    def user_wordmap_to_graph(self, user_id: int) -> Dict:
        """
        Convert user's cumulative wordmap to graph

        Args:
            user_id: User ID

        Returns:
            Graph dict with nodes (words) and edges (co-occurrences)
        """
        from user_wordmap_engine import get_user_wordmap

        # Get user wordmap
        wordmap_data = get_user_wordmap(user_id)

        if not wordmap_data:
            return {'nodes': [], 'edges': [], 'metadata': {'error': 'No wordmap found'}}

        wordmap = wordmap_data['wordmap']

        # Create nodes from words
        nodes = []
        for word, frequency in wordmap.items():
            nodes.append({
                'id': word,
                'label': word,
                'type': 'word',
                'frequency': frequency,
                'source': 'user_wordmap',
                'user_id': user_id
            })

        # Create edges (co-occurrence from original recordings)
        # For now, connect top words to each other with weights
        edges = []
        top_words = sorted(wordmap.items(), key=lambda x: x[1], reverse=True)[:20]

        for i, (word1, freq1) in enumerate(top_words):
            for word2, freq2 in top_words[i+1:i+6]:  # Connect to next 5 words
                # Edge weight = min of two frequencies
                weight = min(freq1, freq2)

                edges.append({
                    'source': word1,
                    'target': word2,
                    'type': 'related',
                    'weight': weight
                })

        return {
            'nodes': nodes,
            'edges': edges,
            'metadata': {
                'content_type': 'user_wordmap',
                'user_id': user_id,
                'recording_count': wordmap_data['recording_count'],
                'total_words': len(wordmap),
                'generated_at': datetime.now().isoformat()
            }
        }


    def domain_wordmap_to_graph(self, domain: str) -> Dict:
        """
        Convert domain's collective wordmap to graph

        Shows how multiple users' voices combine into brand voice

        Args:
            domain: Domain name (e.g., 'soulfra.com')

        Returns:
            Graph with weighted words + contributor nodes
        """
        from domain_wordmap_aggregator import get_domain_wordmap

        # Get domain wordmap
        wordmap_data = get_domain_wordmap(domain)

        if not wordmap_data:
            return {'nodes': [], 'edges': [], 'metadata': {'error': 'No wordmap found'}}

        wordmap = wordmap_data['wordmap']

        # Domain node
        nodes = [{
            'id': f'domain_{domain}',
            'label': domain,
            'type': 'domain',
            'contributor_count': wordmap_data['contributor_count']
        }]

        # Word nodes
        for word, weighted_frequency in wordmap.items():
            nodes.append({
                'id': word,
                'label': word,
                'type': 'word',
                'frequency': int(weighted_frequency),
                'source': 'domain_wordmap',
                'domain': domain
            })

            # Connect word to domain
            edges = [{
                'source': f'domain_{domain}',
                'target': word,
                'type': 'contains',
                'weight': int(weighted_frequency)
            }]

        # TODO: Add contributor nodes (users who contribute to this domain)

        return {
            'nodes': nodes,
            'edges': edges if 'edges' in locals() else [],
            'metadata': {
                'content_type': 'domain_wordmap',
                'domain': domain,
                'contributor_count': wordmap_data['contributor_count'],
                'total_recordings': wordmap_data.get('total_recordings', 0),
                'generated_at': datetime.now().isoformat()
            }
        }


    def cringeproof_wall_to_graph(self, limit: int = 50) -> Dict:
        """
        Convert CringeProof wall posts into conversation graph

        Shows:
        - Posts as nodes
        - Voice recordings as nodes
        - Wordmaps extracted from each
        - Connections between related posts

        Args:
            limit: Max number of posts to include

        Returns:
            Graph showing post network
        """
        db = get_db()

        # Get recent voice recordings
        recordings = db.execute('''
            SELECT id, filename, transcription, created_at
            FROM simple_voice_recordings
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,)).fetchall()

        nodes = []
        edges = []

        # Track all words for global wordmap
        global_wordmap = Counter()

        for recording in recordings:
            rec_id = recording['id']
            transcript = recording['transcription'] or ''

            # Recording node
            nodes.append({
                'id': f'recording_{rec_id}',
                'label': f"Voice {rec_id}",
                'type': 'voice_recording',
                'created_at': recording['created_at'],
                'preview': transcript[:50] + '...' if transcript else 'No transcript'
            })

            # Extract wordmap from transcript
            if transcript:
                from content_parser import ContentParser
                parser = ContentParser()

                try:
                    graph = parser.parse(transcript, 'voice_transcript')

                    # Add word nodes
                    for node in graph['nodes']:
                        word = node['id']

                        # Check if word node already exists
                        existing = next((n for n in nodes if n['id'] == word), None)

                        if existing:
                            # Increase frequency
                            existing['frequency'] += node['frequency']
                        else:
                            # Add new word node
                            nodes.append({
                                'id': word,
                                'label': word,
                                'type': 'word',
                                'frequency': node['frequency'],
                                'source': 'cringeproof_wall'
                            })

                        # Connect recording to word
                        edges.append({
                            'source': f'recording_{rec_id}',
                            'target': word,
                            'type': 'contains',
                            'weight': node['frequency']
                        })

                        # Update global wordmap
                        global_wordmap[word] += node['frequency']

                except Exception as e:
                    print(f"⚠️ Error parsing recording {rec_id}: {e}")

        db.close()

        # Add edges between related words (global co-occurrence)
        top_words = [word for word, freq in global_wordmap.most_common(30)]

        for i, word1 in enumerate(top_words):
            for word2 in top_words[i+1:i+5]:
                # Calculate co-occurrence weight
                weight = min(global_wordmap[word1], global_wordmap[word2])

                edges.append({
                    'source': word1,
                    'target': word2,
                    'type': 'co-occurrence',
                    'weight': weight
                })

        return {
            'nodes': nodes,
            'edges': edges,
            'metadata': {
                'content_type': 'cringeproof_wall',
                'recording_count': len(recordings),
                'unique_words': len(global_wordmap),
                'generated_at': datetime.now().isoformat()
            }
        }


    def stpetepros_network_to_graph(self, limit: int = 50) -> Dict:
        """
        Convert StPetePros professionals into network graph

        Shows:
        - Professional nodes
        - Category nodes
        - Location nodes
        - Tag nodes (from bios)

        Args:
            limit: Max professionals to include

        Returns:
            Graph showing professional network
        """
        db = get_db()

        # Get professionals
        professionals = db.execute('''
            SELECT id, business_name, category, bio, city, rating_avg
            FROM professionals
            ORDER BY rating_avg DESC
            LIMIT ?
        ''', (limit,)).fetchall()

        if not professionals:
            return {'nodes': [], 'edges': [], 'metadata': {'error': 'No professionals found'}}

        # Parse each professional
        from content_parser import ContentParser
        parser = ContentParser()

        all_nodes = []
        all_edges = []

        # Track categories and cities to avoid duplicates
        categories_added = set()
        cities_added = set()

        for prof in professionals:
            prof_data = {
                'id': prof['id'],
                'business_name': prof['business_name'],
                'category': prof['category'],
                'bio': prof['bio'] or '',
                'city': prof['city'],
                'rating_avg': prof['rating_avg'] or 0
            }

            # Parse professional
            graph = parser.parse(prof_data, 'qr_professional')

            # Merge nodes (avoid duplicates)
            for node in graph['nodes']:
                if node['type'] == 'category' and node['id'] in categories_added:
                    continue
                if node['type'] == 'location' and node['id'] in cities_added:
                    continue

                all_nodes.append(node)

                if node['type'] == 'category':
                    categories_added.add(node['id'])
                if node['type'] == 'location':
                    cities_added.add(node['id'])

            # Merge edges
            all_edges.extend(graph['edges'])

        db.close()

        return {
            'nodes': all_nodes,
            'edges': all_edges,
            'metadata': {
                'content_type': 'stpetepros_network',
                'professional_count': len(professionals),
                'category_count': len(categories_added),
                'city_count': len(cities_added),
                'generated_at': datetime.now().isoformat()
            }
        }


    def combined_graph(self, sources: List[str], **kwargs) -> Dict:
        """
        Combine multiple graph sources into one mega-graph

        Args:
            sources: List of source types ['user_wordmap', 'cringeproof_wall', 'stpetepros']
            **kwargs: Source-specific params (user_id, domain, etc.)

        Returns:
            Combined graph
        """
        all_nodes = []
        all_edges = []
        all_metadata = {'sources': sources}

        for source in sources:
            graph = None

            if source == 'user_wordmap' and 'user_id' in kwargs:
                graph = self.user_wordmap_to_graph(kwargs['user_id'])

            elif source == 'domain_wordmap' and 'domain' in kwargs:
                graph = self.domain_wordmap_to_graph(kwargs['domain'])

            elif source == 'cringeproof_wall':
                graph = self.cringeproof_wall_to_graph(kwargs.get('limit', 50))

            elif source == 'stpetepros':
                graph = self.stpetepros_network_to_graph(kwargs.get('limit', 50))

            if graph and 'error' not in graph.get('metadata', {}):
                # Merge nodes (avoid duplicates)
                for node in graph['nodes']:
                    if not any(n['id'] == node['id'] for n in all_nodes):
                        all_nodes.append(node)

                # Merge edges
                all_edges.extend(graph['edges'])

                # Merge metadata
                all_metadata[source] = graph['metadata']

        return {
            'nodes': all_nodes,
            'edges': all_edges,
            'metadata': all_metadata
        }


# =================================================================
# CLI for Testing
# =================================================================

if __name__ == '__main__':
    converter = WordmapToGraph()

    # Test 1: CringeProof wall
    print("\n🧪 Test 1: CringeProof Wall → Graph")
    graph = converter.cringeproof_wall_to_graph(limit=10)
    print(f"   Nodes: {len(graph['nodes'])}, Edges: {len(graph['edges'])}")
    print(f"   Recordings: {graph['metadata'].get('recording_count', 0)}")

    # Test 2: StPetePros network
    print("\n🧪 Test 2: StPetePros Network → Graph")
    graph = converter.stpetepros_network_to_graph(limit=10)
    print(f"   Nodes: {len(graph['nodes'])}, Edges: {len(graph['edges'])}")
    print(f"   Professionals: {graph['metadata'].get('professional_count', 0)}")

    # Test 3: Combined graph
    print("\n🧪 Test 3: Combined Graph")
    graph = converter.combined_graph(
        sources=['cringeproof_wall', 'stpetepros'],
        limit=20
    )
    print(f"   Total Nodes: {len(graph['nodes'])}, Total Edges: {len(graph['edges'])}")

    print("\n✅ All tests complete!")
