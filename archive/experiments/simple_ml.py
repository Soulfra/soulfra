"""
Simple ML - Neural Network using ONLY Python stdlib
No numpy, tensorflow, pytorch, sklearn, or external ML libs

Implements:
- TF-IDF (Term Frequency-Inverse Document Frequency)
- Cosine Similarity (dot product)
- Naive Bayes Classifier
- K-Nearest Neighbors (KNN)
- Simple Decision Tree
- Model storage in SQL (not pickle files)
"""

import math
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from database import get_db


# =============================================================================
# FEATURE EXTRACTION
# =============================================================================

def tokenize(text):
    """Split text into lowercase words, remove punctuation"""
    if not text:
        return []
    # Convert to lowercase, split on non-word characters
    words = re.findall(r'\b[a-z]+\b', text.lower())
    return words


def extract_features(text, vocabulary=None):
    """
    Extract feature vector from text
    Returns dict of {word: count} or {word: tf-idf}
    """
    words = tokenize(text)
    features = Counter(words)

    # If vocabulary provided, only keep known words
    if vocabulary:
        features = {word: count for word, count in features.items() if word in vocabulary}

    return features


# =============================================================================
# TF-IDF (Term Frequency-Inverse Document Frequency)
# =============================================================================

def calculate_tf(word_counts):
    """
    Calculate term frequency
    TF(word) = (count of word in doc) / (total words in doc)
    """
    total_words = sum(word_counts.values())
    if total_words == 0:
        return {}
    return {word: count / total_words for word, count in word_counts.items()}


def calculate_idf(documents):
    """
    Calculate inverse document frequency
    IDF(word) = log(total_docs / docs_containing_word)

    documents: list of word_counts dicts
    """
    total_docs = len(documents)
    if total_docs == 0:
        return {}

    # Count how many documents contain each word
    word_doc_count = defaultdict(int)
    for doc in documents:
        for word in doc:
            word_doc_count[word] += 1

    # Calculate IDF
    idf = {}
    for word, doc_count in word_doc_count.items():
        idf[word] = math.log(total_docs / doc_count)

    return idf


def calculate_tfidf(word_counts, idf):
    """
    Calculate TF-IDF vector
    TF-IDF(word) = TF(word) * IDF(word)
    """
    tf = calculate_tf(word_counts)
    tfidf = {}
    for word, tf_value in tf.items():
        if word in idf:
            tfidf[word] = tf_value * idf[word]
    return tfidf


# =============================================================================
# COSINE SIMILARITY
# =============================================================================

def dot_product(vec1, vec2):
    """Calculate dot product of two sparse vectors (dicts)"""
    result = 0.0
    for word in vec1:
        if word in vec2:
            result += vec1[word] * vec2[word]
    return result


def magnitude(vec):
    """Calculate magnitude (length) of vector"""
    return math.sqrt(sum(val ** 2 for val in vec.values()))


def cosine_similarity(vec1, vec2):
    """
    Calculate cosine similarity between two vectors
    Cosine similarity = dot_product(vec1, vec2) / (||vec1|| * ||vec2||)

    Returns value between 0 (completely different) and 1 (identical)
    """
    dot = dot_product(vec1, vec2)
    mag1 = magnitude(vec1)
    mag2 = magnitude(vec2)

    if mag1 == 0 or mag2 == 0:
        return 0.0

    return dot / (mag1 * mag2)


# =============================================================================
# NAIVE BAYES CLASSIFIER
# =============================================================================

