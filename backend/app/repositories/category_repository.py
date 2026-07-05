"""
repositories/category_repository.py — Database access layer for Category.

Follows same Repository pattern as UserRepository:
- Isolates all SQLAlchemy queries from business logic
- Services call these methods; never raw db.query() in routers
"""

from sqlalchemy.orm import Session

from app.models.category import Category


class CategoryRepository:
    """Encapsulates all DB queries for the Category entity."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_all(self) -> list[Category]:
        """Return all categories ordered by name."""
        return self.db.query(Category).order_by(Category.name).all()

    def get_by_id(self, category_id: int) -> Category | None:
        """Fetch category by primary key. Returns None if not found."""
        return self.db.query(Category).filter(Category.id == category_id).first()

    def get_by_name(self, name: str) -> Category | None:
        """Fetch category by exact name (case-sensitive). Returns None if not found."""
        return self.db.query(Category).filter(Category.name == name).first()

    def exists_by_name(self, name: str) -> bool:
        """Check if a category with the given name already exists."""
        return (
            self.db.query(Category)
            .filter(Category.name == name)
            .first() is not None
        )

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def create(self, *, name: str, description: str | None = None) -> Category:
        """
        Insert a new category.

        Args:
            name: Unique category name
            description: Optional category description

        Returns:
            The created Category ORM instance with id populated.
        """
        category = Category(name=name, description=description)
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category
