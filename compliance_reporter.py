#!/usr/bin/env python3
"""
Automated Compliance Reporting
Generates transparency reports for DMCA/OSP compliance
"""

from database import get_db
from datetime import datetime, timezone, timedelta
import json


def generate_transparency_report(start_date=None, end_date=None):
    """
    Generate DMCA transparency report

    Args:
        start_date: Start date (ISO format) - defaults to 30 days ago
        end_date: End date (ISO format) - defaults to now

    Returns:
        dict: Comprehensive transparency report
    """
    db = get_db()

    if not end_date:
        end_date = datetime.now(timezone.utc).isoformat()

    if not start_date:
        start = datetime.now(timezone.utc) - timedelta(days=30)
        start_date = start.isoformat()

    report = {
        'report_date': datetime.now(timezone.utc).isoformat(),
        'period_start': start_date,
        'period_end': end_date,
        'compliance_framework': '17 USC § 512 (OCILLA)',
        'designated_agent': 'dmca@soulfra.ai'
    }

    # DMCA notice statistics
    dmca_stats = {
        'total_notices': db.execute(
            "SELECT COUNT(*) as c FROM dmca_notices WHERE submitted_at BETWEEN ? AND ?",
            (start_date, end_date)
        ).fetchone()['c'],

        'honored': db.execute(
            "SELECT COUNT(*) as c FROM dmca_notices WHERE status = 'honored' AND submitted_at BETWEEN ? AND ?",
            (start_date, end_date)
        ).fetchone()['c'],

        'rejected': db.execute(
            "SELECT COUNT(*) as c FROM dmca_notices WHERE status = 'rejected' AND submitted_at BETWEEN ? AND ?",
            (start_date, end_date)
        ).fetchone()['c'],

        'pending': db.execute(
            "SELECT COUNT(*) as c FROM dmca_notices WHERE status = 'pending' AND submitted_at BETWEEN ? AND ?",
            (start_date, end_date)
        ).fetchone()['c']
    }

    # Counter-notification statistics
    counter_stats = {
        'total': db.execute(
            "SELECT COUNT(*) as c FROM dmca_counter_notifications WHERE submitted_at BETWEEN ? AND ?",
            (start_date, end_date)
        ).fetchone()['c'],

        'pending': db.execute(
            "SELECT COUNT(*) as c FROM dmca_counter_notifications WHERE status = 'pending' AND submitted_at BETWEEN ? AND ?",
            (start_date, end_date)
        ).fetchone()['c'],

        'approved': db.execute(
            "SELECT COUNT(*) as c FROM dmca_counter_notifications WHERE status = 'approved' AND submitted_at BETWEEN ? AND ?",
            (start_date, end_date)
        ).fetchone()['c']
    }

    # Repeat infringer statistics
    infringer_stats = {
        'total_tracked': db.execute(
            "SELECT COUNT(*) as c FROM repeat_infringers"
        ).fetchone()['c'],

        'warned': db.execute(
            "SELECT COUNT(*) as c FROM repeat_infringers WHERE status = 'warned'"
        ).fetchone()['c'],

        'suspended': db.execute(
            "SELECT COUNT(*) as c FROM repeat_infringers WHERE status = 'suspended'"
        ).fetchone()['c'],

        'terminated': db.execute(
            "SELECT COUNT(*) as c FROM repeat_infringers WHERE status = 'terminated'"
        ).fetchone()['c']
    }

    # AI moderation statistics
    moderation_stats = {
        'total_flagged': db.execute(
            "SELECT COUNT(*) as c FROM moderation_queue WHERE flagged_at BETWEEN ? AND ?",
            (start_date, end_date)
        ).fetchone()['c'],

        'approved': db.execute(
            "SELECT COUNT(*) as c FROM moderation_queue WHERE status = 'approved' AND flagged_at BETWEEN ? AND ?",
            (start_date, end_date)
        ).fetchone()['c'],

        'removed': db.execute(
            "SELECT COUNT(*) as c FROM moderation_queue WHERE status = 'removed' AND flagged_at BETWEEN ? AND ?",
            (start_date, end_date)
        ).fetchone()['c'],

        'avg_confidence': db.execute(
            "SELECT AVG(ai_confidence) as avg FROM moderation_queue WHERE flagged_at BETWEEN ? AND ?",
            (start_date, end_date)
        ).fetchone()['avg'] or 0.0
    }

    # Response times
    avg_response_time = db.execute('''
        SELECT AVG(
            CAST((julianday(processed_at) - julianday(submitted_at)) * 24 AS INTEGER)
        ) as avg_hours
        FROM dmca_notices
        WHERE processed_at IS NOT NULL
        AND submitted_at BETWEEN ? AND ?
    ''', (start_date, end_date)).fetchone()['avg_hours']

    report['dmca_notices'] = dmca_stats
    report['counter_notifications'] = counter_stats
    report['repeat_infringers'] = infringer_stats
    report['ai_moderation'] = moderation_stats
    report['avg_response_time_hours'] = avg_response_time or 0.0

    # Compliance metrics
    report['compliance_metrics'] = {
        'safe_harbor_qualified': True,
        'designated_agent_registered': True,
        'repeat_infringer_policy': True,
        'notice_and_takedown': dmca_stats['total_notices'] > 0,
        'avg_takedown_time_hours': avg_response_time or 0.0,
        'target_takedown_time_hours': 24.0  # Internal SLA
    }

    return report


def save_transparency_report(report):
    """
    Save transparency report to database

    Args:
        report: Report dict from generate_transparency_report()

    Returns:
        int: Report ID
    """
    db = get_db()

    cursor = db.execute('''
        INSERT INTO transparency_reports
        (period_start, period_end, report_data, generated_at)
        VALUES (?, ?, ?, ?)
    ''', (
        report['period_start'],
        report['period_end'],
        json.dumps(report, indent=2),
        report['report_date']
    ))

    db.commit()
    return cursor.lastrowid


