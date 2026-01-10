#!/usr/bin/env python3
"""
Export Replays - Generate .replay JSON files like Starcraft
Exports scan sessions with full event timeline
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = 'soulfra.db'
OUTPUT_DIR = 'build/replays'

def export_replays():
    """Export all scan sessions as .replay JSON files"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Get all completed scan sessions
    sessions = conn.execute('''
        SELECT * FROM scan_sessions
        WHERE ended_at IS NOT NULL
        ORDER BY ended_at DESC
    ''').fetchall()

    print(f"📦 Found {len(sessions)} completed sessions")

    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    for session in sessions:
        session_id = session['id']

        # Get all scans in this session
        scans = conn.execute('''
            SELECT * FROM scan_history
            WHERE session_id = ?
            ORDER BY scanned_at ASC
        ''', (session_id,)).fetchall()

        # Get achievements unlocked in this session
        achievements = []
        if session['badges_unlocked']:
            badge_codes = session['badges_unlocked'].split(',')
            for code in badge_codes:
                badge = conn.execute('''
                    SELECT * FROM user_achievements
                    WHERE achievement_code = ? AND user_id = ?
                ''', (code, session['user_id'])).fetchone()
                if badge:
                    achievements.append(dict(badge))

        # Build replay data
        replay = {
            'version': '1.0',
            'session_id': session_id,
            'user_id': session['user_id'],
            'started_at': session['started_at'],
            'ended_at': session['ended_at'],
            'duration_seconds': None,  # Calculate if needed
            'stats': {
                'total_scans': session['total_scans'],
                'successful_scans': session['successful_scans'],
                'xp_gained': session['xp_gained'],
                'accuracy': round((session['successful_scans'] / session['total_scans'] * 100) if session['total_scans'] > 0 else 0, 2)
            },
            'achievements_unlocked': achievements,
            'scan_timeline': [
                {
                    'timestamp': scan['scanned_at'],
                    'code_type': scan['code_type'],
                    'code_value': scan['code_value'],
                    'validated': bool(scan['validated'])
                }
                for scan in scans
            ],
            'session_data': json.loads(session['session_data']) if session['session_data'] else {}
        }

        # Write replay file
        filename = f"{OUTPUT_DIR}/{session_id}.replay"
        with open(filename, 'w') as f:
            json.dump(replay, f, indent=2)

        print(f"  ✅ {filename} ({replay['stats']['total_scans']} scans, {replay['stats']['xp_gained']} XP)")

    conn.close()
    print(f"\n🎮 Exported {len(sessions)} replay files to {OUTPUT_DIR}/")

if __name__ == '__main__':
    export_replays()
