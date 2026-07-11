"""
data/load_kaggle.py — Load Kaggle Event Recommendation Engine dataset into NovaTicket DB.

Usage:
    python data/load_kaggle.py --data-dir ./kaggle_data [--sample 10000]

Expected files in data-dir:
    train.csv, users.csv, events.csv

Mapping:
    Kaggle user  → NovaTicket User (email: kaggle_{id}@novaticket.dev)
    Kaggle event → NovaTicket Event (title + description from location + bag-of-words)
    Kaggle interested=1  → interaction_type='register', score=5.0
    Kaggle not_interested=1 → interaction_type='click', score=2.0
    Kaggle invited + no response → interaction_type='view', score=1.0
"""

import argparse
import csv
import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text

from app.core.security import hash_password
from app.database.connection import SessionLocal
from app.models.event import Event
from app.models.interaction import UserInteraction
from app.models.user import User

BATCH_SIZE = 2000
ID_OFFSET = 1_000_000
SEED_PASSWORD = "KagglePass123!"
HASHED_SEED_PASSWORD = hash_password(SEED_PASSWORD)


def parse_timestamp(ts_str: str) -> datetime:
    try:
        return datetime.fromtimestamp(int(ts_str), tz=timezone.utc)
    except (ValueError, OSError):
        return datetime.now(timezone.utc)


def build_event_description(row: dict[str, str], word_keys: list[str]) -> str:
    parts = []
    city = row.get("city", "").strip()
    state = row.get("state", "").strip()
    country = row.get("country", "").strip()
    loc_parts = [p for p in [city, state, country] if p]
    if loc_parts:
        parts.append(" ".join(loc_parts))

    word_repeats = []
    for key in word_keys:
        freq = row.get(key, "0").strip()
        if freq and freq not in ("0", "0.0"):
            count = max(1, int(float(freq)))
            word_repeats.extend([key] * min(count, 20))

    if word_repeats:
        parts.append(" ".join(word_repeats[:200]))

    return ". ".join(parts) if parts else ""


def bulk_insert(db, table, rows: list[dict], identity_col: str | None = None) -> None:
    """Bulk insert rows with optional identity_insert for SQL Server."""
    if identity_col:
        db.execute(text(f"SET IDENTITY_INSERT {table.name} ON"))
    db.execute(table.insert(), rows)
    if identity_col:
        db.execute(text(f"SET IDENTITY_INSERT {table.name} OFF"))
    db.commit()


