# Remix Guide - Customize Everything

**Created:** 2025-12-27
**Purpose:** Show how to customize, modify, and "remix" the platform
**Audience:** Developers who want to build on top of Soulfra

---

## What "Remix" Means

**Remix** = Take the existing platform and customize it for your needs

Like remixing a song:
- Keep the core structure (database, Flask, templates)
- Change the details (users, cards, widgets, themes)
- Add new features (custom routes, new tables, integrations)
- Mix and match components (QR + Learning, Widget + Practice Rooms)

---

## Quick Remix Examples

### Remix 1: Different User

```python
# Default (app.py line 11761)
user_id = session.get('user_id', 1)  # Defaults to admin

# Remix: Force different user
user_id = 2  # Use soul_tester instead

# Remix: Get user from request
user_id = request.args.get('user_id', 1)

# Remix: Create new user on the fly
db = get_db()
db.execute('''
    INSERT OR IGNORE INTO users (username, email)
    VALUES (?, ?)
''', ('new_user', 'new@example.com'))
user_id = db.execute('SELECT id FROM users WHERE username = ?', ('new_user',)).fetchone()['id']
```

---

### Remix 2: Different Learning Cards

```python
# Default: Get all cards due
cards = get_cards_due(user_id, limit=20)

# Remix: Only Python cards
db = get_db()
cards = db.execute('''
    SELECT * FROM learning_cards
    WHERE topic = 'Python'
    LIMIT 20
''').fetchall()

# Remix: Only hard cards (low ease_factor)
cards = db.execute('''
    SELECT c.*, p.ease_factor
    FROM learning_cards c
    JOIN learning_progress p ON c.id = p.card_id
    WHERE p.user_id = ? AND p.ease_factor < 2.0
    ORDER BY p.ease_factor ASC
    LIMIT 20
''', (user_id,)).fetchall()

# Remix: Mix topics
topics = ['Python', 'SQLite', 'Flask']
cards = []
for topic in topics:
    topic_cards = db.execute('''
        SELECT * FROM learning_cards WHERE topic = ? LIMIT 5
    ''', (topic,)).fetchall()
    cards.extend(topic_cards)
```

---

### Remix 3: Custom Widget

```python
# Default: Static widget brand
widget_brand = 'soulfra'

# Remix: Dynamic brand based on user
user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
if user['username'] == 'calriven':
    widget_brand = 'calriven'
elif user['username'] == 'deathtodata':
    widget_brand = 'deathtodata'
else:
    widget_brand = 'soulfra'

# Remix: Brand from URL parameter
widget_brand = request.args.get('brand', 'soulfra')

# Remix: Custom widget HTML
custom_widget = f"""
<div id="my-custom-widget">
    <iframe src="/widget.html?brand={widget_brand}&theme=dark"></iframe>
</div>
"""
```

---

### Remix 4: Add New Route

```python
# Add to app.py

@app.route('/custom/my-feature')
def my_custom_feature():
    \"\"\"Custom feature endpoint\"\"\"
    user_id = session.get('user_id', 1)

    db = get_db()

    # Your custom query
    custom_data = db.execute('''
        SELECT * FROM your_custom_table
        WHERE user_id = ?
    ''', (user_id,)).fetchall()

    # Render custom template
    return render_template('custom/my_feature.html',
                         data=custom_data,
                         user_id=user_id)
```

---

## Component Remixes

### 1. Session Handling

#### Default Session

```python
# app.py line 11761
user_id = session.get('user_id', 1)
```

#### Remix: QR-Based Session

```python
# When user scans QR, create temp user
from qr_faucet import validate_qr_payload

qr_payload = request.args.get('qr')
qr_data = validate_qr_payload(qr_payload)

if qr_data and qr_data['action'] == 'create_user':
    # Create temporary user
    temp_username = f"qr_{qr_data['id']}"

    db.execute('''
        INSERT OR IGNORE INTO users (username, email)
        VALUES (?, ?)
    ''', (temp_username, f"{temp_username}@qr.local"))

    user = db.execute('SELECT * FROM users WHERE username = ?', (temp_username,)).fetchone()
    session['user_id'] = user['id']

user_id = session.get('user_id', 1)
```

---

### 2. Database Queries

#### Default Query

