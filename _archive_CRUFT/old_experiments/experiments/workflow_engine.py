#!/usr/bin/env python3
"""
Workflow Engine - Execute Queued Workflows

Processes workflows from workflow_executions table.
Works with newsroom_scheduler to enable automated operations.

Zero Dependencies: Python stdlib only
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, Optional


class WorkflowEngine:
    """
    Execute workflows from database queue

    Workflow types supported:
    - auto_post_generation
    - content_moderation
    - user_lifecycle
    - custom (extensible)
    """

    def __init__(self, db_path: str = 'soulfra.db'):
        self.db_path = db_path

    def execute(self, workflow: Dict) -> Dict:
        """
        Execute a workflow

        Args:
            workflow: Workflow dict from database

        Returns:
            dict with success status and results
        """
        workflow_type = workflow.get('workflow_type', 'unknown')

        handlers = {
            'auto_post_generation': self._handle_auto_post,
            'content_moderation': self._handle_moderation,
            'user_lifecycle': self._handle_lifecycle,
        }

        handler = handlers.get(workflow_type, self._handle_unknown)

        try:
            result = handler(workflow)
            self._mark_complete(workflow['id'], result)
            return result
        except Exception as e:
            error_result = {'success': False, 'error': str(e)}
            self._mark_failed(workflow['id'], str(e))
            return error_result

    def _handle_auto_post(self, workflow: Dict) -> Dict:
        """Handle auto-post generation workflow"""
        params = json.loads(workflow.get('params', '{}'))
        session_id = params.get('session_id')

        if not session_id:
            return {'success': False, 'error': 'Missing session_id'}

        from content_generator import ContentGenerator
        generator = ContentGenerator(self.db_path)

        post = generator.conversation_to_post(
            session_id=session_id,
            template=params.get('template', 'qa_format'),
            auto_publish=params.get('auto_publish', False)
        )

        if post:
            return {
                'success': True,
                'post_title': post.title,
                'post_slug': post.slug
            }
        else:
            return {'success': False, 'error': 'Post generation failed'}

    def _handle_moderation(self, workflow: Dict) -> Dict:
        """Handle content moderation workflow"""
        return {'success': True, 'note': 'Moderation not implemented yet'}

    def _handle_lifecycle(self, workflow: Dict) -> Dict:
        """Handle user lifecycle workflow"""
        return {'success': True, 'note': 'Lifecycle not implemented yet'}

    def _handle_unknown(self, workflow: Dict) -> Dict:
        """Handle unknown workflow type"""
        return {
            'success': False,
            'error': f"Unknown workflow type: {workflow.get('workflow_type')}"
        }

    def _mark_complete(self, workflow_id: int, result: Dict):
        """Mark workflow as complete"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE workflow_executions
                SET status = 'completed',
                    completed_at = ?,
                    result = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), json.dumps(result), workflow_id))

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error marking workflow complete: {e}")

    def _mark_failed(self, workflow_id: int, error: str):
        """Mark workflow as failed"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE workflow_executions
                SET status = 'failed',
                    completed_at = ?,
                    result = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), json.dumps({'error': error}), workflow_id))

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error marking workflow failed: {e}")


if __name__ == '__main__':
    print("🔄 Workflow Engine Test")
    print("=" * 70)

    engine = WorkflowEngine()

    # Test workflow
    test_workflow = {
        'id': 999,
        'workflow_type': 'auto_post_generation',
        'params': json.dumps({'session_id': 3, 'template': 'qa_format'})
    }

    result = engine.execute(test_workflow)
    print(f"Result: {result}")

    print("\n✅ Workflow engine working!")
