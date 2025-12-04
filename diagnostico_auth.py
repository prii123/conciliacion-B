#!/usr/bin/env python3
"""
Script de diagnóstico para verificar que bcrypt y passlib funcionan correctamente
"""

import sys

def check_imports():
    """Verifica que los módulos necesarios se importen correctamente"""
    print("🔍 Verificando imports...")
    
    try:
        import bcrypt
        print(f"✅ bcrypt importado correctamente - versión: {bcrypt.__version__}")
    except ImportError as e:
        print(f"❌ Error al importar bcrypt: {e}")
        return False
    
    try:
        from passlib.context import CryptContext
        print("✅ passlib.context.CryptContext importado correctamente")
    except ImportError as e:
        print(f"❌ Error al importar passlib: {e}")
        return False
    
    return True

def test_password_hashing():
    """Prueba el hash de contraseñas"""
    print("\n🔒 Probando hash de contraseñas...")
    
    try:
        from passlib.context import CryptContext
        
        # Configuración igual a la de auth.py
        pwd_context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto"
        )
        
        # Contraseña de prueba
        test_password = "test123"
        
        # Generar hash
        print(f"   Hasheando contraseña: '{test_password}'")
        hashed = pwd_context.hash(test_password)
        print(f"✅ Hash generado exitosamente")
        print(f"   Hash: {hashed[:50]}...")
        
        # Verificar contraseña correcta
        if pwd_context.verify(test_password, hashed):
            print("✅ Verificación de contraseña correcta: OK")
        else:
            print("❌ Error: la contraseña correcta no se verificó")
            return False
        
        # Verificar contraseña incorrecta
        if not pwd_context.verify("wrong_password", hashed):
            print("✅ Rechazo de contraseña incorrecta: OK")
        else:
            print("❌ Error: contraseña incorrecta fue aceptada")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error al probar hash: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_auth_module():
    """Prueba el módulo de autenticación completo"""
    print("\n🔐 Probando módulo de autenticación...")
    
    try:
        from app.utils.auth import get_password_hash, verify_password
        
        test_password = "admin123"
        
        # Generar hash
        hashed = get_password_hash(test_password)
        print(f"✅ get_password_hash() funciona correctamente")
        
        # Verificar
        if verify_password(test_password, hashed):
            print(f"✅ verify_password() funciona correctamente")
        else:
            print(f"❌ verify_password() falló")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error al probar módulo auth: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_versions():
    """Muestra las versiones de los paquetes clave"""
    print("\n📦 Versiones de paquetes:")
    
    packages = [
        'bcrypt',
        'passlib',
        'fastapi',
        'uvicorn',
        'jose',
        'sqlalchemy'
    ]
    
    for package in packages:
        try:
            mod = __import__(package)
            version = getattr(mod, '__version__', 'desconocida')
            print(f"   {package}: {version}")
        except ImportError:
            print(f"   {package}: ❌ no instalado")

def main():
    print("=" * 60)
    print("🔧 DIAGNÓSTICO DE CONFIGURACIÓN DE AUTENTICACIÓN")
    print("=" * 60)
    print()
    
    # 1. Verificar imports
    if not check_imports():
        print("\n❌ Falló la verificación de imports")
        return 1
    
    # 2. Verificar versiones
    check_versions()
    
    # 3. Probar hash de contraseñas
    if not test_password_hashing():
        print("\n❌ Falló la prueba de hash de contraseñas")
        return 1
    
    # 4. Probar módulo de autenticación
    if not test_auth_module():
        print("\n❌ Falló la prueba del módulo de autenticación")
        return 1
    
    # Resumen
    print("\n" + "=" * 60)
    print("✅ TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
    print("=" * 60)
    print()
    print("🎉 El sistema de autenticación está funcionando correctamente")
    print("   Puedes iniciar la aplicación con confianza.")
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
