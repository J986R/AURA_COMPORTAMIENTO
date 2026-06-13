from datetime import datetime


def calcular_puntaje_planificacion(fecha_entrega, prioridad, dificultad, estado):
    if estado == "Completada":
        return 0

    hoy = datetime.now().date()
    try:
        entrega = datetime.strptime(str(fecha_entrega), "%Y-%m-%d").date()
        dias_restantes = (entrega - hoy).days
    except Exception:
        dias_restantes = 30

    puntaje = 0
    if dias_restantes < 0:
        puntaje += 50
    elif dias_restantes == 0:
        puntaje += 45
    elif dias_restantes == 1:
        puntaje += 40
    elif dias_restantes <= 3:
        puntaje += 30
    elif dias_restantes <= 7:
        puntaje += 20
    else:
        puntaje += 10

    if prioridad == "Alta":
        puntaje += 30
    elif prioridad == "Media":
        puntaje += 20
    else:
        puntaje += 10

    puntaje += int(dificultad or 3) * 5

    if estado == "Pendiente":
        puntaje += 15
    elif estado == "En proceso":
        puntaje += 8

    return puntaje


def generar_plan_semanal(tareas, horas_disponibles_semana, nivel_riesgo):
    tareas_activas = []
    for tarea in tareas:
        if tarea["estado"] != "Completada":
            tarea = dict(tarea)
            tarea["puntaje"] = calcular_puntaje_planificacion(
                tarea["fecha_entrega"], tarea["prioridad"], tarea["dificultad"], tarea["estado"]
            )
            tareas_activas.append(tarea)

    tareas_activas = sorted(tareas_activas, key=lambda x: x["puntaje"], reverse=True)
    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    horas_disponibles_semana = float(horas_disponibles_semana or 7)
    horas_por_dia = round(max(horas_disponibles_semana, 1) / 7, 1)

    if nivel_riesgo == "Alto":
        recomendacion_base = "Prioriza avance académico fuerte y reduce tareas acumuladas."
        bloque_base = 1.5
    elif nivel_riesgo == "Medio":
        recomendacion_base = "Mantén constancia y evita acumular pendientes."
        bloque_base = 1.0
    else:
        recomendacion_base = "Mantén tu ritmo y refuerza los cursos más difíciles."
        bloque_base = 0.75

    plan = []
    indice_tarea = 0

    for dia in dias_semana:
        tareas_del_dia = []
        horas_asignadas = 0
        while horas_asignadas < horas_por_dia and indice_tarea < len(tareas_activas):
            tarea = tareas_activas[indice_tarea]
            horas_tarea = bloque_base
            if tarea["prioridad"] == "Alta":
                horas_tarea += 0.5
            if int(tarea["dificultad"] or 3) >= 4:
                horas_tarea += 0.5
            horas_tarea = min(horas_tarea, horas_por_dia)
            tareas_del_dia.append({
                "Curso": tarea["curso"],
                "Actividad": tarea["titulo"],
                "Prioridad": tarea["prioridad"],
                "Fecha de entrega": tarea["fecha_entrega"],
                "Horas recomendadas": horas_tarea,
            })
            horas_asignadas += horas_tarea
            indice_tarea += 1

        if not tareas_del_dia:
            tareas_del_dia.append({
                "Curso": "Repaso general",
                "Actividad": "Repasar apuntes, ordenar materiales o adelantar lecturas.",
                "Prioridad": "Baja",
                "Fecha de entrega": "-",
                "Horas recomendadas": horas_por_dia,
            })

        plan.append({
            "día": dia,
            "horas_disponibles": horas_por_dia,
            "recomendacion": recomendacion_base,
            "tareas": tareas_del_dia,
        })

    return plan
