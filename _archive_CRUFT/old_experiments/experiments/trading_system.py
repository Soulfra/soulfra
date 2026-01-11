#!/usr/bin/env python3
"""
Trading System - Player-to-Player Item Exchange

NO crypto/blockchain - just traditional database trades!

Features:
- Offer items for trade
- Accept/reject trade offers
- Membership tier limits (Free: 1/day, Premium: 10/day, Pro: unlimited)
- Trade history
"""

import sqlite3
from typing import Dict, List, Optional
from datetime import datetime, timedelta


def get_user_inventory(user_id: int) -> List[Dict]:
    """Get user's inventory with item details"""

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            inv.id as inventory_id,
            inv.item_id,
            inv.quantity,
            inv.equipped,
            inv.earned_from,
            i.name,
            i.rarity,
            i.item_type,
            i.stats
        FROM inventory inv
        JOIN items i ON inv.item_id = i.id
        WHERE inv.user_id = ?
        ORDER BY
            CASE i.rarity
                WHEN 'legendary' THEN 1
                WHEN 'epic' THEN 2
                WHEN 'rare' THEN 3
                WHEN 'uncommon' THEN 4
                WHEN 'common' THEN 5
                ELSE 6
            END,
            i.name
    ''', (user_id,))

    inventory = []
    for row in cursor.fetchall():
        inventory.append({
            'inventory_id': row[0],
            'item_id': row[1],
            'quantity': row[2],
            'equipped': bool(row[3]),
            'earned_from': row[4],
            'name': row[5],
            'rarity': row[6],
            'item_type': row[7],
            'stats': row[8]
        })

    conn.close()
    return inventory


def can_trade_today(user_id: int) -> Dict:
    """Check if user can trade based on membership tier and daily limit"""

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    # Get membership tier
    cursor.execute('''
        SELECT tier FROM memberships WHERE user_id = ?
    ''', (user_id,))

    membership = cursor.fetchone()
    tier = membership[0] if membership else 'free'

    # Get tier limit (hard-coded based on membership tier)
    tier_limits = {
        'free': 1,
        'premium': 10,
        'pro': -1  # -1 means unlimited
    }

    daily_limit = tier_limits.get(tier, 1)  # Default to 1 for free

    # Count trades today
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    cursor.execute('''
        SELECT COUNT(*) FROM trades
        WHERE from_user_id = ?
        AND created_at >= ?
    ''', (user_id, today_start))

    trades_today = cursor.fetchone()[0]

    conn.close()

    can_trade = (daily_limit == -1) or (trades_today < daily_limit)  # -1 = unlimited

    return {
        'can_trade': can_trade,
        'tier': tier,
        'trades_today': trades_today,
        'daily_limit': daily_limit if daily_limit != -1 else 'unlimited',
        'trades_remaining': 'unlimited' if daily_limit == -1 else max(0, daily_limit - trades_today)
    }


def create_trade_offer(from_user_id: int, to_user_id: int, offered_items: List[Dict], requested_items: List[Dict]) -> int:
    """
    Create a trade offer

    Args:
        from_user_id: User making the offer
        to_user_id: User receiving the offer
        offered_items: [{'item_id': 1, 'quantity': 2}, ...]
        requested_items: [{'item_id': 3, 'quantity': 1}, ...]

    Returns:
        trade_id
    """

    # Check if can trade
    trade_check = can_trade_today(from_user_id)
    if not trade_check['can_trade']:
        raise ValueError(f"Daily trade limit reached ({trade_check['daily_limit']}). Upgrade membership for more trades!")

    # Validate offered items are in inventory
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    for item in offered_items:
        cursor.execute('''
            SELECT quantity FROM inventory
            WHERE user_id = ? AND item_id = ?
        ''', (from_user_id, item['item_id']))

        inv = cursor.fetchone()
        if not inv:
            conn.close()
            raise ValueError(f"You don't have item {item['item_id']}")

        if inv[0] < item['quantity']:
            conn.close()
            raise ValueError(f"Not enough quantity of item {item['item_id']} (have {inv[0]}, need {item['quantity']})")

    # Create trade
    import json

    cursor.execute('''
        INSERT INTO trades (
            from_user_id, to_user_id, status,
            offered_items, requested_items
        ) VALUES (?, ?, ?, ?, ?)
    ''', (
        from_user_id,
        to_user_id,
        'pending',
        json.dumps(offered_items),
        json.dumps(requested_items)
    ))

    trade_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return trade_id


def accept_trade(trade_id: int, user_id: int) -> Dict:
    """
    Accept a trade offer

    Args:
        trade_id: Trade to accept
        user_id: User accepting (must be to_user_id)

    Returns:
        Dict with success status and details
    """

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    # Get trade
    cursor.execute('''
        SELECT from_user_id, to_user_id, status, offered_items, requested_items
        FROM trades
        WHERE id = ?
    ''', (trade_id,))

    trade = cursor.fetchone()
    if not trade:
        conn.close()
        raise ValueError("Trade not found")

    from_user_id, to_user_id, status, offered_items_json, requested_items_json = trade

    # Validate
    if to_user_id != user_id:
        conn.close()
        raise ValueError("You are not the recipient of this trade")

    if status != 'pending':
        conn.close()
        raise ValueError(f"Trade already {status}")

    # Parse items
    import json
    offered_items = json.loads(offered_items_json)
    requested_items = json.loads(requested_items_json)

    # Validate accepting user has requested items
    for item in requested_items:
        cursor.execute('''
            SELECT quantity FROM inventory
            WHERE user_id = ? AND item_id = ?
        ''', (to_user_id, item['item_id']))

        inv = cursor.fetchone()
        if not inv or inv[0] < item['quantity']:
            conn.close()
            raise ValueError(f"You don't have enough of item {item['item_id']}")

    # Execute trade
    # 1. Remove offered items from from_user
    for item in offered_items:
        cursor.execute('''
            UPDATE inventory
            SET quantity = quantity - ?
            WHERE user_id = ? AND item_id = ?
        ''', (item['quantity'], from_user_id, item['item_id']))

        # Remove if quantity is 0
        cursor.execute('''
            DELETE FROM inventory
            WHERE user_id = ? AND item_id = ? AND quantity <= 0
        ''', (from_user_id, item['item_id']))

    # 2. Add offered items to to_user
    for item in offered_items:
        cursor.execute('''
            SELECT id, quantity FROM inventory
            WHERE user_id = ? AND item_id = ?
        ''', (to_user_id, item['item_id']))

        existing = cursor.fetchone()
        if existing:
            # Update quantity
            cursor.execute('''
                UPDATE inventory
                SET quantity = quantity + ?
                WHERE id = ?
            ''', (item['quantity'], existing[0]))
        else:
            # Add new item
            cursor.execute('''
                INSERT INTO inventory (user_id, item_id, quantity, earned_from)
                VALUES (?, ?, ?, ?)
            ''', (to_user_id, item['item_id'], item['quantity'], f'trade:{trade_id}'))

    # 3. Remove requested items from to_user
    for item in requested_items:
        cursor.execute('''
            UPDATE inventory
            SET quantity = quantity - ?
            WHERE user_id = ? AND item_id = ?
        ''', (item['quantity'], to_user_id, item['item_id']))

        cursor.execute('''
            DELETE FROM inventory
            WHERE user_id = ? AND item_id = ? AND quantity <= 0
        ''', (to_user_id, item['item_id']))

    # 4. Add requested items to from_user
    for item in requested_items:
        cursor.execute('''
            SELECT id, quantity FROM inventory
            WHERE user_id = ? AND item_id = ?
        ''', (from_user_id, item['item_id']))

        existing = cursor.fetchone()
        if existing:
            cursor.execute('''
                UPDATE inventory
                SET quantity = quantity + ?
                WHERE id = ?
            ''', (item['quantity'], existing[0]))
        else:
            cursor.execute('''
                INSERT INTO inventory (user_id, item_id, quantity, earned_from)
                VALUES (?, ?, ?, ?)
            ''', (from_user_id, item['item_id'], item['quantity'], f'trade:{trade_id}'))

    # 5. Update trade status
    cursor.execute('''
        UPDATE trades
        SET status = 'accepted',
            accepted_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (trade_id,))

    conn.commit()
    conn.close()

    return {
        'success': True,
        'trade_id': trade_id,
        'message': 'Trade completed successfully!'
    }


