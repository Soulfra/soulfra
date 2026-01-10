#!/usr/bin/env python3
"""
OCR Text Extractor - Extract Text from Images

Extract text from images using EasyOCR for training datasets and content analysis.

Features:
- Extract text from local images
- Extract from URLs (download + OCR)
- Build training datasets by scraping images
- Support 80+ languages
- CPU-based (no GPU required)

Requirements:
- easyocr (see requirements.txt)
- Downloads language models on first run (~100MB per language)

Use Cases:
- Extract text from scraped web images
- Build training datasets from image URLs
- Analyze image content for AI training
- OCR for accessibility features
"""

import io
import os
import urllib.request
from typing import List, Dict, Optional, Tuple
from PIL import Image


class OCRExtractor:
    """
    Extract text from images using EasyOCR

    Usage:
        ocr = OCRExtractor()
        text = ocr.extract_text('image.jpg')
        text = ocr.extract_from_url('https://example.com/image.jpg')
    """

    def __init__(self, languages: List[str] = ['en']):
        """
        Initialize OCR extractor

        Args:
            languages: List of language codes (default: English only)
                      Common: 'en', 'es', 'fr', 'de', 'zh', 'ja', 'ko'
        """
        self.languages = languages
        self.reader = None  # Lazy loading
        self.available = self._check_dependencies()

        print(f"📖 OCR Extractor initialized")
        print(f"   Languages: {', '.join(languages)}")
        print(f"   Available: {self.available}")

        if not self.available:
            print(f"   ⚠️  EasyOCR not installed - OCR unavailable")

    def _check_dependencies(self) -> bool:
        """Check if EasyOCR is installed"""
        try:
            import easyocr
            return True
        except ImportError:
            return False

    def _load_reader(self):
        """Lazy load the EasyOCR reader"""
        if self.reader is not None:
            return  # Already loaded

        if not self.available:
            raise RuntimeError("EasyOCR not installed. Install with: pip install easyocr")

        print(f"📥 Loading EasyOCR (first time: downloads language models ~100MB)...")

        try:
            import easyocr

            # Create reader
            self.reader = easyocr.Reader(
                self.languages,
                gpu=False  # Use CPU (more compatible)
            )

            print(f"   ✅ OCR reader loaded")

        except Exception as e:
            print(f"   ❌ Failed to load OCR reader: {e}")
            raise

    def extract_text(self, image_path: str, detail: int = 0) -> str:
        """
        Extract text from local image file

        Args:
            image_path: Path to image file
            detail: Detail level (0=simple text, 1=with confidence, 2=with coordinates)

        Returns:
            Extracted text
        """
        # Ensure reader is loaded
        self._load_reader()

        print(f"📖 Extracting text from: {image_path}")

        try:
            # Read image
            results = self.reader.readtext(image_path)

            # Format results based on detail level
            if detail == 0:
                # Simple: just text
                text = ' '.join([result[1] for result in results])
                return text.strip()
            elif detail == 1:
                # With confidence scores
                lines = []
                for bbox, text, confidence in results:
                    lines.append(f"{text} ({confidence:.2f})")
                return '\n'.join(lines)
            else:
                # With coordinates
                lines = []
                for bbox, text, confidence in results:
                    coords = f"({bbox[0][0]:.0f},{bbox[0][1]:.0f})"
                    lines.append(f"{coords}: {text} ({confidence:.2f})")
                return '\n'.join(lines)

        except Exception as e:
            print(f"   ❌ Extraction failed: {e}")
            raise

    def extract_from_url(self, url: str, detail: int = 0) -> str:
        """
        Extract text from image URL

        Args:
            url: URL to image
            detail: Detail level (0=simple, 1=with confidence, 2=with coords)

        Returns:
            Extracted text
        """
        print(f"📥 Downloading image from: {url}")

        try:
            # Download image
            with urllib.request.urlopen(url, timeout=10) as response:
                image_data = response.read()

            # Save to temporary file
            temp_path = '/tmp/ocr_temp_image.jpg'
            with open(temp_path, 'wb') as f:
                f.write(image_data)

            # Extract text
            text = self.extract_text(temp_path, detail=detail)

            # Clean up
            os.remove(temp_path)

            return text

        except Exception as e:
            print(f"   ❌ Failed to process URL: {e}")
            raise

    def extract_from_bytes(self, image_bytes: bytes, detail: int = 0) -> str:
        """
        Extract text from image bytes

        Args:
            image_bytes: Image data as bytes
            detail: Detail level

        Returns:
            Extracted text
        """
        # Save to temporary file
        temp_path = '/tmp/ocr_temp_image.jpg'

        try:
            with open(temp_path, 'wb') as f:
                f.write(image_bytes)

            text = self.extract_text(temp_path, detail=detail)

            os.remove(temp_path)

            return text

        except Exception as e:
            print(f"   ❌ Failed to process bytes: {e}")
            raise

    def build_dataset_from_urls(
        self,
        urls: List[str],
        output_dir: str = 'datasets/scraped_images'
    ) -> List[Dict[str, str]]:
        """
        Build training dataset by scraping images from URLs

        Args:
            urls: List of image URLs
            output_dir: Directory to save images and text

        Returns:
            List of dicts with {'image_path', 'text', 'url'}
        """
        os.makedirs(output_dir, exist_ok=True)

        dataset = []

        print(f"🔍 Building dataset from {len(urls)} URLs...")
        print(f"   Saving to: {output_dir}")
        print()

        for i, url in enumerate(urls):
            print(f"   [{i+1}/{len(urls)}] Processing {url[:60]}...")

            try:
                # Download image
                with urllib.request.urlopen(url, timeout=10) as response:
                    image_data = response.read()

                # Save image
                image_filename = f"image_{i:04d}.jpg"
                image_path = os.path.join(output_dir, image_filename)

                with open(image_path, 'wb') as f:
                    f.write(image_data)

                # Extract text
                text = self.extract_text(image_path, detail=0)

                # Save text
                text_filename = f"image_{i:04d}.txt"
                text_path = os.path.join(output_dir, text_filename)

                with open(text_path, 'w', encoding='utf-8') as f:
                    f.write(text)

                # Add to dataset
                dataset.append({
                    'image_path': image_path,
                    'text': text,
                    'url': url
                })

                print(f"      ✅ Saved: {len(text)} chars extracted")

            except Exception as e:
                print(f"      ⚠️  Failed: {e}")
                continue

        print()
        print(f"✅ Dataset complete: {len(dataset)} images")

        return dataset

    def batch_extract(self, image_paths: List[str]) -> List[Tuple[str, str]]:
        """
        Extract text from multiple images

        Args:
            image_paths: List of image file paths

        Returns:
            List of tuples (image_path, extracted_text)
        """
        results = []

        for i, path in enumerate(image_paths):
            print(f"   [{i+1}/{len(image_paths)}] {path}")

            try:
                text = self.extract_text(path, detail=0)
                results.append((path, text))
            except Exception as e:
                print(f"      ⚠️  Failed: {e}")
                results.append((path, ""))

        return results


if __name__ == '__main__':
    """Test OCR extractor"""

    print("=" * 70)
    print("📖 OCR Extractor Test")
    print("=" * 70)
    print()

    # Initialize
    ocr = OCRExtractor()

    if not ocr.available:
        print("⚠️  EasyOCR not installed.")
        print("Install with: pip install easyocr")
        print()
    else:
        print("Testing OCR extraction...")
        print()

        # Test with a sample image URL (if available)
        test_url = "https://via.placeholder.com/300x150.png?text=Hello+World"

        try:
            text = ocr.extract_from_url(test_url)
            print(f"✅ Extracted text: '{text}'")
        except Exception as e:
            print(f"⚠️  Test failed: {e}")
            print("   (This is normal if no internet connection)")

        print()
        print("✅ OCR extractor ready")
