#!/usr/bin/env python3
"""
Train Website Structure Model - Pure Python Stdlib

Trains ML model to understand website architecture patterns using:
- Route structures from sitemap
- Template variable usage
- HTTP method patterns
- Parameter naming conventions

Uses simple_ml.py infrastructure (TF-IDF, Naive Bayes, KNN).

Model can predict:
- Missing routes in CRUD operations
- Template variables needed for new routes
- Route naming inconsistencies
- API documentation structure

Like: Teaching AI the "grammar" of your website!
"""

import json
import os
from datetime import datetime
from collections import Counter

# Import existing ML infrastructure
from simple_ml import (
    tokenize,
    extract_features,
    calculate_idf,
    calculate_tfidf,
    cosine_similarity,
    train_naive_bayes,
    predict_naive_bayes,
    train_knn,
    predict_knn
)
from database import get_db
from website_structure_parser import build_training_dataset


def prepare_training_data(dataset):
    """
    Prepare website structure data for ML training

    Args:
        dataset: Output from build_training_dataset()

    Returns:
        tuple: (features_list, labels_list, feature_names)

    Features:
    - Route segments (text features)
    - HTTP method
    - Route type
    - Parameter patterns
    """
    routes = dataset['routes']

    features_list = []
    labels_list = []  # Label = route_type

    for route in routes:
        # Create text representation for TF-IDF
        text_features = ' '.join([
            route['segments'],  # Path segments
            route['param_names'],  # Parameter names
            route['desc_words'],  # Description keywords
            route['method'].lower()  # HTTP method
        ])

        features_list.append(text_features)
        labels_list.append(route['route_type'])

    return features_list, labels_list


def train_route_classifier(dataset):
    """
    Train classifier to predict route type from path/description

    Args:
        dataset: Training dataset from build_training_dataset()

    Returns:
        dict: Trained model data
    """
    print("🧠 Training route classifier...")

    features_list, labels_list = prepare_training_data(dataset)

    # Extract word counts for each document
    documents = [extract_features(text) for text in features_list]

    # Calculate IDF
    idf = calculate_idf(documents)

    # Calculate TF-IDF for each document
    tfidf_vectors = [calculate_tfidf(doc, idf) for doc in documents]

    # Train Naive Bayes classifier
    model = train_naive_bayes(tfidf_vectors, labels_list)

    print(f"✅ Trained on {len(features_list)} routes")
    print(f"   Route types: {set(labels_list)}")

    return {
        'model_type': 'naive_bayes',
        'model_data': model,
        'idf': idf,
        'labels': list(set(labels_list)),
        'training_size': len(features_list)
    }


def train_method_predictor(dataset):
    """
    Train model to predict HTTP method from route path

    Args:
        dataset: Training dataset

    Returns:
        dict: Trained model
    """
    print("🧠 Training HTTP method predictor...")

    routes = dataset['routes']

    # Features: route segments + parameters
    features_list = []
    labels_list = []  # Label = HTTP method

    for route in routes:
        text = route['segments'] + ' ' + route['param_names']
        features_list.append(text)
        labels_list.append(route['method'])

    # Extract features
    documents = [extract_features(text) for text in features_list]
    idf = calculate_idf(documents)
    tfidf_vectors = [calculate_tfidf(doc, idf) for doc in documents]

    # Train KNN (k=3)
    model = train_knn(tfidf_vectors, labels_list, k=3)

    print(f"✅ Trained on {len(features_list)} routes")

    return {
        'model_type': 'knn',
        'model_data': model,
        'idf': idf,
        'k': 3,
        'labels': list(set(labels_list))
    }


