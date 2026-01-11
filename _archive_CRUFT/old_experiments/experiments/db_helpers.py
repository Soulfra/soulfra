"""
Database Helper Functions for Full Platform
Separating these to keep database.py clean

User Functions:
- create_user()
- get_user_by_username()
- get_user_by_email()
- verify_password()
- create_ai_persona()

Comment Functions:
- add_comment()
- get_comments_for_post()
- delete_comment()

Message Functions:
- send_message()
- get_messages()
- mark_message_read()

Notification Functions:
- create_notification()
- get_notifications()
- mark_notification_read()
"""

import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db


# ==========================================
# USER FUNCTIONS
# ==========================================

def create_user(username, email, password, is_admin=False, is_ai_persona=False, display_name=None):
    """Create a new user account"""
    conn = get_db()

    password_hash = generate_password_hash(password)

    try:
        conn.execute('''
            INSERT INTO users (username, email, password_hash, display_name, is_admin, is_ai_persona)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (username, email, password_hash, display_name or username, is_admin, is_ai_persona))
        conn.commit()

        # Get the created user
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        return dict(user) if user else None
    except sqlite3.IntegrityError:
        conn.close()
        return None  # Username or email already exists


def get_user_by_username(username):
    """Get user by username"""
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    return dict(user) if user else None


def get_user_by_email(email):
    """Get user by email"""
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()
    return dict(user) if user else None


def get_user_by_id(user_id):
    """Get user by ID"""
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return dict(user) if user else None


def verify_password(user, password):
    """Verify user password"""
    return check_password_hash(user['password_hash'], password)


def create_ai_persona(username, email, display_name):
    """Create an AI persona user"""
    return create_user(
        username=username,
        email=email,
        password='ai-persona-no-password',  # AI personas don't log in
        is_ai_persona=True,
        display_name=display_name
    )


# ==========================================
# COMMENT FUNCTIONS
# ==========================================

def add_comment(post_id, user_id, content, parent_comment_id=None):
    """Add a comment to a post"""
    conn = get_db()

    conn.execute('''
        INSERT INTO comments (post_id, user_id, content, parent_comment_id)
        VALUES (?, ?, ?, ?)
    ''', (post_id, user_id, content, parent_comment_id))

    comment_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.commit()
    conn.close()

    return comment_id


def get_comments_for_post(post_id):
    """Get all comments for a post (nested structure)"""
    conn = get_db()

    comments = conn.execute('''
        SELECT c.*, u.username, u.display_name, u.is_ai_persona
        FROM comments c
        JOIN users u ON c.user_id = u.id
        WHERE c.post_id = ?
        ORDER BY c.created_at ASC
    ''', (post_id,)).fetchall()

    conn.close()

    # Convert to list of dicts
    comments_list = [dict(row) for row in comments]

    # Build nested structure
    comments_by_id = {c['id']: {**c, 'replies': []} for c in comments_list}
    root_comments = []

    for comment in comments_list:
        if comment['parent_comment_id']:
            parent = comments_by_id.get(comment['parent_comment_id'])
            if parent:
                parent['replies'].append(comments_by_id[comment['id']])
        else:
            root_comments.append(comments_by_id[comment['id']])

    return root_comments


def delete_comment(comment_id, user_id):
    """Delete a comment (only if user owns it or is admin)"""
    conn = get_db()

    # Check ownership
    comment = conn.execute('SELECT * FROM comments WHERE id = ?', (comment_id,)).fetchone()
    if not comment:
        conn.close()
        return False

    comment = dict(comment)
    if comment['user_id'] != user_id:
        # Check if user is admin
        user = get_user_by_id(user_id)
        if not user or not user['is_admin']:
            conn.close()
            return False

    conn.execute('DELETE FROM comments WHERE id = ?', (comment_id,))
    conn.commit()
    conn.close()
    return True


# ==========================================
# MESSAGE FUNCTIONS
# ==========================================

def send_message(from_user_id, to_user_id, content):
    """Send a direct message"""
    conn = get_db()

    conn.execute('''
        INSERT INTO messages (from_user_id, to_user_id, content)
        VALUES (?, ?, ?)
    ''', (from_user_id, to_user_id, content))

    message_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.commit()
    conn.close()

    # Create notification for recipient
    create_notification(
        user_id=to_user_id,
        type='new_message',
        content=f'New message from {get_user_by_id(from_user_id)["username"]}',
        link=f'/messages/{get_user_by_id(from_user_id)["username"]}'
    )

    return message_id


def get_messages(user_id, other_user_id=None):
    """Get messages for a user (optionally filtered by conversation partner)"""
    conn = get_db()

    if other_user_id:
        # Get conversation with specific user
        messages = conn.execute('''
            SELECT m.*,
                   u1.username as from_username,
                   u2.username as to_username
            FROM messages m
            JOIN users u1 ON m.from_user_id = u1.id
            JOIN users u2 ON m.to_user_id = u2.id
            WHERE (m.from_user_id = ? AND m.to_user_id = ?)
               OR (m.from_user_id = ? AND m.to_user_id = ?)
            ORDER BY m.created_at ASC
        ''', (user_id, other_user_id, other_user_id, user_id)).fetchall()
    else:
        # Get all messages for user
        messages = conn.execute('''
            SELECT m.*,
                   u1.username as from_username,
                   u2.username as to_username
            FROM messages m
            JOIN users u1 ON m.from_user_id = u1.id
            JOIN users u2 ON m.to_user_id = u2.id
            WHERE m.to_user_id = ? OR m.from_user_id = ?
            ORDER BY m.created_at DESC
        ''', (user_id, user_id)).fetchall()

    conn.close()
    return [dict(row) for row in messages]


def mark_message_read(message_id, user_id):
    """Mark a message as read"""
    conn = get_db()

    conn.execute('''
        UPDATE messages
        SET read = 1
        WHERE id = ? AND to_user_id = ?
    ''', (message_id, user_id))

    conn.commit()
    conn.close()


# ==========================================
# NOTIFICATION FUNCTIONS
# ==========================================

def create_notification(user_id, type, content, link=None):
    """Create a notification for a user"""
    conn = get_db()

    conn.execute('''
        INSERT INTO notifications (user_id, type, content, link)
        VALUES (?, ?, ?, ?)
    ''', (user_id, type, content, link))

    conn.commit()
    conn.close()


def get_notifications(user_id, unread_only=False):
    """Get notifications for a user"""
    conn = get_db()

    if unread_only:
        notifications = conn.execute('''
            SELECT * FROM notifications
            WHERE user_id = ? AND read = 0
            ORDER BY created_at DESC
        ''', (user_id,)).fetchall()
    else:
        notifications = conn.execute('''
            SELECT * FROM notifications
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 50
        ''', (user_id,)).fetchall()

    conn.close()
    return [dict(row) for row in notifications]


def mark_notification_read(notification_id, user_id):
    """Mark a notification as read"""
    conn = get_db()

    conn.execute('''
        UPDATE notifications
        SET read = 1
        WHERE id = ? AND user_id = ?
    ''', (notification_id, user_id))

    conn.commit()
    conn.close()


def get_unread_count(user_id):
    """Get count of unread notifications"""
    conn = get_db()

    count = conn.execute('''
        SELECT COUNT(*) as count
        FROM notifications
        WHERE user_id = ? AND read = 0
    ''', (user_id,)).fetchone()['count']

    conn.close()
    return count


# ==========================================
# REASONING FUNCTIONS
# ==========================================

def create_reasoning_thread(post_id, initiator_user_id, topic):
    """Create a new reasoning thread for AI debate"""
    conn = get_db()

    conn.execute('''
        INSERT INTO reasoning_threads (post_id, initiator_user_id, topic)
        VALUES (?, ?, ?)
    ''', (post_id, initiator_user_id, topic))

    thread_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.commit()
    conn.close()

    return thread_id


def add_reasoning_step(thread_id, user_id, step_number, step_type, content, confidence=0.0, parent_step_id=None, comment_id=None):
    """Add a reasoning step to a thread"""
    conn = get_db()

    conn.execute('''
        INSERT INTO reasoning_steps (thread_id, user_id, step_number, step_type, content, confidence, parent_step_id, comment_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (thread_id, user_id, step_number, step_type, content, confidence, parent_step_id, comment_id))

    step_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.commit()
    conn.close()

    return step_id


def get_reasoning_thread(post_id):
    """Get reasoning thread for a post"""
    conn = get_db()

    thread = conn.execute('''
        SELECT * FROM reasoning_threads
        WHERE post_id = ?
        ORDER BY created_at DESC
        LIMIT 1
    ''', (post_id,)).fetchone()

    conn.close()
    return dict(thread) if thread else None


def get_reasoning_steps(thread_id):
    """Get all reasoning steps for a thread"""
    conn = get_db()

    steps = conn.execute('''
        SELECT rs.*, u.username, u.display_name, u.is_ai_persona
        FROM reasoning_steps rs
        JOIN users u ON rs.user_id = u.id
        WHERE rs.thread_id = ?
        ORDER BY rs.step_number ASC
    ''', (thread_id,)).fetchall()

    conn.close()
    return [dict(row) for row in steps]


# ==========================================
# CATEGORY & TAG FUNCTIONS
# ==========================================

def get_all_categories():
    """Get all categories"""
    conn = get_db()
    categories = conn.execute('SELECT * FROM categories ORDER BY name ASC').fetchall()
    conn.close()
    return [dict(row) for row in categories]


def get_all_tags():
    """Get all tags"""
    conn = get_db()
    tags = conn.execute('SELECT * FROM tags ORDER BY name ASC').fetchall()
    conn.close()
    return [dict(row) for row in tags]


def add_category_to_post(post_id, category_id):
    """Add a category to a post"""
    conn = get_db()

    try:
        conn.execute('INSERT INTO post_categories (post_id, category_id) VALUES (?, ?)', (post_id, category_id))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


def add_tag_to_post(post_id, tag_id):
    """Add a tag to a post"""
    conn = get_db()

    try:
        conn.execute('INSERT INTO post_tags (post_id, tag_id) VALUES (?, ?)', (post_id, tag_id))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


def get_post_categories(post_id):
    """Get all categories for a post"""
    conn = get_db()

    categories = conn.execute('''
        SELECT c.* FROM categories c
        JOIN post_categories pc ON c.id = pc.category_id
        WHERE pc.post_id = ?
    ''', (post_id,)).fetchall()

    conn.close()
    return [dict(row) for row in categories]


def get_post_tags(post_id):
    """Get all tags for a post"""
    conn = get_db()

    tags = conn.execute('''
        SELECT t.* FROM tags t
        JOIN post_tags pt ON t.id = pt.tag_id
        WHERE pt.post_id = ?
    ''', (post_id,)).fetchall()

    conn.close()
    return [dict(row) for row in tags]


def get_posts_by_category(category_slug, limit=None):
    """Get posts filtered by category"""
    conn = get_db()

    query = '''
        SELECT DISTINCT p.* FROM posts p
        JOIN post_categories pc ON p.id = pc.post_id
        JOIN categories c ON pc.category_id = c.id
        WHERE c.slug = ?
        ORDER BY p.published_at DESC
    '''

    if limit:
        query += f' LIMIT {limit}'

    posts = conn.execute(query, (category_slug,)).fetchall()
    conn.close()

    return [dict(row) for row in posts]


def get_posts_by_tag(tag_slug, limit=None):
    """Get posts filtered by tag"""
    conn = get_db()

    query = '''
        SELECT DISTINCT p.* FROM posts p
        JOIN post_tags pt ON p.id = pt.post_id
        JOIN tags t ON pt.tag_id = t.id
        WHERE t.slug = ?
        ORDER BY p.published_at DESC
    '''

    if limit:
        query += f' LIMIT {limit}'

    posts = conn.execute(query, (tag_slug,)).fetchall()
    conn.close()

    return [dict(row) for row in posts]


def get_posts_by_user(user_id, limit=None):
    """Get all posts by a specific user"""
    conn = get_db()

    query = '''
        SELECT * FROM posts
        WHERE user_id = ?
        ORDER BY published_at DESC
    '''

    if limit:
        query += f' LIMIT {limit}'

    posts = conn.execute(query, (user_id,)).fetchall()
    conn.close()

    return [dict(row) for row in posts]


# ==========================================
# Avatar Functions
# ==========================================

def get_avatar_url(email, username='', is_ai_persona=False, size=80):
    """
    Get avatar URL for a user (DATABASE-FIRST)
    - FIRST: Check database for avatar image
    - FALLBACK: Generate pixel art avatar and store in database
    - LAST RESORT: External services (only if database unavailable)
    """
    import hashlib

    # DATABASE-FIRST: Check for avatar in database
    if username:
        from avatar_generator import get_avatar_url as get_db_avatar
        try:
            return get_db_avatar(username)
        except:
            pass  # Fall through to external services

    # Fallback to external services (only if database fails)
    if is_ai_persona:
        # For AI personas, use robohash for cool robot avatars
        identifier = hashlib.md5(username.encode('utf-8')).hexdigest()
        return f"https://robohash.org/{identifier}?size={size}x{size}&set=set2"
    else:
        # For humans, use Gravatar with identicon fallback
        email_hash = hashlib.md5(email.lower().strip().encode('utf-8')).hexdigest()
        return f"https://www.gravatar.com/avatar/{email_hash}?s={size}&d=identicon"
