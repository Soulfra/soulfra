# 🎨 Template Browser - Quick Start Guide

## ✅ IT'S WORKING NOW!

You asked "how do I see the templates as a frontend" - **NOW YOU CAN**!

---

## 🚀 Open the Template Browser

**URL**: http://localhost:5001/templates/browse

Flask is already running - just open your browser and go there!

---

## 📖 What You'll See

```
┌──────────────────────────────────────────────┐
│ 🎨 Template Browser                          │
├──────────────────────────────────────────────┤
│ [Left]          [Middle]         [Right]     │
│ Templates       Variables        Preview     │
│ ├ email.html    {                [Live view] │
│ └ theme.css       "emoji": "🎨", [Or code]   │
│                   "brand": ...   │            │
└──────────────────────────────────────────────┘
```

---

## 🎯 Full Workflow

### 1. **Pick a Template** (Left Panel)
- Click any `.tmpl` file
- Email, theme, or create your own
- Auto-loads and shows preview

### 2. **Edit Variables** (Middle Panel)
- Change ANY value:
  ```json
  {
    "brand": "Soulfra",
    "emoji": "🎨",        ← Click quick buttons to change!
    "primaryColor": "#4ecca3",
    "fontSize": 16
  }
  ```
- **Add emojis**: Click quick insert buttons (🎨 🚀 💡 ⚡ ✨ 🔥)
- **Add anything**: Lists, objects, numbers, strings

### 3. **See Live Preview** (Right Panel)
- **Visual tab**: See rendered HTML
- **Code tab**: See generated code
- Updates when you click "Render Template"

### 4. **Generate with Ollama** (Optional)
- Enter prompt: "Write a blog post about AI"
- Pick model: llama3.2, mistral, or phi3
- Click "Generate Content"
- Ollama response gets added to variables as `generated_content`
- Template fills with AI-generated content!

### 5. **Deploy to Domain**
- Click "Deploy to Domain"
- Enter filename (e.g., `my-page.html`)
- Saved to `domains/soulfra/blog/my-page.html`
- Immediately accessible at `/blog/soulfra/my-page.html`

---

## 💡 Examples

### Example 1: Quick Emoji Change
1. Open template browser
2. Click email template
3. Click 🚀 emoji button
4. Click "Render Template"
5. See emoji change in preview!

### Example 2: Generate Blog Post with Ollama
1. Pick a blog template (or use email template for now)
2. Enter prompt: "Write about universal theming"
3. Click "Generate Content"
4. Wait ~10 seconds
5. See AI-generated content rendered!

### Example 3: Brand Colors
1. Edit variables JSON:
   ```json
   {
     "primaryColor": "#ff6b6b",  ← Change to red
     "fontSize": 20
   }
   ```
2. Click "Render Template"
3. See preview with RED colors and larger font!

### Example 4: Deploy a Page
1. Render a template (steps above)
2. Click "Deploy to Domain"
3. Enter: `test-page.html`
4. Open: http://localhost:5001/blog/soulfra/test-page.html
5. IT'S LIVE!

---

## 🔧 File Structure Explained

### What `.tmpl` Files Are
- **Formula templates** - Use `{{variables}}` syntax
- Processed by `formula_engine.py`
- Support formulas: `{{fontSize * 2}}`, `{{darken(color, 0.3)}}`

### Where They Live
```
soulfra-simple/
├── examples/           ← Formula templates (.tmpl)
│   ├── email.html.tmpl
│   └── theme.css.tmpl
└── templates/          ← Flask templates (.html)
    ├── template_browser.html  ← The UI you're using
    └── [141 other templates]
```

**The difference:**
- `.tmpl` files → Compiled by formula engine → Static output
- `.html` files → Rendered by Flask/Jinja → Dynamic pages

---

## 🤖 Ollama Integration

### How It Works
1. You enter a prompt
2. Flask calls: `ollama run llama3.2 "Your prompt"`
3. Ollama generates text
4. Text gets added to variables as `generated_content`
5. Template renders with AI content

### Using Generated Content in Templates
```html
<h1>{{brand}}</h1>
<div class="content">
  {{generated_content}}  ← Ollama output goes here
</div>
```

---

## 🚢 Deployment Flow

```
Idea → Variables → Ollama (optional) → Template → Preview → Deploy → Live!
```

### What "Deploy" Does
1. Takes rendered HTML/CSS
2. Saves to `domains/{domain}/blog/{filename}`
3. Flask immediately serves it at `/blog/{domain}/{filename}`
4. No build step needed!

---

## 🎨 Emoji & Custom Data

### Quick Insert Emojis
Click any button:
- 🎨 Art
- 🚀 Rocket
- 💡 Idea
- ⚡ Fast
- ✨ Sparkle
- 🔥 Fire

### Add Your Own
Edit the JSON directly:
```json
{
  "emoji": "🦄",           ← Unicorn
  "secondEmoji": "🌈",     ← Rainbow
  "features": ["AI", "Themes", "Magic"]  ← Array
}
```

Use in template:
```html
<h1>{{emoji}} Welcome {{secondEmoji}}</h1>
<ul>
  {{#each features}}
    <li>{{this}}</li>
  {{/each}}
</ul>
```

---

## ❓ FAQ

### Q: Why can't I see some templates?
**A**: Browser only shows `.tmpl` files (formula templates). The 141 `.html` files in `templates/` are Flask/Jinja templates (different system).

### Q: How do I create a new template?
**A**: Create a `.tmpl` file in `examples/` or `templates/formulas/`:
```html
<!-- my-template.html.tmpl -->
<!DOCTYPE html>
<html>
<head>
  <title>{{brand}}</title>
  <style>
    body { background: {{primaryColor}}; }
  </style>
</head>
<body>
  <h1>{{emoji}} {{tagline}}</h1>
</body>
</html>
```

Refresh browser → New template appears!

### Q: Ollama is slow or failing?
**A**:
- Check Ollama is running: `ollama list`
- Use smaller model: phi3 is faster than llama3.2
- Increase timeout if needed (60 seconds default)

### Q: Where are deployed files?
**A**:
```
domains/
└── soulfra/
    ├── blog/
    │   ├── my-page.html  ← Your deployed pages
    │   └── test-page.html
    └── emails/
        └── newsletter.html
```

### Q: Can I use this for ALL my domains?
**A**: YES! Change the `domain` variable:
```json
{
  "domain": "stpetepros.com",  ← Different domain
  "brand": "St Pete Pros",
  ...
}
```

Deploy → Saves to `domains/stpetepros/blog/`

---

## 🎯 Next Steps

1. **Try it**: http://localhost:5001/templates/browse
2. **Create templates**: Add `.tmpl` files to `examples/`
3. **Connect Ollama**: Generate content for all domains
4. **Deploy**: Build your multi-domain empire!

---

## 🔥 The Big Picture

**What we built:**

1. **Formula Engine** - Universal template system
2. **Template Browser** - Visual UI to test everything
3. **Ollama Integration** - AI-powered content generation
4. **One-Click Deploy** - From idea to live in seconds

**The workflow:**

```
Brand idea → Edit variables (emojis, colors, text)
          ↓
    Pick template (email, blog, theme)
          ↓
    Generate with Ollama (optional)
          ↓
    Preview (visual + code)
          ↓
    Deploy to domain
          ↓
    LIVE ON THE WEB!
```

**This answers your question:**
> "how do i see the templates as a frontend because there are so many different format and file names?"

**NOW YOU CAN SEE THEM ALL** in a visual browser with live preview!

---

**Open it now**: http://localhost:5001/templates/browse 🎨
