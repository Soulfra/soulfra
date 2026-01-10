#!/usr/bin/env python3
"""
Payment Integrations - Stripe, Square, QuickBooks Connectors

Integrates with payment gateways to automatically generate business QR codes
for invoices, receipts, and transactions.

Features:
- Stripe integration (charges, invoices, subscriptions)
- Square integration (payments, orders)
- QuickBooks integration (invoices, bills, expenses)
- Auto-generate business QR codes from payment data
- Sync to unified_content database
"""

import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from business_schemas import InvoiceSchema, ReceiptSchema, TransactionSchema
from business_qr import BusinessQRGenerator, save_business_qr_to_unified


# =============================================================================
# Configuration
# =============================================================================

# Stripe
STRIPE_ENABLED = os.environ.get('STRIPE_ENABLED', 'false').lower() == 'true'
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')

# Square
SQUARE_ENABLED = os.environ.get('SQUARE_ENABLED', 'false').lower() == 'true'
SQUARE_ACCESS_TOKEN = os.environ.get('SQUARE_ACCESS_TOKEN', '')
SQUARE_LOCATION_ID = os.environ.get('SQUARE_LOCATION_ID', '')

# QuickBooks
QUICKBOOKS_ENABLED = os.environ.get('QUICKBOOKS_ENABLED', 'false').lower() == 'true'
QUICKBOOKS_CLIENT_ID = os.environ.get('QUICKBOOKS_CLIENT_ID', '')
QUICKBOOKS_CLIENT_SECRET = os.environ.get('QUICKBOOKS_CLIENT_SECRET', '')
QUICKBOOKS_REALM_ID = os.environ.get('QUICKBOOKS_REALM_ID', '')

# Business QR Generator
BUSINESS_SECRET_KEY = os.environ.get('BUSINESS_SECRET_KEY', 'default-secret-key-change-in-production')


# =============================================================================
# Stripe Integration
# =============================================================================

class StripeIntegration:
    """
    Stripe payment gateway integration

    Converts Stripe charges/invoices into business QR codes
    """

    def __init__(self):
        if STRIPE_ENABLED:
            try:
                import stripe
                stripe.api_key = STRIPE_SECRET_KEY
                self.stripe = stripe
                self.enabled = True
            except ImportError:
                print("⚠️  Stripe not installed. Run: pip install stripe")
                self.enabled = False
        else:
            self.enabled = False

        self.qr_generator = BusinessQRGenerator(
            secret_key=BUSINESS_SECRET_KEY,
            brand_slug='soulfra'
        )

    def fetch_charge(self, charge_id: str) -> Optional[Dict]:
        """Fetch Stripe charge by ID"""
        if not self.enabled:
            return None

        try:
            charge = self.stripe.Charge.retrieve(charge_id)
            return charge
        except Exception as e:
            print(f"Error fetching Stripe charge: {e}")
            return None

    def charge_to_receipt(self, charge: Dict) -> Dict:
        """
        Convert Stripe charge to receipt schema

        Args:
            charge: Stripe charge object

        Returns:
            Receipt document
        """
        # Extract data
        amount = charge.get('amount', 0) / 100  # Stripe uses cents
        currency = charge.get('currency', 'usd').upper()
        created_timestamp = datetime.fromtimestamp(charge.get('created', 0)).isoformat()

        # Payment method details
        payment_method = charge.get('payment_method_details', {})
        card = payment_method.get('card', {})

        receipt = ReceiptSchema.create(
            receipt_id=f"RCP-STRIPE-{charge.get('id', '')}",
            invoice_id=charge.get('metadata', {}).get('invoice_id', ''),
            from_entity={
                "name": "Soulfra LLC",
                "business_id": "BIZ-SOULFRA",
                "email": "billing@soulfra.com"
            },
            to_entity={
                "name": charge.get('billing_details', {}).get('name', 'Customer'),
                "email": charge.get('billing_details', {}).get('email', ''),
                "customer_id": charge.get('customer', '')
            },
            payment={
                "amount": amount,
                "currency": currency,
                "method": "credit_card",
                "transaction_id": charge.get('id'),
                "processor": "stripe",
                "last4": card.get('last4', ''),
                "brand": card.get('brand', ''),
                "status": charge.get('status', '')
            },
            timestamp=created_timestamp
        )

        return receipt

    def generate_receipt_qr(self, charge_id: str, user_id: Optional[int] = None) -> Optional[int]:
        """
        Fetch Stripe charge and generate receipt QR code

        Returns:
            unified_id of saved receipt
        """
        if not self.enabled:
            print("❌ Stripe integration not enabled")
            return None

        # Fetch charge
        charge = self.fetch_charge(charge_id)
        if not charge:
            return None

        # Convert to receipt
        receipt = self.charge_to_receipt(charge)

        # Generate QR code
        qr_image, qr_metadata = self.qr_generator.generate_receipt_qr(receipt)

        # Save to database
        unified_id = save_business_qr_to_unified(
            document=receipt,
            qr_image=qr_image,
            qr_metadata=qr_metadata,
            user_id=user_id
        )

        print(f"✅ Generated receipt QR for Stripe charge {charge_id}")
        print(f"   Receipt ID: {receipt['id']}")
        print(f"   Amount: ${receipt['payment']['amount']}")
        print(f"   Unified ID: {unified_id}")

        return unified_id

    def webhook_handler(self, payload: Dict, user_id: Optional[int] = None) -> Optional[int]:
        """
        Handle Stripe webhook events

        Automatically generates QR codes when charges succeed

        Args:
            payload: Stripe webhook event data
            user_id: User ID to associate with receipt

        Returns:
            unified_id if receipt was generated
        """
        event_type = payload.get('type')

        if event_type == 'charge.succeeded':
            charge = payload.get('data', {}).get('object', {})
            charge_id = charge.get('id')

            if charge_id:
                return self.generate_receipt_qr(charge_id, user_id=user_id)

        return None


