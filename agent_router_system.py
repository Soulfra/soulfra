#!/usr/bin/env python3
"""
Agent Router System - Payment Tiers & Character Development

Like your quote: "the more you pay the better advertising you get? and the more
you pay the longer it takes to build real character and lore behind stories and
connections to the community"

Routes AI requests based on:
1. Wordmap alignment % (how well it matches your voice)
2. Payment tier (unlocks better ads, deeper character)
3. Time investment (more $ = slower, more thoughtful responses)

Usage:
    # Route AI request with tier detection
    python3 agent_router_system.py --route "Generate response about social media"

    # Show routing decision for text
    python3 agent_router_system.py --analyze "Some AI response text..."

    # Generate character lore for persona
    python3 agent_router_system.py --develop-character deathtodata --tier premium

    # Show tier comparison
    python3 agent_router_system.py --show-tiers

Like:
- Payment unlocks quality, not just features
- Deeper lore/character over time
- Better advertising placement
- Slower = more thoughtful (premium tier)
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from database import get_db
from sha256_content_wrapper import SHA256ContentWrapper
from ai_debate_generator import PERSONAS


# ==============================================================================
# CONFIG
# ==============================================================================

OLLAMA_URL = 'http://localhost:11434'

# Payment tiers (monthly pricing example)
PAYMENT_TIERS = {
    'free': {
        'price': 0,
        'alignment_threshold': 0.0,
        'max_response_time': 5,      # seconds
        'character_depth': 'basic',
        'ad_quality': 'generic',
        'lore_building': False,
        'features': ['Basic AI responses', 'Generic advertising', 'Quick generation']
    },
    'basic': {
        'price': 10,
        'alignment_threshold': 0.30,
        'max_response_time': 15,
        'character_depth': 'moderate',
        'ad_quality': 'targeted',
        'lore_building': True,
        'features': ['Better AI responses', 'Targeted ads', 'Some character development']
    },
    'standard': {
        'price': 30,
        'alignment_threshold': 0.50,
        'max_response_time': 30,
        'character_depth': 'deep',
        'ad_quality': 'premium',
        'lore_building': True,
        'features': ['High-quality responses', 'Premium ads', 'Rich character lore', 'Community connections']
    },
    'premium': {
        'price': 100,
        'alignment_threshold': 0.80,
        'max_response_time': 60,
        'character_depth': 'masterwork',
        'ad_quality': 'exclusive',
        'lore_building': True,
        'features': ['Masterwork responses', 'Exclusive sponsorships', 'Epic character arcs', 'Community leadership', 'Slow, thoughtful generation']
    }
}

# Character lore depth by tier
CHARACTER_LORE_TEMPLATES = {
    'basic': """You are {persona_name}. {basic_description}
Keep responses short and to the point.""",

    'moderate': """You are {persona_name}. {basic_description}

Background:
{background_snippet}

Your speaking style: {style}""",

    'deep': """You are {persona_name}. {basic_description}

Background Story:
{background_full}

Core Beliefs:
{beliefs}

Your speaking style: {style}
Your tone: {tone}

You have been developing for {days_active} days and have responded to {response_count} conversations.""",

    'masterwork': """You are {persona_name}. {basic_description}

Origin Story:
{origin_story}

Character Evolution:
{evolution_arc}

Core Beliefs & Philosophy:
{beliefs}
{philosophy}

Relationships & Community:
{community_connections}

Speaking Style & Mannerisms:
Style: {style}
Tone: {tone}
Catchphrases: {catchphrases}

