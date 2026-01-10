#!/usr/bin/env python3
"""
Soulfra Neural - Pure Python Neural Network for Blog Post Classification

Train neural networks on your blog posts using ONLY Python stdlib.
No NumPy, TensorFlow, PyTorch, or external ML libraries.

Features:
- Text classification (categorize posts)
- Keyword extraction (TF-IDF)
- Neural network training (backpropagation)
- Model storage in SQLite (not pickle files)
- Accuracy tracking and validation

Usage:
    from soulfra_neural import NeuralTrainer

    trainer = NeuralTrainer(db_manager)
    trainer.train_on_posts()
    prediction = trainer.classify("My blog post about AI...")
"""

import math
import random
import json
import re
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Optional, Any


# ==============================================================================
# PURE PYTHON MATH UTILITIES
# ==============================================================================

def sigmoid(x: float) -> float:
    """Sigmoid activation: σ(x) = 1 / (1 + e^(-x))"""
    try:
        return 1.0 / (1.0 + math.exp(-x))
    except OverflowError:
        return 0.0 if x < 0 else 1.0


def sigmoid_derivative(x: float) -> float:
    """Derivative of sigmoid: σ'(x) = σ(x) * (1 - σ(x))"""
    s = sigmoid(x)
    return s * (1 - s)


def dot_product(a: List[float], b: List[float]) -> float:
    """Dot product: a · b = Σ(a_i * b_i)"""
    return sum(x * y for x, y in zip(a, b))


def matrix_vector_multiply(matrix: List[List[float]], vector: List[float]) -> List[float]:
    """Matrix-vector multiplication"""
    return [dot_product(row, vector) for row in matrix]


# ==============================================================================
# TEXT FEATURE EXTRACTION
# ==============================================================================

class TextFeatureExtractor:
    """Extract numerical features from text using TF-IDF"""

    def __init__(self, max_features: int = 100):
        self.max_features = max_features
        self.vocabulary: List[str] = []
        self.idf: Dict[str, float] = {}
        self.stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this',
            'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
        }

    def tokenize(self, text: str) -> List[str]:
        """Tokenize text into words"""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Convert to lowercase, extract words
        words = re.findall(r'\b[a-z]{3,}\b', text.lower())
        # Remove stopwords
        return [w for w in words if w not in self.stopwords]

    def build_vocabulary(self, documents: List[str]):
        """Build vocabulary from documents using TF-IDF"""
        # Count word frequencies across all documents
        word_doc_count = Counter()
        all_words = Counter()

        for doc in documents:
            words = self.tokenize(doc)
            all_words.update(words)
            # Count unique words per document
            unique_words = set(words)
            word_doc_count.update(unique_words)

        # Calculate IDF for each word
        total_docs = len(documents)
        for word, doc_count in word_doc_count.items():
            self.idf[word] = math.log(total_docs / doc_count)

        # Select top N words by IDF
        top_words = sorted(self.idf.items(), key=lambda x: x[1], reverse=True)
        self.vocabulary = [word for word, _ in top_words[:self.max_features]]

    def extract_features(self, text: str) -> List[float]:
        """
        Extract feature vector from text
        Returns vector of length max_features with TF-IDF values
        """
        if not self.vocabulary:
            raise ValueError("Vocabulary not built. Call build_vocabulary() first.")

        words = self.tokenize(text)
        word_counts = Counter(words)
        total_words = len(words) if words else 1

        # Calculate TF-IDF for each vocabulary word
        features = []
        for word in self.vocabulary:
            if word in word_counts:
                tf = word_counts[word] / total_words
                tfidf = tf * self.idf.get(word, 0)
                features.append(tfidf)
            else:
                features.append(0.0)

        return features


# ==============================================================================
# PURE PYTHON NEURAL NETWORK
# ==============================================================================