# =============================================================================
# Square Integration
# =============================================================================

class SquareIntegration:
    """
    Square payment gateway integration

    Converts Square payments into business QR codes
    """

    def __init__(self):
        if SQUARE_ENABLED:
            try:
                from square.client import Client
                self.client = Client(
                    access_token=SQUARE_ACCESS_TOKEN,
                    environment='production' if 'prod' in SQUARE_ACCESS_TOKEN else 'sandbox'
                )
                self.enabled = True
            except ImportError:
                print("⚠️  Square SDK not installed. Run: pip install squareup")
                self.enabled = False
        else:
            self.enabled = False

        self.qr_generator = BusinessQRGenerator(
            secret_key=BUSINESS_SECRET_KEY,
            brand_slug='soulfra'
        )

    def fetch_payment(self, payment_id: str) -> Optional[Dict]:
        """Fetch Square payment by ID"""
        if not self.enabled:
            return None

        try:
            result = self.client.payments.get_payment(payment_id)
            if result.is_success():
                return result.body.get('payment')
            else:
                print(f"Error fetching Square payment: {result.errors}")
                return None
        except Exception as e:
            print(f"Error fetching Square payment: {e}")
            return None

    def payment_to_receipt(self, payment: Dict) -> Dict:
        """
        Convert Square payment to receipt schema

        Args:
            payment: Square payment object

        Returns:
            Receipt document
        """
        # Extract data
        amount_money = payment.get('amount_money', {})
        amount = amount_money.get('amount', 0) / 100  # Square uses cents
        currency = amount_money.get('currency', 'USD')

        receipt = ReceiptSchema.create(
            receipt_id=f"RCP-SQUARE-{payment.get('id', '')}",
            invoice_id=payment.get('reference_id', ''),
            from_entity={
                "name": "Soulfra LLC",
                "business_id": "BIZ-SOULFRA",
                "location_id": payment.get('location_id', '')
            },
            to_entity={
                "name": "Customer",
                "customer_id": payment.get('customer_id', '')
            },
            payment={
                "amount": amount,
                "currency": currency,
                "method": "credit_card",
                "transaction_id": payment.get('id'),
                "processor": "square",
                "last4": payment.get('card_details', {}).get('card', {}).get('last_4', ''),
                "status": payment.get('status', '')
            },
            timestamp=payment.get('created_at', datetime.utcnow().isoformat())
        )

        return receipt

    def generate_receipt_qr(self, payment_id: str, user_id: Optional[int] = None) -> Optional[int]:
        """
        Fetch Square payment and generate receipt QR code

        Returns:
            unified_id of saved receipt
        """
        if not self.enabled:
            print("❌ Square integration not enabled")
            return None

        # Fetch payment
        payment = self.fetch_payment(payment_id)
        if not payment:
            return None

        # Convert to receipt
        receipt = self.payment_to_receipt(payment)

        # Generate QR code
        qr_image, qr_metadata = self.qr_generator.generate_receipt_qr(receipt)

        # Save to database
        unified_id = save_business_qr_to_unified(
            document=receipt,
            qr_image=qr_image,
            qr_metadata=qr_metadata,
            user_id=user_id
        )

        print(f"✅ Generated receipt QR for Square payment {payment_id}")
        return unified_id


