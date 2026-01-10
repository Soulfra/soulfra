#!/usr/bin/env python3
"""
Component Factory - Reusable Web Components

Auto-generates styled, interactive web components from data.

Features:
- StatsCard - Numeric metric display cards
- DataTable - Searchable, sortable data tables
- Timeline - Event timeline visualization
- ChartWidget - Auto-generating charts
- SearchBar - Filter/search UI
- ActionButton - Styled action buttons
- StatusBadge - Colored status indicators

Usage:
    from component_factory import StatsCard, DataTable, Timeline

    # Generate a stats card
    html = StatsCard(
        label="Total API Calls",
        value=1234,
        icon="📊",
        color="#667eea"
    ).render()

    # Generate a data table
    html = DataTable(
        columns=['name', 'email', 'tier'],
        rows=[...],
        searchable=True,
        sortable=True
    ).render()
"""

from typing import List, Dict, Optional, Any, Union
from datetime import datetime


# ==============================================================================
# BASE COMPONENT
# ==============================================================================

class Component:
    """Base class for all components"""

    def render(self) -> str:
        """Render component to HTML string"""
        raise NotImplementedError("Subclasses must implement render()")

    def __str__(self):
        return self.render()


# ==============================================================================
# STATS CARD
# ==============================================================================

class StatsCard(Component):
    """
    Numeric stat card with icon, label, and value

    Example:
        StatsCard(label="Total Users", value=1234, icon="👥").render()
    """

    def __init__(self,
                 label: str,
                 value: Union[int, float, str],
                 icon: Optional[str] = None,
                 color: str = "#667eea",
                 subtitle: Optional[str] = None,
                 trend: Optional[str] = None):
        self.label = label
        self.value = value
        self.icon = icon
        self.color = color
        self.subtitle = subtitle
        self.trend = trend  # "up", "down", or None

    def render(self) -> str:
        icon_html = f'<div class="stat-icon">{self.icon}</div>' if self.icon else ''
        subtitle_html = f'<div class="stat-subtitle">{self.subtitle}</div>' if self.subtitle else ''

        trend_html = ''
        if self.trend == 'up':
            trend_html = '<span class="stat-trend stat-trend-up">↑</span>'
        elif self.trend == 'down':
            trend_html = '<span class="stat-trend stat-trend-down">↓</span>'

        return f"""
<div class="stat-card" style="border-left: 4px solid {self.color};">
    {icon_html}
    <div class="stat-label">{self.label}</div>
    <div class="stat-value">{self.value} {trend_html}</div>
    {subtitle_html}
</div>"""


class StatsGrid(Component):
    """Grid container for multiple stat cards"""

    def __init__(self, cards: List[StatsCard], columns: int = 4):
        self.cards = cards
        self.columns = columns

    def render(self) -> str:
        cards_html = '\n'.join(card.render() for card in self.cards)
        return f"""
<div class="stats-grid" style="grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));">
    {cards_html}
</div>"""


# ==============================================================================
# DATA TABLE
# ==============================================================================

class DataTable(Component):
    """
    Interactive data table with search, sort, and pagination

    Example:
        DataTable(
            columns=['name', 'email', 'status'],
            rows=[{'name': 'John', 'email': 'j@x.com', 'status': 'active'}],
            searchable=True
        ).render()
    """

    def __init__(self,
                 columns: List[str],
                 rows: List[Dict],
                 searchable: bool = True,
                 sortable: bool = True,
                 paginate: bool = False,
                 per_page: int = 20,
                 column_labels: Optional[Dict[str, str]] = None,
                 row_actions: Optional[List[Dict]] = None):
        self.columns = columns
        self.rows = rows
        self.searchable = searchable
        self.sortable = sortable
        self.paginate = paginate
        self.per_page = per_page
        self.column_labels = column_labels or {}
        self.row_actions = row_actions or []

    def render(self) -> str:
        table_id = f"table-{id(self)}"

        # Search bar
        search_html = ''
        if self.searchable:
            search_html = f'<input type="text" class="table-search" id="{table_id}-search" placeholder="🔍 Search..." onkeyup="filterTable(\'{table_id}\')">'

        # Table header
        header_cells = []
        for col in self.columns:
            label = self.column_labels.get(col, col.replace('_', ' ').title())
            sort_attr = f'onclick="sortTable(\'{table_id}\', \'{col}\')"' if self.sortable else ''
            header_cells.append(f'<th {sort_attr}>{label}</th>')

        if self.row_actions:
            header_cells.append('<th>Actions</th>')

        header_html = '<thead><tr>' + ''.join(header_cells) + '</tr></thead>'

        # Table body
        body_rows = []
        for row in self.rows:
            cells = []
            for col in self.columns:
                value = row.get(col, '-')
                # Format value
                if value is None:
                    value = '-'
                elif isinstance(value, float):
                    value = f"{value:,.2f}"
                elif isinstance(value, int):
                    value = f"{value:,}"
                cells.append(f'<td>{value}</td>')

            # Add action buttons
            if self.row_actions:
                action_html = ' '.join(
                    f'<a href="{action["url"].format(**row)}" class="btn-small">{action["label"]}</a>'
                    for action in self.row_actions
                )
                cells.append(f'<td>{action_html}</td>')

            body_rows.append('<tr>' + ''.join(cells) + '</tr>')

        body_html = '<tbody>' + ''.join(body_rows) + '</tbody>'

        # Pagination
        pagination_html = ''
        if self.paginate:
            pagination_html = f'<div class="table-pagination">Showing {min(len(self.rows), self.per_page)} of {len(self.rows)} rows</div>'

        return f"""
<div class="data-table-container">
    {search_html}
    <table id="{table_id}" class="data-table">
        {header_html}
        {body_html}
    </table>
    {pagination_html}
</div>"""


