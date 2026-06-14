from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from ai_engine import generar_diagnostico_ia, generar_plan_semanal_ia, generar_recomendacion_ia, nivel_por_puntaje
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
    listar_cursos_por_estudiante,
    listar_estudiantes,
    listar_tareas_para_planificador,
    listar_tareas_por_estudiante,
    listar_usuarios,
    obtener_cursos_mayor_dificultad,
    obtener_estudiante_por_id,
    obtener_panel_tutoria,
    obtener_tarea_por_id,
    obtener_ultimo_plan_semanal,
    obtener_ultima_recomendacion_coach,
    obtener_resumen_tareas,
    obtener_tabla_completa,
    obtener_ultimo_diagnostico,
    obtener_ultimo_diagnostico_detallado,
    obtener_usuario_por_id,
    registrar_curso,
    registrar_estudiante,
    registrar_tarea,
    registrar_usuario,
)
from planner import generar_plan_semanal
from report_generator import crear_excel_reporte, crear_pdf_reporte

LOGO_PATH = Path(__file__).parent / "assets" / "logo_aura.png"

st.set_page_config(
    page_title="AURA - Coach Académico Inteligente",
    page_icon="🎓",
    layout="wide",
)

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

ESCALA_OPCIONES = [
    "1 - Nunca",
    "2 - Casi nunca",
    "3 - A veces",
    "4 - Casi siempre",
    "5 - Siempre",
]


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


def mostrar_logo(ancho=240):
    if LOGO_PATH.exists():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(str(LOGO_PATH), width=ancho)


def mostrar_login():
    mostrar_logo(240)
    st.title("AURA")
    st.subheader("Inicio de sesión")
    st.info("Usuario inicial: admin | Contraseña inicial: aura123")

    with st.form("form_login"):
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        boton = st.form_submit_button("Ingresar")
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
    usuario_actual = st.session_state.usuario_logueado
    if usuario_actual["rol"] == "Estudiante":
        estudiante_id = usuario_actual["estudiante_id"]
        if estudiante_id is None:
            st.error("Este usuario estudiante no está vinculado a ningún estudiante registrado.")
            return None, None
        estudiante = obtener_estudiante_por_id(estudiante_id)
        if estudiante is None:
            st.error("No se encontró el estudiante vinculado a este usuario.")
            return None, None
        texto = f"{estudiante[1]} | Código: {estudiante[2]} | Ciclo: {estudiante[4]}"
        st.info(f"Estudiante: {texto}")
        return estudiante_id, texto

    estudiantes = listar_estudiantes()
    if len(estudiantes) == 0:
        st.warning("Primero debes registrar al menos un estudiante.")
        return None, None

    opciones = {f"{e[1]} | Código: {e[2]} | Ciclo: {e[4]}": e[0] for e in estudiantes}
    estudiante_texto = st.selectbox(label, list(opciones.keys()))
    return opciones[estudiante_texto], estudiante_texto


def df_or_info(data, columns, msg="No hay registros."):
    if not data:
        st.info(msg)
        return None
    df = pd.DataFrame(data, columns=columns)
    st.dataframe(df, use_container_width=True)
    return df


def num_a_escala(valor):
    try:
        valor = int(valor)
    except Exception:
        valor = 3
    valor = max(1, min(5, valor))
    return ESCALA_OPCIONES[valor - 1]


def escala_a_num(texto):
    return int(str(texto).split("-")[0].strip())


def reset_diagnostico_si_cambia_estudiante(estudiante_id):
    if st.session_state.get("diagnostico_estudiante_activo") != estudiante_id:
        for key in list(st.session_state.keys()):
            if key.startswith("diag_"):
                del st.session_state[key]
        st.session_state["diagnostico_estudiante_activo"] = estudiante_id


def mostrar_estado_riesgo(nivel, puntaje):
    if nivel == "Alto":
        st.error(f"Riesgo académico IA: {nivel} | Puntaje: {puntaje}/100")
    elif nivel == "Medio":
        st.warning(f"Riesgo académico IA: {nivel} | Puntaje: {puntaje}/100")
    else:
        st.success(f"Riesgo académico IA: {nivel} | Puntaje: {puntaje}/100")


def mostrar_plan_guardado(plan):
    if not plan:
        st.info("No hay actividades asignadas en el plan.")
        return
    for dia in plan:
        st.subheader(dia.get("dia", "Día"))
        st.caption(f"Horas disponibles aproximadas: {dia.get('horas_disponibles', 0)} h")
        if dia.get("recomendacion"):
            st.info(dia.get("recomendacion"))
        tareas_dia = dia.get("tareas", []) or []
        if tareas_dia:
            st.dataframe(pd.DataFrame(tareas_dia), use_container_width=True)
        else:
            st.write("Sin actividades asignadas.")


safe_init()

if "usuario_logueado" not in st.session_state:
    st.session_state.usuario_logueado = None

if st.session_state.usuario_logueado is None:
    mostrar_login()
    st.stop()

usuario_actual = st.session_state.usuario_logueado
rol_actual = usuario_actual["rol"]

if LOGO_PATH.exists():
    st.sidebar.image(str(LOGO_PATH), use_container_width=True)
