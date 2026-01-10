#!/usr/bin/env python3
"""
Demo: Multi-Part QR Codes (Stackable Like Floppy Disks)

Shows how large content is split across multiple QR codes.
"""

from multi_part_qr import MultiPartQRGenerator, save_qr_parts

# Create large newsletter (>6,000 chars to force 3+ QR codes)
large_newsletter = """
# Soulfra Newsletter - Week 1

Welcome to the first edition of the Soulfra newsletter!

## This Week's Updates

1. **New Features**
   - Multi-part QR code system (you're reading this via QR!)
   - Brand wordmap API
   - Newsletter digest improvements
   - QR gallery system
   - Business QR for invoices/receipts
   - DM via QR (proximity-based messaging)
   - Advanced QR styling (gradients, logos)

2. **Platform Stats**
   - 4 brands active (Soulfra, DeathToData, Cringeproof, HowToCookAtHome)
   - 15+ QR systems running
   - 4 neural networks trained
   - 200+ blog posts
   - 50+ practice rooms
   - 12 learning card decks

3. **Coming Soon**
   - QR code import/export
   - Stackable QR for large content ✅ (you're using it now!)
   - Mobile assembly interface
   - QR analytics dashboard
   - Multi-tenant support
   - API key generation

## How Multi-Part QR Works

Large content is automatically split into multiple QR codes:
- Each QR holds ~2,500 characters (to leave room for metadata)
- Scan all parts in any order
- Phone assembles full content
- Like floppy disks but for QR codes!

Think of it like this:
- Disk 1 of 3: First chunk of content
- Disk 2 of 3: Second chunk of content
- Disk 3 of 3: Final chunk of content

Your phone keeps track of which parts you've scanned and assembles them in the correct order.

## Example Use Cases

**1. Product Manuals**
- 100+ page manual → 10 QR codes on packaging
- Scan all QR codes → Full manual on phone
- Works offline (no internet required)

**2. Event Schedules**
- Full conference agenda → 5 QR codes on badge
- Scan all → Complete schedule with maps, speaker bios, session details
- Updates pushed via new QR codes

**3. Recipe Collections**
- Entire cookbook → Stackable QR on book cover
- Scan → Get all recipes, photos, videos
- Share with friends via QR

**4. Brand Wordmaps**
- 5,000 word vocabulary → Export as multi-part QR
- Import on new device
- Offline vocabulary transfer

**5. Newsletters Like This One**
- Long-form content → Multiple QR codes
- Print in magazine → Scan to read full article
- No typing URLs!

## Technical Details

### QR Code Capacity
- QR Version 1: 25 chars
- QR Version 10: 174 chars
- QR Version 20: 858 chars
- QR Version 40 (max): 4,296 alphanumeric chars

### Metadata Format
Each QR code contains:
```json
{
  "meta": {
    "part": 1,
    "total": 3,
    "id": "abc123",
    "brand": "soulfra",
    "type": "newsletter",
    "chunk_size": 2400
  },
  "data": "First chunk of content..."
}
```

### Assembly Algorithm
1. Scan QR code → Extract metadata + data
2. Check if you have all parts (part 1/3, 2/3, 3/3)
3. Sort by part number
4. Concatenate data chunks
5. Verify content ID matches across all parts
6. Display assembled content

## Get Involved

Visit http://192.168.1.87:5001 to try the platform!

### Available Endpoints:
- `/business` - Create invoices/receipts with QR codes
- `/qr/create` - Vanity URL shortener
- `/gallery/<slug>` - Image galleries
- `/learn` - Spaced repetition learning
- `/chat` - AI assistant

### Open Source
- Pure Python + SQLite (no complex dependencies)
- Neural networks built from scratch (NumPy only)
- 15+ QR systems
- 39+ documentation files
- Offline-first design

## Future Vision

**Phase 1** (Current):
- Multi-part QR for large content ✅
- Business QR for invoices ✅
- Vanity QR for URL shortening ✅

**Phase 2** (Next):
- QR code versioning (track changes)
- Blockchain verification (tamper-proof)
- Multi-language support
- QR expiration dates

**Phase 3** (Future):
- Hosted SaaS platform
- API marketplace
- Mobile app for scanning/assembly
- Analytics dashboard

---

Built with Soulfra 🚀

**Questions?** Check out our docs:
- START_HERE.md - Platform overview
- SOP.md - Git-like workflows
- QR_SYSTEMS_MAP.md - QR architecture
- BRAND_ONBOARDING.md - Brand system

**Want to contribute?** We're open source!
Visit github.com/soulfra/platform
"""

# Generate multi-part QR
print("=== Multi-Part QR Generator Demo ===\n")
print(f"Newsletter size: {len(large_newsletter)} characters")

generator = MultiPartQRGenerator(max_size=2500)
parts = generator.split_and_generate(large_newsletter, brand='soulfra', content_type='newsletter')

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
print("\nFiles saved:")
for part in parts:
    print(f"  - qr_part_{part['part']}_of_{part['total']}_{part['id']}.png")
