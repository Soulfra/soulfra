#!/usr/bin/env python3
"""
Dual Persona Generator - Display Name + Device Fingerprint → Opposing Communication Pathways

Creates two distinct personas from a user's display name:
- FIRST NAME = "Light" Path → WORK, professional, technical (CalRiven)
- LAST NAME = "Shadow" Path → IDEAS, creative, playful (CringeProof)
- DEVICE FINGERPRINT = Hardware-bound account authentication

When WORK + IDEAS merge = "The Play" - complete user vision

Example:
  Display Name: Matthew Mauer
  Device: SHA256 fingerprint
    - "Matthew" → data_master_5884 (calriven.com - technical execution)
    - "Mauer" → legendary_star_7444 (cringeproof.com - creative vision)
    - Device-bound → submissions auto-linked to personas

Together: Complete project from idea to implementation
"""

import hashlib
import random
from typing import Dict, Tuple, Optional


# LIGHT PATH (First Name) - Professional/Work/Technical
LIGHT_WORDS = {
    'calriven.com': {
        'adjectives': ['code', 'data', 'system', 'tech', 'cloud', 'binary', 'logic', 'cyber', 'quantum', 'neural'],
        'nouns': ['architect', 'engineer', 'builder', 'master', 'forge', 'nexus', 'matrix', 'core', 'hub', 'node']
    },
    'deathtodata.com': {
        'adjectives': ['ghost', 'cipher', 'stealth', 'silent', 'void', 'shadow', 'phantom', 'masked', 'hidden', 'dark'],
        'nouns': ['guardian', 'sentinel', 'warden', 'keeper', 'shield', 'vault', 'fortress', 'bastion', 'aegis', 'haven']
    }
}

# SHADOW PATH (Last Name) - Creative/Ideas/Playful
SHADOW_WORDS = {
    'cringeproof.com': {
        'adjectives': ['viral', 'epic', 'legendary', 'based', 'fire', 'savage', 'peak', 'main', 'meme', 'content'],
        'nouns': ['wizard', 'king', 'queen', 'lord', 'boss', 'legend', 'star', 'icon', 'creator', 'artist']
    },
    'howtocookathome.com': {
        'adjectives': ['fresh', 'tasty', 'spicy', 'savory', 'crispy', 'golden', 'herb', 'chef', 'kitchen', 'home'],
        'nouns': ['master', 'pro', 'guru', 'ninja', 'expert', 'artisan', 'maestro', 'virtuoso', 'wizard', 'ace']
    }
}

# NEUTRAL (Full Name / Username) - Balanced/Spiritual
NEUTRAL_WORDS = {
    'soulfra.com': {
        'adjectives': ['soul', 'spirit', 'cosmic', 'zen', 'ethereal', 'luminous', 'sacred', 'divine', 'mystic', 'serene'],
        'nouns': ['wanderer', 'seeker', 'dreamer', 'guide', 'sage', 'oracle', 'nomad', 'voyager', 'keeper', 'pilgrim']
    }
}


def generate_persona_moniker(name: str, domain: str, persona_type: str) -> str:
    """
    Generate moniker for a specific persona path

    Args:
        name: First name, last name, or full username
        domain: Target domain (e.g., 'calriven.com')
        persona_type: 'light', 'shadow', or 'neutral'

    Returns:
        str: Domain-specific moniker
    """
    # Choose word bank based on persona type
    if persona_type == 'light':
        word_banks = LIGHT_WORDS
    elif persona_type == 'shadow':
        word_banks = SHADOW_WORDS
    else:  # neutral
        word_banks = NEUTRAL_WORDS

    # Get words for domain
    if domain not in word_banks:
        domain = list(word_banks.keys())[0]  # Default to first domain

    words = word_banks[domain]

    # Create deterministic seed from name + domain + persona_type
    seed_string = f"{name}:{domain}:{persona_type}"
    seed_hash = hashlib.sha256(seed_string.encode()).hexdigest()

    # Use hash as seed for consistent randomness
    seed = int(seed_hash[:8], 16)
    rng = random.Random(seed)

    # Pick words based on hash
    adjective = rng.choice(words['adjectives'])
    noun = rng.choice(words['nouns'])

    # Generate 4-digit suffix from hash (deterministic)
    number_seed = int(seed_hash[8:12], 16) % 10000

    # Format: adjective_noun_number
    moniker = f"{adjective}_{noun}_{number_seed:04d}"

    return moniker


def generate_dual_personas(first_name: str, last_name: str) -> Dict[str, Dict[str, str]]:
    """
    Generate dual personas from first and last name

    Args:
        first_name: User's first name (Light path)
        last_name: User's last name (Shadow path)

    Returns:
        dict: {
            'light': {'calriven.com': 'code_architect_1234', ...},
            'shadow': {'cringeproof.com': 'viral_wizard_5678', ...},
            'neutral': {'soulfra.com': 'soul_wanderer_9012', ...}
        }
    """
    full_name = f"{first_name}_{last_name}"

    personas = {
        'light': {},    # Professional/Work (first name)
        'shadow': {},   # Creative/Ideas (last name)
        'neutral': {}   # Balanced/Spiritual (full name)
    }

    # LIGHT PATH (First Name) - Professional domains
    for domain in LIGHT_WORDS.keys():
        personas['light'][domain] = generate_persona_moniker(first_name, domain, 'light')

    # SHADOW PATH (Last Name) - Creative domains
    for domain in SHADOW_WORDS.keys():
        personas['shadow'][domain] = generate_persona_moniker(last_name, domain, 'shadow')

    # NEUTRAL PATH (Full Name) - Soulfra
    for domain in NEUTRAL_WORDS.keys():
        personas['neutral'][domain] = generate_persona_moniker(full_name, domain, 'neutral')

    return personas