def load_kaggle(data_dir: Path, sample: int | None = None) -> None:
    print("=" * 60)
    print("NovaTicket — Kaggle Dataset Importer")
    print("=" * 60)

    for name in ("users.csv", "events.csv", "train.csv"):
        if not (data_dir / name).exists():
            print(f"ERROR: {data_dir / name} not found")
            sys.exit(1)

    db = SessionLocal()
    try:
        # ----------------------------------------------------------------
        # 1. Load users
        # ----------------------------------------------------------------
        print("\n[1/4] Loading users...")
        existing_user_ids = {r[0] for r in db.query(User.id).all()}
        new_users = []
        total_users = 0

        with open(data_dir / "users.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            if sample:
                rows = rows[:sample]

            for row in rows:
                kaggle_id = int(row["user_id"].strip())
                full_id = kaggle_id + ID_OFFSET
                if full_id in existing_user_ids:
                    continue
                joined_at = parse_timestamp(row.get("joinedAt", "0"))
                new_users.append({
                    "id": full_id,
                    "email": f"kaggle_{kaggle_id}@novaticket.dev",
                    "username": f"kaggle_{kaggle_id}",
                    "hashed_password": HASHED_SEED_PASSWORD,
                    "full_name": None,
                    "is_active": True,
                    "created_at": joined_at,
                })
                if len(new_users) >= BATCH_SIZE:
                    bulk_insert(db, User.__table__, new_users, identity_col="id")
                    total_users += len(new_users)
                    print(f"  Inserted {total_users} users...")
                    new_users = []

            if new_users:
                bulk_insert(db, User.__table__, new_users, identity_col="id")
                total_users += len(new_users)

        print(f"  Total users: {db.query(User).count()}")

        # ----------------------------------------------------------------
        # 2. Load events
        # ----------------------------------------------------------------
        print("\n[2/4] Loading events...")
        existing_event_ids = {r[0] for r in db.query(Event.id).all()}
        word_keys = [f"c_{i}" for i in range(1, 101)] + ["c_other"]
        new_events = []
        total_events = 0

        with open(data_dir / "events.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            if sample:
                rows = rows[:sample]

            for row in rows:
                kaggle_event_id = int(row["event_id"].strip())
                full_id = kaggle_event_id + ID_OFFSET
                if full_id in existing_event_ids:
                    continue
                start_time = parse_timestamp(row.get("start_time", "0"))
                description = build_event_description(row, word_keys)
                new_events.append({
                    "id": full_id,
                    "title": f"Kaggle Event #{kaggle_event_id}",
                    "description": description or None,
                    "category_id": None,
                    "venue": None,
                    "city": row.get("city", "").strip() or None,
                    "start_date": start_time,
                    "end_date": None,
                    "price": Decimal("0.00"),
                    "capacity": None,
                    "tags": None,
                    "is_active": True,
                })
                if len(new_events) >= BATCH_SIZE:
                    bulk_insert(db, Event.__table__, new_events, identity_col="id")
                    total_events += len(new_events)
                    print(f"  Inserted {total_events} events...")
                    new_events = []

            if new_events:
                bulk_insert(db, Event.__table__, new_events, identity_col="id")
                total_events += len(new_events)

        print(f"  Total events: {db.query(Event).count()}")

        # ----------------------------------------------------------------
        # 3. Load interactions
        # ----------------------------------------------------------------
        print("\n[3/4] Loading interactions...")
        existing_pairs = {
            (r.user_id, r.event_id, r.interaction_type)
            for r in db.query(
                UserInteraction.user_id, UserInteraction.event_id,
                UserInteraction.interaction_type,
            ).all()
        }
        new_interactions = []
        total_ints = 0

        known_users = existing_user_ids | {r.id for r in db.query(User.id).all()}
        known_events = existing_event_ids | {r.id for r in db.query(Event.id).all()}

        with open(data_dir / "train.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            if sample:
                rows = rows[:sample]

            for row in rows:
                user_id = int(row["user"].strip()) + ID_OFFSET
                event_id = int(row["event"].strip()) + ID_OFFSET
                if user_id not in known_users or event_id not in known_events:
                    continue

                interested = int(row.get("interested", "0").strip())
                not_interested = int(row.get("not_interested", "0").strip())
                if interested:
                    itype, score = "register", 5.0
                elif not_interested:
                    itype, score = "click", 2.0
                else:
                    itype, score = "view", 1.0

                key = (user_id, event_id, itype)
                if key in existing_pairs:
                    continue
                existing_pairs.add(key)

                new_interactions.append({
                    "user_id": user_id,
                    "event_id": event_id,
                    "interaction_type": itype,
                    "interaction_score": score,
                })
                if len(new_interactions) >= BATCH_SIZE:
                    bulk_insert(db, UserInteraction.__table__, new_interactions)
                    total_ints += len(new_interactions)
                    print(f"  Inserted {total_ints} interactions...")
                    new_interactions = []

            if new_interactions:
                bulk_insert(db, UserInteraction.__table__, new_interactions)
                total_ints += len(new_interactions)

        print(f"  Total interactions: {db.query(UserInteraction).count()}")
        print(f"\n{'=' * 60}")
        print("Import complete!")
        print(f"  Users:        {db.query(User).count()}")
        print(f"  Events:       {db.query(Event).count()}")
        print(f"  Interactions: {db.query(UserInteraction).count()}")

        print("\nNext step:")
        print("  python training/train_recommender.py")

    except Exception as e:
        db.rollback()
        print(f"\nERROR: Import failed — {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load Kaggle dataset into NovaTicket")
    parser.add_argument("--data-dir", type=str, default="./kaggle_data", help="Path to Kaggle CSV files")
    parser.add_argument("--sample", type=int, default=None, help="Limit rows per file (for testing)")
    args = parser.parse_args()
    load_kaggle(Path(args.data_dir), sample=args.sample)
