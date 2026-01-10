"""
Programmatic SEO (pSEO) Landing Page Generator

Takes a single tutorial and generates 50+ landing page variations
targeting different cities, keywords, and long-tail searches.

Example:
    1 tutorial "How to Fix Leaky Faucet"
    → 50+ pages:
      - tampa-plumber
      - tampa-emergency-plumber
      - st-petersburg-plumber
      - clearwater-24-7-plumber
      - etc.

Usage:
    from pseo_generator import generate_pseo_landing_pages

    # Generate pages for tutorial
    pages_created = generate_pseo_landing_pages(tutorial_id=123)
    # Returns: 52 (52 landing pages created)
"""

from typing import List, Dict, Optional, Tuple
import re
from datetime import datetime
from models import (
    db,
    Tutorial,
    ProfessionalProfile,
    PSEOLandingPage
)


# ============================================================================
# Configuration
# ============================================================================

# City databases (could be loaded from file/API)
CITY_DATABASES = {
    'Tampa': [
        'Tampa', 'St. Petersburg', 'Clearwater', 'Brandon', 'Riverview',
        'Wesley Chapel', 'Land O Lakes', 'Lutz', 'Carrollwood',
        'Temple Terrace', 'Plant City', 'Largo', 'Pinellas Park',
        'Safety Harbor', 'Dunedin', 'Palm Harbor'
    ],
    'Orlando': [
        'Orlando', 'Winter Park', 'Kissimmee', 'Altamonte Springs',
        'Lake Mary', 'Sanford', 'Oviedo', 'Winter Garden',
        'Apopka', 'Maitland'
    ],
    'Miami': [
        'Miami', 'Miami Beach', 'Coral Gables', 'Hialeah', 'Kendall',
        'Homestead', 'Key Biscayne', 'Doral', 'Aventura',
        'North Miami Beach'
    ],
    'Jacksonville': [
        'Jacksonville', 'Jacksonville Beach', 'Orange Park', 'Ponte Vedra',
        'St. Augustine', 'Fernandina Beach'
    ]
}

# Keyword modifiers (trade-specific)
KEYWORD_MODIFIERS = {
    'plumber': [
        'plumber',
        'emergency plumber',
        '24/7 plumber',
        'licensed plumber',
        'best plumber',
        'affordable plumber',
        'residential plumber',
        'commercial plumber'
    ],
    'electrician': [
        'electrician',
        'emergency electrician',
        '24/7 electrician',
        'licensed electrician',
        'residential electrician',
        'commercial electrician'
    ],
    'hvac': [
        'hvac',
        'hvac repair',
        'ac repair',
        'heating repair',
        'hvac installation',
        'hvac maintenance',
        '24/7 hvac'
    ],
    'contractor': [
        'contractor',
        'general contractor',
        'home renovation contractor',
        'licensed contractor',
        'residential contractor'
    ]
}

# City-specific facts (for localization)
CITY_FACTS = {
    'Tampa': 'We proudly serve Tampa residents, from Downtown to Westshore to New Tampa.',
    'St. Petersburg': 'Serving St. Pete from the Pier to Tyrone Mall and everywhere in between.',
    'Clearwater': 'From Clearwater Beach to Countryside, we\'ve got you covered.',
    'Orlando': 'Serving the Orlando metro area, including theme park districts.',
    'Miami': 'Serving Miami-Dade County, from South Beach to Homestead.',
    'Jacksonville': 'Serving Jacksonville and the First Coast region.',
}


# ============================================================================
# Main Generator Function
# ============================================================================

def generate_pseo_landing_pages(tutorial_id: int) -> int:
    """
    Generate 50+ landing page variations for a tutorial

    Args:
        tutorial_id: ID of tutorial to generate pages for

    Returns:
        Number of pages created

    Example:
        >>> pages_created = generate_pseo_landing_pages(123)
        >>> print(f"Created {pages_created} landing pages")
        Created 52 landing pages
    """
    tutorial = Tutorial.query.get(tutorial_id)

    if not tutorial:
        raise ValueError(f"Tutorial {tutorial_id} not found")

    professional = tutorial.professional

    if not professional:
        raise ValueError(f"Tutorial {tutorial_id} has no associated professional")

    # Get service area cities
    cities = get_service_area_cities(professional)

    # Extract keywords from tutorial
    keywords = extract_keywords_from_tutorial(tutorial)

    # Generate landing pages
    pages_created = 0

    for city in cities:
        for keyword in keywords:
            # Create landing page
            landing_page = create_pseo_landing_page(
                tutorial=tutorial,
                professional=professional,
                city=city,
                keyword=keyword
            )

            if landing_page:
                pages_created += 1

    # Update tutorial stats
    tutorial.pseo_pages_count = pages_created
    db.session.commit()

    print(f"✅ Created {pages_created} pSEO landing pages for tutorial #{tutorial_id}")

    return pages_created


