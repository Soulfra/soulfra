#!/usr/bin/env python3
"""
Universal Text Encoder - The Missing "Space"

Ensures text works everywhere:
- SQLite with UTF-8
- JSON/JSON-LD
- Binary encoding
- Emoji support (🎭🟢🔵🟣🟠🟡)
- Any alphabet (Latin, CJK, Arabic, etc.)
- License/attribution metadata

The "Cr ingeproof" space you caught = this encoder layer.
"""

import json
import base64
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime


# Tier emoji mapping
TIER_EMOJI = {
    'legendary': '🟡',
    'epic': '🟠',
    'rare': '🟣',
    'uncommon': '🔵',
    'common': '🟢'
}


def ensure_utf8(text: str) -> str:
    """
    Ensure text is properly UTF-8 encoded

    Handles:
    - Emoji (🎭)
    - Unicode characters
    - Multi-byte characters
    - Control characters
    """
    if not isinstance(text, str):
        text = str(text)

    # Encode to UTF-8 bytes, then decode back
    # This normalizes the encoding
    return text.encode('utf-8', errors='ignore').decode('utf-8')


def safe_json_encode(data: Any) -> str:
    """
    JSON encode with UTF-8 support

    Ensures emojis and Unicode work in JSON
    """
    return json.dumps(data, ensure_ascii=False, indent=2)


def to_binary(text: str) -> bytes:
    """
    Convert text to binary representation

    Universal format that works across any system
    """
    return text.encode('utf-8')


def from_binary(data: bytes) -> str:
    """Decode binary back to text"""
    return data.decode('utf-8', errors='replace')


def to_base64(text: str) -> str:
    """
    Convert text to base64 (for URLs, APIs, etc.)

    Handles emoji and Unicode safely
    """
    binary = to_binary(text)
    return base64.b64encode(binary).decode('ascii')


def from_base64(encoded: str) -> str:
    """Decode base64 back to text"""
    binary = base64.b64decode(encoded.encode('ascii'))
    return from_binary(binary)


def text_hash(text: str) -> str:
    """
    Create deterministic hash of text

    Same text = same hash (regardless of encoding)
    """
    binary = to_binary(text)
    return hashlib.sha256(binary).hexdigest()[:16]


def add_tier_emoji(domain: str, tier: str) -> str:
    """
    Add tier emoji to domain name

    Example: 'cringeproof.com' + 'legendary' → '🟡 cringeproof.com'
    """
    emoji = TIER_EMOJI.get(tier, '⚪')
    return f"{emoji} {domain}"


def to_jsonld(data: Dict, context_type: str = 'VoiceProfile') -> Dict:
    """
    Convert data to JSON-LD format with schema.org context

    Makes wordmaps/domains machine-readable by search engines

    Args:
        data: Python dict with your data
        context_type: schema.org type (VoiceProfile, CreativeWork, etc.)

    Returns:
        JSON-LD dict with @context
    """
    jsonld = {
        '@context': 'https://schema.org/',
        '@type': context_type,
        'dateCreated': datetime.now().isoformat(),
        'license': 'https://opensource.org/licenses/MIT',
        'creator': {
            '@type': 'Organization',
            'name': 'Soulfra',
            'url': 'https://soulfra.com'
        }
    }

    # Merge user data
    jsonld.update(data)

    return jsonld


def wordmap_to_jsonld(wordmap: Dict[str, int], domain: str, tier: str) -> Dict:
    """
    Convert wordmap to JSON-LD format

    Example:
    ```json
    {
      "@context": "https://schema.org/",
      "@type": "VoiceProfile",
      "identifier": "cringeproof.com",
      "name": "🎭 Cringeproof Voice",
      "keywords": ["intent", "intuition", "filter", ...],
      "wordFrequency": {"intent": 42, "intuition": 38, ...}
    }
    ```
    """
    # Extract top keywords
    top_words = sorted(wordmap.items(), key=lambda x: x[1], reverse=True)[:20]
    keywords = [word for word, count in top_words]

    return to_jsonld({
        'identifier': domain,
        'name': f"{TIER_EMOJI.get(tier, '')} {domain} Voice",
        'tier': tier,
        'keywords': keywords,
        'wordFrequency': wordmap,
        'vocabularySize': len(wordmap),
        'encoding': 'UTF-8'
    }, context_type='VoiceProfile')


