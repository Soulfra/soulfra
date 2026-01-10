#!/usr/bin/env python3
"""
Minecraft Connector - Generate Player Data JSON from Soul Pack

Transforms Soul Pack into Minecraft-compatible JSON with:
- Player attributes (health, hunger, experience)
- Custom NBT data for mods/plugins
- Soul items (interests as enchanted books)
- Chat rules for server plugins
- Skin URL reference
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List


class MinecraftConnector:
    """Generate Minecraft player data JSON from Soul Pack"""

    def __init__(self):
        self.output_dir = Path('platform_outputs/minecraft')
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _generate_soul_items(self, interests: List[str], expertise: List[str]) -> List[Dict]:
        """Generate custom items representing Soul interests"""
        items = []

        # Create enchanted books for each interest
        for idx, interest in enumerate(interests[:5]):
            item = {
                "Slot": idx,
                "id": "minecraft:enchanted_book",
                "Count": 1,
                "tag": {
                    "display": {
                        "Name": f"{{\"text\":\"Soul Interest: {interest}\",\"italic\":false}}",
                        "Lore": [
                            f"{{\"text\":\"This soul values {interest}\",\"color\":\"gray\",\"italic\":false}}"
                        ]
                    },
                    "SoulData": {
                        "Type": "Interest",
                        "Value": interest
                    }
                }
            }
            items.append(item)

        # Create special tools for expertise
        tool_map = {
            "python": "minecraft:diamond_pickaxe",
            "web": "minecraft:compass",
            "art": "minecraft:painting",
            "music": "minecraft:note_block"
        }

        # Extract expertise keys (expertise is a dict)
        expertise_list = list(expertise.keys()) if isinstance(expertise, dict) else expertise

        for idx, skill in enumerate(expertise_list[:3]):
            tool_id = tool_map.get(skill.lower(), "minecraft:diamond_sword")
            item = {
                "Slot": idx + 10,
                "id": tool_id,
                "Count": 1,
                "tag": {
                    "display": {
                        "Name": f"{{\"text\":\"Expertise: {skill}\",\"italic\":false,\"color\":\"gold\"}}",
                        "Lore": [
                            f"{{\"text\":\"Master of {skill}\",\"color\":\"yellow\",\"italic\":false}}"
                        ]
                    },
                    "Enchantments": [
                        {"id": "minecraft:unbreaking", "lvl": 3}
                    ],
                    "SoulData": {
                        "Type": "Expertise",
                        "Value": skill
                    }
                }
            }
            items.append(item)

        return items

    def _calculate_stats(self, soul_pack: Dict[str, Any]) -> Dict[str, float]:
        """Calculate Minecraft stats from Soul data"""
        expression = soul_pack.get('expression', {})
        essence = soul_pack.get('essence', {})

        # Base stats
        health = 20.0  # Default Minecraft health
        hunger = 20  # Full hunger
        experience_level = 1 + (expression.get('post_count', 0) // 10)

        # Calculate attribute modifiers from values
        values = essence.get('values', [])

        # Intelligence → max_health boost
        if 'learning' in values or 'knowledge' in values:
            health += 4.0

        # Social → luck boost
        # Creativity → movement speed boost
        # etc.

        return {
            "max_health": health,
            "health": health,
            "hunger": hunger,
            "experience_level": experience_level,
            "experience_total": experience_level * 100
        }

    def generate(self, soul_pack: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate Minecraft player data JSON from Soul Pack

        Args:
            soul_pack: Dictionary containing Soul data (from soul_model.py)

        Returns:
            Dictionary in Minecraft player data format
        """
        identity = soul_pack.get('identity', {})
        essence = soul_pack.get('essence', {})
        expression = soul_pack.get('expression', {})

        username = identity.get('username', 'Unknown')
        user_id = identity.get('user_id', 0)

        # Calculate stats
        stats = self._calculate_stats(soul_pack)

        # Generate Soul items
        soul_items = self._generate_soul_items(
            essence.get('interests', []),
            essence.get('expertise', {})
        )

        # Build player data
        player_data = {
            "DataVersion": 3218,  # Minecraft 1.19.x
            "playerGameType": 0,  # Survival mode
            "Dimension": "minecraft:overworld",
            "Pos": [0.0, 64.0, 0.0],
            "Rotation": [0.0, 0.0],
            "Motion": [0.0, 0.0, 0.0],

            # Health and stats
            "Health": stats["health"],
            "HurtTime": 0,
            "DeathTime": 0,
            "Air": 300,
            "Fire": -20,
            "FallDistance": 0.0,

            # Food
            "foodLevel": stats["hunger"],
            "foodSaturationLevel": 5.0,
            "foodExhaustionLevel": 0.0,

            # Experience
            "XpLevel": stats["experience_level"],
            "XpTotal": stats["experience_total"],
            "XpP": 0.0,

            # Inventory with Soul items
            "Inventory": soul_items,

            # Abilities
            "abilities": {
                "walkSpeed": 0.1,
                "flySpeed": 0.05,
                "mayfly": False,
                "flying": False,
                "invulnerable": False,
                "mayBuild": True,
                "instabuild": False
            },

            # Custom NBT data for Soulfra
            "SoulfraNBT": {
                "UserID": user_id,
                "Username": username,
                "Version": "1.0.0",
                "LastSync": "Never",

                "Identity": {
                    "UserID": user_id,
                    "Username": username,
                    "CreatedAt": identity.get('created_at', 'Unknown')
                },

                "Essence": {
                    "Values": essence.get('values', [])[:5],
                    "Interests": essence.get('interests', [])[:5],
                    "Expertise": list(essence.get('expertise', {}).keys())[:3]
                },

                "Expression": {
                    "PostCount": expression.get('post_count', 0),
                    "Karma": expression.get('karma', 100),
                    "LastActive": expression.get('last_active', 'Never')
                },

                # Chat rules for server plugins
                "ChatRules": {
                    "Enabled": True,
                    "BlockedWords": ["password", "credit card", "ssn", "hack"],
                    "RateLimitSeconds": 2,
                    "MaxMessageLength": 256
                },

                # Sync configuration
                "Sync": {
                    "Endpoint": "http://localhost:5000/api/soul/sync",
                    "IntervalSeconds": 60
                },

                # Appearance
                "Appearance": {
                    "SkinURL": f"http://localhost:5000/static/avatars/generated/{username}.png"
                }
            }
        }

        return player_data

    def save_to_file(self, player_data: Dict[str, Any], filename: str = None) -> Path:
        """
        Save generated player data to JSON file

        Args:
            player_data: Generated Minecraft player data
            filename: Optional custom filename (defaults to player_soul.json)

        Returns:
            Path to saved file
        """
        if filename is None:
            filename = 'player_soul.json'

        filepath = self.output_dir / filename

        with open(filepath, 'w') as f:
            json.dump(player_data, f, indent=2)

        return filepath

    def generate_and_save(self, soul_pack: Dict[str, Any], filename: str = None) -> Path:
        """
        Generate player data and save to file in one step

        Args:
            soul_pack: Dictionary containing Soul data
            filename: Optional custom filename

        Returns:
            Path to saved file
        """
        player_data = self.generate(soul_pack)
        return self.save_to_file(player_data, filename)


if __name__ == '__main__':
    # Test with example Soul Pack
    test_soul = {
        'identity': {
            'user_id': 1,
            'username': 'testminer',
            'created_at': '2024-12-25T00:00:00Z'
        },
        'essence': {
            'values': ['creativity', 'exploration', 'building'],
            'interests': ['redstone', 'architecture', 'farming'],
            'expertise': ['python', 'engineering', 'art']
        },
        'expression': {
            'post_count': 35,
            'karma': 120,
            'last_active': '2024-12-25T10:00:00Z'
        },
        'connections': {}
    }

    connector = MinecraftConnector()
    filepath = connector.generate_and_save(test_soul, 'testminer_soul.json')
    print(f"✅ Generated Minecraft Player Data: {filepath}")

    # Print preview
    with open(filepath) as f:
        data = json.load(f)
        print("\n📦 Soul Items:")
        for item in data['Inventory']:
            print(f"  - {item['id']}: {item['tag']['display']['Name']}")
