"""
Script para crear usuarios de prueba con diferentes roles
"""
import sys
import os

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Ajustar path para imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal
from app.repositories.factory import RepositoryFactory
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

print("Creando usuarios de prueba...")
print("=" * 60)

db = SessionLocal()
factory = RepositoryFactory(db)
user_repo = factory.get_user_repository()

try:
    # Verificar si ya existen usuarios
    existing_admin = user_repo.get_by_username("admin")
    existing_user = user_repo.get_by_username("usuario1")
    
    # Crear administrador si no existe
    if not existing_admin:
        admin_data = {
            "username": "admin",
            "email": "admin@example.com",
            "hashed_password": pwd_context.hash("admin123"),
            "role": "administrador"
        }
        admin = user_repo.create(admin_data)
        print(f"\nAdministrador creado:")
        print(f"   Username: admin")
        print(f"   Email: admin@example.com")
        print(f"   Password: admin123")
        print(f"   Role: {admin.role}")
    else:
        print(f"\nAdministrador 'admin' ya existe (ID: {existing_admin.id})")
    
    # Crear usuario regular si no existe
    if not existing_user:
        user_data = {
            "username": "usuario1",
            "email": "usuario1@example.com",
            "hashed_password": pwd_context.hash("usuario123"),
            "role": "usuario"
        }
        user = user_repo.create(user_data)
        print(f"\nUsuario regular creado:")
        print(f"   Username: usuario1")
        print(f"   Email: usuario1@example.com")
        print(f"   Password: usuario123")
        print(f"   Role: {user.role}")
    else:
        print(f"\nUsuario 'usuario1' ya existe (ID: {existing_user.id})")
    
    # Mostrar estadísticas
    print("\n" + "=" * 60)
    print("Usuarios creados exitosamente!")
    print("\nPuedes iniciar sesion en: http://localhost:8000")
    print("\nCredenciales de prueba:")
    print("   Administrador -> admin / admin123")
    print("   Usuario       -> usuario1 / usuario123")
    print("\nDiferencias de roles:")
    print("   - El administrador puede ver TODAS las conciliaciones")
    print("   - El usuario solo puede ver sus propias conciliaciones")
    print("=" * 60)
    
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
