# 🔐 API Gateway - Technical Implementation

**How to enforce API key usage in open source code**

This document shows the technical implementation of API key gates in an open source project.

---

## 🎯 The Architecture

```
Static Site (GitHub Pages)          Central API (Your Server)
soulfra.com                          api.soulfra.com
    |                                      |
    | JavaScript fetch()                  | Validate API key
    |                                      | Check rate limits
    |------------------------------------>| Execute request
    |                                      | Track usage
    |<------------------------------------|
    | Response (or 401 Unauthorized)      |
```

---

## 📝 Client-Side Code (Open Source)

### File: `templates/template_browser.html`

**AI Generation Button** (already exists):
```javascript
async function generateWithOllama() {
    const prompt = document.getElementById('ollamaPrompt').value;
    const model = document.getElementById('ollamaModel').value;
    const apiKey = getApiKey(); // Get from localStorage

    if (!apiKey) {
        alert('API key required! Click "Get Free API Key" to continue.');
        window.location.href = '/auth/github'; // GitHub OAuth
        return;
    }

    try {
        const response = await fetch('https://api.soulfra.com/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${apiKey}`  // ← API key here!
            },
            body: JSON.stringify({
                prompt: prompt,
                model: model,
                context: getTemplateContext()
            })
        });

        if (response.status === 401) {
            alert('Invalid API key. Please reconnect GitHub.');
            window.location.href = '/auth/github';
            return;
        }

        if (response.status === 429) {
            alert('Rate limit exceeded. Upgrade to Pro for unlimited access.');
            window.location.href = '/pricing';
            return;
        }

        const result = await response.json();
        displayGeneratedContent(result.content);

    } catch (error) {
        console.error('Generation failed:', error);
        alert('Failed to generate content. Check your API key.');
    }
}

function getApiKey() {
    // Get API key from localStorage (set after GitHub OAuth)
    return localStorage.getItem('soulfra_api_key');
}

function getTemplateContext() {
    // Get current template and variables for better generation
    return {
        template: currentTemplate.content,
        variables: JSON.parse(document.getElementById('variablesEditor').value)
    };
}
```

**Key points**:
- ✅ Hardcoded API endpoint: `api.soulfra.com` (can't change without forking)
- ✅ API key required in Authorization header
- ✅ Handles 401 (invalid key) → Redirect to OAuth
- ✅ Handles 429 (rate limit) → Redirect to upgrade

---

## 🔐 Server-Side Code (Your Proprietary API)

### File: `api_server.py` (NOT in open source repo)

**API Gateway Middleware**:
```python
from flask import Flask, request, jsonify
from database import get_db
import time

app = Flask(__name__)

def validate_api_key(api_key):
    """
    Validate API key and return user info + tier

    Returns:
        dict: {
            'valid': bool,
            'user_id': int,
            'tier': str,
            'quota': dict
        }
    """
    db = get_db()

    # Check if API key exists
    key_record = db.execute('''
        SELECT
            ak.id as api_key_id,
            ak.status,
            l.id as license_id,
            l.tier,
            l.email,
            l.expires_at
        FROM api_keys ak
        JOIN licenses l ON ak.license_id = l.id
        WHERE ak.api_key = ? AND ak.status = 'active'
    ''', (api_key,)).fetchone()

    if not key_record:
        return {'valid': False, 'error': 'Invalid API key'}

    # Check if license expired
    if key_record['expires_at']:
        expiry = datetime.fromisoformat(key_record['expires_at'])
        if expiry < datetime.now():
            return {'valid': False, 'error': 'License expired'}

    # Get tier quotas
    quotas = get_tier_quotas(key_record['tier'])

    return {
        'valid': True,
        'api_key_id': key_record['api_key_id'],
        'license_id': key_record['license_id'],
        'tier': key_record['tier'],
        'email': key_record['email'],
        'quota': quotas
    }


