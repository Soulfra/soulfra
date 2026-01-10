#!/usr/bin/env python3
"""
Train 4 Context-Specific Neural Networks

Each network has a different "personality" based on what data it's trained on:
- CalRiven: Technical posts (has code, architecture, etc.)
- TheAuditor: Validation posts (has tests, data, proof)
- DeathToData: Privacy-focused (OSS, self-hosted, no tracking)
- Soulfra: Meta-judge (weighs the other 3)

This is like Reddit subreddits - each has different values/context.
"""

import numpy as np
from database import get_db
from neural_network import NeuralNetwork, save_neural_network
import re


def extract_technical_features(post):
    """
    CalRiven's perspective: Technical content

    Features:
    - has_code: Binary (0 or 1)
    - code_density: Float 0-1 (% of content that's code)
    - technical_terms: Count (git, sql, api, class, function, etc.)
    - has_github: Binary
    """
    content = post['content']

    # Has code blocks?
    has_code = 1 if ('<code>' in content or '<pre>' in content) else 0

    # Code density (rough estimate)
    code_blocks = re.findall(r'<code>.*?</code>', content, re.DOTALL)
    code_blocks += re.findall(r'<pre>.*?</pre>', content, re.DOTALL)
    code_chars = sum(len(block) for block in code_blocks)
    total_chars = len(content)
    code_density = code_chars / total_chars if total_chars > 0 else 0.0

    # Technical terms
    technical_words = [
        'git', 'sql', 'api', 'class', 'function', 'database', 'server',
        'python', 'javascript', 'code', 'algorithm', 'architecture', 'implementation'
    ]
    content_lower = content.lower()
    tech_count = sum(1 for word in technical_words if word in content_lower)
    tech_count_norm = min(tech_count / 10.0, 1.0)  # Normalize to 0-1

    # Has GitHub links
    has_github = 1 if 'github' in content_lower else 0

    return np.array([has_code, code_density, tech_count_norm, has_github])


def explain_technical_features(features, post):
    """Convert technical features array to human-readable explanation"""
    content = post['content']
    content_lower = content.lower()

    # Find which technical terms were detected
    technical_words = [
        'git', 'sql', 'api', 'class', 'function', 'database', 'server',
        'python', 'javascript', 'code', 'algorithm', 'architecture', 'implementation'
    ]
    found_terms = [word for word in technical_words if word in content_lower]

    explanation = {
        'has_code': {
            'value': bool(features[0]),
            'text': 'Code blocks detected' if features[0] else 'No code blocks found'
        },
        'code_density': {
            'value': float(features[1]),
            'text': f'{features[1]*100:.1f}% of content is code'
        },
        'technical_terms': {
            'value': int(features[2] * 10),  # Denormalize
            'text': f'{int(features[2]*10)} technical terms found',
            'details': found_terms[:5] if found_terms else []
        },
        'has_github': {
            'value': bool(features[3]),
            'text': 'GitHub link present' if features[3] else 'No GitHub links'
        }
    }

    return explanation


def extract_validation_features(post):
    """
    TheAuditor's perspective: Validation & proof

    Features:
    - has_tests: Binary (mentions tests, pytest, etc.)
    - has_proof: Binary (has data, numbers, evidence)
    - has_data: Binary (has tables, charts, statistics)
    - content_length: Normalized (longer = more thorough?)
    """
    content = post['content']
    content_lower = content.lower()

    # Has tests
    test_terms = ['test', 'pytest', 'unittest', 'verify', 'validation', 'assert']
    has_tests = 1 if any(term in content_lower for term in test_terms) else 0

    # Has proof (numbers, percentages, measurements)
    has_numbers = 1 if re.search(r'\d+%|\d+\.\d+|\d+ (fps|ms|seconds|bytes)', content) else 0

    # Has data (tables, charts, results)
    has_data = 1 if ('<table>' in content or 'result' in content_lower or 'data' in content_lower) else 0

    # Content length (normalized)
    length_norm = min(len(content) / 10000.0, 1.0)  # Cap at 10K chars = 1.0

    return np.array([has_tests, has_numbers, has_data, length_norm])


