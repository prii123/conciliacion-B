"""
Migration script to add pdf_minio_url column to conciliaciones table.

Run:
  python scripts/migrate_add_minio_pdf.py
"""

import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("DATABASE_URL not found in environment variables")
    raise SystemExit(1)

engine = create_engine(DATABASE_URL)

def migrate():
    with engine.connect() as conn:
        # Check if column exists
        result = conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'conciliaciones' AND column_name = 'pdf_minio_url'
        """))
        if result.fetchone():
            print("Column pdf_minio_url already exists")
            return

        # Add the column
        conn.execute(text("""
            ALTER TABLE conciliaciones ADD COLUMN pdf_minio_url TEXT
        """))
        conn.commit()
        print("Added pdf_minio_url column to conciliaciones table")

if __name__ == "__main__":
    migrate()