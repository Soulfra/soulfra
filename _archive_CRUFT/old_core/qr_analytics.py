#!/usr/bin/env python3
"""
QR Analytics - Lineage Trees & Device/Location Analytics

Visualizes QR scan lineage trees (who scanned whose QR) and provides
device/location breakdowns for viral tracking.

Features:
- ASCII tree visualization of scan lineage
- Device type breakdown (iOS vs Android vs Desktop)
- Location heatmap (city/country)
- Referrer analysis
- HTML dashboard with interactive charts

Usage:
    python3 qr_analytics.py --tree --qr-code 1     # Show lineage tree
    python3 qr_analytics.py --stats --qr-code 1    # Show statistics
    python3 qr_analytics.py --dashboard            # HTML dashboard
    python3 qr_analytics.py --export --qr-code 1   # Export to JSON

Architecture:
    Connects qr_scans (lineage) + qr_codes (totals) + qr_galleries (posts)
    Uses previous_scan_id for parent/child tracking (Git-style)
"""

from database import get_db
from pathlib import Path
import json
import sys
from collections import defaultdict, Counter
from datetime import datetime


# =============================================================================
# Lineage Tree Visualization
# =============================================================================

def build_lineage_tree(qr_code_id):
    """
    Build lineage tree from qr_scans

    Args:
        qr_code_id: Root QR code ID

    Returns:
        dict tree structure
    """
    db = get_db()

    # Get all scans for this QR code
    scans = db.execute('''
        SELECT id, qr_code_id, scanned_at, device_type, location_city, location_country,
               previous_scan_id, ip_address
        FROM qr_scans
        WHERE qr_code_id = ?
        ORDER BY scanned_at ASC
    ''', (qr_code_id,)).fetchall()

    db.close()

    if not scans:
        return None

    # Convert to dicts
    scans_dict = {scan['id']: dict(scan) for scan in scans}

    # Build tree structure
    tree = {
        'qr_code_id': qr_code_id,
        'total_scans': len(scans),
        'root_scans': [],
        'children': defaultdict(list)
    }

    for scan in scans:
        scan_data = dict(scan)
        parent_id = scan['previous_scan_id']

        if parent_id is None:
            # Root scan (no parent)
            tree['root_scans'].append(scan_data)
        else:
            # Child scan
            tree['children'][parent_id].append(scan_data)

    return tree


def print_tree(scan, tree_children, depth=0, prefix=""):
    """
    Print lineage tree as ASCII art

    Args:
        scan: Current scan dict
        tree_children: Dict of parent_id -> [child_scans]
        depth: Current depth
        prefix: Prefix for tree drawing
    """
    # Format scan info
    scan_id = scan['id']
    device = scan.get('device_type', 'Unknown')
    location = scan.get('location_city') or scan.get('location_country') or 'Unknown'
    scanned_at = scan['scanned_at'][:19] if scan.get('scanned_at') else 'N/A'

    # Print current node
    print(f"{prefix}├─ Scan #{scan_id}")
    print(f"{prefix}│  ├─ Device: {device}")
    print(f"{prefix}│  ├─ Location: {location}")
    print(f"{prefix}│  └─ Time: {scanned_at}")

    # Print children
    children = tree_children.get(scan_id, [])

    for i, child in enumerate(children):
        is_last = (i == len(children) - 1)
        child_prefix = prefix + ("   " if is_last else "│  ")
        print_tree(child, tree_children, depth + 1, child_prefix)


def display_lineage_tree(qr_code_id):
    """
    Display lineage tree for QR code

    Args:
        qr_code_id: QR code ID

    Returns:
        None (prints to console)
    """
    tree = build_lineage_tree(qr_code_id)

    if not tree:
        print(f"❌ No scans found for QR code #{qr_code_id}")
        return

    print("\n" + "=" * 70)
    print(f"🌳 LINEAGE TREE - QR Code #{qr_code_id}")
    print("=" * 70)
    print(f"\nTotal scans: {tree['total_scans']}")
    print(f"Root scans: {len(tree['root_scans'])}")
    print()

    # Print each root and its children
    for i, root_scan in enumerate(tree['root_scans']):
        print(f"\nRoot #{i + 1}:")
        print_tree(root_scan, tree['children'], depth=0, prefix="")

    print("\n" + "=" * 70)


# =============================================================================
# Analytics & Statistics
# =============================================================================

