#!/usr/bin/env python3
"""
API Image Generator - Cloud AI Image Generation (No Local Downloads)

Generate real AI images using cloud APIs instead of local models.
Perfect for users who want AI quality without downloading 4GB models.

Supported APIs:
- Replicate (Stable Diffusion, FLUX)
- Stability AI (Official Stable Diffusion API)
- OpenAI DALL-E 3
- Bing Image Creator (Free, requires cookies)

Usage:
    from api_image_generator import APIImageGenerator

    # Option 1: Replicate (best quality, paid)
    gen = APIImageGenerator(provider='replicate', api_key='r8_...')
    image_bytes = gen.generate_from_text(
        prompt='Professional food photography of butter',
        size=(1024, 768)
    )

    # Option 2: Stability AI (official, paid)
    gen = APIImageGenerator(provider='stability', api_key='sk-...')
    image_bytes = gen.generate_from_text(prompt='...')

    # Option 3: OpenAI DALL-E (paid)
    gen = APIImageGenerator(provider='openai', api_key='sk-...')
    image_bytes = gen.generate_from_text(prompt='...')

    # Option 4: Bing (free, requires cookies)
    gen = APIImageGenerator(provider='bing', cookies='U=xxx...')
    image_bytes = gen.generate_from_text(prompt='...')

Benefits:
- ✅ No 4GB model download
- ✅ Fast generation (API handles it)
- ✅ High quality results
- ✅ No GPU required
- ❌ Costs money (except Bing)
- ❌ Requires internet connection
- ❌ API rate limits

Architecture:
    - Lightweight wrapper around cloud APIs
    - Works with prompt_templates.py for brand-specific prompts
    - Fallback to procedural_media.py if API fails
    - Compatible with qr_image_overlay.py for watermarking
"""

import io
import os
import time
import json
import requests
from typing import Optional, Tuple, Dict
from PIL import Image


# =============================================================================
# API Image Generator
# =============================================================================

