#!/usr/bin/env python3
"""
Local Ollama Client - Privacy-Preserving AI

Run AI models entirely on your own machine. No cloud, no API keys, no tracking.

Philosophy:
- Your data never leaves your machine
- Models run locally via Ollama
- Works offline
- Free forever (after downloading models)

Models supported:
- llama3.2:3b (fast, good for chat)
- mistral:7b (balanced)
- codellama:7b (code generation)
- deepseek-coder:6.7b (code understanding)

Like running your own ChatGPT, but:
- Privacy-first
- Offline-capable
- Free (no API costs)
- Full control
"""

import json
import requests
from typing import Dict, List, Optional, Generator
from datetime import datetime

# ==============================================================================
# CONFIGURATION
# ==============================================================================

OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "llama3.2:3b"

# Model profiles
MODELS = {
    'chat': 'llama3.2:3b',        # Fast chat (3B params)
    'writing': 'mistral:7b',       # Better writing quality
    'code': 'codellama:7b',        # Code generation
    'analysis': 'deepseek-coder:6.7b',  # Code understanding
}

# ==============================================================================
# OLLAMA CLIENT
# ==============================================================================

class OllamaClient:
    """Local Ollama client for privacy-preserving AI"""

    def __init__(self, base_url: str = OLLAMA_BASE_URL):
        self.base_url = base_url

    def is_running(self) -> bool:
        """Check if Ollama is running"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False

    def list_models(self) -> List[Dict]:
        """List installed models"""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                return data.get('models', [])
            return []
        except:
            return []

    def pull_model(self, model_name: str) -> Generator[Dict, None, None]:
        """
        Pull/download a model from Ollama library

        Args:
            model_name: Model to download (e.g., 'llama3.2:3b')

        Yields:
            Progress updates
        """
        url = f"{self.base_url}/api/pull"
        data = {'name': model_name, 'stream': True}

        try:
            response = requests.post(url, json=data, stream=True)

            for line in response.iter_lines():
                if line:
                    yield json.loads(line)
        except Exception as e:
            yield {'error': str(e)}

    def generate(
        self,
        prompt: str,
        model: str = DEFAULT_MODEL,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Dict:
        """
        Generate text from prompt

        Args:
            prompt: User prompt
            model: Model to use
            system: System prompt (role/instructions)
            temperature: Randomness (0-1)
            max_tokens: Max tokens to generate
            stream: Stream response

        Returns:
            {'response': str, 'model': str, 'created_at': str}
        """
        url = f"{self.base_url}/api/generate"

        data = {
            'model': model,
            'prompt': prompt,
            'stream': stream,
            'options': {
                'temperature': temperature,
            }
        }

        if system:
            data['system'] = system

        if max_tokens:
            data['options']['num_predict'] = max_tokens

        try:
            response = requests.post(url, json=data)

            if response.status_code == 200:
                return response.json()
            else:
                return {'error': f'HTTP {response.status_code}'}
        except Exception as e:
            return {'error': str(e)}

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = DEFAULT_MODEL,
        temperature: float = 0.7,
        stream: bool = False
    ) -> Dict:
        """
        Chat with conversation history

        Args:
            messages: [{'role': 'user', 'content': '...'}, ...]
            model: Model to use
            temperature: Randomness (0-1)
            stream: Stream response

        Returns:
            {'message': {'role': 'assistant', 'content': '...'}}
        """
        url = f"{self.base_url}/api/chat"

        data = {
            'model': model,
            'messages': messages,
            'stream': stream,
            'options': {
                'temperature': temperature,
            }
        }

        try:
            response = requests.post(url, json=data)

            if response.status_code == 200:
                return response.json()
            else:
                return {'error': f'HTTP {response.status_code}'}
        except Exception as e:
            return {'error': str(e)}

    def embeddings(self, text: str, model: str = 'nomic-embed-text') -> Optional[List[float]]:
        """
        Generate embeddings for semantic search

        Args:
            text: Text to embed
            model: Embedding model

        Returns:
            List of floats (vector representation)
        """
        url = f"{self.base_url}/api/embeddings"

        data = {
            'model': model,
            'prompt': text
        }

        try:
            response = requests.post(url, json=data)

            if response.status_code == 200:
                return response.json().get('embedding')
            return None
        except:
            return None


# ==============================================================================
# VOICE-TO-BLOG PIPELINE (Local Version)
# ==============================================================================

def voice_to_blog_post(
    transcript: str,
    model: str = 'mistral:7b',
    temperature: float = 0.7
) -> Dict:
    """
    Convert voice transcript to structured blog post

    Args:
        transcript: Voice transcript text
        model: Ollama model to use
        temperature: Creative randomness

    Returns:
        {
            'title': str,
            'slug': str,
            'content': str,
            'category': str,
            'tags': List[str],
            'seo_keywords': List[str]
        }
    """

    client = OllamaClient()

    # Check if Ollama is running
    if not client.is_running():
        return {'error': 'Ollama not running. Start with: ollama serve'}

    # System prompt for blog post generation
    system_prompt = """You are a professional blog writer. Convert voice transcripts into well-structured blog posts.