def train_parameter_predictor(dataset):
    """
    Train model to predict parameter types from route segments

    Args:
        dataset: Training dataset

    Returns:
        dict: Trained model
    """
    print("🧠 Training parameter predictor...")

    routes = dataset['routes']

    # Only use routes with parameters
    routes_with_params = [r for r in routes if r['has_params']]

    if not routes_with_params:
        print("⚠️  No routes with parameters to train on")
        return None

    features_list = []
    labels_list = []

    for route in routes_with_params:
        # Features: route segments
        features_list.append(route['segments'])

        # Label: parameter names (space-separated)
        labels_list.append(route['param_names'])

    # Use simple frequency-based model
    # Map segments → common parameter names
    param_associations = {}

    for features, params in zip(features_list, labels_list):
        segments = features.split()
        param_list = params.split()

        for segment in segments:
            if segment not in param_associations:
                param_associations[segment] = Counter()

            for param in param_list:
                param_associations[segment][param] += 1

    print(f"✅ Trained on {len(features_list)} parameterized routes")

    return {
        'model_type': 'frequency',
        'model_data': param_associations,
        'training_size': len(features_list)
    }


def save_model_to_db(model_name, model_data, description):
    """
    Save trained model to database

    Args:
        model_name: Unique model name
        model_data: Model dictionary
        description: Model description

    Returns:
        int: Model ID
    """
    db = get_db()

    # Serialize model data to JSON
    model_json = json.dumps(model_data)

    # Check if model exists
    existing = db.execute(
        'SELECT id FROM ml_models WHERE model_type = ?',
        (model_name,)
    ).fetchone()

    if existing:
        # Update existing model
        db.execute('''
            UPDATE ml_models
            SET model_data = ?,
                trained_on = ?,
                created_at = ?
            WHERE model_type = ?
        ''', (model_json, model_data.get('training_size', 0), datetime.now().isoformat(), model_name))

        model_id = existing['id']
        print(f"📝 Updated existing model: {model_name} (ID: {model_id})")
    else:
        # Insert new model
        cursor = db.execute('''
            INSERT INTO ml_models (model_type, model_data, trained_on, created_at)
            VALUES (?, ?, ?, ?)
        ''', (model_name, model_json, model_data.get('training_size', 0), datetime.now().isoformat()))

        model_id = cursor.lastrowid
        print(f"💾 Saved new model: {model_name} (ID: {model_id})")

    db.commit()
    db.close()

    return model_id


def load_model_from_db(model_name):
    """
    Load trained model from database

    Args:
        model_name: Model type/name

    Returns:
        dict: Model data or None if not found
    """
    db = get_db()

    model = db.execute(
        'SELECT model_data FROM ml_models WHERE model_type = ?',
        (model_name,)
    ).fetchone()

    db.close()

    if model:
        return json.loads(model['model_data'])
    return None


def predict_route_type(route_path, route_desc=''):
    """
    Predict route type from path and description

    Args:
        route_path: Flask route path (e.g., '/api/posts')
        route_desc: Route description

    Returns:
        tuple: (predicted_type, confidence)
    """
    # Load model
    model = load_model_from_db('website_route_classifier')
    if not model:
        return ('unknown', 0.0)

    # Extract features
    from website_structure_parser import extract_route_features

    route_data = {
        'path': route_path,
        'method': 'GET',  # Default
        'desc': route_desc
    }

    features = extract_route_features(route_data)

    # Create text representation
    text = ' '.join([
        features['segments'],
        features['param_names'],
        features['desc_words']
    ])

    # Extract features and calculate TF-IDF
    from simple_ml import extract_features, calculate_tfidf

    word_counts = extract_features(text)
    tfidf = calculate_tfidf(word_counts, model['idf'])

    # Predict using Naive Bayes
    prediction, confidence = predict_naive_bayes(tfidf, model['model_data'])

    return (prediction, confidence)


def predict_http_method(route_path):
    """
    Predict HTTP method from route path

    Args:
        route_path: Flask route path

    Returns:
        tuple: (predicted_method, confidence)
    """
    model = load_model_from_db('website_method_predictor')
    if not model:
        return ('GET', 0.5)

    # Extract segments
    from website_structure_parser import parse_route_pattern

    pattern = parse_route_pattern(route_path)
    text = ' '.join(pattern['segments'])

    # Calculate TF-IDF
    from simple_ml import extract_features, calculate_tfidf

    word_counts = extract_features(text)
    tfidf = calculate_tfidf(word_counts, model['idf'])

    # Predict using KNN
    prediction = predict_knn(tfidf, model['model_data'], k=model['k'])

    # Calculate confidence (simplified)
    confidence = 0.7  # TODO: Implement proper confidence calculation

    return (prediction, confidence)


