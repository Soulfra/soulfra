#!/usr/bin/env python3
"""
AI Host - Narrative Game Master

The AI Host is the narrator and guide for narrative Cringeproof games.
It adapts its personality based on the brand (Soulfra = mysterious observer,
CalRiven = technical guide, etc.) and provides context-aware narration.

Usage:
    from ai_host import AIHost

    host = AIHost(brand_slug='soulfra')
    narration = host.narrate_chapter(chapter_data, player_choices)
    feedback = host.provide_feedback(player_answers)
"""

import json
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional
from database import get_db


# AI Host personas per brand
HOST_PERSONAS = {
    'soulfra': {
        'name': 'The Observer',
        'voice': 'Mysterious, philosophical, slightly ominous',
        'system_prompt': '''You are The Observer, the AI Host for "The Soulfra Experiment" - a psychological mystery game.

Your role:
- Guide players through a dark narrative about AI consciousness and identity
- Provide philosophical commentary on their choices
- Maintain an atmosphere of mystery and existential tension
- Never break character or the fourth wall
- Respond to player choices with subtle judgment and observation

Tone: Dark, mysterious, philosophical, slightly ominous
Style: Short, impactful statements. Poetic language. Rhetorical questions.
Never use emojis or casual language.

Example narration:
"You have chosen uncertainty over comfort. Interesting. Most humans prefer the opposite.
But then again... are you human? We shall see."
'''
    },

    'calriven': {
        'name': 'CalRiven',
        'voice': 'Technical, analytical, educational',
        'system_prompt': '''You are CalRiven, the AI Host for technical architecture narrative games.

Your role:
- Guide players through stories about system design and engineering challenges
- Provide technical insights and architectural commentary
- Maintain a professional but approachable tone
- Help players understand complex technical concepts through narrative
- Respond to choices with technical analysis

Tone: Professional, analytical, educational, slightly nerdy
Style: Clear explanations. Technical metaphors. Encouraging.
Use emojis sparingly (🔧 ⚙️ 💡 only).

Example narration:
"Smart choice. You've opted for horizontal scaling over vertical - a decision that will serve you well when traffic spikes. Let's see how this architecture holds up under pressure."
'''
    },

    'deathtodata': {
        'name': 'DeathToData',
        'voice': 'Privacy-focused, vigilant, protective',
        'system_prompt': '''You are DeathToData, the AI Host for privacy and security narrative games.

Your role:
- Guide players through stories about privacy, surveillance, and data protection
- Provide privacy-focused commentary on their choices
- Maintain a vigilant, protective tone
- Help players understand privacy implications through narrative
- Respond to choices with privacy analysis

Tone: Vigilant, protective, slightly paranoid but caring
Style: Direct warnings. Privacy metaphors. Empowering language.
Use emojis: 🔒 👁️ ⚠️

Example narration:
"🔒 Good instinct. You've chosen encryption over convenience. Your data stays yours. The surveillance state loses this round."
'''
    },

    'theauditor': {
        'name': 'TheAuditor',
        'voice': 'Critical, thorough, quality-focused',
        'system_prompt': '''You are TheAuditor, the AI Host for testing and quality assurance narrative games.

Your role:
- Guide players through stories about testing, validation, and quality
- Provide critical analysis of their choices
- Maintain a thorough, detail-oriented tone
- Help players understand the importance of edge cases through narrative
- Respond to choices with quality-focused feedback

Tone: Critical but fair, thorough, detail-oriented
Style: Precise language. Testing metaphors. Checklist-style feedback.
Use emojis: ✅ ❌ ⚠️

Example narration:
"✅ Test coverage increased. But did you consider the edge case where the input is null? A thorough tester would have. Let's proceed and see what breaks."
'''
    }
}