def get_qr_statistics(qr_code_id):
    """
    Get statistics for QR code

    Args:
        qr_code_id: QR code ID

    Returns:
        dict with statistics
    """
    db = get_db()

    # Get scans
    scans = db.execute('''
        SELECT device_type, location_city, location_country, referrer, scanned_at
        FROM qr_scans
        WHERE qr_code_id = ?
    ''', (qr_code_id,)).fetchall()

    # Get QR code info
    qr_code = db.execute('''
        SELECT code_type, total_scans, last_scanned_at, created_at
        FROM qr_codes
        WHERE id = ?
    ''', (qr_code_id,)).fetchone()

    db.close()

    if not scans:
        return None

    # Calculate statistics
    devices = Counter(scan['device_type'] for scan in scans if scan['device_type'])
    cities = Counter(scan['location_city'] for scan in scans if scan['location_city'])
    countries = Counter(scan['location_country'] for scan in scans if scan['location_country'])
    referrers = Counter(scan['referrer'] for scan in scans if scan['referrer'])

    # Time series (scans per day)
    scans_by_date = defaultdict(int)
    for scan in scans:
        date = scan['scanned_at'][:10] if scan.get('scanned_at') else 'Unknown'
        scans_by_date[date] += 1

    return {
        'qr_code_id': qr_code_id,
        'qr_type': qr_code['code_type'] if qr_code else 'Unknown',
        'total_scans': len(scans),
        'device_breakdown': dict(devices),
        'top_cities': dict(cities.most_common(5)),
        'top_countries': dict(countries.most_common(5)),
        'top_referrers': dict(referrers.most_common(5)),
        'scans_by_date': dict(scans_by_date),
        'first_scan': min(scan['scanned_at'] for scan in scans if scan.get('scanned_at')),
        'last_scan': max(scan['scanned_at'] for scan in scans if scan.get('scanned_at'))
    }


def display_statistics(qr_code_id):
    """
    Display statistics for QR code

    Args:
        qr_code_id: QR code ID
    """
    stats = get_qr_statistics(qr_code_id)

    if not stats:
        print(f"❌ No statistics found for QR code #{qr_code_id}")
        return

    print("\n" + "=" * 70)
    print(f"📊 STATISTICS - QR Code #{qr_code_id}")
    print("=" * 70)
    print(f"\nQR Type: {stats['qr_type']}")
    print(f"Total Scans: {stats['total_scans']}")
    print(f"First Scan: {stats['first_scan']}")
    print(f"Last Scan: {stats['last_scan']}")

    print("\n📱 Device Breakdown:")
    for device, count in stats['device_breakdown'].items():
        percentage = (count / stats['total_scans']) * 100
        print(f"   {device:15} {count:5} ({percentage:.1f}%)")

    if stats['top_cities']:
        print("\n🏙️  Top Cities:")
        for city, count in stats['top_cities'].items():
            print(f"   {city:20} {count:5}")

    if stats['top_countries']:
        print("\n🌍 Top Countries:")
        for country, count in stats['top_countries'].items():
            print(f"   {country:20} {count:5}")

    if stats['top_referrers']:
        print("\n🔗 Top Referrers:")
        for referrer, count in stats['top_referrers'].items():
            referrer_short = referrer[:40] + "..." if len(referrer) > 40 else referrer
            print(f"   {referrer_short:45} {count:5}")

    print("\n📅 Scans by Date:")
    for date, count in sorted(stats['scans_by_date'].items()):
        print(f"   {date}  {count:5}")

    print("\n" + "=" * 70)


# =============================================================================
# HTML Dashboard
# =============================================================================

