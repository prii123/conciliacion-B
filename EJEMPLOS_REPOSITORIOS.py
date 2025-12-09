"""
Ejemplos de uso de la capa de repositorios.
Este archivo muestra cómo usar los repositorios en nuevas funcionalidades.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.repositories.factory import RepositoryFactory
from app.utils.auth import get_current_active_user
from app.models import User

router = APIRouter()


# ============================================
# EJEMPLO 1: Endpoint simple con un repositorio
# ============================================

@router.get("/ejemplos/empresas-activas")
def listar_empresas_activas(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Listar solo empresas activas"""
    
    # Crear el factory
    factory = RepositoryFactory(db)
    
    # Obtener el repositorio de empresas
    empresa_repo = factory.get_empresa_repository()
    
    # Obtener todas las empresas
    empresas = empresa_repo.get_all()
    
    # Filtrar activas (esto idealmente estaría en el repositorio)
    empresas_activas = [e for e in empresas if e.estado == 'activa']
    
    return {
        "total": len(empresas_activas),
        "empresas": [
            {
                "id": e.id,
                "nit": e.nit,
                "razon_social": e.razon_social,
                "ciudad": e.ciudad
            }
            for e in empresas_activas
        ]
    }


# ============================================
# EJEMPLO 2: Usar múltiples repositorios
# ============================================

