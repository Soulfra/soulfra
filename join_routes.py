"""
Referral-based waitlist signup routes (no GitHub required)
Allows viral growth through referral codes
"""

from flask import Blueprint, request, jsonify, render_template_string
import sqlite3
import secrets
import re
from datetime import datetime

join_bp = Blueprint('join', __name__)

DB_PATH = 'soulfra.db'
AVAILABLE_DOMAINS = ['soulfra', 'calriven', 'deathtodata', 'cringeproof']
LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def generate_referral_code():
    """Generate unique 8-character referral code"""
    return secrets.token_hex(4).upper()

def get_next_available_letter(domain_name):
    """Find next available letter for domain"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT letter_code FROM waitlist
        WHERE domain_name = ?
    ''', (domain_name,))

    used_letters = [row['letter_code'] for row in cursor.fetchall()]
    conn.close()

    for letter in LETTERS:
        if letter not in used_letters:
            return letter

    return None  # All letters taken

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

@join_bp.route('/join', methods=['GET'])
def join_form():
    """Show signup form (no referral code)"""
    referral_code = request.args.get('ref', '')

    html = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Join the Waitlist - Soulfra Domains</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #fff;
                min-height: 100vh;
                padding: 20px;
                display: flex;
                align-items: center;
                justify-content: center;
            }

            .container {
                max-width: 500px;
                width: 100%;
            }

            .card {
                background: rgba(255,255,255,0.15);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.3);
                border: 2px solid rgba(255,255,255,0.2);
            }

            h1 {
                font-size: 2.5em;
                margin-bottom: 10px;
                text-align: center;
            }

            .tagline {
                text-align: center;
                opacity: 0.9;
                margin-bottom: 30px;
            }

            .form-group {
                margin-bottom: 20px;
            }

            label {
                display: block;
                margin-bottom: 8px;
                font-weight: 500;
            }

            input[type="email"], select, textarea {
                width: 100%;
                padding: 12px;
                border-radius: 8px;
                border: 2px solid rgba(255,255,255,0.3);
                background: rgba(255,255,255,0.1);
                color: #fff;
                font-size: 16px;
            }

            input::placeholder, textarea::placeholder {
                color: rgba(255,255,255,0.6);
            }

            textarea {
                min-height: 80px;
                resize: vertical;
            }

            button {
                width: 100%;
                padding: 15px;
                background: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 18px;
                font-weight: bold;
                cursor: pointer;
                transition: background 0.3s;
            }

            button:hover {
                background: #45a049;
            }

            button:disabled {
                background: #ccc;
                cursor: not-allowed;
            }

            .alert {
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 20px;
                display: none;
            }

            .alert.success {
                background: rgba(76, 175, 80, 0.3);
                border: 2px solid #4CAF50;
                display: block;
            }

            .alert.error {
                background: rgba(244, 67, 54, 0.3);
                border: 2px solid #f44336;
                display: block;
            }

            .referral-info {
                background: rgba(255, 215, 0, 0.2);
                border: 2px solid #ffd700;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 20px;
            }

            .letter-info {
                background: rgba(255,255,255,0.1);
                padding: 10px;
                border-radius: 8px;
                margin-top: 10px;
                font-size: 0.9em;
            }

            .footer {
                text-align: center;
                margin-top: 30px;
                opacity: 0.8;
                font-size: 0.9em;
            }

            .footer a {
                color: #ffd700;
                text-decoration: none;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="card">
                <h1>🚀 Join Waitlist</h1>
                <p class="tagline">Get your letter. Accelerate the launch. Be first.</p>

                <div id="alertBox" class="alert"></div>

                ''' + (f'''
                <div class="referral-info">
                    ✨ <strong>Referred by a friend!</strong><br>
                    Code: <code>{referral_code}</code>
                </div>
                ''' if referral_code else '') + '''

                <form id="joinForm">
                    <div class="form-group">
                        <label for="email">Email *</label>
                        <input type="email" id="email" name="email"
                               placeholder="you@example.com" required>
                    </div>

                    <div class="form-group">
                        <label for="domain">Preferred Domain *</label>
                        <select id="domain" name="domain" required>
                            <option value="">Choose a domain...</option>
                            <option value="calriven">calriven (4 signups)</option>
                            <option value="deathtodata">deathtodata (3 signups)</option>
                            <option value="soulfra">soulfra (2 signups)</option>
                            <option value="cringeproof">cringeproof (1 signup)</option>
                        </select>
                        <div class="letter-info">
                            📝 You'll get your letter automatically (A-Z, first-come)
                        </div>
                    </div>

                    <div class="form-group">
                        <label for="reason">Why do you want to join? (optional)</label>
                        <textarea id="reason" name="reason"
                                  placeholder="Tell us what you'll use your subdomain for..."></textarea>
                    </div>

                    <input type="hidden" id="referral_code" name="referral_code" value="''' + referral_code + '''">

                    <button type="submit" id="submitBtn">Join Waitlist</button>
                </form>

                <div class="footer">
                    <p>Every 10 signups = -1 day until launch</p>
                    <p>900+ signups = Instant Launch 🚀</p>
                    <p style="margin-top: 15px;">
                        <a href="https://soulfra.github.io/waitlist">View Leaderboard</a>
                    </p>
                </div>
            </div>
        </div>

        <script>
            document.getElementById('joinForm').addEventListener('submit', async (e) => {
                e.preventDefault();

                const btn = document.getElementById('submitBtn');
                const alertBox = document.getElementById('alertBox');

                btn.disabled = true;
                btn.textContent = 'Joining...';

                const formData = new FormData(e.target);
                const data = {
                    email: formData.get('email'),
                    domain_name: formData.get('domain'),
                    reason: formData.get('reason'),
                    referral_code: formData.get('referral_code') || null
                };

                try {
                    const response = await fetch('/api/join', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(data)
                    });

                    const result = await response.json();

                    if (response.ok) {
                        alertBox.className = 'alert success';
                        alertBox.innerHTML = `
                            <strong>✅ Welcome to the waitlist!</strong><br>
                            Your letter: <strong>${result.letter}</strong> on <strong>${result.domain_name}</strong><br>
                            Launch date: <strong>${result.launch_date}</strong><br>
                            <br>
                            <strong>Share your referral code:</strong><br>
                            <code style="font-size: 1.2em; background: rgba(255,255,255,0.2); padding: 5px 10px; border-radius: 5px;">
                                ${result.your_referral_code}
                            </code><br>
                            <br>
                            <a href="/join?ref=${result.your_referral_code}" style="color: #ffd700;">
                                https://soulfra.ai/join?ref=${result.your_referral_code}
                            </a>
                        `;
                        e.target.reset();
                    } else {
                        alertBox.className = 'alert error';
                        alertBox.textContent = '❌ ' + (result.error || 'Something went wrong');
                    }
                } catch (error) {
                    alertBox.className = 'alert error';
                    alertBox.textContent = '❌ Network error. Please try again.';
                }

                btn.disabled = false;
                btn.textContent = 'Join Waitlist';
            });
        </script>
    </body>
    </html>
    '''

    return html

@join_bp.route('/api/join', methods=['POST'])
def api_join():
    """Process signup (with optional referral tracking)"""
    data = request.get_json()

    email = data.get('email', '').strip().lower()
    domain_name = data.get('domain_name', '').strip()
    reason = data.get('reason', '').strip()
    referral_code = data.get('referral_code', '').strip() or None

    # Validate inputs
    if not email or not validate_email(email):
        return jsonify({'error': 'Valid email required'}), 400

    if domain_name not in AVAILABLE_DOMAINS:
        return jsonify({'error': 'Invalid domain'}), 400

    conn = get_db()
    cursor = conn.cursor()

    try:
        # Check if email already signed up for this domain
        cursor.execute('''
            SELECT id FROM waitlist
            WHERE email = ? AND domain_name = ?
        ''', (email, domain_name))

        if cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Email already registered for this domain'}), 400

        # Get next available letter
        letter = get_next_available_letter(domain_name)
        if not letter:
            conn.close()
            return jsonify({'error': 'All letters taken for this domain'}), 400

        # Validate referral code if provided
        referred_by = None
        if referral_code:
            cursor.execute('''
                SELECT id FROM waitlist WHERE referral_code = ?
            ''', (referral_code,))
            referrer = cursor.fetchone()
            if referrer:
                referred_by = referral_code

        # Generate unique referral code for new user
        your_referral_code = generate_referral_code()
        while True:
            cursor.execute('SELECT id FROM waitlist WHERE referral_code = ?',
                          (your_referral_code,))
            if not cursor.fetchone():
                break
            your_referral_code = generate_referral_code()

        # Insert into waitlist
        cursor.execute('''
            INSERT INTO waitlist (email, domain_name, letter_code, referral_code, referred_by)
            VALUES (?, ?, ?, ?, ?)
        ''', (email, domain_name, letter, your_referral_code, referred_by))

        conn.commit()

        # Get launch date
        cursor.execute('''
            SELECT launch_date FROM domain_launches
            WHERE domain_name = ?
        ''', (domain_name,))

        launch_row = cursor.fetchone()
        launch_date = launch_row['launch_date'] if launch_row else '90 days'

        conn.close()

        return jsonify({
            'success': True,
            'email': email,
            'domain_name': domain_name,
            'letter': letter,
            'your_referral_code': your_referral_code,
            'launch_date': launch_date,
            'message': f'Welcome! Your letter is {letter}'
        }), 201

    except Exception as e:
        conn.close()
        print(f'❌ Signup error: {e}')
        return jsonify({'error': 'Database error'}), 500

@join_bp.route('/api/referral-stats/<code>', methods=['GET'])
def referral_stats(code):
    """Get referral statistics for a code"""
    conn = get_db()
    cursor = conn.cursor()

    # Get referrer info
    cursor.execute('''
        SELECT email, domain_name, letter_code, signup_at
        FROM waitlist WHERE referral_code = ?
    ''', (code,))

    referrer = cursor.fetchone()
    if not referrer:
        conn.close()
        return jsonify({'error': 'Referral code not found'}), 404

    # Count referrals
    cursor.execute('''
        SELECT COUNT(*) as count FROM waitlist
        WHERE referred_by = ?
    ''', (code,))

    referral_count = cursor.fetchone()['count']

    conn.close()

    return jsonify({
        'referral_code': code,
        'domain': referrer['domain_name'],
        'letter': referrer['letter_code'],
        'total_referrals': referral_count,
        'signup_date': referrer['signup_at']
    })
