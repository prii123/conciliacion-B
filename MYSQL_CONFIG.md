# ============================================
# Configuración para MySQL
# ============================================

# Pasos para migrar a MySQL:
# 1. Instalar dependencias
#    pip install pymysql cryptography
#
# 2. Crear base de datos en MySQL
#    CREATE DATABASE conciliaciones CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
#
# 3. Actualizar la variable DATABASE_URL en .env o directamente en app/database.py
#
# 4. (Opcional) Ejecutar script de migración de datos
#    python scripts/migrate_to_mysql.py

# ============================================
# Formato de URL para MySQL
# ============================================

# Básico
DATABASE_URL=mysql+pymysql://usuario:contraseña@localhost:3306/conciliaciones

# Con opciones adicionales
DATABASE_URL=mysql+pymysql://usuario:contraseña@localhost:3306/conciliaciones?charset=utf8mb4

# Con SSL
DATABASE_URL=mysql+pymysql://usuario:contraseña@localhost:3306/conciliaciones?ssl_ca=/path/to/ca.pem&ssl_cert=/path/to/cert.pem&ssl_key=/path/to/key.pem

# ============================================
# Ejemplos de configuración
# ============================================

# MySQL local
DATABASE_URL=mysql+pymysql://root:mi_password@localhost:3306/conciliaciones

# MySQL en Docker
DATABASE_URL=mysql+pymysql://conciliacion_user:secure_pass@mysql_container:3306/conciliaciones

# MySQL en servidor remoto
DATABASE_URL=mysql+pymysql://user:pass@192.168.1.100:3306/conciliaciones

# MySQL en AWS RDS
DATABASE_URL=mysql+pymysql://admin:password@mydb.123456.us-east-1.rds.amazonaws.com:3306/conciliaciones

# ============================================
# Configuración avanzada en app/database.py
# ============================================

# Si necesitas configuración más avanzada, edita app/database.py:

# engine = create_engine(
#     DATABASE_URL,
#     pool_size=5,              # Número de conexiones en el pool
#     max_overflow=10,          # Conexiones adicionales permitidas
#     pool_recycle=3600,        # Reciclar conexiones después de 1 hora
#     pool_pre_ping=True,       # Verificar conexión antes de usar
#     echo=False,               # No mostrar SQL queries (True para debug)
#     connect_args={
#         "charset": "utf8mb4",
#         "connect_timeout": 30
#     }
# )

# ============================================
# Comandos útiles de MySQL
# ============================================

# Crear usuario y base de datos:
# CREATE DATABASE conciliaciones CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
# CREATE USER 'conciliacion_user'@'localhost' IDENTIFIED BY 'secure_password';
# GRANT ALL PRIVILEGES ON conciliaciones.* TO 'conciliacion_user'@'localhost';
# FLUSH PRIVILEGES;

# Verificar tablas:
# USE conciliaciones;
# SHOW TABLES;
# DESCRIBE users;

# Backup:
# mysqldump -u usuario -p conciliaciones > backup.sql

# Restaurar:
# mysql -u usuario -p conciliaciones < backup.sql
