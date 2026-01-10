"""
Image Admin Routes - Flask Routes for Professional Image Management

Provides web admin interface for:
- Canvas editor (WYSIWYG)
- Image generation API
- Template management
- QR code management
- Image gallery
"""

from flask import render_template, request, jsonify, send_file
import io
import json
from typing import Dict

from image_workflow import ImageWorkflow, quick_blog_image, quick_social_image, save_generated_image_to_db
from image_composer import ImageComposer
from vanity_qr import create_and_save_vanity_qr, get_vanity_qr, BRAND_DOMAINS
from image_metadata import ImageMetadata
from database import get_db


def register_image_admin_routes(app):
    """Register all image admin routes"""

    # =======================
    # Canvas Editor
    # =======================

    @app.route('/admin/canvas')
    def admin_canvas():
        """Interactive WYSIWYG canvas editor"""
        return render_template('admin/canvas_editor.html')

    # =======================
    # Image Generation API
    # =======================

    @app.route('/api/generate/blog', methods=['POST'])
    def api_generate_blog():
        """
        Generate blog header image

        POST /api/generate/blog
        {
            "title": "Blog Post Title",
            "brand": "cringeproof",
            "url": "https://cringeproof.com/blog/post",
            "keywords": ["keyword1", "keyword2"],
            "author": "Author Name"
        }

        Returns: Binary image data (JPEG)
        """
        data = request.get_json()

        title = data.get('title', 'Untitled')
        brand = data.get('brand', 'soulfra')
        url = data.get('url', 'https://soulfra.com')
        keywords = data.get('keywords', [])
        author = data.get('author')

        # Generate image
        workflow = ImageWorkflow(brand_slug=brand)
        image_bytes = workflow.create_blog_header(
            title=title,
            keywords=keywords,
            url=url,
            author=author
        )

        return send_file(
            io.BytesIO(image_bytes),
            mimetype='image/jpeg',
            as_attachment=True,
            download_name=f'blog_{brand}_{title[:30].replace(" ", "_")}.jpg'
        )

    @app.route('/api/generate/social', methods=['POST'])
    def api_generate_social():
        """
        Generate social media post image

        POST /api/generate/social
        {
            "message": "Social Post Message",
            "brand": "soulfra",
            "url": "https://soulfra.com",
            "style": "bold|minimal|vibrant"
        }

        Returns: Binary image data (JPEG)
        """
        data = request.get_json()

        message = data.get('message', 'Social Post')
        brand = data.get('brand', 'soulfra')
        url = data.get('url', 'https://soulfra.com')
        style = data.get('style', 'bold')

        # Generate image
        workflow = ImageWorkflow(brand_slug=brand)
        image_bytes = workflow.create_social_post(
            message=message,
            url=url,
            style=style
        )

        return send_file(
            io.BytesIO(image_bytes),
            mimetype='image/jpeg',
            as_attachment=True,
            download_name=f'social_{brand}_{style}.jpg'
        )

    @app.route('/api/generate/product', methods=['POST'])
    def api_generate_product():
        """
        Generate product showcase image

        POST /api/generate/product
        {
            "product_name": "Product Name",
            "tagline": "Product Tagline",
            "brand": "cringeproof",
            "url": "https://cringeproof.com/product",
            "features": ["Feature 1", "Feature 2", ...]
        }

        Returns: Binary image data (JPEG)
        """
        data = request.get_json()

        product_name = data.get('product_name', 'Product')
        tagline = data.get('tagline', 'Amazing Product')
        brand = data.get('brand', 'soulfra')
        url = data.get('url', 'https://soulfra.com')
        features = data.get('features', [])

        # Generate image
        workflow = ImageWorkflow(brand_slug=brand)
        image_bytes = workflow.create_product_showcase(
            product_name=product_name,
            tagline=tagline,
            url=url,
            features=features
        )

        return send_file(
            io.BytesIO(image_bytes),
            mimetype='image/jpeg',
            as_attachment=True,
            download_name=f'product_{brand}_{product_name[:30].replace(" ", "_")}.jpg'
        )

    @app.route('/api/generate/custom', methods=['POST'])
    def api_generate_custom():
        """
        Generate custom image from layer composition

        POST /api/generate/custom
        {
            "brand": "soulfra",
            "size": [1200, 630],
            "layers": [
                {"type": "gradient", "colors": ["#FF0000", "#0000FF"], "angle": 45},
                {"type": "text", "content": "Hello", "fontSize": 48, ...},
                ...
            ]
        }

        Returns: Binary image data (PNG)
        """
        def camel_to_snake(name):
            """Convert camelCase to snake_case"""
            import re
            name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
            return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()

        data = request.get_json()

        brand = data.get('brand', 'soulfra')
        size = tuple(data.get('size', [1200, 630]))
        layers = data.get('layers', [])

        # Create composer
        composer = ImageComposer(size=size)

        # Add layers with parameter name conversion
        for layer in layers:
            layer_copy = layer.copy()
            layer_type = layer_copy.pop('type', 'background')

            # Convert camelCase to snake_case for all parameters
            snake_layer = {camel_to_snake(k): v for k, v in layer_copy.items()}

            # Remove parameters that don't belong to the layer (from canvas editor state)
            snake_layer.pop('id', None)
            snake_layer.pop('visible', None)

            # Convert x,y to position tuple for text, shape, and qr layers
            if 'x' in snake_layer and 'y' in snake_layer:
                snake_layer['position'] = (snake_layer.pop('x'), snake_layer.pop('y'))

            # Convert width,height to size tuple for shape layers
            if layer_type == 'shape' and 'width' in snake_layer and 'height' in snake_layer:
                snake_layer['size'] = (snake_layer.pop('width'), snake_layer.pop('height'))

            # Map fill_color and stroke_color for shapes
            if layer_type == 'shape':
                if 'fill_color' in snake_layer:
                    # Already snake_case from conversion
                    pass
                if 'corner_radius' in snake_layer:
                    # Already converted
                    pass

            # Map QR size to a position-based size (QR uses size parameter differently)
            if layer_type == 'qr' and 'size' in snake_layer:
                # QR size stays as-is
                pass

            composer.add_layer(layer_type, **snake_layer)

        # Render
        image_bytes = composer.render()

        # Add metadata
        metadata = ImageMetadata(brand=brand)
        for layer in data.get('layers', []):
            layer_type = layer.get('type', 'unknown')
            metadata.add_layer_data(layer_type, **{k: v for k, v in layer.items() if k != 'type'})

        final_image = metadata.embed_in_image(image_bytes)

        return send_file(
            io.BytesIO(final_image),
            mimetype='image/jpeg',
            as_attachment=True,
            download_name=f'custom_{brand}.jpg'
        )

    @app.route('/api/generate/ai-logo', methods=['POST'])
    def api_generate_ai_logo():
        """
        Generate AI logo using Stable Diffusion

        POST /api/generate/ai-logo
        {
            "brand": "soulfra",
            "description": "futuristic lock with neon glow",
            "size": [512, 512],
            "num_steps": 28
        }

        Returns: Binary PNG image data
        """
        data = request.get_json()

        brand = data.get('brand', 'soulfra')
        description = data.get('description', 'professional logo')
        size = tuple(data.get('size', [512, 512]))
        num_steps = data.get('num_steps', 28)

        try:
            from ai_image_generator import AIImageGenerator

            # Brand color mapping (from brands.json)
            brand_colors_map = {
                'soulfra': {'primary': '#00ffff', 'secondary': '#ff00ff'},
                'deathtodata': {'primary': '#00ff00', 'secondary': '#00cc00'},
                'calriven': {'primary': '#9b59b6', 'secondary': '#8e44ad'},
                'finishthatidea': {'primary': '#e74c3c', 'secondary': '#c0392b'},
                'finishthisrepo': {'primary': '#3498db', 'secondary': '#2980b9'},
                'saveorsink': {'primary': '#1abc9c', 'secondary': '#16a085'},
                'sellthismvp': {'primary': '#f39c12', 'secondary': '#e67e22'},
                'dealordelete': {'primary': '#e91e63', 'secondary': '#c2185b'},
                'mascotrooms': {'primary': '#9c27b0', 'secondary': '#7b1fa2'}
            }

            brand_colors = brand_colors_map.get(brand, brand_colors_map['soulfra'])

            # Initialize generator
            gen = AIImageGenerator()

            if not gen.available:
                return jsonify({
                    'success': False,
                    'error': 'AI image generation not available. Install: pip install diffusers transformers'
                }), 500

            # Enhanced prompt with brand colors
            prompt = f"{description}, professional logo design, clean, {brand_colors['primary']} and {brand_colors['secondary']} color scheme, centered, minimal background, high quality, vector style"

            negative_prompt = "blurry, low quality, distorted, ugly, photo, realistic, 3d render, text, watermark"

            print(f'🎨 Generating AI logo for {brand}: "{description}"')
            print(f'   Size: {size}, Steps: {num_steps}')

            # Generate image
            image_bytes = gen.generate_from_text(
                prompt=prompt,
                brand_colors=[brand_colors['primary'], brand_colors['secondary']],
                size=size,
                negative_prompt=negative_prompt,
                num_steps=num_steps
            )

            print(f'   ✅ Generated ({len(image_bytes):,} bytes)')

            return send_file(
                io.BytesIO(image_bytes),
                mimetype='image/png',
                as_attachment=False,
                download_name=f'ai_logo_{brand}_{description[:20].replace(" ", "_")}.png'
            )

        except Exception as e:
            print(f'   ❌ Generation failed: {e}')
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/generate/comic', methods=['POST'])
    def api_generate_comic():
        """
        Generate comic-style image using procedural generation

        POST /api/generate/comic
        {
            "keywords": ["cooking", "recipe", "fun"],
            "brand": "soulfra",
            "size": [1200, 600]
        }

        Returns: Binary PNG image data
        """
        data = request.get_json()

        keywords = data.get('keywords', ['test', 'comic'])
        brand = data.get('brand', 'soulfra')
        size = tuple(data.get('size', [1200, 600]))

        try:
            # Import procedural media generator
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from procedural_media import ProceduralMediaGenerator

            # Brand color mapping
            brand_colors_map = {
                'soulfra': {'primary': '#00ffff', 'secondary': '#ff00ff', 'accent': '#ffffff'},
                'deathtodata': {'primary': '#00ff00', 'secondary': '#00cc00', 'accent': '#004400'},
                'calriven': {'primary': '#9b59b6', 'secondary': '#8e44ad', 'accent': '#6c3483'},
                'finishthatidea': {'primary': '#e74c3c', 'secondary': '#c0392b', 'accent': '#a93226'},
                'finishthisrepo': {'primary': '#3498db', 'secondary': '#2980b9', 'accent': '#1f618d'},
                'saveorsink': {'primary': '#1abc9c', 'secondary': '#16a085', 'accent': '#117a65'},
                'sellthismvp': {'primary': '#f39c12', 'secondary': '#e67e22', 'accent': '#ca6f1e'},
                'dealordelete': {'primary': '#e91e63', 'secondary': '#c2185b', 'accent': '#880e4f'},
                'mascotrooms': {'primary': '#9c27b0', 'secondary': '#7b1fa2', 'accent': '#6a1b9a'}
            }

            brand_colors = brand_colors_map.get(brand, brand_colors_map['soulfra'])

            # Initialize generator
            gen = ProceduralMediaGenerator()

            print(f'🎨 Generating comic for {brand}: {keywords}')
            print(f'   Size: {size}')

            # Generate comic image
            image_bytes = gen.generate_hero_image(
                keywords=keywords,
                brand_colors=brand_colors,
                size=size,
                style='comic'
            )

            print(f'   ✅ Generated ({len(image_bytes):,} bytes)')

            return send_file(
                io.BytesIO(image_bytes),
                mimetype='image/png',
                as_attachment=False,
                download_name=f'comic_{brand}_{"_".join(keywords[:3])}.png'
            )

        except Exception as e:
            print(f'   ❌ Generation failed: {e}')
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/generate/gif', methods=['POST'])
    def api_generate_gif():
        """
        Generate animated GIF from sequence of procedural images

        POST /api/generate/gif
        {
            "keywords": ["animation", "test"],
            "brand": "soulfra",
            "frames": 10,
            "duration": 100 (ms per frame),
            "styles": ["gradient", "pixel", "geometric"] (optional, cycles through)
        }

        Returns: Binary GIF image data
        """
        data = request.get_json()

        keywords = data.get('keywords', ['test', 'animation'])
        brand = data.get('brand', 'soulfra')
        frames = data.get('frames', 10)
        duration = data.get('duration', 100)  # milliseconds
        styles = data.get('styles', ['gradient', 'pixel', 'geometric'])

        try:
            from PIL import Image
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from procedural_media import ProceduralMediaGenerator

            # Brand color mapping
            brand_colors_map = {
                'soulfra': {'primary': '#00ffff', 'secondary': '#ff00ff', 'accent': '#ffffff'},
                'deathtodata': {'primary': '#00ff00', 'secondary': '#00cc00', 'accent': '#004400'},
                'calriven': {'primary': '#9b59b6', 'secondary': '#8e44ad', 'accent': '#6c3483'},
                'finishthatidea': {'primary': '#e74c3c', 'secondary': '#c0392b', 'accent': '#a93226'},
                'finishthisrepo': {'primary': '#3498db', 'secondary': '#2980b9', 'accent': '#1f618d'},
                'saveorsink': {'primary': '#1abc9c', 'secondary': '#16a085', 'accent': '#117a65'},
                'sellthismvp': {'primary': '#f39c12', 'secondary': '#e67e22', 'accent': '#ca6f1e'},
                'dealordelete': {'primary': '#e91e63', 'secondary': '#c2185b', 'accent': '#880e4f'},
                'mascotrooms': {'primary': '#9c27b0', 'secondary': '#7b1fa2', 'accent': '#6a1b9a'}
            }

            brand_colors = brand_colors_map.get(brand, brand_colors_map['soulfra'])

            gen = ProceduralMediaGenerator()

            print(f'🎬 Generating GIF for {brand}: {keywords}')
            print(f'   Frames: {frames}, Duration: {duration}ms')

            # Generate frames
            frame_images = []
            for i in range(frames):
                # Cycle through styles
                style = styles[i % len(styles)]

                # Generate frame
                frame_bytes = gen.generate_hero_image(
                    keywords=keywords + [f'frame{i}'],  # Vary seed slightly
                    brand_colors=brand_colors,
                    size=(600, 600),
                    style=style
                )

                # Load as PIL Image
                frame_img = Image.open(io.BytesIO(frame_bytes))
                frame_images.append(frame_img)
                print(f'   Frame {i+1}/{frames} ({style})')

            # Save as GIF
            gif_bytes = io.BytesIO()
            frame_images[0].save(
                gif_bytes,
                format='GIF',
                save_all=True,
                append_images=frame_images[1:],
                duration=duration,
                loop=0
            )
            gif_bytes.seek(0)

            print(f'   ✅ Generated GIF ({len(gif_bytes.getvalue()):,} bytes)')

            return send_file(
                gif_bytes,
                mimetype='image/gif',
                as_attachment=False,
                download_name=f'animation_{brand}_{"_".join(keywords[:2])}.gif'
            )

        except Exception as e:
            print(f'   ❌ GIF generation failed: {e}')
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    # =======================
    # Vanity QR Management
    # =======================

    @app.route('/api/qr/create', methods=['POST'])
    def api_qr_create():
        """
        Create branded vanity QR code with advanced features

        POST /api/qr/create
        {
            "url": "https://cringeproof.com/blog/post",
            "brand": "cringeproof",
            "label": "Scan Me",
            "custom_code": "promo2025" (optional),
            "style": "minimal|rounded|circles" (optional),
            "primary_color": "#8B5CF6" (optional),
            "secondary_color": "#3B82F6" (optional, enables gradient),
            "animated": true (optional, Pro feature)
        }

        Returns: JSON with vanity URL, short code, and QR image data
        """
        data = request.get_json()

        url = data.get('url')
        brand = data.get('brand', 'soulfra')
        label = data.get('label')
        custom_code = data.get('custom_code')

        # Advanced features
        style = data.get('style')  # Will use brand default if not specified
        primary_color = data.get('primary_color')  # Will use brand color if not specified
        secondary_color = data.get('secondary_color')  # Optional gradient
        animated = data.get('animated', False)  # Pro feature

        if not url:
            return jsonify({'error': 'URL required'}), 400

        # Check if using advanced features
        use_advanced = secondary_color or animated

        # Create vanity URL first
        from vanity_qr import create_vanity_url, save_vanity_qr, BRAND_DOMAINS
        vanity_url, short_code = create_vanity_url(url, brand, custom_code)

        # Generate QR code with appropriate generator
        if use_advanced:
            # Use advanced QR generator
            from advanced_qr import AdvancedQRGenerator

            # Get brand defaults if not specified
            brand_config = BRAND_DOMAINS.get(brand, BRAND_DOMAINS['soulfra'])
            final_style = style or brand_config['style']
            final_primary = primary_color or brand_config['colors']['primary']

            generator = AdvancedQRGenerator(
                data=vanity_url,
                style=final_style,
                primary_color=final_primary,
                secondary_color=secondary_color,
                label=label,
                size=512
            )

            if animated:
                qr_image = generator.generate_animated()
                mimetype = 'image/gif'
                file_ext = 'gif'
            else:
                qr_image = generator.generate()
                mimetype = 'image/png'
                file_ext = 'png'

            qr_style = f"advanced_{'animated' if animated else 'gradient' if secondary_color else 'styled'}"
        else:
            # Use standard vanity QR generator
            result = create_and_save_vanity_qr(
                full_url=url,
                brand_slug=brand,
                label=label,
                custom_code=custom_code
            )
            qr_image = result['qr_image']
            mimetype = 'image/png'
            file_ext = 'png'
            qr_style = 'branded_with_label' if label else 'branded'

        # Save to database (if not already saved by create_and_save_vanity_qr)
        if use_advanced:
            save_vanity_qr(
                short_code=short_code,
                brand_slug=brand,
                full_url=url,
                vanity_url=vanity_url,
                qr_image=qr_image,
                style=qr_style,
                metadata={'primary_color': final_primary, 'secondary_color': secondary_color, 'animated': animated}
            )

        # Convert image to base64 for JSON response
        import base64
        image_b64 = base64.b64encode(qr_image).decode('utf-8')

        return jsonify({
            'success': True,
            'vanity_url': vanity_url,
            'short_code': short_code,
            'full_url': url,
            'qr_image_base64': image_b64,
            'qr_download_url': f"/api/qr/download/{short_code}",
            'mimetype': mimetype,
            'file_extension': file_ext
        })

    @app.route('/api/qr/download/<short_code>')
    def api_qr_download(short_code):
        """Download QR code image"""
        qr_data = get_vanity_qr(short_code)

        if not qr_data:
            return "QR code not found", 404

        return send_file(
            io.BytesIO(qr_data['qr_image']),
            mimetype='image/png',
            as_attachment=True,
            download_name=f'qr_{short_code}.png'
        )

    @app.route('/api/qr/list')
    def api_qr_list():
        """List all vanity QR codes"""
        conn = get_db()
        qrs = conn.execute('''
            SELECT short_code, brand_slug, full_url, vanity_url,
                   created_at, clicks
            FROM vanity_qr_codes
            ORDER BY created_at DESC
            LIMIT 100
        ''').fetchall()
        conn.close()

        return jsonify({
            'qr_codes': [dict(qr) for qr in qrs]
        })

    @app.route('/v/<short_code>')
    def vanity_qr_redirect(short_code):
        """
        Vanity QR Code Redirect - The CRITICAL route!

        When someone scans a QR code pointing to cringeproof.com/v/WuhOM1:
        1. Look up short code in database
        2. Track the click (increment counter, timestamp)
        3. Redirect to full URL

        Example:
            cringeproof.com/v/WuhOM1
            → Tracks click
            → Redirects to: https://cringeproof.com/blog/how-to-build-a-brand
        """
        from flask import redirect

        qr_data = get_vanity_qr(short_code)

        if not qr_data:
            return f"QR code '{short_code}' not found", 404

        # Track the click
        from vanity_qr import track_qr_click
        track_qr_click(short_code)

        # Redirect to the full URL
        return redirect(qr_data['full_url'], code=302)

    # =======================
    # Image Gallery
    # =======================

    @app.route('/admin/images')
    def admin_images():
        """Image gallery/manager"""
        conn = get_db()
        images = conn.execute('''
            SELECT id, image_hash, platform, post_id,
                   published_at, status
            FROM published_images
            ORDER BY published_at DESC
            LIMIT 50
        ''').fetchall()
        conn.close()

        return render_template('admin/images.html', images=[dict(img) for img in images])

    @app.route('/api/images/<int:image_id>')
    def api_image_get(image_id):
        """Get image by ID"""
        conn = get_db()
        image = conn.execute(
            'SELECT * FROM published_images WHERE id = ?',
            (image_id,)
        ).fetchone()
        conn.close()

        if not image:
            return "Image not found", 404

        return send_file(
            io.BytesIO(image['image_data']),
            mimetype='image/jpeg'
        )

    # =======================
    # Template Management
    # =======================

    @app.route('/admin/templates')
    def admin_templates():
        """Template manager"""
        conn = get_db()
        templates = conn.execute('''
            SELECT id, name, category, brand_slug,
                   is_public, created_at
            FROM visual_templates
            ORDER BY created_at DESC
        ''').fetchall()
        conn.close()

        return render_template('admin/templates.html', templates=[dict(t) for t in templates])

    @app.route('/api/templates/save', methods=['POST'])
    def api_template_save():
        """
        Save image composition as template

        POST /api/templates/save
        {
            "name": "Blog Header Template",
            "category": "blog",
            "brand": "cringeproof",
            "template": {
                "size": [1200, 630],
                "layers": [...]
            },
            "is_public": false
        }
        """
        data = request.get_json()

        name = data.get('name')
        category = data.get('category', 'general')
        brand = data.get('brand', 'soulfra')
        template = data.get('template', {})
        is_public = data.get('is_public', False)

        if not name:
            return jsonify({'error': 'Name required'}), 400

        conn = get_db()
        conn.execute('''
            INSERT INTO visual_templates
            (name, category, brand_slug, template_json, is_public)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            name,
            category,
            brand,
            json.dumps(template),
            1 if is_public else 0
        ))
        conn.commit()

        template_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        conn.close()

        return jsonify({
            'success': True,
            'template_id': template_id
        })

    @app.route('/api/templates/<int:template_id>')
    def api_template_get(template_id):
        """Get template by ID"""
        conn = get_db()
        template = conn.execute(
            'SELECT * FROM visual_templates WHERE id = ?',
            (template_id,)
        ).fetchone()
        conn.close()

        if not template:
            return jsonify({'error': 'Template not found'}), 404

        return jsonify({
            'id': template['id'],
            'name': template['name'],
            'category': template['category'],
            'brand_slug': template['brand_slug'],
            'template': json.loads(template['template_json']),
            'is_public': bool(template['is_public']),
            'created_at': template['created_at']
        })

    # =======================
    # Admin Dashboard
    # =======================

    @app.route('/admin/image-dashboard')
    def admin_image_dashboard():
        """Image management dashboard"""
        conn = get_db()

        # Get stats
        stats = {
            'images_generated': conn.execute('SELECT COUNT(*) FROM published_images').fetchone()[0],
            'qr_codes_created': conn.execute('SELECT COUNT(*) FROM vanity_qr_codes').fetchone()[0],
            'templates_saved': conn.execute('SELECT COUNT(*) FROM visual_templates').fetchone()[0],
            'total_qr_clicks': conn.execute('SELECT COALESCE(SUM(clicks), 0) FROM vanity_qr_codes').fetchone()[0]
        }

        # Recent activity
        recent_images = conn.execute('''
            SELECT id, platform, published_at
            FROM published_images
            ORDER BY published_at DESC
            LIMIT 5
        ''').fetchall()

        recent_qrs = conn.execute('''
            SELECT short_code, brand_slug, created_at, clicks
            FROM vanity_qr_codes
            ORDER BY created_at DESC
            LIMIT 5
        ''').fetchall()

        conn.close()

        return render_template('admin/image_dashboard.html',
                             stats=stats,
                             recent_images=[dict(img) for img in recent_images],
                             recent_qrs=[dict(qr) for qr in recent_qrs])

    # =======================
    # Public QR Builder
    # =======================

    @app.route('/qr/create')
    def qr_builder():
        """Public QR code builder interface"""
        return render_template('qr/builder_v1_dinghy.html',
            theme_primary='#667eea',
            theme_secondary='#764ba2'
        )

    # =======================
    # QR Chat Routes
    # =======================

    @app.route('/qr/chat/<short_code>')
    def qr_chat(short_code):
        """Mobile chat interface for QR code"""
        # Get QR code info
        qr = get_db().execute(
            'SELECT brand_slug FROM vanity_qr_codes WHERE short_code = ?',
            (short_code,)
        ).fetchone()

        if not qr:
            return "QR code not found", 404

        # Get brand colors
        from vanity_qr import BRAND_DOMAINS
        brand_config = BRAND_DOMAINS.get(qr['brand_slug'], {})
        colors = brand_config.get('colors', {})

        return render_template('qr/chat.html',
            short_code=short_code,
            brand_slug=qr['brand_slug'],
            theme_primary=colors.get('primary', '#667eea'),
            theme_secondary=colors.get('secondary', '#764ba2')
        )

    @app.route('/api/qr/chat/<short_code>/messages')
    def qr_chat_messages(short_code):
        """Get chat messages for a QR code"""
        messages = get_db().execute('''
            SELECT sender, message, created_at
            FROM qr_chat_transcripts
            WHERE short_code = ?
            ORDER BY created_at ASC
        ''', (short_code,)).fetchall()

        return jsonify({
            'messages': [dict(m) for m in messages]
        })

    @app.route('/api/qr/chat/<short_code>/send', methods=['POST'])
    def qr_chat_send(short_code):
        """Send a message and get Ollama response"""
        data = request.get_json()
        message = data.get('message', '').strip()

        if not message:
            return jsonify({'error': 'Message required'}), 400

        # Save user message
        conn = get_db()
        conn.execute('''
            INSERT INTO qr_chat_transcripts (short_code, sender, message, user_ip, device_type)
            VALUES (?, 'user', ?, ?, ?)
        ''', (short_code, message, request.remote_addr, request.user_agent.platform))
        conn.commit()

        # Get Ollama response
        try:
            import urllib.request
            import json as json_lib

            ollama_prompt = {
                'model': 'llama2',
                'prompt': f"User: {message}\nAssistant:",
                'stream': False
            }

            req = urllib.request.Request(
                'http://localhost:11434/api/generate',
                data=json_lib.dumps(ollama_prompt).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )

            with urllib.request.urlopen(req, timeout=30) as response:
                result = json_lib.loads(response.read().decode('utf-8'))
                ai_response = result.get('response', 'Sorry, I could not process that.')

        except Exception as e:
            print(f"Ollama error: {e}")
            ai_response = "I'm having trouble connecting. Please try again."

        # Save AI response
        conn.execute('''
            INSERT INTO qr_chat_transcripts (short_code, sender, message, user_ip, device_type)
            VALUES (?, 'assistant', ?, ?, ?)
        ''', (short_code, ai_response, request.remote_addr, request.user_agent.platform))
        conn.commit()

        return jsonify({
            'response': ai_response
        })

    print("✅ Registered image admin routes")
    print("   - /admin/canvas (WYSIWYG editor)")
    print("   - /qr/create (Public QR builder)")
    print("   - /api/generate/* (Image generation)")
    print("   - /api/qr/* (Vanity QR codes)")
    print("   - /v/<code> (QR redirect - CRITICAL!)")
    print("   - /admin/images (Gallery)")
    print("   - /admin/templates (Templates)")
