from __future__ import annotations

from datetime import date, datetime, timedelta
from calendar import monthrange
from typing import Any

DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
DIA_NUM = {d: i for i, d in enumerate(DIAS)}
COLORES_ESTUDIO = ["#7DD3FC", "#A7F3D0", "#DDD6FE", "#FDE68A", "#FBCFE8", "#BAE6FD", "#C4B5FD", "#BBF7D0"]


def normalizar_fecha(valor: Any, default: date | None = None) -> date:
    if default is None:
        default = date.today()
    if isinstance(valor, date):
        return valor
    try:
        return datetime.strptime(str(valor)[:10], "%Y-%m-%d").date()
    except Exception:
        return default


def dia_de_fecha(fecha: date) -> str:
    return DIAS[fecha.weekday()]


def _time_to_float(t: Any) -> float:
    try:
        h, m = str(t)[:5].split(":")
        return int(h) + int(m) / 60
    except Exception:
        return 8.0


def _float_to_time(v: float) -> str:
    h = int(v)
    m = int(round((v - h) * 60))
    if m >= 60:
        h += 1
        m = 0
    return f"{h:02d}:{m:02d}"


def _se_cruza(a_ini: float, a_fin: float, b_ini: float, b_fin: float) -> bool:
    return max(a_ini, b_ini) < min(a_fin, b_fin)


def _rango_fechas(inicio: date, dias: int) -> list[date]:
    return [inicio + timedelta(days=i) for i in range(max(1, int(dias)))]


def dias_restantes_mes(fecha_inicio: date | None = None) -> int:
    fecha_inicio = fecha_inicio or date.today()
    ultimo = date(fecha_inicio.year, fecha_inicio.month, monthrange(fecha_inicio.year, fecha_inicio.month)[1])
    return max(1, (ultimo - fecha_inicio).days + 1)


def calcular_puntaje_planificacion(fecha_entrega, prioridad, dificultad, estado):
    if estado == "Completada":
        return 0
    hoy = date.today()
    entrega = normalizar_fecha(fecha_entrega, hoy + timedelta(days=30))
    dias_restantes = (entrega - hoy).days
    puntaje = 0
    if dias_restantes < 0:
        puntaje += 60
    elif dias_restantes == 0:
        puntaje += 55
    elif dias_restantes == 1:
        puntaje += 45
    elif dias_restantes <= 3:
        puntaje += 35
    elif dias_restantes <= 7:
        puntaje += 25
    else:
        puntaje += 10
    puntaje += {"Alta": 35, "Media": 22, "Baja": 10}.get(prioridad, 16)
    try:
        puntaje += int(dificultad or 3) * 8
    except Exception:
        puntaje += 24
    if estado == "Pendiente":
        puntaje += 15
    elif estado == "En proceso":
        puntaje += 6
    return puntaje


def estimar_horas_tarea(tarea: dict) -> float:
    """Estima horas según tipo de actividad + dificultad + urgencia.

    Reglas base:
    - Tarea: actividad básica y más fácil.
    - Monografía: demanda aproximadamente una semana de trabajo distribuido.
    - Práctica calificada: requiere repaso, pero menos que parcial/final.
    - Examen parcial: alta preparación.
    - Examen final: preparación máxima.
    La dificultad del curso multiplica la carga.
    """
    dificultad = int(tarea.get("dificultad") or 3)
    prioridad = tarea.get("prioridad") or "Media"
    estado = tarea.get("estado") or "Pendiente"
    tipo = (tarea.get("tipo_actividad") or "Tarea").lower()

    if "final" in tipo:
        horas = 9.0
    elif "parcial" in tipo:
        horas = 7.0
    elif "monografía" in tipo or "monografia" in tipo:
        horas = 8.0
    elif "práctica" in tipo or "practica" in tipo:
        horas = 4.5
    else:
        horas = 2.0

    # Ajuste por dificultad: dificultad 5 puede casi duplicar la carga de una tarea simple.
    factor_dificultad = {1: 0.75, 2: 0.9, 3: 1.0, 4: 1.25, 5: 1.55}.get(dificultad, 1.0)
    horas *= factor_dificultad

    if prioridad == "Alta":
        horas *= 1.15
    elif prioridad == "Baja":
        horas *= 0.9
    if estado == "En proceso":
        horas *= 0.70

    entrega = normalizar_fecha(tarea.get("fecha_entrega"), date.today() + timedelta(days=15))
    dias = (entrega - date.today()).days
    # Si vence muy pronto, concentramos más horas, pero el plan no debe pasar del vencimiento.
    if dias <= 1:
        horas *= 1.15
    elif dias <= 3:
        horas *= 1.08

    return round(min(max(horas, 0.75), 18.0), 2)


