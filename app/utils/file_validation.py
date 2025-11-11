import csv
import io
from datetime import datetime
from collections import defaultdict
from sqlalchemy.orm import Session

def validar_archivo_csv(contenido_str):
    columnas_esperadas = [
        "ID Contabilidad", "Concepto", "Fuente", "Comprobante", "Fecha Comprobante",
        "Cod. Cuenta", "Tercero", "Centro de C.", "Contrato", "Fuente Ref.",
        "Doc. Referencia", "Debito", "Credito"
    ]

    columnas_obligatorias = [
        "ID Contabilidad", "Fuente", "Comprobante", "Fecha Comprobante",
        "Cod. Cuenta", "Debito", "Credito"
    ]

    # Detectar el delimitador (',' o ';')
    delimitador = ',' if ',' in contenido_str.splitlines()[0] else ';'

    reader = csv.DictReader(io.StringIO(contenido_str), delimiter=delimitador)
    errores = []
    filas_invalidas = []
    movimientos = []

    # Validar columnas
    for columna in columnas_esperadas:
        if columna not in reader.fieldnames:
            errores.append(f"Falta la columna requerida: {columna}")

    # Validar filas por cada columna obligatoria
    for i, row in enumerate(reader):
        fila_invalida = False
        for columna in columnas_obligatorias:
            if not row.get(columna, '').strip():
                fila_invalida = True
                break

        if fila_invalida:
            filas_invalidas.append({"fila": i + 1, "contenido": row})
        else:
            movimientos.append(row)

    print(f"✓ Archivo CSV validado exitosamente: {len(movimientos)} registros encontrados")
    print(f"✗ Errores encontrados: {len(errores)}")
    print(f"✗ Filas inválidas: {len(filas_invalidas)}")

    return {
        "errores": errores,
        "filas_invalidas": filas_invalidas,
        "movimientos": len(movimientos),
        "delimitador": delimitador
    }

def validar_numeros_debito_credito(contenido_str):
    errores_conversion = []
    # Detectar el delimitador (',' o ';')
    delimitador = ',' if ',' in contenido_str.splitlines()[0] else ';'
    reader = csv.DictReader(io.StringIO(contenido_str), delimiter=delimitador)
    for i, movimiento in enumerate(reader):
        try:
            movimiento["Debito"] = float(movimiento["Debito"])
        except ValueError:
            print(f"Error de conversión en fila {i + 1}, columna 'Debito': {movimiento['Debito']}")
            errores_conversion.append({"fila": i + 1, "columna": "Debito", "valor": movimiento["Debito"]})

        try:
            movimiento["Credito"] = float(movimiento["Credito"])
        except ValueError:
            print(f"Error de conversión en fila {i + 1}, columna 'Credito': {movimiento['Credito']}")
            errores_conversion.append({"fila": i + 1, "columna": "Credito", "valor": movimiento["Credito"]})

    return errores_conversion

def formatear_datos_para_movimientos(contenido_str):
    # Formatear los datos para la tabla movimientos
    movimientos_formateados = []
    delimitador = ',' if ',' in contenido_str.splitlines()[0] else ';'
    reader = csv.DictReader(io.StringIO(contenido_str), delimiter=delimitador)

    for row in reader:
        if row["Debito"] and float(row["Debito"]) > 0:
            # Concatenar Comprobante y Concepto para la descripción
            comprobante = row.get("Comprobante", "").strip()
            concepto = row.get("Concepto", "").strip()
            descripcion = f"{comprobante} - {concepto}" if comprobante and concepto else (comprobante or concepto)
            
            movimientos_formateados.append({
                "tipo": "auxiliar",
                "valor": abs(float(row["Debito"])),
                "es": "E",
                "estado_conciliacion": "no_conciliado",
                "descripcion": descripcion,
                "fecha": row.get("Fecha Comprobante", "")
            })

        if row["Credito"] and float(row["Credito"]) > 0:
            # Concatenar Comprobante y Concepto para la descripción
            comprobante = row.get("Comprobante", "").strip()
            concepto = row.get("Concepto", "").strip()
            descripcion = f"{comprobante} - {concepto}" if comprobante and concepto else (comprobante or concepto)
            
            movimientos_formateados.append({
                "tipo": "auxiliar",
                "valor": abs(float(row["Credito"])),
                "es": "S",
                "estado_conciliacion": "no_conciliado",
                "descripcion": descripcion,
                "fecha": row.get("Fecha Comprobante", "")
            })

    # Filtrar valores iguales a 0
    movimientos_formateados = [mov for mov in movimientos_formateados if mov["valor"] != 0]
    # print(f"✓ Movimientos formateados: {len(movimientos_formateados)} registros")
    # print("✓ Primeros 3 movimientos:", movimientos_formateados[:3])

    return {
        "movimientos_formateados": movimientos_formateados
    }