# ============================================================================
# Service Area Detection
# ============================================================================

def get_service_area_cities(professional: ProfessionalProfile) -> List[str]:
    """
    Get cities in professional's service area

    Args:
        professional: Professional profile

    Returns:
        List of city names

    Example:
        >>> prof = ProfessionalProfile.query.get(1)
        >>> cities = get_service_area_cities(prof)
        >>> print(cities)
        ['Tampa', 'St. Petersburg', 'Clearwater', ...]
    """
    # Start with professional's city
    primary_city = professional.address_city or 'Tampa'

    # Find which metro area this city belongs to
    metro_cities = []

    for metro, cities in CITY_DATABASES.items():
        if primary_city in cities:
            metro_cities = cities
            break

    # Fallback to Tampa if city not found
    if not metro_cities:
        metro_cities = CITY_DATABASES['Tampa']

    # Limit to 10-15 cities (prevent too many pages)
    return metro_cities[:15]


# ============================================================================
# Keyword Extraction
# ============================================================================

def extract_keywords_from_tutorial(tutorial: Tutorial) -> List[str]:
    """
    Extract targetable keywords from tutorial content

    Args:
        tutorial: Tutorial object

    Returns:
        List of keyword phrases

    Example:
        >>> tutorial = Tutorial.query.get(1)
        >>> keywords = extract_keywords_from_tutorial(tutorial)
        >>> print(keywords)
        ['plumber', 'emergency plumber', '24/7 plumber', ...]
    """
    # Detect trade from license type
    license_type = tutorial.professional.license_type or 'plumber'
    trade = detect_trade(license_type)

    # Get keyword modifiers for this trade
    base_keywords = KEYWORD_MODIFIERS.get(trade, KEYWORD_MODIFIERS['plumber'])

    # Extract specific keywords from tutorial title
    title_keywords = extract_title_keywords(tutorial.title)

    # Combine
    all_keywords = base_keywords + title_keywords

    # Remove duplicates
    return list(set(all_keywords))


def detect_trade(license_type: str) -> str:
    """
    Detect trade from license type

    Args:
        license_type: Professional's license type

    Returns:
        Trade identifier

    Example:
        >>> detect_trade("Plumbing Contractor")
        'plumber'
        >>> detect_trade("HVAC Contractor")
        'hvac'
    """
    license_lower = license_type.lower()

    if 'plumb' in license_lower:
        return 'plumber'
    elif 'electric' in license_lower:
        return 'electrician'
    elif 'hvac' in license_lower or 'air' in license_lower or 'cooling' in license_lower:
        return 'hvac'
    elif 'contract' in license_lower:
        return 'contractor'
    else:
        return 'plumber'  # Default


def extract_title_keywords(title: str) -> List[str]:
    """
    Extract specific keywords from tutorial title

    Args:
        title: Tutorial title

    Returns:
        List of specific keywords

    Example:
        >>> extract_title_keywords("How to Fix a Leaky Faucet")
        ['fix leaky faucet', 'faucet repair']
    """
    keywords = []

    title_lower = title.lower()

    # Common patterns
    patterns = {
        'fix': ['fix', 'repair'],
        'install': ['install', 'installation'],
        'replace': ['replace', 'replacement'],
        'maintain': ['maintain', 'maintenance']
    }

    for action, variations in patterns.items():
        if action in title_lower:
            # Extract noun after action word
            # e.g., "fix leaky faucet" → "faucet repair"
            words = title_lower.split()
            if action in words:
                idx = words.index(action)
                # Get next 2-3 words
                noun_phrase = ' '.join(words[idx+1:idx+3])
                keywords.append(f"{action} {noun_phrase}")

                # Add variation
                for variation in variations:
                    keywords.append(f"{noun_phrase} {variation}")

    return keywords


# ============================================================================
# Landing Page Creation
# ============================================================================

