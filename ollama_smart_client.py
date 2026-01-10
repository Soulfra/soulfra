"""
Ollama Smart Client - Auto-Fallback Endpoint Detection

Fixes hardcoded IP issues in cal_auto_publish.py and ollama_soul.py.
Automatically tries multiple endpoints with graceful fallback to mock mode.

Usage:
    from ollama_smart_client import ask_ollama, get_ollama_status

    # Simple query
    response = ask_ollama("Explain this bug", model="llama3.2:latest")

    # With soul personality
    response = ask_ollama("Debug QR auth", use_soul=True)

    # Check status
    status = get_ollama_status()
    print(f"Ollama: {status['mode']} - {status['message']}")

Endpoints tried in order:
1. http://localhost:11434 (local Ollama)
2. http://192.168.1.87:11434 (Cal's machine)
3. Mock mode (intelligent fallback responses)
"""

import requests
import json
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ollama endpoints to try (in order of preference)
OLLAMA_ENDPOINTS = [
    'http://localhost:11434',      # Local Ollama
    'http://192.168.1.87:11434',   # Cal's machine
]

# Global cache for active endpoint
_active_endpoint = None
_endpoint_check_time = None
_endpoint_check_interval = 300  # Re-check every 5 minutes


def test_ollama_connection(endpoint, timeout=3):
    """
    Test if Ollama is reachable at the given endpoint.

    Args:
        endpoint: Base URL (e.g., 'http://localhost:11434')
        timeout: Connection timeout in seconds

    Returns:
        bool: True if Ollama is reachable and responding
    """
    try:
        response = requests.get(f"{endpoint}/api/tags", timeout=timeout)
        if response.status_code == 200:
            models = response.json().get('models', [])
            logger.info(f"✅ Ollama reachable at {endpoint} ({len(models)} models)")
            return True
        else:
            logger.debug(f"⚠️  Ollama at {endpoint} returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        logger.debug(f"❌ Connection refused: {endpoint}")
        return False
    except requests.exceptions.Timeout:
        logger.debug(f"⏱️  Timeout connecting to {endpoint}")
        return False
    except Exception as e:
        logger.debug(f"❌ Error testing {endpoint}: {e}")
        return False


def get_ollama_endpoint(force_refresh=False):
    """
    Get the active Ollama endpoint, with caching and automatic fallback.

    Args:
        force_refresh: Force re-check even if cached endpoint exists

    Returns:
        str or None: Active endpoint URL, or None if using mock mode
    """
    global _active_endpoint, _endpoint_check_time

    # Use cached endpoint if valid
    if not force_refresh and _active_endpoint and _endpoint_check_time:
        elapsed = (datetime.utcnow() - _endpoint_check_time).total_seconds()
        if elapsed < _endpoint_check_interval:
            return _active_endpoint

    # Try each endpoint
    logger.info("🔍 Searching for available Ollama endpoint...")
    for endpoint in OLLAMA_ENDPOINTS:
        if test_ollama_connection(endpoint):
            _active_endpoint = endpoint
            _endpoint_check_time = datetime.utcnow()
            logger.info(f"✅ Using Ollama endpoint: {endpoint}")
            return endpoint

    # No endpoints available - use mock mode
    logger.warning("⚠️  No Ollama endpoints available - using mock mode")
    _active_endpoint = None
    _endpoint_check_time = datetime.utcnow()
    return None


def load_soul_document():
    """
    Load soul document for personality injection.

    Returns:
        str: Soul document content, or empty string if not found
    """
    soul_paths = [
        Path('soul.md'),
        Path('docs/soul.md'),
        Path('../soul.md')
    ]

    for path in soul_paths:
        if path.exists():
            logger.debug(f"Loading soul document: {path}")
            return path.read_text()

    logger.debug("Soul document not found")
    return ""


def generate_mock_response(prompt, model):
    """
    Generate intelligent mock response when Ollama is unavailable.

    Args:
        prompt: User prompt
        model: Model name (ignored in mock mode)

    Returns:
        str: Mock response
    """
    logger.info("🤖 Generating mock response (Ollama unavailable)")

    # Simple keyword-based mock responses
    prompt_lower = prompt.lower()

    if 'error' in prompt_lower or 'bug' in prompt_lower or 'fix' in prompt_lower:
        return """I noticed the issue you're describing. Based on the context, here are the likely causes:

1. **Configuration mismatch** - Check environment variables and API endpoints
2. **Timing issue** - Race condition in async operations
3. **Data validation** - Input format may not match expected schema

I'd recommend adding debug logging to trace the exact failure point, then implementing proper error handling with fallback mechanisms.

*[Note: This is a mock response - Ollama is currently unavailable. For detailed analysis, please ensure Ollama is running.]*
"""

    elif 'qr' in prompt_lower and ('auth' in prompt_lower or 'login' in prompt_lower):
        return """QR code authentication analysis:

The QR auth system uses HMAC-SHA256 signatures with base64 encoding. Common failure points:

1. **Token Expiration** - Default TTL is 1 hour, check if tokens are being validated after expiry
2. **Signature Mismatch** - Ensure SECRET_KEY is consistent across all services
3. **One-Time Use** - Tokens marked as one-time can't be reused, verify database state
4. **JSON Parsing** - Base64 decode → JSON parse chain may fail on malformed input

Recommended fix: Add comprehensive error logging at each validation step to identify exact failure point.

*[Note: This is a mock response - Ollama is currently unavailable.]*
"""

    elif 'blog' in prompt_lower or 'post' in prompt_lower or 'publish' in prompt_lower:
        return f"""# Blog Post Draft

Based on your input, here's a structured blog post:

## Overview
{prompt[:200]}...

## Key Points

1. **Context** - Understanding the problem space
2. **Analysis** - Breaking down the core issues
3. **Solution** - Practical implementation steps
4. **Results** - Expected outcomes and benefits

## Conclusion

This approach provides a systematic way to address the challenge while maintaining flexibility for future iterations.

*[Note: This is a mock blog post - Ollama is currently unavailable. For AI-powered content generation, ensure Ollama is running.]*
"""

    else:
        return f"""I've analyzed your request about: "{prompt[:100]}..."

Here's a structured approach:

1. **Identify Core Issue** - {prompt[:50]}
2. **Root Cause Analysis** - Check logs, verify configuration
3. **Proposed Solution** - Implement proper error handling and validation
4. **Testing Strategy** - Unit tests + integration tests

*[Note: This is a mock response generated because Ollama is currently unavailable. For detailed AI-powered analysis, please ensure Ollama is running on localhost:11434 or 192.168.1.87:11434]*
"""


def ask_ollama(prompt, model='llama3.2:latest', use_soul=True, system_prompt=None, timeout=120):
    """
    Ask Ollama with automatic endpoint detection and fallback.

    Args:
        prompt: User prompt
        model: Ollama model name
        use_soul: Inject soul document personality
        system_prompt: Override system prompt (takes precedence over soul)
        timeout: Request timeout in seconds

    Returns:
        str: Model response (or mock response if Ollama unavailable)
    """
    # Get active endpoint
    endpoint = get_ollama_endpoint()

    # Mock mode fallback
    if endpoint is None:
        return generate_mock_response(prompt, model)

    # Build system prompt
    if system_prompt is None and use_soul:
        soul_doc = load_soul_document()
        if soul_doc:
            system_prompt = f"""You are Soulfra. Follow these principles:

{soul_doc}

User question: {prompt}"""
        else:
            system_prompt = prompt
    elif system_prompt is None:
        system_prompt = prompt

    # Make request to Ollama
    try:
        logger.info(f"🤖 Asking Ollama ({model}) at {endpoint}")

        response = requests.post(
            f"{endpoint}/api/generate",
            json={
                'model': model,
                'prompt': system_prompt,
                'stream': False
            },
            timeout=timeout
        )

        if response.status_code == 200:
            result = response.json()
            answer = result.get('response', '').strip()
            logger.info(f"✅ Ollama responded ({len(answer)} chars)")
            return answer
        else:
            logger.error(f"❌ Ollama error: {response.status_code} - {response.text}")
            # Force endpoint refresh and try mock mode
            get_ollama_endpoint(force_refresh=True)
            return generate_mock_response(prompt, model)

    except requests.exceptions.Timeout:
        logger.error(f"⏱️  Ollama timeout after {timeout}s")
        # Force endpoint refresh and try mock mode
        get_ollama_endpoint(force_refresh=True)
        return generate_mock_response(prompt, model)

    except requests.exceptions.ConnectionError:
        logger.error(f"❌ Connection error to {endpoint}")
        # Force endpoint refresh and try mock mode
        get_ollama_endpoint(force_refresh=True)
        return generate_mock_response(prompt, model)

    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return generate_mock_response(prompt, model)


def ask_ollama_streaming(prompt, model='llama3.2:latest', use_soul=True, system_prompt=None):
    """
    Ask Ollama with streaming response.

    Args:
        prompt: User prompt
        model: Ollama model name
        use_soul: Inject soul document personality
        system_prompt: Override system prompt

    Yields:
        str: Response chunks
    """
    endpoint = get_ollama_endpoint()

    if endpoint is None:
        # Mock streaming
        mock_response = generate_mock_response(prompt, model)
        for chunk in mock_response.split('\n'):
            yield chunk + '\n'
        return

    # Build system prompt
    if system_prompt is None and use_soul:
        soul_doc = load_soul_document()
        if soul_doc:
            system_prompt = f"""You are Soulfra. Follow these principles:

{soul_doc}

User question: {prompt}"""
        else:
            system_prompt = prompt
    elif system_prompt is None:
        system_prompt = prompt

    try:
        response = requests.post(
            f"{endpoint}/api/generate",
            json={
                'model': model,
                'prompt': system_prompt,
                'stream': True
            },
            stream=True,
            timeout=120
        )

        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    if 'response' in chunk:
                        yield chunk['response']
        else:
            logger.error(f"❌ Streaming error: {response.status_code}")
            yield generate_mock_response(prompt, model)

    except Exception as e:
        logger.error(f"❌ Streaming exception: {e}")
        yield generate_mock_response(prompt, model)


def get_ollama_status():
    """
    Get current Ollama status and available models.

    Returns:
        dict: Status info with endpoint, models, availability
    """
    endpoint = get_ollama_endpoint()

    if endpoint is None:
        return {
            'available': False,
            'endpoint': None,
            'mode': 'mock',
            'models': [],
            'message': 'Ollama unavailable - using mock responses'
        }

    try:
        response = requests.get(f"{endpoint}/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = [m['name'] for m in data.get('models', [])]
            return {
                'available': True,
                'endpoint': endpoint,
                'mode': 'ollama',
                'models': models,
                'message': f'Ollama running with {len(models)} models'
            }
    except Exception as e:
        logger.error(f"Error getting status: {e}")

    return {
        'available': False,
        'endpoint': endpoint,
        'mode': 'error',
        'models': [],
        'message': f'Ollama connection error at {endpoint}'
    }


if __name__ == '__main__':
    # Test the smart client
    print("=" * 60)
    print("Ollama Smart Client - Connection Test")
    print("=" * 60)

    status = get_ollama_status()
    print(f"\nStatus: {status['message']}")
    print(f"Endpoint: {status['endpoint']}")
    print(f"Mode: {status['mode']}")
    print(f"Models: {', '.join(status['models']) if status['models'] else 'None'}")

    print("\n" + "=" * 60)
    print("Test Query")
    print("=" * 60)

    test_prompt = "What is the purpose of a QR code authentication system?"
    print(f"\nPrompt: {test_prompt}\n")

    response = ask_ollama(test_prompt, use_soul=False)
    print(f"Response:\n{response}")
