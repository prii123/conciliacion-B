@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ==========================================
echo    Modulo Conciliaciones Bancarias 
echo ==========================================
echo.

:: Cambiar al directorio del script
cd /d "%~dp0"

:: Verificar si Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ ERROR: Python no está instalado o no está en PATH
    echo Por favor instale Python 3.7 o superior
    pause
    exit /b 1
)

:: Verificar si existe el entorno virtual
if exist "venv\Scripts\activate.bat" (
    echo ✓ Entorno virtual encontrado
) else (
    echo ⚠ Entorno virtual no encontrado
    echo.
    call :mostrar_progreso "Creando entorno virtual"
    python -m venv venv >nul 2>&1
    if %errorlevel% neq 0 (
        echo ❌ ERROR: No se pudo crear el entorno virtual
        pause
        exit /b 1
    )
    echo ✓ Entorno virtual creado exitosamente
    echo.
)

:: Activar el entorno virtual
echo 🔄 Activando entorno virtual...
call venv\Scripts\activate.bat

:: Verificar si requirements.txt existe
if not exist "requirements.txt" (
    echo ❌ ERROR: No se encontró el archivo requirements.txt
    pause
    exit /b 1
)

:: Instalar/actualizar dependencias
echo.
call :mostrar_progreso "Configurando dependencias"
echo 📦 Actualizando pip...
venv\Scripts\python.exe -m pip install --upgrade pip --quiet >nul 2>&1

echo 📦 Instalando dependencias...
venv\Scripts\python.exe -m pip install python-multipart fpdf2 --quiet >nul 2>&1
venv\Scripts\python.exe -m pip install -r requirements.txt --quiet >nul 2>&1

if %errorlevel% neq 0 (
    echo ❌ ERROR: No se pudieron instalar las dependencias
    echo Intentando instalación manual...
    venv\Scripts\python.exe -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        pause
        exit /b 1
    )
)

echo.
echo ✅ Configuración completada
echo ==========================================
echo    🚀 Iniciando servidor 
echo ==========================================
echo.
echo 🌐 Servidor disponible en: http://localhost:8000
echo 📖 Documentación API en: http://localhost:8000/docs
echo.
echo ⏹ Presiona Ctrl+C para detener el servidor
echo ==========================================
echo.

:: Ejecutar la aplicación
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

:: Si el servidor se detiene, mostrar mensaje
echo.
echo 🛑 Servidor detenido
pause

goto :eof

:: Función para mostrar progreso con animación
:mostrar_progreso
set "mensaje=%~1"
echo %mensaje%...
for /L %%i in (1,1,3) do (
    echo|set /p="."
    timeout /t 1 >nul 2>&1
)
echo. 
goto :eof