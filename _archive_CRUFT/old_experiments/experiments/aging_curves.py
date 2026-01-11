#!/usr/bin/env python3
"""
Character Aging Curves

Realistic aging mechanics for D&D campaign:
- Attributes change based on character age
- Peak physical at 25, decline after
- Wisdom/Intelligence increase with age
- Creates meaningful trade-offs (can't max everything)

NO crypto/blockchain - just smart math curves!

Age Ranges:
- 18-25: Peak agility, low wisdom
- 26-35: Balanced, prime adventuring years
- 36-45: Declining agility, high wisdom
- 46-60: Low agility, peak wisdom/intelligence
- 61+: Elder, massive wisdom, low physical stats
"""

import math
from typing import Dict


def calculate_agility(age: int) -> float:
    """
    Agility peaks at 25, then declines

    Age 18: 0.85
    Age 25: 1.00 (peak)
    Age 35: 0.75
    Age 50: 0.45
    Age 65: 0.25

    Returns: 0.0 to 1.0
    """
    if age < 18:
        age = 18  # Min age

    if age <= 25:
        # Rising phase (18 to 25)
        return 0.85 + (age - 18) * 0.02
    else:
        # Declining phase (25+)
        decline_rate = 0.015
        decline = (age - 25) * decline_rate
        return max(0.2, 1.0 - decline)


def calculate_strength(age: int) -> float:
    """
    Strength peaks at 28-30, slower decline than agility

    Age 18: 0.75
    Age 28: 1.00 (peak)
    Age 40: 0.80
    Age 55: 0.55
    Age 70: 0.35

    Returns: 0.0 to 1.0
    """
    if age < 18:
        age = 18

    if age <= 28:
        # Rising phase
        return 0.75 + (age - 18) * 0.025
    else:
        # Declining phase (slower than agility)
        decline_rate = 0.012
        decline = (age - 28) * decline_rate
        return max(0.3, 1.0 - decline)


def calculate_constitution(age: int) -> float:
    """
    Constitution (health/endurance) peaks at 30, gradual decline

    Age 18: 0.80
    Age 30: 1.00 (peak)
    Age 45: 0.75
    Age 60: 0.55
    Age 75: 0.40

    Returns: 0.0 to 1.0
    """
    if age < 18:
        age = 18

    if age <= 30:
        # Rising phase
        return 0.80 + (age - 18) * 0.017
    else:
        # Declining phase
        decline_rate = 0.010
        decline = (age - 30) * decline_rate
        return max(0.35, 1.0 - decline)


def calculate_wisdom(age: int) -> float:
    """
    Wisdom increases with age (experience!)

    Age 18: 0.20
    Age 30: 0.45
    Age 45: 0.70
    Age 60: 0.90
    Age 80: 1.00 (cap)

    Returns: 0.0 to 1.0
    """
    if age < 18:
        age = 18

    # Logarithmic growth (fast at first, slows down)
    wisdom = 0.20 + (age - 18) * 0.012
    return min(1.0, wisdom)


def calculate_intelligence(age: int) -> float:
    """
    Intelligence peaks around 45-50

    Age 18: 0.60
    Age 22: 0.75 (education years)
    Age 45: 1.00 (peak)
    Age 65: 0.90
    Age 80: 0.75

    Returns: 0.0 to 1.0
    """
    if age < 18:
        age = 18

    if age <= 45:
        # Rising phase (learning, education, experience)
        if age <= 22:
            # Fast growth during education
            return 0.60 + (age - 18) * 0.0375
        else:
            # Slower growth through experience
            return 0.75 + (age - 22) * 0.011
    else:
        # Slight decline after peak
        decline_rate = 0.004
        decline = (age - 45) * decline_rate
        return max(0.5, 1.0 - decline)


def calculate_charisma(age: int) -> float:
    """
    Charisma varies with age (confidence vs weathered)

    Age 18: 0.60 (shy/inexperienced)
    Age 30: 0.85 (confident)
    Age 50: 0.90 (peak confidence + experience)
    Age 70: 0.75 (wise but weathered)

    Returns: 0.0 to 1.0
    """
    if age < 18:
        age = 18

    if age <= 50:
        # Rising phase (gaining confidence)
        if age <= 30:
            return 0.60 + (age - 18) * 0.021
        else:
            return 0.85 + (age - 30) * 0.0025
    else:
        # Slight decline (weathering)
        decline_rate = 0.003
        decline = (age - 50) * decline_rate
        return max(0.5, 0.90 - decline)


