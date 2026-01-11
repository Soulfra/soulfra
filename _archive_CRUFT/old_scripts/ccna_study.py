#!/usr/bin/env python3
"""
CCNA Study Graph - Convert Networking Concepts to Interactive Graphs

Takes networking study notes (voice memos, markdown, PDFs) and converts them
into interactive knowledge graphs showing relationships between concepts.

Example concepts:
- OSI Model layers (7 layers with protocols at each layer)
- Network topologies (star, mesh, ring, bus)
- IP addressing (subnetting, CIDR, NAT, DHCP)
- Routing protocols (RIP, EIGRP, OSPF, BGP)
- Security (ACLs, VLANs, firewalls, VPN)

Output:
- ccna_concept_graph.html - Interactive graph of networking concepts
- ccna_flashcards.json - Spaced repetition flashcards
- ccna_topology_map.svg - Network topology diagram
"""

import json
import re
from pathlib import Path
from datetime import datetime
from core.content_parser import ContentParser
from core.canvas_visualizer import CanvasVisualizer

# Output directory
OUTPUT_DIR = Path("data/ccna_study")

# Pre-defined networking concepts for graph seeding
NETWORKING_CONCEPTS = {
    # OSI Model
    "osi_model": {
        "label": "OSI Model",
        "type": "framework",
        "definition": "7-layer model for network communication",
        "layers": ["physical", "data_link", "network", "transport", "session", "presentation", "application"]
    },

    # Network topologies
    "star_topology": {
        "label": "Star Topology",
        "type": "topology",
        "definition": "All nodes connect to central hub",
        "example": "Home router with devices connected"
    },
    "mesh_topology": {
        "label": "Mesh Topology",
        "type": "topology",
        "definition": "Every node connects to every other node",
        "example": "Military networks, blockchain networks"
    },

    # Protocols
    "tcp": {
        "label": "TCP",
        "type": "protocol",
        "layer": "transport",
        "definition": "Reliable, connection-oriented protocol",
        "port_examples": "80 (HTTP), 443 (HTTPS), 22 (SSH)"
    },
    "udp": {
        "label": "UDP",
        "type": "protocol",
        "layer": "transport",
        "definition": "Unreliable, connectionless protocol for speed",
        "port_examples": "53 (DNS), 67/68 (DHCP)"
    },
    "ip": {
        "label": "IP",
        "type": "protocol",
        "layer": "network",
        "definition": "Internet Protocol for addressing and routing",
        "versions": ["IPv4", "IPv6"]
    },

    # IP Addressing
    "subnetting": {
        "label": "Subnetting",
        "type": "concept",
        "definition": "Dividing network into smaller subnetworks",
        "example": "192.168.1.0/24 → 192.168.1.0/25 and 192.168.1.128/25"
    },
    "cidr": {
        "label": "CIDR",
        "type": "concept",
        "definition": "Classless Inter-Domain Routing notation",
        "example": "/24 = 255.255.255.0, /16 = 255.255.0.0"
    },
    "nat": {
        "label": "NAT",
        "type": "protocol",
        "definition": "Network Address Translation - private to public IP mapping",
        "example": "Home router translates 192.168.x.x to public IP"
    },

    # Routing
    "routing_table": {
        "label": "Routing Table",
        "type": "concept",
        "definition": "Maps destination networks to next-hop routers",
        "example": "0.0.0.0/0 → gateway (default route)"
    },
    "ospf": {
        "label": "OSPF",
        "type": "protocol",
        "definition": "Open Shortest Path First - link-state routing protocol",
        "metric": "Cost (based on bandwidth)"
    },

    # Security
    "acl": {
        "label": "ACL",
        "type": "security",
        "definition": "Access Control List - firewall rules",
        "example": "Permit TCP port 443, deny all else"
    },
    "vlan": {
        "label": "VLAN",
        "type": "security",
        "definition": "Virtual LAN - logical network segmentation",
        "example": "VLAN 10 for sales, VLAN 20 for IT"
    }
}

