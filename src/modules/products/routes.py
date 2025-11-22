"""
Product and category management routes.

This module defines routes for Product and category management.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from utils.decorators import login_required, role_required
from utils.responses import success_response, error_response
from config.database import get_db
from models.product import Product
from bson import ObjectId
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
            
            # Check if SKU exists
            if db.products.find_one({'sku': sku}):
                flash(f"Product with SKU {sku} already exists", "danger")
                categories = list(db.categories.find())
                return render_template('products/create.html', categories=categories)
            
            product = Product(
                sku=sku,
                name=name,
                description=description,
                category_id=ObjectId(category_id) if category_id else None,
                unit=unit,
                reorder_level=reorder_level,
                is_active=is_active
            )
            
            db.products.insert_one(product.to_mongo())
            flash(f"Product {name} created successfully", "success")
            return redirect(url_for('products.list_products'))
            
        except Exception as e:
            logger.error(f"Error creating product: {e}")
            flash(f"Error creating product: {str(e)}", "danger")
    
    # GET request
    categories = list(db.categories.find())
    return render_template('products/create.html', categories=categories)

@products_bp.route('/<product_id>')
@login_required
def view_product(product_id):
    """View product details."""
    # TODO: Implement view logic
    return render_template('products/detail.html')

@products_bp.route('/<product_id>/edit', methods=['GET', 'POST'])
@login_required
def update_product(product_id):
    """Update product."""
    # TODO: Implement update logic
    return render_template('products/edit.html')

@products_bp.route('/<product_id>/delete', methods=['POST'])
@login_required
def delete_product(product_id):
    """Delete product."""
    # TODO: Implement delete logic
    flash("Product deletion not implemented yet", "warning")
    return redirect(url_for('products.list_products'))
