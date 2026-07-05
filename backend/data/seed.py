"""
data/seed.py — Database seeding script.

Loads seed data from CSV files into the SQL Server database.
This script is idempotent: running it multiple times will NOT create duplicates.

Usage (from backend/ directory, with venv activated):
    python data/seed.py

What this seeds:
    1. Categories (from seed_categories.csv)
    2. Events (from seed_events.csv)
    3. Reviews (from seed_reviews.csv) — with sentiment labels for ML training

Design:
    - Check-before-insert pattern to ensure idempotency
    - Categories seeded first (events have FK to categories)
    - Events reference categories by name (resolved to FK at insert time)
    - Reviews distributed across all events; seed users auto-created if absent
    - Tags stored as comma-separated string (ML pipeline will parse them)
"""

import csv
import sys
import os
from datetime import datetime
from decimal import Decimal
from pathlib import Path

# Add backend/ to sys.path so we can import app modules
# This allows running: python data/seed.py from backend/
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.database.connection import SessionLocal
from app.models.category import Category
from app.models.event import Event
from app.models.user import User
from app.models.review import Review
from app.core.security import hash_password


# ----------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------
DATA_DIR = Path(__file__).parent
CATEGORIES_CSV = DATA_DIR / "seed_categories.csv"
EVENTS_CSV = DATA_DIR / "seed_events.csv"
REVIEWS_CSV = DATA_DIR / "seed_reviews.csv"

# Seed user credentials — created automatically if not present
SEED_USERS = [
    {"email": "seed_user1@novaticket.dev", "username": "seed_user1", "password": "SeedPass123!", "full_name": "Seed User 1"},
    {"email": "seed_user2@novaticket.dev", "username": "seed_user2", "password": "SeedPass123!", "full_name": "Seed User 2"},
    {"email": "seed_user3@novaticket.dev", "username": "seed_user3", "password": "SeedPass123!", "full_name": "Seed User 3"},
]


# ----------------------------------------------------------------------
# Seeding functions
# ----------------------------------------------------------------------

