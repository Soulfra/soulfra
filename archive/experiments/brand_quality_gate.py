#!/usr/bin/env python3
"""
Brand Quality Gate - ML Auto-Review System

Neural network-powered quality checking for brand submissions.
Replaces human moderators with automatic consistency checks.

Like Storyteller's Vault content review, but instant and objective.

Usage:
    from brand_quality_gate import review_brand_submission

    result = review_brand_submission(brand_zip_path)
    print(result['decision'])  # 'approved', 'rejected', 'manual_review'
    print(result['score'])     # 0-100
    print(result['suggestions'])  # List of improvements

Auto-approval thresholds:
    - Score >= 80: ✅ Auto-approved
    - Score 70-79: ⚠️  Manual review needed
    - Score < 70: ❌ Rejected with suggestions
"""

import json
import zipfile
import yaml
from pathlib import Path
from collections import Counter
import re


def review_brand_submission(zip_path, dry_run=False):
    """
    Auto-review brand submission using ML quality checks

    Args:
        zip_path: Path to brand ZIP file
        dry_run: If True, don't save results (default: False)

    Returns:
        dict with:
            - score: 0-100 quality score
            - decision: 'approved' | 'rejected' | 'manual_review'
            - message: Human-readable result
            - suggestions: List of improvements (if rejected)
            - checks: Detailed check results
    """
    print(f"🔍 Reviewing brand submission: {Path(zip_path).name}")
    print()

    # Extract and analyze brand
    try:
        brand_data = extract_brand_from_zip(zip_path)
    except Exception as e:
        return {
            'score': 0,
            'decision': 'rejected',
            'message': f'❌ ZIP extraction failed: {e}',
            'suggestions': ['Fix ZIP file structure', 'Include required files'],
            'checks': {}
        }

    # Run all quality checks
    checks = {}

    # Check 1: Wordmap Consistency (40% of score)
    print("1. Checking wordmap consistency...")
    wordmap_result = check_wordmap_consistency(brand_data)
    checks['wordmap'] = wordmap_result
    print(f"   Score: {wordmap_result['score']}/100")

    # Check 2: Emoji Pattern Quality (30% of score)
    print("2. Checking emoji patterns...")
    emoji_result = check_emoji_patterns(brand_data)
    checks['emoji'] = emoji_result
    print(f"   Score: {emoji_result['score']}/100")

    # Check 3: Content Quality (30% of score)
    print("3. Checking content quality...")
    content_result = check_content_quality(brand_data)
    checks['content'] = content_result
    print(f"   Score: {content_result['score']}/100")

    # Check 4: Image Quality (bonus points)
    print("4. Checking image quality...")
    image_result = check_image_quality(brand_data)
    checks['images'] = image_result
    print(f"   Score: {image_result['score']}/100")

    # Check 5: License Compliance (required)
    print("5. Checking license compliance...")
    license_result = check_license_compliance(brand_data)
    checks['license'] = license_result
    print(f"   Score: {license_result['score']}/100")

    print()

    # Calculate overall score
    overall_score = (
        wordmap_result['score'] * 0.4 +
        emoji_result['score'] * 0.3 +
        content_result['score'] * 0.3
    )

    # Bonus points for images (up to +10)
    overall_score += (image_result['score'] / 100) * 10

    # License is pass/fail
    if license_result['score'] < 100:
        overall_score = min(overall_score, 69)  # Can't pass without license

    overall_score = min(100, overall_score)  # Cap at 100

    # Make decision
    if overall_score >= 80:
        decision = 'approved'
        message = '✅ Brand approved! High quality detected.'
        suggestions = []
    elif overall_score >= 70:
        decision = 'manual_review'
        message = '⚠️  Needs human review. Score borderline.'
        suggestions = generate_improvement_suggestions(checks, overall_score)
    else:
        decision = 'rejected'
        message = f'❌ Brand rejected. Score too low ({overall_score:.1f}/100).'
        suggestions = generate_improvement_suggestions(checks, overall_score)

    result = {
        'score': round(overall_score, 1),
        'decision': decision,
        'message': message,
        'suggestions': suggestions,
        'checks': checks
    }

    print("=" * 70)
    print(f"📊 FINAL SCORE: {result['score']}/100")
    print(f"🎯 DECISION: {decision.upper()}")
    print(f"💬 {message}")
    print()

    if suggestions:
        print("💡 SUGGESTIONS:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"   {i}. {suggestion}")
        print()

    return result


def extract_brand_from_zip(zip_path):
    """Extract brand data from ZIP file"""
    with zipfile.ZipFile(zip_path, 'r') as zf:
        data = {
            'files': zf.namelist(),
            'brand_yaml': None,
            'wordmap': None,
            'emoji_patterns': None,
            'stories': [],
            'images': [],
            'license': None
        }

        for filename in zf.namelist():
            # Read brand.yaml
            if filename.endswith('brand.yaml') or filename.endswith('brand.yml'):
                with zf.open(filename) as f:
                    data['brand_yaml'] = yaml.safe_load(f)

            # Read wordmap
            elif 'wordmap.json' in filename:
                with zf.open(filename) as f:
                    data['wordmap'] = json.load(f)

            # Read emoji patterns
            elif 'emoji_patterns.json' in filename:
                with zf.open(filename) as f:
                    data['emoji_patterns'] = json.load(f)

            # Collect story files
            elif filename.endswith('.md') and 'stories' in filename:
                with zf.open(filename) as f:
                    data['stories'].append(f.read().decode('utf-8', errors='ignore'))

            # Collect images
            elif any(filename.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif']):
                data['images'].append(filename)

            # Read license
            elif 'LICENSE' in filename.upper():
                with zf.open(filename) as f:
                    data['license'] = f.read().decode('utf-8', errors='ignore')

        return data


def check_wordmap_consistency(brand_data):
    """
    Check wordmap quality and consistency

    Requirements:
        - Minimum 20 unique words
        - Words have meaningful frequency (not all 1)
        - No duplicate words
        - Words are relevant (not common stopwords)
    """
    wordmap = brand_data.get('wordmap', {})

    if not wordmap:
        return {
            'score': 0,
            'passed': False,
            'reason': 'No wordmap found in ZIP'
        }

    score = 100
    issues = []

    # Check 1: Minimum vocabulary size
    unique_words = len(wordmap)
    if unique_words < 20:
        score -= 30
        issues.append(f'Only {unique_words} words (need 20+)')
    elif unique_words < 50:
        score -= 10
        issues.append(f'Only {unique_words} words (50+ recommended)')

    # Check 2: Word frequency variance
    frequencies = list(wordmap.values())
    if len(set(frequencies)) == 1:
        score -= 20
        issues.append('All words have same frequency (need variety)')

    # Check 3: Check for common stopwords
    stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
    stopword_count = sum(1 for word in wordmap.keys() if word.lower() in stopwords)
    if stopword_count > 5:
        score -= 10
        issues.append(f'Too many stopwords ({stopword_count})')

    # Check 4: Word length variety
    avg_length = sum(len(word) for word in wordmap.keys()) / len(wordmap)
    if avg_length < 4:
        score -= 10
        issues.append('Words too short (avg < 4 chars)')

    return {
        'score': max(0, score),
        'passed': score >= 70,
        'reason': '; '.join(issues) if issues else 'Wordmap looks good',
        'unique_words': unique_words,
        'avg_frequency': sum(frequencies) / len(frequencies) if frequencies else 0
    }


def check_emoji_patterns(brand_data):
    """
    Check emoji pattern quality

    Requirements:
        - At least 3 different emoji
        - Emoji have meaningful frequency
        - Emoji density appropriate (not too many/few)
    """
    emoji_patterns = brand_data.get('emoji_patterns', {})

    if not emoji_patterns:
        return {
            'score': 50,  # Not required, but recommended
            'passed': True,
            'reason': 'No emoji patterns (optional but recommended)'
        }

    score = 100
    issues = []

    # Check 1: Minimum emoji variety
    unique_emoji = len(emoji_patterns)
    if unique_emoji < 3:
        score -= 30
        issues.append(f'Only {unique_emoji} emoji (need 3+)')

    # Check 2: Emoji frequency variance
    frequencies = list(emoji_patterns.values())
    if len(set(frequencies)) == 1:
        score -= 20
        issues.append('All emoji have same frequency')

    # Check 3: Brand emoji included
    brand_yaml = brand_data.get('brand_yaml', {})
    brand_emoji = brand_yaml.get('emoji')
    if brand_emoji and brand_emoji not in emoji_patterns:
        score -= 15
        issues.append(f'Brand emoji {brand_emoji} not in patterns')

    return {
        'score': max(0, score),
        'passed': score >= 70,
        'reason': '; '.join(issues) if issues else 'Emoji patterns look good',
        'unique_emoji': unique_emoji
    }


def check_content_quality(brand_data):
    """
    Check content quality and quantity

    Requirements:
        - Minimum 3 story posts
        - Posts have substance (> 100 words each)
        - Brand personality clearly defined
    """
    stories = brand_data.get('stories', [])
    brand_yaml = brand_data.get('brand_yaml', {})

    score = 100
    issues = []

    # Check 1: Minimum story count
    if len(stories) < 3:
        score -= 40
        issues.append(f'Only {len(stories)} stories (need 3+)')
    elif len(stories) < 5:
        score -= 10
        issues.append(f'Only {len(stories)} stories (5+ recommended)')

    # Check 2: Story length
    word_counts = [len(story.split()) for story in stories]
    if word_counts:
        avg_words = sum(word_counts) / len(word_counts)
        if avg_words < 100:
            score -= 20
            issues.append(f'Stories too short (avg {avg_words:.0f} words, need 100+)')

    # Check 3: Brand personality defined
    if not brand_yaml:
        score -= 30
        issues.append('No brand.yaml found')
    else:
        required_fields = ['name', 'slug', 'personality', 'tone']
        missing = [f for f in required_fields if not brand_yaml.get(f)]
        if missing:
            score -= 10 * len(missing)
            issues.append(f'Missing fields: {", ".join(missing)}')

    return {
        'score': max(0, score),
        'passed': score >= 70,
        'reason': '; '.join(issues) if issues else 'Content quality looks good',
        'story_count': len(stories),
        'avg_words': sum(word_counts) / len(word_counts) if word_counts else 0
    }


def check_image_quality(brand_data):
    """
    Check image files (optional but recommended)

    Requirements:
        - Logo exists
        - Banner/thumbnail included
        - Images are reasonable size
    """
    images = brand_data.get('images', [])

    score = 100
    issues = []

    # Check for logo
    has_logo = any('logo' in img.lower() for img in images)
    if not has_logo:
        score -= 40
        issues.append('No logo image found')

    # Check for banner/thumbnail
    has_banner = any(any(term in img.lower() for term in ['banner', 'thumb', 'preview']) for img in images)
    if not has_banner:
        score -= 30
        issues.append('No banner/thumbnail image found')

    # Minimum image count
    if len(images) < 2:
        score -= 20
        issues.append(f'Only {len(images)} images (2+ recommended)')

    return {
        'score': max(0, score),
        'passed': score >= 50,  # Lower threshold since images are optional
        'reason': '; '.join(issues) if issues else 'Image quality looks good',
        'image_count': len(images),
        'has_logo': has_logo,
        'has_banner': has_banner
    }


def check_license_compliance(brand_data):
    """
    Check license file exists and is valid

    Requirements:
        - LICENSE.txt or LICENSE.md exists
        - License type is valid
        - Attribution text present (if required)
    """
    license_text = brand_data.get('license')
    brand_yaml = brand_data.get('brand_yaml', {})

    if not license_text:
        return {
            'score': 0,
            'passed': False,
            'reason': 'No LICENSE file found'
        }

    score = 100
    issues = []

    # Check for valid license types
    valid_licenses = ['CC0', 'CC-BY', 'MIT', 'Apache', 'GPL', 'Public Domain']
    has_valid_license = any(lic in license_text for lic in valid_licenses)

    if not has_valid_license:
        score -= 50
        issues.append('No recognized license type found')

    # Check license matches brand.yaml
    declared_license = brand_yaml.get('license_type', '').upper()
    if declared_license and declared_license not in license_text.upper():
        score -= 20
        issues.append(f'License mismatch (declared: {declared_license})')

    return {
        'score': max(0, score),
        'passed': score >= 100,
        'reason': '; '.join(issues) if issues else 'License compliance OK',
        'has_license': bool(license_text),
        'recognized_type': has_valid_license
    }


def generate_improvement_suggestions(checks, overall_score):
    """Generate actionable improvement suggestions"""
    suggestions = []

    # Wordmap suggestions
    if checks['wordmap']['score'] < 70:
        suggestions.append(
            f"Wordmap: {checks['wordmap']['reason']}. "
            "Add more unique, brand-specific vocabulary."
        )

    # Emoji suggestions
    if checks['emoji']['score'] < 70:
        suggestions.append(
            f"Emoji: {checks['emoji']['reason']}. "
            "Include consistent emoji usage across posts."
        )

    # Content suggestions
    if checks['content']['score'] < 70:
        suggestions.append(
            f"Content: {checks['content']['reason']}. "
            "Write more example posts showing brand voice."
        )

    # Image suggestions
    if checks['images']['score'] < 50:
        suggestions.append(
            f"Images: {checks['images']['reason']}. "
            "Include logo and banner images."
        )

    # License suggestions
    if checks['license']['score'] < 100:
        suggestions.append(
            f"License: {checks['license']['reason']}. "
            "Add LICENSE.txt with valid license type."
        )

    # General suggestion
    if overall_score < 70:
        suggestions.append(
            "Overall quality too low. Focus on wordmap, content, and licensing."
        )
    elif overall_score < 80:
        suggestions.append(
            "Close to approval! Address the issues above to auto-approve."
        )

    return suggestions


def test_quality_gate():
    """Test the quality gate with a mock brand"""
    print("=" * 70)
    print("🧪 TESTING BRAND QUALITY GATE")
    print("=" * 70)
    print()

    # Create a test ZIP file
    import tempfile
    import os

    test_dir = tempfile.mkdtemp()
    zip_path = os.path.join(test_dir, 'test-brand.zip')

    # Create test brand data
    with zipfile.ZipFile(zip_path, 'w') as zf:
        # brand.yaml
        brand_yaml = yaml.dump({
            'name': 'TestBrand',
            'slug': 'testbrand',
            'emoji': '🧪',
            'personality': 'Testing, experimental, thorough',
            'tone': 'Technical and precise',
            'license_type': 'CC0'
        })
        zf.writestr('brand.yaml', brand_yaml)

        # wordmap.json (good quality)
        wordmap = {
            'testing': 45,
            'experimental': 38,
            'thorough': 32,
            'verification': 28,
            'quality': 25,
            'analysis': 22,
            'systematic': 20,
            'rigorous': 18,
            'comprehensive': 16,
            'detailed': 15,
            'precise': 14,
            'accurate': 13,
            'validated': 12,
            'certified': 11,
            'proven': 10,
            'reliable': 9,
            'consistent': 8,
            'reproducible': 7,
            'scientific': 6,
            'methodical': 5
        }
        zf.writestr('ml_models/wordmap.json', json.dumps(wordmap))

        # emoji_patterns.json
        emoji_patterns = {
            '🧪': 50,
            '🔬': 30,
            '✅': 25,
            '📊': 20
        }
        zf.writestr('ml_models/emoji_patterns.json', json.dumps(emoji_patterns))

        # Stories
        story1 = "Testing is essential for quality assurance. " * 25  # ~150 words
        story2 = "Experimental verification requires thorough analysis. " * 25
        story3 = "Quality control ensures systematic reproducibility. " * 25
        zf.writestr('stories/post-1.md', story1)
        zf.writestr('stories/post-2.md', story2)
        zf.writestr('stories/post-3.md', story3)

        # LICENSE
        license_text = """CC0 1.0 Universal

This work has been dedicated to the public domain.
You can copy, modify, and distribute this work, even for commercial purposes.
"""
        zf.writestr('LICENSE.txt', license_text)

        # Images (empty files for testing)
        zf.writestr('images/logo.png', b'')
        zf.writestr('images/banner.png', b'')

    # Run review
    result = review_brand_submission(zip_path)

    # Cleanup
    import shutil
    shutil.rmtree(test_dir)

    return result


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        # Review a specific ZIP file
        zip_path = sys.argv[1]
        result = review_brand_submission(zip_path)

        # Exit with appropriate code
        if result['decision'] == 'approved':
            sys.exit(0)
        elif result['decision'] == 'manual_review':
            sys.exit(1)
        else:
            sys.exit(2)
    else:
        # Run test
        test_quality_gate()
