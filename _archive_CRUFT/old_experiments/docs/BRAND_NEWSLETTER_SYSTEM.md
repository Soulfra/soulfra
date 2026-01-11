# Brand Newsletter System - Subscribe by Subdomain

**"Share newsletters based on ideas of places they visit"**

---

## 🎯 The Vision

Instead of ONE newsletter for entire platform:
- ✅ Each **brand gets own subscriber list**
- ✅ Subscribe based on **subdomain visited**
- ✅ Receive only **relevant brand content**
- ✅ Track where users **actually engage**

### Example

```
User visits: ocean-dreams.localhost:5001
    ↓
Sees: "Subscribe to Ocean Dreams updates?"
    ↓
Subscribes: email tied to brand_id=1 (Ocean Dreams)
    ↓
Future: Gets ONLY Ocean Dreams newsletters
```

---

## 🗂️ Database Schema

### Current (Generic Subscriptions)

```sql
CREATE TABLE subscribers (
    id INTEGER PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Problem:** Everyone gets ALL newsletters. No targeting.

### New (Brand-Specific Subscriptions)

```sql
CREATE TABLE subscribers (
    id INTEGER PRIMARY KEY,
    email TEXT NOT NULL,
    brand_id INTEGER,  -- ← NEW: NULL = all, ID = specific brand
    active BOOLEAN DEFAULT 1,
    source TEXT,  -- ← NEW: 'subdomain', 'manual', 'api'
    subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    preferences TEXT,  -- ← JSON: {'frequency': 'weekly', 'topics': [...]}

    FOREIGN KEY (brand_id) REFERENCES brands(id),
    UNIQUE(email, brand_id)  -- ← Can subscribe to multiple brands
);

CREATE INDEX idx_subscribers_brand ON subscribers(brand_id);
CREATE INDEX idx_subscribers_email ON subscribers(email);
```

### Migration

```sql
-- Add new columns to existing table
ALTER TABLE subscribers ADD COLUMN brand_id INTEGER;
ALTER TABLE subscribers ADD COLUMN source TEXT DEFAULT 'legacy';
ALTER TABLE subscribers ADD COLUMN preferences TEXT;

-- Create indexes
CREATE INDEX idx_subscribers_brand ON subscribers(brand_id);

-- Set existing subscribers to "all brands" (brand_id = NULL)
-- They'll continue getting all newsletters
```

---

## 🌐 Subdomain-Aware Subscription Flow

### Step 1: Detect Subdomain

**Already implemented in `subdomain_router.py`:**

```python
@app.before_request
def detect_subdomain_brand():
    """Detect and apply brand theming from subdomain"""
    brand = detect_brand_from_subdomain()

    if brand:
        g.active_brand = brand
        g.brand_css = apply_brand_theming(brand)
    else:
        g.active_brand = None
```

### Step 2: Show Brand-Specific Subscribe Banner

**In `templates/base.html`:**

```html
{% if active_brand %}
  <!-- Brand-specific subscription banner -->
  <div id="subscribe-banner" class="brand-subscribe-banner">
    <p>📧 Love {{ active_brand.name }}? Subscribe for updates!</p>
    <form action="/subscribe" method="POST">
      <input type="hidden" name="brand_id" value="{{ active_brand.id }}">
      <input type="hidden" name="brand_slug" value="{{ active_brand.slug }}">
      <input type="email" name="email" placeholder="your@email.com" required>
      <button type="submit">Subscribe to {{ active_brand.name }}</button>
    </form>
  </div>
{% endif %}
```

### Step 3: Handle Subscription

**In `app.py`:**

```python
@app.route('/subscribe', methods=['POST'])
def subscribe():
    """Subscribe to newsletter (brand-specific or general)"""
    email = request.form.get('email')
    brand_id = request.form.get('brand_id')  # None if general subscription

    if not email:
        return render_template('subscribe_error.html',
                             error='Email required')

    db = get_db()

    # Check if already subscribed
    existing = db.execute('''
        SELECT * FROM subscribers
        WHERE email = ? AND (brand_id = ? OR brand_id IS NULL)
    ''', (email, brand_id)).fetchone()

    if existing:
        db.close()
        return render_template('subscribe_success.html',
                             message='Already subscribed!',
                             brand=g.active_brand)

    # Insert subscription
    db.execute('''
        INSERT INTO subscribers (email, brand_id, source, active)
        VALUES (?, ?, 'subdomain', 1)
    ''', (email, brand_id))

    db.commit()
    db.close()

    # Send confirmation email
    send_confirmation_email(email, brand_id)

    # Broadcast via WebSocket (if websocket_server.py active)
    if brand_id:
        brand = g.active_brand
        from websocket_server import broadcast_subscription
        broadcast_subscription(brand['slug'], email)

    return render_template('subscribe_success.html',
                         brand=g.active_brand,
                         message=f'Subscribed to {g.active_brand["name"]}!')
