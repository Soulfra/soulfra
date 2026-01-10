#!/usr/bin/env python3
"""
Lineage System - Git for QR Scans (Zero Dependencies)

Track QR scan chains like Git tracks commits!

Philosophy:
----------
Every scan is a "commit" in the lineage tree.
- Root scan = initial scan (no parent)
- Child scan = scan that came from sharing a QR code
- Lineage hash = SHA256(parent_hash + current_scan + user + timestamp)

This creates an unforgeable chain (like blockchain/git):
- Can't fake lineage (hash includes parent)
- Can track "who recruited who"
- Build knowledge graphs from scan relationships
- Each UPC/QR digit = position in lineage tree

Example Tree:
```
Root Scan (ABC)
  ├─ Child 1 (DEF) - User shared QR
  │   ├─ Grandchild 1 (GHI)
  │   └─ Grandchild 2 (JKL)
  └─ Child 2 (MNO) - User shared QR
      └─ Grandchild 3 (PQR)
```

UPC Encoding:
- Digit 1-3: Root scan ID
- Digit 4-6: Generation number (how deep in tree)
- Digit 7-12: Unique scan hash

Usage:
    # Create root lineage
    python3 lineage_system.py --create-root --user alice

    # Add child scan
    python3 lineage_system.py --create-child --parent ABC123 --user bob

    # Show lineage tree
    python3 lineage_system.py --tree ABC123

    # Export lineage
    python3 lineage_system.py --export ABC123
"""

import sqlite3
import hashlib
import json
import time
from datetime import datetime
from typing import Dict, List, Optional


# ==============================================================================
# LINEAGE HASHING (Like Git Commits)
# ==============================================================================

def generate_lineage_hash(parent_hash: Optional[str], scan_data: Dict) -> str:
    """
    Generate lineage hash (like git commit hash)

    Args:
        parent_hash: Hash of parent scan (None for root)
        scan_data: Current scan data (user, timestamp, metadata)

    Returns:
        SHA256 hash (first 12 chars for UPC compatibility)
    """
    # Build data string
    data_parts = [
        parent_hash or 'ROOT',
        scan_data.get('user_id', 'anonymous'),
        str(scan_data.get('timestamp', int(time.time()))),
        scan_data.get('qr_code_id', ''),
        scan_data.get('metadata', '{}')
    ]

    data_string = '|'.join(str(p) for p in data_parts)

    # Hash it
    full_hash = hashlib.sha256(data_string.encode()).hexdigest()

    # Return first 12 chars (UPC compatible)
    return full_hash[:12]


def generate_upc_from_lineage(lineage_hash: str, generation: int, root_id: int) -> str:
    """
    Generate UPC code from lineage info

    Format: RRRGGGHHHHHH
    - RRR: Root scan ID (3 digits)
    - GGG: Generation (3 digits, 000-999)
    - HHHHHH: Lineage hash (6 hex chars)

    Args:
        lineage_hash: Lineage hash
        generation: Generation number (0 = root, 1 = child, etc.)
        root_id: Root scan ID

    Returns:
        12-digit UPC
    """
    root_part = str(root_id).zfill(3)
    generation_part = str(generation).zfill(3)
    hash_part = lineage_hash[:6]

    upc = root_part + generation_part + hash_part

    return upc.upper()


# ==============================================================================
# DATABASE FUNCTIONS
# ==============================================================================

def create_lineage_tables():
    """Create lineage tracking tables"""
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    # Lineage table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scan_lineage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_id INTEGER NOT NULL,
            lineage_hash TEXT UNIQUE NOT NULL,
            parent_lineage_hash TEXT,
            generation INTEGER DEFAULT 0,
            root_scan_id INTEGER,
            upc_code TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT,
            FOREIGN KEY (scan_id) REFERENCES qr_scans(id)
        )
    ''')

    # Lineage relationships (adjacency list)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lineage_relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_hash TEXT NOT NULL,
            child_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(parent_hash, child_hash)
        )
    ''')

    conn.commit()
    conn.close()

    print("✅ Lineage tables created")