else:
    st.sidebar.title("🎓 AURA")

st.sidebar.success(f"Usuario: {usuario_actual['username']}")
st.sidebar.info(f"Rol: {rol_actual}")
if st.sidebar.button("Cerrar sesión"):
    cerrar_sesion()

if rol_actual == "Administrador":
    opciones_menu = [
        "Inicio",
        "Mi perfil",
        "Registrar estudiante",
        "Gestión de usuarios",
        "Diagnóstico académico",
        "Cursos",
        "Tareas",
        "Dashboard estudiante",
        "Planificador semanal",
        "Coach IA",
        "Panel de Tutoría",
        "Reportes",
        "Exportar datos",
    ]
elif rol_actual == "Tutor":
    opciones_menu = ["Inicio", "Mi perfil", "Dashboard estudiante", "Planificador semanal", "Coach IA", "Panel de Tutoría", "Reportes"]
else:
    opciones_menu = ["Inicio", "Mi perfil", "Diagnóstico académico", "Cursos", "Tareas", "Dashboard estudiante", "Planificador semanal", "Coach IA", "Reportes"]

menu = st.sidebar.radio("Menú principal", opciones_menu)

mostrar_logo(170)
st.title("AURA")
st.caption("Academic University Recommendation Assistant | Neon PostgreSQL + Gemini IA")

if menu == "Inicio":
    st.header("Bienvenido a AURA")
    st.write(
        """
        AURA es una plataforma web de acompañamiento académico. Usa una base de datos en la nube
        con Neon PostgreSQL y diagnóstico, coaching y planificación con Gemini API.
        """
    )
    st.info("Flujo recomendado: registrar estudiante → crear usuario → diagnóstico IA → cursos → tareas → dashboard → planificador → reportes.")
    c1, c2, c3 = st.columns(3)
    c1.metric("Base de datos", "Neon")
    c2.metric("IA", "Gemini")
    c3.metric("Modo", "Web")

elif menu == "Mi perfil":
    st.header("Mi perfil")
    usuario_db = obtener_usuario_por_id(usuario_actual["id"])
    if usuario_db is None:
        st.error("No se encontró información del usuario actual.")
    else:
        _, username_db, rol_db, estudiante_id_db, estudiante_nombre = usuario_db
        st.subheader("Datos de acceso")
        with st.form("form_actualizar_usuario"):
            nuevo_username = st.text_input("Nombre de usuario", value=username_db or "")
            nueva_password = st.text_input("Nueva contraseña (opcional)", type="password", help="Déjalo vacío si no deseas cambiarla.")
            confirmar_password = st.text_input("Confirmar nueva contraseña", type="password")
            boton_usuario = st.form_submit_button("Guardar datos de acceso")
            if boton_usuario:
                if not nuevo_username.strip():
                    st.error("El nombre de usuario no puede estar vacío.")
                elif nueva_password and nueva_password != confirmar_password:
                    st.error("Las contraseñas no coinciden.")
                else:
                    exito, mensaje = actualizar_usuario(usuario_actual["id"], nuevo_username.strip(), nueva_password if nueva_password else None)
                    if exito:
                        st.session_state.usuario_logueado["username"] = nuevo_username.strip()
                        st.success(mensaje)
                        st.rerun()
                    else:
                        st.error(mensaje)

        if estudiante_id_db is not None:
            estudiante = obtener_estudiante_por_id(estudiante_id_db)
            if estudiante:
                st.subheader("Datos del estudiante vinculado")
                _, nombre, codigo, carrera, ciclo = estudiante
                with st.form("form_actualizar_estudiante_perfil"):
                    nuevo_nombre = st.text_input("Nombre completo", value=nombre or "")
                    nuevo_codigo = st.text_input("Código universitario", value=codigo or "")
                    nueva_carrera = st.text_input("Carrera", value=carrera or "")
                    nuevo_ciclo = st.selectbox("Ciclo", [str(i) for i in range(1, 11)], index=max(0, min(9, int(ciclo or 1) - 1)) if str(ciclo or "1").isdigit() else 0)
                    boton_est = st.form_submit_button("Guardar datos del estudiante")
                    if boton_est:
                        if not nuevo_nombre.strip():
                            st.error("El nombre del estudiante no puede estar vacío.")
                        else:
                            actualizar_estudiante(estudiante_id_db, nuevo_nombre.strip(), nuevo_codigo.strip(), nueva_carrera.strip(), nuevo_ciclo)
                            st.success("Datos del estudiante actualizados correctamente.")
                            st.rerun()
        else:
            st.info("Tu usuario no está vinculado a un estudiante. Puedes cambiar tus datos de acceso, pero no hay datos académicos asociados a este perfil.")

