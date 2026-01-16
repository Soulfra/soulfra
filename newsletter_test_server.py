#!/usr/bin/env python3
"""
Minimal Flask server for newsletter signup + daily quotes
Run: python3 newsletter_test_server.py
"""

from flask import Flask
from flask_cors import CORS
from newsletter_routes import newsletter_bp, init_newsletter_tables
from quote_routes import quote_bp
import os

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'test-secret-key')

# Enable CORS so HTML file can call this server
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Initialize database tables
init_newsletter_tables()

# Register routes
app.register_blueprint(newsletter_bp)
app.register_blueprint(quote_bp)

print("✅ Newsletter + Daily Quotes server ready!")
print("   Newsletter: open generated/frontend_7_20260113_163930.html")
print("   Daily Quote: open generated/daily_quote_20260113.html")
print("   API: http://localhost:5001/api/newsletter/subscribe-public")
print("   API: http://localhost:5001/api/quotes/daily")
print("")

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=True
    )
