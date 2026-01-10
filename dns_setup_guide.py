#!/usr/bin/env python3
"""
DNS Setup Guide for Soulfra

Generates DNS records for custom domain configuration.
Helps users set up:
- A Record (domain → IP address)
- CNAME Record (www → domain)
- TXT Record (verification)
- MX Records (email, optional)

Usage:
    # Generate DNS records for domain
    python3 dns_setup_guide.py --domain myblog.com --ip 123.45.67.89

    # Include email verification
    python3 dns_setup_guide.py --domain myblog.com --ip 123.45.67.89 --email

    # Test current DNS setup
    python3 dns_setup_guide.py --domain myblog.com --test

    # Generate nginx config for domain
    python3 dns_setup_guide.py --domain myblog.com --nginx-config
"""

import argparse
import socket
import sys
import secrets
from pathlib import Path

def generate_verification_token() -> str:
    """Generate verification token for domain ownership"""
    return f"soulfra-verify-{secrets.token_hex(16)}"

def get_server_ip() -> str:
    """Try to detect server's public IP address"""
    try:
        # Try to connect to external service to get public IP
        import urllib.request
        ip = urllib.request.urlopen('https://api.ipify.org').read().decode('utf8')
        return ip
    except:
        return "YOUR.SERVER.IP.HERE"

def print_dns_records(domain: str, ip_address: str, include_email: bool = False):
    """Print DNS records that user should add to their domain registrar"""

    verification_token = generate_verification_token()

    print(f"\n{'='*80}")
    print(f"DNS SETUP GUIDE FOR: {domain}")
    print(f"{'='*80}\n")

    print("📋 Add these DNS records to your domain registrar:\n")
    print("(e.g., Namecheap, GoDaddy, Cloudflare, etc.)\n")

    print(f"{'─'*80}")
    print("1. A RECORD (Point domain to server)")
    print(f"{'─'*80}")
    print(f"   Type:  A")
    print(f"   Host:  @  (or {domain})")
    print(f"   Value: {ip_address}")
    print(f"   TTL:   3600 (1 hour)\n")

    print(f"{'─'*80}")
    print("2. CNAME RECORD (www subdomain)")
    print(f"{'─'*80}")
    print(f"   Type:  CNAME")
    print(f"   Host:  www")
    print(f"   Value: {domain}")
    print(f"   TTL:   3600 (1 hour)\n")

    print(f"{'─'*80}")
    print("3. TXT RECORD (Domain verification)")
    print(f"{'─'*80}")
    print(f"   Type:  TXT")
    print(f"   Host:  _soulfra  (or _soulfra.{domain})")
    print(f"   Value: {verification_token}")
    print(f"   TTL:   3600 (1 hour)\n")

    if include_email:
        print(f"{'─'*80}")
        print("4. MX RECORDS (Email, optional)")
        print(f"{'─'*80}")
        print(f"   Type:     MX")
        print(f"   Host:     @")
        print(f"   Value:    mail.{domain}")
        print(f"   Priority: 10")
        print(f"   TTL:      3600\n")

    print(f"{'='*80}")
    print("WHAT TO DO NEXT")
    print(f"{'='*80}\n")

    print("1. Go to your domain registrar (e.g., Namecheap, GoDaddy)")
    print("2. Find the DNS Management or DNS Settings page")
    print("3. Add the records listed above")
    print("4. Wait 5-30 minutes for DNS propagation")
    print("5. Test with: python3 dns_setup_guide.py --domain {domain} --test\n")

    print(f"💾 Save verification token: {verification_token}\n")

def test_dns_setup(domain: str):
    """Test if DNS is properly configured"""

    print(f"\n{'='*80}")
    print(f"TESTING DNS SETUP FOR: {domain}")
    print(f"{'='*80}\n")

    tests_passed = 0
    tests_failed = 0

    # Test 1: A record (domain resolves to IP)
    print("1. Testing A record (domain → IP)...")
    try:
        ip = socket.gethostbyname(domain)
        print(f"   ✓ {domain} resolves to {ip}")
        tests_passed += 1
    except socket.gaierror:
        print(f"   ✗ {domain} does not resolve to an IP address")
        print(f"      Make sure you added the A record")
        tests_failed += 1

    # Test 2: CNAME record (www subdomain)
    print(f"\n2. Testing CNAME record (www.{domain} → {domain})...")
    try:
        www_ip = socket.gethostbyname(f"www.{domain}")
        print(f"   ✓ www.{domain} resolves to {www_ip}")
        tests_passed += 1
    except socket.gaierror:
        print(f"   ✗ www.{domain} does not resolve")
        print(f"      Make sure you added the CNAME record")
        tests_failed += 1

    # Test 3: TXT record (verification)
    print(f"\n3. Testing TXT record (_soulfra.{domain})...")
    try:
        import dns.resolver
        answers = dns.resolver.resolve(f"_soulfra.{domain}", 'TXT')
        for rdata in answers:
            txt_value = str(rdata).strip('"')
            if txt_value.startswith('soulfra-verify-'):
                print(f"   ✓ Found verification TXT record")
                tests_passed += 1
                break
        else:
            print(f"   ⚠️  TXT record found but doesn't contain soulfra-verify- token")
            tests_failed += 1
    except ImportError:
        print(f"   ⊘ Skipped (requires dnspython: pip install dnspython)")
    except Exception as e:
        print(f"   ✗ No TXT record found")
        print(f"      Make sure you added the TXT record")
        tests_failed += 1

    # Summary
    print(f"\n{'='*80}")
    print(f"TEST RESULTS")
    print(f"{'='*80}")
    print(f"✓ Passed: {tests_passed}")
    print(f"✗ Failed: {tests_failed}")

    if tests_failed == 0:
        print(f"\n🎉 All tests passed! Your domain is configured correctly.")
        print(f"\nNext steps:")
        print(f"1. Update config.py: BASE_URL='https://{domain}'")
        print(f"2. Configure nginx (run with --nginx-config)")
        print(f"3. Set up SSL: sudo certbot --nginx -d {domain} -d www.{domain}")
        return 0
    else:
        print(f"\n⚠️  Some tests failed. DNS changes can take 5-30 minutes to propagate.")
        print(f"   Wait a bit and run this test again.")
        return 1