```python
# anki_learning_system.py line 100
cards = conn.execute('''
    SELECT * FROM learning_cards
    WHERE id IN (
        SELECT card_id FROM learning_progress
        WHERE user_id = ? AND next_review <= datetime('now')
    )
    ORDER BY next_review ASC
    LIMIT ?
''', (user_id, limit)).fetchall()
```

#### Remix: Priority-Based

```python
# Add priority field to learning_cards
cards = conn.execute('''
    SELECT c.*, p.ease_factor,
           CASE
               WHEN c.difficulty_predicted > 0.8 THEN 3
               WHEN c.difficulty_predicted > 0.5 THEN 2
               ELSE 1
           END as priority
    FROM learning_cards c
    JOIN learning_progress p ON c.id = p.card_id
    WHERE p.user_id = ? AND p.next_review <= datetime('now')
    ORDER BY priority DESC, p.next_review ASC
    LIMIT ?
''', (user_id, limit)).fetchall()
```

#### Remix: Spaced by Topic

```python
# Ensure variety: max 3 cards per topic
from collections import Counter

topic_counts = Counter()
cards = []

all_due = conn.execute('''
    SELECT * FROM learning_cards WHERE...
''').fetchall()

for card in all_due:
    if topic_counts[card['topic']] < 3:
        cards.append(card)
        topic_counts[card['topic']] += 1

    if len(cards) >= limit:
        break
```

---

### 3. Template Rendering

#### Default Template

```python
# app.py line 11770
return render_template('learn/dashboard.html',
                     stats=stats,
                     tutorials=[])
```

#### Remix: Dynamic Template

```python
# Choose template based on user preference
user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

if user['theme'] == 'dark':
    template = 'learn/dashboard_dark.html'
elif user['experience_level'] == 'beginner':
    template = 'learn/dashboard_simple.html'
else:
    template = 'learn/dashboard.html'

return render_template(template,
                     stats=stats,
                     tutorials=[],
                     theme=user['theme'])
```

#### Remix: Custom Data

```python
# Add extra data to template
from datetime import datetime

# Get user streak
streak = db.execute('''
    SELECT COUNT(DISTINCT DATE(created_at)) as days
    FROM review_history
    WHERE user_id = ? AND created_at >= datetime('now', '-7 days')
''', (user_id,)).fetchone()

# Get recent achievements
achievements = db.execute('''
    SELECT * FROM achievements
    WHERE user_id = ?
    ORDER BY unlocked_at DESC
    LIMIT 5
''', (user_id,)).fetchall()

return render_template('learn/dashboard.html',
                     stats=stats,
                     streak=streak['days'],
                     achievements=achievements,
                     current_time=datetime.now())
```

---

### 4. API Endpoints

#### Default API

```python
# app.py line 11793
@app.route('/api/learn/answer', methods=['POST'])
def api_learn_answer():
    user_id = session.get('user_id', 1)
    data = request.get_json()

    result = review_card(user_id, data['card_id'], data['quality'])

    return jsonify(result)
```

#### Remix: Add Webhooks

```python
@app.route('/api/learn/answer', methods=['POST'])
def api_learn_answer():
    user_id = session.get('user_id', 1)
    data = request.get_json()

    result = review_card(user_id, data['card_id'], data['quality'])

    # Remix: Trigger webhook on milestone
    if result['streak'] % 10 == 0:
        import requests
        requests.post('https://your-webhook.com/milestone', json={
            'user_id': user_id,
            'streak': result['streak'],
            'card_id': data['card_id']
        })

    # Remix: Log to external analytics
    analytics.track(user_id, 'card_reviewed', {
        'quality': data['quality'],
        'interval_days': result['interval_days']
    })

    return jsonify(result)
```

---

## Mix & Match Features

### Combo 1: QR + Learning

```python
# Create QR code that starts review session

from qr_faucet import generate_qr_payload
import qrcode

# Generate QR payload
payload = generate_qr_payload(
    'review_session',
    {
        'user_id': user_id,
        'topic': 'Python',
        'limit': 10
    },
    ttl_seconds=3600
)

qr_url = f"http://localhost:5001/qr/review/{payload}"

# Generate QR image
qr = qrcode.QRCode()
qr.add_data(qr_url)
qr.make()
img = qr.make_image()
img.save('static/qr_codes/review_session.png')

# Scan QR → Auto-starts review session
@app.route('/qr/review/<payload>')
def qr_review(payload):
    from qr_faucet import validate_qr_payload
    data = validate_qr_payload(payload)

    if data:
        # Start review with QR parameters
        session['user_id'] = data['user_id']
        return redirect(f"/learn/review?topic={data['topic']}&limit={data['limit']}")
    else:
        return "Invalid QR code", 400
```

