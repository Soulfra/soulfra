#!/usr/bin/env python3
"""
QR Card Printer - Generate Printable Trading Cards for Soulfra Dark

Creates physical trading cards with QR codes for story chapters.
Perfect for:
- Radio show giveaways
- Physical book distribution
- Collectible card packs
- Convention swag

Usage:
    from qr_card_printer import generate_chapter_card_pack

    pdf_bytes = generate_chapter_card_pack(chapter_number=1)
    with open('chapter_1_cards.pdf', 'wb') as f:
        f.write(pdf_bytes)
"""

from typing import Dict, List, Optional
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import qrcode
from multi_part_qr import MultiPartQRGenerator
from soulfra_dark_story import generate_soulfra_story

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.units import inch
    from reportlab.lib.utils import ImageReader
except ImportError:
    print("⚠️  reportlab not installed. Run: pip install reportlab")
    print("   (Required for PDF generation)")


class QRCardPrinter:
    """
    Generate printable QR trading cards for story chapters

    Card dimensions: 2.5" × 3.5" (standard trading card size)
    Each card contains:
    - QR code (scannable)
    - Chapter title
    - Part number (1/5, 2/5, etc.)
    - Brand logo area
    - Collectible number
    - Visual design
    """

    def __init__(self, brand: str = 'soulfra', card_size: tuple = (2.5, 3.5)):
        """
        Initialize card printer

        Args:
            brand: Brand slug (soulfra, cringeproof, etc.)
            card_size: Card dimensions in inches (width, height)
        """
        self.brand = brand
        self.card_width = card_size[0] * inch
        self.card_height = card_size[1] * inch

        # Brand colors
        self.brand_colors = {
            'soulfra': {
                'primary': '#8B5CF6',    # Purple
                'secondary': '#3B82F6',  # Blue
                'accent': '#10B981',     # Green
                'text': '#FFFFFF'        # White
            },
            'cringeproof': {
                'primary': '#2D3748',
                'secondary': '#E53E3E',
                'accent': '#EDF2F7',
                'text': '#FFFFFF'
            },
            'deathtodata': {
                'primary': '#1F2937',
                'secondary': '#EF4444',
                'accent': '#9CA3AF',
                'text': '#FFFFFF'
            }
        }

    def generate_chapter_card_pack(self, chapter_number: int) -> bytes:
        """
        Generate printable PDF card pack for a chapter

        Args:
            chapter_number: Chapter number (1-7)

        Returns:
            PDF bytes (ready to print)
        """
        # Get chapter data
        chapters = generate_soulfra_story()
        chapter = chapters[chapter_number - 1]

        # Generate multi-part QR codes
        qr_gen = MultiPartQRGenerator(max_size=2500)
        qr_parts = qr_gen.split_and_generate(
            chapter['content'],
            brand=self.brand,
            content_type='chapter'
        )

        # Create PDF
        pdf_buffer = BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=letter)

        # Generate one card per QR part
        for i, part in enumerate(qr_parts):
            # Create card image
            card_img = self._create_card_image(
                chapter_title=chapter['title'],
                chapter_number=chapter_number,
                part_number=part['part'],
                total_parts=part['total'],
                qr_bytes=part['qr_bytes'],
                collectible_id=f"SD-{chapter_number:02d}-{part['part']:02d}"
            )

            # Add card to PDF (centered on page)
            x = (letter[0] - self.card_width) / 2
            y = (letter[1] - self.card_height) / 2

            c.drawImage(
                ImageReader(card_img),
                x, y,
                width=self.card_width,
                height=self.card_height
            )

            c.showPage()  # New page for next card

        c.save()
        pdf_buffer.seek(0)
        return pdf_buffer.read()

    def _create_card_image(
        self,
        chapter_title: str,
        chapter_number: int,
        part_number: int,
        total_parts: int,
        qr_bytes: bytes,
        collectible_id: str
    ) -> Image:
        """
        Create single trading card image

        Card layout:
        ┌─────────────────────┐
        │  SOULFRA            │  ← Header
        │  CHAPTER 1          │
        ├─────────────────────┤
        │                     │
        │    [QR CODE]        │  ← QR Code (centered)
        │                     │
        ├─────────────────────┤
        │  Awakening          │  ← Chapter title
        │  Part 1/3           │  ← Part number
        │  #SD-01-01          │  ← Collectible ID
        └─────────────────────┘
        """
        # Convert inches to pixels (300 DPI for print quality)
        dpi = 300
        width_px = int(2.5 * dpi)   # 750px
        height_px = int(3.5 * dpi)  # 1050px

        # Create blank card
        card = Image.new('RGB', (width_px, height_px), color='#1F2937')
        draw = ImageDraw.Draw(card)

        # Load fonts (try to use system fonts, fallback to default)
        try:
            title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 48)
            subtitle_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
            text_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
        except:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
            text_font = ImageFont.load_default()

        # Colors
        colors = self.brand_colors.get(self.brand, self.brand_colors['soulfra'])

        # Header section (top 15%)
        header_height = int(height_px * 0.15)
        draw.rectangle(
            [(0, 0), (width_px, header_height)],
            fill=colors['primary']
        )

        # Draw brand name
        brand_text = self.brand.upper()
        draw.text(
            (width_px // 2, header_height // 3),
            brand_text,
            fill=colors['text'],
            font=text_font,
            anchor="mm"
        )

        # Draw chapter number
        chapter_text = f"CHAPTER {chapter_number}"
        draw.text(
            (width_px // 2, header_height * 2 // 3),
            chapter_text,
            fill=colors['text'],
            font=subtitle_font,
            anchor="mm"
        )

        # QR Code section (middle 50%)
        qr_top = header_height + 40
        qr_size = int(width_px * 0.7)  # 70% of card width

        # Load QR code image
        qr_img = Image.open(BytesIO(qr_bytes))
        qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)

        # Paste QR code (centered)
        qr_x = (width_px - qr_size) // 2
        card.paste(qr_img, (qr_x, qr_top))

        # Footer section (bottom 35%)
        footer_top = qr_top + qr_size + 40

        # Draw chapter title
        title_y = footer_top
        draw.text(
            (width_px // 2, title_y),
            chapter_title,
            fill=colors['accent'],
            font=title_font,
            anchor="mm"
        )

        # Draw part number
        part_text = f"Part {part_number}/{total_parts}"
        part_y = title_y + 60
        draw.text(
            (width_px // 2, part_y),
            part_text,
            fill=colors['text'],
            font=subtitle_font,
            anchor="mm"
        )

        # Draw collectible ID
        id_y = part_y + 50
        draw.text(
            (width_px // 2, id_y),
            f"#{collectible_id}",
            fill=colors['secondary'],
            font=text_font,
            anchor="mm"
        )

        # Draw bottom border
        border_y = height_px - 20
        draw.line(
            [(40, border_y), (width_px - 40, border_y)],
            fill=colors['primary'],
            width=4
        )

        # Add small "Scan to unlock" text
        hint_y = border_y + 10
        draw.text(
            (width_px // 2, hint_y),
            "SCAN TO UNLOCK",
            fill=colors['text'],
            font=text_font,
            anchor="ma"
        )

        return card

    def generate_full_book_pack(self, book_number: int = 1) -> bytes:
        """
        Generate card pack for entire book (all chapters)

        Args:
            book_number: Book number (1-10)

        Returns:
            PDF bytes with all chapter cards
        """
        chapters = generate_soulfra_story()

        # For now, Book 1 = all 7 chapters
        # Future: Book 2-10 will have 10 chapters each
        pdf_buffer = BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=letter)

        for chapter in chapters:
            # Generate multi-part QR for chapter
            qr_gen = MultiPartQRGenerator(max_size=2500)
            qr_parts = qr_gen.split_and_generate(
                chapter['content'],
                brand=self.brand,
                content_type='chapter'
            )

            # Create card for each part
            for part in qr_parts:
                card_img = self._create_card_image(
                    chapter_title=chapter['title'],
                    chapter_number=chapter['chapter_number'],
                    part_number=part['part'],
                    total_parts=part['total'],
                    qr_bytes=part['qr_bytes'],
                    collectible_id=f"SD-{chapter['chapter_number']:02d}-{part['part']:02d}"
                )

                x = (letter[0] - self.card_width) / 2
                y = (letter[1] - self.card_height) / 2

                c.drawImage(
                    ImageReader(card_img),
                    x, y,
                    width=self.card_width,
                    height=self.card_height
                )

                c.showPage()

        c.save()
        pdf_buffer.seek(0)
        return pdf_buffer.read()


# =============================================================================
# Convenience Functions
# =============================================================================

def generate_chapter_card_pack(chapter_number: int, brand: str = 'soulfra') -> bytes:
    """
    Quick helper: Generate printable card pack for one chapter

    Args:
        chapter_number: Chapter number (1-7)
        brand: Brand slug

    Returns:
        PDF bytes
    """
    printer = QRCardPrinter(brand=brand)
    return printer.generate_chapter_card_pack(chapter_number)


def generate_full_book_pack(brand: str = 'soulfra') -> bytes:
    """
    Quick helper: Generate card pack for entire Book 1 (all 7 chapters)

    Args:
        brand: Brand slug

    Returns:
        PDF bytes
    """
    printer = QRCardPrinter(brand=brand)
    return printer.generate_full_book_pack(book_number=1)


def save_chapter_cards(chapter_number: int, output_path: str = '.', brand: str = 'soulfra'):
    """
    Generate and save chapter card pack to file

    Args:
        chapter_number: Chapter number (1-7)
        output_path: Directory to save file
        brand: Brand slug
    """
    import os

    pdf_bytes = generate_chapter_card_pack(chapter_number, brand=brand)

    filename = f"soulfra_dark_chapter_{chapter_number}_cards.pdf"
    filepath = os.path.join(output_path, filename)

    with open(filepath, 'wb') as f:
        f.write(pdf_bytes)

    print(f"✓ Saved: {filename} ({len(pdf_bytes)} bytes)")
    return filepath


# =============================================================================
# Demo
# =============================================================================

if __name__ == '__main__':
    print("=== QR Card Printer Demo ===\n")

    # Example 1: Generate cards for Chapter 1
    print("Generating cards for Chapter 1...")
    filepath = save_chapter_cards(chapter_number=1, output_path='.')
    print(f"✓ Created: {filepath}\n")

    # Example 2: Generate cards for all chapters
    print("Generating cards for entire Book 1 (7 chapters)...")
    pdf_bytes = generate_full_book_pack(brand='soulfra')

    with open('soulfra_dark_book_1_complete_cards.pdf', 'wb') as f:
        f.write(pdf_bytes)

    print(f"✓ Created: soulfra_dark_book_1_complete_cards.pdf ({len(pdf_bytes)} bytes)\n")

    print("✓ Demo complete!")
    print("\nGenerated Files:")
    print("  - soulfra_dark_chapter_1_cards.pdf")
    print("  - soulfra_dark_book_1_complete_cards.pdf")
    print("\nNext Steps:")
    print("  1. Print cards on cardstock (2.5\" × 3.5\")")
    print("  2. Cut along edges")
    print("  3. Distribute at radio show / conventions")
    print("  4. Listeners scan QR codes → Unlock chapters!")
