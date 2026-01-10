#!/usr/bin/env python3
"""
Cringeproof Multiplayer Demo - WiFi Testing Guide

Tests the complete Cringeproof flow:
1. Solo play (you answer questions)
2. Multiplayer setup (create room)
3. WiFi testing (grandparents join from phones)
4. Results comparison (leaderboard)
5. Personality pairing (Intent vs Intuition)

Usage:
    python3 test_cringeproof_multiplayer.py
"""

import subprocess
import sys
import os

def get_local_ip():
    """Get local IP address for WiFi access"""
    try:
        result = subprocess.run(
            ['ifconfig'],
            capture_output=True,
            text=True
        )

        for line in result.stdout.split('\n'):
            if 'inet ' in line and '127.0.0.1' not in line:
                parts = line.strip().split()
                for i, part in enumerate(parts):
                    if part == 'inet' and i + 1 < len(parts):
                        ip = parts[i + 1]
                        if ip.startswith('192.168.') or ip.startswith('10.'):
                            return ip

        return '192.168.1.123'  # Fallback

    except Exception as e:
        print(f"⚠️  Could not detect IP: {e}")
        return '192.168.1.123'


def main():
    """Run Cringeproof multiplayer demo"""
    print("\n" + "="*70)
    print("🎮 CRINGEPROOF MULTIPLAYER DEMO")
    print("="*70)

    # Get local IP
    local_ip = get_local_ip()
    base_url = f"http://{local_ip}:5001"

    print(f"\n✅ Your local IP: {local_ip}")
    print(f"✅ Base URL: {base_url}")

    # Step 1: Solo Play Intro
    print("\n" + "="*70)
    print("STEP 1: SOLO PLAY (Try It Yourself First)")
    print("="*70)

    print(f"""
🎯 What is Cringeproof?
   A self-awareness game that reveals your personality through 7 questions.

   Questions like:
   - "I triple-check my texts before sending"
   - "I worry about what people think of my social media"
   - "I rehearse conversations in my head"

📊 Scoring:
   7-14:  Low self-awareness (Relaxed, spontaneous)
   15-21: Moderate (Balanced approach)
   22-28: High self-awareness (Thoughtful, introspective)
   29-35: Very high (Analytical, careful)

🎭 Personality Types:
   - INTENTIONAL: Low scores (action-oriented, present-focused)
   - INTUITIVE: High scores (introspective, self-aware)

💡 Why It Matters:
   Understanding your type helps you:
   - Know how you process information
   - Find compatible collaborators
   - Communicate better with others
""")

    print("\n🖥️  TRY IT NOW:")
    print(f"   1. Open browser: {base_url}/cringeproof")
    print(f"   2. Answer 7 questions honestly")
    print(f"   3. Get your score + AI insights")
    print(f"   4. Remember your score for comparison!")

    # Step 2: Multiplayer Setup
    print("\n" + "="*70)
    print("STEP 2: MULTIPLAYER SETUP (Play with Grandparents)")
    print("="*70)

    print(f"""
🎮 How Multiplayer Works:
   1. You create a "room" (like a game lobby)
   2. Room gets a code (e.g., ABCD1234)
   3. Share code with grandparents
   4. Everyone joins same room
   5. Play together, compare scores!

📱 WiFi Requirement:
   - Everyone must be on same WiFi network
   - Server running on THIS computer ({local_ip})
   - Phones connect to same network
   - No internet required! (local only)
""")

    print("\n🔧 CREATE MULTIPLAYER ROOM:")
    print(f"   1. Visit: {base_url}/cringeproof")
    print(f"   2. Click 'Create Multiplayer Room' button")
    print(f"   3. Get room code (example: ABCD1234)")
    print(f"   4. Keep this page open!")

    # Step 3: Grandparents Join
    print("\n" + "="*70)
    print("STEP 3: GRANDPARENTS JOIN (From Their Phones)")
    print("="*70)

    print(f"""
👴 GRANDMA'S PHONE:
   1. Connect to your WiFi (same network as this computer)
   2. Open Safari/Chrome
   3. Type in address bar: {base_url}/cringeproof/room/ABCD1234
      (Replace ABCD1234 with YOUR actual room code!)
   4. She'll see: "Welcome to room ABCD1234"
   5. Enter her name: "Grandma"
   6. Click "Join Room"
   7. Answer 7 questions
   8. Submit!

👵 GRANDPA'S PHONE:
   1. Same WiFi network
   2. Open browser
   3. Type: {base_url}/cringeproof/room/ABCD1234
   4. Enter name: "Grandpa"
   5. Join Room
   6. Answer 7 questions
   7. Submit!

💡 TIP:
   - If typing the URL is hard, create a QR code:
     python3 -c "
import qr_encoder_stdlib
qr = qr_encoder_stdlib.generate_qr_code('{base_url}/cringeproof/room/ABCD1234', scale=10)
with open('cringeproof-room-qr.bmp', 'wb') as f:
    f.write(qr)
print('QR code saved!')
"
   - Then scan QR code instead of typing URL!
""")

    # Step 4: Results Comparison
    print("\n" + "="*70)
    print("STEP 4: RESULTS & LEADERBOARD")
    print("="*70)

    print(f"""
🏆 VIEW LEADERBOARD:
   Visit: {base_url}/cringeproof/leaderboard

   You'll see something like:

   ┌─────────────────────────────────────┐
   │  CRINGEPROOF LEADERBOARD            │
   ├─────────────┬───────┬───────────────┤
   │ Player      │ Score │ Personality   │
   ├─────────────┼───────┼───────────────┤
   │ You         │  28   │ 🧠 Intuitive  │
   │ Grandma     │  15   │ ⚡ Intentional│
   │ Grandpa     │  22   │ ⚖️  Balanced   │
   └─────────────┴───────┴───────────────┘

💡 PERSONALITY ANALYSIS:

   YOU (Score: 28) - Intuitive Type
   ✓ High self-awareness
   ✓ Thinks before acting
   ✓ Analyzes past interactions
   ✓ Values authenticity

   GRANDMA (Score: 15) - Intentional Type
   ✓ Action-oriented
   ✓ Lives in the moment
   ✓ Doesn't overthink
   ✓ Spontaneous

   GRANDPA (Score: 22) - Balanced Type
   ✓ Mix of both types
   ✓ Thoughtful but decisive
   ✓ Reflects but doesn't ruminate
   ✓ Good mediator

🤝 SUGGESTED PAIRINGS:

   Best Collaborations:
   - You + Grandma = Complementary (Intuitive + Intentional)
     • You plan, she executes
     • You analyze, she acts
     • Balanced team!

   - You + Grandpa = Aligned (Both thoughtful)
     • Similar problem-solving approach
     • Easy communication
     • Mutual understanding

   - Grandma + Grandpa = Dynamic (Spontaneity + Balance)
     • She brings energy
     • He brings structure
     • Fun partnership!
""")

    # Step 5: Intent vs Intuition Deep Dive
    print("\n" + "="*70)
    print("STEP 5: INTENT VS INTUITION (The Science)")
    print("="*70)

    print("""
🧠 What's the Difference?

INTENTIONAL (Low Scores 7-21)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Focus: External world, action
Process: See problem → Act immediately
Strength: Quick decisions, confident
Challenge: May miss nuance, act impulsively

Example:
   Message received → Reply right away
   Problem appears → Fix it now
   Idea comes up → Say it out loud

INTUITIVE (High Scores 22-35)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Focus: Internal world, reflection
Process: See problem → Think → Analyze → Act
Strength: Thoughtful, considers all angles
Challenge: May overthink, second-guess

Example:
   Message received → Read 3 times → Draft reply → Edit → Send
   Problem appears → Think about it → Research → Plan → Fix
   Idea comes up → Analyze → Refine → Share carefully

🎯 Why Both Matter:

   - Intentional people move things forward
   - Intuitive people ensure quality
   - TOGETHER = Unstoppable team!

🔮 Future: Moral Dilemmas

   Next version will add ethical questions:

   "Would you lie to protect someone's feelings?"
   - Intentional: "Yes, protect them" (values action)
   - Intuitive: "Depends on context" (values truth/nuance)

   "Privacy vs security: which matters more?"
   - Intentional: "Security - must act to protect"
   - Intuitive: "Privacy - principles matter"

   Use responses to find VALUE ALIGNMENT
   → Pair people who share ethics
   → Or intentionally mix for debate/growth!
""")

    # Step 6: Verification
    print("\n" + "="*70)
    print("STEP 6: VERIFY IT WORKED")
    print("="*70)

    print("""
✅ Check Database:
   python3 -c "
from database import get_db
import json

db = get_db()
results = db.execute('''
    SELECT
        gr.score,
        gr.insights,
        u.username,
        gr.created_at
    FROM game_results gr
    LEFT JOIN users u ON gr.user_id = u.id
    WHERE gr.game_type = 'cringeproof'
    ORDER BY gr.created_at DESC
    LIMIT 3
''').fetchall()

print('\\n🎮 RECENT CRINGEPROOF RESULTS:\\n')
for r in results:
    print(f'  {r[\"username\"] or \"Anonymous\"}: Score {r[\"score\"]}')
    insights = json.loads(r['insights']) if r['insights'] else {}
    personality = insights.get('personality_type', 'Unknown')
    print(f'    Type: {personality}')
    print(f'    Date: {r[\"created_at\"]}')
    print()

db.close()
"

   You should see entries for:
   - You
   - Grandma
   - Grandpa

   All with scores and personality types!
""")

    # Summary
    print("\n" + "="*70)
    print("🎉 CRINGEPROOF PITCH SUMMARY")
    print("="*70)

    print(f"""
✅ WHAT YOU HAVE:
   - Self-awareness game (7 questions)
   - Solo AND multiplayer modes
   - WiFi-based local multiplayer
   - Personality analysis (Intent vs Intuition)
   - Leaderboard/comparison
   - Pairing suggestions

🎯 THE PITCH:

   "Cringeproof helps you understand yourself and connect with others.

   Answer 7 questions. Get your personality type.
   Play with friends. See how you compare.
   Discover the best people to collaborate with.

   Are you Intentional (action-oriented)?
   Or Intuitive (thoughtful, reflective)?

   Neither is better. Both are needed.
   But knowing YOUR type changes everything.

   Try it now: {base_url}/cringeproof
   Share with others: Create a room, play together.
   Build better teams: Based on personality, not guesswork."

🚀 NEXT STEPS:
   1. Play solo: {base_url}/cringeproof
   2. Create room for multiplayer
   3. Share with grandparents (same WiFi!)
   4. Compare scores on leaderboard
   5. Discuss your personality differences!

📚 LEARN MORE:
   - CRINGEPROOF_PITCH.md (full documentation)
   - FRONTEND_ARCHITECTURE.md (how it works technically)
   - ECOSYSTEM_EXPLAINED.md (how it fits in bigger picture)

💡 MORAL DILEMMA EXPANSION (Future):
   Add ethical questions to assess values
   Pair people based on shared ethics
   Create debates between opposing types
   Build consensus through discussion

   Example room types:
   - "Aligned" room: Only similar personalities
   - "Diverse" room: Mix of all types
   - "Debate" room: Opposite personalities discuss ethics
""")

    print("="*70)
    print(f"🎮 START NOW: {base_url}/cringeproof")
    print("="*70 + "\n")


if __name__ == '__main__':
    main()
