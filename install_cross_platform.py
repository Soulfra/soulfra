#!/usr/bin/env python3
"""
Cross-Platform Installer - Auto-detect Package Manager

Detects and uses the correct package manager for each platform:
- Linux: apt-get, yum, dnf, pacman
- macOS: brew (Homebrew)
- Windows: winget, choco (Chocolatey)

Usage:
    python3 install_cross_platform.py

    # Or import as module
    from install_cross_platform import install_system_packages

    install_system_packages(['zbar', 'ffmpeg'])

Features:
- ✅ Auto-detects operating system
- ✅ Auto-detects available package managers
- ✅ Installs system dependencies (zbar for QR scanning)
- ✅ Installs Python dependencies
- ✅ Works on Linux, macOS, Windows
- ✅ Handles missing package managers gracefully

Package Managers Explained:
- apt/apt-get: Debian/Ubuntu Linux (most common)
- yum/dnf: RedHat/Fedora/CentOS Linux
- pacman: Arch Linux
- brew: macOS (install from brew.sh)
- winget: Windows 11/10 (built-in, use Windows Package Manager)
- choco: Windows (install from chocolatey.org)
- pip/pip3: Python packages (all platforms)
"""

import os
import sys
import platform
import subprocess
import shutil
from typing import List, Optional, Dict


# =============================================================================
# Package Manager Detection
# =============================================================================

def detect_os() -> str:
    """
    Detect operating system

    Returns:
        'linux', 'macos', 'windows', or 'unknown'
    """
    system = platform.system().lower()

    if system == 'linux':
        return 'linux'
    elif system == 'darwin':
        return 'macos'
    elif system == 'windows':
        return 'windows'
    else:
        return 'unknown'


def detect_package_manager() -> Optional[str]:
    """
    Detect available package manager

    Returns:
        Package manager name ('apt', 'brew', 'winget', etc.) or None
    """
    os_type = detect_os()

    # Linux package managers
    if os_type == 'linux':
        if shutil.which('apt-get'):
            return 'apt'
        elif shutil.which('apt'):
            return 'apt'
        elif shutil.which('dnf'):
            return 'dnf'
        elif shutil.which('yum'):
            return 'yum'
        elif shutil.which('pacman'):
            return 'pacman'

    # macOS package managers
    elif os_type == 'macos':
        if shutil.which('brew'):
            return 'brew'

    # Windows package managers
    elif os_type == 'windows':
        if shutil.which('winget'):
            return 'winget'
        elif shutil.which('choco'):
            return 'choco'

    return None


def get_install_command(package_manager: str, package: str) -> List[str]:
    """
    Get install command for package manager

    Args:
        package_manager: Package manager name
        package: Package to install

    Returns:
        Command as list of strings

    Example:
        >>> get_install_command('apt', 'zbar')
        ['sudo', 'apt-get', 'install', '-y', 'libzbar0']
    """
    # Map generic package names to platform-specific names
    package_mappings = {
        'apt': {
            'zbar': 'libzbar0',
            'ffmpeg': 'ffmpeg',
            'imagemagick': 'imagemagick'
        },
        'brew': {
            'zbar': 'zbar',
            'ffmpeg': 'ffmpeg',
            'imagemagick': 'imagemagick'
        },
        'winget': {
            'zbar': 'zbar',  # May not be available
            'ffmpeg': 'ffmpeg',
            'imagemagick': 'ImageMagick.ImageMagick'
        },
        'choco': {
            'zbar': 'zbar',  # May not be available
            'ffmpeg': 'ffmpeg',
            'imagemagick': 'imagemagick'
        },
        'dnf': {
            'zbar': 'zbar',
            'ffmpeg': 'ffmpeg',
            'imagemagick': 'imagemagick'
        },
        'yum': {
            'zbar': 'zbar',
            'ffmpeg': 'ffmpeg',
            'imagemagick': 'imagemagick'
        },
        'pacman': {
            'zbar': 'zbar',
            'ffmpeg': 'ffmpeg',
            'imagemagick': 'imagemagick'
        }
    }

    # Get platform-specific package name
    pkg_name = package_mappings.get(package_manager, {}).get(package, package)

    # Build command based on package manager
    if package_manager == 'apt':
        return ['sudo', 'apt-get', 'install', '-y', pkg_name]
    elif package_manager == 'brew':
        return ['brew', 'install', pkg_name]
    elif package_manager == 'winget':
        return ['winget', 'install', '--id', pkg_name, '--silent']
    elif package_manager == 'choco':
        return ['choco', 'install', pkg_name, '-y']
    elif package_manager in ['dnf', 'yum']:
        return ['sudo', package_manager, 'install', '-y', pkg_name]
    elif package_manager == 'pacman':
        return ['sudo', 'pacman', '-S', '--noconfirm', pkg_name]
    else:
        return []


