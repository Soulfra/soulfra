#!/usr/bin/env python3
"""
Voice SEO Pattern Detector - Find Hidden Advertising Opportunities in Voice Recordings

Traditional SEO: Research keywords manually → Write content around them
Voice SEO: Speak naturally → Algorithm finds SEO patterns → Auto-generate content

Detects:
- Long-tail keywords (multi-word search phrases)
- Compound terms (hyphenated, underscored)
- Natural speech patterns that match search queries
- Advertising keyword targets
- URL slug opportunities
- Technical term formats

Example:
    Transcript: "Ideas is about cringe proof. It's a game where you talk
                 about news articles and they get scraped from Google"

    Basic Wordmap: ideas, cringe, proof, game, news, articles, google

    SEO Patterns Detected:
    - "cringe-proof game" (long-tail keyword)
    - "news article scraper" (search term)
    - "google news feeds" (ad target)
    - "game where you talk" (conversational query)
    - "_cringe_proof_ideas" (technical format)

Usage:
    from voice_seo_pattern_detector import VoiceSEODetector

    detector = VoiceSEODetector()
    patterns = detector.analyze_recording(recording_id=5)
    print(patterns['long_tail_keywords'])

CLI:
    python3 voice_seo_pattern_detector.py --recording 5
    python3 voice_seo_pattern_detector.py --user 1 --all
"""

import re
import json
import sys
from typing import Dict, List, Set
from database import get_db
from collections import Counter


