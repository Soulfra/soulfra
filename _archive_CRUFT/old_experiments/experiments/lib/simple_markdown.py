#!/usr/bin/env python3
"""
Simple Markdown Parser - Pure Python Stdlib (Zero Dependencies)

Minimal markdown-to-HTML converter using only stdlib.
Replaces markdown2 library with from-scratch implementation.

Supports:
- Headers (# ## ###)
- Bold (**text**)
- Italic (*text*)
- Links ([text](url))
- Code blocks (```code```)
- Inline code (`code`)
- Lists (- item)
- Line breaks

Philosophy: Keep it simple. No complex regex. Just string operations.
"""

import re


def markdown_to_html(text, extras=None):
    """
    Convert markdown to HTML

    Args:
        text: Markdown text
        extras: List of extra features (compatible with markdown2 API)
                - 'fenced-code-blocks': ```code``` blocks
                - 'tables': | tables |
                - 'break-on-newline': Convert \\n to <br>
                - 'header-ids': Add id attributes to headers

    Returns:
        HTML string

    Example:
        >>> markdown_to_html("# Hello\\n\\nThis is **bold**!")
        '<h1>Hello</h1>\\n<p>This is <strong>bold</strong>!</p>'
    """
    extras = extras or []

    if not text:
        return ''

    lines = text.split('\n')
    html = []
    in_code_block = False
    code_block_lines = []
    in_paragraph = False
    paragraph_lines = []

    for line in lines:
        # Fenced code blocks (```)
        if 'fenced-code-blocks' in extras and line.strip().startswith('```'):
            if in_code_block:
                # End code block
                code_html = '\n'.join(code_block_lines)
                html.append(f'<pre><code>{_escape_html(code_html)}</code></pre>')
                code_block_lines = []
                in_code_block = False
            else:
                # Start code block
                if in_paragraph:
                    html.append(f'<p>{_process_inline(" ".join(paragraph_lines))}</p>')
                    paragraph_lines = []
                    in_paragraph = False
                in_code_block = True
            continue

        if in_code_block:
            code_block_lines.append(line)
            continue

        # Headers
        if line.startswith('#'):
            if in_paragraph:
                html.append(f'<p>{_process_inline(" ".join(paragraph_lines))}</p>')
                paragraph_lines = []
                in_paragraph = False

            level = len(line) - len(line.lstrip('#'))
            level = min(level, 6)  # Max h6
            text_content = line.lstrip('#').strip()

            if 'header-ids' in extras:
                # Generate ID from header text
                header_id = text_content.lower().replace(' ', '-').replace('?', '').replace('.', '')
                html.append(f'<h{level} id="{header_id}">{_process_inline(text_content)}</h{level}>')
            else:
                html.append(f'<h{level}>{_process_inline(text_content)}</h{level}>')
            continue

        # Empty lines end paragraphs
        if not line.strip():
            if in_paragraph:
                html.append(f'<p>{_process_inline(" ".join(paragraph_lines))}</p>')
                paragraph_lines = []
                in_paragraph = False
            html.append('')
            continue

        # Lists
        if line.strip().startswith(('- ', '* ', '+ ')):
            if in_paragraph:
                html.append(f'<p>{_process_inline(" ".join(paragraph_lines))}</p>')
                paragraph_lines = []
                in_paragraph = False

            item = line.strip()[2:]  # Remove "- " or "* " or "+ "
            html.append(f'<li>{_process_inline(item)}</li>')
            continue

        # Regular text (paragraph)
        if 'break-on-newline' in extras:
            # Each line is a separate paragraph or <br>
            if in_paragraph:
                html.append(f'<p>{_process_inline(" ".join(paragraph_lines))}</p>')
                paragraph_lines = []
            html.append(f'<p>{_process_inline(line)}</p>')
            in_paragraph = False
        else:
            # Accumulate lines into paragraphs
            paragraph_lines.append(line)
            in_paragraph = True

    # Close any open paragraph
    if in_paragraph:
        html.append(f'<p>{_process_inline(" ".join(paragraph_lines))}</p>')

    return '\n'.join(html)


def _process_inline(text):
    """Process inline markdown (bold, italic, links, code)"""
    # Inline code (`code`)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)

    # Bold (**text** or __text__)
    text = re.sub(r'\*\*([^\*]+)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__([^_]+)__', r'<strong>\1</strong>', text)

    # Italic (*text* or _text_)
    text = re.sub(r'\*([^\*]+)\*', r'<em>\1</em>', text)
    text = re.sub(r'_([^_]+)_', r'<em>\1</em>', text)

    # Links ([text](url))
    text = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2">\1</a>', text)

    return text


def _escape_html(text):
    """Escape HTML special characters"""
    return (text
        .replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('"', '&quot;')
        .replace("'", '&#39;'))


# ==============================================================================
# TESTING
# ==============================================================================

if __name__ == '__main__':
    print("🧪 Testing Simple Markdown Parser\n")

    # Test 1: Headers
    md = "# Header 1\n## Header 2\n### Header 3"
    html = markdown_to_html(md)
    print("Test 1: Headers")
    print(f"Input: {md!r}")
    print(f"Output: {html}")
    print()

    # Test 2: Bold and Italic
    md = "This is **bold** and this is *italic*"
    html = markdown_to_html(md)
    print("Test 2: Bold and Italic")
    print(f"Input: {md!r}")
    print(f"Output: {html}")
    print()

    # Test 3: Links
    md = "Check out [Soulfra](https://soulfra.com)"
    html = markdown_to_html(md)
    print("Test 3: Links")
    print(f"Input: {md!r}")
    print(f"Output: {html}")
    print()

    # Test 4: Code blocks
    md = "```\\nprint('hello')\\n```"
    html = markdown_to_html(md, extras=['fenced-code-blocks'])
    print("Test 4: Code Blocks")
    print(f"Input: {md!r}")
    print(f"Output: {html}")
    print()

    # Test 5: Lists
    md = "- Item 1\\n- Item 2\\n- Item 3"
    html = markdown_to_html(md)
    print("Test 5: Lists")
    print(f"Input: {md!r}")
    print(f"Output: {html}")
    print()

    print("✅ Simple Markdown Parser tests complete!")
