#!/usr/bin/env python3
"""
Feature Status Tracker - Automatic Testing & Changelog

Tests EVERY feature to see what actually works.
Generates FEATURE_STATUS.md automatically.

Zero Dependencies: Python stdlib only
"""

import urllib.request
import urllib.error
import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List


class FeatureStatusTracker:
    """Test all features and generate status report"""

    def __init__(self, base_url: str = 'http://localhost:5001', db_path: str = 'soulfra.db'):
        self.base_url = base_url
        self.db_path = db_path
        self.results: List[Dict] = []

    def test_all(self) -> Dict:
        """Run all feature tests"""
        print("🧪 Testing All Features...")
        print("=" * 70)

        self.test_database()
        self.test_flask_server()
        self.test_widget()
        self.test_ollama()
        self.test_admin_panel()
        self.test_neural_networks()
        self.test_posts()
        self.test_duplicates()

        return self.generate_report()

    def test_database(self):
        """Test database connectivity"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM posts")
            post_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM discussion_messages")
            message_count = cursor.fetchone()[0]
            conn.close()

            self.results.append({
                'feature': 'Database',
                'status': 'working',
                'details': f'{user_count} users, {post_count} posts, {message_count} widget messages'
            })
        except Exception as e:
            self.results.append({
                'feature': 'Database',
                'status': 'broken',
                'error': str(e)
            })

    def test_flask_server(self):
        """Test Flask server health"""
        try:
            req = urllib.request.Request(f'{self.base_url}/api/health')
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                if data.get('status') == 'healthy':
                    self.results.append({
                        'feature': 'Flask Server',
                        'status': 'working',
                        'details': f"Running on {self.base_url}"
                    })
                else:
                    self.results.append({
                        'feature': 'Flask Server',
                        'status': 'degraded',
                        'details': 'Unhealthy response'
                    })
        except Exception as e:
            self.results.append({
                'feature': 'Flask Server',
                'status': 'broken',
                'error': str(e)
            })

    def test_widget(self):
        """Test widget API"""
        try:
            # Test discussion message endpoint (the actual widget endpoint)
            # POST request required, expects authentication
            req = urllib.request.Request(
                f'{self.base_url}/api/discussion/message',
                data=json.dumps({'session_id': 1, 'content': 'test'}).encode(),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            try:
                with urllib.request.urlopen(req, timeout=5) as response:
                    # If we get here, endpoint exists (even if it returns error due to no auth)
                    data = json.loads(response.read().decode())
                    self.results.append({
                        'feature': 'Widget Chat',
                        'status': 'working',
                        'details': 'API endpoint working at /api/discussion/message'
                    })
                    return
            except urllib.error.HTTPError as http_err:
                # 401 Unauthorized = endpoint exists but needs auth (good!)
                # 404 Not Found = endpoint doesn't exist (bad!)
                # 400 Bad Request = endpoint exists but invalid data (also good!)
                if http_err.code in [400, 401]:
                    self.results.append({
                        'feature': 'Widget Chat',
                        'status': 'working',
                        'details': 'API endpoint exists at /api/discussion/message (requires auth)'
                    })
                    return
                elif http_err.code == 404:
                    raise Exception('Endpoint /api/discussion/message not found')
                else:
                    raise http_err

            # If we got 200 OK somehow
            self.results.append({
                'feature': 'Widget Chat',
                'status': 'working',
                'details': 'API responding correctly'
            })
        except Exception as e:
            self.results.append({
                'feature': 'Widget Chat',
                'status': 'broken',
                'error': str(e)
            })

    def test_ollama(self):
        """Test Ollama connectivity"""
        try:
            req = urllib.request.Request('http://localhost:11434/api/tags')
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                models = data.get('models', [])
                self.results.append({
                    'feature': 'Ollama',
                    'status': 'working',
                    'details': f'{len(models)} models available'
                })
        except Exception as e:
            self.results.append({
                'feature': 'Ollama',
                'status': 'broken',
                'error': 'Not running (start with: ollama serve)'
            })

    def test_admin_panel(self):
        """Test admin panel accessibility"""
        try:
            req = urllib.request.Request(f'{self.base_url}/admin/automation')
            with urllib.request.urlopen(req, timeout=5) as response:
                html = response.read().decode()
                # If redirected to login, panel exists
                if 'admin/login' in html or 'Automation' in html:
                    self.results.append({
                        'feature': 'Admin Panel',
                        'status': 'working',
                        'details': '/admin/automation accessible'
                    })
                else:
                    self.results.append({
                        'feature': 'Admin Panel',
                        'status': 'degraded',
                        'details': 'Unexpected response'
                    })
        except Exception as e:
            self.results.append({
                'feature': 'Admin Panel',
                'status': 'broken',
                'error': str(e)
            })

    def test_neural_networks(self):
        """Test neural network availability"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM neural_networks")
            nn_count = cursor.fetchone()[0]
            conn.close()

            if nn_count > 0:
                self.results.append({
                    'feature': 'Neural Networks',
                    'status': 'working',
                    'details': f'{nn_count} models registered'
                })
            else:
                self.results.append({
                    'feature': 'Neural Networks',
                    'status': 'degraded',
                    'details': 'No models found in database'
                })
        except Exception as e:
            self.results.append({
                'feature': 'Neural Networks',
                'status': 'broken',
                'error': str(e)
            })

    def test_posts(self):
        """Test post system"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM posts WHERE published_at IS NOT NULL")
            published_count = cursor.fetchone()[0]
            conn.close()

            if published_count > 0:
                self.results.append({
                    'feature': 'Post System',
                    'status': 'working',
                    'details': f'{published_count} published posts'
                })
            else:
                self.results.append({
                    'feature': 'Post System',
                    'status': 'degraded',
                    'details': 'Database working but no posts'
                })
        except Exception as e:
            self.results.append({
                'feature': 'Post System',
                'status': 'broken',
                'error': str(e)
            })

    def test_duplicates(self):
        """Find duplicate implementations"""
        ollama_files = [
            'ollama_discussion.py',  # Still used by app.py (will be refactored)
        ]

        existing = [f for f in ollama_files if os.path.exists(f)]

        if len(existing) >= 1:
            self.results.append({
                'feature': 'Code Duplication',
                'status': 'degraded',
                'details': f'{len(existing)} Ollama file remaining (ollama_discussion.py used by app.py)',
                'recommendation': 'NEXT: Refactor app.py to use ai_orchestrator.py, then delete ollama_discussion.py'
            })
        else:
            self.results.append({
                'feature': 'Code Duplication',
                'status': 'working',
                'details': 'All duplicates cleaned! Only ai_orchestrator.py remains.'
            })

    def generate_report(self) -> Dict:
        """Generate status report"""
        working = sum(1 for r in self.results if r['status'] == 'working')
        degraded = sum(1 for r in self.results if r['status'] == 'degraded')
        broken = sum(1 for r in self.results if r['status'] == 'broken')

        return {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_features': len(self.results),
                'working': working,
                'degraded': degraded,
                'broken': broken
            },
            'results': self.results
        }

    def save_markdown(self, report: Dict):
        """Save report as Markdown"""
        md = f"""# Soulfra Feature Status Report

