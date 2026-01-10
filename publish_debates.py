#!/usr/bin/env python3
"""
Publish AI Debates to GitHub Pages

Copies debate markdown files to soulfra.github.io/debates/
Creates an index page for browsing all debates
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

# Paths
DEBATES_DIR = Path(__file__).parent / 'debates'
GITHUB_IO_DIR = Path(__file__).parent / 'soulfra.github.io'
DEBATES_TARGET_DIR = GITHUB_IO_DIR / 'debates'

def publish_debates():
    """Copy debate files to GitHub Pages"""

    # Create debates directory if it doesn't exist
    DEBATES_TARGET_DIR.mkdir(parents=True, exist_ok=True)

    # Find all debate markdown files
    debate_files = sorted(DEBATES_DIR.glob('*.md'), reverse=True)

    if not debate_files:
        print("❌ No debate files found in debates/")
        return

    print(f"📁 Found {len(debate_files)} debate files")

    # Copy each debate file
    for debate_file in debate_files:
        target_file = DEBATES_TARGET_DIR / debate_file.name
        shutil.copy2(debate_file, target_file)
        print(f"✅ Copied: {debate_file.name}")

    # Create index.html for debates
    create_debate_index(debate_files)

    print(f"\n✅ Published {len(debate_files)} debates to GitHub Pages")
    print(f"📂 Location: {DEBATES_TARGET_DIR}")
    print(f"\n📤 Next steps:")
    print(f"   cd {GITHUB_IO_DIR}")
    print(f"   git add debates/")
    print(f"   git commit -m 'Add AI debates'")
    print(f"   git push origin main")


def create_debate_index(debate_files):
    """Create index.html for browsing debates"""

    # Parse debate frontmatter
    debates_data = []
    for debate_file in debate_files:
        with open(debate_file, 'r') as f:
            content = f.read()

        # Extract frontmatter
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter = parts[1].strip()
                prediction = None
                date = None
                models = None

                for line in frontmatter.split('\n'):
                    if line.startswith('prediction:'):
                        prediction = line.split(':', 1)[1].strip().strip('"')
                    elif line.startswith('date:'):
                        date = line.split(':', 1)[1].strip()
                    elif line.startswith('models:'):
                        models = line.split(':', 1)[1].strip()

                if prediction:
                    debates_data.append({
                        'file': debate_file.name,
                        'prediction': prediction,
                        'date': date or 'Unknown',
                        'models': models or '0'
                    })

    # Generate HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Debates - Soulfra</title>
  <meta name="description" content="Voice predictions debated by AI models">
  <style>
    * {{
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }}

    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: #ffffff;
      min-height: 100vh;
      padding: 2rem;
    }}

    .container {{
      max-width: 1200px;
      margin: 0 auto;
    }}

    header {{
      text-align: center;
      margin-bottom: 3rem;
    }}

    h1 {{
      font-size: 3rem;
      font-weight: 900;
      margin-bottom: 0.5rem;
    }}

    .subtitle {{
      font-size: 1.25rem;
      opacity: 0.9;
    }}

    .back-link {{
      display: inline-block;
      margin-bottom: 1rem;
      padding: 0.5rem 1rem;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 8px;
      text-decoration: none;
      color: white;
      font-size: 0.875rem;
      transition: all 0.2s ease;
    }}

    .back-link:hover {{
      background: rgba(255, 255, 255, 0.2);
    }}

    .debates-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
      gap: 1.5rem;
    }}

    .debate-card {{
      background: rgba(255, 255, 255, 0.1);
      backdrop-filter: blur(10px);
      border-radius: 12px;
      padding: 1.5rem;
      transition: all 0.3s ease;
      border: 2px solid rgba(255, 255, 255, 0.1);
    }}

    .debate-card:hover {{
      transform: translateY(-4px);
      border-color: rgba(255, 255, 255, 0.3);
      box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3);
    }}

    .debate-prediction {{
      font-size: 1.125rem;
      font-weight: 600;
      margin-bottom: 1rem;
      line-height: 1.4;
    }}

    .debate-meta {{
      display: flex;
      gap: 1rem;
      font-size: 0.875rem;
      opacity: 0.8;
      margin-bottom: 1rem;
    }}

    .debate-link {{
      display: inline-block;
      background: rgba(255, 255, 255, 0.2);
      padding: 0.5rem 1rem;
      border-radius: 6px;
      text-decoration: none;
      color: white;
      font-weight: 600;
      transition: all 0.2s ease;
    }}

    .debate-link:hover {{
      background: rgba(255, 255, 255, 0.3);
    }}

    @media (max-width: 768px) {{
      h1 {{ font-size: 2rem; }}
      .debates-grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <a href="/" class="back-link">← Back to Hub</a>
      <h1>🤖 AI Debates</h1>
      <p class="subtitle">Voice predictions analyzed by multiple AI models</p>
    </header>

    <div class="debates-grid">
"""

    # Add debate cards
    for debate in debates_data:
        date_formatted = debate['date'].split('T')[0] if 'T' in debate['date'] else debate['date']
        html += f"""      <div class="debate-card">
        <div class="debate-prediction">"{debate['prediction']}"</div>
        <div class="debate-meta">
          <span>📅 {date_formatted}</span>
          <span>🤖 {debate['models']} models</span>
        </div>
        <a href="/debates/{debate['file']}" class="debate-link">Read Debate →</a>
      </div>
"""

    html += """    </div>
  </div>
</body>
</html>
"""

    # Write index.html
    index_file = DEBATES_TARGET_DIR / 'index.html'
    with open(index_file, 'w') as f:
        f.write(html)

    print(f"✅ Created: debates/index.html")


if __name__ == '__main__':
    publish_debates()