def suggest_route_parameters(route_path):
    """
    Suggest parameter names for a route path

    Args:
        route_path: Flask route path (e.g., '/post')

    Returns:
        list: Suggested parameter names with confidence
    """
    model = load_model_from_db('website_parameter_predictor')
    if not model or not model.get('model_data'):
        return []

    # Extract segments
    from website_structure_parser import parse_route_pattern

    pattern = parse_route_pattern(route_path)
    segments = pattern['segments']

    # Get parameter suggestions from frequency model
    param_associations = model['model_data']
    suggestions = Counter()

    for segment in segments:
        if segment in param_associations:
            # Merge suggestions
            for param, count in param_associations[segment].items():
                suggestions[param] += count

    # Return top suggestions
    return [
        {'param': param, 'confidence': count / 10.0}
        for param, count in suggestions.most_common(3)
    ]


def train_all_models():
    """
    Train all website structure models

    Returns:
        dict: Model IDs and statistics
    """
    print("=" * 60)
    print("Training Website Structure Models")
    print("=" * 60)
    print()

    # Build dataset
    print("📊 Building training dataset...")
    dataset = build_training_dataset()

    stats = dataset['statistics']
    print(f"✅ Dataset ready: {stats['total_routes']} routes, {stats['total_templates']} templates")
    print()

    # Train models
    model_ids = {}

    # 1. Route type classifier
    route_model = train_route_classifier(dataset)
    model_ids['route_classifier'] = save_model_to_db(
        'website_route_classifier',
        route_model,
        'Predicts route type (api, admin, content, user, utility, static)'
    )
    print()

    # 2. HTTP method predictor
    method_model = train_method_predictor(dataset)
    model_ids['method_predictor'] = save_model_to_db(
        'website_method_predictor',
        method_model,
        'Predicts HTTP method (GET, POST, DELETE) from route path'
    )
    print()

    # 3. Parameter predictor
    param_model = train_parameter_predictor(dataset)
    if param_model:
        model_ids['parameter_predictor'] = save_model_to_db(
            'website_parameter_predictor',
            param_model,
            'Suggests parameter names for routes'
        )
        print()

    # Show summary
    print("=" * 60)
    print("✅ Training Complete!")
    print("=" * 60)
    print(f"Models trained: {len(model_ids)}")
    for name, model_id in model_ids.items():
        print(f"  {name}: ID {model_id}")
    print()

    return {
        'model_ids': model_ids,
        'dataset_stats': stats
    }


def test_predictions():
    """
    Test model predictions with example routes
    """
    print("=" * 60)
    print("Testing Model Predictions")
    print("=" * 60)
    print()

    test_routes = [
        ('/api/users', 'Get all users via API'),
        ('/admin/settings', 'Admin settings page'),
        ('/post/my-first-post', 'View blog post'),
        ('/brand/<slug>/export', 'Export brand package'),
    ]

    for route_path, desc in test_routes:
        print(f"Route: {route_path}")
        print(f"  Desc: {desc}")

        # Predict route type
        route_type, type_conf = predict_route_type(route_path, desc)
        print(f"  Predicted type: {route_type} ({type_conf:.1%} confidence)")

        # Predict HTTP method
        method, method_conf = predict_http_method(route_path)
        print(f"  Predicted method: {method} ({method_conf:.1%} confidence)")

        # Suggest parameters
        params = suggest_route_parameters(route_path)
        if params:
            print(f"  Suggested params: {[p['param'] for p in params]}")

        print()


def main():
    """CLI interface"""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        # Test mode
        test_predictions()
    else:
        # Train mode
        result = train_all_models()

        # Test predictions
        print()
        test_predictions()


if __name__ == '__main__':
    main()
