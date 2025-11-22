"""
Stock Ledger Service - Critical component for all stock movements.

This service handles all stock transactions, ensuring atomic updates
to stock levels and maintaining a complete audit trail in the ledger.
"""

from datetime import datetime
from bson import ObjectId

from config.database import get_db
from models.stock import StockLevel, StockLedger
from utils.constants import TRANSACTION_TYPES
import logging

logger = logging.getLogger(__name__)


class StockLedgerService:
    """Service for managing stock ledger transactions."""

    def __init__(self):
        """Initialize StockLedgerService."""
        self.db = get_db()

    def record_transaction(self, product_id, warehouse_id, transaction_type,
                          reference_type, reference_id, reference_number,
                          quantity_change, created_by, notes=''):
        """
        Record a stock transaction with atomic stock level update.

        This is the core method for all stock movements. It ensures:
        1. Stock level is updated atomically
        2. Ledger entry is created with running balance
        3. Transaction is logged for audit trail

        Args:
            product_id (ObjectId): Product ID.
            warehouse_id (ObjectId): Warehouse ID.
            transaction_type (str): Type of transaction.
            reference_type (str): Type of reference document.
            reference_id (ObjectId): Reference document ID.
            reference_number (str): Reference document number.
            quantity_change (float): Quantity change (positive or negative).
            created_by (ObjectId): User ID who created the transaction.
            notes (str, optional): Transaction notes.

        Returns:
            dict: Result with success status and ledger entry.

        Raises:
            ValueError: If transaction would result in negative stock (when not allowed).
        """
        try:
            # Get current stock level
            stock_level = self.db.stock_levels.find_one({
                'product_id': product_id,
                'warehouse_id': warehouse_id
            })

            if stock_level:
                quantity_before = stock_level['quantity']
                quantity_after = quantity_before + quantity_change
            else:
                # Create new stock level if doesn't exist
                quantity_before = 0
                quantity_after = quantity_change

            # Check for negative stock (if not allowed)
            from config.settings import get_config
            config = get_config()
            if not config.ALLOW_NEGATIVE_STOCK and quantity_after < 0:
                raise ValueError(
                    f"Insufficient stock. Available: {quantity_before}, "
                    f"Requested: {abs(quantity_change)}"
                )

            # Create ledger entry
            ledger_entry = StockLedger(
                product_id=product_id,
                warehouse_id=warehouse_id,
                transaction_type=transaction_type,
                reference_type=reference_type,
                reference_id=reference_id,
                reference_number=reference_number,
                quantity_change=quantity_change,
                quantity_before=quantity_before,
                quantity_after=quantity_after,
                created_by=created_by,
                notes=notes
            )

            # Insert ledger entry
            self.db.stock_ledger.insert_one(ledger_entry.to_mongo())

            # Update stock level atomically
            if stock_level:
                self.db.stock_levels.update_one(
                    {
                        'product_id': product_id,
                        'warehouse_id': warehouse_id
                    },
                    {
                        '$set': {
                            'quantity': quantity_after,
                            'last_updated': datetime.utcnow()
                        }
                    }
                )
            else:
                # Create new stock level
                new_stock_level = StockLevel(
                    product_id=product_id,
                    warehouse_id=warehouse_id,
                    quantity=quantity_after,
                    reserved_quantity=0
                )
                self.db.stock_levels.insert_one(new_stock_level.to_mongo())

            logger.info(
                f"Stock transaction recorded: {transaction_type} "
                f"Product:{product_id} Warehouse:{warehouse_id} "
                f"Change:{quantity_change} New Balance:{quantity_after}"
            )

            return {
                'success': True,
                'ledger_entry': ledger_entry.to_dict(),
                'quantity_before': quantity_before,
                'quantity_after': quantity_after
            }

        except Exception as e:
            logger.error(f"Error recording stock transaction: {e}")
            raise

    def reserve_stock(self, product_id, warehouse_id, quantity, created_by,
                     reference_type, reference_id, reference_number):
        """
        Reserve stock for pending orders (doesn't change total quantity).

        Args:
            product_id (ObjectId): Product ID.
            warehouse_id (ObjectId): Warehouse ID.
            quantity (float): Quantity to reserve.
            created_by (ObjectId): User ID.
            reference_type (str): Reference document type.
            reference_id (ObjectId): Reference document ID.
            reference_number (str): Reference document number.

        Returns:
            dict: Result with success status.

        Raises:
            ValueError: If insufficient available stock.
        """
        stock_level = self.db.stock_levels.find_one({
            'product_id': product_id,
            'warehouse_id': warehouse_id
        })

        if not stock_level:
            raise ValueError("Product not found in warehouse")

        available = stock_level['quantity'] - stock_level.get('reserved_quantity', 0)
        
        if available < quantity:
            raise ValueError(
                f"Insufficient available stock. Available: {available}, "
                f"Requested: {quantity}"
            )

        # Update reserved quantity
        self.db.stock_levels.update_one(
            {
                'product_id': product_id,
                'warehouse_id': warehouse_id
            },
            {
                '$inc': {'reserved_quantity': quantity},
                '$set': {'last_updated': datetime.utcnow()}
            }
        )

        logger.info(
            f"Stock reserved: Product:{product_id} Warehouse:{warehouse_id} "
            f"Quantity:{quantity}"
        )

        return {'success': True, 'reserved_quantity': quantity}

    def release_reservation(self, product_id, warehouse_id, quantity):
        """
        Release reserved stock (e.g., when order is cancelled).

        Args:
            product_id (ObjectId): Product ID.
            warehouse_id (ObjectId): Warehouse ID.
            quantity (float): Quantity to release.

        Returns:
            dict: Result with success status.
        """
        self.db.stock_levels.update_one(
            {
                'product_id': product_id,
                'warehouse_id': warehouse_id
            },
            {
                '$inc': {'reserved_quantity': -quantity},
                '$set': {'last_updated': datetime.utcnow()}
            }
        )

        logger.info(
            f"Stock reservation released: Product:{product_id} "
            f"Warehouse:{warehouse_id} Quantity:{quantity}"
        )

        return {'success': True, 'released_quantity': quantity}

    def get_ledger_history(self, product_id=None, warehouse_id=None,
                          start_date=None, end_date=None, page=1, per_page=20):
        """
        Get stock ledger history with filters.

        Args:
            product_id (ObjectId, optional): Filter by product.
            warehouse_id (ObjectId, optional): Filter by warehouse.
            start_date (datetime, optional): Filter by start date.
            end_date (datetime, optional): Filter by end date.
            page (int): Page number.
            per_page (int): Items per page.

        Returns:
            dict: Ledger entries and pagination info.
        """
        query = {}
        
        if product_id:
            query['product_id'] = product_id
        if warehouse_id:
            query['warehouse_id'] = warehouse_id
        if start_date or end_date:
            query['transaction_date'] = {}
            if start_date:
                query['transaction_date']['$gte'] = start_date
            if end_date:
                query['transaction_date']['$lte'] = end_date

        total = self.db.stock_ledger.count_documents(query)
        
        entries = list(
            self.db.stock_ledger.find(query)
            .sort('transaction_date', -1)
            .skip((page - 1) * per_page)
            .limit(per_page)
        )

        ledger_entries = [StockLedger.from_mongo(entry) for entry in entries]

        return {
            'entries': [entry.to_dict() for entry in ledger_entries],
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        }

    def get_current_stock(self, product_id, warehouse_id):
        """
        Get current stock level for a product in a warehouse.

        Args:
            product_id (ObjectId): Product ID.
            warehouse_id (ObjectId): Warehouse ID.

        Returns:
            dict: Stock level information or None.
        """
        stock_level = self.db.stock_levels.find_one({
            'product_id': product_id,
            'warehouse_id': warehouse_id
        })

        if stock_level:
            return StockLevel.from_mongo(stock_level).to_dict()
        
        return None
