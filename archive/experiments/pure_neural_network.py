#!/usr/bin/env python3
"""
Pure Python Neural Network - ZERO Dependencies

Demonstrates that we can build a complete neural network using
ONLY Python stdlib - no numpy, no tensorflow, no torch!

This is the foundation for the neural network marketplace:
- Each "brand" (CalRiven, TheAuditor, DeathToData, Soulfra) is just a trained network
- Networks are pure Python lists - no external dependencies
- Training happens through user feedback (you click correct/wrong)
- Everything is transparent and auditable

Philosophy:
-----------
Neural networks are just:
1. Matrix multiplication (nested loops)
2. Activation functions (math.exp, math.tanh)
3. Backpropagation (calculus + loops)

NO MAGIC. Just math we can understand and build ourselves.

Usage:
  python3 pure_neural_network.py
"""

import math
import random
import json


# ==============================================================================
# 1. MATH UTILITIES (Zero Dependencies)
# ==============================================================================

def sigmoid(x):
    """Sigmoid activation: σ(x) = 1 / (1 + e^(-x))"""
    try:
        return 1.0 / (1.0 + math.exp(-x))
    except OverflowError:
        return 0.0 if x < 0 else 1.0


def sigmoid_derivative(x):
    """Derivative of sigmoid: σ'(x) = σ(x) * (1 - σ(x))"""
    s = sigmoid(x)
    return s * (1 - s)


def tanh(x):
    """Hyperbolic tangent: tanh(x) = (e^x - e^(-x)) / (e^x + e^(-x))"""
    return math.tanh(x)


def tanh_derivative(x):
    """Derivative of tanh: tanh'(x) = 1 - tanh²(x)"""
    t = tanh(x)
    return 1 - t * t


def dot_product(a, b):
    """Dot product of two vectors: a · b = Σ(a_i * b_i)"""
    return sum(x * y for x, y in zip(a, b))


def matrix_multiply(matrix, vector):
    """
    Matrix-vector multiplication

    matrix: [[w11, w12, ...], [w21, w22, ...], ...]
    vector: [x1, x2, ...]

    Returns: [y1, y2, ...] where y_i = Σ(matrix[i][j] * vector[j])
    """
    return [dot_product(row, vector) for row in matrix]


# ==============================================================================
# 2. NEURAL NETWORK (Zero Dependencies)
# ==============================================================================

