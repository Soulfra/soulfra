#!/usr/bin/env python3
"""
Quick Seed Posts - Create blog posts using existing admin user

Populates homepage with content from the 85+ markdown documentation files.
"""

from database import get_db
from datetime import datetime, timedelta
import random

def create_post(db, title, content, slug, user_id=1, days_ago=0):
    """Create a single post"""
    published_at = datetime.now() - timedelta(days=days_ago)

    try:
        cursor = db.execute('''
            INSERT INTO posts (title, content, slug, user_id, published_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (title, content, slug, user_id, published_at))
        db.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"⚠️  Error creating post '{title}': {e}")
        return None


def main():
    print("\n" + "="*70)
    print("🌱 Quick Seed - Populate Homepage with Blog Posts")
    print("="*70)

    db = get_db()

    # Check current post count
    current = db.execute("SELECT COUNT(*) as count FROM posts").fetchone()['count']
    print(f"\n📊 Current posts in database: {current}")

    # Sample posts based on actual Soulfra documentation
    posts = [
        {
            'title': 'Welcome to Soulfra - Self-Documenting Development',
            'slug': 'welcome-to-soulfra',
            'content': '''# Welcome to Soulfra

Soulfra is a self-documenting development platform that combines:

## Core Features

- **AI Reasoning**: 4 AI personas (CalRiven, DeathToData, TheAuditor, Soulfra) that discuss and validate code
- **Soul-Based Profiles**: User profiles that evolve based on activity and interactions
- **Brand System**: Create and manage multiple brand identities with unique personalities
- **QR Code Tracking**: Track user acquisition and engagement through QR codes
- **Neural Networks**: ML models that learn from user behavior and discussions

## Philosophy

Instead of manually writing documentation, Soulfra generates it automatically from:
- Code changes (via git commits)
- AI discussions about features
- User interactions and feedback
- Test results and validations

The platform "documents itself" as you use it.

## Getting Started

1. Create an account at `/signup`
2. Explore brand discussions at `/brand/discuss/<brand>`
3. Play Cringeproof game at `/cringeproof`
4. Check out the brand builder at `/brand/<slug>`

Start building!''',
            'days_ago': 30
        },
        {
            'title': 'Cringeproof: Understanding Intent vs Intuition',
            'slug': 'cringeproof-intent-vs-intuition',
            'content': '''# Cringeproof: Intent vs Intuition

Cringeproof is a self-awareness game that reveals your personality type through 7 simple questions.

## The Two Types

### Intentional (Low Scores: 7-21)
- **Focus**: External world, action
- **Process**: See problem → Act immediately
- **Strength**: Quick decisions, confident execution
- **Example**: Message received → Reply right away

### Intuitive (High Scores: 22-35)
- **Focus**: Internal world, reflection
- **Process**: See problem → Think → Analyze → Act
- **Strength**: Thoughtful, considers all angles
- **Example**: Message received → Read 3 times → Draft → Edit → Send

## Why Both Matter

- Intentional people move things forward
- Intuitive people ensure quality
- **Together = Unstoppable team**

## Multiplayer Mode

Create a room, share with friends on same WiFi, and compare personality types:
- See how you differ
- Discover best collaboration pairings
- Build better teams based on personality, not guesswork

Try it at `/cringeproof`!''',
            'days_ago': 25
        },
        {
            'title': 'Brand Licensing: The Buff System Explained',
            'slug': 'brand-licensing-buff-system',
            'content': '''# Brand Licensing: The Buff System

Think of brand licensing like World of Warcraft's buff system - different licenses give different "powers" to your brand.

## License Types

### CC0 (Public Domain)
- **Allows**: Everything (commercial, derivatives, sharing)
- **Requires**: Nothing
- **Buff**: Maximum freedom, maximum reach

### CC-BY (Attribution)
- **Allows**: Commercial use, derivatives, sharing
- **Requires**: Give credit to original creator
- **Buff**: Spread with credit

### Proprietary
- **Allows**: View only
- **Requires**: Permission for any use
- **Buff**: Full control, restricted sharing

## How It Works

1. Create a brand at `/brand/<slug>`
2. Choose license type (default: CC0)
3. Others can use your brand identity:
   - Colors, personality, tone
   - Product templates
   - Brand values

4. License determines what they can do:
   - Copy directly (CC0)
   - Adapt with credit (CC-BY)
   - Request permission (Proprietary)

## Strategy

- **CC0**: Build ecosystem, encourage remixes
- **CC-BY**: Track influence, get credit
- **Proprietary**: Maintain exclusivity

Choose your buff wisely!''',
            'days_ago': 20
        },
        {
            'title': 'Neural Networks: Learning From QR Scans',
            'slug': 'neural-networks-qr-scans',
            'content': '''# Neural Networks: Learning From QR Scans

Soulfra's ML infrastructure learns from everything you do - especially QR code scans.

## The Training Loop

1. **Generate QR Code**
   - Brand creates QR code linking to `/brand/<slug>`
   - QR code tracks: brand_id, scan_location, utm params

2. **User Scans**
   - Phone camera scans QR → redirects to brand page
   - Scan logged in `qr_scans` table
   - Session cookie tracks user journey

3. **Neural Network Learns**
   - Which brands get most scans?
   - Which locations convert best?
   - Which UTM params drive engagement?
   - Which users share QR codes most?

4. **Recommendations**
   - Suggest brands to promote
   - Optimize QR placement
   - Predict successful campaigns

## Session Tracking

Cookies act as "compiler checkpoints" for the ML transformer:
- Entry point (QR scan, link, search)
- Pages visited
- Time spent
- Actions taken (signup, discussion, game)

## Future: Transformer Training

Neural networks will:
- Predict which content you'll like
- Suggest ideal collaboration partners
- Match you with compatible brands
- Optimize your brand's reach

All from simple QR code scans!''',
            'days_ago': 15
        },
        {
            'title': 'Wikipedia-Style Brand Discussions',
            'slug': 'wikipedia-brand-discussions',
            'content': '''# Wikipedia-Style Brand Discussions

Brand discussions are open like Wikipedia - read without login, contribute with account.

## How It Works

1. **Anonymous Reading**
   - Visit `/brand/discuss/<brand_name>`
   - See all messages without logging in
   - Browse different AI persona perspectives

2. **Login to Contribute**
   - Create account → join discussion
   - Ask questions, share ideas
   - AI responds with brand expertise

3. **Champion Ideas**
   - Vote on best messages
   - Build on others' thoughts
   - Collaborative brand building

## AI Personas

### CalRiven
- **Role**: Technical expert
- **Focus**: Implementation, architecture
- **When to ask**: "How do I build this?"

### DeathToData
- **Role**: Privacy advocate
- **Focus**: Security, data protection
- **When to ask**: "Is this safe/private?"

### TheAuditor
- **Role**: Validator
- **Focus**: Testing, verification
- **When to ask**: "Does this actually work?"

### Soulfra
- **Role**: Platform guide
- **Focus**: Integration, user experience
- **When to ask**: "How does this fit together?"

## Real-Time Discussion

All discussions saved to:
- `discussion_sessions` - Conversation threads
- `discussion_messages` - Individual messages
- Can export to SOP documents
- Generate documentation automatically

Try it: `/brand/discuss/deathtodata`''',
            'days_ago': 10
        },
        {
            'title': 'The Frontend Architecture: HTML, API, and Web Components',
            'slug': 'frontend-architecture-explained',
            'content': '''# The Frontend Architecture

Soulfra uses three different frontend approaches depending on complexity.

## 1. Pure HTML (Form POST)

**Example**: Cringeproof game
```html
<form method="POST" action="/cringeproof/submit">
  <input type="radio" name="q1" value="1"> Strongly Disagree
  <input type="radio" name="q1" value="5"> Strongly Agree
  <button type="submit">Submit</button>
</form>
```

**Flow**:
Browser → Server → Process → Return HTML

**When to use**:
- Simple forms
- No real-time updates needed
- Works without JavaScript

## 2. HTML + API (fetch() Calls)

**Example**: Brand discussions
```javascript
fetch('/api/studio/chat', {
  method: 'POST',
  body: JSON.stringify({message, persona})
})
.then(r => r.json())
.then(data => addMessage(data.response))
```

**Flow**:
Browser ←fetch()→ Server → AI → JSON response

**When to use**:
- Real-time features (chat, live updates)
- Dynamic content
- Progressive enhancement

## 3. Web Components (Future)

**Example**: Reusable game questions
```html
<cringeproof-question
  text="I triple-check my texts"
  id="q1">
</cringeproof-question>
```

**When to use**:
- Reusable UI elements
- Custom behavior encapsulation
- Future-proof architecture

## Strategy

Start with **Pure HTML** (works everywhere).
Add **API calls** when needed (real-time).
Refactor to **Web Components** when patterns emerge.

Progressive enhancement FTW!''',
            'days_ago': 5
        },
        {
            'title': 'Moral Dilemmas: Next Phase of Cringeproof',
            'slug': 'moral-dilemmas-cringeproof',
            'content': '''# Moral Dilemmas: Next Phase of Cringeproof

Cringeproof currently measures **Intent vs Intuition**. Next: **Value alignment** through moral dilemmas.

## The Idea

Beyond personality type, measure ethical framework:

### Privacy vs Security
> "Should platforms monitor messages to prevent terrorism?"

- **Privacy-first**: No, principles matter more than edge cases
- **Security-first**: Yes, must act to protect people

### Truth vs Kindness
> "Would you lie to protect someone's feelings?"

- **Truth-oriented**: No, honesty builds trust
- **Compassion-oriented**: Yes, sometimes kindness matters more

### Individual vs Collective
> "Ban user who violates terms to protect community?"

- **Individual rights**: No, everyone deserves second chances
- **Community health**: Yes, one bad actor ruins it for all

## Personality + Values = Better Pairing

Current Cringeproof:
- Intent vs Intuition → collaboration style

Future Cringeproof:
- Moral framework → value alignment

## Suggested Pairings

**Aligned values** (easy collaboration):
- Both privacy-first → Trust each other's decisions
- Both truth-oriented → Direct communication

**Opposite values** (productive debate):
- Privacy vs Security → Force consideration of tradeoffs
- Truth vs Kindness → Balance honesty with empathy

## Room Types

- **"Aligned"**: Only similar values (echo chamber mode)
- **"Diverse"**: Mix of all types (debate mode)
- **"Debate"**: Opposite values discuss specific dilemmas

## Implementation

Add 5-7 moral dilemma questions to Cringeproof.
Score on multiple axes:
- Privacy ←→ Security
- Truth ←→ Kindness
- Individual ←→ Collective

Match people based on:
1. Personality (Intent/Intuition)
2. Values (moral framework)
3. Goals (collaboration vs debate)

Coming soon!''',
            'days_ago': 3
        },
        {
            'title': 'Zero Dependencies: Python Stdlib Only',
            'slug': 'zero-dependencies-python-stdlib',
            'content': '''# Zero Dependencies: Python Stdlib Only

Soulfra runs entirely on Python standard library - no pip install required.

## Why?

**Dependencies rot**:
- Libraries get abandoned
- Breaking changes
- Security vulnerabilities
- Version conflicts

**Stdlib is stable**:
- Guaranteed to work
- Security updates from Python
- No dependency hell
- Works offline

## What We Built

### QR Code Generator (`qr_encoder_stdlib.py`)
- Pure Python Reed-Solomon error correction
- BMP image generation
- No pillow, no qrcode library

### URL Shortener
- Base64 encoding
- Hash-based short codes
- No external service

### Email System
- SMTP via `smtplib`
- HTML email templates
- No sendgrid, no mailgun

### Session Management
- Cookie-based sessions
- No Redis, no memcached
- Database-backed persistence

## Tradeoffs

**Pros**:
- ✅ No dependencies to manage
- ✅ Works offline
- ✅ Security (less attack surface)
- ✅ Longevity (still works in 10 years)

**Cons**:
- ⚠️ More code to write
- ⚠️ Can't use fancy libraries
- ⚠️ Reinvent some wheels

## Philosophy

**Dependencies are debt**.

Every external library is a promise that:
- It will keep working
- It won't break your code
- It will get security updates
- The maintainer won't abandon it

Most projects violate all four. So we use **stdlib only** and sleep well at night.

The code is ours. Forever.''',
            'days_ago': 1
        },
        {
            'title': 'The Self-Documenting Platform Philosophy',
            'slug': 'self-documenting-platform',
            'content': '''# The Self-Documenting Platform Philosophy

Traditional platforms: Build features → Write docs (maybe).

Soulfra: Features **are** the documentation.

## The Problem

Most platforms have:
- Outdated docs (code changed, docs didn't)
- Missing docs (feature shipped, docs didn't)
- Wrong docs (copy-paste errors)

Why? **Docs are manual work**.

## The Solution

**Generate docs automatically** from:

### 1. Git Commits
```bash
git commit -m "Add brand licensing system"
```
→ Creates blog post explaining feature

### 2. AI Discussions
```
User: "How does brand licensing work?"
AI: [detailed explanation]
```
→ Saves as SOP document

### 3. Test Results
```python
def test_qr_scan():
    # QR scan flow documented in test
```
→ Generates user guide

### 4. User Interactions
```
User scans QR → creates account → joins discussion
```
→ Analytics show user journey → docs update

## Benefits

- **Always current**: Docs generated from actual code
- **Complete**: Every feature auto-documented
- **Accurate**: Can't be wrong (comes from source)
- **Effortless**: No manual doc writing

## How It Works

1. Make code change
2. AI personas discuss it
3. Platform generates:
   - Blog post (for users)
   - API docs (for developers)
   - Tutorial (for beginners)
   - SOP (for team)

4. Docs published automatically

## Philosophy

**If you can't document it automatically, the feature is too complex.**

Simplify until it documents itself.

That's Soulfra.''',
            'days_ago': 0
        }
    ]

    created = 0
    for post_data in posts:
        post_id = create_post(
            db=db,
            title=post_data['title'],
            content=post_data['content'],
            slug=post_data['slug'],
            user_id=1,  # admin user
            days_ago=post_data.get('days_ago', 0)
        )
        if post_id:
            created += 1
            print(f"✅ Created: {post_data['title']}")

    # Verify final count
    final = db.execute("SELECT COUNT(*) as count FROM posts").fetchone()['count']

    print("\n" + "="*70)
    print(f"📊 Created {created} new posts")
    print(f"📊 Total posts in database: {final}")
    print("="*70)

    print("\n✅ Homepage should now show blog posts!")
    print("   Visit: http://localhost:5001/")

    db.close()


if __name__ == '__main__':
    main()
