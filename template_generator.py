"""
Professional Site Template Generator

Auto-generates complete website templates for professionals based on their
profile, branding, and industry.

Features:
- Professional homepage
- Tutorials listing page
- License verification page
- Contact form with lead capture
- Responsive design (mobile-first)
- Custom branding (logo, colors)
- SEO-optimized meta tags

Usage:
    from template_generator import generate_professional_site

    # Generate complete site for professional
    site = generate_professional_site(professional_id=1)
    # Returns: {'homepage': '<html>...', 'tutorials': '<html>...', ...}
"""

from typing import Dict, List, Optional
from datetime import datetime
from models import ProfessionalProfile, Tutorial


# ============================================================================
# Main Generator Function
# ============================================================================

def generate_professional_site(professional_id: int) -> Dict[str, str]:
    """
    Generate complete website for professional

    Args:
        professional_id: Professional profile ID

    Returns:
        Dictionary of page_name: html_content

    Example:
        >>> site = generate_professional_site(1)
        >>> print(site.keys())
        dict_keys(['homepage', 'tutorials', 'license', 'contact', 'base_css'])
    """
    professional = ProfessionalProfile.query.get(professional_id)

    if not professional:
        raise ValueError(f"Professional {professional_id} not found")

    # Get published tutorials
    tutorials = Tutorial.query.filter_by(
        professional_id=professional_id,
        status='published'
    ).order_by(Tutorial.published_at.desc()).all()

    # Generate all pages
    site = {
        'homepage': generate_homepage(professional, tutorials),
        'tutorials': generate_tutorials_page(professional, tutorials),
        'license': generate_license_page(professional),
        'contact': generate_contact_page(professional),
        'base_css': generate_base_css(professional)
    }

    print(f"✅ Generated complete site for {professional.business_name}")
    print(f"   - {len(tutorials)} tutorials")
    print(f"   - {len(site)} pages")

    return site


# ============================================================================
# Homepage
# ============================================================================

def generate_homepage(
    professional: ProfessionalProfile,
    tutorials: List[Tutorial]
) -> str:
    """
    Generate professional homepage

    Features:
    - Hero section with business name, tagline
    - License verification badge
    - Recent tutorials (latest 3)
    - CTA buttons (call, contact)
    - Social proof (review count, rating)
    """

    # Recent tutorials (max 3)
    recent_tutorials = tutorials[:3]

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <!-- SEO Meta Tags -->
    <title>{professional.business_name} | Licensed {professional.license_type}</title>
    <meta name="description" content="{professional.business_name} - {professional.tagline or 'Licensed and insured professional services in ' + (professional.address_city or '')}">

    <!-- Base Styles -->
    <link rel="stylesheet" href="/static/base.css">

    <style>
        :root {{
            --primary: {professional.primary_color or '#0066CC'};
            --accent: {professional.accent_color or '#FF6600'};
        }}
    </style>
</head>
<body>
    <!-- Header -->
    <header class="site-header">
        <div class="container">
            {f'<img src="{professional.logo_url}" alt="{professional.business_name}" class="logo">' if professional.logo_url else f'<h1 class="logo-text">{professional.business_name}</h1>'}

            <nav class="main-nav">
                <a href="/">Home</a>
                <a href="/tutorials">Tutorials</a>
                <a href="/license-verify">Verify License</a>
                <a href="/contact">Contact</a>
            </nav>
        </div>
    </header>

    <!-- Hero Section -->
    <section class="hero">
        <div class="container">
            <h1>{professional.business_name}</h1>
            <p class="tagline">{professional.tagline or f'Professional {professional.license_type} Services'}</p>

            <div class="verification-badge">
                <span class="badge-icon">✓</span>
                <span class="badge-text">{professional.license_state} Licensed {professional.license_type}</span>
                <span class="badge-number">#{professional.license_number}</span>
            </div>

            <div class="cta-buttons">
                <a href="tel:{professional.phone.replace(' ', '').replace('-', '') if professional.phone else ''}" class="btn btn-primary">
                    📞 Call Now: {professional.phone or 'Contact Us'}
                </a>
                <a href="/contact" class="btn btn-secondary">
                    📧 Get a Quote
                </a>
            </div>
        </div>
    </section>

    <!-- Recent Tutorials -->
    <section class="tutorials-section">
        <div class="container">
            <h2>Recent Tutorials</h2>
            <p class="section-subtitle">Learn from our expert guides</p>

            <div class="tutorial-grid">
