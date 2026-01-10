#!/usr/bin/env python3

"""
API DEBUG HELPER
Queries external APIs (Stack Overflow, GitHub, etc.) to help debug issues
No API keys needed for most functions!
"""

import requests
import json
from datetime import datetime

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

def search_stackoverflow(query, tags=None):
    """
    Search Stack Overflow for solutions
    No API key needed for basic searches!
    """
    print_header(f"STACK OVERFLOW: {query}")

    url = "https://api.stackexchange.com/2.3/search/advanced"

    params = {
        'order': 'desc',
        'sort': 'relevance',
        'q': query,
        'site': 'stackoverflow',
        'pagesize': 5
    }

    if tags:
        params['tagged'] = ';'.join(tags)

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if 'items' in data and data['items']:
            print(f"{GREEN}Found {len(data['items'])} results:{NC}\n")

            for i, item in enumerate(data['items'], 1):
                print(f"{BLUE}#{i}: {item['title']}{NC}")
                print(f"   Score: {item.get('score', 0)} | Answers: {item.get('answer_count', 0)}")
                print(f"   Link: {item['link']}")
                print(f"   Tags: {', '.join(item.get('tags', []))}")

                if item.get('is_answered'):
                    print(f"   {GREEN}✅ Has accepted answer{NC}")

                print()
        else:
            print(f"{YELLOW}No results found{NC}\n")

    except Exception as e:
        print(f"{RED}Error: {e}{NC}\n")

