# GitHub + Domain Integration - Airbnb-Style Review System

## Overview

This system connects your 3 Soulfra domains (soulfra.com, deathtodata.com, calriven.com) with GitHub repositories to create organic engagement through Airbnb-style mutual reviews.

**Core Concept:**
Before anyone can comment on your content, they must:
1. Connect their GitHub account
2. Star the domain's GitHub repo
3. Leave a review of the content
4. Wait for you to review their interaction
5. Only then can both reviews be published and they can post their comment

**Why This Works:**
- **Organic GitHub Stars:** Every commenter becomes a GitHub star
- **Quality Control:** Bidirectional reviews prevent spam/trolls
- **Proof of Identity:** GitHub accounts are real, verified identities
- **Network Effect:** More comments = more stars = more visibility

---

## Architecture

### Domain → GitHub Repo Mapping

```
soulfra.com        → github.com/soulfra/soulfra
deathtodata.com    → github.com/soulfra/deathtodata
calriven.com       → github.com/soulfra/calriven
```

Each domain has its own:
- GitHub repository
- Brand theme (subdomain_router.py)
- Comment section (publish_to_github.py generates static HTML)
- Flask API backend (192.168.1.87:5001)

---

## The Complete Flow

### Step 1: User Visits Your Site

```
User visits: https://soulfra.com/blog/posts/my-post.html
  ↓
Static HTML loads from GitHub Pages
  ↓
JavaScript widget calls: http://192.168.1.87:5001/api/comments/1
  ↓
Comments displayed
```

### Step 2: User Clicks "Leave a Comment"

```
Widget checks: Do you have GitHub connected?
  ├─ NO  → Show "Connect GitHub" button
  └─ YES → Check star status (Step 3)
```

**GitHub OAuth Flow (github_faucet.py):**
1. User clicks "Connect GitHub"
2. Redirects to GitHub OAuth
3. User authorizes app
4. Callback to Flask: `/github/callback`
5. Store GitHub username + API key
6. Proceed to Step 3

### Step 3: Verify GitHub Star

```
Widget calls: GET /api/check-star?username=octocat&domain=soulfra.com
  ↓
github_star_validator.py checks:
  - Domain: soulfra.com → Repo: soulfra/soulfra
  - GitHub API: Does @octocat star soulfra/soulfra?
  ↓
  ├─ YES → Show comment form (Step 4)
  └─ NO  → Show "Star our repo to continue"
```

**Star Requirement UI:**
```html
⭐ Star Our Repo to Continue

Please star our GitHub repository before commenting.
[42 developers] have starred us so far.

[⭐ Star on GitHub]  [I've Starred - Check Now]
```

### Step 4: Submit Review (Not Comment Yet!)

```
User writes review of YOUR comment/post:
  - Rating: 1-5 stars
  - Feedback: "Great post! I learned..."
  ↓
POST /api/review/create
{
  "comment_id": 123,
  "github_username": "octocat",
  "rating": 5,
  "feedback": "Awesome content!"
}
  ↓
bidirectional_review_engine.py creates review:
  - review_id: 1
  - status: pending_reciprocal
  - requires_reciprocal: TRUE
  ↓
Stored in database (hidden from both parties)
```

### Step 5: Notify You (Comment Author)

```
📧 Email/Notification to YOU:

"@octocat reviewed your comment!"

Please review their interaction to see their feedback.

[Review @octocat Now]
```

### Step 6: You Review Them Back

```
You visit: /api/review/pending (dashboard)
  ↓
See: "@octocat (5⭐) wants to comment on 'My Post'"
  ↓
You submit reciprocal review:
  - Rating: 4 stars
  - Feedback: "Thoughtful response, thanks!"
  ↓
POST /api/review/reciprocal
{
  "original_review_id": 1,
  "rating": 4,
  "feedback": "Thanks!"
}
  ↓
bidirectional_review_engine.py:
  - Creates reciprocal_review_id: 2
  - Links review 1 ↔️ review 2
  - Sets both: requires_reciprocal = FALSE
  - PUBLISHES BOTH REVIEWS
```

