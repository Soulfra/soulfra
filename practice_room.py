#!/usr/bin/env python3
"""
Practice Rooms - QR + Voice + ASCII + Chat Integration

Create practice rooms that combine:
- QR codes to join (image + ASCII art for terminal)
- Voice transcription (record → auto-transcribe)
- ASCII visualizations (terminal-friendly)
- Chat widget integration

Use Cases:
1. Coding practice: Create room, share QR, collaborate
2. Language learning: Practice pronunciation with transcription
3. Study groups: Join via QR, record notes, chat
4. Remote pair programming: Terminal + voice + chat

Usage:
    from practice_room import create_practice_room, join_room

    # Create room
    room = create_practice_room('python-basics')

    # Join room (via QR scan or direct)
    join_room(room_id, user_id)

    # Record voice in room
    record_voice(room_id, audio_file)

Flow:
    1. Create room: /practice/python-basics
    2. Generate QR code
    3. Display as:
       - Image QR (for phone scanning)
       - ASCII QR (for terminal display)
    4. Users scan → Join room
    5. Record voice → Auto-transcribe
    6. Chat via widget
    7. See ASCII visualizations
"""

import secrets
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from database import get_db


def create_practice_room(topic: str, creator_id: Optional[int] = None,
                        max_participants: int = 10,
                        duration_minutes: int = 60) -> Dict:
    """
    Create practice room with QR + voice + ASCII

    Args:
        topic: Room topic (e.g., "python-basics")
        creator_id: User ID of creator
        max_participants: Max number of participants
        duration_minutes: Room duration

    Returns:
        Dict with room data including QR codes
    """
    from qr_faucet import generate_qr_payload

    # Generate room ID
    room_id = secrets.token_hex(8)

    # Calculate expiration
    expires_at = datetime.now() + timedelta(minutes=duration_minutes)

    # Initialize database
    db = get_db()

    # Create practice_rooms table if needed
    db.execute('''
        CREATE TABLE IF NOT EXISTS practice_rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id TEXT UNIQUE NOT NULL,
            topic TEXT NOT NULL,
            creator_id INTEGER,
            max_participants INTEGER DEFAULT 10,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            status TEXT DEFAULT 'active',
            qr_code TEXT,
            qr_ascii TEXT,
            voice_enabled BOOLEAN DEFAULT 1,
            chat_enabled BOOLEAN DEFAULT 1,
            FOREIGN KEY (creator_id) REFERENCES users(id)
        )
    ''')

    # Generate QR code for joining
    qr_payload = generate_qr_payload(
        'practice_room',
        {
            'room_id': room_id,
            'topic': topic,
            'action': 'join'
        },
        ttl_seconds=duration_minutes * 60
    )

    qr_url = f"/qr/faucet/{qr_payload}"

    # Generate ASCII QR code (for terminal display)
    try:
        from qr_to_ascii import qr_to_ascii
        full_url = f"http://localhost:5001{qr_url}"
        qr_ascii = qr_to_ascii(full_url)
    except:
        qr_ascii = None

    # Insert room
    cursor = db.execute('''
        INSERT INTO practice_rooms (
            room_id, topic, creator_id, max_participants,
            expires_at, qr_code, qr_ascii, voice_enabled, chat_enabled
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, 1)
    ''', (
        room_id,
        topic,
        creator_id,
        max_participants,
        expires_at,
        qr_payload,
        qr_ascii
    ))

    db.commit()

    # Return room data
    room_data = {
        'room_id': room_id,
        'topic': topic,
        'qr_code': qr_payload,
        'qr_url': qr_url,
        'qr_ascii': qr_ascii,
        'full_url': f"http://localhost:5001/practice/room/{room_id}",
        'join_url': f"/practice/room/{room_id}",
        'expires_at': expires_at.isoformat(),
        'max_participants': max_participants,
        'voice_enabled': True,
        'chat_enabled': True,
        'features': [
            'QR Code (Image)',
            'QR Code (ASCII Terminal)',
            'Voice Transcription',
            'Chat Widget',
            'ASCII Visualizations'
        ]
    }

    print(f"✓ Created practice room: {topic}")
    print(f"  Room ID: {room_id}")
    print(f"  Join URL: {room_data['join_url']}")
    print(f"  Expires: {expires_at}")

    return room_data