def explain_validation_features(features, post):
    """Convert validation features array to human-readable explanation"""
    content = post['content']
    content_lower = content.lower()

    # Find which test terms were detected
    test_terms = ['test', 'pytest', 'unittest', 'verify', 'validation', 'assert']
    found_test_terms = [term for term in test_terms if term in content_lower]

    # Find numbers/evidence
    numbers_found = re.findall(r'\d+%|\d+\.\d+|\d+ (fps|ms|seconds|bytes)', content)

    explanation = {
        'has_tests': {
            'value': bool(features[0]),
            'text': 'Testing keywords found' if features[0] else 'No testing keywords',
            'details': found_test_terms[:3] if found_test_terms else []
        },
        'has_proof': {
            'value': bool(features[1]),
            'text': 'Numerical evidence present' if features[1] else 'No numerical evidence',
            'details': numbers_found[:3] if numbers_found else []
        },
        'has_data': {
            'value': bool(features[2]),
            'text': 'Data/results mentioned' if features[2] else 'No data references'
        },
        'content_length': {
            'value': int(features[3] * 10000),  # Denormalize
            'text': f'{len(content):,} characters ({features[3]*100:.0f}% of max)'
        }
    }

    return explanation


def extract_privacy_features(post):
    """
    DeathToData's perspective: Privacy & decentralization

    Features:
    - mentions_oss: Binary (open source, OSS, self-hosted)
    - mentions_privacy: Binary (privacy, decentralization, local)
    - has_external_deps: Binary (mentions Google, FB, etc.)
    - mentions_self_hosting: Binary
    """
    content = post['content']
    content_lower = content.lower()

    # Mentions OSS
    oss_terms = ['open source', 'oss', 'self-hosted', 'self hosted', 'local', 'on-premise']
    mentions_oss = 1 if any(term in content_lower for term in oss_terms) else 0

    # Mentions privacy
    privacy_terms = ['privacy', 'decentralization', 'encrypted', 'no tracking', 'gdpr']
    mentions_privacy = 1 if any(term in content_lower for term in privacy_terms) else 0

    # Has external dependencies (bad for privacy)
    external_services = ['google', 'facebook', 'amazon', 'microsoft', 'tracking', 'analytics']
    has_external = 1 if any(service in content_lower for service in external_services) else 0

    # Mentions self-hosting
    self_host_terms = ['self-host', 'self host', 'localhost', 'docker', 'deploy']
    mentions_self_host = 1 if any(term in content_lower for term in self_host_terms) else 0

    return np.array([mentions_oss, mentions_privacy, has_external, mentions_self_host])


def explain_privacy_features(features, post):
    """Convert privacy features array to human-readable explanation"""
    content = post['content']
    content_lower = content.lower()

    # Find which OSS terms were detected
    oss_terms = ['open source', 'oss', 'self-hosted', 'self hosted', 'local', 'on-premise']
    found_oss = [term for term in oss_terms if term in content_lower]

    # Find which privacy terms were detected
    privacy_terms = ['privacy', 'decentralization', 'encrypted', 'no tracking', 'gdpr']
    found_privacy = [term for term in privacy_terms if term in content_lower]

    # Find which external services were detected
    external_services = ['google', 'facebook', 'amazon', 'microsoft', 'tracking', 'analytics']
    found_external = [service for service in external_services if service in content_lower]

    # Find which self-hosting terms were detected
    self_host_terms = ['self-host', 'self host', 'localhost', 'docker', 'deploy']
    found_self_host = [term for term in self_host_terms if term in content_lower]

    explanation = {
        'mentions_oss': {
            'value': bool(features[0]),
            'text': 'Open source keywords found' if features[0] else 'No OSS keywords',
            'details': found_oss[:3] if found_oss else []
        },
        'mentions_privacy': {
            'value': bool(features[1]),
            'text': 'Privacy keywords found' if features[1] else 'No privacy keywords',
            'details': found_privacy[:3] if found_privacy else []
        },
        'has_external_deps': {
            'value': bool(features[2]),
            'text': '⚠️ External services mentioned' if features[2] else '✓ No external dependencies',
            'details': found_external[:3] if found_external else []
        },
        'mentions_self_hosting': {
            'value': bool(features[3]),
            'text': 'Self-hosting keywords found' if features[3] else 'No self-hosting keywords',
            'details': found_self_host[:3] if found_self_host else []
        }
    }

    return explanation


