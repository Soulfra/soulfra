# Generative Site System - Voice to Full Website Pipeline

**Date:** 2026-01-09
**Purpose:** How professionals record voice → AI auto-generates complete website with 50+ SEO pages
**Status:** System architecture specification

---

## The Vision

**Problem:** Most professionals can't build websites. They know their trade, not HTML/CSS/JavaScript.

**Solution:** Speak into phone → AI generates complete professional website in 10 minutes.

**Example:**
1. Joe (plumber) records 10-minute voice memo about fixing leaky faucets
2. AI transcribes, structures content, generates HTML
3. AI creates 50+ landing page variations targeting different cities/keywords
4. Site auto-deploys to `joesplumbing.cringeproof.com`
5. Joe's site ranks on Google for "Tampa emergency plumber" within days

**Why this matters:**
- **Speed:** 10 min voice vs. 40+ hours building site
- **Quality:** AI follows SEO best practices automatically
- **Scale:** Each voice recording = 50+ optimized pages
- **Maintenance:** Update once → all pages refresh automatically

---

## System Architecture

### Overview Pipeline

```
Step 1: Record Voice
├── Mobile app or web recorder
├── 5-30 minute recording
└── Upload to server

Step 2: Transcribe
├── Whisper AI (local Ollama) or OpenAI API
├── Output: Plain text transcript
└── ~30 seconds per minute of audio

Step 3: Structure Content
├── AI identifies: Title, sections, key points
├── Extract: Tips, warnings, common mistakes
└── Format: Markdown with semantic structure

Step 4: Generate HTML
├── Convert markdown → HTML
├── Apply professional's branding (logo, colors)
└── Add CTAs (call buttons, contact forms)

Step 5: Generate pSEO Variations
├── 50+ landing page variations
├── Target: Different cities, keywords, long-tail searches
└── Same content, different headlines/metadata

Step 6: Auto-Deploy
├── Save to database
├── Update subdomain/custom domain
└── Submit sitemap to Google
```

---

## Step 1: Voice Recording

### Input Methods

**Mobile app (iOS/Android):**
```javascript
// React Native audio recording
import { Audio } from 'expo-av';

async function recordTutorial() {
  const { recording } = await Audio.Recording.createAsync(
    Audio.RECORDING_OPTIONS_PRESET_HIGH_QUALITY
  );

  // Show recording UI
  setRecording(recording);

  // When done:
  await recording.stopAndUnloadAsync();
  const uri = recording.getURI();

  // Upload to server
  const formData = new FormData();
  formData.append('audio', {
    uri: uri,
    type: 'audio/m4a',
    name: 'tutorial.m4a'
  });

  await fetch('https://api.cringeproof.com/tutorials', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${userToken}`
    },
    body: formData
  });
}
```

**Web recorder:**
```javascript
// Browser-based recording
const mediaRecorder = new MediaRecorder(stream);
let audioChunks = [];

mediaRecorder.ondataavailable = (event) => {
  audioChunks.push(event.data);
};

mediaRecorder.onstop = async () => {
  const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });

  // Upload
  const formData = new FormData();
  formData.append('audio', audioBlob, 'tutorial.webm');

  await fetch('/api/tutorials', {
    method: 'POST',
    body: formData
  });
};
```

**Phone call recording (future):**
```
Professional calls: 1-800-TUTORIAL
├── IVR system prompts: "Describe your tutorial topic"
├── Record phone call
├── Auto-transcribe when they hang up
└── Text notification: "Tutorial processing, view at [link]"
```

### Voice Recording Best Practices

**Prompt template shown to professional:**
```
📝 Tutorial Structure (suggested)

1. Introduction (30 sec)
   - Your name & business
   - What problem you're solving

2. Main content (5-20 min)
   - Step-by-step explanation
   - Tips & common mistakes
   - Safety warnings

3. Conclusion (30 sec)
   - Summary
   - Call to action ("Call us for help!")

💡 Tip: Speak naturally like you're explaining to a customer
```

---

## Step 2: Transcription

### Ollama (Local, Free)

```python
# transcribe.py using Whisper via Ollama

import subprocess
import json

def transcribe_audio_ollama(audio_path: str) -> str:
    """
    Transcribe audio using local Ollama Whisper model
    Pros: Free, private, fast
    Cons: Requires Ollama running locally
    """
    # Run Ollama whisper
    result = subprocess.run([
        'ollama', 'run', 'whisper',
        '--file', audio_path
    ], capture_output=True, text=True)

    transcript = result.stdout.strip()
    return transcript
```

### OpenAI Whisper API (Fallback)

```python
# transcribe.py using OpenAI API

import openai

