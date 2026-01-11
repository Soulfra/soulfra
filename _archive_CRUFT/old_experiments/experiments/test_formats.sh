#!/bin/bash
# Test all output formats for the multi-format API

echo "=========================================="
echo "Multi-Format API Testing"
echo "Testing: http://localhost:8888/api/classify-color"
echo "=========================================="
echo ""

# Test data
TEST_DATA='{"r":255,"g":0,"b":0}'
URL="http://localhost:8888/api/classify-color"

echo "Test Data: RGB(255, 0, 0) - Red (should be WARM)"
echo ""

# Test 1: JSON (default)
echo "----------------------------------------"
echo "1. JSON FORMAT (default)"
echo "----------------------------------------"
curl -s -X POST "$URL?format=json" \
  -H "Content-Type: application/json" \
  -d "$TEST_DATA" | head -20
echo ""
echo ""

# Test 2: CSV
echo "----------------------------------------"
echo "2. CSV FORMAT (spreadsheets)"
echo "----------------------------------------"
curl -s -X POST "$URL?format=csv" \
  -H "Content-Type: application/json" \
  -d "$TEST_DATA"
echo ""
echo ""

# Test 3: TXT
echo "----------------------------------------"
echo "3. TXT FORMAT (human-readable)"
echo "----------------------------------------"
curl -s -X POST "$URL?format=txt" \
  -H "Content-Type: application/json" \
  -d "$TEST_DATA"
echo ""
echo ""

# Test 4: HTML
echo "----------------------------------------"
echo "4. HTML FORMAT (styled card)"
echo "----------------------------------------"
curl -s -X POST "$URL?format=html" \
  -H "Content-Type: application/json" \
  -d "$TEST_DATA" | head -30
echo ""
echo ""

# Test 5: RTF
echo "----------------------------------------"
echo "5. RTF FORMAT (word processors)"
echo "----------------------------------------"
curl -s -X POST "$URL?format=rtf" \
  -H "Content-Type: application/json" \
  -d "$TEST_DATA" | head -20
echo ""
echo ""

# Test 6: Binary
echo "----------------------------------------"
echo "6. BINARY FORMAT (efficient storage)"
echo "----------------------------------------"
echo "Hex dump:"
curl -s -X POST "$URL?format=binary" \
  -H "Content-Type: application/json" \
  -d "$TEST_DATA" | xxd
echo ""
echo "Size:"
curl -s -X POST "$URL?format=binary" \
  -H "Content-Type: application/json" \
  -d "$TEST_DATA" | wc -c | xargs echo "bytes"
echo ""
echo ""

# Test different color
echo "=========================================="
echo "Testing Blue Color"
echo "=========================================="
echo ""

TEST_DATA_BLUE='{"r":0,"g":0,"b":255}'

echo "Test Data: RGB(0, 0, 255) - Blue (should be COOL)"
echo ""

echo "----------------------------------------"
echo "JSON Output:"
echo "----------------------------------------"
curl -s -X POST "$URL?format=json" \
  -H "Content-Type: application/json" \
  -d "$TEST_DATA_BLUE" | grep -E "(prediction|confidence)" | head -5
echo ""
echo ""

echo "----------------------------------------"
echo "CSV Output:"
echo "----------------------------------------"
curl -s -X POST "$URL?format=csv" \
  -H "Content-Type: application/json" \
  -d "$TEST_DATA_BLUE" | cut -d',' -f1-4
echo ""
echo ""

# Summary
echo "=========================================="
echo "SUMMARY"
echo "=========================================="
echo ""
echo "✅ All 6 formats tested:"
echo "   1. JSON   - Machine-readable structured data"
echo "   2. CSV    - Spreadsheet-compatible format"
echo "   3. TXT    - Human-readable plain text"
echo "   4. HTML   - Browser-ready styled cards"
echo "   5. RTF    - Word processor compatible"
echo "   6. Binary - Compact binary format"
echo ""
echo "All formats use ZERO external dependencies!"
echo "Pure Python stdlib: json, struct, StringIO"
echo ""
echo "Like a prism splitting white light into a spectrum! 🌈"
echo ""