# ==============================================================================
# TIMELINE
# ==============================================================================

class Timeline(Component):
    """
    Event timeline visualization

    Example:
        Timeline(
            events=[
                {'timestamp': '2024-01-15 10:30', 'title': 'User signed up', 'description': 'john@example.com'},
                ...
            ]
        ).render()
    """

    def __init__(self,
                 events: List[Dict],
                 timestamp_key: str = 'timestamp',
                 title_key: str = 'title',
                 description_key: Optional[str] = 'description',
                 icon_key: Optional[str] = None):
        self.events = events
        self.timestamp_key = timestamp_key
        self.title_key = title_key
        self.description_key = description_key
        self.icon_key = icon_key

    def render(self) -> str:
        items_html = []

        for event in self.events:
            timestamp = event.get(self.timestamp_key, '')
            title = event.get(self.title_key, 'Event')
            description = event.get(self.description_key, '') if self.description_key else ''
            icon = event.get(self.icon_key, '•') if self.icon_key else '•'

            items_html.append(f"""
<div class="timeline-item">
    <div class="timeline-marker">{icon}</div>
    <div class="timeline-content">
        <div class="timeline-timestamp">{timestamp}</div>
        <div class="timeline-title">{title}</div>
        <div class="timeline-description">{description}</div>
    </div>
</div>""")

        return f"""
<div class="timeline">
    {''.join(items_html)}
</div>"""


# ==============================================================================
# CHART WIDGET
# ==============================================================================

class ChartWidget(Component):
    """
    Auto-generating chart widget

    Example:
        ChartWidget(
            chart_type='bar',
            data={'labels': ['Jan', 'Feb'], 'values': [10, 20]},
            title="Monthly Revenue"
        ).render()
    """

    def __init__(self,
                 chart_type: str,  # 'bar', 'line', 'pie', 'donut'
                 data: Dict[str, List],
                 title: Optional[str] = None,
                 height: int = 300):
        self.chart_type = chart_type
        self.data = data
        self.title = title
        self.height = height

    def render(self) -> str:
        chart_id = f"chart-{id(self)}"
        title_html = f'<h3 class="chart-title">{self.title}</h3>' if self.title else ''

        # For now, placeholder - would integrate with Chart.js or similar
        return f"""
<div class="chart-widget">
    {title_html}
    <div id="{chart_id}" class="chart-container" style="height: {self.height}px;">
        <p style="color: #999; text-align: center; padding: 40px;">
            📊 Chart visualization coming soon...<br>
            <small>Type: {self.chart_type}, Data points: {len(self.data.get('labels', []))}</small>
        </p>
    </div>
</div>"""


# ==============================================================================
# ACTION BUTTON
# ==============================================================================

class ActionButton(Component):
    """Styled action button"""

    def __init__(self,
                 label: str,
                 url: str,
                 icon: Optional[str] = None,
                 style: str = 'primary',  # 'primary', 'secondary', 'danger', 'success'
                 size: str = 'medium'):  # 'small', 'medium', 'large'
        self.label = label
        self.url = url
        self.icon = icon
        self.style = style
        self.size = size

    def render(self) -> str:
        icon_html = f'{self.icon} ' if self.icon else ''
        return f'<a href="{self.url}" class="btn btn-{self.style} btn-{self.size}">{icon_html}{self.label}</a>'


class ActionBar(Component):
    """Container for multiple action buttons"""

    def __init__(self, buttons: List[ActionButton]):
        self.buttons = buttons

    def render(self) -> str:
        buttons_html = '\n'.join(btn.render() for btn in self.buttons)
        return f"""
<div class="action-bar">
    {buttons_html}
</div>"""


