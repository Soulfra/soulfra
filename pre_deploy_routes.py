#!/usr/bin/env python3
"""
Pre-Deployment Routes - Flask endpoints for deployment verification

Routes:
    /admin/deploy-ready - Admin dashboard showing deployment status
    /api/deploy/check - Run deployment checks (JSON)
    /api/deploy/qr - Get QR code with deployment status
"""

from flask import Blueprint, render_template, jsonify, request
from pre_deploy_check import PreDeployChecker

pre_deploy_bp = Blueprint('pre_deploy', __name__)


@pre_deploy_bp.route('/api/deploy/check')
def api_deploy_check():
    """
    Run all pre-deployment checks and return JSON

    Query params:
        quick: Set to 'true' to skip slow checks
    """
    quick_mode = request.args.get('quick', 'false').lower() == 'true'

    checker = PreDeployChecker()
    results = checker.run_all_checks(quick_mode=quick_mode)

    return jsonify(results)


@pre_deploy_bp.route('/api/deploy/qr')
def api_deploy_qr():
    """Get QR code with deployment status"""
    checker = PreDeployChecker()
    results = checker.run_all_checks(quick_mode=True)  # Quick mode for QR

    qr_code = checker.generate_qr_report()

    return jsonify({
        'success': True,
        'qr_code': qr_code,
        'status': results['overall_status'],
        'deploy_ready': results['deploy_ready']
    })


@pre_deploy_bp.route('/admin/deploy-ready')
def admin_deploy_ready():
    """Admin dashboard for pre-deployment verification"""
    return render_template('admin_deploy_ready.html')


def register_pre_deploy_routes(app):
    """Register pre-deployment routes"""
    app.register_blueprint(pre_deploy_bp)
    print("✅ Pre-deployment routes registered:")
    print("   - /admin/deploy-ready (Dashboard)")
    print("   - /api/deploy/check (Run checks)")
    print("   - /api/deploy/qr (QR code)")
