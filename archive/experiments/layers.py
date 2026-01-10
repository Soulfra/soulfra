#!/usr/bin/env python3
"""
7-Layer Architecture for Soulfra
================================

Inspired by OSI model - each layer has clear input/output.
Makes debugging easy: "which layer broke?"

Layer 1: DATABASE      - SQL → Row objects
Layer 2: SERIALIZATION - Row → dict
Layer 3: FEATURES      - dict → dict + features (thumbnail, preview, vectors)
Layer 4: NEURAL NET    - features → predictions (4 networks debate)
Layer 5: CONTEXT       - data → template variables
Layer 6: RENDERING     - template → HTML string
Layer 7: RESPONSE      - HTML → HTTP Response

Why this matters:
-----------------
- Bug in /?sort=top? Test each layer to find which one fails
- Want to swap neural networks? Only touch Layer 4
- Want different template? Only touch Layer 5-6
- Want to add Redis cache? Add between Layer 1-2

Like WordPress: Database → PHP → Template → HTML (each layer testable)
Like Neural Networks: Input → Hidden → Output (clear boundaries)
"""

import re
import html
from database import get_db


# ==============================================================================
# LAYER 1: DATABASE - Raw SQL queries
# ==============================================================================

def fetch_posts_layer(sort='new', limit=10):
    """
    Layer 1: Fetch posts from database

    Input: sort method ('new', 'top', 'hot'), limit
    Output: List of sqlite3.Row objects (immutable!)

    Example:
        rows = fetch_posts_layer(sort='top', limit=5)
        # Returns Row objects with all post columns
    """
    db = get_db()

    if sort == 'top':
        # Most commented posts
        posts = db.execute('''
            SELECT p.*, COUNT(c.id) as comment_count
            FROM posts p
            LEFT JOIN comments c ON p.id = c.post_id
            WHERE p.published_at IS NOT NULL
            GROUP BY p.id
            ORDER BY comment_count DESC, p.published_at DESC
            LIMIT ?
        ''', (limit,)).fetchall()

    elif sort == 'hot':
        # Recent posts with activity (comments in last 24h)
        posts = db.execute('''
            SELECT p.*, COUNT(c.id) as recent_comments
            FROM posts p
            LEFT JOIN comments c ON p.id = c.post_id
                AND c.created_at > datetime('now', '-24 hours')
            WHERE p.published_at IS NOT NULL
            GROUP BY p.id
            ORDER BY recent_comments DESC, p.published_at DESC
            LIMIT ?
        ''', (limit,)).fetchall()

    else:  # 'new' (default)
        # Most recent posts
        posts = db.execute('''
            SELECT * FROM posts
            WHERE published_at IS NOT NULL
            ORDER BY published_at DESC
            LIMIT ?
        ''', (limit,)).fetchall()

    db.close()
    return posts


# ==============================================================================
# LAYER 2: SERIALIZATION - Convert DB rows to mutable dicts
# ==============================================================================

def serialize_posts_layer(rows):
    """
    Layer 2: Convert sqlite3.Row to dict

    Input: List of sqlite3.Row (immutable)
    Output: List of dict (mutable - can add keys)

    Why needed: Row objects are read-only. We need to add
    thumbnail, preview, predictions, etc.

    Example:
        rows = fetch_posts_layer(sort='top', limit=5)
        posts = serialize_posts_layer(rows)
        posts[0]['custom_field'] = 'now writable!'  # Works!
    """
    return [dict(row) for row in rows]


# ==============================================================================
# LAYER 3: FEATURE EXTRACTION - Add computed fields
# ==============================================================================

