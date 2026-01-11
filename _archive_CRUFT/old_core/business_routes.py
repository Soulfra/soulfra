#!/usr/bin/env python3
"""
Business Routes - Flask Routes for Business Dashboard

Routes for managing business documents (invoices, receipts, POs) with QR codes

Routes:
- GET /business - Business dashboard
- POST /api/business/invoice - Create invoice with QR
- POST /api/business/receipt - Create receipt with QR
- POST /api/business/purchase-order - Create purchase order with QR
- GET /business/view/<unified_id> - View business document
- GET /api/business/documents - List all business documents
- POST /api/business/stripe/webhook - Stripe webhook handler
- GET /api/business/qr/<unified_id> - Download QR code
"""

from flask import Blueprint, render_template, request, jsonify, session, send_file
from typing import Dict, Optional
import json
from io import BytesIO
import os

from business_schemas import InvoiceSchema, ReceiptSchema, PurchaseOrderSchema, TransactionSchema
from business_qr import BusinessQRGenerator, save_business_qr_to_unified
from payment_integrations import PaymentManager
from database import get_db


business_bp = Blueprint('business', __name__)

# Initialize business QR generator
BUSINESS_SECRET_KEY = os.environ.get('BUSINESS_SECRET_KEY', 'default-secret-key-change-in-production')
qr_generator = BusinessQRGenerator(secret_key=BUSINESS_SECRET_KEY, brand_slug='soulfra')

# Initialize payment manager
payment_manager = PaymentManager()


def register_business_routes(app):
    """Register business blueprint with Flask app"""
    app.register_blueprint(business_bp)
    print("✅ Registered business routes")


# =============================================================================
# Dashboard Routes
# =============================================================================

@business_bp.route('/business')
def business_dashboard():
    """
    Business dashboard - main interface for invoice/receipt management

    Shows:
    - Recent invoices
    - Recent receipts
    - Payment integrations status
    - Quick actions
    """
    user_id = session.get('user_id')

    # Get recent business documents
    conn = get_db()
    conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

    documents = conn.execute('''
        SELECT * FROM unified_content
        WHERE content_type LIKE 'business_%'
        ORDER BY created_at DESC
        LIMIT 20
    ''').fetchall()

    conn.close()

    # Parse metadata
    for doc in documents:
        if doc.get('metadata'):
            doc['metadata_parsed'] = json.loads(doc['metadata'])

    # Get payment integration status
    enabled_integrations = payment_manager.get_enabled_integrations()

    return render_template('business_dashboard.html',
        user_id=user_id,
        documents=documents,
        integrations=enabled_integrations,
        total_documents=len(documents)
    )


@business_bp.route('/business/view/<int:unified_id>')
def view_business_document(unified_id):
    """
    View business document with QR code

    Shows full document details with embedded QR code
    """
    conn = get_db()
    conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

    # Get document
    document = conn.execute('''
        SELECT * FROM unified_content WHERE id = ?
    ''', (unified_id,)).fetchone()

    if not document:
        conn.close()
        return "Document not found", 404

    # Get QR code
    qr_code = conn.execute('''
        SELECT * FROM vanity_qr_codes WHERE short_code = ?
    ''', (f"biz-{unified_id}",)).fetchone()

    conn.close()

    # Parse content JSON
    content = json.loads(document['content']) if document.get('content') else {}

    # Parse metadata
    metadata = json.loads(document['metadata']) if document.get('metadata') else {}

    return render_template('business_view.html',
        document=document,
        content=content,
        metadata=metadata,
        qr_code=qr_code
    )


# =============================================================================
# Invoice API
# =============================================================================

