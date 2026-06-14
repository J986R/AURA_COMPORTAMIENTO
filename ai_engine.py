import json
import re
from typing import Any

import requests

from config import get_setting


MODELO_IA = get_setting("GEMINI_MODEL", "gemini-2.5-flash-lite")

PREGUNTAS_TEXTO = {
    1: "¿Te sientes abrumado por la cantidad de tareas, trabajos o exámenes?",
    2: "¿Sientes que no tienes suficiente tiempo para cumplir con tus responsabilidades académicas?",
    3: "¿Te cuesta relajarte incluso cuando tienes tiempo libre?",
    4: "¿Sientes cansancio mental después de estudiar o asistir a clases?",
    5: "¿Te preocupas demasiado por tus calificaciones o resultados académicos?",
    6: "¿Dejas tus tareas o trabajos para el último momento?",
    7: "¿Te distraes fácilmente cuando intentas estudiar?",
    8: "¿Evitas empezar una tarea porque te parece difícil, larga o aburrida?",
    9: "¿Te cuesta mantener una rutina de estudio constante?",
    10: "¿Empiezas a estudiar recién cuando sientes presión por la fecha de entrega o examen?",
    11: "¿Te sientes motivado para asistir a clases y aprender?",
    12: "¿Tienes claro por qué estás estudiando tu carrera?",
    13: "¿Sientes entusiasmo por lograr tus metas académicas?",
    14: "¿Sientes que lo que estudias será útil para tu futuro profesional?",
    15: "¿Te esfuerzas por mejorar aunque un curso sea difícil?",
    16: "¿Has sentido tristeza, vacío o desánimo durante varios días?",
    17: "¿Has perdido interés en actividades que antes disfrutabas?",
    18: "¿Te has sentido con poca energía o cansancio la mayor parte del día?",
    19: "¿Te ha costado concentrarte en clases, tareas o estudios?",
    20: "¿Has sentido que tus problemas académicos o personales son demasiado difíciles de manejar?",
}


def _api_key() -> str:
    key = get_setting("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("Falta configurar GEMINI_API_KEY en Streamlit Secrets o .env.")
    return str(key)


def nivel_por_puntaje(puntaje: Any) -> str:
    try:
        p = int(float(puntaje))
    except Exception:
        return "Medio"
    if p >= 70:
        return "Alto"
    if p >= 40:
        return "Medio"
    return "Bajo"


def extraer_json(texto: str):
    try:
        return json.loads(texto)
    except Exception:
        pass
    coincidencia = re.search(r"\{[\s\S]*\}", texto or "")
    if coincidencia:
        try:
            return json.loads(coincidencia.group())
        except Exception:
            return None
    return None


def _generar_texto(prompt: str, temperature: float = 0.3, json_mode: bool = False) -> str:
    api_key = _api_key()
    modelo = str(get_setting("GEMINI_MODEL", MODELO_IA))
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"
    generation_config = {"temperature": temperature}
    if json_mode:
        generation_config["responseMimeType"] = "application/json"

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": generation_config,
    }
    response = requests.post(url, json=payload, timeout=90)
    if response.status_code != 200:
        raise RuntimeError(f"Error Gemini API {response.status_code}: {response.text}")
    data = response.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        raise RuntimeError(f"Respuesta inesperada de Gemini: {data}")


def _normalizar_indice(valor, defecto=3.0):
    try:
        return round(max(1.0, min(5.0, float(valor))), 2)
    except Exception:
        return defecto


def _normalizar_resultado_diagnostico(datos: dict, respuestas: dict):
    campos = [
        "puntaje_riesgo",
        "nivel_riesgo",
        "indice_estres",
        "indice_procrastinacion",
        "indice_motivacion",
        "indice_estado_animo",
        "alerta_emocional",
        "diagnostico_general",
        "recomendacion_estudiante",
        "recomendacion_tutoria",
    ]
    for campo in campos:
        if campo not in datos:
            raise ValueError(f"Falta el campo obligatorio: {campo}")

    datos["puntaje_riesgo"] = max(0, min(100, int(float(datos["puntaje_riesgo"]))))
    # El nivel se fuerza por puntaje para evitar contradicciones como 1/100 y riesgo medio.
    datos["nivel_riesgo"] = nivel_por_puntaje(datos["puntaje_riesgo"])
    datos["indice_estres"] = _normalizar_indice(datos["indice_estres"])
    datos["indice_procrastinacion"] = _normalizar_indice(datos["indice_procrastinacion"])
    datos["indice_motivacion"] = _normalizar_indice(datos["indice_motivacion"])
    datos["indice_estado_animo"] = _normalizar_indice(datos["indice_estado_animo"])
    datos["alerta_emocional"] = 1 if int(datos.get("alerta_emocional", 0)) == 1 or int(respuestas[20]) >= 4 else 0
    datos["diagnostico_general"] = str(datos["diagnostico_general"])
    datos["recomendacion_estudiante"] = str(datos["recomendacion_estudiante"])
    datos["recomendacion_tutoria"] = str(datos["recomendacion_tutoria"])
    datos["exito"] = True
    return datos


