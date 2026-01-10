#!/usr/bin/env python3
"""
Business Schemas - JSON Schemas for Business Documents

Defines structured schemas for:
- Invoices
- Receipts
- Purchase Orders
- Transactions
- Contracts

These schemas can be embedded in QR codes for offline-first business documents.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import hashlib


# =============================================================================
# Schema Definitions
# =============================================================================

class InvoiceSchema:
    """
    Invoice schema for business transactions

    Example:
    {
        "type": "invoice",
        "id": "INV-2025-001",
        "version": "1.0",
        "from": {
            "name": "Soulfra LLC",
            "business_id": "BIZ-123",
            "email": "billing@soulfra.com",
            "address": "123 Main St, City, State 12345"
        },
        "to": {
            "name": "Customer Name",
            "customer_id": "CUST-456",
            "email": "customer@example.com",
            "address": "456 Oak Ave, City, State 67890"
        },
        "items": [
            {
                "description": "Consulting Services",
                "quantity": 10,
                "unit_price": 150.00,
                "total": 1500.00,
                "tax_rate": 0.08
            }
        ],
        "subtotal": 1500.00,
        "tax": 120.00,
        "total": 1620.00,
        "currency": "USD",
        "issued_date": "2025-12-28",
        "due_date": "2026-01-28",
        "payment_terms": "Net 30",
        "status": "pending",
        "notes": "Thank you for your business",
        "content_hash": "abc123...",
        "signature": "def456..."
    }
    """

    @staticmethod
    def create(
        invoice_id: str,
        from_entity: Dict[str, str],
        to_entity: Dict[str, str],
        items: List[Dict[str, Any]],
        issued_date: str,
        due_date: str,
        currency: str = "USD",
        payment_terms: str = "Net 30",
        notes: str = "",
        status: str = "pending"
    ) -> Dict:
        """Create a new invoice"""

        # Calculate totals
        subtotal = sum(item.get('total', 0) for item in items)
        tax = sum(item.get('total', 0) * item.get('tax_rate', 0) for item in items)
        total = subtotal + tax

        invoice = {
            "type": "invoice",
            "id": invoice_id,
            "version": "1.0",
            "from": from_entity,
            "to": to_entity,
            "items": items,
            "subtotal": round(subtotal, 2),
            "tax": round(tax, 2),
            "total": round(total, 2),
            "currency": currency,
            "issued_date": issued_date,
            "due_date": due_date,
            "payment_terms": payment_terms,
            "status": status,
            "notes": notes,
            "created_at": datetime.utcnow().isoformat()
        }

        # Add content hash
        invoice['content_hash'] = InvoiceSchema.compute_hash(invoice)

        return invoice

    @staticmethod
    def compute_hash(invoice: Dict) -> str:
        """Compute SHA-256 hash of invoice (excluding hash and signature fields)"""
        # Remove hash and signature for hashing
        invoice_copy = {k: v for k, v in invoice.items() if k not in ['content_hash', 'signature']}

        # Sort keys for deterministic hashing
        invoice_json = json.dumps(invoice_copy, sort_keys=True)
        return hashlib.sha256(invoice_json.encode()).hexdigest()

    @staticmethod
    def validate(invoice: Dict) -> tuple[bool, Optional[str]]:
        """Validate invoice schema"""
        required_fields = ['type', 'id', 'from', 'to', 'items', 'total', 'issued_date', 'due_date']

        for field in required_fields:
            if field not in invoice:
                return False, f"Missing required field: {field}"

        if invoice['type'] != 'invoice':
            return False, "Invalid type, must be 'invoice'"

        if not invoice['items']:
            return False, "Invoice must have at least one item"

        # Verify hash if present
        if 'content_hash' in invoice:
            computed_hash = InvoiceSchema.compute_hash(invoice)
            if computed_hash != invoice['content_hash']:
                return False, "Content hash mismatch - invoice may have been tampered with"

        return True, None


class ReceiptSchema:
    """
    Receipt schema for payment confirmation

    Example:
    {
        "type": "receipt",
        "id": "RCP-2025-001",
        "version": "1.0",
        "invoice_id": "INV-2025-001",
        "from": {
            "name": "Soulfra LLC",
            "business_id": "BIZ-123"
        },
        "to": {
            "name": "Customer Name",
            "customer_id": "CUST-456"
        },
        "payment": {
            "amount": 1620.00,
            "currency": "USD",
            "method": "credit_card",
            "transaction_id": "txn_abc123",
            "processor": "stripe",
            "last4": "4242"
        },
        "timestamp": "2025-12-28T10:30:00Z",
        "status": "completed",
        "content_hash": "xyz789...",
        "signature": "uvw012..."
    }
    """

    @staticmethod
    def create(
        receipt_id: str,
        invoice_id: str,
        from_entity: Dict[str, str],
        to_entity: Dict[str, str],
        payment: Dict[str, Any],
        timestamp: Optional[str] = None
    ) -> Dict:
        """Create a new receipt"""

        receipt = {
            "type": "receipt",
            "id": receipt_id,
            "version": "1.0",
            "invoice_id": invoice_id,
            "from": from_entity,
            "to": to_entity,
            "payment": payment,
            "timestamp": timestamp or datetime.utcnow().isoformat(),
            "status": "completed",
            "created_at": datetime.utcnow().isoformat()
        }

        # Add content hash
        receipt['content_hash'] = ReceiptSchema.compute_hash(receipt)

        return receipt

    @staticmethod
    def compute_hash(receipt: Dict) -> str:
        """Compute SHA-256 hash of receipt"""
        receipt_copy = {k: v for k, v in receipt.items() if k not in ['content_hash', 'signature']}
        receipt_json = json.dumps(receipt_copy, sort_keys=True)
        return hashlib.sha256(receipt_json.encode()).hexdigest()

    @staticmethod
    def validate(receipt: Dict) -> tuple[bool, Optional[str]]:
        """Validate receipt schema"""
        required_fields = ['type', 'id', 'payment', 'timestamp']

        for field in required_fields:
            if field not in receipt:
                return False, f"Missing required field: {field}"

        if receipt['type'] != 'receipt':
            return False, "Invalid type, must be 'receipt'"

        # Verify hash if present
        if 'content_hash' in receipt:
            computed_hash = ReceiptSchema.compute_hash(receipt)
            if computed_hash != receipt['content_hash']:
                return False, "Content hash mismatch - receipt may have been tampered with"

        return True, None


class PurchaseOrderSchema:
    """
    Purchase Order schema for procurement

    Example:
    {
        "type": "purchase_order",
        "id": "PO-2025-001",
        "version": "1.0",
        "from": {
            "name": "Customer Name",
            "business_id": "BIZ-456"
        },
        "to": {
            "name": "Soulfra LLC",
            "business_id": "BIZ-123"
        },
        "items": [
            {
                "sku": "PROD-001",
                "description": "Product Name",
                "quantity": 5,
                "unit_price": 100.00,
                "total": 500.00
            }
        ],
        "total": 500.00,
        "currency": "USD",
        "delivery_date": "2026-01-15",
        "delivery_address": "123 Main St, City, State 12345",
        "status": "pending",
        "created_at": "2025-12-28T10:00:00Z",
        "content_hash": "pqr345..."
    }
    """

    @staticmethod
    def create(
        po_id: str,
        from_entity: Dict[str, str],
        to_entity: Dict[str, str],
        items: List[Dict[str, Any]],
        delivery_date: str,
        delivery_address: str,
        currency: str = "USD",
        status: str = "pending"
    ) -> Dict:
        """Create a new purchase order"""

        total = sum(item.get('total', 0) for item in items)

        po = {
            "type": "purchase_order",
            "id": po_id,
            "version": "1.0",
            "from": from_entity,
            "to": to_entity,
            "items": items,
            "total": round(total, 2),
            "currency": currency,
            "delivery_date": delivery_date,
            "delivery_address": delivery_address,
            "status": status,
            "created_at": datetime.utcnow().isoformat()
        }

        # Add content hash
        po['content_hash'] = PurchaseOrderSchema.compute_hash(po)

        return po

    @staticmethod
    def compute_hash(po: Dict) -> str:
        """Compute SHA-256 hash of purchase order"""
        po_copy = {k: v for k, v in po.items() if k not in ['content_hash', 'signature']}
        po_json = json.dumps(po_copy, sort_keys=True)
        return hashlib.sha256(po_json.encode()).hexdigest()

    @staticmethod
    def validate(po: Dict) -> tuple[bool, Optional[str]]:
        """Validate purchase order schema"""
        required_fields = ['type', 'id', 'from', 'to', 'items', 'total', 'delivery_date']

        for field in required_fields:
            if field not in po:
                return False, f"Missing required field: {field}"

        if po['type'] != 'purchase_order':
            return False, "Invalid type, must be 'purchase_order'"

        if not po['items']:
            return False, "Purchase order must have at least one item"

        # Verify hash if present
        if 'content_hash' in po:
            computed_hash = PurchaseOrderSchema.compute_hash(po)
            if computed_hash != po['content_hash']:
                return False, "Content hash mismatch - PO may have been tampered with"

        return True, None


class TransactionSchema:
    """
    Generic transaction schema for financial records

    Example:
    {
        "type": "transaction",
        "id": "TXN-2025-001",
        "version": "1.0",
        "transaction_type": "payment",
        "amount": 1620.00,
        "currency": "USD",
        "from": {
            "name": "Customer Name",
            "account_id": "ACC-456"
        },
        "to": {
            "name": "Soulfra LLC",
            "account_id": "ACC-123"
        },
        "reference": "INV-2025-001",
        "timestamp": "2025-12-28T10:30:00Z",
        "status": "completed",
        "metadata": {
            "processor": "stripe",
            "transaction_id": "txn_abc123"
        },
        "content_hash": "stu678..."
    }
    """

    @staticmethod
    def create(
        txn_id: str,
        transaction_type: str,
        amount: float,
        from_entity: Dict[str, str],
        to_entity: Dict[str, str],
        currency: str = "USD",
        reference: str = "",
        status: str = "completed",
        metadata: Optional[Dict] = None
    ) -> Dict:
        """Create a new transaction"""

        txn = {
            "type": "transaction",
            "id": txn_id,
            "version": "1.0",
            "transaction_type": transaction_type,
            "amount": round(amount, 2),
            "currency": currency,
            "from": from_entity,
            "to": to_entity,
            "reference": reference,
            "timestamp": datetime.utcnow().isoformat(),
            "status": status,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat()
        }

        # Add content hash
        txn['content_hash'] = TransactionSchema.compute_hash(txn)

        return txn

    @staticmethod
    def compute_hash(txn: Dict) -> str:
        """Compute SHA-256 hash of transaction"""
        txn_copy = {k: v for k, v in txn.items() if k not in ['content_hash', 'signature']}
        txn_json = json.dumps(txn_copy, sort_keys=True)
        return hashlib.sha256(txn_json.encode()).hexdigest()

    @staticmethod
    def validate(txn: Dict) -> tuple[bool, Optional[str]]:
        """Validate transaction schema"""
        required_fields = ['type', 'id', 'transaction_type', 'amount', 'from', 'to', 'timestamp']

        for field in required_fields:
            if field not in txn:
                return False, f"Missing required field: {field}"

        if txn['type'] != 'transaction':
            return False, "Invalid type, must be 'transaction'"

        # Verify hash if present
        if 'content_hash' in txn:
            computed_hash = TransactionSchema.compute_hash(txn)
            if computed_hash != txn['content_hash']:
                return False, "Content hash mismatch - transaction may have been tampered with"

        return True, None


# =============================================================================
# HMAC Signature Generation (Bloomberg/Symphony-style)
# =============================================================================

import hmac

def sign_document(document: Dict, secret_key: str) -> str:
    """
    Generate HMAC-SHA256 signature for document

    This provides Bloomberg/Symphony-style cryptographic signing
    """
    # Get document hash
    doc_copy = {k: v for k, v in document.items() if k not in ['signature']}
    doc_json = json.dumps(doc_copy, sort_keys=True)

    # Generate HMAC signature
    signature = hmac.new(
        secret_key.encode(),
        doc_json.encode(),
        hashlib.sha256
    ).hexdigest()

    return signature


def verify_signature(document: Dict, secret_key: str) -> bool:
    """
    Verify HMAC-SHA256 signature on document

    Returns True if signature is valid
    """
    if 'signature' not in document:
        return False

    # Compute expected signature
    expected_signature = sign_document(document, secret_key)

    # Compare signatures (constant-time comparison)
    return hmac.compare_digest(expected_signature, document['signature'])


# =============================================================================
# Schema Registry
# =============================================================================

SCHEMAS = {
    'invoice': InvoiceSchema,
    'receipt': ReceiptSchema,
    'purchase_order': PurchaseOrderSchema,
    'transaction': TransactionSchema
}


def validate_document(document: Dict) -> tuple[bool, Optional[str]]:
    """
    Validate any business document

    Returns: (is_valid, error_message)
    """
    if 'type' not in document:
        return False, "Missing 'type' field"

    doc_type = document['type']

    if doc_type not in SCHEMAS:
        return False, f"Unknown document type: {doc_type}"

    schema_class = SCHEMAS[doc_type]
    return schema_class.validate(document)


def estimate_qr_size(document: Dict) -> int:
    """
    Estimate QR code size needed for document

    Returns number of bytes
    """
    doc_json = json.dumps(document, separators=(',', ':'))
    return len(doc_json.encode('utf-8'))


def get_recommended_qr_version(document: Dict) -> int:
    """
    Get recommended QR code version for document

    QR Code Capacity (with error correction M):
    - V1: ~25 bytes
    - V5: ~350 bytes
    - V10: ~1,700 bytes
    - V20: ~3,700 bytes
    - V40: ~4,296 bytes
    """
    size = estimate_qr_size(document)

    if size <= 25:
        return 1
    elif size <= 350:
        return 5
    elif size <= 1700:
        return 10
    elif size <= 3700:
        return 20
    else:
        return 40  # Maximum


# =============================================================================
# Compression (for large documents)
# =============================================================================

import gzip
import base64

def compress_document(document: Dict) -> str:
    """
    Compress document using gzip and base64 encode

    Useful for fitting large documents in QR codes
    """
    doc_json = json.dumps(document, separators=(',', ':'))
    compressed = gzip.compress(doc_json.encode('utf-8'))
    encoded = base64.b64encode(compressed).decode('ascii')
    return encoded


def decompress_document(compressed: str) -> Dict:
    """
    Decompress and parse document
    """
    decoded = base64.b64decode(compressed.encode('ascii'))
    decompressed = gzip.decompress(decoded)
    document = json.loads(decompressed.decode('utf-8'))
    return document


if __name__ == '__main__':
    # Test invoice creation
    print("=== Testing Invoice Schema ===")

    invoice = InvoiceSchema.create(
        invoice_id="INV-2025-001",
        from_entity={
            "name": "Soulfra LLC",
            "business_id": "BIZ-123",
            "email": "billing@soulfra.com"
        },
        to_entity={
            "name": "Test Customer",
            "customer_id": "CUST-456",
            "email": "customer@example.com"
        },
        items=[
            {
                "description": "Consulting Services",
                "quantity": 10,
                "unit_price": 150.00,
                "total": 1500.00,
                "tax_rate": 0.08
            }
        ],
        issued_date="2025-12-28",
        due_date="2026-01-28"
    )

    print(f"Invoice ID: {invoice['id']}")
    print(f"Total: ${invoice['total']}")
    print(f"Hash: {invoice['content_hash'][:16]}...")

    # Validate
    valid, error = InvoiceSchema.validate(invoice)
    print(f"Valid: {valid}")

    # Check size
    size = estimate_qr_size(invoice)
    version = get_recommended_qr_version(invoice)
    print(f"Size: {size} bytes")
    print(f"Recommended QR version: V{version}")

    # Test signature
    print("\n=== Testing Signature ===")
    secret_key = "test-secret-key-12345"
    invoice['signature'] = sign_document(invoice, secret_key)
    print(f"Signature: {invoice['signature'][:16]}...")

    # Verify signature
    is_valid = verify_signature(invoice, secret_key)
    print(f"Signature valid: {is_valid}")

    # Test compression
    print("\n=== Testing Compression ===")
    compressed = compress_document(invoice)
    print(f"Original size: {size} bytes")
    print(f"Compressed size: {len(compressed)} bytes")
    print(f"Compression ratio: {len(compressed) / size * 100:.1f}%")

    # Decompress
    decompressed = decompress_document(compressed)
    print(f"Decompression successful: {decompressed['id'] == invoice['id']}")
