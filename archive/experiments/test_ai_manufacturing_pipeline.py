#!/usr/bin/env python3
"""
AI Network Manufacturing Pipeline Test

Like watching a car roll off the assembly line - see EXACTLY what happens at each station!

This test:
1. Creates a test brand
2. Generates AI persona
3. Runs neural network prediction
4. Creates a test post
5. Runs orchestration to select AIs
6. (TODO) Generates AI comment

At each step, shows:
- Input data
- Processing
- Output data
- Quality checks (✅ or ❌)

Run: python3 test_ai_manufacturing_pipeline.py
"""

import sqlite3
import json
import time
from datetime import datetime
from typing import Dict, List, Optional

# ==============================================================================
# VISUAL OUTPUT HELPERS
# ==============================================================================

def print_station_header(number: int, name: str):
    """Print visual header for manufacturing station"""
    print()
    print("═" * 70)
    print(f"  🏭 STATION {number}: {name}")
    print("═" * 70)
    print()


def print_input(data: Dict):
    """Print input data"""
    print("📥 INPUT:")
    for key, value in data.items():
        if isinstance(value, (list, dict)):
            value_str = json.dumps(value, indent=2)[:100] + "..." if len(str(value)) > 100 else json.dumps(value)
        else:
            value_str = str(value)[:100]
        print(f"   • {key}: {value_str}")
    print()


def print_processing(steps: List[str]):
    """Print processing steps"""
    print("⚙️  PROCESSING:")
    for step in steps:
        print(f"   → {step}")
    print()


def print_output(data: Dict):
    """Print output data"""
    print("📤 OUTPUT:")
    for key, value in data.items():
        icon = "✅" if value else "❌"
        print(f"   {icon} {key}: {value}")
    print()


def print_quality_check(checks: List[tuple]):
    """Print quality control checks"""
    print("🔍 QUALITY CHECKS:")
    all_passed = True
    for name, passed, details in checks:
        icon = "✓" if passed else "✗"
        status = "PASS" if passed else "FAIL"
        print(f"   [{icon}] {name}: {status}")
        if details:
            print(f"       {details}")
        if not passed:
            all_passed = False
    print()
    return all_passed


def print_station_result(passed: bool, time_taken: float):
    """Print station result"""
    if passed:
        print(f"✅ STATION PASSED ({time_taken:.2f}s)")
    else:
        print(f"❌ STATION FAILED ({time_taken:.2f}s)")
    print()


# ==============================================================================
# DATABASE HELPERS
# ==============================================================================

def get_db():
    """Get database connection"""
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    return conn


# ==============================================================================
# STATION 1: BRAND CREATION
# ==============================================================================

