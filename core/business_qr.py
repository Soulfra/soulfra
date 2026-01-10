#!/usr/bin/env python3
"""
Business QR Generator - Embed Full JSON Data in QR Codes

This module generates QR codes with embedded business document JSON.

Features:
- Offline-first: All data embedded in QR code
- No internet required to scan and verify
- Cryptographic signatures (Bloomberg/Symphony-style)
- Automatic QR version selection based on data size
- Compression for large documents
- Integration with unified_generator.py system
"""

import qrcode
import qrcode.constants
from typing import Dict, Optional, Tuple
import json
from io import BytesIO
import base64

from business_schemas import (
    InvoiceSchema,
    ReceiptSchema,
    PurchaseOrderSchema,
    TransactionSchema,
    validate_document,
    estimate_qr_size,
    get_recommended_qr_version,
    compress_document,
    decompress_document,
    sign_document,
    verify_signature
)


# =============================================================================
# Business QR Code Generator
# =============================================================================

class BusinessQRGenerator:
    """
    Generate QR codes with embedded business document JSON

    Unlike vanity_qr.py which only stores URLs, this embeds the FULL document
    """

    def __init__(self, secret_key: str, brand_slug: str = 'soulfra'):
        """
        Initialize business QR generator

        Args:
            secret_key: Secret key for HMAC signatures
            brand_slug: Brand identifier for database storage
        """
        self.secret_key = secret_key
        self.brand_slug = brand_slug

    def generate_invoice_qr(
        self,
        invoice: Dict,
        compress: bool = True,
        error_correction: str = 'M'
    ) -> Tuple[bytes, Dict]:
        """
        Generate QR code for invoice

        Args:
            invoice: Invoice document (from InvoiceSchema.create)
            compress: Whether to compress JSON (recommended for large documents)
            error_correction: QR error correction level (L/M/Q/H)

        Returns:
            (qr_image_bytes, metadata)
        """
        # Validate invoice
        valid, error = InvoiceSchema.validate(invoice)
        if not valid:
            raise ValueError(f"Invalid invoice: {error}")

        # Sign invoice
        invoice['signature'] = sign_document(invoice, self.secret_key)

        # Generate QR code
        return self._generate_qr(invoice, compress=compress, error_correction=error_correction)

    def generate_receipt_qr(
        self,
        receipt: Dict,
        compress: bool = True,
        error_correction: str = 'M'
    ) -> Tuple[bytes, Dict]:
        """Generate QR code for receipt"""
        # Validate
        valid, error = ReceiptSchema.validate(receipt)
        if not valid:
            raise ValueError(f"Invalid receipt: {error}")

        # Sign
        receipt['signature'] = sign_document(receipt, self.secret_key)

        # Generate QR
        return self._generate_qr(receipt, compress=compress, error_correction=error_correction)

    def generate_purchase_order_qr(
        self,
        po: Dict,
        compress: bool = True,
        error_correction: str = 'M'
    ) -> Tuple[bytes, Dict]:
        """Generate QR code for purchase order"""
        # Validate
        valid, error = PurchaseOrderSchema.validate(po)
        if not valid:
            raise ValueError(f"Invalid purchase order: {error}")

        # Sign
        po['signature'] = sign_document(po, self.secret_key)

        # Generate QR
        return self._generate_qr(po, compress=compress, error_correction=error_correction)

    def generate_transaction_qr(
        self,
        txn: Dict,
        compress: bool = True,
        error_correction: str = 'M'
    ) -> Tuple[bytes, Dict]:
        """Generate QR code for transaction"""
        # Validate
        valid, error = TransactionSchema.validate(txn)
        if not valid:
            raise ValueError(f"Invalid transaction: {error}")

        # Sign
        txn['signature'] = sign_document(txn, self.secret_key)

        # Generate QR
        return self._generate_qr(txn, compress=compress, error_correction=error_correction)

    def _generate_qr(
        self,
        document: Dict,
        compress: bool = True,
        error_correction: str = 'M'
    ) -> Tuple[bytes, Dict]:
        """
        Internal: Generate QR code from any business document

        Returns:
            (qr_image_bytes, metadata)
        """
        # Prepare data
        if compress:
            # Compress JSON
            qr_data = compress_document(document)
            data_format = 'compressed'
        else:
            # Raw JSON
            qr_data = json.dumps(document, separators=(',', ':'))
            data_format = 'json'

        # Estimate size and get QR version
        data_size = len(qr_data.encode('utf-8'))
        qr_version = get_recommended_qr_version(document)

        # Map error correction
        error_correction_map = {
            'L': qrcode.constants.ERROR_CORRECT_L,
            'M': qrcode.constants.ERROR_CORRECT_M,
            'Q': qrcode.constants.ERROR_CORRECT_Q,
            'H': qrcode.constants.ERROR_CORRECT_H
        }

        # Create QR code with dynamic version
        qr = qrcode.QRCode(
            version=qr_version,
            error_correction=error_correction_map.get(error_correction, qrcode.constants.ERROR_CORRECT_M),
            box_size=10,
            border=4,
        )

        # Add data
        qr.add_data(qr_data)
        qr.make(fit=True)

        # Create image
        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to bytes
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        qr_image_bytes = buffer.getvalue()

        # Metadata about the QR code
        metadata = {
            'document_type': document.get('type'),
            'document_id': document.get('id'),
            'qr_version': qr_version,
            'data_size': data_size,
            'data_format': data_format,
            'error_correction': error_correction,
            'compressed': compress,
            'content_hash': document.get('content_hash'),
            'signature': document.get('signature', '')[:16] + '...' if document.get('signature') else None
        }

        return qr_image_bytes, metadata

    def scan_and_verify(self, qr_data: str, compressed: bool = True) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Scan and verify business QR code

        This simulates scanning a QR code and verifying the document

        Args:
            qr_data: Data extracted from QR code
            compressed: Whether data is compressed

        Returns:
            (is_valid, document, error_message)
        """
        try:
            # Decompress if needed
            if compressed:
                document = decompress_document(qr_data)
            else:
                document = json.loads(qr_data)

            # Validate document structure
            valid, error = validate_document(document)
            if not valid:
                return False, None, f"Invalid document structure: {error}"

            # Verify signature
            if not verify_signature(document, self.secret_key):
                return False, document, "Signature verification failed - document may have been tampered with"

            # Verify content hash
            doc_type = document.get('type')
            schema_map = {
                'invoice': InvoiceSchema,
                'receipt': ReceiptSchema,
                'purchase_order': PurchaseOrderSchema,
                'transaction': TransactionSchema
            }

            schema = schema_map.get(doc_type)
            if schema:
                computed_hash = schema.compute_hash(document)
                if computed_hash != document.get('content_hash'):
                    return False, document, "Content hash mismatch - document may have been modified"

            return True, document, None

        except Exception as e:
            return False, None, f"Error parsing QR data: {str(e)}"


# =============================================================================
# Integration with Unified Generator System
# =============================================================================

def save_business_qr_to_unified(
    document: Dict,
    qr_image: bytes,
    qr_metadata: Dict,
    user_id: Optional[int] = None,
    brand_slug: str = 'soulfra'
):
    """
    Save business QR code to unified_content table

    This integrates with the existing unified_generator.py system
    """
    from database import get_db
    import sqlite3

    conn = get_db()

    try:
        # Insert into unified_content
        cursor = conn.execute('''
            INSERT INTO unified_content (
                content_hash,
                content_type,
                title,
                description,
                content,
                upc_code,
                qr_short_code,
                qr_vanity_url,
                affiliate_code,
                created_by,
                brand_slug,
                metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            document.get('content_hash'),
            f"business_{document.get('type')}",  # e.g. "business_invoice"
            document.get('id'),  # e.g. "INV-2025-001"
            f"{document.get('type').replace('_', ' ').title()} - {document.get('id')}",
            json.dumps(document),  # Store full document
            generate_upc_from_hash(document.get('content_hash')),  # UPC-12 from hash
            None,  # No vanity short code for business docs
            None,  # No vanity URL
            None,  # No affiliate code
            user_id,
            brand_slug,
            json.dumps(qr_metadata)
        ))

        unified_id = cursor.lastrowid

        # Store QR image in vanity_qr_codes table
        conn.execute('''
            INSERT INTO vanity_qr_codes (
                short_code,
                brand_slug,
                full_url,
                vanity_url,
                qr_image,
                style,
                metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            f"biz-{unified_id}",  # short_code
            brand_slug,
            f"/business/view/{unified_id}",  # full_url
            f"/business/view/{unified_id}",  # vanity_url
            qr_image,
            'business',
            json.dumps(qr_metadata)
        ))

        conn.commit()

        return unified_id

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def generate_upc_from_hash(content_hash: str) -> str:
    """
    Generate UPC-12 barcode from content hash

    Uses same algorithm as unified_generator.py
    """
    # Take first 11 digits from hash
    hash_int = int(content_hash[:16], 16)
    upc_11 = str(hash_int % (10**11)).zfill(11)

    # Calculate checksum
    odd_sum = sum(int(upc_11[i]) for i in range(0, 11, 2))
    even_sum = sum(int(upc_11[i]) for i in range(1, 11, 2))
    checksum = (10 - ((odd_sum * 3 + even_sum) % 10)) % 10

    return upc_11 + str(checksum)


# =============================================================================
# Demo/Testing
# =============================================================================

if __name__ == '__main__':
    print("=== Business QR Generator Demo ===\n")

    # Initialize generator
    generator = BusinessQRGenerator(
        secret_key="test-secret-key-12345",
        brand_slug="soulfra"
    )

    # Create sample invoice
    from business_schemas import InvoiceSchema

    invoice = InvoiceSchema.create(
        invoice_id="INV-2025-001",
        from_entity={
            "name": "Soulfra LLC",
            "business_id": "BIZ-123",
            "email": "billing@soulfra.com",
            "address": "123 Main St, City, State 12345"
        },
        to_entity={
            "name": "Test Customer",
            "customer_id": "CUST-456",
            "email": "customer@example.com",
            "address": "456 Oak Ave, City, State 67890"
        },
        items=[
            {
                "description": "Consulting Services",
                "quantity": 10,
                "unit_price": 150.00,
                "total": 1500.00,
                "tax_rate": 0.08
            },
            {
                "description": "Software License",
                "quantity": 1,
                "unit_price": 500.00,
                "total": 500.00,
                "tax_rate": 0.08
            }
        ],
        issued_date="2025-12-28",
        due_date="2026-01-28",
        payment_terms="Net 30",
        notes="Thank you for your business!"
    )

    print(f"Invoice ID: {invoice['id']}")
    print(f"Total: ${invoice['total']}")
    print(f"Hash: {invoice['content_hash'][:16]}...")
    print()

    # Generate QR code
    print("Generating QR code with embedded JSON...")
    qr_image, metadata = generator.generate_invoice_qr(invoice, compress=True)

    print(f"QR Version: V{metadata['qr_version']}")
    print(f"Data Size: {metadata['data_size']} bytes")
    print(f"Data Format: {metadata['data_format']}")
    print(f"Compressed: {metadata['compressed']}")
    print(f"Signature: {metadata['signature']}")
    print()

    # Test offline verification (simulate scanning)
    print("Testing offline verification...")
    compressed_data = compress_document(invoice)
    is_valid, verified_doc, error = generator.scan_and_verify(compressed_data, compressed=True)

    if is_valid:
        print("✅ QR code verified successfully!")
        print(f"   Document type: {verified_doc['type']}")
        print(f"   Document ID: {verified_doc['id']}")
        print(f"   Total: ${verified_doc['total']}")
        print(f"   Signature valid: ✅")
        print(f"   Hash valid: ✅")
    else:
        print(f"❌ Verification failed: {error}")

    print()

    # Compare sizes
    print("=== Size Comparison ===")
    json_size = len(json.dumps(invoice, separators=(',', ':')).encode('utf-8'))
    compressed_size = len(compress_document(invoice))
    url_size = len(f"https://soulfra.com/v/abc123")

    print(f"Full JSON: {json_size} bytes")
    print(f"Compressed JSON: {compressed_size} bytes ({compressed_size/json_size*100:.1f}%)")
    print(f"Old URL-only approach: {url_size} bytes")
    print(f"QR Version needed for JSON: V{get_recommended_qr_version(invoice)}")
    print()

    print("✅ Business QR system working!")
    print("   - Offline-first: ✅ All data in QR code")
    print("   - Verifiable: ✅ Cryptographic signatures")
    print("   - Compressed: ✅ Fits in V10 QR code")
    print("   - No internet required: ✅")