# =============================================================================
# Installation Functions
# =============================================================================

def install_system_package(package: str, package_manager: Optional[str] = None) -> bool:
    """
    Install system package using detected package manager

    Args:
        package: Package name (generic, will be mapped to platform-specific)
        package_manager: Optional specific package manager to use

    Returns:
        True if installation succeeded, False otherwise

    Example:
        >>> install_system_package('zbar')  # Auto-detects package manager
        True
    """
    if not package_manager:
        package_manager = detect_package_manager()

    if not package_manager:
        print(f"⚠️  No package manager detected, cannot install {package}")
        return False

    # Get install command
    cmd = get_install_command(package_manager, package)

    if not cmd:
        print(f"⚠️  Don't know how to install {package} with {package_manager}")
        return False

    # Run install command
    print(f"Installing {package} using {package_manager}...")
    print(f"  Command: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ {package} installed successfully")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package}")
        print(f"   Error: {e.stderr}")
        return False

    except FileNotFoundError:
        print(f"❌ Package manager '{package_manager}' not found in PATH")
        return False


def install_system_packages(packages: List[str]) -> Dict[str, bool]:
    """
    Install multiple system packages

    Args:
        packages: List of package names

    Returns:
        Dict mapping package name to success status

    Example:
        >>> install_system_packages(['zbar', 'ffmpeg'])
        {'zbar': True, 'ffmpeg': True}
    """
    results = {}
    package_manager = detect_package_manager()

    if not package_manager:
        print("⚠️  No package manager detected")
        for pkg in packages:
            results[pkg] = False
        return results

    print(f"Using package manager: {package_manager}")
    print()

    for package in packages:
        results[package] = install_system_package(package, package_manager)
        print()

    return results


def install_python_packages(packages: List[str]) -> bool:
    """
    Install Python packages using pip

    Args:
        packages: List of PyPI package names

    Returns:
        True if all packages installed successfully

    Example:
        >>> install_python_packages(['pyzbar', 'pillow'])
        True
    """
    print(f"Installing Python packages: {', '.join(packages)}")

    cmd = [sys.executable, '-m', 'pip', 'install'] + packages

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ Python packages installed successfully")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Python packages")
        print(f"   Error: {e.stderr}")
        return False


# =============================================================================
# Specific Installers
# =============================================================================

def install_qr_scanning_dependencies():
    """
    Install dependencies for QR code scanning

    Required for:
    - qr_image_overlay.py (verification)
    - verify_image.py (QR scanning)

    System packages:
    - zbar (QR code scanning library)

    Python packages:
    - pyzbar (Python wrapper for zbar)
    """
    print("=" * 70)
    print("Installing QR Scanning Dependencies")
    print("=" * 70)
    print()

    # Install system package (zbar)
    system_success = install_system_package('zbar')
    print()

    # Install Python package (pyzbar)
    python_success = install_python_packages(['pyzbar'])
    print()

    if system_success and python_success:
        print("✅ QR scanning dependencies installed!")
        print()
        print("Test with:")
        print("  python3 -c 'from pyzbar.pyzbar import decode; print(\"QR scanning ready\")'")
    else:
        print("⚠️  Some dependencies failed to install")
        print()
        print("Manual installation:")
        os_type = detect_os()
        if os_type == 'macos':
            print("  brew install zbar")
        elif os_type == 'linux':
            print("  sudo apt install libzbar0")
        elif os_type == 'windows':
            print("  # zbar may not be available on Windows")
            print("  # Use API-based QR scanning instead")
        print("  pip install pyzbar")

    print("=" * 70)


def install_ai_image_dependencies():
    """
    Install dependencies for AI image generation

    Required for:
    - ai_image_generator.py (local Stable Diffusion)

    Python packages:
    - torch, torchvision (PyTorch)
    - diffusers (Stable Diffusion)
    - transformers (models)
    - easyocr (OCR)
    """
    print("=" * 70)
    print("Installing AI Image Generation Dependencies")
    print("=" * 70)
    print()

    print("⚠️  This will download ~4GB of dependencies")
    print()

    # Run install_ai.py if it exists
    if os.path.exists('install_ai.py'):
        print("Running install_ai.py...")
        print()

        try:
            subprocess.run([sys.executable, 'install_ai.py'], check=True)
            print()
            print("✅ AI dependencies installed!")

        except subprocess.CalledProcessError:
            print("❌ AI installation failed")
            print()
            print("See AI_SETUP.md for manual installation")

    else:
        print("install_ai.py not found")
        print()
        print("Install manually:")
        print("  pip install torch torchvision diffusers transformers easyocr")

    print("=" * 70)


