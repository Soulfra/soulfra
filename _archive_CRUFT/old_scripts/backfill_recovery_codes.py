#!/usr/bin/env python3
"""
Backfill Recovery Codes for Existing Professionals

Generates BIP-39 style recovery codes for professionals that don't have them yet.

Usage:
    python3 backfill_recovery_codes.py
"""

import sqlite3
from recovery_code_generator import generate_recovery_code

DB_PATH = 'soulfra.db'


def backfill_recovery_codes():
    """Generate recovery codes for all professionals missing them"""
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

    # Get professionals without recovery codes
    professionals = db.execute('''
        SELECT id, business_name, category, recovery_code
        FROM professionals
        WHERE recovery_code IS NULL
        ORDER BY id ASC
    ''').fetchall()

    if not professionals:
        print("✅ All professionals already have recovery codes!")
        db.close()
        return

    print(f"📝 Generating recovery codes for {len(professionals)} professionals...\n")

    for prof in professionals:
        # Generate recovery code
        recovery_code = generate_recovery_code(prof['id'], prof['category'])

        # Update database
        db.execute('''
            UPDATE professionals
            SET recovery_code = ?
            WHERE id = ?
        ''', (recovery_code, prof['id']))

        print(f"✅ Professional #{prof['id']}: {prof['business_name']}")
        print(f"   Recovery Code: {recovery_code}")
        print(f"   Category: {prof['category']}\n")

    db.commit()
    db.close()

    print(f"\n🎉 Successfully generated {len(professionals)} recovery codes!")
    print("\n📧 Next steps:")
    print("  1. Email each professional their recovery code")
    print("  2. They can verify their listing at: http://localhost:5001/verify-professional")
    print("  3. Or on production: https://soulfra.com/verify-professional")


if __name__ == "__main__":
    backfill_recovery_codes()
