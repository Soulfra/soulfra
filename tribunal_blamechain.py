"""
Tribunal + Blamechain Integration

Connects Kangaroo Court tribunal with message edit history (blamechain).

Creates 3-way AI argument system where:
- CalRiven (Logic): Argues from efficiency and analytical reasoning
- Soulfra (Balance): Seeks truth and fairness, weighs both sides
- DeathToData (Rebellion): Challenges authority, defends individual freedom

Edit history becomes evidence that all 3 personas examine and debate.
"""

import sqlite3
import json
from datetime import datetime
from flask import Blueprint, jsonify, request, session, g


tribunal_bp = Blueprint('tribunal_blamechain', __name__)


def get_db():
    """Get database connection"""
    if 'db' not in g:
        g.db = sqlite3.connect('soulfra.db')
        g.db.row_factory = sqlite3.Row
    return g.db


class TribunalJudge:
    """
    3-way AI tribunal system with blamechain evidence
    """

    def __init__(self, db):
        self.db = db
        self.personas = self._get_personas()

    def _get_personas(self):
        """Get the 3 tribunal personas"""
        personas = self.db.execute('''
            SELECT id, username, display_name, bio
            FROM users
            WHERE username IN ('calriven', 'soulfra', 'deathtodata')
              AND is_ai_persona = 1
        ''').fetchall()

        return {p['username']: dict(p) for p in personas}

    def analyze_edit_history(self, message_table, message_id):
        """
        Analyze message edit history from all 3 AI perspectives

        Returns dict with each persona's analysis
        """
        # Get edit history
        history = self.db.execute('''
            SELECT * FROM v_message_blamechain
            WHERE message_table = ? AND message_id = ?
            ORDER BY version_number ASC
        ''', (message_table, message_id)).fetchall()

        if not history:
            return None

        # Calculate edit metrics
        total_edits = len(history) - 1  # Exclude original
        edit_times = []
        for i in range(1, len(history)):
            # Time between edits (simplified - would need proper datetime parsing)
            edit_times.append(1)  # Placeholder

        # Each persona analyzes the evidence
        analyses = {}

        # CalRiven: Logical analysis
        analyses['calriven'] = {
            'verdict': self._calriven_analyze(history, total_edits),
            'reasoning': f"Analyzed {total_edits} edits. "
                        f"Pattern: {self._detect_pattern(history)}. "
                        f"Logical conclusion based on data consistency.",
            'suspicion_level': self._calculate_suspicion(history)
        }

        # Soulfra: Balanced judgment
        analyses['soulfra'] = {
            'verdict': self._soulfra_analyze(history, total_edits),
            'reasoning': f"Considering both intent and impact across {total_edits} edits. "
                        f"Seeking fairness between transparency and right to correct mistakes.",
            'suspicion_level': (analyses['calriven']['suspicion_level'] +
                               self._calculate_emotional_suspicion(history)) / 2
        }

        # DeathToData: Rebellious defense
        analyses['deathtodata'] = {
            'verdict': self._deathtodata_analyze(history, total_edits),
            'reasoning': f"User has right to edit. {total_edits} revisions show thought evolution, "
                        f"not deception. Authority overreaches by tracking every change.",
            'suspicion_level': max(0, self._calculate_suspicion(history) - 30)  # More lenient
        }

        return {
            'message_table': message_table,
            'message_id': message_id,
            'total_versions': len(history),
            'analyses': analyses,
            'consensus': self._calculate_consensus(analyses)
        }

    def _detect_pattern(self, history):
        """Detect edit patterns (CalRiven's analytical approach)"""
        if len(history) <= 2:
            return "minimal edits"
        elif len(history) >= 5:
            return "excessive editing - potential manipulation"
        else:
            return "normal correction pattern"

    def _calculate_suspicion(self, history):
        """Calculate logical suspicion score (0-100)"""
        score = 0

        # Many edits = suspicious
        score += min(len(history) * 10, 40)

        # No edit reasons = suspicious
        no_reason_count = sum(1 for h in history if not h['edit_reason'])
        score += min(no_reason_count * 15, 30)

        # Already flagged = very suspicious
        if any(h['flagged_for_tribunal'] for h in history):
            score += 30

        return min(score, 100)

    def _calculate_emotional_suspicion(self, history):
        """Calculate suspicion based on content changes (for Soulfra balance)"""
        # Placeholder - would analyze content sentiment changes
        return 50

    def _calriven_analyze(self, history, total_edits):
        """CalRiven's logical verdict"""
        suspicion = self._calculate_suspicion(history)

        if suspicion >= 70:
            return "GUILTY"
        elif suspicion <= 30:
            return "INNOCENT"
        else:
            return "REQUIRES_MORE_DATA"

    def _soulfra_analyze(self, history, total_edits):
        """Soulfra's balanced verdict"""
        logical_susp = self._calculate_suspicion(history)
        emotional_susp = self._calculate_emotional_suspicion(history)

        avg_suspicion = (logical_susp + emotional_susp) / 2

        if avg_suspicion >= 60:
            return "GUILTY"
        elif avg_suspicion <= 40:
            return "INNOCENT"
        else:
            return "MONITORING_RECOMMENDED"

    def _deathtodata_analyze(self, history, total_edits):
        """DeathToData's rebellious verdict"""
        # Always defends individual freedom unless overwhelming evidence
        if len(history) >= 8 and all(not h['edit_reason'] for h in history[1:]):
            return "SUSPICIOUS_BUT_FREE"  # Still defends right to edit
        else:
            return "INNOCENT"

    def _calculate_consensus(self, analyses):
        """Determine if all 3 personas agree"""
        verdicts = [a['verdict'] for a in analyses.values()]

        if len(set(verdicts)) == 1:
            return {
                'unanimous': True,
                'verdict': verdicts[0],
                'confidence': 'HIGH'
            }
        elif verdicts.count('GUILTY') >= 2:
            return {
                'unanimous': False,
                'verdict': 'GUILTY',
                'confidence': 'MODERATE',
                'dissent': 'DeathToData likely dissented'
            }
        elif verdicts.count('INNOCENT') >= 2:
            return {
                'unanimous': False,
                'verdict': 'INNOCENT',
                'confidence': 'MODERATE',
                'dissent': 'CalRiven likely dissented'
            }
        else:
            return {
                'unanimous': False,
                'verdict': 'NO_CONSENSUS',
                'confidence': 'LOW',
                'dissent': 'All 3 personas disagree'
            }


