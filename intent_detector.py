#!/usr/bin/env python3
"""
Intent Detector - Classify audio transcription intent

Determines if transcribed audio is:
- "story": Storytelling/narrative content
- "prediction": Making a prediction about the future
- "idea": Recording an idea/note/thought

Used by unified audio upload API to route to correct processing pipeline:
- Story → story_predictor.py → betting market → Reverse WPM
- Prediction → voice_to_ollama.py → AI debate → publish debates
- Idea → cringeproof_api.py → idea extraction → database

Usage:
    from intent_detector import detect_intent

    intent = detect_intent("Bitcoin will hit 100k by March")
    # Returns: "prediction"

    intent = detect_intent("Once upon a time in a quiet village...")
    # Returns: "story"
"""

import re
from typing import Literal


IntentType = Literal["story", "prediction", "idea"]


def detect_intent(text: str) -> IntentType:
    """
    Detect intent from transcribed audio text

    Args:
        text: Transcribed audio text

    Returns:
        "story", "prediction", or "idea"
    """
    text_lower = text.lower()

    # Story detection (highest priority - most specific)
    story_score = _score_story_intent(text_lower)

    # Prediction detection
    prediction_score = _score_prediction_intent(text_lower)

    # Idea detection (lowest priority - catch-all)
    idea_score = _score_idea_intent(text_lower)

    # Return highest scoring intent
    scores = {
        'story': story_score,
        'prediction': prediction_score,
        'idea': idea_score
    }

    intent = max(scores, key=scores.get)

    # Debug output
    print(f"Intent scores: Story={story_score:.1f} Prediction={prediction_score:.1f} Idea={idea_score:.1f}")
    print(f"Detected intent: {intent}")

    return intent


def _score_story_intent(text: str) -> float:
    """
    Score how likely this is storytelling

    Returns:
        Score from 0-100
    """
    score = 0.0

    # Narrative opening phrases (strong indicators)
    narrative_openings = [
        'once upon a time',
        'there was a',
        'there once was',
        'in a world',
        'long ago',
        'it was a dark',
        'the story begins',
        'chapter ',
        'part one',
        'let me tell you'
    ]

    for opening in narrative_openings:
        if opening in text:
            score += 40
            break

    # Story structure keywords
    story_keywords = {
        'protagonist': 15,
        'character': 10,
        'plot': 15,
        'suddenly': 5,
        'meanwhile': 10,
        'then': 3,
        'next': 3,
        'after that': 5,
        'before': 3,
        'scene': 10,
        'flashback': 15,
        'foreshadowing': 15
    }

    for keyword, points in story_keywords.items():
        if keyword in text:
            score += points

    # Dialogue markers (quotes often indicate storytelling)
    quote_count = text.count('"') + text.count("'he said") + text.count("she said")
    score += min(quote_count * 5, 20)

    # Past tense verbs (stories often told in past tense)
    past_tense_markers = [' was ', ' were ', ' had ', ' did ', ' went ', ' came ', ' saw ', ' said ', ' walked ']
    past_tense_count = sum(1 for marker in past_tense_markers if marker in text)
    score += min(past_tense_count * 2, 15)

    # Length (stories tend to be longer)
    word_count = len(text.split())
    if word_count > 100:
        score += 10
    elif word_count > 50:
        score += 5

    return min(score, 100)


def _score_prediction_intent(text: str) -> float:
    """
    Score how likely this is a prediction

    Returns:
        Score from 0-100
    """
    score = 0.0

    # Future tense / prediction phrases (strong indicators)
    prediction_phrases = [
        'will ',
        'going to ',
        'by the end of',
        'by ',  # "by March", "by 2027"
        'predict that',
        'my prediction',
        'i think that',
        'i believe that',
        'forecast',
        'projecting',
        'expecting',
        'anticipate',
        'should reach',
        'will hit',
        'will be',
        'is going to'
    ]

    for phrase in prediction_phrases:
        if phrase in text:
            score += 15

    # Temporal markers (dates, timeframes)
    temporal_patterns = [
        r'\b\d{4}\b',  # Years: 2026, 2027
        r'\bby [a-z]+\b',  # by March, by summer
        r'\bnext [a-z]+\b',  # next week, next year
        r'\bin \d+ (days|weeks|months|years)',  # in 6 months
        r'\bwithin \d+',  # within 30 days
        r'\bjanuary|february|march|april|may|june|july|august|september|october|november|december\b'
    ]

    for pattern in temporal_patterns:
        if re.search(pattern, text):
            score += 10

    # Measurable outcomes (numbers, percentages, prices)
    measurement_patterns = [
        r'\$[\d,]+',  # $100,000
        r'\d+k\b',  # 100k
        r'\d+%',  # 50%
        r'\d+x\b',  # 10x
        r'\d+ percent'
    ]

    for pattern in measurement_patterns:
        if re.search(pattern, text):
            score += 10

    # Market/financial keywords
    market_keywords = {
        'bitcoin': 15,
        'ethereum': 15,
        'crypto': 10,
        'stock': 10,
        'price': 8,
        'market': 8,
        'bull': 10,
        'bear': 10,
        'crash': 10,
        'rally': 10,
        'housing': 8,
        'real estate': 10,
        'inflation': 10,
        'recession': 10
    }

    for keyword, points in market_keywords.items():
        if keyword in text:
            score += points

    # Conditional language (if/when statements about future)
    conditionals = ['if ', 'when ', 'assuming ', 'provided that', 'unless ']
    conditional_count = sum(1 for cond in conditionals if cond in text)
    score += min(conditional_count * 5, 15)

    return min(score, 100)