---

### Combo 2: Widget + Practice Rooms

```python
# Embeddable widget that joins practice room

# 1. Create practice room
room_id = secrets.token_urlsafe(16)
db.execute('''
    INSERT INTO practice_rooms (room_id, topic, status)
    VALUES (?, ?, 'active')
''', (room_id, 'Python Study'))

# 2. Generate widget with room
widget_html = f"""
<script src="/static/widget-embed.js"></script>
<div id="soulfra-widget"
     data-brand="soulfra"
     data-room="{room_id}"></div>
"""

# 3. Widget loads with room context
@app.route('/widget.html')
def widget_page():
    room_id = request.args.get('room')

    if room_id:
        # Widget shows room chat + cards
        room = db.execute('SELECT * FROM practice_rooms WHERE room_id = ?', (room_id,)).fetchone()
        cards = db.execute('''
            SELECT c.* FROM learning_cards c
            JOIN room_cards rc ON c.id = rc.card_id
            WHERE rc.room_id = ?
        ''', (room_id,)).fetchall()

        return render_template('widgets/room_widget.html',
                             room=room,
                             cards=cards)
    else:
        return render_template('widgets/chat_widget.html')
```

---

### Combo 3: Neural Networks + Learning Cards

```python
# Use AI to generate personalized cards

def generate_personalized_cards(user_id):
    \"\"\"Use neural networks to create custom cards based on user's weak areas\"\"\"

    # Get user's review history
    weak_topics = db.execute('''
        SELECT c.topic, AVG(r.quality) as avg_quality
        FROM review_history r
        JOIN learning_cards c ON r.card_id = c.id
        WHERE r.user_id = ? AND r.quality < 3
        GROUP BY c.topic
        ORDER BY avg_quality ASC
        LIMIT 3
    ''', (user_id,)).fetchall()

    # Load neural network
    from neural_network_inference import load_network
    generator = load_network('content_generator')

    # Generate cards for weak topics
    new_cards = []
    for topic_data in weak_topics:
        # AI generates question/answer
        card_text = generator.generate(f"Create flashcard about {topic_data['topic']}")

        # Parse AI output
        question, answer = parse_flashcard(card_text)

        # Insert new card
        db.execute('''
            INSERT INTO learning_cards (question, answer, topic, created_by_ai)
            VALUES (?, ?, ?, 1)
        ''', (question, answer, topic_data['topic']))

        new_cards.append({'question': question, 'answer': answer})

    return new_cards
```

---

## Add New Tables

### Example: Achievements System

```python
# 1. Create table
db.execute('''
    CREATE TABLE IF NOT EXISTS achievements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        icon TEXT,
        points INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

db.execute('''
    CREATE TABLE IF NOT EXISTS user_achievements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        achievement_id INTEGER,
        unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (achievement_id) REFERENCES achievements(id),
        UNIQUE(user_id, achievement_id)
    )
''')

# 2. Seed achievements
achievements = [
    ("First Card", "Reviewed your first card", "🎴", 10),
    ("Week Streak", "Studied 7 days in a row", "🔥", 50),
    ("Master", "Achieved 100 perfect ratings", "👑", 100),
]

for name, desc, icon, points in achievements:
    db.execute('''
        INSERT OR IGNORE INTO achievements (name, description, icon, points)
        VALUES (?, ?, ?, ?)
    ''', (name, desc, icon, points))

# 3. Check and unlock achievements
def check_achievements(user_id):
    # First Card
    reviews = db.execute('SELECT COUNT(*) as count FROM review_history WHERE user_id = ?', (user_id,)).fetchone()
    if reviews['count'] == 1:
        unlock_achievement(user_id, "First Card")

    # Week Streak
    streak = db.execute('''
        SELECT COUNT(DISTINCT DATE(created_at)) as days
        FROM review_history
        WHERE user_id = ? AND created_at >= datetime('now', '-7 days')
    ''', (user_id,)).fetchone()
    if streak['days'] >= 7:
        unlock_achievement(user_id, "Week Streak")

def unlock_achievement(user_id, achievement_name):
    achievement = db.execute('SELECT * FROM achievements WHERE name = ?', (achievement_name,)).fetchone()
    db.execute('''
        INSERT OR IGNORE INTO user_achievements (user_id, achievement_id)
        VALUES (?, ?)
    ''', (user_id, achievement['id']))
```

