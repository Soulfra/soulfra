#!/usr/bin/env python3
"""
Capitalized MVP - Bootstrap with Your Own Money

Model: You seed the platform with capital (e.g., $10k in T-Bills)
Users buy shares at NAV (Net Asset Value)
T-Bills compound at 4.5% → platform grows automatically

This is transparent, provable, and self-funding.

Example:
- Day 1: You invest $10,000 in T-Bills
- Platform owns: $10,000 in assets
- You own: 100% (10,000 shares @ $1/share NAV)

- Day 30: User pays $1
- Platform buys $1 more T-Bills
- Platform owns: $10,001 in assets
- User gets: 1 share @ $1 NAV
- You now own: 99.99% (10,000 / 10,001 shares)
- User owns: 0.01%

- Year 1: T-Bills compound
- Platform owns: $10,450 (4.5% yield)
- NAV per share: $1.045
- User's $1 is now worth: $1.045
- Your $10k is now worth: $10,449.55
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, Optional
from database import get_db

# ==============================================================================
# CONFIGURATION
# ==============================================================================

# Initial capitalization
FOUNDER_CAPITAL = 10000.00  # $10k seed capital
T_BILL_ANNUAL_YIELD = 0.045  # 4.5% (current 1-year T-Bill rate)

# Shares
INITIAL_SHARES = 10000  # 10,000 shares @ $1 NAV
SHARES_PER_DOLLAR = 1  # 1 share per $1 invested

# ==============================================================================
# DATABASE SCHEMA
# ==============================================================================

def init_capitalized_mvp_tables():
    """Initialize capitalized MVP tables"""
    conn = get_db()

    # Platform assets (T-Bills)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS platform_assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_type TEXT NOT NULL,
            ticker TEXT,
            quantity REAL NOT NULL,
            purchase_price REAL NOT NULL,
            purchase_date TIMESTAMP NOT NULL,
            maturity_date TIMESTAMP,
            annual_yield REAL,
            current_value REAL,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Share ledger
    conn.execute('''
        CREATE TABLE IF NOT EXISTS share_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            email TEXT,
            shares REAL NOT NULL,
            purchase_price_per_share REAL NOT NULL,
            total_paid REAL NOT NULL,
            purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            source TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # NAV history (Net Asset Value per share over time)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS nav_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE UNIQUE NOT NULL,
            total_assets REAL NOT NULL,
            total_shares REAL NOT NULL,
            nav_per_share REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()


# ==============================================================================
# FOUNDER SEED CAPITAL
# ==============================================================================

def seed_platform_capital(amount: float = FOUNDER_CAPITAL) -> Dict:
    """
    Seed platform with founder capital

    Args:
        amount: Dollar amount to invest (default $10k)

    Returns:
        {
            'asset_id': int,
            'shares_issued': int,
            'nav_per_share': float
        }
    """

    conn = get_db()

    # Buy T-Bills with seed capital
    maturity_date = datetime.utcnow() + timedelta(days=365)

    cursor = conn.execute('''
        INSERT INTO platform_assets (
            asset_type, ticker, quantity, purchase_price,
            purchase_date, maturity_date, annual_yield, current_value
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        't_bill',
        'UST_1Y_2027',
        amount,
        amount,
        datetime.utcnow(),
        maturity_date,
        T_BILL_ANNUAL_YIELD,
        amount
    ))

    asset_id = cursor.lastrowid

    # Issue shares to founder
    shares = amount / 1.00  # $1 per share NAV

    conn.execute('''
        INSERT INTO share_ledger (
            user_id, shares, purchase_price_per_share,
            total_paid, source
        ) VALUES (?, ?, ?, ?, ?)
    ''', (
        None,  # Founder (no user_id yet)
        shares,
        1.00,
        amount,
        'founder_seed_capital'
    ))

    # Record NAV
    record_nav(amount, shares, 1.00)

    conn.commit()
    conn.close()

    return {
        'asset_id': asset_id,
        'shares_issued': shares,
        'nav_per_share': 1.00,
        'total_assets': amount
    }


# ==============================================================================
# NAV CALCULATION
# ==============================================================================

def calculate_current_nav() -> Dict:
    """
    Calculate current Net Asset Value per share

    Formula:
        NAV = (Total Assets) / (Total Shares)

    Total Assets = Sum of all T-Bills + accrued interest
    Total Shares = All issued shares

    Returns:
        {
            'total_assets': float,
            'total_shares': float,
            'nav_per_share': float,
            'accrued_interest': float
        }
    """

    conn = get_db()

    # Get all active assets
    assets = conn.execute('''
        SELECT
            purchase_price,
            annual_yield,
            purchase_date,
            maturity_date
        FROM platform_assets
        WHERE status = 'active'
    ''').fetchall()

    # Calculate total assets including accrued interest
    total_assets = 0.0
    total_interest = 0.0

    for asset in assets:
        principal = asset['purchase_price']
        annual_yield = asset['annual_yield']
        purchase_date = datetime.fromisoformat(asset['purchase_date'])
        maturity_date = datetime.fromisoformat(asset['maturity_date'])

        # Days held
        days_held = (datetime.utcnow() - purchase_date).days
        days_to_maturity = (maturity_date - purchase_date).days

        # Accrued interest = principal × yield × (days_held / 365)
        accrued_interest = principal * annual_yield * (days_held / 365.0)

        total_assets += principal + accrued_interest
        total_interest += accrued_interest

    # Get total shares
    shares_result = conn.execute('''
        SELECT SUM(shares) as total_shares
        FROM share_ledger
    ''').fetchone()

    total_shares = shares_result['total_shares'] or 0.0

    conn.close()

    # NAV per share
    nav_per_share = total_assets / total_shares if total_shares > 0 else 1.00

    return {
        'total_assets': round(total_assets, 2),
        'total_shares': round(total_shares, 2),
        'nav_per_share': round(nav_per_share, 4),
        'accrued_interest': round(total_interest, 2)
    }


def record_nav(total_assets: float, total_shares: float, nav_per_share: float):
    """Record NAV for historical tracking"""
    conn = get_db()

    conn.execute('''
        INSERT OR REPLACE INTO nav_history (
            date, total_assets, total_shares, nav_per_share
        ) VALUES (?, ?, ?, ?)
    ''', (
        datetime.utcnow().date(),
        total_assets,
        total_shares,
        nav_per_share
    ))

    conn.commit()
    conn.close()


# ==============================================================================
# USER SHARE PURCHASE
# ==============================================================================

def purchase_shares(user_id: Optional[int], email: str, amount: float) -> Dict:
    """
    User purchases shares at current NAV

    Args:
        user_id: User ID (if logged in)
        email: User email
        amount: Dollar amount to invest

    Returns:
        {
            'shares_purchased': float,
            'nav_per_share': float,
            'total_paid': float
        }
    """

    conn = get_db()

    # Get current NAV
    nav = calculate_current_nav()
    nav_per_share = nav['nav_per_share']

    # Calculate shares
    shares = amount / nav_per_share

    # Buy T-Bills with user's money
    maturity_date = datetime.utcnow() + timedelta(days=365)

    conn.execute('''
        INSERT INTO platform_assets (
            asset_type, ticker, quantity, purchase_price,
            purchase_date, maturity_date, annual_yield, current_value
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        't_bill',
        'UST_1Y_2027',
        amount,
        amount,
        datetime.utcnow(),
        maturity_date,
        T_BILL_ANNUAL_YIELD,
        amount
    ))

    # Issue shares to user
    conn.execute('''
        INSERT INTO share_ledger (
            user_id, email, shares, purchase_price_per_share,
            total_paid, source
        ) VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        user_id,
        email,
        shares,
        nav_per_share,
        amount,
        'user_purchase'
    ))

    # Update NAV
    new_nav = calculate_current_nav()
    record_nav(new_nav['total_assets'], new_nav['total_shares'], new_nav['nav_per_share'])

    conn.commit()
    conn.close()

    return {
        'shares_purchased': round(shares, 4),
        'nav_per_share': round(nav_per_share, 4),
        'total_paid': amount,
        'ownership_percentage': round((shares / new_nav['total_shares']) * 100, 4)
    }


# ==============================================================================
# USER PORTFOLIO
# ==============================================================================

def get_user_portfolio(user_id: int = None, email: str = None) -> Optional[Dict]:
    """
    Get user's portfolio

    Args:
        user_id: User ID
        email: User email

    Returns:
        {
            'total_shares': float,
            'total_invested': float,
            'current_value': float,
            'gain_loss': float,
            'ownership_percentage': float
        }
    """

    conn = get_db()

    if user_id:
        shares_result = conn.execute('''
            SELECT
                SUM(shares) as total_shares,
                SUM(total_paid) as total_invested
            FROM share_ledger
            WHERE user_id = ?
        ''', (user_id,)).fetchone()
    elif email:
        shares_result = conn.execute('''
            SELECT
                SUM(shares) as total_shares,
                SUM(total_paid) as total_invested
            FROM share_ledger
            WHERE email = ?
        ''', (email,)).fetchone()
    else:
        conn.close()
        return None

    if not shares_result or not shares_result['total_shares']:
        conn.close()
        return None

    total_shares = shares_result['total_shares']
    total_invested = shares_result['total_invested']

    # Get current NAV
    nav = calculate_current_nav()
    nav_per_share = nav['nav_per_share']

    # Calculate current value
    current_value = total_shares * nav_per_share
    gain_loss = current_value - total_invested
    ownership_pct = (total_shares / nav['total_shares']) * 100

    conn.close()

    return {
        'total_shares': round(total_shares, 4),
        'total_invested': round(total_invested, 2),
        'current_value': round(current_value, 2),
        'gain_loss': round(gain_loss, 2),
        'gain_loss_percentage': round((gain_loss / total_invested) * 100, 2) if total_invested > 0 else 0,
        'ownership_percentage': round(ownership_pct, 4),
        'nav_per_share': round(nav_per_share, 4)
    }


# ==============================================================================
# PLATFORM STATS
# ==============================================================================

def get_platform_stats() -> Dict:
    """
    Get overall platform statistics

    Returns:
        {
            'total_assets': float,
            'total_shares': float,
            'nav_per_share': float,
            'total_shareholders': int,
            'yield_ytd': float
        }
    """

    conn = get_db()

    nav = calculate_current_nav()

    # Count shareholders
    shareholders = conn.execute('''
        SELECT COUNT(DISTINCT COALESCE(user_id, email)) as count
        FROM share_ledger
    ''').fetchone()

    # Get initial NAV (day 1)
    initial_nav = conn.execute('''
        SELECT nav_per_share
        FROM nav_history
        ORDER BY date ASC
        LIMIT 1
    ''').fetchone()

    initial_nav_value = initial_nav['nav_per_share'] if initial_nav else 1.00

    # YTD yield
    ytd_yield = ((nav['nav_per_share'] - initial_nav_value) / initial_nav_value) * 100

    conn.close()

    return {
        'total_assets': nav['total_assets'],
        'total_shares': nav['total_shares'],
        'nav_per_share': nav['nav_per_share'],
        'accrued_interest': nav['accrued_interest'],
        'total_shareholders': shareholders['count'],
        'yield_ytd': round(ytd_yield, 2),
        'initial_nav': initial_nav_value
    }


# ==============================================================================
# EXPORTS
# ==============================================================================

if __name__ == '__main__':
    print("Initializing capitalized MVP tables...")
    init_capitalized_mvp_tables()
    print("✅ Tables initialized")
    print()

    print("Seeding platform with founder capital...")
    seed_result = seed_platform_capital(FOUNDER_CAPITAL)
    print(f"✅ Seeded with ${FOUNDER_CAPITAL:,.2f}")
    print(f"   Shares issued: {seed_result['shares_issued']:,.0f}")
    print(f"   NAV per share: ${seed_result['nav_per_share']:.4f}")
    print()

    print("Platform stats:")
    stats = get_platform_stats()
    print(f"   Total assets: ${stats['total_assets']:,.2f}")
    print(f"   Total shares: {stats['total_shares']:,.0f}")
    print(f"   NAV per share: ${stats['nav_per_share']:.4f}")
    print(f"   Accrued interest: ${stats['accrued_interest']:,.2f}")
    print(f"   YTD yield: {stats['yield_ytd']:.2f}%")
