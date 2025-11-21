from fpdf import FPDF
import os
import time
import threading

def generar_pdf_informe(conciliacion, conciliados, pendientes):
    print("Generando PDF...")

    # Obtener información de la empresa
    empresa_nombre = conciliacion.empresa.razon_social if conciliacion.empresa and conciliacion.empresa.razon_social else (
        conciliacion.empresa.nombre_comercial if conciliacion.empresa else 'Empresa no especificada'
    )
    
    periodo = f"{conciliacion.mes_conciliado} {conciliacion.año_conciliado}" if conciliacion.mes_conciliado and conciliacion.año_conciliado else "Período no especificado"
    cuenta = conciliacion.cuenta_conciliada if conciliacion.cuenta_conciliada else "Cuenta no especificada"

    # Separar los movimientos conciliados y pendientes por tipo
    conciliados_bancos = [mov for mov in conciliados if mov.tipo == "banco"]
    conciliados_auxiliares = [mov for mov in conciliados if mov.tipo == "auxiliar"]
    pendientes_bancos = [mov for mov in pendientes if mov.tipo == "banco"]
    pendientes_auxiliares = [mov for mov in pendientes if mov.tipo == "auxiliar"]

    # CORRECCIÓN: Separar por mov.es en lugar de mov.valor
    # Separar los movimientos pendientes y conciliados en entradas (E) y salidas (S)
    pendientes_auxiliares_entradas = [mov for mov in pendientes_auxiliares if mov.es == "E"]
    pendientes_auxiliares_salidas = [mov for mov in pendientes_auxiliares if mov.es == "S"]
    conciliados_auxiliares_entradas = [mov for mov in conciliados_auxiliares if mov.es == "E"]
    conciliados_auxiliares_salidas = [mov for mov in conciliados_auxiliares if mov.es == "S"]

    pendientes_bancos_entradas = [mov for mov in pendientes_bancos if mov.es == "E"]
    pendientes_bancos_salidas = [mov for mov in pendientes_bancos if mov.es == "S"]
    conciliados_bancos_entradas = [mov for mov in conciliados_bancos if mov.es == "E"]
    conciliados_bancos_salidas = [mov for mov in conciliados_bancos if mov.es == "S"]

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Times", size=16, style="B")  # Título más grande y en negrita

    # Encabezado principal con información completa
    pdf.cell(200, 12, txt=f"Informe de Conciliación #{conciliacion.id}", ln=True, align="C")
    pdf.ln(1)
    
    # Información de la empresa y período
    pdf.set_font("Times", size=12, style="B")
    pdf.cell(200, 8, txt=f"{empresa_nombre}", ln=True, align="C")
    pdf.cell(200, 8, txt=f"Período: {periodo}", ln=True, align="C")
    pdf.cell(200, 8, txt=f"Cuenta: {cuenta}", ln=True, align="C")
    pdf.ln(5)

    # Estadísticas de movimientos conciliados y pendientes
    pdf.set_font("Times", size=10)
    pdf.cell(200, 10, txt="Las siguientes secciones muestran un resumen de los movimientos que están pendientes por conciliar:", ln=True, align="L")
    pdf.ln(5)

    # Estadísticas totales
    pdf.set_font("Times", size=10)
    pdf.cell(200, 10, txt="Estadísticas Totales", ln=True, align="L")
    pdf.ln(1)

    # Tabla de estadísticas totales
    pdf.set_font("Times", size=9)
    pdf.cell(45, 5, txt="Categoría", border=1, align="C")
    pdf.cell(45, 5, txt="Total", border=1, align="C")
    pdf.cell(45, 5, txt="Pendientes", border=1, align="C")
    pdf.cell(45, 5, txt="Conciliadas", border=1, align="C")
    pdf.ln(5)

    # Auxiliares - Entradas
    total_auxiliares_entradas = sum(mov.valor for mov in conciliados_auxiliares_entradas) + sum(mov.valor for mov in pendientes_auxiliares_entradas)
    pendientes_auxiliares_entradas_total = sum(mov.valor for mov in pendientes_auxiliares_entradas)
    conciliados_auxiliares_entradas_total = sum(mov.valor for mov in conciliados_auxiliares_entradas)
    pdf.cell(45, 5, txt="Entradas Auxiliares", border=1, align="C")
    pdf.cell(45, 5, txt=f"{total_auxiliares_entradas:,.2f}", border=1, align="C")
    pdf.cell(45, 5, txt=f"{pendientes_auxiliares_entradas_total:,.2f}", border=1, align="C")
    pdf.cell(45, 5, txt=f"{conciliados_auxiliares_entradas_total:,.2f}", border=1, align="C")
    pdf.ln(5)

    # Auxiliares - Salidas
    total_auxiliares_salidas = sum(mov.valor for mov in conciliados_auxiliares_salidas) + sum(mov.valor for mov in pendientes_auxiliares_salidas)
    pendientes_auxiliares_salidas_total = sum(mov.valor for mov in pendientes_auxiliares_salidas)
    conciliados_auxiliares_salidas_total = sum(mov.valor for mov in conciliados_auxiliares_salidas)
    pdf.cell(45, 5, txt="Salidas Auxiliares", border=1, align="C")
    pdf.cell(45, 5, txt=f"{total_auxiliares_salidas:,.2f}", border=1, align="C")
    pdf.cell(45, 5, txt=f"{pendientes_auxiliares_salidas_total:,.2f}", border=1, align="C")
    pdf.cell(45, 5, txt=f"{conciliados_auxiliares_salidas_total:,.2f}", border=1, align="C")
    pdf.ln(5)

    # Bancos - Entradas
    total_bancos_entradas = sum(mov.valor for mov in conciliados_bancos_entradas) + sum(mov.valor for mov in pendientes_bancos_entradas)
    pendientes_bancos_entradas_total = sum(mov.valor for mov in pendientes_bancos_entradas)
    conciliados_bancos_entradas_total = sum(mov.valor for mov in conciliados_bancos_entradas)
    pdf.cell(45, 5, txt="Entradas Bancos", border=1, align="C")
    pdf.cell(45, 5, txt=f"{total_bancos_entradas:,.2f}", border=1, align="C")
    pdf.cell(45, 5, txt=f"{pendientes_bancos_entradas_total:,.2f}", border=1, align="C")
    pdf.cell(45, 5, txt=f"{conciliados_bancos_entradas_total:,.2f}", border=1, align="C")
    pdf.ln(5)

    # Bancos - Salidas
    total_bancos_salidas = sum(mov.valor for mov in conciliados_bancos_salidas) + sum(mov.valor for mov in pendientes_bancos_salidas)
    pendientes_bancos_salidas_total = sum(mov.valor for mov in pendientes_bancos_salidas)
    conciliados_bancos_salidas_total = sum(mov.valor for mov in conciliados_bancos_salidas)
    pdf.cell(45, 5, txt="Salidas Bancos", border=1, align="C")
    pdf.cell(45, 5, txt=f"{total_bancos_salidas:,.2f}", border=1, align="C")
    pdf.cell(45, 5, txt=f"{pendientes_bancos_salidas_total:,.2f}", border=1, align="C")
    pdf.cell(45, 5, txt=f"{conciliados_bancos_salidas_total:,.2f}", border=1, align="C")
    pdf.ln(10)

    # Estadísticas de registros (cantidad de movimientos)
    pdf.set_font("Times", size=10)
    pdf.cell(200, 10, txt="Estadísticas de Registros (Cantidad de Movimientos)", ln=True, align="L")
    pdf.ln(1)

    # Tabla de estadísticas de registros
    pdf.set_font("Times", size=9)
    pdf.cell(45, 5, txt="Categoría", border=1, align="C")
    pdf.cell(45, 5, txt="Total", border=1, align="C")
    pdf.cell(45, 5, txt="Pendientes", border=1, align="C")
    pdf.cell(45, 5, txt="Conciliadas", border=1, align="C")
    pdf.ln(5)

    # Auxiliares - Entradas
    total_auxiliares_entradas_count = len(conciliados_auxiliares_entradas) + len(pendientes_auxiliares_entradas)
    pendientes_auxiliares_entradas_count = len(pendientes_auxiliares_entradas)
    conciliados_auxiliares_entradas_count = len(conciliados_auxiliares_entradas)
    pdf.cell(45, 5, txt="Entradas Auxiliares", border=1, align="C")
    pdf.cell(45, 5, txt=f"{total_auxiliares_entradas_count}", border=1, align="C")
    pdf.cell(45, 5, txt=f"{pendientes_auxiliares_entradas_count}", border=1, align="C")
    pdf.cell(45, 5, txt=f"{conciliados_auxiliares_entradas_count}", border=1, align="C")
    pdf.ln(5)

    # Auxiliares - Salidas
    total_auxiliares_salidas_count = len(conciliados_auxiliares_salidas) + len(pendientes_auxiliares_salidas)
    pendientes_auxiliares_salidas_count = len(pendientes_auxiliares_salidas)
    conciliados_auxiliares_salidas_count = len(conciliados_auxiliares_salidas)
    pdf.cell(45, 5, txt="Salidas Auxiliares", border=1, align="C")
    pdf.cell(45, 5, txt=f"{total_auxiliares_salidas_count}", border=1, align="C")
    pdf.cell(45, 5, txt=f"{pendientes_auxiliares_salidas_count}", border=1, align="C")
    pdf.cell(45, 5, txt=f"{conciliados_auxiliares_salidas_count}", border=1, align="C")
    pdf.ln(5)

    # Bancos - Entradas
    total_bancos_entradas_count = len(conciliados_bancos_entradas) + len(pendientes_bancos_entradas)
    pendientes_bancos_entradas_count = len(pendientes_bancos_entradas)
    conciliados_bancos_entradas_count = len(conciliados_bancos_entradas)
    pdf.cell(45, 5, txt="Entradas Bancos", border=1, align="C")
    pdf.cell(45, 5, txt=f"{total_bancos_entradas_count}", border=1, align="C")
    pdf.cell(45, 5, txt=f"{pendientes_bancos_entradas_count}", border=1, align="C")
    pdf.cell(45, 5, txt=f"{conciliados_bancos_entradas_count}", border=1, align="C")
    pdf.ln(5)

    # Bancos - Salidas
    total_bancos_salidas_count = len(conciliados_bancos_salidas) + len(pendientes_bancos_salidas)
    pendientes_bancos_salidas_count = len(pendientes_bancos_salidas)
    conciliados_bancos_salidas_count = len(conciliados_bancos_salidas)
    pdf.cell(45, 5, txt="Salidas Bancos", border=1, align="C")
    pdf.cell(45, 5, txt=f"{total_bancos_salidas_count}", border=1, align="C")
    pdf.cell(45, 5, txt=f"{pendientes_bancos_salidas_count}", border=1, align="C")
    pdf.cell(45, 5, txt=f"{conciliados_bancos_salidas_count}", border=1, align="C")
    pdf.ln(10)

    # Tabla de movimientos pendientes de auxiliares - Entradas
    pdf.set_font("Times", size=12, style="B")
    pdf.cell(200, 10, txt="Movimientos Pendientes - Auxiliares (Entradas)", ln=True, align="L")
    pdf.ln(5)
    
    if pendientes_auxiliares_entradas:
        pdf.set_font("Times", size=9)
        pdf.cell(30, 5, txt="Fecha", border=1, align="C")
        pdf.cell(80, 5, txt="Descripción", border=1, align="C")
        pdf.cell(30, 5, txt="Valor", border=1, align="C")
        pdf.cell(30, 5, txt="E/S", border=1, align="C")
        pdf.ln(5)
        total_entradas_auxiliares = 0
        for mov in pendientes_auxiliares_entradas:
            pdf.cell(30, 5, txt=mov.fecha, border=1, align="C")
            # Limitar descripción para que quepa en el espacio
            descripcion_corta = mov.descripcion[:40] + "..." if len(mov.descripcion) > 40 else mov.descripcion
            pdf.cell(80, 5, txt=descripcion_corta, border=1, align="L")
            pdf.cell(30, 5, txt=f"{mov.valor:,.2f}", border=1, align="R")
            pdf.cell(30, 5, txt=mov.es, border=1, align="C")
            pdf.ln(5)
            total_entradas_auxiliares += mov.valor
        pdf.set_font("Times", size=10, style="B")
        pdf.cell(140, 8, txt=f"Total Entradas Auxiliares Pendientes: {total_entradas_auxiliares:,.2f}", ln=True, align="R")
    else:
        pdf.set_font("Times", size=10, style="I")
        pdf.cell(200, 8, txt="No hay movimientos pendientes de auxiliares (Entradas)", ln=True, align="C")

    pdf.ln(10)

    # Tabla de movimientos pendientes de auxiliares - Salidas
    pdf.set_font("Times", size=12, style="B")
    pdf.cell(200, 10, txt="Movimientos Pendientes - Auxiliares (Salidas)", ln=True, align="L")
    pdf.ln(5)
    
    if pendientes_auxiliares_salidas:
        pdf.set_font("Times", size=9)
        pdf.cell(30, 5, txt="Fecha", border=1, align="C")
        pdf.cell(80, 5, txt="Descripción", border=1, align="C")
        pdf.cell(30, 5, txt="Valor", border=1, align="C")
        pdf.cell(30, 5, txt="E/S", border=1, align="C")
        pdf.ln(5)
        total_salidas_auxiliares = 0
        for mov in pendientes_auxiliares_salidas:
            pdf.cell(30, 5, txt=mov.fecha, border=1, align="C")
            descripcion_corta = mov.descripcion[:40] + "..." if len(mov.descripcion) > 40 else mov.descripcion
            pdf.cell(80, 5, txt=descripcion_corta, border=1, align="L")
            pdf.cell(30, 5, txt=f"{mov.valor:,.2f}", border=1, align="R")
            pdf.cell(30, 5, txt=mov.es, border=1, align="C")
            pdf.ln(5)
            total_salidas_auxiliares += mov.valor
        pdf.set_font("Times", size=10, style="B")
        pdf.cell(140, 8, txt=f"Total Salidas Auxiliares Pendientes: {total_salidas_auxiliares:,.2f}", ln=True, align="R")
    else:
        pdf.set_font("Times", size=10, style="I")
        pdf.cell(200, 8, txt="No hay movimientos pendientes de auxiliares (Salidas)", ln=True, align="C")

    pdf.ln(10)

    # Tabla de movimientos pendientes de bancos - Entradas
    pdf.set_font("Times", size=12, style="B")
    pdf.cell(200, 10, txt="Movimientos Pendientes - Bancos (Entradas)", ln=True, align="L")
    pdf.ln(5)
    
    if pendientes_bancos_entradas:
        pdf.set_font("Times", size=9)
        pdf.cell(30, 5, txt="Fecha", border=1, align="C")
        pdf.cell(80, 5, txt="Descripción", border=1, align="C")
        pdf.cell(30, 5, txt="Valor", border=1, align="C")
        pdf.cell(30, 5, txt="E/S", border=1, align="C")
        pdf.ln(5)
        total_entradas_bancos = 0
        for mov in pendientes_bancos_entradas:
            pdf.cell(30, 5, txt=mov.fecha, border=1, align="C")
            descripcion_corta = mov.descripcion[:40] + "..." if len(mov.descripcion) > 40 else mov.descripcion
            pdf.cell(80, 5, txt=descripcion_corta, border=1, align="L")
            pdf.cell(30, 5, txt=f"{mov.valor:,.2f}", border=1, align="R")
            pdf.cell(30, 5, txt=mov.es, border=1, align="C")
            pdf.ln(5)
            total_entradas_bancos += mov.valor
        pdf.set_font("Times", size=10, style="B")
        pdf.cell(140, 8, txt=f"Total Entradas Bancos Pendientes: {total_entradas_bancos:,.2f}", ln=True, align="R")
    else:
        pdf.set_font("Times", size=10, style="I")
        pdf.cell(200, 8, txt="No hay movimientos pendientes de bancos (Entradas)", ln=True, align="C")

    pdf.ln(10)

    # Tabla de movimientos pendientes de bancos - Salidas
    pdf.set_font("Times", size=12, style="B")
    pdf.cell(200, 10, txt="Movimientos Pendientes - Bancos (Salidas)", ln=True, align="L")
    pdf.ln(5)
    
    if pendientes_bancos_salidas:
        pdf.set_font("Times", size=9)
        pdf.cell(30, 5, txt="Fecha", border=1, align="C")
        pdf.cell(80, 5, txt="Descripción", border=1, align="C")
        pdf.cell(30, 5, txt="Valor", border=1, align="C")
        pdf.cell(30, 5, txt="E/S", border=1, align="C")
        pdf.ln(5)
        total_salidas_bancos = 0
        for mov in pendientes_bancos_salidas:
            pdf.cell(30, 5, txt=mov.fecha, border=1, align="C")
            descripcion_corta = mov.descripcion[:40] + "..." if len(mov.descripcion) > 40 else mov.descripcion
            pdf.cell(80, 5, txt=descripcion_corta, border=1, align="L")
            pdf.cell(30, 5, txt=f"{mov.valor:,.2f}", border=1, align="R")
            pdf.cell(30, 5, txt=mov.es, border=1, align="C")
            pdf.ln(5)
            total_salidas_bancos += mov.valor
        pdf.set_font("Times", size=10, style="B")
        pdf.cell(140, 8, txt=f"Total Salidas Bancos Pendientes: {total_salidas_bancos:,.2f}", ln=True, align="R")
    else:
        pdf.set_font("Times", size=10, style="I")
        pdf.cell(200, 8, txt="No hay movimientos pendientes de bancos (Salidas)", ln=True, align="C")

    pdf.ln(10)

    output_dir = "generated_reports"
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f"informe_conciliacion_{conciliacion.id}.pdf")
    pdf.output(file_path)

    # Programar eliminación automática del archivo después de 20 segundos
    eliminar_pdf_despues_de_tiempo(file_path, 20)

    return file_path

def eliminar_pdf_despues_de_tiempo(file_path, delay):
    """Elimina un archivo PDF después de un tiempo especificado en un subproceso."""
    def eliminar():
        time.sleep(delay)
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"El archivo {file_path} ha sido eliminado automáticamente.")

    # Crear y ejecutar un subproceso para la eliminación
    threading.Thread(target=eliminar, daemon=True).start()