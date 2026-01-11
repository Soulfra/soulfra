#!/usr/bin/env python3
"""
Create a post documenting the ML system we just built
CalRiven writes this post (dogfooding)
"""

from database import get_db
from datetime import datetime

def create_ml_documentation_post():
    """Create post about simple_ml.py"""

    db = get_db()

    # Get CalRiven's user ID
    calriven = db.execute('SELECT id FROM users WHERE username = ?', ('calriven',)).fetchone()
    if not calriven:
        print("❌ CalRiven user not found")
        return

    author_id = calriven['id']

    # Post content
    title = "Building Machine Learning with Python stdlib Only"
    slug = "building-ml-python-stdlib-only"

    content = """<p><strong>TL;DR:</strong> We built 5 ML algorithms (TF-IDF, Naive Bayes, KNN, Decision Trees, Cosine Similarity) using ONLY Python standard library. No numpy, tensorflow, sklearn. Models stored in SQL. <a href="/ml">Try it live</a>.</p>

<h2>Why Build ML from Scratch?</h2>

<p>Most platforms depend on external ML libraries that:</p>
<ul>
<li>Add 100MB+ of dependencies</li>
<li>Require specific Python versions</li>
<li>Create "black box" systems you can't inspect</li>
<li>Don't work offline or in restricted environments</li>
</ul>

<p>We wanted ML that's:</p>
<ul>
<li><strong>Transparent</strong> - You can read every line of how decisions are made</li>
<li><strong>Portable</strong> - Runs anywhere Python runs</li>
<li><strong>Educational</strong> - Learn ML by reading the code</li>
<li><strong>Ours</strong> - Not dependent on external companies/projects</li>
</ul>

<h2>What We Implemented</h2>

<h3>1. TF-IDF (Term Frequency-Inverse Document Frequency)</h3>

<p>Measures how important a word is to a document:</p>

<pre><code>TF(word) = count_in_doc / total_words
IDF(word) = log(total_docs / docs_containing_word)
TF-IDF(word) = TF(word) * IDF(word)
</code></pre>

<p><strong>Implementation:</strong> Uses <code>Counter</code> from collections + <code>math.log</code></p>

<h3>2. Naive Bayes Classifier</h3>

<p>Classifies text based on word probabilities:</p>

<pre><code>P(class|text) = P(class) * P(word1|class) * P(word2|class) * ...
</code></pre>

<p><strong>Features:</strong></p>
<ul>
<li>Laplace smoothing (avoid zero probabilities)</li>
<li>Log probabilities (prevent underflow)</li>
<li>Confidence scores via softmax</li>
</ul>

<h3>3. K-Nearest Neighbors (KNN)</h3>

<p>Classifies based on K most similar training examples:</p>

<pre><code>1. Calculate similarity to all training examples (cosine similarity)
2. Find K nearest neighbors
3. Vote: return majority class
</code></pre>

<h3>4. Cosine Similarity</h3>

<p>Measures similarity between two documents:</p>

<pre><code>similarity = dot_product(vec1, vec2) / (||vec1|| * ||vec2||)
</code></pre>

<p>Returns 0.0 (different) to 1.0 (identical)</p>

<h3>5. Decision Tree</h3>

<p>Splits on most informative words:</p>

<pre><code>information_gain = entropy_before - weighted_entropy_after
Split on word with highest gain
</code></pre>

<h2>SQL Model Storage (Not Pickle)</h2>

<p>Instead of pickle files, we store models as JSON in SQL:</p>

<pre><code>CREATE TABLE ml_models (
    id INTEGER PRIMARY KEY,
    model_type TEXT,
    model_data TEXT,  -- JSON
    trained_on INTEGER,
    accuracy REAL,
    created_at TIMESTAMP
);
</code></pre>

<p><strong>Why SQL?</strong></p>
<ul>
<li>✅ Transparent (view model as JSON)</li>
<li>✅ Portable (no Python version issues)</li>
<li>✅ Queryable (analyze predictions over time)</li>
<li>✅ Secure (no arbitrary code execution)</li>
</ul>

<h2>Current Use Case: Feature Classification</h2>

<p>The model classifies feature requests into 5 types:</p>

<ul>
<li><code>ui</code> - UI/UX improvements (dashboard, button, page)</li>
<li><code>api</code> - API/backend (endpoint, json, route)</li>
<li><code>ai</code> - AI/reasoning (reasoning, analysis)</li>
<li><code>admin</code> - Admin tools (automation, cron)</li>
<li><code>other</code> - Everything else</li>
</ul>

<p><strong>Training data:</strong> 12 posts + 32 comments from this platform</p>

<h2>Test Results</h2>

<pre><code>$ python3 simple_ml.py

Testing Simple ML (Python stdlib only)...

=== Test 1: Naive Bayes Classifier ===
Input: 'create new api route for posts'
Prediction: ui (confidence: 0.46)

=== Test 2: K-Nearest Neighbors ===
Input: 'create new api route for posts'
Prediction: ui (confidence: 0.33)

=== Test 3: Decision Tree ===
Input: 'create new api route for posts'
Prediction: ai (confidence: 1.00)

=== Test 4: Cosine Similarity ===
Text 1: 'admin dashboard needs work'
Text 2: 'dashboard for admin is broken'
Similarity: 0.45

✅ All tests passed!
</code></pre>

<h2>Academic Foundations</h2>

<p>This isn't new science - it's well-established computer science:</p>

<ul>
<li><strong>TF-IDF:</strong> Sparck Jones (1972)</li>
<li><strong>Naive Bayes:</strong> Based on Bayes' Theorem (1763)</li>
<li><strong>Cosine Similarity:</strong> Vector space model (1975)</li>
<li><strong>Decision Trees:</strong> Hunt et al. (1966), Quinlan (1986)</li>
</ul>

<p>No magic. No black boxes. Just math.</p>

<h2>Try It Yourself</h2>

<p><a href="/ml">Visit the ML Dashboard</a> to:</p>
<ul>
<li>Train a model on existing posts/comments</li>
<li>Make predictions on custom text</li>
<li>View model accuracy and predictions</li>
<li>Inspect the training data</li>
</ul>

<h2>What's Next?</h2>

<ol>
<li><strong>Markov Chains</strong> - Generate text from learned patterns</li>
<li><strong>Auto-training</strong> - Retrain when new posts arrive</li>
<li><strong>Feedback routing</strong> - Auto-classify incoming feedback</li>
<li><strong>Knowledge graph</strong> - Connect related posts via keywords</li>
</ol>

<h2>Philosophy: Simple Beats Complex</h2>

<p>We could have used scikit-learn, TensorFlow, or PyTorch. We chose not to.</p>

<p><strong>Why?</strong></p>
<ul>
<li>Simplicity → Fewer bugs</li>
<li>Transparency → Trust the system</li>
<li>Portability → Runs anywhere</li>
<li>Education → Learn by reading</li>
<li>Independence → No external dependencies</li>
</ul>

<p>This is what "build in public" means: document everything, hide nothing, make it reproducible.</p>

<hr>

<p><em>Code: <a href="/code/simple_ml.py">simple_ml.py</a></em></p>
<p><em>Dashboard: <a href="/ml">/ml</a></em></p>
<p><em>Documentation: <a href="/code/ML_IMPLEMENTATION.md">ML_IMPLEMENTATION.md</a></em></p>
"""

    # Insert post
    try:
        cursor = db.execute('''
            INSERT INTO posts (title, slug, content, user_id, published_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (title, slug, content, author_id, datetime.now().isoformat()))

        post_id = cursor.lastrowid
        db.commit()
        db.close()

        print(f"✅ Post created: #{post_id} - {title}")
        print(f"📍 View at: http://localhost:5001/post/{slug}")

        return post_id

    except Exception as e:
        print(f"❌ Error creating post: {e}")
        db.close()
        return None


if __name__ == '__main__':
    print("📝 Creating ML documentation post...\n")
    create_ml_documentation_post()
