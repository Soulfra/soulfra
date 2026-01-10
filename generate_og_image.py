#!/usr/bin/env python3
"""
Generate Open Graph social card image (1200x630 PNG)
"""
from PIL import Image, ImageDraw, ImageFont
import sys

def generate_og_image():
    """Generate 1200x630 OG image for social sharing"""

    # Create image with gradient background
    img = Image.new('RGB', (1200, 630), color='#000000')
    draw = ImageDraw.Draw(img)

    # Create gradient background (black -> dark purple -> pink)
    for y in range(630):
        # Calculate color transition
        progress = y / 630

        if progress < 0.5:
            # Black to dark purple
            r = int(26 * (progress * 2))
            g = int(26 * (progress * 2))
            b = int(46 * (progress * 2))
        else:
            # Dark purple to pink
            local_progress = (progress - 0.5) * 2
            r = int(26 + (255 - 26) * local_progress)
            g = int(26 + (0 - 26) * local_progress)
            b = int(46 + (110 - 46) * local_progress)

        draw.rectangle([(0, y), (1200, y+1)], fill=(r, g, b))

    # Try to load system fonts
    try:
        # macOS system fonts
        title_font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 90)
        subtitle_font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 40)
        badge_font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 28)
        emoji_font = ImageFont.truetype('/System/Library/Fonts/Apple Color Emoji.ttc', 180)
    except:
        # Fallback to default font
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        badge_font = ImageFont.load_default()
        emoji_font = ImageFont.load_default()

    # Draw emoji
    emoji_text = "🚫"
    emoji_bbox = draw.textbbox((0, 0), emoji_text, font=emoji_font)
    emoji_width = emoji_bbox[2] - emoji_bbox[0]
    emoji_x = (1200 - emoji_width) // 2
    draw.text((emoji_x, 50), emoji_text, font=emoji_font, fill='#ffffff')

    # Draw title
    title = "CringeProof"
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (1200 - title_width) // 2
    draw.text((title_x, 300), title, font=title_font, fill='#ffffff')

    # Draw subtitle
    subtitle = "Voice Ideas, Zero Performance Anxiety"
    subtitle_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
    subtitle_x = (1200 - subtitle_width) // 2
    draw.text((subtitle_x, 420), subtitle, font=subtitle_font, fill='#ffe5ec')

    # Draw bottom badge
    badge_y = 540
    badge_height = 60
    draw.rectangle([(300, badge_y), (900, badge_y + badge_height)], fill='#ff006e')

    badge_text = "AI-Powered Voice Archive"
    badge_bbox = draw.textbbox((0, 0), badge_text, font=badge_font)
    badge_width = badge_bbox[2] - badge_bbox[0]
    badge_x = (1200 - badge_width) // 2
    draw.text((badge_x, badge_y + 18), badge_text, font=badge_font, fill='#ffffff')

    # Save image
    output_path = 'voice-archive/og-image.png'
    img.save(output_path, 'PNG', optimize=True)
    print(f"✅ OG image generated: {output_path}")
    print(f"📏 Size: 1200x630 pixels")
    print(f"🎨 Format: PNG")

    return output_path

if __name__ == '__main__':
    try:
        generate_og_image()
    except Exception as e:
        print(f"❌ Error generating OG image: {e}")
        sys.exit(1)
