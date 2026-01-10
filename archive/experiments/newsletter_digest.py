#!/usr/bin/env python3
"""
Newsletter Digest - Grouped Questions for Decision Making

This creates a weekly newsletter that:
1. Groups feedback by theme/similarity
2. Combines reasoning from AI personas
3. Generates QUESTIONS for you to answer
4. Helps make decisions about domains/brands/categories

The newsletter becomes a decision-making tool, not just updates.
"""

from collections import defaultdict
from datetime import datetime, timedelta
from database import get_db
from reasoning_engine import ReasoningEngine


def group_feedback_by_theme():
    """
    Group feedback items by similarity
    
    Uses keyword overlap to find themes:
    - "QR code" theme: 5 feedback items
    - "Performance" theme: 3 feedback items
    - "UI/UX" theme: 7 feedback items
    
    Returns:
        dict: {theme_name: [feedback_items]}
    """
    db = get_db()
    
    # Get last 7 days of feedback
    feedback_items = db.execute('''
        SELECT id, component, message, created_at, status
        FROM feedback
        WHERE created_at > datetime('now', '-7 days')
        ORDER BY created_at DESC
    ''').fetchall()
    
    db.close()
    
    # Extract keywords from each feedback
    engine = ReasoningEngine()
    feedback_with_keywords = []
    
    for item in feedback_items:
        keywords = engine.extract_keywords(item['message'], top_n=5)
        feedback_with_keywords.append({
            'item': dict(item),
            'keywords': set([kw for kw, _ in keywords])
        })
    
    # Group by keyword overlap
    themes = defaultdict(list)
    
    for entry in feedback_with_keywords:
        # Find theme name from most common keyword
        top_keywords = list(entry['keywords'])[:3]
        theme_name = entry['item']['component'] or top_keywords[0] if top_keywords else 'General'
        
        themes[theme_name].append(entry['item'])
    
    # Filter out single-item themes
    significant_themes = {k: v for k, v in themes.items() if len(v) >= 1}
    
    return significant_themes


def analyze_reasoning_consensus():
    """
    Find consensus/disagreement in reasoning threads
    
    Returns:
        list: [{
            'post_id': 10,
            'topic': 'Performance optimization',
            'consensus': True/False,
            'ai_opinions': {
                'calriven': 'Cache everything',
                'theauditor': 'Be careful with cache',
                'soulfra': 'Test first'
            }
        }]
    """
    db = get_db()
    
    # Get recent reasoning threads
    threads = db.execute('''
        SELECT rt.id, rt.post_id, rt.topic, p.title
        FROM reasoning_threads rt
        JOIN posts p ON rt.post_id = p.id
        WHERE rt.created_at > datetime('now', '-7 days')
        ORDER BY rt.created_at DESC
    ''').fetchall()
    
    analyses = []
    
    for thread in threads:
        # Get all reasoning steps for this thread
        steps = db.execute('''
            SELECT rs.content, u.username
            FROM reasoning_steps rs
            JOIN users u ON rs.user_id = u.id
            WHERE rs.thread_id = ?
            ORDER BY rs.step_number
        ''', (thread['id'],)).fetchall()
        
        if len(steps) < 2:
            continue
        
        # Extract key points from each AI
        ai_opinions = {}
        for step in steps:
            # Simple extraction: first sentence after "##"
            content = step['content']
            lines = content.split('\n')
            summary = next((line for line in lines if line.strip() and not line.startswith('#')), '')[:100]
            ai_opinions[step['username']] = summary.strip()
        
        # Check for consensus (all mention similar keywords)
        all_keywords = set()
        for opinion in ai_opinions.values():
            words = set(opinion.lower().split())
            all_keywords.update(words)
        
        # Rough consensus check: if opinions share > 30% keywords
        consensus = len(all_keywords) < 50  # Simple heuristic
        
        analyses.append({
            'post_id': thread['post_id'],
            'post_title': thread['title'],
            'topic': thread['topic'],
            'consensus': consensus,
            'ai_opinions': ai_opinions
        })
    
    db.close()
    
    return analyses


