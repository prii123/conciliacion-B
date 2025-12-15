import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./conciliaciones.db")  DATABASE_URL = "postgresql://usuario:contraseña@localhost:5432/tu_basededatos"
# DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://usuario:contraseña@localhost:5432/tu_basededatos")  

    # Cambia los valores de usuario, contraseña, host, puerto y base de datos según tu configuración
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://printsvallejos:04373847Vallejos@64.23.180.56:5432/conciliaciones"
)
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()