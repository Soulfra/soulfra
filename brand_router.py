#!/usr/bin/env python3
"""
Brand Router - Route Voice Predictions to Correct Domain

Routes predictions based on keywords:
- "real estate", "MLS", "property" → CalRiven
- "crypto", "bitcoin", "privacy", "data" → DeathToData
- Everything else → Soulfra

Usage:
    from brand_router import detect_brand_from_prediction

    brand = detect_brand_from_prediction("Bitcoin will hit 100k")
    # Returns: 'deathtodata'
"""

from typing import Optional


# ==============================================================================
# BRAND KEYWORD ROUTING
# ==============================================================================

BRAND_KEYWORDS = {
    'calriven': [
        # Real estate keywords
        'real estate', 'realtor', 'mls', 'property', 'house', 'home',
        'listing', 'zillow', 'redfin', 'mortgage', 'rent', 'lease',
        'apartment', 'condo', 'land', 'housing', 'buyer', 'seller',
        'broker', 'appraisal', 'inspection', 'closing', 'escrow',
        'square feet', 'bedroom', 'bathroom', 'garage', 'yard',
        'neighborhood', 'hoa', 'foreclosure', 'equity', 'deed'
    ],
    'deathtodata': [
        # Crypto + privacy + data keywords
        'crypto', 'bitcoin', 'btc', 'ethereum', 'eth', 'blockchain',
        'solana', 'sol', 'defi', 'nft', 'web3', 'crypto', 'coin',
        'privacy', 'data', 'tracking', 'surveillance', 'leak',
        'breach', 'hack', 'encrypt', 'vpn', 'tor', 'anonymous',
        'password', 'security', 'gdpr', 'compliance', 'cookie',
        'fingerprint', 'metadata', 'telemetry', 'analytics',
        'facebook', 'google', 'apple', 'meta', 'amazon', 'microsoft'
    ],
    'soulfra': [
        # General life/philosophy/community keywords (default)
        'life', 'authentic', 'community', 'soul', 'purpose', 'meaning',
        'connection', 'relationship', 'friendship', 'love', 'trust',
        'growth', 'learning', 'wisdom', 'experience', 'story',
        'journey', 'reflection', 'mindfulness', 'meditation', 'spiritual'
    ]
}


def detect_brand_from_prediction(prediction_text: str) -> str:
    """
    Detect which brand this prediction belongs to

    Args:
        prediction_text: The user's prediction text

    Returns:
        Brand slug: 'calriven', 'deathtodata', or 'soulfra' (default)
    """
    prediction_lower = prediction_text.lower()

    # Count keyword matches for each brand
    brand_scores = {}

    for brand, keywords in BRAND_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in prediction_lower)
        if score > 0:
            brand_scores[brand] = score

    if not brand_scores:
        # No keywords matched, default to Soulfra
        return 'soulfra'

    # Return brand with highest score
    best_brand = max(brand_scores.items(), key=lambda x: x[1])

    return best_brand[0]


def get_brand_config(brand_slug: str) -> dict:
    """
    Get configuration for a brand

    Args:
        brand_slug: 'calriven', 'deathtodata', 'soulfra', 'stpetepros', or 'cringeproof'

    Returns:
        Brand configuration dict
    """
    configs = {
        'calriven': {
            'name': 'CalRiven',
            'slug': 'calriven',
            'tagline': 'Real Estate Intelligence',
            'debate_folder': 'debates/calriven',
            'github_pages_url': 'https://calriven.github.io',
            'domain': 'calriven.com',
            'primary_color': '#2C5F2D',  # Forest green
            'personality': 'Professional, data-driven, market-focused'
        },
        'deathtodata': {
            'name': 'DeathToData',
            'slug': 'deathtodata',
            'tagline': 'Privacy & Crypto Truth',
            'debate_folder': 'debates/deathtodata',
            'github_pages_url': 'https://deathtodata.github.io',
            'domain': 'deathtodata.com',
            'primary_color': '#1A1A1A',  # Dark gray
            'personality': 'Skeptical, analytical, privacy-focused, anti-surveillance'
        },
        'soulfra': {
            'name': 'Soulfra',
            'slug': 'soulfra',
            'tagline': 'Authentic Community',
            'debate_folder': 'debates',
            'github_pages_url': 'https://soulfra.github.io',
            'domain': 'soulfra.com',
            'primary_color': '#667eea',  # Purple
            'personality': 'Warm, authentic, community-focused, thoughtful'
        },
        'stpetepros': {
            'name': 'StPetePros',
            'slug': 'stpetepros',
            'tagline': 'St. Petersburg Professional Directory',
            'debate_folder': 'debates/stpetepros',
            'github_pages_url': 'https://stpetepros.com',
            'domain': 'stpetepros.com',
            'primary_color': '#0EA5E9',  # Sky blue
            'personality': 'Professional, local-focused, community-driven, verified',
            'geo_restricted': True,  # Only accessible in Tampa Bay area
            'area_codes': ['727', '813'],  # St. Petersburg/Tampa area codes
            'max_radius_miles': 30
        },
        'cringeproof': {
            'name': 'CringeProof',
            'slug': 'cringeproof',
            'tagline': 'Voice Ideas, No Cringe',
            'debate_folder': 'debates/cringeproof',
            'github_pages_url': 'https://cringeproof.com',
            'domain': 'cringeproof.com',
            'primary_color': '#ff006e',  # Hot pink
            'personality': 'Playful, creative, gamified, encouraging'
        }
    }

    return configs.get(brand_slug, configs['soulfra'])


