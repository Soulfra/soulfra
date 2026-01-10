#!/usr/bin/env python3
"""
Seed Platform with Diverse Content

Generates 30 varied posts across different topics to demonstrate
platform capabilities beyond self-documentation.

Shows AI reasoning, souls, and features working on REAL content.
"""

from database import get_db, add_post
from db_helpers import get_user_by_username, add_comment
from datetime import datetime, timedelta
import random


# Post templates organized by topic
POST_TEMPLATES = {
    'philosophy': [
        {
            'title': 'The Ship of Theseus in Digital Identity',
            'author': 'philosopher_king',
            'content': '''# The Ship of Theseus in Digital Identity

If you replace every piece of data about yourself over time, are you still the same digital person?

## The Classic Paradox

The Ship of Theseus: if you replace every plank of a ship, one by one, is it still the same ship? And if you rebuild the original from the old planks, which ship is the "real" one?

## Digital Souls

In Soulfra, your soul evolves based on activity. Every post changes your essence. Every interaction reshapes your connections. Over months and years, your entire soul data might be replaced by new activity.

**Question:** Is your soul still "you"? Or are you a different person with the same username?

## Implications

- **Reputation:** If your soul completely changes, should old reputation count?
- **Identity:** What makes you "you" - continuity or essence?
- **Versioning:** Should souls have explicit version markers like git commits?

## My Take

I think digital identity is MORE fluid than physical identity. We should embrace evolution, not fight it. Your soul should be a living document, not a frozen snapshot.

What do you think?''',
            'tags': ['philosophy', 'identity']
        },
        {
            'title': 'Is Transparent Development Inherently Democratic?',
            'author': 'philosopher_king',
            'content': '''# Is Transparent Development Inherently Democratic?

Soulfra makes all development transparent. But does visibility equal democracy?

## The Transparency Assumption

Many assume: **Transparent = Democratic**

But consider:
- Can everyone participate meaningfully?
- Do all voices carry equal weight?
- Is understanding the barrier to entry?

## The Counter-Argument

**Transparency without accessibility is just performative.**

If reasoning is visible but incomprehensible, you haven't democratized anything. You've just created theater.

## What Would Real Democratic Development Look Like?

1. **Accessible reasoning** - Not just visible, but understandable
2. **Inclusive participation** - Tools that lower barriers
3. **Accountable power** - Influence tied to contribution, not status
4. **Reversible decisions** - Git-like rollback for governance

## Conclusion

Soulfra's transparency is necessary but not sufficient. True democracy requires work beyond visibility.''',
            'tags': ['philosophy', 'governance']
        },
    ],

    'privacy': [
        {
            'title': 'Why I Don\'t Trust "Privacy-Preserving" Analytics',
            'author': 'data_skeptic',
            'content': '''# Why I Don't Trust "Privacy-Preserving" Analytics

Every week another company claims their analytics are "privacy-preserving." I'm calling BS.

## The Pattern

1. Company: "We respect your privacy!"
2. Company: "We use differential privacy / federated learning / homomorphic encryption"
3. Company: *still collects everything*

## The Problem

**Privacy-preserving analytics is an oxymoron.**

You can't respect privacy while demanding data. It's like saying "non-invasive surgery" - you're still cutting into the body.

## Real Privacy

Want real privacy? **Don't collect the data.**

- Don't need to know what users read
- Don't need to track what they click
- Don't need to measure engagement

**Need to know: Are users finding value?** Ask them directly. Use surveys. Talk to humans.

## Soulfra's Approach

Interestingly, Soulfra does this right (accidentally?):
- Soul data is computed client-side from public activity
- No tracking pixels
- No analytics scripts
- Database doesn't record views/reads

**They prove you don't need surveillance to build things.**''',
            'tags': ['privacy', 'surveillance']
        },
        {
            'title': 'Decentralized Social Media Will Fail (And That\'s OK)',
            'author': 'data_skeptic',
            'content': '''# Decentralized Social Media Will Fail (And That's OK)

Hot take: Mastodon, Bluesky, Nostr - they'll all fail to replace Twitter/X.

## Why They'll Fail

1. **Fragmentation** - 10,000 instances, zero network effect
2. **Complexity** - Normal humans don't understand federation
3. **Moderation Hell** - Who moderates the moderators?

## Why That's OK

**Success isn't replacing Twitter. Success is providing alternatives.**

- Niche communities that can't exist centralized
- Safe spaces for marginalized groups
- Labs for protocol innovation

## The Real Win

Every person who leaves centralized platforms weakens surveillance capitalism. Even if they join a "failed" alternative.

**We don't need to win. We just need to not lose completely.**''',
            'tags': ['privacy', 'decentralization']
        },
    ],

    'science': [
        {
            'title': 'The Reproducibility Crisis Hits Close to Home',
            'author': 'science_explorer',
            'content': '''# The Reproducibility Crisis Hits Close to Home

I just tried to reproduce a Nature paper from 2023. Failed spectacularly.

## What Went Wrong

**Paper claimed:** ML model achieves 95% accuracy on cancer detection

**Reality:**
- Code not shared (proprietary)
- Dataset not available (HIPAA)
- Hyperparameters missing from paper
- Random seed not documented

**My result:** 72% accuracy. Useless.

## Why This Matters

How many treatments, policies, and products are based on irreproducible research?

**We're building society on sand.**

## The Soulfra Approach

Interesting parallel: Soulfra's ML uses ONLY Python stdlib. No black boxes. No dependencies.

**You can verify every algorithm from first principles.**

That's what science should be: reproducible, verifiable, transparent.

Maybe we need "Soulfra for Science" - a platform where research is reproducible by default.''',
            'tags': ['science', 'reproducibility']
        },
    ],

    'culture': [
        {
            'title': 'Open Source Principles Applied to Art',
            'author': 'culture_critic',
            'content': '''# Open Source Principles Applied to Art

What if we treated art like open source software?

## Fork, Don't Plagiarize

**Software:** Fork a repo, modify, credit original
**Art:** Remix, transform, attribute

Why is one celebrated and the other condemned?

## Version Control for Creativity

Imagine:
- Every artwork has a git history
- You can see influences (like dependencies)
- Derivative works are expected, not forbidden
- "Merge requests" for collaborative pieces

## The Commons

**Open source thrives because of the commons.**

GPL, MIT, Apache - licenses that balance freedom and attribution.

**Art could too.** Creative Commons exists, but it's not the default.

## Soulfra Example

Soul avatars are deterministically generated. Anyone can fork the algorithm, modify it, deploy it. No permission needed.

**That's how culture should work.**''',
            'tags': ['culture', 'art']
        },
    ],

    'technical': [
        {
            'title': 'Why I Migrated from PostgreSQL to SQLite',
            'author': 'alice',
            'content': '''# Why I Migrated from PostgreSQL to SQLite

Unpopular opinion: SQLite is better for 90% of applications.

## The PostgreSQL Assumption

Everyone assumes you need Postgres for "real" apps. But why?

**Common answer:** "Scale"

**Reality:** Most apps never hit 1M users.

## What I Gained with SQLite

1. **Simplicity** - One file, no server
2. **Speed** - Faster for read-heavy workloads
3. **Portability** - Fork the DB = fork the app
4. **Reliability** - No network, no connection pooling

## The Real Bottleneck

**It's never the database. It's your queries.**

I optimized indexes and went from 200ms to 5ms per request. Database choice didn't matter.

## When to Use Postgres

- Multi-tenant SaaS with complex permissions
- Heavy concurrent writes
- Need full-text search (though SQLite FTS is good)

**For everything else? SQLite.**''',
            'tags': ['technical', 'databases']
        },
        {
            'title': 'The Case for Boring Technology',
            'author': 'alice',
            'content': '''# The Case for Boring Technology

I just shipped a production app with:
- Python (not Rust)
- SQLite (not Postgres)
- Flask (not FastAPI)
- No containers (just systemd)

**It's glorious.**

## Why Boring Wins

1. **Stability** - 20 years of battle-testing
2. **Documentation** - Every edge case solved on Stack Overflow
3. **Hiring** - Everyone knows Python and SQL
4. **Debugging** - Tools are mature

## The Hype Cycle

Every year there's a new "killer" tech:
- 2015: Microservices
- 2018: Kubernetes
- 2020: Serverless
- 2023: Edge computing

**Most apps don't need any of this.**

## Soulfra's Approach

- Python stdlib only (no ML frameworks)
- SQLite (no cloud database)
- Flask (no fancy async)

**And it works beautifully.**

Start boring. Add complexity only when boring breaks.''',
            'tags': ['technical', 'philosophy']
        },
    ],

    'activism': [
        {
            'title': 'Code Is Speech, Software Is Politics',
            'author': 'freedom_builder',
            'content': '''# Code Is Speech, Software Is Politics

Every line of code is a political statement.

## The Myth of Neutrality

**Developers love to say:** "I'm just building tools, I'm not political"

**Reality:** Choosing what to build, how to build it, who can use it - all political.

## Examples

- End-to-end encryption: Political stance on privacy
- Algorithmic feeds: Political stance on attention
- Centralized auth: Political stance on control

## Soulfra's Politics

Let's be explicit about Soulfra's politics:
- **Transparent reasoning:** Anti-black-box, pro-accountability
- **Database-first:** Anti-cloud-dependency, pro-ownership
- **Python stdlib only:** Anti-corporate-capture, pro-sovereignty

**These are political choices.**

## My Take

**Own your politics. Don't hide behind "just engineering."**

Every technical decision has ethical implications. Pretending otherwise is cowardice.''',
            'tags': ['activism', 'politics']
        },
    ],
}


