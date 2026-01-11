#!/usr/bin/env python3
"""
Soulfra Games - Dynamic Question Generator for Cringeproof

Generate personalized cringeproof questions from user's blog posts instead of
hardcoded static questions.

OLD WAY (static):
    7 hardcoded questions for everyone
    "Do you rehearse conversations before having them?"

NEW WAY (dynamic):
    Questions generated from YOUR blog posts
    "You wrote 'worried about code review' - do you rehearse what to say?"

Usage:
    from soulfra_games import DynamicCringeproof

    game = DynamicCringeproof(db_manager)
    game.generate_questions_from_posts(user_id)
    questions = game.get_questions()
"""

import re
import random
import json
import urllib.request
import urllib.error
from typing import Dict, List, Tuple, Any, Optional
from collections import Counter

# Import knowledge graph and reasoning
from soulfra_graph import KeywordExtractor, GraphBuilder
from cringeproof_reasoning import ReasoningEngine
from lib.physics import PhysicsScoring


# ==============================================================================
# OLLAMA AI QUESTION GENERATOR
# ==============================================================================

def generate_questions_with_ollama(content: str, title: str = "", num_questions: int = 7,
                                   model: str = 'llama3.2:3b') -> List[Dict]:
    """
    Use Ollama AI to generate self-awareness questions from blog post content

    Args:
        content: Blog post content (markdown/text)
        title: Blog post title
        num_questions: Number of questions to generate
        model: Ollama model to use

    Returns:
        List of question dicts with 'question', 'category', 'context' fields
    """
    print(f"🔍 Generating {num_questions} questions from article using Ollama...")
    print(f"📝 Content length: {len(content)} characters")
    print(f"🤖 Using model: {model}")

    # Truncate content to avoid token limits (keep first 2000 chars)
    content_excerpt = content[:2000]

    # Build prompt for Ollama
    prompt = f"""You are generating self-awareness questions for a personality assessment game called "Cringeproof."

Read this blog post and generate {num_questions} self-awareness questions that test how the reader relates to the themes and ideas in the content.

Blog Post Title: {title}

Blog Post Content:
{content_excerpt}

Generate {num_questions} questions in this EXACT JSON format:
[
  {{"question": "I often think about how my work documents itself", "category": "reflection"}},
  {{"question": "I find manual documentation tedious and repetitive", "category": "automation"}},
  ...
]

Each question should:
- Be a first-person statement (starting with "I...")
- Relate to themes from the blog post
- Be answerable on a 1-5 scale (Never to Always)
- Test self-awareness about the topic

Return ONLY the JSON array, nothing else."""

    try:
        # Call Ollama API
        url = 'http://localhost:11434/api/generate'

        payload = {
            'model': model,
            'prompt': prompt,
            'stream': False,
            'options': {
                'num_predict': 500,
                'temperature': 0.7
            }
        }

        print(f"📡 Calling Ollama API...")
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            url,
            data=data,
            headers={'Content-Type': 'application/json'}
        )

        response = urllib.request.urlopen(req, timeout=30)
        result = json.loads(response.read().decode('utf-8'))

        response_text = result.get('response', '').strip()
        print(f"✅ Ollama responded ({len(response_text)} chars)")
        print(f"📄 Raw response: {response_text[:200]}...")

        # Parse JSON from response
        # Sometimes Ollama wraps in markdown code blocks
        if '```json' in response_text:
            # Extract JSON from markdown
            start = response_text.find('[')
            end = response_text.rfind(']') + 1
            json_text = response_text[start:end]
        elif response_text.startswith('['):
            json_text = response_text
        else:
            # Try to find JSON array
            start = response_text.find('[')
            end = response_text.rfind(']') + 1
            if start >= 0 and end > start:
                json_text = response_text[start:end]
            else:
                raise ValueError("No JSON array found in response")

        questions_data = json.loads(json_text)

        # Convert to our format
        questions = []
        for i, q in enumerate(questions_data[:num_questions]):
            questions.append({
                'id': i,
                'question': q.get('question', ''),
                'category': q.get('category', 'reflection'),
                'context': f'Generated from: {title[:50]}',
                'answers': [
                    ('Never', 1),
                    ('Rarely', 2),
                    ('Sometimes', 3),
                    ('Often', 4),
                    ('Always', 5)
                ],
                'generated_from': 'ollama_ai'
            })

        print(f"✅ Parsed {len(questions)} questions successfully!")
        for idx, q in enumerate(questions, 1):
            print(f"   {idx}. [{q['category']}] {q['question'][:60]}...")

        return questions

    except urllib.error.URLError as e:
        print(f"❌ Ollama connection error: {e}")
        print(f"   Is Ollama running? Check: http://localhost:11434/api/tags")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        print(f"   Response was: {response_text[:500]}")
        return []
    except Exception as e:
        print(f"❌ Unexpected error in Ollama generation: {e}")
        import traceback
        traceback.print_exc()
        return []