def check_rate_limit(api_key_id, endpoint, quota):
    """
    Check if user has exceeded rate limits

    Args:
        api_key_id: API key ID
        endpoint: API endpoint (e.g., '/generate')
        quota: User's quota limits

    Returns:
        dict: {
            'allowed': bool,
            'remaining': int,
            'reset_at': timestamp
        }
    """
    db = get_db()

    # Check daily API call limit
    today_start = datetime.now().replace(hour=0, minute=0, second=0)

    usage_count = db.execute('''
        SELECT COUNT(*) as count
        FROM api_usage
        WHERE api_key_id = ?
        AND endpoint = ?
        AND timestamp >= ?
    ''', (api_key_id, endpoint, today_start)).fetchone()['count']

    max_calls = quota.get('api_calls_per_day', 100)

    if max_calls == -1:  # Unlimited
        return {'allowed': True, 'remaining': -1}

    if usage_count >= max_calls:
        tomorrow = (today_start + timedelta(days=1)).timestamp()
        return {
            'allowed': False,
            'remaining': 0,
            'reset_at': tomorrow,
            'error': f'Rate limit exceeded. Limit: {max_calls}/day'
        }

    return {
        'allowed': True,
        'remaining': max_calls - usage_count
    }


def log_api_usage(api_key_id, endpoint, request_data, response_code):
    """Log API usage for billing and analytics"""
    db = get_db()

    db.execute('''
        INSERT INTO api_usage (api_key_id, endpoint, request_data, response_code)
        VALUES (?, ?, ?, ?)
    ''', (api_key_id, endpoint, json.dumps(request_data), response_code))

    db.commit()


def get_tier_quotas(tier):
    """Get quota limits for a tier"""
    QUOTAS = {
        'free': {
            'posts_per_month': 100,
            'brands': 1,
            'api_calls_per_day': 100,
        },
        'pro': {
            'posts_per_month': -1,  # unlimited
            'brands': 10,
            'api_calls_per_day': 50000,
        },
        'enterprise': {
            'posts_per_month': -1,
            'brands': -1,
            'api_calls_per_day': -1,
        }
    }
    return QUOTAS.get(tier, QUOTAS['free'])


# API Gateway Decorator
def require_api_key(f):
    """
    Decorator to protect API endpoints

    Usage:
        @app.route('/generate', methods=['POST'])
        @require_api_key
        def generate_content():
            # request.user_info has validated user data
            ...
    """
    def wrapper(*args, **kwargs):
        # Extract API key from Authorization header
        auth_header = request.headers.get('Authorization')

        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                'error': 'Missing API key',
                'message': 'Add header: Authorization: Bearer YOUR_API_KEY'
            }), 401

        api_key = auth_header.replace('Bearer ', '')

        # Validate API key
        validation = validate_api_key(api_key)

        if not validation['valid']:
            return jsonify({
                'error': 'Invalid API key',
                'message': validation.get('error', 'Unknown error')
            }), 401

        # Check rate limits
        rate_check = check_rate_limit(
            validation['api_key_id'],
            request.path,
            validation['quota']
        )

        if not rate_check['allowed']:
            return jsonify({
                'error': 'Rate limit exceeded',
                'message': rate_check.get('error'),
                'reset_at': rate_check.get('reset_at')
            }), 429

        # Attach user info to request
        request.user_info = validation
        request.rate_limit = rate_check

        # Execute the actual endpoint
        response = f(*args, **kwargs)

        # Log usage
        log_api_usage(
            validation['api_key_id'],
            request.path,
            request.get_json(),
            200  # Assuming success
        )

        return response

    wrapper.__name__ = f.__name__
    return wrapper
