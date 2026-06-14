import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

from database import (
    crear_tablas,
    registrar_estudiante,
    listar_estudiantes,
    guardar_diagnostico_ia,
    obtener_ultimo_diagnostico,
    obtener_ultimo_diagnostico_detallado,
    registrar_curso,
    listar_cursos_por_estudiante,
    registrar_tarea,
    listar_tareas_por_estudiante,
    actualizar_estado_tarea,
    obtener_resumen_tareas,
    obtener_cursos_mayor_dificultad,
    obtener_estudiante_por_id,
    listar_tareas_para_planificador,
    autenticar_usuario,
    registrar_usuario,
    listar_usuarios,
    existe_curso,
    existe_tarea,
    eliminar_tarea,
    eliminar_curso,
    crear_backup_base_datos,
    obtener_panel_tutoria,
    eliminar_usuario,
    eliminar_estudiante
)

from ai_engine import generar_recomendacion_ia, generar_diagnostico_ia
from report_generator import crear_excel_reporte, crear_pdf_reporte
from planner import generar_plan_semanal


LOGO_PATH = Path(__file__).parent / "assets" / "logo_aura.png"


st.set_page_config(
    page_title="AURA - Coach Académico Inteligente",
    page_icon="🎓",
    layout="wide"
)


crear_tablas()


if "usuario_logueado" not in st.session_state:
    st.session_state.usuario_logueado = None


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
    ("¿Has sentido que tus problemas académicos o personales son demasiado difíciles de manejar?", "Estado de ánimo / alerta emocional")
]


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
            usuario = autenticar_usuario(username, password)

            if usuario is None:
                st.error("Usuario o contraseña incorrectos.")
            else:
                st.session_state.usuario_logueado = usuario
                st.success("Inicio de sesión correcto.")
                st.rerun()


def cerrar_sesion():
    st.session_state.usuario_logueado = None
    st.rerun()


if st.session_state.usuario_logueado is None:
    mostrar_login()
    st.stop()


mostrar_logo(180)

st.title("AURA")
st.subheader("Academic University Recommendation Assistant")
st.write("Tu coach académico inteligente para mejorar rendimiento, organización y bienestar estudiantil.")


usuario_actual = st.session_state.usuario_logueado
rol_actual = usuario_actual["rol"]


if LOGO_PATH.exists():
    st.sidebar.image(str(LOGO_PATH), use_container_width=True)


st.sidebar.success(f"Usuario: {usuario_actual['username']}")
st.sidebar.info(f"Rol: {rol_actual}")


if st.sidebar.button("Cerrar sesión"):
    cerrar_sesion()


if rol_actual == "Administrador":
    opciones_menu = [
        "Inicio",
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
        "Backup"
    ]

elif rol_actual == "Tutor":
    opciones_menu = [
        "Inicio",
        "Dashboard estudiante",
        "Planificador semanal",
        "Coach IA",
        "Panel de Tutoría",
        "Reportes"
    ]

else:
    opciones_menu = [
        "Inicio",
        "Diagnóstico académico",
        "Cursos",
        "Tareas",
        "Dashboard estudiante",
        "Planificador semanal",
        "Coach IA",
        "Reportes"
    ]


menu = st.sidebar.radio(
    "Menú principal",
    opciones_menu
)


def seleccionar_estudiante():
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

    opciones_estudiantes = {
        f"{estudiante[1]} | Código: {estudiante[2]} | Ciclo: {estudiante[4]}": estudiante[0]
        for estudiante in estudiantes
    }

    estudiante_texto = st.selectbox(
        "Selecciona un estudiante",
        list(opciones_estudiantes.keys())
    )

    estudiante_id = opciones_estudiantes[estudiante_texto]

    return estudiante_id, estudiante_texto


def obtener_nombre_desde_texto(estudiante_texto):
    if estudiante_texto is None:
        return "Estudiante"

    return estudiante_texto.split("|")[0].strip()


if menu == "Inicio":
    st.header("Bienvenido a AURA")

    st.write("""
    AURA es una herramienta web de apoyo académico para estudiantes universitarios.
    Permite registrar estudiantes, realizar diagnósticos con IA, gestionar cursos y tareas,
    generar planes semanales, descargar reportes y monitorear estudiantes desde tutoría.
    """)

    st.info("Flujo recomendado: estudiante → diagnóstico IA → cursos → tareas → dashboard → planificador → Coach IA → reportes.")


