#!/usr/bin/env python3
"""
Seed SOUL Marketplace with example workflows

This creates the "Voice to Blog" workflow that we just built with Cal
"""

from database import get_db
import json
from datetime import datetime

def seed_workflows():
    db = get_db()

    # Get Cal's user_id
    cal_user = db.execute("SELECT id FROM users WHERE username = 'cal'").fetchone()
    if not cal_user:
        print("❌ Cal user not found. Creating Cal user...")
        db.execute("""
            INSERT INTO users (username, email, password_hash)
            VALUES ('cal', 'cal@soulfra.com', 'no_password_ai_user')
        """)
        db.commit()
        cal_user = db.execute("SELECT id FROM users WHERE username = 'cal'").fetchone()

    cal_user_id = cal_user['id']

    # Workflow 1: Voice → Cal → Blog (Calriven)
    workflow_1 = {
        "workflow_name": "Voice to Blog on Calriven",
        "workflow_slug": "voice-to-blog-calriven",
        "description": "Talk into your phone, Cal writes a blog post, auto-publishes to Calriven. The workflow that started it all.",
        "workflow_type": "voice_to_blog",
        "workflow_config": {
            "steps": [
                {
                    "action": "capture_voice",
                    "description": "Record voice via mobile interface",
                    "endpoint": "/cal/mobile",
                    "config": {}
                },
                {
                    "action": "transcribe",
                    "description": "Convert speech to text",
                    "service": "whisper",
                    "config": {"model": "whisper-1"}
                },
                {
                    "action": "send_to_cal",
                    "description": "Cal generates blog post",
                    "endpoint": "http://192.168.1.87:11434/api/generate",
                    "config": {
                        "model": "calos-model",
                        "prompt_template": "You are Cal, an AI writing assistant. Convert this voice memo into a blog post.\n\nVoice memo:\n{transcript}\n\nWrite a complete blog post with:\n1. A catchy title\n2. Introduction\n3. Main content (3-5 paragraphs)\n4. Conclusion\n\nFormat in Markdown. Start with # Title."
                    }
                },
                {
                    "action": "save_to_database",
                    "description": "Save post to database",
                    "table": "posts",
                    "config": {
                        "brand_id": 3,
                        "user_id": cal_user_id
                    }
                },
                {
                    "action": "export_static",
                    "description": "Generate static HTML",
                    "command": "python3 export_static.py --brand calriven",
                    "config": {}
                },
                {
                    "action": "git_push",
                    "description": "Deploy to GitHub Pages",
                    "repo": "~/Desktop/calriven",
                    "config": {
                        "commit_message": "📝 {title}\n\n🤖 Generated with Cal\nCo-Authored-By: Cal <cal@soulfra.com>"
                    }
                }
            ],
            "avatar_effects": {
                "hair_color": "#667eea",
                "mouse_effect": "typing_sparkles",
                "meme_style": "technical_vibes",
                "vibe": "focused_creator"
            }
        },
        "mood_tags": ["focused", "creative", "productive"],
        "avatar_effects": {
            "hair_color": "#667eea",
            "mouse_effect": "typing_sparkles",
            "meme_style": "technical_vibes"
        },
        "price_tokens": 0
    }

    # Workflow 2: Voice to Art Generation
    workflow_2 = {
        "workflow_name": "Voice to AI Art",
        "workflow_slug": "voice-to-art",
        "description": "Describe a scene, get AI-generated artwork. Uses Stable Diffusion via Cal.",
        "workflow_type": "voice_to_art",
        "workflow_config": {
            "steps": [
                {
                    "action": "capture_voice",
                    "endpoint": "/cal/mobile"
                },
                {
                    "action": "transcribe",
                    "service": "whisper"
                },
                {
                    "action": "generate_image_prompt",
                    "service": "cal",
                    "config": {
                        "prompt_template": "Convert this description into a detailed Stable Diffusion prompt:\n\n{transcript}"
                    }
                },
                {
                    "action": "generate_image",
                    "service": "stable_diffusion",
                    "endpoint": "http://192.168.1.87:7860/api/txt2img"
                },
                {
                    "action": "save_to_gallery",
                    "table": "generated_images"
                }
            ],
            "avatar_effects": {
                "hair_color": "#FF69B4",
                "mouse_effect": "paint_brush",
                "meme_style": "artistic_chaos"
            }
        },
        "mood_tags": ["creative", "playful", "imaginative"],
        "avatar_effects": {
            "hair_color": "#FF69B4",
            "mouse_effect": "paint_brush",
            "meme_style": "artistic_chaos"
        },
        "price_tokens": 5
    }

    # Workflow 3: Morning Motivation
    workflow_3 = {
        "workflow_name": "Morning Motivation Mode",
        "workflow_slug": "morning-motivation",
        "description": "Start your day right. Voice journal → Cal gives motivational response → Sets energetic vibe.",
        "workflow_type": "voice_to_motivation",
        "workflow_config": {
            "steps": [
                {
                    "action": "capture_voice",
                    "endpoint": "/cal/mobile"
                },
                {
                    "action": "transcribe"
                },
                {
                    "action": "motivational_response",
                    "service": "cal",
                    "config": {
                        "model": "calos-model",
                        "prompt_template": "You're a motivational coach. The user said: {transcript}\n\nRespond with:\n1. Acknowledgment of their feelings\n2. One actionable tip\n3. An encouraging closing line"
                    }
                },
                {
                    "action": "save_journal_entry",
                    "table": "voice_journal"
                }
            ],
            "avatar_effects": {
                "hair_color": "#06FFA5",
                "mouse_effect": "sun_rays",
                "meme_style": "wholesome_energy"
            }
        },
        "mood_tags": ["energetic", "motivated", "positive"],
        "avatar_effects": {
            "hair_color": "#06FFA5",
            "mouse_effect": "sun_rays",
            "meme_style": "wholesome_energy"
        },
        "price_tokens": 0
    }

    workflows = [workflow_1, workflow_2, workflow_3]

    for wf in workflows:
        # Check if already exists
        existing = db.execute(
            "SELECT id FROM soul_workflows WHERE workflow_slug = ?",
            (wf['workflow_slug'],)
        ).fetchone()

        if existing:
            print(f"⏭️  Workflow '{wf['workflow_name']}' already exists")
            continue

        # Insert workflow
        cursor = db.execute('''
            INSERT INTO soul_workflows (
                creator_user_id, workflow_name, workflow_slug, description,
                workflow_type, workflow_config, mood_tags, avatar_effects, price_tokens
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            cal_user_id,
            wf['workflow_name'],
            wf['workflow_slug'],
            wf['description'],
            wf['workflow_type'],
            json.dumps(wf['workflow_config']),
            json.dumps(wf['mood_tags']),
            json.dumps(wf['avatar_effects']),
            wf['price_tokens']
        ))

        workflow_id = cursor.lastrowid
        print(f"✅ Created workflow: {wf['workflow_name']} (ID: {workflow_id})")

    db.commit()
    db.close()

    print("\n🎉 SOUL Marketplace seeded with 3 workflows!")
    print("\nTo link a workflow to your account:")
    print("  POST /api/soul/link")
    print("  {'workflow_id': 1, 'mood': 'focused', 'make_active': true}")
    print("\nTo execute your active workflow:")
    print("  POST /api/soul/execute")
    print("  {'input_data': {'transcript': 'Your voice memo...'}}")


if __name__ == '__main__':
    seed_workflows()
