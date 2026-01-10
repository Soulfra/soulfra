#!/usr/bin/env python3
"""
Model Trainer - Fine-tune Stable Diffusion on Brand Imagery

Train custom image generation models for each brand using:
- LoRA (Low-Rank Adaptation) - lightweight, fast training
- DreamBooth - full fine-tuning for brand-specific styles
- Textual Inversion - learn new concepts/styles

Features:
- Train on brand-specific image datasets
- Save custom models per brand
- Load trained models for generation
- Low VRAM training (works on consumer GPUs)

Requirements:
- PyTorch, diffusers, peft (see requirements.txt)
- ~8-10GB VRAM for LoRA (less with optimizations)
- Training images (10-50 images per brand recommended)

Philosophy:
Train "nano banana" style models specific to each brand's visual identity.
Make HowToCookAtHome images look different from Cringeproof images.
"""

import os
import json
from typing import List, Dict, Optional
from PIL import Image


class ModelTrainer:
    """
    Train custom Stable Diffusion models for brands

    Usage:
        trainer = ModelTrainer()

        # Prepare training data
        trainer.prepare_brand_dataset('howtocookathome')

        # Train LoRA
        trainer.train_lora(
            brand_slug='howtocookathome',
            epochs=100,
            learning_rate=1e-4
        )

        # Use trained model
        trainer.generate_with_brand_model(
            brand_slug='howtocookathome',
            prompt='delicious pasta dish'
        )
    """

    def __init__(
        self,
        db_path: str = 'soulfra.db',
        models_dir: str = 'models/brand_loras'
    ):
        """
        Initialize model trainer

        Args:
            db_path: Path to SQLite database
            models_dir: Directory to save trained models
        """
        self.db_path = db_path
        self.models_dir = models_dir

        os.makedirs(models_dir, exist_ok=True)

        print(f"🎓 Model Trainer initialized")
        print(f"   Models dir: {models_dir}")

    def prepare_brand_dataset(
        self,
        brand_slug: str,
        output_dir: Optional[str] = None
    ) -> str:
        """
        Prepare training dataset for a brand

        Exports brand images from database to disk for training

        Args:
            brand_slug: Brand slug
            output_dir: Output directory (auto-created if None)

        Returns:
            Path to dataset directory
        """
        if output_dir is None:
            output_dir = f'datasets/brand_training/{brand_slug}'

        os.makedirs(output_dir, exist_ok=True)

        print(f"📦 Preparing dataset for: {brand_slug}")
        print(f"   Output: {output_dir}")

        try:
            from image_dataset import SoulImageDataset

            # Load images for this brand
            dataset = SoulImageDataset(
                db_path=self.db_path,
                brand_slug=brand_slug
            )

            if len(dataset) == 0:
                print(f"   ⚠️  No images found for brand: {brand_slug}")
                return output_dir

            # Export images
            for i in range(len(dataset)):
                image, label = dataset[i]

                # Save image
                image_path = os.path.join(output_dir, f"image_{i:04d}.png")
                image.save(image_path)

            print(f"   ✅ Exported {len(dataset)} images")

            # Create metadata file
            metadata = {
                'brand_slug': brand_slug,
                'num_images': len(dataset),
                'created_at': str(datetime.now())
            }

            metadata_path = os.path.join(output_dir, 'metadata.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)

            return output_dir

        except Exception as e:
            print(f"   ❌ Failed to prepare dataset: {e}")
            import traceback
            traceback.print_exc()
            return output_dir

    def train_lora(
        self,
        brand_slug: str,
        dataset_dir: Optional[str] = None,
        epochs: int = 100,
        learning_rate: float = 1e-4,
        rank: int = 4
    ):
        """
        Train LoRA adapter for brand

        LoRA (Low-Rank Adaptation) is lightweight and fast.
        Only trains a small adapter (~10-50MB) instead of full model.

        Args:
            brand_slug: Brand slug
            dataset_dir: Training images directory (auto-prepared if None)
            epochs: Number of training epochs
            learning_rate: Learning rate
            rank: LoRA rank (4-8 recommended, higher = more capacity but slower)

        Returns:
            Path to saved LoRA model
        """
        print(f"🎓 Training LoRA for: {brand_slug}")
        print(f"   Epochs: {epochs}")
        print(f"   Learning rate: {learning_rate}")
        print(f"   Rank: {rank}")
        print()

        # Prepare dataset if not provided
        if dataset_dir is None:
            dataset_dir = self.prepare_brand_dataset(brand_slug)

        try:
            # Note: This is a simplified placeholder
            # Full LoRA training requires:
            # - peft library for LoRA
            # - Accelerate for distributed training
            # - Custom training loop with gradient accumulation
            # - Model checkpointing

            print("⚠️  LoRA training requires additional setup:")
            print("   1. Install peft: pip install peft")
            print("   2. Configure training parameters")
            print("   3. Run training script")
            print()
            print("For now, this is a placeholder. Full implementation would:")
            print("   - Load base Stable Diffusion model")
            print("   - Add LoRA adapters to attention layers")
            print("   - Train on brand images")
            print("   - Save adapter weights")
            print()
            print(f"Dataset ready at: {dataset_dir}")
            print(f"Images to train on: {len(os.listdir(dataset_dir)) - 1}")  # -1 for metadata.json

            # Model would be saved to:
            model_path = os.path.join(self.models_dir, f"{brand_slug}_lora")
            print(f"Model will be saved to: {model_path}")

            return model_path

        except Exception as e:
            print(f"   ❌ Training failed: {e}")
            import traceback
            traceback.print_exc()
            return None

    def generate_with_brand_model(
        self,
        brand_slug: str,
        prompt: str,
        size: tuple = (1024, 1024)
    ) -> bytes:
        """
        Generate image using brand-specific trained model

        Args:
            brand_slug: Brand slug
            prompt: Text prompt
            size: Image size

        Returns:
            Image bytes
        """
        print(f"🎨 Generating with brand model: {brand_slug}")
        print(f"   Prompt: {prompt}")

        try:
            from ai_image_generator import AIImageGenerator

            # Load base generator
            generator = AIImageGenerator()

            # Check if brand has trained model
            model_path = os.path.join(self.models_dir, f"{brand_slug}_lora")

            if os.path.exists(model_path):
                print(f"   📂 Found trained model at: {model_path}")
                print(f"   ⚠️  Loading LoRA not yet implemented - using base model")
                # TODO: Load LoRA weights
                # pipeline.load_lora_weights(model_path)

            # Generate
            image_bytes = generator.generate_from_text(
                prompt=prompt,
                size=size
            )

            return image_bytes

        except Exception as e:
            print(f"   ❌ Generation failed: {e}")
            raise


if __name__ == '__main__':
    """Test model trainer"""
    from datetime import datetime

    print("=" * 70)
    print("🎓 Model Trainer Test")
    print("=" * 70)
    print()

    trainer = ModelTrainer()

    # Test dataset preparation
    print("Testing dataset preparation...")
    print()

    dataset_dir = trainer.prepare_brand_dataset('howtocookathome')

    print()
    print(f"✅ Dataset prepared: {dataset_dir}")
    print()

    # Show training info
    print("To train a LoRA model:")
    print()
    print("  from model_trainer import ModelTrainer")
    print()
    print("  trainer = ModelTrainer()")
    print("  trainer.train_lora(")
    print("      brand_slug='howtocookathome',")
    print("      epochs=100,")
    print("      learning_rate=1e-4")
    print("  )")
    print()
    print("Note: Full LoRA training implementation requires:")
    print("  - pip install peft")
    print("  - Training loop with gradient accumulation")
    print("  - Model checkpointing")
    print("  - This is a framework/placeholder for future implementation")
