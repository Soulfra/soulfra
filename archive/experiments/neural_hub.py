#!/usr/bin/env python3
"""
Neural Communication Hub - Central Message Router

The "brain" that connects all communication channels (email, blog, messages, forum, IRC, relays).
Uses neural networks to classify, route, and process messages across all channels.

Philosophy:
----------
External services route messages through fixed rules.
Our Neural Hub routes through AI classification:
- CalRiven classifier → Technical content goes to dev channels
- TheAuditor classifier → Reviews go to validation channels
- DeathToData classifier → Privacy content goes to secure channels
- Soulfra judge → General content distributed across all

Architecture:
------------
```
Message In → Neural Classification → Route to Channels → Log Decision
    │              │                       │                  │
    │              ▼                       ▼                  ▼
  Email      CalRiven Network        Email/Blog/Forum     Database
  Blog       TheAuditor Network                           Analytics
  Forum      DeathToData Network
  IRC        Soulfra Judge
```

Usage:
    from neural_hub import process_message, get_hub_stats

    # Process a message
    result = process_message(
        content="Check out this Python debugging technique",
        source="email",
        metadata={"from": "user@example.com"}
    )

    # Get hub statistics
    stats = get_hub_stats()
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import secrets


# ==============================================================================
# DATA CLASSES
# ==============================================================================

@dataclass
class Message:
    """Represents a message in the hub"""
    id: Optional[int] = None
    content: str = ""
    source: str = ""  # email, blog, forum, irc, relay
    metadata: Dict[str, Any] = None
    created_at: Optional[str] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


@dataclass
class Classification:
    """Neural network classification result"""
    network_name: str
    score: float
    label: str
    confidence: float


@dataclass
class RoutingDecision:
    """Decision about where to route a message"""
    message_id: int
    target_channels: List[str]
    classifications: List[Classification]
    reason: str
    created_at: str


# ==============================================================================
# DATABASE CONNECTION
# ==============================================================================

def get_db():
    """Get database connection"""
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    return conn


# ==============================================================================
# NEURAL NETWORK INTEGRATION
# ==============================================================================

def classify_message(content: str) -> List[Classification]:
    """
    Classify message using ALL neural networks

    Args:
        content: Message content to classify

    Returns:
        List of classifications from each network
    """
    from neural_network import load_neural_network
    from train_context_networks import (
        extract_technical_features,
        extract_validation_features,
        extract_privacy_features
    )

    classifications = []

    # Try CalRiven (technical) classifier
    try:
        network = load_neural_network('calriven_technical_classifier')
        if network:
            # Create mock post for feature extraction
            mock_post = {'content': content}
            features = extract_technical_features(mock_post)
            prediction = network.forward(features)
            score = float(prediction[0])

            classifications.append(Classification(
                network_name='calriven_technical_classifier',
                score=score,
                label='technical' if score > 0.5 else 'non-technical',
                confidence=abs(score - 0.5) * 2  # 0.5 = low confidence, 1.0/0.0 = high
            ))
    except Exception as e:
        pass  # Network might not be trained yet

    # Try TheAuditor (validation) classifier
    try:
        network = load_neural_network('theauditor_validation_classifier')
        if network:
            mock_post = {'content': content}
            features = extract_validation_features(mock_post)
            prediction = network.forward(features)
            score = float(prediction[0])

            classifications.append(Classification(
                network_name='theauditor_validation_classifier',
                score=score,
                label='validated' if score > 0.5 else 'unvalidated',
                confidence=abs(score - 0.5) * 2
            ))
    except Exception as e:
        pass

    # Try DeathToData (privacy) classifier
    try:
        network = load_neural_network('deathtodata_privacy_classifier')
        if network:
            mock_post = {'content': content}
            features = extract_privacy_features(mock_post)
            prediction = network.forward(features)
            score = float(prediction[0])

            classifications.append(Classification(
                network_name='deathtodata_privacy_classifier',
                score=score,
                label='privacy-focused' if score > 0.5 else 'general',
                confidence=abs(score - 0.5) * 2
            ))
    except Exception as e:
        pass

    # Try Soulfra judge
    try:
        network = load_neural_network('soulfra_judge')
        if network:
            mock_post = {'content': content}
            # Soulfra uses aggregate features
            features = extract_technical_features(mock_post)  # Simplified for now
            prediction = network.forward(features)
            score = float(prediction[0])

            classifications.append(Classification(
                network_name='soulfra_judge',
                score=score,
                label='approved' if score > 0.5 else 'review',
                confidence=abs(score - 0.5) * 2
            ))
    except Exception as e:
        pass

    return classifications


def route_based_on_classification(
    message: Message,
    classifications: List[Classification]
) -> List[str]:
    """
    Determine which channels should receive this message

    Args:
        message: The message to route
        classifications: Neural network classifications

    Returns:
        List of channel names (e.g., ['blog', 'email', 'forum'])
    """
    channels = []

    # Default: all messages go to at least one channel
    if message.source == 'email':
        channels.append('blog')  # Email → Blog post

    elif message.source == 'blog':
        channels.append('email')  # Blog → Email subscribers

    # Neural-based routing
    for classification in classifications:
        # Technical content → Forum + IRC
        if (classification.network_name == 'calriven_technical_classifier' and
            classification.label == 'technical' and
            classification.confidence > 0.7):
            if 'forum' not in channels:
                channels.append('forum')
            if 'irc' not in channels:
                channels.append('irc')

        # Privacy content → Secure channels only
        if (classification.network_name == 'deathtodata_privacy_classifier' and
            classification.label == 'privacy-focused' and
            classification.confidence > 0.7):
            # Don't post privacy content to public IRC
            if 'irc' in channels:
                channels.remove('irc')

        # Soulfra approved → All channels
        if (classification.network_name == 'soulfra_judge' and
            classification.label == 'approved' and
            classification.confidence > 0.8):
            for channel in ['blog', 'email', 'forum']:
                if channel not in channels:
                    channels.append(channel)

    # Remove duplicates and source channel
    channels = list(set(channels))
    if message.source in channels:
        channels.remove(message.source)

    return channels


# ==============================================================================
# CORE HUB FUNCTIONS
# ==============================================================================

def save_message(message: Message) -> int:
    """
    Save message to hub_messages table

    Returns:
        message_id
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO hub_messages (content, source, metadata, created_at)
        VALUES (?, ?, ?, ?)
    ''', (
        message.content,
        message.source,
        json.dumps(message.metadata),
        message.created_at
    ))

    message_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return message_id


def log_routing_decision(decision: RoutingDecision):
    """Log a routing decision to database"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO hub_routing_log
        (message_id, target_channels, classifications, reason, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        decision.message_id,
        json.dumps(decision.target_channels),
        json.dumps([asdict(c) for c in decision.classifications]),
        decision.reason,
        decision.created_at
    ))

    conn.commit()
    conn.close()


def process_message(
    content: str,
    source: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Process a message through the neural hub

    This is the MAIN ENTRY POINT for all messages.

    Args:
        content: Message content
        source: Source channel (email, blog, forum, irc, relay)
        metadata: Additional metadata (from_user, to_user, subject, etc.)

    Returns:
        Dict with:
        - message_id
        - classifications
        - target_channels
        - routing_decision_id
    """
    # Create message object
    message = Message(content=content, source=source, metadata=metadata or {})

    # Save to database
    message_id = save_message(message)
    message.id = message_id

    # Classify using neural networks
    classifications = classify_message(content)

    # Determine routing
    target_channels = route_based_on_classification(message, classifications)

    # Build reason
    if classifications:
        top_classification = max(classifications, key=lambda c: c.confidence)
        reason = f"Routed by {top_classification.network_name}: {top_classification.label} (confidence: {top_classification.confidence:.2f})"
    else:
        reason = f"Default routing: {source} → {target_channels}"

    # Create routing decision
    decision = RoutingDecision(
        message_id=message_id,
        target_channels=target_channels,
        classifications=classifications,
        reason=reason,
        created_at=datetime.now().isoformat()
    )

    # Log the decision
    log_routing_decision(decision)

    return {
        'message_id': message_id,
        'classifications': [asdict(c) for c in classifications],
        'target_channels': target_channels,
        'reason': reason
    }


# ==============================================================================
# ANALYTICS & STATS
# ==============================================================================

def get_hub_stats() -> Dict[str, Any]:
    """Get hub statistics"""
    conn = get_db()
    cursor = conn.cursor()

    # Total messages processed
    cursor.execute('SELECT COUNT(*) FROM hub_messages')
    total_messages = cursor.fetchone()[0]

    # Messages by source
    cursor.execute('''
        SELECT source, COUNT(*) as count
        FROM hub_messages
        GROUP BY source
        ORDER BY count DESC
    ''')
    by_source = {row[0]: row[1] for row in cursor.fetchall()}

    # Routing decisions
    cursor.execute('SELECT COUNT(*) FROM hub_routing_log')
    total_routings = cursor.fetchone()[0]

    # Most common routes
    cursor.execute('''
        SELECT target_channels, COUNT(*) as count
        FROM hub_routing_log
        GROUP BY target_channels
        ORDER BY count DESC
        LIMIT 10
    ''')
    common_routes = [(row[0], row[1]) for row in cursor.fetchall()]

    conn.close()

    return {
        'total_messages': total_messages,
        'by_source': by_source,
        'total_routings': total_routings,
        'common_routes': common_routes
    }


def get_recent_messages(limit: int = 20) -> List[Dict]:
    """Get recent messages with routing info"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            m.id,
            m.content,
            m.source,
            m.metadata,
            m.created_at,
            r.target_channels,
            r.reason
        FROM hub_messages m
        LEFT JOIN hub_routing_log r ON m.id = r.message_id
        ORDER BY m.created_at DESC
        LIMIT ?
    ''', (limit,))

    messages = []
    for row in cursor.fetchall():
        messages.append({
            'id': row[0],
            'content': row[1][:200],  # Truncate for display
            'source': row[2],
            'metadata': json.loads(row[3]) if row[3] else {},
            'created_at': row[4],
            'target_channels': json.loads(row[5]) if row[5] else [],
            'reason': row[6]
        })

    conn.close()
    return messages


# ==============================================================================
# CLI & TESTING
# ==============================================================================

if __name__ == '__main__':
    print("🧠 Neural Communication Hub\n")

    # Test message
    print("Testing message processing...\n")

    result = process_message(
        content="Here's a Python function that implements clean error handling with try/except blocks",
        source="email",
        metadata={"from": "test@example.com", "subject": "Code Review"}
    )

    print(f"Message ID: {result['message_id']}")
    print(f"\nClassifications:")
    for c in result['classifications']:
        print(f"  - {c['network_name']}: {c['label']} (confidence: {c['confidence']:.2f})")

    print(f"\nTarget Channels: {result['target_channels']}")
    print(f"Reason: {result['reason']}")

    print("\n" + "="*70)
    print("HUB STATISTICS")
    print("="*70)

    stats = get_hub_stats()
    print(f"Total Messages: {stats['total_messages']}")
    print(f"By Source: {stats['by_source']}")
    print(f"Total Routings: {stats['total_routings']}")

    print("\n✅ Neural Hub working!")
