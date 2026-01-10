# TODO: Essential Tasks to Complete Soulfra

**Priority-ordered list of what to do next**

---

## 🎯 Priority 1: Make Cal-Riven Post as Comments (Not Separate Posts)

**Current:** Cal-Riven bridge creates separate AI analysis posts
**Wanted:** Cal-Riven should post AI analysis as COMMENTS on the original post

### What to Change
File: `cal_riven_bridge.py`

**Current code (lines 120-160):**
```python
# Creates a new POST
db.add_ai_commentary_post(
    original_post_id=post['id'],
    title=ai_title,
    slug=ai_slug,
    content=ai_content
)
```

**New code should:**
```python
# Create comment instead
from db_helpers import add_comment, create_reasoning_thread, add_reasoning_step

# 1. Create reasoning thread
thread_id = create_reasoning_thread(
    post_id=post['id'],
    initiator_user_id=soulfra_user_id,  # ID of Soulfra AI
    topic=post['title']
)

# 2. For each AI persona, add comment with reasoning
for persona_name, persona_data in analysis['perspectives'].items():
    # Get AI user ID
    ai_user = get_user_by_username(persona_name)

    # Add as comment
    add_comment(
        post_id=post['id'],
        user_id=ai_user['id'],
        content=persona_data['take']
    )

    # Track reasoning step
    add_reasoning_step(
        thread_id=thread_id,
        user_id=ai_user['id'],
        step_number=1,
        step_type='analysis',
        content=persona_data['take'],
        confidence=persona_data['confidence']
    )
```

**Testing:**
```bash
# 1. Create a new post as admin
http://localhost:5001/admin/dashboard

# 2. Run bridge
python cal_riven_bridge.py --process-id <post-id>

# 3. Check the post - should see AI comments (not separate post)
http://localhost:5001/post/<slug>
```

**Time Estimate:** 15 minutes

---

## 🎯 Priority 2: Show Categories & Tags in Post UI

**Current:** Categories and tags exist in database but not shown
**Wanted:** Display categories/tags on posts

### What to Change

#### File: `app.py` (line ~35, post route)
```python
@app.route('/post/<slug>')
def post(slug):
    post = get_post_by_slug(slug)
    comments = get_comments_for_post(post['id'])
    author = get_user_by_id(post['user_id'])

    # ADD THIS:
    categories = get_post_categories(post['id'])
    tags = get_post_tags(post['id'])

    return render_template('post.html',
                         post=post,
                         comments=comments,
                         author=author,
                         categories=categories,  # NEW
                         tags=tags)              # NEW
```

#### File: `templates/post.html` (add after title)
```html
<h1>{{ post['title'] }}</h1>

<!-- ADD THIS: -->
{% if categories %}
  <div class="categories" style="margin: 0.5rem 0;">
    {% for category in categories %}
      <a href="/category/{{ category['slug'] }}" style="background: #e6f2ff; padding: 0.3rem 0.6rem; border-radius: 4px; margin-right: 0.5rem; text-decoration: none;">
        📁 {{ category['name'] }}
      </a>
    {% endfor %}
  </div>
{% endif %}

{% if tags %}
  <div class="tags" style="margin: 0.5rem 0;">
    {% for tag in tags %}
      <a href="/tag/{{ tag['slug'] }}" style="background: #f0f0f0; padding: 0.2rem 0.5rem; border-radius: 3px; margin-right: 0.3rem; font-size: 0.9rem; text-decoration: none;">
        #{{ tag['name'] }}
      </a>
    {% endfor %}
  </div>
{% endif %}
```

**Testing:**
```bash
# Assign category to test post
sqlite3 soulfra.db "
  INSERT INTO post_categories (post_id, category_id)
  VALUES (1, 1);  -- Add 'Philosophy' category to post 1
"

# Assign tag to test post
sqlite3 soulfra.db "
  INSERT INTO post_tags (post_id, tag_id)
  VALUES (1, 1);  -- Add 'ollama' tag to post 1
"

# Visit post - should see category and tag
http://localhost:5001/post/welcome
```

**Time Estimate:** 10 minutes

---

## 🎯 Priority 3: Add Category Filtering to Homepage

**Current:** Can't filter feed by category
**Wanted:** Click category to see only posts in that category

### What to Change

#### File: `app.py` (add new route)
```python
@app.route('/category/<slug>')
def category_posts(slug):
    """Show posts filtered by category"""
    from db_helpers import get_posts_by_category, get_all_categories

    posts = get_posts_by_category(slug, limit=20)
    categories = get_all_categories()

    # Find the category name
    category = next((c for c in categories if c['slug'] == slug), None)

    return render_template('category.html',
                         posts=posts,
                         category=category,
                         categories=categories)
```

