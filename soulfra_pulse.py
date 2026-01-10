#!/usr/bin/env python3
"""
Soulfra Pulse - Central Timer/Calendar API

Central hub that all domains watch for:
- Timer events
- Calendar events
- Daily question prompts
- User activity pulses
- Recording routing (categorized voice → appropriate domain)

Other domains poll /api/soulfra/pulse to stay synchronized
"""

from flask import Blueprint, jsonify, request
from database import get_db
from daily_worklog import get_todays_recordings
import json
from datetime import datetime, timedelta

pulse_bp = Blueprint('pulse', __name__)


# Domain routing map (category → domain)
DOMAIN_ROUTES = {
    'work': 'calriven.com',
    'ideas': 'cringeproof.com',
    'personal': 'soulfra.com',
    'learning': 'soulfra.com',
    'goals': 'soulfra.com',
    'random': 'soulfra.com'
}


@pulse_bp.route('/api/soulfra/pulse')
def pulse_feed():
    """
    Central pulse feed - other domains poll this endpoint

    Returns:
    - Active users count
    - Recent timer events
    - Calendar events
    - Daily questions
    - Routed recordings (categorized voice memos)
    """
    db = get_db()

    # Get recent pulse events (last 5 minutes)
    five_min_ago = (datetime.utcnow() - timedelta(minutes=5)).isoformat()

    recent_events = db.execute('''
        SELECT *
        FROM soulfra_pulse_events
        WHERE created_at >= ?
        ORDER BY created_at DESC
        LIMIT 50
    ''', (five_min_ago,)).fetchall()

    # Get active users (logged in last hour)
    one_hour_ago = (datetime.utcnow() - timedelta(hours=1)).isoformat()

    active_users = db.execute('''
        SELECT COUNT(*) as count
        FROM soulfra_master_users
        WHERE last_login >= ?
    ''', (one_hour_ago,)).fetchone()

    # Get today's recordings with domain routing
    recordings = get_todays_recordings()

    # Route recordings to domains (with WORK+IDEAS merge support)
    routed_recordings = {
        'calriven.com': [],
        'cringeproof.com': [],
        'soulfra.com': [],
        'deathtodata.com': [],
        'howtocookathome.com': [],
        'the_play': []  # Special: When WORK + IDEAS merge
    }

    for rec in recordings:
        category = rec.get('category', 'random')
        target_domain = DOMAIN_ROUTES.get(category, 'soulfra.com')

        rec_data = {
            'id': rec['id'],
            'category': category,
            'transcription': rec['transcription'][:100],
            'created_at': rec['created_at'],
            'confidence': rec.get('confidence', 0.0)
        }

        # Check if recording has BOTH work AND ideas (THE PLAY)
        transcription_lower = rec['transcription'].lower()
        has_work = 'work' in transcription_lower or category == 'work'
        has_ideas = 'idea' in transcription_lower or category == 'ideas'

        if has_work and has_ideas:
            # "The Play" - Route to BOTH personas
            routed_recordings['the_play'].append(rec_data)
            routed_recordings['calriven.com'].append(rec_data)  # LIGHT path (execution)
            routed_recordings['cringeproof.com'].append(rec_data)  # SHADOW path (vision)
        else:
            # Normal routing
            routed_recordings[target_domain].append(rec_data)

    # Parse events
    events_list = []
    for event in recent_events:
        events_list.append({
            'id': event['id'],
            'type': event['event_type'],
            'data': json.loads(event['event_data']) if event['event_data'] else {},
            'source_domain': event['source_domain'],
            'created_at': event['created_at']
        })

    return jsonify({
        'timestamp': datetime.utcnow().isoformat(),
        'active_users': active_users['count'] if active_users else 0,
        'recent_events': events_list,
        'routed_recordings': routed_recordings,
        'daily_question': _get_daily_question(),
        'timer_active': _get_active_timers()
    })


@pulse_bp.route('/api/soulfra/pulse/emit', methods=['POST'])
def emit_pulse_event():
    """
    Emit a pulse event (timer start, calendar event, etc.)

    POST /api/soulfra/pulse/emit
    {
        "event_type": "timer_start",  // or "calendar", "daily_question", "goal"
        "event_data": { ... },
        "source_domain": "soulfra.com",
        "master_user_id": 1  // optional
    }
    """
    data = request.json

    event_type = data.get('event_type')
    event_data = data.get('event_data', {})
    source_domain = data.get('source_domain', 'soulfra.com')
    master_user_id = data.get('master_user_id')

    if not event_type:
        return jsonify({'error': 'event_type required'}), 400

    db = get_db()

    # Calculate expiration (1 hour default)
    expires_at = (datetime.utcnow() + timedelta(hours=1)).isoformat()

    cursor = db.execute('''
        INSERT INTO soulfra_pulse_events (
            master_user_id,
            event_type,
            event_data,
            source_domain,
            expires_at
        ) VALUES (?, ?, ?, ?, ?)
    ''', (
        master_user_id,
        event_type,
        json.dumps(event_data),
        source_domain,
        expires_at
    ))

    db.commit()

    return jsonify({
        'success': True,
        'event_id': cursor.lastrowid,
        'message': 'Pulse event emitted'
    }), 201


