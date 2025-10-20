"""
Simple SQLite migration script to adapt an older database schema to the current models.

WARNING: Always backup your DB before running this script.

What it does:
- Creates temporary tables with the expected (current) schema.
- Copies data from old tables mapping renamed columns.
- Drops old tables and renames new ones.

Run:
  python scripts/migrate_db.py

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
    cur.execute('PRAGMA foreign_keys=OFF;')
    conn.commit()

    # Create new conciliaciones table
    cur.execute('''
    CREATE TABLE IF NOT EXISTS conciliaciones_new (
        id INTEGER PRIMARY KEY,
        id_empresa INTEGER NOT NULL,
        mes_conciliado TEXT,
        anio_conciliado INTEGER,
        cuenta_conciliada TEXT,
        fecha_proceso TEXT,
        estado TEXT
    );
    ''')

    # Migrate conciliaciones
    cur.execute('''
    INSERT INTO conciliaciones_new (id, id_empresa, mes_conciliado, anio_conciliado, cuenta_conciliada, fecha_proceso, estado)
    SELECT id, id_empresa, mes_conciliado,
           COALESCE(CAST(año_conciliado AS INTEGER), anio_conciliado),
           cuenta_conciliada, fecha_proceso, estado
    FROM conciliaciones;
    ''')

    # Create new movimientos table
    cur.execute('''
    CREATE TABLE IF NOT EXISTS movimientos_new (
        id INTEGER PRIMARY KEY,
        conciliacion_id INTEGER NOT NULL,
        fecha TEXT,
        descripcion TEXT,
        valor REAL,
        es TEXT,
        origen TEXT,
        conciliado TEXT
    );
    ''')

    # Migrate movimientos (map id_conciliacion->conciliacion_id, tipo->origen, estado_conciliacion->conciliado)
    cur.execute('''
    INSERT INTO movimientos_new (id, conciliacion_id, fecha, descripcion, valor, es, origen, conciliado)
    SELECT id, id_conciliacion, fecha, descripcion, valor, es, tipo, estado_conciliacion
    FROM movimientos;
    ''')

    # Create new empresas table (keep basic columns)
    cur.execute('''
    CREATE TABLE IF NOT EXISTS empresas_new (
        id INTEGER PRIMARY KEY,
        nit TEXT UNIQUE,
        razon_social TEXT,
        nombre_comercial TEXT,
        ciudad TEXT,
        estado TEXT
    );
    ''')

    # Migrate empresas (map available columns)
    cur.execute('''
    INSERT INTO empresas_new (id, nit, razon_social, nombre_comercial, ciudad, estado)
    SELECT id, nit, razon_social, nombre_comercial, ciudad, estado
    FROM empresas;
    ''')

    # Create new conciliacion_matches table
    cur.execute('''
    CREATE TABLE IF NOT EXISTS conciliacion_matches_new (
        id INTEGER PRIMARY KEY,
        conciliacion_id INTEGER NOT NULL,
        movimiento_banco_id INTEGER,
        movimiento_auxiliar_id INTEGER,
        diferencia REAL DEFAULT 0.0
    );
    ''')

    # Migrate conciliacion_matches
    cur.execute('''
    INSERT INTO conciliacion_matches_new (id, conciliacion_id, movimiento_banco_id, movimiento_auxiliar_id, diferencia)
    SELECT id, id_conciliacion, id_movimiento_banco, id_movimiento_auxiliar, diferencia_valor
    FROM conciliacion_matches;
    ''')

    conn.commit()

    # Drop old tables and rename new ones
    for old, new in [
        ('conciliaciones', 'conciliaciones_new'),
        ('movimientos', 'movimientos_new'),
        ('empresas', 'empresas_new'),
        ('conciliacion_matches', 'conciliacion_matches_new'),
    ]:
        print('Replacing', old, 'with', new)
        cur.execute(f'DROP TABLE IF EXISTS {old};')
        cur.execute(f'ALTER TABLE {new} RENAME TO {old};')

    conn.commit()
    print('Migration complete. Review your data and restart the app.')

finally:
    cur.execute('PRAGMA foreign_keys=ON;')
    conn.close()
