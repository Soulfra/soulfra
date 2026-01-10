"""
Query Templates - Database query helper for platform stats
============================================================

Provides pre-built queries for common platform statistics.
"""

from database import get_db
from datetime import datetime, timedelta


class QueryTemplates:
    """Helper class for common database queries"""

    def __init__(self):
        self.db = get_db()

    def get_platform_stats(self, days: int = 30) -> dict:
        """
        Get comprehensive platform statistics

        Args:
            days: Number of days to look back for recent activity

        Returns:
            Dictionary with platform stats
        """
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        stats = {
            # Core content
            'total_posts': self._count('posts'),
            'total_users': self._count('users'),
            'total_comments': self._count('comments'),

            # Learning system
            'total_learning_cards': self._count('learning_cards'),
            'total_tutorials': self._count('tutorials'),
            'learning_sessions': self._count('learning_sessions'),

            # QR codes & practice
            'total_qr_codes': self._count('qr_codes'),
            'qr_scans': self._count('qr_scans'),
            'practice_rooms': self._count('practice_rooms'),

            # Games
            'dnd_games': self._count_where('games', "game_type='dnd'"),
            'cringeproof_games': self._count_where('games', "game_type='cringeproof'"),

            # Recent activity (last N days)
            'recent_posts': self._count_where('posts', f"created_at >= '{cutoff_date}'"),
            'recent_comments': self._count_where('comments', f"created_at >= '{cutoff_date}'"),
            'recent_qr_scans': self._count_where('qr_scans', f"scanned_at >= '{cutoff_date}'"),

            # Neural networks
            'neural_networks': self._count('neural_networks'),

            # Brands
            'total_brands': self._count('brands'),

            # Trading
            'active_trades': self._count_where('trades', "status='pending'"),

            # Misc
            'wiki_concepts': self._count('wiki_concepts'),
        }

        # Add derived stats
        stats['total_games'] = stats['dnd_games'] + stats['cringeproof_games']
        stats['activity_score'] = (
            stats['recent_posts'] * 5 +
            stats['recent_comments'] * 2 +
            stats['recent_qr_scans']
        )

        return stats

    def _count(self, table: str) -> int:
        """Count rows in table"""
        try:
            result = self.db.execute(f'SELECT COUNT(*) as count FROM {table}').fetchone()
            return result['count'] if result else 0
        except Exception:
            return 0

    def _count_where(self, table: str, condition: str) -> int:
        """Count rows in table with WHERE condition"""
        try:
            result = self.db.execute(f'SELECT COUNT(*) as count FROM {table} WHERE {condition}').fetchone()
            return result['count'] if result else 0
        except Exception:
            return 0

    def get_recent_activity(self, limit: int = 20) -> list:
        """
        Get recent activity across all platform features

        Returns:
            List of recent activity items sorted by timestamp
        """
        activities = []

        # Recent posts
        try:
            posts = self.db.execute('''
                SELECT 'post' as type, title, created_at, slug
                FROM posts
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,)).fetchall()
            activities.extend([dict(row) for row in posts])
        except Exception:
            pass

        # Recent comments
        try:
            comments = self.db.execute('''
                SELECT 'comment' as type, content, created_at
                FROM comments
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,)).fetchall()
            activities.extend([dict(row) for row in comments])
        except Exception:
            pass

        # Recent QR scans
        try:
            scans = self.db.execute('''
                SELECT 'qr_scan' as type, scanned_at as created_at
                FROM qr_scans
                ORDER BY scanned_at DESC
                LIMIT ?
            ''', (limit,)).fetchall()
            activities.extend([dict(row) for row in scans])
        except Exception:
            pass

        # Sort by timestamp and return top N
        activities.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return activities[:limit]
