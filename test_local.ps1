# Script para probar el despliegue localmente en Windows
# Ejecutar con: .\test_local.ps1

Write-Host "🧪 PRUEBA LOCAL - Conciliaciones Bancarias" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar Docker
Write-Host "🐳 Verificando Docker..." -ForegroundColor Yellow
if (Get-Command docker -ErrorAction SilentlyContinue) {
    $dockerVersion = docker --version
    Write-Host "✅ Docker instalado: $dockerVersion" -ForegroundColor Green
} else {
    Write-Host "❌ Docker no está instalado" -ForegroundColor Red
    Write-Host "   Instala Docker Desktop desde: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

# Verificar Docker Compose
Write-Host "🐳 Verificando Docker Compose..." -ForegroundColor Yellow
if (Get-Command docker-compose -ErrorAction SilentlyContinue) {
    $composeVersion = docker-compose --version
    Write-Host "✅ Docker Compose instalado: $composeVersion" -ForegroundColor Green
} else {
    Write-Host "❌ Docker Compose no está instalado" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Crear .env si no existe
if (-not (Test-Path ".env")) {
    Write-Host "⚙️  Creando archivo .env para desarrollo local..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    
    # Para desarrollo local, mantener localhost
    $envContent = Get-Content ".env"
    $envContent = $envContent -replace "API_BASE_URL=.*", "API_BASE_URL=http://localhost:8000"
    $envContent = $envContent -replace "ALLOWED_ORIGINS=.*", "ALLOWED_ORIGINS=http://localhost:8000,http://localhost,http://127.0.0.1:8000"
    
    # Generar JWT secret
    $bytes = New-Object byte[] 32
    [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
    $jwtSecret = [System.BitConverter]::ToString($bytes).Replace("-", "").ToLower()
    $envContent = $envContent -replace "JWT_SECRET_KEY=.*", "JWT_SECRET_KEY=$jwtSecret"
    
    $envContent | Set-Content ".env"
    Write-Host "✅ Archivo .env creado" -ForegroundColor Green
} else {
    Write-Host "✅ Archivo .env ya existe" -ForegroundColor Green
}

Write-Host ""

# Crear directorio para reportes
if (-not (Test-Path "generated_reports")) {
    New-Item -ItemType Directory -Path "generated_reports" | Out-Null
    Write-Host "✅ Directorio generated_reports creado" -ForegroundColor Green
} else {
    Write-Host "✅ Directorio generated_reports existe" -ForegroundColor Green
}

Write-Host ""

# Detener contenedores anteriores
Write-Host "🛑 Deteniendo contenedores anteriores..." -ForegroundColor Yellow
docker-compose down 2>$null
Write-Host "✅ Contenedores detenidos" -ForegroundColor Green

Write-Host ""

# Construir imagen
Write-Host "🔨 Construyendo imagen Docker..." -ForegroundColor Yellow
docker-compose build
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Imagen construida exitosamente" -ForegroundColor Green
} else {
    Write-Host "❌ Error al construir la imagen" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Levantar contenedores
Write-Host "🚀 Levantando contenedores..." -ForegroundColor Yellow
docker-compose up -d
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Contenedores levantados" -ForegroundColor Green
} else {
    Write-Host "❌ Error al levantar contenedores" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Esperar a que la aplicación inicie
Write-Host "⏳ Esperando a que la aplicación inicie..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Verificar estado
Write-Host "📊 Estado de contenedores:" -ForegroundColor Yellow
docker ps --filter "name=conciliaciones"

Write-Host ""

# Crear usuario administrador
Write-Host "👤 Creando usuario administrador..." -ForegroundColor Yellow
docker exec -it conciliaciones-fastapi python scripts/crear_usuario_prueba.py
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Usuario creado" -ForegroundColor Green
} else {
    Write-Host "⚠️  No se pudo crear el usuario automáticamente" -ForegroundColor Yellow
    Write-Host "   Ejecútalo manualmente:" -ForegroundColor Yellow
    Write-Host "   docker exec -it conciliaciones-fastapi python scripts/crear_usuario_prueba.py" -ForegroundColor White
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "✅ ¡APLICACIÓN LISTA!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "🌐 Accede a la aplicación en:" -ForegroundColor White
Write-Host "   http://localhost:8000" -ForegroundColor Cyan
Write-Host ""
Write-Host "🔐 Credenciales:" -ForegroundColor White
Write-Host "   Usuario: admin" -ForegroundColor White
Write-Host "   Contraseña: admin123" -ForegroundColor White
Write-Host ""
Write-Host "📚 API Docs:" -ForegroundColor White
Write-Host "   http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "📝 Comandos útiles:" -ForegroundColor White
Write-Host "   Ver logs:      docker logs -f conciliaciones-fastapi" -ForegroundColor White
Write-Host "   Reiniciar:     docker-compose restart" -ForegroundColor White
Write-Host "   Detener:       docker-compose down" -ForegroundColor White
Write-Host ""
Write-Host "🎉 ¡Prueba la aplicación!" -ForegroundColor Green
Write-Host ""
