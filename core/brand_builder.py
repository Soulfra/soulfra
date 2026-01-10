#!/usr/bin/env python3
"""
Brand Builder - Conversational Brand Creation with Ollama

Guides users through building a brand by asking questions and using
Ollama to generate brand concepts based on their answers.
"""

import json
import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from database import get_db
from config import OLLAMA_HOST

# Conversation flow steps
CONVERSATION_STEPS = {
    'intro': {
        'question': "Great! Let's start with the basics. What problem are you trying to solve?",
        'next': 'problem'
    },
    'problem': {
        'question': "Interesting! Who is your target audience? Who needs this solution?",
        'next': 'audience'
    },
    'audience': {
        'question': "Perfect! What tone fits your brand best?",
        'options': ['Professional & Serious', 'Fun & Playful', 'Bold & Rebellious', 'Calm & Trustworthy'],
        'next': 'tone'
    },
    'tone': {
        'question': "Great choice! What makes your solution unique compared to others?",
        'next': 'unique'
    },
    'unique': {
        'question': "Awesome! One last thing - if your brand was a person, what 3 words would describe them?",
        'next': 'personality'
    },
    'personality': {
        'question': "Perfect! I have everything I need. Let me create 3 brand concepts for you...",
        'next': 'generate'
    }
}


def get_or_create_conversation(session_id: str) -> int:
    """Get existing conversation or create new one"""
    conn = get_db()

    # Check if conversation exists
    existing = conn.execute(
        'SELECT id FROM conversations WHERE session_id = ?',
        (session_id,)
    ).fetchone()

    if existing:
        return existing['id']

    # Create new conversation
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO conversations (session_id, current_step, context)
        VALUES (?, 'intro', '{}')
    ''', (session_id,))

    conn.commit()
    conversation_id = cursor.lastrowid
    conn.close()

    return conversation_id


def save_message(conversation_id: int, role: str, content: str):
    """Save a chat message"""
    conn = get_db()
    conn.execute('''
        INSERT INTO conversation_messages (conversation_id, role, content)
        VALUES (?, ?, ?)
    ''', (conversation_id, role, content))
    conn.commit()
    conn.close()


def get_conversation_context(conversation_id: int) -> Dict:
    """Get conversation context as dict"""
    conn = get_db()

    conv = conn.execute(
        'SELECT context, current_step FROM conversations WHERE id = ?',
        (conversation_id,)
    ).fetchone()

    conn.close()

    if not conv:
        return {}

    try:
        context = json.loads(conv['context']) if conv['context'] else {}
        context['current_step'] = conv['current_step']
        return context
    except:
        return {'current_step': 'intro'}


def update_conversation(conversation_id: int, step: str, context: Dict):
    """Update conversation state"""
    conn = get_db()
    conn.execute('''
        UPDATE conversations
        SET current_step = ?, context = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (step, json.dumps(context), conversation_id))
    conn.commit()
    conn.close()


def call_ollama(prompt: str, max_tokens: int = 200) -> str:
    """Call Ollama API for text generation"""
    try:
        # Get first available model
        models_response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        if models_response.status_code != 200 or not models_response.json().get('models'):
            return "I'm having trouble connecting to my AI brain. Please try again in a moment."

        model_name = models_response.json()['models'][0]['name']

        # Generate response
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": 0.7
            }
        }

        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            return response.json().get('response', '').strip()
        else:
            return "Sorry, I couldn't process that. Let me try again."

    except Exception as e:
        print(f"Ollama error: {e}")
        return "I'm having trouble thinking right now. Please try again."