def construir_ocupados_por_fecha(
    fechas: list[date],
    horarios_clase: list[dict] | None,
    incluir_descansos: bool = True,
    almuerzo_inicio: str = "13:00",
    almuerzo_fin: str = "14:00",
) -> dict[str, list[tuple[float, float, str]]]:
    ocupados: dict[str, list[tuple[float, float, str]]] = {f.isoformat(): [] for f in fechas}
    for f in fechas:
        key = f.isoformat()
        if incluir_descansos:
            # No se planifica en madrugada/noche tardía; almuerzo y descanso breve se muestran como ocupados.
            ocupados[key].append((0.0, 7.0, "Descanso"))
            ocupados[key].append((_time_to_float(almuerzo_inicio), _time_to_float(almuerzo_fin), "Almuerzo"))
            ocupados[key].append((23.0, 24.0, "Descanso"))
    for h in horarios_clase or []:
        dia = h.get("dia")
        for f in fechas:
            if dia_de_fecha(f) == dia:
                ocupados[f.isoformat()].append((_time_to_float(h.get("inicio")), _time_to_float(h.get("fin")), "Clase"))
    for key in ocupados:
        ocupados[key].sort(key=lambda x: x[0])
    return ocupados


def bloques_descanso_para_fechas(fechas: list[date], almuerzo_inicio="13:00", almuerzo_fin="14:00") -> list[dict]:
    bloques = []
    for f in fechas:
        bloques.append({
            "tipo": "Almuerzo",
            "fecha": f.isoformat(),
            "dia": dia_de_fecha(f),
            "inicio": almuerzo_inicio,
            "fin": almuerzo_fin,
            "curso": "Almuerzo",
            "actividad": "Pausa para almorzar y descansar",
            "tarea_origen": "Descanso",
            "prioridad": "Descanso",
            "color": "#FDE68A",
        })
    return bloques


def buscar_slot_en_fecha(
    fecha: date,
    duracion: float,
    ocupados: dict[str, list[tuple[float, float, str]]],
    preferencia_tarde: bool = False,
) -> tuple[float, float] | None:
    key = fecha.isoformat()
    # Rangos recomendados: mañana, tarde y noche temprana. No se usa madrugada ni post 23:00.
    rangos = [(8.0, 12.5), (14.0, 17.5), (18.0, 22.5)]
    if preferencia_tarde:
        rangos = [(14.0, 17.5), (18.0, 22.5), (8.0, 12.5)]
    for ini_r, fin_r in rangos:
        t = ini_r
        while t + duracion <= fin_r + 1e-6:
            cruza = False
            for a, b, _ in ocupados.get(key, []):
                if _se_cruza(t, t + duracion, a, b):
                    cruza = True
                    t = max(t + 0.25, b)
                    break
            if not cruza:
                ocupados[key].append((t, t + duracion, "Estudio"))
                ocupados[key].sort(key=lambda x: x[0])
                return t, t + duracion
            t += 0.25
    return None


