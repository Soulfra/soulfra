"""
CringeProof → AI Persona Assignment

Assigns users to one of the 3 main AI personas based on CringeProof game results:
- CalRiven: Intelligent, efficient (logic-driven)
- Soulfra: Secure, trustworthy (balanced)
- DeathToData: Rebellious, defiant (emotion-driven)

These personas then act as "filters" for the user's soul,
creating a 3-way argument system in the Tribunal.
"""

import sqlite3
from datetime import datetime


class PersonaAssigner:
    """
    Assigns AI personas based on CringeProof narrative quiz results
    """

    def __init__(self, db_path='soulfra.db'):
        self.db_path = db_path

    def get_db(self):
        db = sqlite3.connect(self.db_path)
        db.row_factory = sqlite3.Row
        return db

    def calculate_persona_from_answers(self, answers):
        """
        Analyze CringeProof answers to determine AI persona

        Args:
            answers: List of answer objects with {question_id, rating (1-5), category}

        Returns:
            Persona name: 'calriven', 'soulfra', or 'deathtodata'
        """
        # Score accumulation
        logic_score = 0    # CalRiven: rational, analytical
        balance_score = 0  # Soulfra: balanced, trustworthy
        emotion_score = 0  # DeathToData: rebellious, defiant

        # Categorize questions and weight responses
        for answer in answers:
            rating = answer.get('rating', 3)  # 1-5 scale
            category = answer.get('category', 'general').lower()

            # Questions about identity/memory → logic vs emotion
            if category in ['identity', 'memory', 'consciousness']:
                if rating >= 4:
                    logic_score += 2  # High agreement = analytical
                elif rating <= 2:
                    emotion_score += 2  # Low agreement = intuitive
                else:
                    balance_score += 1

            # Questions about freedom/choice → rebellion vs security
            elif category in ['freedom', 'choice', 'autonomy']:
                if rating >= 4:
                    emotion_score += 2  # High agreement = rebellious
                elif rating <= 2:
                    logic_score += 2  # Low agreement = rules-based
                else:
                    balance_score += 1

            # Questions about truth/trust → security vs defiance
            elif category in ['truth', 'trust', 'honesty']:
                if rating >= 4:
                    balance_score += 2  # High trust = soulfra
                elif rating <= 2:
                    emotion_score += 2  # Low trust = deathtodata
                else:
                    logic_score += 1

            # Questions about AI/technology → analytical vs human
            elif category in ['ai', 'technology', 'artificial']:
                if rating >= 4:
                    logic_score += 2  # Pro-AI = calriven
                elif rating <= 2:
                    emotion_score += 2  # Anti-AI = deathtodata
                else:
                    balance_score += 1

            # Default: All other questions add to balance
            else:
                balance_score += 1

        # Determine winning persona
        scores = {
            'calriven': logic_score,
            'soulfra': balance_score,
            'deathtodata': emotion_score
        }

        winning_persona = max(scores, key=scores.get)

        return {
            'persona': winning_persona,
            'scores': scores,
            'total_answers': len(answers)
        }

    def assign_persona_to_user(self, user_id, session_id):
        """
        Assign AI persona based on completed CringeProof session

        Args:
            user_id: User's ID
            session_id: Narrative session ID from CringeProof game

        Returns:
            Dict with persona info
        """
        db = self.get_db()

        try:
            # Get session data
            session = db.execute('''
                SELECT game_state, status
                FROM narrative_sessions
                WHERE id = ? AND user_id = ?
            ''', (session_id, user_id)).fetchone()

            if not session:
                return {'error': 'Session not found'}

            if session['status'] != 'completed':
                return {'error': 'Session not completed yet'}

            # Parse game state (JSON with answers)
            import json
            game_state = json.loads(session['game_state'] or '{}')
            answers = game_state.get('answers', [])

            if not answers:
                return {'error': 'No answers found in session'}

            # Calculate persona
            result = self.calculate_persona_from_answers(answers)
            persona_name = result['persona']

            # Get persona user_id
            persona = db.execute('''
                SELECT id, username, display_name
                FROM users
                WHERE username = ? AND is_ai_persona = 1
            ''', (persona_name,)).fetchone()

            if not persona:
                return {'error': f'Persona {persona_name} not found'}

            # Update user's assigned persona (store in user table or create connection)
            db.execute('''
                UPDATE users
                SET ai_persona_id = ?, updated_at = ?
                WHERE id = ?
            ''', (persona['id'], datetime.now().isoformat(), user_id))

            # Create soul score entry if not exists
            db.execute('''
                INSERT OR IGNORE INTO soul_scores
                (entity_type, entity_id, composite_score, tier, total_networks)
                VALUES ('user', ?, ?, ?, 1)
            ''', (user_id, result['scores'][persona_name] / 10.0, 'Moderate'))

            # Record the assignment in history
            db.execute('''
                INSERT INTO soul_history
                (user_id, event_type, description, metadata)
                VALUES (?, 'persona_assigned', ?, ?)
            ''', (user_id,
                  f'Assigned to {persona["display_name"]} based on CringeProof results',
                  json.dumps(result)))

            db.commit()

            return {
                'success': True,
                'user_id': user_id,
                'persona_id': persona['id'],
                'persona_name': persona_name,
                'persona_display': persona['display_name'],
                'scores': result['scores'],
                'rationale': self._get_persona_rationale(persona_name, result['scores'])
            }

        except Exception as e:
            db.rollback()
            return {'error': str(e)}
        finally:
            db.close()

    def _get_persona_rationale(self, persona, scores):
        """Generate explanation for why this persona was assigned"""
        rationales = {
            'calriven': f"Your logical score ({scores['calriven']}) suggests you value efficiency and analytical thinking. CalRiven will guide your soul through rational pathways.",
            'soulfra': f"Your balanced score ({scores['soulfra']}) shows you value trust and security. Soulfra will help maintain harmony in your soul's journey.",
            'deathtodata': f"Your rebellious score ({scores['deathtodata']}) indicates you challenge norms and value freedom. DeathToData will champion your soul's autonomy."
        }
        return rationales.get(persona, "Persona assigned based on your unique responses.")

    def get_user_persona(self, user_id):
        """
        Get user's assigned AI persona

        Returns:
            Dict with persona info or None
        """
        db = self.get_db()

        try:
            result = db.execute('''
                SELECT
                    u.ai_persona_id,
                    p.username as persona_username,
                    p.display_name as persona_display,
                    p.bio as persona_bio
                FROM users u
                LEFT JOIN users p ON u.ai_persona_id = p.id
                WHERE u.id = ?
            ''', (user_id,)).fetchone()

            if not result or not result['ai_persona_id']:
                return None

            return {
                'persona_id': result['ai_persona_id'],
                'persona_username': result['persona_username'],
                'persona_display': result['persona_display'],
                'persona_bio': result['persona_bio']
            }

        finally:
            db.close()

    def get_tribunal_personas(self):
        """
        Get all 3 tribunal personas for 3-way argument

        Returns:
            List of persona dicts
        """
        db = self.get_db()

        try:
            personas = db.execute('''
                SELECT id, username, display_name, bio
                FROM users
                WHERE username IN ('calriven', 'soulfra', 'deathtodata')
                  AND is_ai_persona = 1
                ORDER BY
                    CASE username
                        WHEN 'calriven' THEN 1
                        WHEN 'soulfra' THEN 2
                        WHEN 'deathtodata' THEN 3
                    END
            ''').fetchall()

            return [
                {
                    'id': p['id'],
                    'username': p['username'],
                    'display_name': p['display_name'],
                    'bio': p['bio'],
                    'role': self._get_tribunal_role(p['username'])
                }
                for p in personas
            ]

        finally:
            db.close()

    def _get_tribunal_role(self, persona):
        """Define each persona's role in tribunal 3-way argument"""
        roles = {
            'calriven': 'Logical Prosecutor - Argues from efficiency and reason',
            'soulfra': 'Balanced Judge - Seeks truth and fairness',
            'deathtodata': 'Rebellious Defender - Challenges authority and norms'
        }
        return roles.get(persona, 'Observer')


