#!/usr/bin/env python3
"""
Binary Classifier Neural Network Trainer

Trains a neural network to classify binary values (0 or 1) from arrays.

Use cases:
- Is this value 0 or 1?
- Are most values in array 0 or 1?
- Pattern detection in binary sequences

Example:
    Input: [0.1, 0.2, 0.1]  → Output: "mostly_zero" (confidence: 0.95)
    Input: [0.9, 0.8, 0.95] → Output: "mostly_one" (confidence: 0.92)
"""

import sqlite3
import json
import random
import math


def sigmoid(x):
    """Sigmoid activation function"""
    try:
        return 1.0 / (1.0 + math.exp(-x))
    except OverflowError:
        return 0.0 if x < 0 else 1.0


def sigmoid_derivative(x):
    """Derivative of sigmoid for backpropagation"""
    s = sigmoid(x)
    return s * (1 - s)


def forward_pass(inputs, weights1, weights2, bias1, bias2):
    """Forward propagation through network"""
    # Input to hidden layer
    hidden = []
    for i in range(len(weights1[0])):
        weighted_sum = bias1[i]
        for j in range(len(inputs)):
            weighted_sum += inputs[j] * weights1[j][i]
        hidden.append(sigmoid(weighted_sum))

    # Hidden to output layer
    output = []
    for i in range(len(weights2[0])):
        weighted_sum = bias2[i]
        for j in range(len(hidden)):
            weighted_sum += hidden[j] * weights2[j][i]
        output.append(sigmoid(weighted_sum))

    return hidden, output


def train_network(training_data, input_size=3, hidden_size=4, output_size=2, epochs=1000, learning_rate=0.5):
    """
    Train binary classifier network

    Args:
        training_data: List of (inputs, expected_outputs) tuples
        input_size: Number of input features
        hidden_size: Number of hidden neurons
        output_size: Number of output classes (2 for binary)
        epochs: Training iterations
        learning_rate: Learning rate

    Returns:
        Trained weights and biases
    """
    print(f"🧠 Training Binary Classifier")
    print(f"   Input size: {input_size}")
    print(f"   Hidden size: {hidden_size}")
    print(f"   Output size: {output_size}")
    print(f"   Training samples: {len(training_data)}")
    print(f"   Epochs: {epochs}")

    # Initialize weights randomly
    weights1 = [[random.uniform(-1, 1) for _ in range(hidden_size)] for _ in range(input_size)]
    weights2 = [[random.uniform(-1, 1) for _ in range(output_size)] for _ in range(hidden_size)]
    bias1 = [random.uniform(-1, 1) for _ in range(hidden_size)]
    bias2 = [random.uniform(-1, 1) for _ in range(output_size)]

    # Training loop
    for epoch in range(epochs):
        total_error = 0

        for inputs, expected in training_data:
            # Forward pass
            hidden, output = forward_pass(inputs, weights1, weights2, bias1, bias2)

            # Calculate error
            output_errors = [expected[i] - output[i] for i in range(output_size)]
            total_error += sum(e * e for e in output_errors)

            # Backpropagation - Output layer
            output_deltas = [output_errors[i] * sigmoid_derivative(output[i]) for i in range(output_size)]

            # Backpropagation - Hidden layer
            hidden_errors = [sum(output_deltas[i] * weights2[j][i] for i in range(output_size)) for j in range(hidden_size)]
            hidden_deltas = [hidden_errors[i] * sigmoid_derivative(hidden[i]) for i in range(hidden_size)]

            # Update weights2 (hidden → output)
            for i in range(hidden_size):
                for j in range(output_size):
                    weights2[i][j] += learning_rate * output_deltas[j] * hidden[i]

            # Update weights1 (input → hidden)
            for i in range(input_size):
                for j in range(hidden_size):
                    weights1[i][j] += learning_rate * hidden_deltas[j] * inputs[i]

            # Update biases
            for i in range(output_size):
                bias2[i] += learning_rate * output_deltas[i]
            for i in range(hidden_size):
                bias1[i] += learning_rate * hidden_deltas[i]

        # Print progress
        if (epoch + 1) % 100 == 0:
            avg_error = total_error / len(training_data)
            print(f"   Epoch {epoch + 1}/{epochs} - Error: {avg_error:.6f}")

    print("✅ Training complete")

    return {
        'weights1': weights1,
        'weights2': weights2,
        'bias1': bias1,
        'bias2': bias2
    }