### Step 7: Both See Reviews + User Can Comment

```
🎉 PUBLISHED!

@octocat sees:
  - YOUR review of them (4⭐: "Thoughtful response")

YOU see:
  - THEIR review of your post (5⭐: "Awesome content!")

@octocat can now:
  - Post their actual comment
  - Reply to thread
```

---

## Database Schema

### Extended Tables

```sql
-- Comments (from comment_voice_chain.py)
ALTER TABLE comments ADD COLUMN voice_attachment_id INTEGER;
ALTER TABLE comments ADD COLUMN qr_code TEXT;
ALTER TABLE comments ADD COLUMN chain_hash TEXT;

-- Reviews (Airbnb-style)
ALTER TABLE game_reviews ADD COLUMN github_username TEXT;
ALTER TABLE game_reviews ADD COLUMN github_starred_repo TEXT;
ALTER TABLE game_reviews ADD COLUMN github_star_timestamp TIMESTAMP;
ALTER TABLE game_reviews ADD COLUMN comment_id INTEGER REFERENCES comments(id);
ALTER TABLE game_reviews ADD COLUMN chain_hash TEXT;
ALTER TABLE game_reviews ADD COLUMN requires_reciprocal BOOLEAN DEFAULT 1;
ALTER TABLE game_reviews ADD COLUMN reciprocal_review_id INTEGER REFERENCES game_reviews(id);
```

### Relationships

```
comments (id=123)
  ↓ (comment_id foreign key)
game_reviews (id=1, requires_reciprocal=TRUE)
  ↓ (reciprocal_review_id foreign key)
game_reviews (id=2, reciprocal_review_id=1)

api_keys (github_username='octocat')
  ↓ (github_username foreign key)
game_reviews (github_username='octocat')
```

---

## API Endpoints

### GitHub Authentication

```bash
# Get GitHub OAuth URL
GET /api/github/connect
→ Returns: { "oauth_url": "https://github.com/login/oauth/authorize?..." }

# OAuth callback
GET /api/github/callback?code=abc123&state=xyz
→ Stores GitHub user, generates API key
```

### Star Verification

```bash
# Check if user starred repo
GET /api/check-star?username=octocat&domain=soulfra.com
→ Returns:
{
  "has_starred": true,
  "repo_url": "https://github.com/soulfra/soulfra",
  "star_count": 42,
  "starred_at": "2025-01-02T10:30:00"
}

# Require star (middleware)
POST /api/require-star
{
  "github_username": "octocat",
  "action": "comment"
}
→ 200 if starred, 403 if not
```

### Reviews (Airbnb-Style)

```bash
# Create review (initial, hidden)
POST /api/review/create
{
  "comment_id": 123,
  "github_username": "octocat",
  "rating": 5,
  "feedback": "Great post!"
}
→ Returns: { "review_id": 1, "status": "pending_reciprocal" }

# Create reciprocal review (publishes both)
POST /api/review/reciprocal
{
  "original_review_id": 1,
  "rating": 4,
  "feedback": "Thanks!"
}
→ Returns: { "both_published": true, "can_reply": true }

# Get pending reviews for you to reciprocate
GET /api/review/pending?user_id=15
→ Returns: [{ "id": 1, "reviewer": "@octocat", "rating": 5 }]

# Get review status
GET /api/review/status/1
→ Returns: { "status": "pending_reciprocal", "days_left": 12 }
```

### Comments (Public API)

```bash
# Get comments for post
GET /api/comments/1
→ Returns: [{ "id": 1, "content": "...", "user_name": "@octocat" }]

# Post comment (after review completed)
POST /api/comments
{
  "post_id": 1,
  "content": "Great post!",
  "github_username": "octocat"
}
→ Returns: { "comment_id": 124, "chain_hash": "abc123" }
```

### Comment-GitHub Integration

