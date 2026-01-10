#!/usr/bin/env python3
"""
Fetch - Pure Python Stdlib HTTP Client (Zero Dependencies)

Wrapper around urllib.request for clean, simple HTTP operations.
Replaces requests library with from-scratch stdlib-only implementation.

Philosophy: urllib.request is all you need. No external dependencies.

Usage:
    from lib.fetch import fetch, post

    # GET request
    data = fetch('https://api.example.com/data')

    # POST request
    result = post('https://api.example.com/submit', {'key': 'value'})

Tier System Teaching:
TIER 1: URL string → bytes
TIER 2: Bytes → HTTP request
TIER 3: HTTP response → JSON/text
TIER 4: Data → application logic
"""

import urllib.request
import urllib.error
import urllib.parse
import json
from typing import Dict, Optional, Union


def fetch(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 30
) -> Dict:
    """
    GET request

    Args:
        url: URL to fetch
        headers: Optional HTTP headers
        timeout: Request timeout in seconds

    Returns:
        dict with:
            - success: bool
            - data: response body (parsed JSON or text)
            - status_code: HTTP status code
            - error: error message if failed

    Example:
        >>> result = fetch('https://api.github.com/users/octocat')
        >>> if result['success']:
        >>>     print(result['data']['name'])
    """
    headers = headers or {}

    try:
        req = urllib.request.Request(url, headers=headers)

        with urllib.request.urlopen(req, timeout=timeout) as response:
            status_code = response.getcode()
            body = response.read().decode('utf-8')

            # Try to parse as JSON
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                # Return as text if not JSON
                data = body

            return {
                'success': True,
                'data': data,
                'status_code': status_code,
                'error': None
            }

    except urllib.error.HTTPError as e:
        return {
            'success': False,
            'data': None,
            'status_code': e.code,
            'error': f'HTTP {e.code}: {e.reason}'
        }
    except urllib.error.URLError as e:
        return {
            'success': False,
            'data': None,
            'status_code': None,
            'error': f'Connection error: {e.reason}'
        }
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'status_code': None,
            'error': str(e)
        }


def post(
    url: str,
    data: Union[Dict, str],
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 30
) -> Dict:
    """
    POST request

    Args:
        url: URL to post to
        data: Data to send (dict will be JSON-encoded)
        headers: Optional HTTP headers
        timeout: Request timeout in seconds

    Returns:
        dict with same structure as fetch()

    Example:
        >>> result = post('https://api.example.com/login', {
        >>>     'username': 'alice',
        >>>     'password': 'secret'
        >>> })
    """
    headers = headers or {}

    # Encode data
    if isinstance(data, dict):
        data_bytes = json.dumps(data).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    else:
        data_bytes = data.encode('utf-8')

    try:
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers=headers,
            method='POST'
        )

        with urllib.request.urlopen(req, timeout=timeout) as response:
            status_code = response.getcode()
            body = response.read().decode('utf-8')

            # Try to parse as JSON
            try:
                response_data = json.loads(body)
            except json.JSONDecodeError:
                response_data = body

            return {
                'success': True,
                'data': response_data,
                'status_code': status_code,
                'error': None
            }

    except urllib.error.HTTPError as e:
        return {
            'success': False,
            'data': None,
            'status_code': e.code,
            'error': f'HTTP {e.code}: {e.reason}'
        }
    except urllib.error.URLError as e:
        return {
            'success': False,
            'data': None,
            'status_code': None,
            'error': f'Connection error: {e.reason}'
        }
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'status_code': None,
            'error': str(e)
        }


def put(
    url: str,
    data: Union[Dict, str],
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 30
) -> Dict:
    """PUT request (same as post but with PUT method)"""
    headers = headers or {}

    if isinstance(data, dict):
        data_bytes = json.dumps(data).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    else:
        data_bytes = data.encode('utf-8')

    try:
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers=headers,
            method='PUT'
        )

        with urllib.request.urlopen(req, timeout=timeout) as response:
            status_code = response.getcode()
            body = response.read().decode('utf-8')

            try:
                response_data = json.loads(body)
            except json.JSONDecodeError:
                response_data = body

            return {
                'success': True,
                'data': response_data,
                'status_code': status_code,
                'error': None
            }

    except urllib.error.HTTPError as e:
        return {
            'success': False,
            'data': None,
            'status_code': e.code,
            'error': f'HTTP {e.code}: {e.reason}'
        }
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'status_code': None,
            'error': str(e)
        }


def delete(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 30
) -> Dict:
    """DELETE request"""
    headers = headers or {}

    try:
        req = urllib.request.Request(
            url,
            headers=headers,
            method='DELETE'
        )

        with urllib.request.urlopen(req, timeout=timeout) as response:
            status_code = response.getcode()
            body = response.read().decode('utf-8')

            try:
                response_data = json.loads(body)
            except json.JSONDecodeError:
                response_data = body

            return {
                'success': True,
                'data': response_data,
                'status_code': status_code,
                'error': None
            }

    except urllib.error.HTTPError as e:
        return {
            'success': False,
            'data': None,
            'status_code': e.code,
            'error': f'HTTP {e.code}: {e.reason}'
        }
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'status_code': None,
            'error': str(e)
        }


# ==============================================================================
# TESTING
# ==============================================================================

if __name__ == '__main__':
    print("🧪 Testing Fetch (Stdlib HTTP Client)\n")

    # Test 1: GET request
    print("Test 1: GET https://httpbin.org/get")
    result = fetch('https://httpbin.org/get?test=value')
    print(f"  Success: {result['success']}")
    print(f"  Status: {result['status_code']}")
    if result['success']:
        print(f"  URL called: {result['data']['url']}")
    print()

    # Test 2: POST request
    print("Test 2: POST https://httpbin.org/post")
    result = post('https://httpbin.org/post', {'key': 'value', 'tier': 1})
    print(f"  Success: {result['success']}")
    print(f"  Status: {result['status_code']}")
    if result['success']:
        print(f"  Data echoed: {result['data']['json']}")
    print()

    # Test 3: Error handling
    print("Test 3: 404 Error")
    result = fetch('https://httpbin.org/status/404')
    print(f"  Success: {result['success']}")
    print(f"  Status: {result['status_code']}")
    print(f"  Error: {result['error']}")
    print()

    print("✅ Fetch tests complete!")
