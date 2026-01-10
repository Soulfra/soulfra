#!/usr/bin/env python3
"""
Batch Workflows for Decentralized Customer Sync

Automates customer data distribution across your domains:
- cringeproof.com
- soulfra.com
- soulfra.github.io

Uses GitHub Pages for free static hosting + AI-powered batching
"""

from flask import Blueprint, jsonify, request
import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
import subprocess

batch_workflows_bp = Blueprint('batch_workflows', __name__)

def get_db_connection():
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_new_signups_since(hours: int = 24) -> List[Dict]:
    """Get customers who signed up in last N hours"""
    from customer_export import get_all_customers

    all_customers = get_all_customers()
    cutoff = datetime.now() - timedelta(hours=hours)

    new_customers = []
    for customer in all_customers:
        try:
            created = datetime.fromisoformat(customer['created_at'].replace('T', ' '))
            if created >= cutoff:
                new_customers.append(customer)
        except:
            continue

    return new_customers

def analyze_customer_segments_with_ollama(customers: List[Dict]) -> Dict:
    """
    Use Ollama AI to analyze customer patterns and suggest segments
    Groups customers by: activity, signup source, engagement level
    """
    try:
        import requests

        # Prepare customer data for AI analysis
        customer_summary = {
            'total': len(customers),
            'sources': {},
            'recent_activity': []
        }

        for c in customers:
            source = c.get('source', 'unknown')
            customer_summary['sources'][source] = customer_summary['sources'].get(source, 0) + 1

        # Ask Ollama for segmentation suggestions
        prompt = f"""Analyze this customer data and suggest 3-5 customer segments for targeted marketing:

Customer Data:
{json.dumps(customer_summary, indent=2)}

Provide segments based on:
1. Signup source (user signup, newsletter, QR scan)
2. Engagement level
3. Recommended marketing approach for each segment

Format: JSON with segment names and descriptions."""

        response = requests.post('http://localhost:11434/api/generate', json={
            'model': 'mistral',
            'prompt': prompt,
            'stream': False
        }, timeout=30)

        if response.ok:
            ai_response = response.json().get('response', '{}')
            return {
                'success': True,
                'ai_analysis': ai_response,
                'customer_count': len(customers)
            }
        else:
            return {'success': False, 'error': 'Ollama not responding'}

    except Exception as e:
        return {'success': False, 'error': str(e)}

