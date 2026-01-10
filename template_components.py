"""
Template Components - Reusable navigation and UI elements

Provides consistent header, footer, and navigation across all pages.
Import these components into your templates for unified UX.
"""

# ===========================================
# NAVIGATION HEADER
# ===========================================

NAVIGATION_HEADER = """
<style>
    .site-header {
        background: rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(15px);
        padding: 15px 0;
        margin-bottom: 30px;
        border-bottom: 2px solid rgba(255, 255, 255, 0.2);
    }

    .site-header .container {
        max-width: 1400px;
        margin: 0 auto;
        padding: 0 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 15px;
    }

    .site-logo {
        font-size: 1.8em;
        font-weight: 700;
        color: white;
        text-decoration: none;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .site-nav {
        display: flex;
        gap: 25px;
        flex-wrap: wrap;
        align-items: center;
    }

    .site-nav a {
        color: white;
        text-decoration: none;
        font-weight: 500;
        opacity: 0.85;
        transition: opacity 0.3s;
        font-size: 1.05em;
    }

    .site-nav a:hover {
        opacity: 1;
        text-decoration: underline;
    }

    .nav-button {
        background: rgba(255, 255, 255, 0.2);
        padding: 8px 16px;
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.3);
    }

    .nav-button:hover {
        background: rgba(255, 255, 255, 0.3);
        text-decoration: none;
    }

    @media (max-width: 768px) {
        .site-header .container {
            flex-direction: column;
            text-align: center;
        }

        .site-nav {
            justify-content: center;
        }
    }
</style>

<header class="site-header">
    <div class="container">
        <a href="/" class="site-logo">
            🌙 Soulfra
        </a>

        <nav class="site-nav">
            <a href="/cringeproof/narrative/soulfra">🎮 Play Game</a>
            <a href="/chat">💬 Chat</a>
            <a href="/learn">🎓 Learn</a>
            <a href="/draw">✏️ Draw</a>
            <a href="/canvas">🎨 Canvas</a>
            <a href="/dashboard">📚 Content</a>
            <a href="/galleries">🖼️ Galleries</a>
            <a href="/status" class="nav-button">🔧 Status</a>
        </nav>
    </div>
</header>
"""


# ===========================================
# SITE FOOTER
# ===========================================

SITE_FOOTER = """
<style>
    .site-footer {
        margin-top: 60px;
        padding: 40px 0 20px;
        border-top: 2px solid rgba(255, 255, 255, 0.2);
        background: rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(10px);
    }

    .footer-container {
        max-width: 1400px;
        margin: 0 auto;
        padding: 0 20px;
    }

    .footer-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 40px;
        margin-bottom: 30px;
    }

    .footer-section h3 {
        font-size: 1.3em;
        margin-bottom: 15px;
        opacity: 0.95;
    }

    .footer-links {
        list-style: none;
    }

    .footer-links li {
        margin-bottom: 10px;
    }

    .footer-links a {
        color: white;
        text-decoration: none;
        opacity: 0.8;
        transition: opacity 0.3s;
        font-size: 1.05em;
    }

    .footer-links a:hover {
        opacity: 1;
        text-decoration: underline;
    }

    .footer-bottom {
        text-align: center;
        padding-top: 20px;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        opacity: 0.7;
        font-size: 0.95em;
    }

    .footer-meta {
        display: flex;
        justify-content: center;
        gap: 20px;
        flex-wrap: wrap;
        margin-top: 10px;
    }

    .footer-meta a {
        color: white;
        text-decoration: none;
        opacity: 0.7;
    }

    .footer-meta a:hover {
        opacity: 1;
        text-decoration: underline;
    }

    @media (max-width: 768px) {
        .footer-grid {
            grid-template-columns: 1fr;
            text-align: center;
        }
    }
</style>

<footer class="site-footer">
    <div class="footer-container">
        <div class="footer-grid">
            <div class="footer-section">
                <h3>🎮 Experiences</h3>
                <ul class="footer-links">
                    <li><a href="/cringeproof/narrative/soulfra">Soulfra Narrative</a></li>
                    <li><a href="/cringeproof/narrative/calriven">CalRiven Story</a></li>
                    <li><a href="/cringeproof/narrative/deathtodata">DeathToData Game</a></li>
                    <li><a href="/draw">Drawing & OCR</a></li>
                    <li><a href="/canvas">Canvas Workspace</a></li>
                </ul>
            </div>

            <div class="footer-section">
                <h3>📚 Learn & Build</h3>
                <ul class="footer-links">
                    <li><a href="/learn">7-Chapter Learning Path</a></li>
                    <li><a href="/dashboard">Browse Content</a></li>
                    <li><a href="/galleries">QR Galleries</a></li>
                    <li><a href="/brands/overview">Brand System</a></li>
                    <li><a href="/canvas/tracking">Your Data</a></li>
                </ul>
            </div>

            <div class="footer-section">
                <h3>🔧 System</h3>
                <ul class="footer-links">
                    <li><a href="/status">System Status</a></li>
                    <li><a href="/simple-test">Run Tests</a></li>
                    <li><a href="/api/docs">API Docs</a></li>
                    <li><a href="/sitemap.xml">Sitemap</a></li>
                    <li><a href="/admin/dashboard">Admin Panel</a></li>
                </ul>
            </div>

            <div class="footer-section">
                <h3>🌙 About</h3>
                <ul class="footer-links">
                    <li><a href="/">Home</a></li>
                    <li><a href="/about">About Soulfra</a></li>
                    <li><a href="/privacy">Privacy</a></li>
                    <li><a href="/terms">Terms</a></li>
                </ul>
            </div>
        </div>

        <div class="footer-bottom">
            <p>&copy; 2025 Soulfra. Your AI workspace. Ideas → Reality.</p>
            <div class="footer-meta">
                <a href="/sitemap.xml">Sitemap</a>
                <a href="/robots.txt">Robots</a>
                <a href="/status">System Health</a>
            </div>
        </div>
    </div>
</footer>
"""