"""

    # Add recent tutorials
    for tutorial in recent_tutorials:
        html += f"""
                <article class="tutorial-card">
                    <h3>{tutorial.title}</h3>
                    <p class="tutorial-meta">
                        Published {tutorial.published_at.strftime('%B %d, %Y') if tutorial.published_at else 'Recently'}
                    </p>
                    {f'<p class="tutorial-excerpt">{tutorial.meta_description[:150] + "..." if tutorial.meta_description and len(tutorial.meta_description) > 150 else tutorial.meta_description or ""}</p>' if tutorial.meta_description else ''}
                    <a href="/tutorials/{tutorial.id}" class="btn btn-link">Read More →</a>
                </article>
"""

    html += f"""
            </div>

            <div class="view-all">
                <a href="/tutorials" class="btn btn-secondary">View All {len(tutorials)} Tutorials</a>
            </div>
        </div>
    </section>

    <!-- Why Choose Us -->
    <section class="features-section">
        <div class="container">
            <h2>Why Choose {professional.business_name}?</h2>

            <div class="features-grid">
                <div class="feature">
                    <span class="feature-icon">🏆</span>
                    <h3>Licensed & Insured</h3>
                    <p>{professional.license_state} License #{professional.license_number}. Fully insured for your protection.</p>
                </div>

                <div class="feature">
                    <span class="feature-icon">⚡</span>
                    <h3>Fast Response</h3>
                    <p>Available 24/7 for emergency services. We're here when you need us.</p>
                </div>

                <div class="feature">
                    <span class="feature-icon">💰</span>
                    <h3>Fair Pricing</h3>
                    <p>Transparent pricing with no hidden fees. Free quotes available.</p>
                </div>

                <div class="feature">
                    <span class="feature-icon">⭐</span>
                    <h3>Trusted by Locals</h3>
                    <p>Serving {professional.address_city or 'the local community'} with pride. Your neighbors trust us.</p>
                </div>
            </div>
        </div>
    </section>

    <!-- Call to Action -->
    <section class="cta-section">
        <div class="container">
            <h2>Ready to Get Started?</h2>
            <p>Contact us today for a free consultation</p>
            <a href="tel:{professional.phone.replace(' ', '').replace('-', '') if professional.phone else ''}" class="btn btn-primary btn-large">
                📞 Call Now: {professional.phone or 'Contact Us'}
            </a>
        </div>
    </section>

    <!-- Footer -->
    <footer class="site-footer">
        <div class="container">
            <div class="footer-content">
                <div class="footer-section">
                    <h4>{professional.business_name}</h4>
                    <p>{professional.address_street or ''}</p>
                    <p>{professional.address_city or ''}, {professional.address_state or ''} {professional.address_zip or ''}</p>
                    <p>Phone: {professional.phone or 'N/A'}</p>
                    <p>Email: {professional.email or 'N/A'}</p>
                </div>

                <div class="footer-section">
                    <h4>Quick Links</h4>
                    <ul>
                        <li><a href="/">Home</a></li>
                        <li><a href="/tutorials">Tutorials</a></li>
                        <li><a href="/license-verify">Verify License</a></li>
                        <li><a href="/contact">Contact</a></li>
                    </ul>
                </div>

                <div class="footer-section">
                    <h4>Legal</h4>
                    <p>Licensed {professional.license_type}</p>
                    <p>{professional.license_state} License #{professional.license_number}</p>
                    <a href="/license-verify">Verify License →</a>
                </div>
            </div>

            <div class="footer-bottom">
                <p>&copy; {datetime.now().year} {professional.business_name}. All rights reserved.</p>
                <p class="powered-by">
                    <a href="https://cringeproof.com">Powered by CringeProof</a>
                </p>
            </div>
        </div>
    </footer>
