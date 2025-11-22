"""
Stock levels and ledger routes.

This module defines routes for Stock levels and ledger.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from utils.decorators import login_required, role_required
from config.database import get_db
from modules.stock.ledger_service import StockLedgerService
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

stock_bp = Blueprint('stock', __name__)
ledger_service = StockLedgerService()

@stock_bp.route('/levels')
@login_required
def view_stock_levels():
    """View current stock levels."""
    try:
        db = get_db()
        
        # Get filters
        product_id = request.args.get('product_id')
        warehouse_id = request.args.get('warehouse_id')
        
        # Build query
        query = {}
        if product_id:
            query['product_id'] = ObjectId(product_id)
        if warehouse_id:
            query['warehouse_id'] = ObjectId(warehouse_id)
            
        # Pagination
        page = int(request.args.get('page', 1))
        per_page = 20
        skip = (page - 1) * per_page
        
        # Get stock levels with product and warehouse details
        pipeline = [
            {'$match': query},
            {
                '$lookup': {
                    'from': 'products',
                    'localField': 'product_id',
                    'foreignField': '_id',
                    'as': 'product'
                }
            },
            {'$unwind': '$product'},
            {
                '$lookup': {
                    'from': 'warehouses',
                    'localField': 'warehouse_id',
                    'foreignField': '_id',
                    'as': 'warehouse'
                }
            },
            {'$unwind': '$warehouse'},
            {'$skip': skip},
            {'$limit': per_page}
        ]
        
        stock_levels = list(db.stock_levels.aggregate(pipeline))
        total = db.stock_levels.count_documents(query)
        
        # Get lists for filters
        products = list(db.products.find({'is_active': True}, {'name': 1}))
        warehouses = list(db.warehouses.find({'is_active': True}, {'name': 1}))
        
        pagination = {
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': (total + per_page - 1) // per_page
        }
        
        return render_template(
            'stock/levels.html',
            stock_levels=stock_levels,
            products=products,
            warehouses=warehouses,
            pagination=pagination
        )
        
    except Exception as e:
        logger.error(f"Error viewing stock levels: {e}")
        flash(f"Error loading stock levels: {str(e)}", 'danger')
        return redirect(url_for('dashboard.index'))

@stock_bp.route('/ledger')
@login_required
def view_ledger():
    """View stock ledger (transaction history)."""
    try:
        db = get_db()
        
        # Get filters
        filters = {
            'product_id': request.args.get('product_id'),
            'warehouse_id': request.args.get('warehouse_id'),
            'transaction_type': request.args.get('transaction_type'),
            'date_from': request.args.get('date_from'),
            'date_to': request.args.get('date_to')
        }
        
        # Pagination
        page = int(request.args.get('page', 1))
        per_page = 20
        
        # Get ledger entries using service
        # Fix: Use get_ledger_history instead of get_ledger_entries
        result = ledger_service.get_ledger_history(
            product_id=ObjectId(filters['product_id']) if filters['product_id'] else None,
            warehouse_id=ObjectId(filters['warehouse_id']) if filters['warehouse_id'] else None,
            page=page,
            per_page=per_page
        )
        
        # Get lists for filters
        products = list(db.products.find({'is_active': True}, {'name': 1}))
        warehouses = list(db.warehouses.find({'is_active': True}, {'name': 1}))
        
        return render_template(
            'stock/ledger.html',
            ledger_entries=result['entries'],
            pagination=result,
            products=products,
            warehouses=warehouses
        )
        
    except Exception as e:
        logger.error(f"Error viewing stock ledger: {e}")
        flash(f"Error loading stock ledger: {str(e)}", 'danger')
        return redirect(url_for('dashboard.index'))
