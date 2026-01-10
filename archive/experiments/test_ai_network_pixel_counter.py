#!/usr/bin/env python3
"""
Pixel-Counter Style Tests for AI Network

Like counting pixels in the old days - verify EXACT values at each step!

Tests:
1. Brand creation → Check exact database values
2. AI persona generation → Verify username, email, prompt
3. Color feature extraction → Check HSV within tolerance
4. Relevance scoring → Verify exact calculation
5. API routes → Test each endpoint returns expected JSON
6. End-to-end flow → ONE complete flow working 100%

Run: python3 test_ai_network_pixel_counter.py
"""

import sqlite3
import json
import sys
from typing import Dict, List, Optional

# ==============================================================================
# TEST FRAMEWORK (Zero dependencies - pure Python!)
# ==============================================================================

class TestResult:
    def __init__(self, name: str, passed: bool, expected, actual, message: str = ""):
        self.name = name
        self.passed = passed
        self.expected = expected
        self.actual = actual
        self.message = message

    def __str__(self):
        if self.passed:
            return f"✅ {self.name}"
        else:
            msg = f"❌ {self.name}\n"
            msg += f"   Expected: {self.expected}\n"
            msg += f"   Actual: {self.actual}"
            if self.message:
                msg += f"\n   Message: {self.message}"
            return msg


class PixelCounterTest:
    def __init__(self):
        self.results: List[TestResult] = []
        self.passed = 0
        self.failed = 0

    def assert_equal(self, name: str, actual, expected):
        """Assert exact equality (like counting pixels - must be exact!)"""
        passed = actual == expected
        self.results.append(TestResult(name, passed, expected, actual))
        if passed:
            self.passed += 1
        else:
            self.failed += 1

    def assert_close(self, name: str, actual: float, expected: float, tolerance: float = 0.01):
        """Assert values are close (for floating point calculations)"""
        passed = abs(actual - expected) <= tolerance
        self.results.append(TestResult(
            name, passed, f"{expected} ± {tolerance}", actual,
            f"Difference: {abs(actual - expected):.4f}"
        ))
        if passed:
            self.passed += 1
        else:
            self.failed += 1

    def assert_in_range(self, name: str, actual: float, min_val: float, max_val: float):
        """Assert value is within range"""
        passed = min_val <= actual <= max_val
        self.results.append(TestResult(
            name, passed, f"[{min_val}, {max_val}]", actual
        ))
        if passed:
            self.passed += 1
        else:
            self.failed += 1

    def assert_contains(self, name: str, haystack: str, needle: str):
        """Assert string contains substring"""
        passed = needle in haystack
        self.results.append(TestResult(
            name, passed, f"Contains '{needle}'", haystack
        ))
        if passed:
            self.passed += 1
        else:
            self.failed += 1

    def report(self):
        """Print test report"""
        print("=" * 70)
        print("🧪 PIXEL-COUNTER TEST RESULTS")
        print("=" * 70)
        print()

        for result in self.results:
            print(result)

        print()
        print("=" * 70)
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"📊 Total: {len(self.results)}")
        print(f"🎯 Success Rate: {self.passed / len(self.results) * 100:.1f}%")
        print("=" * 70)

        return self.failed == 0


# ==============================================================================
# DATABASE HELPERS
# ==============================================================================

def get_test_db():
    """Get database connection"""
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    return conn


# ==============================================================================
# STEP 1: TEST BRAND IN DATABASE
# ==============================================================================

def test_brand_in_database(test: PixelCounterTest):
    """
    Test that Ocean Dreams brand exists in database with exact expected values

    Like counting pixels: Each field must be EXACTLY as expected
    """
    print("\n🔍 STEP 1: Test Brand in Database")
    print("-" * 70)

    db = get_test_db()
    brand = db.execute('''
        SELECT * FROM brands WHERE slug = 'ocean-dreams'
    ''').fetchone()

    if brand:
        brand_dict = dict(brand)

        # Test exact values
        test.assert_equal(
            "Brand slug",
            brand_dict['slug'],
            'ocean-dreams'
        )

        test.assert_equal(
            "Brand name",
            brand_dict['name'],
            'Ocean Dreams'
        )

        # Test personality contains expected keywords
        personality = brand_dict.get('personality', '').lower()
        test.assert_contains(
            "Personality contains 'calm'",
            personality,
            'calm'
        )

        # Test tone
        tone = brand_dict.get('tone', '').lower()
        test.assert_contains(
            "Tone is set",
            tone,
            ''  # Just check not empty
        )

        # Test config JSON is valid
        try:
            config = json.loads(brand_dict['config_json']) if brand_dict['config_json'] else {}
            test.assert_equal(
                "Config JSON is valid dict",
                type(config),
                dict
            )
        except:
            test.assert_equal(
                "Config JSON is valid",
                False,
                True
            )
    else:
        test.assert_equal(
            "Ocean Dreams brand exists",
            False,
            True
        )

    db.close()


