#!/usr/bin/env python3
"""
Generate test CSV files with realistic domain data
Usage:
    python3 generate_test_csv.py --count 50
    python3 generate_test_csv.py --count 200
"""

import random
import argparse

# Domain parts by category
DOMAIN_DATA = {
    'cooking': {
        'prefixes': ['quick', 'easy', 'healthy', 'perfect', 'homemade', 'simple', 'tasty', 'fresh'],
        'topics': ['recipes', 'cooking', 'meals', 'kitchen', 'food', 'baking', 'dinner', 'chef'],
        'emoji': '🍳',
        'tier': 'creative',
        'type': 'blog',
        'audience': 'Home cooks and food enthusiasts',
        'purpose': 'Share recipes and cooking tips'
    },
    'tech': {
        'prefixes': ['dev', 'code', 'tech', 'digital', 'smart', 'cloud', 'web', 'app'],
        'topics': ['developer', 'coding', 'startup', 'solutions', 'tools', 'platform', 'api', 'stack'],
        'emoji': '💻',
        'tier': 'business',
        'type': 'platform',
        'audience': 'Developers and tech professionals',
        'purpose': 'Technology solutions and resources'
    },
    'privacy': {
        'prefixes': ['secure', 'private', 'safe', 'encrypted', 'anonymous', 'hidden', 'vpn', 'shield'],
        'topics': ['privacy', 'security', 'data', 'protection', 'encryption', 'browse', 'vault'],
        'emoji': '🔒',
        'tier': 'foundation',
        'type': 'blog',
        'audience': 'Privacy advocates and security-conscious users',
        'purpose': 'Privacy education and tools'
    },
    'business': {
        'prefixes': ['smart', 'pro', 'growth', 'success', 'profit', 'market', 'sales', 'startup'],
        'topics': ['business', 'marketing', 'sales', 'growth', 'strategy', 'consulting', 'services'],
        'emoji': '💼',
        'tier': 'business',
        'type': 'platform',
        'audience': 'Business owners and entrepreneurs',
        'purpose': 'Business growth and consulting'
    },
    'health': {
        'prefixes': ['healthy', 'fit', 'wellness', 'active', 'strong', 'vital', 'balance', 'fresh'],
        'topics': ['health', 'fitness', 'wellness', 'nutrition', 'workout', 'yoga', 'lifestyle'],
        'emoji': '💪',
        'tier': 'creative',
        'type': 'blog',
        'audience': 'Health-conscious individuals',
        'purpose': 'Health and fitness guidance'
    },
    'finance': {
        'prefixes': ['smart', 'wealth', 'money', 'invest', 'finance', 'budget', 'save', 'profit'],
        'topics': ['finance', 'money', 'investing', 'budget', 'wealth', 'savings', 'trading'],
        'emoji': '💰',
        'tier': 'business',
        'type': 'blog',
        'audience': 'Investors and savers',
        'purpose': 'Financial education and advice'
    },
    'education': {
        'prefixes': ['learn', 'study', 'edu', 'smart', 'quick', 'master', 'ace', 'skill'],
        'topics': ['learning', 'education', 'courses', 'tutorials', 'lessons', 'training', 'academy'],
        'emoji': '📚',
        'tier': 'creative',
        'type': 'platform',
        'audience': 'Students and lifelong learners',
        'purpose': 'Educational content and courses'
    },
    'gaming': {
        'prefixes': ['game', 'play', 'epic', 'pro', 'elite', 'master', 'pixel', 'quest'],
        'topics': ['gaming', 'games', 'gamer', 'esports', 'streaming', 'console', 'arena'],
        'emoji': '🎮',
        'tier': 'creative',
        'type': 'community',
        'audience': 'Gamers and esports fans',
        'purpose': 'Gaming content and community'
    },
    'local': {
        'prefixes': ['local', 'city', 'tampa', 'florida', 'community', 'neighborhood', 'area'],
        'topics': ['business', 'services', 'directory', 'guide', 'pros', 'local', 'community'],
        'emoji': '📍',
        'tier': 'business',
        'type': 'directory',
        'audience': 'Local residents and visitors',
        'purpose': 'Local business directory'
    },
    'art': {
        'prefixes': ['creative', 'art', 'design', 'visual', 'modern', 'pixel', 'digital'],
        'topics': ['art', 'design', 'creative', 'gallery', 'studio', 'portfolio', 'graphics'],
        'emoji': '🎨',
        'tier': 'creative',
        'type': 'blog',
        'audience': 'Artists and designers',
        'purpose': 'Art and design showcase'
    }
}

TLDS = ['.com', '.net', '.io', '.org', '.co']

TAGLINES = [
    "Making {topic} simple",
    "Your guide to {topic}",
    "{topic} made easy",
    "Expert {topic} advice",
    "The {topic} experts",
    "Master {topic} today",
    "{topic} tips and tricks",
    "Your {topic} resource"
]

def generate_domain_name(category, data):
    """Generate a domain name for a category"""
    prefix = random.choice(data['prefixes'])
    topic = random.choice(data['topics'])
    tld = random.choice(TLDS)
    return f"{prefix}{topic}{tld}"

def generate_brand_name(domain):
    """Generate brand name from domain"""
    name = domain.split('.')[0]
    return name.title()

def generate_tagline(category):
    """Generate tagline for category"""
    template = random.choice(TAGLINES)
    return template.format(topic=category)

def generate_test_csv(count):
    """Generate test CSV with specified number of domains"""

    categories = list(DOMAIN_DATA.keys())
    lines = []

    # CSV header
    header = "name,domain,category,tier,emoji,brand_type,tagline,target_audience,purpose,ssl_enabled,deployed"
    lines.append(header)

    # Generate domains
    for i in range(count):
        # Pick random category
        category = categories[i % len(categories)]
        data = DOMAIN_DATA[category]

        # Generate domain details
        domain = generate_domain_name(category, data)
        name = generate_brand_name(domain)
        emoji = data['emoji']
        tier = data['tier']
        brand_type = data['type']
        tagline = generate_tagline(category)
        audience = data['audience']
        purpose = data['purpose']

        # Create CSV row
        row = f'{name},{domain},{category},{tier},{emoji},{brand_type},"{tagline}","{audience}","{purpose}",false,false'
        lines.append(row)

    return '\n'.join(lines)

def main():
    parser = argparse.ArgumentParser(description='Generate test CSV files with domain data')
    parser.add_argument('--count', type=int, default=50, help='Number of domains to generate (default: 50)')
    args = parser.parse_args()

    count = args.count
    filename = f'test-domains-{count}.csv'

    print(f"🔧 Generating {count} test domains...")

    csv_content = generate_test_csv(count)

    # Write to file
    with open(filename, 'w') as f:
        f.write(csv_content)

    print(f"✅ Created {filename}")
    print(f"📄 {count + 1} lines (including header)")
    print()
    print("🚀 Next steps:")
    print(f"  1. cat {filename}  # View the file")
    print(f"  2. open http://localhost:5001/admin/domains/csv")
    print(f"  3. Copy contents of {filename}")
    print(f"  4. Paste into CSV import form")
    print(f"  5. Click Parse → Import")
    print()
    print("📊 Category distribution:")

    # Show category counts
    categories = list(DOMAIN_DATA.keys())
    per_category = count // len(categories)
    remainder = count % len(categories)

    for i, cat in enumerate(categories):
        num = per_category + (1 if i < remainder else 0)
        if num > 0:
            emoji = DOMAIN_DATA[cat]['emoji']
            print(f"  {emoji} {cat}: {num} domains")

if __name__ == '__main__':
    main()