#### File: `templates/category.html` (create new file)
```html
<!DOCTYPE html>
<html>
<head>
  <title>{{ category['name'] }} - Soulfra</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
  <header>
    <nav>
      <a href="{{ url_for('index') }}">Soulfra</a>
      <div>
        <a href="{{ url_for('index') }}">All Posts</a>
        {% if session.get('user_id') %}
          <a href="{{ url_for('logout') }}">Logout</a>
        {% else %}
          <a href="{{ url_for('login') }}">Login</a>
        {% endif %}
      </div>
    </nav>
  </header>

  <main style="max-width: 900px; margin: 2rem auto; padding: 0 1rem;">
    <h1>📁 {{ category['name'] }}</h1>
    <p>{{ category['description'] }}</p>

    <div class="category-nav" style="margin: 1rem 0;">
      {% for cat in categories %}
        <a href="/category/{{ cat['slug'] }}"
           style="padding: 0.5rem 1rem; margin-right: 0.5rem; background: {% if cat['slug'] == category['slug'] %}#007bff{% else %}#f0f0f0{% endif %}; color: {% if cat['slug'] == category['slug'] %}white{% else %}black{% endif %}; text-decoration: none; border-radius: 4px;">
          {{ cat['name'] }}
        </a>
      {% endfor %}
    </div>

    {% if posts %}
      {% for post in posts %}
        <article style="margin: 2rem 0; padding: 1rem; border: 1px solid #eee; border-radius: 4px;">
          <h2><a href="/post/{{ post['slug'] }}">{{ post['title'] }}</a></h2>
          <time>{{ post['published_at'][:10] }}</time>
        </article>
      {% endfor %}
    {% else %}
      <p>No posts in this category yet.</p>
    {% endif %}
  </main>
</body>
</html>
```

**Testing:**
```bash
# Visit category page
http://localhost:5001/category/philosophy
http://localhost:5001/category/technology
```

**Time Estimate:** 15 minutes

---

## 🎯 Priority 4: Generate RSS Feed

**Current:** No RSS feed
**Wanted:** RSS feed at `/feed.xml`

### What to Change

#### File: `app.py` (add new route)
```python
from flask import Response
from datetime import datetime

@app.route('/feed.xml')
def rss_feed():
    """Generate RSS feed"""
    posts = get_posts(limit=20)

    rss_items = []
    for post in posts:
        author = get_user_by_id(post['user_id'])
        rss_items.append(f"""
    <item>
      <title>{post['title']}</title>
      <link>http://localhost:5001/post/{post['slug']}</link>
      <description>{post['content'][:200]}...</description>
      <pubDate>{post['published_at']}</pubDate>
      <author>{author['display_name']}</author>
    </item>""")

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Soulfra</title>
    <link>http://localhost:5001</link>
    <description>AI, privacy, and the future of technology</description>
    <language>en-us</language>
    {''.join(rss_items)}
  </channel>
</rss>"""

    return Response(rss, mimetype='application/rss+xml')
```

**Testing:**
```bash
# Visit RSS feed
http://localhost:5001/feed.xml

# Should see XML
```

**Time Estimate:** 10 minutes

---

## 🎯 Priority 5: Add "Show Reasoning" Toggle (Optional)

**Current:** Reasoning steps not visible
**Wanted:** Toggle to show AI reasoning chain

### What to Change

#### File: `app.py` (update post route)
```python
@app.route('/post/<slug>')
def post(slug):
    # ... existing code ...

    # ADD THIS:
    thread = get_reasoning_thread(post['id'])
    reasoning_steps = get_reasoning_steps(thread['id']) if thread else []

    return render_template('post.html',
                         # ... existing params ...
                         reasoning_thread=thread,
                         reasoning_steps=reasoning_steps)
```

#### File: `templates/post.html` (add before comments)
```html
{% if reasoning_steps %}
  <div class="reasoning-section" style="margin: 2rem 0; padding: 1rem; background: #f9f9f9; border-radius: 4px;">
    <h3>🔍 AI Reasoning Process</h3>
    <details>
      <summary style="cursor: pointer; font-weight: bold;">Show Reasoning Steps ({{ reasoning_steps|length }})</summary>
      <div style="margin-top: 1rem;">
        {% for step in reasoning_steps %}
          <div style="margin: 1rem 0; padding: 0.5rem; border-left: 3px solid #007bff;">
            <strong>Step {{ step['step_number'] }}</strong> - {{ step['display_name'] }}
            <span style="color: #666;">({{ step['step_type'] }}, confidence: {{ (step['confidence'] * 100)|int }}%)</span>
            <p>{{ step['content'] }}</p>
          </div>
        {% endfor %}
      </div>
    </details>
  </div>
{% endif %}
```

**Testing:**
```bash
# After updating Cal-Riven bridge (Priority 1)
# Visit post with AI analysis
http://localhost:5001/post/welcome

# Click "Show Reasoning Steps"
```

**Time Estimate:** 15 minutes

---

## Summary

| Priority | Task | Time | Status |
|----------|------|------|--------|
| 1 | Cal-Riven posts as comments | 15 min | ⏳ TODO |
| 2 | Show categories/tags in UI | 10 min | ⏳ TODO |
| 3 | Category filtering | 15 min | ⏳ TODO |
| 4 | RSS feed | 10 min | ⏳ TODO |
| 5 | Show reasoning toggle | 15 min | ⏳ TODO (optional) |
| **TOTAL** | | **65 min** | **~1 hour** |

---

**After completing these 5 tasks, you'll have:**
- ✅ AI personas commenting on posts (not creating separate posts)
- ✅ Categories & tags visible
- ✅ Filter posts by category
- ✅ RSS feed for external readers
- ✅ (Optional) Visible AI reasoning chains

**That's the complete Soulfra Reasoning Platform!**
