#!/usr/bin/env python3
"""
Daily inspirational quotes for leftonreadbygod.com
No email server needed - just in-app distribution
"""

from flask import Blueprint, jsonify, request
import sqlite3
from datetime import datetime, timezone
import subprocess
import json

quote_bp = Blueprint('quotes', __name__)

def get_db():
    """Get database connection"""
    db = sqlite3.connect('soulfra.db')
    db.row_factory = sqlite3.Row
    return db

def init_quote_tables():
    """Initialize quotes database table"""
    db = get_db()
    db.execute('''
        CREATE TABLE IF NOT EXISTS daily_quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand_slug TEXT NOT NULL,
            quote_text TEXT NOT NULL,
            generated_at TEXT NOT NULL,
            active INTEGER DEFAULT 1,
            views INTEGER DEFAULT 0
        )
    ''')
    db.commit()
    db.close()
    print("✅ Daily quotes table initialized")

def generate_quote_with_ollama(brand_slug='leftonreadbygod'):
    """Generate a quote using Ollama"""

    # Different prompts for different brands
    prompts = {
        'leftonreadbygod': "Generate a single inspirational quote for leftonreadbygod.com - a newsletter about modern dating, ghosting, and being left on read. Make it funny but real. Just the quote, nothing else. Max 2 sentences.",
        'default': "Generate a single inspirational quote. Make it meaningful and concise. Just the quote, nothing else. Max 2 sentences."
    }

    prompt = prompts.get(brand_slug, prompts['default'])

    cmd = [
        'curl', '-s', 'http://localhost:11434/api/generate',
        '-d', json.dumps({
            'model': 'mistral:latest',
            'prompt': prompt,
            'stream': False
        })
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        response = json.loads(result.stdout)
        quote = response['response'].strip().strip('"').strip()
        return quote
    except Exception as e:
        print(f"Error generating quote: {e}")
        return "Sometimes being left on read is God's way of saying 'they weren't worth the reply anyway.'"

@quote_bp.route('/api/quotes/generate', methods=['POST'])
def generate_quote():
    """Generate a new daily quote"""
    data = request.get_json() or {}
    brand_slug = data.get('brand_slug', 'leftonreadbygod')

    # Generate quote with Ollama
    quote_text = generate_quote_with_ollama(brand_slug)

    # Save to database
    db = get_db()
    db.execute('''
        INSERT INTO daily_quotes (brand_slug, quote_text, generated_at)
        VALUES (?, ?, ?)
    ''', (brand_slug, quote_text, datetime.now(timezone.utc).isoformat()))
    db.commit()
    quote_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
    db.close()

    return jsonify({
        'success': True,
        'quote_id': quote_id,
        'quote': quote_text,
        'generated_at': datetime.now(timezone.utc).isoformat()
    })

@quote_bp.route('/api/quotes/daily', methods=['GET'])
def get_daily_quote():
    """Get the latest daily quote for a brand"""
    brand_slug = request.args.get('brand_slug', 'leftonreadbygod')

    db = get_db()

    # Get most recent quote
    quote = db.execute('''
        SELECT * FROM daily_quotes
        WHERE brand_slug = ? AND active = 1
        ORDER BY generated_at DESC
        LIMIT 1
    ''', (brand_slug,)).fetchone()

    if not quote:
        # Generate first quote if none exists
        db.close()
        return generate_quote()

    # Increment view count
    db.execute('UPDATE daily_quotes SET views = views + 1 WHERE id = ?', (quote['id'],))
    db.commit()
    db.close()

    return jsonify({
        'success': True,
        'quote_id': quote['id'],
        'quote': quote['quote_text'],
        'generated_at': quote['generated_at'],
        'views': quote['views'] + 1
    })

@quote_bp.route('/api/quotes/all', methods=['GET'])
def get_all_quotes():
    """Get all quotes for a brand (paginated)"""
    brand_slug = request.args.get('brand_slug', 'leftonreadbygod')
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))

    db = get_db()
    quotes = db.execute('''
        SELECT * FROM daily_quotes
        WHERE brand_slug = ? AND active = 1
        ORDER BY generated_at DESC
        LIMIT ? OFFSET ?
    ''', (brand_slug, limit, offset)).fetchall()
    db.close()

    return jsonify({
        'success': True,
        'quotes': [dict(q) for q in quotes],
        'count': len(quotes)
    })

# Initialize on import
init_quote_tables()