def extract_features_layer(posts):
    """
    Layer 3: Extract features from post content

    Input: List of dict with 'content', 'excerpt' fields
    Output: Same list with added fields:
        - thumbnail (str | None): First image URL
        - preview (str): HTML excerpt for homepage
        - word_vector (list): 300-dim embedding (TODO: future)
        - has_code (int): 0 or 1
        - has_images (int): Count of images

    This is where we prepare data for both:
    - Templates (thumbnail, preview)
    - Neural networks (word_vector, has_code, has_images)

    Example:
        posts = serialize_posts_layer(rows)
        posts = extract_features_layer(posts)
        print(posts[0]['thumbnail'])  # "http://example.com/img.png"
        print(posts[0]['preview'])    # "First 200 chars..."
    """
    for post in posts:
        # === Text Features (for templates) ===

        # Extract first image as thumbnail
        img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', post['content'])
        post['thumbnail'] = img_match.group(1) if img_match else None

        # Extract or generate preview text
        if post.get('excerpt'):
            post['preview'] = html.unescape(post['excerpt'])
        else:
            # Fallback: Extract first paragraph with basic formatting
            content = re.sub(r'<(script|style|pre|code)[^>]*>.*?</\1>', '', post['content'], flags=re.DOTALL)

            # Try to extract first <p> tag content
            p_match = re.search(r'<p[^>]*>(.*?)</p>', content, flags=re.DOTALL)
            if p_match:
                preview = p_match.group(1)
            else:
                # Fallback: content after first header
                preview = re.sub(r'^.*?</h[1-6]>', '', content, flags=re.DOTALL)

            # Keep only simple formatting: strong, em, b, i
            preview = re.sub(r'<(?!/?(?:strong|em|b|i)\b)[^>]+>', '', preview)

            # Clean whitespace and truncate
            preview = re.sub(r'\s+', ' ', preview).strip()
            if len(preview) > 200:
                preview = preview[:200].rsplit(' ', 1)[0]

            post['preview'] = html.unescape(preview)

        # === Binary Features (for neural networks) ===

        # Has code blocks? (0 or 1)
        post['has_code'] = 1 if '<code>' in post['content'] or '<pre>' in post['content'] else 0

        # Count images
        post['has_images'] = len(re.findall(r'<img[^>]+>', post['content']))

        # Content length bucket (0-4: very short to very long)
        content_len = len(post['content'])
        if content_len < 500:
            post['length_bucket'] = 0  # Very short
        elif content_len < 2000:
            post['length_bucket'] = 1  # Short
        elif content_len < 5000:
            post['length_bucket'] = 2  # Medium
        elif content_len < 10000:
            post['length_bucket'] = 3  # Long
        else:
            post['length_bucket'] = 4  # Very long

        # TODO: Add word vector embedding (300-dim)
        # post['word_vector'] = text_to_vector(post['content'])
        # For now, just mark as missing
        post['word_vector'] = None

    return posts


# ==============================================================================
# LAYER 4: NEURAL NETWORK - Predictions from multiple networks
# ==============================================================================

def predict_layer(posts, networks=None):
    """
    Layer 4: Run neural network predictions

    Input: List of dict with features (from Layer 3)
    Output: Same list with added 'predictions' dict:
        - calriven: prediction from CalRiven network
        - theauditor: prediction from TheAuditor network
        - deathtodata: prediction from DeathToData network
        - soulfra: judgment from Soulfra network (judges the other 3)

    Why 4 networks?
    - CalRiven: Technical analysis (prefers code, tests, architecture)
    - TheAuditor: Validation (prefers test results, proofs, data)
    - DeathToData: Ethics (prefers privacy, decentralization, OSS)
    - Soulfra: Meta-judge (evaluates other 3, picks winner)

    Example:
        posts = extract_features_layer(posts)
        posts = predict_layer(posts, networks=trained_networks)
        print(posts[0]['predictions'])
        # {
        #   'calriven': {'class': 'technical', 'confidence': 0.92},
        #   'theauditor': {'class': 'validation', 'confidence': 0.85},
        #   'deathtodata': {'class': 'ethics', 'confidence': 0.67},
        #   'soulfra': {'winner': 'calriven', 'confidence': 0.88}
        # }
    """
    if networks is None:
        # No networks loaded - skip predictions
        for post in posts:
            post['predictions'] = None
        return posts

    # Import feature extraction and explanation functions
    try:
        from train_context_networks import (
            extract_technical_features,
            extract_validation_features,
            extract_privacy_features,
            explain_technical_features,
            explain_validation_features,
            explain_privacy_features
        )
        import numpy as np
    except ImportError:
        # Can't import - skip predictions
        for post in posts:
            post['predictions'] = None
        return posts

    for post in posts:
        try:
            # Extract features for each network
            tech_features = extract_technical_features(post)
            validation_features = extract_validation_features(post)
            privacy_features = extract_privacy_features(post)

            # Get feature explanations (human-readable)
            tech_explanation = explain_technical_features(tech_features, post)
            validation_explanation = explain_validation_features(validation_features, post)
            privacy_explanation = explain_privacy_features(privacy_features, post)

            # Get predictions from each network
            calriven_pred = networks['calriven'].predict(np.array([tech_features]))[0][0]
            auditor_pred = networks['auditor'].predict(np.array([validation_features]))[0][0]
            deathtodata_pred = networks['deathtodata'].predict(np.array([privacy_features]))[0][0]

            # Soulfra judges based on the other 3
            soulfra_input = np.array([[calriven_pred, auditor_pred, deathtodata_pred]])
            soulfra_pred = networks['soulfra'].predict(soulfra_input)[0][0]

            post['predictions'] = {
                'calriven': {
                    'score': float(calriven_pred),
                    'label': 'TECHNICAL' if calriven_pred > 0.5 else 'NON-TECHNICAL',
                    'features': tech_explanation
                },
                'auditor': {
                    'score': float(auditor_pred),
                    'label': 'VALIDATED' if auditor_pred > 0.5 else 'UNVALIDATED',
                    'features': validation_explanation
                },
                'deathtodata': {
                    'score': float(deathtodata_pred),
                    'label': 'PRIVACY-FRIENDLY' if deathtodata_pred > 0.5 else 'PRIVACY-HOSTILE',
                    'features': privacy_explanation
                },
                'soulfra': {
                    'score': float(soulfra_pred),
                    'label': 'APPROVED' if soulfra_pred > 0.5 else 'REJECTED',
                    'inputs': {
                        'calriven': float(calriven_pred),
                        'auditor': float(auditor_pred),
                        'deathtodata': float(deathtodata_pred)
                    }
                }
            }
        except Exception as e:
            # If prediction fails for this post, set to None
            print(f"Warning: Failed to predict for post {post.get('id', 'unknown')}: {e}")
            post['predictions'] = None

    return posts


