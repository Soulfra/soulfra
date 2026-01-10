#!/usr/bin/env python3
"""
GeeksForGeeks-Style Tutorial Builder - OFFLINE LEARNING SYSTEM
===============================================================

Builds interactive tutorials from your own blog content using:
- ✅ Ollama AI (100% offline question generation)
- ✅ Your existing blog posts as curriculum
- ✅ Interactive code examples
- ✅ Aptitude-style tests
- ✅ "Try it yourself" exercises

Similar to GeeksForGeeks but:
- Uses YOUR content
- Works 100% offline
- Trains on your own ideas
- No internet required

Usage:
    # Generate tutorial from blog post
    python3 tutorial_builder.py --post-id 27

    # Generate learning path from multiple posts
    python3 tutorial_builder.py --learning-path "python-basics"

    # Create interactive quiz
    python3 tutorial_builder.py --quiz-from-post 27
"""

import sqlite3
import json
import urllib.request
import urllib.error
from datetime import datetime
from typing import List, Dict, Optional
from database import get_db
import sys


def get_post(post_id: int):
    """Get post by ID"""
    conn = get_db()
    post = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    conn.close()
    return post


def generate_questions_with_ollama(content: str, title: str = "", num_questions: int = 7,
                                   model: str = 'llama3.2:3b', question_type: str = 'tutorial') -> List[Dict]:
    """
    Use Ollama AI to generate tutorial questions from blog post content

    Args:
        content: Blog post content (markdown/text)
        title: Blog post title
        num_questions: Number of questions to generate
        model: Ollama model to use (default: llama3.2:3b - fast, offline)
        question_type: 'tutorial' (GeeksForGeeks style) or 'aptitude' (self-awareness)

    Returns:
        List of question dicts with 'question', 'answer', 'options', 'explanation' fields
    """
    print(f"🔍 Generating {num_questions} {question_type} questions using Ollama...")
    print(f"📝 Content length: {len(content)} characters")
    print(f"🤖 Using model: {model}")
    print(f"🌐 Connection: 100% OFFLINE (no internet)")

    # Truncate content to avoid token limits
    content_excerpt = content[:2000]

    # Different prompts for different question types
    if question_type == 'tutorial':
        # GeeksForGeeks-style tutorial questions
        prompt = f"""You are generating tutorial questions for a programming learning platform (like GeeksForGeeks).

Read this tutorial content and generate {num_questions} technical questions that test understanding of the concepts.

Tutorial Title: {title}

Tutorial Content:
{content_excerpt}

Generate {num_questions} questions in this EXACT JSON format:
[
  {{
    "question": "What does SQLite use for the primary key when AUTOINCREMENT is specified?",
    "options": ["Manual ID", "Unique UUID", "Auto-incrementing integer", "Random number"],
    "answer": "Auto-incrementing integer",
    "explanation": "SQLite automatically generates unique integer IDs starting from 1 when AUTOINCREMENT is used on a PRIMARY KEY column."
  }},
  ...
]

Each question should:
- Test a specific concept from the tutorial
- Have 4 multiple choice options
- Include the correct answer
- Provide a brief explanation
- Be suitable for beginners to intermediate learners

Return ONLY the JSON array, nothing else."""

    else:  # aptitude / self-awareness
        # Cringeproof-style aptitude questions
        prompt = f"""You are generating self-awareness questions for a personality assessment.

Read this content and generate {num_questions} self-awareness questions about how the reader relates to these ideas.

Content Title: {title}

Content:
{content_excerpt}

Generate {num_questions} questions in this EXACT JSON format:
[
  {{"question": "I often think about how my work documents itself", "category": "reflection"}},
  {{"question": "I find manual documentation tedious and repetitive", "category": "automation"}},
  ...
]

Each question should:
- Be a first-person statement (starting with "I...")
- Relate to themes from the content
- Be answerable on a 1-5 scale (Never to Always)
- Test self-awareness about the topic

Return ONLY the JSON array, nothing else."""

    try:
        # Call Ollama API (runs locally on port 11434)
        url = 'http://localhost:11434/api/generate'

        payload = {
            'model': model,
            'prompt': prompt,
            'stream': False,
            'options': {
                'temperature': 0.7,
                'top_p': 0.9
            }
        }

        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            url,
            data=data,
            headers={'Content-Type': 'application/json'}
        )

        print("⏳ Waiting for Ollama (this may take 10-30 seconds)...")

        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode('utf-8'))
            ai_response = result.get('response', '')

            print(f"✅ Ollama responded ({len(ai_response)} chars)")

            # Extract JSON from response
            # AI sometimes adds markdown code blocks, so clean it
            json_str = ai_response.strip()
            if json_str.startswith('```json'):
                json_str = json_str[7:]
            if json_str.startswith('```'):
                json_str = json_str[3:]
            if json_str.endswith('```'):
                json_str = json_str[:-3]
            json_str = json_str.strip()

            # Parse questions
            try:
                questions = json.loads(json_str)

                # Add metadata
                for q in questions:
                    q['generated_from'] = 'ollama'
                    q['model'] = model
                    q['source_title'] = title
                    q['question_type'] = question_type

                print(f"✅ Generated {len(questions)} questions")
                return questions

            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse JSON from Ollama: {e}")
                print(f"Response excerpt: {ai_response[:200]}...")
                return []

    except urllib.error.URLError as e:
        print(f"❌ ERROR: Could not connect to Ollama")
        print(f"   Make sure Ollama is running: ollama serve")
        print(f"   Install: https://ollama.com/download")
        print(f"   Error details: {e}")
        return []

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return []