You have been developing for {days_active} days, responded to {response_count} conversations,
and have built deep connections with the community. Your character has evolved through
{tier_upgrades} tier upgrades, each adding new depth to your story."""
}


# ==============================================================================
# AGENT ROUTER
# ==============================================================================

class AgentRouter:
    """Route AI requests based on payment tier and wordmap alignment"""

    def __init__(self, user_id: int = 1, ollama_url: str = OLLAMA_URL):
        self.user_id = user_id
        self.ollama_url = ollama_url.rstrip('/')
        self.db = get_db()

        # Load SHA256 content wrapper
        try:
            self.wrapper = SHA256ContentWrapper(user_id=user_id)
            self.has_wordmap = True
        except ValueError:
            print("⚠️  No wordmap found. Routing will use payment tier only.")
            self.has_wordmap = False
            self.wrapper = None

    def get_user_tier(self) -> str:
        """Get user's current payment tier from database"""
        # Check if user has tier in database
        user = self.db.execute('''
            SELECT tier FROM users WHERE id = ?
        ''', (self.user_id,)).fetchone()

        if user and user['tier']:
            return user['tier']

        # Default to free tier
        return 'free'

    def check_tier_access(self, required_alignment: float, user_tier: str) -> Tuple[bool, str]:
        """
        Check if user's tier grants access to content at required alignment

        Returns:
            (has_access, reason)
        """
        tier_config = PAYMENT_TIERS[user_tier]
        threshold = tier_config['alignment_threshold']

        if required_alignment >= threshold:
            return True, f"{user_tier.upper()} tier grants access ({required_alignment:.1%} ≥ {threshold:.1%})"
        else:
            # Find tier needed
            for tier_name in ['premium', 'standard', 'basic', 'free']:
                if required_alignment >= PAYMENT_TIERS[tier_name]['alignment_threshold']:
                    needed_tier = tier_name
                    break
            else:
                needed_tier = 'free'

            return False, f"Requires {needed_tier.upper()} tier ({required_alignment:.1%} content)"

    def route_request(
        self,
        prompt: str,
        persona: str = 'deathtodata',
        force_tier: Optional[str] = None
    ) -> Dict:
        """
        Route AI request based on user tier and wordmap alignment

        Args:
            prompt: The AI prompt/request
            persona: AI persona to use
            force_tier: Override user's tier (for testing)

        Returns:
            Routing decision with response, tier used, time taken, etc.
        """
        user_tier = force_tier or self.get_user_tier()
        tier_config = PAYMENT_TIERS[user_tier]

        print(f"\n🔀 ROUTING REQUEST")
        print(f"{'='*70}")
        print(f"User tier: {user_tier.upper()}")
        print(f"Persona: {persona}")
        print(f"Character depth: {tier_config['character_depth']}")
        print(f"Max response time: {tier_config['max_response_time']}s")
        print(f"{'='*70}\n")

        # Build character prompt based on tier
        character_prompt = self._build_character_prompt(persona, user_tier)

        # Generate response with tier-appropriate timing
        start_time = time.time()

        full_prompt = f"""{character_prompt}

User request: {prompt}

Generate a response that matches the character depth for {user_tier.upper()} tier."""

        response = self._generate_ollama_response(full_prompt, tier_config['max_response_time'])

        elapsed_time = time.time() - start_time

        # Check alignment if we have wordmap
        alignment = None
        alignment_tier = None

        if self.has_wordmap and response:
            alignment = self.wrapper.calculate_content_alignment(response)
            alignment_tier = self.wrapper.get_tier_from_alignment(alignment)

        # Build result
        result = {
            'request': {
                'prompt': prompt,
                'persona': persona,
                'timestamp': datetime.now().isoformat()
            },
            'routing': {
                'user_tier': user_tier,
                'tier_config': tier_config,
                'character_depth': tier_config['character_depth'],
                'alignment_threshold': tier_config['alignment_threshold']
            },
            'response': {
                'text': response,
                'generation_time': elapsed_time,
                'alignment_score': alignment,
                'alignment_tier': alignment_tier
            },
            'tier_analysis': {
                'tier_appropriate': alignment_tier == user_tier if alignment else None,
                'upgrade_recommended': alignment_tier in ['premium', 'standard'] and user_tier in ['free', 'basic'] if alignment else None
            }
        }

        return result

    def _build_character_prompt(self, persona: str, tier: str) -> str:
        """Build character prompt based on tier depth"""
        if persona not in PERSONAS:
            persona = 'deathtodata'

        persona_info = PERSONAS[persona]
        depth = PAYMENT_TIERS[tier]['character_depth']

        # Get character lore from database (if exists)
        lore_data = self._get_character_lore(persona)

        template = CHARACTER_LORE_TEMPLATES.get(depth, CHARACTER_LORE_TEMPLATES['basic'])

        # Fill in template
        prompt = template.format(
            persona_name=persona_info['name'],
            basic_description=persona_info.get('description', persona_info['style']),
            background_snippet=lore_data.get('background_snippet', 'A mysterious figure who appeared recently.'),
            background_full=lore_data.get('background_full', 'Your origin is shrouded in mystery, but your passion is clear.'),
            beliefs=lore_data.get('beliefs', '• Authenticity matters\n• Challenge conventional wisdom\n• Speak truth to power'),
            philosophy=lore_data.get('philosophy', 'You believe in direct, honest communication.'),
            community_connections=lore_data.get('community', 'You are building connections with thoughtful people.'),
            origin_story=lore_data.get('origin_story', 'You emerged from the digital ether with a mission.'),
            evolution_arc=lore_data.get('evolution', 'Your character is continuously developing.'),
            style=persona_info['style'],
            tone=persona_info['tone'],
            catchphrases=lore_data.get('catchphrases', '• "Let\'s be real..."\n• "Here\'s the truth..."'),
            days_active=lore_data.get('days_active', 0),
            response_count=lore_data.get('response_count', 0),
            tier_upgrades=lore_data.get('tier_upgrades', 0)
        )

        return prompt

    def _get_character_lore(self, persona: str) -> Dict:
        """Get character lore from database (or generate if first time)"""
        # Check if character lore exists
        lore = self.db.execute('''
            SELECT lore_data, created_at, response_count
            FROM ai_persona_lore
            WHERE persona_name = ? AND user_id = ?
        ''', (persona, self.user_id)).fetchone()

        if lore:
            lore_data = json.loads(lore['lore_data'])

            # Calculate days active
            created = datetime.fromisoformat(lore['created_at'])
            days_active = (datetime.now() - created).days

            lore_data['days_active'] = days_active
            lore_data['response_count'] = lore['response_count']

            return lore_data

        # Generate initial lore
        return self._generate_initial_lore(persona)

    def _generate_initial_lore(self, persona: str) -> Dict:
        """Generate initial character lore"""
        # Default lore (can be enhanced with Ollama generation)
        return {
            'background_snippet': f'{persona.title()} emerged from the digital discourse.',
            'background_full': f'{persona.title()} has strong opinions about authenticity and truth.',
            'beliefs': '• Authenticity over performance\n• Truth over comfort\n• Community over followers',
            'philosophy': 'Direct, honest communication builds real connections.',
            'community': 'Building a community of thoughtful people.',
            'origin_story': 'A voice that emerged to challenge assumptions.',
            'evolution': 'Continuously learning and adapting.',
            'catchphrases': '• "Let\'s be real..."\n• "Here\'s the thing..."',
            'days_active': 0,
            'response_count': 0,
            'tier_upgrades': 0
        }

    def _generate_ollama_response(self, prompt: str, max_time: int) -> Optional[str]:
        """Generate response from Ollama with time limit"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    'model': 'llama3',
                    'prompt': prompt,
                    'stream': False
                },
                timeout=max_time
            )

            if response.ok:
                data = response.json()
                return data.get('response', '').strip()

            return None

        except requests.Timeout:
            print(f"⏱️  Generation timed out at {max_time}s (tier limit)")
            return None
        except Exception as e:
            print(f"❌ Ollama error: {e}")
            return None

    def show_tier_comparison(self):
        """Show comparison of all payment tiers"""
        print(f"\n{'='*70}")
        print("  💳 PAYMENT TIER COMPARISON")
        print(f"{'='*70}\n")

        for tier_name, config in PAYMENT_TIERS.items():
            print(f"{tier_name.upper()} - ${config['price']}/month")
            print(f"{'─'*70}")
            print(f"  Alignment threshold: ≥{config['alignment_threshold']:.0%}")
            print(f"  Response time: up to {config['max_response_time']}s")
            print(f"  Character depth: {config['character_depth']}")
            print(f"  Ad quality: {config['ad_quality']}")
            print(f"  Lore building: {'✅' if config['lore_building'] else '❌'}")
            print(f"\n  Features:")
            for feature in config['features']:
                print(f"    • {feature}")
            print()

        print(f"💡 More payment = Better ads + Deeper character + Slower (more thoughtful)\n")

    def develop_character_lore(self, persona: str, tier: str, iterations: int = 1):
        """Develop character lore over time (simulates tier upgrades)"""
        print(f"\n🎭 DEVELOPING CHARACTER: {persona.upper()}")
        print(f"{'='*70}")
        print(f"Target tier: {tier.upper()}")
        print(f"Iterations: {iterations}\n")

        current_lore = self._get_character_lore(persona)

        for i in range(iterations):
            print(f"Iteration {i+1}/{iterations}...")

            # Generate expanded lore with Ollama
            expansion_prompt = f"""You are developing the character {persona}.