def create_pseo_landing_page(
    tutorial: Tutorial,
    professional: ProfessionalProfile,
    city: str,
    keyword: str
) -> Optional[PSEOLandingPage]:
    """
    Create individual pSEO landing page

    Args:
        tutorial: Source tutorial
        professional: Professional profile
        city: Target city
        keyword: Target keyword

    Returns:
        Created landing page or None if duplicate

    Example:
        >>> page = create_pseo_landing_page(
        ...     tutorial=tutorial,
        ...     professional=professional,
        ...     city='Tampa',
        ...     keyword='emergency plumber'
        ... )
        >>> print(page.slug)
        'tampa-emergency-plumber'
    """
    # Generate slug
    slug = generate_slug(city, keyword)

    # Check if already exists
    existing = PSEOLandingPage.query.filter_by(
        professional_id=professional.id,
        slug=slug
    ).first()

    if existing:
        print(f"  ⏭️  Skipping {slug} (already exists)")
        return None

    # Generate SEO content
    long_tail_keyword = f"{keyword} in {city}"
    h1_headline = generate_h1(city, keyword, professional.business_name)
    meta_title = generate_meta_title(city, keyword, professional.business_name)
    meta_description = generate_meta_description(city, keyword, professional)

    # Customize content for city
    content_html = customize_content_for_city(
        base_content=tutorial.html_content,
        city=city,
        keyword=keyword,
        professional=professional
    )

    # Full URL
    if professional.subdomain:
        full_url = f"{professional.subdomain}.cringeproof.com/{slug}"
    else:
        full_url = f"cringeproof.com/p/{professional.id}/{slug}"

    # Create landing page
    landing_page = PSEOLandingPage(
        tutorial_id=tutorial.id,
        professional_id=professional.id,
        slug=slug,
        full_url=full_url,
        target_city=city,
        target_keyword=keyword,
        long_tail_keyword=long_tail_keyword,
        h1_headline=h1_headline,
        meta_title=meta_title,
        meta_description=meta_description,
        content_html=content_html,
        impressions=0,
        clicks=0,
        leads=0
    )

    db.session.add(landing_page)

    print(f"  ✅ Created: {slug}")

    return landing_page


# ============================================================================
# SEO Content Generation
# ============================================================================

def generate_slug(city: str, keyword: str) -> str:
    """
    Generate URL slug from city + keyword

    Args:
        city: City name
        keyword: Keyword phrase

    Returns:
        URL-safe slug

    Example:
        >>> generate_slug("St. Petersburg", "emergency plumber")
        'st-petersburg-emergency-plumber'
    """
    # Combine and clean
    combined = f"{city} {keyword}"

    # Lowercase
    slug = combined.lower()

    # Replace spaces and special chars with hyphens
    slug = re.sub(r'[^a-z0-9]+', '-', slug)

    # Remove leading/trailing hyphens
    slug = slug.strip('-')

    # Limit length (max 100 chars)
    if len(slug) > 100:
        slug = slug[:100].rsplit('-', 1)[0]  # Cut at last hyphen

    return slug


def generate_h1(city: str, keyword: str, business_name: str) -> str:
    """
    Generate H1 headline for landing page

    Args:
        city: City name
        keyword: Keyword phrase
        business_name: Professional's business name

    Returns:
        H1 headline

    Example:
        >>> generate_h1("Tampa", "emergency plumber", "Joe's Plumbing")
        'Emergency Plumber in Tampa | Joe\\'s Plumbing'
    """
    # Capitalize keyword
    keyword_title = keyword.title()

    return f"{keyword_title} in {city} | {business_name}"


def generate_meta_title(city: str, keyword: str, business_name: str) -> str:
    """
    Generate meta title tag (50-60 chars optimal)

    Args:
        city: City name
        keyword: Keyword phrase
        business_name: Professional's business name

    Returns:
        Meta title

    Example:
        >>> generate_meta_title("Tampa", "plumber", "Joe's Plumbing")
        'Plumber in Tampa - Joe\\'s Plumbing'
    """
    keyword_title = keyword.title()

    meta_title = f"{keyword_title} in {city} - {business_name}"

    # Truncate if too long (max 60 chars)
    if len(meta_title) > 60:
        # Try without business name
        meta_title = f"{keyword_title} in {city}"

    return meta_title


