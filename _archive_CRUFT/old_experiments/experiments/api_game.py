#!/usr/bin/env python3
"""
API Explorer Game - Interactive Swagger Alternative

Terminal-based game where you "walk through" API routes like exploring a dungeon!
Pure Python stdlib using curses.

Usage:
    python3 api_game.py

Controls:
    ↑↓        Navigate routes
    Enter     "Enter" route (view details)
    T         Test route (make HTTP request)
    M         Map view (see all categories)
    Q         Quit

Like:
- Swagger UI but game-style
- Zelda/Doom map but for APIs
- Pokemon menu but for HTTP endpoints

Features:
- Visual route map
- Interactive testing
- Achievement system (test all routes = unlock badge)
- Progress tracking
"""

import curses
import json
import sys
import urllib.request
import urllib.error


# Route database (organized like /sitemap)
ROUTES = {
    'Content & Posts': [
        {'path': '/', 'method': 'GET', 'desc': 'Homepage - Posts feed with AI predictions'},
        {'path': '/post/<slug>', 'method': 'GET', 'desc': 'Individual post with comments'},
        {'path': '/live', 'method': 'GET', 'desc': 'Real-time comment stream'},
    ],
    'Theme System': [
        {'path': '/shipyard', 'method': 'GET', 'desc': 'Theme browser (Dinghy → Galleon)'},
        {'path': '/brands', 'method': 'GET', 'desc': 'Brand marketplace'},
        {'path': '/tiers', 'method': 'GET', 'desc': 'Tier showcase'},
    ],
    'Users & Souls': [
        {'path': '/souls', 'method': 'GET', 'desc': 'All user souls/personas'},
        {'path': '/soul/<username>', 'method': 'GET', 'desc': 'Soul profile'},
        {'path': '/login', 'method': 'GET', 'desc': 'User authentication'},
    ],
    'AI & Machine Learning': [
        {'path': '/train', 'method': 'GET', 'desc': 'Training interface'},
        {'path': '/reasoning', 'method': 'GET', 'desc': 'Reasoning dashboard'},
        {'path': '/ml', 'method': 'GET', 'desc': 'ML dashboard'},
        {'path': '/dashboard', 'method': 'GET', 'desc': 'Live predictions'},
    ],
    'Utilities': [
        {'path': '/sitemap', 'method': 'GET', 'desc': 'Visual route map'},
        {'path': '/sitemap.xml', 'method': 'GET', 'desc': 'SEO XML sitemap'},
        {'path': '/robots.txt', 'method': 'GET', 'desc': 'Crawler rules'},
        {'path': '/feed.xml', 'method': 'GET', 'desc': 'RSS feed'},
    ],
    'API Endpoints': [
        {'path': '/api/health', 'method': 'GET', 'desc': 'Server status (JSON)'},
        {'path': '/api/posts', 'method': 'GET', 'desc': 'All posts (JSON)'},
    ],
}


def test_route(base_url, route_path):
    """
    Test HTTP route

    Args:
        base_url: Base URL (e.g., http://localhost:5001)
        route_path: Route path (e.g., /api/health)

    Returns:
        dict: {'success': bool, 'status': int, 'data': str}
    """
    # Replace route params with example values
    test_path = route_path.replace('<slug>', 'test').replace('<username>', 'alice')

    url = base_url + test_path

    try:
        response = urllib.request.urlopen(url, timeout=5)
        status = response.getcode()
        data = response.read().decode('utf-8')[:500]  # First 500 chars

        return {
            'success': True,
            'status': status,
            'data': data,
        }
    except urllib.error.HTTPError as e:
        return {
            'success': False,
            'status': e.code,
            'data': f"HTTP Error: {e.reason}",
        }
    except Exception as e:
        return {
            'success': False,
            'status': 0,
            'data': f"Error: {str(e)}",
        }


def draw_box(stdscr, y, x, height, width, title=""):
    """Draw a box with optional title"""
    try:
        # Corners and edges
        stdscr.addch(y, x, curses.ACS_ULCORNER)
        stdscr.addch(y, x + width - 1, curses.ACS_URCORNER)
        stdscr.addch(y + height - 1, x, curses.ACS_LLCORNER)
        stdscr.addch(y + height - 1, x + width - 1, curses.ACS_LRCORNER)

        for i in range(1, width - 1):
            stdscr.addch(y, x + i, curses.ACS_HLINE)
            stdscr.addch(y + height - 1, x + i, curses.ACS_HLINE)

        for i in range(1, height - 1):
            stdscr.addch(y + i, x, curses.ACS_VLINE)
            stdscr.addch(y + i, x + width - 1, curses.ACS_VLINE)

        # Title
        if title:
            title_text = f" {title} "
            stdscr.addstr(y, x + 2, title_text, curses.A_BOLD)
    except:
        pass


