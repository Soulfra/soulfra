"""
Ideas Extraction API

Extracts ideas/topics from voice transcriptions and categorizes them by domain.
Part of the Voice → Ideas → Blog → Leaderboard pipeline.
"""

from flask import Blueprint, jsonify, request
import sqlite3
import json
from datetime import datetime, timedelta
import re

ideas_bp = Blueprint('ideas', __name__)

# Draft timer settings
DEFAULT_DRAFT_TIMER_MINUTES = 15  # Base time to ideate before auto-publish
DRAFT_EXTENSION_PER_RECORDING = 5  # Minutes added per new voice recording

# Domain keyword mapping for categorization
DOMAIN_KEYWORDS = {
    'soulfra': ['soul', 'identity', 'self', 'consciousness', 'being', 'existence', 'essence', 'spirit'],
    'deathtodata': ['data', 'privacy', 'surveillance', 'tracking', 'analytics', 'metrics', 'information'],
    'calriven': ['create', 'build', 'make', 'design', 'craft', 'develop', 'construct', 'engineer'],
    'cringeproof': ['improve', 'growth', 'better', 'progress', 'learn', 'develop', 'enhance', 'optimize'],
    'stpetepros': ['local', 'community', 'neighborhood', 'city', 'tampa', 'florida', 'regional'],
    'howtocookathome': ['cook', 'recipe', 'food', 'kitchen', 'meal', 'ingredient', 'dish', 'cuisine'],
    'hollowtown': ['empty', 'void', 'space', 'minimal', 'simple', 'bare', 'clean', 'sparse'],
    'oofbox': ['mistake', 'error', 'fail', 'oops', 'wrong', 'problem', 'issue', 'fix'],
    'niceleak': ['share', 'leak', 'reveal', 'expose', 'publish', 'release', 'disclose', 'open']
}

def get_db_connection():
    """Get database connection with Row factory"""
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    return conn

def extract_keywords(text, min_word_length=4):
    """Extract significant keywords from text"""
    # Remove punctuation and convert to lowercase
    text = re.sub(r'[^\w\s]', '', text.lower())
    words = text.split()

    # Filter out common words and short words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been', 'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'which', 'who', 'when', 'where', 'why', 'how'}

    keywords = [word for word in words if len(word) >= min_word_length and word not in stop_words]

    # Count frequency
    keyword_freq = {}
    for word in keywords:
        keyword_freq[word] = keyword_freq.get(word, 0) + 1

    # Sort by frequency
    sorted_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, freq in sorted_keywords[:10]]  # Top 10 keywords

def categorize_by_domain(keywords):
    """Categorize content by domain based on keywords"""
    domain_scores = {}

    for domain, domain_keywords in DOMAIN_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            if keyword in domain_keywords:
                score += 2  # Exact match
            elif any(dk in keyword or keyword in dk for dk in domain_keywords):
                score += 1  # Partial match
        domain_scores[domain] = score

    # Sort by score
    sorted_domains = sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)

    # Return domains with score > 0
    return [domain for domain, score in sorted_domains if score > 0]

def extract_ideas_from_text(text):
    """Extract individual ideas/topics from transcription text"""
    # Split by common sentence delimiters
    sentences = re.split(r'[.!?]+', text)

    ideas = []
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 20:  # Skip very short sentences
            continue

        # Extract keywords from sentence
        keywords = extract_keywords(sentence)
        if len(keywords) >= 2:  # At least 2 significant keywords
            ideas.append({
                'text': sentence,
                'keywords': keywords[:5]  # Top 5 keywords for this idea
            })

    return ideas

