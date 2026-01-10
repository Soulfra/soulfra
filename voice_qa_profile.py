"""
Voice Q&A Profile Builder
Build profiles by answering questions out loud instead of typing README
"""
from flask import Blueprint, request, jsonify, redirect
import os
import json
import hashlib
from datetime import datetime
from database import get_db

# Ollama helper function
def ask_ollama(prompt, model='llama3.2:latest'):
    """Simple Ollama API wrapper"""
    import requests
    try:
        response = requests.post('http://localhost:11434/api/generate', json={
            'model': model,
            'prompt': prompt,
            'stream': False
        }, timeout=120)
        return response.json().get('response', '')
    except Exception as e:
        print(f"Ollama error: {e}")
        return ''

qa_profile_bp = Blueprint('qa_profile', __name__)

# Database initialization
def init_qa_tables():
    """Create tables for voice Q&A sessions"""
    db = get_db()

    db.execute('''
        CREATE TABLE IF NOT EXISTS voice_qa_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            total_questions INTEGER DEFAULT 0,
            answered_questions INTEGER DEFAULT 0,
            claimed_by_user_id INTEGER,
            claimed_at TIMESTAMP
        )
    ''')

    db.execute('''
        CREATE TABLE IF NOT EXISTS voice_qa_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            question_id TEXT NOT NULL,
            question_text TEXT NOT NULL,
            category TEXT NOT NULL,
            recording_id INTEGER REFERENCES simple_voice_recordings(id),
            transcript TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES voice_qa_sessions(session_id)
        )
    ''')

    db.execute('''
        CREATE TABLE IF NOT EXISTS voice_qa_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE NOT NULL,
            skills_detected TEXT,  -- JSON array
            reasoning_score INTEGER,  -- 1-10
            reasoning_quality TEXT,  -- "basic", "good", "advanced"
            infra_score INTEGER,  -- 1-10
            infra_quality TEXT,  -- "beginner", "intermediate", "expert"
            collaboration_mentions TEXT,  -- JSON array of people
            projects_mentioned TEXT,  -- JSON array
            goals_mentioned TEXT,  -- JSON array
            analysis_completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES voice_qa_sessions(session_id)
        )
    ''')

    db.commit()
    print("✅ Voice Q&A tables initialized")

init_qa_tables()

