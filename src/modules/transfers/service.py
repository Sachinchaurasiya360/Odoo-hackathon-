"""
Transfer Service - Manages inter-warehouse stock transfers.

This service implements the transfer workflow:
Draft → In Transit → Completed

Stock decreases from source warehouse and increases in destination warehouse
when transitioning to 'Completed' status.
"""

from datetime import datetime
from bson import ObjectId

from config.database import get_db
from models.transfer import Transfer, TransferItem
from modules.stock.ledger_service import StockLedgerService
from utils.constants import (
    TRANSFER_STATUS_DRAFT,
    TRANSFER_STATUS_IN_TRANSIT,
    TRANSFER_STATUS_COMPLETED,
    TRANSFER_STATUS_CANCELLED,
    TRANSACTION_TYPE_TRANSFER_OUT,
    TRANSACTION_TYPE_TRANSFER_IN
)
import logging

logger = logging.getLogger(__name__)


class TransfersService:
    """Service for managing transfer operations."""

    def __init__(self):
        """Initialize TransfersService."""
        self.db = get_db()
        self.collection = self.db.transfers
        self.ledger_service = StockLedgerService()

    def create_transfer(self, from_warehouse_id, to_warehouse_id, items,
                       scheduled_date=None, notes='', created_by=None):
        """
        Create a new transfer in draft status.

        Args:
            from_warehouse_id (str or ObjectId): Source warehouse ID.
            to_warehouse_id (str or ObjectId): Destination warehouse ID.
            items (list): List of item dictionaries.
            scheduled_date (datetime, optional): Scheduled transfer date.
            notes (str): Transfer notes.
            created_by (str or ObjectId): User ID.

        Returns:
            dict: Created transfer data.
        """
        if isinstance(from_warehouse_id, str):
            from_warehouse_id = ObjectId(from_warehouse_id)
        if isinstance(to_warehouse_id, str):
            to_warehouse_id = ObjectId(to_warehouse_id)
        if isinstance(created_by, str):
            created_by = ObjectId(created_by)

        # Validate warehouses are different
        if from_warehouse_id == to_warehouse_id:
            raise ValueError("Source and destination warehouses must be different")

        # Generate transfer number
        transfer_number = self._generate_transfer_number()

        # Create transfer items
        transfer_items = []
        for item_data in items:
            product_id = ObjectId(item_data['product_id']) if isinstance(item_data['product_id'], str) else item_data['product_id']
            transfer_item = TransferItem(
                product_id=product_id,
                requested_quantity=item_data['requested_quantity'],
                transferred_quantity=item_data.get('transferred_quantity', 0),
                received_quantity=item_data.get('received_quantity', 0),
                notes=item_data.get('notes', '')
            )
            transfer_items.append(transfer_item)

        # Create transfer
        transfer = Transfer(
            transfer_number=transfer_number,
            from_warehouse_id=from_warehouse_id,
            to_warehouse_id=to_warehouse_id,
            status=TRANSFER_STATUS_DRAFT,
            scheduled_date=scheduled_date,
            items=transfer_items,
            notes=notes,
            created_by=created_by
        )

        # Insert into database
        self.collection.insert_one(transfer.to_mongo())

        logger.info(f"Transfer created: {transfer_number}")

        return transfer.to_dict()

    def transition_status(self, transfer_id, new_status, changed_by, **kwargs):
        """
        Transition transfer to new status.

        Args:
            transfer_id (str or ObjectId): Transfer ID.
            new_status (str): Target status.
            changed_by (str or ObjectId): User ID making the change.
            **kwargs: Additional parameters.

        Returns:
            dict: Updated transfer data.
        """
        if isinstance(transfer_id, str):
            transfer_id = ObjectId(transfer_id)
        if isinstance(changed_by, str):
            changed_by = ObjectId(changed_by)

        transfer_doc = self.collection.find_one({'_id': transfer_id})
        if not transfer_doc:
            raise ValueError("Transfer not found")

        transfer = Transfer.from_mongo(transfer_doc)

        if not transfer.can_transition_to(new_status):
            raise ValueError(
                f"Cannot transition from {transfer.status} to {new_status}"
            )

        # Process completion - stock movement happens here
        if new_status == TRANSFER_STATUS_COMPLETED:
            self._process_transfer_completion(transfer, changed_by)

        transfer.status = new_status
        transfer.add_status_history(new_status, changed_by)
        transfer.updated_at = datetime.utcnow()

        if new_status == TRANSFER_STATUS_COMPLETED:
            transfer.completed_date = datetime.utcnow()

        self.collection.update_one(
            {'_id': transfer_id},
            {'$set': transfer.to_mongo()}
        )

        logger.info(f"Transfer {transfer.transfer_number} transitioned to {new_status}")

        return transfer.to_dict()

    def _process_transfer_completion(self, transfer, changed_by):
        """
        Process transfer completion - move stock between warehouses.
        
        This creates two transactions:
        1. TRANSFER_OUT - decreases stock in source warehouse
        2. TRANSFER_IN - increases stock in destination warehouse
        """
        for item in transfer.items:
            # Use received quantity, fallback to transferred or requested
            final_qty = item.received_quantity or item.transferred_quantity or item.requested_quantity
            item.received_quantity = final_qty

            if final_qty > 0:
                # Decrease stock from source warehouse
                self.ledger_service.record_transaction(
                    product_id=item.product_id,
                    warehouse_id=transfer.from_warehouse_id,
                    transaction_type=TRANSACTION_TYPE_TRANSFER_OUT,
                    reference_type='Transfer',
                    reference_id=transfer._id,
                    reference_number=transfer.transfer_number,
                    quantity_change=-final_qty,  # Negative for outgoing
                    created_by=changed_by,
                    notes=f"Transfer to warehouse: {transfer.transfer_number}"
                )

                # Increase stock in destination warehouse
                self.ledger_service.record_transaction(
                    product_id=item.product_id,
                    warehouse_id=transfer.to_warehouse_id,
                    transaction_type=TRANSACTION_TYPE_TRANSFER_IN,
                    reference_type='Transfer',
                    reference_id=transfer._id,
                    reference_number=transfer.transfer_number,
                    quantity_change=final_qty,  # Positive for incoming
                    created_by=changed_by,
                    notes=f"Transfer from warehouse: {transfer.transfer_number}"
                )

                logger.info(f"Stock transferred: Product {item.product_id}, Qty {final_qty}")

    def get_transfer(self, transfer_id):
        """Get transfer by ID with enriched data."""
        if isinstance(transfer_id, str):
            transfer_id = ObjectId(transfer_id)

        transfer_doc = self.collection.find_one({'_id': transfer_id})
        if not transfer_doc:
            return None

        transfer = Transfer.from_mongo(transfer_doc)
        transfer_dict = transfer.to_dict()

        # Enrich with warehouse names
        from_warehouse = self.db.warehouses.find_one({'_id': transfer.from_warehouse_id})
        if from_warehouse:
            transfer_dict['from_warehouse_name'] = from_warehouse['name']

        to_warehouse = self.db.warehouses.find_one({'_id': transfer.to_warehouse_id})
        if to_warehouse:
            transfer_dict['to_warehouse_name'] = to_warehouse['name']

        # Enrich items with product details
        for item_dict in transfer_dict['items']:
            product = self.db.products.find_one({'_id': ObjectId(item_dict['product_id'])})
            if product:
                item_dict['product_name'] = product['name']
                item_dict['product_sku'] = product['sku']

        return transfer_dict

    def list_transfers(self, from_warehouse_id=None, to_warehouse_id=None, 
                      status=None, page=1, per_page=20):
        """List transfers with filters and pagination."""
        query = {}
        if from_warehouse_id:
            query['from_warehouse_id'] = ObjectId(from_warehouse_id) if isinstance(from_warehouse_id, str) else from_warehouse_id
        if to_warehouse_id:
            query['to_warehouse_id'] = ObjectId(to_warehouse_id) if isinstance(to_warehouse_id, str) else to_warehouse_id
        if status:
            query['status'] = status

        total = self.collection.count_documents(query)
        skip = (page - 1) * per_page
        total_pages = (total + per_page - 1) // per_page

        transfers = list(
            self.collection.find(query)
            .sort('created_at', -1)
            .skip(skip)
            .limit(per_page)
        )

        transfer_list = []
        for transfer_doc in transfers:
            transfer = Transfer.from_mongo(transfer_doc)
            transfer_dict = transfer.to_dict()

            # Add warehouse names
            from_warehouse = self.db.warehouses.find_one({'_id': transfer.from_warehouse_id})
            if from_warehouse:
                transfer_dict['from_warehouse_name'] = from_warehouse['name']

            to_warehouse = self.db.warehouses.find_one({'_id': transfer.to_warehouse_id})
            if to_warehouse:
                transfer_dict['to_warehouse_name'] = to_warehouse['name']

            transfer_list.append(transfer_dict)

        return {
            'transfers': transfer_list,
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': total_pages
        }

    def get_status_counts(self, warehouse_id=None):
        """Get count of transfers by status."""
        query = {}
        if warehouse_id:
            wh_id = ObjectId(warehouse_id) if isinstance(warehouse_id, str) else warehouse_id
            query['$or'] = [
                {'from_warehouse_id': wh_id},
                {'to_warehouse_id': wh_id}
            ]

        pipeline = [
            {'$match': query},
            {'$group': {'_id': '$status', 'count': {'$sum': 1}}}
        ]

        result = list(self.collection.aggregate(pipeline))
        return {item['_id']: item['count'] for item in result}

    def _generate_transfer_number(self):
        """Generate unique transfer number."""
        year = datetime.utcnow().year
        prefix = f"TRF-{year}-"

        last_transfer = self.collection.find_one(
            {'transfer_number': {'$regex': f'^{prefix}'}},
            sort=[('transfer_number', -1)]
        )

        if last_transfer:
            last_num = int(last_transfer['transfer_number'].split('-')[-1])
            next_num = last_num + 1
        else:
            next_num = 1

        return f"{prefix}{next_num:04d}"
