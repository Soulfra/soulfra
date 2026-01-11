#!/usr/bin/env python3
"""
Test Reasoning Engine with Various Scenarios

Feeds the reasoning engine different types of content and captures ALL outputs
(successes and failures). This is the testing infrastructure for RL.

Scenario types:
- Bug reports
- Feature requests
- Technical questions
- Brand content
- Philosophical posts
"""

import json
from datetime import datetime
from database import get_db
from reasoning_engine import ReasoningEngine


# Test scenarios (various post types)
TEST_SCENARIOS = [
    {
        'id': 'bug_report_1',
        'type': 'bug_report',
        'title': 'Images not displaying correctly on mobile',
        'content': '''
        <p>When viewing posts on mobile devices, images are cut off at weird aspect ratios.
        The max-width CSS is working but max-height seems to be ignored.</p>

        <p>Steps to reproduce:</p>
        <ol>
        <li>Open any post with images on iPhone</li>
        <li>Scroll to image</li>
        <li>Image extends beyond viewport</li>
        </ol>

        <p>Expected: Images should fit within viewport</p>
        <p>Actual: Images overflow and break layout</p>
        '''
    },
    {
        'id': 'feature_request_1',
        'type': 'feature_request',
        'title': 'Add dark mode to platform',
        'content': '''
        <p>It would be great to have a dark mode option for reading at night.</p>

        <p>Proposed solution:</p>
        <ul>
        <li>Toggle in header nav</li>
        <li>Store preference in localStorage</li>
        <li>Use CSS custom properties for theming</li>
        </ul>

        <p>Benefits: Better UX, reduced eye strain, modern aesthetic</p>
        '''
    },
    {
        'id': 'technical_question_1',
        'type': 'technical_question',
        'title': 'How does soul_git.py version control work?',
        'content': '''
        <p>I noticed there's a soul_git.py file that implements version control.</p>

        <p>Questions:</p>
        <ul>
        <li>How does it differ from regular Git?</li>
        <li>What gets versioned (code, souls, posts)?</li>
        <li>Is there a UI for viewing commit history?</li>
        <li>Can I roll back to previous versions?</li>
        </ul>

        <p>Seems like an interesting approach to versioning user identity data.</p>
        '''
    },
    {
        'id': 'brand_content_1',
        'type': 'brand_content',
        'title': 'Introducing DeathToData: Privacy-First Brand',
        'content': '''
        <h2>DeathToData Brand Philosophy</h2>

        <p>DeathToData represents our commitment to radical privacy. No tracking, no surveillance,
        no data collection beyond what's absolutely necessary.</p>

        <h3>Core Values</h3>
        <ul>
        <li>Privacy by default</li>
        <li>Local-first architecture</li>
        <li>Encryption everywhere</li>
        <li>You own your data</li>
        </ul>

        <p>This brand is for people who believe data collection has gone too far.</p>
        '''
    },
    {
        'id': 'philosophical_1',
        'type': 'philosophical',
        'title': 'Should AI systems document their own failures?',
        'content': '''
        <p>Most AI systems only show you their successes. But what if failures were just as valuable?</p>

        <p>Consider: A reasoning engine that documents when it misclassifies content, extracts wrong
        keywords, or makes poor recommendations. These failures become training data.</p>

        <p>This is the essence of build-in-public for AI: transparency about what works AND what doesn't.</p>

        <p>Thoughts?</p>
        '''
    },
    {
        'id': 'code_documentation_1',
        'type': 'code_documentation',
        'title': 'How reputation.py auto-awards bits',
        'content': '''
        <h2>Perfect Bits Auto-Award System</h2>

        <pre><code>
def award_bits(user_id, amount, reason, contribution_type='other'):
    conn = get_db()
    conn.execute(
        'UPDATE reputation SET bits_earned = bits_earned + ? WHERE user_id = ?',
        (amount, user_id)
    )
    conn.execute(
        'INSERT INTO contribution_logs (user_id, bits_awarded, description) VALUES (?, ?, ?)',
        (user_id, amount, reason)
    )
    conn.commit()
</code></pre>

        <p>This function automatically awards bits when users contribute.
        No manual approval needed - trust the automation.</p>
        '''
    },
    {
        'id': 'mixed_content_1',
        'type': 'mixed_content',
        'title': 'Bug: Reputation not showing on user profiles',
        'content': '''
        <p>CalRiven has 80 bits but /user/calriven doesn't display reputation.</p>

        <p>Technical details:</p>
        <ul>
        <li>Database: reputation table exists, data is correct</li>
        <li>app.py: user_profile() route doesn't fetch reputation</li>
        <li>templates/user.html: no reputation display section</li>
        </ul>

        <p>This is similar to GitHub showing contribution stats on profiles. We should do the same.</p>

        <h3>Proposed fix:</h3>
        <pre><code>
# In app.py user_profile route:
reputation = get_user_reputation(user['id'])

# Pass to template:
return render_template('user.html', user=user, posts=posts, reputation=reputation)
</code></pre>
        '''
    }
]


