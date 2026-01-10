#!/usr/bin/env python3
"""
Voice Query Processor - Convert Voice Transcription to Search Query

Takes voice transcription → processes with Ollama → returns search results
Like Google Voice Search + Siri + ChatGPT combined

Features:
- Voice intent detection (search, command, question)
- Semantic search via Ollama
- Query enhancement (expand keywords)
- Natural language understanding
- Context-aware responses

Flow:
1. Receive voice transcription
2. Detect intent (search/command/question)
3. Extract entities/keywords
4. Query Ollama for semantic search
5. Return formatted results

Usage:
    from voice_query_processor import process_voice_query

    result = process_voice_query("Show me privacy articles")
    # Returns: {
    #   'intent': 'search',
    #   'query': 'privacy',
    #   'results': [...],
    #   'response': 'Found 5 articles about privacy'
    # }
"""

import requests
import json
from typing import Dict, List, Optional
from database import get_db
import re


class VoiceQueryProcessor:
    """Process voice transcriptions into actionable search queries"""

    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.db = get_db()

    def process(self, transcription: str, user_id: Optional[int] = None) -> Dict:
        """
        Process voice transcription into search results

        Args:
            transcription: Voice transcription text
            user_id: Optional user ID for personalization

        Returns:
            {
                'intent': 'search' | 'command' | 'question',
                'original_text': transcription,
                'enhanced_query': processed query,
                'keywords': [extracted keywords],
                'results': [search results],
                'ai_response': natural language response,
                'faucet_unlocked': bool,
                'domains_unlocked': [domain names]
            }
        """
        # Step 1: Detect intent
        intent = self._detect_intent(transcription)

        # Step 2: Extract keywords
        keywords = self._extract_keywords(transcription)

        # Step 3: Enhance query with Ollama
        enhanced_query = self._enhance_query_with_ollama(transcription, intent)

        # Step 4: Search database
        results = self._search_content(keywords, enhanced_query)

        # Step 5: Check faucet unlock
        faucet_result = self._check_faucet_unlock(keywords, user_id)

        # Step 6: Generate natural language response
        ai_response = self._generate_response(transcription, intent, results, faucet_result)

        return {
            'intent': intent,
            'original_text': transcription,
            'enhanced_query': enhanced_query,
            'keywords': keywords,
            'results': results,
            'ai_response': ai_response,
            'faucet_unlocked': faucet_result['unlocked'],
            'domains_unlocked': faucet_result.get('domains', [])
        }

    def _detect_intent(self, text: str) -> str:
        """
        Detect intent from transcription

        Returns:
            'search' - looking for content
            'command' - action to perform
            'question' - asking for information
        """
        text_lower = text.lower()

        # Command patterns
        command_keywords = ['open', 'show me', 'navigate to', 'go to', 'play', 'start']
        if any(keyword in text_lower for keyword in command_keywords):
            return 'command'

        # Question patterns
        question_words = ['what', 'why', 'how', 'when', 'where', 'who', 'is', 'are', 'can', 'do']
        if any(text_lower.startswith(word) for word in question_words):
            return 'question'

        # Default to search
        return 'search'

    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract important keywords from transcription

        Returns list of keywords
        """
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                     'of', 'with', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                     'show', 'me', 'find', 'search', 'look', 'get'}

        # Clean and tokenize
        words = re.findall(r'\b\w+\b', text.lower())

        # Filter stop words and short words
        keywords = [word for word in words if word not in stop_words and len(word) > 2]

        return keywords[:10]  # Top 10 keywords

    def _enhance_query_with_ollama(self, transcription: str, intent: str) -> str:
        """
        Use Ollama to enhance and expand the search query

        Returns enhanced query string
        """
        try:
            # Ask Ollama to extract the core search intent
            prompt = f"""Extract the main search query from this voice input. Return ONLY the search keywords, nothing else.

Voice input: "{transcription}"
Intent: {intent}

