#!/usr/bin/env python3
"""
Script para verificar la configuración antes del despliegue
"""

import os
import sys
from pathlib import Path

def check_file_exists(filepath, required=True):
    """Verifica que un archivo exista"""
    exists = Path(filepath).exists()
    status = "✅" if exists else ("❌" if required else "⚠️")
    print(f"{status} {filepath}")
    return exists

def check_env_var(var_name, required=True):
    """Verifica que una variable de entorno esté definida"""
    value = os.getenv(var_name)
    exists = value is not None and value != ""
    status = "✅" if exists else ("❌" if required else "⚠️")
    
    if exists:
        # Ocultar valores sensibles
        if "SECRET" in var_name.upper() or "PASSWORD" in var_name.upper():
            display_value = "***"
        else:
            display_value = value
        print(f"{status} {var_name}={display_value}")
    else:
        print(f"{status} {var_name} no está definida")
    
    return exists

def main():
    print("🔍 Verificando configuración para despliegue...\n")
    
    errors = []
    warnings = []
    
    # 1. Verificar archivos esenciales
    print("📁 Archivos esenciales:")
    if not check_file_exists("Dockerfile"):
        errors.append("Falta Dockerfile")
    if not check_file_exists("docker-compose.prod.yml"):
        errors.append("Falta docker-compose.prod.yml")
    if not check_file_exists("requirements.txt"):
        errors.append("Falta requirements.txt")
    if not check_file_exists("app/main.py"):
        errors.append("Falta app/main.py")
    
    # Archivos opcionales pero recomendados
    check_file_exists(".env", required=False)
    if not check_file_exists(".env"):
        warnings.append("No existe archivo .env (se usarán valores por defecto)")
    
    print()
    
    # 2. Verificar variables de entorno (si existe .env)
    if Path(".env").exists():
        print("🔐 Variables de entorno (.env):")
        
        # Cargar .env manualmente
        with open(".env") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, value = line.split("=", 1)
                        os.environ[key.strip()] = value.strip()
        
        if not check_env_var("API_BASE_URL", required=False):
            warnings.append("API_BASE_URL no definida")
        else:
            # Verificar que no sea localhost en producción
            api_url = os.getenv("API_BASE_URL", "")
            if "localhost" in api_url:
                warnings.append("⚠️  API_BASE_URL usa localhost, ¿es correcto para producción?")
        
        if not check_env_var("JWT_SECRET_KEY"):
            errors.append("JWT_SECRET_KEY no está definida")
        else:
            secret = os.getenv("JWT_SECRET_KEY", "")
            if secret == "tu-clave-secreta-super-segura-cambiar-en-produccion":
                errors.append("⚠️  JWT_SECRET_KEY usa el valor por defecto - CÁMBIALO!")
            elif len(secret) < 32:
                warnings.append("JWT_SECRET_KEY es muy corta (recomendado: 64+ caracteres)")
        
        check_env_var("DATABASE_URL", required=False)
        check_env_var("ENVIRONMENT", required=False)
        check_env_var("ALLOWED_ORIGINS", required=False)
        
        print()
    
    # 3. Verificar estructura de directorios
    print("📂 Directorios:")
    check_file_exists("app/", required=True)
    check_file_exists("app/api/", required=True)
    check_file_exists("app/static/", required=True)
    check_file_exists("app/utils/", required=True)
    check_file_exists("scripts/", required=True)
    
    # Verificar directorios que deben existir en runtime
    if not check_file_exists("generated_reports/", required=False):
        warnings.append("Directorio generated_reports/ no existe (se creará automáticamente)")
    
    print()
    
    # 4. Verificar archivos de configuración JavaScript
    print("🌐 Configuración Frontend:")
    check_file_exists("app/static/js/config.js")
    check_file_exists("app/static/js/auth.js")
    
    print()
    
    # 5. Verificar que Docker esté disponible
    print("🐳 Docker:")
    try:
        import subprocess
        result = subprocess.run(["docker", "--version"], 
                              capture_output=True, 
                              text=True,
                              timeout=5)
        if result.returncode == 0:
            print(f"✅ Docker: {result.stdout.strip()}")
        else:
            warnings.append("Docker no está disponible")
            print("❌ Docker no está disponible")
    except Exception as e:
        warnings.append("No se pudo verificar Docker")
        print(f"⚠️  No se pudo verificar Docker: {e}")
    
    print()
    
    # Resumen
    print("=" * 60)
    print("📊 RESUMEN:")
    print("=" * 60)
    
    if not errors and not warnings:
        print("✅ ¡Todo listo para desplegar!")
        print("\n🚀 Para desplegar, ejecuta:")
        print("   docker-compose -f docker-compose.prod.yml up -d --build")
        print("\n📝 No olvides crear el usuario administrador:")
        print("   docker exec -it conciliaciones-fastapi python scripts/crear_usuario_prueba.py")
        return 0
    
    if errors:
        print(f"\n❌ {len(errors)} error(es) crítico(s):")
        for error in errors:
            print(f"   - {error}")
    
    if warnings:
        print(f"\n⚠️  {len(warnings)} advertencia(s):")
        for warning in warnings:
            print(f"   - {warning}")
    
    if errors:
        print("\n❌ Corrige los errores antes de desplegar")
        return 1
    else:
        print("\n⚠️  Puedes desplegar, pero revisa las advertencias")
        return 0

if __name__ == "__main__":
    sys.exit(main())