def create_root_lineage(qr_code_id: int, user_id: Optional[int] = None, metadata: Dict = None) -> Dict:
    """
    Create root lineage (first scan in chain)

    Args:
        qr_code_id: QR code that was scanned
        user_id: User who scanned (optional)
        metadata: Additional metadata

    Returns:
        Lineage info dict
    """
    scan_data = {
        'user_id': user_id,
        'timestamp': int(time.time()),
        'qr_code_id': qr_code_id,
        'metadata': json.dumps(metadata or {})
    }

    # Generate lineage hash (no parent = ROOT)
    lineage_hash = generate_lineage_hash(None, scan_data)

    # Create scan record
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO qr_scans (qr_code_id, scanned_at, ip_address)
        VALUES (?, ?, ?)
    ''', (qr_code_id, datetime.now().isoformat(), 'system'))

    scan_id = cursor.lastrowid

    # Generate UPC
    upc = generate_upc_from_lineage(lineage_hash, 0, scan_id)

    # Create lineage record
    cursor.execute('''
        INSERT INTO scan_lineage (
            scan_id, lineage_hash, parent_lineage_hash,
            generation, root_scan_id, upc_code, metadata
        ) VALUES (?, ?, NULL, 0, ?, ?, ?)
    ''', (scan_id, lineage_hash, scan_id, upc, scan_data['metadata']))

    conn.commit()
    conn.close()

    print(f"✅ Created root lineage")
    print(f"   Lineage Hash: {lineage_hash}")
    print(f"   UPC: {upc}")
    print(f"   Scan ID: {scan_id}")

    return {
        'scan_id': scan_id,
        'lineage_hash': lineage_hash,
        'upc_code': upc,
        'generation': 0
    }


def create_child_lineage(parent_lineage_hash: str, qr_code_id: int,
                        user_id: Optional[int] = None, metadata: Dict = None) -> Dict:
    """
    Create child lineage (scan from shared QR)

    Args:
        parent_lineage_hash: Parent's lineage hash
        qr_code_id: QR code that was scanned
        user_id: User who scanned
        metadata: Additional metadata

    Returns:
        Lineage info dict
    """
    # Get parent lineage
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM scan_lineage
        WHERE lineage_hash = ?
    ''', (parent_lineage_hash,))

    parent = cursor.fetchone()

    if not parent:
        conn.close()
        raise ValueError(f"Parent lineage {parent_lineage_hash} not found")

    parent = dict(parent)

    # Generate child lineage hash
    scan_data = {
        'user_id': user_id,
        'timestamp': int(time.time()),
        'qr_code_id': qr_code_id,
        'metadata': json.dumps(metadata or {})
    }

    lineage_hash = generate_lineage_hash(parent_lineage_hash, scan_data)

    # Create scan record
    cursor.execute('''
        INSERT INTO qr_scans (
            qr_code_id, scanned_at, ip_address, previous_scan_id
        ) VALUES (?, ?, ?, ?)
    ''', (qr_code_id, datetime.now().isoformat(), 'system', parent['scan_id']))

    scan_id = cursor.lastrowid

    # Calculate generation
    generation = parent['generation'] + 1

    # Generate UPC
    upc = generate_upc_from_lineage(lineage_hash, generation, parent['root_scan_id'])

    # Create lineage record
    cursor.execute('''
        INSERT INTO scan_lineage (
            scan_id, lineage_hash, parent_lineage_hash,
            generation, root_scan_id, upc_code, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (scan_id, lineage_hash, parent_lineage_hash, generation,
          parent['root_scan_id'], upc, scan_data['metadata']))

    # Create relationship
    cursor.execute('''
        INSERT INTO lineage_relationships (parent_hash, child_hash)
        VALUES (?, ?)
    ''', (parent_lineage_hash, lineage_hash))

    conn.commit()
    conn.close()

    print(f"✅ Created child lineage")
    print(f"   Parent: {parent_lineage_hash}")
    print(f"   Child: {lineage_hash}")
    print(f"   Generation: {generation}")
    print(f"   UPC: {upc}")

    return {
        'scan_id': scan_id,
        'lineage_hash': lineage_hash,
        'parent_lineage_hash': parent_lineage_hash,
        'upc_code': upc,
        'generation': generation
    }


def get_lineage_children(lineage_hash: str) -> List[Dict]:
    """Get all children of a lineage"""
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT sl.* FROM scan_lineage sl
        JOIN lineage_relationships lr ON sl.lineage_hash = lr.child_hash
        WHERE lr.parent_hash = ?
        ORDER BY sl.created_at
    ''', (lineage_hash,))

    children = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return children


