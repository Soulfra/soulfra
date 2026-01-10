#!/usr/bin/env python3
"""
Game Template Registry - "Steam for Soul-Powered Games"

A registry system for game templates that work with Soul identity data.
Think: Steam workshop meets Unity Asset Store, but for Soul-compatible games.

Each template defines:
- What Soul fields it uses (interests, expertise, values)
- Which platforms it supports (Roblox, Minecraft, Unity)
- How to install/import
- Compatibility requirements

This is the foundation for a "marketplace" of Soul-powered games and apps.
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from database import get_db


class GameTemplate:
    """
    Represents a game template that can use Soul data

    Think of this like a Steam game that has "Cloud Save" support,
    but instead of just saves, it imports your entire Soul identity.
    """

    def __init__(self, template_id: str, name: str, description: str,
                 platform: str, soul_requirements: Dict[str, Any]):
        self.template_id = template_id
        self.name = name
        self.description = description
        self.platform = platform  # roblox, minecraft, unity, web
        self.soul_requirements = soul_requirements

        # Installation instructions
        self.install_instructions = []

        # Compatibility rules
        self.min_activity_level = soul_requirements.get('min_activity', 0)
        self.required_fields = soul_requirements.get('required_fields', [])
        self.recommended_interests = soul_requirements.get('recommended_interests', [])

    def is_compatible_with_soul(self, soul_pack: Dict[str, Any]) -> tuple:
        """
        Check if this template is compatible with a Soul

        Returns: (is_compatible: bool, reason: str)
        """
        # Check activity level
        activity = soul_pack.get('fingerprint', {}).get('activity_level', 0)
        if activity < self.min_activity_level:
            return False, f"Requires at least {self.min_activity_level} activity (you have {activity})"

        # Check required fields
        for field_path in self.required_fields:
            parts = field_path.split('.')
            value = soul_pack
            for part in parts:
                if part not in value:
                    return False, f"Missing required field: {field_path}"
                value = value[part]

        # All checks passed
        return True, "Compatible"

    def get_compatibility_score(self, soul_pack: Dict[str, Any]) -> float:
        """
        Calculate compatibility score (0-100)

        Higher score = better match between Soul and template
        """
        score = 50.0  # Base score

        # Bonus for matching interests
        if self.recommended_interests:
            soul_interests = set(soul_pack.get('essence', {}).get('interests', []))
            recommended = set(self.recommended_interests)
            overlap = len(soul_interests & recommended)
            score += (overlap / len(recommended)) * 30 if recommended else 0

        # Bonus for activity level
        activity = soul_pack.get('fingerprint', {}).get('activity_level', 0)
        if activity >= self.min_activity_level * 2:
            score += 20

        return min(score, 100.0)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        return {
            'template_id': self.template_id,
            'name': self.name,
            'description': self.description,
            'platform': self.platform,
            'soul_requirements': self.soul_requirements,
            'install_instructions': self.install_instructions
        }


class GameTemplateRegistry:
    """
    Registry of all available game templates

    This is like the Steam Store, but for Soul-compatible games.
    Users can browse, filter by platform, and see compatibility scores.
    """

    def __init__(self):
        self.templates = {}
        self.registry_path = Path('game_templates_registry.json')

        # Load existing registry or create default
        if self.registry_path.exists():
            self.load()
        else:
            self._create_default_templates()

    def register_template(self, template: GameTemplate):
        """Add a template to the registry"""
        self.templates[template.template_id] = template

    def get_template(self, template_id: str) -> GameTemplate:
        """Get a template by ID"""
        return self.templates.get(template_id)

    def list_templates(self, platform: str = None) -> List[GameTemplate]:
        """List all templates, optionally filtered by platform"""
        templates = list(self.templates.values())

        if platform:
            templates = [t for t in templates if t.platform == platform]

        return templates

    def find_compatible_templates(self, soul_pack: Dict[str, Any],
                                  min_score: float = 60.0) -> List[tuple]:
        """
        Find templates compatible with a Soul

        Returns list of (template, score, compatible, reason) tuples
        sorted by score descending
        """
        results = []

        for template in self.templates.values():
            is_compat, reason = template.is_compatible_with_soul(soul_pack)
            score = template.get_compatibility_score(soul_pack)

            if is_compat and score >= min_score:
                results.append((template, score, is_compat, reason))

        # Sort by score descending
        results.sort(key=lambda x: x[1], reverse=True)

        return results

    def save(self):
        """Save registry to JSON file"""
        data = {
            'version': '1.0',
            'templates': {
                tid: template.to_dict()
                for tid, template in self.templates.items()
            }
        }

        with open(self.registry_path, 'w') as f:
            json.dump(data, f, indent=2)

    def load(self):
        """Load registry from JSON file"""
        with open(self.registry_path) as f:
            data = json.load(f)

        for tid, tdata in data['templates'].items():
            template = GameTemplate(
                template_id=tdata['template_id'],
                name=tdata['name'],
                description=tdata['description'],
                platform=tdata['platform'],
                soul_requirements=tdata['soul_requirements']
            )
            template.install_instructions = tdata.get('install_instructions', [])
            self.templates[tid] = template

    def _create_default_templates(self):
        """Create some example templates to demonstrate the system"""

        # Roblox Tower Defense
        td_template = GameTemplate(
            template_id='roblox_tower_defense_v1',
            name='Soul Tower Defense',
            description='Tower defense game where your interests determine tower types. '
                       'Coding interest = Hacker Tower, Art interest = Paint Cannon, etc.',
            platform='roblox',
            soul_requirements={
                'min_activity': 5,
                'required_fields': ['essence.interests'],
                'recommended_interests': ['coding', 'gaming', 'strategy']
            }
        )
        td_template.install_instructions = [
            '1. Download your Soul Module (.lua)',
            '2. Open Tower Defense template in Roblox Studio',
            '3. Place Soul Module in ServerScriptService/Souls/',
            '4. Publish game and play!'
        ]
        self.register_template(td_template)

        # Minecraft Survival
        mc_survival = GameTemplate(
            template_id='minecraft_survival_v1',
            name='Soul Survival',
            description='Minecraft survival world where your expertise determines starting items. '
                       'Python expertise = Diamond Pickaxe, Art expertise = Painting, etc.',
            platform='minecraft',
            soul_requirements={
                'min_activity': 10,
                'required_fields': ['essence.expertise', 'essence.interests'],
                'recommended_interests': ['building', 'crafting', 'exploration']
            }
        )
        mc_survival.install_instructions = [
            '1. Download your Soul Data (.json)',
            '2. Install Spigot server',
            '3. Add SoulSurvival plugin',
            '4. Place soul JSON in plugins/SoulSurvival/players/',
            '5. Start server and join!'
        ]
        self.register_template(mc_survival)

        # Unity Platformer
        unity_platformer = GameTemplate(
            template_id='unity_platformer_v1',
            name='Soul Jumper',
            description='2D platformer where your Soul values determine character abilities. '
                       'Creativity = double jump, Focus = slow motion, etc.',
            platform='unity',
            soul_requirements={
                'min_activity': 3,
                'required_fields': ['essence.values', 'expression'],
                'recommended_interests': ['gaming', 'art', 'creativity']
            }
        )
        unity_platformer.install_instructions = [
            '1. Download Unity template package',
            '2. Download your Soul Asset (.json)',
            '3. Place in Assets/SoulAssets/',
            '4. Build and run!'
        ]
        self.register_template(unity_platformer)

        # Web Portfolio
        web_portfolio = GameTemplate(
            template_id='web_portfolio_v1',
            name='Soul Portfolio',
            description='Automatically generated portfolio website based on your Soul. '
                       'Interests become project categories, expertise becomes skills section.',
            platform='web',
            soul_requirements={
                'min_activity': 1,
                'required_fields': ['identity', 'essence'],
                'recommended_interests': []  # Any interests work
            }
        )
        web_portfolio.install_instructions = [
            '1. Visit your Soul profile: /@YOUR_USERNAME',
            '2. Click "Generate Portfolio"',
            '3. Customize theme and layout',
            '4. Download static site or deploy to GitHub Pages'
        ]
        self.register_template(web_portfolio)

        # Roblox RPG
        rpg_template = GameTemplate(
            template_id='roblox_rpg_v1',
            name='Soul RPG Adventure',
            description='RPG where your Soul determines character class and starting stats. '
                       'High karma = Paladin, Coding expertise = Technomancer, etc.',
            platform='roblox',
            soul_requirements={
                'min_activity': 15,
                'required_fields': ['essence.values', 'essence.expertise', 'expression.karma'],
                'recommended_interests': ['gaming', 'fantasy', 'story']
            }
        )
        rpg_template.install_instructions = [
            '1. Download Soul Module',
            '2. Load RPG template',
            '3. Run ClassGenerator script',
            '4. Your class is auto-selected from Soul data!'
        ]
        self.register_template(rpg_template)

        # Voice AI Assistant
        voice_template = GameTemplate(
            template_id='voice_assistant_v1',
            name='Your Soul AI',
            description='AI assistant trained on your Soul personality. '
                       'Talks like you, knows your interests, shares your values.',
            platform='voice',
            soul_requirements={
                'min_activity': 20,
                'required_fields': ['essence.interests', 'essence.values', 'expression'],
                'recommended_interests': ['ai', 'technology', 'communication']
            }
        )
        voice_template.install_instructions = [
            '1. Download Soul Persona config',
            '2. Install Ollama or connect to OpenAI',
            '3. Load persona into AI system',
            '4. Chat with your digital twin!'
        ]
        self.register_template(voice_template)

        # Save default templates
        self.save()


def demo_registry():
    """Demo the template registry system"""
    print("=" * 70)
    print("🎮 GAME TEMPLATE REGISTRY DEMO")
    print("=" * 70)
    print()

    # Create registry
    print("Loading template registry...")
    registry = GameTemplateRegistry()
    print(f"✅ Loaded {len(registry.templates)} templates")
    print()

    # List all templates
    print("📋 Available Templates:")
    print()
    for template in registry.list_templates():
        print(f"   {template.template_id}")
        print(f"   Name: {template.name}")
        print(f"   Platform: {template.platform}")
        print(f"   Min Activity: {template.soul_requirements['min_activity']}")
        print()

    # Test with a Soul
    from soul_model import Soul
    conn = get_db()
    user = conn.execute('SELECT id FROM users WHERE is_ai_persona = 0 LIMIT 1').fetchone()
    conn.close()

    if user:
        print(f"🧠 Testing compatibility with user ID {user['id']}...")
        soul = Soul(user['id'])
        pack = soul.compile_pack()

        compatible = registry.find_compatible_templates(pack, min_score=50.0)

        print(f"✅ Found {len(compatible)} compatible templates:")
        print()

        for template, score, is_compat, reason in compatible:
            print(f"   {template.name}")
            print(f"      Score: {score:.1f}/100")
            print(f"      Platform: {template.platform}")
            print(f"      Status: {reason}")
            print()

    print("=" * 70)
    print("Registry saved to: game_templates_registry.json")
    print("=" * 70)


if __name__ == '__main__':
    demo_registry()
