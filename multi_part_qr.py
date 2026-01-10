#!/usr/bin/env python3
"""
Multi-Part QR Code Generator - Stackable QR Codes (Like Floppy Disks)

This module splits large content into multiple QR codes that can be scanned
in any order and reassembled on the client side.

Use Cases:
- Newsletters >4,000 characters
- Brand wordmaps (large vocabulary exports)
- Product manuals
- Event schedules
- Recipe collections

Example:
    from multi_part_qr import MultiPartQRGenerator
    
    generator = MultiPartQRGenerator(max_size=4000)
    qr_parts = generator.split_and_generate(large_newsletter)
    
    # Returns QR 1/3, QR 2/3, QR 3/3
    # User scans all 3 → Phone assembles full content
"""

import qrcode
import json
import hashlib
from typing import List, Dict, Tuple
from io import BytesIO
import base64


class MultiPartQRGenerator:
    """
    Generate multi-part QR codes for large content
    
    Features:
    - Automatic chunking based on QR capacity
    - Metadata headers in each part
    - Client-side assembly
    - Can scan in any order
    - Progress tracking
    """
    
    def __init__(self, max_size: int = 2500, error_correction='M'):
        """
        Initialize multi-part QR generator
        
        Args:
            max_size: Max characters per QR code (default 3800 to leave room for metadata)
            error_correction: QR error correction level (L/M/Q/H)
        """
        self.max_size = max_size
        self.error_correction = error_correction
        
    def split_and_generate(
        self,
        content: str,
        brand: str = 'soulfra',
        content_type: str = 'text'
    ) -> List[Dict]:
        """
        Split large content into multiple QR codes
        
        Args:
            content: Large text content to split
            brand: Brand slug for styling
            content_type: Type of content ('text', 'json', 'wordmap', etc.)
        
        Returns:
            List of parts: [{
                'part': 1,
                'total': 3,
                'id': 'abc123',
                'qr_bytes': b'...',
                'data_chunk': 'chunk...',
                'metadata': {...}
            }]
        """
        # Generate unique ID for this multi-part set
        content_id = self._generate_id(content)
        
        # Split content into chunks
        chunks = self._split_content(content)
        
        # Generate QR code for each chunk
        parts = []
        total_parts = len(chunks)
        
        for i, chunk in enumerate(chunks, 1):
            # Create metadata header
            metadata = {
                'part': i,
                'total': total_parts,
                'id': content_id,
                'brand': brand,
                'type': content_type,
                'chunk_size': len(chunk)
            }
            
            # Combine metadata + data
            qr_data = {
                'meta': metadata,
                'data': chunk
            }
            
            # Encode as JSON
            json_data = json.dumps(qr_data)
            
            # Generate QR code
            qr_bytes = self._generate_qr(json_data)
            
            parts.append({
                'part': i,
                'total': total_parts,
                'id': content_id,
                'qr_bytes': qr_bytes,
                'data_chunk': chunk,
                'metadata': metadata
            })
        
        return parts
    
    def _split_content(self, content: str) -> List[str]:
        """
        Split content into chunks that fit in QR codes

        Args:
            content: Full content to split

        Returns:
            List of content chunks
        """
        # Reserve space for metadata + JSON overhead (~800 chars to be safe)
        # JSON structure adds: {"meta":{...},"data":"..."} plus escaping
        chunk_size = self.max_size - 800
        
        chunks = []
        current_pos = 0
        
        while current_pos < len(content):
            chunk = content[current_pos:current_pos + chunk_size]
            chunks.append(chunk)
            current_pos += chunk_size
        
        return chunks
    
    def _generate_id(self, content: str) -> str:
        """
        Generate unique ID for multi-part set
        
        Args:
            content: Full content
        
        Returns:
            Short hash ID (8 characters)
        """
        hash_obj = hashlib.sha256(content.encode())
        return hash_obj.hexdigest()[:8]
    
    def _generate_qr(self, data: str) -> bytes:
        """
        Generate QR code from data
        
        Args:
            data: JSON string to encode
        
        Returns:
            QR code PNG bytes
        """
        # Map error correction levels
        ec_map = {
            'L': qrcode.constants.ERROR_CORRECT_L,
            'M': qrcode.constants.ERROR_CORRECT_M,
            'Q': qrcode.constants.ERROR_CORRECT_Q,
            'H': qrcode.constants.ERROR_CORRECT_H
        }
        
        qr = qrcode.QRCode(
            version=None,  # Auto-select version
            error_correction=ec_map.get(self.error_correction, qrcode.constants.ERROR_CORRECT_M),
            box_size=10,
            border=4
        )
        
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to bytes
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        return img_bytes.read()
    
    @staticmethod
    def assemble_parts(scanned_parts: List[Dict]) -> Tuple[bool, str]:
        """
        Assemble multi-part QR codes back into full content
        
        This would run client-side (JavaScript) but here's the logic:
        
        Args:
            scanned_parts: List of scanned QR data dicts
        
        Returns:
            (success, assembled_content or error_message)
        """
        # Validate all parts have same ID
        ids = {part['meta']['id'] for part in scanned_parts}
        if len(ids) > 1:
            return False, "Parts from different QR sets"
        
        # Check if we have all parts
        total_parts = scanned_parts[0]['meta']['total']
        if len(scanned_parts) != total_parts:
            return False, f"Missing parts: have {len(scanned_parts)}/{total_parts}"
        
        # Sort by part number
        sorted_parts = sorted(scanned_parts, key=lambda p: p['meta']['part'])
        
        # Assemble content
        full_content = ''.join([part['data'] for part in sorted_parts])
        
        return True, full_content


