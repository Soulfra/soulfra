#!/usr/bin/env python3
"""
Test Ollama question generation directly
"""

from soulfra_games import generate_questions_with_ollama

# Test content
content = """
The Self-Documenting Platform Philosophy

Traditional software documentation becomes outdated the moment it's written.
What if instead, the platform itself could explain its own behavior through observable patterns?

This philosophy suggests that good software should be self-documenting through:
1. Clear naming conventions
2. Observable behavior patterns
3. Internal consistency
4. Predictable structure

The goal is to reduce the cognitive load of understanding a system by making its design
decisions visible and consistent throughout.
"""

title = "The Self-Documenting Platform Philosophy"

print("="*80)
print("Testing Ollama Question Generation")
print("="*80)
print()

questions = generate_questions_with_ollama(content, title, num_questions=7, model='llama3.2:3b')

print()
print("="*80)
print(f"RESULT: {len(questions)} questions generated")
print("="*80)

for i, q in enumerate(questions, 1):
    print(f"\n{i}. [{q.get('category', 'unknown')}]")
    print(f"   {q['question']}")
    print(f"   Generated from: {q.get('generated_from', 'unknown')}")
