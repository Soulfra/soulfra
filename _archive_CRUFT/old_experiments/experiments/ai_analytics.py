#!/usr/bin/env python3
"""
AI Analytics - Graphs & Insights from Logged AI Queries (Zero Dependencies)

Analyzes all AI requests/responses in the database to generate:
- Usage patterns (most common queries)
- Model performance (latency, token usage)
- Knowledge graphs (query relationships)
- Response quality metrics
- Pure HTML/SVG graphs (no matplotlib!)

Philosophy:
----------
Every AI query is logged to database. This gives us:
1. Complete audit trail
2. Performance metrics
3. Usage patterns
4. Knowledge graph potential
5. Cost tracking (if using paid APIs)

But raw data is useless without insights!

This tool transforms logged data into actionable analytics.

Zero Dependencies: Pure Python + SQLite + HTML/SVG for graphs.

Usage:
    # Generate all analytics
    python3 ai_analytics.py --all

    # Specific analytics
    python3 ai_analytics.py --usage-stats
    python3 ai_analytics.py --performance
    python3 ai_analytics.py --knowledge-graph

    # Export as HTML report
    python3 ai_analytics.py --export analytics_report.html
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from collections import Counter


# ==============================================================================
# DATA RETRIEVAL
# ==============================================================================

def get_total_requests() -> int:
    """Get total number of AI requests"""
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM ai_requests')
    count = cursor.fetchone()[0]

    conn.close()
    return count


def get_requests_by_model() -> Dict[str, int]:
    """Get request counts grouped by model"""
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT model, COUNT(*) as count
        FROM ai_requests
        GROUP BY model
        ORDER BY count DESC
    ''')

    results = {row[0]: row[1] for row in cursor.fetchall()}
    conn.close()

    return results


def get_average_latency() -> Dict[str, float]:
    """Get average latency by model"""
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT req.model, AVG(resp.latency_ms) as avg_latency
        FROM ai_requests req
        JOIN ai_responses resp ON req.request_id = resp.request_id
        GROUP BY req.model
    ''')

    results = {row[0]: round(row[1], 2) for row in cursor.fetchall()}
    conn.close()

    return results


def get_token_usage() -> Dict[str, Dict[str, int]]:
    """Get token usage statistics by model"""
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT req.model,
               SUM(resp.prompt_tokens) as total_prompt,
               SUM(resp.completion_tokens) as total_completion,
               SUM(resp.total_tokens) as total
        FROM ai_requests req
        JOIN ai_responses resp ON req.request_id = resp.request_id
        GROUP BY req.model
    ''')

    results = {}
    for row in cursor.fetchall():
        results[row[0]] = {
            'prompt_tokens': row[1],
            'completion_tokens': row[2],
            'total_tokens': row[3]
        }

    conn.close()
    return results


def get_most_common_prompts(limit: int = 10) -> List[Tuple[str, int]]:
    """Get most common prompts"""
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT prompt, COUNT(*) as count
        FROM ai_requests
        GROUP BY prompt
        ORDER BY count DESC
        LIMIT ?
    ''', (limit,))

    results = cursor.fetchall()
    conn.close()

    return results


def get_requests_over_time(days: int = 7) -> List[Dict]:
    """Get request counts over time"""
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    since = datetime.now() - timedelta(days=days)

    cursor.execute('''
        SELECT DATE(created_at) as date, COUNT(*) as count
        FROM ai_requests
        WHERE created_at >= ?
        GROUP BY DATE(created_at)
        ORDER BY date
    ''', (since.isoformat(),))

    results = [{'date': row[0], 'count': row[1]} for row in cursor.fetchall()]
    conn.close()

    return results


def get_recent_interactions(limit: int = 20) -> List[Dict]:
    """Get recent request/response pairs"""
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT req.*, resp.response_text, resp.latency_ms, resp.total_tokens
        FROM ai_requests req
        JOIN ai_responses resp ON req.request_id = resp.request_id
        ORDER BY req.created_at DESC
        LIMIT ?
    ''', (limit,))

    results = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return results


# ==============================================================================
# ANALYTICS
# ==============================================================================

def analyze_usage_patterns() -> Dict:
    """Analyze AI usage patterns"""
    print("=" * 70)
    print("📊 USAGE PATTERNS")
    print("=" * 70)
    print()

    total = get_total_requests()
    by_model = get_requests_by_model()
    common_prompts = get_most_common_prompts()

    print(f"Total Requests: {total}")
    print()

    print("Requests by Model:")
    for model, count in by_model.items():
        percentage = (count / total * 100) if total > 0 else 0
        print(f"  {model:30s} {count:5d} ({percentage:.1f}%)")
    print()

    print("Most Common Prompts:")
    for prompt, count in common_prompts:
        preview = prompt[:50] + "..." if len(prompt) > 50 else prompt
        print(f"  {count:3d}x {preview}")
    print()

    return {
        'total_requests': total,
        'by_model': by_model,
        'common_prompts': common_prompts
    }


def analyze_performance() -> Dict:
    """Analyze model performance"""
    print("=" * 70)
    print("⚡ PERFORMANCE METRICS")
    print("=" * 70)
    print()

    latencies = get_average_latency()
    token_usage = get_token_usage()

    print("Average Latency (ms):")
    for model, latency in latencies.items():
        print(f"  {model:30s} {latency:8.2f} ms")
    print()

    print("Token Usage:")
    for model, tokens in token_usage.items():
        print(f"  {model:30s}")
        print(f"    Prompt tokens:     {tokens['prompt_tokens']:8d}")
        print(f"    Completion tokens: {tokens['completion_tokens']:8d}")
        print(f"    Total tokens:      {tokens['total_tokens']:8d}")
    print()

    return {
        'latencies': latencies,
        'token_usage': token_usage
    }


def analyze_knowledge_graph() -> Dict:
    """Build knowledge graph from query patterns"""
    print("=" * 70)
    print("🕸️  KNOWLEDGE GRAPH")
    print("=" * 70)
    print()

    # Get all prompts
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    cursor.execute('SELECT prompt FROM ai_requests')
    prompts = [row[0] for row in cursor.fetchall()]
    conn.close()

    # Extract keywords (simple word frequency)
    keywords = []
    for prompt in prompts:
        words = prompt.lower().split()
        keywords.extend([w for w in words if len(w) > 4])  # Words > 4 chars

    keyword_counts = Counter(keywords).most_common(20)

    print("Top Keywords:")
    for keyword, count in keyword_counts:
        print(f"  {keyword:20s} {count:3d}")
    print()

    # Build simple co-occurrence graph
    print("Keyword Co-occurrences:")
    cooccurrences = {}
    for prompt in prompts:
        words = set([w.lower() for w in prompt.split() if len(w) > 4])
        for w1 in words:
            for w2 in words:
                if w1 < w2:  # Avoid duplicates
                    pair = f"{w1}+{w2}"
                    cooccurrences[pair] = cooccurrences.get(pair, 0) + 1

    top_pairs = sorted(cooccurrences.items(), key=lambda x: x[1], reverse=True)[:10]
    for pair, count in top_pairs:
        print(f"  {pair:40s} {count:3d}")
    print()

    return {
        'keywords': keyword_counts,
        'cooccurrences': top_pairs
    }


# ==============================================================================
# HTML/SVG GRAPH GENERATION
# ==============================================================================

def generate_bar_chart_svg(data: Dict[str, int], title: str, width: int = 600, height: int = 400) -> str:
    """Generate SVG bar chart (pure HTML/SVG, no matplotlib!)"""

    if not data:
        return f'<svg width="{width}" height="{height}"><text x="10" y="20">No data</text></svg>'

    max_value = max(data.values())
    bar_width = (width - 100) / len(data)
    bar_spacing = 10

    svg = f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">\n'

    # Title
    svg += f'  <text x="{width/2}" y="20" text-anchor="middle" font-size="16" font-weight="bold">{title}</text>\n'

    # Bars
    x = 50
    for label, value in data.items():
        bar_height = (value / max_value * (height - 100)) if max_value > 0 else 0
        y = height - 50 - bar_height

        # Bar
        svg += f'  <rect x="{x}" y="{y}" width="{bar_width - bar_spacing}" height="{bar_height}" fill="#4CAF50" />\n'

        # Value label
        svg += f'  <text x="{x + bar_width/2 - bar_spacing/2}" y="{y - 5}" text-anchor="middle" font-size="12">{value}</text>\n'

        # X-axis label
        label_short = label[:15] + "..." if len(label) > 15 else label
        svg += f'  <text x="{x + bar_width/2 - bar_spacing/2}" y="{height - 30}" text-anchor="middle" font-size="10" transform="rotate(-45, {x + bar_width/2 - bar_spacing/2}, {height - 30})">{label_short}</text>\n'

        x += bar_width

    # Y-axis
    svg += f'  <line x1="50" y1="50" x2="50" y2="{height - 50}" stroke="black" />\n'

    # X-axis
    svg += f'  <line x1="50" y1="{height - 50}" x2="{width - 50}" y2="{height - 50}" stroke="black" />\n'

    svg += '</svg>'

    return svg


def export_html_report(output_path: str = 'ai_analytics_report.html'):
    """Export complete analytics report as HTML"""

    usage = analyze_usage_patterns()
    performance = analyze_performance()
    knowledge = analyze_knowledge_graph()
    recent = get_recent_interactions(10)

    html = '''<!DOCTYPE html>
<html>
<head>
    <title>AI Analytics Report</title>
    <style>
        body { font-family: monospace; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; }
        h1 { color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }
        h2 { color: #666; margin-top: 40px; }
        .metric { background: #f0f0f0; padding: 15px; margin: 10px 0; border-left: 4px solid #4CAF50; }
        .chart { margin: 20px 0; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #4CAF50; color: white; }
        .timestamp { color: #888; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 AI Analytics Report</h1>
        <p class="timestamp">Generated: ''' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '''</p>
'''

    # Usage stats
    html += '''
        <h2>📊 Usage Statistics</h2>
        <div class="metric">
            <strong>Total Requests:</strong> ''' + str(usage['total_requests']) + '''
        </div>
'''

    # Bar chart of requests by model
    if usage['by_model']:
        html += '''
        <div class="chart">
            ''' + generate_bar_chart_svg(usage['by_model'], 'Requests by Model') + '''
        </div>
'''

    # Performance metrics
    html += '''
        <h2>⚡ Performance Metrics</h2>
'''

    if performance['latencies']:
        html += '''
        <div class="chart">
            ''' + generate_bar_chart_svg(performance['latencies'], 'Average Latency (ms)') + '''
        </div>
'''

    # Recent interactions
    html += '''
        <h2>🕐 Recent Interactions</h2>
        <table>
            <thead>
                <tr>
                    <th>Model</th>
                    <th>Prompt</th>
                    <th>Response</th>
                    <th>Latency</th>
                    <th>Tokens</th>
                </tr>
            </thead>
            <tbody>
'''

    for interaction in recent:
        prompt_preview = interaction['prompt'][:50] + "..." if len(interaction['prompt']) > 50 else interaction['prompt']
        response_preview = interaction['response_text'][:50] + "..." if len(interaction['response_text']) > 50 else interaction['response_text']

        html += f'''
                <tr>
                    <td>{interaction['model']}</td>
                    <td>{prompt_preview}</td>
                    <td>{response_preview}</td>
                    <td>{interaction['latency_ms']} ms</td>
                    <td>{interaction['total_tokens']}</td>
                </tr>
'''

    html += '''
            </tbody>
        </table>
    </div>
</body>
</html>
'''

    with open(output_path, 'w') as f:
        f.write(html)

    print(f"✅ HTML report exported to {output_path}")
    return output_path


# ==============================================================================
# CLI
# ==============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='AI Analytics - Graphs & Insights')
    parser.add_argument('--all', action='store_true', help='Show all analytics')
    parser.add_argument('--usage-stats', action='store_true', help='Show usage statistics')
    parser.add_argument('--performance', action='store_true', help='Show performance metrics')
    parser.add_argument('--knowledge-graph', action='store_true', help='Show knowledge graph')
    parser.add_argument('--export', type=str, help='Export HTML report')

    args = parser.parse_args()

    if args.export:
        export_html_report(args.export)

    elif args.all or (not args.usage_stats and not args.performance and not args.knowledge_graph):
        # Show all by default
        analyze_usage_patterns()
        analyze_performance()
        analyze_knowledge_graph()

    else:
        if args.usage_stats:
            analyze_usage_patterns()

        if args.performance:
            analyze_performance()

        if args.knowledge_graph:
            analyze_knowledge_graph()
