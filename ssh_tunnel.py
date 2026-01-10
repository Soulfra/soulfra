#!/usr/bin/env python3
"""
SSH Tunnel - FREE Public Hosting (No ngrok Needed!)
===================================================

Provides FREE alternatives to ngrok using SSH reverse tunneling:
- serveo.net (instant HTTPS, no signup)
- localhost.run (instant HTTPS, no signup)
- Cloudflare Tunnel (free subdomain)
- Your own VPS (DigitalOcean $5/month)

Usage:
    python3 ssh_tunnel.py serveo
    python3 ssh_tunnel.py localhost
    python3 ssh_tunnel.py cloudflare
    python3 ssh_tunnel.py qr https://your-url.com

Features:
- Instant public URL (no auth tokens!)
- QR code generation
- ASCII QR display in terminal
- Auto-detect tunnel URL from output
"""

import subprocess
import sys
import re
import time
import os
import qrcode
from io import BytesIO


def print_header(title):
    """Print section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def start_serveo_tunnel(port=5001):
    """
    Start serveo.net SSH reverse tunnel

    FREE, no signup, instant HTTPS
    """
    print_header("🚀 Starting Serveo.net Tunnel")

    print(f"\n📡 Creating tunnel: localhost:{port} → public URL")
    print("⏳ This will take 5-10 seconds...\n")

    # SSH command for serveo.net
    cmd = f"ssh -o StrictHostKeyChecking=no -R 80:localhost:{port} serveo.net"

    print(f"💻 Command: {cmd}\n")

    try:
        # Start SSH tunnel process
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        # Read output to find the public URL
        url = None
        timeout = 15
        start_time = time.time()

        while time.time() - start_time < timeout:
            line = process.stderr.readline()

            if line:
                print(f"   {line.strip()}")

                # Look for URL in output
                # serveo.net outputs: "Forwarding HTTP traffic from https://xyz.serveo.net"
                match = re.search(r'https://[a-zA-Z0-9-]+\.serveo\.net', line)
                if match:
                    url = match.group(0)
                    break

            # Check if process died
            if process.poll() is not None:
                print("\n❌ SSH tunnel failed to start")
                stderr = process.stderr.read()
                if stderr:
                    print(f"Error: {stderr}")
                return None

        if url:
            print(f"\n✅ Tunnel active!")
            print(f"🌍 Public URL: {url}")
            print(f"📱 Test it: curl {url}")

            # Generate QR code
            generate_qr_code(url)

            print("\n🔥 TUNNEL IS LIVE! Press Ctrl+C to stop\n")

            # Keep tunnel running
            try:
                process.wait()
            except KeyboardInterrupt:
                print("\n\n🛑 Stopping tunnel...")
                process.terminate()
                print("✅ Tunnel stopped")

            return url
        else:
            print("\n⚠️  Could not detect URL. Tunnel may still be running.")
            print("Check output above for public URL.")
            return None

    except Exception as e:
        print(f"\n❌ Error starting tunnel: {e}")
        return None


def start_localhost_run_tunnel(port=5001):
    """
    Start localhost.run SSH reverse tunnel

    FREE alternative to serveo.net
    """
    print_header("🚀 Starting localhost.run Tunnel")

    print(f"\n📡 Creating tunnel: localhost:{port} → public URL")
    print("⏳ This will take 5-10 seconds...\n")

    # SSH command for localhost.run
    cmd = f"ssh -o StrictHostKeyChecking=no -R 80:localhost:{port} localhost.run"

    print(f"💻 Command: {cmd}\n")

    try:
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        url = None
        timeout = 15
        start_time = time.time()

        while time.time() - start_time < timeout:
            line = process.stderr.readline()

            if line:
                print(f"   {line.strip()}")

                # localhost.run outputs URL in format: https://xyz.lhr.life
                match = re.search(r'https://[a-zA-Z0-9-]+\.(lhr|localhost)\.(?:life|run)', line)
                if match:
                    url = match.group(0)
                    break

            if process.poll() is not None:
                print("\n❌ SSH tunnel failed to start")
                return None

        if url:
            print(f"\n✅ Tunnel active!")
            print(f"🌍 Public URL: {url}")

            generate_qr_code(url)

            print("\n🔥 TUNNEL IS LIVE! Press Ctrl+C to stop\n")

            try:
                process.wait()
            except KeyboardInterrupt:
                print("\n\n🛑 Stopping tunnel...")
                process.terminate()
                print("✅ Tunnel stopped")

            return url
        else:
            print("\n⚠️  Could not detect URL. Check output above.")
            return None

    except Exception as e:
        print(f"\n❌ Error starting tunnel: {e}")
        return None


def start_cloudflare_tunnel(port=5001):
    """
    Start Cloudflare Tunnel

    Requires: cloudflared installed
    Installation: brew install cloudflare/cloudflare/cloudflared
    """
    print_header("🚀 Starting Cloudflare Tunnel")

    # Check if cloudflared is installed
    try:
        subprocess.run(['cloudflared', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("\n❌ cloudflared not installed")
        print("\n📦 Install with:")
        print("   brew install cloudflare/cloudflare/cloudflared")
        print("\n   Or visit: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/")
        return None

    print(f"\n📡 Creating tunnel: localhost:{port} → Cloudflare URL")
    print("⏳ This will take 5-10 seconds...\n")

    cmd = f"cloudflared tunnel --url http://localhost:{port}"

    print(f"💻 Command: {cmd}\n")

    try:
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        url = None
        timeout = 20
        start_time = time.time()

        while time.time() - start_time < timeout:
            line = process.stderr.readline()

            if line:
                print(f"   {line.strip()}")

                # Cloudflare outputs: https://xyz.trycloudflare.com
                match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
                if match:
                    url = match.group(0)
                    break

            if process.poll() is not None:
                print("\n❌ Cloudflare tunnel failed to start")
                return None

        if url:
            print(f"\n✅ Tunnel active!")
            print(f"🌍 Public URL: {url}")

            generate_qr_code(url)

            print("\n🔥 TUNNEL IS LIVE! Press Ctrl+C to stop\n")

            try:
                process.wait()
            except KeyboardInterrupt:
                print("\n\n🛑 Stopping tunnel...")
                process.terminate()
                print("✅ Tunnel stopped")

            return url
        else:
            print("\n⚠️  Could not detect URL. Check output above.")
            return None

    except Exception as e:
        print(f"\n❌ Error starting tunnel: {e}")
        return None


def generate_qr_code(url):
    """Generate QR code for URL (both PNG and ASCII terminal display)"""
    print_header("📱 QR Code Generated")

    try:
        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)

        # Save as PNG
        img = qr.make_image(fill_color="black", back_color="white")
        qr_path = 'static/qr_codes/tunnel_qr.png'

        # Ensure directory exists
        os.makedirs('static/qr_codes', exist_ok=True)

        img.save(qr_path)
        print(f"\n💾 Saved: {qr_path}")

        # Print ASCII QR to terminal
        print("\n📱 Scan this QR code:\n")
        qr_terminal = qrcode.QRCode()
        qr_terminal.add_data(url)
        qr_terminal.print_ascii()

        print(f"\n🔗 URL: {url}\n")

    except Exception as e:
        print(f"\n⚠️  QR code generation failed: {e}")
        print(f"🔗 URL: {url}")


def show_help():
    """Show usage instructions"""
    print("""