def get_lineage_tree(root_hash: str, max_depth: int = 10) -> Dict:
    """
    Build lineage tree recursively

    Args:
        root_hash: Root lineage hash
        max_depth: Maximum depth to traverse

    Returns:
        Tree dict
    """
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM scan_lineage WHERE lineage_hash = ?', (root_hash,))
    node = cursor.fetchone()

    if not node:
        conn.close()
        return None

    node = dict(node)
    conn.close()

    # Build tree
    tree = {
        'lineage_hash': node['lineage_hash'],
        'upc_code': node['upc_code'],
        'generation': node['generation'],
        'scan_id': node['scan_id'],
        'children': []
    }

    if max_depth > 0:
        children = get_lineage_children(root_hash)
        for child in children:
            child_tree = get_lineage_tree(child['lineage_hash'], max_depth - 1)
            if child_tree:
                tree['children'].append(child_tree)

    return tree


# ==============================================================================
# VISUALIZATION
# ==============================================================================

def print_lineage_tree(tree: Dict, indent: int = 0, is_last: bool = True):
    """Print lineage tree as ASCII art"""
    if not tree:
        return

    # Print current node
    prefix = '  ' * indent
    if indent > 0:
        prefix += '└─ ' if is_last else '├─ '

    print(f"{prefix}{tree['upc_code']} (Gen {tree['generation']})")

    # Print children
    children = tree.get('children', [])
    for i, child in enumerate(children):
        is_last_child = (i == len(children) - 1)
        print_lineage_tree(child, indent + 1, is_last_child)


def export_lineage_json(root_hash: str, output_path: str = 'lineage_export.json'):
    """Export lineage tree as JSON"""
    tree = get_lineage_tree(root_hash)

    if not tree:
        print(f"❌ Lineage {root_hash} not found")
        return

    with open(output_path, 'w') as f:
        json.dump(tree, f, indent=2)

    print(f"✅ Lineage exported to {output_path}")


# ==============================================================================
# CLI
# ==============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Lineage System - Git for QR Scans')
    parser.add_argument('--init', action='store_true', help='Initialize lineage tables')
    parser.add_argument('--create-root', action='store_true', help='Create root lineage')
    parser.add_argument('--create-child', action='store_true', help='Create child lineage')
    parser.add_argument('--parent', type=str, help='Parent lineage hash')
    parser.add_argument('--qr-code', type=int, default=1, help='QR code ID')
    parser.add_argument('--user', type=int, help='User ID')
    parser.add_argument('--tree', type=str, help='Show lineage tree')
    parser.add_argument('--export', type=str, help='Export lineage to JSON')

    args = parser.parse_args()

    if args.init:
        create_lineage_tables()

    elif args.create_root:
        result = create_root_lineage(args.qr_code, args.user)

        print()
        print("=" * 70)
        print("✅ ROOT LINEAGE CREATED")
        print("=" * 70)
        print(f"UPC Code: {result['upc_code']}")
        print(f"Lineage Hash: {result['lineage_hash']}")

    elif args.create_child:
        if not args.parent:
            print("❌ --parent required for child lineage")
            exit(1)

        result = create_child_lineage(args.parent, args.qr_code, args.user)

        print()
        print("=" * 70)
        print("✅ CHILD LINEAGE CREATED")
        print("=" * 70)
        print(f"UPC Code: {result['upc_code']}")
        print(f"Generation: {result['generation']}")

    elif args.tree:
        tree = get_lineage_tree(args.tree)

        if tree:
            print()
            print("=" * 70)
            print(f"LINEAGE TREE: {args.tree}")
            print("=" * 70)
            print()
            print_lineage_tree(tree)
        else:
            print(f"❌ Lineage {args.tree} not found")

    elif args.export:
        export_lineage_json(args.export)

    else:
        print("Lineage System - Git for QR Scans")
        print()
        print("Usage:")
        print("  --init                          Initialize tables")
        print("  --create-root --qr-code 1       Create root lineage")
        print("  --create-child --parent HASH    Create child lineage")
        print("  --tree HASH                     Show lineage tree")
        print("  --export HASH                   Export lineage to JSON")
