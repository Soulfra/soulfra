#!/bin/bash
# fix_database.sh - One-Command Database Setup
#
# This script:
# 1. Runs database migrations (creates missing tables)
# 2. Creates TestBrand with products
# 3. Generates QR codes
# 4. Shows what was created
# 5. Gives next steps
#
# Usage:
#   bash fix_database.sh

echo "======================================================================"
echo "🔧 Database Setup - One-Command Fix"
echo "======================================================================"

# Step 1: Run migrations
echo ""
echo "======================================================================"
echo "STEP 1: Running Database Migrations"
echo "======================================================================"
echo ""
echo "This will create missing tables (brands, products, qr_scans, etc.)"
echo ""

python3 migrate.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Migration failed! Check error above."
    exit 1
fi

echo ""
echo "✅ Migrations complete!"

# Step 2: Create test brand
echo ""
echo "======================================================================"
echo "STEP 2: Creating TestBrand and Demo Data"
echo "======================================================================"
echo ""

python3 brand_hello_world.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Brand creation failed! Check error above."
    exit 1
fi

echo ""
echo "✅ TestBrand created!"

# Step 3: Show what was created
echo ""
echo "======================================================================"
echo "STEP 3: Verifying Database Contents"
echo "======================================================================"
echo ""

python3 explain_accounts.py

# Step 4: Final instructions
echo ""
echo "======================================================================"
echo "🎉 Database Setup Complete!"
echo "======================================================================"
echo ""
echo "What was created:"
echo "  ✅ Database tables (brands, products, qr_scans, etc.)"
echo "  ✅ TestBrand with 3 products"
echo "  ✅ Test user (demo / password123)"
echo "  ✅ QR code (testbrand-phone-qr.bmp)"
echo "  ✅ URL shortcuts"
echo ""
echo "======================================================================"
echo "🚀 Next Steps"
echo "======================================================================"
echo ""
echo "1. Start server:"
echo "   python3 app.py"
echo ""
echo "2. Open in browser:"
echo "   http://192.168.1.123:5001"
echo ""
echo "3. Login:"
echo "   Username: demo"
echo "   Password: password123"
echo ""
echo "4. Test brand discussion:"
echo "   http://192.168.1.123:5001/brand/discuss/TestBrand"
echo ""
echo "5. Scan QR code with phone:"
echo "   Open testbrand-phone-qr.bmp and scan with phone camera"
echo ""
echo "======================================================================"
echo "📚 Learn More"
echo "======================================================================"
echo ""
echo "Read these files to understand the system:"
echo "  - DATABASE_EXPLAINED.md (simple diagrams)"
echo "  - BRAND_BUILDER_COMPLETE.md (full documentation)"
echo "  - brand_hello_world.py (example code)"
echo ""
echo "Run these scripts to explore:"
echo "  - python3 explain_accounts.py (show what's in database)"
echo "  - python3 test_brand_discussion.py (test all features)"
echo ""
echo "======================================================================"
echo ""