class PureNeuralNetwork:
    """
    Pure Python Neural Network

    Architecture:
    - Input layer: n inputs
    - Hidden layer: m neurons
    - Output layer: k outputs

    No numpy! Just Python lists and math module.
    """

    def __init__(self, input_size, hidden_size, output_size, learning_rate=0.1):
        """
        Initialize network with random weights

        Args:
            input_size: Number of input features
            hidden_size: Number of neurons in hidden layer
            output_size: Number of output neurons
            learning_rate: Step size for weight updates
        """
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.learning_rate = learning_rate

        # Initialize weights randomly in range [-0.5, 0.5]
        # weights_ih: Input → Hidden (hidden_size x input_size)
        self.weights_ih = [
            [random.uniform(-0.5, 0.5) for _ in range(input_size)]
            for _ in range(hidden_size)
        ]

        # weights_ho: Hidden → Output (output_size x hidden_size)
        self.weights_ho = [
            [random.uniform(-0.5, 0.5) for _ in range(hidden_size)]
            for _ in range(output_size)
        ]

        # Biases
        self.bias_h = [random.uniform(-0.5, 0.5) for _ in range(hidden_size)]
        self.bias_o = [random.uniform(-0.5, 0.5) for _ in range(output_size)]

        # Training history
        self.loss_history = []
        self.total_trained = 0
        self.correct = 0

    def forward(self, inputs):
        """
        Forward pass: inputs → hidden → output

        Args:
            inputs: List of input values [x1, x2, ...]

        Returns:
            (hidden_outputs, final_outputs)
        """
        # Hidden layer
        hidden_raw = matrix_multiply(self.weights_ih, inputs)
        hidden_biased = [h + b for h, b in zip(hidden_raw, self.bias_h)]
        hidden_outputs = [sigmoid(x) for x in hidden_biased]

        # Output layer
        output_raw = matrix_multiply(self.weights_ho, hidden_outputs)
        output_biased = [o + b for o, b in zip(output_raw, self.bias_o)]
        final_outputs = [sigmoid(x) for x in output_biased]

        return hidden_outputs, final_outputs

    def predict(self, inputs):
        """
        Make a prediction

        Args:
            inputs: List of input values

        Returns:
            List of output values (probabilities if using sigmoid)
        """
        _, outputs = self.forward(inputs)
        return outputs

    def train(self, inputs, targets):
        """
        Train on a single example using backpropagation

        Args:
            inputs: List of input values [x1, x2, ...]
            targets: List of target values [y1, y2, ...]

        Returns:
            loss: Mean squared error for this example
        """
        # Forward pass
        hidden_outputs, final_outputs = self.forward(inputs)

        # Calculate loss (Mean Squared Error)
        errors = [t - o for t, o in zip(targets, final_outputs)]
        loss = sum(e * e for e in errors) / len(errors)

        # Backward pass (backpropagation)

        # Output layer gradients
        output_gradients = [
            e * sigmoid_derivative(o)
            for e, o in zip(errors, final_outputs)
        ]

        # Hidden layer gradients
        hidden_errors = [
            sum(
                output_gradients[i] * self.weights_ho[i][j]
                for i in range(self.output_size)
            )
            for j in range(self.hidden_size)
        ]

        hidden_gradients = [
            e * sigmoid_derivative(h)
            for e, h in zip(hidden_errors, hidden_outputs)
        ]

        # Update weights: Hidden → Output
        for i in range(self.output_size):
            for j in range(self.hidden_size):
                delta = self.learning_rate * output_gradients[i] * hidden_outputs[j]
                self.weights_ho[i][j] += delta

        # Update biases: Output
        for i in range(self.output_size):
            self.bias_o[i] += self.learning_rate * output_gradients[i]

        # Update weights: Input → Hidden
        for i in range(self.hidden_size):
            for j in range(self.input_size):
                delta = self.learning_rate * hidden_gradients[i] * inputs[j]
                self.weights_ih[i][j] += delta

        # Update biases: Hidden
        for i in range(self.hidden_size):
            self.bias_h[i] += self.learning_rate * hidden_gradients[i]

        # Track training stats
        self.loss_history.append(loss)
        self.total_trained += 1

        # Check if prediction was correct (for binary classification)
        if len(targets) == 1:
            predicted_class = 1 if final_outputs[0] > 0.5 else 0
            target_class = 1 if targets[0] > 0.5 else 0
            if predicted_class == target_class:
                self.correct += 1

        return loss

    def get_accuracy(self):
        """Calculate training accuracy"""
        if self.total_trained == 0:
            return 0.0
        return self.correct / self.total_trained

    def save(self, filename):
        """Save network to JSON file"""
        data = {
            'input_size': self.input_size,
            'hidden_size': self.hidden_size,
            'output_size': self.output_size,
            'learning_rate': self.learning_rate,
            'weights_ih': self.weights_ih,
            'weights_ho': self.weights_ho,
            'bias_h': self.bias_h,
            'bias_o': self.bias_o,
            'loss_history': self.loss_history,
            'total_trained': self.total_trained,
            'correct': self.correct
        }

        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, filename):
        """Load network from JSON file"""
        with open(filename, 'r') as f:
            data = json.load(f)

        network = cls(
            data['input_size'],
            data['hidden_size'],
            data['output_size'],
            data['learning_rate']
        )

        network.weights_ih = data['weights_ih']
        network.weights_ho = data['weights_ho']
        network.bias_h = data['bias_h']
        network.bias_o = data['bias_o']
        network.loss_history = data['loss_history']
        network.total_trained = data['total_trained']
        network.correct = data['correct']

        return network


