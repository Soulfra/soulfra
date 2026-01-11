#!/usr/bin/env python3
"""
Unified QR Factory - Single Entry Point for All QR Systems

This module provides a unified interface to all QR generation systems.
Instead of importing multiple QR generators, use this factory.

Usage:
    from qr_unified import QRFactory

    # Business invoice QR
    qr = QRFactory.create('invoice', data={...})

    # Vanity URL QR
    qr = QRFactory.create('vanity', url='https://example.com', brand='soulfra')

    # Gallery QR
    qr = QRFactory.create('gallery', post_id=29)
"""

from typing import Dict, Optional, Tuple, Any
import json
from io import BytesIO

# Import all QR generators
from business_qr import BusinessQRGenerator
from vanity_qr import create_and_save_vanity_qr, BRAND_DOMAINS
from advanced_qr import AdvancedQRGenerator
from qr_gallery_system import generate_qr_code as generate_gallery_qr
from dm_via_qr import generate_dm_token
import qrcode


# =============================================================================
# QR Factory
# =============================================================================

class QRFactory:
    """
    Unified factory for creating QR codes across all systems

    Supported types:
    - 'invoice': Business invoice with full JSON embedding
    - 'receipt': Payment receipt with full JSON embedding
    - 'purchase_order': Purchase order with full JSON embedding
    - 'vanity': Branded URL shortener
    - 'gallery': Gallery QR code
    - 'advanced': Styled QR with gradients/logos
    - 'dm': In-person DM verification QR
    - 'simple': Basic QR code (no branding)
    """

    # Default configuration
    DEFAULT_BRAND = 'soulfra'
    DEFAULT_SECRET_KEY = 'default-secret-key-change-in-production'

    @classmethod
    def create(
        cls,
        qr_type: str,
        data: Optional[Dict] = None,
        url: Optional[str] = None,
        brand: Optional[str] = None,
        **kwargs
    ) -> Tuple[bytes, Dict]:
        """
        Create QR code of specified type

        Args:
            qr_type: Type of QR code ('invoice', 'receipt', 'vanity', etc.)
            data: Document data (for business QR types)
            url: URL (for vanity/simple types)
            brand: Brand slug (default: 'soulfra')
            **kwargs: Additional type-specific arguments

        Returns:
            (qr_image_bytes, metadata)

        Examples:
            # Business invoice
            qr, meta = QRFactory.create('invoice', data={
                'invoice_id': 'INV-001',
                'from_entity': {...},
                'to_entity': {...},
                'items': [...]
            })

            # Vanity URL
            qr, meta = QRFactory.create('vanity',
                url='https://example.com',
                brand='cringeproof'
            )

            # Advanced styled QR
            qr, meta = QRFactory.create('advanced',
                url='https://example.com',
                style='rounded',
                primary_color='#8B5CF6'
            )
        """
        brand = brand or cls.DEFAULT_BRAND

        # Route to appropriate generator
        if qr_type == 'invoice':
            return cls._create_invoice(data, brand, **kwargs)

        elif qr_type == 'receipt':
            return cls._create_receipt(data, brand, **kwargs)

        elif qr_type == 'purchase_order':
            return cls._create_purchase_order(data, brand, **kwargs)

        elif qr_type == 'vanity':
            return cls._create_vanity(url, brand, **kwargs)

        elif qr_type == 'gallery':
            return cls._create_gallery(brand, **kwargs)

        elif qr_type == 'advanced':
            return cls._create_advanced(url or data.get('url'), brand, **kwargs)

        elif qr_type == 'dm':
            return cls._create_dm(**kwargs)

        elif qr_type == 'simple':
            return cls._create_simple(url or data, **kwargs)

        else:
            raise ValueError(f"Unknown QR type: {qr_type}")

    # =========================================================================
    # Business QR Types
    # =========================================================================

    @classmethod
    def _create_invoice(cls, data: Dict, brand: str, **kwargs) -> Tuple[bytes, Dict]:
        """Create invoice QR with full JSON embedding"""
        generator = BusinessQRGenerator(
            secret_key=kwargs.get('secret_key', cls.DEFAULT_SECRET_KEY),
            brand_slug=brand
        )

        qr_bytes, metadata = generator.generate_invoice_qr(
            invoice=data,
            compress=kwargs.get('compress', True),
            error_correction=kwargs.get('error_correction', 'M')
        )

        return qr_bytes, metadata

    @classmethod
    def _create_receipt(cls, data: Dict, brand: str, **kwargs) -> Tuple[bytes, Dict]:
        """Create receipt QR with full JSON embedding"""
        generator = BusinessQRGenerator(
            secret_key=kwargs.get('secret_key', cls.DEFAULT_SECRET_KEY),
            brand_slug=brand
        )

        qr_bytes, metadata = generator.generate_receipt_qr(
            receipt=data,
            compress=kwargs.get('compress', True),
            error_correction=kwargs.get('error_correction', 'M')
        )

        return qr_bytes, metadata

    @classmethod
    def _create_purchase_order(cls, data: Dict, brand: str, **kwargs) -> Tuple[bytes, Dict]:
        """Create purchase order QR with full JSON embedding"""
        generator = BusinessQRGenerator(
            secret_key=kwargs.get('secret_key', cls.DEFAULT_SECRET_KEY),
            brand_slug=brand
        )

        qr_bytes, metadata = generator.generate_purchase_order_qr(
            purchase_order=data,
            compress=kwargs.get('compress', True),
            error_correction=kwargs.get('error_correction', 'M')
        )

        return qr_bytes, metadata

    # =========================================================================
    # Vanity QR
    # =========================================================================

    @classmethod
    def _create_vanity(cls, url: str, brand: str, **kwargs) -> Tuple[bytes, Dict]:
        """Create branded vanity QR with URL shortening"""
        from database import get_db

        # Create vanity QR in database
        qr_id = create_and_save_vanity_qr(
            full_url=url,
            brand_slug=brand,
            custom_code=kwargs.get('custom_code')
        )

        # Retrieve QR image from database
        conn = get_db()
        conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

        qr_data = conn.execute(
            'SELECT * FROM vanity_qr_codes WHERE id = ?',
            (qr_id,)
        ).fetchone()

        conn.close()

        if not qr_data:
            raise ValueError(f"Failed to create vanity QR for {url}")

        metadata = {
            'qr_id': qr_id,
            'short_code': qr_data['short_code'],
            'vanity_url': qr_data['vanity_url'],
            'brand': brand,
            'style': qr_data['style']
        }

        return qr_data['qr_image'], metadata

    # =========================================================================
    # Gallery QR
    # =========================================================================

    @classmethod
    def _create_gallery(cls, brand: str, **kwargs) -> Tuple[bytes, Dict]:
        """Create gallery QR code"""
        post_id = kwargs.get('post_id')
        slug = kwargs.get('slug', f'post-{post_id}')

        # Generate gallery URL
        gallery_url = f"https://{BRAND_DOMAINS[brand]['domain']}/gallery/{slug}"

        # Create QR image
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(gallery_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to bytes
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)

        metadata = {
            'url': gallery_url,
            'post_id': post_id,
            'slug': slug,
            'brand': brand
        }

        return img_bytes.read(), metadata

    # =========================================================================
    # Advanced Styled QR
    # =========================================================================

    @classmethod
    def _create_advanced(cls, url: str, brand: str, **kwargs) -> Tuple[bytes, Dict]:
        """Create advanced styled QR with gradients/logos"""
        brand_config = BRAND_DOMAINS.get(brand, BRAND_DOMAINS['soulfra'])

        generator = AdvancedQRGenerator(
            data=url,
            style=kwargs.get('style', 'rounded'),
            primary_color=kwargs.get('primary_color', brand_config['colors']['primary']),
            secondary_color=kwargs.get('secondary_color', brand_config['colors']['secondary']),
            label=kwargs.get('label'),
            logo_path=kwargs.get('logo_path'),
            size=kwargs.get('size', 512)
        )

        qr_bytes = generator.generate()

        metadata = {
            'url': url,
            'brand': brand,
            'style': kwargs.get('style', 'rounded'),
            'size': kwargs.get('size', 512)
        }

        return qr_bytes, metadata

    # =========================================================================
    # DM Verification QR
    # =========================================================================

    @classmethod
    def _create_dm(cls, **kwargs) -> Tuple[bytes, Dict]:
        """Create in-person DM verification QR"""
        user_id = kwargs.get('user_id')
        expiry_minutes = kwargs.get('expiry_minutes', 5)

        # Generate secure DM token
        token = generate_dm_token(user_id, expiry_minutes)

        # Create QR with token
        dm_url = f"https://soulfra.com/dm/scan?token={token}"

        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(dm_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to bytes
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)

        metadata = {
            'user_id': user_id,
            'token': token,
            'expiry_minutes': expiry_minutes,
            'url': dm_url
        }

        return img_bytes.read(), metadata

    # =========================================================================
    # Simple QR (No Branding)
    # =========================================================================

    @classmethod
    def _create_simple(cls, data: Any, **kwargs) -> Tuple[bytes, Dict]:
        """Create basic QR code with no branding"""
        # Convert data to string if dict
        if isinstance(data, dict):
            data = json.dumps(data)

        qr = qrcode.QRCode(
            version=kwargs.get('version', 1),
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=kwargs.get('box_size', 10),
            border=kwargs.get('border', 4)
        )

        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(
            fill_color=kwargs.get('fill_color', 'black'),
            back_color=kwargs.get('back_color', 'white')
        )

        # Convert to bytes
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)

        metadata = {
            'data': data[:100],  # Truncate for metadata
            'version': kwargs.get('version', 1)
        }

        return img_bytes.read(), metadata


