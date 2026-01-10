#!/usr/bin/env python3
"""
Workflow Stats API - Powers shields.io badge tracking

This endpoint returns JSON for shields.io dynamic badges embedded in GitHub READMEs.
When someone views a README, their browser fetches the badge image from shields.io,
which then fetches this JSON to get the current count.

We track every request to build analytics on which workflows/industries are trending.
"""

from flask import Blueprint, jsonify, request
from database import get_db
import json
from datetime import datetime, timedelta

stats_bp = Blueprint('workflow_stats', __name__)


@stats_bp.route('/api/workflow-stats')
def workflow_stats():
    """
    Endpoint for shields.io dynamic badges

    Query params:
        ?industry=comics  - Get stats for specific industry
        (none)            - Get overall stats

    Returns JSON format that shields.io expects:
    {
        "schemaVersion": 1,
        "label": "views",
        "message": "1234",
        "color": "blue"
    }
    """
    db = get_db()
    industry = request.args.get('industry')

    # Track this view
    referrer = request.headers.get('Referer', 'direct')
    user_agent = request.headers.get('User-Agent', 'unknown')

    db.execute('''
        INSERT INTO workflow_view_tracking (
            industry, referrer, user_agent, ip_address
        ) VALUES (?, ?, ?, ?)
    ''', (industry, referrer, user_agent, request.remote_addr))
    db.commit()

    if industry:
        # Get views for this specific industry
        result = db.execute('''
            SELECT COUNT(*) as views
            FROM workflow_view_tracking
            WHERE industry = ?
        ''', (industry,)).fetchone()

        views = result['views']

        return jsonify({
            "schemaVersion": 1,
            "label": "views",
            "message": str(views),
            "color": "blue"
        })

    else:
        # Overall stats
        total_templates = db.execute('''
            SELECT COUNT(*) as count FROM workflow_templates
        ''').fetchone()['count']

        active_pipelines = db.execute('''
            SELECT COUNT(*) as count FROM project_pipelines
            WHERE status = 'active'
        ''').fetchone()['count']

        return jsonify({
            "total": total_templates,
            "active": active_pipelines
        })


@stats_bp.route('/api/analytics/dashboard')
def analytics_dashboard():
    """
    Internal analytics dashboard - shows what's working

    Returns:
    - Total views by industry
    - Trending workflows (most active in last 7 days)
    - Click-through rates on promotion links
    - Referrer sources (who's linking to us)
    """
    db = get_db()

    # Views by industry
    views_by_industry = db.execute('''
        SELECT
            industry,
            COUNT(*) as total_views,
            COUNT(DISTINCT DATE(created_at)) as days_tracked
        FROM workflow_view_tracking
        WHERE industry IS NOT NULL
        GROUP BY industry
        ORDER BY total_views DESC
    ''').fetchall()

    # Trending in last 7 days
    trending = db.execute('''
        SELECT
            industry,
            COUNT(*) as recent_views
        FROM workflow_view_tracking
        WHERE created_at >= datetime('now', '-7 days')
            AND industry IS NOT NULL
        GROUP BY industry
        ORDER BY recent_views DESC
    ''').fetchall()

    # Referrer analysis
    referrers = db.execute('''
        SELECT
            CASE
                WHEN referrer LIKE '%github.com%' THEN 'GitHub'
                WHEN referrer LIKE '%google.com%' THEN 'Google'
                WHEN referrer LIKE '%twitter.com%' THEN 'Twitter'
                WHEN referrer LIKE '%reddit.com%' THEN 'Reddit'
                WHEN referrer = 'direct' THEN 'Direct'
                ELSE 'Other'
            END as source,
            COUNT(*) as views
        FROM workflow_view_tracking
        GROUP BY source
        ORDER BY views DESC
    ''').fetchall()

    # Click-through tracking (from promotion links)
    # This requires tracking clicks on the promotion badges
    promotions = db.execute('''
        SELECT
            target_service,
            industry_context,
            COUNT(*) as clicks
        FROM promotion_click_tracking
        GROUP BY target_service, industry_context
        ORDER BY clicks DESC
        LIMIT 20
    ''').fetchall() if db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='promotion_click_tracking'"
    ).fetchone() else []

    return jsonify({
        "views_by_industry": [dict(row) for row in views_by_industry],
        "trending": [dict(row) for row in trending],
        "referrers": [dict(row) for row in referrers],
        "promotions": [dict(row) for row in promotions]
    })


@stats_bp.route('/api/track/promotion-click')
def track_promotion_click():
    """
    Track when someone clicks a promotion badge in the README

    Query params:
        ?service=cringeproof-freelancers
        &industry=comics
        &ref=github-readme-comics
    """
    db = get_db()

    service = request.args.get('service')
    industry = request.args.get('industry')
    ref = request.args.get('ref')

    # Ensure promotion_click_tracking table exists
    db.execute('''
        CREATE TABLE IF NOT EXISTS promotion_click_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target_service TEXT,
            industry_context TEXT,
            ref_param TEXT,
            referrer TEXT,
            user_agent TEXT,
            ip_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    db.execute('''
        INSERT INTO promotion_click_tracking (
            target_service, industry_context, ref_param, referrer, user_agent, ip_address
        ) VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        service,
        industry,
        ref,
        request.headers.get('Referer', 'direct'),
        request.headers.get('User-Agent', 'unknown'),
        request.remote_addr
    ))

    db.commit()

    # Redirect to actual service
    # (In production, this would be a proper redirect)
    return jsonify({"tracked": True, "service": service, "industry": industry})


def register_workflow_stats_routes(app):
    """Register stats routes with the app"""
    app.register_blueprint(stats_bp)

    # Create view tracking table if it doesn't exist
    db = get_db()
    db.execute('''
        CREATE TABLE IF NOT EXISTS workflow_view_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            industry TEXT,
            referrer TEXT,
            user_agent TEXT,
            ip_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    db.commit()

    print("✅ Workflow stats API routes registered")
