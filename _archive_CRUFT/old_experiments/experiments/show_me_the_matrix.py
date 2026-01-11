#!/usr/bin/env python3
"""
Show Me The Matrix - Neural Network Internals Viewer

Demonstrates that neural networks are REAL - just Python lists of numbers.
No magic, no black boxes. Just math.

Usage:
    python3 show_me_the_matrix.py
"""

import sqlite3
import json
import math


def sigmoid(x):
    """The activation function used in the network"""
    try:
        return 1.0 / (1.0 + math.exp(-x))
    except OverflowError:
        return 0.0 if x < 0 else 1.0


def show_network_internals(model_name='color_classifier'):
    """Show the actual weights and math inside a neural network"""

    print("=" * 70)
    print("🧠 NEURAL NETWORK INTERNALS - THE MATRIX IS REAL")
    print("=" * 70)
    print()

    # Load network from database
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT model_name, description, input_size, hidden_sizes,
               output_size, model_data
        FROM neural_networks
        WHERE model_name = ?
    ''', (model_name,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        print(f"❌ Network '{model_name}' not found!")
        return

    # Parse network data
    name, desc, input_size, hidden_sizes_json, output_size, model_data_json = row
    hidden_sizes = json.loads(hidden_sizes_json)
    model_data = json.loads(model_data_json)

    weights = model_data.get('weights', [])
    biases = model_data.get('biases', [])
    accuracy_history = model_data.get('accuracy_history', [])

    print(f"📌 Network: {name}")
    print(f"📝 Description: {desc}")
    print(f"🏗️  Architecture: {input_size} → {hidden_sizes} → {output_size}")
    print()

    # Show actual weights (first layer, first 10 weights)
    print("🔢 ACTUAL WEIGHTS (These are REAL numbers learned from training)")
    print("-" * 70)

    if weights and len(weights) > 0:
        print(f"\nInput → Hidden Layer weights:")
        # weights structure: [[[layer1_neuron1_weights], [layer1_neuron2_weights], ...], [[layer2_weights], ...]]
        layer1_weights = weights[0]  # First layer (input → hidden)
        if isinstance(layer1_weights, list) and len(layer1_weights) > 0:
            first_neuron = layer1_weights[0]  # First neuron in hidden layer
            if isinstance(first_neuron, list):
                print(f"\n  First hidden neuron (first 10 of {len(first_neuron)} weights):")
                for i, w in enumerate(first_neuron[:10]):
                    print(f"    Weight[{i}]: {w:+.8f}")
                print(f"\n  Total hidden neurons: {len(layer1_weights)}")
            else:
                # Fallback if structure is different
                print(f"  Unexpected weight structure: {type(first_neuron)}")

        print(f"\n  Total layers: {len(weights)}")
    else:
        print("  No weights found in model_data")

    print()

    # Show actual biases
    print("⚖️  ACTUAL BIASES (Shift values for each neuron)")
    print("-" * 70)

    if biases and len(biases) > 0:
        layer1_biases = biases[0]  # First layer biases
        if isinstance(layer1_biases, list) and len(layer1_biases) > 0:
            # Check if biases are nested or flat
            first_bias = layer1_biases[0]
            if isinstance(first_bias, (int, float)):
                # Flat list
                print(f"\nHidden layer biases (first 10 of {len(layer1_biases)}):")
                for i, b in enumerate(layer1_biases[:10]):
                    print(f"  Bias[{i}]: {b:+.8f}")
            elif isinstance(first_bias, list):
                # Nested list - flatten first
                flat_biases = [b for sublist in layer1_biases for b in sublist]
                print(f"\nHidden layer biases (first 10 of {len(flat_biases)}):")
                for i, b in enumerate(flat_biases[:10]):
                    print(f"  Bias[{i}]: {b:+.8f}")
            else:
                print(f"  Unexpected bias type: {type(first_bias)}")
        else:
            print(f"  Unexpected bias structure")
    else:
        print("  No biases found in model_data")

    print()

    # Show training history
    print("📈 TRAINING HISTORY (Network learned over time)")
    print("-" * 70)

    if accuracy_history:
        print(f"\nTotal epochs trained: {len(accuracy_history)}")
        print(f"Starting accuracy: {accuracy_history[0] * 100:.2f}%")
        print(f"Final accuracy: {accuracy_history[-1] * 100:.2f}%")
        print(f"Improvement: +{(accuracy_history[-1] - accuracy_history[0]) * 100:.2f}%")

        print("\nLast 10 epochs:")
        for i, acc in enumerate(accuracy_history[-10:], start=len(accuracy_history) - 9):
            bar = "█" * int(acc * 50)
            print(f"  Epoch {i:4d}: {acc * 100:5.2f}% {bar}")
    else:
        print("  No training history found")

    print()

    # Demonstrate forward pass
    print("🚀 LIVE DEMO: Forward Pass (Actual Calculation)")
    print("-" * 70)

    if model_name == 'color_classifier':
        # Red color example
        inputs = [1.0, 0.0, 0.0]  # RGB(255, 0, 0) normalized
        input_label = "RGB(255, 0, 0) = RED"
    else:
        # Generic example
        inputs = [1.0] + [0.0] * (input_size - 1)
        input_label = f"Input: {inputs}"

    print(f"\n📥 Input: {input_label}")
    print(f"   As numbers: {inputs}")
    print()

    if weights and biases and len(weights) > 0 and len(weights[0]) > 0:
        # Calculate first hidden neuron manually
        print("🧮 Hidden Layer Calculation (first neuron):")

        first_neuron_weights = weights[0][0]  # First neuron, first layer
        # Handle nested or flat bias structure
        if len(biases) > 0 and len(biases[0]) > 0:
            first_bias_elem = biases[0][0]
            if isinstance(first_bias_elem, (int, float)):
                first_neuron_bias = first_bias_elem
            elif isinstance(first_bias_elem, list) and len(first_bias_elem) > 0:
                first_neuron_bias = first_bias_elem[0]
            else:
                first_neuron_bias = 0
        else:
            first_neuron_bias = 0

        print(f"\n   Sum = (weight × input) for each input:")
        total = 0
        for i, (w, x) in enumerate(zip(first_neuron_weights[:len(inputs)], inputs)):
            product = w * x
            total += product
            print(f"     ({w:+.6f} × {x:.1f}) = {product:+.6f}")

        print(f"\n   Sum of products: {total:+.6f}")
        print(f"   Add bias: {total:+.6f} + {first_neuron_bias:+.6f} = {total + first_neuron_bias:+.6f}")

        activated = sigmoid(total + first_neuron_bias)
        print(f"\n   Apply sigmoid: sigmoid({total + first_neuron_bias:+.6f}) = {activated:.6f}")
        print(f"   ✅ First hidden neuron output: {activated:.6f}")

        print()
        print(f"   (Repeat this for all {len(weights[0])} hidden neurons...)")
        print("   (Then multiply hidden outputs by output layer weights...)")
        print()

        print(f"🎯 Final Output: Neural network multiplies all these values")
        print(f"   Result: Probability between 0 and 1")
        if model_name == 'color_classifier':
            print(f"   > 0.5 = WARM, < 0.5 = COOL")
    else:
        print("  Cannot demonstrate - weights/biases not available")

    print()
    print("=" * 70)
    print("💡 THIS IS REAL MATH - NO MAGIC!")
    print("=" * 70)
    print()
    print("Every number you see above:")
    print("  • Was LEARNED from training data")
    print("  • Is stored as JSON in SQLite")
    print("  • Is used in REAL calculations")
    print("  • Is just Python lists and floats")
    print()
    print("The neural network is:")
    print("  • Matrix multiplication (nested for loops)")
    print("  • Sigmoid activation (1 / (1 + e^(-x)))")
    print("  • Backpropagation (calculus + gradient descent)")
    print()
    print("NO external libraries. NO magic. Just MATH.")
    print()


if __name__ == '__main__':
    import sys

    # Allow specifying network name
    network_name = sys.argv[1] if len(sys.argv) > 1 else 'color_classifier'

    show_network_internals(network_name)

    # Show available networks
    print("📚 Available Networks:")
    print("-" * 70)

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()
    cursor.execute('SELECT model_name, description FROM neural_networks')

    for name, desc in cursor.fetchall():
        print(f"  • {name}")
        if desc:
            print(f"    {desc}")

    conn.close()

    print()
    print("Usage: python3 show_me_the_matrix.py [network_name]")
    print()
