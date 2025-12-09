"""
Script de ejemplo para migrar de SQLite a MySQL.
Ejecutar después de configurar la conexión a MySQL.
"""
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models import Base, User, Empresa, Conciliacion, Movimiento
from app.database import SessionLocal as SQLiteSession

# ============================================
# CONFIGURACIÓN
# ============================================

# URL de la base de datos MySQL
MYSQL_URL = os.getenv(
    "MYSQL_URL",
    "mysql+pymysql://usuario:contraseña@localhost:3306/conciliaciones"
)

print("=" * 60)
print("🔄 SCRIPT DE MIGRACIÓN SQLite -> MySQL")
print("=" * 60)
print()

# ============================================
# PASO 1: Crear el engine de MySQL
# ============================================
print("📦 Paso 1: Conectando a MySQL...")
try:
    mysql_engine = create_engine(
        MYSQL_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=True  # Ver las queries SQL
    )
    
    # Probar conexión
    with mysql_engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("✅ Conexión a MySQL exitosa")
        print()
except Exception as e:
    print(f"❌ Error conectando a MySQL: {e}")
    print("Verifica que:")
    print("  1. MySQL esté corriendo")
    print("  2. La base de datos 'conciliaciones' exista")
    print("  3. Las credenciales sean correctas")
    print("  4. pymysql esté instalado: pip install pymysql")
    exit(1)

# ============================================
# PASO 2: Crear las tablas en MySQL
# ============================================
print("🏗️  Paso 2: Creando tablas en MySQL...")
try:
    Base.metadata.create_all(bind=mysql_engine)
    print("✅ Tablas creadas exitosamente")
    print()
except Exception as e:
    print(f"❌ Error creando tablas: {e}")
    exit(1)

# ============================================
# PASO 3: Migrar datos (OPCIONAL)
# ============================================
print("📋 Paso 3: ¿Deseas migrar los datos de SQLite?")
print("   Esto copiará todos los registros de SQLite a MySQL")
respuesta = input("   (s/n): ").lower().strip()

if respuesta == 's':
    print()
    print("🔄 Migrando datos...")
    
    try:
        # Crear sesiones
        sqlite_session = SQLiteSession()
        MySQLSession = sessionmaker(bind=mysql_engine)
        mysql_session = MySQLSession()
        
        # Migrar usuarios
        print("   👤 Migrando usuarios...")
        usuarios = sqlite_session.query(User).all()
        for usuario in usuarios:
            nuevo_usuario = User(
                id=usuario.id,
                username=usuario.username,
                email=usuario.email,
                hashed_password=usuario.hashed_password,
                is_active=usuario.is_active,
                created_at=usuario.created_at
            )
            mysql_session.merge(nuevo_usuario)
        mysql_session.commit()
        print(f"      ✅ {len(usuarios)} usuarios migrados")
        
        # Migrar empresas
        print("   🏢 Migrando empresas...")
        empresas = sqlite_session.query(Empresa).all()
        for empresa in empresas:
            nueva_empresa = Empresa(
                id=empresa.id,
                nit=empresa.nit,
                razon_social=empresa.razon_social,
                nombre_comercial=empresa.nombre_comercial,
                email=empresa.email,
                telefono=empresa.telefono,
                direccion=empresa.direccion,
                ciudad=empresa.ciudad,
                estado=empresa.estado,
                fecha_creacion=empresa.fecha_creacion
            )
            mysql_session.merge(nueva_empresa)
        mysql_session.commit()
        print(f"      ✅ {len(empresas)} empresas migradas")
        
        # Migrar conciliaciones
        print("   📊 Migrando conciliaciones...")
        conciliaciones = sqlite_session.query(Conciliacion).all()
        for conc in conciliaciones:
            nueva_conc = Conciliacion(
                id=conc.id,
                id_empresa=conc.id_empresa,
                fecha_proceso=conc.fecha_proceso,
                nombre_archivo_banco=conc.nombre_archivo_banco,
                nombre_archivo_auxiliar=conc.nombre_archivo_auxiliar,
                estado=conc.estado,
                mes_conciliado=conc.mes_conciliado,
                cuenta_conciliada=conc.cuenta_conciliada,
                año_conciliado=getattr(conc, 'año_conciliado', None)
            )
            mysql_session.merge(nueva_conc)
        mysql_session.commit()
        print(f"      ✅ {len(conciliaciones)} conciliaciones migradas")
        
        # Migrar movimientos
        print("   💰 Migrando movimientos...")
        movimientos = sqlite_session.query(Movimiento).all()
        batch_size = 1000
        for i in range(0, len(movimientos), batch_size):
            batch = movimientos[i:i+batch_size]
            for mov in batch:
                nuevo_mov = Movimiento(
                    id=mov.id,
                    id_conciliacion=mov.id_conciliacion,
                    fecha=mov.fecha,
                    descripcion=mov.descripcion,
                    valor=mov.valor,
                    tipo=mov.tipo,
                    es=mov.es,
                    estado_conciliacion=mov.estado_conciliacion
                )
                mysql_session.merge(nuevo_mov)
            mysql_session.commit()
            print(f"      ... {min(i+batch_size, len(movimientos))}/{len(movimientos)} movimientos")
        print(f"      ✅ {len(movimientos)} movimientos migrados")
        
        print()
        print("✅ ¡Migración completada exitosamente!")
        
        # Cerrar sesiones
        sqlite_session.close()
        mysql_session.close()
        
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        mysql_session.rollback()
        exit(1)
else:
    print("   ⏭️  Migración de datos omitida")

# ============================================
# PASO 4: Verificar migración
# ============================================
print()
print("🔍 Paso 4: Verificando migración...")

MySQLSession = sessionmaker(bind=mysql_engine)
mysql_session = MySQLSession()

try:
    # Contar registros
    num_usuarios = mysql_session.query(User).count()
    num_empresas = mysql_session.query(Empresa).count()
    num_conciliaciones = mysql_session.query(Conciliacion).count()
    num_movimientos = mysql_session.query(Movimiento).count()
    
    print(f"   📊 Estadísticas de MySQL:")
    print(f"      - Usuarios: {num_usuarios}")
    print(f"      - Empresas: {num_empresas}")
    print(f"      - Conciliaciones: {num_conciliaciones}")
    print(f"      - Movimientos: {num_movimientos}")
    print()
    
except Exception as e:
    print(f"❌ Error verificando: {e}")

mysql_session.close()

# ============================================
# PASO 5: Instrucciones finales
# ============================================
print("=" * 60)
print("✅ MIGRACIÓN COMPLETADA")
print("=" * 60)
print()
print("📝 Próximos pasos:")
print()
print("1. Actualizar app/database.py:")
print(f'   DATABASE_URL = "{MYSQL_URL}"')
print()
print("2. O usar variable de entorno:")
print(f'   export DATABASE_URL="{MYSQL_URL}"')
print()
print("3. Reiniciar la aplicación:")
print("   python -m uvicorn app.main:app --reload")
print()
print("4. (OPCIONAL) Hacer backup de SQLite:")
print("   cp conciliaciones.db conciliaciones.db.backup")
print()
print("=" * 60)
