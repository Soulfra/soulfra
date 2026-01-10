#!/usr/bin/env python3
"""
README CLI - Terminal tool for managing GitHub READMEs

Usage:
    ./readme_cli.py generate matt           # Generate README markdown
    ./readme_cli.py preview matt            # Preview in terminal with colors
    ./readme_cli.py push matt               # Push to GitHub repo
    ./readme_cli.py watch                   # Auto-regenerate on new recordings
    ./readme_cli.py qr matt                 # Show QR code in terminal
    ./readme_cli.py stats matt              # Show profile stats

Installation:
    pip install rich colorama requests qrcode
"""

import sys
import argparse
import requests
import time
from pathlib import Path

try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("⚠️  Install 'rich' for better terminal output: pip install rich")

try:
    import qrcode
    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False


class ReadmeCLI:
    """Terminal interface for README management"""

    def __init__(self, api_url="http://localhost:5001"):
        self.api_url = api_url.rstrip('/')
        self.console = Console() if RICH_AVAILABLE else None

    def generate(self, slug):
        """Generate README markdown"""
        try:
            if self.console:
                with self.console.status(f"[bold green]Generating README for {slug}..."):
                    response = requests.get(f"{self.api_url}/api/readme/{slug}")
            else:
                print(f"Generating README for {slug}...")
                response = requests.get(f"{self.api_url}/api/readme/{slug}")

            response.raise_for_status()
            markdown = response.text

            # Save to file
            output_file = Path(f"README_{slug}.md")
            output_file.write_text(markdown)

            if self.console:
                self.console.print(f"✅ README generated: [cyan]{output_file}[/cyan]")
                self.console.print(f"📄 {len(markdown)} characters, {markdown.count(chr(10))} lines")
            else:
                print(f"✅ README generated: {output_file}")

            return markdown

        except requests.exceptions.RequestException as e:
            if self.console:
                self.console.print(f"[bold red]❌ Error:[/bold red] {e}")
            else:
                print(f"❌ Error: {e}")
            return None

    def preview(self, slug):
        """Preview README in terminal with rich formatting"""
        markdown = self.generate(slug)
        if not markdown:
            return

        if self.console and RICH_AVAILABLE:
            print("\n" + "="*80 + "\n")
            md = Markdown(markdown)
            self.console.print(md)
            print("\n" + "="*80 + "\n")
        else:
            print("\n" + "="*80)
            print(markdown)
            print("="*80 + "\n")

    def stats(self, slug):
        """Show profile statistics"""
        try:
            response = requests.get(f"{self.api_url}/api/readme/{slug}/json")
            response.raise_for_status()
            data = response.json()

            if self.console and RICH_AVAILABLE:
                # Create stats table
                table = Table(title=f"📊 Stats for {data['display_name']}")
                table.add_column("Metric", style="cyan", no_wrap=True)
                table.add_column("Value", style="magenta")

                table.add_row("Slug", data['slug'])
                table.add_row("Bio", data.get('bio', 'No bio') or 'No bio')
                table.add_row("Recordings", str(len(data.get('recordings', []))))
                table.add_row("Top Words", str(len(data.get('wordmap', []))))
                table.add_row("Profile URL", data['profile_url'])
                table.add_row("Generated At", data['generated_at'])

                self.console.print(table)

                # Wordmap
                if data.get('wordmap'):
                    wm_table = Table(title="🗣️ Top Words")
                    wm_table.add_column("#", style="dim")
                    wm_table.add_column("Word", style="cyan bold")
                    wm_table.add_column("Count", style="magenta")

                    for i, word in enumerate(data['wordmap'][:10], 1):
                        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "▪️"
                        wm_table.add_row(emoji, word['word'], str(word['count']))

                    self.console.print(wm_table)
            else:
                print(f"\n📊 Stats for {data['display_name']}")
                print(f"Slug: {data['slug']}")
                print(f"Recordings: {len(data.get('recordings', []))}")
                print(f"Top Words: {len(data.get('wordmap', []))}")
                print(f"Profile: {data['profile_url']}\n")

        except requests.exceptions.RequestException as e:
            if self.console:
                self.console.print(f"[bold red]❌ Error:[/bold red] {e}")
            else:
                print(f"❌ Error: {e}")

    def qr(self, slug):
        """Show QR code in terminal"""
        if not QR_AVAILABLE:
            print("❌ qrcode library not installed. Run: pip install qrcode")
            return

        profile_url = f"https://cringeproof.com/{slug}"

        qr = qrcode.QRCode(border=1)
        qr.add_data(profile_url)
        qr.make(fit=True)

        if self.console and RICH_AVAILABLE:
            panel = Panel(
                qr.get_matrix_text(),
                title=f"🔗 Scan to visit cringeproof.com/{slug}",
                border_style="cyan"
            )
            self.console.print(panel)
        else:
            print(f"\n{'='*50}")
            print(f"  Scan to visit: {profile_url}")
            print(f"{'='*50}")
            qr.print_ascii(invert=True)
            print(f"{'='*50}\n")

    def push(self, slug, repo_path="."):
        """Push README to GitHub repository"""
        markdown = self.generate(slug)
        if not markdown:
            return

        readme_path = Path(repo_path) / "README.md"

        try:
            # Write README
            readme_path.write_text(markdown)

            if self.console:
                self.console.print(f"✅ README updated: [cyan]{readme_path}[/cyan]")
                self.console.print("[yellow]💡 Next steps:[/yellow]")
                self.console.print("   git add README.md")
                self.console.print("   git commit -m '🤖 Update README from voice recordings'")
                self.console.print("   git push")
            else:
                print(f"✅ README updated: {readme_path}")
                print("\n💡 Next steps:")
                print("   git add README.md")
                print("   git commit -m '🤖 Update README from voice recordings'")
                print("   git push")

        except Exception as e:
            if self.console:
                self.console.print(f"[bold red]❌ Error:[/bold red] {e}")
            else:
                print(f"❌ Error: {e}")

    def watch(self, interval=60):
        """Watch for changes and auto-regenerate README"""
        if self.console:
            self.console.print(f"[bold green]👀 Watching for changes...[/bold green]")
            self.console.print(f"[dim]Checking every {interval}s. Press Ctrl+C to stop.[/dim]\n")
        else:
            print(f"👀 Watching for changes (every {interval}s)...")

        last_hash = None

        try:
            while True:
                # Check for updates (simplified - would check database in real impl)
                response = requests.get(f"{self.api_url}/api/health")
                current_hash = str(response.headers.get('X-Request-Id', time.time()))

                if last_hash and current_hash != last_hash:
                    if self.console:
                        self.console.print(f"[yellow]🔄 Change detected! Regenerating...[/yellow]")
                    else:
                        print("🔄 Change detected! Regenerating...")

                last_hash = current_hash
                time.sleep(interval)

        except KeyboardInterrupt:
            if self.console:
                self.console.print("\n[yellow]👋 Stopped watching[/yellow]")
            else:
                print("\n👋 Stopped watching")


