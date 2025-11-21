@echo off
chcp 65001 >nul
:: Script rápido para desarrolladores
cd /d "%~dp0"

if exist "venv\Scripts\activate.bat" (
    echo 🔄 Activando entorno virtual...
    call venv\Scripts\activate.bat
) else (
    echo ⚙ Creando entorno virtual...
    python -m venv venv >nul 2>&1
    call venv\Scripts\activate.bat
    echo 📦 Instalando dependencias...
    venv\Scripts\python.exe -m pip install python-multipart fpdf2 --quiet >nul 2>&1
    venv\Scripts\python.exe -m pip install -r requirements.txt --quiet >nul 2>&1
    echo ✅ Configuración completada
)

echo 🚀 Iniciando FastAPI...
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000