#!/usr/bin/env python3
"""
Interactive Docs - DocuSign for Onboarding/Training

Turn documentation into interactive agreements:
- User reads docs (TERMS_OF_SERVICE, PRIVACY_POLICY, etc.)
- Clicks "I Agree" button
- Signature recorded with device fingerprint + timestamp
- Creates record in database
- Like DocuSign but for onboarding/training

Use Cases:
1. Terms of Service: User must read and agree before signup
2. Training Docs: Track who completed which training
3. Policy Acknowledgment: Employees acknowledge company policies
4. Feature Agreements: Users opt-in to new features

Usage:
    from interactive_docs import create_agreement, check_agreement

    # User signs agreement
    create_agreement(
        user_id=1,
        doc_name='TERMS_OF_SERVICE',
        ip_address='192.168.1.100'
    )

    # Check if user agreed
    agreed = check_agreement(user_id=1, doc_name='TERMS_OF_SERVICE')
"""

import sqlite3
import hashlib
import json
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime


def get_db():
    """Get database connection"""
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    return conn


def init_doc_agreements_tables():
    """Initialize document agreements tables"""
    db = get_db()

    # Create doc_agreements table
    db.execute('''
        CREATE TABLE IF NOT EXISTS doc_agreements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            doc_name TEXT NOT NULL,
            doc_version TEXT DEFAULT '1.0',
            doc_hash TEXT,
            agreed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            user_agent TEXT,
            device_fingerprint TEXT,
            signature TEXT,
            metadata TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # Create doc_versions table
    db.execute('''
        CREATE TABLE IF NOT EXISTS doc_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_name TEXT NOT NULL,
            version TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            content TEXT,
            file_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            active BOOLEAN DEFAULT 1,
            UNIQUE(doc_name, version)
        )
    ''')

    # Create indexes
    db.execute('''
        CREATE INDEX IF NOT EXISTS idx_agreements_user
        ON doc_agreements(user_id, doc_name)
    ''')

    db.execute('''
        CREATE INDEX IF NOT EXISTS idx_agreements_doc
        ON doc_agreements(doc_name, doc_version)
    ''')

    db.commit()
    db.close()


def register_document(doc_name: str, file_path: str, version: str = '1.0') -> str:
    """
    Register document version in database

    Args:
        doc_name: Document name (e.g., 'TERMS_OF_SERVICE')
        file_path: Path to markdown file
        version: Version string

    Returns:
        content_hash: SHA-256 hash of document
    """
    init_doc_agreements_tables()

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Document not found: {file_path}")

    # Read content
    content = path.read_text()

    # Calculate hash
    content_hash = hashlib.sha256(content.encode()).hexdigest()

    db = get_db()

    # Check if version exists
    existing = db.execute('''
        SELECT id FROM doc_versions
        WHERE doc_name = ? AND version = ?
    ''', (doc_name, version)).fetchone()

    if existing:
        # Update existing
        db.execute('''
            UPDATE doc_versions
            SET content_hash = ?,
                content = ?,
                file_path = ?
            WHERE doc_name = ? AND version = ?
        ''', (content_hash, content, str(path), doc_name, version))
    else:
        # Insert new
        db.execute('''
            INSERT INTO doc_versions (
                doc_name, version, content_hash, content, file_path
            ) VALUES (?, ?, ?, ?, ?)
        ''', (doc_name, version, content_hash, content, str(path)))

    db.commit()
    db.close()

    print(f"✓ Registered document: {doc_name} v{version}")
    print(f"  Hash: {content_hash[:16]}...")

    return content_hash


def create_agreement(user_id: Optional[int], doc_name: str,
                    ip_address: str, user_agent: str = None,
                    username: str = None, version: str = '1.0',
                    metadata: Dict = None) -> int:
    """
    Create agreement record (user "signs" document)

    Args:
        user_id: User ID (optional for anonymous)
        doc_name: Document name
        ip_address: IP address of signer
        user_agent: Browser user agent
        username: Username (if not logged in)
        version: Document version
        metadata: Optional metadata dict

    Returns:
        agreement_id: ID of agreement record
    """
    init_doc_agreements_tables()

    db = get_db()

    # Get document hash
    doc = db.execute('''
        SELECT content_hash FROM doc_versions
        WHERE doc_name = ? AND version = ?
    ''', (doc_name, version)).fetchone()

    doc_hash = doc['content_hash'] if doc else None

    # Create device fingerprint
    fingerprint_data = {
        'ip': ip_address,
        'user_agent': user_agent or '',
        'timestamp': datetime.now().isoformat()
    }
    fingerprint = hashlib.sha256(
        json.dumps(fingerprint_data, sort_keys=True).encode()
    ).hexdigest()

    # Create signature (hash of user + doc + timestamp)
    signature_data = {
        'user_id': user_id,
        'username': username,
        'doc_name': doc_name,
        'doc_version': version,
        'doc_hash': doc_hash,
        'timestamp': datetime.now().isoformat(),
        'ip': ip_address
    }
    signature = hashlib.sha256(
        json.dumps(signature_data, sort_keys=True).encode()
    ).hexdigest()

    # Insert agreement
    cursor = db.execute('''
        INSERT INTO doc_agreements (
            user_id, username, doc_name, doc_version, doc_hash,
            ip_address, user_agent, device_fingerprint,
            signature, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id,
        username,
        doc_name,
        version,
        doc_hash,
        ip_address,
        user_agent,
        fingerprint,
        signature,
        json.dumps(metadata) if metadata else None
    ))

    agreement_id = cursor.lastrowid
    db.commit()
    db.close()

    print(f"✓ Agreement created: {doc_name} v{version}")
    print(f"  User: {username or user_id or 'anonymous'}")
    print(f"  Signature: {signature[:16]}...")

    return agreement_id


