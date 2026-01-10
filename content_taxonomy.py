"""
Content Taxonomy - How Content is Organized by Trade/Vertical

Defines:
- Trade categories (plumber, electrician, podcast, etc.)
- Keywords per trade
- Service types
- Auto-detection from voice content

Usage:
    from content_taxonomy import detect_trade, get_trade_keywords

    # Detect trade from voice transcript
    trade = detect_trade("I fixed a leaky faucet today...")
    # Returns: 'plumber'

    # Get keywords for trade
    keywords = get_trade_keywords('plumber')
    # Returns: ['plumber', 'plumbing', 'faucet', 'leak', ...]
"""

from typing import List, Dict, Optional


# ============================================================================
# Trade Category Definitions
# ============================================================================

TRADE_CATEGORIES = {
    # Licensed Professionals (Trades)
    'plumber': {
        'display_name': 'Plumber',
        'keywords': [
            'plumber', 'plumbing', 'faucet', 'leak', 'drain', 'pipe', 'water',
            'sink', 'toilet', 'shower', 'bathtub', 'sewer', 'clog', 'unclog',
            'water heater', 'tankless', 'disposal', 'garbage disposal',
            'valve', 'shutoff', 'fixture', 'pressure', 'flow'
        ],
        'service_types': ['emergency', 'residential', 'commercial', '24/7'],
        'common_jobs': [
            'fix leaky faucet',
            'unclog drain',
            'water heater repair',
            'toilet running',
            'low water pressure',
            'sewer line backup',
            'garbage disposal repair',
            'install faucet'
        ],
        'license_types': ['Plumbing Contractor', 'Master Plumber', 'Journeyman Plumber'],
        'cities': []  # Populated dynamically
    },

    'electrician': {
        'display_name': 'Electrician',
        'keywords': [
            'electrician', 'electrical', 'electric', 'wiring', 'wire', 'outlet',
            'switch', 'breaker', 'circuit', 'panel', 'voltage', 'amp',
            'lighting', 'light', 'fixture', 'ceiling fan', 'gfci', 'afci',
            'surge', 'generator', 'meter', 'fuse', 'short circuit'
        ],
        'service_types': ['emergency', 'residential', 'commercial', '24/7'],
        'common_jobs': [
            'install outlet',
            'fix breaker',
            'rewire house',
            'install ceiling fan',
            'upgrade electrical panel',
            'add circuit',
            'install generator',
            'troubleshoot electrical issue'
        ],
        'license_types': ['Electrical Contractor', 'Master Electrician', 'Journeyman Electrician'],
        'cities': []
    },

    'hvac': {
        'display_name': 'HVAC Technician',
        'keywords': [
            'hvac', 'heating', 'cooling', 'ac', 'air conditioning', 'furnace',
            'air conditioner', 'heat pump', 'thermostat', 'duct', 'ductwork',
            'ventilation', 'refrigerant', 'compressor', 'evaporator', 'condenser',
            'filter', 'air filter', 'temperature', 'climate control'
        ],
        'service_types': ['emergency', 'residential', 'commercial', '24/7', 'maintenance'],
        'common_jobs': [
            'ac repair',
            'furnace repair',
            'hvac maintenance',
            'replace air filter',
            'install thermostat',
            'duct cleaning',
            'refrigerant recharge',
            'replace ac unit'
        ],
        'license_types': ['HVAC Contractor', 'EPA Certification', 'NATE Certification'],
        'cities': []
    },

    'contractor': {
        'display_name': 'General Contractor',
        'keywords': [
            'contractor', 'construction', 'remodel', 'renovation', 'build',
            'drywall', 'framing', 'foundation', 'roofing', 'siding', 'deck',
            'permit', 'blueprint', 'inspection', 'code', 'building code'
        ],
        'service_types': ['residential', 'commercial', 'remodeling', 'new construction'],
        'common_jobs': [
            'home renovation',
            'kitchen remodel',
            'bathroom remodel',
            'room addition',
            'deck building',
            'roof replacement',
            'foundation repair',
            'drywall repair'
        ],
        'license_types': ['General Contractor', 'Licensed Builder'],
        'cities': []
    },

    # Content Creators
    'podcast': {
        'display_name': 'Podcast',
        'keywords': [
            'podcast', 'episode', 'interview', 'guest', 'host', 'discuss',
            'discussion', 'conversation', 'talk', 'show', 'listen', 'audio',
            'recording', 'microphone', 'series', 'season'
        ],
        'content_types': ['interview', 'solo', 'panel', 'narrative', 'educational'],
        'common_topics': [
            'business',
            'technology',
            'lifestyle',
            'health',
            'entrepreneurship',
            'comedy',
            'news',
            'true crime'
        ],
        'platforms': ['Spotify', 'Apple Podcasts', 'YouTube', 'Google Podcasts'],
        'cities': []  # Not location-specific
    },

    'youtube': {
        'display_name': 'YouTuber',
        'keywords': [
            'youtube', 'video', 'vlog', 'vlogging', 'subscribe', 'channel',
            'thumbnail', 'views', 'watch', 'stream', 'streaming', 'live',
            'upload', 'camera', 'editing', 'content creator'
        ],
        'content_types': ['tutorial', 'vlog', 'review', 'gaming', 'educational', 'entertainment'],
        'common_topics': [
            'tech reviews',
            'gaming',
            'beauty',
            'cooking',
            'diy',
            'travel',
            'fitness',
            'comedy'
        ],
        'platforms': ['YouTube', 'YouTube Shorts', 'TikTok'],
        'cities': []
    },

    'blog': {
        'display_name': 'Blogger',
        'keywords': [
            'blog', 'blogger', 'write', 'writing', 'article', 'post',
            'content', 'publish', 'newsletter', 'essay', 'opinion',
            'tutorial', 'guide', 'how-to', 'list', 'review'
        ],
        'content_types': ['tutorial', 'listicle', 'review', 'opinion', 'news', 'personal'],
        'common_topics': [
            'technology',
            'travel',
            'food',
            'lifestyle',
            'parenting',
            'finance',
            'health',
            'fashion'
        ],
        'platforms': ['WordPress', 'Medium', 'Substack', 'Ghost'],
        'cities': []
    },

    # Small Businesses (Future)
    'restaurant': {
        'display_name': 'Restaurant',
        'keywords': [
            'restaurant', 'food', 'menu', 'chef', 'kitchen', 'cooking',
            'recipe', 'dish', 'meal', 'dine', 'dining', 'cuisine',
            'reservation', 'table', 'delivery', 'takeout'
        ],
        'business_types': ['fast food', 'casual dining', 'fine dining', 'cafe', 'food truck'],
        'common_topics': [
            'specials',
            'new menu items',
            'recipes',
            'behind the scenes',
            'chef tips',
            'food sourcing'
        ],
        'platforms': ['Yelp', 'Google My Business', 'DoorDash', 'Uber Eats'],
        'cities': []  # Very location-specific
    }
}


