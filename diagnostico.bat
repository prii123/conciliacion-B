@echo off
chcp 65001 >nul
echo ==========================================
echo    Diagnóstico del Sistema
echo ==========================================
echo.

echo 🔍 Verificando Python...
python --version 2>nul
if %errorlevel% neq 0 (
    echo ❌ Python no encontrado
    echo Por favor instale Python desde https://www.python.org/
) else (
    echo ✓ Python instalado
)

echo.
echo 🔍 Verificando pip...
python -m pip --version 2>nul
if %errorlevel% neq 0 (
    echo ❌ pip no disponible
) else (
    echo ✓ pip disponible
)

echo.
echo 🔍 Verificando herramientas de compilación...
python -c "import distutils.util; print('✓ distutils disponible')" 2>nul
if %errorlevel% neq 0 (
    echo ⚠ distutils no disponible - puede causar problemas con algunos paquetes
)

echo.
echo 🔍 Verificando Visual Studio Build Tools...
where cl.exe >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠ Visual Studio Build Tools no encontrados
    echo   Esto puede causar problemas al instalar algunos paquetes como pandas
    echo   Solución: Instalar "Microsoft C++ Build Tools" o Visual Studio
) else (
    echo ✓ Herramientas de compilación disponibles
)

echo.
echo 🔍 Verificando conectividad a PyPI...
python -m pip search setuptools >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠ Problemas de conectividad o PyPI no accesible
) else (
    echo ✓ Conectividad a PyPI disponible
)

echo.
echo ==========================================
echo    Soluciones Sugeridas
echo ==========================================
echo.
echo Si pandas falla al instalar:
echo 1. Instalar Visual Studio Build Tools
echo 2. Usar conda en lugar de pip: conda install pandas
echo 3. Descargar wheel precompilado desde PyPI
echo.
echo Si persisten los problemas:
echo - Usar Python 3.11 (más estable para Windows)
echo - Crear entorno virtual limpio
echo - Actualizar pip: python -m pip install --upgrade pip
echo.
pause