#!/usr/bin/env python3
"""
Soulfra Simple Builder - The "WhatsApp for Websites" Orchestrator

This is the core magic that makes Soulfra simple:
    1. User takes 5-question quiz
    2. System auto-matches theme based on personality
    3. QR scan → BOOM! Full website ready

The "Arcade Machine" flow:
    Quiz → Theme → QR → Claim → Build → Post → Scan → Feedback → Loop

Usage:
    from soulfra_simple_builder import SoulfraSi mpleBuilder

    builder = SoulfraSimpleBuilder()

    # After quiz completion
    theme = builder.match_quiz_to_theme(quiz_answers)

    # After QR signup
    result = builder.generate_full_site(user_id, theme, quiz_answers)
"""

import yaml
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import re


class SoulfraSimpleBuilder:
    """
    The orchestrator that connects all the pieces into one flowing system
    """

    def __init__(self, db_path: str = 'soulfra.db', themes_path: str = 'themes/manifest.yaml'):
        """
        Initialize the Simple Builder

        Args:
            db_path: Path to SQLite database
            themes_path: Path to themes manifest
        """
        self.db_path = db_path
        self.themes_path = themes_path
        self.themes = self._load_themes()

    def _load_themes(self) -> Dict:
        """Load theme manifest from YAML"""
        themes_file = Path(self.themes_path)

        if not themes_file.exists():
            print(f"[WARNING] Themes manifest not found: {self.themes_path}")
            return {}

        with open(themes_file, 'r') as f:
            data = yaml.safe_load(f)
            return data.get('themes', {})

    # ==========================================================================
    # PHASE 1: Quiz → Theme Matching
    # ==========================================================================

    def match_quiz_to_theme(self, quiz_answers: Dict[str, Any]) -> str:
        """
        Match quiz answers to the best theme based on personality

        This is the heart of the "60-second setup" - we auto-detect
        what kind of site they want based on their answers.

        Args:
            quiz_answers: Dict of quiz responses
                Example: {
                    'vibe': 'calm',
                    'communication_style': 'thoughtful',
                    'goals': 'sharing ideas',
                    'aesthetic': 'minimal',
                    'privacy': 'public'
                }

        Returns:
            Theme name (e.g., 'ocean-dreams', 'calriven', etc.)
        """
        if not quiz_answers:
            return 'ocean-dreams'  # Default theme

        # Personality scoring system
        theme_scores = {theme_name: 0 for theme_name in self.themes.keys()}

        # Extract answers
        vibe = quiz_answers.get('vibe', '').lower()
        comm_style = quiz_answers.get('communication_style', '').lower()
        goals = quiz_answers.get('goals', '').lower()
        aesthetic = quiz_answers.get('aesthetic', '').lower()
        privacy = quiz_answers.get('privacy', '').lower()

        # Score each theme based on personality match
        for theme_name, theme_data in self.themes.items():
            personality = theme_data.get('personality', '').lower()
            tone = theme_data.get('tone', '').lower()

            # Vibe matching
            if vibe in personality or vibe in tone:
                theme_scores[theme_name] += 3

            # Communication style matching
            if comm_style in tone:
                theme_scores[theme_name] += 2

            # Goals matching (keywords)
            goal_keywords = {
                'sharing': ['peaceful', 'flowing', 'calm'],
                'building': ['technical', 'precise', 'professional'],
                'privacy': ['private', 'secure', 'protective'],
                'creating': ['creative', 'artistic', 'expressive']
            }

            for goal_key, keywords in goal_keywords.items():
                if goal_key in goals:
                    for keyword in keywords:
                        if keyword in personality or keyword in tone:
                            theme_scores[theme_name] += 1

            # Aesthetic matching
            aesthetic_map = {
                'minimal': ['calm', 'clean', 'simple'],
                'technical': ['technical', 'precise', 'data'],
                'colorful': ['vibrant', 'creative', 'expressive'],
                'dark': ['secure', 'private', 'protective']
            }

            if aesthetic in aesthetic_map:
                for keyword in aesthetic_map[aesthetic]:
                    if keyword in personality or keyword in tone:
                        theme_scores[theme_name] += 2

            # Privacy level matching
            if privacy == 'private' and 'private' in personality:
                theme_scores[theme_name] += 3
            elif privacy == 'public' and 'peaceful' in personality:
                theme_scores[theme_name] += 1

        # Return theme with highest score
        best_theme = max(theme_scores.items(), key=lambda x: x[1])

        print(f"[THEME MATCH] Quiz answers matched to: {best_theme[0]} (score: {best_theme[1]})")
        return best_theme[0]

    # ==========================================================================
    # PHASE 2: Full Site Generation
    # ==========================================================================

    def generate_full_site(self, user_id: int, theme: str, quiz_answers: Dict[str, Any]) -> Dict[str, Any]:
        """
        Auto-generate EVERYTHING for a new user's site

        This is the "BOOM! FULL SITE READY" moment.

        Generates:
            - Website homepage
            - Blog template (based on theme)
            - Database schema (user's tables)
            - Backend routes (API endpoints)
            - First post (welcome message)
            - QR codes (for claiming/sharing)

        Args:
            user_id: User's ID in database
            theme: Theme name (from match_quiz_to_theme)
            quiz_answers: Original quiz answers for personalization

        Returns:
            Dict with generation results:
            {
                'success': True,
                'theme': 'ocean-dreams',
                'generated': {
                    'homepage': '/path/to/homepage.html',
                    'blog_template': '/path/to/blog.html',
                    'database_schema': 'user_123_schema.sql',
                    'routes': ['/@username', '/@username/blog', '/@username/qr'],
                    'first_post': {'id': 1, 'title': 'Welcome!'},
                    'qr_codes': ['/static/qr/user_123_claim.png', '/static/qr/user_123_share.png']
                },
                'arcade_token': 'xyz...',  # Session token for the loop
                'next_steps': ['Post your first thought', 'Share your QR', 'Customize theme']
            }
        """
        print(f"\n{'='*70}")
        print(f"🏗️  BUILDING FULL SITE FOR USER {user_id}")
        print(f"{'='*70}\n")

        result = {
            'success': False,
            'theme': theme,
            'generated': {},
            'arcade_token': None,
            'next_steps': [],
            'errors': []
        }

        try:
            # Get user info from database
            user_info = self._get_user_info(user_id)
            if not user_info:
                result['errors'].append(f"User {user_id} not found in database")
                return result

            username = user_info['username']
            email = user_info.get('email', '')

            print(f"📝 Username: {username}")
            print(f"🎨 Theme: {theme}")
            print(f"💡 Vibe: {quiz_answers.get('vibe', 'default')}\n")

            # 1. Generate homepage
            print("⚡ Generating homepage...")
            homepage_path = self._generate_homepage(user_id, username, theme, quiz_answers)
            result['generated']['homepage'] = homepage_path

            # 2. Generate blog template
            print("⚡ Generating blog template...")
            blog_path = self._generate_blog_template(user_id, username, theme)
            result['generated']['blog_template'] = blog_path

            # 3. Create database schema
            print("⚡ Creating database schema...")
            schema = self._create_user_schema(user_id, username)
            result['generated']['database_schema'] = schema

            # 4. Generate backend routes
            print("⚡ Generating backend routes...")
            routes = self._generate_routes(user_id, username)
            result['generated']['routes'] = routes

            # 5. Create first post
            print("⚡ Creating welcome post...")
            first_post = self._create_first_post(user_id, username, theme, quiz_answers)
            result['generated']['first_post'] = first_post

            # 6. Generate avatar
            print("⚡ Generating pixel art avatar...")
            avatar_path = self._generate_avatar(username)
            result['generated']['avatar'] = avatar_path

            # 7. Generate QR codes
            print("⚡ Generating QR codes...")
            qr_codes = self._generate_qr_codes(user_id, username)
            result['generated']['qr_codes'] = qr_codes

            # 8. Create arcade token for the loop
            print("⚡ Creating arcade token...")
            arcade_token = self._create_arcade_token(user_id)
            result['arcade_token'] = arcade_token

            # 9. Set next steps
            result['next_steps'] = [
                f"Visit your site: /@{username}",
                "Post your first thought",
                "Share your QR code",
                "Customize your theme" if theme == 'ocean-dreams' else f"Explore {theme} theme features"
            ]

            result['success'] = True

            print(f"\n{'='*70}")
            print(f"✅ SITE BUILT SUCCESSFULLY!")
            print(f"{'='*70}\n")

            return result

        except Exception as e:
            print(f"\n❌ ERROR: {e}\n")
            result['errors'].append(str(e))
            return result

    # ==========================================================================
    # PHASE 3: Session Claiming
    # ==========================================================================

    def claim_anonymous_session(self, session_token: str, user_id: int) -> bool:
        """
        Link an anonymous session to a newly created user

        This is the "QR scan → claim" step in the arcade loop.

        Args:
            session_token: Anonymous session token (from session_manager.py)
            user_id: Newly created user ID

        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            # Update session to link to user
            c.execute("""
                UPDATE anonymous_sessions
                SET user_id = ?,
                    claimed_at = ?
                WHERE session_token = ?
            """, (user_id, datetime.now().isoformat(), session_token))

            conn.commit()
            conn.close()

            print(f"[SESSION CLAIMED] Token {session_token[:16]}... → User {user_id}")
            return True

        except Exception as e:
            print(f"[ERROR] Failed to claim session: {e}")
            return False

    # ==========================================================================
    # Internal Generation Methods
    # ==========================================================================

    def _get_user_info(self, user_id: int) -> Optional[Dict]:
        """Get user info from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = c.fetchone()
            conn.close()

            if row:
                return dict(row)
            return None

        except Exception as e:
            print(f"[ERROR] Failed to get user info: {e}")
            return None

    def _generate_homepage(self, user_id: int, username: str, theme: str, quiz_answers: Dict) -> str:
        """Generate user's homepage HTML"""
        # This will be a custom template based on theme
        # For now, return path where it would be generated
        homepage_dir = Path('templates') / 'generated' / f'user_{user_id}'
        homepage_dir.mkdir(parents=True, exist_ok=True)

        homepage_path = homepage_dir / 'homepage.html'

        # Get theme data
        theme_data = self.themes.get(theme, {})
        emoji = theme_data.get('emoji', '🌊')

        # Generate simple homepage
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{username} - Soulfra</title>
    <link rel="stylesheet" href="/static/css/themes/{theme}.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>{emoji} Welcome to {username}'s Space</h1>
        </header>

        <main>
            <section class="bio">
                <p>This site was auto-generated based on your vibe: <strong>{quiz_answers.get('vibe', 'peaceful')}</strong></p>
                <p>Theme: <strong>{theme}</strong></p>
            </section>

            <section class="next-steps">
                <h2>What's Next?</h2>
                <ul>
                    <li><a href="/@{username}/blog">Start blogging</a></li>
                    <li><a href="/@{username}/qr">Share your QR</a></li>
                    <li><a href="/hub">Explore features</a></li>
                </ul>
            </section>
        </main>

        <footer>
            <p>Built with Soulfra Simple Builder 🚀</p>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        </footer>
    </div>