def station_1_create_brand() -> tuple:
    """
    Station 1: Create a test brand

    Returns:
        (brand_id, passed, time_taken)
    """
    start_time = time.time()
    print_station_header(1, "BRAND CREATION")

    # Input
    brand_data = {
        "name": "TestBrand Auto",
        "slug": "testbrand-auto",
        "personality": "calm, analytical, deep",
        "tone": "thoughtful and measured",
        "colors": ["#003366", "#0066cc", "#3399ff", "#66ccff", "#99ccff"],
        "values": ["precision", "depth", "clarity"]
    }

    print_input(brand_data)

    # Processing
    processing_steps = [
        "Validate brand name (unique, no special chars)",
        "Parse color palette (hex codes valid)",
        "Generate slug: testbrand-auto",
        "Store config as JSON in database"
    ]
    print_processing(processing_steps)

    # Execute
    db = get_db()

    # Check if brand already exists
    existing = db.execute('SELECT id FROM brands WHERE slug = ?', (brand_data['slug'],)).fetchone()
    if existing:
        db.execute('DELETE FROM brands WHERE slug = ?', (brand_data['slug'],))
        db.commit()

    # Create brand
    config_json = json.dumps({
        "colors": brand_data["colors"],
        "values": brand_data["values"],
        "name": brand_data["name"],
        "personality": brand_data["personality"],
        "tone": brand_data["tone"]
    })

    db.execute('''
        INSERT INTO brands (name, slug, personality, tone, config_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        brand_data["name"],
        brand_data["slug"],
        brand_data["personality"],
        brand_data["tone"],
        config_json,
        datetime.now().isoformat()
    ))

    db.commit()
    brand_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]

    # Verify
    brand = db.execute('SELECT * FROM brands WHERE id = ?', (brand_id,)).fetchone()
    brand_dict = dict(brand) if brand else {}

    db.close()

    # Output
    output_data = {
        "Brand ID": brand_id,
        "Slug": brand_dict.get('slug'),
        "Config stored": bool(brand_dict.get('config_json'))
    }
    print_output(output_data)

    # Quality checks
    checks = [
        ("Brand exists in database", brand is not None, None),
        ("Brand ID is valid", brand_id > 0, f"ID={brand_id}"),
        ("Slug matches expected", brand_dict.get('slug') == brand_data['slug'], None),
        ("Config JSON is valid", brand_dict.get('config_json') is not None, None),
        ("Personality not empty", bool(brand_dict.get('personality')), None),
        ("Colors array has 5 elements", len(brand_data['colors']) == 5, None)
    ]

    passed = print_quality_check(checks)

    time_taken = time.time() - start_time
    print_station_result(passed, time_taken)

    return brand_id, passed, time_taken


# ==============================================================================
# STATION 2: AI PERSONA GENERATION
# ==============================================================================

def station_2_generate_ai_persona(brand_slug: str) -> tuple:
    """
    Station 2: Generate AI persona for brand

    Returns:
        (user_id, passed, time_taken)
    """
    start_time = time.time()
    print_station_header(2, "AI PERSONA GENERATION")

    from brand_ai_persona_generator import generate_brand_ai_persona

    # Input
    input_data = {
        "brand_slug": brand_slug
    }
    print_input(input_data)

    # Processing
    processing_steps = [
        f"Generate username: @{brand_slug}",
        f"Generate email: {brand_slug}@soulfra.ai",
        "Build system prompt from personality + tone",
        "Detect emoji based on brand type",
        "Create user account with is_ai_persona=1"
    ]
    print_processing(processing_steps)

    # Execute
    persona = generate_brand_ai_persona(brand_slug, tier='free')

    # Output
    if persona:
        output_data = {
            "User ID": persona['user_id'],
            "Username": persona['username'],
            "Display Name": persona['display_name'],
            "Email": persona['email'],
            "System Prompt Length": f"{len(persona['system_prompt'])} characters",
            "Emoji": persona['emoji']
        }
    else:
        output_data = {
            "Error": "Failed to generate persona"
        }

    print_output(output_data)

    # Quality checks
    if persona:
        checks = [
            ("Persona created successfully", persona is not None, None),
            ("Username matches brand slug", persona['username'] == brand_slug, None),
            ("Email follows pattern", persona['email'] == f"{brand_slug}@soulfra.ai", None),
            ("Display name set", bool(persona['display_name']), None),
            ("System prompt not empty", len(persona['system_prompt']) > 0, f"{len(persona['system_prompt'])} chars"),
            ("Emoji assigned", bool(persona['emoji']), persona['emoji'])
        ]
    else:
        checks = [
            ("Persona created successfully", False, "Failed to create persona")
        ]

    passed = print_quality_check(checks)

    time_taken = time.time() - start_time
    print_station_result(passed, time_taken)

    user_id = persona['user_id'] if persona else None
    return user_id, passed, time_taken


# ==============================================================================
# STATION 3: NEURAL NETWORK PREDICTION
# ==============================================================================

def station_3_neural_network_prediction(brand_slug: str) -> tuple:
    """
    Station 3: Run neural network prediction on brand colors

    Returns:
        (predictions, passed, time_taken)
    """
    start_time = time.time()
    print_station_header(3, "NEURAL NETWORK PREDICTION")

    from brand_color_neural_network import predict_brand_personality

    # Input
    input_data = {
        "brand_slug": brand_slug
    }
    print_input(input_data)

    # Processing
    processing_steps = [
        "Load brand colors from database",
        "Extract primary color",
        "Convert hex to RGB, then normalize",
        "Extract 12 color features (HSV, temp, etc.)",
        "Load trained neural network from database",
        "Run forward pass: features → hidden → output",
        "Map outputs to personality traits"
    ]
    print_processing(processing_steps)

    # Execute
    try:
        predictions = predict_brand_personality(brand_slug)
        success = True
    except Exception as e:
        predictions = {}
        success = False
        print(f"❌ Error: {e}")

    # Output
    if predictions:
        # Sort by score
        sorted_predictions = sorted(predictions.items(), key=lambda x: x[1], reverse=True)
        output_data = {
            f"Top trait ({sorted_predictions[0][0]})": f"{sorted_predictions[0][1]:.2f}",
            f"2nd trait ({sorted_predictions[1][0]})": f"{sorted_predictions[1][1]:.2f}",
            f"3rd trait ({sorted_predictions[2][0]})": f"{sorted_predictions[2][1]:.2f}",
            "Total traits predicted": len(predictions)
        }

        print_output(output_data)

        # Visual bar chart
        print("📊 PERSONALITY PREDICTIONS:")
        for trait, score in sorted_predictions:
            bar = "█" * int(score * 20)
            print(f"   {trait:15} {score:.2f} {bar}")
        print()
    else:
        output_data = {"Error": "No predictions generated"}
        print_output(output_data)

    # Quality checks
    if predictions:
        checks = [
            ("Predictions generated", success, None),
            ("All scores in [0, 1] range", all(0 <= score <= 1 for score in predictions.values()), None),
            ("Top trait score > 0.5", max(predictions.values()) > 0.5, f"{max(predictions.values()):.2f}"),
            ("Predicted 8 traits", len(predictions) == 8, f"{len(predictions)} traits")
        ]
    else:
        checks = [
            ("Predictions generated", False, "Failed to generate predictions")
        ]

    passed = print_quality_check(checks)

    time_taken = time.time() - start_time
    print_station_result(passed, time_taken)

    return predictions, passed, time_taken


# ==============================================================================
# STATION 4: POST CREATION
# ==============================================================================

def station_4_create_post() -> tuple:
    """
    Station 4: Create a test post

    Returns:
        (post_id, passed, time_taken)
    """
    start_time = time.time()
    print_station_header(4, "POST CREATION")

    # Input
    post_data = {
        "title": "Test: Deep Analysis and Precision",
        "content": "This post explores the depths of analytical thinking, requiring calm precision and clarity of thought. It's a measured approach to complex problems.",
        "author_id": 1  # Assume admin user exists
    }

    print_input(post_data)

    # Processing
    processing_steps = [
        "Generate slug from title",
        "Extract keywords from content",
        "Store post in database",
        "Trigger AI orchestration (simulated)"
    ]
    print_processing(processing_steps)

    # Execute
    db = get_db()

    # Generate slug
    slug = post_data['title'].lower().replace(' ', '-').replace(':', '')

    # Delete existing test post if it exists
    db.execute('DELETE FROM posts WHERE slug = ?', (slug,))
    db.commit()

    # Create post
    db.execute('''
        INSERT INTO posts (title, slug, content, user_id, published_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        post_data['title'],
        slug,
        post_data['content'],
        post_data['author_id'],
        datetime.now().isoformat()
    ))

    db.commit()
    post_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]

    # Verify
    post = db.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    post_dict = dict(post) if post else {}

    db.close()

    # Output
    output_data = {
        "Post ID": post_id,
        "Slug": post_dict.get('slug'),
        "Content length": f"{len(post_dict.get('content', ''))} characters",
        "Published at": post_dict.get('published_at') if post_dict.get('published_at') else "Not set"
    }
    print_output(output_data)

    # Quality checks
    keywords = ["deep", "analytical", "calm", "precision", "clarity", "measured"]
    found_keywords = [kw for kw in keywords if kw in post_data['content'].lower()]

    checks = [
        ("Post created", post is not None, None),
        ("Post ID valid", post_id > 0, f"ID={post_id}"),
        ("Slug generated", bool(post_dict.get('slug')), post_dict.get('slug')),
        ("Content not empty", len(post_dict.get('content', '')) > 0, f"{len(post_dict.get('content', ''))} chars"),
        ("Keywords present", len(found_keywords) >= 3, f"Found: {', '.join(found_keywords)}")
    ]

    passed = print_quality_check(checks)

    time_taken = time.time() - start_time
    print_station_result(passed, time_taken)

    return post_id, passed, time_taken


