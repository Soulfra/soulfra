#!/usr/bin/env python3
"""
CalRiven Post Script - AI posts through the platform (dogfooding)

Instead of SQL-injecting posts, CalRiven uses the same posting mechanism
as human users. This ensures:
- Posts are validated the same way
- Platform features are used (not bypassed)
- AI follows the same rules as humans
- Transparent, auditable posting process

Usage:
    python calriven_post.py --title "My Post Title" --slug "my-post-slug" --content "Post content in markdown"

Or use as module:
    from calriven_post import create_ai_post
    create_ai_post(ai_username='calriven', title='...', slug='...', content='...')
"""

import argparse
import sys
from datetime import datetime
import markdown2
from database import get_db, add_post
from db_helpers import get_user_by_username


def create_ai_post(ai_username, title, slug, content_markdown, category=None, tags=None):
    """
    Create a post from an AI persona using the platform's normal posting flow

    Args:
        ai_username (str): AI persona username ('calriven', 'soulfra', 'deathtodata', 'theauditor')
        title (str): Post title
        slug (str): URL-safe slug
        content_markdown (str): Post content in Markdown
        category (str, optional): Category slug
        tags (list, optional): List of tag names

    Returns:
        dict: Created post data, or None if failed
    """

    # Get AI user
    ai_user = get_user_by_username(ai_username)

    if not ai_user:
        print(f"❌ AI user '{ai_username}' not found in database")
        return None

    if not ai_user['is_ai_persona']:
        print(f"❌ User '{ai_username}' is not marked as AI persona")
        return None

    # Convert markdown to HTML (same as platform does)
    content_html = markdown2.markdown(
        content_markdown,
        extras=['fenced-code-blocks', 'tables', 'break-on-newline']
    )

    # Create post using platform's add_post function
    try:
        post_id = add_post(
            user_id=ai_user['id'],
            title=title,
            slug=slug,
            content=content_html,
            published_at=datetime.now()
        )

        print(f"✅ Post created by {ai_username}: '{title}'")
        print(f"   Post ID: {post_id}")
        print(f"   Slug: {slug}")
        print(f"   URL: http://localhost:5001/post/{slug}")

        # Add category if specified
        if category:
            from db_helpers import add_post_category
            try:
                add_post_category(post_id, category)
                print(f"   Category: {category}")
            except Exception as e:
                print(f"   ⚠️  Could not add category '{category}': {e}")

        # Add tags if specified
        if tags:
            from db_helpers import add_post_tag
            for tag in tags:
                try:
                    add_post_tag(post_id, tag)
                    print(f"   Tag: #{tag}")
                except Exception as e:
                    print(f"   ⚠️  Could not add tag '{tag}': {e}")

        # Get created post data
        conn = get_db()
        post = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
        conn.close()

        return dict(post) if post else None

    except Exception as e:
        print(f"❌ Error creating post: {e}")
        return None


def create_ai_comment(ai_username, post_slug, content_markdown, parent_comment_id=None):
    """
    Create a comment from an AI persona

    Args:
        ai_username (str): AI persona username
        post_slug (str): Post slug to comment on
        content_markdown (str): Comment content in Markdown
        parent_comment_id (int, optional): Parent comment ID for replies

    Returns:
        int: Comment ID, or None if failed
    """

    from database import get_post_by_slug
    from db_helpers import add_comment

    # Get AI user
    ai_user = get_user_by_username(ai_username)

    if not ai_user:
        print(f"❌ AI user '{ai_username}' not found")
        return None

    # Get post
    post = get_post_by_slug(post_slug)

    if not post:
        print(f"❌ Post with slug '{post_slug}' not found")
        return None

    # Convert markdown to HTML
    content_html = markdown2.markdown(
        content_markdown,
        extras=['fenced-code-blocks', 'tables', 'break-on-newline']
    )

    # Add comment using platform's add_comment function
    try:
        comment_id = add_comment(
            post_id=post['id'],
            user_id=ai_user['id'],
            content=content_html,
            parent_comment_id=parent_comment_id
        )

        print(f"✅ Comment created by {ai_username} on '{post['title']}'")
        print(f"   Comment ID: {comment_id}")
        print(f"   URL: http://localhost:5001/post/{post_slug}")

        return comment_id

    except Exception as e:
        print(f"❌ Error creating comment: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description='CalRiven Post Script - AI posts through the platform',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a post
  python calriven_post.py --title "New Feature" --slug "new-feature" --content "This is my post"

  # Create a post with category and tags
  python calriven_post.py --title "Security Update" --slug "security-update" \\
      --content "Security improvements" --category "announcement" --tags "security,important"

  # Create a post from a different AI
  python calriven_post.py --ai "soulfra" --title "Privacy Analysis" --slug "privacy-analysis" \\
      --content "Privacy review of new feature"

  # Create a comment
  python calriven_post.py --comment --post-slug "foundation-lock-in" --content "Great work!"
        """
    )

    parser.add_argument('--ai', default='calriven',
                       help='AI username (default: calriven)')

    parser.add_argument('--title', help='Post title')
    parser.add_argument('--slug', help='Post slug (URL-safe)')
    parser.add_argument('--content', help='Post/comment content (markdown)')
    parser.add_argument('--content-file', help='Read content from file')

    parser.add_argument('--category', help='Post category')
    parser.add_argument('--tags', help='Comma-separated tags')

    parser.add_argument('--comment', action='store_true',
                       help='Create comment instead of post')
    parser.add_argument('--post-slug', help='Post slug to comment on (for --comment)')
    parser.add_argument('--parent-id', type=int, help='Parent comment ID (for replies)')

    args = parser.parse_args()

    # Get content
    content = args.content

    if args.content_file:
        try:
            with open(args.content_file, 'r') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ Error reading content file: {e}")
            sys.exit(1)

    if not content:
        print("❌ Content required (--content or --content-file)")
        parser.print_help()
        sys.exit(1)

    # Create comment or post
    if args.comment:
        if not args.post_slug:
            print("❌ --post-slug required for comments")
            sys.exit(1)

        result = create_ai_comment(
            ai_username=args.ai,
            post_slug=args.post_slug,
            content_markdown=content,
            parent_comment_id=args.parent_id
        )

        if not result:
            sys.exit(1)

    else:
        if not args.title or not args.slug:
            print("❌ --title and --slug required for posts")
            parser.print_help()
            sys.exit(1)

        tags = args.tags.split(',') if args.tags else None

        result = create_ai_post(
            ai_username=args.ai,
            title=args.title,
            slug=args.slug,
            content_markdown=content,
            category=args.category,
            tags=tags
        )

        if not result:
            sys.exit(1)


if __name__ == '__main__':
    main()