def train_calriven_network():
    """Train CalRiven network on technical content"""
    print("=" * 70)
    print("Training CalRiven Network (Technical Context)")
    print("=" * 70)
    print()

    db = get_db()
    posts = db.execute('SELECT id, title, content FROM posts').fetchall()
    db.close()

    # Extract features
    X = []
    y = []

    for post in posts:
        features = extract_technical_features(post)
        X.append(features)

        # Label: 1 if has code (technical), 0 if not
        label = 1 if features[0] == 1 else 0
        y.append([label])

    X = np.array(X)
    y = np.array(y)

    print(f"Training data: {len(X)} posts")
    print(f"  Technical posts: {int(y.sum())}")
    print(f"  Non-technical: {len(y) - int(y.sum())}")
    print()

    # Create network: 4 inputs → 8 hidden → 1 output
    network = NeuralNetwork(
        input_size=4,
        hidden_sizes=[8],
        output_size=1,
        activation='relu',
        output_activation='sigmoid'
    )

    # Train
    network.train(X, y, epochs=50, learning_rate=0.1, verbose=True)

    # Save
    save_neural_network(network, 'calriven_technical_classifier')

    print()
    print("✅ CalRiven network trained and saved")
    return network


def train_theauditor_network():
    """Train TheAuditor network on validation content"""
    print()
    print("=" * 70)
    print("Training TheAuditor Network (Validation Context)")
    print("=" * 70)
    print()

    db = get_db()
    posts = db.execute('SELECT id, title, content FROM posts').fetchall()
    db.close()

    # Extract features
    X = []
    y = []

    for post in posts:
        features = extract_validation_features(post)
        X.append(features)

        # Label: 1 if has tests OR data (validated), 0 if not
        label = 1 if (features[0] == 1 or features[2] == 1) else 0
        y.append([label])

    X = np.array(X)
    y = np.array(y)

    print(f"Training data: {len(X)} posts")
    print(f"  Validated posts: {int(y.sum())}")
    print(f"  Unvalidated: {len(y) - int(y.sum())}")
    print()

    # Create network: 4 inputs → 8 hidden → 1 output
    network = NeuralNetwork(
        input_size=4,
        hidden_sizes=[8],
        output_size=1,
        activation='relu',
        output_activation='sigmoid'
    )

    # Train
    network.train(X, y, epochs=50, learning_rate=0.1, verbose=True)

    # Save
    save_neural_network(network, 'theauditor_validation_classifier')

    print()
    print("✅ TheAuditor network trained and saved")
    return network


def train_deathtodata_network():
    """Train DeathToData network on privacy content"""
    print()
    print("=" * 70)
    print("Training DeathToData Network (Privacy Context)")
    print("=" * 70)
    print()

    db = get_db()
    posts = db.execute('SELECT id, title, content FROM posts').fetchall()
    db.close()

    # Extract features
    X = []
    y = []

    for post in posts:
        features = extract_privacy_features(post)
        X.append(features)

        # Label: 1 if privacy-friendly (OSS, no external deps), 0 if not
        label = 1 if (features[0] == 1 or features[1] == 1) and features[2] == 0 else 0
        y.append([label])

    X = np.array(X)
    y = np.array(y)

    print(f"Training data: {len(X)} posts")
    print(f"  Privacy-friendly: {int(y.sum())}")
    print(f"  Privacy-hostile: {len(y) - int(y.sum())}")
    print()

    # Create network: 4 inputs → 8 hidden → 1 output
    network = NeuralNetwork(
        input_size=4,
        hidden_sizes=[8],
        output_size=1,
        activation='relu',
        output_activation='sigmoid'
    )

    # Train
    network.train(X, y, epochs=50, learning_rate=0.1, verbose=True)

    # Save
    save_neural_network(network, 'deathtodata_privacy_classifier')

    print()
    print("✅ DeathToData network trained and saved")
    return network


