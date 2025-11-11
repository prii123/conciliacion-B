import pandas as pd
from app.models import Conciliacion, Movimiento


# Variable base para la URL del servidor
BASE_URL = "http://localhost"


def format_currency(v):
    try:
        return f"${v:,.2f}"
    except Exception:
        return str(v)

def calcular_stats_conciliacion(db, conciliacion_id):
    """
    Calcula totales y porcentaje de conciliación para una conciliación dada
    """
    movimientos = db.query(Movimiento).filter(
        Movimiento.id_conciliacion == conciliacion_id
    ).all()

    total_movimientos = len(movimientos)
    total_conciliados = len([m for m in movimientos if m.estado_conciliacion == 'conciliado'])
    total_no_conciliados = total_movimientos - total_conciliados
    porcentaje_conciliacion = (total_conciliados / total_movimientos * 100) if total_movimientos > 0 else 0

    return {
        'total_movimientos': total_movimientos,
        'conciliados': total_conciliados,
        'no_conciliados': total_no_conciliados,
        'porcentaje_conciliacion': porcentaje_conciliacion
    }



def validar_excel(df, nombre_archivo, tipo_archivo):
    """
    Función mejorada para validar las columnas y tipos de datos del DataFrame.
    
    Args:
        df: DataFrame a validar
        nombre_archivo: Nombre del archivo para identificación
        tipo_archivo: Tipo de archivo (BANCO, AUXILIAR o MOVIMIENTOS)
    """
    columnas_requeridas = ['fecha', 'descripcion', 'valor', 'es']
    
    # 1. Validar que el DataFrame no esté vacío
    if df.empty:
        raise ValueError(f"El archivo está vacío o no contiene datos")
    
    # 2. Validar que las columnas existan
    columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
    if columnas_faltantes:
        columnas_disponibles = list(df.columns)
        raise ValueError(
            f"Faltan las siguientes columnas requeridas: {', '.join(columnas_faltantes)}. "
            f"Columnas disponibles en el archivo: {', '.join(columnas_disponibles)}"
        )
    
    # 3. Validar que no haya filas completamente vacías
    filas_vacias = df[df[columnas_requeridas].isnull().all(axis=1)]
    if not filas_vacias.empty:
        indices_vacias = (filas_vacias.index + 2).tolist()  # +2 porque Excel cuenta desde 1 y tiene encabezados
        raise ValueError(
            f"Se encontraron filas completamente vacías en las posiciones: {indices_vacias}"
        )
    
    # 4. Validar la columna 'fecha'
    fechas_nulas = df[df['fecha'].isnull()]
    if not fechas_nulas.empty:
        filas_fechas_nulas = (fechas_nulas.index + 2).tolist()
        raise ValueError(
            f"La columna 'fecha' tiene valores vacíos en las filas: {filas_fechas_nulas}"
        )
    
    # 5. Validar la columna 'descripcion'
    descripciones_nulas = df[df['descripcion'].isnull()]
    if not descripciones_nulas.empty:
        filas_descripciones_nulas = (descripciones_nulas.index + 2).tolist()
        raise ValueError(
            f"La columna 'descripcion' tiene valores vacíos en las filas: {filas_descripciones_nulas}"
        )
    
    # 6. Validar que la columna 'valor' sea numérica
    try:
        # Crear una copia para no modificar el DataFrame original durante la validación
        valores_temp = pd.to_numeric(df['valor'], errors='coerce')
        valores_nulos = df[valores_temp.isnull()]
        
        if not valores_nulos.empty:
            filas_no_numericas = (valores_nulos.index + 2).tolist()
            valores_problematicos = df.loc[valores_nulos.index, 'valor'].tolist()
            raise ValueError(
                f"La columna 'valor' contiene valores no numéricos en las filas: {filas_no_numericas}. "
                f"Valores problemáticos: {valores_problematicos}"
            )
            
        # Validar que no haya valores cero (opcional, según las reglas de negocio)
        valores_cero = df[df['valor'] == 0]
        if not valores_cero.empty:
            filas_cero = (valores_cero.index + 2).tolist()
            print(f"Advertencia en {tipo_archivo}: Se encontraron valores cero en las filas: {filas_cero}")
            
    except Exception as e:
        raise ValueError(f"Error al validar la columna 'valor': {str(e)}")
    
    # 7. Validar la columna 'es' (Entrada/Salida)
    es_nulas = df[df['es'].isnull()]
    if not es_nulas.empty:
        filas_es_nulas = (es_nulas.index + 2).tolist()
        raise ValueError(
            f"La columna 'es' tiene valores vacíos en las filas: {filas_es_nulas}"
        )
    
    # Validar que los valores de 'es' sean solo 'E' o 'S'
    valores_es_validos = ['E', 'S', 'e', 's']  # Aceptar mayúsculas y minúsculas
    valores_es_invalidos = df[~df['es'].str.upper().isin(['E', 'S'])]
    if not valores_es_invalidos.empty:
        filas_es_invalidas = (valores_es_invalidos.index + 2).tolist()
        valores_problematicos = df.loc[valores_es_invalidos.index, 'es'].tolist()
        raise ValueError(
            f"La columna 'es' contiene valores inválidos en las filas: {filas_es_invalidas}. "
            f"Valores problemáticos: {valores_problematicos}. Solo se permiten 'E' (Entrada) o 'S' (Salida)"
        )
    
    # 8. Validar que haya al menos una fila de datos
    if len(df) == 0:
        raise ValueError("El archivo no contiene filas de datos")
    
    print(f"✓ Archivo {tipo_archivo} ({nombre_archivo}) validado exitosamente: {len(df)} registros encontrados")
    # """
    # Función mejorada para validar las columnas y tipos de datos del DataFrame.
    
    # Args:
    #     df: DataFrame a validar
    #     nombre_archivo: Nombre del archivo para identificación
    #     tipo_archivo: Tipo de archivo (BANCO o AUXILIAR)
    # """
    # columnas_requeridas = ['fecha', 'descripcion', 'valor']
    
    # # 1. Validar que el DataFrame no esté vacío
    # if df.empty:
    #     raise ValueError(f"El archivo está vacío o no contiene datos")
    
    # # 2. Validar que las columnas existan
    # columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
    # if columnas_faltantes:
    #     columnas_disponibles = list(df.columns)
    #     raise ValueError(
    #         f"Faltan las siguientes columnas requeridas: {', '.join(columnas_faltantes)}. "
    #         f"Columnas disponibles en el archivo: {', '.join(columnas_disponibles)}"
    #     )
    
    # # 3. Validar que no haya filas completamente vacías
    # filas_vacias = df[df[columnas_requeridas].isnull().all(axis=1)]
    # if not filas_vacias.empty:
    #     indices_vacias = (filas_vacias.index + 2).tolist()  # +2 porque Excel cuenta desde 1 y tiene encabezados
    #     raise ValueError(
    #         f"Se encontraron filas completamente vacías en las posiciones: {indices_vacias}"
    #     )
    
    # # 4. Validar la columna 'fecha'
    # fechas_nulas = df[df['fecha'].isnull()]
    # if not fechas_nulas.empty:
    #     filas_fechas_nulas = (fechas_nulas.index + 2).tolist()
    #     raise ValueError(
    #         f"La columna 'fecha' tiene valores vacíos en las filas: {filas_fechas_nulas}"
    #     )
    
    # # 5. Validar la columna 'descripcion'
    # descripciones_nulas = df[df['descripcion'].isnull()]
    # if not descripciones_nulas.empty:
    #     filas_descripciones_nulas = (descripciones_nulas.index + 2).tolist()
    #     raise ValueError(
    #         f"La columna 'descripcion' tiene valores vacíos en las filas: {filas_descripciones_nulas}"
    #     )
    
    # # 6. Validar que la columna 'valor' sea numérica
    # try:
    #     # Crear una copia para no modificar el DataFrame original durante la validación
    #     valores_temp = pd.to_numeric(df['valor'], errors='coerce')
    #     valores_nulos = df[valores_temp.isnull()]
        
    #     if not valores_nulos.empty:
    #         filas_no_numericas = (valores_nulos.index + 2).tolist()
    #         valores_problematicos = df.loc[valores_nulos.index, 'valor'].tolist()
    #         raise ValueError(
    #             f"La columna 'valor' contiene valores no numéricos en las filas: {filas_no_numericas}. "
    #             f"Valores problemáticos: {valores_problematicos}"
    #         )
            
    #     # Validar que no haya valores cero (opcional, según las reglas de negocio)
    #     valores_cero = df[df['valor'] == 0]
    #     if not valores_cero.empty:
    #         filas_cero = (valores_cero.index + 2).tolist()
    #         print(f"Advertencia en {tipo_archivo}: Se encontraron valores cero en las filas: {filas_cero}")
            
    # except Exception as e:
    #     raise ValueError(f"Error al validar la columna 'valor': {str(e)}")
    
    # # 7. Validar que haya al menos una fila de datos
    # if len(df) == 0:
    #     raise ValueError("El archivo no contiene filas de datos")
    
    # print(f"✓ Archivo {tipo_archivo} ({nombre_archivo}) validado exitosamente: {len(df)} registros encontrados")