class VoiceSEODetector:
    """Detect SEO and advertising patterns in voice recordings"""

    def __init__(self):
        self.db = get_db()

        # Common stop words to filter out
        self.stop_words = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'will', 'with', 'you', 'they', 'this', 'but', 'or',
            'where', 'when', 'who', 'what', 'why', 'how', 'about'
        }

    def analyze_recording(self, recording_id: int) -> Dict:
        """
        Analyze a recording for SEO patterns

        Returns:
            {
                'recording_id': int,
                'transcript': str,
                'patterns_detected': {
                    'long_tail_keywords': [str],
                    'compound_phrases': [str],
                    'technical_formats': [str],
                    'advertising_targets': [str],
                    'url_slug_opportunities': [str],
                    'conversational_queries': [str]
                },
                'seo_score': float (0-100),
                'estimated_search_volume': str,
                'monetization_potential': str
            }
        """
        # Get recording
        rec = self.db.execute('''
            SELECT id, user_id, transcription, filename
            FROM simple_voice_recordings
            WHERE id = ?
        ''', (recording_id,)).fetchone()

        if not rec or not rec['transcription']:
            return {'error': 'No transcription found'}

        transcript = rec['transcription']

        result = {
            'recording_id': recording_id,
            'transcript': transcript,
            'patterns_detected': {},
            'seo_score': 0,
            'estimated_search_volume': 'unknown',
            'monetization_potential': 'unknown'
        }

        # Extract all patterns
        result['patterns_detected']['long_tail_keywords'] = self._extract_long_tail(transcript)
        result['patterns_detected']['compound_phrases'] = self._extract_compound_phrases(transcript)
        result['patterns_detected']['technical_formats'] = self._extract_technical_formats(transcript)
        result['patterns_detected']['advertising_targets'] = self._extract_ad_targets(transcript)
        result['patterns_detected']['url_slug_opportunities'] = self._generate_url_slugs(transcript)
        result['patterns_detected']['conversational_queries'] = self._extract_conversational_queries(transcript)

        # Calculate SEO score
        result['seo_score'] = self._calculate_seo_score(result['patterns_detected'])

        # Estimate search volume and monetization potential
        result['estimated_search_volume'] = self._estimate_search_volume(result['patterns_detected'])
        result['monetization_potential'] = self._estimate_monetization(result['seo_score'])

        return result

    def _extract_long_tail(self, transcript: str) -> List[str]:
        """
        Extract 2-4 word phrases (long-tail keywords)

        Long-tail keywords are specific, multi-word search queries with:
        - Lower competition
        - Higher conversion rates
        - More specific intent
        """
        words = self._tokenize(transcript)
        long_tail = []

        # Extract 2-word phrases
        for i in range(len(words) - 1):
            phrase = f"{words[i]} {words[i+1]}"
            if self._is_valuable_phrase(words[i], words[i+1]):
                long_tail.append(phrase)

        # Extract 3-word phrases
        for i in range(len(words) - 2):
            phrase = f"{words[i]} {words[i+1]} {words[i+2]}"
            if self._is_valuable_phrase(words[i], words[i+1], words[i+2]):
                long_tail.append(phrase)

        # Extract 4-word phrases (super specific)
        for i in range(len(words) - 3):
            phrase = f"{words[i]} {words[i+1]} {words[i+2]} {words[i+3]}"
            if self._is_valuable_phrase(words[i], words[i+1], words[i+2], words[i+3]):
                long_tail.append(phrase)

        # Deduplicate and sort by potential value
        return list(set(long_tail))[:15]  # Top 15

    def _extract_compound_phrases(self, transcript: str) -> List[str]:
        """
        Extract compound phrases and create hyphenated/underscored versions

        Examples:
        - "cringe proof" → "cringe-proof", "cringe_proof"
        - "news article" → "news-article", "news_article"
        """
        words = self._tokenize(transcript)
        compounds = []

        # 2-word compounds
        for i in range(len(words) - 1):
            if not self._is_stop_word(words[i]) and not self._is_stop_word(words[i+1]):
                compounds.append(f"{words[i]}-{words[i+1]}")
                compounds.append(f"{words[i]}_{words[i+1]}")

        # 3-word compounds (less common but valuable)
        for i in range(len(words) - 2):
            if all(not self._is_stop_word(w) for w in [words[i], words[i+1], words[i+2]]):
                compounds.append(f"{words[i]}-{words[i+1]}-{words[i+2]}")

        return list(set(compounds))[:20]  # Top 20

    def _extract_technical_formats(self, transcript: str) -> List[str]:
        """
        Generate technical term formats (for product names, code, URLs)

        Examples:
        - "CringeProof" (PascalCase)
        - "cringe_proof" (snake_case)
        - "CRINGE_PROOF" (SCREAMING_SNAKE_CASE)
        - "cringeProof" (camelCase)
        """
        words = self._tokenize(transcript)
        technical = []

        # Take most important 2-word pairs
        for i in range(len(words) - 1):
            if not self._is_stop_word(words[i]) and not self._is_stop_word(words[i+1]):
                w1, w2 = words[i], words[i+1]

                # PascalCase
                technical.append(f"{w1.capitalize()}{w2.capitalize()}")

                # camelCase
                technical.append(f"{w1.lower()}{w2.capitalize()}")

                # snake_case
                technical.append(f"{w1.lower()}_{w2.lower()}")

                # SCREAMING_SNAKE_CASE
                technical.append(f"{w1.upper()}_{w2.upper()}")

        return list(set(technical))[:15]  # Top 15

    def _extract_ad_targets(self, transcript: str) -> List[str]:
        """
        Extract keywords worth bidding on for Google Ads / Meta Ads

        Focuses on:
        - Action words (verbs)
        - Product-related nouns
        - Problem/solution terms
        """
        words = self._tokenize(transcript)
        ad_targets = []

        # Action verb + noun combinations (high intent)
        action_verbs = {'talk', 'create', 'build', 'make', 'get', 'use', 'find', 'learn', 'play', 'scrape', 'input'}

        for i in range(len(words) - 1):
            if words[i] in action_verbs:
                ad_targets.append(f"{words[i]} {words[i+1]}")

        # Product/tool keywords
        product_terms = {'game', 'tool', 'app', 'system', 'platform', 'service'}
        for i in range(len(words)):
            if words[i] in product_terms and i > 0:
                ad_targets.append(f"{words[i-1]} {words[i]}")

        return list(set(ad_targets))[:10]  # Top 10

    def _generate_url_slugs(self, transcript: str) -> List[str]:
        """
        Generate SEO-friendly URL slugs from voice content

        Examples:
        - "/game/cringe-proof-news"
        - "/tools/news-scraper"
        - "/how-to/talk-about-articles"
        """
        words = self._tokenize(transcript)
        slugs = []

        # Category-based slugs
        categories = {
            'game': ['game', 'play'],
            'tool': ['tool', 'tools', 'scraper'],
            'guide': ['guide', 'how', 'learn'],
            'app': ['app', 'application']
        }

        for cat, triggers in categories.items():
            for i in range(len(words)):
                if words[i] in triggers and i < len(words) - 2:
                    slug = f"/{cat}/{words[i+1]}-{words[i+2]}"
                    slugs.append(slug)

        # Generic 2-word slugs
        for i in range(len(words) - 1):
            if not self._is_stop_word(words[i]) and not self._is_stop_word(words[i+1]):
                slugs.append(f"/{words[i]}-{words[i+1]}")

        return list(set(slugs))[:10]  # Top 10

    def _extract_conversational_queries(self, transcript: str) -> List[str]:
        """
        Extract conversational search queries (voice search optimization)

        Voice searches are:
        - Longer (3-5+ words)
        - More conversational
        - Question-based
        """
        # Look for question patterns
        question_words = ['how', 'what', 'where', 'when', 'why', 'who']

        sentences = transcript.split('.')
        queries = []

        for sentence in sentences:
            words = sentence.lower().strip().split()
            if any(q in words for q in question_words):
                # This is a potential voice query
                queries.append(sentence.strip())

        # Also extract action-based queries
        action_patterns = [
            r'(how to \w+ \w+)',
            r'(ways to \w+ \w+)',
            r'(best \w+ for \w+)'
        ]

        for pattern in action_patterns:
            matches = re.findall(pattern, transcript.lower())
            queries.extend(matches)

        return queries[:5]  # Top 5

    def _calculate_seo_score(self, patterns: Dict) -> float:
        """Calculate overall SEO potential score (0-100)"""
        score = 0

        # Long-tail keywords (most valuable)
        score += min(len(patterns.get('long_tail_keywords', [])) * 5, 30)

        # Compound phrases
        score += min(len(patterns.get('compound_phrases', [])) * 2, 20)

        # Technical formats (product names)
        score += min(len(patterns.get('technical_formats', [])) * 2, 15)

        # Advertising targets
        score += min(len(patterns.get('advertising_targets', [])) * 3, 20)

        # URL slugs
        score += min(len(patterns.get('url_slug_opportunities', [])) * 1, 10)

        # Conversational queries (voice search)
        score += min(len(patterns.get('conversational_queries', [])) * 1, 5)

        return min(score, 100)

    def _estimate_search_volume(self, patterns: Dict) -> str:
        """Estimate combined search volume potential"""
        total_keywords = sum(len(v) for v in patterns.values() if isinstance(v, list))

        if total_keywords > 50:
            return 'high (50+ potential keywords)'
        elif total_keywords > 20:
            return 'medium (20-50 potential keywords)'
        elif total_keywords > 5:
            return 'low (5-20 potential keywords)'
        else:
            return 'very low (<5 keywords)'

    def _estimate_monetization(self, seo_score: float) -> str:
        """Estimate monetization potential based on SEO score"""
        if seo_score >= 75:
            return 'excellent - high ad revenue potential'
        elif seo_score >= 50:
            return 'good - moderate ad revenue'
        elif seo_score >= 25:
            return 'fair - some monetization possible'
        else:
            return 'low - needs richer content'

    def _tokenize(self, text: str) -> List[str]:
        """Convert text to lowercase word list"""
        # Remove punctuation, convert to lowercase, split
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        return [w for w in text.split() if w]

    def _is_stop_word(self, word: str) -> bool:
        """Check if word is a stop word"""
        return word.lower() in self.stop_words

    def _is_valuable_phrase(self, *words) -> bool:
        """Check if phrase has SEO value (not all stop words)"""
        # Phrase is valuable if at least one word is NOT a stop word
        return any(not self._is_stop_word(w) for w in words)

    def print_report(self, analysis: Dict):
        """Print formatted SEO analysis report"""
        if 'error' in analysis:
            print(f"\n❌ Error: {analysis['error']}\n")
            return

        rid = analysis['recording_id']
        score = analysis['seo_score']

        print(f"\n{'='*70}")
        print(f"🔍 SEO Pattern Analysis - Recording #{rid}")
        print(f"{'='*70}\n")

        print(f"SEO Score: {score:.0f}/100")
        print(f"Search Volume: {analysis['estimated_search_volume']}")
        print(f"Monetization: {analysis['monetization_potential']}")

        print(f"\n{'─'*70}")
        print("Long-Tail Keywords:")
        for keyword in analysis['patterns_detected']['long_tail_keywords'][:10]:
            print(f"  • {keyword}")

        print(f"\n{'─'*70}")
        print("Compound Phrases:")
        for phrase in analysis['patterns_detected']['compound_phrases'][:10]:
            print(f"  • {phrase}")

        print(f"\n{'─'*70}")
        print("Technical Formats:")
        for fmt in analysis['patterns_detected']['technical_formats'][:8]:
            print(f"  • {fmt}")

        print(f"\n{'─'*70}")
        print("Advertising Targets:")
        for target in analysis['patterns_detected']['advertising_targets']:
            print(f"  • {target}")

        print(f"\n{'─'*70}")
        print("URL Slugs:")
        for slug in analysis['patterns_detected']['url_slug_opportunities'][:5]:
            print(f"  • {slug}")

        if analysis['patterns_detected']['conversational_queries']:
            print(f"\n{'─'*70}")
            print("Voice Search Queries:")
            for query in analysis['patterns_detected']['conversational_queries']:
                print(f"  • {query}")

        print(f"\n{'='*70}\n")


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Voice SEO Pattern Detector')
    parser.add_argument('--recording', type=int, help='Analyze specific recording ID')
    parser.add_argument('--user', type=int, help='Analyze all recordings for user')
    parser.add_argument('--all', action='store_true', help='Analyze all recordings for user')

    args = parser.parse_args()

    detector = VoiceSEODetector()

    if args.recording:
        # Analyze single recording
        analysis = detector.analyze_recording(args.recording)
        detector.print_report(analysis)

    elif args.user:
        # Analyze all recordings for user
        db = get_db()
        recordings = db.execute('''
            SELECT id FROM simple_voice_recordings
            WHERE user_id = ? AND transcription IS NOT NULL
            ORDER BY created_at DESC
        ''', (args.user,)).fetchall()

        print(f"\n🔍 Analyzing {len(recordings)} recordings for user {args.user}...\n")

        for rec in recordings:
            analysis = detector.analyze_recording(rec['id'])
            if 'error' not in analysis:
                detector.print_report(analysis)

    else:
        print("\nUsage:")
        print("  python3 voice_seo_pattern_detector.py --recording 5")
        print("  python3 voice_seo_pattern_detector.py --user 1 --all")
        print()
        sys.exit(1)


if __name__ == '__main__':
    main()