elif menu == "Registrar estudiante":
    st.header("Registro de estudiante")

    with st.form("form_registro_estudiante"):
        nombre = st.text_input("Nombre completo")
        codigo = st.text_input("Código universitario")
        carrera = st.text_input("Carrera", value="Ingeniería Industrial")
        ciclo = st.selectbox(
            "Ciclo académico",
            ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
        )

        boton_registrar = st.form_submit_button("Registrar estudiante")

        if boton_registrar:
            if nombre.strip() == "":
                st.error("Debes ingresar el nombre del estudiante.")
            else:
                registrar_estudiante(nombre, codigo, carrera, ciclo)
                st.success("Estudiante registrado correctamente.")

    st.subheader("Estudiantes registrados")

    estudiantes = listar_estudiantes()

    if len(estudiantes) == 0:
        st.info("Aún no hay estudiantes registrados.")
    else:
        df_estudiantes = pd.DataFrame(
            estudiantes,
            columns=["ID", "Nombre", "Código", "Carrera", "Ciclo"]
        )
        st.dataframe(df_estudiantes, use_container_width=True)

        st.divider()
        st.subheader("Eliminar estudiante")

        st.warning("""
        Al eliminar un estudiante, también se eliminarán sus diagnósticos,
        cursos, tareas y usuarios vinculados.
        """)

        opciones_eliminar_estudiante = {
            f"{estudiante[1]} | Código: {estudiante[2]} | Ciclo: {estudiante[4]}": estudiante[0]
            for estudiante in estudiantes
        }

        estudiante_eliminar_texto = st.selectbox(
            "Selecciona el estudiante a eliminar",
            list(opciones_eliminar_estudiante.keys()),
            key="select_eliminar_estudiante"
        )

        estudiante_id_eliminar = opciones_eliminar_estudiante[estudiante_eliminar_texto]

        confirmar_eliminar_estudiante = st.checkbox(
            "Confirmo que deseo eliminar este estudiante y todos sus datos asociados",
            key="check_eliminar_estudiante"
        )

        if st.button("Eliminar estudiante", key="btn_eliminar_estudiante"):
            if usuario_actual["estudiante_id"] == estudiante_id_eliminar:
                st.error("No puedes eliminar el estudiante vinculado a tu propio usuario mientras estás logueado.")
            elif confirmar_eliminar_estudiante:
                exito, mensaje = eliminar_estudiante(estudiante_id_eliminar)

                if exito:
                    st.success(mensaje)
                    st.rerun()
                else:
                    st.error(mensaje)
            else:
                st.error("Debes marcar la confirmación antes de eliminar.")


elif menu == "Gestión de usuarios":
    st.header("Gestión de usuarios")

    estudiantes = listar_estudiantes()
    opciones_estudiantes = {"Sin vincular": None}

    for estudiante in estudiantes:
        opciones_estudiantes[f"{estudiante[1]} | Código: {estudiante[2]}"] = estudiante[0]

    with st.form("form_crear_usuario"):
        username = st.text_input("Nombre de usuario")
        password = st.text_input("Contraseña", type="password")
        rol = st.selectbox("Rol", ["Estudiante", "Tutor", "Administrador"])

        estudiante_texto = st.selectbox(
            "Vincular con estudiante",
            list(opciones_estudiantes.keys())
        )

        estudiante_id = opciones_estudiantes[estudiante_texto]

        boton_crear = st.form_submit_button("Crear usuario")

        if boton_crear:
            if username.strip() == "":
                st.error("Debes ingresar un nombre de usuario.")
            elif password.strip() == "":
                st.error("Debes ingresar una contraseña.")
            elif rol == "Estudiante" and estudiante_id is None:
                st.error("Un usuario con rol Estudiante debe estar vinculado a un estudiante.")
            else:
                exito, mensaje = registrar_usuario(
                    username,
                    password,
                    rol,
                    estudiante_id
                )

                if exito:
                    st.success(mensaje)
                    st.rerun()
                else:
                    st.error(mensaje)

    st.subheader("Usuarios registrados")

    usuarios = listar_usuarios()

    if len(usuarios) == 0:
        st.info("No hay usuarios registrados.")
    else:
        df_usuarios = pd.DataFrame(
            usuarios,
            columns=["ID", "Usuario", "Rol", "Estudiante vinculado", "Fecha de registro"]
        )

        st.dataframe(df_usuarios, use_container_width=True)

        st.divider()
        st.subheader("Eliminar usuario")

        st.warning("""
        No se puede eliminar el usuario actualmente logueado.
        Tampoco se puede eliminar el último administrador del sistema.
        """)

        opciones_eliminar_usuario = {
            f"{usuario[1]} | Rol: {usuario[2]} | Estudiante: {usuario[3]}": usuario[0]
            for usuario in usuarios
        }

        usuario_eliminar_texto = st.selectbox(
            "Selecciona el usuario a eliminar",
            list(opciones_eliminar_usuario.keys()),
            key="select_eliminar_usuario"
        )

        usuario_id_eliminar = opciones_eliminar_usuario[usuario_eliminar_texto]

        confirmar_eliminar_usuario = st.checkbox(
            "Confirmo que deseo eliminar este usuario",
            key="check_eliminar_usuario"
        )

        if st.button("Eliminar usuario", key="btn_eliminar_usuario"):
            if usuario_id_eliminar == usuario_actual["id"]:
                st.error("No puedes eliminar el usuario con el que estás logueado actualmente.")
            elif confirmar_eliminar_usuario:
                exito, mensaje = eliminar_usuario(usuario_id_eliminar)

                if exito:
                    st.success(mensaje)
                    st.rerun()
                else:
                    st.error(mensaje)
            else:
                st.error("Debes marcar la confirmación antes de eliminar.")


