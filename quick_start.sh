#!/bin/bash

# QUICK START - Digital Ocean Deployment
# Ejecutar este script en tu servidor Digital Ocean

set -e  # Detener si hay errores

echo "🚀 DESPLIEGUE RÁPIDO - Conciliaciones Bancarias"
echo "================================================"
echo ""

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para imprimir mensajes
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# 1. Verificar que estamos como root
if [ "$EUID" -ne 0 ]; then 
    print_error "Este script debe ejecutarse como root"
    echo "Usa: sudo bash quick_start.sh"
    exit 1
fi

print_success "Usuario root verificado"

# 2. Actualizar sistema
echo ""
echo "📦 Actualizando sistema..."
apt update && apt upgrade -y
print_success "Sistema actualizado"

# 3. Instalar Docker si no está instalado
if ! command -v docker &> /dev/null; then
    echo ""
    echo "🐳 Instalando Docker..."
    curl -fsSL https://get.docker.com | sh
    print_success "Docker instalado"
else
    print_success "Docker ya está instalado"
fi

# 4. Instalar Docker Compose si no está instalado
if ! command -v docker-compose &> /dev/null; then
    echo ""
    echo "🐳 Instalando Docker Compose..."
    apt install docker-compose -y
    print_success "Docker Compose instalado"
else
    print_success "Docker Compose ya está instalado"
fi

# 5. Clonar repositorio si no existe
if [ ! -d "/opt/conciliacion-B" ]; then
    echo ""
    echo "📥 Clonando repositorio..."
    cd /opt
    git clone https://github.com/prii123/conciliacion-B.git
    cd conciliacion-B
    print_success "Repositorio clonado"
else
    echo ""
    print_warning "El directorio /opt/conciliacion-B ya existe"
    cd /opt/conciliacion-B
    echo "Actualizando repositorio..."
    git pull
    print_success "Repositorio actualizado"
fi

# 6. Configurar variables de entorno
if [ ! -f ".env" ]; then
    echo ""
    echo "⚙️  Configurando variables de entorno..."
    cp .env.example .env
    
    # Obtener IP pública del servidor
    PUBLIC_IP=$(curl -s ifconfig.me)
    
    if [ ! -z "$PUBLIC_IP" ]; then
        print_success "IP pública detectada: $PUBLIC_IP"
        
        # Actualizar .env con la IP
        sed -i "s|API_BASE_URL=http://localhost:8000|API_BASE_URL=http://$PUBLIC_IP:8000|g" .env
        sed -i "s|ALLOWED_ORIGINS=http://localhost:8000,http://localhost,http://127.0.0.1:8000|ALLOWED_ORIGINS=http://$PUBLIC_IP:8000,http://$PUBLIC_IP|g" .env
        
        # Generar JWT secret
        JWT_SECRET=$(openssl rand -hex 32)
        sed -i "s|JWT_SECRET_KEY=tu-clave-secreta-super-segura-cambiar-en-produccion|JWT_SECRET_KEY=$JWT_SECRET|g" .env
        
        print_success "Variables de entorno configuradas automáticamente"
    else
        print_warning "No se pudo detectar la IP pública"
        print_warning "Edita manualmente el archivo .env"
    fi
else
    print_warning "El archivo .env ya existe, no se sobrescribirá"
fi

# 7. Crear directorios necesarios
echo ""
echo "📁 Creando directorios..."
mkdir -p generated_reports
chmod 777 generated_reports
print_success "Directorios creados"

# 8. Configurar firewall
echo ""
echo "🔥 Configurando firewall..."
if command -v ufw &> /dev/null; then
    ufw --force enable
    ufw allow 22/tcp   # SSH
    ufw allow 8000/tcp # Aplicación
    print_success "Firewall configurado"
else
    print_warning "UFW no está disponible, configura el firewall manualmente"
fi

# 9. Construir y levantar contenedores
echo ""
echo "🏗️  Construyendo y levantando aplicación..."
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build

# Esperar a que la aplicación inicie
echo "⏳ Esperando a que la aplicación inicie..."
sleep 15

# 10. Crear usuario administrador
echo ""
echo "👤 Creando usuario administrador..."
docker exec -it conciliaciones-fastapi python scripts/crear_usuario_prueba.py || print_warning "No se pudo crear el usuario automáticamente"

# 11. Verificar estado
echo ""
echo "📊 Estado de la aplicación:"
docker ps | grep conciliaciones

# 12. Mostrar información final
echo ""
echo "================================================"
print_success "¡DESPLIEGUE COMPLETADO!"
echo "================================================"
echo ""
echo "🌐 Tu aplicación está disponible en:"
echo "   http://$PUBLIC_IP:8000"
echo ""
echo "🔐 Credenciales por defecto:"
echo "   Usuario: admin"
echo "   Contraseña: admin123"
echo ""
echo "📝 IMPORTANTE:"
echo "   1. Cambia la contraseña del usuario admin"
echo "   2. Revisa el archivo .env para ajustes adicionales"
echo "   3. Considera instalar Nginx + SSL para producción"
echo ""
echo "📋 Comandos útiles:"
echo "   Ver logs:      docker logs -f conciliaciones-fastapi"
echo "   Reiniciar:     docker-compose -f docker-compose.prod.yml restart"
echo "   Detener:       docker-compose -f docker-compose.prod.yml down"
echo "   Actualizar:    git pull && docker-compose -f docker-compose.prod.yml up -d --build"
echo ""
echo "📚 Más información en: /opt/conciliacion-B/DEPLOY.md"
echo ""
