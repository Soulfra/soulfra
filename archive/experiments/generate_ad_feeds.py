#!/usr/bin/env python3
"""
Generate ad feeds for different marketing platforms.

Tier System:
- Tier 1: Google Ads (premium products, highest budget)
- Tier 2: Facebook Ads (mid-tier products)
- Tier 3: Organic (free/low-budget products)

Output Formats:
- Google Shopping XML (tier 1)
- Facebook Product Catalog JSON (tier 2)
- Generic Product JSON (all tiers)
- RSS Product Feed (all tiers)
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET
from xml.dom import minidom


def get_products_by_tier(tier=None):
    """Get products from database, optionally filtered by tier."""
    db = sqlite3.connect('soulfra.db')
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    if tier:
        query = """
            SELECT
                p.*,
                b.name as brand_name,
                b.slug as brand_slug,
                b.tagline as brand_tagline,
                b.category as brand_category,
                b.color_primary,
                b.tier as brand_tier
            FROM products p
            JOIN brands b ON p.brand_id = b.id
            WHERE p.ad_tier = ?
            ORDER BY p.brand_id, p.type, p.price DESC
        """
        cursor.execute(query, (tier,))
    else:
        query = """
            SELECT
                p.*,
                b.name as brand_name,
                b.slug as brand_slug,
                b.tagline as brand_tagline,
                b.category as brand_category,
                b.color_primary,
                b.tier as brand_tier
            FROM products p
            JOIN brands b ON p.brand_id = b.id
            ORDER BY p.ad_tier, p.brand_id, p.type, p.price DESC
        """
        cursor.execute(query)

    products = cursor.fetchall()
    db.close()

    return [dict(p) for p in products]


def generate_google_shopping_xml(products, output_file):
    """
    Generate Google Shopping feed (XML format).

    Spec: https://support.google.com/merchants/answer/7052112
    """
    # Create RSS feed root
    rss = ET.Element('rss', {
        'version': '2.0',
        'xmlns:g': 'http://base.google.com/ns/1.0'
    })
    channel = ET.SubElement(rss, 'channel')

    # Channel metadata
    ET.SubElement(channel, 'title').text = 'Soulfra Product Catalog'
    ET.SubElement(channel, 'link').text = 'https://soulfra.com'
    ET.SubElement(channel, 'description').text = 'Privacy-focused products and APIs'

    for product in products:
        item = ET.SubElement(channel, 'item')

        # Required fields
        ET.SubElement(item, '{http://base.google.com/ns/1.0}id').text = product['sku']
        ET.SubElement(item, '{http://base.google.com/ns/1.0}title').text = product['name']
        ET.SubElement(item, '{http://base.google.com/ns/1.0}description').text = product['description'] or product['name']
        ET.SubElement(item, '{http://base.google.com/ns/1.0}link').text = f"https://soulfra.com/products/{product['sku'].lower()}"
        ET.SubElement(item, '{http://base.google.com/ns/1.0}image_link').text = f"https://soulfra.com/images/products/{product['sku'].lower()}.png"
        ET.SubElement(item, '{http://base.google.com/ns/1.0}availability').text = 'in stock' if product['stock_quantity'] > 0 else 'out of stock'
        ET.SubElement(item, '{http://base.google.com/ns/1.0}price').text = f"{product['price']:.2f} USD"
        ET.SubElement(item, '{http://base.google.com/ns/1.0}brand').text = product['brand_name']
        ET.SubElement(item, '{http://base.google.com/ns/1.0}gtin').text = product['upc']
        ET.SubElement(item, '{http://base.google.com/ns/1.0}condition').text = 'new'

        # Category mapping
        category_map = {
            'merch': 'Apparel & Accessories',
            'api': 'Software',
            'email': 'Media > Books & Magazines',
            'service': 'Business & Industrial'
        }
        ET.SubElement(item, '{http://base.google.com/ns/1.0}google_product_category').text = category_map.get(product['type'], 'Software')

        # Custom labels for campaign organization
        ET.SubElement(item, '{http://base.google.com/ns/1.0}custom_label_0').text = product['brand_slug']
        ET.SubElement(item, '{http://base.google.com/ns/1.0}custom_label_1').text = product['type']
        ET.SubElement(item, '{http://base.google.com/ns/1.0}custom_label_2').text = f"tier_{product['ad_tier']}"
        ET.SubElement(item, '{http://base.google.com/ns/1.0}custom_label_3').text = product['brand_category']

    # Pretty print XML
    xml_str = minidom.parseString(ET.tostring(rss)).toprettyxml(indent='  ')

    with open(output_file, 'w') as f:
        f.write(xml_str)

    return output_file


def generate_facebook_catalog_json(products, output_file):
    """
    Generate Facebook Product Catalog (JSON format).

    Spec: https://developers.facebook.com/docs/marketing-api/catalog/reference
    """
    catalog = []

    for product in products:
        catalog.append({
            'id': product['sku'],
            'title': product['name'],
            'description': product['description'] or product['name'],
            'availability': 'in stock' if product['stock_quantity'] > 0 else 'out of stock',
            'condition': 'new',
            'price': f"{product['price']:.2f} USD",
            'link': f"https://soulfra.com/products/{product['sku'].lower()}",
            'image_link': f"https://soulfra.com/images/products/{product['sku'].lower()}.png",
            'brand': product['brand_name'],
            'gtin': product['upc'],
            'product_type': product['type'],
            'custom_label_0': product['brand_slug'],
            'custom_label_1': f"tier_{product['ad_tier']}",
            'custom_label_2': product['brand_category'],
        })

    with open(output_file, 'w') as f:
        json.dump(catalog, f, indent=2)

    return output_file


def generate_product_rss(products, output_file):
    """
    Generate RSS 2.0 product feed (compatible with most feed readers).
    """
    rss = ET.Element('rss', {'version': '2.0'})
    channel = ET.SubElement(rss, 'channel')

    # Channel metadata
    ET.SubElement(channel, 'title').text = 'Soulfra Products'
    ET.SubElement(channel, 'link').text = 'https://soulfra.com/products'
    ET.SubElement(channel, 'description').text = 'Privacy-focused products and APIs'
    ET.SubElement(channel, 'language').text = 'en-us'
    ET.SubElement(channel, 'lastBuildDate').text = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')

    for product in products:
        item = ET.SubElement(channel, 'item')

        ET.SubElement(item, 'title').text = f"{product['brand_name']}: {product['name']}"
        ET.SubElement(item, 'link').text = f"https://soulfra.com/products/{product['sku'].lower()}"
        ET.SubElement(item, 'description').text = f"{product['description'] or product['name']} | ${product['price']:.2f} | {product['brand_category']}"
        ET.SubElement(item, 'guid', {'isPermaLink': 'false'}).text = product['sku']
        ET.SubElement(item, 'pubDate').text = datetime.fromisoformat(product['created_at']).strftime('%a, %d %b %Y %H:%M:%S GMT')
        ET.SubElement(item, 'category').text = product['type']

    xml_str = minidom.parseString(ET.tostring(rss)).toprettyxml(indent='  ')

    with open(output_file, 'w') as f:
        f.write(xml_str)

    return output_file


def generate_generic_json(products, output_file):
    """
    Generate generic JSON product feed (for custom integrations).
    """
    feed = {
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'product_count': len(products),
        'products': []
    }

    for product in products:
        feed['products'].append({
            'id': product['id'],
            'sku': product['sku'],
            'upc': product['upc'],
            'name': product['name'],
            'description': product['description'],
            'type': product['type'],
            'price': product['price'],
            'stock_quantity': product['stock_quantity'],
            'ad_tier': product['ad_tier'],
            'brand': {
                'id': product['brand_id'],
                'name': product['brand_name'],
                'slug': product['brand_slug'],
                'tagline': product['brand_tagline'],
                'category': product['brand_category'],
                'color': product['color_primary']
            },
            'urls': {
                'product': f"https://soulfra.com/products/{product['sku'].lower()}",
                'image': f"https://soulfra.com/images/products/{product['sku'].lower()}.png",
                'api_endpoint': product['endpoint'] if product['type'] == 'api' else None
            },
            'created_at': product['created_at']
        })

    with open(output_file, 'w') as f:
        json.dump(feed, f, indent=2)

    return output_file


def generate_all_feeds():
    """Generate all ad feeds organized by tier."""
    output_dir = Path('feeds')
    output_dir.mkdir(exist_ok=True)

    print("📢 Ad Feed Generator\n")

    # Tier 1: Google Ads (premium)
    tier1_products = get_products_by_tier(1)
    if tier1_products:
        google_file = output_dir / 'google-shopping-tier1.xml'
        generate_google_shopping_xml(tier1_products, google_file)
        print(f"✅ Tier 1 (Google Ads): {len(tier1_products)} products → {google_file}")
    else:
        print("⚠️  Tier 1 (Google Ads): No products")

    # Tier 2: Facebook Ads (mid-tier)
    tier2_products = get_products_by_tier(2)
    if tier2_products:
        facebook_file = output_dir / 'facebook-catalog-tier2.json'
        generate_facebook_catalog_json(tier2_products, facebook_file)
        print(f"✅ Tier 2 (Facebook Ads): {len(tier2_products)} products → {facebook_file}")
    else:
        print("⚠️  Tier 2 (Facebook Ads): No products")

    # Tier 3: Organic (low-budget)
    tier3_products = get_products_by_tier(3)
    if tier3_products:
        rss_file = output_dir / 'organic-products-tier3.rss'
        generate_product_rss(tier3_products, rss_file)
        print(f"✅ Tier 3 (Organic): {len(tier3_products)} products → {rss_file}")
    else:
        print("⚠️  Tier 3 (Organic): No products")

    # All products (generic JSON)
    all_products = get_products_by_tier()
    if all_products:
        json_file = output_dir / 'all-products.json'
        generate_generic_json(all_products, json_file)
        print(f"✅ All tiers (Generic JSON): {len(all_products)} products → {json_file}")

        # Also generate a combined RSS
        rss_all_file = output_dir / 'all-products.rss'
        generate_product_rss(all_products, rss_all_file)
        print(f"✅ All tiers (RSS): {len(all_products)} products → {rss_all_file}")

    print()
    print("📊 Feed Summary:")
    print(f"   Total products: {len(all_products)}")
    print(f"   Tier 1 (Google): {len(tier1_products)} products")
    print(f"   Tier 2 (Facebook): {len(tier2_products)} products")
    print(f"   Tier 3 (Organic): {len(tier3_products)} products")
    print()
    print(f"📁 All feeds saved to: {output_dir.absolute()}/")

    return {
        'tier1': len(tier1_products),
        'tier2': len(tier2_products),
        'tier3': len(tier3_products),
        'total': len(all_products)
    }


if __name__ == '__main__':
    generate_all_feeds()
