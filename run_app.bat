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
    echo 🔍 Ejecute 'diagnostico.bat' para más información
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
    if exist "requirements-simple.txt" (
        echo ⚠ Usando requirements simplificados
        copy "requirements-simple.txt" "requirements.txt" >nul 2>&1
    ) else (
        echo ❌ ERROR: No se encontró ningún archivo de requirements
        pause
        exit /b 1
    )
)

:: Instalar/actualizar dependencias
echo.
call :mostrar_progreso "Configurando dependencias"
echo 📦 Actualizando pip...
venv\Scripts\python.exe -m pip install --upgrade pip --quiet >nul 2>&1

::echo 📦 Instalando dependencias...
venv\Scripts\python.exe -m pip install python-multipart fpdf2 --quiet >nul 2>&1

echo 📦 Instalando dependencias principales...
venv\Scripts\python.exe -m pip install fastapi uvicorn[standard] sqlalchemy python-dotenv jinja2 --quiet >nul 2>&1

echo 📦 Instalando dependencias de datos...
:: Instalar pandas desde wheel precompilado para evitar problemas de compilación
venv\Scripts\python.exe -m pip install --only-binary=all pandas openpyxl numpy --quiet >nul 2>&1

echo 📦 Instalando dependencias restantes...
venv\Scripts\python.exe -m pip install -r requirements.txt --only-binary=all --quiet >nul 2>&1

if %errorlevel% neq 0 (
    echo ⚠ Algunos paquetes necesitaron instalación manual...
    echo 📦 Instalando paquetes críticos individualmente...
    
    :: Instalar FastAPI y sus dependencias core
    venv\Scripts\python.exe -m pip install fastapi uvicorn
    if %errorlevel% neq 0 (
        echo ❌ ERROR: No se pudo instalar FastAPI
        pause
        exit /b 1
    )
    
    :: Instalar pandas con método alternativo
    echo 📦 Instalando pandas (esto puede tomar unos minutos)...
    venv\Scripts\python.exe -m pip install --prefer-binary pandas
    if %errorlevel% neq 0 (
        echo ⚠ Probando instalación de pandas sin dependencias de compilación...
        venv\Scripts\python.exe -m pip install --no-deps pandas
        if %errorlevel% neq 0 (
            echo ❌ WARNING: No se pudo instalar pandas. Funcionalidad limitada.
        )
    )
    
    :: Instalar SQLAlchemy y otras dependencias críticas
    venv\Scripts\python.exe -m pip install sqlalchemy python-multipart fpdf2 openpyxl jinja2 python-dotenv
    if %errorlevel% neq 0 (
        echo ❌ ERROR: No se pudieron instalar dependencias críticas
        pause
        exit /b 1
    )
)

echo.
echo ✅ Configuración completada
echo 🔍 Verificando instalación...

:: Verificar que FastAPI esté disponible
venv\Scripts\python.exe -c "import fastapi; print('✓ FastAPI instalado correctamente')" 2>nul
if %errorlevel% neq 0 (
    echo ❌ ERROR: FastAPI no está disponible
    pause
    exit /b 1
)

:: Verificar uvicorn
venv\Scripts\python.exe -c "import uvicorn; print('✓ Uvicorn instalado correctamente')" 2>nul
if %errorlevel% neq 0 (
    echo ❌ ERROR: Uvicorn no está disponible
    pause
    exit /b 1
)

:: Verificar pandas (opcional)
venv\Scripts\python.exe -c "import pandas; print('✓ Pandas disponible')" 2>nul
if %errorlevel% neq 0 (
    echo ⚠ WARNING: Pandas no disponible - funcionalidad limitada
)

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