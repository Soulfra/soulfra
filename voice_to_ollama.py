#!/usr/bin/env python3
"""
Voice to Ollama - AI Debate System

Record voice prediction → Transcribe → Send to multiple AI models → Publish debate

Usage:
    python3 voice_to_ollama.py "Bitcoin will hit 100k by March"
    python3 voice_to_ollama.py ~/Downloads/voice-memo.m4a
"""

import sys
import os
import json
import subprocess
from pathlib import Path
from datetime import datetime

# Import Ollama
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    print("⚠️  Ollama not installed. Install with: pip install ollama")
    OLLAMA_AVAILABLE = False

# Import Whisper transcriber
try:
    from whisper_transcriber import WhisperTranscriber
    WHISPER_AVAILABLE = True
except ImportError:
    print("⚠️  Whisper transcriber not found")
    WHISPER_AVAILABLE = False

# Import market data for real-time context
try:
    from market_data import format_price_context_for_ai
    MARKET_DATA_AVAILABLE = True
except ImportError:
    print("⚠️  Market data module not found")
    MARKET_DATA_AVAILABLE = False

# Import brand router
try:
    from brand_router import detect_brand_from_prediction, get_brand_config, get_brand_models
    BRAND_ROUTER_AVAILABLE = True
except ImportError:
    print("⚠️  Brand router not found")
    BRAND_ROUTER_AVAILABLE = False

# Import real estate data
try:
    from real_estate_data import format_property_context_for_ai
    REAL_ESTATE_DATA_AVAILABLE = True
except ImportError:
    print("⚠️  Real estate data module not found")
    REAL_ESTATE_DATA_AVAILABLE = False

# Import prediction tracker
try:
    from prediction_tracker import log_prediction, get_accuracy
    PREDICTION_TRACKER_AVAILABLE = True
except ImportError:
    print("⚠️  Prediction tracker not found")
    PREDICTION_TRACKER_AVAILABLE = False


def transcribe_voice(audio_path):
    """Transcribe voice file to text"""
    if not WHISPER_AVAILABLE:
        print("❌ Whisper not available")
        return None

    print(f"🎧 Transcribing audio file: {audio_path}")
    transcriber = WhisperTranscriber()
    result = transcriber.transcribe(audio_path)

    if result and result.get('text'):
        print(f"📄 Transcription: {result['text'][:200]}...")
        return result['text']
    else:
        print("❌ Transcription failed")
        return None