# ==============================================================================
# LAYER 5: TEMPLATE CONTEXT - Prepare data for Jinja2
# ==============================================================================

def build_template_context_layer(posts, sort='new', **kwargs):
    """
    Layer 5: Build context dict for template rendering

    Input: posts (with features and predictions), sort method, extra kwargs
    Output: dict ready for Jinja2 template

    Example:
        context = build_template_context_layer(
            posts=posts,
            sort='top',
            user=current_user
        )
        # Returns: {'posts': [...], 'sort': 'top', 'user': {...}}
    """
    context = {
        'posts': posts,
        'sort': sort
    }

    # Add any extra context variables
    context.update(kwargs)

    return context


# ==============================================================================
# LAYER 6: HTML RENDERING - Template → HTML string
# ==============================================================================

def render_html_layer(context, template_name, template_engine):
    """
    Layer 6: Render Jinja2 template to HTML

    Input: context dict, template name, Flask render_template function
    Output: HTML string

    Example:
        from flask import render_template
        html = render_html_layer(
            context={'posts': [...]},
            template_name='index.html',
            template_engine=render_template
        )
    """
    return template_engine(template_name, **context)


# ==============================================================================
# LAYER 7: HTTP RESPONSE - HTML → Flask Response
# ==============================================================================

def build_response_layer(html, status=200, headers=None):
    """
    Layer 7: Build Flask Response object

    Input: HTML string, status code, headers dict
    Output: Flask Response object (or just HTML for testing)

    Example:
        from flask import Response
        response = build_response_layer(
            html="<html>...</html>",
            status=200,
            headers={'Cache-Control': 'max-age=3600'}
        )
    """
    # For now, just return HTML
    # In production, wrap in Flask Response with headers
    return html


# ==============================================================================
# FULL PIPELINE - Combine all layers
# ==============================================================================

def full_pipeline(sort='new', limit=10, networks=None, template_name='index.html', render_func=None):
    """
    Run full 7-layer pipeline

    This is what app.py should call. If any layer breaks,
    we know exactly which one by testing each layer independently.

    Example:
        from flask import render_template

        @app.route('/')
        def index():
            html = full_pipeline(
                sort=request.args.get('sort', 'new'),
                limit=10,
                networks=app.networks,  # Trained networks
                template_name='index.html',
                render_func=render_template
            )
            return html
    """
    # Layer 1: Database
    rows = fetch_posts_layer(sort=sort, limit=limit)

    # Layer 2: Serialization
    posts = serialize_posts_layer(rows)

    # Layer 3: Feature extraction
    posts = extract_features_layer(posts)

    # Layer 4: Neural network predictions
    posts = predict_layer(posts, networks=networks)

    # Layer 5: Template context
    context = build_template_context_layer(posts, sort=sort)

    # Layer 6: Render HTML
    if render_func:
        html = render_html_layer(context, template_name, render_func)
    else:
        # Testing mode - just return context
        return context

    # Layer 7: HTTP response
    return build_response_layer(html)
