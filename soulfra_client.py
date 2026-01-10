#!/usr/bin/env python3
"""
Soulfra Python Client Library

Programmatic access to Soulfra ghost writing platform.

Installation:
    # Copy this file to your project
    # Or install as package: pip install soulfra-client (future)

Usage:
    from soulfra_client import Soulfra

    # Initialize client
    client = Soulfra(
        api_key="sk-abc123...",
        base_url="https://myblog.com"  # or http://localhost:5001
    )

    # Create post
    post = client.create_post(
        brand="mybrand",
        title="How to Use Neural Networks",
        content="A comprehensive guide to...",
        auto_publish=True
    )

    # Generate post with AI
    post = client.generate_post(
        brand="mybrand",
        topic="blockchain technology",
        auto_publish=True
    )

    # List posts
    posts = client.list_posts(brand="mybrand", limit=10)

    # Batch import from list
    posts_data = [
        {"title": "Post 1", "content": "...", "brand": "mybrand"},
        {"title": "Post 2", "content": "...", "brand": "mybrand"},
    ]
    results = client.batch_create_posts(posts_data)

    # Train neural network
    client.train_network(brand="mybrand", topics=["AI", "ML"])
"""

import requests
from typing import List, Dict, Optional
import time

class SoulframaClient:
    """Python client for Soulfra API"""

    def __init__(self, api_key: str, base_url: str = "http://localhost:5001"):
        """
        Initialize Soulfra client

        Args:
            api_key: Your API key (from license_manager.py)
            base_url: Soulfra instance URL
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'X-API-Key': api_key,
            'Content-Type': 'application/json'
        })

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make API request with error handling"""

        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                raise ValueError("Invalid API key")
            elif response.status_code == 429:
                raise ValueError("Rate limit exceeded")
            elif response.status_code == 404:
                raise ValueError(f"Not found: {endpoint}")
            else:
                raise Exception(f"API error: {response.status_code} - {response.text}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Connection error: {e}")

    # ==================== POSTS ====================

    def create_post(
        self,
        brand: str,
        title: str,
        content: str,
        tags: Optional[List[str]] = None,
        auto_publish: bool = True
    ) -> Dict:
        """
        Create a new blog post

        Args:
            brand: Brand slug
            title: Post title
            content: Post content (markdown or HTML)
            tags: List of tags
            auto_publish: Publish immediately (default: True)

        Returns:
            Dict with post data including ID and URL
        """

        data = {
            "title": title,
            "content": content,
            "tags": tags or [],
            "auto_publish": auto_publish
        }

        return self._request('POST', f"/api/v1/{brand}/posts", json=data)

    def list_posts(
        self,
        brand: str,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict]:
        """
        List posts for a brand

        Args:
            brand: Brand slug
            limit: Number of posts to return
            offset: Pagination offset

        Returns:
            List of post dictionaries
        """

        params = {"limit": limit, "offset": offset}
        return self._request('GET', f"/api/v1/{brand}/posts", params=params)

    def get_post(self, brand: str, post_id: int) -> Dict:
        """Get a specific post by ID"""
        return self._request('GET', f"/api/v1/{brand}/posts/{post_id}")

    def update_post(
        self,
        brand: str,
        post_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict:
        """Update an existing post"""

        data = {}
        if title:
            data['title'] = title
        if content:
            data['content'] = content
        if tags:
            data['tags'] = tags

        return self._request('PUT', f"/api/v1/{brand}/posts/{post_id}", json=data)

    def delete_post(self, brand: str, post_id: int) -> Dict:
        """Delete a post"""
        return self._request('DELETE', f"/api/v1/{brand}/posts/{post_id}")

    # ==================== AI GENERATION ====================

    def generate_post(
        self,
        brand: str,
        topic: str,
        auto_publish: bool = True,
        length: str = "medium"
    ) -> Dict:
        """
        Generate post using AI

        Args:
            brand: Brand slug
            topic: Topic to write about
            auto_publish: Publish immediately
            length: "short" (300 words), "medium" (500 words), or "long" (1000 words)

        Returns:
            Dict with generated post
        """

        data = {
            "topic": topic,
            "auto_publish": auto_publish,
            "length": length
        }

        return self._request('POST', f"/api/v1/{brand}/generate", json=data)

    def classify_post(self, brand: str, post_id: int) -> Dict:
        """
        Classify post using neural network

        Returns:
            Dict with topic classifications and confidence scores
        """
        return self._request('GET', f"/api/v1/{brand}/classify/{post_id}")

    # ==================== BATCH OPERATIONS ====================

    def batch_create_posts(self, posts: List[Dict], delay: float = 1.0) -> List[Dict]:
        """
        Create multiple posts with rate limiting

        Args:
            posts: List of post dicts with title, content, brand
            delay: Delay between requests in seconds

        Returns:
            List of results for each post
        """

        results = []

        for post in posts:
            try:
                brand = post.get('brand')
                if not brand:
                    results.append({"error": "Missing brand"})
                    continue

                result = self.create_post(
                    brand=brand,
                    title=post.get('title'),
                    content=post.get('content'),
                    tags=post.get('tags'),
                    auto_publish=post.get('auto_publish', True)
                )

                results.append({"success": True, "post": result})

            except Exception as e:
                results.append({"success": False, "error": str(e)})

            # Rate limiting
            time.sleep(delay)

        return results

    # ==================== NEURAL NETWORKS ====================

    def train_network(self, brand: str, topics: List[str]) -> Dict:
        """
        Train neural network on specific topics

        Args:
            brand: Brand slug
            topics: List of topics to train on

        Returns:
            Dict with training results
        """

        data = {"topics": topics}
        return self._request('POST', f"/api/v1/{brand}/train", json=data)

    def get_network_stats(self, brand: str) -> Dict:
        """Get neural network statistics for brand"""
        return self._request('GET', f"/api/v1/{brand}/network/stats")

    # ==================== ANALYTICS ====================

    def get_analytics(self, brand: str, days: int = 30) -> Dict:
        """
        Get analytics for brand

        Args:
            brand: Brand slug
            days: Number of days to analyze

        Returns:
            Dict with views, subscribers, top posts, etc.
        """

        params = {"days": days}
        return self._request('GET', f"/api/v1/{brand}/analytics", params=params)

    # ==================== SUBSCRIBERS ====================

    def add_subscriber(self, brand: str, email: str) -> Dict:
        """Add subscriber to newsletter"""

        data = {"email": email}
        return self._request('POST', f"/api/v1/{brand}/subscribers", json=data)

    def list_subscribers(self, brand: str) -> List[Dict]:
        """List all subscribers for brand"""
        return self._request('GET', f"/api/v1/{brand}/subscribers")

    # ==================== EXPORT/IMPORT ====================

    def export_brand(self, brand: str) -> Dict:
        """
        Export brand data (config, posts, neural networks)

        Returns:
            Dict with download URL
        """
        return self._request('GET', f"/api/v1/{brand}/export")

    def import_brand(self, brand: str, data: Dict) -> Dict:
        """Import brand data from export"""
        return self._request('POST', f"/api/v1/{brand}/import", json=data)


# Convenience wrapper
Soulfra = SoulframaClient


# ==================== EXAMPLES ====================

if __name__ == "__main__":
    """Example usage"""

    # Initialize client
    client = Soulfra(
        api_key="sk-test-key",
        base_url="http://localhost:5001"
    )

    print("Soulfra Python Client Examples\n")

    # Example 1: Create post
    print("1. Create post")
    try:
        post = client.create_post(
            brand="mybrand",
            title="Test Post from Python Client",
            content="This post was created using the Soulfra Python client library.",
            tags=["test", "api"],
            auto_publish=True
        )
        print(f"   ✓ Created post #{post['id']}: {post['url']}\n")
    except Exception as e:
        print(f"   ✗ Error: {e}\n")

    # Example 2: Generate post with AI
    print("2. Generate post with AI")
    try:
        post = client.generate_post(
            brand="mybrand",
            topic="neural networks",
            auto_publish=False
        )
        print(f"   ✓ Generated: {post['title']}\n")
    except Exception as e:
        print(f"   ✗ Error: {e}\n")

    # Example 3: List posts
    print("3. List posts")
    try:
        posts = client.list_posts(brand="mybrand", limit=5)
        print(f"   ✓ Found {len(posts)} posts:")
        for post in posts[:3]:
            print(f"      • {post['title']}")
        print()
    except Exception as e:
        print(f"   ✗ Error: {e}\n")

    # Example 4: Batch create
    print("4. Batch create posts")
    try:
        posts_data = [
            {
                "brand": "mybrand",
                "title": f"Batch Post {i}",
                "content": f"This is batch post number {i}",
                "tags": ["batch", "test"]
            }
            for i in range(1, 4)
        ]

        results = client.batch_create_posts(posts_data, delay=0.5)
        success_count = sum(1 for r in results if r.get('success'))
        print(f"   ✓ Created {success_count}/{len(posts_data)} posts\n")
    except Exception as e:
        print(f"   ✗ Error: {e}\n")

    print("Done! See soulfra_client.py for more examples.")