# =============================================================================
# QuickBooks Integration
# =============================================================================

class QuickBooksIntegration:
    """
    QuickBooks accounting integration

    Syncs invoices/bills from QuickBooks to business QR system
    """

    def __init__(self):
        if QUICKBOOKS_ENABLED:
            try:
                from intuitlib.client import AuthClient
                from intuitlib.enums import Scopes
                self.auth_client = AuthClient(
                    client_id=QUICKBOOKS_CLIENT_ID,
                    client_secret=QUICKBOOKS_CLIENT_SECRET,
                    environment='production',
                    redirect_uri='http://localhost:5001/quickbooks/callback'
                )
                self.realm_id = QUICKBOOKS_REALM_ID
                self.enabled = True
            except ImportError:
                print("⚠️  QuickBooks SDK not installed. Run: pip install intuit-oauth python-quickbooks")
                self.enabled = False
        else:
            self.enabled = False

        self.qr_generator = BusinessQRGenerator(
            secret_key=BUSINESS_SECRET_KEY,
            brand_slug='soulfra'
        )

    def fetch_invoice(self, invoice_id: str, access_token: str) -> Optional[Dict]:
        """
        Fetch QuickBooks invoice by ID

        Args:
            invoice_id: QuickBooks invoice ID
            access_token: OAuth access token

        Returns:
            QuickBooks invoice object
        """
        if not self.enabled:
            return None

        try:
            from quickbooks.objects.invoice import Invoice
            from quickbooks import QuickBooks

            client = QuickBooks(
                auth_client=self.auth_client,
                refresh_token=access_token,
                company_id=self.realm_id
            )

            invoice = Invoice.get(invoice_id, qb=client)
            return invoice
        except Exception as e:
            print(f"Error fetching QuickBooks invoice: {e}")
            return None

    def qb_invoice_to_invoice(self, qb_invoice: Any) -> Dict:
        """
        Convert QuickBooks invoice to our invoice schema

        Args:
            qb_invoice: QuickBooks Invoice object

        Returns:
            Invoice document
        """
        # Extract customer info
        customer = qb_invoice.CustomerRef if hasattr(qb_invoice, 'CustomerRef') else {}

        # Extract line items
        items = []
        if hasattr(qb_invoice, 'Line'):
            for line in qb_invoice.Line:
                if hasattr(line, 'SalesItemLineDetail'):
                    items.append({
                        "description": line.Description if hasattr(line, 'Description') else '',
                        "quantity": line.SalesItemLineDetail.Qty if hasattr(line.SalesItemLineDetail, 'Qty') else 1,
                        "unit_price": float(line.SalesItemLineDetail.UnitPrice) if hasattr(line.SalesItemLineDetail, 'UnitPrice') else 0,
                        "total": float(line.Amount) if hasattr(line, 'Amount') else 0,
                        "tax_rate": 0
                    })

        invoice = InvoiceSchema.create(
            invoice_id=f"INV-QB-{qb_invoice.Id if hasattr(qb_invoice, 'Id') else ''}",
            from_entity={
                "name": "Soulfra LLC",
                "business_id": "BIZ-SOULFRA"
            },
            to_entity={
                "name": customer.name if hasattr(customer, 'name') else 'Customer',
                "customer_id": customer.value if hasattr(customer, 'value') else ''
            },
            items=items,
            issued_date=str(qb_invoice.TxnDate) if hasattr(qb_invoice, 'TxnDate') else datetime.utcnow().date().isoformat(),
            due_date=str(qb_invoice.DueDate) if hasattr(qb_invoice, 'DueDate') else '',
            currency="USD",
            notes=""
        )

        return invoice

    def generate_invoice_qr(self, invoice_id: str, access_token: str, user_id: Optional[int] = None) -> Optional[int]:
        """
        Fetch QuickBooks invoice and generate invoice QR code

        Returns:
            unified_id of saved invoice
        """
        if not self.enabled:
            print("❌ QuickBooks integration not enabled")
            return None

        # Fetch invoice
        qb_invoice = self.fetch_invoice(invoice_id, access_token)
        if not qb_invoice:
            return None

        # Convert to our schema
        invoice = self.qb_invoice_to_invoice(qb_invoice)

        # Generate QR code
        qr_image, qr_metadata = self.qr_generator.generate_invoice_qr(invoice)

        # Save to database
        unified_id = save_business_qr_to_unified(
            document=invoice,
            qr_image=qr_image,
            qr_metadata=qr_metadata,
            user_id=user_id
        )

        print(f"✅ Generated invoice QR for QuickBooks invoice {invoice_id}")
        return unified_id


