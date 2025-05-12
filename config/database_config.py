# config/database_config.py

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from models import Base


class DatabaseManager:
    """Manages database connection and session creation"""

    def __init__(self, db_path=None):
        if db_path is None:
            # Create database in the application directory
            app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(app_dir, "edsi_database.db")

        self.database_url = f"sqlite:///{db_path}"
        self.engine = None
        self.session_factory = None
        self.Session = None

    def initialize_database(self):
        """Initialize database connection and create tables"""
        self.engine = create_engine(
            self.database_url,
            echo=False,  # Set to True for SQL logging
            pool_pre_ping=True,
            connect_args={"check_same_thread": False},  # Needed for SQLite
        )

        # Create all tables
        Base.metadata.create_all(self.engine)

        # Create session factory
        self.session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.session_factory)

        # Create default admin user if it doesn't exist
        self._create_default_user()

    def get_session(self):
        """Get a new database session"""
        return self.Session()

    def close_session(self):
        """Close the current session"""
        self.Session.remove()

    def _create_default_user(self):
        """Create default admin user if none exists"""
        from models import User
        import hashlib

        session = self.get_session()
        try:
            # Check if any users exist
            user_count = session.query(User).count()
            if user_count == 0:
                # Create default admin user
                default_password = (
                    "admin123"  # In production, this should be more secure
                )
                password_hash = hashlib.sha256(default_password.encode()).hexdigest()

                admin_user = User(
                    user_id="ADMIN",
                    password_hash=password_hash,
                    user_name="System Administrator",
                    is_active=True,
                )
                session.add(admin_user)
                session.commit()
                print("Created default admin user (ADMIN/admin123)")
        finally:
            session.close()

    def close(self):
        """Close database connection"""
        if self.engine:
            self.engine.dispose()


# Global database manager instance
db_manager = DatabaseManager()
