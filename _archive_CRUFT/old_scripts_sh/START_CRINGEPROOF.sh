#!/bin/bash
# CringeProof Startup Script - Fresh Database (0 users proof-of-concept)
# Uses cringeproof.db (clean 7-table schema)

cd "$(dirname "$0")"

export SOULFRA_DB=cringeproof.db
export FLASK_PORT=5001

echo "============================================"
echo "🚀 Starting CringeProof (Fresh Database)"
echo "============================================"
echo ""
echo "📍 Directory: $(pwd)"
echo "🗄️  Database: $SOULFRA_DB"
echo "🔢 Port: $FLASK_PORT"
echo ""
echo "📊 Database Status:"
USER_COUNT=$(sqlite3 $SOULFRA_DB "SELECT COUNT(*) FROM users;")
SUB_COUNT=$(sqlite3 $SOULFRA_DB "SELECT COUNT(*) FROM subscribers;")
SCAN_COUNT=$(sqlite3 $SOULFRA_DB "SELECT COUNT(*) FROM qr_scans;")
echo "   Users: $USER_COUNT"
echo "   Subscribers: $SUB_COUNT"
echo "   QR Scans: $SCAN_COUNT"
echo ""
echo "🌐 Local Access:"
echo "   http://localhost:$FLASK_PORT"
echo "   http://127.0.0.1:$FLASK_PORT"
echo ""
echo "📊 Admin Dashboards:"
echo "   Database Admin: http://localhost:$FLASK_PORT/admin/database"
echo "   Customer Export: http://localhost:$FLASK_PORT/customers/dashboard"
echo ""
echo "📧 Customer Export:"
echo "   Mailchimp CSV: http://localhost:$FLASK_PORT/api/customers/export/mailchimp"
echo "   SendGrid CSV: http://localhost:$FLASK_PORT/api/customers/export/sendgrid"
echo "   Stats API: http://localhost:$FLASK_PORT/api/customers/stats"
echo ""
echo "⚙️  Batch Workflows:"
echo "   Daily Sync: http://localhost:$FLASK_PORT/api/batch/sync-daily"
echo "   Weekly Report: http://localhost:$FLASK_PORT/api/batch/weekly-report"
echo "   Run All: http://localhost:$FLASK_PORT/api/batch/run-all"
echo ""
echo "📦 Product Tracking:"
echo "   List Products: http://localhost:$FLASK_PORT/api/products/list"
echo "   Top Scanned: http://localhost:$FLASK_PORT/api/products/top-scanned"
echo ""
echo "🎤 Voice Recorder API:"
echo "   http://localhost:$FLASK_PORT/api/simple-voice/save"
echo ""
echo "============================================"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start Flask
python3 app.py
