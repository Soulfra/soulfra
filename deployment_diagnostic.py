#!/usr/bin/env python3
"""
Deployment Diagnostic Tool

Checks system status and helps fix common deployment issues.

Usage:
    python3 deployment_diagnostic.py check-all     # Full diagnostic
    python3 deployment_diagnostic.py check-db      # Database check
    python3 deployment_diagnostic.py fix-db        # Fix database schema
    python3 deployment_diagnostic.py kill-zombies  # Kill Flask zombies
    python3 deployment_diagnostic.py check-ports   # Check all ports
    python3 deployment_diagnostic.py check-ollama  # Check Ollama status
"""

import sys
import os
import subprocess
import sqlite3
import json
from pathlib import Path
from database import get_db

# Colors
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(msg):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'═'*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{msg}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'═'*70}{Colors.ENDC}\n")

def print_success(msg):
    print(f"{Colors.OKGREEN}✅ {msg}{Colors.ENDC}")

def print_error(msg):
    print(f"{Colors.FAIL}❌ {msg}{Colors.ENDC}")

def print_warning(msg):
    print(f"{Colors.WARNING}⚠️  {msg}{Colors.ENDC}")

def print_info(msg):
    print(f"{Colors.OKBLUE}ℹ️  {msg}{Colors.ENDC}")


# =============================================================================
# PORT CHECKS
# =============================================================================

