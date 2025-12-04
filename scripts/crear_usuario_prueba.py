"""
Script para crear usuario de prueba
"""
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import datetime
from app.database import SessionLocal, engine, Base
from app.models import User
from app.utils.auth import get_password_hash

def crear_usuario_prueba():
    """
    Crea un usuario de prueba con credenciales predefinidas
    """
    # Crear todas las tablas
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Verificar si el usuario ya existe
        usuario_existente = db.query(User).filter(User.username == "admin").first()
        
        if usuario_existente:
            print("❌ El usuario 'admin' ya existe en la base de datos")
            return
        
        # Crear nuevo usuario de prueba
        usuario_prueba = User(
            username="admin",
            email="admin@conciliaciones.com",
            hashed_password=get_password_hash("admin123"),
            is_active=True,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        db.add(usuario_prueba)
        db.commit()
        db.refresh(usuario_prueba)
        
        print("✓ Usuario de prueba creado exitosamente:")
        print(f"  Username: admin")
        print(f"  Password: admin123")
        print(f"  Email: admin@conciliaciones.com")
        print(f"\nPuedes usar estas credenciales para hacer login en /api/auth/login")
        
    except Exception as e:
        print(f"❌ Error al crear usuario: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    crear_usuario_prueba()
