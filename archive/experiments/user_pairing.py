#!/usr/bin/env python3
"""
User Pairing System - Spotify Blend-style Account Pairing

Enables users to pair accounts and compare/merge cringeproof results.

Features:
- Send pairing requests to other users
- Accept/decline pairing requests
- Generate "blend" profiles merging personality traits
- Calculate compatibility scores
- Generate combined insights using neural networks

Architecture:
- user_connections: Tracks relationships between users
- connection_blends: Stores merged results and compatibility
- Integration with cringeproof.py for personality data

Usage:
    from user_pairing import send_pairing_request, create_blend

    # User 1 sends request to User 2
    connection_id = send_pairing_request(user_id=1, target_username='bob')

    # User 2 accepts
    accept_pairing_request(connection_id, user_id=2)

    # Generate blend
    blend = create_blend(connection_id)
    print(f"Compatibility: {blend['compatibility_score']}%")
"""

import json
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from database import get_db


# ==============================================================================
# PAIRING REQUESTS
# ==============================================================================

def send_pairing_request(
    user_id: int,
    target_username: str,
    connection_type: str = 'blend'
) -> Optional[int]:
    """
    Send pairing request to another user

    Args:
        user_id: ID of user sending request
        target_username: Username of user to pair with
        connection_type: Type of connection ('blend', 'pair', 'compare')

    Returns:
        connection_id if successful, None if failed
    """
    db = get_db()

    # Get target user ID
    target_user = db.execute(
        'SELECT id FROM users WHERE username = ?',
        (target_username,)
    ).fetchone()

    if not target_user:
        return None

    target_user_id = target_user['id']

    # Can't pair with yourself
    if user_id == target_user_id:
        return None

    # Check if connection already exists (either direction)
    existing = db.execute('''
        SELECT id FROM user_connections
        WHERE ((user_id_1 = ? AND user_id_2 = ?) OR (user_id_1 = ? AND user_id_2 = ?))
        AND connection_type = ?
    ''', (user_id, target_user_id, target_user_id, user_id, connection_type)).fetchone()

    if existing:
        return existing['id']

    # Create new connection
    cursor = db.execute('''
        INSERT INTO user_connections (user_id_1, user_id_2, connection_type, status)
        VALUES (?, ?, ?, 'pending')
    ''', (user_id, target_user_id, connection_type))

    db.commit()

    return cursor.lastrowid


def accept_pairing_request(connection_id: int, user_id: int) -> bool:
    """
    Accept pairing request

    Args:
        connection_id: ID of connection to accept
        user_id: ID of user accepting (must be user_id_2)

    Returns:
        True if accepted, False if not allowed
    """
    db = get_db()

    # Verify user is the recipient
    connection = db.execute('''
        SELECT user_id_2, status FROM user_connections
        WHERE id = ?
    ''', (connection_id,)).fetchone()

    if not connection:
        return False

    if connection['user_id_2'] != user_id:
        return False

    if connection['status'] != 'pending':
        return False

    # Accept connection
    db.execute('''
        UPDATE user_connections
        SET status = 'accepted', updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (connection_id,))

    db.commit()

    return True


def decline_pairing_request(connection_id: int, user_id: int) -> bool:
    """
    Decline pairing request

    Args:
        connection_id: ID of connection to decline
        user_id: ID of user declining (must be user_id_2)

    Returns:
        True if declined, False if not allowed
    """
    db = get_db()

    # Verify user is the recipient
    connection = db.execute('''
        SELECT user_id_2, status FROM user_connections
        WHERE id = ?
    ''', (connection_id,)).fetchone()

    if not connection:
        return False

    if connection['user_id_2'] != user_id:
        return False

    if connection['status'] != 'pending':
        return False

    # Decline connection
    db.execute('''
        UPDATE user_connections
        SET status = 'declined', updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (connection_id,))

    db.commit()

    return True


# ==============================================================================
# BLEND GENERATION
# ==============================================================================

def create_blend(connection_id: int) -> Optional[Dict[str, Any]]:
    """
    Create blend profile for accepted connection

    Merges cringeproof results from both users and calculates compatibility.

    Args:
        connection_id: ID of accepted connection

    Returns:
        Blend data dict or None if failed
    """
    from cringeproof import get_user_latest_result

    db = get_db()

    # Get connection info
    connection = db.execute('''
        SELECT user_id_1, user_id_2, status
        FROM user_connections
        WHERE id = ?
    ''', (connection_id,)).fetchone()

    if not connection or connection['status'] != 'accepted':
        return None

    user1_id = connection['user_id_1']
    user2_id = connection['user_id_2']

    # Get latest cringeproof results for both users
    result1 = get_user_latest_result(user1_id, 'cringeproof')
    result2 = get_user_latest_result(user2_id, 'cringeproof')

    if not result1 or not result2:
        return None

    # Extract score data
    scores1 = result1['result_data']
    scores2 = result2['result_data']

    # Calculate merged scores and compatibility
    blend_data = merge_cringeproof_results(scores1, scores2)
    compatibility = calculate_compatibility(scores1, scores2)
    insights = generate_blend_insights(scores1, scores2, compatibility)

    # Save blend to database
    cursor = db.execute('''
        INSERT OR REPLACE INTO connection_blends
        (connection_id, blend_data, compatibility_score, insights)
        VALUES (?, ?, ?, ?)
    ''', (connection_id, json.dumps(blend_data), compatibility, json.dumps(insights)))

    db.commit()

    return {
        'id': cursor.lastrowid,
        'connection_id': connection_id,
        'blend_data': blend_data,
        'compatibility_score': compatibility,
        'insights': insights,
        'user1_scores': scores1,
        'user2_scores': scores2
    }


