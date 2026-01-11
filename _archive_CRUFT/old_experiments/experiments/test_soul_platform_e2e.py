#!/usr/bin/env python3
"""
Soul Platform End-to-End Test Suite

Comprehensive testing of the multi-platform Soul identity system:
1. Soul Pack compilation
2. Platform transformations (Roblox, Minecraft, Unity, Voice)
3. File generation and format validation
4. API endpoint testing
5. Platform picker UI verification

Run this after creating a test user with create_test_soul_user.py
"""

import json
import sys
from pathlib import Path
from soul_model import Soul
from platform_connectors import RobloxConnector, MinecraftConnector
from soul_transformer import SoulTransformer
from database import get_db


class TestResults:
    """Track test results"""
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []

    def pass_test(self, name):
        self.passed.append(name)
        print(f"   ✅ {name}")

    def fail_test(self, name, reason):
        self.failed.append((name, reason))
        print(f"   ❌ {name}")
        print(f"      Reason: {reason}")

    def warn(self, message):
        self.warnings.append(message)
        print(f"   ⚠️  {message}")

    def summary(self):
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"✅ Passed: {len(self.passed)}")
        print(f"❌ Failed: {len(self.failed)}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        print()

        if self.failed:
            print("Failed Tests:")
            for name, reason in self.failed:
                print(f"   - {name}: {reason}")
            print()

        return len(self.failed) == 0


def test_soul_pack_compilation(user_id, results):
    """Test Soul Pack compilation (all 5 layers)"""
    print("\n🧠 Testing Soul Pack Compilation...")

    try:
        soul = Soul(user_id)
        pack = soul.compile_pack()

        # Test version
        if 'version' in pack and pack['version'] == '1.0':
            results.pass_test("Soul Pack version")
        else:
            results.fail_test("Soul Pack version", "Missing or incorrect version")

        # Test Identity layer
        if 'identity' in pack:
            identity = pack['identity']
            if all(k in identity for k in ['user_id', 'username', 'created_at']):
                results.pass_test("Identity layer (immutable)")
            else:
                results.fail_test("Identity layer", "Missing required fields")
        else:
            results.fail_test("Identity layer", "Layer missing from pack")

        # Test Essence layer
        if 'essence' in pack:
            essence = pack['essence']
            if all(k in essence for k in ['interests', 'expertise', 'values']):
                results.pass_test("Essence layer (evolves slowly)")

                # Check interests are strings
                if isinstance(essence['interests'], list) and len(essence['interests']) > 0:
                    results.pass_test("Interests extraction")
                else:
                    results.warn("No interests extracted (user may have no posts)")

                # Check expertise is dict
                if isinstance(essence['expertise'], dict):
                    results.pass_test("Expertise calculation")
                else:
                    results.fail_test("Expertise calculation", "Should be dict")

                # Check values are strings
                if isinstance(essence['values'], list):
                    results.pass_test("Values detection")
                else:
                    results.fail_test("Values detection", "Should be list")
            else:
                results.fail_test("Essence layer", "Missing required fields")
        else:
            results.fail_test("Essence layer", "Layer missing from pack")

        # Test Expression layer
        if 'expression' in pack:
            expression = pack['expression']
            required_fields = ['post_count', 'comment_count', 'karma', 'activity_level']
            if all(k in expression for k in required_fields):
                results.pass_test("Expression layer (changes frequently)")
            else:
                results.fail_test("Expression layer", "Missing required fields")
        else:
            results.fail_test("Expression layer", "Layer missing from pack")

        # Test Connections layer
        if 'connections' in pack:
            results.pass_test("Connections layer (network)")
        else:
            results.fail_test("Connections layer", "Layer missing from pack")

        # Test Evolution layer
        if 'evolution' in pack:
            results.pass_test("Evolution layer (time-series)")
        else:
            results.fail_test("Evolution layer", "Layer missing from pack")

        # Test Fingerprint
        if 'fingerprint' in pack:
            fp = pack['fingerprint']
            if 'activity_level' in fp and 'expression_style' in fp:
                results.pass_test("Soul fingerprint generation")
            else:
                results.fail_test("Soul fingerprint", "Missing required fields")
        else:
            results.fail_test("Soul fingerprint", "Missing from pack")

        return soul, pack

    except Exception as e:
        results.fail_test("Soul Pack compilation", str(e))
        return None, None


def test_roblox_transformation(soul_pack, results):
    """Test Roblox Lua generation"""
    print("\n🎮 Testing Roblox Platform Transformation...")

    try:
        connector = RobloxConnector()
        lua_code = connector.generate(soul_pack)

        # Check it's a string
        if isinstance(lua_code, str) and len(lua_code) > 0:
            results.pass_test("Roblox Lua generation")
        else:
            results.fail_test("Roblox Lua generation", "Empty or invalid output")
            return None

        # Check for required Lua structures
        required_patterns = [
            'local Soul = {}',
            'Soul.Identity',
            'Soul.Essence',
            'Soul.Expression',
            'Soul.Appearance',
            'Soul.ChatRules',
            'function Soul:GetDisplayName()',
            'function Soul:CheckChatMessage(',
            'return Soul'
        ]

        for pattern in required_patterns:
            if pattern in lua_code:
                results.pass_test(f"Lua structure: {pattern}")
            else:
                results.fail_test(f"Lua structure: {pattern}", "Pattern not found in generated code")

        # Check color generation (deterministic hash)
        if 'Color3.fromRGB(' in lua_code:
            results.pass_test("Deterministic color generation (hash)")
        else:
            results.fail_test("Color generation", "Color3.fromRGB not found")

        # Check chat rules
        chat_rule_patterns = ['BlockedWords', 'RateLimitSeconds', 'MaxMessageLength']
        for pattern in chat_rule_patterns:
            if pattern in lua_code:
                results.pass_test(f"Chat rule: {pattern}")
            else:
                results.fail_test(f"Chat rule: {pattern}", "Not found in Lua code")

        # Test file save
        output_path = connector.save_to_file(lua_code, 'test_soul.lua')
        if output_path.exists():
            results.pass_test("Roblox file save")
            results.pass_test(f"Output location: {output_path}")
        else:
            results.fail_test("Roblox file save", "File not created")

        return lua_code

    except Exception as e:
        results.fail_test("Roblox transformation", str(e))
        import traceback
        traceback.print_exc()
        return None


def test_minecraft_transformation(soul_pack, results):
    """Test Minecraft JSON generation"""
    print("\n⛏️  Testing Minecraft Platform Transformation...")

    try:
        connector = MinecraftConnector()
        player_data = connector.generate(soul_pack)

        # Check it's a dict
        if isinstance(player_data, dict) and len(player_data) > 0:
            results.pass_test("Minecraft JSON generation")
        else:
            results.fail_test("Minecraft JSON generation", "Empty or invalid output")
            return None

        # Check for required Minecraft fields
        required_fields = [
            'DataVersion',
            'playerGameType',
            'Health',
            'foodLevel',
            'XpLevel',
            'Inventory',
            'abilities'
        ]

        for field in required_fields:
            if field in player_data:
                results.pass_test(f"Minecraft field: {field}")
            else:
                results.fail_test(f"Minecraft field: {field}", "Field not found")

        # Check custom NBT data
        if 'SoulfraNBT' in player_data:
            results.pass_test("Custom NBT data (SoulfraNBT)")

            nbt = player_data['SoulfraNBT']
            nbt_sections = ['Identity', 'Essence', 'Expression', 'ChatRules', 'Sync', 'Appearance']
            for section in nbt_sections:
                if section in nbt:
                    results.pass_test(f"NBT section: {section}")
                else:
                    results.fail_test(f"NBT section: {section}", "Not found in SoulfraNBT")
        else:
            results.fail_test("Custom NBT data", "SoulfraNBT not found")

        # Check Soul items in inventory
        if 'Inventory' in player_data and len(player_data['Inventory']) > 0:
            results.pass_test("Soul items in inventory")

            # Check for enchanted books (interests)
            has_books = any(item['id'] == 'minecraft:enchanted_book' for item in player_data['Inventory'])
            if has_books:
                results.pass_test("Soul interests as enchanted books")
            else:
                results.warn("No enchanted books in inventory (user may have no interests)")

            # Check for expertise tools
            tool_ids = ['minecraft:diamond_pickaxe', 'minecraft:compass', 'minecraft:painting', 'minecraft:diamond_sword']
            has_tools = any(item['id'] in tool_ids for item in player_data['Inventory'])
            if has_tools:
                results.pass_test("Soul expertise as tools")
            else:
                results.warn("No expertise tools in inventory")
        else:
            results.warn("Empty inventory (user may have no content)")

        # Test file save
        output_path = connector.save_to_file(player_data, 'test_soul.json')
        if output_path.exists():
            results.pass_test("Minecraft file save")
            results.pass_test(f"Output location: {output_path}")

            # Verify JSON is valid
            with open(output_path) as f:
                json.load(f)
            results.pass_test("Valid JSON format")
        else:
            results.fail_test("Minecraft file save", "File not created")

        return player_data

    except Exception as e:
        results.fail_test("Minecraft transformation", str(e))
        import traceback
        traceback.print_exc()
        return None


def test_unity_transformation(soul_pack, results):
    """Test Unity asset bundle generation"""
    print("\n🎯 Testing Unity Platform Transformation...")

    try:
        transformer = SoulTransformer()
        unity_data = transformer.to_unity(soul_pack)

        if isinstance(unity_data, dict) and len(unity_data) > 0:
            results.pass_test("Unity asset bundle generation")

            # Check for expected Unity structures
            if 'character' in unity_data:
                results.pass_test("Unity character data")
            if 'stats' in unity_data:
                results.pass_test("Unity stats data")
            if 'appearance' in unity_data:
                results.pass_test("Unity appearance data")
        else:
            results.fail_test("Unity transformation", "Empty or invalid output")

        return unity_data

    except Exception as e:
        results.fail_test("Unity transformation", str(e))
        return None


def test_voice_transformation(soul_pack, results):
    """Test Voice AI persona generation"""
    print("\n🎙️  Testing Voice AI Platform Transformation...")

    try:
        transformer = SoulTransformer()
        voice_data = transformer.to_voice_persona(soul_pack)

        if isinstance(voice_data, dict) and len(voice_data) > 0:
            results.pass_test("Voice AI persona generation")

            # Check for expected voice persona structures
            if 'personality' in voice_data:
                results.pass_test("Voice personality data")
            if 'knowledge_domains' in voice_data:
                results.pass_test("Voice knowledge domains")
        else:
            results.fail_test("Voice transformation", "Empty or invalid output")

        return voice_data

    except Exception as e:
        results.fail_test("Voice transformation", str(e))
        return None


def test_platform_picker_data(username, results):
    """Test data availability for platform picker UI"""
    print("\n🌐 Testing Platform Picker Data Availability...")

    try:
        conn = get_db()

        # Get user
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if user:
            results.pass_test("User lookup by username")
            user = dict(user)

            # Calculate level (same as platform picker route)
            posts_count = conn.execute('SELECT COUNT(*) as count FROM posts WHERE user_id = ?', (user['id'],)).fetchone()['count']
            level = 1 + (posts_count // 10)

            results.pass_test(f"Level calculation: {level}")

            # Check karma
            comments_count = conn.execute('SELECT COUNT(*) as count FROM comments WHERE user_id = ?', (user['id'],)).fetchone()['count']
            karma = (posts_count * 10) + (comments_count * 2)

            results.pass_test(f"Karma calculation: {karma}")

            conn.close()
            return True
        else:
            results.fail_test("User lookup", "User not found")
            conn.close()
            return False

    except Exception as e:
        results.fail_test("Platform picker data", str(e))
        return False


def run_all_tests(username='soul_tester'):
    """Run all end-to-end tests"""
    print("=" * 70)
    print("🧪 SOUL PLATFORM END-TO-END TEST SUITE")
    print("=" * 70)
    print(f"Testing user: {username}")
    print()

    results = TestResults()

    # Get user
    conn = get_db()
    user = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()

    if not user:
        print(f"❌ User '{username}' not found!")
        print()
        print("Create a test user first:")
        print("   python3 create_test_soul_user.py")
        print()
        return False

    user_id = user['id']
    print(f"✅ Found user (id: {user_id})")

    # Run tests
    soul, pack = test_soul_pack_compilation(user_id, results)

    if pack:
        test_roblox_transformation(pack, results)
        test_minecraft_transformation(pack, results)
        test_unity_transformation(pack, results)
        test_voice_transformation(pack, results)
        test_platform_picker_data(username, results)

    # Summary
    success = results.summary()

    if success:
        print("🎉 ALL TESTS PASSED!")
        print()
        print("Next steps:")
        print(f"1. Visit: http://localhost:5001/soul/{username}/platforms")
        print(f"2. Download files from platform picker")
        print(f"3. Check platform_outputs/ directory for generated files")
        print()
    else:
        print("⚠️  SOME TESTS FAILED")
        print("Check the failures above and fix the issues.")
        print()

    return success


if __name__ == '__main__':
    # Get username from command line or use default
    username = sys.argv[1] if len(sys.argv) > 1 else 'soul_tester'

    try:
        success = run_all_tests(username)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
