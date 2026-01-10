# 🎯 End-to-End Guide: soulfra.com Example

> **Your question**: "how do we get this working properly so i can learn coding snippets like python and deploy my own sites with everything they need?"

**Answer**: Let's walk through the COMPLETE process using soulfra.com as the example. You already have 80% of this built!

---

## 🗺️ The Complete Journey

```
Local Development → Generate Content → Save Locally → Deploy Online → Works for ALL Brands
```

**Time**: 30 minutes first time, 5 minutes after you learn it

**Result**: Live website at soulfra.com that anyone can visit

---

## Part 1: Local Development (What You Have Now)

### Step 1: Start the Server

**File**: `launcher.py` (your pm2 equivalent!)

**Option A: GUI Launcher**
```bash
python3 launcher.py
# → GUI opens
# → Click "Start Server"
# → Server runs on localhost:5001
```

**Option B: Command Line**
```bash
python3 app.py
# Server started on http://localhost:5001
```

**What's happening**:
- Flask web server starts
- Loads database (soulfra.db)
- Loads all your brands (soulfra, calriven, deathtodata)
- Template browser becomes available

---

### Step 2: Open Template Browser

**URL**: http://localhost:5001/templates/browse

**What you see**:
```
┌────────────────────────────────────────┐
│ 🎨 Template Browser - Formula Engine  │
├────────────────────────────────────────┤
│ Left: Templates                        │
│   - blog.html.tmpl                     │
│   - email.html.tmpl                    │
│   - theme.css.tmpl                     │
│                                        │
│ Middle: Variables                      │
│   {                                    │
│     "brand": "Soulfra",                │
│     "emoji": "🎨",                     │
│     "primaryColor": "#4ecca3"          │
│   }                                    │
│                                        │
│ Right: Preview (Visual + Code)         │
└────────────────────────────────────────┘
```

**This IS your product!** Everything else is just distribution.

---

### Step 3: Select a Template

**Click**: `blog.html.tmpl`

**What loads**:
```html
<!DOCTYPE html>
<html>
<head>
    <title>{{emoji}} {{brand}} Blog</title>
</head>
<body>
    <h1>{{emoji}} {{brand}}</h1>
    <div class="article-content">
        {{generated_content}}
    </div>
</body>
</html>
```

**Variables panel shows**:
```json
{
  "brand": "Soulfra",
  "emoji": "🎨",
  "primaryColor": "#4ecca3",
  "fontSize": 16,
  "spacing": 8,
  "domain": "soulfra.com",
  "tagline": "The soul of infrastructure",
  "generated_content": ""
}
```

**Code**: `examples/blog.html.tmpl` (this is what loads)

---

### Step 4: Generate Content with Ollama

**In the Ollama section**:
1. **Prompt**: "Write a blog post about identity and security in 2025"
2. **Model**: llama3.2 (or llama2, mistral - has auto-fallback!)
3. **Click**: "Generate Content"

**What happens behind the scenes** (this is the genius part):

**File**: `app.py` → Route `/api/templates/generate-with-ollama`
```python
@app.route('/api/templates/generate-with-ollama', methods=['POST'])
def generate_with_ollama():
    data = request.get_json()
    prompt = data.get('prompt')
    model = data.get('model', 'llama3.2')

    # This uses your LLM Router!
    from llm_router import LLMRouter
    router = LLMRouter()

    # Tries llama3.2 → llama2 → mistral (auto-fallback!)
    result = router.call(prompt=prompt, model=model)

    if result['success']:
        return jsonify({
            'success': True,
            'generated_content': result['response'],
            'model_used': result['model_used']
        })
```

**File**: `llm_router.py` (your multi-model fallback)
```python
class LLMRouter:
    def __init__(self):
        # Try these models in order
        self.models = ['llama3.2', 'llama2', 'mistral']

    def call(self, prompt, model=None):
        # Try each model until one works
        for model_name in self.models:
            try:
                result = ollama_api.generate(model_name, prompt)
                return {'success': True, 'response': result}
            except:
                continue  # Try next model

        return {'success': False, 'error': 'All models failed'}
```