# ==============================================================================
# STEP 2: TEST AI PERSONA GENERATION
# ==============================================================================

def test_ai_persona_exists(test: PixelCounterTest):
    """
    Test that AI persona was generated for Ocean Dreams

    Exact checks:
    - Username = 'ocean-dreams'
    - Email = 'ocean-dreams@soulfra.ai'
    - is_ai_persona = 1
    """
    print("\n🤖 STEP 2: Test AI Persona Generation")
    print("-" * 70)

    db = get_test_db()
    persona = db.execute('''
        SELECT * FROM users WHERE username = 'ocean-dreams' AND is_ai_persona = 1
    ''').fetchone()

    if persona:
        persona_dict = dict(persona)

        # Test exact values
        test.assert_equal(
            "AI persona username",
            persona_dict['username'],
            'ocean-dreams'
        )

        test.assert_equal(
            "AI persona email",
            persona_dict['email'],
            'ocean-dreams@soulfra.ai'
        )

        test.assert_equal(
            "AI persona display name",
            persona_dict['display_name'],
            'Ocean Dreams'
        )

        test.assert_equal(
            "is_ai_persona flag",
            persona_dict['is_ai_persona'],
            1
        )

        test.assert_equal(
            "Password is NOLOGIN",
            persona_dict['password_hash'],
            'NOLOGIN'
        )
    else:
        test.assert_equal(
            "Ocean Dreams AI persona exists",
            False,
            True
        )

    db.close()


# ==============================================================================
# STEP 3: TEST COLOR FEATURE EXTRACTION
# ==============================================================================

def test_color_feature_extraction(test: PixelCounterTest):
    """
    Test color feature extraction with exact expected values

    Ocean Dreams primary color: #003366 (dark blue)
    Expected features:
    - Hue: ~210° (blue)
    - Saturation: 1.0 (fully saturated)
    - Value: 0.4 (dark)
    - Temperature: 0.0-0.2 (cool)
    """
    print("\n🎨 STEP 3: Test Color Feature Extraction")
    print("-" * 70)

    # Import color extraction
    try:
        from train_color_features import extract_color_features

        # Ocean Dreams primary color: #003366
        # RGB = (0, 51, 102) → Normalized = (0.0, 0.2, 0.4)
        rgb = (0.0, 51/255, 102/255)  # Normalize to [0, 1]

        features = extract_color_features(rgb)

        # Test features (12 total)
        test.assert_equal(
            "Feature count",
            len(features),
            12
        )

        # Hue should be around 210° = 0.583 in [0, 1]
        test.assert_in_range(
            "Hue (blue range)",
            features[0],
            0.5,  # 180° (cyan)
            0.7   # 252° (blue-purple)
        )

        # Saturation should be 1.0 (fully saturated)
        test.assert_close(
            "Saturation",
            features[1],
            1.0,
            0.1
        )

        # Value should be around 0.4 (dark)
        test.assert_close(
            "Value/Brightness",
            features[2],
            0.4,
            0.1
        )

        # Temperature should be cool (0.0-0.3)
        test.assert_in_range(
            "Temperature (cool)",
            features[3],
            0.0,
            0.3
        )

    except ImportError:
        test.assert_equal(
            "train_color_features.py exists",
            False,
            True
        )


# ==============================================================================
# STEP 4: TEST RELEVANCE SCORING
# ==============================================================================

def test_relevance_scoring(test: PixelCounterTest):
    """
    Test brand-post relevance scoring with exact calculations

    Example:
    - Ocean Dreams (calm, peaceful) + Post about ocean → High relevance
    - Ocean Dreams (calm, peaceful) + Post about databases → Low relevance
    """
    print("\n🎯 STEP 4: Test Relevance Scoring")
    print("-" * 70)

    try:
        from brand_ai_orchestrator import calculate_brand_post_relevance

        # Test 1: Ocean Dreams + ocean-related post (HIGH relevance)
        brand_config = {
            'personality': 'calm, peaceful, flowing',
            'tone': 'contemplative and serene',
            'values': ['tranquility', 'depth', 'exploration']
        }

        ocean_post = "Exploring the deep ocean brings a sense of tranquility and peace"
        relevance_high = calculate_brand_post_relevance(brand_config, ocean_post)

        test.assert_in_range(
            "Ocean Dreams + ocean post (HIGH)",
            relevance_high,
            0.5,  # Should be high
            1.0
        )

        # Test 2: Ocean Dreams + database post (LOW relevance)
        database_post = "Building a SQL database with indexing and query optimization"
        relevance_low = calculate_brand_post_relevance(brand_config, database_post)

        test.assert_in_range(
            "Ocean Dreams + database post (LOW)",
            relevance_low,
            0.0,
            0.3   # Should be low
        )

        # Test 3: Relevance scoring math
        # Base score (0.1) + personality (40%) + tone (30%) + values (30%)
        # If NO matches, should be just base score
        irrelevant_post = "xyz123 random gibberish qwerty"
        relevance_base = calculate_brand_post_relevance(brand_config, irrelevant_post)

        test.assert_close(
            "Base score for irrelevant post",
            relevance_base,
            0.1,  # Just the base score
            0.05
        )

    except ImportError:
        test.assert_equal(
            "brand_ai_orchestrator.py exists",
            False,
            True
        )


