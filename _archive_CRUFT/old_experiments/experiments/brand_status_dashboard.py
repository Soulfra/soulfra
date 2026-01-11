#!/usr/bin/env python3
"""
Brand Status Dashboard - Verification & Health Checks

Provides comprehensive status checking for the brand voice ML system:
- Which brands are synced from manifest
- ML model training status
- Brand-post association health
- Test predictions and confidence scores
- System readiness verification

Used by /admin/brand-status route to show visual dashboard.
"""

import json
from datetime import datetime
from collections import defaultdict

from database import get_db
from brand_vocabulary_trainer import (
    load_brand_model_from_db,
    predict_brand,
    get_brand_wordmap
)
from emoji_pattern_analyzer import load_emoji_patterns_from_db


def get_manifest_brands():
    """
    Load brand definitions from themes/manifest.yaml

    Returns:
        dict: {slug: {name, emoji, personality, tone, ...}}
    """
    try:
        import yaml
        with open('themes/manifest.yaml', 'r') as f:
            manifest = yaml.safe_load(f)

        brands = {}
        for slug, data in manifest.get('themes', {}).items():
            brands[slug] = {
                'name': data.get('name', slug),
                'emoji': data.get('emoji', ''),
                'personality': data.get('personality', ''),
                'tone': data.get('tone', ''),
                'tier': data.get('tier', 'unknown'),
                'ship_class': data.get('ship_class', 'unknown')
            }

        return brands
    except Exception as e:
        print(f"Error loading manifest: {e}")
        return {}


def get_database_brands():
    """
    Get all brands from database

    Returns:
        list: [{'slug': ..., 'name': ..., 'id': ..., ...}]
    """
    db = get_db()

    brands = db.execute('''
        SELECT id, slug, name, personality, tone, emoji, config_json
        FROM brands
        ORDER BY name
    ''').fetchall()

    db.close()

    return [dict(brand) for brand in brands]


def get_sync_status():
    """
    Check which brands from manifest are synced to database

    Returns:
        dict: {
            'in_manifest': [slugs],
            'in_database': [slugs],
            'missing_from_db': [slugs],
            'missing_from_manifest': [slugs],
            'synced': [slugs]
        }
    """
    manifest_brands = get_manifest_brands()
    database_brands = get_database_brands()

    manifest_slugs = set(manifest_brands.keys())
    database_slugs = set([b['slug'] for b in database_brands])

    return {
        'in_manifest': list(manifest_slugs),
        'in_database': list(database_slugs),
        'missing_from_db': list(manifest_slugs - database_slugs),
        'missing_from_manifest': list(database_slugs - manifest_slugs),
        'synced': list(manifest_slugs & database_slugs)
    }


def get_brand_post_associations():
    """
    Get brand-post association statistics

    Returns:
        dict: {
            'total_associations': int,
            'valid_associations': int,
            'orphaned_associations': int,
            'brands_with_posts': [{brand_slug, post_count}, ...],
            'posts_per_brand': {brand_slug: count}
        }
    """
    db = get_db()

    # Total associations
    total = db.execute('SELECT COUNT(*) as count FROM brand_posts').fetchone()['count']

    # Valid associations (brand exists)
    valid = db.execute('''
        SELECT COUNT(*) as count
        FROM brand_posts bp
        WHERE bp.brand_id IN (SELECT id FROM brands)
    ''').fetchone()['count']

    # Orphaned (brand doesn't exist)
    orphaned = total - valid

    # Posts per brand
    brand_stats = db.execute('''
        SELECT b.slug, b.name, COUNT(bp.post_id) as post_count
        FROM brands b
        LEFT JOIN brand_posts bp ON b.id = bp.brand_id
        GROUP BY b.id, b.slug, b.name
        ORDER BY post_count DESC
    ''').fetchall()

    db.close()

    brands_with_posts = [dict(row) for row in brand_stats]
    posts_per_brand = {row['slug']: row['post_count'] for row in brand_stats}

    return {
        'total_associations': total,
        'valid_associations': valid,
        'orphaned_associations': orphaned,
        'brands_with_posts': brands_with_posts,
        'posts_per_brand': posts_per_brand
    }


