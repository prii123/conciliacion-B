# Guía de la Capa de Repositorios

## 📋 Resumen

Se ha implementado el **patrón Repository** para separar la capa de datos del resto de la aplicación. Esto permite cambiar fácilmente de SQLite a MySQL u otra base de datos sin modificar la lógica de negocio.

## 🏗️ Arquitectura

### Estructura de la Capa de Repositorios

```
app/
├── repositories/
│   ├── __init__.py          # Exportaciones principales
│   ├── interfaces.py        # Interfaces abstractas (contratos)
│   ├── sqlalchemy_impl.py   # Implementación para SQLAlchemy
│   └── factory.py           # Factory para crear repositorios
```

### Componentes Principales

#### 1. **Interfaces (interfaces.py)**
Define los contratos que debe cumplir cualquier implementación:

- `IUserRepository` - Gestión de usuarios
- `IEmpresaRepository` - Gestión de empresas
- `IConciliacionRepository` - Gestión de conciliaciones
- `IMovimientoRepository` - Gestión de movimientos
- `IConciliacionMatchRepository` - Gestión de matches
- `IConciliacionManualRepository` - Gestión de conciliaciones manuales

#### 2. **Implementaciones (sqlalchemy_impl.py)**
Implementación concreta usando SQLAlchemy/SQLite:

- `SQLAlchemyUserRepository`
- `SQLAlchemyEmpresaRepository`
- `SQLAlchemyConciliacionRepository`
- `SQLAlchemyMovimientoRepository`
- `SQLAlchemyConciliacionMatchRepository`
- `SQLAlchemyConciliacionManualRepository`

#### 3. **Factory (factory.py)**
Centraliza la creación de repositorios y facilita el cambio de implementación.

## 🔄 Uso de los Repositorios

### Ejemplo Básico

```python
from app.repositories.factory import RepositoryFactory
from sqlalchemy.orm import Session
from app.database import get_db

def mi_funcion(db: Session = Depends(get_db)):
    # Crear factory
    factory = RepositoryFactory(db)
    
    # Obtener repositorios
    user_repo = factory.get_user_repository()
    empresa_repo = factory.get_empresa_repository()
    
    # Usar repositorios
    usuario = user_repo.get_by_username("admin")
    empresas = empresa_repo.get_all()
```

### Operaciones Comunes

#### Crear un registro
```python
empresa_data = {
    "nit": "123456789",
    "razon_social": "Mi Empresa",
    "ciudad": "Bogotá"
}
nueva_empresa = empresa_repo.create(empresa_data)
```

#### Leer un registro
```python
empresa = empresa_repo.get_by_id(1)
empresa_por_nit = empresa_repo.get_by_nit("123456789")
todas_empresas = empresa_repo.get_all()
```

#### Actualizar un registro
```python
update_data = {"ciudad": "Medellín"}
empresa_repo.update(empresa_id=1, empresa_data=update_data)
```

#### Eliminar un registro
```python
empresa_repo.delete(empresa_id=1)
```

#### Operaciones en lote
```python
# Crear múltiples movimientos
movimientos_data = [
    {"id_conciliacion": 1, "fecha": "2024-01-01", "valor": 1000},
    {"id_conciliacion": 1, "fecha": "2024-01-02", "valor": 2000}
]
movimiento_repo.create_bulk(movimientos_data)
```

## 🔀 Cómo Cambiar a MySQL

### Opción 1: Cambiar la URL de Base de Datos (Más Simple)

Si quieres seguir usando SQLAlchemy pero con MySQL:

1. **Actualizar `app/database.py`:**
```python
# Antes
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./conciliaciones.db")

# Después
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "mysql+pymysql://usuario:contraseña@localhost/conciliaciones"
)
```

2. **Instalar dependencias de MySQL:**
```bash
pip install pymysql cryptography
```

3. **Actualizar `requirements.txt`:**
```
pymysql==1.1.0
cryptography==41.0.7
```

4. **Actualizar la configuración del engine en `app/database.py`:**
```python
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    pool_pre_ping=True,  # Para MySQL
    pool_recycle=3600    # Para MySQL
)
```

5. **Crear las tablas en MySQL:**
```python
# Ejecutar una vez
from app.database import Base, engine
Base.metadata.create_all(bind=engine)
```

### Opción 2: Implementación Personalizada (Más Control)

Si necesitas consultas SQL nativas o lógica específica de MySQL:

1. **Crear `app/repositories/mysql_impl.py`:**
```python
from typing import List, Dict, Any
from .interfaces import IEmpresaRepository
import pymysql

class MySQLEmpresaRepository(IEmpresaRepository):
    def __init__(self, connection):
        self.conn = connection
    
    def get_by_id(self, empresa_id: int):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM empresas WHERE id = %s", 
            (empresa_id,)
        )
        return cursor.fetchone()
    
    def create(self, empresa_data: Dict[str, Any]):
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO empresas (nit, razon_social, ciudad)
               VALUES (%s, %s, %s)""",
            (empresa_data['nit'], empresa_data['razon_social'], 
             empresa_data.get('ciudad'))
        )
        self.conn.commit()
        return cursor.lastrowid
    
    # ... implementar otros métodos
```

2. **Actualizar el Factory (`app/repositories/factory.py`):**
```python
class RepositoryFactory:
    def __init__(self, db, implementation: Literal['sqlalchemy', 'mysql'] = 'sqlalchemy'):
        self.db = db
        self.implementation = implementation
    
    def get_empresa_repository(self) -> IEmpresaRepository:
        if self.implementation == 'sqlalchemy':
            return SQLAlchemyEmpresaRepository(self.db)
        elif self.implementation == 'mysql':
            return MySQLEmpresaRepository(self.db)
        raise ValueError(f"Implementación desconocida: {self.implementation}")
```

3. **Usar la nueva implementación:**
```python
# En variables de entorno o configuración
DB_IMPLEMENTATION = "mysql"  # o "sqlalchemy"

# En el código
factory = RepositoryFactory(db, implementation=DB_IMPLEMENTATION)
```

## 📁 Archivos Modificados

### Rutas API
- ✅ `app/api/routes_auth.py` - Usa repositorios para usuarios
- ✅ `app/api/routes_empresas.py` - Usa repositorios para empresas
- ✅ `app/api/routes_conciliacion.py` - Usa repositorios para conciliaciones

### Utilidades
- ✅ `app/utils/auth.py` - Usa repositorios para autenticación
- ✅ `app/utils/conciliaciones.py` - Usa repositorios para lógica de conciliación

### Web Routers
- ✅ `app/web/router_conciliaciones.py` - Usa repositorios para renderizado

## 🎯 Beneficios de esta Arquitectura

1. **Separación de Responsabilidades**: La lógica de negocio no depende de la implementación de base de datos.

2. **Facilidad de Cambio**: Cambiar de SQLite a MySQL solo requiere:
   - Cambiar la URL de conexión, O
   - Crear una nueva implementación del repositorio

3. **Testeable**: Puedes crear repositorios mock para pruebas unitarias.

4. **Mantenible**: Toda la lógica de acceso a datos está centralizada.

5. **Escalable**: Fácil agregar nuevas operaciones o repositorios.

## 🔍 Ejemplo de Testing con Repositorios

```python
from unittest.mock import Mock
from app.repositories.interfaces import IEmpresaRepository

def test_crear_empresa():
    # Mock del repositorio
    mock_repo = Mock(spec=IEmpresaRepository)
    mock_repo.create.return_value = {"id": 1, "nit": "123"}
    
    # Usar el mock en tests
    nueva_empresa = mock_repo.create({"nit": "123", "razon_social": "Test"})
    
    assert nueva_empresa["id"] == 1
    mock_repo.create.assert_called_once()
```

## ⚠️ Consideraciones Importantes

1. **Transacciones**: Los repositorios SQLAlchemy hacen commit automáticamente. Si necesitas transacciones más complejas, usa el objeto `db` directamente.

2. **Relaciones**: Las relaciones de SQLAlchemy (como `empresa.conciliaciones`) siguen funcionando porque devolvemos objetos ORM.

3. **Filtros Complejos**: Para filtros muy específicos, algunos lugares todavía usan `db.query()` directamente. Esto es aceptable para casos edge.

4. **Performance**: Las operaciones en lote (`create_bulk`, `update_bulk`) están optimizadas para mejor rendimiento.

## 🚀 Próximos Pasos Recomendados

1. **Testing**: Crear tests unitarios para los repositorios
2. **Caché**: Implementar caché en repositorios frecuentemente usados
3. **Paginación**: Agregar soporte para paginación en `get_all()`
4. **Auditoría**: Agregar logging de todas las operaciones de repositorio
5. **Documentación**: Generar documentación API con Swagger/OpenAPI

## 📚 Recursos Adicionales

- [Patrón Repository](https://martinfowler.com/eaaCatalog/repository.html)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/20/orm/)
- [MySQL con Python](https://dev.mysql.com/doc/connector-python/en/)
