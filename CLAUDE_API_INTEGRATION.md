# Claude API Integration

**How to force Claude to auto-generate Soulfra newsletter content**

---

## Setup

```bash
pip install anthropic
```

Create `config_secrets.py`:
```python
CLAUDE_API_KEY = "sk-ant-api03-..."  # From console.anthropic.com
```

---

## Basic Usage

```python
from anthropic import Anthropic

client = Anthropic(api_key="YOUR_API_KEY")

def generate_post_with_claude(brand_slug, topic):
    """Generate a blog post using Claude"""

    # Get brand personality from database
    brand_personality = get_brand_personality(brand_slug)

    prompt = f"""
    You are writing for the {brand_slug} brand.
    Brand personality: {brand_personality}

    Topic: {topic}

    Write a 500-word blog post in the brand's voice.
    Format as markdown with ## headers.
    """

    message = client.messages.create(
        model="claude-sonnet-4",
        max_tokens=2000,
        messages=[{
            "role": "user",
            "content": prompt
        }]
    )

    return message.content[0].text

# Usage
post = generate_post_with_claude("deathtodata", "privacy vs surveillance")
print(post)
```

---

## Auto-Post to Database

```python
import sqlite3
from datetime import datetime

def save_claude_post(brand_slug, title, content):
    """Save Claude-generated post to database"""

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    # Get brand ID
    cursor.execute("SELECT id FROM brands WHERE slug = ?", (brand_slug,))
    brand_id = cursor.fetchone()[0]

    # Create post
    slug = title.lower().replace(' ', '-').replace(',', '')
    cursor.execute("""
        INSERT INTO posts (user_id, title, slug, content, published_at, brand_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        14,  # Claude AI user ID
        title,
        slug,
        content,
        datetime.now().isoformat(),
        brand_id
    ))

    post_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return post_id

# Full flow
post_content = generate_post_with_claude("deathtodata", "data privacy")
post_id = save_claude_post("deathtodata", "Why Privacy Matters", post_content)
print(f"✓ Post #{post_id} created by Claude")
```

---

## Terminal Command

```bash
python3 force_claude_write.py --brand deathtodata --topic "privacy"
# ✓ Post #26 created: "Why Privacy Matters in 2025"
```

---

## Daily Auto-Generation

```python
# cron_claude_daily.py
import schedule
import time
from config_secrets import CLAUDE_API_KEY

topics = {
    "deathtodata": ["privacy", "encryption", "surveillance", "data rights"],
    "calriven": ["AI", "neural networks", "architecture", "Python"],
    "soulfra": ["platforms", "self-hosting", "OSS", "ownership"]
}

def daily_post(brand_slug):
    """Generate daily post for a brand"""
    topic = random.choice(topics[brand_slug])
    post = generate_post_with_claude(brand_slug, topic)
    save_claude_post(brand_slug, f"Daily {brand_slug}: {topic}", post)
    print(f"✓ Generated daily post for {brand_slug}")

# Run every day at 9am
schedule.every().day.at("09:00").do(daily_post, "deathtodata")
schedule.every().day.at("10:00").do(daily_post, "calriven")
schedule.every().day.at("11:00").do(daily_post, "soulfra")

while True:
    schedule.run_pending()
    time.sleep(3600)
```

**Start daemon:**
```bash
nohup python3 cron_claude_daily.py &
# Claude now generates 3 posts/day automatically
```

---

## With Newsletter Integration

```python
def claude_post_and_send(brand_slug, topic):
    """Generate post + send newsletter"""

    # 1. Generate with Claude
    post = generate_post_with_claude(brand_slug, topic)

    # 2. Save to database
    post_id = save_claude_post(brand_slug, f"{topic.title()}", post)

    # 3. Classify with neural network (optional)
    classify_post(post_id)

    # 4. Send newsletter
    send_newsletter(brand_slug, post_id)

    return post_id

# One function = complete automation
post_id = claude_post_and_send("deathtodata", "privacy")
```

---

## Conversation-to-Post

```python
def claude_conversation_to_post(session_id):
    """Turn user conversation into blog post"""

    # Get conversation from database
    conv = get_conversation(session_id)

    prompt = f"""
    A user had this conversation:

    {conv['messages']}

    Turn this into a structured blog post with:
    - Catchy title
    - Introduction
    - Key points
    - Conclusion

    Format as markdown.
    """

    message = client.messages.create(
        model="claude-sonnet-4",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text

# Usage (called from /generate post command)
post = claude_conversation_to_post("session_123")
```

---

## Bulk Generation

```python
def bulk_generate_posts(brand_slug, topics_list):
    """Generate many posts at once"""

    for topic in topics_list:
        try:
            post = generate_post_with_claude(brand_slug, topic)
            post_id = save_claude_post(brand_slug, topic, post)
            print(f"✓ Created post #{post_id}: {topic}")
            time.sleep(2)  # Rate limit
        except Exception as e:
            print(f"✗ Failed {topic}: {e}")

# Generate 20 posts
topics = [
    "encryption basics", "tor browser guide", "signal setup",
    "protonmail tutorial", "vpn comparison", # ... etc
]
bulk_generate_posts("deathtodata", topics)
```

---

## API Endpoint

Add to `app.py`:
```python
@app.route('/api/claude/generate', methods=['POST'])
def api_claude_generate():
    """API endpoint for Claude generation"""

    data = request.json
    brand = data.get('brand')
    topic = data.get('topic')

    post = generate_post_with_claude(brand, topic)
    post_id = save_claude_post(brand, topic, post)

    return jsonify({
        'success': True,
        'post_id': post_id,
        'url': f'/post/{post_id}'
    })

# Call from anywhere
curl -X POST http://localhost:5001/api/claude/generate \
  -H "Content-Type: application/json" \
  -d '{"brand": "deathtodata", "topic": "privacy"}'
```

---

## Cost Estimation

**Claude Sonnet 4 pricing:**
- Input: $3 / million tokens
- Output: $15 / million tokens

**Average blog post:**
- Input: ~500 tokens (prompt)
- Output: ~1000 tokens (post)
- Cost: ~$0.02 per post

**Monthly:**
- 100 posts × $0.02 = **$2/month**

**Way cheaper than hiring writers.**

---

## Next Steps

1. Get API key from console.anthropic.com
2. Add to config_secrets.py
3. Run `force_claude_write.py`
4. Set up daily cron job
5. Watch automated content flow

**Your newsletter runs itself.** 🤖
