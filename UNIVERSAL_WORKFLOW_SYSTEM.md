# Universal Workflow System

**One system for ALL your industries** - Comics, Sales, Transcription, Music, Video, whatever.

## The Problem You Had

Every industry has different workflows:
- **Comics**: Wireframe → Pencils → Inks → Colors → Letters → Publish
- **StPetePros Sales**: Scrape → Score → Contact → Demo → Close
- **CringeProof**: Scrape News → Record → Pair → Time-lock → Publish
- **Transcription**: Upload → Transcribe → Edit → Review → Deliver
- **Music**: Compose → Record → Mix → Master → Release

You were building separate systems for each. That's insane.

## The Solution: Universal Pipeline

**Same pattern everywhere:**
1. Pick a **workflow template** (comics, sales, whatever)
2. Create a **pipeline** (specific project/deal/track)
3. Move through **stages** (each industry has different stages)
4. Export to **CSV/JSON** for Notion/Airtable

## What We Built

### 1. Database Tables

```sql
-- Templates define the workflow
workflow_templates (
    slug, name, industry,
    stages,  -- JSON: ["Wireframe", "Pencils", "Inks", ...]
    stage_config  -- JSON: Time estimates, required fields, etc.
)

-- Pipelines are instances of workflows
project_pipelines (
    title, workflow_template_id, current_stage,
    stage_data,  -- JSON: Data collected at each stage
    status, priority
)

-- Activity log for audit trail
pipeline_activity (pipeline_id, stage_index, action, metadata)

-- Files attached at any stage
pipeline_attachments (pipeline_id, stage_index, file_path, file_type)
```

### 2. Pre-Built Workflow Templates

Run the migration to get these **6 templates**:

```bash
python3 migrate_workflow_system.py
```

**Templates created:**
1. **comics-production** - Wireframe → Pencils → Inks → Colors → Letters → Publish
2. **stpetepros-sales** - Scraped Lead → Scored → Contacted → Demo → Proposal → Closed
3. **cringeproof-predictions** - News Scraped → Voice Recorded → Paired → Time-Locked → Published
4. **transcription-service** - Upload → Transcribe → Edit/QA → Client Review → Delivered
5. **music-production** - Composition → Recording → Mixing → Mastering → Distribution
6. **video-production** - Script → Filming → Editing → Color → Audio → Publish

### 3. API Routes

**View all templates:**
```
GET /workflows
```

**View specific workflow:**
```
GET /workflows/comics-production
GET /workflows/stpetepros-sales
```

**Kanban dashboard (all active pipelines):**
```
GET /pipelines
```

**Create new pipeline:**
```
POST /pipelines/create
{
  "template_id": 1,
  "title": "New Comic: Superhero Story #1"
}
```

**View pipeline details:**
```
GET /pipelines/1
```

**Advance to next stage:**
```
POST /pipelines/1/advance
```

**Update stage data:**
```
POST /pipelines/1/update
{
  "stage_index": 2,
  "field": "notes",
  "value": "Finished inking page 5"
}
```

**Export to CSV:**
```
GET /pipelines/export.csv?industry=comics&status=active
```

**Export to JSON:**
```
GET /pipelines/export.json
```

## Usage Examples

### Example 1: Comic Production

```python
import requests

# Create a new comic pipeline
r = requests.post('http://localhost:5001/pipelines/create', data={
    'template_id': 1,  # comics-production template
    'title': 'Issue #42: The Final Battle'
})
pipeline_id = r.json()['pipeline_id']

# Update wireframe stage
requests.post(f'http://localhost:5001/pipelines/{pipeline_id}/update', json={
    'stage_index': 0,
    'field': 'sketch_file',
    'value': '/uploads/issue42-wireframe.jpg'
})

# Advance to pencils stage
requests.post(f'http://localhost:5001/pipelines/{pipeline_id}/advance')

# Export all comic pipelines to CSV
csv = requests.get('http://localhost:5001/pipelines/export.csv?industry=comics')
open('comics.csv', 'wb').write(csv.content)
```

### Example 2: StPetePros Sales

```bash
# Scrape leads (already done with stpetepros_scraper.py)
python3 stpetepros_scraper.py --category plumbing

# Now convert scraped prospects to sales pipelines
python3 -c "
import sqlite3, requests

db = sqlite3.connect('soulfra.db')
prospects = db.execute('SELECT * FROM scraped_prospects WHERE score >= 70 LIMIT 10').fetchall()

for p in prospects:
    r = requests.post('http://localhost:5001/pipelines/create', data={
        'template_id': 2,  # stpetepros-sales
        'title': p['business_name']
    })
    print(f\"Created pipeline {r.json()['pipeline_id']} for {p['business_name']}\")
"

# View all sales pipelines
curl http://localhost:5001/workflows/stpetepros-sales

# Export to CSV for sales team
curl http://localhost:5001/pipelines/export.csv?industry=sales > sales_pipeline.csv
```

### Example 3: Transcription Service

```python
# Customer uploads audio file → creates pipeline automatically
requests.post('http://localhost:5001/pipelines/create', data={
    'template_id': 4,  # transcription-service
    'title': 'Client: Acme Corp - Interview Recording'
})

# Auto-transcribe (stage 1) happens via Whisper API
# Editor reviews (stage 2)
# Client approves (stage 3)
# Mark as delivered (advance to final stage)
```

## Cross-Brand Workflows

**This works across ALL your brands:**

- **StPetePros** professional can hire a **CringeProof** freelancer
- **Soulfra** course can use **StPetePros** marketing agency
- **CringeProof** predictions can embed **Soulfra** courses

All tracked in the same pipeline system!

## No External APIs Needed

- ✅ Works 100% locally with SQLite
- ✅ Export to CSV/JSON for Notion/Airtable
- ✅ No Google Places API, no Airtable API required
- ✅ Free forever

## Next Steps

1. **Register routes in app.py:**
   ```python
   from universal_workflow_routes import register_universal_workflow_routes
   register_universal_workflow_routes(app)
   ```

2. **Create a pipeline:**
   ```bash
   curl -X POST http://localhost:5001/pipelines/create \
     -d 'template_id=1&title=My First Comic'
   ```

3. **View Kanban dashboard:**
   ```
   http://localhost:5001/pipelines
   ```

4. **Export to CSV and open in Google Sheets/Excel:**
   ```bash
   curl http://localhost:5001/pipelines/export.csv > my_pipelines.csv
   open my_pipelines.csv
   ```

## Comparison to Old Way

**Before:**
- StPetePros scraper → scraped_prospects table → sales dashboard (only works for sales)
- CringeProof news → news_articles table → custom pairing logic (only works for predictions)
- Comics → ??? (no system at all)

**Now:**
- Universal workflow templates
- All industries use same pipeline system
- Easy CSV export to any tool you want
- Cross-brand collaboration built-in

---

**Built 2026-01-04**
You can now run ANY industry workflow through the same system.
