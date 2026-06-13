import json
import re

from google import genai
from google.genai import types

from config import get_setting

MODELO_IA = get_setting("GEMINI_MODEL", "gemini-2.0-flash-lite")

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
        raise RuntimeError("Falta configurar GEMINI_API_KEY en Streamlit Secrets o en el archivo .env local.")
    return key


def _client():
    return genai.Client(api_key=_api_key())


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


def _normalizar_resultado(datos: dict, respuestas: dict[int, int]):
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
    if datos["nivel_riesgo"] not in ["Bajo", "Medio", "Alto"]:
        datos["nivel_riesgo"] = "Medio"

    for campo in ["indice_estres", "indice_procrastinacion", "indice_motivacion", "indice_estado_animo"]:
        datos[campo] = round(max(1.0, min(5.0, float(datos[campo]))), 2)

    datos["alerta_emocional"] = 1 if int(datos["alerta_emocional"]) == 1 or int(respuestas[20]) >= 4 else 0
    datos["exito"] = True
    return datos


def _generar_texto(prompt: str, temperature: float = 0.3, json_mode: bool = False) -> str:
    config_kwargs = {"temperature": temperature}
    if json_mode:
        config_kwargs["response_mime_type"] = "application/json"

    response = _client().models.generate_content(
        model=MODELO_IA,
        contents=prompt,
        config=types.GenerateContentConfig(**config_kwargs),
    )
    return response.text or ""


def generar_diagnostico_ia(nombre_estudiante: str, horas_estudio_dia: float, promedio_ponderado: float, respuestas: dict[int, int]):
    respuestas_texto = "\n".join([
        f"Pregunta {i}: {PREGUNTAS_TEXTO[i]} Respuesta: {respuestas[i]}/5"
        for i in range(1, 21)
    ])

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
- Pregunta 20: señal de alerta emocional si la respuesta es alta

Devuelve SOLO JSON válido, sin markdown ni texto adicional:
{{
  "puntaje_riesgo": número entero de 0 a 100,
  "nivel_riesgo": "Bajo" o "Medio" o "Alto",
  "indice_estres": número decimal de 1 a 5,
  "indice_procrastinacion": número decimal de 1 a 5,
  "indice_motivacion": número decimal de 1 a 5,
  "indice_estado_animo": número decimal de 1 a 5,
  "alerta_emocional": 0 o 1,
  "diagnostico_general": "texto breve",
  "recomendacion_estudiante": "texto breve",
  "recomendacion_tutoria": "texto breve"
}}

Criterios:
- Considera promedio ponderado, horas de estudio, estrés, procrastinación, motivación y estado de ánimo.
- Si la pregunta 20 es 4 o 5, alerta_emocional debe ser 1.
- Si hay promedio bajo, poco estudio, alta procrastinación y señales de malestar, el riesgo debe subir.
- Si hay buen promedio, buena motivación y pocas señales de estrés/procrastinación, el riesgo debe bajar.
- Sé prudente: orientación académica, no diagnóstico clínico.
"""

    try:
        contenido = _generar_texto(prompt, temperature=0.2, json_mode=True)
        datos = extraer_json(contenido)
        if datos is None:
            return {
                "exito": False,
                "error": "La IA no devolvió un JSON válido.",
                "respuesta_original": contenido,
            }
        return _normalizar_resultado(datos, respuestas)
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
    cursos_texto = "No hay cursos registrados."
    if cursos_dificultad:
        cursos_texto = "\n".join([f"- {curso[0]}: dificultad {curso[1]}/5" for curso in cursos_dificultad])

    prompt = f"""
Eres AURA, un coach académico universitario.
No des diagnósticos médicos ni psicológicos.

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

Sé concreto, empático y práctico.
"""
    try:
        return _generar_texto(prompt, temperature=0.4, json_mode=False)
    except Exception as error:
        return f"""
No se pudo conectar con la IA en la nube.

Recomendación básica:
Tu nivel de riesgo académico actual es {nivel_riesgo}. Prioriza las tareas pendientes,
organiza un bloque de estudio corto y actualiza tu avance en AURA.

Detalle técnico:
{error}
"""
