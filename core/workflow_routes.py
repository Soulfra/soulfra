"""
Flask routes for automation workflows
Provides API endpoints for triggering and managing automated tasks
"""

from flask import jsonify, request, session, render_template
from automation_workflows import WorkflowAutomation, WorkflowScheduler
from functools import wraps


def require_auth(f):
    """Decorator to require authentication for workflow endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function


def register_workflow_routes(app):
    """Register workflow automation routes"""

    workflows = WorkflowAutomation()
    scheduler = WorkflowScheduler()

    @app.route('/workflows')
    @require_auth
    def workflows_dashboard():
        """Dashboard for managing workflows"""
        return render_template('workflows_dashboard.html')

    @app.route('/api/workflows/auto-syndicate', methods=['POST'])
    @require_auth
    def api_auto_syndicate():
        """Auto-syndicate recent posts"""
        data = request.json or {}
        hours_back = data.get('hours_back', 24)

        result = workflows.auto_syndicate_new_posts(hours_back=hours_back)
        return jsonify(result)

    @app.route('/api/workflows/weekly-summary', methods=['POST'])
    @require_auth
    def api_weekly_summary():
        """Generate weekly summary with Claude"""
        data = request.json or {}
        domain = data.get('domain', 'soulfra.com')

        result = workflows.generate_weekly_summary(domain=domain)
        return jsonify(result)

    @app.route('/api/workflows/optimize-post', methods=['POST'])
    @require_auth
    def api_optimize_post():
        """Optimize a post with AI"""
        data = request.json or {}

        if 'post_id' not in data:
            return jsonify({'error': 'post_id required'}), 400

        post_id = data['post_id']
        task = data.get('task', 'improve_seo')

        result = workflows.optimize_post_with_ai(post_id, task)
        return jsonify(result)

    @app.route('/api/workflows/schedule-publish', methods=['POST'])
    @require_auth
    def api_schedule_publish():
        """Schedule a post for future publication"""
        data = request.json or {}

        if 'post_id' not in data or 'publish_at' not in data:
            return jsonify({'error': 'post_id and publish_at required'}), 400

        from datetime import datetime
        post_id = data['post_id']
        publish_at = datetime.fromisoformat(data['publish_at'])

        result = workflows.schedule_publish(post_id, publish_at)
        return jsonify(result)

    @app.route('/api/workflows/bulk-tag', methods=['POST'])
    @require_auth
    def api_bulk_tag():
        """Bulk tag posts in a domain"""
        data = request.json or {}

        if 'domain' not in data or 'tags' not in data:
            return jsonify({'error': 'domain and tags required'}), 400

        domain = data['domain']
        tags = data['tags']  # Should be a list

        result = workflows.bulk_tag_posts(domain, tags)
        return jsonify(result)

    @app.route('/api/workflows/run-daily', methods=['POST'])
    @require_auth
    def api_run_daily_tasks():
        """Run all daily automated tasks"""
        result = scheduler.run_daily_tasks()
        return jsonify(result)

    @app.route('/api/workflows/run-weekly', methods=['POST'])
    @require_auth
    def api_run_weekly_tasks():
        """Run all weekly automated tasks"""
        result = scheduler.run_weekly_tasks()
        return jsonify(result)

    print("✅ Registered workflow automation routes")
