#!/bin/bash

# Script de despliegue rápido en Digital Ocean
# Ejecutar con: bash deploy.sh

echo "🚀 Iniciando despliegue de Conciliaciones Bancarias..."

# 1. Verificar que estamos en el directorio correcto
if [ ! -f "docker-compose.prod.yml" ]; then
    echo "❌ Error: No se encontró docker-compose.prod.yml"
    echo "   Asegúrate de estar en el directorio del proyecto"
    exit 1
fi

# 2. Verificar que existe el archivo .env
if [ ! -f ".env" ]; then
    echo "⚠️  No se encontró archivo .env"
    echo "   Creando desde .env.example..."
    cp .env.example .env
    echo "   ⚠️  IMPORTANTE: Edita el archivo .env con tus configuraciones"
    echo "   nano .env"
    exit 1
fi

# 3. Crear directorios necesarios
echo "📁 Creando directorios..."
mkdir -p generated_reports
chmod 777 generated_reports

# 4. Detener contenedores anteriores
echo "🛑 Deteniendo contenedores anteriores..."
docker-compose -f docker-compose.prod.yml down

# 5. Construir y levantar contenedores
echo "🔨 Construyendo imagen Docker..."
docker-compose -f docker-compose.prod.yml build --no-cache

echo "🚀 Levantando contenedores..."
docker-compose -f docker-compose.prod.yml up -d

# 6. Esperar a que el contenedor esté listo
echo "⏳ Esperando a que la aplicación inicie..."
sleep 10

# 7. Verificar estado
echo "📊 Estado de contenedores:"
docker ps | grep conciliaciones

# 8. Mostrar logs
echo ""
echo "📋 Últimas líneas de logs:"
docker logs --tail 20 conciliaciones-fastapi

echo ""
echo "✅ Despliegue completado!"
echo ""
echo "🌐 La aplicación debería estar disponible en:"
echo "   http://$(curl -s ifconfig.me):8000"
echo ""
echo "📝 Para ver logs en tiempo real:"
echo "   docker logs -f conciliaciones-fastapi"
echo ""
echo "🔄 Para reiniciar:"
echo "   docker-compose -f docker-compose.prod.yml restart"
echo ""
echo "⚠️  IMPORTANTE: No olvides crear el usuario administrador:"
echo "   docker exec -it conciliaciones-fastapi python scripts/crear_usuario_prueba.py"
