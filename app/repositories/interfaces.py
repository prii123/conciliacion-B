"""
Interfaces abstractas para los repositorios.
Define el contrato que debe cumplir cualquier implementación de repositorio.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime


class IUserRepository(ABC):
    """Repositorio para gestión de usuarios"""
    
    @abstractmethod
    def get_by_id(self, user_id: int):
        """Obtiene un usuario por ID"""
        pass
    
    @abstractmethod
    def get_by_username(self, username: str):
        """Obtiene un usuario por nombre de usuario"""
        pass
    
    @abstractmethod
    def get_by_email(self, email: str):
        """Obtiene un usuario por email"""
        pass
    
    @abstractmethod
    def create(self, user_data: Dict[str, Any]):
        """Crea un nuevo usuario"""
        pass
    
    @abstractmethod
    def update(self, user_id: int, user_data: Dict[str, Any]):
        """Actualiza un usuario"""
        pass
    
    @abstractmethod
    def delete(self, user_id: int):
        """Elimina un usuario"""
        pass


class IEmpresaRepository(ABC):
    """Repositorio para gestión de empresas"""
    
    @abstractmethod
    def get_by_id(self, empresa_id: int):
        """Obtiene una empresa por ID"""
        pass
    
    @abstractmethod
    def get_by_nit(self, nit: str):
        """Obtiene una empresa por NIT"""
        pass
    
    @abstractmethod
    def get_all(self, order_by: str = 'id', desc: bool = True) -> List:
        """Obtiene todas las empresas"""
        pass
    
    @abstractmethod
    def create(self, empresa_data: Dict[str, Any]):
        """Crea una nueva empresa"""
        pass
    
    @abstractmethod
    def update(self, empresa_id: int, empresa_data: Dict[str, Any]):
        """Actualiza una empresa"""
        pass
    
    @abstractmethod
    def delete(self, empresa_id: int):
        """Elimina una empresa"""
        pass


class IConciliacionRepository(ABC):
    """Repositorio para gestión de conciliaciones"""
    
    @abstractmethod
    def get_by_id(self, conciliacion_id: int):
        """Obtiene una conciliación por ID"""
        pass
    
    @abstractmethod
    def get_all(self, order_by: str = 'id', desc: bool = True) -> List:
        """Obtiene todas las conciliaciones"""
        pass
    
    @abstractmethod
    def get_by_empresa(self, empresa_id: int) -> List:
        """Obtiene todas las conciliaciones de una empresa"""
        pass
    
    @abstractmethod
    def create(self, conciliacion_data: Dict[str, Any]):
        """Crea una nueva conciliación"""
        pass
    
    @abstractmethod
    def update(self, conciliacion_id: int, conciliacion_data: Dict[str, Any]):
        """Actualiza una conciliación"""
        pass
    
    @abstractmethod
    def delete(self, conciliacion_id: int):
        """Elimina una conciliación"""
        pass


class IMovimientoRepository(ABC):
    """Repositorio para gestión de movimientos"""
    
    @abstractmethod
    def get_by_id(self, movimiento_id: int):
        """Obtiene un movimiento por ID"""
        pass
    
    @abstractmethod
    def get_by_conciliacion(self, conciliacion_id: int, filters: Optional[Dict[str, Any]] = None) -> List:
        """Obtiene movimientos de una conciliación con filtros opcionales"""
        pass
    
    @abstractmethod
    def count_by_conciliacion(self, conciliacion_id: int, filters: Optional[Dict[str, Any]] = None) -> int:
        """Cuenta movimientos de una conciliación con filtros opcionales"""
        pass
    
    @abstractmethod
    def create(self, movimiento_data: Dict[str, Any]):
        """Crea un nuevo movimiento"""
        pass
    
    @abstractmethod
    def create_bulk(self, movimientos_data: List[Dict[str, Any]]) -> List:
        """Crea múltiples movimientos en lote"""
        pass
    
    @abstractmethod
    def update(self, movimiento_id: int, movimiento_data: Dict[str, Any]):
        """Actualiza un movimiento"""
        pass
    
    @abstractmethod
    def update_bulk(self, movimientos_updates: List[Dict[str, Any]]):
        """Actualiza múltiples movimientos en lote"""
        pass
    
    @abstractmethod
    def delete(self, movimiento_id: int):
        """Elimina un movimiento"""
        pass


class IConciliacionMatchRepository(ABC):
    """Repositorio para gestión de matches de conciliación"""
    
    @abstractmethod
    def get_by_id(self, match_id: int):
        """Obtiene un match por ID"""
        pass
    
    @abstractmethod
    def get_by_conciliacion(self, conciliacion_id: int) -> List:
        """Obtiene todos los matches de una conciliación"""
        pass
    
    @abstractmethod
    def create(self, match_data: Dict[str, Any]):
        """Crea un nuevo match"""
        pass
    
    @abstractmethod
    def create_bulk(self, matches_data: List[Dict[str, Any]]) -> List:
        """Crea múltiples matches en lote"""
        pass
    
    @abstractmethod
    def delete(self, match_id: int):
        """Elimina un match"""
        pass
    
    @abstractmethod
    def delete_by_conciliacion(self, conciliacion_id: int):
        """Elimina todos los matches de una conciliación"""
        pass


class IConciliacionManualRepository(ABC):
    """Repositorio para gestión de conciliaciones manuales"""
    
    @abstractmethod
    def get_by_id(self, manual_id: int):
        """Obtiene una conciliación manual por ID"""
        pass
    
    @abstractmethod
    def get_by_conciliacion(self, conciliacion_id: int) -> List:
        """Obtiene todas las conciliaciones manuales de una conciliación"""
        pass
    
    @abstractmethod
    def create(self, manual_data: Dict[str, Any]):
        """Crea una nueva conciliación manual"""
        pass
    
    @abstractmethod
    def delete(self, manual_id: int):
        """Elimina una conciliación manual"""
        pass
    
    @abstractmethod
    def get_banco_items(self, manual_id: int) -> List:
        """Obtiene items del banco de una conciliación manual"""
        pass
    
    @abstractmethod
    def get_auxiliar_items(self, manual_id: int) -> List:
        """Obtiene items auxiliares de una conciliación manual"""
        pass
    
    @abstractmethod
    def create_banco_item(self, item_data: Dict[str, Any]):
        """Crea un item de banco para conciliación manual"""
        pass
    
    @abstractmethod
    def create_auxiliar_item(self, item_data: Dict[str, Any]):
        """Crea un item auxiliar para conciliación manual"""
        pass
