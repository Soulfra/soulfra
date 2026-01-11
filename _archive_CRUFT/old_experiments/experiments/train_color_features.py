#!/usr/bin/env python3
"""
Color Feature Extraction for Transparent AI Training

Extracts meaningful features from RGB colors to explain
WHY the AI classifies something as warm vs cool.

Features include:
- HSV (Hue, Saturation, Value/Brightness)
- Color wheel position (0-360 degrees)
- Temperature score (warm vs cool)
- Saturation level (vibrant vs muted)
- Brightness level (dark vs light)
- Dominant channel (R/G/B)
"""

import colorsys
import math


def extract_color_features(rgb):
    """
    Extract features from RGB color

    Input: [R, G, B] normalized to [0, 1]
    Output: List of 12 features

    Features:
    0: Hue (0-1, maps to 0-360°)
    1: Saturation (0-1)
    2: Value/Brightness (0-1)
    3: Temperature score (0=cool, 1=warm)
    4: Red dominance (0-1)
    5: Green dominance (0-1)
    6: Blue dominance (0-1)
    7: Is vibrant (saturation > 0.6)
    8: Is muted (saturation < 0.3)
    9: Is bright (value > 0.7)
    10: Is dark (value < 0.3)
    11: Is grayscale (saturation < 0.1)
    """
    r, g, b = rgb

    # Convert to HSV
    h, s, v = colorsys.rgb_to_hsv(r, g, b)

    # Temperature score (0=cool, 1=warm)
    # Based on hue: Red/Orange/Yellow = warm (hue 0-60, 300-360)
    # Blue/Cyan/Green = cool (hue 120-240)
    hue_degrees = h * 360
    if hue_degrees < 60 or hue_degrees > 300:
        # Red to yellow range
        temperature = 0.8 + (s * 0.2)  # More saturated = more warm
    elif 120 <= hue_degrees <= 240:
        # Blue to cyan range
        temperature = 0.2 - (s * 0.2)  # More saturated = more cool
    else:
        # Transition zones
        if hue_degrees < 120:
            # Yellow to green
            temperature = 0.5 + (60 - (hue_degrees - 60)) / 120
        else:
            # Green to red
            temperature = 0.5 - (60 - (hue_degrees - 240)) / 120

    temperature = max(0, min(1, temperature))

    # Channel dominance
    total = r + g + b
    if total > 0:
        r_dominance = r / total
        g_dominance = g / total
        b_dominance = b / total
    else:
        r_dominance = g_dominance = b_dominance = 0.33

    # Binary features
    is_vibrant = 1 if s > 0.6 else 0
    is_muted = 1 if s < 0.3 else 0
    is_bright = 1 if v > 0.7 else 0
    is_dark = 1 if v < 0.3 else 0
    is_grayscale = 1 if s < 0.1 else 0

    return [
        h,              # 0: Hue (0-1)
        s,              # 1: Saturation (0-1)
        v,              # 2: Value/Brightness (0-1)
        temperature,    # 3: Temperature score
        r_dominance,    # 4: Red dominance
        g_dominance,    # 5: Green dominance
        b_dominance,    # 6: Blue dominance
        is_vibrant,     # 7: Is vibrant
        is_muted,       # 8: Is muted
        is_bright,      # 9: Is bright
        is_dark,        # 10: Is dark
        is_grayscale    # 11: Is grayscale
    ]


def explain_color_features(features, rgb):
    """
    Generate human-readable explanations of color features

    Input:
        features: List of 12 feature values from extract_color_features()
        rgb: [R, G, B] normalized to [0, 1]

    Output: List of explanation strings with emojis
    """
    h, s, v, temp, r_dom, g_dom, b_dom, is_vib, is_mut, is_bri, is_dar, is_gray = features

    explanations = []

    # Hue / Color wheel position
    hue_degrees = h * 360
    hue_name = get_hue_name(hue_degrees)
    explanations.append(f"🎨 Hue: {hue_degrees:.0f}° ({hue_name})")

    # Saturation
    sat_percent = s * 100
    if is_gray:
        sat_desc = "Grayscale (no color)"
    elif is_mut:
        sat_desc = "Muted/desaturated"
    elif is_vib:
        sat_desc = "Highly vibrant"
    else:
        sat_desc = "Moderate saturation"
    explanations.append(f"🌈 Saturation: {sat_percent:.0f}% ({sat_desc})")

    # Brightness
    bright_percent = v * 100
    if is_dar:
        bright_desc = "Dark"
    elif is_bri:
        bright_desc = "Bright/light"
    else:
        bright_desc = "Medium brightness"
    explanations.append(f"💡 Brightness: {bright_percent:.0f}% ({bright_desc})")

    # Temperature
    temp_percent = temp * 100
    if temp > 0.7:
        temp_desc = "Very warm (red/orange/yellow)"
    elif temp > 0.55:
        temp_desc = "Warm-leaning"
    elif temp < 0.3:
        temp_desc = "Very cool (blue/cyan/green)"
    elif temp < 0.45:
        temp_desc = "Cool-leaning"
    else:
        temp_desc = "Neutral temperature"
    explanations.append(f"🌡️ Temperature: {temp_percent:.0f}% ({temp_desc})")

    # Dominant channel
    channels = [('Red', r_dom), ('Green', g_dom), ('Blue', b_dom)]
    dominant = max(channels, key=lambda x: x[1])
    dom_percent = dominant[1] * 100
    explanations.append(f"🎯 Dominant: {dominant[0]} ({dom_percent:.0f}%)")

    # RGB raw values
    r, g, b = rgb
    explanations.append(f"🔢 RGB: ({int(r*255)}, {int(g*255)}, {int(b*255)})")

    return explanations


