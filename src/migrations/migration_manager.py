"""
Migration manager for database schema evolution.

This module manages the execution and tracking of database migrations,
ensuring proper versioning and rollback capabilities.
"""

from datetime import datetime
from pymongo import ASCENDING
import logging
import importlib
import os
import sys

logger = logging.getLogger(__name__)


class MigrationManager:
    """
    Manages database migrations with version tracking.
    
    Migrations are stored in the 'migrations/versions' directory and
    tracked in the 'schema_migrations' collection.
    """

    MIGRATIONS_COLLECTION = 'schema_migrations'
    MIGRATIONS_DIR = 'migrations/versions'

    def __init__(self, db):
        """
        Initialize migration manager.
        
        Args:
            db: MongoDB database instance
        """
        self.db = db
        self._ensure_migrations_collection()

    def _ensure_migrations_collection(self):
        """Create migrations collection with proper indexes if it doesn't exist."""
        if self.MIGRATIONS_COLLECTION not in self.db.list_collection_names():
            self.db.create_collection(self.MIGRATIONS_COLLECTION)
            self.db[self.MIGRATIONS_COLLECTION].create_index(
                [('version', ASCENDING)], 
                unique=True
            )
            logger.info(f"Created {self.MIGRATIONS_COLLECTION} collection")

    def get_current_version(self):
        """
        Get the current migration version from database.
        
        Returns:
            str: Current version or None if no migrations applied
        """
        result = self.db[self.MIGRATIONS_COLLECTION].find_one(
            sort=[('applied_at', -1)]
        )
        return result['version'] if result else None

    def get_applied_migrations(self):
        """
        Get list of all applied migrations.
        
        Returns:
            list: List of applied migration documents
        """
        return list(self.db[self.MIGRATIONS_COLLECTION].find(
            sort=[('applied_at', ASCENDING)]
        ))

    def is_migration_applied(self, version):
        """
        Check if a specific migration has been applied.
        
        Args:
            version (str): Migration version to check
            
        Returns:
            bool: True if migration is applied
        """
        return self.db[self.MIGRATIONS_COLLECTION].find_one(
            {'version': version}
        ) is not None

    def record_migration(self, migration):
        """
        Record a migration as applied.
        
        Args:
            migration: BaseMigration instance
        """
        self.db[self.MIGRATIONS_COLLECTION].insert_one({
            'version': migration.version,
            'description': migration.description,
            'applied_at': datetime.utcnow(),
            'status': 'applied'
        })
        logger.info(f"Recorded migration {migration.version} as applied")

    def remove_migration_record(self, version):
        """
        Remove migration record (used during rollback).
        
        Args:
            version (str): Migration version to remove
        """
        self.db[self.MIGRATIONS_COLLECTION].delete_one({'version': version})
        logger.info(f"Removed migration record {version}")

    def load_migrations(self):
        """
        Load all migration classes from the versions directory.
        
        Returns:
            dict: Dictionary of {version: MigrationClass}
        """
        migrations = {}
        migrations_path = os.path.join(
            os.path.dirname(__file__), 
            'versions'
        )

        if not os.path.exists(migrations_path):
            logger.warning(f"Migrations directory not found: {migrations_path}")
            return migrations

        # Add migrations directory to Python path
        if migrations_path not in sys.path:
            sys.path.insert(0, migrations_path)

        # Load all Python files in versions directory
        for filename in sorted(os.listdir(migrations_path)):
            if filename.endswith('.py') and not filename.startswith('__'):
                module_name = filename[:-3]
                try:
                    module = importlib.import_module(f'migrations.versions.{module_name}')
                    
                    # Find migration class in module
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (isinstance(attr, type) and 
                            hasattr(attr, 'version') and 
                            hasattr(attr, 'upgrade')):
                            migrations[attr.version] = attr
                            logger.debug(f"Loaded migration: {attr.version}")
                except Exception as e:
                    logger.error(f"Error loading migration {filename}: {e}")

        return migrations

    def migrate_up(self, target_version=None):
        """
        Run pending migrations up to target version.
        
        Args:
            target_version (str, optional): Version to migrate to. 
                                          None means migrate to latest.
                                          
        Returns:
            int: Number of migrations applied
        """
        migrations = self.load_migrations()
        current_version = self.get_current_version()
        applied_count = 0

        # Get pending migrations
        pending = []
        for version in sorted(migrations.keys()):
            if not self.is_migration_applied(version):
                if target_version is None or version <= target_version:
                    pending.append(version)

        logger.info(f"Found {len(pending)} pending migration(s)")

        # Apply each pending migration
        for version in pending:
            migration_class = migrations[version]
            migration = migration_class(self.db)

            logger.info(f"Applying migration {version}: {migration.description}")
            
            try:
                migration.upgrade()
                self.record_migration(migration)
                applied_count += 1
                logger.info(f"Successfully applied migration {version}")
            except Exception as e:
                logger.error(f"Migration {version} failed: {e}")
                raise

        return applied_count

    def migrate_down(self, target_version=None):
        """
        Rollback migrations to target version.
        
        Args:
            target_version (str, optional): Version to rollback to.
                                          None means rollback all.
                                          
        Returns:
            int: Number of migrations rolled back
        """
        migrations = self.load_migrations()
        applied = self.get_applied_migrations()
        rollback_count = 0

        # Get migrations to rollback (in reverse order)
        to_rollback = []
        for migration_doc in reversed(applied):
            version = migration_doc['version']
            if target_version is None or version > target_version:
                to_rollback.append(version)

        logger.info(f"Rolling back {len(to_rollback)} migration(s)")

        # Rollback each migration
        for version in to_rollback:
            if version not in migrations:
                logger.error(f"Migration class not found for version {version}")
                continue

            migration_class = migrations[version]
            migration = migration_class(self.db)

            logger.info(f"Rolling back migration {version}: {migration.description}")

            try:
                migration.downgrade()
                self.remove_migration_record(version)
                rollback_count += 1
                logger.info(f"Successfully rolled back migration {version}")
            except Exception as e:
                logger.error(f"Rollback of migration {version} failed: {e}")
                raise

        return rollback_count

    def get_migration_status(self):
        """
        Get current migration status.
        
        Returns:
            dict: Status information including current version and pending migrations
        """
        migrations = self.load_migrations()
        applied = set(m['version'] for m in self.get_applied_migrations())
        pending = [v for v in sorted(migrations.keys()) if v not in applied]

        return {
            'current_version': self.get_current_version(),
            'total_migrations': len(migrations),
            'applied_count': len(applied),
            'pending_count': len(pending),
            'applied_migrations': sorted(applied),
            'pending_migrations': pending
        }
