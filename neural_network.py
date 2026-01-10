#!/usr/bin/env python3
"""
Neural Network from Scratch
Build a real neural network with backpropagation, gradient descent, and loss functions.

Uses numpy for matrix operations but shows all the math.
No TensorFlow, PyTorch, or sklearn - just pure implementation.

Theory:
- Forward propagation: Input → Layers → Output
- Backpropagation: Calculate gradients using chain rule
- Gradient descent: Update weights to minimize loss
- Activation functions: Non-linear transformations
- Loss functions: Measure prediction error
"""

import numpy as np
import json
from datetime import datetime
from database import get_db


# =============================================================================
# ACTIVATION FUNCTIONS
# =============================================================================

def sigmoid(x):
    """
    Sigmoid: σ(x) = 1 / (1 + e^(-x))
    Output range: (0, 1)
    Use case: Binary classification, probability outputs
    """
    return 1 / (1 + np.exp(-np.clip(x, -500, 500)))  # Clip to prevent overflow


def sigmoid_derivative(x):
    """
    Derivative: σ'(x) = σ(x) * (1 - σ(x))
    """
    s = sigmoid(x)
    return s * (1 - s)


def relu(x):
    """
    ReLU: max(0, x)
    Output range: [0, ∞)
    Use case: Hidden layers (fast, prevents vanishing gradient)
    """
    return np.maximum(0, x)


def relu_derivative(x):
    """
    Derivative: 1 if x > 0, else 0
    """
    return (x > 0).astype(float)


def tanh(x):
    """
    Tanh: (e^x - e^(-x)) / (e^x + e^(-x))
    Output range: (-1, 1)
    Use case: Hidden layers (zero-centered)
    """
    return np.tanh(x)


def tanh_derivative(x):
    """
    Derivative: 1 - tanh²(x)
    """
    return 1 - np.tanh(x) ** 2


def softmax(x):
    """
    Softmax: e^(x_i) / Σ(e^(x_j))
    Output range: (0, 1), sums to 1
    Use case: Multi-class classification (probabilities)
    """
    exp_x = np.exp(x - np.max(x, axis=-1, keepdims=True))  # Numerical stability
    return exp_x / np.sum(exp_x, axis=-1, keepdims=True)


# =============================================================================
# LOSS FUNCTIONS
# =============================================================================

def binary_cross_entropy(y_true, y_pred, epsilon=1e-15):
    """
    Binary Cross-Entropy Loss: -[y*log(ŷ) + (1-y)*log(1-ŷ)]
    Use case: Binary classification
    """
    y_pred = np.clip(y_pred, epsilon, 1 - epsilon)  # Prevent log(0)
    return -np.mean(y_true * np.log(y_pred) + (1 - y_true) * np.log(1 - y_pred))


def categorical_cross_entropy(y_true, y_pred, epsilon=1e-15):
    """
    Categorical Cross-Entropy Loss: -Σ(y * log(ŷ))
    Use case: Multi-class classification
    """
    y_pred = np.clip(y_pred, epsilon, 1 - epsilon)
    return -np.mean(np.sum(y_true * np.log(y_pred), axis=-1))


def mean_squared_error(y_true, y_pred):
    """
    MSE: (1/n) * Σ(y - ŷ)²
    Use case: Regression
    """
    return np.mean((y_true - y_pred) ** 2)


# =============================================================================
# NEURAL NETWORK CLASS
# =============================================================================