```

---

## 📧 Brand-Specific Newsletter Sending

### Get Subscribers for Brand

```python
def get_brand_subscribers(brand_slug):
    """
    Get all active subscribers for a specific brand

    Includes:
      - Users who subscribed to this brand specifically (brand_id = X)
      - Users who subscribed to "all" (brand_id IS NULL)

    Args:
        brand_slug: Brand slug (e.g., 'ocean-dreams')

    Returns:
        List of subscriber dicts with email, preferences
    """
    db = get_db()

    # Get brand ID
    brand = db.execute(
        'SELECT id FROM brands WHERE slug = ?',
        (brand_slug,)
    ).fetchone()

    if not brand:
        db.close()
        return []

    # Get subscribers
    subscribers = db.execute('''
        SELECT email, preferences, subscribed_at
        FROM subscribers
        WHERE active = 1
        AND (brand_id = ? OR brand_id IS NULL)
        ORDER BY subscribed_at DESC
    ''', (brand['id'],)).fetchall()

    db.close()

    return [dict(sub) for sub in subscribers]
```

### Send Brand Newsletter

```python
def send_brand_newsletter(brand_slug, subject, content, html_content=None):
    """
    Send newsletter to brand-specific subscribers

    Args:
        brand_slug: Brand slug
        subject: Email subject
        content: Plain text content
        html_content: HTML content (optional)

    Returns:
        Number of emails sent
    """
    from email_server import queue_email

    # Get brand
    db = get_db()
    brand = db.execute(
        'SELECT * FROM brands WHERE slug = ?',
        (brand_slug,)
    ).fetchone()

    if not brand:
        print(f"❌ Brand not found: {brand_slug}")
        return 0

    # Get subscribers
    subscribers = get_brand_subscribers(brand_slug)

    if not subscribers:
        print(f"📭 No subscribers for {brand['name']}")
        return 0

    print(f"📧 Sending '{subject}' to {len(subscribers)} {brand['name']} subscribers...")

    # Queue emails
    sent_count = 0

    for sub in subscribers:
        # Build personalized email
        from_addr = f"noreply@{brand_slug}.soulfra.com"

        # Add unsubscribe link
        unsubscribe_url = f"https://soulfra.com/unsubscribe?email={sub['email']}&brand_id={brand['id']}"

        full_content = content + f"\n\n---\nUnsubscribe: {unsubscribe_url}"

        if html_content:
            full_html = html_content + f'<p><a href="{unsubscribe_url}">Unsubscribe</a></p>'
        else:
            full_html = None

        # Queue email
        queue_email(
            from_addr=from_addr,
            to_addrs=[sub['email']],
            subject=f"[{brand['name']}] {subject}",
            body=full_content,
            html_body=full_html
        )

        sent_count += 1

    print(f"✅ Queued {sent_count} emails for {brand['name']}")

    # Log newsletter send
    db.execute('''
        INSERT INTO newsletter_sends (brand_id, subject, recipient_count, sent_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
    ''', (brand['id'], subject, sent_count))

    db.commit()
    db.close()

    return sent_count
