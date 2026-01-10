#!/usr/bin/env python3
"""
Traffic Blackhole - The Game

A mysterious traffic tracking system where visitors get lost in the void.
People see traffic going in but can't figure out where it ends.

The Game:
- Track every visitor
- Show mysterious haikus
- Cookies disappear
- Traffic visualization
- Leaderboard of lost souls
- No clear purpose (that's the point)
"""

from flask import Blueprint, request, jsonify, make_response, session
from database import get_db
import hashlib
import random
from datetime import datetime
from haiku_generator import (
    get_random_haiku,
    get_visitor_haiku,
    get_referrer_haiku,
    get_cookie_death_haiku
)

blackhole_bp = Blueprint('blackhole', __name__)

def generate_void_id():
    """Generate unique ID for void visitor"""
    timestamp = str(datetime.now().timestamp())
    random_salt = str(random.random())
    return hashlib.sha256(f"{timestamp}{random_salt}".encode()).hexdigest()[:12]

def track_visitor(request):
    """Track visitor in the void"""
    db = get_db()

    # Get visitor info
    referrer = request.referrer or 'direct'
    user_agent = request.headers.get('User-Agent', 'unknown')
    ip = request.remote_addr
    void_id = generate_void_id()

    # Count existing visitors
    visitor_count = db.execute('SELECT COUNT(*) as count FROM void_visitors').fetchone()
    visitor_num = visitor_count['count'] + 1 if visitor_count else 1

    # Store in database
    db.execute('''
        INSERT INTO void_visitors (void_id, visitor_num, referrer, user_agent, ip_hash, visited_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        void_id,
        visitor_num,
        referrer,
        user_agent,
        hashlib.sha256(ip.encode()).hexdigest()[:16],  # Hash IP for privacy
        datetime.now().isoformat()
    ))
    db.commit()

    return {
        'void_id': void_id,
        'visitor_num': visitor_num,
        'referrer': referrer
    }

def create_void_tables():
    """Create tables for void tracking"""
    db = get_db()

    db.execute('''
        CREATE TABLE IF NOT EXISTS void_visitors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            void_id TEXT UNIQUE,
            visitor_num INTEGER,
            referrer TEXT,
            user_agent TEXT,
            ip_hash TEXT,
            visited_at TIMESTAMP,
            escaped INTEGER DEFAULT 0
        )
    ''')

    db.execute('''
        CREATE TABLE IF NOT EXISTS cookie_graveyard (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cookie_name TEXT,
            cookie_value TEXT,
            died_at TIMESTAMP,
            void_id TEXT
        )
    ''')

    db.commit()

# Initialize tables
try:
    create_void_tables()
except:
    pass

@blackhole_bp.route('/void')
def void_entrance():
    """Main entrance to the void"""
    visitor_info = track_visitor(request)

    # Generate haiku
    haiku = get_visitor_haiku(visitor_info['visitor_num'])

    # Kill a random cookie (if any exist)
    cookies_to_kill = []
    for cookie_name in request.cookies:
        if random.random() < 0.3:  # 30% chance each cookie dies
            cookies_to_kill.append(cookie_name)

    # Store dead cookies
    db = get_db()
    for cookie_name in cookies_to_kill:
        cookie_value = request.cookies.get(cookie_name, '')
        db.execute('''
            INSERT INTO cookie_graveyard (cookie_name, cookie_value, died_at, void_id)
            VALUES (?, ?, ?, ?)
        ''', (cookie_name, cookie_value[:50], datetime.now().isoformat(), visitor_info['void_id']))
    db.commit()

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>The Void</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            background: #000;
            color: #0f0;
            font-family: 'Courier New', monospace;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 2rem;
            overflow: hidden;
        }}

        .void-container {{
            max-width: 800px;
            text-align: center;
            z-index: 10;
        }}

        h1 {{
            font-size: 4rem;
            margin-bottom: 2rem;
            text-shadow: 0 0 20px #0f0;
            animation: flicker 3s infinite;
        }}

        @keyframes flicker {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.8; }}
        }}

        .haiku {{
            font-size: 1.5rem;
            line-height: 2;
            margin: 3rem 0;
            white-space: pre-line;
            opacity: 0;
            animation: fadeIn 2s forwards;
        }}

        @keyframes fadeIn {{
            to {{ opacity: 1; }}
        }}

        .stats {{
            margin: 2rem 0;
            padding: 1.5rem;
            border: 2px solid #0f0;
            background: rgba(0, 255, 0, 0.05);
        }}

        .stat-row {{
            margin: 0.5rem 0;
            font-size: 1.2rem;
        }}

        .cookies-died {{
            color: #f00;
            margin: 2rem 0;
            font-size: 1.1rem;
        }}

        .matrix-rain {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 1;
            opacity: 0.3;
        }}

        .nav-links {{
            margin-top: 3rem;
        }}

        .nav-link {{
            color: #0f0;
            text-decoration: none;
            padding: 0.5rem 1rem;
            border: 1px solid #0f0;
            margin: 0.5rem;
            display: inline-block;
            transition: all 0.3s;
        }}

        .nav-link:hover {{
            background: #0f0;
            color: #000;
        }}
    </style>
</head>
<body>
    <canvas class="matrix-rain" id="matrix"></canvas>

    <div class="void-container">
        <h1>∞ THE VOID ∞</h1>

        <div class="haiku">{haiku}</div>

        <div class="stats">
            <div class="stat-row">📊 VOID ID: {visitor_info['void_id']}</div>
            <div class="stat-row">👤 LOST SOULS: {visitor_info['visitor_num']}</div>
            <div class="stat-row">🌐 ORIGIN: {visitor_info['referrer'][:50]}</div>
            <div class="stat-row">⏰ ENTRY TIME: {datetime.now().strftime('%H:%M:%S')}</div>
        </div>

        {f'<div class="cookies-died">🍪 {len(cookies_to_kill)} COOKIES DIED</div>' if cookies_to_kill else ''}

        <div class="nav-links">
            <a href="/cookie-graveyard.html" class="nav-link">🪦 Cookie Graveyard</a>
            <a href="/void-leaderboard" class="nav-link">🏆 Leaderboard</a>
            <a href="/" class="nav-link">🚪 Try to Escape</a>
        </div>
    </div>

    <script>
        // Matrix rain effect
        const canvas = document.getElementById('matrix');
        const ctx = canvas.getContext('2d');

        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;

        const chars = '01アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン';
        const fontSize = 14;
        const columns = canvas.width / fontSize;
        const drops = Array(Math.floor(columns)).fill(1);

        function draw() {{
            ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            ctx.fillStyle = '#0f0';
            ctx.font = fontSize + 'px monospace';

            for (let i = 0; i < drops.length; i++) {{
                const text = chars[Math.floor(Math.random() * chars.length)];
                ctx.fillText(text, i * fontSize, drops[i] * fontSize);

                if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) {{
                    drops[i] = 0;
                }}
                drops[i]++;
            }}
        }}

        setInterval(draw, 33);
    </script>
</body>
</html>
    """

    response = make_response(html)

    # Kill cookies in response
    for cookie_name in cookies_to_kill:
        response.set_cookie(cookie_name, '', expires=0)

    # Set void tracking cookie
    response.set_cookie('void_id', visitor_info['void_id'], max_age=60*60*24*365)  # 1 year

    return response


@blackhole_bp.route('/void-leaderboard')
def void_leaderboard():
    """Show leaderboard of lost souls"""
    db = get_db()

    # Get top visitors
    visitors = db.execute('''
        SELECT void_id, visitor_num, referrer, visited_at
        FROM void_visitors
        ORDER BY visitor_num DESC
        LIMIT 50
    ''').fetchall()

    total_visitors = db.execute('SELECT COUNT(*) as count FROM void_visitors').fetchone()['count']
    total_cookies_died = db.execute('SELECT COUNT(*) as count FROM cookie_graveyard').fetchone()['count']

    return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Void Leaderboard</title>
    <style>
        body {{
            background: #000;
            color: #0f0;
            font-family: 'Courier New', monospace;
            padding: 2rem;
        }}

        h1 {{
            text-align: center;
            font-size: 3rem;
            margin-bottom: 2rem;
            text-shadow: 0 0 20px #0f0;
        }}

        .stats-summary {{
            text-align: center;
            font-size: 1.5rem;
            margin: 2rem 0;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 2rem 0;
        }}

        th, td {{
            padding: 1rem;
            border: 1px solid #0f0;
            text-align: left;
        }}

        th {{
            background: rgba(0, 255, 0, 0.2);
        }}

        .back-link {{
            display: block;
            text-align: center;
            margin: 2rem 0;
            color: #0f0;
            text-decoration: none;
            font-size: 1.2rem;
        }}
    </style>
</head>
<body>
    <h1>🏆 LEADERBOARD OF THE LOST 🏆</h1>

    <div class="stats-summary">
        <div>Total Lost Souls: {total_visitors}</div>
        <div>Total Cookies Died: {total_cookies_died}</div>
    </div>

    <table>
        <tr>
            <th>Rank</th>
            <th>Void ID</th>
            <th>Origin</th>
            <th>Entry Time</th>
        </tr>
        {''.join([f'''
        <tr>
            <td>#{v['visitor_num']}</td>
            <td>{v['void_id']}</td>
            <td>{v['referrer'][:40]}</td>
            <td>{v['visited_at']}</td>
        </tr>
        ''' for v in visitors])}
    </table>

    <a href="/void" class="back-link">← Return to Void</a>
</body>
</html>
    """


@blackhole_bp.route('/api/void/stats')
def void_stats_api():
    """API endpoint for void stats"""
    db = get_db()

    total_visitors = db.execute('SELECT COUNT(*) as count FROM void_visitors').fetchone()['count']
    total_cookies = db.execute('SELECT COUNT(*) as count FROM cookie_graveyard').fetchone()['count']

    recent_visitors = db.execute('''
        SELECT void_id, visitor_num, referrer, visited_at
        FROM void_visitors
        ORDER BY visited_at DESC
        LIMIT 10
    ''').fetchall()

    return jsonify({
        'success': True,
        'total_visitors': total_visitors,
        'total_cookies_died': total_cookies,
        'recent_visitors': [dict(v) for v in recent_visitors],
        'haiku': get_random_haiku()
    })


@blackhole_bp.route('/api/cookie-graveyard')
def cookie_graveyard_api():
    """API endpoint for cookie graveyard"""
    db = get_db()

    total_cookies = db.execute('SELECT COUNT(*) as count FROM cookie_graveyard').fetchone()['count']

    dead_cookies = db.execute('''
        SELECT cookie_name, cookie_value, died_at, void_id
        FROM cookie_graveyard
        ORDER BY died_at DESC
        LIMIT 100
    ''').fetchall()

    return jsonify({
        'success': True,
        'total_cookies': total_cookies,
        'cookies': [dict(c) for c in dead_cookies],
        'haiku': get_cookie_death_haiku(total_cookies)
    })