def reject_trade(trade_id: int, user_id: int) -> Dict:
    """Reject a trade offer"""

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    # Get trade
    cursor.execute('''
        SELECT from_user_id, to_user_id, status
        FROM trades
        WHERE id = ?
    ''', (trade_id,))

    trade = cursor.fetchone()
    if not trade:
        conn.close()
        raise ValueError("Trade not found")

    from_user_id, to_user_id, status = trade

    # Validate
    if to_user_id != user_id:
        conn.close()
        raise ValueError("You are not the recipient of this trade")

    if status != 'pending':
        conn.close()
        raise ValueError(f"Trade already {status}")

    # Reject
    cursor.execute('''
        UPDATE trades
        SET status = 'rejected',
            accepted_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (trade_id,))

    conn.commit()
    conn.close()

    return {
        'success': True,
        'trade_id': trade_id,
        'message': 'Trade rejected'
    }


def get_incoming_trades(user_id: int) -> List[Dict]:
    """Get pending trade offers where user is recipient"""

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            t.id,
            t.from_user_id,
            u.username as from_username,
            t.status,
            t.offered_items,
            t.requested_items,
            t.created_at
        FROM trades t
        JOIN users u ON t.from_user_id = u.id
        WHERE t.to_user_id = ? AND t.status = 'pending'
        ORDER BY t.created_at DESC
    ''', (user_id,))

    trades = []
    import json
    for row in cursor.fetchall():
        trades.append({
            'trade_id': row[0],
            'from_user_id': row[1],
            'from_username': row[2],
            'status': row[3],
            'offered_items': json.loads(row[4]),
            'requested_items': json.loads(row[5]),
            'created_at': row[6]
        })

    # Enrich with item names
    for trade in trades:
        for item_list in [trade['offered_items'], trade['requested_items']]:
            for item in item_list:
                cursor.execute('SELECT name, rarity FROM items WHERE id = ?', (item['item_id'],))
                item_row = cursor.fetchone()
                if item_row:
                    item['name'] = item_row[0]
                    item['rarity'] = item_row[1]

    conn.close()
    return trades


