#!/usr/bin/env python3
"""
Recovery Code Generator for StPetePros
Inspired by BIP-39 mnemonic generation

Generates human-readable recovery codes like:
- clearwater-plumber-reliable-7239
- tampa-hvac-trusted-4891

Format: [location]-[category]-[quality]-[4-digit-number]

Usage:
    from recovery_code_generator import generate_recovery_code
    code = generate_recovery_code(professional_id=18, category="hvac")
    # Returns: "clearwater-hvac-certified-1834"
"""

import hashlib
import random
from pathlib import Path


class RecoveryCodeGenerator:
    """Generate deterministic recovery codes from wordlist"""

    def __init__(self, wordlist_path='stpetepros-wordlist.txt'):
        self.wordlist_path = Path(wordlist_path)
        self.words = self._load_wordlist()

    def _load_wordlist(self):
        """Load and parse wordlist file"""
        if not self.wordlist_path.exists():
            raise FileNotFoundError(f"Wordlist not found: {self.wordlist_path}")

        words = {
            'locations': [],
            'categories': [],
            'qualities': [],
            'numbers': list(range(1000, 10000))  # 4-digit numbers
        }

        current_section = None

        with open(self.wordlist_path, 'r') as f:
            for line in f:
                line = line.strip()

                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    # Detect section headers
                    if '# Tampa Bay Locations' in line:
                        current_section = 'locations'
                    elif '# Professional Categories' in line or '# Service Types' in line:
                        current_section = 'categories'
                    elif '# Quality/Trust Words' in line or '# Action Words' in line:
                        current_section = 'qualities'
                    continue

                # Add word to current section
                if current_section and current_section != 'numbers':
                    words[current_section].append(line)

        # Deduplicate
        words['locations'] = list(set(words['locations']))
        words['categories'] = list(set(words['categories']))
        words['qualities'] = list(set(words['qualities']))

        return words

    def generate(self, professional_id, category=None, deterministic=True):
        """
        Generate recovery code.

        Args:
            professional_id (int): Database ID of professional
            category (str, optional): Professional category (plumbing, hvac, etc.)
            deterministic (bool): Use professional_id as seed for reproducible codes

        Returns:
            str: Recovery code in format "location-category-quality-number"
        """
        if deterministic:
            # Use professional ID as seed for deterministic generation
            random.seed(professional_id)

        # Select words
        location = random.choice(self.words['locations'])

        # Use provided category if available, otherwise random
        if category:
            # Normalize category (remove underscores, hyphens)
            category_normalized = category.lower().replace('_', '').replace('-', '')
            # Try to find matching word
            category_word = None
            for word in self.words['categories']:
                if category_normalized in word or word in category_normalized:
                    category_word = word
                    break
            if not category_word:
                category_word = random.choice(self.words['categories'])
        else:
            category_word = random.choice(self.words['categories'])

        quality = random.choice(self.words['qualities'])

        # Generate 4-digit number from professional_id
        # Use last 4 digits if ID > 9999, otherwise pad with hash
        if professional_id < 10000:
            # Hash the ID to get consistent 4-digit number
            hash_val = int(hashlib.sha256(str(professional_id).encode()).hexdigest(), 16)
            number = (hash_val % 9000) + 1000  # Ensures 4-digit number (1000-9999)
        else:
            number = professional_id % 10000

        # Reset random seed if deterministic
        if deterministic:
            random.seed()

        return f"{location}-{category_word}-{quality}-{number}"

    def validate(self, recovery_code):
        """
        Validate recovery code format.

        Returns:
            bool: True if valid format
        """
        parts = recovery_code.split('-')

        if len(parts) != 4:
            return False

        location, category, quality, number = parts

        # Check each component
        if location not in self.words['locations']:
            return False
        if category not in self.words['categories']:
            return False
        if quality not in self.words['qualities']:
            return False
        if not number.isdigit() or len(number) != 4:
            return False

        return True


# Convenience function for easy imports
def generate_recovery_code(professional_id, category=None, wordlist_path='stpetepros-wordlist.txt'):
    """
    Generate recovery code for professional.

    Args:
        professional_id (int): Database ID
        category (str, optional): Professional category
        wordlist_path (str): Path to wordlist file

    Returns:
        str: Recovery code
    """
    generator = RecoveryCodeGenerator(wordlist_path)
    return generator.generate(professional_id, category)


def validate_recovery_code(recovery_code, wordlist_path='stpetepros-wordlist.txt'):
    """
    Validate recovery code format.

    Args:
        recovery_code (str): Code to validate
        wordlist_path (str): Path to wordlist file

    Returns:
        bool: True if valid
    """
    generator = RecoveryCodeGenerator(wordlist_path)
    return generator.validate(recovery_code)


if __name__ == "__main__":
    # Test recovery code generation
    print("StPetePros Recovery Code Generator")
    print("=" * 50)

    generator = RecoveryCodeGenerator()

    # Generate test codes
    test_cases = [
        (1, "plumbing"),
        (2, "electrical"),
        (3, "hvac"),
        (18, "roofing"),
        (26, "web-design"),
        (100, "landscaping"),
        (9999, "cleaning")
    ]

    print("\nGenerated Recovery Codes:\n")
    for pro_id, category in test_cases:
        code = generator.generate(pro_id, category)
        is_valid = generator.validate(code)
        print(f"Professional #{pro_id} ({category})")
        print(f"  Code: {code}")
        print(f"  Valid: {is_valid}")
        print()

    # Test deterministic generation (same ID = same code)
    print("\nDeterministic Test (Professional #18):")
    code1 = generator.generate(18, "hvac")
    code2 = generator.generate(18, "hvac")
    print(f"  First:  {code1}")
    print(f"  Second: {code2}")
    print(f"  Match:  {code1 == code2}")
