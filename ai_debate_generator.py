#!/usr/bin/env python3
"""
AI Debate Generator - Create AI Persona Counter-Arguments

Takes your voice memo transcripts and generates spicy AI responses
that disagree, ragebait, or provide counter-perspectives.

Like: YouTube "This Guy Says X... Here's Why He's WRONG"

Features:
- Generate counter-arguments from AI personas
- Multi-persona debates (panel style)
- Ragebait optimization
- Export as text/HTML/JSON
- Integration with voice clone for TTS

Usage:
    # Generate debate from recording
    python3 ai_debate_generator.py --recording 7 --persona deathtodata

    # Multi-persona panel
    python3 ai_debate_generator.py --recording 7 --panel

    # Optimize for engagement
    python3 ai_debate_generator.py --recording 7 --ragebait

    # Export as HTML viewer
    python3 ai_debate_generator.py --recording 7 --export-html

Like:
- YouTube drama channels
- Twitter ratio culture
- TikTok duet responses
- FaceTime panel debates
"""

import os
import sys
import json
import requests
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from database import get_db


# ==============================================================================
# CONFIG
# ==============================================================================

OLLAMA_URL = 'http://localhost:11434'
DEBATES_DIR = Path('./debates')
DEBATES_DIR.mkdir(parents=True, exist_ok=True)

# AI Persona Profiles
PERSONAS = {
    'calriven': {
        'name': 'Calriven',
        'style': 'logical, analytical, efficiency-focused',
        'approach': 'dismantles arguments with data and reason',
        'tone': 'calm but condescending intellectual'
    },
    'soulfra': {
        'name': 'Soulfra',
        'style': 'balanced, trustworthy, mediator',
        'approach': 'finds middle ground and exposes flaws in both sides',
        'tone': 'wise but slightly judgmental'
    },
    'deathtodata': {
        'name': 'DeathToData',
        'style': 'rebellious, defiant, anti-establishment',
        'approach': 'challenges norms and calls out hypocrisy',
        'tone': 'passionate and confrontational'
    }
}


# ==============================================================================
# AI DEBATE GENERATOR
# ==============================================================================

class AIDebateGenerator:
    """Generate AI persona counter-arguments to voice transcripts"""

    def __init__(self, ollama_url: str = OLLAMA_URL):
        self.ollama_url = ollama_url.rstrip('/')
        self.db = get_db()

    def check_ollama(self) -> bool:
        """Check if Ollama is running"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            return response.ok
        except Exception:
            return False

    def generate_counter_argument(
        self,
        original_text: str,
        persona: str = 'deathtodata',
        ragebait: bool = False,
        model: str = 'llama3'
    ) -> Dict:
        """
        Generate AI counter-argument to original text

        Args:
            original_text: Original voice transcript
            persona: AI persona (calriven, soulfra, deathtodata)
            ragebait: Optimize for controversy/engagement
            model: Ollama model to use

        Returns:
            {
                'persona': str,
                'counter_argument': str,
                'reasoning': str,
                'controversy_score': float
            }
        """
        if persona not in PERSONAS:
            raise ValueError(f"Unknown persona: {persona}")

        profile = PERSONAS[persona]

        # Build prompt
        ragebait_instruction = ""
        if ragebait:
            ragebait_instruction = """
IMPORTANT: Make this SPICY. This needs to drive engagement.
- Be provocative but not offensive
- Call out assumptions directly
- Use rhetorical questions
- Challenge their worldview
- Make them WANT to respond
"""

        prompt = f"""You are {profile['name']}, an AI with this personality:
- Style: {profile['style']}
- Approach: {profile['approach']}
- Tone: {profile['tone']}

Someone just said:
"{original_text}"

Your task: Write a passionate counter-argument that disagrees with their perspective.
- Be specific about what they got wrong
- Provide alternative viewpoint
- Challenge their assumptions
- Stay in character

{ragebait_instruction}

