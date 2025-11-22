# Database Architecture Improvements

## Overview

This document outlines the comprehensive database architecture improvements implemented to address critical issues in the inventory management system.

## Issues Addressed

### 1. ✅ Migration and Versioning Strategy

**Problem**: No migration/versioning strategy for MongoDB schema evolution.

**Solution**: Implemented a complete migration system with:

#### Migration System Components

**Base Migration Class** (`migrations/base_migration.py`)

- Abstract base class defining migration contract
- Required methods: `upgrade()` and `downgrade()`
- Built-in logging and database access
- Version and description metadata

**Migration Manager** (`migrations/migration_manager.py`)

- Orchestrates migration execution
- Tracks applied migrations in `schema_migrations` collection
- Supports forward migrations (`migrate_up`)
- Supports rollback (`migrate_down`)
- Automatic migration discovery from `migrations/versions/`
- Version status reporting

**Example Migration** (`migrations/versions/001_initial_setup.py`)

- Creates all collections with comprehensive indexes
- Demonstrates proper migration structure
- Includes both upgrade and downgrade logic

#### Usage

```python
from config.database import db
from migrations.migration_manager import MigrationManager

# Initialize migration manager
manager = MigrationManager(db.get_db())

# Check migration status
status = manager.get_migration_status()
print(f"Applied: {status['applied_migrations']}")
print(f"Pending: {status['pending_migrations']}")

# Apply all pending migrations
manager.migrate_up()

# Rollback to specific version
manager.migrate_down(target_version='001')
```

#### Creating New Migrations

1. Create file in `migrations/versions/` with naming: `XXX_description.py`
2. Inherit from `BaseMigration`
3. Set `version` and `description` attributes
4. Implement `upgrade()` and `downgrade()` methods

```python
from migrations.base_migration import BaseMigration

class Migration002AddCategoryIndexes(BaseMigration):
    version = "002"
    description = "Add category-specific indexes"

    def upgrade(self):
        self.db.categories.create_index([('path', 1)], name='idx_category_path')
        self.log_info("Category indexes created")

    def downgrade(self):
        self.db.categories.drop_index('idx_category_path')
        self.log_info("Category indexes removed")
```

---

### 2. ✅ Explicit Index Definitions

**Problem**: No explicit index definitions visible in code.

**Solution**: Comprehensive indexing strategy documented in migration 001.

#### Index Coverage

**Users Collection**

- Unique: `username`, `email`
- Standard: `role`, `is_active`

**Products Collection**

- Unique: `sku`
- Standard: `name`, `category_id`, `is_active`
- Full-text: `name`, `description`

**Warehouses Collection**

- Unique: `code`
- Standard: `name`, `is_active`

**Stock Levels Collection**

- Unique compound: `(product_id, warehouse_id)`
- Standard: `product_id`, `warehouse_id`, `quantity`

**Stock Ledger Collection**

- Standard: `product_id`, `warehouse_id`, `transaction_type`, `reference_id`, `created_by`
- Descending: `transaction_date`
- Compound: `(product_id, warehouse_id, transaction_date DESC)`

**Receipts Collection**

- Unique: `receipt_number`
- Standard: `warehouse_id`, `status`, `created_by`
- Descending: `created_at`
- Compound: `(warehouse_id, status, created_at DESC)`

**Deliveries Collection**

- Unique: `delivery_number`
- Standard: `warehouse_id`, `status`, `created_by`
- Descending: `created_at`
- Compound: `(warehouse_id, status, created_at DESC)`

**Transfers Collection**

- Unique: `transfer_number`
- Standard: `from_warehouse_id`, `to_warehouse_id`, `status`, `created_by`
- Descending: `created_at`
- Compound: `(from_warehouse_id, to_warehouse_id, status)`

**Adjustments Collection**

- Unique: `adjustment_number`
- Standard: `warehouse_id`, `product_id`, `status`, `created_by`
- Descending: `created_at`

#### Index Management

The old inline index creation in `database.py` is now **DEPRECATED**. Index creation is managed through the migration system:

```python
# OLD (deprecated)
def _create_indexes(self):
    """DEPRECATED: Use migration system"""
    # Creates only critical unique constraints

# NEW (recommended)
# Run migration 001 to create all indexes
manager.migrate_up(target_version='001')
```

---

### 3. ✅ ObjectId Serialization Consistency

**Problem**: Inconsistent ObjectId handling in model `to_dict()` methods.

**Solution**: Created centralized serialization utilities.

#### Serialization Utilities (`utils/serializers.py`)

