from fpdf import FPDF
import os
import time

def generar_pdf_informe(conciliacion_id, conciliados, pendientes):
    print("Generando PDF...")

    # Separar los movimientos conciliados y pendientes por tipo
    conciliados_bancos = [mov for mov in conciliados if mov.tipo == "banco"]
    conciliados_auxiliares = [mov for mov in conciliados if mov.tipo == "auxiliar"]
    pendientes_bancos = [mov for mov in pendientes if mov.tipo == "banco"]
    pendientes_auxiliares = [mov for mov in pendientes if mov.tipo == "auxiliar"]

    # Separar los movimientos pendientes y conciliados en entradas y salidas
    pendientes_auxiliares_entradas = [mov for mov in pendientes_auxiliares if mov.valor > 0]
    pendientes_auxiliares_salidas = [mov for mov in pendientes_auxiliares if mov.valor < 0]
    conciliados_auxiliares_entradas = [mov for mov in conciliados_auxiliares if mov.valor > 0]
    conciliados_auxiliares_salidas = [mov for mov in conciliados_auxiliares if mov.valor < 0]

    pendientes_bancos_entradas = [mov for mov in pendientes_bancos if mov.valor > 0]
    pendientes_bancos_salidas = [mov for mov in pendientes_bancos if mov.valor < 0]
    conciliados_bancos_entradas = [mov for mov in conciliados_bancos if mov.valor > 0]
    conciliados_bancos_salidas = [mov for mov in conciliados_bancos if mov.valor < 0]

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Times", size=12)  # Cambiar a Times New Roman

    pdf.cell(200, 10, txt=f"Informe de Conciliación #{conciliacion_id}", ln=True, align="C")
    pdf.ln(10)

    # Estadísticas de movimientos conciliados y pendientes
    pdf.set_font("Times", size=10)
    pdf.cell(200, 10, txt="Las siguientes secciones muestran un resumen de los movimientos que están pendientes por conciliar:", ln=True, align="L")
    pdf.ln(5)

    # Estadísticas totales
    pdf.set_font("Times", size=10)
    pdf.cell(200, 10, txt="Estadísticas Totales", ln=True, align="L")
    pdf.ln(5)

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
    pdf.ln(5)

    # Estadísticas de registros (cantidad de movimientos)
    pdf.set_font("Times", size=10)
    pdf.cell(200, 10, txt="Estadísticas de Registros (Cantidad de Movimientos)", ln=True, align="L")
    pdf.ln(5)

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
    pdf.cell(200, 10, txt="Movimientos Pendientes - Auxiliares (Entradas)", ln=True, align="L")
    pdf.ln(5)
    pdf.set_font("Times", size=9)
    pdf.cell(50, 5, txt="Fecha", border=1, align="C")
    pdf.cell(90, 5, txt="Descripción", border=1, align="C")
    pdf.cell(40, 5, txt="Valor", border=1, align="C")
    pdf.ln(5)
    total_entradas_auxiliares = 0
    for mov in pendientes_auxiliares_entradas:
        pdf.cell(50, 5, txt=mov.fecha, border=1, align="C")
        pdf.cell(90, 5, txt=mov.descripcion, border=1, align="C")
        pdf.cell(40, 5, txt=f"{mov.valor:,.2f}", border=1, align="C")
        pdf.ln(5)
        total_entradas_auxiliares += mov.valor
    pdf.cell(170, 10, txt=f"Total Entradas Auxiliares: {total_entradas_auxiliares:,.2f}", ln=True, align="R")

    pdf.ln(10)

    # Tabla de movimientos pendientes de auxiliares - Salidas
    pdf.cell(200, 10, txt="Movimientos Pendientes - Auxiliares (Salidas)", ln=True, align="L")
    pdf.ln(5)
    pdf.set_font("Times", size=9)
    pdf.cell(50, 5, txt="Fecha", border=1, align="C")
    pdf.cell(90, 5, txt="Descripción", border=1, align="C")
    pdf.cell(40, 5, txt="Valor", border=1, align="C")
    pdf.ln(5)
    total_salidas_auxiliares = 0
    for mov in pendientes_auxiliares_salidas:
        pdf.cell(50, 5, txt=mov.fecha, border=1, align="C")
        pdf.cell(90, 5, txt=mov.descripcion, border=1, align="C")
        pdf.cell(40, 5, txt=f"{mov.valor:,.2f}", border=1, align="C")
        pdf.ln(5)
        total_salidas_auxiliares += mov.valor
    pdf.cell(170, 10, txt=f"Total Salidas Auxiliares: {total_salidas_auxiliares:,.2f}", ln=True, align="R")

    pdf.ln(10)

    # Tabla de movimientos pendientes de bancos - Entradas
    pdf.cell(200, 10, txt="Movimientos Pendientes - Bancos (Entradas)", ln=True, align="L")
    pdf.ln(5)
    pdf.set_font("Times", size=9)
    pdf.cell(50, 5, txt="Fecha", border=1, align="C")
    pdf.cell(90, 5, txt="Descripción", border=1, align="C")
    pdf.cell(40, 5, txt="Valor", border=1, align="C")
    pdf.ln(5)
    total_entradas_bancos = 0
    for mov in pendientes_bancos_entradas:
        pdf.cell(50, 5, txt=mov.fecha, border=1, align="C")
        pdf.cell(90, 5, txt=mov.descripcion, border=1, align="C")
        pdf.cell(40, 5, txt=f"{mov.valor:,.2f}", border=1, align="C")
        pdf.ln(5)
        total_entradas_bancos += mov.valor
    pdf.cell(170, 10, txt=f"Total Entradas Bancos: {total_entradas_bancos:,.2f}", ln=True, align="R")

    pdf.ln(10)

    # Tabla de movimientos pendientes de bancos - Salidas
    pdf.cell(200, 10, txt="Movimientos Pendientes - Bancos (Salidas)", ln=True, align="L")
    pdf.ln(5)
    pdf.set_font("Times", size=9)
    pdf.cell(50, 5, txt="Fecha", border=1, align="C")
    pdf.cell(90, 5, txt="Descripción", border=1, align="C")
    pdf.cell(40, 5, txt="Valor", border=1, align="C")
    pdf.ln(5)
    total_salidas_bancos = 0
    for mov in pendientes_bancos_salidas:
        pdf.cell(50, 5, txt=mov.fecha, border=1, align="C")
        pdf.cell(90, 5, txt=mov.descripcion, border=1, align="C")
        pdf.cell(40, 5, txt=f"{mov.valor:,.2f}", border=1, align="C")
        pdf.ln(5)
        total_salidas_bancos += mov.valor
    pdf.cell(170, 10, txt=f"Total Salidas Bancos: {total_salidas_bancos:,.2f}", ln=True, align="R")

    pdf.ln(10)

    output_dir = "generated_reports"
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f"informe_conciliacion_{conciliacion_id}.pdf")
    pdf.output(file_path)

    # Programar eliminación automática del archivo después de 20 segundos
    # eliminar_pdf_despues_de_tiempo(file_path, 20)

    return file_path

def eliminar_pdf_despues_de_tiempo(file_path, delay):
    """Elimina un archivo PDF después de un tiempo especificado."""
    time.sleep(delay)
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"El archivo {file_path} ha sido eliminado automáticamente.")