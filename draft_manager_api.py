"""
Draft Manager API

Manages the "Chat → Yap → Ideate → Lock In" flow with timers.
Ideas start in draft mode and can be extended or published.
"""

from flask import Blueprint, jsonify, request
import sqlite3
from datetime import datetime, timedelta

draft_manager_bp = Blueprint('draft_manager', __name__)

DEFAULT_DRAFT_TIMER_MINUTES = 15

def get_db_connection():
    """Get database connection with Row factory"""
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_draft_tables():
    """Add draft columns to ideas table if they don't exist"""
    conn = get_db_connection()
    cursor = conn.cursor()

    #  Add columns (SQLite will ignore if they already exist via try/except)
    try:
        cursor.execute('ALTER TABLE ideas ADD COLUMN draft_state TEXT DEFAULT "draft"')
    except:
        pass

    try:
        cursor.execute('ALTER TABLE ideas ADD COLUMN draft_expires_at TEXT')
    except:
        pass

    try:
        cursor.execute('ALTER TABLE ideas ADD COLUMN locked_in INTEGER DEFAULT 0')
    except:
        pass

    conn.commit()
    conn.close()

@draft_manager_bp.route('/api/drafts/active', methods=['GET'])
def get_active_drafts():
    """Get all active drafts with time remaining"""
    try:
        init_draft_tables()
        conn = get_db_connection()
        cursor = conn.cursor()

        user_id = request.args.get('user_id', type=int)

        query = '''
            SELECT i.*, r.filename, r.created_at as recording_created_at
            FROM ideas i
            LEFT JOIN simple_voice_recordings r ON i.recording_id = r.id
            WHERE i.draft_state = 'draft'
            AND i.locked_in = 0
            AND (i.draft_expires_at IS NULL OR i.draft_expires_at > ?)
        '''
        params = [datetime.utcnow().isoformat()]

        if user_id:
            query += ' AND i.user_id = ?'
            params.append(user_id)

        query += ' ORDER BY i.created_at DESC'

        cursor.execute(query, params)
        drafts = cursor.fetchall()

        # Calculate time remaining for each draft
        drafts_list = []
        now = datetime.utcnow()

        for draft in drafts:
            time_remaining = None
            if draft['draft_expires_at']:
                expires_at = datetime.fromisoformat(draft['draft_expires_at'])
                delta = expires_at - now
                time_remaining = int(delta.total_seconds())  # Seconds remaining

            drafts_list.append({
                'id': draft['id'],
                'idea_text': draft['idea_text'],
                'keywords': draft['keywords'],
                'assigned_domain': draft['assigned_domain'],
                'created_at': draft['created_at'],
                'draft_expires_at': draft['draft_expires_at'],
                'time_remaining_seconds': time_remaining,
                'expired': time_remaining is not None and time_remaining <= 0
            })

        conn.close()

        return jsonify({
            'success': True,
            'drafts': drafts_list,
            'count': len(drafts_list)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@draft_manager_bp.route('/api/drafts/extend/<int:idea_id>', methods=['POST'])
def extend_draft(idea_id):
    """Extend draft timer by spending tokens or earning more time"""
    try:
        data = request.get_json()
        minutes_to_add = data.get('minutes', 5)
        user_id = data.get('user_id')

        init_draft_tables()
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get current draft
        cursor.execute('SELECT * FROM ideas WHERE id = ?', (idea_id,))
        draft = cursor.fetchone()

        if not draft:
            return jsonify({'success': False, 'error': 'Draft not found'}), 404

        # Calculate new expiration
        if draft['draft_expires_at']:
            current_expires = datetime.fromisoformat(draft['draft_expires_at'])
        else:
            current_expires = datetime.utcnow()

        new_expires = current_expires + timedelta(minutes=minutes_to_add)

        cursor.execute('''
            UPDATE ideas
            SET draft_expires_at = ?
            WHERE id = ?
        ''', (new_expires.isoformat(), idea_id))

        conn.commit()
        conn.close()

        # Award tokens for extending (engagement reward)
        if user_id:
            try:
                from token_economy_api import earn_tokens
                # User engaged with draft = earn 2 minutes worth of tokens
            except:
                pass

        return jsonify({
            'success': True,
            'idea_id': idea_id,
            'minutes_added': minutes_to_add,
            'new_expiration': new_expires.isoformat()
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@draft_manager_bp.route('/api/drafts/lock-in/<int:idea_id>', methods=['POST'])
def lock_in_draft(idea_id):
    """Lock in draft for immediate publishing"""
    try:
        init_draft_tables()
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE ideas
            SET locked_in = 1, draft_state = 'locked'
            WHERE id = ?
        ''', (idea_id,))

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'idea_id': idea_id,
            'message': 'Draft locked in and ready for publishing'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@draft_manager_bp.route('/api/drafts/auto-lock-expired', methods=['POST'])
def auto_lock_expired():
    """Auto-lock all expired drafts (run periodically)"""
    try:
        init_draft_tables()
        conn = get_db_connection()
        cursor = conn.cursor()

        # Find expired drafts
        cursor.execute('''
            UPDATE ideas
            SET locked_in = 1, draft_state = 'auto-locked'
            WHERE draft_state = 'draft'
            AND locked_in = 0
            AND draft_expires_at IS NOT NULL
            AND draft_expires_at < ?
        ''', (datetime.utcnow().isoformat(),))

        locked_count = cursor.rowcount

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'locked_count': locked_count,
            'message': f'Auto-locked {locked_count} expired drafts'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@draft_manager_bp.route('/api/drafts/stats', methods=['GET'])
def draft_stats():
    """Get draft statistics"""
    try:
        init_draft_tables()
        conn = get_db_connection()
        cursor = conn.cursor()

        user_id = request.args.get('user_id', type=int)

        # Count drafts by state
        query_base = 'SELECT COUNT(*) as count FROM ideas WHERE'
        params = []

        if user_id:
            query_base += ' user_id = ? AND'
            params.append(user_id)

        # Active drafts
        cursor.execute(query_base + ' draft_state = "draft" AND locked_in = 0', params)
        active_count = cursor.fetchone()['count']

        # Locked drafts
        cursor.execute(query_base + ' locked_in = 1', params)
        locked_count = cursor.fetchone()['count']

        # Expired but not locked
        cursor.execute(query_base + ' draft_state = "draft" AND draft_expires_at < ?', params + [datetime.utcnow().isoformat()])
        expired_count = cursor.fetchone()['count']

        conn.close()

        return jsonify({
            'success': True,
            'active_drafts': active_count,
            'locked_drafts': locked_count,
            'expired_drafts': expired_count
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
