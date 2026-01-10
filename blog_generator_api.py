"""
Blog Generator API

Generates blog posts from extracted ideas.
Part of the Voice → Ideas → Blog → Leaderboard pipeline.
"""

from flask import Blueprint, jsonify, request
import sqlite3
import json
from datetime import datetime
import os
from pathlib import Path
import re

blog_generator_bp = Blueprint('blog_generator', __name__)

def get_db_connection():
    """Get database connection with Row factory"""
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    return conn

def slugify(text):
    """Convert text to URL-friendly slug"""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')

def generate_blog_post_content(ideas, domain):
    """Generate markdown blog post from ideas"""
    # Group ideas by topic/theme based on shared keywords
    # For now, just combine ideas into sections

    # Create title from most common keywords
    all_keywords = []
    for idea in ideas:
        keywords = json.loads(idea['keywords']) if idea['keywords'] else []
        all_keywords.extend(keywords)

    # Count keyword frequency
    keyword_freq = {}
    for kw in all_keywords:
        keyword_freq[kw] = keyword_freq.get(kw, 0) + 1

    # Get top 3 keywords for title
    top_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:3]
    title_words = [kw.capitalize() for kw, freq in top_keywords]
    title = f"{domain.capitalize()}: {' & '.join(title_words)}"

    # Generate content
    content_parts = [
        f"# {title}\n",
        f"*Generated from voice recordings on {datetime.utcnow().strftime('%B %d, %Y')}*\n",
        "---\n"
    ]

    # Add introduction
    content_parts.append(f"This post explores ideas from recent voice memos related to {domain}.\n")

    # Add ideas as sections
    for i, idea in enumerate(ideas, 1):
        keywords = json.loads(idea['keywords']) if idea['keywords'] else []
        section_title = keywords[0].capitalize() if keywords else f"Idea {i}"

        content_parts.append(f"\n## {section_title}\n")
        content_parts.append(f"{idea['idea_text']}\n")

        # Add keywords as tags
        if len(keywords) > 1:
            tags = ', '.join([f"`{kw}`" for kw in keywords[:5]])
            content_parts.append(f"\n*Related topics: {tags}*\n")

    # Add footer
    content_parts.append("\n---\n")
    content_parts.append(f"*This post was auto-generated from {len(ideas)} voice memo{'s' if len(ideas) > 1 else ''}*\n")

    return ''.join(content_parts), title

@blog_generator_bp.route('/api/blog/generate-from-domain/<domain>', methods=['POST'])
def generate_blog_from_domain(domain):
    """Generate blog post from all unassigned ideas for a domain"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get unassigned ideas for this domain
        cursor.execute('''
            SELECT * FROM ideas
            WHERE assigned_domain = ?
            AND blog_post_id IS NULL
            ORDER BY created_at DESC
        ''', (domain,))

        ideas = cursor.fetchall()

        if not ideas:
            return jsonify({
                'success': False,
                'error': f'No unassigned ideas found for domain: {domain}'
            }), 404

        # Generate blog post content
        content, title = generate_blog_post_content(ideas, domain)

        # Create slug
        slug = f"{domain}-{slugify(title)}-{datetime.utcnow().strftime('%Y%m%d')}"

        # Create blog_posts table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blog_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT NOT NULL,
                title TEXT NOT NULL,
                slug TEXT UNIQUE NOT NULL,
                content TEXT NOT NULL,
                idea_count INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                published_at TEXT,
                file_path TEXT,
                committed_to_github INTEGER DEFAULT 0
            )
        ''')

        # Insert blog post
        cursor.execute('''
            INSERT INTO blog_posts (
                domain, title, slug, content, idea_count, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            domain,
            title,
            slug,
            content,
            len(ideas),
            datetime.utcnow().isoformat()
        ))

        blog_post_id = cursor.lastrowid

        # Update ideas to mark them as used
        idea_ids = [idea['id'] for idea in ideas]
        placeholders = ','.join(['?' for _ in idea_ids])
        cursor.execute(f'''
            UPDATE ideas
            SET blog_post_id = ?
            WHERE id IN ({placeholders})
        ''', [blog_post_id] + idea_ids)

        # Save markdown file
        output_dir = Path('output') / domain / 'posts'
        output_dir.mkdir(parents=True, exist_ok=True)

        file_path = output_dir / f"{slug}.md"

        # Create markdown with frontmatter
        frontmatter = f"""---
