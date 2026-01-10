#!/usr/bin/env python3
"""
USER PROFILE PAGE GENERATOR

Creates personalized profile pages for each user
- Profile page at /u/{username}.html
- Shows voice recordings, podcasts, bio
- Includes RSS feed link, invite link, stats
- Auto-generates for all users with content

Usage:
    python3 generate_user_profiles.py --username matt
    python3 generate_user_profiles.py --all
    python3 generate_user_profiles.py --user-id 1005
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
            SELECT u.id, u.email, u.created_at,
                   COALESCE(up.user_slug, SUBSTRING(u.email, 1, INSTR(u.email, '@') - 1)) as username,
                   COALESCE(up.readme_content, 'Voice-first creator exploring ideas through audio.') as bio,
                   up.github_username,
                   up.projects_want_to_build
            FROM users u
            LEFT JOIN user_profiles up ON u.id = up.id
            WHERE u.id = ?
        """
        user = conn.execute(query, (user_id,)).fetchone()
    elif username:
        query = """
            SELECT u.id, u.email, u.created_at,
                   COALESCE(up.user_slug, SUBSTRING(u.email, 1, INSTR(u.email, '@') - 1)) as username,
                   COALESCE(up.readme_content, 'Voice-first creator exploring ideas through audio.') as bio,
                   up.github_username,
                   up.projects_want_to_build
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


def get_user_recordings(user_id):
    """Get user's voice recordings"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    recordings = conn.execute("""
        SELECT id, filename, transcription, created_at
        FROM simple_voice_recordings
        WHERE user_id = ? AND transcription IS NOT NULL
        ORDER BY created_at DESC
        LIMIT 20
    """, (user_id,)).fetchall()

    conn.close()

    return [dict(rec) for rec in recordings]


def get_user_podcasts(user_id):
    """Get user's podcast episodes"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    podcasts = conn.execute("""
        SELECT id, title, description, created_at, duration_seconds
        FROM voice_podcast_episodes
        WHERE user_id = ? AND published = 1
        ORDER BY created_at DESC
        LIMIT 10
    """, (user_id,)).fetchall()

    conn.close()

    return [dict(pod) for pod in podcasts]


def get_user_stats(user_id):
    """Get user statistics"""
    conn = sqlite3.connect(DB_PATH)

    voice_count = conn.execute(
        "SELECT COUNT(*) FROM simple_voice_recordings WHERE user_id = ? AND transcription IS NOT NULL",
        (user_id,)
    ).fetchone()[0]

    podcast_count = conn.execute(
        "SELECT COUNT(*) FROM voice_podcast_episodes WHERE user_id = ? AND published = 1",
        (user_id,)
    ).fetchone()[0]

    conn.close()

    return {
        'voice_count': voice_count,
        'podcast_count': podcast_count
    }


def generate_profile_page(user_info, recordings, podcasts, stats):
    """Generate user profile page HTML"""

    username = user_info['username']
    bio = user_info['bio']
    github = user_info.get('github_username', '')
    projects = user_info.get('projects_want_to_build', '')

    # Format join date
    try:
        join_date = datetime.fromisoformat(user_info['created_at']).strftime('%B %Y')
    except:
        join_date = "Recently"

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{username} - CringeProof</title>
<meta name="description" content="{bio[:160]}">
<link rel="stylesheet" href="../css/soulfra.css">
<link rel="stylesheet" href="../css/cringeproof.css">
<style>
body {{
    background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
    color: white;
    min-height: 100vh;
    padding-bottom: 3rem;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}}

.profile-header {{
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 3rem 1rem 4rem 1rem;
    text-align: center;
    position: relative;
}}

.profile-avatar {{
    width: 120px;
    height: 120px;
    border-radius: 50%;
    background: linear-gradient(135deg, #ff006e 0%, #764ba2 100%);
    margin: 0 auto 1rem auto;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 3rem;
    font-weight: 900;
    border: 5px solid white;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}}

.profile-username {{
    font-size: 2.5rem;
    font-weight: 900;
    margin-bottom: 0.5rem;
}}

.profile-bio {{
    font-size: 1.1rem;
    max-width: 600px;
    margin: 0 auto 1.5rem auto;
    opacity: 0.9;
    line-height: 1.6;
}}

.profile-meta {{
    display: flex;
    justify-content: center;
    gap: 2rem;
    flex-wrap: wrap;
    font-size: 0.9rem;
    opacity: 0.8;
}}

.profile-stats {{
    display: flex;
    justify-content: center;
    gap: 3rem;
    margin-top: 2rem;
    flex-wrap: wrap;
}}

.stat {{
    text-align: center;
}}

.stat-value {{
    font-size: 2rem;
    font-weight: 900;
    display: block;
}}

.stat-label {{
    font-size: 0.85rem;
    opacity: 0.7;
    text-transform: uppercase;
    letter-spacing: 1px;
}}

.profile-actions {{
    display: flex;
    justify-content: center;
    gap: 1rem;
    margin-top: 2rem;
    flex-wrap: wrap;
}}

.btn {{
    display: inline-block;
    padding: 0.75rem 1.5rem;
    border-radius: 8px;
    text-decoration: none;
    font-weight: 700;
    border: 2px solid #000;
    box-shadow: 3px 3px 0 #000;
    transition: all 0.1s;
    font-size: 0.9rem;
}}

.btn-primary {{
    background: #ff006e;
    color: white;
}}

.btn-secondary {{
    background: rgba(255, 255, 255, 0.1);
    color: white;
}}

.btn:hover {{
    transform: translate(-2px, -2px);
    box-shadow: 5px 5px 0 #000;
}}

.content-container {{
    max-width: 900px;
    margin: -2rem auto 0 auto;
    padding: 0 1rem;
}}

.content-card {{
    background: rgba(255, 255, 255, 0.05);
    border-radius: 16px;
    padding: 2rem;
    margin-bottom: 2rem;
    border: 2px solid rgba(255, 255, 255, 0.1);
}}

.content-card h2 {{
    font-size: 1.5rem;
    font-weight: 900;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}}

.recording-item {{
    background: rgba(0, 0, 0, 0.3);
    padding: 1.5rem;
    border-radius: 12px;
    margin-bottom: 1rem;
    border-left: 4px solid #ff006e;
}}

.recording-header {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0.75rem;
}}

.recording-title {{
    font-weight: 700;
    font-size: 1rem;
}}

.recording-date {{
    font-size: 0.85rem;
    opacity: 0.6;
}}

.recording-transcript {{
    font-size: 0.95rem;
    line-height: 1.6;
    opacity: 0.9;
}}

.podcast-item {{
    background: rgba(0, 0, 0, 0.3);
    padding: 1.5rem;
    border-radius: 12px;
    margin-bottom: 1rem;
    border-left: 4px solid #00ff88;
}}

.podcast-title {{
    font-weight: 700;
    font-size: 1.1rem;
    margin-bottom: 0.5rem;
}}

.podcast-description {{
    font-size: 0.9rem;
    opacity: 0.8;
    line-height: 1.5;
    margin-bottom: 0.75rem;
}}

.podcast-meta {{
    display: flex;
    gap: 1rem;
    font-size: 0.85rem;
    opacity: 0.6;
}}

.empty-state {{
    text-align: center;
    padding: 3rem 1rem;
    opacity: 0.6;
}}

.projects-list {{
    line-height: 1.8;
    opacity: 0.9;
}}

@media (max-width: 768px) {{
    .profile-username {{
        font-size: 2rem;
    }}

    .profile-stats {{
        gap: 2rem;
    }}

    .content-card {{
        padding: 1.5rem;
    }}
}}
</style>
</head>
<body>

<!-- Navigation -->
<nav class="soulfra-nav">
    <div class="soulfra-nav-container">
        <a href="../index.html" class="soulfra-logo">🚫 CringeProof</a>
        <div class="soulfra-links">
            <a href="../wall.html">The Wall</a>
            <a href="../voice-recorder.html">🎤 Record</a>
        </div>
    </div>
</nav>

<!-- Profile Header -->
<div class="profile-header">
    <div class="profile-avatar">{username[0].upper()}</div>
    <h1 class="profile-username">{username}</h1>
    <p class="profile-bio">{bio}</p>

    <div class="profile-meta">
        <span>📅 Joined {join_date}</span>
        {f'<span>💻 <a href="https://github.com/{github}" style="color: white; text-decoration: underline;">{github}</a></span>' if github else ''}
    </div>

    <div class="profile-stats">
        <div class="stat">
            <span class="stat-value">{stats['voice_count']}</span>
            <span class="stat-label">Voice Ideas</span>
        </div>
        <div class="stat">
            <span class="stat-value">{stats['podcast_count']}</span>
            <span class="stat-label">Podcasts</span>
        </div>
    </div>

    <div class="profile-actions">
        <a href="../feeds/{username}.xml" class="btn btn-primary">
            📻 Subscribe RSS
        </a>
        <a href="../join/{username}.html" class="btn btn-secondary">
            🔗 Invite Friends
        </a>
    </div>
</div>

<!-- Content -->
<div class="content-container">

    <!-- Voice Recordings -->
    <div class="content-card">
        <h2>🎙️ Voice Ideas</h2>

        {''.join([f'''
        <div class="recording-item">
            <div class="recording-header">
                <div class="recording-title">{rec['filename'] or f"Recording #{rec['id']}"}</div>
                <div class="recording-date">{datetime.fromisoformat(rec['created_at']).strftime('%b %d, %Y')}</div>
            </div>
            <div class="recording-transcript">{rec['transcription'][:300]}{'...' if len(rec['transcription']) > 300 else ''}</div>
        </div>
        ''' for rec in recordings]) if recordings else '<div class="empty-state">No voice recordings yet</div>'}
    </div>

    <!-- Podcasts -->
    {f'''
    <div class="content-card">
        <h2>📻 Podcast Episodes</h2>

        {''.join([f"""
        <div class="podcast-item">
            <div class="podcast-title">{pod['title']}</div>
            <div class="podcast-description">{pod['description'][:200]}{'...' if len(pod['description']) > 200 else ''}</div>
            <div class="podcast-meta">
                <span>{datetime.fromisoformat(pod['created_at']).strftime('%b %d, %Y')}</span>
                {f"<span>{pod['duration_seconds'] // 60} min</span>" if pod['duration_seconds'] else ""}
            </div>
        </div>
        """ for pod in podcasts]) if podcasts else '<div class="empty-state">No podcast episodes yet</div>'}
    </div>
    ''' if podcasts or stats['podcast_count'] > 0 else ''}

    <!-- Projects -->
    {f'''
    <div class="content-card">
        <h2>🚀 Projects & Ideas</h2>
        <div class="projects-list">{projects}</div>
    </div>
    ''' if projects else ''}

</div>

</body>
</html>"""

    return html_content


