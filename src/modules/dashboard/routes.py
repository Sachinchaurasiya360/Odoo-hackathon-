"""
Dashboard routes.

This module provides the main dashboard with KPIs and metrics.
"""

from flask import Blueprint, render_template, request
from utils.decorators import login_required
from config.database import get_db
import logging

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    """Display main dashboard with KPIs."""
    try:
        db = get_db()
        
        # Calculate KPIs
        total_products = db.products.count_documents({'is_active': True})
        total_warehouses = db.warehouses.count_documents({'is_active': True})
        
        # Pending documents
        pending_receipts = db.receipts.count_documents({'status': {'$in': ['draft', 'waiting', 'ready']}})
        pending_deliveries = db.deliveries.count_documents({'status': {'$in': ['pick', 'pack', 'validate']}})
        pending_transfers = db.transfers.count_documents({'status': {'$in': ['draft', 'in_transit']}})
        
        # Low stock items (where quantity < reorder_level)
        pipeline = [
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
                '$match': {
                    '$expr': {'$lt': ['$quantity', '$product.reorder_level']}
                }
            },
            {'$count': 'low_stock_count'}
        ]
        
        low_stock_result = list(db.stock_levels.aggregate(pipeline))
        low_stock_items = low_stock_result[0]['low_stock_count'] if low_stock_result else 0
        
        # Recent movements (last 10)
        recent_movements = list(
            db.stock_ledger.find()
            .sort('transaction_date', -1)
            .limit(10)
        )
        
        # Total stock value (simplified - would need product prices)
        total_stock_qty = db.stock_levels.aggregate([
            {'$group': {'_id': None, 'total': {'$sum': '$quantity'}}}
        ])
        total_stock_qty = list(total_stock_qty)
        total_stock = total_stock_qty[0]['total'] if total_stock_qty else 0
        
        return render_template(
            'dashboard/index.html',
            total_products=total_products,
            total_warehouses=total_warehouses,
            pending_receipts=pending_receipts,
            pending_deliveries=pending_deliveries,
            pending_transfers=pending_transfers,
            low_stock_items=low_stock_items,
            total_stock=total_stock,
            recent_movements=recent_movements
        )
        
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return render_template('dashboard/index.html', error=str(e))
