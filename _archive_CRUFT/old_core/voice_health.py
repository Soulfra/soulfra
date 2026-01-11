#!/usr/bin/env python3
"""
Voice Health Dashboard - Monitor Voice System Integration

Tracks health metrics for:
- Voice recordings (transcription rate, quality scores)
- QR authentication (active sessions)
- Ollama integration (response time, availability)
- Voice captcha (verification rate, trust scores)
- Question answers (voice vs text, XP distribution)
"""

from flask import Blueprint, render_template, jsonify
from database import get_db
from typing import Dict
import time

voice_health_bp = Blueprint('voice_health', __name__)


def get_voice_health_metrics() -> Dict:
    """
    Collect comprehensive health metrics for voice system

    Returns:
        {
            'voice_recordings': {...},
            'qr_auth': {...},
            'ollama': {...},
            'captcha': {...},
            'questions': {...},
            'overall_health': int (0-100)
        }
    """
    db = get_db()

    # Voice Recordings Metrics
    voice_stats = db.execute('''
        SELECT
            COUNT(*) as total_recordings,
            COUNT(transcription) as transcribed,
            COUNT(CASE WHEN transcription IS NULL THEN 1 END) as null_transcriptions,
            AVG(file_size) as avg_file_size,
            COUNT(DISTINCT user_id) as unique_users
        FROM simple_voice_recordings
    ''').fetchone()

    transcription_rate = 0
    if voice_stats['total_recordings'] > 0:
        transcription_rate = (voice_stats['transcribed'] / voice_stats['total_recordings']) * 100

    # QR Auth Metrics
    qr_stats = db.execute('''
        SELECT
            COUNT(*) as total_sessions,
            COUNT(CASE WHEN expires_at > datetime('now') THEN 1 END) as active_sessions,
            COUNT(DISTINCT device_fingerprint) as unique_devices
        FROM search_sessions
    ''').fetchone()

    # Voice Captcha Metrics
    captcha_stats = db.execute('''
        SELECT
            COUNT(*) as total_challenges,
            COUNT(CASE WHEN used = 1 THEN 1 END) as completed_challenges,
            AVG(match_score) as avg_match_score
        FROM voice_captcha_challenges
    ''').fetchone()

    captcha_completion_rate = 0
    if captcha_stats and captcha_stats['total_challenges'] > 0:
        captcha_completion_rate = (captcha_stats['completed_challenges'] / captcha_stats['total_challenges']) * 100

    # Question Answer Metrics
    question_stats = db.execute('''
        SELECT
            COUNT(*) as total_answers,
            COUNT(DISTINCT user_id) as unique_answerers,
            SUM(xp_awarded) as total_xp_awarded
        FROM user_question_answers
    ''').fetchone()

    # Check Ollama availability
    ollama_status = check_ollama_status()

    # Get recent recordings for quality analysis
    recent_quality = db.execute('''
        SELECT
            id,
            transcription,
            created_at
        FROM simple_voice_recordings
        WHERE transcription IS NOT NULL
        ORDER BY created_at DESC
        LIMIT 10
    ''').fetchall()

    db.close()

    # Analyze recent quality with Ollama (if available)
    avg_quality_score = 50  # Default
    quality_scores = []

    if ollama_status['available'] and len(recent_quality) > 0:
        try:
            from voice_ollama_processor import VoiceOllamaProcessor
            processor = VoiceOllamaProcessor()

            for rec in recent_quality[:5]:  # Only check last 5 to avoid slowdown
                analysis = processor.analyze_recording(rec['id'])
                if 'quality_score' in analysis and 'error' not in analysis:
                    quality_scores.append(analysis['quality_score'])

            if quality_scores:
                avg_quality_score = sum(quality_scores) / len(quality_scores)

        except Exception as e:
            print(f"⚠️  Quality analysis failed in health check: {e}")

    # Calculate overall health score (0-100)
    health_factors = []

    # Factor 1: Transcription rate (30% weight)
    health_factors.append(transcription_rate * 0.3)

    # Factor 2: QR auth active sessions (15% weight)
    qr_health = min(100, (qr_stats['active_sessions'] / max(1, qr_stats['total_sessions'])) * 100) if qr_stats['total_sessions'] > 0 else 0
    health_factors.append(qr_health * 0.15)

    # Factor 3: Ollama availability (25% weight)
    ollama_health = 100 if ollama_status['available'] else 0
    health_factors.append(ollama_health * 0.25)

    # Factor 4: Average quality score (20% weight)
    health_factors.append(avg_quality_score * 0.2)

    # Factor 5: Captcha completion rate (10% weight)
    health_factors.append(captcha_completion_rate * 0.1)

    overall_health = int(sum(health_factors))

    return {
        'voice_recordings': {
            'total': voice_stats['total_recordings'],
            'transcribed': voice_stats['transcribed'],
            'null_transcriptions': voice_stats['null_transcriptions'],
            'transcription_rate': round(transcription_rate, 1),
            'avg_file_size': round(voice_stats['avg_file_size'] or 0, 0),
            'unique_users': voice_stats['unique_users'],
            'avg_quality_score': round(avg_quality_score, 1)
        },
        'qr_auth': {
            'total_sessions': qr_stats['total_sessions'],
            'active_sessions': qr_stats['active_sessions'],
            'unique_devices': qr_stats['unique_devices'],
            'health': round(qr_health, 1)
        },
        'ollama': {
            'available': ollama_status['available'],
            'response_time_ms': ollama_status.get('response_time_ms', 0),
            'error': ollama_status.get('error'),
            'health': ollama_health
        },
        'captcha': {
            'total_challenges': captcha_stats['total_challenges'] if captcha_stats else 0,
            'completed': captcha_stats['completed_challenges'] if captcha_stats else 0,
            'completion_rate': round(captcha_completion_rate, 1),
            'avg_match_score': round(captcha_stats['avg_match_score'] or 0, 1) if captcha_stats else 0
        },
        'questions': {
            'total_answers': question_stats['total_answers'] if question_stats else 0,
            'unique_answerers': question_stats['unique_answerers'] if question_stats else 0,
            'total_xp_awarded': question_stats['total_xp_awarded'] if question_stats else 0
        },
        'overall_health': overall_health,
        'timestamp': time.time()
    }


