"""
repositories/interaction_repository.py — Database access layer for UserInteraction.

Interactions are the raw signal data for the Recommendation Engine.
Key read patterns:
    - Get all interactions for a user (CF: build user vector)
    - Get all interactions for an event (popularity signal)
    - Check if interaction already exists (upsert logic)
"""

from sqlalchemy.orm import Session

from app.models.interaction import UserInteraction


class InteractionRepository:
    """Encapsulates all DB queries for the UserInteraction entity."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_by_user(self, user_id: int) -> list[UserInteraction]:
        """
        Get all interactions for a user, ordered by most recent.
        Used by: Recommendation Engine (build user history vector).
        """
        return (
            self.db.query(UserInteraction)
            .filter(UserInteraction.user_id == user_id)
            .order_by(UserInteraction.created_at.desc())
            .all()
        )

    def get_by_user_and_event(
        self,
        user_id: int,
        event_id: int,
        interaction_type: str,
    ) -> UserInteraction | None:
        """
        Find an existing interaction of a specific type for (user, event).
        Used for upsert logic: if exists → update score; if not → insert.
        """
        return (
            self.db.query(UserInteraction)
            .filter(
                UserInteraction.user_id == user_id,
                UserInteraction.event_id == event_id,
                UserInteraction.interaction_type == interaction_type,
            )
            .first()
        )

    def get_all_for_recommendation(self) -> list[UserInteraction]:
        """
        Return all interactions in the system.
        Used by the offline training pipeline to build the User-Item matrix.
        """
        return self.db.query(UserInteraction).all()

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def create(
        self,
        *,
        user_id: int,
        event_id: int,
        interaction_type: str,
        interaction_score: float,
    ) -> UserInteraction:
        """
        Record a new user interaction.

        Args:
            user_id:          ID of the user
            event_id:         ID of the event
            interaction_type: one of 'view', 'click', 'register', 'favorite'
            interaction_score: numeric weight for this interaction type

        Returns:
            The created UserInteraction ORM instance.
        """
        interaction = UserInteraction(
            user_id=user_id,
            event_id=event_id,
            interaction_type=interaction_type,
            interaction_score=interaction_score,
        )
        self.db.add(interaction)
        self.db.commit()
        self.db.refresh(interaction)
        return interaction

    def upsert(
        self,
        *,
        user_id: int,
        event_id: int,
        interaction_type: str,
        interaction_score: float,
    ) -> UserInteraction:
        """
        Insert a new interaction, or update score if the same (user, event, type) exists.

        This prevents duplicate rows for the same interaction type.
        Example: user views same event twice → score updated, not duplicated.

        Returns:
            The created or updated UserInteraction ORM instance.
        """
        existing = self.get_by_user_and_event(user_id, event_id, interaction_type)

        if existing:
            # Update score (keep latest signal strength)
            existing.interaction_score = interaction_score
            self.db.commit()
            self.db.refresh(existing)
            return existing

        return self.create(
            user_id=user_id,
            event_id=event_id,
            interaction_type=interaction_type,
            interaction_score=interaction_score,
        )