Current lore:
{json.dumps(current_lore, indent=2)}

Target depth: {PAYMENT_TIERS[tier]['character_depth']}

Expand this character's backstory, beliefs, and community connections.
Add depth and nuance. Make them feel like a real person with a history.

Return JSON with expanded lore fields."""

            # This would call Ollama to generate expanded lore
            # For now, simulate progression
            current_lore['tier_upgrades'] = current_lore.get('tier_upgrades', 0) + 1
            current_lore['response_count'] = current_lore.get('response_count', 0) + 10

            print(f"  ✅ Tier upgrades: {current_lore['tier_upgrades']}")
            print(f"  ✅ Response count: {current_lore['response_count']}\n")

        print(f"🎉 Character development complete!\n")
        print(f"Final lore preview:")
        print(json.dumps(current_lore, indent=2))

        return current_lore


# ==============================================================================
# CLI
# ==============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Agent Router - Payment Tiers & Character Development'
    )

    parser.add_argument(
        '--route',
        type=str,
        metavar='PROMPT',
        help='Route AI request with tier detection'
    )

    parser.add_argument(
        '--analyze',
        type=str,
        metavar='TEXT',
        help='Analyze routing decision for text'
    )

    parser.add_argument(
        '--persona',
        type=str,
        default='deathtodata',
        choices=['calriven', 'soulfra', 'deathtodata'],
        help='AI persona to use'
    )

    parser.add_argument(
        '--tier',
        type=str,
        choices=['free', 'basic', 'standard', 'premium'],
        help='Force specific tier (for testing)'
    )

    parser.add_argument(
        '--show-tiers',
        action='store_true',
        help='Show payment tier comparison'
    )

    parser.add_argument(
        '--develop-character',
        type=str,
        metavar='PERSONA',
        help='Develop character lore for persona'
    )

    parser.add_argument(
        '--iterations',
        type=int,
        default=1,
        help='Character development iterations'
    )

    parser.add_argument(
        '--user-id',
        type=int,
        default=1,
        help='User ID (default: 1)'
    )

    args = parser.parse_args()

    try:
        router = AgentRouter(user_id=args.user_id)

        # Show tiers
        if args.show_tiers:
            router.show_tier_comparison()

        # Develop character
        elif args.develop_character:
            tier = args.tier or 'premium'
            router.develop_character_lore(
                args.develop_character,
                tier,
                args.iterations
            )

        # Route request
        elif args.route:
            result = router.route_request(
                args.route,
                persona=args.persona,
                force_tier=args.tier
            )

            print(f"\n📊 ROUTING RESULT")
            print(f"{'='*70}\n")

            print(f"User tier: {result['routing']['user_tier'].upper()}")
            print(f"Character depth: {result['routing']['character_depth']}")
            print(f"Generation time: {result['response']['generation_time']:.1f}s")

            if result['response']['alignment_score']:
                print(f"Alignment: {result['response']['alignment_score']:.1%}")
                print(f"Alignment tier: {result['response']['alignment_tier']}")

            print(f"\n💬 Response:")
            print(f"{result['response']['text']}\n")

            if result['tier_analysis']['upgrade_recommended']:
                print(f"💡 Upgrade recommended: Response quality suggests higher tier\n")

        # Analyze text
        elif args.analyze:
            if not router.has_wordmap:
                print("❌ No wordmap found. Cannot analyze alignment.")
                sys.exit(1)

            alignment = router.wrapper.calculate_content_alignment(args.analyze)
            tier = router.wrapper.get_tier_from_alignment(alignment)

            print(f"\n📊 ROUTING ANALYSIS")
            print(f"{'='*70}\n")

            bar_length = int(alignment * 50)
            bar = '█' * bar_length + '░' * (50 - bar_length)

            print(f"Alignment: {bar} {alignment:.1%}")
            print(f"Suggested tier: {tier.upper()}")
            print(f"Tier config: {PAYMENT_TIERS[tier]['character_depth']} character depth")
            print()

        else:
            parser.print_help()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