def process_message(session_id: str, user_message: str) -> Tuple[str, Optional[List[str]]]:
    """
    Process user message and return AI response + optional button options

    Returns: (response_text, options_list or None)
    """
    conversation_id = get_or_create_conversation(session_id)

    # Save user message
    save_message(conversation_id, 'user', user_message)

    # Get conversation context
    context = get_conversation_context(conversation_id)
    current_step = context.get('current_step', 'intro')

    # Handle initial greeting
    if current_step == 'intro' and 'do this' in user_message.lower():
        context['started'] = True
        next_step = 'problem'
        update_conversation(conversation_id, next_step, context)

        response = CONVERSATION_STEPS['intro']['question']
        save_message(conversation_id, 'assistant', response)
        return response, None

    # Handle more info request
    if 'tell me more' in user_message.lower() or 'more first' in user_message.lower():
        response = ("I'll ask you 5-6 quick questions about your brand idea. "
                   "Then I'll use AI to generate 3 unique brand concepts - complete with names, "
                   "taglines, and visual directions. Ready?")
        save_message(conversation_id, 'assistant', response)
        return response, ['Yes, let\'s start!']

    # Store answer and move to next step
    if current_step in CONVERSATION_STEPS:
        # Save the answer
        context[current_step] = user_message

        # Get next step
        step_config = CONVERSATION_STEPS[current_step]
        next_step = step_config.get('next')

        if not next_step:
            # End of conversation - generate brands
            response = generate_brand_concepts(conversation_id, context)
            save_message(conversation_id, 'assistant', response)
            return response, None

        # Move to next question
        update_conversation(conversation_id, next_step, context)

        next_config = CONVERSATION_STEPS.get(next_step, {})
        response = next_config.get('question', 'Thank you!')
        options = next_config.get('options')

        save_message(conversation_id, 'assistant', response)
        return response, options

    # Fallback
    response = "I didn't quite catch that. Can you tell me more?"
    save_message(conversation_id, 'assistant', response)
    return response, None


def generate_brand_concepts(conversation_id: int, context: Dict) -> str:
    """Generate 3 brand concepts using Ollama based on conversation"""

    # Build prompt from context
    prompt = f"""Based on this information, generate ONE creative brand name with a tagline:

Problem: {context.get('problem', 'Unknown')}
Target Audience: {context.get('audience', 'Unknown')}
Tone: {context.get('tone', 'Professional')}
Unique Value: {context.get('unique', 'Unknown')}
Personality: {context.get('personality', 'Unknown')}

Generate a brand name and one-line tagline that captures this essence. Format:
BrandName - Tagline

Be creative and memorable. Keep it short."""

    # Generate 3 concepts
    concepts = []
    for i in range(3):
        result = call_ollama(prompt)
        if result and '-' in result:
            parts = result.split('-', 1)
            brand_name = parts[0].strip()
            tagline = parts[1].strip() if len(parts) > 1 else ''

            # Save to database
            conn = get_db()
            conn.execute('''
                INSERT INTO brand_concepts
                (conversation_id, brand_name, tagline, description,
                 target_audience, tone, problem_solving, unique_value)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                conversation_id,
                brand_name,
                tagline,
                f"Generated from conversation {conversation_id}",
                context.get('audience', ''),
                context.get('tone', ''),
                context.get('problem', ''),
                context.get('unique', '')
            ))
            conn.commit()
            conn.close()

            concepts.append(f"**{brand_name}**\n_{tagline}_")

    # Return formatted concepts
    response = "🎉 Here are 3 brand concepts I created for you:\n\n"
    response += "\n\n".join(f"{i+1}. {c}" for i, c in enumerate(concepts))
    response += "\n\n✨ Which one resonates with you most?"

    return response


if __name__ == '__main__':
    # Test the conversation flow
    test_session = f"test_{datetime.now().timestamp()}"

    print("Testing brand builder conversation flow...\n")

    # Simulate conversation
    messages = [
        "Let's do this!",
        "Help people track their carbon footprint",
        "Environmentally conscious millennials",
        "Fun & Playful",
        "We make it a game with rewards",
        "Green, energetic, competitive"
    ]

    for msg in messages:
        print(f"User: {msg}")
        response, options = process_message(test_session, msg)
        print(f"AI: {response}")
        if options:
            print(f"Options: {options}")
        print()