def get_hue_name(hue_degrees):
    """
    Convert hue (0-360°) to color name with wheel position
    """
    if hue_degrees < 15 or hue_degrees >= 345:
        return "Red (top of wheel)"
    elif hue_degrees < 45:
        return "Red-Orange (warm side)"
    elif hue_degrees < 75:
        return "Orange (warm)"
    elif hue_degrees < 105:
        return "Yellow (warm side)"
    elif hue_degrees < 135:
        return "Yellow-Green (transition)"
    elif hue_degrees < 165:
        return "Green (cool side)"
    elif hue_degrees < 195:
        return "Cyan (cool)"
    elif hue_degrees < 225:
        return "Blue (bottom of wheel)"
    elif hue_degrees < 255:
        return "Blue-Violet (cool side)"
    elif hue_degrees < 285:
        return "Violet (transition)"
    elif hue_degrees < 315:
        return "Magenta (warm-cool mix)"
    else:
        return "Red-Magenta (warm side)"


def get_color_wheel_svg(hue_degrees):
    """
    Generate SVG for color wheel with pointer

    Returns SVG string showing the color's position on the wheel
    """
    # Calculate pointer position
    angle_rad = (hue_degrees - 90) * (math.pi / 180)  # -90 to start at top
    pointer_x = 50 + 35 * round(math.cos(angle_rad), 2)
    pointer_y = 50 + 35 * round(math.sin(angle_rad), 2)

    svg = f'''
    <svg width="100" height="100" viewBox="0 0 100 100" style="margin: 1rem auto; display: block;">
        <!-- Color wheel gradient -->
        <defs>
            <linearGradient id="rainbow" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" style="stop-color:rgb(255,0,0);stop-opacity:1" />
                <stop offset="17%" style="stop-color:rgb(255,255,0);stop-opacity:1" />
                <stop offset="33%" style="stop-color:rgb(0,255,0);stop-opacity:1" />
                <stop offset="50%" style="stop-color:rgb(0,255,255);stop-opacity:1" />
                <stop offset="67%" style="stop-color:rgb(0,0,255);stop-opacity:1" />
                <stop offset="83%" style="stop-color:rgb(255,0,255);stop-opacity:1" />
                <stop offset="100%" style="stop-color:rgb(255,0,0);stop-opacity:1" />
            </linearGradient>
        </defs>

        <!-- Wheel circle -->
        <circle cx="50" cy="50" r="40" fill="none" stroke="url(#rainbow)" stroke-width="12"/>

        <!-- Pointer to current hue -->
        <line x1="50" y1="50" x2="{pointer_x}" y2="{pointer_y}"
              stroke="#333" stroke-width="3" stroke-linecap="round"/>
        <circle cx="{pointer_x}" cy="{pointer_y}" r="5" fill="#333"/>
    </svg>
    '''

    return svg


if __name__ == '__main__':
    # Test with some colors
    print("=" * 70)
    print("COLOR FEATURE EXTRACTION TEST")
    print("=" * 70)
    print()

    test_colors = [
        ([1.0, 0.0, 0.0], "Pure Red"),
        ([0.0, 0.0, 1.0], "Pure Blue"),
        ([1.0, 0.5, 0.0], "Orange"),
        ([0.0, 0.8, 0.8], "Cyan"),
        ([0.5, 0.5, 0.5], "Gray"),
    ]

    for rgb, name in test_colors:
        print(f"\n{name}: RGB{tuple(int(c*255) for c in rgb)}")
        print("-" * 50)

        features = extract_color_features(rgb)
        explanations = explain_color_features(features, rgb)

        for exp in explanations:
            print(f"  {exp}")

        print()
