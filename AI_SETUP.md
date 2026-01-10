# AI Image Generation Setup Guide

**Generate real AI images (like "nano banana") instead of colored shapes**

Works on Windows, Linux, and macOS (Intel + Apple Silicon)

---

## Quick Start (3 Commands)

```bash
# 1. Install AI dependencies
python install_ai.py

# 2. Test with butter image
python test_butter_image.py

# 3. Done! Images now AI-generated automatically
```

That's it. The system now uses **Stable Diffusion 3.5** for image generation.

---

## What You Get

✅ **Real AI-generated images** - Not colored shapes
✅ **Brand-specific styles** - HowToCookAtHome looks like food photography, Cringeproof looks minimalist
✅ **Better prompts** - "Professional food photography" vs "some shapes"
✅ **OCR text extraction** - Extract text from images for training
✅ **PyTorch datasets** - Build training data like the tutorial
✅ **Works offline** - Everything runs locally (after model download)
✅ **Graceful fallback** - Uses procedural if AI unavailable

---

## Installation Details

### What Gets Installed

**install_ai.py** installs:

1. **PyTorch** (~500MB)
   - Neural network framework
   - CPU version by default (works everywhere)
   - GPU version if CUDA/MPS detected

2. **Stable Diffusion** (~4GB first run)
   - Text-to-image AI model
   - Downloads from Hugging Face
   - Cached locally after first use

3. **EasyOCR** (~100MB)
   - Extract text from images
   - 80+ languages supported

4. **Pillow** (image processing)

### First Run

When you first generate an image, Stable Diffusion downloads ~4GB of model weights from Hugging Face. This only happens once - models are cached in `~/.cache/huggingface/`.

**Bandwidth warning:** First generation takes ~10-15 minutes depending on internet speed.

---

## pip vs pip3 Explained

**Question:** Is `pip` for Windows/Linux and `pip3` for macOS?

**Answer:** No. Both work everywhere, but:

- `pip` = Python 2 OR Python 3 (depends on system)
- `pip3` = Forces Python 3 only
- **Best practice**: Use `python -m pip` (always uses correct version)

**Examples:**
```bash
# These all work:
pip install torch
pip3 install torch
python -m pip install torch
python3 -m pip install torch

# install_ai.py uses:
python install_ai.py  # Uses sys.executable to get correct pip
```

---

## Platform Support

### macOS (Intel)
- ✅ CPU mode (works)
- ⚠️  GPU mode (no CUDA support)
- Uses: CPU-only PyTorch

### macOS (Apple Silicon M1/M2/M3)
- ✅ CPU mode (works)
- ✅ **MPS mode** (GPU acceleration via Metal)
- Uses: MPS-enabled PyTorch
- **Faster than Intel Macs**

### Windows
- ✅ CPU mode (works)
- ✅ GPU mode (if NVIDIA GPU + CUDA)
- Uses: CUDA PyTorch if GPU detected

### Linux
- ✅ CPU mode (works)
- ✅ GPU mode (if NVIDIA GPU + CUDA)
- Uses: CUDA PyTorch if GPU detected

---

## GPU vs CPU

### With GPU (CUDA/MPS)
- Image generation: ~30-60 seconds
- First time setup: ~10-15 minutes (model download)
- Memory required: ~6-8GB VRAM
- Recommended for: Production use

### Without GPU (CPU only)
- Image generation: ~5-10 minutes
- First time setup: ~10-15 minutes (model download)
- Memory required: ~8GB RAM
- Recommended for: Testing, development

**Note:** The system auto-detects and uses best available device.

---

## Testing

### Test Prompt Templates (No Dependencies)
```bash
python prompt_templates.py
```

Shows how prompts are generated for each brand.

### Test Image Generation
```bash
python test_butter_image.py
```

Generates a real "butter" image for the recipe. Output:
- `butter_test.png` (if AI available)
- `butter_fallback.png` (if AI unavailable)

### Test in Content Generator
```python
from content_generator import ContentGenerator

gen = ContentGenerator()

# This now uses AI images automatically
post = gen.conversation_to_post(
    session_id=1,
    brand_slug='howtocookathome',
    generate_images=True
)
```

---

## Brand-Specific Prompts

Each brand gets custom prompts:

### HowToCookAtHome (Food Blog)
**Prompt template:**
> "Professional food photography of [title], warm kitchen lighting, rustic wooden table, shallow depth of field, natural light, Instagram food styling"

**Style:** Food photography, appetizing, warm colors

### Cringeproof (Minimalist)
**Prompt template:**
> "Minimalist design for [title], clean aesthetic, modern typography, bold colors, negative space"

**Style:** Clean, modern, minimalist aesthetic

### SoulFra (Creative/Tech)
**Prompt template:**
> "Abstract creative visualization of [title], vibrant colors, artistic composition, digital art style"

**Style:** Abstract, colorful, artistic

### Custom Brands
Edit `prompt_templates.py` to add your own brand templates.

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'torch'"
**Solution:** Run `python install_ai.py`

### "CUDA out of memory"
**Solution:** Reduce image size or use CPU mode:
```python
gen = AIImageGenerator(device='cpu')
```

### "Model download too slow"
**Solution:** First run requires ~4GB download. Be patient or use public WiFi.

### "Images still look like shapes"
**Solution:** Check if PyTorch installed:
```bash
python -c "import torch; print(torch.__version__)"
```

If error, reinstall: `python install_ai.py`

---

## Advanced: Custom Models

See `model_trainer.py` for training brand-specific models:

```python
from model_trainer import ModelTrainer

trainer = ModelTrainer()

# Prepare brand dataset
trainer.prepare_brand_dataset('howtocookathome')

# Train LoRA (coming soon)
trainer.train_lora('howtocookathome', epochs=100)
```

**Note:** Full LoRA training implementation requires `pip install peft`

---

## File Reference

- `install_ai.py` - One-click installer
- `ai_image_generator.py` - Stable Diffusion wrapper
- `prompt_templates.py` - Brand-specific prompts
- `test_butter_image.py` - Test script
- `ocr_extractor.py` - Text extraction from images
- `image_dataset.py` - PyTorch dataset loader
- `model_trainer.py` - Fine-tuning framework

---

## FAQs

**Q: Do I need a GPU?**
A: No. CPU works (just slower).

**Q: How big are the models?**
A: ~4GB for Stable Diffusion 3.5

**Q: Can I use a different model?**
A: Yes. Edit `ai_image_generator.py`:
```python
gen = AIImageGenerator(model_id="stabilityai/stable-diffusion-2-1")
```

**Q: Does this work offline?**
A: Yes, after initial model download.

**Q: How do I uninstall?**
A: `pip uninstall torch torchvision diffusers transformers easyocr`

---

## Next Steps

1. ✅ Run `python install_ai.py`
2. ✅ Run `python test_butter_image.py`
3. Generate blog posts - images now AI-generated automatically!
4. (Optional) Train custom models with `model_trainer.py`
5. (Optional) Extract text from images with `ocr_extractor.py`

---

**It's 2025. Time to generate real images, not colored shapes.**
