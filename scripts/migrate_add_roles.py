"""
Script para migrar la base de datos y agregar las nuevas columnas:
- role en la tabla users
- id_usuario_creador en la tabla conciliaciones
"""
from sqlalchemy import create_engine, text
import os
import sys

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Ajustar path para imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import Base, engine
from app.models import User, Empresa, Conciliacion

print("Iniciando migracion de base de datos...")
print("=" * 60)

# Crear todas las tablas si no existen
print("\nCreando tablas base si no existen...")
Base.metadata.create_all(bind=engine)
print("OK - Tablas base creadas/verificadas")

try:
    with engine.connect() as conn:
        # Verificar si la columna 'role' existe en users
        print("\nPaso 1: Verificando columna 'role' en tabla users...")
        try:
            result = conn.execute(text("SELECT role FROM users LIMIT 1"))
            print("   OK - La columna 'role' ya existe")
        except Exception:
            print("   Agregando columna 'role' a tabla users...")
            conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR DEFAULT 'usuario'"))
            conn.commit()
            print("   OK - Columna 'role' agregada exitosamente")
        
        # Verificar si la columna 'id_usuario_creador' existe en conciliaciones
        print("\nPaso 2: Verificando columna 'id_usuario_creador' en tabla conciliaciones...")
        try:
            result = conn.execute(text("SELECT id_usuario_creador FROM conciliaciones LIMIT 1"))
            print("   OK - La columna 'id_usuario_creador' ya existe")
        except Exception:
            print("   Agregando columna 'id_usuario_creador' a tabla conciliaciones...")
            conn.execute(text("ALTER TABLE conciliaciones ADD COLUMN id_usuario_creador INTEGER"))
            conn.commit()
            print("   OK - Columna 'id_usuario_creador' agregada exitosamente")
        
        # Actualizar usuarios existentes sin rol
        print("\nPaso 3: Actualizando usuarios existentes sin rol...")
        result = conn.execute(text("UPDATE users SET role = 'usuario' WHERE role IS NULL"))
        conn.commit()
        print(f"   OK - {result.rowcount} usuarios actualizados")
        
        # Mostrar estadísticas
        print("\nEstadisticas:")
        result = conn.execute(text("SELECT COUNT(*) as total FROM users"))
        total_users = result.fetchone()[0]
        print(f"   - Total de usuarios: {total_users}")
        
        result = conn.execute(text("SELECT COUNT(*) as total FROM users WHERE role = 'administrador'"))
        admin_count = result.fetchone()[0]
        print(f"   - Administradores: {admin_count}")
        
        result = conn.execute(text("SELECT COUNT(*) as total FROM users WHERE role = 'usuario'"))
        user_count = result.fetchone()[0]
        print(f"   - Usuarios: {user_count}")
        
        result = conn.execute(text("SELECT COUNT(*) as total FROM conciliaciones"))
        total_conc = result.fetchone()[0]
        print(f"   - Total de conciliaciones: {total_conc}")
        
        result = conn.execute(text("SELECT COUNT(*) as total FROM conciliaciones WHERE id_usuario_creador IS NOT NULL"))
        conc_con_creador = result.fetchone()[0]
        print(f"   - Conciliaciones con creador asignado: {conc_con_creador}")
        
except Exception as e:
    print(f"\nError durante la migracion: {e}")
    exit(1)

print("\n" + "=" * 60)
print("Migracion completada exitosamente")
print("\nNotas importantes:")
print("   1. Todas las conciliaciones existentes no tienen usuario creador asignado")
print("   2. Solo los administradores podran verlas todas")
print("   3. Las nuevas conciliaciones se asignaran al usuario que las cree")
print("   4. Puedes crear un administrador con el endpoint /api/auth/register")
print("      especificando role='administrador'")
print("\nPara crear un usuario administrador:")
print("   POST /api/auth/register")
print('   Body: {"username": "admin", "email": "admin@example.com", ')
print('          "password": "tu_password", "role": "administrador"}')
print("=" * 60)
