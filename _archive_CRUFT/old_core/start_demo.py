#!/usr/bin/env python3
"""
Quick Start Demo - Prove Practice Rooms Work FROM YOUR PHONE

Creates a practice room, shows QR code, lets multiple people join and submit.

Usage:
    python3 start_demo.py

Then:
    1. Scan QR code with your phone
    2. Fill out form
    3. Submit
    4. Watch it appear in database
    5. Tell friends to scan same QR and join
"""

import socket
import qrcode
from practice_room import create_practice_room, get_active_rooms
from database import get_db
from datetime import datetime


def get_local_ip():
    """Get local IP for LAN access"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "192.168.1.74"  # Fallback to known IP


def print_qr_code(url):
    """Print ASCII QR code"""
    qr = qrcode.QRCode(version=1, box_size=1, border=2)
    qr.add_data(url)
    qr.make()

    print("\n" + "="*70)
    print("  SCAN THIS QR CODE WITH YOUR PHONE")
    print("="*70 + "\n")

    qr.print_ascii(invert=True)
    print()


def show_room_activity(room_id):
    """Show real-time room activity"""
    conn = get_db()

    # Get participants
    participants = conn.execute('''
        SELECT username, joined_at
        FROM practice_room_participants
        WHERE room_id = ? AND status = 'active'
        ORDER BY joined_at DESC
    ''', (room_id,)).fetchall()

    # Get recordings
    recordings = conn.execute('''
        SELECT id, transcription, created_at
        FROM practice_room_recordings
        WHERE room_id = ?
        ORDER BY created_at DESC
        LIMIT 5
    ''', (room_id,)).fetchall()

    conn.close()

    print("\n" + "="*70)
    print(f"  ROOM ACTIVITY (Updates every 5 seconds)")
    print("="*70)

    print(f"\n👥 Participants ({len(participants)}):")
    if participants:
        for p in participants:
            print(f"   • {p['username']} (joined {p['joined_at']})")
    else:
        print("   (No one has joined yet)")

    print(f"\n🎤 Recent Submissions ({len(recordings)}):")
    if recordings:
        for r in recordings:
            text = r['transcription'][:60] if r['transcription'] else 'No text'
            print(f"   • {text}... ({r['created_at']})")
    else:
        print("   (No submissions yet)")

    print()


def main():
    print("\n" + "="*70)
    print("  🚀 PRACTICE ROOM DEMO - PROOF IT WORKS")
    print("="*70)

    # Create room
    print("\n📝 Creating practice room...")

    room_data = create_practice_room(
        topic="LIVE DEMO - Join from your phone!",
        creator_id=1,
        max_participants=20,
        duration_minutes=120
    )

    room_id = room_data['room_id']

    print(f"✅ Room created: {room_id}")

    # Get URLs
    local_ip = get_local_ip()
    room_path = f"/practice/room/{room_id}"

    localhost_url = f"http://localhost:5001{room_path}"
    phone_url = f"http://{local_ip}:5001{room_path}"

    # Show QR code
    print_qr_code(phone_url)

    # Show URLs
    print("="*70)
    print("  ACCESS FROM YOUR DEVICES")
    print("="*70)
    print(f"\n🖥️  From this computer:")
    print(f"   {localhost_url}")
    print(f"\n📱 From your phone (same WiFi):")
    print(f"   {phone_url}")
    print(f"\n🌐 LAN IP: {local_ip}")
    print()

    # Instructions
    print("="*70)
    print("  WHAT TO DO NOW")
    print("="*70)
    print("""
1. Scan the QR code with your phone camera
2. Tap the notification to open in browser
3. Fill out the form and submit
4. Watch your submission appear below in real-time
5. Share QR with friends - multiple people can join!

Press Ctrl+C to stop
""")

    # Show activity loop
    import time

    try:
        while True:
            show_room_activity(room_id)
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n\n✅ Demo stopped\n")
        print(f"Room still active at: {phone_url}")
        print()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
