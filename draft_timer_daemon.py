"""
Draft Timer Daemon

Implements chat-yap-ideate-lockin service logic.
Manages the voice → chat → yap → ideate → lock-in pipeline with timers.

Processes:
- Draft expiration (15 min default timer)
- Auto-lock expired drafts
- Token economy integration
- Quiz completion rewards
- Achievement unlocking
"""

import argparse
import time
import logging
import sqlite3
import requests
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('draft_timer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DraftTimerDaemon:
    def __init__(self, check_interval=10, auto_lock_expired=True,
                 token_integration=True, quiz_rewards=True):
        self.check_interval = check_interval
        self.auto_lock_expired = auto_lock_expired
        self.token_integration = token_integration
        self.quiz_rewards = quiz_rewards
        self.running = True

        self.db_path = 'soulfra.db'
        self.api_url = 'http://localhost:5001'

        logger.info("Initializing Draft Timer Daemon")
        logger.info(f"Check interval: {check_interval} seconds")
        logger.info(f"Auto-lock expired: {auto_lock_expired}")

    def get_db_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def check_expired_drafts(self):
        """Check for expired drafts and auto-lock them"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            # Find drafts that have expired
            cursor.execute('''
                SELECT id, idea_text, user_id, draft_expires_at, created_at
                FROM ideas
                WHERE draft_state = 'draft'
                AND locked_in = 0
                AND draft_expires_at IS NOT NULL
                AND draft_expires_at < ?
            ''', (datetime.utcnow().isoformat(),))

            expired_drafts = cursor.fetchall()

            if not expired_drafts:
                logger.debug("No expired drafts found")
                conn.close()
                return

            logger.info(f"Found {len(expired_drafts)} expired drafts")

            # Auto-lock each expired draft
            for draft in expired_drafts:
                logger.info(f"  Auto-locking draft #{draft['id']}: {draft['idea_text'][:50]}...")

                cursor.execute('''
                    UPDATE ideas
                    SET locked_in = 1, draft_state = 'auto-locked'
                    WHERE id = ?
                ''', (draft['id'],))

            conn.commit()
            conn.close()

            logger.info(f"✅ Auto-locked {len(expired_drafts)} expired drafts")

        except Exception as e:
            logger.error(f"Error checking expired drafts: {e}", exc_info=True)

    def process_token_rewards(self):
        """Process pending token rewards from quiz completions and achievements"""
        if not self.token_integration:
            return

        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            # Find completed quizzes that earned tokens but haven't been credited
            cursor.execute('''
                SELECT id, user_id, tokens_earned
                FROM quiz_attempts
                WHERE passed = 1
                AND tokens_earned > 0
                AND id NOT IN (
                    SELECT CAST(substr(description, instr(description, '#') + 1) as INTEGER)
                    FROM token_transactions
                    WHERE action = 'quiz_passed'
                )
            ''')

            pending_quiz_rewards = cursor.fetchall()

            for quiz in pending_quiz_rewards:
                logger.info(f"  Crediting {quiz['tokens_earned']} tokens for quiz #{quiz['id']} (user {quiz['user_id']})")

                # Credit tokens via API
                try:
                    response = requests.post(f"{self.api_url}/api/tokens/earn", json={
                        'user_id': quiz['user_id'],
                        'action': 'quiz_passed',
                        'description': f"Passed quiz #{quiz['id']}"
                    }, timeout=5)

                    if response.ok:
                        logger.info(f"    ✅ Tokens credited")
                    else:
                        logger.warning(f"    ⚠️  Token credit failed: {response.text}")

                except requests.RequestException as e:
                    logger.error(f"    ❌ Token API error: {e}")

            conn.close()

        except Exception as e:
            logger.error(f"Error processing token rewards: {e}", exc_info=True)

    def check_achievement_unlocks(self):
        """Check for newly unlocked achievements"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            # Find users with milestone reading progress but no corresponding achievement
            # Example: 5 posts read in a domain = "Explorer" achievement
            cursor.execute('''
                SELECT user_id, domain, COUNT(*) as count
                FROM reading_progress
                WHERE completed = 1
                GROUP BY user_id, domain
                HAVING count IN (5, 10, 25)
            ''')

            milestones = cursor.fetchall()

            for milestone in milestones:
                user_id = milestone['user_id']
                domain = milestone['domain']
                count = milestone['count']

                # Determine achievement name
                achievement_name = {
                    5: f"{domain.capitalize()} Explorer",
                    10: f"{domain.capitalize()} Expert",
                    25: f"{domain.capitalize()} Master"
                }.get(count)

                if not achievement_name:
                    continue

                # Check if already awarded
                cursor.execute('''
                    SELECT id FROM user_achievements
                    WHERE user_id = ? AND achievement_name = ?
                ''', (user_id, achievement_name))

                if cursor.fetchone():
                    continue  # Already awarded

                # Award achievement
                logger.info(f"🎖️  Unlocking achievement: {achievement_name} for user {user_id}")

                cursor.execute('''
                    INSERT INTO user_achievements (user_id, achievement_type, achievement_name, domain, earned_at, tokens_awarded)
                    VALUES (?, 'reading', ?, ?, ?, 20)
                ''', (user_id, achievement_name, domain, datetime.utcnow().isoformat()))

                # Award tokens
                try:
                    requests.post(f"{self.api_url}/api/tokens/earn", json={
                        'user_id': user_id,
                        'action': 'achievement_unlocked',
                        'description': f"Unlocked: {achievement_name}"
                    }, timeout=5)
                except:
                    pass

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Error checking achievements: {e}", exc_info=True)

    def get_draft_stats(self):
        """Get current draft statistics"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            # Active drafts
            cursor.execute('''
                SELECT COUNT(*) as count FROM ideas
                WHERE draft_state = 'draft' AND locked_in = 0
            ''')
            active_count = cursor.fetchone()['count']

            # Locked drafts
            cursor.execute('''
                SELECT COUNT(*) as count FROM ideas
                WHERE locked_in = 1
            ''')
            locked_count = cursor.fetchone()['count']

            # Expired (pending auto-lock)
            cursor.execute('''
                SELECT COUNT(*) as count FROM ideas
                WHERE draft_state = 'draft' AND draft_expires_at < ?
            ''', (datetime.utcnow().isoformat(),))
            expired_count = cursor.fetchone()['count']

            conn.close()

            return {
                'active': active_count,
                'locked': locked_count,
                'expired': expired_count
            }

        except Exception as e:
            logger.error(f"Error getting draft stats: {e}")
            return {'active': 0, 'locked': 0, 'expired': 0}

    def run_check_cycle(self):
        """Run one complete check cycle"""
        logger.info("=" * 60)
        logger.info("Running draft timer check cycle")

        # Get stats
        stats = self.get_draft_stats()
        logger.info(f"📊 Active: {stats['active']} | Locked: {stats['locked']} | Expired: {stats['expired']}")

        # Check and auto-lock expired drafts
        if self.auto_lock_expired and stats['expired'] > 0:
            self.check_expired_drafts()

        # Process token rewards
        if self.token_integration:
            self.process_token_rewards()

        # Check achievement unlocks
        if self.quiz_rewards:
            self.check_achievement_unlocks()

        logger.info("=" * 60)

    def run(self):
        """Main daemon loop"""
        logger.info("Starting Draft Timer Daemon")
        logger.info(f"Check interval: {self.check_interval} seconds")

        try:
            while self.running:
                self.run_check_cycle()
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
            self.running = False

        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
            sys.exit(1)

        finally:
            logger.info("Draft Timer Daemon stopped")

def main():
    parser = argparse.ArgumentParser(description='Draft Timer Daemon')
    parser.add_argument('--check-interval', type=int, default=10, help='Check interval in seconds')
    parser.add_argument('--auto-lock-expired', type=bool, default=True, help='Auto-lock expired drafts')
    parser.add_argument('--token-integration', type=bool, default=True, help='Enable token rewards')
    parser.add_argument('--quiz-rewards', type=bool, default=True, help='Enable quiz/achievement rewards')

    args = parser.parse_args()

    daemon = DraftTimerDaemon(
        check_interval=args.check_interval,
        auto_lock_expired=args.auto_lock_expired,
        token_integration=args.token_integration,
        quiz_rewards=args.quiz_rewards
    )

    daemon.run()

if __name__ == '__main__':
    main()