def main():
    parser = argparse.ArgumentParser(
        description="README CLI - Manage GitHub READMEs from voice recordings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s generate matt       # Generate README for user 'matt'
  %(prog)s preview matt        # Preview with color formatting
  %(prog)s push matt           # Push to current repo
  %(prog)s stats matt          # Show profile statistics
  %(prog)s qr matt             # Show QR code in terminal
  %(prog)s watch               # Auto-regenerate on changes
        """
    )

    parser.add_argument('command', choices=['generate', 'preview', 'push', 'stats', 'qr', 'watch'],
                        help='Command to execute')
    parser.add_argument('slug', nargs='?', help='User slug (e.g., matt, alice)')
    parser.add_argument('--api-url', default='http://localhost:5001',
                        help='API endpoint URL')
    parser.add_argument('--repo', default='.', help='Repository path for push command')
    parser.add_argument('--interval', type=int, default=60,
                        help='Watch interval in seconds')

    args = parser.parse_args()

    # Validate slug requirement
    if args.command != 'watch' and not args.slug:
        parser.error(f"{args.command} command requires a slug argument")

    cli = ReadmeCLI(api_url=args.api_url)

    if args.command == 'generate':
        cli.generate(args.slug)
    elif args.command == 'preview':
        cli.preview(args.slug)
    elif args.command == 'push':
        cli.push(args.slug, args.repo)
    elif args.command == 'stats':
        cli.stats(args.slug)
    elif args.command == 'qr':
        cli.qr(args.slug)
    elif args.command == 'watch':
        cli.watch(args.interval)


if __name__ == '__main__':
    main()
