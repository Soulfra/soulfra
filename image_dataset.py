#!/usr/bin/env python3
"""
Image Dataset - PyTorch Dataset for Image Management

PyTorch Dataset implementation following the tutorial pattern from:
https://docs.pytorch.org/tutorials/beginner/basics/data_tutorial.html

Features:
- Load images from database BLOBs
- Load from URLs with metadata
- Training data preparation
- Visualization support
- Follows PyTorch __init__, __len__, __getitem__ pattern

Use Cases:
- Train custom Stable Diffusion models
- Fine-tune on brand-specific imagery
- Build datasets from scraped images
- Iterate and visualize like Fashion-MNIST tutorial
"""

import io
import os
import sqlite3
from typing import List, Dict, Optional, Tuple, Callable
from PIL import Image


class SoulImageDataset:
    """
    PyTorch-compatible dataset for Soulfra images

    Follows the standard PyTorch Dataset pattern:
    - __init__: Initialize dataset attributes
    - __len__: Return number of samples
    - __getitem__: Retrieve and transform individual samples

    Usage:
        from torch.utils.data import DataLoader

        dataset = SoulImageDataset(brand_slug='howtocookathome')
        dataloader = DataLoader(dataset, batch_size=4, shuffle=True)

        for images, labels in dataloader:
            # Train model
            pass
    """

    def __init__(
        self,
        db_path: str = 'soulfra.db',
        brand_slug: Optional[str] = None,
        transform: Optional[Callable] = None,
        target_transform: Optional[Callable] = None
    ):
        """
        Initialize dataset

        Args:
            db_path: Path to SQLite database
            brand_slug: Filter by brand (optional, None = all brands)
            transform: Transform to apply to images
            target_transform: Transform to apply to labels
        """
        self.db_path = db_path
        self.brand_slug = brand_slug
        self.transform = transform
        self.target_transform = target_transform

        # Load image metadata
        self.images = self._load_image_metadata()

        print(f"📦 Dataset initialized")
        print(f"   Database: {db_path}")
        print(f"   Brand: {brand_slug or 'all'}")
        print(f"   Images: {len(self.images)}")

    def _load_image_metadata(self) -> List[Dict]:
        """Load image metadata from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row

            # Build query
            if self.brand_slug:
                # Filter by brand (if images table has brand_id reference)
                query = """
                    SELECT
                        i.id,
                        i.hash,
                        i.mime_type,
                        i.width,
                        i.height,
                        i.metadata,
                        i.created_at
                    FROM images i
                    WHERE json_extract(i.metadata, '$.brand_slug') = ?
                    ORDER BY i.created_at DESC
                """
                cursor = conn.execute(query, (self.brand_slug,))
            else:
                # All images
                query = """
                    SELECT
                        id,
                        hash,
                        mime_type,
                        width,
                        height,
                        metadata,
                        created_at
                    FROM images
                    ORDER BY created_at DESC
                """
                cursor = conn.execute(query)

            images = [dict(row) for row in cursor.fetchall()]
            conn.close()

            return images

        except Exception as e:
            print(f"⚠️  Failed to load images: {e}")
            return []

    def __len__(self) -> int:
        """Return number of samples in dataset"""
        return len(self.images)

    def __getitem__(self, idx: int) -> Tuple[Image.Image, Dict]:
        """
        Retrieve sample by index

        Args:
            idx: Sample index

        Returns:
            Tuple of (image, label)
            - image: PIL Image
            - label: Dict with metadata
        """
        if idx >= len(self.images):
            raise IndexError(f"Index {idx} out of range (dataset has {len(self.images)} images)")

        # Get metadata
        image_meta = self.images[idx]

        # Load image from database
        image = self._load_image_from_db(image_meta['hash'])

        # Create label dict
        label = {
            'id': image_meta['id'],
            'hash': image_meta['hash'],
            'width': image_meta['width'],
            'height': image_meta['height'],
            'metadata': image_meta.get('metadata', '{}')
        }

        # Apply transforms
        if self.transform:
            image = self.transform(image)

        if self.target_transform:
            label = self.target_transform(label)

        return image, label

    def _load_image_from_db(self, image_hash: str) -> Image.Image:
        """Load image bytes from database and convert to PIL Image"""
        try:
            conn = sqlite3.connect(self.db_path)

            cursor = conn.execute(
                'SELECT data FROM images WHERE hash = ?',
                (image_hash,)
            )

            row = cursor.fetchone()
            conn.close()

            if row is None:
                raise ValueError(f"Image not found: {image_hash}")

            # Convert bytes to PIL Image
            image_bytes = row[0]
            image = Image.open(io.BytesIO(image_bytes))

            return image

        except Exception as e:
            print(f"⚠️  Failed to load image {image_hash}: {e}")
            # Return placeholder image
            return Image.new('RGB', (256, 256), color='gray')

    def visualize_samples(self, num_samples: int = 9, save_path: Optional[str] = None):
        """
        Visualize dataset samples in a grid

        Like the Fashion-MNIST tutorial visualization

        Args:
            num_samples: Number of samples to show (must be perfect square)
            save_path: Optional path to save visualization
        """
        try:
            import matplotlib.pyplot as plt
            import math

            # Calculate grid size
            grid_size = int(math.sqrt(num_samples))
            if grid_size * grid_size != num_samples:
                grid_size = int(math.ceil(math.sqrt(num_samples)))

            # Create figure
            fig, axes = plt.subplots(grid_size, grid_size, figsize=(12, 12))
            fig.suptitle(f'Dataset Samples (Brand: {self.brand_slug or "all"})', fontsize=16)

            # Flatten axes for easier iteration
            if grid_size == 1:
                axes = [axes]
            else:
                axes = axes.flatten()

            # Plot samples
            for i in range(grid_size * grid_size):
                ax = axes[i]

                if i < len(self):
                    # Get sample
                    image, label = self[i]

                    # Display
                    ax.imshow(image)
                    ax.axis('off')
                    ax.set_title(f"{label['width']}x{label['height']}", fontsize=8)
                else:
                    # Empty plot
                    ax.axis('off')

            plt.tight_layout()

            if save_path:
                plt.savefig(save_path)
                print(f"✅ Visualization saved to: {save_path}")
            else:
                plt.show()

        except ImportError:
            print("⚠️  matplotlib not installed. Install with: pip install matplotlib")
        except Exception as e:
            print(f"⚠️  Visualization failed: {e}")


class URLImageDataset:
    """
    Dataset from image URLs (for scraping/training)

    Like SoulImageDataset but loads from URLs instead of database

    Usage:
        urls = ['https://example.com/img1.jpg', 'https://example.com/img2.jpg']
        dataset = URLImageDataset(urls)

        for image, label in dataset:
            # Process image
            pass
    """

    def __init__(
        self,
        urls: List[str],
        labels: Optional[List[str]] = None,
        transform: Optional[Callable] = None,
        cache_dir: str = 'datasets/url_cache'
    ):
        """
        Initialize URL dataset

        Args:
            urls: List of image URLs
            labels: Optional labels for each URL
            transform: Transform to apply to images
            cache_dir: Directory to cache downloaded images
        """
        self.urls = urls
        self.labels = labels or [f"image_{i}" for i in range(len(urls))]
        self.transform = transform
        self.cache_dir = cache_dir

        # Create cache directory
        os.makedirs(cache_dir, exist_ok=True)

        print(f"📦 URL Dataset initialized")
        print(f"   URLs: {len(urls)}")
        print(f"   Cache: {cache_dir}")

    def __len__(self) -> int:
        """Return number of samples"""
        return len(self.urls)

    def __getitem__(self, idx: int) -> Tuple[Image.Image, str]:
        """
        Retrieve sample by index

        Downloads image from URL if not cached

        Args:
            idx: Sample index

        Returns:
            Tuple of (image, label)
        """
        if idx >= len(self.urls):
            raise IndexError(f"Index {idx} out of range")

        url = self.urls[idx]
        label = self.labels[idx]

        # Load or download image
        image = self._load_or_download(url, idx)

        # Apply transform
        if self.transform:
            image = self.transform(image)

        return image, label

    def _load_or_download(self, url: str, idx: int) -> Image.Image:
        """Load from cache or download from URL"""
        import urllib.request
        import hashlib

        # Create cache filename from URL hash
        url_hash = hashlib.md5(url.encode()).hexdigest()
        cache_path = os.path.join(self.cache_dir, f"{idx:04d}_{url_hash}.jpg")

        # Check cache
        if os.path.exists(cache_path):
            try:
                return Image.open(cache_path)
            except:
                pass  # Re-download if corrupted

        # Download
        try:
            print(f"📥 Downloading [{idx}]: {url[:60]}...")

            with urllib.request.urlopen(url, timeout=10) as response:
                image_data = response.read()

            # Save to cache
            with open(cache_path, 'wb') as f:
                f.write(image_data)

            # Load image
            return Image.open(io.BytesIO(image_data))

        except Exception as e:
            print(f"   ⚠️  Download failed: {e}")
            # Return placeholder
            return Image.new('RGB', (256, 256), color='gray')


if __name__ == '__main__':
    """Test dataset"""

    print("=" * 70)
    print("📦 Image Dataset Test")
    print("=" * 70)
    print()

    # Test SoulImageDataset
    print("Testing SoulImageDataset...")
    dataset = SoulImageDataset()

    print(f"Dataset size: {len(dataset)}")

    if len(dataset) > 0:
        # Get first sample
        image, label = dataset[0]
        print(f"Sample 0:")
        print(f"  Image: {image.size}")
        print(f"  Label: {label}")

        # Visualize samples
        print()
        print("Generating visualization...")
        dataset.visualize_samples(num_samples=4, save_path='dataset_samples.png')

    print()
    print("✅ Dataset test complete")