# ============================================================================
# Trade Detection
# ============================================================================

def detect_trade(transcript: str, confidence_threshold: float = 0.3) -> Optional[str]:
    """
    Auto-detect trade/vertical from voice transcript

    Args:
        transcript: Voice transcript text
        confidence_threshold: Minimum confidence score (0-1)

    Returns:
        Trade category string or None if unclear

    Example:
        >>> detect_trade("I fixed a leaky faucet today")
        'plumber'
        >>> detect_trade("Today's episode we interview...")
        'podcast'
    """
    transcript_lower = transcript.lower()

    # Score each trade by keyword matches
    scores = {}

    for trade, config in TRADE_CATEGORIES.items():
        score = 0
        keyword_count = 0

        for keyword in config.get('keywords', []):
            if keyword in transcript_lower:
                score += 1
                keyword_count += 1

        # Normalize score by number of keywords checked
        if len(config.get('keywords', [])) > 0:
            normalized_score = score / len(config['keywords'])
            scores[trade] = normalized_score

    # Get highest scoring trade
    if scores:
        best_trade = max(scores, key=scores.get)
        best_score = scores[best_trade]

        if best_score >= confidence_threshold:
            return best_trade

    return None


def detect_trade_with_confidence(transcript: str) -> Dict[str, float]:
    """
    Get confidence scores for all trades

    Args:
        transcript: Voice transcript text

    Returns:
        Dictionary of trade -> confidence score

    Example:
        >>> detect_trade_with_confidence("I'm a plumber and electrician")
        {'plumber': 0.45, 'electrician': 0.38, 'hvac': 0.05, ...}
    """
    transcript_lower = transcript.lower()

    scores = {}

    for trade, config in TRADE_CATEGORIES.items():
        score = 0

        for keyword in config.get('keywords', []):
            if keyword in transcript_lower:
                score += 1

        # Normalize
        if len(config.get('keywords', [])) > 0:
            normalized_score = score / len(config['keywords'])
            scores[trade] = round(normalized_score, 3)

    return scores


