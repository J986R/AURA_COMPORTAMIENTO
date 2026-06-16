from pathlib import Path
from datetime import date, datetime, timedelta
import html

import pandas as pd
import plotly.express as px
import streamlit as st

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


def render_calendario(horarios=None, bloques_estudio=None, titulo="Calendario semanal", fecha_inicio=None, horizonte_dias=7):
    horarios = horarios or []
    bloques_estudio = bloques_estudio or []
    fecha_inicio = fecha_inicio or date.today()
    fechas = rango_fechas(fecha_inicio, horizonte_dias)
    bloques = bloques_clase_para_calendar(horarios, fechas) + bloques_estudio
    min_hour, max_hour, px_h = 7, 23, 60
    height = (max_hour - min_hour) * px_h

    toolbar = f"""
    <div class='aura-calendar-toolbar'>
        <div class='aura-toolbar-left'><span class='aura-icon-btn'>☰</span><span class='aura-icon-btn'>📅 Hoy</span><span>{escape(titulo)}</span></div>
        <div><span class='aura-icon-btn'>🔎 Buscar</span><span class='aura-icon-btn'>⚙️ Semana</span></div>
    </div>
    """
    head_cells = ["<div>GMT-05</div>"]
    for f in fechas[:7]:
        head_cells.append(f"<div><small>{fecha_a_dia(f)[:3].upper()}</small><br><b>{f.day}</b></div>")
    head = "<div class='aura-cal-head'>" + "".join(head_cells) + "</div>"
    time_labels = "".join([f"<div class='aura-time' style='top:{(h-min_hour)*px_h}px'>{h:02d}:00</div>" for h in range(min_hour, max_hour + 1)])
    cols = [f"<div class='aura-time-col'>{time_labels}</div>"]
    for f in fechas[:7]:
        d = fecha_a_dia(f)
        f_iso = f.isoformat()
        events = []
        for b in bloques:
            b_fecha = str(b.get("fecha", ""))[:10]
            if b_fecha:
                if b_fecha != f_iso:
                    continue
            elif b.get("dia") != d:
                continue
            ini = max(min_hour, time_to_float(b.get("inicio")))
            fin = min(max_hour, time_to_float(b.get("fin")))
            if fin <= ini:
                fin = ini + 1
            top = (ini - min_hour) * px_h
            hgt = max(30, (fin - ini) * px_h - 4)
            color = escape(b.get("color") or ("#BDE0FE" if b.get("tipo") == "Clase" else "#A7F3D0"))
            tipo_lower = str(b.get("tipo", "")).lower()
            act_lower = str(b.get("tipo_actividad", b.get("actividad", ""))).lower()
            if "clase" in tipo_lower:
                clase = "clase"
            elif "almuerzo" in tipo_lower or "descanso" in tipo_lower:
                clase = "descanso"
            elif "final" in act_lower or "parcial" in act_lower or "examen" in act_lower:
                clase = "estudio examen"
            elif "monograf" in act_lower:
                clase = "estudio monografia"
            elif "práctica" in act_lower or "practica" in act_lower:
                clase = "estudio practica"
            elif "tarea" in act_lower:
                clase = "estudio tarea"
            else:
                clase = "estudio"
            titulo_b = escape(b.get("curso", "Actividad"))
            actividad = escape(b.get("actividad", ""))
            hora = f"{escape(b.get('inicio'))} - {escape(b.get('fin'))}"
            tarea = escape(b.get("tarea_origen", ""))
            tipo_act = escape(b.get("tipo_actividad", ""))
            if tipo_act:
                tarea = f"{tipo_act} · {tarea}" if tarea else tipo_act
            events.append(
                f"<div class='aura-event {clase}' style='top:{top}px;height:{hgt}px;background:{color};'>"
                f"<b>{titulo_b}</b><br><span>{actividad}</span><small>{hora}</small><small>{tarea}</small></div>"
            )
        cols.append(f"<div class='aura-day-col'>{''.join(events)}</div>")
    body = f"<div class='aura-cal-body' style='height:{height}px;'>" + "".join(cols) + "</div>"
    st.markdown(toolbar, unsafe_allow_html=True)
    st.markdown(f"<div class='aura-calendar'>{head}{body}</div>", unsafe_allow_html=True)