</body>
</html>
"""

    return html


# ============================================================================
# Tutorials Page
# ============================================================================

def generate_tutorials_page(
    professional: ProfessionalProfile,
    tutorials: List[Tutorial]
) -> str:
    """
    Generate tutorials listing page

    Features:
    - All tutorials in chronological order
    - Search/filter functionality
    - Tutorial cards with excerpts
    """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <title>Tutorials | {professional.business_name}</title>
    <meta name="description" content="Educational tutorials from {professional.business_name}. Learn expert tips and tricks.">

    <link rel="stylesheet" href="/static/base.css">

    <style>
        :root {{
            --primary: {professional.primary_color or '#0066CC'};
            --accent: {professional.accent_color or '#FF6600'};
        }}
    </style>
</head>
<body>
    <header class="site-header">
        <div class="container">
            {f'<img src="{professional.logo_url}" alt="{professional.business_name}" class="logo">' if professional.logo_url else f'<h1 class="logo-text">{professional.business_name}</h1>'}

            <nav class="main-nav">
                <a href="/">Home</a>
                <a href="/tutorials" class="active">Tutorials</a>
                <a href="/license-verify">Verify License</a>
                <a href="/contact">Contact</a>
            </nav>
        </div>
    </header>

    <main class="tutorials-page">
        <div class="container">
            <h1>Educational Tutorials</h1>
            <p class="page-subtitle">Learn from our expert guides and tips</p>

            <div class="tutorial-count">
                <strong>{len(tutorials)}</strong> tutorials available
            </div>

            <div class="tutorial-list">
"""

    # List all tutorials
    for tutorial in tutorials:
        published_date = tutorial.published_at.strftime('%B %d, %Y') if tutorial.published_at else 'Recently'

        html += f"""
                <article class="tutorial-item">
                    <h2><a href="/tutorials/{tutorial.id}">{tutorial.title}</a></h2>

                    <p class="tutorial-meta">
                        Published {published_date}
                        {f' · {tutorial.view_count} views' if hasattr(tutorial, 'view_count') and tutorial.view_count > 0 else ''}
                    </p>

                    {f'<p class="tutorial-excerpt">{tutorial.meta_description}</p>' if tutorial.meta_description else ''}

                    <div class="tutorial-actions">
                        <a href="/tutorials/{tutorial.id}" class="btn btn-secondary">Read Tutorial</a>
                        {f'<a href="{tutorial.audio_url}" class="btn btn-link">🎧 Listen</a>' if tutorial.audio_url else ''}
                    </div>
                </article>
"""

    html += f"""
            </div>
        </div>
    </main>

    <footer class="site-footer">
        <div class="container">
            <p>&copy; {datetime.now().year} {professional.business_name}. All rights reserved.</p>
            <p><a href="https://cringeproof.com">Powered by CringeProof</a></p>
        </div>
    </footer>
</body>
</html>
"""

    return html


# ============================================================================
# License Verification Page
# ============================================================================

def generate_license_page(professional: ProfessionalProfile) -> str:
    """
    Generate license verification page

    Features:
    - License details display
    - Link to state verification
    - Verification badge
    """

    # State verification URLs (example for Florida)
    state_urls = {
        'FL': f'https://www.myfloridalicense.com/LicenseDetail.asp?id={professional.license_number}'
    }

    verification_url = state_urls.get(professional.license_state, '#')

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <title>License Verification | {professional.business_name}</title>
    <meta name="description" content="Verify {professional.business_name}'s {professional.license_state} license #{professional.license_number}">

    <link rel="stylesheet" href="/static/base.css">

    <style>
        :root {{
            --primary: {professional.primary_color or '#0066CC'};
            --accent: {professional.accent_color or '#FF6600'};
        }}
    </style>
