#!/usr/bin/env python3
"""
SOP Generator - AI-Assisted SOP Filling

Uses Ollama to intelligently fill SOP templates based on brand discussion context.
Turns unstructured conversations into actionable, structured SOPs.

Usage:
    from sop_generator import SOPGenerator

    generator = SOPGenerator()
    filled_sop = generator.generate_from_discussion(discussion_id, 'brand_identity')
"""

import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, List
from database import get_db
from brand_sop_templates import SOPTemplateLibrary


class SOPGenerator:
    """Generate filled SOPs from brand discussions using Ollama"""

    def __init__(self, ollama_host: str = 'http://localhost:11434'):
        """
        Initialize SOP generator

        Args:
            ollama_host: Ollama API endpoint
        """
        self.ollama_host = ollama_host
        self.template_library = SOPTemplateLibrary()

    def call_ollama(self, prompt: str, system_prompt: str = None, max_tokens: int = 300) -> Optional[str]:
        """
        Call Ollama API

        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            max_tokens: Maximum tokens to generate

        Returns:
            AI response or None if error
        """
        try:
            request_data = {
                'model': 'llama2',
                'prompt': prompt,
                'stream': False,
                'options': {
                    'temperature': 0.7,
                    'num_predict': max_tokens
                }
            }

            if system_prompt:
                request_data['system'] = system_prompt

            req = urllib.request.Request(
                f'{self.ollama_host}/api/generate',
                data=json.dumps(request_data).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )

            response = urllib.request.urlopen(req, timeout=60)
            result = json.loads(response.read().decode('utf-8'))
            return result.get('response', '').strip()

        except urllib.error.URLError:
            print("❌ Error: Ollama not running. Start with: ollama serve")
            return None
        except Exception as e:
            print(f"❌ Error calling Ollama: {str(e)}")
            return None

    def get_discussion_context(self, session_id: int) -> Dict[str, Any]:
        """
        Get discussion context from database

        Args:
            session_id: Discussion session ID

        Returns:
            Dictionary with brand info and discussion messages
        """
        db = get_db()

        # Get session details
        session = db.execute('''
            SELECT * FROM discussion_sessions WHERE id = ?
        ''', (session_id,)).fetchone()

        if not session:
            db.close()
            return {}

        # Get brand if this is a brand discussion
        brand = None
        if session['brand_name']:
            brand = db.execute('''
                SELECT * FROM brands WHERE slug = ?
            ''', (session['brand_name'],)).fetchone()

        # Get all messages
        messages = db.execute('''
            SELECT * FROM discussion_messages
            WHERE session_id = ?
            ORDER BY created_at ASC
        ''', (session_id,)).fetchall()

        db.close()

        return {
            'session': dict(session),
            'brand': dict(brand) if brand else None,
            'messages': [dict(m) for m in messages],
            'discussion_text': '\n'.join([
                f"{m['sender']}: {m['content']}"
                for m in messages
                if m['message_type'] == 'chat'
            ])
        }

    def fill_field_with_ai(self, field_config: Dict[str, Any], discussion_context: Dict[str, Any]) -> Any:
        """
        Use Ollama to fill a single field based on discussion context

        Args:
            field_config: Field configuration from template
            discussion_context: Discussion context dictionary

        Returns:
            Filled value (string, list, object, etc.)
        """
        field_type = field_config['type']
        prompt_question = field_config['prompt']
        example = field_config.get('example', '')

        # Build prompt based on field type
        system_prompt = """You are an expert brand strategist helping to create structured SOPs.
Based on the brand discussion provided, extract specific information to fill SOP fields.
Be concise and actionable. If information is not in the discussion, use your expertise to suggest reasonable defaults."""

        user_prompt = f"""Brand Discussion:
{discussion_context.get('discussion_text', 'No discussion yet')}

Question: {prompt_question}

Example answer: {example}

Based on the discussion above, provide a {field_type} answer to this question.
"""

        # Add type-specific instructions
        if field_type == 'list':
            user_prompt += "\nProvide your answer as a comma-separated list (e.g., Item 1, Item 2, Item 3)"
        elif field_type == 'object':
            user_prompt += "\nProvide your answer as JSON object"
        elif field_type == 'select':
            options = field_config.get('options', [])
            user_prompt += f"\nChoose ONE from: {', '.join(options)}"
        elif field_type == 'boolean':
            user_prompt += "\nAnswer with: yes or no"
        elif field_type == 'color':
            user_prompt += "\nProvide as hex color code (e.g., #667eea)"
        elif field_type == 'number':
            user_prompt += "\nProvide as a number only"

        # Call Ollama
        response = self.call_ollama(user_prompt, system_prompt=system_prompt)

        if not response:
            return None

        # Parse response based on type
        try:
            if field_type == 'list':
                # Split by comma and clean
                items = [item.strip() for item in response.split(',')]
                return [item for item in items if item]

            elif field_type == 'object':
                # Try to parse as JSON, fallback to key:value pairs
                try:
                    return json.loads(response)
                except:
                    # Parse "key: value" format
                    obj = {}
                    for line in response.split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            obj[key.strip()] = value.strip()
                    return obj

            elif field_type == 'boolean':
                return 'yes' in response.lower() or 'true' in response.lower()

            elif field_type == 'number':
                # Extract first number found
                import re
                numbers = re.findall(r'\d+', response)
                return int(numbers[0]) if numbers else 0

            elif field_type == 'select':
                # Find which option was mentioned
                options = field_config.get('options', [])
                response_lower = response.lower()
                for option in options:
                    if option.lower() in response_lower:
                        return option
                return options[0] if options else response

            else:  # text, color
                return response

        except Exception as e:
            print(f"⚠️  Error parsing field: {e}")
            return response  # Return raw response if parsing fails

    def generate_from_discussion(self, session_id: int, template_id: str, auto_fill: bool = True) -> Optional[Dict[str, Any]]:
        """
        Generate SOP from discussion session

        Args:
            session_id: Discussion session ID
            template_id: SOP template ID (e.g., 'brand_identity')
            auto_fill: Whether to use AI to fill fields automatically

        Returns:
            Filled SOP dictionary or None if error
        """
        # Get discussion context
        context = self.get_discussion_context(session_id)
        if not context:
            print(f"❌ Discussion session {session_id} not found")
            return None

        print(f"\n📋 Generating {template_id} SOP from discussion {session_id}...")

        # Generate empty SOP
        sop = self.template_library.generate_empty_sop(template_id)
        if not sop:
            print(f"❌ Template '{template_id}' not found")
            return None

        # Add brand metadata
        if context.get('brand'):
            sop['brand_name'] = context['brand']['name']
            sop['brand_slug'] = context['brand']['slug']

        sop['discussion_session_id'] = session_id

        # Auto-fill fields if requested
        if auto_fill:
            template = self.template_library.get_template(template_id)

            for section_idx, section in enumerate(template['sections']):
                print(f"\n  📝 Filling section: {section['title']}")

                for field_name, field_config in section['fields'].items():
                    print(f"     - {field_name}...", end=' ')

                    value = self.fill_field_with_ai(field_config, context)

                    if value:
                        sop = self.template_library.fill_field(sop, section_idx, field_name, value)
                        print("✅")
                    else:
                        print("⚠️  (skipped)")

        # Mark as complete if all required fields filled
        if self.template_library.is_complete(sop):
            sop['status'] = 'complete'
        else:
            sop['status'] = 'partial'

        print(f"\n✅ SOP generated (status: {sop['status']})")

        return sop

    def generate_all_sops(self, session_id: int) -> Dict[str, Dict[str, Any]]:
        """
        Generate all SOP types from a discussion

        Args:
            session_id: Discussion session ID

        Returns:
            Dictionary of {template_id: sop_dict}
        """
        sops = {}
        templates = self.template_library.list_templates()

        print(f"\n📚 Generating all SOPs from discussion {session_id}...")

        for template_info in templates:
            template_id = template_info['id']
            sop = self.generate_from_discussion(session_id, template_id, auto_fill=True)
            if sop:
                sops[template_id] = sop

        return sops

    def save_sop_to_database(self, sop: Dict[str, Any], brand_id: int) -> int:
        """
        Save SOP to database

        Args:
            sop: SOP dictionary
            brand_id: Brand ID

        Returns:
            SOP record ID
        """
        db = get_db()

        cursor = db.execute('''
            INSERT INTO brand_sops (
                brand_id,
                template_id,
                template_name,
                sop_data,
                status,
                created_at
            ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            brand_id,
            sop['template_id'],
            sop['template_name'],
            json.dumps(sop),
            sop['status']
        ))

        sop_id = cursor.lastrowid
        db.commit()
        db.close()

        return sop_id


# Create brand_sops table if needed
def init_sop_tables():
    """Initialize SOP tables in database"""
    db = get_db()

    db.execute('''
        CREATE TABLE IF NOT EXISTS brand_sops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand_id INTEGER NOT NULL,
            template_id TEXT NOT NULL,
            template_name TEXT NOT NULL,
            sop_data TEXT NOT NULL,
            status TEXT DEFAULT 'draft',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (brand_id) REFERENCES brands(id)
        )
    ''')

    db.commit()
    db.close()
    print("✅ SOP tables initialized")


if __name__ == '__main__':
    # Demo the SOP generator
    print("🤖 SOP Generator - AI-Assisted SOP Filling")
    print("=" * 70)

    # Initialize tables
    init_sop_tables()

    # Demo with mock discussion context
    print("\n📝 Demo: Generating Brand Identity SOP from discussion...")

    mock_context = {
        'discussion_text': '''user: We want to build a privacy-first analytics tool
ai: That's a great mission. Who would use this?
user: Developers who care about user privacy
ai: What makes you different from Google Analytics?
user: We're open source and don't track individual users
ai: What tone should the brand have?
user: Professional but approachable, technical'''
    }

    generator = SOPGenerator()

    # Test field filling
    field_config = {
        'type': 'text',
        'prompt': 'What is the mission of this brand?',
        'example': 'To empower developers with privacy-first tools'
    }

    value = generator.fill_field_with_ai(field_config, mock_context)
    print(f"\n✅ Filled field value: {value}")

    print("\n✅ SOP Generator Ready!")
    print("\nTo use with real discussion:")
    print("  generator = SOPGenerator()")
    print("  sop = generator.generate_from_discussion(session_id=1, template_id='brand_identity')")
