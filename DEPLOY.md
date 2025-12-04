# Guía de Despliegue en Digital Ocean

## 1. Preparación del Servidor

### Conectarse al droplet:
```bash
ssh root@tu-ip-digital-ocean
```

### Actualizar el sistema:
```bash
apt update && apt upgrade -y
```

### Instalar Docker y Docker Compose:
```bash
# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Instalar Docker Compose
apt install docker-compose -y

# Verificar instalación
docker --version
docker-compose --version
```

## 2. Configurar el Proyecto

### Clonar el repositorio:
```bash
cd /opt
git clone https://github.com/tu-usuario/conciliacion-B.git
cd conciliacion-B
```

### Crear archivo .env:
```bash
cp .env.example .env
nano .env
```

### Editar las siguientes variables en .env:
```bash
# Cambiar por tu IP o dominio
API_BASE_URL=http://TU_IP_DIGITAL_OCEAN:8000
# O si tienes un dominio:
# API_BASE_URL=https://conciliaciones.tudominio.com

# Generar clave secreta segura
JWT_SECRET_KEY=$(openssl rand -hex 32)
```

### Crear directorios necesarios:
```bash
mkdir -p generated_reports
chmod 777 generated_reports
```

## 3. Construir y Ejecutar con Docker

### Para desarrollo (con hot-reload):
```bash
docker-compose up -d
```

### Para producción (recomendado en Digital Ocean):
```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

### Ver logs:
```bash
docker-compose logs -f
```

### Detener contenedores:
```bash
docker-compose down
```

## 4. Configurar Firewall (UFW)

```bash
# Permitir SSH
ufw allow 22/tcp

# Permitir puerto de la aplicación
ufw allow 8000/tcp

# Si usas Nginx como reverse proxy
ufw allow 80/tcp
ufw allow 443/tcp

# Habilitar firewall
ufw enable
```

## 5. Crear Usuario Administrador

```bash
# Entrar al contenedor
docker exec -it conciliaciones-fastapi bash

# Ejecutar script de creación de usuario
python scripts/crear_usuario_prueba.py

# Salir del contenedor
exit
```

## 6. Configurar Nginx como Reverse Proxy (Opcional pero Recomendado)

### Instalar Nginx:
```bash
apt install nginx -y
```

### Crear configuración:
```bash
nano /etc/nginx/sites-available/conciliaciones
```

### Agregar contenido:
```nginx
server {
    listen 80;
    server_name tu-dominio.com www.tu-dominio.com;

    client_max_body_size 100M;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Activar configuración:
```bash
ln -s /etc/nginx/sites-available/conciliaciones /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

### Instalar SSL con Let's Encrypt (HTTPS):
```bash
apt install certbot python3-certbot-nginx -y
certbot --nginx -d tu-dominio.com -d www.tu-dominio.com
```

## 7. Configurar Auto-inicio

El docker-compose.prod.yml ya incluye `restart: always`, por lo que los contenedores se reiniciarán automáticamente si el servidor se reinicia.

## 8. Monitoreo

### Ver estado de contenedores:
```bash
docker ps
docker stats
```

### Ver logs en tiempo real:
```bash
docker logs -f conciliaciones-fastapi
```

### Reiniciar aplicación:
```bash
docker-compose restart
```

## 9. Actualizaciones

### Para actualizar la aplicación:
```bash
cd /opt/conciliacion-B
git pull
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build
```

## 10. Backup de Base de Datos

### Crear backup:
```bash
cp conciliaciones.db conciliaciones.db.backup-$(date +%Y%m%d)
```

### Backup automático con cron:
```bash
crontab -e
```

Agregar línea:
```
0 2 * * * cd /opt/conciliacion-B && cp conciliaciones.db conciliaciones.db.backup-$(date +\%Y\%m\%d)
```

## Notas Importantes

1. **CORS**: Con la configuración actual usando rutas relativas en `config.js`, no deberías tener problemas de CORS ya que el frontend y backend están en el mismo origen.

2. **Seguridad**:
   - Cambia la `JWT_SECRET_KEY` en producción
   - Nunca cometas el archivo `.env` al repositorio
   - Usa HTTPS en producción (con Nginx + Let's Encrypt)

3. **Recursos**: Un droplet básico de Digital Ocean ($6/mes con 1GB RAM) es suficiente para comenzar.

4. **Dominio**: Si usas un dominio, apunta un registro A a la IP de tu droplet.

## Solución de Problemas

### Si el contenedor no inicia:
```bash
docker logs conciliaciones-fastapi
```

### Si hay errores de permisos:
```bash
chmod -R 755 /opt/conciliacion-B
chmod 777 generated_reports
```

### Si la base de datos no se crea:
```bash
docker exec -it conciliaciones-fastapi python -c "from app.database import engine, Base; Base.metadata.create_all(bind=engine)"
```