def api_explorer(base_url='http://localhost:5001'):
    """
    Main API explorer game loop

    Args:
        base_url: Base URL for API testing
    """
    def main(stdscr):
        # Setup
        curses.curs_set(0)
        stdscr.clear()

        # Colors
        try:
            curses.start_color()
            curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
            curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
            curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
            curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)
        except:
            pass

        # State
        current_category = 0
        current_route = 0
        view_mode = 'list'  # 'list' or 'detail' or 'test'
        test_results = {}
        tested_routes = set()

        categories = list(ROUTES.keys())

        while True:
            stdscr.clear()
            height, width = stdscr.getmaxyx()

            if view_mode == 'list':
                # List view - browse routes
                stdscr.addstr(0, 0, "🗺️  API EXPLORER", curses.A_BOLD | curses.color_pair(1))
                stdscr.addstr(0, width - 30, f"Tested: {len(tested_routes)} routes", curses.A_DIM)

                stdscr.addstr(1, 0, "=" * min(width - 1, 80))

                # Category tabs
                tab_y = 2
                tab_x = 0

                for i, category in enumerate(categories):
                    if i == current_category:
                        attr = curses.A_REVERSE | curses.A_BOLD
                    else:
                        attr = curses.A_DIM

                    tab_text = f" {category} "
                    try:
                        stdscr.addstr(tab_y, tab_x, tab_text, attr)
                    except:
                        pass
                    tab_x += len(tab_text) + 1

                # Routes list
                route_y = 4
                routes_in_category = ROUTES[categories[current_category]]

                for i, route in enumerate(routes_in_category):
                    if i == current_route:
                        prefix = "▶ "
                        attr = curses.A_BOLD | curses.color_pair(2)
                    else:
                        prefix = "  "
                        attr = curses.A_NORMAL

                    # Mark tested routes
                    route_key = f"{route['method']} {route['path']}"
                    if route_key in tested_routes:
                        status = "✓"
                        attr |= curses.color_pair(2)
                    else:
                        status = " "

                    line = f"{prefix}{status} {route['method']:4} {route['path']:30} # {route['desc']}"

                    try:
                        stdscr.addstr(route_y + i, 0, line[:width-1], attr)
                    except:
                        pass

                # Controls
                controls_y = height - 3
                try:
                    stdscr.addstr(controls_y, 0, "─" * min(width - 1, 80), curses.A_DIM)
                    stdscr.addstr(controls_y + 1, 0, "↑↓: Navigate  Enter: Details  T: Test  Tab: Next Category  Q: Quit", curses.A_DIM)
                except:
                    pass

            elif view_mode == 'detail':
                # Detail view - show route details
                route = ROUTES[categories[current_category]][current_route]

                stdscr.addstr(0, 0, "📖  ROUTE DETAILS", curses.A_BOLD | curses.color_pair(1))
                stdscr.addstr(1, 0, "=" * min(width - 1, 80))

                try:
                    stdscr.addstr(3, 0, f"Method: {route['method']}", curses.A_BOLD)
                    stdscr.addstr(4, 0, f"Path:   {route['path']}", curses.color_pair(2))
                    stdscr.addstr(5, 0, f"Desc:   {route['desc']}")

                    stdscr.addstr(7, 0, "Full URL:", curses.A_BOLD)
                    test_url = base_url + route['path'].replace('<slug>', 'test').replace('<username>', 'alice')
                    stdscr.addstr(8, 0, test_url, curses.color_pair(3))

                    # Show test results if available
                    route_key = f"{route['method']} {route['path']}"
                    if route_key in test_results:
                        result = test_results[route_key]

                        stdscr.addstr(10, 0, "Last Test Result:", curses.A_BOLD)

                        if result['success']:
                            stdscr.addstr(11, 0, f"Status: {result['status']}", curses.color_pair(2))
                            stdscr.addstr(12, 0, "Response:", curses.A_DIM)
                            for i, line in enumerate(result['data'].split('\n')[:10]):
                                stdscr.addstr(13 + i, 0, line[:width-1], curses.A_DIM)
                        else:
                            stdscr.addstr(11, 0, f"Failed: {result['data']}", curses.color_pair(4))

                    # Controls
                    stdscr.addstr(height - 2, 0, "T: Test Route  B: Back  Q: Quit", curses.A_DIM)
                except:
                    pass

            # Handle input
            key = stdscr.getch()

            if key == ord('q') or key == ord('Q'):
                break

            elif key == curses.KEY_UP:
                if view_mode == 'list':
                    current_route = max(0, current_route - 1)

            elif key == curses.KEY_DOWN:
                if view_mode == 'list':
                    max_route = len(ROUTES[categories[current_category]]) - 1
                    current_route = min(max_route, current_route + 1)

            elif key == ord('\t'):  # Tab
                if view_mode == 'list':
                    current_category = (current_category + 1) % len(categories)
                    current_route = 0

            elif key == ord('\n'):  # Enter
                if view_mode == 'list':
                    view_mode = 'detail'

            elif key == ord('b') or key == ord('B'):
                view_mode = 'list'

            elif key == ord('t') or key == ord('T'):
                # Test current route
                route = ROUTES[categories[current_category]][current_route]
                route_key = f"{route['method']} {route['path']}"

                # Show "Testing..." message
                stdscr.addstr(height - 1, 0, "Testing route...", curses.A_BOLD)
                stdscr.refresh()

                result = test_route(base_url, route['path'])
                test_results[route_key] = result

                if result['success']:
                    tested_routes.add(route_key)

                view_mode = 'detail'  # Switch to detail to show results

            stdscr.refresh()

    curses.wrapper(main)


def main():
    """CLI interface"""
    print("🎮 API Explorer Game - Interactive Swagger Alternative")
    print("=" * 60)
    print()

    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = 'http://localhost:5001'

    print(f"Base URL: {base_url}")
    print()
    print("Starting game...")
    print()

    try:
        api_explorer(base_url)
    except KeyboardInterrupt:
        pass

    print()
    print("✅ Thanks for exploring!")


if __name__ == '__main__':
    main()
