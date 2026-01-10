#!/usr/bin/env python3
"""
Brand Color → Personality Neural Network

Trains a neural network to predict brand personality from color palettes.

Input: Color features (12 features from HSV, temperature, dominance, etc.)
Output: Personality traits (calm, energetic, professional, creative, etc.)

Uses pure_neural_network.py (zero dependencies!)

Example:
    Ocean Dreams: #003366 (dark blue)
    → Features: [hue=0.58, sat=1.0, val=0.4, temp=0.2, ...]
    → Prediction: calm=0.9, deep=0.8, professional=0.7

Usage:
    python3 brand_color_neural_network.py train
    python3 brand_color_neural_network.py predict ocean-dreams
    python3 brand_color_neural_network.py test
"""

import sqlite3
import json
import colorsys
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from database import get_db
from pure_neural_network import PureNeuralNetwork as NeuralNetwork
from train_color_features import extract_color_features


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def hex_to_rgb(hex_color: str) -> tuple:
    """Convert hex color to RGB tuple (0-255)"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))


# ==============================================================================
# PERSONALITY TRAITS (Output Labels)
# ==============================================================================

PERSONALITY_TRAITS = [
    'calm',
    'energetic',
    'professional',
    'creative',
    'playful',
    'serious',
    'warm',
    'cool'
]


# ==============================================================================
# TRAINING DATA EXTRACTION
# ==============================================================================

def extract_training_data() -> List[Tuple[List[float], List[float]]]:
    """
    Extract training data from brands in database

    Returns:
        List of (features, labels) tuples
        - features: 12-element list of color features
        - labels: 8-element list of personality trait scores (0-1)

    Example:
        Ocean Dreams:
        - Colors: ['#003366', '#0066cc', ...]
        - Personality: "calm, deep, flowing"
        - Labels: [calm=0.9, energetic=0.1, professional=0.7, ...]
    """
    db = get_db()

    brands = db.execute('''
        SELECT name, personality, tone, config_json
        FROM brands
        WHERE config_json IS NOT NULL
    ''').fetchall()

    db.close()

    training_data = []

    for brand in brands:
        brand_dict = dict(brand)

        # Parse config
        try:
            config = json.loads(brand_dict['config_json'])
        except:
            continue

        # Extract colors
        colors = config.get('colors', [])
        if not colors:
            continue

        # Get primary color (first in palette)
        if isinstance(colors, list) and len(colors) > 0:
            primary_color = colors[0]
        elif isinstance(colors, dict):
            primary_color = colors.get('primary', '#667eea')
        else:
            continue

        # Convert to RGB
        try:
            rgb = hex_to_rgb(primary_color)
        except:
            continue

        # Extract features
        features = extract_color_features(rgb)

        # Extract personality labels
        personality = brand_dict.get('personality', '').lower()
        tone = brand_dict.get('tone', '').lower()
        combined_text = f"{personality} {tone}"

        # Create label vector (0 or 1 for each trait)
        labels = []
        for trait in PERSONALITY_TRAITS:
            # Check if trait keyword appears in personality/tone
            if trait in combined_text:
                labels.append(1.0)
            else:
                # Opposite traits
                opposite = {
                    'calm': 'energetic',
                    'energetic': 'calm',
                    'professional': 'playful',
                    'creative': 'serious',
                    'playful': 'professional',
                    'serious': 'creative',
                    'warm': 'cool',
                    'cool': 'warm'
                }
                if trait in opposite and opposite[trait] in combined_text:
                    labels.append(0.0)
                else:
                    labels.append(0.5)  # Neutral

        training_data.append((features, labels))

    return training_data


# ==============================================================================
# TRAINING
# ==============================================================================

def train_color_personality_network(epochs: int = 1000, learning_rate: float = 0.1) -> NeuralNetwork:
    """
    Train neural network on color → personality mapping

    Args:
        epochs: Number of training epochs
        learning_rate: Learning rate for gradient descent

    Returns:
        Trained NeuralNetwork

    Architecture:
        Input: 12 (color features)
        Hidden: [8, 6] (two hidden layers)
        Output: 8 (personality traits)
    """
    print("=" * 70)
    print("🧠 TRAINING COLOR → PERSONALITY NEURAL NETWORK")
    print("=" * 70)
    print()

    # Extract training data
    print("📊 Extracting training data from brands...")
    training_data = extract_training_data()

    if not training_data:
        print("❌ No training data found!")
        return None

    print(f"✅ Found {len(training_data)} training examples")
    print()

    # Create network
    print("🏗️  Creating neural network...")
    print(f"   Architecture: 12 → 8 → 8")
    print(f"   Epochs: {epochs}")
    print(f"   Learning Rate: {learning_rate}")
    print()

    nn = NeuralNetwork(
        input_size=12,
        hidden_size=8,
        output_size=8,
        learning_rate=learning_rate
    )

    # Train
    print("🎓 Training...")
    print()

    for epoch in range(epochs):
        total_loss = 0.0

        for features, labels in training_data:
            loss = nn.train(features, labels)
            total_loss += loss

        avg_loss = total_loss / len(training_data)

        if epoch % 100 == 0 or epoch == epochs - 1:
            print(f"   Epoch {epoch:4d}: Loss = {avg_loss:.6f}")

    print()
    print("✅ Training complete!")
    print()

    return nn


def save_network_to_database(nn: NeuralNetwork, model_name: str = 'color_to_personality'):
    """
    Save trained network to database

    Stores:
    - Model architecture (input_size, hidden_sizes, output_size)
    - Weights (as JSON)
    - Biases (as JSON)
    - Metadata (created_at, etc.)
    """
    print(f"💾 Saving network '{model_name}' to database...")

    db = get_db()

    # Convert weights and biases to JSON (store in model_data)
    model_data = json.dumps({
        'weights_ih': nn.weights_ih,
        'weights_ho': nn.weights_ho,
        'bias_h': nn.bias_h,
        'bias_o': nn.bias_o
    })

    # Insert into database
    db.execute('''
        INSERT INTO neural_networks
        (model_name, description, input_size, hidden_sizes, output_size,
         model_data, trained_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        model_name,
        'Color to personality prediction network',
        nn.input_size,
        json.dumps([nn.hidden_size]),  # Store as array for consistency
        nn.output_size,
        model_data,
        datetime.now().isoformat()
    ))

    db.commit()
    network_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
    db.close()

    print(f"✅ Saved network with ID: {network_id}")
    print()


# ==============================================================================
# PREDICTION
# ==============================================================================

def load_network_from_database(model_name: str = 'color_to_personality') -> Optional[NeuralNetwork]:
    """
    Load trained network from database

    Args:
        model_name: Name of model to load

    Returns:
        NeuralNetwork or None if not found
    """
    db = get_db()

    network = db.execute('''
        SELECT * FROM neural_networks
        WHERE model_name = ?
        ORDER BY trained_at DESC
        LIMIT 1
    ''', (model_name,)).fetchone()

    db.close()

    if not network:
        return None

    network_dict = dict(network)

    # Parse architecture
    input_size = network_dict['input_size']
    hidden_sizes = json.loads(network_dict['hidden_sizes'])
    hidden_size = hidden_sizes[0] if hidden_sizes else 8  # Use first hidden layer
    output_size = network_dict['output_size']

    # Create network
    nn = NeuralNetwork(input_size, hidden_size, output_size)

    # Load weights and biases from model_data
    try:
        model_data = json.loads(network_dict['model_data'])
        nn.weights_ih = model_data['weights_ih']
        nn.weights_ho = model_data['weights_ho']
        nn.bias_h = model_data['bias_h']
        nn.bias_o = model_data['bias_o']
    except:
        return None

    return nn


def predict_personality_from_color(color_hex: str, model_name: str = 'color_to_personality') -> Dict[str, float]:
    """
    Predict personality traits from a color

    Args:
        color_hex: Hex color code (e.g., '#003366')
        model_name: Name of model to use

    Returns:
        Dict mapping trait names to scores (0-1)

    Example:
        predict_personality_from_color('#003366')
        → {'calm': 0.85, 'energetic': 0.12, 'professional': 0.78, ...}
    """
    # Load network
    nn = load_network_from_database(model_name)
    if not nn:
        raise ValueError(f"Model '{model_name}' not found in database")

    # Extract features
    rgb = hex_to_rgb(color_hex)
    features = extract_color_features(rgb)

    # Predict
    _, outputs = nn.forward(features)

    # Map to trait names
    predictions = {}
    for i, trait in enumerate(PERSONALITY_TRAITS):
        predictions[trait] = outputs[i]

    return predictions


def predict_brand_personality(brand_slug: str) -> Dict[str, float]:
    """
    Predict personality for a brand based on its colors

    Args:
        brand_slug: Brand slug (e.g., 'ocean-dreams')

    Returns:
        Dict mapping trait names to scores (0-1)
    """
    db = get_db()

    brand = db.execute('''
        SELECT config_json FROM brands WHERE slug = ?
    ''', (brand_slug,)).fetchone()

    db.close()

    if not brand:
        raise ValueError(f"Brand '{brand_slug}' not found")

    brand_dict = dict(brand)

    # Parse config
    try:
        config = json.loads(brand_dict['config_json'])
    except:
        raise ValueError("Invalid brand config")

    # Get primary color
    colors = config.get('colors', [])
    if isinstance(colors, list) and len(colors) > 0:
        primary_color = colors[0]
    elif isinstance(colors, dict):
        primary_color = colors.get('primary', '#667eea')
    else:
        raise ValueError("No colors found in brand config")

    return predict_personality_from_color(primary_color)


# ==============================================================================
# TESTING
# ==============================================================================

def test_predictions():
    """Test predictions on known colors"""
    print("=" * 70)
    print("🧪 TESTING PREDICTIONS")
    print("=" * 70)
    print()

    test_cases = [
        ('#003366', 'Ocean Dreams (dark blue)', ['calm', 'professional', 'cool']),
        ('#ff6b6b', 'Coral Red', ['energetic', 'warm', 'playful']),
        ('#2ecc71', 'Green', ['calm', 'creative']),
        ('#9b59b6', 'Purple', ['creative', 'professional'])
    ]

    for color_hex, name, expected_traits in test_cases:
        print(f"🎨 {name}: {color_hex}")

        try:
            predictions = predict_personality_from_color(color_hex)

            # Show top 3 traits
            sorted_traits = sorted(predictions.items(), key=lambda x: x[1], reverse=True)
            top_3 = sorted_traits[:3]

            print(f"   Top traits:")
            for trait, score in top_3:
                bar = '█' * int(score * 20)
                print(f"      {trait:15} {score:.2f} {bar}")

            # Check if expected traits are in top predictions
            top_trait_names = [t[0] for t in top_3]
            matches = [t for t in expected_traits if t in top_trait_names]
            print(f"   Expected: {expected_traits}")
            print(f"   Matched: {matches} ({len(matches)}/{len(expected_traits)})")

        except Exception as e:
            print(f"   ❌ Error: {e}")

        print()


# ==============================================================================
# CLI
# ==============================================================================

def main():
    """CLI for color neural network"""
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 brand_color_neural_network.py train")
        print("  python3 brand_color_neural_network.py predict <brand_slug>")
        print("  python3 brand_color_neural_network.py test")
        print()
        print("Examples:")
        print("  python3 brand_color_neural_network.py train")
        print("  python3 brand_color_neural_network.py predict ocean-dreams")
        print("  python3 brand_color_neural_network.py test")
        return

    command = sys.argv[1]

    if command == 'train':
        # Train network
        nn = train_color_personality_network(epochs=1000, learning_rate=0.1)

        if nn:
            # Save to database
            save_network_to_database(nn, model_name='color_to_personality')

            # Test predictions
            print()
            test_predictions()

    elif command == 'predict':
        if len(sys.argv) < 3:
            print("Error: Missing brand slug")
            return

        brand_slug = sys.argv[2]

        try:
            predictions = predict_brand_personality(brand_slug)

            print("=" * 70)
            print(f"🔮 PERSONALITY PREDICTION FOR: {brand_slug}")
            print("=" * 70)
            print()

            # Sort by score
            sorted_traits = sorted(predictions.items(), key=lambda x: x[1], reverse=True)

            for trait, score in sorted_traits:
                bar = '█' * int(score * 20)
                print(f"{trait:15} {score:.2f} {bar}")

            print()

        except Exception as e:
            print(f"❌ Error: {e}")

    elif command == 'test':
        test_predictions()

    else:
        print(f"Unknown command: {command}")


if __name__ == '__main__':
    main()
