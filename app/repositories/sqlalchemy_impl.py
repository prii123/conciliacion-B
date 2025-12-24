"""
Implementación de repositorios usando SQLAlchemy.
Esta es la capa que interactúa directamente con la base de datos.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, and_
from datetime import datetime

from ..models import (
    User, Empresa, Conciliacion, Movimiento, 
    ConciliacionMatch, ConciliacionManual,
    ConciliacionManualBanco, ConciliacionManualAuxiliar, Task, DeepSeekProcessingResult
)
from .interfaces import (
    IUserRepository, IEmpresaRepository, IConciliacionRepository,
    IMovimientoRepository, IConciliacionMatchRepository, IConciliacionManualRepository, ITaskRepository, IDeepSeekProcessingResultRepository
)


class SQLAlchemyUserRepository(IUserRepository):
    """Implementación de UserRepository con SQLAlchemy"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, user_id: int):
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_username(self, username: str):
        return self.db.query(User).filter(User.username == username).first()
    
    def get_by_email(self, email: str):
        return self.db.query(User).filter(User.email == email).first()
    
    def get_all(self) -> List:
        return self.db.query(User).order_by(desc(User.created_at)).all()
    
    def create(self, user_data: Dict[str, Any]):
        user = User(**user_data)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def update(self, user_id: int, user_data: Dict[str, Any]):
        user = self.get_by_id(user_id)
        if user:
            for key, value in user_data.items():
                setattr(user, key, value)
            self.db.commit()
            self.db.refresh(user)
        return user
    
    def delete(self, user_id: int):
        user = self.get_by_id(user_id)
        if user:
            self.db.delete(user)
            self.db.commit()
        return user


class SQLAlchemyEmpresaRepository(IEmpresaRepository):
    """Implementación de EmpresaRepository con SQLAlchemy"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, empresa_id: int):
        return self.db.query(Empresa).filter(Empresa.id == empresa_id).first()
    
    def get_by_nit(self, nit: str):
        return self.db.query(Empresa).filter(Empresa.nit == nit).first()
    
    def get_all(self, order_by: str = 'id', desc_order: bool = True) -> List:
        query = self.db.query(Empresa)
        if desc_order:
            query = query.order_by(desc(getattr(Empresa, order_by)))
        else:
            query = query.order_by(asc(getattr(Empresa, order_by)))
        return query.all()
    
    def get_by_usuario(self, usuario_id: int) -> List:
        return (self.db.query(Empresa)
                .filter(Empresa.id_usuario_creador == usuario_id)
                .order_by(desc(Empresa.fecha_creacion))
                .all())
    
    def create(self, empresa_data: Dict[str, Any]):
        empresa = Empresa(**empresa_data)
        self.db.add(empresa)
        self.db.commit()
        self.db.refresh(empresa)
        return empresa
    
    def update(self, empresa_id: int, empresa_data: Dict[str, Any]):
        empresa = self.get_by_id(empresa_id)
        if empresa:
            for key, value in empresa_data.items():
                setattr(empresa, key, value)
            self.db.commit()
            self.db.refresh(empresa)
        return empresa
    
    def delete(self, empresa_id: int):
        empresa = self.get_by_id(empresa_id)
        if empresa:
            self.db.delete(empresa)
            self.db.commit()
        return empresa


class SQLAlchemyConciliacionRepository(IConciliacionRepository):
    """Implementación de ConciliacionRepository con SQLAlchemy"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, conciliacion_id: int):
        return self.db.query(Conciliacion).filter(Conciliacion.id == conciliacion_id).first()
    
    def get_all(self, order_by: str = 'id', desc_order: bool = True) -> List:
        query = self.db.query(Conciliacion)
        if desc_order:
            query = query.order_by(desc(getattr(Conciliacion, order_by)))
        else:
            query = query.order_by(asc(getattr(Conciliacion, order_by)))
        return query.all()
    
    def get_by_empresa(self, empresa_id: int) -> List:
        return self.db.query(Conciliacion).filter(
            Conciliacion.id_empresa == empresa_id
        ).order_by(desc(Conciliacion.id)).all()
    
    def get_by_usuario(self, usuario_id: int) -> List:
        """Obtiene todas las conciliaciones creadas por un usuario"""
        return self.db.query(Conciliacion).filter(
            Conciliacion.id_usuario_creador == usuario_id
        ).order_by(desc(Conciliacion.id)).all()
    
    def create(self, conciliacion_data: Dict[str, Any]):
        conciliacion = Conciliacion(**conciliacion_data)
        self.db.add(conciliacion)
        self.db.commit()
        self.db.refresh(conciliacion)
        return conciliacion
    
    def update(self, conciliacion_id: int, conciliacion_data: Dict[str, Any]):
        conciliacion = self.get_by_id(conciliacion_id)
        if conciliacion:
            for key, value in conciliacion_data.items():
                setattr(conciliacion, key, value)
            self.db.commit()
            self.db.refresh(conciliacion)
        return conciliacion
    
    def delete(self, conciliacion_id: int):
        conciliacion = self.get_by_id(conciliacion_id)
        if conciliacion:
            self.db.delete(conciliacion)
            self.db.commit()
        return conciliacion


