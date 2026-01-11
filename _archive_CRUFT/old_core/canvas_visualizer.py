#!/usr/bin/env python3
"""
Canvas Visualizer - Knowledge Graph Renderer

Visualize word embeddings and LLM knowledge as an interactive graph.

Outputs:
- SVG: Static vector graphics (scalable, print-ready)
- HTML: Interactive canvas (D3.js-style)
- JSON: Data for external visualizers
- ASCII: Terminal-friendly visualization

Like:
- Obsidian graph view
- Neo4j Bloom
- Gephi
- But simpler and self-contained
"""

import json
import math
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from pathlib import Path
import numpy as np


class CanvasVisualizer:
    """
    Render knowledge graphs on canvas

    Supports multiple output formats:
    - SVG (vector graphics)
    - HTML (interactive)
    - JSON (data export)
    - ASCII (terminal)
    """

    def __init__(self, width: int = 800, height: int = 600):
        """
        Initialize visualizer

        Args:
            width: Canvas width in pixels
            height: Canvas height in pixels
        """
        self.width = width
        self.height = height

        print(f"🎨 Initialized Canvas Visualizer")
        print(f"   Canvas size: {width}x{height}")


    def layout_force_directed(
        self,
        nodes: List[Dict],
        edges: List[Dict],
        iterations: int = 50
    ) -> Dict[str, Tuple[float, float]]:
        """
        Force-directed layout (Fruchterman-Reingold algorithm)

        Nodes repel each other (like charges)
        Edges attract connected nodes (like springs)

        Args:
            nodes: List of node dicts with 'id'
            edges: List of edge dicts with 'source', 'target'
            iterations: Number of layout iterations

        Returns:
            Dict mapping node_id → (x, y) position
        """
        # Initialize random positions
        positions = {}
        for node in nodes:
            node_id = node['id']
            positions[node_id] = (
                np.random.uniform(0, self.width),
                np.random.uniform(0, self.height)
            )

        # Build adjacency list
        adjacency = {node['id']: [] for node in nodes}
        for edge in edges:
            # Skip edges with missing nodes
            if edge['source'] not in adjacency or edge['target'] not in adjacency:
                continue
            adjacency[edge['source']].append(edge['target'])
            adjacency[edge['target']].append(edge['source'])

        # Force-directed parameters
        area = self.width * self.height
        k = math.sqrt(area / len(nodes))  # Optimal distance
        temperature = self.width / 10  # Initial temperature
        cooling_rate = 0.95

        print(f"🧲 Computing force-directed layout...")
        print(f"   Nodes: {len(nodes)}, Edges: {len(edges)}")
        print(f"   Iterations: {iterations}")

        for iteration in range(iterations):
            # Calculate repulsive forces (all pairs)
            forces = {node_id: (0.0, 0.0) for node_id in positions.keys()}

            # Repulsion between all nodes
            node_ids = list(positions.keys())
            for i, node1 in enumerate(node_ids):
                for node2 in node_ids[i+1:]:
                    pos1 = positions[node1]
                    pos2 = positions[node2]

                    # Distance vector
                    dx = pos1[0] - pos2[0]
                    dy = pos1[1] - pos2[1]
                    distance = math.sqrt(dx*dx + dy*dy) + 0.01  # Avoid division by zero

                    # Repulsive force (inversely proportional to distance)
                    force = k * k / distance

                    # Normalized direction
                    fx = (dx / distance) * force
                    fy = (dy / distance) * force

                    # Apply to both nodes (equal and opposite)
                    forces[node1] = (forces[node1][0] + fx, forces[node1][1] + fy)
                    forces[node2] = (forces[node2][0] - fx, forces[node2][1] - fy)

            # Attractive forces (connected nodes only)
            for edge in edges:
                source = edge['source']
                target = edge['target']

                if source not in positions or target not in positions:
                    continue

                pos1 = positions[source]
                pos2 = positions[target]

                # Distance vector
                dx = pos2[0] - pos1[0]
                dy = pos2[1] - pos1[1]
                distance = math.sqrt(dx*dx + dy*dy) + 0.01

                # Attractive force (proportional to distance)
                force = distance * distance / k

                # Normalized direction
                fx = (dx / distance) * force
                fy = (dy / distance) * force

                # Apply to both nodes
                forces[source] = (forces[source][0] + fx, forces[source][1] + fy)
                forces[target] = (forces[target][0] - fx, forces[target][1] - fy)

            # Update positions (with temperature)
            for node_id in positions.keys():
                force_x, force_y = forces[node_id]
                force_mag = math.sqrt(force_x*force_x + force_y*force_y) + 0.01

                # Limit displacement by temperature
                displacement = min(force_mag, temperature)

                # Update position
                new_x = positions[node_id][0] + (force_x / force_mag) * displacement
                new_y = positions[node_id][1] + (force_y / force_mag) * displacement

                # Keep within bounds
                new_x = max(30, min(self.width - 30, new_x))
                new_y = max(30, min(self.height - 30, new_y))

                positions[node_id] = (new_x, new_y)

            # Cool down
            temperature *= cooling_rate

        print(f"✅ Layout complete!")

        return positions


    def render_svg(
        self,
        nodes: List[Dict],
        edges: List[Dict],
        positions: Dict[str, Tuple[float, float]],
        output_path: str
    ):
        """
        Render graph as SVG

        Args:
            nodes: List of node dicts
            edges: List of edge dicts
            positions: Node positions from layout
            output_path: Where to save SVG
        """
        svg_lines = [
            f'<svg width="{self.width}" height="{self.height}" xmlns="http://www.w3.org/2000/svg">',
            '<style>',
            '.node { stroke: #333; stroke-width: 2; cursor: pointer; }',
            '.node-base { fill: #4CAF50; }',
            '.node-expanded { fill: #2196F3; }',
            '.edge { stroke: #999; stroke-width: 1; opacity: 0.6; }',
            '.label { font-family: Arial; font-size: 12px; fill: #333; text-anchor: middle; }',
            '</style>',
            '<g id="edges">'
        ]

        # Draw edges
        for edge in edges:
            source = edge['source']
            target = edge['target']

            if source not in positions or target not in positions:
                continue

            x1, y1 = positions[source]
            x2, y2 = positions[target]

            svg_lines.append(
                f'<line class="edge" x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" />'
            )

        svg_lines.append('</g>')
        svg_lines.append('<g id="nodes">')

        # Draw nodes
        for node in nodes:
            node_id = node['id']

            if node_id not in positions:
                continue

            x, y = positions[node_id]
            node_type = node.get('type', 'base')
            label = node.get('label', node_id)

            # Node circle
            node_class = f"node node-{node_type}"
            radius = 8 if node_type == 'base' else 6

            svg_lines.append(
                f'<circle class="{node_class}" cx="{x:.1f}" cy="{y:.1f}" r="{radius}" />'
            )

            # Label
            svg_lines.append(
                f'<text class="label" x="{x:.1f}" y="{y + 20:.1f}">{label}</text>'
            )

        svg_lines.append('</g>')
        svg_lines.append('</svg>')

        # Write to file
        Path(output_path).parent.mkdir(exist_ok=True)
        with open(output_path, 'w') as f:
            f.write('\n'.join(svg_lines))

        print(f"💾 Saved SVG to {output_path}")


    def render_html_interactive(
        self,
        nodes: List[Dict],
        edges: List[Dict],
        positions: Dict[str, Tuple[float, float]],
        output_path: str
    ):
        """
        Render interactive HTML with canvas

        Args:
            nodes: List of node dicts
            edges: List of edge dicts
            positions: Node positions from layout
            output_path: Where to save HTML
        """
        # Prepare data for JavaScript
        nodes_js = []
        for node in nodes:
            node_id = node['id']
            if node_id not in positions:
                continue

            x, y = positions[node_id]
            nodes_js.append({
                'id': node_id,
                'label': node.get('label', node_id),
                'type': node.get('type', 'base'),
                'x': x,
                'y': y,
                'definition': node.get('definition', ''),
                'usage_count': node.get('usage_count', 0)
            })

        edges_js = []
        for edge in edges:
            if edge['source'] in positions and edge['target'] in positions:
                edges_js.append({
                    'source': edge['source'],
                    'target': edge['target'],
                    'type': edge.get('type', 'related')
                })

        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Words to Canvas - Knowledge Graph</title>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            font-family: Arial, sans-serif;
            background: #f5f5f5;
        }}
        h1 {{
            color: #333;
            margin: 0 0 20px 0;
        }}
        #canvas {{
            background: white;
            border: 1px solid #ddd;
            cursor: grab;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        #canvas:active {{
            cursor: grabbing;
        }}
        #info {{
            margin-top: 20px;
            padding: 15px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 4px;
        }}
        .stats {{
            display: flex;
            gap: 20px;
            margin-bottom: 10px;
        }}
        .stat {{
            padding: 10px;
            background: #f0f0f0;
            border-radius: 4px;
        }}
        .stat strong {{
            color: #2196F3;
        }}
    </style>
