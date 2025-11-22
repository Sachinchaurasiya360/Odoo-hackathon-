"""
Receipt Service - Manages incoming inventory receipts.

This service implements the receipt workflow:
Draft → Waiting → Ready → Done

Stock increases occur when transitioning to 'Done' status.
"""

from datetime import datetime
from bson import ObjectId

from config.database import get_db
from models.receipt import Receipt, ReceiptItem
from modules.stock.ledger_service import StockLedgerService
from utils.constants import (
    RECEIPT_STATUS_DRAFT, RECEIPT_STATUS_WAITING,
    RECEIPT_STATUS_READY, RECEIPT_STATUS_DONE,
    RECEIPT_STATUS_CANCELLED, TRANSACTION_TYPE_RECEIPT
)
import logging

logger = logging.getLogger(__name__)


class ReceiptService:
    """Service for managing receipt operations."""

    def __init__(self):
        """Initialize ReceiptService."""
        self.db = get_db()
        self.ledger_service = StockLedgerService()

    def create_receipt(self, warehouse_id, supplier_name, items,
                      scheduled_date=None, notes='', created_by=None):
        """
        Create a new receipt in draft status.

        Args:
            warehouse_id (str or ObjectId): Warehouse ID.
            supplier_name (str): Supplier name.
            items (list): List of item dictionaries.
            scheduled_date (datetime, optional): Scheduled receipt date.
            notes (str): Receipt notes.
            created_by (str or ObjectId): User ID.

        Returns:
            dict: Created receipt data.
        """
        if isinstance(warehouse_id, str):
            warehouse_id = ObjectId(warehouse_id)
        if isinstance(created_by, str):
            created_by = ObjectId(created_by)

        # Generate receipt number
        receipt_number = self._generate_receipt_number()

        # Create receipt items
        receipt_items = []
        for item_data in items:
            product_id = ObjectId(item_data['product_id']) if isinstance(item_data['product_id'], str) else item_data['product_id']
            receipt_item = ReceiptItem(
                product_id=product_id,
                expected_quantity=item_data['expected_quantity'],
                received_quantity=item_data.get('received_quantity', 0),
                damaged_quantity=item_data.get('damaged_quantity', 0),
                unit_price=item_data.get('unit_price', 0),
                notes=item_data.get('notes', '')
            )
            receipt_items.append(receipt_item)

        # Create receipt
        receipt = Receipt(
            receipt_number=receipt_number,
            warehouse_id=warehouse_id,
            supplier_name=supplier_name,
            status=RECEIPT_STATUS_DRAFT,
            scheduled_date=scheduled_date,
            items=receipt_items,
            notes=notes,
            created_by=created_by
        )

        # Insert into database
        self.db.receipts.insert_one(receipt.to_mongo())

        logger.info(f"Receipt created: {receipt_number}")

        return receipt.to_dict()

    def transition_status(self, receipt_id, new_status, changed_by, **kwargs):
        """
        Transition receipt to new status.

        Args:
            receipt_id (str or ObjectId): Receipt ID.
            new_status (str): Target status.
            changed_by (str or ObjectId): User ID making the change.
            **kwargs: Additional parameters (e.g., received_quantities).

        Returns:
            dict: Updated receipt data.

        Raises:
            ValueError: If transition is not allowed.
        """
        if isinstance(receipt_id, str):
            receipt_id = ObjectId(receipt_id)
        if isinstance(changed_by, str):
            changed_by = ObjectId(changed_by)

        # Get receipt
        receipt_doc = self.db.receipts.find_one({'_id': receipt_id})
        if not receipt_doc:
            raise ValueError("Receipt not found")

        receipt = Receipt.from_mongo(receipt_doc)

        # Check if transition is allowed
        if not receipt.can_transition_to(new_status):
            raise ValueError(
                f"Cannot transition from {receipt.status} to {new_status}"
            )

        # Handle status-specific logic
        if new_status == RECEIPT_STATUS_DONE:
            self._process_receipt_completion(receipt, changed_by, kwargs.get('received_quantities', {}))

        # Update status
        receipt.status = new_status
        receipt.add_status_history(new_status, changed_by)
        receipt.updated_at = datetime.utcnow()

        if new_status == RECEIPT_STATUS_DONE:
            receipt.received_date = datetime.utcnow()

        # Update in database
        self.db.receipts.update_one(
            {'_id': receipt_id},
            {'$set': receipt.to_mongo()}
        )

        logger.info(f"Receipt {receipt.receipt_number} transitioned to {new_status}")

        return receipt.to_dict()

    def _process_receipt_completion(self, receipt, changed_by, received_quantities):
        """
        Process receipt completion - update stock levels.

        Args:
            receipt (Receipt): Receipt instance.
            changed_by (ObjectId): User ID.
            received_quantities (dict): Product ID to received quantity mapping.
        """
        for item in receipt.items:
            # Get received quantity (use provided or expected)
            received_qty = received_quantities.get(
                str(item.product_id),
                item.received_quantity or item.expected_quantity
            )

            # Update item received quantity
            item.received_quantity = received_qty

            # Record stock transaction (only for non-damaged items)
            usable_qty = received_qty - item.damaged_quantity

            if usable_qty > 0:
                self.ledger_service.record_transaction(
                    product_id=item.product_id,
                    warehouse_id=receipt.warehouse_id,
                    transaction_type=TRANSACTION_TYPE_RECEIPT,
                    reference_type='Receipt',
                    reference_id=receipt._id,
                    reference_number=receipt.receipt_number,
                    quantity_change=usable_qty,
                    created_by=changed_by,
                    notes=f"Receipt completed: {receipt.receipt_number}"
                )

            logger.info(
                f"Stock increased: Product {item.product_id}, "
                f"Warehouse {receipt.warehouse_id}, Qty {usable_qty}"
            )

    def get_receipt(self, receipt_id):
        """
        Get receipt by ID.

        Args:
            receipt_id (str or ObjectId): Receipt ID.

        Returns:
            dict: Receipt data or None.
        """
        if isinstance(receipt_id, str):
            receipt_id = ObjectId(receipt_id)

        receipt_doc = self.db.receipts.find_one({'_id': receipt_id})
        
        if receipt_doc:
            receipt = Receipt.from_mongo(receipt_doc)
            return receipt.to_dict()
        
        return None

    def list_receipts(self, warehouse_id=None, status=None, page=1, per_page=20):
        """
        List receipts with filters and pagination.

        Args:
            warehouse_id (str or ObjectId, optional): Filter by warehouse.
            status (str, optional): Filter by status.
            page (int): Page number.
            per_page (int): Items per page.

        Returns:
            dict: Receipts and pagination info.
        """
        query = {}
        
        if warehouse_id:
            if isinstance(warehouse_id, str):
                warehouse_id = ObjectId(warehouse_id)
            query['warehouse_id'] = warehouse_id
        
        if status:
            query['status'] = status

        total = self.db.receipts.count_documents(query)
        
        receipts = list(
            self.db.receipts.find(query)
            .sort('created_at', -1)
            .skip((page - 1) * per_page)
            .limit(per_page)
        )

        receipt_list = [Receipt.from_mongo(r).to_dict() for r in receipts]

        return {
            'receipts': receipt_list,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        }

    def cancel_receipt(self, receipt_id, changed_by):
        """
        Cancel a receipt.

        Args:
            receipt_id (str or ObjectId): Receipt ID.
            changed_by (str or ObjectId): User ID.

        Returns:
            dict: Updated receipt data.
        """
        return self.transition_status(
            receipt_id,
            RECEIPT_STATUS_CANCELLED,
            changed_by
        )

    def _generate_receipt_number(self):
        """
        Generate unique receipt number.

        Returns:
            str: Receipt number (e.g., RCP-20230615-0001).
        """
        today = datetime.utcnow().strftime('%Y%m%d')
        prefix = f"RCP-{today}"

        # Find the last receipt number for today
        last_receipt = self.db.receipts.find_one(
            {'receipt_number': {'$regex': f'^{prefix}'}},
            sort=[('receipt_number', -1)]
        )

        if last_receipt:
            last_number = int(last_receipt['receipt_number'].split('-')[-1])
            new_number = last_number + 1
        else:
            new_number = 1

        return f"{prefix}-{new_number:04d}"
