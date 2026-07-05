"""
routers/categories.py — Category CRUD endpoints.

Pattern: Thin router — delegates all business logic to CategoryRepository.
Categories are reference data (seeded), so write endpoints are admin-only
(protected by JWT for now; admin role can be added later).

Endpoints:
    GET  /categories        — List all categories
    GET  /categories/{id}   — Get category by ID
    POST /categories        — Create new category (requires auth)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user
from app.database.connection import get_db
from app.models.user import User
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryResponse

router = APIRouter(prefix="/categories", tags=["Categories"])


# ----------------------------------------------------------------------
# GET /categories
# ----------------------------------------------------------------------
@router.get(
    "",
    response_model=list[CategoryResponse],
    summary="List all categories",
)
def list_categories(
    db: Session = Depends(get_db),
) -> list:
    """
    Returns all event categories, ordered by name.
    Public endpoint — no authentication required.
    """
    repo = CategoryRepository(db)
    return repo.get_all()


# ----------------------------------------------------------------------
# GET /categories/{category_id}
# ----------------------------------------------------------------------
@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Get category by ID",
)
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
):
    """
    Returns a single category by ID.
    Public endpoint — no authentication required.
    """
    repo = CategoryRepository(db)
    category = repo.get_by_id(category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id={category_id} not found",
        )
    return category


# ----------------------------------------------------------------------
# POST /categories (requires auth — logged-in users only for now)
# ----------------------------------------------------------------------
@router.post(
    "",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new category (requires auth)",
)
def create_category(
    body: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create a new event category.
    Requires authentication. Name must be unique.
    """
    repo = CategoryRepository(db)

    if repo.exists_by_name(body.name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Category '{body.name}' already exists",
        )

    return repo.create(name=body.name, description=body.description)