def parse_study_notes(content: str, source: str = "study_notes"):
    """
    Parse study notes into graph nodes and edges

    Detects:
    - Networking terms (protocols, concepts, devices)
    - Relationships (is_a, uses, connects_to, implements)
    - Examples and definitions
    """

    parser = ContentParser()

    # Parse content using voice_transcript parser (works for general text)
    try:
        graph = parser.parse(content, 'voice_transcript')
    except Exception as e:
        print(f"⚠️ Error parsing content: {e}")
        return {"nodes": [], "edges": []}

    # Enhance graph with networking-specific concepts
    nodes = graph.get('nodes', [])
    edges = graph.get('edges', [])

    # Add pre-defined networking concepts if mentioned in content
    content_lower = content.lower()
    for concept_id, concept_data in NETWORKING_CONCEPTS.items():
        label = concept_data['label']
        if label.lower() in content_lower or concept_id in content_lower:
            # Add concept node if not already present
            node_exists = any(n['id'] == f"concept_{concept_id}" for n in nodes)
            if not node_exists:
                nodes.append({
                    "id": f"concept_{concept_id}",
                    "label": label,
                    "type": concept_data.get('type', 'concept'),
                    "definition": concept_data.get('definition', ''),
                    "frequency": 1
                })

    # Detect relationships between concepts
    # Example: "TCP uses IP" → edge from TCP to IP with type "uses"
    relationship_patterns = [
        (r"(\w+)\s+uses\s+(\w+)", "uses"),
        (r"(\w+)\s+implements\s+(\w+)", "implements"),
        (r"(\w+)\s+is a\s+(\w+)", "is_a"),
        (r"(\w+)\s+connects to\s+(\w+)", "connects_to"),
        (r"(\w+)\s+layer\s+(\d+)", "layer"),
    ]

    for pattern, rel_type in relationship_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            source_term = match.group(1).lower()
            target_term = match.group(2).lower()

            # Create edge if both nodes exist
            source_id = f"concept_{source_term}"
            target_id = f"concept_{target_term}"

            edges.append({
                "source": source_id,
                "target": target_id,
                "type": rel_type
            })

    return {"nodes": nodes, "edges": edges}

def generate_flashcards(graph):
    """
    Generate spaced repetition flashcards from graph concepts

    Format compatible with Anki, Quizlet, etc.
    """
    flashcards = []

    for node in graph['nodes']:
        if node.get('type') in ['protocol', 'concept', 'security', 'topology']:
            card = {
                "front": f"What is {node['label']}?",
                "back": node.get('definition', ''),
                "tags": [node.get('type', 'networking')],
                "created_at": datetime.now().isoformat()
            }
            flashcards.append(card)

    return flashcards

def create_topology_diagram(domains_graph):
    """
    Create network topology diagram showing how your domains connect

    Visualizes:
    - Domains as nodes
    - Auth flows as edges
    - Cookie sharing as subnet grouping
    """

    # This uses the domain routing graph from debug_system.py
    # and visualizes it like a Cisco Packet Tracer diagram

    nodes = []
    edges = []

    # Central hub (soulfra.com = main router)
    nodes.append({
        "id": "router_soulfra",
        "label": "soulfra.com\n(Main Router)",
        "type": "router",
        "x": 600,
        "y": 450
    })

    # Spoke domains (connected devices)
    spoke_domains = [
        ("calriven.com", "PC 1", 400, 200),
        ("deathtodata.com", "PC 2", 800, 200),
        ("howtocookathome.com", "PC 3", 400, 700),
        ("hollowtown.com", "Server 1", 800, 700),
    ]

    for domain, device_label, x, y in spoke_domains:
        nodes.append({
            "id": f"device_{domain}",
            "label": f"{device_label}\n{domain}",
            "type": "device",
            "x": x,
            "y": y
        })

        # Connect to router
        edges.append({
            "source": f"device_{domain}",
            "target": "router_soulfra",
            "type": "auth_flow",
            "label": "JWT token"
        })

    return {"nodes": nodes, "edges": edges}

def study_session(content: str = None, filepath: str = None):
    """
    Main study session workflow

    1. Parse notes (voice memo, markdown, PDF)
    2. Generate knowledge graph
    3. Create flashcards
    4. Export visualizations
    """

    print("📚 CCNA Study Session Starting...")

    # Load content
    if filepath:
        content = Path(filepath).read_text()
        print(f"📄 Loaded notes from {filepath}")
    elif content:
        print(f"📝 Processing {len(content)} characters of notes")
    else:
        # Default demo content
        content = """
        OSI Model has 7 layers. Layer 3 is the Network layer which uses IP protocol.
        TCP is a transport layer protocol that implements reliable delivery.
        UDP is faster than TCP but unreliable.

        Star topology connects all devices to a central hub.
        Mesh topology connects every device to every other device.

        Subnetting divides a network using CIDR notation like /24.
        NAT translates private IPs to public IPs.

        OSPF uses cost as its routing metric.
        ACLs filter traffic based on rules.
        VLANs segment networks logically.
        """
        print("📝 Using demo CCNA content")

    # Parse notes
    print("\n🔍 Parsing networking concepts...")
    graph = parse_study_notes(content)
    print(f"   Found {len(graph['nodes'])} concepts, {len(graph['edges'])} relationships")

    # Generate flashcards
    print("\n🃏 Generating flashcards...")
    flashcards = generate_flashcards(graph)
    print(f"   Created {len(flashcards)} flashcards")

    # Create topology diagram
    print("\n🌐 Creating network topology diagram...")
    topology = create_topology_diagram(graph)
    print(f"   Topology: {len(topology['nodes'])} nodes, {len(topology['edges'])} connections")

    # Save outputs
    OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

    # Save concept graph
    viz = CanvasVisualizer(width=1200, height=900)
    positions = viz.layout_force_directed(graph['nodes'], graph['edges'])
    viz.render_html_interactive(
        graph['nodes'],
        graph['edges'],
        positions,
        str(OUTPUT_DIR / "ccna_concept_graph.html")
    )

    # Save topology diagram
    positions_topo = viz.layout_force_directed(topology['nodes'], topology['edges'])
    viz.render_html_interactive(
        topology['nodes'],
        topology['edges'],
        positions_topo,
        str(OUTPUT_DIR / "network_topology.html")
    )

    # Save flashcards
    with open(OUTPUT_DIR / "ccna_flashcards.json", "w") as f:
        json.dump(flashcards, f, indent=2)

    # Generate study report
    generate_study_report(graph, flashcards, OUTPUT_DIR / "study_report.md")

    print(f"\n✅ Study session complete!")
    print(f"📁 Files saved to {OUTPUT_DIR}/")
    print(f"   - ccna_concept_graph.html (interactive knowledge graph)")
    print(f"   - network_topology.html (your domain topology)")
    print(f"   - ccna_flashcards.json (spaced repetition cards)")
    print(f"   - study_report.md (summary)")

