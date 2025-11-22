"""
Base migration class for database schema evolution.

All migrations should inherit from this class and implement
the upgrade() and downgrade() methods.
"""

from abc import ABC, abstractmethod
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BaseMigration(ABC):
    """
    Abstract base class for database migrations.
    
    Attributes:
        version (str): Migration version identifier (e.g., "001", "002")
        description (str): Human-readable description of the migration
        created_at (datetime): When this migration was created
    """

    version = None
    description = None

    def __init__(self, db):
        """
        Initialize migration with database connection.
        
        Args:
            db: MongoDB database instance
        """
        if not self.version:
            raise ValueError("Migration must have a version identifier")
        if not self.description:
            raise ValueError("Migration must have a description")
            
        self.db = db
        self.created_at = datetime.utcnow()

    @abstractmethod
    def upgrade(self):
        """
        Execute migration to upgrade database schema/data.
        
        This method should contain all forward migration logic.
        Must be idempotent - safe to run multiple times.
        
        Raises:
            Exception: If migration fails
        """
        pass

    @abstractmethod
    def downgrade(self):
        """
        Rollback migration to previous state.
        
        This method should undo all changes made in upgrade().
        Must be idempotent - safe to run multiple times.
        
        Raises:
            Exception: If rollback fails
        """
        pass

    def log_info(self, message):
        """Log migration info message."""
        logger.info(f"[Migration {self.version}] {message}")

    def log_warning(self, message):
        """Log migration warning message."""
        logger.warning(f"[Migration {self.version}] {message}")

    def log_error(self, message):
        """Log migration error message."""
        logger.error(f"[Migration {self.version}] {message}")

    def __repr__(self):
        """String representation of migration."""
        return f"<Migration {self.version}: {self.description}>"