title: {title}
slug: {slug}
published: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}
domain: {domain}
idea_count: {len(ideas)}
---

"""
        with open(file_path, 'w') as f:
            f.write(frontmatter + content)

        # Update file_path in database
        cursor.execute('''
            UPDATE blog_posts
            SET file_path = ?, published_at = ?
            WHERE id = ?
        ''', (str(file_path), datetime.utcnow().isoformat(), blog_post_id))

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'blog_post_id': blog_post_id,
            'title': title,
            'slug': slug,
            'file_path': str(file_path),
            'idea_count': len(ideas)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@blog_generator_bp.route('/api/blog/generate-all', methods=['POST'])
def generate_all_blogs():
    """Generate blog posts for all domains with unassigned ideas"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get domains with unassigned ideas
        cursor.execute('''
            SELECT assigned_domain, COUNT(*) as idea_count
            FROM ideas
            WHERE blog_post_id IS NULL
            GROUP BY assigned_domain
            HAVING idea_count >= 3
        ''')

        domains_with_ideas = cursor.fetchall()
        conn.close()

        if not domains_with_ideas:
            return jsonify({
                'success': True,
                'message': 'No domains with enough unassigned ideas (minimum 3)',
                'generated_posts': 0
            })

        generated_posts = []
        errors = []

        for domain_row in domains_with_ideas:
            domain = domain_row['assigned_domain']
            try:
                # Call generate endpoint for each domain
                result = generate_blog_from_domain(domain)
                if result[1] == 200:  # Success
                    data = json.loads(result[0].data)
                    generated_posts.append({
                        'domain': domain,
                        'title': data['title'],
                        'slug': data['slug'],
                        'idea_count': data['idea_count']
                    })
            except Exception as e:
                errors.append({
                    'domain': domain,
                    'error': str(e)
                })

        return jsonify({
            'success': True,
            'generated_posts': generated_posts,
            'count': len(generated_posts),
            'errors': errors
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@blog_generator_bp.route('/api/blog/list', methods=['GET'])
def list_blog_posts():
    """List all generated blog posts"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get query parameters
        domain = request.args.get('domain')
        limit = request.args.get('limit', 50, type=int)

        # Build query
        query = 'SELECT * FROM blog_posts'
        params = []

        if domain:
            query += ' WHERE domain = ?'
            params.append(domain)

        query += ' ORDER BY created_at DESC LIMIT ?'
        params.append(limit)

        cursor.execute(query, params)
        posts = cursor.fetchall()

        # Convert to dict
        posts_list = []
        for post in posts:
            posts_list.append({
                'id': post['id'],
                'domain': post['domain'],
                'title': post['title'],
                'slug': post['slug'],
                'idea_count': post['idea_count'],
                'created_at': post['created_at'],
                'published_at': post['published_at'],
                'file_path': post['file_path'],
                'committed_to_github': bool(post['committed_to_github'])
            })

        conn.close()

        return jsonify({
            'success': True,
            'posts': posts_list,
            'count': len(posts_list)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@blog_generator_bp.route('/api/blog/stats', methods=['GET'])
def blog_stats():
    """Get statistics about generated blog posts"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Total posts
        cursor.execute('SELECT COUNT(*) as count FROM blog_posts')
        total_posts = cursor.fetchone()['count']

        # Posts by domain
        cursor.execute('''
            SELECT domain, COUNT(*) as count
            FROM blog_posts
            GROUP BY domain
            ORDER BY count DESC
        ''')
        by_domain = [{'domain': row['domain'], 'count': row['count']} for row in cursor.fetchall()]

        # Posts not yet committed to GitHub
        cursor.execute('SELECT COUNT(*) as count FROM blog_posts WHERE committed_to_github = 0')
        pending_commit = cursor.fetchone()['count']

        conn.close()

        return jsonify({
            'success': True,
            'total_posts': total_posts,
            'by_domain': by_domain,
            'pending_commit': pending_commit
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
