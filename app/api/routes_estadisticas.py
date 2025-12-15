"""
Rutas para estadísticas de conciliaciones
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, case, cast, Date
from app.database import get_db
from app.models import User, Conciliacion, Empresa
from app.utils.auth import get_current_admin_user
from typing import List, Dict, Optional
from datetime import datetime

router = APIRouter()


@router.get("/estadisticas", response_model=List[Dict])
async def obtener_estadisticas(
    año: Optional[int] = Query(None, description="Año a filtrar (por defecto año actual)"),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene estadísticas de conciliaciones agrupadas por empresa, año y mes
    Solo disponible para administradores
    """
    # Si no se especifica año, usar el año actual
    if año is None:
        año = datetime.now().year
    # Si no se especifica año, usar el año actual
    if año is None:
        año = datetime.now().year
    
    # Consulta agrupada por empresa, año y mes, filtrada por año
    resultados = db.query(
        Empresa.id.label('empresa_id'),
        Empresa.razon_social.label('empresa_nombre'),
        func.to_char(cast(Conciliacion.fecha_proceso, Date), 'YYYY').label('año'),
        func.to_char(cast(Conciliacion.fecha_proceso, Date), 'MM').label('mes'),
        func.count(Conciliacion.id).label('total_conciliaciones'),
        func.sum(
            case(
                (Conciliacion.estado == 'finalizada', 1),
                else_=0
            )
        ).label('completadas'),
        func.sum(
            case(
                (Conciliacion.estado.in_(['en_proceso', 'pendiente']), 1),
                else_=0
            )
        ).label('en_proceso')
    ).join(
        Empresa, Conciliacion.id_empresa == Empresa.id
    ).filter(
        func.to_char(cast(Conciliacion.fecha_proceso, Date), 'YYYY') == str(año)
    ).group_by(
        Empresa.id,
        Empresa.razon_social,
        func.to_char(cast(Conciliacion.fecha_proceso, Date), 'YYYY'),
        func.to_char(cast(Conciliacion.fecha_proceso, Date), 'MM')
    ).order_by(
        Empresa.razon_social,
        func.to_char(cast(Conciliacion.fecha_proceso, Date), 'YYYY').desc(),
        func.to_char(cast(Conciliacion.fecha_proceso, Date), 'MM').desc()
    ).all()

    # Transformar resultados en diccionarios
    estadisticas = []
    for r in resultados:
        estadisticas.append({
            'empresa_id': r.empresa_id,
            'empresa_nombre': r.empresa_nombre,
            'año': int(r.año),
            'mes': int(r.mes),
            'total_conciliaciones': r.total_conciliaciones,
            'completadas': r.completadas or 0,
            'en_proceso': r.en_proceso or 0
        })

    return estadisticas


@router.get("/estadisticas/resumen")
async def obtener_resumen_estadisticas(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene un resumen general de estadísticas
    """
    total_empresas = db.query(func.count(Empresa.id)).scalar()
    total_conciliaciones = db.query(func.count(Conciliacion.id)).scalar()
    
    # Completadas: estado 'finalizada'
    conciliaciones_completadas = db.query(func.count(Conciliacion.id)).filter(
        Conciliacion.estado == 'finalizada'
    ).scalar()
    
    # En proceso: estado 'en_proceso' o 'pendiente'
    conciliaciones_en_proceso = db.query(func.count(Conciliacion.id)).filter(
        Conciliacion.estado.in_(['en_proceso', 'pendiente'])
    ).scalar()

    return {
        'total_empresas': total_empresas or 0,
        'total_conciliaciones': total_conciliaciones or 0,
        'conciliaciones_completadas': conciliaciones_completadas or 0,
        'conciliaciones_en_proceso': conciliaciones_en_proceso or 0
    }


@router.get("/estadisticas/años")
async def obtener_años_disponibles(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene la lista de años con conciliaciones registradas
    """
    años = db.query(
        func.to_char(cast(Conciliacion.fecha_proceso, Date), 'YYYY').label('año')
    ).distinct().order_by(
        func.to_char(cast(Conciliacion.fecha_proceso, Date), 'YYYY').desc()
    ).all()
    
    return [int(a.año) for a in años if a.año]


@router.get("/estadisticas/meses-pendientes")
async def obtener_meses_pendientes(
    año: Optional[int] = Query(None, description="Año a consultar (por defecto año actual)"),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene los meses pendientes por conciliar (sin conciliaciones) 
    desde enero hasta el mes actual del año especificado
    """
    # Si no se especifica año, usar el año actual
    if año is None:
        año = datetime.now().year
    
    ahora = datetime.now()
    año_actual = ahora.year
    mes_actual = ahora.month
    
    # Si el año solicitado es futuro, no hay meses pendientes
    if año > año_actual:
        return []
    
    # Determinar hasta qué mes buscar
    mes_limite = 12 if año < año_actual else mes_actual
    
    # Obtener todas las empresas
    empresas = db.query(Empresa.id, Empresa.razon_social).all()
    
    # Para cada empresa, obtener los meses con conciliaciones
    resultado = []
    
    for empresa in empresas:
        meses_con_conciliacion = db.query(
            func.to_char(cast(Conciliacion.fecha_proceso, Date), 'MM').label('mes')
        ).filter(
            Conciliacion.id_empresa == empresa.id,
            func.to_char(cast(Conciliacion.fecha_proceso, Date), 'YYYY') == str(año)
        ).distinct().all()
        
        meses_con_data = set(int(m.mes) for m in meses_con_conciliacion)
        
        # Calcular meses pendientes (sin conciliaciones)
        meses_pendientes = []
        for mes in range(1, mes_limite + 1):
            if mes not in meses_con_data:
                meses_pendientes.append(mes)
        
        if meses_pendientes:
            resultado.append({
                'empresa_id': empresa.id,
                'empresa_nombre': empresa.razon_social,
                'meses_pendientes': meses_pendientes,
                'cantidad': len(meses_pendientes)
            })
    
    return resultado