# ==============================================================================
# QUESTION TEMPLATES
# ==============================================================================

class QuestionTemplates:
    """
    Templates for generating questions from blog content

    Each template has:
    - Pattern: What to look for in blog posts
    - Question template: How to phrase the question
    - Category: Which anxiety category it measures
    """

    TEMPLATES = [
        # Communication Anxiety Templates
        {
            'category': 'communication_anxiety',
            'pattern': r'\b(text|message|email|dm|slack|wrote)\b',
            'keywords': ['worried', 'anxious', 'nervous', 'careful', 'draft', 'rewrite'],
            'question_template': "You mentioned {context}. Do you often reread messages multiple times before sending?",
            'answers': [
                ('Always - I check every word', 4),
                ('Often - just to make sure', 3),
                ('Sometimes', 2),
                ('Rarely', 1),
                ('Never - I just send it', 0)
            ]
        },
        {
            'category': 'communication_anxiety',
            'pattern': r'\b(chat|conversation|talking|speaking)\b',
            'keywords': ['difficult', 'hard', 'struggle', 'awkward'],
            'question_template': "In your post about {context}, you seem thoughtful about communication. Do you rehearse conversations?",
            'answers': [
                ('Yes, I script them out', 4),
                ('I plan key points', 3),
                ('Occasionally for important talks', 2),
                ('Rarely', 1),
                ('No, I\'m spontaneous', 0)
            ]
        },

        # Social Anxiety Templates
        {
            'category': 'social_anxiety',
            'pattern': r'\b(meeting|event|gathering|party|social)\b',
            'keywords': ['avoid', 'cancel', 'excuse', 'nervous', 'dread'],
            'question_template': "You wrote about {context}. How often do you find reasons to skip social events?",
            'answers': [
                ('Very often - I actively avoid them', 4),
                ('Often - when I can', 3),
                ('Sometimes', 2),
                ('Rarely', 1),
                ('Never - I enjoy them', 0)
            ]
        },
        {
            'category': 'social_anxiety',
            'pattern': r'\b(presentation|demo|show|public)\b',
            'keywords': ['scared', 'terrified', 'anxious', 'worried', 'fear'],
            'question_template': "Based on your writing about {context}, how anxious do you feel before public situations?",
            'answers': [
                ('Extremely anxious', 4),
                ('Very anxious', 3),
                ('Somewhat anxious', 2),
                ('Slightly anxious', 1),
                ('Not anxious', 0)
            ]
        },

        # Preparation Anxiety Templates
        {
            'category': 'preparation_anxiety',
            'pattern': r'\b(prepare|plan|ready|beforehand)\b',
            'keywords': ['overthink', 'stress', 'worry', 'perfect', 'practice'],
            'question_template': "You mentioned {context} in your posts. How much time do you spend preparing for interactions?",
            'answers': [
                ('Hours - I need everything perfect', 4),
                ('Significant time', 3),
                ('Some preparation', 2),
                ('Minimal', 1),
                ('None - I wing it', 0)
            ]
        },

        # Retrospective Anxiety Templates
        {
            'category': 'retrospective_anxiety',
            'pattern': r'\b(said|mistake|wrong|regret|embarrass)\b',
            'keywords': ['cringe', 'replay', 'think about', 'worry', 'dwell'],
            'question_template': "You wrote about {context}. How often do you replay past conversations?",
            'answers': [
                ('Constantly - for days/weeks', 4),
                ('Often - daily', 3),
                ('Sometimes', 2),
                ('Rarely', 1),
                ('Never - I move on quickly', 0)
            ]
        },
        {
            'category': 'retrospective_anxiety',
            'pattern': r'\b(awkward|uncomfortable|weird|strange)\b',
            'keywords': ['moment', 'interaction', 'conversation', 'situation'],
            'question_template': "Based on {context}, do you analyze what went wrong in conversations?",
            'answers': [
                ('Always - in great detail', 4),
                ('Often', 3),
                ('Sometimes', 2),
                ('Rarely', 1),
                ('Never', 0)
            ]
        },

        # Validation Seeking Templates
        {
            'category': 'validation_seeking',
            'pattern': r'\b(feedback|opinion|think|approval|validate)\b',
            'keywords': ['need', 'want', 'seek', 'look for', 'hoping'],
            'question_template': "You mentioned {context}. How important is others' approval to you?",
            'answers': [
                ('Extremely important', 4),
                ('Very important', 3),
                ('Somewhat important', 2),
                ('Not very important', 1),
                ('Not important at all', 0)
            ]
        },
        {
            'category': 'validation_seeking',
            'pattern': r'\b(like|upvote|reaction|response|reply)\b',
            'keywords': ['wait', 'check', 'hope', 'anxious', 'nervous'],
            'question_template': "In your post about {context}, do you check for reactions/responses frequently?",
            'answers': [
                ('Constantly refreshing', 4),
                ('Very frequently', 3),
                ('Occasionally', 2),
                ('Rarely', 1),
                ('Never', 0)
            ]
        },

        # Fallback generic templates (if no blog content matches)
        {
            'category': 'communication_anxiety',
            'pattern': None,
            'keywords': None,
            'question_template': "How often do you reread messages before sending?",
            'answers': [
                ('Always', 4),
                ('Often', 3),
                ('Sometimes', 2),
                ('Rarely', 1),
                ('Never', 0)
            ]
        }
    ]


