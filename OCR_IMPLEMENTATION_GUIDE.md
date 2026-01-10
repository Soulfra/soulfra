# OCR Implementation Guide - Python + SQL (2026)

**Created:** 2025-12-27
**Question:** "How do we build OCR from scratch in 2026 with python and sql?"
**Answer:** Three approaches below (simple → advanced)

---

## Use Cases for Soulfra

Before building OCR, clarify the use case:

1. **QR Code Enhancement:** Extract text from QR codes? *(Already have QR system)*
2. **Document Scanning:** Upload images of handwritten notes → Convert to searchable text
3. **Learning Card Import:** Scan physical flashcards → Import to learning system
4. **Game Asset Recognition:** Detect text in game screenshots for analysis
5. **Blog Post from Photos:** Upload photo of whiteboard → Generate blog post

**Recommendation:** Start with **Approach 2** (Tesseract wrapper) for speed, move to **Approach 3** (pure Python) if you want to avoid dependencies.

---

## Approach 1: Cloud OCR API (Easiest, Not From Scratch)

### Pros:
- Highest accuracy (Google Cloud Vision, AWS Textract)
- No ML training needed
- Handles complex layouts

### Cons:
- Requires API key + internet
- Costs money (after free tier)
- Not "from scratch"
- Defeats platform's offline philosophy

**Verdict:** ❌ Avoid - Violates Soulfra's zero-dependency ethos

---

## Approach 2: Tesseract Wrapper (Recommended)

### Overview

Tesseract is an open-source OCR engine (C++ library) with Python bindings.

**Philosophy Fit:**
- ✅ Open source (Apache 2.0 license)
- ✅ Runs offline
- ⚠️ Adds dependency (pytesseract + tesseract binary)
- ✅ Simple integration
- ✅ Production-ready accuracy

### Installation

```bash
# Install Tesseract binary (one-time)
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# Windows
# Download from: https://github.com/UB-Mannheim/tesseract/wiki

# Install Python wrapper
pip install pytesseract pillow
```

### Implementation

#### 1. Database Schema

```sql
CREATE TABLE ocr_scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    image_filename TEXT NOT NULL,
    extracted_text TEXT,
    confidence REAL,  -- OCR confidence score (0.0 - 1.0)
    language TEXT DEFAULT 'eng',
    scan_type TEXT,  -- 'document', 'flashcard', 'whiteboard', etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE ocr_words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id INTEGER NOT NULL,
    word TEXT NOT NULL,
    confidence REAL,
    bbox_x INTEGER,  -- Bounding box coordinates
    bbox_y INTEGER,
    bbox_width INTEGER,
    bbox_height INTEGER,
    FOREIGN KEY (scan_id) REFERENCES ocr_scans(id)
);
```

#### 2. OCR Service (`ocr_service.py`)

