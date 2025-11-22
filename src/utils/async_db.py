"""
Async database operations wrapper.

This module provides utilities for executing database operations
in a non-blocking manner using thread pools, improving throughput
under load without requiring full async/await refactoring.
"""

from concurrent.futures import ThreadPoolExecutor
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# Thread pool for database operations (adjust size based on workload)
db_executor = ThreadPoolExecutor(
    max_workers=20,
    thread_name_prefix='db_worker'
)


def async_db_operation(func):
    """
    Decorator to execute database operations in a thread pool.
    
    This allows Flask routes to handle multiple requests concurrently
    without blocking on synchronous database calls.
    
    Usage:
        @async_db_operation
        def get_products():
            return db.products.find({}).limit(100)
    
    Args:
        func: Function that performs database operations
        
    Returns:
        Wrapper function that executes in thread pool
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        return db_executor.submit(func, *args, **kwargs)
    
    return wrapper


def execute_async_db(func, *args, **kwargs):
    """
    Execute a database operation asynchronously in thread pool.
    
    Args:
        func: Function to execute
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func
        
    Returns:
        Future object that can be waited on with .result()
        
    Example:
        future = execute_async_db(db.products.find, {"is_active": True})
        # Do other work...
        results = future.result()  # Wait for completion
    """
    return db_executor.submit(func, *args, **kwargs)


def execute_async_db_batch(operations):
    """
    Execute multiple database operations concurrently.
    
    Args:
        operations: List of tuples (func, args, kwargs)
        
    Returns:
        List of results in same order as operations
        
    Example:
        ops = [
            (db.products.count_documents, ({"is_active": True},), {}),
            (db.warehouses.count_documents, ({},), {}),
            (db.stock_levels.count_documents, ({},), {})
        ]
        results = execute_async_db_batch(ops)
        product_count, warehouse_count, stock_count = results
    """
    futures = []
    for op in operations:
        func = op[0]
        args = op[1] if len(op) > 1 else ()
        kwargs = op[2] if len(op) > 2 else {}
        futures.append(db_executor.submit(func, *args, **kwargs))
    
    return [future.result() for future in futures]


class AsyncDBContext:
    """
    Context manager for batching async database operations.
    
    Example:
        with AsyncDBContext() as async_db:
            products_future = async_db.submit(db.products.find, {"is_active": True})
            warehouses_future = async_db.submit(db.warehouses.find, {})
            
            # Both queries run concurrently
            products = list(products_future.result())
            warehouses = list(warehouses_future.result())
    """
    
    def __init__(self):
        self.futures = []
    
    def submit(self, func, *args, **kwargs):
        """Submit a database operation to the thread pool."""
        future = db_executor.submit(func, *args, **kwargs)
        self.futures.append(future)
        return future
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Wait for all submitted operations to complete
        for future in self.futures:
            try:
                future.result(timeout=30)  # 30 second timeout
            except Exception as e:
                logger.error(f"Async DB operation failed: {e}")
        return False


def optimize_query_with_projection(collection, query, fields=None, limit=None):
    """
    Optimize database queries with field projection to reduce data transfer.
    
    Args:
        collection: MongoDB collection object
        query: Query filter dict
        fields: List of field names to return (None for all fields)
        limit: Maximum number of documents to return
        
    Returns:
        Cursor with optimized query
        
    Example:
        # Only fetch needed fields
        products = optimize_query_with_projection(
            db.products,
            {"is_active": True},
            fields=["_id", "name", "sku"],
            limit=100
        )
    """
    cursor = collection.find(query)
    
    if fields:
        projection = {field: 1 for field in fields}
        cursor = collection.find(query, projection)
    
    if limit:
        cursor = cursor.limit(limit)
    
    return cursor


def batch_insert_optimized(collection, documents, batch_size=1000):
    """
    Insert documents in optimized batches to improve performance.
    
    Args:
        collection: MongoDB collection object
        documents: List of documents to insert
        batch_size: Number of documents per batch
        
    Returns:
        Total number of inserted documents
        
    Example:
        inserted_count = batch_insert_optimized(
            db.products,
            large_product_list,
            batch_size=500
        )
    """
    total_inserted = 0
    
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        result = collection.insert_many(batch, ordered=False)
        total_inserted += len(result.inserted_ids)
        logger.info(f"Inserted batch {i//batch_size + 1}: {len(result.inserted_ids)} documents")
    
    return total_inserted


def shutdown_async_db():
    """
    Gracefully shutdown the database thread pool.
    Call this during application shutdown.
    """
    logger.info("Shutting down async database executor...")
    db_executor.shutdown(wait=True)
    logger.info("Async database executor shutdown complete")
