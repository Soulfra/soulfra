#!/usr/bin/env python3
"""
Domain Liquidity Pools - Uniswap AMM for Communities

Apply Uniswap's constant product formula (x * y = k) to domains:
- x = Subscribers in Domain A
- y = Subscribers in Domain B
- k = Constant product

Like co-ops and unions for ideas:
- Collective ownership of cross-pollinated communities
- Automated rebalancing via content sharing
- LP tokens = ownership shares

Example:
    Pool: soulfra.com ↔ deathtodata.com

    soulfra_subs = 1000
    deathtodata_subs = 500
    k = 1000 × 500 = 500,000 (constant)

    Add liquidity: Contribute 100 subs to both sides
    Earn fees: Get access to cross-posted content
    Withdraw: Pull subs + accumulated value
"""

import math
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from database import get_db

# ==============================================================================
# DATABASE SCHEMA
# ==============================================================================

def init_liquidity_pool_tables():
    """Initialize liquidity pool tables"""
    conn = get_db()

    # Liquidity pools (pairs of domains)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS liquidity_pools (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain_a_id INTEGER NOT NULL,
            domain_b_id INTEGER NOT NULL,
            reserve_a REAL DEFAULT 0.0,
            reserve_b REAL DEFAULT 0.0,
            k_constant REAL DEFAULT 0.0,
            total_lp_tokens REAL DEFAULT 0.0,
            fee_percentage REAL DEFAULT 0.003,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (domain_a_id) REFERENCES domains(id),
            FOREIGN KEY (domain_b_id) REFERENCES domains(id),
            UNIQUE(domain_a_id, domain_b_id)
        )
    ''')

    # LP token holders (liquidity providers)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS lp_token_holders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pool_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            lp_tokens REAL NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pool_id) REFERENCES liquidity_pools(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Liquidity events (add/remove liquidity, swaps)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS liquidity_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pool_id INTEGER NOT NULL,
            user_id INTEGER,
            event_type TEXT NOT NULL,
            amount_a REAL,
            amount_b REAL,
            lp_tokens_change REAL,
            k_before REAL,
            k_after REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pool_id) REFERENCES liquidity_pools(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    conn.commit()
    conn.close()


# ==============================================================================
# POOL CREATION
# ==============================================================================

def create_pool(domain_a_id: int, domain_b_id: int, initial_a: float, initial_b: float, user_id: int) -> Dict:
    """
    Create new liquidity pool between two domains

    Args:
        domain_a_id: First domain ID
        domain_b_id: Second domain ID
        initial_a: Initial reserve for domain A (e.g., 1000 subscribers)
        initial_b: Initial reserve for domain B (e.g., 500 subscribers)
        user_id: User creating the pool

    Returns:
        {
            'pool_id': int,
            'k_constant': float,
            'lp_tokens': float
        }
    """

    conn = get_db()

    # Calculate k constant
    k = initial_a * initial_b

    # Initial LP tokens = sqrt(k) (Uniswap formula)
    lp_tokens = math.sqrt(k)

    # Create pool
    cursor = conn.execute('''
        INSERT INTO liquidity_pools (
            domain_a_id, domain_b_id,
            reserve_a, reserve_b, k_constant, total_lp_tokens
        ) VALUES (?, ?, ?, ?, ?, ?)
    ''', (domain_a_id, domain_b_id, initial_a, initial_b, k, lp_tokens))

    pool_id = cursor.lastrowid

    # Issue LP tokens to creator
    conn.execute('''
        INSERT INTO lp_token_holders (pool_id, user_id, lp_tokens)
        VALUES (?, ?, ?)
    ''', (pool_id, user_id, lp_tokens))

    # Record event
    conn.execute('''
        INSERT INTO liquidity_events (
            pool_id, user_id, event_type,
            amount_a, amount_b, lp_tokens_change, k_before, k_after
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (pool_id, user_id, 'create_pool', initial_a, initial_b, lp_tokens, 0, k))

    conn.commit()
    conn.close()

    return {
        'pool_id': pool_id,
        'k_constant': k,
        'lp_tokens': lp_tokens,
        'reserve_a': initial_a,
        'reserve_b': initial_b
    }


# ==============================================================================
# ADD LIQUIDITY
# ==============================================================================

