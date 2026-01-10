#!/usr/bin/env python3
"""
Initialize Game State Database Tables

Creates the foundation for cross-platform D&D-style game:
- game_state: Current world state (shared across platforms)
- game_actions: Turn-by-turn action log
- verified_proofs: Neural network validations
- cross_platform_players: Player presence across platforms
- game_sessions: Active game instances

This is the "truth database" that all platforms sync to.
"""

import sqlite3
from datetime import datetime


def init_game_tables():
    """Create all game-related database tables"""

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    print("=" * 70)
    print("🎮 INITIALIZING GAME STATE DATABASE")
    print("=" * 70)
    print()

    # =============================================================================
    # GAME SESSIONS - Active game instances
    # =============================================================================

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS game_sessions (
            game_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_name TEXT NOT NULL,
            game_type TEXT DEFAULT 'dnd',  -- 'dnd', 'pvp', 'coop'
            creator_user_id INTEGER NOT NULL,

            -- State
            status TEXT DEFAULT 'active',  -- 'active', 'paused', 'completed'
            current_turn INTEGER DEFAULT 1,
            turn_player_id INTEGER,  -- Whose turn is it?

            -- Configuration
            max_players INTEGER DEFAULT 8,
            allow_mobile_commanders BOOLEAN DEFAULT 1,
            require_phone_verification BOOLEAN DEFAULT 0,

            -- AI Configuration
            dungeon_master_ai TEXT DEFAULT 'soulfra',  -- Which AI persona is DM
            enable_ai_judging BOOLEAN DEFAULT 1,

            -- Timestamps
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP,
            last_action_at TIMESTAMP,

            FOREIGN KEY (creator_user_id) REFERENCES users(id)
        )
    ''')
    print("✅ Created table: game_sessions")

    # =============================================================================
    # GAME STATE - Current world state (provably fair)
    # =============================================================================

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS game_state (
            state_id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id INTEGER NOT NULL,
            turn_number INTEGER NOT NULL,

            -- State Data (JSON)
            board_state TEXT,  -- JSON: World map, territories, resources
            player_positions TEXT,  -- JSON: {user_id: {platform: 'roblox', x: 50, y: 50}}
            active_effects TEXT,  -- JSON: Spells, buffs, debuffs currently active

            -- Verification
            state_hash TEXT NOT NULL,  -- SHA-256 of entire state
            verified_by_network TEXT,  -- Which neural network verified this
            verification_confidence REAL,  -- AI confidence score (0-1)
            proof_hash TEXT,  -- Zero-knowledge proof of state transition

            -- Timestamps
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_current BOOLEAN DEFAULT 1,  -- Only one current state per game

            FOREIGN KEY (game_id) REFERENCES game_sessions(game_id),
            UNIQUE(game_id, turn_number)
        )
    ''')
    print("✅ Created table: game_state")

    # Add index for faster lookups
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_game_state_current
        ON game_state(game_id, is_current)
    ''')

    # =============================================================================
    # GAME ACTIONS - Turn-by-turn log (immutable history)
    # =============================================================================

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS game_actions (
            action_id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id INTEGER NOT NULL,
            turn_number INTEGER NOT NULL,

            -- Player Info
            player_user_id INTEGER NOT NULL,
            player_platform TEXT NOT NULL,  -- 'roblox', 'minecraft', 'mobile'
            soul_pack_snapshot TEXT,  -- JSON: Player's Soul at time of action

            -- Action Details
            action_type TEXT NOT NULL,  -- 'move', 'attack', 'cast_spell', 'build', etc.
            action_data TEXT,  -- JSON: Action-specific parameters
            target_user_id INTEGER,  -- If action targets another player

            -- AI Judgment
            judged_by_ai TEXT,  -- 'calriven', 'deathtodata', 'theauditor', 'soulfra'
            ai_verdict TEXT,  -- 'success', 'failure', 'partial'
            ai_reasoning TEXT,  -- Why AI made this decision
            ai_confidence REAL,  -- Confidence score (0-1)

            -- Effects
            state_before_hash TEXT NOT NULL,
            state_after_hash TEXT NOT NULL,
            changes_applied TEXT,  -- JSON: What changed in world state

            -- Verification
            action_hash TEXT NOT NULL,  -- SHA-256 of action
            verified BOOLEAN DEFAULT 0,
            verification_proof TEXT,  -- Neural network proof

            -- Timestamps
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_at TIMESTAMP,

            FOREIGN KEY (game_id) REFERENCES game_sessions(game_id),
            FOREIGN KEY (player_user_id) REFERENCES users(id)
        )
    ''')
    print("✅ Created table: game_actions")

    # Add indices
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_game_actions_game
        ON game_actions(game_id, turn_number)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_game_actions_player
        ON game_actions(player_user_id)
    ''')

    # =============================================================================
    # CROSS PLATFORM PLAYERS - Who's playing where
    # =============================================================================

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cross_platform_players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,

            -- Platform Presence
            roblox_active BOOLEAN DEFAULT 0,
            minecraft_active BOOLEAN DEFAULT 0,
            mobile_active BOOLEAN DEFAULT 0,
            web_active BOOLEAN DEFAULT 0,

            -- Role
            player_role TEXT DEFAULT 'player',  -- 'player', 'commander', 'spectator'
            team_id INTEGER,  -- For team-based games

            -- Status
            is_online BOOLEAN DEFAULT 1,
            last_action_at TIMESTAMP,

            -- Soul Reference
            soul_pack_id TEXT,  -- Reference to compiled Soul Pack
            character_stats TEXT,  -- JSON: Game-specific stats derived from Soul

            -- Timestamps
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            left_at TIMESTAMP,

            FOREIGN KEY (game_id) REFERENCES game_sessions(game_id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(game_id, user_id)
        )
    ''')
    print("✅ Created table: cross_platform_players")

    # =============================================================================
    # VERIFIED PROOFS - Neural network validations
    # =============================================================================

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS verified_proofs (
            proof_id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id INTEGER NOT NULL,
            action_id INTEGER NOT NULL,

            -- Proof Data
            proof_type TEXT NOT NULL,  -- 'state_transition', 'action_valid', 'random_fair'
            proof_hash TEXT NOT NULL UNIQUE,

            -- Neural Network Info
            network_name TEXT NOT NULL,  -- 'game_state_validator'
            network_weights_hash TEXT NOT NULL,  -- Hash of network weights (reproducible!)

            -- Inputs/Outputs
            input_vector TEXT,  -- JSON: What went into neural net
            output_vector TEXT,  -- JSON: What came out
            confidence_score REAL,

            -- Verification
            is_valid BOOLEAN NOT NULL,
            can_be_reproduced BOOLEAN DEFAULT 1,  -- Anyone can verify

            -- Timestamps
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (game_id) REFERENCES game_sessions(game_id),
            FOREIGN KEY (action_id) REFERENCES game_actions(action_id)
        )
    ''')
    print("✅ Created table: verified_proofs")

    # Add index
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_verified_proofs_action
        ON verified_proofs(action_id)
    ''')

    # =============================================================================
    # QR GAME PORTALS - Scan to join games
    # =============================================================================

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS qr_game_portals (
            portal_id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id INTEGER NOT NULL,

            -- QR Code Data
            qr_code_data TEXT NOT NULL UNIQUE,  -- The actual QR payload
            qr_code_image_path TEXT,  -- Path to generated QR image

            -- Portal Config
            portal_type TEXT DEFAULT 'entrance',  -- 'entrance', 'exit', 'teleport'
            destination TEXT,  -- Where this portal leads
            requires_verification BOOLEAN DEFAULT 0,
            requires_soul_level INTEGER DEFAULT 1,

            -- Usage
            max_uses INTEGER DEFAULT -1,  -- -1 = unlimited
            current_uses INTEGER DEFAULT 0,

            -- Status
            is_active BOOLEAN DEFAULT 1,
            expires_at TIMESTAMP,

            -- Timestamps
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_used_at TIMESTAMP,

            FOREIGN KEY (game_id) REFERENCES game_sessions(game_id)
        )
    ''')
    print("✅ Created table: qr_game_portals")

    conn.commit()

    # =============================================================================
    # Create initial test game
    # =============================================================================

    print()
    print("🎯 Creating test game session...")

    # Get admin user (or create test user)
    cursor.execute('SELECT id FROM users WHERE is_admin = 1 LIMIT 1')
    admin = cursor.fetchone()

    if not admin:
        # Use first available user
        cursor.execute('SELECT id FROM users LIMIT 1')
        admin = cursor.fetchone()

    if not admin:
        # Create test user
        print("   Creating test user...")
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, is_admin)
            VALUES (?, ?, ?, ?)
        ''', ('admin', 'admin@soulfra.local', 'testpass', 1))
        conn.commit()
        admin_id = cursor.lastrowid
        print(f"   ✅ Created admin user (ID: {admin_id})")
    else:
        admin_id = admin[0]

    if admin_id:
        cursor.execute('''
            INSERT INTO game_sessions (
                session_name, game_type, creator_user_id,
                dungeon_master_ai, enable_ai_judging
            ) VALUES (?, ?, ?, ?, ?)
        ''', (
            'Cringeproof D&D Campaign #1',
            'dnd',
            admin_id,
            'soulfra',
            1
        ))

        game_id = cursor.lastrowid

        # Create initial game state
        import json
        import hashlib

        initial_state = {
            'world_map': {
                'size': [100, 100],
                'territories': [],
                'resources': []
            },
            'active_players': [],
            'turn': 1
        }

        state_json = json.dumps(initial_state, sort_keys=True)
        state_hash = hashlib.sha256(state_json.encode()).hexdigest()

        cursor.execute('''
            INSERT INTO game_state (
                game_id, turn_number, board_state, state_hash,
                verified_by_network, is_current
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (game_id, 1, state_json, state_hash, 'game_state_validator', 1))

        print(f"   ✅ Created game: {game_id}")
        print(f"   ✅ Initial state hash: {state_hash[:16]}...")

    conn.commit()
    conn.close()

    print()
    print("=" * 70)
    print("✅ GAME DATABASE INITIALIZED")
    print("=" * 70)
    print()
    print("Tables created:")
    print("  - game_sessions: Active game instances")
    print("  - game_state: World state (provable, hashed)")
    print("  - game_actions: Turn log (immutable)")
    print("  - cross_platform_players: Player presence tracking")
    print("  - verified_proofs: Neural network validations")
    print("  - qr_game_portals: Scan-to-join portals")
    print()
    print("Next steps:")
    print("  1. Run: python3 game_orchestrator.py")
    print("  2. Test: python3 test_cross_platform_game.py")
    print()


if __name__ == '__main__':
    init_game_tables()