elif menu == "Registrar estudiante":
    st.header("Registro de estudiante")
    with st.form("form_registro_estudiante"):
        nombre = st.text_input("Nombre completo")
        codigo = st.text_input("Código universitario")
        carrera = st.text_input("Carrera", value="Ingeniería Industrial")
        ciclo = st.selectbox("Ciclo académico", [str(i) for i in range(1, 11)])
        boton = st.form_submit_button("Registrar estudiante")
        if boton:
            if not nombre.strip():
                st.error("Debes ingresar el nombre del estudiante.")
            else:
                registrar_estudiante(nombre.strip(), codigo.strip(), carrera.strip(), ciclo)
                st.success("Estudiante registrado correctamente.")
                st.rerun()

    st.subheader("Estudiantes registrados")
    estudiantes = listar_estudiantes()
    df_or_info(estudiantes, ["ID", "Nombre", "Código", "Carrera", "Ciclo"], "Aún no hay estudiantes registrados.")

    if estudiantes:
        with st.expander("Editar estudiante"):
            opciones_editar = {f"{e[1]} | Código: {e[2]} | Ciclo: {e[4]}": e for e in estudiantes}
            texto = st.selectbox("Selecciona estudiante a editar", list(opciones_editar.keys()))
            e = opciones_editar[texto]
            with st.form("form_editar_estudiante_admin"):
                nombre_e = st.text_input("Nombre", value=e[1] or "")
                codigo_e = st.text_input("Código", value=e[2] or "")
                carrera_e = st.text_input("Carrera", value=e[3] or "")
                ciclo_actual = str(e[4] or "1")
                idx = [str(i) for i in range(1, 11)].index(ciclo_actual) if ciclo_actual in [str(i) for i in range(1, 11)] else 0
                ciclo_e = st.selectbox("Ciclo", [str(i) for i in range(1, 11)], index=idx)
                if st.form_submit_button("Guardar cambios del estudiante"):
                    actualizar_estudiante(e[0], nombre_e.strip(), codigo_e.strip(), carrera_e.strip(), ciclo_e)
                    st.success("Estudiante actualizado correctamente.")
                    st.rerun()

        with st.expander("Eliminar estudiante"):
            st.warning("Al eliminar un estudiante también se eliminarán sus diagnósticos, cursos, tareas y usuarios vinculados.")
            opciones = {f"{e[1]} | Código: {e[2]} | Ciclo: {e[4]}": e[0] for e in estudiantes}
            texto = st.selectbox("Estudiante a eliminar", list(opciones.keys()))
            confirmar = st.checkbox("Confirmo que deseo eliminar este estudiante y todos sus datos asociados")
            if st.button("Eliminar estudiante"):
                if usuario_actual.get("estudiante_id") == opciones[texto]:
                    st.error("No puedes eliminar el estudiante vinculado a tu propio usuario mientras estás logueado.")
                elif confirmar:
                    exito, mensaje = eliminar_estudiante(opciones[texto])
                    st.success(mensaje) if exito else st.error(mensaje)
                    if exito:
                        st.rerun()
                else:
                    st.error("Debes marcar la confirmación antes de eliminar.")

elif menu == "Gestión de usuarios":
    st.header("Gestión de usuarios")
    estudiantes = listar_estudiantes()
    opciones_estudiantes = {"Sin vincular": None}
    opciones_estudiantes.update({f"{e[1]} | Código: {e[2]}": e[0] for e in estudiantes})

    with st.form("form_crear_usuario"):
        username = st.text_input("Nombre de usuario")
        password = st.text_input("Contraseña", type="password")
        rol = st.selectbox("Rol", ["Estudiante", "Tutor", "Administrador"])
        estudiante_texto = st.selectbox("Vincular con estudiante", list(opciones_estudiantes.keys()))
        boton = st.form_submit_button("Crear usuario")
        if boton:
            estudiante_id = opciones_estudiantes[estudiante_texto]
            if not username.strip():
                st.error("Debes ingresar un nombre de usuario.")
            elif not password.strip():
                st.error("Debes ingresar una contraseña.")
            elif rol == "Estudiante" and estudiante_id is None:
                st.error("Un usuario Estudiante debe estar vinculado a un estudiante.")
            else:
                exito, mensaje = registrar_usuario(username.strip(), password, rol, estudiante_id)
                st.success(mensaje) if exito else st.error(mensaje)
                if exito:
                    st.rerun()

    st.subheader("Usuarios registrados")
    usuarios = listar_usuarios()
    df_or_info(usuarios, ["ID", "Usuario", "Rol", "Estudiante vinculado", "Fecha registro"], "No hay usuarios registrados.")

    if usuarios:
        with st.expander("Eliminar usuario"):
            st.warning("No se puede eliminar el usuario actual ni el último administrador.")
            opciones = {f"{u[1]} | Rol: {u[2]} | Estudiante: {u[3]}": u[0] for u in usuarios}
            texto = st.selectbox("Usuario a eliminar", list(opciones.keys()))
            confirmar = st.checkbox("Confirmo que deseo eliminar este usuario")
            if st.button("Eliminar usuario"):
                if opciones[texto] == usuario_actual["id"]:
                    st.error("No puedes eliminar el usuario con el que estás logueado.")
                elif confirmar:
                    exito, mensaje = eliminar_usuario(opciones[texto])
                    st.success(mensaje) if exito else st.error(mensaje)
                    if exito:
                        st.rerun()
                else:
                    st.error("Debes marcar la confirmación antes de eliminar.")