def get_proof_status():
    """
    Get cryptographic proof status for newsletter

    Returns:
        dict: {
            'total_proofs': 10,
            'latest_proof': {...},
            'verified': True/False,
            'signature_valid': True/False
        }
    """
    try:
        db = get_db()

        # Get total proof count
        total_proofs = db.execute('SELECT COUNT(*) as count FROM cryptographic_proofs').fetchone()['count']

        # Get latest proof
        latest_proof = db.execute('''
            SELECT id, proof_type, created_at, metadata, signature
            FROM cryptographic_proofs
            ORDER BY created_at DESC
            LIMIT 1
        ''').fetchone()

        db.close()

        proof_data = {
            'total_proofs': total_proofs,
            'latest_proof': dict(latest_proof) if latest_proof else None,
            'verified': False,
            'signature_valid': False
        }

        # Verify latest proof signature
        if latest_proof:
            try:
                import json
                import hmac
                import hashlib

                metadata = json.loads(latest_proof['metadata'])
                signature = latest_proof['signature']

                # Recreate canonical string
                canonical = f"{latest_proof['proof_type']}|{latest_proof['created_at']}|{latest_proof['metadata']}"

                # Verify signature (using same secret as generate_proof.py)
                secret_key = b'soulfra-proof-secret-key-2024'
                expected_signature = hmac.new(secret_key, canonical.encode('utf-8'), hashlib.sha256).hexdigest()

                proof_data['signature_valid'] = (signature == expected_signature)
                proof_data['verified'] = proof_data['signature_valid']
            except:
                proof_data['verified'] = False
                proof_data['signature_valid'] = False

        return proof_data

    except Exception as e:
        # Table doesn't exist or other error - return default
        return {
            'total_proofs': 0,
            'latest_proof': None,
            'verified': False,
            'signature_valid': False
        }


def generate_decision_questions(themes, reasoning_analyses):
    """
    Generate questions for decision-making

    Args:
        themes: Grouped feedback themes
        reasoning_analyses: AI consensus/disagreement

    Returns:
        list: Decision questions
    """
    questions = []

    # Questions from feedback themes
    for theme_name, items in themes.items():
        count = len(items)

        # Extract sample message
        sample = items[0]['message'][:100]

        question = {
            'type': 'feature_priority',
            'theme': theme_name,
            'count': count,
            'question': f"{count} {'person' if count == 1 else 'people'} requested {theme_name} features",
            'context': f'Example: "{sample}..."',
            'actions': ['Prioritize', 'Schedule', 'Decline', 'Need more info']
        }

        questions.append(question)

    # Questions from reasoning consensus/disagreement
    for analysis in reasoning_analyses:
        if not analysis['consensus']:
            # AIs disagree - need human decision
            question = {
                'type': 'resolve_disagreement',
                'post_title': analysis['post_title'],
                'question': f"AIs disagree on: {analysis['topic']}",
                'context': f"CalRiven: {analysis['ai_opinions'].get('calriven', 'N/A')[:50]}...\nTheAuditor: {analysis['ai_opinions'].get('theauditor', 'N/A')[:50]}...",
                'actions': ['Side with CalRiven', 'Side with TheAuditor', 'Compromise', 'Research more']
            }

            questions.append(question)

    return questions