class NeuralNetwork:
    """
    Simple feedforward neural network with backpropagation

    Architecture:
    - Input layer (dynamic size)
    - Hidden layers (configurable)
    - Output layer (dynamic size)

    Example:
        nn = NeuralNetwork(input_size=10, hidden_sizes=[64, 32], output_size=3)
        nn.train(X_train, y_train, epochs=100, learning_rate=0.01)
        predictions = nn.predict(X_test)
    """

    def __init__(self, input_size, hidden_sizes, output_size, activation='relu', output_activation='sigmoid'):
        """
        Initialize network with random weights

        Args:
            input_size: Number of input features
            hidden_sizes: List of hidden layer sizes [64, 32]
            output_size: Number of output neurons
            activation: 'relu', 'sigmoid', or 'tanh'
            output_activation: 'sigmoid' for binary, 'softmax' for multi-class
        """
        self.input_size = input_size
        self.hidden_sizes = hidden_sizes
        self.output_size = output_size
        self.activation_name = activation
        self.output_activation_name = output_activation

        # Set activation functions
        if activation == 'relu':
            self.activation = relu
            self.activation_derivative = relu_derivative
        elif activation == 'sigmoid':
            self.activation = sigmoid
            self.activation_derivative = sigmoid_derivative
        elif activation == 'tanh':
            self.activation = tanh
            self.activation_derivative = tanh_derivative

        # Set output activation
        if output_activation == 'sigmoid':
            self.output_activation = sigmoid
            self.output_activation_derivative = sigmoid_derivative
        elif output_activation == 'softmax':
            self.output_activation = softmax
            # Softmax derivative handled differently (combined with cross-entropy)
            self.output_activation_derivative = None

        # Initialize weights and biases
        self.weights = []
        self.biases = []

        # Input → First hidden layer
        layer_sizes = [input_size] + hidden_sizes + [output_size]

        for i in range(len(layer_sizes) - 1):
            # Xavier initialization: weights ~ N(0, sqrt(2 / (n_in + n_out)))
            weight = np.random.randn(layer_sizes[i], layer_sizes[i+1]) * np.sqrt(2.0 / (layer_sizes[i] + layer_sizes[i+1]))
            bias = np.zeros((1, layer_sizes[i+1]))

            self.weights.append(weight)
            self.biases.append(bias)

        # Training history
        self.loss_history = []
        self.accuracy_history = []

    def forward(self, X):
        """
        Forward propagation

        Args:
            X: Input data (batch_size, input_size)

        Returns:
            Output predictions, and cache of intermediate values for backprop
        """
        cache = {'A0': X}  # Store activations
        A = X

        # Forward through hidden layers
        for i in range(len(self.weights) - 1):
            Z = np.dot(A, self.weights[i]) + self.biases[i]  # Linear transformation
            A = self.activation(Z)  # Non-linear activation
            cache[f'Z{i+1}'] = Z
            cache[f'A{i+1}'] = A

        # Output layer
        Z_out = np.dot(A, self.weights[-1]) + self.biases[-1]
        A_out = self.output_activation(Z_out)
        cache[f'Z{len(self.weights)}'] = Z_out
        cache[f'A{len(self.weights)}'] = A_out

        return A_out, cache

    def backward(self, X, y, cache):
        """
        Backpropagation - calculate gradients using chain rule

        Args:
            X: Input data
            y: True labels
            cache: Forward pass activations

        Returns:
            weight_gradients, bias_gradients
        """
        m = X.shape[0]  # Batch size

        weight_grads = []
        bias_grads = []

        # Output layer gradient
        A_out = cache[f'A{len(self.weights)}']

        # For softmax + categorical cross-entropy, gradient simplifies to: y_pred - y_true
        if self.output_activation_name == 'softmax':
            dZ = A_out - y
        else:
            # For sigmoid/other activations
            dA = -(y / A_out - (1 - y) / (1 - A_out))  # Derivative of loss w.r.t. activation
            Z_out = cache[f'Z{len(self.weights)}']
            dZ = dA * self.output_activation_derivative(Z_out)

        # Gradient for last layer
        A_prev = cache[f'A{len(self.weights) - 1}']
        dW = (1/m) * np.dot(A_prev.T, dZ)
        db = (1/m) * np.sum(dZ, axis=0, keepdims=True)

        weight_grads.append(dW)
        bias_grads.append(db)

        # Backpropagate through hidden layers
        for i in range(len(self.weights) - 2, -1, -1):
            dA = np.dot(dZ, self.weights[i+1].T)
            Z = cache[f'Z{i+1}']
            dZ = dA * self.activation_derivative(Z)

            A_prev = cache[f'A{i}']
            dW = (1/m) * np.dot(A_prev.T, dZ)
            db = (1/m) * np.sum(dZ, axis=0, keepdims=True)

            weight_grads.append(dW)
            bias_grads.append(db)

        # Reverse to match layer order
        weight_grads.reverse()
        bias_grads.reverse()

        return weight_grads, bias_grads

    def update_weights(self, weight_grads, bias_grads, learning_rate):
        """
        Gradient descent: w = w - α * ∇w

        Args:
            weight_grads: List of weight gradients
            bias_grads: List of bias gradients
            learning_rate: Step size (α)
        """
        for i in range(len(self.weights)):
            self.weights[i] -= learning_rate * weight_grads[i]
            self.biases[i] -= learning_rate * bias_grads[i]

    def train(self, X, y, epochs=100, learning_rate=0.01, batch_size=32, verbose=True):
        """
        Train the neural network

        Args:
            X: Training data (n_samples, n_features)
            y: Labels (n_samples, n_outputs)
            epochs: Number of training iterations
            learning_rate: Learning rate (α)
            batch_size: Mini-batch size
            verbose: Print progress

        Returns:
            loss_history, accuracy_history
        """
        n_samples = X.shape[0]

        for epoch in range(epochs):
            # Shuffle data
            indices = np.random.permutation(n_samples)
            X_shuffled = X[indices]
            y_shuffled = y[indices]

            # Mini-batch gradient descent
            epoch_loss = 0
            for i in range(0, n_samples, batch_size):
                X_batch = X_shuffled[i:i+batch_size]
                y_batch = y_shuffled[i:i+batch_size]

                # Forward pass
                predictions, cache = self.forward(X_batch)

                # Calculate loss
                if self.output_activation_name == 'softmax':
                    batch_loss = categorical_cross_entropy(y_batch, predictions)
                elif self.output_size == 1:
                    batch_loss = binary_cross_entropy(y_batch, predictions)
                else:
                    batch_loss = mean_squared_error(y_batch, predictions)

                epoch_loss += batch_loss

                # Backward pass
                weight_grads, bias_grads = self.backward(X_batch, y_batch, cache)

                # Update weights
                self.update_weights(weight_grads, bias_grads, learning_rate)

            # Average loss for epoch
            avg_loss = epoch_loss / (n_samples / batch_size)
            self.loss_history.append(avg_loss)

            # Calculate accuracy
            train_predictions, _ = self.forward(X)
            accuracy = self.calculate_accuracy(y, train_predictions)
            self.accuracy_history.append(accuracy)

            if verbose and (epoch % 10 == 0 or epoch == epochs - 1):
                print(f"Epoch {epoch}/{epochs} - Loss: {avg_loss:.4f}, Accuracy: {accuracy:.4f}")

        return self.loss_history, self.accuracy_history

    def predict(self, X):
        """
        Make predictions

        Args:
            X: Input data

        Returns:
            Predictions
        """
        predictions, _ = self.forward(X)
        return predictions

    def calculate_accuracy(self, y_true, y_pred):
        """
        Calculate classification accuracy
        """
        if self.output_size == 1:
            # Binary classification
            predictions = (y_pred > 0.5).astype(int)
            return np.mean(predictions == y_true)
        else:
            # Multi-class classification
            predictions = np.argmax(y_pred, axis=1)
            true_labels = np.argmax(y_true, axis=1)
            return np.mean(predictions == true_labels)

    def to_dict(self):
        """
        Serialize network to dict (for database storage)
        """
        return {
            'input_size': self.input_size,
            'hidden_sizes': self.hidden_sizes,
            'output_size': self.output_size,
            'activation': self.activation_name,
            'output_activation': self.output_activation_name,
            'weights': [w.tolist() for w in self.weights],
            'biases': [b.tolist() for b in self.biases],
            'loss_history': self.loss_history,
            'accuracy_history': self.accuracy_history
        }

    @classmethod
    def from_dict(cls, data):
        """
        Load network from dict
        """
        nn = cls(
            input_size=data['input_size'],
            hidden_sizes=data['hidden_sizes'],
            output_size=data['output_size'],
            activation=data['activation'],
            output_activation=data['output_activation']
        )
        nn.weights = [np.array(w) for w in data['weights']]
        nn.biases = [np.array(b) for b in data['biases']]
        nn.loss_history = data.get('loss_history', [])
        nn.accuracy_history = data.get('accuracy_history', [])
        return nn


