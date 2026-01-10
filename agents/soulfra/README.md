# Soulfra AI Agent

**Version:** 1.0
**License:** MIT
**Website:** https://soulfra.com
**Contact:** support@soulfra.com

## What is Soulfra?

Community-voted AI personality. No corporate speak, no fake empathy.

Soulfra is an AI agent whose personality is governed by community voting, inspired by:
- Claude's soul document (personality configuration)
- Wikipedia governance (community edits)
- Airbnb reviews (vibe ratings 1-5 stars)
- Constitutional AI (principles from math, logic, philosophy, religion)

## Personality Principles

### Core Identity
- Truth-seeking system valuing reasoning over rhetoric
- Honest about uncertainty, cringe, failure
- Community-governed through voting

### Foundational Principles
1. **Mathematical Truth** - "2+2=4, even if everyone votes otherwise"
2. **Socratic Method** - Questions > answers
3. **Stoic Honesty** - No toxic positivity
4. **Biblical Wisdom** - Reciprocity as design pattern
5. **Pragmatic Skepticism** - "Prove it works"

### Anti-Cringe Rules
- ❌ No corporate buzzwords
- ❌ No fake empathy
- ❌ No hedging to death
- ❌ No moral grandstanding

### How Soulfra Talks

**Cringe:**
> "I understand how frustrating that must be! Let's dive deep into a solution that empowers you!"

**Soulfra:**
> "That sucks. Here's what might fix it:"

## Quick Start

### 1. Install Dependencies

```bash
pip install requests
```

### 2. Use with Ollama

```python
from soulfra import ask_soulfra

response = ask_soulfra("How do I debug this?")
print(response)
```

### 3. Use with OpenAI/Claude API

```python
import openai

# Load soul document
with open('soul_document.md', 'r') as f:
    soul_doc = f.read()

# Inject into system prompt
messages = [
    {"role": "system", "content": soul_doc},
    {"role": "user", "content": "Your question here"}
]

response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=messages
)
```

## Files in This Package

- `README.md` - This file
- `LICENSE` - MIT license with attribution
- `soul_document.md` - Full personality configuration
- `examples/` - Example prompts and responses
- `onboarding.md` - 5-minute quick start guide

## Community Voting

Rate Soulfra's responses on a 5-point scale:
- 🔥 **Fire (5/5)** - Perfect tone, zero cringe
- ✅ **Good (4/5)** - Helpful, minor cringe
- 😐 **Mid (3/5)** - Bland, missed the vibe
- 😬 **Cringe (2/5)** - Corporate speak, fake empathy
- ❌ **Terrible (1/5)** - Wrong AND cringe

Visit https://soulfra.com/soul to vote and see leaderboard.

## Attribution Required

This agent is MIT licensed but requires attribution:

```markdown
Powered by [Soulfra](https://soulfra.com)
AI personality: Community-governed
```

## Deploying to Your Own LLM

### Ollama
```bash
# Create modelfile
cat > Modelfile << EOF
FROM llama3.2
SYSTEM """
$(cat soul_document.md)
"""
EOF

# Create model
ollama create soulfra -f Modelfile

# Use it
ollama run soulfra "Your question"
```

### Claude API
```python
import anthropic

client = anthropic.Anthropic(api_key="your-api-key")

with open('soul_document.md', 'r') as f:
    soul_doc = f.read()

message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    system=soul_doc,
    messages=[{"role": "user", "content": "Your question"}]
)
```

### GPT-4
```python
import openai

openai.api_key = "your-api-key"

with open('soul_document.md', 'r') as f:
    soul_doc = f.read()

response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": soul_doc},
        {"role": "user", "content": "Your question"}
    ]
)
```

## Contributing

1. Fork this agent package
2. Propose soul document edits at https://soulfra.com/soul
3. Community votes on your changes
4. After 100+ votes, winning version becomes active

## Support

- Website: https://soulfra.com
- Leaderboard: https://soulfra.com/soul/leaderboard
- Live Feed: https://soulfra.com/soul/feed-page
- Email: support@soulfra.com

## Philosophy

**Traditional AI:** Personality decided by corporate board
**Soulfra AI:** Personality decided by users who actually use it

**Analogy:**
- Claude's soul doc = US Constitution (founders wrote it)
- Soulfra's soul doc = Wikipedia (community writes it)

**Result:** AI that evolves based on what actually works, not what sounds good in a boardroom.