def generate_meta_description(
    city: str,
    keyword: str,
    professional: ProfessionalProfile
) -> str:
    """
    Generate meta description tag (150-160 chars optimal)

    Args:
        city: City name
        keyword: Keyword phrase
        professional: Professional profile

    Returns:
        Meta description

    Example:
        >>> generate_meta_description("Tampa", "plumber", professional)
        'Need a plumber in Tampa? Joe\\'s Plumbing is licensed, insured...'
    """
    description = (
        f"Need a {keyword} in {city}? "
        f"{professional.business_name} is licensed, insured, and available 24/7. "
        f"Call {professional.phone} for fast service."
    )

    # Truncate if too long (max 160 chars)
    if len(description) > 160:
        description = description[:157] + "..."

    return description


def customize_content_for_city(
    base_content: str,
    city: str,
    keyword: str,
    professional: ProfessionalProfile
) -> str:
    """
    Add city-specific context to base tutorial content

    Args:
        base_content: Base HTML content from tutorial
        city: Target city
        keyword: Target keyword
        professional: Professional profile

    Returns:
        Customized HTML content

    Example:
        >>> content = customize_content_for_city(
        ...     base_content="<div>Tutorial content...</div>",
        ...     city="Tampa",
        ...     keyword="plumber",
        ...     professional=professional
        ... )
        >>> print(content)
        <div class="city-intro">
            <p>Serving Tampa with professional plumber services...</p>
        </div>
        <div>Tutorial content...</div>
    """
    # City intro paragraph
    city_fact = CITY_FACTS.get(city, f'Proud to serve the {city} community.')

    city_intro = f"""
    <div class="city-intro" style="background: #f8f9fa; padding: 20px; border-left: 4px solid var(--primary-color); margin: 20px 0;">
        <p><strong>Serving {city}</strong></p>
        <p>Professional {keyword} services in {city} and surrounding areas. {city_fact}</p>
        <p>📞 Call now: <a href="tel:{professional.phone.replace(' ', '').replace('-', '')}">{professional.phone}</a></p>
    </div>
"""

    # Insert city intro after opening tag
    # Look for first </header> or <main> tag
    if '</header>' in base_content:
        customized = base_content.replace('</header>', f'</header>{city_intro}', 1)
    elif '<main>' in base_content:
        customized = base_content.replace('<main>', f'<main>{city_intro}', 1)
    else:
        # Prepend if no header/main found
        customized = city_intro + base_content

    # Replace generic references with city-specific
    customized = customized.replace('[CITY]', city)
    customized = customized.replace('[KEYWORD]', keyword)

    # Add city to title if present
    customized = re.sub(
        r'<h1>(.*?)</h1>',
        f'<h1>\\1 in {city}</h1>',
        customized,
        count=1
    )

    return customized


# ============================================================================
# Batch Operations
# ============================================================================

def generate_pseo_for_all_tutorials(professional_id: int) -> Tuple[int, int]:
    """
    Generate pSEO landing pages for all tutorials from a professional

    Args:
        professional_id: Professional profile ID

    Returns:
        Tuple of (tutorials_processed, pages_created)

    Example:
        >>> tutorials, pages = generate_pseo_for_all_tutorials(1)
        >>> print(f"Processed {tutorials} tutorials, created {pages} pages")
        Processed 10 tutorials, created 520 pages
    """
    tutorials = Tutorial.query.filter_by(
        professional_id=professional_id,
        status='published'
    ).all()

    tutorials_processed = 0
    total_pages_created = 0

    for tutorial in tutorials:
        print(f"\n📝 Processing tutorial #{tutorial.id}: {tutorial.title}")

        pages_created = generate_pseo_landing_pages(tutorial.id)
        total_pages_created += pages_created
        tutorials_processed += 1

    print(f"\n✅ COMPLETE: Processed {tutorials_processed} tutorials, created {total_pages_created} landing pages")

    return tutorials_processed, total_pages_created


def regenerate_pseo_for_tutorial(tutorial_id: int, force: bool = False) -> int:
    """
    Regenerate pSEO landing pages for a tutorial

    Args:
        tutorial_id: Tutorial ID
        force: If True, delete existing pages first

    Returns:
        Number of pages created

    Example:
        >>> pages = regenerate_pseo_for_tutorial(123, force=True)
        >>> print(f"Regenerated {pages} pages")
        Regenerated 52 pages
    """
    tutorial = Tutorial.query.get(tutorial_id)

    if not tutorial:
        raise ValueError(f"Tutorial {tutorial_id} not found")

    if force:
        # Delete existing pages
        existing_pages = PSEOLandingPage.query.filter_by(
            tutorial_id=tutorial_id
        ).delete()

        db.session.commit()

        print(f"🗑️  Deleted {existing_pages} existing pages")

    # Generate new pages
    pages_created = generate_pseo_landing_pages(tutorial_id)

    return pages_created