elif menu == "Diagnóstico académico":
    st.header("Diagnóstico académico y de bienestar con IA")

    estudiante_id, estudiante_texto = seleccionar_estudiante()

    if estudiante_id is not None:
        nombre_estudiante = obtener_nombre_desde_texto(estudiante_texto)

        st.write("""
        Responde pensando en cómo te has sentido durante las últimas dos semanas.
        AURA enviará tus respuestas a la IA en la nube para generar un diagnóstico académico referencial.
        """)

        st.warning("""
        Este diagnóstico es una orientación académica y de bienestar, no un diagnóstico clínico.
        Si el estudiante presenta señales de alerta, se recomienda seguimiento por tutoría o área de apoyo correspondiente.
        """)

        st.info("""
        Escala de respuesta:
        1 = Nunca | 2 = Casi nunca | 3 = A veces | 4 = Casi siempre | 5 = Siempre
        """)

        with st.form("form_diagnostico"):
            horas_estudio_dia = st.number_input(
                "Horas de estudio por día",
                min_value=0.0,
                max_value=16.0,
                value=2.0,
                step=0.5
            )

            promedio_ponderado = st.number_input(
                "Promedio ponderado actual",
                min_value=0.0,
                max_value=20.0,
                value=13.0,
                step=0.1
            )

            st.divider()

            respuestas = {}
            dimensiones = [
                "Estrés",
                "Procrastinación",
                "Motivación",
                "Estado de ánimo",
                "Estado de ánimo / alerta emocional"
            ]

            for dimension in dimensiones:
                st.subheader(dimension)

                for indice, (pregunta, dim) in enumerate(PREGUNTAS_DIAGNOSTICO, start=1):
                    if dim == dimension:
                        respuestas[indice] = st.slider(
                            f"{indice}. {pregunta}",
                            min_value=1,
                            max_value=5,
                            value=3,
                            key=f"pregunta_{indice}"
                        )

            boton_guardar = st.form_submit_button("Generar diagnóstico con IA y guardar")

            if boton_guardar:
                with st.spinner("AURA está generando el diagnóstico con IA..."):
                    resultado_ia = generar_diagnostico_ia(
                        nombre_estudiante,
                        horas_estudio_dia,
                        promedio_ponderado,
                        respuestas
                    )

                if not resultado_ia["exito"]:
                    st.error("No se pudo generar el diagnóstico con IA.")
                    st.write("Detalle del error:")
                    st.code(resultado_ia["error"])

                    if resultado_ia.get("respuesta_original"):
                        st.write("Respuesta original de la IA:")
                        st.code(resultado_ia["respuesta_original"])

                else:
                    guardar_diagnostico_ia(
                        estudiante_id,
                        horas_estudio_dia,
                        promedio_ponderado,
                        respuestas,
                        resultado_ia
                    )

                    nivel_riesgo = resultado_ia["nivel_riesgo"]
                    puntaje_riesgo = resultado_ia["puntaje_riesgo"]

                    if nivel_riesgo == "Alto":
                        st.error(f"Diagnóstico IA guardado. Riesgo académico: {nivel_riesgo} | Puntaje: {puntaje_riesgo}/100")
                    elif nivel_riesgo == "Medio":
                        st.warning(f"Diagnóstico IA guardado. Riesgo académico: {nivel_riesgo} | Puntaje: {puntaje_riesgo}/100")
                    else:
                        st.success(f"Diagnóstico IA guardado. Riesgo académico: {nivel_riesgo} | Puntaje: {puntaje_riesgo}/100")

                    col1, col2, col3, col4 = st.columns(4)

                    col1.metric("Estrés IA", resultado_ia["indice_estres"])
                    col2.metric("Procrastinación IA", resultado_ia["indice_procrastinacion"])
                    col3.metric("Motivación IA", resultado_ia["indice_motivacion"])
                    col4.metric("Estado de ánimo IA", resultado_ia["indice_estado_animo"])

                    st.subheader("Diagnóstico general generado por IA")
                    st.write(resultado_ia["diagnostico_general"])

                    st.subheader("Recomendación para el estudiante")
                    st.write(resultado_ia["recomendacion_estudiante"])

                    st.subheader("Recomendación para tutoría")
                    st.write(resultado_ia["recomendacion_tutoria"])

                    if resultado_ia["alerta_emocional"] == 1:
                        st.error("""
                        Alerta emocional detectada.
                        Esta alerta no representa un diagnóstico clínico, pero sí recomienda seguimiento por tutoría o área de apoyo correspondiente.
                        """)