```python
"""OCR Service using Tesseract"""

import pytesseract
from PIL import Image
import sqlite3
from datetime import datetime
import os


class OCRService:
    """Optical Character Recognition service"""

    def __init__(self, db_path='soulfra.db', upload_folder='static/uploads/ocr'):
        self.db_path = db_path
        self.upload_folder = upload_folder
        os.makedirs(upload_folder, exist_ok=True)

    def extract_text(self, image_path, language='eng'):
        """
        Extract text from image using Tesseract

        Args:
            image_path: Path to image file
            language: OCR language (eng, spa, fra, deu, etc.)

        Returns:
            dict with extracted_text and confidence
        """
        try:
            # Open image
            img = Image.open(image_path)

            # Run OCR
            text = pytesseract.image_to_string(img, lang=language)

            # Get detailed data with bounding boxes
            data = pytesseract.image_to_data(img, lang=language, output_type=pytesseract.Output.DICT)

            # Calculate average confidence
            confidences = [conf for conf in data['conf'] if conf != -1]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0

            # Extract words with positions
            words = []
            for i in range(len(data['text'])):
                if data['text'][i].strip():  # Skip empty text
                    words.append({
                        'word': data['text'][i],
                        'confidence': data['conf'][i] / 100.0,  # Convert to 0-1 range
                        'bbox': {
                            'x': data['left'][i],
                            'y': data['top'][i],
                            'width': data['width'][i],
                            'height': data['height'][i]
                        }
                    })

            return {
                'extracted_text': text.strip(),
                'confidence': avg_confidence / 100.0,
                'words': words
            }

        except Exception as e:
            return {
                'extracted_text': '',
                'confidence': 0.0,
                'error': str(e)
            }

    def scan_and_save(self, image_path, user_id, scan_type='document', language='eng'):
        """
        Scan image and save results to database

        Args:
            image_path: Path to uploaded image
            user_id: ID of user who uploaded
            scan_type: Type of scan (document, flashcard, etc.)
            language: OCR language

        Returns:
            scan_id (int) of created record
        """
        # Extract text
        result = self.extract_text(image_path, language)

        # Save to database
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Insert scan
        cur.execute('''
            INSERT INTO ocr_scans
            (user_id, image_filename, extracted_text, confidence, language, scan_type, processed_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        ''', (
            user_id,
            os.path.basename(image_path),
            result['extracted_text'],
            result['confidence'],
            language,
            scan_type
        ))

        scan_id = cur.lastrowid

        # Insert words
        for word_data in result.get('words', []):
            cur.execute('''
                INSERT INTO ocr_words
                (scan_id, word, confidence, bbox_x, bbox_y, bbox_width, bbox_height)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                scan_id,
                word_data['word'],
                word_data['confidence'],
                word_data['bbox']['x'],
                word_data['bbox']['y'],
                word_data['bbox']['width'],
                word_data['bbox']['height']
            ))

        conn.commit()
        conn.close()

        return scan_id

    def get_scan(self, scan_id):
        """Get OCR scan results"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        scan = conn.execute('SELECT * FROM ocr_scans WHERE id = ?', (scan_id,)).fetchone()
        words = conn.execute('SELECT * FROM ocr_words WHERE scan_id = ?', (scan_id,)).fetchall()

        conn.close()

        return {
            'scan': dict(scan),
            'words': [dict(w) for w in words]
        }
```

#### 3. Flask Routes (`app.py`)

```python
from ocr_service import OCRService

ocr_service = OCRService()


@app.route('/ocr/upload', methods=['GET', 'POST'])
def ocr_upload():
    """Upload image for OCR"""
    if request.method == 'POST':
        if 'image' not in request.files:
            flash('No image uploaded', 'error')
            return redirect(url_for('ocr_upload'))

        file = request.files['image']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('ocr_upload'))

        # Save uploaded file
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        filepath = os.path.join('static/uploads/ocr', filename)
        file.save(filepath)

        # Run OCR
        user_id = session.get('user_id', 1)
        scan_id = ocr_service.scan_and_save(
            filepath,
            user_id,
            scan_type=request.form.get('scan_type', 'document'),
            language=request.form.get('language', 'eng')
        )

        flash(f'OCR scan completed! Scan ID: {scan_id}', 'success')
        return redirect(url_for('ocr_result', scan_id=scan_id))

    return render_template('ocr/upload.html')


@app.route('/ocr/result/<int:scan_id>')
def ocr_result(scan_id):
    """Show OCR results"""
    result = ocr_service.get_scan(scan_id)

    return render_template('ocr/result.html',
                         scan=result['scan'],
                         words=result['words'])


@app.route('/api/ocr/scan', methods=['POST'])
def api_ocr_scan():
    """API endpoint for OCR"""
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400

    file = request.files['image']

    # Save temp file
    filename = f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    filepath = os.path.join('static/uploads/ocr', filename)
    file.save(filepath)

    # Extract text
    result = ocr_service.extract_text(filepath)

    # Optionally delete temp file
    # os.remove(filepath)

    return jsonify({
        'text': result['extracted_text'],
        'confidence': result['confidence'],
        'word_count': len(result.get('words', []))
    })
```

#### 4. Template (`templates/ocr/upload.html`)

```html
{% extends "base.html" %}

{% block title %}OCR Upload{% endblock %}

{% block content %}
<div class="container mx-auto px-4 py-8 max-w-2xl">
    <h1 class="text-3xl font-bold mb-6">📸 OCR: Extract Text from Image</h1>

    <form method="POST" enctype="multipart/form-data" class="space-y-6">
        <div>
            <label class="block font-semibold mb-2">Upload Image:</label>
            <input type="file" name="image" accept="image/*" required
                   class="block w-full border border-gray-300 rounded p-2">
            <p class="text-sm text-gray-600 mt-1">
                Supports: JPG, PNG, PDF (scanned documents, flashcards, whiteboards)
            </p>
        </div>

        <div>
            <label class="block font-semibold mb-2">Scan Type:</label>
            <select name="scan_type" class="block w-full border border-gray-300 rounded p-2">
                <option value="document">Document</option>
                <option value="flashcard">Flashcard</option>
                <option value="whiteboard">Whiteboard</option>
                <option value="handwriting">Handwriting</option>
            </select>
        </div>

        <div>
            <label class="block font-semibold mb-2">Language:</label>
            <select name="language" class="block w-full border border-gray-300 rounded p-2">
                <option value="eng">English</option>
                <option value="spa">Spanish</option>
                <option value="fra">French</option>
                <option value="deu">German</option>
                <option value="chi_sim">Chinese (Simplified)</option>
            </select>
        </div>

        <button type="submit" class="w-full bg-indigo-600 text-white py-3 rounded-lg font-semibold hover:bg-indigo-700">
            🔍 Extract Text
        </button>
    </form>
</div>
{% endblock %}
```

