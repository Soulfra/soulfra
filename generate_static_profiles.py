#!/usr/bin/env python3
"""
Generate static profile pages for GitHub Pages

Reads from soulfra.db and creates static HTML files in voice-archive/profile/
"""

import sqlite3
import os
from pathlib import Path

# Paths
DB_PATH = '/Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/soulfra.db'
OUTPUT_DIR = '/Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/voice-archive/profile'

def get_profile_html(user, recordings, skills):
    """Generate HTML for a user profile"""

    skills_html = ''
    if skills:
        skills_badges = '\n'.join([
            f'<span class="skill-badge {"verified" if s["verified"] else ""} {"expert" if s["level"] == "expert" else ""}">'
            f'{s["skill_name"]} '
            f'{"✓" if s["verified"] else ""} '
            f'{"(" + s["level"] + ")" if s["level"] else ""}'
            f'</span>'
            for s in skills
        ])
        skills_html = f'''
        <section class="skills-section">
            <h2 style="font-size: 2rem; font-weight: 900; margin-bottom: 2rem; text-align: center;">
                🎯 Verified Skills
            </h2>
            <div style="text-align: center;">
                {skills_badges}
            </div>
        </section>
        '''

    recordings_html = ''
    if recordings:
        recording_cards = '\n'.join([
            f'''
            <div class="recording-card">
                <h3>Recording #{i+1}</h3>
                <p class="recording-transcript">{r["transcription"] or "[Transcription pending...]"}</p>
                <div class="recording-meta">
                    Recorded: {r["created_at"]}
                </div>
            </div>
            '''
            for i, r in enumerate(recordings)
        ])
    else:
        recording_cards = '''
        <div style="text-align: center; padding: 4rem; opacity: 0.5;">
            <p>No voice recordings yet.</p>
            <p><a href="/record-simple.html" style="color: #ff006e; font-weight: 700;">Record your first idea →</a></p>
        </div>
        '''

    recordings_html = f'''
    <section class="recordings-section">
        <h2 style="font-size: 2rem; font-weight: 900; margin-bottom: 2rem; text-align: center;">
            🎤 Voice Proofs
        </h2>
        <p style="text-align: center; margin-bottom: 2rem; opacity: 0.8;">
            Skills verified by voice recordings. No certificates, just real knowledge demonstrated in your own words.
        </p>
        {recording_cards}
    </section>
    '''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{user["display_name"] or user["username"]} - CringeProof Profile</title>