elif menu == "Cursos":
    st.header("Registro de cursos")

    estudiante_id, estudiante_texto = seleccionar_estudiante()

    if estudiante_id is not None:
        with st.form("form_registro_curso"):
            nombre_curso = st.text_input("Nombre del curso")
            docente = st.text_input("Docente")
            creditos = st.number_input("Créditos", min_value=1, max_value=8, value=3)
            dificultad = st.slider("Dificultad del curso", 1, 5, 3)
            estado = st.selectbox("Estado", ["En curso", "Aprobado", "Desaprobado", "Retirado"])

            boton_curso = st.form_submit_button("Registrar curso")

            if boton_curso:
                if nombre_curso.strip() == "":
                    st.error("Debes ingresar el nombre del curso.")
                elif existe_curso(estudiante_id, nombre_curso):
                    st.warning("Este curso ya está registrado para el estudiante.")
                else:
                    registrar_curso(
                        estudiante_id,
                        nombre_curso,
                        docente,
                        creditos,
                        dificultad,
                        estado
                    )
                    st.success("Curso registrado correctamente.")

        st.subheader("Cursos registrados")

        cursos = listar_cursos_por_estudiante(estudiante_id)

        if len(cursos) == 0:
            st.info("Este estudiante aún no tiene cursos registrados.")
        else:
            df_cursos = pd.DataFrame(
                cursos,
                columns=["ID", "Curso", "Docente", "Créditos", "Dificultad", "Estado"]
            )

            st.dataframe(df_cursos, use_container_width=True)

            st.subheader("Eliminar curso")

            st.warning("Si eliminas un curso, también se eliminarán sus tareas asociadas.")

            opciones_eliminar_curso = {
                f"{curso[1]} | Docente: {curso[2]} | Estado: {curso[5]}": curso[0]
                for curso in cursos
            }

            curso_eliminar_texto = st.selectbox(
                "Selecciona el curso a eliminar",
                list(opciones_eliminar_curso.keys())
            )

            curso_id_eliminar = opciones_eliminar_curso[curso_eliminar_texto]

            confirmar_eliminar_curso = st.checkbox("Confirmo que deseo eliminar este curso y sus tareas asociadas")

            if st.button("Eliminar curso"):
                if confirmar_eliminar_curso:
                    eliminar_curso(curso_id_eliminar)
                    st.success("Curso eliminado correctamente.")
                    st.rerun()
                else:
                    st.error("Debes marcar la confirmación antes de eliminar.")


