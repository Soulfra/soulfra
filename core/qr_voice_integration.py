#!/usr/bin/env python3
"""
QR + Voice Integration - Attach Voice Memos to QR Code Scans

Connect QR codes with voice input:
- Scan QR → Record voice memo → Attach to scan
- Store audio in database
- Transcribe (manual or auto)
- Play back voice memos from scan history

Use Cases:
1. Voice notes: Scan QR, record idea, save to database
2. Audio feedback: Scan product QR, record feedback
3. Voice commands: Scan QR, speak command, execute
4. Meeting notes: Scan room QR, record discussion

Usage:
    from qr_voice_integration import attach_voice_to_scan, get_scan_voice

    # Attach voice memo to QR scan
    attach_voice_to_scan(scan_id=123, audio_file='note.wav')

    # Get voice memo for scan
    voice = get_scan_voice(scan_id=123)
"""

import sqlite3
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime


def get_db():
    """Get database connection"""
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    return conn


def init_voice_qr_tables():
    """Initialize voice+QR integration tables"""
    db = get_db()

    # Create voice_qr_attachments table
    db.execute('''
        CREATE TABLE IF NOT EXISTS voice_qr_attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_id INTEGER NOT NULL,
            voice_input_id INTEGER,
            audio_file_path TEXT,
            duration_seconds REAL,
            transcription TEXT,
            transcription_status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            transcribed_at TIMESTAMP,
            FOREIGN KEY (scan_id) REFERENCES qr_faucet_scans(id),
            FOREIGN KEY (voice_input_id) REFERENCES voice_inputs(id)
        )
    ''')

    # Create index for faster lookups
    db.execute('''
        CREATE INDEX IF NOT EXISTS idx_voice_qr_scan
        ON voice_qr_attachments(scan_id)
    ''')

    db.commit()
    db.close()


def attach_voice_to_scan(scan_id: int, audio_file: str,
                         transcription: Optional[str] = None) -> int:
    """
    Attach voice memo to QR scan

    Args:
        scan_id: QR scan ID
        audio_file: Path to audio file
        transcription: Optional transcription text

    Returns:
        attachment_id: ID of voice attachment
    """
    init_voice_qr_tables()

    audio_path = Path(audio_file)

    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_file}")

    db = get_db()

    # Get audio duration (if available)
    duration = None
    try:
        import subprocess
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries',
             'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1',
             str(audio_path)],
            capture_output=True,
            text=True
        )
        duration = float(result.stdout.strip())
    except:
        pass  # Duration not critical

    # Insert attachment
    cursor = db.execute('''
        INSERT INTO voice_qr_attachments (
            scan_id, audio_file_path, duration_seconds,
            transcription, transcription_status
        ) VALUES (?, ?, ?, ?, ?)
    ''', (
        scan_id,
        str(audio_path),
        duration,
        transcription,
        'completed' if transcription else 'pending'
    ))

    attachment_id = cursor.lastrowid
    db.commit()
    db.close()

    print(f"✓ Attached voice memo to scan {scan_id}")
    if transcription:
        print(f"  Transcription: {transcription[:50]}...")
    if duration:
        print(f"  Duration: {duration:.1f}s")

    return attachment_id


def get_scan_voice(scan_id: int) -> Optional[Dict]:
    """
    Get voice memo attached to scan

    Args:
        scan_id: QR scan ID

    Returns:
        Voice attachment data or None
    """
    init_voice_qr_tables()

    db = get_db()

    row = db.execute('''
        SELECT * FROM voice_qr_attachments
        WHERE scan_id = ?
        ORDER BY created_at DESC
        LIMIT 1
    ''', (scan_id,)).fetchone()

    db.close()

    if not row:
        return None

    return dict(row)


def get_all_voice_scans() -> List[Dict]:
    """Get all QR scans with voice attachments"""
    init_voice_qr_tables()

    db = get_db()

    rows = db.execute('''
        SELECT
            v.*,
            s.faucet_id,
            s.ip_address,
            s.device_type,
            s.scanned_at
        FROM voice_qr_attachments v
        LEFT JOIN qr_faucet_scans s ON v.scan_id = s.id
        ORDER BY v.created_at DESC
    ''').fetchall()

    db.close()

    return [dict(row) for row in rows]


def transcribe_voice_attachment(attachment_id: int, transcription: str) -> bool:
    """
    Add transcription to voice attachment

    Args:
        attachment_id: Attachment ID
        transcription: Transcription text

    Returns:
        True if updated
    """
    init_voice_qr_tables()

    db = get_db()

    result = db.execute('''
        UPDATE voice_qr_attachments
        SET transcription = ?,
            transcription_status = 'completed',
            transcribed_at = ?
        WHERE id = ?
    ''', (transcription, datetime.now(), attachment_id))

    db.commit()
    db.close()

    return result.rowcount > 0