### Usage Example

```python
from ocr_service import OCRService

ocr = OCRService()

# Extract text from image
result = ocr.extract_text('static/uploads/flashcard.jpg')
print(f"Extracted: {result['extracted_text']}")
print(f"Confidence: {result['confidence']:.2%}")

# Save to database
scan_id = ocr.scan_and_save('static/uploads/flashcard.jpg', user_id=1, scan_type='flashcard')
print(f"Saved as scan #{scan_id}")

# Retrieve results
data = ocr.get_scan(scan_id)
print(f"Text: {data['scan']['extracted_text']}")
print(f"Words detected: {len(data['words'])}")
```

---

## Approach 3: Pure Python OCR (From Scratch)

### Overview

Build basic OCR using only NumPy (no external OCR libraries).

**Complexity:** High
**Accuracy:** Low-moderate (unless you train advanced models)
**Use Case:** Educational, understanding how OCR works

### Algorithm Steps

1. **Preprocessing:**
   - Convert image to grayscale
   - Apply thresholding (binary image)
   - Noise reduction (median filter)
   - Skew correction (straighten rotated text)

2. **Character Segmentation:**
   - Find connected components (blobs)
   - Extract bounding boxes
   - Sort left-to-right, top-to-bottom

3. **Feature Extraction:**
   - Resize characters to 28x28 pixels
   - Extract pixel intensity features
   - Or use HOG (Histogram of Oriented Gradients)

