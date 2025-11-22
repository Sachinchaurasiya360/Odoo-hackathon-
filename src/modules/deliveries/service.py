"""
Delivery Service - Manages outgoing inventory deliveries.

This service implements the delivery workflow:
Draft → Pick → Pack → Validate → Done

Stock decreases occur when transitioning to 'Done' status.
"""

from datetime import datetime
from bson import ObjectId

from config.database import get_db
from models.delivery import Delivery, DeliveryItem
from modules.stock.ledger_service import StockLedgerService
from utils.constants import (
    DELIVERY_STATUS_DRAFT, DELIVERY_STATUS_PICK,
    DELIVERY_STATUS_PACK, DELIVERY_STATUS_VALIDATE,
    DELIVERY_STATUS_DONE, DELIVERY_STATUS_CANCELLED,
    TRANSACTION_TYPE_DELIVERY
)
import logging

logger = logging.getLogger(__name__)


class DeliveryService:
    """Service for managing delivery operations."""

    def __init__(self):
        """Initialize DeliveryService."""
        self.db = get_db()
        self.ledger_service = StockLedgerService()

    def create_delivery(self, warehouse_id, customer_name, items,
                       scheduled_date=None, customer_address='', notes='', created_by=None):
        """
        Create a new delivery in draft status.

        Args:
            warehouse_id (str or ObjectId): Warehouse ID.
            customer_name (str): Customer name.
            items (list): List of item dictionaries.
            scheduled_date (datetime, optional): Scheduled delivery date.
            customer_address (str): Customer address.
            notes (str): Delivery notes.
            created_by (str or ObjectId): User ID.

        Returns:
            dict: Created delivery data.
        """
        if isinstance(warehouse_id, str):
            warehouse_id = ObjectId(warehouse_id)
        if isinstance(created_by, str):
            created_by = ObjectId(created_by)

        # Generate delivery number
        delivery_number = self._generate_delivery_number()

        # Create delivery items
        delivery_items = []
        for item_data in items:
            product_id = ObjectId(item_data['product_id']) if isinstance(item_data['product_id'], str) else item_data['product_id']
            delivery_item = DeliveryItem(
                product_id=product_id,
                ordered_quantity=item_data['ordered_quantity'],
                picked_quantity=item_data.get('picked_quantity', 0),
                packed_quantity=item_data.get('packed_quantity', 0),
                validated_quantity=item_data.get('validated_quantity', 0),
                unit_price=item_data.get('unit_price', 0),
                notes=item_data.get('notes', '')
            )
            delivery_items.append(delivery_item)

        # Create delivery
        delivery = Delivery(
            delivery_number=delivery_number,
            warehouse_id=warehouse_id,
            customer_name=customer_name,
            customer_address=customer_address,
            status=DELIVERY_STATUS_DRAFT,
            scheduled_date=scheduled_date,
            items=delivery_items,
            notes=notes,
            created_by=created_by
        )

        # Insert into database
        self.db.deliveries.insert_one(delivery.to_mongo())

        logger.info(f"Delivery created: {delivery_number}")

        return delivery.to_dict()

    def transition_status(self, delivery_id, new_status, changed_by, **kwargs):
        """
        Transition delivery to new status.

        Args:
            delivery_id (str or ObjectId): Delivery ID.
            new_status (str): Target status.
            changed_by (str or ObjectId): User ID making the change.
            **kwargs: Additional parameters.

        Returns:
            dict: Updated delivery data.
        """
        if isinstance(delivery_id, str):
            delivery_id = ObjectId(delivery_id)
        if isinstance(changed_by, str):
            changed_by = ObjectId(changed_by)

        delivery_doc = self.db.deliveries.find_one({'_id': delivery_id})
        if not delivery_doc:
            raise ValueError("Delivery not found")

        delivery = Delivery.from_mongo(delivery_doc)

        if not delivery.can_transition_to(new_status):
            raise ValueError(
                f"Cannot transition from {delivery.status} to {new_status}"
            )

        if new_status == DELIVERY_STATUS_DONE:
            self._process_delivery_completion(delivery, changed_by)

        delivery.status = new_status
        delivery.add_status_history(new_status, changed_by)
        delivery.updated_at = datetime.utcnow()

        if new_status == DELIVERY_STATUS_DONE:
            delivery.shipped_date = datetime.utcnow()

        self.db.deliveries.update_one(
            {'_id': delivery_id},
            {'$set': delivery.to_mongo()}
        )

        logger.info(f"Delivery {delivery.delivery_number} transitioned to {new_status}")

        return delivery.to_dict()

    def _process_delivery_completion(self, delivery, changed_by):
        """Process delivery completion - decrease stock."""
        for item in delivery.items:
            # Use validated quantity, fallback to packed, picked, or ordered
            final_qty = item.validated_quantity or item.packed_quantity or item.picked_quantity or item.ordered_quantity
            item.validated_quantity = final_qty

            if final_qty > 0:
                self.ledger_service.record_transaction(
                    product_id=item.product_id,
                    warehouse_id=delivery.warehouse_id,
                    transaction_type=TRANSACTION_TYPE_DELIVERY,
                    reference_type='Delivery',
                    reference_id=delivery._id,
                    reference_number=delivery.delivery_number,
                    quantity_change=-final_qty,
                    created_by=changed_by,
                    notes=f"Delivery completed: {delivery.delivery_number}"
                )

            logger.info(f"Stock decreased: Product {item.product_id}, Qty {final_qty}")

    def get_delivery(self, delivery_id):
        """Get delivery by ID with enriched data."""
        if isinstance(delivery_id, str):
            delivery_id = ObjectId(delivery_id)

        delivery_doc = self.db.deliveries.find_one({'_id': delivery_id})
        if not delivery_doc:
            return None

        delivery = Delivery.from_mongo(delivery_doc)
        delivery_dict = delivery.to_dict()

        warehouse = self.db.warehouses.find_one({'_id': delivery.warehouse_id})
        if warehouse:
            delivery_dict['warehouse_name'] = warehouse['name']

        for item_dict in delivery_dict['items']:
            product = self.db.products.find_one({'_id': ObjectId(item_dict['product_id'])})
            if product:
                item_dict['product_name'] = product['name']
                item_dict['product_sku'] = product['sku']

        return delivery_dict

    def list_deliveries(self, warehouse_id=None, status=None, page=1, per_page=20):
        """List deliveries with filters and pagination."""
        query = {}
        if warehouse_id:
            query['warehouse_id'] = ObjectId(warehouse_id) if isinstance(warehouse_id, str) else warehouse_id
        if status:
            query['status'] = status

        total = self.db.deliveries.count_documents(query)
        skip = (page - 1) * per_page
        total_pages = (total + per_page - 1) // per_page

        deliveries = list(
            self.db.deliveries.find(query)
            .sort('created_at', -1)
            .skip(skip)
            .limit(per_page)
        )

        delivery_list = []
        for delivery_doc in deliveries:
            delivery = Delivery.from_mongo(delivery_doc)
            delivery_dict = delivery.to_dict()

            warehouse = self.db.warehouses.find_one({'_id': delivery.warehouse_id})
            if warehouse:
                delivery_dict['warehouse_name'] = warehouse['name']

            delivery_list.append(delivery_dict)

        return {
            'deliveries': delivery_list,
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': total_pages
        }

    def get_status_counts(self, warehouse_id=None):
        """Get count of deliveries by status."""
        query = {}
        if warehouse_id:
            query['warehouse_id'] = ObjectId(warehouse_id) if isinstance(warehouse_id, str) else warehouse_id

        pipeline = [
            {'$match': query},
            {'$group': {'_id': '$status', 'count': {'$sum': 1}}}
        ]

        result = list(self.db.deliveries.aggregate(pipeline))
        return {item['_id']: item['count'] for item in result}

    def _generate_delivery_number(self):
        """Generate unique delivery number."""
        year = datetime.utcnow().year
        prefix = f"DEL-{year}-"

        last_delivery = self.db.deliveries.find_one(
            {'delivery_number': {'$regex': f'^{prefix}'}},
            sort=[('delivery_number', -1)]
        )

        if last_delivery:
            last_num = int(last_delivery['delivery_number'].split('-')[-1])
            next_num = last_num + 1
        else:
            next_num = 1

        return f"{prefix}{next_num:04d}"