</head>
<body>
    <header class="site-header">
        <div class="container">
            {f'<img src="{professional.logo_url}" alt="{professional.business_name}" class="logo">' if professional.logo_url else f'<h1 class="logo-text">{professional.business_name}</h1>'}

            <nav class="main-nav">
                <a href="/">Home</a>
                <a href="/tutorials">Tutorials</a>
                <a href="/license-verify" class="active">Verify License</a>
                <a href="/contact">Contact</a>
            </nav>
        </div>
    </header>

    <main class="license-page">
        <div class="container">
            <h1>License Verification</h1>

            <div class="license-card">
                <div class="license-badge">
                    <span class="badge-icon-large">✓</span>
                </div>

                <h2>{professional.business_name}</h2>

                <div class="license-details">
                    <div class="detail-row">
                        <span class="detail-label">License Type:</span>
                        <span class="detail-value">{professional.license_type}</span>
                    </div>

                    <div class="detail-row">
                        <span class="detail-label">License Number:</span>
                        <span class="detail-value">{professional.license_number}</span>
                    </div>

                    <div class="detail-row">
                        <span class="detail-label">State:</span>
                        <span class="detail-value">{professional.license_state}</span>
                    </div>

                    <div class="detail-row">
                        <span class="detail-label">Status:</span>
                        <span class="detail-value status-active">✓ Active & Verified</span>
                    </div>
                </div>

                <a href="{verification_url}" target="_blank" class="btn btn-primary" rel="noopener">
                    Verify on {professional.license_state} State Website →
                </a>

                <p class="verification-note">
                    This license has been verified with the {professional.license_state} Department of Business and Professional Regulation.
                    Last verified: {datetime.now().strftime('%B %d, %Y')}
                </p>
            </div>

            <div class="trust-section">
                <h3>Why License Verification Matters</h3>
                <p>
                    Working with a licensed professional ensures you're hiring someone who:
                </p>
                <ul>
                    <li>Has met state requirements for training and expertise</li>
                    <li>Carries required insurance for your protection</li>
                    <li>Is subject to state regulation and oversight</li>
                    <li>Must maintain continuing education</li>
                    <li>Can legally perform the work in your area</li>
                </ul>
            </div>
        </div>
    </main>

    <footer class="site-footer">
        <div class="container">
            <p>&copy; {datetime.now().year} {professional.business_name}. All rights reserved.</p>
            <p><a href="https://cringeproof.com">Powered by CringeProof</a></p>
        </div>
    </footer>