def get_brand_models(brand_slug: str) -> list:
    """
    Get Ollama models for each brand

    Args:
        brand_slug: 'calriven', 'deathtodata', or 'soulfra'

    Returns:
        List of model names to use for this brand
    """
    brand_models = {
        'calriven': [
            'calriven-model:latest',      # Real estate expert model (if exists)
            'mistral:latest',              # General analytical model
        ],
        'deathtodata': [
            'deathtodata-model:latest',    # Privacy/crypto skeptic model
            'mistral:latest',              # General analytical model
        ],
        'soulfra': [
            'soulfra-model:latest',        # Authentic community model
            'deathtodata-model:latest',    # Skeptic counterpoint
            'mistral:latest',              # Creative model
        ]
    }

    return brand_models.get(brand_slug, brand_models['soulfra'])


def check_geo_access(request, brand_config: dict) -> tuple[bool, str]:
    """
    Check if user's location allows access to geo-restricted brand

    Args:
        request: Flask request object
        brand_config: Brand configuration dict

    Returns:
        tuple: (allowed: bool, reason: str)
    """
    # Not geo-restricted? Always allow
    if not brand_config.get('geo_restricted'):
        return (True, '')

    # Allow localhost/dev access with ?geo_override=true
    if request.args.get('geo_override') == 'true':
        host = request.headers.get('Host', '').lower()
        if 'localhost' in host or '127.0.0.1' in host or '192.168.' in host:
            return (True, 'Dev override enabled')

    # Get client IP (handle X-Forwarded-For for proxies/tunnels)
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if ',' in client_ip:
        client_ip = client_ip.split(',')[0].strip()

    # Allow localhost/private IPs for development
    if client_ip in ['127.0.0.1', '::1'] or client_ip.startswith('192.168.') or client_ip.startswith('10.'):
        return (True, 'Local network access')

    # TODO: Add real IP geolocation check
    # For now, geo-restriction is documented but not enforced
    # In production, integrate with:
    # - ipapi.co API (free tier: 1000 requests/day)
    # - MaxMind GeoLite2 database (offline lookup)
    # - CloudFlare geolocation headers (if using CF)

    # Example implementation:
    # try:
    #     import requests
    #     response = requests.get(f'https://ipapi.co/{client_ip}/json/', timeout=2)
    #     data = response.json()
    #
    #     # Check if in Florida
    #     if data.get('region_code') != 'FL':
    #         return (False, f"StPetePros is only available in Florida (detected: {data.get('region')})")
    #
    #     # Check if within 30 miles of St. Petersburg (27.7676° N, 82.6403° W)
    #     lat, lon = data.get('latitude'), data.get('longitude')
    #     distance = haversine_distance(lat, lon, 27.7676, -82.6403)
    #
    #     if distance > brand_config.get('max_radius_miles', 30):
    #         return (False, f"StPetePros is only available within 30 miles of St. Petersburg")
    #
    #     return (True, f"Access from {data.get('city')}, FL")
    # except:
    #     # On error, allow access (fail open)
    #     return (True, 'Geo-check unavailable')

    return (True, 'Geo-restriction not yet enforced')


def detect_brand_from_request(request) -> str:
    """
    Detect brand from HTTP request

    Checks in order:
    1. ?brand= query parameter (for local development/testing)
    2. Host header (for production domains)
    3. Defaults to 'stpetepros' for localhost

    Args:
        request: Flask request object

    Returns:
        Brand slug string
    """
    # 1. Check query parameter first (highest priority for testing)
    brand_param = request.args.get('brand', '').lower()
    if brand_param in ['soulfra', 'stpetepros', 'cringeproof', 'calriven', 'deathtodata']:
        return brand_param

    # 2. Check Host header
    host = request.headers.get('Host', '').lower()

    # Map domains to brand slugs
    domain_mapping = {
        'stpetepros.com': 'stpetepros',
        'www.stpetepros.com': 'stpetepros',
        'cringeproof.com': 'cringeproof',
        'www.cringeproof.com': 'cringeproof',
        'soulfra.com': 'soulfra',
        'www.soulfra.com': 'soulfra',
        'calriven.com': 'calriven',
        'www.calriven.com': 'calriven',
        'deathtodata.com': 'deathtodata',
        'www.deathtodata.com': 'deathtodata'
    }

    # Check for exact domain match (strip port if present)
    host_without_port = host.split(':')[0]
    if host_without_port in domain_mapping:
        return domain_mapping[host_without_port]

    # 3. Default to stpetepros for localhost
    if 'localhost' in host or '127.0.0.1' in host or '192.168.' in host:
        return 'stpetepros'

    # 4. Ultimate fallback
    return 'soulfra'


# ==============================================================================
# CLI TESTING
# ==============================================================================

def main():
    """Test brand routing"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 brand_router.py <prediction text>")
        print()
        print("Examples:")
        print('  python3 brand_router.py "Bitcoin will hit 100k by March"')
        print('  python3 brand_router.py "Real estate prices will crash in CA"')
        print('  python3 brand_router.py "Community trust is the future"')
        return

    prediction_text = sys.argv[1]

    print("=" * 70)
    print("🔍 BRAND ROUTING TEST")
    print("=" * 70)
    print()
    print(f"Prediction: {prediction_text}")
    print()

    # Detect brand
    brand_slug = detect_brand_from_prediction(prediction_text)
    config = get_brand_config(brand_slug)
    models = get_brand_models(brand_slug)

    print(f"✅ Routed to: {config['name']}")
    print(f"   Slug: {config['slug']}")
    print(f"   Tagline: {config['tagline']}")
    print(f"   Debate folder: {config['debate_folder']}")
    print(f"   Models: {', '.join(models)}")
    print(f"   Personality: {config['personality']}")
    print()


if __name__ == '__main__':
    main()
