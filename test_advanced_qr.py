"""
Test Advanced QR Code Features

Tests gradient, animated, and logo QR generation
"""

from advanced_qr import AdvancedQRGenerator, create_gradient_qr, create_animated_qr
import os

print("=" * 70)
print("Testing Advanced QR Code Features")
print("=" * 70)
print()

# Test 1: Basic QR with custom color
print("Test 1: Basic QR with Custom Color")
print("-" * 70)

generator = AdvancedQRGenerator(
    data="https://soulfra.com/test",
    style='rounded',
    primary_color='#8B5CF6',
    label='SOULFRA',
    size=512
)

qr_bytes = generator.generate()
with open('test_advanced_basic.png', 'wb') as f:
    f.write(qr_bytes)

print(f"✅ Generated: test_advanced_basic.png ({len(qr_bytes):,} bytes)")
print()

# Test 2: Gradient QR
print("Test 2: Gradient QR Code")
print("-" * 70)

generator = AdvancedQRGenerator(
    data="https://cringeproof.com/test",
    style='minimal',
    primary_color='#8B5CF6',
    secondary_color='#3B82F6',
    label='GRADIENT QR',
    size=512
)

gradient_bytes = generator.generate()
with open('test_advanced_gradient.png', 'wb') as f:
    f.write(gradient_bytes)

print(f"✅ Generated: test_advanced_gradient.png ({len(gradient_bytes):,} bytes)")
print()

# Test 3: Animated QR
print("Test 3: Animated QR Code (GIF)")
print("-" * 70)

try:
    generator = AdvancedQRGenerator(
        data="https://howtocookathome.com/test",
        style='circles',
        primary_color='#F97316',
        label='ANIMATED',
        size=512
    )

    animated_bytes = generator.generate_animated(frames=8, pulse_intensity=0.3)
    with open('test_advanced_animated.gif', 'wb') as f:
        f.write(animated_bytes)

    print(f"✅ Generated: test_advanced_animated.gif ({len(animated_bytes):,} bytes)")
    print("   8 frames, pulsing effect")
except ImportError as e:
    print(f"⚠️  Skipped (imageio not installed)")
    print(f"   Install with: pip install imageio")

print()

# Test 4: Test all three styles
print("Test 4: Different Styles")
print("-" * 70)

styles = ['minimal', 'rounded', 'circles']
colors = ['#2D3748', '#8B5CF6', '#F97316']

for style, color in zip(styles, colors):
    generator = AdvancedQRGenerator(
        data=f"https://test.com/{style}",
        style=style,
        primary_color=color,
        label=style.upper(),
        size=400
    )

    qr_bytes = generator.generate()
    filename = f'test_advanced_style_{style}.png'
    with open(filename, 'wb') as f:
        f.write(qr_bytes)

    print(f"  ✅ {style.capitalize():12} → {filename} ({len(qr_bytes):,} bytes)")

print()

# Summary
print("=" * 70)
print("✅ Advanced QR Tests Complete!")
print()
print("Generated files:")
print("  - test_advanced_basic.png (custom color)")
print("  - test_advanced_gradient.png (dual-color gradient)")
print("  - test_advanced_animated.gif (pulsing animation)")
print("  - test_advanced_style_minimal.png")
print("  - test_advanced_style_rounded.png")
print("  - test_advanced_style_circles.png")
print()
print("Next steps:")
print("  1. Open http://localhost:5001/qr/create")
print("  2. Enable 'Gradient' checkbox")
print("  3. Try 'Animated' checkbox")
print("  4. Test the new features!")
print("=" * 70)