```bash
# Check reply permission (all gates)
GET /api/comment/can-reply/123?github_username=octocat
→ Returns:
{
  "allowed": false,
  "next_step": "star_repo",
  "repo_url": "https://github.com/soulfra/soulfra"
}

# Submit reply with review in one call
POST /api/comment/reply-with-review
{
  "comment_id": 123,
  "github_username": "octocat",
  "rating": 5,
  "feedback": "Cool!",
  "reply_content": "I agree!"  // optional
}
```

---

## Files Created

### 1. `github_star_validator.py`
**Purpose:** Verify GitHub users have starred domain repos

**Key functions:**
- `check_star(username, owner, repo)` - Check if starred
- `check_star_for_domain(username, domain)` - Domain-aware check
- `get_repo_for_domain(domain)` - Map domain → repo

**Usage:**
```python
validator = GitHubStarValidator()
result = validator.check_star_for_domain('octocat', 'soulfra.com')
print(result['has_starred'])  # True/False
```

### 2. `bidirectional_review_engine.py`
**Purpose:** Airbnb-style mutual review system

**Key functions:**
- `create_review()` - Create initial review (hidden)
- `create_reciprocal_review()` - Complete pair, publish both
- `get_pending_reciprocals(user_id)` - Reviews waiting for you
- `get_review_status(review_id)` - Check review state

**States:**
- `pending_reciprocal` - Waiting for other party
- `published` - Both reviews complete
- `expired` - 14-day deadline passed

### 3. `comment_github_integration.py`
**Purpose:** Orchestrate full flow (comment → GitHub → review)

**Key functions:**
- `check_reply_permission()` - All-in-one gate check
- `submit_reply_with_review()` - Unified submit endpoint
- `get_comment_reviews()` - All reviews for comment

**Checks performed:**
1. GitHub connected?
2. Repo starred?
3. Review submitted?
4. Reciprocal completed?

### 4. Updated `publish_to_github.py`
**Changes:** Added GitHub gating UI to comment widget

**New HTML elements:**
- `#github-gate` - Connect GitHub prompt
- `#star-gate` - Star repo prompt
- `#comment-form-content` - Actual comment form (hidden until ready)
- `#github-user-info` - Shows authenticated user

**JavaScript flow:**
1. Check localStorage for github_username
2. If no username → show GitHub gate
3. If username → check star via API
4. If no star → show star gate
5. If starred → show comment form

---

## GitHub Pages Setup

### Repository Structure

```
soulfra/soulfra/
├── blog/
│   ├── index.html (generated by publish_to_github.py)
│   └── posts/
│       ├── post-1.html
│       ├── post-2.html
│       └── ...
├── feed.xml (RSS)
├── about.html
└── CNAME (soulfra.com)
```

### DNS Configuration

For each domain, add:

```dns
# soulfra.com
Type: CNAME
Name: @
Value: soulfra.github.io

# www.soulfra.com
Type: CNAME
Name: www
Value: soulfra.github.io
```

Repeat for deathtodata.com, calriven.com, etc.

### GitHub Pages Settings

1. Go to repo Settings → Pages
2. Source: Deploy from branch `main` / `root`
3. Custom domain: `soulfra.com`
4. Enforce HTTPS: ✓

---

## The Flywheel Effect

```
More Comments → More Required Stars → More GitHub Visibility
                                               ↓
                                    More Organic Traffic
                                               ↓
                                          More Comments
```

**Math:**
- 100 comments = 100 GitHub stars (minimum)
- 100 stars = Better GitHub search ranking
- Better ranking = More discoverability
- More discovery = More readers = More comments
- **Flywheel accelerates!**

---

## Testing

### Manual Test Flow

1. **Test GitHub Connection:**
```bash
# Visit: http://localhost:5001/blog/posts/post-1.html
# Click "Connect GitHub"
# Enter username (OAuth coming soon)
```