def generate_nginx_config(domain: str, port: int = 5001):
    """Generate nginx configuration for the domain"""

    config = f"""# Soulfra nginx configuration for {domain}
# Save this to: /etc/nginx/sites-available/{domain}

server {{
    listen 80;
    listen [::]:80;
    server_name {domain} www.{domain};

    # Redirect to HTTPS (after SSL is set up)
    # return 301 https://$host$request_uri;

    # For now, proxy to Flask app
    location / {{
        proxy_pass http://127.0.0.1:{port};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (for real-time features)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }}

    # Serve static files directly (faster)
    location /static {{
        alias /path/to/soulfra-simple/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }}

    # Generated QR codes
    location /qr {{
        alias /path/to/soulfra-simple/static/qr;
        expires 7d;
    }}

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/log/nginx/{domain}-access.log;
    error_log /var/log/nginx/{domain}-error.log;
}}

# HTTPS configuration (uncomment after running certbot)
# server {{
#     listen 443 ssl http2;
#     listen [::]:443 ssl http2;
#     server_name {domain} www.{domain};
#
#     ssl_certificate /etc/letsencrypt/live/{domain}/fullchain.pem;
#     ssl_certificate_key /etc/letsencrypt/live/{domain}/privkey.pem;
#     include /etc/letsencrypt/options-ssl-nginx.conf;
#     ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
#
#     location / {{
#         proxy_pass http://127.0.0.1:{port};
#         proxy_set_header Host $host;
#         proxy_set_header X-Real-IP $remote_addr;
#         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
#         proxy_set_header X-Forwarded-Proto $scheme;
#     }}
#
#     location /static {{
#         alias /path/to/soulfra-simple/static;
#         expires 30d;
#         add_header Cache-Control "public, immutable";
#     }}
# }}
"""

    print(f"\n{'='*80}")
    print(f"NGINX CONFIGURATION FOR: {domain}")
    print(f"{'='*80}\n")
    print(config)

    print(f"{'='*80}")
    print("HOW TO USE THIS CONFIG")
    print(f"{'='*80}\n")

    print(f"1. Save config to file:")
    print(f"   sudo nano /etc/nginx/sites-available/{domain}\n")

    print(f"2. Update the path to your Soulfra installation:")
    print(f"   Replace '/path/to/soulfra-simple' with your actual path\n")

    print(f"3. Enable the site:")
    print(f"   sudo ln -s /etc/nginx/sites-available/{domain} /etc/nginx/sites-enabled/\n")

    print(f"4. Test nginx config:")
    print(f"   sudo nginx -t\n")

    print(f"5. Reload nginx:")
    print(f"   sudo systemctl reload nginx\n")

    print(f"6. Set up SSL with Let's Encrypt:")
    print(f"   sudo certbot --nginx -d {domain} -d www.{domain}\n")

    # Save to file
    config_path = Path(f"{domain}.nginx.conf")
    with open(config_path, 'w') as f:
        f.write(config)

    print(f"✓ Config saved to: {config_path}\n")

def main():
    parser = argparse.ArgumentParser(description="DNS setup guide for Soulfra")
    parser.add_argument('--domain', required=True, help='Your domain name (e.g., myblog.com)')
    parser.add_argument('--ip', help='Server IP address')
    parser.add_argument('--email', action='store_true', help='Include email (MX) records')
    parser.add_argument('--test', action='store_true', help='Test DNS configuration')
    parser.add_argument('--nginx-config', action='store_true', help='Generate nginx configuration')
    parser.add_argument('--port', type=int, default=5001, help='Flask app port (default: 5001)')

    args = parser.parse_args()

    domain = args.domain.strip().lower()

    # Test mode
    if args.test:
        return test_dns_setup(domain)

    # Nginx config mode
    if args.nginx_config:
        generate_nginx_config(domain, args.port)
        return 0

    # DNS records mode
    ip_address = args.ip
    if not ip_address:
        # Try to detect
        ip_address = get_server_ip()
        if ip_address == "YOUR.SERVER.IP.HERE":
            print("⚠️  Could not detect server IP. Please provide with --ip flag")
            return 1

    print_dns_records(domain, ip_address, args.email)

    return 0

if __name__ == "__main__":
    sys.exit(main())
