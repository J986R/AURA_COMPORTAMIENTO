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

    try:
        puntaje += int(dificultad) * 5
    except Exception:
        puntaje += 10

    if estado == "Pendiente":
        puntaje += 15
    elif estado == "En proceso":
        puntaje += 8
    return puntaje


def generar_plan_semanal(tareas, horas_disponibles_semana, nivel_riesgo):
    """Plan de respaldo si falla la IA. Distribuye tareas en bloques, no concentra todo en un día."""
    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    horas_por_dia = max(0.5, round(float(horas_disponibles_semana or 7) / 7, 1))

    activas = []
    for tarea in tareas:
        if tarea.get("estado") == "Completada":
            continue
        tarea = tarea.copy()
        tarea["puntaje"] = calcular_puntaje_planificacion(
            tarea.get("fecha_entrega"), tarea.get("prioridad"), tarea.get("dificultad"), tarea.get("estado")
        )
        activas.append(tarea)
    activas.sort(key=lambda x: x["puntaje"], reverse=True)

    if nivel_riesgo == "Alto":
        recomendacion = "Prioriza avances pequeños y constantes. Evita concentrar todo al final."
    elif nivel_riesgo == "Medio":
        recomendacion = "Mantén constancia y reparte las tareas complejas en varios bloques."
    else:
        recomendacion = "Mantén tu ritmo y usa los días libres para repasar o adelantar."

    plan = []
    for dia in dias_semana:
        plan.append({"dia": dia, "horas_disponibles": horas_por_dia, "recomendacion": recomendacion, "tareas": []})

    if not activas:
        for dia in plan:
            dia["tareas"].append({
                "curso": "Repaso general",
                "actividad": "Repasar apuntes, ordenar materiales o adelantar lecturas",
                "tarea_origen": "-",
                "prioridad": "Baja",
                "fecha_entrega": "-",
                "horas_recomendadas": horas_por_dia,
            })
        return plan

    dia_idx = 0
    horas_restantes_dia = [horas_por_dia for _ in dias_semana]
    for tarea in activas:
        dificultad = int(tarea.get("dificultad") or 3)
        prioridad = tarea.get("prioridad", "Media")
        horas_estimadas = 1.0 + dificultad * 0.7
        if prioridad == "Alta":
            horas_estimadas += 1.0
        elif prioridad == "Media":
            horas_estimadas += 0.5

        while horas_estimadas > 0.05 and dia_idx < 7:
            disponible = horas_restantes_dia[dia_idx]
            if disponible <= 0.05:
                dia_idx += 1
                continue
            bloque = min(disponible, horas_estimadas, 1.5)
            actividad = "Avance de la tarea"
            if horas_estimadas > bloque:
                actividad = "Avance parcial: dividir, desarrollar y dejar evidencia"
            plan[dia_idx]["tareas"].append({
                "curso": tarea.get("curso", "-"),
                "actividad": actividad,
                "tarea_origen": tarea.get("titulo", "-"),
                "prioridad": prioridad,
                "fecha_entrega": tarea.get("fecha_entrega", "-"),
                "horas_recomendadas": round(bloque, 1),
            })
            horas_restantes_dia[dia_idx] -= bloque
            horas_estimadas -= bloque
            if horas_restantes_dia[dia_idx] <= 0.05:
                dia_idx += 1

    for idx, dia in enumerate(plan):
        if not dia["tareas"]:
            dia["tareas"].append({
                "curso": "Repaso general",
                "actividad": "Repasar apuntes o adelantar lecturas de cursos difíciles",
                "tarea_origen": "-",
                "prioridad": "Baja",
                "fecha_entrega": "-",
                "horas_recomendadas": horas_por_dia,
            })
    return plan