**Core Functions**

```python
from utils.serializers import (
    serialize_object_id,
    serialize_datetime,
    serialize_document,
    deserialize_object_id,
    deserialize_datetime,
    deserialize_document
)

# Serialize ObjectId
serialize_object_id(ObjectId('...'))  # Returns: '...' or None
serialize_object_id(None)             # Returns: None

# Serialize datetime
serialize_datetime(datetime.utcnow()) # Returns: '2024-01-01T12:00:00'
serialize_datetime(None)              # Returns: None

# Serialize entire document
doc = {'_id': ObjectId('...'), 'created_at': datetime.utcnow()}
serialize_document(doc)
# Returns: {'_id': '...', 'created_at': '2024-01-01T12:00:00'}
```

**Updated All Models**

All model classes now use consistent serialization:

```python
from utils.serializers import serialize_object_id, serialize_datetime

class Product:
    def to_dict(self):
        return {
            '_id': serialize_object_id(self._id),
            'category_id': serialize_object_id(self.category_id),
            'created_at': serialize_datetime(self.created_at),
            # ... other fields
        }
```

**Benefits**

- ✅ Consistent null handling (no more `if x else None` checks)
- ✅ Type-safe serialization
- ✅ Automatic validation
- ✅ Single source of truth for serialization logic
- ✅ Easy to extend for custom types

**Models Updated**

- ✅ User
- ✅ Product, Category
- ✅ Warehouse
- ✅ StockLevel, StockLedger
- ✅ Receipt, ReceiptItem
- ✅ Delivery, DeliveryItem
- ✅ Transfer, TransferItem
- ✅ Adjustment

---

### 4. ✅ Hard-coded Database Credentials

**Problem**: Hard-coded MongoDB credentials in `config/settings.py`.

**Solution**: Environment-based configuration with mandatory security.

#### Security Improvements

**Environment Variables** (`.env.example` template provided)

```bash
# Required - Application will not start without these
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/database
SECRET_KEY=your-secret-key-min-32-chars
JWT_SECRET_KEY=your-jwt-secret-key-min-32-chars

# Optional - with sensible defaults
MONGODB_DB_NAME=inventory_management
JWT_ACCESS_TOKEN_EXPIRES=3600
ITEMS_PER_PAGE=20
```

**Updated Settings** (`config/settings.py`)

```python
class Config:
    # Required environment variables (no defaults)
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable must be set")

    MONGODB_URI = os.getenv('MONGODB_URI')
    if not MONGODB_URI:
        raise ValueError("MONGODB_URI environment variable must be set")

    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    if not JWT_SECRET_KEY:
        raise ValueError("JWT_SECRET_KEY environment variable must be set")
```

**Benefits**

- ✅ No credentials in source code
- ✅ Application fails fast if credentials missing
- ✅ Environment-specific configurations
- ✅ Template file for easy setup (`.env.example`)
- ✅ Production-ready security

**Setup Instructions**

1. Copy `.env.example` to `.env`
2. Fill in your actual credentials
3. Never commit `.env` to version control (already in `.gitignore`)

---

## Migration Workflow

### Initial Setup (New Database)

```bash
# 1. Ensure .env is configured
cp .env.example .env
# Edit .env with your credentials

# 2. Run migrations
python -c "
from config.database import db
from migrations.migration_manager import MigrationManager

# Initialize database connection
from config.settings import get_config
config = get_config()
db.initialize(config.MONGODB_URI, config.MONGODB_DB_NAME)

# Run migrations
manager = MigrationManager(db.get_db())
manager.migrate_up()
print('Migrations completed successfully')
"
```

### Development Workflow

```bash
# Check migration status
python -c "
from config.database import db
from migrations.migration_manager import MigrationManager
from config.settings import get_config

config = get_config()
db.initialize(config.MONGODB_URI, config.MONGODB_DB_NAME)
manager = MigrationManager(db.get_db())
status = manager.get_migration_status()

print(f'Applied: {len(status[\"applied_migrations\"])}')
print(f'Pending: {len(status[\"pending_migrations\"])}')
for migration in status['pending_migrations']:
    print(f'  - {migration}')
"

# Apply migrations
python -c "
from config.database import db
from migrations.migration_manager import MigrationManager
from config.settings import get_config

config = get_config()
db.initialize(config.MONGODB_URI, config.MONGODB_DB_NAME)
manager = MigrationManager(db.get_db())
manager.migrate_up()
"
```

### Rollback Workflow