# ============================================================================
# Trade Information
# ============================================================================

def get_trade_keywords(trade: str) -> List[str]:
    """
    Get keywords for a trade

    Args:
        trade: Trade category

    Returns:
        List of keywords

    Example:
        >>> get_trade_keywords('plumber')
        ['plumber', 'plumbing', 'faucet', 'leak', ...]
    """
    config = TRADE_CATEGORIES.get(trade)
    if config:
        return config.get('keywords', [])
    return []


def get_trade_service_types(trade: str) -> List[str]:
    """
    Get service types for a trade

    Args:
        trade: Trade category

    Returns:
        List of service types

    Example:
        >>> get_trade_service_types('plumber')
        ['emergency', 'residential', 'commercial', '24/7']
    """
    config = TRADE_CATEGORIES.get(trade)
    if config:
        return config.get('service_types', [])
    return []


def get_trade_common_jobs(trade: str) -> List[str]:
    """
    Get common jobs/topics for a trade

    Args:
        trade: Trade category

    Returns:
        List of common jobs

    Example:
        >>> get_trade_common_jobs('plumber')
        ['fix leaky faucet', 'unclog drain', ...]
    """
    config = TRADE_CATEGORIES.get(trade)
    if config:
        return config.get('common_jobs', []) or config.get('common_topics', [])
    return []


def get_all_trades() -> List[str]:
    """
    Get list of all available trades

    Returns:
        List of trade category strings

    Example:
        >>> get_all_trades()
        ['plumber', 'electrician', 'hvac', 'podcast', 'youtube', ...]
    """
    return list(TRADE_CATEGORIES.keys())


def get_trade_display_name(trade: str) -> str:
    """
    Get human-readable name for trade

    Args:
        trade: Trade category

    Returns:
        Display name

    Example:
        >>> get_trade_display_name('plumber')
        'Plumber'
    """
    config = TRADE_CATEGORIES.get(trade)
    if config:
        return config.get('display_name', trade.title())
    return trade.title()


def get_trades_by_vertical(vertical: str) -> List[str]:
    """
    Get trades in a specific vertical

    Args:
        vertical: 'professional', 'creator', or 'business'

    Returns:
        List of trade categories

    Example:
        >>> get_trades_by_vertical('professional')
        ['plumber', 'electrician', 'hvac', 'contractor']
    """
    vertical_mapping = {
        'professional': ['plumber', 'electrician', 'hvac', 'contractor'],
        'creator': ['podcast', 'youtube', 'blog'],
        'business': ['restaurant']
    }

    return vertical_mapping.get(vertical, [])


# ============================================================================
# Keyword Expansion
# ============================================================================

def expand_keywords(base_keyword: str, trade: str) -> List[str]:
    """
    Expand base keyword with variations

    Args:
        base_keyword: Base keyword (e.g., "plumber")
        trade: Trade category

    Returns:
        List of keyword variations

    Example:
        >>> expand_keywords('plumber', 'plumber')
        ['plumber', 'emergency plumber', '24/7 plumber', 'licensed plumber', ...]
    """
    modifiers = [
        '',  # Base keyword
        'emergency',
        '24/7',
        'licensed',
        'best',
        'affordable',
        'local',
        'professional',
        'experienced',
        'trusted'
    ]

    service_types = get_trade_service_types(trade)

    variations = []

    # Add base keyword
    variations.append(base_keyword)

    # Add with modifiers
    for modifier in modifiers:
        if modifier:
            variations.append(f"{modifier} {base_keyword}")

    # Add with service types
    for service_type in service_types:
        if service_type not in modifiers:
            variations.append(f"{service_type} {base_keyword}")

    return list(set(variations))  # Remove duplicates