def join_room(room_id: str, user_id: Optional[int] = None,
              username: Optional[str] = None) -> Dict:
    """
    Join practice room

    Args:
        room_id: Room ID
        user_id: User ID (if logged in)
        username: Username (if not logged in)

    Returns:
        Join result
    """
    db = get_db()

    # Check if room exists and is active
    room = db.execute('''
        SELECT * FROM practice_rooms
        WHERE room_id = ? AND status = 'active'
    ''', (room_id,)).fetchone()

    if not room:
        return {'success': False, 'error': 'Room not found or expired'}

    # Check expiration
    if room['expires_at']:
        expires = datetime.fromisoformat(room['expires_at'])
        if datetime.now() > expires:
            return {'success': False, 'error': 'Room expired'}

    # Check participant limit
    participant_count = db.execute('''
        SELECT COUNT(*) as count FROM practice_room_participants
        WHERE room_id = ? AND status = 'active'
    ''', (room_id,)).fetchone()

    if participant_count and participant_count['count'] >= room['max_participants']:
        return {'success': False, 'error': 'Room full'}

    # Create participants table if needed
    db.execute('''
        CREATE TABLE IF NOT EXISTS practice_room_participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id TEXT NOT NULL,
            user_id INTEGER,
            username TEXT,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            left_at TIMESTAMP,
            status TEXT DEFAULT 'active',
            FOREIGN KEY (room_id) REFERENCES practice_rooms(room_id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Add participant
    db.execute('''
        INSERT INTO practice_room_participants (
            room_id, user_id, username, status
        ) VALUES (?, ?, ?, 'active')
    ''', (room_id, user_id, username))

    db.commit()

    print(f"✓ Joined room: {room['topic']}")
    print(f"  User: {username or f'User #{user_id}'}")

    return {
        'success': True,
        'room_id': room_id,
        'topic': room['topic'],
        'voice_enabled': bool(room['voice_enabled']),
        'chat_enabled': bool(room['chat_enabled'])
    }


def record_voice_in_room(room_id: str, audio_file: str,
                        user_id: Optional[int] = None,
                        transcription: Optional[str] = None) -> int:
    """
    Record voice memo in practice room

    Args:
        room_id: Room ID
        audio_file: Path to audio file
        user_id: User ID
        transcription: Optional transcription text

    Returns:
        recording_id: ID of voice recording
    """
    from voice_input import add_audio

    # Add audio to voice_inputs
    audio_id = add_audio(audio_file, source='practice_room', metadata={
        'room_id': room_id,
        'user_id': user_id
    })

    # Link to room
    db = get_db()

    db.execute('''
        CREATE TABLE IF NOT EXISTS practice_room_recordings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id TEXT NOT NULL,
            audio_id INTEGER NOT NULL,
            user_id INTEGER,
            transcription TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (room_id) REFERENCES practice_rooms(room_id),
            FOREIGN KEY (audio_id) REFERENCES voice_inputs(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    cursor = db.execute('''
        INSERT INTO practice_room_recordings (
            room_id, audio_id, user_id, transcription
        ) VALUES (?, ?, ?, ?)
    ''', (room_id, audio_id, user_id, transcription))

    recording_id = cursor.lastrowid
    db.commit()

    print(f"✓ Recorded voice in room {room_id}")
    if transcription:
        print(f"  Transcription: {transcription[:50]}...")

    return recording_id


def get_room_recordings(room_id: str) -> List[Dict]:
    """Get all voice recordings for room"""
    db = get_db()

    recordings = db.execute('''
        SELECT
            r.*,
            v.filename,
            v.file_path,
            v.duration_seconds
        FROM practice_room_recordings r
        LEFT JOIN voice_inputs v ON r.audio_id = v.id
        WHERE r.room_id = ?
        ORDER BY r.created_at DESC
    ''', (room_id,)).fetchall()

    return [dict(r) for r in recordings]


def get_active_rooms() -> List[Dict]:
    """Get all active practice rooms"""
    db = get_db()

    rooms = db.execute('''
        SELECT
            r.*,
            COUNT(DISTINCT p.id) as participant_count
        FROM practice_rooms r
        LEFT JOIN practice_room_participants p
            ON r.room_id = p.room_id AND p.status = 'active'
        WHERE r.status = 'active'
        AND (r.expires_at IS NULL OR r.expires_at > ?)
        GROUP BY r.id
        ORDER BY r.created_at DESC
    ''', (datetime.now().isoformat(),)).fetchall()

    return [dict(r) for r in rooms]


def close_room(room_id: str) -> bool:
    """Close practice room"""
    db = get_db()

    # Update room status
    db.execute('''
        UPDATE practice_rooms
        SET status = 'closed'
        WHERE room_id = ?
    ''', (room_id,))

    # Mark all participants as left
    db.execute('''
        UPDATE practice_room_participants
        SET status = 'left', left_at = ?
        WHERE room_id = ? AND status = 'active'
    ''', (datetime.now(), room_id))

    db.commit()

    print(f"✓ Closed room: {room_id}")
    return True


# CLI for testing
if __name__ == '__main__':
    import sys

    print("Practice Rooms - QR + Voice + ASCII + Chat\n")

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'create' and len(sys.argv) >= 3:
            # Create room
            topic = sys.argv[2]
            duration = int(sys.argv[3]) if len(sys.argv) > 3 else 60

            room = create_practice_room(topic, duration_minutes=duration)

            print(f"\n{'='*60}")
            print("PRACTICE ROOM CREATED")
            print(f"{'='*60}")
            print(f"\nTopic: {room['topic']}")
            print(f"Room ID: {room['room_id']}")
            print(f"\nJoin URL: {room['join_url']}")
            print(f"QR URL: {room['qr_url']}")
            print(f"\nExpires: {room['expires_at']}")
            print(f"Max Participants: {room['max_participants']}")

            print(f"\nFeatures:")
            for feature in room['features']:
                print(f"  ✓ {feature}")

            if room['qr_ascii']:
                print(f"\nASCII QR Code (scan from terminal!):")
                print(room['qr_ascii'])

        elif command == 'join' and len(sys.argv) >= 3:
            # Join room
            room_id = sys.argv[2]
            username = sys.argv[3] if len(sys.argv) > 3 else 'guest'

            result = join_room(room_id, username=username)

            if result['success']:
                print(f"✓ Joined room: {result['topic']}")
                print(f"  Voice: {'✓' if result['voice_enabled'] else '✗'}")
                print(f"  Chat: {'✓' if result['chat_enabled'] else '✗'}")
            else:
                print(f"✗ {result['error']}")

        elif command == 'list':
            # List active rooms
            rooms = get_active_rooms()

            if rooms:
                print(f"Active Practice Rooms ({len(rooms)}):\n")
                for room in rooms:
                    print(f"• {room['topic']}")
                    print(f"  Room ID: {room['room_id']}")
                    print(f"  Participants: {room['participant_count']}/{room['max_participants']}")
                    print(f"  Created: {room['created_at']}")
                    print()
            else:
                print("No active rooms")

        elif command == 'close' and len(sys.argv) >= 3:
            # Close room
            room_id = sys.argv[2]
            success = close_room(room_id)

            if success:
                print(f"✓ Room closed: {room_id}")

        else:
            print("Unknown command")

    else:
        print("Practice Room Commands:\n")
        print("  python3 practice_room.py create <topic> [duration_minutes]")
        print("      Create practice room\n")
        print("  python3 practice_room.py join <room_id> [username]")
        print("      Join room\n")
        print("  python3 practice_room.py list")
        print("      List active rooms\n")
        print("  python3 practice_room.py close <room_id>")
        print("      Close room\n")
        print("Examples:")
        print("  python3 practice_room.py create python-basics 90")
        print("  python3 practice_room.py join abc123def456 alice")
        print("  python3 practice_room.py list")
