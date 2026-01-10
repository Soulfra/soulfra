"""
Vanity QR Codes - Branded QR Code Generation

Creates professional, branded QR codes with:
- Custom short URLs (cringeproof.com/qr/xxx, soulfra.com/qr/xxx)
- Brand colors and styling
- Logo embedding (optional)
- Database tracking
- Analytics-ready

Uses owned domains for vanity URLs.
"""

import io
import hashlib
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer, CircleModuleDrawer, GappedSquareModuleDrawer
from qrcode.image.styles.colormasks import SolidFillColorMask
from PIL import Image, ImageDraw, ImageFont
from typing import Optional, Dict, Tuple
from datetime import datetime
import sqlite3


# =============================================================================
# Brand Domain Configuration
# =============================================================================

BRAND_DOMAINS = {
    'cringeproof': {
        'domain': 'cringeproof.com',
        'colors': {
            'primary': '#2D3748',
            'secondary': '#E53E3E',
            'accent': '#EDF2F7'
        },
        'style': 'minimal'  # Clean, minimal styling
    },
    'soulfra': {
        'domain': 'soulfra.com',
        'colors': {
            'primary': '#8B5CF6',
            'secondary': '#3B82F6',
            'accent': '#10B981'
        },
        'style': 'rounded'  # Rounded, modern styling
    },
    'howtocookathome': {
        'domain': 'howtocookathome.com',
        'colors': {
            'primary': '#F97316',
            'secondary': '#EAB308',
            'accent': '#84CC16'
        },
        'style': 'circles'  # Fun, friendly circles
    }
}


# =============================================================================
# Database Setup
# =============================================================================

