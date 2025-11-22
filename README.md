# Inventory Management System

A comprehensive, modular Flask-based inventory management system with MongoDB, following strict PEP8 standards and clean architecture principles.

## 🎉 Recent Improvements

### ✅ Database Architecture Enhancements

- **Migration System**: Complete versioning strategy with rollback support
- **Index Optimization**: Comprehensive indexing via migration system
- **ObjectId Serialization**: Centralized utilities for consistent data handling
- **Security**: Environment-based configuration, no hard-coded credentials

📖 See [DATABASE_IMPROVEMENTS.md](DATABASE_IMPROVEMENTS.md) for details

### ✅ UI/UX Enhancements

- **Accessibility**: WCAG 2.1 Level AA compliant, screen reader support
- **Responsive Design**: Mobile-first approach with optimized layouts
- **Design System**: 150+ utility classes, consistent theming
- **Performance**: Optimized CSS/JS, smooth transitions

📖 See [UI_UX_IMPROVEMENTS.md](UI_UX_IMPROVEMENTS.md) for details

---

## Features

### Core Functionality

- **Multi-warehouse Management**: Track inventory across multiple warehouse locations
- **Product Catalog**: Comprehensive product management with categories and SKUs
- **Stock Tracking**: Real-time stock levels with reserved quantity management
- **Complete Audit Trail**: Every stock movement logged in the ledger

### Document Workflows

#### Receipts (Incoming Inventory)

- **Workflow**: Draft → Waiting → Ready → Done
- Stock increases when transitioning to 'Done'
- Support for partial receipts and damaged items
- Supplier tracking

#### Deliveries (Outgoing Inventory)

- **Workflow**: Pick → Pack → Validate → Shipped
- Stock reservation during picking
- Stock deduction on validation
- Negative stock prevention
- Customer order tracking

#### Transfers (Inter-warehouse)

- **Workflow**: Draft → In Transit → Completed
- Location-to-location stock movement
- Dual ledger entries (source and destination)
- Partial transfer support

#### Adjustments (Stock Corrections)

- **Workflow**: Draft → Approved
- Physical count reconciliation
- Damage/loss/found item tracking
- Automatic difference calculation

### Security Features

- JWT and session-based authentication
- **OTP-based password reset via email**
- Role-based access control (Admin, Inventory Manager, Warehouse Staff, Viewer)
- Password hashing with Werkzeug
- Input sanitization and validation
- CSRF protection for forms
- XSS-safe template rendering
- Brute force protection for password reset

### Performance Optimizations

- MongoDB indexing on critical fields
- Pagination for all list views
- Efficient query optimization
- Dashboard metrics caching
- Connection pooling

## Project Structure

```
src/
├── app.py                          # Application entry point
├── config/
│   ├── settings.py                 # Environment-based configuration
│   └── database.py                 # MongoDB connection manager
├── models/                         # Data models
│   ├── user.py
│   ├── warehouse.py
│   ├── product.py
│   ├── stock.py
│   ├── receipt.py
│   ├── delivery.py
│   ├── transfer.py
│   └── adjustment.py
├── modules/                        # Feature modules (Blueprints)
│   ├── auth/
│   ├── dashboard/
│   ├── products/
│   ├── warehouses/
│   ├── receipts/
│   ├── deliveries/
│   ├── transfers/
│   ├── adjustments/
│   └── stock/
├── services/                       # Business logic layer
├── utils/                          # Utilities
│   ├── constants.py
│   ├── validators.py
│   ├── decorators.py
│   └── responses.py
├── middleware/                     # Middleware components
├── templates/                      # Jinja2 templates
└── static/                         # CSS, JS, images
```

## Installation

### Prerequisites

- Python 3.8+
- MongoDB 4.4+

### Setup

1. **Clone the repository**

   ```bash
   cd Odoo-hackathon-
   ```

2. **Create virtual environment**

   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**

   ```bash
   # Windows
   copy .env.example .env

   # Linux/Mac
   cp .env.example .env

   # Edit .env with your MongoDB connection string and secrets
   ```

   **⚠️ Important**: The application will NOT start without these required environment variables:

   - `MONGODB_URI` - Your MongoDB connection string
   - `SECRET_KEY` - Flask secret key (min 32 characters)
   - `JWT_SECRET_KEY` - JWT secret key (min 32 characters)

5. **Run database migrations**

   ```bash
   # Check migration status
   python migrate.py status

   # Apply all migrations
   python migrate.py up
   ```

6. **Run the application**

   ```bash
   # Development
   python src/app.py

   # Or using Flask CLI
   set FLASK_APP=src/app.py
   set FLASK_ENV=development
   flask run
   ```

7. **Access the application**
   ```
   http://localhost:5000
   ```

## Configuration

Edit `.env` file (see `.env.example` for template):

```env
# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key-change-in-production

# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB_NAME=inventory_management

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-key-change-in-production
JWT_ACCESS_TOKEN_EXPIRES=3600

# Application Settings
ITEMS_PER_PAGE=20
CACHE_TIMEOUT=300
ALLOW_NEGATIVE_STOCK=false
```

## Usage

### Creating a Receipt

1. Navigate to **Receipts** → **Create New**
2. Select warehouse and enter supplier information
3. Add products with expected quantities
4. Save as Draft
5. Transition through workflow: Draft → Waiting → Ready → Done
6. Stock automatically increases when marked as Done

### Creating a Delivery