def get_ml_models_status():
    """
    Check which ML models are trained

    Returns:
        dict: {
            'total_models': int,
            'models': [{model_type, trained_on, created_at}, ...],
            'brand_voice_model': {...} or None,
            'emoji_patterns_model': {...} or None
        }
    """
    db = get_db()

    # Get all ML models
    models = db.execute('''
        SELECT model_type, trained_on, created_at,
               length(model_data) as model_size_bytes
        FROM ml_models
        ORDER BY created_at DESC
    ''').fetchall()

    db.close()

    models_list = [dict(model) for model in models]
    total = len(models_list)

    # Load specific models
    brand_voice = load_brand_model_from_db()
    emoji_patterns = load_emoji_patterns_from_db()

    return {
        'total_models': total,
        'models': models_list,
        'brand_voice_model': brand_voice,
        'emoji_patterns_model': emoji_patterns
    }


def get_brand_wordmap_stats(brand_slug):
    """
    Get wordmap statistics for a brand

    Args:
        brand_slug: Brand slug

    Returns:
        dict: {
            'has_wordmap': bool,
            'word_count': int,
            'top_words': [(word, score), ...],
            'sample_words': [words]
        }
    """
    wordmap = get_brand_wordmap(brand_slug)

    if not wordmap:
        return {
            'has_wordmap': False,
            'word_count': 0,
            'top_words': [],
            'sample_words': []
        }

    top_words = sorted(wordmap.items(), key=lambda x: x[1], reverse=True)[:10]
    sample_words = list(wordmap.keys())[:20]

    return {
        'has_wordmap': True,
        'word_count': len(wordmap),
        'top_words': top_words,
        'sample_words': sample_words
    }


def run_test_predictions():
    """
    Run test predictions to verify models work

    Returns:
        list: [{'text': ..., 'predicted_brand': ..., 'confidence': ..., 'correct': ...}, ...]
    """
    # Test cases (text, expected_brand)
    test_cases = [
        ("Technical deep dive into database optimization and caching strategies", "calriven"),
        ("Calm flowing updates streaming peacefully through the system", "ocean-dreams"),
        ("Privacy-first encryption ensuring secure protected user data", "deathtodata"),
        ("Thorough validation and testing of all system components", "theauditor"),
        ("Building a balanced platform with trustworthy foundations", "soulfra"),
        ("Breaking down game mechanics and strategic implementations", "gamebreaker"),
        ("Secure vault architecture with encrypted storage layers", "stellarvault"),
        ("Crafting ship-based systems with forge-like precision", "skyforge"),
    ]

    results = []

    for text, expected in test_cases:
        predicted, confidence = predict_brand(text)

        results.append({
            'text': text,
            'expected_brand': expected,
            'predicted_brand': predicted,
            'confidence': confidence,
            'correct': (predicted == expected) if predicted else False
        })

    return results