# ==============================================================================
# 3. DEMONSTRATION: XOR Problem
# ==============================================================================

def demo_xor():
    """
    Train a neural network to solve XOR

    XOR truth table:
    0 XOR 0 = 0
    0 XOR 1 = 1
    1 XOR 0 = 1
    1 XOR 1 = 0

    This is the classic test for neural networks because
    XOR is not linearly separable (you need a hidden layer).
    """
    print("=" * 70)
    print("PURE PYTHON NEURAL NETWORK - XOR DEMONSTRATION")
    print("=" * 70)
    print()
    print("Training a neural network to solve XOR using ZERO dependencies!")
    print("Just Python lists and the math module.")
    print()

    # Training data
    training_data = [
        ([0, 0], [0]),
        ([0, 1], [1]),
        ([1, 0], [1]),
        ([1, 1], [0])
    ]

    # Create network: 2 inputs → 4 hidden neurons → 1 output
    network = PureNeuralNetwork(
        input_size=2,
        hidden_size=4,
        output_size=1,
        learning_rate=0.5
    )

    print("Network Architecture:")
    print(f"  Input layer:  {network.input_size} neurons")
    print(f"  Hidden layer: {network.hidden_size} neurons")
    print(f"  Output layer: {network.output_size} neuron")
    print()
    print("Training...")
    print()

    # Train for 10,000 epochs
    for epoch in range(10000):
        total_loss = 0

        # Shuffle training data
        random.shuffle(training_data)

        # Train on each example
        for inputs, targets in training_data:
            loss = network.train(inputs, targets)
            total_loss += loss

        # Print progress every 1000 epochs
        if (epoch + 1) % 1000 == 0:
            avg_loss = total_loss / len(training_data)
            print(f"Epoch {epoch + 1:5d} | Loss: {avg_loss:.6f}")

    print()
    print("Training complete!")
    print()
    print("Testing XOR predictions:")
    print("-" * 50)

    for inputs, expected in training_data:
        prediction = network.predict(inputs)
        predicted_value = prediction[0]
        predicted_class = 1 if predicted_value > 0.5 else 0

        print(f"{inputs[0]} XOR {inputs[1]} = {expected[0]}")
        print(f"  Predicted: {predicted_value:.4f} → {predicted_class}")
        print(f"  Correct: {'✓' if predicted_class == expected[0] else '✗'}")
        print()

    print("=" * 70)
    print("SUCCESS! We built a neural network with ZERO dependencies!")
    print()
    print("What just happened:")
    print("  ✅ Matrix multiplication: nested loops (no numpy)")
    print("  ✅ Activation functions: math.exp (no tensorflow)")
    print("  ✅ Backpropagation: calculus + loops (no torch)")
    print("  ✅ Saved to JSON: json module (no pickle)")
    print()
    print("This is the EXACT same math that powers:")
    print("  - CalRiven (technical analysis)")
    print("  - TheAuditor (validation)")
    print("  - DeathToData (privacy)")
    print("  - Soulfra (meta-judgment)")
    print()
    print("We can build EVERYTHING ourselves! 🚀")
    print("=" * 70)

    # Save the trained network
    network.save('xor_network.json')
    print()
    print("Saved trained network to: xor_network.json")


# ==============================================================================
# 4. DEMONSTRATION: Color Classification
# ==============================================================================

