#!/usr/bin/env python3
"""
Voice Identity Time Capsule System - Database Initialization

This creates the database schema for voice-based identity time capsules:
- Users answer rotating questions via voice
- Transcriptions stored (audio deleted for privacy)
- Yearly "identity snapshots" generated
- Different domains (CalRiven, DeathToData, etc) ask different questions
"""

import sqlite3
from datetime import datetime


def init_voice_capsule_tables():
    """Initialize all tables for voice time capsule system"""

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    # ==========================================================================
    # VOICE QUESTIONS - Pool of questions that can be asked
    # ==========================================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS voice_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_text TEXT NOT NULL,
            domain TEXT NOT NULL,
            category TEXT,
            rotation_period TEXT DEFAULT 'monthly',
            rotation_order INTEGER,
            vibe TEXT,
            expected_duration_seconds INTEGER DEFAULT 90,
            follow_up_prompts TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            active BOOLEAN DEFAULT 1
        )
    ''')

    # ==========================================================================
    # VOICE RESPONSES - User answers to questions
    # ==========================================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS voice_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            transcription TEXT NOT NULL,
            sentiment REAL,
            key_themes TEXT,
            word_count INTEGER,
            duration_seconds INTEGER,
            emotion_detected TEXT,
            answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            year INTEGER,
            month INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (question_id) REFERENCES voice_questions(id)
        )
    ''')

    # ==========================================================================
    # VOICE IDENTITIES - Yearly snapshots of user identity
    # ==========================================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS voice_identities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            domain TEXT NOT NULL,
            year INTEGER NOT NULL,
            total_responses INTEGER DEFAULT 0,
            avg_sentiment REAL,
            top_themes TEXT,
            most_used_words TEXT,
            emotional_arc TEXT,
            growth_insights TEXT,
            capsule_data TEXT,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, domain, year)
        )
    ''')

    # ==========================================================================
    # DOMAIN QUESTION ROTATIONS - Which questions belong to which domains
    # ==========================================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS domain_question_rotations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT NOT NULL,
            question_id INTEGER NOT NULL,
            start_date DATE,
            end_date DATE,
            rotation_position INTEGER,
            priority INTEGER DEFAULT 0,
            FOREIGN KEY (question_id) REFERENCES voice_questions(id)
        )
    ''')

    # ==========================================================================
    # USER QUESTION SCHEDULE - Track which user gets which question when
    # ==========================================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_question_schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            domain TEXT NOT NULL,
            question_id INTEGER NOT NULL,
            scheduled_for DATE,
            asked_at TIMESTAMP,
            answered_at TIMESTAMP,
            skipped BOOLEAN DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (question_id) REFERENCES voice_questions(id)
        )
    ''')

    conn.commit()
    conn.close()

    print("✅ Voice time capsule tables created successfully")


def seed_example_questions():
    """Seed database with example questions for each domain"""

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    # CalRiven - Philosophy of Ownership Questions
    calriven_questions = [
        ("What do you own that you wish you didn't?", "ownership", 1, "thoughtful"),
        ("What owns you that you don't control?", "control", 2, "introspective"),
        ("What would you give away tomorrow if you could?", "generosity", 3, "contemplative"),
        ("What possession defines you most?", "identity", 4, "reflective"),
        ("What do you own that nobody knows about?", "secrets", 5, "honest"),
        ("If you lost everything, what would you rebuild first?", "priorities", 6, "revealing"),
        ("What relationship do you own vs what owns you?", "relationships", 7, "vulnerable"),
        ("What skill do you own that can't be taken away?", "capability", 8, "confident"),
        ("What memory do you own that shaped who you are?", "nostalgia", 9, "emotional"),
        ("What truth do you own that others deny?", "wisdom", 10, "bold"),
        ("What fear owns your decisions?", "fear", 11, "raw"),
        ("What dream do you own that feels impossible?", "hope", 12, "aspirational")
    ]

    for question_text, category, order, vibe in calriven_questions:
        cursor.execute('''
            INSERT INTO voice_questions
            (question_text, domain, category, rotation_period, rotation_order, vibe, expected_duration_seconds)
            VALUES (?, 'calriven', ?, 'monthly', ?, ?, 90)
        ''', (question_text, category, order, vibe))

    # DeathToData - Privacy/Autonomy Questions
    deathtodata_questions = [
        ("What data do they have on you that you wish they didn't?", "privacy", 1, "defensive"),
        ("When did you last choose convenience over privacy?", "tradeoffs", 2, "honest"),
        ("What would you do if all your data was deleted tomorrow?", "freedom", 3, "liberating"),
        ("Who profits from knowing your habits?", "exploitation", 4, "angry"),
        ("What do you hide from algorithms?", "resistance", 5, "secretive"),
        ("When did surveillance become normal to you?", "awareness", 6, "awakening"),
        ("What digital ghost will outlive you?", "legacy", 7, "haunting"),
        ("How much of you is real vs performative online?", "authenticity", 8, "vulnerable"),
        ("What corporation knows you better than your friends?", "intimacy", 9, "disturbing"),
        ("When will you stop being the product?", "agency", 10, "activating"),
        ("What freedom did you trade for a free account?", "cost", 11, "regretful"),
        ("Who has the right to forget you?", "erasure", 12, "existential")
    ]

    for question_text, category, order, vibe in deathtodata_questions:
        cursor.execute('''
            INSERT INTO voice_questions
            (question_text, domain, category, rotation_period, rotation_order, vibe, expected_duration_seconds)
            VALUES (?, 'deathtodata', ?, 'monthly', ?, ?, 90)
        ''', (question_text, category, order, vibe))

    # Cooking Blog - Food/Memory Questions
    cooking_questions = [
        ("What meal made you happiest this week?", "joy", 1, "warm"),
        ("What recipe reminds you of home?", "nostalgia", 2, "comforting"),
        ("What cooking mistake taught you the most?", "growth", 3, "humble"),
        ("What dish would you cook for your younger self?", "care", 4, "nurturing"),
        ("What food brings your family together?", "connection", 5, "loving"),
        ("What ingredient changed how you cook?", "discovery", 6, "excited"),
        ("What meal tells your story?", "identity", 7, "personal"),
        ("What kitchen disaster are you proud of?", "resilience", 8, "funny"),
        ("What food makes you feel most alive?", "vitality", 9, "energetic"),
        ("What recipe are you still learning?", "patience", 10, "persistent"),
        ("What did someone cook that changed your life?", "gratitude", 11, "thankful"),
        ("What will you cook when you're 80?", "legacy", 12, "hopeful")
    ]

    for question_text, category, order, vibe in cooking_questions:
        cursor.execute('''
            INSERT INTO voice_questions
            (question_text, domain, category, rotation_period, rotation_order, vibe, expected_duration_seconds)
            VALUES (?, 'howtocookathome', ?, 'weekly', ?, ?, 60)
        ''', (question_text, category, order, vibe))

    # Soulfra - Meta/Creation Questions
    soulfra_questions = [
        ("What are you building that might outlive you?", "legacy", 1, "ambitious"),
        ("What pattern do you keep repeating?", "awareness", 2, "introspective"),
        ("What experiment are you running on yourself?", "growth", 3, "curious"),
        ("What truth did you discover this month?", "insight", 4, "wise"),
        ("What are you automating that should stay human?", "humanity", 5, "cautious"),
        ("What system did you break free from?", "liberation", 6, "rebellious"),
        ("What are you creating vs what's creating you?", "agency", 7, "philosophical"),
        ("What skill are you compounding?", "progress", 8, "focused"),
        ("What paradox are you living in?", "contradiction", 9, "complex"),
        ("What would future you thank you for?", "foresight", 10, "optimistic"),
        ("What system needs to die?", "destruction", 11, "radical"),
        ("What are you becoming?", "transformation", 12, "evolving")
    ]

    for question_text, category, order, vibe in soulfra_questions:
        cursor.execute('''
            INSERT INTO voice_questions
            (question_text, domain, category, rotation_period, rotation_order, vibe, expected_duration_seconds)
            VALUES (?, 'soulfra', ?, 'monthly', ?, ?, 120)
        ''', (question_text, category, order, vibe))

    conn.commit()
    conn.close()

    print("✅ Seeded 48 example questions across 4 domains")
    print("   - CalRiven: 12 ownership questions (monthly)")
    print("   - DeathToData: 12 privacy questions (monthly)")
    print("   - HowToCookAtHome: 12 food questions (weekly)")
    print("   - Soulfra: 12 meta questions (monthly)")


if __name__ == '__main__':
    print("Initializing Voice Identity Time Capsule System...")
    print("")

    init_voice_capsule_tables()
    seed_example_questions()

    print("")
    print("🎉 Voice Time Capsule system ready!")
    print("")
    print("Next steps:")
    print("1. Users scan QR code from domain")
    print("2. Get question based on signup date + rotation")
    print("3. Voice answer (transcribed, audio deleted)")
    print("4. End of year: Identity capsule generated")