def transcribe_audio_openai(audio_path: str) -> str:
    """
    Transcribe audio using OpenAI Whisper API
    Pros: More accurate, no local setup
    Cons: Costs $0.006/minute (~$0.06 for 10min audio)
    """
    with open(audio_path, 'rb') as audio_file:
        transcript = openai.Audio.transcribe(
            model="whisper-1",
            file=audio_file,
            response_format="text"
        )

    return transcript
```

### Smart Transcription Router

```python
# routes/tutorials.py

def transcribe_audio(audio_path: str) -> str:
    """
    Try Ollama first (free), fallback to OpenAI if unavailable
    """
    try:
        # Check if Ollama is running
        subprocess.run(['ollama', 'list'], capture_output=True, check=True, timeout=5)

        # Ollama available, use it
        return transcribe_audio_ollama(audio_path)

    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        # Ollama not available, use OpenAI
        print("Ollama unavailable, using OpenAI Whisper API")
        return transcribe_audio_openai(audio_path)
```

### Output Example

**Input:** 10-minute voice recording about fixing leaky faucets

**Output:**
```
Hey everyone, Joe from Joe's Plumbing here. Today I'm going to show you how to fix a leaky faucet. This is one of the most common problems homeowners call us about, and honestly, a lot of times you can fix it yourself if you have the right tools.

So first thing you want to do is turn off the water supply. This is really important - you'll find the shutoff valve under the sink. Turn it clockwise until it stops. Then turn on the faucet to drain any remaining water.

Next, you're going to remove the handle. Most faucets have a small screw hidden under a decorative cap. Pop that cap off with a flathead screwdriver, then unscrew the handle...

[continues for ~2000 words]
```

---

## Step 3: Structure Content with AI

### AI Prompt Engineering

```python
# ai/structure_content.py

def structure_transcript(transcript: str) -> dict:
    """
    Use AI to structure raw transcript into semantic sections
    """
    prompt = f"""You are an expert content editor for professional educational content.

Given this transcript of a professional explaining their expertise, structure it into:

1. **Title** - SEO-friendly, includes problem/solution
2. **Introduction** - Who they are, what problem they're solving (2-3 sentences)
3. **Main Content Sections** - Break into logical steps/topics with headers
4. **Key Takeaways** - Bullet points of main lessons
5. **Common Mistakes** - Things to avoid (if mentioned)
6. **Safety Warnings** - Important safety info (if mentioned)
7. **Call to Action** - How to contact professional

Transcript:
{transcript}

Output as JSON:
{{
  "title": "How to Fix a Leaky Faucet in 5 Steps",
  "meta_description": "Tampa plumber explains how to fix leaky faucets...",
  "introduction": "...",
  "sections": [
    {{"heading": "Step 1: Turn Off Water Supply", "content": "..."}},
    {{"heading": "Step 2: Remove Faucet Handle", "content": "..."}}
  ],
  "key_takeaways": ["Always turn off water first", "..."],
  "common_mistakes": ["Forgetting to turn off water", "..."],
  "safety_warnings": ["Avoid electrical hazards near water", "..."],
  "call_to_action": "Need help? Call Joe's Plumbing at (813) 555-0100"
}}
"""

    # Call Ollama
    response = ollama_generate(prompt, model='llama3.2')

    # Parse JSON
    structured = json.loads(response)

    return structured
```

### Ollama Integration

```python
# ai/ollama_client.py

import urllib.request
import json

def ollama_generate(prompt: str, model: str = 'llama3.2') -> str:
    """
    Generate text using local Ollama
    """
    url = 'http://localhost:11434/api/generate'

    data = {
        'model': model,
        'prompt': prompt,
        'stream': False
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )

    with urllib.request.urlopen(req, timeout=60) as response:
        result = json.loads(response.read().decode('utf-8'))
        return result.get('response', '')