SSH Tunnel - FREE Public Hosting
=================================

Usage:
    python3 ssh_tunnel.py serveo          # serveo.net (recommended)
    python3 ssh_tunnel.py localhost       # localhost.run
    python3 ssh_tunnel.py cloudflare      # Cloudflare Tunnel
    python3 ssh_tunnel.py qr <url>        # Just generate QR code

Options:
    serveo       - FREE, instant HTTPS, no signup (RECOMMENDED)
    localhost    - FREE alternative to serveo
    cloudflare   - FREE, requires cloudflared installed
    qr           - Generate QR code for existing URL

Examples:
    # Start serveo tunnel (easiest!)
    python3 ssh_tunnel.py serveo

    # Generate QR for existing URL
    python3 ssh_tunnel.py qr https://mysite.com

Features:
    ✅ FREE (no paid plans needed)
    ✅ No signup/auth tokens
    ✅ Instant HTTPS
    ✅ QR code generation
    ✅ ASCII QR in terminal

Requirements:
    - SSH client (built into macOS/Linux)
    - cloudflared (only for Cloudflare option)
    - qrcode library: pip install qrcode[pil]
    """)


def main():
    """Main entry point"""

    # Check arguments
    if len(sys.argv) < 2:
        show_help()
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == 'serveo':
        start_serveo_tunnel()

    elif command == 'localhost':
        start_localhost_run_tunnel()

    elif command == 'cloudflare':
        start_cloudflare_tunnel()

    elif command == 'qr':
        if len(sys.argv) < 3:
            print("❌ Error: URL required")
            print("Usage: python3 ssh_tunnel.py qr <url>")
            sys.exit(1)

        url = sys.argv[2]
        generate_qr_code(url)

    elif command in ['help', '--help', '-h']:
        show_help()

    else:
        print(f"❌ Unknown command: {command}")
        show_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