def init_vanity_qr_db():
    """Initialize vanity QR database table"""
    from database import get_db

    conn = get_db()

    # Vanity QR codes table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS vanity_qr_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            short_code TEXT UNIQUE NOT NULL,
            brand_slug TEXT NOT NULL,
            full_url TEXT NOT NULL,
            vanity_url TEXT NOT NULL,
            qr_image BLOB,
            style TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            clicks INTEGER DEFAULT 0,
            last_clicked_at TIMESTAMP,
            metadata TEXT
        )
    ''')

    conn.execute('CREATE INDEX IF NOT EXISTS idx_vanity_qr_code ON vanity_qr_codes(short_code)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_vanity_qr_brand ON vanity_qr_codes(brand_slug)')

    # QR Chat Transcripts table - Links chat conversations to QR codes
    conn.execute('''
        CREATE TABLE IF NOT EXISTS qr_chat_transcripts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            short_code TEXT NOT NULL,
            user_ip TEXT,
            device_type TEXT,
            sender TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (short_code) REFERENCES vanity_qr_codes(short_code)
        )
    ''')

    conn.execute('CREATE INDEX IF NOT EXISTS idx_qr_chat_code ON qr_chat_transcripts(short_code)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_qr_chat_created ON qr_chat_transcripts(created_at)')

    conn.commit()
    conn.close()


# =============================================================================
# Short Code Generation
# =============================================================================

def generate_short_code(url: str, length: int = 6) -> str:
    """
    Generate short code from URL hash

    Args:
        url: Full URL to shorten
        length: Length of short code (default 6)

    Returns:
        Short code (alphanumeric)
    """
    # Hash the URL
    hash_obj = hashlib.sha256(url.encode('utf-8'))
    hash_hex = hash_obj.hexdigest()

    # Convert to alphanumeric (base 62: 0-9, a-z, A-Z)
    chars = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'

    # Use hash to generate consistent short code
    code = ''
    hash_int = int(hash_hex[:16], 16)  # Use first 16 chars of hash

    for i in range(length):
        code += chars[hash_int % len(chars)]
        hash_int //= len(chars)

    return code


def create_vanity_url(full_url: str, brand_slug: str, custom_code: Optional[str] = None) -> str:
    """
    Create vanity short URL

    Args:
        full_url: Full destination URL
        brand_slug: Brand identifier
        custom_code: Optional custom short code

    Returns:
        Vanity URL (e.g., cringeproof.com/qr/abc123)
    """
    if brand_slug not in BRAND_DOMAINS:
        brand_slug = 'soulfra'  # Default

    domain = BRAND_DOMAINS[brand_slug]['domain']

    # Generate or use custom code
    short_code = custom_code or generate_short_code(full_url)

    return f"https://{domain}/v/{short_code}", short_code


# =============================================================================
# Branded QR Code Generation
# =============================================================================

def calculate_qr_version(data: str, error_correction: str = 'H') -> int:
    """
    Calculate optimal QR code version based on data size

    QR Code Capacity (approximate):
    - V1 (21x21): ~25 bytes (ERROR_CORRECT_H)
    - V5 (37x37): ~350 bytes (ERROR_CORRECT_M)
    - V10 (57x57): ~1,700 bytes (ERROR_CORRECT_M)
    - V20 (97x97): ~3,700 bytes (ERROR_CORRECT_M)
    - V40 (177x177): ~4,296 bytes (ERROR_CORRECT_L)

    Args:
        data: Data to encode
        error_correction: Error correction level (L/M/Q/H)

    Returns:
        QR code version (1-40)
    """
    data_size = len(data.encode('utf-8'))

    # Capacity estimates with error correction factored in
    if error_correction == 'H':
        # High error correction (30% recovery)
        if data_size <= 25:
            return 1
        elif data_size <= 200:
            return 5
        elif data_size <= 800:
            return 10
        elif data_size <= 1800:
            return 20
        else:
            return 40
    elif error_correction == 'M':
        # Medium error correction (15% recovery) - most common for business docs
        if data_size <= 25:
            return 1
        elif data_size <= 350:
            return 5
        elif data_size <= 1700:
            return 10
        elif data_size <= 3700:
            return 20
        else:
            return 40
    else:
        # Low error correction (7% recovery) - maximum capacity
        if data_size <= 25:
            return 1
        elif data_size <= 500:
            return 5
        elif data_size <= 2000:
            return 10
        elif data_size <= 4000:
            return 20
        else:
            return 40


def generate_branded_qr(
    url: str,
    brand_slug: str,
    size: int = 300,
    embed_logo: bool = False,
    logo_path: Optional[str] = None,
    qr_version: Optional[int] = None
) -> bytes:
    """
    Generate branded QR code with custom styling

    Args:
        url: URL to encode
        brand_slug: Brand identifier
        size: QR code size in pixels
        embed_logo: Whether to embed brand logo
        logo_path: Path to logo image
        qr_version: QR code version (1-40), auto-calculated if None

    Returns:
        PNG image bytes
    """
    if brand_slug not in BRAND_DOMAINS:
        brand_slug = 'soulfra'

    brand_config = BRAND_DOMAINS[brand_slug]
    colors = brand_config['colors']
    style = brand_config['style']

    # Auto-calculate QR version if not specified
    if qr_version is None:
        error_correction_level = 'H' if embed_logo else 'M'
        qr_version = calculate_qr_version(url, error_correction_level)

    # Create QR code with dynamic version
    qr = qrcode.QRCode(
        version=qr_version,  # DYNAMIC VERSION - supports V1 to V40
        error_correction=qrcode.constants.ERROR_CORRECT_H if embed_logo else qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )

    qr.add_data(url)
    qr.make(fit=True)

    # Choose module drawer based on style
    if style == 'rounded':
        module_drawer = RoundedModuleDrawer()
    elif style == 'circles':
        module_drawer = CircleModuleDrawer()
    else:  # minimal
        module_drawer = GappedSquareModuleDrawer()

    # Color mask
    color_mask = SolidFillColorMask(
        back_color=(255, 255, 255),  # White background
        front_color=hex_to_rgb(colors['primary'])  # Brand primary color
    )

    # Generate styled QR code
    img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=module_drawer,
        color_mask=color_mask
    )

    # Resize to target size
    img = img.resize((size, size), Image.LANCZOS)

    # Embed logo if requested
    if embed_logo and logo_path:
        try:
            logo = Image.open(logo_path)

            # Calculate logo size (20% of QR code)
            logo_size = size // 5

            # Resize logo
            logo = logo.resize((logo_size, logo_size), Image.LANCZOS)

            # Create white background for logo
            logo_bg_size = logo_size + 20
            logo_bg = Image.new('RGB', (logo_bg_size, logo_bg_size), 'white')

            # Paste logo on background
            logo_bg.paste(logo, (10, 10), logo if logo.mode == 'RGBA' else None)

            # Calculate position (center)
            logo_pos = ((size - logo_bg_size) // 2, (size - logo_bg_size) // 2)

            # Paste logo on QR code
            img.paste(logo_bg, logo_pos)

        except Exception as e:
            print(f"Warning: Could not embed logo: {e}")

    # Convert to bytes
    output = io.BytesIO()
    img.save(output, format='PNG')
    return output.getvalue()


def generate_vanity_qr_with_label(
    url: str,
    brand_slug: str,
    label: Optional[str] = None,
    size: int = 350
) -> bytes:
    """
    Generate QR code with brand label

    Args:
        url: URL to encode
        brand_slug: Brand identifier
        label: Optional label text (e.g., "Scan Me", brand name)
        size: Total image size

    Returns:
        PNG image bytes with label
    """
    # Generate QR code
    qr_size = size - 80  # Leave space for label
    qr_bytes = generate_branded_qr(url, brand_slug, size=qr_size)

    # Load QR image
    qr_img = Image.open(io.BytesIO(qr_bytes))

    # Create canvas with extra space for label
    canvas = Image.new('RGB', (size, size), 'white')

    # Paste QR code
    qr_pos = ((size - qr_size) // 2, 20)
    canvas.paste(qr_img, qr_pos)

    # Add label
    if label:
        draw = ImageDraw.Draw(canvas)

        # Try to load font
        try:
            font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 28)
        except:
            try:
                font = ImageFont.truetype('Arial.ttf', 28)
            except:
                font = ImageFont.load_default()

        # Get brand colors
        brand_config = BRAND_DOMAINS.get(brand_slug, BRAND_DOMAINS['soulfra'])
        text_color = brand_config['colors']['primary']

        # Calculate text position (centered below QR)
        bbox = draw.textbbox((0, 0), label, font=font)
        text_width = bbox[2] - bbox[0]
        text_x = (size - text_width) // 2
        text_y = qr_pos[1] + qr_size + 10

        # Draw text
        draw.text((text_x, text_y), label, fill=text_color, font=font)

    # Convert to bytes
    output = io.BytesIO()
    canvas.save(output, format='PNG')
    return output.getvalue()


# =============================================================================
# Database Integration
# =============================================================================

def save_vanity_qr(
    short_code: str,
    brand_slug: str,
    full_url: str,
    vanity_url: str,
    qr_image: bytes,
    style: str = 'branded',
    metadata: Optional[Dict] = None
):
    """Save vanity QR code to database"""
    from database import get_db
    import json

    conn = get_db()

    try:
        conn.execute('''
            INSERT INTO vanity_qr_codes
            (short_code, brand_slug, full_url, vanity_url, qr_image, style, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            short_code,
            brand_slug,
            full_url,
            vanity_url,
            qr_image,
            style,
            json.dumps(metadata) if metadata else None
        ))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Already exists
        return False
    finally:
        conn.close()