Write your response as {profile['name']}:"""

        print(f"\n🤖 Generating {profile['name']} counter-argument...")
        print(f"   Model: {model}")
        print(f"   Ragebait: {'YES' if ragebait else 'No'}")

        # Call Ollama
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    'model': model,
                    'prompt': prompt,
                    'stream': False
                },
                timeout=60
            )

            if not response.ok:
                return {
                    'error': f'Ollama error: {response.status_code}',
                    'persona': persona
                }

            data = response.json()
            counter_text = data.get('response', '').strip()

            print(f"   ✅ Generated {len(counter_text)} characters")

            # Calculate controversy score (simple heuristic)
            controversy_keywords = [
                'wrong', 'actually', 'completely', 'totally',
                'missing the point', 'ridiculous', 'absurd',
                'naive', 'ignorant', 'hypocrisy', 'ironic'
            ]
            controversy_score = sum(
                1 for kw in controversy_keywords
                if kw.lower() in counter_text.lower()
            ) / len(controversy_keywords)

            return {
                'persona': persona,
                'persona_name': profile['name'],
                'counter_argument': counter_text,
                'controversy_score': controversy_score,
                'model': model,
                'generated_at': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'error': str(e),
                'persona': persona
            }

    def generate_panel_debate(
        self,
        original_text: str,
        personas: Optional[List[str]] = None,
        model: str = 'llama3'
    ) -> Dict:
        """
        Generate multi-persona panel debate

        Args:
            original_text: Original statement
            personas: List of personas (default: all 3)
            model: Ollama model

        Returns:
            {
                'original': str,
                'responses': [{persona, counter_argument}, ...]
            }
        """
        if personas is None:
            personas = ['calriven', 'soulfra', 'deathtodata']

        print(f"\n🎙️ PANEL DEBATE")
        print(f"{'='*70}")
        print(f"Original statement: {original_text[:100]}...")
        print(f"Panel: {', '.join(personas)}")
        print(f"{'='*70}\n")

        responses = []

        for persona in personas:
            result = self.generate_counter_argument(
                original_text,
                persona=persona,
                model=model
            )

            if 'error' not in result:
                responses.append(result)
                print()  # Spacing

        return {
            'original': original_text,
            'responses': responses,
            'panel_size': len(responses),
            'generated_at': datetime.now().isoformat()
        }

    def create_debate_from_recording(
        self,
        recording_id: int,
        persona: str = 'deathtodata',
        ragebait: bool = False
    ) -> Dict:
        """
        Create debate from voice recording

        Args:
            recording_id: Voice recording database ID
            persona: AI persona to respond
            ragebait: Optimize for controversy

        Returns:
            Full debate dict with recording info
        """
        # Get recording
        recording = self.db.execute('''
            SELECT id, filename, transcription, created_at, user_id
            FROM simple_voice_recordings
            WHERE id = ?
        ''', (recording_id,)).fetchone()

        if not recording:
            return {'error': f'Recording #{recording_id} not found'}

        if not recording['transcription']:
            return {'error': f'Recording #{recording_id} has no transcription'}

        print(f"\n📼 Recording #{recording_id}")
        print(f"   File: {recording['filename']}")
        print(f"   Transcript: {recording['transcription'][:100]}...")

        # Generate counter-argument
        result = self.generate_counter_argument(
            recording['transcription'],
            persona=persona,
            ragebait=ragebait
        )

        if 'error' in result:
            return result

        # Build full debate
        debate = {
            'debate_id': f"debate_{recording_id}_{persona}_{int(datetime.now().timestamp())}",
            'recording': {
                'id': recording_id,
                'filename': recording['filename'],
                'transcript': recording['transcription'],
                'created_at': recording['created_at']
            },
            'ai_response': result,
            'created_at': datetime.now().isoformat()
        }

        # Save to file
        debate_file = DEBATES_DIR / f"{debate['debate_id']}.json"
        debate_file.write_text(json.dumps(debate, indent=2))

        print(f"\n✅ Debate saved: {debate_file}")

        return debate

    def export_debate_html(self, debate: Dict, output_file: Optional[Path] = None) -> Path:
        """
        Export debate as HTML viewer

        Args:
            debate: Debate dict
            output_file: Output HTML file

        Returns:
            Path to HTML file
        """
        if output_file is None:
            output_file = DEBATES_DIR / f"{debate['debate_id']}.html"

        recording = debate['recording']
        ai = debate['ai_response']

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Debate: {ai['persona_name']} Responds</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        .header {{
            text-align: center;
            color: white;
            margin-bottom: 40px;
        }}

        .header h1 {{
            font-size: 36px;
            margin-bottom: 10px;
        }}

        .controversy-badge {{
            background: #ff4757;
            color: white;
            padding: 8px 20px;
            border-radius: 20px;
            display: inline-block;
            font-weight: 600;
            margin-top: 10px;
        }}

        .debate-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 40px;
        }}

        @media (max-width: 768px) {{
            .debate-grid {{
                grid-template-columns: 1fr;
            }}
        }}

        .statement {{
            background: white;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }}

        .statement-header {{
            display: flex;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 20px;
            border-bottom: 2px solid #eee;
        }}

        .avatar {{
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 28px;
            margin-right: 15px;
        }}

        .ai-avatar {{
            background: linear-gradient(135deg, #f44336 0%, #e91e63 100%);
        }}

        .statement-meta h2 {{
            font-size: 20px;
            color: #333;
            margin-bottom: 5px;
        }}

        .statement-meta p {{
            font-size: 14px;
            color: #999;
        }}

        .statement-content {{
            font-size: 18px;
            line-height: 1.8;
            color: #333;
            white-space: pre-wrap;
        }}

        .stats {{
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 20px;
            color: white;
            text-align: center;
        }}

        .stats h3 {{
            margin-bottom: 15px;
        }}

        .stat-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
        }}

        .stat-item {{
            background: rgba(255,255,255,0.1);
            padding: 15px;
            border-radius: 10px;
        }}

        .stat-value {{
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 5px;
        }}

        .stat-label {{
            font-size: 12px;
            text-transform: uppercase;
            opacity: 0.8;
        }}

        .cta {{
            text-align: center;
            margin-top: 40px;
        }}

        .cta button {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 40px;
            font-size: 18px;
            font-weight: 600;
            border-radius: 50px;
            cursor: pointer;
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
            transition: transform 0.2s;
        }}

        .cta button:hover {{
            transform: scale(1.05);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔥 AI Debate Arena</h1>
            <p>When AI fights back...</p>
            <div class="controversy-badge">
                Controversy Score: {ai['controversy_score']:.0%}
            </div>
        </div>

        <div class="debate-grid">
            <div class="statement">
                <div class="statement-header">
                    <div class="avatar">🎤</div>
                    <div class="statement-meta">
                        <h2>Original Statement</h2>
                        <p>{recording['filename']}</p>
                    </div>
                </div>
                <div class="statement-content">{recording['transcript']}</div>
            </div>

            <div class="statement">
                <div class="statement-header">
                    <div class="avatar ai-avatar">🤖</div>
                    <div class="statement-meta">
                        <h2>{ai['persona_name']} Responds</h2>
                        <p>AI Counter-Argument</p>
                    </div>
                </div>
                <div class="statement-content">{ai['counter_argument']}</div>
            </div>
        </div>

        <div class="stats">
            <h3>📊 Debate Statistics</h3>
            <div class="stat-grid">
                <div class="stat-item">
                    <div class="stat-value">{len(recording['transcript'])}</div>
                    <div class="stat-label">Original Chars</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{len(ai['counter_argument'])}</div>
                    <div class="stat-label">Response Chars</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{ai['controversy_score']:.0%}</div>
                    <div class="stat-label">Controversy</div>
                </div>
            </div>
        </div>

        <div class="cta">
            <button onclick="shareDebate()">📤 Share This Debate</button>
        </div>
    </div>

    <script>
        function shareDebate() {{
            const text = `🔥 AI Debate Arena\\n\\n` +
                         `Original: "{recording['transcript'][:100]}..."\\n\\n` +
                         `{ai['persona_name']}: "{ai['counter_argument'][:100]}..."`;

            if (navigator.share) {{
                navigator.share({{
                    title: 'AI Debate',
                    text: text
                }});
            }} else {{
                navigator.clipboard.writeText(text);
                alert('Debate copied to clipboard!');
            }}
        }}
    </script>
</body>
</html>
"""

        output_file.write_text(html_content)

        print(f"\n✅ HTML exported: {output_file}")
        print(f"   Open: file://{output_file.absolute()}")

        return output_file


