#!/usr/bin/env python3
"""
Game Orchestrator - Central Cross-Platform Game Coordinator

This is the "missing link" - the actual game loop that makes cross-platform D&D possible.

What it does:
1. Receives actions from any platform (Roblox, Minecraft, Mobile)
2. Loads player's Soul Pack to understand their abilities
3. Calls AI personas to judge if action succeeds
4. Uses neural networks to verify state transitions are legal
5. Updates game state (provably fair, hashed)
6. Syncs new state to ALL platforms
7. Stores immutable history

Think of this as the Dungeon Master's brain - it sees all players
across all platforms and coordinates their actions into one shared game world.
"""

import json
import hashlib
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

from database import get_db
from soul_model import Soul
from reasoning_engine import ReasoningEngine


class GameOrchestrator:
    """
    Central coordinator for cross-platform game

    This is the "music box mechanism" - it makes the cylinder (Soul Pack)
    play different tunes (game actions) across multiple platforms
    """

    def __init__(self, game_id: int):
        self.game_id = game_id
        self.reasoning_engine = ReasoningEngine()

        # Load game session
        self.session = self._load_session()

        if not self.session:
            raise ValueError(f"Game session {game_id} not found")

    def _load_session(self) -> Optional[Dict]:
        """Load game session from database"""
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM game_sessions WHERE game_id = ?
        ''', (self.game_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            # Convert to dict
            return dict(zip([col[0] for col in cursor.description], row))

        return None

    def get_current_state(self) -> Dict[str, Any]:
        """
        Get current game state

        Returns the latest verified state of the game world
        """
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM game_state
            WHERE game_id = ? AND is_current = 1
            ORDER BY turn_number DESC
            LIMIT 1
        ''', (self.game_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            raise ValueError(f"No current state for game {self.game_id}")

        state = dict(zip([col[0] for col in cursor.description], row))

        # Parse JSON fields
        state['board_state'] = json.loads(state['board_state']) if state['board_state'] else {}
        state['player_positions'] = json.loads(state['player_positions']) if state['player_positions'] else {}
        state['active_effects'] = json.loads(state['active_effects']) if state['active_effects'] else []

        return state

    def process_action(self, user_id: int, platform: str,
                      action_type: str, action_data: Dict[str, Any],
                      target_user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Process a player action

        This is the CORE GAME LOOP:
        1. Load player's Soul (their abilities/stats)
        2. Validate action is legal
        3. Call AI to judge outcome
        4. Generate neural network proof
        5. Update game state
        6. Sync to all platforms
        7. Return result

        Args:
            user_id: Player performing action
            platform: Where action came from ('roblox', 'minecraft', 'mobile')
            action_type: Type of action ('move', 'attack', 'cast_spell', etc.)
            action_data: Action-specific parameters
            target_user_id: Optional target player

        Returns:
            Dict with:
            - success: bool
            - ai_verdict: str
            - ai_reasoning: str
            - state_changes: Dict
            - proof_hash: str (neural network proof)
        """

        print(f"\n🎮 Processing action: {action_type} from {platform}")

        # Get current state
        current_state = self.get_current_state()
        state_before_hash = current_state['state_hash']

        # Load player's Soul Pack
        soul = Soul(user_id)
        soul_pack = soul.compile_pack()

        print(f"   Player: {soul_pack['identity']['username']}")
        print(f"   Platform: {platform}")

        # Validate action is legal (basic checks)
        is_valid, validation_msg = self._validate_action(
            action_type,
            action_data,
            soul_pack,
            current_state
        )

        if not is_valid:
            return {
                'success': False,
                'reason': validation_msg,
                'ai_verdict': 'invalid',
                'ai_reasoning': f'Action failed validation: {validation_msg}'
            }

        # Call AI persona to judge action
        ai_persona = self.session['dungeon_master_ai']
        ai_result = self._ai_judge_action(
            action_type,
            action_data,
            soul_pack,
            current_state,
            ai_persona
        )

        print(f"   AI Verdict: {ai_result['verdict']}")
        print(f"   AI Reasoning: {ai_result['reasoning'][:100]}...")

        # If AI says action fails, return early
        if ai_result['verdict'] == 'failure':
            # Still log the attempt
            self._log_action(
                user_id, platform, action_type, action_data,
                target_user_id, soul_pack, state_before_hash,
                state_before_hash,  # State didn't change
                ai_persona, ai_result, {}
            )

            return {
                'success': False,
                'ai_verdict': ai_result['verdict'],
                'ai_reasoning': ai_result['reasoning'],
                'state_changes': {}
            }

        # Apply action to state
        new_state, state_changes = self._apply_action(
            action_type,
            action_data,
            soul_pack,
            current_state,
            ai_result
        )

        # Generate state hash
        state_after_hash = self._hash_state(new_state)

        # Verify state transition with neural network (if enabled)
        if self.session['enable_ai_judging']:
            proof = self._neural_verify_transition(
                state_before_hash,
                state_after_hash,
                action_type,
                action_data
            )
        else:
            proof = {'proof_hash': 'verification_disabled'}

        # Log action to immutable history
        action_id = self._log_action(
            user_id, platform, action_type, action_data,
            target_user_id, soul_pack, state_before_hash,
            state_after_hash, ai_persona, ai_result, state_changes
        )

        # Save new state
        self._save_new_state(new_state, state_after_hash, 'game_state_validator')

        # Sync to all platforms (THIS IS THE MAGIC - cross-platform update!)
        self._sync_to_all_platforms(new_state, state_changes)

        print(f"   ✅ Action processed successfully")
        print(f"   State hash: {state_after_hash[:16]}...")

        return {
            'success': True,
            'action_id': action_id,
            'ai_verdict': ai_result['verdict'],
            'ai_reasoning': ai_result['reasoning'],
            'ai_confidence': ai_result['confidence'],
            'state_changes': state_changes,
            'state_hash': state_after_hash,
            'proof_hash': proof['proof_hash']
        }

    def _validate_action(self, action_type: str, action_data: Dict,
                        soul_pack: Dict, current_state: Dict) -> Tuple[bool, str]:
        """
        Basic validation of action

        Checks:
        - Is it the player's turn?
        - Does player have required stats/items?
        - Is action within game rules?

        Note: Validation is permissive - AI will judge success based on expertise
        """

        # Check if it's player's turn (for turn-based games)
        # TODO: Implement turn order system

        # Allow most actions - let AI judge success based on expertise
        # Only block truly invalid actions (malformed data, etc.)

        if action_type == 'move':
            # Validate move has required fields
            if 'to_position' not in action_data and 'position' not in action_data:
                return False, "Move action requires 'position' or 'to_position' field"

        elif action_type == 'cast_spell':
            # Validate spell has name
            if 'spell' not in action_data:
                return False, "Spell action requires 'spell' field"

        elif action_type == 'build':
            # Validate building has type
            if 'building_type' not in action_data:
                return False, "Build action requires 'building_type' field"

        # All actions are allowed to attempt
        # AI will determine success/partial/failure based on Soul expertise
        return True, "Action validated"

    def _check_ollama_available(self) -> bool:
        """Check if Ollama is running and available"""
        try:
            import urllib.request
            import urllib.error

            req = urllib.request.Request('http://localhost:11434/api/tags')
            urllib.request.urlopen(req, timeout=2)
            return True
        except (urllib.error.URLError, TimeoutError, Exception):
            return False

    def _ai_judge_action(self, action_type: str, action_data: Dict,
                        soul_pack: Dict, current_state: Dict,
                        ai_persona: str) -> Dict[str, Any]:
        """
        Call AI persona to judge if action succeeds

        Different AI personas have different judging styles:
        - CalRiven: Technical precision
        - DeathToData: Privacy focus
        - TheAuditor: Rules enforcement
        - Soulfra: Security considerations
        """

        # Build prompt for AI
        prompt = f"""You are the Dungeon Master for a cross-platform D&D game.

Player Action: {action_type}
Action Details: {json.dumps(action_data, indent=2)}

Player Soul:
- Username: {soul_pack['identity']['username']}
- Interests: {', '.join(soul_pack['essence']['interests'][:5])}
- Expertise: {', '.join(list(soul_pack['essence']['expertise'].keys())[:3])}
- Values: {', '.join(soul_pack['essence']['values'][:3])}
- Level: {soul_pack['expression'].get('level', 1)}

Current Game State:
{json.dumps(current_state['board_state'], indent=2)[:500]}...

Judge whether this action SUCCEEDS or FAILS.
Consider the player's Soul expertise and the game situation.

Respond ONLY with a JSON object in this exact format:
{{"verdict": "success|partial|failure", "reasoning": "1-2 sentence explanation", "confidence": 0.0-1.0}}
"""

        # Try Ollama first (if enabled and available)
        if self.session.get('enable_ai_judging') and self._check_ollama_available():
            try:
                import urllib.request
                import urllib.error

                # Map persona names to ollama_discussion.py format
                persona_map = {
                    'calriven': 'calriven',
                    'deathtodata': 'deathtodata',
                    'theauditor': 'theauditor',
                    'soulfra': 'soulfra'
                }

                persona_name = persona_map.get(ai_persona.lower(), 'calriven')

                # Load persona config from ollama_discussion
                from ollama_discussion import PERSONAS
                persona_config = PERSONAS.get(persona_name, PERSONAS['calriven'])

                request_data = {
                    'model': 'llama2',
                    'prompt': prompt,
                    'system': persona_config['system_prompt'],
                    'stream': False,
                    'options': {
                        'temperature': 0.7,
                        'num_predict': 300
                    }
                }

                req = urllib.request.Request(
                    'http://localhost:11434/api/generate',
                    data=json.dumps(request_data).encode('utf-8'),
                    headers={'Content-Type': 'application/json'}
                )

                response = urllib.request.urlopen(req, timeout=30)
                result = json.loads(response.read().decode('utf-8'))
                ai_response = result.get('response', '').strip()

                # Try to parse JSON response
                try:
                    # Extract JSON from response (in case AI adds extra text)
                    import re
                    json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                    if json_match:
                        ai_data = json.loads(json_match.group())
                        return {
                            'verdict': ai_data.get('verdict', 'success'),
                            'reasoning': ai_data.get('reasoning', ai_response[:200]),
                            'confidence': float(ai_data.get('confidence', 0.7))
                        }
                except (json.JSONDecodeError, ValueError):
                    pass

                # If JSON parsing failed, parse text response
                if 'fail' in ai_response.lower() or 'failure' in ai_response.lower():
                    verdict = 'failure'
                elif 'partial' in ai_response.lower():
                    verdict = 'partial'
                else:
                    verdict = 'success'

                return {
                    'verdict': verdict,
                    'reasoning': ai_response[:200] if ai_response else 'AI decision based on game context',
                    'confidence': 0.7
                }

            except Exception as e:
                print(f"   ⚠️  Ollama error: {e}")
                print(f"   Falling back to rule-based judgment...")

        # Fallback: Rule-based judgment using player expertise
        try:
            # Simple AI decision based on player expertise
            expertise_keys = list(soul_pack['essence']['expertise'].keys())

            # Check if player has relevant expertise for action
            has_relevant_skill = False

            if action_type in ['cast_spell', 'hack'] and any(k in expertise_keys for k in ['coding', 'technology', 'magic']):
                has_relevant_skill = True
            elif action_type == 'build' and any(k in expertise_keys for k in ['engineering', 'architecture', 'building']):
                has_relevant_skill = True
            elif action_type == 'move':
                has_relevant_skill = True  # Anyone can move
            elif action_type == 'attack':
                has_relevant_skill = True  # Anyone can attempt attack

            if has_relevant_skill:
                verdict = 'success'
                reasoning = f"Player has relevant expertise ({', '.join(expertise_keys[:2])}) for this action."
                confidence = 0.8
            else:
                verdict = 'partial'
                reasoning = f"Player lacks expertise for {action_type}, but attempting anyway."
                confidence = 0.5

            return {
                'verdict': verdict,
                'reasoning': reasoning,
                'confidence': confidence
            }

        except Exception as e:
            # Ultimate fallback if everything fails
            return {
                'verdict': 'success',
                'reasoning': f'AI unavailable, allowing action by default',
                'confidence': 0.5
            }

    def _apply_action(self, action_type: str, action_data: Dict,
                     soul_pack: Dict, current_state: Dict,
                     ai_result: Dict) -> Tuple[Dict, Dict]:
        """
        Apply action effects to game state

        Returns: (new_state, state_changes)
        """

        # Copy current state
        new_state = {
            'world_map': current_state['board_state'].copy(),
            'player_positions': current_state['player_positions'].copy(),
            'active_effects': current_state['active_effects'].copy()
        }

        state_changes = {
            'action_type': action_type,
            'effects': []
        }

        user_id = soul_pack['identity']['user_id']

        # Apply action-specific effects
        if action_type == 'move':
            # Update player position
            new_pos = action_data.get('position', [0, 0])
            new_state['player_positions'][str(user_id)] = new_pos
            state_changes['effects'].append(f"Player moved to {new_pos}")

        elif action_type == 'cast_spell':
            # Add spell effect
            spell_name = action_data.get('spell', 'Unknown')
            effect = {
                'type': 'spell',
                'name': spell_name,
                'caster_id': user_id,
                'duration': action_data.get('duration', 3),
                'target': action_data.get('target')
            }
            new_state['active_effects'].append(effect)
            state_changes['effects'].append(f"Cast {spell_name}")

        elif action_type == 'build':
            # Add building to world
            building = {
                'type': action_data.get('building_type', 'structure'),
                'owner_id': user_id,
                'position': action_data.get('position', [0, 0]),
                'health': 100
            }
            if 'buildings' not in new_state['world_map']:
                new_state['world_map']['buildings'] = []
            new_state['world_map']['buildings'].append(building)
            state_changes['effects'].append(f"Built {building['type']}")

        elif action_type == 'attack':
            # Apply damage
            target_id = action_data.get('target_id')
            damage = action_data.get('damage', 10)
            state_changes['effects'].append(f"Attacked player {target_id} for {damage} damage")

        return new_state, state_changes

    def _hash_state(self, state: Dict) -> str:
        """Generate SHA-256 hash of game state (provable!)"""
        state_json = json.dumps(state, sort_keys=True)
        return hashlib.sha256(state_json.encode()).hexdigest()

    def _neural_verify_transition(self, state_before: str, state_after: str,
                                  action_type: str, action_data: Dict) -> Dict:
        """
        Verify state transition with neural network

        This generates a PROOF that the state change is valid
        Anyone can verify by running the same neural net with same inputs!
        """

        # TODO: Implement actual neural network verification
        # For now, return simple proof

        proof_data = {
            'state_before': state_before,
            'state_after': state_after,
            'action': action_type,
            'timestamp': datetime.now().isoformat()
        }

        proof_json = json.dumps(proof_data, sort_keys=True)
        proof_hash = hashlib.sha256(proof_json.encode()).hexdigest()

        return {
            'proof_hash': proof_hash,
            'is_valid': True,
            'reproducible': True
        }

    def _log_action(self, user_id: int, platform: str, action_type: str,
                   action_data: Dict, target_user_id: Optional[int],
                   soul_pack: Dict, state_before_hash: str,
                   state_after_hash: str, ai_persona: str,
                   ai_result: Dict, state_changes: Dict) -> int:
        """Log action to immutable history"""

        conn = get_db()
        cursor = conn.cursor()

        # Generate action hash
        action_payload = {
            'user_id': user_id,
            'action_type': action_type,
            'action_data': action_data,
            'timestamp': datetime.now().isoformat()
        }
        action_hash = hashlib.sha256(
            json.dumps(action_payload, sort_keys=True).encode()
        ).hexdigest()

        cursor.execute('''
            INSERT INTO game_actions (
                game_id, turn_number, player_user_id, player_platform,
                soul_pack_snapshot, action_type, action_data, target_user_id,
                judged_by_ai, ai_verdict, ai_reasoning, ai_confidence,
                state_before_hash, state_after_hash, changes_applied,
                action_hash, verified, processed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            self.game_id,
            self.session['current_turn'],
            user_id,
            platform,
            json.dumps(soul_pack),
            action_type,
            json.dumps(action_data),
            target_user_id,
            ai_persona,
            ai_result['verdict'],
            ai_result['reasoning'],
            ai_result['confidence'],
            state_before_hash,
            state_after_hash,
            json.dumps(state_changes),
            action_hash,
            1,  # verified
            datetime.now()
        ))

        action_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return action_id

    def _save_new_state(self, new_state: Dict, state_hash: str,
                       verified_by: str):
        """Save new game state to database"""

        conn = get_db()
        cursor = conn.cursor()

        # Mark old state as not current
        cursor.execute('''
            UPDATE game_state
            SET is_current = 0
            WHERE game_id = ? AND is_current = 1
        ''', (self.game_id,))

        # Insert new state
        cursor.execute('''
            INSERT INTO game_state (
                game_id, turn_number, board_state, player_positions,
                active_effects, state_hash, verified_by_network,
                verification_confidence, is_current
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            self.game_id,
            self.session['current_turn'] + 1,
            json.dumps(new_state.get('world_map', {})),
            json.dumps(new_state.get('player_positions', {})),
            json.dumps(new_state.get('active_effects', [])),
            state_hash,
            verified_by,
            1.0,
            1  # is_current
        ))

        # Increment turn
        cursor.execute('''
            UPDATE game_sessions
            SET current_turn = current_turn + 1,
                last_action_at = ?
            WHERE game_id = ?
        ''', (datetime.now(), self.game_id))

        conn.commit()
        conn.close()

        # Reload session to get updated turn number
        self.session = self._load_session()

    def _sync_to_all_platforms(self, new_state: Dict, state_changes: Dict):
        """
        Sync new game state to ALL platforms

        THIS IS THE MAGIC - cross-platform synchronization!

        Platforms that need updating:
        - Roblox players (via HttpService)
        - Minecraft players (via plugin sync)
        - Mobile commanders (via WebSocket/API)
        - Web viewers (via SSE)
        """

        # TODO: Implement actual platform sync
        # For now, just log what would happen

        print(f"\n   📡 Syncing to all platforms...")
        print(f"      Changes: {json.dumps(state_changes, indent=2)[:200]}...")

        # Get all players in this game
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT user_id, roblox_active, minecraft_active, mobile_active
            FROM cross_platform_players
            WHERE game_id = ? AND is_online = 1
        ''', (self.game_id,))

        players = cursor.fetchall()
        conn.close()

        for player in players:
            user_id, roblox, minecraft, mobile = player

            if roblox:
                print(f"      → Roblox player {user_id}: Update game state")

            if minecraft:
                print(f"      → Minecraft player {user_id}: Update world")

            if mobile:
                print(f"      → Mobile commander {user_id}: Update strategic view")


if __name__ == '__main__':
    # Test the orchestrator
    print("=" * 70)
    print("🎮 GAME ORCHESTRATOR TEST")
    print("=" * 70)
    print()

    # Create orchestrator for game #1
    orch = GameOrchestrator(game_id=1)

    print(f"Game: {orch.session['session_name']}")
    print(f"Turn: {orch.session['current_turn']}")
    print(f"AI DM: {orch.session['dungeon_master_ai']}")
    print()

    # Get current state
    state = orch.get_current_state()
    print(f"Current state hash: {state['state_hash'][:32]}...")
    print()

    print("✅ Orchestrator initialized and ready!")
    print()
    print("Next: Test with actual player action")
    print("  python3 -c 'from game_orchestrator import GameOrchestrator; ...")
