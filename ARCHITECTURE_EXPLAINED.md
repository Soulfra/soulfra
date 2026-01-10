# Soulfra Architecture Explained

**How database + filesystem + templates + CSS all work together**

---

## The Big Picture

Soulfra uses a **hybrid architecture**:
- **Database (SQLite)** = Source of truth for dynamic data
- **Filesystem** = Git-trackable exports, static assets, templates
- **Templates (Jinja2)** = Dynamic HTML generation
- **CSS** = Brand-specific styling via variables

Think of it like Linux:
- Database = `/proc` (dynamic, runtime data)
- Filesystem = `/home` (persistent, exportable)
- Templates = `/etc/` (configuration files)
- CSS = Themes/desktop environments

---

## Directory Structure (Linux-Style)

```
soulfra-simple/
├── app.py                      # Main Flask server (like systemd)
├── soulfra.db                  # SQLite database (like /var/lib)
│
├── templates/                  # HTML templates (like /etc/)
│   ├── components/             # Reusable UI components
│   │   ├── header.html         # Site header
│   │   ├── footer.html         # Site footer
│   │   └── menu.html           # Navigation menu
│   ├── base.html               # Base template (all pages inherit)
│   ├── index.html              # Homepage
│   └── post.html               # Blog post page
│
├── static/                     # Static assets (like /usr/share/)
│   ├── css/                    # Stylesheets
│   │   ├── theme.css           # Global theme system
│   │   ├── deathtodata.css     # DeathToData brand colors
│   │   ├── calriven.css        # Calriven brand colors
│   │   └── soulfra.css         # Soulfra brand colors
│   ├── js/                     # JavaScript
│   └── generated/              # AI-generated images
│
├── brands/                     # Exported brand filesystems
│   ├── deathtodata/            # DeathToData export
│   │   ├── config.json         # Brand configuration
│   │   ├── posts/              # All posts as markdown
│   │   └── README.md           # Documentation
│   ├── calriven/
│   └── soulfra/
│
├── neural_networks/            # Trained classifiers (like /var/models/)
│   ├── deathtodata_privacy_classifier.pkl
│   ├── calriven_technical_classifier.pkl
│   └── topic_classifier_encryption_privacy.pkl
│
├── logs/                       # Application logs (like /var/log/)
│
└── archive/                    # Old experiments (like /opt/)
    ├── experiments/            # Archived Python scripts
    └── docs/                   # Archived documentation
```

---

## How It All Connects

### 1. Database → Templates → HTML

**Flow:** User visits `/post/privacy-101` → Flask queries database → Jinja2 renders template → HTML sent to browser

**Example:**

```python
# app.py
@app.route('/post/<slug>')
def view_post(slug):
    # 1. Query database
    post = db.execute("SELECT * FROM posts WHERE slug = ?", (slug,))
    brand = db.execute("SELECT * FROM brands WHERE id = ?", (post.brand_id,))

    # 2. Render template with data
    return render_template('post.html', post=post, brand=brand)
```

```html
<!-- templates/post.html -->
{% include 'components/header.html' %}

<article>
  <h1>{{ post.title }}</h1>
  <div class="content">{{ post.content }}</div>
</article>

{% include 'components/footer.html' %}
```

**Result:** Dynamic HTML page with post content from database

---

### 2. Database → CSS Variables → Styled Page

**Flow:** Brand colors stored in database → Injected as CSS variables → Page styled dynamically

**Example:**

```python
# app.py
@app.route('/brand/<slug>')
def view_brand(slug):
    brand = get_brand(slug)

    # Inject brand colors as CSS variables
    return render_template('brand.html',
        brand=brand,
        css_vars={
            '--brand-primary': brand.color_primary,
            '--brand-secondary': brand.color_secondary,
            '--brand-accent': brand.color_accent
        }
    )
```

```html
<!-- templates/brand.html -->
<html>
<head>
  <link rel="stylesheet" href="/static/css/theme.css">
  <link rel="stylesheet" href="/static/css/{{ brand.slug }}.css">
  <style>
    :root {
      --brand-primary: {{ css_vars['--brand-primary'] }};
      --brand-secondary: {{ css_vars['--brand-secondary'] }};
      --brand-accent: {{ css_vars['--brand-accent'] }};
    }
  </style>
</head>
<body class="brand-{{ brand.slug }}">
  <header style="background: var(--color-primary);">
    {{ brand.name }}
  </header>
</body>
</html>
```

**Result:** Page styled with brand-specific colors from database

---

### 3. Database → Filesystem Export → Git