def generar_plan_calendario_respaldo(
    tareas: list[dict],
    horarios_clase: list[dict] | None,
    horas_disponibles_semana: float,
    nivel_riesgo: str,
    fecha_inicio: date | None = None,
    horizonte_dias: int = 7,
    incluir_descansos: bool = True,
    almuerzo_inicio: str = "13:00",
    almuerzo_fin: str = "14:00",
) -> list[dict]:
    """Planificador determinístico: respeta fecha actual, vencimientos, clases y pausas.

    Reglas principales:
    - Nunca coloca avances después de la fecha de entrega.
    - Usa fecha_inicio como hoy por defecto.
    - Cursos más difíciles reciben más horas y bloques.
    - Bloquea clases, almuerzo y descanso nocturno.
    """
    fecha_inicio = fecha_inicio or date.today()
    fechas = _rango_fechas(fecha_inicio, horizonte_dias)
    fecha_fin = fechas[-1]
    ocupados = construir_ocupados_por_fecha(fechas, horarios_clase, incluir_descansos, almuerzo_inicio, almuerzo_fin)

    tareas_activas = []
    for tarea in tareas or []:
        if tarea.get("estado") == "Completada":
            continue
        t = dict(tarea)
        entrega = normalizar_fecha(t.get("fecha_entrega"), fecha_inicio + timedelta(days=14))
        t["fecha_entrega_date"] = entrega
        t["puntaje"] = calcular_puntaje_planificacion(t.get("fecha_entrega"), t.get("prioridad"), t.get("dificultad"), t.get("estado"))
        t["horas_estimadas"] = estimar_horas_tarea(t)
        tareas_activas.append(t)

    tareas_activas.sort(key=lambda x: (x["fecha_entrega_date"], -x["puntaje"]))
    if not tareas_activas:
        return bloques_descanso_para_fechas(fechas, almuerzo_inicio, almuerzo_fin) if incluir_descansos else []

    # Horas máximas en horizonte. Para vista mensual escalamos por semanas disponibles.
    semanas_equiv = max(1.0, horizonte_dias / 7)
    horas_maximas = max(1.0, float(horas_disponibles_semana or 7) * semanas_equiv)
    horas_usadas = 0.0
    bloques: list[dict] = []
    if incluir_descansos:
        bloques.extend(bloques_descanso_para_fechas(fechas, almuerzo_inicio, almuerzo_fin))

    for idx, tarea in enumerate(tareas_activas):
        if horas_usadas >= horas_maximas - 0.1:
            break
        entrega = tarea["fecha_entrega_date"]
        if entrega < fecha_inicio:
            # Vencida: bloque de recuperación en la primera fecha posible.
            fechas_validas = [fecha_inicio]
            vencida = True
        else:
            limite = min(entrega, fecha_fin)
            fechas_validas = [f for f in fechas if fecha_inicio <= f <= limite]
            vencida = False
        if not fechas_validas:
            continue

        horas_objetivo = min(tarea["horas_estimadas"], max(0.0, horas_maximas - horas_usadas))
        dificultad = int(tarea.get("dificultad") or 3)
        duracion_base = 1.5 if dificultad >= 4 or tarea.get("prioridad") == "Alta" else 1.0
        duracion_base = min(2.0, max(0.75, duracion_base))
        avance = 0
        horas_asignadas = 0.0
        # Repartimos desde hoy hasta máximo fecha de entrega. Si vence pronto, se concentra pero no pasa de entrega.
        ciclo_fechas = fechas_validas[:]
        while horas_asignadas < horas_objetivo - 0.1 and horas_usadas < horas_maximas - 0.1:
            progreso = False
            for f in ciclo_fechas:
                restante = min(horas_objetivo - horas_asignadas, horas_maximas - horas_usadas)
                if restante <= 0.1:
                    break
                duracion = min(duracion_base, restante)
                if duracion < 0.5:
                    duracion = 0.5
                slot = buscar_slot_en_fecha(f, duracion, ocupados, preferencia_tarde=(dificultad >= 4))
                if not slot:
                    continue
                ini, fin = slot
                avance += 1
                if vencida:
                    actividad = "Recuperar tarea vencida y definir entrega urgente"
                    prioridad = "Alta"
                    color = "#FCA5A5"
                elif avance == 1:
                    tipo_act = tarea.get("tipo_actividad", "Tarea")
                    if "Examen" in tipo_act:
                        actividad = "Repasar teoría base y organizar temas críticos"
                    elif "Monografía" in tipo_act:
                        actividad = "Definir estructura, fuentes y primer esquema"
                    elif "Práctica" in tipo_act:
                        actividad = "Repasar fórmulas y resolver ejercicios tipo"
                    else:
                        actividad = "Revisar indicaciones y avanzar primera parte"
                    prioridad = tarea.get("prioridad", "Media")
                    color = COLORES_ESTUDIO[idx % len(COLORES_ESTUDIO)]
                elif horas_asignadas + duracion >= horas_objetivo - 0.1 or f == entrega:
                    tipo_act = tarea.get("tipo_actividad", "Tarea")
                    if "Examen" in tipo_act:
                        actividad = "Simulacro, repaso final y puntos débiles"
                    elif "Monografía" in tipo_act:
                        actividad = "Revisar, corregir citas y dejar listo para entrega"
                    elif "Práctica" in tipo_act:
                        actividad = "Practicar ejercicios finales y revisar errores"
                    else:
                        actividad = "Revisar, corregir y dejar listo para entrega"
                    prioridad = tarea.get("prioridad", "Media")
                    color = COLORES_ESTUDIO[idx % len(COLORES_ESTUDIO)]
                else:
                    tipo_act = tarea.get("tipo_actividad", "Tarea")
                    if "Examen" in tipo_act:
                        actividad = "Estudio profundo por temas y práctica guiada"
                    elif "Monografía" in tipo_act:
                        actividad = "Redactar desarrollo y consolidar contenido"
                    elif "Práctica" in tipo_act:
                        actividad = "Resolver batería de ejercicios"
                    else:
                        actividad = "Desarrollar avance principal de la tarea"
                    prioridad = tarea.get("prioridad", "Media")
                    color = COLORES_ESTUDIO[idx % len(COLORES_ESTUDIO)]
                bloques.append({
                    "tipo": "Estudio",
                    "fecha": f.isoformat(),
                    "dia": dia_de_fecha(f),
                    "inicio": _float_to_time(ini),
                    "fin": _float_to_time(fin),
                    "curso": tarea.get("curso", "Curso"),
                    "actividad": actividad,
                    "tarea_origen": tarea.get("titulo", "Tarea"),
                    "tipo_actividad": tarea.get("tipo_actividad", "Tarea"),
                    "prioridad": prioridad,
                    "color": color,
                    "fecha_entrega": entrega.isoformat(),
                })
                horas_asignadas += duracion
                horas_usadas += duracion
                progreso = True
                if horas_asignadas >= horas_objetivo - 0.1:
                    break
            if not progreso:
                break
    return bloques


# Compatibilidad con versiones previas.
def generar_plan_semanal(tareas, horas_disponibles_semana, nivel_riesgo):
    bloques = generar_plan_calendario_respaldo(tareas, [], horas_disponibles_semana, nivel_riesgo, date.today(), 7)
    agrupado = []
    for dia in DIAS:
        tareas_dia = [b for b in bloques if b.get("dia") == dia and b.get("tipo") == "Estudio"]
        agrupado.append({
            "dia": dia,
            "horas_disponibles": sum((_time_to_float(b["fin"]) - _time_to_float(b["inicio"])) for b in tareas_dia),
            "recomendacion": "Plan generado automáticamente respetando vencimientos y horarios.",
            "tareas": tareas_dia,
        })
    return agrupado
