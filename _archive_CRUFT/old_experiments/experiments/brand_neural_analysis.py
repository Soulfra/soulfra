#!/usr/bin/env python3
"""
Brand Neural Analysis

Uses neural networks to analyze brands:
- Color → personality mapping
- Generate rotation questions based on brand colors/personality
- Predict brand alignment with user behavior
"""

import json
import numpy as np
from neural_network import load_neural_network


def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple (0-255)"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_normalized(rgb):
    """Convert RGB (0-255) to normalized (0-1) for neural network"""
    return np.array([r / 255.0 for r in rgb])


def analyze_brand_colors(brand):
    """
    Analyze brand colors using color_to_personality neural network

    Args:
        brand: Brand dict with 'colors_list' field

    Returns:
        Dict with personality predictions
    """
    if not brand or not brand.get('colors_list'):
        return {'personality': 'Neutral', 'energy': 'Medium', 'warmth': 'Balanced'}

    colors = brand['colors_list']

    # Try to load color_to_personality network
    try:
        network = load_neural_network('color_to_personality')
        if not network:
            return fallback_color_analysis(colors)

        # Get primary color RGB
        primary_hex = colors[0]
        rgb = hex_to_rgb(primary_hex)
        normalized = rgb_to_normalized(rgb)

        # Predict personality (network expects 3 inputs: R, G, B)
        prediction = network.predict(normalized.reshape(1, -1))

        # Interpret prediction
        # Output is a personality score (0-1)
        score = float(prediction[0][0]) if len(prediction[0]) > 0 else 0.5

        if score > 0.7:
            personality = 'Energetic and bold'
            energy = 'High'
        elif score > 0.4:
            personality = 'Balanced and friendly'
            energy = 'Medium'
        else:
            personality = 'Calm and thoughtful'
            energy = 'Low'

        # Determine warmth based on red channel
        warmth = 'Warm' if rgb[0] > 150 else 'Cool' if rgb[2] > 150 else 'Neutral'

        return {
            'personality': personality,
            'energy': energy,
            'warmth': warmth,
            'primary_color': primary_hex,
            'confidence': score
        }

    except Exception as e:
        print(f"Neural analysis failed: {e}")
        return fallback_color_analysis(colors)


def fallback_color_analysis(colors):
    """Simple heuristic color analysis when neural network unavailable"""
    primary_hex = colors[0]
    rgb = hex_to_rgb(primary_hex)

    # Simple heuristics
    avg_intensity = sum(rgb) / 3

    if rgb[0] > 200:  # High red
        personality = 'Energetic and bold'
        energy = 'High'
    elif rgb[2] > 200:  # High blue
        personality = 'Calm and trustworthy'
        energy = 'Low'
    elif rgb[1] > 200:  # High green
        personality = 'Natural and balanced'
        energy = 'Medium'
    elif avg_intensity > 200:  # Bright colors
        personality = 'Vibrant and friendly'
        energy = 'High'
    else:
        personality = 'Professional and subtle'
        energy = 'Medium'

    warmth = 'Warm' if rgb[0] > rgb[2] else 'Cool' if rgb[2] > rgb[0] else 'Neutral'

    return {
        'personality': personality,
        'energy': energy,
        'warmth': warmth,
        'primary_color': primary_hex,
        'confidence': 0.5
    }


def generate_rotation_questions(personality_analysis, count=4):
    """
    Generate rotation questions based on brand personality

    Args:
        personality_analysis: Dict from analyze_brand_colors()
        count: Number of questions to generate

    Returns:
        List of question strings
    """
    energy = personality_analysis.get('energy', 'Medium')
    warmth = personality_analysis.get('warmth', 'Neutral')

    question_templates = {
        ('High', 'Warm'): [
            'What bold move will you make today?',
            'Ready to ignite something amazing?',
            'What challenge excites you most?',
            'How will you bring the heat?'
        ],
        ('High', 'Cool'): [
            'What innovative idea drives you?',
            'Ready to push boundaries?',
            'What problem will you solve today?',
            'How will you level up?'
        ],
        ('High', 'Neutral'): [
            'What will you accomplish today?',
            'Ready to make your mark?',
            'What action will you take?',
            'How will you stand out?'
        ],
        ('Medium', 'Warm'): [
            'What brings you joy today?',
            'How will you connect with others?',
            'What are you grateful for?',
            'What makes you smile?'
        ],
        ('Medium', 'Cool'): [
            'What will you create today?',
            'How will you make progress?',
            'What goal are you working toward?',
            'What brings you peace?'
        ],
        ('Medium', 'Neutral'): [
            'What will you build today?',
            'How will you move forward?',
            'What brings you clarity?',
            'What are you working on?'
        ],
        ('Low', 'Warm'): [
            'What comforts you today?',
            'How will you show kindness?',
            'What small joy will you notice?',
            'What brings you calm?'
        ],
        ('Low', 'Cool'): [
            'What will you contemplate today?',
            'How will you find clarity?',
            'What insight are you seeking?',
            'What truth will you discover?'
        ],
        ('Low', 'Neutral'): [
            'What brings you peace?',
            'How will you reflect today?',
            'What quiet moment will you savor?',
            'What wisdom will you gain?'
        ]
    }

    key = (energy, warmth)
    default_questions = [
        'What will you create today?',
        'How will you make progress?',
        'What brings you joy?',
        'What are you working on?'
    ]
    questions = question_templates.get(key, default_questions)

    return questions[:count]


def get_brand_neural_summary(brand):
    """
    Get complete neural network analysis summary for a brand

    Args:
        brand: Brand dict

    Returns:
        Dict with personality, questions, and analysis
    """
    personality = analyze_brand_colors(brand)
    questions = generate_rotation_questions(personality)

    return {
        'personality_analysis': personality,
        'suggested_questions': questions,
        'brand_name': brand['name'] if brand else 'Unknown',
        'analyzed_at': 'runtime'
    }


# =============================================================================
# TESTING
# =============================================================================

if __name__ == '__main__':
    print("\n🧪 Testing Brand Neural Analysis\n")

    # Test with sample brand colors
    test_brand = {
        'name': 'Test Brand',
        'colors_list': ['#FF6B6B', '#4ECDC4', '#FFE66D']  # Red, cyan, yellow
    }

    analysis = analyze_brand_colors(test_brand)
    print(f"Color Analysis for {test_brand['name']}:")
    print(f"  Personality: {analysis['personality']}")
    print(f"  Energy: {analysis['energy']}")
    print(f"  Warmth: {analysis['warmth']}")
    print(f"  Confidence: {analysis['confidence']:.2f}")

    print("\nGenerated Questions:")
    questions = generate_rotation_questions(analysis)
    for i, q in enumerate(questions, 1):
        print(f"  {i}. {q}")

    print("\n✅ Brand neural analysis tests complete!\n")
