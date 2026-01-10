#!/usr/bin/env python3
"""
Knowledge Extractor - Background Learning System

Runs invisibly after each chat interaction to extract:
- Entities (people, places, concepts, technologies)
- Topics (themes user cares about)
- Relationships (how concepts connect)
- Domain mapping (CalRiven, DeathToData, Soulfra, HowToCookAtHome)

User never sees this - it just makes the AI smarter about them over time.
"""

import json
import re
from typing import Dict, List, Optional
from datetime import datetime
from database import get_db


class KnowledgeExtractor:
    """Extract knowledge from conversations and build user profile"""

    # Domain keywords for automatic domain mapping
    DOMAIN_KEYWORDS = {
        'calriven': ['architecture', 'algorithm', 'scalability', 'performance', 'design', 'pattern', 'system', 'technical'],
        'deathtodata': ['privacy', 'tracking', 'surveillance', 'decentralization', 'data', 'anonymous', 'federation'],
        'soulfra': ['security', 'encryption', 'cryptography', 'authentication', 'auth', 'access', 'key', 'hash'],
        'howtocookathome': ['cooking', 'recipe', 'ingredient', 'kitchen', 'food', 'cook', 'bake', 'chef']
    }

    # Common entity patterns (simple keyword extraction)
    TECHNOLOGY_KEYWORDS = [
        'python', 'javascript', 'flask', 'ollama', 'ai', 'llm', 'model', 'api', 'database',
        'sqlite', 'encryption', 'aes', 'qr', 'code', 'server', 'http', 'https', 'ssl',
        'json', 'html', 'css', 'template', 'route', 'endpoint', 'query', 'session'
    ]

    CONCEPT_KEYWORDS = [
        'security', 'privacy', 'architecture', 'design', 'pattern', 'system', 'framework',
        'workflow', 'automation', 'integration', 'federation', 'decentralization', 'chat',
        'conversation', 'knowledge', 'graph', 'relationship', 'entity', 'topic'
    ]

    def __init__(self, user_id: Optional[int] = None):
        """Initialize knowledge extractor"""
        self.user_id = user_id

    def extract_from_conversation(self, user_message: str, ai_response: str, session_id: str) -> Dict:
        """
        Extract knowledge from a conversation turn

        Args:
            user_message: What the user said
            ai_response: How the AI responded
            session_id: Conversation session ID

        Returns:
            Dict with extraction stats
        """
        start_time = datetime.now()

        # Combine messages for context
        full_conversation = f"{user_message} {ai_response}"

        # Extract entities
        entities = self._extract_entities(full_conversation)

        # Extract topics
        topics = self._extract_topics(full_conversation)

        # Map to domains
        domain_mappings = self._map_to_domains(entities, topics, full_conversation)

        # Store in database
        db = get_db()

        entities_stored = 0
        for entity in entities:
            entities_stored += self._store_entity(db, entity, domain_mappings.get(entity, {}))

        topics_stored = 0
        for topic in topics:
            topics_stored += self._store_topic(db, topic, domain_mappings.get(topic, {}))

        # Find relationships between entities
        relationships_added = self._extract_relationships(db, entities)

        # Update user profile
        self._update_user_profile(db, topics)

        # Log extraction
        end_time = datetime.now()
        extraction_time_ms = int((end_time - start_time).total_seconds() * 1000)

        db.execute('''
            INSERT INTO knowledge_extraction_log
            (session_id, entities_extracted, topics_identified, relationships_added, extraction_time_ms)
            VALUES (?, ?, ?, ?, ?)
        ''', (session_id, entities_stored, topics_stored, relationships_added, extraction_time_ms))

        db.commit()
        db.close()

        return {
            'entities': entities_stored,
            'topics': topics_stored,
            'relationships': relationships_added,
            'extraction_time_ms': extraction_time_ms
        }

    def _extract_entities(self, text: str) -> List[str]:
        """Extract entities from text (simple keyword matching for now)"""
        text_lower = text.lower()
        entities = []

        # Technology entities
        for keyword in self.TECHNOLOGY_KEYWORDS:
            if keyword in text_lower:
                entities.append(keyword)

        # Concept entities
        for keyword in self.CONCEPT_KEYWORDS:
            if keyword in text_lower:
                entities.append(keyword)

        return list(set(entities))  # Deduplicate

    def _extract_topics(self, text: str) -> List[str]:
        """Extract topics/themes from conversation"""
        topics = []

        # Check for question patterns
        if '?' in text:
            if any(word in text.lower() for word in ['how', 'what', 'why', 'when', 'where']):
                topics.append('question-asking')

        # Check for domain-related topics
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            if any(kw in text.lower() for kw in keywords):
                topics.append(domain)

        # Check for technical vs casual tone
        if any(word in text.lower() for word in ['implement', 'build', 'create', 'develop', 'code']):
            topics.append('technical-implementation')

        if any(word in text.lower() for word in ['help', 'understand', 'explain', 'learn']):
            topics.append('learning')

        return list(set(topics))

    def _map_to_domains(self, entities: List[str], topics: List[str], text: str) -> Dict[str, Dict]:
        """Map entities/topics to domains with relevance scores"""
        mappings = {}
        text_lower = text.lower()

        for entity in entities + topics:
            scores = {}

            # Calculate relevance to each domain
            for domain, keywords in self.DOMAIN_KEYWORDS.items():
                # Count keyword matches
                matches = sum(1 for kw in keywords if kw in text_lower)
                if matches > 0:
                    scores[domain] = matches / len(keywords)  # Normalized score

            if scores:
                # Get top domain
                top_domain = max(scores, key=scores.get)
                mappings[entity] = {
                    'domain': top_domain,
                    'relevance': scores[top_domain]
                }

        return mappings

    def _store_entity(self, db, entity_text: str, domain_info: Dict) -> int:
        """Store or update entity in database"""
        if not self.user_id:
            return 0

        domain = domain_info.get('domain')

        # Check if entity exists
        existing = db.execute('''
            SELECT id, mention_count, relevance_score
            FROM knowledge_entities
            WHERE entity_text = ? AND user_id = ?
        ''', (entity_text, self.user_id)).fetchone()

        if existing:
            # Update existing entity
            new_mention_count = existing['mention_count'] + 1
            new_relevance = min(existing['relevance_score'] + 0.1, 10.0)  # Increase relevance, cap at 10

            db.execute('''
                UPDATE knowledge_entities
                SET mention_count = ?,
                    relevance_score = ?,
                    last_mentioned_at = datetime('now')
                WHERE id = ?
            ''', (new_mention_count, new_relevance, existing['id']))

            return 0  # Updated, not new
        else:
            # Create new entity
            db.execute('''
                INSERT INTO knowledge_entities
                (entity_text, entity_type, user_id, domain_context, relevance_score)
                VALUES (?, 'concept', ?, ?, ?)
            ''', (entity_text, self.user_id, domain, domain_info.get('relevance', 1.0)))

            return 1  # New entity

    def _store_topic(self, db, topic_name: str, domain_info: Dict) -> int:
        """Store or update topic in database"""
        if not self.user_id:
            return 0

        domain = domain_info.get('domain')

        # Check if topic exists
        existing = db.execute('''
            SELECT id, conversation_count, interest_level
            FROM knowledge_topics
            WHERE topic_name = ? AND user_id = ?
        ''', (topic_name, self.user_id)).fetchone()

        if existing:
            # Update existing topic
            new_count = existing['conversation_count'] + 1
            new_interest = min(existing['interest_level'] + 0.2, 10.0)  # Increase interest

            db.execute('''
                UPDATE knowledge_topics
                SET conversation_count = ?,
                    interest_level = ?,
                    last_discussed_at = datetime('now')
                WHERE id = ?
            ''', (new_count, new_interest, existing['id']))

            return 0
        else:
            # Create new topic
            db.execute('''
                INSERT INTO knowledge_topics
                (topic_name, user_id, domain_affinity, interest_level)
                VALUES (?, ?, ?, 1.0)
            ''', (topic_name, self.user_id, domain))

            return 1

    def _extract_relationships(self, db, entities: List[str]) -> int:
        """Find relationships between entities (co-occurrence)"""
        if not self.user_id or len(entities) < 2:
            return 0

        relationships_added = 0

        # For each pair of entities
        for i, entity_a in enumerate(entities):
            for entity_b in entities[i+1:]:
                # Get entity IDs
                entity_a_row = db.execute('''
                    SELECT id FROM knowledge_entities
                    WHERE entity_text = ? AND user_id = ?
                ''', (entity_a, self.user_id)).fetchone()

                entity_b_row = db.execute('''
                    SELECT id FROM knowledge_entities
                    WHERE entity_text = ? AND user_id = ?
                ''', (entity_b, self.user_id)).fetchone()

                if not entity_a_row or not entity_b_row:
                    continue

                entity_a_id = entity_a_row['id']
                entity_b_id = entity_b_row['id']

                # Check if relationship exists
                existing = db.execute('''
                    SELECT id, co_occurrence_count, strength
                    FROM knowledge_relationships
                    WHERE entity_a_id = ? AND entity_b_id = ?
                       AND relationship_type = 'related_to'
                ''', (entity_a_id, entity_b_id)).fetchone()

                if existing:
                    # Strengthen existing relationship
                    new_count = existing['co_occurrence_count'] + 1
                    new_strength = min(existing['strength'] + 0.1, 10.0)

                    db.execute('''
                        UPDATE knowledge_relationships
                        SET co_occurrence_count = ?,
                            strength = ?,
                            last_seen_at = datetime('now')
                        WHERE id = ?
                    ''', (new_count, new_strength, existing['id']))
                else:
                    # Create new relationship
                    db.execute('''
                        INSERT INTO knowledge_relationships
                        (entity_a_id, entity_b_id, relationship_type, strength)
                        VALUES (?, ?, 'related_to', 1.0)
                    ''', (entity_a_id, entity_b_id))

                    relationships_added += 1

        return relationships_added

    def _update_user_profile(self, db, topics: List[str]):
        """Update user's overall profile with latest topics"""
        if not self.user_id:
            return

        # Get top topics by interest level
        top_topics = db.execute('''
            SELECT topic_name, interest_level
            FROM knowledge_topics
            WHERE user_id = ?
            ORDER BY interest_level DESC
            LIMIT 10
        ''', (self.user_id,)).fetchall()

        primary_interests = [t['topic_name'] for t in top_topics]

        # Get favorite domains
        domain_counts = {}
        for topic in top_topics:
            topic_row = db.execute('''
                SELECT domain_affinity FROM knowledge_topics
                WHERE topic_name = ? AND user_id = ?
            ''', (topic['topic_name'], self.user_id)).fetchone()

            if topic_row and topic_row['domain_affinity']:
                domain = topic_row['domain_affinity']
                domain_counts[domain] = domain_counts.get(domain, 0) + 1

        favorite_domains = sorted(domain_counts.keys(), key=lambda d: domain_counts[d], reverse=True)[:3]

        # Check if profile exists
        existing = db.execute('''
            SELECT user_id, total_conversations FROM knowledge_user_profile
            WHERE user_id = ?
        ''', (self.user_id,)).fetchone()

        if existing:
            # Update existing profile
            db.execute('''
                UPDATE knowledge_user_profile
                SET primary_interests = ?,
                    favorite_domains = ?,
                    total_conversations = ?,
                    updated_at = datetime('now')
                WHERE user_id = ?
            ''', (json.dumps(primary_interests), json.dumps(favorite_domains),
                  existing['total_conversations'] + 1, self.user_id))
        else:
            # Create new profile
            db.execute('''
                INSERT INTO knowledge_user_profile
                (user_id, primary_interests, favorite_domains, total_conversations)
                VALUES (?, ?, ?, 1)
            ''', (self.user_id, json.dumps(primary_interests), json.dumps(favorite_domains)))

    def get_user_context(self) -> Dict:
        """Get enriched context about user for future queries"""
        if not self.user_id:
            return {}

        db = get_db()

        # Get user profile
        profile = db.execute('''
            SELECT primary_interests, favorite_domains, total_conversations
            FROM knowledge_user_profile
            WHERE user_id = ?
        ''', (self.user_id,)).fetchone()

        if not profile:
            db.close()
            return {}

        # Get top entities
        top_entities = db.execute('''
            SELECT entity_text, domain_context, relevance_score
            FROM knowledge_entities
            WHERE user_id = ?
            ORDER BY relevance_score DESC
            LIMIT 10
        ''', (self.user_id,)).fetchall()

        # Get top topics
        top_topics = db.execute('''
            SELECT topic_name, domain_affinity, interest_level
            FROM knowledge_topics
            WHERE user_id = ?
            ORDER BY interest_level DESC
            LIMIT 10
        ''', (self.user_id,)).fetchall()

        db.close()

        return {
            'interests': json.loads(profile['primary_interests']) if profile['primary_interests'] else [],
            'domains': json.loads(profile['favorite_domains']) if profile['favorite_domains'] else [],
            'conversations': profile['total_conversations'],
            'top_entities': [e['entity_text'] for e in top_entities],
            'top_topics': [t['topic_name'] for t in top_topics]
        }


if __name__ == '__main__':
    print("Knowledge Extractor Test")
    print("")

    # Example usage
    extractor = KnowledgeExtractor(user_id=1)

    result = extractor.extract_from_conversation(
        user_message="How do I implement encryption for my voice memos?",
        ai_response="You can use AES-256 encryption with Python's cryptography library. Store the encrypted data with an IV and key hash for verification.",
        session_id="test-session"
    )

    print("Extraction Results:")
    print(f"  Entities: {result['entities']}")
    print(f"  Topics: {result['topics']}")
    print(f"  Relationships: {result['relationships']}")
    print(f"  Time: {result['extraction_time_ms']}ms")
    print("")

    context = extractor.get_user_context()
    print("User Context:")
    print(f"  Interests: {context.get('interests', [])}")
    print(f"  Domains: {context.get('domains', [])}")
    print(f"  Conversations: {context.get('conversations', 0)}")
