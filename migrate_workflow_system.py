#!/usr/bin/env python3
"""
Universal Workflow System Migration
Creates tables for industry-specific workflows that all work the same way
"""

import sqlite3

def migrate():
    db = sqlite3.connect('soulfra.db')
    cursor = db.cursor()

    # 1. Workflow Templates - Define industry-specific pipelines
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS workflow_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            industry TEXT,  -- 'comics', 'sales', 'transcription', 'music', 'video', etc.
            stages TEXT NOT NULL,  -- JSON array: ["wireframe", "pencils", "inks", "colors", "publish"]
            stage_config TEXT,  -- JSON: Per-stage configs (time estimates, required fields, etc.)
            is_system_template BOOLEAN DEFAULT 0,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    ''')

    # 2. Project Pipelines - Instances of workflows
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS project_pipelines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            workflow_template_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            current_stage INTEGER DEFAULT 0,  -- Index in stages array
            stage_data TEXT,  -- JSON: Data collected at each stage
            status TEXT DEFAULT 'active',  -- 'active', 'paused', 'completed', 'cancelled'
            priority INTEGER DEFAULT 0,  -- Higher = more urgent
            assigned_to INTEGER,  -- User responsible
            due_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id),
            FOREIGN KEY (workflow_template_id) REFERENCES workflow_templates(id),
            FOREIGN KEY (assigned_to) REFERENCES users(id)
        )
    ''')

    # 3. Pipeline Activity Log
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pipeline_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pipeline_id INTEGER NOT NULL,
            stage_index INTEGER NOT NULL,
            action TEXT NOT NULL,  -- 'started', 'completed', 'note_added', 'file_uploaded'
            actor_id INTEGER,
            metadata TEXT,  -- JSON: Additional context
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pipeline_id) REFERENCES project_pipelines(id),
            FOREIGN KEY (actor_id) REFERENCES users(id)
        )
    ''')

    # 4. Pipeline Attachments - Files at any stage
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pipeline_attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pipeline_id INTEGER NOT NULL,
            stage_index INTEGER NOT NULL,
            file_type TEXT,  -- 'image', 'audio', 'video', 'document', 'link'
            file_path TEXT,
            file_url TEXT,
            thumbnail_path TEXT,
            filename TEXT,
            filesize INTEGER,
            metadata TEXT,  -- JSON
            uploaded_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pipeline_id) REFERENCES project_pipelines(id),
            FOREIGN KEY (uploaded_by) REFERENCES users(id)
        )
    ''')

    db.commit()

    # Insert system workflow templates
    templates = [
        {
            'slug': 'comics-production',
            'name': 'Comics Production Pipeline',
            'description': 'Standard comic book production workflow',
            'industry': 'comics',
            'stages': '["Wireframe/Sketch", "Pencils", "Inks", "Colors", "Letters", "Publish"]',
            'stage_config': '''{
                "Wireframe/Sketch": {"time_estimate_hours": 8, "deliverable": "sketch files"},
                "Pencils": {"time_estimate_hours": 16, "deliverable": "pencil drawings"},
                "Inks": {"time_estimate_hours": 12, "deliverable": "inked pages"},
                "Colors": {"time_estimate_hours": 10, "deliverable": "colored pages"},
                "Letters": {"time_estimate_hours": 4, "deliverable": "lettered pages"},
                "Publish": {"time_estimate_hours": 2, "deliverable": "final files"}
            }''',
            'is_system_template': 1
        },
        {
            'slug': 'stpetepros-sales',
            'name': 'StPetePros Sales Pipeline',
            'description': 'Door-to-door sales workflow for local professionals',
            'industry': 'sales',
            'stages': '["Scraped Lead", "Scored/Routed", "Contacted", "Demo Scheduled", "Proposal Sent", "Closed"]',
            'stage_config': '''{
                "Scraped Lead": {"auto": true, "source": "Google Places or manual"},
                "Scored/Routed": {"auto": true, "scoring": "review_count + no_website bonus"},
                "Contacted": {"required_fields": ["contact_method", "contact_date", "notes"]},
                "Demo Scheduled": {"required_fields": ["demo_date", "demo_type"]},
                "Proposal Sent": {"required_fields": ["proposal_amount", "proposal_date"]},
                "Closed": {"required_fields": ["close_date", "deal_value", "payment_terms"]}
            }''',
            'is_system_template': 1
        },
        {
            'slug': 'cringeproof-predictions',
            'name': 'CringeProof Prediction Workflow',
            'description': 'Time-locked prediction system for news reactions',
            'industry': 'media',
            'stages': '["News Scraped", "Voice Recorded", "Prediction Paired", "Time-Locked", "Unlocked/Scored", "Published"]',
            'stage_config': '''{
                "News Scraped": {"auto": true, "source": "Google News RSS"},
                "Voice Recorded": {"required_fields": ["recording_id", "transcript"]},
                "Prediction Paired": {"required_fields": ["article_id", "prediction_text"]},
                "Time-Locked": {"time_lock_days": 90, "hash_published": true},
                "Unlocked/Scored": {"auto": true, "trigger": "time_lock_expired"},
                "Published": {"auto": true, "destination": "GitHub Pages"}
            }''',
            'is_system_template': 1
        },
        {
            'slug': 'transcription-service',
            'name': 'Transcription Service Pipeline',
            'description': 'Audio/video transcription workflow',
            'industry': 'transcription',
            'stages': '["Upload", "Transcribe", "Edit/QA", "Client Review", "Delivered"]',
            'stage_config': '''{
                "Upload": {"required_fields": ["file_path", "client_id", "deadline"]},
                "Transcribe": {"auto": true, "service": "Whisper API"},
                "Edit/QA": {"required_fields": ["editor_id", "qa_notes"]},
                "Client Review": {"required_fields": ["sent_to_client_date"]},
                "Delivered": {"required_fields": ["delivery_date", "client_approval"]}
            }''',
            'is_system_template': 1
        },
        {
            'slug': 'music-production',
            'name': 'Music Production Pipeline',
            'description': 'Track from composition to release',
            'industry': 'music',
            'stages': '["Composition", "Recording", "Mixing", "Mastering", "Distribution"]',
            'stage_config': '''{
                "Composition": {"deliverable": "sheet music / MIDI"},
                "Recording": {"deliverable": "raw tracks"},
                "Mixing": {"deliverable": "mixed stereo file"},
                "Mastering": {"deliverable": "mastered final"},
                "Distribution": {"platforms": ["Spotify", "Apple Music", "Bandcamp"]}
            }''',
            'is_system_template': 1
        },
        {
            'slug': 'video-production',
            'name': 'Video Production Pipeline',
            'description': 'Video from concept to publish',
            'industry': 'video',
            'stages': '["Script", "Filming", "Editing", "Color Grade", "Audio Mix", "Publish"]',
            'stage_config': '''{
                "Script": {"deliverable": "final script"},
                "Filming": {"deliverable": "raw footage"},
                "Editing": {"deliverable": "rough cut"},
                "Color Grade": {"deliverable": "color-corrected video"},
                "Audio Mix": {"deliverable": "final audio"},
                "Publish": {"platforms": ["YouTube", "Vimeo", "social"]}
            }''',
            'is_system_template': 1
        }
    ]

    for template in templates:
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO workflow_templates
                (slug, name, description, industry, stages, stage_config, is_system_template)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                template['slug'],
                template['name'],
                template['description'],
                template['industry'],
                template['stages'],
                template['stage_config'],
                template['is_system_template']
            ))
        except Exception as e:
            print(f"Error inserting template {template['slug']}: {e}")

    db.commit()
    db.close()

    print("✅ Workflow system migration complete!")
    print("   Created tables:")
    print("   - workflow_templates (6 presets)")
    print("   - project_pipelines")
    print("   - pipeline_activity")
    print("   - pipeline_attachments")


if __name__ == '__main__':
    migrate()
