#!/usr/bin/env python3
"""
Share Analytics - Time-Series Queries and Metrics Aggregation

SQL patterns for connecting data across tables (UNION, JOIN, GROUP BY)

Features:
- Time-series aggregation (hourly/daily/weekly buckets)
- Cross-domain analytics (compare all 5 brands)
- Voice → README pipeline metrics
- User activity tracking
- Hot score calculation (Reddit-style)
- Trend detection
"""

from database import get_db
from datetime import datetime, timedelta
import math


def get_response_analytics(response_id):
    """
    Comprehensive analytics for single response

    Returns metrics, timeline, referrers, devices
    """
    db = get_db()

    # Get response data
    response = db.execute('''
        SELECT * FROM shared_responses WHERE id = ?
    ''', (response_id,)).fetchone()

    if not response:
        db.close()
        return None

    # Get metrics by type
    metrics = db.execute('''
        SELECT metric_type, COUNT(*) as count
        FROM response_metrics
        WHERE response_id = ?
        GROUP BY metric_type
    ''', (response_id,)).fetchall()

    # Get hourly timeline (last 24 hours)
    timeline = db.execute('''
        SELECT
            strftime('%Y-%m-%dT%H:00:00', timestamp) as hour,
            COUNT(*) as count
        FROM response_metrics
        WHERE response_id = ?
        AND metric_type = 'view'
        AND timestamp >= datetime('now', '-1 day')
        GROUP BY hour
        ORDER BY hour
    ''', (response_id,)).fetchall()

    # Get top referrers (from User-Agent)
    referrers = db.execute('''
        SELECT
            CASE
                WHEN user_agent LIKE '%Mobile%' THEN 'Mobile'
                WHEN user_agent LIKE '%iPhone%' THEN 'iPhone'
                WHEN user_agent LIKE '%Android%' THEN 'Android'
                ELSE 'Desktop'
            END as device_type,
            COUNT(*) as count
        FROM response_metrics
        WHERE response_id = ?
        AND metric_type = 'view'
        GROUP BY device_type
        ORDER BY count DESC
    ''', (response_id,)).fetchall()

    db.close()

    return {
        'response': dict(response),
        'metrics': {row['metric_type']: row['count'] for row in metrics},
        'timeline': [{'hour': row['hour'], 'count': row['count']} for row in timeline],
        'devices': [{'type': row['device_type'], 'count': row['count']} for row in referrers]
    }


def get_trending_responses(timeframe='day', limit=10):
    """
    Get trending responses using Reddit hot score algorithm

    hot_score = sign * log(max(abs(views), 1), 10) + (hours_old / 45000)
    """
    db = get_db()

    # Map timeframe to hours
    hours = {
        'hour': 1,
        'day': 24,
        'week': 168,
        'month': 720
    }

    since_hours = hours.get(timeframe, 24)

    trending = db.execute(f'''
        SELECT
            s.id,
            s.response_text,
            s.source_type,
            s.crazy_level,
            s.view_count,
            s.agent_name,
            s.created_at,
            (julianday('now') - julianday(s.created_at)) * 24 as hours_old,
            -- Reddit hot score
            SIGN(s.view_count) * log10(max(abs(s.view_count), 1)) +
            ((julianday('now') - julianday(s.created_at)) * 24 * 3600) / 45000.0
            as hot_score
        FROM shared_responses s
        WHERE s.created_at >= datetime('now', '-{since_hours} hours')
        ORDER BY hot_score DESC
        LIMIT ?
    ''', (limit,)).fetchall()

    db.close()

    return [
        {
            'id': row['id'],
            'excerpt': row['response_text'][:100] + ('...' if len(row['response_text']) > 100 else ''),
            'source': row['source_type'],
            'crazy_level': row['crazy_level'],
            'views': row['view_count'],
            'agent': row['agent_name'],
            'age_hours': row['hours_old'],
            'hot_score': row['hot_score'],
            'timestamp': row['created_at']
        }
        for row in trending
    ]


def get_cross_domain_stats():
    """
    Aggregate stats across all 5 domains (UNION pattern)

    Shows which domain's AI is most active
    """
    db = get_db()

    # Group by agent_name (each domain has an agent)
    stats = db.execute('''
        SELECT
            agent_name,
            COUNT(*) as response_count,
            SUM(view_count) as total_views,
            AVG(crazy_level) as avg_crazy_level,
            MAX(created_at) as last_activity
        FROM shared_responses
        GROUP BY agent_name
        ORDER BY response_count DESC
    ''').fetchall()

    db.close()

    return [
        {
            'agent': row['agent_name'],
            'responses': row['response_count'],
            'total_views': row['total_views'],
            'avg_crazy': round(row['avg_crazy_level'], 1),
            'last_active': row['last_activity']
        }
        for row in stats
    ]


def get_voice_readme_pipeline():
    """
    Track voice memo → README conversion pipeline

    INNER JOIN pattern - Connect voice recordings with shared responses
    """
    db = get_db()

    pipeline = db.execute('''
        SELECT
            v.id as voice_id,
            v.transcription,
            v.created_at as recorded_at,
            s.id as response_id,
            s.response_text,
            s.created_at as analyzed_at,
            s.view_count,
            -- Time from recording to analysis
            (julianday(s.created_at) - julianday(v.created_at)) * 24 as processing_hours
        FROM simple_voice_recordings v
        INNER JOIN shared_responses s ON v.id = s.source_id
        WHERE s.source_type = 'voice'
        ORDER BY s.created_at DESC
        LIMIT 50
    ''').fetchall()

    db.close()

    return [
        {
            'voice_id': row['voice_id'],
            'transcription': row['transcription'][:100],
            'response_id': row['response_id'],
            'response_excerpt': row['response_text'][:100],
            'views': row['view_count'],
            'processing_time_hours': round(row['processing_hours'], 2),
            'recorded_at': row['recorded_at'],
            'analyzed_at': row['analyzed_at']
        }
        for row in pipeline
    ]