@pulse_bp.route('/api/soulfra/route-recording', methods=['POST'])
def route_recording():
    """
    Manually route a recording to a specific domain

    POST /api/soulfra/route-recording
    {
        "recording_id": 1,
        "target_domain": "cringeproof.com",
        "reason": "User override"
    }
    """
    data = request.json

    recording_id = data.get('recording_id')
    target_domain = data.get('target_domain')
    reason = data.get('reason', 'Manual routing')

    if not recording_id or not target_domain:
        return jsonify({'error': 'recording_id and target_domain required'}), 400

    db = get_db()

    # Emit pulse event for this routing
    event_data = {
        'recording_id': recording_id,
        'target_domain': target_domain,
        'reason': reason
    }

    expires_at = (datetime.utcnow() + timedelta(hours=24)).isoformat()

    db.execute('''
        INSERT INTO soulfra_pulse_events (
            event_type,
            event_data,
            source_domain,
            expires_at
        ) VALUES (?, ?, ?, ?)
    ''', (
        'recording_routed',
        json.dumps(event_data),
        'soulfra.com',
        expires_at
    ))

    db.commit()

    return jsonify({
        'success': True,
        'recording_id': recording_id,
        'routed_to': target_domain
    })


@pulse_bp.route('/api/soulfra/recordings-for-domain/<domain>')
def recordings_for_domain(domain):
    """
    Get recordings routed to a specific domain

    GET /api/soulfra/recordings-for-domain/cringeproof.com
    """
    recordings = get_todays_recordings()

    domain_recordings = []

    for rec in recordings:
        category = rec.get('category', 'random')
        target_domain = DOMAIN_ROUTES.get(category, 'soulfra.com')

        if target_domain == domain:
            domain_recordings.append({
                'id': rec['id'],
                'category': category,
                'transcription': rec['transcription'],
                'created_at': rec['created_at'],
                'confidence': rec.get('confidence', 0.0)
            })

    return jsonify({
        'domain': domain,
        'count': len(domain_recordings),
        'recordings': domain_recordings
    })


@pulse_bp.route('/api/soulfra/stats')
def soulfra_stats():
    """
    Overall Soulfra platform stats

    Returns:
    - Total users across all domains
    - Recordings by category
    - Active timers
    - Calendar events
    """
    db = get_db()

    # Total master users
    total_users = db.execute(
        'SELECT COUNT(*) as count FROM soulfra_master_users'
    ).fetchone()

    # Today's recordings by category
    recordings = get_todays_recordings()

    category_counts = {}
    for rec in recordings:
        category = rec.get('category', 'random')
        category_counts[category] = category_counts.get(category, 0) + 1

    # Domain distribution
    domain_counts = {}
    for category, count in category_counts.items():
        target_domain = DOMAIN_ROUTES.get(category, 'soulfra.com')
        domain_counts[target_domain] = domain_counts.get(target_domain, 0) + count

    return jsonify({
        'total_users': total_users['count'] if total_users else 0,
        'recordings_today': len(recordings),
        'category_breakdown': category_counts,
        'domain_distribution': domain_counts,
        'timestamp': datetime.utcnow().isoformat()
    })


# Helper functions

def _get_daily_question():
    """Get today's daily question prompt"""
    # Rotate questions based on day of week
    questions = [
        "What's one thing you learned today?",
        "What are you grateful for?",
        "What's your biggest challenge right now?",
        "What's one goal you want to achieve this week?",
        "Who inspired you today?",
        "What would make tomorrow better than today?",
        "What's one thing you'd like to improve?"
    ]

    day_of_week = datetime.utcnow().weekday()
    return questions[day_of_week]


def _get_active_timers():
    """Check if any timers are currently active"""
    db = get_db()

    now = datetime.utcnow().isoformat()

    active_timers = db.execute('''
        SELECT COUNT(*) as count
        FROM soulfra_pulse_events
        WHERE event_type = 'timer_start'
          AND expires_at > ?
    ''', (now,)).fetchone()

    return active_timers['count'] if active_timers else 0


if __name__ == '__main__':
    print("Soulfra Pulse API - Central hub for all domains")
    print("\nDomain Routes:")
    for category, domain in DOMAIN_ROUTES.items():
        print(f"  {category:15s} → {domain}")