def add_liquidity(pool_id: int, user_id: int, amount_a: float, amount_b: float) -> Dict:
    """
    Add liquidity to existing pool

    Args:
        pool_id: Pool ID
        user_id: User adding liquidity
        amount_a: Amount to add to reserve A
        amount_b: Amount to add to reserve B

    Returns:
        {
            'lp_tokens_minted': float,
            'new_k': float
        }
    """

    conn = get_db()

    # Get current pool state
    pool = conn.execute(
        'SELECT * FROM liquidity_pools WHERE id = ?',
        (pool_id,)
    ).fetchone()

    if not pool:
        conn.close()
        return {'error': 'Pool not found'}

    # Calculate proportional amounts
    # User must add liquidity in proportion to current reserves
    ratio = pool['reserve_a'] / pool['reserve_b']
    expected_b = amount_a / ratio

    if abs(amount_b - expected_b) > 0.01:  # Allow 1% slippage
        conn.close()
        return {'error': f'Amounts must be proportional. Expected {expected_b:.2f} for domain B'}

    # Calculate LP tokens to mint
    # LP tokens = (amount_a / reserve_a) × total_lp_tokens
    lp_tokens_minted = (amount_a / pool['reserve_a']) * pool['total_lp_tokens']

    # Update pool reserves
    new_reserve_a = pool['reserve_a'] + amount_a
    new_reserve_b = pool['reserve_b'] + amount_b
    new_k = new_reserve_a * new_reserve_b
    new_total_lp = pool['total_lp_tokens'] + lp_tokens_minted

    conn.execute('''
        UPDATE liquidity_pools
        SET reserve_a = ?, reserve_b = ?, k_constant = ?, total_lp_tokens = ?
        WHERE id = ?
    ''', (new_reserve_a, new_reserve_b, new_k, new_total_lp, pool_id))

    # Issue LP tokens to user
    existing = conn.execute(
        'SELECT lp_tokens FROM lp_token_holders WHERE pool_id = ? AND user_id = ?',
        (pool_id, user_id)
    ).fetchone()

    if existing:
        conn.execute('''
            UPDATE lp_token_holders
            SET lp_tokens = lp_tokens + ?
            WHERE pool_id = ? AND user_id = ?
        ''', (lp_tokens_minted, pool_id, user_id))
    else:
        conn.execute('''
            INSERT INTO lp_token_holders (pool_id, user_id, lp_tokens)
            VALUES (?, ?, ?)
        ''', (pool_id, user_id, lp_tokens_minted))

    # Record event
    conn.execute('''
        INSERT INTO liquidity_events (
            pool_id, user_id, event_type,
            amount_a, amount_b, lp_tokens_change, k_before, k_after
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (pool_id, user_id, 'add_liquidity', amount_a, amount_b, lp_tokens_minted, pool['k_constant'], new_k))

    conn.commit()
    conn.close()

    return {
        'lp_tokens_minted': lp_tokens_minted,
        'new_k': new_k,
        'new_reserve_a': new_reserve_a,
        'new_reserve_b': new_reserve_b
    }


# ==============================================================================
# SWAP (Cross-Pollination)
# ==============================================================================

def swap(pool_id: int, user_id: int, input_domain: str, amount_in: float) -> Dict:
    """
    Swap between domains (cross-pollination)

    Example:
        Post content to Domain A
        Automatically cross-post to Domain B
        Rebalances pool via constant product

    Args:
        pool_id: Pool ID
        user_id: User performing swap
        input_domain: 'a' or 'b' (which domain receives content)
        amount_in: Amount of subscribers/content added

    Returns:
        {
            'amount_out': float,
            'price_impact': float
        }
    """

    conn = get_db()

    pool = conn.execute(
        'SELECT * FROM liquidity_pools WHERE id = ?',
        (pool_id,)
    ).fetchone()

    if not pool:
        conn.close()
        return {'error': 'Pool not found'}

    # Get reserves
    reserve_in = pool['reserve_a'] if input_domain == 'a' else pool['reserve_b']
    reserve_out = pool['reserve_b'] if input_domain == 'a' else pool['reserve_a']

    # Apply fee (0.3% like Uniswap)
    fee = pool['fee_percentage']
    amount_in_with_fee = amount_in * (1 - fee)

    # Constant product formula: k = x * y
    # New reserves: (reserve_in + amount_in) * (reserve_out - amount_out) = k
    # Solve for amount_out:
    # amount_out = reserve_out - (k / (reserve_in + amount_in_with_fee))

    k = pool['k_constant']
    amount_out = reserve_out - (k / (reserve_in + amount_in_with_fee))

    # Price impact
    price_before = reserve_out / reserve_in
    price_after = (reserve_out - amount_out) / (reserve_in + amount_in)
    price_impact = abs((price_after - price_before) / price_before) * 100

    # Update reserves
    if input_domain == 'a':
        new_reserve_a = reserve_in + amount_in
        new_reserve_b = reserve_out - amount_out
    else:
        new_reserve_b = reserve_in + amount_in
        new_reserve_a = reserve_out - amount_out

    conn.execute('''
        UPDATE liquidity_pools
        SET reserve_a = ?, reserve_b = ?
        WHERE id = ?
    ''', (new_reserve_a, new_reserve_b, pool_id))

    # Record event
    conn.execute('''
        INSERT INTO liquidity_events (
            pool_id, user_id, event_type,
            amount_a, amount_b, k_before, k_after
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        pool_id, user_id, 'swap',
        amount_in if input_domain == 'a' else -amount_out,
        amount_in if input_domain == 'b' else -amount_out,
        k, k  # k stays constant
    ))

    conn.commit()
    conn.close()

    return {
        'amount_out': amount_out,
        'price_impact': price_impact,
        'exchange_rate': amount_out / amount_in
    }


