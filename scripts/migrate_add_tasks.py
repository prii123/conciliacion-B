"""
Migration script to add the tasks table to the database.

Run:
  python scripts/migrate_add_tasks.py
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
    # Create tasks table
    cur.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY,
        id_conciliacion INTEGER NOT NULL,
        tipo TEXT NOT NULL,
        estado TEXT DEFAULT 'pending',
        descripcion TEXT,
        progreso REAL DEFAULT 0.0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (id_conciliacion) REFERENCES conciliaciones (id) ON DELETE CASCADE
    );
    ''')

    conn.commit()
    print("✅ Tasks table created successfully")

except Exception as e:
    print(f"❌ Error creating tasks table: {e}")
    conn.rollback()

finally:
    conn.close()