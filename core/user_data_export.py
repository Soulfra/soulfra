#!/usr/bin/env python3
"""
User Data Export - GDPR/SOC2 Compliance

Export all user data in JSON format for GDPR compliance.
Includes everything the user has created, unlocked, or interacted with.

Features:
- Complete data export (quiz history, unlocks, profile, QR scans)
- JSON format for easy parsing
- Privacy-compliant (only user's own data)
- Includes metadata (export date, user info)

Usage:
    from user_data_export import export_user_data, delete_user_account

    # Export user data
    data = export_user_data(user_id=42)

    # Delete account (GDPR right to deletion)
    success = delete_user_account(user_id=42, confirmation='DELETE')
"""

import json
from datetime import datetime
from typing import Dict, Optional, List
from database import get_db


def export_user_data(user_id: int) -> Dict:
    """
    Export all user data (GDPR compliant)

    Args:
        user_id: User ID to export

    Returns:
        Dict with all user data:
        {
            'export_info': {...},
            'profile': {...},
            'quiz_history': [...],
            'unlocks': [...],
            'qr_scans': [...],
            'connections': [...]
        }
    """
    db = get_db()

    # Get user profile
    user = db.execute('''
        SELECT id, username, email, display_name, bio, profile_pic,
               is_admin, is_ai_persona, created_at, character_age,
               total_years_aged, personality_profile
        FROM users
        WHERE id = ?
    ''', (user_id,)).fetchone()

    if not user:
        return {'error': 'User not found'}

    user_dict = dict(user)

    # Get quiz history (narrative sessions)
    quiz_history = db.execute('''
        SELECT ns.id, ns.brand_id, b.name as brand_name, b.slug as brand_slug,
               ns.current_chapter, ns.game_state, ns.status,
               ns.created_at, ns.completed_at
        FROM narrative_sessions ns
        LEFT JOIN brands b ON ns.brand_id = b.id
        WHERE ns.user_id = ?
        ORDER BY ns.created_at DESC
    ''', (user_id,)).fetchall()

    quiz_history_list = [dict(row) for row in quiz_history]

    # Get unlocked features (keyring)
    unlocks = db.execute('''
        SELECT id, feature_key, unlocked_at, expires_at, unlock_source
        FROM user_unlocks
        WHERE user_id = ?
        ORDER BY unlocked_at DESC
    ''', (user_id,)).fetchall()

    unlocks_list = [dict(row) for row in unlocks]

    # Get QR code scans (if user generated QR codes)
    qr_scans = db.execute('''
        SELECT f.id as faucet_id, f.payload_type, f.times_scanned,
               f.created_at, f.last_scanned_at
        FROM qr_faucets f
        WHERE f.payload_data LIKE ?
        ORDER BY f.created_at DESC
    ''', (f'%"user_id":{user_id}%',)).fetchall()

    qr_scans_list = [dict(row) for row in qr_scans]

    # Get user connections (if they exist)
    connections = db.execute('''
        SELECT uc.id, uc.connection_type, uc.status,
               uc.compatibility_score, uc.created_at,
               u.username as connected_user
        FROM user_connections uc
        LEFT JOIN users u ON (
            CASE
                WHEN uc.user_id_1 = ? THEN uc.user_id_2
                ELSE uc.user_id_1
            END = u.id
        )
        WHERE uc.user_id_1 = ? OR uc.user_id_2 = ?
        ORDER BY uc.created_at DESC
    ''', (user_id, user_id, user_id)).fetchall()

    connections_list = [dict(row) for row in connections]

    # Build export data
    export_data = {
        'export_info': {
            'exported_at': datetime.now().isoformat(),
            'user_id': user_id,
            'username': user_dict['username'],
            'format_version': '1.0'
        },
        'profile': {
            'username': user_dict['username'],
            'email': user_dict['email'],
            'display_name': user_dict['display_name'],
            'bio': user_dict['bio'],
            'profile_pic': user_dict['profile_pic'],
            'created_at': user_dict['created_at'],
            'character_age': user_dict['character_age'],
            'total_years_aged': user_dict['total_years_aged'],
            'personality_profile': user_dict['personality_profile']
        },
        'quiz_history': quiz_history_list,
        'unlocks': unlocks_list,
        'qr_scans': qr_scans_list,
        'connections': connections_list,
        'stats': {
            'total_quizzes_completed': len([q for q in quiz_history_list if q.get('status') == 'completed']),
            'total_unlocks': len(unlocks_list),
            'total_connections': len(connections_list),
            'account_age_days': (datetime.now() - datetime.fromisoformat(user_dict['created_at'])).days
        }
    }

    return export_data


def export_user_data_json(user_id: int, pretty: bool = True) -> str:
    """
    Export user data as JSON string

    Args:
        user_id: User ID
        pretty: Pretty-print JSON (default True)

    Returns:
        JSON string
    """
    data = export_user_data(user_id)

    if pretty:
        return json.dumps(data, indent=2, ensure_ascii=False)
    else:
        return json.dumps(data, ensure_ascii=False)