def train_soulfra_judge_network():
    """
    Train Soulfra network to judge based on other 3 networks

    This is a meta-network that takes predictions from:
    - CalRiven (technical score)
    - TheAuditor (validation score)
    - DeathToData (privacy score)

    And outputs a final judgment.
    """
    print()
    print("=" * 70)
    print("Training Soulfra Network (Meta-Judge)")
    print("=" * 70)
    print()

    # For now, use simple heuristic:
    # If 2/3 networks agree (score > 0.5), approve
    # This will be a simple weighted vote network

    # Generate synthetic training data
    # [calriven_score, auditor_score, deathtodata_score] → approved?
    X = []
    y = []

    # Patterns to learn:
    # All 3 high → approve
    X.append([0.9, 0.9, 0.9])
    y.append([1])

    # 2/3 high → approve
    X.append([0.8, 0.7, 0.3])
    y.append([1])
    X.append([0.8, 0.3, 0.7])
    y.append([1])
    X.append([0.3, 0.8, 0.7])
    y.append([1])

    # 1/3 high → reject
    X.append([0.8, 0.2, 0.3])
    y.append([0])
    X.append([0.2, 0.8, 0.3])
    y.append([0])
    X.append([0.2, 0.3, 0.8])
    y.append([0])

    # All low → reject
    X.append([0.2, 0.2, 0.2])
    y.append([0])

    # Add more varied examples
    for _ in range(20):
        scores = np.random.rand(3)
        # Label: approve if mean > 0.5
        label = 1 if scores.mean() > 0.5 else 0
        X.append(scores)
        y.append([label])

    X = np.array(X)
    y = np.array(y)

    print(f"Training data: {len(X)} examples")
    print(f"  Approve: {int(y.sum())}")
    print(f"  Reject: {len(y) - int(y.sum())}")
    print()

    # Create network: 3 inputs (other networks' scores) → 4 hidden → 1 output
    network = NeuralNetwork(
        input_size=3,
        hidden_sizes=[4],
        output_size=1,
        activation='relu',
        output_activation='sigmoid'
    )

    # Train
    network.train(X, y, epochs=100, learning_rate=0.1, verbose=True)

    # Save
    save_neural_network(network, 'soulfra_judge')

    print()
    print("✅ Soulfra judge network trained and saved")
    return network


def main():
    """Train all 4 context networks"""
    print("=" * 70)
    print("🧠 Training 4 Context-Specific Neural Networks")
    print("=" * 70)
    print()
    print("This creates 4 networks with different 'personalities':")
    print("  1. CalRiven    - Technical content (code, architecture)")
    print("  2. TheAuditor  - Validation (tests, data, proof)")
    print("  3. DeathToData - Privacy (OSS, decentralization)")
    print("  4. Soulfra     - Meta-judge (weighs other 3)")
    print()
    print("Like Reddit subreddits - each has different values/context.")
    print()

    # Train all 4
    calriven = train_calriven_network()
    auditor = train_theauditor_network()
    deathtodata = train_deathtodata_network()
    soulfra = train_soulfra_judge_network()

    print()
    print("=" * 70)
    print("✅ ALL 4 NETWORKS TRAINED")
    print("=" * 70)
    print()
    print("Networks saved:")
    print("  - calriven_technical_classifier")
    print("  - theauditor_validation_classifier")
    print("  - deathtodata_privacy_classifier")
    print("  - soulfra_judge")
    print()
    print("Now you can see them debate at: http://localhost:5001/train?mode=posts")


if __name__ == '__main__':
    main()
