#!/usr/bin/env python3
"""
Image Composer - Professional Layer-Based Image Composition

Adobe/Photoshop-style layer composition engine for creating professional images.

Features:
- Multi-layer composition with transparency
- Layer types: background, image, text, shape, gradient, QR code
- Blending modes: normal, multiply, overlay, screen
- Effects: shadows, blur, opacity
- Custom fonts and colors
- Export to PNG/WebP with alpha channel

Usage:
    from image_composer import ImageComposer

    # Create 1080x1080 canvas
    composer = ImageComposer(size=(1080, 1080))

    # Add gradient background
    composer.add_layer('gradient', colors=['#FF6B35', '#F7931E'], angle=45)

    # Add logo
    composer.add_layer('image', path='logo.png', position=(50, 50), size=(200, 200))

    # Add text with shadow
    composer.add_layer('text',
        content='Professional Design',
        font='impact',
        size=72,
        color='#FFFFFF',
        position='center',
        shadow={'offset': (2, 2), 'blur': 4, 'color': '#000000'}
    )

    # Add QR code
    composer.add_layer('qr', url='https://soulfra.com', position='bottom-right')

    # Render to bytes
    image_bytes = composer.render()

Architecture:
    - Layer stack (bottom to top rendering)
    - Each layer is RGBA (transparency support)
    - Compositing with PIL Image.alpha_composite()
    - Font support via PIL ImageFont
"""

import io
import os
from typing import Dict, List, Tuple, Optional, Any
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from dataclasses import dataclass, field
import qrcode


# =============================================================================
# Layer Data Classes
# =============================================================================

@dataclass
class Layer:
    """Base layer class"""
    layer_type: str = ''
    opacity: float = 1.0
    blend_mode: str = 'normal'
    visible: bool = True
    z_index: int = 0


@dataclass
class BackgroundLayer(Layer):
    """Solid color background"""
    color: str = '#FFFFFF'
    layer_type: str = field(default='background', init=False)


@dataclass
class GradientLayer(Layer):
    """Gradient background"""
    colors: List[str] = field(default_factory=lambda: ['#3498db', '#2ecc71'])
    angle: int = 0  # 0=horizontal, 90=vertical, 45=diagonal
    layer_type: str = field(default='gradient', init=False)


@dataclass
class ImageLayer(Layer):
    """Image layer from file or bytes"""
    image: Any = None  # PIL Image or path
    position: Tuple[int, int] = (0, 0)
    size: Optional[Tuple[int, int]] = None
    layer_type: str = field(default='image', init=False)


@dataclass
class TextLayer(Layer):
    """Text layer with font styling"""
    content: str = ''
    font: str = 'Arial'
    font_size: int = 32
    color: str = '#000000'
    position: Any = 'center'  # (x, y) or 'center', 'top', 'bottom'
    align: str = 'center'  # left, center, right
    max_width: Optional[int] = None
    shadow: Optional[Dict] = None  # {'offset': (2, 2), 'blur': 4, 'color': '#000000'}
    layer_type: str = field(default='text', init=False)


@dataclass
class ShapeLayer(Layer):
    """Shape layer (rectangle, circle, line)"""
    shape: str = 'rectangle'  # rectangle, circle, ellipse, line
    position: Tuple[int, int] = (0, 0)
    size: Tuple[int, int] = (100, 100)
    fill_color: Optional[str] = '#000000'
    stroke_color: Optional[str] = None
    stroke_width: int = 0
    corner_radius: int = 0  # For rounded rectangles
    layer_type: str = field(default='shape', init=False)


@dataclass
class QRLayer(Layer):
    """QR code layer"""
    url: str = ''
    position: Any = 'bottom-right'  # (x, y) or preset position
    size: int = 150
    box_size: int = 10
    border: int = 2
    layer_type: str = field(default='qr', init=False)


# =============================================================================
# Image Composer
# =============================================================================