# ==============================================================================
# POOL STATS
# ==============================================================================

def get_pool_stats(pool_id: int) -> Dict:
    """Get pool statistics"""

    conn = get_db()

    pool = conn.execute('''
        SELECT
            lp.*,
            da.domain_name as domain_a_name,
            db.domain_name as domain_b_name
        FROM liquidity_pools lp
        JOIN domains da ON lp.domain_a_id = da.id
        JOIN domains db ON lp.domain_b_id = db.id
        WHERE lp.id = ?
    ''', (pool_id,)).fetchone()

    if not pool:
        conn.close()
        return {'error': 'Pool not found'}

    # Get total value locked (TVL)
    tvl = pool['reserve_a'] + pool['reserve_b']

    # Get 24h volume
    volume_24h = conn.execute('''
        SELECT
            SUM(ABS(amount_a)) + SUM(ABS(amount_b)) as volume
        FROM liquidity_events
        WHERE pool_id = ?
            AND event_type = 'swap'
            AND created_at > datetime('now', '-1 day')
    ''', (pool_id,)).fetchone()

    conn.close()

    return {
        'pool_id': pool['id'],
        'domain_a': pool['domain_a_name'],
        'domain_b': pool['domain_b_name'],
        'reserve_a': pool['reserve_a'],
        'reserve_b': pool['reserve_b'],
        'k_constant': pool['k_constant'],
        'total_lp_tokens': pool['total_lp_tokens'],
        'tvl': tvl,
        'volume_24h': volume_24h['volume'] or 0.0,
        'exchange_rate': pool['reserve_b'] / pool['reserve_a'] if pool['reserve_a'] > 0 else 0
    }


# ==============================================================================
# USER LP POSITION
# ==============================================================================

def get_user_lp_position(pool_id: int, user_id: int) -> Dict:
    """Get user's liquidity provider position"""

    conn = get_db()

    # Get user's LP tokens
    holder = conn.execute('''
        SELECT lp_tokens
        FROM lp_token_holders
        WHERE pool_id = ? AND user_id = ?
    ''', (pool_id, user_id)).fetchone()

    if not holder:
        conn.close()
        return {'error': 'No position found'}

    # Get pool stats
    pool = conn.execute(
        'SELECT * FROM liquidity_pools WHERE id = ?',
        (pool_id,)
    ).fetchone()

    # Calculate share of pool
    share = holder['lp_tokens'] / pool['total_lp_tokens']

    # Calculate claimable amounts
    claimable_a = pool['reserve_a'] * share
    claimable_b = pool['reserve_b'] * share

    conn.close()

    return {
        'lp_tokens': holder['lp_tokens'],
        'pool_share': round(share * 100, 4),
        'claimable_a': claimable_a,
        'claimable_b': claimable_b
    }


# ==============================================================================
# EXPORTS
# ==============================================================================

if __name__ == '__main__':
    print("Initializing liquidity pool tables...")
    init_liquidity_pool_tables()
    print("✅ Liquidity pool tables initialized")
    print()
    print("Domain Liquidity Pools (Uniswap AMM for Communities)")
    print()
    print("Features:")
    print("  - Constant product formula (x * y = k)")
    print("  - Add/remove liquidity")
    print("  - Swap (cross-pollination)")
    print("  - LP tokens (ownership shares)")
    print("  - Like co-ops and unions for ideas")