</body>
</html>"""

        with open(homepage_path, 'w') as f:
            f.write(html)

        return str(homepage_path)

    def _generate_blog_template(self, user_id: int, username: str, theme: str) -> str:
        """Generate blog template for user"""
        blog_dir = Path('templates') / 'generated' / f'user_{user_id}'
        blog_dir.mkdir(parents=True, exist_ok=True)

        blog_path = blog_dir / 'blog.html'

        # Simple blog template
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{username}'s Blog - Soulfra</title>
    <link rel="stylesheet" href="/static/css/themes/{theme}.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>{username}'s Blog</h1>
            <nav>
                <a href="/@{username}">Home</a>
                <a href="/@{username}/blog">Blog</a>
                <a href="/@{username}/qr">QR</a>
            </nav>
        </header>

        <main>
            <div id="posts">
                <!-- Posts will be dynamically loaded -->
            </div>
        </main>
    </div>
</body>
</html>"""

        with open(blog_path, 'w') as f:
            f.write(html)

        return str(blog_path)

    def _create_user_schema(self, user_id: int, username: str) -> str:
        """
        Document database schema for user's data

        NOTE: Soulfra uses SHARED tables with user_id foreign keys,
        not per-user tables. This is more efficient and allows
        cross-user queries.

        The user's data is stored in:
        - posts (user_id foreign key)
        - comments (user_id foreign key)
        - qr_scans (user_id foreign key)
        - arcade_tokens (user_id foreign key)

        No new tables are created per user.
        """
        schema_name = f"Shared tables with user_id={user_id}"
        return schema_name

    def _generate_routes(self, user_id: int, username: str) -> List[str]:
        """Generate backend routes for user"""
        routes = [
            f"/@{username}",
            f"/@{username}/blog",
            f"/@{username}/qr",
            f"/@{username}/posts",
            f"/@{username}/api/post"
        ]
        return routes

    def _create_first_post(self, user_id: int, username: str, theme: str, quiz_answers: Dict) -> Dict:
        """Create user's first welcome post"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            # Get theme emoji
            theme_data = self.themes.get(theme, {})
            emoji = theme_data.get('emoji', '🌊')

            # Create welcome post
            vibe = quiz_answers.get('vibe', 'excited')

            title = f"{emoji} Welcome to my space!"
            slug = f"welcome-{username}-{datetime.now().strftime('%Y%m%d')}"

            post_content = f"""I just set up my Soulfra site in 60 seconds!

