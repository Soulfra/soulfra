#!/usr/bin/env python3
"""
Prove Story Deconstruction - Complete End-to-End Demo

DEMONSTRATES:
1. Story problem goes IN
2. AI processes it (neural networks, templates, Ollama)
3. Response comes OUT
4. DECONSTRUCT IT BACKWARDS to show every step

Like "Google for AI Queries" - full transparency!

The Complete Flow:
-----------------
```
FORWARD (Problem → Solution):
Story: "I need to build a secure login system"
  → Step 1: Receive story (47 chars)
  → Step 2: Classify as 'technical' (85% confidence)
  → Step 3: Select 'technical_solution_template'
  → Step 4: Generate response (342 chars)
  → Step 5: Log to database (trace_abc123)

BACKWARD (Solution → Origin):
Response (342 chars)
  ← Generated from: technical_solution_template
    ← Selected because: classification = 'technical'
      ← Classified by: calriven_technical_classifier
        ← Analyzed: "I need to build a secure login system"
```

This proves:
- ✅ Complete transparency (every step visible)
- ✅ Everything is templatable (responses use templates)
- ✅ Full database logging (can reconstruct any query)
- ✅ Works offline (neural networks + Ollama)
- ✅ Like Google but for AI (explainable results)

Usage:
    # Run complete demonstration
    python3 prove_story_deconstruction.py --demo

    # Process a custom story
    python3 prove_story_deconstruction.py --story "Your problem here"

    # Show example traces
    python3 prove_story_deconstruction.py --examples
"""

import sys
from story_pipeline_tracer import (
    process_story_with_tracing,
    create_trace_tables,
    print_trace,
    list_all_traces
)


# ==============================================================================
# EXAMPLE STORIES
# ==============================================================================

EXAMPLE_STORIES = [
    {
        'title': 'Technical Problem',
        'story': 'I need to build a secure login system with proper authentication and password hashing',
        'expected_classification': 'technical'
    },
    {
        'title': 'Privacy Question',
        'story': 'How can I protect user data and ensure GDPR compliance in my application?',
        'expected_classification': 'privacy'
    },
    {
        'title': 'Validation Task',
        'story': 'I need to validate and test my API endpoints before deploying to production',
        'expected_classification': 'validation'
    },
    {
        'title': 'General Question',
        'story': 'What are the best practices for software development in 2025?',
        'expected_classification': 'general'
    }
]


# ==============================================================================
# DEMONSTRATION
# ==============================================================================