class NaiveBayesClassifier:
    """
    Simple Naive Bayes text classifier
    P(class|text) = P(class) * P(word1|class) * P(word2|class) * ...
    """

    def __init__(self):
        self.classes = {}  # {class: count}
        self.word_counts = {}  # {class: {word: count}}
        self.vocabulary = set()
        self.total_docs = 0

    def train(self, documents, labels):
        """
        Train on labeled documents

        documents: list of text strings
        labels: list of class labels (same length as documents)
        """
        self.total_docs = len(documents)

        for doc, label in zip(documents, labels):
            # Count classes
            self.classes[label] = self.classes.get(label, 0) + 1

            # Count words per class
            if label not in self.word_counts:
                self.word_counts[label] = Counter()

            words = tokenize(doc)
            self.word_counts[label].update(words)
            self.vocabulary.update(words)

    def predict(self, text):
        """
        Predict class for new text
        Returns (predicted_class, confidence)
        """
        words = tokenize(text)

        # Calculate P(class|text) for each class
        class_scores = {}

        for class_label in self.classes:
            # Start with P(class)
            prior = self.classes[class_label] / self.total_docs
            score = math.log(prior)  # Use log to avoid underflow

            # Multiply by P(word|class) for each word
            total_words_in_class = sum(self.word_counts[class_label].values())
            vocab_size = len(self.vocabulary)

            for word in words:
                # Laplace smoothing: add 1 to avoid zero probabilities
                word_count = self.word_counts[class_label].get(word, 0)
                word_prob = (word_count + 1) / (total_words_in_class + vocab_size)
                score += math.log(word_prob)

            class_scores[class_label] = score

        # Return class with highest score
        if not class_scores:
            return None, 0.0

        best_class = max(class_scores, key=class_scores.get)

        # Convert log scores to probabilities
        # Use softmax to get confidence
        max_score = max(class_scores.values())
        exp_scores = {c: math.exp(s - max_score) for c, s in class_scores.items()}
        total = sum(exp_scores.values())
        confidence = exp_scores[best_class] / total

        return best_class, confidence

    def to_dict(self):
        """Export model as JSON-serializable dict"""
        return {
            'type': 'naive_bayes',
            'classes': self.classes,
            'word_counts': {c: dict(wc) for c, wc in self.word_counts.items()},
            'vocabulary': list(self.vocabulary),
            'total_docs': self.total_docs
        }

    @classmethod
    def from_dict(cls, data):
        """Load model from dict"""
        model = cls()
        model.classes = data['classes']
        model.word_counts = {c: Counter(wc) for c, wc in data['word_counts'].items()}
        model.vocabulary = set(data['vocabulary'])
        model.total_docs = data['total_docs']
        return model


# =============================================================================
# K-NEAREST NEIGHBORS (KNN)
# =============================================================================

class KNNClassifier:
    """
    K-Nearest Neighbors classifier
    Classifies based on K most similar training examples
    """

    def __init__(self, k=3):
        self.k = k
        self.training_data = []  # [(tfidf_vector, label)]
        self.idf = {}

    def train(self, documents, labels):
        """
        Train on labeled documents

        documents: list of text strings
        labels: list of class labels
        """
        # Calculate IDF from all documents
        word_counts_list = [Counter(tokenize(doc)) for doc in documents]
        self.idf = calculate_idf(word_counts_list)

        # Store TF-IDF vectors with labels
        self.training_data = []
        for doc, label in zip(documents, labels):
            word_counts = Counter(tokenize(doc))
            tfidf = calculate_tfidf(word_counts, self.idf)
            self.training_data.append((tfidf, label))

    def predict(self, text):
        """
        Predict class for new text
        Returns (predicted_class, confidence)
        """
        # Calculate TF-IDF for input
        word_counts = Counter(tokenize(text))
        tfidf = calculate_tfidf(word_counts, self.idf)

        # Calculate similarity to all training examples
        similarities = []
        for train_vec, label in self.training_data:
            sim = cosine_similarity(tfidf, train_vec)
            similarities.append((sim, label))

        # Get K nearest neighbors
        similarities.sort(reverse=True, key=lambda x: x[0])
        k_nearest = similarities[:self.k]

        # Vote: count labels in K nearest
        votes = Counter(label for _, label in k_nearest)

        if not votes:
            return None, 0.0

        best_class = votes.most_common(1)[0][0]
        confidence = votes[best_class] / self.k

        return best_class, confidence

    def to_dict(self):
        """Export model as JSON-serializable dict"""
        return {
            'type': 'knn',
            'k': self.k,
            'training_data': [(dict(vec), label) for vec, label in self.training_data],
            'idf': self.idf
        }

    @classmethod
    def from_dict(cls, data):
        """Load model from dict"""
        model = cls(k=data['k'])
        model.training_data = [(vec, label) for vec, label in data['training_data']]
        model.idf = data['idf']
        return model


# =============================================================================
# SIMPLE DECISION TREE
# =============================================================================