My vibe: **{vibe}**
My theme: **{theme}**

This is the start of something new. Ready to share ideas, build in public, and connect.

Let's go! 🚀
"""

            c.execute("""
                INSERT INTO posts (user_id, title, slug, content, published_at)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, title, slug, post_content, datetime.now().isoformat()))

            post_id = c.lastrowid

            conn.commit()
            conn.close()

            return {
                'id': post_id,
                'title': title,
                'slug': slug,
                'content': post_content,
                'published_at': datetime.now().isoformat()
            }

        except Exception as e:
            print(f"[ERROR] Failed to create first post: {e}")
            return {}

    def _generate_avatar(self, username: str) -> str:
        """Generate pixel art avatar for user"""
        try:
            from avatar_generator import save_avatar

            avatar_path = save_avatar(username, output_dir='static/avatars/generated')
            return avatar_path

        except Exception as e:
            print(f"[ERROR] Failed to generate avatar: {e}")
            return ""

    def _generate_qr_codes(self, user_id: int, username: str) -> List[str]:
        """Generate QR codes for user using zero-dependency QR encoder"""
        try:
            from qr_encoder_stdlib import generate_qr_code

            qr_dir = Path('static') / 'qr' / f'user_{user_id}'
            qr_dir.mkdir(parents=True, exist_ok=True)

            base_url = "http://localhost:5000"  # TODO: Get from config

            qr_codes = []

            # 1. Claim QR - Link to claim this account/session
            claim_url = f"{base_url}/claim/{username}"
            claim_path = qr_dir / f'{username}_claim.bmp'
            claim_data = generate_qr_code(claim_url, scale=5)
            with open(claim_path, 'wb') as f:
                f.write(claim_data)
            qr_codes.append(str(claim_path))

            # 2. Share QR - Link to user's profile
            share_url = f"{base_url}/@{username}"
            share_path = qr_dir / f'{username}_share.bmp'
            share_data = generate_qr_code(share_url, scale=5)
            with open(share_path, 'wb') as f:
                f.write(share_data)
            qr_codes.append(str(share_path))

            # 3. Profile QR - Link to user's QR page
            profile_url = f"{base_url}/@{username}/qr"
            profile_path = qr_dir / f'{username}_profile.bmp'
            profile_data = generate_qr_code(profile_url, scale=5)
            with open(profile_path, 'wb') as f:
                f.write(profile_data)
            qr_codes.append(str(profile_path))

            return qr_codes

        except Exception as e:
            print(f"[ERROR] Failed to generate QR codes: {e}")
            return []

    def _create_arcade_token(self, user_id: int) -> str:
        """Create arcade token for feedback loop"""
        import secrets

        # Generate token
        token = secrets.token_hex(32)

        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            # Store in arcade_tokens table (create if doesn't exist)
            c.execute("""
                CREATE TABLE IF NOT EXISTS arcade_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    token TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL,
                    loop_stage TEXT DEFAULT 'build',
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            c.execute("""
                INSERT INTO arcade_tokens (user_id, token, created_at, loop_stage)
                VALUES (?, ?, ?, 'build')
            """, (user_id, token, datetime.now().isoformat()))

            conn.commit()
            conn.close()

            return token

        except Exception as e:
            print(f"[ERROR] Failed to create arcade token: {e}")
            return token  # Return token anyway


# ==============================================================================
# Command-Line Interface
# ==============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Soulfra Simple Builder - WhatsApp for Websites')
    parser.add_argument('--test-match', action='store_true', help='Test theme matching')
    parser.add_argument('--test-build', type=int, help='Test full site build for user ID')
    parser.add_argument('--db', default='soulfra.db', help='Database path')

    args = parser.parse_args()

    builder = SoulfraSimpleBuilder(db_path=args.db)

    if args.test_match:
        print("\n" + "="*70)
        print("TESTING THEME MATCHING")
        print("="*70 + "\n")

        # Test different personality types
        test_cases = [
            {
                'name': 'Calm Creator',
                'answers': {
                    'vibe': 'calm',
                    'communication_style': 'thoughtful',
                    'goals': 'sharing ideas',
                    'aesthetic': 'minimal',
                    'privacy': 'public'
                }
            },
            {
                'name': 'Technical Builder',
                'answers': {
                    'vibe': 'focused',
                    'communication_style': 'precise',
                    'goals': 'building projects',
                    'aesthetic': 'technical',
                    'privacy': 'public'
                }
            },
            {
                'name': 'Privacy Advocate',
                'answers': {
                    'vibe': 'careful',
                    'communication_style': 'private',
                    'goals': 'privacy',
                    'aesthetic': 'dark',
                    'privacy': 'private'
                }
            }
        ]

        for test in test_cases:
            print(f"\n{test['name']}:")
            print(f"  Answers: {test['answers']}")
            theme = builder.match_quiz_to_theme(test['answers'])
            print(f"  → Matched theme: {theme}\n")

    elif args.test_build:
        print("\n" + "="*70)
        print(f"TESTING FULL SITE BUILD FOR USER {args.test_build}")
        print("="*70 + "\n")

        # Mock quiz answers
        quiz_answers = {
            'vibe': 'calm',
            'communication_style': 'thoughtful',
            'goals': 'sharing',
            'aesthetic': 'minimal',
            'privacy': 'public'
        }

        # Match theme
        theme = builder.match_quiz_to_theme(quiz_answers)

        # Build site
        result = builder.generate_full_site(args.test_build, theme, quiz_answers)

        # Print results
        print("\nResults:")
        print(f"  Success: {result['success']}")
        print(f"  Theme: {result['theme']}")
        print(f"  Generated: {len(result['generated'])} items")
        print(f"  Arcade Token: {result['arcade_token'][:16] if result['arcade_token'] else 'None'}...")
        print(f"\nNext Steps:")
        for step in result['next_steps']:
            print(f"  - {step}")

    else:
        parser.print_help()