# ============================================================================
# Analytics & Reporting
# ============================================================================

def get_pseo_stats(professional_id: int) -> Dict:
    """
    Get pSEO statistics for a professional

    Args:
        professional_id: Professional profile ID

    Returns:
        Dictionary of stats

    Example:
        >>> stats = get_pseo_stats(1)
        >>> print(stats)
        {
            'total_pages': 520,
            'total_impressions': 12450,
            'total_clicks': 387,
            'total_leads': 47,
            'ctr': 3.1,
            'conversion_rate': 12.1
        }
    """
    pages = PSEOLandingPage.query.filter_by(
        professional_id=professional_id
    ).all()

    total_pages = len(pages)
    total_impressions = sum(p.impressions for p in pages)
    total_clicks = sum(p.clicks for p in pages)
    total_leads = sum(p.leads for p in pages)

    ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
    conversion_rate = (total_leads / total_clicks * 100) if total_clicks > 0 else 0

    return {
        'total_pages': total_pages,
        'total_impressions': total_impressions,
        'total_clicks': total_clicks,
        'total_leads': total_leads,
        'ctr': round(ctr, 2),
        'conversion_rate': round(conversion_rate, 2)
    }


def get_top_performing_pages(professional_id: int, limit: int = 10) -> List[PSEOLandingPage]:
    """
    Get top performing pSEO landing pages by leads

    Args:
        professional_id: Professional profile ID
        limit: Number of pages to return

    Returns:
        List of landing pages sorted by leads

    Example:
        >>> top_pages = get_top_performing_pages(1, limit=5)
        >>> for page in top_pages:
        ...     print(f"{page.slug}: {page.leads} leads")
        tampa-emergency-plumber: 23 leads
        st-petersburg-plumber: 18 leads
        clearwater-24-7-plumber: 14 leads
    """
    return PSEOLandingPage.query.filter_by(
        professional_id=professional_id
    ).order_by(
        PSEOLandingPage.leads.desc()
    ).limit(limit).all()


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    """
    Command-line interface for pSEO generator

    Usage:
        python pseo_generator.py --tutorial-id 123
        python pseo_generator.py --professional-id 1 --all
        python pseo_generator.py --regenerate 123 --force
        python pseo_generator.py --stats 1
    """
    import argparse

    parser = argparse.ArgumentParser(description='pSEO Landing Page Generator')

    parser.add_argument('--tutorial-id', type=int, help='Generate pages for specific tutorial')
    parser.add_argument('--professional-id', type=int, help='Professional ID')
    parser.add_argument('--all', action='store_true', help='Generate for all tutorials')
    parser.add_argument('--regenerate', type=int, help='Regenerate pages for tutorial')
    parser.add_argument('--force', action='store_true', help='Force regeneration (delete existing)')
    parser.add_argument('--stats', type=int, help='Show stats for professional')

    args = parser.parse_args()

    if args.tutorial_id:
        pages = generate_pseo_landing_pages(args.tutorial_id)
        print(f"\n✅ Created {pages} landing pages for tutorial #{args.tutorial_id}")

    elif args.all and args.professional_id:
        tutorials, pages = generate_pseo_for_all_tutorials(args.professional_id)
        print(f"\n✅ Processed {tutorials} tutorials, created {pages} landing pages")

    elif args.regenerate:
        pages = regenerate_pseo_for_tutorial(args.regenerate, force=args.force)
        print(f"\n✅ Regenerated {pages} landing pages for tutorial #{args.regenerate}")

    elif args.stats and args.professional_id:
        stats = get_pseo_stats(args.professional_id)
        print(f"\n📊 pSEO Stats for Professional #{args.professional_id}:")
        print(f"  Total Pages: {stats['total_pages']}")
        print(f"  Total Impressions: {stats['total_impressions']:,}")
        print(f"  Total Clicks: {stats['total_clicks']:,}")
        print(f"  Total Leads: {stats['total_leads']}")
        print(f"  CTR: {stats['ctr']}%")
        print(f"  Conversion Rate: {stats['conversion_rate']}%")

        print(f"\n🏆 Top Performing Pages:")
        top_pages = get_top_performing_pages(args.professional_id, limit=5)
        for page in top_pages:
            print(f"  {page.slug}: {page.leads} leads ({page.clicks} clicks, {page.impressions} views)")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
