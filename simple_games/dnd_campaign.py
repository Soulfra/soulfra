#!/usr/bin/env python3
"""
D&D Campaign Game - AI Dungeon Master with Item Economy

A complete D&D-style campaign where:
- AI judges your actions using Ollama
- Earn items through quests and battles
- Character ages through gameplay (trade agility for wisdom)
- Trade items with other players
- No crypto/blockchain - pure gameplay

This replaces ALL blockchain mechanics with traditional game design.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_orchestrator import GameOrchestrator
from aging_curves import get_all_attributes, get_attribute_change
import sqlite3
import json
import hashlib
from typing import Dict, List, Optional
try:
    from binary_protocol import encode, decode
    BINARY_AVAILABLE = True
except ImportError:
    BINARY_AVAILABLE = False

try:
    from dnd_ai_commenters import notify_ai_commenters
    AI_COMMENTERS_AVAILABLE = True
except ImportError:
    AI_COMMENTERS_AVAILABLE = False


class DNDCampaign:
    """
    Turn-based D&D campaign with AI dungeon master

    Flow:
    1. Select quest from quest board
    2. Form party (single or multiplayer)
    3. AI describes scenario
    4. Players take turns (attack, cast spell, use item, etc.)
    5. AI judges each action based on player's Soul expertise
    6. Quest completes → character ages → earn items
    """

    def __init__(self, game_id: int, user_id: int, quest_slug: str):
        self.game_id = game_id
        self.user_id = user_id
        self.quest_slug = quest_slug
        self.conn = sqlite3.connect('soulfra.db')
        self.cursor = self.conn.cursor()

        # Load quest details
        self.quest = self._load_quest()

        # Load character details
        self.character = self._load_character()

    def _load_quest(self) -> Dict:
        """Load quest from database"""
        self.cursor.execute('''
            SELECT id, name, description, story, difficulty,
                   aging_years, rewards, max_party_size
            FROM quests
            WHERE quest_slug = ? AND active = 1
        ''', (self.quest_slug,))

        row = self.cursor.fetchone()
        if not row:
            raise ValueError(f"Quest '{self.quest_slug}' not found or inactive")

        return {
            'id': row[0],
            'name': row[1],
            'description': row[2],
            'story': row[3],
            'difficulty': row[4],
            'aging_years': row[5],
            'rewards': json.loads(row[6]) if row[6] else {},
            'max_party_size': row[7]
        }

    def _load_character(self) -> Dict:
        """Load character from database"""
        self.cursor.execute('''
            SELECT username, character_age, total_years_aged
            FROM users
            WHERE id = ?
        ''', (self.user_id,))

        row = self.cursor.fetchone()
        if not row:
            raise ValueError(f"User {self.user_id} not found")

        age = row[1] or 20  # Default age 20

        # Get attributes based on age
        attributes = get_all_attributes(age)

        return {
            'username': row[0],
            'age': age,
            'total_years_aged': row[2] or 0,
            'attributes': attributes
        }

    def start_quest(self) -> Dict:
        """Start the quest - AI describes opening scenario"""

        # Build context for AI
        context = f"""
You are the Dungeon Master for a D&D quest.

Quest: {self.quest['name']}
Difficulty: {self.quest['difficulty']}
Story: {self.quest['story']}

Player: {self.character['username']}
Age: {self.character['age']} years old
Attributes:
- Agility: {self.character['attributes']['agility']:.2f}
- Strength: {self.character['attributes']['strength']:.2f}
- Wisdom: {self.character['attributes']['wisdom']:.2f}
- Intelligence: {self.character['attributes']['intelligence']:.2f}
- Constitution: {self.character['attributes']['constitution']:.2f}
- Charisma: {self.character['attributes']['charisma']:.2f}

Describe the opening scene. Set the stage for adventure.
Keep it to 2-3 sentences. End with what the player sees/hears.
"""

        # Use game orchestrator to get AI response
        orch = GameOrchestrator(self.game_id)

        # Create opening narration action
        result = orch.process_action(
            user_id=self.user_id,
            platform='web',
            action_type='quest_start',
            action_data={
                'quest_slug': self.quest_slug,
                'quest_name': self.quest['name'],
                'character_age': self.character['age'],
                'ai_prompt': context
            }
        )

        quest_result = {
            'success': True,
            'narration': result.get('ai_response', self.quest.get('description', 'The quest begins...')),
            'quest': self.quest,
            'character': self.character
        }

        # Notify brand AIs about quest start
        if AI_COMMENTERS_AVAILABLE:
            try:
                rewards = json.loads(self.quest.get('rewards', '{}')) if isinstance(self.quest.get('rewards'), str) else self.quest.get('rewards', {})
                notify_ai_commenters('quest_start', {
                    'quest_name': self.quest['name'],
                    'difficulty': self.quest['difficulty'],
                    'aging_years': self.quest.get('aging_years', 0),
                    'rewards': rewards
                }, max_comments=2)
            except Exception as e:
                print(f"AI commenters notification failed: {e}")

        return quest_result

    def take_action(self, action_type: str, action_description: str, target: Optional[str] = None) -> Dict:
        """
        Player takes an action during quest

        Args:
            action_type: 'attack', 'cast_spell', 'use_item', 'investigate', 'talk'
            action_description: What the player is doing
            target: Optional target (enemy, object, NPC)
        """

        # Build AI prompt
        context = f"""
