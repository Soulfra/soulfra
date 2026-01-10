#!/usr/bin/env python3
"""
Generate PWA icons for Practice Rooms
"""
from PIL import Image, ImageDraw, ImageFont
import os

# Icon sizes needed for PWA
SIZES = [72, 96, 128, 144, 152, 192, 384, 512]

# Output directory
OUTPUT_DIR = "static/icons"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def create_gradient_icon(size):
    """Create a gradient icon with 'P' letter"""
    # Create image
    img = Image.new('RGB', (size, size), color='white')
    draw = ImageDraw.Draw(img)

    # Draw gradient background (indigo to purple)
    for y in range(size):
        # Interpolate between indigo (#6366f1) and purple (#a855f7)
        ratio = y / size
        r = int(99 + (168 - 99) * ratio)
        g = int(102 + (85 - 102) * ratio)
        b = int(241 + (247 - 241) * ratio)
        draw.line([(0, y), (size, y)], fill=(r, g, b))

    # Draw 'P' letter in white
    try:
        # Try to use a system font
        font_size = int(size * 0.6)
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
        except:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
            except:
                # Fallback to default font
                font = ImageFont.load_default()

        # Draw text centered
        text = "P"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (size - text_width) // 2
        y = (size - text_height) // 2 - bbox[1]

        draw.text((x, y), text, fill='white', font=font)
    except Exception as e:
        print(f"Warning: Could not add text to {size}x{size} icon: {e}")

    return img

def main():
    print("Generating PWA icons...")

    for size in SIZES:
        icon = create_gradient_icon(size)
        filename = f"{OUTPUT_DIR}/icon-{size}x{size}.png"
        icon.save(filename, 'PNG')
        print(f"  ✓ Created {filename}")

    print(f"\n✅ Generated {len(SIZES)} PWA icons!")
    print(f"📁 Icons saved to {OUTPUT_DIR}/")

if __name__ == '__main__':
    main()