def generate_training_data():
    """Generate training data for binary classification"""
    data = []

    # Class 0: Arrays with mostly zeros (< 0.5)
    for _ in range(50):
        inputs = [random.uniform(0, 0.4) for _ in range(3)]
        outputs = [1, 0]  # Class 0: mostly_zero
        data.append((inputs, outputs))

    # Class 1: Arrays with mostly ones (> 0.5)
    for _ in range(50):
        inputs = [random.uniform(0.6, 1.0) for _ in range(3)]
        outputs = [0, 1]  # Class 1: mostly_one
        data.append((inputs, outputs))

    random.shuffle(data)
    return data


def test_network(model_data):
    """Test the trained network"""
    print("\n🧪 Testing Binary Classifier")

    test_cases = [
        ([0.1, 0.2, 0.1], "mostly_zero"),
        ([0.9, 0.8, 0.95], "mostly_one"),
        ([0.05, 0.1, 0.15], "mostly_zero"),
        ([0.85, 0.9, 0.88], "mostly_one"),
        ([0.3, 0.2, 0.4], "mostly_zero"),
        ([0.7, 0.8, 0.6], "mostly_one"),
    ]

    weights1 = model_data['weights1']
    weights2 = model_data['weights2']
    bias1 = model_data['bias1']
    bias2 = model_data['bias2']

    correct = 0
    for inputs, expected_label in test_cases:
        _, output = forward_pass(inputs, weights1, weights2, bias1, bias2)

        predicted_label = "mostly_zero" if output[0] > output[1] else "mostly_one"
        confidence = max(output)

        is_correct = predicted_label == expected_label
        correct += 1 if is_correct else 0

        status = "✅" if is_correct else "❌"
        print(f"   {status} Input: {inputs}")
        print(f"      Predicted: {predicted_label} (confidence: {confidence:.2f})")
        print(f"      Expected: {expected_label}")

    accuracy = (correct / len(test_cases)) * 100
    print(f"\n📊 Accuracy: {accuracy:.1f}% ({correct}/{len(test_cases)})")

    return accuracy >= 80


def save_to_database(model_data):
    """Save trained model to database"""
    print("\n💾 Saving to database...")

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    # Check if table exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS neural_networks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_name TEXT UNIQUE NOT NULL,
            description TEXT,
            input_size INTEGER,
            hidden_sizes TEXT,
            output_size INTEGER,
            model_data TEXT NOT NULL,
            accuracy REAL,
            trained_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Insert or update model
    cursor.execute('''
        INSERT OR REPLACE INTO neural_networks
        (model_name, description, input_size, hidden_sizes, output_size, model_data)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        'binary_classifier',
        'Binary classification: 0 vs 1 for arrays of values',
        3,  # input_size
        json.dumps([4]),  # hidden_sizes
        2,  # output_size (2 classes: mostly_zero, mostly_one)
        json.dumps(model_data)
    ))

    conn.commit()
    conn.close()

    print("✅ Model saved to database as 'binary_classifier'")


if __name__ == '__main__':
    print("=" * 70)
    print("🤖 BINARY CLASSIFIER NEURAL NETWORK TRAINER")
    print("=" * 70)
    print()

    # Generate training data
    print("📝 Generating training data...")
    training_data = generate_training_data()
    print(f"✅ Generated {len(training_data)} training examples")

    # Train network
    print()
    model_data = train_network(training_data, epochs=1000)

    # Test network
    success = test_network(model_data)

    if success:
        # Save to database
        save_to_database(model_data)
        print("\n✅ Binary classifier ready to use!")
    else:
        print("\n⚠️  Accuracy too low - try retraining with more epochs")
