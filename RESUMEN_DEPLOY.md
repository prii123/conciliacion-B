# 🚀 Configuración para Despliegue en Digital Ocean - Resumen

## ✅ Cambios Realizados

### 1. **Configuración Dinámica de URLs**

**Problema:** URLs hardcodeadas a `localhost` causarían errores en producción.

**Solución:**
- ✅ `app/static/js/config.js`: Ahora detecta automáticamente el origen
  ```javascript
  // Usa localhost:8000 en desarrollo
  // Usa window.location.origin en producción (tu dominio/IP)
  ```

- ✅ `app/utils/utils.py`: Lee URL desde variable de entorno
  ```python
  BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
  ```

### 2. **CORS Configurado**

**Problema:** Bloqueos de CORS entre frontend y API.

**Solución:**
- ✅ `app/main.py`: Middleware CORS configurado
  ```python
  # Lee orígenes permitidos de variable de entorno
  ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "...").split(",")
  ```

### 3. **Docker Optimizado para Producción**

**Cambios:**
- ✅ `Dockerfile`: Quitado `--reload` para mejor rendimiento
- ✅ `docker-compose.prod.yml`: Configuración de producción
  - Sin hot-reload
  - `restart: always` para auto-reinicio
  - Variables de entorno configurables

### 4. **Archivos de Configuración Creados**

- ✅ `.env.example`: Plantilla de variables de entorno
- ✅ `docker-compose.prod.yml`: Para despliegue en servidor
- ✅ `DEPLOY.md`: Guía completa paso a paso
- ✅ `deploy.sh`: Script automático de despliegue
- ✅ `check_deploy.py`: Verificador de configuración

### 5. **Dockerignore Mejorado**

- ✅ Excluye archivos innecesarios de la imagen Docker
- ✅ Reduce tamaño de imagen
- ✅ Excluye .env, base de datos, archivos temporales

---

## 📋 Pasos para Desplegar en Digital Ocean

### Opción A: Script Automático (Recomendado) 🎯

```bash
# 1. Conectar a tu droplet
ssh root@TU_IP_DIGITAL_OCEAN

# 2. Instalar Docker
curl -fsSL https://get.docker.com | sh
apt install docker-compose -y

# 3. Clonar repositorio
cd /opt
git clone https://github.com/prii123/conciliacion-B.git
cd conciliacion-B

# 4. Configurar variables de entorno
cp .env.example .env
nano .env  # Editar las siguientes líneas:

# Cambiar:
API_BASE_URL=http://TU_IP:8000
ALLOWED_ORIGINS=http://TU_IP:8000,http://TU_IP
JWT_SECRET_KEY=$(openssl rand -hex 32)  # Generar clave segura

# 5. Verificar configuración
python3 check_deploy.py

# 6. Desplegar
bash deploy.sh

# 7. Crear usuario administrador
docker exec -it conciliaciones-fastapi python scripts/crear_usuario_prueba.py
```

### Opción B: Manual 📝

```bash
# Después de configurar .env:
docker-compose -f docker-compose.prod.yml up -d --build

# Ver logs
docker logs -f conciliaciones-fastapi

# Crear usuario
docker exec -it conciliaciones-fastapi python scripts/crear_usuario_prueba.py
```

---

## 🔧 Configuración de Variables de Entorno

Archivo `.env` debe contener:

```bash
# Tu IP de Digital Ocean o dominio
API_BASE_URL=http://165.227.XXX.XXX:8000

# Orígenes permitidos
ALLOWED_ORIGINS=http://165.227.XXX.XXX:8000,http://165.227.XXX.XXX

# Clave secreta JWT (generar con: openssl rand -hex 32)
JWT_SECRET_KEY=abc123def456...tu-clave-generada

# Tiempo de expiración del token (minutos)
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Base de datos
DATABASE_URL=sqlite:///./conciliaciones.db

# Entorno
ENVIRONMENT=production
```

---

## 🌐 URLs Después del Despliegue

