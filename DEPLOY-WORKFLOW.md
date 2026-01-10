# Deploy Workflow - Why Content Manager Was Empty

> **Your issue**: "i went to the content manager but there is no post about what i asked ollama to generate even though it showed up in the templates/browse"

**Answer**: You saw a PREVIEW, not a DEPLOYED file!

---

## 🎯 The Two States of Content

### State 1: PREVIEW (Temporary)

**Where**: Template Browser → Visual tab

**What it is**: HTML rendered in memory, shown in iframe

**Stored**: NOWHERE! Only in browser memory

**Lasts**: Until you refresh the page or close browser

**Code**:
```javascript
// Template browser creates preview
const iframe = document.getElementById('previewFrame');
iframe.contentDocument.write(renderedHTML);  // Shows in browser

// BUT... nothing saved to disk!
```

**Visual**:
```
Template + Variables → Render → Show in browser
                                      ↓
                                 (nothing saved)
```

---

### State 2: DEPLOYED (Permanent)

**Where**: Content Manager shows this

**What it is**: HTML file saved to disk

**Stored**: `domains/soulfra/blog/my-post.html`

**Lasts**: Forever (until you delete it)

**Code**:
```python
# Deploy button saves to disk
output_path = Path('domains/soulfra/blog/my-post.html')
output_path.write_text(renderedHTML)  # SAVED TO DISK

# Now Content Manager can find it!
```

**Visual**:
```
Template + Variables → Render → Click Deploy → Save to domains/
                                                       ↓
                                              (Content Manager shows it)
```

---

## 📊 Side-by-Side Comparison

| Aspect | PREVIEW | DEPLOYED |
|--------|---------|----------|
| **Where you see it** | Template Browser | Content Manager |
| **Where it's stored** | Browser memory | domains/ folder on disk |
| **How long it lasts** | Until page refresh | Forever |
| **Can others access** | NO (only you) | YES (via URL) |
| **Has URL** | NO | YES (localhost:5001/blog/...) |
| **Button to create** | "Render Template" | "Deploy to Domain" |

---

## 🔄 The Complete Workflow

### What You Did:

```
1. Open Template Browser ✅
   http://localhost:5001/templates/browse

2. Click blog.html.tmpl ✅
   Loaded template

3. Click "Generate with Ollama" ✅
   Prompt: "Write about AI and branding"

4. Ollama generated content ✅
   Shows in "Generated Content" box

5. Preview updated ✅
   Visual tab shows blog post with AI content

6. ??? ❌
   You STOPPED HERE!
```

### What You Needed To Do:

```
6. Click "Deploy to Domain" ⬅️ THIS IS THE MISSING STEP!
   Enter filename: ai-branding-post.html

7. File saved ✅
   domains/soulfra/blog/ai-branding-post.html

8. Go to Content Manager ✅
   http://localhost:5001/content/manager

9. See your post! ✅
   Listed in deployed files
```

---

## 🎯 Why This Design?

**Good question**: Why two steps? Why not auto-deploy?

**Reasons**:

### 1. Preview Before Publish
```
Generate → Preview → Edit → Preview → Deploy
```
You might want to:
- Try different prompts
- Edit variables
- Check multiple templates
- Make sure it looks good

**Without preview**: Every test would create a file!

### 2. Control Over Filename
```
Deploy button asks: "Enter filename"
```
You choose:
- `ai-branding-post.html` (descriptive)
- `2025-01-01-blog.html` (dated)
- `test.html` (quick test)

### 3. Multiple Deploys
```
Same template → Different variables → Different files
```
Example:
- Generate post about AI → Deploy as `ai-post.html`
- Generate post about branding → Deploy as `branding-post.html`
- Same template, different content!

---

## 🔍 How to Tell Preview vs Deployed

### Preview (Template Browser):

**Visual clues**:
- URL: `localhost:5001/templates/browse` (still on browser page)
- Top of page: "Template Browser - Formula Engine"
- Right panel: "Visual" and "Code" tabs
- Nothing in domains/ folder

**What you see**:
```
┌──────────────────────────────────────┐
│ 🎨 Template Browser                  │
├──────────────────────────────────────┤
│ Left: Templates                      │
│ Middle: Variables                    │
│ Right: PREVIEW ← (This is temporary!)│
└──────────────────────────────────────┘
```

---

### Deployed (Content Manager):

**Visual clues**:
- URL: `localhost:5001/content/manager` (different page)
- Top of page: "Content Manager"
- Left panel: List of files
- Files exist in domains/ folder

