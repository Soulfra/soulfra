"""
GitHub Auto-Commit API

Automatically commits generated blog posts to GitHub repositories.
Part of the Voice → Ideas → Blog → GitHub → Leaderboard pipeline.
"""

from flask import Blueprint, jsonify, request
import sqlite3
import subprocess
import os
from pathlib import Path
from datetime import datetime

github_commit_bp = Blueprint('github_commit', __name__)

def get_db_connection():
    """Get database connection with Row factory"""
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    return conn

def run_git_command(repo_path, command):
    """Run a git command in the specified repository"""
    try:
        result = subprocess.run(
            command,
            cwd=repo_path,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout.strip(),
            'stderr': result.stderr.strip(),
            'returncode': result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': 'Command timed out after 30 seconds'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

@github_commit_bp.route('/api/github/commit-blog/<int:blog_post_id>', methods=['POST'])
def commit_blog_post(blog_post_id):
    """Commit a specific blog post to GitHub"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get blog post details
        cursor.execute('''
            SELECT * FROM blog_posts
            WHERE id = ?
        ''', (blog_post_id,))

        post = cursor.fetchone()

        if not post:
            return jsonify({'success': False, 'error': 'Blog post not found'}), 404

        if post['committed_to_github']:
            return jsonify({
                'success': False,
                'error': 'Blog post already committed to GitHub'
            }), 400

        if not post['file_path']:
            return jsonify({
                'success': False,
                'error': 'Blog post has no file path'
            }), 400

        # Verify file exists
        file_path = Path(post['file_path'])
        if not file_path.exists():
            return jsonify({
                'success': False,
                'error': f'Blog post file not found: {file_path}'
            }), 404

        # Determine repository path
        # Assuming output/{domain}/posts/{slug}.md structure
        # And git repo is at the parent level
        repo_path = Path.cwd()  # Current directory (soulfra-simple)

        # Check if we're in a git repository
        git_check = run_git_command(repo_path, 'git status')
        if not git_check['success']:
            return jsonify({
                'success': False,
                'error': 'Not in a git repository',
                'details': git_check
            }), 400

        # Stage the blog post file
        relative_path = file_path.relative_to(repo_path)
        stage_result = run_git_command(repo_path, f'git add "{relative_path}"')

        if not stage_result['success']:
            return jsonify({
                'success': False,
                'error': 'Failed to stage file',
                'details': stage_result
            }), 500

        # Create commit message
        commit_message = f"""Add blog post: {post['title']}

Domain: {post['domain']}
Ideas: {post['idea_count']}
Generated: {post['created_at']}

🤖 Auto-generated via Voice Content Factory
"""

        # Commit
        commit_result = run_git_command(
            repo_path,
            f'git commit -m "{commit_message.replace(chr(10), " ")}"'
        )

        if not commit_result['success']:
            # Check if it's because there's nothing to commit
            if 'nothing to commit' in commit_result['stdout'] or 'nothing to commit' in commit_result['stderr']:
                return jsonify({
                    'success': False,
                    'error': 'Nothing to commit (file may already be committed)',
                    'details': commit_result
                }), 400

            return jsonify({
                'success': False,
                'error': 'Failed to commit',
                'details': commit_result
            }), 500

        # Mark as committed in database
        cursor.execute('''
            UPDATE blog_posts
            SET committed_to_github = 1
            WHERE id = ?
        ''', (blog_post_id,))

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'blog_post_id': blog_post_id,
            'commit_hash': commit_result['stdout'].split()[0] if commit_result['stdout'] else None,
            'message': 'Blog post committed to git (not pushed)'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@github_commit_bp.route('/api/github/commit-all-pending', methods=['POST'])
def commit_all_pending_blogs():
    """Commit all blog posts that haven't been committed yet"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get all uncommitted blog posts
        cursor.execute('''
            SELECT * FROM blog_posts
            WHERE committed_to_github = 0
            AND file_path IS NOT NULL
        ''')

        pending_posts = cursor.fetchall()
        conn.close()

        if not pending_posts:
            return jsonify({
                'success': True,
                'message': 'No pending blog posts to commit',
                'committed_count': 0
            })

        committed = []
        errors = []

        for post in pending_posts:
            try:
                # Call commit endpoint for each post
                result = commit_blog_post(post['id'])
                response_data = result[0].get_json() if hasattr(result[0], 'get_json') else result[0]

                if response_data.get('success'):
                    committed.append({
                        'id': post['id'],
                        'title': post['title'],
                        'domain': post['domain']
                    })
            except Exception as e:
                errors.append({
                    'id': post['id'],
                    'title': post['title'],
                    'error': str(e)
                })

        return jsonify({
            'success': True,
            'committed': committed,
            'committed_count': len(committed),
            'errors': errors
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@github_commit_bp.route('/api/github/push', methods=['POST'])
def push_to_github():
    """Push all commits to GitHub remote"""
    try:
        repo_path = Path.cwd()

        # Check git status
        status_result = run_git_command(repo_path, 'git status')
        if not status_result['success']:
            return jsonify({
                'success': False,
                'error': 'Failed to check git status',
                'details': status_result
            }), 500

        # Push to origin
        push_result = run_git_command(repo_path, 'git push origin HEAD')

        if not push_result['success']:
            return jsonify({
                'success': False,
                'error': 'Failed to push to GitHub',
                'details': push_result
            }), 500

        return jsonify({
            'success': True,
            'message': 'Successfully pushed to GitHub',
            'output': push_result['stdout']
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@github_commit_bp.route('/api/github/update-leaderboard', methods=['POST'])
def update_leaderboard_json():
    """Update leaderboard.json with contributor stats"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get contributor stats
        cursor.execute('''
            SELECT
                i.user_id,
                COUNT(DISTINCT i.recording_id) as voice_memos,
                COUNT(DISTINCT i.id) as ideas_contributed,
                COUNT(DISTINCT i.blog_post_id) as blog_posts
            FROM ideas i
            WHERE i.user_id IS NOT NULL
            GROUP BY i.user_id
            ORDER BY voice_memos DESC, ideas_contributed DESC
        ''')

        contributors_data = cursor.fetchall()
        conn.close()

        # Convert to leaderboard format
        contributors = []
        for i, contributor in enumerate(contributors_data, 1):
            contributors.append({
                'rank': i,
                'user_id': contributor['user_id'],
                'voice_memos': contributor['voice_memos'],
                'ideas': contributor['ideas_contributed'],
                'blog_posts': contributor['blog_posts']
            })

        # Create leaderboard JSON
        leaderboard_data = {
            'generated_at': datetime.utcnow().isoformat() + 'Z',
            'total_contributors': len(contributors),
            'contributors': contributors
        }

        # Save to file
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)

        leaderboard_path = output_dir / 'leaderboard.json'

        import json
        with open(leaderboard_path, 'w') as f:
            json.dump(leaderboard_data, f, indent=2)

        # Commit leaderboard
        repo_path = Path.cwd()
        relative_path = leaderboard_path.relative_to(repo_path)

        stage_result = run_git_command(repo_path, f'git add "{relative_path}"')
        if not stage_result['success']:
            return jsonify({
                'success': False,
                'error': 'Failed to stage leaderboard',
                'details': stage_result
            }), 500

        commit_result = run_git_command(
            repo_path,
            f'git commit -m "Update leaderboard: {len(contributors)} contributors"'
        )

        # It's okay if there's nothing to commit
        if not commit_result['success'] and 'nothing to commit' not in commit_result['stdout']:
            return jsonify({
                'success': False,
                'error': 'Failed to commit leaderboard',
                'details': commit_result
            }), 500

        return jsonify({
            'success': True,
            'file_path': str(leaderboard_path),
            'total_contributors': len(contributors),
            'message': 'Leaderboard updated and committed'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
