"""
Flask routes for admin dashboard
User management, roles, and permissions
"""

from flask import jsonify, request, session, render_template, redirect, url_for
from admin_system import AdminSystem, UserRole, require_role, require_domain_access


def register_admin_routes(app):
    """Register admin dashboard routes"""

    admin = AdminSystem()

    @app.route('/admin')
    @require_role(UserRole.ADMIN)
    def admin_dashboard():
        """Admin dashboard homepage"""
        return render_template('admin_dashboard.html')

    @app.route('/admin/users')
    @require_role(UserRole.ADMIN)
    def admin_users():
        """User management page"""
        users = admin.get_all_users()
        return render_template('admin_users.html', users=users)

    @app.route('/api/admin/users', methods=['GET'])
    @require_role(UserRole.ADMIN)
    def api_admin_get_users():
        """Get all users with roles"""
        users = admin.get_all_users()
        return jsonify({'users': users})

    @app.route('/api/admin/users/<int:user_id>/role', methods=['POST'])
    @require_role(UserRole.ADMIN)
    def api_admin_set_role(user_id):
        """Set user's role"""
        data = request.json or {}

        if 'role' not in data:
            return jsonify({'error': 'role required'}), 400

        result = admin.set_user_role(
            user_id=user_id,
            role=data['role'],
            granted_by=session['user_id']
        )

        if 'error' in result:
            return jsonify(result), 400

        return jsonify(result)

    @app.route('/api/admin/users/<int:user_id>/domains', methods=['GET'])
    @require_role(UserRole.ADMIN)
    def api_admin_get_user_domains(user_id):
        """Get user's domain permissions"""
        domains = admin.get_user_domains(user_id)
        return jsonify({'user_id': user_id, 'domains': domains})

    @app.route('/api/admin/domains/grant', methods=['POST'])
    @require_role(UserRole.ADMIN)
    def api_admin_grant_domain():
        """Grant domain permission to user"""
        data = request.json or {}

        required = ['user_id', 'domain', 'permission']
        if not all(field in data for field in required):
            return jsonify({'error': f'{", ".join(required)} required'}), 400

        result = admin.grant_domain_permission(
            user_id=data['user_id'],
            domain=data['domain'],
            permission=data['permission'],
            granted_by=session['user_id']
        )

        if 'error' in result:
            return jsonify(result), 400

        return jsonify(result)

    @app.route('/api/admin/domains/revoke', methods=['POST'])
    @require_role(UserRole.ADMIN)
    def api_admin_revoke_domain():
        """Revoke domain permission from user"""
        data = request.json or {}

        if 'user_id' not in data or 'domain' not in data:
            return jsonify({'error': 'user_id and domain required'}), 400

        result = admin.revoke_domain_permission(
            user_id=data['user_id'],
            domain=data['domain'],
            revoked_by=session['user_id']
        )

        return jsonify(result)

    @app.route('/api/admin/activity', methods=['GET'])
    @require_role(UserRole.ADMIN)
    def api_admin_activity_log():
        """Get admin activity log"""
        limit = request.args.get('limit', 100, type=int)
        user_id = request.args.get('user_id', type=int)

        logs = admin.get_activity_log(limit=limit, user_id=user_id)
        return jsonify({'logs': logs})

    @app.route('/api/admin/check-access', methods=['POST'])
    def api_admin_check_access():
        """Check if current user can access a domain"""
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401

        data = request.json or {}
        domain = data.get('domain')
        permission = data.get('permission', 'view')

        if not domain:
            return jsonify({'error': 'domain required'}), 400

        has_access = admin.can_user_access_domain(
            user_id=session['user_id'],
            domain=domain,
            required_permission=permission
        )

        return jsonify({
            'user_id': session['user_id'],
            'domain': domain,
            'permission': permission,
            'has_access': has_access
        })

    @app.route('/api/admin/my-role', methods=['GET'])
    def api_admin_my_role():
        """Get current user's role"""
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401

        role = admin.get_user_role(session['user_id'])
        domains = admin.get_user_domains(session['user_id'])

        return jsonify({
            'user_id': session['user_id'],
            'role': role,
            'domains': domains
        })

    print("✅ Registered admin system routes")
