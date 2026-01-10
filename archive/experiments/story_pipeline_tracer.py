#!/usr/bin/env python3
"""
Story Pipeline Tracer - Google for AI Queries (Zero Dependencies)

Shows the COMPLETE JOURNEY of a story/problem through the AI system.

Like Google showing "About X results (0.5 seconds)" and explaining
how it found answers, we show:

Story Problem → Classification → Template → Response

Then TRACE IT BACKWARDS to show every step!

Philosophy:
----------
Most AI systems are black boxes. You send a query, get a response,
but have NO IDEA what happened in between.

This is like Google before they showed search result explanations.

We make AI FULLY TRANSPARENT:
- Every step logged
- Every decision explained
- Every template shown
- Complete deconstruction

Example Output:
--------------
```
Story: "I need to build a login system with proper security"

FORWARD TRACE:
Step 1: Received story (52 chars)
Step 2: Classified as 'technical' (85% confidence)
Step 3: Selected template: technical_solution_template
Step 4: Generated response (342 chars)
Step 5: Logged to database (request_id: req_abc123)

BACKWARD TRACE:
Response → technical_solution_template
  → Classification: technical (85%)
    → Neural network: calriven_technical_classifier
      → Original prompt: "I need to build a login system..."
```

Zero Dependencies: Python stdlib + SQLite

Usage:
    # Process a story and trace it
    python3 story_pipeline_tracer.py --story "My coding problem..."

    # Trace an existing request
    python3 story_pipeline_tracer.py --trace req_abc123

    # Show all traces
    python3 story_pipeline_tracer.py --list
"""

import sqlite3
import json
import time
import secrets
from datetime import datetime
from typing import Dict, List, Optional


# ==============================================================================
# PIPELINE PROCESSING
# ==============================================================================

def process_story_with_tracing(story: str, user_id: Optional[int] = None) -> Dict:
    """
    Process a story through the AI pipeline WITH FULL TRACING

    Args:
        story: The story/problem to process
        user_id: Optional user ID

    Returns:
        Complete trace information
    """
    trace_id = f"trace_{secrets.token_hex(8)}"
    request_id = f"req_{secrets.token_hex(8)}"

    trace_steps = []
    start_time = time.time()

    # Step 1: Receive story
    step1_time = time.time()
    trace_steps.append({
        'step_number': 1,
        'step_name': 'Receive Story',
        'description': f'Received story ({len(story)} chars)',
        'input_data': story,
        'output_data': {'length': len(story), 'word_count': len(story.split())},
        'duration_ms': 0,
        'timestamp': datetime.now().isoformat()
    })

    # Step 2: Classify with neural network
    step2_start = time.time()

    from neural_proxy import classify_with_neural_network
    classification_result = classify_with_neural_network(story)

    step2_duration = int((time.time() - step2_start) * 1000)

    trace_steps.append({
        'step_number': 2,
        'step_name': 'Neural Classification',
        'description': f"Classified as '{classification_result['classification']}' ({classification_result['confidence']:.0%} confidence)",
        'input_data': story,
        'output_data': classification_result,
        'duration_ms': step2_duration,
        'timestamp': datetime.now().isoformat()
    })

    # Step 3: Select template based on classification
    step3_start = time.time()

    template = select_template_for_classification(classification_result['classification'])

    step3_duration = int((time.time() - step3_start) * 1000)

    trace_steps.append({
        'step_number': 3,
        'step_name': 'Template Selection',
        'description': f"Selected template: {template['name']}",
        'input_data': classification_result,
        'output_data': template,
        'duration_ms': step3_duration,
        'timestamp': datetime.now().isoformat()
    })

    # Step 4: Generate response from template
    step4_start = time.time()

    response = generate_response_from_template(template, story, classification_result)

    step4_duration = int((time.time() - step4_start) * 1000)

    trace_steps.append({
        'step_number': 4,
        'step_name': 'Response Generation',
        'description': f"Generated response ({len(response)} chars)",
        'input_data': {'template': template['name'], 'story': story},
        'output_data': response,
        'duration_ms': step4_duration,
        'timestamp': datetime.now().isoformat()
    })

    # Step 5: Log to database
    step5_start = time.time()

    save_trace_to_database(trace_id, request_id, story, response, trace_steps, classification_result)

    step5_duration = int((time.time() - step5_start) * 1000)

    trace_steps.append({
        'step_number': 5,
        'step_name': 'Database Logging',
        'description': f"Logged to database (trace_id: {trace_id})",
        'input_data': {'request_id': request_id},
        'output_data': {'trace_id': trace_id, 'saved': True},
        'duration_ms': step5_duration,
        'timestamp': datetime.now().isoformat()
    })

    total_duration = int((time.time() - start_time) * 1000)

    return {
        'trace_id': trace_id,
        'request_id': request_id,
        'story': story,
        'response': response,
        'classification': classification_result,
        'template': template,
        'steps': trace_steps,
        'total_duration_ms': total_duration
    }