def render_calendario_mensual(horarios=None, bloques_estudio=None, titulo="Calendario mensual", fecha_inicio=None):
    horarios = horarios or []
    bloques_estudio = bloques_estudio or []
    fecha_inicio = fecha_inicio or date.today()
    primer_dia = date(fecha_inicio.year, fecha_inicio.month, 1)
    if fecha_inicio.month == 12:
        siguiente = date(fecha_inicio.year + 1, 1, 1)
    else:
        siguiente = date(fecha_inicio.year, fecha_inicio.month + 1, 1)
    ultimo_dia = siguiente - timedelta(days=1)
    fechas_mes = rango_fechas(primer_dia, (ultimo_dia - primer_dia).days + 1)
    bloques_clase = bloques_clase_para_calendar(horarios, fechas_mes)
    bloques = bloques_clase + (bloques_estudio or [])
    por_fecha = {}
    for b in bloques:
        f = str(b.get("fecha", ""))[:10]
        if not f:
            continue
        por_fecha.setdefault(f, []).append(b)

    st.subheader(titulo)
    heads = "".join([f"<div class='aura-month-head'>{d[:3]}</div>" for d in DIAS])
    html_mes = ["<div class='aura-month'>", heads]
    for _ in range(primer_dia.weekday()):
        html_mes.append("<div class='aura-month-day empty'></div>")
    for f in fechas_mes:
        eventos = por_fecha.get(f.isoformat(), [])
        eventos = sorted(eventos, key=lambda x: str(x.get("inicio", "00:00")))[:5]
        ev_html = ""
        for e in eventos:
            color = escape(e.get("color") or "#A7F3D0")
            act_lower = str(e.get("tipo_actividad", e.get("actividad", ""))).lower()
            clase_ev = ""
            if "final" in act_lower or "parcial" in act_lower or "examen" in act_lower:
                clase_ev = " examen"
            elif "monograf" in act_lower:
                clase_ev = " monografia"
            elif "práctica" in act_lower or "practica" in act_lower:
                clase_ev = " practica"
            elif "tarea" in act_lower:
                clase_ev = " tarea"
            etiqueta = escape(f"{e.get('inicio','')} {e.get('curso','')} · {e.get('actividad','')}")
            ev_html += f"<div class='aura-month-event{clase_ev}' style='background:{color};'>{etiqueta}</div>"
        if len(por_fecha.get(f.isoformat(), [])) > 5:
            ev_html += f"<div class='aura-muted'>+{len(por_fecha[f.isoformat()])-5} más</div>"
        marca_hoy = " style='outline:2px solid #60A5FA;'" if f == date.today() else ""
        html_mes.append(f"<div class='aura-month-day'{marca_hoy}><div class='aura-day-number'>{f.day}</div>{ev_html}</div>")
    html_mes.append("</div>")
    st.markdown("".join(html_mes), unsafe_allow_html=True)

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
                    if st.form_submit_button("Guardar curso"):
                        if not nombre_curso.strip():
                            st.error("Ingresa el nombre del curso.")
                        elif existe_curso(estudiante_id, nombre_curso):
                            st.warning("Este curso ya está registrado.")
                        else:
                            registrar_curso(estudiante_id, nombre_curso, docente, creditos, dificultad, estado)
                            st.success("Curso registrado.")
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

        horarios = listar_horarios_clase(estudiante_id)
        render_calendario(horarios, [], "🗓️ Horario de clases")
        if horarios and st.button("🧹 Limpiar horarios importados"):
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
