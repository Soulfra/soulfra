#!/usr/bin/env python3
"""
QR Event System - Event-Driven Automated QR Generation

This module handles automatic QR code generation triggered by events:
- Payment received → Auto-generate receipt QR
- Invoice created → Auto-generate invoice QR
- Order shipped → Auto-generate tracking QR
- Customer check-in → Auto-generate loyalty QR
- Product scanned → Auto-update inventory QR

Event Sources:
- Stripe webhooks
- Square webhooks
- QuickBooks webhooks
- Internal app events
- Scheduled jobs

Usage:
    # Register event handlers
    from qr_events import QREventHandler

    handler = QREventHandler()
    handler.on('payment.succeeded', auto_generate_receipt)
    handler.on('invoice.created', auto_generate_invoice)

    # Process webhook
    handler.process_webhook('stripe', webhook_data)
"""

from typing import Dict, Callable, Optional, List, Any
from datetime import datetime
import json
import os
from enum import Enum

from qr_unified import QRFactory
from business_schemas import InvoiceSchema, ReceiptSchema
from database import get_db


# =============================================================================
# Event Types
# =============================================================================

class EventType(Enum):
    """Standard event types across all systems"""
    # Payment events
    PAYMENT_RECEIVED = 'payment.received'
    PAYMENT_FAILED = 'payment.failed'
    PAYMENT_REFUNDED = 'payment.refunded'

    # Invoice events
    INVOICE_CREATED = 'invoice.created'
    INVOICE_SENT = 'invoice.sent'
    INVOICE_PAID = 'invoice.paid'
    INVOICE_OVERDUE = 'invoice.overdue'

    # Order events
    ORDER_PLACED = 'order.placed'
    ORDER_SHIPPED = 'order.shipped'
    ORDER_DELIVERED = 'order.delivered'
    ORDER_CANCELLED = 'order.cancelled'

    # Customer events
    CUSTOMER_CREATED = 'customer.created'
    CUSTOMER_CHECKIN = 'customer.checkin'
    CUSTOMER_CHECKOUT = 'customer.checkout'

    # Product events
    PRODUCT_CREATED = 'product.created'
    PRODUCT_SCANNED = 'product.scanned'
    PRODUCT_LOW_STOCK = 'product.low_stock'

    # Custom events
    CUSTOM = 'custom'


# =============================================================================
# Event Handler
# =============================================================================

