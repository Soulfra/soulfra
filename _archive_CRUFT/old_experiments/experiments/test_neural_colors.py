#!/usr/bin/env python3
"""
Test Neural Network: Color Classification (Warm vs Cool)

Trains neural network to classify RGB colors as "warm" or "cool".
This demonstrates learning on continuous features (not just binary).

Warm colors: Red, Orange, Yellow (high R, low B)
Cool colors: Blue, Green, Cyan (high B/G, low R)
"""

import numpy as np
import matplotlib.pyplot as plt
from neural_network import NeuralNetwork, save_neural_network


def generate_color_data(n_samples=1000):
    """
    Generate RGB color data with warm/cool labels

    Warm: Red/Orange/Yellow (R > 150, B < 100)
    Cool: Blue/Green/Cyan (B > 150, R < 100)
    """
    X = []
    y = []

    for _ in range(n_samples // 2):
        # Warm color
        r = np.random.randint(150, 256)
        g = np.random.randint(50, 200)
        b = np.random.randint(0, 100)
        X.append([r/255, g/255, b/255])  # Normalize to [0, 1]
        y.append([1])  # Warm = 1

        # Cool color
        r = np.random.randint(0, 100)
        g = np.random.randint(100, 256)
        b = np.random.randint(150, 256)
        X.append([r/255, g/255, b/255])
        y.append([0])  # Cool = 0

    X = np.array(X)
    y = np.array(y)

    # Shuffle
    indices = np.random.permutation(len(X))
    X = X[indices]
    y = y[indices]

    return X, y


def test_color_classification():
    """
    Train neural network to classify warm vs cool colors
    """
    print("=" * 70)
    print("NEURAL NETWORK TEST: Warm vs Cool Color Classification")
    print("=" * 70)
    print()

    # Generate data
    print("Generating color data...")
    X_train, y_train = generate_color_data(n_samples=1000)
    X_test, y_test = generate_color_data(n_samples=200)

    print(f"Training samples: {X_train.shape[0]}")
    print(f"Test samples: {X_test.shape[0]}")
    print()

    # Create neural network
    print("Creating neural network...")
    print("  Architecture: 3 inputs (RGB) → 32 hidden → 1 output")
    print("  Activation: ReLU (hidden), Sigmoid (output)")
    print()

    nn = NeuralNetwork(
        input_size=3,
        hidden_sizes=[32],
        output_size=1,
        activation='relu',
        output_activation='sigmoid'
    )

    # Train
    print("Training...")
    print()
    nn.train(X_train, y_train, epochs=100, learning_rate=0.01, batch_size=32, verbose=True)

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
    print("-" * 80)
    print(f"{'RGB (scaled)':<25} {'True Label':<12} {'Prediction':<12} {'Confidence':<12}")
    print("-" * 80)

    for i in range(min(10, len(X_test))):
        rgb = X_test[i] * 255  # Scale back to [0, 255]
        true_label = "Warm" if y_test[i][0] == 1 else "Cool"
        pred_prob = predictions[i][0]
        pred_label = "Warm" if pred_prob > 0.5 else "Cool"
        confidence = pred_prob if pred_prob > 0.5 else (1 - pred_prob)

        correct = "✓" if true_label == pred_label else "✗"
        rgb_str = f"R:{int(rgb[0])} G:{int(rgb[1])} B:{int(rgb[2])}"
        print(f"{rgb_str:<25} {true_label:<12} {pred_label:<12} {confidence:.4f} {correct}")

    print()

    # Plot learning curves
    print("Generating learning curves...")
    plot_learning_curves(nn.loss_history, nn.accuracy_history)

    # Save model
    save_neural_network(nn, 'color_classifier', 'Binary classifier: Warm vs Cool colors (RGB)')

    return nn


def plot_learning_curves(loss_history, accuracy_history):
    """
    Visualize learning curves
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
    output_path = 'output/color_learning_curves.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✅ Saved learning curves to: {output_path}")

    try:
        plt.show(block=False)
        plt.pause(0.1)
    except:
        pass

    return fig


if __name__ == '__main__':
    np.random.seed(42)
    test_color_classification()

    print()
    print("=" * 70)
    print("NEURAL NETWORK LEARNED COLOR PATTERNS")
    print("=" * 70)
    print()
    print("This demonstrates:")
    print("  - Learning on CONTINUOUS features (RGB values 0-255)")
    print("  - Decision boundary: separating warm from cool colors")
    print("  - Generalization: Works on unseen test colors")
    print()
    print("Next: Train on POST classification (bug reports, features, etc.)")
    print()
