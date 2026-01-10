#!/usr/bin/env python3
"""
FRIEND INVITE LINK GENERATOR

Creates shareable invite landing pages for viral growth
- Each user gets personalized invite link: cringeproof.com/join/matt
- Landing page shows who invited them
- Simplified claim flow with referral tracking
- Auto-generates invite pages for all existing users

Usage:
    python3 generate_invite_links.py --username matt
    python3 generate_invite_links.py --all
    python3 generate_invite_links.py --user-id 1005
"""

import sqlite3
import argparse
from pathlib import Path
from datetime import datetime


# Configuration
DB_PATH = "soulfra.db"
VOICE_ARCHIVE_PATH = Path("/Users/matthewmauer/Desktop/voice-archive")


def get_user_info(user_id=None, username=None):
    """Get user information"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    if user_id:
        query = """
            SELECT u.id, u.email,
                   COALESCE(up.user_slug, SUBSTRING(u.email, 1, INSTR(u.email, '@') - 1)) as username,
                   COALESCE(up.readme_content, 'Voice-first creator') as bio
            FROM users u
            LEFT JOIN user_profiles up ON u.id = up.id
            WHERE u.id = ?
        """
        user = conn.execute(query, (user_id,)).fetchone()
    elif username:
        query = """
            SELECT u.id, u.email,
                   COALESCE(up.user_slug, SUBSTRING(u.email, 1, INSTR(u.email, '@') - 1)) as username,
                   COALESCE(up.readme_content, 'Voice-first creator') as bio
            FROM users u
            LEFT JOIN user_profiles up ON u.id = up.id
            WHERE up.user_slug = ? OR u.email LIKE ?
        """
        user = conn.execute(query, (username, f"{username}%")).fetchone()
    else:
        raise ValueError("Must provide user_id or username")

    conn.close()

    if not user:
        raise ValueError(f"User not found: {user_id or username}")

    return dict(user)


def count_user_recordings(user_id):
    """Count voice recordings for user"""
    conn = sqlite3.connect(DB_PATH)
    count = conn.execute(
        "SELECT COUNT(*) FROM simple_voice_recordings WHERE user_id = ? AND transcription IS NOT NULL",
        (user_id,)
    ).fetchone()[0]
    conn.close()
    return count


def generate_invite_page(user_info):
    """Generate invite landing page HTML"""

    username = user_info['username']
    bio = user_info['bio']
    recording_count = count_user_recordings(user_info['id'])

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Join {username} on CringeProof</title>
<meta name="description" content="{username} invited you to join CringeProof - Turn your voice into ideas, podcasts, and content">
<link rel="stylesheet" href="../css/soulfra.css">
<link rel="stylesheet" href="../css/cringeproof.css">
<style>
body {{
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    min-height: 100vh;
    padding: 2rem;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}}

.invite-container {{
    max-width: 700px;
    margin: 0 auto;
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    border-radius: 20px;
    padding: 3rem;
    border: 2px solid rgba(255, 255, 255, 0.2);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}}

.invite-header {{
    text-align: center;
    margin-bottom: 3rem;
}}

.invite-badge {{
    display: inline-block;
    background: rgba(255, 0, 110, 0.2);
    color: #ff006e;
    padding: 0.5rem 1rem;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 700;
    margin-bottom: 1rem;
    border: 2px solid #ff006e;
}}

.invite-header h1 {{
    font-size: 2.5rem;
    font-weight: 900;
    margin-bottom: 1rem;
    line-height: 1.2;
}}

.invite-header .subtitle {{
    font-size: 1.2rem;
    opacity: 0.9;
    margin-bottom: 2rem;
}}

.inviter-card {{
    background: rgba(0, 0, 0, 0.3);
    padding: 2rem;
    border-radius: 16px;
    margin-bottom: 2rem;
    border: 2px solid rgba(255, 255, 255, 0.1);
}}

.inviter-info {{
    display: flex;
    align-items: center;
    gap: 1.5rem;
    margin-bottom: 1rem;
}}

.inviter-avatar {{
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background: linear-gradient(135deg, #ff006e 0%, #764ba2 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
    font-weight: 900;
    border: 3px solid white;
}}

.inviter-details {{
    flex: 1;
}}

.inviter-name {{
    font-size: 1.3rem;
    font-weight: 900;
    margin-bottom: 0.25rem;
}}

.inviter-stats {{
    font-size: 0.9rem;
    opacity: 0.7;
}}

.inviter-bio {{
    margin-top: 1rem;
    font-size: 0.95rem;
    line-height: 1.6;
    opacity: 0.9;
}}

.features {{
    margin: 2rem 0;
}}

.feature {{
    background: rgba(0, 0, 0, 0.2);
    padding: 1.5rem;
    border-radius: 12px;
    margin-bottom: 1rem;
    border-left: 4px solid #00ff88;
}}

.feature h3 {{
    font-size: 1.1rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}}

.feature p {{
    opacity: 0.8;
    font-size: 0.95rem;
    line-height: 1.5;
}}

.cta-section {{
    text-align: center;
    margin-top: 3rem;
}}

.btn-claim {{
    display: inline-block;
    background: #ff006e;
    color: white;
    padding: 1.25rem 3rem;
    border-radius: 12px;
    text-decoration: none;
    font-weight: 900;
    font-size: 1.2rem;
    border: 3px solid #000;
    box-shadow: 5px 5px 0 #000;
    transition: all 0.1s;
    margin-bottom: 1rem;
}}

.btn-claim:hover {{
    transform: translate(-2px, -2px);
    box-shadow: 7px 7px 0 #000;
}}

.btn-claim:active {{
    transform: translate(0, 0);
    box-shadow: 3px 3px 0 #000;
}}

.cta-note {{
    margin-top: 1rem;
    font-size: 0.85rem;
    opacity: 0.7;
}}

.trust-badge {{
    text-align: center;
    margin-top: 2rem;
    padding-top: 2rem;
    border-top: 1px solid rgba(255, 255, 255, 0.2);
}}

.trust-badge p {{
    font-size: 0.85rem;
    opacity: 0.6;
}}

@media (max-width: 768px) {{
    .invite-container {{
        padding: 2rem 1.5rem;
    }}

    .invite-header h1 {{
        font-size: 2rem;
    }}

    .inviter-info {{
        flex-direction: column;
        text-align: center;
    }}
}}
</style>
</head>
<body>

<div class="invite-container">
    <div class="invite-header">
        <div class="invite-badge">🎤 PERSONAL INVITE</div>
        <h1>{username} invited you to CringeProof</h1>
        <p class="subtitle">Turn your voice into ideas, podcasts, and content in seconds</p>
    </div>

    <div class="inviter-card">
        <div class="inviter-info">
            <div class="inviter-avatar">{username[0].upper()}</div>
            <div class="inviter-details">
                <div class="inviter-name">{username}</div>
                <div class="inviter-stats">📊 {recording_count} voice ideas published</div>
            </div>
        </div>
        <div class="inviter-bio">"{bio[:200]}{'...' if len(bio) > 200 else ''}"</div>
    </div>

    <div class="features">
        <div class="feature">
            <h3>🎙️ Voice → Ideas</h3>
            <p>Record any idea, thought, or braindump. AI automatically transcribes and enhances it.</p>
        </div>

        <div class="feature">
            <h3>📻 Auto Podcasts</h3>
            <p>Long recordings turn into podcast episodes with chapters, timestamps, and RSS feeds.</p>
        </div>

        <div class="feature">
            <h3>🚀 Your Own Domain</h3>
            <p>Get your personal page: {username.lower()}.soulfra.com with your own invite link to share.</p>
        </div>

        <div class="feature">
            <h3>🚫 Zero Cringe</h3>
            <p>Private by default. Publish when ready. No algorithms, no performative BS.</p>
        </div>
    </div>

    <div class="cta-section">
        <a href="../claim.html?ref={username}" class="btn-claim">
            Claim Your Username
        </a>
        <p class="cta-note">Free forever. Takes 30 seconds.</p>
    </div>

    <div class="trust-badge">
        <p>✨ Invited by {username} • Powered by open source • All data stays yours</p>
    </div>
</div>

</body>
</html>"""

    return html_content