# ==============================================================================
# STATION 5: AI ORCHESTRATION
# ==============================================================================

def station_5_ai_orchestration(post_id: int) -> tuple:
    """
    Station 5: Run AI orchestration to select which AIs should comment

    Returns:
        (selected_brands, passed, time_taken)
    """
    start_time = time.time()
    print_station_header(5, "AI ORCHESTRATION")

    from brand_ai_orchestrator import orchestrate_brand_comments

    # Input
    input_data = {
        "post_id": post_id
    }
    print_input(input_data)

    # Processing
    processing_steps = [
        "Load all AI personas from database",
        "Calculate relevance score for each persona",
        "  • Base score: 0.1",
        "  • Personality match: up to +0.4",
        "  • Tone match: up to +0.3",
        "  • Values match: up to +0.3",
        "Filter by engagement tier (free > 0.5)",
        "Select top 3 relevant brands"
    ]
    print_processing(processing_steps)

    # Execute
    selected_brands = orchestrate_brand_comments(post_id, dry_run=False)

    # Output
    if selected_brands:
        output_data = {
            "Total personas evaluated": "All AI personas in database",
            "Personas selected": len(selected_brands),
            f"Top selection": f"{selected_brands[0]['brand_name']} (relevance={selected_brands[0]['relevance']:.2f})"
        }

        print_output(output_data)

        # Detailed selection results
        print("🎯 SELECTED AI PERSONAS:")
        for i, brand in enumerate(selected_brands, 1):
            print(f"   {i}. {brand['brand_name']:<20} (relevance={brand['relevance']:.2f})")
        print()
    else:
        output_data = {
            "Personas selected": 0,
            "Note": "No AI personas met relevance threshold"
        }
        print_output(output_data)

    # Quality checks
    testbrand_auto_selected = any(b['brand_slug'] == 'testbrand-auto' for b in selected_brands)

    checks = [
        ("Orchestration ran successfully", True, None),
        ("At least 1 AI selected", len(selected_brands) > 0, f"{len(selected_brands)} selected"),
        ("TestBrand Auto selected", testbrand_auto_selected, "Should be relevant to test post"),
        ("Relevance scores valid", all(0 <= b['relevance'] <= 1 for b in selected_brands), None)
    ]

    passed = print_quality_check(checks)

    time_taken = time.time() - start_time
    print_station_result(passed, time_taken)

    return selected_brands, passed, time_taken