def get_outgoing_trades(user_id: int) -> List[Dict]:
    """Get trade offers created by user"""

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            t.id,
            t.to_user_id,
            u.username as to_username,
            t.status,
            t.offered_items,
            t.requested_items,
            t.created_at
        FROM trades t
        JOIN users u ON t.to_user_id = u.id
        WHERE t.from_user_id = ?
        ORDER BY t.created_at DESC
        LIMIT 20
    ''', (user_id,))

    trades = []
    import json
    for row in cursor.fetchall():
        trades.append({
            'trade_id': row[0],
            'to_user_id': row[1],
            'to_username': row[2],
            'status': row[3],
            'offered_items': json.loads(row[4]),
            'requested_items': json.loads(row[5]),
            'created_at': row[6]
        })

    # Enrich with item names
    for trade in trades:
        for item_list in [trade['offered_items'], trade['requested_items']]:
            for item in item_list:
                cursor.execute('SELECT name, rarity FROM items WHERE id = ?', (item['item_id'],))
                item_row = cursor.fetchone()
                if item_row:
                    item['name'] = item_row[0]
                    item['rarity'] = item_row[1]

    conn.close()
    return trades


if __name__ == '__main__':
    """Test trading system"""

    # Get first two users
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    cursor.execute('SELECT id, username FROM users LIMIT 2')
    users = cursor.fetchall()
    conn.close()

    if len(users) < 2:
        print("❌ Need at least 2 users to test trading")
        exit(1)

    user1_id, user1_name = users[0]
    user2_id, user2_name = users[1]

    print()
    print("=" * 60)
    print("🔄 TRADING SYSTEM TEST")
    print("=" * 60)
    print()

    print(f"👤 User 1: {user1_name} (ID: {user1_id})")
    print(f"👤 User 2: {user2_name} (ID: {user2_id})")
    print()

    # Check trade limits
    print("-" * 60)
    print("📊 TRADE LIMITS")
    print("-" * 60)
    limits1 = can_trade_today(user1_id)
    print(f"{user1_name}: {limits1['tier']} tier - {limits1['trades_remaining']} trades remaining")

    limits2 = can_trade_today(user2_id)
    print(f"{user2_name}: {limits2['tier']} tier - {limits2['trades_remaining']} trades remaining")
    print()

    # Show inventories
    print("-" * 60)
    print(f"🎒 {user1_name}'S INVENTORY")
    print("-" * 60)
    inv1 = get_user_inventory(user1_id)
    if inv1:
        for item in inv1[:5]:
            print(f"  {item['name']} ({item['rarity']}) x{item['quantity']}")
    else:
        print("  Empty inventory")
    print()

    print("-" * 60)
    print(f"🎒 {user2_name}'S INVENTORY")
    print("-" * 60)
    inv2 = get_user_inventory(user2_id)
    if inv2:
        for item in inv2[:5]:
            print(f"  {item['name']} ({item['rarity']}) x{item['quantity']}")
    else:
        print("  Empty inventory")
    print()

    # Create a test trade if both have items
    if inv1 and inv2:
        print("-" * 60)
        print("🔄 CREATING TEST TRADE")
        print("-" * 60)

        try:
            trade_id = create_trade_offer(
                from_user_id=user1_id,
                to_user_id=user2_id,
                offered_items=[{'item_id': inv1[0]['item_id'], 'quantity': 1}],
                requested_items=[{'item_id': inv2[0]['item_id'], 'quantity': 1}]
            )

            print(f"✅ Trade created (ID: {trade_id})")
            print(f"   {user1_name} offers: {inv1[0]['name']} x1")
            print(f"   {user1_name} wants: {inv2[0]['name']} x1")
            print()

            # Show incoming trades
            incoming = get_incoming_trades(user2_id)
            print(f"📨 {user2_name} has {len(incoming)} incoming trade(s)")

        except Exception as e:
            print(f"❌ Error creating trade: {e}")

    print("=" * 60)