def calculate_system_health():
    """
    Calculate overall system health score

    Returns:
        dict: {
            'score': 0-100,
            'status': 'healthy'/'warning'/'error',
            'checks': [{name, passed, message}, ...]
        }
    """
    checks = []
    passed_count = 0

    # Check 1: Manifest brands synced
    sync_status = get_sync_status()
    manifest_count = len(sync_status['in_manifest'])
    synced_count = len(sync_status['synced'])

    if synced_count == manifest_count and manifest_count > 0:
        checks.append({
            'name': 'Brands Synced',
            'passed': True,
            'message': f'{synced_count}/{manifest_count} brands synced from manifest'
        })
        passed_count += 1
    else:
        checks.append({
            'name': 'Brands Synced',
            'passed': False,
            'message': f'Only {synced_count}/{manifest_count} brands synced. Run bootstrap!'
        })

    # Check 2: No orphaned associations
    assoc_stats = get_brand_post_associations()
    if assoc_stats['orphaned_associations'] == 0:
        checks.append({
            'name': 'Associations Clean',
            'passed': True,
            'message': f'{assoc_stats["valid_associations"]} valid associations, 0 orphaned'
        })
        passed_count += 1
    else:
        checks.append({
            'name': 'Associations Clean',
            'passed': False,
            'message': f'{assoc_stats["orphaned_associations"]} orphaned associations found. Run cleanup!'
        })

    # Check 3: Brands have posts
    brands_with_content = sum(1 for count in assoc_stats['posts_per_brand'].values() if count > 0)
    total_brands = len(sync_status['in_database'])

    if brands_with_content >= 2:
        checks.append({
            'name': 'Training Data',
            'passed': True,
            'message': f'{brands_with_content} brands have posts for training'
        })
        passed_count += 1
    else:
        checks.append({
            'name': 'Training Data',
            'passed': False,
            'message': f'Only {brands_with_content} brands have posts. Need at least 2!'
        })

    # Check 4: ML models trained
    ml_status = get_ml_models_status()
    if ml_status['brand_voice_model']:
        checks.append({
            'name': 'Brand Voice Model',
            'passed': True,
            'message': f'Trained on {ml_status["brand_voice_model"]["training_size"]} examples'
        })
        passed_count += 1
    else:
        checks.append({
            'name': 'Brand Voice Model',
            'passed': False,
            'message': 'Not trained. Click "Train Models" in admin!'
        })

    # Check 5: Test predictions work
    if ml_status['brand_voice_model']:
        test_results = run_test_predictions()
        correct_count = sum(1 for r in test_results if r['correct'])
        total_tests = len(test_results)
        accuracy = correct_count / total_tests if total_tests > 0 else 0

        if accuracy > 0.5:
            checks.append({
                'name': 'Prediction Accuracy',
                'passed': True,
                'message': f'{correct_count}/{total_tests} predictions correct ({accuracy:.0%})'
            })
            passed_count += 1
        else:
            checks.append({
                'name': 'Prediction Accuracy',
                'passed': False,
                'message': f'Only {correct_count}/{total_tests} correct. Retrain models!'
            })
    else:
        checks.append({
            'name': 'Prediction Accuracy',
            'passed': False,
            'message': 'Cannot test - no model trained'
        })

    # Calculate score
    total_checks = len(checks)
    score = int((passed_count / total_checks) * 100) if total_checks > 0 else 0

    # Determine status
    if score >= 80:
        status = 'healthy'
    elif score >= 50:
        status = 'warning'
    else:
        status = 'error'

    return {
        'score': score,
        'status': status,
        'checks': checks,
        'passed': passed_count,
        'total': total_checks
    }


def get_full_status():
    """
    Get complete system status for dashboard

    Returns:
        dict: All status data combined
    """
    return {
        'sync_status': get_sync_status(),
        'associations': get_brand_post_associations(),
        'ml_models': get_ml_models_status(),
        'health': calculate_system_health(),
        'test_predictions': run_test_predictions() if load_brand_model_from_db() else [],
        'timestamp': datetime.now().isoformat()
    }


def main():
    """CLI interface"""
    print("=" * 70)
    print("Brand Status Dashboard - System Health Check")
    print("=" * 70)
    print()

    status = get_full_status()
    health = status['health']

    # Health score
    score_icon = "✅" if health['score'] >= 80 else "⚠️" if health['score'] >= 50 else "❌"
    print(f"{score_icon} System Health: {health['score']}/100 ({health['status'].upper()})")
    print()

    # Health checks
    print("Health Checks:")
    for check in health['checks']:
        icon = "✅" if check['passed'] else "❌"
        print(f"  {icon} {check['name']}: {check['message']}")
    print()

    # Sync status
    sync = status['sync_status']
    print(f"📦 Brands:")
    print(f"  Manifest: {len(sync['in_manifest'])} brands defined")
    print(f"  Database: {len(sync['in_database'])} brands synced")
    if sync['missing_from_db']:
        print(f"  ⚠️  Missing: {', '.join(sync['missing_from_db'])}")
    print()

    # ML models
    ml = status['ml_models']
    print(f"🧠 ML Models:")
    print(f"  Total: {ml['total_models']} models trained")
    if ml['brand_voice_model']:
        print(f"  ✅ Brand Voice: {ml['brand_voice_model']['training_size']} examples")
    else:
        print(f"  ❌ Brand Voice: Not trained")
    print()

    # Test predictions
    if status['test_predictions']:
        print("🧪 Test Predictions:")
        for result in status['test_predictions'][:3]:
            icon = "✅" if result['correct'] else "❌"
            print(f"  {icon} Expected: {result['expected_brand']}, "
                  f"Got: {result['predicted_brand']} ({result['confidence']:.0%})")
        print()


if __name__ == '__main__':
    main()
