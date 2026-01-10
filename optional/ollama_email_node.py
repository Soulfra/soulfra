#!/usr/bin/env python3
"""
Ollama Email Node - Decentralized AI via Email

Turn ANY device into an Ollama node that processes requests via email.

The Vision:
- Your Mac, old iPhones, Raspberry Pis all run this script
- They all check the same email inbox
- First one to see a request handles it
- Sends AI response back via email
- Like a spam botnet but for good!

Hardware you can use:
- Mac (primary - runs Ollama)
- Old iPhone (via Termux/iSH - email relay)
- Raspberry Pi (backup Ollama node)
- Old router (email forwarder)
- Any device with Python + email access

Usage:
    python3 ollama_email_node.py --email ollama@yourdomain.com --password xxx

The node will:
1. Check inbox every 30 seconds
2. Look for unprocessed requests
3. Process with local Ollama (if available)
4. Send response back
5. Delete processed emails

Like email spam chains but actually useful!
"""

import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
import time
import json
import requests
import hashlib
import os
import sys
from datetime import datetime
from typing import Dict, Optional, List

# =============================================================================
# CONFIG
# =============================================================================

OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434')
NODE_NAME = os.environ.get('NODE_NAME', 'unknown-node')
CHECK_INTERVAL = int(os.environ.get('CHECK_INTERVAL', '30'))  # seconds

# IMAP/SMTP config (override via environment or args)
IMAP_HOST = os.environ.get('IMAP_HOST', 'imap.gmail.com')
IMAP_PORT = int(os.environ.get('IMAP_PORT', '993'))
SMTP_HOST = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))

# =============================================================================
# EMAIL HELPER
# =============================================================================