# ==============================================================================
# STATUS BADGE
# ==============================================================================

class StatusBadge(Component):
    """Colored status indicator badge"""

    def __init__(self, label: str, status: str = 'default'):
        self.label = label
        self.status = status  # 'success', 'warning', 'error', 'info', 'default'

    def render(self) -> str:
        return f'<span class="badge badge-{self.status}">{self.label}</span>'


# ==============================================================================
# SEARCH BAR
# ==============================================================================

class SearchBar(Component):
    """Search/filter input with auto-complete"""

    def __init__(self,
                 placeholder: str = "Search...",
                 target_id: Optional[str] = None,
                 filters: Optional[List[Dict]] = None):
        self.placeholder = placeholder
        self.target_id = target_id
        self.filters = filters or []

    def render(self) -> str:
        search_id = f"search-{id(self)}"
        onkeyup = f'onkeyup="filterTable(\'{self.target_id}\')"' if self.target_id else ''

        filters_html = ''
        if self.filters:
            filter_options = ''.join(
                f'<option value="{f["value"]}">{f["label"]}</option>'
                for f in self.filters
            )
            filters_html = f'<select class="search-filter">{filter_options}</select>'

        return f"""
<div class="search-bar">
    <input type="text" id="{search_id}" class="search-input" placeholder="🔍 {self.placeholder}" {onkeyup}>
    {filters_html}
</div>"""


# ==============================================================================
# SECTION CONTAINER
# ==============================================================================

class Section(Component):
    """Card section container with title"""

    def __init__(self, title: str, content: Union[str, Component, List[Component]]):
        self.title = title
        self.content = content

    def render(self) -> str:
        if isinstance(self.content, list):
            content_html = '\n'.join(
                c.render() if isinstance(c, Component) else str(c)
                for c in self.content
            )
        elif isinstance(self.content, Component):
            content_html = self.content.render()
        else:
            content_html = str(self.content)

        return f"""
<div class="section">
    <h2>{self.title}</h2>
    {content_html}
</div>"""


# ==============================================================================
# COMPONENT STYLES
# ==============================================================================

