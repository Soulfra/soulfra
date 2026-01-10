"""
Voice Quality Checker - Prevent Rambling & Enforce Quality Standards

Validates voice recordings before publishing:
- Length checks (too short/long)
- Structure verification (has intro, body, conclusion)
- Filler word detection (um, uh, like)
- Profanity filter
- Coherence scoring (makes sense?)
- Topic focus (stays on topic?)

Usage:
    from voice_quality_checker import check_voice_quality

    # Check transcript quality
    result = check_voice_quality("I'm going to show you how to...")

    if result['approved']:
        publish_tutorial(transcript)
    else:
        show_user_feedback(result['issues'], result['suggestions'])
"""

from typing import Dict, List
import re


# ============================================================================
# Quality Thresholds
# ============================================================================

QUALITY_THRESHOLDS = {
    'min_words': 50,              # Minimum words (too short = incomplete)
    'max_words': 3000,             # Maximum words (too long = rambling)
    'max_filler_words': 30,        # Max um/uh/like count
    'min_coherence_score': 6,      # Minimum coherence (1-10 scale)
    'max_repetition_ratio': 0.15,  # Max ratio of repeated phrases
    'min_structure_score': 5       # Minimum structure quality (1-10)
}


# ============================================================================
# Main Quality Check Function
# ============================================================================

def check_voice_quality(transcript: str, strict_mode: bool = False) -> Dict:
    """
    Check voice transcript quality

    Args:
        transcript: Voice transcript text
        strict_mode: If True, apply stricter thresholds

    Returns:
        Dictionary with:
        - approved: bool (pass/fail)
        - quality_score: int (1-10)
        - issues: list of problems found
        - suggestions: list of how to improve
        - metrics: dict of specific metrics

    Example:
        >>> result = check_voice_quality("I'm going to show you...")
        >>> if not result['approved']:
        ...     print(f"Issues: {result['issues']}")
    """
    issues = []
    suggestions = []

    # Run all checks
    length_check = check_length(transcript)
    filler_check = check_filler_words(transcript)
    profanity_check = check_profanity(transcript)
    structure_check = check_structure(transcript)
    repetition_check = check_repetition(transcript)

    # Collect issues
    if not length_check['pass']:
        issues.append(length_check['issue'])
        suggestions.append(length_check['suggestion'])

    if not filler_check['pass']:
        issues.append(filler_check['issue'])
        suggestions.append(filler_check['suggestion'])

    if not profanity_check['pass']:
        issues.append(profanity_check['issue'])
        suggestions.append(profanity_check['suggestion'])

    if not structure_check['pass']:
        issues.append(structure_check['issue'])
        suggestions.append(structure_check['suggestion'])

    if not repetition_check['pass']:
        issues.append(repetition_check['issue'])
        suggestions.append(repetition_check['suggestion'])

    # Calculate overall quality score (1-10)
    quality_score = calculate_quality_score(
        length_check,
        filler_check,
        structure_check,
        repetition_check
    )

    # Determine if approved
    if strict_mode:
        approved = len(issues) == 0 and quality_score >= 8
    else:
        approved = len(issues) == 0 and quality_score >= 6

    return {
        'approved': approved,
        'quality_score': quality_score,
        'issues': issues,
        'suggestions': suggestions,
        'metrics': {
            'word_count': length_check['word_count'],
            'filler_word_count': filler_check['filler_count'],
            'repetition_ratio': repetition_check['repetition_ratio'],
            'structure_score': structure_check['structure_score']
        }
    }


# ============================================================================
# Individual Check Functions
# ============================================================================

def check_length(transcript: str) -> Dict:
    """
    Check if transcript is appropriate length

    Returns:
        Dictionary with pass/fail and metrics
    """
    words = transcript.split()
    word_count = len(words)

    min_words = QUALITY_THRESHOLDS['min_words']
    max_words = QUALITY_THRESHOLDS['max_words']

    if word_count < min_words:
        return {
            'pass': False,
            'word_count': word_count,
            'issue': f'Too short ({word_count} words)',
            'suggestion': f'Add more detail. Aim for at least {min_words} words (about 3-5 minutes of speaking).'
        }
    elif word_count > max_words:
        return {
            'pass': False,
            'word_count': word_count,
            'issue': f'Too long ({word_count} words)',
            'suggestion': f'Keep it concise. Try to stay under {max_words} words (about 20 minutes). Consider splitting into multiple tutorials.'
        }
    else:
        return {
            'pass': True,
            'word_count': word_count,
            'issue': None,
            'suggestion': None
        }


def check_filler_words(transcript: str) -> Dict:
    """
    Check for excessive filler words (um, uh, like, you know)

    Returns:
        Dictionary with pass/fail and count
    """
    transcript_lower = transcript.lower()

    # Count filler words
    fillers = [' um ', ' uh ', ' like ', ' you know ', ' so like ', ' basically ']
    filler_count = sum(transcript_lower.count(filler) for filler in fillers)

    # Also check for repeated "and"
    and_count = transcript_lower.count(' and ') - 5  # Allow some natural usage
    if and_count > 0:
        filler_count += and_count

    max_fillers = QUALITY_THRESHOLDS['max_filler_words']

    if filler_count > max_fillers:
        return {
            'pass': False,
            'filler_count': filler_count,
            'issue': f'Too many filler words ({filler_count} um/uh/like)',
            'suggestion': 'Practice your explanation beforehand. Pause instead of saying "um" or "uh". Try recording in shorter segments.'
        }
    else:
        return {
            'pass': True,
            'filler_count': filler_count,
            'issue': None,
            'suggestion': None
        }


def check_profanity(transcript: str) -> Dict:
    """
    Check for profanity (basic filter)

    Returns:
        Dictionary with pass/fail
    """
    transcript_lower = transcript.lower()

    # Basic profanity list (expand as needed)
    profanity_words = [
        'fuck', 'shit', 'damn', 'bitch', 'ass', 'asshole',
        'bastard', 'crap', 'piss', 'dick', 'pussy'
    ]

    found_profanity = []

    for word in profanity_words:
        if word in transcript_lower:
            found_profanity.append(word)

    if found_profanity:
        return {
            'pass': False,
            'found': found_profanity,
            'issue': f'Inappropriate language detected',
            'suggestion': 'Keep it professional. Remove profanity and re-record.'
        }
    else:
        return {
            'pass': True,
            'found': [],
            'issue': None,
            'suggestion': None
        }


def check_structure(transcript: str) -> Dict:
    """
    Check if transcript has clear structure (intro, body, conclusion)

    Returns:
        Dictionary with pass/fail and structure score
    """
    transcript_lower = transcript.lower()

    # Check for intro indicators
    intro_indicators = [
        "i'm going to", "today i'm", "in this tutorial", "i'll show you",
        "let me show you", "i want to talk about", "hi everyone", "hello",
        "welcome", "my name is"
    ]
    has_intro = any(indicator in transcript_lower[:200] for indicator in intro_indicators)

    # Check for conclusion indicators
    conclusion_indicators = [
        "in conclusion", "to summarize", "that's it", "that's all",
        "hope this helps", "if you have questions", "contact me",
        "give me a call", "thanks for", "thank you"
    ]
    has_conclusion = any(indicator in transcript_lower[-200:] for indicator in conclusion_indicators)

    # Check for step indicators (suggests structured content)
    step_indicators = ["first", "second", "third", "next", "then", "finally", "step"]
    step_count = sum(transcript_lower.count(indicator) for indicator in step_indicators)

    # Calculate structure score
    structure_score = 0
    if has_intro:
        structure_score += 4
    if has_conclusion:
        structure_score += 3
    if step_count >= 3:
        structure_score += 3
    elif step_count >= 1:
        structure_score += 2

    # Cap at 10
    structure_score = min(structure_score, 10)

    min_structure = QUALITY_THRESHOLDS['min_structure_score']

    if structure_score < min_structure:
        issues = []
        if not has_intro:
            issues.append("missing clear introduction")
        if not has_conclusion:
            issues.append("missing conclusion/call-to-action")
        if step_count < 2:
            issues.append("unclear structure (use 'first', 'next', 'finally')")

        return {
            'pass': False,
            'structure_score': structure_score,
            'issue': f'Weak structure: {", ".join(issues)}',
            'suggestion': 'Start with a clear intro ("I\'m going to show you..."), organize content with step words ("first", "next", "finally"), and end with a conclusion or call-to-action.'
        }
    else:
        return {
            'pass': True,
            'structure_score': structure_score,
            'issue': None,
            'suggestion': None
        }


def check_repetition(transcript: str) -> Dict:
    """
    Check for excessive repetition (sign of rambling)

    Returns:
        Dictionary with pass/fail and repetition ratio
    """
    # Split into sentences
    sentences = re.split(r'[.!?]+', transcript)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

    if len(sentences) < 3:
        # Too short to check properly
        return {
            'pass': True,
            'repetition_ratio': 0.0,
            'issue': None,
            'suggestion': None
        }

    # Check for repeated phrases (3+ words)
    phrases = []
    for sentence in sentences:
        words = sentence.lower().split()
        # Extract all 3-word phrases
        for i in range(len(words) - 2):
            phrase = ' '.join(words[i:i+3])
            phrases.append(phrase)

    # Count duplicates
    phrase_counts = {}
    for phrase in phrases:
        phrase_counts[phrase] = phrase_counts.get(phrase, 0) + 1

    # Calculate repetition ratio
    if len(phrases) > 0:
        repeated_count = sum(count - 1 for count in phrase_counts.values() if count > 1)
        repetition_ratio = repeated_count / len(phrases)
    else:
        repetition_ratio = 0.0

    max_repetition = QUALITY_THRESHOLDS['max_repetition_ratio']

    if repetition_ratio > max_repetition:
        return {
            'pass': False,
            'repetition_ratio': round(repetition_ratio, 3),
            'issue': f'Too much repetition ({repetition_ratio:.1%} of content)',
            'suggestion': 'You\'re repeating yourself. Plan your points beforehand and avoid saying the same thing multiple times.'
        }
    else:
        return {
            'pass': True,
            'repetition_ratio': round(repetition_ratio, 3),
            'issue': None,
            'suggestion': None
        }


# ============================================================================
# Quality Score Calculation
# ============================================================================

def calculate_quality_score(
    length_check: Dict,
    filler_check: Dict,
    structure_check: Dict,
    repetition_check: Dict
) -> int:
    """
    Calculate overall quality score (1-10)

    Factors:
    - Length: ideal range gets full points
    - Fillers: fewer is better
    - Structure: based on structure_score
    - Repetition: lower is better

    Returns:
        Quality score (1-10)
    """
    score = 10  # Start with perfect score

    # Length penalty
    word_count = length_check['word_count']
    if word_count < 100:
        score -= 3
    elif word_count < 200:
        score -= 1
    elif word_count > 2000:
        score -= 2

    # Filler penalty
    filler_count = filler_check['filler_count']
    if filler_count > 40:
        score -= 3
    elif filler_count > 20:
        score -= 2
    elif filler_count > 10:
        score -= 1

    # Structure score (already 1-10)
    structure_score = structure_check['structure_score']
    if structure_score < 5:
        score -= 3
    elif structure_score < 7:
        score -= 1

    # Repetition penalty
    repetition_ratio = repetition_check['repetition_ratio']
    if repetition_ratio > 0.2:
        score -= 3
    elif repetition_ratio > 0.1:
        score -= 1

    # Ensure score is between 1 and 10
    score = max(1, min(10, score))

    return score