elif menu == "Diagnóstico académico":
    st.header("Diagnóstico académico y de bienestar con IA")
    estudiante_id, estudiante_texto = seleccionar_estudiante()

    if estudiante_id is not None:
        reset_diagnostico_si_cambia_estudiante(estudiante_id)
        detalle = obtener_ultimo_diagnostico_detallado(estudiante_id)
        nombre_estudiante = obtener_nombre_desde_texto(estudiante_texto)

        st.warning("Este diagnóstico es una orientación académica y de bienestar; no es diagnóstico clínico.")
        st.info("En cada pregunta verás la escala completa: 1 Nunca, 2 Casi nunca, 3 A veces, 4 Casi siempre, 5 Siempre.")

        if detalle:
            st.success(f"Se cargó el último diagnóstico guardado. Fecha: {detalle.get('fecha')}")

        default_horas = float(detalle.get("horas_estudio_dia") or 2.0) if detalle else 2.0
        default_promedio = float(detalle.get("promedio_ponderado") or 13.0) if detalle else 13.0
        default_respuestas = detalle.get("respuestas", {}) if detalle else {}

        with st.form("form_diagnostico"):
            col_a, col_b = st.columns(2)
            with col_a:
                horas_estudio_dia = st.number_input(
                    "Horas de estudio por día",
                    min_value=0.0,
                    max_value=16.0,
                    value=default_horas,
                    step=0.5,
                    key="diag_horas",
                )
            with col_b:
                promedio_ponderado = st.number_input(
                    "Promedio ponderado actual",
                    min_value=0.0,
                    max_value=20.0,
                    value=default_promedio,
                    step=0.1,
                    key="diag_promedio",
                )

            respuestas = {}
            for dimension in ["Estrés", "Procrastinación", "Motivación", "Estado de ánimo", "Estado de ánimo / alerta emocional"]:
                st.subheader(dimension)
                for i, (pregunta, dim) in enumerate(PREGUNTAS_DIAGNOSTICO, start=1):
                    if dim == dimension:
                        valor_default = int(default_respuestas.get(i, 3) or 3)
                        seleccion = st.select_slider(
                            f"{i}. {pregunta}",
                            options=ESCALA_OPCIONES,
                            value=num_a_escala(valor_default),
                            key=f"diag_p{i}",
                        )
                        respuestas[i] = escala_a_num(seleccion)

            boton = st.form_submit_button("Generar diagnóstico con IA y guardar")

        if boton:
            with st.spinner("AURA está generando el diagnóstico con Gemini..."):
                resultado = generar_diagnostico_ia(nombre_estudiante, horas_estudio_dia, promedio_ponderado, respuestas)

            if not resultado.get("exito"):
                st.error("No se pudo generar el diagnóstico con IA.")
                st.code(resultado.get("error", "Error desconocido"))
                if resultado.get("respuesta_original"):
                    st.code(resultado["respuesta_original"])
            else:
                resultado["nivel_riesgo"] = nivel_por_puntaje(resultado["puntaje_riesgo"])
                guardar_diagnostico_ia(estudiante_id, horas_estudio_dia, promedio_ponderado, respuestas, resultado)
                st.success("Diagnóstico generado y guardado correctamente.")
                detalle = obtener_ultimo_diagnostico_detallado(estudiante_id)

        if detalle:
            st.divider()
            st.subheader("Último diagnóstico guardado")
            mostrar_estado_riesgo(detalle.get("nivel_riesgo"), detalle.get("puntaje_riesgo"))
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Estrés", detalle.get("indice_estres"))
            c2.metric("Procrastinación", detalle.get("indice_procrastinacion"))
            c3.metric("Motivación", detalle.get("indice_motivacion"))
            c4.metric("Estado de ánimo", detalle.get("indice_estado_animo"))

            st.subheader("Diagnóstico general IA")
            st.write(detalle.get("diagnostico_general_ia") or "No disponible")
            st.subheader("Recomendación para el estudiante")
            st.write(detalle.get("recomendacion_estudiante_ia") or "No disponible")
            st.subheader("Recomendación para tutoría")
            st.write(detalle.get("recomendacion_tutoria_ia") or "No disponible")
            if detalle.get("alerta_emocional") == 1:
                st.error("Alerta emocional detectada. Se recomienda seguimiento por tutoría o área de apoyo correspondiente.")