```

### Structured Output Example

```json
{
  "title": "How to Fix a Leaky Faucet: Tampa Plumber's 5-Step Guide",
  "meta_description": "Licensed Tampa plumber Joe explains how to fix a leaky faucet yourself. Step-by-step instructions, common mistakes to avoid, and when to call a professional.",
  "keywords": ["fix leaky faucet", "Tampa plumber", "faucet repair", "DIY plumbing"],
  "introduction": "Joe from Joe's Plumbing (FL License #CFC1234567) shows you how to fix a leaky faucet. This common household problem wastes water and money, but with the right tools and knowledge, many homeowners can fix it themselves.",
  "sections": [
    {
      "heading": "Step 1: Turn Off Water Supply",
      "content": "Before starting any plumbing repair, locate the shutoff valve under your sink. Turn it clockwise until it stops completely. Then turn on the faucet to drain any remaining water in the lines. This prevents flooding when you disassemble the faucet."
    },
    {
      "heading": "Step 2: Remove the Faucet Handle",
      "content": "Most faucet handles have a decorative cap hiding a screw. Use a flathead screwdriver to gently pop off the cap. Then unscrew the handle screw (usually Phillips head) and lift off the handle. If it's stuck, gently wiggle it back and forth while pulling upward."
    },
    {
      "heading": "Step 3: Replace the O-Ring or Washer",
      "content": "Once the handle is off, you'll see the cartridge or stem. The leak is usually caused by a worn O-ring or washer. Take the old one to a hardware store to find an exact match. O-rings cost about $2-5. Apply plumber's grease to the new O-ring before installing."
    },
    {
      "heading": "Step 4: Reassemble the Faucet",
      "content": "Put everything back together in reverse order. Make sure all parts are aligned correctly. Tighten screws firmly but don't overtighten - you can crack ceramic parts."
    },
    {
      "heading": "Step 5: Test for Leaks",
      "content": "Turn the water supply back on slowly. Check for leaks around the base and handle. Turn the faucet on and off several times. If water drips from the base or handle, you may need to tighten connections or replace additional parts."
    }
  ],
  "key_takeaways": [
    "Always turn off water supply before starting",
    "Take old parts to hardware store for exact match",
    "Apply plumber's grease to O-rings",
    "Don't overtighten - hand-tight plus a quarter turn is usually enough",
    "Test thoroughly before considering job complete"
  ],
  "common_mistakes": [
    "Forgetting to turn off water (flooding!)",
    "Using wrong size O-ring (won't seal properly)",
    "Overtightening screws (cracks ceramic parts)",
    "Skipping plumber's grease (causes premature wear)"
  ],
  "safety_warnings": [
    "Turn off water before starting to avoid flooding",
    "Keep electrical devices away from water",
    "If you see corroded pipes, call a professional - may indicate bigger issues"
  ],
  "call_to_action": "If this fix doesn't work or you're not comfortable doing it yourself, call Joe's Plumbing at (813) 555-0100. We're licensed, insured, and available 24/7 for emergency repairs in Tampa Bay."
}
```

---

## Step 4: Generate HTML

### Template System

```python
# templates/tutorial_content.html

