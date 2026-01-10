#!/usr/bin/env python3
"""
Narrative Cringeproof - Story-Driven Game Engine

Manages narrative gameplay sessions where users progress through story chapters,
answer questions, and receive personalized feedback from AI Host.

Architecture:
- Cringeproof = the game mechanic (questions + ratings + progressive story)
- Brands = editions/skins (Soulfra = dark mystery, CalRiven = technical, etc.)
- Each brand has its own story content and visual theme
- AI Host provides narration and adapts to player choices

Usage:
    from narrative_cringeproof import NarrativeSession

    session = NarrativeSession(user_id=1, brand_slug='soulfra')
    session.start_game()
    session.answer_question(question_id=1, rating=4)
    session.advance_chapter()
"""

import json
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional
from database import get_db


class NarrativeSession:
    """Manages a single player's narrative game session"""

    def __init__(self, user_id: int, brand_slug: str, session_id: int = None):
        """
        Initialize or resume a narrative session

        Args:
            user_id: Player's user ID
            brand_slug: Brand edition (e.g., 'soulfra', 'calriven')
            session_id: Resume existing session (or create new if None)
        """
        self.user_id = user_id
        self.brand_slug = brand_slug

        if session_id:
            self.session_id = session_id
            self._load_session()
        else:
            self.session_id = self._create_session()

    def _create_session(self) -> int:
        """Create new narrative game session"""
        db = get_db()

        # Get brand ID
        brand = db.execute('SELECT id FROM brands WHERE slug = ?', (self.brand_slug,)).fetchone()
        if not brand:
            db.close()
            raise ValueError(f"Brand '{self.brand_slug}' not found")

        brand_id = brand['id']

        # Create session
        cursor = db.execute('''
            INSERT INTO narrative_sessions (
                user_id,
                brand_id,
                current_chapter,
                game_state,
                status,
                created_at
            ) VALUES (?, ?, ?, ?, 'active', CURRENT_TIMESTAMP)
        ''', (self.user_id, brand_id, 1, json.dumps({
            'answers': {},
            'chapter_completion': {},
            'total_score': 0
        })))

        session_id = cursor.lastrowid
        db.commit()
        db.close()

        return session_id

    def _load_session(self):
        """Load existing session"""
        db = get_db()
        session = db.execute('''
            SELECT * FROM narrative_sessions WHERE id = ?
        ''', (self.session_id,)).fetchone()
        db.close()

        if session:
            self.user_id = session['user_id']
            brand = db.execute('SELECT slug FROM brands WHERE id = ?', (session['brand_id'],)).fetchone()
            self.brand_slug = brand['slug'] if brand else 'soulfra'

    def get_brand_info(self) -> Dict[str, Any]:
        """Get brand configuration"""
        db = get_db()
        brand_row = db.execute('''
            SELECT * FROM brands WHERE slug = ?
        ''', (self.brand_slug,)).fetchone()
        db.close()

        if brand_row:
            # Convert sqlite3.Row to dict
            brand = dict(brand_row)

            # Support both old schema (separate columns) and new schema (config_json)
            config = {}
            if 'config_json' in brand.keys() and brand['config_json']:
                config = json.loads(brand['config_json'])
            elif 'color_primary' in brand.keys():
                # Build config from existing columns
                config = {
                    'colors': {
                        'primary': brand.get('color_primary', '#667eea'),
                        'secondary': brand.get('color_secondary', '#764ba2'),
                        'accent': brand.get('color_accent', '#f093fb')
                    }
                }

            return {
                'id': brand['id'],
                'name': brand['name'],
                'slug': brand['slug'],
                'personality': brand.get('personality_tone', 'Mysterious'),
                'traits': brand.get('personality_traits', 'Unknown'),
                'config': config
            }
        return {}

    def get_story_chapters(self) -> List[Dict[str, Any]]:
        """Get all story chapters for this brand"""
        db = get_db()
        brand_info = self.get_brand_info()

        posts = db.execute('''
            SELECT id, title, slug, content, published_at
            FROM posts
            WHERE brand_id = ?
            ORDER BY published_at ASC
        ''', (brand_info['id'],)).fetchall()
        db.close()

        # Import story structure if available
        if self.brand_slug == 'soulfra':
            from soulfra_dark_story import STORY_CHAPTERS
            return STORY_CHAPTERS

        # Otherwise parse from posts
        chapters = []
        for i, post in enumerate(posts, 1):
            chapters.append({
                'chapter_number': i,
                'title': post['title'],
                'slug': post['slug'],
                'content': post['content'],
                'questions': [],  # Would be populated from separate table
                'ai_host_narration': ''
            })

        return chapters

    def get_current_chapter(self) -> Optional[Dict[str, Any]]:
        """Get the current chapter player is on"""
        db = get_db()
        session = db.execute('''
            SELECT current_chapter FROM narrative_sessions WHERE id = ?
        ''', (self.session_id,)).fetchone()
        db.close()

        if not session:
            return None

        chapters = self.get_story_chapters()
        current_chapter_num = session['current_chapter']

        if current_chapter_num <= len(chapters):
            return chapters[current_chapter_num - 1]

        return None

    def get_game_state(self) -> Dict[str, Any]:
        """Get current game state"""
        db = get_db()
        session_row = db.execute('''
            SELECT * FROM narrative_sessions WHERE id = ?
        ''', (self.session_id,)).fetchone()
        db.close()

        if session_row:
            # Convert sqlite3.Row to dict
            session = dict(session_row)

            game_state = json.loads(session['game_state']) if session['game_state'] else {}
            return {
                'session_id': session['id'],
                'current_chapter': session['current_chapter'],
                'status': session['status'],
                'state': game_state,
                'created_at': session['created_at'],
                'completed_at': session.get('completed_at')
            }

        return {}

    def answer_question(self, question_id: int, rating: int) -> Dict[str, Any]:
        """
        Record player's answer to a question

        Args:
            question_id: Question identifier
            rating: Player's rating (1-5)

        Returns:
            Answer record with AI feedback
        """
        db = get_db()

        # Get current game state
        session = db.execute('''
            SELECT game_state FROM narrative_sessions WHERE id = ?
        ''', (self.session_id,)).fetchone()

        game_state = json.loads(session['game_state']) if session else {}

        # Record answer
        game_state['answers'][str(question_id)] = {
            'rating': rating,
            'answered_at': datetime.now().isoformat()
        }

        # Update session
        db.execute('''
            UPDATE narrative_sessions
            SET game_state = ?
            WHERE id = ?
        ''', (json.dumps(game_state), self.session_id))

        db.commit()
        db.close()

        return {
            'question_id': question_id,
            'rating': rating,
            'recorded': True
        }

    def advance_chapter(self) -> Dict[str, Any]:
        """
        Move to next chapter

        Returns:
            Next chapter info or completion status
        """
        db = get_db()

        session = db.execute('''
            SELECT current_chapter, game_state FROM narrative_sessions WHERE id = ?
        ''', (self.session_id,)).fetchone()

        if not session:
            db.close()
            return {'error': 'Session not found'}

        current_chapter = session['current_chapter']
        game_state = json.loads(session['game_state']) if session['game_state'] else {}

        # Mark current chapter complete
        game_state['chapter_completion'][str(current_chapter)] = {
            'completed_at': datetime.now().isoformat()
        }

        # Get total chapters
        chapters = self.get_story_chapters()
        total_chapters = len(chapters)

        # Check if game is complete
        if current_chapter >= total_chapters:
            db.execute('''
                UPDATE narrative_sessions
                SET status = 'completed',
                    game_state = ?,
                    completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (json.dumps(game_state), self.session_id))
            db.commit()
            db.close()

            return {
                'game_complete': True,
                'total_chapters': total_chapters
            }

        # Advance to next chapter
        next_chapter = current_chapter + 1
        db.execute('''
            UPDATE narrative_sessions
            SET current_chapter = ?,
                game_state = ?
            WHERE id = ?
        ''', (next_chapter, json.dumps(game_state), self.session_id))

        db.commit()
        db.close()

        return {
            'game_complete': False,
            'next_chapter': next_chapter,
            'total_chapters': total_chapters
        }

    def get_progress_summary(self) -> Dict[str, Any]:
        """Get player's progress summary"""
        game_state = self.get_game_state()
        chapters = self.get_story_chapters()

        answers = game_state['state'].get('answers', {})
        completed_chapters = game_state['state'].get('chapter_completion', {})

        return {
            'session_id': self.session_id,
            'brand': self.brand_slug,
            'current_chapter': game_state['current_chapter'],
            'total_chapters': len(chapters),
            'chapters_completed': len(completed_chapters),
            'questions_answered': len(answers),
            'status': game_state['status'],
            'progress_percent': (len(completed_chapters) / len(chapters) * 100) if chapters else 0
        }


# =============================================================================
# Database Schema
# =============================================================================

def init_narrative_tables():
    """Initialize narrative game tables"""
    db = get_db()

    db.execute('''
        CREATE TABLE IF NOT EXISTS narrative_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            brand_id INTEGER NOT NULL,
            current_chapter INTEGER DEFAULT 1,
            game_state TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (brand_id) REFERENCES brands(id)
        )
    ''')

    db.commit()
    db.close()
    print("✅ Narrative tables initialized")


if __name__ == '__main__':
    print("🎮 Narrative Cringeproof - Story-Driven Game Engine")
    print("=" * 70)

    # Initialize tables
    init_narrative_tables()

    # Test session
    print("\n🧪 Testing game session...")

    try:
        session = NarrativeSession(user_id=1, brand_slug='soulfra')
        print(f"✅ Created session {session.session_id}")

        # Get brand info
        brand = session.get_brand_info()
        print(f"✅ Brand: {brand.get('name', 'Unknown')}")

        # Get story chapters
        chapters = session.get_story_chapters()
        print(f"✅ Story has {len(chapters)} chapters")

        # Get current chapter
        current = session.get_current_chapter()
        if current:
            print(f"✅ Current chapter: {current['title']}")

        # Get progress
        progress = session.get_progress_summary()
        print(f"✅ Progress: {progress['progress_percent']:.0f}%")

        print("\n" + "=" * 70)
        print("✅ All tests passed!")

    except Exception as e:
        print(f"❌ Error: {e}")
