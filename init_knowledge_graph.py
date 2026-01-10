#!/usr/bin/env python3
"""
Knowledge Graph - Background Learning System

Invisible to user, runs automatically after each chat to build knowledge graph.

Tables:
- knowledge_entities - People, places, concepts extracted from conversations
- knowledge_topics - Topics/themes the user cares about
- knowledge_relationships - How concepts connect
- knowledge_domain_mapping - Which domains (CalRiven, DeathToData, etc.) relate to which concepts
- knowledge_user_profile - User interests, patterns, frequently asked questions
"""

import sqlite3
from datetime import datetime


def init_knowledge_graph_tables():
    """Initialize knowledge graph database tables"""

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    # ==========================================================================
    # KNOWLEDGE ENTITIES - Things extracted from conversations
    # ==========================================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS knowledge_entities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_text TEXT NOT NULL,
            entity_type TEXT,
            -- Type: person, place, concept, technology, domain, question
            user_id INTEGER,
            domain_context TEXT,
            -- Which domain was this mentioned in? (calriven, deathtodata, soulfra, howtocookathome)
            first_mentioned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_mentioned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            mention_count INTEGER DEFAULT 1,
            relevance_score REAL DEFAULT 1.0,
            -- How important is this to the user? (updated over time)
            UNIQUE(entity_text, user_id)
        )
    ''')

    # ==========================================================================
    # KNOWLEDGE TOPICS - Themes user cares about
    # ==========================================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS knowledge_topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_name TEXT NOT NULL,
            -- e.g., "security", "privacy", "cooking", "domains"
            user_id INTEGER,
            domain_affinity TEXT,
            -- Which domain is this topic most related to?
            conversation_count INTEGER DEFAULT 0,
            -- How many times discussed?
            interest_level REAL DEFAULT 1.0,
            -- 0.0 to 10.0, increases with repeated mentions
            keywords TEXT,
            -- JSON array of related keywords
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_discussed_at TIMESTAMP,
            UNIQUE(topic_name, user_id)
        )
    ''')

    # ==========================================================================
    # KNOWLEDGE RELATIONSHIPS - How concepts connect
    # ==========================================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS knowledge_relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_a_id INTEGER NOT NULL,
            entity_b_id INTEGER NOT NULL,
            relationship_type TEXT,
            -- e.g., "related_to", "part_of", "enables", "requires"
            strength REAL DEFAULT 1.0,
            -- How strong is this connection? (0.0 to 10.0)
            co_occurrence_count INTEGER DEFAULT 1,
            -- How many times mentioned together?
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (entity_a_id) REFERENCES knowledge_entities(id),
            FOREIGN KEY (entity_b_id) REFERENCES knowledge_entities(id),
            UNIQUE(entity_a_id, entity_b_id, relationship_type)
        )
    ''')

    # ==========================================================================
    # KNOWLEDGE DOMAIN MAPPING - Connect concepts to domains
    # ==========================================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS knowledge_domain_mapping (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_id INTEGER NOT NULL,
            domain_name TEXT NOT NULL,
            -- calriven, deathtodata, soulfra, howtocookathome
            relevance_score REAL DEFAULT 1.0,
            -- How relevant is this entity to this domain?
            context TEXT,
            -- Why does this entity belong to this domain?
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (entity_id) REFERENCES knowledge_entities(id),
            UNIQUE(entity_id, domain_name)
        )
    ''')

    # ==========================================================================
    # KNOWLEDGE USER PROFILE - Overall user patterns
    # ==========================================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS knowledge_user_profile (
            user_id INTEGER PRIMARY KEY,
            primary_interests TEXT,
            -- JSON array of top topics
            favorite_domains TEXT,
            -- JSON array: ["calriven", "deathtodata"]
            question_patterns TEXT,
            -- JSON: Common question types user asks
            conversation_style TEXT,
            -- technical, casual, exploratory, etc.
            learning_trajectory TEXT,
            -- JSON: How interests evolved over time
            total_conversations INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # ==========================================================================
    # KNOWLEDGE EXTRACTION LOG - Track what was extracted
    # ==========================================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS knowledge_extraction_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            message_id INTEGER,
            entities_extracted INTEGER DEFAULT 0,
            topics_identified INTEGER DEFAULT 0,
            relationships_added INTEGER DEFAULT 0,
            extraction_time_ms INTEGER,
            -- How long did extraction take?
            extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES discussion_sessions(id)
        )
    ''')

    # Indexes for performance
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_knowledge_entities_user
        ON knowledge_entities(user_id, relevance_score DESC)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_knowledge_topics_user
        ON knowledge_topics(user_id, interest_level DESC)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_knowledge_relationships_entities
        ON knowledge_relationships(entity_a_id, entity_b_id)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_knowledge_domain_mapping_entity
        ON knowledge_domain_mapping(entity_id, relevance_score DESC)
    ''')

    conn.commit()
    conn.close()

    print("✅ Knowledge Graph tables created successfully")


def seed_example_domains():
    """Seed the four core domains"""

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    domains = [
        {
            'name': 'calriven',
            'description': 'Technical architecture, algorithms, system design',
            'keywords': ['architecture', 'algorithms', 'scalability', 'performance', 'design-patterns']
        },
        {
            'name': 'deathtodata',
            'description': 'Privacy, anti-tracking, decentralization',
            'keywords': ['privacy', 'tracking', 'surveillance', 'decentralization', 'data-minimization']
        },
        {
            'name': 'soulfra',
            'description': 'Security, encryption, authentication',
            'keywords': ['security', 'encryption', 'cryptography', 'authentication', 'access-control']
        },
        {
            'name': 'howtocookathome',
            'description': 'Cooking, recipes, food preparation',
            'keywords': ['cooking', 'recipes', 'ingredients', 'techniques', 'kitchen']
        }
    ]

    # These will be used as context during knowledge extraction

    print("✅ Domain context ready for knowledge extraction")
    print("")
    print("Domains:")
    for d in domains:
        print(f"  - {d['name']}: {d['description']}")

    conn.close()


if __name__ == '__main__':
    print("Initializing Knowledge Graph...")
    print("")

    init_knowledge_graph_tables()
    seed_example_domains()

    print("")
    print("🧠 Knowledge Graph ready!")
    print("")
    print("How it works:")
    print("  1. User chats with AI")
    print("  2. After response, background extractor analyzes conversation")
    print("  3. Extracts entities, topics, relationships")
    print("  4. Maps to domains (CalRiven, DeathToData, Soulfra, HowToCookAtHome)")
    print("  5. Builds weighted graph of user interests")
    print("  6. Future queries enriched with this context")
    print("")
    print("Invisible to user. Just works.")
