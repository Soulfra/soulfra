#!/usr/bin/env python3
"""
Sandbox Routes - AI-powered domain management interface

Features:
- Drag-and-drop wordmap management
- Multi-domain comparison view
- Ollama/Claude AI integration for suggestions
- Diff viewer and rollback system
"""

from flask import Blueprint, render_template, request, jsonify
from database import get_db
from domain_diff_engine import (
    calculate_wordmap_diff,
    generate_ai_prompt_from_diff,
    merge_domains,
    create_diff_snapshot,
    rollback_to_snapshot,
    get_domain_wordmap,
    init_snapshots_table
)
import json

sandbox_bp = Blueprint('sandbox', __name__)


@sandbox_bp.route('/admin/sandbox')
def sandbox_dashboard():
    """
    Main sandbox editor interface

    Shows all domains with drag-and-drop wordmap editing
    """
    db = get_db()

    # Get all domains
    domains = db.execute('''
        SELECT domain, contributor_count, total_recordings, last_updated
        FROM domain_wordmaps
        ORDER BY domain
    ''').fetchall()

    domain_list = [dict(row) for row in domains]

    db.close()

    return render_template('admin/sandbox.html', domains=domain_list)


@sandbox_bp.route('/api/sandbox/domains')
def list_domains():
    """Get all domains with wordmap summaries"""
    db = get_db()

    domains = db.execute('''
        SELECT domain, wordmap_json, contributor_count, total_recordings, last_updated
        FROM domain_wordmaps
        ORDER BY domain
    ''').fetchall()

    result = []
    for domain in domains:
        wordmap = json.loads(domain['wordmap_json']) if domain['wordmap_json'] else {}
        top_words = sorted(wordmap.items(), key=lambda x: x[1], reverse=True)[:10]

        result.append({
            'domain': domain['domain'],
            'total_words': len(wordmap),
            'top_words': dict(top_words),
            'contributor_count': domain['contributor_count'],
            'total_recordings': domain['total_recordings'],
            'last_updated': domain['last_updated']
        })

    db.close()

    return jsonify({
        'success': True,
        'domains': result
    })


@sandbox_bp.route('/api/sandbox/domain/<domain>')
def get_domain_details(domain):
    """Get full wordmap for a specific domain"""
    wordmap = get_domain_wordmap(domain)

    return jsonify({
        'success': True,
        'domain': domain,
        'wordmap': wordmap,
        'total_words': len(wordmap)
    })


@sandbox_bp.route('/api/sandbox/compare', methods=['POST'])
def compare_domains():
    """
    Compare two domains and return diff analysis

    POST body:
    {
        "domain_a": "cringeproof.com",
        "domain_b": "soulfra.com"
    }
    """
    data = request.get_json()
    domain_a = data.get('domain_a')
    domain_b = data.get('domain_b')

    if not domain_a or not domain_b:
        return jsonify({'success': False, 'error': 'Missing domains'}), 400

    diff = calculate_wordmap_diff(domain_a, domain_b)

    return jsonify({
        'success': True,
        **diff
    })


@sandbox_bp.route('/api/sandbox/ai-prompt', methods=['POST'])
def generate_ai_prompt():
    """
    Generate AI prompt based on domain comparison

    POST body:
    {
        "domain_a": "cringeproof.com",
        "domain_b": "soulfra.com",
        "operation": "merge" | "contrast" | "suggest_vocabulary" | "extract_themes"
    }
    """
    data = request.get_json()
    domain_a = data.get('domain_a')
    domain_b = data.get('domain_b')
    operation = data.get('operation', 'merge')

    diff = calculate_wordmap_diff(domain_a, domain_b)
    prompt = generate_ai_prompt_from_diff(diff, operation)

    return jsonify({
        'success': True,
        'prompt': prompt,
        'operation': operation,
        'diff_summary': {
            'similarity': diff['similarity_score'],
            'shared_words': diff['shared_words'],
            'unique_to_a': len(diff['only_in_a']),
            'unique_to_b': len(diff['only_in_b'])
        }
    })


