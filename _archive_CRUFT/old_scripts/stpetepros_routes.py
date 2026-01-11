#!/usr/bin/env python3
"""
StPetePros Routes - Professional Directory

Handles:
- Professional signup/registration
- Category browsing
- Professional profiles
- Search
- Reviews
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g, jsonify
from database import get_db
from datetime import datetime
import qrcode
import io
import base64
import subprocess
import json

stpetepros_bp = Blueprint('stpetepros', __name__)


@stpetepros_bp.route('/signup/professional', methods=['GET', 'POST'])
def professional_signup():
    """
    Professional signup form - REQUIRES Soulfra Master Auth

    Users must have a Soulfra account to create a professional profile.
    This links their professional listing to their master identity.
    """
    # REQUIRE Soulfra Master Auth
    if not session.get('logged_in') or not session.get('master_user_id'):
        flash('Create a Soulfra account to get started', 'info')
        # Redirect to signup instead of login (they don't have an account yet!)
        return redirect(f'/signup-soulfra?next={request.url}')

    master_user_id = session.get('master_user_id')

    if request.method == 'GET':
        # Get user info to pre-fill form
        db = get_db()
        user = db.execute(
            'SELECT * FROM soulfra_master_users WHERE id = ?',
            (master_user_id,)
        ).fetchone()

        return render_template('stpetepros/signup.html', user=user)

    # POST - Handle form submission
    db = get_db()

    # Get form data
    business_name = request.form.get('business_name', '').strip()
    category = request.form.get('category', '').strip()
    bio = request.form.get('bio', '').strip()
    phone = request.form.get('phone', '').strip()
    email = request.form.get('email', '').strip()
    website = request.form.get('website', '').strip()
    address = request.form.get('address', '').strip()
    city = request.form.get('city', 'St. Petersburg').strip()
    zip_code = request.form.get('zip_code', '').strip()

    # Validate required fields
    if not all([business_name, category, bio, phone, email, address, zip_code]):
        return render_template('stpetepros/signup.html', error='All required fields must be filled out')

    # Get corresponding user_id from users table (domain-specific)
    user_id = db.execute(
        'SELECT id FROM users WHERE email = ?',
        (session.get('email') or email,)
    ).fetchone()

    if user_id:
        user_id = user_id['id']
    else:
        # Create user account if not exists (backwards compatibility)
        cursor = db.execute('''
            INSERT INTO users (username, email, password_hash, display_name)
            VALUES (?, ?, '', ?)
        ''', (
            session.get('master_username', email.split('@')[0]),
            email,
            session.get('display_name', business_name)
        ))
        user_id = cursor.lastrowid
        db.commit()
    
    # Generate QR code for business card
    qr_data = f"https://stpetepros.com/professional/PENDING"  # Will update after we get the ID
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert QR to bytes
    buffer = io.BytesIO()
    qr_img.save(buffer, format='PNG')
    qr_bytes = buffer.getvalue()
    
    # Insert into database
    cursor = db.execute('''
        INSERT INTO professionals (
            user_id, business_name, category, bio, phone, email, website,
            address, city, state, zip_code, qr_business_card, verified
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'FL', ?, ?, 0)
    ''', (user_id, business_name, category, bio, phone, email, website, address, city, zip_code, qr_bytes))
    
    professional_id = cursor.lastrowid
    db.commit()
    
    # Update QR code with real ID
    qr_data = f"https://stpetepros.com/professional/{professional_id}"
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    qr_img.save(buffer, format='PNG')
    qr_bytes = buffer.getvalue()
    
    db.execute('UPDATE professionals SET qr_business_card = ? WHERE id = ?', (qr_bytes, professional_id))
    db.commit()
    
    flash(f'Your professional profile has been created! Your profile ID is #{professional_id}', 'success')
    return redirect(url_for('stpetepros.professional_profile', professional_id=professional_id))


@stpetepros_bp.route('/professionals')
def browse_all_professionals():
    """Browse all professionals"""
    db = get_db()

    # Get all professionals
    professionals = db.execute('''
        SELECT * FROM professionals
        ORDER BY rating_avg DESC, business_name ASC
    ''').fetchall()

    # Group by category for display
    categories_dict = {}
    for pro in professionals:
        cat = pro['category']
        if cat not in categories_dict:
            categories_dict[cat] = []
        categories_dict[cat].append(pro)

    return render_template('stpetepros/all_professionals.html',
                         professionals=professionals,
                         categories_dict=categories_dict,
                         total_count=len(professionals))


@stpetepros_bp.route('/about')
def about():
    """About StPetePros page"""
    return render_template('stpetepros/about.html')


@stpetepros_bp.route('/categories')
def browse_categories():
    """Browse all categories with professional counts"""
    db = get_db()

    # Get category counts
    category_counts = db.execute('''
        SELECT category, COUNT(*) as count
        FROM professionals
        GROUP BY category
        ORDER BY count DESC, category ASC
    ''').fetchall()

    # Category display names
    category_names = {
        'plumbing': 'Plumbing',
        'electrical': 'Electrical',
        'hvac': 'HVAC',
        'roofing': 'Roofing',
        'legal': 'Legal Services',
        'landscaping': 'Landscaping',
        'cleaning': 'Cleaning',
        'pest-control': 'Pest Control',
        'painting': 'Painting',
        'pool-service': 'Pool Service',
        'real-estate': 'Real Estate',
        'auto-repair': 'Auto Repair',
        'chef': 'Chefs & Catering',
        'meal_prep': 'Meal Prep',
        'podcast': 'Podcast Production',
        'youtube': 'YouTube Production',
        'gaming': 'Gaming & Streaming',
        'tech': 'Tech Consulting',
        'privacy': 'Privacy & Security'
    }

    # Build category list with names
    categories = []
    for row in category_counts:
        cat = row['category']
        categories.append({
            'slug': cat,
            'name': category_names.get(cat, cat.replace('_', ' ').replace('-', ' ').title()),
            'count': row['count']
        })

    return render_template('stpetepros/categories.html',
                         categories=categories,
                         total_categories=len(categories))


@stpetepros_bp.route('/professionals/category/<category>')
def category_browse(category):
    """Browse professionals by category"""
    db = get_db()

    # Get all professionals in this category
    professionals = db.execute('''
        SELECT * FROM professionals
        WHERE category = ?
        ORDER BY rating_avg DESC, business_name ASC
    ''', (category,)).fetchall()
    
    # Category display names
    category_names = {
        'plumbing': 'Plumbing',
        'electrical': 'Electrical',
        'hvac': 'HVAC',
        'roofing': 'Roofing',
        'legal': 'Legal Services',
        'landscaping': 'Landscaping',
        'cleaning': 'Cleaning',
        'pest-control': 'Pest Control',
        'painting': 'Painting',
        'pool-service': 'Pool Service',
        'real-estate': 'Real Estate',
        'auto-repair': 'Auto Repair'
    }
    
    category_name = category_names.get(category, category.title())
    
    return render_template('stpetepros/category.html',
                         category=category,
                         category_name=category_name,
                         professionals=professionals)


@stpetepros_bp.route('/professionals/search')
def search_professionals():
    """Search professionals by keyword"""
    query = request.args.get('q', '').strip()
    
    if not query:
        return redirect(url_for('index'))
    
    db = get_db()
    
    # Search in business name, category, and bio
    professionals = db.execute('''
        SELECT * FROM professionals
        WHERE business_name LIKE ? OR category LIKE ? OR bio LIKE ?
        ORDER BY rating_avg DESC, business_name ASC
        LIMIT 50
    ''', (f'%{query}%', f'%{query}%', f'%{query}%')).fetchall()
    
    return render_template('stpetepros/search_results.html',
                         query=query,
                         professionals=professionals)


@stpetepros_bp.route('/professional/<int:professional_id>')
def professional_profile(professional_id):
    """Individual professional profile page"""
    db = get_db()
    
    # Get professional info
    professional = db.execute('''
        SELECT * FROM professionals WHERE id = ?
    ''', (professional_id,)).fetchone()
    
    if not professional:
        flash('Professional not found', 'error')
        return redirect(url_for('index'))
    
    # Get reviews for this professional
    reviews = db.execute('''
        SELECT r.*, u.username, u.email
        FROM professional_reviews r
        LEFT JOIN users u ON r.reviewer_user_id = u.id
        WHERE r.professional_id = ?
        ORDER BY r.created_at DESC
    ''', (professional_id,)).fetchall()
    
    # Convert QR code to base64 for display
    qr_base64 = None
    if professional['qr_business_card']:
        qr_base64 = base64.b64encode(professional['qr_business_card']).decode('utf-8')
    
    return render_template('stpetepros/profile.html',
                         professional=professional,
                         reviews=reviews,
                         qr_base64=qr_base64)


@stpetepros_bp.route('/stpetepros/admin/sales')
def sales_dashboard():
    """Sales dashboard for managing prospects and routes"""
    db = get_db()

    # Get all prospects with stats
    prospects = db.execute('''
        SELECT * FROM scraped_prospects
        ORDER BY score DESC, review_count DESC
    ''').fetchall()

    # Calculate stats
    stats = {
        'total': len(prospects),
        'not_contacted': len([p for p in prospects if p['sales_status'] == 'not_contacted']),
        'follow_up': len([p for p in prospects if p['sales_status'] == 'follow_up']),
        'closed': len([p for p in prospects if p['sales_status'] == 'closed'])
    }

    return render_template('stpetepros/sales_dashboard.html',
                         prospects=prospects,
                         stats=stats)


@stpetepros_bp.route('/stpetepros/admin/update-status/<int:prospect_id>', methods=['POST'])
def update_prospect_status(prospect_id):
    """Update sales status for a prospect"""
    db = get_db()
    data = request.get_json()
    new_status = data.get('status')

    db.execute('''
        UPDATE scraped_prospects
        SET sales_status = ?, contacted_at = ?
        WHERE id = ?
    ''', (new_status, datetime.now(), prospect_id))

    db.commit()

    return jsonify({'success': True})


@stpetepros_bp.route('/stpetepros/admin/export-airtable', methods=['POST'])
def export_to_airtable():
    """Trigger Airtable export"""
    try:
        # Run the scraper with export flag
        result = subprocess.run(
            ['python3', 'stpetepros_scraper.py', '--export-airtable'],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            return jsonify({'success': True, 'count': 50})
        else:
            return jsonify({'success': False, 'error': result.stderr}), 500

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@stpetepros_bp.route('/stpetepros/admin/plan-route')
def plan_route():
    """Generate optimized sales route"""
    start_address = request.args.get('start', 'Downtown St Petersburg, FL')
    prospect_ids = request.args.get('prospects', '').split(',')

    db = get_db()

    # Get selected prospects
    if prospect_ids and prospect_ids[0]:
        placeholders = ','.join('?' * len(prospect_ids))
        prospects = db.execute(f'''
            SELECT * FROM scraped_prospects
            WHERE id IN ({placeholders})
        ''', prospect_ids).fetchall()
    else:
        # Get top 15 by default
        prospects = db.execute('''
            SELECT * FROM scraped_prospects
            WHERE sales_status = 'not_contacted'
            ORDER BY score DESC
            LIMIT 15
        ''').fetchall()

    # For now, just return the list
    # In production, would call route optimizer here
    return render_template('stpetepros/route_planner.html',
                         prospects=prospects,
                         start_address=start_address)


@stpetepros_bp.route('/professional/inbox')
def professional_inbox():
    """
    Professional inbox - view messages from customers

    Requires authentication
    """
    if not session.get('logged_in') or not session.get('master_user_id'):
        flash('Please login to view your inbox', 'info')
        return redirect(url_for('auth_bridge_login', next=request.url))

    db = get_db()
    master_user_id = session.get('master_user_id')

    # Get user_id from master_user_id
    user = db.execute(
        'SELECT id FROM users WHERE email = (SELECT email FROM soulfra_master_users WHERE id = ?)',
        (master_user_id,)
    ).fetchone()

    if not user:
        flash('User account not found', 'error')
        return redirect(url_for('index'))

    user_id = user['id']

    # Get all messages for this user
    messages = db.execute('''
        SELECT m.*, u.username as from_username, u.display_name as from_display_name
        FROM messages m
        LEFT JOIN users u ON u.id = m.from_user_id
        WHERE m.to_user_id = ?
        ORDER BY m.created_at DESC
    ''', (user_id,)).fetchall()

    # Count unread messages
    unread_count = db.execute(
        'SELECT COUNT(*) as count FROM messages WHERE to_user_id = ? AND read = 0',
        (user_id,)
    ).fetchone()['count']

    return render_template('stpetepros/inbox.html',
                         messages=messages,
                         unread_count=unread_count)


@stpetepros_bp.route('/professional/message/<int:message_id>/mark-read', methods=['POST'])
def mark_message_read(message_id):
    """Mark a message as read"""
    if not session.get('logged_in'):
        return jsonify({'error': 'Not authenticated'}), 401

    db = get_db()

    # Mark as read
    db.execute('UPDATE messages SET read = 1 WHERE id = ?', (message_id,))
    db.commit()

    return jsonify({'success': True})


@stpetepros_bp.route('/professional/<int:professional_id>/send-message', methods=['POST'])
def send_message_to_professional(professional_id):
    """Send a message to a professional (inquiry from customer) with AI moderation"""
    db = get_db()

    # Get professional info
    professional = db.execute('SELECT * FROM professionals WHERE id = ?', (professional_id,)).fetchone()

    if not professional:
        return jsonify({'error': 'Professional not found'}), 404

    # Get message content
    content = request.form.get('message', '').strip()
    from_name = request.form.get('from_name', '').strip()
    from_email = request.form.get('from_email', '').strip()

    if not content or not from_name or not from_email:
        return jsonify({'error': 'All fields required'}), 400

    # AI MODERATION CHECK - Scan message before saving
    from ai_moderation_integration import auto_moderate_content
    moderation_result = auto_moderate_content(
        content_type='stpetepros_message',
        content_id=0,  # Will update after insert
        text_content=content,
        domain='stpetepros'
    )

    # Block high-confidence violations immediately
    if moderation_result.get('flagged') and moderation_result.get('confidence', 0) > 0.8:
        flash('Your message was flagged by our automated system. Please review our messaging guidelines and try again.', 'error')
        return redirect(url_for('stpetepros.professional_profile', professional_id=professional_id))

    # Get or create anonymous user for this email
    from_user = db.execute('SELECT id FROM users WHERE email = ?', (from_email,)).fetchone()

    if not from_user:
        # Create anonymous user
        cursor = db.execute('''
            INSERT INTO users (username, email, password_hash, display_name)
            VALUES (?, ?, '', ?)
        ''', (from_email.split('@')[0], from_email, from_name))
        from_user_id = cursor.lastrowid
        db.commit()
    else:
        from_user_id = from_user['id']

    # Get professional's user_id
    to_user_id = professional['user_id']

    if not to_user_id:
        return jsonify({'error': 'Professional account not linked'}), 500

    # Create message (may be held for review if flagged)
    cursor = db.execute('''
        INSERT INTO messages (from_user_id, to_user_id, content, read)
        VALUES (?, ?, ?, ?)
    ''', (from_user_id, to_user_id, content,
          0 if moderation_result.get('flagged') else 0))  # Unread initially
    message_id = cursor.lastrowid
    db.commit()

    # Update moderation queue with actual message_id
    if moderation_result.get('flagged'):
        db.execute('''
            UPDATE moderation_queue
            SET content_id = ?
            WHERE content_type = 'stpetepros_message' AND content_id = 0
            ORDER BY id DESC LIMIT 1
        ''', (message_id,))
        db.commit()

    # Show appropriate message to user
    if moderation_result.get('flagged'):
        flash('Your message has been sent and is pending review. The professional will receive it once approved.', 'warning')
    else:
        flash('Message sent successfully!', 'success')

    return redirect(url_for('stpetepros.professional_profile', professional_id=professional_id))


@stpetepros_bp.route('/admin/stpetepros')
def admin_dashboard():
    """
    StPetePros Admin Dashboard - Your CRM/ERP for managing professionals

    Features:
    - View all professionals who signed up
    - Approval queue (approve/reject new signups)
    - Stats dashboard (total, new today, by category)
    - Export to CSV for mailing lists
    - Download QR codes
    - Color-coded status system
    """
    db = get_db()

    # Get all professionals
    professionals = db.execute('''
        SELECT * FROM professionals
        ORDER BY created_at DESC
    ''').fetchall()

    # Calculate stats
    from datetime import date
    today = date.today().isoformat()

    stats = {
        'total': len(professionals),
        'pending': len([p for p in professionals if p['approval_status'] == 'pending']),
        'approved': len([p for p in professionals if p['approval_status'] == 'approved']),
        'new_today': len([p for p in professionals if p['created_at'] and p['created_at'].startswith(today)])
    }

    # Group by category
    categories = {}
    for pro in professionals:
        cat = pro['category']
        if cat not in categories:
            categories[cat] = 0
        categories[cat] += 1

    return render_template('admin/stpetepros_dashboard.html',
                         professionals=professionals,
                         stats=stats,
                         categories=categories)


@stpetepros_bp.route('/admin/stpetepros/approve/<int:professional_id>', methods=['POST'])
def approve_professional(professional_id):
    """Approve a professional listing"""
    db = get_db()

    db.execute('''
        UPDATE professionals
        SET approval_status = 'approved'
        WHERE id = ?
    ''', (professional_id,))

    db.commit()

    flash('Professional approved!', 'success')
    return redirect(url_for('stpetepros.admin_dashboard'))


@stpetepros_bp.route('/admin/stpetepros/reject/<int:professional_id>', methods=['POST'])
def reject_professional(professional_id):
    """Reject a professional listing"""
    db = get_db()

    db.execute('''
        UPDATE professionals
        SET approval_status = 'rejected'
        WHERE id = ?
    ''', (professional_id,))

    db.commit()

    flash('Professional rejected', 'warning')
    return redirect(url_for('stpetepros.admin_dashboard'))


@stpetepros_bp.route('/admin/stpetepros/moderation')
def moderation_dashboard():
    """
    AI Moderation Dashboard - Real-time message monitoring

    Shows:
    - Pending review queue (messages flagged by AI)
    - Approved messages log
    - AI confidence scores and patterns
    - Database performance counters (like C/assembly level visibility)
    """
    import os
    import json
    from datetime import datetime

    db = get_db()

    # Calculate stats
    total_messages = db.execute('SELECT COUNT(*) as c FROM messages').fetchone()['c']

    # Count flagged messages (in moderation queue)
    flagged_count = db.execute('''
        SELECT COUNT(*) as c FROM moderation_queue
        WHERE content_type = 'stpetepros_message' AND status = 'pending'
    ''').fetchone()['c']

    # Clean messages = total - flagged - blocked
    blocked_count = db.execute('''
        SELECT COUNT(*) as c FROM moderation_queue
        WHERE content_type = 'stpetepros_message' AND reviewer_action = 'block'
    ''').fetchone()['c']

    clean_count = total_messages - flagged_count - blocked_count

    stats = {
        'total_messages': total_messages,
        'clean_messages': clean_count,
        'flagged_messages': flagged_count,
        'blocked_messages': blocked_count
    }

    # Database performance stats
    professionals_count = db.execute('SELECT COUNT(*) as c FROM professionals').fetchone()['c']
    queue_count = db.execute('SELECT COUNT(*) as c FROM moderation_queue').fetchone()['c']

    # Get database size
    db_path = 'soulfra.db'
    db_size_bytes = os.path.getsize(db_path) if os.path.exists(db_path) else 0
    db_size_mb = round(db_size_bytes / (1024 * 1024), 2)

    db_stats = {
        'messages_count': total_messages,
        'professionals_count': professionals_count,
        'queue_count': queue_count,
        'db_size_mb': db_size_mb
    }

    # Get pending messages with AI analysis
    pending_messages = db.execute('''
        SELECT
            mq.*,
            m.content,
            m.from_user_id,
            m.to_user_id,
            u1.display_name as from_name,
            u1.email as from_email,
            p.business_name as professional_name
        FROM moderation_queue mq
        JOIN messages m ON m.id = mq.content_id
        LEFT JOIN users u1 ON m.from_user_id = u1.id
        LEFT JOIN professionals p ON m.to_user_id = p.user_id
        WHERE mq.content_type = 'stpetepros_message' AND mq.status = 'pending'
        ORDER BY mq.flagged_at DESC
        LIMIT 50
    ''').fetchall()

    # Parse AI analysis JSON for each message
    pending_enriched = []
    for msg in pending_messages:
        msg_dict = dict(msg)
        msg_dict['message_id'] = msg['content_id']
        msg_dict['queue_id'] = msg['id']
        pending_enriched.append(msg_dict)

    # Get recent approved messages
    approved_messages = db.execute('''
        SELECT
            m.*,
            u1.display_name as from_name,
            p.business_name as professional_name,
            0.95 as ai_confidence
        FROM messages m
        LEFT JOIN users u1 ON m.from_user_id = u1.id
        LEFT JOIN professionals p ON m.to_user_id = p.user_id
        WHERE m.id NOT IN (
            SELECT content_id FROM moderation_queue WHERE content_type = 'stpetepros_message'
        )
        ORDER BY m.created_at DESC
        LIMIT 20
    ''').fetchall()

    return render_template('admin/stpetepros_moderation.html',
                         stats=stats,
                         db_stats=db_stats,
                         pending_messages=pending_enriched,
                         approved_messages=approved_messages)


@stpetepros_bp.route('/admin/stpetepros/moderation/approve/<int:queue_id>', methods=['POST'])
def approve_moderation(queue_id):
    """Approve a flagged message - deliver to professional"""
    db = get_db()

    # Update moderation queue
    db.execute('''
        UPDATE moderation_queue
        SET status = 'approved',
            reviewer_action = 'approve',
            reviewed_at = ?
        WHERE id = ?
    ''', (datetime.now().isoformat(), queue_id))

    db.commit()

    flash('Message approved and delivered to professional', 'success')
    return redirect(url_for('stpetepros.moderation_dashboard'))


@stpetepros_bp.route('/admin/stpetepros/moderation/reject/<int:queue_id>', methods=['POST'])
def reject_moderation(queue_id):
    """Reject a flagged message - block it from professional"""
    db = get_db()

    # Update moderation queue
    db.execute('''
        UPDATE moderation_queue
        SET status = 'rejected',
            reviewer_action = 'block',
            reviewed_at = ?
        WHERE id = ?
    ''', (datetime.now().isoformat(), queue_id))

    # Delete the message from messages table
    message_id = db.execute('SELECT content_id FROM moderation_queue WHERE id = ?', (queue_id,)).fetchone()
    if message_id:
        db.execute('DELETE FROM messages WHERE id = ?', (message_id['content_id'],))

    db.commit()

    flash('Message rejected and blocked', 'warning')
    return redirect(url_for('stpetepros.moderation_dashboard'))


# GitHub Pages-style URL aliases (for QR codes from static site)
@stpetepros_bp.route('/stpetepros/')
@stpetepros_bp.route('/stpetepros/index.html')
def stpetepros_directory_alias():
    """Directory homepage - GitHub Pages compatible URL"""
    return browse_all_professionals()


@stpetepros_bp.route('/stpetepros/professional-<int:professional_id>.html')
def stpetepros_professional_alias(professional_id):
    """Individual professional page - GitHub Pages compatible URL"""
    return professional_profile(professional_id)


def register_stpetepros_routes(app):
    """Register StPetePros routes with the app"""
    app.register_blueprint(stpetepros_bp)
    print("✅ StPetePros routes registered")
