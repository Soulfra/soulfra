#!/usr/bin/env python3
"""
Real AI Analysis using Reasoning Engine

Uses actual logic, keyword extraction, and similarity calculations.
No hardcoded responses - generates contextual analysis based on post content.
"""

from datetime import datetime
from db_helpers import (
    get_user_by_username,
    add_comment,
    create_reasoning_thread,
    add_reasoning_step
)
from database import get_db, mark_post_ai_processed, get_post_by_slug
from reasoning_engine import ReasoningEngine
import sys
import markdown2


def simulate_ai_analysis_on_post(post_id):
    """Run REAL AI analysis on a post"""

    # Get the post
    conn = get_db()
    post = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    conn.close()

    if not post:
        print(f"❌ Post {post_id} not found")
        return False

    post = dict(post)
    print(f"🧠 Running REAL AI analysis on: {post['title'][:60]}...")

    # Initialize reasoning engine
    engine = ReasoningEngine()

    # Analyze post content
    print("   📊 Extracting keywords, questions, code blocks...")
    analysis = engine.analyze_post(post)

    print(f"      Keywords: {[kw for kw, _ in analysis['keywords'][:5]]}")
    print(f"      Complexity: {analysis['complexity']}")
    print(f"      Related posts: {len(analysis['related_posts'])}")

    # Get AI personas
    calriven = get_user_by_username('calriven')
    theauditor = get_user_by_username('theauditor')

    if not all([calriven, theauditor]):
        print("❌ AI personas not found in database")
        return False

    # Create reasoning thread (initiated by CalRiven as primary analyst)
    print("   🧵 Creating reasoning thread...")
    thread_id = create_reasoning_thread(
        post_id=post['id'],
        initiator_user_id=calriven['id'],
        topic=post['title']
    )

    # CalRiven's perspective (REAL analysis from reasoning engine)
    print("   💻 Generating CalRiven's analysis...")
    calriven_take = engine.generate_response(post, analysis, persona='calriven')

    # Convert markdown to HTML for comment display
    comment_content_html = markdown2.markdown(
        calriven_take,
        extras=['fenced-code-blocks', 'tables', 'break-on-newline']
    )

    calriven_comment_id = add_comment(
        post_id=post['id'],
        user_id=calriven['id'],
        content=comment_content_html
    )

    add_reasoning_step(
        thread_id=thread_id,
        user_id=calriven['id'],
        step_number=1,
        step_type='analysis',
        content=calriven_take,
        confidence=0.85,
        comment_id=calriven_comment_id
    )

    # TheAuditor's validation (REAL analysis from reasoning engine)
    print("   🔍 Generating TheAuditor's validation...")
    auditor_take = engine.generate_response(post, analysis, persona='theauditor')

    # Convert markdown to HTML for comment display
    comment_content_html = markdown2.markdown(
        auditor_take,
        extras=['fenced-code-blocks', 'tables', 'break-on-newline']
    )

    auditor_comment_id = add_comment(
        post_id=post['id'],
        user_id=theauditor['id'],
        content=comment_content_html
    )

    add_reasoning_step(
        thread_id=thread_id,
        user_id=theauditor['id'],
        step_number=2,
        step_type='validation',
        content=auditor_take,
        confidence=0.90,
        comment_id=auditor_comment_id
    )

    # Mark post as processed
    mark_post_ai_processed(post['id'])

    print(f"   ✅ Analysis complete - 2 reasoning steps created")
    print(f"      CalRiven: {len(calriven_take)} chars")
    print(f"      TheAuditor: {len(auditor_take)} chars")
    return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python simulate_ai_analysis.py <post_id>")
        sys.exit(1)

    post_id = int(sys.argv[1])

    print("=" * 70)
    print("🧠 Real AI Analysis (Reasoning Engine)")
    print("=" * 70)
    print()

    success = simulate_ai_analysis_on_post(post_id)

    if success:
        print()
        print("=" * 70)
        print("✅ AI analysis complete!")
        print("=" * 70)
        print()
    else:
        print("\n❌ Analysis failed")
        sys.exit(1)


if __name__ == '__main__':
    main()