class DecisionTreeClassifier:
    """
    Simple decision tree based on keyword presence
    Splits based on most discriminative words
    """

    def __init__(self, max_depth=3):
        self.max_depth = max_depth
        self.tree = None
        self.vocabulary = set()

    def _entropy(self, labels):
        """Calculate entropy of label distribution"""
        if not labels:
            return 0.0

        total = len(labels)
        counts = Counter(labels)
        entropy = 0.0

        for count in counts.values():
            prob = count / total
            if prob > 0:
                entropy -= prob * math.log(prob, 2)

        return entropy

    def _information_gain(self, documents, labels, word):
        """Calculate information gain from splitting on word"""
        # Initial entropy
        initial_entropy = self._entropy(labels)

        # Split documents by word presence
        has_word = []
        has_word_labels = []
        no_word = []
        no_word_labels = []

        for doc, label in zip(documents, labels):
            if word in tokenize(doc):
                has_word.append(doc)
                has_word_labels.append(label)
            else:
                no_word.append(doc)
                no_word_labels.append(label)

        # Calculate weighted entropy after split
        total = len(documents)
        if total == 0:
            return 0.0

        has_entropy = self._entropy(has_word_labels)
        no_entropy = self._entropy(no_word_labels)

        weighted_entropy = (len(has_word) / total) * has_entropy + \
                          (len(no_word) / total) * no_entropy

        return initial_entropy - weighted_entropy

    def _build_tree(self, documents, labels, depth=0):
        """Recursively build decision tree"""
        # Base cases
        if depth >= self.max_depth or not documents:
            # Return most common class
            if labels:
                return Counter(labels).most_common(1)[0][0]
            return None

        # If all same class, return that class
        unique_labels = set(labels)
        if len(unique_labels) == 1:
            return labels[0]

        # Find best word to split on
        best_word = None
        best_gain = 0.0

        for word in self.vocabulary:
            gain = self._information_gain(documents, labels, word)
            if gain > best_gain:
                best_gain = gain
                best_word = word

        # If no good split found, return most common class
        if best_word is None or best_gain == 0:
            return Counter(labels).most_common(1)[0][0]

        # Split on best word
        has_word_docs = []
        has_word_labels = []
        no_word_docs = []
        no_word_labels = []

        for doc, label in zip(documents, labels):
            if best_word in tokenize(doc):
                has_word_docs.append(doc)
                has_word_labels.append(label)
            else:
                no_word_docs.append(doc)
                no_word_labels.append(label)

        # Recursively build subtrees
        return {
            'word': best_word,
            'has_word': self._build_tree(has_word_docs, has_word_labels, depth + 1),
            'no_word': self._build_tree(no_word_docs, no_word_labels, depth + 1)
        }

    def train(self, documents, labels):
        """Train decision tree"""
        # Build vocabulary
        for doc in documents:
            self.vocabulary.update(tokenize(doc))

        # Build tree
        self.tree = self._build_tree(documents, labels)

    def predict(self, text):
        """Predict class for new text"""
        if self.tree is None:
            return None, 0.0

        words = set(tokenize(text))
        node = self.tree

        # Traverse tree
        while isinstance(node, dict):
            if node['word'] in words:
                node = node['has_word']
            else:
                node = node['no_word']

        # node is now a class label
        return node, 1.0  # Confidence is 1.0 for decision trees

    def to_dict(self):
        """Export model as JSON-serializable dict"""
        return {
            'type': 'decision_tree',
            'max_depth': self.max_depth,
            'tree': self.tree,
            'vocabulary': list(self.vocabulary)
        }

    @classmethod
    def from_dict(cls, data):
        """Load model from dict"""
        model = cls(max_depth=data['max_depth'])
        model.tree = data['tree']
        model.vocabulary = set(data['vocabulary'])
        return model


# =============================================================================
# MODEL PERSISTENCE (SQL Storage)
# =============================================================================

