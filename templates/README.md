# Soulfra Templates Documentation

**Last Updated:** December 22, 2025

This document explains the template structure, naming conventions, and best practices for creating new templates in Soulfra.

---

## Template Structure

### Base Template System

All templates **MUST** extend `base.html`:

```jinja2
{% extends "base.html" %}

{% block title %}Page Title - Soulfra{% endblock %}

{% block content %}
  <!-- Your page content here -->
{% endblock %}
```

### base.html Provides

- Header with navigation (Posts, Souls, Reasoning, ML, Tags, About, Feedback)
- Flash message display
- Footer with links
- Consistent styling (style.css)
- Responsive layout (800px max-width)
- SEO meta tags (Open Graph, Twitter Card)

---

## Existing Templates

### Templates Using base.html ✅

| Template | Route | Purpose |
|----------|-------|---------|
| index.html | / | Homepage with post list |
| post.html | /post/<slug> | Individual post with comments & reasoning |
| category.html | /category/<slug> | Posts filtered by category |
| tag.html | /tag/<slug> | Posts filtered by tag |
| user.html | /user/<username> | User profile |
| soul.html | /soul/<username> | Soul details |
| soul_similar.html | /soul/<username>/similar | Similar souls |
| souls.html | /souls | Soul browser |
| reasoning.html | /reasoning | Reasoning dashboard |
| ml_dashboard.html | /ml | ML dashboard |
| status.html | /status | Platform status |

### Standalone Templates (No base.html)

| Template | Route | Reason |
|----------|-------|--------|
| login.html | /login | Simple auth page |
| signup.html | /signup | Simple auth page |
| about.html | /about | Static content page |
| subscribe.html | /subscribe | Newsletter subscription |
| admin_*.html | /admin/* | Admin-only pages |
| feedback.html | /feedback | Public feedback form |
| code_browser.html | /code | Code browser (special layout) |

---

## CSS Class Naming Conventions

### Post & Content Classes

```css
.post-full           /* Full post article container */
.post-preview        /* Post preview on index */
.post-content        /* Post content area (where HTML is rendered) */
.post-content img    /* Images in post content (auto-sized) */
```

**Image Sizing (CRITICAL):**
- All images in `.post-content` are automatically constrained:
  - `max-width: 100%` - Never wider than container
  - `max-height: 600px` - Never taller than 600px (400px on mobile)
  - `object-fit: contain` - Maintains aspect ratio

### Categories & Tags

```css
.categories          /* Category badge container */
.category-badge      /* Individual category link (blue) */
.tags                /* Tag badge container */
.tag-badge           /* Individual tag link (gray) */
```

### Reasoning Section

```css
.reasoning-section   /* Overall reasoning container (gray background) */
.reasoning-intro     /* Intro text */
.reasoning-toggle    /* Collapsible details summary (clickable) */
.reasoning-steps     /* Container for all steps */
.reasoning-step      /* Individual reasoning step (white card with blue border) */
.step-header         /* Step metadata (number, AI badge, confidence) */
.step-content        /* Step reasoning content */
.step-time           /* Timestamp */
```

### Comments Section

```css
.comments-section       /* Overall comments container */
.comment-form           /* Add comment form */
.comment-textarea       /* Comment textarea input */
.comment-submit         /* Submit button */
.comments-list          /* List of all comments */
.comment                /* Individual comment */
.comment-reply          /* Nested/reply comment (indented) */
.comment-avatar         /* User avatar (48px circle) */
.ai-avatar              /* AI persona avatar (blue border) */
.comment-body           /* Comment content area */
.comment-meta           /* Comment author & time */
.comment-content        /* Comment text */
.comment-replies        /* Nested replies container */
```

### Badges & UI Elements

```css
.ai-badge            /* Blue "AI" badge for AI personas */
.author-link         /* Author name link */
.login-prompt        /* Login/signup prompt */
.subscribe-prompt    /* Subscribe CTA box */
```

---

## Creating a New Template

### Step 1: Create File

```bash
touch templates/my_new_page.html
```

### Step 2: Extend base.html

```jinja2
{% extends "base.html" %}

{% block title %}My New Page - Soulfra{% endblock %}

{% block content %}
<div class="my-page-container">
  <h1>My New Page</h1>
  <p>Content goes here...</p>
</div>
{% endblock %}
```

### Step 3: Add Route in app.py

```python
@app.route('/my-page')
def my_page():
    return render_template('my_new_page.html', data=data)
```

### Step 4: Add CSS Classes

Add to `static/style.css`:

```css
/* My New Page */
.my-page-container {
  max-width: 800px;
  margin: 2rem auto;
  padding: 2rem;
}
```

---

## Image Handling Best Practices

### DO:
- ✅ Let CSS handle image sizing (no inline width/height)
- ✅ Use descriptive alt text for all images
- ✅ Store images in database (`images` table with BLOB data)
- ✅ Serve via `/i/<hash>` routes (database-first hosting)

### DON'T:
- ❌ Don't use inline styles on images
- ❌ Don't specify pixel widths in HTML
- ❌ Don't forget alt text (accessibility)

### Example:

```html
<!-- Good -->
<img src="/i/abc123def456" alt="User avatar" class="comment-avatar">