Output format (JSON):
{
    "title": "Compelling Title",
    "slug": "url-friendly-slug",
    "content": "Full markdown blog post with headers, paragraphs, lists",
    "category": "Technology|Business|Lifestyle|etc",
    "tags": ["tag1", "tag2", "tag3"],
    "seo_keywords": ["keyword1", "keyword2", "keyword3"]
}

Make content engaging, scannable, and SEO-friendly."""

    prompt = f"""Convert this voice transcript into a blog post:

{transcript}

Output JSON only (no additional text):"""

    # Generate blog post
    result = client.generate(
        prompt=prompt,
        model=model,
        system=system_prompt,
        temperature=temperature
    )

    if 'error' in result:
        return result

    # Parse JSON response
    try:
        response_text = result.get('response', '')

        # Extract JSON (sometimes models add explanatory text)
        if '{' in response_text and '}' in response_text:
            json_start = response_text.index('{')
            json_end = response_text.rindex('}') + 1
            json_text = response_text[json_start:json_end]

            blog_post = json.loads(json_text)
            blog_post['model_used'] = model
            blog_post['generated_at'] = datetime.utcnow().isoformat()

            return blog_post
        else:
            return {'error': 'No JSON in response', 'raw_response': response_text}

    except json.JSONDecodeError as e:
        return {'error': f'JSON parse error: {str(e)}', 'raw_response': result.get('response')}


# ==============================================================================
# NEWS ARTICLE ANALYSIS (The "Roast" System)
# ==============================================================================

def analyze_news_article(
    article_url: str,
    article_text: str,
    perspective: str = 'critical',
    model: str = 'mistral:7b'
) -> Dict:
    """
    Analyze news article with critical perspective

    Args:
        article_url: URL of article
        article_text: Full article text
        perspective: 'critical', 'supportive', 'neutral', 'opposite'
        model: Ollama model

    Returns:
        {
            'analysis': str,
            'key_points': List[str],
            'bias_detected': str,
            'counterarguments': List[str],
            'hash': str (content hash for verification)
        }
    """

    client = OllamaClient()

    if not client.is_running():
        return {'error': 'Ollama not running'}

    # System prompts for different perspectives
    system_prompts = {
        'critical': """You are a critical analyst. Find logical flaws, biases, and unsupported claims.
Output JSON with: analysis, key_points, bias_detected, counterarguments.""",

        'supportive': """You are a supportive analyst. Find strengths, valid arguments, and good points.
Output JSON with: analysis, key_points, strengths, supporting_evidence.""",

        'neutral': """You are a neutral fact-checker. Verify claims, check sources, assess objectivity.
Output JSON with: analysis, key_points, verified_claims, questionable_claims.""",

        'opposite': """You are a contrarian analyst. Take the opposite position and argue it convincingly.
Output JSON with: analysis, key_points, opposite_perspective, alternative_interpretation."""
    }

    system = system_prompts.get(perspective, system_prompts['critical'])

    prompt = f"""Analyze this news article from a {perspective} perspective:

URL: {article_url}

Article:
{article_text[:4000]}  # Limit to 4000 chars for context window

