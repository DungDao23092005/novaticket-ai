"""
schemas/category.py — Pydantic schemas for Category.

Schemas:
    CategoryResponse  — returned by GET /categories and nested in events
    CategoryCreate    — request body for POST /categories (admin only)
"""

from pydantic import BaseModel, ConfigDict, Field


class CategoryCreate(BaseModel):
    """Request body for creating a new category."""
    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Unique category name",
        examples=["Technology"],
    )
    description: str | None = Field(
        default=None,
        max_length=500,
        description="Optional category description",
        examples=["Tech conferences, hackathons, workshops"],
    )


class CategoryResponse(BaseModel):
    """Category data returned by API endpoints."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
