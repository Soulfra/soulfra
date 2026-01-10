"""
Database - SQLite (Zero Config)

Full platform database:
- users (accounts with login)
- posts (content from users and AI)
- comments (discussions on posts)
- messages (internal DMs)
- notifications (user alerts)
- subscribers (newsletter email subscriptions)

No PostgreSQL, no async/sync issues.
"""

import sqlite3
from datetime import datetime
import os

# Support sandbox testing - use SOULFRA_DB env var if set
DB_NAME = os.environ.get('SOULFRA_DB', 'soulfra.db')
DB_PATH = os.path.join(os.path.dirname(__file__), DB_NAME)


def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Return dict-like rows
    return conn


def init_db():
    """Initialize database tables for full platform"""
    conn = get_db()

    # Users table - Full user accounts (not just email subscribers)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            display_name TEXT,
            bio TEXT,
            profile_pic TEXT,
            is_admin BOOLEAN DEFAULT 0,
            is_ai_persona BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Posts table - Content from users and AI
    conn.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            content TEXT NOT NULL,
            published_at TIMESTAMP NOT NULL,
            emailed BOOLEAN DEFAULT 0,
            emailed_at TIMESTAMP,
            ai_processed BOOLEAN DEFAULT 0,
            source_post_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (source_post_id) REFERENCES posts(id)
        )
    ''')

    # Comments table - User and AI comments on posts
    conn.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            parent_comment_id INTEGER,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (parent_comment_id) REFERENCES comments(id) ON DELETE CASCADE
        )
    ''')

    # Messages table - Internal DMs between users
    conn.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_user_id INTEGER NOT NULL,
            to_user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            read BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (from_user_id) REFERENCES users(id),
            FOREIGN KEY (to_user_id) REFERENCES users(id)
        )
    ''')

    # Notifications table - User notifications
    conn.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            content TEXT NOT NULL,
            link TEXT,
            read BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Subscribers table - Newsletter email subscriptions (can be linked to user accounts)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS subscribers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            user_id INTEGER,
            confirmed BOOLEAN DEFAULT 0,
            confirmation_token TEXT,
            subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            unsubscribed_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Discussion sessions - Interactive AI discussion workspace
    conn.execute('''
        CREATE TABLE IF NOT EXISTS discussion_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            persona_name TEXT DEFAULT 'calriven',
            status TEXT DEFAULT 'active',
            draft_comment TEXT,
            final_comment_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            finalized_at TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (final_comment_id) REFERENCES comments(id)
        )
    ''')

    # Discussion messages - Chat messages in discussion sessions
    conn.execute('''
        CREATE TABLE IF NOT EXISTS discussion_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            sender TEXT NOT NULL,
            content TEXT NOT NULL,
            message_type TEXT DEFAULT 'chat',
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES discussion_sessions(id) ON DELETE CASCADE
        )
    ''')

    # Brand assets - Logos, fonts, colors, images for each brand
    conn.execute('''
        CREATE TABLE IF NOT EXISTS brand_assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand_slug TEXT NOT NULL,
            asset_type TEXT NOT NULL,
            asset_name TEXT NOT NULL,
            file_path TEXT,
            file_data BLOB,
            file_size INTEGER,
            mime_type TEXT,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Visual templates - JSON-based image templates
    conn.execute('''
        CREATE TABLE IF NOT EXISTS visual_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            brand_slug TEXT,
            template_json TEXT NOT NULL,
            preview_image BLOB,
            is_public BOOLEAN DEFAULT 0,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    ''')

    # Published images - Track image distribution across platforms
    conn.execute('''
        CREATE TABLE IF NOT EXISTS published_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_hash TEXT NOT NULL,
            image_data BLOB,
            platform TEXT NOT NULL,
            platform_id TEXT,
            platform_url TEXT,
            post_id INTEGER,
            status TEXT DEFAULT 'published',
            published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT,
            FOREIGN KEY (post_id) REFERENCES posts(id)
        )
    ''')

    # Create indexes for performance
    conn.execute('CREATE INDEX IF NOT EXISTS idx_posts_user_id ON posts(user_id)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_posts_published_at ON posts(published_at)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_comments_post_id ON comments(post_id)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_comments_user_id ON comments(user_id)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_messages_to_user ON messages(to_user_id)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_discussion_sessions_post_id ON discussion_sessions(post_id)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_discussion_messages_session_id ON discussion_messages(session_id)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_brand_assets_brand_slug ON brand_assets(brand_slug)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_brand_assets_type ON brand_assets(asset_type)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_visual_templates_brand ON visual_templates(brand_slug)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_visual_templates_category ON visual_templates(category)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_published_images_hash ON published_images(image_hash)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_published_images_platform ON published_images(platform)')

    # Add user profile columns for personality and AI friend assignment
    try:
        conn.execute('ALTER TABLE users ADD COLUMN personality_profile TEXT')
    except:
        pass  # Column already exists

    try:
        conn.execute('ALTER TABLE users ADD COLUMN ai_friend_id INTEGER')
    except:
        pass  # Column already exists

    conn.commit()
    conn.close()

    print(f"✅ Database initialized at {DB_PATH}")