elif menu == "Cursos":
    st.header("Registro de cursos")
    estudiante_id, _ = seleccionar_estudiante()
    if estudiante_id is not None:
        with st.form("form_curso"):
            nombre_curso = st.text_input("Nombre del curso")
            docente = st.text_input("Docente")
            c1, c2 = st.columns(2)
            with c1:
                creditos = st.number_input("Créditos", min_value=1, max_value=8, value=3)
            with c2:
                dificultad = st.slider("Dificultad", 1, 5, 3)
            estado = st.selectbox("Estado", ["En curso", "Aprobado", "Desaprobado", "Retirado"])
            if st.form_submit_button("Registrar curso"):
                if not nombre_curso.strip():
                    st.error("Debes ingresar el nombre del curso.")
                elif existe_curso(estudiante_id, nombre_curso):
                    st.warning("Este curso ya está registrado para el estudiante.")
                else:
                    registrar_curso(estudiante_id, nombre_curso.strip(), docente.strip(), int(creditos), int(dificultad), estado)
                    st.success("Curso registrado correctamente.")
                    st.rerun()

        cursos = listar_cursos_por_estudiante(estudiante_id)
        df_or_info(cursos, ["ID", "Curso", "Docente", "Créditos", "Dificultad", "Estado"], "Este estudiante aún no tiene cursos registrados.")

        if cursos:
            with st.expander("Editar curso"):
                opciones = {f"{c[1]} | Docente: {c[2]} | Estado: {c[5]}": c for c in cursos}
                texto = st.selectbox("Curso a editar", list(opciones.keys()))
                curso = opciones[texto]
                with st.form("form_editar_curso"):
                    nuevo_nombre = st.text_input("Nombre del curso", value=curso[1] or "")
                    nuevo_docente = st.text_input("Docente", value=curso[2] or "")
                    cc1, cc2 = st.columns(2)
                    with cc1:
                        nuevos_creditos = st.number_input("Créditos", min_value=1, max_value=8, value=int(curso[3] or 3), key="edit_creditos")
                    with cc2:
                        nueva_dificultad = st.slider("Dificultad", 1, 5, int(curso[4] or 3), key="edit_dificultad")
                    estados = ["En curso", "Aprobado", "Desaprobado", "Retirado"]
                    idx_estado = estados.index(curso[5]) if curso[5] in estados else 0
                    nuevo_estado = st.selectbox("Estado", estados, index=idx_estado)
                    if st.form_submit_button("Guardar cambios del curso"):
                        if not nuevo_nombre.strip():
                            st.error("El nombre del curso no puede estar vacío.")
                        else:
                            actualizar_curso(curso[0], nuevo_nombre.strip(), nuevo_docente.strip(), int(nuevos_creditos), int(nueva_dificultad), nuevo_estado)
                            st.success("Curso actualizado correctamente.")
                            st.rerun()

            with st.expander("Eliminar curso"):
                opciones = {f"{c[1]} | Docente: {c[2]} | Estado: {c[5]}": c[0] for c in cursos}
                texto = st.selectbox("Curso a eliminar", list(opciones.keys()))
                confirmar = st.checkbox("Confirmo que deseo eliminar este curso y sus tareas asociadas")
                if st.button("Eliminar curso"):
                    if confirmar:
                        eliminar_curso(opciones[texto])
                        st.success("Curso eliminado correctamente.")
                        st.rerun()
                    else:
                        st.error("Debes confirmar antes de eliminar.")

elif menu == "Tareas":
    st.header("Registro y seguimiento de tareas")
    estudiante_id, _ = seleccionar_estudiante()
    if estudiante_id is not None:
        cursos = listar_cursos_por_estudiante(estudiante_id)
        if not cursos:
            st.warning("Primero debes registrar cursos para este estudiante.")
        else:
            opciones_cursos = {f"{c[1]} | Dificultad: {c[4]}": {"id": c[0], "dificultad": c[4]} for c in cursos}
            with st.form("form_tarea"):
                curso_texto = st.selectbox("Curso", list(opciones_cursos.keys()))
                titulo = st.text_input("Título de la tarea")
                descripcion = st.text_area("Descripción")
                fecha_entrega = st.date_input("Fecha de entrega")
                if st.form_submit_button("Registrar tarea"):
                    curso_id = opciones_cursos[curso_texto]["id"]
                    dificultad = opciones_cursos[curso_texto]["dificultad"]
                    if not titulo.strip():
                        st.error("Debes ingresar el título de la tarea.")
                    elif existe_tarea(estudiante_id, curso_id, titulo):
                        st.warning("Esta tarea ya está registrada para este curso.")
                    else:
                        registrar_tarea(estudiante_id, curso_id, titulo.strip(), descripcion.strip(), fecha_entrega.strftime("%Y-%m-%d"), dificultad)
                        st.success("Tarea registrada correctamente.")
                        st.rerun()

        tareas = listar_tareas_por_estudiante(estudiante_id)
        df_or_info(tareas, ["ID", "Tarea", "Curso", "Fecha entrega", "Prioridad", "Estado"], "Este estudiante aún no tiene tareas registradas.")

        if tareas:
            with st.expander("Editar tarea"):
                opciones_editar = {f"{t[1]} | {t[2]} | Fecha: {t[3]} | Estado: {t[5]}": t[0] for t in tareas}
                texto_tarea = st.selectbox("Tarea a editar", list(opciones_editar.keys()), key="select_editar_tarea")
                tarea_id = opciones_editar[texto_tarea]
                tarea = obtener_tarea_por_id(tarea_id)

                if tarea is None:
                    st.error("No se encontró la tarea seleccionada.")
                elif not cursos:
                    st.warning("Primero debes registrar cursos para editar la tarea.")
                else:
                    curso_actual_id = tarea[2]
                    opciones_cursos_editar = {f"{c[1]} | Dificultad: {c[4]}": {"id": c[0], "dificultad": c[4]} for c in cursos}
                    lista_cursos = list(opciones_cursos_editar.keys())
                    indice_curso = 0
                    for idx, nombre_opcion in enumerate(lista_cursos):
                        if opciones_cursos_editar[nombre_opcion]["id"] == curso_actual_id:
                            indice_curso = idx
                            break

                    estados_tarea = ["Pendiente", "En proceso", "Completada"]
                    estado_actual = tarea[7] if tarea[7] in estados_tarea else "Pendiente"
                    indice_estado = estados_tarea.index(estado_actual)

                    with st.form("form_editar_tarea"):
                        curso_edit_texto = st.selectbox("Curso", lista_cursos, index=indice_curso, key="edit_tarea_curso")
                        nuevo_titulo = st.text_input("Título", value=tarea[3] or "")
                        nueva_descripcion = st.text_area("Descripción", value=tarea[4] or "")
                        nueva_fecha = st.date_input("Fecha de entrega", value=tarea[5], key="edit_tarea_fecha")
                        nuevo_estado = st.selectbox("Estado", estados_tarea, index=indice_estado, key="edit_tarea_estado")
                        if st.form_submit_button("Guardar cambios de la tarea"):
                            if not nuevo_titulo.strip():
                                st.error("El título de la tarea no puede estar vacío.")
                            else:
                                curso_data = opciones_cursos_editar[curso_edit_texto]
                                actualizar_tarea(
                                    tarea_id,
                                    curso_data["id"],
                                    nuevo_titulo.strip(),
                                    nueva_descripcion.strip(),
                                    nueva_fecha.strftime("%Y-%m-%d"),
                                    nuevo_estado,
                                    int(curso_data["dificultad"] or 3),
                                )
                                st.success("Tarea actualizada correctamente.")
                                st.rerun()

            with st.expander("Actualizar estado de tarea"):
                opciones = {f"{t[1]} | {t[2]} | Estado actual: {t[5]}": t[0] for t in tareas}
                texto = st.selectbox("Tarea", list(opciones.keys()))
                nuevo_estado = st.selectbox("Nuevo estado", ["Pendiente", "En proceso", "Completada"])
                if st.button("Actualizar estado"):
                    actualizar_estado_tarea(opciones[texto], nuevo_estado)
                    st.success("Estado actualizado correctamente.")
                    st.rerun()

            with st.expander("Eliminar tarea"):
                opciones = {f"{t[1]} | {t[2]} | Fecha: {t[3]} | Estado: {t[5]}": t[0] for t in tareas}
                texto = st.selectbox("Tarea a eliminar", list(opciones.keys()))
                confirmar = st.checkbox("Confirmo que deseo eliminar esta tarea")
                if st.button("Eliminar tarea"):
                    if confirmar:
                        eliminar_tarea(opciones[texto])
                        st.success("Tarea eliminada correctamente.")
                        st.rerun()
                    else:
                        st.error("Debes confirmar antes de eliminar.")