@batch_workflows_bp.route('/api/batch/sync-daily')
def sync_daily():
    """
    Daily batch job: Export new signups and push to GitHub Pages
    Creates static JSON file that your domains can fetch
    """
    try:
        # Get new signups from last 24 hours
        new_customers = get_new_signups_since(hours=24)

        # Create batch export
        batch_data = {
            'sync_date': datetime.now().isoformat(),
            'period': 'last_24_hours',
            'new_customers_count': len(new_customers),
            'customers': new_customers
        }

        # Save to voice-archive directory (GitHub Pages repo)
        output_dir = 'voice-archive/data'
        os.makedirs(output_dir, exist_ok=True)

        filename = f"{output_dir}/daily_sync_{datetime.now().strftime('%Y%m%d')}.json"

        with open(filename, 'w') as f:
            json.dump(batch_data, f, indent=2)

        return jsonify({
            'success': True,
            'message': 'Daily sync completed',
            'file': filename,
            'new_customers': len(new_customers)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@batch_workflows_bp.route('/api/batch/weekly-report')
def weekly_report():
    """
    Weekly batch: Generate customer activity report as static HTML
    Hosted on GitHub Pages for easy viewing
    """
    try:
        # Get stats for last 7 days
        new_customers = get_new_signups_since(hours=168)  # 7 days

        conn = get_db_connection()

        # Aggregate weekly stats
        stats = {
            'new_customers': len(new_customers),
            'total_qr_scans': conn.execute("""
                SELECT COUNT(*) as c FROM qr_scans
                WHERE scanned_at >= datetime('now', '-7 days')
            """).fetchone()['c'],
            'total_voice_recordings': conn.execute("""
                SELECT COUNT(*) as c FROM simple_voice_recordings
                WHERE uploaded_at >= datetime('now', '-7 days')
            """).fetchone()['c']
        }

        conn.close()

        # Generate HTML report
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Weekly Report - {datetime.now().strftime('%Y-%m-%d')}</title>
    <style>
        body {{ font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        .stat {{ background: #f0f0f0; padding: 20px; margin: 10px 0; border-radius: 8px; }}
        .stat h2 {{ margin: 0 0 10px 0; }}
        .stat p {{ font-size: 2rem; font-weight: bold; margin: 0; }}
    </style>
</head>
<body>
    <h1>📊 Weekly Report</h1>
    <p>Week ending: {datetime.now().strftime('%Y-%m-%d')}</p>

    <div class="stat">
        <h2>New Customers</h2>
        <p>{stats['new_customers']}</p>
    </div>

    <div class="stat">
        <h2>QR Code Scans</h2>
        <p>{stats['total_qr_scans']}</p>
    </div>

    <div class="stat">
        <h2>Voice Recordings</h2>
        <p>{stats['total_voice_recordings']}</p>
    </div>

    <h2>Customer Breakdown</h2>
    <ul>
"""

        # Add customer list
        for customer in new_customers[:10]:  # Top 10
            html += f"        <li>{customer['email']} - {customer['source']}</li>\n"

        html += """
    </ul>

    <p style="opacity: 0.7; margin-top: 40px;">
        Generated by Soulfra Batch Workflows<br>
        Hosted on GitHub Pages
    </p>
</body>
</html>
"""

        # Save to GitHub Pages repo
        output_dir = 'voice-archive/reports'
        os.makedirs(output_dir, exist_ok=True)

        filename = f"{output_dir}/weekly_{datetime.now().strftime('%Y%m%d')}.html"

        with open(filename, 'w') as f:
            f.write(html)

        return jsonify({
            'success': True,
            'message': 'Weekly report generated',
            'file': filename,
            'stats': stats,
            'url': f'https://cringeproof.com/reports/weekly_{datetime.now().strftime("%Y%m%d")}.html'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@batch_workflows_bp.route('/api/batch/ai-segment')
def ai_segment_customers():
    """
    AI-powered customer segmentation using Ollama
    Analyzes customer patterns and suggests targeted campaigns
    """
    try:
        from customer_export import get_all_customers

        customers = get_all_customers()

        # Run AI analysis
        analysis = analyze_customer_segments_with_ollama(customers)

        if analysis['success']:
            # Save segmentation results
            output_dir = 'voice-archive/data'
            os.makedirs(output_dir, exist_ok=True)

            filename = f"{output_dir}/ai_segments_{datetime.now().strftime('%Y%m%d')}.json"

            with open(filename, 'w') as f:
                json.dump(analysis, f, indent=2)

            return jsonify({
                'success': True,
                'message': 'AI segmentation completed',
                'file': filename,
                'analysis': analysis['ai_analysis']
            })
        else:
            return jsonify(analysis), 500

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@batch_workflows_bp.route('/api/batch/push-to-github')
def push_to_github():
    """
    Push customer data files to GitHub Pages
    Publishes synced data to cringeproof.com
    """
    try:
        # Change to voice-archive directory
        os.chdir('voice-archive')

        # Git add, commit, push
        commands = [
            'git add data/ reports/',
            f'git commit -m "Batch sync: {datetime.now().strftime("%Y-%m-%d %H:%M")}"',
            'git push origin main'
        ]

        results = []
        for cmd in commands:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            results.append({
                'command': cmd,
                'success': result.returncode == 0,
                'output': result.stdout or result.stderr
            })

        # Change back
        os.chdir('..')

        return jsonify({
            'success': True,
            'message': 'Pushed to GitHub Pages',
            'results': results
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@batch_workflows_bp.route('/api/batch/run-all')
def run_all_workflows():
    """
    Run all batch workflows at once
    Daily sync + Weekly report + AI segmentation + GitHub push
    """
    try:
        import requests

        base_url = request.host_url.rstrip('/')

        # Run all workflows in sequence
        workflows = [
            f'{base_url}/api/batch/sync-daily',
            f'{base_url}/api/batch/weekly-report',
            f'{base_url}/api/batch/ai-segment',
            f'{base_url}/api/batch/push-to-github'
        ]

        results = []
        for url in workflows:
            response = requests.get(url)
            results.append({
                'workflow': url.split('/')[-1],
                'success': response.ok,
                'data': response.json() if response.ok else None
            })

        return jsonify({
            'success': True,
            'message': 'All workflows completed',
            'results': results
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def register_batch_workflow_routes(app):
    """Register batch workflow routes"""
    app.register_blueprint(batch_workflows_bp)
    print("⚙️  Batch Workflow routes registered:")
    print("   Daily Sync: GET /api/batch/sync-daily")
    print("   Weekly Report: GET /api/batch/weekly-report")
    print("   AI Segmentation: GET /api/batch/ai-segment")
    print("   Push to GitHub: GET /api/batch/push-to-github")
    print("   Run All: GET /api/batch/run-all")
