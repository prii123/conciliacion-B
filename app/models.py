from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from .database import Base
from datetime import date, datetime


class User(Base):
    """
    Modelo para almacenar usuarios del sistema
    """
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(String, default='usuario')  # 'administrador' o 'usuario'
    created_at = Column(String)


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
    id_usuario_creador = Column(Integer, ForeignKey("users.id"), nullable=True)  # Usuario que creó la empresa
    
    # Relación uno-a-muchos con Conciliaciones
    conciliaciones = relationship("Conciliacion", back_populates="empresa")

class Conciliacion(Base):
    __tablename__ = 'conciliaciones'
    id = Column(Integer, primary_key=True)
    id_empresa = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    id_usuario_creador = Column(Integer, ForeignKey("users.id"), nullable=True)  # Usuario que creó la conciliación
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

    
#======================================INTERMEDIOS PARA CONCILIACION MANUALES ==========================
class ConciliacionManual(Base):
    __tablename__ = 'conciliaciones_manuales'
    id = Column(Integer, primary_key=True)
    id_conciliacion = Column(Integer, ForeignKey('conciliaciones.id'), nullable=False)
    fecha_creacion = Column(String, default=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    # Relaciones con movimientos
    movimientos_banco = relationship("Movimiento", secondary="conciliacion_manual_banco")
    movimientos_auxiliar = relationship("Movimiento", secondary="conciliacion_manual_auxiliar")

class ConciliacionManualBanco(Base):
    __tablename__ = 'conciliacion_manual_banco'
    id = Column(Integer, primary_key=True)
    id_conciliacion_manual = Column(Integer, ForeignKey('conciliaciones_manuales.id'), nullable=False)
    id_movimiento_banco = Column(Integer, ForeignKey('movimientos.id'), nullable=False)

class ConciliacionManualAuxiliar(Base):
    __tablename__ = 'conciliacion_manual_auxiliar'
    id = Column(Integer, primary_key=True)
    id_conciliacion_manual = Column(Integer, ForeignKey('conciliaciones_manuales.id'), nullable=False)
    id_movimiento_auxiliar = Column(Integer, ForeignKey('movimientos.id'), nullable=False)


class DeepSeekProcessingResult(Base):
    """
    Modelo para guardar resultados parciales del procesamiento de DeepSeek.
    Permite recuperación en caso de fallos durante procesamiento de PDFs grandes.
    """
    __tablename__ = 'deepseek_processing_results'
    
    id = Column(Integer, primary_key=True, index=True)
    id_task = Column(Integer, ForeignKey('tasks.id'), nullable=False)
    group_number = Column(Integer, nullable=False)  # Número del grupo de páginas procesado
    total_groups = Column(Integer, nullable=False)  # Total de grupos
    pages_range = Column(String, nullable=False)  # Rango de páginas procesadas (ej: "1-5")
    raw_response = Column(Text)  # Respuesta cruda de DeepSeek
    parsed_json = Column(Text)  # JSON parseado y validado
    status = Column(String, default='pending')  # 'pending', 'processed', 'failed', 'saved'
    error_message = Column(Text)  # Mensaje de error si falló
    created_at = Column(String, default=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    updated_at = Column(String, default=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    # Relación con task
    task = relationship("Task")


class Task(Base):
    """
    Modelo para almacenar tareas pendientes del sistema, como procesamiento de DeepSeek
    """
    __tablename__ = 'tasks'
    
    id = Column(Integer, primary_key=True, index=True)
    id_conciliacion = Column(Integer, ForeignKey('conciliaciones.id'), nullable=False)
    tipo = Column(String, nullable=False)  # 'deepseek_processing', etc.
    estado = Column(String, default='pending')  # 'pending', 'processing', 'completed', 'failed'
    descripcion = Column(Text)
    progreso = Column(Float, default=0.0)  # Porcentaje de progreso (0-100)
    created_at = Column(String, default=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    updated_at = Column(String, default=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    # Relación con conciliación
    conciliacion = relationship("Conciliacion")
    
    # Relación con resultados de procesamiento
    processing_results = relationship("DeepSeekProcessingResult", back_populates="task", cascade="all, delete-orphan")