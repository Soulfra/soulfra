#!/usr/bin/env python3
"""
Payment Routes - Revenue Distribution System

Monthly revenue distribution based on ownership percentages
Integration with Stripe Connect for payouts

Routes:
- /admin/revenue/domains - View domain revenue
- /admin/revenue/calculate - Calculate monthly payouts
- /admin/revenue/payout - Execute payouts
- /admin/revenue/history - Payout history
- /user/earnings - User earnings dashboard
- /user/payout-settings - User payout preferences

Payment methods:
- Stripe Connect (US, international)
- ACH/Wire transfer (US banks)
- Cryptocurrency (offshore-friendly)
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from database import get_db
from ownership_ledger import (
    get_domain_ownership_distribution,
    calculate_revenue_share,
    get_user_ownership_summary
)
from datetime import datetime, timedelta
import json

# Blueprint for payment routes
payments = Blueprint('payments', __name__)


# ==============================================================================
# ADMIN - REVENUE MANAGEMENT
# ==============================================================================

@payments.route('/admin/revenue/domains')
def admin_domain_revenue():
    """
    Admin view of domain revenue

    Shows revenue per domain, ownership distribution
    Requires admin login
    """

    if not session.get('is_admin'):
        return redirect(url_for('tier_0.homepage'))

    conn = get_db()

    # Get all domains with revenue data
    domains = conn.execute('''
        SELECT
            d.id,
            d.domain_name,
            d.category,
            COUNT(DISTINCT do.user_id) as owner_count,
            SUM(do.ownership_percentage) as total_ownership
        FROM domains d
        LEFT JOIN domain_ownership do ON d.id = do.domain_id
        GROUP BY d.id
        ORDER BY d.domain_name
    ''').fetchall()

    conn.close()

    # Get revenue for each domain (would come from analytics)
    # For now, placeholder data structure
    domain_revenue = []
    for domain in domains:
        # In production, fetch from Google Analytics, Stripe, etc.
        revenue_data = {
            'domain_id': domain['id'],
            'domain_name': domain['domain_name'],
            'owner_count': domain['owner_count'],
            'total_ownership': domain['total_ownership'] or 0,
            'monthly_revenue': 0.0,  # Placeholder
            'ytd_revenue': 0.0  # Placeholder
        }
        domain_revenue.append(revenue_data)

    return render_template('admin/revenue_domains.html',
                          domains=domain_revenue)


@payments.route('/admin/revenue/calculate', methods=['GET', 'POST'])
def admin_calculate_payouts():
    """
    Calculate monthly payouts for all domains

    Admin enters revenue per domain
    System calculates payouts based on ownership
    """

    if not session.get('is_admin'):
        return redirect(url_for('tier_0.homepage'))

    if request.method == 'GET':
        # Show form to enter revenue
        conn = get_db()
        domains = conn.execute('SELECT id, domain_name FROM domains ORDER BY domain_name').fetchall()
        conn.close()

        return render_template('admin/revenue_calculate.html', domains=domains)

    # POST - Calculate payouts
    revenue_data = request.form.to_dict()

    # revenue_data = {'domain_1': '10000.00', 'domain_2': '5000.00', ...}
    payouts_by_domain = {}

    for key, value in revenue_data.items():
        if key.startswith('domain_'):
            domain_id = int(key.split('_')[1])
            monthly_revenue = float(value) if value else 0.0

            if monthly_revenue > 0:
                payouts = calculate_revenue_share(domain_id, monthly_revenue)
                payouts_by_domain[domain_id] = {
                    'monthly_revenue': monthly_revenue,
                    'payouts': payouts
                }

    # Aggregate payouts per user (across all domains)
    user_totals = {}
    for domain_id, data in payouts_by_domain.items():
        for payout in data['payouts']:
            user_id = payout['user_id']
            if user_id not in user_totals:
                user_totals[user_id] = {
                    'user_id': user_id,
                    'username': payout['username'],
                    'total_payout': 0.0,
                    'domains': []
                }

            user_totals[user_id]['total_payout'] += payout['payout']
            user_totals[user_id]['domains'].append({
                'domain_id': domain_id,
                'payout': payout['payout']
            })

    # Sort by total payout (descending)
    sorted_payouts = sorted(user_totals.values(), key=lambda x: x['total_payout'], reverse=True)

    return render_template('admin/revenue_payouts.html',
                          payouts=sorted_payouts,
                          payouts_by_domain=payouts_by_domain)


@payments.route('/admin/revenue/payout', methods=['POST'])
def admin_execute_payouts():
    """
    Execute payouts via Stripe Connect

    Creates payout records in database
    Triggers Stripe transfers
    Generates 1099 data for US users
    """

    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 403

    # Get payout data from form
    payout_data = request.get_json()

    # payout_data = [
    #     {'user_id': 15, 'amount': 3187.50, 'domain_ids': [1, 2, 3]},
    #     ...
    # ]

    conn = get_db()

    payout_records = []
    total_paid = 0.0

    for payout in payout_data:
        user_id = payout['user_id']
        amount = payout['amount']
        domain_ids = payout['domain_ids']

        # Create payout record
        cursor = conn.execute('''
            INSERT INTO payouts (
                user_id,
                amount,
                payout_date,
                payout_method,
                status,
                domains
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            amount,
            datetime.utcnow(),
            'stripe_connect',  # or 'wire', 'crypto'
            'pending',
            json.dumps(domain_ids)
        ))

        payout_id = cursor.lastrowid
        payout_records.append(payout_id)
        total_paid += amount

        # TODO: Trigger Stripe Connect transfer
        # stripe.Transfer.create(
        #     amount=int(amount * 100),  # cents
        #     currency='usd',
        #     destination=user_stripe_account_id,
        #     transfer_group=f'monthly_payout_{datetime.now().strftime("%Y%m")}'
        # )

    conn.commit()
    conn.close()

    return jsonify({
        'success': True,
        'payout_count': len(payout_records),
        'total_paid': total_paid,
        'payout_ids': payout_records
    })


@payments.route('/admin/revenue/history')
def admin_payout_history():
    """
    View payout history

    Shows all past payouts with status
    """

    if not session.get('is_admin'):
        return redirect(url_for('tier_0.homepage'))

    conn = get_db()

    payouts = conn.execute('''
        SELECT
            p.id,
            p.user_id,
            u.username,
            p.amount,
            p.payout_date,
            p.payout_method,
            p.status
        FROM payouts p
        JOIN users u ON p.user_id = u.id
        ORDER BY p.payout_date DESC
        LIMIT 100
    ''').fetchall()

    conn.close()

    return render_template('admin/revenue_history.html', payouts=payouts)


# ==============================================================================
# USER - EARNINGS DASHBOARD
# ==============================================================================

@payments.route('/user/earnings')
def user_earnings():
    """
    User earnings dashboard

    Shows ownership percentages, estimated earnings, payout history
    """

    if 'user_id' not in session:
        return redirect(url_for('tier_0.github_login'))

    user_id = session['user_id']

    # Get ownership summary
    summary = get_user_ownership_summary(user_id)

    # Get payout history
    conn = get_db()

    payouts = conn.execute('''
        SELECT
            id,
            amount,
            payout_date,
            payout_method,
            status
        FROM payouts
        WHERE user_id = ?
        ORDER BY payout_date DESC
    ''', (user_id,)).fetchall()

    # Get estimated next payout (placeholder - would calculate from current month revenue)
    estimated_next = 0.0  # TODO: Calculate from current month traffic/revenue

    conn.close()

    return render_template('user/earnings.html',
                          summary=summary,
                          payouts=payouts,
                          estimated_next=estimated_next)


@payments.route('/user/payout-settings', methods=['GET', 'POST'])
def user_payout_settings():
    """
    User payout preferences

    Choose payment method:
    - Stripe Connect (default)
    - ACH/Wire transfer
    - Cryptocurrency

    Store bank/crypto info
    """

    if 'user_id' not in session:
        return redirect(url_for('tier_0.github_login'))

    user_id = session['user_id']
    conn = get_db()

    if request.method == 'GET':
        # Get current settings
        settings = conn.execute('''
            SELECT payout_method, payout_details
            FROM user_payout_settings
            WHERE user_id = ?
        ''', (user_id,)).fetchone()

        conn.close()

        return render_template('user/payout_settings.html', settings=settings)

    # POST - Update settings
    payout_method = request.form.get('payout_method')  # stripe, wire, crypto
    payout_details = {}

    if payout_method == 'stripe':
        # Stripe Connect onboarding would happen here
        # For now, placeholder
        payout_details['stripe_account_id'] = request.form.get('stripe_account_id')

    elif payout_method == 'wire':
        payout_details['bank_name'] = request.form.get('bank_name')
        payout_details['account_number'] = request.form.get('account_number')
        payout_details['routing_number'] = request.form.get('routing_number')
        payout_details['swift'] = request.form.get('swift')

    elif payout_method == 'crypto':
        payout_details['wallet_address'] = request.form.get('wallet_address')
        payout_details['network'] = request.form.get('network')  # ethereum, bitcoin, etc.

    # Store settings
    conn.execute('''
        INSERT INTO user_payout_settings (user_id, payout_method, payout_details)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            payout_method = excluded.payout_method,
            payout_details = excluded.payout_details
    ''', (user_id, payout_method, json.dumps(payout_details)))

    conn.commit()
    conn.close()

    return redirect(url_for('payments.user_earnings'))


# ==============================================================================
# API ENDPOINTS
# ==============================================================================

@payments.route('/api/earnings/<int:user_id>')
def api_user_earnings(user_id):
    """
    API endpoint for user earnings

    Requires auth (API key or session)
    """

    # Check auth
    if session.get('user_id') != user_id:
        # Check API key
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'error': 'Unauthorized'}), 401

        # Verify API key
        conn = get_db()
        github = conn.execute(
            'SELECT user_id FROM github_profiles WHERE api_key = ?',
            (api_key,)
        ).fetchone()
        conn.close()

        if not github or github['user_id'] != user_id:
            return jsonify({'error': 'Invalid API key'}), 401

    # Get earnings data
    summary = get_user_ownership_summary(user_id)

    conn = get_db()
    payouts = conn.execute('''
        SELECT
            amount,
            payout_date,
            status
        FROM payouts
        WHERE user_id = ?
        ORDER BY payout_date DESC
        LIMIT 10
    ''', (user_id,)).fetchall()
    conn.close()

    return jsonify({
        'user_id': user_id,
        'ownership_summary': summary,
        'recent_payouts': [dict(p) for p in payouts]
    })


@payments.route('/api/domain-revenue/<int:domain_id>')
def api_domain_revenue(domain_id):
    """
    API endpoint for domain revenue

    Public (aggregated stats only)
    """

    distribution = get_domain_ownership_distribution(domain_id)

    return jsonify({
        'domain_id': domain_id,
        'total_distributed': distribution['total_distributed'],
        'platform_reserve': distribution['platform_reserve'],
        'owner_count': len(distribution['owners'])
    })


# ==============================================================================
# DATABASE SCHEMA (run once to initialize)
# ==============================================================================

def init_payment_tables():
    """Initialize payment-related tables"""
    conn = get_db()

    # Payouts table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS payouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            payout_date TIMESTAMP NOT NULL,
            payout_method TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            domains TEXT,
            stripe_transfer_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # User payout settings
    conn.execute('''
        CREATE TABLE IF NOT EXISTS user_payout_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            payout_method TEXT NOT NULL,
            payout_details TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Domain revenue tracking (for historical data)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS domain_revenue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain_id INTEGER NOT NULL,
            month TEXT NOT NULL,
            revenue REAL NOT NULL,
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (domain_id) REFERENCES domains(id),
            UNIQUE(domain_id, month)
        )
    ''')

    # 1099 data (for US tax reporting)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS tax_1099_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            tax_year INTEGER NOT NULL,
            total_paid REAL NOT NULL,
            tax_id TEXT,
            address TEXT,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, tax_year)
        )
    ''')

    conn.commit()
    conn.close()


# ==============================================================================
# STRIPE CONNECT INTEGRATION (PLACEHOLDER)
# ==============================================================================

def create_stripe_connect_account(user_id, email):
    """
    Create Stripe Connect account for user

    Returns account ID for payouts
    """

    # In production, use Stripe API:
    # import stripe
    # stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
    #
    # account = stripe.Account.create(
    #     type='express',
    #     email=email,
    #     capabilities={
    #         'transfers': {'requested': True}
    #     }
    # )
    #
    # return account.id

    # Placeholder
    return f'acct_placeholder_{user_id}'


def generate_stripe_onboarding_link(stripe_account_id, return_url, refresh_url):
    """
    Generate Stripe Connect onboarding link

    User completes KYC/banking info on Stripe
    """

    # In production:
    # account_link = stripe.AccountLink.create(
    #     account=stripe_account_id,
    #     refresh_url=refresh_url,
    #     return_url=return_url,
    #     type='account_onboarding'
    # )
    #
    # return account_link.url

    # Placeholder
    return f'https://connect.stripe.com/setup/{stripe_account_id}'


# ==============================================================================
# EXPORTS
# ==============================================================================

def register_payment_routes(app):
    """
    Register payment blueprint with Flask app

    Usage in app.py:
        from payment_routes import register_payment_routes
        register_payment_routes(app)
    """
    app.register_blueprint(payments)


if __name__ == '__main__':
    print("Initializing payment tables...")
    init_payment_tables()
    print("✅ Payment tables initialized")
    print()
    print("Payment routes defined:")
    print("  GET  /admin/revenue/domains")
    print("  GET/POST  /admin/revenue/calculate")
    print("  POST /admin/revenue/payout")
    print("  GET  /admin/revenue/history")
    print("  GET  /user/earnings")
    print("  GET/POST  /user/payout-settings")
    print()
    print("API:")
    print("  GET  /api/earnings/<user_id>")
    print("  GET  /api/domain-revenue/<domain_id>")