@sandbox_bp.route('/api/sandbox/merge', methods=['POST'])
def merge_wordmaps():
    """
    Transfer words from one domain to another

    POST body:
    {
        "source_domain": "cringeproof.com",
        "target_domain": "soulfra.com",
        "words": ["authentic", "cringe", "real"],
        "mode": "copy" | "move"
    }
    """
    data = request.get_json()
    source_domain = data.get('source_domain')
    target_domain = data.get('target_domain')
    words = data.get('words', [])
    mode = data.get('mode', 'copy')

    if not source_domain or not target_domain:
        return jsonify({'success': False, 'error': 'Missing domains'}), 400

    if not words:
        return jsonify({'success': False, 'error': 'No words specified'}), 400

    # Create snapshot before merge
    snapshot_id = create_diff_snapshot(target_domain, f"Before merge from {source_domain}")

    result = merge_domains(source_domain, target_domain, words, mode)

    return jsonify({
        'success': True,
        **result,
        'snapshot_id': snapshot_id
    })


@sandbox_bp.route('/api/sandbox/snapshot', methods=['POST'])
def create_snapshot():
    """
    Create a rollback point for a domain

    POST body:
    {
        "domain": "cringeproof.com",
        "description": "Before major changes"
    }
    """
    data = request.get_json()
    domain = data.get('domain')
    description = data.get('description', 'Manual snapshot')

    snapshot_id = create_diff_snapshot(domain, description)

    return jsonify({
        'success': True,
        'snapshot_id': snapshot_id,
        'domain': domain,
        'description': description
    })


@sandbox_bp.route('/api/sandbox/snapshots/<domain>')
def list_snapshots(domain):
    """Get all snapshots for a domain"""
    db = get_db()

    snapshots = db.execute('''
        SELECT id, description, created_at
        FROM domain_wordmap_snapshots
        WHERE domain = ?
        ORDER BY created_at DESC
        LIMIT 20
    ''', (domain,)).fetchall()

    db.close()

    return jsonify({
        'success': True,
        'domain': domain,
        'snapshots': [dict(row) for row in snapshots]
    })


@sandbox_bp.route('/api/sandbox/rollback', methods=['POST'])
def rollback():
    """
    Rollback a domain to a previous snapshot

    POST body:
    {
        "domain": "cringeproof.com",
        "snapshot_id": 42
    }
    """
    data = request.get_json()
    domain = data.get('domain')
    snapshot_id = data.get('snapshot_id')

    success = rollback_to_snapshot(domain, snapshot_id)

    if success:
        return jsonify({
            'success': True,
            'message': f'Rolled back {domain} to snapshot {snapshot_id}'
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Snapshot not found or rollback failed'
        }), 404


@sandbox_bp.route('/api/sandbox/add-words', methods=['POST'])
def add_words_to_domain():
    """
    Add new words to a domain's wordmap (AI-suggested words)

    POST body:
    {
        "domain": "soulfra.com",
        "words": {
            "integration": 5,
            "synergy": 3,
            "ecosystem": 4
        }
    }
    """
    data = request.get_json()
    domain = data.get('domain')
    new_words = data.get('words', {})

    if not domain or not new_words:
        return jsonify({'success': False, 'error': 'Missing domain or words'}), 400

    # Get current wordmap
    db = get_db()
    current = get_domain_wordmap(domain)

    # Merge new words
    for word, count in new_words.items():
        if word in current:
            current[word] += count
        else:
            current[word] = count

    # Save
    from datetime import datetime
    db.execute('''
        UPDATE domain_wordmaps
        SET wordmap_json = ?, last_updated = ?
        WHERE domain = ?
    ''', (json.dumps(current), datetime.now().isoformat(), domain))

    db.commit()
    db.close()

    return jsonify({
        'success': True,
        'domain': domain,
        'words_added': len(new_words),
        'total_words': len(current)
    })


def register_sandbox_routes(app):
    """Register sandbox routes and initialize database"""
    init_snapshots_table()
    app.register_blueprint(sandbox_bp)
    print("🎨 Sandbox routes registered:")
    print("   Dashboard: GET /admin/sandbox")
    print("   List Domains: GET /api/sandbox/domains")
    print("   Compare: POST /api/sandbox/compare")
    print("   Merge: POST /api/sandbox/merge")
    print("   Snapshots: GET /api/sandbox/snapshots/<domain>")
    print("   Rollback: POST /api/sandbox/rollback")