# ==============================================================================
# DYNAMIC QUESTION GENERATOR
# ==============================================================================

class DynamicCringeproof:
    """
    Generate personalized cringeproof questions from blog posts

    Workflow:
    1. Extract keywords from user's blog posts
    2. Match keywords to question templates
    3. Generate personalized questions with context
    4. Score responses using physics-based analysis
    5. Run reasoning engine for insights
    """

    def __init__(self, db_manager=None):
        """
        Initialize dynamic question generator

        Args:
            db_manager: Optional database manager from soulfra_local
        """
        self.db = db_manager
        self.extractor = KeywordExtractor()
        self.physics = PhysicsScoring()
        self.reasoning = ReasoningEngine()
        self.templates = QuestionTemplates.TEMPLATES

        self.generated_questions = []
        self.user_posts = []

    def generate_questions_from_posts(self, user_id: Optional[int] = None,
                                     posts: Optional[List[Dict]] = None,
                                     num_questions: int = 7) -> List[Dict]:
        """
        Generate questions from user's blog posts

        Args:
            user_id: User ID to fetch posts for (if using database)
            posts: Direct list of posts (if not using database)
            num_questions: Number of questions to generate

        Returns:
            List of generated questions with context
        """
        # Get posts
        if posts:
            self.user_posts = posts
        elif self.db and user_id:
            self.user_posts = self._fetch_user_posts(user_id)
        else:
            # No posts - use fallback generic questions
            return self._generate_fallback_questions(num_questions)

        if not self.user_posts:
            return self._generate_fallback_questions(num_questions)

        # Extract content from all posts
        all_content = ' '.join(post.get('content', '') for post in self.user_posts)

        # Try Ollama AI generation FIRST
        print("\n" + "="*80)
        print("🤖 ATTEMPTING OLLAMA AI QUESTION GENERATION")
        print("="*80)
        title = self.user_posts[0].get('title', '') if self.user_posts else ''
        print(f"📚 Using {len(self.user_posts)} blog post(s)")
        print(f"📝 Title: {title}")
        print(f"📊 Content length: {len(all_content)} characters")

        ollama_questions = generate_questions_with_ollama(all_content, title, num_questions)

        if len(ollama_questions) >= num_questions:
            print(f"\n✅ SUCCESS! Ollama generated {len(ollama_questions)} questions")
            print(f"🎯 Using Ollama questions exclusively")
            print("="*80 + "\n")
            self.generated_questions = ollama_questions
            return ollama_questions
        elif ollama_questions:
            print(f"\n⚠️  Ollama generated {len(ollama_questions)}/{num_questions} questions")
            print(f"📝 Will supplement with pattern matching...")
            questions = ollama_questions
        else:
            print(f"\n❌ Ollama generation failed")
            print(f"📝 Falling back to pattern matching...")
            questions = []

        print("="*80 + "\n")

        # Tokenize and find keywords (for pattern matching fallback)
        words = self.extractor.tokenize(all_content)
        word_counts = Counter(words)

        # Generate questions from templates (FALLBACK)
        used_categories = set()

        for template in self.templates:
            if len(questions) >= num_questions:
                break

            # Skip if we already have a question from this category
            category = template['category']
            if category in used_categories and template['pattern']:  # Allow fallback templates
                continue

            # Try to match pattern and keywords
            matched_context = self._find_matching_context(
                all_content,
                template.get('pattern'),
                template.get('keywords', []),
                word_counts
            )

            if matched_context or not template['pattern']:  # Use fallback if no pattern
                # Generate question
                if matched_context:
                    question_text = template['question_template'].format(context=matched_context)
                else:
                    question_text = template['question_template']

                questions.append({
                    'id': len(questions),
                    'category': category,
                    'question': question_text,
                    'answers': template['answers'],
                    'context': matched_context,
                    'generated_from': 'blog_posts' if matched_context else 'fallback'
                })

                used_categories.add(category)

        # Fill remaining with fallback questions if needed
        if len(questions) < num_questions:
            fallback = self._generate_fallback_questions(num_questions - len(questions))
            questions.extend(fallback)

        self.generated_questions = questions
        return questions

    def _find_matching_context(self, content: str, pattern: Optional[str],
                               keywords: Optional[List[str]], word_counts: Counter) -> Optional[str]:
        """Find a relevant excerpt from blog content that matches pattern and keywords"""
        if not pattern:
            return None

        # Find sentences matching pattern
        pattern_matches = re.finditer(pattern, content, re.IGNORECASE)

        for match in pattern_matches:
            # Get sentence containing match
            start = max(0, match.start() - 50)
            end = min(len(content), match.end() + 50)
            excerpt = content[start:end]

            # Check if any keywords present
            if keywords:
                excerpt_lower = excerpt.lower()
                for keyword in keywords:
                    if keyword in excerpt_lower:
                        # Found a match! Clean up excerpt
                        clean_excerpt = self._clean_excerpt(excerpt)
                        return clean_excerpt

        return None

    def _clean_excerpt(self, excerpt: str) -> str:
        """Clean excerpt for question template"""
        # Remove HTML tags
        excerpt = re.sub(r'<[^>]+>', '', excerpt)

        # Truncate to ~50 chars
        if len(excerpt) > 50:
            excerpt = excerpt[:47] + '...'

        # Remove extra whitespace
        excerpt = ' '.join(excerpt.split())

        return f'"{excerpt}"'

    def _fetch_user_posts(self, user_id: int) -> List[Dict]:
        """Fetch user posts from database"""
        if not self.db:
            return []

        try:
            posts = self.db.get_posts_by_user(user_id)
            return posts
        except:
            return []

    def _generate_fallback_questions(self, num_questions: int) -> List[Dict]:
        """Generate generic fallback questions (original cringeproof style)"""
        fallback_templates = [t for t in self.templates if t['pattern'] is None]

        questions = []
        for i, template in enumerate(fallback_templates[:num_questions]):
            questions.append({
                'id': i,
                'category': template['category'],
                'question': template['question_template'],
                'answers': template['answers'],
                'context': None,
                'generated_from': 'fallback'
            })

        return questions

    def get_questions(self) -> List[Dict]:
        """Get currently generated questions"""
        return self.generated_questions

    def calculate_score(self, responses: List[int],
                       score_history: Optional[List[float]] = None) -> Dict[str, Any]:
        """
        Calculate score with physics-based analysis

        Args:
            responses: List of answer indices (0-4)
            score_history: Optional history of past scores for momentum analysis

        Returns:
            Complete analysis with physics + reasoning
        """
        # Calculate category scores
        category_totals = {}
        category_counts = {}

        for question, response_idx in zip(self.generated_questions, responses):
            category = question['category']
            score = question['answers'][response_idx][1]  # Get point value

            if category not in category_totals:
                category_totals[category] = 0
                category_counts[category] = 0

            category_totals[category] += score
            category_counts[category] += 1

        # Calculate percentages for each category
        category_scores = {
            cat: (total / (category_counts[cat] * 4)) * 100  # Normalize to 0-100
            for cat, total in category_totals.items()
        }

        # Overall score
        total_score = sum(category_totals.values())
        max_possible = len(responses) * 4
        overall_percentage = (total_score / max_possible) * 100

        # If we have score history, use physics analysis
        result = {
            'overall_score': overall_percentage,
            'category_scores': category_scores,
            'responses': responses
        }

        if score_history:
            # Add current score to history
            full_history = score_history + [overall_percentage]

            # Run deep analysis with reasoning engine
            analysis = self.reasoning.deep_analyze(
                full_history,
                category_scores
            )

            result['physics_analysis'] = analysis['physics']
            result['root_cause'] = analysis['root_cause']
            result['archetype'] = analysis['archetype']
            result['insights'] = analysis['personalized_insights']
            result['summary'] = analysis['summary']
        else:
            # First time - just category breakdown
            result['message'] = 'Complete more sessions to unlock trend analysis!'

        return result