def _score_idea_intent(text: str) -> float:
    """
    Score how likely this is an idea/note

    Returns:
        Score from 0-100
    """
    score = 20.0  # Lower base score (was too high, competing with stories)

    # Idea capture phrases
    idea_phrases = [
        'i just thought',
        'i had an idea',
        'what if',
        'we could',
        'we should',
        'reminder',
        'note to self',
        'don\'t forget',
        'remember to',
        'todo',
        'to do'
    ]

    for phrase in idea_phrases:
        if phrase in text:
            score += 20
            break

    # Action verbs (ideas often actionable)
    action_verbs = ['build', 'create', 'make', 'implement', 'design', 'develop', 'try', 'test', 'research']
    for verb in action_verbs:
        if f' {verb} ' in text or text.startswith(verb):
            score += 5

    # Question marks (ideas often posed as questions)
    score += min(text.count('?') * 10, 20)

    # Brevity (ideas tend to be shorter)
    word_count = len(text.split())
    if word_count < 30:
        score += 15
    elif word_count < 50:
        score += 10

    # Problem/solution language
    problem_solution_keywords = ['problem', 'solution', 'issue', 'fix', 'improve', 'better way']
    for keyword in problem_solution_keywords:
        if keyword in text:
            score += 8

    return min(score, 100)


def classify_with_confidence(text: str) -> dict:
    """
    Classify intent with confidence scores for all types

    Args:
        text: Transcribed audio text

    Returns:
        {
            'intent': 'story' | 'prediction' | 'idea',
            'confidence': float (0-1),
            'scores': {
                'story': float,
                'prediction': float,
                'idea': float
            }
        }
    """
    text_lower = text.lower()

    scores = {
        'story': _score_story_intent(text_lower),
        'prediction': _score_prediction_intent(text_lower),
        'idea': _score_idea_intent(text_lower)
    }

    # Normalize scores to 0-1
    max_score = max(scores.values())
    total_score = sum(scores.values())

    if total_score > 0:
        normalized_scores = {k: v / 100.0 for k, v in scores.items()}
    else:
        normalized_scores = scores

    intent = max(scores, key=scores.get)
    confidence = max_score / 100.0 if max_score > 0 else 0.3

    return {
        'intent': intent,
        'confidence': confidence,
        'scores': normalized_scores,
        'raw_scores': scores
    }


def main():
    """Demo the intent detector"""

    test_cases = [
        # Stories
        ("Once upon a time in a quiet village, there lived a young girl named Sarah. She had always dreamed of adventure.", "story"),
        ("The rain was falling hard that night. John looked out the window, thinking about what he had lost.", "story"),

        # Predictions
        ("Bitcoin will hit 100k by March 2026. The market is showing strong bullish signals.", "prediction"),
        ("I predict the housing market in California will crash by 30% within the next 18 months.", "prediction"),
        ("Ethereum is going to reach 5k before the end of the year.", "prediction"),

        # Ideas
        ("I just thought of a great app idea - what if we built a voice-to-text note taker?", "idea"),
        ("Reminder: need to research blockchain explorers for the data verification system.", "idea"),
        ("We should create a betting market for AI predictions.", "idea"),
    ]

    print("=" * 60)
    print("INTENT DETECTOR TEST")
    print("=" * 60)

    correct = 0
    total = len(test_cases)

    for text, expected in test_cases:
        print(f"\nText: {text[:80]}...")
        print(f"Expected: {expected}")

        result = classify_with_confidence(text)
        detected = result['intent']
        confidence = result['confidence']

        print(f"Detected: {detected} (confidence: {confidence:.1%})")
        print(f"Scores: Story={result['raw_scores']['story']:.0f} "
              f"Prediction={result['raw_scores']['prediction']:.0f} "
              f"Idea={result['raw_scores']['idea']:.0f}")

        if detected == expected:
            print("✅ CORRECT")
            correct += 1
        else:
            print("❌ WRONG")

    print("\n" + "=" * 60)
    print(f"Accuracy: {correct}/{total} ({correct/total:.1%})")
    print("=" * 60)


if __name__ == '__main__':
    main()
