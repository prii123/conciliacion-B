"""
Migration script to add the deepseek_processing_results table to the database.

Run:
  python scripts/migrate_add_deepseek_results.py
"""

import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parents[1] / "conciliaciones.db"
if not DB.exists():
    print("Database file not found at:", DB)
    raise SystemExit(1)

conn = sqlite3.connect(str(DB))
cur = conn.cursor()
print('Connected to', DB)

try:
    # Create deepseek_processing_results table
    cur.execute('''
    CREATE TABLE IF NOT EXISTS deepseek_processing_results (
        id INTEGER PRIMARY KEY,
        id_task INTEGER NOT NULL,
        group_number INTEGER NOT NULL,
        total_groups INTEGER NOT NULL,
        pages_range TEXT NOT NULL,
        raw_response TEXT,
        parsed_json TEXT,
        status TEXT DEFAULT 'pending',
        error_message TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (id_task) REFERENCES tasks (id) ON DELETE CASCADE
    );
    ''')

    conn.commit()
    print("✅ DeepSeek processing results table created successfully")

except Exception as e:
    print(f"❌ Error creating deepseek_processing_results table: {e}")
    conn.rollback()

finally:
    conn.close()