#!/usr/bin/env python3
"""
AI Dependencies Installer - One-Click Setup

Installs PyTorch, Stable Diffusion, and OCR dependencies
Works on Windows, Linux, and macOS (both Intel and Apple Silicon)

Usage:
    python install_ai.py

Features:
- Auto-detects platform and GPU
- Installs lightweight CPU version by default
- Optional GPU version if CUDA/MPS detected
- Shows progress, handles errors
- Works with pip OR pip3 (uses python -m pip)
"""

import subprocess
import sys
import platform
import os


def print_header():
    """Print installation header"""
    print("=" * 70)
    print("🎨 AI Image Generation - Dependency Installer")
    print("=" * 70)
    print()


def detect_platform():
    """Detect operating system and architecture"""
    system = platform.system()
    machine = platform.machine()

    print(f"Platform: {system} ({machine})")

    return system, machine


def detect_gpu():
    """Detect if GPU is available"""
    print("Checking for GPU...")

    # Check NVIDIA CUDA
    try:
        result = subprocess.run(
            ['nvidia-smi'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            print("  ✅ NVIDIA GPU detected (CUDA available)")
            return 'cuda'
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Check Apple Silicon (M1/M2/M3)
    if platform.system() == 'Darwin' and platform.machine() == 'arm64':
        print("  ✅ Apple Silicon detected (MPS available)")
        return 'mps'

    print("  ℹ️  No GPU detected - will install CPU version")
    return 'cpu'


def install_pytorch(device='cpu'):
    """Install PyTorch based on device"""
    print()
    print("📥 Installing PyTorch...")
    print(f"   Device: {device}")
    print()

    if device == 'cuda':
        # NVIDIA GPU - install CUDA version
        url = "https://download.pytorch.org/whl/cu118"
        packages = [
            'torch>=2.0.0',
            'torchvision>=0.15.0'
        ]
    elif device == 'mps':
        # Apple Silicon - standard PyPI (has MPS support)
        url = None
        packages = [
            'torch>=2.0.0',
            'torchvision>=0.15.0'
        ]
    else:
        # CPU only
        url = "https://download.pytorch.org/whl/cpu"
        packages = [
            'torch>=2.0.0',
            'torchvision>=0.15.0'
        ]

    # Build install command
    cmd = [sys.executable, '-m', 'pip', 'install'] + packages

    if url:
        cmd.extend(['--index-url', url])

    print(f"Running: {' '.join(cmd)}")
    print()

    try:
        result = subprocess.run(cmd, check=True)

        if result.returncode == 0:
            print()
            print("  ✅ PyTorch installed successfully")
            return True
    except subprocess.CalledProcessError as e:
        print(f"  ❌ PyTorch installation failed: {e}")
        return False


def install_diffusers():
    """Install Stable Diffusion and related packages"""
    print()
    print("📥 Installing Stable Diffusion (diffusers)...")
    print()

    packages = [
        'diffusers>=0.25.0',
        'transformers>=4.30.0',
        'accelerate>=0.20.0',
        'safetensors>=0.3.0',
        'invisible_watermark>=0.2.0'
    ]

    cmd = [sys.executable, '-m', 'pip', 'install'] + packages

    print(f"Running: {' '.join(cmd)}")
    print()

    try:
        result = subprocess.run(cmd, check=True)

        if result.returncode == 0:
            print()
            print("  ✅ Diffusers installed successfully")
            return True
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Diffusers installation failed: {e}")
        return False


def install_ocr():
    """Install OCR dependencies"""
    print()
    print("📥 Installing OCR (EasyOCR)...")
    print()

    packages = [
        'easyocr>=1.7.0'
    ]

    cmd = [sys.executable, '-m', 'pip', 'install'] + packages

    print(f"Running: {' '.join(cmd)}")
    print()

    try:
        result = subprocess.run(cmd, check=True)

        if result.returncode == 0:
            print()
            print("  ✅ EasyOCR installed successfully")
            return True
    except subprocess.CalledProcessError as e:
        print(f"  ❌ EasyOCR installation failed: {e}")
        return False


def install_pillow():
    """Install Pillow (image processing)"""
    print()
    print("📥 Installing Pillow (image processing)...")
    print()

    packages = [
        'Pillow>=10.0.0'
    ]

    cmd = [sys.executable, '-m', 'pip', 'install'] + packages

    print(f"Running: {' '.join(cmd)}")
    print()

    try:
        result = subprocess.run(cmd, check=True)

        if result.returncode == 0:
            print()
            print("  ✅ Pillow installed successfully")
            return True
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Pillow installation failed: {e}")
        return False


def verify_installation():
    """Verify all packages are installed"""
    print()
    print("🔍 Verifying installation...")
    print()

    packages_to_check = [
        'torch',
        'torchvision',
        'diffusers',
        'transformers',
        'easyocr',
        'PIL'
    ]

    all_ok = True

    for package in packages_to_check:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} - not found")
            all_ok = False

    return all_ok


def main():
    """Main installation flow"""
    print_header()

    # Detect platform
    system, machine = detect_platform()
    print()

    # Detect GPU
    device = detect_gpu()
    print()

    # Ask user if they want to proceed
    print("This will install:")
    print("  - PyTorch (~500MB)")
    print("  - Stable Diffusion (~1GB first run)")
    print("  - EasyOCR (~100MB)")
    print("  - Pillow")
    print()

    response = input("Continue? [Y/n]: ").strip().lower()

    if response and response not in ['y', 'yes']:
        print("Installation cancelled")
        return

    print()
    print("Starting installation...")
    print()

    # Install PyTorch
    if not install_pytorch(device=device):
        print()
        print("❌ Installation failed at PyTorch")
        print("Try manually: python -m pip install torch torchvision")
        return

    # Install Diffusers
    if not install_diffusers():
        print()
        print("⚠️  Diffusers installation failed - AI generation won't work")
        print("But procedural fallback will still work")

    # Install OCR
    if not install_ocr():
        print()
        print("⚠️  EasyOCR installation failed - OCR won't work")
        print("But image generation will still work")

    # Install Pillow
    if not install_pillow():
        print()
        print("⚠️  Pillow installation failed")

    # Verify
    all_ok = verify_installation()

    print()
    print("=" * 70)

    if all_ok:
        print("✅ Installation Complete!")
        print()
        print("Next steps:")
        print("  1. Test image generation: python test_butter_image.py")
        print("  2. Read setup guide: cat AI_SETUP.md")
    else:
        print("⚠️  Installation completed with warnings")
        print()
        print("Some packages failed to install.")
        print("The system will fall back to procedural generation.")

    print("=" * 70)


if __name__ == '__main__':
    main()
