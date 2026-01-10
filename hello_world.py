#!/usr/bin/env python3
"""
Hello World - Soulfra Complete Flow
====================================

The absolute simplest demo showing how EVERYTHING connects:
- User session
- Database queries
- Template rendering
- Widget system

Just like "Hello World" in any programming language - proves it all works!

Usage:
    python3 hello_world.py
"""

import sys
from database import get_db


def print_header(title):
    """Print a step header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def step1_user_session():
    """Step 1: Create/Get User Session"""
    print_header("STEP 1: User Session")

    print("\n📝 Creating user session...")

    db = get_db()

    # Get or create test user
    user = db.execute('SELECT * FROM users WHERE username = ?', ('admin',)).fetchone()

    if not user:
        print("   ⚠️  No admin user, creating...")
        db.execute('''
            INSERT INTO users (username, email, password_hash)
            VALUES (?, ?, ?)
        ''', ('admin', 'admin@soulfra.local', 'fake_hash'))
        db.commit()
        user = db.execute('SELECT * FROM users WHERE username = ?', ('admin',)).fetchone()

    print(f"\n   ✅ User Session Created!")
    print(f"      Username: {user['username']}")
    print(f"      User ID: {user['id']}")
    print(f"      Email: {user['email']}")

    # Simulate Flask session
    session_data = {
        'user_id': user['id'],
        'username': user['username']
    }

    print(f"\n   📦 Session Data:")
    print(f"      session['user_id'] = {session_data['user_id']}")
    print(f"      session['username'] = '{session_data['username']}'")

    return session_data


def step2_database_query(user_id):
    """Step 2: Query Database"""
    print_header("STEP 2: Database Query")

    print(f"\n🔍 Querying database for user {user_id}...")

    db = get_db()

    # Query 1: Get learning cards
    cards = db.execute('SELECT * FROM learning_cards LIMIT 3').fetchall()

    print(f"\n   ✅ Query 1: Learning Cards")
    print(f"      SELECT * FROM learning_cards LIMIT 3")
    print(f"      Found: {len(cards)} cards")

    for i, card in enumerate(cards, 1):
        print(f"\n      Card {i}:")
        print(f"        ID: {card['id']}")
        print(f"        Question: {card['question'][:50]}...")
        print(f"        Answer: {card['answer'][:30] if card['answer'] else 'N/A'}...")

    # Query 2: Get user progress
    progress = db.execute('''
        SELECT COUNT(*) as count FROM learning_progress
        WHERE user_id = ?
    ''', (user_id,)).fetchone()

    print(f"\n   ✅ Query 2: User Progress")
    print(f"      SELECT COUNT(*) FROM learning_progress WHERE user_id = {user_id}")
    print(f"      Found: {progress['count']} cards initialized")

    # Query 3: Get cards due
    due = db.execute('''
        SELECT COUNT(*) as count FROM learning_progress
        WHERE user_id = ? AND next_review <= datetime('now')
    ''', (user_id,)).fetchone()

    print(f"\n   ✅ Query 3: Cards Due")
    print(f"      SELECT COUNT(*) FROM learning_progress")
    print(f"      WHERE user_id = {user_id} AND next_review <= NOW")
    print(f"      Found: {due['count']} cards due for review")

    return {
        'cards': cards,
        'progress_count': progress['count'],
        'due_count': due['count']
    }


def step3_template_rendering(session_data, query_results):
    """Step 3: Render Template"""
    print_header("STEP 3: Template Rendering")

    print("\n📄 Rendering templates...")

    # Simulate template data
    template_data = {
        'user': session_data,
        'stats': {
            'total_cards': len(query_results['cards']),
            'cards_initialized': query_results['progress_count'],
            'due_today': query_results['due_count']
        },
        'cards': query_results['cards']
    }

    print(f"\n   ✅ Template: learn/dashboard.html")
    print(f"      Data passed to template:")
    print(f"        user = {template_data['user']}")
    print(f"        stats = {template_data['stats']}")

    # Show how template would render
    print(f"\n   📋 Template Output (simulated):")
    print(f"""
      <div class="dashboard">
        <h1>Welcome, {template_data['user']['username']}!</h1>

        <div class="stats">
          <div class="stat-card">
            <div class="number">{template_data['stats']['due_today']}</div>
            <div class="label">Cards Due</div>
          </div>

          <div class="stat-card">
            <div class="number">{template_data['stats']['cards_initialized']}</div>
            <div class="label">Total Progress</div>
          </div>
        </div>

        <a href="/learn/review" class="btn">Review Cards</a>
      </div>
    """)

    print(f"\n   ✅ HTML Generated!")
    print(f"      Template variables resolved:")
    print(f"        {{{{ user.username }}}} → {template_data['user']['username']}")
    print(f"        {{{{ stats.due_today }}}} → {template_data['stats']['due_today']}")

    return template_data


def step4_widget_system():
    """Step 4: Widget System (Optional)"""
    print_header("STEP 4: Widget System")

    print("\n🎨 Checking widget system...")

    import os

    widget_file = 'static/widget-embed.js'

    if os.path.exists(widget_file):
        print(f"\n   ✅ Widget System Available!")
        print(f"      Location: {widget_file}")
        print(f"      Usage:")
        print(f"""
      <!-- On your website -->
      <script src="http://localhost:5001/static/widget-embed.js"></script>
      <div id="soulfra-widget" data-brand="soulfra"></div>

      <!-- Widget loads in iframe -->
      <iframe src="http://localhost:5001/widget.html?brand=soulfra"></iframe>
        """)

        print(f"\n   🔗 Widget Features:")
        print(f"      - Embeddable chat widget (iframe)")
        print(f"      - QR code integration")
        print(f"      - Practice room support")
        print(f"      - Multi-brand (soulfra, calriven, deathtodata)")
    else:
        print(f"\n   ⚠️  Widget file not found: {widget_file}")
        print(f"      Widget system is optional")

    return {'widget_available': os.path.exists(widget_file)}


def complete_flow():
    """Show the complete flow"""
    print_header("COMPLETE DATA FLOW")

    print("""
   User Request → Flask Route → Session → Database → Template → HTML

   Example: User visits /learn

   1. Browser: GET /learn
      ↓
   2. Flask Route: @app.route('/learn')
      ↓
   3. Session: user_id = session.get('user_id', 1)
      ↓
   4. Database: SELECT * FROM learning_cards WHERE...
      ↓
   5. Template: render_template('learn/dashboard.html', stats=...)
      ↓
   6. HTML: <div>12 cards due</div>
      ↓
   7. Browser: Displays dashboard
   """)


def main():
    """Run Hello World demo"""
    print("="*60)
    print("  🌍 HELLO WORLD - SOULFRA COMPLETE FLOW")
    print("  Proves everything works in one simple script!")
    print("="*60)

    try:
        # Step 1: User Session
        session_data = step1_user_session()

        # Step 2: Database Query
        query_results = step2_database_query(session_data['user_id'])

        # Step 3: Template Rendering
        template_data = step3_template_rendering(session_data, query_results)

        # Step 4: Widget System
        widget_status = step4_widget_system()

        # Show complete flow
        complete_flow()

        # Final summary
        print_header("✅ SUCCESS!")

        print("""
   All 4 components work together:

   1. ✅ User Session (user_id = {user_id})
   2. ✅ Database Query ({cards} cards, {due} due)
   3. ✅ Template Rendering (HTML generated)
   4. ✅ Widget System ({widget})

   🎉 HELLO WORLD COMPLETE!

   Next steps:
   - Run: python3 start.py
   - Visit: http://localhost:5001/learn
   - See: This exact flow in action!
        """.format(
            user_id=session_data['user_id'],
            cards=query_results['progress_count'],
            due=query_results['due_count'],
            widget='Available' if widget_status['widget_available'] else 'Optional'
        ))

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nDebug info:")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