# ===========================================
# HELPER FUNCTIONS
# ===========================================

def render_page_with_nav(title, content, show_header=True, show_footer=True):
    """
    Wrap content with navigation components

    Args:
        title: Page title
        content: Main page content (HTML)
        show_header: Include navigation header
        show_footer: Include site footer

    Returns:
        Complete HTML page with navigation
    """
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Soulfra</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
        }}

        .page-content {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}
    </style>
</head>
<body>
    {NAVIGATION_HEADER if show_header else ''}

    <div class="page-content">
        {content}
    </div>

    {SITE_FOOTER if show_footer else ''}
</body>
</html>
"""
    return html


def get_navigation_links():
    """
    Get navigation links as Python dict for template rendering

    Returns:
        Dict with categorized navigation links
    """
    return {
        'main': [
            {'url': '/', 'text': '🏠 Home'},
            {'url': '/cringeproof/narrative/soulfra', 'text': '🎮 Play Game'},
            {'url': '/learn', 'text': '🎓 Learn'},
            {'url': '/draw', 'text': '✏️ Draw'},
            {'url': '/canvas', 'text': '🎨 Canvas'},
            {'url': '/dashboard', 'text': '📚 Content'},
        ],
        'tools': [
            {'url': '/galleries', 'text': '🖼️ Galleries'},
            {'url': '/brands/overview', 'text': '🏷️ Brands'},
            {'url': '/canvas/tracking', 'text': '📊 Your Data'},
            {'url': '/status', 'text': '🔧 Status'},
        ],
        'system': [
            {'url': '/simple-test', 'text': 'Run Tests'},
            {'url': '/api/docs', 'text': 'API Docs'},
            {'url': '/admin/dashboard', 'text': 'Admin Panel'},
        ]
    }


# ===========================================
# USAGE EXAMPLES
# ===========================================

if __name__ == '__main__':
    # Example 1: Direct HTML inclusion
    print("Example 1: Navigation Header HTML")
    print("=" * 60)
    print(NAVIGATION_HEADER[:200] + "...")
    print()

    # Example 2: Complete page wrapper
    print("Example 2: Complete Page")
    print("=" * 60)
    sample_content = "<h1>Welcome to My Page</h1><p>This is sample content.</p>"
    full_page = render_page_with_nav("Test Page", sample_content)
    print(full_page[:300] + "...")
    print()

    # Example 3: Navigation links as data
    print("Example 3: Navigation Links (for Jinja templates)")
    print("=" * 60)
    import json
    print(json.dumps(get_navigation_links(), indent=2))