</head>
<body>
    <h1>🎨 Words to Canvas - Knowledge Graph</h1>

    <canvas id="canvas" width="{self.width}" height="{self.height}"></canvas>

    <div id="info">
        <div class="stats">
            <div class="stat"><strong>{len(nodes)}</strong> nodes</div>
            <div class="stat"><strong>{len(edges)}</strong> edges</div>
            <div class="stat"><strong id="selected-node">Click a node to see details</strong></div>
        </div>
        <div id="details"></div>
    </div>

    <script>
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');
        const selectedNode = document.getElementById('selected-node');
        const details = document.getElementById('details');

        // Data
        const nodes = {json.dumps(nodes_js)};
        const edges = {json.dumps(edges_js)};

        // Colors
        const colors = {{
            base: '#4CAF50',
            expanded: '#2196F3',
            edge: '#999'
        }};

        // Draw graph
        function draw() {{
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // Draw edges
            ctx.strokeStyle = colors.edge;
            ctx.lineWidth = 1;
            ctx.globalAlpha = 0.6;

            edges.forEach(edge => {{
                const source = nodes.find(n => n.id === edge.source);
                const target = nodes.find(n => n.id === edge.target);

                if (source && target) {{
                    ctx.beginPath();
                    ctx.moveTo(source.x, source.y);
                    ctx.lineTo(target.x, target.y);
                    ctx.stroke();
                }}
            }});

            ctx.globalAlpha = 1.0;

            // Draw nodes
            nodes.forEach(node => {{
                const radius = node.type === 'base' ? 8 : 6;
                const color = colors[node.type] || colors.base;

                // Circle
                ctx.fillStyle = color;
                ctx.strokeStyle = '#333';
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI);
                ctx.fill();
                ctx.stroke();

                // Label
                ctx.fillStyle = '#333';
                ctx.font = '12px Arial';
                ctx.textAlign = 'center';
                ctx.fillText(node.label, node.x, node.y + 20);
            }});
        }}

        // Handle clicks
        canvas.addEventListener('click', (e) => {{
            const rect = canvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            // Find clicked node
            const clickedNode = nodes.find(node => {{
                const dx = x - node.x;
                const dy = y - node.y;
                const distance = Math.sqrt(dx*dx + dy*dy);
                return distance < 15;
            }});

            if (clickedNode) {{
                selectedNode.textContent = clickedNode.label;
                details.innerHTML = `
                    <h3>${{clickedNode.label}}</h3>
                    <p><strong>Type:</strong> ${{clickedNode.type}}</p>
                    ${{clickedNode.definition ? `<p><strong>Definition:</strong> ${{clickedNode.definition}}</p>` : ''}}
                    ${{clickedNode.usage_count > 0 ? `<p><strong>Usage count:</strong> ${{clickedNode.usage_count}}</p>` : ''}}
                `;
            }}
        }});

        // Initial draw
        draw();

        console.log('📊 Knowledge graph loaded');
        console.log('Nodes:', nodes.length);
        console.log('Edges:', edges.length);
    </script>