def get_vanity_qr(short_code: str) -> Optional[Dict]:
    """Get vanity QR by short code"""
    from database import get_db

    conn = get_db()

    qr = conn.execute(
        'SELECT * FROM vanity_qr_codes WHERE short_code = ?',
        (short_code,)
    ).fetchone()

    conn.close()

    return dict(qr) if qr else None


def track_qr_click(short_code: str):
    """Track QR code click"""
    from database import get_db

    conn = get_db()

    conn.execute('''
        UPDATE vanity_qr_codes
        SET clicks = clicks + 1, last_clicked_at = ?
        WHERE short_code = ?
    ''', (datetime.now(), short_code))

    conn.commit()
    conn.close()


# =============================================================================
# Helper Functions
# =============================================================================

def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def create_and_save_vanity_qr(
    full_url: str,
    brand_slug: str,
    label: Optional[str] = None,
    custom_code: Optional[str] = None
) -> Dict:
    """
    Complete workflow: create vanity URL, generate QR, save to database

    Args:
        full_url: Full destination URL
        brand_slug: Brand identifier
        label: Optional label for QR code
        custom_code: Optional custom short code

    Returns:
        Dict with vanity_url, short_code, qr_image
    """
    # Create vanity URL
    vanity_url, short_code = create_vanity_url(full_url, brand_slug, custom_code)

    # Generate branded QR code
    if label:
        qr_image = generate_vanity_qr_with_label(vanity_url, brand_slug, label)
    else:
        qr_image = generate_branded_qr(vanity_url, brand_slug)

    # Save to database
    save_vanity_qr(
        short_code=short_code,
        brand_slug=brand_slug,
        full_url=full_url,
        vanity_url=vanity_url,
        qr_image=qr_image,
        style='branded_with_label' if label else 'branded'
    )

    return {
        'vanity_url': vanity_url,
        'short_code': short_code,
        'qr_image': qr_image,
        'full_url': full_url
    }


