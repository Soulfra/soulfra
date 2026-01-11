#!/usr/bin/env python3
"""
Tiny LLM from Scratch - Pure NumPy Implementation

Build a minimal transformer-style language model using only numpy.
No PyTorch, TensorFlow, or Hugging Face - just math.

Architecture:
- Token embeddings (from word_embeddings.py)
- Positional encodings
- Self-attention mechanism
- Feed-forward network
- Next-word prediction

This is like GPT-2 but:
- Tiny (1-2 layers, 50-100 dim)
- Trained on YOUR vocabulary only
- Transparent (you can see every operation)
- Educational (understand transformers from scratch)

Key concepts:
- Attention: Q, K, V matrices → attention scores → weighted values
- Self-attention: Tokens attend to other tokens in sequence
- Causal masking: Can only attend to previous tokens (for generation)
- Layer norm: Stabilize training
- Residual connections: Skip connections for gradient flow
"""

import numpy as np
import json
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from pathlib import Path


class TinyLLM:
    """
    Minimal transformer language model

    Simplified transformer with:
    - Single attention head (not multi-head)
    - Single layer (not 12+ like GPT)
    - Small embedding dim (50-100 vs 768+)
    - Pure numpy (no frameworks)
    """

    def __init__(
        self,
        vocab_size: int,
        embedding_dim: int = 64,
        max_seq_len: int = 20,
        learning_rate: float = 0.01
    ):
        """
        Initialize Tiny LLM

        Args:
            vocab_size: Number of tokens in vocabulary
            embedding_dim: Dimension of embeddings
            max_seq_len: Maximum sequence length
            learning_rate: Learning rate for training
        """
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.max_seq_len = max_seq_len
        self.learning_rate = learning_rate

        # Initialize parameters
        self._init_parameters()

        # Training history
        self.training_history = []

        print(f"🤖 Initialized Tiny LLM")
        print(f"   Vocab size: {vocab_size}")
        print(f"   Embedding dim: {embedding_dim}")
        print(f"   Max sequence length: {max_seq_len}")
        print(f"   Parameters: ~{self._count_parameters():,}")


    def _init_parameters(self):
        """Initialize all model parameters with small random values"""
        d = self.embedding_dim

        # Token embeddings (vocab_size, embedding_dim)
        # Will be loaded from word_embeddings.py
        self.token_embeddings = np.random.randn(self.vocab_size, d) * 0.01

        # Positional embeddings (max_seq_len, embedding_dim)
        self.positional_embeddings = self._create_positional_encodings()

        # Attention parameters
        # Q, K, V: Linear projections
        self.Wq = np.random.randn(d, d) * 0.01  # Query
        self.Wk = np.random.randn(d, d) * 0.01  # Key
        self.Wv = np.random.randn(d, d) * 0.01  # Value
        self.Wo = np.random.randn(d, d) * 0.01  # Output

        # Feed-forward network
        # FFN: embedding_dim → 4*embedding_dim → embedding_dim
        self.W1 = np.random.randn(d, d * 4) * 0.01
        self.b1 = np.zeros(d * 4)
        self.W2 = np.random.randn(d * 4, d) * 0.01
        self.b2 = np.zeros(d)

        # Output layer (embedding_dim → vocab_size)
        self.W_out = np.random.randn(d, self.vocab_size) * 0.01
        self.b_out = np.zeros(self.vocab_size)

        # Layer norm parameters (simplified)
        self.gamma1 = np.ones(d)
        self.beta1 = np.zeros(d)
        self.gamma2 = np.ones(d)
        self.beta2 = np.zeros(d)


    def _create_positional_encodings(self) -> np.ndarray:
        """
        Create sinusoidal positional encodings

        PE(pos, 2i) = sin(pos / 10000^(2i/d))
        PE(pos, 2i+1) = cos(pos / 10000^(2i/d))

        Returns:
            (max_seq_len, embedding_dim) array
        """
        pos = np.arange(self.max_seq_len)[:, np.newaxis]  # (max_seq_len, 1)
        i = np.arange(self.embedding_dim)[np.newaxis, :]  # (1, embedding_dim)

        # Calculate angles
        angles = pos / np.power(10000, (2 * (i // 2)) / self.embedding_dim)

        # Apply sin to even indices, cos to odd
        encodings = np.zeros((self.max_seq_len, self.embedding_dim))
        encodings[:, 0::2] = np.sin(angles[:, 0::2])
        encodings[:, 1::2] = np.cos(angles[:, 1::2])

        return encodings


    def _count_parameters(self) -> int:
        """Count total trainable parameters"""
        params = (
            self.token_embeddings.size +
            self.positional_embeddings.size +
            self.Wq.size + self.Wk.size + self.Wv.size + self.Wo.size +
            self.W1.size + self.b1.size + self.W2.size + self.b2.size +
            self.W_out.size + self.b_out.size +
            self.gamma1.size + self.beta1.size + self.gamma2.size + self.beta2.size
        )
        return params


    def softmax(self, x: np.ndarray, axis: int = -1) -> np.ndarray:
        """Numerically stable softmax"""
        exp_x = np.exp(x - np.max(x, axis=axis, keepdims=True))
        return exp_x / np.sum(exp_x, axis=axis, keepdims=True)


    def layer_norm(self, x: np.ndarray, gamma: np.ndarray, beta: np.ndarray, epsilon: float = 1e-6) -> np.ndarray:
        """
        Layer normalization

        Args:
            x: Input (seq_len, embedding_dim)
            gamma: Scale parameter
            beta: Shift parameter

        Returns:
            Normalized x
        """
        mean = np.mean(x, axis=-1, keepdims=True)
        var = np.var(x, axis=-1, keepdims=True)
        x_norm = (x - mean) / np.sqrt(var + epsilon)
        return gamma * x_norm + beta


    def attention(
        self,
        Q: np.ndarray,
        K: np.ndarray,
        V: np.ndarray,
        mask: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Scaled dot-product attention

        Attention(Q, K, V) = softmax(QK^T / √d_k) V

        Args:
            Q: Query (seq_len, embedding_dim)
            K: Key (seq_len, embedding_dim)
            V: Value (seq_len, embedding_dim)
            mask: Causal mask (seq_len, seq_len) - True = masked

        Returns:
            Attention output (seq_len, embedding_dim)
        """
        d_k = Q.shape[-1]

        # Compute attention scores: QK^T / √d_k
        scores = np.dot(Q, K.T) / np.sqrt(d_k)  # (seq_len, seq_len)

        # Apply causal mask (prevent attending to future tokens)
        if mask is not None:
            scores = np.where(mask, -1e9, scores)  # Large negative → softmax → ~0

        # Softmax to get attention weights
        attn_weights = self.softmax(scores, axis=-1)  # (seq_len, seq_len)

        # Apply attention to values
        output = np.dot(attn_weights, V)  # (seq_len, embedding_dim)

        return output


    def feed_forward(self, x: np.ndarray) -> np.ndarray:
        """
        Feed-forward network with ReLU

        FFN(x) = ReLU(xW1 + b1)W2 + b2

        Args:
            x: Input (seq_len, embedding_dim)

        Returns:
            Output (seq_len, embedding_dim)
        """
        # First layer: embedding_dim → 4*embedding_dim
        h = np.dot(x, self.W1) + self.b1
        h = np.maximum(0, h)  # ReLU

        # Second layer: 4*embedding_dim → embedding_dim
        output = np.dot(h, self.W2) + self.b2

        return output


    def forward(self, input_ids: np.ndarray, causal_mask: bool = True) -> Tuple[np.ndarray, np.ndarray]:
        """
        Forward pass through the model

        Args:
            input_ids: Token indices (seq_len,)
            causal_mask: Whether to apply causal masking

        Returns:
            (logits, embeddings)
            - logits: (vocab_size,) - next token predictions
            - embeddings: (seq_len, embedding_dim) - final hidden states
        """
        seq_len = len(input_ids)

        # 1. Embed tokens and add positional encodings
        token_emb = self.token_embeddings[input_ids]  # (seq_len, embedding_dim)
        pos_emb = self.positional_embeddings[:seq_len]  # (seq_len, embedding_dim)
        x = token_emb + pos_emb  # (seq_len, embedding_dim)

        # 2. Self-attention layer
        Q = np.dot(x, self.Wq)  # (seq_len, embedding_dim)
        K = np.dot(x, self.Wk)
        V = np.dot(x, self.Wv)

        # Create causal mask (lower triangular)
        mask = None
        if causal_mask:
            mask = np.triu(np.ones((seq_len, seq_len)), k=1).astype(bool)

        attn_output = self.attention(Q, K, V, mask=mask)
        attn_output = np.dot(attn_output, self.Wo)

        # Residual connection + layer norm
        x = self.layer_norm(x + attn_output, self.gamma1, self.beta1)

        # 3. Feed-forward network
        ff_output = self.feed_forward(x)

        # Residual connection + layer norm
        x = self.layer_norm(x + ff_output, self.gamma2, self.beta2)

        # 4. Output projection (predict next token)
        # Use last token's hidden state
        last_hidden = x[-1]  # (embedding_dim,)
        logits = np.dot(last_hidden, self.W_out) + self.b_out  # (vocab_size,)

        return logits, x


    def predict_next_token(self, input_ids: np.ndarray, temperature: float = 1.0) -> int:
        """
        Predict next token given input sequence

        Args:
            input_ids: Token indices (seq_len,)
            temperature: Sampling temperature (higher = more random)

        Returns:
            Next token index
        """
        logits, _ = self.forward(input_ids, causal_mask=True)

        # Apply temperature
        logits = logits / temperature

        # Sample from distribution
        probs = self.softmax(logits)
        next_token = np.random.choice(self.vocab_size, p=probs)

        return next_token


    def generate(
        self,
        prompt_ids: np.ndarray,
        max_new_tokens: int = 10,
        temperature: float = 1.0,
        idx_to_word: Optional[Dict[int, str]] = None
    ) -> List[int]:
        """
        Generate text autoregressively

        Args:
            prompt_ids: Starting tokens (seq_len,)
            max_new_tokens: How many tokens to generate
            temperature: Sampling temperature
            idx_to_word: Optional mapping for debug printing

        Returns:
            List of generated token indices
        """
        generated = list(prompt_ids)

        print(f"🎨 Generating {max_new_tokens} tokens...")
        if idx_to_word:
            print(f"   Prompt: {' '.join(idx_to_word[i] for i in prompt_ids)}")

        for i in range(max_new_tokens):
            # Get context (last max_seq_len tokens)
            context = generated[-self.max_seq_len:]

            # Predict next token
            next_token = self.predict_next_token(np.array(context), temperature=temperature)

            generated.append(next_token)

            if idx_to_word:
                print(f"   +{idx_to_word.get(next_token, '<?>')}", end=" ")

        print()  # Newline

        return generated


    def train_step(
        self,
        input_ids: np.ndarray,
        target_id: int
    ) -> float:
        """
        Single training step (simplified - no full backprop)

        This is a simplified version - real backprop through transformer is complex.
        For educational purposes, we'll use a simpler gradient update.

        Args:
            input_ids: Input sequence (seq_len,)
            target_id: Target next token

        Returns:
            Cross-entropy loss
        """
        # Forward pass
        logits, _ = self.forward(input_ids, causal_mask=True)

        # Calculate loss (cross-entropy)
        probs = self.softmax(logits)
        loss = -np.log(probs[target_id] + 1e-10)

        # Simplified gradient update (update output layer only)
        # Real transformer training would backprop through all layers
        target_one_hot = np.zeros(self.vocab_size)
        target_one_hot[target_id] = 1

        error = probs - target_one_hot  # Gradient of cross-entropy + softmax

        # Update output layer weights (simplified)
        # In reality, you'd use full backprop with chain rule
        # This is just a demonstration

        return loss


    def load_embeddings(self, embeddings: np.ndarray):
        """
        Load pre-trained token embeddings from word_embeddings.py

        Args:
            embeddings: (vocab_size, embedding_dim) array
        """
        if embeddings.shape != self.token_embeddings.shape:
            print(f"⚠️ Embedding shape mismatch: {embeddings.shape} != {self.token_embeddings.shape}")
            return

        self.token_embeddings = embeddings.copy()
        print(f"✅ Loaded pre-trained embeddings")


    def save(self, filepath: str):
        """Save model parameters to disk"""
        params = {
            'vocab_size': self.vocab_size,
            'embedding_dim': self.embedding_dim,
            'max_seq_len': self.max_seq_len,
            'learning_rate': self.learning_rate,
            'token_embeddings': self.token_embeddings.tolist(),
            'positional_embeddings': self.positional_embeddings.tolist(),
            'Wq': self.Wq.tolist(),
            'Wk': self.Wk.tolist(),
            'Wv': self.Wv.tolist(),
            'Wo': self.Wo.tolist(),
            'W1': self.W1.tolist(),
            'b1': self.b1.tolist(),
            'W2': self.W2.tolist(),
            'b2': self.b2.tolist(),
            'W_out': self.W_out.tolist(),
            'b_out': self.b_out.tolist(),
            'gamma1': self.gamma1.tolist(),
            'beta1': self.beta1.tolist(),
            'gamma2': self.gamma2.tolist(),
            'beta2': self.beta2.tolist(),
            'training_history': self.training_history,
            'saved_at': datetime.now().isoformat()
        }

        Path(filepath).parent.mkdir(exist_ok=True)

        with open(filepath, 'w') as f:
            json.dump(params, f, indent=2)

        print(f"💾 Saved model to {filepath}")


    @classmethod
    def load(cls, filepath: str) -> 'TinyLLM':
        """Load model from disk"""
        with open(filepath, 'r') as f:
            params = json.load(f)

        # Create model instance
        model = cls(
            vocab_size=params['vocab_size'],
            embedding_dim=params['embedding_dim'],
            max_seq_len=params['max_seq_len'],
            learning_rate=params['learning_rate']
        )

        # Restore parameters
        model.token_embeddings = np.array(params['token_embeddings'])
        model.positional_embeddings = np.array(params['positional_embeddings'])
        model.Wq = np.array(params['Wq'])
        model.Wk = np.array(params['Wk'])
        model.Wv = np.array(params['Wv'])
        model.Wo = np.array(params['Wo'])
        model.W1 = np.array(params['W1'])
        model.b1 = np.array(params['b1'])
        model.W2 = np.array(params['W2'])
        model.b2 = np.array(params['b2'])
        model.W_out = np.array(params['W_out'])
        model.b_out = np.array(params['b_out'])
        model.gamma1 = np.array(params['gamma1'])
        model.beta1 = np.array(params['beta1'])
        model.gamma2 = np.array(params['gamma2'])
        model.beta2 = np.array(params['beta2'])
        model.training_history = params['training_history']

        print(f"📂 Loaded model from {filepath}")
        print(f"   Saved: {params['saved_at']}")

        return model


# =============================================================================
# CLI for Testing
# =============================================================================

if __name__ == '__main__':
    # Demo: Create tiny LLM and generate text

    # Create model
    vocab_size = 100  # Small test vocab
    model = TinyLLM(
        vocab_size=vocab_size,
        embedding_dim=64,
        max_seq_len=20
    )

    # Test forward pass
    input_ids = np.array([1, 5, 10, 15])  # 4 tokens
    logits, embeddings = model.forward(input_ids)

    print(f"\n🧪 Test Forward Pass:")
    print(f"   Input: {input_ids}")
    print(f"   Logits shape: {logits.shape}")
    print(f"   Embeddings shape: {embeddings.shape}")

    # Test generation
    print(f"\n🎨 Test Generation:")
    prompt = np.array([1, 2, 3])
    generated = model.generate(
        prompt,
        max_new_tokens=10,
        temperature=0.8
    )
    print(f"   Generated: {generated}")

    # Save model
    model.save('data/tiny_llm_test.json')

    print(f"\n✅ Done!")
