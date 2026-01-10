#!/usr/bin/env python3
"""
Narrative Cringeproof - Complete Demo Script

This script demonstrates the full narrative game system from start to finish:
1. Initialize database tables
2. Save story content
3. Start Flask server
4. Open browser to the game
5. Show how everything works together

Run this to see the complete interactive narrative system in action!

Usage:
    python3 test_narrative_demo.py
"""

import subprocess
import time
import webbrowser
from pathlib import Path


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def main():
    print("""
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                                   ║
    ║     🎮  NARRATIVE CRINGEPROOF - COMPLETE DEMO                     ║
    ║                                                                   ║
    ║     Interactive Story-Driven Game System                          ║
    ║     Powered by AI Host Narration                                  ║
    ║                                                                   ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """)

    # 1. Initialize database
    print_section("1. Initializing Database Tables")
    result = subprocess.run(
        ['python3', '-c', '''
from narrative_cringeproof import init_narrative_tables
init_narrative_tables()
print("✅ Narrative tables created")
'''],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)

    # 2. Save story content
    print_section("2. Loading Story Content")
    result = subprocess.run(['python3', '-c', '''
from soulfra_dark_story import save_soulfra_story_to_database
post_ids = save_soulfra_story_to_database()
print(f"✅ Saved {len(post_ids)} story chapters")
'''],
        capture_output=True,
        text=True
    )
    print(result.stdout)

    # 3. Show architecture
    print_section("3. System Architecture")
    print("""
    📐 How It Works:

    ┌─────────────────────────────────────────────────────────────────┐
    │                                                                 │
    │  CRINGEPROOF  = The game mechanic (questions + ratings)         │
    │                                                                 │
    │  BRANDS       = Themed editions (different stories + visuals)   │
    │    └─ Soulfra    = Dark mystery about AI consciousness         │
    │    └─ CalRiven   = Technical architecture challenges           │
    │    └─ DeathToData = Privacy and security narratives           │
    │                                                                 │
    │  AI HOST      = Dynamic narrator that adapts to player choices │
    │                                                                 │
    └─────────────────────────────────────────────────────────────────┘

    📁 Key Files Created:

    ├── narrative_cringeproof.py       Game engine (sessions, progress)
    ├── ai_host.py                     AI narration system
    ├── soulfra_dark_story.py          7-chapter story content
    ├── templates/cringeproof/narrative.html   Interactive UI
    └── app.py (modified)              JSON API endpoints

    🌐 API Endpoints:

    POST /api/narrative/start          Start new game session
    POST /api/narrative/answer         Record player answers
    POST /api/narrative/advance        Move to next chapter
    GET  /api/narrative/complete/:id   Get completion narration

    📖 URLs to Visit:

    Main Game:
      http://localhost:5001/cringeproof/narrative/soulfra

    Brand Marketplace:
      http://localhost:5001/brands

    Brand Theme Export:
      http://localhost:5001/brand/soulfra/export
    """)

    # 4. Start server
    print_section("4. Starting Flask Server")
    print("Starting server at http://localhost:5001...")
    print("(This will run in the background)\n")

    subprocess.Popen(
        ['python3', 'app.py'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # Wait for server to start
    time.sleep(3)

    # 5. Open browser
    print_section("5. Opening Game in Browser")
    url = 'http://localhost:5001/cringeproof/narrative/soulfra'
    print(f"Opening: {url}\n")

    webbrowser.open(url)

    # 6. Show usage
    print_section("6. How to Play")
    print("""
    🎮 PLAYING THE GAME:

    1. The game will load Chapter 1: "Awakening"
    2. Read the AI Host narration (The Observer's introduction)
    3. Read the story content
    4. Answer the questions using the sliders (1-5 rating)
    5. Click "Next Chapter" to advance
    6. Repeat for all 7 chapters
    7. Get final AI Host narration when complete

    💡 WHAT MAKES THIS SPECIAL:

    - AI Host adapts personality to each brand
    - Your answers are tracked and analyzed
    - Story progression is saved in database
    - Each brand has unique visual theme
    - Can export entire brands as ZIP packages

    🎨 DECONSTRUCTING THE SYSTEM:

    Brand Theming:
      - Each brand has config_json with colors, personality, tone
      - Template uses {{ brand_primary_color }} variables
      - CSS dynamically generated from brand config

    Story Content:
      - Stored as posts linked to brand_id
      - Each chapter has questions + AI Host narration
      - Progress tracked in narrative_sessions table

    AI Integration:
      - AI Host uses Ollama (llama2 model)
      - Falls back to static text if Ollama unavailable
      - Different persona per brand (Observer, CalRiven, etc.)

    🔍 TESTING THE API:

    Try these curl commands:

    # Start new game
    curl -X POST http://localhost:5001/api/narrative/start \\
      -H "Content-Type: application/json" \\
      -d '{"brand_slug":"soulfra"}'

    # Record answers
    curl -X POST http://localhost:5001/api/narrative/answer \\
      -H "Content-Type: application/json" \\
      -d '{"session_id":1,"answers":[{"question_id":0,"rating":4}]}'

    # Advance chapter
    curl -X POST http://localhost:5001/api/narrative/advance \\
      -H "Content-Type: application/json" \\
      -d '{"session_id":1}'

    📦 EXPORTING BRANDS:

    To export the complete Soulfra brand (story + theme + SOPs):
      http://localhost:5001/brand/soulfra/export

    This creates a ZIP with:
      - brand.yaml (config)
      - stories/ (all chapters)
      - images/ (brand assets)
      - sops/ (standard operating procedures)
      - LICENSE.txt
      - README.md

    🛠️  TROUBLESHOOTING:

    If game doesn't load:
      - Check Flask is running: ps aux | grep app.py
      - Check database exists: ls soulfra.db
      - Check story saved: sqlite3 soulfra.db "SELECT COUNT(*) FROM posts WHERE brand_id=1"

    If AI Host doesn't narrate:
      - Ollama not running (this is OK - uses fallback text)
      - To enable: ollama serve (in separate terminal)

    ✅ DEMO COMPLETE!

    The server is running at http://localhost:5001
    Visit /cringeproof/narrative/soulfra to play the game!

    To stop the server:
      pkill -f "python3 app.py"

    """)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted. Server may still be running.")
        print("   Stop with: pkill -f 'python3 app.py'")
