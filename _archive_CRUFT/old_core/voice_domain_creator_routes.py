#!/usr/bin/env python3
"""
Voice Domain Creator Routes - Ollama-Powered Domain Generator

Flask routes for creating custom voice capsule domains:
- /domain-creator - Web UI to create new domains
- /api/domain/generate-questions - Use Ollama to generate questions
- /api/domain/save - Save domain + questions to database
- /api/domain/templates - List existing domains as templates
"""

from flask import Blueprint, render_template, request, jsonify
from database import get_db
from ollama_client import OllamaClient
import json
import re
import qrcode
from io import BytesIO
import base64
from config import BASE_URL


# Create blueprint
voice_domain_creator_bp = Blueprint('voice_domain_creator', __name__)


@voice_domain_creator_bp.route('/domain-creator')
def domain_creator():
    """
    Web interface for creating custom voice capsule domains

    Shows:
    - Form to enter domain details (name, theme, vibe, rotation)
    - Button to generate questions with Ollama
    - Question review/edit interface
    - QR code generation
    """
    return render_template('voice_domain_creator.html')


@voice_domain_creator_bp.route('/api/domain/generate-questions', methods=['POST'])
def api_generate_questions():
    """
    Generate questions using Ollama based on theme/vibe

    Request JSON:
    {
        "theme": "Daily productivity habits",
        "vibe": "motivational",
        "num_questions": 12,
        "rotation_period": "weekly"
    }

    Returns:
    {
        "success": true,
        "questions": [
            {
                "question_text": "What productivity win are you proud of today?",
                "category": "achievement",
                "vibe": "motivational"
            },
            ...
        ]
    }
    """
    data = request.get_json()

    theme = data.get('theme', '').strip()
    vibe = data.get('vibe', 'thoughtful').strip()
    num_questions = int(data.get('num_questions', 12))
    rotation_period = data.get('rotation_period', 'monthly')

    if not theme:
        return jsonify({
            'success': False,
            'error': 'Theme is required'
        }), 400

    # Build Ollama prompt
    system_prompt = """You are an expert at designing thought-provoking questions for voice time capsules.
Your questions should be:
- Personal and introspective
- Open-ended (not yes/no)
- Encourage 60-120 second voice responses
- Build on the theme and vibe provided

Output ONLY valid JSON array with no other text. Each question must have:
- question_text: The actual question
- category: A short category (1-2 words)
- vibe: The emotional tone (thoughtful, bold, vulnerable, etc.)"""

    user_prompt = f"""Generate {num_questions} questions for a voice time capsule domain.

Theme: {theme}
Target Vibe: {vibe}
Rotation: Users get one question every {rotation_period}

Output format (JSON array only, no markdown, no other text):
[
  {{
    "question_text": "Your first question here?",
    "category": "category1",
    "vibe": "{vibe}"
  }},
  ...
]"""

    # Call Ollama
    ollama = OllamaClient()

    # Check if Ollama is running
    if not ollama.check_health():
        return jsonify({
            'success': False,
            'error': 'Ollama is not running. Start it with: ollama serve'
        }), 503

    # Generate questions
    result = ollama.generate(
        prompt=user_prompt,
        system_prompt=system_prompt,
        model='llama3.2',
        temperature=0.8,
        max_tokens=2000,
        timeout=90
    )

    if not result['success']:
        return jsonify({
            'success': False,
            'error': result.get('error', 'Ollama generation failed')
        }), 500

    # Parse JSON response from Ollama
    try:
        response_text = result['response'].strip()

        # Remove markdown code blocks if present
        response_text = re.sub(r'^```json\s*', '', response_text)
        response_text = re.sub(r'^```\s*', '', response_text)
        response_text = re.sub(r'\s*```$', '', response_text)

        # Parse JSON
        questions = json.loads(response_text)

        # Validate structure
        if not isinstance(questions, list):
            raise ValueError("Response is not a list")

        if len(questions) == 0:
            raise ValueError("No questions generated")

        # Ensure each question has required fields
        validated_questions = []
        for i, q in enumerate(questions):
            if not isinstance(q, dict):
                continue

            validated_questions.append({
                'question_text': q.get('question_text', f'Question {i+1}'),
                'category': q.get('category', 'general'),
                'vibe': q.get('vibe', vibe),
                'rotation_order': i + 1
            })

        return jsonify({
            'success': True,
            'questions': validated_questions,
            'model': result.get('model'),
            'generation_time_ms': result.get('time_ms')
        })

    except json.JSONDecodeError as e:
        return jsonify({
            'success': False,
            'error': f'Failed to parse Ollama response as JSON: {str(e)}',
            'raw_response': result['response'][:500]  # First 500 chars for debugging
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error processing questions: {str(e)}'
        }), 500


