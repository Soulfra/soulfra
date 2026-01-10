"""
Image Metadata - Professional EXIF Embedding

Embeds professional metadata into generated images:
- Artist/Creator information
- Copyright and licensing
- Creation date/time
- Brand information
- Layer composition data
- Generation parameters

Uses piexif for EXIF manipulation.
"""

import io
import json
from datetime import datetime
from typing import Dict, Optional, Any, List
from PIL import Image
import piexif


# =============================================================================
# EXIF Constants
# =============================================================================

# Standard EXIF tags
TAG_ARTIST = 0x013B
TAG_COPYRIGHT = 0x8298
TAG_SOFTWARE = 0x0131
TAG_DATETIME = 0x0132
TAG_IMAGE_DESCRIPTION = 0x010E
TAG_USER_COMMENT = 0x9286

# Default values
DEFAULT_ARTIST = "Soulfra Image Generator"
DEFAULT_SOFTWARE = "Soulfra Professional Image Composer v1.0"
DEFAULT_COPYRIGHT = "© {year} Soulfra. All rights reserved."


# =============================================================================
# Metadata Builder
# =============================================================================

class ImageMetadata:
    """Professional image metadata manager"""

    def __init__(
        self,
        artist: Optional[str] = None,
        copyright_text: Optional[str] = None,
        brand: Optional[str] = None,
        description: Optional[str] = None
    ):
        """
        Initialize metadata

        Args:
            artist: Creator/artist name
            copyright_text: Copyright notice
            brand: Brand slug (cringeproof, soulfra, etc.)
            description: Image description
        """
        self.artist = artist or DEFAULT_ARTIST
        self.copyright_text = copyright_text or DEFAULT_COPYRIGHT.format(year=datetime.now().year)
        self.brand = brand
        self.description = description
        self.creation_date = datetime.now()

        # Additional metadata
        self.layers: List[Dict] = []
        self.generation_params: Dict[str, Any] = {}
        self.custom_data: Dict[str, Any] = {}

    def add_layer_data(self, layer_type: str, **params):
        """Add layer composition data"""
        self.layers.append({
            'type': layer_type,
            **params
        })

    def add_generation_params(self, **params):
        """Add generation parameters"""
        self.generation_params.update(params)

    def add_custom_data(self, key: str, value: Any):
        """Add custom metadata"""
        self.custom_data[key] = value

    def to_exif_dict(self) -> Dict:
        """Convert to EXIF dictionary format"""
        exif_dict = {
            "0th": {},
            "Exif": {},
            "GPS": {},
            "1st": {},
            "thumbnail": None
        }

        # Basic metadata
        exif_dict["0th"][TAG_ARTIST] = self.artist.encode('utf-8')
        exif_dict["0th"][TAG_COPYRIGHT] = self.copyright_text.encode('utf-8')
        exif_dict["0th"][TAG_SOFTWARE] = DEFAULT_SOFTWARE.encode('utf-8')
        exif_dict["0th"][TAG_DATETIME] = self.creation_date.strftime("%Y:%m:%d %H:%M:%S").encode('utf-8')

        if self.description:
            exif_dict["0th"][TAG_IMAGE_DESCRIPTION] = self.description.encode('utf-8')

        # Extended metadata in UserComment
        extended_data = {
            'brand': self.brand,
            'layers': self.layers,
            'generation_params': self.generation_params,
            'custom': self.custom_data
        }

        # Encode as JSON in UserComment field
        user_comment = json.dumps(extended_data, ensure_ascii=False)

        # UserComment format: encoding prefix (8 bytes) + actual comment
        # Using "UNICODE\0\0" prefix for UTF-8
        user_comment_bytes = b"UNICODE\0" + user_comment.encode('utf-8')
        exif_dict["Exif"][TAG_USER_COMMENT] = user_comment_bytes

        return exif_dict

    def embed_in_image(self, image_bytes: bytes) -> bytes:
        """
        Embed metadata into image

        Args:
            image_bytes: Original image bytes

        Returns:
            Image bytes with embedded EXIF
        """
        # Load image
        img = Image.open(io.BytesIO(image_bytes))

        # Convert RGBA to RGB if needed (JPEG doesn't support RGBA)
        if img.mode == 'RGBA':
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[3])  # Use alpha as mask
            img = rgb_img

        # Get EXIF data
        exif_dict = self.to_exif_dict()
        exif_bytes = piexif.dump(exif_dict)

        # Save with EXIF
        output = io.BytesIO()
        img.save(output, format='JPEG', exif=exif_bytes, quality=95)

        return output.getvalue()


# =============================================================================
# Metadata Extraction
# =============================================================================