def check_agreement(user_id: Optional[int], doc_name: str,
                   version: Optional[str] = None, username: Optional[str] = None) -> bool:
    """
    Check if user has agreed to document

    Args:
        user_id: User ID
        doc_name: Document name
        version: Specific version (or None for any)
        username: Username (if no user_id)

    Returns:
        True if user agreed, False otherwise
    """
    init_doc_agreements_tables()

    db = get_db()

    if version:
        query = '''
            SELECT id FROM doc_agreements
            WHERE (user_id = ? OR username = ?)
            AND doc_name = ?
            AND doc_version = ?
        '''
        params = (user_id, username, doc_name, version)
    else:
        query = '''
            SELECT id FROM doc_agreements
            WHERE (user_id = ? OR username = ?)
            AND doc_name = ?
        '''
        params = (user_id, username, doc_name)

    result = db.execute(query, params).fetchone()
    db.close()

    return result is not None


def get_user_agreements(user_id: Optional[int] = None,
                       username: Optional[str] = None) -> List[Dict]:
    """Get all agreements for user"""
    init_doc_agreements_tables()

    db = get_db()

    rows = db.execute('''
        SELECT * FROM doc_agreements
        WHERE user_id = ? OR username = ?
        ORDER BY agreed_at DESC
    ''', (user_id, username)).fetchall()

    db.close()

    return [dict(row) for row in rows]


def get_document_signers(doc_name: str, version: Optional[str] = None) -> List[Dict]:
    """Get all users who signed a document"""
    init_doc_agreements_tables()

    db = get_db()

    if version:
        rows = db.execute('''
            SELECT * FROM doc_agreements
            WHERE doc_name = ? AND doc_version = ?
            ORDER BY agreed_at DESC
        ''', (doc_name, version)).fetchall()
    else:
        rows = db.execute('''
            SELECT * FROM doc_agreements
            WHERE doc_name = ?
            ORDER BY agreed_at DESC
        ''', (doc_name,)).fetchall()

    db.close()

    return [dict(row) for row in rows]


def get_agreement_stats() -> Dict:
    """Get statistics about agreements"""
    init_doc_agreements_tables()

    db = get_db()

    stats = {}

    # Total agreements
    stats['total_agreements'] = db.execute(
        'SELECT COUNT(*) as count FROM doc_agreements'
    ).fetchone()['count']

    # Unique users
    stats['unique_users'] = db.execute('''
        SELECT COUNT(DISTINCT COALESCE(user_id, username)) as count
        FROM doc_agreements
    ''').fetchone()['count']

    # Unique documents
    stats['unique_documents'] = db.execute('''
        SELECT COUNT(DISTINCT doc_name) as count
        FROM doc_agreements
    ''').fetchone()['count']

    # Most agreed document
    most_agreed = db.execute('''
        SELECT doc_name, COUNT(*) as count
        FROM doc_agreements
        GROUP BY doc_name
        ORDER BY count DESC
        LIMIT 1
    ''').fetchone()

    if most_agreed:
        stats['most_agreed_doc'] = {
            'name': most_agreed['doc_name'],
            'count': most_agreed['count']
        }

    db.close()

    return stats