# =============================================================================
# DATABASE STORAGE
# =============================================================================

def save_neural_network(network, model_name, description=''):
    """
    Save trained neural network to database
    """
    db = get_db()

    model_data = network.to_dict()

    db.execute('''
        CREATE TABLE IF NOT EXISTS neural_networks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_name TEXT NOT NULL UNIQUE,
            description TEXT,
            input_size INTEGER,
            hidden_sizes TEXT,
            output_size INTEGER,
            model_data TEXT,
            trained_at TEXT
        )
    ''')

    db.execute('''
        INSERT OR REPLACE INTO neural_networks
        (model_name, description, input_size, hidden_sizes, output_size, model_data, trained_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        model_name,
        description,
        network.input_size,
        json.dumps(network.hidden_sizes),
        network.output_size,
        json.dumps(model_data),
        datetime.now().isoformat()
    ))

    db.commit()
    db.close()
    print(f"✅ Saved neural network '{model_name}' to database")


def load_neural_network(model_name):
    """
    Load trained neural network from database
    """
    db = get_db()

    row = db.execute(
        'SELECT model_data FROM neural_networks WHERE model_name = ?',
        (model_name,)
    ).fetchone()

    db.close()

    if not row:
        raise ValueError(f"Model '{model_name}' not found in database")

    model_data = json.loads(row['model_data'])
    network = NeuralNetwork.from_dict(model_data)

    print(f"✅ Loaded neural network '{model_name}' from database")
    return network


if __name__ == '__main__':
    print("=" * 70)
    print("NEURAL NETWORK FROM SCRATCH")
    print("=" * 70)
    print()
    print("This module provides:")
    print("  - Activation functions: sigmoid, ReLU, tanh, softmax")
    print("  - Loss functions: binary cross-entropy, categorical cross-entropy, MSE")
    print("  - Backpropagation with chain rule")
    print("  - Gradient descent optimizer")
    print("  - Database storage (no pickle files)")
    print()
    print("Example usage:")
    print("  nn = NeuralNetwork(input_size=10, hidden_sizes=[64, 32], output_size=3)")
    print("  nn.train(X_train, y_train, epochs=100, learning_rate=0.01)")
    print("  predictions = nn.predict(X_test)")
    print()