def agrupar_movimientos_por_mes_y_guardar(movimientos_formateados, empresa_id, cuenta_conciliada, nombre_archivo, db: Session):
    """
    Agrupa los movimientos por mes, crea una conciliación por cada mes y guarda los movimientos asociados.
    """
    from app.models import Movimiento, Conciliacion
    
    # Agrupar movimientos por mes
    movimientos_por_mes = defaultdict(list)
    
    for movimiento in movimientos_formateados:
        try:
            # Parsear la fecha (múltiples formatos posibles)
            fecha_str = movimiento["fecha"].strip()
            fecha_obj = None
            
            # Intentar diferentes formatos de fecha
            formatos_fecha = [
                "%Y-%m-%d",      # 2025-01-07
                "%d/%m/%Y",      # 15/01/2025
                "%d-%m-%Y",      # 15-01-2025
                "%m/%d/%Y",      # 01/15/2025 (formato americano)
                "%Y/%m/%d",      # 2025/01/15
            ]
            
            for formato in formatos_fecha:
                try:
                    fecha_obj = datetime.strptime(fecha_str, formato)
                    break
                except ValueError:
                    continue
            
            if fecha_obj is None:
                print(f"No se pudo parsear la fecha '{fecha_str}' con ningún formato conocido")
                continue
            
            # Crear clave de mes-año
            mes_año = f"{fecha_obj.month:02d}-{fecha_obj.year}"
            movimientos_por_mes[mes_año].append({
                **movimiento,
                "fecha_parsed": fecha_obj.strftime("%Y-%m-%d"),
                "mes": fecha_obj.month,
                "año": fecha_obj.year
            })
        except (ValueError, AttributeError) as e:
            print(f"Error al parsear fecha '{movimiento['fecha']}': {e}")
            continue
    
    # Crear conciliaciones y guardar movimientos por mes
    conciliaciones_creadas = []
    movimientos_guardados = []
    
    for mes_año, movimientos in movimientos_por_mes.items():
        # Obtener mes y año del primer movimiento
        primer_movimiento = movimientos[0]
        mes = primer_movimiento["mes"]
        año = primer_movimiento["año"]
        
        # Crear nueva conciliación para este mes
        nueva_conciliacion = Conciliacion(
            id_empresa=empresa_id,
            fecha_proceso=datetime.now().strftime("%Y-%m-%d"),
            nombre_archivo_banco="",  # No hay archivo banco en este caso
            nombre_archivo_auxiliar=nombre_archivo,
            mes_conciliado=f"{mes:02d}",  # Formato MM
            cuenta_conciliada=cuenta_conciliada,
            año_conciliado=año
        )
        
        db.add(nueva_conciliacion)
        db.flush()  # Para obtener el ID de la conciliación
        
        conciliacion_id = nueva_conciliacion.id
        print(f"Conciliación creada #{conciliacion_id} para el mes {mes_año}")
        
        # Guardar movimientos para esta conciliación
        for movimiento in movimientos:
            nuevo_movimiento = Movimiento(
                id_conciliacion=conciliacion_id,
                fecha=movimiento["fecha_parsed"],
                descripcion=movimiento["descripcion"],
                valor=movimiento["valor"],
                es=movimiento["es"],
                tipo=movimiento["tipo"],
                estado_conciliacion=movimiento["estado_conciliacion"]
            )
            db.add(nuevo_movimiento)
            movimientos_guardados.append({
                "mes_año": mes_año,
                "conciliacion_id": conciliacion_id,
                "movimiento": movimiento
            })
        
        conciliaciones_creadas.append({
            "id": conciliacion_id,
            "mes_año": mes_año,
            "mes": mes,
            "año": año,
            "cantidad_movimientos": len(movimientos)
        })
    
    # Confirmar cambios en la base de datos
    db.commit()
    
    return {
        "conciliaciones_creadas": conciliaciones_creadas,
        "movimientos_por_mes": dict(movimientos_por_mes),
        "total_guardados": len(movimientos_guardados),
        "resumen_por_mes": {mes: len(movs) for mes, movs in movimientos_por_mes.items()}
    }