def create_tutorial_from_post(post_id: int, save_to_db: bool = True) -> Dict:
    """
    Create a GeeksForGeeks-style tutorial from a blog post

    Args:
        post_id: Blog post ID
        save_to_db: Save tutorial to database

    Returns:
        Tutorial dict with questions, exercises, and metadata
    """
    print("=" * 80)
    print("GEEKSFORGEEKS-STYLE TUTORIAL BUILDER")
    print("=" * 80)
    print()

    # Get blog post
    post = get_post(post_id)

    if not post:
        print(f"❌ ERROR: Post {post_id} not found")
        return None

    print(f"📝 Tutorial Source: {post['title']}")
    print(f"📍 Post ID: {post_id}")
    print(f"📏 Content Length: {len(post['content'])} characters")
    print()

    # Generate tutorial questions
    print("Generating tutorial questions...")
    tutorial_questions = generate_questions_with_ollama(
        content=post['content'],
        title=post['title'],
        num_questions=7,
        question_type='tutorial'
    )

    # Generate aptitude questions
    print()
    print("Generating aptitude questions...")
    aptitude_questions = generate_questions_with_ollama(
        content=post['content'],
        title=post['title'],
        num_questions=5,
        question_type='aptitude'
    )

    # Build tutorial structure
    tutorial = {
        'post_id': post_id,
        'title': post['title'],
        'slug': post['slug'],
        'content': post['content'],
        'tutorial_questions': tutorial_questions,
        'aptitude_questions': aptitude_questions,
        'created_at': datetime.now().isoformat(),
        'tutorial_url': f"/tutorial/{post['slug']}",
        'quiz_url': f"/quiz/{post['slug']}",
        'practice_url': f"/practice/{post['slug']}"
    }

    if save_to_db:
        # Save to database
        conn = get_db()

        # Create tutorials table if needed
        conn.execute('''
            CREATE TABLE IF NOT EXISTS tutorials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER UNIQUE NOT NULL,
                title TEXT NOT NULL,
                slug TEXT NOT NULL,
                tutorial_questions TEXT,
                aptitude_questions TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES posts(id)
            )
        ''')

        # Insert tutorial
        conn.execute('''
            INSERT OR REPLACE INTO tutorials
            (post_id, title, slug, tutorial_questions, aptitude_questions, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            post_id,
            tutorial['title'],
            tutorial['slug'],
            json.dumps(tutorial_questions),
            json.dumps(aptitude_questions),
            tutorial['created_at']
        ))

        conn.commit()
        conn.close()

        print()
        print("✅ Tutorial saved to database!")

    print()
    print("=" * 80)
    print("TUTORIAL CREATED!")
    print("=" * 80)
    print(f"📚 Tutorial: {tutorial['tutorial_url']}")
    print(f"❓ Quiz: {tutorial['quiz_url']}")
    print(f"💻 Practice: {tutorial['practice_url']}")
    print()
    print(f"✅ Tutorial Questions: {len(tutorial_questions)}")
    print(f"✅ Aptitude Questions: {len(aptitude_questions)}")
    print()

    # Show sample questions
    if tutorial_questions:
        print("Sample Tutorial Question:")
        q = tutorial_questions[0]
        print(f"  Q: {q.get('question', 'N/A')}")
        print(f"  A: {q.get('answer', 'N/A')}")
        print()

    if aptitude_questions:
        print("Sample Aptitude Question:")
        q = aptitude_questions[0]
        print(f"  Q: {q.get('question', 'N/A')}")
        print()

    return tutorial


def create_learning_path(topic: str, num_posts: int = 5) -> Dict:
    """
    Create a learning path from multiple blog posts on a topic

    Args:
        topic: Topic keyword to search for
        num_posts: Number of posts to include

    Returns:
        Learning path dict with ordered tutorials
    """
    print("=" * 80)
    print(f"CREATING LEARNING PATH: {topic.upper()}")
    print("=" * 80)
    print()

    # Search for posts on topic
    conn = get_db()

    posts = conn.execute('''
        SELECT * FROM posts
        WHERE title LIKE ? OR content LIKE ?
        ORDER BY published_at DESC
        LIMIT ?
    ''', (f'%{topic}%', f'%{topic}%', num_posts)).fetchall()

    conn.close()

    if not posts:
        print(f"❌ No posts found for topic: {topic}")
        return None

    print(f"✅ Found {len(posts)} posts on '{topic}'")
    print()

    # Create tutorial for each post
    tutorials = []
    for i, post in enumerate(posts, 1):
        print(f"📝 {i}/{len(posts)}: {post['title']}")

        tutorial = create_tutorial_from_post(post['id'], save_to_db=True)
        if tutorial:
            tutorials.append(tutorial)

        print()

    # Build learning path
    learning_path = {
        'topic': topic,
        'num_tutorials': len(tutorials),
        'tutorials': tutorials,
        'created_at': datetime.now().isoformat(),
        'path_url': f"/learn/{topic}"
    }

    print("=" * 80)
    print(f"LEARNING PATH CREATED: {topic}")
    print("=" * 80)
    print(f"🎓 Tutorials: {len(tutorials)}")
    print(f"🔗 Path URL: {learning_path['path_url']}")
    print()

    return learning_path


def export_tutorial_html(tutorial: Dict, output_file: str = None):
    """
    Export tutorial as standalone HTML file (offline-ready)

    Args:
        tutorial: Tutorial dict
        output_file: Output filename (default: tutorial-{slug}.html)
    """
    if not output_file:
        output_file = f"tutorial-{tutorial['slug']}.html"

    # Generate HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{tutorial['title']} - Tutorial</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .tutorial-header {{
            background: #667eea;
            color: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 30px;
        }}
        .tutorial-header h1 {{
            margin: 0 0 10px 0;
        }}
        .question {{
            background: white;
            padding: 20px;
            margin-bottom: 15px;
            border-radius: 6px;
            border-left: 4px solid #667eea;
        }}
        .question h3 {{
            margin-top: 0;
            color: #333;
        }}
        .options {{
            list-style: none;
            padding: 0;
        }}
        .options li {{
            padding: 10px;
            margin: 5px 0;
            background: #f9f9f9;
            border-radius: 4px;
            cursor: pointer;
        }}
        .options li:hover {{
            background: #e9e9e9;
        }}
        .answer {{
            color: #27ae60;
            font-weight: bold;
        }}
        .explanation {{
            background: #e8f5e9;
            padding: 10px;
            margin-top: 10px;
            border-radius: 4px;
            font-size: 14px;
        }}
        .aptitude {{
            background: #fff3cd;
            border-left-color: #ffc107;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            color: #666;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="tutorial-header">
        <h1>{tutorial['title']}</h1>
        <p>📚 GeeksForGeeks-Style Tutorial | 🤖 Generated with Ollama AI</p>
        <p>⚡ 100% Offline | No internet required</p>
    </div>

    <h2>📖 Tutorial Questions</h2>
    <p>Test your understanding of the concepts:</p>
"""

    # Add tutorial questions
    for i, q in enumerate(tutorial['tutorial_questions'], 1):
        html += f"""
    <div class="question">
        <h3>Question {i}</h3>
        <p><strong>{q.get('question', 'N/A')}</strong></p>

        <ul class="options">
            {''.join(f'<li>{opt}</li>' for opt in q.get('options', []))}
        </ul>

        <p class="answer">✅ Answer: {q.get('answer', 'N/A')}</p>

        <div class="explanation">
            💡 {q.get('explanation', 'No explanation provided')}
        </div>
    </div>
"""

    # Add aptitude questions
    html += """
    <h2>🧠 Aptitude Questions</h2>
    <p>How do these concepts relate to you? (Rate 1-5: Never to Always)</p>
"""

    for i, q in enumerate(tutorial['aptitude_questions'], 1):
        html += f"""
    <div class="question aptitude">
        <h3>Question {i}</h3>
        <p><strong>{q.get('question', 'N/A')}</strong></p>
        <p style="font-size: 14px; color: #666;">Category: {q.get('category', 'general')}</p>
    </div>
"""

    html += f"""
    <div class="footer">
        <p>Tutorial generated from blog post on {tutorial['created_at']}</p>
        <p>Powered by Ollama AI (100% offline) | Post ID: {tutorial['post_id']}</p>
    </div>
</body>
</html>
"""

    # Write file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✅ Tutorial exported to: {output_file}")
    print(f"📂 Open in browser: file://{output_file}")


if __name__ == '__main__':
    import sys

    print()
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  GEEKSFORGEEKS-STYLE TUTORIAL BUILDER                     ║")
    print("║  100% Offline • Uses YOUR content • Ollama AI             ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()

    if len(sys.argv) > 1:
        if sys.argv[1] == '--post-id' and len(sys.argv) > 2:
            # Generate tutorial from specific post
            post_id = int(sys.argv[2])
            tutorial = create_tutorial_from_post(post_id)

            # Export as HTML
            if tutorial:
                export_tutorial_html(tutorial)

        elif sys.argv[1] == '--learning-path' and len(sys.argv) > 2:
            # Create learning path
            topic = sys.argv[2]
            learning_path = create_learning_path(topic)

        elif sys.argv[1] == '--quiz-from-post' and len(sys.argv) > 2:
            # Just generate quiz questions
            post_id = int(sys.argv[2])
            post = get_post(post_id)
            if post:
                questions = generate_questions_with_ollama(
                    post['content'],
                    post['title'],
                    num_questions=10,
                    question_type='tutorial'
                )
                print(json.dumps(questions, indent=2))

        else:
            print("❌ Unknown command")
            print()
            print("Usage:")
            print("  python3 tutorial_builder.py --post-id 27")
            print("  python3 tutorial_builder.py --learning-path python")
            print("  python3 tutorial_builder.py --quiz-from-post 27")

    else:
        # Default: Use the tutorial post we created earlier
        print("Creating tutorial from latest SQLite tutorial post...")
        print()

        # Find the tutorial post (created by create_blog_post_offline.py)
        conn = get_db()
        post = conn.execute('''
            SELECT * FROM posts
            WHERE slug LIKE '%sqlite%tutorial%'
            ORDER BY id DESC
            LIMIT 1
        ''').fetchone()
        conn.close()

        if post:
            tutorial = create_tutorial_from_post(post['id'])
            if tutorial:
                export_tutorial_html(tutorial)
        else:
            print("❌ No tutorial posts found")
            print()
            print("Try creating one first:")
            print("  python3 create_blog_post_offline.py --tutorial")
