#!/usr/bin/env python3
"""
Brand SOP Templates - Structured Standard Operating Procedures

Provides templates for generating actionable SOPs from brand discussions.
Like CSS themes for brands, but for operational procedures.

Usage:
    from brand_sop_templates import SOPTemplateLibrary

    library = SOPTemplateLibrary()
    template = library.get_template('brand_identity')
    filled_sop = library.fill_template('brand_identity', discussion_context)
"""

import json
import yaml
from typing import Dict, Any, List, Optional
from datetime import datetime


# SOP Template Definitions
SOP_TEMPLATES = {
    'brand_identity': {
        'name': 'Brand Identity SOP',
        'description': 'Core brand mission, values, voice, and positioning',
        'version': '1.0',
        'sections': [
            {
                'title': 'Mission Statement',
                'fields': {
                    'mission': {
                        'type': 'text',
                        'prompt': 'What is this brand trying to achieve? Why does it exist?',
                        'example': 'To empower developers with privacy-first tools',
                        'required': True
                    },
                    'target_audience': {
                        'type': 'text',
                        'prompt': 'Who is this brand serving?',
                        'example': 'Privacy-conscious developers and tech leads',
                        'required': True
                    }
                }
            },
            {
                'title': 'Brand Values',
                'fields': {
                    'core_values': {
                        'type': 'list',
                        'prompt': 'What are the 3-5 core values that guide decisions?',
                        'example': ['Privacy First', 'Developer Experience', 'Open Source'],
                        'required': True
                    },
                    'non_negotiables': {
                        'type': 'list',
                        'prompt': 'What will this brand NEVER compromise on?',
                        'example': ['User data privacy', 'Transparency', 'Community trust'],
                        'required': False
                    }
                }
            },
            {
                'title': 'Brand Voice & Personality',
                'fields': {
                    'tone': {
                        'type': 'select',
                        'prompt': 'What tone best represents this brand?',
                        'options': ['Professional', 'Casual', 'Bold', 'Trustworthy', 'Playful'],
                        'required': True
                    },
                    'personality_traits': {
                        'type': 'list',
                        'prompt': 'If this brand was a person, what 3 words describe them?',
                        'example': ['Technical', 'Analytical', 'Direct'],
                        'required': True
                    },
                    'voice_guidelines': {
                        'type': 'object',
                        'prompt': 'How should this brand communicate?',
                        'structure': {
                            'do': ['Use clear technical language', 'Be direct and honest'],
                            'dont': ['Use marketing jargon', 'Make unrealistic promises']
                        },
                        'required': True
                    }
                }
            },
            {
                'title': 'Positioning',
                'fields': {
                    'unique_value': {
                        'type': 'text',
                        'prompt': 'What makes this brand different from competitors?',
                        'example': 'Only open-source, privacy-first analytics platform',
                        'required': True
                    },
                    'elevator_pitch': {
                        'type': 'text',
                        'prompt': 'Explain this brand in one sentence',
                        'example': 'We help developers build privacy-first apps without sacrificing analytics',
                        'required': True
                    }
                }
            }
        ]
    },

    'content_strategy': {
        'name': 'Content Strategy SOP',
        'description': 'Guidelines for content creation, topics, and publishing',
        'version': '1.0',
        'sections': [
            {
                'title': 'Content Pillars',
                'fields': {
                    'core_topics': {
                        'type': 'list',
                        'prompt': 'What 3-5 topics should content focus on?',
                        'example': ['Privacy engineering', 'Developer tools', 'Open source culture'],
                        'required': True
                    },
                    'content_formats': {
                        'type': 'list',
                        'prompt': 'What formats work best for this brand?',
                        'example': ['Technical blog posts', 'Code tutorials', 'Case studies'],
                        'required': True
                    }
                }
            },
            {
                'title': 'Publishing Schedule',
                'fields': {
                    'frequency': {
                        'type': 'text',
                        'prompt': 'How often should new content be published?',
                        'example': '2-3 posts per week',
                        'required': True
                    },
                    'best_times': {
                        'type': 'list',
                        'prompt': 'When is the audience most active?',
                        'example': ['Tuesday 9am EST', 'Thursday 2pm EST'],
                        'required': False
                    }
                }
            },
            {
                'title': 'Content Quality Standards',
                'fields': {
                    'minimum_word_count': {
                        'type': 'number',
                        'prompt': 'Minimum words for blog posts?',
                        'example': 800,
                        'required': False
                    },
                    'required_elements': {
                        'type': 'list',
                        'prompt': 'What must every piece of content include?',
                        'example': ['Code examples', 'Real-world use case', 'Call to action'],
                        'required': True
                    }
                }
            }
        ]
    },

    'visual_standards': {
        'name': 'Visual Standards SOP',
        'description': 'Colors, typography, imagery, and design guidelines',
        'version': '1.0',
        'sections': [
            {
                'title': 'Color Palette',
                'fields': {
                    'primary_color': {
                        'type': 'color',
                        'prompt': 'Primary brand color (hex)',
                        'example': '#667eea',
                        'required': True
                    },
                    'secondary_color': {
                        'type': 'color',
                        'prompt': 'Secondary brand color (hex)',
                        'example': '#764ba2',
                        'required': True
                    },
                    'accent_colors': {
                        'type': 'object',
                        'prompt': 'Additional accent colors',
                        'structure': {
                            'success': '#4ECDC4',
                            'warning': '#FFE66D',
                            'error': '#FF6B6B'
                        },
                        'required': False
                    }
                }
            },
            {
                'title': 'Typography',
                'fields': {
                    'heading_font': {
                        'type': 'text',
                        'prompt': 'Font family for headings',
                        'example': 'Inter, sans-serif',
                        'required': True
                    },
                    'body_font': {
                        'type': 'text',
                        'prompt': 'Font family for body text',
                        'example': 'system-ui, -apple-system, sans-serif',
                        'required': True
                    },
                    'code_font': {
                        'type': 'text',
                        'prompt': 'Font family for code blocks',
                        'example': 'Monaco, Courier New, monospace',
                        'required': False
                    }
                }
            },
            {
                'title': 'Imagery Guidelines',
                'fields': {
                    'image_style': {
                        'type': 'select',
                        'prompt': 'What style of images fits the brand?',
                        'options': ['Minimalist', 'Technical diagrams', 'Photography', 'Illustrations'],
                        'required': True
                    },
                    'avoid_imagery': {
                        'type': 'list',
                        'prompt': 'What types of images should be avoided?',
                        'example': ['Stock photos', 'Clipart', 'Generic business imagery'],
                        'required': False
                    }
                }
            }
        ]
    },

    'api_integration': {
        'name': 'API Integration SOP',
        'description': 'API design, authentication, and usage guidelines',
        'version': '1.0',
        'sections': [
            {
                'title': 'API Design Principles',
                'fields': {
                    'api_style': {
                        'type': 'select',
                        'prompt': 'What API architecture to use?',
                        'options': ['REST', 'GraphQL', 'gRPC', 'WebSocket'],
                        'required': True
                    },
                    'versioning_strategy': {
                        'type': 'select',
                        'prompt': 'How should API versions be handled?',
                        'options': ['URL path (/v1/)', 'Header (Accept-Version)', 'Query param (?v=1)'],
                        'required': True
                    }
                }
            },
            {
                'title': 'Authentication',
                'fields': {
                    'auth_method': {
                        'type': 'select',
                        'prompt': 'What authentication method to use?',
                        'options': ['API Keys', 'JWT', 'OAuth 2.0', 'Session-based'],
                        'required': True
                    },
                    'rate_limits': {
                        'type': 'object',
                        'prompt': 'Define rate limits for API endpoints',
                        'structure': {
                            'free_tier': '100 requests/hour',
                            'paid_tier': '10000 requests/hour'
                        },
                        'required': True
                    }
                }
            },
            {
                'title': 'Documentation Standards',
                'fields': {
                    'doc_format': {
                        'type': 'select',
                        'prompt': 'What format for API documentation?',
                        'options': ['OpenAPI/Swagger', 'Markdown', 'Interactive playground'],
                        'required': True
                    },
                    'example_requests': {
                        'type': 'boolean',
                        'prompt': 'Include code examples in multiple languages?',
                        'required': True
                    }
                }
            }
        ]
    },

    'deployment': {
        'name': 'Deployment SOP',
        'description': 'Hosting, infrastructure, and launch procedures',
        'version': '1.0',
        'sections': [
            {
                'title': 'Infrastructure',
                'fields': {
                    'hosting_platform': {
                        'type': 'select',
                        'prompt': 'Where will this be hosted?',
                        'options': ['Self-hosted (VPS)', 'Docker', 'Kubernetes', 'Serverless', 'PaaS (Heroku/Vercel)'],
                        'required': True
                    },
                    'domain_strategy': {
                        'type': 'object',
                        'prompt': 'Define domain structure',
                        'structure': {
                            'primary': 'example.com',
                            'api': 'api.example.com',
                            'docs': 'docs.example.com'
                        },
                        'required': True
                    }
                }
            },
            {
                'title': 'Environment Configuration',
                'fields': {
                    'required_env_vars': {
                        'type': 'list',
                        'prompt': 'What environment variables are required?',
                        'example': ['DATABASE_URL', 'API_SECRET_KEY', 'OLLAMA_HOST'],
                        'required': True
                    },
                    'config_management': {
                        'type': 'select',
                        'prompt': 'How to manage configuration?',
                        'options': ['.env files', 'Config service', 'Environment variables', 'YAML files'],
                        'required': True
                    }
                }
            },
            {
                'title': 'Launch Checklist',
                'fields': {
                    'pre_launch_steps': {
                        'type': 'list',
                        'prompt': 'What must be done before launch?',
                        'example': ['Database migrations', 'SSL certificate', 'DNS records', 'Monitoring setup'],
                        'required': True
                    },
                    'rollback_plan': {
                        'type': 'text',
                        'prompt': 'What to do if deployment fails?',
                        'example': 'Revert to previous Docker image, restore database backup',
                        'required': True
                    }
                }
            }
        ]
    }
}


