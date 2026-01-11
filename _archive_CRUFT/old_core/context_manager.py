#!/usr/bin/env python3
"""
Context Manager - Query Allocation & Reasoning Router

Tracks user context, allocates memory, routes queries to specialist models.

Architecture:
1. User asks question → Context Manager analyzes it
2. Determines best model (soulfra-model vs deathtodata vs calos vs specialist)
3. Loads conversation history and relevant context
4. Routes to Ollama with enriched prompt
5. Stores response and updates context profile

Context Profile includes:
- Topics user is interested in (keywords, entities)
- Navigation history (which pages visited)
- Questions asked (to avoid repetition)
- Preferred models (learns from user feedback)
- Current thread (multi-turn conversations)
"""

import json
import urllib.request
import urllib.error
from datetime import datetime
from typing import Dict, List, Optional
from database import get_db
from config import OLLAMA_HOST


class ContextManager:
    """Manages user context and routes queries to appropriate models"""

    # Model specializations
    MODEL_SPECIALIZATIONS = {
        'soulfra-model': {
            'expertise': ['security', 'encryption', 'cryptography', 'authentication', 'privacy'],
            'description': 'Security and encryption expert',
            'icon': '🔐'
        },
        'deathtodata-model': {
            'expertise': ['privacy', 'tracking', 'surveillance', 'decentralization', 'data-minimization'],
            'description': 'Privacy and anti-tracking advocate',
            'icon': '🕵️'
        },
        'calos-model': {
            'expertise': ['architecture', 'algorithms', 'performance', 'scalability', 'design-patterns'],
            'description': 'Technical architecture expert',
            'icon': '🏗️'
        },
        'publishing-model': {
            'expertise': ['writing', 'content', 'blogging', 'documentation', 'publishing'],
            'description': 'Content creation specialist',
            'icon': '📝'
        },
        'drseuss-model': {
            'expertise': ['creative', 'storytelling', 'narrative', 'rhyme', 'fun'],
            'description': 'Creative storytelling specialist',
            'icon': '🎭'
        },
        'visual-expert': {
            'expertise': ['images', 'vision', 'ocr', 'visual', 'graphics'],
            'description': 'Visual analysis specialist',
            'icon': '👁️'
        },
        'iiif-expert': {
            'expertise': ['iiif', 'images', 'metadata', 'standards', 'interoperability'],
            'description': 'IIIF and image standards expert',
            'icon': '🖼️'
        },
        'jsonld-expert': {
            'expertise': ['json-ld', 'linked-data', 'semantic-web', 'ontology', 'rdf'],
            'description': 'JSON-LD and semantic web expert',
            'icon': '🔗'
        },
        'codellama:7b': {
            'expertise': ['code', 'programming', 'debugging', 'refactoring', 'syntax'],
            'description': 'Code generation and debugging',
            'icon': '💻'
        },
        'mistral:7b': {
            'expertise': ['general', 'reasoning', 'analysis', 'explanation'],
            'description': 'General purpose reasoning',
            'icon': '🧠'
        }
    }

    def __init__(self, user_id: Optional[int] = None, session_id: Optional[str] = None):
        """
        Initialize context manager

        Args:
            user_id: User ID for tracking history
            session_id: Session ID for conversation threading
        """
        self.user_id = user_id
        self.session_id = session_id or self._generate_session_id()
        self.context_profile = self._load_context_profile()

    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        import hashlib
        timestamp = datetime.now().isoformat()
        data = f"{self.user_id}_{timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def _load_context_profile(self) -> Dict:
        """Load user's context profile from database"""
        if not self.user_id:
            return {
                'topics': [],
                'navigation_history': [],
                'questions_asked': [],
                'preferred_models': {},
                'current_thread': None
            }

        db = get_db()

        # Get recent questions
        questions = db.execute('''
            SELECT content, created_at FROM discussion_messages
            WHERE sender = 'user' AND session_id IN (
                SELECT id FROM discussion_sessions WHERE user_id = ?
            )
            ORDER BY created_at DESC LIMIT 20
        ''', (self.user_id,)).fetchall()

        # Extract topics from questions
        topics = self._extract_topics([q['content'] for q in questions])

        db.close()

        return {
            'topics': topics,
            'navigation_history': [],
            'questions_asked': [q['content'] for q in questions],
            'preferred_models': {},
            'current_thread': None
        }

    def _extract_topics(self, texts: List[str]) -> List[str]:
        """Extract key topics from text list"""
        from collections import Counter
        import re

        # Simple keyword extraction
        all_words = []
        for text in texts:
            words = re.findall(r'\b[a-z]{4,}\b', text.lower())
            all_words.extend(words)

        # Filter stopwords
        stopwords = {'what', 'when', 'where', 'how', 'why', 'this', 'that', 'with', 'from', 'have', 'will', 'would', 'could', 'should'}
        filtered = [w for w in all_words if w not in stopwords]

        # Return top 20
        counter = Counter(filtered)
        return [word for word, count in counter.most_common(20)]

    def select_model(self, query: str) -> str:
        """
        Select best model for the query

        Args:
            query: User's question

        Returns:
            Model name (e.g., 'soulfra-model')
        """
        query_lower = query.lower()

        # Score each model based on keyword matches
        scores = {}
        for model_name, spec in self.MODEL_SPECIALIZATIONS.items():
            score = 0
            for keyword in spec['expertise']:
                if keyword in query_lower:
                    score += 1
            scores[model_name] = score

        # Get model with highest score
        best_model = max(scores, key=scores.get)

        # If no matches, use general purpose model
        if scores[best_model] == 0:
            return 'mistral:7b'

        return best_model

    def get_available_models(self) -> List[Dict]:
        """Get list of available Ollama models"""
        try:
            req = urllib.request.Request(
                f'{OLLAMA_HOST}/api/tags',
                headers={'Content-Type': 'application/json'}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                models = []
                for model in data.get('models', []):
                    model_name = model['name']
                    spec = self.MODEL_SPECIALIZATIONS.get(model_name, {
                        'expertise': ['general'],
                        'description': 'General purpose model',
                        'icon': '🤖'
                    })
                    models.append({
                        'name': model_name,
                        'size': model.get('size', 0),
                        'modified': model.get('modified_at', ''),
                        'description': spec['description'],
                        'icon': spec['icon'],
                        'expertise': spec['expertise']
                    })
                return models
        except Exception as e:
            print(f"Error fetching models: {e}")
            return []

    def build_enriched_prompt(self, query: str, model_name: str) -> str:
        """
        Build prompt with context

        Args:
            query: User's question
            model_name: Selected model

        Returns:
            Enriched prompt string
        """
        # Get model specialization
        spec = self.MODEL_SPECIALIZATIONS.get(model_name, {})

        # Build context from user profile
        context_parts = []

        if self.context_profile['topics']:
            context_parts.append(f"User is interested in: {', '.join(self.context_profile['topics'][:5])}")

        if self.context_profile['questions_asked']:
            recent_questions = self.context_profile['questions_asked'][:3]
            context_parts.append(f"Recent questions: {'; '.join(recent_questions)}")

        context_str = "\n".join(context_parts) if context_parts else "No prior context"

        # Build system prompt based on model
        system_prompt = f"""You are {model_name}, a specialist in {', '.join(spec.get('expertise', ['general topics']))}.

{spec.get('description', 'General assistant')}.

User Context:
{context_str}

Provide concise, technical answers. If the question is outside your expertise, acknowledge it and suggest which model would be better."""

        return system_prompt

    def query_ollama(self, model_name: str, prompt: str, system_prompt: str) -> str:
        """
        Query Ollama API

        Args:
            model_name: Model to use
            prompt: User's question
            system_prompt: System/context prompt

        Returns:
            Model's response
        """
        try:
            data = json.dumps({
                'model': model_name,
                'prompt': prompt,
                'system': system_prompt,
                'stream': False
            }).encode('utf-8')

            req = urllib.request.Request(
                f'{OLLAMA_HOST}/api/generate',
                data=data,
                headers={'Content-Type': 'application/json'}
            )

            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get('response', 'No response from model')

        except urllib.error.URLError as e:
            return f"Error connecting to Ollama: {e}"
        except Exception as e:
            return f"Error querying model: {e}"

    def process_query(self, query: str, model_name: Optional[str] = None) -> Dict:
        """
        Process user query through reasoning pipeline

        Args:
            query: User's question
            model_name: Optional specific model (otherwise auto-select)

        Returns:
            Dict with response, model used, reasoning steps
        """
        # Auto-select model if not specified
        if not model_name:
            model_name = self.select_model(query)

        # Build enriched prompt
        system_prompt = self.build_enriched_prompt(query, model_name)

        # Query Ollama
        response = self.query_ollama(model_name, query, system_prompt)

        # Save to conversation history
        self._save_message('user', query)
        self._save_message('assistant', response, metadata={
            'model': model_name,
            'system_prompt': system_prompt
        })

        # Update context profile
        self.context_profile['questions_asked'].insert(0, query)
        self.context_profile['questions_asked'] = self.context_profile['questions_asked'][:20]

        return {
            'response': response,
            'model_used': model_name,
            'model_description': self.MODEL_SPECIALIZATIONS.get(model_name, {}).get('description', 'Unknown'),
            'context_used': system_prompt,
            'session_id': self.session_id
        }

    def _save_message(self, sender: str, content: str, metadata: Optional[Dict] = None):
        """Save message to database"""
        if not self.user_id:
            return

        db = get_db()

        # Ensure session exists
        session = db.execute('''
            SELECT id FROM discussion_sessions WHERE id = ?
        ''', (self.session_id,)).fetchone()

        if not session:
            db.execute('''
                INSERT INTO discussion_sessions (id, user_id, persona_name, status)
                VALUES (?, ?, 'context_manager', 'active')
            ''', (self.session_id, self.user_id))
            db.commit()

        # Save message
        db.execute('''
            INSERT INTO discussion_messages (session_id, sender, content, message_type, metadata)
            VALUES (?, ?, ?, 'chat', ?)
        ''', (self.session_id, sender, content, json.dumps(metadata) if metadata else None))

        db.commit()
        db.close()


if __name__ == '__main__':
    # Test context manager
    cm = ContextManager(user_id=1)

    print("=" * 60)
    print("Context Manager Test")
    print("=" * 60)

    # Test model selection
    queries = [
        "How do I implement encryption in Python?",
        "What are the privacy concerns with cookies?",
        "How can I optimize this SQL query?",
        "Help me write a blog post about AI"
    ]

    for query in queries:
        selected = cm.select_model(query)
        spec = cm.MODEL_SPECIALIZATIONS.get(selected, {})
        print(f"\nQuery: {query}")
        print(f"Selected: {spec.get('icon', '?')} {selected} - {spec.get('description', 'Unknown')}")

    # Test available models
    print("\n" + "=" * 60)
    print("Available Models:")
    print("=" * 60)
    models = cm.get_available_models()
    for model in models[:5]:
        print(f"{model['icon']} {model['name']} - {model['description']}")
