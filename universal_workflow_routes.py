#!/usr/bin/env python3
"""
Universal Workflow Management Routes
Handles ALL industry workflows the same way
"""

from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session, Response
from database import get_db
import json
from datetime import datetime
import csv
import io

workflow_bp = Blueprint('workflow', __name__)


@workflow_bp.route('/workflows')
def workflow_list():
    """List all available workflow templates"""
    db = get_db()

    templates = db.execute('''
        SELECT * FROM workflow_templates ORDER BY industry, name
    ''').fetchall()

    return render_template('workflow/templates.html', templates=templates)


@workflow_bp.route('/workflows/<slug>')
def workflow_detail(slug):
    """View a specific workflow template"""
    db = get_db()

    template = db.execute('''
        SELECT * FROM workflow_templates WHERE slug = ?
    ''', (slug,)).fetchone()

    if not template:
        return "Workflow not found", 404

    # Parse stages JSON
    stages = json.loads(template['stages'])
    stage_config = json.loads(template['stage_config']) if template['stage_config'] else {}

    # Get active pipelines using this template
    pipelines = db.execute('''
        SELECT * FROM project_pipelines
        WHERE workflow_template_id = ? AND status = 'active'
        ORDER BY priority DESC, created_at DESC
    ''', (template['id'],)).fetchall()

    return render_template('workflow/detail.html',
                         template=template,
                         stages=stages,
                         stage_config=stage_config,
                         pipelines=pipelines)


@workflow_bp.route('/pipelines')
def pipeline_list():
    """Kanban view of all active pipelines"""
    db = get_db()

    # Get all active pipelines with their templates
    pipelines = db.execute('''
        SELECT p.*, t.name as template_name, t.stages, t.industry
        FROM project_pipelines p
        JOIN workflow_templates t ON p.workflow_template_id = t.id
        WHERE p.status = 'active'
        ORDER BY p.priority DESC, p.created_at DESC
    ''').fetchall()

    # Group by industry
    by_industry = {}
    for pipeline in pipelines:
        industry = pipeline['industry']
        if industry not in by_industry:
            by_industry[industry] = []
        by_industry[industry].append(dict(pipeline))

    return render_template('workflow/kanban.html', by_industry=by_industry)


@workflow_bp.route('/pipelines/create', methods=['POST'])
def pipeline_create():
    """Create a new pipeline from a template"""
    db = get_db()

    template_id = request.form.get('template_id')
    title = request.form.get('title')
    project_id = request.form.get('project_id')  # Optional

    if not template_id or not title:
        return jsonify({'error': 'Missing required fields'}), 400

    # Create pipeline
    cursor = db.execute('''
        INSERT INTO project_pipelines (
            project_id, workflow_template_id, title, current_stage, stage_data, status
        ) VALUES (?, ?, ?, 0, '{}', 'active')
    ''', (project_id, template_id, title))

    pipeline_id = cursor.lastrowid
    db.commit()

    # Log activity
    db.execute('''
        INSERT INTO pipeline_activity (pipeline_id, stage_index, action, metadata)
        VALUES (?, 0, 'created', ?)
    ''', (pipeline_id, json.dumps({'title': title})))

    db.commit()

    return jsonify({'pipeline_id': pipeline_id, 'success': True})


@workflow_bp.route('/pipelines/<int:pipeline_id>')
def pipeline_view(pipeline_id):
    """View a single pipeline with all stages"""
    db = get_db()

    pipeline = db.execute('''
        SELECT p.*, t.name as template_name, t.stages, t.stage_config, t.industry
        FROM project_pipelines p
        JOIN workflow_templates t ON p.workflow_template_id = t.id
        WHERE p.id = ?
    ''', (pipeline_id,)).fetchone()

    if not pipeline:
        return "Pipeline not found", 404

    stages = json.loads(pipeline['stages'])
    stage_config = json.loads(pipeline['stage_config']) if pipeline['stage_config'] else {}
    stage_data = json.loads(pipeline['stage_data']) if pipeline['stage_data'] else {}

    # Get activity log
    activity = db.execute('''
        SELECT * FROM pipeline_activity
        WHERE pipeline_id = ?
        ORDER BY created_at DESC
        LIMIT 50
    ''', (pipeline_id,)).fetchall()

    # Get attachments
    attachments = db.execute('''
        SELECT * FROM pipeline_attachments
        WHERE pipeline_id = ?
        ORDER BY stage_index, created_at
    ''', (pipeline_id,)).fetchall()

    return render_template('workflow/pipeline.html',
                         pipeline=pipeline,
                         stages=stages,
                         stage_config=stage_config,
                         stage_data=stage_data,
                         activity=activity,
                         attachments=attachments)