def demo_color_classification():
    """
    Train a neural network to classify colors as warm vs cool

    This connects to the color training interface!
    """
    print()
    print("=" * 70)
    print("COLOR CLASSIFICATION DEMONSTRATION")
    print("=" * 70)
    print()
    print("Training a network to classify colors as WARM vs COOL")
    print()

    # Training data: RGB → warm(1) or cool(0)
    training_data = [
        # Warm colors (red, orange, yellow)
        ([1.0, 0.0, 0.0], [1]),  # Red
        ([1.0, 0.5, 0.0], [1]),  # Orange
        ([1.0, 1.0, 0.0], [1]),  # Yellow
        ([1.0, 0.0, 0.5], [1]),  # Pink
        ([0.8, 0.2, 0.0], [1]),  # Dark orange

        # Cool colors (blue, cyan, green)
        ([0.0, 0.0, 1.0], [0]),  # Blue
        ([0.0, 1.0, 1.0], [0]),  # Cyan
        ([0.0, 1.0, 0.0], [0]),  # Green
        ([0.0, 0.5, 1.0], [0]),  # Sky blue
        ([0.0, 0.8, 0.8], [0]),  # Turquoise
    ]

    # Create network: 3 inputs (RGB) → 6 hidden → 1 output
    network = PureNeuralNetwork(
        input_size=3,
        hidden_size=6,
        output_size=1,
        learning_rate=0.3
    )

    print("Network Architecture:")
    print(f"  Input layer:  {network.input_size} neurons (R, G, B)")
    print(f"  Hidden layer: {network.hidden_size} neurons")
    print(f"  Output layer: {network.output_size} neuron (warm/cool)")
    print()
    print("Training...")
    print()

    # Train for 5,000 epochs
    for epoch in range(5000):
        total_loss = 0
        random.shuffle(training_data)

        for inputs, targets in training_data:
            loss = network.train(inputs, targets)
            total_loss += loss

        if (epoch + 1) % 500 == 0:
            avg_loss = total_loss / len(training_data)
            accuracy = network.get_accuracy()
            print(f"Epoch {epoch + 1:4d} | Loss: {avg_loss:.6f} | Accuracy: {accuracy * 100:.1f}%")

    print()
    print("Testing on training colors:")
    print("-" * 50)

    for inputs, expected in training_data:
        prediction = network.predict(inputs)
        predicted_value = prediction[0]
        predicted_class = "WARM" if predicted_value > 0.5 else "COOL"
        expected_class = "WARM" if expected[0] == 1 else "COOL"

        r, g, b = [int(c * 255) for c in inputs]
        print(f"RGB({r:3d}, {g:3d}, {b:3d}) → {expected_class}")
        print(f"  Predicted: {predicted_value:.4f} → {predicted_class}")
        print(f"  Correct: {'✓' if predicted_class == expected_class else '✗'}")
        print()

    # Test on new colors
    print()
    print("Testing on NEW colors (not in training data):")
    print("-" * 50)

    test_colors = [
        ([0.9, 0.3, 0.1], "WARM (reddish orange)"),
        ([0.1, 0.3, 0.9], "COOL (blue)"),
        ([1.0, 0.8, 0.0], "WARM (gold)"),
        ([0.0, 0.6, 0.6], "COOL (teal)"),
    ]

    for inputs, description in test_colors:
        prediction = network.predict(inputs)
        predicted_value = prediction[0]
        predicted_class = "WARM" if predicted_value > 0.5 else "COOL"

        r, g, b = [int(c * 255) for c in inputs]
        print(f"RGB({r:3d}, {g:3d}, {b:3d}) - {description}")
        print(f"  Predicted: {predicted_value:.4f} → {predicted_class}")
        print()

    # Save
    network.save('color_network.json')
    print("Saved trained network to: color_network.json")
    print()
    print("=" * 70)


# ==============================================================================
# 5. MAIN
# ==============================================================================

if __name__ == '__main__':
    # Run XOR demo
    demo_xor()

    # Run color classification demo
    demo_color_classification()

    print()
    print("🎉 Both demonstrations complete!")
    print()
    print("Key takeaways:")
    print("  1. Neural networks are just math (no magic)")
    print("  2. We can build everything with Python stdlib")
    print("  3. No external dependencies = full control")
    print("  4. This is the foundation for the neural network marketplace")
    print()
    print("Next steps:")
    print("  - Integrate with soulfra_zero.py (web interface)")
    print("  - Train CalRiven, TheAuditor, DeathToData models")
    print("  - Let users train via clicking correct/wrong")
    print("  - Build the 'hello world per brand' system")
    print()