def get_user_activity_timeline(user_id, days=7):
    """
    Time-series user activity (GROUP BY date)

    Shows daily activity buckets
    """
    db = get_db()

    activity = db.execute('''
        SELECT
            DATE(created_at) as activity_date,
            COUNT(*) as responses_created,
            SUM(view_count) as total_views_received
        FROM shared_responses
        WHERE user_id = ?
        AND created_at >= datetime('now', '-? days')
        GROUP BY activity_date
        ORDER BY activity_date DESC
    ''', (user_id, days)).fetchall()

    db.close()

    return [
        {
            'date': row['activity_date'],
            'responses': row['responses_created'],
            'views': row['total_views_received']
        }
        for row in activity
    ]


def get_scan_validation_rate():
    """
    QR scanner validation success rate over time

    Time-series aggregation by hour
    """
    db = get_db()

    validation_rate = db.execute('''
        SELECT
            strftime('%Y-%m-%dT%H:00:00', scanned_at) as hour,
            COUNT(*) as total_scans,
            SUM(CASE WHEN validated = 1 THEN 1 ELSE 0 END) as successful_scans,
            CAST(SUM(CASE WHEN validated = 1 THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 100 as success_rate
        FROM scan_history
        WHERE scanned_at >= datetime('now', '-1 day')
        GROUP BY hour
        ORDER BY hour DESC
    ''').fetchall()

    db.close()

    return [
        {
            'hour': row['hour'],
            'total_scans': row['total_scans'],
            'successful': row['successful_scans'],
            'success_rate': round(row['success_rate'], 1)
        }
        for row in validation_rate
    ]


def get_unified_content_feed(limit=50):
    """
    UNION ALL pattern - Combine different content sources

    Merge voice, screenshot, and text inputs into single feed
    """
    db = get_db()

    # UNION ALL - Include all sources
    unified = db.execute('''
        SELECT 'voice' as type, id, transcription as content, created_at
        FROM simple_voice_recordings
        WHERE transcription IS NOT NULL

        UNION ALL

        SELECT 'response' as type, id, response_text as content, created_at
        FROM shared_responses

        ORDER BY created_at DESC
        LIMIT ?
    ''', (limit,)).fetchall()

    db.close()

    return [
        {
            'type': row['type'],
            'id': row['id'],
            'content': row['content'][:150] + ('...' if len(row['content']) > 150 else ''),
            'timestamp': row['created_at']
        }
        for row in unified
    ]


def get_stpetepros_voice_qa_stats():
    """
    Tampa Bay voice Q&A stats (StPetePros integration)

    Shows voice questions vs AI responses
    """
    db = get_db()

    # Get voice Q&A specific to StPetePros domain
    qa_stats = db.execute('''
        SELECT
            COUNT(DISTINCT v.id) as total_questions,
            COUNT(DISTINCT s.id) as total_responses,
            AVG(s.view_count) as avg_views_per_response
        FROM simple_voice_recordings v
        LEFT JOIN shared_responses s ON v.id = s.source_id
        WHERE v.domain = 'stpetepros.com'
        OR s.agent_name = 'stpetepros'
    ''').fetchone()

    # Get top categories (from transcription keywords)
    top_categories = db.execute('''
        SELECT
            CASE
                WHEN v.transcription LIKE '%plumber%' OR v.transcription LIKE '%plumbing%' THEN 'Plumbing'
                WHEN v.transcription LIKE '%electric%' THEN 'Electrical'
                WHEN v.transcription LIKE '%lawyer%' OR v.transcription LIKE '%legal%' THEN 'Legal'
                WHEN v.transcription LIKE '%real estate%' OR v.transcription LIKE '%realtor%' THEN 'Real Estate'
                ELSE 'Other'
            END as category,
            COUNT(*) as count
        FROM simple_voice_recordings v
        WHERE v.domain = 'stpetepros.com'
        GROUP BY category
        ORDER BY count DESC
        LIMIT 5
    ''').fetchall()

    db.close()

    return {
        'overview': dict(qa_stats) if qa_stats else {},
        'top_categories': [
            {'category': row['category'], 'count': row['count']}
            for row in top_categories
        ]
    }


def calculate_response_velocity(response_id, window_hours=1):
    """
    Calculate view velocity (views per hour) for trending detection

    High velocity = going viral
    """
    db = get_db()

    velocity = db.execute('''
        SELECT
            COUNT(*) as recent_views,
            (julianday('now') - julianday(MAX(timestamp))) * 24 as hours_since_last_view
        FROM response_metrics
        WHERE response_id = ?
        AND metric_type = 'view'
        AND timestamp >= datetime('now', '-? hours')
    ''', (response_id, window_hours)).fetchone()

    db.close()

    if not velocity or velocity['recent_views'] == 0:
        return 0.0

    # Views per hour
    return velocity['recent_views'] / window_hours