@workflow_bp.route('/pipelines/<int:pipeline_id>/advance', methods=['POST'])
def pipeline_advance(pipeline_id):
    """Move pipeline to next stage"""
    db = get_db()

    pipeline = db.execute('''
        SELECT * FROM project_pipelines WHERE id = ?
    ''', (pipeline_id,)).fetchone()

    if not pipeline:
        return jsonify({'error': 'Pipeline not found'}), 404

    # Get template stages
    template = db.execute('''
        SELECT stages FROM workflow_templates WHERE id = ?
    ''', (pipeline['workflow_template_id'],)).fetchone()

    stages = json.loads(template['stages'])
    current_stage = pipeline['current_stage']

    if current_stage >= len(stages) - 1:
        # Already at final stage, mark as completed
        db.execute('''
            UPDATE project_pipelines
            SET status = 'completed', completed_at = ?
            WHERE id = ?
        ''', (datetime.now(), pipeline_id))

        db.execute('''
            INSERT INTO pipeline_activity (pipeline_id, stage_index, action)
            VALUES (?, ?, 'completed')
        ''', (pipeline_id, current_stage))

        db.commit()
        return jsonify({'success': True, 'status': 'completed'})

    # Advance to next stage
    next_stage = current_stage + 1
    db.execute('''
        UPDATE project_pipelines SET current_stage = ? WHERE id = ?
    ''', (next_stage, pipeline_id))

    db.execute('''
        INSERT INTO pipeline_activity (pipeline_id, stage_index, action)
        VALUES (?, ?, 'advanced')
    ''', (pipeline_id, next_stage))

    db.commit()

    return jsonify({'success': True, 'current_stage': next_stage, 'stage_name': stages[next_stage]})


@workflow_bp.route('/pipelines/<int:pipeline_id>/update', methods=['POST'])
def pipeline_update(pipeline_id):
    """Update pipeline stage data"""
    db = get_db()

    stage_index = request.json.get('stage_index')
    field = request.json.get('field')
    value = request.json.get('value')

    pipeline = db.execute('''
        SELECT stage_data FROM project_pipelines WHERE id = ?
    ''', (pipeline_id,)).fetchone()

    if not pipeline:
        return jsonify({'error': 'Pipeline not found'}), 404

    stage_data = json.loads(pipeline['stage_data']) if pipeline['stage_data'] else {}

    # Update nested data
    stage_key = f"stage_{stage_index}"
    if stage_key not in stage_data:
        stage_data[stage_key] = {}

    stage_data[stage_key][field] = value

    db.execute('''
        UPDATE project_pipelines SET stage_data = ? WHERE id = ?
    ''', (json.dumps(stage_data), pipeline_id))

    db.execute('''
        INSERT INTO pipeline_activity (pipeline_id, stage_index, action, metadata)
        VALUES (?, ?, 'data_updated', ?)
    ''', (pipeline_id, stage_index, json.dumps({field: value})))

    db.commit()

    return jsonify({'success': True})


@workflow_bp.route('/pipelines/export.csv')
def export_csv():
    """Export all pipelines to CSV"""
    db = get_db()

    industry_filter = request.args.get('industry')
    status_filter = request.args.get('status', 'active')

    query = '''
        SELECT
            p.id,
            p.title,
            t.name as workflow,
            t.industry,
            p.current_stage,
            p.status,
            p.priority,
            p.created_at,
            p.completed_at
        FROM project_pipelines p
        JOIN workflow_templates t ON p.workflow_template_id = t.id
        WHERE p.status = ?
    '''

    params = [status_filter]

    if industry_filter:
        query += ' AND t.industry = ?'
        params.append(industry_filter)

    query += ' ORDER BY p.created_at DESC'

    pipelines = db.execute(query, params).fetchall()

    # Generate CSV
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(['ID', 'Title', 'Workflow', 'Industry', 'Stage', 'Status', 'Priority', 'Created', 'Completed'])

    for p in pipelines:
        writer.writerow([
            p['id'],
            p['title'],
            p['workflow'],
            p['industry'],
            p['current_stage'],
            p['status'],
            p['priority'],
            p['created_at'],
            p['completed_at'] or ''
        ])

    output.seek(0)

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=pipelines.csv'}
    )


@workflow_bp.route('/pipelines/export.json')
def export_json():
    """Export all pipelines to JSON"""
    db = get_db()

    pipelines = db.execute('''
        SELECT
            p.*,
            t.name as workflow_name,
            t.stages,
            t.industry
        FROM project_pipelines p
        JOIN workflow_templates t ON p.workflow_template_id = t.id
        WHERE p.status = 'active'
        ORDER BY p.created_at DESC
    ''').fetchall()

    data = []
    for p in pipelines:
        data.append({
            'id': p['id'],
            'title': p['title'],
            'workflow': p['workflow_name'],
            'industry': p['industry'],
            'stages': json.loads(p['stages']),
            'current_stage': p['current_stage'],
            'stage_data': json.loads(p['stage_data']) if p['stage_data'] else {},
            'status': p['status'],
            'priority': p['priority'],
            'created_at': p['created_at'],
            'completed_at': p['completed_at']
        })

    return jsonify(data)


def register_universal_workflow_routes(app):
    """Register workflow routes with the app"""
    app.register_blueprint(workflow_bp)
    print("✅ Universal workflow routes registered")
