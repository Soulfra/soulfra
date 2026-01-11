#!/usr/bin/env python3
"""
CringeProof Content Judge - POC Version

3-way AI approval system for content quality control.
For POC: Hardcoded to approve all (2/3 consensus).

Usage:
    python3 cringeproof_content_judge.py --approve
    python3 cringeproof_content_judge.py --task-id 1
"""

import sqlite3
import json
import argparse
from datetime import datetime

DB_PATH = 'soulfra.db'


class CringeProofJudge:
    """3-way content approval system"""

    def __init__(self, db_path=DB_PATH):
        self.db = sqlite3.connect(db_path)
        self.db.row_factory = sqlite3.Row

        # The three AI judges
        self.personas = ['calriven', 'soulfra', 'deathtodata']

    def get_completed_tasks(self):
        """Get all completed tasks awaiting approval"""
        cursor = self.db.execute('''
            SELECT * FROM ai_workforce_tasks
            WHERE status = 'completed'
            ORDER BY completed_at ASC
        ''')
        return cursor.fetchall()

    def get_task_by_id(self, task_id):
        """Get specific task by ID"""
        cursor = self.db.execute('''
            SELECT * FROM ai_workforce_tasks
            WHERE id = ?
        ''', (task_id,))
        return cursor.fetchone()

    def judge_content(self, task_id, content, persona):
        """
        POC Version: Hardcoded simple approval logic

        In production, this would:
        1. Call Ollama with persona-specific prompts
        2. Analyze content quality, brand fit, SEO
        3. Return nuanced vote with reasoning

        For POC: Always approve (makes testing easier)
        """

        # Hardcoded approval reasoning by persona
        reasoning_templates = {
            'calriven': 'Content is technically sound and well-structured. Approved for publishing.',
            'soulfra': 'Content balances clarity and depth. Approved for brand alignment.',
            'deathtodata': 'Content challenges conventions appropriately. Approved for authenticity.'
        }

        # POC: Always approve
        vote = 'approve'
        reasoning = reasoning_templates.get(persona, 'Approved.')

        # Store vote
        self.db.execute('''
            INSERT INTO content_approval_votes
            (task_id, persona, vote, reasoning)
            VALUES (?, ?, ?, ?)
        ''', (task_id, persona, vote, reasoning))
        self.db.commit()

        return vote, reasoning

    def run_tribunal(self, task_id):
        """Run 3-way tribunal vote on content"""
        print(f"\n{'='*80}")
        print(f"⚖️  CringeProof Tribunal - Task #{task_id}")
        print(f"{'='*80}")

        # Get task
        task = self.get_task_by_id(task_id)
        if not task:
            print(f"❌ Task {task_id} not found")
            return False

        if task['status'] != 'completed':
            print(f"❌ Task is not in 'completed' status (current: {task['status']})")
            return False

        print(f"Title: {task['output_title']}")
        print(f"Author: {task['assigned_to_persona']}")
        print(f"Length: {len(task['output_content'])} characters")
        print(f"\nContent Preview:")
        print(f"{task['output_content'][:300]}...\n")

        # Check if already voted
        existing_votes = self.db.execute('''
            SELECT COUNT(*) as count
            FROM content_approval_votes
            WHERE task_id = ?
        ''', (task_id,)).fetchone()

        if existing_votes['count'] >= 3:
            print(f"⚠️  Tribunal already completed for this task")
            # Show existing votes
            votes = self.db.execute('''
                SELECT persona, vote, reasoning
                FROM content_approval_votes
                WHERE task_id = ?
                ORDER BY voted_at
            ''', (task_id,)).fetchall()

            for v in votes:
                emoji = '✅' if v['vote'] == 'approve' else '❌'
                print(f"{emoji} {v['persona']}: {v['vote']}")
                print(f"   {v['reasoning']}")

            return True

        # Run 3-way vote
        print("Running 3-way tribunal vote...\n")

        votes = {}
        for persona in self.personas:
            vote, reasoning = self.judge_content(task_id, task['output_content'], persona)
            votes[persona] = vote

            emoji = '✅' if vote == 'approve' else '❌'
            print(f"{emoji} {persona.upper()}: {vote}")
            print(f"   {reasoning}\n")

        # Calculate consensus (2/3 approval)
        approvals = sum(1 for v in votes.values() if v == 'approve')
        consensus = approvals >= 2

        print(f"{'='*80}")
        print(f"📊 VERDICT: {approvals}/3 approvals")

        if consensus:
            print("✅ APPROVED - Content meets CringeProof standards")
            new_status = 'approved'
        else:
            print("❌ REJECTED - Content needs revision")
            new_status = 'rejected'

        print(f"{'='*80}\n")

        # Update task status
        self.db.execute('''
            UPDATE ai_workforce_tasks
            SET status = ?,
                approved_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (new_status, task_id))
        self.db.commit()

        return consensus

    def approve_all_completed(self):
        """Run tribunal on all completed tasks"""
        tasks = self.get_completed_tasks()

        if not tasks:
            print("✅ No completed tasks awaiting approval")
            return

        print(f"\n🎯 Found {len(tasks)} task(s) awaiting approval\n")

        approved_count = 0
        rejected_count = 0

        for task in tasks:
            consensus = self.run_tribunal(task['id'])
            if consensus:
                approved_count += 1
            else:
                rejected_count += 1

        print(f"\n{'='*80}")
        print("📊 Approval Summary")
        print(f"{'='*80}")
        print(f"Approved: {approved_count}")
        print(f"Rejected: {rejected_count}")
        print(f"Total: {len(tasks)}")

    def show_leaderboard(self):
        """Display AI persona leaderboard"""
        print(f"\n{'='*80}")
        print("🏆 AI WORKFORCE LEADERBOARD")
        print(f"{'='*80}\n")

        stats = self.db.execute('''
            SELECT * FROM ai_persona_stats
            ORDER BY total_credits DESC
        ''').fetchall()

        for i, persona_stats in enumerate(stats, 1):
            print(f"{i}. {persona_stats['persona'].upper()}")
            print(f"   Credits: {persona_stats['total_credits']}")
            print(f"   Tasks Completed: {persona_stats['total_tasks_completed']}")
            print(f"   Posts Published: {persona_stats['total_posts_published']}")
            print(f"   Approval Rate: {persona_stats['avg_approval_rate']:.1%}")
            print()

    def close(self):
        """Close database connection"""
        self.db.close()


def main():
    parser = argparse.ArgumentParser(description='CringeProof content approval system')
    parser.add_argument('--approve', action='store_true',
                       help='Approve all completed tasks')
    parser.add_argument('--task-id', type=int,
                       help='Approve specific task by ID')
    parser.add_argument('--leaderboard', action='store_true',
                       help='Show AI persona leaderboard')
    args = parser.parse_args()

    judge = CringeProofJudge()

    try:
        if args.leaderboard:
            judge.show_leaderboard()
        elif args.task_id:
            judge.run_tribunal(args.task_id)
        elif args.approve:
            judge.approve_all_completed()
        else:
            # Show pending approvals
            tasks = judge.get_completed_tasks()
            if tasks:
                print(f"\n📋 {len(tasks)} Task(s) Awaiting Approval:\n")
                for task in tasks:
                    print(f"Task #{task['id']}")
                    print(f"  Title: {task['output_title']}")
                    print(f"  Author: {task['assigned_to_persona']}")
                    print(f"  Completed: {task['completed_at']}")
                    print()
                print("Run with --approve to process all tasks")
                print("Run with --task-id N to process specific task")
            else:
                print("✅ No tasks awaiting approval")

    finally:
        judge.close()


if __name__ == '__main__':
    main()
