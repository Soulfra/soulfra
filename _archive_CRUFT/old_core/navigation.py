#!/usr/bin/env python3
"""
Navigation System - Enhanced Menu with Docs, Notifications, and User Context

Provides dynamic navigation based on user permissions and roles.
Fixes the issue where docs aren't in menus and navigation is disorganized.

Usage:
    from navigation import get_navigation, get_breadcrumbs, get_notifications

    # In Flask route
    nav = get_navigation(current_user)
    notifications = get_notifications(current_user)

    # In template
    {{ navigation.main }}
    {{ navigation.docs }}
    {{ navigation.admin }}
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import os


@dataclass
class NavItem:
    """Navigation item"""
    label: str
    url: str
    icon: Optional[str] = None
    badge: Optional[str] = None
    children: Optional[List['NavItem']] = None
    requires_auth: bool = False
    requires_admin: bool = False
    active: bool = False

    def to_dict(self) -> Dict:
        """Convert to dictionary for templates"""
        return {
            'label': self.label,
            'url': self.url,
            'icon': self.icon,
            'badge': self.badge,
            'children': [child.to_dict() for child in self.children] if self.children else None,
            'requires_auth': self.requires_auth,
            'requires_admin': self.requires_admin,
            'active': self.active
        }


class NavigationManager:
    """Manage site navigation"""

    def __init__(self):
        """Initialize navigation manager"""
        self.docs_path = os.path.dirname(os.path.abspath(__file__))

    def get_navigation(self, user: Optional[Any] = None, current_path: str = '/') -> Dict[str, List[Dict]]:
        """
        Get complete navigation structure

        Args:
            user: Current user object (or None if not logged in)
            current_path: Current URL path for active state

        Returns:
            Dict with navigation sections: main, docs, user, admin
        """
        is_authenticated = user is not None
        is_admin = user and hasattr(user, 'is_admin') and user.is_admin

        navigation = {
            'main': self._get_main_nav(current_path),
            'docs': self._get_docs_nav(current_path),
            'user': self._get_user_nav(user, current_path),
            'footer': self._get_footer_nav(current_path)
        }

        # Add admin nav if admin
        if is_admin:
            navigation['admin'] = self._get_admin_nav(current_path)

        # Filter by permissions
        navigation = self._filter_by_permissions(navigation, is_authenticated, is_admin)

        return navigation

    def _get_main_nav(self, current_path: str) -> List[Dict]:
        """Main navigation items"""
        items = [
            NavItem(
                label='Home',
                url='/',
                icon='🏠',
                active=current_path == '/'
            ),
            NavItem(
                label='Posts',
                url='/posts',
                icon='📝',
                active=current_path.startswith('/posts')
            ),
            NavItem(
                label='AI Personas',
                url='/personas',
                icon='🤖',
                active=current_path.startswith('/personas')
            ),
            NavItem(
                label='About',
                url='/about',
                icon='ℹ️',
                active=current_path == '/about'
            ),
            NavItem(
                label='Subscribe',
                url='/subscribe',
                icon='📧',
                active=current_path == '/subscribe'
            )
        ]

        return [item.to_dict() for item in items]

    def _get_docs_nav(self, current_path: str) -> List[Dict]:
        """Documentation navigation - NEW!"""
        items = [
            NavItem(
                label='Documentation',
                url='/@docs',
                icon='📚',
                children=[
                    NavItem(
                        label='Getting Started',
                        url='/@docs/hello_world_blog',
                        icon='🚀',
                        active=current_path == '/@docs/hello_world_blog'
                    ),
                    NavItem(
                        label='Network Guide',
                        url='/@docs/NETWORK_GUIDE',
                        icon='🌐',
                        active=current_path == '/@docs/NETWORK_GUIDE'
                    ),
                    NavItem(
                        label='Encryption Tiers',
                        url='/@docs/ENCRYPTION_TIERS',
                        icon='🔒',
                        active=current_path == '/@docs/ENCRYPTION_TIERS'
                    ),
                    NavItem(
                        label='Port Guide',
                        url='/@docs/PORT_GUIDE',
                        icon='🔌',
                        active=current_path == '/@docs/PORT_GUIDE'
                    ),
                    NavItem(
                        label='Launcher Guide',
                        url='/@docs/LAUNCHER_GUIDE',
                        icon='🚀',
                        active=current_path == '/@docs/LAUNCHER_GUIDE'
                    ),
                    NavItem(
                        label='Connection Map',
                        url='/@docs/connection_map',
                        icon='🗺️',
                        active=current_path == '/@docs/connection_map'
                    )
                ]
            )
        ]

        return [item.to_dict() for item in items]

    def _get_user_nav(self, user: Optional[Any], current_path: str) -> List[Dict]:
        """User-specific navigation"""
        if not user:
            # Not logged in
            items = [
                NavItem(
                    label='Login',
                    url='/login',
                    icon='🔓',
                    active=current_path == '/login'
                ),
                NavItem(
                    label='Login with QR',
                    url='/login/qr',
                    icon='📱',
                    active=current_path == '/login/qr'
                ),
                NavItem(
                    label='Register',
                    url='/register',
                    icon='✏️',
                    active=current_path == '/register'
                )
            ]
        else:
            # Logged in
            username = user.username if hasattr(user, 'username') else 'User'
            items = [
                NavItem(
                    label=f'Profile ({username})',
                    url=f'/user/{username}',
                    icon='👤',
                    active=current_path == f'/user/{username}'
                ),
                NavItem(
                    label='My Posts',
                    url='/my/posts',
                    icon='📝',
                    active=current_path == '/my/posts',
                    requires_auth=True
                ),
                NavItem(
                    label='Settings',
                    url='/settings',
                    icon='⚙️',
                    active=current_path == '/settings',
                    requires_auth=True
                ),
                NavItem(
                    label='Logout',
                    url='/logout',
                    icon='🔒',
                    active=False
                )
            ]

        return [item.to_dict() for item in items]

    def _get_admin_nav(self, current_path: str) -> List[Dict]:
        """Admin navigation"""
        items = [
            NavItem(
                label='Admin',
                url='/admin',
                icon='🔧',
                requires_admin=True,
                children=[
                    NavItem(
                        label='Dashboard',
                        url='/admin',
                        icon='📊',
                        active=current_path == '/admin',
                        requires_admin=True
                    ),
                    NavItem(
                        label='Users',
                        url='/admin/users',
                        icon='👥',
                        active=current_path == '/admin/users',
                        requires_admin=True
                    ),
                    NavItem(
                        label='Posts',
                        url='/admin/posts',
                        icon='📝',
                        active=current_path == '/admin/posts',
                        requires_admin=True
                    ),
                    NavItem(
                        label='AI Personas',
                        url='/admin/personas',
                        icon='🤖',
                        active=current_path == '/admin/personas',
                        requires_admin=True
                    ),
                    NavItem(
                        label='QR Auth Stats',
                        url='/admin/qr-stats',
                        icon='📱',
                        active=current_path == '/admin/qr-stats',
                        requires_admin=True
                    ),
                    NavItem(
                        label='System Health',
                        url='/admin/health',
                        icon='💚',
                        active=current_path == '/admin/health',
                        requires_admin=True
                    )
                ]
            )
        ]

        return [item.to_dict() for item in items]

    def _get_footer_nav(self, current_path: str) -> List[Dict]:
        """Footer navigation"""
        items = [
            NavItem(
                label='Privacy Policy',
                url='/privacy',
                active=current_path == '/privacy'
            ),
            NavItem(
                label='Terms of Service',
                url='/terms',
                active=current_path == '/terms'
            ),
            NavItem(
                label='API Docs',
                url='/api/docs',
                active=current_path == '/api/docs'
            ),
            NavItem(
                label='GitHub',
                url='https://github.com/soulfra',
                icon='💻'
            )
        ]

        return [item.to_dict() for item in items]

    def _filter_by_permissions(self, navigation: Dict, is_authenticated: bool, is_admin: bool) -> Dict:
        """Filter navigation items by user permissions"""
        filtered = {}

        for section, items in navigation.items():
            filtered_items = []

            for item in items:
                # Check permissions
                if item.get('requires_admin') and not is_admin:
                    continue
                if item.get('requires_auth') and not is_authenticated:
                    continue

                # Filter children
                if item.get('children'):
                    filtered_children = [
                        child for child in item['children']
                        if not (child.get('requires_admin') and not is_admin)
                        and not (child.get('requires_auth') and not is_authenticated)
                    ]
                    item['children'] = filtered_children if filtered_children else None

                filtered_items.append(item)

            filtered[section] = filtered_items

        return filtered

    def get_breadcrumbs(self, current_path: str) -> List[Dict]:
        """
        Generate breadcrumb navigation

        Args:
            current_path: Current URL path

        Returns:
            List of breadcrumb items
        """
        breadcrumbs = [{'label': 'Home', 'url': '/'}]

        # Parse path
        parts = current_path.strip('/').split('/')

        # Build breadcrumbs
        for i, part in enumerate(parts):
            if not part:
                continue

            # Capitalize and format
            label = part.replace('-', ' ').replace('_', ' ').title()
            url = '/' + '/'.join(parts[:i+1])

            breadcrumbs.append({
                'label': label,
                'url': url,
                'active': i == len(parts) - 1
            })

        return breadcrumbs

    def get_notifications(self, user: Optional[Any] = None) -> List[Dict]:
        """
        Get user notifications

        Args:
            user: Current user object

        Returns:
            List of notifications
        """
        if not user:
            return []

        # In production, fetch from database
        # For now, return mock notifications
        notifications = []

        # Check for new comments on user's posts
        # Check for new followers
        # Check for mentions
        # Check for system announcements

        # Mock example:
        notifications.append({
            'id': 1,
            'type': 'comment',
            'title': 'New comment on your post',
            'message': 'Someone commented on "Hello World"',
            'url': '/post/hello-world#comments',
            'timestamp': datetime.now().isoformat(),
            'read': False,
            'icon': '💬'
        })

        return notifications

    def get_unread_notification_count(self, user: Optional[Any] = None) -> int:
        """Get count of unread notifications"""
        if not user:
            return 0

        notifications = self.get_notifications(user)
        return sum(1 for n in notifications if not n.get('read', True))


# Global instance
_nav_manager = None

def get_navigation_manager() -> NavigationManager:
    """Get navigation manager singleton"""
    global _nav_manager
    if _nav_manager is None:
        _nav_manager = NavigationManager()
    return _nav_manager


def get_navigation(user: Optional[Any] = None, current_path: str = '/') -> Dict[str, List[Dict]]:
    """Helper function to get navigation"""
    manager = get_navigation_manager()
    return manager.get_navigation(user, current_path)


def get_breadcrumbs(current_path: str) -> List[Dict]:
    """Helper function to get breadcrumbs"""
    manager = get_navigation_manager()
    return manager.get_breadcrumbs(current_path)


def get_notifications(user: Optional[Any] = None) -> List[Dict]:
    """Helper function to get notifications"""
    manager = get_navigation_manager()
    return manager.get_notifications(user)


def get_notification_count(user: Optional[Any] = None) -> int:
    """Helper function to get notification count"""
    manager = get_navigation_manager()
    return manager.get_unread_notification_count(user)


# Flask integration
def init_navigation(app):
    """
    Initialize navigation for Flask app

    Usage:
        from navigation import init_navigation
        init_navigation(app)
    """
    @app.context_processor
    def inject_navigation():
        """Inject navigation into all templates"""
        from flask import request, g

        # Get current user (if using flask-login)
        user = getattr(g, 'user', None)

        # Get current path
        current_path = request.path

        # Get navigation
        nav = get_navigation(user, current_path)
        breadcrumbs = get_breadcrumbs(current_path)
        notifications = get_notifications(user)
        notification_count = get_notification_count(user)

        return {
            'navigation': nav,
            'breadcrumbs': breadcrumbs,
            'notifications': notifications,
            'notification_count': notification_count
        }


# CLI for testing
if __name__ == '__main__':
    import json

    print("Navigation System Test\n")

    # Test without user
    print("=== Guest Navigation ===")
    nav = get_navigation(user=None, current_path='/')
    print(json.dumps(nav, indent=2))
    print()

    # Test breadcrumbs
    print("=== Breadcrumbs ===")
    breadcrumbs = get_breadcrumbs('/admin/users/edit/123')
    print(json.dumps(breadcrumbs, indent=2))
    print()

    # Test with mock user
    print("=== Authenticated User Navigation ===")
    class MockUser:
        username = 'testuser'
        is_admin = False

    nav = get_navigation(user=MockUser(), current_path='/posts')
    print(json.dumps(nav, indent=2))
    print()

    # Test with admin user
    print("=== Admin Navigation ===")
    class MockAdmin:
        username = 'admin'
        is_admin = True

    nav = get_navigation(user=MockAdmin(), current_path='/admin')
    print(json.dumps(nav, indent=2))
    print()

    # Test notifications
    print("=== Notifications ===")
    notifications = get_notifications(user=MockUser())
    print(json.dumps(notifications, indent=2))
    print(f"\nUnread count: {get_notification_count(user=MockUser())}")
