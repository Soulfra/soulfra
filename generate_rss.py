#!/usr/bin/env python3
"""
RSS FEED GENERATOR - Soulfra Personal Blog

Converts voice recordings into RSS feed for personal blog
- Filters by authenticated user_id (vs anonymous CringeProof)
- Uses Ollama to enhance transcripts into blog posts
- Exports to GitHub Pages as feed.xml
- Auto-updates on new recordings

Usage:
    python3 generate_rss.py --user-id 1              # Generate RSS for specific user
    python3 generate_rss.py --username matt          # Generate by username
    python3 generate_rss.py --all                    # Generate feeds for all users
    python3 generate_rss.py --anonymous              # CringeProof anonymous feed (original behavior)
"""

import sqlite3
import os
import json
import argparse
import requests
from pathlib import Path
from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
import html


# Configuration
DB_PATH = "soulfra.db"
VOICE_ARCHIVE_PATH = Path("/Users/matthewmauer/Desktop/voice-archive")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")


def get_user(user_id=None, username=None):
    """Get user from database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Check if users table exists
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if not cursor.fetchone():
        conn.close()
        # No users table yet - use claimed_domains instead
        if username:
            return {'id': None, 'email': f'{username}@soulfra.com'}
        else:
            raise ValueError("Users table not found. Use --username or create users table.")

    if user_id:
        query = "SELECT * FROM users WHERE id = ?"
        user = conn.execute(query, (user_id,)).fetchone()
    elif username:
        # Try github_username first, then email
        query = "SELECT * FROM users WHERE email LIKE ?"
        user = conn.execute(query, (f"{username}%",)).fetchone()
    else:
        raise ValueError("Must provide user_id or username")

    conn.close()

    if not user:
        # Fallback - create minimal user object
        return {'id': user_id, 'email': f'{username or "user"}@soulfra.com'}

    return dict(user)


def get_user_recordings(user_id, limit=20):
    """Get voice recordings for specific user (personal blog, not anonymous)"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    if user_id is None:
        # Anonymous CringeProof feed
        query = """
            SELECT * FROM simple_voice_recordings
            WHERE transcription IS NOT NULL
            ORDER BY created_at DESC
            LIMIT ?
        """
        recordings = conn.execute(query, (limit,)).fetchall()
    else:
        # Personal blog feed (filtered by user)
        query = """
            SELECT * FROM simple_voice_recordings
            WHERE user_id = ?
            AND transcription IS NOT NULL
            ORDER BY created_at DESC
            LIMIT ?
        """
        recordings = conn.execute(query, (user_id, limit)).fetchall()

    conn.close()

    return [dict(rec) for rec in recordings]


def enhance_for_blog(transcript, user_info=None):
    """
    Use Ollama to convert voice transcript into polished blog post
    Different from CringeProof (anonymous ideas) - this is personal blog voice
    """

    author_name = "the author"
    if user_info:
        author_name = user_info.get('github_username') or user_info.get('email', '').split('@')[0]

    prompt = f"""You are converting a personal voice memo into a polished blog post.

This is from {author_name}'s personal blog (not anonymous).

Voice transcript: "{transcript}"

Convert this into a blog post with:
1. Catchy title (5-10 words)
2. Brief excerpt (1-2 sentences, 200 chars max - for RSS preview)
3. Full polished content (preserve personal voice, clean up filler words)
4. Tags/categories (3-5 relevant keywords)

Keep the author's personal voice and perspective. This is a blog, not anonymous content.

Respond ONLY with valid JSON:
{{
  "title": "Blog Post Title Here",
  "excerpt": "Brief excerpt for RSS feed preview (200 chars max)",
  "content": "Full polished blog post content in Markdown format",
  "tags": ["tag1", "tag2", "tag3"],
  "reasoning": "Why these choices for title and tags"
}}"""

    print(f"  🤖 Enhancing with Ollama...")

    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": "llama2",
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )

        result = response.json()
        response_text = result.get("response", "")

        # Extract JSON from response
        start = response_text.find('{')
        end = response_text.rfind('}') + 1
        json_str = response_text[start:end]
        enhanced = json.loads(json_str)

        return enhanced

    except Exception as e:
        print(f"  ⚠️  Ollama enhancement failed: {e}")
        # Fallback - use raw transcript
        return {
            "title": transcript[:50] + "...",
            "excerpt": transcript[:200],
            "content": transcript,
            "tags": ["voice-memo"],
            "reasoning": "Fallback - Ollama unavailable"
        }