def generar_diagnostico_ia(nombre_estudiante: str, horas_estudio_dia: float, promedio_ponderado: float, respuestas: dict):
    respuestas_texto = "\n".join(
        [f"Pregunta {i}: {PREGUNTAS_TEXTO[i]} Respuesta: {respuestas[i]}/5" for i in range(1, 21)]
    )

    prompt = f"""
Eres AURA, un sistema de acompañamiento académico universitario.

Tu tarea es generar un diagnóstico académico y de bienestar REFERENCIAL.
No debes dar diagnósticos médicos, clínicos ni psicológicos.
No afirmes que el estudiante tiene depresión, ansiedad u otro trastorno.
Solo habla de señales académicas, hábitos, bienestar percibido y necesidad de seguimiento.

Datos del estudiante:
- Nombre: {nombre_estudiante}
- Horas de estudio por día: {horas_estudio_dia}
- Promedio ponderado: {promedio_ponderado}

Escala:
1 = Nunca
2 = Casi nunca
3 = A veces
4 = Casi siempre
5 = Siempre

Respuestas:
{respuestas_texto}

Dimensiones:
- Preguntas 1 a 5: estrés
- Preguntas 6 a 10: procrastinación
- Preguntas 11 a 15: motivación
- Preguntas 16 a 20: estado de ánimo
- Pregunta 20: señal de alerta emocional si la respuesta es 4 o 5

Devuelve SOLO JSON válido, sin markdown ni texto adicional.

Formato obligatorio:
{{
  "puntaje_riesgo": 0,
  "nivel_riesgo": "Bajo",
  "indice_estres": 1.0,
  "indice_procrastinacion": 1.0,
  "indice_motivacion": 5.0,
  "indice_estado_animo": 1.0,
  "alerta_emocional": 0,
  "diagnostico_general": "texto breve",
  "recomendacion_estudiante": "texto breve",
  "recomendacion_tutoria": "texto breve"
}}

Criterios obligatorios de coherencia:
- puntaje_riesgo debe estar entre 0 y 100.
- nivel_riesgo debe seguir estos rangos: 0-39 Bajo, 40-69 Medio, 70-100 Alto.
- Si la pregunta 20 es 4 o 5, alerta_emocional debe ser 1.
- Si hay promedio bajo, poco estudio, alta procrastinación y señales de malestar, el riesgo debe subir.
- Si hay buen promedio, buena motivación y pocas señales de estrés/procrastinación, el riesgo debe bajar.
- Sé prudente: orientación académica, no diagnóstico clínico.
"""
    try:
        contenido = _generar_texto(prompt, temperature=0.2, json_mode=True)
        datos = extraer_json(contenido)
        if datos is None:
            return {"exito": False, "error": "La IA no devolvió un JSON válido.", "respuesta_original": contenido}
        return _normalizar_resultado_diagnostico(datos, respuestas)
    except Exception as error:
        return {"exito": False, "error": str(error), "respuesta_original": ""}


def generar_recomendacion_ia(
    nombre_estudiante: str,
    horas_estudio: float,
    promedio_actual: float,
    tareas_pendientes_diagnostico: int,
    nivel_estres: float,
    nivel_motivacion: float,
    nivel_procrastinacion: float,
    puntaje_riesgo: int,
    nivel_riesgo: str,
    resumen_tareas: dict,
    cursos_dificultad: list,
):
    nivel_riesgo = nivel_por_puntaje(puntaje_riesgo)
    cursos_texto = "No hay cursos registrados."
    if cursos_dificultad:
        cursos_texto = "\n".join([f"- {curso[0]}: dificultad {curso[1]}/5" for curso in cursos_dificultad])

    prompt = f"""
Eres AURA, un coach académico universitario.
No des diagnósticos médicos ni psicológicos.

IMPORTANTE: No cambies el nivel de riesgo. Debes usar exactamente este nivel: {nivel_riesgo}.
El puntaje asociado es {puntaje_riesgo}/100. Si mencionas el riesgo, debe coincidir con ese nivel.

Datos del estudiante:
- Nombre: {nombre_estudiante}
- Horas de estudio por día: {horas_estudio}
- Promedio ponderado: {promedio_actual}
- Nivel de estrés: {nivel_estres}/5
- Nivel de motivación: {nivel_motivacion}/5
- Nivel de procrastinación: {nivel_procrastinacion}/5
- Puntaje de riesgo académico: {puntaje_riesgo}/100
- Nivel de riesgo académico: {nivel_riesgo}

Resumen de tareas:
- Total: {resumen_tareas['total']}
- Completadas: {resumen_tareas['completadas']}
- Pendientes: {resumen_tareas['pendientes']}
- Alta prioridad: {resumen_tareas['alta_prioridad']}
- Cumplimiento: {resumen_tareas['porcentaje_cumplimiento']}%

Cursos con mayor dificultad:
{cursos_texto}

Responde en español con esta estructura:
1. Diagnóstico breve.
2. Prioridad principal para hoy.
3. Plan de acción de 3 pasos.
4. Consejo de organización.
5. Mensaje motivacional final.

Sé concreto, empático y práctico. No contradigas el nivel de riesgo entregado.
"""
    try:
        return _generar_texto(prompt, temperature=0.35, json_mode=False)
    except Exception as error:
        return f"""
No se pudo conectar con la IA en la nube.

Recomendación básica:
Tu nivel de riesgo académico actual es {nivel_riesgo}. Prioriza las tareas pendientes,
organiza un bloque de estudio corto y actualiza tu avance en AURA.

Detalle técnico:
{error}
"""