elif menu == "Tareas":
    st.header("Registro y seguimiento de tareas")

    estudiante_id, estudiante_texto = seleccionar_estudiante()

    if estudiante_id is not None:
        cursos = listar_cursos_por_estudiante(estudiante_id)

        if len(cursos) == 0:
            st.warning("Primero debes registrar cursos para este estudiante.")
        else:
            opciones_cursos = {
                f"{curso[1]} | Dificultad: {curso[4]}": {
                    "id": curso[0],
                    "dificultad": curso[4]
                }
                for curso in cursos
            }

            with st.form("form_registro_tarea"):
                curso_texto = st.selectbox("Selecciona el curso", list(opciones_cursos.keys()))
                titulo = st.text_input("Título de la tarea")
                descripcion = st.text_area("Descripción")
                fecha_entrega = st.date_input("Fecha de entrega")

                boton_tarea = st.form_submit_button("Registrar tarea")

                if boton_tarea:
                    if titulo.strip() == "":
                        st.error("Debes ingresar el título de la tarea.")
                    else:
                        curso_id = opciones_cursos[curso_texto]["id"]
                        dificultad = opciones_cursos[curso_texto]["dificultad"]

                        if existe_tarea(estudiante_id, curso_id, titulo):
                            st.warning("Esta tarea ya está registrada para este curso.")
                        else:
                            registrar_tarea(
                                estudiante_id,
                                curso_id,
                                titulo,
                                descripcion,
                                fecha_entrega.strftime("%Y-%m-%d"),
                                dificultad
                            )

                            st.success("Tarea registrada correctamente.")

        st.subheader("Tareas registradas")

        tareas = listar_tareas_por_estudiante(estudiante_id)

        if len(tareas) == 0:
            st.info("Este estudiante aún no tiene tareas registradas.")
        else:
            df_tareas = pd.DataFrame(
                tareas,
                columns=["ID", "Tarea", "Curso", "Fecha de entrega", "Prioridad", "Estado"]
            )

            st.dataframe(df_tareas, use_container_width=True)

            st.subheader("Actualizar estado de tarea")

            opciones_tareas = {
                f"{tarea[1]} | {tarea[2]} | Estado actual: {tarea[5]}": tarea[0]
                for tarea in tareas
            }

            tarea_texto = st.selectbox("Selecciona una tarea", list(opciones_tareas.keys()))
            tarea_id = opciones_tareas[tarea_texto]

            nuevo_estado = st.selectbox(
                "Nuevo estado",
                ["Pendiente", "En proceso", "Completada"]
            )

            if st.button("Actualizar estado"):
                actualizar_estado_tarea(tarea_id, nuevo_estado)
                st.success("Estado actualizado correctamente.")
                st.rerun()

            st.subheader("Eliminar tarea")

            opciones_eliminar_tarea = {
                f"{tarea[1]} | {tarea[2]} | Fecha: {tarea[3]} | Estado: {tarea[5]}": tarea[0]
                for tarea in tareas
            }

            tarea_eliminar_texto = st.selectbox(
                "Selecciona la tarea a eliminar",
                list(opciones_eliminar_tarea.keys())
            )

            tarea_id_eliminar = opciones_eliminar_tarea[tarea_eliminar_texto]

            confirmar_eliminar_tarea = st.checkbox("Confirmo que deseo eliminar esta tarea")

            if st.button("Eliminar tarea"):
                if confirmar_eliminar_tarea:
                    eliminar_tarea(tarea_id_eliminar)
                    st.success("Tarea eliminada correctamente.")
                    st.rerun()
                else:
                    st.error("Debes marcar la confirmación antes de eliminar.")


elif menu == "Dashboard estudiante":
    st.header("Dashboard del estudiante")

    estudiante_id, estudiante_texto = seleccionar_estudiante()

    if estudiante_id is not None:
        diagnostico = obtener_ultimo_diagnostico(estudiante_id)
        diagnostico_detallado = obtener_ultimo_diagnostico_detallado(estudiante_id)
        resumen_tareas = obtener_resumen_tareas(estudiante_id)
        cursos_dificultad = obtener_cursos_mayor_dificultad(estudiante_id)

        if diagnostico is None:
            st.warning("Este estudiante aún no tiene diagnóstico registrado.")
        else:
            (
                horas_estudio,
                promedio_actual,
                tareas_pendientes,
                nivel_estres,
                nivel_motivacion,
                nivel_procrastinacion,
                puntaje_riesgo,
                nivel_riesgo,
                fecha
            ) = diagnostico

            st.subheader("Resumen académico")

            col1, col2, col3, col4 = st.columns(4)

            col1.metric("Horas de estudio", f"{horas_estudio} h/día")
            col2.metric("Promedio ponderado", promedio_actual)
            col3.metric("Puntaje de riesgo IA", f"{puntaje_riesgo}/100")
            col4.metric("Nivel de riesgo IA", nivel_riesgo)

            st.divider()

            st.subheader("Resumen de tareas")

            col5, col6, col7, col8 = st.columns(4)

            col5.metric("Total de tareas", resumen_tareas["total"])
            col6.metric("Completadas", resumen_tareas["completadas"])
            col7.metric("Pendientes", resumen_tareas["pendientes"])
            col8.metric("Alta prioridad", resumen_tareas["alta_prioridad"])

            st.progress(resumen_tareas["porcentaje_cumplimiento"] / 100)
            st.write(f"Cumplimiento de tareas: {resumen_tareas['porcentaje_cumplimiento']}%")

            st.divider()

            col9, col10 = st.columns(2)

            with col9:
                st.subheader("Indicadores generados por IA")

                if diagnostico_detallado is not None:
                    datos_indicadores = pd.DataFrame({
                        "Indicador": [
                            "Estrés",
                            "Procrastinación",
                            "Motivación",
                            "Estado de ánimo"
                        ],
                        "Nivel": [
                            diagnostico_detallado["indice_estres"],
                            diagnostico_detallado["indice_procrastinacion"],
                            diagnostico_detallado["indice_motivacion"],
                            diagnostico_detallado["indice_estado_animo"]
                        ]
                    })
                else:
                    datos_indicadores = pd.DataFrame({
                        "Indicador": [
                            "Estrés",
                            "Motivación",
                            "Procrastinación"
                        ],
                        "Nivel": [
                            nivel_estres,
                            nivel_motivacion,
                            nivel_procrastinacion
                        ]
                    })

                fig = px.bar(
                    datos_indicadores,
                    x="Indicador",
                    y="Nivel",
                    title="Estado actual del estudiante",
                    range_y=[0, 5],
                    text="Nivel"
                )

                st.plotly_chart(fig, use_container_width=True)

            with col10:
                st.subheader("Cursos con mayor dificultad")

                if len(cursos_dificultad) == 0:
                    st.info("Aún no hay cursos registrados.")
                else:
                    df_dificultad = pd.DataFrame(
                        cursos_dificultad,
                        columns=["Curso", "Dificultad"]
                    )

                    fig2 = px.bar(
                        df_dificultad,
                        x="Curso",
                        y="Dificultad",
                        title="Dificultad por curso",
                        range_y=[0, 5],
                        text="Dificultad"
                    )

                    st.plotly_chart(fig2, use_container_width=True)

            st.divider()

            st.subheader("Diagnóstico general IA")

            if diagnostico_detallado is not None and diagnostico_detallado.get("diagnostico_general_ia"):
                st.write(diagnostico_detallado["diagnostico_general_ia"])
            else:
                st.info("No hay texto de diagnóstico IA guardado para este registro.")

            st.subheader("Recomendación para el estudiante")

            if diagnostico_detallado is not None and diagnostico_detallado.get("recomendacion_estudiante_ia"):
                st.write(diagnostico_detallado["recomendacion_estudiante_ia"])
            else:
                st.info("No hay recomendación IA guardada para el estudiante.")

            st.subheader("Recomendación para tutoría")

            if diagnostico_detallado is not None and diagnostico_detallado.get("recomendacion_tutoria_ia"):
                st.write(diagnostico_detallado["recomendacion_tutoria_ia"])
            else:
                st.info("No hay recomendación IA guardada para tutoría.")

            if diagnostico_detallado is not None and diagnostico_detallado["alerta_emocional"] == 1:
                st.error("""
                Alerta emocional detectada.
                Esta alerta no representa un diagnóstico clínico, pero sí recomienda seguimiento por tutoría o área de apoyo correspondiente.
                """)

            st.info(f"Último diagnóstico registrado: {fecha}")