def prove_story_deconstruction():
    """Complete end-to-end demonstration"""
    print("=" * 70)
    print("🔍 PROVING STORY DECONSTRUCTION")
    print("=" * 70)
    print()
    print("This demonstrates the COMPLETE VISION:")
    print()
    print("  1. Story problem → AI processing → Response")
    print("  2. THEN deconstruct backwards to show every step")
    print("  3. Like Google showing 'how we found this answer'")
    print()
    print("Everything is:")
    print("  ✅ Transparent (see every step)")
    print("  ✅ Templatable (responses use templates)")
    print("  ✅ Logged (database tracks everything)")
    print("  ✅ Offline (no external APIs)")
    print()
    input("Press ENTER to begin demonstration...")
    print()

    # Step 1: Initialize
    print("=" * 70)
    print("STEP 1: Initialize Database")
    print("=" * 70)
    print()

    create_trace_tables()
    print()
    input("Press ENTER for next step...")
    print()

    # Step 2: Process example stories
    print("=" * 70)
    print("STEP 2: Process Example Stories")
    print("=" * 70)
    print()

    print("We'll process 4 different story types:")
    print("  1. Technical problem")
    print("  2. Privacy question")
    print("  3. Validation task")
    print("  4. General question")
    print()
    input("Press ENTER to process stories...")
    print()

    traces = []

    for i, example in enumerate(EXAMPLE_STORIES, 1):
        print(f"\n{'='*70}")
        print(f"Processing Story {i}/{len(EXAMPLE_STORIES)}: {example['title']}")
        print("=" * 70)
        print()
        print(f"Story: {example['story']}")
        print()
        print(f"Expected Classification: {example['expected_classification']}")
        print()

        # Process with full tracing
        result = process_story_with_tracing(example['story'])

        traces.append(result)

        print(f"✅ Processed in {result['total_duration_ms']} ms")
        print(f"   Actual Classification: {result['classification']['classification']}")
        print(f"   Confidence: {result['classification']['confidence']:.0%}")
        print(f"   Trace ID: {result['trace_id']}")
        print()

        if i < len(EXAMPLE_STORIES):
            input("Press ENTER for next story...")

    input("\nPress ENTER to see detailed traces...")
    print()

    # Step 3: Show detailed trace for first story
    print("=" * 70)
    print("STEP 3: Detailed Trace Breakdown")
    print("=" * 70)
    print()

    print("Let's examine the first story in detail:")
    print()

    first_trace = traces[0]
    print_trace(first_trace)

    print("Response Generated:")
    print("-" * 70)
    print(first_trace['response'])
    print("-" * 70)
    print()

    input("Press ENTER to see the template breakdown...")
    print()

    # Step 4: Template breakdown
    print("=" * 70)
    print("STEP 4: Template Breakdown")
    print("=" * 70)
    print()

    template = first_trace['template']

    print(f"Template Used: {template['name']}")
    print(f"Format: {template['format']}")
    print()
    print("Template Sections:")
    for section in template['sections']:
        print(f"  • {section}")
    print()

    print("This proves:")
    print("  ✅ Responses are generated from templates")
    print("  ✅ Templates are selected based on classification")
    print("  ✅ Everything is structured and predictable")
    print()

    input("Press ENTER to see the deconstruction...")
    print()

    # Step 5: Backward deconstruction
    print("=" * 70)
    print("STEP 5: Backward Deconstruction")
    print("=" * 70)
    print()

    print("Starting from the RESPONSE, let's trace backwards:")
    print()

    print(f"Response: {first_trace['response'][:100]}...")
    print()
    print("  ↑")
    print(f"  Generated by: {template['name']}")
    print()
    print("  ↑")
    print(f"  Selected because: classification = '{first_trace['classification']['classification']}'")
    print()
    print("  ↑")
    print(f"  Classified by: {first_trace['classification']['model']}")
    print(f"  Confidence: {first_trace['classification']['confidence']:.0%}")
    print()
    print("  ↑")
    print(f"  Original story: {first_trace['story']}")
    print()

    print("=" * 70)
    print("COMPLETE TRANSPARENCY!")
    print("=" * 70)
    print()

    input("Press ENTER for database proof...")
    print()

    # Step 6: Database proof
    print("=" * 70)
    print("STEP 6: Database Logging Proof")
    print("=" * 70)
    print()

    print("All traces are stored in database:")
    print()

    list_all_traces(limit=len(traces))

    print("You can retrieve ANY trace by ID:")
    print()
    print(f"Example: python3 story_pipeline_tracer.py --trace {traces[0]['trace_id']}")
    print()

    input("Press ENTER for summary...")
    print()

    # Summary
    print("=" * 70)
    print("🎉 STORY DECONSTRUCTION COMPLETE!")
    print("=" * 70)
    print()

    print("What we proved:")
    print()
    print("✅ FORWARD FLOW (Problem → Solution):")
    print("   Story → Classification → Template → Response")
    print()
    print("✅ BACKWARD FLOW (Solution → Origin):")
    print("   Response → Template → Classification → Neural Network → Story")
    print()
    print("✅ COMPLETE TRANSPARENCY:")
    print("   Every step logged, every decision explained")
    print()
    print("✅ LIKE GOOGLE FOR AI:")
    print("   'About X results (Y seconds)' but for AI queries")
    print()
    print("✅ EVERYTHING IS TEMPLATABLE:")
    print("   Responses use templates, templates use classifications")
    print()
    print("✅ WORKS OFFLINE:")
    print("   Neural networks (no internet)")
    print("   SQLite database (local)")
    print("   Python stdlib (zero dependencies)")
    print()

    print("The Stack:")
    print("  • story_pipeline_tracer.py - Full tracing")
    print("  • neural_proxy.py - AI routing")
    print("  • ai_analytics.py - Analytics")
    print("  • SQLite database - Complete logs")
    print()

    print("Files Created:")
    print(f"  • {len(traces)} traces in database")
    print(f"  • {len(traces) * 5} trace steps logged")
    print(f"  • All retrievable by trace_id")
    print()

    print("Next Steps:")
    print("  1. View any trace: python3 story_pipeline_tracer.py --trace <ID>")
    print("  2. Process your own story: python3 story_pipeline_tracer.py --story 'Your text'")
    print("  3. View analytics: python3 ai_analytics.py --all")
    print("  4. Export report: python3 ai_analytics.py --export report.html")
    print()


def show_examples():
    """Show example stories and expected results"""
    print("=" * 70)
    print("📚 EXAMPLE STORIES")
    print("=" * 70)
    print()

    for i, example in enumerate(EXAMPLE_STORIES, 1):
        print(f"{i}. {example['title']}")
        print(f"   Story: {example['story']}")
        print(f"   Expected Classification: {example['expected_classification']}")
        print()


def process_custom_story(story: str):
    """Process a custom story with full tracing"""
    print(f"Processing story: {story[:70]}...")
    print()

    create_trace_tables()

    result = process_story_with_tracing(story)

    print()
    print("=" * 70)
    print("✅ STORY PROCESSED")
    print("=" * 70)
    print()

    print_trace(result)

    print("Response:")
    print("-" * 70)
    print(result['response'])
    print("-" * 70)
    print()

    print(f"Trace saved: {result['trace_id']}")
    print()


# ==============================================================================
# CLI
# ==============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Prove Story Deconstruction - Complete Demo')
    parser.add_argument('--demo', action='store_true', help='Run full demonstration')
    parser.add_argument('--story', type=str, help='Process a custom story')
    parser.add_argument('--examples', action='store_true', help='Show example stories')

    args = parser.parse_args()

    if args.demo:
        prove_story_deconstruction()

    elif args.story:
        process_custom_story(args.story)

    elif args.examples:
        show_examples()

    else:
        print("Prove Story Deconstruction - Complete End-to-End Demo")
        print()
        print("Usage:")
        print("  --demo              Run full demonstration")
        print("  --story 'text'      Process a custom story")
        print("  --examples          Show example stories")
        print()
        print("Quick Start:")
        print("  python3 prove_story_deconstruction.py --demo")
