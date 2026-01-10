#!/usr/bin/env python3
"""
README-as-Profile System

Let users create profiles via README submission.
No image uploads - avatars auto-generate from feedback.

Profile = What you CLAIM (README)
Avatar = What others CONFIRM (feedback)

The gap shows authenticity.
"""

from flask import Blueprint, request, jsonify, Response
from database import get_db
import json
from datetime import datetime
import re

profile_bp = Blueprint('profile', __name__)

def create_profile_tables():
    """Create tables for README-based profiles"""
    db = get_db()

    db.execute('''
        CREATE TABLE IF NOT EXISTS user_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_slug TEXT UNIQUE NOT NULL,
            readme_content TEXT NOT NULL,
            projects_want_to_build TEXT,  -- JSON array
            github_username TEXT,
            skills_claimed TEXT,  -- JSON array from README
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    db.commit()

# Initialize tables
try:
    create_profile_tables()
except:
    pass

def parse_readme_sections(readme_content):
    """
    Parse README into structured sections

    Looks for:
    - ## Skills / ## What I Know
    - ## Projects / ## Want to Build
    - Bio (first paragraph)
    """
    sections = {
        'bio': '',
        'skills_claimed': [],
        'projects': []
    }

    lines = readme_content.split('\n')

    # Get bio (everything before first ##)
    bio_lines = []
    for line in lines:
        if line.startswith('##'):
            break
        if line.strip() and not line.startswith('#'):
            bio_lines.append(line)

    sections['bio'] = ' '.join(bio_lines).strip()

    # Extract skills
    in_skills_section = False
    for line in lines:
        if re.match(r'##\s*(Skills|What I Know|Technologies)', line, re.IGNORECASE):
            in_skills_section = True
            continue
        elif line.startswith('##'):
            in_skills_section = False

        if in_skills_section and line.strip().startswith('-'):
            skill = line.strip().lstrip('- ')
            sections['skills_claimed'].append(skill)

    # Extract projects
    in_projects_section = False
    for line in lines:
        if re.match(r'##\s*(Projects|Want to Build|Building)', line, re.IGNORECASE):
            in_projects_section = True
            continue
        elif line.startswith('##'):
            in_projects_section = False

        if in_projects_section and line.strip().startswith('-'):
            project = line.strip().lstrip('- ')
            sections['projects'].append(project)

    return sections

@profile_bp.route('/api/profile/create', methods=['POST'])
def create_profile():
    """
    Create profile from README submission

    POST /api/profile/create
    {
        "slug": "alice",
        "readme_content": "# Alice\n\nBackend engineer...",
        "github_username": "alice-codes" (optional)
    }

    Returns profile with auto-generated avatar URL
    """
    data = request.json
    slug = data.get('slug', '').lower().strip()
    readme_content = data.get('readme_content', '')
    github_username = data.get('github_username', '')

    if not slug or not readme_content:
        return jsonify({
            'error': 'slug and readme_content required'
        }), 400

    # Validate slug (import from slug_routes)
    from slug_routes import validate_slug
    valid, message = validate_slug(slug)
    if not valid:
        return jsonify({'error': message}), 400

    db = get_db()

    # Check if slug already taken
    existing = db.execute(
        'SELECT id FROM user_profiles WHERE user_slug = ?',
        (slug,)
    ).fetchone()

    if existing:
        return jsonify({
            'error': f'Slug "{slug}" already taken'
        }), 409

    # Parse README sections
    sections = parse_readme_sections(readme_content)

    # Store profile
    cursor = db.execute('''
        INSERT INTO user_profiles (
            user_slug, readme_content, projects_want_to_build,
            github_username, skills_claimed
        ) VALUES (?, ?, ?, ?, ?)
    ''', (
        slug,
        readme_content,
        json.dumps(sections['projects']),
        github_username,
        json.dumps(sections['skills_claimed'])
    ))

    profile_id = cursor.lastrowid
    db.commit()

    return jsonify({
        'success': True,
        'profile_id': profile_id,
        'slug': slug,
        'url': f'/{slug}',
        'avatar_url': f'/api/profile/{slug}/avatar',
        'sections': sections,
        'message': f'✨ Profile created at /{slug}'
    })


@profile_bp.route('/api/profile/<slug>')
def get_profile(slug):
    """
    Get profile by slug

    Returns README content + feedback stats + avatar URL
    """
    db = get_db()

    profile = db.execute(
        'SELECT * FROM user_profiles WHERE user_slug = ?',
        (slug,)
    ).fetchone()

    if not profile:
        return jsonify({'error': f'Profile "{slug}" not found'}), 404

    # Get feedback stats
    feedback = db.execute('''
        SELECT mention_count, positive_mentions, skills_mentioned
        FROM collaboration_people
        WHERE name = ?
    ''', (slug,)).fetchone()

    feedback_stats = {
        'mention_count': 0,
        'skills_confirmed': []
    }

    if feedback:
        feedback_stats = {
            'mention_count': feedback['mention_count'],
            'positive_mentions': feedback['positive_mentions'],
            'skills_confirmed': json.loads(feedback['skills_mentioned'] or '[]')
        }

    return jsonify({
        'success': True,
        'slug': slug,
        'readme_content': profile['readme_content'],
        'github_username': profile['github_username'],
        'skills_claimed': json.loads(profile['skills_claimed'] or '[]'),
        'skills_confirmed': feedback_stats['skills_confirmed'],
        'projects': json.loads(profile['projects_want_to_build'] or '[]'),
        'created_at': profile['created_at'],
        'avatar_url': f'/api/profile/{slug}/avatar',
        'feedback_stats': feedback_stats,
        'authenticity_gap': calculate_authenticity_gap(
            json.loads(profile['skills_claimed'] or '[]'),
            feedback_stats['skills_confirmed']
        )
    })


@profile_bp.route('/api/profile/<slug>/avatar')
def get_profile_avatar(slug):
    """
    Generate avatar SVG from feedback (not self-reported data)

    Avatar is deterministic from what OTHERS say about you
    """
    db = get_db()

    # Get feedback for this person
    feedback = db.execute('''
        SELECT mention_count, skills_mentioned
        FROM collaboration_people
        WHERE name = ?
    ''', (slug,)).fetchone()

    if not feedback or not feedback['skills_mentioned']:
        # No feedback yet - generate default avatar from slug
        svg = generate_default_avatar_from_slug(slug)
    else:
        # Generate avatar from feedback words
        skills = json.loads(feedback['skills_mentioned'])
        svg = generate_avatar_from_skills(slug, skills, feedback['mention_count'])

    return Response(svg, mimetype='image/svg+xml')


def generate_avatar_from_skills(slug, skills, mention_count):
    """
    Generate SVG avatar from skill keywords and mention count

    More mentions = more complex pattern
    Different skills = different colors
    """
    import hashlib

    # Create deterministic hash from skills
    skills_str = ''.join(sorted(skills))
    skill_hash = hashlib.sha256(f"{slug}{skills_str}".encode()).hexdigest()

    # Extract visual parameters
    hue1 = int(skill_hash[0:2], 16) % 360
    hue2 = (hue1 + int(skill_hash[2:4], 16)) % 360
    hue3 = (hue2 + int(skill_hash[4:6], 16)) % 360

    # Complexity from mention count (1-10 scale)
    complexity = min(mention_count, 10)

    size = 200

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 200 200">
    <defs>
        <linearGradient id="grad{slug}" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:hsl({hue1}, 70%, 60%);stop-opacity:1" />
            <stop offset="50%" style="stop-color:hsl({hue2}, 70%, 60%);stop-opacity:1" />
            <stop offset="100%" style="stop-color:hsl({hue3}, 70%, 60%);stop-opacity:1" />
        </linearGradient>
    </defs>

    <!-- Background circle -->
    <circle cx="100" cy="100" r="95" fill="url(#grad{slug})" />

    <!-- Complexity patterns (more mentions = more shapes) -->
    '''

    # Add shapes based on mention count
    for i in range(complexity):
        angle = (360 / complexity) * i
        x = 100 + 60 * ((int(skill_hash[i*2:i*2+2], 16) % 100) / 100)
        y = 100 + 60 * ((int(skill_hash[i*2+1:i*2+3], 16) % 100) / 100)
        r = 10 + (int(skill_hash[i*3:i*3+2], 16) % 20)

        svg += f'''
    <circle cx="{x}" cy="{y}" r="{r}" fill="hsla({(hue1 + i*30) % 360}, 80%, 50%, 0.6)" />'''

    # Add skill indicators (one per skill)
    for idx, skill in enumerate(skills[:5]):  # Max 5 skill indicators
        skill_hash_val = hashlib.md5(skill.encode()).hexdigest()
        x = 50 + (idx * 30)
        y = 180
        color_hue = int(skill_hash_val[0:2], 16) % 360

        svg += f'''
    <rect x="{x}" y="{y}" width="20" height="10" fill="hsl({color_hue}, 80%, 50%)" rx="2" />'''

    svg += '''
</svg>'''

    return svg


def generate_default_avatar_from_slug(slug):
    """Generate simple avatar for users with no feedback yet"""
    import hashlib

    slug_hash = hashlib.sha256(slug.encode()).hexdigest()
    hue = int(slug_hash[0:2], 16) % 360

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200">
    <circle cx="100" cy="100" r="95" fill="hsl({hue}, 50%, 70%)" />
    <circle cx="100" cy="100" r="60" fill="hsl({hue}, 50%, 60%)" opacity="0.5" />
    <text x="100" y="110" text-anchor="middle" font-size="48" fill="white" font-family="monospace">
        {slug[0].upper()}
    </text>
    <text x="100" y="180" text-anchor="middle" font-size="12" fill="white" opacity="0.7">
        No feedback yet
    </text>
</svg>'''


def calculate_authenticity_gap(skills_claimed, skills_confirmed):
    """
    Calculate gap between what user claims and what others confirm

    Returns:
    {
        'verified': [skills both claimed and confirmed],
        'unverified': [skills claimed but not confirmed],
        'unexpected': [skills confirmed but not claimed],
        'authenticity_score': 0-100
    }
    """
    skills_claimed_set = set([s.lower() for s in skills_claimed])
    skills_confirmed_set = set([s.lower() for s in skills_confirmed])

    verified = list(skills_claimed_set & skills_confirmed_set)
    unverified = list(skills_claimed_set - skills_confirmed_set)
    unexpected = list(skills_confirmed_set - skills_claimed_set)

    # Authenticity score
    if not skills_claimed:
        score = 100 if not skills_confirmed else 50
    else:
        score = int((len(verified) / len(skills_claimed)) * 100)

    return {
        'verified': verified,
        'unverified': unverified,
        'unexpected': unexpected,
        'authenticity_score': score
    }


@profile_bp.route('/api/profile/<slug>/update-readme', methods=['PUT'])
def update_readme(slug):
    """Update profile README content"""
    data = request.json
    readme_content = data.get('readme_content', '')

    if not readme_content:
        return jsonify({'error': 'readme_content required'}), 400

    db = get_db()

    # Check profile exists
    profile = db.execute(
        'SELECT id FROM user_profiles WHERE user_slug = ?',
        (slug,)
    ).fetchone()

    if not profile:
        return jsonify({'error': 'Profile not found'}), 404

    # Parse new sections
    sections = parse_readme_sections(readme_content)

    # Update
    db.execute('''
        UPDATE user_profiles
        SET readme_content = ?,
            projects_want_to_build = ?,
            skills_claimed = ?,
            last_updated = ?
        WHERE user_slug = ?
    ''', (
        readme_content,
        json.dumps(sections['projects']),
        json.dumps(sections['skills_claimed']),
        datetime.now().isoformat(),
        slug
    ))
    db.commit()

    return jsonify({
        'success': True,
        'message': 'Profile updated',
        'sections': sections
    })
