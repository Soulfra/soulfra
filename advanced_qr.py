"""
Advanced QR Code Generation - 2025/2026 Modern Features

Supports:
- Animated QR codes (GIF with pulsing effects)
- Gradient overlays (dual-color linear gradients)
- Logo embedding (center placement with error correction)
- Custom shapes (rounded corners, circular dots)
"""

import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer, CircleModuleDrawer, SquareModuleDrawer
from qrcode.image.styles.colormasks import SolidFillColorMask
from PIL import Image, ImageDraw, ImageFont
import io
from typing import Optional, Tuple, List
import os


class AdvancedQRGenerator:
    """Generate modern QR codes with advanced styling"""

    # Style to module drawer mapping
    STYLE_DRAWERS = {
        'minimal': SquareModuleDrawer,
        'rounded': RoundedModuleDrawer,
        'circles': CircleModuleDrawer
    }

    def __init__(
        self,
        data: str,
        style: str = 'minimal',
        primary_color: str = '#000000',
        secondary_color: Optional[str] = None,
        label: Optional[str] = None,
        logo_path: Optional[str] = None,
        size: int = 512
    ):
        """
        Initialize advanced QR generator

        Args:
            data: URL or text to encode
            style: 'minimal', 'rounded', or 'circles'
            primary_color: Main QR color (hex)
            secondary_color: Gradient end color (hex), if None no gradient
            label: Text label below QR code
            logo_path: Path to logo image for center embedding
            size: Final image size in pixels
        """
        self.data = data
        self.style = style
        self.primary_color = primary_color
        self.secondary_color = secondary_color
        self.label = label
        self.logo_path = logo_path
        self.size = size

    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def _create_gradient_overlay(self, qr_img: Image.Image) -> Image.Image:
        """Apply linear gradient overlay to QR code"""
        if not self.secondary_color:
            return qr_img

        # Create gradient image
        gradient = Image.new('RGB', qr_img.size)
        draw = ImageDraw.Draw(gradient)

        # Get colors
        color1 = self._hex_to_rgb(self.primary_color)
        color2 = self._hex_to_rgb(self.secondary_color)

        # Draw vertical gradient
        width, height = qr_img.size
        for y in range(height):
            # Interpolate between colors
            ratio = y / height
            r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
            g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
            b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        # Convert QR to RGBA for transparency
        qr_rgba = qr_img.convert('RGBA')

        # Create mask from QR (black pixels become opaque)
        # Extract alpha channel based on luminance
        pixels = qr_rgba.load()
        for y in range(height):
            for x in range(width):
                r, g, b, a = pixels[x, y]
                # If pixel is dark (QR module), keep it; if light (background), make transparent
                if r < 128:  # Dark pixel (QR module)
                    pixels[x, y] = gradient.getpixel((x, y)) + (255,)
                else:  # Light pixel (background)
                    pixels[x, y] = (255, 255, 255, 255)

        return qr_rgba.convert('RGB')

    def _embed_logo(self, qr_img: Image.Image) -> Image.Image:
        """Embed logo in center of QR code"""
        if not self.logo_path or not os.path.exists(self.logo_path):
            return qr_img

        # Open and resize logo
        logo = Image.open(self.logo_path)

        # Logo should be ~20% of QR size
        logo_size = int(qr_img.size[0] * 0.2)
        logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)

        # Add white background to logo
        logo_bg = Image.new('RGB', (logo_size + 20, logo_size + 20), 'white')
        logo_bg.paste(logo, (10, 10), logo.convert('RGBA') if logo.mode == 'RGBA' else None)

        # Calculate center position
        qr_width, qr_height = qr_img.size
        logo_width, logo_height = logo_bg.size
        position = (
            (qr_width - logo_width) // 2,
            (qr_height - logo_height) // 2
        )

        # Paste logo
        qr_img.paste(logo_bg, position)
        return qr_img

    def _add_label(self, qr_img: Image.Image) -> Image.Image:
        """Add text label below QR code"""
        if not self.label:
            return qr_img

        # Create new image with space for label
        label_height = 60
        final_img = Image.new('RGB', (qr_img.size[0], qr_img.size[1] + label_height), 'white')
        final_img.paste(qr_img, (0, 0))

        # Draw label
        draw = ImageDraw.Draw(final_img)

        # Try to use a nice font, fall back to default
        try:
            font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 36)
        except:
            try:
                font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 36)
            except:
                font = ImageFont.load_default()

        # Center text
        bbox = draw.textbbox((0, 0), self.label, font=font)
        text_width = bbox[2] - bbox[0]
        text_x = (qr_img.size[0] - text_width) // 2
        text_y = qr_img.size[1] + 10

        draw.text((text_x, text_y), self.label, fill='black', font=font)

        return final_img

    def generate(self) -> bytes:
        """
        Generate QR code with all styling options

        Returns:
            PNG image bytes
        """
        # Create QR code with high error correction (allows logo embedding)
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,  # 30% redundancy
            box_size=10,
            border=4,
        )
        qr.add_data(self.data)
        qr.make(fit=True)

        # Get module drawer for style
        module_drawer = self.STYLE_DRAWERS.get(self.style, SquareModuleDrawer)()

        # Generate styled QR image
        color_mask = SolidFillColorMask(
            back_color=(255, 255, 255),
            front_color=self._hex_to_rgb(self.primary_color)
        )

        qr_img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=module_drawer,
            color_mask=color_mask
        )

        # Resize to target size
        qr_img = qr_img.resize((self.size, self.size), Image.Resampling.LANCZOS)

        # Apply gradient if secondary color provided
        if self.secondary_color:
            qr_img = self._create_gradient_overlay(qr_img)

        # Embed logo if provided
        if self.logo_path:
            qr_img = self._embed_logo(qr_img)

        # Add label if provided
        if self.label:
            qr_img = self._add_label(qr_img)

        # Convert to bytes
        buffer = io.BytesIO()
        qr_img.save(buffer, format='PNG')
        return buffer.getvalue()

    def generate_animated(self, frames: int = 8, pulse_intensity: float = 0.3) -> bytes:
        """
        Generate animated GIF QR code with pulsing effect

        Each frame is a valid QR code with slightly different styling

        Args:
            frames: Number of animation frames (8-10 recommended)
            pulse_intensity: How much the colors pulse (0.0 to 1.0)

        Returns:
            GIF image bytes
        """
        try:
            import imageio
        except ImportError:
            raise ImportError("imageio required for animated QR codes. Run: pip install imageio")

        frame_images = []

        # Generate frames with color pulsing
        for i in range(frames):
            # Calculate pulse factor (sine wave)
            import math
            pulse = 1.0 + (pulse_intensity * math.sin(2 * math.pi * i / frames))

            # Adjust primary color brightness
            rgb = self._hex_to_rgb(self.primary_color)
            pulsed_rgb = tuple(min(255, int(c * pulse)) for c in rgb)

            # Create QR for this frame
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )
            qr.add_data(self.data)
            qr.make(fit=True)

            module_drawer = self.STYLE_DRAWERS.get(self.style, SquareModuleDrawer)()
            color_mask = SolidFillColorMask(
                back_color=(255, 255, 255),
                front_color=pulsed_rgb
            )

            qr_img = qr.make_image(
                image_factory=StyledPilImage,
                module_drawer=module_drawer,
                color_mask=color_mask
            )

            qr_img = qr_img.resize((self.size, self.size), Image.Resampling.LANCZOS)

            # Apply gradient if secondary color
            if self.secondary_color:
                # Also pulse secondary color
                rgb2 = self._hex_to_rgb(self.secondary_color)
                pulsed_rgb2 = tuple(min(255, int(c * pulse)) for c in rgb2)

                # Temporarily override colors for gradient
                original_primary = self.primary_color
                original_secondary = self.secondary_color
                self.primary_color = '#%02x%02x%02x' % pulsed_rgb
                self.secondary_color = '#%02x%02x%02x' % pulsed_rgb2

                qr_img = self._create_gradient_overlay(qr_img)

                # Restore original colors
                self.primary_color = original_primary
                self.secondary_color = original_secondary

            # Embed logo
            if self.logo_path:
                qr_img = self._embed_logo(qr_img)

            # Add label
            if self.label:
                qr_img = self._add_label(qr_img)

            frame_images.append(qr_img)

        # Create GIF
        buffer = io.BytesIO()
        imageio.mimsave(
            buffer,
            frame_images,
            format='GIF',
            duration=0.15,  # 150ms per frame
            loop=0  # Infinite loop
        )

        return buffer.getvalue()


# Convenience functions
def create_gradient_qr(
    data: str,
    color1: str,
    color2: str,
    style: str = 'rounded',
    label: Optional[str] = None
) -> bytes:
    """Quick function to create gradient QR code"""
    generator = AdvancedQRGenerator(
        data=data,
        style=style,
        primary_color=color1,
        secondary_color=color2,
        label=label
    )
    return generator.generate()


def create_animated_qr(
    data: str,
    color: str,
    style: str = 'rounded',
    label: Optional[str] = None
) -> bytes:
    """Quick function to create animated QR code"""
    generator = AdvancedQRGenerator(
        data=data,
        style=style,
        primary_color=color,
        label=label
    )
    return generator.generate_animated()


def create_logo_qr(
    data: str,
    logo_path: str,
    color: str = '#000000',
    style: str = 'minimal',
    label: Optional[str] = None
) -> bytes:
    """Quick function to create QR with logo"""
    generator = AdvancedQRGenerator(
        data=data,
        style=style,
        primary_color=color,
        logo_path=logo_path,
        label=label
    )
    return generator.generate()