# ==============================================================================
# GAME EXPORT (for server/desktop sync)
# ==============================================================================

def export_game_json(game: DynamicCringeproof) -> Dict[str, Any]:
    """
    Export game as JSON for server sync or storage

    Returns:
        JSON-serializable game data
    """
    return {
        'game_type': 'dynamic_cringeproof',
        'version': '1.0',
        'questions': game.get_questions(),
        'generated_from_posts': len(game.user_posts),
        'total_questions': len(game.generated_questions)
    }


def import_game_json(game_data: Dict[str, Any]) -> DynamicCringeproof:
    """
    Import game from JSON

    Args:
        game_data: JSON game data from export_game_json

    Returns:
        DynamicCringeproof instance with loaded questions
    """
    game = DynamicCringeproof()
    game.generated_questions = game_data['questions']
    return game


# ==============================================================================
# CLI INTERFACE
# ==============================================================================

def play_interactive(game: DynamicCringeproof):
    """Interactive CLI game"""
    print("\n🎮 Dynamic Cringeproof - Personalized Version")
    print("=" * 70)

    questions = game.get_questions()

    if not questions:
        print("❌ No questions generated. Try adding blog posts first!")
        return

    # Show generation stats
    from_posts = sum(1 for q in questions if q['generated_from'] == 'blog_posts')
    print(f"\n📊 Questions generated:")
    print(f"   From your blog posts: {from_posts}")
    print(f"   Fallback questions: {len(questions) - from_posts}")
    print()

    responses = []

    for i, question in enumerate(questions, 1):
        print(f"\n{'='*70}")
        print(f"Question {i}/{len(questions)}")
        print(f"{'='*70}\n")

        # Show context if available
        if question['context']:
            print(f"💭 Context from your writing: {question['context']}\n")

        print(f"❓ {question['question']}\n")

        # Show answers
        for idx, (answer_text, points) in enumerate(question['answers']):
            print(f"   {idx + 1}. {answer_text}")

        # Get response
        while True:
            try:
                choice = input("\nYour answer (1-5): ").strip()
                choice_idx = int(choice) - 1

                if 0 <= choice_idx < len(question['answers']):
                    responses.append(choice_idx)
                    break
                else:
                    print("❌ Invalid choice. Try again.")
            except (ValueError, KeyboardInterrupt):
                print("\n❌ Exiting game.")
                return

    # Calculate score
    print("\n\n" + "🎯" * 35)
    print("  RESULTS")
    print("🎯" * 35 + "\n")

    result = game.calculate_score(responses)

    print(f"Overall Anxiety Score: {result['overall_score']:.1f}%")
    print("\nCategory Breakdown:")

    for category, score in result['category_scores'].items():
        print(f"   {category.replace('_', ' ').title()}: {score:.1f}%")

    print("\n" + result.get('message', ''))

    if 'insights' in result:
        print("\n💡 Personalized Insights:")
        for insight in result['insights']:
            print(f"   {insight}")


