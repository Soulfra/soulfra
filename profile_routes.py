#!/usr/bin/env python3
"""
CringeProof Profile Routes - Show skills verified by voice

Routes:
- GET /profile/<username> - User's voice-verified skill profile
- GET /api/profile/<username> - JSON profile data

Skills are extracted from voice recording transcriptions via AI
"""

from flask import jsonify, request, render_template, Blueprint
from database import get_db
import json

profile_bp = Blueprint('profile', __name__)


@profile_bp.route('/profile/<username>')
def user_profile(username):
    """
    Display user's voice-verified skill profile

    Shows:
    - User info + reputation
    - Voice recordings (proof of knowledge)
    - AI-extracted skills from voice
    - Skill badges/certifications
    """
    db = get_db()

    # Get user
    user = db.execute('''
        SELECT u.*,
               COALESCE(r.bits_earned, 0) as reputation,
               COALESCE(r.contribution_count, 0) as contributions
        FROM users u
        LEFT JOIN reputation r ON r.user_id = u.id
        WHERE u.username = ?
    ''', (username,)).fetchone()

    if not user:
        return "User not found", 404

    # Get voice recordings with transcriptions
    recordings = db.execute('''
        SELECT id, transcription, created_at, file_path
        FROM simple_voice_recordings
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 20
    ''', (user['id'],)).fetchall()

    # Get skill certifications
    skills = db.execute('''
        SELECT skill_name, skill_category, level, verified, issued_at
        FROM skill_certifications
        WHERE user_id = ?
        ORDER BY issued_at DESC
    ''', (user['id'],)).fetchall()

    db.close()

    return render_template('profile.html',
                         user=dict(user),
                         recordings=[dict(r) for r in recordings],
                         skills=[dict(s) for s in skills])


@profile_bp.route('/api/profile/<username>')
def api_user_profile(username):
    """JSON API for profile data"""
    db = get_db()

    user = db.execute('''
        SELECT u.id, u.username, u.display_name, u.created_at,
               COALESCE(r.bits_earned, 0) as reputation,
               COALESCE(r.contribution_count, 0) as contributions
        FROM users u
        LEFT JOIN reputation r ON r.user_id = u.id
        WHERE u.username = ?
    ''', (username,)).fetchone()

    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404

    recordings = db.execute('''
        SELECT id, transcription, created_at
        FROM simple_voice_recordings
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 20
    ''', (user['id'],)).fetchall()

    skills = db.execute('''
        SELECT skill_name, skill_category, level, verified
        FROM skill_certifications
        WHERE user_id = ?
    ''', (user['id'],)).fetchall()

    db.close()

    return jsonify({
        'success': True,
        'user': dict(user),
        'recordings': [dict(r) for r in recordings],
        'skills': [dict(s) for s in skills],
        'total_recordings': len(recordings),
        'total_skills': len(skills)
    })


def register_profile_routes(app):
    """Register profile routes with Flask app"""
    app.register_blueprint(profile_bp)
    print("✅ Profile routes registered:")
    print("   - GET /profile/<username>")
    print("   - GET /api/profile/<username>")
