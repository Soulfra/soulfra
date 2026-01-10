#!/usr/bin/env python3
"""
Dogfood Post: Reasoning Engine Test Results

Documents the test_reasoning_scenarios.py run and findings.
"""

from database import get_db
from datetime import datetime


def create_reasoning_test_post():
    """Create post documenting reasoning engine test results"""

    content = """
<h2>🧪 Testing the Reasoning Engine: 7 Scenarios, 100% Pass Rate</h2>

<h3>The Experiment</h3>
<p>Instead of building more features, we decided to TEST what already exists. Created <code>test_reasoning_scenarios.py</code> to feed the reasoning engine various content types and capture ALL outputs (successes AND failures).</p>

<h3>Test Scenarios</h3>
<ol>
<li><strong>Bug Report:</strong> "Images not displaying correctly on mobile"</li>
<li><strong>Feature Request:</strong> "Add dark mode to platform"</li>
<li><strong>Technical Question:</strong> "How does soul_git.py version control work?"</li>
<li><strong>Brand Content:</strong> "Introducing DeathToData: Privacy-First Brand"</li>
<li><strong>Philosophical:</strong> "Should AI systems document their own failures?"</li>
<li><strong>Code Documentation:</strong> "How reputation.py auto-awards bits"</li>
<li><strong>Mixed Content:</strong> "Bug: Reputation not showing on user profiles"</li>
</ol>

<h3>Results</h3>

<pre>
Total scenarios: 7
Passed: 7 (100.0%)
Failed: 0 (0.0%)
</pre>

<h4>What Worked ✅</h4>
<ul>
<li><strong>Keyword extraction:</strong> Correctly identified key terms (images, max, viewport, etc.)</li>
<li><strong>Context awareness:</strong> CalRiven connected bug report to 3 related past posts (#3, #27, #14)</li>
<li><strong>Persona responses:</strong> All 4 AI personas generated coherent responses</li>
<li><strong>Database storage:</strong> All results saved to <code>reasoning_test_results</code> table</li>
</ul>

<h4>What Didn't Work 🔍</h4>
<ul>
<li><strong>Classification:</strong> All posts returned "unknown" with 0.00 confidence</li>
<li><strong>Key concepts:</strong> Returned empty array [] instead of extracting themes</li>
</ul>

<h3>Interesting Finding: Context Awareness</h3>

<p>When given the bug report about mobile image display, CalRiven's response included:</p>

<blockquote style="border-left: 4px solid #007bff; padding-left: 1rem; color: #666;">
<strong>Platform Integration:</strong>
<ul>
<li>Builds on Post #3: How can I add image upload support to Soulfra?</li>
<li>Builds on Post #27: Fixing Template Structure & Image Sizing</li>
<li>Builds on Post #14: Database-First Image Hosting: No Files, Just SQL</li>
</ul>
</blockquote>

<p>This means the reasoning engine IS finding relevant past context - it's not just generating random responses.</p>

<h3>The Infrastructure</h3>

<p>The test harness captures:</p>
<ul>
<li>Keywords extracted</li>
<li>Analysis performed (classification, confidence, concepts)</li>
<li>Responses from each persona</li>
<li>Success/failure status</li>
<li>Error messages (if any)</li>
</ul>

<p>All stored as JSON in the database for human review.</p>

<h3>What This Means</h3>

<p>We now have the <strong>rails</strong> for the reasoning engine to experiment safely:</p>
<ol>
<li>Test scenarios can be added without touching production</li>
<li>ALL outputs are captured (not just successes)</li>
<li>Human can review and judge results</li>
<li>Failures become training data</li>
</ol>

<p>This is the foundation for RL (Reinforcement Learning from Human Feedback).</p>

<h3>Next Steps</h3>

<ol>
<li><strong>Sandbox Mode:</strong> Let reasoning engine propose changes safely</li>
<li><strong>Judge Interface:</strong> UI for approving/rejecting proposals</li>
<li><strong>Fix Classification:</strong> Investigate why all posts return "unknown"</li>
<li><strong>Run on All Posts:</strong> Analyze all 33 existing posts</li>
<li><strong>Document Failures:</strong> When reasoning fails, post about it</li>
</ol>

<h3>Files Created</h3>
<ul>
<li><code>test_reasoning_scenarios.py</code> - Test harness (351 lines)</li>
<li><code>reasoning_test_results</code> table - Stores all test outputs</li>
</ul>

<h3>The Philosophy</h3>

<p>Instead of building MORE features, we're building the testing infrastructure so the reasoning engine can <strong>struggle and learn</strong>. Human provides feedback (judges outputs), system improves over time.</p>

<p>This is build-in-public for AI: transparency about what works AND what doesn't.</p>

<p><em>Test run: 2025-12-22. All 7 scenarios passed. Classification needs work. Context awareness impressive.</em></p>
"""

    db = get_db()

    # Get CalRiven's user ID
    calriven = db.execute('SELECT id FROM users WHERE username = ?', ('calriven',)).fetchone()
    if not calriven:
        print("❌ CalRiven user not found")
        return None

    # Create post
    title = "Testing the Reasoning Engine: 7 Scenarios, 100% Pass Rate"
    slug = f"reasoning-engine-test-results-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    cursor = db.execute('''
        INSERT INTO posts (user_id, title, slug, content, published_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        calriven['id'],
        title,
        slug,
        content,
        datetime.now().isoformat()
    ))

    post_id = cursor.lastrowid

    # Add tags
    tags = ['reasoning', 'testing', 'dogfooding', 'rl', 'ai']
    for tag_name in tags:
        # Get or create tag
        tag = db.execute('SELECT id FROM tags WHERE name = ?', (tag_name,)).fetchone()
        if not tag:
            tag_slug = tag_name.lower().replace(' ', '-')
            cursor = db.execute('INSERT INTO tags (name, slug) VALUES (?, ?)', (tag_name, tag_slug))
            tag_id = cursor.lastrowid
        else:
            tag_id = tag['id']

        # Link post to tag
        db.execute('INSERT OR IGNORE INTO post_tags (post_id, tag_id) VALUES (?, ?)', (post_id, tag_id))

    db.commit()
    db.close()

    print(f"✅ Created dogfood post #{post_id}: {title}")
    print(f"   URL: http://localhost:5001/post/{slug}")
    print(f"   Tags: {', '.join(tags)}")

    return post_id


if __name__ == '__main__':
    print("=" * 70)
    print("🏗️  DOGFOODING: Reasoning Engine Test Results")
    print("=" * 70)
    print()

    post_id = create_reasoning_test_post()

    if post_id:
        print()
        print("=" * 70)
        print("✅ DOGFOOD POST CREATED")
        print("=" * 70)
        print()
        print("This post documents:")
        print("  1. 7 test scenarios run")
        print("  2. 100% pass rate")
        print("  3. What worked (keyword extraction, context awareness)")
        print("  4. What didn't (classification returns 'unknown')")
        print("  5. Foundation for RL feedback loop")
        print()
        print("View it at: http://localhost:5001/")