# ==============================================================================
# TEMPLATE SYSTEM
# ==============================================================================

def select_template_for_classification(classification: str) -> Dict:
    """Select appropriate response template based on classification"""

    templates = {
        'technical': {
            'name': 'technical_solution_template',
            'format': 'structured_solution',
            'sections': ['Problem Analysis', 'Solution Steps', 'Code Example', 'Best Practices']
        },
        'privacy': {
            'name': 'privacy_explanation_template',
            'format': 'educational',
            'sections': ['Privacy Concern', 'Impact', 'Recommendations', 'Resources']
        },
        'validation': {
            'name': 'validation_checklist_template',
            'format': 'checklist',
            'sections': ['What to Test', 'Test Steps', 'Expected Results', 'Edge Cases']
        },
        'general': {
            'name': 'general_response_template',
            'format': 'conversational',
            'sections': ['Understanding', 'Response', 'Next Steps']
        }
    }

    return templates.get(classification, templates['general'])


def generate_response_from_template(template: Dict, story: str, classification: Dict) -> str:
    """Generate response using selected template"""

    template_name = template['name']

    if template_name == 'technical_solution_template':
        return f"""**Technical Solution**

**Problem Analysis:**
Your question relates to: {story[:100]}...

**Classification:** {classification['classification']} (confidence: {classification['confidence']:.0%})

**Solution Steps:**
1. Identify the core requirements
2. Choose appropriate technologies
3. Implement with best practices
4. Test thoroughly

**Code Example:**
```python
# Example implementation
def solve_problem():
    # Your solution here
    pass
```

**Best Practices:**
- Follow established patterns
- Write tests
- Document your code
- Consider edge cases
"""

    elif template_name == 'privacy_explanation_template':
        return f"""**Privacy Explanation**

**Privacy Concern:**
{story[:150]}...

**Impact:**
This relates to data privacy and user protection.

**Recommendations:**
- Minimize data collection
- Use encryption
- Implement access controls
- Follow GDPR guidelines

**Resources:**
- Privacy by Design principles
- Data protection regulations
- Security best practices
"""

    elif template_name == 'validation_checklist_template':
        return f"""**Validation Checklist**

**What to Test:**
Based on: {story[:100]}...

**Test Steps:**
1. Test happy path
2. Test edge cases
3. Test error conditions
4. Test performance

**Expected Results:**
- All tests pass
- No regressions
- Performance acceptable

**Edge Cases:**
- Empty input
- Null values
- Boundary conditions
"""

    else:  # general template
        return f"""**Response**

**Understanding:**
You asked about: {story[:150]}...

**Classification:** {classification['classification']}

**Response:**
Based on the analysis, here's what I can suggest...

**Next Steps:**
1. Consider your specific requirements
2. Review available options
3. Implement solution
4. Test and iterate
"""


# ==============================================================================
# DATABASE STORAGE
# ==============================================================================

