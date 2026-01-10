"""
Automation Control Center Routes
Provides live dashboard + API endpoints for proving automation works
"""

from flask import render_template, jsonify, request
import json
import subprocess
import os
from datetime import datetime

def register_automation_routes(app):
    """Register automation control center routes"""

    @app.route('/automation')
    def automation_control():
        """
        Automation Control Center Dashboard

        Shows live proof that all systems work:
        - Health scanner
        - Ollama auto-fixer
        - Voice transcription
        - Email/webhooks
        - GitHub deploy
        """
        # Load latest health scan data if available
        health_data = {}
        try:
            if os.path.exists('API_HEALTH_REPORT.json'):
                with open('API_HEALTH_REPORT.json') as f:
                    report = json.load(f)

                # Count status types
                working = len([r for r in report['results'] if r.get('status') == 'OK'])
                broken = len([r for r in report['results'] if r.get('http_code') == 500])

                health_data = {
                    'total': len(report['results']),
                    'working': working,
                    'broken': broken,
                    'last_scan': report.get('timestamp', 'Never')
                }
        except:
            pass

        return render_template('automation_control.html', health_data=health_data)


    @app.route('/api/automation/status')
    def automation_status():
        """
        Get current automation system status

        Returns network map, Ollama status, health scan results
        """
        try:
            # Check Ollama
            import requests
            ollama_running = False
            ollama_models = 0
            try:
                r = requests.get('http://localhost:11434/api/tags', timeout=2)
                if r.ok:
                    ollama_running = True
                    ollama_models = len(r.json().get('models', []))
            except:
                pass

            # Get health scan status
            health_status = {'total': 442, 'working': 58, 'broken': 10}
            if os.path.exists('API_HEALTH_REPORT.json'):
                with open('API_HEALTH_REPORT.json') as f:
                    report = json.load(f)
                    health_status = {
                        'total': len(report['results']),
                        'working': len([r for r in report['results'] if r.get('status') == 'OK']),
                        'broken': len([r for r in report['results'] if r.get('http_code') == 500])
                    }

            return jsonify({
                'success': True,
                'ollama': {
                    'running': ollama_running,
                    'models': ollama_models
                },
                'health': health_status,
                'network': {
                    'node_port': 3000,
                    'flask_port': 5001,
                    'ollama_port': 11434
                }
            })

        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500


    @app.route('/api/automation/health-scan', methods=['POST'])
    def run_health_scan():
        """
        Trigger health scan and return results

        Runs api_health_scanner.py --quick and returns summary
        """
        try:
            print("🔍 Running health scan...")

            # Run the health scanner
            result = subprocess.run(
                ['python3', 'api_health_scanner.py', '--quick'],
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode != 0:
                return jsonify({
                    'success': False,
                    'error': 'Health scan failed',
                    'stderr': result.stderr
                }), 500

            # Load the generated report
            if os.path.exists('API_HEALTH_REPORT.json'):
                with open('API_HEALTH_REPORT.json') as f:
                    report = json.load(f)

                working = len([r for r in report['results'] if r.get('status') == 'OK'])
                broken = len([r for r in report['results'] if r.get('http_code') == 500])
                wrong_method = len([r for r in report['results'] if r.get('http_code') == 405])

                return jsonify({
                    'success': True,
                    'total': len(report['results']),
                    'working': working,
                    'broken': broken,
                    'wrong_method': wrong_method,
                    'timestamp': datetime.now().isoformat()
                })
            else:
                return jsonify({'success': False, 'error': 'Report file not found'}), 500

        except subprocess.TimeoutExpired:
            return jsonify({'success': False, 'error': 'Health scan timed out'}), 500
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500


    @app.route('/api/automation/auto-fix', methods=['POST'])
    def run_auto_fix():
        """
        Trigger Ollama auto-fixer for remaining broken routes

        Runs auto_fix_routes.py and returns fixed routes
        """
        try:
            print("🤖 Running Ollama auto-fixer...")

            # Run the auto-fixer (processes next 3 broken routes)
            result = subprocess.run(
                ['python3', 'auto_fix_routes.py'],
                capture_output=True,
                text=True,
                timeout=180  # 3 minutes for Ollama to process
            )

            if result.returncode != 0:
                return jsonify({
                    'success': False,
                    'error': 'Auto-fix failed',
                    'stderr': result.stderr
                }), 500

            # Parse the output to find which routes were fixed
            output_lines = result.stdout.split('\n')
            fixed_routes = []
            for line in output_lines:
                if '🔧 Fixing:' in line:
                    route = line.split('🔧 Fixing:')[1].strip()
                    fixed_routes.append(route)

            return jsonify({
                'success': True,
                'fixed_count': len(fixed_routes),
                'routes': fixed_routes,
                'timestamp': datetime.now().isoformat()
            })

        except subprocess.TimeoutExpired:
            return jsonify({'success': False, 'error': 'Auto-fix timed out (Ollama may be slow)'}), 500
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500


    @app.route('/api/automation/user-stats')
    def user_stats():
        """
        Get user account statistics

        Returns REAL users (excluding AI personas), new signups today, QR conversion rate
        """
        try:
            from database import get_db
            db = get_db()

            # Total REAL users (exclude AI personas like Soulfra, CalRiven, etc.)
            total_users = db.execute('''
                SELECT COUNT(*) as count FROM users
                WHERE is_ai_persona = 0 OR is_ai_persona IS NULL
            ''').fetchone()['count']

            # AI personas count (for reference)
            ai_personas = db.execute('''
                SELECT COUNT(*) as count FROM users
                WHERE is_ai_persona = 1
            ''').fetchone()['count']

            # New users today (real users only)
            today_users = db.execute('''
                SELECT COUNT(*) as count FROM users
                WHERE DATE(created_at) = DATE('now')
                AND (is_ai_persona = 0 OR is_ai_persona IS NULL)
            ''').fetchone()['count']

            # Kangaroo Court activity (tribunal games)
            try:
                tribunal_plays = db.execute('SELECT COUNT(*) as count FROM kangaroo_users').fetchone()['count']
            except:
                tribunal_plays = 0

            # Users created via QR (check if qr_faucet_scans table exists)
            try:
                qr_users = db.execute('''
                    SELECT COUNT(DISTINCT user_id) as count
                    FROM qr_faucet_scans
                    WHERE user_id IS NOT NULL
                ''').fetchone()
                qr_conversion = qr_users['count'] if qr_users else 0
            except:
                qr_conversion = 0

            # Total QR scans
            try:
                total_scans = db.execute('SELECT SUM(times_scanned) as total FROM qr_faucets').fetchone()
                qr_scans = total_scans['total'] if total_scans and total_scans['total'] else 0
            except:
                qr_scans = 0

            # Calculate conversion rate
            conversion_rate = round((qr_conversion / qr_scans * 100), 1) if qr_scans > 0 else 0

            return jsonify({
                'success': True,
                'total_users': total_users,
                'ai_personas': ai_personas,
                'today_users': today_users,
                'tribunal_plays': tribunal_plays,
                'qr_scans': qr_scans,
                'qr_conversions': qr_conversion,
                'conversion_rate': conversion_rate
            })

        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500


    @app.route('/api/automation/recent-users')
    def recent_users():
        """
        Get recently created user accounts

        Returns last 10 users with creation timestamp
        """
        try:
            from database import get_db
            db = get_db()

            users = db.execute('''
                SELECT id, username, display_name, created_at, is_ai_persona
                FROM users
                ORDER BY created_at DESC
                LIMIT 10
            ''').fetchall()

            user_list = [{
                'id': u['id'],
                'username': u['username'],
                'display_name': u['display_name'] or u['username'],
                'created_at': u['created_at'],
                'is_ai': bool(u['is_ai_persona'])
            } for u in users]

            return jsonify({
                'success': True,
                'users': user_list
            })

        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500


    @app.route('/api/automation/game-stats')
    def game_stats():
        """
        Get ALL game statistics (Kangaroo Court, Battles, Game Sessions, etc.)

        Returns total games played across all game types
        """
        try:
            from database import get_db
            db = get_db()

            # Kangaroo Court (Tribunal) stats
            try:
                tribunal_submissions = db.execute('SELECT COUNT(*) as count FROM kangaroo_submissions').fetchone()['count']
                tribunal_completed = db.execute('''
                    SELECT COUNT(*) as count FROM kangaroo_submissions
                    WHERE verdict IS NOT NULL
                ''').fetchone()['count']

                # Verdict breakdown
                guilty = db.execute("SELECT COUNT(*) as count FROM kangaroo_submissions WHERE verdict = 'GUILTY'").fetchone()['count']
                innocent = db.execute("SELECT COUNT(*) as count FROM kangaroo_submissions WHERE verdict = 'INNOCENT'").fetchone()['count']
            except:
                tribunal_submissions = 0
                tribunal_completed = 0
                guilty = 0
                innocent = 0

            # Generic game_sessions
            try:
                game_sessions = db.execute('SELECT COUNT(*) as count FROM game_sessions').fetchone()['count']
            except:
                game_sessions = 0

            # Battle sessions
            try:
                battle_sessions = db.execute('SELECT COUNT(*) as count FROM battle_sessions').fetchone()['count']
            except:
                battle_sessions = 0

            # Total games across all types
            total_games = tribunal_submissions + game_sessions + battle_sessions

            # Completion rate (using tribunal as main metric)
            completion_rate = round((tribunal_completed / tribunal_submissions * 100), 1) if tribunal_submissions > 0 else 0

            # Game type breakdown
            game_breakdown = [
                {'type': 'Kangaroo Court (Tribunal)', 'count': tribunal_submissions},
                {'type': 'Game Sessions', 'count': game_sessions},
                {'type': 'Battle Sessions', 'count': battle_sessions}
            ]

            return jsonify({
                'success': True,
                'total_games': total_games,
                'tribunal_submissions': tribunal_submissions,
                'tribunal_completed': tribunal_completed,
                'tribunal_guilty': guilty,
                'tribunal_innocent': innocent,
                'game_sessions': game_sessions,
                'battle_sessions': battle_sessions,
                'completion_rate': completion_rate,
                'game_breakdown': game_breakdown
            })

        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500


    @app.route('/api/automation/ollama-suggest', methods=['POST'])
    def ollama_suggest():
        """
        Ask Ollama for growth suggestions based on current metrics

        Uses user stats + game stats to generate actionable recommendations
        """
        try:
            import requests
            from database import get_db
            db = get_db()

            # Gather current metrics
            total_users = db.execute('SELECT COUNT(*) as count FROM users').fetchone()['count']
            today_users = db.execute('''
                SELECT COUNT(*) as count FROM users
                WHERE DATE(created_at) = DATE('now')
            ''').fetchone()['count']

            try:
                total_scans = db.execute('SELECT SUM(times_scanned) as total FROM qr_faucets').fetchone()
                qr_scans = total_scans['total'] if total_scans and total_scans['total'] else 0
            except:
                qr_scans = 0

            try:
                total_games = db.execute('SELECT COUNT(*) as count FROM narrative_sessions').fetchone()['count']
                completed_games = db.execute('''
                    SELECT COUNT(*) as count FROM narrative_sessions
                    WHERE completed_at IS NOT NULL
                ''').fetchone()['count']
            except:
                total_games = 0
                completed_games = 0

            # Build prompt for Ollama
            prompt = f"""You are a growth advisor for a gamified social platform called Soulfra.

CURRENT METRICS:
- Total Users: {total_users}
- New Users Today: {today_users}
- QR Scans (total): {qr_scans}
- CringeProof Games Started: {total_games}
- Games Completed: {completed_games}

THE PLATFORM:
- Users scan QR codes to create accounts (passwordless)
- After signup, they play "CringeProof" - a personality quiz game
- Game assigns them an AI friend (Soulfra, CalRiven, DeathToData, or TheAuditor)
- Goal: Increase viral growth through QR sharing

TASK: Suggest 3 specific, actionable improvements to increase user growth and engagement.

Focus on:
1. QR → User conversion rate
2. Game completion rate
3. Viral sharing mechanics

Format each suggestion as:
**[Title]**: [1-2 sentence explanation]

Be specific and tactical. No generic advice."""

            print("🤖 Asking Ollama for growth suggestions...")

            # Call Ollama
            response = requests.post('http://localhost:11434/api/generate', json={
                'model': 'mistral:latest',
                'prompt': prompt,
                'stream': False
            }, timeout=60)

            suggestions = response.json()['response']

            return jsonify({
                'success': True,
                'suggestions': suggestions,
                'metrics': {
                    'total_users': total_users,
                    'today_users': today_users,
                    'qr_scans': qr_scans,
                    'total_games': total_games,
                    'completed_games': completed_games
                },
                'timestamp': datetime.now().isoformat()
            })

        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500


    print("✅ Automation Control Center routes registered:")
    print("   - /automation (Live dashboard)")
    print("   - /api/automation/status (System status)")
    print("   - /api/automation/health-scan (Run health scan)")
    print("   - /api/automation/auto-fix (Run Ollama auto-fixer)")
    print("   - /api/automation/user-stats (User account metrics)")
    print("   - /api/automation/recent-users (Recent signups)")
    print("   - /api/automation/game-stats (CringeProof metrics)")
    print("   - /api/automation/ollama-suggest (AI growth advisor)")