def generate_qr_with_voice_prompt(payload_type: str, data: Dict,
                                  voice_prompt: str = "Scan and speak your thoughts") -> Dict:
    """
    Generate QR code that prompts for voice input after scan

    Args:
        payload_type: QR payload type
        data: Payload data
        voice_prompt: Prompt to show user

    Returns:
        QR generation result with voice prompt
    """
    from qr_faucet import generate_qr_payload

    # Add voice prompt to payload data
    data['voice_prompt'] = voice_prompt
    data['expects_voice'] = True

    # Generate QR
    encoded = generate_qr_payload(payload_type, data)

    return {
        'encoded_payload': encoded,
        'voice_prompt': voice_prompt,
        'voice_enabled': True
    }


def process_voice_qr_scan(encoded_payload: str, device_fingerprint: Dict,
                         audio_file: Optional[str] = None,
                         transcription: Optional[str] = None) -> Dict:
    """
    Process QR scan with optional voice attachment

    Args:
        encoded_payload: QR payload
        device_fingerprint: Device info
        audio_file: Optional audio file path
        transcription: Optional transcription

    Returns:
        Processing result with scan_id and attachment_id
    """
    from qr_faucet import process_qr_faucet

    # Process QR scan
    result = process_qr_faucet(encoded_payload, device_fingerprint)

    if not result['success']:
        return result

    # Get scan ID (last scan in database)
    db = get_db()
    scan = db.execute('''
        SELECT id FROM qr_faucet_scans
        ORDER BY id DESC LIMIT 1
    ''').fetchone()
    db.close()

    if not scan:
        return result

    scan_id = scan['id']

    # Attach voice if provided
    attachment_id = None
    if audio_file:
        attachment_id = attach_voice_to_scan(scan_id, audio_file, transcription)
        result['voice_attached'] = True
        result['attachment_id'] = attachment_id
    else:
        result['voice_attached'] = False

    result['scan_id'] = scan_id

    return result


# CLI for testing
if __name__ == '__main__':
    import sys
    import json

    print("QR + Voice Integration\n")

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'init':
            # Initialize tables
            init_voice_qr_tables()
            print("✓ Voice+QR tables initialized")

        elif command == 'attach' and len(sys.argv) >= 4:
            # Attach voice to scan
            scan_id = int(sys.argv[2])
            audio_file = sys.argv[3]
            transcription = sys.argv[4] if len(sys.argv) > 4 else None

            attachment_id = attach_voice_to_scan(scan_id, audio_file, transcription)
            print(f"✓ Voice attached (ID: {attachment_id})")

        elif command == 'get' and len(sys.argv) >= 3:
            # Get voice for scan
            scan_id = int(sys.argv[2])
            voice = get_scan_voice(scan_id)

            if voice:
                print(json.dumps(voice, indent=2, default=str))
            else:
                print(f"No voice attachment for scan {scan_id}")

        elif command == 'list':
            # List all voice scans
            scans = get_all_voice_scans()

            if scans:
                print(f"Found {len(scans)} QR scans with voice:\n")
                for scan in scans:
                    print(f"Scan #{scan['scan_id']}")
                    print(f"  Audio: {scan['audio_file_path']}")
                    if scan['transcription']:
                        print(f"  Transcription: {scan['transcription'][:50]}...")
                    print(f"  Device: {scan['device_type']}")
                    print(f"  Scanned: {scan['scanned_at']}")
                    print()
            else:
                print("No voice scans found")

        elif command == 'transcribe' and len(sys.argv) >= 4:
            # Add transcription
            attachment_id = int(sys.argv[2])
            transcription = sys.argv[3]

            success = transcribe_voice_attachment(attachment_id, transcription)

            if success:
                print(f"✓ Transcription added to attachment {attachment_id}")
            else:
                print(f"✗ Failed to update attachment {attachment_id}")

        elif command == 'generate':
            # Generate QR with voice prompt
            result = generate_qr_with_voice_prompt(
                'blog',
                {'topic': 'voice test'},
                voice_prompt="Scan and record your thoughts about this topic"
            )

            print("✓ QR code generated with voice prompt:")
            print(f"  Payload: {result['encoded_payload'][:50]}...")
            print(f"  Prompt: {result['voice_prompt']}")

        else:
            print("Unknown command")

    else:
        print("QR + Voice Integration Commands:\n")
        print("  python3 qr_voice_integration.py init")
        print("      Initialize tables\n")
        print("  python3 qr_voice_integration.py attach <scan_id> <audio_file> [transcription]")
        print("      Attach voice memo to scan\n")
        print("  python3 qr_voice_integration.py get <scan_id>")
        print("      Get voice memo for scan\n")
        print("  python3 qr_voice_integration.py list")
        print("      List all voice scans\n")
        print("  python3 qr_voice_integration.py transcribe <attachment_id> <text>")
        print("      Add transcription\n")
        print("  python3 qr_voice_integration.py generate")
        print("      Generate QR with voice prompt\n")
