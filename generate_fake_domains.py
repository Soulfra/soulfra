#!/usr/bin/env python3
"""
Generate 200 realistic fake domain names for testing
Output: test-domains.txt
"""

import random

# Domain name parts by category
CATEGORIES = {
    'cooking': {
        'prefixes': ['quick', 'easy', 'healthy', 'delicious', 'perfect', 'homemade', 'simple', 'tasty', 'fresh', 'chef'],
        'topics': ['recipes', 'cooking', 'meals', 'kitchen', 'food', 'chef', 'baking', 'dinner', 'breakfast', 'lunch'],
        'suffixes': ['guide', 'tips', 'pro', 'hub', 'blog', 'daily', 'zone', 'world', 'basics', 'master']
    },
    'tech': {
        'prefixes': ['dev', 'code', 'tech', 'digital', 'smart', 'cloud', 'cyber', 'web', 'app', 'software'],
        'topics': ['developer', 'coding', 'startup', 'innovation', 'solutions', 'tools', 'platform', 'framework', 'api', 'stack'],
        'suffixes': ['hub', 'lab', 'pro', 'guide', 'tips', 'zone', 'central', 'network', 'base', 'forge']
    },
    'privacy': {
        'prefixes': ['secure', 'private', 'safe', 'encrypted', 'anonymous', 'hidden', 'protected', 'vpn', 'shield', 'guard'],
        'topics': ['privacy', 'security', 'data', 'protection', 'encryption', 'anonymous', 'vpn', 'browse', 'shield', 'vault'],
        'suffixes': ['guide', 'pro', 'hub', 'zone', 'central', 'tools', 'first', 'matters', 'tips', 'now']
    },
    'business': {
        'prefixes': ['smart', 'quick', 'pro', 'business', 'growth', 'success', 'profit', 'market', 'sales', 'startup'],
        'topics': ['business', 'marketing', 'sales', 'growth', 'strategy', 'consulting', 'solutions', 'services', 'advisor', 'tools'],
        'suffixes': ['hub', 'pro', 'guide', 'tips', 'zone', 'central', 'network', 'solutions', 'expert', 'coach']
    },
    'health': {
        'prefixes': ['healthy', 'fit', 'wellness', 'active', 'strong', 'vital', 'natural', 'pure', 'balance', 'fresh'],
        'topics': ['health', 'fitness', 'wellness', 'nutrition', 'workout', 'yoga', 'meditation', 'lifestyle', 'body', 'mind'],
        'suffixes': ['guide', 'hub', 'pro', 'tips', 'zone', 'journey', 'life', 'daily', 'coach', 'tracker']
    },
    'finance': {
        'prefixes': ['smart', 'wealth', 'money', 'invest', 'finance', 'budget', 'save', 'profit', 'cash', 'rich'],
        'topics': ['finance', 'money', 'investing', 'budget', 'wealth', 'savings', 'trading', 'crypto', 'stocks', 'passive'],
        'suffixes': ['hub', 'pro', 'guide', 'tips', 'zone', 'guru', 'expert', 'advisor', 'tracker', 'central']
    },
    'education': {
        'prefixes': ['learn', 'study', 'edu', 'smart', 'quick', 'easy', 'master', 'ace', 'skill', 'course'],
        'topics': ['learning', 'education', 'courses', 'tutorials', 'lessons', 'training', 'skills', 'academy', 'school', 'knowledge'],
        'suffixes': ['hub', 'pro', 'guide', 'zone', 'academy', 'lab', 'portal', 'central', 'platform', 'network']
    },
    'travel': {
        'prefixes': ['travel', 'wander', 'adventure', 'explore', 'journey', 'trip', 'vacation', 'discover', 'roam', 'globe'],
        'topics': ['travel', 'adventures', 'destinations', 'trips', 'vacation', 'explore', 'wanderlust', 'journey', 'tourism', 'backpack'],
        'suffixes': ['guide', 'hub', 'tips', 'zone', 'blog', 'world', 'now', 'pro', 'central', 'diary']
    },
    'gaming': {
        'prefixes': ['game', 'play', 'epic', 'pro', 'elite', 'master', 'pixel', 'quest', 'level', 'power'],
        'topics': ['gaming', 'games', 'gamer', 'esports', 'streaming', 'play', 'console', 'arcade', 'victory', 'quest'],
        'suffixes': ['hub', 'zone', 'pro', 'central', 'network', 'arena', 'world', 'guild', 'clan', 'gg']
    },
    'lifestyle': {
        'prefixes': ['modern', 'simple', 'minimalist', 'urban', 'daily', 'lifestyle', 'living', 'home', 'better', 'happy'],
        'topics': ['lifestyle', 'living', 'home', 'design', 'decor', 'style', 'trends', 'life', 'daily', 'simple'],
        'suffixes': ['guide', 'hub', 'blog', 'tips', 'zone', 'daily', 'now', 'matters', 'central', 'life']
    }
}

# TLDs to use
TLDS = ['.com', '.net', '.io', '.org', '.co', '.app', '.dev', '.tech', '.blog', '.club']

def generate_domain(category, cat_data):
    """Generate a single domain name"""
    prefix = random.choice(cat_data['prefixes'])
    topic = random.choice(cat_data['topics'])
    tld = random.choice(TLDS)

    # 70% chance to include suffix
    if random.random() < 0.7:
        suffix = random.choice(cat_data['suffixes'])
        return f"{prefix}{topic}{suffix}{tld}"
    else:
        return f"{prefix}{topic}{tld}"

def generate_fake_domains(count=200):
    """Generate {count} fake domains distributed across categories"""
    domains = []
    categories = list(CATEGORIES.keys())

    # Distribute domains across categories
    per_category = count // len(categories)
    remainder = count % len(categories)

    for i, category in enumerate(categories):
        cat_data = CATEGORIES[category]

        # Add extra domains to first few categories for remainder
        num_domains = per_category + (1 if i < remainder else 0)

        for _ in range(num_domains):
            domain = generate_domain(category, cat_data)
            domains.append(domain)

    # Shuffle to mix categories
    random.shuffle(domains)

    return domains

def main():
    print("🤖 Generating 200 fake domains for testing...")
    print()

    # Generate domains
    domains = generate_fake_domains(200)

    # Write to file
    output_file = 'test-domains.txt'
    with open(output_file, 'w') as f:
        f.write('\n'.join(domains))

    print(f"✅ Generated {len(domains)} fake domains")
    print(f"📄 Saved to: {output_file}")
    print()

    # Show sample
    print("📋 Sample domains:")
    for i, domain in enumerate(domains[:10], 1):
        print(f"  {i}. {domain}")
    print("  ...")
    print(f"  {len(domains)}. {domains[-1]}")
    print()

    # Show distribution
    print("📊 Distribution by TLD:")
    tld_counts = {}
    for domain in domains:
        tld = '.' + domain.split('.')[-1]
        tld_counts[tld] = tld_counts.get(tld, 0) + 1

    for tld, count in sorted(tld_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {tld}: {count} domains")
    print()

    print("🚀 Next steps:")
    print("  1. Visit: http://localhost:5001/admin/domains/import")
    print(f"  2. Copy contents of {output_file}")
    print("  3. Paste into the form")
    print("  4. Click 'Analyze with Ollama'")
    print("  5. Wait 1-3 hours for analysis")
    print("  6. Review and import!")
    print()
    print("💡 To view the file:")
    print(f"  cat {output_file}")
    print()
    print("🧹 To clean up after testing:")
    print("  python cleanup_fake_domains.py")

if __name__ == '__main__':
    main()
