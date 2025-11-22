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
    """Display main dashboard with KPIs and dynamic filters."""
    try:
        db = get_db()
        
        # Get filter parameters
        doc_type = request.args.get('doc_type', 'all')
        status_filter = request.args.get('status', 'all')
        warehouse_filter = request.args.get('warehouse', 'all')
        category_filter = request.args.get('category', 'all')
        
        # Calculate KPIs
        total_products = db.products.count_documents({'is_active': True})
        total_warehouses = db.warehouses.count_documents({'is_active': True})
        
        # Pending documents
        pending_receipts = db.receipts.count_documents({'status': {'$in': ['draft', 'waiting', 'ready']}})
        pending_deliveries = db.deliveries.count_documents({'status': {'$in': ['pick', 'pack', 'validate']}})
        pending_transfers = db.transfers.count_documents({'status': {'$in': ['draft', 'in_transit']}})
        pending_adjustments = db.adjustments.count_documents({'status': 'draft'})
        
        # Low stock items (where quantity < reorder_level and quantity > 0)
        low_stock_pipeline = [
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
                    '$and': [
                        {'$expr': {'$lt': ['$quantity', '$product.reorder_level']}},
                        {'$expr': {'$gt': ['$quantity', 0]}}
                    ]
                }
            },
            {'$count': 'low_stock_count'}
        ]
        
        low_stock_result = list(db.stock_levels.aggregate(low_stock_pipeline))
        low_stock_items = low_stock_result[0]['low_stock_count'] if low_stock_result else 0
        
        # Out of stock items (where quantity = 0)
        out_of_stock_items = db.stock_levels.count_documents({'quantity': 0})
        
        # Total stock value (simplified - would need product prices)
        total_stock_qty = db.stock_levels.aggregate([
            {'$group': {'_id': None, 'total': {'$sum': '$quantity'}}}
        ])
        total_stock_qty = list(total_stock_qty)
        total_stock = total_stock_qty[0]['total'] if total_stock_qty else 0
        
        # Build query for filtered movements
        movement_query = {}
        
        # Apply document type filter
        if doc_type != 'all':
            if doc_type == 'receipts':
                movement_query['reference_type'] = 'Receipt'
            elif doc_type == 'deliveries':
                movement_query['reference_type'] = 'Delivery'
            elif doc_type == 'transfers':
                movement_query['reference_type'] = 'Transfer'
            elif doc_type == 'adjustments':
                movement_query['reference_type'] = 'Adjustment'
        
        # Apply warehouse filter
        if warehouse_filter != 'all':
            from bson import ObjectId
            try:
                movement_query['warehouse_id'] = ObjectId(warehouse_filter)
            except:
                pass
        
        # Get recent movements with filters
        recent_movements_cursor = db.stock_ledger.find(movement_query).sort('transaction_date', -1).limit(20)
        recent_movements = list(recent_movements_cursor)
        
        # Enrich movements with product and warehouse names
        for movement in recent_movements:
            # Get product name
            product = db.products.find_one({'_id': movement.get('product_id')})
            movement['product_name'] = product.get('name', 'Unknown') if product else 'Unknown'
            
            # Get warehouse name
            warehouse = db.warehouses.find_one({'_id': movement.get('warehouse_id')})
            movement['warehouse_name'] = warehouse.get('name', 'Unknown') if warehouse else 'Unknown'
        
        # Apply status-based filtering for document counts
        if status_filter != 'all':
            status_query = {'status': status_filter}
            filtered_receipts = db.receipts.count_documents(status_query)
            filtered_deliveries = db.deliveries.count_documents(status_query)
            filtered_transfers = db.transfers.count_documents(status_query)
            filtered_adjustments = db.adjustments.count_documents(status_query)
        else:
            filtered_receipts = pending_receipts
            filtered_deliveries = pending_deliveries
            filtered_transfers = pending_transfers
            filtered_adjustments = pending_adjustments
        
        # Get all warehouses for filter dropdown
        warehouses = list(db.warehouses.find({'is_active': True}).sort('name', 1))
        
        # Get all categories for filter dropdown
        categories = list(db.products.aggregate([
            {'$match': {'is_active': True, 'category_id': {'$exists': True, '$ne': None}}},
            {'$lookup': {
                'from': 'products',
                'localField': 'category_id',
                'foreignField': '_id',
                'as': 'category'
            }},
            {'$unwind': {'path': '$category', 'preserveNullAndEmptyArrays': True}},
            {'$group': {'_id': '$category_id', 'name': {'$first': '$category.name'}}},
            {'$sort': {'name': 1}}
        ]))
        
        return render_template(
            'dashboard/index.html',
            total_products=total_products,
            total_warehouses=total_warehouses,
            pending_receipts=pending_receipts,
            pending_deliveries=pending_deliveries,
            pending_transfers=pending_transfers,
            pending_adjustments=pending_adjustments,
            filtered_receipts=filtered_receipts,
            filtered_deliveries=filtered_deliveries,
            filtered_transfers=filtered_transfers,
            filtered_adjustments=filtered_adjustments,
            low_stock_items=low_stock_items,
            out_of_stock_items=out_of_stock_items,
            total_stock=total_stock,
            recent_movements=recent_movements,
            warehouses=warehouses,
            categories=categories,
            doc_type=doc_type,
            status_filter=status_filter,
            warehouse_filter=warehouse_filter,
            category_filter=category_filter
        )
        
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return render_template('dashboard/index.html', error=str(e))