Search keywords:"""

            response = requests.post(
                f'{self.ollama_url}/api/generate',
                json={
                    'model': 'llama3.2:latest',
                    'prompt': prompt,
                    'stream': False,
                    'options': {'temperature': 0.3}  # Low temperature for focused extraction
                },
                timeout=10
            )

            if response.status_code == 200:
                enhanced = response.json().get('response', '').strip()

                # Remove quotes if Ollama added them
                enhanced = enhanced.strip('"\'').strip()

                # Fallback to original if enhancement is empty
                return enhanced if enhanced else transcription
            else:
                return transcription

        except Exception as e:
            print(f"Ollama enhancement failed: {e}")
            return transcription

    def _search_content(self, keywords: List[str], enhanced_query: str) -> List[Dict]:
        """
        Search for content in database using keywords

        Returns list of matching content
        """
        results = []

        # Search posts
        for keyword in keywords[:5]:  # Top 5 keywords
            posts = self.db.execute('''
                SELECT id, title, content, slug, brand, created_at
                FROM posts
                WHERE title LIKE ? OR content LIKE ?
                ORDER BY created_at DESC
                LIMIT 5
            ''', (f'%{keyword}%', f'%{keyword}%')).fetchall()

            for post in posts:
                result = dict(post)
                result['type'] = 'post'
                result['match_keyword'] = keyword
                results.append(result)

        # Remove duplicates
        seen_ids = set()
        unique_results = []
        for result in results:
            if result['id'] not in seen_ids:
                seen_ids.add(result['id'])
                unique_results.append(result)

        return unique_results[:10]  # Top 10 results

    def _check_faucet_unlock(self, keywords: List[str], user_id: Optional[int]) -> Dict:
        """
        Check if voice keywords unlock any domains via faucet

        Returns unlock status and domains
        """
        if not user_id:
            return {'unlocked': False, 'domains': []}

        unlocked_domains = []

        # Check domain contexts for keyword matches
        for keyword in keywords:
            domains = self.db.execute('''
                SELECT domain, tier, required_mentions
                FROM domain_contexts
                WHERE contexts LIKE ?
                LIMIT 5
            ''', (f'%{keyword}%',)).fetchall()

            for domain_row in domains:
                domain = domain_row['domain']

                # Check if user has mentioned this keyword enough
                # (In real implementation, track keyword mentions per user)
                unlocked_domains.append({
                    'domain': domain,
                    'tier': domain_row['tier'],
                    'keyword': keyword
                })

        return {
            'unlocked': len(unlocked_domains) > 0,
            'domains': unlocked_domains[:5]  # Top 5 unlocked
        }

    def _generate_response(self, transcription: str, intent: str,
                          results: List[Dict], faucet_result: Dict) -> str:
        """
        Generate natural language response using Ollama

        Returns conversational response
        """
        try:
            # Build context from results
            result_summary = ""
            if results:
                result_summary = f"\nFound {len(results)} results:\n"
                for i, result in enumerate(results[:3], 1):
                    result_summary += f"{i}. {result['title']} (in {result['brand']})\n"

            # Build faucet context
            faucet_summary = ""
            if faucet_result['unlocked']:
                domains = [d['domain'] for d in faucet_result['domains']]
                faucet_summary = f"\n🎉 You unlocked access to: {', '.join(domains)}"

            # Generate response
            prompt = f"""You are a helpful voice assistant. Respond naturally to this voice query.

Query: "{transcription}"
Intent: {intent}
{result_summary}{faucet_summary}

Provide a concise, conversational response (2-3 sentences):"""

            response = requests.post(
                f'{self.ollama_url}/api/generate',
                json={
                    'model': 'llama3.2:latest',
                    'prompt': prompt,
                    'stream': False,
                    'options': {'temperature': 0.7}
                },
                timeout=15
            )

            if response.status_code == 200:
                ai_text = response.json().get('response', '').strip()
                return ai_text if ai_text else self._fallback_response(transcription, results)
            else:
                return self._fallback_response(transcription, results)

        except Exception as e:
            print(f"AI response generation failed: {e}")
            return self._fallback_response(transcription, results)

    def _fallback_response(self, transcription: str, results: List[Dict]) -> str:
        """Simple fallback response when Ollama unavailable"""
        if results:
            return f"I found {len(results)} results for '{transcription}'. Check out the top matches below."
        else:
            return f"I couldn't find anything for '{transcription}'. Try different keywords."


# Convenience function
def process_voice_query(transcription: str, user_id: Optional[int] = None) -> Dict:
    """
    Process voice query and return results

    Args:
        transcription: Voice transcription text
        user_id: Optional user ID

    Returns:
        Query processing results
    """
    processor = VoiceQueryProcessor()
    return processor.process(transcription, user_id)


# CLI for testing
if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        query = ' '.join(sys.argv[1:])

        print(f"\n🎤 Processing voice query: '{query}'\n")

        result = process_voice_query(query)

        print(f"Intent: {result['intent']}")
        print(f"Keywords: {', '.join(result['keywords'])}")
        print(f"Enhanced Query: {result['enhanced_query']}")
        print(f"\nAI Response:")
        print(f"  {result['ai_response']}")

        if result['results']:
            print(f"\nSearch Results ({len(result['results'])}):")
            for i, res in enumerate(result['results'][:5], 1):
                print(f"  {i}. {res['title']} ({res['brand']})")

        if result['faucet_unlocked']:
            print(f"\n🎉 Domains Unlocked:")
            for domain in result['domains_unlocked']:
                print(f"  - {domain['domain']} (via keyword: {domain['keyword']})")

        print()
    else:
        print("\nVoice Query Processor")
        print("\nUsage:")
        print("  python3 voice_query_processor.py <voice query>")
        print("\nExamples:")
        print("  python3 voice_query_processor.py show me privacy articles")
        print("  python3 voice_query_processor.py what is encryption")
        print("  python3 voice_query_processor.py find posts about AI")
        print()
