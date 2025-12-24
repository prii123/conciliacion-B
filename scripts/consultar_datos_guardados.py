#!/usr/bin/env python3
"""
Script para consultar datos guardados de tareas fallidas y permitir recuperación.
Uso: python consultar_datos_guardados.py <task_id>
"""

import sys
import json
from sqlalchemy.orm import sessionmaker
from app.database import engine
from app.repositories.factory import RepositoryFactory
from app.models import Task, DeepSeekProcessingResult

def consultar_datos_tarea_fallida(task_id):
    """
    Consulta los datos guardados de una tarea fallida
    """
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        factory = RepositoryFactory(db)
        task_repo = factory.get_task_repository()
        deepseek_repo = factory.get_deepseek_result_repository()

        # Obtener la tarea
        task = task_repo.get_by_id(task_id)
        if not task:
            print(f"❌ Tarea {task_id} no encontrada")
            return

        print(f"📋 Información de la Tarea #{task_id}")
        print(f"   Tipo: {task.tipo}")
        print(f"   Estado: {task.estado}")
        print(f"   Descripción: {task.descripcion}")
        print(f"   Progreso: {task.progreso}%")
        print(f"   Creada: {task.created_at}")
        print(f"   Actualizada: {task.updated_at}")
        print(f"   Conciliación ID: {task.id_conciliacion}")
        print(f"   Grupos de páginas: 1 página por grupo (máxima estabilidad para DeepSeek)")
        print()

        # Obtener resultados de procesamiento
        processing_results = deepseek_repo.get_by_task(task_id)

        if not processing_results:
            print("⚠️  No hay resultados de procesamiento guardados para esta tarea")
            return

        print(f"📊 Resultados de Procesamiento ({len(processing_results)} grupos)")
        print("=" * 60)

        successful_groups = 0
        failed_groups = 0

        for result in processing_results:
            status_icon = "✅" if result.status == "saved" else "❌" if result.status == "failed" else "⏳"
            print(f"{status_icon} Grupo {result.group_number}/{result.total_groups}")
            print(f"   Páginas: {result.pages_range}")
            print(f"   Estado: {result.status}")
            print(f"   Creado: {result.created_at}")

            if result.status == "saved":
                successful_groups += 1
                try:
                    data = json.loads(result.parsed_json)
                    resumen = data.get('resumen', {})
                    movimientos = data.get('movimientos', {})

                    entradas = movimientos.get('entradas', [])
                    salidas = movimientos.get('salidas', [])

                    print("   ✅ Datos extraídos exitosamente:"                    print(f"      Saldo inicial: {resumen.get('saldo_inicial', 0):.2f}")
                    print(f"      Total entradas: {resumen.get('total_abonos', 0):.2f}")
                    print(f"      Total salidas: {resumen.get('total_cargos', 0):.2f}")
                    print(f"      Saldo final: {resumen.get('saldo_final', 0):.2f}")
                    print(f"      Movimientos: {len(entradas)} entradas, {len(salidas)} salidas")
                except json.JSONDecodeError as e:
                    print(f"   ❌ Error parseando JSON guardado: {e}")
            elif result.status == "failed":
                failed_groups += 1
                if result.error_message:
                    print(f"   ❌ Error: {result.error_message[:100]}...")
                if result.raw_response:
                    print(f"   📄 Respuesta cruda guardada ({len(result.raw_response)} caracteres)")

            print()

        print("=" * 60)
        print(f"📈 Resumen:")
        print(f"   Grupos exitosos: {successful_groups}")
        print(f"   Grupos fallidos: {failed_groups}")
        print(f"   Total grupos: {len(processing_results)}")

        if successful_groups > 0 and failed_groups > 0:
            print()
            print("💡 RECUPERACIÓN POSIBLE:")
            print("   Esta tarea puede ser recuperada porque tiene datos exitosos guardados.")
            print("   Al reintentar, se continuará desde los grupos exitosos.")
            print(f"   Endpoint: POST /api/conciliaciones/tasks/{task_id}/retry")

        elif successful_groups == 0:
            print()
            print("❌ RECUPERACIÓN DIFÍCIL:")
            print("   No hay datos exitosos guardados. Puede requerir reprocesamiento completo.")
            print("   Revisa el archivo PDF original y la configuración de DeepSeek.")

    except Exception as e:
        print(f"❌ Error consultando tarea: {e}")
    finally:
        db.close()

def listar_tareas_fallidas():
    """
    Lista todas las tareas fallidas del sistema
    """
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        factory = RepositoryFactory(db)
        task_repo = factory.get_task_repository()

        # Obtener todas las tareas fallidas (esto requiere modificar el repo para filtrar por estado)
        # Por ahora, obtenemos todas y filtramos
        all_tasks = []  # Esto debería ser task_repo.get_by_status('failed')

        # Como workaround, vamos a buscar en la BD directamente
        from sqlalchemy import text
        result = db.execute(text("SELECT id, tipo, descripcion, created_at, id_conciliacion FROM tasks WHERE estado = 'failed' ORDER BY created_at DESC"))
        failed_tasks = result.fetchall()

        if not failed_tasks:
            print("✅ No hay tareas fallidas en el sistema")
            return

        print("📋 Tareas Fallidas del Sistema")
        print("=" * 80)
        print("<10")
        print("-" * 80)

        for task in failed_tasks:
            print("<10")

        print("=" * 80)
        print(f"Total de tareas fallidas: {len(failed_tasks)}")
        print()
        print("💡 Para ver detalles de una tarea específica:")
        print("   python consultar_datos_guardados.py <task_id>")

    except Exception as e:
        print(f"❌ Error listando tareas fallidas: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("📋 Listando todas las tareas fallidas...")
        listar_tareas_fallidas()
    elif len(sys.argv) == 2:
        try:
            task_id = int(sys.argv[1])
            consultar_datos_tarea_fallida(task_id)
        except ValueError:
            print("❌ El ID de tarea debe ser un número")
    else:
        print("Uso:")
        print("  python consultar_datos_guardados.py              # Lista todas las tareas fallidas")
        print("  python consultar_datos_guardados.py <task_id>    # Muestra detalles de una tarea específica")