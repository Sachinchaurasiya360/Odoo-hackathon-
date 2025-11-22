"""
Receipt routes.

This module defines routes for managing incoming inventory receipts.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from modules.receipts.service import ReceiptService
from utils.decorators import login_required, role_required
from utils.responses import success_response, error_response
from utils.constants import ROLE_ADMIN, ROLE_INVENTORY_MANAGER, ROLE_WAREHOUSE_STAFF
import logging

logger = logging.getLogger(__name__)

receipts_bp = Blueprint('receipts', __name__)
receipt_service = ReceiptService()


@receipts_bp.route('/')
@login_required
def list_receipts():
    """List all receipts with filters."""
    page = request.args.get('page', 1, type=int)
    warehouse_id = request.args.get('warehouse_id')
    status = request.args.get('status')

    try:
        result = receipt_service.list_receipts(
            warehouse_id=warehouse_id,
            status=status,
            page=page,
            per_page=20
        )

        return render_template(
            'receipts/list.html',
            receipts=result['receipts'],
            pagination=result,
            current_warehouse=warehouse_id,
            current_status=status
        )

    except Exception as e:
        logger.error(f"Error listing receipts: {e}")
        flash('Error loading receipts', 'danger')
        return render_template('receipts/list.html', receipts=[], pagination={})


@receipts_bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required(ROLE_ADMIN, ROLE_INVENTORY_MANAGER, ROLE_WAREHOUSE_STAFF)
def create_receipt():
    """Create a new receipt."""
    if request.method == 'GET':
        return render_template('receipts/create.html')

    # Handle POST request
    try:
        warehouse_id = request.form.get('warehouse_id')
        supplier_name = request.form.get('supplier_name')
        scheduled_date = request.form.get('scheduled_date')
        notes = request.form.get('notes', '')

        # Parse items from form
        items = []
        item_count = int(request.form.get('item_count', 0))
        
        for i in range(item_count):
            product_id = request.form.get(f'items[{i}][product_id]')
            expected_quantity = request.form.get(f'items[{i}][expected_quantity]')
            unit_price = request.form.get(f'items[{i}][unit_price]', 0)
            
            if product_id and expected_quantity:
                items.append({
                    'product_id': product_id,
                    'expected_quantity': float(expected_quantity),
                    'unit_price': float(unit_price) if unit_price else 0
                })

        if not items:
            flash('At least one item is required', 'danger')
            return render_template('receipts/create.html')

        receipt = receipt_service.create_receipt(
            warehouse_id=warehouse_id,
            supplier_name=supplier_name,
            items=items,
            scheduled_date=scheduled_date,
            notes=notes,
            created_by=request.user_id
        )

        flash(f"Receipt {receipt['receipt_number']} created successfully", 'success')
        return redirect(url_for('receipts.view_receipt', receipt_id=receipt['_id']))

    except Exception as e:
        logger.error(f"Error creating receipt: {e}")
        flash(f'Error creating receipt: {str(e)}', 'danger')
        return render_template('receipts/create.html')


@receipts_bp.route('/<receipt_id>')
@login_required
def view_receipt(receipt_id):
    """View receipt details."""
    try:
        receipt = receipt_service.get_receipt(receipt_id)
        
        if not receipt:
            flash('Receipt not found', 'danger')
            return redirect(url_for('receipts.list_receipts'))

        return render_template('receipts/detail.html', receipt=receipt)

    except Exception as e:
        logger.error(f"Error viewing receipt: {e}")
        flash('Error loading receipt', 'danger')
        return redirect(url_for('receipts.list_receipts'))


@receipts_bp.route('/<receipt_id>/transition', methods=['POST'])
@login_required
@role_required(ROLE_ADMIN, ROLE_INVENTORY_MANAGER, ROLE_WAREHOUSE_STAFF)
def transition_receipt(receipt_id):
    """Transition receipt to new status."""
    try:
        new_status = request.form.get('new_status')
        
        if not new_status:
            flash('Status is required', 'danger')
            return redirect(url_for('receipts.view_receipt', receipt_id=receipt_id))

        # Get received quantities if transitioning to done
        received_quantities = {}
        if new_status == 'done':
            for key, value in request.form.items():
                if key.startswith('received_qty_'):
                    product_id = key.replace('received_qty_', '')
                    received_quantities[product_id] = float(value)

        receipt = receipt_service.transition_status(
            receipt_id=receipt_id,
            new_status=new_status,
            changed_by=request.user_id,
            received_quantities=received_quantities
        )

        flash(f"Receipt transitioned to {new_status}", 'success')
        return redirect(url_for('receipts.view_receipt', receipt_id=receipt_id))

    except ValueError as e:
        flash(str(e), 'danger')
        return redirect(url_for('receipts.view_receipt', receipt_id=receipt_id))
    except Exception as e:
        logger.error(f"Error transitioning receipt: {e}")
        flash('Error updating receipt status', 'danger')
        return redirect(url_for('receipts.view_receipt', receipt_id=receipt_id))


# API Endpoints

@receipts_bp.route('/api/receipts', methods=['GET'])
@login_required
def api_list_receipts():
    """API endpoint to list receipts."""
    page = request.args.get('page', 1, type=int)
    warehouse_id = request.args.get('warehouse_id')
    status = request.args.get('status')

    try:
        result = receipt_service.list_receipts(
            warehouse_id=warehouse_id,
            status=status,
            page=page,
            per_page=20
        )

        return success_response(result)

    except Exception as e:
        logger.error(f"API error listing receipts: {e}")
        return error_response("Error loading receipts", status_code=500)


@receipts_bp.route('/api/receipts', methods=['POST'])
@login_required
@role_required(ROLE_ADMIN, ROLE_INVENTORY_MANAGER, ROLE_WAREHOUSE_STAFF)
def api_create_receipt():
    """API endpoint to create receipt."""
    data = request.get_json()
    
    if not data:
        return error_response("Invalid request data", status_code=400)

    try:
        receipt = receipt_service.create_receipt(
            warehouse_id=data.get('warehouse_id'),
            supplier_name=data.get('supplier_name'),
            items=data.get('items', []),
            scheduled_date=data.get('scheduled_date'),
            notes=data.get('notes', ''),
            created_by=request.user_id
        )

        return success_response(receipt, "Receipt created successfully", status_code=201)

    except Exception as e:
        logger.error(f"API error creating receipt: {e}")
        return error_response(str(e), status_code=400)


@receipts_bp.route('/api/receipts/<receipt_id>', methods=['GET'])
@login_required
def api_get_receipt(receipt_id):
    """API endpoint to get receipt details."""
    try:
        receipt = receipt_service.get_receipt(receipt_id)
        
        if not receipt:
            return error_response("Receipt not found", status_code=404)

        return success_response(receipt)

    except Exception as e:
        logger.error(f"API error getting receipt: {e}")
        return error_response("Error loading receipt", status_code=500)