**Flow:** Content in database → Export to filesystem → Track with git → Deploy anywhere

**Example:**

```bash
# Export brand to filesystem
python3 export_brand_filesystem.py --brand deathtodata

# Creates:
brands/deathtodata/
├── config.json          # Brand settings
├── posts/               # All posts as markdown
│   ├── privacy-101.md
│   └── encryption-guide.md
└── README.md
```

```json
// brands/deathtodata/config.json
{
  "name": "DeathToData",
  "slug": "deathtodata",
  "colors": {
    "primary": "#e74c3c",
    "secondary": "#c0392b",
    "accent": "#f39c12"
  },
  "personality": {
    "tone": "Rebellious, defiant",
    "ai_style": "edgy, confrontational"
  }
}
```

```markdown
<!-- brands/deathtodata/posts/privacy-101.md -->
---
title: Privacy 101
slug: privacy-101
published: 2025-12-26T09:59:39
brand: deathtodata
---

# Privacy 101

Your guide to digital privacy...
```

**Result:** Git-trackable, portable brand content

---

### 4. Templates → Components → Reusable UI

**Flow:** Base template → Include components → DRY (Don't Repeat Yourself)

**Example:**

```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html>
<head>
  <link rel="stylesheet" href="/static/css/theme.css">
  <link rel="stylesheet" href="/static/css/{{ brand_slug }}.css">
</head>
<body class="brand-{{ brand_slug }}">
  {% include 'components/header.html' %}

  <main>
    {% block content %}{% endblock %}
  </main>

  {% include 'components/footer.html' %}
</body>
</html>
```

```html
<!-- templates/post.html -->
{% extends 'base.html' %}

{% block content %}
<article>
  <h1>{{ post.title }}</h1>
  <div>{{ post.content }}</div>
</article>
{% endblock %}
```

**Result:** Shared layout across all pages, easy to update

---

### 5. Neural Networks → Topic Classification → Smart Content

**Flow:** User chats about "encryption" → Neural network detects topic → Recommends related posts

**Example:**

```bash
# Train topic classifier
python3 train_topic_networks.py --topics encryption,privacy,surveillance --train

# Creates:
neural_networks/topic_classifier_encryption_privacy_surveillance.pkl
```

```python
# soulfra_assistant.py
import pickle

def recommend_posts(user_message):
    # Load topic classifier
    model = pickle.load(open('neural_networks/topic_classifier.pkl', 'rb'))

    # Classify user's message
    topic = model['classifier'].predict(
        model['vectorizer'].transform([user_message])
    )[0]

    # Find posts about that topic
    posts = db.execute("""
        SELECT * FROM posts
        WHERE content LIKE ?
        ORDER BY published_at DESC
        LIMIT 5
    """, (f"%{topic}%",))

    return posts
```

**Result:** AI understands what user is interested in, suggests relevant content

---

## Data Flow Examples

### Example 1: QR Code → Chat → Blog Post

```
1. User scans QR code
   → GET /chat?username=matt

2. User types: "I want to learn about encryption"
   → POST /chat/send
   → soulfra_assistant.py processes message
   → Ollama generates response

3. User says: "Turn this into a blog post"
   → POST /generate-post
   → Creates post in database:
      INSERT INTO posts (title, content, brand_id)
      VALUES ('Encryption Guide', '...', 2)

4. Neural network classifies post
   → python3 classify_post.py --post-id 26
   → Adds topic tags: encryption, privacy

5. Post appears on website
   → GET /post/encryption-guide-1766764779
   → Template renders with DeathToData styling
```

### Example 2: Brand Export → ZIP → Share

```
1. Export brand to filesystem
   → python3 export_brand_filesystem.py --brand deathtodata --zip

2. Creates ZIP package:
   deathtodata_export_1766764779.zip
   ├── config.json
   ├── posts/
   │   ├── encryption-guide.md
   │   └── privacy-101.md
   └── deathtodata_privacy_classifier.pkl

3. Share with others
   → Upload to GitHub
   → Others can import: python3 import_brand_filesystem.py

4. Or track with git
   → git add brands/deathtodata/
   → git commit -m "Update DeathToData content"
   → git push
```

### Example 3: Claude Auto-Generation

```
1. Trigger Claude to write
   → python3 force_claude_write.py --brand deathtodata --topic "privacy" --save

2. Claude API generates content
   → Anthropic API call
   → Returns 500-word blog post

3. Saves to database
   → INSERT INTO posts (...)
   → Post appears on website immediately

4. Neural network learns
   → New training data for topic classifier
   → Improves recommendations
```

---

## Key Design Principles

### 1. Database as Source of Truth

- All dynamic data lives in `soulfra.db`
- Fast queries, easy to update
- Relationships between brands, posts, users

### 2. Filesystem for Portability

- Export brands to git-trackable format
- Share as ZIP packages
- Import into other Soulfra instances

### 3. Templates for Flexibility

- Shared components (header, footer, menu)
- Easy to update site-wide changes
- Brand-specific styling via CSS variables

### 4. CSS Variables for Theming

- Brand colors defined once in database
- Injected as CSS variables
- Automatic light/dark mode support

### 5. Neural Networks for Intelligence

- Topic classification (not just brand)
- User profiling based on conversations
- Content recommendations

---

## Terminology Translation

| Linux/Unix | Soulfra | Purpose |
|------------|---------|---------|
| `/home/user/` | `brands/deathtodata/` | User's home directory |
| `/etc/nginx/nginx.conf` | `templates/base.html` | Configuration file |
| `/var/www/html/` | `static/` | Static web content |
| `/var/lib/mysql/` | `soulfra.db` | Database storage |
| `/var/log/` | `logs/` | Application logs |
| `/usr/share/themes/` | `static/css/` | Theme files |
| `/opt/` | `archive/` | Optional software |

---

## How to Use This Architecture

### Creating a New Brand

```bash
# 1. Add to database (via admin panel or SQL)
INSERT INTO brands (name, slug, color_primary, color_secondary, color_accent)
VALUES ('MyBrand', 'mybrand', '#ff0000', '#cc0000', '#ffaa00');

# 2. Create CSS file
cat > static/css/mybrand.css << EOF
:root {
  --brand-primary: #ff0000;
  --brand-secondary: #cc0000;
  --brand-accent: #ffaa00;
}
EOF

# 3. Export to filesystem
python3 export_brand_filesystem.py --brand mybrand

# 4. Visit website
open http://localhost:5001/brand/mybrand
```

### Adding a New Template Component

```bash
# 1. Create component
cat > templates/components/sidebar.html << EOF
<aside class="sidebar">
  <h3>Related Posts</h3>
  {% for post in related_posts %}
    <a href="/post/{{ post.slug }}">{{ post.title }}</a>
  {% endfor %}
</aside>
EOF

# 2. Include in templates
# Edit templates/post.html:
{% include 'components/sidebar.html' %}
```

### Training a New Topic Classifier

```bash
# 1. Analyze topic coverage
python3 train_topic_networks.py --topic blockchain --analyze

# 2. Generate more content if needed
python3 force_claude_write.py --brand calriven --topic "blockchain" --save

# 3. Train classifier
python3 train_topic_networks.py --topics blockchain,crypto,web3 --train

# 4. Use in recommendations
# Neural network now understands blockchain content
```

---

## The Philosophy

**Why this architecture?**

1. **Database for Speed**
   - Fast queries, indexing, relationships
   - Perfect for dynamic content

2. **Filesystem for Control**
   - Git-trackable, human-readable
   - Easy to backup, share, migrate

3. **Templates for Maintainability**
   - DRY principle, reusable components
   - One change updates entire site

4. **CSS Variables for Branding**
   - Dynamic theming without rebuilding
   - Same codebase, infinite brands

5. **Neural Networks for Intelligence**
   - Learn from user behavior
   - Improve over time automatically

---

## Future Enhancements

### 2025 Q1
- Import brands from filesystem back to database
- Multi-brand newsletters (one email, multiple brands)
- Topic-based content clustering

### 2025 Q2
- User profiling neural networks
- Automated content suggestions based on conversation
- Domain name suggestions based on topics

### 2025 Q3
- Federated brand sharing (ActivityPub)
- Cross-brand content recommendations
- Neural network ensemble voting

---

## Quick Reference

**Export brand:**
```bash
python3 export_brand_filesystem.py --brand deathtodata --zip
```

**Train topic classifier:**
```bash
python3 train_topic_networks.py --topics encryption,privacy --train
```

**Generate post with Claude:**
```bash
python3 force_claude_write.py --brand deathtodata --topic "privacy" --save
```

**View brand on website:**
```
http://localhost:5001/brand/deathtodata
```

**Check database schema:**
```bash
sqlite3 soulfra.db ".schema brands"
sqlite3 soulfra.db ".schema posts"
```

---

**The system is designed to be simple yet powerful: database for speed, filesystem for control, templates for flexibility, and neural networks for intelligence.**

Built with Python, Flask, SQLite, Jinja2, and scikit-learn.
