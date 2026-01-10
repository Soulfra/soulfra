#!/usr/bin/env python3
"""
Recent Activity API - Show who's recording and what they're saying

GET /api/recent-activity?limit=10
Returns:
{
    "activity": [
        {
            "user_email": "user@example.com",
            "user_id": 1,
            "transcription_preview": "I was thinking about decentralization...",
            "recorded_at": "2026-01-04T02:30:00Z",
            "recording_id": 123,
            "keywords": ["decentralization", "blockchain", "web3"]
        }
    ]
}

GET /api/top-contributors?limit=10
Returns:
{
    "contributors": [
        {
            "user_email": "user@example.com",
            "user_id": 1,
            "recording_count": 47,
            "unique_words": 523,
            "level": 3,
            "last_recorded": "2026-01-04T02:30:00Z"
        }
    ]
}
"""

from database import get_db
from flask import jsonify, request


def get_recent_activity(limit=10):
    """Get recent recording activity across all users"""
    db = get_db()

    results = db.execute('''
        SELECT
            u.display_name as user_email,
            u.id as user_id,
            r.transcription,
            r.created_at as recorded_at,
            r.id as recording_id
        FROM simple_voice_recordings r
        JOIN users u ON r.user_id = u.id
        WHERE r.transcription IS NOT NULL
          AND r.transcription != ''
        ORDER BY r.created_at DESC
        LIMIT ?
    ''', (limit,)).fetchall()

    activity = []
    for row in results:
        # Extract keywords (first 3-5 interesting words)
        words = row['transcription'].split()
        keywords = [w.strip('.,!?') for w in words if len(w) > 5][:5]

        # Preview first 80 chars
        preview = row['transcription'][:80]
        if len(row['transcription']) > 80:
            preview += "..."

        activity.append({
            'user_email': row['user_email'],
            'user_id': row['user_id'],
            'transcription_preview': preview,
            'recorded_at': row['recorded_at'],
            'recording_id': row['recording_id'],
            'keywords': keywords
        })

    return {'activity': activity}


def get_top_contributors(limit=10):
    """Get top contributors by recording count"""
    db = get_db()

    results = db.execute('''
        SELECT
            u.display_name as user_email,
            u.id as user_id,
            COUNT(r.id) as recording_count,
            MAX(r.created_at) as last_recorded
        FROM users u
        LEFT JOIN simple_voice_recordings r ON u.id = r.user_id
        GROUP BY u.id
        HAVING recording_count > 0
        ORDER BY recording_count DESC
        LIMIT ?
    ''', (limit,)).fetchall()

    contributors = []
    for row in results:
        # Get wordmap data from user_wordmaps
        wordmap = db.execute('''
            SELECT wordmap_json, recording_count
            FROM user_wordmaps
            WHERE user_id = ?
        ''', (row['user_id'],)).fetchone()

        unique_words = 0
        if wordmap and wordmap['wordmap_json']:
            try:
                import json
                wordmap_data = json.loads(wordmap['wordmap_json'])
                unique_words = len(wordmap_data)  # Count unique words
            except:
                unique_words = 0

        contributors.append({
            'user_email': row['user_email'],
            'user_id': row['user_id'],
            'recording_count': row['recording_count'],
            'unique_words': unique_words,
            'last_recorded': row['last_recorded']
        })

    return {'contributors': contributors}


# Flask route integration (add to cringeproof_api.py)
def register_activity_routes(app):
    """Register activity API routes"""

    @app.route('/api/recent-activity', methods=['GET'])
    def recent_activity():
        limit = request.args.get('limit', 10, type=int)
        return jsonify(get_recent_activity(limit))

    @app.route('/api/top-contributors', methods=['GET'])
    def top_contributors():
        limit = request.args.get('limit', 10, type=int)
        return jsonify(get_top_contributors(limit))


if __name__ == '__main__':
    # Test the functions
    print("Recent Activity:")
    print(get_recent_activity(5))

    print("\nTop Contributors:")
    print(get_top_contributors(5))