</body>
</html>'''

        # Write to file
        Path(output_path).parent.mkdir(exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(html)

        print(f"💾 Saved interactive HTML to {output_path}")


    def render_ascii(
        self,
        nodes: List[Dict],
        edges: List[Dict],
        positions: Dict[str, Tuple[float, float]]
    ) -> str:
        """
        Render ASCII art version for terminal

        Args:
            nodes: List of node dicts
            edges: List of edge dicts
            positions: Node positions

        Returns:
            ASCII art string
        """
        # Create 2D grid
        grid_width = 80
        grid_height = 30

        grid = [[' ' for _ in range(grid_width)] for _ in range(grid_height)]

        # Scale positions to grid
        def scale_pos(x, y):
            grid_x = int((x / self.width) * (grid_width - 1))
            grid_y = int((y / self.height) * (grid_height - 1))
            return grid_x, grid_y

        # Draw edges (lines)
        for edge in edges:
            source = edge['source']
            target = edge['target']

            if source not in positions or target not in positions:
                continue

            x1, y1 = scale_pos(*positions[source])
            x2, y2 = scale_pos(*positions[target])

            # Simple line drawing (Bresenham's algorithm simplified)
            dx = abs(x2 - x1)
            dy = abs(y2 - y1)

            if dx == 0 and dy == 0:
                continue

            steps = max(dx, dy)
            for i in range(steps):
                t = i / steps
                x = int(x1 + t * (x2 - x1))
                y = int(y1 + t * (y2 - y1))

                if 0 <= x < grid_width and 0 <= y < grid_height:
                    if grid[y][x] == ' ':
                        grid[y][x] = '-' if dx > dy else '|'

        # Draw nodes
        for node in nodes:
            node_id = node['id']

            if node_id not in positions:
                continue

            x, y = scale_pos(*positions[node_id])

            if 0 <= x < grid_width and 0 <= y < grid_height:
                node_type = node.get('type', 'base')
                symbol = 'O' if node_type == 'base' else 'o'
                grid[y][x] = symbol

        # Convert grid to string
        ascii_art = '\n'.join(''.join(row) for row in grid)

        # Add legend
        legend = f"""
{'='*80}
Knowledge Graph (ASCII)
Nodes: {len(nodes)} | Edges: {len(edges)}
O = Base vocabulary | o = Expanded vocabulary | -/| = Relationships
{'='*80}
"""

        return legend + '\n' + ascii_art


    def export_json(
        self,
        nodes: List[Dict],
        edges: List[Dict],
        positions: Dict[str, Tuple[float, float]],
        output_path: str
    ):
        """
        Export graph data as JSON

        Args:
            nodes: List of node dicts
            edges: List of edge dicts
            positions: Node positions
            output_path: Where to save JSON
        """
        # Add positions to nodes
        nodes_with_pos = []
        for node in nodes:
            node_id = node['id']
            if node_id in positions:
                node_copy = node.copy()
                node_copy['x'], node_copy['y'] = positions[node_id]
                nodes_with_pos.append(node_copy)

        data = {
            'nodes': nodes_with_pos,
            'edges': edges,
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'canvas_width': self.width,
                'canvas_height': self.height,
                'node_count': len(nodes_with_pos),
                'edge_count': len(edges)
            }
        }

        Path(output_path).parent.mkdir(exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"💾 Saved JSON to {output_path}")


    def render_html_sigma(
        self,
        nodes: List[Dict],
        edges: List[Dict],
        positions: Dict[str, Tuple[float, float]],
        output_path: str,
        title: str = "Knowledge Graph"
    ):
        """
        Render interactive HTML using Sigma.js (for large graphs 500+ nodes)

        Args:
            nodes: List of node dicts
            edges: List of edge dicts
            positions: Node positions from layout
            output_path: Where to save HTML
            title: Graph title
        """
        from jinja2 import Template

        # Prepare nodes with positions
        nodes_with_pos = []
        for node in nodes:
            node_id = node['id']
            if node_id not in positions:
                continue

            x, y = positions[node_id]
            nodes_with_pos.append({
                'id': node_id,
                'label': node.get('label', node_id),
                'type': node.get('type', 'default'),
                'x': x,
                'y': y,
                'definition': node.get('definition', ''),
                'usage_count': node.get('usage_count', 0)
            })

        # Prepare edges
        edges_prepared = []
        for edge in edges:
            edges_prepared.append({
                'source': edge['source'],
                'target': edge['target'],
                'type': edge.get('type', 'default')
            })

        # Load Sigma.js template
        template_path = Path(__file__).parent.parent / 'templates' / 'graph_sigma.html'

        if not template_path.exists():
            print(f"❌ Sigma.js template not found: {template_path}")
            print("   Using fallback canvas renderer...")
            return self.render_html_interactive(nodes, edges, positions, output_path)

        with open(template_path) as f:
            template = Template(f.read())

        # Render template
        html = template.render(
            title=title,
            node_count=len(nodes_with_pos),
            edge_count=len(edges_prepared),
            nodes_json=json.dumps(nodes_with_pos),
            edges_json=json.dumps(edges_prepared)
        )

        # Write to file
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(html)

        print(f"💾 Saved interactive Sigma.js graph to {output_path}")


# =============================================================================
# CLI for Testing
# =============================================================================

if __name__ == '__main__':
    # Test with sample graph
    print("🧪 Testing Canvas Visualizer...")

    # Sample nodes and edges
    nodes = [
        {'id': 'tampa', 'label': 'Tampa', 'type': 'base'},
        {'id': 'plumber', 'label': 'Plumber', 'type': 'base'},
        {'id': 'repair', 'label': 'Repair', 'type': 'base'},
        {'id': 'service', 'label': 'Service', 'type': 'base'},
        {'id': 'database', 'label': 'Database', 'type': 'expanded', 'definition': 'Organized collection of data'},
        {'id': 'blockchain', 'label': 'Blockchain', 'type': 'expanded', 'definition': 'Distributed ledger technology'},
    ]

    edges = [
        {'source': 'tampa', 'target': 'plumber'},
        {'source': 'plumber', 'target': 'repair'},
        {'source': 'plumber', 'target': 'service'},
        {'source': 'repair', 'target': 'service'},
        {'source': 'service', 'target': 'database'},
        {'source': 'database', 'target': 'blockchain'},
    ]

    # Create visualizer
    viz = CanvasVisualizer(width=800, height=600)

    # Compute layout
    positions = viz.layout_force_directed(nodes, edges, iterations=50)

    # Render outputs
    Path('data/visualizations').mkdir(parents=True, exist_ok=True)

    viz.render_svg(nodes, edges, positions, 'data/visualizations/graph.svg')
    viz.render_html_interactive(nodes, edges, positions, 'data/visualizations/graph.html')
    viz.export_json(nodes, edges, positions, 'data/visualizations/graph.json')

    # Show ASCII version
    ascii_art = viz.render_ascii(nodes, edges, positions)
    print(ascii_art)

    print(f"\n✅ All visualizations generated!")
    print(f"   Open data/visualizations/graph.html in browser to see interactive version")