def merge_cringeproof_results(scores1: Dict, scores2: Dict) -> Dict[str, Any]:
    """
    Merge two cringeproof score dictionaries

    Creates combined profile showing averaged scores and shared traits.

    Args:
        scores1: First user's cringeproof scores
        scores2: Second user's cringeproof scores

    Returns:
        Merged scores dict
    """
    merged = {
        'category_scores': {},
        'total_score': 0,
        'percentage': 0,
        'level': '',
        'description': ''
    }

    # Merge category scores (average)
    categories1 = scores1.get('category_scores', {})
    categories2 = scores2.get('category_scores', {})

    all_categories = set(categories1.keys()) | set(categories2.keys())

    for category in all_categories:
        score1 = categories1.get(category, 0)
        score2 = categories2.get(category, 0)
        merged['category_scores'][category] = round((score1 + score2) / 2, 1)

    # Calculate merged total
    total1 = scores1.get('total_score', 0)
    total2 = scores2.get('total_score', 0)
    merged['total_score'] = round((total1 + total2) / 2, 1)

    # Calculate merged percentage
    percentage1 = scores1.get('percentage', 0)
    percentage2 = scores2.get('percentage', 0)
    merged['percentage'] = round((percentage1 + percentage2) / 2, 1)

    # Determine blend level
    if merged['percentage'] >= 80:
        merged['level'] = 'Master Blend'
        merged['description'] = 'Your combined personalities create an unstoppable force'
    elif merged['percentage'] >= 60:
        merged['level'] = 'Expert Blend'
        merged['description'] = 'Together you balance each other perfectly'
    elif merged['percentage'] >= 40:
        merged['level'] = 'Intermediate Blend'
        merged['description'] = 'Your differences make you stronger together'
    else:
        merged['level'] = 'Beginner Blend'
        merged['description'] = 'Opposites attract - you bring unique perspectives'

    return merged


def calculate_compatibility(scores1: Dict, scores2: Dict) -> float:
    """
    Calculate compatibility score between two users

    Uses category scores to determine how compatible personalities are.
    Similar to Spotify Blend's taste match percentage.

    Args:
        scores1: First user's cringeproof scores
        scores2: Second user's cringeproof scores

    Returns:
        Compatibility percentage (0-100)
    """
    categories1 = scores1.get('category_scores', {})
    categories2 = scores2.get('category_scores', {})

    if not categories1 or not categories2:
        return 50.0  # Default middle score

    # Calculate similarity across all categories
    similarities = []

    for category in categories1.keys():
        if category in categories2:
            score1 = categories1[category]
            score2 = categories2[category]

            # Calculate percentage difference (inverted to similarity)
            # If scores are same: 100% similarity
            # If scores are opposite: 0% similarity
            max_diff = 100  # Max possible difference in percentage
            actual_diff = abs(score1 - score2)
            similarity = 100 - (actual_diff / max_diff * 100)

            similarities.append(similarity)

    if not similarities:
        return 50.0

    # Average similarity across all categories
    compatibility = sum(similarities) / len(similarities)

    # Add bonus for high combined scores (power couple effect)
    avg_score = (scores1.get('percentage', 0) + scores2.get('percentage', 0)) / 2
    if avg_score >= 80:
        compatibility += 5  # Bonus for both being high performers

    # Cap at 100
    compatibility = min(100, compatibility)

    return round(compatibility, 1)