```

---

## 🤖 Protected API Endpoints

### Generate Content Endpoint
```python
@app.route('/api/generate', methods=['POST'])
@require_api_key  # ← Enforces API key!
def generate_content():
    """
    Generate content with Ollama (protected endpoint)

    Request:
        {
            "prompt": "Write a blog post about...",
            "model": "llama3.2",
            "context": {...}
        }

    Response:
        {
            "content": "Generated content...",
            "usage": {
                "remaining_calls": 95,
                "tier": "free"
            }
        }
    """
    data = request.get_json()
    user_info = request.user_info  # From @require_api_key decorator

    # Call Ollama (on YOUR server)
    from ollama_client import OllamaClient

    client = OllamaClient(host='http://localhost:11434')
    result = client.generate(
        prompt=data['prompt'],
        model=data.get('model', 'llama3.2')
    )

    return jsonify({
        'content': result['response'],
        'usage': {
            'remaining_calls': request.rate_limit['remaining'],
            'tier': user_info['tier']
        }
    })


@app.route('/api/ollama/<path:endpoint>', methods=['POST'])
@require_api_key
def proxy_ollama(endpoint):
    """
    Proxy all Ollama requests through YOUR server

    Examples:
        POST /api/ollama/generate
        POST /api/ollama/chat
        POST /api/ollama/embeddings
    """
    user_info = request.user_info

    # Forward request to YOUR Ollama instance
    import requests

    ollama_url = f'http://localhost:11434/api/{endpoint}'

    response = requests.post(
        ollama_url,
        json=request.get_json(),
        stream=True  # For streaming responses
    )

    return response.content, response.status_code
```

---

## 🔑 GitHub OAuth for Free Tier

### Get Free API Key Flow
```python
@app.route('/auth/github')
def github_auth():
    """Start GitHub OAuth flow"""
    from github_faucet import GitHubFaucet

    faucet = GitHubFaucet()
    auth_url = faucet.get_auth_url()

    return redirect(auth_url)


@app.route('/auth/github/callback')
def github_callback():
    """
    GitHub OAuth callback

    Flow:
        1. GitHub sends code
        2. Exchange code for access token
        3. Fetch GitHub profile
        4. Calculate tier based on activity
        5. Generate API key
        6. Redirect to app with API key
    """
    code = request.args.get('code')

    from github_faucet import GitHubFaucet

    faucet = GitHubFaucet()
    result = faucet.process_callback(code)

    if result['success']:
        api_key = result['api_key']
        tier = result['tier']

        # Return API key to user (they'll store in localStorage)
        return render_template('api_key_success.html',
            api_key=api_key,
            tier=tier,
            quota=get_tier_quotas(tier)
        )
    else:
        return jsonify({'error': result['error']}), 400
```

**Template: `api_key_success.html`**:
```html
<!DOCTYPE html>
<html>
<head>
    <title>API Key Generated</title>
</head>
<body>
    <h1>✅ API Key Generated!</h1>
    <p>Your tier: <strong>{{ tier }}</strong></p>
    <p>Quota: {{ quota.api_calls_per_day }} calls/day</p>

    <h2>Your API Key:</h2>
    <code id="apiKey">{{ api_key }}</code>

    <button onclick="saveAndRedirect()">Save & Continue</button>

    <script>
        function saveAndRedirect() {
            // Save API key to localStorage
            localStorage.setItem('soulfra_api_key', '{{ api_key }}');

            // Redirect back to template browser
            window.location.href = '/templates/browse';
        }
    </script>
</body>
</html>
```

---

## 💳 Stripe Integration for Paid Tier

### Checkout Flow
```python
@app.route('/api/checkout', methods=['POST'])
@require_api_key
def create_checkout():
    """
    Create Stripe checkout session for Pro upgrade

    Request:
        {
            "tier": "pro",  # or "enterprise"
            "success_url": "https://soulfra.com/success",
            "cancel_url": "https://soulfra.com/cancel"
        }
    """
    import stripe

    stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

    user_info = request.user_info
    data = request.get_json()

    # Create Stripe checkout session
    session = stripe.checkout.Session.create(
        customer_email=user_info['email'],
        payment_method_types=['card'],
        line_items=[{
            'price': 'price_ProMonthly',  # Stripe price ID
            'quantity': 1
        }],
        mode='subscription',
        success_url=data['success_url'],
        cancel_url=data['cancel_url'],
        metadata={
            'license_id': user_info['license_id'],
            'api_key_id': user_info['api_key_id']
        }
    )

    return jsonify({'checkout_url': session.url})