@qa_profile_bp.route('/api/voice-qa/answer', methods=['POST'])
def process_qa_answer():
    """
    Receive voice answer, transcribe, store, analyze

    POST /api/voice-qa/answer
    Form data:
        - audio (file): WebM audio
        - session_id (str): Unique session ID
        - question_id (str): Question identifier
        - question_text (str): The question asked
        - category (str): Question category
    """
    try:
        audio_file = request.files.get('audio')
        session_id = request.form.get('session_id')
        question_id = request.form.get('question_id')
        question_text = request.form.get('question_text')
        category = request.form.get('category')

        if not all([audio_file, session_id, question_id]):
            return jsonify({'error': 'Missing required fields'}), 400

        db = get_db()

        # Create session if doesn't exist
        session = db.execute(
            'SELECT * FROM voice_qa_sessions WHERE session_id = ?',
            (session_id,)
        ).fetchone()

        if not session:
            db.execute('''
                INSERT INTO voice_qa_sessions (session_id, total_questions)
                VALUES (?, 0)
            ''', (session_id,))
            db.commit()

        # Save audio file to disk
        recordings_dir = 'voice-archive/recordings'
        os.makedirs(recordings_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"qa_{session_id}_{question_id}_{timestamp}.webm"
        filepath = os.path.join(recordings_dir, filename)

        audio_file.save(filepath)

        # Store in simple_voice_recordings table
        db.execute('''
            INSERT INTO simple_voice_recordings (
                user_id, filename, file_path, created_at
            ) VALUES (?, ?, ?, ?)
        ''', (None, filename, filepath, datetime.now()))
        db.commit()

        recording_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]

        # Transcribe with Whisper
        transcript = transcribe_audio(filepath)

        if transcript:
            db.execute('''
                UPDATE simple_voice_recordings
                SET transcription = ?, transcription_completed_at = ?
                WHERE id = ?
            ''', (transcript, datetime.now(), recording_id))
            db.commit()

        # Store Q&A answer
        db.execute('''
            INSERT INTO voice_qa_answers (
                session_id, question_id, question_text, category,
                recording_id, transcript
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (session_id, question_id, question_text, category, recording_id, transcript))
        db.commit()

        # Update session counts
        db.execute('''
            UPDATE voice_qa_sessions
            SET answered_questions = answered_questions + 1
            WHERE session_id = ?
        ''', (session_id,))
        db.commit()

        return jsonify({
            'success': True,
            'recording_id': recording_id,
            'transcript': transcript,
            'message': 'Answer saved'
        })

    except Exception as e:
        print(f"Error processing answer: {e}")
        return jsonify({'error': str(e)}), 500

@qa_profile_bp.route('/api/voice-qa/results/<session_id>')
def get_session_results(session_id):
    """
    Get analysis results for completed Q&A session

    GET /api/voice-qa/results/<session_id>
    Returns: skills, reasoning score, infra score, etc.
    """
    db = get_db()

    # Check if analysis exists
    analysis = db.execute(
        'SELECT * FROM voice_qa_analysis WHERE session_id = ?',
        (session_id,)
    ).fetchone()

    if not analysis:
        # Run analysis now
        run_qa_analysis(session_id)

        analysis = db.execute(
            'SELECT * FROM voice_qa_analysis WHERE session_id = ?',
            (session_id,)
        ).fetchone()

    if not analysis:
        return jsonify({'error': 'Analysis not complete'}), 404

    return jsonify({
        'success': True,
        'session_id': session_id,
        'skills': json.loads(analysis['skills_detected'] or '[]'),
        'reasoning_score': analysis['reasoning_score'],
        'reasoning_quality': analysis['reasoning_quality'],
        'infra_score': analysis['infra_score'],
        'infra_quality': analysis['infra_quality'],
        'collaboration_mentions': json.loads(analysis['collaboration_mentions'] or '[]'),
        'projects': json.loads(analysis['projects_mentioned'] or '[]'),
        'goals': json.loads(analysis['goals_mentioned'] or '[]')
    })

@qa_profile_bp.route('/api/voice-qa/generate-profile/<session_id>', methods=['POST'])
def generate_profile_from_qa(session_id):
    """
    Generate README profile from Q&A session

    POST /api/voice-qa/generate-profile/<session_id>
    Body: { user_id, slug }

    Creates profile in user_profiles table
    """
    data = request.json
    user_id = data.get('user_id')
    slug = data.get('slug')

    if not slug:
        return jsonify({'error': 'Slug required'}), 400

    db = get_db()

    # Get analysis
    analysis = db.execute(
        'SELECT * FROM voice_qa_analysis WHERE session_id = ?',
        (session_id,)
    ).fetchone()

    if not analysis:
        return jsonify({'error': 'No analysis found for session'}), 404

    # Get all answers
    answers = db.execute('''
        SELECT question_text, category, transcript
        FROM voice_qa_answers
        WHERE session_id = ? AND transcript IS NOT NULL
        ORDER BY created_at
    ''', (session_id,)).fetchall()

    # Generate README content from answers
    readme_content = generate_readme_from_answers(answers, analysis)

    # Create profile
    db.execute('''
        INSERT INTO user_profiles (
            user_slug, readme_content, skills_claimed,
            projects_want_to_build, created_at
        ) VALUES (?, ?, ?, ?, ?)
    ''', (
        slug,
        readme_content,
        analysis['skills_detected'],
        analysis['projects_mentioned'],
        datetime.now()
    ))
    db.commit()

    # Mark session as claimed
    db.execute('''
        UPDATE voice_qa_sessions
        SET claimed_by_user_id = ?, claimed_at = ?, completed_at = ?
        WHERE session_id = ?
    ''', (user_id, datetime.now(), datetime.now(), session_id))
    db.commit()

    return jsonify({
        'success': True,
        'slug': slug,
        'profile_url': f'/{slug}'
    })

@qa_profile_bp.route('/api/voice-qa/claim-github')
def claim_qa_github():
    """
    Start GitHub OAuth flow to claim Q&A session
    Redirects to GitHub, then back to callback
    """
    session_id = request.args.get('session_id')

    if not session_id:
        return jsonify({'error': 'session_id required'}), 400

    # Store session_id in Flask session for callback
    from flask import session as flask_session
    flask_session['qa_claiming_session_id'] = session_id

    # Redirect to GitHub OAuth
    from github_oauth import get_github_auth_url
    auth_url = get_github_auth_url(redirect_uri='/api/voice-qa/claim-github/callback')
    return redirect(auth_url)

@qa_profile_bp.route('/api/voice-qa/claim-github/callback')
def claim_qa_github_callback():
    """
    GitHub OAuth callback - Create profile from Q&A session
    """
    from flask import session as flask_session

    code = request.args.get('code')
    session_id = flask_session.get('qa_claiming_session_id')

    if not code or not session_id:
        return jsonify({'error': 'Missing code or session_id'}), 400

    # Exchange code for GitHub access token
    from github_oauth import get_github_access_token, get_github_user

    access_token = get_github_access_token(code)
    if not access_token:
        return jsonify({'error': 'Failed to get GitHub access token'}), 400

    github_user = get_github_user(access_token)
    if not github_user:
        return jsonify({'error': 'Failed to get GitHub user info'}), 400

    username = github_user.get('login')
    slug = username.lower()

    db = get_db()

    # Check if user exists
    user = db.execute(
        'SELECT id FROM users WHERE github_username = ?',
        (username,)
    ).fetchone()

    if not user:
        # Create new user
        db.execute('''
            INSERT INTO users (username, github_username, created_at)
            VALUES (?, ?, ?)
        ''', (username, username, datetime.now()))
        db.commit()

        user_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
    else:
        user_id = user['id']

    # Generate profile from Q&A session
    analysis = db.execute(
        'SELECT * FROM voice_qa_analysis WHERE session_id = ?',
        (session_id,)
    ).fetchone()

    if not analysis:
        # Run analysis if not done yet
        run_qa_analysis(session_id)
        analysis = db.execute(
            'SELECT * FROM voice_qa_analysis WHERE session_id = ?',
            (session_id,)
        ).fetchone()

    # Get all answers
    answers = db.execute('''
        SELECT question_text, category, transcript
        FROM voice_qa_answers
        WHERE session_id = ? AND transcript IS NOT NULL
        ORDER BY created_at
    ''', (session_id,)).fetchall()

    # Generate README
    readme_content = generate_readme_from_answers(answers, analysis)

    # Create profile
    db.execute('''
        INSERT OR REPLACE INTO user_profiles (
            user_slug, readme_content, skills_claimed,
            projects_want_to_build, github_username, created_at
        ) VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        slug,
        readme_content,
        analysis['skills_detected'],
        analysis['projects_mentioned'],
        username,
        datetime.now()
    ))
    db.commit()

    # Mark session as claimed
    db.execute('''
        UPDATE voice_qa_sessions
        SET claimed_by_user_id = ?, claimed_at = ?
        WHERE session_id = ?
    ''', (user_id, datetime.now(), session_id))
    db.commit()

    # Redirect to profile page
    return redirect(f'/{slug}')