class SQLAlchemyMovimientoRepository(IMovimientoRepository):
    """Implementación de MovimientoRepository con SQLAlchemy"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, movimiento_id: int):
        return self.db.query(Movimiento).filter(Movimiento.id == movimiento_id).first()
    
    def get_by_conciliacion(self, conciliacion_id: int, filters: Optional[Dict[str, Any]] = None) -> List:
        query = self.db.query(Movimiento).filter(Movimiento.id_conciliacion == conciliacion_id)
        
        if filters:
            if 'tipo' in filters:
                query = query.filter(Movimiento.tipo == filters['tipo'])
            if 'es' in filters:
                query = query.filter(Movimiento.es == filters['es'])
            if 'estado_conciliacion' in filters:
                query = query.filter(Movimiento.estado_conciliacion == filters['estado_conciliacion'])
        
        return query.all()
    
    def count_by_conciliacion(self, conciliacion_id: int, filters: Optional[Dict[str, Any]] = None) -> int:
        query = self.db.query(Movimiento).filter(Movimiento.id_conciliacion == conciliacion_id)
        
        if filters:
            if 'tipo' in filters:
                query = query.filter(Movimiento.tipo == filters['tipo'])
            if 'es' in filters:
                query = query.filter(Movimiento.es == filters['es'])
            if 'estado_conciliacion' in filters:
                query = query.filter(Movimiento.estado_conciliacion == filters['estado_conciliacion'])
        
        return query.count()
    
    def create(self, movimiento_data: Dict[str, Any]):
        movimiento = Movimiento(**movimiento_data)
        self.db.add(movimiento)
        self.db.commit()
        self.db.refresh(movimiento)
        return movimiento
    
    def create_bulk(self, movimientos_data: List[Dict[str, Any]]) -> List:
        movimientos = [Movimiento(**data) for data in movimientos_data]
        self.db.add_all(movimientos)
        self.db.commit()
        for mov in movimientos:
            self.db.refresh(mov)
        return movimientos
    
    def update(self, movimiento_id: int, movimiento_data: Dict[str, Any]):
        movimiento = self.get_by_id(movimiento_id)
        if movimiento:
            for key, value in movimiento_data.items():
                setattr(movimiento, key, value)
            self.db.commit()
            self.db.refresh(movimiento)
        return movimiento
    
    def update_bulk(self, movimientos_updates: List[Dict[str, Any]]):
        """
        Actualiza múltiples movimientos.
        Cada dict debe tener 'id' y los campos a actualizar
        """
        for update_data in movimientos_updates:
            movimiento_id = update_data.pop('id')
            self.update(movimiento_id, update_data)
    
    def delete(self, movimiento_id: int):
        movimiento = self.get_by_id(movimiento_id)
        if movimiento:
            self.db.delete(movimiento)
            self.db.commit()
        return movimiento


class SQLAlchemyConciliacionMatchRepository(IConciliacionMatchRepository):
    """Implementación de ConciliacionMatchRepository con SQLAlchemy"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, match_id: int):
        return self.db.query(ConciliacionMatch).filter(ConciliacionMatch.id == match_id).first()
    
    def get_by_conciliacion(self, conciliacion_id: int) -> List:
        return self.db.query(ConciliacionMatch).filter(
            ConciliacionMatch.id_conciliacion == conciliacion_id
        ).all()
    
    def create(self, match_data: Dict[str, Any]):
        match = ConciliacionMatch(**match_data)
        self.db.add(match)
        self.db.commit()
        self.db.refresh(match)
        return match
    
    def create_bulk(self, matches_data: List[Dict[str, Any]]) -> List:
        matches = [ConciliacionMatch(**data) for data in matches_data]
        self.db.add_all(matches)
        self.db.commit()
        for match in matches:
            self.db.refresh(match)
        return matches
    
    def delete(self, match_id: int):
        match = self.get_by_id(match_id)
        if match:
            self.db.delete(match)
            self.db.commit()
        return match
    
    def delete_by_conciliacion(self, conciliacion_id: int):
        self.db.query(ConciliacionMatch).filter(
            ConciliacionMatch.id_conciliacion == conciliacion_id
        ).delete()
        self.db.commit()