def get_user_stats(user_id: int) -> Dict:
    """
    Get user statistics for dashboard

    Args:
        user_id: User ID

    Returns:
        Dict with user stats
    """
    db = get_db()

    # Quiz stats
    quiz_stats = db.execute('''
        SELECT
            COUNT(*) as total_sessions,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
            SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active
        FROM narrative_sessions
        WHERE user_id = ?
    ''', (user_id,)).fetchone()

    # Unlock stats
    unlock_stats = db.execute('''
        SELECT COUNT(*) as total_unlocks
        FROM user_unlocks
        WHERE user_id = ?
          AND (expires_at IS NULL OR expires_at > datetime('now'))
    ''', (user_id,)).fetchone()

    # Connection stats
    connection_stats = db.execute('''
        SELECT COUNT(*) as total_connections
        FROM user_connections
        WHERE (user_id_1 = ? OR user_id_2 = ?)
          AND status = 'active'
    ''', (user_id, user_id)).fetchone()

    return {
        'quizzes': {
            'total': quiz_stats['total_sessions'] if quiz_stats else 0,
            'completed': quiz_stats['completed'] if quiz_stats else 0,
            'active': quiz_stats['active'] if quiz_stats else 0
        },
        'unlocks': {
            'total': unlock_stats['total_unlocks'] if unlock_stats else 0
        },
        'connections': {
            'total': connection_stats['total_connections'] if connection_stats else 0
        }
    }


def delete_user_account(user_id: int, confirmation: str) -> tuple[bool, str]:
    """
    Delete user account and all associated data (GDPR right to deletion)

    Args:
        user_id: User ID to delete
        confirmation: Must be exactly 'DELETE' to proceed

    Returns:
        Tuple of (success, message)
    """
    if confirmation != 'DELETE':
        return False, 'Confirmation failed. Must type DELETE to confirm.'

    db = get_db()

    # Check if user exists
    user = db.execute('SELECT id, username FROM users WHERE id = ?', (user_id,)).fetchone()

    if not user:
        return False, 'User not found'

    username = user['username']

    try:
        # Delete user data (cascading deletes handled by foreign keys)
        # 1. Narrative sessions
        db.execute('DELETE FROM narrative_sessions WHERE user_id = ?', (user_id,))

        # 2. User unlocks
        db.execute('DELETE FROM user_unlocks WHERE user_id = ?', (user_id,))

        # 3. User connections
        db.execute('DELETE FROM user_connections WHERE user_id_1 = ? OR user_id_2 = ?',
                  (user_id, user_id))

        # 4. QR auth tokens
        db.execute('DELETE FROM qr_auth_tokens WHERE user_id = ?', (user_id,))

        # 5. Finally, delete user
        db.execute('DELETE FROM users WHERE id = ?', (user_id,))

        db.commit()

        return True, f'Account {username} (ID: {user_id}) deleted successfully'

    except Exception as e:
        db.rollback()
        return False, f'Error deleting account: {str(e)}'


def anonymize_user_data(user_id: int) -> tuple[bool, str]:
    """
    Anonymize user data (alternative to full deletion)

    Keeps statistical data but removes personal identifiers.

    Args:
        user_id: User ID to anonymize

    Returns:
        Tuple of (success, message)
    """
    db = get_db()

    # Check if user exists
    user = db.execute('SELECT id, username FROM users WHERE id = ?', (user_id,)).fetchone()

    if not user:
        return False, 'User not found'

    try:
        # Anonymize user data
        anonymous_username = f"deleted_user_{user_id}"
        anonymous_email = f"deleted_{user_id}@anonymized.local"

        db.execute('''
            UPDATE users
            SET username = ?,
                email = ?,
                display_name = 'Deleted User',
                bio = NULL,
                profile_pic = NULL,
                password_hash = 'ANONYMIZED'
            WHERE id = ?
        ''', (anonymous_username, anonymous_email, user_id))

        db.commit()

        return True, f'User {user_id} anonymized successfully'

    except Exception as e:
        db.rollback()
        return False, f'Error anonymizing account: {str(e)}'


# CLI for testing
if __name__ == '__main__':
    import sys

    print("User Data Export & Management\n")

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'export' and len(sys.argv) >= 3:
            # Export user data
            user_id = int(sys.argv[2])
            data = export_user_data(user_id)

            if 'error' in data:
                print(f"❌ {data['error']}")
            else:
                print(f"✅ Exported data for user {user_id}")
                print(f"\n{json.dumps(data, indent=2)}")

                # Save to file
                filename = f"user_{user_id}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(filename, 'w') as f:
                    f.write(json.dumps(data, indent=2))
                print(f"\n💾 Saved to: {filename}")

        elif command == 'stats' and len(sys.argv) >= 3:
            # Get user stats
            user_id = int(sys.argv[2])
            stats = get_user_stats(user_id)

            print(f"User {user_id} Stats:")
            print(f"  Quizzes: {stats['quizzes']['completed']}/{stats['quizzes']['total']} completed")
            print(f"  Unlocks: {stats['unlocks']['total']}")
            print(f"  Connections: {stats['connections']['total']}")

        elif command == 'delete' and len(sys.argv) >= 3:
            # Delete user (requires confirmation)
            user_id = int(sys.argv[2])
            confirmation = sys.argv[3] if len(sys.argv) > 3 else ''

            if confirmation != 'DELETE':
                print("⚠️  WARNING: This will permanently delete the user account!")
                print(f"To confirm, run: python3 user_data_export.py delete {user_id} DELETE")
            else:
                success, message = delete_user_account(user_id, confirmation)

                if success:
                    print(f"✅ {message}")
                else:
                    print(f"❌ {message}")

        else:
            print("Unknown command")

    else:
        print("Commands:\n")
        print("  python3 user_data_export.py export <user_id>")
        print("      Export all data for user\n")
        print("  python3 user_data_export.py stats <user_id>")
        print("      Show user statistics\n")
        print("  python3 user_data_export.py delete <user_id> DELETE")
        print("      Delete user account (requires DELETE confirmation)\n")
        print("Examples:")
        print("  python3 user_data_export.py export 1")
        print("  python3 user_data_export.py stats 1")
        print("  python3 user_data_export.py delete 1 DELETE")