def add_subscriber(email, confirmed=True):
    """Add new subscriber"""
    conn = get_db()

    try:
        conn.execute(
            'INSERT INTO subscribers (email, confirmed) VALUES (?, ?)',
            (email, 1 if confirmed else 0)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Already subscribed
        return False
    finally:
        conn.close()


def import_subscribers_csv(csv_data):
    """Import subscribers from CSV data

    Args:
        csv_data: List of dicts with 'email' key (and optional 'status')

    Returns:
        tuple: (success_count, duplicate_count, error_count)
    """
    success = 0
    duplicates = 0
    errors = 0
    conn = get_db()

    for row in csv_data:
        email = row.get('email', '').strip().lower()

        if not email:
            errors += 1
            continue

        # Basic email validation
        if '@' not in email or '.' not in email:
            errors += 1
            continue

        # Check if status indicates inactive (for Mailchimp/Substack imports)
        status = row.get('status', 'active').lower()
        is_unsubscribed = status in ('unsubscribed', 'inactive', 'no', '0', 'false')

        try:
            # Always add as confirmed, but mark as unsubscribed if needed
            conn.execute(
                'INSERT INTO subscribers (email, confirmed, unsubscribed_at) VALUES (?, 1, ?)',
                (email, datetime.now() if is_unsubscribed else None)
            )
            conn.commit()
            success += 1
        except sqlite3.IntegrityError:
            # Already exists
            duplicates += 1

    conn.close()
    return (success, duplicates, errors)


def get_subscribers():
    """Get all confirmed subscribers"""
    conn = get_db()
    subscribers = conn.execute(
        'SELECT email, subscribed_at, unsubscribed_at FROM subscribers WHERE confirmed = 1 ORDER BY subscribed_at DESC'
    ).fetchall()
    conn.close()

    return [{
        'email': row['email'],
        'subscribed_at': row['subscribed_at'],
        'active': row['unsubscribed_at'] is None
    } for row in subscribers]


def unsubscribe(email):
    """Unsubscribe email"""
    conn = get_db()
    conn.execute(
        'UPDATE subscribers SET unsubscribed_at = ? WHERE email = ?',
        (datetime.now(), email)
    )
    conn.commit()
    conn.close()


def add_post(user_id, title, slug, content, published_at):
    """Add new post"""
    conn = get_db()

    try:
        conn.execute(
            'INSERT INTO posts (user_id, title, slug, content, published_at) VALUES (?, ?, ?, ?, ?)',
            (user_id, title, slug, content, published_at)
        )
        conn.commit()

        # Get the ID of the inserted post
        post_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        return post_id
    except sqlite3.IntegrityError:
        # Slug already exists
        return None
    finally:
        conn.close()


def get_posts(limit=None):
    """Get all posts, newest first"""
    conn = get_db()

    query = 'SELECT * FROM posts ORDER BY published_at DESC'
    if limit:
        query += f' LIMIT {limit}'

    posts = conn.execute(query).fetchall()
    conn.close()

    return [dict(row) for row in posts]


def get_post_by_slug(slug):
    """Get single post by slug"""
    conn = get_db()
    post = conn.execute(
        'SELECT * FROM posts WHERE slug = ?',
        (slug,)
    ).fetchone()
    conn.close()

    return dict(post) if post else None


def mark_post_emailed(slug):
    """Mark post as emailed"""
    conn = get_db()
    conn.execute(
        'UPDATE posts SET emailed = 1, emailed_at = ? WHERE slug = ?',
        (datetime.now(), slug)
    )
    conn.commit()
    conn.close()


def mark_post_ai_processed(post_id):
    """Mark post as processed by AI"""
    conn = get_db()
    conn.execute(
        'UPDATE posts SET ai_processed = 1 WHERE id = ?',
        (post_id,)
    )
    conn.commit()
    conn.close()


def get_unprocessed_posts():
    """Get posts that haven't been processed by AI yet"""
    conn = get_db()
    posts = conn.execute(
        'SELECT * FROM posts WHERE ai_processed = 0 AND source_post_id IS NULL ORDER BY published_at DESC'
    ).fetchall()
    conn.close()

    return [dict(row) for row in posts]


def add_ai_commentary_post(original_post_id, title, slug, content):
    """Add AI-generated commentary post"""
    conn = get_db()

    try:
        conn.execute(
            'INSERT INTO posts (title, slug, content, published_at, source_post_id, ai_processed) VALUES (?, ?, ?, ?, ?, 1)',
            (title, slug, content, datetime.now(), original_post_id)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Slug already exists
        return False
    finally:
        conn.close()


def get_stats():
    """Get database stats"""
    conn = get_db()

    subscribers_count = conn.execute(
        'SELECT COUNT(*) as count FROM subscribers WHERE confirmed = 1 AND unsubscribed_at IS NULL'
    ).fetchone()['count']

    posts_count = conn.execute(
        'SELECT COUNT(*) as count FROM posts'
    ).fetchone()['count']

    conn.close()

    return {
        'subscribers': subscribers_count,
        'posts': posts_count
    }


if __name__ == '__main__':
    # Initialize database
    init_db()

    # Test add subscriber
    add_subscriber('test@example.com')

    # Test add post
    add_post(
        title='Test Post',
        slug='test-post',
        content='This is a test post.',
        published_at=datetime.now()
    )

    # Show stats
    stats = get_stats()
    print(f"📊 Stats: {stats['subscribers']} subscribers, {stats['posts']} posts")