def get_ollama_response(model, prompt, prediction_text):
    """Get response from Ollama model"""
    if not OLLAMA_AVAILABLE:
        return {"error": "Ollama not available"}

    print(f"🤖 Querying {model}...")

    # Inject real-time market data if available
    market_context = ""
    if MARKET_DATA_AVAILABLE:
        try:
            market_context = format_price_context_for_ai(prediction_text)
        except Exception as e:
            print(f"⚠️  Could not fetch market data: {e}")

    # Inject real estate data if available
    property_context = ""
    if REAL_ESTATE_DATA_AVAILABLE:
        try:
            property_context = format_property_context_for_ai(prediction_text)
        except Exception as e:
            print(f"⚠️  Could not fetch real estate data: {e}")

    # Add current date prominently
    current_date = datetime.now().strftime('%B %d, %Y')
    current_year = datetime.now().year

    system_prompt = f"""TODAY IS: {current_date}

{market_context}

{property_context}

You are debating a prediction. The user said:

"{prediction_text}"

Your job is to:
1. Analyze the prediction
2. Provide counterarguments or supporting evidence
3. Rate the likelihood (0-100%)
4. Give your own prediction
5. CITE YOUR SOURCES - Reference specific URLs and data sources

CRITICAL: Today is {current_year}. DO NOT cite your training data dates (2024/2025) as "current".
Use ONLY the live data provided above for your analysis.
ALWAYS cite sources with URLs (e.g., "According to CoinGecko API, BTC is at $X").
Be direct, insightful, and specific."""

    try:
        response = ollama.chat(
            model=model,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt}
            ]
        )

        return {
            'model': model,
            'response': response['message']['content'],
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        print(f"❌ Error with {model}: {e}")
        return {'model': model, 'error': str(e)}


def debate_with_models(prediction_text, brand_slug=None):
    """Send prediction to multiple models and collect responses"""

    # Auto-detect brand if not provided
    if not brand_slug and BRAND_ROUTER_AVAILABLE:
        brand_slug = detect_brand_from_prediction(prediction_text)
        brand_config = get_brand_config(brand_slug)
        print(f"🏷️  Auto-routed to: {brand_config['name']} ({brand_slug})")
        print(f"   {brand_config['tagline']}")
        print()

    # Check historical accuracy if available
    if PREDICTION_TRACKER_AVAILABLE and brand_slug:
        topic = brand_slug  # Simple topic detection
        for model in (get_brand_models(brand_slug) if BRAND_ROUTER_AVAILABLE else []):
            accuracy = get_accuracy(model=model, topic=topic)
            if accuracy > 0:
                print(f"📊 Historical accuracy for {model} on {topic}: {accuracy:.1f}%")

    # Get brand-specific models
    if brand_slug and BRAND_ROUTER_AVAILABLE:
        models = get_brand_models(brand_slug)
    else:
        # Fallback to default Soulfra models
        models = [
            'soulfra-model:latest',     # Soulfra authentic community model
            'deathtodata-model:latest', # DeathToData skeptic model
            'mistral:latest',           # Mistral creative model
        ]

    # Check which models are available
    try:
        available_models = ollama.list()
        available_names = [m['name'] for m in available_models.get('models', [])]
        print(f"📊 Available models: {available_names}")

        # Filter to only use available models
        models = [m for m in models if any(m.split(':')[0] in name for name in available_names)]

        if not models:
            print("⚠️  No target models available. Using first available model.")
            models = [available_names[0]] if available_names else []

    except Exception as e:
        print(f"⚠️  Could not list models: {e}")

    if not models:
        print("❌ No Ollama models available")
        return []

    print(f"\n🎯 Debating with {len(models)} models...")
    print(f"📢 Your prediction: {prediction_text}\n")

    prompt = f"Debate this prediction: {prediction_text}"

    responses = []
    for model in models:
        response = get_ollama_response(model, prompt, prediction_text)
        responses.append(response)

        if 'error' not in response:
            print(f"\n{'='*60}")
            print(f"🤖 {model}:")
            print(f"{'='*60}")
            print(response['response'][:500] + "..." if len(response['response']) > 500 else response['response'])
            print()

    return responses


def publish_debate(prediction_text, responses, output_dir="debates", brand_slug=None):
    """Publish debate to markdown file for GitHub Pages"""

    # Auto-detect brand if not provided
    if not brand_slug and BRAND_ROUTER_AVAILABLE:
        brand_slug = detect_brand_from_prediction(prediction_text)
        brand_config = get_brand_config(brand_slug)
        # Use brand-specific debate folder
        output_dir = brand_config['debate_folder']
        print(f"📁 Publishing to: {output_dir} ({brand_config['name']})")

    os.makedirs(output_dir, exist_ok=True)

    # Create filename
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M")
    slug = prediction_text[:50].lower().replace(' ', '-').replace(',', '').replace('.', '')
    filename = f"{timestamp}-{slug}.md"
    filepath = Path(output_dir) / filename

    # Generate markdown
    markdown = f"""---
title: AI Debate - {prediction_text[:80]}
date: {datetime.now().isoformat()}
prediction: "{prediction_text}"
models: {len(responses)}
---

# AI Model Debate

## Your Prediction
> {prediction_text}

---

## AI Responses

"""

    for response in responses:
        if 'error' in response:
            markdown += f"""
### ❌ {response['model']} (Error)
```
{response['error']}
```

"""
        else:
            markdown += f"""
### 🤖 {response['model']}

{response['response']}

<details>
<summary>Metadata</summary>

- **Model:** `{response['model']}`
- **Timestamp:** `{response['timestamp']}`

</details>

---

"""

    # Add footer
    markdown += f"""
## Verdict

Vote on which AI had the best response:
- [ ] {responses[0].get('model', 'Model 1')}
- [ ] {responses[1].get('model', 'Model 2') if len(responses) > 1 else 'N/A'}
- [ ] {responses[2].get('model', 'Model 3') if len(responses) > 2 else 'N/A'}

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    # Write file
    with open(filepath, 'w') as f:
        f.write(markdown)

    print(f"\n✅ Debate published: {filepath}")
    return filepath


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 voice_to_ollama.py <text or audio file>")
        print()
        print("Examples:")
        print("  python3 voice_to_ollama.py \"Bitcoin will hit 100k\"")
        print("  python3 voice_to_ollama.py ~/Downloads/prediction.m4a")
        sys.exit(1)

    input_arg = sys.argv[1]

    # Check if input is a file or text
    if os.path.isfile(input_arg):
        # Transcribe audio file
        prediction_text = transcribe_voice(input_arg)
        if not prediction_text:
            print("❌ Could not transcribe audio")
            sys.exit(1)
    else:
        # Use as direct text
        prediction_text = input_arg

    # Debate with AI models
    responses = debate_with_models(prediction_text)

    if not responses:
        print("❌ No responses from models")
        sys.exit(1)

    # Publish debate
    debate_file = publish_debate(prediction_text, responses)

    # Log prediction to tracker
    if PREDICTION_TRACKER_AVAILABLE and BRAND_ROUTER_AVAILABLE:
        brand_slug = detect_brand_from_prediction(prediction_text)
        models_used = [r.get('model') for r in responses if 'error' not in r]

        prediction_id = log_prediction(
            text=prediction_text,
            brand=brand_slug,
            debate_file=str(debate_file),
            models=models_used,
            model_responses=responses
        )

    print("\n" + "="*60)
    print("✅ Debate Complete!")
    print("="*60)
    print(f"📄 File: {debate_file}")
    print(f"🤖 Models: {len(responses)}")
    print(f"💬 Prediction: {prediction_text[:100]}")
    print()
    print("📤 Next step: Publish to GitHub Pages")
    print("   cd debates && git add . && git commit -m 'New debate' && git push")
    print("="*60)


if __name__ == '__main__':
    main()
