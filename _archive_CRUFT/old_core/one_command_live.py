#!/usr/bin/env python3
"""
One Command Live - Make Everything Work in ONE Command
=======================================================

This is it. ONE command to:
1. ✅ Check database
2. ✅ Generate AI comments on latest post
3. ✅ Expand best comment to new post
4. ✅ Start SSH tunnel (public hosting)
5. ✅ Generate QR code
6. ✅ Print scannable QR + URL
7. ✅ Keep running (tunnel stays open)

Usage:
    python3 one_command_live.py             # Use serveo.net tunnel (default)
    python3 one_command_live.py cloudflare  # Use Cloudflare tunnel
    python3 one_command_live.py localhost   # Use localhost.run

What you get:
    - Blog post with AI comments
    - Comment expanded to NEW post
    - Public URL (scannable QR code)
    - Self-sustaining content loop

The Magic:
    Original post → AI comment → Expand to new post → AI comments → Repeat!
"""

import sys
import subprocess
import time
from database import get_db
from comment_to_post import (
    check_database_schema,
    auto_expand_qualifying_comments,
    check_expandable_comments,
    migrate_database
)


def print_header(title):
    """Print section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def print_step(step_num, total_steps, description, status=""):
    """Print step status"""
    emoji = "🔄" if not status else status
    print(f"\n{emoji} Step {step_num}/{total_steps}: {description}")


def check_prerequisites():
    """Check if all prerequisites are met"""
    print_header("🔍 Checking Prerequisites")

    checks = {
        'database': False,
        'flask_running': False,
        'schema_ready': False
    }

    # 1. Check database exists
    print("\n📦 Checking database...")
    try:
        conn = get_db()
        posts = conn.execute('SELECT COUNT(*) as count FROM posts').fetchone()
        checks['database'] = True
        print(f"   ✅ Database found ({posts['count']} posts)")
        conn.close()
    except Exception as e:
        print(f"   ❌ Database error: {e}")
        return checks

    # 2. Check if Flask is running
    print("\n🌐 Checking Flask server...")
    try:
        import urllib.request
        urllib.request.urlopen('http://localhost:5001', timeout=2)
        checks['flask_running'] = True
        print("   ✅ Flask running on http://localhost:5001")
    except:
        print("   ⚠️  Flask not running")
        print("   💡 Start with: python3 app.py")

    # 3. Check database schema
    print("\n🗄️  Checking database schema...")
    schema = check_database_schema()
    if schema['ready']:
        checks['schema_ready'] = True
        print("   ✅ Schema ready for comment→post expansion")
    else:
        print("   ⚠️  Schema needs migration")
        print("   💡 Will run migration automatically")

    return checks


def ensure_flask_running():
    """Start Flask if not running"""
    print_header("🚀 Starting Flask Server")

    # Check if already running
    try:
        import urllib.request
        urllib.request.urlopen('http://localhost:5001', timeout=2)
        print("\n✅ Flask already running on port 5001")
        return True
    except:
        pass

    print("\n🔄 Starting Flask server in background...")

    try:
        # Start Flask in background
        process = subprocess.Popen(
            ['python3', 'app.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Wait for Flask to start
        print("⏳ Waiting for Flask to start...")
        for i in range(10):
            time.sleep(1)
            try:
                import urllib.request
                urllib.request.urlopen('http://localhost:5001', timeout=1)
                print(f"\n✅ Flask started successfully!")
                return True
            except:
                continue

        print("\n⚠️  Flask might not have started")
        print("   Check manually: http://localhost:5001")
        return False

    except Exception as e:
        print(f"\n❌ Failed to start Flask: {e}")
        return False


def get_latest_post():
    """Get the latest blog post"""
    conn = get_db()

    post = conn.execute('''
        SELECT * FROM posts
        WHERE published_at IS NOT NULL
        ORDER BY published_at DESC
        LIMIT 1
    ''').fetchone()

    conn.close()

    return dict(post) if post else None


def generate_ai_comments_simple(post_id):
    """
    Generate AI comments (simplified version)

    Uses existing comment system if available, or creates mock comments
    for demonstration purposes
    """
    print(f"\n🤖 Generating AI comments for post #{post_id}...")

    try:
        # Try to use existing orchestrator
        from brand_ai_orchestrator import select_relevant_brands_for_post
        from ollama_auto_commenter import generate_ai_comment

        # Select relevant brands
        brands = select_relevant_brands_for_post(post_id, max_brands=2)

        if not brands:
            print("   ⚠️  No relevant brands found")
            return []

        print(f"   📝 Selected {len(brands)} brand(s) to comment")

        comments = []
        for brand in brands:
            try:
                comment_id = generate_ai_comment(brand['brand_slug'], post_id)
                if comment_id:
                    comments.append(comment_id)
                    print(f"   ✅ {brand['brand_name']} commented")
            except Exception as e:
                print(f"   ⚠️  {brand['brand_name']} failed: {e}")

        return comments

    except ImportError:
        print("   ⚠️  AI comment system not available")
        return []

    except Exception as e:
        print(f"   ⚠️  Error generating comments: {e}")
        return []


def start_tunnel(tunnel_type='serveo'):
    """Start SSH tunnel using ssh_tunnel.py"""
    print_header(f"🌍 Starting Public Tunnel ({tunnel_type})")

    print(f"\n🚀 Launching {tunnel_type} tunnel...")
    print("⏳ This may take 10-15 seconds...\n")

    try:
        # Run ssh_tunnel.py in foreground (it will print QR code)
        process = subprocess.Popen(
            ['python3', 'ssh_tunnel.py', tunnel_type],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        # Read output line by line
        url = None
        for line in iter(process.stdout.readline, ''):
            if not line:
                break

            print(line.rstrip())

            # Detect URL
            if 'Public URL:' in line:
                # Extract URL from line
                import re
                match = re.search(r'https://[^\s]+', line)
                if match:
                    url = match.group(0)

        return url

    except KeyboardInterrupt:
        print("\n\n🛑 Tunnel stopped by user")
        return None

    except Exception as e:
        print(f"\n❌ Failed to start tunnel: {e}")
        return None


def main():
    """Main orchestration"""

    # Parse arguments
    tunnel_type = sys.argv[1] if len(sys.argv) > 1 else 'serveo'

    if tunnel_type in ['help', '--help', '-h']:
        print(__doc__)
        return

    print("="*70)
    print("  🎉 ONE COMMAND LIVE - Make Everything Work!")
    print("="*70)
    print("""