def create_trace_tables():
    """Create tables for pipeline tracing"""
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    # Pipeline traces
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pipeline_traces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trace_id TEXT UNIQUE NOT NULL,
            request_id TEXT NOT NULL,
            story_text TEXT NOT NULL,
            response_text TEXT NOT NULL,
            classification TEXT,
            confidence REAL,
            template_name TEXT,
            total_duration_ms INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Trace steps
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trace_steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trace_id TEXT NOT NULL,
            step_number INTEGER NOT NULL,
            step_name TEXT NOT NULL,
            description TEXT,
            input_data TEXT,
            output_data TEXT,
            duration_ms INTEGER,
            timestamp TIMESTAMP,
            FOREIGN KEY (trace_id) REFERENCES pipeline_traces(trace_id)
        )
    ''')

    conn.commit()
    conn.close()

    print("✅ Trace tables created")


def save_trace_to_database(trace_id: str, request_id: str, story: str, response: str,
                           steps: List[Dict], classification: Dict):
    """Save complete trace to database"""
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    # Save main trace
    total_duration = sum(step['duration_ms'] for step in steps)

    cursor.execute('''
        INSERT INTO pipeline_traces (
            trace_id, request_id, story_text, response_text,
            classification, confidence, template_name, total_duration_ms
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        trace_id,
        request_id,
        story,
        response,
        classification['classification'],
        classification['confidence'],
        'template',  # Will be filled from steps
        total_duration
    ))

    # Save steps
    for step in steps:
        cursor.execute('''
            INSERT INTO trace_steps (
                trace_id, step_number, step_name, description,
                input_data, output_data, duration_ms, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            trace_id,
            step['step_number'],
            step['step_name'],
            step['description'],
            json.dumps(step['input_data']) if isinstance(step['input_data'], dict) else str(step['input_data']),
            json.dumps(step['output_data']) if isinstance(step['output_data'], dict) else str(step['output_data']),
            step['duration_ms'],
            step['timestamp']
        ))

    conn.commit()
    conn.close()


# ==============================================================================
# TRACE RETRIEVAL & DISPLAY
# ==============================================================================

def get_trace_by_id(trace_id: str) -> Optional[Dict]:
    """Retrieve complete trace from database"""
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get main trace
    cursor.execute('SELECT * FROM pipeline_traces WHERE trace_id = ?', (trace_id,))
    trace = cursor.fetchone()

    if not trace:
        conn.close()
        return None

    trace = dict(trace)

    # Get steps
    cursor.execute('''
        SELECT * FROM trace_steps
        WHERE trace_id = ?
        ORDER BY step_number
    ''', (trace_id,))

    steps = [dict(row) for row in cursor.fetchall()]
    conn.close()

    trace['steps'] = steps
    return trace


def print_trace(trace: Dict):
    """Print trace in human-readable format"""
    print()
    print("=" * 70)
    print("🔍 PIPELINE TRACE")
    print("=" * 70)
    print()
    print(f"Trace ID: {trace['trace_id']}")
    print(f"Request ID: {trace.get('request_id', 'N/A')}")
    print(f"Total Duration: {trace.get('total_duration_ms', 0)} ms")
    print()

    print("FORWARD TRACE (Story → Response):")
    print()

    for step in trace.get('steps', []):
        print(f"Step {step['step_number']}: {step['step_name']}")
        print(f"  {step['description']}")
        print(f"  Duration: {step['duration_ms']} ms")
        print()

    print("=" * 70)
    print("BACKWARD TRACE (Response → Origin):")
    print("=" * 70)
    print()

    # Reverse the steps
    for step in reversed(trace.get('steps', [])):
        print(f"← Step {step['step_number']}: {step['step_name']}")
        if step['step_name'] == 'Response Generation':
            print(f"   Used template from classification")
        elif step['step_name'] == 'Template Selection':
            print(f"   Selected based on neural network output")
        elif step['step_name'] == 'Neural Classification':
            print(f"   Analyzed original story")
        print()

    print("=" * 70)
    print()


def list_all_traces(limit: int = 10):
    """List recent traces"""
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT trace_id, classification, confidence, total_duration_ms, created_at
        FROM pipeline_traces
        ORDER BY created_at DESC
        LIMIT ?
    ''', (limit,))

    traces = cursor.fetchall()
    conn.close()

    print()
    print("=" * 70)
    print("📋 RECENT TRACES")
    print("=" * 70)
    print()

    for trace in traces:
        print(f"Trace ID: {trace['trace_id']}")
        print(f"  Classification: {trace['classification']} ({trace['confidence']:.0%})")
        print(f"  Duration: {trace['total_duration_ms']} ms")
        print(f"  Created: {trace['created_at']}")
        print()


# ==============================================================================
# CLI
# ==============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Story Pipeline Tracer - Google for AI Queries')
    parser.add_argument('--init', action='store_true', help='Initialize trace tables')
    parser.add_argument('--story', type=str, help='Process a story and trace it')
    parser.add_argument('--trace', type=str, help='Show trace by ID')
    parser.add_argument('--list', action='store_true', help='List recent traces')

    args = parser.parse_args()

    if args.init:
        create_trace_tables()

    elif args.story:
        print(f"Processing story: {args.story[:50]}...")
        print()

        result = process_story_with_tracing(args.story)

        print()
        print("=" * 70)
        print("✅ STORY PROCESSED WITH FULL TRACING")
        print("=" * 70)
        print()

        print_trace(result)

        print("Response:")
        print("-" * 70)
        print(result['response'])
        print("-" * 70)
        print()

    elif args.trace:
        trace = get_trace_by_id(args.trace)

        if trace:
            print_trace(trace)
        else:
            print(f"❌ Trace {args.trace} not found")

    elif args.list:
        list_all_traces()

    else:
        print("Story Pipeline Tracer - Google for AI Queries")
        print()
        print("Usage:")
        print("  --init                    Initialize trace tables")
        print("  --story 'text'            Process story and trace it")
        print("  --trace trace_abc123      Show trace by ID")
        print("  --list                    List recent traces")
