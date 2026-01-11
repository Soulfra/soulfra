#!/usr/bin/env python3
"""Test gallery routes integration with Flask app"""

from gallery_routes import register_gallery_routes
from flask import Flask

# Create test app
app = Flask(__name__)
app.secret_key = 'test-secret-key'

# Register gallery routes
register_gallery_routes(app)

# Check what routes were added
print('✅ Gallery routes registered successfully')
print('\nRoutes added:')
for rule in app.url_map.iter_rules():
    rule_str = str(rule)
    if any(keyword in rule_str.lower() for keyword in ['gallery', 'dm', 'qr', 'track']):
        print(f'  {rule.rule} -> {rule.endpoint}')

print('\n✅ Integration test passed!')