# =============================================================================
# Utility Functions
# =============================================================================

def quick_invoice_qr(invoice_data: Dict, brand: str = 'soulfra') -> bytes:
    """Quick helper to generate invoice QR"""
    qr_bytes, _ = QRFactory.create('invoice', data=invoice_data, brand=brand)
    return qr_bytes


def quick_vanity_qr(url: str, brand: str = 'soulfra') -> bytes:
    """Quick helper to generate vanity QR"""
    qr_bytes, _ = QRFactory.create('vanity', url=url, brand=brand)
    return qr_bytes


def quick_qr(data: str) -> bytes:
    """Quick helper to generate simple QR"""
    qr_bytes, _ = QRFactory.create('simple', data=data)
    return qr_bytes


# =============================================================================
# Example Usage
# =============================================================================

if __name__ == '__main__':
    # Example 1: Business invoice QR
    from business_schemas import InvoiceSchema

    invoice = InvoiceSchema.create(
        invoice_id='INV-2025-001',
        from_entity={
            'name': 'Soulfra LLC',
            'business_id': 'BIZ-123',
            'email': 'billing@soulfra.com'
        },
        to_entity={
            'name': 'Test Customer',
            'customer_id': 'CUST-456',
            'email': 'customer@example.com'
        },
        items=[{
            'description': 'Consulting Services',
            'quantity': 10,
            'unit_price': 100.00
        }],
        issued_date='2025-12-30',
        due_date='2026-01-28'
    )

    qr, meta = QRFactory.create('invoice', data=invoice, brand='soulfra')
    print(f"Created invoice QR: {meta['data_size']} bytes, version {meta['qr_version']}")

    # Example 2: Vanity URL QR
    qr, meta = QRFactory.create('vanity', url='https://soulfra.com/blog/post', brand='soulfra')
    print(f"Created vanity QR: {meta['vanity_url']}")

    # Example 3: Simple QR
    qr, meta = QRFactory.create('simple', data='Hello, World!')
    print(f"Created simple QR: {len(qr)} bytes")
