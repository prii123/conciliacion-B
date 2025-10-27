import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, Movimiento, Conciliacion, ConciliacionManual, ConciliacionManualBanco, ConciliacionManualAuxiliar

# Configuración de la base de datos de prueba
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependencia para la base de datos de prueba
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Crear las tablas en la base de datos de prueba
@pytest.fixture(scope="module", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

# Cliente de prueba
client = TestClient(app)

# Test para crear una conciliación manual
def test_crear_conciliacion_manual():
    # Insertar datos iniciales
    with TestingSessionLocal() as db:
        conciliacion = Conciliacion(id=1, estado="en_proceso")
        db.add(conciliacion)
        db.commit()

        movimiento_banco = Movimiento(id=1, id_conciliacion=1, tipo="banco")
        movimiento_auxiliar = Movimiento(id=2, id_conciliacion=1, tipo="auxiliar")
        db.add_all([movimiento_banco, movimiento_auxiliar])
        db.commit()

    # Realizar la solicitud
    payload = {
        "id_banco": [1],
        "id_auxiliar": [2]
    }
    response = client.post("/conciliacion/1/conciliar-manual", json=payload)

    # Verificar la respuesta
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "conciliacion_manual_id" in data

# Test para eliminar una conciliación manual
def test_eliminar_conciliacion_manual():
    # Insertar datos iniciales
    with TestingSessionLocal() as db:
        conciliacion_manual = ConciliacionManual(id=1, id_conciliacion=1)
        db.add(conciliacion_manual)
        db.commit()

        movimiento_banco = ConciliacionManualBanco(id=1, id_conciliacion_manual=1, id_movimiento_banco=1)
        movimiento_auxiliar = ConciliacionManualAuxiliar(id=1, id_conciliacion_manual=1, id_movimiento_auxiliar=2)
        db.add_all([movimiento_banco, movimiento_auxiliar])
        db.commit()

    # Realizar la solicitud
    response = client.delete("/conciliacion/match/1/eliminar")

    # Verificar la respuesta
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["mensaje"] == "Conciliación manual eliminada exitosamente"