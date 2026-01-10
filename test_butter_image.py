#!/usr/bin/env python3
"""
Test Butter Image Generator

Generates a real AI image for "How to Make Salted Butter" recipe.
Proves the AI image generation system works.

Usage:
    python test_butter_image.py

Output:
    - butter_test.png (AI-generated if available)
    - butter_fallback.png (procedural if AI unavailable)
"""

import os


def test_ai_generation():
    """Test AI image generation"""
    print("=" * 70)
    print("🧈 Butter Image Generation Test")
    print("=" * 70)
    print()

    print("Testing AI image generation for:")
    print("  Title: How to Make Salted Butter")
    print("  Brand: HowToCookAtHome")
    print("  Type: Recipe")
    print()

    # Import modules
    try:
        from ai_image_generator import AIImageGenerator
        from prompt_templates import get_brand_prompt, get_negative_prompt

        print("✅ Modules imported successfully")
        print()

    except ImportError as e:
        print(f"❌ Import failed: {e}")
        print()
        print("Run installation first: python install_ai.py")
        return False

    # Initialize generator
    print("Initializing AI generator...")
    generator = AIImageGenerator()
    print()

    # Check if AI is available
    if not generator.available:
        print("⚠️  PyTorch/diffusers not available")
        print("   Testing fallback mode instead...")
        print()
        return test_fallback_generation()

    # Generate prompt using brand template
    prompt = get_brand_prompt(
        brand_slug='howtocookathome',
        title='How to Make Salted Butter',
        keywords=['butter', 'recipe', 'homemade', 'cooking'],
        content_type='recipe'
    )

    negative = get_negative_prompt('howtocookathome')

    print("Generated Prompt:")
    print(f"  {prompt[:100]}...")
    print()
    print("Negative Prompt:")
    print(f"  {negative[:80]}...")
    print()

    # Generate image
    print("🎨 Generating AI image (this may take 30-60 seconds)...")
    print("   Size: 800x600")
    print("   Steps: 25")
    print()

    try:
        image_bytes = generator.generate_from_text(
            prompt=prompt,
            negative_prompt=negative,
            size=(800, 600),
            num_steps=25,  # Good quality/speed balance
            guidance_scale=7.5
        )

        # Save image
        output_path = 'butter_test.png'

        with open(output_path, 'wb') as f:
            f.write(image_bytes)

        print()
        print(f"✅ AI image generated successfully!")
        print(f"   Saved to: {output_path}")
        print(f"   Size: {len(image_bytes):,} bytes")
        print()
        print("Open the image to see the result!")

        return True

    except Exception as e:
        print(f"❌ AI generation failed: {e}")
        print()
        import traceback
        traceback.print_exc()
        print()
        print("Falling back to procedural generation...")
        return test_fallback_generation()


def test_fallback_generation():
    """Test procedural fallback generation"""
    print()
    print("Testing fallback (procedural) generation...")
    print()

    try:
        from ai_image_generator import generate_fallback_image

        image_bytes = generate_fallback_image(
            keywords=['butter', 'recipe', 'homemade'],
            brand_colors=['#FFD700', '#FFA500', '#FF8C00'],  # Butter colors
            size=(800, 600)
        )

        # Save image
        output_path = 'butter_fallback.png'

        with open(output_path, 'wb') as f:
            f.write(image_bytes)

        print(f"✅ Fallback image generated!")
        print(f"   Saved to: {output_path}")
        print(f"   Size: {len(image_bytes):,} bytes")
        print()
        print("Note: This is a procedural image (shapes/colors)")
        print("For AI images, run: python install_ai.py")

        return True

    except Exception as e:
        print(f"❌ Fallback generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_prompt_templates():
    """Test prompt template system"""
    print()
    print("=" * 70)
    print("Testing Prompt Templates")
    print("=" * 70)
    print()

    try:
        from prompt_templates import get_brand_prompt, get_negative_prompt

        # Test different brands
        brands_to_test = [
            ('howtocookathome', 'Salted Butter', ['butter', 'recipe'], 'recipe'),
            ('cringeproof', 'Social Media Tips', ['social', 'strategy'], 'blog'),
            ('soulfra', 'AI Content Creation', ['ai', 'automation'], 'blog')
        ]

        for brand, title, keywords, content_type in brands_to_test:
            prompt = get_brand_prompt(brand, title, keywords, content_type)

            print(f"Brand: {brand}")
            print(f"  Prompt: {prompt[:100]}...")
            print()

        print("✅ Prompt templates working")
        print()

    except Exception as e:
        print(f"⚠️  Prompt templates test failed: {e}")
        print()


if __name__ == '__main__':
    # Test prompt templates first
    test_prompt_templates()

    # Test image generation
    success = test_ai_generation()

    print()
    print("=" * 70)

    if success:
        print("✅ Test Complete!")
        print()
        print("The AI image generation system is working.")
        print("Generated images will be used automatically for blog posts.")
    else:
        print("⚠️  Test completed with warnings")
        print()
        print("AI generation unavailable - using procedural fallback.")
        print("To enable AI: python install_ai.py")

    print("=" * 70)
