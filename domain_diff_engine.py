#!/usr/bin/env python3
"""
Domain Diff Engine - Calculate semantic differences between domain wordmaps

Features:
- Compare two domain wordmaps and identify differences
- Calculate semantic similarity scores
- Generate AI prompts for Ollama/Claude based on differentials
- Track changes and create rollback points
"""

from typing import Dict, List, Tuple
from database import get_db
import json
from datetime import datetime
import difflib


def get_domain_wordmap(domain: str) -> Dict[str, int]:
    """Fetch wordmap for a specific domain"""
    db = get_db()
    result = db.execute('''
        SELECT wordmap_json FROM domain_wordmaps
        WHERE domain = ?
    ''', (domain,)).fetchone()
    db.close()

    if result and result['wordmap_json']:
        return json.loads(result['wordmap_json'])
    return {}


def calculate_wordmap_diff(
    domain_a: str,
    domain_b: str
) -> Dict:
    """
    Calculate differences between two domain wordmaps

    Returns:
        {
            'only_in_a': {word: count},  # Words only in domain A
            'only_in_b': {word: count},  # Words only in domain B
            'shared': {word: (count_a, count_b)},  # Words in both
            'similarity_score': 0.75  # 0-1 similarity metric
        }
    """
    wordmap_a = get_domain_wordmap(domain_a)
    wordmap_b = get_domain_wordmap(domain_b)

    words_a = set(wordmap_a.keys())
    words_b = set(wordmap_b.keys())

    only_in_a = {word: wordmap_a[word] for word in words_a - words_b}
    only_in_b = {word: wordmap_b[word] for word in words_b - words_a}
    shared = {word: (wordmap_a[word], wordmap_b[word]) for word in words_a & words_b}

    # Calculate similarity using Jaccard index
    if not words_a and not words_b:
        similarity = 1.0
    else:
        similarity = len(words_a & words_b) / len(words_a | words_b)

    return {
        'domain_a': domain_a,
        'domain_b': domain_b,
        'only_in_a': only_in_a,
        'only_in_b': only_in_b,
        'shared': shared,
        'similarity_score': round(similarity, 3),
        'total_words_a': len(wordmap_a),
        'total_words_b': len(wordmap_b),
        'shared_words': len(shared)
    }


def generate_ai_prompt_from_diff(diff: Dict, operation: str = "merge") -> str:
    """
    Generate Ollama/Claude prompt based on differential analysis

    Args:
        diff: Output from calculate_wordmap_diff()
        operation: "merge", "contrast", "extract_themes", "suggest_vocabulary"

    Returns:
        Formatted prompt for AI
    """
    domain_a = diff['domain_a']
    domain_b = diff['domain_b']

    if operation == "merge":
        return f"""Analyze these two domain wordmaps and suggest how to merge them:

**{domain_a}** unique words:
{', '.join(list(diff['only_in_a'].keys())[:20])}

**{domain_b}** unique words:
{', '.join(list(diff['only_in_b'].keys())[:20])}

**Shared vocabulary:**
{', '.join(list(diff['shared'].keys())[:15])}

Task: Suggest 10 words that would bridge these two domains while maintaining their distinct identities.
Format: Return as JSON array: ["word1", "word2", ...]"""

    elif operation == "contrast":
        return f"""Compare the semantic identities of these two domains:

**{domain_a}:**
- Unique vocabulary: {', '.join(list(diff['only_in_a'].keys())[:10])}
- Domain philosophy: [infer from words]

**{domain_b}:**
- Unique vocabulary: {', '.join(list(diff['only_in_b'].keys())[:10])}
- Domain philosophy: [infer from words]

Task: In 3 sentences, explain how these domains differ philosophically based on their vocabulary.
"""

    elif operation == "suggest_vocabulary":
        # Find words with high frequency in one domain but missing in other
        high_freq_a = sorted(diff['only_in_a'].items(), key=lambda x: x[1], reverse=True)[:5]
        return f"""The domain **{domain_b}** is missing these high-value words from **{domain_a}**:

{', '.join([f"{word} ({count}x)" for word, count in high_freq_a])}

Task: Suggest 5 related words that {domain_b} should add to its vocabulary to strengthen this semantic area.
Format: JSON array with explanations: [{{"word": "example", "reason": "why this fits"}}]
"""

    else:  # extract_themes
        all_words_a = list(diff['only_in_a'].keys())[:15]
        all_words_b = list(diff['only_in_b'].keys())[:15]
        return f"""Extract the core themes from these domains:

**{domain_a}:** {', '.join(all_words_a)}
**{domain_b}:** {', '.join(all_words_b)}

Task: Identify 3 core themes for each domain.
Format:
{domain_a}: [theme1, theme2, theme3]
{domain_b}: [theme1, theme2, theme3]
"""


