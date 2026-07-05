"""
data/seed.py — Database seeding script.

Loads seed data from CSV files into the SQL Server database.
This script is idempotent: running it multiple times will NOT create duplicates.

Usage (from backend/ directory, with venv activated):
    python data/seed.py

What this seeds:
    1. Categories (from seed_categories.csv)
    2. Events (from seed_events.csv)

Design:
    - Check-before-insert pattern to ensure idempotency
    - Categories are seeded first (events have FK to categories)
    - Events reference categories by name (resolved to FK at insert time)
    - Dates parsed from ISO format strings
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


# ----------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------
DATA_DIR = Path(__file__).parent
CATEGORIES_CSV = DATA_DIR / "seed_categories.csv"
EVENTS_CSV = DATA_DIR / "seed_events.csv"


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


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main() -> None:
    print("=" * 60)
    print("NovaTicket — Database Seed Script")
    print("=" * 60)

    # Verify CSV files exist
    if not CATEGORIES_CSV.exists():
        print(f"ERROR: {CATEGORIES_CSV} not found")
        sys.exit(1)
    if not EVENTS_CSV.exists():
        print(f"ERROR: {EVENTS_CSV} not found")
        sys.exit(1)

    db = SessionLocal()
    try:
        category_map = seed_categories(db)
        seed_events(db, category_map)

        # Summary
        total_categories = db.query(Category).count()
        total_events = db.query(Event).count()
        print(f"\n{'=' * 60}")
        print(f"Seed complete!")
        print(f"  Total categories in DB: {total_categories}")
        print(f"  Total events in DB:     {total_events}")
        print(f"{'=' * 60}")

    except Exception as e:
        db.rollback()
        print(f"\nERROR: Seed failed — {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
