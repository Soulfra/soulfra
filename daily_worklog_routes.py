#!/usr/bin/env python3
"""
Daily Worklog Routes
Simple dashboard to review your day
"""

from flask import Blueprint, render_template_string, jsonify, request
from daily_worklog import get_todays_recordings, generate_daily_summary, save_daily_worklog, get_daily_worklog
from datetime import date

daily_bp = Blueprint('daily', __name__)


@daily_bp.route('/daily')
def daily_dashboard():
    """Your daily dashboard - review today's work"""

    template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily Dashboard - {{ today }}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { font-size: 2.5rem; margin-bottom: 0.5rem; }
        .subtitle { opacity: 0.9; margin-bottom: 2rem; }
        .card {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 16px;
            padding: 2rem;
            backdrop-filter: blur(10px);
            margin-bottom: 2rem;
        }
        .btn {
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: white;
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 10px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            margin-right: 1rem;
        }
        .btn:hover { transform: translateY(-2px); }
        .category { margin-bottom: 2rem; }
        .category h2 {
            font-size: 1.3rem;
            margin-bottom: 1rem;
            border-left: 4px solid #38ef7d;
            padding-left: 1rem;
        }
        .recording {
            background: rgba(255, 255, 255, 0.05);
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 0.5rem;
        }
        .recording .time {
            font-weight: 600;
            color: #38ef7d;
            margin-right: 0.5rem;
        }
        #summary {
            background: rgba(255, 255, 255, 0.15);
            padding: 2rem;
            border-radius: 12px;
            white-space: pre-wrap;
            line-height: 1.6;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }
        .stat {
            background: rgba(255, 255, 255, 0.1);
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
        }
        .stat-value {
            font-size: 2rem;
            font-weight: 800;
            color: #38ef7d;
        }
        .stat-label { opacity: 0.9; margin-top: 0.5rem; }
        .loading { text-align: center; padding: 2rem; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📅 Daily Dashboard</h1>
        <p class="subtitle">Review your day • {{ today }}</p>

        <div class="card">
            <button class="btn" onclick="generateSummary()">🤖 Generate AI Summary</button>
            <button class="btn" onclick="saveSummary()" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">💾 Save Worklog</button>
            <button class="btn" onclick="location.href='/voice'" style="background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);">🎤 Record Voice</button>
        </div>

        <div class="stats" id="stats">
            <div class="stat">
                <div class="stat-value">0</div>
                <div class="stat-label">Total Recordings</div>
            </div>
            <div class="stat">
                <div class="stat-value">0</div>
                <div class="stat-label">Work Items</div>
            </div>
            <div class="stat">
                <div class="stat-value">0</div>
                <div class="stat-label">Ideas</div>
            </div>
            <div class="stat">
                <div class="stat-value">0</div>
                <div class="stat-label">Goals</div>
            </div>
        </div>

        <div class="card">
            <h2 style="margin-bottom: 1rem;">🧠 AI Summary</h2>
            <div id="summary">Click "Generate AI Summary" to create your daily worklog</div>
        </div>

        <div class="card" id="categories">
            <h2 style="margin-bottom: 1.5rem;">📝 Today's Recordings</h2>
            <div class="loading">Loading recordings...</div>
        </div>
    </div>

    <script>
        async function loadRecordings() {
            const res = await fetch('/api/daily/recordings');
            const recordings = await res.json();

            const statsEl = document.getElementById('stats');
            const categoriesEl = document.getElementById('categories');

            // Update stats
            const total = recordings.length;
            const work = recordings.filter(r => r.category === 'work').length;
            const ideas = recordings.filter(r => r.category === 'ideas').length;
            const goals = recordings.filter(r => r.category === 'goals').length;

            statsEl.innerHTML = `
                <div class="stat"><div class="stat-value">${total}</div><div class="stat-label">Total Recordings</div></div>
                <div class="stat"><div class="stat-value">${work}</div><div class="stat-label">Work Items</div></div>
                <div class="stat"><div class="stat-value">${ideas}</div><div class="stat-label">Ideas</div></div>
                <div class="stat"><div class="stat-value">${goals}</div><div class="stat-label">Goals</div></div>
            `;

            // Group by category
            const byCategory = {};
            recordings.forEach(r => {
                if (!byCategory[r.category]) byCategory[r.category] = [];
                byCategory[r.category].push(r);
            });

            // Display categories
            let html = '<h2 style="margin-bottom: 1.5rem;">📝 Today\\'s Recordings</h2>';

            for (const [category, items] of Object.entries(byCategory)) {
                html += `<div class="category">`;
                html += `<h2>${category.toUpperCase()} (${items.length})</h2>`;
                items.forEach(item => {
                    html += `<div class="recording">`;
                    html += `<span class="time">${item.created_at.substring(11, 16)}</span>`;
                    html += `${item.transcription}`;
                    html += `</div>`;
                });
                html += `</div>`;
            }

            if (recordings.length === 0) {
                html = '<p>No recordings today. <a href="/voice" style="color: #38ef7d;">Record your first voice memo!</a></p>';
            }

            categoriesEl.innerHTML = html;
        }

        async function generateSummary() {
            document.getElementById('summary').innerHTML = 'Generating AI summary...';

            const res = await fetch('/api/daily/summary');
            const data = await res.json();

            document.getElementById('summary').innerHTML = data.summary;
        }

        async function saveSummary() {
            const res = await fetch('/api/daily/save', { method: 'POST' });
            const data = await res.json();

            if (data.success) {
                alert('✅ Daily worklog saved!');
            } else {
                alert('❌ Error saving: ' + data.error);
            }
        }

        // Load on page load
        loadRecordings();
    </script>
</body>
</html>
    """

    return render_template_string(template, today=date.today().isoformat())


@daily_bp.route('/api/daily/recordings')
def api_daily_recordings():
    """Get today's recordings with categories"""
    recordings = get_todays_recordings()
    return jsonify(recordings)


@daily_bp.route('/api/daily/summary')
def api_daily_summary():
    """Generate AI summary of today"""
    summary = generate_daily_summary()
    return jsonify(summary)


@daily_bp.route('/api/daily/save', methods=['POST'])
def api_daily_save():
    """Save today's worklog"""
    try:
        worklog_id = save_daily_worklog()
        return jsonify({'success': True, 'id': worklog_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@daily_bp.route('/api/daily/<target_date>')
def api_daily_get(target_date):
    """Get worklog for specific date"""
    worklog = get_daily_worklog(target_date)

    if not worklog:
        return jsonify({'error': 'No worklog for this date'}), 404

    return jsonify(worklog)
