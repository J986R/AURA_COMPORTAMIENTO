from pathlib import Path
from datetime import date, datetime, timedelta, time
import html
import json

import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

from ai_engine import generar_diagnostico_ia, generar_plan_calendario_ia, generar_recomendacion_ia, nivel_por_puntaje
from boleta_parser import parsear_boleta_matricula
from database import (
    actualizar_curso,
    actualizar_estado_tarea,
    actualizar_tarea,
    actualizar_estudiante,
    actualizar_usuario,
    autenticar_usuario,
    crear_tablas,
    eliminar_curso,
    eliminar_estudiante,
    eliminar_tarea,
    eliminar_usuario,
    eliminar_horario_clase,
    existe_curso,
    existe_tarea,
    guardar_diagnostico_ia,
    guardar_plan_semanal,
    guardar_recomendacion_coach,
    importar_boleta_matricula,
    limpiar_horarios_clase,
    listar_cursos_por_estudiante,
    listar_estudiantes,
    listar_horarios_clase,
    listar_tareas_para_planificador,
    listar_tareas_por_estudiante,
    listar_usuarios,
    obtener_curso_por_id,
    obtener_cursos_mayor_dificultad,
    obtener_estudiante_por_id,
    obtener_panel_tutoria,
    obtener_tarea_por_id,
    obtener_tabla_completa,
    obtener_ultimo_diagnostico,
    obtener_ultimo_diagnostico_detallado,
    obtener_ultimo_plan_semanal,
    obtener_ultima_recomendacion_coach,
    obtener_resumen_tareas,
    obtener_usuario_por_id,
    registrar_curso,
    registrar_estudiante,
    registrar_horario_clase,
    registrar_tarea,
    registrar_usuario,
)
from planner import generar_plan_calendario_respaldo, dias_restantes_mes
from report_generator import crear_excel_reporte, crear_pdf_reporte

LOGO_PATH = Path(__file__).parent / "assets" / "logo_aura.png"
AUDIO_PATH = Path(__file__).parent / "assets" / "background.mp3"

st.set_page_config(page_title="AURA - Coach Académico Inteligente", page_icon="🎓", layout="wide")

PREGUNTAS_DIAGNOSTICO = [
    ("¿Te sientes abrumado por la cantidad de tareas, trabajos o exámenes?", "Estrés"),
    ("¿Sientes que no tienes suficiente tiempo para cumplir con tus responsabilidades académicas?", "Estrés"),
    ("¿Te cuesta relajarte incluso cuando tienes tiempo libre?", "Estrés"),
    ("¿Sientes cansancio mental después de estudiar o asistir a clases?", "Estrés"),
    ("¿Te preocupas demasiado por tus calificaciones o resultados académicos?", "Estrés"),
    ("¿Dejas tus tareas o trabajos para el último momento?", "Procrastinación"),
    ("¿Te distraes fácilmente cuando intentas estudiar?", "Procrastinación"),
    ("¿Evitas empezar una tarea porque te parece difícil, larga o aburrida?", "Procrastinación"),
    ("¿Te cuesta mantener una rutina de estudio constante?", "Procrastinación"),
    ("¿Empiezas a estudiar recién cuando sientes presión por la fecha de entrega o examen?", "Procrastinación"),
    ("¿Te sientes motivado para asistir a clases y aprender?", "Motivación"),
    ("¿Tienes claro por qué estás estudiando tu carrera?", "Motivación"),
    ("¿Sientes entusiasmo por lograr tus metas académicas?", "Motivación"),
    ("¿Sientes que lo que estudias será útil para tu futuro profesional?", "Motivación"),
    ("¿Te esfuerzas por mejorar aunque un curso sea difícil?", "Motivación"),
    ("¿Has sentido tristeza, vacío o desánimo durante varios días?", "Estado de ánimo"),
    ("¿Has perdido interés en actividades que antes disfrutabas?", "Estado de ánimo"),
    ("¿Te has sentido con poca energía o cansancio la mayor parte del día?", "Estado de ánimo"),
    ("¿Te ha costado concentrarte en clases, tareas o estudios?", "Estado de ánimo"),
    ("¿Has sentido que tus problemas académicos o personales son demasiado difíciles de manejar?", "Estado de ánimo / alerta emocional"),
]

ESCALA_OPCIONES = ["1 - Nunca", "2 - Casi nunca", "3 - A veces", "4 - Casi siempre", "5 - Siempre"]
DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
PALETA = ["#BDE0FE", "#A7F3D0", "#DDD6FE", "#FDE68A", "#FBCFE8", "#BFDBFE", "#C7D2FE"]
TIPOS_ACTIVIDAD = ["Tarea", "Monografía", "Práctica calificada", "Examen parcial", "Examen final"]
COLOR_TIPO = {"Tarea": "#A7F3D0", "Monografía": "#DDD6FE", "Práctica calificada": "#FDE68A", "Examen parcial": "#FBCFE8", "Examen final": "#FCA5A5"}


def aplicar_estilos():
    st.markdown(
        """
        <style>
        :root{
            --aura-ink:#24324B;
            --aura-muted:#64748B;
            --aura-bg:#F7F9FF;
            --aura-card:#FFFFFF;
            --aura-blue:#BDE0FE;
            --aura-cyan:#A7F3D0;
            --aura-purple:#DDD6FE;
            --aura-yellow:#FDE68A;
            --aura-pink:#FBCFE8;
            --aura-accent:#60A5FA;
        }
        html, body, [data-testid="stAppViewContainer"]{
            background:
                radial-gradient(circle at top left, rgba(189,224,254,.55), transparent 28%),
                radial-gradient(circle at top right, rgba(221,214,254,.55), transparent 28%),
                linear-gradient(180deg,#FBFDFF 0%,#F7F9FF 100%);
            color:var(--aura-ink);
        }
        .block-container{padding-top:1.2rem;max-width:1280px;}
        h1,h2,h3{letter-spacing:-0.03em;color:var(--aura-ink);}
        p, label, .stMarkdown{color:var(--aura-ink);}
        div[data-testid="stSidebar"]{
            background:linear-gradient(180deg,#F8FBFF 0%,#EEF5FF 55%,#F6F0FF 100%);
            border-right:1px solid rgba(96,165,250,.18);
        }
        div[data-testid="stSidebar"] *{color:#24324B !important;}
        .aura-hero{
            border-radius:30px;
            padding:28px 32px;
            background:linear-gradient(135deg,#BDE0FE 0%,#A7F3D0 48%,#DDD6FE 100%);
            color:#24324B;
            box-shadow:0 18px 45px rgba(96,165,250,.18);
            margin-bottom:20px;
            border:1px solid rgba(255,255,255,.72);
        }
        .aura-hero h1{margin:0;font-size:2.15rem;color:#24324B;}
        .aura-hero p{margin:8px 0 0 0;color:#475569;}
        .aura-card{
            background:rgba(255,255,255,.88);
            backdrop-filter:blur(10px);
            border:1px solid rgba(148,163,184,.16);
            border-radius:24px;
            padding:18px 20px;
            box-shadow:0 10px 30px rgba(96,165,250,.08);
            margin-bottom:16px;
        }
        .aura-pill{
            display:inline-flex;align-items:center;border-radius:999px;padding:7px 13px;
            background:rgba(255,255,255,.62);color:#24324B;font-weight:800;font-size:.88rem;margin-right:8px;
            border:1px solid rgba(96,165,250,.16);
        }
        .stButton > button, .stDownloadButton > button{
            border-radius:16px !important;
            border:1px solid rgba(96,165,250,.30) !important;
            background:linear-gradient(135deg,#BDE0FE,#DDD6FE) !important;
            color:#24324B !important;font-weight:800 !important;padding:.58rem 1.05rem !important;
            box-shadow:0 8px 18px rgba(96,165,250,.14);
            transition:all .16s ease-in-out;
        }
        .stButton > button:hover, .stDownloadButton > button:hover{transform:translateY(-1px);filter:saturate(1.1);}
        div[data-testid="stMetric"]{
            background:rgba(255,255,255,.90);border:1px solid rgba(148,163,184,.14);
            border-radius:22px;padding:14px 16px;box-shadow:0 8px 24px rgba(96,165,250,.08);
        }
        div[data-testid="stMetricValue"]{color:#24324B;}
        div[data-baseweb="select"] > div, div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input, textarea{
            border-radius:14px !important;
        }
        .aura-calendar{
            background:rgba(255,255,255,.92);border:1px solid rgba(148,163,184,.18);
            border-radius:26px;overflow:hidden;box-shadow:0 12px 34px rgba(96,165,250,.10);margin-top:10px;
        }
        .aura-cal-head{display:grid;grid-template-columns:78px repeat(7,1fr);background:linear-gradient(90deg,#EFF6FF,#F5F3FF);border-bottom:1px solid #E5E7EB;}
        .aura-cal-head div{padding:13px 10px;font-weight:900;text-align:center;color:#24324B;}
        .aura-cal-body{display:grid;grid-template-columns:78px repeat(7,1fr);position:relative;}
        .aura-time-col{background:#F8FAFF;border-right:1px solid #E5E7EB;position:relative;}
        .aura-time{position:absolute;left:10px;font-size:12px;color:#64748B;transform:translateY(-8px);}
        .aura-day-col{position:relative;border-right:1px solid #E5E7EB;background-image:linear-gradient(to bottom,#E5E7EB 1px,transparent 1px);background-size:100% 60px;}
        .aura-day-col:last-child{border-right:none;}
        .aura-event{position:absolute;left:6px;right:6px;border-radius:14px;padding:8px 9px;color:#24324B;font-size:12px;line-height:1.20;overflow:hidden;box-shadow:0 8px 18px rgba(15,23,42,.11);border:1px solid rgba(255,255,255,.55);}
        .aura-event small{display:block;opacity:.86;font-weight:700;margin-top:3px;}
        .aura-event.clase{background:#BDE0FE;}
        .aura-event.estudio{background:#A7F3D0;}
        .aura-event.descanso{background:#FDE68A;}
        .aura-month{display:grid;grid-template-columns:repeat(7,1fr);gap:10px;margin-top:10px;}
        .aura-month-head{font-weight:900;text-align:center;color:#24324B;background:#EEF6FF;border-radius:14px;padding:10px;}
        .aura-month-day{min-height:132px;background:rgba(255,255,255,.92);border:1px solid rgba(148,163,184,.18);border-radius:18px;padding:10px;box-shadow:0 6px 18px rgba(96,165,250,.07);}
        .aura-month-day.empty{opacity:.35;background:#F8FAFC;}
        .aura-day-number{font-weight:900;margin-bottom:6px;color:#24324B;}
        .aura-month-event{font-size:11px;line-height:1.2;border-radius:10px;padding:5px 6px;margin-bottom:5px;color:#24324B;overflow:hidden;white-space:nowrap;text-overflow:ellipsis;border:1px solid rgba(255,255,255,.55);}
        .aura-muted{color:#64748B;font-size:.92rem;}
        
        .stTabs [data-baseweb="tab-list"]{gap:8px;background:rgba(255,255,255,.65);padding:6px;border-radius:20px;}
        .stTabs [data-baseweb="tab"]{border-radius:16px;padding:8px 16px;font-weight:800;}
        .stRadio [role="radiogroup"]{background:rgba(255,255,255,.70);border-radius:18px;padding:6px;}
        .aura-dashboard-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin:12px 0 20px 0;}
        .aura-stat{background:linear-gradient(135deg,rgba(255,255,255,.92),rgba(248,251,255,.92));border:1px solid rgba(148,163,184,.16);border-radius:24px;padding:16px;box-shadow:0 10px 26px rgba(96,165,250,.10);}
        .aura-stat .label{font-size:12px;color:#64748B;font-weight:800;text-transform:uppercase;letter-spacing:.04em;}
        .aura-stat .value{font-size:28px;color:#24324B;font-weight:950;margin-top:4px;}
        .aura-calendar-toolbar{display:flex;justify-content:space-between;align-items:center;background:#F8FAFF;border:1px solid rgba(148,163,184,.18);border-radius:28px;padding:12px 16px;margin:10px 0 8px 0;box-shadow:0 10px 28px rgba(96,165,250,.08);}
        .aura-toolbar-left{display:flex;gap:10px;align-items:center;font-weight:900;color:#24324B;}
        .aura-icon-btn{display:inline-flex;align-items:center;gap:8px;border-radius:999px;padding:9px 15px;font-weight:900;color:#24324B;background:linear-gradient(135deg,#FFFFFF,#EEF6FF);border:1px solid rgba(148,163,184,.20);}
        .aura-event.examen{background:#FCA5A5!important;color:#2A1C1C;}
        .aura-event.monografia{background:#DDD6FE!important;}
        .aura-event.practica{background:#FDE68A!important;}
        .aura-event.tarea{background:#A7F3D0!important;}
        .aura-month-event.examen{background:#FCA5A5!important;}
        .aura-month-event.monografia{background:#DDD6FE!important;}
        .aura-month-event.practica{background:#FDE68A!important;}
        .aura-month-event.tarea{background:#A7F3D0!important;}
        .aura-player{position:fixed;right:22px;bottom:22px;z-index:9999;background:rgba(255,255,255,.90);border:1px solid rgba(148,163,184,.18);border-radius:22px;padding:10px 12px;box-shadow:0 12px 28px rgba(15,23,42,.16);backdrop-filter:blur(10px);}
        @media(max-width:900px){.aura-dashboard-grid{grid-template-columns:repeat(2,minmax(0,1fr));}.aura-cal-head,.aura-cal-body{grid-template-columns:58px repeat(7,170px);overflow-x:auto;}.aura-calendar{overflow-x:auto;}}
        </style>
        """,
        unsafe_allow_html=True,
    )