You are the Dungeon Master judging a player's action.

Quest: {self.quest['name']} ({self.quest['difficulty']} difficulty)

Player: {self.character['username']} (Age {self.character['age']})
Attributes:
- Agility: {self.character['attributes']['agility']:.2f}
- Strength: {self.character['attributes']['strength']:.2f}
- Wisdom: {self.character['attributes']['wisdom']:.2f}
- Intelligence: {self.character['attributes']['intelligence']:.2f}

Action Type: {action_type}
Action: {action_description}
{f"Target: {target}" if target else ""}

Judge this action. Consider the player's attributes.
Does it succeed, fail, or partially succeed?
Respond with: SUCCESS, FAILURE, or PARTIAL
Then explain what happens in 2-3 sentences.
"""

        # Use game orchestrator for AI judging
        orch = GameOrchestrator(self.game_id)

        result = orch.process_action(
            user_id=self.user_id,
            platform='web',
            action_type=action_type,
            action_data={
                'action': action_description,
                'target': target,
                'character_age': self.character['age'],
                'attributes': self.character['attributes'],
                'ai_prompt': context
            }
        )

        return {
            'success': result.get('success', False),
            'verdict': result.get('ai_verdict', 'unknown'),
            'narration': result.get('ai_response', 'The action unfolds...'),
            'reasoning': result.get('ai_reasoning', '')
        }

    def complete_quest(self) -> Dict:
        """
        Complete the quest - age character, award items, update Soul

        Returns:
            Dict with:
            - age_before, age_after
            - attribute_changes
            - items_earned
            - xp_earned
            - reputation_earned
        """

        age_before = self.character['age']
        age_after = age_before + self.quest['aging_years']

        # Calculate attribute changes
        attribute_changes = get_attribute_change(age_before, age_after)

        # Update character age in database
        total_years_aged = self.character['total_years_aged'] + self.quest['aging_years']

        self.cursor.execute('''
            UPDATE users
            SET character_age = ?,
                total_years_aged = ?
            WHERE id = ?
        ''', (age_after, total_years_aged, self.user_id))

        # Create character snapshot
        new_attrs = get_all_attributes(age_after)
        self.cursor.execute('''
            INSERT INTO character_snapshots
            (user_id, age, agility, wisdom, strength, charisma, intelligence, constitution, snapshot_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            self.user_id,
            age_after,
            new_attrs['agility'],
            new_attrs['wisdom'],
            new_attrs['strength'],
            new_attrs['charisma'],
            new_attrs['intelligence'],
            new_attrs['constitution'],
            f'quest_complete:{self.quest_slug}'
        ))

        # Award items to inventory
        items_earned = []
        rewards = self.quest['rewards']

        if 'items' in rewards:
            for item_reward in rewards['items']:
                item_id = item_reward['id']
                quantity = item_reward['quantity']

                # Check if item already in inventory
                self.cursor.execute('''
                    SELECT id, quantity FROM inventory
                    WHERE user_id = ? AND item_id = ?
                ''', (self.user_id, item_id))

                existing = self.cursor.fetchone()

                if existing:
                    # Update quantity
                    new_quantity = existing[1] + quantity
                    self.cursor.execute('''
                        UPDATE inventory
                        SET quantity = ?
                        WHERE id = ?
                    ''', (new_quantity, existing[0]))
                else:
                    # Add new item
                    self.cursor.execute('''
                        INSERT INTO inventory
                        (user_id, item_id, quantity, earned_from)
                        VALUES (?, ?, ?, ?)
                    ''', (self.user_id, item_id, quantity, f'quest:{self.quest_slug}'))

                # Get item details
                self.cursor.execute('SELECT name, rarity FROM items WHERE id = ?', (item_id,))
                item_row = self.cursor.fetchone()
                if item_row:
                    items_earned.append({
                        'id': item_id,
                        'name': item_row[0],
                        'rarity': item_row[1],
                        'quantity': quantity
                    })

        self.conn.commit()

        completion_result = {
            'success': True,
            'age_before': age_before,
            'age_after': age_after,
            'years_aged': self.quest['aging_years'],
            'attribute_changes': attribute_changes,
            'items_earned': items_earned,
            'xp_earned': rewards.get('xp', 0),
            'reputation_earned': rewards.get('reputation', 0)
        }

        # Notify brand AIs about quest completion
        if AI_COMMENTERS_AVAILABLE:
            try:
                notify_ai_commenters('quest_complete', {
                    'quest_name': self.quest['name'],
                    'years_aged': self.quest['aging_years'],
                    'items_earned': items_earned,
                    'xp_earned': rewards.get('xp', 0)
                }, max_comments=3)
            except Exception as e:
                print(f"AI commenters notification failed: {e}")

        return completion_result

    def create_binary_snapshot(self, tag: str = None) -> Optional[bytes]:
        """
        Create binary snapshot of current game state (filesystem-style storage)

        This uses binary protocol to store game state compactly in database,
        like a filesystem stores files. Can be tagged for organization.

        Args:
            tag: Optional tag for this snapshot (like a git tag)

        Returns:
            Binary encoded state or None if binary protocol unavailable
        """
        if not BINARY_AVAILABLE:
            return None

        # Gather full game state
        state = {
            'game_id': self.game_id,
            'user_id': self.user_id,
            'quest_slug': self.quest_slug,
            'quest_name': self.quest.get('name', ''),
            'character_age': self.character.get('character_age', 20),
            'character_attributes': get_all_attributes(self.character.get('character_age', 20)),
            'progress': self.quest.get('progress', 0),
            'timestamp': str(datetime.now())
        }

        # Encode to binary (compressed automatically if enabled)
        binary_state = encode(state, compress=True)

        # Store in database with tag
        self.cursor.execute('''
            INSERT INTO game_state_snapshots (game_id, user_id, state_binary, state_tag, created_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (self.game_id, self.user_id, binary_state, tag or f'snapshot-{datetime.now().timestamp()}'))

        self.conn.commit()

        return binary_state

    def load_binary_snapshot(self, snapshot_tag: str) -> Optional[Dict]:
        """
        Load game state from binary snapshot by tag (filesystem-style retrieval)

        Args:
            snapshot_tag: Tag to load

        Returns:
            Decoded state dict or None
        """
        if not BINARY_AVAILABLE:
            return None

        self.cursor.execute('''
            SELECT state_binary FROM game_state_snapshots
            WHERE user_id = ? AND state_tag = ?
            ORDER BY created_at DESC
            LIMIT 1
        ''', (self.user_id, snapshot_tag))

        row = self.cursor.fetchone()
        if not row:
            return None

        # Decode binary state
        binary_data = row[0]
        state = decode(binary_data)

        return state

    def __del__(self):
        """Clean up database connection"""
        if hasattr(self, 'conn'):
            self.conn.close()


def create_dnd_game(user_id: int, quest_slug: str) -> int:
    """Create a new D&D campaign game session"""

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    # Get quest name
    cursor.execute('SELECT name FROM quests WHERE quest_slug = ?', (quest_slug,))
    quest_row = cursor.fetchone()
    quest_name = quest_row[0] if quest_row else 'D&D Quest'

    # Create game session
    cursor.execute('''
        INSERT INTO game_sessions (
            session_name, game_type, creator_user_id,
            max_players, dungeon_master_ai, enable_ai_judging
        ) VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        f'D&D: {quest_name}',
        'dnd',
        user_id,
        4,  # Max 4 players in party
        'calriven',  # AI dungeon master
        1  # Enable AI judging
    ))

    game_id = cursor.lastrowid

    # Create initial game state
    initial_state = {
        'quest_slug': quest_slug,
        'turn_number': 0,
        'quest_started': False,
        'quest_completed': False,
        'party_members': [user_id]
    }

    state_json = json.dumps(initial_state, sort_keys=True)
    state_hash = hashlib.sha256(state_json.encode()).hexdigest()

    cursor.execute('''
        INSERT INTO game_state (
            game_id, turn_number, board_state, player_positions,
            active_effects, state_hash, verified_by_network, is_current
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (game_id, 0, state_json, '{}', '[]', state_hash, 'ai_dungeon_master', 1))

    conn.commit()
    conn.close()

    return game_id


def get_available_quests() -> List[Dict]:
    """Get all available quests from database"""

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT quest_slug, name, description, difficulty,
               aging_years, rewards, estimated_time_minutes
        FROM quests
        WHERE active = 1
        ORDER BY
            CASE difficulty
                WHEN 'easy' THEN 1
                WHEN 'medium' THEN 2
                WHEN 'hard' THEN 3
                WHEN 'legendary' THEN 4
                ELSE 5
            END
    ''')

    quests = []
    for row in cursor.fetchall():
        rewards = json.loads(row[5]) if row[5] else {}

        quests.append({
            'slug': row[0],
            'name': row[1],
            'description': row[2],
            'difficulty': row[3],
            'aging_years': row[4],
            'rewards': rewards,
            'estimated_minutes': row[6]
        })

    conn.close()
    return quests


def get_user_active_game(user_id: int) -> Optional[Dict]:
    """
    Get user's active D&D game

    Args:
        user_id: User ID

    Returns:
        Dict with game info or None if no active game
    """
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM dnd_games
        WHERE user_id = ? AND status = 'active'
        ORDER BY created_at DESC
        LIMIT 1
    ''', (user_id,))

    game = cursor.fetchone()
    conn.close()

    return dict(game) if game else None


if __name__ == '__main__':
    """Test the D&D campaign"""

    # Get first user
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, username FROM users LIMIT 1')
    user = cursor.fetchone()
    conn.close()

    if not user:
        print("❌ No users found. Create a user first.")
        sys.exit(1)

    user_id = user[0]
    username = user[1]

    print()
    print("=" * 60)
    print("🐉 D&D CAMPAIGN")
    print("=" * 60)
    print()
    print(f"🎮 Player: {username} (ID: {user_id})")
    print()

    # Show available quests
    quests = get_available_quests()

    print("📜 AVAILABLE QUESTS:")
    print("-" * 60)
    for i, quest in enumerate(quests, 1):
        print(f"{i}. {quest['name']} ({quest['difficulty'].upper()})")
        print(f"   {quest['description']}")
        print(f"   ⏰ Ages +{quest['aging_years']} years | 🎁 {len(quest['rewards'].get('items', []))} items")
        print()

    # Let user choose quest
    choice = input("Choose quest (1-4): ").strip()

    try:
        quest_idx = int(choice) - 1
        if quest_idx < 0 or quest_idx >= len(quests):
            raise ValueError()

        selected_quest = quests[quest_idx]
    except (ValueError, IndexError):
        print("❌ Invalid choice")
        sys.exit(1)

    # Create game
    game_id = create_dnd_game(user_id, selected_quest['slug'])
    print()
    print(f"✅ Game created (ID: {game_id})")
    print()

    # Start quest
    campaign = DNDCampaign(game_id, user_id, selected_quest['slug'])
    start_result = campaign.start_quest()

    print("=" * 60)
    print("📖 QUEST BEGINS")
    print("=" * 60)
    print()
    print(start_result['narration'])
    print()

    # Take some actions
    print("-" * 60)
    print("⚔️  BATTLE BEGINS")
    print("-" * 60)
    print()

    action = input("What do you do? (e.g., 'attack with sword', 'cast fireball'): ").strip()

    if action:
        action_result = campaign.take_action('attack', action, 'enemy')

        print()
        print(f"🎲 Verdict: {action_result['verdict'].upper()}")
        print()
        print(action_result['narration'])
        print()

    # Complete quest
    print("-" * 60)
    complete = input("Complete quest? (y/n): ").strip().lower()

    if complete == 'y':
        completion_result = campaign.complete_quest()

        print()
        print("=" * 60)
        print("🎉 QUEST COMPLETED!")
        print("=" * 60)
        print()
        print(f"⏰ Age: {completion_result['age_before']} → {completion_result['age_after']} (+{completion_result['years_aged']} years)")
        print()
        print("📊 ATTRIBUTE CHANGES:")
        for attr, change in completion_result['attribute_changes'].items():
            symbol = "▲" if change['delta'] > 0 else "▼" if change['delta'] < 0 else "="
            print(f"   {attr.capitalize():<15} {change['before']:.2f} → {change['after']:.2f} ({symbol} {abs(change['delta']):.2f})")

        print()
        print("🎁 ITEMS EARNED:")
        for item in completion_result['items_earned']:
            print(f"   {item['name']} ({item['rarity']}) x{item['quantity']}")

        print()
        print(f"✨ XP: +{completion_result['xp_earned']}")
        print(f"⭐ Reputation: +{completion_result['reputation_earned']}")
        print()
        print("=" * 60)