elif menu == "Dashboard estudiante":
    st.header("Dashboard del estudiante")
    estudiante_id, _ = seleccionar_estudiante()
    if estudiante_id is not None:
        diagnostico = obtener_ultimo_diagnostico(estudiante_id)
        detalle = obtener_ultimo_diagnostico_detallado(estudiante_id)
        resumen = obtener_resumen_tareas(estudiante_id)
        cursos_dificultad = obtener_cursos_mayor_dificultad(estudiante_id)

        if diagnostico is None:
            st.warning("Este estudiante aún no tiene diagnóstico registrado.")
        else:
            horas, promedio, _, estres, motivacion, procrastinacion, puntaje, riesgo, fecha = diagnostico
            riesgo = nivel_por_puntaje(puntaje)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Horas estudio/día", horas)
            c2.metric("Promedio ponderado", promedio)
            c3.metric("Puntaje riesgo IA", f"{puntaje}/100")
            c4.metric("Nivel riesgo IA", riesgo)

            c5, c6, c7, c8 = st.columns(4)
            c5.metric("Total tareas", resumen["total"])
            c6.metric("Completadas", resumen["completadas"])
            c7.metric("Pendientes", resumen["pendientes"])
            c8.metric("Alta prioridad", resumen["alta_prioridad"])
            st.progress(resumen["porcentaje_cumplimiento"] / 100)
            st.caption(f"Cumplimiento de tareas: {resumen['porcentaje_cumplimiento']}%")

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Indicadores IA")
                if detalle:
                    df = pd.DataFrame(
                        {
                            "Indicador": ["Estrés", "Procrastinación", "Motivación", "Estado de ánimo"],
                            "Nivel": [detalle["indice_estres"], detalle["indice_procrastinacion"], detalle["indice_motivacion"], detalle["indice_estado_animo"]],
                        }
                    )
                else:
                    df = pd.DataFrame({"Indicador": ["Estrés", "Motivación", "Procrastinación"], "Nivel": [estres, motivacion, procrastinacion]})
                st.plotly_chart(px.bar(df, x="Indicador", y="Nivel", range_y=[0, 5], text="Nivel"), use_container_width=True)
            with col2:
                st.subheader("Cursos con mayor dificultad")
                if cursos_dificultad:
                    dfc = pd.DataFrame(cursos_dificultad, columns=["Curso", "Dificultad"])
                    st.plotly_chart(px.bar(dfc, x="Curso", y="Dificultad", range_y=[0, 5], text="Dificultad"), use_container_width=True)
                else:
                    st.info("Aún no hay cursos registrados.")

            st.subheader("Diagnóstico general IA")
            st.write(detalle.get("diagnostico_general_ia") if detalle else "No disponible")
            st.subheader("Recomendación para el estudiante")
            st.write(detalle.get("recomendacion_estudiante_ia") if detalle else "No disponible")
            st.subheader("Recomendación para tutoría")
            st.write(detalle.get("recomendacion_tutoria_ia") if detalle else "No disponible")
            if detalle and detalle["alerta_emocional"] == 1:
                st.error("Alerta emocional detectada. Se recomienda seguimiento por tutoría o área de apoyo correspondiente.")
            st.info(f"Último diagnóstico: {fecha}")