1. Navigate to **Deliveries** → **Create New**
2. Select warehouse and enter customer information
3. Add products with ordered quantities
4. Save and start picking
5. Transition: Pick (reserves stock) → Pack → Validate (deducts stock) → Shipped

### Stock Transfer

1. Navigate to **Transfers** → **Create New**
2. Select source and destination warehouses
3. Add products to transfer
4. Transition: Draft → In Transit (deducts from source) → Completed (adds to destination)

### Stock Adjustment

1. Navigate to **Adjustments** → **Create New**
2. Select warehouse and product
3. Enter system quantity and physical count
4. System calculates difference
5. Approve to update stock

### Viewing Stock Ledger

1. Navigate to **Stock** → **Ledger**
2. Filter by product, warehouse, or date range
3. View complete transaction history with running balances

## API Endpoints

### Authentication

- `POST /auth/api/login` - Login and get JWT token
- `POST /auth/api/register` - Register new user
- `POST /auth/api/verify` - Verify JWT token

### Receipts

- `GET /receipts/api/receipts` - List receipts
- `POST /receipts/api/receipts` - Create receipt
- `GET /receipts/api/receipts/<id>` - Get receipt details

### Similar endpoints exist for:

- Deliveries (`/deliveries/api/...`)
- Transfers (`/transfers/api/...`)
- Adjustments (`/adjustments/api/...`)
- Products (`/products/api/...`)
- Warehouses (`/warehouses/api/...`)
- Stock (`/stock/api/...`)

## Architecture

### Clean Architecture Principles

1. **Separation of Concerns**

   - Models: Data structure only
   - Services: Business logic
   - Routes: Input validation and response formatting
   - Repositories: Data access (where applicable)

2. **No Business Logic in Routes**

   - Routes handle HTTP concerns only
   - All business logic in service layer
   - Services are reusable and testable

3. **No Hard-coded Values**
   - All constants in `utils/constants.py`
   - Configuration in environment variables
   - Status flows defined as constants

### Stock Movement Flow

```
Document Created (Draft)
    ↓
Workflow Transitions
    ↓
Status Change Triggers Stock Update
    ↓
Service Layer Calls Ledger Service
    ↓
Ledger Service Records Transaction:
  - Gets current stock level
  - Validates (negative stock check)
  - Creates ledger entry with running balance
  - Updates stock level atomically
    ↓
Complete Audit Trail Maintained
```

## Database Indexes

The system automatically creates indexes on:

- User: username, email
- Product: SKU, category_id, name
- Warehouse: code
- StockLevel: (product_id, warehouse_id) compound unique
- StockLedger: product_id, warehouse_id, transaction_date, reference_id
- All document collections: document_number, warehouse_id, status, created_at

## Security Best Practices

1. **Password Security**

   - Werkzeug password hashing
   - Minimum 8 characters required
   - Never stored in plain text

2. **Authentication**

   - JWT tokens with expiration
   - Session-based auth for web interface
   - Secure cookie settings

3. **Authorization**

   - Role-based access control
   - Decorator-based route protection
   - Fine-grained permissions

4. **Input Validation**

   - Server-side validation for all inputs
   - Sanitization to prevent XSS
   - Parameterized queries to prevent injection

5. **CSRF Protection**
   - CSRF tokens in all forms
   - Validation on POST requests

## Development

### Code Standards

- PEP8 formatting (use `black` or `autopep8`)
- Meaningful variable and function names
- Docstrings for all public functions
- Type hints where applicable

### Adding a New Module

1. Create module directory in `src/modules/`
2. Add `__init__.py`, `routes.py`, `service.py`
3. Create model in `src/models/` if needed
4. Register blueprint in `src/app.py`
5. Create templates in `src/templates/module_name/`

### Running Tests

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# All tests
pytest -v
```

## Deployment

### Production Checklist

1. **Environment Variables**

   - Set strong SECRET_KEY
   - Set strong JWT_SECRET_KEY
   - Configure production MongoDB URI
   - Set FLASK_ENV=production

2. **Security**

   - Enable HTTPS
   - Set secure cookie flags
   - Configure CORS if needed
   - Set up firewall rules

3. **Performance**

   - Use production WSGI server (Gunicorn, uWSGI)
   - Enable MongoDB replica set
   - Configure caching
   - Set up monitoring

4. **Example with Gunicorn**
   ```bash
   gunicorn -w 4 -b 0.0.0.0:8000 src.app:app
   ```

## Troubleshooting

### MongoDB Connection Issues

- Verify MongoDB is running: `mongosh`
- Check connection string in `.env`
- Ensure network access to MongoDB

### Import Errors

- Verify virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`
- Check Python path includes `src/` directory

### Stock Discrepancies

- Check stock ledger for transaction history
- Verify workflow transitions completed properly
- Run stock reconciliation report

## Contributing

1. Follow PEP8 coding standards
2. Add docstrings to all functions
3. Write tests for new features
4. Update documentation
5. No business logic in route handlers

## License

[Your License Here]

## Support

For issues and questions:

- Create an issue in the repository
- Check documentation
- Review code comments

## Roadmap

- [ ] Barcode scanning support
- [ ] Mobile app integration
- [ ] Advanced reporting and analytics
- [ ] Multi-currency support
- [ ] Batch and serial number tracking
- [ ] Integration with accounting systems
- [ ] Automated reorder points
- [ ] Supplier management module
