#!/usr/bin/env python3
"""
LLM Router - Pure Python + stdlib
Routes requests to multiple LLM models with automatic fallback

No requirements.txt, no external libraries, just Python + urllib.
Tries models in order until one responds successfully.

Usage:
    from llm_router import LLMRouter

    router = LLMRouter()
    result = router.call("Explain butter in 10 words")

    if result['success']:
        print(f"Model: {result['model_used']}")
        print(f"Response: {result['response']}")
"""

import json
import urllib.request
import urllib.error
from typing import Dict, Optional, List


class LLMRouter:
    """
    Simple LLM router with automatic fallback

    Tries multiple models until one responds successfully.
    Pure Python + stdlib - no external dependencies.
    """

    def __init__(self, models: List[str] = None, ollama_url: str = 'http://localhost:11434'):
        """
        Initialize LLM router

        Args:
            models: List of model names to try (default: llama2, llama3.2, mistral)
            ollama_url: Ollama API URL (default: http://localhost:11434)
        """
        self.models = models or ['llama2', 'llama3.2:latest', 'mistral:latest']
        self.ollama_url = ollama_url.rstrip('/')

    def call(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        timeout: int = 30
    ) -> Dict:
        """
        Call LLM with automatic fallback to other models

        Args:
            prompt: User question/prompt
            system_prompt: System instructions (optional)
            model: Specific model to use (optional, tries all models if None)
            temperature: Sampling temperature 0.0-1.0 (default: 0.7)
            timeout: Request timeout in seconds (default: 30)

        Returns:
            Success: {'success': True, 'response': '...', 'model_used': 'llama2', 'duration_ms': 1234}
            Failure: {'success': False, 'error': '...', 'tried_models': [...]}
        """
        models_to_try = [model] if model else self.models
        errors = []

        for model_name in models_to_try:
            try:
                result = self._call_single_model(
                    model=model_name,
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    timeout=timeout
                )

                # Success! Return immediately
                return {
                    'success': True,
                    'response': result['response'],
                    'model_used': model_name,
                    'duration_ms': result.get('total_duration', 0) // 1_000_000,  # ns → ms
                    'eval_count': result.get('eval_count', 0)
                }

            except urllib.error.HTTPError as e:
                if e.code == 404:
                    # Model not found, try next
                    errors.append(f'{model_name}: Not found (404)')
                    continue
                else:
                    errors.append(f'{model_name}: HTTP {e.code}')
                    continue

            except urllib.error.URLError as e:
                # Ollama not running or network error
                return {
                    'success': False,
                    'error': f'Ollama not running or network error: {e.reason}',
                    'tried_models': models_to_try,
                    'hint': 'Start Ollama with: ollama serve'
                }

            except Exception as e:
                # Unexpected error, try next model
                errors.append(f'{model_name}: {type(e).__name__}: {str(e)}')
                continue

        # All models failed
        return {
            'success': False,
            'error': f'All {len(models_to_try)} models failed',
            'tried_models': models_to_try,
            'errors': errors,
            'hint': f'Install models with: ollama pull {models_to_try[0]}'
        }

    def _call_single_model(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        timeout: int = 30
    ) -> Dict:
        """
        Call a single Ollama model (internal method)

        Raises:
            urllib.error.HTTPError: If model not found or other HTTP error
            urllib.error.URLError: If Ollama not running
            Exception: For other errors

        Returns:
            Raw Ollama API response dict
        """
        # Build request payload
        payload = {
            'model': model,
            'prompt': prompt,
            'stream': False,
            'options': {'temperature': temperature}
        }

        if system_prompt:
            payload['system'] = system_prompt

        # Make HTTP request (pure urllib, no requests library)
        req = urllib.request.Request(
            f'{self.ollama_url}/api/generate',
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )

        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode('utf-8'))

    def list_available_models(self) -> List[str]:
        """
        Get list of actually installed Ollama models

        Returns:
            List of model names (e.g., ['llama2', 'llama3.2:latest'])
            Empty list if Ollama not running
        """
        try:
            req = urllib.request.Request(f'{self.ollama_url}/api/tags')
            with urllib.request.urlopen(req, timeout=2) as response:
                result = json.loads(response.read().decode('utf-8'))
                return [m['name'] for m in result.get('models', [])]
        except:
            return []

    def is_ollama_running(self) -> bool:
        """Check if Ollama is running and accessible"""
        try:
            req = urllib.request.Request(f'{self.ollama_url}/api/tags')
            with urllib.request.urlopen(req, timeout=2) as response:
                return response.status == 200
        except:
            return False


# Example usage
if __name__ == '__main__':
    router = LLMRouter()

    print("Available models:", router.list_available_models())
    print()

    # Try to call LLM (will fallback if primary model unavailable)
    result = router.call(
        prompt="Explain how salted butter is made in exactly 10 words.",
        system_prompt="You are a helpful AI assistant. Be concise."
    )

    if result['success']:
        print(f"✅ Success!")
        print(f"   Model: {result['model_used']}")
        print(f"   Duration: {result['duration_ms']}ms")
        print(f"   Response: {result['response']}")
    else:
        print(f"❌ Error: {result['error']}")
        print(f"   Tried: {result.get('tried_models', [])}")
        if 'errors' in result:
            for err in result['errors']:
                print(f"     - {err}")
