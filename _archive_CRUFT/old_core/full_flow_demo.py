#!/usr/bin/env python3
"""
Full Flow Demo - Interactive Walkthrough
=========================================

Shows the COMPLETE path from widget → session → database → template → browser

Interactive: Press Enter to move through each step

Usage:
    python3 full_flow_demo.py
"""

import sys
from database import get_db


def wait_for_user(prompt="\n▶ Press Enter to continue..."):
    """Wait for user to press Enter"""
    input(prompt)


def print_box(title, content, width=70):
    """Print a nice box"""
    print("\n" + "┌" + "─"*width + "┐")
    print("│" + title.center(width) + "│")
    print("├" + "─"*width + "┤")
    for line in content.split('\n'):
        print("│ " + line.ljust(width-2) + " │")
    print("└" + "─"*width + "┘")


def demo_intro():
    """Introduction"""
    print("="*72)
    print("  FULL FLOW DEMO - Widget → Session → Database → Template")
    print("="*72)
    print("""
This demo shows EXACTLY how data flows through the platform:

1. User interacts with widget/page
2. Flask creates session
3. Database is queried
4. Template renders with data
5. Browser displays HTML
6. User interacts → API call → Database update → Repeat!

Press Enter to see each step in detail...
    """)
    wait_for_user()


def step1_user_interaction():
    """Step 1: User clicks widget/visits page"""
    print("\n" + "="*72)
    print("  STEP 1: User Interaction")
    print("="*72)

    print_box(
        "User's Browser",
        """User visits: http://localhost:5001/learn

Browser sends HTTP request:
  GET /learn HTTP/1.1
  Host: localhost:5001
  Cookie: session=abc123def456...
"""
    )

    print("\n💭 What happens next?")
    print("   Flask receives the request and routes it to the @app.route('/learn') function")

    wait_for_user()


def step2_flask_route():
    """Step 2: Flask route handler"""
    print("\n" + "="*72)
    print("  STEP 2: Flask Route Handler")
    print("="*72)

    print_box(
        "app.py (lines 11758-11772)",
        """@app.route('/learn')
def learn_dashboard():
    # Get user from session
    user_id = session.get('user_id', 1)

    # Import learning system
    from anki_learning_system import get_learning_stats

    # Query database for user stats
    stats = get_learning_stats(user_id)

    # Render template with data
    return render_template('learn/dashboard.html',
                         stats=stats,
                         tutorials=[])
"""
    )

    print("\n💭 What happens next?")
    print("   Flask extracts user_id from session (defaults to 1 if not logged in)")
    print("   Then calls get_learning_stats(1) to query the database")

    wait_for_user()


def step3_session_handling():
    """Step 3: Session handling"""
    print("\n" + "="*72)
    print("  STEP 3: Session Handling")
    print("="*72)

    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = 1').fetchone()

    print_box(
        "Flask Session",
        f"""session.get('user_id', 1)
  ↓
Returns: {user['id']}

Session data (encrypted cookie):
  user_id: {user['id']}
  username: {user['username']}
  email: {user['email']}

Note: Session persists across requests via encrypted cookie
"""
    )

    print(f"\n✅ User identified: {user['username']} (ID: {user['id']})")

    wait_for_user()