COMPONENT_STYLES = """
<style>
    /* Stats Cards */
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 16px;
        margin-bottom: 24px;
    }

    .stat-card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: transform 0.3s;
    }

    .stat-card:hover {
        transform: translateY(-3px);
    }

    .stat-icon {
        font-size: 36px;
        margin-bottom: 12px;
    }

    .stat-label {
        font-size: 12px;
        color: #999;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
    }

    .stat-value {
        font-size: 32px;
        font-weight: bold;
        color: #333;
    }

    .stat-subtitle {
        font-size: 13px;
        color: #666;
        margin-top: 8px;
    }

    .stat-trend {
        font-size: 20px;
        margin-left: 8px;
    }

    .stat-trend-up { color: #4caf50; }
    .stat-trend-down { color: #f44336; }

    /* Data Table */
    .data-table-container {
        background: white;
        padding: 24px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }

    .table-search {
        width: 100%;
        padding: 12px;
        border: 2px solid #e0e0e0;
        border-radius: 8px;
        margin-bottom: 16px;
        font-size: 14px;
    }

    .table-search:focus {
        outline: none;
        border-color: #667eea;
    }

    .data-table {
        width: 100%;
        border-collapse: collapse;
    }

    .data-table th {
        text-align: left;
        padding: 12px;
        background: #f8f9fa;
        color: #666;
        font-size: 13px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        cursor: pointer;
    }

    .data-table th:hover {
        background: #e9ecef;
    }

    .data-table td {
        padding: 12px;
        border-bottom: 1px solid #f0f0f0;
        font-size: 14px;
        color: #333;
    }

    .data-table tr:hover {
        background: #f8f9fa;
    }

    /* Timeline */
    .timeline {
        position: relative;
        padding-left: 30px;
    }

    .timeline::before {
        content: '';
        position: absolute;
        left: 10px;
        top: 0;
        bottom: 0;
        width: 2px;
        background: #e0e0e0;
    }

    .timeline-item {
        position: relative;
        margin-bottom: 24px;
    }

    .timeline-marker {
        position: absolute;
        left: -25px;
        width: 20px;
        height: 20px;
        background: #667eea;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 10px;
    }

    .timeline-content {
        background: white;
        padding: 16px;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }

    .timeline-timestamp {
        font-size: 12px;
        color: #999;
        margin-bottom: 4px;
    }

    .timeline-title {
        font-weight: 600;
        color: #333;
        margin-bottom: 4px;
    }

    .timeline-description {
        font-size: 14px;
        color: #666;
    }

    /* Buttons */
    .btn {
        padding: 10px 20px;
        border-radius: 8px;
        text-decoration: none;
        font-weight: 600;
        font-size: 14px;
        display: inline-block;
        transition: all 0.3s;
        border: none;
        cursor: pointer;
    }

    .btn-primary { background: #667eea; color: white; }
    .btn-primary:hover { background: #5568d3; }

    .btn-secondary { background: #e0e0e0; color: #333; }
    .btn-secondary:hover { background: #d0d0d0; }

    .btn-danger { background: #f44336; color: white; }
    .btn-danger:hover { background: #d32f2f; }

    .btn-success { background: #4caf50; color: white; }
    .btn-success:hover { background: #45a049; }

    .btn-small {
        padding: 6px 12px;
        font-size: 12px;
    }

    .btn-large {
        padding: 14px 28px;
        font-size: 16px;
    }

    /* Action Bar */
    .action-bar {
        display: flex;
        gap: 12px;
        margin-bottom: 24px;
        flex-wrap: wrap;
    }

    /* Badges */
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 600;
    }

    .badge-success { background: #e8f5e9; color: #2e7d32; }
    .badge-warning { background: #fff3e0; color: #e65100; }
    .badge-error { background: #ffebee; color: #c62828; }
    .badge-info { background: #e3f2fd; color: #1976d2; }
    .badge-default { background: #f1f3f4; color: #5f6368; }

    /* Search Bar */
    .search-bar {
        display: flex;
        gap: 12px;
        margin-bottom: 16px;
    }

    .search-input {
        flex: 1;
        padding: 12px;
        border: 2px solid #e0e0e0;
        border-radius: 8px;
        font-size: 14px;
    }

    .search-input:focus {
        outline: none;
        border-color: #667eea;
    }

    .search-filter {
        padding: 12px;
        border: 2px solid #e0e0e0;
        border-radius: 8px;
        font-size: 14px;
    }

    /* Section */
    .section {
        background: white;
        padding: 24px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 24px;
    }

    .section h2 {
        font-size: 20px;
        color: #333;
        margin-bottom: 16px;
        padding-bottom: 12px;
        border-bottom: 2px solid #f0f0f0;
    }
</style>
"""


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def render_components(*components: Component) -> str:
    """Render multiple components together with styles"""
    html_parts = [COMPONENT_STYLES]
    for comp in components:
        if isinstance(comp, Component):
            html_parts.append(comp.render())
        else:
            html_parts.append(str(comp))
    return '\n'.join(html_parts)


# ==============================================================================
# JAVASCRIPT UTILITIES
# ==============================================================================

COMPONENT_SCRIPTS = """
<script>
    // Table search filter
    function filterTable(tableId) {
        const searchId = tableId + '-search';
        const input = document.getElementById(searchId);
        const filter = input.value.toLowerCase();
        const table = document.getElementById(tableId);
        const rows = table.getElementsByTagName('tr');

        for (let i = 1; i < rows.length; i++) {
            const row = rows[i];
            const text = row.textContent || row.innerText;
            row.style.display = text.toLowerCase().includes(filter) ? '' : 'none';
        }
    }

    // Table sorting
    function sortTable(tableId, column) {
        const table = document.getElementById(tableId);
        const rows = Array.from(table.querySelectorAll('tbody tr'));
        const columnIndex = Array.from(table.querySelectorAll('th')).findIndex(th => th.textContent.includes(column));

        rows.sort((a, b) => {
            const aVal = a.cells[columnIndex].textContent;
            const bVal = b.cells[columnIndex].textContent;
            return aVal.localeCompare(bVal);
        });

        const tbody = table.querySelector('tbody');
        rows.forEach(row => tbody.appendChild(row));
    }
</script>
"""


# ==============================================================================
# CLI DEMO
# ==============================================================================

if __name__ == '__main__':
    print("Component Factory Demo\n")

    # Demo stats cards
    print("=== Stats Cards ===")
    card = StatsCard(
        label="Total Users",
        value=1234,
        icon="👥",
        trend="up",
        subtitle="↑ 12% from last month"
    )
    print(card.render())

    # Demo data table
    print("\n=== Data Table ===")
    table = DataTable(
        columns=['name', 'email', 'status'],
        rows=[
            {'name': 'John Doe', 'email': 'john@example.com', 'status': 'active'},
            {'name': 'Jane Smith', 'email': 'jane@example.com', 'status': 'inactive'}
        ],
        searchable=True,
        sortable=True
    )
    print(table.render()[:500] + "...")

    print("\n✅ Component factory ready!")
    print("   Import components: from component_factory import StatsCard, DataTable, Timeline")