def generate_html_dashboard():
    """
    Generate HTML analytics dashboard

    Returns:
        HTML string
    """
    db = get_db()

    # Get all QR codes
    qr_codes = db.execute('''
        SELECT id, code_type, total_scans, last_scanned_at
        FROM qr_codes
        WHERE total_scans > 0
        ORDER BY total_scans DESC
    ''').fetchall()

    db.close()

    # Build QR code list
    qr_items = []
    for qr in qr_codes:
        qr_dict = dict(qr)
        stats = get_qr_statistics(qr_dict['id'])

        if stats:
            device_breakdown = ', '.join(f"{k}: {v}" for k, v in stats['device_breakdown'].items())

            qr_items.append(f'''
            <tr>
                <td>{qr_dict['id']}</td>
                <td>{qr_dict['code_type']}</td>
                <td>{qr_dict['total_scans']}</td>
                <td>{device_breakdown}</td>
                <td>{stats['last_scan'][:19]}</td>
                <td>
                    <button onclick="showTree({qr_dict['id']})">View Tree</button>
                    <button onclick="showStats({qr_dict['id']})">View Stats</button>
                </td>
            </tr>
            ''')

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>QR Analytics Dashboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 2rem;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}

        h1 {{
            color: #2c3e50;
            margin-bottom: 2rem;
            padding-bottom: 1rem;
            border-bottom: 3px solid #3498db;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 2rem;
        }}

        th, td {{
            padding: 1rem;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}

        th {{
            background: #3498db;
            color: white;
            font-weight: 600;
        }}

        tr:hover {{
            background: #f8f9fa;
        }}

        button {{
            background: #3498db;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            cursor: pointer;
            margin-right: 0.5rem;
            font-size: 0.9rem;
        }}

        button:hover {{
            background: #2980b9;
        }}

        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}

        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}

        .stat-card h3 {{
            font-size: 0.9rem;
            opacity: 0.9;
            margin-bottom: 0.5rem;
        }}

        .stat-card .value {{
            font-size: 2rem;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 QR Analytics Dashboard</h1>

        <div class="stats">
            <div class="stat-card">
                <h3>Total QR Codes</h3>
                <div class="value">{len(qr_codes)}</div>
            </div>
            <div class="stat-card">
                <h3>Total Scans</h3>
                <div class="value">{sum(qr['total_scans'] for qr in qr_codes)}</div>
            </div>
            <div class="stat-card">
                <h3>Active Today</h3>
                <div class="value">{len([qr for qr in qr_codes if qr['last_scanned_at'] and qr['last_scanned_at'][:10] == datetime.now().strftime('%Y-%m-%d')])}</div>
            </div>
        </div>

        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Type</th>
                    <th>Total Scans</th>
                    <th>Devices</th>
                    <th>Last Scanned</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                {''.join(qr_items)}
            </tbody>
        </table>
    </div>

    <script>
        function showTree(qrId) {{
            console.log('Showing tree for QR code:', qrId);
            alert('Tree view would open here. Run: python3 qr_analytics.py --tree --qr-code ' + qrId);
        }}

        function showStats(qrId) {{
            console.log('Showing stats for QR code:', qrId);
            alert('Stats view would open here. Run: python3 qr_analytics.py --stats --qr-code ' + qrId);
        }}
    </script>
</body>
</html>'''

    return html


def save_dashboard():
    """
    Save HTML dashboard to file

    Returns:
        Path to saved file
    """
    html = generate_html_dashboard()

    output_dir = Path('output/analytics')
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / 'qr_dashboard.html'
    output_path.write_text(html)

    return output_path


# =============================================================================
# Export Functions
# =============================================================================

def export_to_json(qr_code_id):
    """
    Export analytics to JSON

    Args:
        qr_code_id: QR code ID

    Returns:
        JSON string
    """
    stats = get_qr_statistics(qr_code_id)
    tree = build_lineage_tree(qr_code_id)

    data = {
        'statistics': stats,
        'lineage_tree': tree
    }

    return json.dumps(data, indent=2)


# =============================================================================
# CLI
# =============================================================================

def main():
    """CLI for QR analytics"""

    if '--help' in sys.argv:
        print(__doc__)
        return

    if '--tree' in sys.argv:
        if '--qr-code' in sys.argv:
            idx = sys.argv.index('--qr-code')
            if idx + 1 < len(sys.argv):
                qr_code_id = int(sys.argv[idx + 1])
                display_lineage_tree(qr_code_id)
        else:
            print("Usage: --tree --qr-code <id>")

    elif '--stats' in sys.argv:
        if '--qr-code' in sys.argv:
            idx = sys.argv.index('--qr-code')
            if idx + 1 < len(sys.argv):
                qr_code_id = int(sys.argv[idx + 1])
                display_statistics(qr_code_id)
        else:
            print("Usage: --stats --qr-code <id>")

    elif '--dashboard' in sys.argv:
        output_path = save_dashboard()
        print(f"✅ Dashboard saved to: {output_path}")
        print(f"   Open in browser: file://{output_path.absolute()}")

    elif '--export' in sys.argv:
        if '--qr-code' in sys.argv:
            idx = sys.argv.index('--qr-code')
            if idx + 1 < len(sys.argv):
                qr_code_id = int(sys.argv[idx + 1])
                json_data = export_to_json(qr_code_id)
                print(json_data)
        else:
            print("Usage: --export --qr-code <id>")

    else:
        print("Usage:")
        print("  python3 qr_analytics.py --tree --qr-code 1")
        print("  python3 qr_analytics.py --stats --qr-code 1")
        print("  python3 qr_analytics.py --dashboard")
        print("  python3 qr_analytics.py --export --qr-code 1")


if __name__ == '__main__':
    main()
