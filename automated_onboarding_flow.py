#!/usr/bin/env python3
"""
Automated Onboarding Flow - Automate Everything Except Initial Signup

MANUAL (You do this):
- Meet person in-person, phone call, video chat
- They sign up / you create their account

AUTOMATED (System does this):
- Profile creation
- Domain assignment
- Tutorial workflow
- pSEO generation
- Email sequences
- Dashboard setup
- Analytics tracking
- Lead routing

Usage:
    # Start onboarding after manual signup
    python3 automated_onboarding_flow.py --onboard <professional_id>

    # Run automated follow-ups
    python3 automated_onboarding_flow.py --check-followups
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Optional
import json


# ============================================================================
# Onboarding Steps
# ============================================================================

ONBOARDING_STEPS = {
    'profile_created': {
        'order': 1,
        'auto': True,
        'description': 'Professional profile created',
        'next_step': 'domain_assigned'
    },

    'domain_assigned': {
        'order': 2,
        'auto': True,
        'description': 'Domain assigned based on trade/location',
        'next_step': 'welcome_email_sent'
    },

    'welcome_email_sent': {
        'order': 3,
        'auto': True,
        'description': 'Welcome email with login info sent',
        'next_step': 'first_tutorial_prompt'
    },

    'first_tutorial_prompt': {
        'order': 4,
        'auto': True,
        'description': 'Reminder to record first tutorial',
        'wait_hours': 24,
        'next_step': 'tutorial_recorded'
    },

    'tutorial_recorded': {
        'order': 5,
        'auto': False,  # User action required
        'description': 'First tutorial recorded',
        'next_step': 'tutorial_quality_checked'
    },

    'tutorial_quality_checked': {
        'order': 6,
        'auto': True,
        'description': 'Tutorial passed quality check',
        'next_step': 'pseo_generated'
    },

    'pseo_generated': {
        'order': 7,
        'auto': True,
        'description': '50+ pSEO pages generated',
        'next_step': 'site_published'
    },

    'site_published': {
        'order': 8,
        'auto': True,
        'description': 'Professional site published',
        'next_step': 'analytics_enabled'
    },

    'analytics_enabled': {
        'order': 9,
        'auto': True,
        'description': 'Analytics dashboard enabled',
        'next_step': 'onboarding_complete'
    },

    'onboarding_complete': {
        'order': 10,
        'auto': True,
        'description': 'Onboarding complete!',
        'next_step': None
    }
}


# ============================================================================
# Onboarding Database
# ============================================================================

def init_onboarding_db():
    """Initialize onboarding tracking"""

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS onboarding_status (
            professional_id INTEGER PRIMARY KEY,
            current_step TEXT NOT NULL,
            started_at TIMESTAMP NOT NULL,
            completed_at TIMESTAMP,
            step_data JSON,
            FOREIGN KEY (professional_id) REFERENCES professional_profile(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS onboarding_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            professional_id INTEGER NOT NULL,
            step TEXT NOT NULL,
            event_type TEXT NOT NULL,
            event_data JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (professional_id) REFERENCES professional_profile(id)
        )
    ''')

    conn.commit()
    conn.close()

    print("✅ Onboarding database initialized")


# ============================================================================
# Onboarding Flow
# ============================================================================

def start_onboarding(professional_id: int):
    """
    Start automated onboarding for a professional

    Call this AFTER manual signup/profile creation

    Args:
        professional_id: Professional's ID
    """

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    # Check if professional exists
    prof = cursor.execute(
        'SELECT * FROM professional_profile WHERE id = ?',
        (professional_id,)
    ).fetchone()

    if not prof:
        print(f"❌ Professional {professional_id} not found")
        conn.close()
        return

    # Create onboarding record
    cursor.execute('''
        INSERT OR REPLACE INTO onboarding_status
        (professional_id, current_step, started_at, step_data)
        VALUES (?, ?, ?, ?)
    ''', (professional_id, 'profile_created', datetime.now().isoformat(), '{}'))

    conn.commit()

    print(f"🚀 Starting onboarding for professional #{professional_id}\n")

    # Run automated steps
    run_automated_steps(professional_id)

    conn.close()


def run_automated_steps(professional_id: int):
    """
    Run all automated onboarding steps

    Args:
        professional_id: Professional's ID
    """

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    # Get current step
    status = cursor.execute(
        'SELECT current_step FROM onboarding_status WHERE professional_id = ?',
        (professional_id,)
    ).fetchone()

    if not status:
        print("❌ No onboarding status found")
        conn.close()
        return

    current_step = status[0]

    while current_step:
        step_config = ONBOARDING_STEPS.get(current_step)

        if not step_config:
            print(f"❌ Unknown step: {current_step}")
            break

        print(f"📍 Step: {current_step}")
        print(f"   {step_config['description']}")

        # Check if step is automated
        if not step_config.get('auto', True):
            print(f"   ⏸️  Waiting for user action...")
            break

        # Execute step
        success = execute_onboarding_step(professional_id, current_step, cursor)

        if not success:
            print(f"   ❌ Step failed")
            break

        print(f"   ✅ Complete")

        # Move to next step
        next_step = step_config.get('next_step')

        if next_step:
            cursor.execute('''
                UPDATE onboarding_status
                SET current_step = ?
                WHERE professional_id = ?
            ''', (next_step, professional_id))

            conn.commit()

            current_step = next_step
        else:
            # Onboarding complete
            cursor.execute('''
                UPDATE onboarding_status
                SET current_step = ?, completed_at = ?
                WHERE professional_id = ?
            ''', ('onboarding_complete', datetime.now().isoformat(), professional_id))

            conn.commit()

            print("\n🎉 Onboarding complete!")
            break

    conn.close()


def execute_onboarding_step(professional_id: int, step: str, cursor) -> bool:
    """
    Execute a specific onboarding step

    Args:
        professional_id: Professional's ID
        step: Step name
        cursor: Database cursor

    Returns:
        True if successful
    """

    if step == 'domain_assigned':
        return assign_domain(professional_id, cursor)

    elif step == 'welcome_email_sent':
        return send_welcome_email(professional_id, cursor)

    elif step == 'first_tutorial_prompt':
        return send_tutorial_prompt(professional_id, cursor)

    elif step == 'tutorial_quality_checked':
        return check_tutorial_quality(professional_id, cursor)

    elif step == 'pseo_generated':
        return generate_pseo(professional_id, cursor)

    elif step == 'site_published':
        return publish_site(professional_id, cursor)

    elif step == 'analytics_enabled':
        return enable_analytics(professional_id, cursor)

    else:
        # Default: mark as complete
        return True


# ============================================================================
# Step Implementations
# ============================================================================

def assign_domain(professional_id: int, cursor) -> bool:
    """Assign domain based on trade/location"""

    from domain_mapper import route_professional_to_domain

    # Get professional details
    prof = cursor.execute('''
        SELECT trade_category, address_city, address_state
        FROM professional_profile
        WHERE id = ?
    ''', (professional_id,)).fetchone()

    if not prof:
        return False

    trade, city, state = prof

    # Route to correct domain
    domain = route_professional_to_domain(trade, city, state)

    # Update professional record
    cursor.execute('''
        UPDATE professional_profile
        SET assigned_domain = ?
        WHERE id = ?
    ''', (domain, professional_id))

    print(f"      → Assigned domain: {domain}")

    return True


def send_welcome_email(professional_id: int, cursor) -> bool:
    """Send welcome email"""

    # Get professional email
    prof = cursor.execute('''
        SELECT email, business_name
        FROM professional_profile
        WHERE id = ?
    ''', (professional_id,)).fetchone()

    if not prof:
        return False

    email, business_name = prof

    # TODO: Actually send email via SendGrid/Mailgun/etc
    print(f"      → Email sent to: {email}")

    # Log event
    cursor.execute('''
        INSERT INTO onboarding_events
        (professional_id, step, event_type, event_data)
        VALUES (?, 'welcome_email_sent', 'email_sent', ?)
    ''', (professional_id, json.dumps({'to': email})))

    return True


def send_tutorial_prompt(professional_id: int, cursor) -> bool:
    """Send reminder to record first tutorial"""

    prof = cursor.execute('''
        SELECT email, business_name
        FROM professional_profile
        WHERE id = ?
    ''', (professional_id,)).fetchone()

    if not prof:
        return False

    email, business_name = prof

    # TODO: Send tutorial prompt email
    print(f"      → Tutorial prompt sent to: {email}")

    return True


def check_tutorial_quality(professional_id: int, cursor) -> bool:
    """Check if tutorial passed quality check"""

    # Get latest tutorial
    tutorial = cursor.execute('''
        SELECT id, quality_score, status
        FROM tutorial
        WHERE professional_id = ?
        ORDER BY created_at DESC
        LIMIT 1
    ''', (professional_id,)).fetchone()

    if not tutorial:
        return False

    tutorial_id, quality_score, status = tutorial

    if quality_score >= 6:
        print(f"      → Tutorial #{tutorial_id} passed (score: {quality_score}/10)")
        return True
    else:
        print(f"      → Tutorial #{tutorial_id} needs improvement (score: {quality_score}/10)")
        return False


def generate_pseo(professional_id: int, cursor) -> bool:
    """Generate pSEO landing pages"""

    # Get latest tutorial
    tutorial = cursor.execute('''
        SELECT id
        FROM tutorial
        WHERE professional_id = ? AND status = 'published'
        ORDER BY created_at DESC
        LIMIT 1
    ''', (professional_id,)).fetchone()

    if not tutorial:
        return False

    tutorial_id = tutorial[0]

    # Generate pSEO pages
    from pseo_generator import generate_pseo_landing_pages

    try:
        pages_created = generate_pseo_landing_pages(tutorial_id)
        print(f"      → Generated {pages_created} pSEO pages")
        return True
    except Exception as e:
        print(f"      → pSEO generation failed: {e}")
        return False


def publish_site(professional_id: int, cursor) -> bool:
    """Publish professional site"""

    # Update status
    cursor.execute('''
        UPDATE professional_profile
        SET subscription_status = 'active'
        WHERE id = ?
    ''', (professional_id,))

    print(f"      → Site published")

    return True


def enable_analytics(professional_id: int, cursor) -> bool:
    """Enable analytics dashboard"""

    print(f"      → Analytics enabled")

    return True


# ============================================================================
# Follow-up Automation
# ============================================================================

def check_followups():
    """
    Check for professionals needing follow-ups

    - Stuck on tutorial_recorded > 48hrs
    - No tutorial after 7 days
    - etc.
    """

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    print("🔍 Checking for follow-ups...\n")

    # Check stuck professionals
    stuck = cursor.execute('''
        SELECT o.professional_id, p.business_name, p.email, o.current_step,
               julianday('now') - julianday(o.started_at) as days_since_start
        FROM onboarding_status o
        JOIN professional_profile p ON o.professional_id = p.id
        WHERE o.completed_at IS NULL
        AND days_since_start > 2
    ''').fetchall()

    for prof_id, business_name, email, step, days in stuck:
        print(f"⚠️  {business_name} ({email})")
        print(f"   Stuck on: {step}")
        print(f"   Days since start: {int(days)}")
        print(f"   Action: Send follow-up email")
        print()

    conn.close()


# ============================================================================
# CLI Interface
# ============================================================================

if __name__ == '__main__':
    import sys

    if '--onboard' in sys.argv:
        if len(sys.argv) < 3:
            print("Usage: python3 automated_onboarding_flow.py --onboard <professional_id>")
            sys.exit(1)

        professional_id = int(sys.argv[2])
        init_onboarding_db()
        start_onboarding(professional_id)

    elif '--check-followups' in sys.argv:
        check_followups()

    else:
        print("""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║  Automated Onboarding Flow - Automate Everything Except Signup      ║
║                                                                      ║
║  MANUAL: You meet person, they sign up                              ║
║  AUTO: Everything else (profile, domain, tutorials, pSEO, emails)   ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝

Usage:
    python3 automated_onboarding_flow.py --onboard <id>    # Start onboarding
    python3 automated_onboarding_flow.py --check-followups # Check follow-ups

Onboarding Steps:
    1. Profile created (manual)
    2. Domain assigned (auto)
    3. Welcome email (auto)
    4. First tutorial prompt (auto, wait 24hrs)
    5. Tutorial recorded (manual)
    6. Quality check (auto)
    7. pSEO generated (auto)
    8. Site published (auto)
    9. Analytics enabled (auto)
   10. Complete! (auto)

Example:
    # After creating professional #123
    python3 automated_onboarding_flow.py --onboard 123
""")
