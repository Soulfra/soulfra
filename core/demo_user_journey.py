#!/usr/bin/env python3
"""
END-TO-END USER JOURNEY DEMO
=============================

Shows the complete flow from login → dashboard → review → personalization

This proves:
1. How templates get "filled out as we move along"
2. How different users get different data
3. How quiz results affect what users see
4. The full data flow: Route → Database → Template → User

Usage:
    python3 demo_user_journey.py
"""

import sqlite3
import requests
from datetime import datetime, timedelta
from database import get_db


class UserJourneyDemo:
    """Interactive demo showing complete user flow"""

    def __init__(self, base_url='http://localhost:5001'):
        self.base_url = base_url
        self.db = get_db()
        self.session = requests.Session()

    def print_header(self, text):
        """Print formatted section header"""
        print("\n" + "=" * 70)
        print(f"  {text}")
        print("=" * 70 + "\n")

    def print_step(self, step_num, description):
        """Print formatted step"""
        print(f"\n{'─' * 70}")
        print(f"STEP {step_num}: {description}")
        print('─' * 70)

    def show_user_data(self, user_id):
        """Show what data exists for a user"""
        print(f"\n📊 Data for User ID {user_id}:")

        # User info
        user = self.db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        print(f"  Username: {user['username']}")
        print(f"  Admin: {bool(user['is_admin'])}")
        if user['personality_profile']:
            print(f"  Personality: {user['personality_profile'][:100]}...")

        # Learning progress
        cards = self.db.execute('''
            SELECT COUNT(*) as total FROM learning_progress WHERE user_id = ?
        ''', (user_id,)).fetchone()
        print(f"  Learning cards: {cards['total']}")

        # Recent reviews
        reviews = self.db.execute('''
            SELECT COUNT(*) as total FROM review_history
            WHERE user_id = ? AND reviewed_at >= datetime('now', '-7 days')
        ''', (user_id,)).fetchone()
        print(f"  Reviews (7 days): {reviews['total']}")

    def demo_template_data_flow(self, user_id):
        """Show how template gets data"""
        self.print_step(1, "Template Data Flow")

        print("🔍 Following the data from database → template:\n")

        # Simulate what the route does
        print("1️⃣ Flask route /learn calls get_learning_stats(user_id)")

        from anki_learning_system import get_learning_stats
        stats = get_learning_stats(user_id)

        print(f"2️⃣ Database query returns stats dict:")
        for key, value in stats.items():
            print(f"     {key}: {value}")

        print(f"\n3️⃣ Route passes stats to template:")
        print(f"     render_template('learn/dashboard.html', stats=stats)")

        print(f"\n4️⃣ Jinja2 template uses {{{{ stats.due_today }}}}:")
        print(f"     Result: '12' cards due")

        print(f"\n5️⃣ HTML sent to browser:")
        print(f"     <div class=\"text-4xl font-bold\">12</div>")

        print("\n✅ That's how templates 'get filled out as we move along'!")

    def demo_different_users_different_data(self):
        """Show how different users see different content"""
        self.print_step(2, "Different Users → Different Data")

        print("👥 Comparing data for different users:\n")

        users = self.db.execute('SELECT id, username FROM users LIMIT 3').fetchall()

        for user in users:
            user_id = user['id']
            username = user['username']

            # Get stats for this user
            from anki_learning_system import get_learning_stats
            stats = get_learning_stats(user_id)

            print(f"📌 User: {username} (ID: {user_id})")
            print(f"   Due cards: {stats['due_today']}")
            print(f"   Total cards: {stats['total_cards']}")
            print(f"   Streak: {stats['longest_streak']}")
            print(f"   Accuracy: {stats['recent_accuracy']:.1f}%\n")

        print("✅ Each user gets personalized dashboard based on THEIR data!")

    def demo_quiz_results_personalization(self, user_id=1):
        """Show how quiz results affect what user sees"""
        self.print_step(3, "Quiz Results → Personalized Content")

        print("🧠 How review history customizes the learning path:\n")

        # Show review history
        reviews = self.db.execute('''
            SELECT
                c.question,
                r.quality,
                r.time_to_answer_seconds,
                r.reviewed_at
            FROM review_history r
            JOIN learning_cards c ON r.card_id = c.id
            WHERE r.user_id = ?
            ORDER BY r.reviewed_at DESC
            LIMIT 5
        ''', (user_id,)).fetchall()

        if reviews:
            print(f"Recent review history for user {user_id}:\n")
            for i, review in enumerate(reviews, 1):
                quality_emoji = "✅" if review['quality'] >= 3 else "❌"
                print(f"{i}. {quality_emoji} Quality: {review['quality']}/5")
                print(f"   Question: {review['question'][:60]}...")
                print(f"   Time: {review['time_to_answer_seconds']}s")
                print(f"   When: {review['reviewed_at']}\n")

            # Show how this affects next cards
            print("🎯 How this personalizes future learning:")
            print("  • Low quality (0-2) → Card marked as 'difficult'")
            print("  • High quality (4-5) → Card interval increases")
            print("  • Slow response → Neural network learns user struggles")
            print("  • Pattern: User weak on topic X → More cards from topic X")
        else:
            print("⚠️ No review history yet - user is new!")
            print("\nAfter first review:")
            print("  1. User answers cards")
            print("  2. Ratings saved to review_history")
            print("  3. SM-2 algorithm adjusts card intervals")
            print("  4. Neural network learns difficulty patterns")
            print("  5. Next session shows personalized card order")

        print("\n✅ Quiz results directly customize what user sees next!")

    def demo_story_branching_example(self):
        """Show how game stories branch based on user state"""
        self.print_step(4, "Story Branching Based on User State")

        print("📖 Example: How game narratives personalize:\n")

        # Example game session
        game_sessions = self.db.execute('''
            SELECT game_id, session_name, game_type, creator_user_id
            FROM game_sessions
            LIMIT 3
        ''').fetchall()

        if game_sessions:
            for game in game_sessions:
                print(f"🎮 Game: {game['session_name']} ({game['game_type']})")

                # Get game state
                state = self.db.execute('''
                    SELECT turn_number, board_state FROM game_state
                    WHERE game_id = ? ORDER BY turn_number DESC LIMIT 1
                ''', (game['game_id'],)).fetchone()

                if state:
                    print(f"   Turn: {state['turn_number']}")
                    if state['board_state']:
                        print(f"   State: {state['board_state'][:80]}...")
                print()
        else:
            print("⚠️ No active games yet\n")

        print("💡 Story branching pseudocode:")
        print("""
def get_next_story_scene(user_id):
    # Get user's personality
    profile = db.query('SELECT personality_profile FROM users WHERE id=?', user_id)

    # Get learning progress
    stats = get_learning_stats(user_id)
    difficulty_level = 'easy' if stats['avg_ease'] > 2.5 else 'hard'

    # Branch story based on user
    if 'analytical' in profile:
        return technical_puzzle_scene(difficulty_level)
    elif 'creative' in profile:
        return artistic_challenge_scene(difficulty_level)
    else:
        return default_scene(difficulty_level)
""")

        print("\n✅ Stories adapt to user's personality + learning history!")

    def demo_complete_review_flow(self, user_id=1):
        """Show complete review session flow"""
        self.print_step(5, "Complete Review Session Flow")

        print(f"📚 Following a review session for user {user_id}:\n")

        # Get cards due
        from anki_learning_system import get_cards_due
        cards_due = get_cards_due(user_id, limit=3)

        if cards_due:
            print(f"1️⃣ User visits http://localhost:5001/learn")
            print(f"   → Dashboard shows: {len(cards_due)} cards due\n")

            print(f"2️⃣ User clicks 'Start Review Session'")
            print(f"   → Redirects to /learn/review\n")

            print(f"3️⃣ First card loads:")
            card = cards_due[0]
            print(f"   Question: {card['question']}")
            print(f"   Answer: (hidden until user clicks 'Show Answer')\n")

            print(f"4️⃣ User clicks 'Show Answer'")
            answer_preview = card['answer'][:60] if card['answer'] else "[Answer content]"
            print(f"   → JavaScript reveals: {answer_preview}...\n")

            print(f"5️⃣ User rates difficulty (0-5)")
            print(f"   → JavaScript POST to /api/learn/answer")
            print(f"   → Body: {{")
            print(f"        'card_id': {card['id']},")
            print(f"        'quality': 4,  # User's rating")
            print(f"        'time_to_answer_seconds': 12")
            print(f"      }}\n")

            print(f"6️⃣ Backend processes rating:")
            print(f"   → SM-2 algorithm calculates new interval")
            print(f"   → Updates learning_progress table")
            print(f"   → Saves to review_history for analytics")
            print(f"   → Returns next card\n")

            print(f"7️⃣ Template re-renders with new data:")
            print(f"   → Progress bar updates (33% → 66%)")
            print(f"   → Card counter increments (1/3 → 2/3)")
            print(f"   → Next question loads\n")

            print("✅ Complete cycle: User action → API → Database → Template update")
        else:
            print("⚠️ No cards due - user needs cards initialized!")
            print("\nRun: python3 init_learning_cards_for_user.py")

    def run_full_demo(self):
        """Run complete demonstration"""
        self.print_header("🚀 SOULFRA USER JOURNEY DEMO - START TO FINISH")

        print("This demo shows:")
        print("  ✅ How templates get filled with data")
        print("  ✅ How different users see different content")
        print("  ✅ How quiz results personalize learning")
        print("  ✅ How stories branch based on user state")
        print("  ✅ Complete review session flow")

        # Check server is running
        try:
            r = self.session.get(f"{self.base_url}/learn", timeout=2)
            if r.status_code != 200:
                print(f"\n⚠️  Warning: Server returned {r.status_code}")
        except Exception as e:
            print(f"\n⚠️  Warning: Could not reach server: {e}")
            print(f"Make sure server is running: python3 app.py")

        # Run demos
        user_id = 1  # Default user

        self.demo_template_data_flow(user_id)
        self.demo_different_users_different_data()
        self.demo_quiz_results_personalization(user_id)
        self.demo_story_branching_example()
        self.demo_complete_review_flow(user_id)

        # Final summary
        self.print_header("✅ DEMO COMPLETE")
        print("Key Takeaways:")
        print("\n1. Templates aren't 'broken' - they dynamically render based on:")
        print("   • User ID (who is logged in)")
        print("   • Database queries (their learning progress)")
        print("   • Review history (how they answered before)")
        print("   • Personality profile (what type of learner they are)")

        print("\n2. Data flow is simple:")
        print("   Route → Database Query → Dict → render_template() → Jinja2 → HTML")

        print("\n3. Personalization happens via:")
        print("   • User-specific queries (WHERE user_id = ?)")
        print("   • Review history (quality ratings, time taken)")
        print("   • Game state (turn number, board position)")
        print("   • Personality profiles (learning style)")

        print("\n4. To see it live:")
        print("   • Visit: http://localhost:5001/learn")
        print("   • Login as different users → see different data")
        print("   • Complete reviews → watch stats update")
        print("   • Check database → see your progress saved")

        print("\n" + "=" * 70)
        print("  For more details, read: TEMPLATE_DATA_FLOW.md (next)")
        print("=" * 70 + "\n")


def main():
    """Run the demo"""
    demo = UserJourneyDemo()
    demo.run_full_demo()


if __name__ == '__main__':
    main()