# =============================================================================
# Unified Payment Manager
# =============================================================================

class PaymentManager:
    """
    Unified payment manager

    Provides single interface for all payment gateways
    """

    def __init__(self):
        self.stripe = StripeIntegration()
        self.square = SquareIntegration()
        self.quickbooks = QuickBooksIntegration()

    def get_enabled_integrations(self) -> List[str]:
        """Get list of enabled payment integrations"""
        integrations = []
        if self.stripe.enabled:
            integrations.append('stripe')
        if self.square.enabled:
            integrations.append('square')
        if self.quickbooks.enabled:
            integrations.append('quickbooks')
        return integrations

    def generate_receipt_from_stripe(self, charge_id: str, user_id: Optional[int] = None) -> Optional[int]:
        """Generate receipt QR from Stripe charge"""
        return self.stripe.generate_receipt_qr(charge_id, user_id=user_id)

    def generate_receipt_from_square(self, payment_id: str, user_id: Optional[int] = None) -> Optional[int]:
        """Generate receipt QR from Square payment"""
        return self.square.generate_receipt_qr(payment_id, user_id=user_id)

    def generate_invoice_from_quickbooks(self, invoice_id: str, access_token: str, user_id: Optional[int] = None) -> Optional[int]:
        """Generate invoice QR from QuickBooks invoice"""
        return self.quickbooks.generate_invoice_qr(invoice_id, access_token, user_id=user_id)

    def handle_stripe_webhook(self, payload: Dict, user_id: Optional[int] = None) -> Optional[int]:
        """Handle Stripe webhook event"""
        return self.stripe.webhook_handler(payload, user_id=user_id)


# =============================================================================
# Demo/Testing
# =============================================================================

if __name__ == '__main__':
    print("=== Payment Integrations Demo ===\n")

    # Initialize payment manager
    manager = PaymentManager()

    # Check enabled integrations
    enabled = manager.get_enabled_integrations()
    print(f"Enabled integrations: {', '.join(enabled) if enabled else 'None (set environment variables)'}")
    print()

    if not enabled:
        print("To enable integrations, set environment variables:")
        print()
        print("Stripe:")
        print("  export STRIPE_ENABLED=true")
        print("  export STRIPE_SECRET_KEY=sk_test_...")
        print()
        print("Square:")
        print("  export SQUARE_ENABLED=true")
        print("  export SQUARE_ACCESS_TOKEN=sq0atp-...")
        print("  export SQUARE_LOCATION_ID=...")
        print()
        print("QuickBooks:")
        print("  export QUICKBOOKS_ENABLED=true")
        print("  export QUICKBOOKS_CLIENT_ID=...")
        print("  export QUICKBOOKS_CLIENT_SECRET=...")
        print("  export QUICKBOOKS_REALM_ID=...")
        print()

    # Test creating a mock receipt (without actual API calls)
    print("=== Creating Mock Receipt ===")

    from business_schemas import ReceiptSchema

    mock_receipt = ReceiptSchema.create(
        receipt_id="RCP-DEMO-001",
        invoice_id="INV-DEMO-001",
        from_entity={
            "name": "Soulfra LLC",
            "business_id": "BIZ-SOULFRA"
        },
        to_entity={
            "name": "Demo Customer",
            "customer_id": "CUST-DEMO"
        },
        payment={
            "amount": 99.99,
            "currency": "USD",
            "method": "credit_card",
            "transaction_id": "demo_txn_123",
            "processor": "demo",
            "last4": "4242"
        }
    )

    print(f"Receipt ID: {mock_receipt['id']}")
    print(f"Amount: ${mock_receipt['payment']['amount']}")
    print(f"Hash: {mock_receipt['content_hash'][:16]}...")
    print()

    print("✅ Payment integrations module ready!")
    print("   - Stripe: {'✅' if manager.stripe.enabled else '❌'}")
    print("   - Square: {'✅' if manager.square.enabled else '❌'}")
    print("   - QuickBooks: {'✅' if manager.quickbooks.enabled else '❌'}")