def step4_database_query():
    """Step 4: Database queries"""
    print("\n" + "="*72)
    print("  STEP 4: Database Queries")
    print("="*72)

    db = get_db()

    print("\n🔍 Query 1: Get learning stats")
    print("   SQL:")
    print("   SELECT COUNT(DISTINCT c.id) as total_cards,")
    print("          AVG(p.ease_factor) as avg_ease")
    print("   FROM learning_cards c")
    print("   LEFT JOIN learning_progress p ON c.id = p.card_id")
    print("   WHERE p.user_id = 1")

    stats = db.execute('''
        SELECT COUNT(*) as total_cards FROM learning_cards
    ''').fetchone()

    progress = db.execute('''
        SELECT COUNT(*) as initialized FROM learning_progress WHERE user_id = 1
    ''').fetchone()

    due = db.execute('''
        SELECT COUNT(*) as due FROM learning_progress
        WHERE user_id = 1 AND next_review <= datetime('now')
    ''').fetchone()

    print(f"\n   Results:")
    print(f"     total_cards: {stats['total_cards']}")
    print(f"     initialized: {progress['initialized']}")
    print(f"     due_today: {due['due']}")

    print("\n💾 Database tables involved:")
    print("   - learning_cards (flashcard questions/answers)")
    print("   - learning_progress (user's SM-2 algorithm data)")
    print("   - review_history (complete review log)")

    result_data = {
        'total_cards': stats['total_cards'],
        'cards_initialized': progress['initialized'],
        'due_today': due['due']
    }

    wait_for_user()
    return result_data


def step5_template_rendering(stats):
    """Step 5: Template rendering"""
    print("\n" + "="*72)
    print("  STEP 5: Template Rendering")
    print("="*72)

    print("\n📄 Template: templates/learn/dashboard.html")

    print_box(
        "Jinja2 Template (simplified)",
        f"""<div class="dashboard">
  <h1>Learning Dashboard</h1>

  <div class="stats-grid">
    <div class="stat-card">
      <div class="number">{{{{ stats.due_today }}}}</div>
      <div class="label">Cards Due</div>
    </div>

    <div class="stat-card">
      <div class="number">{{{{ stats.cards_initialized }}}}</div>
      <div class="label">Total Progress</div>
    </div>
  </div>

  <a href="/learn/review" class="btn">Review Cards</a>
</div>
"""
    )

    print("\n🔄 Template variables resolved:")
    print(f"   {{{{ stats.due_today }}}}          → {stats['due_today']}")
    print(f"   {{{{ stats.cards_initialized }}}}  → {stats['cards_initialized']}")

    wait_for_user()


def step6_html_output(stats):
    """Step 6: Final HTML output"""
    print("\n" + "="*72)
    print("  STEP 6: HTML Output to Browser")
    print("="*72)

    print_box(
        "Final HTML sent to browser",
        f"""<div class="dashboard">
  <h1>Learning Dashboard</h1>

  <div class="stats-grid">
    <div class="stat-card">
      <div class="number">{stats['due_today']}</div>
      <div class="label">Cards Due</div>
    </div>

    <div class="stat-card">
      <div class="number">{stats['cards_initialized']}</div>
      <div class="label">Total Progress</div>
    </div>
  </div>

  <a href="/learn/review" class="btn">Review Cards</a>
</div>
"""
    )

    print("\n🌐 Browser renders this HTML:")
    print(f"""
   ┌────────────────────────────────────┐
   │   Learning Dashboard               │
   ├────────────────────────────────────┤
   │                                    │
   │   ┌──────────┐  ┌──────────┐      │
   │   │    {str(stats['due_today']).center(2)}    │  │    {str(stats['cards_initialized']).center(2)}    │      │
   │   │Cards Due │  │  Total   │      │
   │   └──────────┘  └──────────┘      │
   │                                    │
   │   [ Review Cards → ]               │
   └────────────────────────────────────┘
    """)

    wait_for_user()


def step7_user_clicks_review():
    """Step 7: User clicks Review Cards"""
    print("\n" + "="*72)
    print("  STEP 7: User Clicks 'Review Cards'")
    print("="*72)

    print_box(
        "User Action",
        """User clicks: "Review Cards" button

Browser sends:
  GET /learn/review HTTP/1.1
  Cookie: session=abc123def456...

Flask route:
  @app.route('/learn/review')
  def learn_review():
      user_id = session.get('user_id', 1)
      cards = get_cards_due(user_id, limit=20)
      session_id = start_session(user_id, 'review')
      return render_template('learn/review.html',
                           cards=cards,
                           session_id=session_id)
"""
    )

    db = get_db()
    cards = db.execute('''
        SELECT * FROM learning_cards
        LIMIT 1
    ''').fetchone()

    print(f"\n🎴 First card loaded:")
    print(f"   Question: {cards['question']}")
    print(f"   Answer: {cards['answer'] if cards['answer'] else '[No answer]'}")

    wait_for_user()
    return cards


