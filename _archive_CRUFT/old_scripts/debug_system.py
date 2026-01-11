#!/usr/bin/env python3
"""
System Debugger - Visualize Your Codebase as a Graph

Parses your 21k+ files and shows:
- Which routes connect to which databases
- Which domains use which templates
- Where systems overlap (conflicts)
- Dead code (isolated nodes)

Usage:
    python3 debug_system.py              # Debug app.py
    python3 debug_system.py --all        # Debug entire codebase
    python3 debug_system.py --routes     # Debug just routes
    python3 debug_system.py --domains    # Debug domain routing
"""

import sys
import os
from pathlib import Path
import json
import re
from collections import defaultdict
from datetime import datetime

# Add core to path
sys.path.insert(0, str(Path(__file__).parent / 'core'))

from content_parser import ContentParser
from canvas_visualizer import CanvasVisualizer


class SystemDebugger:
    """
    Debug your system by visualizing code as a graph
    """

    def __init__(self, output_dir: Path = None):
        self.parser = ContentParser()
        self.viz = CanvasVisualizer(width=1200, height=900)
        self.output_dir = output_dir or Path(__file__).parent / 'data' / 'system_debug'
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.all_nodes = []
        self.all_edges = []

    def debug_app_routes(self):
        """
        Parse app.py → Show all Flask routes and their connections

        Returns graph showing:
        - Route nodes (@app.route('/path'))
        - Database nodes (get_db(), execute())
        - Template nodes (render_template())
        - Function nodes (def route_handler())
        """
        print("\n🔍 Debugging Flask App Routes...\n")

        app_path = Path(__file__).parent / 'app.py'

        if not app_path.exists():
            print(f"❌ app.py not found at {app_path}")
            return None

        # Parse as Python code
        code = app_path.read_text()
        graph = self.parser.parse(code, 'code_python', metadata={'file': 'app.py'})

        print(f"   📊 Found {len(graph['nodes'])} nodes, {len(graph['edges'])} edges")

        # Extract route patterns
        routes = []
        route_pattern = r"@app\.route\(['\"]([^'\"]+)['\"]"
        for match in re.finditer(route_pattern, code):
            routes.append(match.group(1))

        print(f"   🛣️  Found {len(routes)} routes:")
        for route in routes[:10]:
            print(f"      - {route}")
        if len(routes) > 10:
            print(f"      ... and {len(routes) - 10} more")

        # Add route nodes
        for route in routes:
            if not any(n['id'] == route for n in graph['nodes']):
                graph['nodes'].append({
                    'id': route,
                    'label': route,
                    'type': 'route',
                    'frequency': 1,
                    'source': 'flask_routes'
                })

        return graph

    def debug_database_schema(self):
        """
        Parse database schema → Show all tables and relationships

        Returns graph showing:
        - Table nodes
        - Column nodes
        - Foreign key edges
        - Index nodes
        """
        print("\n🔍 Debugging Database Schema...\n")

        db_path = Path(__file__).parent / 'soulfra.db'

        if not db_path.exists():
            print(f"❌ soulfra.db not found at {db_path}")
            return None

        # Read schema using sqlite3
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]

        print(f"   📊 Found {len(tables)} tables")

        nodes = []
        edges = []

        # Create table nodes
        for table in tables:
            nodes.append({
                'id': f'table_{table}',
                'label': table,
                'type': 'database_table',
                'frequency': 1,
                'source': 'database_schema'
            })

            # Get columns
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()

            for col in columns:
                col_name = col[1]
                col_type = col[2]

                # Add column node
                col_id = f'{table}.{col_name}'
                nodes.append({
                    'id': col_id,
                    'label': f'{col_name} ({col_type})',
                    'type': 'database_column',
                    'frequency': 1,
                    'source': 'database_schema'
                })

                # Connect table to column
                edges.append({
                    'source': f'table_{table}',
                    'target': col_id,
                    'type': 'has_column',
                    'weight': 1
                })

        conn.close()

        print(f"   📊 Created {len(nodes)} nodes, {len(edges)} edges")

        return {'nodes': nodes, 'edges': edges, 'metadata': {'tables': len(tables)}}

    def debug_domain_routing(self):
        """
        Parse domain configs → Show routing logic

        Returns graph showing:
        - Domain nodes
        - Template directory nodes
        - Route pattern nodes
        - Database table nodes
        """
        print("\n🔍 Debugging Domain Routing...\n")

        domains_file = Path(__file__).parent / 'domains-simple.txt'

        if not domains_file.exists():
            print(f"❌ domains-simple.txt not found")
            return None

        # Read domains
        domains = []
        for line in domains_file.read_text().split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                domains.append(line)

        print(f"   🌐 Found {len(domains)} domains:")
        for domain in domains:
            print(f"      - {domain}")

        nodes = []
        edges = []

        # Check which domains have templates
        templates_dir = Path(__file__).parent / 'templates'

        for domain in domains:
            domain_clean = domain.replace('.com', '').replace('.', '_')

            # Domain node
            nodes.append({
                'id': f'domain_{domain}',
                'label': domain,
                'type': 'domain',
                'frequency': 1,
                'source': 'domain_config'
            })

            # Check for template directory
            template_path = templates_dir / domain_clean
            if template_path.exists():
                nodes.append({
                    'id': f'templates_{domain_clean}',
                    'label': f'templates/{domain_clean}/',
                    'type': 'template_dir',
                    'frequency': 1,
                    'source': 'filesystem'
                })

                edges.append({
                    'source': f'domain_{domain}',
                    'target': f'templates_{domain_clean}',
                    'type': 'uses_templates',
                    'weight': 1
                })

            # Check for routes file
            routes_file = Path(__file__).parent / f'{domain_clean}_routes.py'
            if routes_file.exists():
                nodes.append({
                    'id': f'routes_{domain_clean}',
                    'label': f'{domain_clean}_routes.py',
                    'type': 'routes_file',
                    'frequency': 1,
                    'source': 'filesystem'
                })

                edges.append({
                    'source': f'domain_{domain}',
                    'target': f'routes_{domain_clean}',
                    'type': 'has_routes',
                    'weight': 1
                })

        print(f"   📊 Created {len(nodes)} nodes, {len(edges)} edges")

        return {'nodes': nodes, 'edges': edges, 'metadata': {'domains': len(domains)}}

    def debug_template_usage(self):
        """
        Find which routes use which templates

        Returns graph showing:
        - Route → Template connections
        - Duplicate templates (same content, different paths)
        - Unused templates
        """
        print("\n🔍 Debugging Template Usage...\n")

        # Find all render_template calls in Python files
        python_files = list(Path(__file__).parent.glob('**/*.py'))

        template_usage = defaultdict(list)  # template → [files using it]

        for py_file in python_files:
            try:
                code = py_file.read_text()
                # Find render_template calls
                for match in re.finditer(r"render_template\(['\"]([^'\"]+)['\"]", code):
                    template = match.group(1)
                    template_usage[template].append(py_file.name)
            except:
                continue

        print(f"   📊 Found {len(template_usage)} templates in use:")

        nodes = []
        edges = []

        for template, files in sorted(template_usage.items(), key=lambda x: len(x[1]), reverse=True)[:20]:
            # Template node
            nodes.append({
                'id': f'template_{template}',
                'label': template,
                'type': 'template',
                'frequency': len(files),
                'source': 'template_usage'
            })

            print(f"      {template}: used in {len(files)} files")

            # Connect to files
            for file in files:
                # File node
                if not any(n['id'] == f'file_{file}' for n in nodes):
                    nodes.append({
                        'id': f'file_{file}',
                        'label': file,
                        'type': 'python_file',
                        'frequency': 1,
                        'source': 'filesystem'
                    })

                edges.append({
                    'source': f'file_{file}',
                    'target': f'template_{template}',
                    'type': 'renders',
                    'weight': 1
                })

        return {'nodes': nodes, 'edges': edges, 'metadata': {'templates': len(template_usage)}}

    def combine_graphs(self, *graphs):
        """
        Merge multiple graphs into one mega-graph

        Args:
            *graphs: Variable number of graph dicts

        Returns:
            Combined graph
        """
        combined_nodes = []
        combined_edges = []
        node_ids = set()

        for graph in graphs:
            if not graph:
                continue

            # Add unique nodes
            for node in graph['nodes']:
                if node['id'] not in node_ids:
                    combined_nodes.append(node)
                    node_ids.add(node['id'])

            # Add edges
            combined_edges.extend(graph['edges'])

        return {'nodes': combined_nodes, 'edges': combined_edges}

    def visualize(self, graph, name='system_debug'):
        """
        Render graph as interactive HTML + SVG + JSON

        Args:
            graph: Graph dict with nodes and edges
            name: Output filename prefix
        """
        print(f"\n🎨 Rendering visualizations...\n")

        # Compute layout
        print("   🧲 Computing force-directed layout...")
        positions = self.viz.layout_force_directed(
            nodes=graph['nodes'],
            edges=graph['edges'],
            iterations=150  # More iterations for complex graphs
        )

        # Render HTML (use Sigma.js for large graphs)
        html_path = self.output_dir / f'{name}.html'
        node_count = len(graph['nodes'])

        if node_count >= 500:
            print(f"   ⚡ Using Sigma.js renderer (large graph: {node_count} nodes)")
            self.viz.render_html_sigma(
                graph['nodes'],
                graph['edges'],
                positions,
                str(html_path),
                title=f"System Debug: {name}"
            )
        else:
            self.viz.render_html_interactive(graph['nodes'], graph['edges'], positions, str(html_path))

        print(f"   ✅ Interactive HTML: {html_path}")

        # Render SVG
        svg_path = self.output_dir / f'{name}.svg'
        self.viz.render_svg(graph['nodes'], graph['edges'], positions, str(svg_path))
        print(f"   ✅ Static SVG: {svg_path}")

        # Export JSON
        json_path = self.output_dir / f'{name}.json'
        self.viz.export_json(graph['nodes'], graph['edges'], positions, str(json_path))
        print(f"   ✅ Graph data: {json_path}")

        # Generate report
        report = self._generate_report(graph, name)
        report_path = self.output_dir / f'{name}_REPORT.md'
        report_path.write_text(report)
        print(f"   ✅ Analysis report: {report_path}")

        print(f"\n🌐 Open {html_path} in your browser to explore!\n")

    def _generate_report(self, graph, name):
        """Generate markdown analysis report"""

        # Count node types
        node_types = defaultdict(int)
        for node in graph['nodes']:
            node_types[node.get('type', 'unknown')] += 1

        # Count edge types
        edge_types = defaultdict(int)
        for edge in graph['edges']:
            edge_types[edge.get('type', 'unknown')] += 1

        # Find isolated nodes (no connections)
        connected_nodes = set()
        for edge in graph['edges']:
            connected_nodes.add(edge['source'])
            connected_nodes.add(edge['target'])

        isolated = [n for n in graph['nodes'] if n['id'] not in connected_nodes]

        # Find hub nodes (most connections)
        node_degree = defaultdict(int)
        for edge in graph['edges']:
            node_degree[edge['source']] += 1
            node_degree[edge['target']] += 1

        hubs = sorted(node_degree.items(), key=lambda x: x[1], reverse=True)[:10]

        report = f"""# System Debug Report: {name}

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overview

- **Total Nodes:** {len(graph['nodes'])}
- **Total Edges:** {len(graph['edges'])}
- **Isolated Nodes:** {len(isolated)} (potential dead code)

## Node Types

| Type | Count |
|------|-------|
"""

        for node_type, count in sorted(node_types.items(), key=lambda x: x[1], reverse=True):
            report += f"| {node_type} | {count} |\n"

        report += f"""

## Edge Types

| Type | Count |
|------|-------|
"""

        for edge_type, count in sorted(edge_types.items(), key=lambda x: x[1], reverse=True):
            report += f"| {edge_type} | {count} |\n"

        report += f"""

## Hub Nodes (Most Connected)

These are the most critical parts of your system:

| Node | Connections |
|------|-------------|
"""

        for node_id, degree in hubs:
            node = next((n for n in graph['nodes'] if n['id'] == node_id), None)
            label = node['label'] if node else node_id
            report += f"| {label} | {degree} |\n"

        if isolated:
            report += f"""

## ⚠️ Isolated Nodes (Potential Dead Code)

These nodes have no connections. Consider removing:

"""
            for node in isolated[:20]:
                report += f"- **{node['label']}** ({node['type']})\n"

            if len(isolated) > 20:
                report += f"\n... and {len(isolated) - 20} more\n"

        report += """

## Next Steps

1. **Review hub nodes** - These are critical, test thoroughly
2. **Investigate isolated nodes** - Dead code or missing connections?
3. **Look for unexpected edges** - Coupling you didn't know about
4. **Compare domain graphs** - Are your brands too similar?

"""

        return report


