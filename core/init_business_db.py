#!/usr/bin/env python3
"""
Initialize Business QR Database Tables

Run this once to set up the database for the business QR system.
"""

from database import get_db
from vanity_qr import init_vanity_qr_db
from unified_generator import init_unified_content_table

def init_all_business_tables():
    """Initialize all tables needed for business QR system"""

    print("Initializing business QR database tables...")

    # 1. Initialize vanity QR tables
    print("  → Creating vanity_qr_codes table...")
    init_vanity_qr_db()

    # 2. Initialize unified content table
    print("  → Creating unified_content table...")
    init_unified_content_table()

    print("✅ All business tables initialized!")
    print()
    print("You can now:")
    print("  1. Start the server: python3 app.py")
    print("  2. Visit http://localhost:5001/business")
    print("  3. Create your first invoice with QR code!")


if __name__ == '__main__':
    init_all_business_tables()
