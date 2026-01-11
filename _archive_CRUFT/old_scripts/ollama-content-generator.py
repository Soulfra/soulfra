#!/usr/bin/env python3
"""
Ollama-Powered Auto-Content Generator

Use Ollama (running on YOUR laptop) to generate business descriptions,
bios, email templates, etc.

NO API keys, NO third-party, all local.

Usage:
    python3 ollama-content-generator.py bio "Joe's Plumbing" plumbing
    python3 ollama-content-generator.py email "Joe's Plumbing"
    python3 ollama-content-generator.py batch-bios   # Generate for all professionals without bios
"""

import sqlite3
import requests
import json
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent / 'soulfra.db'
OLLAMA_URL = 'http://localhost:11434/api/generate'


def call_ollama(prompt, model='llama2'):
    """Call Ollama API (localhost)"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                'model': model,
                'prompt': prompt,
                'stream': False
            },
            timeout=30
        )

        if response.status_code == 200:
            return response.json()['response'].strip()
        else:
            return None

    except Exception as e:
        print(f"❌ Ollama error: {e}")
        print("   Make sure Ollama is running: ollama serve")
        return None


def generate_bio(business_name, category):
    """Generate business bio using Ollama"""

    prompt = f"""Write a brief, professional bio (2-3 sentences) for a local Tampa Bay business:

Business: {business_name}
Category: {category}

The bio should be friendly, professional, and mention that they serve the Tampa Bay area. Do not use quotes or special formatting."""

    print()
    print(f"🤖 Generating bio for {business_name}...")
    print()

    bio = call_ollama(prompt)

    if bio:
        print(f"✅ Generated bio:")
        print()
        print(f"   {bio}")
        print()
        return bio
    else:
        return None


def generate_email_template(business_name):
    """Generate customer email template using Ollama"""

    prompt = f"""Write a brief, friendly email to send to a customer who just signed up for the StPetePros directory.

Business: {business_name}

The email should:
- Thank them for signing up
- Mention their QR code business card is attached
- Explain how to use it
- Keep it under 100 words
- Be warm and professional

Do not include subject line or signature."""

    print()
    print(f"🤖 Generating email for {business_name}...")
    print()

    email = call_ollama(prompt)

    if email:
        print(f"✅ Generated email:")
        print()
        print(email)
        print()
        return email
    else:
        return None


def batch_generate_bios():
    """Generate bios for all professionals that don't have one"""

    print()
    print("=" * 60)
    print("  Batch Generate Bios with Ollama")
    print("=" * 60)
    print()

    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

    # Get professionals without bios
    professionals = db.execute('''
        SELECT id, business_name, category
        FROM professionals
        WHERE (bio IS NULL OR bio = '')
        AND approval_status = 'approved'
        ORDER BY business_name
    ''').fetchall()

    if not professionals:
        print("✅ All professionals already have bios!")
        print()
        db.close()
        return

    print(f"📊 Found {len(professionals)} professionals without bios")
    print()

    confirm = input("Generate bios using Ollama? (y/n): ").lower()
    if confirm != 'y':
        print("Cancelled.")
        print()
        db.close()
        return

    generated = 0

    for prof in professionals:
        bio = generate_bio(prof['business_name'], prof['category'] or 'local business')

        if bio:
            # Save to database
            db.execute(
                'UPDATE professionals SET bio = ? WHERE id = ?',
                (bio, prof['id'])
            )
            db.commit()
            generated += 1
            print(f"   Saved to database")
            print()

        else:
            print(f"   Skipped (Ollama error)")
            print()

    db.close()

    print(f"✅ Generated {generated} bios")
    print()
    print("Next steps:")
    print("  python3 export-to-github-pages.py  # Export updated bios to website")
    print()


def main():
    if len(sys.argv) < 2:
        print()
        print("Usage:")
        print("  python3 ollama-content-generator.py bio \"Business Name\" category")
        print("  python3 ollama-content-generator.py email \"Business Name\"")
        print("  python3 ollama-content-generator.py batch-bios")
        print()
        return

    command = sys.argv[1]

    if command == 'bio':
        if len(sys.argv) < 4:
            print()
            print("❌ Usage: python3 ollama-content-generator.py bio \"Business Name\" category")
            print()
            return

        business_name = sys.argv[2]
        category = sys.argv[3]
        generate_bio(business_name, category)

    elif command == 'email':
        if len(sys.argv) < 3:
            print()
            print("❌ Usage: python3 ollama-content-generator.py email \"Business Name\"")
            print()
            return

        business_name = sys.argv[2]
        generate_email_template(business_name)

    elif command == 'batch-bios':
        batch_generate_bios()

    else:
        print()
        print(f"❌ Unknown command: {command}")
        print()
        print("Valid commands: bio, email, batch-bios")
        print()


if __name__ == '__main__':
    main()
