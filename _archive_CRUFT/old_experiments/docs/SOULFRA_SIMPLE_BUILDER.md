# Soulfra Simple Builder - "WhatsApp for Websites" 🚀

**The 60-Second Website Generator**

Built: December 25, 2024

---

## What Is This?

Soulfra Simple Builder is the "arcade machine" orchestrator that makes Soulfra truly simple. It connects quiz → theme → auto-generation into one seamless flow.

**The Magic:**
1. User takes a 5-question personality quiz during signup
2. System auto-matches them to the perfect theme
3. QR scan → BOOM! Full website ready

**No manual setup. No configuration. Just answer 5 questions and get a complete site.**

---

## How It Works

### The Signup Flow

```
┌─────────────────┐
│  Step 1: User   │  Username + Email
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Step 2: Quiz   │  5 personality questions
└────────┬────────┘  - Vibe (calm, focused, creative...)
         │           - Communication style
         ▼           - Goals
┌─────────────────┐  - Aesthetic
│  Step 3: Plot   │  - Privacy level
└────────┬────────┘
         │           Town name + Plot type
         ▼
┌─────────────────┐
│ Step 4: Review  │  Preview + Password
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  🎉 FULL SITE AUTO-GENERATED!      │
│                                     │
│  ✓ Homepage                         │
│  ✓ Blog template                    │
│  ✓ Database schema                  │
│  ✓ Backend routes                   │
│  ✓ First welcome post               │
│  ✓ QR codes                         │
│  ✓ Arcade token (for feedback loop) │
└─────────────────────────────────────┘
```

---

## Files Modified/Created

### Core Builder
- **`soulfra_simple_builder.py`** - The orchestrator
  - `match_quiz_to_theme(quiz_answers)` - Personality → Theme matching
  - `generate_full_site(user_id, theme, answers)` - Auto-generates everything
  - `claim_anonymous_session(token, user_id)` - Links session to user

### Signup Flow
- **`templates/signup/v1_dinghy.html`** - Enhanced with 5-question quiz
  - Step 1: Username + Email
  - Step 2: ✨ Personality Quiz (NEW)
  - Step 3: Town/Plot Name
  - Step 4: Review & Confirm

### Backend Integration
- **`app.py`** (lines 4381-4490) - Signup route enhanced
  - Collects quiz answers from form
  - Calls SoulfraSimpleBuilder
  - Auto-generates full site on signup
  - Stores theme + arcade token in session

---

## The Personality Quiz

### 5 Questions That Determine Your Theme

1. **What's your vibe?**
   - 🌊 Calm & Peaceful → ocean-dreams
   - 🎯 Focused & Driven → calriven
   - 🎨 Creative & Expressive → (custom themes)
   - 🔒 Careful & Private → deathtodata
   - ⚡ Energetic & Bold

2. **How do you communicate?**
   - 💭 Thoughtful & Reflective
   - 📊 Precise & Data-Driven
   - 🎭 Expressive & Creative
   - 🤐 Private & Selective
   - 💬 Direct & Quick

3. **What brings you here?**
   - 💡 Sharing Ideas
   - 🛠️ Building Projects
   - 🔐 Privacy & Control
   - 🎨 Creating Art
   - 🤝 Connecting with Others

4. **Pick your aesthetic**
   - ⚪ Minimal & Clean
   - 💻 Technical & Precise
   - 🌈 Colorful & Vibrant
   - 🌑 Dark & Secure
   - 🌿 Natural & Organic

5. **How public is your work?**
   - 🌍 Public - Share with everyone
   - 👥 Selective - Share with some
   - 🔒 Private - Just for me

---

## Theme Matching Algorithm

The builder uses a **personality scoring system** to match quiz answers to themes from `themes/manifest.yaml`.

### Example Matches:

**Calm Creator** (calm + thoughtful + sharing + minimal + public)
```python
{
    'vibe': 'calm',
    'communication_style': 'thoughtful',
    'goals': 'sharing ideas',
    'aesthetic': 'minimal',
    'privacy': 'public'
}
# → Matched to: ocean-dreams (score: 8)
```

**Technical Builder** (focused + precise + building + technical + public)
```python
{
    'vibe': 'focused',
    'communication_style': 'precise',
    'goals': 'building projects',
    'aesthetic': 'technical',
    'privacy': 'public'
}
# → Matched to: calriven (score: 9)
```

**Privacy Advocate** (careful + private + privacy + dark + private)
```python
{
    'vibe': 'careful',
    'communication_style': 'private',
    'goals': 'privacy',
    'aesthetic': 'dark',
    'privacy': 'private'
}
# → Matched to: deathtodata (score: 12)
```

---

## The 5-Tier File Schema

Following HOW_IT_ALL_CONNECTS.md, here's what file types are generated at each tier:

### TIER 0: Binary/Raw Data
- **QR Codes** (.bmp) - Zero-dependency bitmap QR codes
  - `static/qr/user_{id}/{username}_claim.bmp` (32KB)
  - `static/qr/user_{id}/{username}_share.bmp` (32KB)
  - `static/qr/user_{id}/{username}_profile.bmp` (32KB)

### TIER 1: Database (SQL)
- **Shared Tables** (no per-user tables!)
  - `posts` table with `user_id` foreign key
  - `comments` table with `user_id` foreign key
  - `arcade_tokens` table with `user_id` foreign key
  - `qr_scans` table with `user_id` foreign key

### TIER 2: ML Processing
- (Currently handled by separate systems - not in builder)

