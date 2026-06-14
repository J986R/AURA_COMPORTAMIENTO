from datetime import datetime

DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]


def _time_to_float(t):
    try:
        h, m = str(t)[:5].split(":")
        return int(h) + int(m) / 60
    except Exception:
        return 8.0


def _float_to_time(v):
    h = int(v)
    m = int(round((v - h) * 60))
    if m >= 60:
        h += 1
        m = 0
    return f"{h:02d}:{m:02d}"


def _se_cruza(a_ini, a_fin, b_ini, b_fin):
    return max(a_ini, b_ini) < min(a_fin, b_fin)


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
    puntaje += {"Alta": 30, "Media": 20, "Baja": 10}.get(prioridad, 15)
    try:
        puntaje += int(dificultad or 3) * 5
    except Exception:
        puntaje += 15
    if estado == "Pendiente":
        puntaje += 15
    elif estado == "En proceso":
        puntaje += 8
    return puntaje


def generar_plan_calendario_respaldo(tareas, horarios_clase, horas_disponibles_semana, nivel_riesgo):
    """Planificador simple de respaldo que no se cruza con clases."""
    tareas_activas = []
    for tarea in tareas:
        if tarea.get("estado") != "Completada":
            tarea = dict(tarea)
            tarea["puntaje"] = calcular_puntaje_planificacion(tarea.get("fecha_entrega"), tarea.get("prioridad"), tarea.get("dificultad"), tarea.get("estado"))
            tareas_activas.append(tarea)
    tareas_activas.sort(key=lambda x: x["puntaje"], reverse=True)
    if not tareas_activas:
        return []

    ocupados = {d: [] for d in DIAS}
    for h in horarios_clase or []:
        d = h.get("dia")
        if d in ocupados:
            ocupados[d].append((_time_to_float(h.get("inicio")), _time_to_float(h.get("fin"))))

    total_horas = max(1.0, float(horas_disponibles_semana or 7))
    horas_restantes = total_horas
    bloques = []
    colores = ["#14B8B8", "#7C3AED", "#2563EB", "#16A34A", "#F59E0B", "#DC2626"]
    tarea_idx = 0

    def buscar_slot(dia, duracion):
        # Rangos de estudio preferidos: mañana/tarde, evitando madrugada y muy tarde.
        candidatos = [(8.0, 12.0), (13.0, 16.0), (18.0, 22.0), (20.0, 23.0)]
        for start_range, end_range in candidatos:
            t = start_range
            while t + duracion <= end_range:
                cruza = False
                for a, b in ocupados[dia]:
                    if _se_cruza(t, t + duracion, a, b):
                        cruza = True
                        t = b
                        break
                if not cruza:
                    ocupados[dia].append((t, t + duracion))
                    ocupados[dia].sort()
                    return t, t + duracion
                t += 0.5
        return None

    while horas_restantes > 0.25 and tarea_idx < len(tareas_activas) * 3:
        tarea = tareas_activas[tarea_idx % len(tareas_activas)]
        dificultad = int(tarea.get("dificultad") or 3)
        duracion = 1.5 if dificultad >= 4 or tarea.get("prioridad") == "Alta" else 1.0
        duracion = min(duracion, horas_restantes)
        asignado = False
        for dia in DIAS:
            slot = buscar_slot(dia, duracion)
            if slot:
                ini, fin = slot
                actividad = "Avance principal"
                if tarea_idx % 3 == 0:
                    actividad = "Revisar indicaciones y avanzar primera parte"
                elif tarea_idx % 3 == 1:
                    actividad = "Desarrollar contenido o resolver ejercicios"
                else:
                    actividad = "Revisar, corregir y dejar listo para entrega"
                bloques.append({
                    "tipo": "Estudio",
                    "dia": dia,
                    "inicio": _float_to_time(ini),
                    "fin": _float_to_time(fin),
                    "curso": tarea.get("curso", "Curso"),
                    "actividad": actividad,
                    "tarea_origen": tarea.get("titulo", "Tarea"),
                    "prioridad": tarea.get("prioridad", "Media"),
                    "color": colores[tarea_idx % len(colores)],
                })
                horas_restantes -= duracion
                asignado = True
                break
        tarea_idx += 1
        if not asignado:
            break
    return bloques


# Compatibilidad con versiones previas.
def generar_plan_semanal(tareas, horas_disponibles_semana, nivel_riesgo):
    bloques = generar_plan_calendario_respaldo(tareas, [], horas_disponibles_semana, nivel_riesgo)
    agrupado = []
    for dia in DIAS:
        tareas_dia = [b for b in bloques if b["dia"] == dia]
        agrupado.append({"dia": dia, "horas_disponibles": sum((_time_to_float(b["fin"]) - _time_to_float(b["inicio"])) for b in tareas_dia), "recomendacion": "Plan de respaldo generado automáticamente.", "tareas": tareas_dia})
    return agrupado
