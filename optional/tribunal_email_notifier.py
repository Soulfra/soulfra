"""
Tribunal Email Notifications

Sends email notifications when tribunal verdicts are reached.
Includes BCC for delivery tracking.

Uses Gmail SMTP by default (configure in .env)
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIME

Multipart
from datetime import datetime
import sqlite3


class TribunalEmailNotifier:
    """Send tribunal verdict notifications via email"""

    def __init__(self):
        # Load SMTP config from environment
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.smtp_user = os.getenv('SMTP_USER')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.from_email = os.getenv('SMTP_FROM_EMAIL', 'noreply@soulfra.com')
        self.from_name = os.getenv('SMTP_FROM_NAME', 'Soulfra Tribunal')
        self.bcc_email = os.getenv('SMTP_BCC')  # Optional: BCC yourself

    def send_verdict_notification(self, submission_id, recipient_emails):
        """
        Send tribunal verdict email to all participants

        Args:
            submission_id: Kangaroo Court submission ID
            recipient_emails: List of email addresses to notify

        Returns:
            Dict with success status and details
        """
        if not self.smtp_user or not self.smtp_password:
            return {
                'success': False,
                'error': 'SMTP credentials not configured in .env'
            }

        # Get tribunal data from database
        db = sqlite3.connect('soulfra.db')
        db.row_factory = sqlite3.Row

        submission = db.execute('''
            SELECT * FROM kangaroo_submissions WHERE id = ?
        ''', (submission_id,)).fetchone()

        if not submission:
            db.close()
            return {'success': False, 'error': 'Submission not found'}

        # Get user who submitted
        submitter = db.execute('''
            SELECT username, email FROM users WHERE id = ?
        ''', (submission['user_id'],)).fetchone()

        db.close()

        # Parse verdict details
        verdict = submission['verdict']
        reasoning = submission['reasoning'] or 'See full transcript'
        submitted_at = submission['submitted_at']
        judged_at = submission['judged_at']

        # Create email
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"🏛️ Tribunal Verdict: {verdict}"
        msg['From'] = f"{self.from_name} <{self.from_email}>"

        # HTML email body
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #3498db, #2ecc71);
                    color: white;
                    padding: 30px;
                    text-align: center;
                    border-radius: 8px 8px 0 0;
                }}
                .verdict {{
                    background: #f8f9fa;
                    padding: 20px;
                    margin: 20px 0;
                    border-left: 4px solid #3498db;
                }}
                .verdict-badge {{
                    display: inline-block;
                    padding: 8px 16px;
                    background: {self._get_verdict_color(verdict)};
                    color: white;
                    border-radius: 20px;
                    font-weight: bold;
                    text-transform: uppercase;
                }}
                .personas {{
                    margin: 20px 0;
                    padding: 15px;
                    background: #fff;
                    border: 1px solid #ddd;
                    border-radius: 8px;
                }}
                .persona {{
                    margin: 10px 0;
                    padding: 10px;
                    border-left: 3px solid #3498db;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    font-size: 0.9em;
                    color: #666;
                }}
                .btn {{
                    display: inline-block;
                    padding: 12px 24px;
                    background: #3498db;
                    color: white;
                    text-decoration: none;
                    border-radius: 6px;
                    margin: 10px 0;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>⚖️ Tribunal Verdict Reached</h1>
                <p>3-Way AI Debate Complete</p>
            </div>

            <div class="verdict">
                <h2>Final Verdict: <span class="verdict-badge">{verdict}</span></h2>
                <p><strong>Submitted:</strong> {submitted_at}</p>
                <p><strong>Decided:</strong> {judged_at or 'Just now'}</p>
                <p><strong>Reasoning:</strong> {reasoning}</p>
            </div>

            <div class="personas">
                <h3>3-Way AI Analysis</h3>

                <div class="persona">
                    <strong>🤖 CalRiven (Logic)</strong>
                    <p>Analyzed from efficiency and analytical reasoning perspective.</p>
                </div>

                <div class="persona">
                    <strong>⚖️ Soulfra (Balance)</strong>
                    <p>Weighed fairness and sought truth between both sides.</p>
                </div>

                <div class="persona">
                    <strong>🔥 DeathToData (Rebellion)</strong>
                    <p>Challenged authority and defended individual freedom.</p>
                </div>
            </div>

            <div style="text-align: center; margin: 30px 0;">
                <a href="http://192.168.1.87:5001/tribunal/case/{submission_id}" class="btn">
                    View Full Tribunal Transcript →
                </a>
            </div>

            <div class="footer">
                <p><strong>What is the Tribunal?</strong></p>
                <p>The Soulfra Tribunal is a 3-way AI debate system where CalRiven (logic),
                Soulfra (balance), and DeathToData (rebellion) analyze cases from different
                philosophical perspectives.</p>

                <p><strong>About Blamechain:</strong></p>
                <p>All message edits are permanently tracked with cryptographic hashes.
                The chain never forgets - ensuring accountability and transparency.</p>

                <p style="margin-top: 20px;">
                    <a href="http://192.168.1.87:5001/cringeproof">Play CringeProof</a> to get
                    assigned your own AI persona!
                </p>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(html, 'html'))

        # Send to each recipient
        try:
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)

            sent_count = 0
            failed = []

            for email in recipient_emails:
                try:
                    msg['To'] = email

                    # Add BCC if configured (for delivery tracking)
                    if self.bcc_email:
                        msg['Bcc'] = self.bcc_email

                    server.send_message(msg)
                    sent_count += 1
                    print(f"✓ Sent tribunal verdict to {email}")

                    # Remove To/Bcc for next iteration
                    del msg['To']
                    if 'Bcc' in msg:
                        del msg['Bcc']

                except Exception as e:
                    failed.append({'email': email, 'error': str(e)})
                    print(f"✗ Failed to send to {email}: {e}")

            server.quit()

            return {
                'success': True,
                'sent': sent_count,
                'failed': failed,
                'submission_id': submission_id,
                'verdict': verdict
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'SMTP error: {str(e)}'
            }

    def _get_verdict_color(self, verdict):
        """Get color for verdict badge"""
        colors = {
            'GUILTY': '#e74c3c',
            'INNOCENT': '#2ecc71',
            'NO_CONSENSUS': '#95a5a6',
            'MONITORING_RECOMMENDED': '#f39c12',
            'REQUIRES_MORE_DATA': '#3498db'
        }
        return colors.get(verdict, '#95a5a6')

    def send_edit_flag_notification(self, message_id, message_table, flagged_by_email):
        """
        Notify when message edit history is flagged for tribunal

        Args:
            message_id: ID of flagged message
            message_table: Table containing message
            flagged_by_email: Email of person who flagged it

        Returns:
            Dict with success status
        """
        if not self.smtp_user or not self.smtp_password:
            return {'success': False, 'error': 'SMTP not configured'}

        # Simple notification
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "🚨 Message Flagged for Tribunal Review"
        msg['From'] = f"{self.from_name} <{self.from_email}>"
        msg['To'] = flagged_by_email

        if self.bcc_email:
            msg['Bcc'] = self.bcc_email

        html = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: sans-serif; padding: 20px;">
            <h2>Message Flagged for Tribunal</h2>
            <p>A message edit history has been flagged for tribunal review.</p>
            <p><strong>Message ID:</strong> {message_id} ({message_table})</p>
            <p>The 3-way AI tribunal will analyze the edit history and provide a verdict.</p>
            <p><a href="http://192.168.1.87:5001/blamechain/history/{message_table}/{message_id}">
                View Edit History →
            </a></p>
        </body>
        </html>
        """

        msg.attach(MIMEText(html, 'html'))

        try:
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            server.send_message(msg)
            server.quit()

            return {'success': True, 'sent_to': flagged_by_email}

        except Exception as e:
            return {'success': False, 'error': str(e)}


def send_tribunal_verdict_email(submission_id, recipient_emails):
    """
    Convenience function: Send tribunal verdict notification

    Usage:
        send_tribunal_verdict_email(
            submission_id=5,
            recipient_emails=['user1@example.com', 'user2@example.com']
        )
    """
    notifier = TribunalEmailNotifier()
    return notifier.send_verdict_notification(submission_id, recipient_emails)