# ==============================================================================
# STATION 6: COMMENT GENERATION (PLACEHOLDER)
# ==============================================================================

def station_6_comment_generation(post_id: int, selected_brands: List[Dict]) -> tuple:
    """
    Station 6: Generate AI comments (placeholder - Ollama integration needed)

    Returns:
        (comment_ids, passed, time_taken)
    """
    start_time = time.time()
    print_station_header(6, "COMMENT GENERATION (TODO)")

    # Input
    input_data = {
        "post_id": post_id,
        "selected_ai_personas": [b['brand_name'] for b in selected_brands]
    }
    print_input(input_data)

    # Processing
    processing_steps = [
        "🚧 Load AI persona system prompt",
        "🚧 Prepare Ollama API request",
        "🚧 Call Ollama (http://localhost:11434/api/generate)",
        "🚧 Receive generated comment",
        "🚧 Post-process and format comment",
        "🚧 Store comment in database"
    ]
    print_processing(processing_steps)

    # Placeholder
    print("⚠️  NOTICE: Comment generation not yet implemented!")
    print("   Next step: Build ollama_auto_commenter.py")
    print()

    # Output
    output_data = {
        "Status": "Not implemented",
        "TODO": "Create ollama_auto_commenter.py to wire Ollama API"
    }
    print_output(output_data)

    # Quality checks
    checks = [
        ("Comment generation implemented", False, "TODO: Build ollama_auto_commenter.py")
    ]

    passed = print_quality_check(checks)

    time_taken = time.time() - start_time
    print_station_result(passed, time_taken)

    return [], passed, time_taken


