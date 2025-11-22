"""
Product and category management routes.

This module defines routes for Product and category management.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.decorators import login_required, role_required
from utils.responses import success_response, error_response
from config.database import get_db
from models.product import Product
from bson import ObjectId
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

products_bp = Blueprint('products', __name__)

@products_bp.route('/')
@login_required
def list_products():
    """List all products."""
    try:
        db = get_db()
        products = list(db.products.find({'is_active': True}))
        # Enrich with category names if needed, or do it in aggregation
        # For now, simple list
        return render_template('products/list.html', products=products)
    except Exception as e:
        logger.error(f"Error listing products: {e}")
        flash("Error loading products", "danger")
        return render_template('products/list.html', products=[])

@products_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_product():
    """Create a new product."""
    db = get_db()
    
    if request.method == 'POST':
        try:
            sku = request.form.get('sku')
            name = request.form.get('name')
            description = request.form.get('description')
            category_id = request.form.get('category_id')
            unit = request.form.get('unit')
            reorder_level = int(request.form.get('reorder_level', 0))
            is_active = request.form.get('is_active') == 'on'
            warehouse_id = request.form.get('warehouse_id')
            initial_stock = float(request.form.get('initial_stock', 0))
            
            # Check if SKU exists
            if db.products.find_one({'sku': sku}):
                flash(f"Product with SKU {sku} already exists", "danger")
                categories = list(db.categories.find())
                warehouses = list(db.warehouses.find({'is_active': True}))
                return render_template('products/create.html', categories=categories, warehouses=warehouses)
            
            product = Product(
                sku=sku,
                name=name,
                description=description,
                category_id=ObjectId(category_id) if category_id else None,
                unit=unit,
                reorder_level=reorder_level,
                is_active=is_active
            )
            
            result = db.products.insert_one(product.to_mongo())
            product_id = result.inserted_id
            
            # Handle initial stock if warehouse is selected
            if warehouse_id and initial_stock > 0:
                from modules.stock.ledger_service import StockLedgerService
                from utils.constants import TRANSACTION_TYPE_ADJUSTMENT
                
                ledger_service = StockLedgerService()
                ledger_service.record_transaction(
                    product_id=product_id,
                    warehouse_id=ObjectId(warehouse_id),
                    transaction_type=TRANSACTION_TYPE_ADJUSTMENT,
                    reference_type='Initial Stock',
                    reference_id=product_id,
                    reference_number=f'INIT-{sku}',
                    quantity_change=initial_stock,
                    created_by=ObjectId(session.get('user_id')),
                    notes=f'Initial stock for new product {name}'
                )
                flash(f"Product {name} created successfully with initial stock of {initial_stock} in selected warehouse", "success")
            else:
                flash(f"Product {name} created successfully", "success")
            
            return redirect(url_for('products.list_products'))
            
        except Exception as e:
            logger.error(f"Error creating product: {e}")
            flash(f"Error creating product: {str(e)}", "danger")
    
    # GET request
    categories = list(db.categories.find())
    warehouses = list(db.warehouses.find({'is_active': True}))
    return render_template('products/create.html', categories=categories, warehouses=warehouses)

@products_bp.route('/<product_id>')
@login_required
def view_product(product_id):
    """View product details."""
    try:
        db = get_db()
        
        # Get product
        product = db.products.find_one({'_id': ObjectId(product_id)})
        if not product:
            flash("Product not found", "danger")
            return redirect(url_for('products.list_products'))
        
        # Get category if exists
        category = None
        if product.get('category_id'):
            category = db.categories.find_one({'_id': product['category_id']})
        
        # Get stock by warehouse
        stock_pipeline = [
            {'$match': {'product_id': ObjectId(product_id)}},
            {
                '$lookup': {
                    'from': 'warehouses',
                    'localField': 'warehouse_id',
                    'foreignField': '_id',
                    'as': 'warehouse'
                }
            },
            {'$unwind': '$warehouse'},
            {
                '$project': {
                    'warehouse_name': '$warehouse.name',
                    'quantity': 1,
                    'reserved_quantity': 1
                }
            }
        ]
        stock_by_warehouse = list(db.stock_levels.aggregate(stock_pipeline))
        
        # Calculate total stock
        total_stock = sum(s.get('quantity', 0) for s in stock_by_warehouse)
        available_stock = sum(s.get('quantity', 0) - s.get('reserved_quantity', 0) for s in stock_by_warehouse)
        
        # Get recent movements
        movements_pipeline = [
            {'$match': {'product_id': ObjectId(product_id)}},
            {
                '$lookup': {
                    'from': 'warehouses',
                    'localField': 'warehouse_id',
                    'foreignField': '_id',
                    'as': 'warehouse'
                }
            },
            {'$unwind': '$warehouse'},
            {
                '$project': {
                    'transaction_type': 1,
                    'warehouse_name': '$warehouse.name',
                    'quantity_change': 1,
                    'quantity_after': 1,
                    'reference': 1,
                    'created_at': 1
                }
            },
            {'$sort': {'created_at': -1}},
            {'$limit': 10}
        ]
        recent_movements = list(db.stock_movements.aggregate(movements_pipeline))
        
        return render_template(
            'products/detail.html',
            product=product,
            category=category,
            stock_by_warehouse=stock_by_warehouse,
            total_stock=total_stock,
            available_stock=available_stock,
            recent_movements=recent_movements
        )
    except Exception as e:
        logger.error(f"Error viewing product: {e}")
        flash(f"Error loading product details: {str(e)}", "danger")
        return redirect(url_for('products.list_products'))

@products_bp.route('/<product_id>/edit', methods=['GET', 'POST'])
@login_required
def update_product(product_id):
    """Update product."""
    try:
        db = get_db()
        
        # Get existing product
        product = db.products.find_one({'_id': ObjectId(product_id)})
        if not product:
            flash("Product not found", "danger")
            return redirect(url_for('products.list_products'))
        
        if request.method == 'POST':
            sku = request.form.get('sku')
            name = request.form.get('name')
            description = request.form.get('description')
            category_id = request.form.get('category_id')
            unit = request.form.get('unit')
            reorder_level = int(request.form.get('reorder_level', 0))
            is_active = request.form.get('is_active') == 'on'
            
            # Check if SKU exists (excluding current product)
            existing = db.products.find_one({
                'sku': sku,
                '_id': {'$ne': ObjectId(product_id)}
            })
            if existing:
                flash(f"Product with SKU {sku} already exists", "danger")
                categories = list(db.categories.find())
                return render_template('products/edit.html', product=product, categories=categories)
            
            # Update product
            update_data = {
                'sku': sku,
                'name': name,
                'description': description,
                'category_id': ObjectId(category_id) if category_id else None,
                'unit': unit,
                'reorder_level': reorder_level,
                'is_active': is_active,
                'updated_at': datetime.utcnow()
            }
            
            db.products.update_one(
                {'_id': ObjectId(product_id)},
                {'$set': update_data}
            )
            
            flash(f"Product {name} updated successfully", "success")
            return redirect(url_for('products.view_product', product_id=product_id))
        
        # GET request
        categories = list(db.categories.find())
        return render_template('products/edit.html', product=product, categories=categories)
        
    except Exception as e:
        logger.error(f"Error updating product: {e}")
        flash(f"Error updating product: {str(e)}", "danger")
        return redirect(url_for('products.list_products'))

@products_bp.route('/<product_id>/delete', methods=['POST'])
@login_required
def delete_product(product_id):
    """Delete product."""
    try:
        db = get_db()
        
        # Check if product exists
        product = db.products.find_one({'_id': ObjectId(product_id)})
        if not product:
            flash("Product not found", "danger")
            return redirect(url_for('products.list_products'))
        
        # Check if product has stock
        stock_count = db.stock_levels.count_documents({'product_id': ObjectId(product_id)})
        if stock_count > 0:
            flash("Cannot delete product with existing stock records. Please remove all stock first.", "danger")
            return redirect(url_for('products.view_product', product_id=product_id))
        
        # Soft delete - mark as inactive
        db.products.update_one(
            {'_id': ObjectId(product_id)},
            {'$set': {'is_active': False, 'updated_at': datetime.utcnow()}}
        )
        
        flash(f"Product {product['name']} has been deactivated", "success")
        return redirect(url_for('products.list_products'))
        
    except Exception as e:
        logger.error(f"Error deleting product: {e}")
        flash(f"Error deleting product: {str(e)}", "danger")
        return redirect(url_for('products.list_products'))