# Helper functions

def transcribe_audio(filepath):
    """Transcribe audio with Whisper"""
    try:
        import whisper
        model = whisper.load_model("base")
        result = model.transcribe(filepath)
        return result['text']
    except Exception as e:
        print(f"Whisper transcription failed: {e}")
        return None

def run_qa_analysis(session_id):
    """
    Analyze all answers in a Q&A session with Ollama
    Extract: skills, reasoning quality, infrastructure knowledge
    """
    db = get_db()

    # Get all transcripts
    answers = db.execute('''
        SELECT question_text, category, transcript
        FROM voice_qa_answers
        WHERE session_id = ? AND transcript IS NOT NULL
    ''', (session_id,)).fetchall()

    if not answers:
        return

    # Combine all transcripts
    combined_text = '\n\n'.join([
        f"Q ({a['category']}): {a['question_text']}\nA: {a['transcript']}"
        for a in answers
    ])

    # Extract skills
    skills_prompt = f"""
    Analyze these voice Q&A answers and extract technical skills mentioned.
    Return ONLY a JSON array of skill strings, nothing else.

    Answers:
    {combined_text}

    Skills (JSON array):
    """

    skills_response = ask_ollama(skills_prompt, model='llama3.2:latest')
    skills = []
    try:
        skills = json.loads(skills_response)
    except:
        # Fallback: extract anything between brackets
        import re
        match = re.search(r'\[(.*?)\]', skills_response, re.DOTALL)
        if match:
            try:
                skills = json.loads(f'[{match.group(1)}]')
            except:
                skills = []

    # Evaluate reasoning quality
    reasoning_prompt = f"""
    Evaluate the reasoning quality in these answers. Rate 1-10 and classify as "basic", "good", or "advanced".

    Consider:
    - Do they explain WHY, not just WHAT?
    - Do they consider trade-offs?
    - Do they show depth of understanding?

    Answers:
    {combined_text}

    Return ONLY a JSON object: {{"score": 8, "quality": "good"}}
    """

    reasoning_response = ask_ollama(reasoning_prompt, model='llama3.2:latest')
    reasoning_score = 5
    reasoning_quality = "basic"

    try:
        reasoning_data = json.loads(reasoning_response)
        reasoning_score = reasoning_data.get('score', 5)
        reasoning_quality = reasoning_data.get('quality', 'basic')
    except:
        pass

    # Evaluate infrastructure knowledge
    infra_prompt = f"""
    Evaluate infrastructure knowledge from these answers. Rate 1-10 and classify as "beginner", "intermediate", or "expert".

    Look for mentions of:
    - Deployment processes
    - Database choices
    - Cloud vs local vs self-hosted
    - DevOps practices

    Answers:
    {combined_text}

    Return ONLY a JSON object: {{"score": 7, "quality": "intermediate"}}
    """

    infra_response = ask_ollama(infra_prompt, model='llama3.2:latest')
    infra_score = 5
    infra_quality = "beginner"

    try:
        infra_data = json.loads(infra_response)
        infra_score = infra_data.get('score', 5)
        infra_quality = infra_data.get('quality', 'beginner')
    except:
        pass

    # Extract people mentioned (for collaboration tracking)
    people_prompt = f"""
    Extract names of people mentioned in these answers (teammates, mentors, collaborators).
    Return ONLY a JSON array of names.

    Answers:
    {combined_text}

    Names (JSON array):
    """

    people_response = ask_ollama(people_prompt, model='llama3.2:latest')
    people = []
    try:
        people = json.loads(people_response)
    except:
        pass

    # Extract projects mentioned
    projects_prompt = f"""
    Extract project names or descriptions mentioned. Return ONLY a JSON array.

    Answers:
    {combined_text}

    Projects (JSON array):
    """

    projects_response = ask_ollama(projects_prompt, model='llama3.2:latest')
    projects = []
    try:
        projects = json.loads(projects_response)
    except:
        pass

    # Extract goals
    goals_prompt = f"""
    Extract goals or things they want to build. Return ONLY a JSON array.

    Answers:
    {combined_text}

    Goals (JSON array):
    """

    goals_response = ask_ollama(goals_prompt, model='llama3.2:latest')
    goals = []
    try:
        goals = json.loads(goals_response)
    except:
        pass

    # Store analysis
    db.execute('''
        INSERT OR REPLACE INTO voice_qa_analysis (
            session_id, skills_detected, reasoning_score, reasoning_quality,
            infra_score, infra_quality, collaboration_mentions,
            projects_mentioned, goals_mentioned
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        session_id,
        json.dumps(skills),
        reasoning_score,
        reasoning_quality,
        infra_score,
        infra_quality,
        json.dumps(people),
        json.dumps(projects),
        json.dumps(goals)
    ))
    db.commit()

def generate_readme_from_answers(answers, analysis):
    """Generate README content from Q&A answers"""

    skills = json.loads(analysis['skills_detected'] or '[]')
    projects = json.loads(analysis['projects_mentioned'] or '[]')
    goals = json.loads(analysis['goals_mentioned'] or '[]')

    # Find bio from first technical answer
    bio = ""
    for answer in answers:
        if answer['category'] == 'Technical' and answer['transcript']:
            bio = answer['transcript'][:200]
            break

    readme = f"""# About Me

{bio}

## Skills

{chr(10).join([f"- {skill}" for skill in skills])}

## Projects

{chr(10).join([f"- {project}" for project in projects])}

## What I Want to Build

{chr(10).join([f"- {goal}" for goal in goals])}

---

*Profile built from voice Q&A on CringeProof*
"""

    return readme