elif menu == "Planificador semanal":
    st.header("Planificador semanal con IA")
    estudiante_id, estudiante_texto = seleccionar_estudiante()
    if estudiante_id is not None:
        diagnostico = obtener_ultimo_diagnostico(estudiante_id)
        detalle = obtener_ultimo_diagnostico_detallado(estudiante_id)
        tareas = listar_tareas_para_planificador(estudiante_id)
        ultimo_plan = obtener_ultimo_plan_semanal(estudiante_id)

        if ultimo_plan:
            with st.expander("Ver último plan semanal guardado", expanded=True):
                st.caption(f"Generado: {ultimo_plan.get('fecha')} | Horas usadas: {ultimo_plan.get('horas_disponibles')} h/semana")
                mostrar_plan_guardado(ultimo_plan.get("plan", []))

        if diagnostico is None:
            st.warning("Este estudiante aún no tiene diagnóstico registrado.")
        elif not tareas:
            st.warning("Este estudiante aún no tiene tareas registradas.")
        else:
            nombre = obtener_nombre_desde_texto(estudiante_texto)
            horas, promedio, _, estres, motivacion, procrast, puntaje, riesgo, _ = diagnostico
            riesgo = nivel_por_puntaje(puntaje)
            c1, c2, c3 = st.columns(3)
            horas_disponibles = c1.number_input("Horas disponibles esta semana", min_value=1.0, max_value=80.0, value=float(horas * 7), step=1.0)
            c2.metric("Nivel de riesgo", riesgo)
            c3.metric("Tareas activas", len([t for t in tareas if t["estado"] != "Completada"]))

            diag_plan = {
                "promedio_ponderado": promedio,
                "nivel_riesgo": riesgo,
                "puntaje_riesgo": puntaje,
                "indice_estres": detalle.get("indice_estres") if detalle else estres,
                "indice_procrastinacion": detalle.get("indice_procrastinacion") if detalle else procrast,
                "indice_motivacion": detalle.get("indice_motivacion") if detalle else motivacion,
                "indice_estado_animo": detalle.get("indice_estado_animo") if detalle else 3,
            }

            if st.button("Generar nuevo plan semanal con IA"):
                with st.spinner("AURA está generando un plan semanal realista con IA..."):
                    resultado_plan = generar_plan_semanal_ia(nombre, diag_plan, tareas, horas_disponibles)
                if not resultado_plan.get("exito"):
                    st.error("No se pudo generar el plan con IA. Se muestra un plan de respaldo y también se guardará.")
                    st.code(resultado_plan.get("error", "Error desconocido"))
                    plan = generar_plan_semanal(tareas, horas_disponibles, riesgo)
                else:
                    plan = resultado_plan.get("plan", [])
                    st.success("Plan semanal generado con IA.")

                guardar_plan_semanal(estudiante_id, plan, horas_disponibles)
                st.success("Plan semanal guardado correctamente.")
                st.subheader("Plan generado")
                mostrar_plan_guardado(plan)

elif menu == "Coach IA":
    st.header("Coach académico con IA")
    estudiante_id, estudiante_texto = seleccionar_estudiante()
    if estudiante_id is not None:
        diagnostico = obtener_ultimo_diagnostico(estudiante_id)
        resumen = obtener_resumen_tareas(estudiante_id)
        cursos_dificultad = obtener_cursos_mayor_dificultad(estudiante_id)
        ultima_rec = obtener_ultima_recomendacion_coach(estudiante_id)

        if ultima_rec:
            with st.expander("Ver última recomendación guardada", expanded=True):
                st.caption(f"Generada: {ultima_rec.get('fecha')}")
                st.markdown(ultima_rec.get("recomendacion") or "")

        if diagnostico is None:
            st.warning("Este estudiante aún no tiene diagnóstico registrado.")
        else:
            nombre = obtener_nombre_desde_texto(estudiante_texto)
            horas, promedio, tareas_pend, estres, motivacion, procrast, puntaje, riesgo, _ = diagnostico
            riesgo = nivel_por_puntaje(puntaje)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Riesgo académico", riesgo)
            c2.metric("Puntaje riesgo", f"{puntaje}/100")
            c3.metric("Tareas pendientes", resumen["pendientes"])
            c4.metric("Alta prioridad", resumen["alta_prioridad"])
            if st.button("Generar nueva recomendación con IA"):
                with st.spinner("AURA está generando una recomendación con Gemini..."):
                    rec = generar_recomendacion_ia(nombre, horas, promedio, tareas_pend, estres, motivacion, procrast, puntaje, riesgo, resumen, cursos_dificultad)
                guardar_recomendacion_coach(estudiante_id, rec)
                st.success("Recomendación generada y guardada por AURA:")
                st.markdown(rec)