def export_wordmap_binary(wordmap: Dict[str, int]) -> bytes:
    """
    Export wordmap as compact binary format

    Format: msgpack or JSON bytes
    For portability across languages
    """
    json_str = safe_json_encode(wordmap)
    return to_binary(json_str)


def sqlite_utf8_pragma() -> str:
    """
    SQL pragma to ensure UTF-8 encoding

    Run this when creating database connections
    """
    return "PRAGMA encoding = 'UTF-8';"


def ascii_wordmap_viz(wordmap: Dict[str, int], width: int = 60) -> str:
    """
    Render wordmap as ASCII art visualization

    Practice room comic-style display

    Example:
    ```
    ┌──────────────────────────────────────────────────────────┐
    │ WORDMAP PRACTICE STATS                                   │
    ├──────────────────────────────────────────────────────────┤
    │ intent        ████████████████████████████ 42            │
    │ intuition     ███████████████████████ 38                 │
    │ filter        ██████████████ 24                          │
    └──────────────────────────────────────────────────────────┘
    ```
    """
    if not wordmap:
        return "[ No words yet - start recording! ]"

    # Sort by frequency
    top_words = sorted(wordmap.items(), key=lambda x: x[1], reverse=True)[:10]
    max_count = max(count for word, count in top_words) if top_words else 1

    lines = []
    lines.append("┌" + "─" * (width - 2) + "┐")
    lines.append("│ WORDMAP PRACTICE STATS" + " " * (width - 26) + "│")
    lines.append("├" + "─" * (width - 2) + "┤")

    for word, count in top_words:
        # Calculate bar length
        bar_max_width = width - 30
        bar_len = int((count / max_count) * bar_max_width)
        bar = "█" * bar_len

        # Format line
        line = f"│ {word:12s} {bar:30s} {count:4d}" + " " * (width - len(f"│ {word:12s} {bar:30s} {count:4d}") - 1) + "│"
        lines.append(line[:width-1] + "│")

    lines.append("└" + "─" * (width - 2) + "┘")

    return "\n".join(lines)


def test_encoding():
    """Test all encoding functions"""
    print("🧪 Testing Universal Text Encoder\n")

    # Test 1: UTF-8
    test_text = "Cringeproof 🎭 means Intent vs Intuition"
    encoded = ensure_utf8(test_text)
    print(f"✅ UTF-8: {encoded}")

    # Test 2: Binary
    binary = to_binary(test_text)
    decoded = from_binary(binary)
    print(f"✅ Binary roundtrip: {decoded == test_text}")

    # Test 3: Base64
    b64 = to_base64(test_text)
    back = from_base64(b64)
    print(f"✅ Base64 roundtrip: {back == test_text}")

    # Test 4: Hash
    h = text_hash(test_text)
    print(f"✅ Hash: {h}")

    # Test 5: Tier emoji
    domain_with_emoji = add_tier_emoji("cringeproof.com", "legendary")
    print(f"✅ Tier emoji: {domain_with_emoji}")

    # Test 6: JSON-LD
    wordmap = {"intent": 42, "intuition": 38, "filter": 24}
    jsonld = wordmap_to_jsonld(wordmap, "cringeproof.com", "legendary")
    print(f"✅ JSON-LD:\n{safe_json_encode(jsonld)}")

    # Test 7: ASCII viz
    viz = ascii_wordmap_viz(wordmap)
    print(f"✅ ASCII visualization:\n{viz}")


if __name__ == '__main__':
    test_encoding()
