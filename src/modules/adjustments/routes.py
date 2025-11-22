"""
Adjustment routes.

This module defines routes for managing stock adjustments.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from modules.adjustments.service import AdjustmentsService
from utils.decorators import login_required, role_required
from utils.responses import success_response, error_response
from utils.constants import ROLE_ADMIN, ROLE_INVENTORY_MANAGER
import logging

logger = logging.getLogger(__name__)

adjustments_bp = Blueprint('adjustments', __name__)
adjustment_service = AdjustmentsService()


@adjustments_bp.route('/')
@login_required
def list_adjustments():
    """List all adjustments with filters."""
    page = request.args.get('page', 1, type=int)
    warehouse_id = request.args.get('warehouse_id')
    status = request.args.get('status')
    adjustment_type = request.args.get('adjustment_type')

    try:
        result = adjustment_service.list_adjustments(
            warehouse_id=warehouse_id,
            status=status,
            adjustment_type=adjustment_type,
            page=page,
            per_page=20
        )
        
        status_counts = adjustment_service.get_status_counts(warehouse_id)

        return render_template(
            'adjustments/list.html',
            adjustments=result['adjustments'],
            pagination=result,
            current_warehouse=warehouse_id,
            current_status=status,
            current_type=adjustment_type,
            status_counts=status_counts
        )

    except Exception as e:
        logger.error(f"Error listing adjustments: {e}")
        flash('Error loading adjustments', 'danger')
        return render_template('adjustments/list.html', adjustments=[], pagination={})


@adjustments_bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required(ROLE_ADMIN, ROLE_INVENTORY_MANAGER)
def create_adjustment():
    """Create a new adjustment."""
    if request.method == 'GET':
        return render_template('adjustments/create.html')

    # Handle POST request
    try:
        warehouse_id = request.form.get('warehouse_id')
        product_id = request.form.get('product_id')
        physical_quantity = request.form.get('physical_quantity')
        adjustment_type = request.form.get('adjustment_type')
        adjustment_date = request.form.get('adjustment_date')
        reason = request.form.get('reason', '')
        notes = request.form.get('notes', '')

        adjustment = adjustment_service.create_adjustment(
            warehouse_id=warehouse_id,
            product_id=product_id,
            physical_quantity=float(physical_quantity),
            adjustment_type=adjustment_type,
            adjustment_date=adjustment_date,
            reason=reason,
            notes=notes,
            created_by=session.get('user_id')
        )

        flash(f"Adjustment {adjustment['adjustment_number']} created successfully", 'success')
        return redirect(url_for('adjustments.view_adjustment', adjustment_id=adjustment['_id']))

    except Exception as e:
        logger.error(f"Error creating adjustment: {e}")
        flash(f'Error creating adjustment: {str(e)}', 'danger')
        return render_template('adjustments/create.html')


@adjustments_bp.route('/<adjustment_id>')
@login_required
def view_adjustment(adjustment_id):
    """View adjustment details."""
    try:
        adjustment = adjustment_service.get_adjustment(adjustment_id)
        
        if not adjustment:
            flash('Adjustment not found', 'danger')
            return redirect(url_for('adjustments.list_adjustments'))

        return render_template('adjustments/detail.html', adjustment=adjustment)

    except Exception as e:
        logger.error(f"Error viewing adjustment: {e}")
        flash('Error loading adjustment', 'danger')
        return redirect(url_for('adjustments.list_adjustments'))


@adjustments_bp.route('/<adjustment_id>/approve', methods=['POST'])
@login_required
@role_required(ROLE_ADMIN, ROLE_INVENTORY_MANAGER)
def approve_adjustment(adjustment_id):
    """Approve an adjustment."""
    try:
        adjustment = adjustment_service.approve_adjustment(
            adjustment_id=adjustment_id,
            approved_by=session.get('user_id')
        )

        flash(f"Adjustment approved and stock updated", 'success')
        return redirect(url_for('adjustments.view_adjustment', adjustment_id=adjustment_id))

    except ValueError as e:
        flash(str(e), 'danger')
        return redirect(url_for('adjustments.view_adjustment', adjustment_id=adjustment_id))
    except Exception as e:
        logger.error(f"Error approving adjustment: {e}")
        flash('Error approving adjustment', 'danger')
        return redirect(url_for('adjustments.view_adjustment', adjustment_id=adjustment_id))


@adjustments_bp.route('/<adjustment_id>/cancel', methods=['POST'])
@login_required
@role_required(ROLE_ADMIN, ROLE_INVENTORY_MANAGER)
def cancel_adjustment(adjustment_id):
    """Cancel an adjustment."""
    try:
        adjustment = adjustment_service.cancel_adjustment(adjustment_id)

        flash(f"Adjustment cancelled", 'warning')
        return redirect(url_for('adjustments.view_adjustment', adjustment_id=adjustment_id))

    except ValueError as e:
        flash(str(e), 'danger')
        return redirect(url_for('adjustments.view_adjustment', adjustment_id=adjustment_id))
    except Exception as e:
        logger.error(f"Error cancelling adjustment: {e}")
        flash('Error cancelling adjustment', 'danger')
        return redirect(url_for('adjustments.view_adjustment', adjustment_id=adjustment_id))


# API Endpoints
@adjustments_bp.route('/api/adjustments', methods=['GET'])
@login_required
def api_list_adjustments():
    """API endpoint to list adjustments."""
    try:
        page = request.args.get('page', 1, type=int)
        warehouse_id = request.args.get('warehouse_id')
        status = request.args.get('status')

        result = adjustment_service.list_adjustments(
            warehouse_id=warehouse_id,
            status=status,
            page=page,
            per_page=20
        )

        return success_response(result)

    except Exception as e:
        logger.error(f"API error listing adjustments: {e}")
        return error_response(str(e))


@adjustments_bp.route('/api/adjustments/<adjustment_id>', methods=['GET'])
@login_required
def api_get_adjustment(adjustment_id):
    """API endpoint to get adjustment details."""
    try:
        adjustment = adjustment_service.get_adjustment(adjustment_id)
        
        if not adjustment:
            return error_response('Adjustment not found', status_code=404)

        return success_response(adjustment)

    except Exception as e:
        logger.error(f"API error getting adjustment: {e}")
        return error_response(str(e))
