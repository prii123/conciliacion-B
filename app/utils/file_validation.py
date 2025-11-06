import csv
import io

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
            movimientos_formateados.append({
                "tipo": "auxiliar",
                "valor": abs(float(row["Debito"])),
                "es": "E",
                "estado_conciliacion": "no_conciliado",
                "descripcion": row.get("Concepto", ""),
                "fecha": row.get("Fecha Comprobante", "")
            })

        if row["Credito"] and float(row["Credito"]) > 0:
            movimientos_formateados.append({
                "tipo": "auxiliar",
                "valor": abs(float(row["Credito"])),
                "es": "S",
                "estado_conciliacion": "no_conciliado",
                "descripcion": row.get("Concepto", ""),
                "fecha": row.get("Fecha Comprobante", "")
            })

    # Filtrar valores iguales a 0
    movimientos_formateados = [mov for mov in movimientos_formateados if mov["valor"] != 0]
    print(f"✓ Movimientos formateados: {len(movimientos_formateados)} registros")
    print("✓ Primeros 3 movimientos:", movimientos_formateados[:3])

    return {
        "movimientos_formateados": movimientos_formateados
    }