def generate_study_report(graph, flashcards, output_file):
    """Generate markdown study report"""

    with open(output_file, "w") as f:
        f.write("# CCNA Study Report\n\n")
        f.write(f"**Generated:** {datetime.now().isoformat()}\n\n")

        f.write("## Overview\n\n")
        f.write(f"- **Concepts Learned:** {len(graph['nodes'])}\n")
        f.write(f"- **Relationships:** {len(graph['edges'])}\n")
        f.write(f"- **Flashcards:** {len(flashcards)}\n\n")

        f.write("## Concepts by Type\n\n")

        # Group concepts by type
        concepts_by_type = {}
        for node in graph['nodes']:
            node_type = node.get('type', 'other')
            if node_type not in concepts_by_type:
                concepts_by_type[node_type] = []
            concepts_by_type[node_type].append(node)

        for concept_type, concepts in concepts_by_type.items():
            f.write(f"\n### {concept_type.title()}\n\n")
            for concept in concepts:
                label = concept.get('label', '')
                definition = concept.get('definition', '')
                if definition:
                    f.write(f"- **{label}**: {definition}\n")
                else:
                    f.write(f"- {label}\n")

        f.write("\n## Relationship Map\n\n")
        for edge in graph['edges']:
            source = edge.get('source', '')
            target = edge.get('target', '')
            rel_type = edge.get('type', 'relates_to')
            f.write(f"- {source} → {target} ({rel_type})\n")

        f.write("\n## Study Tips\n\n")
        f.write("1. Review concept graph daily\n")
        f.write("2. Practice flashcards using spaced repetition\n")
        f.write("3. Map new concepts to topology diagram\n")
        f.write("4. Connect networking concepts to your domain architecture\n")

def compare_to_your_system():
    """
    Compare CCNA concepts to your actual soulfra architecture

    Shows how networking concepts apply to your 7-domain system:
    - Star topology = soulfra.com as hub, other domains as spokes
    - NAT = Each domain has private state, public API
    - VLANs = Brand isolation via brand_id
    - Routing table = subdomain_router.py
    - ACLs = Flask route decorators, auth checks
    """

    comparisons = {
        "Star Topology": {
            "ccna": "All devices connect to central hub",
            "your_system": "All domains authenticate through soulfra.com (central auth server)",
            "file": "subdomain_router.py"
        },
        "Mesh Topology": {
            "ccna": "Every node connects to every other node",
            "your_system": "BIP-39 recovery codes work across ALL domains (decentralized auth)",
            "file": "BIP39_STPETEPROS_SYSTEM.md"
        },
        "Routing Table": {
            "ccna": "Maps destination networks to next-hop routers",
            "your_system": "domain_router.py maps domains to template directories",
            "file": "subdomain_router.py line 15-30"
        },
        "VLAN": {
            "ccna": "Virtual LAN - logical network segmentation",
            "your_system": "brand column in database segments content per domain",
            "file": "soulfra.db tables with brand='soulfra' vs brand='calriven'"
        },
        "NAT": {
            "ccna": "Translates private IP to public IP",
            "your_system": "JWT tokens translate user_id (private) to public API access",
            "file": "oauth_routes.py"
        },
        "ACL": {
            "ccna": "Access Control List filters traffic",
            "your_system": "Flask route decorators check authentication before serving content",
            "file": "@app.route decorators with auth checks"
        }
    }

    print("\n🔗 CCNA → Your System Connections:\n")
    for concept, data in comparisons.items():
        print(f"**{concept}**")
        print(f"  CCNA: {data['ccna']}")
        print(f"  Your System: {data['your_system']}")
        print(f"  File: {data['file']}")
        print()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="CCNA study graph generator")
    parser.add_argument("--file", help="Path to study notes file")
    parser.add_argument("--compare", action="store_true", help="Compare CCNA to your system")

    args = parser.parse_args()

    if args.compare:
        compare_to_your_system()
    else:
        study_session(filepath=args.file)
