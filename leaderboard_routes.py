"""
Leaderboard Routes - Reputation tracking and device rankings

Routes:
- GET /api/leaderboard - Get top users/devices by reputation
- GET /api/leaderboard/user/<user_id> - Get specific user's rank
- POST /api/reputation/earn - Award reputation points
- GET /leaderboard.html - Leaderboard display page

Usage in app.py:
    from leaderboard_routes import register_leaderboard_routes
    register_leaderboard_routes(app)
"""

from flask import jsonify, request, render_template_string
from database import get_db
from datetime import datetime


def register_leaderboard_routes(app):
    """Register leaderboard routes with Flask app"""

    @app.route('/api/leaderboard')
    def api_leaderboard():
        """
        Get leaderboard rankings

        Query params:
        - limit: Max entries (default 100)
        - type: 'devices' or 'users' (default 'users')

        Returns:
        {
            "success": true,
            "leaderboard": [
                {
                    "rank": 1,
                    "username": "alice",
                    "bits_earned": 500,
                    "bits_spent": 100,
                    "net_bits": 400,
                    "contribution_count": 25
                }
            ]
        }
        """
        limit = request.args.get('limit', 100, type=int)
        lb_type = request.args.get('type', 'users')

        db = get_db()
        db.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))

        if lb_type == 'devices':
            # Device leaderboard
            cursor = db.execute('''
                SELECT
                    d.device_id,
                    d.device_type,
                    d.created_at,
                    COALESCE(r.bits_earned, 0) as bits_earned,
                    COALESCE(r.bits_spent, 0) as bits_spent,
                    COALESCE(r.bits_earned - r.bits_spent, 0) as net_bits,
                    COALESCE(r.contribution_count, 0) as contribution_count,
                    u.username
                FROM devices d
                LEFT JOIN reputation r ON r.user_id = d.user_id
                LEFT JOIN users u ON u.id = d.user_id
                ORDER BY net_bits DESC
                LIMIT ?
            ''', (limit,))
        else:
            # User leaderboard
            cursor = db.execute('''
                SELECT
                    u.id,
                    u.username,
                    u.display_name,
                    u.created_at,
                    COALESCE(r.bits_earned, 0) as bits_earned,
                    COALESCE(r.bits_spent, 0) as bits_spent,
                    COALESCE(r.bits_earned - r.bits_spent, 0) as net_bits,
                    COALESCE(r.contribution_count, 0) as contribution_count
                FROM users u
                LEFT JOIN reputation r ON r.user_id = u.id
                WHERE u.is_ai_persona = 0
                ORDER BY net_bits DESC
                LIMIT ?
            ''', (limit,))

        results = cursor.fetchall()

        # Add rank
        leaderboard = []
        for i, entry in enumerate(results):
            entry['rank'] = i + 1
            leaderboard.append(entry)

        return jsonify({
            'success': True,
            'leaderboard': leaderboard,
            'count': len(leaderboard)
        })

    @app.route('/api/leaderboard/user/<int:user_id>')
    def api_user_rank(user_id):
        """
        Get specific user's leaderboard rank

        Returns:
        {
            "success": true,
            "user_id": 42,
            "username": "alice",
            "rank": 5,
            "bits_earned": 300,
            "bits_spent": 50,
            "net_bits": 250,
            "can_unlock_email": true
        }
        """
        db = get_db()
        db.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))

        # Get user reputation
        cursor = db.execute('''
            SELECT
                u.id,
                u.username,
                u.display_name,
                u.email,
                COALESCE(r.bits_earned, 0) as bits_earned,
                COALESCE(r.bits_spent, 0) as bits_spent,
                COALESCE(r.bits_earned - r.bits_spent, 0) as net_bits,
                COALESCE(r.contribution_count, 0) as contribution_count
            FROM users u
            LEFT JOIN reputation r ON r.user_id = u.id
            WHERE u.id = ?
        ''', (user_id,))

        user = cursor.fetchone()

        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404

        # Get rank (count users with higher net_bits)
        cursor = db.execute('''
            SELECT COUNT(*) + 1 as rank
            FROM users u
            LEFT JOIN reputation r ON r.user_id = u.id
            WHERE (COALESCE(r.bits_earned, 0) - COALESCE(r.bits_spent, 0)) >
                  (SELECT COALESCE(bits_earned, 0) - COALESCE(bits_spent, 0)
                   FROM reputation WHERE user_id = ?)
              AND u.is_ai_persona = 0
        ''', (user_id,))

        rank = cursor.fetchone()['rank']

        # Check if can unlock email (threshold: 100 bits)
        EMAIL_UNLOCK_THRESHOLD = 100
        can_unlock_email = user['net_bits'] >= EMAIL_UNLOCK_THRESHOLD

        return jsonify({
            'success': True,
            'user_id': user['id'],
            'username': user['username'],
            'rank': rank,
            'bits_earned': user['bits_earned'],
            'bits_spent': user['bits_spent'],
            'net_bits': user['net_bits'],
            'contribution_count': user['contribution_count'],
            'can_unlock_email': can_unlock_email,
            'email_unlock_threshold': EMAIL_UNLOCK_THRESHOLD
        })

    @app.route('/api/reputation/earn', methods=['POST'])
    def api_earn_reputation():
        """
        Award reputation points to user

        POST body:
        {
            "user_id": 42,
            "bits": 10,
            "reason": "recorded_voice_memo"
        }

        Returns:
        {
            "success": true,
            "new_total": 110
        }
        """
        data = request.json

        user_id = data.get('user_id')
        bits = data.get('bits', 0)
        reason = data.get('reason', 'manual_award')

        if not user_id or bits <= 0:
            return jsonify({
                'success': False,
                'error': 'user_id and bits (>0) required'
            }), 400

        db = get_db()

        # Check if user has reputation record
        cursor = db.execute('''
            SELECT * FROM reputation WHERE user_id = ?
        ''', (user_id,))

        existing = cursor.fetchone()

        if existing:
            # Update existing
            db.execute('''
                UPDATE reputation
                SET bits_earned = bits_earned + ?,
                    contribution_count = contribution_count + 1
                WHERE user_id = ?
            ''', (bits, user_id))
        else:
            # Create new
            db.execute('''
                INSERT INTO reputation (user_id, bits_earned, contribution_count)
                VALUES (?, ?, 1)
            ''', (user_id, bits))

        db.commit()

        # Get new total
        cursor = db.execute('''
            SELECT bits_earned - bits_spent as net_bits
            FROM reputation WHERE user_id = ?
        ''', (user_id,))

        new_total = cursor.fetchone()[0]

        return jsonify({
            'success': True,
            'new_total': new_total,
            'reason': reason
        })

    @app.route('/leaderboard.html')
    def leaderboard_page():
        """Display leaderboard page"""
        return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Leaderboard - CringeProof</title>
    <link rel="stylesheet" href="/css/soulfra.css">
    <style>
        .leaderboard-container {
            max-width: 800px;
            margin: 2rem auto;
            padding: 2rem;
        }
        .leaderboard-entry {
            background: #fff;
            border: 4px solid #000;
            padding: 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 8px 8px 0 #bdb2ff;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .rank {
            font-size: 2rem;
            font-weight: 900;
            color: #ff006e;
            min-width: 60px;
        }
        .user-info {
            flex-grow: 1;
            margin: 0 1rem;
        }
        .username {
            font-weight: 900;
            font-size: 1.2rem;
        }
        .stats {
            color: #666;
            font-size: 0.9rem;
        }
        .bits {
            font-size: 1.5rem;
            font-weight: 900;
            color: #00C49A;
        }
    </style>