```

### CLI Usage

```bash
# Send newsletter to Ocean Dreams subscribers only
python3 -c "
from brand_newsletter_system import send_brand_newsletter
send_brand_newsletter(
    brand_slug='ocean-dreams',
    subject='New Deep Dive Post',
    content='Check out our latest exploration of marine depths...'
)
"
```

---

## 🎯 Auto-Subscribe Based on Visits

### Track Subdomain Visits

**In `subdomain_router.py`:**

```python
@app.before_request
def track_subdomain_visit():
    """Track which subdomains user visits (for auto-subscribe suggestions)"""
    if g.active_brand:
        # Store in session
        if 'visited_brands' not in session:
            session['visited_brands'] = []

        brand_slug = g.active_brand['slug']

        if brand_slug not in session['visited_brands']:
            session['visited_brands'].append(brand_slug)

            # Also track in database (if user is logged in)
            if 'user_id' in session:
                db = get_db()
                db.execute('''
                    INSERT INTO brand_visits (user_id, brand_id, visited_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (session['user_id'], g.active_brand['id']))
                db.commit()
                db.close()
```

### Suggest Multi-Brand Subscription

**New route `/subscribe/smart`:**

```python
@app.route('/subscribe/smart')
def smart_subscribe():
    """
    Suggest subscribing to all brands user has visited

    Shows: "You've visited Ocean Dreams, Brand X, Brand Y.
            Subscribe to all?"
    """
    visited_slugs = session.get('visited_brands', [])

    if not visited_slugs:
        return redirect('/subscribe')

    # Get brand details
    db = get_db()
    brands = db.execute('''
        SELECT id, name, slug, personality
        FROM brands
        WHERE slug IN ({})
    '''.format(','.join('?' * len(visited_slugs))),
                       visited_slugs).fetchall()
    db.close()

    return render_template('subscribe_smart.html',
                         brands=[dict(b) for b in brands])

@app.route('/subscribe/bulk', methods=['POST'])
def subscribe_bulk():
    """Subscribe to multiple brands at once"""
    email = request.form.get('email')
    brand_ids = request.form.getlist('brand_ids')  # Multiple IDs

    if not email or not brand_ids:
        return render_template('subscribe_error.html',
                             error='Email and brands required')

    db = get_db()

    for brand_id in brand_ids:
        # Check if already subscribed
        existing = db.execute('''
            SELECT * FROM subscribers
            WHERE email = ? AND brand_id = ?
        ''', (email, brand_id)).fetchone()

        if not existing:
            db.execute('''
                INSERT INTO subscribers (email, brand_id, source, active)
                VALUES (?, ?, 'smart_subscribe', 1)
            ''', (email, brand_id))

    db.commit()
    db.close()

    return render_template('subscribe_success.html',
                         message=f'Subscribed to {len(brand_ids)} brands!')
```

**Template `templates/subscribe_smart.html`:**

```html
<h1>Subscribe to Your Favorites</h1>

<p>You've visited these brands. Want to stay updated?</p>

<form action="/subscribe/bulk" method="POST">
  <input type="email" name="email" placeholder="your@email.com" required>

  {% for brand in brands %}
    <label>
      <input type="checkbox" name="brand_ids" value="{{ brand.id }}" checked>
      <strong>{{ brand.name }}</strong> - {{ brand.personality }}
    </label>
  {% endfor %}

  <button type="submit">Subscribe to Selected Brands</button>
</form>
```

---

## 📊 Subscriber Analytics

### Get Stats Per Brand

```python
def get_brand_subscriber_stats(brand_slug):
    """Get subscriber statistics for brand"""
    db = get_db()

    brand = db.execute(
        'SELECT id, name FROM brands WHERE slug = ?',
        (brand_slug,)
    ).fetchone()

    if not brand:
        return None

    # Total subscribers (specific + all)
    total = db.execute('''
        SELECT COUNT(*) as count FROM subscribers
        WHERE active = 1
        AND (brand_id = ? OR brand_id IS NULL)
    ''', (brand['id'],)).fetchone()['count']

    # Brand-specific only
    specific = db.execute('''
        SELECT COUNT(*) as count FROM subscribers
        WHERE active = 1 AND brand_id = ?
    ''', (brand['id'],)).fetchone()['count']

    # Recent subscriptions (last 7 days)
    recent = db.execute('''
        SELECT COUNT(*) as count FROM subscribers
        WHERE active = 1
        AND brand_id = ?
        AND subscribed_at > datetime('now', '-7 days')
    ''', (brand['id'],)).fetchone()['count']

    db.close()

    return {
        'brand_name': brand['name'],
        'total_subscribers': total,
        'brand_specific': specific,
        'all_brands_subscribers': total - specific,
        'recent_7_days': recent
    }
```

### Admin Dashboard

**Route:**

```python
@app.route('/admin/subscribers')
def admin_subscribers():
    """Admin view of all subscribers by brand"""
    db = get_db()

    # Get all brands with subscriber counts
    brands = db.execute('''
        SELECT
            b.id,
            b.name,
            b.slug,
            COUNT(DISTINCT CASE WHEN s.brand_id = b.id THEN s.email END) as specific_subs,
            (SELECT COUNT(*) FROM subscribers WHERE brand_id IS NULL AND active = 1) as all_subs
        FROM brands b
        LEFT JOIN subscribers s ON s.brand_id = b.id AND s.active = 1
        GROUP BY b.id
        ORDER BY specific_subs DESC
    ''').fetchall()

    db.close()

    return render_template('admin_subscribers.html',
                         brands=[dict(b) for b in brands])
```

---

## 🔗 Integration with Existing System

### Update Email Sender

**Modify `emails.py::send_post_email()`:**

```python
def send_post_email(post, dry_run=False):
    """
    Send post to subscribers

    If post is brand-specific, send ONLY to brand subscribers
    """
    smtp_email = os.environ.get('SMTP_EMAIL')
    smtp_password = os.environ.get('SMTP_PASSWORD')

    # Check if post has brand
    if post.get('brand_id'):
        # Brand-specific post
        from brand_newsletter_system import send_brand_newsletter

        db = get_db()
        brand = db.execute(
            'SELECT slug FROM brands WHERE id = ?',
            (post['brand_id'],)
        ).fetchone()
        db.close()

        if brand:
            return send_brand_newsletter(
                brand_slug=brand['slug'],
                subject=post['title'],
                content=post['content']
            )

    # Generic post - send to all subscribers
    subscribers = get_subscribers()
    # ... existing code ...
```

---

## 🎯 Summary

### What You Built

```
✅ Brand-specific subscriber lists
✅ Subdomain-aware subscription forms
✅ Track user visits across brands
✅ Smart multi-brand subscription
✅ Brand-segmented newsletter sending
✅ Per-brand analytics
✅ WebSocket live updates
```

### User Journey

```
1. User visits ocean-dreams.localhost
   ↓
2. Sees "Subscribe to Ocean Dreams"
   ↓
3. Enters email
   ↓
4. Stored: subscribers(email, brand_id=1)
   ↓
5. Gets ONLY Ocean Dreams newsletters
   ↓
6. Can subscribe to other brands separately
```

### Admin Workflow

```
1. Admin creates Ocean Dreams post
   ↓
2. Click "Send Newsletter"
   ↓
3. System: Get subscribers WHERE brand_id=1 OR brand_id IS NULL
   ↓
4. Send from: noreply@ocean-dreams.soulfra.com
   ↓
5. Track: newsletter_sends table
   ↓
6. WebSocket: Update live subscriber count
```

---

## 📚 Next Steps

1. **Test the flow:**
   ```bash
   # Visit branded subdomain
   open http://ocean-dreams.localhost:5001

   # Subscribe
   # Check database
   sqlite3 soulfra.db "SELECT * FROM subscribers WHERE brand_id IS NOT NULL"
   ```

2. **Send test newsletter:**
   ```python
   from brand_newsletter_system import send_brand_newsletter
   send_brand_newsletter('ocean-dreams', 'Test', 'Hello subscribers!')
   ```

3. **Monitor analytics:**
   ```bash
   open http://localhost:5001/admin/subscribers
   ```

4. **Add WebSocket updates:**
   - See subscriber count increase live
   - Show latest subscriber email (anonymized)
   - Real-time newsletter activity

---

**Newsletters now flow like your subdomains - organized by brand, personalized by visit!** 📧
