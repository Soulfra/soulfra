#!/usr/bin/env python3
"""
SIMPLE TEST - Prove Practice Rooms Work

Run this to:
1. Create a test room
2. Show you exact URLs
3. NO ngrok, NO cloud, just local WiFi
"""

import socket
import sys
from practice_room import create_practice_room

def get_local_ip():
    """Get your local WiFi IP"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def main():
    print("\n" + "="*70)
    print("  PRACTICE ROOM TEST - LOCAL WIFI ONLY")
    print("="*70)

    # Get network info
    local_ip = get_local_ip()

    print(f"\n✅ Your WiFi IP: {local_ip}")

    # Create test room
    print("\n📝 Creating test room...")

    try:
        room_data = create_practice_room(
            topic="TEST - Scan this from your phone!",
            creator_id=1,
            max_participants=10,
            duration_minutes=60
        )

        room_id = room_data['room_id']
        print(f"✅ Room created: {room_id}")

    except Exception as e:
        print(f"❌ Error creating room: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Show URLs
    print("\n" + "="*70)
    print("  HOW TO ACCESS")
    print("="*70)

    localhost_url = f"http://localhost:5001/practice/room/{room_id}"
    wifi_url = f"http://{local_ip}:5001/practice/room/{room_id}"
    create_url = f"http://{local_ip}:5001/practice/create"

    print(f"\n🖥️  From THIS computer:")
    print(f"   {localhost_url}")

    print(f"\n📱 From your PHONE (same WiFi):")
    print(f"   {wifi_url}")

    print(f"\n🆕 To create NEW rooms:")
    print(f"   {create_url}")

    # Instructions
    print("\n" + "="*70)
    print("  WHAT TO DO NOW")
    print("="*70)
    print(f"""
1. Start server in another terminal:
   python3 app.py

2. On your phone:
   - Connect to SAME WiFi as this computer
   - Open browser
   - Go to: {wifi_url}

3. Submit a test message

4. Verify in database:
   sqlite3 soulfra.db "SELECT transcription FROM practice_room_recordings WHERE room_id = '{room_id}' ORDER BY created_at DESC LIMIT 5"

THAT'S IT. No ngrok. No cloud. Just works on your WiFi.
""")

    print("="*70)
    print(f"Room ID saved: {room_id}")
    print("="*70 + "\n")

if __name__ == '__main__':
    main()