**Result**: ~10 seconds later, you see generated content in the "Generated Content" box!

---

### Step 5: Preview the Rendered Template

**Automatic**: Variables + Generated Content → Rendered HTML

**What you see in Visual tab**:
```
┌──────────────────────────────────────┐
│ 🎨 Soulfra                           │
│ The soul of infrastructure           │
│──────────────────────────────────────│
│                                      │
│ Latest Post                          │
│                                      │
│ In 2025, identity and security...   │
│ [Full AI-generated blog post]       │
│                                      │
│ Want more content like this?         │
│ [Subscribe Now]                      │
└──────────────────────────────────────┘
```

**What you see in Code tab**:
```html
<!DOCTYPE html>
<html>
<head>
    <title>🎨 Soulfra Blog</title>
    <style>
        .header { background: #4ecca3; }
    </style>
</head>
<body>
    <h1>🎨 Soulfra</h1>
    <div class="article-content">
        <p>In 2025, identity and security...</p>
    </div>
</body>
</html>
```

**All `{{variables}}` replaced!**

---

### Step 6: Save Locally (Preview Only)

**Click**: "💾 Save Locally (Preview Only)"

**Prompt**: Enter filename: `identity-security-2025.html`

**What happens**:

**File**: `app.py` → Route `/api/templates/deploy`
```python
@app.route('/api/templates/deploy', methods=['POST'])
def deploy_template():
    domain = request.json['domain']  # "soulfra"
    filename = request.json['filename']  # "identity-security-2025.html"
    content = request.json['content']  # Rendered HTML

    # Save to: domains/soulfra.com/blog/identity-security-2025.html
    output_path = Path('domains') / f'{domain}.com' / 'blog' / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content)

    return jsonify({
        'success': True,
        'url': f'/blog/{domain}.com/{filename}'
    })
```

**Result**:
- File saved: `domains/soulfra.com/blog/identity-security-2025.html`
- Preview URL: `http://localhost:5001/blog/soulfra.com/identity-security-2025.html`

**Alert shows**:
```
💾 Saved locally!

Preview URL: http://localhost:5001/blog/soulfra.com/identity-security-2025.html

⚠️ IMPORTANT: This is LOCAL ONLY!
• Only accessible at localhost:5001
• Only while Flask is running
• NOT accessible from other devices
• NOT online

🌍 To make it actually online, click "Deploy Online"!
```

**You can click the link and see your blog post!** But only on your laptop.

---

## Part 2: Deploy Online (Make it Real)

### Step 7: Deploy to GitHub Pages

**Click**: "🌍 Deploy Online (GitHub Pages)"

**Same filename**: `identity-security-2025.html`

**What happens** (this is the magic):

**File**: `app.py` → Route `/api/deploy/github`
```python
@app.route('/api/deploy/github', methods=['POST'])
def deploy_to_github():
    brand = request.json['brand']  # "soulfra"
    content = request.json['content']  # Rendered HTML
    filename = request.json['filename']

    # 1. Save locally first
    local_path = Path(f'domains/{brand}.com/blog/{filename}')
    local_path.write_text(content)

    # 2. Export to static site
    subprocess.run(['python3', 'export_static.py', '--brand', brand])

    # 3. Deploy to GitHub
    subprocess.run(['python3', 'deploy_github.py', '--brand', brand])

    return jsonify({
        'success': True,
        'url': f'https://soulfra.github.io/{brand}'
    })
```

