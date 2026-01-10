# Template Data Flow - How "It Gets Filled Out As We Move Along"

**Created:** 2025-12-27
**Status:** ✅ COMPLETE EXPLANATION

---

## The Big Question

> "How the fuck does this work and basically get filled out as we move along?"

**Answer:** Flask routes query the database, create Python dictionaries, pass them to Jinja2 templates, which replace `{{ variable }}` placeholders with actual data, and send HTML to the browser.

---

## The Complete Flow (5 Steps)

### Visual Overview

```
┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐
│  User    │  →   │  Flask   │  →   │ Database │  →   │ Template │  →   │  Browser │
│          │      │  Route   │      │  Query   │      │  Jinja2  │      │   HTML   │
└──────────┘      └──────────┘      └──────────┘      └──────────┘      └──────────┘
   "Visit           /learn           SELECT            {{ stats           <div>12
    /learn"         function         ...               .due_today }}      </div>
```

---

## Step-by-Step Example: Learning Dashboard

### 1. User Visits URL

```
User types: http://localhost:5001/learn
Browser sends: GET /learn HTTP/1.1
```

### 2. Flask Route Handles Request

**File:** `app.py:11751`

```python
@app.route('/learn')
def learn_dashboard():
    """Learning dashboard - Anki-style spaced repetition"""
    user_id = session.get('user_id', 1)  # Who is logged in?

    from anki_learning_system import get_learning_stats

    stats = get_learning_stats(user_id)  # ← Call helper function

    return render_template('learn/dashboard.html',  # ← Pass data to template
                         stats=stats,
                         tutorials=[])
```