@business_bp.route('/api/business/invoice', methods=['POST'])
def create_invoice():
    """
    Create invoice with QR code

    POST body:
    {
        "invoice_id": "INV-2025-001",
        "from_entity": {
            "name": "Soulfra LLC",
            "business_id": "BIZ-123",
            "email": "billing@soulfra.com"
        },
        "to_entity": {
            "name": "Customer Name",
            "customer_id": "CUST-456",
            "email": "customer@example.com"
        },
        "items": [
            {
                "description": "Service",
                "quantity": 1,
                "unit_price": 100.00,
                "total": 100.00,
                "tax_rate": 0.08
            }
        ],
        "issued_date": "2025-12-28",
        "due_date": "2026-01-28",
        "payment_terms": "Net 30",
        "notes": "Thank you"
    }

    Returns:
    {
        "success": true,
        "unified_id": 123,
        "invoice_id": "INV-2025-001",
        "total": 108.00,
        "content_hash": "abc123...",
        "qr_metadata": {...}
    }
    """
    user_id = session.get('user_id')
    data = request.get_json()

    try:
        # Create invoice
        invoice = InvoiceSchema.create(
            invoice_id=data.get('invoice_id'),
            from_entity=data.get('from_entity'),
            to_entity=data.get('to_entity'),
            items=data.get('items'),
            issued_date=data.get('issued_date'),
            due_date=data.get('due_date'),
            currency=data.get('currency', 'USD'),
            payment_terms=data.get('payment_terms', 'Net 30'),
            notes=data.get('notes', '')
        )

        # Generate QR code
        qr_image, qr_metadata = qr_generator.generate_invoice_qr(invoice)

        # Save to database
        unified_id = save_business_qr_to_unified(
            document=invoice,
            qr_image=qr_image,
            qr_metadata=qr_metadata,
            user_id=user_id
        )

        return jsonify({
            'success': True,
            'unified_id': unified_id,
            'invoice_id': invoice['id'],
            'total': invoice['total'],
            'content_hash': invoice['content_hash'],
            'qr_metadata': qr_metadata
        })

    except Exception as e:
        print(f"Error creating invoice: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# Receipt API
# =============================================================================

@business_bp.route('/api/business/receipt', methods=['POST'])
def create_receipt():
    """
    Create receipt with QR code

    POST body:
    {
        "receipt_id": "RCP-2025-001",
        "invoice_id": "INV-2025-001",
        "from_entity": {...},
        "to_entity": {...},
        "payment": {
            "amount": 108.00,
            "currency": "USD",
            "method": "credit_card",
            "transaction_id": "txn_123",
            "processor": "stripe",
            "last4": "4242"
        }
    }
    """
    user_id = session.get('user_id')
    data = request.get_json()

    try:
        # Create receipt
        receipt = ReceiptSchema.create(
            receipt_id=data.get('receipt_id'),
            invoice_id=data.get('invoice_id'),
            from_entity=data.get('from_entity'),
            to_entity=data.get('to_entity'),
            payment=data.get('payment')
        )

        # Generate QR code
        qr_image, qr_metadata = qr_generator.generate_receipt_qr(receipt)

        # Save to database
        unified_id = save_business_qr_to_unified(
            document=receipt,
            qr_image=qr_image,
            qr_metadata=qr_metadata,
            user_id=user_id
        )

        return jsonify({
            'success': True,
            'unified_id': unified_id,
            'receipt_id': receipt['id'],
            'amount': receipt['payment']['amount'],
            'content_hash': receipt['content_hash'],
            'qr_metadata': qr_metadata
        })

    except Exception as e:
        print(f"Error creating receipt: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# Purchase Order API
# =============================================================================

@business_bp.route('/api/business/purchase-order', methods=['POST'])
def create_purchase_order():
    """
    Create purchase order with QR code

    POST body:
    {
        "po_id": "PO-2025-001",
        "from_entity": {...},
        "to_entity": {...},
        "items": [...],
        "delivery_date": "2026-01-15",
        "delivery_address": "123 Main St"
    }
    """
    user_id = session.get('user_id')
    data = request.get_json()

    try:
        # Create PO
        po = PurchaseOrderSchema.create(
            po_id=data.get('po_id'),
            from_entity=data.get('from_entity'),
            to_entity=data.get('to_entity'),
            items=data.get('items'),
            delivery_date=data.get('delivery_date'),
            delivery_address=data.get('delivery_address'),
            currency=data.get('currency', 'USD')
        )

        # Generate QR code
        qr_image, qr_metadata = qr_generator.generate_purchase_order_qr(po)

        # Save to database
        unified_id = save_business_qr_to_unified(
            document=po,
            qr_image=qr_image,
            qr_metadata=qr_metadata,
            user_id=user_id
        )

        return jsonify({
            'success': True,
            'unified_id': unified_id,
            'po_id': po['id'],
            'total': po['total'],
            'content_hash': po['content_hash'],
            'qr_metadata': qr_metadata
        })

    except Exception as e:
        print(f"Error creating purchase order: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# Document List API
# =============================================================================

@business_bp.route('/api/business/documents')
def list_documents():
    """
    Get all business documents

    Query params:
    - type: Filter by document type (invoice, receipt, purchase_order)
    - limit: Number of documents to return (default 50)

    Returns:
    {
        "success": true,
        "documents": [...]
    }
    """
    doc_type = request.args.get('type', '')
    limit = request.args.get('limit', 50, type=int)

    conn = get_db()
    conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

    if doc_type:
        documents = conn.execute('''
            SELECT * FROM unified_content
            WHERE content_type = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (f'business_{doc_type}', limit)).fetchall()
    else:
        documents = conn.execute('''
            SELECT * FROM unified_content
            WHERE content_type LIKE 'business_%'
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,)).fetchall()

    conn.close()

    # Parse metadata
    for doc in documents:
        if doc.get('metadata'):
            doc['metadata_parsed'] = json.loads(doc['metadata'])

    return jsonify({
        'success': True,
        'documents': documents
    })


# =============================================================================
# QR Code Download
# =============================================================================

@business_bp.route('/api/business/qr/<int:unified_id>')
def download_qr(unified_id):
    """
    Download QR code image

    Returns PNG image
    """
    conn = get_db()

    # Get QR code
    qr_data = conn.execute('''
        SELECT qr_image FROM vanity_qr_codes WHERE short_code = ?
    ''', (f"biz-{unified_id}",)).fetchone()

    conn.close()

    if not qr_data:
        return "QR code not found", 404

    qr_image = qr_data[0]

    return send_file(
        BytesIO(qr_image),
        mimetype='image/png',
        as_attachment=True,
        download_name=f'business_qr_{unified_id}.png'
    )


# =============================================================================
# Payment Integration Webhooks
# =============================================================================

@business_bp.route('/api/business/stripe/webhook', methods=['POST'])
def stripe_webhook():
    """
    Stripe webhook handler

    Automatically generates receipts when payments succeed
    """
    payload = request.get_json()

    try:
        unified_id = payment_manager.handle_stripe_webhook(payload)

        if unified_id:
            return jsonify({
                'success': True,
                'unified_id': unified_id,
                'message': 'Receipt generated successfully'
            })
        else:
            return jsonify({
                'success': True,
                'message': 'Event processed (no receipt generated)'
            })

    except Exception as e:
        print(f"Error handling Stripe webhook: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@business_bp.route('/api/business/square/webhook', methods=['POST'])
def square_webhook():
    """
    Square webhook handler

    (To be implemented based on Square webhook events)
    """
    payload = request.get_json()

    # TODO: Implement Square webhook handling
    print(f"Received Square webhook: {payload.get('type')}")

    return jsonify({'success': True})


# =============================================================================
# Stats API
# =============================================================================

@business_bp.route('/api/business/stats')
def get_business_stats():
    """
    Get business document statistics

    Returns:
    {
        "total_invoices": 10,
        "total_receipts": 15,
        "total_purchase_orders": 5,
        "total_revenue": 50000.00
    }
    """
    conn = get_db()

    # Count documents by type
    invoice_count = conn.execute('''
        SELECT COUNT(*) FROM unified_content WHERE content_type = 'business_invoice'
    ''').fetchone()[0]

    receipt_count = conn.execute('''
        SELECT COUNT(*) FROM unified_content WHERE content_type = 'business_receipt'
    ''').fetchone()[0]

    po_count = conn.execute('''
        SELECT COUNT(*) FROM unified_content WHERE content_type = 'business_purchase_order'
    ''').fetchone()[0]

    # Calculate total revenue (from receipts)
    receipts = conn.execute('''
        SELECT content FROM unified_content WHERE content_type = 'business_receipt'
    ''').fetchall()

    total_revenue = 0
    for receipt_row in receipts:
        receipt = json.loads(receipt_row[0])
        total_revenue += receipt.get('payment', {}).get('amount', 0)

    conn.close()

    return jsonify({
        'success': True,
        'stats': {
            'total_invoices': invoice_count,
            'total_receipts': receipt_count,
            'total_purchase_orders': po_count,
            'total_revenue': round(total_revenue, 2)
        }
    })


# =============================================================================
# Integration Status
# =============================================================================

@business_bp.route('/api/business/integrations')
def get_integration_status():
    """
    Get payment integration status

    Returns:
    {
        "integrations": {
            "stripe": true,
            "square": false,
            "quickbooks": false
        }
    }
    """
    enabled = payment_manager.get_enabled_integrations()

    return jsonify({
        'success': True,
        'integrations': {
            'stripe': 'stripe' in enabled,
            'square': 'square' in enabled,
            'quickbooks': 'quickbooks' in enabled
        }
    })


if __name__ == '__main__':
    print("Business routes module")
    print("Import this module and call register_business_routes(app)")