This script will:
1. ✅ Check database and Flask server
2. ✅ Migrate database if needed
3. ✅ Find latest blog post
4. ✅ Generate AI comments on post
5. ✅ Expand best comment → new post
6. ✅ Start SSH tunnel (public URL)
7. ✅ Display QR code
8. ✅ Keep running!

Press Ctrl+C to stop at any time.
    """)

    input("Press Enter to start... ")

    total_steps = 7

    # Step 1: Check prerequisites
    print_step(1, total_steps, "Checking prerequisites")
    checks = check_prerequisites()

    # Step 2: Migrate database if needed
    print_step(2, total_steps, "Ensuring database schema")
    if not checks['schema_ready']:
        print("\n🔧 Running database migration...")
        migrate_database()
    else:
        print("\n✅ Database schema ready")

    # Step 3: Ensure Flask is running
    print_step(3, total_steps, "Ensuring Flask server is running")
    if not checks['flask_running']:
        flask_ok = ensure_flask_running()
        if not flask_ok:
            print("\n⚠️  Warning: Flask may not be running")
            print("   The tunnel will still work, but blog won't be accessible")
            response = input("\nContinue anyway? [y/N]: ")
            if response.lower() != 'y':
                print("\n❌ Aborted. Start Flask with: python3 app.py")
                return

    # Step 4: Get latest post
    print_step(4, total_steps, "Finding latest blog post")
    latest_post = get_latest_post()

    if not latest_post:
        print("\n❌ No posts found in database")
        print("   Create a post first or run: python3 init_blog_posts.py")
        return

    print(f"\n✅ Found post #{latest_post['id']}: {latest_post['title']}")
    print(f"   URL: /post/{latest_post['slug']}")

    # Step 5: Generate AI comments
    print_step(5, total_steps, "Generating AI comments")

    # Check if post already has comments
    conn = get_db()
    existing_comments = conn.execute(
        'SELECT COUNT(*) as count FROM comments WHERE post_id = ?',
        (latest_post['id'],)
    ).fetchone()
    conn.close()

    if existing_comments['count'] > 0:
        print(f"\n✅ Post already has {existing_comments['count']} comment(s)")
        print("   Skipping AI comment generation")
    else:
        comments = generate_ai_comments_simple(latest_post['id'])

        if comments:
            print(f"\n✅ Generated {len(comments)} AI comment(s)")
        else:
            print("\n⚠️  No AI comments generated")
            print("   Continuing anyway...")

    # Step 6: Expand comments to posts
    print_step(6, total_steps, "Expanding comments to new posts")

    # Check for expandable comments
    check_expandable_comments(latest_post['id'])

    # Auto-expand qualifying comments
    print("\n🔄 Auto-expanding qualifying comments...")
    auto_expand_qualifying_comments(limit=3)

    # Step 7: Start tunnel
    print_step(7, total_steps, f"Starting public tunnel ({tunnel_type})")

    print("\n" + "="*70)
    print("  🚀 LAUNCHING PUBLIC TUNNEL")
    print("="*70)
    print(f"""
Tunnel type: {tunnel_type}

Your blog will be accessible at a public URL.
QR code will be displayed below.

The tunnel will stay open until you press Ctrl+C.
    """)

    input("Press Enter to start tunnel... ")

    # Start tunnel (this will run until Ctrl+C)
    url = start_tunnel(tunnel_type)

    if url:
        print("\n" + "="*70)
        print("  🎉 SUCCESS! YOUR BLOG IS LIVE!")
        print("="*70)
        print(f"\n🌍 Public URL: {url}")
        print(f"📱 Scan the QR code above with your phone")
        print(f"\n🔥 Tunnel will stay open until you press Ctrl+C")

    else:
        print("\n⚠️  Tunnel may not have started successfully")
        print("   Check output above for errors")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Stopped by user")
        print("✅ Done!")