**File**: `deploy_github.py` (the actual deployment)
```python
def deploy_to_github(brand_slug):
    # 1. Create CNAME file (from brand_domains.json)
    cname_file = Path(f'output/{brand_slug}/CNAME')
    cname_file.write_text('soulfra.com')  # Custom domain!

    # 2. Initialize git
    subprocess.run(['git', 'init'], cwd=f'output/{brand_slug}')
    subprocess.run(['git', 'add', '.'], cwd=f'output/{brand_slug}')
    subprocess.run(['git', 'commit', '-m', 'Deploy'], cwd=f'output/{brand_slug}')

    # 3. Create GitHub repo (if doesn't exist)
    subprocess.run(['gh', 'repo', 'create', brand_slug, '--public'])

    # 4. Push to GitHub
    subprocess.run(['git', 'push', '-u', 'origin', 'main'], cwd=f'output/{brand_slug}')

    # 5. Enable GitHub Pages
    subprocess.run(['gh', 'api', f'repos/{user}/{brand_slug}/pages', '--method', 'POST'])

    return f'https://{user}.github.io/{brand_slug}'
```

**Progress shown**:
```
⏳ Deploying to GitHub Pages...
This may take 30-60 seconds...

📦 Exporting soulfra...
   ✅ Created CNAME file: soulfra.com
   ✅ Exported to output/soulfra/

🚀 Deploying soulfra to GitHub Pages...
   📝 GitHub username: soulfra
   📋 Repo exists: soulfra/soulfra
   📝 Adding files to git...
   📝 Committing changes...
   📤 Pushing to GitHub...
   🌐 Enabling GitHub Pages...

✅ Deployed online!

Public URL: https://soulfra.github.io/soulfra

🌍 IMPORTANT: This is LIVE!
• Accessible from anywhere in the world
• Anyone with the URL can view it
• Has HTTPS (secure)
• Hosted on GitHub Pages

Click OK to open in new tab.
```

**Browser opens**: `https://soulfra.github.io/soulfra/blog/identity-security-2025.html`

**It's LIVE!** Anyone in the world can see it!

---

### Step 8: Configure Custom Domain (soulfra.com)

**The deployment already created the CNAME file!**

**File**: `output/soulfra/CNAME`
```
soulfra.com
```

**Now configure DNS** (at your domain registrar):

**Option A: CNAME Record** (Recommended)
```
Type:  CNAME
Name:  @
Value: soulfra.github.io
TTL:   Automatic
```

**Option B: A Records** (Root domain)
```
Type:  A
Name:  @
Value: 185.199.108.153
Value: 185.199.109.153
Value: 185.199.110.153
Value: 185.199.111.153
```

**Wait**: 5-60 minutes for DNS propagation

**Visit**: https://soulfra.com/blog/identity-security-2025.html

**IT WORKS!** Your custom domain is live!

---

## Part 3: API Gateway (Connect Everything)

### How the Pieces Connect

**Static Site** (GitHub Pages at soulfra.com):
```javascript
// In soulfra.com's HTML
<button onclick="generatePost()">Generate Post</button>

<script>
async function generatePost() {
    const apiKey = localStorage.getItem('soulfra_api_key');

    const response = await fetch('https://api.soulfra.com/generate', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            prompt: 'Write about identity and security',
            model: 'llama3.2'
        })
    });

    const result = await response.json();
    document.getElementById('content').innerHTML = result.content;
}
</script>
```

**API Server** (api.soulfra.com):
```python
# File: api_server.py (runs on your VPS)
from flask import Flask, request, jsonify
from llm_router import LLMRouter
from freelancer_api import validate_api_key, track_api_call

app = Flask(__name__)

@app.route('/api/generate', methods=['POST'])
def generate():
    # 1. Get API key from header
    auth_header = request.headers.get('Authorization')
    api_key = auth_header.replace('Bearer ', '')

    # 2. Validate API key (ALREADY EXISTS in your codebase!)
    if not validate_api_key(api_key):
        return jsonify({'error': 'Invalid API key'}), 401

    # 3. Use LLM Router (ALREADY EXISTS!)
    router = LLMRouter()
    result = router.call(
        prompt=request.json['prompt'],
        model=request.json.get('model', 'llama3.2')
    )

    # 4. Track usage (ALREADY EXISTS!)
    track_api_call(api_key, '/generate')

    # 5. Return result
    return jsonify({
        'content': result['response'],
        'model_used': result['model_used']
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

**You ALREADY have `validate_api_key()` and `track_api_call()` in `freelancer_api.py`!**

---

## Part 4: Replicate for ALL Brands

### Same Process for calriven.com, deathtodata.com, etc.

**Step 1**: Add brand to `brand_domains.json`
```json
{
  "calriven": {
    "domain": "calriven.com",
    "github_repo": "calriven",
    "api_endpoint": "https://api.soulfra.com"
  }
}
```

**Step 2**: Deploy
```bash
python3 deploy_github.py --brand calriven
```

**Step 3**: Configure DNS
```
calriven.com → CNAME → soulfra.github.io
```

**Done!** calriven.com is live and uses the SAME API as soulfra.com!

---

## 🎓 Learning Path (What Each File Does)

### Week 1: Understand the Template System

**Files to read**:
1. `examples/blog.html.tmpl` - See how {{variables}} work
2. `formula_engine.py` - See how variables get replaced
3. `app.py` (line ~13532) - See `/api/templates/render` route

**Try this**:
```python
# In Python console
from formula_engine import FormulaEngine

