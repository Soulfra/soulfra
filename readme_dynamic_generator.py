#!/usr/bin/env python3
"""
Dynamic README Generator - GitHub as Content Distribution System

Generates personalized README files based on:
- Industry (comics, sales, transcription, etc.)
- Reader source (which competitor referred them)
- Trending workflows
- Time of day

Usage:
    python3 readme_dynamic_generator.py --industry comics
    python3 readme_dynamic_generator.py --trending
    python3 readme_dynamic_generator.py --all
"""

import sqlite3
import json
import argparse
from datetime import datetime
from typing import Dict, List

# Cross-promotion mapping: Which service to promote for each industry
PROMOTION_MAP = {
    'comics': {
        'service': 'CringeProof Freelancer Marketplace',
        'url': 'https://cringeproof.com/freelancers',
        'pitch': 'Need artists for your comic? Hire vetted freelancers on CringeProof',
        'badge': 'https://img.shields.io/badge/🎨_Hire_Comic_Artists-FF006E?style=for-the-badge'
    },
    'sales': {
        'service': 'StPetePros CRM',
        'url': 'https://stpetepros.com/signup/professional',
        'pitch': 'Get more local customers with StPetePros professional directory',
        'badge': 'https://img.shields.io/badge/📈_Get_More_Leads-10B981?style=for-the-badge'
    },
    'transcription': {
        'service': 'Soulfra Transcription API',
        'url': 'https://soulfra.com/api/transcription',
        'pitch': 'Auto-transcribe with Whisper API integration via Soulfra',
        'badge': 'https://img.shields.io/badge/🎙️_Auto_Transcribe-0EA5E9?style=for-the-badge'
    },
    'music': {
        'service': 'Soulfra Distribution',
        'url': 'https://soulfra.com/distribution',
        'pitch': 'Distribute your music to Spotify, Apple Music, and more',
        'badge': 'https://img.shields.io/badge/🎵_Distribute_Music-8B5CF6?style=for-the-badge'
    },
    'video': {
        'service': 'CringeProof Video Hosting',
        'url': 'https://cringeproof.com/video',
        'pitch': 'Host videos with community engagement and time-locked predictions',
        'badge': 'https://img.shields.io/badge/📹_Host_Videos-F59E0B?style=for-the-badge'
    },
    'media': {
        'service': 'CringeProof Predictions',
        'url': 'https://cringeproof.com',
        'pitch': 'Make time-locked predictions on news and get CringeProof score',
        'badge': 'https://img.shields.io/badge/🔮_Make_Predictions-EF4444?style=for-the-badge'
    }
}


def get_workflow_template(industry: str) -> Dict:
    """Get workflow template from database"""
    db = sqlite3.connect('soulfra.db')
    db.row_factory = sqlite3.Row

    template = db.execute('''
        SELECT * FROM workflow_templates WHERE industry = ?
    ''', (industry,)).fetchone()

    db.close()

    if not template:
        return None

    return {
        'name': template['name'],
        'description': template['description'],
        'stages': json.loads(template['stages']),
        'stage_config': json.loads(template['stage_config']) if template['stage_config'] else {}
    }


def generate_workflow_section(industry: str, template: Dict) -> str:
    """Generate markdown section for a workflow"""

    stages = template['stages']
    stage_config = template['stage_config']

    # Tracking badge (shields.io = free analytics)
    tracking_badge = f"![Workflow Views](https://img.shields.io/badge/dynamic/json?url=https://soulfra.com/api/workflow-stats?industry={industry}&label=views&query=$.views&color=blue)"

    md = f"""
## {template['name']}

{template['description']}

{tracking_badge}

### Pipeline Stages

"""

    # Generate stage list with time estimates
    for i, stage in enumerate(stages, 1):
        config = stage_config.get(stage, {})
        time_est = config.get('time_estimate_hours', '?')
        deliverable = config.get('deliverable', 'N/A')

        md += f"{i}. **{stage}**"
        if time_est != '?':
            md += f" (~{time_est}h)"
        if deliverable != 'N/A':
            md += f" → Deliverable: *{deliverable}*"
        md += "\n"

    return md


def generate_promotion_section(industry: str) -> str:
    """Generate cross-promotion for relevant service"""

    promo = PROMOTION_MAP.get(industry)
    if not promo:
        # Default promo
        promo = {
            'service': 'Soulfra Platform',
            'url': 'https://soulfra.com',
            'pitch': 'Build custom workflows for any industry on Soulfra',
            'badge': 'https://img.shields.io/badge/🚀_Try_Soulfra-6366F1?style=for-the-badge'
        }

    return f"""
---

### ✨ {promo['pitch']}

<div align="center">
  <a href="{promo['url']}?ref=github-readme-{industry}">
    <img src="{promo['badge']}" alt="{promo['service']}">
  </a>
</div>

"""


