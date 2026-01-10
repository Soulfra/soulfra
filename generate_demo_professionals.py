#!/usr/bin/env python3
"""
StPetePros Demo Data Generator - Ollama Edition

Generates realistic Tampa Bay professional listings using Ollama.
NO Claude attribution - pure Ollama output.

Usage:
    python3 generate_demo_professionals.py
    python3 generate_demo_professionals.py --count 20
"""

import sqlite3
import argparse
import json
from datetime import datetime
import qrcode
import io
from ollama_smart_client import ask_ollama, get_ollama_status

DB_PATH = "soulfra.db"

CATEGORIES = [
    "plumbing",
    "electrical",
    "hvac",
    "roofing",
    "landscaping",
    "painting",
    "flooring",
    "carpentry",
    "cleaning",
    "pest_control",
    "pool_service",
    "handyman",
    "auto_repair",
    "legal",
    "real_estate",
    "photography"
]

TAMPA_BAY_CITIES = [
    "St. Petersburg",
    "Tampa",
    "Clearwater",
    "Largo",
    "Pinellas Park",
    "Dunedin",
    "Safety Harbor",
    "Gulfport"
]

TAMPA_BAY_ZIPS = [
    "33701", "33702", "33703", "33704", "33705",  # St. Pete
    "33801", "33802", "33803", "33805", "33806",  # Tampa
    "33755", "33756", "33759", "33760", "33761",  # Clearwater
    "33770", "33771", "33773", "33774", "33777"   # Largo, Pinellas Park
]


def generate_professional_data(category, city, zip_code):
    """
    Use Ollama to generate realistic professional data.
    Returns dict with business_name, bio, phone, email, address, website.
    """
    prompt = f"""Generate a realistic {category} business in {city}, FL.

Output ONLY a JSON object with these exact fields (no markdown, no explanation):
{{
  "business_name": "realistic business name",
  "bio": "50-100 word professional bio describing services and experience",
  "phone": "(727) XXX-XXXX format",
  "email": "email@businessname.com",
  "address": "realistic street address",
  "website": "https://businessname.com"
}}

Make it authentic for Tampa Bay area. Use local landmarks or neighborhoods if relevant."""

    print(f"  [AI] Asking Ollama to generate {category} business in {city}...")

    response = ask_ollama(prompt, model="llama3.2:latest")

    if not response:
        print(f"  [WARNING] Ollama failed, using fallback data")
        return generate_fallback_data(category, city, zip_code)

    try:
        # Extract JSON from response (Ollama sometimes wraps it)
        response_clean = response.strip()
        if response_clean.startswith("```"):
            # Remove markdown code blocks
            lines = response_clean.split('\n')
            response_clean = '\n'.join([l for l in lines if not l.startswith('```')])

        # Find JSON object
        start = response_clean.find('{')
        end = response_clean.rfind('}') + 1
        if start != -1 and end > start:
            json_str = response_clean[start:end]
            data = json.loads(json_str)

            # Validate required fields
            required = ['business_name', 'bio', 'phone', 'email', 'address']
            if all(field in data for field in required):
                print(f"  [SUCCESS] Generated: {data['business_name']}")
                return data

        print(f"  [WARNING] Invalid JSON from Ollama, using fallback")
        return generate_fallback_data(category, city, zip_code)

    except json.JSONDecodeError as e:
        print(f"  [WARNING] JSON parse error: {e}, using fallback")
        return generate_fallback_data(category, city, zip_code)


def generate_fallback_data(category, city, zip_code):
    """
    Fallback data when Ollama is unavailable.
    Simple template-based generation.
    """
    category_name = category.replace('_', ' ').title()
    business_name = f"{city} {category_name} Experts"

    return {
        "business_name": business_name,
        "bio": f"Professional {category.replace('_', ' ')} services in {city} and surrounding Tampa Bay areas. Licensed, insured, and committed to quality workmanship. Family-owned and operated with over 15 years of experience serving the community.",
        "phone": f"(727) 555-{str(hash(business_name) % 10000).zfill(4)}",
        "email": f"info@{business_name.lower().replace(' ', '')}.com",
        "address": f"{hash(business_name) % 9999 + 100} Central Ave",
        "website": f"https://{business_name.lower().replace(' ', '')}.com"
    }


def generate_qr_code(professional_id):
    """Generate QR code for professional profile"""
    url = f"https://soulfra.com/stpetepros/professional-{professional_id}.html"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=2
    )
    qr.add_data(url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    qr_img.save(buffer, format='PNG')
    return buffer.getvalue()


def insert_professional(db, professional_data):
    """Insert professional into database and auto-approve"""
    cursor = db.cursor()

    # Insert without QR first to get ID
    cursor.execute('''
        INSERT INTO professionals (
            business_name, category, bio, phone, email,
            address, city, zip_code, website,
            approval_status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        professional_data['business_name'],
        professional_data['category'],
        professional_data['bio'],
        professional_data['phone'],
        professional_data['email'],
        professional_data['address'],
        professional_data['city'],
        professional_data['zip_code'],
        professional_data.get('website', ''),
        'approved',  # Auto-approve demo data
        datetime.now().isoformat()
    ))

    professional_id = cursor.lastrowid
    db.commit()

    # Generate and update QR code
    qr_bytes = generate_qr_code(professional_id)
    cursor.execute('''
        UPDATE professionals
        SET qr_business_card = ?
        WHERE id = ?
    ''', (qr_bytes, professional_id))
    db.commit()

    return professional_id


def generate_demo_professionals(count=15):
    """Generate N demo professionals using Ollama"""
    print(f"\n[BUILD] Generating {count} demo professionals...")
    print(f"[INFO] Using Ollama for realistic business data\n")

    # Check Ollama status
    status = get_ollama_status()
    print(f"[INFO] Ollama: {status['mode']} - {status['message']}\n")

    db = sqlite3.connect(DB_PATH)

    generated = 0
    for i in range(count):
        # Rotate through categories and cities
        category = CATEGORIES[i % len(CATEGORIES)]
        city = TAMPA_BAY_CITIES[i % len(TAMPA_BAY_CITIES)]
        zip_code = TAMPA_BAY_ZIPS[i % len(TAMPA_BAY_ZIPS)]

        print(f"\n[{i+1}/{count}] Generating {category} in {city}...")

        # Generate using Ollama
        pro_data = generate_professional_data(category, city, zip_code)

        # Add metadata
        pro_data['category'] = category
        pro_data['city'] = city
        pro_data['zip_code'] = zip_code

        # Insert into database
        pro_id = insert_professional(db, pro_data)
        print(f"  [SAVE] Saved to database (ID: {pro_id})")

        generated += 1

    db.close()

    print(f"\n[SUCCESS] Generated {generated} professionals!")
    print(f"[INFO] Database: {DB_PATH}")
    print(f"\nNext steps:")
    print(f"  1. Run: python3 build_stpetepros_demo.py")
    print(f"  2. Run: python3 build_stpetepros_demo.py --serve")
    print(f"  3. Deploy to GitHub Pages")


def main():
    parser = argparse.ArgumentParser(description="Generate demo professionals using Ollama")
    parser.add_argument('--count', type=int, default=15, help='Number of professionals to generate')
    args = parser.parse_args()

    generate_demo_professionals(args.count)


if __name__ == "__main__":
    main()