def step8_javascript_interaction(card):
    """Step 8: JavaScript interaction"""
    print("\n" + "="*72)
    print("  STEP 8: JavaScript Card Interaction")
    print("="*72)

    print_box(
        "templates/learn/review.html (JavaScript)",
        f"""// Page loads with cards array
const cards = [{{"id": {card['id']}, "question": "{card['question'][:30]}...", ...}}];
let currentCardIndex = 0;

// Display first card
function loadCard(index) {{
    const card = cards[index];
    document.getElementById('question-text').textContent = card.question;
    document.getElementById('answer-text').textContent = card.answer;

    // Show question, hide answer
    showQuestionSide();
}}

// User clicks "Show Answer"
function showAnswer() {{
    hideQuestionSide();
    showAnswerSide();  // Shows answer + rating buttons
}}

// User clicks rating button (0-5)
function rateCard(quality) {{
    fetch('/api/learn/answer', {{
        method: 'POST',
        body: JSON.stringify({{
            card_id: {card['id']},
            quality: quality,
            session_id: sessionId
        }})
    }})
    .then(res => res.json())
    .then(data => {{
        // Show next review interval
        showResult(data);
        nextCard();
    }});
}}
"""
    )

    print("\n💭 User flow:")
    print("   1. Question displays")
    print("   2. User thinks of answer")
    print("   3. Clicks 'Show Answer'")
    print("   4. Sees answer + explanation")
    print("   5. Clicks rating button (0-5)")
    print("   6. API call → Database update → Next card")

    wait_for_user()


def step9_api_call():
    """Step 9: API call and database update"""
    print("\n" + "="*72)
    print("  STEP 9: API Call & Database Update")
    print("="*72)

    print_box(
        "API Request",
        """POST /api/learn/answer HTTP/1.1
Content-Type: application/json

{
  "card_id": 5,
  "quality": 4,
  "session_id": 8,
  "time_to_answer": 12
}
"""
    )

    print("\n🔄 Flask route handler:")
    print("   @app.route('/api/learn/answer', methods=['POST'])")
    print("   def api_learn_answer():")
    print("       data = request.get_json()")
    print("       user_id = session.get('user_id', 1)")
    print("       result = review_card(user_id, data['card_id'], data['quality'])")
    print("       return jsonify(result)")

    print("\n🧠 SM-2 Algorithm calculates:")
    print("   - New ease_factor (how 'easy' this card is)")
    print("   - New interval_days (when to review next)")
    print("   - Repetitions count (how many times reviewed)")

    print("\n💾 Database UPDATE:")
    print("   UPDATE learning_progress SET")
    print("     ease_factor = 2.6,")
    print("     interval_days = 1,")
    print("     repetitions = 1,")
    print("     next_review = '2025-12-28'")
    print("   WHERE user_id = 1 AND card_id = 5")

    print("\n📊 API Response:")
    print("   {")
    print('     "interval_days": 1,')
    print('     "next_review": "2025-12-28",')
    print('     "streak": 1,')
    print('     "accuracy": 100.0')
    print("   }")

    wait_for_user()


