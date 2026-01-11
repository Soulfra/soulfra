#!/usr/bin/env python3
"""
Notification System - Real-time notifications with bell icon and badge

Provides:
- In-app notifications (comments, mentions, follows)
- Badge count in navigation
- Mark as read/unread
- Notification types (comment, mention, follow, system)
- Database storage

Usage:
    from notifications import NotificationManager

    # Create notification
    nm = NotificationManager()
    nm.create_notification(
        user_id=1,
        type='comment',
        title='New comment',
        message='Someone commented on your post',
        url='/post/hello-world#comments'
    )

    # Get notifications
    notifications = nm.get_user_notifications(user_id=1, unread_only=True)

    # Mark as read
    nm.mark_as_read(notification_id=1)
"""

from database import get_db
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class Notification:
    """Notification data class"""
    id: int
    user_id: int
    type: str  # comment, mention, follow, like, system
    title: str
    message: str
    url: Optional[str]
    icon: str
    read: bool
    created_at: datetime

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type,
            'title': self.title,
            'message': self.message,
            'url': self.url,
            'icon': self.icon,
            'read': self.read,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'time_ago': self._time_ago()
        }

    def _time_ago(self) -> str:
        """Human-readable time ago"""
        if not isinstance(self.created_at, datetime):
            try:
                created = datetime.fromisoformat(str(self.created_at).replace('Z', '+00:00'))
            except:
                return 'recently'
        else:
            created = self.created_at

        now = datetime.now()
        diff = now - created

        if diff.total_seconds() < 60:
            return 'just now'
        elif diff.total_seconds() < 3600:
            minutes = int(diff.total_seconds() / 60)
            return f'{minutes}m ago'
        elif diff.total_seconds() < 86400:
            hours = int(diff.total_seconds() / 3600)
            return f'{hours}h ago'
        elif diff.days < 7:
            return f'{diff.days}d ago'
        elif diff.days < 30:
            weeks = diff.days // 7
            return f'{weeks}w ago'
        else:
            months = diff.days // 30
            return f'{months}mo ago'


