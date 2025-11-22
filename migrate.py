"""
Database Migration Management Script

This script provides a command-line interface for managing database migrations.

Usage:
    python migrate.py status              # Show migration status
    python migrate.py up                  # Apply all pending migrations
    python migrate.py up --target 001     # Apply migrations up to version 001
    python migrate.py down --target 001   # Rollback to version 001
    python migrate.py down --target 0     # Rollback all migrations
"""

import sys
import argparse
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from config.database import db
from config.settings import get_config
from migrations.migration_manager import MigrationManager


def print_status(status):
    """Print migration status in a formatted way."""
    print("\n" + "=" * 60)
    print("DATABASE MIGRATION STATUS")
    print("=" * 60)
    
    applied = status['applied_migrations']
    pending = status['pending_migrations']
    
    print(f"\n✓ Applied Migrations: {len(applied)}")
    if applied:
        for migration in applied:
            version = migration['version']
            desc = migration['description']
            applied_at = migration['applied_at']
            print(f"  • {version}: {desc}")
            print(f"    Applied at: {applied_at}")
    
    print(f"\n○ Pending Migrations: {len(pending)}")
    if pending:
        for migration in pending:
            version = migration['version']
            desc = migration['description']
            print(f"  • {version}: {desc}")
    
    if not pending:
        print("  All migrations are up to date!")
    
    print("\n" + "=" * 60 + "\n")


def migrate_up(manager, target_version=None):
    """Apply migrations."""
    print("\n🔄 Applying migrations...")
    
    try:
        manager.migrate_up(target_version=target_version)
        print("✓ Migrations applied successfully!")
        
        # Show updated status
        status = manager.get_migration_status()
        print_status(status)
        
    except Exception as e:
        print(f"\n✗ Migration failed: {str(e)}")
        sys.exit(1)


def migrate_down(manager, target_version):
    """Rollback migrations."""
    if target_version is None:
        print("\n✗ Error: --target is required for rollback")
        print("Usage: python migrate.py down --target <version>")
        sys.exit(1)
    
    print(f"\n🔄 Rolling back to version {target_version}...")
    
    # Confirm if rolling back everything
    if target_version == '0' or target_version == '000':
        response = input("\n⚠️  WARNING: This will rollback ALL migrations. Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Rollback cancelled.")
            sys.exit(0)
    
    try:
        manager.migrate_down(target_version=target_version)
        print("✓ Rollback completed successfully!")
        
        # Show updated status
        status = manager.get_migration_status()
        print_status(status)
        
    except Exception as e:
        print(f"\n✗ Rollback failed: {str(e)}")
        sys.exit(1)


def main():
    """Main entry point for migration script."""
    parser = argparse.ArgumentParser(
        description='Database Migration Management',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python migrate.py status                    # Show migration status
  python migrate.py up                        # Apply all pending migrations
  python migrate.py up --target 001           # Apply up to version 001
  python migrate.py down --target 001         # Rollback to version 001
  python migrate.py down --target 0           # Rollback all migrations
        """
    )
    
    parser.add_argument(
        'command',
        choices=['status', 'up', 'down'],
        help='Migration command to execute'
    )
    
    parser.add_argument(
        '--target',
        type=str,
        help='Target migration version'
    )
    
    args = parser.parse_args()
    
    # Initialize database connection
    try:
        print("\n🔌 Connecting to database...")
        config = get_config()
        db.initialize(config.MONGODB_URI, config.MONGODB_DB_NAME)
        print(f"✓ Connected to database: {config.MONGODB_DB_NAME}")
    except Exception as e:
        print(f"\n✗ Database connection failed: {str(e)}")
        print("\nMake sure:")
        print("  1. MongoDB is running")
        print("  2. .env file exists with correct MONGODB_URI")
        print("  3. Database credentials are valid")
        sys.exit(1)
    
    # Initialize migration manager
    manager = MigrationManager(db.get_db())
    
    # Execute command
    if args.command == 'status':
        status = manager.get_migration_status()
        print_status(status)
        
    elif args.command == 'up':
        migrate_up(manager, args.target)
        
    elif args.command == 'down':
        migrate_down(manager, args.target)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Unexpected error: {str(e)}")
        sys.exit(1)
