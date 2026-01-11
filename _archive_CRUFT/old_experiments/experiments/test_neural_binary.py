#!/usr/bin/env python3
"""
Test Neural Network: Binary Classification (Even vs Odd)

Proves the neural network actually LEARNS by training it to classify
numbers as even or odd. This is simpler than text classification and
demonstrates backpropagation working correctly.

If loss decreases and accuracy increases, backprop is working!
"""

import numpy as np
import matplotlib.pyplot as plt
from neural_network import NeuralNetwork, save_neural_network


def generate_even_odd_data(n_samples=1000):
    """
    Generate training data: numbers and their even/odd labels

    Input: Integer encoded as binary features [bit7, bit6, ..., bit0]
    Output: 1 if even, 0 if odd
    """
    # Generate random integers (0-255)
    numbers = np.random.randint(0, 256, size=n_samples)

    # Convert to binary representation (8 bits)
    X = np.zeros((n_samples, 8))
    for i, num in enumerate(numbers):
        X[i] = [int(b) for b in format(num, '08b')]

    # Label: 1 if even, 0 if odd
    y = (numbers % 2 == 0).astype(float).reshape(-1, 1)

    return X, y, numbers


def test_even_odd_classification():
    """
    Train neural network to classify even vs odd
    """
    print("=" * 70)
    print("NEURAL NETWORK TEST: Even vs Odd Classification")
    print("=" * 70)
    print()

    # Generate data
    print("Generating training data...")
    X_train, y_train, train_numbers = generate_even_odd_data(n_samples=1000)
    X_test, y_test, test_numbers = generate_even_odd_data(n_samples=200)

    print(f"Training samples: {X_train.shape[0]}")
    print(f"Test samples: {X_test.shape[0]}")
    print()

    # Create neural network
    print("Creating neural network...")
    print("  Architecture: 8 inputs → 16 hidden → 1 output")
    print("  Activation: ReLU (hidden), Sigmoid (output)")
    print()

    nn = NeuralNetwork(
        input_size=8,
        hidden_sizes=[16],
        output_size=1,
        activation='relu',
        output_activation='sigmoid'
    )

    # Train
    print("Training...")
    print()
    nn.train(X_train, y_train, epochs=50, learning_rate=0.1, batch_size=32, verbose=True)

    print()
    print("=" * 70)
    print("TRAINING COMPLETE")
    print("=" * 70)
    print()

    # Evaluate
    predictions = nn.predict(X_test)
    accuracy = nn.calculate_accuracy(y_test, predictions)

    print(f"Test Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
    print()

    # Show some predictions
    print("Sample Predictions:")
    print("-" * 50)
    print(f"{'Number':<10} {'True Label':<15} {'Prediction':<15} {'Confidence':<15}")
    print("-" * 50)

    for i in range(min(10, len(test_numbers))):
        num = test_numbers[i]
        true_label = "Even" if y_test[i][0] == 1 else "Odd"
        pred_prob = predictions[i][0]
        pred_label = "Even" if pred_prob > 0.5 else "Odd"
        confidence = pred_prob if pred_prob > 0.5 else (1 - pred_prob)

        correct = "✓" if true_label == pred_label else "✗"
        print(f"{num:<10} {true_label:<15} {pred_label:<15} {confidence:.4f} {correct}")

    print()

    # Plot learning curves
    print("Generating learning curves...")
    plot_learning_curves(nn.loss_history, nn.accuracy_history)

    # Save model
    save_neural_network(nn, 'even_odd_classifier', 'Binary classifier: Even vs Odd numbers')

    return nn


def plot_learning_curves(loss_history, accuracy_history):
    """
    Visualize learning: loss and accuracy over epochs
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

    # Loss curve
    ax1.plot(loss_history, color='red', linewidth=2)
    ax1.set_xlabel('Epoch')
    ax1.set_ylabel('Loss')
    ax1.set_title('Training Loss Over Time')
    ax1.grid(True, alpha=0.3)

    # Accuracy curve
    ax2.plot(accuracy_history, color='green', linewidth=2)
    ax2.set_xlabel('Epoch')
    ax2.set_ylabel('Accuracy')
    ax2.set_title('Training Accuracy Over Time')
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim([0, 1])

    plt.tight_layout()

    # Save to file
    output_path = 'output/even_odd_learning_curves.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✅ Saved learning curves to: {output_path}")

    # Try to display (might not work in headless environment)
    try:
        plt.show(block=False)
        plt.pause(0.1)
    except:
        pass

    return fig


if __name__ == '__main__':
    np.random.seed(42)  # Reproducible results
    test_even_odd_classification()

    print()
    print("=" * 70)
    print("PROOF THAT BACKPROPAGATION WORKS")
    print("=" * 70)
    print()
    print("If you see:")
    print("  - Loss DECREASING over epochs → Gradient descent working")
    print("  - Accuracy INCREASING over epochs → Network learning")
    print("  - Test accuracy > 95% → Network generalized")
    print()
    print("This proves the neural network is ACTUALLY LEARNING,")
    print("not just returning templates!")
    print()