4. **Classification:**
   - Use pre-trained neural network (from platform's existing networks!)
   - Or train simple SVM/KNN classifier
   - Match features against known characters

5. **Post-processing:**
   - Spell check (dictionary lookup)
   - Grammar correction

### Minimal Implementation

```python
"""Pure Python OCR using NumPy + existing neural networks"""

import numpy as np
from PIL import Image
import sqlite3


class SimplePythonOCR:
    """Basic OCR using NumPy only"""

    def __init__(self):
        # Load character templates (A-Z, a-z, 0-9)
        self.templates = self.load_templates()

    def load_templates(self):
        """Load character templates from database or file"""
        # Simplified: Use pre-rendered characters as templates
        # In production, train a neural network
        templates = {}

        # Example: Store 28x28 pixel templates for each character
        chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'

        for char in chars:
            # Create simple template (would load from file/DB in real system)
            template = self.create_char_template(char)
            templates[char] = template

        return templates

    def preprocess(self, image_path):
        """Convert image to binary (black/white)"""
        # Open image
        img = Image.open(image_path).convert('L')  # Grayscale

        # Convert to NumPy array
        img_array = np.array(img)

        # Apply threshold (Otsu's method)
        threshold = np.mean(img_array)
        binary = (img_array > threshold).astype(np.uint8) * 255

        return binary

    def segment_characters(self, binary_image):
        """Find individual characters in image"""
        # Simplified: Assume characters are separated by white space
        # Real implementation would use connected component analysis

        chars = []

        # Project vertically (sum pixel values in each column)
        vertical_projection = np.sum(binary_image, axis=0)

        # Find gaps (columns with low pixel sum = white space)
        threshold = np.max(vertical_projection) * 0.1
        in_char = False
        start_col = 0

        for col in range(len(vertical_projection)):
            if vertical_projection[col] > threshold and not in_char:
                # Start of character
                start_col = col
                in_char = True
            elif vertical_projection[col] <= threshold and in_char:
                # End of character
                char_img = binary_image[:, start_col:col]
                chars.append(char_img)
                in_char = False

        return chars

    def recognize_character(self, char_image):
        """Match character against templates"""
        # Resize to standard size (28x28)
        char_resized = np.array(Image.fromarray(char_image).resize((28, 28)))

        # Normalize
        char_normalized = char_resized.flatten() / 255.0

        best_match = None
        best_score = -1

        # Compare against all templates
        for char, template in self.templates.items():
            # Simple correlation
            score = np.corrcoef(char_normalized, template.flatten())[0, 1]

            if score > best_score:
                best_score = score
                best_match = char

        return best_match, best_score

    def extract_text(self, image_path):
        """Full OCR pipeline"""
        # 1. Preprocess
        binary = self.preprocess(image_path)

        # 2. Segment characters
        char_images = self.segment_characters(binary)

        # 3. Recognize each character
        text = ""
        confidences = []

        for char_img in char_images:
            char, confidence = self.recognize_character(char_img)
            text += char
            confidences.append(confidence)

        avg_confidence = np.mean(confidences) if confidences else 0

        return {
            'extracted_text': text,
            'confidence': avg_confidence
        }

    def create_char_template(self, char):
        """Create simple template for character (stub)"""
        # In real implementation, load from pre-rendered font or trained model
        return np.random.rand(28, 28)  # Placeholder
```

### Integration with Soulfra Neural Networks

```python
def recognize_with_neural_network(char_image):
    """Use existing Soulfra neural network for character recognition"""
    from database import get_db

    # Load trained character recognition network
    db = get_db()
    network_data = db.execute('''
        SELECT weights_blob, architecture_json
        FROM neural_networks
        WHERE model_name = 'char_recognition_network'
    ''').fetchone()

    if not network_data:
        # Train new network first
        raise ValueError("No character recognition network found. Train one first.")

    # Deserialize network
    weights = pickle.loads(network_data['weights_blob'])
    architecture = json.loads(network_data['architecture_json'])

    # Prepare input (28x28 flattened)
    char_resized = np.array(Image.fromarray(char_image).resize((28, 28)))
    input_vector = char_resized.flatten() / 255.0

    # Forward pass (using NumPy, like existing Soulfra networks)
    hidden = sigmoid(np.dot(input_vector, weights['W1']) + weights['b1'])
    output = softmax(np.dot(hidden, weights['W2']) + weights['b2'])

    # Get predicted character
    char_index = np.argmax(output)
    confidence = output[char_index]

    # Map index to character (A-Z, a-z, 0-9)
    chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    predicted_char = chars[char_index]

    return predicted_char, confidence


def sigmoid(x):
    return 1 / (1 + np.exp(-x))


def softmax(x):
    exp_x = np.exp(x - np.max(x))
    return exp_x / exp_x.sum()
```

---

## Comparison Matrix

| Feature | Cloud API | Tesseract | Pure Python |
|---------|-----------|-----------|-------------|
| **Accuracy** | 95-99% | 85-95% | 60-80% |
| **Speed** | Fast | Fast | Slow |
| **Offline** | ❌ No | ✅ Yes | ✅ Yes |
| **Dependencies** | HTTP client | pytesseract + binary | NumPy only |
| **License** | Proprietary | Apache 2.0 | DIY |
| **Training Needed** | No | No | Yes (for high accuracy) |
| **Handwriting** | ✅ Good | ⚠️ Limited | ❌ Poor |
| **Multi-language** | ✅ 100+ | ✅ 100+ | ❌ Requires training per language |
| **Learning Value** | Low | Medium | High |
| **Production Ready** | ✅ Yes | ✅ Yes | ⚠️ Depends on use case |

---

## Recommended Implementation Plan

### Phase 1: Tesseract Wrapper (Week 1)

1. Install Tesseract binary
2. Create `ocr_scans` and `ocr_words` tables
3. Implement `ocr_service.py`
4. Add Flask routes for upload/results
5. Test with simple documents

**Deliverable:** Working OCR system for typed documents

### Phase 2: Integrate with Learning System (Week 2)

1. Add "Scan Flashcard" feature
2. OCR extracts question/answer from photo
3. Auto-create learning cards from scans
4. Track which cards came from OCR vs manual entry

**Use Case:**
```
User scans physical flashcard:
  Front: "What is 2+2?"
  Back: "4"

System:
  1. OCR extracts text
  2. Creates learning_card with question="What is 2+2?", answer="4"
  3. Assigns to user's deck
  4. User can review via /learn
```

### Phase 3: Advanced Features (Week 3+)

1. **Handwriting recognition** (train custom model)
2. **Math equation parsing** (convert symbols to LaTeX)
3. **Multi-column detection** (newspapers, articles)
4. **Table extraction** (preserve structure)

---

## Training Custom OCR Model (Pure Python Approach)

If you want to build from scratch without Tesseract:

### 1. Collect Training Data

```python
def create_training_dataset():
    """Generate training data for characters"""
    from PIL import ImageFont, ImageDraw

    chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    fonts = ['Arial', 'Times New Roman', 'Courier', 'Helvetica']

    X = []  # Features (28x28 images)
    y = []  # Labels (character indices)

    for char_idx, char in enumerate(chars):
        for font_name in fonts:
            # Render character
            img = Image.new('L', (28, 28), color=255)
            draw = ImageDraw.Draw(img)
            font = ImageFont.truetype(font_name, 20)
            draw.text((4, 4), char, fill=0, font=font)

            # Convert to array
            img_array = np.array(img).flatten() / 255.0

            X.append(img_array)
            y.append(char_idx)

    return np.array(X), np.array(y)
```

### 2. Train Neural Network

```python
def train_char_recognition_network():
    """Train character recognition network using Soulfra's NumPy approach"""
    X, y = create_training_dataset()

    # Architecture: 784 input → 128 hidden → 62 output (chars)
    input_size = 28 * 28
    hidden_size = 128
    output_size = 62  # A-Z, a-z, 0-9

    # Initialize weights
    W1 = np.random.randn(input_size, hidden_size) * 0.01
    b1 = np.zeros(hidden_size)
    W2 = np.random.randn(hidden_size, output_size) * 0.01
    b2 = np.zeros(output_size)

    # Train (gradient descent)
    epochs = 1000
    learning_rate = 0.01

    for epoch in range(epochs):
        # Forward pass
        hidden = sigmoid(np.dot(X, W1) + b1)
        output = softmax(np.dot(hidden, W2) + b2)

        # Loss (cross-entropy)
        y_one_hot = np.zeros((len(y), output_size))
        y_one_hot[np.arange(len(y)), y] = 1

        loss = -np.mean(np.sum(y_one_hot * np.log(output + 1e-8), axis=1))

        # Backward pass (backpropagation)
        d_output = output - y_one_hot
        d_W2 = np.dot(hidden.T, d_output) / len(y)
        d_b2 = np.mean(d_output, axis=0)

        d_hidden = np.dot(d_output, W2.T) * hidden * (1 - hidden)
        d_W1 = np.dot(X.T, d_hidden) / len(y)
        d_b1 = np.mean(d_hidden, axis=0)

        # Update weights
        W1 -= learning_rate * d_W1
        b1 -= learning_rate * d_b1
        W2 -= learning_rate * d_W2
        b2 -= learning_rate * d_b2

        if epoch % 100 == 0:
            print(f"Epoch {epoch}, Loss: {loss:.4f}")

    # Save to database (Soulfra style)
    from database import get_db
    import pickle

    weights_blob = pickle.dumps({'W1': W1, 'b1': b1, 'W2': W2, 'b2': b2})
    architecture_json = json.dumps({'input': input_size, 'hidden': hidden_size, 'output': output_size})

    db = get_db()
    db.execute('''
        INSERT INTO neural_networks (model_name, weights_blob, architecture_json, trained_at)
        VALUES (?, ?, ?, datetime('now'))
    ''', ('char_recognition_network', weights_blob, architecture_json))
    db.commit()

    print("✅ Model trained and saved to database!")
```

---

## Summary & Recommendation

**For Soulfra Platform:**

✅ **Use Approach 2 (Tesseract)** if:
- You need production-ready accuracy
- You want results fast
- You're okay adding one dependency

✅ **Use Approach 3 (Pure Python)** if:
- You want to learn how OCR works
- You want to integrate with existing neural networks
- You want to train custom models for specific use cases
- You're willing to sacrifice accuracy for control

**Best of Both Worlds:**
1. Start with Tesseract for general OCR
2. Build custom neural network for specialized recognition (handwriting, math equations)
3. Use Soulfra's existing neural network infrastructure for training/storage

---

## Next Steps

1. **Choose approach** (recommend Tesseract)
2. **Create database tables** (`ocr_scans`, `ocr_words`)
3. **Implement `ocr_service.py`**
4. **Add Flask routes** for upload/results
5. **Test with sample images**
6. **Integrate with learning system** (scan flashcards → auto-create cards)

---

**Created:** 2025-12-27
**Status:** ✅ READY TO IMPLEMENT
**Dependencies:** pytesseract (optional), NumPy (already have)
**Database:** SQLite (already have)