def step10_complete_cycle():
    """Step 10: Complete cycle"""
    print("\n" + "="*72)
    print("  STEP 10: Complete Cycle")
    print("="*72)

    print("""
   🔄 THE COMPLETE CYCLE:

   ┌──────────────────────────────────────────────────────────────────┐
   │                                                                  │
   │  User visits /learn                                              │
   │        ↓                                                        │
   │  Flask route: @app.route('/learn')                               │
   │        ↓                                                        │
   │  Session: user_id = session.get('user_id', 1)                    │
   │        ↓                                                        │
   │  Database: SELECT stats WHERE user_id = 1                        │
   │        ↓                                                        │
   │  Template: render_template('dashboard.html', stats=...)          │
   │        ↓                                                        │
   │  HTML: <div>{{stats.due_today}}</div>                            │
   │        ↓                                                        │
   │  Browser: Displays "12 cards due"                                │
   │        ↓                                                        │
   │  User: Clicks "Review Cards"                                     │
   │        ↓                                                        │
   │  Flask: GET /learn/review → Load cards                           │
   │        ↓                                                        │
   │  JavaScript: Display question                                    │
   │        ↓                                                        │
   │  User: Clicks "Show Answer"                                      │
   │        ↓                                                        │
   │  JavaScript: Display answer + rating buttons                     │
   │        ↓                                                        │
   │  User: Clicks rating button (0-5)                                │
   │        ↓                                                        │
   │  JavaScript: POST /api/learn/answer                              │
   │        ↓                                                        │
   │  Flask: Process rating, call SM-2 algorithm                      │
   │        ↓                                                        │
   │  Database: UPDATE learning_progress SET...                       │
   │        ↓                                                        │
   │  API Response: {interval_days: 1, ...}                           │
   │        ↓                                                        │
   │  JavaScript: Show result, load next card                         │
   │        ↓                                                        │
   │  [REPEAT FROM "JavaScript: Display question"]                    │
   │                                                                  │
   └──────────────────────────────────────────────────────────────────┘
    """)

    wait_for_user()


def demo_widget_integration():
    """Bonus: Widget integration"""
    print("\n" + "="*72)
    print("  BONUS: Widget Integration")
    print("="*72)

    print("""
   🎨 WIDGET SYSTEM:

   The platform includes an embeddable widget system:

   1. Widget Embed (static/widget-embed.js)
      - Creates iframe with chat widget
      - Embeddable on any website
      - Supports QR code integration

   2. Widget QR Bridge (widget_qr_bridge.py)
      - Connects widget to QR code system
      - Scan QR → Open widget
      - Widget shows QR to join

   3. Practice Rooms
      - Collaborative study sessions
      - Each room has QR code
      - Scan → Join room → Start learning

   Flow with widget:
     User scans QR code
       ↓
     Browser opens: /practice/room/abc123
       ↓
     Flask creates session (or QR creates temp user)
       ↓
     Database queries room cards
       ↓
     Template renders room.html
       ↓
     Widget loads with room data
       ↓
     User reviews cards in collaborative session
    """)

    wait_for_user()


def main():
    """Run full flow demo"""
    demo_intro()

    step1_user_interaction()
    step2_flask_route()
    step3_session_handling()
    stats = step4_database_query()
    step5_template_rendering(stats)
    step6_html_output(stats)
    card = step7_user_clicks_review()
    step8_javascript_interaction(card)
    step9_api_call()
    step10_complete_cycle()
    demo_widget_integration()

    print("\n" + "="*72)
    print("  ✅ FULL FLOW DEMO COMPLETE!")
    print("="*72)
    print("""
   You now understand EXACTLY how data flows through the platform!

   Key takeaways:
   1. Flask routes handle HTTP requests
   2. Sessions track user_id across requests
   3. Database queries fetch user-specific data
   4. Templates render HTML with data from database
   5. JavaScript adds interactivity (card ratings)
   6. API calls update database (SM-2 algorithm)
   7. Widgets extend platform (embeddable, QR codes)

   Next steps:
   - Run: python3 hello_world.py (simple version)
   - Run: python3 start.py (start the platform)
   - Read: REMIX_GUIDE.md (customize the flow)

   🎉 You're ready to build on this platform!
    """)


if __name__ == '__main__':
    main()
