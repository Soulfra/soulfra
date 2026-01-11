#!/usr/bin/env python3
"""
Email Batch Processor for StPetePros

Processes signup emails in batches, saves to database.
Like you mentioned - "batches or emails" approach.

This is for the simple Venmo/Zelle payment flow where:
1. User pays via Venmo/Zelle
2. User fills form → email sent to you
3. You run this script to import emails into database

Usage:
    python3 email-batch-processor.py

Then it will:
- Read emails from a folder you specify
- Or paste email text directly
- Parse the signup info
- Save to soulfra.db
- Mark as processed
"""

import sqlite3
import re
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / 'soulfra.db'


def get_db():
    """Get database connection"""
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db


def parse_email_text(email_text):
    """
    Parse email form submission text.

    Expected format (from mailto: form):
        business_name=Joe's Plumbing
        category=plumbing
        email=joe@example.com
        phone=(727) 555-1234
        description=Family business...
        payment_method=Venmo
    """
    data = {}

    # Try to parse key=value format
    lines = email_text.strip().split('\n')
    for line in lines:
        if '=' in line:
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()

            if key in ['business_name', 'category', 'email', 'phone', 'description', 'payment_method']:
                data[key] = value

    # Validate required fields
    required = ['business_name', 'email', 'phone']
    missing = [f for f in required if not data.get(f)]

    if missing:
        return None, f"Missing required fields: {', '.join(missing)}"

    return data, None


def save_to_database(data):
    """Save professional to database"""
    db = get_db()

    try:
        cursor = db.execute('''
            INSERT INTO professionals (
                business_name,
                category,
                email,
                phone,
                description,
                approval_status,
                paid,
                payment_method,
                created_at
            ) VALUES (?, ?, ?, ?, ?, 'pending', 0, ?, CURRENT_TIMESTAMP)
        ''', (
            data['business_name'],
            data.get('category', 'other'),
            data['email'],
            data['phone'],
            data.get('description', ''),
            data.get('payment_method', 'unknown')
        ))

        professional_id = cursor.lastrowid
        db.commit()

        return professional_id, None

    except sqlite3.IntegrityError as e:
        return None, f"Database error (may be duplicate): {e}"

    except Exception as e:
        return None, f"Error: {e}"

    finally:
        db.close()


def interactive_mode():
    """Interactive mode - paste emails one at a time"""
    print()
    print("=" * 60)
    print("  StPetePros Email Batch Processor")
    print("=" * 60)
    print()
    print("Paste email text below (Ctrl+D when done, or type 'quit'):")
    print()

    processed = 0
    failed = 0

    while True:
        print("-" * 60)
        print("Paste email text (or 'quit' to exit, 'list' to show all):")
        print()

        lines = []
        try:
            while True:
                line = input()
                if line.lower() == 'quit':
                    print()
                    print(f"✅ Processed {processed} signups, {failed} failed")
                    print()
                    return
                elif line.lower() == 'list':
                    list_signups()
                    break
                lines.append(line)
        except EOFError:
            break

        if not lines:
            continue

        email_text = '\n'.join(lines)

        # Parse email
        data, error = parse_email_text(email_text)

        if error:
            print(f"❌ Error: {error}")
            print()
            failed += 1
            continue

        # Show parsed data
        print()
        print(f"📋 Parsed:")
        print(f"   Business: {data['business_name']}")
        print(f"   Category: {data.get('category', 'other')}")
        print(f"   Email: {data['email']}")
        print(f"   Phone: {data['phone']}")
        print(f"   Payment: {data.get('payment_method', 'unknown')}")
        print()

        # Confirm
        confirm = input("Save to database? (y/n): ").lower()
        if confirm != 'y':
            print("Skipped.")
            print()
            continue

        # Save
        professional_id, error = save_to_database(data)

        if error:
            print(f"❌ {error}")
            print()
            failed += 1
        else:
            print(f"✅ Saved! Professional ID: {professional_id}")
            print()
            processed += 1


def list_signups():
    """List all signups from database"""
    db = get_db()

    signups = db.execute('''
        SELECT id, business_name, email, phone, approval_status, paid, created_at
        FROM professionals
        ORDER BY created_at DESC
        LIMIT 20
    ''').fetchall()

    print()
    print("=" * 60)
    print(f"  Recent Signups (last 20)")
    print("=" * 60)
    print()

    if not signups:
        print("No signups yet.")
        print()
        return

    for signup in signups:
        paid_status = "💰 PAID" if signup['paid'] else "⏳ UNPAID"
        approval_status = {
            'pending': '⏳ PENDING',
            'approved': '✅ APPROVED',
            'rejected': '❌ REJECTED'
        }.get(signup['approval_status'], signup['approval_status'])

        print(f"ID {signup['id']:03d} | {signup['business_name']:30s} | {paid_status} | {approval_status}")
        print(f"        {signup['email']:30s} | {signup['phone']}")
        print(f"        Created: {signup['created_at']}")
        print()

    db.close()


def batch_import_from_folder(folder_path):
    """Import all .txt files from a folder"""
    folder = Path(folder_path)

    if not folder.exists():
        print(f"❌ Folder not found: {folder}")
        return

    files = list(folder.glob('*.txt'))

    if not files:
        print(f"❌ No .txt files found in: {folder}")
        return

    print()
    print(f"📂 Found {len(files)} email files")
    print()

    processed = 0
    failed = 0

    for file in files:
        print(f"Processing: {file.name}...")

        email_text = file.read_text()
        data, error = parse_email_text(email_text)

        if error:
            print(f"  ❌ {error}")
            failed += 1
            continue

        professional_id, error = save_to_database(data)

        if error:
            print(f"  ❌ {error}")
            failed += 1
        else:
            print(f"  ✅ Saved! ID: {professional_id} - {data['business_name']}")
            processed += 1

            # Move to processed folder
            processed_folder = folder / 'processed'
            processed_folder.mkdir(exist_ok=True)
            file.rename(processed_folder / file.name)

    print()
    print(f"✅ Processed {processed} signups, {failed} failed")
    print()


def main():
    import sys

    if len(sys.argv) > 1:
        # Batch import from folder
        folder_path = sys.argv[1]
        batch_import_from_folder(folder_path)
    else:
        # Interactive mode
        interactive_mode()


if __name__ == '__main__':
    main()
