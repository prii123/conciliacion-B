"""
Factory para crear instancias de repositorios.
Facilita el cambio entre diferentes implementaciones (SQLAlchemy, MySQL directo, etc.)
"""
from sqlalchemy.orm import Session
from typing import Literal

from .interfaces import (
    IUserRepository, IEmpresaRepository, IConciliacionRepository,
    IMovimientoRepository, IConciliacionMatchRepository, IConciliacionManualRepository, ITaskRepository, IDeepSeekProcessingResultRepository
)
from .sqlalchemy_impl import (
    SQLAlchemyUserRepository,
    SQLAlchemyEmpresaRepository,
    SQLAlchemyConciliacionRepository,
    SQLAlchemyMovimientoRepository,
    SQLAlchemyConciliacionMatchRepository,
    SQLAlchemyConciliacionManualRepository,
    SQLAlchemyTaskRepository,
    SQLAlchemyDeepSeekProcessingResultRepository
)


class RepositoryFactory:
    """
    Factory para crear repositorios.
    
    Uso:
        factory = RepositoryFactory(db)
        user_repo = factory.get_user_repository()
        empresa_repo = factory.get_empresa_repository()
    
    Para cambiar a otra implementación (ej: MySQL directo), 
    solo hay que modificar esta clase.
    """
    
    def __init__(self, db: Session, implementation: Literal['sqlalchemy'] = 'sqlalchemy'):
        self.db = db
        self.implementation = implementation
    
    def get_user_repository(self) -> IUserRepository:
        """Obtiene repositorio de usuarios"""
        if self.implementation == 'sqlalchemy':
            return SQLAlchemyUserRepository(self.db)
        # Aquí se pueden agregar otras implementaciones:
        # elif self.implementation == 'mysql':
        #     return MySQLUserRepository(self.db)
        raise ValueError(f"Implementación desconocida: {self.implementation}")
    
    def get_empresa_repository(self) -> IEmpresaRepository:
        """Obtiene repositorio de empresas"""
        if self.implementation == 'sqlalchemy':
            return SQLAlchemyEmpresaRepository(self.db)
        raise ValueError(f"Implementación desconocida: {self.implementation}")
    
    def get_conciliacion_repository(self) -> IConciliacionRepository:
        """Obtiene repositorio de conciliaciones"""
        if self.implementation == 'sqlalchemy':
            return SQLAlchemyConciliacionRepository(self.db)
        raise ValueError(f"Implementación desconocida: {self.implementation}")
    
    def get_movimiento_repository(self) -> IMovimientoRepository:
        """Obtiene repositorio de movimientos"""
        if self.implementation == 'sqlalchemy':
            return SQLAlchemyMovimientoRepository(self.db)
        raise ValueError(f"Implementación desconocida: {self.implementation}")
    
    def get_match_repository(self) -> IConciliacionMatchRepository:
        """Obtiene repositorio de matches"""
        if self.implementation == 'sqlalchemy':
            return SQLAlchemyConciliacionMatchRepository(self.db)
        raise ValueError(f"Implementación desconocida: {self.implementation}")
    
    def get_manual_repository(self) -> IConciliacionManualRepository:
        """Obtiene repositorio de conciliaciones manuales"""
        if self.implementation == 'sqlalchemy':
            return SQLAlchemyConciliacionManualRepository(self.db)
        raise ValueError(f"Implementación desconocida: {self.implementation}")
    
    def get_task_repository(self) -> ITaskRepository:
        """Obtiene repositorio de tareas"""
        if self.implementation == 'sqlalchemy':
            return SQLAlchemyTaskRepository(self.db)
        raise ValueError(f"Implementación desconocida: {self.implementation}")
    
    def get_deepseek_result_repository(self) -> IDeepSeekProcessingResultRepository:
        """Obtiene repositorio de resultados de procesamiento DeepSeek"""
        if self.implementation == 'sqlalchemy':
            return SQLAlchemyDeepSeekProcessingResultRepository(self.db)
        raise ValueError(f"Implementación desconocida: {self.implementation}")


# Helper function para obtener todos los repositorios de una vez
def get_repositories(db: Session):
    """
    Función helper que devuelve todos los repositorios.
    Útil para dependency injection en FastAPI.
    
    Returns:
        tuple: (user_repo, empresa_repo, conciliacion_repo, movimiento_repo, match_repo, manual_repo, task_repo, deepseek_result_repo)
    """
    factory = RepositoryFactory(db)
    return (
        factory.get_user_repository(),
        factory.get_empresa_repository(),
        factory.get_conciliacion_repository(),
        factory.get_movimiento_repository(),
        factory.get_match_repository(),
        factory.get_manual_repository(),
        factory.get_task_repository(),
        factory.get_deepseek_result_repository()
    )