class SQLAlchemyConciliacionManualRepository(IConciliacionManualRepository):
    """Implementación de ConciliacionManualRepository con SQLAlchemy"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, manual_id: int):
        return self.db.query(ConciliacionManual).filter(ConciliacionManual.id == manual_id).first()
    
    def get_by_conciliacion(self, conciliacion_id: int) -> List:
        return self.db.query(ConciliacionManual).filter(
            ConciliacionManual.id_conciliacion == conciliacion_id
        ).all()
    
    def create(self, manual_data: Dict[str, Any]):
        manual = ConciliacionManual(**manual_data)
        self.db.add(manual)
        self.db.commit()
        self.db.refresh(manual)
        return manual
    
    def delete(self, manual_id: int):
        manual = self.get_by_id(manual_id)
        if manual:
            self.db.delete(manual)
            self.db.commit()
        return manual
    
    def get_banco_items(self, manual_id: int) -> List:
        return self.db.query(ConciliacionManualBanco).filter(
            ConciliacionManualBanco.id_conciliacion_manual == manual_id
        ).all()
    
    def get_auxiliar_items(self, manual_id: int) -> List:
        return self.db.query(ConciliacionManualAuxiliar).filter(
            ConciliacionManualAuxiliar.id_conciliacion_manual == manual_id
        ).all()
    
    def create_banco_item(self, item_data: Dict[str, Any]):
        item = ConciliacionManualBanco(**item_data)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item
    
    def create_auxiliar_item(self, item_data: Dict[str, Any]):
        item = ConciliacionManualAuxiliar(**item_data)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item


class SQLAlchemyTaskRepository(ITaskRepository):
    """Implementación de TaskRepository con SQLAlchemy"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, task_id: int):
        return self.db.query(Task).filter(Task.id == task_id).first()
    
    def get_by_conciliacion(self, conciliacion_id: int) -> List:
        return self.db.query(Task).filter(Task.id_conciliacion == conciliacion_id).order_by(desc(Task.created_at)).all()
    
    def get_pending(self) -> List:
        return self.db.query(Task).filter(Task.estado.in_(['pending', 'processing'])).order_by(desc(Task.created_at)).all()
    
    def get_by_user(self, user_id: int) -> List:
        from ..models import Conciliacion
        return self.db.query(Task).join(Conciliacion).filter(Conciliacion.id_usuario_creador == user_id).order_by(desc(Task.created_at)).all()
    
    def create(self, task_data: Dict[str, Any]):
        task = Task(**task_data)
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task
    
    def update(self, task_id: int, task_data: Dict[str, Any]):
        task = self.get_by_id(task_id)
        if task:
            for key, value in task_data.items():
                setattr(task, key, value)
            task.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.db.commit()
            self.db.refresh(task)
        return task
    
    def delete(self, task_id: int):
        task = self.get_by_id(task_id)
        if task:
            self.db.delete(task)
            self.db.commit()
            return True
        return False
    
    def count_pending(self) -> int:
        return self.db.query(Task).filter(Task.estado.in_(['pending', 'processing'])).count()


class SQLAlchemyDeepSeekProcessingResultRepository(IDeepSeekProcessingResultRepository):
    """Implementación de DeepSeekProcessingResultRepository con SQLAlchemy"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_task(self, task_id: int) -> List:
        return self.db.query(DeepSeekProcessingResult).filter(DeepSeekProcessingResult.id_task == task_id).order_by(DeepSeekProcessingResult.group_number).all()
    
    def get_by_task_and_group(self, task_id: int, group_number: int):
        return self.db.query(DeepSeekProcessingResult).filter(
            DeepSeekProcessingResult.id_task == task_id,
            DeepSeekProcessingResult.group_number == group_number
        ).first()
    
    def create(self, result_data: Dict[str, Any]):
        result = DeepSeekProcessingResult(**result_data)
        self.db.add(result)
        self.db.commit()
        self.db.refresh(result)
        return result
    
    def update(self, result_id: int, result_data: Dict[str, Any]):
        result = self.db.query(DeepSeekProcessingResult).filter(DeepSeekProcessingResult.id == result_id).first()
        if result:
            for key, value in result_data.items():
                setattr(result, key, value)
            result.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.db.commit()
            self.db.refresh(result)
        return result
    
    def get_successful_results(self, task_id: int) -> List:
        return self.db.query(DeepSeekProcessingResult).filter(
            DeepSeekProcessingResult.id_task == task_id,
            DeepSeekProcessingResult.status == 'saved'
        ).order_by(DeepSeekProcessingResult.group_number).all()
    
    def delete_by_task(self, task_id: int):
        results = self.db.query(DeepSeekProcessingResult).filter(DeepSeekProcessingResult.id_task == task_id).all()
        for result in results:
            self.db.delete(result)
        self.db.commit()
