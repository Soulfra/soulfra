#!/usr/bin/env python3
"""
Chapter Tutorials - Interactive Learning Content for Each Chapter

Maps chapters to hands-on tutorials that teach you to build Soulfra features.
"""

# Tutorial content for each chapter
CHAPTER_TUTORIALS = {
    1: {
        'title': 'Build Your First Neural Network',
        'description': 'Learn how neural networks work by building one from scratch',
        'steps': [
            {
                'title': 'Understanding Neurons',
                'content': '''A neural network is made of layers of "neurons" that process information.

Think of it like a factory assembly line:
- **Input Layer**: Raw materials come in
- **Hidden Layers**: Processing stations transform the materials
- **Output Layer**: Final product comes out

Each neuron applies a simple transformation: `output = activation(weights * inputs + bias)`
                ''',
                'code_example': '''# Simple neuron implementation
def neuron(inputs, weights, bias):
    # Dot product of inputs and weights
    total = sum(i * w for i, w in zip(inputs, weights)) + bias

    # Activation function (sigmoid)
    return 1 / (1 + math.exp(-total))

# Example
inputs = [1.0, 0.5, 0.3]
weights = [0.2, 0.8, -0.5]
bias = 1.0

output = neuron(inputs, weights, bias)
print(f"Neuron output: {output}")
''',
                'try_it': 'neuron_demo',
                'quiz_question': 'What does a neuron do in a neural network?',
                'quiz_options': [
                    'Stores data permanently',
                    'Applies weights to inputs and an activation function',
                    'Generates random numbers',
                    'Connects to the internet'
                ],
                'quiz_answer': 1
            },
            {
                'title': 'Training with Backpropagation',
                'content': '''Neural networks learn by adjusting weights based on errors.

The process:
1. **Forward pass**: Input → Output
2. **Calculate error**: How wrong was the prediction?
3. **Backward pass**: Update weights to reduce error
4. **Repeat**: Do this thousands of times

This is called **backpropagation** + **gradient descent**.
                ''',
                'code_example': '''# Training loop
for epoch in range(1000):
    # Forward pass
    prediction = network.forward(input_data)

    # Calculate error
    error = target - prediction
    loss = error ** 2

    # Backward pass (update weights)
    network.backward(error, learning_rate=0.01)

    if epoch % 100 == 0:
        print(f"Epoch {epoch}, Loss: {loss}")
''',
                'try_it': 'training_demo'
            }
        ]
    },

    2: {
        'title': 'Generate QR Codes for Your Gallery',
        'description': 'Create scannable QR codes to share your content',
        'steps': [
            {
                'title': 'What Are QR Codes?',
                'content': '''QR codes are 2D barcodes that store information like URLs, text, or data.

**Use cases in Soulfra:**
- Gallery pages (scan to view on phone)
- DM links (scan to start private chat)
- Sharing blog posts
- Event check-ins

**How they work:**
1. Encode data into black/white pattern
2. Add error correction
3. Generate PNG image
4. Scan with phone camera
                ''',
                'quiz_question': 'What can QR codes store?',
                'quiz_options': [
                    'Only URLs',
                    'URLs, text, and arbitrary data',
                    'Only images',
                    'Only phone numbers'
                ],
                'quiz_answer': 1
            },
            {
                'title': 'Generate Your First QR Code',
                'content': '''Let's generate a QR code for a gallery page.

**Python code (pure stdlib, no external libs):**

```python
import qrcode

# Create QR code instance
qr = qrcode.QRCode(version=1, box_size=10, border=4)

# Add data
qr.add_data('https://soulfra.com/gallery/my-first-post')
qr.make(fit=True)

# Generate image
img = qr.make_image(fill_color="black", back_color="white")
img.save('my_qr.png')
```

**Try it yourself below!**
                ''',
                'try_it': 'qr_generator',
                'quiz_question': 'Which parameter controls the size of QR code squares?',
                'quiz_options': ['version', 'box_size', 'border', 'fill_color'],
                'quiz_answer': 1
            },
            {
                'title': 'Scan & Track QR Codes',
                'content': '''You can track who scans your QR codes!

**Database schema:**
```sql
CREATE TABLE qr_scans (
    id INTEGER PRIMARY KEY,
    qr_id TEXT,
    scanned_at TIMESTAMP,
    ip_address TEXT,
    device_type TEXT
);
```

**When someone scans:**
1. Redirect to target URL
2. Log scan event
3. Track device type, location
4. Show analytics dashboard
                ''',
                'try_it': 'qr_analytics',
                'quiz_question': 'What information can you track from QR scans?',
                'quiz_options': [
                    'Only the time',
                    'Time, IP, device type, location',
                    'Only the URL',
                    'Nothing, QR codes are anonymous'
                ],
                'quiz_answer': 1
            }
        ]
    },

    3: {
        'title': 'Customize Themes with Templates',
        'description': 'Build beautiful themes using Flask templates and CSS',
        'steps': [
            {
                'title': 'Flask Templates Basics',
                'content': '''Flask uses **Jinja2** templates to generate HTML dynamically.

**Template syntax:**
- `{{ variable }}` - Print variable
- `{% if condition %}` - Logic
- `{% for item in items %}` - Loops
- `{% include 'file.html' %}` - Include other templates

**Example:**
```html
<h1>Hello {{ username }}!</h1>
{% if user.is_admin %}
    <a href="/admin">Admin Panel</a>
{% endif %}
```
                '''
            }
        ]
    },

    4: {
        'title': 'Self-Host with Docker',
        'description': 'Deploy your own Soulfra instance',
        'steps': []
    },

    5: {
        'title': 'Clone & Customize Brands',
        'description': 'Fork CalRiven, DeathToData, or create your own brand',
        'steps': []
    },

    6: {
        'title': 'API Key Management & Privacy',
        'description': 'Secure your instance and manage API access',
        'steps': []
    },

    7: {
        'title': 'Deploy to Production',
        'description': 'Final project: Get your Soulfra instance online',
        'steps': []
    }
}


def get_chapter_tutorial(chapter_num):
    """Get tutorial content for a chapter"""
    return CHAPTER_TUTORIALS.get(chapter_num, {})


def get_tutorial_quiz_questions(chapter_num):
    """Extract quiz questions from tutorial steps"""
    tutorial = CHAPTER_TUTORIALS.get(chapter_num, {})
    questions = []

    for step in tutorial.get('steps', []):
        if 'quiz_question' in step:
            questions.append({
                'question': step['quiz_question'],
                'options': step.get('quiz_options', []),
                'answer_index': step.get('quiz_answer', 0),
                'step_title': step['title']
            })

    return questions
