#!/usr/bin/env python3
"""
Content Pipeline - Complete File Processing Flow

**The Complete Pipeline:**
1. **Validate** - Check format, size, content quality
2. **Convert** - Normalize to markdown (file_importer.py)
3. **Enrich** - Add metadata, extract tags, generate summaries
4. **Route** - Assign @brand/category path (folder_router.py)
5. **Database** - Save to posts and file_routes tables
6. **Generate** - QR codes, thumbnails, pSEO pages
7. **Export** - Static HTML site, API endpoints

**Flow Diagram:**
```
Upload File
    ↓
Validate (size, format, content)
    ↓
Convert to Markdown (file_importer)
    ↓
Enrich Metadata (Ollama summary, tags, images)
    ↓
Route (@brand/category via folder_router)
    ↓
Save to Database (posts, file_routes)
    ↓
Generate Artifacts (QR, thumbnails, pSEO)
    ↓
Export Static Site
    ↓
Return Success + URLs
```

**Usage:**
```python
from content_pipeline import ContentPipeline

pipeline = ContentPipeline()

# Process a file
result = pipeline.process_file(
    file_path='uploads/privacy-guide.md',
    brand='soulfra',
    category='blog',
    user_id=15
)

# Returns:
{
    'success': True,
    'route': '@soulfra/blog/privacy-guide',
    'url': 'https://soulfra.com/blog/privacy-guide',
    'qr_code': '/static/qr/privacy-guide.png',
    'pseo_pages': 50,
    'static_export': '/output/soulfra/blog/privacy-guide.html'
}
```
"""

import os
import re
import json
import shutil
import requests
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Import our modules
from file_importer import FileImporter
from folder_router import FolderRouter


# ==============================================================================
# CONFIG
# ==============================================================================

OLLAMA_HOST = os.environ.get('OLLAMA_HOST', 'http://localhost:11434')
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'llama2')

OUTPUT_DIR = os.environ.get('OUTPUT_DIR', './output')
STATIC_DIR = os.environ.get('STATIC_DIR', './static')

# Generation settings
PSEO_ENABLED = os.environ.get('PSEO_ENABLED', 'true').lower() == 'true'
QR_ENABLED = os.environ.get('QR_ENABLED', 'true').lower() == 'true'
STATIC_EXPORT_ENABLED = os.environ.get('STATIC_EXPORT', 'true').lower() == 'true'


# ==============================================================================
# CONTENT PIPELINE CLASS
# ==============================================================================