def generate_rss_feed(user_id=None, username=None, use_ollama=True):
    """Generate RSS 2.0 feed for user's blog"""

    print(f"\n📻 GENERATING RSS FEED")
    print("=" * 60)

    # Get user info (if authenticated feed)
    user = None
    if user_id or username:
        user = get_user(user_id=user_id, username=username)
        username = user.get('github_username') or user.get('email', '').split('@')[0]
        print(f"👤 User: {username} (ID: {user['id']})")
    else:
        username = "cringeproof"
        print(f"👤 Mode: Anonymous CringeProof feed")

    # Get recordings
    recordings = get_user_recordings(user['id'] if user else None)

    if not recordings:
        print(f"⚠️  No recordings found")
        return None, username

    print(f"📝 Found {len(recordings)} voice posts")

    # Create RSS root
    rss = Element('rss', version='2.0', attrib={
        'xmlns:atom': 'http://www.w3.org/2005/Atom',
        'xmlns:content': 'http://purl.org/rss/1.0/modules/content/'
    })

    channel = SubElement(rss, 'channel')

    # Channel metadata
    if user:
        SubElement(channel, 'title').text = f"{username}'s Soulfra Blog"
        SubElement(channel, 'link').text = f"https://{username}.soulfra.com"
        SubElement(channel, 'description').text = f"Voice-first personal blog by {username}"
        atom_link = f"https://{username}.soulfra.com/feed.xml"
    else:
        SubElement(channel, 'title').text = "CringeProof Ideas"
        SubElement(channel, 'link').text = "https://cringeproof.com"
        SubElement(channel, 'description').text = "AI-extracted insights from voice recordings. Zero cringe, maximum authenticity."
        atom_link = "https://cringeproof.com/feed.xml"

    SubElement(channel, 'language').text = "en-us"
    SubElement(channel, 'lastBuildDate').text = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
    SubElement(channel, 'generator').text = "Soulfra Voice-to-RSS Generator"

    # Atom self-link
    SubElement(channel, 'atom:link', attrib={
        'href': atom_link,
        'rel': 'self',
        'type': 'application/rss+xml'
    })

    # Process each recording into RSS item
    for rec in recordings:
        print(f"\n  📄 Processing recording #{rec['id']}...")

        # Enhance transcript with Ollama (if enabled)
        if use_ollama:
            enhanced = enhance_for_blog(rec['transcription'], user)
        else:
            # Simple fallback
            title = rec.get('filename', f"Recording {rec['id']}").replace('.webm', '').replace('_', ' ').title()
            enhanced = {
                'title': title,
                'excerpt': rec['transcription'][:200],
                'content': rec['transcription'],
                'tags': ['voice-memo']
            }

        # Create RSS item
        item = SubElement(channel, 'item')

        SubElement(item, 'title').text = enhanced['title']
        SubElement(item, 'description').text = enhanced['excerpt']
        SubElement(item, 'content:encoded').text = f"<![CDATA[{enhanced['content']}]]>"

        # Permalink
        if user:
            post_url = f"https://{username}.soulfra.com/posts/{rec['id']}.html"
        else:
            post_url = f"https://cringeproof.com/ideas/{rec['id']}.html"

        SubElement(item, 'link').text = post_url
        SubElement(item, 'guid', isPermaLink='true').text = post_url

        # Publish date
        pub_date = datetime.fromisoformat(rec['created_at']).strftime('%a, %d %b %Y %H:%M:%S GMT')
        SubElement(item, 'pubDate').text = pub_date

        # Author
        if user:
            SubElement(item, 'author').text = f"{user.get('email', 'noreply@soulfra.com')} ({username})"

        # Categories/tags
        for tag in enhanced['tags']:
            SubElement(item, 'category').text = tag

        # Audio enclosure (if available)
        if rec.get('audio_data'):
            if user:
                audio_url = f"https://{username}.soulfra.com/audio/{rec['id']}/recording.webm"
            else:
                audio_url = f"https://cringeproof.com/audio/{rec['id']}/recording.webm"

            audio_size = len(rec['audio_data'])
            SubElement(item, 'enclosure', attrib={
                'url': audio_url,
                'length': str(audio_size),
                'type': 'audio/webm'
            })

        print(f"  ✅ Added: {enhanced['title']}")

    # Pretty print XML
    xml_str = minidom.parseString(tostring(rss, encoding='utf-8')).toprettyxml(indent="  ")

    # Remove extra blank lines
    xml_lines = [line for line in xml_str.split('\n') if line.strip()]
    xml_output = '\n'.join(xml_lines)

    return xml_output, username