def seed_categories(db) -> dict[str, int]:
    """
    Insert categories from CSV.
    Returns a dict mapping category name → category id for use when seeding events.
    """
    print("\n[1/2] Seeding categories...")

    with open(CATEGORIES_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    inserted = 0
    skipped = 0
    category_map: dict[str, int] = {}

    for row in rows:
        name = row["name"].strip()
        description = row["description"].strip()

        # Check if already exists (idempotent)
        existing = db.query(Category).filter_by(name=name).first()
        if existing:
            category_map[name] = existing.id
            skipped += 1
            continue

        category = Category(name=name, description=description)
        db.add(category)
        db.flush()  # Get the ID without committing
        category_map[name] = category.id
        inserted += 1
        print(f"  + Category: {name}")

    db.commit()
    print(f"  → Inserted: {inserted}, Skipped (already exists): {skipped}")
    return category_map


def seed_events(db, category_map: dict[str, int]) -> None:
    """
    Insert events from CSV.
    category_map: dict mapping category name → category id
    """
    print("\n[2/2] Seeding events...")

    with open(EVENTS_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    inserted = 0
    skipped = 0

    for row in rows:
        title = row["title"].strip()

        # Check if already exists (idempotent)
        existing = db.query(Event).filter_by(title=title).first()
        if existing:
            skipped += 1
            continue

        # Resolve category FK
        category_name = row["category_name"].strip()
        category_id = category_map.get(category_name)
        if not category_id:
            print(f"  ! Warning: Category '{category_name}' not found for event '{title}'. Skipping.")
            continue

        # Parse dates
        start_date = datetime.strptime(row["start_date"].strip(), "%Y-%m-%d %H:%M:%S")
        end_date_str = row.get("end_date", "").strip()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d %H:%M:%S") if end_date_str else None

        # Parse numeric fields
        price_str = row.get("price", "0").strip()
        price = Decimal(price_str) if price_str else Decimal("0")

        capacity_str = row.get("capacity", "").strip()
        capacity = int(capacity_str) if capacity_str else None

        # Build tags string — CSV uses | separator to avoid comma conflicts
        # Store as comma-separated in DB (ML pipeline expects this format)
        tags_raw = row.get("tags", "").strip()
        if tags_raw:
            # Convert pipe-separated → comma-separated for DB storage
            tags = ",".join(t.strip() for t in tags_raw.split("|") if t.strip())
        else:
            tags = None

        event = Event(
            title=title,
            description=row.get("description", "").strip() or None,
            category_id=category_id,
            venue=row.get("venue", "").strip() or None,
            city=row.get("city", "").strip() or None,
            start_date=start_date,
            end_date=end_date,
            price=price,
            capacity=capacity,
            tags=tags,
            is_active=True,
        )
        db.add(event)
        inserted += 1
        print(f"  + Event: {title[:60]}...")

    db.commit()
    print(f"  → Inserted: {inserted}, Skipped (already exists): {skipped}")


def seed_users(db) -> list[int]:
    """
    Create seed users for review seeding.
    Returns list of user IDs.
    """
    print("\n[3/4] Seeding users (for review data)...")
    user_ids = []
    inserted = 0
    skipped = 0

    for u in SEED_USERS:
        existing = db.query(User).filter_by(email=u["email"]).first()
        if existing:
            user_ids.append(existing.id)
            skipped += 1
            continue
        user = User(
            email=u["email"],
            username=u["username"],
            hashed_password=hash_password(u["password"]),
            full_name=u["full_name"],
            is_active=True,
        )
        db.add(user)
        db.flush()
        user_ids.append(user.id)
        inserted += 1
        print(f"  + User: {u['username']}")

    db.commit()
    print(f"  → Inserted: {inserted}, Skipped: {skipped}")
    return user_ids


def seed_reviews(db, user_ids: list[int]) -> None:
    """
    Insert reviews from seed_reviews.csv.
    Reviews are distributed round-robin across all events and seed users.
    Skips if review content already exists in DB (idempotent).
    """
    print("\n[4/4] Seeding reviews...")

    if not REVIEWS_CSV.exists():
        print(f"  ! REVIEWS_CSV not found: {REVIEWS_CSV}. Skipping.")
        return

    with open(REVIEWS_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Get all active event IDs from DB
    event_ids = [e.id for e in db.query(Event.id).filter(Event.is_active == True).all()]
    if not event_ids:
        print("  ! No events in DB. Skipping reviews.")
        return

    # Pre-load existing (user_id, event_id) pairs from DB into a set
    # DB queries can't see uncommitted session objects, so we track with a Python set
    existing_pairs: set[tuple[int, int]] = {
        (r.user_id, r.event_id)
        for r in db.query(Review.user_id, Review.event_id).all()
    }
    existing_contents: set[str] = {
        r.content for r in db.query(Review.content).all()
    }

    inserted = 0
    skipped = 0

    for i, row in enumerate(rows):
        content = row["content"].strip().strip('"')
        rating = int(row["rating"].strip())
        sentiment_label = row["sentiment_label"].strip()

        # Skip if content already in DB (idempotent)
        if content in existing_contents:
            skipped += 1
            continue

        # Find a valid (user, event) pair not already used
        # Cycle through events and users to find an unused pair
        user_id = None
        event_id = None

        for e_offset in range(len(event_ids)):
            candidate_event = event_ids[(i + e_offset) % len(event_ids)]
            for u_offset in range(len(user_ids)):
                candidate_user = user_ids[(i + u_offset) % len(user_ids)]
                if (candidate_user, candidate_event) not in existing_pairs:
                    user_id = candidate_user
                    event_id = candidate_event
                    break
            if user_id is not None:
                break

        if user_id is None:
            # All (user, event) combinations exhausted — skip
            skipped += 1
            continue

        # Track assignment in-memory immediately (before commit)
        existing_pairs.add((user_id, event_id))
        existing_contents.add(content)

        review = Review(
            user_id=user_id,
            event_id=event_id,
            rating=rating,
            content=content,
            sentiment_label=sentiment_label,
            sentiment_confidence=None,
        )
        db.add(review)
        inserted += 1

    db.commit()
    print(f"  → Inserted: {inserted}, Skipped: {skipped}")


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main() -> None:
    print("=" * 60)
    print("NovaTicket — Database Seed Script")
    print("=" * 60)

    # Verify CSV files exist
    for csv_path, name in [(CATEGORIES_CSV, "categories"), (EVENTS_CSV, "events")]:
        if not csv_path.exists():
            print(f"ERROR: {csv_path} not found")
            sys.exit(1)

    db = SessionLocal()
    try:
        category_map = seed_categories(db)
        seed_events(db, category_map)
        user_ids = seed_users(db)
        seed_reviews(db, user_ids)

        # Summary
        total_categories = db.query(Category).count()
        total_events = db.query(Event).count()
        total_reviews = db.query(Review).count()
        print(f"\n{'=' * 60}")
        print(f"Seed complete!")
        print(f"  Total categories in DB: {total_categories}")
        print(f"  Total events in DB:     {total_events}")
        print(f"  Total reviews in DB:    {total_reviews}")
        print(f"{'=' * 60}")

    except Exception as e:
        db.rollback()
        print(f"\nERROR: Seed failed — {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
