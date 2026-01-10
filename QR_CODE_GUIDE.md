# QR Code Technology - Complete Guide

## What is a QR Code?

**QR Code** (Quick Response Code) is a **2D barcode** invented in 1994 by Denso Wave (Toyota subsidiary) for tracking automotive parts. Unlike traditional 1D barcodes (like UPC), QR codes can store significantly more data and can be scanned from any angle.

### Key Characteristics

- **Invented**: 1994 by Masahiro Hara (Denso Wave, Japan)
- **Type**: 2D matrix barcode (two-dimensional)
- **Capacity**: Up to 4,296 alphanumeric characters
- **Error Correction**: Built-in Reed-Solomon error correction
- **Scan Direction**: Omnidirectional (360° readable)
- **Open Standard**: ISO/IEC 18004:2015

---

## QR Code Capacity

### Data Limits by Version

QR codes come in 40 versions (sizes), from Version 1 (21x21 modules) to Version 40 (177x177 modules):

| Version | Size (modules) | Numeric | Alphanumeric | Binary (bytes) | Kanji |
|---------|---------------|---------|--------------|----------------|-------|
| V1      | 21×21         | 41      | 25           | 17             | 10    |
| V5      | 37×37         | 174     | 106          | 72             | 44    |
| V10     | 57×57         | 652     | 395          | 271            | 167   |
| V20     | 97×97         | 2,953   | 1,784        | 1,224          | 755   |
| V30     | 137×137       | 5,596   | 3,391        | 2,331          | 1,435 |
| V40     | 177×177       | 7,089   | 4,296        | 2,953          | 1,817 |

**Error Correction Levels** (trade-off: more correction = less capacity):
- **L** (Low): 7% damage recovery
- **M** (Medium): 15% damage recovery ← **Most common**
- **Q** (Quartile): 25% damage recovery
- **H** (High): 30% damage recovery ← **Recommended for logos**

---

## QR Code vs Other Technologies

### 1. **QR Code vs Barcode (1D)**

| Feature | QR Code | 1D Barcode (UPC/EAN) |
|---------|---------|----------------------|
| Data capacity | 4,296 chars | 12-20 digits |
| Dimensions | 2D (height + width) | 1D (width only) |
| Error correction | Yes (7-30%) | No |
| Scan angle | Any angle | Horizontal only |
| Best for | URLs, JSON, documents | Product IDs |

**Use QR when**: You need to embed URLs, structured data (JSON), or more than 20 characters.

### 2. **QR Code vs RFID**

| Feature | QR Code | RFID |
|---------|---------|------|
| Cost | Free (just print) | $0.10-$50 per tag |
| Read distance | 10cm-1m (visual scan) | 1cm-100m (radio waves) |
| Line of sight | Required | NOT required |
| Power | Passive (no battery) | Passive or active |
| Durability | Paper-based | Chip embedded |
| Data capacity | 4,296 chars | 2 KB typical |
| Best for | Printed materials, receipts | Inventory tracking, access control |

**Use QR when**: Budget-constrained, printed media, customer-facing use cases.

**Use RFID when**: Need to scan without line-of-sight (e.g., warehouse pallets, contactless payment, asset tracking through walls).

### 3. **QR Code vs NFC**

| Feature | QR Code | NFC (Near Field Communication) |
|---------|---------|-------------------------------|
| Cost | Free | $0.10-$5 per tag |
| Read distance | 10cm-1m | 4cm max (tap distance) |
| Speed | 1-2 seconds | <0.1 seconds |
| Device support | Any camera phone | Requires NFC chip (Android, iPhone 7+) |
| Security | Visual only | Encrypted communication |
| Best for | Marketing, menus, documents | Payments, access cards, device pairing |

**Use QR when**: Wide compatibility needed, printed materials, visual verification.

**Use NFC when**: Contactless payments, high-security access, device-to-device communication.