Output JSON only:"""

    result = client.generate(
        prompt=prompt,
        model=model,
        system=system,
        temperature=0.7
    )

    if 'error' in result:
        return result

    try:
        response_text = result.get('response', '')

        # Extract JSON
        if '{' in response_text and '}' in response_text:
            json_start = response_text.index('{')
            json_end = response_text.rindex('}') + 1
            json_text = response_text[json_start:json_end]

            analysis = json.loads(json_text)

            # Add metadata
            import hashlib
            content_hash = hashlib.sha256(article_text.encode()).hexdigest()[:16]

            analysis['hash'] = content_hash
            analysis['article_url'] = article_url
            analysis['perspective'] = perspective
            analysis['model_used'] = model
            analysis['analyzed_at'] = datetime.utcnow().isoformat()

            return analysis
        else:
            return {'error': 'No JSON in response', 'raw_response': response_text}

    except json.JSONDecodeError as e:
        return {'error': f'JSON parse error: {str(e)}'}


# ==============================================================================
# CODE GENERATION
# ==============================================================================

def generate_code(
    description: str,
    language: str = 'python',
    model: str = 'codellama:7b'
) -> Dict:
    """
    Generate code from natural language description

    Args:
        description: What the code should do
        language: Programming language
        model: Ollama code model

    Returns:
        {'code': str, 'explanation': str}
    """

    client = OllamaClient()

    if not client.is_running():
        return {'error': 'Ollama not running'}

    system = f"""You are an expert {language} programmer. Generate clean, efficient, well-commented code.

Output format:
```{language}
# Code here
```

Then explain how it works."""

    prompt = f"""Write {language} code that does the following:

{description}

Include comments and a brief explanation."""

    result = client.generate(
        prompt=prompt,
        model=model,
        system=system,
        temperature=0.3  # Lower temperature for code
    )

    if 'error' in result:
        return result

    response_text = result.get('response', '')

    # Extract code block
    code = None
    if f'```{language}' in response_text:
        start = response_text.index(f'```{language}') + len(f'```{language}')
        end = response_text.index('```', start)
        code = response_text[start:end].strip()
    elif '```' in response_text:
        start = response_text.index('```') + 3
        end = response_text.index('```', start)
        code = response_text[start:end].strip()

    return {
        'code': code,
        'explanation': response_text,
        'language': language,
        'model_used': model
    }


# ==============================================================================
# SETUP HELPERS
# ==============================================================================

def check_ollama_status() -> Dict:
    """Check Ollama installation and status"""

    client = OllamaClient()

    status = {
        'running': False,
        'models_installed': [],
        'recommended_models': list(MODELS.values()),
        'setup_instructions': None
    }

    # Check if running
    if client.is_running():
        status['running'] = True
        status['models_installed'] = [m['name'] for m in client.list_models()]
    else:
        status['setup_instructions'] = """Ollama not running. Install:

1. Install Ollama:
   curl -fsSL https://ollama.com/install.sh | sh

2. Start Ollama:
   ollama serve

3. Pull a model:
   ollama pull llama3.2:3b

4. Test:
   ollama run llama3.2:3b "Hello!"
"""

    return status


def setup_recommended_models() -> Generator[Dict, None, None]:
    """Download recommended models"""

    client = OllamaClient()

    if not client.is_running():
        yield {'error': 'Ollama not running'}
        return

    for purpose, model_name in MODELS.items():
        yield {'status': 'downloading', 'model': model_name, 'purpose': purpose}

        for progress in client.pull_model(model_name):
            yield progress

        yield {'status': 'complete', 'model': model_name}


# ==============================================================================
# EXPORTS
# ==============================================================================

if __name__ == '__main__':
    print("Local Ollama Client - Privacy-Preserving AI")
    print()

    status = check_ollama_status()

    if status['running']:
        print("✅ Ollama is running")
        print(f"   Models installed: {len(status['models_installed'])}")

        for model in status['models_installed']:
            print(f"     - {model}")

        print()
        print("Recommended models:")
        for purpose, model in MODELS.items():
            installed = '✅' if model in status['models_installed'] else '❌'
            print(f"  {installed} {purpose}: {model}")
    else:
        print("❌ Ollama not running")
        print()
        print(status['setup_instructions'])

    print()
    print("Features:")
    print("  - Voice-to-blog conversion")
    print("  - News article analysis (multiple perspectives)")
    print("  - Code generation")
    print("  - Embeddings for semantic search")
    print("  - 100% local, 100% private")