def merge_domains(
    source_domain: str,
    target_domain: str,
    words_to_transfer: List[str],
    merge_mode: str = "copy"
) -> Dict:
    """
    Transfer words from one domain to another

    Args:
        source_domain: Domain to copy words from
        target_domain: Domain to add words to
        words_to_transfer: List of words to move
        merge_mode: "copy" (keep in source) or "move" (remove from source)

    Returns:
        Status dict with before/after wordmaps
    """
    db = get_db()

    # Get source wordmap
    source = get_domain_wordmap(source_domain)
    target = get_domain_wordmap(target_domain)

    # Transfer words
    transferred = {}
    for word in words_to_transfer:
        if word in source:
            count = source[word]
            transferred[word] = count

            # Add to target
            if word in target:
                target[word] += count
            else:
                target[word] = count

            # Remove from source if move mode
            if merge_mode == "move":
                del source[word]

    # Save changes
    if merge_mode == "move":
        db.execute('''
            UPDATE domain_wordmaps
            SET wordmap_json = ?, last_updated = ?
            WHERE domain = ?
        ''', (json.dumps(source), datetime.now().isoformat(), source_domain))

    db.execute('''
        UPDATE domain_wordmaps
        SET wordmap_json = ?, last_updated = ?
        WHERE domain = ?
    ''', (json.dumps(target), datetime.now().isoformat(), target_domain))

    db.commit()
    db.close()

    return {
        'success': True,
        'transferred_words': len(transferred),
        'words': list(transferred.keys()),
        'mode': merge_mode,
        'source_remaining': len(source),
        'target_total': len(target)
    }


def create_diff_snapshot(domain: str, description: str = "Manual snapshot") -> int:
    """
    Create a rollback point for a domain's wordmap

    Returns:
        Snapshot ID
    """
    db = get_db()

    wordmap = get_domain_wordmap(domain)

    cursor = db.execute('''
        INSERT INTO domain_wordmap_snapshots (
            domain, wordmap_json, description, created_at
        ) VALUES (?, ?, ?, ?)
    ''', (domain, json.dumps(wordmap), description, datetime.now().isoformat()))

    snapshot_id = cursor.lastrowid
    db.commit()
    db.close()

    return snapshot_id


def rollback_to_snapshot(domain: str, snapshot_id: int) -> bool:
    """Restore a domain's wordmap from a snapshot"""
    db = get_db()

    # Get snapshot
    snapshot = db.execute('''
        SELECT wordmap_json FROM domain_wordmap_snapshots
        WHERE id = ? AND domain = ?
    ''', (snapshot_id, domain)).fetchone()

    if not snapshot:
        db.close()
        return False

    # Restore wordmap
    db.execute('''
        UPDATE domain_wordmaps
        SET wordmap_json = ?, last_updated = ?
        WHERE domain = ?
    ''', (snapshot['wordmap_json'], datetime.now().isoformat(), domain))

    db.commit()
    db.close()

    return True


def get_diff_suggestions_ollama(diff: Dict, operation: str = "merge") -> List[str]:
    """
    Use Ollama to generate suggestions based on diff

    This is a placeholder - actual implementation would call Ollama API
    """
    # TODO: Integrate with actual Ollama client
    prompt = generate_ai_prompt_from_diff(diff, operation)

    # Placeholder response
    return [
        "integration",
        "synergy",
        "ecosystem",
        "framework",
        "platform"
    ]


# Initialize snapshots table if it doesn't exist
def init_snapshots_table():
    """Create domain_wordmap_snapshots table"""
    db = get_db()
    db.execute('''
        CREATE TABLE IF NOT EXISTS domain_wordmap_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT NOT NULL,
            wordmap_json TEXT NOT NULL,
            description TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (domain) REFERENCES domain_wordmaps(domain)
        )
    ''')
    db.commit()
    db.close()


if __name__ == "__main__":
    # Test the diff engine
    init_snapshots_table()

    print("🔍 Testing Domain Diff Engine\n")

    # Compare two domains
    diff = calculate_wordmap_diff('cringeproof.com', 'soulfra.com')

    print(f"Similarity Score: {diff['similarity_score']}")
    print(f"Shared Words: {diff['shared_words']}")
    print(f"\nOnly in CringeProof: {list(diff['only_in_a'].keys())[:5]}")
    print(f"Only in Soulfra: {list(diff['only_in_b'].keys())[:5]}")

    # Generate AI prompt
    print("\n📝 AI Prompt (Merge Operation):\n")
    print(generate_ai_prompt_from_diff(diff, "merge"))
