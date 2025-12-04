from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse
from app.database import get_db
from app.models import Conciliacion, Movimiento, User
from app.utils.pdf_generator import generar_pdf_informe
from app.utils.auth import get_current_active_user
import os

router = APIRouter()

@router.get("/{conciliacion_id}", response_class=FileResponse)
def generar_informe(
    conciliacion_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    conciliacion = db.query(Conciliacion).filter(Conciliacion.id == conciliacion_id).first()
    if not conciliacion:
        raise HTTPException(status_code=404, detail="Conciliación no encontrada")

    movimientos = db.query(Movimiento).filter(Movimiento.id_conciliacion == conciliacion_id).all()

    conciliados = [m for m in movimientos if m.estado_conciliacion == "conciliado"]
    pendientes = [m for m in movimientos if m.estado_conciliacion == "no_conciliado"]

    file_path = generar_pdf_informe(conciliacion, conciliados, pendientes)

    return FileResponse(file_path, media_type="application/pdf", filename=f"informe_conciliacion_{conciliacion_id}.pdf")