- **Aplicación Web:** `http://TU_IP:8000`
- **Login:** `http://TU_IP:8000/login`
- **API Docs:** `http://TU_IP:8000/docs`

**Credenciales por defecto:** `admin` / `admin123`

---

## 🔒 Seguridad Adicional (Opcional pero Recomendado)

### 1. Configurar Nginx como Reverse Proxy

```bash
apt install nginx -y

# Crear configuración
cat > /etc/nginx/sites-available/conciliaciones << 'EOF'
server {
    listen 80;
    server_name TU_DOMINIO.com;
    client_max_body_size 100M;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Activar
ln -s /etc/nginx/sites-available/conciliaciones /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

### 2. Instalar SSL (HTTPS) con Let's Encrypt

```bash
apt install certbot python3-certbot-nginx -y
certbot --nginx -d TU_DOMINIO.com
```

### 3. Configurar Firewall

```bash
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 8000/tcp  # App (si no usas Nginx)
ufw enable
```

---

## 📊 Comandos Útiles

```bash
# Ver contenedores corriendo
docker ps

# Ver logs en tiempo real
docker logs -f conciliaciones-fastapi

# Reiniciar aplicación
docker-compose -f docker-compose.prod.yml restart

# Detener aplicación
docker-compose -f docker-compose.prod.yml down

# Actualizar aplicación
git pull
docker-compose -f docker-compose.prod.yml up -d --build

# Entrar al contenedor
docker exec -it conciliaciones-fastapi bash

# Backup de base de datos
cp conciliaciones.db conciliaciones.db.backup-$(date +%Y%m%d)

# Ver uso de recursos
docker stats
```

---

## 🐛 Solución de Problemas

### Error: "No module named uvicorn"
```bash
docker-compose -f docker-compose.prod.yml build --no-cache
```

### Error: "Permission denied" en generated_reports
```bash
chmod 777 generated_reports/
```

### Error 401 en todas las peticiones
- Verificar que el token se guardó en cookies después del login
- Revisar que `auth.js` se cargó correctamente
- Verificar en DevTools > Application > Cookies que existe `access_token`

### La aplicación no responde
```bash
# Ver logs
docker logs conciliaciones-fastapi

# Reiniciar
docker-compose -f docker-compose.prod.yml restart
```

### CORS errors
- Verificar que `ALLOWED_ORIGINS` en `.env` incluye tu dominio/IP
- Verificar que `config.js` detecta correctamente el origen

---

## ✅ Checklist Final

Antes de considerar el despliegue completo:

- [ ] Droplet creado en Digital Ocean
- [ ] Docker y Docker Compose instalados
- [ ] Repositorio clonado en `/opt/conciliacion-B`
- [ ] Archivo `.env` configurado con IP/dominio correcto
- [ ] `JWT_SECRET_KEY` generada y cambiada
- [ ] `check_deploy.py` ejecutado sin errores
- [ ] Aplicación desplegada con `deploy.sh`
- [ ] Usuario administrador creado
- [ ] Login funciona correctamente
- [ ] API responde (probar en /docs)
- [ ] Firewall configurado
- [ ] (Opcional) Nginx configurado
- [ ] (Opcional) SSL instalado
- [ ] Backup automático configurado

---

## 📞 Notas Importantes

1. **Sin CORS con la configuración actual:** Como el frontend se sirve desde el mismo servidor que la API, no hay problemas de CORS. `config.js` usa `window.location.origin` que será tu dominio/IP.

2. **Costos Digital Ocean:** Un droplet básico ($6/mes, 1GB RAM) es suficiente para empezar.

3. **Base de datos:** Se usa SQLite por simplicidad. Para producción con mucho tráfico, considera migrar a PostgreSQL.

4. **Backups:** Configura backups automáticos de `conciliaciones.db`.

5. **Monitoreo:** Revisa logs regularmente con `docker logs`.

---

## 🎉 ¡Listo!

Tu aplicación está lista para ejecutarse en Digital Ocean sin problemas de CORS ni comunicación.

**¿Preguntas?** Revisa `DEPLOY.md` para más detalles.
