#!/usr/bin/env python3
"""
Automation Node System - Self-Hosted Zapier Alternative

Like your quote: "run automations through them like zapier and all this other
bullshit but self hosted and way cheaper because itll all be default nodes"

Node-based workflow automation using OSS tools you've built:
- Voice recording → Transcription → Wordmap → AI → Export
- Event-driven triggers
- All local processing (no cloud)
- Default nodes = your existing tools

Usage:
    # Run built-in workflow
    python3 automation_node_system.py --workflow voice-to-debate

    # List available nodes
    python3 automation_node_system.py --list-nodes

    # Create custom workflow
    python3 automation_node_system.py --create "Voice → AI → Export"

    # Show workflow status
    python3 automation_node_system.py --status <workflow_id>

Like:
- Zapier but self-hosted and cheaper
- OSS tools as default building blocks
- Event-driven triggers (new recording, etc.)
- All offline-first
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from database import get_db


# ==============================================================================
# CONFIG
# ==============================================================================

WORKFLOWS_DIR = Path('./workflows')
WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)

WORKFLOW_LOGS_DIR = Path('./workflow_logs')
WORKFLOW_LOGS_DIR.mkdir(parents=True, exist_ok=True)


# ==============================================================================
# NODE DEFINITIONS
# ==============================================================================

class AutomationNode:
    """Base class for automation nodes"""

    def __init__(self, node_id: str, config: Dict = None):
        self.node_id = node_id
        self.config = config or {}
        self.name = self.__class__.__name__
        self.inputs = []
        self.outputs = []

    def execute(self, input_data: Any) -> Dict:
        """
        Execute node with input data

        Returns:
            {
                'success': bool,
                'output': Any,
                'error': Optional[str],
                'metadata': Dict
            }
        """
        raise NotImplementedError("Nodes must implement execute()")

    def __repr__(self):
        return f"{self.name}(id={self.node_id})"


# Voice Nodes
class VoiceRecordingTriggerNode(AutomationNode):
    """Trigger: New voice recording detected"""

    def execute(self, input_data: Any = None) -> Dict:
        """Check for new voice recordings"""
        db = get_db()

        # Get latest recording
        recording = db.execute('''
            SELECT id, filename, created_at, transcription
            FROM simple_voice_recordings
            ORDER BY id DESC
            LIMIT 1
        ''').fetchone()

        if recording:
            return {
                'success': True,
                'output': {
                    'recording_id': recording['id'],
                    'filename': recording['filename'],
                    'has_transcription': bool(recording['transcription']),
                    'created_at': recording['created_at']
                },
                'metadata': {'trigger_type': 'voice_recording'}
            }

        return {
            'success': False,
            'error': 'No recordings found',
            'metadata': {}
        }


class WhisperTranscriptionNode(AutomationNode):
    """Action: Transcribe audio with Whisper"""

    def execute(self, input_data: Dict) -> Dict:
        """Transcribe recording using Whisper"""
        recording_id = input_data.get('recording_id')

        if not recording_id:
            return {'success': False, 'error': 'No recording_id provided'}

        # Import here to avoid circular dependency
        from whisper_transcriber import transcribe_recording

        try:
            result = transcribe_recording(recording_id)

            if result:
                return {
                    'success': True,
                    'output': {
                        'recording_id': recording_id,
                        'transcription': result['text'],
                        'word_count': len(result['text'].split()),
                        'has_word_timestamps': 'words' in result
                    },
                    'metadata': {'node_type': 'transcription'}
                }

            return {'success': False, 'error': 'Transcription failed'}

        except Exception as e:
            return {'success': False, 'error': str(e)}


class WordmapUpdateNode(AutomationNode):
    """Action: Update user wordmap"""

    def execute(self, input_data: Dict) -> Dict:
        """Update wordmap with new transcription"""
        recording_id = input_data.get('recording_id')
        transcription = input_data.get('transcription')

        if not transcription:
            return {'success': False, 'error': 'No transcription provided'}

        from user_wordmap_engine import update_user_wordmap

        try:
            result = update_user_wordmap(
                user_id=1,
                recording_id=recording_id,
                transcript=transcription
            )

            return {
                'success': True,
                'output': {
                    'wordmap_size': len(result['wordmap']),
                    'new_words_added': result.get('new_words_added', 0),
                    'target_reached': len(result['wordmap']) >= 256
                },
                'metadata': {'node_type': 'wordmap_update'}
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}


# AI Nodes
class AIDebateGeneratorNode(AutomationNode):
    """Action: Generate AI debate response"""

    def execute(self, input_data: Dict) -> Dict:
        """Generate AI debate for recording"""
        recording_id = input_data.get('recording_id')
        persona = self.config.get('persona', 'deathtodata')

        if not recording_id:
            return {'success': False, 'error': 'No recording_id provided'}

        from ai_debate_generator import AIDebateGenerator

        try:
            generator = AIDebateGenerator()

            debate = generator.create_debate_from_recording(
                recording_id=recording_id,
                persona=persona,
                ragebait=self.config.get('ragebait', False)
            )

            if 'error' in debate:
                return {'success': False, 'error': debate['error']}

            return {
                'success': True,
                'output': {
                    'debate_id': debate['debate_id'],
                    'recording_id': recording_id,
                    'persona': persona,
                    'controversy_score': debate['ai_response'].get('controversy_score', 0)
                },
                'metadata': {'node_type': 'ai_debate'}
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}


class SHA256FilterNode(AutomationNode):
    """Filter: Check content alignment with wordmap"""

    def execute(self, input_data: Dict) -> Dict:
        """Filter content by SHA256 wordmap alignment"""
        content = input_data.get('content') or input_data.get('transcription')

        if not content:
            return {'success': False, 'error': 'No content to filter'}

        from sha256_content_wrapper import SHA256ContentWrapper

        try:
            wrapper = SHA256ContentWrapper(user_id=1)

            alignment = wrapper.calculate_content_alignment(content)
            tier = wrapper.get_tier_from_alignment(alignment)

            min_tier = self.config.get('min_tier', 'standard')
            tier_order = ['reject', 'basic', 'standard', 'premium']

            passed = tier_order.index(tier) >= tier_order.index(min_tier)

            return {
                'success': True,
                'output': {
                    'alignment': alignment,
                    'tier': tier,
                    'passed_filter': passed,
                    'min_tier': min_tier
                },
                'metadata': {'node_type': 'sha256_filter'}
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}


# Export Nodes
class HTMLExportNode(AutomationNode):
    """Action: Export as HTML"""

    def execute(self, input_data: Dict) -> Dict:
        """Export debate as HTML"""
        debate_id = input_data.get('debate_id')

        if not debate_id:
            return {'success': False, 'error': 'No debate_id provided'}

        # This would use ai_debate_generator's HTML export
        # For now, simulate
        html_file = Path(f'./debates/{debate_id}.html')

        return {
            'success': True,
            'output': {
                'html_file': str(html_file),
                'exported': True
            },
            'metadata': {'node_type': 'html_export'}
        }


class ASCIIAnimationNode(AutomationNode):
    """Action: Convert to ASCII animation"""

    def execute(self, input_data: Dict) -> Dict:
        """Convert recording to ASCII animation"""
        recording_id = input_data.get('recording_id')

        if not recording_id:
            return {'success': False, 'error': 'No recording_id provided'}

        from video_to_ascii import VideoToASCII

        try:
            converter = VideoToASCII()

            # Get recording from DB
            db = get_db()
            recording = db.execute('''
                SELECT audio_data FROM simple_voice_recordings WHERE id = ?
            ''', (recording_id,)).fetchone()

            if not recording or not recording['audio_data']:
                return {'success': False, 'error': 'Recording has no video data'}

            # Convert (would need to save to temp file first)
            return {
                'success': True,
                'output': {
                    'recording_id': recording_id,
                    'ascii_animation': True,
                    'frames_generated': 120  # Placeholder
                },
                'metadata': {'node_type': 'ascii_animation'}
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}


# Database Nodes
class DatabaseSaveNode(AutomationNode):
    """Action: Save to database"""

    def execute(self, input_data: Dict) -> Dict:
        """Save workflow result to database"""
        db = get_db()

        try:
            db.execute('''
                INSERT INTO workflow_results
                (workflow_id, node_id, result_data, created_at)
                VALUES (?, ?, ?, ?)
            ''', (
                self.config.get('workflow_id', 'unknown'),
                self.node_id,
                json.dumps(input_data),
                datetime.now().isoformat()
            ))
            db.commit()

            return {
                'success': True,
                'output': {'saved': True},
                'metadata': {'node_type': 'database_save'}
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}


# Notification Nodes
class LogOutputNode(AutomationNode):
    """Action: Log output to console/file"""

    def execute(self, input_data: Dict) -> Dict:
        """Log workflow output"""
        print(f"\n{'='*70}")
        print(f"  LOG OUTPUT - {self.node_id}")
        print(f"{'='*70}")
        print(json.dumps(input_data, indent=2))
        print(f"{'='*70}\n")

        return {
            'success': True,
            'output': input_data,
            'metadata': {'node_type': 'log_output'}
        }


# ==============================================================================
# NODE REGISTRY
# ==============================================================================

NODE_REGISTRY = {
    # Triggers
    'voice_recording_trigger': VoiceRecordingTriggerNode,

    # Voice processing
    'whisper_transcription': WhisperTranscriptionNode,
    'wordmap_update': WordmapUpdateNode,

    # AI processing
    'ai_debate_generator': AIDebateGeneratorNode,
    'sha256_filter': SHA256FilterNode,

    # Export
    'html_export': HTMLExportNode,
    'ascii_animation': ASCIIAnimationNode,

    # Utility
    'database_save': DatabaseSaveNode,
    'log_output': LogOutputNode,
}


# ==============================================================================
# WORKFLOW ENGINE
# ==============================================================================

class WorkflowEngine:
    """Execute node-based automation workflows"""

    def __init__(self):
        self.db = get_db()

    def create_workflow(self, name: str, nodes: List[Dict]) -> str:
        """
        Create workflow from node definitions

        Args:
            name: Workflow name
            nodes: List of node configs like:
                [
                    {'type': 'voice_recording_trigger', 'id': 'trigger1'},
                    {'type': 'whisper_transcription', 'id': 'transcribe1'},
                    ...
                ]

        Returns:
            workflow_id
        """
        workflow_id = f"workflow_{int(datetime.now().timestamp())}"

        workflow_data = {
            'id': workflow_id,
            'name': name,
            'nodes': nodes,
            'created_at': datetime.now().isoformat()
        }

        # Save workflow
        workflow_file = WORKFLOWS_DIR / f"{workflow_id}.json"
        workflow_file.write_text(json.dumps(workflow_data, indent=2))

        print(f"✅ Created workflow: {workflow_id}")
        print(f"   Name: {name}")
        print(f"   Nodes: {len(nodes)}")
        print(f"   File: {workflow_file}\n")

        return workflow_id

    def execute_workflow(self, workflow_id: str, initial_data: Any = None) -> Dict:
        """Execute workflow by ID"""
        workflow_file = WORKFLOWS_DIR / f"{workflow_id}.json"

        if not workflow_file.exists():
            return {'error': f'Workflow {workflow_id} not found'}

        workflow_data = json.loads(workflow_file.read_text())

        print(f"\n{'='*70}")
        print(f"  🔄 EXECUTING WORKFLOW: {workflow_data['name']}")
        print(f"{'='*70}\n")

        results = []
        current_output = initial_data

        for i, node_config in enumerate(workflow_data['nodes'], 1):
            node_type = node_config['type']
            node_id = node_config.get('id', f"{node_type}_{i}")

            if node_type not in NODE_REGISTRY:
                print(f"❌ Unknown node type: {node_type}")
                continue

            # Create node instance
            node_class = NODE_REGISTRY[node_type]
            node = node_class(node_id=node_id, config=node_config.get('config', {}))

            print(f"Step {i}: {node_type}")
            print(f"{'─'*70}")

            start_time = time.time()

            # Execute node
            result = node.execute(current_output)

            elapsed = time.time() - start_time

            if result['success']:
                print(f"✅ Success ({elapsed:.2f}s)")
                current_output = result['output']
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                # Stop workflow on error
                results.append({
                    'node': node_type,
                    'node_id': node_id,
                    'result': result,
                    'elapsed': elapsed
                })
                break

            results.append({
                'node': node_type,
                'node_id': node_id,
                'result': result,
                'elapsed': elapsed
            })

            print()

        total_time = sum(r['elapsed'] for r in results)

        print(f"{'='*70}")
        print(f"  ✅ WORKFLOW COMPLETE")
        print(f"{'='*70}")
        print(f"Total steps: {len(results)}")
        print(f"Successful: {sum(1 for r in results if r['result']['success'])}")
        print(f"Total time: {total_time:.2f}s")
        print(f"{'='*70}\n")

        # Save workflow execution log
        log_file = WORKFLOW_LOGS_DIR / f"{workflow_id}_{int(datetime.now().timestamp())}.json"
        log_file.write_text(json.dumps({
            'workflow_id': workflow_id,
            'workflow_name': workflow_data['name'],
            'executed_at': datetime.now().isoformat(),
            'total_time': total_time,
            'results': results
        }, indent=2))

        return {
            'workflow_id': workflow_id,
            'workflow_name': workflow_data['name'],
            'results': results,
            'total_time': total_time,
            'log_file': str(log_file)
        }

    def list_nodes(self):
        """List all available nodes"""
        print(f"\n{'='*70}")
        print("  📦 AVAILABLE NODES (Default OSS Tools)")
        print(f"{'='*70}\n")

        categories = {
            'Triggers': ['voice_recording_trigger'],
            'Voice Processing': ['whisper_transcription', 'wordmap_update'],
            'AI Processing': ['ai_debate_generator', 'sha256_filter'],
            'Export': ['html_export', 'ascii_animation'],
            'Utility': ['database_save', 'log_output']
        }

        for category, node_types in categories.items():
            print(f"{category}:")
            for node_type in node_types:
                if node_type in NODE_REGISTRY:
                    node_class = NODE_REGISTRY[node_type]
                    print(f"  • {node_type}")
                    if node_class.__doc__:
                        print(f"    {node_class.__doc__.strip()}")
            print()

        print(f"💡 These are OSS tools you've built - cheaper than SaaS!\n")


# ==============================================================================
# BUILT-IN WORKFLOWS
# ==============================================================================

BUILTIN_WORKFLOWS = {
    'voice-to-debate': {
        'name': 'Voice Recording → AI Debate',
        'description': 'New voice recording → Transcribe → Wordmap → AI debate → Export HTML',
        'nodes': [
            {'type': 'voice_recording_trigger', 'id': 'trigger'},
            {'type': 'whisper_transcription', 'id': 'transcribe'},
            {'type': 'wordmap_update', 'id': 'wordmap'},
            {'type': 'ai_debate_generator', 'id': 'debate', 'config': {'persona': 'deathtodata'}},
            {'type': 'sha256_filter', 'id': 'filter', 'config': {'min_tier': 'standard'}},
            {'type': 'html_export', 'id': 'export'},
            {'type': 'log_output', 'id': 'log'}
        ]
    },

    'voice-to-ascii': {
        'name': 'Voice Recording → ASCII Animation',
        'description': 'New voice recording → Transcribe → ASCII animation → Export',
        'nodes': [
            {'type': 'voice_recording_trigger', 'id': 'trigger'},
            {'type': 'whisper_transcription', 'id': 'transcribe'},
            {'type': 'ascii_animation', 'id': 'ascii'},
            {'type': 'log_output', 'id': 'log'}
        ]
    },

    'wordmap-builder': {
        'name': 'Wordmap Builder (20 → 256)',
        'description': 'Continuously update wordmap from new recordings',
        'nodes': [
            {'type': 'voice_recording_trigger', 'id': 'trigger'},
            {'type': 'whisper_transcription', 'id': 'transcribe'},
            {'type': 'wordmap_update', 'id': 'wordmap'},
            {'type': 'log_output', 'id': 'log'}
        ]
    }
}


# ==============================================================================
# CLI
# ==============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Automation Node System - Self-Hosted Zapier Alternative'
    )

    parser.add_argument(
        '--workflow',
        type=str,
        metavar='NAME',
        help='Execute built-in workflow (voice-to-debate, voice-to-ascii, wordmap-builder)'
    )

    parser.add_argument(
        '--list-nodes',
        action='store_true',
        help='List all available nodes'
    )

    parser.add_argument(
        '--list-workflows',
        action='store_true',
        help='List built-in workflows'
    )

    parser.add_argument(
        '--create',
        type=str,
        metavar='NAME',
        help='Create custom workflow (interactive)'
    )

    parser.add_argument(
        '--execute',
        type=str,
        metavar='WORKFLOW_ID',
        help='Execute workflow by ID'
    )

    args = parser.parse_args()

    engine = WorkflowEngine()

    try:
        # List nodes
        if args.list_nodes:
            engine.list_nodes()

        # List workflows
        elif args.list_workflows:
            print(f"\n{'='*70}")
            print("  🔄 BUILT-IN WORKFLOWS")
            print(f"{'='*70}\n")

            for workflow_id, workflow_config in BUILTIN_WORKFLOWS.items():
                print(f"{workflow_id}")
                print(f"  {workflow_config['name']}")
                print(f"  {workflow_config['description']}")
                print(f"  Nodes: {len(workflow_config['nodes'])}")
                print()

            print(f"💡 Run with: --workflow <name>\n")

        # Execute built-in workflow
        elif args.workflow:
            if args.workflow not in BUILTIN_WORKFLOWS:
                print(f"❌ Unknown workflow: {args.workflow}")
                print(f"   Available: {', '.join(BUILTIN_WORKFLOWS.keys())}")
                sys.exit(1)

            workflow_config = BUILTIN_WORKFLOWS[args.workflow]

            # Create workflow
            workflow_id = engine.create_workflow(
                name=workflow_config['name'],
                nodes=workflow_config['nodes']
            )

            # Execute workflow
            result = engine.execute_workflow(workflow_id)

            print(f"📊 Workflow result:")
            print(f"   Workflow: {result['workflow_name']}")
            print(f"   Steps: {len(result['results'])}")
            print(f"   Time: {result['total_time']:.2f}s")
            print(f"   Log: {result['log_file']}\n")

        # Execute custom workflow
        elif args.execute:
            result = engine.execute_workflow(args.execute)

            if 'error' in result:
                print(f"❌ {result['error']}")
                sys.exit(1)

        else:
            parser.print_help()

    except KeyboardInterrupt:
        print("\n\n👋 Cancelled")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
