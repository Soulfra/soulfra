#!/usr/bin/env python3
"""
QR + Learning Integration Demo
================================

Shows how to use QR codes with the learning system:
1. Create collaborative review sessions
2. Share flashcard decks via QR
3. Join practice rooms for group study

Usage:
    python3 qr_learning_session.py
"""

import sqlite3
import qrcode
import hashlib
import secrets
from datetime import datetime, timedelta
from database import get_db


class QRLearningIntegration:
    """Integrate QR codes with learning system"""

    def __init__(self):
        self.db = get_db()
        self.base_url = 'http://localhost:5001'

    def create_collaborative_session(self, topic, cards_limit=20, duration_minutes=60):
        """
        Create a collaborative review session accessible via QR code

        Args:
            topic: Session topic/title
            cards_limit: Number of cards to review
            duration_minutes: Session duration

        Returns:
            dict with session_id, qr_url, qr_image_path
        """
        # Create practice room
        room_id = secrets.token_urlsafe(16)
        expires_at = (datetime.now() + timedelta(minutes=duration_minutes)).isoformat()

        # Insert room
        self.db.execute('''
            INSERT INTO practice_rooms
            (room_id, topic, created_by_user_id, max_participants, expires_at, status)
            VALUES (?, ?, ?, ?, ?, 'active')
        ''', (room_id, topic, 1, 10, expires_at))

        # Link learning cards to room
        cards = self.db.execute('''
            SELECT id FROM learning_cards
            ORDER BY difficulty_predicted DESC
            LIMIT ?
        ''', (cards_limit,)).fetchall()

        for card in cards:
            self.db.execute('''
                INSERT INTO room_cards (room_id, card_id)
                VALUES (?, ?)
            ''', (room_id, card['id']))

        self.db.commit()

        # Generate QR code
        join_url = f"{self.base_url}/practice/room/{room_id}"
        qr_image_path = f"static/qr_codes/session_{room_id}.png"

        # Create QR image
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(join_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img.save(qr_image_path)

        print(f"✅ Created collaborative session!")
        print(f"   Topic: {topic}")
        print(f"   Room ID: {room_id}")
        print(f"   Cards: {len(cards)}")
        print(f"   Expires: {expires_at}")
        print(f"   Join URL: {join_url}")
        print(f"   QR Code: {qr_image_path}")
        print()
        print("📱 Scan QR code with phone → Join session → Review together!")

        return {
            'room_id': room_id,
            'join_url': join_url,
            'qr_image_path': qr_image_path,
            'cards_count': len(cards),
            'expires_at': expires_at
        }

    def share_deck_qr(self, deck_name, topic_filter=None):
        """
        Create QR code to share a flashcard deck

        Args:
            deck_name: Name of deck
            topic_filter: Optional topic filter

        Returns:
            dict with deck_url, qr_url
        """
        # Get cards for deck
        if topic_filter:
            cards = self.db.execute('''
                SELECT * FROM learning_cards
                WHERE topic = ?
            ''', (topic_filter,)).fetchall()
        else:
            cards = self.db.execute('SELECT * FROM learning_cards').fetchall()

        # Create deck shareable link
        deck_hash = hashlib.sha256(deck_name.encode()).hexdigest()[:16]
        share_url = f"{self.base_url}/learn/import/deck/{deck_hash}"

        # Store deck metadata
        self.db.execute('''
            CREATE TABLE IF NOT EXISTS shared_decks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deck_hash TEXT UNIQUE,
                deck_name TEXT,
                topic_filter TEXT,
                card_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self.db.execute('''
            INSERT OR REPLACE INTO shared_decks
            (deck_hash, deck_name, topic_filter, card_count)
            VALUES (?, ?, ?, ?)
        ''', (deck_hash, deck_name, topic_filter, len(cards)))

        self.db.commit()

        # Generate QR
        qr_image_path = f"static/qr_codes/deck_{deck_hash}.png"

        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(share_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="indigo", back_color="white")
        img.save(qr_image_path)

        print(f"✅ Created shareable deck!")
        print(f"   Name: {deck_name}")
        print(f"   Cards: {len(cards)}")
        print(f"   Share URL: {share_url}")
        print(f"   QR Code: {qr_image_path}")
        print()
        print("📱 Others scan QR → Get copy of your deck → Start learning!")

        return {
            'deck_hash': deck_hash,
            'share_url': share_url,
            'qr_image_path': qr_image_path,
            'card_count': len(cards)
        }

    def join_session_via_qr(self, room_id, user_id=1):
        """
        Simulate joining a session via QR code

        Args:
            room_id: Practice room ID
            user_id: User joining

        Returns:
            dict with session info
        """
        # Get room
        room = self.db.execute('''
            SELECT * FROM practice_rooms WHERE room_id = ?
        ''', (room_id,)).fetchone()

        if not room:
            print(f"❌ Room {room_id} not found!")
            return None

        # Check if expired
        if room['expires_at'] and datetime.fromisoformat(room['expires_at']) < datetime.now():
            print(f"❌ Room {room_id} has expired!")
            return None

        # Add user to room
        self.db.execute('''
            CREATE TABLE IF NOT EXISTS room_participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id TEXT,
                user_id INTEGER,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(room_id, user_id)
            )
        ''')

        self.db.execute('''
            INSERT OR IGNORE INTO room_participants (room_id, user_id)
            VALUES (?, ?)
        ''', (room_id, user_id))

        # Get room cards
        cards = self.db.execute('''
            SELECT c.* FROM learning_cards c
            JOIN room_cards rc ON c.id = rc.card_id
            WHERE rc.room_id = ?
        ''', (room_id,)).fetchall()

        self.db.commit()

        # Get participant count
        participants = self.db.execute('''
            SELECT COUNT(*) as count FROM room_participants
            WHERE room_id = ?
        ''', (room_id,)).fetchone()

        print(f"✅ Joined session!")
        print(f"   Topic: {room['topic']}")
        print(f"   Cards: {len(cards)}")
        print(f"   Participants: {participants['count']}")
        print(f"   Status: {room['status']}")
        print()
        print("🎓 Ready to learn together!")

        return {
            'room': dict(room),
            'cards': [dict(c) for c in cards],
            'participant_count': participants['count']
        }

    def demo_qr_to_learning_flow(self):
        """Run complete QR → Learning integration demo"""
        print("=" * 70)
        print("  QR + LEARNING INTEGRATION DEMO")
        print("=" * 70)
        print()

        # Demo 1: Create collaborative session
        print("DEMO 1: Create Collaborative Review Session")
        print("-" * 70)

        session = self.create_collaborative_session(
            topic="Python & SQLite Study Group",
            cards_limit=10,
            duration_minutes=90
        )

        print()
        input("Press Enter to continue...")
        print()

        # Demo 2: Share deck via QR
        print("DEMO 2: Share Flashcard Deck via QR")
        print("-" * 70)

        deck = self.share_deck_qr(
            deck_name="SQLite Basics",
            topic_filter="tutorial"
        )

        print()
        input("Press Enter to continue...")
        print()

        # Demo 3: Join session via QR
        print("DEMO 3: Join Session (Simulating QR Scan)")
        print("-" * 70)

        joined = self.join_session_via_qr(session['room_id'], user_id=2)

        print()

        # Demo 4: Show QR integration points
        print("=" * 70)
        print("  QR INTEGRATION POINTS")
        print("=" * 70)
        print()

        print("1. Practice Room QR:")
        print(f"   URL: {session['join_url']}")
        print(f"   Scan → Join collaborative session")
        print()

        print("2. Deck Share QR:")
        print(f"   URL: {deck['share_url']}")
        print(f"   Scan → Import flashcards to your account")
        print()

        print("3. User Business Card QR:")
        print(f"   URL: {self.base_url}/user/admin/qr-card")
        print(f"   Scan → View profile + shared decks")
        print()

        print("=" * 70)
        print("  WHAT YOU CAN DO NOW")
        print("=" * 70)
        print()

        print("📱 Test on Mobile:")
        print(f"   1. Find your IP: ifconfig | grep inet")
        print(f"   2. Start Flask with host='0.0.0.0'")
        print(f"   3. Visit practice room on phone")
        print(f"   4. Scan QR codes with camera")
        print()

        print("🔗 Integration Examples:")
        print(f"   - Collaborative study sessions (scan → join)")
        print(f"   - Deck sharing (scan → copy cards)")
        print(f"   - User profiles (scan → view stats)")
        print(f"   - Game portals (scan → enter game)")
        print()

        print("📂 Files Created:")
        print(f"   - {session['qr_image_path']}")
        print(f"   - {deck['qr_image_path']}")
        print()

        print("✅ Demo complete!")


def create_qr_learning_routes():
    """
    Example Flask routes to add to app.py for QR + Learning integration
    """
    code = '''
# Add these routes to app.py

@app.route('/practice/room/<room_id>')
def join_practice_room(room_id):
    """Join practice room via QR scan"""
    user_id = session.get('user_id', 1)

    # Get room
    room = db.execute('SELECT * FROM practice_rooms WHERE room_id = ?', (room_id,)).fetchone()

    if not room:
        return "Room not found", 404

    # Add user to participants
    db.execute('''
        INSERT OR IGNORE INTO room_participants (room_id, user_id)
        VALUES (?, ?)
    ''', (room_id, user_id))
    db.commit()

    # Get room cards
    cards = db.execute('''
        SELECT c.* FROM learning_cards c
        JOIN room_cards rc ON c.id = rc.card_id
        WHERE rc.room_id = ?
    ''', (room_id,)).fetchall()

    # Start review session with room cards
    return render_template('practice/room.html',
                         room=room,
                         cards=cards)


@app.route('/learn/import/deck/<deck_hash>')
def import_deck(deck_hash):
    """Import shared deck via QR scan"""
    user_id = session.get('user_id', 1)

    # Get deck metadata
    deck = db.execute('SELECT * FROM shared_decks WHERE deck_hash = ?', (deck_hash,)).fetchone()

    if not deck:
        return "Deck not found", 404

    # Get cards
    if deck['topic_filter']:
        cards = db.execute('SELECT * FROM learning_cards WHERE topic = ?', (deck['topic_filter'],)).fetchall()
    else:
        cards = db.execute('SELECT * FROM learning_cards').fetchall()

    # Initialize cards for user
    for card in cards:
        db.execute('''
            INSERT OR IGNORE INTO learning_progress
            (card_id, user_id, repetitions, ease_factor, interval_days, next_review, status)
            VALUES (?, ?, 0, 2.5, 0, datetime('now'), 'new')
        ''', (card['id'], user_id))

    db.commit()

    flash(f"Imported {len(cards)} cards from '{deck['deck_name']}'!", 'success')
    return redirect(url_for('learn_dashboard'))


@app.route('/user/<username>/qr-card')
def user_qr_card(username):
    """User business card with QR code"""
    user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

    if not user:
        return "User not found", 404

    # Get user's shared decks
    decks = db.execute('''
        SELECT sd.* FROM shared_decks sd
        JOIN users u ON sd.created_by = u.id
        WHERE u.username = ?
    ''', (username,)).fetchall()

    # Generate QR for profile
    qr_url = f"{request.host_url}user/{username}/qr-card"

    return render_template('user/qr_card.html',
                         user=user,
                         decks=decks,
                         qr_url=qr_url)
'''

    print(code)


def main():
    """Run QR + Learning integration demo"""
    demo = QRLearningIntegration()
    demo.demo_qr_to_learning_flow()

    print()
    print("=" * 70)
    print("  FLASK ROUTES TO ADD")
    print("=" * 70)
    print()
    print("Copy these routes to app.py:")
    print()
    create_qr_learning_routes()


if __name__ == '__main__':
    main()