def generate_blend_insights(scores1: Dict, scores2: Dict, compatibility: float) -> List[str]:
    """
    Generate AI insights about personality blend

    Args:
        scores1: First user's scores
        scores2: Second user's scores
        compatibility: Compatibility percentage

    Returns:
        List of insight strings
    """
    insights = []

    categories1 = scores1.get('category_scores', {})
    categories2 = scores2.get('category_scores', {})

    # Find strongest shared category
    shared_strengths = []
    for category in categories1.keys():
        if category in categories2:
            avg = (categories1[category] + categories2[category]) / 2
            if avg >= 70:
                shared_strengths.append((category, avg))

    if shared_strengths:
        strongest = max(shared_strengths, key=lambda x: x[1])
        insights.append(f"🔥 Both of you excel at {strongest[0].replace('_', ' ')} - a powerful shared strength!")

    # Find complementary differences
    differences = []
    for category in categories1.keys():
        if category in categories2:
            diff = abs(categories1[category] - categories2[category])
            if diff >= 30:
                differences.append((category, diff))

    if differences:
        biggest_diff = max(differences, key=lambda x: x[1])
        insights.append(f"⚖️ You balance each other in {biggest_diff[0].replace('_', ' ')} - your differences create harmony")

    # Compatibility-based insights
    if compatibility >= 80:
        insights.append("💫 Your personalities are highly compatible - you think alike in many ways")
    elif compatibility >= 60:
        insights.append("🤝 You have a great balance of similarity and difference")
    elif compatibility >= 40:
        insights.append("🌈 Your diverse perspectives create a rich dynamic")
    else:
        insights.append("🎭 You're opposites in many ways - this creates interesting contrasts")

    # Overall blend insight
    avg_percentage = (scores1.get('percentage', 0) + scores2.get('percentage', 0)) / 2
    if avg_percentage >= 75:
        insights.append("⭐ Together you form a power duo with exceptional combined abilities")

    return insights


# ==============================================================================
# QUERIES
# ==============================================================================

def get_user_connections(user_id: int, status: Optional[str] = None) -> List[Dict]:
    """
    Get all connections for a user

    Args:
        user_id: User ID to get connections for
        status: Optional filter by status ('pending', 'accepted', etc.)

    Returns:
        List of connection dicts with user info
    """
    db = get_db()

    query = '''
        SELECT
            uc.*,
            CASE
                WHEN uc.user_id_1 = ? THEN u2.username
                ELSE u1.username
            END as partner_username,
            CASE
                WHEN uc.user_id_1 = ? THEN u2.id
                ELSE u1.id
            END as partner_id
        FROM user_connections uc
        JOIN users u1 ON uc.user_id_1 = u1.id
        JOIN users u2 ON uc.user_id_2 = u2.id
        WHERE (uc.user_id_1 = ? OR uc.user_id_2 = ?)
    '''

    params = [user_id, user_id, user_id, user_id]

    if status:
        query += ' AND uc.status = ?'
        params.append(status)

    query += ' ORDER BY uc.created_at DESC'

    rows = db.execute(query, params).fetchall()

    return [dict(row) for row in rows]


def get_blend(connection_id: int) -> Optional[Dict[str, Any]]:
    """
    Get blend data for connection

    Args:
        connection_id: Connection ID

    Returns:
        Blend dict or None
    """
    db = get_db()

    row = db.execute('''
        SELECT * FROM connection_blends
        WHERE connection_id = ?
    ''', (connection_id,)).fetchone()

    if not row:
        return None

    blend = dict(row)
    blend['blend_data'] = json.loads(blend['blend_data'])
    blend['insights'] = json.loads(blend['insights']) if blend['insights'] else []

    return blend


# ==============================================================================
# CLI TESTING
# ==============================================================================

if __name__ == '__main__':
    print("🔗 User Pairing System Test\n")

    # Create test users if needed
    db = get_db()

    # Check if test users exist
    users = db.execute('SELECT id, username FROM users LIMIT 2').fetchall()

    if len(users) < 2:
        print("⚠️  Need at least 2 users in database to test pairing")
        print("   Create users via /signup first")
        exit(1)

    user1 = users[0]
    user2 = users[1]

    print(f"Test users: {user1['username']} (ID {user1['id']}) & {user2['username']} (ID {user2['id']})")

    # Test 1: Send pairing request
    print("\n" + "=" * 70)
    print("TEST 1: Send Pairing Request")
    print("=" * 70)

    connection_id = send_pairing_request(user1['id'], user2['username'])

    if connection_id:
        print(f"✅ Pairing request sent (connection_id: {connection_id})")
    else:
        print("❌ Failed to send pairing request")

    # Test 2: Accept pairing
    print("\n" + "=" * 70)
    print("TEST 2: Accept Pairing Request")
    print("=" * 70)

    if connection_id:
        accepted = accept_pairing_request(connection_id, user2['id'])
        if accepted:
            print("✅ Pairing request accepted")
        else:
            print("❌ Failed to accept pairing")

    # Test 3: Create blend (only works if both users have cringeproof results)
    print("\n" + "=" * 70)
    print("TEST 3: Create Blend")
    print("=" * 70)

    if connection_id:
        blend = create_blend(connection_id)
        if blend:
            print("✅ Blend created successfully")
            print(f"   Compatibility: {blend['compatibility_score']}%")
            print(f"   Level: {blend['blend_data']['level']}")
            print(f"   Insights: {len(blend['insights'])} generated")
        else:
            print("⚠️  Could not create blend (both users need cringeproof results)")

    print("\n✅ Pairing system working!")