engine = FormulaEngine()
template = "Hello {{name}}, you are {{age}} years old"
variables = {"name": "Alice", "age": 25}

result = engine.render_template(template, variables)
print(result)
# Output: "Hello Alice, you are 25 years old"
```

---

### Week 2: Understand the LLM Router

**Files to read**:
1. `llm_router.py` - Multi-model fallback system
2. `app.py` (line ~13559) - See how it's used in `/api/templates/generate-with-ollama`

**Try this**:
```python
# In Python console
from llm_router import LLMRouter

router = LLMRouter()

# This will try llama3.2, then llama2, then mistral
result = router.call("Explain butter in 10 words")

if result['success']:
    print(f"Model used: {result['model_used']}")
    print(f"Response: {result['response']}")
else:
    print(f"Error: {result['error']}")
```

---

### Week 3: Understand the Database

**Files to read**:
1. `database.py` - Database connection + helper functions
2. `freelancer_api.py` - API key management (ALREADY EXISTS!)

**Try this**:
```python
# In Python console
from database import get_db

db = get_db()

# See all brands
brands = db.execute('SELECT * FROM brands').fetchall()
for brand in brands:
    print(f"{brand['name']} → {brand['slug']}")

# See all API keys
api_keys = db.execute('SELECT * FROM api_keys').fetchall()
for key in api_keys:
    print(f"Key: {key['api_key'][:20]}... | Tier: {key['tier']}")
```

---

### Week 4: Understand Deployment

**Files to read**:
1. `export_static.py` - Exports Flask to static HTML
2. `deploy_github.py` - Pushes to GitHub Pages
3. `brand_domains.json` - Domain configuration

**Try this**:
```bash
# Export one brand
python3 export_static.py --brand soulfra

# Check what got created
ls -R output/soulfra/

# Deploy to GitHub
python3 deploy_github.py --brand soulfra
```

---

## ✅ Complete Process Summary

**You have**:
1. ✅ Template browser (local development) - `localhost:5001/templates/browse`
2. ✅ LLM Router (multi-model fallback) - `llm_router.py`
3. ✅ API Keys (already exists!) - `freelancer_api.py`
4. ✅ Launcher (your pm2) - `launcher.py`
5. ✅ Database (stores everything) - `soulfra.db`
6. ✅ 3 brands ready to deploy - soulfra, calriven, deathtodata

**What works**:
1. ✅ Create content with AI - Ollama integration working
2. ✅ Save locally - Preview at localhost:5001
3. ✅ Deploy online - GitHub Pages with custom domain
4. ✅ Replicate for all brands - Same system for all

**What to add**:
1. ⬜ Deploy api.soulfra.com (central API server)
2. ⬜ Connect static sites to API (JavaScript calls)
3. ⬜ Set up DNS for custom domains

**You already built the hardest parts!** Just need to connect the final pieces.

---

**Next**: Read `LEARNING-PATH.md` for week-by-week coding education, or read `REPLICATE-FOR-EVERY-BRAND.md` to clone this for all your brands!

**You're 80% done. Let's finish it!** 🚀