class APIImageGenerator:
    """
    Generate images using cloud AI APIs (no local model download)

    Example:
        >>> gen = APIImageGenerator(provider='replicate', api_key='r8_...')
        >>> image_bytes = gen.generate_from_text('food photography of butter')
    """

    def __init__(
        self,
        provider: str = 'replicate',
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        """
        Initialize API image generator

        Args:
            provider: API provider ('replicate', 'stability', 'openai', 'bing')
            api_key: API key for the provider (required for paid APIs)
            model: Optional specific model to use

        Raises:
            ValueError: If provider is invalid or API key is missing
        """
        self.provider = provider.lower()
        self.api_key = api_key or os.environ.get(f'{provider.upper()}_API_KEY')
        self.model = model

        # Validate provider
        valid_providers = ['replicate', 'stability', 'openai', 'bing']
        if self.provider not in valid_providers:
            raise ValueError(f"Provider must be one of {valid_providers}")

        # Check API key for paid providers
        if self.provider in ['replicate', 'stability', 'openai'] and not self.api_key:
            raise ValueError(f"API key required for {self.provider}. "
                           f"Set {provider.upper()}_API_KEY environment variable or pass api_key.")

        # Set default models
        if not self.model:
            self.model = self._get_default_model()

        self.available = True

    def _get_default_model(self) -> str:
        """Get default model for provider"""
        defaults = {
            'replicate': 'stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b',
            'stability': 'stable-diffusion-v1-6',
            'openai': 'dall-e-3',
            'bing': 'bing-image-creator'
        }
        return defaults.get(self.provider, 'default')

    def generate_from_text(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        size: Tuple[int, int] = (1024, 1024),
        num_steps: int = 25,
        guidance_scale: float = 7.5,
        **kwargs
    ) -> bytes:
        """
        Generate image from text prompt using API

        Args:
            prompt: Text description of image to generate
            negative_prompt: Things to avoid in the image
            size: Image size (width, height)
            num_steps: Number of inference steps (quality)
            guidance_scale: How closely to follow prompt (higher = more literal)
            **kwargs: Provider-specific parameters

        Returns:
            Image as PNG bytes

        Example:
            >>> gen = APIImageGenerator(provider='replicate', api_key='r8_...')
            >>> image_bytes = gen.generate_from_text(
            ...     prompt='Professional food photography of butter',
            ...     size=(1200, 800),
            ...     num_steps=30
            ... )
        """
        if self.provider == 'replicate':
            return self._generate_replicate(prompt, negative_prompt, size, num_steps, guidance_scale, **kwargs)
        elif self.provider == 'stability':
            return self._generate_stability(prompt, negative_prompt, size, num_steps, guidance_scale, **kwargs)
        elif self.provider == 'openai':
            return self._generate_openai(prompt, size, **kwargs)
        elif self.provider == 'bing':
            return self._generate_bing(prompt, size, **kwargs)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    # =========================================================================
    # Replicate API
    # =========================================================================

    def _generate_replicate(
        self,
        prompt: str,
        negative_prompt: Optional[str],
        size: Tuple[int, int],
        num_steps: int,
        guidance_scale: float,
        **kwargs
    ) -> bytes:
        """
        Generate image using Replicate API

        Docs: https://replicate.com/stability-ai/sdxl
        """
        import replicate

        # Set API token
        os.environ['REPLICATE_API_TOKEN'] = self.api_key

        # Prepare inputs
        width, height = size
        inputs = {
            'prompt': prompt,
            'width': width,
            'height': height,
            'num_inference_steps': num_steps,
            'guidance_scale': guidance_scale,
            **kwargs
        }

        if negative_prompt:
            inputs['negative_prompt'] = negative_prompt

        # Run model
        output = replicate.run(self.model, input=inputs)

        # Download image from URL
        if isinstance(output, list):
            image_url = output[0]
        else:
            image_url = output

        response = requests.get(image_url)
        response.raise_for_status()

        return response.content

    # =========================================================================
    # Stability AI API
    # =========================================================================

    def _generate_stability(
        self,
        prompt: str,
        negative_prompt: Optional[str],
        size: Tuple[int, int],
        num_steps: int,
        guidance_scale: float,
        **kwargs
    ) -> bytes:
        """
        Generate image using Stability AI API

        Docs: https://platform.stability.ai/docs/api-reference
        """
        width, height = size

        # API endpoint
        url = f"https://api.stability.ai/v1/generation/{self.model}/text-to-image"

        # Headers
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        # Request body
        body = {
            'text_prompts': [
                {'text': prompt, 'weight': 1.0}
            ],
            'cfg_scale': guidance_scale,
            'height': height,
            'width': width,
            'steps': num_steps,
            'samples': 1,
            **kwargs
        }

        if negative_prompt:
            body['text_prompts'].append({'text': negative_prompt, 'weight': -1.0})

        # Make request
        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()

        # Parse response
        data = response.json()
        image_b64 = data['artifacts'][0]['base64']

        # Decode base64
        import base64
        return base64.b64decode(image_b64)

    # =========================================================================
    # OpenAI DALL-E API
    # =========================================================================

    def _generate_openai(
        self,
        prompt: str,
        size: Tuple[int, int],
        **kwargs
    ) -> bytes:
        """
        Generate image using OpenAI DALL-E API

        Docs: https://platform.openai.com/docs/guides/images
        """
        from openai import OpenAI

        client = OpenAI(api_key=self.api_key)

        # DALL-E supports specific sizes
        width, height = size
        if width == height == 1024:
            size_str = "1024x1024"
        elif width == 1792 and height == 1024:
            size_str = "1792x1024"
        elif width == 1024 and height == 1792:
            size_str = "1024x1792"
        else:
            # Default to square
            size_str = "1024x1024"

        # Generate image
        response = client.images.generate(
            model=self.model,
            prompt=prompt,
            size=size_str,
            quality=kwargs.get('quality', 'standard'),
            n=1
        )

        # Download image
        image_url = response.data[0].url
        img_response = requests.get(image_url)
        img_response.raise_for_status()

        return img_response.content

    # =========================================================================
    # Bing Image Creator (Free)
    # =========================================================================

    def _generate_bing(
        self,
        prompt: str,
        size: Tuple[int, int],
        **kwargs
    ) -> bytes:
        """
        Generate image using Bing Image Creator (free)

        Requires: pip install BingImageCreator

        Note: Requires cookies from logged-in Bing session
        Get cookies: https://www.bing.com/images/create
        """
        try:
            from BingImageCreator import ImageGen
        except ImportError:
            raise ImportError("BingImageCreator not installed. Install with: pip install BingImageCreator")

        # Cookies from environment or parameter
        cookies = kwargs.get('cookies') or os.environ.get('BING_COOKIES') or self.api_key

        if not cookies:
            raise ValueError("Bing requires cookies. Set BING_COOKIES environment variable or pass cookies parameter.")

        # Initialize Bing
        image_generator = ImageGen(auth_cookie=cookies)

        # Generate images
        images = image_generator.get_images(prompt)

        if not images:
            raise RuntimeError("Bing Image Creator failed to generate images")

        # Download first image
        image_url = images[0]
        response = requests.get(image_url)
        response.raise_for_status()

        image_bytes = response.content

        # Resize if needed
        if size != (1024, 1024):
            img = Image.open(io.BytesIO(image_bytes))
            img = img.resize(size, Image.LANCZOS)
            output = io.BytesIO()
            img.save(output, format='PNG')
            return output.getvalue()

        return image_bytes


# =============================================================================
# Fallback Integration
# =============================================================================

def generate_with_fallback(
    prompt: str,
    provider: str = 'replicate',
    api_key: Optional[str] = None,
    size: Tuple[int, int] = (1024, 1024),
    **kwargs
) -> bytes:
    """
    Generate image with automatic fallback to procedural if API fails

    Args:
        prompt: Text description
        provider: API provider
        api_key: API key
        size: Image size
        **kwargs: Additional parameters

    Returns:
        Image bytes (API or procedural fallback)

    Example:
        >>> image_bytes = generate_with_fallback(
        ...     prompt='Professional food photography of butter',
        ...     provider='replicate',
        ...     api_key='r8_...'
        ... )
    """
    try:
        # Try API generation
        gen = APIImageGenerator(provider=provider, api_key=api_key)
        return gen.generate_from_text(prompt=prompt, size=size, **kwargs)

    except Exception as e:
        print(f"⚠️  API generation failed: {e}")
        print(f"   Falling back to procedural generation...")

        # Fallback to procedural
        from procedural_media import ProceduralMediaGenerator

        gen = ProceduralMediaGenerator()

        # Extract keywords from prompt
        keywords = [word for word in prompt.split() if len(word) > 3][:5]

        return gen.generate_hero_image(
            keywords=keywords,
            size=size,
            style='xkcd'  # XKCD style for fallback
        )


# =============================================================================
# CLI Testing
# =============================================================================

if __name__ == '__main__':
    """
    Test API image generation

    Usage:
        # Test with Replicate (requires API key)
        export REPLICATE_API_KEY='r8_...'
        python3 api_image_generator.py

        # Test with Stability AI
        export STABILITY_API_KEY='sk-...'
        python3 api_image_generator.py --provider stability

        # Test fallback (no API key)
        python3 api_image_generator.py --fallback
    """
    import sys
    import argparse

    parser = argparse.ArgumentParser(description='Test API image generation')
    parser.add_argument('--provider', default='replicate', choices=['replicate', 'stability', 'openai', 'bing'])
    parser.add_argument('--prompt', default='Professional food photography of salted butter on rustic wooden table')
    parser.add_argument('--size', type=int, nargs=2, default=[800, 600], metavar=('WIDTH', 'HEIGHT'))
    parser.add_argument('--output', default='api_test.png')
    parser.add_argument('--fallback', action='store_true', help='Test fallback to procedural')

    args = parser.parse_args()

    print("=" * 70)
    print("🌐 API Image Generator Test")
    print("=" * 70)
    print()

    if args.fallback:
        print("Testing fallback mode (no API)...")
        print("-" * 70)
        print()

        image_bytes = generate_with_fallback(
            prompt=args.prompt,
            provider=args.provider,
            api_key=None,  # Force fallback
            size=tuple(args.size)
        )

        with open(args.output, 'wb') as f:
            f.write(image_bytes)

        print(f"✅ Fallback image generated: {args.output}")
        print(f"   Size: {len(image_bytes):,} bytes")
        print()

    else:
        print(f"Provider: {args.provider}")
        print(f"Prompt: {args.prompt}")
        print(f"Size: {args.size[0]}x{args.size[1]}")
        print("-" * 70)
        print()

        # Get API key
        api_key = os.environ.get(f'{args.provider.upper()}_API_KEY')

        if not api_key:
            print(f"❌ No API key found")
            print(f"   Set {args.provider.upper()}_API_KEY environment variable")
            print()
            print("Example:")
            print(f"  export {args.provider.upper()}_API_KEY='your-key-here'")
            print(f"  python3 api_image_generator.py --provider {args.provider}")
            print()
            print("Or test fallback mode:")
            print("  python3 api_image_generator.py --fallback")
            sys.exit(1)

        try:
            # Initialize generator
            gen = APIImageGenerator(provider=args.provider, api_key=api_key)

            print(f"🎨 Generating image via {args.provider} API...")
            print()

            # Generate image
            start_time = time.time()

            image_bytes = gen.generate_from_text(
                prompt=args.prompt,
                size=tuple(args.size),
                num_steps=25,
                guidance_scale=7.5
            )

            elapsed = time.time() - start_time

            # Save image
            with open(args.output, 'wb') as f:
                f.write(image_bytes)

            print(f"✅ Image generated successfully!")
            print(f"   Output: {args.output}")
            print(f"   Size: {len(image_bytes):,} bytes")
            print(f"   Time: {elapsed:.1f} seconds")
            print()

        except Exception as e:
            print(f"❌ Generation failed: {e}")
            print()
            import traceback
            traceback.print_exc()
            sys.exit(1)

    print("=" * 70)
    print("✅ API Image Generator Ready")
    print()
    print("Usage:")
    print("  from api_image_generator import APIImageGenerator")
    print()
    print("  gen = APIImageGenerator(provider='replicate', api_key='r8_...')")
    print("  image_bytes = gen.generate_from_text(prompt='...')")
    print()
    print("Supported providers: replicate, stability, openai, bing")
    print("=" * 70)