<meta name="description" content="Skills verified by voice recordings. {len(recordings)} contributions, {user['reputation']} reputation.">
<link rel="stylesheet" href="https://cringeproof.com/css/soulfra.css">
<style>
.profile-header {{
    background: linear-gradient(135deg, #ff006e, #bdb2ff);
    padding: 3rem 2rem;
    color: white;
    text-align: center;
    border-bottom: 6px solid #000;
}}

.profile-header h1 {{
    font-size: 3rem;
    font-weight: 900;
    margin-bottom: 0.5rem;
}}

.profile-stats {{
    display: flex;
    gap: 2rem;
    justify-content: center;
    margin-top: 1.5rem;
    flex-wrap: wrap;
}}

.stat-box {{
    background: rgba(0,0,0,0.2);
    padding: 1rem 2rem;
    border-radius: 8px;
    border: 3px solid rgba(255,255,255,0.3);
}}

.stat-value {{
    font-size: 2rem;
    font-weight: 900;
    display: block;
}}

.stat-label {{
    font-size: 0.875rem;
    text-transform: uppercase;
    opacity: 0.9;
}}

.skills-section {{
    max-width: 900px;
    margin: 3rem auto;
    padding: 0 2rem;
}}

.skill-badge {{
    display: inline-block;
    background: #fff;
    border: 4px solid #000;
    padding: 0.75rem 1.5rem;
    margin: 0.5rem;
    box-shadow: 4px 4px 0 #bdb2ff;
    font-weight: 700;
}}

.skill-badge.verified {{
    border-color: #10b981;
}}

.skill-badge.expert {{
    background: #ffe5ec;
}}

.recordings-section {{
    max-width: 900px;
    margin: 3rem auto;
    padding: 0 2rem;
}}

.recording-card {{
    background: #fff;
    border: 5px solid #000;
    padding: 2rem;
    margin-bottom: 2rem;
    box-shadow: 8px 8px 0 #bdb2ff;
}}

.recording-card h3 {{
    font-size: 1.25rem;
    font-weight: 900;
    margin-bottom: 1rem;
    color: #ff006e;
}}

.recording-transcript {{
    line-height: 1.8;
    color: #333;
    margin-bottom: 1rem;
}}

.recording-meta {{
    font-size: 0.875rem;
    opacity: 0.7;
}}
</style>
</head>
<body>
<nav class="soulfra-nav">
    <div class="soulfra-nav-container">
        <a href="/" class="soulfra-logo">🚫 CringeProof</a>
        <div class="soulfra-links">
            <a href="/">Home</a>
            <a href="/record-simple.html">Record</a>
            <a href="/profile/{user["username"]}/" class="active">Profile</a>
        </div>
    </div>
</nav>

<div class="profile-header">
    <h1>{user["display_name"] or user["username"]}</h1>
    <p>@{user["username"]}</p>

    <div class="profile-stats">
        <div class="stat-box">
            <span class="stat-value">{user["reputation"]}</span>
            <span class="stat-label">Reputation</span>
        </div>
        <div class="stat-box">
            <span class="stat-value">{len(recordings)}</span>
            <span class="stat-label">Voice Proofs</span>
        </div>
        <div class="stat-box">
            <span class="stat-value">{len(skills)}</span>
            <span class="stat-label">Skills</span>
        </div>
    </div>
</div>

<div class="container">
    {skills_html}
    {recordings_html}
</div>

<footer style="text-align: center; padding: 2rem; opacity: 0.7; margin-top: 4rem;">
    <p><strong>CringeProof</strong> - Skills verified by voice, not certificates</p>
    <p style="margin-top: 0.5rem;">
        <a href="/">Home</a> |
        <a href="/ideas/">Ideas</a> |
        <a href="/record-simple.html">Record</a>
    </p>
</footer>
</body>
</html>
'''

def main():
    """Generate static profile pages for all users"""

    # Connect to database
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

    # Get all users
    users = db.execute('''
        SELECT u.*,
               COALESCE(r.bits_earned, 0) as reputation,
               COALESCE(r.contribution_count, 0) as contributions
        FROM users u
        LEFT JOIN reputation r ON r.user_id = u.id
    ''').fetchall()

    print(f"📊 Found {len(users)} users")

    for user in users:
        username = user['username']
        print(f"\n👤 Generating profile for: {username}")

        # Get recordings
        recordings = db.execute('''
            SELECT id, transcription, created_at
            FROM simple_voice_recordings
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 20
        ''', (user['id'],)).fetchall()

        # Get skills
        skills = db.execute('''
            SELECT skill_name, skill_category, level, verified, issued_at
            FROM skill_certifications
            WHERE user_id = ?
            ORDER BY issued_at DESC
        ''', (user['id'],)).fetchall()

        # Convert to dicts
        user_dict = dict(user)
        recordings_list = [dict(r) for r in recordings]
        skills_list = [dict(s) for s in skills]

        print(f"   📝 {len(recordings_list)} recordings")
        print(f"   🎯 {len(skills_list)} skills")

        # Generate HTML
        html = get_profile_html(user_dict, recordings_list, skills_list)

        # Create directory
        profile_dir = Path(OUTPUT_DIR) / username
        profile_dir.mkdir(parents=True, exist_ok=True)

        # Write HTML file
        output_file = profile_dir / 'index.html'
        output_file.write_text(html)

        print(f"   ✅ Saved to: {output_file}")

    db.close()

    print(f"\n✨ Generated {len(users)} profile pages in {OUTPUT_DIR}")
    print(f"🌐 Profiles will be available at:")
    for user in users:
        print(f"   - https://cringeproof.com/profile/{user['username']}/")

if __name__ == '__main__':
    main()