def export_invite_page(username, html_content):
    """Export invite page to GitHub Pages directory"""

    join_dir = VOICE_ARCHIVE_PATH / "join"
    join_dir.mkdir(exist_ok=True)

    page_path = join_dir / f"{username}.html"

    with open(page_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"📄 Invite page created: {page_path}")
    print(f"   🔗 Shareable link: https://cringeproof.com/join/{username}")

    return page_path


def main():
    parser = argparse.ArgumentParser(description="Friend Invite Link Generator")
    parser.add_argument("--user-id", type=int, help="User ID to generate invite for")
    parser.add_argument("--username", help="Username to generate invite for")
    parser.add_argument("--all", action="store_true", help="Generate invites for all users")

    args = parser.parse_args()

    if not args.user_id and not args.username and not args.all:
        parser.error("Must specify --user-id, --username, or --all")

    print("\n🔗 FRIEND INVITE LINK GENERATOR")
    print("=" * 60)

    if args.all:
        # Generate for all users
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row

        users = conn.execute("""
            SELECT DISTINCT u.id
            FROM users u
            LEFT JOIN user_profiles up ON u.id = up.id
        """).fetchall()

        conn.close()

        print(f"📋 Generating invite pages for {len(users)} users...\n")

        for user in users:
            try:
                user_info = get_user_info(user_id=user['id'])
                html_content = generate_invite_page(user_info)
                export_invite_page(user_info['username'], html_content)
            except Exception as e:
                print(f"❌ Error generating invite for user {user['id']}: {e}")

        print(f"\n✅ Generated {len(users)} invite pages")

    else:
        # Generate for single user
        user_info = get_user_info(user_id=args.user_id, username=args.username)

        print(f"👤 User: {user_info['username']} (ID: {user_info['id']})")
        print(f"📊 Recordings: {count_user_recordings(user_info['id'])}")

        html_content = generate_invite_page(user_info)
        page_path = export_invite_page(user_info['username'], html_content)

        print(f"\n🎉 SUCCESS!")
        print(f"   Share this link with friends:")
        print(f"   📱 https://cringeproof.com/join/{user_info['username']}")
        print(f"\n   Or copy the HTML:")
        print(f"   📂 {page_path}")


if __name__ == "__main__":
    main()