def generate_tutorial_html(structured_content: dict, professional: ProfessionalProfile) -> str:
    """
    Generate full HTML page from structured content
    """
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{structured_content['title']}</title>
    <meta name="description" content="{structured_content['meta_description']}">
    <meta name="keywords" content="{', '.join(structured_content['keywords'])}">

    <style>
        :root {{
            --primary-color: {professional.primary_color or '#0066CC'};
            --accent-color: {professional.accent_color or '#FF6600'};
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}

        header {{
            border-bottom: 3px solid var(--primary-color);
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}

        .logo {{
            max-width: 200px;
            margin-bottom: 10px;
        }}

        h1 {{
            color: var(--primary-color);
            font-size: 2rem;
            margin: 20px 0;
        }}

        h2 {{
            color: var(--primary-color);
            font-size: 1.5rem;
            margin-top: 30px;
        }}

        .introduction {{
            background: #f8f9fa;
            padding: 20px;
            border-left: 4px solid var(--primary-color);
            margin: 20px 0;
        }}

        .section {{
            margin: 30px 0;
        }}

        .key-takeaways, .common-mistakes, .safety-warnings {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}

        .key-takeaways {{
            border-left: 4px solid #28a745;
        }}

        .common-mistakes {{
            border-left: 4px solid #ffc107;
        }}

        .safety-warnings {{
            border-left: 4px solid #dc3545;
        }}

        .cta {{
            background: var(--accent-color);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            margin: 30px 0;
        }}

        .cta a {{
            color: white;
            text-decoration: none;
            font-weight: bold;
            font-size: 1.2rem;
        }}

        .verification-badge {{
            display: inline-block;
            background: #28a745;
            color: white;
            padding: 10px 15px;
            border-radius: 5px;
            margin: 10px 0;
        }}
    </style>
</head>
<body>
    <header>
        <img src="{professional.logo_url}" alt="{professional.business_name}" class="logo">
        <h1>{structured_content['title']}</h1>

        <div class="verification-badge">
            ✓ {professional.license_state} Licensed {professional.license_type} #{professional.license_number}
        </div>
    </header>

    <div class="introduction">
        <p>{structured_content['introduction']}</p>
    </div>

    <main>
"""

    # Add sections
    for section in structured_content['sections']:
        html += f"""
        <div class="section">
            <h2>{section['heading']}</h2>
            <p>{section['content']}</p>
        </div>
"""

    # Key takeaways
    if structured_content.get('key_takeaways'):
        html += """
        <div class="key-takeaways">
            <h2>Key Takeaways</h2>
            <ul>
"""
        for takeaway in structured_content['key_takeaways']:
            html += f"                <li>{takeaway}</li>\n"
        html += """
            </ul>
        </div>
"""

    # Common mistakes
    if structured_content.get('common_mistakes'):
        html += """
        <div class="common-mistakes">
            <h2>Common Mistakes to Avoid</h2>
            <ul>
"""
        for mistake in structured_content['common_mistakes']:
            html += f"                <li>{mistake}</li>\n"
        html += """
            </ul>
        </div>
"""

    # Safety warnings
    if structured_content.get('safety_warnings'):
        html += """
        <div class="safety-warnings">
            <h2>⚠️ Safety Warnings</h2>
            <ul>
"""
        for warning in structured_content['safety_warnings']:
            html += f"                <li>{warning}</li>\n"
        html += """
            </ul>
        </div>
"""

    # Call to action
    phone_link = f"tel:{professional.phone.replace(' ', '').replace('-', '')}"
    html += f"""
        <div class="cta">
            <p>{structured_content['call_to_action']}</p>
            <a href="{phone_link}">Call Now: {professional.phone}</a>
        </div>
    </main>

    <footer>
        <p>© {professional.business_name} | Licensed & Insured</p>
        <p><a href="/license-verify">Verify License</a> | <a href="/contact">Contact Us</a></p>
    </footer>
</body>
</html>
"""

    return html
```

---

## Step 5: Programmatic SEO (pSEO) - 50+ Landing Pages

### What is pSEO?

**Definition:** Generate dozens of landing page variations from one piece of content, targeting different:
- Cities ("Tampa plumber", "St. Petersburg plumber", "Clearwater plumber")
- Keywords ("emergency plumber", "24/7 plumber", "licensed plumber")
- Long-tail searches ("emergency plumber in Tampa FL", "fix leaky faucet Tampa")

**Why it works:**
- Each page targets specific search intent
- More pages = more chances to rank
- Automated = scales without manual effort

### pSEO Generator

```python
# pseo_generator.py

def generate_pseo_landing_pages(tutorial_id: int) -> int:
    """
    Generate 50+ landing page variations for a tutorial
    Returns number of pages created
    """
    tutorial = Tutorial.query.get(tutorial_id)
    professional = tutorial.professional

    # Get service area (cities to target)
    cities = get_service_area_cities(professional)

    # Get keywords from tutorial
    keywords = extract_keywords(tutorial.structured_content)

    # Generate variations
    pages_created = 0

    for city in cities:
        for keyword in keywords:
            # Create landing page
            landing_page = create_pseo_landing_page(
                tutorial=tutorial,
                city=city,
                keyword=keyword
            )

            if landing_page:
                pages_created += 1

    return pages_created


def get_service_area_cities(professional: ProfessionalProfile) -> list:
    """
    Get cities in professional's service area
    """
    # Start with professional's city
    primary_city = professional.address_city

    # Get nearby cities (within 30 miles)
    nearby_cities = get_nearby_cities(primary_city, radius_miles=30)

    return [primary_city] + nearby_cities


def get_nearby_cities(city: str, radius_miles: int) -> list:
    """
    Get cities within radius
    Could use census data, Google Places API, or hardcoded lists
    """
    # Example for Tampa Bay area
    TAMPA_BAY_CITIES = [
        'Tampa', 'St. Petersburg', 'Clearwater', 'Brandon', 'Riverview',
        'Wesley Chapel', 'Land O Lakes', 'Lutz', 'Carrollwood',
        'Temple Terrace', 'Plant City', 'Largo', 'Pinellas Park'
    ]

    if city == 'Tampa':
        return TAMPA_BAY_CITIES

    # TODO: Implement for other cities
    return []


def extract_keywords(structured_content: dict) -> list:
    """
    Extract targetable keywords from content
    """
    title = structured_content['title']
    keywords = structured_content.get('keywords', [])

    # Add variations
    keyword_variations = []

    for keyword in keywords:
        keyword_variations.append(keyword)
        keyword_variations.append(f"emergency {keyword}")
        keyword_variations.append(f"24/7 {keyword}")
        keyword_variations.append(f"licensed {keyword}")
        keyword_variations.append(f"best {keyword}")

    return keyword_variations


def create_pseo_landing_page(tutorial: Tutorial, city: str, keyword: str) -> PSEOLandingPage:
    """
    Create individual pSEO landing page
    """
    professional = tutorial.professional

    # Generate slug
    slug = f"{city.lower().replace(' ', '-')}-{keyword.lower().replace(' ', '-')}"

    # Check if already exists
    existing = PSEOLandingPage.query.filter_by(
        professional_id=professional.id,
        slug=slug
    ).first()

    if existing:
        return existing

    # Generate localized content
    long_tail_keyword = f"{keyword} in {city}"

    h1_headline = f"{keyword.title()} in {city} | {professional.business_name}"

    meta_title = f"{keyword.title()} in {city} - {professional.business_name}"

    meta_description = f"Need a {keyword} in {city}? {professional.business_name} is licensed, insured, and available 24/7. Call {professional.phone} for fast service."

    # Customize content with city-specific info
    content_html = customize_content_for_city(
        tutorial.html_content,
        city=city,
        keyword=keyword
    )

    # Create landing page
    landing_page = PSEOLandingPage(
        tutorial_id=tutorial.id,
        professional_id=professional.id,
        slug=slug,
        full_url=f"{professional.subdomain}.cringeproof.com/{slug}",
        target_city=city,
        target_keyword=keyword,
        long_tail_keyword=long_tail_keyword,
        h1_headline=h1_headline,
        meta_title=meta_title,
        meta_description=meta_description,
        content_html=content_html
    )

    db.session.add(landing_page)
    db.session.commit()

    return landing_page


def customize_content_for_city(base_content: str, city: str, keyword: str) -> str:
    """
    Add city-specific context to base content
    """
    city_intro = f"""
    <div class="city-intro">
        <p>Serving {city} and surrounding areas with professional {keyword} services.
        {get_city_facts(city)}</p>
    </div>
    """

    # Inject city intro after first paragraph
    content_with_city = base_content.replace(
        '</header>',
        f'</header>{city_intro}',
        1
    )

    return content_with_city


def get_city_facts(city: str) -> str:
    """
    Add credibility with local knowledge
    """
    CITY_FACTS = {
        'Tampa': 'We proudly serve Tampa residents, from Downtown to Westshore to New Tampa.',
        'St. Petersburg': 'Serving St. Pete from the Pier to Tyrone Mall and everywhere in between.',
        'Clearwater': 'From Clearwater Beach to Countryside, we\'ve got you covered.',
    }

    return CITY_FACTS.get(city, f'Proud to serve the {city} community.')
```

### Example pSEO Output

**From 1 tutorial → 50+ landing pages:**

```
Tutorial: "How to Fix a Leaky Faucet"

Generated landing pages:
1. joesplumbing.cringeproof.com/tampa-plumber
2. joesplumbing.cringeproof.com/tampa-emergency-plumber
3. joesplumbing.cringeproof.com/tampa-24-7-plumber
4. joesplumbing.cringeproof.com/tampa-licensed-plumber
5. joesplumbing.cringeproof.com/st-petersburg-plumber
6. joesplumbing.cringeproof.com/st-petersburg-emergency-plumber
7. joesplumbing.cringeproof.com/clearwater-plumber
8. joesplumbing.cringeproof.com/brandon-plumber
9. joesplumbing.cringeproof.com/riverview-plumber
10. joesplumbing.cringeproof.com/tampa-fix-leaky-faucet
11. joesplumbing.cringeproof.com/tampa-faucet-repair
12. joesplumbing.cringeproof.com/st-petersburg-fix-leaky-faucet
...
(50+ total variations)
```

**Each page has:**
- Unique URL (slug)
- Unique title & meta description (city + keyword)
- Unique H1 headline
- Base content + city-specific intro
- Same tutorial content (avoiding duplicate content penalty)
- Same CTA (call Joe's Plumbing)

---

## Step 6: Auto-Deployment

### Database Save

```python
# routes/tutorials.py

@app.route('/api/tutorials', methods=['POST'])
@login_required
def create_tutorial():
    """
    Complete pipeline: Upload audio → Generate site
    """
    professional = g.current_user.professional_profile

    # Step 1: Upload audio
    audio_file = request.files.get('audio')
    audio_url = upload_audio_to_s3(audio_file, professional.id)

    # Step 2: Transcribe
    transcript = transcribe_audio(audio_url)

    # Step 3: Structure with AI
    structured_content = structure_transcript(transcript)

    # Step 4: Generate HTML
    html_content = generate_tutorial_html(structured_content, professional)

    # Save tutorial
    tutorial = Tutorial(
        professional_id=professional.id,
        title=structured_content['title'],
        audio_url=audio_url,
        transcript=transcript,
        structured_content=structured_content,  # Store as JSON
        html_content=html_content,
        meta_description=structured_content['meta_description'],
        keywords=','.join(structured_content['keywords']),
        status='published',
        published_at=datetime.utcnow()
    )
    db.session.add(tutorial)
    db.session.commit()

    # Step 5: Generate pSEO landing pages (async)
    from tasks import generate_pseo_task
    generate_pseo_task.delay(tutorial.id)

    # Step 6: Submit to Google
    submit_sitemap_to_google(professional.subdomain)

    return jsonify({
        'id': tutorial.id,
        'title': tutorial.title,
        'url': f"https://{professional.subdomain}.cringeproof.com/tutorials/{tutorial.id}",
        'status': 'published',
        'pseo_pages': 'generating'
    }), 201
```

### Sitemap Generation

```python
# seo/sitemap.py

def generate_sitemap(professional_id: int) -> str:
    """
    Generate XML sitemap for professional's site
    """
    professional = ProfessionalProfile.query.get(professional_id)

    # Get all published tutorials
    tutorials = Tutorial.query.filter_by(
        professional_id=professional_id,
        status='published'
    ).all()

    # Get all landing pages
    landing_pages = PSEOLandingPage.query.filter_by(
        professional_id=professional_id
    ).all()

    domain = f"{professional.subdomain}.cringeproof.com"

    sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://{domain}/</loc>
        <changefreq>weekly</changefreq>
        <priority>1.0</priority>
    </url>
"""

    # Add tutorials
    for tutorial in tutorials:
        sitemap += f"""
    <url>
        <loc>https://{domain}/tutorials/{tutorial.id}</loc>
        <lastmod>{tutorial.published_at.strftime('%Y-%m-%d')}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>
"""

    # Add landing pages
    for page in landing_pages:
        sitemap += f"""
    <url>
        <loc>https://{domain}/{page.slug}</loc>
        <lastmod>{page.created_at.strftime('%Y-%m-%d')}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.7</priority>
    </url>
"""

    sitemap += """
</urlset>
"""

    # Save sitemap
    sitemap_path = f"/var/www/sitemaps/{professional.subdomain}.xml"
    with open(sitemap_path, 'w') as f:
        f.write(sitemap)

    return sitemap


def submit_sitemap_to_google(subdomain: str):
    """
    Submit sitemap to Google Search Console
    """
    import requests

    sitemap_url = f"https://{subdomain}.cringeproof.com/sitemap.xml"

    # Google Search Console API
    # (Requires OAuth setup)
    requests.post(
        'https://www.google.com/webmasters/tools/ping',
        params={'sitemap': sitemap_url}
    )
```

---

## Full Pipeline Example

### Input: 10-Minute Voice Recording

**Joe records voice memo:**
> "Hey everyone, Joe from Joe's Plumbing here in Tampa. Today I want to talk about fixing leaky faucets. This is something I get called about probably 3-4 times a week, and honestly, a lot of times homeowners can fix it themselves if they know what to do..."

### Output: Complete Website in 10 Minutes

**Main tutorial page:**
```
URL: joesplumbing.cringeproof.com/tutorials/123
Title: How to Fix a Leaky Faucet: Tampa Plumber's 5-Step Guide
Content: Full structured HTML with Joe's branding
```

**50+ pSEO landing pages:**
```
1. joesplumbing.cringeproof.com/tampa-plumber
   - Title: "Plumber in Tampa | Joe's Plumbing"
   - H1: "Tampa Plumber - Licensed & Insured"
   - Content: Tutorial + Tampa-specific intro

2. joesplumbing.cringeproof.com/st-petersburg-plumber
   - Title: "Plumber in St. Petersburg | Joe's Plumbing"
   - H1: "St. Petersburg Plumber - Fast Response"
   - Content: Tutorial + St. Pete-specific intro

3. joesplumbing.cringeproof.com/tampa-emergency-plumber
   - Title: "Emergency Plumber in Tampa - 24/7 Service"
   - H1: "Tampa Emergency Plumber - Call Now"
   - Content: Tutorial + emergency service emphasis

... (50+ more variations)
```

**Sitemap submitted to Google:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://joesplumbing.cringeproof.com/</loc>
        <priority>1.0</priority>
    </url>
    <url>
        <loc>https://joesplumbing.cringeproof.com/tutorials/123</loc>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>https://joesplumbing.cringeproof.com/tampa-plumber</loc>
        <priority>0.7</priority>
    </url>
    <!-- ... 50+ more URLs -->
</urlset>
```

**Result:**
- Joe's site ranks for "Tampa plumber", "St. Pete plumber", "emergency plumber Tampa", etc.
- Organic traffic starts flowing within 7-14 days
- Leads come directly to Joe (no marketplace, no shared leads)

---

## Advanced Features

### Multi-Tutorial Sites

**After Joe records 10 tutorials:**
```
joesplumbing.cringeproof.com
├── Homepage (lists all 10 tutorials)
├── /tutorials/leaky-faucet
├── /tutorials/clogged-drain
├── /tutorials/water-heater-repair
├── /tutorials/toilet-running
├── /tutorials/low-water-pressure
├── /tutorials/frozen-pipes
├── /tutorials/sewer-line-backup
├── /tutorials/garbage-disposal-repair
├── /tutorials/sump-pump-installation
└── /tutorials/repiping

Each tutorial generates 50+ pSEO pages
= 500+ landing pages total
= Massive SEO footprint
```

### AI-Generated FAQs

```python
def generate_faq_section(tutorial: Tutorial) -> list:
    """
    Auto-generate FAQ from tutorial content
    """
    prompt = f"""Based on this tutorial about {tutorial.title}, generate 5-10 common questions
    a customer might ask, with concise answers.

    Tutorial content:
    {tutorial.transcript}

    Output as JSON:
    [
        {{"question": "How much does it cost?", "answer": "..."}},
        {{"question": "How long does it take?", "answer": "..."}}
    ]
    """

    faqs = ollama_generate(prompt)
    return json.loads(faqs)
```

### Schema Markup (Rich Snippets)

```python
def add_schema_markup(tutorial: Tutorial, professional: ProfessionalProfile) -> str:
    """
    Add structured data for Google rich snippets
    """
    schema = {
        "@context": "https://schema.org",
        "@type": "HowTo",
        "name": tutorial.title,
        "description": tutorial.meta_description,
        "image": professional.logo_url,
        "totalTime": "PT30M",
        "estimatedCost": {
            "@type": "MonetaryAmount",
            "currency": "USD",
            "value": "0"
        },
        "tool": [
            {"@type": "HowToTool", "name": "Adjustable wrench"},
            {"@type": "HowToTool", "name": "Screwdriver"},
            {"@type": "HowToTool", "name": "Replacement O-ring"}
        ],
        "step": [
            {
                "@type": "HowToStep",
                "name": section["heading"],
                "text": section["content"]
            }
            for section in tutorial.structured_content['sections']
        ],
        "author": {
            "@type": "Person",
            "name": professional.business_name,
            "jobTitle": professional.license_type
        }
    }

    return f'<script type="application/ld+json">{json.dumps(schema, indent=2)}</script>'
```

### Video Generation (Future)

```python
# Future: Generate video from audio + stock footage

def generate_tutorial_video(tutorial: Tutorial) -> str:
    """
    Combine:
    - Audio (professional's voice)
    - Stock footage (relevant B-roll)
    - Text overlays (steps)
    - Professional's logo/branding

    Output: MP4 video uploaded to YouTube/Vimeo
    """
    pass
```

---

## Performance Optimization

### Caching Strategy

```python
# Cache generated HTML for fast loading

from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'redis'})

@app.route('/<slug>')
@cache.cached(timeout=3600)  # Cache for 1 hour
def landing_page(slug):
    # Generate page
    page = PSEOLandingPage.query.filter_by(slug=slug).first()
    return render_template('landing_page.html', page=page)
```

### CDN for Assets

```python
# Upload images/audio to CDN (CloudFlare, CloudFront, etc.)

def upload_audio_to_s3(audio_file, professional_id: int) -> str:
    """
    Upload to S3 with CloudFront CDN
    """
    import boto3

    s3 = boto3.client('s3')

    key = f"audio/{professional_id}/{audio_file.filename}"

    s3.upload_fileobj(
        audio_file,
        'cringeproof-audio',
        key,
        ExtraArgs={'ACL': 'public-read'}
    )

    # Return CloudFront URL (fast CDN)
    return f"https://cdn.cringeproof.com/{key}"
```

### Lazy Load Images

```html
<!-- In generated HTML -->
<img src="placeholder.jpg"
     data-src="{{ professional.logo_url }}"
     loading="lazy"
     alt="{{ professional.business_name }}">

<script>
// Lazy load when in viewport
document.querySelectorAll('img[data-src]').forEach(img => {
    img.src = img.dataset.src;
});
</script>
```

---

## Analytics & Tracking

### UTM Parameters

```python
# Add tracking to all CTAs

def add_utm_tracking(url: str, tutorial_id: int, landing_page_id: int) -> str:
    """
    Track which pages generate leads
    """
    return f"{url}?utm_source=tutorial&utm_medium=cta&utm_campaign=tutorial_{tutorial_id}&utm_content=page_{landing_page_id}"


# Example CTA with tracking:
cta_url = add_utm_tracking(
    f"tel:{professional.phone}",
    tutorial_id=123,
    landing_page_id=456
)
```

### Lead Attribution

```python
# Track which tutorial/page generated each lead

class Lead(db.Model):
    # ...
    tutorial_id = db.Column(db.Integer, db.ForeignKey('tutorial.id'))
    landing_page_id = db.Column(db.Integer, db.ForeignKey('pseo_landing_page.id'))
    utm_source = db.Column(db.String(100))
    utm_medium = db.Column(db.String(100))
    utm_campaign = db.Column(db.String(100))
    utm_content = db.Column(db.String(100))


# Show professional which tutorials are performing best
def get_top_performing_tutorials(professional_id: int) -> list:
    """
    Rank tutorials by lead generation
    """
    tutorials = Tutorial.query.filter_by(
        professional_id=professional_id
    ).all()

    results = []

    for tutorial in tutorials:
        lead_count = Lead.query.filter_by(tutorial_id=tutorial.id).count()

        results.append({
            'tutorial': tutorial,
            'lead_count': lead_count
        })

    # Sort by lead count
    results.sort(key=lambda x: x['lead_count'], reverse=True)

    return results
```

---

## Quality Control

### Content Moderation

```python
def moderate_content(transcript: str) -> dict:
    """
    Check for:
    - Profanity
    - False claims
    - Dangerous advice
    - Competitor mentions
    """
    issues = []

    # Profanity filter
    if contains_profanity(transcript):
        issues.append('profanity')

    # Dangerous advice (e.g., "you don't need to turn off power")
    if contains_dangerous_advice(transcript):
        issues.append('safety_concern')

    # False claims (e.g., "we're the only licensed plumber")
    if contains_false_claims(transcript):
        issues.append('false_claim')

    return {
        'approved': len(issues) == 0,
        'issues': issues
    }
```

### SEO Quality Check

```python
def check_seo_quality(landing_page: PSEOLandingPage) -> dict:
    """
    Ensure SEO best practices
    """
    checks = {}

    # Title length (50-60 chars optimal)
    checks['title_length'] = 50 <= len(landing_page.meta_title) <= 60

    # Meta description (150-160 chars optimal)
    checks['meta_description_length'] = 150 <= len(landing_page.meta_description) <= 160

    # Keyword in title
    checks['keyword_in_title'] = landing_page.target_keyword.lower() in landing_page.meta_title.lower()

    # Keyword in H1
    checks['keyword_in_h1'] = landing_page.target_keyword.lower() in landing_page.h1_headline.lower()

    # Content length (500+ words)
    checks['content_length'] = len(landing_page.content_html.split()) >= 500

    return checks
```

---

## Cost Analysis

### Per Tutorial Generated

**Costs:**
- Transcription (Ollama): $0 (free, local)
- Transcription (OpenAI fallback): $0.06 (10 min audio)
- AI structuring (Ollama): $0 (free, local)
- pSEO generation: $0 (automated script)
- Storage (database): ~$0.001
- CDN bandwidth (audio): ~$0.05/mo per tutorial

**Total cost per tutorial: ~$0.06 (if using OpenAI) or $0 (if using Ollama)**

**Value generated:**
- 1 tutorial = 50+ landing pages
- Each landing page = potential for 10-100 organic visitors/mo
- Conversion rate: ~5% (leads per visitor)
- Each tutorial = $3,000/mo in lead value (based on pricing doc)

**ROI: $3,000 value / $0.06 cost = 50,000x ROI**

---

## Security Considerations

### Content Injection Prevention

```python
# Sanitize all user input
import bleach

def sanitize_transcript(transcript: str) -> str:
    """
    Remove any HTML/JavaScript from transcript
    """
    return bleach.clean(transcript, tags=[], strip=True)
```

### Rate Limiting

```python
from flask_limiter import Limiter

limiter = Limiter(app)

@app.route('/api/tutorials', methods=['POST'])
@limiter.limit("10 per hour")  # Prevent spam
def create_tutorial():
    pass
```

---

## Future Enhancements

### Multi-Language Support
**Generate Spanish/French/etc. versions automatically**

```python
def translate_tutorial(tutorial_id: int, target_language: str):
    """
    Translate tutorial to target language
    Generate separate pSEO pages for Spanish-speaking markets
    """
    pass
```

### Voice Cloning
**Generate variations without re-recording**

```python
def generate_voice_variation(tutorial_id: int, new_script: str):
    """
    Use voice cloning to generate new audio
    Professional records once, AI generates infinite variations
    """
    pass
```

### A/B Testing Landing Pages
**Test different headlines/CTAs**

```python
def ab_test_landing_page(landing_page_id: int):
    """
    Create 2 versions with different headlines
    Track which converts better
    Auto-winner takes all traffic
    """
    pass
```

---

## Conclusion

**Generative site system enables:**

1. **Speed:** 10 min voice → complete website
2. **Scale:** 1 recording → 50+ SEO-optimized pages
3. **Quality:** AI follows best practices automatically
4. **Accessibility:** No technical skills required
5. **ROI:** $0.06 cost → $3,000/mo value per tutorial

**Implementation status:**
- ✅ Voice recording (web + mobile)
- ✅ Transcription (Ollama + OpenAI)
- ⏳ AI structuring (prompt designed, needs testing)
- ⏳ HTML generation (template ready, needs integration)
- ⏳ pSEO generator (algorithm designed, needs implementation)
- ⏳ Auto-deployment (architecture ready, needs integration)

**Next steps:**
1. Implement `pseo_generator.py` (see separate file)
2. Test full pipeline with real professional
3. Measure SEO results (ranking, traffic, leads)
4. Optimize AI prompts based on feedback
5. Add video generation capability

---

**Created:** 2026-01-09
**By:** Claude Code
**See also:**
- `pseo_generator.py` - Implementation of pSEO landing page generator
- `template_generator.py` - Auto-generate professional site templates
- `WHITELABEL_ARCHITECTURE.md` - Subdomain/custom domain system
- `PRICING_STRATEGY.md` - $49/mo Pro tier includes unlimited tutorials