class QREventHandler:
    """
    Event-driven QR code generation system

    Listens for events and automatically generates QR codes
    """

    def __init__(self, secret_key: Optional[str] = None, brand: str = 'soulfra'):
        """
        Initialize event handler

        Args:
            secret_key: Secret key for cryptographic signatures
            brand: Default brand slug
        """
        self.secret_key = secret_key or os.environ.get('BUSINESS_SECRET_KEY', 'default-secret-key')
        self.brand = brand
        self.handlers: Dict[str, List[Callable]] = {}

        # Register default handlers
        self._register_defaults()

    def _register_defaults(self):
        """Register default event handlers"""
        self.on(EventType.PAYMENT_RECEIVED.value, self.handle_payment_received)
        self.on(EventType.INVOICE_CREATED.value, self.handle_invoice_created)
        self.on(EventType.ORDER_SHIPPED.value, self.handle_order_shipped)
        self.on(EventType.CUSTOMER_CHECKIN.value, self.handle_customer_checkin)

    def on(self, event_type: str, handler: Callable):
        """
        Register event handler

        Args:
            event_type: Event type (e.g., 'payment.received')
            handler: Callback function(event_data) -> None
        """
        if event_type not in self.handlers:
            self.handlers[event_type] = []

        self.handlers[event_type].append(handler)

    def emit(self, event_type: str, event_data: Dict) -> List[Any]:
        """
        Emit event and trigger handlers

        Args:
            event_type: Event type
            event_data: Event payload

        Returns:
            List of handler results
        """
        if event_type not in self.handlers:
            print(f"⚠️  No handlers registered for event: {event_type}")
            return []

        results = []
        for handler in self.handlers[event_type]:
            try:
                result = handler(event_data)
                results.append(result)
            except Exception as e:
                print(f"❌ Error in handler for {event_type}: {e}")
                results.append(None)

        return results

    # =========================================================================
    # Webhook Processing
    # =========================================================================

    def process_webhook(self, provider: str, webhook_data: Dict) -> List[Any]:
        """
        Process webhook from payment provider

        Args:
            provider: 'stripe', 'square', 'quickbooks', etc.
            webhook_data: Raw webhook payload

        Returns:
            List of handler results
        """
        if provider == 'stripe':
            return self._process_stripe_webhook(webhook_data)
        elif provider == 'square':
            return self._process_square_webhook(webhook_data)
        elif provider == 'quickbooks':
            return self._process_quickbooks_webhook(webhook_data)
        else:
            print(f"⚠️  Unknown provider: {provider}")
            return []

    def _process_stripe_webhook(self, data: Dict) -> List[Any]:
        """Process Stripe webhook"""
        event_type = data.get('type', '')

        # Map Stripe events to our events
        if event_type == 'payment_intent.succeeded':
            return self.emit(EventType.PAYMENT_RECEIVED.value, data)
        elif event_type == 'payment_intent.payment_failed':
            return self.emit(EventType.PAYMENT_FAILED.value, data)
        elif event_type == 'charge.refunded':
            return self.emit(EventType.PAYMENT_REFUNDED.value, data)
        elif event_type == 'invoice.created':
            return self.emit(EventType.INVOICE_CREATED.value, data)
        elif event_type == 'invoice.paid':
            return self.emit(EventType.INVOICE_PAID.value, data)
        else:
            print(f"⚠️  Unhandled Stripe event: {event_type}")
            return []

    def _process_square_webhook(self, data: Dict) -> List[Any]:
        """Process Square webhook"""
        event_type = data.get('type', '')

        # Map Square events
        if event_type == 'payment.updated':
            payment = data.get('data', {}).get('object', {}).get('payment', {})
            if payment.get('status') == 'COMPLETED':
                return self.emit(EventType.PAYMENT_RECEIVED.value, data)

        return []

    def _process_quickbooks_webhook(self, data: Dict) -> List[Any]:
        """Process QuickBooks webhook"""
        entity_name = data.get('eventNotifications', [{}])[0].get('dataChangeEvent', {}).get('entities', [{}])[0].get('name', '')

        if entity_name == 'Invoice':
            return self.emit(EventType.INVOICE_CREATED.value, data)

        return []

    # =========================================================================
    # Default Event Handlers
    # =========================================================================

    def handle_payment_received(self, event_data: Dict) -> Dict:
        """
        Auto-generate receipt QR when payment received

        Args:
            event_data: Payment event data

        Returns:
            Receipt metadata
        """
        print(f"✅ Payment received event triggered")

        # Extract payment info
        payment_amount = self._extract_payment_amount(event_data)
        transaction_id = self._extract_transaction_id(event_data)
        customer_email = self._extract_customer_email(event_data)

        # Create receipt
        receipt = ReceiptSchema.create(
            receipt_id=f"REC-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            from_entity={
                'name': 'Soulfra LLC',
                'business_id': 'BIZ-123',
                'email': 'billing@soulfra.com'
            },
            to_entity={
                'name': 'Customer',
                'email': customer_email
            },
            payment={
                'method': 'credit_card',
                'amount': payment_amount,
                'currency': 'USD',
                'transaction_id': transaction_id,
                'processor': 'stripe',
                'last4': '4242'
            },
            timestamp=datetime.now().isoformat()
        )

        # Generate QR
        qr_bytes, metadata = QRFactory.create('receipt', data=receipt, brand=self.brand)

        # TODO: Email QR to customer
        print(f"📧 Would email receipt QR to {customer_email}")

        return metadata

    def handle_invoice_created(self, event_data: Dict) -> Dict:
        """
        Auto-generate invoice QR when invoice created

        Args:
            event_data: Invoice event data

        Returns:
            Invoice metadata
        """
        print(f"✅ Invoice created event triggered")

        # Extract invoice info
        invoice_id = self._extract_invoice_id(event_data)
        customer_email = self._extract_customer_email(event_data)

        # Invoice should already exist in database
        # Just generate QR and attach to invoice

        conn = get_db()
        invoice_doc = conn.execute(
            'SELECT * FROM unified_content WHERE title = ? AND content_type = ?',
            (invoice_id, 'business_invoice')
        ).fetchone()

        if not invoice_doc:
            print(f"⚠️  Invoice {invoice_id} not found in database")
            return {}

        invoice_data = json.loads(invoice_doc[2])  # content column

        # Generate QR
        qr_bytes, metadata = QRFactory.create('invoice', data=invoice_data, brand=self.brand)

        print(f"📧 Would email invoice QR to {customer_email}")

        return metadata

    def handle_order_shipped(self, event_data: Dict) -> Dict:
        """
        Auto-generate tracking QR when order shipped

        Args:
            event_data: Order event data

        Returns:
            Tracking QR metadata
        """
        print(f"✅ Order shipped event triggered")

        # Extract order info
        order_id = event_data.get('order_id')
        tracking_number = event_data.get('tracking_number')
        carrier = event_data.get('carrier', 'USPS')

        # Generate tracking URL
        tracking_url = f"https://tools.usps.com/go/TrackConfirmAction?tLabels={tracking_number}"

        # Generate QR
        qr_bytes, metadata = QRFactory.create('vanity', url=tracking_url, brand=self.brand)

        print(f"📦 Generated tracking QR for order {order_id}")

        return metadata

    def handle_customer_checkin(self, event_data: Dict) -> Dict:
        """
        Auto-generate loyalty QR when customer checks in

        Args:
            event_data: Check-in event data

        Returns:
            Loyalty QR metadata
        """
        print(f"✅ Customer check-in event triggered")

        customer_id = event_data.get('customer_id')
        location = event_data.get('location')

        # Generate loyalty points QR
        loyalty_data = {
            'customer_id': customer_id,
            'location': location,
            'points': 10,
            'timestamp': datetime.now().isoformat()
        }

        qr_bytes, metadata = QRFactory.create('simple', data=loyalty_data)

        print(f"🎁 Generated loyalty QR for customer {customer_id}")

        return metadata

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _extract_payment_amount(self, event_data: Dict) -> float:
        """Extract payment amount from webhook"""
        # Stripe
        if 'payment_intent' in event_data:
            return event_data.get('payment_intent', {}).get('amount', 0) / 100.0

        # Square
        if 'data' in event_data:
            return float(event_data.get('data', {}).get('object', {}).get('payment', {}).get('amount_money', {}).get('amount', 0)) / 100.0

        return 0.0

    def _extract_transaction_id(self, event_data: Dict) -> str:
        """Extract transaction ID from webhook"""
        # Stripe
        if 'payment_intent' in event_data:
            return event_data.get('payment_intent', {}).get('id', 'UNKNOWN')

        # Square
        if 'data' in event_data:
            return event_data.get('data', {}).get('object', {}).get('payment', {}).get('id', 'UNKNOWN')

        return 'UNKNOWN'

    def _extract_customer_email(self, event_data: Dict) -> str:
        """Extract customer email from webhook"""
        # Stripe
        if 'payment_intent' in event_data:
            return event_data.get('payment_intent', {}).get('receipt_email', 'noreply@example.com')

        # Square
        if 'data' in event_data:
            return event_data.get('data', {}).get('object', {}).get('payment', {}).get('buyer_email_address', 'noreply@example.com')

        return 'noreply@example.com'

    def _extract_invoice_id(self, event_data: Dict) -> str:
        """Extract invoice ID from webhook"""
        # Stripe
        if 'invoice' in event_data:
            return event_data.get('invoice', {}).get('id', 'UNKNOWN')

        # QuickBooks
        if 'eventNotifications' in event_data:
            return event_data.get('eventNotifications', [{}])[0].get('dataChangeEvent', {}).get('entities', [{}])[0].get('id', 'UNKNOWN')

        return 'UNKNOWN'


