#!/usr/bin/env python3
"""
Public Builder - Build in Public Automation Engine

This is the core automation that makes Soulfra build itself in public:

1. Check feedback → Find high-priority items
2. CalRiven creates post → Documents the fix/feature
3. Reasoning engine analyzes → Other AIs weigh in
4. Gallery updates → New showcase generated
5. QR code created → Track scans as time capsule
6. Email digest → Tell users what got built

This automates the "build in public" workflow.
Run this via cron every hour or trigger manually.
"""

import re
from datetime import datetime, timedelta
from database import get_db
from reasoning_engine import ReasoningEngine
from reputation import award_bits


def generate_excerpt(html_content, max_length=200):
    """
    Generate a clean excerpt from HTML content

    Preserves some formatting (bold, emphasis) but removes complex HTML.
    Extracts first meaningful paragraph or section.

    Args:
        html_content: HTML string
        max_length: Maximum character length for excerpt

    Returns:
        str: Clean excerpt with minimal HTML formatting
    """
    # Remove script, style, code blocks
    text = re.sub(r'<(script|style|pre|code)[^>]*>.*?</\1>', '', html_content, flags=re.DOTALL)

    # Remove HTML comments
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)

    # Extract first meaningful paragraph (skip headers)
    paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', text, flags=re.DOTALL)
    if paragraphs:
        # Use first paragraph
        excerpt = paragraphs[0]
    else:
        # Fallback: get content after first header
        after_header = re.sub(r'^.*?</h[1-6]>', '', text, flags=re.DOTALL)
        excerpt = after_header

    # Keep only simple formatting: <strong>, <em>, <b>, <i>
    excerpt = re.sub(r'<(?!/?(?:strong|em|b|i)\b)[^>]+>', '', excerpt)

    # Clean up whitespace
    excerpt = re.sub(r'\s+', ' ', excerpt).strip()

    # Truncate to max length
    if len(excerpt) > max_length:
        excerpt = excerpt[:max_length].rsplit(' ', 1)[0]

    return excerpt


def check_feedback_for_building():
    """
    Find feedback that should trigger a build-in-public post
    
    Priority:
    - Multiple people reporting same issue
    - Feedback marked as "high priority"
    - Keywords: bug, broken, doesn't work, error
    
    Returns:
        list: Feedback items to build from
    """
    db = get_db()
    
    # Get recent unprocessed feedback (last 24 hours)
    feedback_items = db.execute('''
        SELECT id, name, email, component, message, created_at
        FROM feedback
        WHERE status = 'new'
        AND created_at > datetime('now', '-24 hours')
        ORDER BY created_at DESC
    ''').fetchall()
    
    db.close()
    
    # Prioritize feedback
    priority_items = []
    
    for item in feedback_items:
        score = 0
        message_lower = item['message'].lower()
        
        # Bug keywords = high priority
        if any(word in message_lower for word in ['bug', 'broken', 'error', 'crash', 'fail']):
            score += 10
        
        # Feature requests = medium priority
        if any(word in message_lower for word in ['should', 'could', 'want', 'need', 'feature']):
            score += 5
        
        # Multiple component mentions = system-wide issue
        if item['component'] in ['Reasoning Engine', 'Admin Panel', 'Soul Browser']:
            score += 5
        
        if score >= 10:  # High priority threshold
            priority_items.append({
                'feedback_id': item['id'],
                'score': score,
                'component': item['component'],
                'message': item['message'],
                'reporter': item['name'] or 'Anonymous'
            })
    
    return sorted(priority_items, key=lambda x: x['score'], reverse=True)