**What happens:**
- Route function `learn_dashboard()` runs
- Gets `user_id` from session (who's logged in)
- Calls `get_learning_stats(user_id)` to fetch data
- Passes `stats` dict to template
- Returns rendered HTML

### 3. Database Query Runs

**File:** `anki_learning_system.py:536`

```python
def get_learning_stats(user_id: int = 1) -> Dict:
    """Get learning statistics for a user"""
    conn = get_db()

    # Query 1: Overall stats
    overall = conn.execute('''
        SELECT
            COUNT(DISTINCT c.id) as total_cards,
            COUNT(DISTINCT CASE WHEN p.status = 'new' THEN c.id END) as new_cards,
            COUNT(DISTINCT CASE WHEN p.status = 'learning' THEN c.id END) as learning_cards,
            AVG(p.ease_factor) as avg_ease,
            MAX(p.streak) as longest_streak
        FROM learning_cards c
        LEFT JOIN learning_progress p ON c.id = p.card_id AND p.user_id = ?
    ''', (user_id,)).fetchone()

    # Query 2: Cards due today
    due_today = conn.execute('''
        SELECT COUNT(*) as count
        FROM learning_progress
        WHERE user_id = ? AND next_review <= datetime('now')
    ''', (user_id,)).fetchone()

    # Query 3: Recent accuracy
    recent_accuracy = conn.execute('''
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN quality >= 3 THEN 1 ELSE 0 END) as correct
        FROM review_history
        WHERE user_id = ?
        AND reviewed_at >= datetime('now', '-7 days')
    ''', (user_id,)).fetchone()

    accuracy = (recent_accuracy['correct'] / max(1, recent_accuracy['total']) * 100) if recent_accuracy['total'] > 0 else 0

    # Return Python dictionary
    return {
        'total_cards': overall['total_cards'],
        'new_cards': overall['new_cards'],
        'learning_cards': overall['learning_cards'],
        'young_cards': overall['young_cards'],
        'mature_cards': overall['mature_cards'],
        'due_today': due_today['count'],
        'avg_ease': overall['avg_ease'] or 2.5,
        'longest_streak': overall['longest_streak'] or 0,
        'recent_accuracy': accuracy
    }
```

**What happens:**
- Function queries `learning_cards`, `learning_progress`, `review_history` tables
- Filters by `user_id` (so each user sees their own data)
- Calculates stats (total cards, due cards, accuracy, etc.)
- Returns Python dict: `{'due_today': 12, 'total_cards': 12, ...}`

### 4. Template Renders with Data

**File:** `templates/learn/dashboard.html:16`

```jinja2
<!-- Quick Stats Grid -->
<div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
    <div class="bg-white rounded-lg shadow p-6 text-center">
        <div class="text-4xl font-bold text-red-600">{{ stats.due_today }}</div>
        <div class="text-sm text-gray-600 mt-2">Due Today</div>
    </div>

    <div class="bg-white rounded-lg shadow p-6 text-center">
        <div class="text-4xl font-bold text-indigo-600">{{ stats.total_cards }}</div>
        <div class="text-sm text-gray-600 mt-2">Total Cards</div>
    </div>

    <div class="bg-white rounded-lg shadow p-6 text-center">
        <div class="text-4xl font-bold text-green-600">{{ stats.longest_streak }}</div>
        <div class="text-sm text-gray-600 mt-2">Longest Streak</div>
    </div>

    <div class="bg-white rounded-lg shadow p-6 text-center">
        <div class="text-4xl font-bold text-purple-600">{{ "%.1f"|format(stats.recent_accuracy) }}%</div>
        <div class="text-sm text-gray-600 mt-2">Accuracy (7d)</div>
    </div>
</div>
```

**What happens:**
- Jinja2 template engine processes `{{ variable }}` placeholders
- `{{ stats.due_today }}` → Replaced with `12` (from Python dict)
- `{{ stats.total_cards }}` → Replaced with `12`
- `{{ "%.1f"|format(stats.recent_accuracy) }}` → Formats number as `85.3%`

**Rendered HTML:**

```html
<div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
    <div class="bg-white rounded-lg shadow p-6 text-center">
        <div class="text-4xl font-bold text-red-600">12</div>
        <div class="text-sm text-gray-600 mt-2">Due Today</div>
    </div>

    <div class="bg-white rounded-lg shadow p-6 text-center">
        <div class="text-4xl font-bold text-indigo-600">12</div>
        <div class="text-sm text-gray-600 mt-2">Total Cards</div>
    </div>

    <!-- ... more cards ... -->
</div>
```

### 5. Browser Displays HTML

```
User sees:
┌────────────────────────────────────────┐
│        📚 Learning Dashboard           │
│                                        │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐
│  │  12  │  │  12  │  │   0  │  │ 0.0% │
│  │ Due  │  │Total │  │Streak│  │Accur.│
│  └──────┘  └──────┘  └──────┘  └──────┘
│                                        │
│  [Start Review Session →]              │
└────────────────────────────────────────┘
```

---

## How Different Users See Different Data

### User 1 (admin) - Has cards initialized

```python
# Database state for user_id=1
learning_progress:
  - user_id: 1, card_id: 1, next_review: "2025-12-27 08:00"
  - user_id: 1, card_id: 2, next_review: "2025-12-27 08:00"
  - user_id: 1, card_id: 3, next_review: "2025-12-27 08:00"
  ... (12 cards total)

# Query result for user_id=1
stats = {
  'due_today': 12,  # ← 12 cards where next_review <= now
  'total_cards': 12
}

# Template renders
<div>12</div>  # ← Shows "12 due cards"
```

### User 2 (soul_tester) - No cards initialized

```python
# Database state for user_id=2
learning_progress:
  (empty - no rows for user_id=2)

# Query result for user_id=2
stats = {
  'due_today': 0,  # ← No cards assigned to this user
  'total_cards': 12  # ← Cards exist, but not assigned
}

# Template renders
<div>0</div>  # ← Shows "0 due cards"
```

**Key Point:** Same route, same template, **different SQL results** based on `user_id`.

---

## How Templates "Get Filled Out As We Move Along"

### Example: Review Session Updates

**Initial State (before review):**

```python
# Database
learning_progress:
  - card_id: 1, repetitions: 0, ease_factor: 2.5, next_review: "2025-12-27 08:00"

# Template shows
<div>12 cards due</div>
<div>0% accuracy</div>
```

**User Reviews Card:**

```javascript
// User clicks rating button
fetch('/api/learn/answer', {
  method: 'POST',
  body: JSON.stringify({
    card_id: 1,
    quality: 4  // User rated "easy"
  })
})
```

**Backend Updates Database:**

```python
@app.route('/api/learn/answer', methods=['POST'])
def submit_answer():
    card_id = request.json['card_id']
    quality = request.json['quality']
    user_id = session['user_id']

    # SM-2 algorithm calculates new values
    reps, ease, interval = sm2_schedule(quality, ...)

    # Update database
    db.execute('''
        UPDATE learning_progress
        SET repetitions = ?, ease_factor = ?, interval_days = ?,
            next_review = datetime('now', '+' || ? || ' days')
        WHERE card_id = ? AND user_id = ?
    ''', (reps, ease, interval, interval, card_id, user_id))

    # Save to review history
    db.execute('''
        INSERT INTO review_history (card_id, user_id, quality, reviewed_at)
        VALUES (?, ?, ?, datetime('now'))
    ''', (card_id, user_id, quality))

    db.commit()
```

**Updated State (after review):**

```python
# Database NOW
learning_progress:
  - card_id: 1, repetitions: 1, ease_factor: 2.6, next_review: "2025-12-28"  # ← Updated!

review_history:
  - card_id: 1, user_id: 1, quality: 4, reviewed_at: "2025-12-27 10:15"  # ← New row!

# Next time user visits /learn, template shows
<div>11 cards due</div>  # ← Decreased by 1
<div>100% accuracy</div>  # ← 1/1 correct
```

**That's how it "gets filled out as we move along"!**

---

## Personalization: Different Stories Based on User & Quiz Results

### Scenario: Adaptive Learning Paths

```python
def get_next_card(user_id):
    """Show different cards based on user's quiz results"""

    # Get user's review history
    struggle_topics = db.execute('''
        SELECT c.topic, AVG(r.quality) as avg_quality
        FROM review_history r
        JOIN learning_cards c ON r.card_id = c.id
        WHERE r.user_id = ?
        GROUP BY c.topic
        HAVING avg_quality < 3  -- Topics where user struggles
        ORDER BY avg_quality ASC
        LIMIT 1
    ''', (user_id,)).fetchone()

    if struggle_topics:
        # User struggling with topic → Show more cards from that topic
        card = db.execute('''
            SELECT * FROM learning_cards
            WHERE topic = ?
            ORDER BY difficulty ASC
            LIMIT 1
        ''', (struggle_topics['topic'],)).fetchone()
    else:
        # User doing well → Show next card normally
        card = db.execute('''
            SELECT * FROM learning_cards
            WHERE next_review <= datetime('now')
            LIMIT 1
        ''').fetchone()

    return card
```

**Result:** User who struggles with Python gets more Python cards, user who excels gets variety.

### Scenario: Story Branching in Games

```python
def get_story_scene(user_id, game_id):
    """Different story based on user personality + game state"""

    # Get user's personality
    user = db.execute('SELECT personality_profile FROM users WHERE id = ?', (user_id,)).fetchone()

    # Get game state
    state = db.execute('SELECT turn_number, board_state FROM game_state WHERE game_id = ?', (game_id,)).fetchone()

    # Branch story
    if 'analytical' in user['personality_profile']:
        if state['turn_number'] < 5:
            return "You notice mathematical patterns in the ancient ruins..."
        else:
            return "The equations finally click - you've solved the puzzle!"
    elif 'creative' in user['personality_profile']:
        if state['turn_number'] < 5:
            return "The colors and shapes inspire a wild idea..."
        else:
            return "Your artistic vision reveals a hidden path!"
    else:
        return "You explore the area carefully..."
```

**Result:** Same game, different narrative based on user's personality profile.

---

## Common Template Patterns

### 1. **Conditional Rendering**

```jinja2
{% if stats.due_today > 0 %}
  <a href="/learn/review">Start Review Session</a>
{% else %}
  <div>All caught up! No cards due.</div>
{% endif %}
```

**Python equivalent:**

```python
if stats['due_today'] > 0:
    print("<a href='/learn/review'>Start Review Session</a>")
else:
    print("<div>All caught up! No cards due.</div>")
```

### 2. **Loops**

```jinja2
<ul>
{% for card in cards %}
  <li>{{ card.question }}</li>
{% endfor %}
</ul>
```

**Python equivalent:**

```python
print("<ul>")
for card in cards:
    print(f"<li>{card['question']}</li>")
print("</ul>")
```

### 3. **Filters (Formatting)**

```jinja2
{{ "%.1f"|format(stats.recent_accuracy) }}%  <!-- Output: "85.3%" -->
{{ card.created_at|datetime }}  <!-- Format datetime -->
{{ text[:100] }}  <!-- Truncate to 100 chars -->
```

### 4. **Variable Access**

```jinja2
{{ stats.due_today }}  <!-- Dict key access: stats['due_today'] -->
{{ user.username }}    <!-- Dict key access: user['username'] -->
{{ cards|length }}     <!-- List length: len(cards) -->
```

---

## Debugging Template Issues

### Problem: "Variable not showing"

**Symptom:** Template shows `{{ stats.due_today }}` literally in HTML

**Cause:** Variable not passed from route

**Fix:**

```python
# WRONG
return render_template('dashboard.html')  # ← stats missing!

# RIGHT
stats = get_learning_stats(user_id)
return render_template('dashboard.html', stats=stats)
```

### Problem: "AttributeError: 'NoneType' object has no attribute 'X'"

**Symptom:** Template crashes with AttributeError

**Cause:** Database query returned None

**Fix:**

```jinja2
<!-- WRONG -->
{{ user.username }}  <!-- Crashes if user is None -->

<!-- RIGHT -->
{% if user %}
  {{ user.username }}
{% else %}
  Guest
{% endif %}
```

Or use default filter:

```jinja2
{{ user.username|default('Guest') }}
```

### Problem: "Template shows old data"

**Symptom:** Made database changes but template still shows old values

**Cause:** Flask cached the response or you're looking at wrong data

**Debug:**

```python
@app.route('/learn')
def learn_dashboard():
    stats = get_learning_stats(user_id)

    # Add debug print
    print(f"DEBUG: stats = {stats}")  # ← Check what's being passed

    return render_template('learn/dashboard.html', stats=stats)
```

Then check terminal output when visiting page.

---

## Complete Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                       INITIAL PAGE LOAD                         │
└─────────────────────────────────────────────────────────────────┘

1. User → Browser
   GET http://localhost:5001/learn

2. Browser → Flask Server
   GET /learn HTTP/1.1
   Cookie: session=abc123

3. Flask Server → Route Function
   @app.route('/learn')
   def learn_dashboard():
       user_id = session.get('user_id', 1)  # ← Extract from cookie

4. Route → Database
   SELECT ... FROM learning_progress WHERE user_id = 1
   (Returns: due_today=12, total_cards=12, ...)

5. Route → Template Engine
   render_template('dashboard.html', stats={...})

6. Template Engine → HTML
   {{ stats.due_today }} → 12
   {{ stats.total_cards }} → 12

7. Flask → Browser
   HTTP 200 OK
   Content-Type: text/html
   <html><body>...<div>12</div>...</body></html>

8. Browser → User
   Renders: Dashboard with "12 cards due"

┌─────────────────────────────────────────────────────────────────┐
│                     USER INTERACTION (AJAX)                     │
└─────────────────────────────────────────────────────────────────┘

9. User → Browser
   Clicks "Rate: Easy (4)"

10. Browser → JavaScript
    fetch('/api/learn/answer', {
      method: 'POST',
      body: {card_id: 1, quality: 4}
    })

11. JavaScript → Flask Server
    POST /api/learn/answer
    Body: {"card_id": 1, "quality": 4}

12. Flask → Database
    UPDATE learning_progress SET ... WHERE card_id=1
    INSERT INTO review_history ...

13. Flask → JavaScript
    HTTP 200 OK
    Body: {"success": true, "next_card": {...}}

14. JavaScript → DOM
    Updates page without reload:
    - Progress bar: 33% → 66%
    - Card counter: 1/3 → 2/3
    - Loads next card

15. User sees updated page INSTANTLY (no refresh!)
```

---

## Key Takeaways

1. **Templates are NOT broken** - They're dynamic placeholders waiting for data

2. **Data flow is predictable:**
   - URL → Route function → Database query → Python dict → Template → HTML

3. **Personalization happens via SQL:**
   - `WHERE user_id = ?` gives each user their own data
   - Different users = Different queries = Different HTML

4. **Templates "get filled out" when:**
   - Route calls `render_template()` with data dict
   - Jinja2 replaces `{{ variable }}` with actual values
   - Result sent to browser

5. **"As we move along" means:**
   - User actions (clicks, reviews) → API calls → Database updates
   - Next page load → New query → Updated data → Updated template

6. **Stories personalize via:**
   - User table: `personality_profile` column
   - Review history: `quality` ratings
   - Game state: `turn_number`, `board_state`

---

## Try It Yourself

### Test 1: See Template Rendering

```bash
# 1. Start server
python3 app.py

# 2. Visit in browser
http://localhost:5001/learn

# 3. View page source (Cmd+U or Ctrl+U)
# Look for: <div class="text-4xl font-bold">12</div>
# That's the RENDERED template!
```

### Test 2: See Different Users

```python
# In Python shell
from database import get_db
from anki_learning_system import get_learning_stats

# User 1 (has cards)
print(get_learning_stats(user_id=1))
# → {'due_today': 12, ...}

# User 2 (no cards)
print(get_learning_stats(user_id=2))
# → {'due_today': 0, ...}

# Same function, different data!
```

### Test 3: See Data Update

```bash
# 1. Check current state
curl http://localhost:5001/learn | grep "due_today"
# → Shows: 12

# 2. Answer a card (simulate review)
python3 -c "
from database import get_db
db = get_db()
db.execute('''
  UPDATE learning_progress
  SET next_review = datetime('now', '+1 day')
  WHERE card_id = 1 AND user_id = 1
''')
db.commit()
"

# 3. Refresh page
curl http://localhost:5001/learn | grep "due_today"
# → Shows: 11  (decreased by 1!)
```

---

**Created:** 2025-12-27
**For:** Understanding how Soulfra templates work
**See also:**
- `demo_user_journey.py` - Interactive demo
- `ANKI_LEARNING_API_DOCS.md` - API documentation
- `PLATFORM_ARCHITECTURE.md` - Overall system design