### 4. **QR Code vs Bluetooth Beacons**

| Feature | QR Code | Bluetooth Beacon |
|---------|---------|------------------|
| Cost | Free | $5-$30 per beacon |
| Range | 10cm-1m | 1-100m |
| Power | None (passive) | Battery (1-5 years) |
| User action | Manual scan | Auto-detect (background) |
| Privacy | Opt-in (scan) | Passive tracking possible |
| Best for | Explicit user intent | Proximity marketing, indoor positioning |

**Use QR when**: User must explicitly opt-in, one-time interactions, printed materials.

**Use Bluetooth when**: Proximity detection, location-based push notifications, indoor navigation.

---

## Mesh Networks & QR Codes

### Can QR Codes Create a Mesh Network?

**Short answer**: No, not directly. QR codes are passive data storage, not communication devices.

**However**, you can use QR codes to **bootstrap** mesh networks:

1. **Scenario**: Offline QR code mesh
   - Each QR code embeds a **node ID** and **connection instructions**
   - Scanning QR → phone connects to local WiFi/Bluetooth mesh
   - QR codes act as "entry points" to the mesh

2. **Example Use Case**: Disaster recovery
   - Deploy QR codes on posters around disaster zone
   - Each QR connects to local mesh network node
   - People scan QR → join mesh → share info without internet

3. **How to Build**:
   ```json
   {
     "mesh_node_id": "node-42",
     "wifi_ssid": "DisasterMesh-42",
     "wifi_password": "rescue2025",
     "bluetooth_uuid": "550e8400-e29b-41d4-a716-446655440000",
     "join_instructions": "Connect to WiFi, open app"
   }
   ```

### QR + LoRa Mesh

**Use case**: Long-range offline communication

- QR code embeds **LoRa device ID** and **frequency**
- User scans QR → phone app connects to LoRa device via Bluetooth
- LoRa device relays messages through mesh (range: 5-15km)

**Example**: Forest fire evacuation QR codes on trails

---

## Event-Based Automation with QR Codes

### Webhook Triggers

QR codes can trigger automated workflows when scanned:

```python
# Example: QR code scan triggers webhook
{
  "event": "qr_scanned",
  "qr_id": "INV-2025-001",
  "timestamp": "2025-12-30T14:00:00Z",
  "location": {"lat": 37.7749, "lon": -122.4194},
  "actions": [
    {"type": "send_email", "to": "customer@example.com"},
    {"type": "update_crm", "status": "delivered"},
    {"type": "generate_analytics", "metric": "qr_engagement"}
  ]
}
```

### Common Event Triggers

1. **Payment Received** → Auto-generate receipt QR
2. **Invoice Created** → Auto-generate invoice QR with payment link
3. **Order Shipped** → Auto-generate tracking QR
4. **Customer Check-in** → Auto-generate loyalty points QR
5. **Product Scanned** → Auto-update inventory

### Event-Driven Architecture

```
[Stripe Payment] → Webhook → [Generate Receipt QR] → [Email to Customer]
[New Invoice] → Event Bus → [Create QR + PDF] → [Save to Cloud]
[QR Scanned] → Analytics → [Update Dashboard] → [Send Alert]
```

---

## QR Code Security

### Offline Verification (Bloomberg/Symphony-Style)

**Problem**: How to verify a QR code is legitimate without internet?

**Solution**: Cryptographic signatures embedded in QR code

```json
{
  "invoice_id": "INV-2025-001",
  "amount": 100.00,
  "customer": "John Doe",
  "hash": "sha256:a3f5b8c9d1e2f3...",
  "signature": "hmac:9f7e6d5c4b3a2..."
}
```

**Verification Steps**:
1. Scan QR → Extract JSON
2. Compute SHA-256 hash of invoice data
3. Verify HMAC signature with secret key
4. Compare hash with embedded hash
5. ✅ Valid if both match