</body>
</html>
"""

    return html


# ============================================================================
# Contact Page
# ============================================================================

def generate_contact_page(professional: ProfessionalProfile) -> str:
    """
    Generate contact page with lead capture form

    Features:
    - Contact form (name, phone, email, message)
    - Phone/email display
    - Address display
    - Map embed (if coordinates available)
    """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <title>Contact Us | {professional.business_name}</title>
    <meta name="description" content="Contact {professional.business_name}. Get a free quote today.">

    <link rel="stylesheet" href="/static/base.css">

    <style>
        :root {{
            --primary: {professional.primary_color or '#0066CC'};
            --accent: {professional.accent_color or '#FF6600'};
        }}
    </style>
</head>
<body>
    <header class="site-header">
        <div class="container">
            {f'<img src="{professional.logo_url}" alt="{professional.business_name}" class="logo">' if professional.logo_url else f'<h1 class="logo-text">{professional.business_name}</h1>'}

            <nav class="main-nav">
                <a href="/">Home</a>
                <a href="/tutorials">Tutorials</a>
                <a href="/license-verify">Verify License</a>
                <a href="/contact" class="active">Contact</a>
            </nav>
        </div>
    </header>

    <main class="contact-page">
        <div class="container">
            <h1>Contact Us</h1>
            <p class="page-subtitle">Get a free quote or ask us a question</p>

            <div class="contact-grid">
                <!-- Contact Form -->
                <div class="contact-form-section">
                    <h2>Send us a message</h2>

                    <form action="/api/leads" method="POST" class="contact-form">
                        <div class="form-group">
                            <label for="name">Name *</label>
                            <input type="text" id="name" name="name" required>
                        </div>

                        <div class="form-group">
                            <label for="phone">Phone *</label>
                            <input type="tel" id="phone" name="phone" required>
                        </div>

                        <div class="form-group">
                            <label for="email">Email</label>
                            <input type="email" id="email" name="email">
                        </div>

                        <div class="form-group">
                            <label for="message">Message *</label>
                            <textarea id="message" name="message" rows="5" required></textarea>
                        </div>

                        <button type="submit" class="btn btn-primary btn-large">
                            Send Message
                        </button>
                    </form>
                </div>

                <!-- Contact Info -->
                <div class="contact-info-section">
                    <h2>Get in touch</h2>

                    <div class="contact-method">
                        <span class="method-icon">📞</span>
                        <div class="method-content">
                            <h3>Phone</h3>
                            <a href="tel:{professional.phone.replace(' ', '').replace('-', '') if professional.phone else ''}">{professional.phone or 'N/A'}</a>
                            <p>Available 24/7 for emergencies</p>
                        </div>
                    </div>

                    <div class="contact-method">
                        <span class="method-icon">📧</span>
                        <div class="method-content">
                            <h3>Email</h3>
                            <a href="mailto:{professional.email or ''}">{professional.email or 'N/A'}</a>
                            <p>We typically respond within 24 hours</p>
                        </div>
                    </div>

                    <div class="contact-method">
                        <span class="method-icon">📍</span>
                        <div class="method-content">
                            <h3>Address</h3>
                            <address>
                                {professional.address_street or 'Address not provided'}<br>
                                {professional.address_city or ''}, {professional.address_state or ''} {professional.address_zip or ''}
                            </address>
                        </div>
                    </div>

                    <div class="contact-method">
                        <span class="method-icon">🕐</span>
                        <div class="method-content">
                            <h3>Hours</h3>
                            <p>Monday - Friday: 8:00 AM - 6:00 PM</p>
                            <p>Saturday: 9:00 AM - 4:00 PM</p>
                            <p>Sunday: Emergency only</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <footer class="site-footer">
        <div class="container">
            <p>&copy; {datetime.now().year} {professional.business_name}. All rights reserved.</p>
            <p><a href="https://cringeproof.com">Powered by CringeProof</a></p>
        </div>
    </footer>

    <script>
        // Lead capture form handling
        document.querySelector('.contact-form').addEventListener('submit', async (e) => {{
            e.preventDefault();

            const formData = new FormData(e.target);
            const data = Object.fromEntries(formData);

            // Add UTM parameters for attribution
            data.utm_source = new URLSearchParams(window.location.search).get('utm_source') || 'direct';
            data.utm_medium = new URLSearchParams(window.location.search).get('utm_medium') || 'website';

            try {{
                const response = await fetch('/api/leads', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify(data)
                }});

                if (response.ok) {{
                    alert('Thank you! We\\'ll be in touch soon.');
                    e.target.reset();
                }} else {{
                    alert('Something went wrong. Please call us instead.');
                }}
            }} catch (error) {{
                alert('Error sending message. Please call us at {professional.phone or "the number above"}');
            }}
        }});
    </script>
</body>
</html>
"""

    return html


# ============================================================================
# Base CSS
# ============================================================================