class NotificationManager:
    """Manage notifications"""

    # Notification type to icon mapping
    TYPE_ICONS = {
        'comment': '💬',
        'mention': '@',
        'follow': '👤',
        'like': '❤️',
        'system': '🔔',
        'qr_auth': '📱',
        'post': '📝',
        'ai': '🤖'
    }

    def __init__(self):
        """Initialize notification manager"""
        self.init_database()

    def init_database(self):
        """Create notifications table if not exists"""
        db = get_db()

        db.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                url TEXT,
                icon TEXT,
                read BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')

        # Create index for faster queries
        db.execute('''
            CREATE INDEX IF NOT EXISTS idx_notifications_user_read
            ON notifications(user_id, read)
        ''')

        db.execute('''
            CREATE INDEX IF NOT EXISTS idx_notifications_created
            ON notifications(created_at DESC)
        ''')

        db.commit()

    def create_notification(self, user_id: int, type: str, title: str,
                          message: str, url: Optional[str] = None,
                          icon: Optional[str] = None) -> int:
        """
        Create notification

        Args:
            user_id: User to notify
            type: Notification type (comment, mention, follow, etc.)
            title: Notification title
            message: Notification message
            url: Optional URL to link to
            icon: Optional custom icon (defaults to type icon)

        Returns:
            Notification ID
        """
        db = get_db()

        # Use default icon if not provided
        if icon is None:
            icon = self.TYPE_ICONS.get(type, '🔔')

        cursor = db.execute('''
            INSERT INTO notifications (user_id, type, title, message, url, icon, read)
            VALUES (?, ?, ?, ?, ?, ?, 0)
        ''', (user_id, type, title, message, url, icon))

        db.commit()

        return cursor.lastrowid

    def get_user_notifications(self, user_id: int, unread_only: bool = False,
                               limit: int = 50) -> List[Notification]:
        """
        Get notifications for user

        Args:
            user_id: User ID
            unread_only: Only return unread notifications
            limit: Maximum number to return

        Returns:
            List of Notification objects
        """
        db = get_db()

        if unread_only:
            query = '''
                SELECT * FROM notifications
                WHERE user_id = ? AND read = 0
                ORDER BY created_at DESC
                LIMIT ?
            '''
        else:
            query = '''
                SELECT * FROM notifications
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            '''

        rows = db.execute(query, (user_id, limit)).fetchall()

        notifications = []
        for row in rows:
            notifications.append(Notification(
                id=row['id'],
                user_id=row['user_id'],
                type=row['type'],
                title=row['title'],
                message=row['message'],
                url=row['url'],
                icon=row['icon'],
                read=bool(row['read']),
                created_at=row['created_at']
            ))

        return notifications

    def get_unread_count(self, user_id: int) -> int:
        """
        Get count of unread notifications

        Args:
            user_id: User ID

        Returns:
            Count of unread notifications
        """
        db = get_db()

        row = db.execute('''
            SELECT COUNT(*) as count FROM notifications
            WHERE user_id = ? AND read = 0
        ''', (user_id,)).fetchone()

        return row['count'] if row else 0

    def mark_as_read(self, notification_id: int, user_id: Optional[int] = None) -> bool:
        """
        Mark notification as read

        Args:
            notification_id: Notification ID
            user_id: Optional user ID for security check

        Returns:
            True if marked, False if not found
        """
        db = get_db()

        if user_id:
            # Verify user owns notification
            result = db.execute('''
                UPDATE notifications
                SET read = 1
                WHERE id = ? AND user_id = ?
            ''', (notification_id, user_id))
        else:
            result = db.execute('''
                UPDATE notifications
                SET read = 1
                WHERE id = ?
            ''', (notification_id,))

        db.commit()

        return result.rowcount > 0

    def mark_all_as_read(self, user_id: int) -> int:
        """
        Mark all notifications as read for user

        Args:
            user_id: User ID

        Returns:
            Number of notifications marked as read
        """
        db = get_db()

        result = db.execute('''
            UPDATE notifications
            SET read = 1
            WHERE user_id = ? AND read = 0
        ''', (user_id,))

        db.commit()

        return result.rowcount

    def delete_notification(self, notification_id: int, user_id: Optional[int] = None) -> bool:
        """
        Delete notification

        Args:
            notification_id: Notification ID
            user_id: Optional user ID for security check

        Returns:
            True if deleted, False if not found
        """
        db = get_db()

        if user_id:
            result = db.execute('''
                DELETE FROM notifications
                WHERE id = ? AND user_id = ?
            ''', (notification_id, user_id))
        else:
            result = db.execute('''
                DELETE FROM notifications
                WHERE id = ?
            ''', (notification_id,))

        db.commit()

        return result.rowcount > 0

    def delete_old_notifications(self, days: int = 30) -> int:
        """
        Delete notifications older than X days

        Args:
            days: Delete notifications older than this many days

        Returns:
            Number of notifications deleted
        """
        db = get_db()

        cutoff_date = datetime.now() - timedelta(days=days)

        result = db.execute('''
            DELETE FROM notifications
            WHERE created_at < ? AND read = 1
        ''', (cutoff_date,))

        db.commit()

        return result.rowcount

    def get_notification_by_id(self, notification_id: int, user_id: Optional[int] = None) -> Optional[Notification]:
        """
        Get single notification by ID

        Args:
            notification_id: Notification ID
            user_id: Optional user ID for security check

        Returns:
            Notification object or None
        """
        db = get_db()

        if user_id:
            query = 'SELECT * FROM notifications WHERE id = ? AND user_id = ?'
            row = db.execute(query, (notification_id, user_id)).fetchone()
        else:
            query = 'SELECT * FROM notifications WHERE id = ?'
            row = db.execute(query, (notification_id,)).fetchone()

        if not row:
            return None

        return Notification(
            id=row['id'],
            user_id=row['user_id'],
            type=row['type'],
            title=row['title'],
            message=row['message'],
            url=row['url'],
            icon=row['icon'],
            read=bool(row['read']),
            created_at=row['created_at']
        )

    def create_comment_notification(self, user_id: int, post_title: str,
                                   commenter_name: str, post_slug: str) -> int:
        """Helper: Create notification for new comment"""
        return self.create_notification(
            user_id=user_id,
            type='comment',
            title='New comment',
            message=f'{commenter_name} commented on "{post_title}"',
            url=f'/post/{post_slug}#comments'
        )

    def create_mention_notification(self, user_id: int, mentioned_by: str,
                                   post_slug: str) -> int:
        """Helper: Create notification for mention"""
        return self.create_notification(
            user_id=user_id,
            type='mention',
            title='You were mentioned',
            message=f'{mentioned_by} mentioned you in a post',
            url=f'/post/{post_slug}'
        )

    def create_follow_notification(self, user_id: int, follower_name: str) -> int:
        """Helper: Create notification for new follower"""
        return self.create_notification(
            user_id=user_id,
            type='follow',
            title='New follower',
            message=f'{follower_name} started following you',
            url=f'/user/{follower_name}'
        )

    def create_qr_auth_notification(self, user_id: int, device_info: str) -> int:
        """Helper: Create notification for QR auth login"""
        return self.create_notification(
            user_id=user_id,
            type='qr_auth',
            title='New login via QR code',
            message=f'Logged in from {device_info}',
            url='/settings/security'
        )

    def create_system_notification(self, user_id: int, title: str, message: str,
                                  url: Optional[str] = None) -> int:
        """Helper: Create system notification"""
        return self.create_notification(
            user_id=user_id,
            type='system',
            title=title,
            message=message,
            url=url
        )