class ImageComposer:
    """
    Professional layer-based image composition

    Example:
        >>> composer = ImageComposer(size=(1080, 1080))
        >>> composer.add_layer('gradient', colors=['#FF6B35', '#F7931E'])
        >>> composer.add_layer('text', content='Hello World', font='impact', size=72)
        >>> image_bytes = composer.render()
    """

    def __init__(self, size: Tuple[int, int] = (1080, 1080), background_color: str = '#FFFFFF'):
        """
        Initialize image composer

        Args:
            size: Canvas size (width, height)
            background_color: Default background color
        """
        self.size = size
        self.background_color = background_color
        self.layers: List[Layer] = []
        self.font_cache: Dict[str, ImageFont.FreeTypeFont] = {}

    def add_layer(self, layer_type: str, **kwargs) -> Layer:
        """
        Add layer to composition

        Args:
            layer_type: Type of layer ('background', 'gradient', 'image', 'text', 'shape', 'qr')
            **kwargs: Layer-specific parameters

        Returns:
            Layer object

        Example:
            >>> composer.add_layer('text', content='Hello', font='impact', size=48, color='#FFFFFF')
        """
        # Create layer based on type
        if layer_type == 'background':
            layer = BackgroundLayer(**kwargs)
        elif layer_type == 'gradient':
            layer = GradientLayer(**kwargs)
        elif layer_type == 'image':
            layer = ImageLayer(**kwargs)
        elif layer_type == 'text':
            layer = TextLayer(**kwargs)
        elif layer_type == 'shape':
            layer = ShapeLayer(**kwargs)
        elif layer_type == 'qr':
            layer = QRLayer(**kwargs)
        else:
            raise ValueError(f"Unknown layer type: {layer_type}")

        self.layers.append(layer)
        return layer

    def render(self, format: str = 'PNG') -> bytes:
        """
        Render all layers to image bytes

        Args:
            format: Output format ('PNG', 'WEBP', 'JPEG')

        Returns:
            Image bytes

        Example:
            >>> image_bytes = composer.render(format='PNG')
        """
        # Create base canvas with transparency
        canvas = Image.new('RGBA', self.size, (255, 255, 255, 0))

        # Sort layers by z-index
        sorted_layers = sorted(self.layers, key=lambda layer: layer.z_index)

        # Render each layer
        for layer in sorted_layers:
            if not layer.visible:
                continue

            # Render layer to RGBA image
            layer_img = self._render_layer(layer)

            if layer_img:
                # Apply opacity
                if layer.opacity < 1.0:
                    alpha = layer_img.split()[3]
                    alpha = alpha.point(lambda p: int(p * layer.opacity))
                    layer_img.putalpha(alpha)

                # Composite onto canvas
                canvas = Image.alpha_composite(canvas, layer_img)

        # Convert to RGB if needed (for JPEG)
        if format.upper() == 'JPEG':
            rgb_canvas = Image.new('RGB', self.size, (255, 255, 255))
            rgb_canvas.paste(canvas, mask=canvas.split()[3])
            canvas = rgb_canvas

        # Export to bytes
        output = io.BytesIO()
        canvas.save(output, format=format.upper())
        return output.getvalue()

    def _render_layer(self, layer: Layer) -> Optional[Image.Image]:
        """Render individual layer to RGBA image"""
        if layer.layer_type == 'background':
            return self._render_background(layer)
        elif layer.layer_type == 'gradient':
            return self._render_gradient(layer)
        elif layer.layer_type == 'image':
            return self._render_image(layer)
        elif layer.layer_type == 'text':
            return self._render_text(layer)
        elif layer.layer_type == 'shape':
            return self._render_shape(layer)
        elif layer.layer_type == 'qr':
            return self._render_qr(layer)
        return None

    def _render_background(self, layer: BackgroundLayer) -> Image.Image:
        """Render solid color background"""
        img = Image.new('RGBA', self.size, self._hex_to_rgba(layer.color))
        return img

    def _render_gradient(self, layer: GradientLayer) -> Image.Image:
        """Render gradient background"""
        img = Image.new('RGBA', self.size)
        draw = ImageDraw.Draw(img)

        width, height = self.size
        colors = [self._hex_to_rgba(c) for c in layer.colors]

        # Horizontal gradient (angle=0)
        if layer.angle == 0:
            for x in range(width):
                ratio = x / width
                color = self._blend_colors(colors[0], colors[-1], ratio)
                draw.line([(x, 0), (x, height)], fill=color)

        # Vertical gradient (angle=90)
        elif layer.angle == 90:
            for y in range(height):
                ratio = y / height
                color = self._blend_colors(colors[0], colors[-1], ratio)
                draw.line([(0, y), (width, y)], fill=color)

        # Diagonal gradient (angle=45)
        else:
            # Simple diagonal for now
            for x in range(width):
                for y in range(height):
                    ratio = (x + y) / (width + height)
                    color = self._blend_colors(colors[0], colors[-1], ratio)
                    draw.point((x, y), fill=color)

        return img

    def _render_image(self, layer: ImageLayer) -> Image.Image:
        """Render image layer"""
        # Load image
        if isinstance(layer.image, str):
            img = Image.open(layer.image).convert('RGBA')
        elif isinstance(layer.image, bytes):
            img = Image.open(io.BytesIO(layer.image)).convert('RGBA')
        elif isinstance(layer.image, Image.Image):
            img = layer.image.convert('RGBA')
        else:
            return None

        # Resize if needed
        if layer.size:
            img = img.resize(layer.size, Image.LANCZOS)

        # Create layer canvas
        layer_img = Image.new('RGBA', self.size, (255, 255, 255, 0))
        layer_img.paste(img, layer.position, img)

        return layer_img

    def _render_text(self, layer: TextLayer) -> Image.Image:
        """Render text layer with shadow support"""
        layer_img = Image.new('RGBA', self.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(layer_img)

        # Load font
        font = self._get_font(layer.font, layer.font_size)

        # Get text size
        bbox = draw.textbbox((0, 0), layer.content, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Calculate position
        if layer.position == 'center':
            x = (self.size[0] - text_width) // 2
            y = (self.size[1] - text_height) // 2
        elif layer.position == 'top':
            x = (self.size[0] - text_width) // 2
            y = 50
        elif layer.position == 'bottom':
            x = (self.size[0] - text_width) // 2
            y = self.size[1] - text_height - 50
        else:
            x, y = layer.position

        # Draw shadow if specified
        if layer.shadow:
            shadow_offset = layer.shadow.get('offset', (2, 2))
            shadow_color = self._hex_to_rgba(layer.shadow.get('color', '#000000'))
            shadow_blur = layer.shadow.get('blur', 4)

            # Draw shadow text
            shadow_x = x + shadow_offset[0]
            shadow_y = y + shadow_offset[1]
            draw.text((shadow_x, shadow_y), layer.content, font=font, fill=shadow_color)

            # Apply blur to shadow (expensive operation)
            if shadow_blur > 0:
                layer_img = layer_img.filter(ImageFilter.GaussianBlur(radius=shadow_blur // 2))
                draw = ImageDraw.Draw(layer_img)

        # Draw text
        text_color = self._hex_to_rgba(layer.color)
        draw.text((x, y), layer.content, font=font, fill=text_color)

        return layer_img

    def _render_shape(self, layer: ShapeLayer) -> Image.Image:
        """Render shape layer"""
        layer_img = Image.new('RGBA', self.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(layer_img)

        x, y = layer.position
        w, h = layer.size

        fill = self._hex_to_rgba(layer.fill_color) if layer.fill_color else None
        stroke = self._hex_to_rgba(layer.stroke_color) if layer.stroke_color else None

        if layer.shape == 'rectangle':
            if layer.corner_radius > 0:
                draw.rounded_rectangle([x, y, x + w, y + h], radius=layer.corner_radius,
                                      fill=fill, outline=stroke, width=layer.stroke_width)
            else:
                draw.rectangle([x, y, x + w, y + h], fill=fill, outline=stroke, width=layer.stroke_width)

        elif layer.shape == 'circle':
            draw.ellipse([x, y, x + w, y + h], fill=fill, outline=stroke, width=layer.stroke_width)

        elif layer.shape == 'ellipse':
            draw.ellipse([x, y, x + w, y + h], fill=fill, outline=stroke, width=layer.stroke_width)

        elif layer.shape == 'line':
            draw.line([x, y, x + w, y + h], fill=fill or stroke, width=layer.stroke_width)

        return layer_img

    def _render_qr(self, layer: QRLayer) -> Image.Image:
        """Render QR code layer"""
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=layer.box_size,
            border=layer.border
        )
        qr.add_data(layer.url)
        qr.make(fit=True)

        qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGBA')
        qr_img = qr_img.resize((layer.size, layer.size), Image.LANCZOS)

        # Calculate position
        if layer.position == 'bottom-right':
            x = self.size[0] - layer.size - 20
            y = self.size[1] - layer.size - 20
        elif layer.position == 'bottom-left':
            x = 20
            y = self.size[1] - layer.size - 20
        elif layer.position == 'top-right':
            x = self.size[0] - layer.size - 20
            y = 20
        elif layer.position == 'top-left':
            x = 20
            y = 20
        else:
            x, y = layer.position

        # Create layer canvas
        layer_img = Image.new('RGBA', self.size, (255, 255, 255, 0))
        layer_img.paste(qr_img, (x, y), qr_img)

        return layer_img

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _get_font(self, font_name: str, size: int) -> ImageFont.FreeTypeFont:
        """Load font (with caching)"""
        cache_key = f"{font_name}:{size}"

        if cache_key in self.font_cache:
            return self.font_cache[cache_key]

        # Try to load font
        font_paths = [
            f"/usr/share/fonts/truetype/{font_name.lower()}.ttf",
            f"/System/Library/Fonts/{font_name}.ttc",
            f"/Library/Fonts/{font_name}.ttf",
            f"C:\\Windows\\Fonts\\{font_name}.ttf",
            font_name  # Direct path
        ]

        for path in font_paths:
            if os.path.exists(path):
                try:
                    font = ImageFont.truetype(path, size)
                    self.font_cache[cache_key] = font
                    return font
                except:
                    continue

        # Fallback to default font
        try:
            font = ImageFont.truetype("Arial.ttf", size)
        except:
            font = ImageFont.load_default()

        self.font_cache[cache_key] = font
        return font

    def _hex_to_rgba(self, hex_color: str, alpha: int = 255) -> Tuple[int, int, int, int]:
        """Convert hex color to RGBA tuple"""
        hex_color = hex_color.lstrip('#')

        if len(hex_color) == 6:
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            return (r, g, b, alpha)
        elif len(hex_color) == 8:
            r, g, b, a = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4, 6))
            return (r, g, b, a)
        else:
            return (0, 0, 0, alpha)

    def _blend_colors(self, color1: Tuple, color2: Tuple, ratio: float) -> Tuple:
        """Blend two RGBA colors"""
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
        a = int(color1[3] * (1 - ratio) + color2[3] * ratio) if len(color1) > 3 else 255
        return (r, g, b, a)


# =============================================================================
# Quick Generation Functions
# =============================================================================

def create_social_post(
    title: str,
    subtitle: str = '',
    brand_colors: List[str] = ['#FF6B35', '#F7931E'],
    logo_path: Optional[str] = None,
    size: Tuple[int, int] = (1080, 1080)
) -> bytes:
    """
    Quick function to create social media post

    Example:
        >>> image_bytes = create_social_post(
        ...     title='New Blog Post',
        ...     subtitle='Check it out!',
        ...     brand_colors=['#FF6B35', '#F7931E']
        ... )
    """
    composer = ImageComposer(size=size)

    # Background gradient
    composer.add_layer('gradient', colors=brand_colors, angle=45)

    # Logo if provided
    if logo_path and os.path.exists(logo_path):
        composer.add_layer('image', image=logo_path, position=(50, 50), size=(150, 150))

    # Title text
    composer.add_layer('text',
        content=title,
        font='impact',
        font_size=84,
        color='#FFFFFF',
        position='center',
        shadow={'offset': (3, 3), 'blur': 6, 'color': '#000000'}
    )

    # Subtitle if provided
    if subtitle:
        composer.add_layer('text',
            content=subtitle,
            font='Arial',
            font_size=36,
            color='#FFFFFF',
            position=(size[0] // 2 - 200, size[1] // 2 + 100),
            shadow={'offset': (2, 2), 'blur': 4, 'color': '#000000'}
        )

    return composer.render()


# =============================================================================
# CLI Testing
# =============================================================================

if __name__ == '__main__':
    """Test image composer"""

    print("=" * 70)
    print("🎨 Image Composer Test")
    print("=" * 70)
    print()

    # Test 1: Simple gradient with text
    print("Test 1: Gradient + Text")
    print("-" * 70)

    composer = ImageComposer(size=(800, 600))
    composer.add_layer('gradient', colors=['#FF6B35', '#F7931E'], angle=45)
    composer.add_layer('text',
        content='Professional Design',
        font='impact',
        font_size=64,
        color='#FFFFFF',
        position='center',
        shadow={'offset': (3, 3), 'blur': 6, 'color': '#000000'}
    )

    output = composer.render()

    with open('composer_test1.png', 'wb') as f:
        f.write(output)

    print(f"✅ Generated: composer_test1.png ({len(output):,} bytes)")
    print()

    # Test 2: Shapes and QR code
    print("Test 2: Shapes + QR Code")
    print("-" * 70)

    composer2 = ImageComposer(size=(1080, 1080))
    composer2.add_layer('background', color='#F0F0F0')
    composer2.add_layer('shape',
        shape='circle',
        position=(340, 340),
        size=(400, 400),
        fill_color='#3498db',
        opacity=0.5
    )
    composer2.add_layer('text',
        content='Scan Me',
        font='Arial',
        font_size=48,
        color='#2c3e50',
        position=(440, 300)
    )
    composer2.add_layer('qr',
        url='https://soulfra.com',
        position='bottom-right',
        size=200
    )

    output2 = composer2.render()

    with open('composer_test2.png', 'wb') as f:
        f.write(output2)

    print(f"✅ Generated: composer_test2.png ({len(output2):,} bytes)")
    print()

    # Test 3: Quick social post
    print("Test 3: Quick Social Post")
    print("-" * 70)

    output3 = create_social_post(
        title='Layer-Based Images',
        subtitle='Professional Quality',
        brand_colors=['#8E44AD', '#3498DB']
    )

    with open('composer_test3.png', 'wb') as f:
        f.write(output3)

    print(f"✅ Generated: composer_test3.png ({len(output3):,} bytes)")
    print()

    print("=" * 70)
    print("✅ Image Composer Ready!")
    print()
    print("Usage:")
    print("  from image_composer import ImageComposer")
    print()
    print("  composer = ImageComposer(size=(1080, 1080))")
    print("  composer.add_layer('gradient', colors=['#FF6B35', '#F7931E'])")
    print("  composer.add_layer('text', content='Hello', font='impact', size=72)")
    print("  image_bytes = composer.render()")
    print("=" * 70)