def search_github_issues(query, repo=None):
    """
    Search GitHub issues and discussions
    No API key needed for public repos!
    """
    print_header(f"GITHUB ISSUES: {query}")

    url = "https://api.github.com/search/issues"

    # Build search query
    search_query = query
    if repo:
        search_query += f" repo:{repo}"

    params = {
        'q': search_query,
        'per_page': 5,
        'sort': 'relevance'
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if 'items' in data and data['items']:
            print(f"{GREEN}Found {len(data['items'])} issues:{NC}\n")

            for i, item in enumerate(data['items'], 1):
                state_color = GREEN if item['state'] == 'closed' else YELLOW
                state_icon = '✅' if item['state'] == 'closed' else '🔓'

                print(f"{BLUE}#{i}: {item['title']}{NC}")
                print(f"   State: {state_color}{state_icon} {item['state']}{NC}")
                print(f"   Link: {item['html_url']}")
                print(f"   Comments: {item.get('comments', 0)}")

                if 'labels' in item:
                    labels = [label['name'] for label in item['labels']]
                    if labels:
                        print(f"   Labels: {', '.join(labels[:3])}")

                print()
        else:
            print(f"{YELLOW}No results found{NC}\n")

    except Exception as e:
        print(f"{RED}Error: {e}{NC}\n")

def search_github_code(query, language=None):
    """
    Search GitHub code repositories
    Find actual implementation examples!
    """
    print_header(f"GITHUB CODE: {query}")

    url = "https://api.github.com/search/code"

    search_query = query
    if language:
        search_query += f" language:{language}"

    params = {
        'q': search_query,
        'per_page': 5
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if 'items' in data and data['items']:
            print(f"{GREEN}Found {len(data['items'])} code examples:{NC}\n")

            for i, item in enumerate(data['items'], 1):
                print(f"{BLUE}#{i}: {item['name']}{NC}")
                print(f"   Repo: {item['repository']['full_name']}")
                print(f"   Path: {item['path']}")
                print(f"   Link: {item['html_url']}")
                print()
        else:
            print(f"{YELLOW}No results found{NC}\n")

    except Exception as e:
        print(f"{RED}Error: {e}{NC}\n")

def check_pypi_package(package_name):
    """
    Check PyPI for package info, versions, documentation
    """
    print_header(f"PyPI PACKAGE: {package_name}")

    url = f"https://pypi.org/pypi/{package_name}/json"

    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        info = data['info']

        print(f"{GREEN}Package found!{NC}\n")
        print(f"Name:        {info['name']}")
        print(f"Version:     {info['version']}")
        print(f"Summary:     {info['summary']}")
        print(f"Author:      {info.get('author', 'N/A')}")
        print(f"License:     {info.get('license', 'N/A')}")
        print(f"Home:        {info.get('home_page', 'N/A')}")
        print(f"PyPI:        https://pypi.org/project/{package_name}/")

        if 'docs_url' in info and info['docs_url']:
            print(f"Docs:        {info['docs_url']}")

        print()

        # Show install command
        print(f"{BLUE}Install:{NC}")
        print(f"  pip3 install {package_name}")
        print()

    except Exception as e:
        print(f"{RED}Package not found or error: {e}{NC}\n")

def search_reddit(query, subreddit=None):
    """
    Search Reddit for community discussions
    No API key needed for read-only!
    """
    print_header(f"REDDIT: {query}")

    # Use Reddit's JSON API (no auth needed for read-only)
    base_url = "https://www.reddit.com"

    if subreddit:
        url = f"{base_url}/r/{subreddit}/search.json"
    else:
        url = f"{base_url}/search.json"

    params = {
        'q': query,
        'limit': 5,
        'sort': 'relevance'
    }

    if subreddit:
        params['restrict_sr'] = 'on'

    try:
        # Reddit requires a user agent
        headers = {'User-Agent': 'python:debug-helper:v1.0'}
        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = response.json()

        if 'data' in data and 'children' in data['data']:
            posts = data['data']['children']

            if posts:
                print(f"{GREEN}Found {len(posts)} posts:{NC}\n")

                for i, post in enumerate(posts, 1):
                    p = post['data']
                    print(f"{BLUE}#{i}: {p['title']}{NC}")
                    print(f"   Subreddit: r/{p['subreddit']}")
                    print(f"   Score: {p['score']} | Comments: {p['num_comments']}")
                    print(f"   Link: https://reddit.com{p['permalink']}")
                    print()
            else:
                print(f"{YELLOW}No results found{NC}\n")
        else:
            print(f"{YELLOW}No results found{NC}\n")

    except Exception as e:
        print(f"{RED}Error: {e}{NC}\n")

def debug_common_issues():
    """
    Search for solutions to common issues we're seeing
    """
    print()
    print(f"{CYAN}{'='*80}{NC}")
    print(f"{CYAN}  🔍 API DEBUG HELPER - Common Issues{NC}")
    print(f"{CYAN}  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{NC}")
    print(f"{CYAN}{'='*80}{NC}")

    # Issue 1: Ollama network access
    search_stackoverflow("ollama network access localhost 0.0.0.0", tags=['networking', 'localhost'])

    # Issue 2: Flask network binding
    search_stackoverflow("flask bind 0.0.0.0 allow network connections", tags=['flask', 'python'])

    # Issue 3: GitHub Pages custom domain
    search_github_issues("custom domain CNAME not working", repo="github/docs")

    # Issue 4: BeautifulSoup XML parsing
    check_pypi_package("lxml")

    # Issue 5: SSH tunneling
    search_stackoverflow("ssh tunnel port forwarding local network", tags=['ssh', 'networking'])

    print_header("SUMMARY")
    print("Searched multiple APIs for solutions to common issues!")
    print()
    print("You can also run individual functions:")
    print(f"  python3 -c 'from api_debug_helper import *; search_stackoverflow(\"your query\")'")
    print()

def custom_search(query):
    """
    Run a custom search across multiple platforms
    """
    print()
    print(f"{CYAN}{'='*80}{NC}")
    print(f"{CYAN}  🔍 SEARCHING: {query}{NC}")
    print(f"{CYAN}{'='*80}{NC}")

    search_stackoverflow(query)
    search_github_issues(query)
    search_reddit(query, subreddit='selfhosted')

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # Custom search from command line
        query = ' '.join(sys.argv[1:])
        custom_search(query)
    else:
        # Debug common issues
        debug_common_issues()
