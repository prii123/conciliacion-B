from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from .database import Base
from datetime import date


class Empresa(Base):
    """
    Modelo para almacenar las empresas del sistema
    """
    __tablename__ = 'empresas'
    
    id = Column(Integer, primary_key=True)
    nit = Column(String, unique=True, nullable=False)  # NIT de la empresa
    razon_social = Column(String, nullable=False)      # Nombre legal
    nombre_comercial = Column(String)                  # Nombre comercial (opcional)
    email = Column(String)
    telefono = Column(String)
    direccion = Column(String)
    ciudad = Column(String)
    estado = Column(String, default='activa')          # 'activa' o 'inactiva'
    fecha_creacion = Column(String)
    
    # Relación uno-a-muchos con Conciliaciones
    conciliaciones = relationship("Conciliacion", back_populates="empresa")

class Conciliacion(Base):
    __tablename__ = 'conciliaciones'
    id = Column(Integer, primary_key=True)
    id_empresa = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    fecha_proceso = Column(String)
    nombre_archivo_banco = Column(String)
    nombre_archivo_auxiliar = Column(String)
    estado = Column(String, default='en_proceso')
    mes_conciliado = Column(String)
    cuenta_conciliada = Column(String)
    año_conciliado = Column(String)

    empresa = relationship("Empresa", back_populates="conciliaciones")
    movimientos = relationship("Movimiento", back_populates="conciliacion", cascade="all, delete-orphan")
    matches = relationship("ConciliacionMatch", back_populates="conciliacion", cascade="all, delete-orphan")

class Movimiento(Base):
    __tablename__ = 'movimientos'
    id = Column(Integer, primary_key=True)
    id_conciliacion = Column(Integer, ForeignKey('conciliaciones.id'))
    fecha = Column(String)  # Puedes usar Date para fechas
    descripcion = Column(String)
    valor = Column(Float)
    tipo = Column(String)  # 'banco' o 'auxiliar'
    es = Column(String)
    estado_conciliacion = Column(String, default='no_conciliado')

    # Relación con la tabla Conciliacion
    conciliacion = relationship("Conciliacion", back_populates="movimientos")

    def to_dict(self):
        return {
            "id": self.id,
            "id_conciliacion": self.id_conciliacion,
            "fecha": self.fecha,
            "descripcion": self.descripcion,
            "valor": self.valor,
            "es": self.es,
            "tipo": self.tipo,  # Usar 'tipo' en lugar de 'origen'
            "estado_conciliacion": self.estado_conciliacion,
        }

class ConciliacionMatch(Base):
    __tablename__ = 'conciliacion_matches'
    id = Column(Integer, primary_key=True)
    id_conciliacion = Column(Integer, ForeignKey('conciliaciones.id'))
    id_movimiento_banco = Column(Integer, ForeignKey('movimientos.id'))
    id_movimiento_auxiliar = Column(Integer, ForeignKey('movimientos.id'))
    fecha_match = Column(String)
    criterio_match = Column(String)  # 'exacto', 'aproximado', 'manual'
    diferencia_valor = Column(Float, default=0.0)  # Para matches aproximados
    
    # Relaciones
    conciliacion = relationship("Conciliacion")
    movimiento_banco = relationship("Movimiento", foreign_keys=[id_movimiento_banco])
    movimiento_auxiliar = relationship("Movimiento", foreign_keys=[id_movimiento_auxiliar])