def install_api_image_dependencies():
    """
    Install dependencies for API-based image generation

    Required for:
    - api_image_generator.py (Replicate, Stability AI, etc.)

    Python packages:
    - replicate (Replicate API)
    - openai (OpenAI API)
    - requests (HTTP requests)
    - BingImageCreator (Bing API - optional)
    """
    print("=" * 70)
    print("Installing API Image Generation Dependencies")
    print("=" * 70)
    print()

    packages = ['replicate', 'openai', 'requests']

    success = install_python_packages(packages)
    print()

    # Optional: BingImageCreator
    print("Optional: Bing Image Creator (free API)")
    print("  pip install BingImageCreator")
    print()

    if success:
        print("✅ API image generation dependencies installed!")
        print()
        print("Set API keys:")
        print("  export REPLICATE_API_KEY='r8_...'")
        print("  export OPENAI_API_KEY='sk-...'")
        print("  export STABILITY_API_KEY='sk-...'")
    else:
        print("⚠️  Some dependencies failed to install")

    print("=" * 70)


# =============================================================================
# CLI Interface
# =============================================================================

if __name__ == '__main__':
    """
    Cross-platform installer CLI

    Usage:
        python3 install_cross_platform.py
        python3 install_cross_platform.py --qr
        python3 install_cross_platform.py --ai
        python3 install_cross_platform.py --api
    """
    import argparse

    parser = argparse.ArgumentParser(description='Cross-platform dependency installer')
    parser.add_argument('--qr', action='store_true', help='Install QR scanning dependencies')
    parser.add_argument('--ai', action='store_true', help='Install AI image generation dependencies')
    parser.add_argument('--api', action='store_true', help='Install API image generation dependencies')
    parser.add_argument('--all', action='store_true', help='Install all dependencies')
    parser.add_argument('--detect', action='store_true', help='Just detect system and package manager')

    args = parser.parse_args()

    print("=" * 70)
    print("Cross-Platform Installer")
    print("=" * 70)
    print()

    # Detect system
    os_type = detect_os()
    pkg_mgr = detect_package_manager()

    print(f"Operating System: {os_type}")
    print(f"Package Manager:  {pkg_mgr or 'None detected'}")
    print()

    if args.detect:
        # Just show detection info
        print("Package Manager Guide:")
        print("-" * 70)
        print()

        if os_type == 'linux':
            print("Linux package managers:")
            print("  apt/apt-get  - Debian, Ubuntu, Linux Mint")
            print("  dnf          - Fedora, RedHat, CentOS 8+")
            print("  yum          - RedHat, CentOS 7")
            print("  pacman       - Arch Linux, Manjaro")
            print()
            print("Install packages:")
            if pkg_mgr == 'apt':
                print("  sudo apt-get install <package>")
            elif pkg_mgr in ['dnf', 'yum']:
                print(f"  sudo {pkg_mgr} install <package>")
            elif pkg_mgr == 'pacman':
                print("  sudo pacman -S <package>")

        elif os_type == 'macos':
            print("macOS package managers:")
            print("  brew         - Homebrew (install from brew.sh)")
            print()
            if pkg_mgr == 'brew':
                print("Install packages:")
                print("  brew install <package>")
            else:
                print("Homebrew not installed. Install from:")
                print("  https://brew.sh")

        elif os_type == 'windows':
            print("Windows package managers:")
            print("  winget       - Windows Package Manager (built-in Win11/10)")
            print("  choco        - Chocolatey (install from chocolatey.org)")
            print()
            if pkg_mgr == 'winget':
                print("Install packages:")
                print("  winget install <package>")
            elif pkg_mgr == 'choco':
                print("Install packages:")
                print("  choco install <package>")
            else:
                print("No package manager detected. Install:")
                print("  - winget: Built into Windows 11/10")
                print("  - choco: https://chocolatey.org/install")

        print()
        print("Python packages (all platforms):")
        print("  pip install <package>")
        print("  python -m pip install <package>")
        print()

    elif args.qr or args.all:
        install_qr_scanning_dependencies()

    elif args.ai or args.all:
        install_ai_image_dependencies()

    elif args.api or args.all:
        install_api_image_dependencies()

    else:
        # Show menu
        print("What would you like to install?")
        print("-" * 70)
        print()
        print("1. QR Scanning Dependencies (zbar, pyzbar)")
        print("2. AI Image Generation (PyTorch, Stable Diffusion) [~4GB]")
        print("3. API Image Generation (Replicate, OpenAI APIs)")
        print("4. All Dependencies")
        print()
        print("Run with flags:")
        print("  python3 install_cross_platform.py --qr")
        print("  python3 install_cross_platform.py --ai")
        print("  python3 install_cross_platform.py --api")
        print("  python3 install_cross_platform.py --all")
        print()
        print("Or just detect system:")
        print("  python3 install_cross_platform.py --detect")
        print()

    print("=" * 70)