def check_ollama_status() -> Dict:
    """
    Check if Ollama is available and responsive

    Returns:
        {
            'available': bool,
            'response_time_ms': int,
            'error': str (if any)
        }
    """
    try:
        from ollama_client import OllamaClient
        import time

        client = OllamaClient()

        start = time.time()
        result = client.generate(
            prompt="test",
            model="llama3.2",
            max_tokens=5,
            timeout=5
        )
        response_time_ms = int((time.time() - start) * 1000)

        if result['success']:
            return {
                'available': True,
                'response_time_ms': response_time_ms
            }
        else:
            return {
                'available': False,
                'response_time_ms': response_time_ms,
                'error': result.get('error', 'Unknown error')
            }

    except Exception as e:
        return {
            'available': False,
            'response_time_ms': 0,
            'error': str(e)
        }


# Flask Routes

@voice_health_bp.route('/health/voice')
def voice_health_dashboard():
    """
    Voice health dashboard page

    Shows real-time metrics for all voice system components
    """
    metrics = get_voice_health_metrics()

    return render_template('voice_health.html',
        metrics=metrics
    )


@voice_health_bp.route('/api/health/voice')
def voice_health_api():
    """
    Voice health API endpoint

    Returns JSON health metrics

    Returns:
    {
        "voice_recordings": {...},
        "qr_auth": {...},
        "ollama": {...},
        "captcha": {...},
        "questions": {...},
        "overall_health": 85,
        "timestamp": 1234567890
    }
    """
    metrics = get_voice_health_metrics()

    return jsonify({
        'success': True,
        **metrics
    })


@voice_health_bp.route('/api/health/voice/quick')
def voice_health_quick():
    """
    Quick health check (lightweight)

    Returns:
    {
        "status": "healthy" | "degraded" | "unhealthy",
        "overall_health": 85,
        "timestamp": 1234567890
    }
    """
    db = get_db()

    # Quick checks
    total_recordings = db.execute('SELECT COUNT(*) as count FROM simple_voice_recordings').fetchone()['count']
    active_sessions = db.execute('''
        SELECT COUNT(*) as count FROM search_sessions
        WHERE expires_at > datetime('now')
    ''').fetchone()['count']

    db.close()

    # Quick Ollama check
    ollama_status = check_ollama_status()

    # Calculate quick health score
    health_score = 0

    if total_recordings > 0:
        health_score += 30

    if active_sessions > 0:
        health_score += 20

    if ollama_status['available']:
        health_score += 50

    # Determine status
    if health_score >= 80:
        status = 'healthy'
    elif health_score >= 50:
        status = 'degraded'
    else:
        status = 'unhealthy'

    return jsonify({
        'success': True,
        'status': status,
        'overall_health': health_score,
        'components': {
            'recordings': total_recordings > 0,
            'qr_auth': active_sessions > 0,
            'ollama': ollama_status['available']
        },
        'timestamp': time.time()
    })


def register_voice_health_routes(app):
    """Register voice health routes"""
    app.register_blueprint(voice_health_bp)
    print("✅ Voice Health routes registered:")
    print("   - /health/voice (Health dashboard)")
    print("   - /api/health/voice (Full health metrics)")
    print("   - /api/health/voice/quick (Quick health check)")


if __name__ == '__main__':
    # CLI test
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 voice_health.py check     # Full health check")
        print("  python3 voice_health.py quick     # Quick health check")
        print("  python3 voice_health.py ollama    # Check Ollama only")
        sys.exit(1)

    if sys.argv[1] == 'check':
        metrics = get_voice_health_metrics()
        print(json.dumps(metrics, indent=2))

    elif sys.argv[1] == 'quick':
        # Simulate quick check
        print("Quick health check:")
        print(f"  Overall Health: {get_voice_health_metrics()['overall_health']}/100")

    elif sys.argv[1] == 'ollama':
        status = check_ollama_status()
        print(f"Ollama Status: {status}")