# CLI for testing
if __name__ == '__main__':
    import sys

    print("Interactive Docs - DocuSign for Onboarding\n")

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'init':
            # Initialize tables
            init_doc_agreements_tables()
            print("✓ Document agreement tables initialized")

        elif command == 'register' and len(sys.argv) >= 4:
            # Register document
            doc_name = sys.argv[2]
            file_path = sys.argv[3]
            version = sys.argv[4] if len(sys.argv) > 4 else '1.0'

            content_hash = register_document(doc_name, file_path, version)
            print(f"✓ Document registered: {doc_name} v{version}")

        elif command == 'sign' and len(sys.argv) >= 4:
            # Sign document
            doc_name = sys.argv[2]
            username = sys.argv[3]
            ip = sys.argv[4] if len(sys.argv) > 4 else '127.0.0.1'

            agreement_id = create_agreement(
                user_id=None,
                doc_name=doc_name,
                username=username,
                ip_address=ip,
                user_agent='CLI'
            )

            print(f"✓ Document signed (Agreement ID: {agreement_id})")

        elif command == 'check' and len(sys.argv) >= 4:
            # Check agreement
            doc_name = sys.argv[2]
            username = sys.argv[3]

            agreed = check_agreement(None, doc_name, username=username)

            if agreed:
                print(f"✓ {username} has agreed to {doc_name}")
            else:
                print(f"✗ {username} has NOT agreed to {doc_name}")

        elif command == 'list-user' and len(sys.argv) >= 3:
            # List user agreements
            username = sys.argv[2]
            agreements = get_user_agreements(username=username)

            if agreements:
                print(f"Agreements for {username}:\n")
                for agr in agreements:
                    print(f"• {agr['doc_name']} v{agr['doc_version']}")
                    print(f"  Signed: {agr['agreed_at']}")
                    print(f"  Signature: {agr['signature'][:16]}...")
                    print()
            else:
                print(f"No agreements for {username}")

        elif command == 'list-doc' and len(sys.argv) >= 3:
            # List document signers
            doc_name = sys.argv[2]
            signers = get_document_signers(doc_name)

            if signers:
                print(f"Signers of {doc_name}:\n")
                for signer in signers:
                    print(f"• {signer['username'] or f'User #{signer[\"user_id\"]}'}")
                    print(f"  Signed: {signer['agreed_at']}")
                    print(f"  IP: {signer['ip_address']}")
                    print()
            else:
                print(f"No signers for {doc_name}")

        elif command == 'stats':
            # Show stats
            stats = get_agreement_stats()

            print("Agreement Statistics:\n")
            print(f"  Total agreements: {stats['total_agreements']}")
            print(f"  Unique users: {stats['unique_users']}")
            print(f"  Unique documents: {stats['unique_documents']}")

            if 'most_agreed_doc' in stats:
                print(f"\n  Most agreed document:")
                print(f"    {stats['most_agreed_doc']['name']}")
                print(f"    ({stats['most_agreed_doc']['count']} signatures)")

        else:
            print("Unknown command")

    else:
        print("Interactive Docs Commands:\n")
        print("  python3 interactive_docs.py init")
        print("      Initialize tables\n")
        print("  python3 interactive_docs.py register <doc_name> <file_path> [version]")
        print("      Register document\n")
        print("  python3 interactive_docs.py sign <doc_name> <username> [ip]")
        print("      Sign document\n")
        print("  python3 interactive_docs.py check <doc_name> <username>")
        print("      Check if user signed\n")
        print("  python3 interactive_docs.py list-user <username>")
        print("      List user's agreements\n")
        print("  python3 interactive_docs.py list-doc <doc_name>")
        print("      List document signers\n")
        print("  python3 interactive_docs.py stats")
        print("      Show statistics\n")
        print("\nExample:")
        print("  python3 interactive_docs.py register TERMS_OF_SERVICE ENCRYPTION_TIERS.md 1.0")
        print("  python3 interactive_docs.py sign TERMS_OF_SERVICE john 192.168.1.100")
        print("  python3 interactive_docs.py check TERMS_OF_SERVICE john")