elif menu == "Planificador semanal":
    st.header("Planificador Semanal Inteligente")

    estudiante_id, estudiante_texto = seleccionar_estudiante()

    if estudiante_id is not None:
        diagnostico = obtener_ultimo_diagnostico(estudiante_id)
        tareas_planificador = listar_tareas_para_planificador(estudiante_id)

        if diagnostico is None:
            st.warning("Este estudiante aún no tiene diagnóstico registrado.")
        elif len(tareas_planificador) == 0:
            st.warning("Este estudiante aún no tiene tareas registradas.")
        else:
            (
                horas_estudio,
                promedio_actual,
                tareas_pendientes,
                nivel_estres,
                nivel_motivacion,
                nivel_procrastinacion,
                puntaje_riesgo,
                nivel_riesgo,
                fecha
            ) = diagnostico

            st.write("""
            AURA generará un plan semanal considerando tus tareas pendientes,
            fechas de entrega, prioridad, dificultad del curso y nivel de riesgo académico.
            """)

            col1, col2, col3 = st.columns(3)

            with col1:
                horas_disponibles = st.number_input(
                    "Horas disponibles esta semana",
                    min_value=1.0,
                    max_value=80.0,
                    value=float(horas_estudio * 7),
                    step=1.0
                )

            with col2:
                st.metric("Nivel de riesgo", nivel_riesgo)

            with col3:
                tareas_activas = [t for t in tareas_planificador if t["estado"] != "Completada"]
                st.metric("Tareas activas", len(tareas_activas))

            if st.button("Generar plan semanal"):
                plan = generar_plan_semanal(
                    tareas_planificador,
                    horas_disponibles,
                    nivel_riesgo
                )

                st.success("Plan semanal generado correctamente.")

                for dia in plan:
                    st.subheader(dia["dia"])
                    st.caption(f'Horas disponibles aproximadas: {dia["horas_disponibles"]} h')
                    st.info(dia["recomendacion"])

                    datos_dia = []

                    for tarea in dia["tareas"]:
                        datos_dia.append({
                            "Curso": tarea["curso"],
                            "Actividad": tarea["tarea"],
                            "Prioridad": tarea["prioridad"],
                            "Fecha de entrega": tarea["fecha_entrega"],
                            "Horas recomendadas": tarea["horas_recomendadas"]
                        })

                    df_dia = pd.DataFrame(datos_dia)
                    st.dataframe(df_dia, use_container_width=True)


