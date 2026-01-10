"""
User Admin System
Role-based access control and user management for blog network
"""

import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
from functools import wraps
from flask import session, jsonify
import hashlib


class UserRole:
    """User roles for access control"""
    OWNER = 'owner'       # Full access to all domains
    ADMIN = 'admin'       # Manage users and content
    EDITOR = 'editor'     # Edit content on assigned domains
    VIEWER = 'viewer'     # Read-only access


class AdminSystem:
    """Manages user roles and permissions"""

    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(__file__), 'soulfra.db')
        self._ensure_admin_tables()

    def _ensure_admin_tables(self):
        """Create admin tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)

        # User roles table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS user_roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL DEFAULT 'viewer',
                granted_by INTEGER,
                granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (granted_by) REFERENCES users(id),
                UNIQUE(user_id)
            )
        ''')

        # Domain permissions table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS domain_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                domain TEXT NOT NULL,
                permission TEXT NOT NULL DEFAULT 'view',
                granted_by INTEGER,
                granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (granted_by) REFERENCES users(id),
                UNIQUE(user_id, domain)
            )
        ''')

        # Activity log table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS admin_activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                target_type TEXT,
                target_id INTEGER,
                details TEXT,
                ip_address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        conn.commit()
        conn.close()

    def get_user_role(self, user_id: int) -> str:
        """Get user's role"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        role = conn.execute('''
            SELECT role FROM user_roles WHERE user_id = ?
        ''', (user_id,)).fetchone()

        conn.close()

        if role:
            return role['role']
        return UserRole.VIEWER  # Default role

    def set_user_role(self, user_id: int, role: str, granted_by: int) -> Dict:
        """Set user's role"""
        if role not in [UserRole.OWNER, UserRole.ADMIN, UserRole.EDITOR, UserRole.VIEWER]:
            return {'error': 'Invalid role'}

        conn = sqlite3.connect(self.db_path)

        conn.execute('''
            INSERT OR REPLACE INTO user_roles (user_id, role, granted_by, granted_at)
            VALUES (?, ?, ?, ?)
        ''', (user_id, role, granted_by, datetime.now()))

        conn.commit()

        # Log action
        self.log_activity(
            user_id=granted_by,
            action='set_user_role',
            target_type='user',
            target_id=user_id,
            details=f'Role set to {role}'
        )

        conn.close()

        return {'user_id': user_id, 'role': role, 'granted_at': datetime.now().isoformat()}

    def grant_domain_permission(self, user_id: int, domain: str, permission: str, granted_by: int) -> Dict:
        """Grant user permission to a domain"""
        if permission not in ['owner', 'edit', 'view']:
            return {'error': 'Invalid permission'}

        conn = sqlite3.connect(self.db_path)

        conn.execute('''
            INSERT OR REPLACE INTO domain_permissions (user_id, domain, permission, granted_by, granted_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, domain, permission, granted_by, datetime.now()))

        conn.commit()

        # Log action
        self.log_activity(
            user_id=granted_by,
            action='grant_domain_permission',
            target_type='domain',
            target_id=user_id,
            details=f'{domain}: {permission}'
        )

        conn.close()

        return {
            'user_id': user_id,
            'domain': domain,
            'permission': permission,
            'granted_at': datetime.now().isoformat()
        }

    def revoke_domain_permission(self, user_id: int, domain: str, revoked_by: int) -> Dict:
        """Revoke user's permission to a domain"""
        conn = sqlite3.connect(self.db_path)

        conn.execute('''
            DELETE FROM domain_permissions WHERE user_id = ? AND domain = ?
        ''', (user_id, domain))

        conn.commit()

        # Log action
        self.log_activity(
            user_id=revoked_by,
            action='revoke_domain_permission',
            target_type='domain',
            target_id=user_id,
            details=f'{domain}'
        )

        conn.close()

        return {'user_id': user_id, 'domain': domain, 'revoked': True}

    def get_user_domains(self, user_id: int) -> List[Dict]:
        """Get all domains a user has access to"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        # Check if user is owner/admin (has access to all)
        role = self.get_user_role(user_id)
        if role in [UserRole.OWNER, UserRole.ADMIN]:
            domains = conn.execute('''
                SELECT domain, name, slug FROM brands
            ''').fetchall()

            conn.close()
            return [{'domain': d['domain'], 'name': d['name'], 'permission': 'owner'} for d in domains]

        # Get specific domain permissions
        domains = conn.execute('''
            SELECT dp.domain, dp.permission, b.name
            FROM domain_permissions dp
            LEFT JOIN brands b ON dp.domain = b.domain
            WHERE dp.user_id = ?
        ''', (user_id,)).fetchall()

        conn.close()

        return [{'domain': d['domain'], 'name': d['name'], 'permission': d['permission']} for d in domains]

    def can_user_access_domain(self, user_id: int, domain: str, required_permission: str = 'view') -> bool:
        """Check if user can access a domain"""
        role = self.get_user_role(user_id)

        # Owners and admins have full access
        if role in [UserRole.OWNER, UserRole.ADMIN]:
            return True

        # Check domain-specific permission
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        permission = conn.execute('''
            SELECT permission FROM domain_permissions
            WHERE user_id = ? AND domain = ?
        ''', (user_id, domain)).fetchone()

        conn.close()

        if not permission:
            return False

        # Permission hierarchy: owner > edit > view
        permissions_hierarchy = {'owner': 3, 'edit': 2, 'view': 1}
        user_level = permissions_hierarchy.get(permission['permission'], 0)
        required_level = permissions_hierarchy.get(required_permission, 0)

        return user_level >= required_level

    def log_activity(self, user_id: int, action: str, target_type: str = None,
                    target_id: int = None, details: str = None, ip_address: str = None):
        """Log admin activity"""
        conn = sqlite3.connect(self.db_path)

        conn.execute('''
            INSERT INTO admin_activity_log (user_id, action, target_type, target_id, details, ip_address)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, action, target_type, target_id, details, ip_address))

        conn.commit()
        conn.close()

    def get_activity_log(self, limit: int = 100, user_id: int = None) -> List[Dict]:
        """Get recent admin activity"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        if user_id:
            logs = conn.execute('''
                SELECT al.*, u.username
                FROM admin_activity_log al
                LEFT JOIN users u ON al.user_id = u.id
                WHERE al.user_id = ?
                ORDER BY al.created_at DESC
                LIMIT ?
            ''', (user_id, limit)).fetchall()
        else:
            logs = conn.execute('''
                SELECT al.*, u.username
                FROM admin_activity_log al
                LEFT JOIN users u ON al.user_id = u.id
                ORDER BY al.created_at DESC
                LIMIT ?
            ''', (limit,)).fetchall()

        conn.close()

        return [dict(log) for log in logs]

    def get_all_users(self) -> List[Dict]:
        """Get all users with their roles"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        users = conn.execute('''
            SELECT u.id, u.username, u.email, u.created_at,
                   COALESCE(ur.role, 'viewer') as role
            FROM users u
            LEFT JOIN user_roles ur ON u.id = ur.user_id
            ORDER BY u.created_at DESC
        ''').fetchall()

        conn.close()

        return [dict(user) for user in users]


# Decorators for role-based access control
def require_role(required_role: str):
    """Decorator to require a specific role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({'error': 'Authentication required'}), 401

            admin = AdminSystem()
            user_role = admin.get_user_role(session['user_id'])

            role_hierarchy = {
                UserRole.OWNER: 4,
                UserRole.ADMIN: 3,
                UserRole.EDITOR: 2,
                UserRole.VIEWER: 1
            }

            if role_hierarchy.get(user_role, 0) < role_hierarchy.get(required_role, 0):
                return jsonify({'error': 'Insufficient permissions'}), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_domain_access(domain_param: str = 'domain', permission: str = 'view'):
    """Decorator to require domain-specific access"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({'error': 'Authentication required'}), 401

            # Get domain from request
            from flask import request
            domain = request.json.get(domain_param) if request.is_json else request.args.get(domain_param)

            if not domain:
                return jsonify({'error': f'{domain_param} required'}), 400

            admin = AdminSystem()
            if not admin.can_user_access_domain(session['user_id'], domain, permission):
                return jsonify({'error': 'Access denied to this domain'}), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator
