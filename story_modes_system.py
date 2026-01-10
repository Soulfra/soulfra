#!/usr/bin/env python3
"""
Story Modes System - Multiple AI Personalities for Same Story Content

This is like the LLM Router pattern, but for narrative storytelling:
- LLM Router: Try different models (llama2 → llama3.2 → mistral)
- Story Modes: Try different personalities (serious → funny → dramatic)

Use Cases:
- "Ridiculously funny" version of Soulfra Dark
- Documentary-style narration for educational content
- Dramatic thriller version for suspense
- Children's version (simplified language)
- Academic version (research paper style)

Example:
    from story_modes_system import StoryModeGenerator

    gen = StoryModeGenerator()

    # Get Chapter 1 in different modes
    serious = gen.generate(chapter=1, mode='serious')
    funny = gen.generate(chapter=1, mode='funny')
    dramatic = gen.generate(chapter=1, mode='dramatic')
"""

from typing import Dict, List, Optional
from soulfra_dark_story import generate_soulfra_story
from llm_router import LLMRouter


class StoryModeGenerator:
    """
    Generate multiple narrative versions of the same story content

    Like LLM Router's automatic fallback, but for creative storytelling.
    Each mode uses AI to rewrite the story in a different personality.
    """

    def __init__(self, ollama_url: str = 'http://localhost:11434'):
        """
        Initialize story mode generator

        Args:
            ollama_url: Ollama API URL (default: http://localhost:11434)
        """
        self.router = LLMRouter(ollama_url=ollama_url)

        # Define available story modes
        self.modes = {
            'serious': {
                'name': 'Serious (Original)',
                'description': 'Original Soulfra Dark storytelling',
                'prompt_template': None,  # Use original content as-is
                'icon': '📖'
            },
            'funny': {
                'name': 'Comedy Gold',
                'description': 'Ridiculously funny retelling with jokes, puns, and absurdist humor',
                'prompt_template': '''Rewrite this story chapter in a ridiculously funny style. Add:
- Unexpected punchlines and comedic timing
- Absurdist situations and characters
- Pop culture references
- Self-aware meta-humor
- Running gags throughout

Keep the core plot but make it hilariously entertaining.

Original Chapter:
{content}

Funny Version:''',
                'icon': '😂'
            },
            'dramatic': {
                'name': 'Thriller/Drama',
                'description': 'Intense, suspenseful retelling with dramatic tension',
                'prompt_template': '''Rewrite this story chapter as a dramatic thriller. Add:
- Intense suspense and tension
- Dramatic foreshadowing
- Emotional depth and character conflict
- Plot twists and cliffhangers
- Cinematic pacing

Keep the core plot but amplify the drama.

Original Chapter:
{content}

Dramatic Version:''',
                'icon': '🎭'
            },
            'documentary': {
                'name': 'Documentary Style',
                'description': 'Educational narration like a nature documentary or PBS special',
                'prompt_template': '''Rewrite this story chapter as a documentary narration (like David Attenborough or Ken Burns). Add:
- Observational third-person narration
- Educational explanations of concepts
- Historical/scientific context
- Thoughtful reflections
- Smooth transitions between scenes

Keep the core plot but present it as an educational documentary.

Original Chapter:
{content}

Documentary Version:''',
                'icon': '🎥'
            },
            'childrens': {
                'name': 'Children\'s Story',
                'description': 'Kid-friendly version with simple language and positive messages',
                'prompt_template': '''Rewrite this story chapter for children (ages 8-12). Make it:
- Simple, clear language
- Positive and encouraging tone
- Educational life lessons
- Age-appropriate themes
- Fun and engaging

Keep the core plot but make it suitable for young readers.

Original Chapter:
{content}

Children\'s Version:''',
                'icon': '👶'
            },
            'academic': {
                'name': 'Academic Analysis',
                'description': 'Research paper style with citations and scholarly tone',
                'prompt_template': '''Rewrite this story chapter as an academic research paper. Include:
- Formal scholarly tone
- Theoretical frameworks
- Citations and references
- Analysis of themes and symbols
- Critical perspectives

Keep the core plot but present it as academic literature analysis.

Original Chapter:
{content}

Academic Version:''',
                'icon': '🎓'
            },
            'noir': {
                'name': 'Film Noir',
                'description': 'Hard-boiled detective style with cynical narrator',
                'prompt_template': '''Rewrite this story chapter as film noir (1940s detective story). Add:
- Hard-boiled cynical narrator
- Femme fatales and shady characters
- Gritty urban atmosphere
- Metaphorical descriptions
- Moral ambiguity

Keep the core plot but give it noir detective vibes.

Original Chapter:
{content}

Noir Version:''',
                'icon': '🕵️'
            },
            'scifi': {
                'name': 'Hard Sci-Fi',
                'description': 'Technical sci-fi with scientific explanations',
                'prompt_template': '''Rewrite this story chapter as hard science fiction. Add:
- Scientific explanations and technical details
- Futuristic technology descriptions
- Theoretical physics concepts
- Speculative science
- Technical jargon and world-building

Keep the core plot but amplify the sci-fi elements.

Original Chapter:
{content}

Sci-Fi Version:''',
                'icon': '🚀'
            }
        }

    def generate(
        self,
        chapter: int,
        mode: str = 'serious',
        model: Optional[str] = None,
        temperature: float = 0.8
    ) -> Dict:
        """
        Generate story chapter in specified mode

        Args:
            chapter: Chapter number (1-7)
            mode: Story mode ('serious', 'funny', 'dramatic', etc.)
            model: Specific LLM model to use (optional)
            temperature: AI creativity (0.0-1.0, higher = more creative)

        Returns:
            {
                'success': True/False,
                'chapter_number': 1,
                'mode': 'funny',
                'title': 'Awakening',
                'original_content': '...',
                'rewritten_content': '...',
                'model_used': 'llama2',
                'mode_info': {...}
            }
        """
        # Validate chapter number
        chapters = generate_soulfra_story()
        if chapter < 1 or chapter > len(chapters):
            return {
                'success': False,
                'error': f'Invalid chapter number. Must be 1-{len(chapters)}'
            }

        # Validate mode
        if mode not in self.modes:
            return {
                'success': False,
                'error': f'Invalid mode. Choose from: {list(self.modes.keys())}'
            }

        # Get original chapter
        original_chapter = chapters[chapter - 1]
        mode_info = self.modes[mode]

        # If mode is 'serious', return original content
        if mode == 'serious':
            return {
                'success': True,
                'chapter_number': chapter,
                'mode': mode,
                'title': original_chapter['title'],
                'original_content': original_chapter['content'],
                'rewritten_content': original_chapter['content'],
                'model_used': None,
                'mode_info': mode_info
            }

        # Generate rewritten version using AI
        prompt = mode_info['prompt_template'].format(
            content=original_chapter['content']
        )

        result = self.router.call(
            prompt=prompt,
            system_prompt="You are a creative writer skilled at adapting stories into different narrative styles.",
            model=model,
            temperature=temperature
        )

        if not result['success']:
            return {
                'success': False,
                'error': result.get('error', 'AI generation failed'),
                'chapter_number': chapter,
                'mode': mode,
                'tried_models': result.get('tried_models', [])
            }

        return {
            'success': True,
            'chapter_number': chapter,
            'mode': mode,
            'title': original_chapter['title'],
            'original_content': original_chapter['content'],
            'rewritten_content': result['response'],
            'model_used': result['model_used'],
            'duration_ms': result.get('duration_ms', 0),
            'mode_info': mode_info
        }

    def generate_all_modes(
        self,
        chapter: int,
        exclude_modes: List[str] = None
    ) -> Dict[str, Dict]:
        """
        Generate chapter in all available modes

        Args:
            chapter: Chapter number (1-7)
            exclude_modes: Modes to skip (optional)

        Returns:
            {
                'serious': {...},
                'funny': {...},
                'dramatic': {...},
                ...
            }
        """
        exclude_modes = exclude_modes or []
        results = {}

        for mode_name in self.modes.keys():
            if mode_name not in exclude_modes:
                results[mode_name] = self.generate(chapter=chapter, mode=mode_name)

        return results

    def list_modes(self) -> List[Dict]:
        """
        Get list of available story modes

        Returns:
            [
                {'mode': 'serious', 'name': 'Serious (Original)', 'description': '...', 'icon': '📖'},
                {'mode': 'funny', 'name': 'Comedy Gold', 'description': '...', 'icon': '😂'},
                ...
            ]
        """
        return [
            {
                'mode': mode_key,
                'name': mode_data['name'],
                'description': mode_data['description'],
                'icon': mode_data['icon']
            }
            for mode_key, mode_data in self.modes.items()
        ]


# =============================================================================
# Convenience Functions
# =============================================================================

def generate_chapter_in_mode(chapter: int, mode: str = 'funny') -> str:
    """
    Quick helper: Get chapter in specified mode

    Args:
        chapter: Chapter number (1-7)
        mode: Story mode ('serious', 'funny', 'dramatic', etc.)

    Returns:
        Rewritten chapter content (or original if mode='serious')
    """
    gen = StoryModeGenerator()
    result = gen.generate(chapter=chapter, mode=mode)

    if result['success']:
        return result['rewritten_content']
    else:
        raise Exception(result.get('error', 'Generation failed'))


def compare_modes(chapter: int, modes: List[str] = None) -> Dict[str, str]:
    """
    Quick helper: Compare same chapter across multiple modes

    Args:
        chapter: Chapter number (1-7)
        modes: List of modes to compare (default: ['serious', 'funny', 'dramatic'])

    Returns:
        {
            'serious': 'original content...',
            'funny': 'funny version...',
            'dramatic': 'dramatic version...'
        }
    """
    modes = modes or ['serious', 'funny', 'dramatic']
    gen = StoryModeGenerator()

    results = {}
    for mode in modes:
        result = gen.generate(chapter=chapter, mode=mode)
        if result['success']:
            results[mode] = result['rewritten_content']
        else:
            results[mode] = f"ERROR: {result.get('error', 'Failed')}"

    return results


# =============================================================================
# Demo / Testing
# =============================================================================

if __name__ == '__main__':
    print("=== Story Modes System Demo ===\n")

    gen = StoryModeGenerator()

    # List available modes
    print("Available Story Modes:")
    for mode in gen.list_modes():
        print(f"  {mode['icon']} {mode['mode']:15} - {mode['name']}")
        print(f"     {mode['description']}\n")

    print("\n" + "="*60 + "\n")

    # Example 1: Generate Chapter 1 in Funny Mode
    print("Example 1: Chapter 1 in 'funny' mode\n")

    result = gen.generate(chapter=1, mode='funny')

    if result['success']:
        print(f"✅ Success!")
        print(f"   Chapter: {result['chapter_number']} - {result['title']}")
        print(f"   Mode: {result['mode']} {result['mode_info']['icon']}")
        print(f"   Model: {result['model_used']}")
        print(f"   Duration: {result.get('duration_ms', 0)}ms\n")
        print(f"Original (first 200 chars):")
        print(f"{result['original_content'][:200]}...\n")
        print(f"Funny Version (first 200 chars):")
        print(f"{result['rewritten_content'][:200]}...\n")
    else:
        print(f"❌ Error: {result['error']}")

    print("\n" + "="*60 + "\n")

    # Example 2: Compare multiple modes
    print("Example 2: Comparing Chapter 1 across 3 modes\n")

    comparison = compare_modes(chapter=1, modes=['serious', 'funny', 'noir'])

    for mode, content in comparison.items():
        print(f"{mode.upper()} (first 150 chars):")
        print(f"{content[:150]}...\n")

    print("\n✅ Demo complete!")
    print("\nNext Steps:")
    print("  1. Try: python3 story_modes_system.py")
    print("  2. Generate cards with modes: qr_card_printer.py + story_modes_system.py")
    print("  3. Create 'ridiculously funny' card pack for radio giveaway")
    print("  4. Build mode selector into web app (let users choose their flavor)")
