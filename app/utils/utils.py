def format_currency(v):
    try:
        return f"${v:,.2f}"
    except Exception:
        return str(v)

def calcular_stats_conciliacion(movimientos, matches):
    total = len(movimientos)
    conciliados = len(matches)
    porcentaje = int((conciliados / total) * 100) if total else 0
    return {"porcentaje_conciliacion": porcentaje, "conciliados": conciliados, "total_movimientos": total}