"""
schemas/interaction.py — Pydantic schemas for UserInteraction.

Interaction types (aligned with ORM CHECK constraint):
    view      — User viewed the event detail page
    click     — User clicked on event card
    register  — User registered / bought ticket for event
    favorite  — User favorited / bookmarked the event

Scores used by Recommendation Engine:
    view      → 1.0
    click     → 2.0
    favorite  → 3.0
    register  → 5.0  (strongest signal)
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# Valid interaction types — must match CHECK constraint in ORM model
InteractionType = Literal["view", "click", "register", "favorite"]

# Score map — used by service to set interaction_score automatically
INTERACTION_SCORES: dict[str, float] = {
    "view": 1.0,
    "click": 2.0,
    "favorite": 3.0,
    "register": 5.0,
}


class InteractionCreate(BaseModel):
    """Request body for POST /interactions."""
    event_id: int = Field(..., description="ID of the event being interacted with")
    interaction_type: InteractionType = Field(
        ...,
        description="Type of interaction: view | click | register | favorite",
        examples=["view"],
    )


class InteractionResponse(BaseModel):
    """Response schema after recording an interaction."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    event_id: int
    interaction_type: str
    interaction_score: float
    created_at: datetime