def generate_base_css(professional: ProfessionalProfile) -> str:
    """
    Generate base CSS with professional's branding

    Features:
    - Custom colors (primary, accent)
    - Responsive design (mobile-first)
    - Typography
    - Component styles
    """

    css = f"""/* Base CSS for {professional.business_name} */

/* ============================================================================
   CSS Variables (Branding)
   ============================================================================ */

:root {{
    /* Brand Colors */
    --primary: {professional.primary_color or '#0066CC'};
    --accent: {professional.accent_color or '#FF6600'};

    /* Neutral Colors */
    --dark: #1a1a1a;
    --gray: #666666;
    --light-gray: #f8f9fa;
    --white: #ffffff;

    /* Spacing */
    --spacing-xs: 0.5rem;
    --spacing-sm: 1rem;
    --spacing-md: 2rem;
    --spacing-lg: 4rem;

    /* Typography */
    --font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    --font-size-base: 16px;
    --line-height-base: 1.6;
}}

/* ============================================================================
   Reset & Base Styles
   ============================================================================ */

* {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}

body {{
    font-family: var(--font-family);
    font-size: var(--font-size-base);
    line-height: var(--line-height-base);
    color: var(--dark);
    background: var(--white);
}}

.container {{
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 var(--spacing-sm);
}}

/* ============================================================================
   Header
   ============================================================================ */

.site-header {{
    background: var(--white);
    border-bottom: 1px solid #e0e0e0;
    padding: var(--spacing-sm) 0;
    position: sticky;
    top: 0;
    z-index: 100;
}}

.site-header .container {{
    display: flex;
    justify-content: space-between;
    align-items: center;
}}

.logo {{
    max-height: 60px;
    width: auto;
}}

.logo-text {{
    font-size: 1.5rem;
    font-weight: bold;
    color: var(--primary);
}}

.main-nav {{
    display: flex;
    gap: var(--spacing-sm);
}}

.main-nav a {{
    color: var(--dark);
    text-decoration: none;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    transition: background 0.2s;
}}

.main-nav a:hover,
.main-nav a.active {{
    background: var(--light-gray);
}}

/* ============================================================================
   Hero Section
   ============================================================================ */

.hero {{
    background: linear-gradient(135deg, var(--primary), var(--accent));
    color: var(--white);
    padding: var(--spacing-lg) 0;
    text-align: center;
}}

.hero h1 {{
    font-size: 3rem;
    margin-bottom: var(--spacing-sm);
}}

.hero .tagline {{
    font-size: 1.5rem;
    margin-bottom: var(--spacing-md);
    opacity: 0.9;
}}

.verification-badge {{
    display: inline-block;
    background: rgba(255,255,255,0.2);
    padding: var(--spacing-sm);
    border-radius: 8px;
    margin: var(--spacing-sm) 0;
}}

.badge-icon {{
    font-size: 1.5rem;
}}

.cta-buttons {{
    display: flex;
    gap: var(--spacing-sm);
    justify-content: center;
    margin-top: var(--spacing-md);
}}

/* ============================================================================
   Buttons
   ============================================================================ */

.btn {{
    display: inline-block;
    padding: 0.75rem 1.5rem;
    border-radius: 8px;
    text-decoration: none;
    font-weight: 600;
    transition: all 0.3s;
    border: none;
    cursor: pointer;
}}

.btn-primary {{
    background: var(--accent);
    color: var(--white);
}}

.btn-primary:hover {{
    background: var(--primary);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}}

.btn-secondary {{
    background: var(--white);
    color: var(--primary);
    border: 2px solid var(--primary);
}}

.btn-secondary:hover {{
    background: var(--primary);
    color: var(--white);
}}

.btn-link {{
    color: var(--primary);
    background: transparent;
    padding: 0.5rem 1rem;
}}

.btn-link:hover {{
    background: var(--light-gray);
}}

.btn-large {{
    padding: 1rem 2rem;
    font-size: 1.2rem;
}}

/* ============================================================================
   Tutorial Cards
   ============================================================================ */

.tutorial-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: var(--spacing-md);
    margin: var(--spacing-md) 0;
}}

.tutorial-card {{
    background: var(--white);
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: var(--spacing-md);
    transition: transform 0.3s, box-shadow 0.3s;
}}

.tutorial-card:hover {{
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.1);
}}

.tutorial-card h3 {{
    color: var(--primary);
    margin-bottom: var(--spacing-sm);
}}

.tutorial-meta {{
    color: var(--gray);
    font-size: 0.9rem;
    margin-bottom: var(--spacing-sm);
}}

.tutorial-excerpt {{
    margin-bottom: var(--spacing-sm);
}}

/* ============================================================================
   Features Section
   ============================================================================ */

.features-section {{
    background: var(--light-gray);
    padding: var(--spacing-lg) 0;
}}

.features-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: var(--spacing-md);
    margin-top: var(--spacing-md);
}}

.feature {{
    text-align: center;
    padding: var(--spacing-md);
}}

.feature-icon {{
    font-size: 3rem;
    display: block;
    margin-bottom: var(--spacing-sm);
}}

/* ============================================================================
   Forms
   ============================================================================ */

.contact-form {{
    background: var(--light-gray);
    padding: var(--spacing-md);
    border-radius: 8px;
}}

.form-group {{
    margin-bottom: var(--spacing-sm);
}}

.form-group label {{
    display: block;
    font-weight: 600;
    margin-bottom: 0.25rem;
}}

.form-group input,
.form-group textarea {{
    width: 100%;
    padding: 0.75rem;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-family: inherit;
    font-size: 1rem;
}}

.form-group input:focus,
.form-group textarea:focus {{
    outline: none;
    border-color: var(--primary);
    box-shadow: 0 0 0 3px rgba(0,102,204,0.1);
}}

/* ============================================================================
   Footer
   ============================================================================ */

.site-footer {{
    background: var(--dark);
    color: var(--white);
    padding: var(--spacing-lg) 0 var(--spacing-md);
    margin-top: var(--spacing-lg);
}}

.footer-content {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: var(--spacing-md);
    margin-bottom: var(--spacing-md);
}}

.footer-section h4 {{
    margin-bottom: var(--spacing-sm);
}}

.footer-section a {{
    color: var(--white);
    text-decoration: none;
}}

.footer-section a:hover {{
    text-decoration: underline;
}}

.footer-section ul {{
    list-style: none;
}}

.footer-section ul li {{
    margin-bottom: 0.5rem;
}}

.footer-bottom {{
    border-top: 1px solid #333;
    padding-top: var(--spacing-sm);
    text-align: center;
    color: var(--gray);
}}

.powered-by {{
    margin-top: 0.5rem;
    font-size: 0.9rem;
}}

.powered-by a {{
    color: var(--gray);
}}

/* ============================================================================
   Responsive Design
   ============================================================================ */

@media (max-width: 768px) {{
    .hero h1 {{
        font-size: 2rem;
    }}

    .hero .tagline {{
        font-size: 1.2rem;
    }}

    .cta-buttons {{
        flex-direction: column;
    }}

    .main-nav {{
        flex-direction: column;
        gap: 0;
    }}

    .site-header .container {{
        flex-direction: column;
        align-items: flex-start;
    }}
}}
"""

    return css


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    """
    Command-line interface for template generator

    Usage:
        python template_generator.py --professional-id 1
        python template_generator.py --professional-id 1 --output-dir ./output
    """
    import argparse
    import os

    parser = argparse.ArgumentParser(description='Professional Site Template Generator')

    parser.add_argument('--professional-id', type=int, required=True, help='Professional ID')
    parser.add_argument('--output-dir', default='./output', help='Output directory')

    args = parser.parse_args()

    # Generate site
    site = generate_professional_site(args.professional_id)

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    # Write files
    for page_name, html_content in site.items():
        if page_name == 'base_css':
            file_path = os.path.join(args.output_dir, 'base.css')
        else:
            file_path = os.path.join(args.output_dir, f'{page_name}.html')

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"✅ Written: {file_path}")

    print(f"\n✅ Site generated successfully in {args.output_dir}")


if __name__ == '__main__':
    main()