@tribunal_bp.route('/api/tribunal/analyze-edits/<message_table>/<int:message_id>')
def analyze_message_edits(message_table, message_id):
    """
    Run 3-way tribunal analysis on message edit history

    GET /api/tribunal/analyze-edits/messages/123

    Returns analysis from all 3 AI personas
    """
    db = get_db()

    # Validate table name
    allowed_tables = ['messages', 'irc_messages', 'dm_messages', 'qr_chat_transcripts']
    if message_table not in allowed_tables:
        return jsonify({'error': 'Invalid message table'}), 400

    try:
        judge = TribunalJudge(db)
        analysis = judge.analyze_edit_history(message_table, message_id)

        if not analysis:
            return jsonify({'error': 'No edit history found'}), 404

        return jsonify({
            'success': True,
            **analysis
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@tribunal_bp.route('/api/tribunal/submit-with-edits', methods=['POST'])
def submit_to_tribunal_with_edits():
    """
    Submit message with edit history to Kangaroo Court

    POST /api/tribunal/submit-with-edits
    {
        "message_table": "messages",
        "message_id": 123,
        "accusation": "User edited message to hide original intent"
    }

    Creates tribunal submission with 3-way AI analysis
    """
    db = get_db()
    data = request.get_json() or {}

    message_table = data.get('message_table')
    message_id = data.get('message_id')
    accusation = data.get('accusation', 'Edit history flagged for review')

    if not all([message_table, message_id]):
        return jsonify({'error': 'Missing required fields'}), 400

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        # Get 3-way analysis
        judge = TribunalJudge(db)
        analysis = judge.analyze_edit_history(message_table, message_id)

        if not analysis:
            return jsonify({'error': 'No edit history found'}), 404

        # Get edit history for evidence
        history = db.execute('''
            SELECT version_number, content, edited_at, editor_username, edit_reason
            FROM v_message_blamechain
            WHERE message_table = ? AND message_id = ?
            ORDER BY version_number ASC
        ''', (message_table, message_id)).fetchall()

        # Build evidence transcript
        evidence_lines = [
            f"=== TRIBUNAL SUBMISSION ===",
            f"Accusation: {accusation}",
            f"",
            f"=== EDIT HISTORY ({len(history)} versions) ===",
        ]

        for h in history:
            evidence_lines.append(f"\n--- Version {h['version_number']} ---")
            evidence_lines.append(f"Time: {h['edited_at']}")
            evidence_lines.append(f"Editor: {h['editor_username']}")
            evidence_lines.append(f"Reason: {h['edit_reason'] or '(none given)'}")
            evidence_lines.append(f"Content: {h['content'][:200]}...")

        evidence_lines.append(f"\n=== 3-WAY AI ANALYSIS ===")
        for persona, data in analysis['analyses'].items():
            evidence_lines.append(f"\n{persona.upper()}: {data['verdict']}")
            evidence_lines.append(f"Reasoning: {data['reasoning']}")
            evidence_lines.append(f"Suspicion: {data['suspicion_level']}/100")

        evidence_lines.append(f"\n=== CONSENSUS ===")
        consensus = analysis['consensus']
        evidence_lines.append(f"Unanimous: {consensus['unanimous']}")
        evidence_lines.append(f"Verdict: {consensus['verdict']}")
        evidence_lines.append(f"Confidence: {consensus['confidence']}")

        transcription = "\n".join(evidence_lines)

        # Create tribunal submission
        db.execute('''
            INSERT INTO kangaroo_submissions
            (user_id, transcription, verdict)
            VALUES (?, ?, ?)
        ''', (user_id, transcription, consensus['verdict']))

        submission_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]

        # Flag history entries
        db.execute('''
            UPDATE message_history
            SET flagged_for_tribunal = 1, tribunal_submission_id = ?
            WHERE message_table = ? AND message_id = ?
        ''', (submission_id, message_table, message_id))

        db.commit()

        return jsonify({
            'success': True,
            'tribunal_submission_id': submission_id,
            'verdict': consensus['verdict'],
            'unanimous': consensus['unanimous'],
            'analyses': analysis['analyses']
        })

    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500


@tribunal_bp.route('/api/tribunal/three-way-debate/<int:submission_id>')
def get_three_way_debate(submission_id):
    """
    Get the 3-way debate transcript for a tribunal case

    Shows how CalRiven, Soulfra, and DeathToData argued

    GET /api/tribunal/three-way-debate/5
    """
    db = get_db()

    try:
        # Get submission
        submission = db.execute('''
            SELECT * FROM kangaroo_submissions WHERE id = ?
        ''', (submission_id,)).fetchone()

        if not submission:
            return jsonify({'error': 'Submission not found'}), 404

        # Parse the 3-way analysis from transcription
        # (In real implementation, store analyses in separate table)
        transcript = submission['transcription']

        return jsonify({
            'success': True,
            'submission_id': submission_id,
            'verdict': submission['verdict'],
            'full_transcript': transcript,
            'debate_participants': ['CalRiven', 'Soulfra', 'DeathToData']
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def init_tribunal_blamechain(app):
    """Initialize tribunal + blamechain integration"""
    app.register_blueprint(tribunal_bp)