# =================================================================
# CLI
# =================================================================

def main():
    debugger = SystemDebugger()

    import argparse
    parser = argparse.ArgumentParser(description='Debug your system as a graph')
    parser.add_argument('--all', action='store_true', help='Debug entire system')
    parser.add_argument('--routes', action='store_true', help='Debug Flask routes only')
    parser.add_argument('--database', action='store_true', help='Debug database schema')
    parser.add_argument('--domains', action='store_true', help='Debug domain routing')
    parser.add_argument('--templates', action='store_true', help='Debug template usage')

    args = parser.parse_args()

    graphs = []

    if args.all or (not any([args.routes, args.database, args.domains, args.templates])):
        # Debug everything
        print("🚀 Debugging entire system...\n")
        print("=" * 80)

        routes_graph = debugger.debug_app_routes()
        if routes_graph:
            graphs.append(routes_graph)

        db_graph = debugger.debug_database_schema()
        if db_graph:
            graphs.append(db_graph)

        domain_graph = debugger.debug_domain_routing()
        if domain_graph:
            graphs.append(domain_graph)

        template_graph = debugger.debug_template_usage()
        if template_graph:
            graphs.append(template_graph)

        # Combine all
        combined = debugger.combine_graphs(*graphs)
        debugger.visualize(combined, 'system_complete')

    else:
        # Debug specific parts
        if args.routes:
            graph = debugger.debug_app_routes()
            if graph:
                debugger.visualize(graph, 'routes')

        if args.database:
            graph = debugger.debug_database_schema()
            if graph:
                debugger.visualize(graph, 'database_schema')

        if args.domains:
            graph = debugger.debug_domain_routing()
            if graph:
                debugger.visualize(graph, 'domain_routing')

        if args.templates:
            graph = debugger.debug_template_usage()
            if graph:
                debugger.visualize(graph, 'template_usage')

    print("\n" + "=" * 80)
    print("✅ System debugging complete!")
    print("=" * 80)


if __name__ == '__main__':
    main()