def get_persona_for_category(category: str, personas: Dict[str, Dict[str, str]]) -> Tuple[str, str]:
    """
    Determine which persona to use based on voice recording category

    Args:
        category: Voice memo category ('work', 'ideas', 'personal', etc.)
        personas: Output from generate_dual_personas()

    Returns:
        tuple: (domain, moniker)
    """
    # WORK category → LIGHT PATH (first name)
    if category == 'work':
        # Choose CalRiven for technical work
        return ('calriven.com', personas['light'].get('calriven.com', 'unknown'))

    # IDEAS category → SHADOW PATH (last name)
    elif category == 'ideas':
        # Choose CringeProof for creative ideas
        return ('cringeproof.com', personas['shadow'].get('cringeproof.com', 'unknown'))

    # PERSONAL/LEARNING/GOALS → NEUTRAL PATH (full name)
    else:
        # Choose Soulfra for personal content
        return ('soulfra.com', personas['neutral'].get('soulfra.com', 'unknown'))


def check_dual_category_merge(categories: list) -> bool:
    """
    Check if voice recording has BOTH work AND ideas

    This triggers "The Play" - merging light and shadow personas

    Args:
        categories: List of detected categories

    Returns:
        bool: True if both WORK and IDEAS present
    """
    has_work = 'work' in categories
    has_ideas = 'ideas' in categories

    return has_work and has_ideas


def generate_device_fingerprint(user_agent: str, ip_address: str, device_id: Optional[str] = None) -> str:
    """
    Generate device fingerprint from hardware/network characteristics

    Args:
        user_agent: Browser User-Agent string
        ip_address: Client IP address
        device_id: Optional unique device identifier

    Returns:
        str: SHA256 hash of device characteristics
    """
    fingerprint_data = f"{user_agent}|{ip_address}|{device_id or 'unknown'}"
    return hashlib.sha256(fingerprint_data.encode()).hexdigest()


def generate_display_name_personas(display_name: str, device_fingerprint: str) -> Dict[str, any]:
    """
    Generate dual personas from display name + bind to device

    Args:
        display_name: User's chosen display name (e.g., "Matthew Mauer")
        device_fingerprint: SHA256 hash of device characteristics

    Returns:
        dict: {
            'display_name': str,
            'device_fingerprint': str,
            'first_name': str,
            'last_name': str,
            'personas': {
                'light': {...},
                'shadow': {...},
                'neutral': {...}
            },
            'device_bound': True
        }
    """
    # Split display name
    parts = display_name.strip().split()
    first_name = parts[0] if len(parts) > 0 else display_name
    last_name = parts[-1] if len(parts) > 1 else display_name

    # Generate personas
    personas = generate_dual_personas(first_name, last_name)

    return {
        'display_name': display_name,
        'device_fingerprint': device_fingerprint,
        'first_name': first_name,
        'last_name': last_name,
        'personas': personas,
        'device_bound': True
    }


# CLI
if __name__ == '__main__':
    import sys

    if len(sys.argv) < 3:
        print("Dual Persona Generator")
        print("\nUsage:")
        print("  python3 dual_persona_generator.py <first_name> <last_name>")
        print("\nExample:")
        print("  python3 dual_persona_generator.py Matthew Mauer")
        sys.exit(1)

    first_name = sys.argv[1]
    last_name = sys.argv[2]

    print(f"\n🎭 Dual Persona System: {first_name} {last_name}\n")
    print("=" * 70)

    personas = generate_dual_personas(first_name, last_name)

    print(f"\n💼 LIGHT PATH (First Name: {first_name}) - Professional/Work/Technical")
    print("-" * 70)
    for domain, moniker in personas['light'].items():
        print(f"  {domain:25s} → {moniker}")

    print(f"\n🎨 SHADOW PATH (Last Name: {last_name}) - Creative/Ideas/Playful")
    print("-" * 70)
    for domain, moniker in personas['shadow'].items():
        print(f"  {domain:25s} → {moniker}")

    print(f"\n✨ NEUTRAL PATH (Full Name: {first_name} {last_name}) - Balanced/Spiritual")
    print("-" * 70)
    for domain, moniker in personas['neutral'].items():
        print(f"  {domain:25s} → {moniker}")

    print("\n" + "=" * 70)
    print("\n📊 Category Routing:")
    print("-" * 70)

    # Test routing
    test_categories = ['work', 'ideas', 'personal', 'learning', 'goals']
    for category in test_categories:
        domain, moniker = get_persona_for_category(category, personas)
        path = 'LIGHT' if domain == 'calriven.com' else 'SHADOW' if domain == 'cringeproof.com' else 'NEUTRAL'
        print(f"  {category:10s} → {path:8s} → {domain:25s} → {moniker}")

    print("\n" + "=" * 70)
    print("\n🎯 THE PLAY:")
    print("When you record a voice memo with BOTH 'work' AND 'ideas' keywords...")
    print("  → Routes to BOTH personas (LIGHT + SHADOW)")
    print("  → Shows on CalRiven as technical plan (first name)")
    print("  → Shows on CringeProof as creative vision (last name)")
    print("  → Merge unlocks: Complete project from idea to execution")
    print("\n" + "=" * 70)