@ideas_bp.route('/api/ideas/extract/<int:recording_id>', methods=['POST'])
def extract_ideas_from_recording(recording_id):
    """Extract ideas from a specific voice recording"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get recording with transcription
        cursor.execute('''
            SELECT id, transcription, created_at, user_id
            FROM simple_voice_recordings
            WHERE id = ?
        ''', (recording_id,))

        recording = cursor.fetchone()

        if not recording:
            return jsonify({'success': False, 'error': 'Recording not found'}), 404

        if not recording['transcription']:
            return jsonify({'success': False, 'error': 'Recording not yet transcribed'}), 400

        # Extract ideas
        transcription = recording['transcription']
        ideas = extract_ideas_from_text(transcription)

        # Extract overall keywords
        keywords = extract_keywords(transcription)

        # Categorize by domain
        suggested_domains = categorize_by_domain(keywords)

        # Create ideas table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ideas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recording_id INTEGER NOT NULL,
                user_id INTEGER,
                idea_text TEXT NOT NULL,
                keywords TEXT,
                suggested_domains TEXT,
                assigned_domain TEXT,
                created_at TEXT NOT NULL,
                blog_post_id INTEGER,
                FOREIGN KEY (recording_id) REFERENCES simple_voice_recordings (id)
            )
        ''')

        # Insert ideas into database
        idea_ids = []
        for idea in ideas:
            idea_domains = categorize_by_domain(idea['keywords'])

            cursor.execute('''
                INSERT INTO ideas (
                    recording_id, user_id, idea_text, keywords,
                    suggested_domains, assigned_domain, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                recording_id,
                recording['user_id'],
                idea['text'],
                json.dumps(idea['keywords']),
                json.dumps(idea_domains),
                idea_domains[0] if idea_domains else 'general',
                datetime.utcnow().isoformat()
            ))
            idea_ids.append(cursor.lastrowid)

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'recording_id': recording_id,
            'ideas_count': len(ideas),
            'idea_ids': idea_ids,
            'overall_keywords': keywords,
            'suggested_domains': suggested_domains,
            'ideas': ideas
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ideas_bp.route('/api/ideas/extract-all-pending', methods=['POST'])
def extract_all_pending():
    """Extract ideas from all recordings that haven't been processed yet"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Create ideas table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ideas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recording_id INTEGER NOT NULL,
                user_id INTEGER,
                idea_text TEXT NOT NULL,
                keywords TEXT,
                suggested_domains TEXT,
                assigned_domain TEXT,
                created_at TEXT NOT NULL,
                blog_post_id INTEGER,
                FOREIGN KEY (recording_id) REFERENCES simple_voice_recordings (id)
            )
        ''')

        # Get recordings with transcriptions but no ideas yet
        cursor.execute('''
            SELECT r.id, r.transcription, r.created_at, r.user_id
            FROM simple_voice_recordings r
            LEFT JOIN ideas i ON r.id = i.recording_id
            WHERE r.transcription IS NOT NULL
            AND r.transcription != ''
            AND i.id IS NULL
        ''')

        pending_recordings = cursor.fetchall()

        if not pending_recordings:
            return jsonify({
                'success': True,
                'message': 'No pending recordings to process',
                'processed_count': 0
            })

        processed_count = 0
        total_ideas = 0

        for recording in pending_recordings:
            try:
                # Extract ideas
                ideas = extract_ideas_from_text(recording['transcription'])
                keywords = extract_keywords(recording['transcription'])

                # Insert ideas
                for idea in ideas:
                    idea_domains = categorize_by_domain(idea['keywords'])

                    cursor.execute('''
                        INSERT INTO ideas (
                            recording_id, user_id, idea_text, keywords,
                            suggested_domains, assigned_domain, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        recording['id'],
                        recording['user_id'],
                        idea['text'],
                        json.dumps(idea['keywords']),
                        json.dumps(idea_domains),
                        idea_domains[0] if idea_domains else 'general',
                        datetime.utcnow().isoformat()
                    ))

                total_ideas += len(ideas)
                processed_count += 1

            except Exception as e:
                print(f"Error processing recording {recording['id']}: {e}")
                continue

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'processed_recordings': processed_count,
            'total_ideas_extracted': total_ideas
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ideas_bp.route('/api/ideas/list', methods=['GET'])
def list_ideas():
    """List all extracted ideas with optional filtering"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get query parameters
        domain = request.args.get('domain')
        limit = request.args.get('limit', 50, type=int)

        # Build query
        query = '''
            SELECT i.*, r.filename, r.created_at as recording_created_at
            FROM ideas i
            LEFT JOIN simple_voice_recordings r ON i.recording_id = r.id
        '''
        params = []

        if domain:
            query += ' WHERE i.assigned_domain = ?'
            params.append(domain)

        query += ' ORDER BY i.created_at DESC LIMIT ?'
        params.append(limit)

        cursor.execute(query, params)
        ideas = cursor.fetchall()

        # Convert to dict
        ideas_list = []
        for idea in ideas:
            ideas_list.append({
                'id': idea['id'],
                'recording_id': idea['recording_id'],
                'idea_text': idea['idea_text'],
                'keywords': json.loads(idea['keywords']) if idea['keywords'] else [],
                'suggested_domains': json.loads(idea['suggested_domains']) if idea['suggested_domains'] else [],
                'assigned_domain': idea['assigned_domain'],
                'created_at': idea['created_at'],
                'blog_post_id': idea['blog_post_id']
            })

        conn.close()

        return jsonify({
            'success': True,
            'ideas': ideas_list,
            'count': len(ideas_list)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ideas_bp.route('/api/ideas/stats', methods=['GET'])
def ideas_stats():
    """Get statistics about extracted ideas"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Total ideas
        cursor.execute('SELECT COUNT(*) as count FROM ideas')
        total_ideas = cursor.fetchone()['count']

        # Ideas by domain
        cursor.execute('''
            SELECT assigned_domain, COUNT(*) as count
            FROM ideas
            GROUP BY assigned_domain
            ORDER BY count DESC
        ''')
        by_domain = [{'domain': row['assigned_domain'], 'count': row['count']} for row in cursor.fetchall()]

        # Ideas ready for blog posts (not yet assigned to a post)
        cursor.execute('SELECT COUNT(*) as count FROM ideas WHERE blog_post_id IS NULL')
        ready_for_blog = cursor.fetchone()['count']

        conn.close()

        return jsonify({
            'success': True,
            'total_ideas': total_ideas,
            'by_domain': by_domain,
            'ready_for_blog': ready_for_blog
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
