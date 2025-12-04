# 🎯 COMANDOS RÁPIDOS

## Para Digital Ocean (Producción)

### Instalación Completa Automática
```bash
ssh root@TU_IP
curl -fsSL https://raw.githubusercontent.com/prii123/conciliacion-B/main/quick_start.sh | bash
```

### O Manual
```bash
# 1. Instalar Docker
curl -fsSL https://get.docker.com | sh
apt install docker-compose -y

# 2. Clonar y configurar
cd /opt
git clone https://github.com/prii123/conciliacion-B.git
cd conciliacion-B
cp .env.example .env
nano .env  # Editar API_BASE_URL con tu IP

# 3. Desplegar
bash deploy.sh

# 4. Crear usuario
docker exec -it conciliaciones-fastapi python scripts/crear_usuario_prueba.py
```

## Para Desarrollo Local (Windows)

### Con Docker
```powershell
# PowerShell
.\test_local.ps1
```

### Sin Docker
```powershell
# PowerShell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python scripts\crear_usuario_prueba.py
py -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Comandos de Gestión

```bash
# Ver logs
docker logs -f conciliaciones-fastapi

# Reiniciar
docker-compose -f docker-compose.prod.yml restart

# Detener
docker-compose -f docker-compose.prod.yml down

# Actualizar código
git pull
docker-compose -f docker-compose.prod.yml up -d --build

# Entrar al contenedor
docker exec -it conciliaciones-fastapi bash

# Backup de DB
cp conciliaciones.db conciliaciones.db.backup-$(date +%Y%m%d)

# Ver estado
docker ps
docker stats
```

## URLs

- **App:** http://TU_IP:8000
- **Login:** http://TU_IP:8000/login
- **API Docs:** http://TU_IP:8000/docs

## Credenciales Default

- **Usuario:** admin
- **Password:** admin123

---

Ver documentación completa en:
- `README.md` - Información general
- `DEPLOY.md` - Guía detallada de despliegue
- `RESUMEN_DEPLOY.md` - Resumen de configuración