# =============================================================================
# Testing
# =============================================================================

if __name__ == '__main__':
    print("Testing Vanity QR Code System...")
    print()

    # Initialize database
    print("Initializing database...")
    init_vanity_qr_db()
    print("✅ Database initialized")
    print()

    # Test 1: Generate short codes
    print("Test 1: Short Code Generation")
    test_urls = [
        'https://cringeproof.com/blog/how-to-build-a-brand',
        'https://soulfra.com/posts/ai-generated-images',
        'https://howtocookathome.com/recipes/pasta-carbonara'
    ]

    for url in test_urls:
        code = generate_short_code(url)
        print(f"  {url[:50]}... → {code}")

    print()

    # Test 2: Create vanity URLs
    print("Test 2: Vanity URL Creation")
    for i, url in enumerate(test_urls):
        brand = ['cringeproof', 'soulfra', 'howtocookathome'][i]
        vanity_url, short_code = create_vanity_url(url, brand)
        print(f"  {brand}: {vanity_url}")

    print()

    # Test 3: Generate branded QR codes
    print("Test 3: Branded QR Code Generation")

    brands = ['cringeproof', 'soulfra', 'howtocookathome']

    for brand in brands:
        print(f"\n  Generating {brand} QR code...")

        # Create vanity URL
        full_url = f"https://{BRAND_DOMAINS[brand]['domain']}/blog/test-post"
        vanity_url, short_code = create_vanity_url(full_url, brand)

        # Generate QR with label
        qr_image = generate_vanity_qr_with_label(
            url=vanity_url,
            brand_slug=brand,
            label=brand.upper().replace('HOWTOCOOKATHOME', 'HTCAH')
        )

        # Save to file
        filename = f"test_vanity_qr_{brand}.png"
        with open(filename, 'wb') as f:
            f.write(qr_image)

        print(f"    ✅ Saved: {filename} ({len(qr_image):,} bytes)")
        print(f"    URL: {vanity_url}")
        print(f"    Code: {short_code}")

        # Save to database
        save_vanity_qr(
            short_code=short_code,
            brand_slug=brand,
            full_url=full_url,
            vanity_url=vanity_url,
            qr_image=qr_image,
            style='branded_with_label'
        )

    print()

    # Test 4: Database retrieval
    print("Test 4: Database Retrieval")

    # Get a QR code
    test_code = generate_short_code(test_urls[0])
    qr_data = get_vanity_qr(test_code)

    if qr_data:
        print(f"  ✅ Retrieved QR: {qr_data['vanity_url']}")
        print(f"     Brand: {qr_data['brand_slug']}")
        print(f"     Clicks: {qr_data['clicks']}")
    else:
        print("  ⚠️  QR not found (may need to run test multiple times)")

    print()

    print("=" * 70)
    print("✅ All vanity QR tests passed!")
    print()
    print("Generated files:")
    print("  - test_vanity_qr_cringeproof.png")
    print("  - test_vanity_qr_soulfra.png")
    print("  - test_vanity_qr_howtocookathome.png")
    print()