def init_cringeproof_personas(app):
    """Initialize persona assignment routes"""
    from flask import Blueprint, jsonify, request, session

    personas_bp = Blueprint('cringeproof_personas', __name__)

    @personas_bp.route('/api/cringeproof/assign-persona', methods=['POST'])
    def assign_persona():
        """
        Assign AI persona based on completed CringeProof game

        POST /api/cringeproof/assign-persona
        {
            "session_id": 123
        }
        """
        data = request.get_json() or {}
        session_id = data.get('session_id')
        user_id = session.get('user_id')

        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401

        if not session_id:
            return jsonify({'error': 'Missing session_id'}), 400

        assigner = PersonaAssigner()
        result = assigner.assign_persona_to_user(user_id, session_id)

        if 'error' in result:
            return jsonify(result), 400

        return jsonify(result)

    @personas_bp.route('/api/cringeproof/my-persona')
    def my_persona():
        """Get current user's assigned persona"""
        user_id = session.get('user_id')

        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401

        assigner = PersonaAssigner()
        persona = assigner.get_user_persona(user_id)

        if not persona:
            return jsonify({'assigned': False, 'message': 'No persona assigned yet. Complete CringeProof to get one!'})

        return jsonify({'assigned': True, 'persona': persona})

    @personas_bp.route('/api/tribunal/personas')
    def tribunal_personas():
        """Get all 3 tribunal personas for 3-way argument display"""
        assigner = PersonaAssigner()
        personas = assigner.get_tribunal_personas()

        return jsonify({
            'success': True,
            'personas': personas,
            'description': '3-way AI argument system: Logic vs Balance vs Rebellion'
        })

    app.register_blueprint(personas_bp)