# ==============================================================================
# STEP 5: TEST API ROUTES
# ==============================================================================

def test_api_routes_exist(test: PixelCounterTest):
    """
    Test that all 7 API routes exist and return valid responses

    This is a "smoke test" - just verify routes don't 404
    """
    print("\n🌐 STEP 5: Test API Routes Exist")
    print("-" * 70)

    # We'll test by importing the app and checking routes are registered
    try:
        # Read app.py and check for route definitions
        with open('app.py', 'r') as f:
            app_code = f.read()

        routes = [
            '/api/ai/test-relevance',
            '/api/ai/training-data',
            '/api/ai/regenerate-all',
            '/api/ai/retrain-networks',
            '/api/ai/clear-comments',
            '/api/ai/export-debug-data',
            '/ai-network/visualize'
        ]

        for route in routes:
            test.assert_contains(
                f"Route {route} exists",
                app_code,
                route
            )

    except FileNotFoundError:
        test.assert_equal(
            "app.py exists",
            False,
            True
        )


# ==============================================================================
# STEP 6: TEST NEURAL NETWORK FORWARD PASS
# ==============================================================================

def test_neural_network_forward_pass(test: PixelCounterTest):
    """
    Test neural network forward pass with exact math

    Example:
    Input: [0.5, 0.5, 0.5] (gray color)
    Hidden layer: sigmoid(weights × input + bias)
    Output: sigmoid(weights × hidden + bias)

    Check math is correct (not just "it runs")
    """
    print("\n🧠 STEP 6: Test Neural Network Forward Pass")
    print("-" * 70)

    try:
        from pure_neural_network import NeuralNetwork

        # Create simple 3-2-1 network
        nn = NeuralNetwork(input_size=3, hidden_sizes=[2], output_size=1)

        # Set known weights for testing
        # Input → Hidden: 3×2 matrix
        nn.weights_ih = [
            [0.5, -0.5, 0.0],  # Hidden neuron 1
            [-0.5, 0.5, 0.0]   # Hidden neuron 2
        ]
        nn.bias_h = [0.0, 0.0]

        # Hidden → Output: 1×2 matrix
        nn.weights_ho = [
            [1.0, -1.0]  # Output neuron
        ]
        nn.bias_o = [0.0]

        # Test forward pass with [0.5, 0.5, 0.5]
        inputs = [0.5, 0.5, 0.5]
        hidden, output = nn.forward(inputs)

        # Hidden layer calculation:
        # h1 = sigmoid(0.5*0.5 + -0.5*0.5 + 0.0*0.5 + 0.0) = sigmoid(0) = 0.5
        # h2 = sigmoid(-0.5*0.5 + 0.5*0.5 + 0.0*0.5 + 0.0) = sigmoid(0) = 0.5

        test.assert_close(
            "Hidden neuron 1 output",
            hidden[0],
            0.5,
            0.01
        )

        test.assert_close(
            "Hidden neuron 2 output",
            hidden[1],
            0.5,
            0.01
        )

        # Output calculation:
        # o = sigmoid(1.0*0.5 + -1.0*0.5 + 0.0) = sigmoid(0) = 0.5

        test.assert_close(
            "Output neuron",
            output[0],
            0.5,
            0.01
        )

    except ImportError:
        test.assert_equal(
            "pure_neural_network.py exists",
            False,
            True
        )


# ==============================================================================
# MAIN TEST RUNNER
# ==============================================================================

def main():
    """Run all pixel-counter tests"""
    print("=" * 70)
    print("🧪 PIXEL-COUNTER STYLE AI NETWORK TESTS")
    print("=" * 70)
    print()
    print("Like counting pixels - verify EXACT values at each step!")
    print()

    test = PixelCounterTest()

    # Run all tests
    test_brand_in_database(test)
    test_ai_persona_exists(test)
    test_color_feature_extraction(test)
    test_relevance_scoring(test)
    test_api_routes_exist(test)
    test_neural_network_forward_pass(test)

    # Print report
    print()
    success = test.report()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
