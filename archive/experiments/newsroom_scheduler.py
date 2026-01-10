#!/usr/bin/env python3
"""
Newsroom Scheduler - Background Job Automation

Enables "whenever it feels like it" auto-post generation from widget conversations.

Philosophy:
----------
Instead of manually typing `/generate post`, the scheduler monitors conversations
and automatically creates posts when they're "complete" and interesting.

Like a newsroom editor that:
- Monitors all conversations
- Decides which are worth publishing
- Creates multiple stories from one conversation
- Publishes on schedule

Zero Dependencies: Uses Python stdlib (threading, time, sqlite3)
"""

import threading
import time
import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional


class NewsroomScheduler:
    """
    Background scheduler for automated content generation

    Runs periodically to:
    1. Monitor widget conversations for completeness
    2. Auto-generate posts from complete conversations
    3. Execute scheduled workflows
    4. Clean up inactive sessions

    Usage:
        scheduler = NewsroomScheduler()
        scheduler.start()  # Runs in background thread
    """

    def __init__(self, db_path: str = 'soulfra.db', interval_minutes: int = 30):
        """
        Initialize scheduler

        Args:
            db_path: Path to database
            interval_minutes: How often to run jobs (default 30 minutes)
        """
        self.db_path = db_path
        self.interval = interval_minutes * 60  # Convert to seconds
        self.running = False
        self.thread = None
        self.job_log: List[Dict] = []

    # ==========================================================================
    # SCHEDULER CONTROL
    # ==========================================================================

    def start(self):
        """Start scheduler in background thread"""
        if self.running:
            print("⚠️  Scheduler already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        print(f"✅ Newsroom scheduler started (runs every {self.interval // 60} minutes)")

    def stop(self):
        """Stop scheduler"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("🛑 Newsroom scheduler stopped")

    def _run_loop(self):
        """Main scheduler loop (runs in background thread)"""
        while self.running:
            try:
                self._run_jobs()
            except Exception as e:
                self._log_error(f"Scheduler error: {e}")

            # Sleep until next run
            time.sleep(self.interval)

    def _run_jobs(self):
        """Run all scheduled jobs"""
        start_time = datetime.now()
        print(f"\n📰 Newsroom scheduler running at {start_time.isoformat()}")

        jobs_run = []

        # Job 1: Monitor conversations for auto-post generation
        result = self._job_auto_generate_posts()
        jobs_run.append(('auto_generate_posts', result))

        # Job 2: Clean up abandoned sessions
        result = self._job_cleanup_sessions()
        jobs_run.append(('cleanup_sessions', result))

        # Job 3: Process workflow queue
        result = self._job_process_workflows()
        jobs_run.append(('process_workflows', result))

        # Log results
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        self.job_log.append({
            'timestamp': start_time.isoformat(),
            'duration_seconds': duration,
            'jobs': jobs_run
        })

        print(f"✅ Scheduler run complete ({duration:.2f}s)")
        for job_name, result in jobs_run:
            print(f"   {job_name}: {result}")

    # ==========================================================================
    # JOB 1: AUTO-GENERATE POSTS
    # ==========================================================================

    def _job_auto_generate_posts(self) -> Dict:
        """
        Monitor widget conversations and auto-generate posts

        Returns:
            dict with results
        """
        try:
            # Find conversations ready for post generation
            candidates = self._find_post_candidates()

            if not candidates:
                return {'status': 'no_candidates', 'posts_generated': 0}

            posts_generated = 0
            for candidate in candidates:
                success = self._auto_generate_from_conversation(candidate)
                if success:
                    posts_generated += 1

            return {
                'status': 'success',
                'candidates_found': len(candidates),
                'posts_generated': posts_generated
            }

        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def _find_post_candidates(self) -> List[Dict]:
        """
        Find conversations that are ready to become posts

        Criteria for "completeness":
        - Message count >= 10
        - Last message >= 15 minutes ago (conversation ended)
        - Has Q&A pairs (user + AI messages)
        - Not already converted to post
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Find sessions with enough messages
            cursor.execute("""
                SELECT
                    s.id as session_id,
                    s.created_at,
                    s.status,
                    COUNT(m.id) as message_count,
                    MAX(m.created_at) as last_message_at
                FROM discussion_sessions s
                JOIN discussion_messages m ON s.id = m.session_id
                WHERE s.status = 'active'
                GROUP BY s.id
                HAVING COUNT(m.id) >= 10
            """)

            sessions = [dict(row) for row in cursor.fetchall()]
            conn.close()

            # Filter by time criteria
            candidates = []
            now = datetime.now()

            for session in sessions:
                last_msg_time = datetime.fromisoformat(session['last_message_at'])
                time_since_last = (now - last_msg_time).total_seconds() / 60  # minutes

                # Conversation ended if no activity for 15+ minutes
                if time_since_last >= 15:
                    # Check if has Q&A pairs
                    if self._has_qa_pairs(session['session_id']):
                        # Check if not already converted
                        if not self._already_converted(session['session_id']):
                            candidates.append(session)

            return candidates

        except Exception as e:
            print(f"Error finding candidates: {e}")
            return []

    def _has_qa_pairs(self, session_id: int) -> bool:
        """Check if conversation has user questions and AI answers"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    SUM(CASE WHEN sender = 'user' THEN 1 ELSE 0 END) as user_msgs,
                    SUM(CASE WHEN sender = 'ai' THEN 1 ELSE 0 END) as ai_msgs
                FROM discussion_messages
                WHERE session_id = ?
            """, (session_id,))

            result = cursor.fetchone()
            conn.close()

            # Need at least 3 messages from each
            return result[0] >= 3 and result[1] >= 3

        except Exception as e:
            print(f"Error checking Q&A pairs: {e}")
            return False

    def _already_converted(self, session_id: int) -> bool:
        """Check if conversation already converted to post"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT COUNT(*) FROM posts
                WHERE content LIKE '%widget_session_' || ? || '%'
            """, (session_id,))

            count = cursor.fetchone()[0]
            conn.close()

            return count > 0

        except Exception as e:
            print(f"Error checking conversion: {e}")
            return True  # Assume converted to avoid duplicates

    def _auto_generate_from_conversation(self, session: Dict) -> bool:
        """
        Auto-generate post from conversation

        Args:
            session: Session dict with session_id, message_count, etc.

        Returns:
            bool: True if post generated successfully
        """
        try:
            from content_generator import ContentGenerator

            generator = ContentGenerator(self.db_path)

            # Generate post (as draft, not auto-published)
            post = generator.conversation_to_post(
                session_id=session['session_id'],
                author_id=6,  # SoulAssistant
                template='qa_format',
                auto_publish=False  # Save as draft for review
            )

            if post:
                print(f"   ✨ Generated post from session {session['session_id']}: {post.title}")

                # Mark session as processed
                self._mark_session_processed(session['session_id'])

                return True
            else:
                print(f"   ⚠️  Could not generate post from session {session['session_id']}")
                return False

        except Exception as e:
            print(f"   ❌ Error generating post: {e}")
            return False

    def _mark_session_processed(self, session_id: int):
        """Mark session as processed to avoid re-processing"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE discussion_sessions
                SET status = 'processed'
                WHERE id = ?
            """, (session_id,))

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"Error marking session processed: {e}")

    # ==========================================================================
    # JOB 2: CLEANUP SESSIONS
    # ==========================================================================

    def _job_cleanup_sessions(self) -> Dict:
        """
        Clean up abandoned or stale sessions

        Returns:
            dict with results
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Find sessions with no activity for 24+ hours
            cutoff_time = (datetime.now() - timedelta(hours=24)).isoformat()

            cursor.execute("""
                SELECT s.id, MAX(m.created_at) as last_activity
                FROM discussion_sessions s
                LEFT JOIN discussion_messages m ON s.id = m.session_id
                WHERE s.status = 'active'
                GROUP BY s.id
                HAVING MAX(m.created_at) < ?
            """, (cutoff_time,))

            stale_sessions = cursor.fetchall()

            if not stale_sessions:
                conn.close()
                return {'status': 'no_stale_sessions', 'cleaned': 0}

            # Mark as abandoned
            for session_id, last_activity in stale_sessions:
                cursor.execute("""
                    UPDATE discussion_sessions
                    SET status = 'abandoned'
                    WHERE id = ?
                """, (session_id,))

            conn.commit()
            conn.close()

            return {
                'status': 'success',
                'cleaned': len(stale_sessions)
            }

        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    # ==========================================================================
    # JOB 3: PROCESS WORKFLOWS
    # ==========================================================================

    def _job_process_workflows(self) -> Dict:
        """
        Process queued workflows from workflow_executions table

        Returns:
            dict with results
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Find pending workflows
            cursor.execute("""
                SELECT * FROM workflow_executions
                WHERE status = 'pending'
                ORDER BY created_at ASC
                LIMIT 10
            """)

            workflows = [dict(row) for row in cursor.fetchall()]
            conn.close()

            if not workflows:
                return {'status': 'no_workflows', 'processed': 0}

            processed = 0
            for workflow in workflows:
                success = self._execute_workflow(workflow)
                if success:
                    processed += 1

            return {
                'status': 'success',
                'workflows_found': len(workflows),
                'processed': processed
            }

        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def _execute_workflow(self, workflow: Dict) -> bool:
        """
        Execute a workflow

        Args:
            workflow: Workflow dict from database

        Returns:
            bool: True if executed successfully
        """
        try:
            # Import workflow engine (will create in next step)
            from workflow_engine import WorkflowEngine

            engine = WorkflowEngine(self.db_path)
            result = engine.execute(workflow)

            return result.get('success', False)

        except ImportError:
            # Workflow engine not implemented yet
            print("   ⚠️  Workflow engine not available yet")
            return False
        except Exception as e:
            print(f"   ❌ Workflow execution error: {e}")
            return False

    # ==========================================================================
    # LOGGING & UTILITIES
    # ==========================================================================

    def _log_error(self, message: str):
        """Log error"""
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': 'ERROR',
            'message': message
        }
        self.job_log.append(error_entry)
        print(f"❌ {message}")

    def get_stats(self) -> Dict:
        """Get scheduler statistics"""
        if not self.job_log:
            return {
                'total_runs': 0,
                'status': 'not_started'
            }

        successful_runs = sum(1 for log in self.job_log if 'jobs' in log)

        return {
            'total_runs': len(self.job_log),
            'successful_runs': successful_runs,
            'failed_runs': len(self.job_log) - successful_runs,
            'last_run': self.job_log[-1].get('timestamp', 'N/A'),
            'running': self.running
        }

    def run_now(self):
        """Manually trigger a scheduler run (for testing)"""
        print("🔄 Manually triggering scheduler run...")
        self._run_jobs()


