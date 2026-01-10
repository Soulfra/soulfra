"""
Wordmap → CSS Generator
Converts user's wordmap (word frequencies) into dynamic CSS styling
"""
import hashlib
import json
from database import get_db

def word_to_color(word):
    """
    Convert a word to a hex color using hash
    This creates consistent colors for the same word across all users
    """
    # Hash the word to get consistent color
    hash_bytes = hashlib.md5(word.lower().encode()).digest()

    # Use first 3 bytes for RGB
    r = hash_bytes[0]
    g = hash_bytes[1]
    b = hash_bytes[2]

    # Ensure colors aren't too dark (minimum brightness)
    min_brightness = 40
    r = max(r, min_brightness)
    g = max(g, min_brightness)
    b = max(b, min_brightness)

    return f'#{r:02x}{g:02x}{b:02x}'

def get_user_wordmap(user_id):
    """
    Get user's wordmap from database
    Returns dict of {word: count}
    """
    db = get_db()

    # Get all user's voice recordings
    recordings = db.execute('''
        SELECT transcription FROM simple_voice_recordings
        WHERE user_id = ? AND transcription IS NOT NULL
    ''', (user_id,)).fetchall()

    # Build wordmap
    wordmap = {}
    for rec in recordings:
        text = rec['transcription'].lower()
        # Remove punctuation and split
        words = text.replace('.', ' ').replace(',', ' ').replace('!', ' ').replace('?', ' ').split()

        for word in words:
            word = word.strip()
            if len(word) > 2:  # Skip short words
                wordmap[word] = wordmap.get(word, 0) + 1

    return wordmap

def get_top_words(wordmap, limit=5):
    """Get top N words by frequency"""
    sorted_words = sorted(wordmap.items(), key=lambda x: x[1], reverse=True)
    return sorted_words[:limit]

def generate_css_from_wordmap(user_id, parent_domain=None):
    """
    Generate CSS styling based on user's wordmap

    Args:
        user_id: User to generate CSS for
        parent_domain: Optional parent domain to inherit from (cross-pollination)

    Returns:
        CSS string with custom properties
    """
    wordmap = get_user_wordmap(user_id)

    if not wordmap:
        # Default to parent domain colors if no wordmap yet
        if parent_domain == 'cringeproof':
            return """
:root {
    --primary-color: #ff006e;
    --secondary-color: #bdb2ff;
    --accent-color: #000;
    --bg-gradient-start: #000;
    --bg-gradient-end: #1a1a2e;
}
"""

    top_words = get_top_words(wordmap, limit=5)

    # Generate colors from top words
    colors = [word_to_color(word) for word, count in top_words]

    # Primary color = most frequent word
    primary = colors[0] if colors else '#ff006e'
    secondary = colors[1] if len(colors) > 1 else '#bdb2ff'
    accent = colors[2] if len(colors) > 2 else '#000'

    # Background gradient from top 2 words
    bg_start = colors[0] if colors else '#000'
    bg_end = colors[1] if len(colors) > 1 else '#1a1a2e'

    # Build CSS
    css = f"""
/* Auto-generated CSS from wordmap */
/* Top words: {', '.join(word for word, count in top_words)} */

:root {{
    --primary-color: {primary};
    --secondary-color: {secondary};
    --accent-color: {accent};
    --bg-gradient-start: {bg_start};
    --bg-gradient-end: {bg_end};

    /* Wordmap colors */
    --word-1: {colors[0] if len(colors) > 0 else '#ff006e'};
    --word-2: {colors[1] if len(colors) > 1 else '#bdb2ff'};
    --word-3: {colors[2] if len(colors) > 2 else '#00C49A'};
    --word-4: {colors[3] if len(colors) > 3 else '#ffe66d'};
    --word-5: {colors[4] if len(colors) > 4 else '#a8dadc'};
}}

body {{
    background: linear-gradient(135deg, var(--bg-gradient-start) 0%, var(--bg-gradient-end) 100%);
    color: white;
}}

.domain-card {{
    border-color: var(--primary-color);
}}

.domain-badge {{
    background: var(--primary-color);
}}

.header h1 {{
    background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}}

.record-btn-small {{
    background: var(--primary-color);
}}
"""

    return css

def get_wordmap_metadata(user_id):
    """
    Get metadata about user's wordmap for API responses
    """
    wordmap = get_user_wordmap(user_id)
    top_words = get_top_words(wordmap, limit=10)

    return {
        'total_words': sum(wordmap.values()),
        'unique_words': len(wordmap),
        'top_words': [{'word': word, 'count': count, 'color': word_to_color(word)}
                      for word, count in top_words]
    }
