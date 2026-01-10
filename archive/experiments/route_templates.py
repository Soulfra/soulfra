#!/usr/bin/env python3
"""
Route Templates - Reusable Flask Route Patterns

Like query templates for SQL, but for Flask routes. Generate entire features
from templates in seconds.

Philosophy:
-----------
Don't repeat route patterns. Define them once, generate many times.

Usage:
    from route_templates import RouteTemplate

    # Generate CRUD routes
    crud = RouteTemplate.crud('newsletter', ['email', 'brand', 'verified'])
    print(crud.flask_code)  # Python code for routes
    print(crud.html_template)  # HTML template code
    print(crud.test_code)  # Test code

    # Generate API endpoint
    api = RouteTemplate.api_endpoint('comments', 'brand_slug')
    print(api.flask_code)

    # Generate dashboard
    dashboard = RouteTemplate.dashboard('analytics', ['api_calls', 'users'])
    print(dashboard.flask_code)
"""

from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class GeneratedRoute:
    """Container for generated route code"""
    name: str
    flask_code: str
    html_template: str
    test_code: str
    url_path: str


class RouteTemplate:
    """
    Generate Flask routes from templates

    Provides reusable patterns for common route types.
    """

    @staticmethod
    def crud(
        resource_name: str,
        fields: List[str],
        require_auth: bool = False
    ) -> GeneratedRoute:
        """
        Generate complete CRUD routes for a resource

        Args:
            resource_name: Name of resource (e.g., 'newsletter', 'user')
            fields: List of field names
            require_auth: Require login for access

        Returns:
            GeneratedRoute with all code

        Example:
            >>> crud = RouteTemplate.crud('newsletter', ['email', 'brand'])
            >>> print(crud.flask_code)
            @app.route('/newsletter')
            def newsletter_list():
                ...
        """
        singular = resource_name.rstrip('s')
        plural = resource_name if resource_name.endswith('s') else resource_name + 's'

        # Flask routes code
        flask_code = f'''
# ==============================================================================
# {resource_name.upper()} CRUD ROUTES
# ==============================================================================

@app.route('/{plural}')
def {singular}_list():
    """List all {plural}"""
    {'if not session.get("user_id"): return redirect(url_for("login"))' if require_auth else ''}

    from database import get_db
    conn = get_db()
    items = conn.execute('SELECT * FROM {plural} ORDER BY id DESC').fetchall()
    conn.close()

    return render_template('{plural}/list.html', items=items)


@app.route('/{plural}/create', methods=['GET', 'POST'])
def {singular}_create():
    """Create new {singular}"""
    {'if not session.get("user_id"): return redirect(url_for("login"))' if require_auth else ''}

    if request.method == 'POST':
        from database import get_db
        conn = get_db()

        # Get form data
        {chr(10).join(f"        {field} = request.form.get('{field}')" for field in fields)}

        # Insert
        conn.execute(f"""
            INSERT INTO {plural} ({', '.join(fields)})
            VALUES ({', '.join('?' for _ in fields)})
        """, ({', '.join(fields)}))
        conn.commit()
        conn.close()

        flash('{singular.title()} created successfully!', 'success')
        return redirect(url_for('{singular}_list'))

    return render_template('{plural}/create.html')


@app.route('/{plural}/<int:id>')
def {singular}_view(id):
    """View single {singular}"""
    from database import get_db
    conn = get_db()
    item = conn.execute('SELECT * FROM {plural} WHERE id = ?', (id,)).fetchone()
    conn.close()

    if not item:
        flash('{singular.title()} not found', 'error')
        return redirect(url_for('{singular}_list'))

    return render_template('{plural}/view.html', item=item)


@app.route('/{plural}/<int:id>/edit', methods=['GET', 'POST'])
def {singular}_edit(id):
    """Edit {singular}"""
    {'if not session.get("user_id"): return redirect(url_for("login"))' if require_auth else ''}

    from database import get_db
    conn = get_db()

    if request.method == 'POST':
        # Get form data
        {chr(10).join(f"        {field} = request.form.get('{field}')" for field in fields)}

        # Update
        conn.execute(f"""
            UPDATE {plural}
            SET {', '.join(f'{field} = ?' for field in fields)}
            WHERE id = ?
        """, ({', '.join(fields)}, id))
        conn.commit()
        conn.close()

        flash('{singular.title()} updated successfully!', 'success')
        return redirect(url_for('{singular}_view', id=id))

    item = conn.execute('SELECT * FROM {plural} WHERE id = ?', (id,)).fetchone()
    conn.close()

    if not item:
        flash('{singular.title()} not found', 'error')
        return redirect(url_for('{singular}_list'))

    return render_template('{plural}/edit.html', item=item)


@app.route('/{plural}/<int:id>/delete', methods=['POST'])
def {singular}_delete(id):
    """Delete {singular}"""
    {'if not session.get("user_id"): return redirect(url_for("login"))' if require_auth else ''}

    from database import get_db
    conn = get_db()
    conn.execute('DELETE FROM {plural} WHERE id = ?', (id,))
    conn.commit()
    conn.close()

    flash('{singular.title()} deleted successfully!', 'success')
    return redirect(url_for('{singular}_list'))
'''

        # HTML template code
        html_template = f'''
<!-- templates/{plural}/list.html -->
{{% extends "base.html" %}}

{{% block title %}}{plural.title()}{{% endblock %}}

{{% block content %}}
<div class="container">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
        <h1>{plural.title()}</h1>
        <a href="{{{{ url_for('{singular}_create') }}}}" class="button">Create New {singular.title()}</a>
    </div>

    {{% if items %}}
    <table style="width: 100%; border-collapse: collapse;">
        <thead>
            <tr>
                <th>ID</th>
                {chr(10).join(f'                <th>{field.title()}</th>' for field in fields)}
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            {{% for item in items %}}
            <tr>
                <td>{{{{ item.id }}}}</td>
                {chr(10).join(f'                <td>{{{{ item.{field} }}}}</td>' for field in fields)}
                <td>
                    <a href="{{{{ url_for('{singular}_view', id=item.id) }}}}">View</a>
                    <a href="{{{{ url_for('{singular}_edit', id=item.id) }}}}">Edit</a>
                    <form action="{{{{ url_for('{singular}_delete', id=item.id) }}}}" method="POST" style="display: inline;">
                        <button type="submit" onclick="return confirm('Delete this {singular}?')">Delete</button>
                    </form>
                </td>
            </tr>
            {{% endfor %}}
        </tbody>
    </table>
    {{% else %}}
    <p>No {plural} yet. <a href="{{{{ url_for('{singular}_create') }}}}">Create one</a></p>
    {{% endif %}}
</div>
{{% endblock %}}
'''

        # Test code
        test_code = f'''
# test_{plural}.py
import pytest
from app import app
from database import get_db

def test_{singular}_list():
    """Test listing {plural}"""
    with app.test_client() as client:
        response = client.get('/{plural}')
        assert response.status_code == 200
        assert b'{plural.title()}' in response.data

def test_{singular}_create():
    """Test creating {singular}"""
    with app.test_client() as client:
        response = client.post('/{plural}/create', data={{
            {chr(10).join(f"            '{field}': 'test_{field}'," for field in fields)}
        }}, follow_redirects=True)
        assert response.status_code == 200
'''

        return GeneratedRoute(
            name=resource_name,
            flask_code=flask_code,
            html_template=html_template,
            test_code=test_code,
            url_path=f'/{plural}'
        )

    @staticmethod
    def api_endpoint(
        resource_name: str,
        path_param: Optional[str] = None,
        methods: List[str] = ['GET', 'POST']
    ) -> GeneratedRoute:
        """
        Generate API endpoint routes

        Args:
            resource_name: API resource (e.g., 'comments', 'users')
            path_param: Optional path parameter (e.g., 'brand_slug')
            methods: HTTP methods to support

        Returns:
            GeneratedRoute with API code

        Example:
            >>> api = RouteTemplate.api_endpoint('comments', 'brand_slug')
            >>> print(api.flask_code)
        """
        path = f'/api/v1/{resource_name}'
        if path_param:
            path += f'/<{path_param}>'

        flask_code = f'''
# API endpoint for {resource_name}
@app.route('{path}', methods={methods})
def api_{resource_name.replace('/', '_')}({path_param or ''}):
    """API endpoint for {resource_name}"""

    if request.method == 'GET':
        from database import get_db
        conn = get_db()
        results = conn.execute('SELECT * FROM {resource_name}').fetchall()
        conn.close()

        return jsonify({{
            'success': True,
            'data': [dict(r) for r in results]
        }})

    elif request.method == 'POST':
        data = request.get_json()

        # Validate data
        if not data:
            return jsonify({{'error': 'No data provided'}}), 400

        # Process request
        from database import get_db
        conn = get_db()
        # Add your logic here
        conn.close()

        return jsonify({{'success': True}}), 201
'''

        test_code = f'''
def test_api_{resource_name.replace('/', '_')}_get():
    """Test GET {path}"""
    with app.test_client() as client:
        response = client.get('{path}')
        assert response.status_code == 200
        data = response.get_json()
        assert 'data' in data
'''

        return GeneratedRoute(
            name=f'api_{resource_name}',
            flask_code=flask_code,
            html_template='',  # APIs don't have templates
            test_code=test_code,
            url_path=path
        )

    @staticmethod
    def dashboard(
        name: str,
        stats_queries: List[str]
    ) -> GeneratedRoute:
        """
        Generate dashboard page

        Args:
            name: Dashboard name (e.g., 'analytics', 'admin')
            stats_queries: List of stats to display

        Returns:
            GeneratedRoute with dashboard code

        Example:
            >>> dash = RouteTemplate.dashboard('analytics', ['total_users', 'api_calls'])
            >>> print(dash.flask_code)
        """
        flask_code = f'''
@app.route('/{name}')
def {name}_dashboard():
    """{name.title()} Dashboard"""
    from database import get_db
    conn = get_db()

    stats = {{}}
    {chr(10).join(f"    stats['{stat}'] = conn.execute('SELECT COUNT(*) FROM {stat}').fetchone()[0]" for stat in stats_queries)}

    conn.close()

    return render_template('{name}_dashboard.html', stats=stats)
'''

        html_template = f'''
{{% extends "base.html" %}}

{{% block title %}}{name.title()} Dashboard{{% endblock %}}

{{% block content %}}
<div class="dashboard">
    <h1>{name.title()} Dashboard</h1>

    <div class="stats-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 2rem 0;">
        {chr(10).join(f'''        <div class="stat-card" style="background: #f5f5f5; padding: 20px; border-radius: 8px;">
            <h3>{stat.replace('_', ' ').title()}</h3>
            <div class="stat-value" style="font-size: 32px; font-weight: bold; color: #667eea;">{{{{ stats.{stat} }}}}</div>
        </div>''' for stat in stats_queries)}
    </div>
</div>
{{% endblock %}}
'''

        test_code = f'''
def test_{name}_dashboard():
    """Test {name} dashboard loads"""
    with app.test_client() as client:
        response = client.get('/{name}')
        assert response.status_code == 200
        assert b'{name.title()}' in response.data
'''

        return GeneratedRoute(
            name=f'{name}_dashboard',
            flask_code=flask_code,
            html_template=html_template,
            test_code=test_code,
            url_path=f'/{name}'
        )


if __name__ == '__main__':
    # Demo route template generation
    print("🔧 Route Templates - Auto-Generate Features")
    print("=" * 60)

    # 1. CRUD Example
    print("\n1. CRUD Routes for 'newsletter':")
    crud = RouteTemplate.crud('newsletter', ['email', 'brand', 'verified'])
    print(f"   Generated {len(crud.flask_code)} chars of Flask code")
    print(f"   URL: {crud.url_path}")
    print(f"   Routes: list, create, view, edit, delete")

    # 2. API Example
    print("\n2. API Endpoint for 'comments':")
    api = RouteTemplate.api_endpoint('comments', 'brand_slug')
    print(f"   Generated {len(api.flask_code)} chars of API code")
    print(f"   URL: {api.url_path}")

    # 3. Dashboard Example
    print("\n3. Dashboard for 'analytics':")
    dashboard = RouteTemplate.dashboard('analytics', ['users', 'posts', 'comments'])
    print(f"   Generated {len(dashboard.flask_code)} chars of dashboard code")
    print(f"   URL: {dashboard.url_path}")

    print("\n✅ Route templates ready! Use generate_route.py to create features.\n")
