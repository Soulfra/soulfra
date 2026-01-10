#!/usr/bin/env python3
"""
Device Fingerprinting API Routes

Endpoints for viewing device information and statistics.

Routes:
- GET /api/devices/<slug> - Get all devices for a user
- GET /api/devices/recording/<recording_id> - Get device for a recording
- GET /api/devices/stats - Get overall device statistics
"""

from flask import Blueprint, jsonify
from database import get_db
from device_hash import get_user_devices, get_recording_device, get_device_stats

device_bp = Blueprint('device', __name__)


@device_bp.route('/api/devices/<slug>')
def get_user_devices_api(slug):
    """
    Get all devices used by a user (by slug)

    Example:
        GET /api/devices/matt

    Response:
        {
            "success": true,
            "devices": [
                {
                    "id": 1,
                    "device_name": "iPhone (iOS 15.0)",
                    "device_type": "iPhone",
                    "first_seen": "2026-01-04T12:00:00Z",
                    "last_seen": "2026-01-04T14:30:00Z",
                    "recording_count": 5
                },
                {
                    "id": 2,
                    "device_name": "Mac (macOS 14.2)",
                    "device_type": "Mac",
                    "first_seen": "2026-01-03T10:00:00Z",
                    "last_seen": "2026-01-04T11:00:00Z",
                    "recording_count": 3
                }
            ]
        }
    """
    db = get_db()

    # Get user by slug
    user = db.execute('SELECT id FROM users WHERE user_slug = ?', (slug,)).fetchone()

    if not user:
        return jsonify({
            'success': False,
            'error': 'User not found'
        }), 404

    devices = get_user_devices(user['id'])

    return jsonify({
        'success': True,
        'devices': devices
    })


@device_bp.route('/api/devices/recording/<int:recording_id>')
def get_recording_device_api(recording_id):
    """
    Get device information for a specific recording

    Example:
        GET /api/devices/recording/123

    Response:
        {
            "success": true,
            "device": {
                "device_name": "iPhone (iOS 15.0)",
                "device_type": "iPhone",
                "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0...",
                "ip_address": "192.168.1.100",
                "first_seen": "2026-01-04T12:00:00Z",
                "recording_count": 5
            }
        }
    """
    device = get_recording_device(recording_id)

    if not device:
        return jsonify({
            'success': False,
            'error': 'Recording not found or no device info'
        }), 404

    return jsonify({
        'success': True,
        'device': device
    })


@device_bp.route('/api/devices/stats')
def get_device_stats_api():
    """
    Get overall device statistics

    Example:
        GET /api/devices/stats

    Response:
        {
            "success": true,
            "total_devices": 10,
            "device_types": {
                "iPhone": 5,
                "Mac": 3,
                "Windows": 2
            },
            "most_active_device": {
                "device_name": "iPhone (iOS 15.0)",
                "device_type": "iPhone",
                "recording_count": 50
            }
        }
    """
    stats = get_device_stats()

    return jsonify({
        'success': True,
        **stats
    })


@device_bp.route('/api/devices/recording/<int:recording_id>/badge.svg')
def device_badge_svg(recording_id):
    """
    Generate SVG badge showing device for a recording

    Example:
        GET /api/devices/recording/123/badge.svg

    Returns:
        SVG image showing device name and type
    """
    from flask import Response

    device = get_recording_device(recording_id)

    if not device:
        # Return "Unknown Device" badge
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="150" height="30">
  <rect width="150" height="30" fill="#6c757d" rx="5"/>
  <text x="75" y="20" text-anchor="middle" font-family="Arial, sans-serif" font-size="12" fill="white">
    Unknown Device
  </text>
</svg>'''
        return Response(svg, mimetype='image/svg+xml')

    # Color code by device type
    color_map = {
        'iPhone': '#007aff',
        'iPad': '#5856d6',
        'Mac': '#5ac8fa',
        'Windows': '#0078d4',
        'Android Phone': '#34c759',
        'Android Tablet': '#32d74b',
        'Linux': '#ff9500',
        'Unknown': '#6c757d'
    }

    color = color_map.get(device['device_type'], '#6c757d')
    device_name = device['device_name']

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="200" height="30">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:{color};stop-opacity:1" />
      <stop offset="100%" style="stop-color:{color};stop-opacity:0.7" />
    </linearGradient>
  </defs>
  <rect width="200" height="30" fill="url(#grad)" rx="5"/>
  <text x="100" y="20" text-anchor="middle" font-family="'SF Pro Display', -apple-system, sans-serif" font-size="12" fill="white" font-weight="600">
    📱 {device_name}
  </text>
</svg>'''

    return Response(svg, mimetype='image/svg+xml')
