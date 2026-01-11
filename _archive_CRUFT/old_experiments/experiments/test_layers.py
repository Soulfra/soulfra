#!/usr/bin/env python3
"""
Test 7-Layer Architecture

Run with: python3 test_layers.py

This shows HOW to debug "which layer is broken?"
Each test is independent - if test_layer_3 fails,
you know the bug is in feature extraction.
"""

import sys
from layers import (
    fetch_posts_layer,
    serialize_posts_layer,
    extract_features_layer,
    predict_layer,
    build_template_context_layer,
    full_pipeline
)


def print_test(name, passed):
    """Print test result"""
    symbol = "✓" if passed else "✗"
    status = "PASS" if passed else "FAIL"
    print(f"{symbol} {name}: {status}")
    return passed


def test_layer_1_database():
    """Test Layer 1: Database queries work"""
    try:
        # Test 'new' sorting
        rows = fetch_posts_layer(sort='new', limit=3)
        assert len(rows) <= 3, "Should return <= 3 posts"
        if len(rows) > 0:
            assert 'title' in rows[0].keys(), "Should have 'title' field"

        # Test 'top' sorting
        rows_top = fetch_posts_layer(sort='top', limit=3)
        assert len(rows_top) <= 3, "Should return <= 3 posts"

        # Test 'hot' sorting
        rows_hot = fetch_posts_layer(sort='hot', limit=3)
        assert len(rows_hot) <= 3, "Should return <= 3 posts"

        return print_test("Layer 1 (Database)", True)

    except Exception as e:
        print(f"   Error: {e}")
        return print_test("Layer 1 (Database)", False)


def test_layer_2_serialization():
    """Test Layer 2: Row → dict conversion"""
    try:
        # Get Row objects from Layer 1
        rows = fetch_posts_layer(sort='new', limit=1)

        # Convert to dicts (Layer 2)
        posts = serialize_posts_layer(rows)

        # Test: Should be dict, not Row
        assert isinstance(posts[0], dict), "Should be dict"

        # Test: Should be writable (not read-only like Row)
        posts[0]['test_field'] = 'writable'
        assert posts[0]['test_field'] == 'writable', "Should be writable"

        return print_test("Layer 2 (Serialization)", True)

    except Exception as e:
        print(f"   Error: {e}")
        return print_test("Layer 2 (Serialization)", False)


def test_layer_3_features():
    """Test Layer 3: Feature extraction"""
    try:
        # Create mock post data
        mock_posts = [{
            'id': 1,
            'title': 'Test Post',
            'content': '<h1>Title</h1><p>Test content with <strong>bold</strong></p><img src="test.png"><code>code block</code>',
            'excerpt': None
        }]

        # Run Layer 3
        posts = extract_features_layer(mock_posts)

        # Test: Should have thumbnail
        assert 'thumbnail' in posts[0], "Should extract thumbnail"
        assert posts[0]['thumbnail'] == 'test.png', "Should extract correct image"

        # Test: Should have preview
        assert 'preview' in posts[0], "Should have preview"
        assert len(posts[0]['preview']) > 0, "Preview should not be empty"

        # Test: Should have binary features
        assert 'has_code' in posts[0], "Should have has_code"
        assert posts[0]['has_code'] == 1, "Should detect code block"

        assert 'has_images' in posts[0], "Should have has_images"
        assert posts[0]['has_images'] == 1, "Should count 1 image"

        assert 'length_bucket' in posts[0], "Should have length_bucket"

        return print_test("Layer 3 (Features)", True)

    except Exception as e:
        print(f"   Error: {e}")
        return print_test("Layer 3 (Features)", False)


def test_layer_4_predictions():
    """Test Layer 4: Neural network predictions"""
    try:
        # Create mock post with features
        mock_posts = [{
            'id': 1,
            'title': 'Test',
            'content': 'test',
            'has_code': 1,
            'has_images': 0,
            'length_bucket': 1,
            'word_vector': None
        }]

        # Run Layer 4 (no networks loaded)
        posts = predict_layer(mock_posts, networks=None)

        # Test: Should have predictions field
        assert 'predictions' in posts[0], "Should have predictions"

        # Test: Should be None when no networks
        assert posts[0]['predictions'] is None, "Should be None when no networks"

        return print_test("Layer 4 (Predictions)", True)

    except Exception as e:
        print(f"   Error: {e}")
        return print_test("Layer 4 (Predictions)", False)


def test_layer_5_context():
    """Test Layer 5: Template context building"""
    try:
        # Mock posts
        mock_posts = [{'id': 1, 'title': 'Test'}]

        # Run Layer 5
        context = build_template_context_layer(
            mock_posts,
            sort='top',
            custom_var='test_value'
        )

        # Test: Should have posts
        assert 'posts' in context, "Should have posts"
        assert len(context['posts']) == 1, "Should have 1 post"

        # Test: Should have sort
        assert 'sort' in context, "Should have sort"
        assert context['sort'] == 'top', "Should be 'top'"

        # Test: Should have custom vars
        assert 'custom_var' in context, "Should have custom_var"
        assert context['custom_var'] == 'test_value', "Should pass through custom vars"

        return print_test("Layer 5 (Context)", True)

    except Exception as e:
        print(f"   Error: {e}")
        return print_test("Layer 5 (Context)", False)


def test_full_pipeline():
    """Test full 7-layer pipeline (integration test)"""
    try:
        # Run full pipeline (no render function = return context)
        context = full_pipeline(
            sort='new',
            limit=5,
            networks=None,
            render_func=None  # Skip rendering, just get context
        )

        # Test: Should have posts
        assert 'posts' in context, "Should have posts"
        assert len(context['posts']) <= 5, "Should have <= 5 posts"

        # Test: Posts should have all features from Layer 3
        if len(context['posts']) > 0:
            post = context['posts'][0]
            assert 'thumbnail' in post, "Should have thumbnail from Layer 3"
            assert 'preview' in post, "Should have preview from Layer 3"
            assert 'has_code' in post, "Should have has_code from Layer 3"
            assert 'has_images' in post, "Should have has_images from Layer 3"
            assert 'predictions' in post, "Should have predictions from Layer 4"

        return print_test("Full Pipeline (Integration)", True)

    except Exception as e:
        print(f"   Error: {e}")
        return print_test("Full Pipeline (Integration)", False)


def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing 7-Layer Architecture")
    print("=" * 60)
    print()

    results = []

    print("Layer-by-layer tests:")
    results.append(test_layer_1_database())
    results.append(test_layer_2_serialization())
    results.append(test_layer_3_features())
    results.append(test_layer_4_predictions())
    results.append(test_layer_5_context())

    print()
    print("Integration test:")
    results.append(test_full_pipeline())

    print()
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"✅ ALL TESTS PASSED ({passed}/{total})")
        print()
        print("Architecture is solid. Each layer works independently.")
        print("If a bug appears, run this to find which layer broke.")
        return 0
    else:
        print(f"❌ SOME TESTS FAILED ({passed}/{total})")
        print()
        print("Failed tests show which layer has the bug.")
        print("Fix that layer, re-run tests.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