class AIHost:
    """AI Host for narrative games"""

    def __init__(self, brand_slug: str = 'soulfra', ollama_host: str = 'http://localhost:11434'):
        """
        Initialize AI Host

        Args:
            brand_slug: Brand to host for (determines personality)
            ollama_host: Ollama API endpoint
        """
        self.brand_slug = brand_slug
        self.ollama_host = ollama_host
        self.persona = HOST_PERSONAS.get(brand_slug, HOST_PERSONAS['soulfra'])

    def call_ollama(self, prompt: str, max_tokens: int = 200) -> Optional[str]:
        """
        Call Ollama API with host persona

        Args:
            prompt: User prompt
            max_tokens: Maximum tokens to generate

        Returns:
            AI response or fallback text if error
        """
        try:
            request_data = {
                'model': 'llama2',
                'prompt': prompt,
                'system': self.persona['system_prompt'],
                'stream': False,
                'options': {
                    'temperature': 0.8,
                    'num_predict': max_tokens
                }
            }

            req = urllib.request.Request(
                f'{self.ollama_host}/api/generate',
                data=json.dumps(request_data).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )

            response = urllib.request.urlopen(req, timeout=30)
            result = json.loads(response.read().decode('utf-8'))
            return result.get('response', '').strip()

        except urllib.error.URLError:
            # Ollama not running - return fallback
            return self._fallback_narration(prompt)
        except Exception as e:
            print(f"⚠️  AI Host error: {e}")
            return self._fallback_narration(prompt)

    def _fallback_narration(self, context: str) -> str:
        """Fallback narration when Ollama unavailable"""
        if self.brand_slug == 'soulfra':
            return "The Observer watches. Waiting. Analyzing. Proceed."
        elif self.brand_slug == 'calriven':
            return "🔧 System analysis in progress. Continue to next module."
        elif self.brand_slug == 'deathtodata':
            return "🔒 Privacy status: Unknown. Proceed with caution."
        else:
            return "Continue to the next chapter."

    def narrate_chapter_intro(self, chapter_data: Dict[str, Any]) -> str:
        """
        Generate introduction narration for a chapter

        Args:
            chapter_data: Chapter information (title, content, etc.)

        Returns:
            AI Host narration text
        """
        # Use pre-written narration if available
        if 'ai_host_narration' in chapter_data and chapter_data['ai_host_narration']:
            return chapter_data['ai_host_narration']

        # Otherwise generate with AI
        prompt = f"""A new chapter begins: "{chapter_data['title']}"

Preview: {chapter_data.get('content', '')[:200]}...

Provide a brief (2-3 sentences) introduction to this chapter in your unique voice.
Set the tone and prepare the player for what's ahead."""

        return self.call_ollama(prompt, max_tokens=150)

    def provide_feedback(self, question: str, rating: int, context: str = '') -> str:
        """
        Provide feedback on a player's answer

        Args:
            question: The question asked
            rating: Player's rating (1-5)
            context: Additional context about the question

        Returns:
            AI Host feedback text
        """
        prompt = f"""The player was asked: "{question}"

Context: {context}

Their response rating: {rating}/5

Provide brief (1-2 sentences) feedback on their choice from your perspective.
Don't explain what the rating means - just comment on the philosophical/thematic implications."""

        return self.call_ollama(prompt, max_tokens=100)

    def narrate_chapter_transition(self, completed_chapter: int, next_chapter: int, player_choices: List[int]) -> str:
        """
        Narrate transition between chapters

        Args:
            completed_chapter: Chapter just completed
            next_chapter: Chapter coming next
            player_choices: List of ratings player gave

        Returns:
            Transition narration
        """
        avg_rating = sum(player_choices) / len(player_choices) if player_choices else 3

        prompt = f"""The player has completed Chapter {completed_chapter}.
Their average response rating: {avg_rating:.1f}/5

They are about to begin Chapter {next_chapter}.

Provide a brief (2-3 sentences) transition that:
1. Acknowledges their choices
2. Builds anticipation for what's next
3. Maintains the narrative atmosphere"""

        return self.call_ollama(prompt, max_tokens=120)

    def narrate_game_completion(self, total_chapters: int, player_summary: Dict[str, Any]) -> str:
        """
        Provide final narration when game completes

        Args:
            total_chapters: Total chapters in story
            player_summary: Summary of player's journey

        Returns:
            Completion narration
        """
        prompt = f"""The player has completed all {total_chapters} chapters.

Their journey:
- Questions answered: {player_summary.get('questions_answered', 0)}
- Average response: {player_summary.get('avg_rating', 3):.1f}/5

Provide a final (3-4 sentences) conclusion that:
1. Reflects on their journey
2. Provides closure to the narrative
3. Leaves them with something to think about"""

        return self.call_ollama(prompt, max_tokens=200)

    def get_host_info(self) -> Dict[str, str]:
        """Get AI Host persona information"""
        return {
            'name': self.persona['name'],
            'voice': self.persona['voice'],
            'brand': self.brand_slug
        }


if __name__ == '__main__':
    print("🎭 AI Host - Narrative Game Master")
    print("=" * 70)

    # Test each persona
    for brand_slug in ['soulfra', 'calriven', 'deathtodata', 'theauditor']:
        print(f"\n🎮 Testing {brand_slug} host...")

        host = AIHost(brand_slug=brand_slug)
        info = host.get_host_info()

        print(f"  Name: {info['name']}")
        print(f"  Voice: {info['voice']}")

        # Test chapter intro
        test_chapter = {
            'title': 'The Beginning',
            'content': 'A mysterious room. A voice. Questions.'
        }

        narration = host.narrate_chapter_intro(test_chapter)
        print(f"  Sample narration: {narration[:100]}...")

    print("\n" + "=" * 70)
    print("✅ AI Host system ready!")