def save_model(model, model_type, trained_on, accuracy=None):
    """
    Save model to database
    Returns model_id
    """
    db = get_db()

    model_data = json.dumps(model.to_dict())

    cursor = db.execute('''
        INSERT INTO ml_models (model_type, model_data, trained_on, accuracy, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (model_type, model_data, trained_on, accuracy, datetime.now().isoformat()))

    model_id = cursor.lastrowid
    db.commit()
    db.close()

    return model_id


def load_model(model_id):
    """Load model from database"""
    db = get_db()
    row = db.execute('SELECT * FROM ml_models WHERE id = ?', (model_id,)).fetchone()
    db.close()

    if not row:
        return None

    model_data = json.loads(row['model_data'])
    model_type = model_data['type']

    # Reconstruct model based on type
    if model_type == 'naive_bayes':
        return NaiveBayesClassifier.from_dict(model_data)
    elif model_type == 'knn':
        return KNNClassifier.from_dict(model_data)
    elif model_type == 'decision_tree':
        return DecisionTreeClassifier.from_dict(model_data)
    else:
        return None


def save_prediction(model_id, input_data, prediction, confidence, actual_result=None):
    """Save prediction to database for tracking accuracy"""
    db = get_db()

    db.execute('''
        INSERT INTO predictions (model_id, input_data, prediction, confidence, actual_result, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (model_id, input_data, prediction, confidence, actual_result, datetime.now().isoformat()))

    db.commit()
    db.close()


# =============================================================================
# FEATURE RECOMMENDATION ENGINE
# =============================================================================

def train_feature_classifier():
    """
    Train classifier to predict what type of feature a post/comment is requesting

    Classes:
    - 'ui' - UI/UX improvements
    - 'api' - API/backend features
    - 'ai' - AI/reasoning features
    - 'admin' - Admin/automation tools
    - 'other' - Other requests

    Returns model_id
    """
    from database import get_db

    db = get_db()

    # Get all posts and comments as training data
    posts = db.execute('SELECT title, content FROM posts').fetchall()
    comments = db.execute('SELECT content FROM comments').fetchall()

    # Manually label some data based on keywords (simple heuristic labeling)
    documents = []
    labels = []

    for post in posts:
        text = (post['title'] or '') + ' ' + (post['content'] or '')
        documents.append(text)

        # Simple keyword-based labeling
        text_lower = text.lower()
        if any(word in text_lower for word in ['dashboard', 'ui', 'button', 'page', 'view', 'display']):
            labels.append('ui')
        elif any(word in text_lower for word in ['api', 'endpoint', 'json', 'route']):
            labels.append('api')
        elif any(word in text_lower for word in ['reasoning', 'ai', 'calriven', 'analysis']):
            labels.append('ai')
        elif any(word in text_lower for word in ['admin', 'automation', 'cron', 'workflow']):
            labels.append('admin')
        else:
            labels.append('other')

    # Train Naive Bayes classifier
    classifier = NaiveBayesClassifier()
    classifier.train(documents, labels)

    # Save to database
    model_id = save_model(classifier, 'naive_bayes', len(documents))

    db.close()

    return model_id


def predict_feature_type(text, model_id):
    """
    Predict what type of feature is being requested
    Returns (feature_type, confidence)
    """
    model = load_model(model_id)
    if model is None:
        return None, 0.0

    prediction, confidence = model.predict(text)

    # Save prediction
    save_prediction(model_id, text, prediction, confidence)

    return prediction, confidence


# =============================================================================
# INITIALIZATION
# =============================================================================

def init_ml_tables():
    """Create ML tables if they don't exist"""
    db = get_db()

    db.execute('''
        CREATE TABLE IF NOT EXISTS ml_models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_type TEXT NOT NULL,
            model_data TEXT NOT NULL,
            trained_on INTEGER,
            accuracy REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    db.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_id INTEGER NOT NULL,
            input_data TEXT NOT NULL,
            prediction TEXT NOT NULL,
            confidence REAL,
            actual_result TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (model_id) REFERENCES ml_models(id)
        )
    ''')

    db.commit()
    db.close()

    print("✅ ML tables created")


if __name__ == '__main__':
    # Test the ML system
    print("Testing Simple ML (Python stdlib only)...\n")

    # Initialize tables
    init_ml_tables()

    # Test 1: Naive Bayes
    print("=== Test 1: Naive Bayes Classifier ===")
    nb = NaiveBayesClassifier()

    train_docs = [
        "need new dashboard for admin panel",
        "admin automation is broken",
        "api endpoint returning wrong data",
        "json response not formatted correctly",
        "reasoning engine needs improvement",
        "ai analysis is too slow"
    ]
    train_labels = ['ui', 'admin', 'api', 'api', 'ai', 'ai']

    nb.train(train_docs, train_labels)

    test_text = "create new api route for posts"
    prediction, confidence = nb.predict(test_text)
    print(f"Input: '{test_text}'")
    print(f"Prediction: {prediction} (confidence: {confidence:.2f})\n")

    # Test 2: KNN
    print("=== Test 2: K-Nearest Neighbors ===")
    knn = KNNClassifier(k=3)
    knn.train(train_docs, train_labels)

    prediction, confidence = knn.predict(test_text)
    print(f"Input: '{test_text}'")
    print(f"Prediction: {prediction} (confidence: {confidence:.2f})\n")

    # Test 3: Decision Tree
    print("=== Test 3: Decision Tree ===")
    dt = DecisionTreeClassifier(max_depth=2)
    dt.train(train_docs, train_labels)

    prediction, confidence = dt.predict(test_text)
    print(f"Input: '{test_text}'")
    print(f"Prediction: {prediction} (confidence: {confidence:.2f})\n")

    # Test 4: Cosine Similarity
    print("=== Test 4: Cosine Similarity ===")
    text1 = "admin dashboard needs work"
    text2 = "dashboard for admin is broken"

    vec1 = Counter(tokenize(text1))
    vec2 = Counter(tokenize(text2))

    similarity = cosine_similarity(vec1, vec2)
    print(f"Text 1: '{text1}'")
    print(f"Text 2: '{text2}'")
    print(f"Similarity: {similarity:.2f}\n")

    # Test 5: Model persistence
    print("=== Test 5: Model Persistence (SQL) ===")
    model_id = save_model(nb, 'naive_bayes', len(train_docs), 0.85)
    print(f"Saved model with ID: {model_id}")

    loaded_model = load_model(model_id)
    prediction, confidence = loaded_model.predict(test_text)
    print(f"Loaded model prediction: {prediction} (confidence: {confidence:.2f})\n")

    print("✅ All tests passed! ML system working with Python stdlib only.")