### TIER 3: Visual Output
- **HTML Templates** (.html)
  - `templates/generated/user_{id}/homepage.html`
  - `templates/generated/user_{id}/blog.html`
- **Avatars** (.png) - Pixel art generated from username
  - `static/avatars/generated/{username}.png` (462 bytes)

### TIER 4: Distribution
- **QR Codes** (see Tier 0)
- **Posts** (in database, ready for email/export)

---

## What Gets Auto-Generated

When a user completes signup, the builder generates:

### 1. Homepage (`templates/generated/user_{id}/homepage.html`)
- Personalized with theme emoji
- Shows user's vibe from quiz
- Links to blog, QR, and features

### 2. Blog Template (`templates/generated/user_{id}/blog.html`)
- Themed with user's selected aesthetic
- Navigation links
- Dynamic post loading

### 3. Database Schema
- `user_{id}_schema` created
- Tables: posts, comments, qr_scans

### 4. Backend Routes
- `/@{username}` - Homepage
- `/@{username}/blog` - Blog
- `/@{username}/qr` - QR codes
- `/@{username}/posts` - Posts list
- `/@{username}/api/post` - API endpoint

### 5. First Welcome Post
```markdown
# 🌊 Welcome to my space!

I just set up my Soulfra site in 60 seconds!

My vibe: **calm**
My theme: **ocean-dreams**

This is the start of something new. Ready to share ideas,
build in public, and connect.

Let's go! 🚀
```

### 6. Pixel Art Avatar (`static/avatars/generated/{username}.png`)
- Auto-generated from username hash
- Unique 16x16 pixel art design
- Deterministic (same username = same avatar)
- 462 bytes PNG file

### 7. QR Codes (using qr_encoder_stdlib - zero dependencies!)
- **Claim QR** (`{username}_claim.bmp`) - 32KB
  - Links to `/claim/{username}`
  - For claiming account/session
- **Share QR** (`{username}_share.bmp`) - 32KB
  - Links to `/@{username}`
  - For sharing profile
- **Profile QR** (`{username}_profile.bmp`) - 32KB
  - Links to `/@{username}/qr`
  - For QR page access

### 8. Arcade Token
Stored in `arcade_tokens` table for the feedback loop:
```
Quiz → QR → Claim → Build → Post → Scan → Feedback → Loop
```

---

## Testing

### Test Theme Matching
```bash
python3 soulfra_simple_builder.py --test-match
```

### Test Full Site Build
```bash
python3 soulfra_simple_builder.py --test-build USER_ID
```

### Example Output
```
======================================================================
🏗️  BUILDING FULL SITE FOR USER 15
======================================================================

📝 Username: testbrand-auto
🎨 Theme: ocean-dreams
💡 Vibe: calm

⚡ Generating homepage...
⚡ Generating blog template...
⚡ Creating database schema...
⚡ Generating backend routes...
⚡ Creating welcome post...
⚡ Generating QR codes...
⚡ Creating arcade token...

======================================================================
✅ SITE BUILT SUCCESSFULLY!
======================================================================
```

---

## Database Tables

### `arcade_tokens`
Tracks the "arcade loop" for each user:

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| user_id | INTEGER | Foreign key to users |
| token | TEXT | Unique 64-char token |
| created_at | TEXT | ISO timestamp |
| loop_stage | TEXT | Current stage (build/post/scan/feedback) |

---

## Next Steps (Phase 2 & 3 from Original Plan)

### Phase 2: Make Loops Visible
- [ ] Create "Arcade Dashboard" showing token cycling
- [ ] Create "Loop Visualizer" for real-time feedback
- [ ] Move Feature Factory to `/advanced`

### Phase 3: WhatsApp-like UX
- [ ] Simplify to 5-question quiz only
- [ ] Add theme preview before signup
- [ ] Generate QR on signup completion
- [ ] Offline support
- [ ] Mobile-first design

---

## Key Insights

### What Makes This "Simple"

1. **No choices to make** - System auto-detects what you need
2. **No setup required** - Everything generated automatically
3. **Instant gratification** - Full site ready in 60 seconds
4. **Personality-driven** - Your vibe determines your theme

### The "Arcade Machine" Metaphor

Just like an arcade machine cycles tokens through a loop, Soulfra cycles session tokens through:

```
Quiz → Theme Match → Site Generation → QR Claim →
Post Creation → QR Scan → Feedback → Learn → Loop Again
```

Each stage builds on the previous, creating a self-reinforcing system.

---

## Technical Details

### Dependencies
- `yaml` - For reading themes manifest
- `sqlite3` - Database operations
- `secrets` - Secure token generation
- `datetime` - Timestamps
- Flask integration in `app.py`

### File Structure
```
soulfra-simple/
├── soulfra_simple_builder.py      # The orchestrator
├── themes/manifest.yaml            # Theme definitions
├── templates/
│   ├── signup/v1_dinghy.html      # Enhanced signup form
│   └── generated/                  # Auto-generated templates
│       └── user_{id}/
│           ├── homepage.html
│           └── blog.html
└── static/qr/                      # QR codes
    └── user_{id}/
        ├── {username}_claim.png
        ├── {username}_share.png
        └── {username}_profile.png
```

---

## Conclusion

**Soulfra Simple Builder transforms the onboarding experience from:**
- ❌ "Fill out 20 fields and configure your site"
- ✅ "Answer 5 questions and get a complete website"

**This is the foundation for "WhatsApp for websites" - dead simple, instant, and powerful.**

---

Built with ❤️ for the Soulfra ecosystem
