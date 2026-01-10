"""
Blamechain API - Immutable Message Edit Tracking

Provides accountability system where users can edit messages,
but every edit is permanently recorded in a blockchain-like chain.

Use cases:
- Tribunal evidence (Kangaroo Court examines edit history)
- User accountability (can't hide what they originally said)
- 3-way AI argument tracking (CalRiven/Soulfra/DeathToData debate history)
"""

import hashlib
import sqlite3
from datetime import datetime
from flask import Blueprint, jsonify, request, session, g

blamechain_bp = Blueprint('blamechain', __name__)


def get_db():
    """Get database connection from Flask g object"""
    if 'db' not in g:
        g.db = sqlite3.connect('soulfra.db')
        g.db.row_factory = sqlite3.Row
    return g.db


def compute_content_hash(content):
    """Hash message content for integrity verification"""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def compute_chain_hash(previous_hash, content_hash, timestamp):
    """
    Compute immutable blamechain hash

    Links this edit to the chain:
    chain_hash = SHA256(previous_hash + content_hash + timestamp)
    """
    chain_input = f"{previous_hash or 'GENESIS'}{content_hash}{timestamp}"
    return hashlib.sha256(chain_input.encode('utf-8')).hexdigest()


@blamechain_bp.route('/api/blamechain/history/<message_table>/<int:message_id>')
def get_message_history(message_table, message_id):
    """
    Get full edit history for a message

    Returns all versions with hashes, editor info, and suspicion level

    GET /api/blamechain/history/messages/123
    """
    db = get_db()

    # Security: Only allow specific table names to prevent SQL injection
    allowed_tables = ['messages', 'irc_messages', 'dm_messages', 'qr_chat_transcripts']
    if message_table not in allowed_tables:
        return jsonify({'error': 'Invalid message table'}), 400

    try:
        history = db.execute('''
            SELECT * FROM v_message_blamechain
            WHERE message_table = ? AND message_id = ?
            ORDER BY version_number ASC
        ''', (message_table, message_id)).fetchall()

        if not history:
            return jsonify({'error': 'No history found'}), 404

        # Convert to dict
        history_data = []
        for row in history:
            history_data.append({
                'version': row['version_number'],
                'content': row['content'],
                'editor_id': row['edited_by_user_id'],
                'editor_username': row['editor_username'],
                'edit_reason': row['edit_reason'],
                'edited_at': row['edited_at'],
                'content_hash': row['content_hash'],
                'previous_hash': row['previous_hash'],
                'chain_hash': row['chain_hash'],
                'flagged_for_tribunal': bool(row['flagged_for_tribunal']),
                'tribunal_submission_id': row['tribunal_submission_id'],
                'suspicion_level': row['suspicion_level']
            })

        return jsonify({
            'success': True,
            'message_table': message_table,
            'message_id': message_id,
            'total_versions': len(history_data),
            'history': history_data
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@blamechain_bp.route('/api/blamechain/edit', methods=['POST'])
def edit_message():
    """
    Edit a message and record it in the blamechain

    POST /api/blamechain/edit
    {
        "message_table": "messages",
        "message_id": 123,
        "new_content": "Updated message text",
        "edit_reason": "Fixed typo" (optional)
    }

    Returns: Updated message with chain verification
    """
    db = get_db()
    data = request.get_json() or {}

    message_table = data.get('message_table')
    message_id = data.get('message_id')
    new_content = data.get('new_content')
    edit_reason = data.get('edit_reason')

    # Validation
    if not all([message_table, message_id, new_content]):
        return jsonify({'error': 'Missing required fields'}), 400

    allowed_tables = ['messages', 'irc_messages', 'dm_messages', 'qr_chat_transcripts']
    if message_table not in allowed_tables:
        return jsonify({'error': 'Invalid message table'}), 400

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        # Get latest version from history
        latest = db.execute('''
            SELECT version_number, chain_hash
            FROM message_history
            WHERE message_table = ? AND message_id = ?
            ORDER BY version_number DESC
            LIMIT 1
        ''', (message_table, message_id)).fetchone()

        if not latest:
            # No history exists - this is first edit after original message
            # Fetch original message and create v1 history first
            original = db.execute(f'SELECT content, from_user_id FROM {message_table} WHERE id = ?',
                                 (message_id,)).fetchone()

            if not original:
                return jsonify({'error': 'Message not found'}), 404

            # Create version 1 (original)
            original_content = original['content']
            original_hash = compute_content_hash(original_content)
            original_chain_hash = compute_chain_hash(None, original_hash, datetime.now().isoformat())

            db.execute('''
                INSERT INTO message_history
                (message_id, message_table, version_number, content,
                 edited_by_user_id, content_hash, previous_hash, chain_hash)
                VALUES (?, ?, 1, ?, ?, ?, NULL, ?)
            ''', (message_id, message_table, original_content,
                  original['from_user_id'], original_hash, original_chain_hash))

            # Now set latest for the edit
            latest = {
                'version_number': 1,
                'chain_hash': original_chain_hash
            }

        # Create new version
        new_version = latest['version_number'] + 1
        new_content_hash = compute_content_hash(new_content)
        timestamp = datetime.now().isoformat()
        new_chain_hash = compute_chain_hash(latest['chain_hash'], new_content_hash, timestamp)

        # Insert history entry
        db.execute('''
            INSERT INTO message_history
            (message_id, message_table, version_number, content,
             edited_by_user_id, edit_reason, content_hash, previous_hash, chain_hash,
             editor_platform)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (message_id, message_table, new_version, new_content,
              user_id, edit_reason, new_content_hash, latest['chain_hash'], new_chain_hash,
              request.headers.get('User-Agent', 'unknown')[:50]))

        # Update original message
        db.execute(f'''
            UPDATE {message_table}
            SET content = ?, edited = 1, edit_count = edit_count + 1, last_edited_at = ?
            WHERE id = ?
        ''', (new_content, timestamp, message_id))

        db.commit()

        return jsonify({
            'success': True,
            'message_id': message_id,
            'version': new_version,
            'chain_hash': new_chain_hash,
            'previous_hash': latest['chain_hash'],
            'edited_at': timestamp
        })

    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500


@blamechain_bp.route('/api/blamechain/verify/<message_table>/<int:message_id>')
def verify_chain(message_table, message_id):
    """
    Verify the integrity of the blamechain for a message

    Recalculates all hashes and ensures no tampering occurred

    GET /api/blamechain/verify/messages/123
    """
    db = get_db()

    allowed_tables = ['messages', 'irc_messages', 'dm_messages', 'qr_chat_transcripts']
    if message_table not in allowed_tables:
        return jsonify({'error': 'Invalid message table'}), 400

    try:
        history = db.execute('''
            SELECT version_number, content, content_hash, previous_hash, chain_hash, edited_at
            FROM message_history
            WHERE message_table = ? AND message_id = ?
            ORDER BY version_number ASC
        ''', (message_table, message_id)).fetchall()

        if not history:
            return jsonify({'error': 'No history found'}), 404

        verification_results = []
        chain_valid = True

        for i, row in enumerate(history):
            # Verify content hash
            expected_content_hash = compute_content_hash(row['content'])
            content_hash_valid = (expected_content_hash == row['content_hash'])

            # Verify chain hash
            expected_chain_hash = compute_chain_hash(
                row['previous_hash'],
                row['content_hash'],
                row['edited_at']
            )
            chain_hash_valid = (expected_chain_hash == row['chain_hash'])

            # Verify previous hash links correctly
            if i > 0:
                previous_row = history[i - 1]
                previous_hash_valid = (row['previous_hash'] == previous_row['chain_hash'])
            else:
                # First version should have no previous_hash
                previous_hash_valid = (row['previous_hash'] is None)

            version_valid = content_hash_valid and chain_hash_valid and previous_hash_valid
            chain_valid = chain_valid and version_valid

            verification_results.append({
                'version': row['version_number'],
                'content_hash_valid': content_hash_valid,
                'chain_hash_valid': chain_hash_valid,
                'previous_hash_valid': previous_hash_valid,
                'version_valid': version_valid
            })

        return jsonify({
            'success': True,
            'message_table': message_table,
            'message_id': message_id,
            'chain_valid': chain_valid,
            'total_versions': len(verification_results),
            'verification': verification_results
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@blamechain_bp.route('/api/blamechain/flag-for-tribunal', methods=['POST'])
def flag_for_tribunal():
    """
    Flag a message's edit history for tribunal review

    POST /api/blamechain/flag-for-tribunal
    {
        "message_table": "messages",
        "message_id": 123,
        "reason": "Suspicious edit pattern"
    }

    This creates a Kangaroo Court submission with edit history as evidence
    """
    db = get_db()
    data = request.get_json() or {}

    message_table = data.get('message_table')
    message_id = data.get('message_id')
    reason = data.get('reason', 'Edit history flagged for review')

    if not all([message_table, message_id]):
        return jsonify({'error': 'Missing required fields'}), 400

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        # Get edit history summary
        history = db.execute('''
            SELECT COUNT(*) as total_versions, GROUP_CONCAT(content, ' -> ') as all_versions
            FROM message_history
            WHERE message_table = ? AND message_id = ?
        ''', (message_table, message_id)).fetchone()

        if not history or history['total_versions'] == 0:
            return jsonify({'error': 'No history found'}), 404

        # Create tribunal submission
        transcription = f"Edit History ({history['total_versions']} versions):\n{reason}\n\n{history['all_versions']}"

        db.execute('''
            INSERT INTO kangaroo_submissions
            (user_id, transcription, verdict)
            VALUES (?, ?, 'PENDING')
        ''', (user_id, transcription))

        submission_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]

        # Flag all history entries
        db.execute('''
            UPDATE message_history
            SET flagged_for_tribunal = 1, tribunal_submission_id = ?
            WHERE message_table = ? AND message_id = ?
        ''', (submission_id, message_table, message_id))

        db.commit()

        return jsonify({
            'success': True,
            'tribunal_submission_id': submission_id,
            'message_id': message_id,
            'total_versions_flagged': history['total_versions']
        })

    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500


def init_blamechain(app):
    """Initialize blamechain with Flask app"""
    app.register_blueprint(blamechain_bp)