# =============================================================================
# Convenience Functions
# =============================================================================

def generate_multipart_newsletter(newsletter_text: str, brand: str = 'soulfra') -> List[Dict]:
    """
    Quick helper: Generate multi-part QR for newsletter
    
    Args:
        newsletter_text: Full newsletter content
        brand: Brand slug
    
    Returns:
        List of QR parts
    """
    generator = MultiPartQRGenerator()
    return generator.split_and_generate(newsletter_text, brand=brand, content_type='newsletter')


def generate_multipart_wordmap(wordmap: Dict, brand: str = 'soulfra') -> List[Dict]:
    """
    Quick helper: Generate multi-part QR for brand wordmap
    
    Args:
        wordmap: Brand word frequency dict
        brand: Brand slug
    
    Returns:
        List of QR parts
    """
    # Convert wordmap to pretty JSON
    wordmap_json = json.dumps(wordmap, indent=2)
    
    generator = MultiPartQRGenerator()
    return generator.split_and_generate(wordmap_json, brand=brand, content_type='wordmap')


def save_qr_parts(parts: List[Dict], output_dir: str = '.'):
    """
    Save QR parts to PNG files
    
    Args:
        parts: List of QR parts from split_and_generate()
        output_dir: Directory to save files
    """
    import os
    
    for part in parts:
        filename = f"qr_part_{part['part']}_of_{part['total']}_{part['id']}.png"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'wb') as f:
            f.write(part['qr_bytes'])
        
        print(f"✓ Saved: {filename} ({len(part['data_chunk'])} chars)")


# =============================================================================
# Demo
# =============================================================================

if __name__ == '__main__':
    print("=== Multi-Part QR Generator Demo ===\n")
    
    # Example 1: Large newsletter
    newsletter = """
    # Soulfra Newsletter - Week 1
    
    Welcome to the first edition of the Soulfra newsletter!
    
    ## This Week's Updates
    
    1. **New Features**
       - Multi-part QR code system (you're reading this via QR!)
       - Brand wordmap API
       - Newsletter digest improvements
    
    2. **Platform Stats**
       - 4 brands active (Soulfra, DeathToData, Cringeproof, HowToCookAtHome)
       - 15+ QR systems running
       - 4 neural networks trained
    
    3. **Coming Soon**
       - QR code import/export
       - Stackable QR for large content
       - Mobile assembly interface
    
    ## How Multi-Part QR Works
    
    Large content is automatically split into multiple QR codes:
    - Each QR holds ~3,800 characters
    - Scan all parts in any order
    - Phone assembles full content
    - Like floppy disks but for QR codes!
    
    ## Example Use Cases
    
    - Product manuals (100+ pages → QR codes on packaging)
    - Event schedules (full agenda → QR on conference badge)
    - Recipe collections (cookbook → stackable QR)
    - Brand wordmaps (5,000 words → export as QR)
    
    ## Get Involved
    
    Visit http://192.168.1.87:5001 to try the platform!
    
    ---
    
    Built with Soulfra 🚀
    """  # Already large enough for multiple QR codes

    # Generate multi-part QR
    generator = MultiPartQRGenerator(max_size=2500)
    parts = generator.split_and_generate(newsletter, brand='soulfra', content_type='newsletter')
    
    print(f"Newsletter size: {len(newsletter)} characters")
    print(f"Split into: {len(parts)} QR codes\n")
    
    for part in parts:
        print(f"Part {part['part']}/{part['total']}:")
        print(f"  ID: {part['id']}")
        print(f"  Chunk size: {len(part['data_chunk'])} chars")
        print(f"  QR image: {len(part['qr_bytes'])} bytes")
        print()
    
    # Save to files
    print("Saving QR codes...")
    save_qr_parts(parts, output_dir='.')
    
    print("\n✓ Demo complete!")
    print(f"\nGenerated {len(parts)} QR code files:")
    print("  - Scan all QR codes with your phone")
    print("  - Phone will assemble full newsletter")
    print("  - Works offline (all data in QR codes)")