# =============================================================================
# Scheduled Jobs
# =============================================================================

class QRScheduler:
    """
    Scheduled QR generation jobs

    Example:
        scheduler = QRScheduler()
        scheduler.daily('generate_daily_reports', generate_report_qrs)
    """

    def __init__(self):
        self.jobs: Dict[str, Callable] = {}

    def daily(self, job_name: str, job_func: Callable):
        """Register daily job"""
        self.jobs[job_name] = job_func
        print(f"✅ Registered daily job: {job_name}")

    def hourly(self, job_name: str, job_func: Callable):
        """Register hourly job"""
        self.jobs[job_name] = job_func
        print(f"✅ Registered hourly job: {job_name}")

    def run_job(self, job_name: str):
        """Run specific job"""
        if job_name not in self.jobs:
            print(f"⚠️  Job not found: {job_name}")
            return

        try:
            self.jobs[job_name]()
            print(f"✅ Ran job: {job_name}")
        except Exception as e:
            print(f"❌ Error running job {job_name}: {e}")


# =============================================================================
# Example Usage
# =============================================================================

if __name__ == '__main__':
    # Initialize handler
    handler = QREventHandler()

    # Example 1: Process Stripe webhook
    stripe_webhook = {
        'type': 'payment_intent.succeeded',
        'payment_intent': {
            'id': 'pi_1234567890',
            'amount': 10000,  # $100.00 in cents
            'receipt_email': 'customer@example.com'
        }
    }

    print("\n=== Processing Stripe Webhook ===")
    results = handler.process_webhook('stripe', stripe_webhook)
    print(f"Results: {results}")

    # Example 2: Emit custom event
    print("\n=== Emitting Custom Event ===")
    handler.on('product.scanned', lambda data: print(f"Product {data['product_id']} scanned!"))
    handler.emit('product.scanned', {'product_id': 'PROD-123'})

    # Example 3: Scheduled job
    print("\n=== Scheduling Job ===")
    scheduler = QRScheduler()

    def generate_daily_report_qrs():
        print("Generating daily report QR codes...")
        # TODO: Generate QR codes for daily reports

    scheduler.daily('daily_reports', generate_daily_report_qrs)
    scheduler.run_job('daily_reports')