if __name__ == '__main__':
    import sys

    print("🎮 Soulfra Games - Dynamic Cringeproof Generator")
    print("=" * 70)

    print("\n⚠️  This module requires blog posts to generate personalized questions.")
    print("    For demonstration, we'll use sample blog content.\n")

    # Demo: Create sample blog posts
    sample_posts = [
        {
            'title': 'My Code Review Anxiety',
            'content': '''
            I get really nervous when submitting code for review. I spend hours
            preparing the perfect pull request, worrying about every comment.
            After submitting, I constantly check for feedback and dwell on any
            criticism for days. I know I need to be less anxious about this.
            '''
        },
        {
            'title': 'Struggling with Team Meetings',
            'content': '''
            Team meetings make me anxious. I rehearse what I'll say beforehand,
            but then feel awkward during the actual conversation. I often
            find excuses to skip optional social events. After meetings, I
            replay everything I said and cringe at awkward moments.
            '''
        }
    ]

    # Generate game
    game = DynamicCringeproof()
    questions = game.generate_questions_from_posts(posts=sample_posts, num_questions=5)

    print(f"✅ Generated {len(questions)} personalized questions!\n")

    # Show sample questions
    print("📋 Sample Questions Generated:\n")
    for i, q in enumerate(questions[:3], 1):
        print(f"{i}. {q['question']}")
        if q['context']:
            print(f"   Context: {q['context']}")
        print(f"   Category: {q['category']}")
        print()

    # Ask if user wants to play
    if '--play' in sys.argv or '-p' in sys.argv:
        play_interactive(game)
    else:
        print("💡 Use --play flag to play interactively")
        print("   Example: python3 soulfra_games.py --play")
