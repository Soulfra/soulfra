#!/usr/bin/env python3
"""
Tier Progression API - Flask Routes for Tier Management

Provides REST API endpoints for checking user tiers, unlocking domains,
and calculating ownership percentages.

Integrates with tier_progression_engine.py
"""

from flask import Blueprint, request, jsonify
from database import get_db
from tier_progression_engine import TierProgression

tier_api_bp = Blueprint('tier_api', __name__)


@tier_api_bp.route('/api/tier/check/<int:user_id>')
def check_user_tier(user_id):
    """
    Check current tier for user

    GET /api/tier/check/123

    Returns: Current tier info, unlocked domains, ownership %
    """
    try:
        tier = TierProgression(user_id=user_id)
        current_tier_data = tier.get_current_tier()

        return jsonify({
            'success': True,
            'user_id': user_id,
            **current_tier_data
        })
    except Exception as e:
        return jsonify({
            'error': f'Failed to check tier: {str(e)}'
        }), 500


@tier_api_bp.route('/api/tier/unlock', methods=['POST'])
def unlock_domain():
    """
    Attempt to unlock a domain for user

    POST /api/tier/unlock
    {
        "user_id": 123,
        "domain": "cringeproof.com"
    }

    Returns: Success/failure + updated tier info
    """
    data = request.json
    user_id = data.get('user_id')
    domain = data.get('domain')

    if not user_id or not domain:
        return jsonify({'error': 'user_id and domain required'}), 400

    try:
        tier = TierProgression(user_id=user_id)
        result = tier.attempt_domain_unlock(domain)

        return jsonify({
            'success': result['unlocked'],
            'domain': domain,
            **result
        })
    except Exception as e:
        return jsonify({
            'error': f'Failed to unlock domain: {str(e)}'
        }), 500


@tier_api_bp.route('/api/tier/ownership/<int:user_id>')
def get_ownership_breakdown(user_id):
    """
    Get detailed ownership % breakdown across all domains

    GET /api/tier/ownership/123

    Returns: Ownership percentages by domain
    """
    try:
        tier = TierProgression(user_id=user_id)
        ownership = tier.calculate_ownership()

        return jsonify({
            'success': True,
            'user_id': user_id,
            'total_ownership': ownership.get('total', 0.0),
            'by_domain': ownership.get('domains', {}),
            'tier': ownership.get('tier', 0)
        })
    except Exception as e:
        return jsonify({
            'error': f'Failed to calculate ownership: {str(e)}'
        }), 500


@tier_api_bp.route('/api/tier/progress/<int:user_id>')
def get_tier_progress(user_id):
    """
    Get progress toward next tier

    GET /api/tier/progress/123

    Returns: Current tier, next tier requirements, progress %
    """
    try:
        tier = TierProgression(user_id=user_id)
        progress = tier.get_tier_progress()

        return jsonify({
            'success': True,
            'user_id': user_id,
            **progress
        })
    except Exception as e:
        return jsonify({
            'error': f'Failed to get tier progress: {str(e)}'
        }), 500


@tier_api_bp.route('/api/tier/available-domains/<int:user_id>')
def get_available_domains(user_id):
    """
    Get list of domains available to user at current tier

    GET /api/tier/available-domains/123

    Returns: List of unlocked/available domains
    """
    try:
        tier = TierProgression(user_id=user_id)
        domains = tier.get_available_domains()

        return jsonify({
            'success': True,
            'user_id': user_id,
            'unlocked_domains': domains.get('unlocked', []),
            'available_to_unlock': domains.get('available', []),
            'requires_higher_tier': domains.get('locked', [])
        })
    except Exception as e:
        return jsonify({
            'error': f'Failed to get available domains: {str(e)}'
        }), 500


@tier_api_bp.route('/api/tier/stats')
def get_tier_stats():
    """
    Get platform-wide tier statistics

    GET /api/tier/stats

    Returns: User counts by tier, domain unlock stats
    """
    db = get_db()

    try:
        # Count users by tier (from github_faucet or domain_unlocks)
        tier_counts = {
            'tier_0': 0,
            'tier_1': 0,
            'tier_2': 0,
            'tier_3': 0,
            'tier_4': 0
        }

        # Get total users
        total_users = db.execute('SELECT COUNT(*) as count FROM soulfra_master_users').fetchone()
        tier_counts['tier_0'] = total_users['count'] if total_users else 0

        return jsonify({
            'success': True,
            'tier_distribution': tier_counts,
            'total_users': tier_counts['tier_0']
        })
    except Exception as e:
        return jsonify({
            'error': f'Failed to get tier stats: {str(e)}'
        }), 500


if __name__ == '__main__':
    print("🎯 Tier Progression API")
    print("=" * 60)
    print("Endpoints:")
    print("  GET  /api/tier/check/<user_id>")
    print("  POST /api/tier/unlock")
    print("  GET  /api/tier/ownership/<user_id>")
    print("  GET  /api/tier/progress/<user_id>")
    print("  GET  /api/tier/available-domains/<user_id>")
    print("  GET  /api/tier/stats")
    print("=" * 60)