**What you see**:
```
┌──────────────────────────────────────┐
│ 📂 Content Manager                   │
├──────────────────────────────────────┤
│ Left: Deployed files list            │
│ Right: File preview                  │
│                                      │
│ Files: ai-post.html                  │
│        branding-post.html            │
│        test.html                     │
└──────────────────────────────────────┘
```

---

## 💾 Where Files Actually Go

### Deployed Files Live Here:

```
/Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/
└── domains/
    ├── soulfra/
    │   ├── blog/
    │   │   ├── ai-post.html       ← Your deployed posts!
    │   │   ├── branding-post.html
    │   │   └── test.html
    │   └── emails/
    │       └── newsletter.html
    └── stpetepros/
        └── blog/
            └── welcome.html
```

**Access via URL**:
```
http://localhost:5001/blog/soulfra/ai-post.html
http://localhost:5001/blog/soulfra/branding-post.html
http://localhost:5001/blog/stpetepros/welcome.html
```

---

## 🎬 Step-by-Step Fix (Do This Now!)

### Let's deploy your generated content:

```bash
# 1. Open Template Browser
http://localhost:5001/templates/browse

# 2. Click blog.html.tmpl (or email.html.tmpl)

# 3. Variables are already filled in (default values)

# 4. Generate with Ollama
Prompt: "Write a blog post about AI and branding"
Click "Generate Content"
Wait ~10 seconds

# 5. See preview
Visual tab shows: Blog post with AI content ✅
Generated Content box shows: The AI text ✅

# 6. NOW CLICK "DEPLOY TO DOMAIN" ← DO THIS!
Button at top right of page

# 7. Enter filename
Type: ai-branding-post.html
Click OK

# 8. Success message
"✅ Deployed!
Path: domains/soulfra/blog/ai-branding-post.html
URL: /blog/soulfra/ai-branding-post.html"

# 9. Go to Content Manager
http://localhost:5001/content/manager

# 10. See your file!
Left panel: ai-branding-post.html (listed!)
Click it → Preview shows your content
```

---

## 🐛 Common Mistakes

### Mistake 1: "I clicked Render, why not in Content Manager?"

**What you did**: Click "Render Template"

**What it does**: Shows PREVIEW only

**What you need**: Click "Deploy to Domain"

---

### Mistake 2: "I generated with Ollama, isn't that deployed?"

**What you did**: Click "Generate Content"

**What it does**:
- Calls Ollama ✅
- Shows generated text ✅
- Updates preview ✅
- Does NOT save file ❌

**What you need**: Click "Deploy to Domain" AFTER generating

---

### Mistake 3: "The preview looks good, where is it?"

**Answer**: Preview is in browser memory!

**Analogy**:
```
Preview = Looking at a photo on your phone
Deploy  = Saving the photo to camera roll
```

You need to SAVE it (deploy) for it to persist!

---

## 📋 Cheat Sheet

| I want to... | Action | Where to look |
|--------------|--------|---------------|
| **See if template works** | Render Template | Template Browser → Visual tab |
| **Test with Ollama** | Generate Content | Template Browser → Generated Content box |
| **Save permanently** | Deploy to Domain | Enter filename → Check Content Manager |
| **View deployed files** | N/A | Content Manager → Left panel |
| **Delete a deployed file** | Select file | Content Manager → Delete button |
| **Access via URL** | Deploy first | localhost:5001/blog/{domain}/{filename} |

---

## 🎯 Quick Reference

### To CREATE content:
```
Template Browser → Generate → Preview → Deploy
```

### To VIEW deployed content:
```
Content Manager → Click file → Preview/Open
```

### To ACCESS via URL:
```
localhost:5001/blog/soulfra/filename.html
```

---

## ✅ Summary

**Why Content Manager was empty**:
- ❌ You PREVIEWED content (Template Browser)
- ❌ You did NOT DEPLOY content (missing step!)
- ❌ Content Manager only shows DEPLOYED files

**The fix**:
- ✅ Generate content (you did this)
- ✅ See preview (you did this)
- ✅ Click "Deploy to Domain" (DO THIS!)
- ✅ Enter filename (my-post.html)
- ✅ Now Content Manager shows it!

**Remember**:
```
PREVIEW = Temporary (browser memory)
DEPLOY  = Permanent (saved to disk)
```

**Always deploy if you want to keep it!**

---

**Try it now**: Follow the step-by-step above and deploy your first post!