# Flask integration
def init_notifications_routes(app):
    """
    Add notification routes to Flask app

    Usage:
        from notifications import init_notifications_routes
        init_notifications_routes(app)
    """
    from flask import jsonify, request, g

    nm = NotificationManager()

    @app.route('/api/notifications')
    def api_get_notifications():
        """Get user notifications"""
        user = getattr(g, 'user', None)
        if not user:
            return jsonify({'error': 'Unauthorized'}), 401

        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        limit = int(request.args.get('limit', 50))

        notifications = nm.get_user_notifications(user.id, unread_only, limit)

        return jsonify({
            'notifications': [n.to_dict() for n in notifications],
            'unread_count': nm.get_unread_count(user.id)
        })

    @app.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
    def api_mark_notification_read(notification_id):
        """Mark notification as read"""
        user = getattr(g, 'user', None)
        if not user:
            return jsonify({'error': 'Unauthorized'}), 401

        success = nm.mark_as_read(notification_id, user.id)

        return jsonify({'success': success})

    @app.route('/api/notifications/read-all', methods=['POST'])
    def api_mark_all_read():
        """Mark all notifications as read"""
        user = getattr(g, 'user', None)
        if not user:
            return jsonify({'error': 'Unauthorized'}), 401

        count = nm.mark_all_as_read(user.id)

        return jsonify({'count': count})

    @app.route('/api/notifications/<int:notification_id>', methods=['DELETE'])
    def api_delete_notification(notification_id):
        """Delete notification"""
        user = getattr(g, 'user', None)
        if not user:
            return jsonify({'error': 'Unauthorized'}), 401

        success = nm.delete_notification(notification_id, user.id)

        return jsonify({'success': success})


# CLI for testing
if __name__ == '__main__':
    import sys

    nm = NotificationManager()

    print("Notification System\n")

    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        # Create test notifications
        print("Creating test notifications...")

        # Mock user ID
        user_id = 1

        nm.create_comment_notification(
            user_id=user_id,
            post_title='Hello World',
            commenter_name='John Doe',
            post_slug='hello-world'
        )

        nm.create_mention_notification(
            user_id=user_id,
            mentioned_by='Jane Smith',
            post_slug='test-post'
        )

        nm.create_follow_notification(
            user_id=user_id,
            follower_name='Alice'
        )

        nm.create_qr_auth_notification(
            user_id=user_id,
            device_info='iPhone 14 (Safari)'
        )

        print(f"✓ Created 4 test notifications for user {user_id}\n")

        # Get notifications
        notifications = nm.get_user_notifications(user_id)
        unread_count = nm.get_unread_count(user_id)

        print(f"Total notifications: {len(notifications)}")
        print(f"Unread: {unread_count}\n")

        for notif in notifications:
            read_indicator = '  ' if notif.read else '🔴'
            print(f"{read_indicator} {notif.icon} {notif.title}")
            print(f"   {notif.message}")
            print(f"   {notif.to_dict()['time_ago']}")
            if notif.url:
                print(f"   → {notif.url}")
            print()

    else:
        print("Usage:")
        print("  python3 notifications.py test    # Create test notifications")