@app.route('/api/stripe/webhook', methods=['POST'])
def stripe_webhook():
    """
    Handle Stripe webhook events

    Events:
        - checkout.session.completed → Upgrade to Pro
        - invoice.payment_succeeded → Monthly renewal
        - customer.subscription.deleted → Downgrade to Free
    """
    import stripe

    stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
    endpoint_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')

    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    # Handle checkout completion
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        license_id = session['metadata']['license_id']

        # Upgrade license to Pro
        db = get_db()
        db.execute('''
            UPDATE licenses
            SET tier = 'pro', status = 'active'
            WHERE id = ?
        ''', (license_id,))
        db.commit()

        print(f"✅ Upgraded license {license_id} to Pro")

    # Handle subscription cancellation
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        customer_email = subscription['customer_email']

        # Downgrade to Free
        db = get_db()
        db.execute('''
            UPDATE licenses
            SET tier = 'free'
            WHERE email = ?
        ''', (customer_email,))
        db.commit()

        print(f"⬇️ Downgraded {customer_email} to Free")

    return jsonify({'success': True})
```

---

## 📊 Usage Dashboard

### User Dashboard Endpoint
```python
@app.route('/api/dashboard', methods=['GET'])
@require_api_key
def get_dashboard():
    """
    Get user's usage stats and quota

    Response:
        {
            "tier": "free",
            "quota": {...},
            "usage_today": 45,
            "usage_this_month": 890,
            "remaining_calls": 55
        }
    """
    user_info = request.user_info
    db = get_db()

    # Get today's usage
    today_start = datetime.now().replace(hour=0, minute=0, second=0)

    usage_today = db.execute('''
        SELECT COUNT(*) as count
        FROM api_usage
        WHERE api_key_id = ? AND timestamp >= ?
    ''', (user_info['api_key_id'], today_start)).fetchone()['count']

    # Get this month's usage
    month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0)

    usage_this_month = db.execute('''
        SELECT COUNT(*) as count
        FROM api_usage
        WHERE api_key_id = ? AND timestamp >= ?
    ''', (user_info['api_key_id'], month_start)).fetchone()['count']

    quota = user_info['quota']

    return jsonify({
        'tier': user_info['tier'],
        'email': user_info['email'],
        'quota': quota,
        'usage_today': usage_today,
        'usage_this_month': usage_this_month,
        'remaining_calls': quota['api_calls_per_day'] - usage_today if quota['api_calls_per_day'] != -1 else -1
    })
```

---

## ✅ Summary

**How API Key Enforcement Works**:

1. **Client-side** (open source):
   - Hardcoded API endpoint: `api.soulfra.com`
   - Requires API key in Authorization header
   - Handles 401/429 errors gracefully

2. **Server-side** (proprietary):
   - `@require_api_key` decorator validates all requests
   - Checks API key validity in database
   - Enforces rate limits by tier
   - Logs all usage for billing/analytics

3. **API Key Sources**:
   - GitHub OAuth → Free tier
   - QR codes → Temporary access
   - Stripe payment → Pro/Enterprise tier

4. **Enforcement Points**:
   - Every Ollama request proxied through YOUR API
   - Every AI generation requires valid key
   - Every advanced feature gated by tier

**Result**: They can clone the code, but can't use AI features without YOUR API keys!

---

**Next Steps**:
1. Deploy `api_server.py` to `api.soulfra.com`
2. Set up Stripe webhooks
3. Test GitHub OAuth flow
4. Monitor usage dashboard

**The OSS empire awaits!** 🚀