**Why This Works**:
- Tamper-proof: Changing any data breaks the signature
- Offline: No internet needed to verify
- Fast: Hash verification takes <0.01 seconds
- Same tech as Bloomberg Terminal, Symphony messaging

---

## QR Code Best Practices

### When to Use QR Codes

✅ **Good Use Cases**:
- Restaurant menus (COVID-era innovation)
- Product packaging (specs, manuals, warranties)
- Event tickets (offline verification)
- Business cards (LinkedIn, contact info)
- Invoices & receipts (full document embedded)
- Marketing campaigns (trackable URLs)
- Wi-Fi network sharing
- Cryptocurrency wallet addresses

❌ **Bad Use Cases**:
- Security access (use RFID/NFC instead)
- Real-time tracking (use GPS/Bluetooth)
- Underwater scanning (use RFID)
- Long-distance identification (use Bluetooth beacons)

### Design Tips

1. **Size**: Minimum 2×2 cm (0.8×0.8 inches) for reliable scanning
2. **Contrast**: High contrast (black on white) scans best
3. **Quiet Zone**: Maintain white border around QR (4 modules wide)
4. **Error Correction**: Use Level H if adding logo/branding
5. **Testing**: Test with multiple devices and lighting conditions

---

## Advanced QR Features

### 1. **Animated QR Codes**

Generate GIF QR codes with pulsing effects:
- Attracts attention
- Cycles through multiple URLs
- Works with any QR scanner

**Use case**: Event promotion (scan reveals different prizes each second)

### 2. **Logo Embedding**

Add brand logo to center of QR:
- Use error correction level H (30% damage tolerance)
- Logo should cover <20% of QR area
- Test thoroughly after adding logo

### 3. **Gradient & Styling**

Modern QR codes support:
- Gradient colors (dual-color overlays)
- Rounded corners (better aesthetics)
- Custom shapes (circles, triangles)
- Branded colors (maintain contrast)

**Warning**: Heavy styling can reduce scan reliability. Always test!

---

## QR Code Standards

### ISO/IEC 18004:2015

The official QR code standard defines:
- 40 versions (21×21 to 177×177 modules)
- 4 error correction levels (L/M/Q/H)
- 4 encoding modes: Numeric, Alphanumeric, Byte, Kanji
- Reed-Solomon error correction algorithm

### Micro QR Code

Smaller variant for limited space:
- Versions M1 to M4 (11×11 to 17×17 modules)
- Capacity: 35 numeric / 21 alphanumeric
- Use case: Small products, jewelry tags

---

## QR Code Future

### Emerging Trends (2025-2026)

1. **AR-Enhanced QR Codes**: Scan QR → 3D AR experience
2. **Dynamic QR Codes**: QR content changes based on time/location
3. **Blockchain QR**: Verify product authenticity via blockchain
4. **Audio QR**: Embed audio files (compressed MP3 in QR)
5. **Multi-QR Linking**: Chain multiple QR codes for large datasets

---

## Summary

| Technology | Best For | Cost | Range |
|-----------|----------|------|-------|
| **QR Code** | URLs, documents, receipts | Free | Visual (1m) |
| **RFID** | Inventory, access control | $0.10-$50 | 1cm-100m |
| **NFC** | Payments, device pairing | $0.10-$5 | 4cm |
| **Bluetooth** | Proximity marketing | $5-$30 | 1-100m |
| **LoRa** | Long-range mesh | $10-$100 | 5-15km |

**Choose QR codes when**: Budget is tight, wide device compatibility needed, printed media, explicit user opt-in required.

---

## Resources

- **QR Code Generator**: https://qr-code-generator.com
- **ISO Standard**: https://www.iso.org/standard/62021.html
- **QR Code Capacity Calculator**: https://www.qrcode.com/en/about/version.html
- **Error Correction Explained**: https://www.thonky.com/qr-code-tutorial/error-correction-coding

---

**Built with Soulfra QR System** 🚀