elif menu == "Coach IA":
    st.header("Coach académico con IA")

    estudiante_id, estudiante_texto = seleccionar_estudiante()

    if estudiante_id is not None:
        diagnostico = obtener_ultimo_diagnostico(estudiante_id)
        resumen_tareas = obtener_resumen_tareas(estudiante_id)
        cursos_dificultad = obtener_cursos_mayor_dificultad(estudiante_id)

        if diagnostico is None:
            st.warning("Este estudiante aún no tiene diagnóstico registrado.")
        else:
            nombre_estudiante = obtener_nombre_desde_texto(estudiante_texto)

            (
                horas_estudio,
                promedio_actual,
                tareas_pendientes,
                nivel_estres,
                nivel_motivacion,
                nivel_procrastinacion,
                puntaje_riesgo,
                nivel_riesgo,
                fecha
            ) = diagnostico

            st.write("""
            AURA analizará tu diagnóstico, tareas y cursos registrados para generar
            una recomendación personalizada usando IA.
            """)

            col1, col2, col3 = st.columns(3)
            col1.metric("Riesgo académico", nivel_riesgo)
            col2.metric("Tareas pendientes", resumen_tareas["pendientes"])
            col3.metric("Alta prioridad", resumen_tareas["alta_prioridad"])

            if st.button("Generar recomendación con IA"):
                with st.spinner("AURA está generando una recomendación personalizada..."):
                    recomendacion = generar_recomendacion_ia(
                        nombre_estudiante,
                        horas_estudio,
                        promedio_actual,
                        tareas_pendientes,
                        nivel_estres,
                        nivel_motivacion,
                        nivel_procrastinacion,
                        puntaje_riesgo,
                        nivel_riesgo,
                        resumen_tareas,
                        cursos_dificultad
                    )

                st.success("Recomendación generada por AURA:")
                st.markdown(recomendacion)


elif menu == "Panel de Tutoría":
    st.header("Panel de Tutoría")

    st.write("""
    Este panel permite identificar estudiantes con posible riesgo académico
    y priorizar el seguimiento por parte de tutoría.
    """)

    datos_panel = obtener_panel_tutoria()

    if len(datos_panel) == 0:
        st.info("Aún no hay estudiantes registrados.")
    else:
        df_panel = pd.DataFrame(
            datos_panel,
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
                "Alta prioridad"
            ]
        )

        st.subheader("Resumen general")

        total_estudiantes = len(df_panel)
        riesgo_alto = len(df_panel[df_panel["Nivel riesgo"] == "Alto"])
        riesgo_medio = len(df_panel[df_panel["Nivel riesgo"] == "Medio"])
        riesgo_bajo = len(df_panel[df_panel["Nivel riesgo"] == "Bajo"])
        alertas_emocionales = len(df_panel[df_panel["Alerta emocional"] == 1])

        col1, col2, col3, col4, col5 = st.columns(5)

        col1.metric("Total estudiantes", total_estudiantes)
        col2.metric("Riesgo alto", riesgo_alto)
        col3.metric("Riesgo medio", riesgo_medio)
        col4.metric("Riesgo bajo", riesgo_bajo)
        col5.metric("Alertas emocionales", alertas_emocionales)

        st.divider()

        filtro_riesgo = st.selectbox(
            "Filtrar por nivel de riesgo",
            ["Todos", "Alto", "Medio", "Bajo", "Sin diagnóstico"]
        )

        df_filtrado = df_panel.copy()

        if filtro_riesgo != "Todos":
            if filtro_riesgo == "Sin diagnóstico":
                df_filtrado = df_filtrado[df_filtrado["Nivel riesgo"].isna()]
            else:
                df_filtrado = df_filtrado[df_filtrado["Nivel riesgo"] == filtro_riesgo]

        st.subheader("Estudiantes monitoreados")
        st.dataframe(df_filtrado, use_container_width=True)

        st.divider()

        st.subheader("Alertas de tutoría")

        alertas = []

        for _, fila in df_panel.iterrows():
            nombre = fila["Nombre"]
            riesgo = fila["Nivel riesgo"]
            promedio = fila["Promedio ponderado"]
            estres = fila["Estrés"]
            estado_animo = fila["Estado de ánimo"]
            alerta_emocional = fila["Alerta emocional"]
            pendientes = fila["Tareas pendientes"]
            alta = fila["Alta prioridad"]

            if pd.isna(riesgo):
                alertas.append({
                    "Estudiante": nombre,
                    "Alerta": "Sin diagnóstico registrado",
                    "Prioridad": "Media"
                })
            else:
                if riesgo == "Alto":
                    alertas.append({
                        "Estudiante": nombre,
                        "Alerta": "Riesgo académico alto",
                        "Prioridad": "Alta"
                    })

                if promedio is not None and not pd.isna(promedio) and promedio < 11:
                    alertas.append({
                        "Estudiante": nombre,
                        "Alerta": "Promedio ponderado menor a 11",
                        "Prioridad": "Alta"
                    })

                if estres is not None and not pd.isna(estres) and estres >= 4:
                    alertas.append({
                        "Estudiante": nombre,
                        "Alerta": "Nivel de estrés alto",
                        "Prioridad": "Media"
                    })

                if estado_animo is not None and not pd.isna(estado_animo) and estado_animo >= 4:
                    alertas.append({
                        "Estudiante": nombre,
                        "Alerta": "Estado de ánimo con señal de riesgo",
                        "Prioridad": "Alta"
                    })

                if alerta_emocional == 1:
                    alertas.append({
                        "Estudiante": nombre,
                        "Alerta": "Alerta emocional por pregunta 20",
                        "Prioridad": "Alta"
                    })

                if pendientes is not None and not pd.isna(pendientes) and pendientes >= 5:
                    alertas.append({
                        "Estudiante": nombre,
                        "Alerta": "Muchas tareas pendientes",
                        "Prioridad": "Media"
                    })

                if alta is not None and not pd.isna(alta) and alta >= 3:
                    alertas.append({
                        "Estudiante": nombre,
                        "Alerta": "Varias tareas de alta prioridad",
                        "Prioridad": "Media"
                    })

        if len(alertas) == 0:
            st.success("No se detectaron alertas relevantes.")
        else:
            df_alertas = pd.DataFrame(alertas)
            st.dataframe(df_alertas, use_container_width=True)

        st.divider()

        st.subheader("Gráfico de riesgo académico")

        conteo_riesgo = df_panel["Nivel riesgo"].fillna("Sin diagnóstico").value_counts().reset_index()
        conteo_riesgo.columns = ["Nivel de riesgo", "Cantidad"]

        fig_riesgo = px.bar(
            conteo_riesgo,
            x="Nivel de riesgo",
            y="Cantidad",
            title="Distribución de estudiantes por nivel de riesgo",
            text="Cantidad"
        )

        st.plotly_chart(fig_riesgo, use_container_width=True)