def check_ports():
    """Check which ports are in use"""
    print_header("PORT STATUS")

    ports_to_check = {
        5001: "Flask App (main)",
        5000: "Control Center",
        7000: "Control Center",
        3000: "Node.js",
        5432: "PostgreSQL",
        11434: "Ollama (default)",
        11435: "Ollama (creative)",
        11436: "Ollama (precise)",
        11437: "Ollama (experimental)"
    }

    for port, service in ports_to_check.items():
        try:
            result = subprocess.run(
                f"lsof -i:{port} -t",
                shell=True,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                print_success(f"Port {port:5d} - {service:25s} ({len(pids)} process(es))")
            else:
                print_warning(f"Port {port:5d} - {service:25s} (not running)")
        except Exception as e:
            print_error(f"Port {port:5d} - Error checking: {e}")


# =============================================================================
# FLASK PROCESS CHECKS
# =============================================================================

def check_flask_processes():
    """Check for Flask zombie processes"""
    print_header("FLASK PROCESSES")

    try:
        result = subprocess.run(
            "ps aux | grep 'python3 app.py' | grep -v grep",
            shell=True,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            processes = result.stdout.strip().split('\n')
            count = len([p for p in processes if p.strip()])

            if count > 1:
                print_error(f"Found {count} Flask processes (should be 1)")
                print_warning("Zombie processes detected - run: python3 deployment_diagnostic.py kill-zombies")

                for proc in processes:
                    if proc.strip():
                        print(f"  {proc}")
            else:
                print_success(f"Flask running cleanly ({count} process)")
        else:
            print_warning("No Flask processes found")
            print_info("Start with: python3 app.py")

    except Exception as e:
        print_error(f"Error checking processes: {e}")


def kill_flask_zombies():
    """Kill all Flask processes"""
    print_header("KILLING FLASK ZOMBIES")

    try:
        result = subprocess.run(
            "pkill -9 -f 'python3 app.py'",
            shell=True,
            capture_output=True,
            text=True
        )

        print_success("Killed all Flask processes")
        print_info("Wait 2 seconds then start fresh: python3 app.py")

    except Exception as e:
        print_error(f"Error killing processes: {e}")


# =============================================================================
# OLLAMA CHECKS
# =============================================================================

def check_ollama():
    """Check Ollama status on all ports"""
    print_header("OLLAMA STATUS")

    ports = [11434, 11435, 11436, 11437]
    names = ["Default (Technical)", "Creative", "Precise", "Experimental"]

    for port, name in zip(ports, names):
        try:
            import requests
            response = requests.get(f"http://localhost:{port}/api/tags", timeout=2)

            if response.status_code == 200:
                data = response.json()
                models = data.get('models', [])
                model_names = [m['name'] for m in models]

                print_success(f"Port {port} - {name:20s} - Models: {', '.join(model_names)}")
            else:
                print_error(f"Port {port} - {name:20s} - HTTP {response.status_code}")

        except requests.exceptions.ConnectionError:
            print_warning(f"Port {port} - {name:20s} - Not running")
            print_info(f"          Start with: OLLAMA_HOST=0.0.0.0:{port} ollama serve &")
        except Exception as e:
            print_error(f"Port {port} - {name:20s} - Error: {e}")

    print()
    print_info("For full tumbler system, you need all 4 ports running")


# =============================================================================
# DATABASE CHECKS
# =============================================================================

def check_database():
    """Check database schema and integrity"""
    print_header("DATABASE STATUS")

    # Check if database exists
    db_path = Path('soulfra.db')

    if not db_path.exists():
        print_error("Database not found: soulfra.db")
        print_info("Initialize with: python3 -c 'from database import init_db; init_db()'")
        return

    # Check size
    size_mb = db_path.stat().st_size / (1024 * 1024)
    print_success(f"Database exists: {size_mb:.2f} MB")

    # Check schema
    db = get_db()

    # Get all tables
    tables = db.execute('''
        SELECT name FROM sqlite_master WHERE type='table'
    ''').fetchall()

    table_names = [t['name'] for t in tables]

    print_info(f"Found {len(table_names)} tables")

    # Check critical tables
    critical_tables = [
        'users', 'posts', 'brands', 'projects', 'api_keys',
        'domain_ownership', 'referral_codes', 'content_tumbles'
    ]

    missing_tables = []

    for table in critical_tables:
        if table in table_names:
            count = db.execute(f'SELECT COUNT(*) as count FROM {table}').fetchone()['count']
            print_success(f"Table '{table}' exists ({count} rows)")
        else:
            print_warning(f"Table '{table}' missing")
            missing_tables.append(table)

    # Check for problematic columns
    print()
    print_info("Checking schema integrity...")

    issues = []

    # Check users.role
    try:
        db.execute('SELECT role FROM users LIMIT 1')
        print_success("Column 'users.role' exists")
    except sqlite3.OperationalError:
        print_warning("Column 'users.role' missing")
        issues.append(('users', 'role', 'TEXT DEFAULT "user"'))

    # Check tokens_used tracking
    try:
        db.execute('SELECT tokens_used FROM api_usage LIMIT 1')
        print_success("Column 'api_usage.tokens_used' exists")
    except sqlite3.OperationalError:
        print_warning("Table 'api_usage' or column 'tokens_used' missing")
        issues.append(('api_usage', 'tokens_used', 'INTEGER DEFAULT 0'))

    db.close()

    if issues or missing_tables:
        print()
        print_error(f"Found {len(issues)} schema issues")
        print_info("Fix with: python3 deployment_diagnostic.py fix-db")
    else:
        print()
        print_success("Database schema is healthy!")


def fix_database():
    """Fix database schema issues"""
    print_header("FIXING DATABASE SCHEMA")

    db = get_db()

    # Fix users.role
    try:
        db.execute('SELECT role FROM users LIMIT 1')
        print_info("users.role already exists")
    except sqlite3.OperationalError:
        print_info("Adding users.role column...")
        db.execute('ALTER TABLE users ADD COLUMN role TEXT DEFAULT "user"')
        db.commit()
        print_success("Added users.role")

    # Create api_usage table if missing
    try:
        db.execute('SELECT * FROM api_usage LIMIT 1')
        print_info("api_usage table already exists")
    except sqlite3.OperationalError:
        print_info("Creating api_usage table...")
        db.execute('''
            CREATE TABLE IF NOT EXISTS api_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                endpoint TEXT,
                tokens_used INTEGER DEFAULT 0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        db.commit()
        print_success("Created api_usage table")

    # Create content_tumbles if missing
    try:
        db.execute('SELECT * FROM content_tumbles LIMIT 1')
        print_info("content_tumbles table already exists")
    except sqlite3.OperationalError:
        print_info("Creating content_tumbles table...")
        db.execute('''
            CREATE TABLE IF NOT EXISTS content_tumbles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                project_slug TEXT NOT NULL,
                content_type TEXT NOT NULL,
                user_id INTEGER,
                best_port INTEGER,
                best_model TEXT,
                best_score REAL,
                best_content TEXT,
                tracking_codes TEXT,
                all_results TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        ''')
        db.commit()
        print_success("Created content_tumbles table")

    db.close()

    print()
    print_success("Database schema fixed!")


# =============================================================================
# DEPLOYMENT STATUS
# =============================================================================

def check_deployment_status():
    """Check deployment configuration"""
    print_header("DEPLOYMENT STATUS")

    # Check for deployment config files
    configs = {
        'railway.json': 'Railway',
        'railway.toml': 'Railway',
        'Procfile': 'Railway/Heroku',
        'vercel.json': 'Vercel',
        'Dockerfile': 'Docker',
        'docker-compose.yml': 'Docker Compose',
        '.env': 'Environment Variables'
    }

    print_info("Deployment configs found:")

    for filename, platform in configs.items():
        if Path(filename).exists():
            print_success(f"{filename:20s} → {platform}")
        else:
            print_warning(f"{filename:20s} → Missing")

    print()

    # Check environment variables
    env_vars = ['BASE_URL', 'SECRET_KEY', 'FLASK_ENV', 'DATABASE_PATH']

    print_info("Environment variables:")

    for var in env_vars:
        value = os.environ.get(var)
        if value:
            # Don't print full secret key
            if 'SECRET' in var or 'PASSWORD' in var:
                print_success(f"{var:20s} = ****** (set)")
            else:
                print_success(f"{var:20s} = {value}")
        else:
            print_warning(f"{var:20s} = (not set)")

    print()
    print_info("Current deployment: LOCALHOST ONLY")
    print_info("To deploy: See DEPLOYMENT-DIAGNOSTIC.md for full guide")


# =============================================================================
# SYSTEM OVERVIEW
# =============================================================================

def check_all():
    """Run all diagnostic checks"""
    print(f"""
{Colors.HEADER}{Colors.BOLD}
╔═══════════════════════════════════════════════════════════════════╗
║     SOULFRA DEPLOYMENT DIAGNOSTIC                                ║
║     Complete System Check                                         ║
╚═══════════════════════════════════════════════════════════════════╝
{Colors.ENDC}
""")

    check_ports()
    check_flask_processes()
    check_ollama()
    check_database()
    check_deployment_status()

    print_header("SUMMARY")

    print_info("Next steps:")
    print("  1. Kill Flask zombies:      python3 deployment_diagnostic.py kill-zombies")
    print("  2. Fix database schema:     python3 deployment_diagnostic.py fix-db")
    print("  3. Start fresh Flask:       python3 app.py")
    print("  4. Start multi-port Ollama: See DEPLOYMENT-DIAGNOSTIC.md")
    print("  5. Deploy to production:    See DEPLOYMENT-DIAGNOSTIC.md")
    print()


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Soulfra Deployment Diagnostic Tool')
    parser.add_argument('command',
                       choices=['check-all', 'check-db', 'fix-db', 'kill-zombies',
                               'check-ports', 'check-ollama'],
                       help='Diagnostic command to run')

    args = parser.parse_args()

    if args.command == 'check-all':
        check_all()
    elif args.command == 'check-db':
        check_database()
    elif args.command == 'fix-db':
        fix_database()
    elif args.command == 'kill-zombies':
        kill_flask_zombies()
    elif args.command == 'check-ports':
        check_ports()
    elif args.command == 'check-ollama':
        check_ollama()

    return 0


if __name__ == '__main__':
    sys.exit(main())
