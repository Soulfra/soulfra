# Soulfra Distribution Model: Email + Git + RSS

## The Core Insight

**The platform doesn't need servers. It distributes via standard internet protocols.**

Instead of:
- ❌ Centralized hosting (AWS, Vercel, etc.)
- ❌ Custom APIs (GraphQL, REST with auth)
- ❌ Proprietary widgets/chatbots
- ❌ Vendor lock-in

Soulfra uses:
- ✅ **Email (SMTP)** - push distribution to inboxes
- ✅ **Git** - version control as deployment
- ✅ **RSS/Atom** - standard syndication
- ✅ **OpenAPI** - standard API documentation
- ✅ **Static HTML** - host anywhere

## How It Works

### 1. Email as Hosting

**Every inbox IS a deployed copy of the platform.**

```
Newsletter Email:
├── HTML content (interactive forms)
├── Inline CSS (works offline)
├── mailto: links (write capability)
└── Attachments (portable data)

Click "Reply" → post comment
Click "Vote" → record feedback
Forward email → share content
```

**Key features:**
- Works in ANY email client (Gmail, Outlook, Apple Mail, Thunderbird)
- No JavaScript required
- Fully functional offline
- Can't be deplatformed (email is decentralized)
- Users OWN their copy (it's in their inbox forever)

### 2. Git as Deployment

**Fork repo = copy entire platform**

```bash
# Clone platform
git clone https://github.com/soulfra/soulfra-simple.git
cd soulfra-simple

# Run migrations (rebuild database from scratch)
python3 migrate.py

# Start platform
python3 app.py

# You now have the ENTIRE platform running locally
```

**What you get:**
- Complete database schema (migrations/*.sql)
- All code (*.py files)
- All content (soulfra.db)
- All configuration (config.py)
- OpenAPI spec (openapi.yaml)

**Fork = Sovereignty**
- Change BASE_URL, run anywhere
- Modify code, it's yours
- Add features, no permission needed
- Can't be shut down (code is yours)

### 3. RSS as Read API

**Standard syndication - works with any RSS reader**

```xml
<!-- /feed.xml -->
<rss version="2.0">
  <channel>
    <title>Soulfra</title>
    <link>http://localhost:5001</link>
    <item>
      <title>Post Title</title>
      <description>Post excerpt...</description>
      <link>http://localhost:5001/post/slug</link>
      <pubDate>Sat, 21 Dec 2024 12:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
```

**Why RSS?**
- Every RSS reader works (Feedly, NetNewsWire, etc.)
- No custom API clients needed
- Decentralized (each reader fetches independently)
- Works offline (readers cache)
- Can't be rate-limited (it's pull, not push)

### 4. Email as Write API

**Post via email using mailto: links**

```html
<!-- In newsletter email -->
<a href="mailto:post@soulfra.local?subject=New%20Post&body=Content%20here">
  Create New Post
</a>

<a href="mailto:comment@soulfra.local?subject=Re:Post-Slug&body=My%20comment">
  Reply to Post
</a>

<a href="mailto:vote@soulfra.local?subject=Upvote:123">
  Upvote
</a>
```

**How it works:**
1. User clicks mailto: link in newsletter
2. Email client opens with pre-filled subject/body
3. User sends email
4. Platform's email processor receives it
5. Creates post/comment/vote in database
6. Next newsletter includes the new content

**No web browser needed. Works in email client only.**

### 5. OpenAPI as Contract

**API spec generated from code, not written by hand**

```bash
# Generate OpenAPI spec from migrations + routes
python3 generate_openapi.py

# Output:
# - openapi.yaml (standard spec)
# - openapi.json (for tools)
```

**Use the spec:**
- Import into Postman/Insomnia
- Generate API clients (any language)
- Validate requests/responses
- Auto-generate documentation

**Schema is code → API spec is code**

### 6. Static HTML Export

**Entire platform as portable static files**

```bash
# Build static site
python3 public_builder.py

# Output: docs/ folder
docs/
├── index.html
├── post/
│   ├── post-1.html
│   ├── post-2.html
├── feed.xml
└── static/
    └── style.css

# Host anywhere:
# - GitHub Pages
# - Netlify
# - CDN
# - USB drive
# - Email attachment (!)
```

**Why static?**
- Host on free platforms (GitHub Pages, Netlify)
- Works offline completely
- Can't be hacked (no server-side code)
- Fast (pre-rendered HTML)
- Portable (zip folder = entire site)

## Complete Distribution Flows

### Flow 1: Read-Only User

```
User subscribes → Receives weekly newsletter via email
                ↓
              Opens email in Gmail/Outlook
                ↓
              Reads posts, reasoning, souls
                ↓
              Clicks RSS link → Adds to Feedly
                ↓
              Gets updates via RSS reader
```

**No web browser needed. No servers needed. Just email + RSS reader.**

### Flow 2: Contributing User

```
User wants to comment → Clicks "Reply" in newsletter
                       ↓
                     Email client opens with pre-filled content
                       ↓
                     User types comment, sends email
                       ↓
                     Platform processes email, creates comment
                       ↓
                     Next newsletter includes the comment
```

**No login. No web forms. Just email.**

### Flow 3: Platform Forker

```
Developer sees platform → Clones git repo
                        ↓
                      Runs python3 migrate.py
                        ↓
                      Database built from migrations
                        ↓
                      Changes BASE_URL to their domain
                        ↓
                      Runs python3 app.py
                        ↓
                      ENTIRE platform running on their server
```

**Fork = copy. No permission needed. No API keys. No accounts.**

### Flow 4: Offline Archive

```
User wants offline copy → Downloads git repo as ZIP
                        ↓
                       Extracts files
                         ↓
                       Runs python3 public_builder.py
                         ↓
                       Gets docs/ folder (static HTML)
                         ↓
                       Opens docs/index.html in browser
                         ↓
                       Entire platform works offline, no server
```

**Portable. Permanent. Can't be deleted.**

## Why This Matters

### Traditional Platform

```
User → Browser → Load balancer → App server → Database → Cache → CDN
```

**Problems:**
- Vendor lock-in (AWS, Vercel, etc.)
- Centralized control (can be shut down)
- Requires always-on servers (costs money)
- Complex infrastructure (DevOps needed)
- Surveillance (analytics, tracking)

### Soulfra Distribution

```
User → Email client → Reads newsletter
    OR
User → RSS reader → Reads feed
    OR
User → Browser → Reads static HTML (local or hosted)
    OR
Developer → Git clone → Runs migrations → Full platform
```

**Benefits:**
- ✅ No vendor lock-in (standard protocols)
- ✅ Can't be deplatformed (email is decentralized)
- ✅ Free hosting (email, GitHub Pages, etc.)
- ✅ Simple infrastructure (one Python script)
- ✅ No surveillance (email is private)
- ✅ Truly open source (fork = sovereignty)

## Comparison to Other Platforms

### Substack

- ✅ Email distribution
- ❌ Proprietary platform
- ❌ Can't export database
- ❌ Can't self-host
- ❌ Vendor lock-in

### Ghost

- ✅ Self-hostable
- ✅ Open source
- ❌ Requires server
- ❌ No email-first design
- ❌ Complex deployment

### WordPress

- ✅ Self-hostable
- ✅ Plugins ecosystem
- ❌ PHP/MySQL complexity
- ❌ Security vulnerabilities
- ❌ Not database-first

### Soulfra

- ✅ Email distribution (like Substack)
- ✅ Self-hostable (like Ghost)
- ✅ Simple deployment (Python + SQLite)
- ✅ Database-first (fork DB = fork platform)
- ✅ Standard protocols (SMTP, RSS, HTTP, Git)
- ✅ Truly portable (static export)
- ✅ Can't be shut down (distributed via email)

## Technical Implementation

### Email Processor

```python
# Process incoming emails
import imaplib
import email

def process_incoming_emails():
    """Check inbox for post/comment/vote emails"""
    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    mail.login(email_user, email_password)
    mail.select('inbox')

    # Search for unread emails
    status, messages = mail.search(None, 'UNSEEN')

    for msg_id in messages[0].split():
        # Fetch email
        status, data = mail.fetch(msg_id, '(RFC822)')
        msg = email.message_from_bytes(data[0][1])

        subject = msg['subject']
        body = get_email_body(msg)

        # Parse command from subject
        if subject.startswith('Post:'):
            create_post_from_email(body)
        elif subject.startswith('Comment:'):
            create_comment_from_email(subject, body)
        elif subject.startswith('Vote:'):
            record_vote_from_email(subject)
```

### RSS Generator

```python
# Generate RSS feed from database
from database import get_posts

def generate_rss():
    """Generate RSS feed from posts"""
    posts = get_posts(limit=20)

    rss = f'''<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
      <channel>
        <title>Soulfra</title>
        <link>{BASE_URL}</link>
        <description>Database-first platform</description>

        {chr(10).join(post_to_rss_item(p) for p in posts)}
      </channel>
    </rss>'''

    return rss
```

### Static Site Builder

```python
# Build static HTML from database
def build_static_site():
    """Export entire platform as static HTML"""
    posts = get_posts()

    for post in posts:
        html = render_template('post.html', post=post)

        filepath = f"docs/post/{post['slug']}.html"
        with open(filepath, 'w') as f:
            f.write(html)

    # Generate index
    html = render_template('index.html', posts=posts)
    with open('docs/index.html', 'w') as f:
        f.write(html)
```

## The Vision

**The internet before surveillance capitalism.**

- No tracking
- No algorithms
- No ads
- No engagement metrics
- No growth hacking

Just:
- Email (1971 protocol)
- RSS (1999 protocol)
- Git (2005 protocol)
- OpenAPI (2015 protocol)

**Old protocols. New platform. True ownership.**

---

*This is Soulfra: Email as hosting, Git as deployment, RSS as API.*

*Fork the repo. Run the migrations. You have the platform.*

*Can't be shut down. Can't be deplatformed. Can't be enshittified.*

*Because it's yours.*
