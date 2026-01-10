#!/usr/bin/env python3
"""
Ollama HTTP API Client for Flask

This module provides Ollama integration via HTTP API (like Node.js does)
instead of subprocess, allowing context passing (files, templates, etc.)
"""

import requests
import json
from typing import Dict, Optional, List, Any
from pathlib import Path

OLLAMA_BASE_URL = 'http://127.0.0.1:11434'

class OllamaClient:
    """Client for Ollama HTTP API"""

    def __init__(self, base_url: str = OLLAMA_BASE_URL):
        self.base_url = base_url

    def check_health(self) -> bool:
        """Check if Ollama is running"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def list_models(self) -> List[Dict[str, Any]]:
        """List available Ollama models"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get('models', [])
            return []
        except Exception:
            return []

    def generate(
        self,
        prompt: str,
        model: str = 'llama3.2',
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
        context_files: Optional[List[str]] = None,
        timeout: int = 60
    ) -> Dict[str, Any]:
        """
        Generate response from Ollama

        Args:
            prompt: User prompt
            model: Model name (llama3.2, mistral, phi3, etc.)
            system_prompt: System prompt for context
            temperature: Temperature (0.1 to 2.0)
            max_tokens: Max tokens to generate
            context_files: List of file paths to include as context
            timeout: Request timeout in seconds

        Returns:
            Dict with:
            - success: bool
            - response: str (generated text)
            - error: str (if failed)
            - model: str
            - tokens_generated: int
            - tokens_prompt: int
            - time_ms: int
        """

        # Build full prompt with context
        full_prompt = prompt

        # Add file context if provided
        if context_files:
            context_parts = []
            for file_path in context_files:
                try:
                    path = Path(file_path)
                    if path.exists():
                        content = path.read_text()
                        context_parts.append(f"\n--- File: {file_path} ---\n{content}\n")
                except Exception as e:
                    context_parts.append(f"\n--- Error reading {file_path}: {e} ---\n")

            if context_parts:
                full_prompt = "".join(context_parts) + "\n\nUser question:\n" + prompt

        # Build system prompt
        if not system_prompt:
            system_prompt = "You are a helpful AI assistant. You can see file contents provided as context."

        # Build final prompt
        final_prompt = f"{system_prompt}\n\nUser: {full_prompt}\n\nAssistant:"

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": final_prompt,
                    "stream": False,
                    "options": {
                        "temperature": max(0.1, min(2.0, temperature)),
                        "num_predict": max_tokens,
                        "top_p": 0.9,
                        "top_k": 40
                    }
                },
                timeout=timeout
            )

            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f"Ollama API error: {response.status_code} - {response.text}",
                    'response': ''
                }

            data = response.json()

            return {
                'success': True,
                'response': data.get('response', '').strip(),
                'model': model,
                'tokens_generated': data.get('eval_count', 0),
                'tokens_prompt': data.get('prompt_eval_count', 0),
                'time_ms': int(data.get('total_duration', 0) / 1_000_000) if data.get('total_duration') else 0,
                'error': None
            }

        except requests.Timeout:
            return {
                'success': False,
                'error': f'Ollama timeout after {timeout}s. Try a smaller model or simpler question.',
                'response': ''
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Ollama error: {str(e)}',
                'response': ''
            }

    def generate_with_template_context(
        self,
        prompt: str,
        template_content: str,
        variables: Dict[str, Any],
        model: str = 'llama3.2',
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate with template and variables as context

        Useful for:
        - "Help me improve this template"
        - "What variables can I add?"
        - "Generate content for this template"
        """

        context = f"""
--- Template Content ---
{template_content}

--- Current Variables ---
{json.dumps(variables, indent=2)}
"""

        full_prompt = context + "\n\n" + prompt

        system_prompt = """You are a template and branding expert. You can see the template code and variables.
Help users improve their templates, suggest variables, generate content, and create brand assets."""

        return self.generate(
            prompt=full_prompt,
            model=model,
            system_prompt=system_prompt,
            **kwargs
        )


# Convenience function
def generate_ollama_response(
    prompt: str,
    model: str = 'llama3.2',
    context_files: Optional[List[str]] = None,
    **kwargs
) -> Dict[str, Any]:
    """Generate response from Ollama (convenience wrapper)"""
    client = OllamaClient()
    return client.generate(prompt, model=model, context_files=context_files, **kwargs)


if __name__ == '__main__':
    # Test
    client = OllamaClient()

    print("Testing Ollama HTTP API client...")
    print(f"Ollama running: {client.check_health()}")

    print("\nAvailable models:")
    models = client.list_models()
    for model in models:
        print(f"  - {model.get('name')}")

    print("\nTest generation:")
    result = client.generate("Say hello in 5 words", model='llama3.2', max_tokens=50)
    if result['success']:
        print(f"✅ Response: {result['response']}")
        print(f"   Tokens: {result['tokens_generated']}, Time: {result['time_ms']}ms")
    else:
        print(f"❌ Error: {result['error']}")