@voice_domain_creator_bp.route('/api/domain/save', methods=['POST'])
def api_save_domain():
    """
    Save a new domain with its questions to the database

    Request JSON:
    {
        "domain_slug": "myproductivity",
        "display_name": "My Productivity Journey",
        "theme": "Daily productivity habits",
        "rotation_period": "weekly",
        "expected_duration_seconds": 90,
        "questions": [
            {
                "question_text": "...",
                "category": "...",
                "vibe": "...",
                "rotation_order": 1
            },
            ...
        ]
    }

    Returns:
    {
        "success": true,
        "domain_slug": "myproductivity",
        "num_questions": 12,
        "qr_code_url": "/qr-question?domain=myproductivity",
        "qr_code_image": "data:image/png;base64,..."
    }
    """
    data = request.get_json()

    domain_slug = data.get('domain_slug', '').strip().lower()
    display_name = data.get('display_name', '').strip()
    theme = data.get('theme', '').strip()
    rotation_period = data.get('rotation_period', 'monthly')
    expected_duration = int(data.get('expected_duration_seconds', 90))
    questions = data.get('questions', [])

    # Validation
    if not domain_slug:
        return jsonify({'success': False, 'error': 'Domain slug is required'}), 400

    if not re.match(r'^[a-z0-9_-]+$', domain_slug):
        return jsonify({
            'success': False,
            'error': 'Domain slug must contain only lowercase letters, numbers, hyphens, and underscores'
        }), 400

    if len(questions) == 0:
        return jsonify({'success': False, 'error': 'At least one question is required'}), 400

    db = get_db()

    # Check if domain already exists
    existing = db.execute(
        'SELECT COUNT(*) as count FROM voice_questions WHERE domain = ?',
        (domain_slug,)
    ).fetchone()

    if existing['count'] > 0:
        return jsonify({
            'success': False,
            'error': f'Domain "{domain_slug}" already exists. Choose a different name.'
        }), 409

    # Insert all questions
    try:
        for question in questions:
            db.execute('''
                INSERT INTO voice_questions
                (question_text, domain, category, rotation_period, rotation_order,
                 vibe, expected_duration_seconds, active)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            ''', (
                question.get('question_text'),
                domain_slug,
                question.get('category', 'general'),
                rotation_period,
                question.get('rotation_order', 1),
                question.get('vibe', 'thoughtful'),
                expected_duration
            ))

        db.commit()

        # Generate QR code
        qr_url = f"{BASE_URL}/qr-question?domain={domain_slug}"

        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(qr_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()

        return jsonify({
            'success': True,
            'domain_slug': domain_slug,
            'display_name': display_name,
            'theme': theme,
            'num_questions': len(questions),
            'qr_code_url': qr_url,
            'qr_code_image': f'data:image/png;base64,{qr_code_base64}'
        })

    except Exception as e:
        db.rollback()
        return jsonify({
            'success': False,
            'error': f'Database error: {str(e)}'
        }), 500


@voice_domain_creator_bp.route('/api/domain/templates')
def api_domain_templates():
    """
    List all existing voice capsule domains that can be used as templates

    Returns:
    {
        "success": true,
        "templates": [
            {
                "domain": "calriven",
                "num_questions": 12,
                "rotation_period": "monthly",
                "sample_question": "What do you own that you wish you didn't?",
                "categories": ["ownership", "control", "generosity"]
            },
            ...
        ]
    }
    """
    db = get_db()

    # Get all domains with question counts
    domains = db.execute('''
        SELECT
            domain,
            rotation_period,
            COUNT(*) as num_questions,
            GROUP_CONCAT(DISTINCT category) as categories
        FROM voice_questions
        WHERE active = 1
        GROUP BY domain, rotation_period
        ORDER BY domain ASC
    ''').fetchall()

    templates = []
    for domain_row in domains:
        domain = domain_row['domain']

        # Get a sample question
        sample = db.execute('''
            SELECT question_text FROM voice_questions
            WHERE domain = ? AND active = 1
            ORDER BY rotation_order ASC
            LIMIT 1
        ''', (domain,)).fetchone()

        templates.append({
            'domain': domain,
            'num_questions': domain_row['num_questions'],
            'rotation_period': domain_row['rotation_period'],
            'sample_question': sample['question_text'] if sample else '',
            'categories': domain_row['categories'].split(',') if domain_row['categories'] else []
        })

    return jsonify({
        'success': True,
        'templates': templates
    })


@voice_domain_creator_bp.route('/api/domain/clone', methods=['POST'])
def api_clone_domain():
    """
    Clone an existing domain as a starting template

    Request JSON:
    {
        "source_domain": "calriven",
        "new_domain_slug": "myownership"
    }

    Returns all questions from source domain with new domain slug
    """
    data = request.get_json()

    source_domain = data.get('source_domain', '').strip()
    new_slug = data.get('new_domain_slug', '').strip().lower()

    if not source_domain or not new_slug:
        return jsonify({
            'success': False,
            'error': 'Both source_domain and new_domain_slug are required'
        }), 400

    db = get_db()

    # Get all questions from source domain
    questions = db.execute('''
        SELECT question_text, category, vibe, rotation_order, rotation_period,
               expected_duration_seconds
        FROM voice_questions
        WHERE domain = ? AND active = 1
        ORDER BY rotation_order ASC
    ''', (source_domain,)).fetchall()

    if not questions:
        return jsonify({
            'success': False,
            'error': f'Source domain "{source_domain}" not found'
        }), 404

    # Return questions for editing
    return jsonify({
        'success': True,
        'source_domain': source_domain,
        'new_domain_slug': new_slug,
        'rotation_period': questions[0]['rotation_period'] if questions else 'monthly',
        'expected_duration_seconds': questions[0]['expected_duration_seconds'] if questions else 90,
        'questions': [dict(q) for q in questions]
    })


def register_voice_domain_creator_routes(app):
    """Register voice domain creator routes with Flask app"""
    app.register_blueprint(voice_domain_creator_bp)
    print("✅ Voice Domain Creator routes registered")


if __name__ == '__main__':
    print("Voice Domain Creator Routes")
    print("")
    print("Routes:")
    print("  GET  /domain-creator - Create new domain UI")
    print("  POST /api/domain/generate-questions - Generate questions with Ollama")
    print("  POST /api/domain/save - Save domain to database")
    print("  GET  /api/domain/templates - List existing domains")
    print("  POST /api/domain/clone - Clone existing domain")