class EmailNode:
    """
    Email-based Ollama node

    Checks inbox for AI requests, processes them, sends responses
    """

    def __init__(self, email_addr: str, password: str, node_name: str = None):
        self.email = email_addr
        self.password = password
        self.node_name = node_name or NODE_NAME
        self.processed_ids = set()  # Track processed emails

    def check_ollama_available(self) -> bool:
        """Check if Ollama is running locally"""
        try:
            response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
            return response.ok
        except:
            return False

    def connect_imap(self) -> imaplib.IMAP4_SSL:
        """Connect to IMAP server"""
        try:
            mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
            mail.login(self.email, self.password)
            return mail
        except Exception as e:
            print(f"❌ IMAP connection failed: {e}")
            return None

    def connect_smtp(self) -> smtplib.SMTP:
        """Connect to SMTP server"""
        try:
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
            server.starttls()
            server.login(self.email, self.password)
            return server
        except Exception as e:
            print(f"❌ SMTP connection failed: {e}")
            return None

    def parse_request_email(self, msg) -> Optional[Dict]:
        """
        Parse email to extract AI request

        Email format:
        Subject: [OLLAMA_REQUEST] api_key_here
        Body: The prompt to send to AI
        """
        subject = ""
        for s in msg.get("Subject", "").split():
            decoded = decode_header(s)
            if decoded and decoded[0][0]:
                try:
                    subject += decoded[0][0].decode() if isinstance(decoded[0][0], bytes) else decoded[0][0]
                except:
                    subject += str(decoded[0][0])

        # Check if this is a request
        if not subject.startswith('[OLLAMA_REQUEST]'):
            return None

        # Extract API key from subject
        parts = subject.split()
        api_key = parts[1] if len(parts) > 1 else None

        if not api_key:
            return None

        # Get body (prompt)
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode()
                    except:
                        pass
        else:
            try:
                body = msg.get_payload(decode=True).decode()
            except:
                pass

        if not body:
            return None

        # Extract sender email
        sender = email.utils.parseaddr(msg.get("From", ""))[1]

        return {
            'api_key': api_key,
            'prompt': body.strip(),
            'sender': sender
        }

    def process_with_ollama(self, prompt: str, model: str = 'llama3') -> Optional[str]:
        """
        Process prompt with local Ollama

        Args:
            prompt: User prompt
            model: Model name

        Returns:
            AI response or None if failed
        """
        try:
            response = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    'model': model,
                    'prompt': prompt,
                    'stream': False
                },
                timeout=120
            )

            if response.ok:
                data = response.json()
                return data.get('response', '')
            else:
                return f"Error: Ollama returned {response.status_code}"

        except requests.exceptions.Timeout:
            return "Error: Ollama timeout (>2 minutes)"
        except requests.exceptions.ConnectionError:
            return "Error: Ollama not running"
        except Exception as e:
            return f"Error: {str(e)}"

    def send_response_email(self, to_email: str, prompt: str, response: str):
        """
        Send AI response back via email

        Args:
            to_email: Recipient email
            prompt: Original prompt
            response: AI response
        """
        server = self.connect_smtp()
        if not server:
            return

        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"[OLLAMA_RESPONSE] from {self.node_name}"
        msg['From'] = self.email
        msg['To'] = to_email

        # Plain text version
        text = f"""
Ollama Response
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Your prompt:
{prompt}

AI Response:
{response}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Processed by: {self.node_name}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """

        # HTML version
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: monospace; background: #1a1a1a; color: #fff; padding: 20px; }}
                .prompt {{ background: #2a2a2a; padding: 15px; border-radius: 8px; margin: 10px 0; }}
                .response {{ background: #1a3a1a; padding: 15px; border-radius: 8px; margin: 10px 0; }}
                .meta {{ opacity: 0.7; font-size: 0.9em; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <h2>🤖 Ollama Response</h2>
            <div class="prompt">
                <strong>Your prompt:</strong><br>
                {prompt}
            </div>
            <div class="response">
                <strong>AI Response:</strong><br>
                <pre>{response}</pre>
            </div>
            <div class="meta">
                Processed by: {self.node_name}<br>
                Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(text, 'plain'))
        msg.attach(MIMEText(html, 'html'))

        try:
            server.send_message(msg)
            print(f"✅ Sent response to {to_email}")
        except Exception as e:
            print(f"❌ Failed to send response: {e}")
        finally:
            server.quit()

    def process_inbox(self):
        """
        Check inbox and process requests

        Returns:
            Number of requests processed
        """
        mail = self.connect_imap()
        if not mail:
            return 0

        try:
            # Select inbox
            mail.select('INBOX')

            # Search for unread emails
            status, messages = mail.search(None, 'UNSEEN')

            if status != 'OK':
                return 0

            email_ids = messages[0].split()

            if not email_ids:
                return 0

            processed_count = 0

            for email_id in email_ids:
                # Skip if already processed
                email_id_str = email_id.decode()
                if email_id_str in self.processed_ids:
                    continue

                # Fetch email
                status, msg_data = mail.fetch(email_id, '(RFC822)')

                if status != 'OK':
                    continue

                # Parse email
                msg = email.message_from_bytes(msg_data[0][1])

                # Extract request
                request = self.parse_request_email(msg)

                if not request:
                    # Not an Ollama request, mark as read and skip
                    mail.store(email_id, '+FLAGS', '\\Seen')
                    continue

                print(f"\n📧 New request from {request['sender']}")
                print(f"Prompt: {request['prompt'][:100]}...")

                # Check if Ollama is available
                if not self.check_ollama_available():
                    print(f"⚠️  Ollama not available on this node, skipping...")
                    # Leave unread for other nodes
                    continue

                # Process with Ollama
                print(f"🤖 Processing with Ollama...")
                ai_response = self.process_with_ollama(request['prompt'])

                if ai_response:
                    # Send response
                    self.send_response_email(
                        request['sender'],
                        request['prompt'],
                        ai_response
                    )

                    # Mark as processed
                    mail.store(email_id, '+FLAGS', '\\Seen')
                    self.processed_ids.add(email_id_str)
                    processed_count += 1

                    print(f"✅ Request processed and response sent")
                else:
                    print(f"❌ Failed to process request")

            return processed_count

        except Exception as e:
            print(f"❌ Error processing inbox: {e}")
            return 0

        finally:
            try:
                mail.close()
                mail.logout()
            except:
                pass

    def run(self):
        """
        Run the email node indefinitely

        Checks inbox every CHECK_INTERVAL seconds
        """
        print(f"""
╔═══════════════════════════════════════════════════════════════╗
║     OLLAMA EMAIL NODE                                        ║
║     Decentralized AI via Email                               ║
╚═══════════════════════════════════════════════════════════════╝

Node Name:     {self.node_name}
Email:         {self.email}
Ollama URL:    {OLLAMA_URL}
Check Interval: {CHECK_INTERVAL}s

Ollama Status: {'✅ Online' if self.check_ollama_available() else '❌ Offline'}

Waiting for requests...
        """)

        while True:
            try:
                processed = self.process_inbox()

                if processed > 0:
                    print(f"\n📊 Processed {processed} request(s)")

                time.sleep(CHECK_INTERVAL)

            except KeyboardInterrupt:
                print("\n\n👋 Shutting down node...")
                break

            except Exception as e:
                print(f"\n❌ Error in main loop: {e}")
                print(f"Retrying in {CHECK_INTERVAL}s...")
                time.sleep(CHECK_INTERVAL)


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Ollama Email Node - Decentralized AI')
    parser.add_argument('--email', required=True, help='Email address to check')
    parser.add_argument('--password', required=True, help='Email password (app password for Gmail)')
    parser.add_argument('--node-name', help='Node name (default: hostname)')
    parser.add_argument('--ollama-url', default=OLLAMA_URL, help='Ollama URL')
    parser.add_argument('--check-interval', type=int, default=CHECK_INTERVAL, help='Check interval in seconds')

    args = parser.parse_args()

    # Override globals
    global OLLAMA_URL, NODE_NAME, CHECK_INTERVAL
    OLLAMA_URL = args.ollama_url
    NODE_NAME = args.node_name or os.uname().nodename
    CHECK_INTERVAL = args.check_interval

    # Create and run node
    node = EmailNode(args.email, args.password, NODE_NAME)
    node.run()


if __name__ == '__main__':
    main()