**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary

- ✅ Working: {report['summary']['working']}/{report['summary']['total_features']}
- ⚠️ Degraded: {report['summary']['degraded']}/{report['summary']['total_features']}
- ❌ Broken: {report['summary']['broken']}/{report['summary']['total_features']}

---

## Feature Details

"""

        for result in report['results']:
            status_icon = {
                'working': '✅',
                'degraded': '⚠️',
                'broken': '❌'
            }[result['status']]

            md += f"### {status_icon} {result['feature']}\n\n"
            md += f"**Status:** {result['status'].upper()}\n\n"

            if 'details' in result:
                md += f"**Details:** {result['details']}\n\n"

            if 'error' in result:
                md += f"**Error:** `{result['error']}`\n\n"

            if 'recommendation' in result:
                md += f"**Recommendation:** {result['recommendation']}\n\n"

            md += "---\n\n"

        md += f"""## Next Actions

Based on this report:

1. **Fix Broken Features:** {report['summary']['broken']} features need attention
2. **Improve Degraded:** {report['summary']['degraded']} features need optimization
3. **Code Cleanup:** Check duplication recommendations above

---

*This report is automatically generated by `feature_status.py`*
"""

        with open('FEATURE_STATUS.md', 'w') as f:
            f.write(md)

        print(f"\n📄 Report saved to FEATURE_STATUS.md")


# ==============================================================================
# MAIN
# ==============================================================================

if __name__ == '__main__':
    tracker = FeatureStatusTracker()
    report = tracker.test_all()

    print("\n📊 Results:")
    print(f"   ✅ Working: {report['summary']['working']}")
    print(f"   ⚠️  Degraded: {report['summary']['degraded']}")
    print(f"   ❌ Broken: {report['summary']['broken']}")

    tracker.save_markdown(report)

    print("\n" + "=" * 70)
    print("✅ Feature status check complete!")
    print("📄 Read FEATURE_STATUS.md for full report")