class SOPTemplateLibrary:
    """Manage SOP templates for brands"""

    def __init__(self):
        """Initialize template library"""
        self.templates = SOP_TEMPLATES

    def list_templates(self) -> List[Dict[str, str]]:
        """
        Get list of available templates

        Returns:
            List of template metadata (name, description)
        """
        return [
            {
                'id': template_id,
                'name': template['name'],
                'description': template['description'],
                'version': template['version']
            }
            for template_id, template in self.templates.items()
        ]

    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Get template by ID

        Args:
            template_id: Template identifier (e.g., 'brand_identity')

        Returns:
            Template definition or None if not found
        """
        return self.templates.get(template_id)

    def generate_empty_sop(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Generate empty SOP structure from template

        Args:
            template_id: Template identifier

        Returns:
            Empty SOP with metadata and sections
        """
        template = self.get_template(template_id)
        if not template:
            return None

        sop = {
            'template_id': template_id,
            'template_name': template['name'],
            'template_version': template['version'],
            'created_at': datetime.now().isoformat(),
            'status': 'draft',
            'sections': []
        }

        for section in template['sections']:
            sop_section = {
                'title': section['title'],
                'fields': {}
            }

            for field_name, field_config in section['fields'].items():
                sop_section['fields'][field_name] = {
                    'type': field_config['type'],
                    'value': None,
                    'filled': False,
                    'prompt': field_config['prompt']
                }

            sop['sections'].append(sop_section)

        return sop

    def fill_field(self, sop: Dict[str, Any], section_index: int, field_name: str, value: Any) -> Dict[str, Any]:
        """
        Fill a field in an SOP

        Args:
            sop: SOP dictionary
            section_index: Index of section
            field_name: Name of field to fill
            value: Value to set

        Returns:
            Updated SOP
        """
        if section_index < len(sop['sections']):
            section = sop['sections'][section_index]
            if field_name in section['fields']:
                section['fields'][field_name]['value'] = value
                section['fields'][field_name]['filled'] = True

        return sop

    def is_complete(self, sop: Dict[str, Any]) -> bool:
        """
        Check if all required fields are filled

        Args:
            sop: SOP dictionary

        Returns:
            True if complete, False otherwise
        """
        template = self.get_template(sop['template_id'])
        if not template:
            return False

        for section_idx, section in enumerate(template['sections']):
            for field_name, field_config in section['fields'].items():
                if field_config.get('required', False):
                    sop_field = sop['sections'][section_idx]['fields'].get(field_name, {})
                    if not sop_field.get('filled', False):
                        return False

        return True

    def export_as_yaml(self, sop: Dict[str, Any]) -> str:
        """
        Export SOP as YAML

        Args:
            sop: SOP dictionary

        Returns:
            YAML string
        """
        # Extract just the values for clean YAML
        clean_sop = {
            'template': sop['template_name'],
            'version': sop['template_version'],
            'created': sop['created_at'],
            'status': sop['status'],
            'sections': []
        }

        for section in sop['sections']:
            clean_section = {
                'title': section['title'],
                'data': {}
            }
            for field_name, field_data in section['fields'].items():
                if field_data['filled']:
                    clean_section['data'][field_name] = field_data['value']

            clean_sop['sections'].append(clean_section)

        return yaml.dump(clean_sop, default_flow_style=False, allow_unicode=True)

    def export_as_markdown(self, sop: Dict[str, Any]) -> str:
        """
        Export SOP as Markdown

        Args:
            sop: SOP dictionary

        Returns:
            Markdown string
        """
        md = f"# {sop['template_name']}\n\n"
        md += f"**Version:** {sop['template_version']}  \n"
        md += f"**Created:** {sop['created_at']}  \n"
        md += f"**Status:** {sop['status']}  \n\n"
        md += "---\n\n"

        for section in sop['sections']:
            md += f"## {section['title']}\n\n"

            for field_name, field_data in section['fields'].items():
                if field_data['filled']:
                    value = field_data['value']
                    md += f"### {field_name.replace('_', ' ').title()}\n\n"

                    if isinstance(value, list):
                        for item in value:
                            md += f"- {item}\n"
                        md += "\n"
                    elif isinstance(value, dict):
                        md += "```yaml\n"
                        md += yaml.dump(value, default_flow_style=False)
                        md += "```\n\n"
                    else:
                        md += f"{value}\n\n"

        return md


if __name__ == '__main__':
    # Demo the SOP template system
    print("📋 Brand SOP Template System")
    print("=" * 70)

    library = SOPTemplateLibrary()

    # List templates
    print("\n📚 Available Templates:")
    for template in library.list_templates():
        print(f"  - {template['name']}: {template['description']}")

    # Generate empty SOP
    print("\n📝 Generating Brand Identity SOP...")
    sop = library.generate_empty_sop('brand_identity')

    # Fill some fields
    sop = library.fill_field(sop, 0, 'mission', 'To empower developers with privacy-first tools')
    sop = library.fill_field(sop, 0, 'target_audience', 'Privacy-conscious developers')
    sop = library.fill_field(sop, 1, 'core_values', ['Privacy First', 'Developer Experience', 'Open Source'])

    # Export as Markdown
    print("\n📄 Exported as Markdown:")
    print(library.export_as_markdown(sop))

    print("\n✅ SOP Template System Ready!")