@router.get("/ejemplos/estadisticas-empresa/{empresa_id}")
def estadisticas_empresa(
    empresa_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener estadísticas completas de una empresa"""
    
    factory = RepositoryFactory(db)
    empresa_repo = factory.get_empresa_repository()
    conciliacion_repo = factory.get_conciliacion_repository()
    movimiento_repo = factory.get_movimiento_repository()
    
    # Obtener empresa
    empresa = empresa_repo.get_by_id(empresa_id)
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    # Obtener conciliaciones
    conciliaciones = conciliacion_repo.get_by_empresa(empresa_id)
    
    # Calcular estadísticas
    total_conciliaciones = len(conciliaciones)
    finalizadas = len([c for c in conciliaciones if c.estado == 'finalizada'])
    
    # Contar movimientos totales
    total_movimientos = 0
    for conc in conciliaciones:
        total_movimientos += movimiento_repo.count_by_conciliacion(conc.id)
    
    return {
        "empresa": {
            "id": empresa.id,
            "razon_social": empresa.razon_social,
            "nit": empresa.nit
        },
        "estadisticas": {
            "total_conciliaciones": total_conciliaciones,
            "conciliaciones_finalizadas": finalizadas,
            "conciliaciones_pendientes": total_conciliaciones - finalizadas,
            "total_movimientos": total_movimientos,
            "porcentaje_completado": round((finalizadas / total_conciliaciones * 100) if total_conciliaciones > 0 else 0, 2)
        }
    }


# ============================================
# EJEMPLO 3: Crear registros relacionados
# ============================================

@router.post("/ejemplos/quick-conciliacion")
def crear_conciliacion_rapida(
    empresa_id: int,
    mes: str,
    cuenta: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Crear una conciliación rápida sin archivos"""
    
    factory = RepositoryFactory(db)
    empresa_repo = factory.get_empresa_repository()
    conciliacion_repo = factory.get_conciliacion_repository()
    
    # Verificar que la empresa existe
    empresa = empresa_repo.get_by_id(empresa_id)
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    # Crear la conciliación
    from datetime import datetime
    conciliacion_data = {
        "id_empresa": empresa_id,
        "fecha_proceso": datetime.now().strftime("%Y-%m-%d"),
        "mes_conciliado": mes,
        "cuenta_conciliada": cuenta,
        "estado": "en_proceso",
        "nombre_archivo_banco": "manual",
        "nombre_archivo_auxiliar": "manual"
    }
    
    nueva_conciliacion = conciliacion_repo.create(conciliacion_data)
    
    return {
        "success": True,
        "conciliacion": {
            "id": nueva_conciliacion.id,
            "mes": nueva_conciliacion.mes_conciliado,
            "cuenta": nueva_conciliacion.cuenta_conciliada,
            "estado": nueva_conciliacion.estado
        },
        "mensaje": f"Conciliación #{nueva_conciliacion.id} creada exitosamente"
    }


# ============================================
# EJEMPLO 4: Operaciones en lote
# ============================================

@router.post("/ejemplos/importar-movimientos-lote")
def importar_movimientos_lote(
    conciliacion_id: int,
    movimientos: list,  # Lista de dicts con datos de movimientos
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Importar múltiples movimientos de una vez"""
    
    factory = RepositoryFactory(db)
    conciliacion_repo = factory.get_conciliacion_repository()
    movimiento_repo = factory.get_movimiento_repository()
    
    # Verificar conciliación
    conciliacion = conciliacion_repo.get_by_id(conciliacion_id)
    if not conciliacion:
        raise HTTPException(status_code=404, detail="Conciliación no encontrada")
    
    # Preparar datos
    movimientos_data = []
    for mov in movimientos:
        movimientos_data.append({
            "id_conciliacion": conciliacion_id,
            "fecha": mov.get("fecha"),
            "descripcion": mov.get("descripcion"),
            "valor": mov.get("valor"),
            "tipo": mov.get("tipo"),  # 'banco' o 'auxiliar'
            "es": mov.get("es"),  # 'E' o 'S'
            "estado_conciliacion": "no_conciliado"
        })
    
    # Crear en lote (más eficiente que uno por uno)
    movimientos_creados = movimiento_repo.create_bulk(movimientos_data)
    
    return {
        "success": True,
        "total_creados": len(movimientos_creados),
        "mensaje": f"{len(movimientos_creados)} movimientos importados"
    }


# ============================================
# EJEMPLO 5: Búsquedas complejas
# ============================================

@router.get("/ejemplos/movimientos-sin-conciliar")
def movimientos_sin_conciliar(
    conciliacion_id: int,
    tipo: str = None,  # 'banco' o 'auxiliar'
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener movimientos pendientes de conciliar"""
    
    factory = RepositoryFactory(db)
    movimiento_repo = factory.get_movimiento_repository()
    
    # Construir filtros
    filters = {"estado_conciliacion": "no_conciliado"}
    if tipo:
        filters["tipo"] = tipo
    
    # Obtener movimientos
    movimientos = movimiento_repo.get_by_conciliacion(conciliacion_id, filters)
    
    # Calcular totales
    total_valor = sum(m.valor for m in movimientos)
    
    return {
        "conciliacion_id": conciliacion_id,
        "tipo_filtrado": tipo or "todos",
        "cantidad": len(movimientos),
        "valor_total": total_valor,
        "movimientos": [
            {
                "id": m.id,
                "fecha": m.fecha,
                "descripcion": m.descripcion,
                "valor": m.valor,
                "tipo": m.tipo
            }
            for m in movimientos
        ]
    }


# ============================================
# EJEMPLO 6: Actualización de múltiples registros
# ============================================

@router.put("/ejemplos/marcar-movimientos-revisados")
def marcar_movimientos_revisados(
    movimiento_ids: list[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Marcar múltiples movimientos como revisados"""
    
    factory = RepositoryFactory(db)
    movimiento_repo = factory.get_movimiento_repository()
    
    # Preparar actualizaciones
    updates = []
    for mov_id in movimiento_ids:
        updates.append({
            "id": mov_id,
            "estado_conciliacion": "revisado"  # o cualquier otro estado
        })
    
    # Actualizar en lote
    movimiento_repo.update_bulk(updates)
    
    return {
        "success": True,
        "actualizados": len(movimiento_ids),
        "mensaje": f"{len(movimiento_ids)} movimientos actualizados"
    }


# ============================================
# EJEMPLO 7: Helper function para simplificar
# ============================================

def get_repos(db: Session):
    """
    Helper function para obtener todos los repositorios de una vez.
    Útil cuando necesitas varios repositorios en una función.
    """
    factory = RepositoryFactory(db)
    return {
        'user': factory.get_user_repository(),
        'empresa': factory.get_empresa_repository(),
        'conciliacion': factory.get_conciliacion_repository(),
        'movimiento': factory.get_movimiento_repository(),
        'match': factory.get_match_repository(),
        'manual': factory.get_manual_repository()
    }


@router.get("/ejemplos/dashboard")
def dashboard_completo(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Dashboard con estadísticas globales"""
    
    # Obtener todos los repositorios
    repos = get_repos(db)
    
    # Obtener estadísticas
    total_empresas = len(repos['empresa'].get_all())
    total_conciliaciones = len(repos['conciliacion'].get_all())
    
    # Calcular conciliaciones activas
    conciliaciones = repos['conciliacion'].get_all()
    activas = len([c for c in conciliaciones if c.estado == 'en_proceso'])
    
    return {
        "estadisticas_globales": {
            "total_empresas": total_empresas,
            "total_conciliaciones": total_conciliaciones,
            "conciliaciones_activas": activas,
            "conciliaciones_finalizadas": total_conciliaciones - activas,
            "usuario_actual": current_user.username
        }
    }


# ============================================
# EJEMPLO 8: Testing con repositorios mock
# ============================================

"""
Para testing, puedes crear mocks fácilmente:

from unittest.mock import Mock
from app.repositories.interfaces import IEmpresaRepository

def test_listar_empresas():
    # Mock del repositorio
    mock_repo = Mock(spec=IEmpresaRepository)
    mock_repo.get_all.return_value = [
        Mock(id=1, nit="123", razon_social="Empresa Test", estado="activa")
    ]
    
    # Usar el mock
    empresas = mock_repo.get_all()
    
    # Verificar
    assert len(empresas) == 1
    assert empresas[0].razon_social == "Empresa Test"
    mock_repo.get_all.assert_called_once()
"""
