#!/usr/bin/env python3
"""
Pixel Layer Compositor Routes
Backend "backdoor switch" for visual layer composition

Provides server-side image blending with CRT color effects
"""

from flask import Blueprint, render_template, request, jsonify, send_file
from PIL import Image, ImageFilter, ImageEnhance, ImageOps
import io
import base64
from datetime import datetime
import json

composer_bp = Blueprint('composer', __name__)


@composer_bp.route('/build/composer')
def visual_composer():
    """
    Visual layer composition interface

    Replaces /api/build/templates with user-friendly pixel art tool
    """
    return render_template('layer_composer.html')


@composer_bp.route('/api/compose/layers', methods=['POST'])
def compose_layers():
    """
    Composite multiple pixel art layers with blending

    Request:
    {
      "layers": [
        {
          "data": "data:image/png;base64,...",
          "opacity": 1.0,
          "blend": "normal"
        }
      ],
      "colorMode": "rainbow",  // rainbow, bw, grey, white
      "brightness": 1.0,
      "contrast": 1.0,
      "scanlines": true
    }

    Response:
    {
      "success": true,
      "composited": "data:image/png;base64,...",
      "stats": {
        "layers": 3,
        "size": "512x512",
        "mode": "rainbow"
      }
    }
    """
    try:
        data = request.json
        layers_data = data.get('layers', [])
        color_mode = data.get('colorMode', 'rainbow')
        brightness = float(data.get('brightness', 1.0))
        contrast = float(data.get('contrast', 1.0))
        add_scanlines = data.get('scanlines', True)

        if not layers_data:
            return jsonify({'success': False, 'error': 'No layers provided'}), 400

        # Decode layers
        layers = []
        for layer_data in layers_data:
            img_data = layer_data['data']
            opacity = float(layer_data.get('opacity', 1.0))
            blend_mode = layer_data.get('blend', 'normal')

            # Decode base64 image
            if img_data.startswith('data:image'):
                img_data = img_data.split(',')[1]

            img_bytes = base64.b64decode(img_data)
            img = Image.open(io.BytesIO(img_bytes))

            layers.append({
                'image': img,
                'opacity': opacity,
                'blend': blend_mode
            })

        # Composite layers
        base = layers[0]['image'].convert('RGBA')

        for i in range(1, len(layers)):
            layer = layers[i]
            overlay = layer['image'].convert('RGBA')

            # Apply opacity
            if layer['opacity'] < 1.0:
                alpha = overlay.split()[3]
                alpha = ImageEnhance.Brightness(alpha).enhance(layer['opacity'])
                overlay.putalpha(alpha)

            # Blend (simplified - PIL doesn't support all CSS blend modes)
            # For full blend mode support, would need to implement manually
            base = Image.alpha_composite(base, overlay)

        # Apply CRT color effects
        final = apply_crt_effects(base, color_mode, brightness, contrast)

        # Add scanlines
        if add_scanlines:
            final = add_crt_scanlines(final)

        # Convert to base64
        output = io.BytesIO()
        final.save(output, format='PNG')
        output.seek(0)
        b64_data = base64.b64encode(output.read()).decode()

        return jsonify({
            'success': True,
            'composited': f'data:image/png;base64,{b64_data}',
            'stats': {
                'layers': len(layers),
                'size': f'{final.width}x{final.height}',
                'mode': color_mode
            }
        })

    except Exception as e:
        print(f"❌ Composition error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@composer_bp.route('/api/compose/animation', methods=['POST'])
def compose_animation():
    """
    Animate layered frames → GIF/WebM

    Request:
    {
      "frames": [
        {"layers": [...], "duration": 100},
        {"layers": [...], "duration": 100}
      ],
      "colorMode": "rainbow",
      "loop": true
    }

    Response:
    {
      "success": true,
      "animation": "data:image/gif;base64,...",
      "frames": 10,
      "duration": 1000
    }
    """
    try:
        data = request.json
        frames_data = data.get('frames', [])
        color_mode = data.get('colorMode', 'rainbow')
        loop = data.get('loop', True)

        if not frames_data:
            return jsonify({'success': False, 'error': 'No frames provided'}), 400

        # Process each frame
        frames = []
        durations = []

        for frame_data in frames_data:
            # Composite layers for this frame
            layers_data = frame_data.get('layers', [])
            duration = frame_data.get('duration', 100)

            # Similar compositing logic as compose_layers
            # (simplified for now)

            durations.append(duration)

        # Create GIF
        # TODO: Implement GIF encoding

        return jsonify({
            'success': True,
            'message': 'Animation encoding coming soon',
            'frames': len(frames_data)
        })

    except Exception as e:
        print(f"❌ Animation error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


def apply_crt_effects(img, mode, brightness=1.0, contrast=1.0):
    """
    Apply CRT color tone effects

    Args:
        img: PIL Image
        mode: rainbow, bw, grey, white
        brightness: 0.5 to 1.5
        contrast: 0.5 to 2.0

    Returns:
        PIL Image with CRT effects applied
    """
    # Convert to RGB for processing
    img = img.convert('RGB')

    # Apply brightness
    if brightness != 1.0:
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(brightness)

    # Apply contrast
    if contrast != 1.0:
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(contrast)

    # Apply color mode
    if mode == 'rainbow':
        # Increase saturation for arcade-style colors
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(1.5)

    elif mode == 'bw':
        # Pure black and white (threshold)
        img = img.convert('L')
        img = img.point(lambda x: 0 if x < 128 else 255, '1')
        img = img.convert('RGB')

    elif mode == 'grey':
        # Greyscale with phosphor glow (desaturate)
        img = img.convert('L')
        img = img.convert('RGB')

    elif mode == 'white':
        # Amber CRT (invert + sepia)
        img = ImageOps.invert(img)
        # Apply amber tint (simplified - would need proper color grading)
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(0.5)

    return img


def add_crt_scanlines(img, intensity=0.15):
    """
    Add CRT scanline effect

    Args:
        img: PIL Image
        intensity: 0.0 to 1.0 (darkness of scanlines)

    Returns:
        PIL Image with scanlines
    """
    width, height = img.size
    pixels = img.load()

    # Add horizontal scanlines
    for y in range(0, height, 2):
        for x in range(width):
            r, g, b = pixels[x, y]
            # Darken every other row
            pixels[x, y] = (
                int(r * (1 - intensity)),
                int(g * (1 - intensity)),
                int(b * (1 - intensity))
            )

    return img


def register_composer_routes(app):
    """
    Register compositor routes with Flask app

    Usage:
        from composer_routes import register_composer_routes
        register_composer_routes(app)
    """
    app.register_blueprint(composer_bp)
    print('🎨 Pixel Composer routes registered')
    print('   Visual: /build/composer')
    print('   API: /api/compose/layers')
    print('   API: /api/compose/animation')


# Testing
if __name__ == '__main__':
    from flask import Flask

    app = Flask(__name__)
    register_composer_routes(app)

    print('\n🧪 Testing Pixel Compositor Routes\n')

    # Test route registration
    print('Routes registered:')
    for rule in app.url_map.iter_rules():
        if 'compose' in rule.rule or 'build' in rule.rule:
            print(f'  {rule.rule} → {rule.endpoint}')

    print('\n✅ Compositor routes ready!\n')
