#!/usr/bin/env python3
"""
QR Gallery System - Enhanced QR Codes as Interactive Galleries

Creates QR codes that open rich galleries instead of simple text posts.

Gallery Features:
- Image carousel from post
- Soul ratings from neural networks
- AI agent chat interface
- In-person DM QR code
- Share buttons

Usage:
    python3 qr_gallery_system.py --post 29
    python3 qr_gallery_system.py --all
    python3 qr_gallery_system.py --brand howtocookathome

Architecture:
    TIER 5: Distribution Layer
    - Generates QR codes that point to /gallery/{slug}
    - Creates gallery HTML pages
    - Combines TIER 1 (images), TIER 2 (text), TIER 3 (AI ratings)
"""

import os
import sys
import qrcode
from pathlib import Path
from database import get_db
import hashlib
from datetime import datetime
import json


# =============================================================================
# QR Code Generation
# =============================================================================

def generate_qr_code(url, output_path, box_size=10, border=4):
    """
    Generate QR code for URL

    Args:
        url: URL to encode
        output_path: Path to save QR code
        box_size: Size of each box in pixels
        border: Border size in boxes

    Returns:
        Path to QR code
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=box_size,
        border=border,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    img.save(output_path)
    return output_path


def generate_qr_hash(url):
    """
    Generate cryptographic hash of QR code data

    Args:
        url: URL encoded in QR

    Returns:
        SHA256 hash
    """
    return hashlib.sha256(url.encode('utf-8')).hexdigest()


# =============================================================================
# Gallery Data Retrieval
# =============================================================================

def get_post_with_brand(post_id):
    """
    Get post with brand information

    Args:
        post_id: ID of post

    Returns:
        dict with post and brand data
    """
    db = get_db()

    post = db.execute('''
        SELECT p.*,
               COALESCE(b.name, 'Soulfra') as brand_name,
               COALESCE(b.slug, 'soulfra') as brand_slug,
               COALESCE(b.color_primary, '#4a90e2') as color_primary,
               COALESCE(b.color_secondary, '#2c3e50') as color_secondary,
               COALESCE(b.color_accent, '#27ae60') as color_accent
        FROM posts p
        LEFT JOIN brands b ON p.brand_id = b.id
        WHERE p.id = ?
    ''', (post_id,)).fetchone()

    db.close()

    if not post:
        return None

    return dict(post)


def get_post_images(post_id):
    """
    Get all images for a post

    Args:
        post_id: ID of post

    Returns:
        list of image dicts
    """
    db = get_db()

    images = db.execute('''
        SELECT id, hash, alt_text, image_type, created_at
        FROM images
        WHERE post_id = ?
        ORDER BY created_at ASC
    ''', (post_id,)).fetchall()

    db.close()

    return [dict(img) for img in images]


def get_post_soul_rating(post_id):
    """
    Get soul rating for a post

    Args:
        post_id: ID of post

    Returns:
        dict with soul score data or None
    """
    db = get_db()

    soul = db.execute('''
        SELECT composite_score, tier, total_networks, last_updated
        FROM soul_scores
        WHERE entity_type = 'post' AND entity_id = ?
    ''', (post_id,)).fetchone()

    db.close()

    if not soul:
        return None

    return dict(soul)


def get_post_neural_ratings(post_id):
    """
    Get individual neural network ratings for a post

    Args:
        post_id: ID of post

    Returns:
        list of rating dicts
    """
    db = get_db()

    ratings = db.execute('''
        SELECT network_name, score, confidence, reasoning, rated_at
        FROM neural_ratings
        WHERE entity_type = 'post' AND entity_id = ?
        ORDER BY score DESC
    ''', (post_id,)).fetchall()

    db.close()

    return [dict(r) for r in ratings]


# =============================================================================
# Gallery HTML Generation
# =============================================================================

def generate_gallery_html(post, images, soul_rating, neural_ratings, base_url='http://localhost:5001'):
    """
    Generate gallery HTML page

    Args:
        post: Post dict
        base_url: Base URL for links
        images: List of image dicts
        soul_rating: Soul score dict
        neural_ratings: List of neural rating dicts

    Returns:
        HTML string
    """
    # Soul tier emoji
    tier_emoji = {
        'Legendary': '🌟',
        'High': '⭐',
        'Moderate': '⚡',
        'Low': '💧',
        'None': '❌'
    }
    soul_emoji = tier_emoji.get(soul_rating['tier'] if soul_rating else 'None', '')

    # Soul score display
    if soul_rating:
        soul_display = f'''
        <div class="soul-rating">
            <h2>⭐ Soul Rating</h2>
            <div class="soul-score">
                <span class="score">{soul_rating['composite_score']:.2f}</span>
                <span class="tier">{soul_rating['tier']} Soul {soul_emoji}</span>
            </div>
            <p class="rated-by">Rated by {soul_rating['total_networks']} neural networks</p>
        </div>
        '''
    else:
        soul_display = '<div class="soul-rating"><p>Not yet rated</p></div>'

    # Neural ratings breakdown
    neural_display = ''
    if neural_ratings:
        neural_items = []
        for rating in neural_ratings:
            # Shorten network name for display
            display_name = rating['network_name'].replace('_classifier', '').replace('_', ' ').title()
            neural_items.append(f'''
            <div class="neural-rating-item">
                <span class="network-name">{display_name}</span>
                <span class="network-score">{rating['score']:.2f}</span>
            </div>
            ''')

        neural_display = f'''
        <div class="neural-ratings">
            <h3>Neural Network Breakdown</h3>
            <div class="neural-ratings-list">
                {''.join(neural_items)}
            </div>
        </div>
        '''

    # Image gallery
    gallery_images = ''
    if images:
        image_items = []
        for img in images:
            image_url = f"/image/{img['hash']}"
            alt_text = img.get('alt_text', 'Gallery image')
            image_items.append(f'''
            <div class="gallery-item">
                <img src="{image_url}" alt="{alt_text}" loading="lazy">
            </div>
            ''')

        gallery_images = f'''
        <div class="image-gallery">
            <h2>🖼️ Gallery ({len(images)} images)</h2>
            <div class="gallery-grid">
                {''.join(image_items)}
            </div>
        </div>
        '''
    else:
        gallery_images = '<div class="image-gallery"><p>No images in this post</p></div>'

    # Chat interface
    chat_interface = f'''
    <div class="chat-interface">
        <h2>💬 Chat with AI</h2>
        <p>Ask questions about this post</p>
        <button onclick="openChat()" class="chat-btn">Start Chat</button>
    </div>

    <!-- Chat Modal -->
    <div id="chatModal" class="chat-modal">
        <div class="chat-modal-content">
            <div class="chat-modal-header">
                <h2>💬 Chat with AI</h2>
                <button class="close-chat" onclick="closeChat()">&times;</button>
            </div>
            <div class="chat-modal-body">
                <div id="chatHistory" class="chat-history">
                    <div class="chat-message ai-message">
                        <strong>AI Assistant:</strong> Hi! I'm here to help answer questions about this post. What would you like to know?
                    </div>
                </div>
                <div class="chat-input-group">
                    <input type="text" id="chatInput" class="chat-input" placeholder="Ask a question..." onkeypress="if(event.key==='Enter') sendMessage()">
                    <button id="chatSendBtn" class="chat-send-btn" onclick="sendMessage()">Send</button>
                </div>
                <div id="chatError" class="chat-error" style="display: none;"></div>
            </div>
        </div>
    </div>
    '''

    # DM QR code
    dm_section = f'''
    <div class="dm-section">
        <h2>📱 DM Author</h2>
        <p>Scan QR code in person to message the author</p>
        <button onclick="showDMQR()" class="dm-btn">Show DM QR Code</button>
        <div id="dm-qr" style="display: none;">
            <p class="security-note">⚠️ This QR code expires in 5 minutes and only works when scanned in person</p>
        </div>
    </div>
    '''

    # QR Code Display Section
    qr_rel_path = f"/static/qr_codes/galleries/{post['slug']}.png"
    qr_code_display = f'''
    <div class="qr-code-display">
        <h2>📱 Share This Gallery</h2>
        <p>Scan this QR code to open this gallery on your phone</p>
        <img src="{qr_rel_path}" alt="QR Code for {post['title']}" />
        <div class="share-note">
            💡 When someone scans your shared QR code, we track the lineage!<br>
            Share link: {base_url}/gallery/{post['slug']}
        </div>
    </div>
    '''

    # Full HTML
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{post['title']} - Gallery</title>
    <meta name="description" content="Interactive gallery for {post['title']}">

    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 2rem 1rem;
        }}

        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }}

        .header {{
            background: {post.get('color_primary', '#4a90e2')};
            color: white;
            padding: 2rem;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }}

        .header .brand {{
            font-size: 0.9rem;
            opacity: 0.9;
        }}

        .content {{
            padding: 2rem;
        }}

        .soul-rating {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 12px;
            margin-bottom: 2rem;
            text-align: center;
        }}

        .soul-score {{
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 1rem;
            margin: 1rem 0;
        }}

        .soul-score .score {{
            font-size: 3rem;
            font-weight: bold;
        }}

        .soul-score .tier {{
            font-size: 1.2rem;
        }}

        .rated-by {{
            font-size: 0.9rem;
            opacity: 0.9;
        }}

        .neural-ratings {{
            background: #f8f9fa;
            padding: 1.5rem;
            border-radius: 12px;
            margin-bottom: 2rem;
        }}

        .neural-ratings h3 {{
            margin-bottom: 1rem;
            color: #333;
        }}

        .neural-rating-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.8rem;
            background: white;
            margin-bottom: 0.5rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }}

        .network-name {{
            font-weight: 500;
            color: #555;
        }}

        .network-score {{
            font-weight: bold;
            color: {post.get('color_accent', '#27ae60')};
            font-size: 1.2rem;
        }}

        .image-gallery {{
            margin-bottom: 2rem;
        }}

        .image-gallery h2 {{
            margin-bottom: 1rem;
            color: #333;
        }}

        .gallery-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 1rem;
        }}

        .gallery-item {{
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease;
        }}

        .gallery-item:hover {{
            transform: scale(1.05);
        }}

        .gallery-item img {{
            width: 100%;
            height: 250px;
            object-fit: cover;
            display: block;
        }}

        .chat-interface, .dm-section {{
            background: {post.get('color_secondary', '#2c3e50')};
            color: white;
            padding: 1.5rem;
            border-radius: 12px;
            margin-bottom: 1rem;
            text-align: center;
        }}

        .chat-btn, .dm-btn {{
            background: {post.get('color_accent', '#27ae60')};
            color: white;
            border: none;
            padding: 1rem 2rem;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: bold;
            cursor: pointer;
            margin-top: 1rem;
            transition: opacity 0.3s ease;
        }}

        .chat-btn:hover, .dm-btn:hover {{
            opacity: 0.9;
        }}

        .security-note {{
            font-size: 0.85rem;
            margin-top: 1rem;
            background: rgba(255, 255, 255, 0.1);
            padding: 0.8rem;
            border-radius: 6px;
        }}

        .footer {{
            background: #f8f9fa;
            padding: 1.5rem;
            text-align: center;
            color: #666;
            font-size: 0.9rem;
        }}

        .footer a {{
            color: {post.get('color_primary', '#4a90e2')};
            text-decoration: none;
        }}

        .footer-nav {{
            display: flex;
            justify-content: center;
            gap: 2rem;
            margin-bottom: 1rem;
            flex-wrap: wrap;
        }}

        .qr-code-display {{
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            margin-bottom: 2rem;
            text-align: center;
        }}

        .qr-code-display img {{
            max-width: 250px;
            margin: 1rem auto;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
        }}

        .share-note {{
            background: #e3f2fd;
            padding: 1rem;
            border-radius: 8px;
            margin-top: 1rem;
            color: #1976d2;
            font-size: 0.9rem;
        }}

        /* Chat Modal Styles */
        .chat-modal {{
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            animation: fadeIn 0.3s ease;
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}

        .chat-modal-content {{
            background: white;
            margin: 5% auto;
            padding: 0;
            border-radius: 16px;
            width: 90%;
            max-width: 600px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
            animation: slideDown 0.3s ease;
        }}

        @keyframes slideDown {{
            from {{ transform: translateY(-50px); opacity: 0; }}
            to {{ transform: translateY(0); opacity: 1; }}
        }}

        .chat-modal-header {{
            background: {post.get('color_primary', '#4a90e2')};
            color: white;
            padding: 1.5rem;
            border-radius: 16px 16px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .chat-modal-header h2 {{
            margin: 0;
            font-size: 1.5rem;
        }}

        .close-chat {{
            color: white;
            font-size: 2rem;
            font-weight: bold;
            cursor: pointer;
            background: none;
            border: none;
            padding: 0;
            line-height: 1;
            transition: transform 0.2s;
        }}

        .close-chat:hover {{
            transform: scale(1.2);
        }}

        .chat-modal-body {{
            padding: 2rem;
        }}

        .chat-history {{
            max-height: 300px;
            overflow-y: auto;
            margin-bottom: 1.5rem;
            padding: 1rem;
            background: #f8f9fa;
            border-radius: 8px;
        }}

        .chat-message {{
            margin-bottom: 1rem;
            padding: 0.8rem;
            border-radius: 8px;
        }}

        .user-message {{
            background: #e3f2fd;
            color: #1976d2;
            margin-left: 2rem;
        }}

        .ai-message {{
            background: #f1f8e9;
            color: #558b2f;
            margin-right: 2rem;
        }}

        .chat-input-group {{
            display: flex;
            gap: 0.5rem;
        }}

        .chat-input {{
            flex: 1;
            padding: 0.8rem;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 1rem;
            font-family: inherit;
        }}

        .chat-input:focus {{
            outline: none;
            border-color: {post.get('color_primary', '#4a90e2')};
        }}

        .chat-send-btn {{
            background: {post.get('color_accent', '#27ae60')};
            color: white;
            border: none;
            padding: 0.8rem 1.5rem;
            border-radius: 8px;
            font-weight: bold;
            cursor: pointer;
            transition: opacity 0.3s;
        }}

        .chat-send-btn:hover {{
            opacity: 0.9;
        }}

        .chat-send-btn:disabled {{
            opacity: 0.5;
            cursor: not-allowed;
        }}

        .chat-loading {{
            text-align: center;
            padding: 1rem;
            color: #666;
        }}

        .chat-error {{
            background: #ffebee;
            color: #c62828;
            padding: 1rem;
            border-radius: 8px;
            margin-top: 1rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{post['title']}</h1>
            <div class="brand">{post['brand_name']}</div>
        </div>

        <div class="content">
            {soul_display}
            {neural_display}
            {gallery_images}
            {qr_code_display}
            {chat_interface}
            {dm_section}
        </div>

        <div class="footer">
            <div class="footer-nav">
                <a href="/">🏠 Home</a>
                <a href="/post/{post['slug']}">📖 Read Full Post</a>
                <a href="/galleries">🖼️ All Galleries</a>
                <a href="/@docs/">📚 Docs</a>
            </div>
            <p>Powered by Soulfra - Multi-tier gallery system with QR lineage tracking</p>
        </div>
    </div>

    <script>
        const GALLERY_SLUG = '{post['slug']}';

        function openChat() {{
            const modal = document.getElementById('chatModal');
            modal.style.display = 'block';
            document.getElementById('chatInput').focus();
        }}

        function closeChat() {{
            const modal = document.getElementById('chatModal');
            modal.style.display = 'none';
            document.getElementById('chatError').style.display = 'none';
        }}

        // Close modal when clicking outside
        window.onclick = function(event) {{
            const modal = document.getElementById('chatModal');
            if (event.target === modal) {{
                closeChat();
            }}
        }}

        async function sendMessage() {{
            const input = document.getElementById('chatInput');
            const question = input.value.trim();

            if (!question) return;

            // Disable input while processing
            const sendBtn = document.getElementById('chatSendBtn');
            input.disabled = true;
            sendBtn.disabled = true;
            document.getElementById('chatError').style.display = 'none';

            // Add user message to history
            const chatHistory = document.getElementById('chatHistory');
            const userMsg = document.createElement('div');
            userMsg.className = 'chat-message user-message';
            userMsg.innerHTML = `<strong>You:</strong> ${{question}}`;
            chatHistory.appendChild(userMsg);

            // Add loading indicator
            const loadingMsg = document.createElement('div');
            loadingMsg.className = 'chat-loading';
            loadingMsg.id = 'loadingIndicator';
            loadingMsg.textContent = '🤔 Thinking...';
            chatHistory.appendChild(loadingMsg);

            // Scroll to bottom
            chatHistory.scrollTop = chatHistory.scrollHeight;

            // Clear input
            input.value = '';

            try {{
                // Call chat API
                const response = await fetch('/api/gallery/chat', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({{
                        slug: GALLERY_SLUG,
                        question: question
                    }})
                }});

                const data = await response.json();

                // Remove loading indicator
                const loading = document.getElementById('loadingIndicator');
                if (loading) loading.remove();

                if (data.success) {{
                    // Add AI response
                    const aiMsg = document.createElement('div');
                    aiMsg.className = 'chat-message ai-message';
                    aiMsg.innerHTML = `<strong>AI Assistant:</strong> ${{data.answer}}`;
                    chatHistory.appendChild(aiMsg);
                }} else {{
                    // Show error
                    const errorDiv = document.getElementById('chatError');
                    errorDiv.textContent = data.error || 'Failed to get response';
                    errorDiv.style.display = 'block';

                    // Also add error to chat
                    const errorMsg = document.createElement('div');
                    errorMsg.className = 'chat-message ai-message';
                    errorMsg.innerHTML = `<strong>Error:</strong> ${{data.error || 'Failed to get response'}}`;
                    chatHistory.appendChild(errorMsg);
                }}

                // Scroll to bottom
                chatHistory.scrollTop = chatHistory.scrollHeight;

            }} catch (error) {{
                // Remove loading indicator
                const loading = document.getElementById('loadingIndicator');
                if (loading) loading.remove();

                // Show error
                const errorDiv = document.getElementById('chatError');
                errorDiv.textContent = 'Network error: ' + error.message;
                errorDiv.style.display = 'block';

                const errorMsg = document.createElement('div');
                errorMsg.className = 'chat-message ai-message';
                errorMsg.innerHTML = `<strong>Error:</strong> Could not connect to AI. Make sure Ollama is running.`;
                chatHistory.appendChild(errorMsg);

                chatHistory.scrollTop = chatHistory.scrollHeight;
            }} finally {{
                // Re-enable input
                input.disabled = false;
                sendBtn.disabled = false;
                input.focus();
            }}
        }}

        async function showDMQR() {{
            const dmQR = document.getElementById('dm-qr');
            const dmBtn = document.querySelector('.dm-btn');

            // Disable button and show loading
            dmBtn.disabled = true;
            dmBtn.textContent = 'Generating...';
            dmQR.style.display = 'block';
            dmQR.innerHTML = '<p class="security-note">⏳ Generating DM QR code...</p>';

            try {{
                // Call API to generate DM QR
                const response = await fetch('/api/dm/generate-qr', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({{
                        post_slug: GALLERY_SLUG
                    }})
                }});

                const data = await response.json();

                if (data.success) {{
                    // Calculate expiry time
                    const expiryDate = new Date(data.expiry * 1000);
                    const now = new Date();
                    const minutesRemaining = Math.floor((expiryDate - now) / 60000);
                    const secondsRemaining = Math.floor(((expiryDate - now) % 60000) / 1000);

                    // Display QR code
                    dmQR.innerHTML = `
                        <div style="background: white; padding: 1rem; border-radius: 8px; margin-top: 1rem;">
                            <img src="${{data.qr_url}}" alt="DM QR Code" style="max-width: 250px; display: block; margin: 0 auto;">
                            <p style="margin-top: 1rem; font-size: 0.9rem;">
                                <strong>@${{data.username}}</strong><br>
                                ⏰ Expires in ${{minutesRemaining}}m ${{secondsRemaining}}s<br>
                                🔐 Scan in person to send a DM
                            </p>
                        </div>
                        <p class="security-note">
                            ⚠️ This QR code expires in 5 minutes and only works when scanned in person.<br>
                            After scanning, the recipient will be able to send you an encrypted DM.
                        </p>
                    `;

                    // Start countdown timer
                    const countdownInterval = setInterval(() => {{
                        const now = new Date();
                        const remaining = expiryDate - now;

                        if (remaining <= 0) {{
                            clearInterval(countdownInterval);
                            dmQR.innerHTML = '<p class="security-note">⚠️ QR code expired. Click "Show DM QR Code" to generate a new one.</p>';
                            dmBtn.disabled = false;
                            dmBtn.textContent = 'Show DM QR Code';
                        }} else {{
                            const mins = Math.floor(remaining / 60000);
                            const secs = Math.floor((remaining % 60000) / 1000);
                            const timeDisplay = dmQR.querySelector('p strong');
                            if (timeDisplay && timeDisplay.nextSibling) {{
                                timeDisplay.nextSibling.nextSibling.innerHTML = `⏰ Expires in ${{mins}}m ${{secs}}s<br>`;
                            }}
                        }}
                    }}, 1000);

                    // Re-enable button
                    dmBtn.disabled = false;
                    dmBtn.textContent = 'Generate New QR Code';

                }} else {{
                    dmQR.innerHTML = `<p class="security-note">❌ Error: ${{data.error}}</p>`;
                    dmBtn.disabled = false;
                    dmBtn.textContent = 'Show DM QR Code';
                }}

            }} catch (error) {{
                dmQR.innerHTML = `<p class="security-note">❌ Network error: ${{error.message}}</p>`;
                dmBtn.disabled = false;
                dmBtn.textContent = 'Show DM QR Code';
            }}
        }}
    </script>
</body>
</html>'''

    return html


# =============================================================================
# Gallery Creation
# =============================================================================

def create_qr_gallery(post_id, base_url="http://localhost:5001", output_dir="output/galleries"):
    """
    Create QR gallery for a post

    Args:
        post_id: ID of post
        base_url: Base URL for gallery
        output_dir: Directory to save gallery files

    Returns:
        dict with gallery info
    """
    print(f"\n🎨 Creating QR Gallery for Post #{post_id}...")

    # Get post data
    post = get_post_with_brand(post_id)
    if not post:
        print(f"   ❌ Post not found: {post_id}")
        return None

    # Get images
    images = get_post_images(post_id)
    print(f"   🖼️  Found {len(images)} image(s)")

    # Get soul rating
    soul_rating = get_post_soul_rating(post_id)
    if soul_rating:
        print(f"   ⭐ Soul Rating: {soul_rating['composite_score']:.2f} \"{soul_rating['tier']}\"")
    else:
        print(f"   ⚠️  No soul rating yet (run neural_soul_scorer.py first)")

    # Get neural ratings
    neural_ratings = get_post_neural_ratings(post_id)

    # Generate gallery HTML
    gallery_html = generate_gallery_html(post, images, soul_rating, neural_ratings, base_url)

    # Save gallery HTML
    gallery_dir = Path(output_dir)
    gallery_dir.mkdir(parents=True, exist_ok=True)

    gallery_path = gallery_dir / f"{post['slug']}.html"
    gallery_path.write_text(gallery_html)
    print(f"   ✅ Created gallery HTML: {gallery_path}")

    # Generate QR code
    gallery_url = f"{base_url}/gallery/{post['slug']}"
    qr_dir = Path("static/qr_codes/galleries")
    qr_path = qr_dir / f"{post['slug']}.png"

    generate_qr_code(gallery_url, str(qr_path))
    print(f"   ✅ Generated QR code: {qr_path}")

    # Calculate QR hash
    qr_hash = generate_qr_hash(gallery_url)

    # Save to database
    db = get_db()
    db.execute('''
        INSERT OR REPLACE INTO qr_galleries
        (post_id, gallery_slug, qr_code_path, qr_code_hash, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (post_id, post['slug'], str(qr_path), qr_hash, datetime.now()))
    db.commit()
    db.close()

    print(f"   ✅ Saved to qr_galleries table")
    print(f"   🌐 Gallery URL: {gallery_url}")

    return {
        'post_id': post_id,
        'slug': post['slug'],
        'gallery_url': gallery_url,
        'qr_path': str(qr_path),
        'gallery_html_path': str(gallery_path)
    }


def create_all_galleries(base_url="http://localhost:5001", output_dir="output/galleries"):
    """
    Create QR galleries for all published posts

    Args:
        base_url: Base URL for galleries
        output_dir: Directory to save gallery files

    Returns:
        Number of galleries created
    """
    print("=" * 70)
    print("🎨 QR GALLERY SYSTEM - Creating Galleries for All Posts")
    print("=" * 70)

    db = get_db()
    posts = db.execute('''
        SELECT id FROM posts
        WHERE published_at IS NOT NULL
        ORDER BY id ASC
    ''').fetchall()
    db.close()

    if not posts:
        print("❌ No published posts found")
        return 0

    print(f"\n📋 Found {len(posts)} published post(s)")

    created = 0
    for post_row in posts:
        try:
            result = create_qr_gallery(post_row['id'], base_url, output_dir)
            if result:
                created += 1
        except Exception as e:
            print(f"   ❌ Error creating gallery for post {post_row['id']}: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 70)
    print(f"✅ Created {created}/{len(posts)} QR gallery(ies)")
    print("=" * 70)
    print()

    return created


# =============================================================================
# CLI
# =============================================================================

def main():
    """CLI for QR gallery system"""

    if '--help' in sys.argv:
        print(__doc__)
        return

    base_url = "http://localhost:5001"
    output_dir = "output/galleries"

    # Parse base URL
    if '--url' in sys.argv:
        idx = sys.argv.index('--url')
        if idx + 1 < len(sys.argv):
            base_url = sys.argv[idx + 1]

    # Parse output directory
    if '--output-dir' in sys.argv:
        idx = sys.argv.index('--output-dir')
        if idx + 1 < len(sys.argv):
            output_dir = sys.argv[idx + 1]

    if '--all' in sys.argv:
        create_all_galleries(base_url, output_dir)

    elif '--post' in sys.argv:
        idx = sys.argv.index('--post')
        if idx + 1 < len(sys.argv):
            post_id = int(sys.argv[idx + 1])
            create_qr_gallery(post_id, base_url, output_dir)

    else:
        print("Usage:")
        print("  python3 qr_gallery_system.py --all")
        print("  python3 qr_gallery_system.py --post 29")
        print("  python3 qr_gallery_system.py --post 29 --url https://soulfra.com")
        print("  python3 qr_gallery_system.py --all --output-dir ./galleries")


if __name__ == '__main__':
    main()