2. **Test Star Check:**
```bash
curl "http://192.168.1.87:5001/api/check-star?username=YOUR_GITHUB&domain=soulfra.com"
```

3. **Test Review Creation:**
```bash
curl -X POST http://192.168.1.87:5001/api/review/create \
  -H "Content-Type: application/json" \
  -d '{
    "comment_id": 1,
    "github_username": "testuser",
    "rating": 5,
    "feedback": "Great post!"
  }'
```

4. **Test Reciprocal:**
```bash
curl -X POST http://192.168.1.87:5001/api/review/reciprocal \
  -H "Content-Type: application/json" \
  -d '{
    "original_review_id": 1,
    "rating": 4,
    "feedback": "Thanks!"
  }'
```

### CLI Testing

```bash
# Check star status
python3 github_star_validator.py --check YOUR_GITHUB --domain soulfra.com

# Run bidirectional review test
python3 bidirectional_review_engine.py

# Run integration test
python3 comment_github_integration.py
```

---

## Production Deployment

### 1. Set Environment Variables

```bash
export GITHUB_CLIENT_ID=your_github_app_id
export GITHUB_CLIENT_SECRET=your_github_app_secret
export GITHUB_REDIRECT_URI=https://soulfra.com/github/callback
```

### 2. Create GitHub OAuth App

1. Go to: https://github.com/settings/developers
2. New OAuth App
3. Application name: Soulfra
4. Homepage URL: https://soulfra.com
5. Callback URL: https://soulfra.com/github/callback (or Flask server URL)
6. Copy CLIENT_ID and CLIENT_SECRET

### 3. Deploy Flask API

```bash
# Production server (not localhost)
# Use gunicorn or uwsgi
gunicorn app:app -b 0.0.0.0:5001 --workers 4
```

### 4. Update API_BASE in Static HTML

Change in `publish_to_github.py`:
```javascript
const API_BASE = 'https://your-production-server.com';
```

### 5. Register Blueprints in app.py

```python
from github_star_validator import github_star_bp
from bidirectional_review_engine import bidirectional_review_bp
from comment_github_integration import comment_github_bp

app.register_blueprint(github_star_bp)
app.register_blueprint(bidirectional_review_bp)
app.register_blueprint(comment_github_bp)
```

---

## Why This Is Like Airbnb

### Airbnb's Review System

```
Guest stays at Host's place
  ↓
Guest writes review (HIDDEN)
  ↓
Host writes review (HIDDEN)
  ↓
After both submit OR 14 days pass:
  → BOTH reviews published simultaneously
```

**Why:** Prevents gaming. Can't see what they wrote before you write yours.

### Our Comment System

```
User reads your post
  ↓
User writes review of post (HIDDEN)
  ↓
You write review of user interaction (HIDDEN)
  ↓
After both submit OR 14 days pass:
  → BOTH reviews published + user can comment
```

**Why:** Same! Prevents:
- Users giving fake 5-stars just to comment
- You being harsh because you saw their 1-star review
- Gaming the system

---

## Next Steps

1. **Enable Full OAuth:** Replace prompt() with real GitHub OAuth flow
2. **Add Email Notifications:** Notify when reviews are ready
3. **Build Review Dashboard:** UI to manage pending reciprocals
4. **Add Voice Memos:** Integrate comment_voice_chain.py for audio reviews
5. **Blockchain Verification:** Use chain_hash for immutable audit trail
6. **Multi-Domain QR Codes:** QR codes that route to different brands

---

## Summary

You now have:

✅ **3 Domains** (soulfra, deathtodata, calriven)
✅ **GitHub Pages** (static hosting)
✅ **GitHub Star Gating** (must star to comment)
✅ **Airbnb-Style Reviews** (bidirectional, simultaneous publish)
✅ **Comment Chain Integration** (Merkle tree verification)
✅ **Domain-Specific Routing** (subdomain_router.py)

**Result:** Every comment = 1 GitHub star + 2 bidirectional reviews = Organic growth flywheel! 🚀
