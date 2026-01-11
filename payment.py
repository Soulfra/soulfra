#!/usr/bin/env python3
"""
THE ONLY STRIPE FILE YOU NEED
Simple $10 payment for StPetePros

Forget:
- Apple Pay
- Multi-gateway (Lightning, BTCPay, etc.)
- Complex payment flows
- All the other payment*.py files

This is it. 50 lines. Credit card → database → done.
"""

import os
import stripe
from flask import Blueprint, request, jsonify, render_template_string
from database import get_db

# Create Flask blueprint
simple_payment = Blueprint('simple_payment', __name__)

# Set Stripe key from environment
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')


@simple_payment.route('/pay', methods=['GET'])
def payment_form():
    """Dead simple payment form - just name, email, card"""

    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Get Listed on StPetePros - $10</title>
        <script src="https://js.stripe.com/v3/"></script>
    </head>
    <body>
        <h1>Get Your Business Listed</h1>
        <h2>$10 One-Time Fee</h2>

        <form id="payment-form">
            <input id="business-name" placeholder="Business Name" required>
            <input id="email" type="email" placeholder="Email" required>
            <input id="phone" placeholder="Phone" required>

            <div id="card-element"></div>
            <div id="error-message"></div>

            <button type="submit">Pay $10</button>
        </form>

        <script>
        const stripe = Stripe('{{ STRIPE_PUB_KEY }}');
        const elements = stripe.elements();
        const card = elements.create('card');
        card.mount('#card-element');

        document.getElementById('payment-form').addEventListener('submit', async (e) => {
            e.preventDefault();

            const {token, error} = await stripe.createToken(card);
            if (error) {
                document.getElementById('error-message').textContent = error.message;
                return;
            }

            // Send to server
            const response = await fetch('/pay', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    token: token.id,
                    business_name: document.getElementById('business-name').value,
                    email: document.getElementById('email').value,
                    phone: document.getElementById('phone').value
                })
            });

            const result = await response.json();
            if (result.success) {
                alert('Payment successful! Check your email for QR code.');
                window.location.href = '/';
            } else {
                document.getElementById('error-message').textContent = result.error;
            }
        });
        </script>
    </body>
    </html>
    '''

    pub_key = os.environ.get('STRIPE_PUBLISHABLE_KEY', 'pk_test_...')
    return render_template_string(html, STRIPE_PUB_KEY=pub_key)


@simple_payment.route('/pay', methods=['POST'])
def process_payment():
    """Charge card, save to database"""

    data = request.json

    try:
        # 1. Charge the card
        charge = stripe.Charge.create(
            amount=1000,  # $10.00 in cents
            currency='usd',
            source=data['token'],
            description=f"StPetePros: {data['business_name']}"
        )

        # 2. Save to database
        db = get_db()
        cursor = db.execute('''
            INSERT INTO professionals (
                business_name, email, phone,
                approval_status, paid, payment_id, created_at
            ) VALUES (?, ?, ?, 'approved', 1, ?, CURRENT_TIMESTAMP)
        ''', (
            data['business_name'],
            data['email'],
            data['phone'],
            charge.id
        ))

        professional_id = cursor.lastrowid
        db.commit()

        # 3. Done
        return jsonify({
            'success': True,
            'professional_id': professional_id
        })

    except stripe.error.CardError as e:
        # Card declined
        return jsonify({'error': str(e)}), 400

    except Exception as e:
        # Other error
        return jsonify({'error': 'Payment failed'}), 500


# That's it. 50 lines. No Apple Pay. No complexity.