def generate_trending_section() -> str:
    """Show most active workflows (tracked via pipeline_activity)"""

    db = sqlite3.connect('soulfra.db')
    db.row_factory = sqlite3.Row

    # Get workflow activity in last 7 days
    trending = db.execute('''
        SELECT
            t.industry,
            t.name,
            COUNT(pa.id) as activity_count
        FROM pipeline_activity pa
        JOIN project_pipelines pp ON pa.pipeline_id = pp.id
        JOIN workflow_templates t ON pp.workflow_template_id = t.id
        WHERE pa.created_at >= datetime('now', '-7 days')
        GROUP BY t.id
        ORDER BY activity_count DESC
        LIMIT 5
    ''').fetchall()

    db.close()

    if not trending:
        return ""

    md = """
## 🔥 Trending Workflows This Week

"""

    for i, row in enumerate(trending, 1):
        badge_color = ['FF006E', '10B981', '0EA5E9', 'F59E0B', '8B5CF6'][i-1]
        md += f"{i}. **{row['name']}** ({row['industry']}) - {row['activity_count']} active pipelines\n"
        md += f"   ![Activity](https://img.shields.io/badge/activity-{row['activity_count']}_pipelines-{badge_color})\n\n"

    return md


def generate_readme(industry: str = None, trending: bool = False) -> str:
    """Generate complete README"""

    md = f"""# Universal Workflow Templates

**Free, open-source workflow templates for ANY industry.**

Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}

"""

    if trending:
        md += generate_trending_section()

    if industry:
        # Single industry focus
        template = get_workflow_template(industry)
        if template:
            md += generate_workflow_section(industry, template)
            md += generate_promotion_section(industry)
        else:
            md += f"\n❌ No workflow template found for industry: {industry}\n"

    else:
        # Show all industries
        db = sqlite3.connect('soulfra.db')
        db.row_factory = sqlite3.Row

        templates = db.execute('''
            SELECT * FROM workflow_templates ORDER BY industry
        ''').fetchall()

        db.close()

        md += """
## 📚 Available Workflows

Choose your industry:

"""

        for t in templates:
            stages_count = len(json.loads(t['stages']))
            md += f"- [{t['name']}](#{t['industry']}) - {stages_count} stages\n"

        md += "\n---\n"

        # Generate section for each
        for t in templates:
            template_dict = {
                'name': t['name'],
                'description': t['description'],
                'stages': json.loads(t['stages']),
                'stage_config': json.loads(t['stage_config']) if t['stage_config'] else {}
            }
            md += f"\n<a name=\"{t['industry']}\"></a>\n"
            md += generate_workflow_section(t['industry'], template_dict)
            md += generate_promotion_section(t['industry'])

    # Footer with analytics
    md += """
---

## 📊 GitHub Workflow Stats

![Total Templates](https://img.shields.io/badge/dynamic/json?url=https://soulfra.com/api/workflow-stats&label=total%20templates&query=$.total&color=blue)
![Active Pipelines](https://img.shields.io/badge/dynamic/json?url=https://soulfra.com/api/workflow-stats&label=active%20pipelines&query=$.active&color=green)

## 🚀 Get Started

```bash
# Clone workflow templates
git clone https://github.com/soulfra/workflow-templates

# Run migration
python3 migrate_workflow_system.py

# Create your first pipeline
curl -X POST http://localhost:5001/pipelines/create \\
  -d 'template_id=1&title=My First Project'
```

## 🤝 Contribute

Have a workflow template to share? Open a PR!

---

<div align="center">
  <sub>Built with ❤️ by Soulfra | Free forever | No API keys required</sub>
</div>
"""

    return md


def main():
    parser = argparse.ArgumentParser(description='Generate dynamic README')
    parser.add_argument('--industry', help='Generate for specific industry')
    parser.add_argument('--trending', action='store_true', help='Show trending workflows')
    parser.add_argument('--all', action='store_true', help='Generate full README with all industries')
    parser.add_argument('--output', default='README_WORKFLOWS.md', help='Output file')

    args = parser.parse_args()

    if args.all:
        readme = generate_readme(trending=True)
    elif args.industry:
        readme = generate_readme(industry=args.industry, trending=args.trending)
    elif args.trending:
        readme = generate_readme(trending=True)
    else:
        readme = generate_readme(trending=True)

    # Write to file
    with open(args.output, 'w') as f:
        f.write(readme)

    print(f"✅ Generated {args.output}")
    print(f"   {len(readme)} characters")
    print(f"\n📊 Tracking pixels embedded:")
    print(f"   - Workflow view badges (shields.io)")
    print(f"   - Activity counters")
    print(f"   - Promotion click-throughs (ref= params)")


if __name__ == '__main__':
    main()
