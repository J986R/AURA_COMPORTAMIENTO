from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet


def _header_style(ws, row, max_col):
    fill = PatternFill("solid", fgColor="6B0F1A")
    font = Font(color="FFFFFF", bold=True)
    border = Border(bottom=Side(style="thin", color="999999"))
    for col in range(1, max_col + 1):
        cell = ws.cell(row=row, column=col)
        cell.fill = fill
        cell.font = font
        cell.alignment = Alignment(horizontal="center")
        cell.border = border


def crear_excel_reporte(nombre, codigo, carrera, ciclo, diagnostico, detalle, resumen_tareas, cursos, tareas):
    output = BytesIO()
    wb = Workbook()
    ws = wb.active
    ws.title = "Resumen"

    ws.append(["REPORTE AURA"])
    ws["A1"].font = Font(bold=True, size=16, color="6B0F1A")
    ws.append([])
    ws.append(["Estudiante", nombre])
    ws.append(["Código", codigo])
    ws.append(["Carrera", carrera])
    ws.append(["Ciclo", ciclo])
    ws.append([])

    if diagnostico:
        ws.append(["Horas de estudio por día", diagnostico[0]])
        ws.append(["Promedio ponderado", diagnostico[1]])
        ws.append(["Puntaje de riesgo IA", diagnostico[6]])
        ws.append(["Nivel de riesgo IA", diagnostico[7]])
        ws.append(["Fecha diagnóstico", diagnostico[8]])

    ws.append([])
    ws.append(["Total tareas", resumen_tareas["total"]])
    ws.append(["Completadas", resumen_tareas["completadas"]])
    ws.append(["Pendientes", resumen_tareas["pendientes"]])
    ws.append(["Alta prioridad", resumen_tareas["alta_prioridad"]])
    ws.append(["Cumplimiento", f"{resumen_tareas['porcentaje_cumplimiento']}%"])

    if detalle:
        ws.append([])
        ws.append(["Diagnóstico general IA", detalle.get("diagnostico_general_ia", "")])
        ws.append(["Recomendación estudiante", detalle.get("recomendacion_estudiante_ia", "")])
        ws.append(["Recomendación tutoría", detalle.get("recomendacion_tutoria_ia", "")])

    ws2 = wb.create_sheet("Cursos")
    ws2.append(["ID", "Curso", "Docente", "Créditos", "Dificultad", "Estado"])
    _header_style(ws2, 1, 6)
    for curso in cursos:
        ws2.append(list(curso))

    ws3 = wb.create_sheet("Tareas")
    ws3.append(["ID", "Tarea", "Curso", "Fecha entrega", "Prioridad", "Estado"])
    _header_style(ws3, 1, 6)
    for tarea in tareas:
        ws3.append(list(tarea))

    for sheet in wb.worksheets:
        for column in sheet.columns:
            max_length = 0
            letter = column[0].column_letter
            for cell in column:
                try:
                    max_length = max(max_length, len(str(cell.value)))
                except Exception:
                    pass
            sheet.column_dimensions[letter].width = min(max_length + 3, 80)

    wb.save(output)
    output.seek(0)
    return output.getvalue()


def _style_table():
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6B0F1A")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
    ])


def crear_pdf_reporte(nombre, codigo, carrera, ciclo, diagnostico, detalle, resumen_tareas, cursos, tareas):
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Reporte AURA", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>Estudiante:</b> {nombre}", styles["Normal"]))
    story.append(Paragraph(f"<b>Código:</b> {codigo}", styles["Normal"]))
    story.append(Paragraph(f"<b>Carrera:</b> {carrera}", styles["Normal"]))
    story.append(Paragraph(f"<b>Ciclo:</b> {ciclo}", styles["Normal"]))
    story.append(Spacer(1, 12))

    if diagnostico:
        data = [
            ["Indicador", "Valor"],
            ["Horas estudio/día", str(diagnostico[0])],
            ["Promedio ponderado", str(diagnostico[1])],
            ["Puntaje riesgo IA", f"{diagnostico[6]}/100"],
            ["Nivel riesgo IA", str(diagnostico[7])],
            ["Fecha", str(diagnostico[8])],
        ]
        table = Table(data, colWidths=[170, 320])
        table.setStyle(_style_table())
        story.append(table)
        story.append(Spacer(1, 12))

    if detalle:
        story.append(Paragraph("Diagnóstico IA", styles["Heading2"]))
        story.append(Paragraph(str(detalle.get("diagnostico_general_ia", "")), styles["Normal"]))
        story.append(Spacer(1, 8))
        story.append(Paragraph("Recomendación al estudiante", styles["Heading3"]))
        story.append(Paragraph(str(detalle.get("recomendacion_estudiante_ia", "")), styles["Normal"]))
        story.append(Spacer(1, 8))
        story.append(Paragraph("Recomendación a tutoría", styles["Heading3"]))
        story.append(Paragraph(str(detalle.get("recomendacion_tutoria_ia", "")), styles["Normal"]))
        story.append(Spacer(1, 12))

    resumen = [
        ["Resumen de tareas", "Valor"],
        ["Total", resumen_tareas["total"]],
        ["Completadas", resumen_tareas["completadas"]],
        ["Pendientes", resumen_tareas["pendientes"]],
        ["Alta prioridad", resumen_tareas["alta_prioridad"]],
        ["Cumplimiento", f"{resumen_tareas['porcentaje_cumplimiento']}%"],
    ]
    table = Table(resumen, colWidths=[170, 320])
    table.setStyle(_style_table())
    story.append(table)
    story.append(Spacer(1, 12))

    if cursos:
        story.append(Paragraph("Cursos", styles["Heading2"]))
        data = [["Curso", "Docente", "Dificultad", "Estado"]]
        for c in cursos[:10]:
            data.append([str(c[1]), str(c[2]), str(c[4]), str(c[5])])
        table = Table(data, colWidths=[150, 140, 80, 100])
        table.setStyle(_style_table())
        story.append(table)
        story.append(Spacer(1, 12))

    if tareas:
        story.append(Paragraph("Tareas", styles["Heading2"]))
        data = [["Tarea", "Curso", "Fecha", "Prioridad", "Estado"]]
        for t in tareas[:15]:
            data.append([str(t[1])[:24], str(t[2])[:18], str(t[3]), str(t[4]), str(t[5])])
        table = Table(data, colWidths=[120, 110, 85, 75, 85])
        table.setStyle(_style_table())
        story.append(table)

    doc.build(story)
    output.seek(0)
    return output.getvalue()
