from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from .database import Base
from datetime import date

class Empresa(Base):
    __tablename__ = "empresas"
    id = Column(Integer, primary_key=True, index=True)
    nit = Column(String(50), unique=True, nullable=False)
    razon_social = Column(String(200), nullable=False)
    nombre_comercial = Column(String(200), nullable=True)
    ciudad = Column(String(100), nullable=True)
    estado = Column(String(50), default="activa")

    conciliaciones = relationship("Conciliacion", back_populates="empresa")

class Conciliacion(Base):
    __tablename__ = "conciliaciones"
    id = Column(Integer, primary_key=True, index=True)
    id_empresa = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    mes_conciliado = Column(String(50))
    anio_conciliado = Column(Integer)
    cuenta_conciliada = Column(String(200))
    fecha_proceso = Column(Date, default=date.today)
    estado = Column(String(50), default="en_proceso")

    empresa = relationship("Empresa", back_populates="conciliaciones")
    movimientos = relationship("Movimiento", back_populates="conciliacion", cascade="all, delete-orphan")
    matches = relationship("ConciliacionMatch", back_populates="conciliacion", cascade="all, delete-orphan")

class Movimiento(Base):
    __tablename__ = "movimientos"
    id = Column(Integer, primary_key=True, index=True)
    conciliacion_id = Column(Integer, ForeignKey("conciliaciones.id"), nullable=False)
    fecha = Column(String(50))
    descripcion = Column(Text)
    valor = Column(Float)
    es = Column(String(1))  # 'E' entrada, 'S' salida
    origen = Column(String(20))  # 'banco' o 'auxiliar'
    conciliado = Column(String(5), default="no")

    conciliacion = relationship("Conciliacion", back_populates="movimientos")

    def to_dict(self):
        return {
            "id": self.id,
            "conciliacion_id": self.conciliacion_id,
            "fecha": self.fecha,
            "descripcion": self.descripcion,
            "valor": self.valor,
            "es": self.es,
            "origen": self.origen,
            "conciliado": self.conciliado,
        }

class ConciliacionMatch(Base):
    __tablename__ = "conciliacion_matches"
    id = Column(Integer, primary_key=True, index=True)
    conciliacion_id = Column(Integer, ForeignKey("conciliaciones.id"), nullable=False)
    movimiento_banco_id = Column(Integer, nullable=True)
    movimiento_auxiliar_id = Column(Integer, nullable=True)
    diferencia = Column(Float, default=0.0)

    conciliacion = relationship("Conciliacion", back_populates="matches")