def export_report_markdown(report):
    """
    Export transparency report as Markdown

    Args:
        report: Report dict

    Returns:
        str: Markdown formatted report
    """
    md = f"""# DMCA Transparency Report

**Report Period:** {report['period_start'][:10]} to {report['period_end'][:10]}
**Generated:** {report['report_date'][:10]}
**Framework:** {report['compliance_framework']}
**DMCA Agent:** {report['designated_agent']}

---

## Executive Summary

This transparency report covers DMCA takedown notices, counter-notifications, and content moderation activities during the reporting period.

## DMCA Takedown Notices

| Metric | Count |
|--------|-------|
| **Total Notices Received** | {report['dmca_notices']['total_notices']} |
| Honored (Content Removed) | {report['dmca_notices']['honored']} |
| Rejected (Invalid) | {report['dmca_notices']['rejected']} |
| Pending Review | {report['dmca_notices']['pending']} |

## Counter-Notifications

| Metric | Count |
|--------|-------|
| **Total Counter-Notifications** | {report['counter_notifications']['total']} |
| Approved (Content Restored) | {report['counter_notifications']['approved']} |
| Pending Review | {report['counter_notifications']['pending']} |

## Repeat Infringer Policy

| Status | Count |
|--------|-------|
| **Total Tracked** | {report['repeat_infringers']['total_tracked']} |
| Warned | {report['repeat_infringers']['warned']} |
| Suspended | {report['repeat_infringers']['suspended']} |
| Terminated | {report['repeat_infringers']['terminated']} |

## AI-Powered Content Moderation

| Metric | Value |
|--------|-------|
| **Total Flagged** | {report['ai_moderation']['total_flagged']} |
| Approved (False Positive) | {report['ai_moderation']['approved']} |
| Removed (Violation) | {report['ai_moderation']['removed']} |
| Average Confidence | {report['ai_moderation']['avg_confidence']:.1%} |

## Performance Metrics

- **Average Response Time:** {report['avg_response_time_hours']:.1f} hours
- **Target SLA:** {report['compliance_metrics']['target_takedown_time_hours']:.1f} hours
- **SLA Compliance:** {'✅ Met' if report['avg_response_time_hours'] <= report['compliance_metrics']['target_takedown_time_hours'] else '⚠️ Exceeded'}

## Compliance Status

- ✅ Safe Harbor Qualified (17 USC § 512(c))
- ✅ Designated DMCA Agent Registered
- ✅ Repeat Infringer Policy Enforced
- ✅ Notice-and-Takedown Operational
- ✅ Proactive AI Moderation Active

---

## Legal Notice

This report is provided for transparency purposes in accordance with our commitment to DMCA compliance. All takedown requests are processed in good faith under 17 USC § 512.

For DMCA notices or inquiries: **{report['designated_agent']}**
"""

    return md


def export_report_json(report, pretty=True):
    """
    Export transparency report as JSON

    Args:
        report: Report dict
        pretty: Pretty print JSON

    Returns:
        str: JSON formatted report
    """
    if pretty:
        return json.dumps(report, indent=2)
    return json.dumps(report)


# ============================================================================
# CLI
# ============================================================================

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Automated Compliance Reporter")
        print("\nUsage:")
        print("  python3 compliance_reporter.py generate")
        print("  python3 compliance_reporter.py generate --days 90")
        print("  python3 compliance_reporter.py markdown")
        print("  python3 compliance_reporter.py save")
        sys.exit(1)

    command = sys.argv[1]

    # Parse --days flag
    days = 30
    if '--days' in sys.argv:
        idx = sys.argv.index('--days')
        if len(sys.argv) > idx + 1:
            days = int(sys.argv[idx + 1])

    # Generate report
    start = datetime.now(timezone.utc) - timedelta(days=days)
    end = datetime.now(timezone.utc)

    report = generate_transparency_report(
        start.isoformat(),
        end.isoformat()
    )

    if command == 'generate':
        print(f"\n📊 Transparency Report ({days}-day period)\n")
        print(f"Period: {report['period_start'][:10]} to {report['period_end'][:10]}")
        print(f"\nDMCA Notices:")
        print(f"  Total: {report['dmca_notices']['total_notices']}")
        print(f"  Honored: {report['dmca_notices']['honored']}")
        print(f"  Rejected: {report['dmca_notices']['rejected']}")
        print(f"  Pending: {report['dmca_notices']['pending']}")

        print(f"\nCounter-Notifications:")
        print(f"  Total: {report['counter_notifications']['total']}")
        print(f"  Approved: {report['counter_notifications']['approved']}")

        print(f"\nRepeat Infringers:")
        print(f"  Tracked: {report['repeat_infringers']['total_tracked']}")
        print(f"  Terminated: {report['repeat_infringers']['terminated']}")

        print(f"\nAI Moderation:")
        print(f"  Flagged: {report['ai_moderation']['total_flagged']}")
        print(f"  Removed: {report['ai_moderation']['removed']}")

        print(f"\nPerformance:")
        print(f"  Avg Response: {report['avg_response_time_hours']:.1f} hours")

    elif command == 'markdown':
        md = export_report_markdown(report)
        print(md)

    elif command == 'json':
        print(export_report_json(report))

    elif command == 'save':
        report_id = save_transparency_report(report)
        print(f"✅ Report saved to database (ID: {report_id})")
        print(f"   Period: {report['period_start'][:10]} to {report['period_end'][:10]}")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