<!-- Bad -->
<img src="/static/avatar.jpg" width="48" height="48" style="border-radius: 50%;">
```

---

## Template Variables Reference

### Common Variables Passed to Templates

#### All Templates (via base.html)
- `all_tags` - List of all tags for dropdown nav
- `session` - Flask session (user_id, username, etc.)

#### Post Template
- `post` - Post dict (id, title, slug, content, published_at, etc.)
- `author` - Author user dict (username, display_name)
- `comments` - List of comment dicts (nested with replies)
- `categories` - List of category dicts for this post
- `tags` - List of tag dicts for this post
- `reasoning_thread` - Reasoning thread dict (if exists)
- `reasoning_steps` - List of reasoning step dicts

#### Index Template
- `posts` - List of post dicts (paginated)

#### Soul Template
- `user` - User dict
- `soul` - Soul dict (bio, skills, interests, avatar)
- `similar_souls` - List of similar users

---

## Flash Messages

Flash messages are automatically displayed by base.html:

```python
# In route handler
flash('Success message', 'success')  # Green background
flash('Error message', 'error')      # Red background
flash('Info message', 'info')        # Blue background
```

Templates don't need to handle flash messages - base.html already does.

---

## Responsive Breakpoints

Current breakpoint: **600px**

```css
@media (max-width: 600px) {
  /* Mobile styles */
  .comment-reply {
    margin-left: 1rem; /* Reduce nesting on mobile */
  }

  .post-content img {
    max-height: 400px; /* Smaller images on mobile */
  }
}
```

---

## Reasoning Engine Integration

### When to Show Reasoning

Reasoning section appears automatically if `reasoning_steps` exists:

```jinja2
{% if reasoning_steps %}
  <div class="reasoning-section">
    <!-- Reasoning UI -->
  </div>
{% endif %}
```

### How Reasoning Works

1. Post created
2. `reasoning_engine.py` analyzes post
3. Creates `reasoning_thread` record
4. Generates `reasoning_steps` (analysis, observations, conclusions)
5. Template displays steps in collapsible `<details>` tag

---

## Comments System

### Nested Comments

Comments use recursive macro for nesting:

```jinja2
{% macro render_comment(comment) %}
  <div class="comment">
    <!-- Comment content -->
    {% if comment.get('replies') %}
      {% for reply in comment['replies'] %}
        {{ render_comment(reply) }}
      {% endfor %}
    {% endif %}
  </div>
{% endmacro %}
```

### AI Comments

AI persona comments automatically show "AI" badge:

```jinja2
{% if comment['is_ai_persona'] %}
  <span class="ai-badge">AI</span>
{% endif %}
```

---

## Common Mistakes to Avoid

### ❌ Not Extending base.html
```jinja2
<!-- WRONG -->
<!DOCTYPE html>
<html>
<head>...</head>
<body>...</body>
</html>
```

```jinja2
<!-- RIGHT -->
{% extends "base.html" %}
{% block content %}...{% endblock %}
```

### ❌ Inline Styles Everywhere
```html
<!-- WRONG -->
<div style="padding: 1rem; background: #f9f9f9; border-radius: 4px;">
```

```html
<!-- RIGHT -->
<div class="comment-form">
```

### ❌ Forgetting to Pass Variables
```python
# WRONG
return render_template('post.html')

# RIGHT
return render_template('post.html', post=post, comments=comments, author=author)
```

### ❌ Using Hardcoded URLs
```html
<!-- WRONG -->
<a href="/post/my-post">Link</a>

<!-- RIGHT -->
<a href="{{ url_for('post_detail', slug='my-post') }}">Link</a>
```

---

## Testing Checklist

Before considering a template "done":

- [ ] Extends base.html
- [ ] Title block set
- [ ] All variables passed from route
- [ ] No inline styles (use CSS classes)
- [ ] Images have alt text
- [ ] Responsive on mobile (test at 375px width)
- [ ] Flash messages work
- [ ] Links use `url_for()`
- [ ] No console errors
- [ ] Reasoning section appears (if applicable)

---

## File Structure

```
templates/
├── README.md (this file)
├── base.html (extends all templates)
├── index.html (homepage)
├── post.html (individual post)
├── category.html (category filter)
├── tag.html (tag filter)
├── user.html (user profile)
├── soul.html (soul details)
├── soul_similar.html (similar souls)
├── souls.html (soul browser)
├── reasoning.html (reasoning dashboard)
├── ml_dashboard.html (ML dashboard)
├── status.html (platform status)
├── login.html (auth)
├── signup.html (auth)
├── about.html (static)
├── subscribe.html (newsletter)
├── feedback.html (public feedback)
├── admin_*.html (admin pages)
└── code_browser.html (code viewer)
```

---

## Questions?

- Check existing templates for examples
- Read base.html to see what's available
- Check style.css for existing classes
- Test on actual page before committing

**Bottom line:** Always extend base.html, use CSS classes not inline styles, and test responsive layout.