def generar_plan_semanal_ia(nombre_estudiante: str, diagnostico: dict, tareas: list, horas_disponibles_semana: float):
    tareas_activas = [t for t in tareas if t.get("estado") != "Completada"]
    if not tareas_activas:
        return {"exito": True, "plan": []}

    tareas_texto = json.dumps(tareas_activas, ensure_ascii=False, indent=2)
    prompt = f"""
Eres AURA, un planificador académico inteligente para estudiantes universitarios.

Objetivo: crear un plan semanal realista. No pongas una tarea grande completa en un solo día si por su dificultad, fecha o descripción conviene dividirla.
Divide tareas complejas en avances pequeños durante varios días.

Datos del estudiante:
- Nombre: {nombre_estudiante}
- Horas disponibles en la semana: {horas_disponibles_semana}
- Promedio ponderado: {diagnostico.get('promedio_ponderado')}
- Nivel de riesgo académico: {diagnostico.get('nivel_riesgo')}
- Puntaje de riesgo: {diagnostico.get('puntaje_riesgo')}/100
- Estrés: {diagnostico.get('indice_estres')}/5
- Procrastinación: {diagnostico.get('indice_procrastinacion')}/5
- Motivación: {diagnostico.get('indice_motivacion')}/5
- Estado de ánimo: {diagnostico.get('indice_estado_animo')}/5

Tareas activas en JSON:
{tareas_texto}

Reglas:
- Distribuye las horas en 7 días: Lunes a Domingo.
- Si una tarea es difícil, extensa o de prioridad alta, divídela en subactividades.
- No asignes más horas de las disponibles en la semana.
- Considera fechas de entrega, prioridad y dificultad.
- Incluye descansos o repaso ligero si el estudiante tiene estrés alto.
- Usa actividades concretas: "leer fuentes", "hacer borrador", "resolver 5 ejercicios", "revisar y entregar".

Devuelve SOLO JSON válido con este formato:
{{
  "plan": [
    {{
      "dia": "Lunes",
      "horas_disponibles": 2.0,
      "recomendacion": "texto breve",
      "tareas": [
        {{
          "curso": "nombre del curso",
          "actividad": "actividad concreta",
          "tarea_origen": "título de la tarea",
          "prioridad": "Alta/Media/Baja",
          "fecha_entrega": "YYYY-MM-DD",
          "horas_recomendadas": 1.0
        }}
      ]
    }}
  ]
}}
"""
    try:
        contenido = _generar_texto(prompt, temperature=0.25, json_mode=True)
        datos = extraer_json(contenido)
        if datos is None or "plan" not in datos:
            return {"exito": False, "error": "La IA no devolvió un plan JSON válido.", "respuesta_original": contenido}
        plan = datos["plan"]
        # Normalización mínima.
        dias_validos = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        plan_normalizado = []
        for idx, item in enumerate(plan):
            dia = item.get("dia", dias_validos[min(idx, 6)])
            tareas_dia = item.get("tareas", []) or []
            plan_normalizado.append(
                {
                    "dia": dia,
                    "horas_disponibles": float(item.get("horas_disponibles", 0) or 0),
                    "recomendacion": str(item.get("recomendacion", "")),
                    "tareas": tareas_dia,
                }
            )
        return {"exito": True, "plan": plan_normalizado}
    except Exception as error:
        return {"exito": False, "error": str(error), "respuesta_original": ""}