# ==============================================================================
# TESTING & STANDALONE EXECUTION
# ==============================================================================

if __name__ == '__main__':
    import sys

    print("📰 Newsroom Scheduler")
    print("=" * 70)

    scheduler = NewsroomScheduler(interval_minutes=30)

    if len(sys.argv) > 1 and sys.argv[1] == 'once':
        # Run once and exit (for testing)
        print("\n🧪 Running once (test mode)")
        scheduler.run_now()

        # Show stats
        print("\n📊 Stats:")
        stats = scheduler.get_stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")

    else:
        # Start background scheduler
        print("\n🚀 Starting background scheduler...")
        print("   Press Ctrl+C to stop\n")

        scheduler.start()

        try:
            # Keep main thread alive
            while True:
                time.sleep(60)

                # Print stats every minute
                stats = scheduler.get_stats()
                print(f"📊 Runs: {stats['total_runs']} | Last: {stats.get('last_run', 'N/A')}")

        except KeyboardInterrupt:
            print("\n\n🛑 Stopping scheduler...")
            scheduler.stop()
            print("✅ Stopped")

    print("\n" + "=" * 70)
    print("💡 To run scheduler in production:")
    print("   python3 newsroom_scheduler.py &  # Background")
    print("   python3 newsroom_scheduler.py once  # Test run")