# ============================================================================
# Content Quality Hints
# ============================================================================

def get_content_structure_hints(trade: str) -> Dict:
    """
    Get content structure suggestions for a trade

    Args:
        trade: Trade category

    Returns:
        Dictionary with structure hints

    Example:
        >>> hints = get_content_structure_hints('plumber')
        >>> print(hints['suggested_sections'])
        ['Introduction', 'Tools Needed', 'Step-by-Step Instructions', ...]
    """
    # Professional trades
    if trade in ['plumber', 'electrician', 'hvac', 'contractor']:
        return {
            'suggested_sections': [
                'Introduction',
                'Tools & Materials Needed',
                'Safety Warnings',
                'Step-by-Step Instructions',
                'Common Mistakes to Avoid',
                'When to Call a Professional',
                'Conclusion & Contact Info'
            ],
            'ideal_length': '5-15 minutes',
            'tone': 'Professional, helpful, educational',
            'avoid': ['Sales pitches', 'Competitor mentions', 'Personal rambling']
        }

    # Content creators
    elif trade in ['podcast', 'youtube', 'blog']:
        return {
            'suggested_sections': [
                'Hook/Introduction',
                'Main Content',
                'Key Takeaways',
                'Call to Action',
                'Credits/Outro'
            ],
            'ideal_length': '10-30 minutes',
            'tone': 'Engaging, conversational, authentic',
            'avoid': ['Too many tangents', 'Poor audio quality', 'Excessive filler words']
        }

    # Businesses
    elif trade in ['restaurant']:
        return {
            'suggested_sections': [
                'Introduction',
                'Today\'s Special/Topic',
                'Behind the Scenes',
                'Call to Action (visit us!)',
                'Conclusion'
            ],
            'ideal_length': '3-10 minutes',
            'tone': 'Friendly, inviting, authentic',
            'avoid': ['Overly promotional', 'Menu reading', 'Complex recipes']
        }

    # Default
    else:
        return {
            'suggested_sections': [
                'Introduction',
                'Main Content',
                'Conclusion'
            ],
            'ideal_length': '5-15 minutes',
            'tone': 'Clear, helpful, authentic',
            'avoid': ['Rambling', 'Off-topic content']
        }


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    """
    CLI interface for taxonomy exploration

    Usage:
        python content_taxonomy.py --detect "I fixed a leaky faucet"
        python content_taxonomy.py --keywords plumber
        python content_taxonomy.py --list-trades
    """
    import sys

    if '--detect' in sys.argv:
        idx = sys.argv.index('--detect')
        if idx + 1 < len(sys.argv):
            transcript = sys.argv[idx + 1]
            trade = detect_trade(transcript)
            if trade:
                print(f"✅ Detected trade: {get_trade_display_name(trade)} ({trade})")
                scores = detect_trade_with_confidence(transcript)
                print(f"\n📊 Confidence scores:")
                for t, score in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5]:
                    print(f"  {get_trade_display_name(t)}: {score:.1%}")
            else:
                print("❌ Could not detect trade (no clear match)")

    elif '--keywords' in sys.argv:
        idx = sys.argv.index('--keywords')
        if idx + 1 < len(sys.argv):
            trade = sys.argv[idx + 1]
            keywords = get_trade_keywords(trade)
            print(f"\n📝 Keywords for {get_trade_display_name(trade)}:")
            for keyword in keywords[:20]:  # Show first 20
                print(f"  - {keyword}")
            if len(keywords) > 20:
                print(f"  ... and {len(keywords) - 20} more")

    elif '--list-trades' in sys.argv:
        print("\n📚 Available Trade Categories:\n")
        for vertical in ['professional', 'creator', 'business']:
            trades = get_trades_by_vertical(vertical)
            print(f"{vertical.title()}s:")
            for trade in trades:
                print(f"  - {get_trade_display_name(trade)} ({trade})")
            print()

    else:
        print("""
Usage:
    python content_taxonomy.py --detect "transcript text"
    python content_taxonomy.py --keywords plumber
    python content_taxonomy.py --list-trades
""")


if __name__ == '__main__':
    main()