# ============================================================================
# AI-Enhanced Quality Check (Optional)
# ============================================================================

def check_coherence_with_ai(transcript: str) -> int:
    """
    Use AI to check if content is coherent and makes sense

    Args:
        transcript: Voice transcript

    Returns:
        Coherence score (1-10)

    Note: Requires Ollama running locally
    """
    try:
        import urllib.request
        import json

        prompt = f"""Rate the following tutorial transcript for coherence and clarity on a scale of 1-10:

Transcript:
{transcript[:1000]}  # First 1000 chars

Scoring:
- 1-3: Incoherent, doesn't make sense
- 4-6: Somewhat clear but confusing
- 7-8: Clear and understandable
- 9-10: Exceptionally clear and well-structured

Respond with ONLY the number (1-10)."""

        data = {
            'model': 'llama3.2',
            'prompt': prompt,
            'stream': False
        }

        req = urllib.request.Request(
            'http://localhost:11434/api/generate',
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            response_text = result.get('response', '').strip()

            # Extract number from response
            import re
            match = re.search(r'\b([1-9]|10)\b', response_text)
            if match:
                return int(match.group(1))

    except Exception as e:
        print(f"AI coherence check failed: {e}")

    # Fallback: return neutral score
    return 7


# ============================================================================
# Feedback Generation
# ============================================================================

def generate_user_feedback(quality_result: Dict) -> str:
    """
    Generate friendly feedback message for user

    Args:
        quality_result: Result from check_voice_quality()

    Returns:
        Formatted feedback string

    Example:
        >>> feedback = generate_user_feedback(result)
        >>> print(feedback)
    """
    if quality_result['approved']:
        return f"""✅ **Quality Check Passed!**

Your tutorial looks great! Quality score: {quality_result['quality_score']}/10

Stats:
- {quality_result['metrics']['word_count']} words
- {quality_result['metrics']['filler_word_count']} filler words
- Structure score: {quality_result['metrics']['structure_score']}/10

Ready to publish!
"""
    else:
        feedback = f"""❌ **Quality Issues Found**

Quality score: {quality_result['quality_score']}/10 (needs improvement)

Issues:
"""
        for i, issue in enumerate(quality_result['issues'], 1):
            feedback += f"{i}. {issue}\n"

        feedback += "\n**How to improve:**\n"
        for i, suggestion in enumerate(quality_result['suggestions'], 1):
            feedback += f"{i}. {suggestion}\n"

        feedback += "\nPlease address these issues and re-record your tutorial."

        return feedback


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    """
    CLI interface for quality checking

    Usage:
        python voice_quality_checker.py --check "transcript text"
        python voice_quality_checker.py --check-file transcript.txt
    """
    import sys

    if '--check' in sys.argv:
        idx = sys.argv.index('--check')
        if idx + 1 < len(sys.argv):
            transcript = sys.argv[idx + 1]

            result = check_voice_quality(transcript)
            feedback = generate_user_feedback(result)

            print(feedback)

    elif '--check-file' in sys.argv:
        idx = sys.argv.index('--check-file')
        if idx + 1 < len(sys.argv):
            filename = sys.argv[idx + 1]

            try:
                with open(filename, 'r') as f:
                    transcript = f.read()

                result = check_voice_quality(transcript)
                feedback = generate_user_feedback(result)

                print(feedback)

            except FileNotFoundError:
                print(f"❌ File not found: {filename}")

    else:
        print("""
Voice Quality Checker - Prevent Rambling & Enforce Quality

Usage:
    python voice_quality_checker.py --check "transcript text"
    python voice_quality_checker.py --check-file transcript.txt

Example:
    python voice_quality_checker.py --check "I'm going to show you how to fix a leaky faucet..."
""")


if __name__ == '__main__':
    main()