---

## Customize Templates

### Example: Dark Theme

```html
<!-- templates/learn/dashboard_dark.html -->
{% extends "base.html" %}

{% block extra_head %}
<style>
  body {
    background-color: #1a1a1a;
    color: #ffffff;
  }

  .stat-card {
    background-color: #2a2a2a;
    border: 1px solid #3a3a3a;
  }

  .stat-card .number {
    color: #60a5fa;
  }

  .btn {
    background-color: #3b82f6;
    color: white;
  }

  .btn:hover {
    background-color: #2563eb;
  }
</style>
{% endblock %}

{% block content %}
<!-- Same content as dashboard.html but with dark theme -->
<div class="dashboard dark-theme">
  ...
</div>
{% endblock %}
```

---

## Environment-Based Remixes

### Development vs Production

```python
# config.py

import os

ENV = os.getenv('FLASK_ENV', 'development')

if ENV == 'production':
    # Production config
    DEBUG = False
    HOST = '0.0.0.0'
    PORT = 80
    DATABASE = '/var/www/soulfra/soulfra.db'
    BASE_URL = 'https://soulfra.com'
else:
    # Development config
    DEBUG = True
    HOST = '127.0.0.1'
    PORT = 5001
    DATABASE = 'soulfra.db'
    BASE_URL = 'http://localhost:5001'

# app.py
from config import HOST, PORT, DEBUG

if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=DEBUG)
```

---

## Feature Flags

```python
# Enable/disable features dynamically

FEATURES = {
    'qr_codes': True,
    'practice_rooms': True,
    'widgets': True,
    'neural_networks': True,
    'achievements': False,  # Not ready yet
    'social': False,        # Coming soon
}

# In routes
@app.route('/practice/rooms')
def practice_rooms():
    if not FEATURES['practice_rooms']:
        return "Feature not available", 404

    # ... rest of route
```

---

## Common Remix Patterns

### Pattern 1: Filter by User Attribute

```python
# Get user preference
user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

if user['difficulty_preference'] == 'easy':
    cards = db.execute('SELECT * FROM learning_cards WHERE difficulty_predicted < 0.5')
elif user['difficulty_preference'] == 'hard':
    cards = db.execute('SELECT * FROM learning_cards WHERE difficulty_predicted > 0.7')
else:
    cards = db.execute('SELECT * FROM learning_cards')
```

---

### Pattern 2: Time-Based Logic

```python
from datetime import datetime, time

now = datetime.now()
current_time = now.time()

# Morning: easier cards
if current_time < time(12, 0):
    cards = get_cards_by_difficulty(user_id, max_difficulty=0.5)
# Afternoon: normal mix
elif current_time < time(18, 0):
    cards = get_cards_due(user_id)
# Evening: review cards
else:
    cards = get_previously_learned_cards(user_id)
```

---

### Pattern 3: Gamification

```python
# Award points for reviews
def review_card_with_points(user_id, card_id, quality):
    # Standard review
    result = review_card(user_id, card_id, quality)

    # Award points
    points = 0
    if quality == 5:
        points = 10
    elif quality >= 3:
        points = 5
    else:
        points = 1

    db.execute('''
        UPDATE users
        SET points = points + ?
        WHERE id = ?
    ''', (points, user_id))

    result['points_earned'] = points

    return result
```

---

## Summary

**Remix = Customize the platform for your needs**

**Key areas to remix:**
1. **Users** - Different user types, auth methods
2. **Cards** - Custom topics, difficulty, sources
3. **Queries** - Filter, sort, prioritize
4. **Templates** - Themes, layouts, components
5. **Routes** - New endpoints, custom logic
6. **APIs** - Webhooks, integrations, analytics
7. **Features** - Mix QR + Learning, Widget + Rooms, AI + Cards

**Remember:**
- Start with `hello_world.py` to understand the flow
- Run `full_flow_demo.py` to see data flow
- Test changes with `test_everything.py`
- Read existing code in `app.py` for patterns

**You can remix anything!** The platform is designed to be flexible and extensible.

---

**Created:** 2025-12-27
**Next:** Run `python3 hello_world.py` to see the complete flow!
