#!/usr/bin/env python3
"""
Soulfra Start - Wordle Easy Mode
=================================

Just run: python3 start.py

No thinking required - it just works!
"""

import os
import sys
import webbrowser
import time
import subprocess
from pathlib import Path


def clean_pycache():
    """Remove all __pycache__ directories"""
    print("🧹 Cleaning __pycache__...")
    count = 0
    for path in Path('.').rglob('__pycache__'):
        subprocess.run(['rm', '-rf', str(path)], capture_output=True)
        count += 1
    print(f"   ✅ Cleaned {count} directories!\n")


def test_database():
    """Quick database sanity check"""
    print("🔍 Testing database...")
    from database import get_db
    db = get_db()
    cards = db.execute('SELECT COUNT(*) as count FROM learning_cards').fetchone()
    print(f"   ✅ {cards['count']} learning cards found\n")
    return cards['count']


def initialize_cards():
    """Initialize cards for user if needed"""
    print("📚 Checking learning progress...")
    from database import get_db
    db = get_db()
    progress = db.execute('SELECT COUNT(*) as count FROM learning_progress WHERE user_id = 1').fetchone()

    if progress['count'] == 0:
        print("   ⚠️  No cards initialized, setting up...")
        from init_learning_cards_for_user import init_cards_for_user
        count = init_cards_for_user(1)
        print(f"   ✅ Initialized {count} cards!\n")
    else:
        print(f"   ✅ {progress['count']} cards ready!\n")


def start_server():
    """Start Flask server and open browser"""
    print("🚀 Starting server...")
    print("   Flask running on http://localhost:5001")
    print("   Learning System: http://localhost:5001/learn\n")

    # Open browser after short delay
    time.sleep(2)
    print("🌐 Opening browser...")
    webbrowser.open('http://localhost:5001/learn')

    # Start Flask
    from app import app
    app.run(host='127.0.0.1', debug=False, port=5001)


def main():
    print("=" * 60)
    print("  🚀 SOULFRA LEARNING PLATFORM")
    print("  Wordle-Easy Mode: Just Works™")
    print("=" * 60)
    print()

    try:
        clean_pycache()
        test_database()
        initialize_cards()

        print("✅ READY TO LEARN!")
        print()
        print("   Visit: http://localhost:5001/learn")
        print("   Review: http://localhost:5001/learn/review")
        print()

        start_server()

    except KeyboardInterrupt:
        print("\n\n👋 Bye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTry running: python3 PROOF_IT_ALL_WORKS.py")
        sys.exit(1)


if __name__ == '__main__':
    main()
