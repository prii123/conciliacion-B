from fastapi import FastAPI, Request, Form, UploadFile
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from .database import Base, engine, SessionLocal
from .routers import empresas, conciliaciones
from .models import Empresa

# create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Conciliaciones Bancarias")

# Resolve project directory and point static and templates directories to the package's folders
project_dir = Path(__file__).resolve().parent
static_dir = project_dir / "static"
templates_dir = project_dir / "templates"

# mount static directory from app package (prevents RuntimeError when CWD differs)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
templates = Jinja2Templates(directory=str(templates_dir))

# include routers
app.include_router(empresas.router)
app.include_router(conciliaciones.router)

@app.get("/")
def root(request: Request):
    # Render the index template and pass the list of empresas for the picker
    db = SessionLocal()
    try:
        empresas_list = db.query(Empresa).order_by(Empresa.razon_social).all()
    finally:
        db.close()

    return templates.TemplateResponse("index.html", {"request": request, "empresas": empresas_list})

@app.post("/upload")
async def upload_files(
    request: Request,
    id_empresa: int = Form(...),
    mes: str = Form(...),
    anio: int = Form(...),
    cuenta: str = Form(...),
    banco: UploadFile = Form(...),
    auxiliar: UploadFile = Form(...),
):
    try:
        # Simular validación y procesamiento de archivos
        if banco.filename == "" or auxiliar.filename == "":
            raise ValueError("Ambos archivos deben ser cargados.")

        # Aquí iría la lógica para procesar los archivos y crear la conciliación
        # Por ejemplo, guardar los archivos y registrar la conciliación en la base de datos

        return templates.TemplateResponse("success.html", {"request": request})
    except Exception as e:
        return templates.TemplateResponse("error.html", {"request": request, "error_message": str(e)})