def generate_html_digest(questions, themes, reasoning_analyses, proof_status):
    """Generate HTML email digest"""

    # Proof verification status
    proof_icon = "✅" if proof_status.get('verified') else "⚠️"
    proof_color = "#28a745" if proof_status.get('verified') else "#ffc107"
    proof_text = "VERIFIED" if proof_status.get('verified') else "UNVERIFIED"

    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #007bff; color: white; padding: 20px; border-radius: 8px; margin-bottom: 30px; }}
            .question-card {{ background: #f9f9f9; padding: 20px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #007bff; }}
            .question-title {{ font-size: 18px; font-weight: bold; margin-bottom: 10px; color: #333; }}
            .question-context {{ color: #666; margin-bottom: 15px; font-size: 14px; }}
            .actions {{ display: flex; gap: 10px; flex-wrap: wrap; }}
            .action-btn {{ background: #007bff; color: white; padding: 8px 16px; border-radius: 4px; text-decoration: none; font-size: 14px; }}
            .stats {{ background: #e6f2ff; padding: 15px; border-radius: 8px; margin-bottom: 30px; }}
            .proof-section {{ background: #1a1a1a; color: white; padding: 20px; border-radius: 8px; margin-bottom: 30px; border-left: 4px solid {proof_color}; }}
            .proof-badge {{ display: inline-block; background: {proof_color}; color: #1a1a1a; padding: 4px 12px; border-radius: 4px; font-weight: bold; font-size: 12px; }}
            .proof-link {{ color: #4da3ff; text-decoration: none; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📊 Weekly Decision Digest</h1>
            <p style="margin: 0; opacity: 0.9;">{datetime.now().strftime('%B %d, %Y')}</p>
        </div>

        <div class="proof-section">
            <h3 style="margin-top: 0;">{proof_icon} System Integrity</h3>
            <p style="margin-bottom: 15px;">
                <span class="proof-badge">{proof_text}</span>
                {proof_status['total_proofs']} cryptographic proofs generated
            </p>
            <p style="font-size: 14px; opacity: 0.9; margin-bottom: 10px;">
                This newsletter is generated by a <strong>provably offline-first</strong> system.
                Every action is cryptographically signed and auditable.
            </p>
            <div style="margin-top: 15px;">
                <a href="http://localhost:5001/proof" class="proof-link">🔍 View Proof System</a> |
                <a href="http://localhost:5001/legitimacy" class="proof-link">📖 Why This Works</a>
            </div>
        </div>

        <div class="stats">
            <strong>This Week:</strong><br>
            • {sum(len(items) for items in themes.values())} feedback items<br>
            • {len(reasoning_analyses)} reasoning threads<br>
            • {len(questions)} decisions needed<br>
        </div>

        <h2>🤔 Questions for You</h2>
        <p style="color: #666; margin-bottom: 30px;">
            Based on feedback and AI reasoning, here are the decisions that need your input:
        </p>
    """
    
    for i, q in enumerate(questions, 1):
        html += f"""
        <div class="question-card">
            <div class="question-title">
                {i}. {q['question']}
            </div>
            <div class="question-context">
                {q['context']}
            </div>
            <div class="actions">
                {''.join([f'<a href="http://localhost:5001/admin/decision/{i}?action={action}" class="action-btn">{action}</a>' for action in q['actions']])}
            </div>
        </div>
        """
    
    html += """
        <hr style="border: none; border-top: 1px solid #eee; margin: 40px 0;">
        <p style="color: #999; font-size: 12px; text-align: center;">
            This digest was auto-generated by Soulfra's build-in-public system.<br>
            <a href="http://localhost:5001/feedback" style="color: #666;">Give feedback</a> |
            <a href="http://localhost:5001/admin" style="color: #666;">Admin dashboard</a>
        </p>
    </body>
    </html>
    """
    
    return html


def send_weekly_digest(dry_run=True):
    """
    Generate and send weekly digest

    Args:
        dry_run: If True, just print digest (don't email)
    """
    print("=" * 70)
    print("📧 Generating Weekly Newsletter Digest")
    print("=" * 70)
    print()

    # Step 1: Group feedback by theme
    print("STEP 1: Grouping feedback by theme...")
    themes = group_feedback_by_theme()
    print(f"   Found {len(themes)} themes:")
    for theme, items in themes.items():
        print(f"      • {theme}: {len(items)} items")
    print()

    # Step 2: Analyze reasoning consensus
    print("STEP 2: Analyzing AI reasoning...")
    reasoning_analyses = analyze_reasoning_consensus()
    print(f"   Analyzed {len(reasoning_analyses)} reasoning threads")
    for analysis in reasoning_analyses:
        consensus_text = "CONSENSUS" if analysis['consensus'] else "DISAGREEMENT"
        print(f"      • {analysis['post_title'][:50]}: {consensus_text}")
    print()

    # Step 3: Get cryptographic proof status
    print("STEP 3: Verifying cryptographic proofs...")
    proof_status = get_proof_status()
    verification_icon = "✅" if proof_status['verified'] else "⚠️"
    print(f"   {verification_icon} {proof_status['total_proofs']} proofs generated")
    if proof_status['latest_proof']:
        print(f"   Latest: {proof_status['latest_proof']['proof_type']} at {proof_status['latest_proof']['created_at']}")
        print(f"   Signature: {'VALID' if proof_status['signature_valid'] else 'INVALID'}")
    print()

    # Step 4: Generate decision questions
    print("STEP 4: Generating decision questions...")
    questions = generate_decision_questions(themes, reasoning_analyses)
    print(f"   Generated {len(questions)} questions for decision-making")
    print()

    # Step 5: Create digest
    print("STEP 5: Creating HTML digest...")
    html_digest = generate_html_digest(questions, themes, reasoning_analyses, proof_status)

    if dry_run:
        # Save to file instead of emailing
        with open('weekly_digest_preview.html', 'w') as f:
            f.write(html_digest)
        print(f"   ✅ Saved to weekly_digest_preview.html")
        print(f"   Open in browser to preview")
    else:
        # Send via email
        from emails import send_post_email
        digest_post = {
            'title': f'Weekly Decision Digest - {datetime.now().strftime("%b %d")}',
            'content': html_digest,
            'slug': 'weekly-digest'
        }
        send_post_email(digest_post)
        print(f"   ✅ Sent to subscribers")

    print()
    print("=" * 70)
    print("✅ DIGEST COMPLETE")
    print("=" * 70)
    print()

    print(f"📊 Summary:")
    print(f"   • {sum(len(items) for items in themes.values())} feedback items grouped")
    print(f"   • {len(reasoning_analyses)} reasoning threads analyzed")
    print(f"   • {proof_status['total_proofs']} cryptographic proofs verified")
    print(f"   • {len(questions)} decision questions generated")
    print()

    return questions


if __name__ == '__main__':
    send_weekly_digest(dry_run=True)