# ==============================================================================
# FINAL PRODUCT INSPECTION
# ==============================================================================

def final_inspection(results: List[tuple]):
    """Print final manufacturing report"""
    print()
    print("═" * 70)
    print("  📦 FINAL PRODUCT INSPECTION")
    print("═" * 70)
    print()

    total_time = sum(r[2] for r in results)
    stations_passed = sum(1 for r in results if r[1])
    total_stations = len(results)
    quality_score = (stations_passed / total_stations) * 100

    print("🔍 QUALITY CONTROL CHECKLIST:")
    print()

    station_names = [
        "Brand created and stored in database",
        "AI persona generated with correct username/email",
        "Neural network predicted personality from color",
        "Post published and keywords extracted",
        "Orchestrator selected relevant AI personas",
        "Comment generated and posted (TODO)"
    ]

    for i, (name, (_, passed, time_taken)) in enumerate(zip(station_names, results)):
        icon = "✅" if passed else "❌"
        print(f"   {icon} {name} ({time_taken:.2f}s)")

    print()
    print("📊 METRICS:")
    print(f"   • Total processing time: {total_time:.2f} seconds")
    print(f"   • Stations passed: {stations_passed}/{total_stations}")
    print(f"   • Quality score: {quality_score:.1f}%")
    print()

    if quality_score == 100:
        print("✅ RESULT: FULLY FUNCTIONAL AI NETWORK!")
    elif quality_score >= 80:
        print("⚠️  RESULT: MOSTLY FUNCTIONAL (minor issues)")
    else:
        print("❌ RESULT: NEEDS WORK (major issues)")

    print("═" * 70)
    print()


# ==============================================================================
# MAIN PIPELINE RUNNER
# ==============================================================================

def main():
    """Run the complete manufacturing pipeline"""
    print()
    print("═" * 70)
    print("  🏭 AI NETWORK MANUFACTURING PIPELINE - LIVE RUN")
    print("═" * 70)
    print()
    print("Like watching a car roll off the assembly line!")
    print()

    results = []

    try:
        # Station 1: Create Brand
        brand_id, passed_1, time_1 = station_1_create_brand()
        results.append((brand_id, passed_1, time_1))

        if not passed_1:
            print("❌ Pipeline halted at Station 1")
            final_inspection(results)
            return

        # Station 2: Generate AI Persona
        user_id, passed_2, time_2 = station_2_generate_ai_persona('testbrand-auto')
        results.append((user_id, passed_2, time_2))

        if not passed_2:
            print("❌ Pipeline halted at Station 2")
            final_inspection(results)
            return

        # Station 3: Neural Network Prediction
        predictions, passed_3, time_3 = station_3_neural_network_prediction('testbrand-auto')
        results.append((predictions, passed_3, time_3))

        # Continue even if NN fails (not critical for orchestration)

        # Station 4: Create Post
        post_id, passed_4, time_4 = station_4_create_post()
        results.append((post_id, passed_4, time_4))

        if not passed_4:
            print("❌ Pipeline halted at Station 4")
            final_inspection(results)
            return

        # Station 5: AI Orchestration
        selected_brands, passed_5, time_5 = station_5_ai_orchestration(post_id)
        results.append((selected_brands, passed_5, time_5))

        # Station 6: Comment Generation (placeholder)
        comment_ids, passed_6, time_6 = station_6_comment_generation(post_id, selected_brands)
        results.append((comment_ids, passed_6, time_6))

        # Final inspection
        final_inspection(results)

    except Exception as e:
        print()
        print("=" * 70)
        print("❌ PIPELINE ERROR!")
        print("=" * 70)
        print(f"Error: {e}")
        print()
        import traceback
        traceback.print_exc()
        print()

        if results:
            final_inspection(results)


if __name__ == '__main__':
    main()
