#!/usr/bin/env python3
"""
AI Image Generator - Stable Diffusion Integration

Real neural network-based image generation using Stable Diffusion 3.5.
Replaces procedural Pillow shapes with actual AI-generated images.

Features:
- Text-to-image generation
- Image-to-image (style transfer)
- Brand color integration
- Local/self-hosted (no cloud APIs)
- Graceful degradation (falls back to procedural if GPU unavailable)

Requirements:
- torch, diffusers, transformers (see requirements.txt)
- ~4-6GB download first time (SD model)
- ~6-8GB RAM recommended (less with quantization)
- GPU optional (CPU works but slower)

Philosophy:
It's 2025. We shouldn't be generating colored shapes.
We should be generating real AI art like "nano banana".
"""

import io
import os
import hashlib
from typing import List, Optional, Tuple
from PIL import Image


class AIImageGenerator:
    """
    Stable Diffusion image generator with brand integration

    Usage:
        gen = AIImageGenerator()
        image_bytes = gen.generate_from_text(
            prompt="vibrant cooking ingredients on wooden table",
            brand_colors=['#FF6B35', '#F7931E'],
            size=(1200, 600)
        )
    """

    def __init__(self, model_id: str = "stabilityai/stable-diffusion-3.5-large", device: str = "auto"):
        """
        Initialize AI image generator

        Args:
            model_id: Hugging Face model ID (default: SD 3.5 large)
            device: Device to use ('auto', 'cuda', 'cpu')
        """
        self.model_id = model_id
        self.device = self._detect_device() if device == "auto" else device
        self.pipeline = None  # Lazy loading
        self.available = self._check_dependencies()

        print(f"🎨 AI Image Generator initialized")
        print(f"   Device: {self.device}")
        print(f"   Model: {model_id}")
        print(f"   Available: {self.available}")

        if not self.available:
            print(f"   ⚠️  PyTorch/diffusers not installed - will use fallback")

    def _check_dependencies(self) -> bool:
        """Check if required dependencies are installed"""
        try:
            import torch
            import diffusers
            return True
        except ImportError:
            return False

    def _detect_device(self) -> str:
        """Detect best available device (CUDA > MPS > CPU)"""
        try:
            import torch

            if torch.cuda.is_available():
                return "cuda"
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                return "mps"  # Apple Silicon
            else:
                return "cpu"
        except ImportError:
            return "cpu"

    def _load_pipeline(self):
        """Lazy load the Stable Diffusion pipeline"""
        if self.pipeline is not None:
            return  # Already loaded

        if not self.available:
            raise RuntimeError("PyTorch/diffusers not installed. Install with: pip install -r requirements.txt")

        print(f"📥 Loading Stable Diffusion model (first time: ~4-6GB download)...")

        try:
            import torch
            from diffusers import StableDiffusion3Pipeline

            # Determine dtype based on device
            if self.device == "cuda":
                torch_dtype = torch.float16  # Use FP16 on CUDA
            elif self.device == "mps":
                torch_dtype = torch.float32  # MPS doesn't support FP16 well
            else:
                torch_dtype = torch.float32  # CPU uses FP32

            # Load pipeline
            self.pipeline = StableDiffusion3Pipeline.from_pretrained(
                self.model_id,
                torch_dtype=torch_dtype
            )

            # Move to device
            self.pipeline = self.pipeline.to(self.device)

            # Enable memory optimizations
            if self.device == "cuda":
                self.pipeline.enable_attention_slicing()
                self.pipeline.enable_vae_slicing()

            print(f"   ✅ Model loaded successfully")

        except Exception as e:
            print(f"   ❌ Failed to load model: {e}")
            raise

    def generate_from_text(
        self,
        prompt: str,
        brand_colors: Optional[List[str]] = None,
        size: Tuple[int, int] = (1024, 1024),
        negative_prompt: Optional[str] = None,
        num_steps: int = 28,
        guidance_scale: float = 7.0
    ) -> bytes:
        """
        Generate image from text prompt

        Args:
            prompt: Text description of desired image
            brand_colors: Optional brand colors to incorporate (hex codes)
            size: Image size (width, height) - must be multiples of 8
            negative_prompt: Things to avoid in the image
            num_steps: Number of denoising steps (more = better quality, slower)
            guidance_scale: How closely to follow prompt (7-9 recommended)

        Returns:
            PNG image bytes
        """
        # Ensure model is loaded
        self._load_pipeline()

        # Enhance prompt with brand colors if provided
        enhanced_prompt = self._enhance_prompt_with_colors(prompt, brand_colors)

        # Default negative prompt
        if negative_prompt is None:
            negative_prompt = "blurry, low quality, distorted, ugly, bad anatomy"

        print(f"🎨 Generating image...")
        print(f"   Prompt: {enhanced_prompt[:100]}...")
        print(f"   Size: {size}")
        print(f"   Steps: {num_steps}")

        try:
            import torch

            # Generate image
            with torch.no_grad():
                result = self.pipeline(
                    prompt=enhanced_prompt,
                    negative_prompt=negative_prompt,
                    height=size[1],
                    width=size[0],
                    num_inference_steps=num_steps,
                    guidance_scale=guidance_scale
                )

            # Get image
            image = result.images[0]

            # Convert to bytes
            img_bytes = io.BytesIO()
            image.save(img_bytes, format='PNG')
            image_bytes = img_bytes.getvalue()

            print(f"   ✅ Generated ({len(image_bytes):,} bytes)")

            return image_bytes

        except Exception as e:
            print(f"   ❌ Generation failed: {e}")
            raise

    def generate_from_image(
        self,
        image: Image.Image,
        prompt: str,
        strength: float = 0.75,
        brand_colors: Optional[List[str]] = None
    ) -> bytes:
        """
        Generate image from existing image (style transfer)

        Args:
            image: Input PIL Image
            prompt: Text description of transformation
            strength: How much to transform (0-1, higher = more change)
            brand_colors: Optional brand colors to incorporate

        Returns:
            PNG image bytes
        """
        # Note: Requires StableDiffusionImg2ImgPipeline
        # For now, just do text-to-image
        # TODO: Implement img2img pipeline

        enhanced_prompt = self._enhance_prompt_with_colors(prompt, brand_colors)
        return self.generate_from_text(enhanced_prompt, brand_colors=brand_colors)

    def batch_generate(
        self,
        prompts: List[str],
        brand_colors: Optional[List[str]] = None,
        size: Tuple[int, int] = (1024, 1024)
    ) -> List[bytes]:
        """
        Generate multiple images at once

        Args:
            prompts: List of text prompts
            brand_colors: Optional brand colors
            size: Image size

        Returns:
            List of PNG image bytes
        """
        results = []

        for i, prompt in enumerate(prompts):
            print(f"📸 Generating {i+1}/{len(prompts)}...")
            image_bytes = self.generate_from_text(prompt, brand_colors=brand_colors, size=size)
            results.append(image_bytes)

        return results

    def _enhance_prompt_with_colors(self, prompt: str, brand_colors: Optional[List[str]]) -> str:
        """Enhance prompt with brand color information"""
        if not brand_colors:
            return prompt

        # Convert hex colors to color names (simple mapping)
        color_descriptions = []
        for hex_color in brand_colors[:3]:  # Max 3 colors
            desc = self._hex_to_color_description(hex_color)
            if desc:
                color_descriptions.append(desc)

        if color_descriptions:
            color_text = ", ".join(color_descriptions)
            enhanced = f"{prompt}, with {color_text} color palette"
            return enhanced

        return prompt

    def _hex_to_color_description(self, hex_color: str) -> Optional[str]:
        """Convert hex color to descriptive text"""
        # Simple color mapping
        hex_color = hex_color.lstrip('#').lower()

        # RGB extraction
        try:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)

            # Determine dominant color
            if r > g and r > b:
                if r > 200:
                    return "vibrant red"
                elif r > 150:
                    return "warm orange"
                else:
                    return "deep red"
            elif g > r and g > b:
                if g > 200:
                    return "bright green"
                elif g > 150:
                    return "fresh green"
                else:
                    return "deep green"
            elif b > r and b > g:
                if b > 200:
                    return "bright blue"
                elif b > 150:
                    return "ocean blue"
                else:
                    return "deep blue"
            else:
                # Grayscale or mixed
                avg = (r + g + b) // 3
                if avg > 200:
                    return "bright"
                elif avg > 100:
                    return "neutral"
                else:
                    return "dark"
        except:
            return None