def create_post_from_feedback(feedback_item):
    """
    CalRiven creates a post documenting the fix

    Args:
        feedback_item: Dict with feedback data

    Returns:
        int: Post ID created
    """
    # Check if this feedback already has a post (prevent duplicates)
    db = get_db()
    existing = db.execute('''
        SELECT post_id FROM feedback
        WHERE id = ? AND post_id IS NOT NULL
    ''', (feedback_item['feedback_id'],)).fetchone()

    if existing:
        print(f"   ⊘ Feedback #{feedback_item['feedback_id']} already has post #{existing['post_id']} (skipping duplicate)")
        db.close()
        return existing['post_id']

    db.close()

    component = feedback_item['component']
    message = feedback_item['message']
    reporter = feedback_item['reporter']

    # Generate post title
    if 'bug' in message.lower() or 'broken' in message.lower():
        post_type = "Bug Fix"
    elif 'feature' in message.lower() or 'should' in message.lower():
        post_type = "Feature Request"
    else:
        post_type = "Improvement"

    title = f"{post_type}: {component}"
    
    # Generate post content
    content = f"""
<h2>🔧 {post_type} - {component}</h2>

<h3>Feedback from {reporter}</h3>
<blockquote style="border-left: 4px solid #007bff; padding-left: 1rem; color: #666;">
{message}
</blockquote>

<h3>Status: In Progress</h3>
<p>We're addressing this feedback and building the fix in public. Watch this post for updates.</p>

<h3>How You Can Help</h3>
<ul>
<li>Comment with additional context or examples</li>
<li>Test the fix when it's ready</li>
<li>Share your own experiences with this issue</li>
</ul>

<p><em>This post was auto-generated from public feedback. That's build-in-public! 🚀</em></p>
"""
    
    # Create slug with timestamp to avoid duplicates
    base_slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    slug = f"{base_slug}-{timestamp}"

    # Generate excerpt for homepage preview
    excerpt = generate_excerpt(content, max_length=200)

    # Insert post
    db = get_db()

    # Get CalRiven's user ID
    calriven = db.execute('SELECT id FROM users WHERE username = ?', ('calriven',)).fetchone()

    if not calriven:
        print("❌ CalRiven user not found")
        db.close()
        return None

    cursor = db.execute('''
        INSERT INTO posts (user_id, title, slug, content, excerpt, published_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        calriven['id'],
        title,
        slug,
        content,
        excerpt,
        datetime.now().isoformat()
    ))
    
    post_id = cursor.lastrowid

    # Mark feedback as processed and link to post (prevents duplicates)
    db.execute('''
        UPDATE feedback
        SET status = 'in-progress',
            admin_notes = ?,
            post_id = ?
        WHERE id = ?
    ''', (f'Auto-created post #{post_id}', post_id, feedback_item['feedback_id']))

    # Get feedback reporter email (before closing connection)
    feedback_email = db.execute('SELECT email FROM feedback WHERE id = ?',
                                 (feedback_item['feedback_id'],)).fetchone()

    db.commit()
    db.close()

    # Award bits for post creation
    award_bits(
        user_id=calriven['id'],
        amount=20,
        reason=f'Created build-in-public post from feedback',
        contribution_type='post',
        post_id=post_id
    )

    # Award bits to feedback reporter (if they have an account)
    if feedback_email and feedback_email['email']:
        db2 = get_db()
        reporter = db2.execute('SELECT id FROM users WHERE email = ?',
                              (feedback_email['email'],)).fetchone()
        db2.close()

        if reporter:
            award_bits(
                user_id=reporter['id'],
                amount=10,
                reason=f'Feedback resulted in post #{post_id}',
                contribution_type='feedback',
                post_id=post_id
            )

    return post_id


def trigger_reasoning_on_post(post_id):
    """
    Trigger reasoning engine to analyze the post
    
    This makes TheAuditor, Soulfra, etc. weigh in automatically
    
    Args:
        post_id: Post to analyze
    
    Returns:
        int: Reasoning thread ID
    """
    db = get_db()
    post = db.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    db.close()
    
    if not post:
        return None
    
    # Analyze post
    engine = ReasoningEngine()
    analysis = engine.analyze_post(dict(post))
    
    # Generate responses from all personas
    responses = {}
    for persona in ['calriven', 'theauditor', 'soulfra', 'deathtodata']:
        response = engine.generate_response(dict(post), analysis, persona=persona)
        responses[persona] = response
    
    # Store in database
    db = get_db()
    
    # Create reasoning thread
    cursor = db.execute('''
        INSERT INTO reasoning_threads (post_id, initiator_user_id, topic, status)
        VALUES (?, ?, ?, ?)
    ''', (post_id, post['user_id'], f"Analysis of: {post['title']}", 'completed'))
    
    thread_id = cursor.lastrowid
    
    # Store reasoning steps
    step_number = 1
    for persona, response in responses.items():
        user = db.execute('SELECT id FROM users WHERE username = ?', (persona,)).fetchone()
        if user:
            db.execute('''
                INSERT INTO reasoning_steps 
                (thread_id, user_id, step_number, step_type, content, confidence)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (thread_id, user['id'], step_number, 'analysis', response, 0.9))
            step_number += 1
    
    # Mark post as AI processed
    db.execute('UPDATE posts SET ai_processed = ? WHERE id = ?', (True, post_id))
    
    db.commit()
    db.close()
    
    return thread_id


def run_public_builder():
    """Main automation loop"""
    print("=" * 70)
    print("🏗️  PUBLIC BUILDER - Build in Public Automation")
    print("=" * 70)
    print()

    # Step 1: Check feedback
    print("STEP 1: Checking feedback for build opportunities...")
    priority_feedback = check_feedback_for_building()

    if not priority_feedback:
        print("   ℹ️  No high-priority feedback to build from")
        return {
            'posts_created': 0,
            'feedback_processed': 0,
            'reasoning_threads': 0
        }

    print(f"   ✅ Found {len(priority_feedback)} priority items:")
    for item in priority_feedback[:5]:  # Show top 5
        print(f"      • [{item['component']}] {item['message'][:60]}... (score: {item['score']})")
    print()

    # Step 2: Create posts from top feedback
    print("STEP 2: Creating posts from feedback (CalRiven)...")
    posts_created = []

    for item in priority_feedback[:3]:  # Build top 3
        post_id = create_post_from_feedback(item)
        if post_id:
            posts_created.append(post_id)
            print(f"   ✅ Created post #{post_id}: {item['component']}")

    print()

    # Step 3: Trigger reasoning on each post
    print("STEP 3: Triggering reasoning engine...")
    for post_id in posts_created:
        thread_id = trigger_reasoning_on_post(post_id)
        print(f"   ✅ Reasoning thread #{thread_id} for post #{post_id}")

    print()

    # Step 4: Summary
    print("=" * 70)
    print("✅ PUBLIC BUILDER COMPLETE")
    print("=" * 70)
    print()
    print(f"📊 Summary:")
    print(f"   • {len(priority_feedback)} priority feedback items found")
    print(f"   • {len(posts_created)} posts created by CalRiven")
    print(f"   • {len(posts_created)} reasoning threads started")
    print()
    print("🌐 View posts at: http://localhost:5001/")
    print()

    return {
        'posts_created': len(posts_created),
        'feedback_processed': len(priority_feedback),
        'reasoning_threads': len(posts_created)
    }


if __name__ == '__main__':
    run_public_builder()