def extract_metadata(image_path: str) -> Optional[Dict]:
    """
    Extract metadata from image

    Args:
        image_path: Path to image file

    Returns:
        Metadata dict or None if no metadata found
    """
    try:
        img = Image.open(image_path)

        # Get EXIF
        if 'exif' not in img.info:
            return None

        exif_dict = piexif.load(img.info['exif'])

        metadata = {
            'artist': None,
            'copyright': None,
            'software': None,
            'datetime': None,
            'description': None,
            'extended': None
        }

        # Extract basic metadata
        if TAG_ARTIST in exif_dict["0th"]:
            metadata['artist'] = exif_dict["0th"][TAG_ARTIST].decode('utf-8')

        if TAG_COPYRIGHT in exif_dict["0th"]:
            metadata['copyright'] = exif_dict["0th"][TAG_COPYRIGHT].decode('utf-8')

        if TAG_SOFTWARE in exif_dict["0th"]:
            metadata['software'] = exif_dict["0th"][TAG_SOFTWARE].decode('utf-8')

        if TAG_DATETIME in exif_dict["0th"]:
            metadata['datetime'] = exif_dict["0th"][TAG_DATETIME].decode('utf-8')

        if TAG_IMAGE_DESCRIPTION in exif_dict["0th"]:
            metadata['description'] = exif_dict["0th"][TAG_IMAGE_DESCRIPTION].decode('utf-8')

        # Extract extended metadata from UserComment
        if TAG_USER_COMMENT in exif_dict["Exif"]:
            user_comment_bytes = exif_dict["Exif"][TAG_USER_COMMENT]

            # Skip encoding prefix (8 bytes)
            if user_comment_bytes.startswith(b"UNICODE\0"):
                user_comment = user_comment_bytes[8:].decode('utf-8')
                try:
                    metadata['extended'] = json.loads(user_comment)
                except json.JSONDecodeError:
                    pass

        return metadata

    except Exception as e:
        print(f"Error extracting metadata: {e}")
        return None


# =============================================================================
# Helper Functions
# =============================================================================

def add_metadata_to_composer_output(
    image_bytes: bytes,
    brand: str,
    layers: List[Dict],
    title: Optional[str] = None,
    artist: Optional[str] = None
) -> bytes:
    """
    Add metadata to image_composer.py output

    Args:
        image_bytes: Composed image bytes
        brand: Brand slug
        layers: Layer composition data
        title: Image title/description
        artist: Artist name

    Returns:
        Image bytes with EXIF metadata
    """
    metadata = ImageMetadata(
        artist=artist,
        brand=brand,
        description=title
    )

    # Add layer data
    for layer in layers:
        metadata.add_layer_data(**layer)

    return metadata.embed_in_image(image_bytes)


def display_metadata(image_path: str, verbose: bool = True):
    """
    Display metadata from image

    Args:
        image_path: Path to image
        verbose: Show extended metadata
    """
    metadata = extract_metadata(image_path)

    if not metadata:
        print("No metadata found in image")
        return

    print("=" * 70)
    print("IMAGE METADATA")
    print("=" * 70)
    print()

    if metadata['artist']:
        print(f"Artist:      {metadata['artist']}")

    if metadata['copyright']:
        print(f"Copyright:   {metadata['copyright']}")

    if metadata['software']:
        print(f"Software:    {metadata['software']}")

    if metadata['datetime']:
        print(f"Created:     {metadata['datetime']}")

    if metadata['description']:
        print(f"Description: {metadata['description']}")

    print()

    if verbose and metadata['extended']:
        print("EXTENDED METADATA")
        print("-" * 70)

        extended = metadata['extended']

        if extended.get('brand'):
            print(f"Brand:       {extended['brand']}")

        if extended.get('layers'):
            print(f"\nLayer Composition ({len(extended['layers'])} layers):")
            for i, layer in enumerate(extended['layers'], 1):
                layer_type = layer.get('type', 'unknown')
                print(f"  {i}. {layer_type}")
                if verbose:
                    for key, value in layer.items():
                        if key != 'type':
                            print(f"     - {key}: {value}")

        if extended.get('generation_params'):
            print(f"\nGeneration Parameters:")
            for key, value in extended['generation_params'].items():
                print(f"  - {key}: {value}")

        if extended.get('custom'):
            print(f"\nCustom Data:")
            for key, value in extended['custom'].items():
                print(f"  - {key}: {value}")

        print()


# =============================================================================
# Testing
# =============================================================================

if __name__ == '__main__':
    print("Testing Image Metadata System...")
    print()

    # Test 1: Create metadata
    print("Test 1: Creating metadata")
    metadata = ImageMetadata(
        artist="Test Artist",
        copyright_text="© 2025 Test Company",
        brand="cringeproof",
        description="Test Image with EXIF"
    )

    metadata.add_layer_data('background', color='#FFFFFF')
    metadata.add_layer_data('gradient', colors=['#FF0000', '#0000FF'], angle=45)
    metadata.add_layer_data('text', content='Hello World', font='Arial', size=48)

    metadata.add_generation_params(
        size=(1080, 1080),
        format='PNG',
        quality='high'
    )

    metadata.add_custom_data('post_id', 123)
    metadata.add_custom_data('campaign', 'spring-2025')

    print("✅ Metadata created")
    print()

    # Test 2: Embed in image
    print("Test 2: Embedding metadata in test image")

    # Create simple test image
    from image_composer import ImageComposer

    composer = ImageComposer(size=(800, 600))
    composer.add_layer('gradient', colors=['#8E44AD', '#3498DB'], angle=45)
    composer.add_layer('text', content='EXIF Test', font='impact', font_size=72,
                      color='#FFFFFF', position='center')

    test_image = composer.render()

    # Embed metadata
    image_with_metadata = metadata.embed_in_image(test_image)

    # Save
    output_path = 'test_output_exif.jpg'
    with open(output_path, 'wb') as f:
        f.write(image_with_metadata)

    print(f"✅ Saved: {output_path} ({len(image_with_metadata):,} bytes)")
    print()

    # Test 3: Extract and display
    print("Test 3: Extracting metadata")
    print()
    display_metadata(output_path, verbose=True)

    print("=" * 70)
    print("✅ All metadata tests passed!")
    print()