def run_scenario_test(scenario, engine):
    """
    Run reasoning engine on a single scenario

    Returns dict with:
    - scenario_id
    - keywords extracted
    - analysis generated
    - response generated (from each persona)
    - success/failure status
    - error messages (if any)
    """
    print(f"\n{'='*70}")
    print(f"SCENARIO: {scenario['id']} ({scenario['type']})")
    print(f"TITLE: {scenario['title']}")
    print(f"{'='*70}\n")

    result = {
        'scenario_id': scenario['id'],
        'scenario_type': scenario['type'],
        'title': scenario['title'],
        'timestamp': datetime.now().isoformat(),
        'success': True,
        'errors': [],
        'keywords': [],
        'analysis': {},
        'responses': {}
    }

    # Create fake post dict for reasoning engine
    fake_post = {
        'id': 999 + hash(scenario['id']) % 1000,  # Fake ID
        'title': scenario['title'],
        'content': scenario['content'],
        'user_id': 1,  # CalRiven
        'published_at': datetime.now().isoformat()
    }

    try:
        # Step 1: Extract keywords
        print("STEP 1: Extracting keywords...")
        keywords = engine.extract_keywords(scenario['content'], top_n=10)
        result['keywords'] = keywords
        print(f"   Keywords: {[k[0] for k in keywords[:5]]}")

        # Step 2: Analyze post
        print("\nSTEP 2: Analyzing content...")
        analysis = engine.analyze_post(fake_post)
        result['analysis'] = analysis
        print(f"   Classification: {analysis.get('classification', 'unknown')}")
        print(f"   Confidence: {analysis.get('confidence', 0):.2f}")
        print(f"   Key concepts: {analysis.get('key_concepts', [])[:3]}")

        # Step 3: Generate responses from each persona
        print("\nSTEP 3: Generating persona responses...")
        for persona in ['calriven', 'theauditor', 'soulfra', 'deathtodata']:
            try:
                response = engine.generate_response(fake_post, analysis, persona=persona)
                result['responses'][persona] = response
                print(f"   {persona}: {response[:80]}...")
            except Exception as e:
                result['errors'].append(f"{persona} response failed: {str(e)}")
                result['success'] = False
                print(f"   ❌ {persona}: ERROR - {str(e)}")

        if result['success']:
            print(f"\n✅ Scenario {scenario['id']} PASSED")
        else:
            print(f"\n⚠️  Scenario {scenario['id']} PARTIALLY FAILED (see errors)")

    except Exception as e:
        result['success'] = False
        result['errors'].append(f"Fatal error: {str(e)}")
        print(f"\n❌ Scenario {scenario['id']} FAILED: {str(e)}")

    return result


def save_test_results(results):
    """Save test results to database for human review"""
    db = get_db()

    for result in results:
        db.execute('''
            INSERT INTO reasoning_test_results (
                scenario_id, scenario_type, title, timestamp,
                success, keywords, analysis, responses, errors
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            result['scenario_id'],
            result['scenario_type'],
            result['title'],
            result['timestamp'],
            result['success'],
            json.dumps(result['keywords']),
            json.dumps(result['analysis']),
            json.dumps(result['responses']),
            json.dumps(result['errors'])
        ))

    db.commit()
    db.close()
    print(f"\n💾 Saved {len(results)} test results to database")


def create_test_results_table():
    """Create table for storing test results"""
    db = get_db()

    db.execute('''
        CREATE TABLE IF NOT EXISTS reasoning_test_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scenario_id TEXT NOT NULL,
            scenario_type TEXT NOT NULL,
            title TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            success BOOLEAN NOT NULL,
            keywords TEXT,
            analysis TEXT,
            responses TEXT,
            errors TEXT
        )
    ''')

    db.commit()
    db.close()
    print("✅ Created reasoning_test_results table")


def print_summary(results):
    """Print test summary"""
    print(f"\n{'='*70}")
    print("TEST SUMMARY")
    print(f"{'='*70}\n")

    total = len(results)
    passed = sum(1 for r in results if r['success'])
    failed = total - passed

    print(f"Total scenarios: {total}")
    print(f"Passed: {passed} ({passed/total*100:.1f}%)")
    print(f"Failed: {failed} ({failed/total*100:.1f}%)")

    if failed > 0:
        print(f"\nFailed scenarios:")
        for r in results:
            if not r['success']:
                print(f"  - {r['scenario_id']}: {r['errors'][0] if r['errors'] else 'Unknown error'}")

    print(f"\n{'='*70}")


def main():
    print("=" * 70)
    print("REASONING ENGINE TEST SCENARIOS")
    print("=" * 70)
    print(f"\nTesting {len(TEST_SCENARIOS)} scenarios...")
    print("This will capture ALL outputs (successes AND failures)\n")

    # Create table if doesn't exist
    create_test_results_table()

    # Initialize reasoning engine
    engine = ReasoningEngine()

    # Run all scenarios
    results = []
    for scenario in TEST_SCENARIOS:
        result = run_scenario_test(scenario, engine)
        results.append(result)

    # Save results
    save_test_results(results)

    # Print summary
    print_summary(results)

    print("\n💡 View results at: http://localhost:5001/sandbox (coming soon)")
    print("💡 Results saved to: reasoning_test_results table\n")


if __name__ == '__main__':
    main()
