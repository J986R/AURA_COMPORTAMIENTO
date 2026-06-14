from pathlib import Path
from datetime import date
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
from planner import generar_plan_calendario_respaldo
from report_generator import crear_excel_reporte, crear_pdf_reporte

LOGO_PATH = Path(__file__).parent / "assets" / "logo_aura.png"

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
PALETA = ["#0B1F4D", "#14B8B8", "#7C3AED", "#2563EB", "#16A34A", "#F59E0B", "#DC2626"]


def aplicar_estilos():
    st.markdown(
        """
        <style>
        :root{
            --aura-navy:#0B1F4D;
            --aura-cyan:#14B8B8;
            --aura-purple:#7C3AED;
            --aura-soft:#F4F8FB;
            --aura-card:#FFFFFF;
        }
        .block-container{padding-top:1.2rem;}
        h1,h2,h3{letter-spacing:-0.02em;}
        div[data-testid="stSidebar"]{background:linear-gradient(180deg,#0B1F4D 0%,#102A63 55%,#111827 100%);}
        div[data-testid="stSidebar"] *{color:white;}
        .aura-hero{
            border-radius:24px;
            padding:26px 30px;
            background:linear-gradient(135deg,#0B1F4D 0%,#123A77 52%,#14B8B8 115%);
            color:white;
            box-shadow:0 18px 45px rgba(11,31,77,.22);
            margin-bottom:18px;
        }
        .aura-hero h1{margin:0;font-size:2.1rem;color:white;}
        .aura-hero p{margin:8px 0 0 0;opacity:.92;}
        .aura-card{
            background:var(--aura-card);
            border:1px solid rgba(11,31,77,.08);
            border-radius:20px;
            padding:18px 20px;
            box-shadow:0 8px 24px rgba(11,31,77,.06);
            margin-bottom:15px;
        }
        .aura-pill{
            display:inline-flex;
            align-items:center;
            border-radius:999px;
            padding:6px 12px;
            background:rgba(20,184,184,.12);
            color:#0B1F4D;
            font-weight:700;
            font-size:.88rem;
            margin-right:8px;
        }
        .stButton > button, .stDownloadButton > button{
            border-radius:14px !important;
            border:1px solid rgba(20,184,184,.35) !important;
            background:linear-gradient(135deg,#0B1F4D,#14B8B8) !important;
            color:white !important;
            font-weight:700 !important;
            padding:.55rem 1rem !important;
            box-shadow:0 8px 18px rgba(20,184,184,.18);
        }
        .stButton > button:hover, .stDownloadButton > button:hover{
            transform:translateY(-1px);
            border-color:#7C3AED !important;
        }
        div[data-testid="stMetric"]{
            background:white;
            border:1px solid rgba(11,31,77,.08);
            border-radius:18px;
            padding:14px 16px;
            box-shadow:0 6px 18px rgba(11,31,77,.05);
        }
        .aura-calendar{
            background:white;
            border:1px solid rgba(11,31,77,.10);
            border-radius:22px;
            overflow:hidden;
            box-shadow:0 10px 30px rgba(11,31,77,.07);
        }
        .aura-cal-head{display:grid;grid-template-columns:72px repeat(7,1fr);background:#F8FAFC;border-bottom:1px solid #E5E7EB;}
        .aura-cal-head div{padding:12px 10px;font-weight:800;text-align:center;color:#0B1F4D;}
        .aura-cal-body{display:grid;grid-template-columns:72px repeat(7,1fr);height:960px;position:relative;}
        .aura-time-col{background:#F8FAFC;border-right:1px solid #E5E7EB;position:relative;}
        .aura-time{position:absolute;left:10px;font-size:12px;color:#475569;transform:translateY(-8px);}
        .aura-day-col{position:relative;border-right:1px solid #E5E7EB;background-image:linear-gradient(to bottom,#E5E7EB 1px,transparent 1px);background-size:100% 60px;}
        .aura-day-col:last-child{border-right:none;}
        .aura-event{position:absolute;left:6px;right:6px;border-radius:12px;padding:8px 9px;color:white;font-size:12px;line-height:1.20;overflow:hidden;box-shadow:0 8px 18px rgba(15,23,42,.15);}
        .aura-event small{display:block;opacity:.95;font-weight:600;margin-top:3px;}
        .aura-event.clase{background:#0B1F4D;}
        .aura-event.estudio{background:#14B8B8;}
        .aura-muted{color:#64748B;font-size:.92rem;}
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


def bloques_clase_para_calendar(horarios):
    bloques = []
    for h in horarios or []:
        bloques.append({
            "tipo": "Clase",
            "dia": h.get("dia"),
            "inicio": h.get("inicio"),
            "fin": h.get("fin"),
            "curso": h.get("codigo_curso") or h.get("nombre_curso"),
            "actividad": f"{h.get('tipo','Clase')} · {h.get('aula','')}",
            "tarea_origen": h.get("docente", ""),
            "prioridad": "Clase",
            "color": h.get("color") or "#0B1F4D",
        })
    return bloques


def render_calendario(horarios=None, bloques_estudio=None, titulo="Calendario semanal"):
    horarios = horarios or []
    bloques_estudio = bloques_estudio or []
    bloques = bloques_clase_para_calendar(horarios) + bloques_estudio
    min_hour, max_hour, px_h = 7, 23, 60
    height = (max_hour - min_hour) * px_h

    head = "<div class='aura-cal-head'><div>GMT-05</div>" + "".join([f"<div>{d[:3].upper()}</div>" for d in DIAS]) + "</div>"
    time_labels = "".join([f"<div class='aura-time' style='top:{(h-min_hour)*px_h}px'>{h:02d}:00</div>" for h in range(min_hour, max_hour + 1)])
    cols = [f"<div class='aura-time-col'>{time_labels}</div>"]
    for d in DIAS:
        events = []
        for b in bloques:
            if b.get("dia") != d:
                continue
            ini = max(min_hour, time_to_float(b.get("inicio")))
            fin = min(max_hour, time_to_float(b.get("fin")))
            if fin <= ini:
                fin = ini + 1
            top = (ini - min_hour) * px_h
            hgt = max(28, (fin - ini) * px_h - 4)
            color = escape(b.get("color") or ("#0B1F4D" if b.get("tipo") == "Clase" else "#14B8B8"))
            clase = "clase" if b.get("tipo") == "Clase" else "estudio"
            titulo_b = escape(b.get("curso", "Actividad"))
            actividad = escape(b.get("actividad", ""))
            hora = f"{escape(b.get('inicio'))} - {escape(b.get('fin'))}"
            tarea = escape(b.get("tarea_origen", ""))
            events.append(
                f"<div class='aura-event {clase}' style='top:{top}px;height:{hgt}px;background:{color};'>"
                f"<b>{titulo_b}</b><br><span>{actividad}</span><small>{hora}</small><small>{tarea}</small></div>"
            )
        cols.append(f"<div class='aura-day-col'>{''.join(events)}</div>")
    body = f"<div class='aura-cal-body' style='height:{height}px;'>" + "".join(cols) + "</div>"
    st.subheader(titulo)
    st.markdown(f"<div class='aura-calendar'>{head}{body}</div>", unsafe_allow_html=True)


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

if rol_actual == "Administrador":
    opciones_menu = ["Inicio", "Dashboard estudiante", "Perfil y Cursos", "Diagnóstico académico", "Tareas y Planificador", "Coach IA", "Panel de Tutoría", "Gestión de usuarios", "Reportes", "Exportar datos"]
    default_index = 0
elif rol_actual == "Tutor":
    opciones_menu = ["Dashboard estudiante", "Perfil y Cursos", "Diagnóstico académico", "Tareas y Planificador", "Coach IA", "Panel de Tutoría", "Reportes"]
    default_index = 0
else:
    opciones_menu = ["Dashboard estudiante", "Perfil y Cursos", "Diagnóstico académico", "Tareas y Planificador", "Coach IA", "Reportes"]
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

elif menu == "Dashboard estudiante":
    st.header("📊 Dashboard del estudiante")
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
                st.plotly_chart(px.bar(df_ind, x="Indicador", y="Nivel", text="Nivel", range_y=[0, 5], color="Indicador", color_discrete_sequence=PALETA), use_container_width=True)
            with col2:
                st.subheader("Cursos con mayor dificultad")
                if cursos_dificultad:
                    df_dif = pd.DataFrame(cursos_dificultad, columns=["Curso", "Dificultad"])
                    st.plotly_chart(px.bar(df_dif, x="Curso", y="Dificultad", text="Dificultad", range_y=[0, 5], color="Curso", color_discrete_sequence=PALETA), use_container_width=True)
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

elif menu == "Perfil y Cursos":
    st.header("👤 Perfil y Cursos")
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

elif menu == "Diagnóstico académico":
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
                    titulo = st.text_input("Título de la tarea")
                    descripcion = st.text_area("Descripción")
                    fecha_entrega = st.date_input("Fecha de entrega", value=date.today())
                    if st.form_submit_button("Guardar tarea"):
                        curso = opciones_cursos[curso_txt]
                        if not titulo.strip():
                            st.error("Ingresa el título.")
                        elif existe_tarea(estudiante_id, curso[0], titulo):
                            st.warning("Esta tarea ya existe para este curso.")
                        else:
                            registrar_tarea(estudiante_id, curso[0], titulo, descripcion, fecha_entrega.strftime("%Y-%m-%d"), int(curso[4] or 3))
                            st.success("Tarea registrada.")
                            st.rerun()

        if tareas:
            st.dataframe(pd.DataFrame(tareas, columns=["ID", "Tarea", "Curso", "Fecha de entrega", "Prioridad", "Estado"]), use_container_width=True)
            with st.expander("✏️ Editar o eliminar tarea"):
                opciones_t = {f"{t[1]} | {t[2]} | {t[5]}": t[0] for t in tareas}
                tarea_sel = st.selectbox("Tarea", list(opciones_t.keys()))
                tarea_id = opciones_t[tarea_sel]
                tarea_info = obtener_tarea_por_id(tarea_id)
                if tarea_info and cursos:
                    curso_ids = [c[0] for c in cursos]
                    idx_curso = curso_ids.index(tarea_info[2]) if tarea_info[2] in curso_ids else 0
                    with st.form("form_edit_tarea"):
                        curso_opciones = {c[1]: c for c in cursos}
                        curso_nombre = st.selectbox("Curso", list(curso_opciones.keys()), index=idx_curso)
                        e_titulo = st.text_input("Título", value=tarea_info[3] or "")
                        e_desc = st.text_area("Descripción", value=tarea_info[4] or "")
                        e_fecha = st.date_input("Fecha de entrega", value=tarea_info[5] or date.today())
                        estados = ["Pendiente", "En proceso", "Completada"]
                        e_estado = st.selectbox("Estado", estados, index=estados.index(tarea_info[7]) if tarea_info[7] in estados else 0)
                        colg, colb = st.columns(2)
                        if colg.form_submit_button("💾 Actualizar tarea"):
                            curso_nuevo = curso_opciones[curso_nombre]
                            actualizar_tarea(tarea_id, curso_nuevo[0], e_titulo, e_desc, e_fecha.strftime("%Y-%m-%d"), e_estado, int(curso_nuevo[4] or 3))
                            st.success("Tarea actualizada.")
                            st.rerun()
                        if colb.form_submit_button("🗑️ Eliminar tarea"):
                            eliminar_tarea(tarea_id)
                            st.warning("Tarea eliminada.")
                            st.rerun()
        else:
            st.info("Aún no hay tareas registradas.")

        st.divider()
        st.subheader("🗓️ Planificador calendario")
        bloques_guardados = (ultimo_plan or {}).get("plan", []) if ultimo_plan else []
        render_calendario(horarios, bloques_guardados, "Calendario actual")
        if ultimo_plan:
            st.caption(f"Último plan generado: {ultimo_plan.get('fecha')} | Horas: {ultimo_plan.get('horas_disponibles')} h/semana")

        if diagnostico is None:
            st.warning("Registra primero un diagnóstico para personalizar el plan.")
        elif not tareas_plan:
            st.warning("Registra tareas para generar un plan de estudio.")
        else:
            nombre = obtener_nombre_desde_texto(estudiante_texto)
            horas, promedio, _, estres, motivacion, procrast, puntaje, riesgo, _ = diagnostico
            riesgo = nivel_por_puntaje(puntaje)
            c1, c2, c3 = st.columns(3)
            horas_disponibles = c1.number_input("Horas disponibles para estudiar esta semana", 1.0, 80.0, value=float(max(1, horas * 7)), step=1.0)
            c2.metric("Riesgo", riesgo)
            c3.metric("Tareas activas", len([t for t in tareas_plan if t.get("estado") != "Completada"]))
            diag_plan = {
                "promedio_ponderado": promedio,
                "nivel_riesgo": riesgo,
                "puntaje_riesgo": puntaje,
                "indice_estres": detalle.get("indice_estres") if detalle else estres,
                "indice_procrastinacion": detalle.get("indice_procrastinacion") if detalle else procrast,
                "indice_motivacion": detalle.get("indice_motivacion") if detalle else motivacion,
                "indice_estado_animo": detalle.get("indice_estado_animo") if detalle else 3,
            }
            if st.button("🤖 Generar nuevo calendario con IA"):
                with st.spinner("AURA está armando tu calendario sin cruzar clases..."):
                    resultado = generar_plan_calendario_ia(nombre, diag_plan, tareas_plan, horarios, horas_disponibles)
                if resultado.get("exito"):
                    bloques = resultado.get("bloques", [])
                    st.success(resultado.get("recomendacion_general", "Plan generado con IA."))
                else:
                    st.error("No se pudo generar con IA. Se usará un plan de respaldo.")
                    st.code(resultado.get("error", "Error desconocido"))
                    bloques = generar_plan_calendario_respaldo(tareas_plan, horarios, horas_disponibles, riesgo)
                guardar_plan_semanal(estudiante_id, bloques, horas_disponibles)
                st.success("Plan guardado correctamente.")
                render_calendario(horarios, bloques, "Nuevo calendario generado")

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