@st.cache_resource(show_spinner=False)
def inicializar_bd():
    crear_tablas()
    return True


def safe_init():
    try:
        inicializar_bd()
    except Exception as error:
        st.error("No se pudo conectar o inicializar la base de datos Neon.")
        st.code(str(error))
        st.info("Verifica NEON_DATABASE_URL en Streamlit Secrets o en tu archivo .env local.")
        st.stop()


def mostrar_logo(ancho=230):
    if LOGO_PATH.exists():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(str(LOGO_PATH), width=ancho)


def mostrar_musica():
    with st.sidebar.expander("🎵 Música de fondo", expanded=False):
        st.caption("Los navegadores requieren que el usuario presione reproducir. Sube un archivo como assets/background.mp3 para activar la música.")
        if AUDIO_PATH.exists():
            st.audio(str(AUDIO_PATH), format="audio/mp3", loop=True)
        else:
            st.info("Aún no hay música cargada. Agrega assets/background.mp3 al repositorio.")


def mostrar_hero(titulo="AURA", subtitulo="Academic University Recommendation Assistant"):
    logo_html = ""
    if LOGO_PATH.exists():
        # Se usa la imagen visible de Streamlit aparte; el hero queda limpio.
        pass
    st.markdown(
        f"""
        <div class='aura-hero'>
            <span class='aura-pill'>🎓 Coach académico inteligente</span>
            <span class='aura-pill'>🤖 IA + Neon Cloud</span>
            <h1>{html.escape(titulo)}</h1>
            <p>{html.escape(subtitulo)} · Mejora rendimiento, organización y bienestar estudiantil.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def mostrar_login():
    mostrar_logo(250)
    st.title("AURA")
    st.subheader("Inicio de sesión")
    st.info("Usuario inicial: admin | Contraseña inicial: aura123")

    with st.form("form_login"):
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        boton = st.form_submit_button("🔐 Ingresar")
        if boton:
            try:
                usuario = autenticar_usuario(username, password)
            except Exception as error:
                st.error("No se pudo iniciar sesión.")
                st.code(str(error))
                return
            if usuario is None:
                st.error("Usuario o contraseña incorrectos.")
            else:
                st.session_state.usuario_logueado = usuario
                st.rerun()


def cerrar_sesion():
    st.session_state.usuario_logueado = None
    st.rerun()


def obtener_nombre_desde_texto(estudiante_texto):
    if estudiante_texto is None:
        return "Estudiante"
    return estudiante_texto.split("|")[0].strip()


def seleccionar_estudiante(label="Selecciona un estudiante"):
    usuario = st.session_state.usuario_logueado
    if usuario["rol"] == "Estudiante":
        estudiante_id = usuario["estudiante_id"]
        if estudiante_id is None:
            st.error("Este usuario estudiante no está vinculado a ningún estudiante registrado.")
            return None, None
        estudiante = obtener_estudiante_por_id(estudiante_id)
        if estudiante is None:
            st.error("No se encontró el estudiante vinculado a este usuario.")
            return None, None
        texto = f"{estudiante[1]} | Código: {estudiante[2]} | Ciclo: {estudiante[4]}"
        return estudiante_id, texto

    estudiantes = listar_estudiantes()
    if not estudiantes:
        st.warning("Primero debes registrar al menos un estudiante.")
        return None, None
    opciones = {f"{e[1]} | Código: {e[2]} | Ciclo: {e[4]}": e[0] for e in estudiantes}
    estudiante_texto = st.selectbox(label, list(opciones.keys()))
    return opciones[estudiante_texto], estudiante_texto


def num_a_escala(valor):
    try:
        valor = int(valor)
    except Exception:
        valor = 3
    valor = max(1, min(5, valor))
    return ESCALA_OPCIONES[valor - 1]


def escala_a_num(texto):
    return int(str(texto).split("-")[0].strip())


def mostrar_estado_riesgo(nivel, puntaje):
    if nivel == "Alto":
        st.error(f"Riesgo académico IA: {nivel} | Puntaje: {puntaje}/100")
    elif nivel == "Medio":
        st.warning(f"Riesgo académico IA: {nivel} | Puntaje: {puntaje}/100")
    else:
        st.success(f"Riesgo académico IA: {nivel} | Puntaje: {puntaje}/100")


def time_to_float(t):
    try:
        h, m = str(t)[:5].split(":")
        return int(h) + int(m) / 60
    except Exception:
        return 8.0


def escape(s):
    return html.escape(str(s or ""))


def fecha_a_dia(fecha_obj):
    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    return dias[fecha_obj.weekday()]


def rango_fechas(inicio, dias):
    return [inicio + timedelta(days=i) for i in range(max(1, int(dias)))]


def bloques_clase_para_calendar(horarios, fechas=None):
    bloques = []
    fechas = fechas or []
    for h in horarios or []:
        if fechas:
            for f in fechas:
                if fecha_a_dia(f) != h.get("dia"):
                    continue
                bloques.append({
                    "tipo": "Clase",
                    "fecha": f.isoformat(),
                    "dia": h.get("dia"),
                    "inicio": h.get("inicio"),
                    "fin": h.get("fin"),
                    "curso": h.get("codigo_curso") or h.get("nombre_curso"),
                    "actividad": f"{h.get('tipo','Clase')} · {h.get('aula','')}",
                    "tarea_origen": h.get("docente", ""),
                    "prioridad": "Clase",
                    "color": h.get("color") or "#BDE0FE",
                })
        else:
            bloques.append({
                "tipo": "Clase",
                "dia": h.get("dia"),
                "inicio": h.get("inicio"),
                "fin": h.get("fin"),
                "curso": h.get("codigo_curso") or h.get("nombre_curso"),
                "actividad": f"{h.get('tipo','Clase')} · {h.get('aula','')}",
                "tarea_origen": h.get("docente", ""),
                "prioridad": "Clase",
                "color": h.get("color") or "#BDE0FE",
            })
    return bloques


def _normalizar_hora(valor, defecto="08:00"):
    texto = str(valor or defecto).strip()
    if len(texto) >= 5 and texto[2] == ":":
        return texto[:5]
    try:
        partes = texto.split(":")
        h = int(partes[0])
        m = int(partes[1]) if len(partes) > 1 else 0
        return f"{h:02d}:{m:02d}"
    except Exception:
        return defecto


def _normalizar_tipo_calendar(valor):
    texto = str(valor or "").lower()
    if "clase" in texto or "teoria" in texto or "teoría" in texto or "practica" in texto and "calificada" not in texto:
        return "clase"
    if "monograf" in texto:
        return "monografia"
    if "práctica" in texto or "practica" in texto:
        return "practica"
    if "final" in texto:
        return "final"
    if "parcial" in texto or "examen" in texto:
        return "parcial"
    if "almuerzo" in texto or "descanso" in texto:
        return "descanso"
    return "tarea"


def _fecha_de_bloque(bloque, fecha_inicio, horizonte_dias):
    fecha_texto = str(bloque.get("fecha", ""))[:10]
    if fecha_texto:
        return fecha_texto
    dia = bloque.get("dia")
    if dia:
        for f in rango_fechas(fecha_inicio, horizonte_dias):
            if fecha_a_dia(f) == dia:
                return f.isoformat()
    return fecha_inicio.isoformat()


def _construir_eventos_calendar(horarios=None, bloques_estudio=None, fecha_inicio=None, horizonte_dias=7):
    horarios = horarios or []
    bloques_estudio = bloques_estudio or []
    fecha_inicio = fecha_inicio or date.today()
    eventos = []
    fechas = rango_fechas(fecha_inicio, max(7, int(horizonte_dias or 7)))

    for h in horarios:
        for f in fechas:
            if fecha_a_dia(f) != h.get("dia"):
                continue
            curso = h.get("codigo_curso") or h.get("nombre_curso") or "Clase"
            nombre = h.get("nombre_curso") or curso
            tipo = h.get("tipo") or "Clase"
            aula = h.get("aula") or ""
            docente = h.get("docente") or ""
            eventos.append({
                "id": f"clase-{curso}-{f.isoformat()}-{h.get('inicio')}-{h.get('fin')}",
                "title": f"{curso} · {nombre}",
                "date": f.isoformat(),
                "startTime": _normalizar_hora(h.get("inicio"), "08:00"),
                "endTime": _normalizar_hora(h.get("fin"), "09:00"),
                "course": nombre,
                "type": "clase",
                "difficulty": "media",
                "repeat": "weekly",
                "description": f"{tipo} · {docente} · Aula: {aula}".strip(" ·"),
            })

    for i, b in enumerate(bloques_estudio):
        tipo_base = b.get("tipo_actividad") or b.get("tipo") or b.get("actividad") or "Tarea"
        tipo = _normalizar_tipo_calendar(tipo_base)
        fecha_evento = _fecha_de_bloque(b, fecha_inicio, horizonte_dias)
        curso = b.get("curso") or "Actividad"
        actividad = b.get("actividad") or b.get("tarea_origen") or "Bloque de estudio"
        tarea = b.get("tarea_origen") or b.get("descripcion") or ""
        if tipo == "descanso":
            titulo = actividad
        elif str(b.get("tipo", "")).lower() == "clase":
            titulo = f"{curso}"
            tipo = "clase"
        else:
            titulo = f"{curso} · {actividad}"
        eventos.append({
            "id": f"plan-{i}-{fecha_evento}-{b.get('inicio')}-{b.get('fin')}",
            "title": titulo,
            "date": fecha_evento,
            "startTime": _normalizar_hora(b.get("inicio"), "08:00"),
            "endTime": _normalizar_hora(b.get("fin"), "09:00"),
            "course": curso,
            "type": tipo,
            "difficulty": str(b.get("dificultad", "media")).lower(),
            "repeat": "none",
            "description": tarea,
        })

    # evitar eventos sin duración válida
    limpios = []
    for e in eventos:
        if e["endTime"] <= e["startTime"]:
            h = int(e["startTime"][:2])
            m = e["startTime"][3:5]
            e["endTime"] = f"{min(23, h + 1):02d}:{m}"
        limpios.append(e)
    return limpios


def _calendar_google_html(eventos, vista="week", fecha_inicio=None, titulo="AURA Calendar"):
    fecha_inicio = fecha_inicio or date.today()
    cursos = sorted({str(e.get("course") or "Sin curso") for e in eventos})
    course_options = "<option value='todos'>Todos los cursos</option>" + "".join(
        [f"<option value=\"{escape(c)}\">{escape(c)}</option>" for c in cursos]
    )
    eventos_json = json.dumps(eventos, ensure_ascii=False)
    initial_date = fecha_inicio.isoformat()
    initial_view = "month" if vista.lower().startswith("month") or vista.lower().startswith("mes") else "week"

    template = r'''
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<style>
*{box-sizing:border-box;margin:0;padding:0;font-family:"Google Sans","Segoe UI",Arial,sans-serif;}
body{background:#f8fafd;color:#202124;overflow:hidden;}
.app{display:grid;grid-template-columns:250px 1fr;height:820px;border:1px solid #dadce0;border-radius:24px;overflow:hidden;background:#fff;box-shadow:0 14px 38px rgba(15,23,42,.10);}
.sidebar{background:#fff;border-right:1px solid #dadce0;padding:20px;display:flex;flex-direction:column;gap:18px;}
.logo{font-size:22px;font-weight:800;color:#1a73e8;letter-spacing:-.03em;}
.btn-create{border:none;background:#fff;box-shadow:0 2px 8px rgba(60,64,67,.25);border-radius:28px;padding:14px 18px;font-size:15px;cursor:pointer;text-align:left;font-weight:700;transition:.2s;}
.btn-create:hover{background:#f1f3f4;transform:translateY(-1px);}
.side-card{border:1px solid #e0e0e0;border-radius:18px;padding:16px;background:#fff;}
.side-card h3{font-size:15px;margin-bottom:12px;color:#202124;}
.filter-group{display:flex;flex-direction:column;gap:11px;}
label{font-size:13px;font-weight:700;color:#5f6368;}
select,input,textarea{width:100%;border:1px solid #dadce0;border-radius:10px;padding:10px;background:#fff;outline:none;font-size:14px;color:#202124;}
select:focus,input:focus,textarea:focus{border-color:#1a73e8;box-shadow:0 0 0 2px rgba(26,115,232,.12);}
.legend{display:flex;flex-direction:column;gap:10px;font-size:14px;}
.legend-item{display:flex;align-items:center;gap:9px;}
.dot{width:12px;height:12px;border-radius:50%;}
.dot.clase{background:#49a3e8}.dot.tarea{background:#1a73e8}.dot.monografia{background:#34a853}.dot.practica{background:#fbbc04}.dot.parcial{background:#ea4335}.dot.final{background:#9334e6}.dot.descanso{background:#93c5fd}
.main{display:flex;flex-direction:column;height:820px;overflow:hidden;}
.topbar{height:76px;background:#fff;border-bottom:1px solid #dadce0;display:flex;align-items:center;justify-content:space-between;padding:0 24px;gap:16px;}
.left-controls,.right-controls{display:flex;align-items:center;gap:10px;}
.today-btn,.nav-btn{border:1px solid #dadce0;background:#fff;border-radius:10px;padding:9px 14px;cursor:pointer;font-weight:600;color:#3c4043;transition:.15s;}
.nav-btn{width:40px;height:40px;font-size:22px;display:flex;align-items:center;justify-content:center;padding:0;}
.today-btn:hover,.nav-btn:hover{background:#f1f3f4;}
.calendar-title{font-size:23px;font-weight:600;min-width:270px;margin-left:8px;letter-spacing:-.03em;}
.calendar-wrapper{flex:1;overflow:hidden;padding:16px 20px 22px;}
.hidden{display:none!important;}
.month-calendar{background:#fff;border:1px solid #dadce0;border-radius:18px;overflow:hidden;height:100%;display:grid;grid-template-rows:48px 1fr;}
.weekdays{display:grid;grid-template-columns:repeat(7,1fr);background:#f8fafd;border-bottom:1px solid #dadce0;}
.weekday{display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;color:#5f6368;border-right:1px solid #e0e0e0;}
.weekday:last-child{border-right:none;}
.days{display:grid;grid-template-columns:repeat(7,1fr);grid-auto-rows:minmax(110px,1fr);overflow:auto;}
.day{border-right:1px solid #e0e0e0;border-bottom:1px solid #e0e0e0;padding:8px;background:#fff;cursor:pointer;transition:.15s;overflow:hidden;}
.day:hover{background:#f8fafd;}.day:nth-child(7n){border-right:none;}
.day-number{width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:13px;margin-bottom:6px;}
.today .day-number{background:#1a73e8;color:#fff;font-weight:800;}.other-month{background:#fafafa;color:#a0a0a0;}
.month-event{padding:5px 7px;border-radius:8px;font-size:12px;margin-bottom:5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;cursor:pointer;font-weight:700;color:#fff;}
.week-calendar{background:#fff;border:1px solid #dadce0;border-radius:18px;height:100%;display:grid;grid-template-rows:64px 1fr;overflow:hidden;}
.week-header{display:grid;grid-template-columns:70px 1fr;border-bottom:1px solid #dadce0;background:#fff;}
.week-corner{border-right:1px solid #dadce0;display:flex;align-items:center;justify-content:center;font-size:11px;color:#5f6368;}
.week-days-header{display:grid;grid-template-columns:repeat(7,1fr);}
.week-day-header{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:3px;border-right:1px solid #e0e0e0;color:#5f6368;font-size:12px;font-weight:700;}
.week-day-header:last-child{border-right:none;}
.week-day-header .number{width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;color:#202124;font-size:18px;font-weight:600;}
.week-day-header.today-header .number{background:#1a73e8;color:#fff;font-weight:800;}
.week-scroll{display:grid;grid-template-columns:70px 1fr;overflow-y:auto;overflow-x:hidden;}
.time-column{border-right:1px solid #dadce0;background:#fff;}
.hour-label{height:64px;padding-right:10px;text-align:right;font-size:12px;color:#70757a;transform:translateY(-8px);}
.week-day-columns{display:grid;grid-template-columns:repeat(7,1fr);position:relative;}
.week-day{position:relative;min-height:1152px;border-right:1px solid #e0e0e0;background-image:linear-gradient(to bottom,#e0e0e0 1px,transparent 1px);background-size:100% 64px;cursor:pointer;}
.week-day:last-child{border-right:none;}
.week-event{position:absolute;left:5px;right:5px;border-radius:8px;padding:7px 8px;color:white;font-size:12px;line-height:1.2;cursor:pointer;overflow:hidden;box-shadow:0 1px 3px rgba(60,64,67,.25);font-weight:700;}
.week-event small{display:block;font-size:11px;margin-top:2px;font-weight:600;opacity:.95;}
.month-event.clase,.week-event.clase{background:#49a3e8;color:#fff;}
.month-event.tarea,.week-event.tarea{background:#1a73e8;color:#fff;}
.month-event.monografia,.week-event.monografia{background:#34a853;color:#fff;}
.month-event.practica,.week-event.practica{background:#fbbc04;color:#202124;}
.month-event.parcial,.week-event.parcial{background:#ea4335;color:#fff;}
.month-event.final,.week-event.final{background:#9334e6;color:#fff;}
.month-event.descanso,.week-event.descanso{background:#93c5fd;color:#202124;}
.event-popover{position:fixed;width:500px;background:#f1f4f9;border-radius:26px;box-shadow:0 6px 20px rgba(60,64,67,.28);z-index:120;padding:18px 22px 22px;animation:popoverIn .18s ease;}
@keyframes popoverIn{from{opacity:0;transform:translateY(8px) scale(.98);}to{opacity:1;transform:translateY(0) scale(1);}}
.popover-actions{display:flex;justify-content:flex-end;gap:12px;margin-bottom:18px;}
.popover-actions button{border:none;background:transparent;font-size:20px;color:#3c4043;cursor:pointer;width:30px;height:30px;border-radius:50%;}
.popover-actions button:hover{background:#e3e7ee;}
.popover-content{display:grid;grid-template-columns:24px 1fr;gap:16px;}
.color-box{width:14px;height:14px;border-radius:4px;margin-top:8px;}
.popover-main h2{font-size:23px;line-height:1.25;font-weight:500;color:#202124;margin-bottom:5px;}
.popover-date,.popover-repeat{font-size:14px;color:#3c4043;margin-bottom:3px;}.popover-repeat{margin-bottom:16px;}
.invite-btn{border:1px solid #9aa0a6;background:transparent;color:#0b57d0;border-radius:24px;padding:9px 18px;font-size:14px;font-weight:600;cursor:pointer;margin-bottom:18px;}
.invite-btn:hover{background:#e8f0fe;}.popover-info{display:flex;flex-direction:column;gap:14px;}.info-row{display:grid;grid-template-columns:26px 1fr;gap:14px;align-items:flex-start;font-size:14px;color:#3c4043;}.info-row span{color:#5f6368;font-size:18px;}.info-row p{line-height:1.35;}
@media(max-width:950px){.app{grid-template-columns:1fr}.sidebar{display:none}.topbar{height:auto;padding:14px;flex-wrap:wrap}.calendar-title{font-size:20px;min-width:180px}.calendar-wrapper{padding:10px}.event-popover{width:calc(100vw - 24px);left:12px!important;right:12px}.right-controls{flex-wrap:wrap}}
</style>
</head>
<body>
<div class="app">
<aside class="sidebar">
  <div class="logo">AURA Calendar</div>
  <button class="btn-create" onclick="alert('Para crear o editar actividades usa los botones de AURA debajo del calendario.')">+ Crear actividad</button>
  <div class="side-card"><h3>Filtros</h3><div class="filter-group">
    <label>Tipo de actividad</label><select id="filterType" onchange="renderCalendar()">
      <option value="todos">Todos</option><option value="clase">Clases</option><option value="tarea">Tareas</option><option value="monografia">Monografías</option><option value="practica">Prácticas calificadas</option><option value="parcial">Examen parcial</option><option value="final">Examen final</option><option value="descanso">Descanso / almuerzo</option>
    </select>
    <label>Curso</label><select id="filterCourse" onchange="renderCalendar()">__COURSES_OPTIONS__</select>
  </div></div>
  <div class="side-card"><h3>Leyenda</h3><div class="legend">
    <div class="legend-item"><span class="dot clase"></span> Clase</div>
    <div class="legend-item"><span class="dot tarea"></span> Tarea</div>
    <div class="legend-item"><span class="dot monografia"></span> Monografía</div>
    <div class="legend-item"><span class="dot practica"></span> Práctica calificada</div>
    <div class="legend-item"><span class="dot parcial"></span> Examen parcial</div>
    <div class="legend-item"><span class="dot final"></span> Examen final</div>
    <div class="legend-item"><span class="dot descanso"></span> Descanso</div>
  </div></div>
</aside>
<main class="main">
<header class="topbar">
  <div class="left-controls"><button class="today-btn" onclick="goToday()">Hoy</button><button class="nav-btn" onclick="previousPeriod()">‹</button><button class="nav-btn" onclick="nextPeriod()">›</button><div class="calendar-title" id="calendarTitle"></div></div>
  <div class="right-controls"><select id="monthSelect" onchange="changeMonthYear()"></select><select id="yearSelect" onchange="changeMonthYear()"></select><select id="viewSelect" onchange="renderCalendar()"><option value="week">Semana</option><option value="month">Mes</option></select></div>
</header>
<section class="calendar-wrapper">
  <div class="month-calendar hidden" id="monthView"><div class="weekdays"><div class="weekday">Dom</div><div class="weekday">Lun</div><div class="weekday">Mar</div><div class="weekday">Mié</div><div class="weekday">Jue</div><div class="weekday">Vie</div><div class="weekday">Sáb</div></div><div class="days" id="days"></div></div>
  <div class="week-calendar" id="weekView"><div class="week-header"><div class="week-corner">GMT-05</div><div class="week-days-header" id="weekDaysHeader"></div></div><div class="week-scroll"><div class="time-column" id="timeColumn"></div><div class="week-day-columns" id="weekDayColumns"></div></div></div>
</section>
</main>
</div>
<div class="event-popover hidden" id="eventPopover">
  <div class="popover-actions"><button title="Correo">✉</button><button title="Más">⋮</button><button title="Cerrar" onclick="closeEventPopover()">×</button></div>
  <div class="popover-content"><div class="color-box" id="popoverColor"></div><div class="popover-main"><h2 id="popoverTitle">Título</h2><p class="popover-date" id="popoverDate"></p><p class="popover-repeat" id="popoverRepeat"></p><button class="invite-btn" onclick="copyInviteLink()">⤴ Copiar enlace</button><div class="popover-info"><div class="info-row"><span>☰</span><p id="popoverCourse"></p></div><div class="info-row"><span>🔔</span><p>30 minutos antes</p></div><div class="info-row"><span>📅</span><p>AURA</p></div><div class="info-row"><span>📝</span><p id="popoverDescription"></p></div></div></div></div>
</div>
<script>
const monthNames=["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"];
const shortMonthNames=["ene","feb","mar","abr","may","jun","jul","ago","sep","oct","nov","dic"];
const dayNames=["Domingo","Lunes","Martes","Miércoles","Jueves","Viernes","Sábado"];
const shortDayNames=["DOM","LUN","MAR","MIÉ","JUE","VIE","SÁB"];
const colors={clase:"#49a3e8",tarea:"#1a73e8",monografia:"#34a853",practica:"#fbbc04",parcial:"#ea4335",final:"#9334e6",descanso:"#93c5fd"};
const START_HOUR=6, END_HOUR=24, HOUR_HEIGHT=64;
let currentDate=parseDate("__INITIAL_DATE__");
let selectedEventIndex=null;
let events=__EVENTS_JSON__;
const calendarTitle=document.getElementById("calendarTitle"),monthSelect=document.getElementById("monthSelect"),yearSelect=document.getElementById("yearSelect"),viewSelect=document.getElementById("viewSelect"),monthView=document.getElementById("monthView"),weekView=document.getElementById("weekView"),daysContainer=document.getElementById("days"),weekDaysHeader=document.getElementById("weekDaysHeader"),timeColumn=document.getElementById("timeColumn"),weekDayColumns=document.getElementById("weekDayColumns");
function initSelectors(){monthNames.forEach((m,i)=>{const o=document.createElement("option");o.value=i;o.textContent=m;monthSelect.appendChild(o);});const yNow=new Date().getFullYear();for(let y=yNow-5;y<=yNow+10;y++){const o=document.createElement("option");o.value=y;o.textContent=y;yearSelect.appendChild(o);}viewSelect.value="__INITIAL_VIEW__";}
function renderCalendar(){closeEventPopover();const view=viewSelect.value;monthSelect.value=currentDate.getMonth();yearSelect.value=currentDate.getFullYear();if(view==="month"){monthView.classList.remove("hidden");weekView.classList.add("hidden");renderMonthView();}else{weekView.classList.remove("hidden");monthView.classList.add("hidden");renderWeekView();}}
function renderMonthView(){daysContainer.innerHTML="";const year=currentDate.getFullYear(),month=currentDate.getMonth();calendarTitle.textContent=`${monthNames[month]} ${year}`;const firstDay=new Date(year,month,1),lastDay=new Date(year,month+1,0),startDay=firstDay.getDay(),totalDays=lastDay.getDate(),prevLastDay=new Date(year,month,0).getDate(),today=new Date();let dayNumber=1,nextMonthDay=1;for(let i=0;i<42;i++){const dayCell=document.createElement("div");dayCell.classList.add("day");let displayedDay,cellDate,isCurrentMonth=true;if(i<startDay){displayedDay=prevLastDay-startDay+i+1;cellDate=new Date(year,month-1,displayedDay);isCurrentMonth=false;}else if(dayNumber<=totalDays){displayedDay=dayNumber;cellDate=new Date(year,month,dayNumber);dayNumber++;}else{displayedDay=nextMonthDay;cellDate=new Date(year,month+1,nextMonthDay);nextMonthDay++;isCurrentMonth=false;}const formattedDate=formatDate(cellDate);if(!isCurrentMonth)dayCell.classList.add("other-month");if(isSameDay(cellDate,today))dayCell.classList.add("today");const number=document.createElement("div");number.classList.add("day-number");number.textContent=displayedDay;dayCell.appendChild(number);const dayEvents=getFilteredEvents().filter(e=>e.date===formattedDate).sort((a,b)=>a.startTime.localeCompare(b.startTime));dayEvents.forEach(event=>{const realIndex=events.findIndex(item=>item.id===event.id);const el=document.createElement("div");el.classList.add("month-event",event.type);el.textContent=`${formatShortTime(event.startTime)} ${event.title}`;el.title=`${event.title} - ${event.course}`;el.onclick=function(e){e.stopPropagation();openEventPopover(event,realIndex,e);};dayCell.appendChild(el);});daysContainer.appendChild(dayCell);}}
function renderWeekView(){weekDaysHeader.innerHTML="";timeColumn.innerHTML="";weekDayColumns.innerHTML="";const weekStart=getWeekStart(currentDate),weekEnd=addDays(weekStart,6);calendarTitle.textContent=getWeekTitle(weekStart,weekEnd);for(let hour=START_HOUR;hour<END_HOUR;hour++){const label=document.createElement("div");label.classList.add("hour-label");label.textContent=formatHourLabel(hour);timeColumn.appendChild(label);}for(let i=0;i<7;i++){const dayDate=addDays(weekStart,i),formattedDate=formatDate(dayDate);const header=document.createElement("div");header.classList.add("week-day-header");if(isSameDay(dayDate,new Date()))header.classList.add("today-header");header.innerHTML=`<div>${shortDayNames[i]}</div><div class="number">${dayDate.getDate()}</div>`;weekDaysHeader.appendChild(header);const dayColumn=document.createElement("div");dayColumn.classList.add("week-day");const dayEvents=getFilteredEvents().filter(e=>e.date===formattedDate).sort((a,b)=>a.startTime.localeCompare(b.startTime));dayEvents.forEach(event=>{const realIndex=events.findIndex(item=>item.id===event.id);const card=document.createElement("div");card.classList.add("week-event",event.type);card.style.top=`${getEventTop(event.startTime)}px`;card.style.height=`${getEventHeight(event.startTime,event.endTime)}px`;card.innerHTML=`${event.title}<small>${formatTimeRange(event.startTime,event.endTime)}</small>`;card.onclick=function(e){e.stopPropagation();openEventPopover(event,realIndex,e);};dayColumn.appendChild(card);});weekDayColumns.appendChild(dayColumn);}}
function getFilteredEvents(){const filterType=document.getElementById("filterType").value,filterCourse=document.getElementById("filterCourse").value;return events.filter(e=>(filterType==="todos"||e.type===filterType)&&(filterCourse==="todos"||e.course===filterCourse));}
function getEventTop(t){return Math.max(0,(timeToDecimal(t)-START_HOUR)*HOUR_HEIGHT);}function getEventHeight(s,e){const d=Math.max(.5,timeToDecimal(e)-timeToDecimal(s));return Math.max(34,d*HOUR_HEIGHT);}function timeToDecimal(time){const [h,m]=time.split(":").map(Number);return h+m/60;}
function previousPeriod(){if(viewSelect.value==="month")currentDate.setMonth(currentDate.getMonth()-1);else currentDate.setDate(currentDate.getDate()-7);renderCalendar();}function nextPeriod(){if(viewSelect.value==="month")currentDate.setMonth(currentDate.getMonth()+1);else currentDate.setDate(currentDate.getDate()+7);renderCalendar();}function goToday(){currentDate=new Date();renderCalendar();}function changeMonthYear(){currentDate=new Date(parseInt(yearSelect.value),parseInt(monthSelect.value),1);renderCalendar();}
function openEventPopover(event,index,mouseEvent){selectedEventIndex=index;const popover=document.getElementById("eventPopover");document.getElementById("popoverTitle").textContent=event.title;document.getElementById("popoverDate").textContent=formatPopoverDate(event);document.getElementById("popoverRepeat").textContent=getRepeatText(event);document.getElementById("popoverCourse").innerHTML=`${event.course}<br>Dificultad: ${capitalize(event.difficulty || "media")}`;document.getElementById("popoverDescription").textContent=event.description||"Sin descripción";document.getElementById("popoverColor").style.background=colors[event.type]||"#1a73e8";popover.classList.remove("hidden");const x=mouseEvent.clientX,y=mouseEvent.clientY,w=500,h=370;let left=x+16,top=y-40;if(left+w>window.innerWidth)left=x-w-16;if(top+h>window.innerHeight)top=window.innerHeight-h-20;if(top<20)top=20;popover.style.left=`${left}px`;popover.style.top=`${top}px`;}
function closeEventPopover(){document.getElementById("eventPopover").classList.add("hidden");selectedEventIndex=null;}function copyInviteLink(){navigator.clipboard.writeText(window.location.href);alert("Enlace copiado.");}
function getRepeatText(event){if(event.repeat==="weekly"){const d=parseDate(event.date);return `Cada semana el ${dayNames[d.getDay()].toLowerCase()}`;}return "No se repite";}
function formatPopoverDate(event){const d=parseDate(event.date);return `${dayNames[d.getDay()]}, ${d.getDate()} de ${shortMonthNames[d.getMonth()]} · ${formatTimeRange(event.startTime,event.endTime)}`;}function formatTimeRange(s,e){return `${formatShortTime(s)} – ${formatShortTime(e)}`;}function formatShortTime(time){const [hrRaw,minRaw]=time.split(":").map(Number);let hr=hrRaw;const min=String(minRaw).padStart(2,"0"),ampm=hr>=12?"pm":"am";hr=hr%12||12;return min==="00"?`${hr}${ampm}`:`${hr}:${min}${ampm}`;}function formatHourLabel(h){const a=h>=12?"pm":"am",fh=h%12||12;return `${fh} ${a}`;}
function getWeekStart(date){const d=new Date(date);d.setDate(d.getDate()-d.getDay());d.setHours(0,0,0,0);return d;}function getWeekTitle(start,end){const sameMonth=start.getMonth()===end.getMonth(),sameYear=start.getFullYear()===end.getFullYear();if(sameMonth&&sameYear)return `${start.getDate()} – ${end.getDate()} de ${monthNames[start.getMonth()]} ${start.getFullYear()}`;if(sameYear)return `${start.getDate()} ${shortMonthNames[start.getMonth()]} – ${end.getDate()} ${shortMonthNames[end.getMonth()]} ${start.getFullYear()}`;return `${start.getDate()} ${shortMonthNames[start.getMonth()]} ${start.getFullYear()} – ${end.getDate()} ${shortMonthNames[end.getMonth()]} ${end.getFullYear()}`;}
function addDays(date,days){const d=new Date(date);d.setDate(d.getDate()+days);return d;}function formatDate(date){return `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,"0")}-${String(date.getDate()).padStart(2,"0")}`;}function parseDate(str){const [y,m,d]=str.split("-").map(Number);return new Date(y,m-1,d);}function isSameDay(a,b){return a.getDate()===b.getDate()&&a.getMonth()===b.getMonth()&&a.getFullYear()===b.getFullYear();}function capitalize(t){return String(t||"").charAt(0).toUpperCase()+String(t||"").slice(1);}
document.addEventListener("click",function(e){const popover=document.getElementById("eventPopover");if(!popover.classList.contains("hidden")&&!popover.contains(e.target)&&!e.target.classList.contains("month-event")&&!e.target.classList.contains("week-event")){closeEventPopover();}});
initSelectors();renderCalendar();
</script>
</body></html>
'''
    html_code = template.replace("__EVENTS_JSON__", eventos_json)
    html_code = html_code.replace("__COURSES_OPTIONS__", course_options)
    html_code = html_code.replace("__INITIAL_DATE__", initial_date)
    html_code = html_code.replace("__INITIAL_VIEW__", initial_view)
    return html_code


def render_calendario(horarios=None, bloques_estudio=None, titulo="Calendario semanal", fecha_inicio=None, horizonte_dias=7):
    fecha_inicio = fecha_inicio or date.today()
    eventos = _construir_eventos_calendar(horarios, bloques_estudio, fecha_inicio, horizonte_dias)
    st.caption(titulo)
    components.html(_calendar_google_html(eventos, vista="week", fecha_inicio=fecha_inicio, titulo=titulo), height=850, scrolling=False)


def render_calendario_mensual(horarios=None, bloques_estudio=None, titulo="Calendario mensual", fecha_inicio=None):
    fecha_inicio = fecha_inicio or date.today()
    # Se muestra todo el mes desde el día 1, pero mantiene eventos de clases y plan desde el horizonte actual.
    primer_dia = date(fecha_inicio.year, fecha_inicio.month, 1)
    if fecha_inicio.month == 12:
        siguiente = date(fecha_inicio.year + 1, 1, 1)
    else:
        siguiente = date(fecha_inicio.year, fecha_inicio.month + 1, 1)
    horizonte = max(7, (siguiente - primer_dia).days)
    eventos = _construir_eventos_calendar(horarios, bloques_estudio, primer_dia, horizonte)
    st.caption(titulo)
    components.html(_calendar_google_html(eventos, vista="month", fecha_inicio=fecha_inicio, titulo=titulo), height=850, scrolling=False)

def inicializar_diagnostico_state(estudiante_id, detalle):
    pref = f"diag_{estudiante_id}_"
    if f"{pref}horas" not in st.session_state:
        st.session_state[f"{pref}horas"] = float((detalle or {}).get("horas_estudio_dia") or 2.0)
    if f"{pref}promedio" not in st.session_state:
        st.session_state[f"{pref}promedio"] = float((detalle or {}).get("promedio_ponderado") or 13.0)
    respuestas = (detalle or {}).get("respuestas", {}) or {}
    for i in range(1, 21):
        key = f"{pref}p{i}"
        if key not in st.session_state:
            st.session_state[key] = num_a_escala(respuestas.get(i, 3))


def mostrar_diagnostico_guardado(detalle):
    if not detalle:
        st.info("Aún no hay diagnóstico guardado.")
        return
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Riesgo", detalle.get("nivel_riesgo"))
    c2.metric("Puntaje", f"{detalle.get('puntaje_riesgo')}/100")
    c3.metric("Estrés", detalle.get("indice_estres"))
    c4.metric("Motivación", detalle.get("indice_motivacion"))
    if detalle.get("diagnostico_general_ia"):
        st.markdown("**Diagnóstico guardado:**")
        st.write(detalle.get("diagnostico_general_ia"))
    if detalle.get("alerta_emocional") == 1:
        st.error("Alerta emocional detectada. Se recomienda seguimiento por tutoría o área de apoyo correspondiente.")


safe_init()
aplicar_estilos()

if "usuario_logueado" not in st.session_state:
    st.session_state.usuario_logueado = None

if st.session_state.usuario_logueado is None:
    mostrar_login()
    st.stop()

usuario_actual = st.session_state.usuario_logueado
rol_actual = usuario_actual["rol"]

if LOGO_PATH.exists():
    st.sidebar.image(str(LOGO_PATH), use_container_width=True)
st.sidebar.success(f"👤 Usuario: {usuario_actual['username']}")
st.sidebar.info(f"🛡️ Rol: {rol_actual}")
if st.sidebar.button("🚪 Cerrar sesión"):
    cerrar_sesion()
mostrar_musica()

if rol_actual == "Administrador":
    opciones_menu = ["Dashboard Estudiante", "Diagnóstico Académico", "Perfil Académico", "Tareas y Planificador", "Coach IA", "Reportes", "Panel de Tutoría", "Gestión de usuarios", "Exportar datos"]
    default_index = 0
elif rol_actual == "Tutor":
    opciones_menu = ["Dashboard Estudiante", "Diagnóstico Académico", "Perfil Académico", "Tareas y Planificador", "Coach IA", "Reportes", "Panel de Tutoría"]
    default_index = 0
else:
    opciones_menu = ["Dashboard Estudiante", "Diagnóstico Académico", "Perfil Académico", "Tareas y Planificador", "Coach IA", "Reportes"]
    default_index = 0

menu = st.sidebar.radio("Menú principal", opciones_menu, index=default_index)

mostrar_hero("AURA", "Academic University Recommendation Assistant")

if menu == "Inicio":
    st.header("Bienvenido a AURA")
    st.markdown(
        """
        <div class='aura-card'>
        AURA integra diagnóstico académico con IA, seguimiento de cursos y tareas, lectura de boletas de matrícula,
        calendario semanal inteligente y reportes para tutoría.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.info("Flujo recomendado: importar boleta → diagnóstico IA → tareas → planificador calendario → coach IA → reportes.")

elif menu == "Dashboard Estudiante":
    st.header("📊 Dashboard Estudiante")
    estudiante_id, estudiante_texto = seleccionar_estudiante()
    if estudiante_id is not None:
        diagnostico = obtener_ultimo_diagnostico(estudiante_id)
        detalle = obtener_ultimo_diagnostico_detallado(estudiante_id)
        resumen = obtener_resumen_tareas(estudiante_id)
        cursos_dificultad = obtener_cursos_mayor_dificultad(estudiante_id)
        horarios = listar_horarios_clase(estudiante_id)
        ultimo_plan = obtener_ultimo_plan_semanal(estudiante_id)

        if diagnostico is None:
            st.warning("Este estudiante aún no tiene diagnóstico registrado.")
        else:
            horas, promedio, _, estres, motivacion, procrast, puntaje, riesgo, fecha = diagnostico
            riesgo = nivel_por_puntaje(puntaje)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Horas de estudio", f"{horas} h/día")
            c2.metric("Promedio ponderado", promedio)
            c3.metric("Riesgo", riesgo)
            c4.metric("Puntaje IA", f"{puntaje}/100")
            c5, c6, c7, c8 = st.columns(4)
            c5.metric("Total tareas", resumen["total"])
            c6.metric("Completadas", resumen["completadas"])
            c7.metric("Pendientes", resumen["pendientes"])
            c8.metric("Alta prioridad", resumen["alta_prioridad"])
            st.progress(resumen["porcentaje_cumplimiento"] / 100)
            st.caption(f"Cumplimiento de tareas: {resumen['porcentaje_cumplimiento']}% · Último diagnóstico: {fecha}")

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Indicadores IA")
                df_ind = pd.DataFrame({
                    "Indicador": ["Estrés", "Procrastinación", "Motivación", "Estado de ánimo"],
                    "Nivel": [detalle.get("indice_estres") if detalle else estres, detalle.get("indice_procrastinacion") if detalle else procrast, detalle.get("indice_motivacion") if detalle else motivacion, detalle.get("indice_estado_animo") if detalle else 3],
                })
                fig_ind = px.bar(df_ind, x="Nivel", y="Indicador", orientation="h", text="Nivel", range_x=[0, 5], color="Indicador", color_discrete_sequence=PALETA)
                fig_ind.update_traces(textposition="outside", marker_line_width=1, marker_line_color="rgba(255,255,255,.9)")
                fig_ind.update_layout(height=340, margin=dict(l=8, r=32, t=24, b=8), showlegend=False, plot_bgcolor="rgba(255,255,255,0)", paper_bgcolor="rgba(255,255,255,0)")
                st.plotly_chart(fig_ind, use_container_width=True)
            with col2:
                st.subheader("Cursos con mayor dificultad")
                if cursos_dificultad:
                    df_dif = pd.DataFrame(cursos_dificultad, columns=["Curso", "Dificultad"])
                    fig_dif = px.bar(df_dif, x="Dificultad", y="Curso", orientation="h", text="Dificultad", range_x=[0, 5], color="Curso", color_discrete_sequence=PALETA)
                    fig_dif.update_traces(textposition="outside", marker_line_width=1, marker_line_color="rgba(255,255,255,.9)")
                    fig_dif.update_layout(height=340, margin=dict(l=8, r=32, t=24, b=8), showlegend=False, plot_bgcolor="rgba(255,255,255,0)", paper_bgcolor="rgba(255,255,255,0)")
                    st.plotly_chart(fig_dif, use_container_width=True)
                else:
                    st.info("Aún no hay cursos registrados.")

            st.divider()
            if detalle:
                st.subheader("Diagnóstico general IA")
                st.write(detalle.get("diagnostico_general_ia") or "No hay texto de diagnóstico guardado.")
                if detalle.get("alerta_emocional") == 1:
                    st.error("Alerta emocional detectada. Se recomienda seguimiento por tutoría.")

        bloques_estudio = (ultimo_plan or {}).get("plan", []) if ultimo_plan else []
        render_calendario(horarios, bloques_estudio, "🗓️ Calendario semanal: clases y plan de estudio")

elif menu == "Perfil Académico":
    st.header("👤 Perfil Académico")
    estudiante_id, estudiante_texto = seleccionar_estudiante()
    if estudiante_id is not None:
        estudiante = obtener_estudiante_por_id(estudiante_id)
        if estudiante:
            _, nombre, codigo, carrera, ciclo = estudiante
            with st.expander("✏️ Editar datos del estudiante", expanded=False):
                with st.form("form_perfil_estudiante"):
                    n_nombre = st.text_input("Nombre completo", value=nombre or "")
                    n_codigo = st.text_input("Código universitario", value=codigo or "")
                    n_carrera = st.text_input("Carrera", value=carrera or "")
                    n_ciclo = st.selectbox("Ciclo", [str(i) for i in range(1, 13)], index=max(0, min(11, int(ciclo or 1) - 1)) if str(ciclo or "1").isdigit() else 0)
                    if st.form_submit_button("💾 Guardar datos"):
                        actualizar_estudiante(estudiante_id, n_nombre, n_codigo, n_carrera, n_ciclo)
                        st.success("Datos actualizados correctamente.")
                        st.rerun()

            if rol_actual == "Estudiante" and usuario_actual.get("id"):
                with st.expander("🔐 Cambiar usuario o contraseña", expanded=False):
                    user_row = obtener_usuario_por_id(usuario_actual["id"])
                    with st.form("form_usuario_actual"):
                        new_user = st.text_input("Usuario", value=user_row[1] if user_row else usuario_actual["username"])
                        new_pass = st.text_input("Nueva contraseña (opcional)", type="password")
                        if st.form_submit_button("Actualizar acceso"):
                            exito, msg = actualizar_usuario(usuario_actual["id"], new_user, new_pass)
                            if exito:
                                st.success(msg)
                                st.session_state.usuario_logueado["username"] = new_user
                            else:
                                st.error(msg)

        st.subheader("📄 Importar boleta de matrícula")
        st.write("Sube tu boleta PDF para crear automáticamente cursos y horarios de clase.")
        archivo_boleta = st.file_uploader("Boleta de matrícula PDF", type=["pdf"])
        if archivo_boleta:
            try:
                datos_boleta = parsear_boleta_matricula(archivo_boleta)
                st.success(f"Se detectaron {len(datos_boleta['cursos'])} cursos y {len(datos_boleta['horarios'])} bloques de horario.")
                col_a, col_b = st.columns(2)
                with col_a:
                    st.caption("Cursos detectados")
                    st.dataframe(pd.DataFrame(datos_boleta["cursos"]), use_container_width=True)
                with col_b:
                    st.caption("Horarios detectados")
                    st.dataframe(pd.DataFrame(datos_boleta["horarios"]), use_container_width=True)
                reemplazar = st.checkbox("Reemplazar horarios anteriores", value=True)
                if st.button("📥 Importar cursos y horarios"):
                    exito, msg = importar_boleta_matricula(estudiante_id, datos_boleta["cursos"], datos_boleta["horarios"], reemplazar_horarios=reemplazar)
                    if exito:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
            except Exception as error:
                st.error("No se pudo leer la boleta. Verifica que sea un PDF con texto seleccionable.")
                st.code(str(error))

        st.divider()
        st.subheader("📚 Cursos")
        cursos = listar_cursos_por_estudiante(estudiante_id)
        col_add, col_hint = st.columns([1, 3])
        with col_add:
            with st.popover("➕ Agregar curso"):
                with st.form("form_add_curso"):
                    nombre_curso = st.text_input("Nombre del curso")
                    docente = st.text_input("Docente")
                    creditos = st.number_input("Créditos", 0, 8, 3)
                    dificultad = st.slider("Dificultad", 1, 5, 3)
                    estado = st.selectbox("Estado", ["En curso", "Aprobado", "Desaprobado", "Retirado"])

                    st.markdown("#### 🕒 Horario del curso")
                    agregar_horario = st.checkbox("Agregar horario ahora", value=True)
                    tipo_clase = st.selectbox("Tipo de clase", ["Teoría", "Práctica", "Laboratorio", "Clase"], disabled=not agregar_horario)
                    dias_clase = st.multiselect(
                        "Día(s) de clase",
                        ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"],
                        default=[],
                        disabled=not agregar_horario
                    )
                    col_h1, col_h2 = st.columns(2)
                    with col_h1:
                        hora_inicio = st.time_input("Hora de inicio", value=time(8, 0), disabled=not agregar_horario)
                    with col_h2:
                        hora_fin = st.time_input("Hora de fin", value=time(10, 0), disabled=not agregar_horario)
                    aula = st.text_input("Aula", disabled=not agregar_horario)

                    if st.form_submit_button("💾 Guardar curso"):
                        if not nombre_curso.strip():
                            st.error("Ingresa el nombre del curso.")
                        elif existe_curso(estudiante_id, nombre_curso):
                            st.warning("Este curso ya está registrado.")
                        elif agregar_horario and not dias_clase:
                            st.warning("Selecciona al menos un día de clase o desactiva 'Agregar horario ahora'.")
                        elif agregar_horario and hora_fin <= hora_inicio:
                            st.warning("La hora de fin debe ser mayor que la hora de inicio.")
                        else:
                            curso_id_nuevo = registrar_curso(estudiante_id, nombre_curso, docente, creditos, dificultad, estado)

                            if agregar_horario:
                                for dia in dias_clase:
                                    registrar_horario_clase(
                                        estudiante_id=estudiante_id,
                                        curso_id=curso_id_nuevo,
                                        codigo_curso="",
                                        nombre_curso=nombre_curso,
                                        tipo=tipo_clase,
                                        docente=docente,
                                        dia=dia,
                                        hora_inicio=hora_inicio.strftime("%H:%M"),
                                        hora_fin=hora_fin.strftime("%H:%M"),
                                        aula=aula,
                                    )

                            st.success("Curso registrado con su horario." if agregar_horario else "Curso registrado.")
                            st.rerun()
        with col_hint:
            st.caption("También puedes importar cursos y horarios automáticamente desde la boleta.")
        if cursos:
            st.dataframe(pd.DataFrame(cursos, columns=["ID", "Curso", "Docente", "Créditos", "Dificultad", "Estado"]), use_container_width=True)
            with st.expander("✏️ Editar o eliminar curso"):
                opciones = {f"{c[1]} | {c[5]}": c for c in cursos}
                sel = st.selectbox("Curso", list(opciones.keys()))
                c = opciones[sel]
                with st.form("form_edit_curso"):
                    e_nombre = st.text_input("Nombre", value=c[1] or "")
                    e_docente = st.text_input("Docente", value=c[2] or "")
                    e_creditos = st.number_input("Créditos", 0, 8, int(c[3] or 0))
                    e_dificultad = st.slider("Dificultad", 1, 5, int(c[4] or 3))
                    e_estado = st.selectbox("Estado", ["En curso", "Aprobado", "Desaprobado", "Retirado"], index=["En curso", "Aprobado", "Desaprobado", "Retirado"].index(c[5]) if c[5] in ["En curso", "Aprobado", "Desaprobado", "Retirado"] else 0)
                    guardar, borrar = st.columns(2)
                    if guardar.form_submit_button("💾 Actualizar curso"):
                        actualizar_curso(c[0], e_nombre, e_docente, e_creditos, e_dificultad, e_estado)
                        st.success("Curso actualizado.")
                        st.rerun()
                    if borrar.form_submit_button("🗑️ Eliminar curso"):
                        eliminar_curso(c[0])
                        st.warning("Curso eliminado.")
                        st.rerun()
        else:
            st.info("Aún no hay cursos registrados.")

        if cursos:
            st.divider()
            st.subheader("🕒 Horarios de clase")
            with st.popover("➕ Agregar horario a un curso"):
                with st.form("form_add_horario_manual"):
                    opciones_curso_horario = {f"{c[1]} | Dificultad {c[4]}": c for c in cursos}
                    curso_horario_txt = st.selectbox("Curso", list(opciones_curso_horario.keys()))
                    curso_horario = opciones_curso_horario[curso_horario_txt]
                    tipo_horario = st.selectbox("Tipo", ["Teoría", "Práctica", "Laboratorio", "Clase"])
                    dias_horario = st.multiselect(
                        "Día(s)",
                        ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"],
                        default=[]
                    )
                    col_i, col_f = st.columns(2)
                    with col_i:
                        inicio_horario = st.time_input("Inicio", value=time(8, 0), key="inicio_horario_manual")
                    with col_f:
                        fin_horario = st.time_input("Fin", value=time(10, 0), key="fin_horario_manual")
                    aula_horario = st.text_input("Aula")

                    if st.form_submit_button("💾 Guardar horario"):
                        if not dias_horario:
                            st.warning("Selecciona al menos un día.")
                        elif fin_horario <= inicio_horario:
                            st.warning("La hora de fin debe ser mayor que la hora de inicio.")
                        else:
                            for dia in dias_horario:
                                registrar_horario_clase(
                                    estudiante_id=estudiante_id,
                                    curso_id=curso_horario[0],
                                    codigo_curso="",
                                    nombre_curso=curso_horario[1],
                                    tipo=tipo_horario,
                                    docente=curso_horario[2] or "",
                                    dia=dia,
                                    hora_inicio=inicio_horario.strftime("%H:%M"),
                                    hora_fin=fin_horario.strftime("%H:%M"),
                                    aula=aula_horario,
                                )
                            st.success("Horario agregado correctamente.")
                            st.rerun()

        horarios = listar_horarios_clase(estudiante_id)
        if horarios:
            st.dataframe(
                pd.DataFrame(horarios)[["id", "nombre_curso", "tipo", "docente", "dia", "inicio", "fin", "aula"]],
                use_container_width=True
            )
            with st.expander("🗑️ Eliminar un bloque de horario"):
                opciones_h = {f"{h['nombre_curso']} | {h['tipo']} | {h['dia']} {h['inicio']}-{h['fin']}": h['id'] for h in horarios}
                horario_sel = st.selectbox("Bloque de horario", list(opciones_h.keys()))
                if st.button("🗑️ Eliminar horario seleccionado"):
                    eliminar_horario_clase(opciones_h[horario_sel])
                    st.warning("Horario eliminado.")
                    st.rerun()

        render_calendario(horarios, [], "🗓️ Horario de clases")
        if horarios and st.button("🧹 Limpiar todos los horarios"):
            limpiar_horarios_clase(estudiante_id)
            st.success("Horarios eliminados.")
            st.rerun()

elif menu == "Diagnóstico Académico":
    st.header("🧠 Diagnóstico académico y bienestar con IA")
    estudiante_id, estudiante_texto = seleccionar_estudiante()
    if estudiante_id is not None:
        nombre_estudiante = obtener_nombre_desde_texto(estudiante_texto)
        detalle = obtener_ultimo_diagnostico_detallado(estudiante_id)
        inicializar_diagnostico_state(estudiante_id, detalle)
        mostrar_diagnostico_guardado(detalle)
        st.warning("Este diagnóstico es una orientación académica y de bienestar, no un diagnóstico clínico.")
        st.info("Escala: 1 = Nunca | 2 = Casi nunca | 3 = A veces | 4 = Casi siempre | 5 = Siempre")
        pref = f"diag_{estudiante_id}_"
        with st.form("form_diagnostico_ia"):
            c1, c2 = st.columns(2)
            c1.number_input("Horas de estudio por día", 0.0, 16.0, step=0.5, key=f"{pref}horas")
            c2.number_input("Promedio ponderado actual", 0.0, 20.0, step=0.1, key=f"{pref}promedio")
            st.divider()
            for dimension in ["Estrés", "Procrastinación", "Motivación", "Estado de ánimo", "Estado de ánimo / alerta emocional"]:
                st.subheader(dimension)
                for i, (pregunta, dim) in enumerate(PREGUNTAS_DIAGNOSTICO, start=1):
                    if dim == dimension:
                        st.select_slider(
                            f"{i}. {pregunta}",
                            options=ESCALA_OPCIONES,
                            key=f"{pref}p{i}",
                            help="1 Nunca · 2 Casi nunca · 3 A veces · 4 Casi siempre · 5 Siempre",
                        )
            if st.form_submit_button("🤖 Generar diagnóstico con IA y guardar"):
                respuestas = {i: escala_a_num(st.session_state[f"{pref}p{i}"]) for i in range(1, 21)}
                with st.spinner("AURA está generando el diagnóstico con IA..."):
                    resultado = generar_diagnostico_ia(nombre_estudiante, st.session_state[f"{pref}horas"], st.session_state[f"{pref}promedio"], respuestas)
                if not resultado.get("exito"):
                    st.error("No se pudo generar el diagnóstico con IA.")
                    st.code(resultado.get("error", "Error desconocido"))
                else:
                    guardar_diagnostico_ia(estudiante_id, st.session_state[f"{pref}horas"], st.session_state[f"{pref}promedio"], respuestas, resultado)
                    mostrar_estado_riesgo(resultado["nivel_riesgo"], resultado["puntaje_riesgo"])
                    st.write(resultado.get("diagnostico_general", ""))
                    st.success("Diagnóstico guardado correctamente.")

elif menu == "Tareas y Planificador":
    st.header("✅ Tareas y Planificador")
    estudiante_id, estudiante_texto = seleccionar_estudiante()
    if estudiante_id is not None:
        cursos = listar_cursos_por_estudiante(estudiante_id)
        tareas = listar_tareas_por_estudiante(estudiante_id)
        tareas_plan = listar_tareas_para_planificador(estudiante_id)
        horarios = listar_horarios_clase(estudiante_id)
        diagnostico = obtener_ultimo_diagnostico(estudiante_id)
        detalle = obtener_ultimo_diagnostico_detallado(estudiante_id)
        ultimo_plan = obtener_ultimo_plan_semanal(estudiante_id)

        st.subheader("Tareas")
        with st.popover("➕ Agregar tarea"):
            if not cursos:
                st.warning("Primero registra o importa cursos.")
            else:
                opciones_cursos = {f"{c[1]} | Dificultad {c[4]}": c for c in cursos}
                with st.form("form_add_tarea"):
                    curso_txt = st.selectbox("Curso", list(opciones_cursos.keys()))
                    tipo_actividad = st.selectbox("Tipo de actividad", TIPOS_ACTIVIDAD, help="Tarea = básica; Monografía = más días; Práctica = repaso medio; Exámenes = más preparación")
                    titulo = st.text_input("Título de la actividad")
                    descripcion = st.text_area("Descripción")
                    fecha_entrega = st.date_input("Fecha de entrega / evaluación", value=date.today())
                    if st.form_submit_button("Guardar tarea"):
                        curso = opciones_cursos[curso_txt]
                        if not titulo.strip():
                            st.error("Ingresa el título.")
                        elif existe_tarea(estudiante_id, curso[0], titulo):
                            st.warning("Esta tarea ya existe para este curso.")
                        else:
                            registrar_tarea(estudiante_id, curso[0], titulo, descripcion, fecha_entrega.strftime("%Y-%m-%d"), int(curso[4] or 3), tipo_actividad)
                            st.success("Tarea registrada.")
                            st.rerun()

        if tareas:
            st.dataframe(pd.DataFrame(tareas, columns=["ID", "Tipo", "Actividad", "Curso", "Fecha de entrega", "Prioridad", "Estado"]), use_container_width=True)
            with st.expander("✏️ Editar o eliminar tarea"):
                opciones_t = {f"{t[2]} | {t[3]} | {t[1]} | {t[6]}": t[0] for t in tareas}
                tarea_sel = st.selectbox("Tarea", list(opciones_t.keys()))
                tarea_id = opciones_t[tarea_sel]
                tarea_info = obtener_tarea_por_id(tarea_id)
                if tarea_info and cursos:
                    curso_ids = [c[0] for c in cursos]
                    idx_curso = curso_ids.index(tarea_info[2]) if tarea_info[2] in curso_ids else 0
                    with st.form("form_edit_tarea"):
                        curso_opciones = {c[1]: c for c in cursos}
                        curso_nombre = st.selectbox("Curso", list(curso_opciones.keys()), index=idx_curso)
                        tipo_actual = tarea_info[10] if len(tarea_info) > 10 and tarea_info[10] in TIPOS_ACTIVIDAD else "Tarea"
                        e_tipo = st.selectbox("Tipo de actividad", TIPOS_ACTIVIDAD, index=TIPOS_ACTIVIDAD.index(tipo_actual))
                        e_titulo = st.text_input("Título", value=tarea_info[3] or "")
                        e_desc = st.text_area("Descripción", value=tarea_info[4] or "")
                        e_fecha = st.date_input("Fecha de entrega / evaluación", value=tarea_info[5] or date.today())
                        estados = ["Pendiente", "En proceso", "Completada"]
                        e_estado = st.selectbox("Estado", estados, index=estados.index(tarea_info[7]) if tarea_info[7] in estados else 0)
                        colg, colb = st.columns(2)
                        if colg.form_submit_button("💾 Actualizar tarea"):
                            curso_nuevo = curso_opciones[curso_nombre]
                            actualizar_tarea(tarea_id, curso_nuevo[0], e_titulo, e_desc, e_fecha.strftime("%Y-%m-%d"), e_estado, int(curso_nuevo[4] or 3), e_tipo)
                            st.success("Tarea actualizada.")
                            st.rerun()
                        if colb.form_submit_button("🗑️ Eliminar tarea"):
                            eliminar_tarea(tarea_id)
                            st.warning("Tarea eliminada.")
                            st.rerun()
        else:
            st.info("Aún no hay tareas registradas.")

        st.divider()
        st.subheader("🗓️ Planificador inteligente")
        st.caption("El plan parte desde la fecha actual, no asigna tareas después de su vencimiento y evita clases, almuerzo y descanso.")

        vista_plan = st.radio(
            "Vista del calendario",
            ["Semanal", "Mensual"],
            horizontal=True,
            key=f"vista_plan_{estudiante_id}"
        )
        fecha_inicio_plan = date.today()
        horizonte = 7 if vista_plan == "Semanal" else dias_restantes_mes(fecha_inicio_plan)
        almuerzo_inicio = "13:00"
        almuerzo_fin = "14:00"

        bloques_guardados = (ultimo_plan or {}).get("plan", []) if ultimo_plan else []
        if vista_plan == "Semanal":
            render_calendario(
                horarios,
                bloques_guardados,
                f"Calendario semanal desde hoy: {fecha_inicio_plan.strftime('%d/%m/%Y')}",
                fecha_inicio=fecha_inicio_plan,
                horizonte_dias=7,
            )
        else:
            render_calendario_mensual(
                horarios,
                bloques_guardados,
                f"Calendario mensual: {fecha_inicio_plan.strftime('%B %Y')}",
                fecha_inicio=fecha_inicio_plan,
            )

        if ultimo_plan:
            st.caption(f"Último plan generado: {ultimo_plan.get('fecha')} | Horas base: {ultimo_plan.get('horas_disponibles')} h/semana")

        if diagnostico is None:
            st.warning("Registra primero un diagnóstico para personalizar el plan.")
        elif not tareas_plan:
            st.warning("Registra tareas para generar un plan de estudio.")
        else:
            nombre = obtener_nombre_desde_texto(estudiante_texto)
            horas, promedio, _, estres, motivacion, procrast, puntaje, riesgo, _ = diagnostico
            riesgo = nivel_por_puntaje(puntaje)

            c1, c2, c3, c4 = st.columns(4)
            horas_disponibles = c1.number_input(
                "Horas disponibles por semana",
                1.0,
                80.0,
                value=float(max(1, horas * 7)),
                step=1.0,
                help="El plan mensual escala estas horas según los días restantes del mes."
            )
            c2.metric("Riesgo", riesgo)
            c3.metric("Tareas activas", len([t for t in tareas_plan if t.get("estado") != "Completada"]))
            c4.metric("Horizonte", f"{horizonte} días")

            with st.expander("⚙️ Preferencias de planificación"):
                col_a, col_b, col_c = st.columns(3)
                almuerzo_inicio = col_a.selectbox("Inicio almuerzo", ["12:00", "12:30", "13:00", "13:30", "14:00"], index=2)
                almuerzo_fin = col_b.selectbox("Fin almuerzo", ["13:00", "13:30", "14:00", "14:30", "15:00"], index=2)
                usar_ia = col_c.toggle("Usar IA primero", value=True)
                st.info("AURA siempre valida la fecha actual y usa un respaldo automático si la IA falla o no hay cuota disponible.")

            diag_plan = {
                "promedio_ponderado": promedio,
                "nivel_riesgo": riesgo,
                "puntaje_riesgo": puntaje,
                "indice_estres": detalle.get("indice_estres") if detalle else estres,
                "indice_procrastinacion": detalle.get("indice_procrastinacion") if detalle else procrast,
                "indice_motivacion": detalle.get("indice_motivacion") if detalle else motivacion,
                "indice_estado_animo": detalle.get("indice_estado_animo") if detalle else 3,
            }

            if st.button("✨ Generar / actualizar calendario inteligente"):
                bloques = []
                recomendacion = ""
                if usar_ia:
                    with st.spinner("AURA está armando tu calendario con IA y validando fechas límite..."):
                        resultado = generar_plan_calendario_ia(
                            nombre,
                            diag_plan,
                            tareas_plan,
                            horarios,
                            horas_disponibles,
                            fecha_inicio=fecha_inicio_plan.isoformat(),
                            horizonte_dias=horizonte,
                            almuerzo_inicio=almuerzo_inicio,
                            almuerzo_fin=almuerzo_fin,
                        )
                    if resultado.get("exito"):
                        bloques = resultado.get("bloques", [])
                        recomendacion = resultado.get("recomendacion_general", "Plan generado con IA.")
                    else:
                        st.warning("La IA no pudo generar el calendario. Se usará el planificador automático de respaldo.")
                        st.code(resultado.get("error", "Error desconocido"))

                if not bloques:
                    bloques = generar_plan_calendario_respaldo(
                        tareas_plan,
                        horarios,
                        horas_disponibles,
                        riesgo,
                        fecha_inicio=fecha_inicio_plan,
                        horizonte_dias=horizonte,
                        incluir_descansos=True,
                        almuerzo_inicio=almuerzo_inicio,
                        almuerzo_fin=almuerzo_fin,
                    )
                    recomendacion = "Plan generado automáticamente respetando clases, almuerzo, dificultad y vencimientos."

                guardar_plan_semanal(estudiante_id, bloques, horas_disponibles)
                st.success("Plan guardado correctamente. " + recomendacion)
                if vista_plan == "Semanal":
                    render_calendario(horarios, bloques, "Nuevo calendario semanal", fecha_inicio=fecha_inicio_plan, horizonte_dias=7)
                else:
                    render_calendario_mensual(horarios, bloques, "Nuevo calendario mensual", fecha_inicio=fecha_inicio_plan)

elif menu == "Coach IA":
    st.header("🤖 Coach académico con IA")
    estudiante_id, estudiante_texto = seleccionar_estudiante()
    if estudiante_id is not None:
        diagnostico = obtener_ultimo_diagnostico(estudiante_id)
        resumen = obtener_resumen_tareas(estudiante_id)
        cursos_dificultad = obtener_cursos_mayor_dificultad(estudiante_id)
        ultima = obtener_ultima_recomendacion_coach(estudiante_id)
        if ultima:
            st.subheader("Última recomendación guardada")
            st.caption(f"Generada: {ultima.get('fecha')}")
            st.markdown(ultima.get("recomendacion") or "")
        if diagnostico is None:
            st.warning("Este estudiante aún no tiene diagnóstico registrado.")
        else:
            nombre = obtener_nombre_desde_texto(estudiante_texto)
            horas, promedio, tareas_pend, estres, motivacion, procrast, puntaje, riesgo, _ = diagnostico
            riesgo = nivel_por_puntaje(puntaje)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Riesgo", riesgo)
            c2.metric("Puntaje", f"{puntaje}/100")
            c3.metric("Pendientes", resumen["pendientes"])
            c4.metric("Alta prioridad", resumen["alta_prioridad"])
            if st.button("✨ Generar nueva recomendación"):
                with st.spinner("AURA está generando una recomendación personalizada..."):
                    rec = generar_recomendacion_ia(nombre, horas, promedio, tareas_pend, estres, motivacion, procrast, puntaje, riesgo, resumen, cursos_dificultad)
                guardar_recomendacion_coach(estudiante_id, rec)
                st.success("Recomendación generada y guardada.")
                st.markdown(rec)

elif menu == "Panel de Tutoría":
    st.header("🧑‍🏫 Panel de Tutoría")
    datos = obtener_panel_tutoria()
    if not datos:
        st.info("Aún no hay estudiantes registrados.")
    else:
        df = pd.DataFrame(datos, columns=["ID", "Nombre", "Código", "Carrera", "Ciclo", "Promedio ponderado", "Estrés", "Motivación", "Procrastinación", "Estado de ánimo", "Alerta emocional", "Puntaje riesgo", "Nivel riesgo", "Fecha diagnóstico", "Total tareas", "Tareas pendientes", "Alta prioridad"])
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total", len(df))
        c2.metric("Riesgo alto", len(df[df["Nivel riesgo"] == "Alto"]))
        c3.metric("Riesgo medio", len(df[df["Nivel riesgo"] == "Medio"]))
        c4.metric("Riesgo bajo", len(df[df["Nivel riesgo"] == "Bajo"]))
        c5.metric("Alertas", len(df[df["Alerta emocional"] == 1]))
        filtro = st.selectbox("Filtrar por riesgo", ["Todos", "Alto", "Medio", "Bajo", "Sin diagnóstico"])
        filtrado = df.copy()
        if filtro != "Todos":
            filtrado = filtrado[filtrado["Nivel riesgo"].isna()] if filtro == "Sin diagnóstico" else filtrado[filtrado["Nivel riesgo"] == filtro]
        st.dataframe(filtrado, use_container_width=True)
        conteo = df["Nivel riesgo"].fillna("Sin diagnóstico").value_counts().reset_index()
        conteo.columns = ["Nivel de riesgo", "Cantidad"]
        st.plotly_chart(px.bar(conteo, x="Nivel de riesgo", y="Cantidad", text="Cantidad", color="Nivel de riesgo", color_discrete_sequence=PALETA), use_container_width=True)

elif menu == "Gestión de usuarios":
    st.header("🛠️ Gestión de usuarios")
    estudiantes = listar_estudiantes()
    opciones_est = {"Sin vincular": None}
    for e in estudiantes:
        opciones_est[f"{e[1]} | Código: {e[2]}"] = e[0]
    with st.popover("➕ Crear usuario"):
        with st.form("form_crear_usuario"):
            username = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            rol = st.selectbox("Rol", ["Estudiante", "Tutor", "Administrador"])
            est_txt = st.selectbox("Vincular estudiante", list(opciones_est.keys()))
            if st.form_submit_button("Crear usuario"):
                estudiante_link = opciones_est[est_txt]
                if rol == "Estudiante" and estudiante_link is None:
                    st.error("Un estudiante debe estar vinculado.")
                else:
                    exito, msg = registrar_usuario(username, password, rol, estudiante_link)
                    st.success(msg) if exito else st.error(msg)
                    if exito:
                        st.rerun()
    usuarios = listar_usuarios()
    if usuarios:
        st.dataframe(pd.DataFrame(usuarios, columns=["ID", "Usuario", "Rol", "Estudiante vinculado", "Fecha"]), use_container_width=True)
        with st.expander("✏️ Editar o eliminar usuario"):
            opts = {f"{u[1]} | {u[2]}": u for u in usuarios}
            sel = st.selectbox("Usuario", list(opts.keys()))
            u = opts[sel]
            with st.form("form_edit_usuario"):
                user_n = st.text_input("Usuario", value=u[1])
                pass_n = st.text_input("Nueva contraseña (opcional)", type="password")
                cg, cb = st.columns(2)
                if cg.form_submit_button("Actualizar"):
                    exito, msg = actualizar_usuario(u[0], user_n, pass_n)
                    st.success(msg) if exito else st.error(msg)
                if cb.form_submit_button("Eliminar"):
                    if u[0] == usuario_actual["id"]:
                        st.error("No puedes eliminar tu propio usuario mientras estás logueado.")
                    else:
                        exito, msg = eliminar_usuario(u[0])
                        st.success(msg) if exito else st.error(msg)
                        if exito:
                            st.rerun()

elif menu == "Reportes":
    st.header("📄 Generación de reportes")
    estudiante_id, _ = seleccionar_estudiante()
    if estudiante_id is not None:
        estudiante = obtener_estudiante_por_id(estudiante_id)
        if estudiante:
            _, nombre, codigo, carrera, ciclo = estudiante
            diagnostico = obtener_ultimo_diagnostico(estudiante_id)
            detalle = obtener_ultimo_diagnostico_detallado(estudiante_id)
            resumen = obtener_resumen_tareas(estudiante_id)
            cursos = listar_cursos_por_estudiante(estudiante_id)
            tareas = listar_tareas_por_estudiante(estudiante_id)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Estudiante", nombre)
            c2.metric("Cursos", len(cursos))
            c3.metric("Tareas", resumen["total"])
            c4.metric("Riesgo", diagnostico[7] if diagnostico else "Sin diagnóstico")
            excel = crear_excel_reporte(nombre, codigo, carrera, ciclo, diagnostico, detalle, resumen, cursos, tareas)
            pdf = crear_pdf_reporte(nombre, codigo, carrera, ciclo, diagnostico, detalle, resumen, cursos, tareas)
            nombre_limpio = nombre.replace(" ", "_").lower()
            colx, colp = st.columns(2)
            colx.download_button("⬇️ Descargar Excel", excel, file_name=f"reporte_aura_{nombre_limpio}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            colp.download_button("⬇️ Descargar PDF", pdf, file_name=f"reporte_aura_{nombre_limpio}.pdf", mime="application/pdf")

elif menu == "Exportar datos":
    st.header("📦 Exportar datos")
    tabla = st.selectbox("Tabla", ["estudiantes", "usuarios", "diagnosticos", "cursos", "tareas", "horarios_clase", "planes_semanales", "coach_recomendaciones"])
    columnas, filas = obtener_tabla_completa(tabla)
    df = pd.DataFrame(filas, columns=columnas)
    st.dataframe(df, use_container_width=True)
    st.download_button("Descargar CSV", df.to_csv(index=False).encode("utf-8"), file_name=f"aura_{tabla}.csv", mime="text/csv")
