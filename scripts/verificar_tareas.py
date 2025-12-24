#!/usr/bin/env python3
"""
Script para verificar y crear tareas de prueba para debugging
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import sessionmaker
from app.database import engine
from app.repositories.factory import RepositoryFactory
from app.models import Task, Conciliacion, User

def verificar_tareas():
    """
    Verifica las tareas existentes en la base de datos
    """
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        factory = RepositoryFactory(db)
        task_repo = factory.get_task_repository()

        # Obtener todas las tareas
        all_tasks = db.query(Task).all()
        print(f"📊 Total de tareas en BD: {len(all_tasks)}")

        for task in all_tasks:
            print(f"  - ID: {task.id}, Estado: {task.estado}, Tipo: {task.tipo}")
            print(f"    Descripción: {task.descripcion}")
            print(f"    Progreso: {task.progreso}%")
            print(f"    Creada: {task.created_at}")
            print()

        # Verificar tareas por usuario (asumiendo usuario ID 1)
        user_tasks = task_repo.get_by_user(1)
        print(f"👤 Tareas del usuario 1: {len(user_tasks)}")

        # Verificar tareas activas
        active_tasks = [t for t in user_tasks if t.estado in ['pending', 'processing']]
        print(f"🔄 Tareas activas: {len(active_tasks)}")

        # Verificar tareas fallidas
        failed_tasks = [t for t in user_tasks if t.estado == 'failed']
        print(f"❌ Tareas fallidas: {len(failed_tasks)}")

        # Si no hay tareas, crear algunas de prueba
        if len(all_tasks) == 0:
            print("⚠️ No hay tareas en la BD. Creando tareas de prueba...")
            crear_tareas_prueba(db)

    except Exception as e:
        print(f"❌ Error verificando tareas: {e}")
    finally:
        db.close()

def crear_tareas_prueba(db):
    """
    Crea algunas tareas de prueba para testing
    """
    try:
        # Verificar si hay conciliaciones
        conciliaciones = db.query(Conciliacion).limit(1).all()
        if not conciliaciones:
            print("❌ No hay conciliaciones en la BD. Crea una conciliación primero.")
            return

        conciliacion = conciliaciones[0]

        # Crear tareas de prueba
        tareas_prueba = [
            {
                "id_conciliacion": conciliacion.id,
                "tipo": "deepseek_processing",
                "estado": "pending",
                "descripcion": "Tarea pendiente de prueba",
                "progreso": 0.0
            },
            {
                "id_conciliacion": conciliacion.id,
                "tipo": "deepseek_processing",
                "estado": "processing",
                "descripcion": "Tarea en procesamiento de prueba",
                "progreso": 50.0
            },
            {
                "id_conciliacion": conciliacion.id,
                "tipo": "deepseek_processing",
                "estado": "failed",
                "descripcion": "Tarea fallida de prueba",
                "progreso": 0.0
            }
        ]

        factory = RepositoryFactory(db)
        task_repo = factory.get_task_repository()

        for tarea_data in tareas_prueba:
            task = task_repo.create(tarea_data)
            print(f"✅ Creada tarea de prueba: {task.id} - {task.estado}")

        print("🎉 Tareas de prueba creadas exitosamente!")

    except Exception as e:
        print(f"❌ Error creando tareas de prueba: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--crear":
        print("🛠️ Creando tareas de prueba...")
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        try:
            crear_tareas_prueba(db)
        finally:
            db.close()
    else:
        print("🔍 Verificando tareas existentes...")
        verificar_tareas()