elif menu == "Reportes":
    st.header("Generación de reportes")

    estudiante_id, estudiante_texto = seleccionar_estudiante()

    if estudiante_id is not None:
        estudiante = obtener_estudiante_por_id(estudiante_id)

        if estudiante is None:
            st.error("No se encontró información del estudiante.")
        else:
            _, nombre, codigo, carrera, ciclo = estudiante

            diagnostico = obtener_ultimo_diagnostico(estudiante_id)
            resumen_tareas = obtener_resumen_tareas(estudiante_id)
            cursos = listar_cursos_por_estudiante(estudiante_id)
            tareas = listar_tareas_por_estudiante(estudiante_id)

            st.subheader("Vista previa del reporte")

            col1, col2, col3, col4 = st.columns(4)

            col1.metric("Estudiante", nombre)
            col2.metric("Cursos", len(cursos))
            col3.metric("Tareas", resumen_tareas["total"])

            if diagnostico:
                col4.metric("Riesgo", diagnostico[7])
            else:
                col4.metric("Riesgo", "Sin diagnóstico")

            st.write("El reporte incluirá diagnóstico, cursos, tareas y resumen de cumplimiento.")

            excel_file = crear_excel_reporte(
                nombre,
                codigo,
                carrera,
                ciclo,
                diagnostico,
                resumen_tareas,
                cursos,
                tareas
            )

            pdf_file = crear_pdf_reporte(
                nombre,
                codigo,
                carrera,
                ciclo,
                diagnostico,
                resumen_tareas,
                cursos,
                tareas
            )

            nombre_limpio = nombre.replace(" ", "_").lower()

            col_excel, col_pdf = st.columns(2)

            with col_excel:
                st.download_button(
                    label="Descargar reporte Excel",
                    data=excel_file,
                    file_name=f"reporte_aura_{nombre_limpio}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            with col_pdf:
                st.download_button(
                    label="Descargar reporte PDF",
                    data=pdf_file,
                    file_name=f"reporte_aura_{nombre_limpio}.pdf",
                    mime="application/pdf"
                )


elif menu == "Backup":
    st.header("Backup de base de datos")

    st.write("""
    Desde aquí puedes crear una copia de seguridad local del archivo aura.db.
    Esto es importante antes de hacer pruebas, mover el sistema o usarlo con varios usuarios.
    """)

    st.info("El backup se guardará en la carpeta 'backups' dentro del proyecto.")

    if st.button("Crear backup ahora"):
        exito, resultado = crear_backup_base_datos()

        if exito:
            st.success(f"Backup creado correctamente: {resultado}")
        else:
            st.error(resultado)
