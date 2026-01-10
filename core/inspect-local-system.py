#!/usr/bin/env python3

"""
LOCAL SYSTEM INSPECTOR
Deep dive into what's ACTUALLY on your laptop - directories, logs, databases, processes
Shows you the REAL state of your local system vs what's deployed
"""

import os
import glob
import sqlite3
import json
from pathlib import Path
from datetime import datetime
import subprocess

# ANSI colors
GREEN = '\033[0;32m'
BLUE = '\033[0;34m'
YELLOW = '\033[1;33m'
RED = '\033[0;91m'
CYAN = '\033[0;36m'
NC = '\033[0m'

def print_header(text):
    print(f"\n{CYAN}{'='*80}{NC}")
    print(f"{CYAN}  {text}{NC}")
    print(f"{CYAN}{'='*80}{NC}\n")

def check_running_services():
    """Check what's actually running on your laptop"""
    print_header("RUNNING SERVICES ON YOUR LAPTOP")

    ports = {
        5001: "Flask (Magic Publish)",
        8001: "Soulfra.com (QR Flow)",
        5002: "Soulfraapi.com (API)",
        5003: "Soulfra.ai (Chat)",
        11434: "Ollama (AI Models)"
    }

    for port, service in ports.items():
        try:
            result = subprocess.run(
                ["lsof", "-i", f":{port}"],
                capture_output=True,
                text=True
            )
            if result.stdout and "LISTEN" in result.stdout:
                pid = result.stdout.split()[1] if len(result.stdout.split()) > 1 else "?"
                print(f"{GREEN}✅ Port {port:5}{NC} - {service:30} (PID: {pid})")
            else:
                print(f"{RED}❌ Port {port:5}{NC} - {service:30} (NOT RUNNING)")
        except Exception as e:
            print(f"{RED}❌ Port {port:5}{NC} - {service:30} (Error: {e})")

    print()

def scan_directory_structure():
    """Show what directories and files you actually have"""
    print_header("LOCAL DIRECTORY STRUCTURE")

    base = "/Users/matthewmauer/Desktop/roommate-chat"

    important_dirs = [
        "soulfra-simple",
        "github-repos",
        "Soulfra",
        "logs"
    ]

    for dir_name in important_dirs:
        path = os.path.join(base, dir_name)
        if os.path.exists(path):
            size = subprocess.run(
                ["du", "-sh", path],
                capture_output=True,
                text=True
            ).stdout.split()[0]
            file_count = len(list(Path(path).rglob("*")))
            print(f"{GREEN}✅{NC} {dir_name:20} - {size:>8} ({file_count:,} files/dirs)")
        else:
            print(f"{RED}❌{NC} {dir_name:20} - NOT FOUND")

    print()

def scan_all_databases():
    """Find and inspect ALL soulfra.db files"""
    print_header("ALL SQLITE DATABASES ON YOUR LAPTOP")

    base = "/Users/matthewmauer/Desktop/roommate-chat"
    db_files = list(Path(base).rglob("soulfra.db"))

    print(f"Found {len(db_files)} soulfra.db files:\n")

    for i, db_path in enumerate(db_files, 1):
        print(f"{BLUE}Database #{i}:{NC} {db_path}")

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Get table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()

            print(f"  Tables: {', '.join([t[0] for t in tables])}")

            # Count records in key tables
            for table in ['posts', 'brands', 'users']:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"  {table:15} {count:>5} records")
                except:
                    pass

            # Check file size
            size = os.path.getsize(db_path)
            print(f"  Size: {size:,} bytes")

            # Check last modified
            mtime = datetime.fromtimestamp(os.path.getmtime(db_path))
            print(f"  Modified: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")

            conn.close()
            print()

        except Exception as e:
            print(f"  {RED}ERROR: {e}{NC}\n")

def scan_log_files():
    """Find and show recent log file contents"""
    print_header("LOG FILES ON YOUR LAPTOP")

    base = "/Users/matthewmauer/Desktop/roommate-chat"
    log_patterns = ["**/*.log", "**/logs/*.log"]

    all_logs = []
    for pattern in log_patterns:
        all_logs.extend(list(Path(base).glob(pattern)))

    # Remove duplicates
    all_logs = list(set(all_logs))

    print(f"Found {len(all_logs)} log files:\n")

    for log_path in sorted(all_logs, key=lambda x: os.path.getmtime(x), reverse=True)[:10]:
        size = os.path.getsize(log_path)
        mtime = datetime.fromtimestamp(os.path.getmtime(log_path))
        rel_path = log_path.relative_to(base)

        print(f"{BLUE}{rel_path}{NC}")
        print(f"  Size: {size:,} bytes | Modified: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")

        # Show last 5 lines
        if size > 0:
            try:
                with open(log_path, 'r') as f:
                    lines = f.readlines()
                    last_lines = lines[-5:] if len(lines) >= 5 else lines
                    print(f"  {YELLOW}Last {len(last_lines)} lines:{NC}")
                    for line in last_lines:
                        print(f"    {line.rstrip()[:100]}")
            except:
                print(f"  {RED}(Binary or unreadable){NC}")
        else:
            print(f"  {YELLOW}(Empty file){NC}")

        print()