def obtener_estadisticas_empresa(db, empresa_id):
    """
    Obtiene estadísticas generales de una empresa
    
    Returns:
        dict con total de conciliaciones, finalizadas, en proceso, etc.
    """
    conciliaciones = db.query(Conciliacion).filter(
        Conciliacion.id_empresa == empresa_id
    ).all()
    
    total_conciliaciones = len(conciliaciones)
    finalizadas = len([c for c in conciliaciones if c.estado == 'finalizada'])
    en_proceso = len([c for c in conciliaciones if c.estado == 'en_proceso'])
    
    # Calcular promedio de avance
    if total_conciliaciones > 0:
        promedios = []
        for c in conciliaciones:
            stats = calcular_stats_conciliacion(db, c.id)
            promedios.append(stats['porcentaje_conciliacion'])
        promedio_avance = sum(promedios) / len(promedios)
    else:
        promedio_avance = 0
    
    return {
        'total_conciliaciones': total_conciliaciones,
        'finalizadas': finalizadas,
        'en_proceso': en_proceso,
        'promedio_avance': round(promedio_avance, 2)
    }

def verificar_duplicado_conciliacion(db, id_empresa, mes, año, cuenta):
    """
    Verifica si ya existe una conciliación para la misma empresa, mes, año y cuenta
    
    Returns:
        bool: True si existe, False si no
    """
    existe = db.query(Conciliacion).filter(
        Conciliacion.id_empresa == id_empresa,
        Conciliacion.mes_conciliado == mes,
        Conciliacion.año_conciliado == año,
        Conciliacion.cuenta_conciliada == cuenta
    ).first()
    
    return existe is not None