```bash
# Rollback to specific version
python -c "
from config.database import db
from migrations.migration_manager import MigrationManager
from config.settings import get_config

config = get_config()
db.initialize(config.MONGODB_URI, config.MONGODB_DB_NAME)
manager = MigrationManager(db.get_db())
manager.migrate_down(target_version='001')
"
```

---

## Best Practices

### Migration Best Practices

1. **Versioning**: Use sequential numbers (001, 002, 003...)
2. **Naming**: Use descriptive names (`001_initial_setup.py`)
3. **Idempotency**: Ensure migrations can be run multiple times safely
4. **Rollback**: Always implement `downgrade()` method
5. **Testing**: Test migrations on development database first
6. **Documentation**: Add clear docstrings explaining what the migration does

### Index Best Practices

1. **Unique Constraints**: Create unique indexes for all natural keys
2. **Compound Indexes**: Use for common multi-field queries
3. **Background Creation**: Use `background=True` for large collections
4. **Index Order**: Put equality fields before range fields
5. **Query Patterns**: Index based on actual query patterns, not theoretical needs
6. **Monitoring**: Regularly check index usage with `db.collection.getIndexes()`

### Serialization Best Practices

1. **Consistency**: Always use `serialize_object_id()` for ObjectIds
2. **Null Safety**: Serializers handle None automatically
3. **Type Checking**: Serializers validate types before conversion
4. **API Responses**: Use `to_dict()` for all API responses
5. **Database Storage**: Use `to_mongo()` for database operations

### Security Best Practices

1. **Never Commit Secrets**: Add `.env` to `.gitignore`
2. **Rotate Credentials**: Change production secrets regularly
3. **Environment Separation**: Use different credentials for dev/staging/prod
4. **Secret Length**: Use minimum 32 characters for SECRET_KEY and JWT_SECRET_KEY
5. **Access Control**: Limit database user permissions to necessary operations

---

## File Structure

```
src/
├── config/
│   ├── database.py          # Database connection (minimal indexes)
│   └── settings.py          # Environment-based config (secured)
├── migrations/
│   ├── __init__.py          # Migration package exports
│   ├── base_migration.py    # Abstract base class
│   ├── migration_manager.py # Migration orchestration
│   └── versions/            # Migration files
│       ├── __init__.py
│       └── 001_initial_setup.py
├── models/
│   ├── user.py              # ✅ Uses serializers
│   ├── product.py           # ✅ Uses serializers
│   ├── warehouse.py         # ✅ Uses serializers
│   ├── stock.py             # ✅ Uses serializers
│   ├── receipt.py           # ✅ Uses serializers
│   ├── delivery.py          # ✅ Uses serializers
│   ├── transfer.py          # ✅ Uses serializers
│   └── adjustment.py        # ✅ Uses serializers
└── utils/
    └── serializers.py       # Centralized serialization utilities
```

---

## Testing

### Test Migration System

```python
# test_migrations.py
from config.database import db
from migrations.migration_manager import MigrationManager

def test_migration_status():
    manager = MigrationManager(db.get_db())
    status = manager.get_migration_status()
    assert 'applied_migrations' in status
    assert 'pending_migrations' in status

def test_migration_up():
    manager = MigrationManager(db.get_db())
    manager.migrate_up(target_version='001')
    status = manager.get_migration_status()
    assert '001' in status['applied_migrations']

def test_migration_down():
    manager = MigrationManager(db.get_db())
    manager.migrate_down(target_version='000')
    status = manager.get_migration_status()
    assert len(status['applied_migrations']) == 0
```

### Test Serialization

```python
# test_serializers.py
from utils.serializers import serialize_object_id, serialize_datetime
from bson import ObjectId
from datetime import datetime

def test_serialize_object_id():
    obj_id = ObjectId()
    serialized = serialize_object_id(obj_id)
    assert isinstance(serialized, str)
    assert len(serialized) == 24

def test_serialize_none():
    assert serialize_object_id(None) is None
    assert serialize_datetime(None) is None

def test_serialize_datetime():
    dt = datetime.utcnow()
    serialized = serialize_datetime(dt)
    assert 'T' in serialized
    assert isinstance(serialized, str)
```

---

## Summary

All four critical database issues have been successfully addressed:

1. ✅ **Migration/Versioning**: Complete migration system with version tracking
2. ✅ **Index Definitions**: Comprehensive indexing via migration 001
3. ✅ **ObjectId Serialization**: Centralized utilities used across all models
4. ✅ **Hard-coded Credentials**: Environment-based configuration with security validation

The system is now production-ready with proper database architecture, security, and maintainability.
