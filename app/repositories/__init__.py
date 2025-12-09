"""
Capa de repositorios para abstraer el acceso a datos.
Esto permite cambiar fácilmente de SQLite a MySQL u otra base de datos.
"""
from .interfaces import (
    IUserRepository,
    IEmpresaRepository,
    IConciliacionRepository,
    IMovimientoRepository,
    IConciliacionMatchRepository,
    IConciliacionManualRepository
)
from .factory import RepositoryFactory

__all__ = [
    'IUserRepository',
    'IEmpresaRepository',
    'IConciliacionRepository',
    'IMovimientoRepository',
    'IConciliacionMatchRepository',
    'IConciliacionManualRepository',
    'RepositoryFactory'
]