def generate_fallback_image(
    keywords: List[str],
    brand_colors: List[str],
    size: Tuple[int, int] = (1200, 600)
) -> bytes:
    """
    Fallback to procedural image generation

    Used when PyTorch/Stable Diffusion is unavailable

    Args:
        keywords: Keywords for image theme
        brand_colors: Brand colors (hex codes)
        size: Image size

    Returns:
        PNG image bytes
    """
    try:
        # Try to use existing procedural generator
        from procedural_media import ProceduralMediaGenerator

        generator = ProceduralMediaGenerator()
        return generator.generate_hero_image(
            keywords=keywords,
            brand_colors=brand_colors,
            size=size
        )
    except Exception as e:
        print(f"⚠️  Fallback failed: {e}")

        # Ultimate fallback: solid color
        from PIL import Image, ImageDraw
        import io

        img = Image.new('RGB', size, color=brand_colors[0] if brand_colors else '#FF6B35')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        return img_bytes.getvalue()


if __name__ == '__main__':
    """Test the AI image generator"""

    print("=" * 70)
    print("🎨 AI Image Generator Test")
    print("=" * 70)
    print()

    # Initialize generator
    gen = AIImageGenerator()

    if not gen.available:
        print("⚠️  PyTorch/diffusers not installed.")
        print("Install with: pip install -r requirements.txt")
        print()
        print("Testing fallback mode...")

        fallback_bytes = generate_fallback_image(
            keywords=['cooking', 'food', 'kitchen'],
            brand_colors=['#FF6B35', '#F7931E'],
            size=(512, 512)
        )

        print(f"✅ Fallback generated: {len(fallback_bytes):,} bytes")
    else:
        print("Testing AI generation...")
        print()

        # Test generation
        image_bytes = gen.generate_from_text(
            prompt="vibrant cooking ingredients on a wooden table, professional food photography",
            brand_colors=['#FF6B35', '#F7931E'],
            size=(512, 512),  # Small for testing
            num_steps=20  # Fewer steps for speed
        )

        # Save test image
        with open('test_ai_generated.png', 'wb') as f:
            f.write(image_bytes)

        print()
        print(f"✅ Test complete!")
        print(f"   Generated: {len(image_bytes):,} bytes")
        print(f"   Saved to: test_ai_generated.png")