def get_all_attributes(age: int) -> Dict[str, float]:
    """
    Get all character attributes for a given age

    Returns:
        Dict with all 6 D&D-style attributes
    """
    return {
        'agility': round(calculate_agility(age), 2),
        'strength': round(calculate_strength(age), 2),
        'constitution': round(calculate_constitution(age), 2),
        'wisdom': round(calculate_wisdom(age), 2),
        'intelligence': round(calculate_intelligence(age), 2),
        'charisma': round(calculate_charisma(age), 2)
    }


def get_attribute_change(age_before: int, age_after: int) -> Dict[str, Dict[str, float]]:
    """
    Calculate attribute changes after aging

    Args:
        age_before: Character's age before quest
        age_after: Character's age after quest

    Returns:
        Dict with before/after/delta for each attribute
    """
    before = get_all_attributes(age_before)
    after = get_all_attributes(age_after)

    changes = {}
    for attr in before.keys():
        changes[attr] = {
            'before': before[attr],
            'after': after[attr],
            'delta': round(after[attr] - before[attr], 2),
            'change_percent': round(((after[attr] - before[attr]) / before[attr]) * 100, 1) if before[attr] > 0 else 0
        }

    return changes


def get_age_milestones() -> Dict[int, Dict]:
    """
    Get predefined age milestones

    Returns:
        Dict of age -> milestone info
    """
    return {
        25: {
            'title': '⚡ Peak Agility',
            'description': 'You are at your physical prime! Maximum agility unlocked.',
            'type': 'peak_agility'
        },
        28: {
            'title': '💪 Peak Strength',
            'description': 'Your strength reaches its maximum potential!',
            'type': 'peak_strength'
        },
        30: {
            'title': '❤️ Peak Constitution',
            'description': 'Your endurance and health are at their best.',
            'type': 'peak_constitution'
        },
        40: {
            'title': '🧙 Sage Wisdom Unlocked',
            'description': 'Decades of experience grant you profound wisdom.',
            'type': 'wisdom_unlock'
        },
        45: {
            'title': '🧠 Peak Intelligence',
            'description': 'Your knowledge and mental acuity reach their zenith.',
            'type': 'peak_intelligence'
        },
        50: {
            'title': '🎭 Peak Charisma',
            'description': 'Confidence and experience make you incredibly persuasive.',
            'type': 'peak_charisma'
        },
        60: {
            'title': '👴 Elder Status',
            'description': 'You are now considered an elder. Wisdom at maximum, but physical abilities declining.',
            'type': 'elder_status'
        }
    }


def visualize_aging_curve(start_age: int = 18, end_age: int = 70):
    """
    Print ASCII visualization of aging curves

    Useful for testing/debugging
    """
    print("\n" + "=" * 80)
    print("CHARACTER AGING CURVES")
    print("=" * 80)
    print()

    ages = list(range(start_age, end_age + 1, 5))

    # Print header
    print(f"{'Age':<5} {'Agility':<10} {'Strength':<10} {'Const':<10} {'Wisdom':<10} {'Intel':<10} {'Charisma':<10}")
    print("-" * 80)

    # Print curves
    for age in ages:
        attrs = get_all_attributes(age)
        print(
            f"{age:<5} "
            f"{attrs['agility']:<10.2f} "
            f"{attrs['strength']:<10.2f} "
            f"{attrs['constitution']:<10.2f} "
            f"{attrs['wisdom']:<10.2f} "
            f"{attrs['intelligence']:<10.2f} "
            f"{attrs['charisma']:<10.2f}"
        )

    print()
    print("=" * 80)
    print()


if __name__ == '__main__':
    """Test the aging curves"""

    # Show aging curves
    visualize_aging_curve()

    # Test aging from quest
    print("\n" + "=" * 80)
    print("QUEST AGING SIMULATION")
    print("=" * 80)
    print()

    print("Scenario: Character completes 'Dragon Slayer' quest")
    print("Age before quest: 25 years old")
    print("Quest ages character: +10 years")
    print("Age after quest: 35 years old")
    print()

    changes = get_attribute_change(25, 35)

    print("Attribute Changes:")
    print("-" * 80)
    for attr, change in changes.items():
        symbol = "▲" if change['delta'] > 0 else "▼" if change['delta'] < 0 else "="
        print(
            f"{attr.capitalize():<15} "
            f"{change['before']:.2f} → {change['after']:.2f} "
            f"({symbol} {abs(change['delta']):.2f}, {change['change_percent']:+.1f}%)"
        )

    print()

    # Show milestones
    print("\n" + "=" * 80)
    print("AGE MILESTONES")
    print("=" * 80)
    print()

    milestones = get_age_milestones()
    for age, milestone in sorted(milestones.items()):
        print(f"Age {age}: {milestone['title']}")
        print(f"         {milestone['description']}")
        print()

    print("=" * 80)
