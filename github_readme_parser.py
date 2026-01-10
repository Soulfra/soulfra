"""
GitHub README → Wordmap Parser
Fetches README.md from GitHub repos and extracts wordmap
"""
import requests
import re
from database import get_db

def fetch_github_readme(owner, repo, branch='main'):
    """
    Fetch README.md from GitHub repo

    Args:
        owner: GitHub username/org (e.g., 'Soulfra')
        repo: Repository name (e.g., 'soulfra')
        branch: Branch name (default: 'main')

    Returns:
        README.md content as string, or None if not found
    """
    # Try main branch first, then master
    for branch_name in [branch, 'master', 'main']:
        url = f'https://raw.githubusercontent.com/{owner}/{repo}/{branch_name}/README.md'

        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.text
        except requests.RequestException as e:
            print(f"Error fetching README from {url}: {e}")
            continue

    return None

def parse_readme_to_wordmap(readme_text):
    """
    Extract wordmap from README.md text

    Returns:
        Dict of {word: count}
    """
    if not readme_text:
        return {}

    # Remove markdown syntax
    text = readme_text

    # Remove code blocks
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`[^`]+`', '', text)

    # Remove URLs
    text = re.sub(r'https?://\S+', '', text)

    # Remove markdown formatting
    text = re.sub(r'[#*_\[\]()]+', ' ', text)

    # Convert to lowercase
    text = text.lower()

    # Remove punctuation and split into words
    words = re.findall(r'\b[a-z]{3,}\b', text)  # Only words 3+ chars

    # Count frequencies
    wordmap = {}
    for word in words:
        # Skip common words
        if word in ['the', 'and', 'for', 'are', 'but', 'not', 'you', 'all',
                   'can', 'her', 'was', 'one', 'our', 'out', 'day', 'get',
                   'has', 'him', 'his', 'how', 'man', 'new', 'now', 'old',
                   'see', 'two', 'way', 'who', 'boy', 'did', 'its', 'let',
                   'put', 'say', 'she', 'too', 'use', 'with', 'from', 'have',
                   'this', 'that', 'will', 'your', 'there', 'about', 'than',
                   'into', 'them', 'these', 'would', 'could', 'where', 'which']:
            continue

        wordmap[word] = wordmap.get(word, 0) + 1

    return wordmap

def update_domain_wordmap_from_github(domain_name, github_owner, github_repo):
    """
    Fetch README from GitHub and update domain_wordmaps table

    Args:
        domain_name: Domain to update (e.g., 'soulfra')
        github_owner: GitHub owner (e.g., 'Soulfra')
        github_repo: Repository name (e.g., 'soulfra')

    Returns:
        Dict with success status and wordmap
    """
    # Fetch README
    readme = fetch_github_readme(github_owner, github_repo)

    if not readme:
        return {
            'success': False,
            'error': f'Could not fetch README from github.com/{github_owner}/{github_repo}'
        }

    # Parse to wordmap
    wordmap = parse_readme_to_wordmap(readme)

    if not wordmap:
        return {
            'success': False,
            'error': 'No valid words found in README'
        }

    # Store in database
    db = get_db()

    # Store wordmap as JSON
    import json
    wordmap_json = json.dumps(wordmap)

    # Check if entry exists (using existing schema: domain as primary key)
    existing = db.execute(
        'SELECT domain FROM domain_wordmaps WHERE domain = ?',
        (domain_name,)
    ).fetchone()

    if existing:
        # Update existing
        db.execute('''
            UPDATE domain_wordmaps
            SET wordmap_json = ?, last_updated = CURRENT_TIMESTAMP
            WHERE domain = ?
        ''', (wordmap_json, domain_name))
    else:
        # Insert new
        db.execute('''
            INSERT INTO domain_wordmaps (domain, wordmap_json, contributor_count, total_recordings)
            VALUES (?, ?, 0, 0)
        ''', (domain_name, wordmap_json))

    db.commit()

    # Get top words
    top_words = sorted(wordmap.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        'success': True,
        'domain': domain_name,
        'github': f'{github_owner}/{github_repo}',
        'total_words': sum(wordmap.values()),
        'unique_words': len(wordmap),
        'top_words': [{'word': word, 'count': count} for word, count in top_words],
        'source': 'github_readme'
    }

def get_domain_wordmap(domain_name):
    """
    Get wordmap for a domain from database

    Returns:
        Dict with wordmap data
    """
    db = get_db()

    try:
        result = db.execute('''
            SELECT wordmap_json, last_updated
            FROM domain_wordmaps
            WHERE domain = ?
        ''', (domain_name,)).fetchone()

        if not result:
            return {'error': 'No wordmap found for domain'}

        import json
        wordmap = json.loads(result['wordmap_json'])
        top_words = sorted(wordmap.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            'domain': domain_name,
            'total_words': sum(wordmap.values()),
            'unique_words': len(wordmap),
            'top_words': [{'word': w, 'count': c} for w, c in top_words],
            'source': 'github_readme',
            'last_updated': result['last_updated']
        }
    except Exception as e:
        return {'error': str(e)}
