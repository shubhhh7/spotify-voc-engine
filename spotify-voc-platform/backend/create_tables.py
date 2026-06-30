"""
Utility script to create all tables directly.
Use this if Alembic is not yet configured or DB is fresh.

Usage: python create_tables.py
"""
from sqlalchemy import text, inspect

from database import engine, Base
from models import Review, ScrapeRun, Insight, Report, Setting  # noqa: F401


def _add_missing_columns():
    """Add columns that may be missing in an existing database."""
    inspector = inspect(engine)
    if "reviews" in inspector.get_table_names():
        columns = [col["name"] for col in inspector.get_columns("reviews")]
        if "last_analyzed_at" not in columns:
            with engine.begin() as conn:
                conn.execute(text(
                    "ALTER TABLE reviews ADD COLUMN last_analyzed_at TIMESTAMP NULL"
                ))
                conn.execute(text(
                    "CREATE INDEX IF NOT EXISTS idx_reviews_last_analyzed_at ON reviews (last_analyzed_at)"
                ))
            print("  ↳ Added last_analyzed_at column to reviews table")


def main():
    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ All tables created successfully.")

    print("\nChecking for missing columns...")
    _add_missing_columns()

    print("\nTables:")
    for table in Base.metadata.sorted_tables:
        print(f"  - {table.name}")


if __name__ == "__main__":
    main()