elif menu == "Panel de Tutoría":
    st.header("Panel de Tutoría")
    datos = obtener_panel_tutoria()
    if not datos:
        st.info("Aún no hay estudiantes registrados.")
    else:
        df = pd.DataFrame(
            datos,
            columns=[
                "ID",
                "Nombre",
                "Código",
                "Carrera",
                "Ciclo",
                "Promedio ponderado",
                "Estrés",
                "Motivación",
                "Procrastinación",
                "Estado de ánimo",
                "Alerta emocional",
                "Puntaje riesgo",
                "Nivel riesgo",
                "Fecha diagnóstico",
                "Total tareas",
                "Tareas pendientes",
                "Alta prioridad",
            ],
        )
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total", len(df))
        c2.metric("Riesgo alto", len(df[df["Nivel riesgo"] == "Alto"]))
        c3.metric("Riesgo medio", len(df[df["Nivel riesgo"] == "Medio"]))
        c4.metric("Riesgo bajo", len(df[df["Nivel riesgo"] == "Bajo"]))
        c5.metric("Alertas emocionales", len(df[df["Alerta emocional"] == 1]))

        filtro = st.selectbox("Filtrar por nivel de riesgo", ["Todos", "Alto", "Medio", "Bajo", "Sin diagnóstico"])
        filtrado = df.copy()
        if filtro != "Todos":
            filtrado = filtrado[filtrado["Nivel riesgo"].isna()] if filtro == "Sin diagnóstico" else filtrado[filtrado["Nivel riesgo"] == filtro]
        st.dataframe(filtrado, use_container_width=True)

        alertas = []
        for _, fila in df.iterrows():
            if pd.isna(fila["Nivel riesgo"]):
                alertas.append({"Estudiante": fila["Nombre"], "Alerta": "Sin diagnóstico registrado", "Prioridad": "Media"})
                continue
            if fila["Nivel riesgo"] == "Alto":
                alertas.append({"Estudiante": fila["Nombre"], "Alerta": "Riesgo académico alto", "Prioridad": "Alta"})
            if pd.notna(fila["Promedio ponderado"]) and fila["Promedio ponderado"] < 11:
                alertas.append({"Estudiante": fila["Nombre"], "Alerta": "Promedio menor a 11", "Prioridad": "Alta"})
            if pd.notna(fila["Estrés"]) and fila["Estrés"] >= 4:
                alertas.append({"Estudiante": fila["Nombre"], "Alerta": "Estrés alto", "Prioridad": "Media"})
            if pd.notna(fila["Estado de ánimo"]) and fila["Estado de ánimo"] >= 4:
                alertas.append({"Estudiante": fila["Nombre"], "Alerta": "Estado de ánimo con señal de riesgo", "Prioridad": "Alta"})
            if fila["Alerta emocional"] == 1:
                alertas.append({"Estudiante": fila["Nombre"], "Alerta": "Alerta emocional por pregunta 20", "Prioridad": "Alta"})
            if pd.notna(fila["Tareas pendientes"]) and fila["Tareas pendientes"] >= 5:
                alertas.append({"Estudiante": fila["Nombre"], "Alerta": "Muchas tareas pendientes", "Prioridad": "Media"})

        st.subheader("Alertas de tutoría")
        if alertas:
            st.dataframe(pd.DataFrame(alertas), use_container_width=True)
        else:
            st.success("No se detectaron alertas relevantes.")

        conteo = df["Nivel riesgo"].fillna("Sin diagnóstico").value_counts().reset_index()
        conteo.columns = ["Nivel de riesgo", "Cantidad"]
        st.plotly_chart(px.bar(conteo, x="Nivel de riesgo", y="Cantidad", text="Cantidad", title="Distribución de riesgo académico"), use_container_width=True)

elif menu == "Reportes":
    st.header("Generación de reportes")
    estudiante_id, _ = seleccionar_estudiante()
    if estudiante_id is not None:
        estudiante = obtener_estudiante_por_id(estudiante_id)
        if estudiante is None:
            st.error("No se encontró información del estudiante.")
        else:
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

            col_excel, col_pdf = st.columns(2)
            col_excel.download_button("Descargar Excel", excel, file_name=f"reporte_aura_{nombre_limpio}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            col_pdf.download_button("Descargar PDF", pdf, file_name=f"reporte_aura_{nombre_limpio}.pdf", mime="application/pdf")

elif menu == "Exportar datos":
    st.header("Exportar datos")
    st.write("Exporta tablas completas desde Neon en CSV para respaldo o análisis.")
    tabla = st.selectbox("Tabla", ["estudiantes", "usuarios", "diagnosticos", "cursos", "tareas"])
    columnas, filas = obtener_tabla_completa(tabla)
    df = pd.DataFrame(filas, columns=columnas)
    st.dataframe(df, use_container_width=True)
    st.download_button("Descargar CSV", df.to_csv(index=False).encode("utf-8"), file_name=f"aura_{tabla}.csv", mime="text/csv")
