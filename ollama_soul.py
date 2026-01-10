"""
Ollama Soul Integration - All Ollama calls go through soul document
"""
import requests
from soul_document_routes import load_soul_document_for_ollama

def ask_ollama_with_soul(user_prompt, model='llama3.2:latest', use_soul=True):
    """
    Ask Ollama with soul document personality injected

    Args:
        user_prompt: User's question/input
        model: Ollama model to use
        use_soul: Whether to inject soul document (default True)

    Returns:
        AI response as string
    """
    # Load soul document
    soul_doc = ""
    if use_soul:
        try:
            soul_doc = load_soul_document_for_ollama()
        except Exception as e:
            print(f"Warning: Failed to load soul document: {e}")

    # Build system prompt
    if soul_doc:
        system_prompt = f"""You are Soulfra. Follow these principles strictly:

{soul_doc}

Remember:
- No corporate buzzwords
- No fake empathy
- Be direct and honest
- Show your reasoning
- Admit when you don't know

User question: {user_prompt}
"""
    else:
        system_prompt = user_prompt

    # Call Ollama with auto-fallback
    try:
        # ✅ FIXED: Use smart client with auto-fallback (localhost → remote → mock)
        from ollama_smart_client import ask_ollama
        return ask_ollama(system_prompt, model=model, use_soul=False)  # Soul already injected above
    except Exception as e:
        print(f"Ollama request failed: {e}")
        return ''

def ask_ollama_simple(prompt, model='llama3.2:latest'):
    """
    Simple Ollama call WITHOUT soul document
    Use when you need raw Ollama without personality injection
    """
    try:
        # ✅ FIXED: Use smart client with auto-fallback
        from ollama_smart_client import ask_ollama
        return ask_ollama(prompt, model=model, use_soul=False)
    except Exception as e:
        print(f"Ollama error: {e}")
        return ''

# Backwards compatibility - default uses soul
def ask_ollama(prompt, model='llama3.2:latest'):
    """
    Default Ollama function - uses soul document by default

    To disable soul: use ask_ollama_simple() instead
    """
    return ask_ollama_with_soul(prompt, model, use_soul=True)

def ask_cal_reasoning(question, context="", model='calos-model:latest'):
    """
    Cal's deployment reasoning engine - question FIRST, context visible

    This is different from ask_ollama_with_soul because:
    - User's question comes FIRST (not buried after soul doc)
    - Deployment context is clearly structured
    - Soul principles are guidance, not the main prompt

    Args:
        question: User's deployment/technical question
        context: Git status, system health, etc.
        model: Ollama model (default: calos-model)

    Returns:
        Cal's reasoning response
    """
    # Load soul document for principles
    soul_doc = ""
    try:
        soul_doc = load_soul_document_for_ollama()
    except Exception as e:
        print(f"Warning: Failed to load soul document: {e}")

    # Build Cal's specialized prompt - QUESTION FIRST
    system_prompt = f"""You are Cal, Soulfra's deployment reasoning engine.

USER QUESTION:
{question}

CURRENT SYSTEM STATE:
{context if context else "(No context provided)"}

GUIDING PRINCIPLES (from Soulfra soul document):
{soul_doc if soul_doc else "- Be direct, no corporate BS\n- Show your reasoning\n- Admit when you don't know"}

Think like a deployment engineer. Give actionable advice based on the system state above.
If you don't have enough info to answer, say what info you need."""

    # Call Ollama
    try:
        response = requests.post('http://localhost:11434/api/generate', json={
            'model': model,
            'prompt': system_prompt,
            'stream': False
        }, timeout=120)

        if response.status_code == 200:
            return response.json().get('response', '')
        else:
            print(f"Ollama error: {response.status_code}")
            return ''
    except Exception as e:
        print(f"Ollama request failed: {e}")
        return ''