def export_rss(xml_content, username):
    """Export RSS feed to GitHub Pages repo"""

    # Export to voice-archive repo (GitHub Pages)
    if username == "cringeproof":
        rss_path = VOICE_ARCHIVE_PATH / "feed.xml"
    else:
        # User-specific feed
        user_feed_dir = VOICE_ARCHIVE_PATH / "feeds"
        user_feed_dir.mkdir(exist_ok=True)
        rss_path = user_feed_dir / f"{username}.xml"

    with open(rss_path, 'w', encoding='utf-8') as f:
        f.write(xml_content)

    print(f"\n📄 RSS feed exported: {rss_path}")

    return rss_path


def get_podcast_episodes(user_id=None):
    """Get podcast episodes (all or by user)"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    if user_id:
        query = """
            SELECT * FROM voice_podcast_episodes
            WHERE user_id = ? AND published = 1
            ORDER BY created_at DESC
            LIMIT 20
        """
        episodes = conn.execute(query, (user_id,)).fetchall()
    else:
        query = """
            SELECT * FROM voice_podcast_episodes
            WHERE published = 1
            ORDER BY created_at DESC
            LIMIT 20
        """
        episodes = conn.execute(query).fetchall()

    conn.close()

    return [dict(ep) for ep in episodes]


def generate_podcast_rss_feed(user_id=None, username=None):
    """Generate podcast RSS feed (Apple Podcasts / Spotify compatible)"""

    print(f"\n📻 GENERATING PODCAST RSS FEED")
    print("=" * 60)

    # Get user info (if personal podcast)
    user = None
    if user_id or username:
        user = get_user(user_id=user_id, username=username)
        username = user.get('email', '').split('@')[0]
        print(f"👤 User: {username} (ID: {user['id']})")
    else:
        username = "cringeproof"
        print(f"👤 Mode: Public Podcast Feed")

    # Get podcast episodes
    episodes = get_podcast_episodes(user['id'] if user else None)

    if not episodes:
        print(f"⚠️  No podcast episodes found")
        return None, username

    print(f"📝 Found {len(episodes)} podcast episodes")

    # Create RSS root with iTunes namespace
    rss = Element('rss', version='2.0', attrib={
        'xmlns:atom': 'http://www.w3.org/2005/Atom',
        'xmlns:itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd',
        'xmlns:content': 'http://purl.org/rss/1.0/modules/content/'
    })

    channel = SubElement(rss, 'channel')

    # Podcast metadata
    if user:
        podcast_title = f"{username}'s Podcast"
        podcast_link = f"https://{username}.soulfra.com/podcast"
        podcast_description = f"Voice-first podcast by {username}"
        podcast_image = f"https://{username}.soulfra.com/podcast-cover.png"
        atom_link = f"https://{username}.soulfra.com/podcast.xml"
    else:
        podcast_title = "CringeProof Podcast"
        podcast_link = "https://cringeproof.com/podcast"
        podcast_description = "Ideas, insights, and conversations from the CringeProof community"
        podcast_image = "https://cringeproof.com/podcast-cover.png"
        atom_link = "https://cringeproof.com/podcast.xml"

    SubElement(channel, 'title').text = podcast_title
    SubElement(channel, 'link').text = podcast_link
    SubElement(channel, 'description').text = podcast_description
    SubElement(channel, 'language').text = "en-us"
    SubElement(channel, 'lastBuildDate').text = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
    SubElement(channel, 'generator').text = "Soulfra Podcast Generator"

    # iTunes podcast tags
    SubElement(channel, 'itunes:subtitle').text = podcast_description
    SubElement(channel, 'itunes:author').text = username
    SubElement(channel, 'itunes:summary').text = podcast_description
    SubElement(channel, 'itunes:explicit').text = "no"

    # Podcast image
    itunes_image = SubElement(channel, 'itunes:image')
    itunes_image.set('href', podcast_image)

    # iTunes category
    itunes_category = SubElement(channel, 'itunes:category')
    itunes_category.set('text', 'Technology')

    # Atom self-link
    SubElement(channel, 'atom:link', attrib={
        'href': atom_link,
        'rel': 'self',
        'type': 'application/rss+xml'
    })

    # Process each episode
    for ep in episodes:
        print(f"\n  📄 Processing episode #{ep['id']}: {ep['title']}")

        item = SubElement(channel, 'item')

        SubElement(item, 'title').text = ep['title']
        SubElement(item, 'description').text = ep['description']

        # Episode link
        if user:
            episode_url = f"https://{username}.soulfra.com/podcast/{ep['id']}.html"
        else:
            episode_url = f"https://cringeproof.com/podcast/{ep['id']}.html"

        SubElement(item, 'link').text = episode_url
        SubElement(item, 'guid', isPermaLink='true').text = episode_url

        # Publish date
        pub_date = datetime.fromisoformat(ep['created_at']).strftime('%a, %d %b %Y %H:%M:%S GMT')
        SubElement(item, 'pubDate').text = pub_date

        # iTunes episode tags
        SubElement(item, 'itunes:title').text = ep['title']
        SubElement(item, 'itunes:summary').text = ep['description']
        if ep['duration_seconds']:
            SubElement(item, 'itunes:duration').text = str(ep['duration_seconds'])

        # Audio enclosure (from recording)
        if ep['recording_id']:
            conn = sqlite3.connect(DB_PATH)
            rec = conn.execute(
                "SELECT audio_data FROM simple_voice_recordings WHERE id = ?",
                (ep['recording_id'],)
            ).fetchone()
            conn.close()

            if rec and rec[0]:
                if user:
                    audio_url = f"https://{username}.soulfra.com/audio/{ep['recording_id']}/recording.webm"
                else:
                    audio_url = f"https://cringeproof.com/audio/{ep['recording_id']}/recording.webm"

                SubElement(item, 'enclosure', attrib={
                    'url': audio_url,
                    'length': str(len(rec[0])),
                    'type': 'audio/webm'
                })

        print(f"  ✅ Added: {ep['title']}")

    # Pretty print XML
    xml_str = minidom.parseString(tostring(rss, encoding='utf-8')).toprettyxml(indent="  ")

    # Remove extra blank lines
    xml_lines = [line for line in xml_str.split('\n') if line.strip()]
    xml_output = '\n'.join(xml_lines)

    return xml_output, username


def export_podcast_rss(xml_content, username):
    """Export podcast RSS feed"""

    if username == "cringeproof":
        rss_path = VOICE_ARCHIVE_PATH / "podcast.xml"
    else:
        # User-specific podcast feed
        user_feed_dir = VOICE_ARCHIVE_PATH / "podcasts"
        user_feed_dir.mkdir(exist_ok=True)
        rss_path = user_feed_dir / f"{username}.xml"

    with open(rss_path, 'w', encoding='utf-8') as f:
        f.write(xml_content)

    print(f"\n📄 Podcast RSS exported: {rss_path}")

    return rss_path


def main():
    parser = argparse.ArgumentParser(description="RSS Feed Generator - Soulfra Personal Blog & Podcasts")
    parser.add_argument("--user-id", type=int, help="User ID to generate RSS for")
    parser.add_argument("--username", help="Username to generate RSS for")
    parser.add_argument("--all", action="store_true", help="Generate feeds for all users")
    parser.add_argument("--anonymous", action="store_true", help="Generate anonymous CringeProof feed")
    parser.add_argument("--podcast", action="store_true", help="Generate podcast RSS (not blog)")
    parser.add_argument("--limit", type=int, default=20, help="Max items in feed (default: 20)")
    parser.add_argument("--no-ollama", action="store_true", help="Skip Ollama enhancement (faster)")

    args = parser.parse_args()

    use_ollama = not args.no_ollama
    is_podcast = args.podcast

    if args.anonymous:
        # Anonymous CringeProof feed
        if is_podcast:
            xml_content, username = generate_podcast_rss_feed(user_id=None)
            if xml_content:
                rss_path = export_podcast_rss(xml_content, username)
                print(f"\n🎉 SUCCESS!")
                print(f"   📻 Podcast RSS: https://cringeproof.com/podcast.xml")
                print(f"   📂 Local file: {rss_path}")
        else:
            xml_content, username = generate_rss_feed(user_id=None, use_ollama=use_ollama)
            if xml_content:
                rss_path = export_rss(xml_content, username)
                print(f"\n🎉 SUCCESS!")
                print(f"   📻 RSS Feed: https://cringeproof.com/feed.xml")
                print(f"   📂 Local file: {rss_path}")

    elif args.all:
        # Generate feeds for all users with recordings
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row

        # Check if users table exists
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if cursor.fetchone():
            users = conn.execute("""
                SELECT DISTINCT u.*
                FROM users u
                JOIN simple_voice_recordings r ON r.user_id = u.id
                WHERE r.transcription IS NOT NULL
            """).fetchall()
        else:
            print("⚠️  No users table found - only anonymous feed available")
            users = []

        conn.close()

        if not users:
            print("📻 Generating anonymous CringeProof feed only...")
            xml_content, username = generate_rss_feed(user_id=None, use_ollama=use_ollama)
            if xml_content:
                export_rss(xml_content, username)
                print(f"\n✅ Generated 1 RSS feed")
        else:
            print(f"📻 Generating feeds for {len(users)} users...")

            for user in users:
                try:
                    xml_content, username = generate_rss_feed(user_id=user['id'], use_ollama=use_ollama)
                    if xml_content:
                        export_rss(xml_content, username)
                except Exception as e:
                    print(f"❌ Error generating feed for user {user['id']}: {e}")

            print(f"\n✅ Generated {len(users)} RSS feeds")

    elif args.user_id or args.username:
        # Generate single user feed
        if is_podcast:
            xml_content, username = generate_podcast_rss_feed(
                user_id=args.user_id,
                username=args.username
            )

            if xml_content:
                rss_path = export_podcast_rss(xml_content, username)

                print(f"\n🎉 SUCCESS!")
                print(f"   📻 Podcast RSS: https://{username}.soulfra.com/podcast.xml")
                print(f"   📂 Local file: {rss_path}")
                print(f"\n   Submit to Apple Podcasts, Spotify, etc.")
        else:
            xml_content, username = generate_rss_feed(
                user_id=args.user_id,
                username=args.username,
                use_ollama=use_ollama
            )

            if xml_content:
                rss_path = export_rss(xml_content, username)

                print(f"\n🎉 SUCCESS!")
                print(f"   📻 RSS Feed: https://{username}.soulfra.com/feed.xml")
                print(f"   📂 Local file: {rss_path}")
                print(f"\n   Subscribe in any RSS reader:")
                print(f"   - Feedly, Inoreader, NewsBlur, etc.")
    else:
        parser.error("Must specify --user-id, --username, --all, or --anonymous")


if __name__ == "__main__":
    main()