class ContentPipeline:
    """
    Complete content processing pipeline
    """

    def __init__(
        self,
        ollama_host: str = OLLAMA_HOST,
        model: str = OLLAMA_MODEL
    ):
        self.ollama_host = ollama_host
        self.model = model

        # Initialize components
        self.importer = FileImporter()
        self.router = FolderRouter()

        # Output directories
        self.output_dir = Path(OUTPUT_DIR)
        self.static_dir = Path(STATIC_DIR)

        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.static_dir.mkdir(parents=True, exist_ok=True)


    # ==========================================================================
    # MAIN PIPELINE
    # ==========================================================================

    def process_file(
        self,
        file_path: str,
        brand: str,
        category: str,
        user_id: int,
        subcategory: Optional[str] = None,
        skip_validation: bool = False
    ) -> Dict:
        """
        Process file through complete pipeline

        Args:
            file_path: Path to uploaded file
            brand: Brand name
            category: Category
            user_id: Owner user ID
            subcategory: Optional subcategory
            skip_validation: Skip validation step

        Returns:
            Dict with processing results

        Example:
            >>> pipeline = ContentPipeline()
            >>> result = pipeline.process_file(
            ...     file_path='uploads/post.md',
            ...     brand='soulfra',
            ...     category='blog',
            ...     user_id=15
            ... )
        """
        pipeline_result = {
            'success': False,
            'steps': {},
            'errors': []
        }

        try:
            # Step 1: Validate
            if not skip_validation:
                validation = self._validate_file(file_path)
                pipeline_result['steps']['validate'] = validation

                if not validation['valid']:
                    pipeline_result['errors'] = validation['errors']
                    return pipeline_result

            # Step 2: Import and Convert
            import_result = self.importer.import_file(
                file_path=file_path,
                brand=brand,
                category=category,
                user_id=user_id,
                subcategory=subcategory
            )

            pipeline_result['steps']['import'] = import_result
            pipeline_result['route'] = import_result['route']
            pipeline_result['file_id'] = import_result['file_id']

            # Step 3: Enrich
            enrichment = self._enrich_content(
                file_path=import_result['brand_file_path'],
                metadata=import_result['metadata']
            )

            pipeline_result['steps']['enrich'] = enrichment
            pipeline_result['metadata'] = enrichment['metadata']

            # Step 4: Generate Artifacts
            if QR_ENABLED:
                qr_result = self._generate_qr_code(
                    route=import_result['route'],
                    filename=import_result['metadata'].get('slug', 'file')
                )
                pipeline_result['steps']['qr'] = qr_result
                pipeline_result['qr_code'] = qr_result.get('qr_path', '')

            # Step 5: Generate pSEO Pages
            if PSEO_ENABLED:
                pseo_result = self._generate_pseo_pages(
                    route=import_result['route'],
                    content_path=import_result['brand_file_path'],
                    metadata=enrichment['metadata']
                )
                pipeline_result['steps']['pseo'] = pseo_result
                pipeline_result['pseo_pages'] = pseo_result.get('pages_generated', 0)

            # Step 6: Export Static Site
            if STATIC_EXPORT_ENABLED:
                export_result = self._export_static_site(
                    route=import_result['route'],
                    content_path=import_result['brand_file_path'],
                    metadata=enrichment['metadata']
                )
                pipeline_result['steps']['export'] = export_result
                pipeline_result['static_export'] = export_result.get('export_path', '')

            # Mark as success
            pipeline_result['success'] = True
            pipeline_result['url'] = import_result['url']

            return pipeline_result

        except Exception as e:
            pipeline_result['errors'].append(str(e))
            return pipeline_result


    # ==========================================================================
    # STEP 1: VALIDATION
    # ==========================================================================

    def _validate_file(self, file_path: str) -> Dict:
        """
        Validate file before processing

        Args:
            file_path: Path to file

        Returns:
            Dict with validation results
        """
        errors = []
        warnings = []

        file_path = Path(file_path)

        # Check file exists
        if not file_path.exists():
            errors.append(f"File not found: {file_path}")
            return {'valid': False, 'errors': errors}

        # Check file size
        file_size = file_path.stat().st_size
        max_size = 10 * 1024 * 1024  # 10 MB

        if file_size == 0:
            errors.append("File is empty")

        if file_size > max_size:
            errors.append(f"File too large: {file_size} bytes (max {max_size})")

        # Check format
        extension = file_path.suffix.lstrip('.').lower()
        supported = ['txt', 'md', 'mdx', 'html', 'htm', 'doc', 'docx', 'json', 'yaml', 'csv']

        if extension not in supported:
            warnings.append(f"Unusual format: {extension}")

        # Read file to check encoding
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(1000)  # Read first 1KB

            # Check for minimum content
            if len(content.strip()) < 10:
                warnings.append("File has very little content")

        except UnicodeDecodeError:
            errors.append("File encoding error (not UTF-8)")
        except Exception as e:
            errors.append(f"Error reading file: {e}")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'file_size': file_size,
            'format': extension
        }


    # ==========================================================================
    # STEP 3: ENRICHMENT
    # ==========================================================================

    def _enrich_content(self, file_path: str, metadata: Dict) -> Dict:
        """
        Enrich content with AI-generated metadata

        Args:
            file_path: Path to content file
            metadata: Existing metadata

        Returns:
            Dict with enrichment results
        """
        file_path = Path(file_path)

        # Read content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        enriched_metadata = metadata.copy()

        # Generate summary if missing
        if 'summary' not in enriched_metadata or 'description' not in enriched_metadata:
            summary = self._generate_summary(content)
            enriched_metadata['summary'] = summary
            enriched_metadata['description'] = summary[:200]  # Truncate for meta desc

        # Extract tags if missing
        if 'tags' not in enriched_metadata:
            tags = self._extract_tags(content)
            enriched_metadata['tags'] = tags

        # Count words
        word_count = len(content.split())
        enriched_metadata['word_count'] = word_count

        # Estimate reading time (average 200 words per minute)
        reading_time = max(1, word_count // 200)
        enriched_metadata['reading_time_minutes'] = reading_time

        return {
            'metadata': enriched_metadata,
            'content_length': len(content),
            'word_count': word_count
        }


    def _generate_summary(self, content: str, max_length: int = 500) -> str:
        """
        Generate AI summary of content

        Args:
            content: Full content text
            max_length: Max summary length

        Returns:
            Summary string
        """
        # Truncate content for Ollama
        preview = content[:2000]

        prompt = f"""
Summarize this content in 2-3 sentences:

{preview}

Summary:
"""

        try:
            response = self._ask_ollama(prompt)
            # Clean up response
            summary = response.strip()

            # Truncate if needed
            if len(summary) > max_length:
                summary = summary[:max_length] + '...'

            return summary

        except:
            # Fallback: use first paragraph
            paragraphs = content.split('\n\n')
            return paragraphs[0][:max_length] if paragraphs else content[:max_length]


    def _extract_tags(self, content: str) -> List[str]:
        """
        Extract relevant tags from content

        Args:
            content: Content text

        Returns:
            List of tags
        """
        prompt = f"""
Extract 5-10 relevant tags from this content. Return ONLY the tags, comma-separated:

{content[:1000]}

Tags:
"""

        try:
            response = self._ask_ollama(prompt)
            # Parse tags
            tags = [tag.strip() for tag in response.split(',')]
            # Clean and limit
            tags = [tag.lower() for tag in tags if tag and len(tag) < 30]
            return tags[:10]

        except:
            # Fallback: simple word frequency
            words = re.findall(r'\b[a-z]{4,}\b', content.lower())
            from collections import Counter
            common = Counter(words).most_common(10)
            return [word for word, count in common if count > 2]


    # ==========================================================================
    # STEP 4: QR CODE GENERATION
    # ==========================================================================

    def _generate_qr_code(self, route: str, filename: str) -> Dict:
        """
        Generate QR code for route

        Args:
            route: File route
            filename: File slug

        Returns:
            Dict with QR code info
        """
        try:
            import qrcode

            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(route)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            # Save QR code
            qr_dir = self.static_dir / 'qr'
            qr_dir.mkdir(exist_ok=True)

            qr_filename = f'{filename}.png'
            qr_path = qr_dir / qr_filename

            img.save(str(qr_path))

            return {
                'success': True,
                'qr_path': f'/static/qr/{qr_filename}',
                'qr_file': str(qr_path)
            }

        except ImportError:
            return {
                'success': False,
                'error': 'QR code library not available (pip install qrcode)'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


    # ==========================================================================
    # STEP 5: pSEO PAGE GENERATION
    # ==========================================================================

    def _generate_pseo_pages(self, route: str, content_path: str, metadata: Dict) -> Dict:
        """
        Generate programmatic SEO pages

        Args:
            route: File route
            content_path: Path to content
            metadata: Content metadata

        Returns:
            Dict with pSEO results
        """
        # pSEO strategy: Generate variations of the content
        # For example:
        # - /brands/soulfra/blog/privacy
        # - /brands/soulfra/blog/privacy/summary
        # - /brands/soulfra/blog/privacy/tl-dr
        # - /brands/soulfra/blog/privacy/for-beginners

        pages_generated = 0
        pseo_pages = []

        try:
            with open(content_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Generate summary page
            summary_page = self._generate_summary_page(content, metadata)
            if summary_page:
                pseo_pages.append(summary_page)
                pages_generated += 1

            # Generate TL;DR page
            tldr_page = self._generate_tldr_page(content, metadata)
            if tldr_page:
                pseo_pages.append(tldr_page)
                pages_generated += 1

            return {
                'success': True,
                'pages_generated': pages_generated,
                'pages': pseo_pages
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'pages_generated': 0
            }


    def _generate_summary_page(self, content: str, metadata: Dict) -> Optional[str]:
        """Generate a summary version of the page"""
        summary = self._generate_summary(content, max_length=1000)

        page_content = f"""
# Summary: {metadata.get('title', 'Untitled')}

{summary}

[Read full article →]({metadata.get('route', '')})
"""
        return page_content


    def _generate_tldr_page(self, content: str, metadata: Dict) -> Optional[str]:
        """Generate TL;DR version"""
        prompt = f"""
Create a TL;DR (Too Long; Didn't Read) summary of this content in 3-5 bullet points:

{content[:1500]}

TL;DR:
"""

        try:
            tldr = self._ask_ollama(prompt)

            page_content = f"""
# TL;DR: {metadata.get('title', 'Untitled')}

{tldr}

---

[Read full article →]({metadata.get('route', '')})
"""
            return page_content

        except:
            return None


    # ==========================================================================
    # STEP 6: STATIC EXPORT
    # ==========================================================================

    def _export_static_site(self, route: str, content_path: str, metadata: Dict) -> Dict:
        """
        Export content as static HTML

        Args:
            route: File route
            content_path: Path to markdown file
            metadata: Content metadata

        Returns:
            Dict with export results
        """
        try:
            # Parse route
            parsed = self.router.parse_route(route)
            if not parsed:
                return {'success': False, 'error': 'Invalid route'}

            # Create output directory
            export_dir = self.output_dir / parsed['brand']
            if parsed['category']:
                export_dir = export_dir / parsed['category']
            if parsed['subcategory']:
                export_dir = export_dir / parsed['subcategory']

            export_dir.mkdir(parents=True, exist_ok=True)

            # Read markdown
            with open(content_path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()

            # Convert to HTML
            html_content = self._markdown_to_html(markdown_content, metadata)

            # Save HTML
            html_filename = f"{parsed['file']}.html"
            html_path = export_dir / html_filename

            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            return {
                'success': True,
                'export_path': str(html_path),
                'url': f'/output/{parsed["brand"]}/{parsed["category"]}/{html_filename}'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


    def _markdown_to_html(self, markdown: str, metadata: Dict) -> str:
        """
        Convert markdown to HTML with template

        Args:
            markdown: Markdown content
            metadata: Page metadata

        Returns:
            HTML string
        """
        # Try using markdown2 if available
        try:
            import markdown2
            html_body = markdown2.markdown(markdown, extras=['fenced-code-blocks', 'tables'])
        except:
            # Fallback: simple conversion
            html_body = markdown.replace('\n\n', '</p><p>').replace('\n', '<br>')
            html_body = f'<p>{html_body}</p>'

        # Wrap in HTML template
        title = metadata.get('title', 'Untitled')
        description = metadata.get('description', '')

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{description}">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }}
        h1, h2, h3 {{ color: #333; }}
        code {{
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
        }}
        pre {{
            background: #f4f4f4;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }}
    </style>
</head>
<body>
    {html_body}

    <hr>
    <footer>
        <p><small>Generated by Soulfra Content Pipeline</small></p>
    </footer>
</body>
</html>
"""

        return html


    # ==========================================================================
    # OLLAMA INTEGRATION
    # ==========================================================================

    def _ask_ollama(self, prompt: str) -> str:
        """
        Ask Ollama a question

        Args:
            prompt: Prompt text

        Returns:
            Response string
        """
        response = requests.post(
            f'{self.ollama_host}/api/generate',
            json={
                'model': self.model,
                'prompt': prompt,
                'stream': False
            },
            timeout=30
        )

        if response.status_code != 200:
            raise Exception(f"Ollama API error: {response.status_code}")

        return response.json().get('response', '').strip()


# ==============================================================================
# CLI USAGE
# ==============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Content Pipeline')
    parser.add_argument('--process', type=str, help='Process a file')
    parser.add_argument('--brand', type=str, help='Brand name')
    parser.add_argument('--category', type=str, help='Category')
    parser.add_argument('--user-id', type=int, default=1, help='User ID')

    args = parser.parse_args()

    if args.process:
        if not args.brand or not args.category:
            print('Error: --brand and --category required')
            exit(1)

        pipeline = ContentPipeline()

        print(f'\n🚀 Processing: {args.process}\n')

        result = pipeline.process_file(
            file_path=args.process,
            brand=args.brand,
            category=args.category,
            user_id=args.user_id
        )

        if result['success']:
            print('✅ Pipeline completed successfully!\n')
            print(f'   Route: {result.get("route")}')
            print(f'   URL: {result.get("url")}')
            print(f'   QR Code: {result.get("qr_code", "N/A")}')
            print(f'   pSEO Pages: {result.get("pseo_pages", 0)}')
            print(f'   Static Export: {result.get("static_export", "N/A")}\n')
        else:
            print('❌ Pipeline failed!\n')
            for error in result.get('errors', []):
                print(f'   Error: {error}')
            print()

    else:
        print('Usage: python3 content_pipeline.py --process file.md --brand soulfra --category blog')
