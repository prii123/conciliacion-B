# Sistema de Conciliación Bancaria

Sistema web desarrollado con FastAPI para gestionar conciliaciones bancarias de múltiples empresas con autenticación JWT.

## 🚀 Características

- ✅ Gestión de múltiples empresas y conciliaciones
- ✅ Carga de archivos Excel (banco y auxiliar)
- ✅ Conciliación automática y manual de movimientos
- ✅ Generación de informes PDF
- ✅ Autenticación JWT con cookies
- ✅ Interfaz web responsiva con Bootstrap 5
- ✅ Dockerizado para fácil despliegue

## 📋 Requisitos

- Python 3.11+
- Docker y Docker Compose (para despliegue)

## 🔧 Instalación Local

### 1. Clonar el repositorio:
```bash
git clone https://github.com/tu-usuario/conciliacion-B.git
cd conciliacion-B
```

### 2. Crear entorno virtual:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

### 4. Ejecutar la aplicación:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Crear usuario administrador:
```bash
python scripts/crear_usuario_prueba.py
```

### 6. Acceder a la aplicación:
- Web: http://localhost:8000
- Login: http://localhost:8000/login
- Docs API: http://localhost:8000/docs

**Credenciales por defecto:** admin / admin123

## 🐳 Despliegue con Docker

### Desarrollo:
```bash
docker-compose up -d
```

### Producción (Digital Ocean, VPS, etc.):
```bash
# 1. Copiar archivo de configuración
cp .env.example .env

# 2. Editar variables de entorno
nano .env
# Cambiar API_BASE_URL por tu dominio o IP

# 3. Construir y ejecutar
docker-compose -f docker-compose.prod.yml up -d --build

# 4. Crear usuario administrador
docker exec -it conciliaciones-fastapi python scripts/crear_usuario_prueba.py
```

**Script automatizado:**
```bash
bash deploy.sh
```

## 🌐 Despliegue en Digital Ocean

Ver guía completa en [DEPLOY.md](DEPLOY.md)

**Resumen rápido:**

1. Crear droplet en Digital Ocean
2. Instalar Docker
3. Clonar repositorio
4. Configurar .env con tu IP/dominio
5. Ejecutar `bash deploy.sh`

## 📁 Estructura del Proyecto

```
conciliacion-B/
├── app/
│   ├── api/              # Endpoints de la API
│   │   ├── routes_auth.py
│   │   ├── routes_conciliacion.py
│   │   ├── routes_empresas.py
│   │   └── routes_informes.py
│   ├── static/           # Frontend (CSS, JS)
│   │   ├── css/
│   │   └── js/
│   ├── utils/            # Utilidades
│   │   ├── auth.py       # JWT y autenticación
│   │   ├── conciliaciones.py
│   │   └── pdf_generator.py
│   ├── web/              # Rutas web (templates)
│   ├── database.py       # Configuración DB
│   ├── models.py         # Modelos SQLAlchemy
│   └── main.py           # Aplicación principal
├── scripts/              # Scripts de utilidad
├── Dockerfile
├── docker-compose.yml    # Para desarrollo
├── docker-compose.prod.yml  # Para producción
├── .env.example          # Variables de entorno ejemplo
└── requirements.txt
```

## 🔐 Seguridad

- Autenticación JWT con cookies HTTP-only
- Tokens con expiración de 30 minutos
- Contraseñas hasheadas con bcrypt
- CORS configurado para producción
- Variables de entorno para secretos

## 🛠️ Configuración

### Variables de Entorno (.env)

```bash
# URL de la API
API_BASE_URL=http://tu-dominio.com

# CORS
ALLOWED_ORIGINS=http://tu-dominio.com,https://tu-dominio.com

# JWT
JWT_SECRET_KEY=tu-clave-secreta  # Generar con: openssl rand -hex 32
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Base de datos
DATABASE_URL=sqlite:///./conciliaciones.db
```

## 📚 Documentación API

Una vez ejecutada la aplicación, accede a:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🧪 Testing

```bash
pytest tests/
```

## 📝 Uso

1. **Crear Empresa:** Registrar empresas a conciliar
2. **Nueva Conciliación:** Subir archivos Excel de banco y auxiliar
3. **Procesar:** Sistema concilia automáticamente movimientos similares
4. **Conciliar Manual:** Seleccionar y emparejar movimientos manualmente
5. **Generar Informe:** Descargar PDF con resultados

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto es privado y confidencial.

## 👥 Autor

Tu Nombre - [@tu-usuario](https://github.com/tu-usuario)

## 📞 Soporte

Para problemas o preguntas, abrir un issue en GitHub.

---

**Nota:** En producción, asegúrate de:
- Cambiar `JWT_SECRET_KEY` por una clave segura
- Usar HTTPS (configurar SSL con Let's Encrypt)
- Configurar backups automáticos de la base de datos
- Monitorear logs regularmente