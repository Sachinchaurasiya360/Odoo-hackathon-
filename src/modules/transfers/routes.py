"""
Transfer routes.

This module defines routes for managing inter-warehouse transfers.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from modules.transfers.service import TransfersService
from utils.decorators import login_required, role_required
from utils.responses import success_response, error_response
from utils.constants import ROLE_ADMIN, ROLE_INVENTORY_MANAGER, ROLE_WAREHOUSE_STAFF
import logging

logger = logging.getLogger(__name__)

transfers_bp = Blueprint('transfers', __name__)
transfer_service = TransfersService()


@transfers_bp.route('/')
@login_required
def list_transfers():
    """List all transfers with filters."""
    page = request.args.get('page', 1, type=int)
    from_warehouse_id = request.args.get('from_warehouse_id')
    to_warehouse_id = request.args.get('to_warehouse_id')
    status = request.args.get('status')

    try:
        result = transfer_service.list_transfers(
            from_warehouse_id=from_warehouse_id,
            to_warehouse_id=to_warehouse_id,
            status=status,
            page=page,
            per_page=20
        )
        
        status_counts = transfer_service.get_status_counts()

        return render_template(
            'transfers/list.html',
            transfers=result['transfers'],
            pagination=result,
            current_from_warehouse=from_warehouse_id,
            current_to_warehouse=to_warehouse_id,
            current_status=status,
            status_counts=status_counts
        )

    except Exception as e:
        logger.error(f"Error listing transfers: {e}")
        flash('Error loading transfers', 'danger')
        return render_template('transfers/list.html', transfers=[], pagination={})


@transfers_bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required(ROLE_ADMIN, ROLE_INVENTORY_MANAGER, ROLE_WAREHOUSE_STAFF)
def create_transfer():
    """Create a new transfer."""
    if request.method == 'GET':
        return render_template('transfers/create.html')

    # Handle POST request
    try:
        from_warehouse_id = request.form.get('from_warehouse_id')
        to_warehouse_id = request.form.get('to_warehouse_id')
        scheduled_date = request.form.get('scheduled_date')
        notes = request.form.get('notes', '')

        # Parse items from form
        items = []
        item_count = int(request.form.get('item_count', 0))
        
        for i in range(item_count):
            product_id = request.form.get(f'items[{i}][product_id]')
            requested_quantity = request.form.get(f'items[{i}][requested_quantity]')
            
            if product_id and requested_quantity:
                items.append({
                    'product_id': product_id,
                    'requested_quantity': float(requested_quantity)
                })

        if not items:
            flash('At least one item is required', 'danger')
            return render_template('transfers/create.html')

        transfer = transfer_service.create_transfer(
            from_warehouse_id=from_warehouse_id,
            to_warehouse_id=to_warehouse_id,
            items=items,
            scheduled_date=scheduled_date,
            notes=notes,
            created_by=session.get('user_id')
        )

        flash(f"Transfer {transfer['transfer_number']} created successfully", 'success')
        return redirect(url_for('transfers.view_transfer', transfer_id=transfer['_id']))

    except ValueError as e:
        flash(str(e), 'danger')
        return render_template('transfers/create.html')
    except Exception as e:
        logger.error(f"Error creating transfer: {e}")
        flash(f'Error creating transfer: {str(e)}', 'danger')
        return render_template('transfers/create.html')


@transfers_bp.route('/<transfer_id>')
@login_required
def view_transfer(transfer_id):
    """View transfer details."""
    try:
        transfer = transfer_service.get_transfer(transfer_id)
        
        if not transfer:
            flash('Transfer not found', 'danger')
            return redirect(url_for('transfers.list_transfers'))

        return render_template('transfers/detail.html', transfer=transfer)

    except Exception as e:
        logger.error(f"Error viewing transfer: {e}")
        flash('Error loading transfer', 'danger')
        return redirect(url_for('transfers.list_transfers'))


@transfers_bp.route('/<transfer_id>/transition', methods=['POST'])
@login_required
@role_required(ROLE_ADMIN, ROLE_INVENTORY_MANAGER, ROLE_WAREHOUSE_STAFF)
def transition_transfer_status(transfer_id):
    """Transition transfer to new status."""
    try:
        new_status = request.form.get('status')
        
        if not new_status:
            flash('Status is required', 'danger')
            return redirect(url_for('transfers.view_transfer', transfer_id=transfer_id))

        transfer = transfer_service.transition_status(
            transfer_id=transfer_id,
            new_status=new_status,
            changed_by=session.get('user_id')
        )

        flash(f"Transfer transitioned to {new_status}", 'success')
        return redirect(url_for('transfers.view_transfer', transfer_id=transfer_id))

    except ValueError as e:
        flash(str(e), 'danger')
        return redirect(url_for('transfers.view_transfer', transfer_id=transfer_id))
    except Exception as e:
        logger.error(f"Error transitioning transfer status: {e}")
        flash('Error updating transfer status', 'danger')
        return redirect(url_for('transfers.view_transfer', transfer_id=transfer_id))


# API Endpoints
@transfers_bp.route('/api/transfers', methods=['GET'])
@login_required
def api_list_transfers():
    """API endpoint to list transfers."""
    try:
        page = request.args.get('page', 1, type=int)
        from_warehouse_id = request.args.get('from_warehouse_id')
        to_warehouse_id = request.args.get('to_warehouse_id')
        status = request.args.get('status')

        result = transfer_service.list_transfers(
            from_warehouse_id=from_warehouse_id,
            to_warehouse_id=to_warehouse_id,
            status=status,
            page=page,
            per_page=20
        )

        return success_response(result)

    except Exception as e:
        logger.error(f"API error listing transfers: {e}")
        return error_response(str(e))


@transfers_bp.route('/api/transfers/<transfer_id>', methods=['GET'])
@login_required
def api_get_transfer(transfer_id):
    """API endpoint to get transfer details."""
    try:
        transfer = transfer_service.get_transfer(transfer_id)
        
        if not transfer:
            return error_response('Transfer not found', status_code=404)

        return success_response(transfer)

    except Exception as e:
        logger.error(f"API error getting transfer: {e}")
        return error_response(str(e))