def export_profile_page(username, html_content):
    """Export profile page to GitHub Pages directory"""

    profiles_dir = VOICE_ARCHIVE_PATH / "u"
    profiles_dir.mkdir(exist_ok=True)

    page_path = profiles_dir / f"{username}.html"

    with open(page_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"📄 Profile page created: {page_path}")
    print(f"   🔗 Live URL: https://cringeproof.com/u/{username}")

    return page_path


def main():
    parser = argparse.ArgumentParser(description="User Profile Page Generator")
    parser.add_argument("--user-id", type=int, help="User ID to generate profile for")
    parser.add_argument("--username", help="Username to generate profile for")
    parser.add_argument("--all", action="store_true", help="Generate profiles for all users")

    args = parser.parse_args()

    if not args.user_id and not args.username and not args.all:
        parser.error("Must specify --user-id, --username, or --all")

    print("\n👤 USER PROFILE PAGE GENERATOR")
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

        print(f"📋 Generating profile pages for {len(users)} users...\n")

        for user in users:
            try:
                user_info = get_user_info(user_id=user['id'])
                recordings = get_user_recordings(user['id'])
                podcasts = get_user_podcasts(user['id'])
                stats = get_user_stats(user['id'])

                html_content = generate_profile_page(user_info, recordings, podcasts, stats)
                export_profile_page(user_info['username'], html_content)
            except Exception as e:
                print(f"❌ Error generating profile for user {user['id']}: {e}")

        print(f"\n✅ Generated {len(users)} profile pages")

    else:
        # Generate for single user
        user_info = get_user_info(user_id=args.user_id, username=args.username)
        recordings = get_user_recordings(user_info['id'])
        podcasts = get_user_podcasts(user_info['id'])
        stats = get_user_stats(user_info['id'])

        print(f"👤 User: {user_info['username']} (ID: {user_info['id']})")
        print(f"📊 Voice Ideas: {stats['voice_count']}")
        print(f"📻 Podcasts: {stats['podcast_count']}")

        html_content = generate_profile_page(user_info, recordings, podcasts, stats)
        page_path = export_profile_page(user_info['username'], html_content)

        print(f"\n🎉 SUCCESS!")
        print(f"   Profile live at:")
        print(f"   🌐 https://cringeproof.com/u/{user_info['username']}")
        print(f"\n   Local file:")
        print(f"   📂 {page_path}")


if __name__ == "__main__":
    main()
