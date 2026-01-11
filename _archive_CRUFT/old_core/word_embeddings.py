#!/usr/bin/env python3
"""
Word Embeddings from Scratch - Word2Vec Style
Build word embeddings using YOUR controlled vocabulary.

Theory:
- Word2Vec (Skip-gram): Predict context words from target word
- Embedding: Dense vector representation of words
- Similar words → Similar vectors (measured by cosine similarity)
- No pre-trained models - train on YOUR words only

Algorithm:
1. Build vocabulary from wordlist
2. Generate training pairs (word, context)
3. Train 2-layer neural network
4. Extract embedding layer as word vectors

Math:
- Input: One-hot encoded word (vocab_size,)
- Hidden: Dense embedding (embedding_dim,)
- Output: Context word probabilities (vocab_size,)
- Loss: Cross-entropy between predicted & actual context
"""

import numpy as np
import json
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from pathlib import Path


class WordEmbeddings:
    """
    Word2Vec-style word embeddings trained from scratch

    Like Word2Vec Skip-gram but simplified:
    - Train on your controlled vocabulary
    - Learn word relationships through context
    - Export embeddings for downstream tasks
    """

    def __init__(self, vocab_size: int, embedding_dim: int = 50, learning_rate: float = 0.01):
        """
        Initialize embedding matrices

        Args:
            vocab_size: Number of words in vocabulary
            embedding_dim: Dimension of word vectors (50-300 typical)
            learning_rate: Step size for gradient descent
        """
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.learning_rate = learning_rate

        # Initialize weight matrices (small random values)
        # W1: vocab_size → embedding_dim (embedding layer)
        # W2: embedding_dim → vocab_size (output layer)
        self.W1 = np.random.randn(vocab_size, embedding_dim) * 0.01
        self.W2 = np.random.randn(embedding_dim, vocab_size) * 0.01

        # Track training history
        self.training_history = []

        print(f"✅ Initialized Word Embeddings")
        print(f"   Vocab size: {vocab_size}")
        print(f"   Embedding dim: {embedding_dim}")
        print(f"   Total parameters: {vocab_size * embedding_dim * 2:,}")


    def softmax(self, x: np.ndarray) -> np.ndarray:
        """Numerically stable softmax"""
        exp_x = np.exp(x - np.max(x))
        return exp_x / np.sum(exp_x)


    def forward(self, word_idx: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Forward pass: word → embedding → context prediction

        Args:
            word_idx: Index of input word

        Returns:
            (hidden, output, probabilities)
        """
        # One-hot encode input word
        x = np.zeros(self.vocab_size)
        x[word_idx] = 1

        # Hidden layer (embedding)
        h = np.dot(x, self.W1)  # (vocab_size,) @ (vocab_size, embedding_dim) = (embedding_dim,)

        # Output layer
        u = np.dot(h, self.W2)  # (embedding_dim,) @ (embedding_dim, vocab_size) = (vocab_size,)

        # Probabilities (softmax)
        y_pred = self.softmax(u)

        return h, u, y_pred


    def backward(self, word_idx: int, context_idx: int, h: np.ndarray, y_pred: np.ndarray):
        """
        Backward pass: Update weights using gradient descent

        Args:
            word_idx: Input word index
            context_idx: Target context word index
            h: Hidden layer from forward pass
            y_pred: Predicted probabilities from forward pass
        """
        # Create one-hot encoded input and target
        x = np.zeros(self.vocab_size)
        x[word_idx] = 1

        y_true = np.zeros(self.vocab_size)
        y_true[context_idx] = 1

        # Calculate error (derivative of cross-entropy + softmax)
        e = y_pred - y_true  # (vocab_size,)

        # Gradient for W2
        # dL/dW2 = h.T @ e
        dW2 = np.outer(h, e)  # (embedding_dim, 1) @ (1, vocab_size) = (embedding_dim, vocab_size)

        # Gradient for W1
        # dL/dW1 = x.T @ (e @ W2.T)
        dh = np.dot(e, self.W2.T)  # (vocab_size,) @ (vocab_size, embedding_dim) = (embedding_dim,)
        dW1 = np.outer(x, dh)  # (vocab_size, 1) @ (1, embedding_dim) = (vocab_size, embedding_dim)

        # Update weights (gradient descent)
        self.W1 -= self.learning_rate * dW1
        self.W2 -= self.learning_rate * dW2


    def train_step(self, word_idx: int, context_idx: int) -> float:
        """
        Single training step

        Args:
            word_idx: Input word
            context_idx: Context word to predict

        Returns:
            Cross-entropy loss
        """
        # Forward pass
        h, u, y_pred = self.forward(word_idx)

        # Calculate loss (cross-entropy)
        loss = -np.log(y_pred[context_idx] + 1e-10)  # Add epsilon to prevent log(0)

        # Backward pass
        self.backward(word_idx, context_idx, h, y_pred)

        return loss


    def train(self, training_pairs: List[Tuple[int, int]], epochs: int = 100, verbose: bool = True):
        """
        Train embeddings on word-context pairs

        Args:
            training_pairs: List of (word_idx, context_idx) tuples
            epochs: Number of training iterations
            verbose: Print progress
        """
        print(f"\n🏋️ Training Word Embeddings...")
        print(f"   Training pairs: {len(training_pairs)}")
        print(f"   Epochs: {epochs}")

        for epoch in range(epochs):
            total_loss = 0

            # Shuffle training data
            np.random.shuffle(training_pairs)

            # Train on each pair
            for word_idx, context_idx in training_pairs:
                loss = self.train_step(word_idx, context_idx)
                total_loss += loss

            # Average loss
            avg_loss = total_loss / len(training_pairs)
            self.training_history.append(avg_loss)

            if verbose and (epoch + 1) % 10 == 0:
                print(f"   Epoch {epoch + 1}/{epochs} - Loss: {avg_loss:.4f}")

        print(f"\n✅ Training complete!")
        print(f"   Final loss: {self.training_history[-1]:.4f}")


    def get_embedding(self, word_idx: int) -> np.ndarray:
        """Get embedding vector for word"""
        return self.W1[word_idx]


    def get_all_embeddings(self) -> np.ndarray:
        """Get all word embeddings (vocab_size, embedding_dim)"""
        return self.W1


    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two vectors

        Returns:
            Similarity score (-1 to 1, higher = more similar)
        """
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)


    def most_similar(self, word_idx: int, word_to_idx: Dict[str, int], idx_to_word: Dict[int, str], top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Find most similar words using cosine similarity

        Args:
            word_idx: Index of target word
            word_to_idx: Word to index mapping
            idx_to_word: Index to word mapping
            top_k: Number of similar words to return

        Returns:
            List of (word, similarity_score) tuples
        """
        target_vec = self.get_embedding(word_idx)

        # Calculate similarity with all other words
        similarities = []
        for idx in range(self.vocab_size):
            if idx == word_idx:
                continue  # Skip same word

            vec = self.get_embedding(idx)
            sim = self.cosine_similarity(target_vec, vec)
            word = idx_to_word[idx]
            similarities.append((word, sim))

        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)

        return similarities[:top_k]


    def save(self, filepath: str, word_to_idx: Dict[str, int], idx_to_word: Dict[int, str]):
        """Save embeddings to disk"""
        data = {
            'vocab_size': self.vocab_size,
            'embedding_dim': self.embedding_dim,
            'W1': self.W1.tolist(),
            'W2': self.W2.tolist(),
            'word_to_idx': word_to_idx,
            'idx_to_word': idx_to_word,
            'training_history': self.training_history,
            'trained_at': datetime.now().isoformat()
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"💾 Saved embeddings to {filepath}")


    @classmethod
    def load(cls, filepath: str) -> Tuple['WordEmbeddings', Dict[str, int], Dict[int, str]]:
        """Load embeddings from disk"""
        with open(filepath, 'r') as f:
            data = json.load(f)

        # Create embeddings instance
        embeddings = cls(
            vocab_size=data['vocab_size'],
            embedding_dim=data['embedding_dim']
        )

        # Restore weights
        embeddings.W1 = np.array(data['W1'])
        embeddings.W2 = np.array(data['W2'])
        embeddings.training_history = data['training_history']

        # Restore vocab mappings
        word_to_idx = data['word_to_idx']
        idx_to_word = {int(k): v for k, v in data['idx_to_word'].items()}

        print(f"📂 Loaded embeddings from {filepath}")
        print(f"   Trained: {data['trained_at']}")

        return embeddings, word_to_idx, idx_to_word


# =============================================================================
# VOCABULARY BUILDER
# =============================================================================

def build_vocabulary_from_wordlist(wordlist_path: str) -> Tuple[List[str], Dict[str, int], Dict[int, str]]:
    """
    Build vocabulary from StPetePros wordlist

    Args:
        wordlist_path: Path to wordlist file

    Returns:
        (words, word_to_idx, idx_to_word)
    """
    words = []

    with open(wordlist_path, 'r') as f:
        for line in f:
            line = line.strip()

            # Skip comments and empty lines
            if line.startswith('#') or not line:
                continue

            words.append(line.lower())

    # Remove duplicates while preserving order
    words = list(dict.fromkeys(words))

    # Create mappings
    word_to_idx = {word: idx for idx, word in enumerate(words)}
    idx_to_word = {idx: word for idx, word in enumerate(words)}

    print(f"📚 Built vocabulary from {wordlist_path}")
    print(f"   Total words: {len(words)}")

    return words, word_to_idx, idx_to_word


def generate_training_pairs(words: List[str], window_size: int = 2) -> List[Tuple[int, int]]:
    """
    Generate Skip-gram training pairs from word list

    For each word, predict surrounding context words within window

    Example:
        Words: ["tampa", "bay", "plumber", "repair", "service"]
        Window: 2
        Pairs: (bay → tampa), (bay → plumber), (plumber → bay), (plumber → repair), ...

    Args:
        words: List of words (sentences/contexts)
        window_size: How many words on each side to consider context

    Returns:
        List of (word_idx, context_idx) pairs
    """
    pairs = []

    for center_idx in range(len(words)):
        # Get context window
        start = max(0, center_idx - window_size)
        end = min(len(words), center_idx + window_size + 1)

        for context_idx in range(start, end):
            if context_idx == center_idx:
                continue  # Skip center word

            pairs.append((center_idx, context_idx))

    print(f"🔗 Generated {len(pairs)} training pairs")
    print(f"   Window size: {window_size}")

    return pairs


# =============================================================================
# CLI for Testing
# =============================================================================

if __name__ == '__main__':
    import sys

    # Load StPetePros wordlist
    wordlist_path = 'stpetepros-wordlist.txt'

    if not Path(wordlist_path).exists():
        print(f"❌ Wordlist not found: {wordlist_path}")
        print(f"   Make sure you're in the project root directory")
        sys.exit(1)

    # Build vocabulary
    words, word_to_idx, idx_to_word = build_vocabulary_from_wordlist(wordlist_path)

    # Generate training pairs (treat wordlist as sequence)
    training_pairs_idx = generate_training_pairs(
        list(range(len(words))),
        window_size=3
    )

    # Initialize embeddings
    embeddings = WordEmbeddings(
        vocab_size=len(words),
        embedding_dim=50,
        learning_rate=0.1
    )

    # Train
    embeddings.train(training_pairs_idx, epochs=50, verbose=True)

    # Test similarity
    print("\n🔍 Testing word similarities...")

    test_words = ['plumber', 'tampa', 'repair', 'professional', 'service']

    for word in test_words:
        if word not in word_to_idx:
            continue

        word_idx = word_to_idx[word]
        similar = embeddings.most_similar(word_idx, word_to_idx, idx_to_word, top_k=5)

        print(f"\n'{word}' is similar to:")
        for sim_word, score in similar:
            print(f"   {sim_word}: {score:.3f}")

    # Save embeddings
    save_path = 'data/stpetepros_embeddings.json'
    Path('data').mkdir(exist_ok=True)
    embeddings.save(save_path, word_to_idx, idx_to_word)

    print(f"\n✅ Done! Embeddings saved to {save_path}")