</head>
<body>
    <nav class="soulfra-nav">
        <div class="soulfra-nav-container">
            <a href="/" class="soulfra-logo">🚫 CringeProof</a>
            <div class="soulfra-links">
                <a href="/ideas/">💡 Ideas</a>
                <a href="/">🎤 Archive</a>
                <a href="/record.html">🎙️ Record</a>
                <a href="/leaderboard.html" class="active">🏆 Leaderboard</a>
                <a href="/login.html">🔐 Login</a>
            </div>
        </div>
    </nav>

    <div class="container">
        <header style="text-align: center; margin-bottom: 3rem;">
            <h1>🏆 Leaderboard</h1>
            <p class="subtitle">Top contributors by reputation</p>
            <p style="color: #666; margin-top: 1rem;">
                Earn 100 bits to unlock email registration!
            </p>
        </header>

        <div class="leaderboard-container" id="leaderboard">
            <p style="text-align: center;">Loading...</p>
        </div>
    </div>

    <script>
        async function loadLeaderboard() {
            try {
                const response = await fetch('/api/leaderboard?limit=50');
                const data = await response.json();

                if (data.success) {
                    displayLeaderboard(data.leaderboard);
                }
            } catch (error) {
                console.error('Failed to load leaderboard:', error);
                document.getElementById('leaderboard').innerHTML =
                    '<p style="text-align: center; color: #ff006e;">Failed to load leaderboard</p>';
            }
        }

        function displayLeaderboard(entries) {
            const container = document.getElementById('leaderboard');

            if (entries.length === 0) {
                container.innerHTML = '<p style="text-align: center;">No entries yet. Be the first!</p>';
                return;
            }

            container.innerHTML = entries.map(entry => `
                <div class="leaderboard-entry">
                    <div class="rank">#${entry.rank}</div>
                    <div class="user-info">
                        <div class="username">${entry.username || entry.device_id}</div>
                        <div class="stats">
                            ${entry.contribution_count} contributions •
                            Earned: ${entry.bits_earned} •
                            Spent: ${entry.bits_spent}
                        </div>
                    </div>
                    <div class="bits">${entry.net_bits} bits</div>
                </div>
            `).join('');
        }

        // Load on page load
        loadLeaderboard();

        // Refresh every 30 seconds
        setInterval(loadLeaderboard, 30000);
    </script>
</body>
</html>
        ''')

    print("✅ Leaderboard routes registered:")
    print("   - GET /api/leaderboard (Get rankings)")
    print("   - GET /api/leaderboard/user/<id> (Get user rank)")
    print("   - POST /api/reputation/earn (Award reputation)")
    print("   - GET /leaderboard.html (Display page)")
