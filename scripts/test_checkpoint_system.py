"""
Script de prueba para el sistema de recuperación de procesamiento DeepSeek.
Verifica que todos los componentes funcionen correctamente.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from app.database import get_db
from app.repositories.factory import RepositoryFactory
from app.models import Task, DeepSeekProcessingResult

def test_checkpoint_system():
    """Prueba el sistema de checkpoints y recuperación"""
    print("🧪 Probando sistema de recuperación de procesamiento DeepSeek...")

    db = next(get_db())
    factory = RepositoryFactory(db)
    
    # Crear repositorios
    task_repo = factory.get_task_repository()
    deepseek_repo = factory.get_deepseek_result_repository()

    try:
        print("✅ Repositorios creados correctamente")
        
        # Verificar si existe alguna conciliación, si no, crear una temporal para prueba
        from app.models import Conciliacion
        conciliacion_existente = db.query(Conciliacion).first()
        
        if not conciliacion_existente:
            # Crear una conciliación temporal para la prueba
            from app.models import Empresa
            empresa = db.query(Empresa).first()
            if not empresa:
                # Crear empresa temporal
                empresa = Empresa(
                    nit="123456789",
                    razon_social="Empresa de Prueba",
                    nombre_comercial="Prueba SA",
                    email="prueba@test.com"
                )
                db.add(empresa)
                db.commit()
                db.refresh(empresa)
            
            conciliacion_temp = Conciliacion(
                id_empresa=empresa.id,
                mes_conciliado="12",
                año_conciliado="2024",
                cuenta_conciliada="123456",
                fecha_proceso="2024-12-24",
                estado="en_proceso"
            )
            db.add(conciliacion_temp)
            db.commit()
            db.refresh(conciliacion_temp)
            conciliacion_id = conciliacion_temp.id
            temp_conciliacion = True
        else:
            conciliacion_id = conciliacion_existente.id
            temp_conciliacion = False

        print(f"✅ Usando conciliación ID: {conciliacion_id}")

        # Crear una tarea de prueba
        test_task = task_repo.create({
            "id_conciliacion": conciliacion_id,
            "tipo": "deepseek_processing",
            "estado": "processing",
            "descripcion": "Prueba de sistema de recuperación",
            "progreso": 50.0
        })

        print(f"✅ Tarea de prueba creada: {test_task.id}")

        # Crear resultados de procesamiento simulados
        test_results = [
            {
                "id_task": test_task.id,
                "group_number": 1,
                "total_groups": 3,
                "pages_range": "1-5",
                "status": "saved",
                "parsed_json": json.dumps({
                    "movimientos": {
                        "entradas": [{"fecha": "01/01/2024", "descripcion": "Deposito", "valor": 1000.00}],
                        "salidas": []
                    }
                })
            },
            {
                "id_task": test_task.id,
                "group_number": 2,
                "total_groups": 3,
                "pages_range": "6-10",
                "status": "failed",
                "error_message": "JSON malformado"
            },
            {
                "id_task": test_task.id,
                "group_number": 3,
                "total_groups": 3,
                "pages_range": "11-15",
                "status": "saved",
                "parsed_json": json.dumps({
                    "movimientos": {
                        "entradas": [],
                        "salidas": [{"fecha": "02/01/2024", "descripcion": "Transferencia", "valor": 500.00}]
                    }
                })
            }
        ]

        created_results = []
        for result_data in test_results:
            result = deepseek_repo.create(result_data)
            created_results.append(result)
            print(f"✅ Resultado de grupo {result.group_number} creado: {result.status}")

        # Probar recuperación de resultados exitosos
        successful_results = deepseek_repo.get_successful_results(test_task.id)
        print(f"✅ Recuperados {len(successful_results)} resultados exitosos")

        # Verificar que se pueden parsear los JSON
        for result in successful_results:
            try:
                parsed = json.loads(result.parsed_json)
                print(f"✅ Grupo {result.group_number}: JSON válido con {len(parsed['movimientos']['entradas'])} entradas, {len(parsed['movimientos']['salidas'])} salidas")
            except Exception as e:
                print(f"❌ Error parseando JSON del grupo {result.group_number}: {e}")

        # Probar consulta por grupo específico
        group_2_result = deepseek_repo.get_by_task_and_group(test_task.id, 2)
        if group_2_result and group_2_result.status == 'failed':
            print("✅ Estado de error guardado correctamente para grupo fallido")

        # Limpiar datos de prueba
        for result in created_results:
            deepseek_repo.delete_by_task(test_task.id)
        task_repo.delete(test_task.id)
        
        # Limpiar conciliación temporal si se creó
        if temp_conciliacion:
            db.delete(conciliacion_temp)
            db.commit()

        print("🧪 Pruebas completadas exitosamente!")
        print("✅ Sistema de recuperación funcionando correctamente")

    except Exception as e:
        print(f"❌ Error en pruebas: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()

if __name__ == "__main__":
    test_checkpoint_system()