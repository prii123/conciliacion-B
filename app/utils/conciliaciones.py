import pandas as pd
import numpy as np
import re
from datetime import datetime, timedelta
from sqlalchemy import and_
from sqlalchemy.sql import text  # Importar text para consultas SQL sin procesar
from difflib import SequenceMatcher
from ..models import Conciliacion, ConciliacionMatch, Movimiento, ConciliacionManual, ConciliacionManualBanco, ConciliacionManualAuxiliar
from ..repositories.factory import RepositoryFactory



def obtener_movimientos_por_tipo(conciliacion_id, db, fuente, tipo_es):
    """
    Obtiene movimientos filtrados por fuente (banco/auxiliar) y tipo (E/S)
    """
    factory = RepositoryFactory(db)
    movimiento_repo = factory.get_movimiento_repository()
    
    filters = {
        'tipo': fuente,
        'es': tipo_es,
        'estado_conciliacion': 'no_conciliado'
    }
    
    return movimiento_repo.get_by_conciliacion(conciliacion_id, filters)

def categorizar_por_valor(valor):
    if valor < 100000: return 'pequeño'
    elif valor < 1000000: return 'mediano'
    elif valor < 10000000: return 'grande'
    else: return 'muy_grande'

def limpiar_descripcion(descripcion):
    if not descripcion: return ""
    clean = descripcion.lower()
    clean = re.sub(r'[^\w\s]', ' ', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    stop_words = {
        'de', 'la', 'el', 'en', 'a', 'por', 'con', 'para', 'del', 'los', 'las', 'y', 'o', 'un', 'una',
        'banco', 'debito', 'credito', 'transferencia', 'pago', 'ref', 'referencia', 'mov', 'movimiento'
    }
    words = [w for w in clean.split() if w not in stop_words and len(w) > 2]
    return ' '.join(words)

def parse_fecha_segura(fecha_str):
    if not fecha_str: return pd.NaT
    fecha_clean = str(fecha_str).strip()
    formatos = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y', '%Y%m%d', '%d/%m/%y']
    for formato in formatos:
        try: return pd.to_datetime(fecha_clean, format=formato)
        except: continue
    try: return pd.to_datetime(fecha_clean, dayfirst=True)
    except: return pd.NaT

def crear_dataframe_movimientos(movimientos_query, tipo, tipo_es):
    if not movimientos_query: return pd.DataFrame()
    data = []
    for mov in movimientos_query:
        data.append({
            'id': mov.id,
            'fecha': mov.fecha,
            'fecha_parsed': parse_fecha_segura(mov.fecha),
            'descripcion': mov.descripcion.strip().lower() if mov.descripcion else '',
            'descripcion_clean': limpiar_descripcion(mov.descripcion) if mov.descripcion else '',
            'valor': float(mov.valor),
            'valor_rounded': round(float(mov.valor), 2),
            'tipo': tipo,
            'es': tipo_es
        })
    df = pd.DataFrame(data)
    if not df.empty:
        df['descripcion_words'] = df['descripcion_clean'].apply(lambda x: set(x.split()) if x else set())
        df['valor_str'] = df['valor_rounded'].astype(str)
        df['rango_valor'] = df['valor_rounded'].apply(categorizar_por_valor)
    return df

def extraer_palabras_clave(desc1, desc2):
    patron_numeros = r'\b\d{3,}\b'
    patron_codigos = r'\b[A-Z]{2,}\d+\b'
    nums1 = set(re.findall(patron_numeros, desc1.upper()))
    nums2 = set(re.findall(patron_numeros, desc2.upper()))
    codigos1 = set(re.findall(patron_codigos, desc1.upper()))
    codigos2 = set(re.findall(patron_codigos, desc2.upper()))
    return nums1.intersection(nums2).union(codigos1.intersection(codigos2))

def calcular_similitud_descripcion_mejorada(desc1_clean, desc2_clean, words1, words2):
    if not desc1_clean or not desc2_clean: return 0.0
    if not words1 or not words2: jaccard = 0.0
    else:
        interseccion = len(words1.intersection(words2))
        union = len(words1.union(words2))
        jaccard = interseccion / union if union > 0 else 0.0
    secuencia = SequenceMatcher(None, desc1_clean, desc2_clean).ratio()
    palabras_clave = extraer_palabras_clave(desc1_clean, desc2_clean)
    similitud_clave = len(palabras_clave) / max(len(words1), len(words2), 1)
    similitud_final = (jaccard * 0.4) + (secuencia * 0.4) + (similitud_clave * 0.2)
    return min(similitud_final, 1.0)

def encontrar_matches_exactos(df_banco: pd.DataFrame, df_auxiliar: pd.DataFrame) -> pd.DataFrame:
    """
    Busca matches EXACTOS por valor, día de la fecha y rango.
    
    Se considera un match exacto si coinciden:
    1. valor_rounded (valor)
    2. fecha (solo el día)
    3. rango_valor (rango)
    
    Args:
        df_banco: DataFrame con transacciones bancarias (debe tener 'fecha' como datetime).
        df_auxiliar: DataFrame auxiliar (debe tener 'fecha' como datetime).
    
    Returns:
        DataFrame con los matches exactos encontrados (relación 1:1).
    """
    if df_banco.empty or df_auxiliar.empty:
        return pd.DataFrame()

    # Copiar dataframes
    df_banco_temp = df_banco.copy()
    df_auxiliar_temp = df_auxiliar.copy()
    # print(df_banco_temp)
    # print(df_auxiliar_temp)
    # --- LÓGICA: Generar ID por valor y día de la fecha ---
    try:
        # AÑADIDO EL FIX: Conversión obligatoria a datetime para evitar errores.
        df_banco_temp['fecha'] = pd.to_datetime(df_banco_temp['fecha'], errors='coerce')
        df_auxiliar_temp['fecha'] = pd.to_datetime(df_auxiliar_temp['fecha'], errors='coerce')
        
        df_banco_temp['dia_valor_id'] = (
            df_banco_temp['valor_rounded'].astype(str) + 
            '_' + 
            df_banco_temp['fecha'].dt.day.astype(str)
        )
        df_auxiliar_temp['dia_valor_id'] = (
            df_auxiliar_temp['valor_rounded'].astype(str) + 
            '_' + 
            df_auxiliar_temp['fecha'].dt.day.astype(str)
        )
    except AttributeError:
        print("Error: Asegúrate de que la columna 'fecha' sea de tipo datetime antes de llamar a la función.")
        return pd.DataFrame()

    # El merge se realiza ÚNICAMENTE con el nuevo identificador, más 'rango_valor'
    merged = pd.merge(
        df_banco_temp, 
        df_auxiliar_temp, 
        on=['dia_valor_id', 'rango_valor'], 
        suffixes=('_banco', '_auxiliar')
    )
    # print(merged)
    if merged.empty:
        return pd.DataFrame()
    
    # Ya no se requiere calcular ni filtrar por similitud de descripción
    matches_exactos = merged.copy()
    # print(matches_exactos)
    # Eliminar duplicados para asegurar relación 1:1
    # Mantener el primer match encontrado para asegurar la unicidad
    matches_exactos = matches_exactos.drop_duplicates(subset=['id_banco'], keep='first')
    matches_exactos = matches_exactos.drop_duplicates(subset=['id_auxiliar'], keep='first')
    # print(matches_exactos[['id_banco', 'id_auxiliar', 'valor_rounded', 'es_banco']], " funcion de encontrar exactos")
    # print(matches_exactos, " funcion de encontrar exactossssssssss")
    # Devolver las columnas relevantes, sin 'similitud'
    # return matches_exactos[['id_banco', 'id_auxiliar', 'valor_rounded', 'es_banco']]
    return matches_exactos[['id_banco', 'id_auxiliar', 'valor_rounded_banco', 'es_banco']]

def encontrar_matches_valor_fecha_aproximada(df_banco: pd.DataFrame, df_auxiliar: pd.DataFrame) -> pd.DataFrame:
    """
    FUNCIÓN CORREGIDA: Busca matches por valor y rango, permitiendo diferencia de fecha <= 2 días.
    
    CORRECCIONES APLICADAS:
    1. Se eliminó la referencia a columnas inexistentes
    2. Se corrigió el manejo de fechas
    3. Se agregó cálculo de similitud de descripción
    4. Se corrigió el nombre de la variable de retorno
    """
    if df_banco.empty or df_auxiliar.empty:
        return pd.DataFrame()

    # Copiar dataframes
    df_banco_temp = df_banco.copy()
    df_auxiliar_temp = df_auxiliar.copy()
    
    print(f"Procesando {len(df_banco_temp)} banco vs {len(df_auxiliar_temp)} auxiliar para matches aproximados")
    
    try:
        # Asegurar que fecha_parsed sea datetime
        df_banco_temp['fecha_dt'] = pd.to_datetime(df_banco_temp['fecha_parsed'], format='%Y-%m-%d', errors='coerce')
        df_auxiliar_temp['fecha_dt'] = pd.to_datetime(df_auxiliar_temp['fecha_parsed'], format='%Y-%m-%d', errors='coerce')
        # print(df_auxiliar_temp)
        # print(df_banco_temp)
    except Exception as e:
        print(f"Error convirtiendo fechas: {e}")
        return pd.DataFrame()
    
        # Renombrar columnas para el merge (Necesario para el cálculo de diferencia)
    # df_banco_temp.rename(columns={'valor_rounded': 'valor_rounded_banco'}, inplace=True)
    # df_auxiliar_temp.rename(columns={'valor_rounded': 'valor_rounded_auxiliar'}, inplace=True)
    # print(df_banco_temp)
    # print(df_banco_temp.columns)
    # Merge basado en valor_rounded y rango_valor (sin fecha para permitir aproximación)
    merged = pd.merge(
        df_banco_temp, 
        df_auxiliar_temp, 
        on=['valor_rounded', 'rango_valor'], 
        suffixes=('_banco', '_auxiliar')
    )
    print(merged[['fecha_dt_banco', 'fecha_dt_auxiliar']])
    if merged.empty:
        print("No hay coincidencias por valor y rango")
        return pd.DataFrame()
    
    print(f"Encontradas {len(merged)} combinaciones por valor/rango")
    
    # Calcular la diferencia de días entre las fechas
    merged['diff_dias'] = abs(merged['fecha_dt_banco'] - merged['fecha_dt_auxiliar']).dt.days
    # print(merged)
    # print(merged.columns)
    # Filtrar por diferencia de días <= 2
    matches_fecha_aprox = merged[merged['diff_dias'] <= 2].copy()
    # print(matches_fecha_aprox, 'matchs aproximados')
    if matches_fecha_aprox.empty:
        print("No hay matches con diferencia de fecha <= 2 días")
        return pd.DataFrame()
    
    print(f"Encontrados {len(matches_fecha_aprox)} matches con diferencia <= 2 días")
    

    # if matches_finales.empty:
    #     print("No hay matches que superen el umbral de similitud del 85%")
    #     return pd.DataFrame()
    
    # Ordenar por similitud descendente
    matches_finales = matches_fecha_aprox.copy()
    # print(matches_finales, 'matchs finales 1') 
    # matches_finales = matches_finales.sort_values('similitud', ascending=False)
    
    # Eliminar duplicados para asegurar relación 1:1
    matches_finales = matches_finales.drop_duplicates(subset=['id_banco'], keep='first')
    matches_finales = matches_finales.drop_duplicates(subset=['id_auxiliar'], keep='first')
    # print(matches_finales, 'matchs finales')
    print(f"✓ Matches aproximados finales: {len(matches_finales)}")
    print(matches_finales.columns)
    # CORRECCIÓN: Devolver el DataFrame con el nombre correcto
    #matches_exactos[['id_banco', 'id_auxiliar', 'valor_rounded_banco', 'es_banco']]
    return matches_finales[['id_banco', 'id_auxiliar', 'valor_rounded', 'es_banco']]


def crear_match_y_actualizar_movimientos(mov_banco, mov_auxiliar, conciliacion_id, db, criterio, diferencia=0.0):
    """
    Crea un match entre dos movimientos y actualiza su estado
    """
    factory = RepositoryFactory(db)
    match_repo = factory.get_match_repository()
    movimiento_repo = factory.get_movimiento_repository()
    
    match_data = {
        "id_conciliacion": conciliacion_id,
        "id_movimiento_banco": mov_banco.id,
        "id_movimiento_auxiliar": mov_auxiliar.id,
        "fecha_match": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "criterio_match": criterio,
        "diferencia_valor": diferencia
    }
    
    match = match_repo.create(match_data)
    
    # Actualizar estado de los movimientos
    movimiento_repo.update(mov_banco.id, {"estado_conciliacion": "conciliado"})
    movimiento_repo.update(mov_auxiliar.id, {"estado_conciliacion": "conciliado"})
    
    return match

def verificar_conciliacion_completa(conciliacion_id, db):
    """
    Verifica si la conciliación está completa y actualiza el estado
    """
    factory = RepositoryFactory(db)
    movimiento_repo = factory.get_movimiento_repository()
    conciliacion_repo = factory.get_conciliacion_repository()
    
    movimientos_pendientes = movimiento_repo.count_by_conciliacion(
        conciliacion_id,
        {'estado_conciliacion': 'no_conciliado'}
    )
    
    print(f"Movimientos pendientes: {movimientos_pendientes}")
    
    if movimientos_pendientes == 0:
        conciliacion = conciliacion_repo.get_by_id(conciliacion_id)
        if conciliacion:
            conciliacion_repo.update(conciliacion_id, {"estado": "finalizada"})
            print("✅ Conciliación marcada como finalizada")


def procesar_matches(matches_df, criterio, conciliacion_id, db):
    """
    Procesa los matches encontrados y los guarda en base de datos
    
    Args:
        matches_df: DataFrame con los matches encontrados
        criterio: Tipo de criterio ('exacto', 'aproximado', etc.)
        conciliacion_id: ID de la conciliación
        db: Sesión de base de datos
    """
    factory = RepositoryFactory(db)
    movimiento_repo = factory.get_movimiento_repository()
    
    matches_creados = []
    
    for _, match_row in matches_df.iterrows():
        # Obtener los movimientos originales
        mov_banco = movimiento_repo.get_by_id(match_row['id_banco'])
        mov_auxiliar = movimiento_repo.get_by_id(match_row['id_auxiliar'])
        
        if mov_banco and mov_auxiliar:
            # Determinar la diferencia según el tipo de match
            if 'diferencia_dias' in match_row:
                diferencia = match_row['diferencia_dias']
            elif 'similitud' in match_row:
                diferencia = 1.0 - match_row['similitud']  # Convertir similitud a diferencia
            else:
                diferencia = 0.0
            
            # Crear el match usando la función de repositorio
            match_obj = crear_match_y_actualizar_movimientos(
                mov_banco, 
                mov_auxiliar, 
                conciliacion_id, 
                db, 
                criterio, 
                diferencia
            )
            
            matches_creados.append(match_obj)
    
    return matches_creados

def procesar_conciliacion_por_tipo(df_banco, df_auxiliar, tipo_es, conciliacion_id, db):
    # print(df_banco)
    # print(df_auxiliar)
    """
    Procesa la conciliación para un tipo específico (E o S)
    """
    stats_tipo = {
        'matches_exactos': 0,
        'matches_aproximados': 0,
        'matches_valor_descripcion': 0
    }
    
    if df_banco.empty or df_auxiliar.empty:
        print(f"No hay suficientes movimientos tipo {tipo_es} para conciliar")
        return stats_tipo
    
    print(f"Conciliando {len(df_banco)} movimientos banco vs {len(df_auxiliar)} auxiliar (tipo {tipo_es})")
    
    # ESTRATEGIA 1: Match exacto (valor + fecha + descripción similar)
    matches_exactos = encontrar_matches_exactos(df_banco, df_auxiliar)
    # print(matches_exactos, "en funcion principal llamando a matche exactos")
    if not matches_exactos.empty:
        procesar_matches(matches_exactos, f'exacto_{tipo_es}', conciliacion_id, db)
        stats_tipo['matches_exactos'] = len(matches_exactos)
        print(f"✓ Matches exactos ({tipo_es}): {len(matches_exactos)}")
        # print(df_banco)
        # Remover los matches encontrados
        df_banco = df_banco[~df_banco['id'].isin(matches_exactos['id_banco'])]
        df_auxiliar = df_auxiliar[~df_auxiliar['id'].isin(matches_exactos['id_auxiliar'])]
        # print(df_banco)

    # ESTRATEGIA 2: Match por valor exacto y fecha cercana
    if not df_banco.empty and not df_auxiliar.empty:
        matches_aproximados = encontrar_matches_valor_fecha_aproximada(df_banco, df_auxiliar)
        print(matches_aproximados, "estrategia 2 encontrat matches valor fecha aproximadaaaaaaaa")
        if not matches_aproximados.empty:
            procesar_matches(matches_aproximados, f'aproximado_{tipo_es}', conciliacion_id, db)
            stats_tipo['matches_aproximados'] = len(matches_aproximados)
            print(f"✓ Matches aproximados ({tipo_es}): {len(matches_aproximados)}")

            # --- CORRECCIÓN APLICADA AQUÍ: Remover matches de la Estrategia 3 ---
            df_banco = df_banco[~df_banco['id'].isin(matches_aproximados['id_banco'])]
            df_auxiliar = df_auxiliar[~df_auxiliar['id'].isin(matches_aproximados['id_auxiliar'])]
            # -------------------------------------------------------------------
            
    return stats_tipo

def realizar_conciliacion_automatica(conciliacion_id, db):
    # print(conciliacion_id, "id en funcion de conciliacion automatica")
    # El resto de la función se mantiene igual, ya que solo llama a la función corregida.
    movimientos_banco_entradas = obtener_movimientos_por_tipo(conciliacion_id, db, 'banco', 'E')
    movimientos_banco_salidas = obtener_movimientos_por_tipo(conciliacion_id, db, 'banco', 'S')
    movimientos_auxiliar_entradas = obtener_movimientos_por_tipo(conciliacion_id, db, 'auxiliar', 'E')
    movimientos_auxiliar_salidas = obtener_movimientos_por_tipo(conciliacion_id, db, 'auxiliar', 'S')
    
    df_banco_e = crear_dataframe_movimientos(movimientos_banco_entradas, 'banco', 'E')
    df_banco_s = crear_dataframe_movimientos(movimientos_banco_salidas, 'banco', 'S')
    df_auxiliar_e = crear_dataframe_movimientos(movimientos_auxiliar_entradas, 'auxiliar', 'E')
    df_auxiliar_s = crear_dataframe_movimientos(movimientos_auxiliar_salidas, 'auxiliar', 'S')
    
    stats = {
        'matches_exactos_entradas': 0, 'matches_exactos_salidas': 0, 'matches_aproximados_entradas': 0, 
        'matches_aproximados_salidas': 0, 'matches_valor_descripcion_entradas': 0, 'matches_valor_descripcion_salidas': 0, 
        'movimientos_banco_entradas_procesados': len(df_banco_e), 'movimientos_banco_salidas_procesados': len(df_banco_s), 
        'movimientos_auxiliar_entradas_procesados': len(df_auxiliar_e), 'movimientos_auxiliar_salidas_procesados': len(df_auxiliar_s), 
        'movimientos_banco_conciliados': 0, 'movimientos_auxiliar_conciliados': 0, 'total_matches': 0
    }
    
    print("Procesando conciliación de ENTRADAS...")
    # print(df_banco_e)
    # print(df_auxiliar_e)
    stats_entradas = procesar_conciliacion_por_tipo(df_banco_e, df_auxiliar_e, 'E', conciliacion_id, db)
    # print(stats_entradas)
    print("Procesando conciliación de SALIDAS...")
    stats_salidas = procesar_conciliacion_por_tipo(df_banco_s, df_auxiliar_s, 'S', conciliacion_id, db)
    
    stats['matches_exactos_entradas'] = stats_entradas['matches_exactos']
    stats['matches_exactos_salidas'] = stats_salidas['matches_exactos']
    stats['matches_aproximados_entradas'] = stats_entradas['matches_aproximados']
    stats['matches_aproximados_salidas'] = stats_salidas['matches_aproximados']
    stats['matches_valor_descripcion_entradas'] = stats_entradas['matches_valor_descripcion']
    stats['matches_valor_descripcion_salidas'] = stats_salidas['matches_valor_descripcion']
    
    stats['total_matches'] = (
        stats['matches_exactos_entradas'] + stats['matches_exactos_salidas'] +
        stats['matches_aproximados_entradas'] + stats['matches_aproximados_salidas'] +
        stats['matches_valor_descripcion_entradas'] + stats['matches_valor_descripcion_salidas']
    )
    
    stats['movimientos_banco_conciliados'] = stats['total_matches']
    stats['movimientos_auxiliar_conciliados'] = stats['total_matches']
    
    stats['matches_exactos'] = stats['matches_exactos_entradas'] + stats['matches_exactos_salidas']
    stats['matches_aproximados'] = stats['matches_aproximados_entradas'] + stats['matches_aproximados_salidas']
    stats['matches_valor_descripcion'] = stats['matches_valor_descripcion_entradas'] + stats['matches_valor_descripcion_salidas']
    
    # print(stats)
    verificar_conciliacion_completa(conciliacion_id, db)
    
    db.commit() # Asumiendo que el commit se maneja en el endpoint de Flask
    return stats




def crear_conciliacion_manual(conciliacion_id, id_banco, id_auxiliar, db):
    """
    Actualización: Crear una conciliación manual agrupando movimientos seleccionados.
    """
    print(f"Creando conciliación manual para conciliación ID {conciliacion_id} con bancos {id_banco} y auxiliares {id_auxiliar}")
    try:
        # Verificar conexión a la base de datos
        try:
            db.execute(text("SELECT 1"))  # Usar text para consultas SQL sin procesar
            print("Conexión a la base de datos verificada.")
        except Exception as conn_error:
            print(f"Error de conexión: {conn_error}")
            return {
                'success': False,
                'error': 'No se pudo conectar a la base de datos.'
            }

        # Normalizar inputs a listas
        bancos_ids = [int(i) for i in id_banco] if isinstance(id_banco, (list, tuple)) else [int(id_banco)]
        aux_ids = [int(i) for i in id_auxiliar] if isinstance(id_auxiliar, (list, tuple)) else [int(id_auxiliar)]

        factory = RepositoryFactory(db)
        movimiento_repo = factory.get_movimiento_repository()
        manual_repo = factory.get_manual_repository()

        # Validar movimientos usando repositorio
        movimientos_banco = []
        for banco_id in bancos_ids:
            mov = movimiento_repo.get_by_id(banco_id)
            if mov and mov.id_conciliacion == conciliacion_id and mov.tipo == 'banco':
                movimientos_banco.append(mov)

        movimientos_auxiliar = []
        for aux_id in aux_ids:
            mov = movimiento_repo.get_by_id(aux_id)
            if mov and mov.id_conciliacion == conciliacion_id and mov.tipo == 'auxiliar':
                movimientos_auxiliar.append(mov)

        print(f"Movimientos banco encontrados: {[m.id for m in movimientos_banco]}")
        print(f"Movimientos auxiliar encontrados: {[m.id for m in movimientos_auxiliar]}\n")

        # Crear registro en ConciliacionManual
        conciliacion_manual_data = {"id_conciliacion": conciliacion_id}
        conciliacion_manual = manual_repo.create(conciliacion_manual_data)

        # Asociar movimientos a la conciliación manual
        for mov in movimientos_banco:
            manual_repo.create_banco_item({
                "id_conciliacion_manual": conciliacion_manual.id,
                "id_movimiento_banco": mov.id
            })
            movimiento_repo.update(mov.id, {"estado_conciliacion": "conciliado"})
            
        for mov in movimientos_auxiliar:
            manual_repo.create_auxiliar_item({
                "id_conciliacion_manual": conciliacion_manual.id,
                "id_movimiento_auxiliar": mov.id
            })
            movimiento_repo.update(mov.id, {"estado_conciliacion": "conciliado"})

        return {
            'success': True,
            'conciliacion_manual_id': conciliacion_manual.id,
            'mensaje': f'Conciliación manual creada con éxito (ID: {conciliacion_manual.id}).'
        }

    except Exception as e:
        db.rollback()
        print(f"Error al crear conciliación manual: {str(e)}")
        return {
            'success': False,
            'error': f'Error al crear conciliación manual: {str(e)}'
        }
    


    
def eliminar_conciliacion_manual(match_id, db):
    """
    Elimina una conciliación manual y libera los movimientos
    
    Args:
        match_id: ID del match a eliminar
        db: Sesión de base de datos
    
    Returns:
        dict con el resultado de la operación
    """
    try:
        factory = RepositoryFactory(db)
        match_repo = factory.get_match_repository()
        movimiento_repo = factory.get_movimiento_repository()
        
        # Buscar el match (usando db.query por el filtro LIKE complejo)
        match = db.query(ConciliacionMatch).filter(
            and_(
                ConciliacionMatch.id == match_id,
                ConciliacionMatch.criterio_match.like('manual_%')
            )
        ).first()
        
        if not match:
            return {
                'success': False,
                'error': 'Match manual no encontrado'
            }
        
        # Obtener los movimientos
        mov_banco = movimiento_repo.get_by_id(match.id_movimiento_banco)
        mov_auxiliar = movimiento_repo.get_by_id(match.id_movimiento_auxiliar)
        
        # Restaurar estado de los movimientos
        if mov_banco:
            movimiento_repo.update(mov_banco.id, {"estado_conciliacion": "no_conciliado"})
        
        if mov_auxiliar:
            movimiento_repo.update(mov_auxiliar.id, {"estado_conciliacion": "no_conciliado"})
        
        # Eliminar el match
        match_repo.delete(match_id)
        
        return {
            'success': True,
            'mensaje': 'Conciliación manual eliminada exitosamente'
        }
        
    except Exception as e:
        db.rollback()
        return {
            'success': False,
            'error': f'Error al eliminar conciliación manual: {str(e)}'
        }