def scan_github_repos():
    """Show what GitHub repos you have locally"""
    print_header("LOCAL GITHUB REPOS")

    repos_dir = "/Users/matthewmauer/Desktop/roommate-chat/github-repos"

    if not os.path.exists(repos_dir):
        print(f"{RED}github-repos directory not found!{NC}")
        return

    repos = [d for d in os.listdir(repos_dir) if os.path.isdir(os.path.join(repos_dir, d)) and not d.startswith('.')]

    print(f"Found {len(repos)} local repos:\n")

    for repo in sorted(repos):
        repo_path = os.path.join(repos_dir, repo)

        # Check if it's a git repo
        git_dir = os.path.join(repo_path, '.git')
        if os.path.exists(git_dir):
            # Get remote URL
            try:
                result = subprocess.run(
                    ["git", "-C", repo_path, "remote", "get-url", "origin"],
                    capture_output=True,
                    text=True
                )
                remote = result.stdout.strip()

                # Count HTML files
                html_files = list(Path(repo_path).glob("*.html"))
                post_files = list(Path(repo_path).glob("post/*.html"))

                # Check CNAME
                cname_path = os.path.join(repo_path, "CNAME")
                cname = ""
                if os.path.exists(cname_path):
                    with open(cname_path, 'r') as f:
                        cname = f.read().strip()

                print(f"{GREEN}✅{NC} {repo:25}")
                print(f"   Remote: {remote}")
                if cname:
                    print(f"   CNAME:  {cname}")
                print(f"   Files:  {len(html_files)} HTML, {len(post_files)} posts")
                print()

            except Exception as e:
                print(f"{YELLOW}⚠️{NC}  {repo:25} (git error: {e})\n")
        else:
            print(f"{RED}❌{NC} {repo:25} (not a git repo)\n")

def check_ollama_models():
    """Check what Ollama models are available"""
    print_header("OLLAMA MODELS ON YOUR LAPTOP")

    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            print(result.stdout)
        else:
            print(f"{RED}Ollama not running or not installed{NC}")
    except Exception as e:
        print(f"{RED}Error checking Ollama: {e}{NC}")

    print()

def check_python_packages():
    """Check what Python packages you have installed"""
    print_header("PYTHON PACKAGES (relevant ones)")

    important_packages = [
        "flask",
        "requests",
        "beautifulsoup4",
        "lxml",
        "openai",
        "anthropic",
        "ollama"
    ]

    for package in important_packages:
        try:
            result = subprocess.run(
                ["pip3", "show", package],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                version = [line for line in result.stdout.split('\n') if line.startswith('Version:')]
                version = version[0].split(':')[1].strip() if version else "unknown"
                print(f"{GREEN}✅{NC} {package:20} v{version}")
            else:
                print(f"{RED}❌{NC} {package:20} NOT INSTALLED")
        except:
            print(f"{RED}❌{NC} {package:20} ERROR")

    print()

def network_access_info():
    """Show info about network access (for roommate sharing)"""
    print_header("NETWORK ACCESS CONFIGURATION")

    # Get local IP
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        print(f"{BLUE}Your local IP:{NC} {local_ip}")
        print(f"{BLUE}Computer name:{NC} {socket.gethostname()}")
    except Exception as e:
        print(f"{RED}Could not get local IP: {e}{NC}")

    print()
    print(f"{YELLOW}For roommates to access your services:{NC}")
    print(f"  1. Flask (Magic Publish): http://{local_ip}:5001/studio")
    print(f"  2. Ollama API:            http://{local_ip}:11434/api/tags")
    print(f"  3. QR Flow:               http://{local_ip}:8001")
    print()
    print(f"{YELLOW}⚠️  Security notes:{NC}")
    print(f"  • Services are currently bound to localhost (127.0.0.1)")
    print(f"  • To allow roommate access, need to bind to 0.0.0.0")
    print(f"  • Consider firewall rules and authentication!")
    print()

def main():
    print()
    print(f"{CYAN}{'='*80}{NC}")
    print(f"{CYAN}  🔍 LOCAL SYSTEM INSPECTOR{NC}")
    print(f"{CYAN}  Showing what's ACTUALLY on your laptop{NC}")
    print(f"{CYAN}  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{NC}")
    print(f"{CYAN}{'='*80}{NC}")

    check_running_services()
    scan_directory_structure()
    scan_all_databases()
    scan_github_repos()
    scan_log_files()
    check_ollama_models()
    check_python_packages()
    network_access_info()

    print_header("SUMMARY")
    print(f"{GREEN}✅ Local system inspection complete!{NC}\n")
    print("Now you can see:")
    print("  • What services are actually running")
    print("  • What files/databases exist on your laptop")
    print("  • What GitHub repos you have locally")
    print("  • Recent log file contents")
    print("  • Network access info for roommates")
    print()
    print(f"{CYAN}{'='*80}{NC}")
    print()

if __name__ == "__main__":
    main()
