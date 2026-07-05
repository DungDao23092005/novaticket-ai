"""
repositories/user_repository.py — Database access layer for User.

Pattern: Repository isolates all SQLAlchemy queries from business logic.
- Services call repository methods (not raw db.query())
- Easier to test (can mock repository)
- Single place to change if query logic needs updating

All methods receive a db Session (injected by service or dependency).
"""

from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    """Encapsulates all DB queries for the User entity."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_by_id(self, user_id: int) -> User | None:
        """Fetch user by primary key. Returns None if not found."""
        return (
            self.db.query(User)
            .filter(User.id == user_id)
            .first()
        )

    def get_by_email(self, email: str) -> User | None:
        """Fetch user by email (case-insensitive). Returns None if not found."""
        return (
            self.db.query(User)
            .filter(User.email == email.lower())
            .first()
        )

    def get_by_username(self, username: str) -> User | None:
        """Fetch user by username. Returns None if not found."""
        return (
            self.db.query(User)
            .filter(User.username == username)
            .first()
        )

    def exists_by_email(self, email: str) -> bool:
        """Check if a user with the given email already exists.
        Uses TOP 1 SELECT — SQL Server compatible (avoids EXISTS subquery syntax).
        """
        return self.db.query(User).filter(User.email == email.lower()).first() is not None

    def exists_by_username(self, username: str) -> bool:
        """Check if a user with the given username already exists.
        Uses TOP 1 SELECT — SQL Server compatible.
        """
        return self.db.query(User).filter(User.username == username).first() is not None

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def create(
        self,
        *,
        email: str,
        username: str,
        hashed_password: str,
        full_name: str | None = None,
    ) -> User:
        """
        Insert a new user into the database.
        Commits the transaction and refreshes the instance.

        Args:
            email: Unique email address (stored lowercase)
            username: Unique username
            hashed_password: bcrypt hash (NEVER plaintext)
            full_name: Optional display name

        Returns:
            The created User ORM instance with id and created_at populated.
        """
        user = User(
            email=email.lower(),
            username=username,
            hashed_password=hashed_password,
            full_name=full_name,
            is_active=True,
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return user

    def update_active_status(
        self,
        user_id: int,
        is_active: bool,
    ) -> User | None:
        """Activate or deactivate a user account."""
        user = self.get_by_id(user_id)

        if not user:
            return None

        user.is_active = is_active

        self.db.commit()
        self.db.refresh(user)

        return user