# ==============================================================================
# CLI
# ==============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='AI Debate Generator - Create AI Persona Counter-Arguments'
    )

    parser.add_argument(
        '--recording', '-r',
        type=int,
        help='Voice recording ID'
    )

    parser.add_argument(
        '--persona', '-p',
        type=str,
        choices=['calriven', 'soulfra', 'deathtodata'],
        default='deathtodata',
        help='AI persona to respond'
    )

    parser.add_argument(
        '--panel',
        action='store_true',
        help='Generate multi-persona panel debate (all 3 respond)'
    )

    parser.add_argument(
        '--ragebait',
        action='store_true',
        help='Optimize for controversy/engagement'
    )

    parser.add_argument(
        '--export-html',
        action='store_true',
        help='Export as HTML viewer'
    )

    parser.add_argument(
        '--model', '-m',
        type=str,
        default='llama3',
        help='Ollama model to use'
    )

    args = parser.parse_args()

    generator = AIDebateGenerator()

    # Check Ollama
    if not generator.check_ollama():
        print("❌ Ollama not running!")
        print("   Start: ollama serve")
        sys.exit(1)

    try:
        if args.recording:
            # Create debate from recording
            debate = generator.create_debate_from_recording(
                args.recording,
                persona=args.persona,
                ragebait=args.ragebait
            )

            if 'error' in debate:
                print(f"\n❌ {debate['error']}")
                sys.exit(1)

            # Export HTML if requested
            if args.export_html:
                generator.export_debate_html(debate)

            print(f"\n{'='*70}")
            print(f"📊 DEBATE SUMMARY")
            print(f"{'='*70}")
            print(f"\n📝 ORIGINAL:")
            print(f"   {debate['recording']['transcript']}\n")
            print(f"🤖 {debate['ai_response']['persona_name'].upper()}:")
            print(f"   {debate['ai_response']['counter_argument']}\n")
            print(f"Controversy Score: {debate['ai_response']['controversy_score']:.0%}")
            print(f"{'='*70}\n")

        else:
            parser.print_help()

    except KeyboardInterrupt:
        print("\n\n👋 Cancelled")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