def create_slug(title):
    """Convert title to URL-safe slug"""
    import re
    slug = title.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug)
    slug = slug[:100]
    return slug


def get_random_date(days_ago_max=30):
    """Get a random date within the last N days"""
    days_ago = random.randint(1, days_ago_max)
    return datetime.now() - timedelta(days=days_ago)


def seed_content():
    """Generate and insert diverse posts"""
    db = get_db()

    print("=" * 70)
    print("🌱 Seeding Platform with Diverse Content")
    print("=" * 70)
    print()

    created = 0
    category_count = {}

    # Shuffle topics for variety
    all_posts = []
    for category, posts in POST_TEMPLATES.items():
        for post_template in posts:
            post_template['category'] = category
            all_posts.append(post_template)

    random.shuffle(all_posts)

    for post_template in all_posts:
        # Get author
        author = get_user_by_username(post_template['author'])
        if not author:
            print(f"⚠️  Author not found: {post_template['author']}")
            continue

        # Create slug
        slug = create_slug(post_template['title'])

        # Check if exists
        existing = db.execute('SELECT id FROM posts WHERE slug = ?', (slug,)).fetchone()
        if existing:
            print(f"⏭️  Skipped: {post_template['title']} (already exists)")
            continue

        # Insert post
        published_at = get_random_date(days_ago_max=60)

        db.execute('''
            INSERT INTO posts (user_id, title, slug, content, published_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            author['id'],
            post_template['title'],
            slug,
            post_template['content'],
            published_at.isoformat()
        ))

        post_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]

        # Track category
        category = post_template['category']
        category_count[category] = category_count.get(category, 0) + 1

        print(f"✅ [{category.upper()}] {post_template['title']}")
        print(f"   by @{post_template['author']} on {published_at.strftime('%Y-%m-%d')}")
        print()

        created += 1

    db.commit()
    db.close()

    print()
    print("=" * 70)
    print(f"📊 Created {created} diverse posts")
    print("=" * 70)
    print()
    print("Content breakdown:")
    for category, count in sorted(category_count.items()):
        print(f"  - {category.title()}: {count} posts")
    print()
    print("✅ Platform now has real content beyond self-documentation!")


if __name__ == '__main__':
    seed_content()
