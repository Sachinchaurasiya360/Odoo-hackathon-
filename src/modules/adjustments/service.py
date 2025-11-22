"""
Adjustment Service - Manages stock adjustments for corrections.

This service implements the adjustment workflow:
Draft → Approved

Stock is automatically adjusted (increased or decreased) when approved
based on the difference between physical_quantity and system_quantity.
"""

from datetime import datetime
from bson import ObjectId

from config.database import get_db
from models.adjustment import Adjustment
from modules.stock.ledger_service import StockLedgerService
from modules.stock.service import StockService
from utils.constants import (
    ADJUSTMENT_STATUS_DRAFT,
    ADJUSTMENT_STATUS_APPROVED,
    ADJUSTMENT_STATUS_CANCELLED,
    TRANSACTION_TYPE_ADJUSTMENT,
    ADJUSTMENT_TYPE_PHYSICAL_COUNT
)
import logging

logger = logging.getLogger(__name__)


class AdjustmentsService:
    """Service for managing adjustment operations."""

    def __init__(self):
        """Initialize AdjustmentsService."""
        self.db = get_db()
        self.collection = self.db.adjustments
        self.ledger_service = StockLedgerService()
        self.stock_service = StockService()

    def create_adjustment(self, warehouse_id, product_id, physical_quantity,
                         adjustment_type=ADJUSTMENT_TYPE_PHYSICAL_COUNT,
                         adjustment_date=None, reason='', notes='', created_by=None):
        """
        Create a new adjustment in draft status.

        Args:
            warehouse_id (str or ObjectId): Warehouse ID.
            product_id (str or ObjectId): Product ID.
            physical_quantity (float): Physically counted quantity.
            adjustment_type (str): Type of adjustment.
            adjustment_date (datetime, optional): Adjustment date.
            reason (str): Reason for adjustment.
            notes (str): Additional notes.
            created_by (str or ObjectId): User ID.

        Returns:
            dict: Created adjustment data.
        """
        if isinstance(warehouse_id, str):
            warehouse_id = ObjectId(warehouse_id)
        if isinstance(product_id, str):
            product_id = ObjectId(product_id)
        if isinstance(created_by, str):
            created_by = ObjectId(created_by)

        # Get current system quantity
        system_quantity = self.stock_service.get_stock_level(
            product_id=product_id,
            warehouse_id=warehouse_id
        )

        # Generate adjustment number
        adjustment_number = self._generate_adjustment_number()

        # Create adjustment
        adjustment = Adjustment(
            adjustment_number=adjustment_number,
            warehouse_id=warehouse_id,
            product_id=product_id,
            adjustment_type=adjustment_type,
            status=ADJUSTMENT_STATUS_DRAFT,
            adjustment_date=adjustment_date or datetime.utcnow(),
            system_quantity=system_quantity,
            physical_quantity=physical_quantity,
            reason=reason,
            notes=notes,
            created_by=created_by
        )

        # Insert into database
        self.collection.insert_one(adjustment.to_mongo())

        logger.info(f"Adjustment created: {adjustment_number}, Diff: {adjustment.difference}")

        return adjustment.to_dict()

    def approve_adjustment(self, adjustment_id, approved_by):
        """
        Approve adjustment and apply stock correction.

        Args:
            adjustment_id (str or ObjectId): Adjustment ID.
            approved_by (str or ObjectId): User ID approving the adjustment.

        Returns:
            dict: Updated adjustment data.
        """
        if isinstance(adjustment_id, str):
            adjustment_id = ObjectId(adjustment_id)
        if isinstance(approved_by, str):
            approved_by = ObjectId(approved_by)

        adjustment_doc = self.collection.find_one({'_id': adjustment_id})
        if not adjustment_doc:
            raise ValueError("Adjustment not found")

        adjustment = Adjustment.from_mongo(adjustment_doc)

        if not adjustment.can_transition_to(ADJUSTMENT_STATUS_APPROVED):
            raise ValueError(
                f"Cannot approve adjustment in {adjustment.status} status"
            )

        # Apply stock adjustment
        if adjustment.difference != 0:
            self.ledger_service.record_transaction(
                product_id=adjustment.product_id,
                warehouse_id=adjustment.warehouse_id,
                transaction_type=TRANSACTION_TYPE_ADJUSTMENT,
                reference_type='Adjustment',
                reference_id=adjustment._id,
                reference_number=adjustment.adjustment_number,
                quantity_change=adjustment.difference,  # Positive or negative
                created_by=approved_by,
                notes=f"Stock adjustment: {adjustment.reason or adjustment.adjustment_type}"
            )

            logger.info(
                f"Stock adjusted: Product {adjustment.product_id}, "
                f"Warehouse {adjustment.warehouse_id}, Diff {adjustment.difference}"
            )

        # Update adjustment status
        adjustment.status = ADJUSTMENT_STATUS_APPROVED
        adjustment.approved_by = approved_by
        adjustment.updated_at = datetime.utcnow()

        self.collection.update_one(
            {'_id': adjustment_id},
            {'$set': adjustment.to_mongo()}
        )

        logger.info(f"Adjustment {adjustment.adjustment_number} approved")

        return adjustment.to_dict()

    def cancel_adjustment(self, adjustment_id):
        """
        Cancel an adjustment.

        Args:
            adjustment_id (str or ObjectId): Adjustment ID.

        Returns:
            dict: Updated adjustment data.
        """
        if isinstance(adjustment_id, str):
            adjustment_id = ObjectId(adjustment_id)

        adjustment_doc = self.collection.find_one({'_id': adjustment_id})
        if not adjustment_doc:
            raise ValueError("Adjustment not found")

        adjustment = Adjustment.from_mongo(adjustment_doc)

        if not adjustment.can_transition_to(ADJUSTMENT_STATUS_CANCELLED):
            raise ValueError(
                f"Cannot cancel adjustment in {adjustment.status} status"
            )

        adjustment.status = ADJUSTMENT_STATUS_CANCELLED
        adjustment.updated_at = datetime.utcnow()

        self.collection.update_one(
            {'_id': adjustment_id},
            {'$set': adjustment.to_mongo()}
        )

        logger.info(f"Adjustment {adjustment.adjustment_number} cancelled")

        return adjustment.to_dict()

    def get_adjustment(self, adjustment_id):
        """Get adjustment by ID with enriched data."""
        if isinstance(adjustment_id, str):
            adjustment_id = ObjectId(adjustment_id)

        adjustment_doc = self.collection.find_one({'_id': adjustment_id})
        if not adjustment_doc:
            return None

        adjustment = Adjustment.from_mongo(adjustment_doc)
        adjustment_dict = adjustment.to_dict()

        # Enrich with warehouse name
        warehouse = self.db.warehouses.find_one({'_id': adjustment.warehouse_id})
        if warehouse:
            adjustment_dict['warehouse_name'] = warehouse['name']

        # Enrich with product details
        product = self.db.products.find_one({'_id': adjustment.product_id})
        if product:
            adjustment_dict['product_name'] = product['name']
            adjustment_dict['product_sku'] = product['sku']

        return adjustment_dict

    def list_adjustments(self, warehouse_id=None, product_id=None, 
                        status=None, adjustment_type=None, page=1, per_page=20):
        """List adjustments with filters and pagination."""
        query = {}
        if warehouse_id:
            query['warehouse_id'] = ObjectId(warehouse_id) if isinstance(warehouse_id, str) else warehouse_id
        if product_id:
            query['product_id'] = ObjectId(product_id) if isinstance(product_id, str) else product_id
        if status:
            query['status'] = status
        if adjustment_type:
            query['adjustment_type'] = adjustment_type

        total = self.collection.count_documents(query)
        skip = (page - 1) * per_page
        total_pages = (total + per_page - 1) // per_page

        adjustments = list(
            self.collection.find(query)
            .sort('created_at', -1)
            .skip(skip)
            .limit(per_page)
        )

        adjustment_list = []
        for adjustment_doc in adjustments:
            adjustment = Adjustment.from_mongo(adjustment_doc)
            adjustment_dict = adjustment.to_dict()

            # Add warehouse name
            warehouse = self.db.warehouses.find_one({'_id': adjustment.warehouse_id})
            if warehouse:
                adjustment_dict['warehouse_name'] = warehouse['name']

            # Add product details
            product = self.db.products.find_one({'_id': adjustment.product_id})
            if product:
                adjustment_dict['product_name'] = product['name']
                adjustment_dict['product_sku'] = product['sku']

            adjustment_list.append(adjustment_dict)

        return {
            'adjustments': adjustment_list,
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': total_pages
        }

    def get_status_counts(self, warehouse_id=None):
        """Get count of adjustments by status."""
        query = {}
        if warehouse_id:
            query['warehouse_id'] = ObjectId(warehouse_id) if isinstance(warehouse_id, str) else warehouse_id

        pipeline = [
            {'$match': query},
            {'$group': {'_id': '$status', 'count': {'$sum': 1}}}
        ]

        result = list(self.collection.aggregate(pipeline))
        return {item['_id']: item['count'] for item in result}

    def _generate_adjustment_number(self):
        """Generate unique adjustment number."""
        year = datetime.utcnow().year
        prefix = f"ADJ-{year}-"

        last_adjustment = self.collection.find_one(
            {'adjustment_number': {'$regex': f'^{prefix}'}},
            sort=[('adjustment_number', -1)]
        )

        if last_adjustment:
            last_num = int(last_adjustment['adjustment_number'].split('-')[-1])
            next_num = last_num + 1
        else:
            next_num = 1

        return f"{prefix}{next_num:04d}"