class PureNeuralNetwork:
    """
    Pure Python Neural Network - ZERO Dependencies

    Architecture: Input → Hidden → Output
    Uses sigmoid activation and backpropagation
    """

    def __init__(self, input_size: int, hidden_size: int, output_size: int, learning_rate: float = 0.1):
        """
        Initialize network with random weights

        Args:
            input_size: Number of input features
            hidden_size: Number of neurons in hidden layer
            output_size: Number of output categories
            learning_rate: Learning rate for gradient descent
        """
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.learning_rate = learning_rate

        # Initialize weights randomly (-0.5 to 0.5)
        self.weights_input_hidden = [
            [random.uniform(-0.5, 0.5) for _ in range(input_size)]
            for _ in range(hidden_size)
        ]
        self.weights_hidden_output = [
            [random.uniform(-0.5, 0.5) for _ in range(hidden_size)]
            for _ in range(output_size)
        ]

        # Biases
        self.bias_hidden = [random.uniform(-0.5, 0.5) for _ in range(hidden_size)]
        self.bias_output = [random.uniform(-0.5, 0.5) for _ in range(output_size)]

    def forward(self, inputs: List[float]) -> List[float]:
        """
        Forward propagation

        Args:
            inputs: Input feature vector

        Returns:
            Output predictions (probabilities for each class)
        """
        # Hidden layer
        self.hidden_inputs = matrix_vector_multiply(self.weights_input_hidden, inputs)
        self.hidden_inputs = [h + b for h, b in zip(self.hidden_inputs, self.bias_hidden)]
        self.hidden_outputs = [sigmoid(h) for h in self.hidden_inputs]

        # Output layer
        self.output_inputs = matrix_vector_multiply(self.weights_hidden_output, self.hidden_outputs)
        self.output_inputs = [o + b for o, b in zip(self.output_inputs, self.bias_output)]
        self.outputs = [sigmoid(o) for o in self.output_inputs]

        return self.outputs

    def backward(self, inputs: List[float], targets: List[float]):
        """
        Backpropagation - update weights based on error

        Args:
            inputs: Input feature vector
            targets: Target output (one-hot encoded)
        """
        # Calculate output layer error
        output_errors = [t - o for t, o in zip(targets, self.outputs)]
        output_deltas = [
            error * sigmoid_derivative(output_input)
            for error, output_input in zip(output_errors, self.output_inputs)
        ]

        # Calculate hidden layer error
        hidden_errors = [
            sum(output_deltas[j] * self.weights_hidden_output[j][i]
                for j in range(self.output_size))
            for i in range(self.hidden_size)
        ]
        hidden_deltas = [
            error * sigmoid_derivative(hidden_input)
            for error, hidden_input in zip(hidden_errors, self.hidden_inputs)
        ]

        # Update weights (hidden → output)
        for j in range(self.output_size):
            for i in range(self.hidden_size):
                self.weights_hidden_output[j][i] += (
                    self.learning_rate * output_deltas[j] * self.hidden_outputs[i]
                )
            self.bias_output[j] += self.learning_rate * output_deltas[j]

        # Update weights (input → hidden)
        for j in range(self.hidden_size):
            for i in range(self.input_size):
                self.weights_input_hidden[j][i] += (
                    self.learning_rate * hidden_deltas[j] * inputs[i]
                )
            self.bias_hidden[j] += self.learning_rate * hidden_deltas[j]

    def train_epoch(self, training_data: List[Tuple[List[float], List[float]]]) -> float:
        """
        Train for one epoch

        Args:
            training_data: List of (inputs, targets) tuples

        Returns:
            Average loss for this epoch
        """
        total_loss = 0.0

        for inputs, targets in training_data:
            # Forward pass
            outputs = self.forward(inputs)

            # Calculate loss (mean squared error)
            loss = sum((t - o) ** 2 for t, o in zip(targets, outputs)) / len(targets)
            total_loss += loss

            # Backward pass
            self.backward(inputs, targets)

        return total_loss / len(training_data)

    def predict(self, inputs: List[float]) -> int:
        """
        Predict class for input

        Args:
            inputs: Input feature vector

        Returns:
            Predicted class index
        """
        outputs = self.forward(inputs)
        return outputs.index(max(outputs))

    def to_dict(self) -> Dict:
        """Serialize network to dictionary"""
        return {
            'input_size': self.input_size,
            'hidden_size': self.hidden_size,
            'output_size': self.output_size,
            'learning_rate': self.learning_rate,
            'weights_input_hidden': self.weights_input_hidden,
            'weights_hidden_output': self.weights_hidden_output,
            'bias_hidden': self.bias_hidden,
            'bias_output': self.bias_output
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'PureNeuralNetwork':
        """Load network from dictionary"""
        net = cls(
            data['input_size'],
            data['hidden_size'],
            data['output_size'],
            data['learning_rate']
        )
        net.weights_input_hidden = data['weights_input_hidden']
        net.weights_hidden_output = data['weights_hidden_output']
        net.bias_hidden = data['bias_hidden']
        net.bias_output = data['bias_output']
        return net


# ==============================================================================
# NEURAL TRAINER - Train on Blog Posts
# ==============================================================================

class NeuralTrainer:
    """Train neural networks on blog post content"""

    def __init__(self, db_manager):
        """
        Initialize trainer

        Args:
            db_manager: DatabaseManager instance from soulfra_local
        """
        self.db = db_manager
        self.feature_extractor = TextFeatureExtractor(max_features=50)
        self.network: Optional[PureNeuralNetwork] = None
        self.categories: List[str] = []

    def train_on_posts(self, min_tier: int = 1, epochs: int = 100) -> Dict[str, Any]:
        """
        Train neural network on blog posts

        Args:
            min_tier: Minimum tier of posts to train on
            epochs: Number of training epochs

        Returns:
            Training statistics
        """
        # Get posts
        posts = self.db.get_posts_by_tier(min_tier)

        if len(posts) < 5:
            return {'error': 'Need at least 5 posts to train'}

        # Extract categories from posts (use first word of title as category)
        category_map = defaultdict(list)
        for post in posts:
            # Simple heuristic: first word of title is category
            first_word = post['title'].split()[0].lower() if post['title'] else 'general'
            category_map[first_word].append(post)

        # Keep only categories with at least 2 posts
        self.categories = [cat for cat, posts in category_map.items() if len(posts) >= 2]

        if len(self.categories) < 2:
            return {'error': 'Need at least 2 categories with 2+ posts each'}

        # Build vocabulary from all posts
        all_texts = [post['content'] for post in posts]
        self.feature_extractor.build_vocabulary(all_texts)

        # Prepare training data
        training_data = []
        for post in posts:
            first_word = post['title'].split()[0].lower() if post['title'] else 'general'
            if first_word in self.categories:
                # Extract features
                features = self.feature_extractor.extract_features(post['content'])

                # One-hot encode category
                target = [0.0] * len(self.categories)
                category_index = self.categories.index(first_word)
                target[category_index] = 1.0

                training_data.append((features, target))

        # Initialize network
        self.network = PureNeuralNetwork(
            input_size=len(self.feature_extractor.vocabulary),
            hidden_size=25,
            output_size=len(self.categories),
            learning_rate=0.1
        )

        # Train network
        print(f"🧠 Training network on {len(training_data)} posts...")
        print(f"   Categories: {', '.join(self.categories)}")
        print(f"   Features: {len(self.feature_extractor.vocabulary)} keywords")

        losses = []
        for epoch in range(epochs):
            loss = self.network.train_epoch(training_data)
            losses.append(loss)

            if epoch % 20 == 0:
                print(f"   Epoch {epoch}/{epochs}, Loss: {loss:.4f}")

        # Calculate accuracy
        correct = 0
        for inputs, targets in training_data:
            prediction = self.network.predict(inputs)
            actual = targets.index(1.0)
            if prediction == actual:
                correct += 1

        accuracy = correct / len(training_data)

        print(f"\n✅ Training complete!")
        print(f"   Final loss: {losses[-1]:.4f}")
        print(f"   Accuracy: {accuracy * 100:.1f}%")

        # Save to database
        self._save_network()

        return {
            'categories': self.categories,
            'vocabulary_size': len(self.feature_extractor.vocabulary),
            'training_examples': len(training_data),
            'epochs': epochs,
            'final_loss': losses[-1],
            'accuracy': accuracy
        }

    def classify(self, text: str) -> Dict[str, Any]:
        """
        Classify text using trained network

        Args:
            text: Text to classify

        Returns:
            Classification results with confidence scores
        """
        if not self.network or not self.categories:
            # Try to load from database
            if not self._load_network():
                return {'error': 'No trained network found. Run train_on_posts() first.'}

        # Extract features
        features = self.feature_extractor.extract_features(text)

        # Get predictions
        outputs = self.network.forward(features)

        # Get predicted category
        predicted_index = outputs.index(max(outputs))
        predicted_category = self.categories[predicted_index]
        confidence = outputs[predicted_index]

        # Get all scores
        scores = {cat: score for cat, score in zip(self.categories, outputs)}

        return {
            'category': predicted_category,
            'confidence': confidence,
            'all_scores': scores
        }

    def _save_network(self):
        """Save network to database"""
        if not self.network:
            return

        network_data = {
            'network': self.network.to_dict(),
            'categories': self.categories,
            'vocabulary': self.feature_extractor.vocabulary,
            'idf': self.feature_extractor.idf
        }

        cursor = self.db.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO neural_networks (name, weights, accuracy, training_examples)
            VALUES ('blog_classifier', ?, ?, ?)
        ''', (
            json.dumps(network_data),
            0.0,  # Will be updated during training
            0     # Will be updated during training
        ))
        self.db.conn.commit()

    def _load_network(self) -> bool:
        """Load network from database"""
        cursor = self.db.conn.cursor()
        cursor.execute('SELECT weights FROM neural_networks WHERE name = ?', ('blog_classifier',))
        row = cursor.fetchone()

        if not row:
            return False

        network_data = json.loads(row['weights'])
        self.network = PureNeuralNetwork.from_dict(network_data['network'])
        self.categories = network_data['categories']
        self.feature_extractor.vocabulary = network_data['vocabulary']
        self.feature_extractor.idf = network_data['idf']

        return True


if __name__ == '__main__':
    print("🧠 Soulfra Neural - Pure Python Neural Network")
    print("Import this module into soulfra_local.py to train on blog posts")
    print("\nExample usage:")
    print("  from soulfra_neural import NeuralTrainer")
    print("  trainer = NeuralTrainer(db_manager)")
    print("  trainer.train_on_posts()")
    print("  result = trainer.classify('Your blog post text...')")
