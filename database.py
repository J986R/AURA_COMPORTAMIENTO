import hashlib
from datetime import datetime
from typing import Any

import psycopg
from psycopg.rows import tuple_row

from config import get_setting


def _database_url() -> str:
    url = get_setting("NEON_DATABASE_URL")
    if not url:
        raise RuntimeError(
            "Falta configurar NEON_DATABASE_URL. En Streamlit Cloud agrégalo en Secrets. "
            "En local puedes crear un archivo .env."
        )
    return url


def conectar():
    return psycopg.connect(_database_url(), row_factory=tuple_row)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def crear_tablas():
    with conectar() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS estudiantes (
                    id SERIAL PRIMARY KEY,
                    nombre TEXT NOT NULL,
                    codigo TEXT,
                    carrera TEXT,
                    ciclo TEXT,
                    fecha_registro TEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id SERIAL PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    rol TEXT NOT NULL,
                    estudiante_id INTEGER REFERENCES estudiantes(id) ON DELETE SET NULL,
                    fecha_registro TEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS diagnosticos (
                    id SERIAL PRIMARY KEY,
                    estudiante_id INTEGER NOT NULL REFERENCES estudiantes(id) ON DELETE CASCADE,
                    horas_estudio REAL NOT NULL,
                    promedio_actual REAL NOT NULL,
                    tareas_pendientes INTEGER NOT NULL,
                    nivel_estres INTEGER NOT NULL,
                    nivel_motivacion INTEGER NOT NULL,
                    nivel_procrastinacion INTEGER NOT NULL,
                    puntaje_riesgo INTEGER NOT NULL,
                    nivel_riesgo TEXT NOT NULL,
                    fecha TEXT NOT NULL,
                    horas_estudio_dia REAL,
                    promedio_ponderado REAL,
                    pregunta_1 INTEGER,
                    pregunta_2 INTEGER,
                    pregunta_3 INTEGER,
                    pregunta_4 INTEGER,
                    pregunta_5 INTEGER,
                    pregunta_6 INTEGER,
                    pregunta_7 INTEGER,
                    pregunta_8 INTEGER,
                    pregunta_9 INTEGER,
                    pregunta_10 INTEGER,
                    pregunta_11 INTEGER,
                    pregunta_12 INTEGER,
                    pregunta_13 INTEGER,
                    pregunta_14 INTEGER,
                    pregunta_15 INTEGER,
                    pregunta_16 INTEGER,
                    pregunta_17 INTEGER,
                    pregunta_18 INTEGER,
                    pregunta_19 INTEGER,
                    pregunta_20 INTEGER,
                    indice_estres REAL,
                    indice_procrastinacion REAL,
                    indice_motivacion REAL,
                    indice_estado_animo REAL,
                    alerta_emocional INTEGER,
                    diagnostico_general_ia TEXT,
                    recomendacion_estudiante_ia TEXT,
                    recomendacion_tutoria_ia TEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cursos (
                    id SERIAL PRIMARY KEY,
                    estudiante_id INTEGER NOT NULL REFERENCES estudiantes(id) ON DELETE CASCADE,
                    nombre_curso TEXT NOT NULL,
                    docente TEXT,
                    creditos INTEGER,
                    dificultad INTEGER,
                    estado TEXT,
                    fecha_registro TEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tareas (
                    id SERIAL PRIMARY KEY,
                    estudiante_id INTEGER NOT NULL REFERENCES estudiantes(id) ON DELETE CASCADE,
                    curso_id INTEGER NOT NULL REFERENCES cursos(id) ON DELETE CASCADE,
                    titulo TEXT NOT NULL,
                    descripcion TEXT,
                    fecha_entrega TEXT,
                    prioridad TEXT,
                    estado TEXT,
                    fecha_registro TEXT
                )
            """)

            migrar_tabla_diagnosticos(cursor)

    crear_admin_por_defecto()


def migrar_tabla_diagnosticos(cursor):
    columnas = {
        "horas_estudio_dia": "REAL",
        "promedio_ponderado": "REAL",
        **{f"pregunta_{i}": "INTEGER" for i in range(1, 21)},
        "indice_estres": "REAL",
        "indice_procrastinacion": "REAL",
        "indice_motivacion": "REAL",
        "indice_estado_animo": "REAL",
        "alerta_emocional": "INTEGER",
        "diagnostico_general_ia": "TEXT",
        "recomendacion_estudiante_ia": "TEXT",
        "recomendacion_tutoria_ia": "TEXT",
    }
    for nombre, tipo in columnas.items():
        cursor.execute(f"ALTER TABLE diagnosticos ADD COLUMN IF NOT EXISTS {nombre} {tipo}")


def crear_admin_por_defecto():
    with conectar() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT id FROM usuarios WHERE username = %s", ("admin",))
            existe = cursor.fetchone()
            if existe is None:
                fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("""
                    INSERT INTO usuarios (username, password_hash, rol, estudiante_id, fecha_registro)
                    VALUES (%s, %s, %s, %s, %s)
                """, ("admin", hash_password("aura123"), "Administrador", None, fecha))


def autenticar_usuario(username: str, password: str):
    with conectar() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute("""
                SELECT id, username, password_hash, rol, estudiante_id
                FROM usuarios
                WHERE username = %s
            """, (username,))
            usuario = cursor.fetchone()

    if usuario is None:
        return None

    id_usuario, username_db, password_hash_db, rol, estudiante_id = usuario
    if hash_password(password) == password_hash_db:
        return {
            "id": id_usuario,
            "username": username_db,
            "rol": rol,
            "estudiante_id": estudiante_id
        }
    return None


def registrar_usuario(username: str, password: str, rol: str, estudiante_id=None):
    try:
        with conectar() as conexion:
            with conexion.cursor() as cursor:
                fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("""
                    INSERT INTO usuarios (username, password_hash, rol, estudiante_id, fecha_registro)
                    VALUES (%s, %s, %s, %s, %s)
                """, (username, hash_password(password), rol, estudiante_id, fecha))
        return True, "Usuario creado correctamente."
    except psycopg.errors.UniqueViolation:
        return False, "El nombre de usuario ya existe."
    except Exception as error:
        return False, f"No se pudo crear el usuario: {error}"


def listar_usuarios():
    with conectar() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute("""
                SELECT u.id, u.username, u.rol, e.nombre, u.fecha_registro
                FROM usuarios u
                LEFT JOIN estudiantes e ON u.estudiante_id = e.id
                ORDER BY u.id DESC
            """)
            return cursor.fetchall()


def eliminar_usuario(usuario_id: int):
    with conectar() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT rol FROM usuarios WHERE id = %s", (usuario_id,))
            usuario = cursor.fetchone()
            if usuario is None:
                return False, "El usuario no existe."
            rol = usuario[0]
            if rol == "Administrador":
                cursor.execute("SELECT COUNT(*) FROM usuarios WHERE rol = 'Administrador'")
                total_admins = cursor.fetchone()[0]
                if total_admins <= 1:
                    return False, "No se puede eliminar el último usuario administrador."
            cursor.execute("DELETE FROM usuarios WHERE id = %s", (usuario_id,))
    return True, "Usuario eliminado correctamente."


def registrar_estudiante(nombre: str, codigo: str, carrera: str, ciclo: str):
    with conectar() as conexion:
        with conexion.cursor() as cursor:
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT INTO estudiantes (nombre, codigo, carrera, ciclo, fecha_registro)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (nombre, codigo, carrera, ciclo, fecha))
            return cursor.fetchone()[0]


def listar_estudiantes():
    with conectar() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute("""
                SELECT id, nombre, codigo, carrera, ciclo
                FROM estudiantes
                ORDER BY id DESC
            """)
            return cursor.fetchall()


def obtener_estudiante_por_id(estudiante_id: int):
    with conectar() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute("""
                SELECT id, nombre, codigo, carrera, ciclo
                FROM estudiantes
                WHERE id = %s
            """, (estudiante_id,))
            return cursor.fetchone()


def eliminar_estudiante(estudiante_id: int):
    with conectar() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT id FROM estudiantes WHERE id = %s", (estudiante_id,))
            if cursor.fetchone() is None:
                return False, "El estudiante no existe."
            cursor.execute("DELETE FROM estudiantes WHERE id = %s", (estudiante_id,))
    return True, "Estudiante eliminado correctamente junto con sus datos asociados."


def guardar_diagnostico_ia(estudiante_id: int, horas_estudio_dia: float, promedio_ponderado: float, respuestas: dict[int, int], resultado_ia: dict[str, Any]):
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    puntaje_riesgo = int(resultado_ia["puntaje_riesgo"])
    nivel_riesgo = resultado_ia["nivel_riesgo"]
    indice_estres = float(resultado_ia["indice_estres"])
    indice_procrastinacion = float(resultado_ia["indice_procrastinacion"])
    indice_motivacion = float(resultado_ia["indice_motivacion"])
    indice_estado_animo = float(resultado_ia["indice_estado_animo"])
    alerta_emocional = int(resultado_ia["alerta_emocional"])

    valores = [
        estudiante_id,
        horas_estudio_dia,
        promedio_ponderado,
        0,
        round(indice_estres),
        round(indice_motivacion),
        round(indice_procrastinacion),
        puntaje_riesgo,
        nivel_riesgo,
        fecha,
        horas_estudio_dia,
        promedio_ponderado,
    ]
    valores.extend([int(respuestas[i]) for i in range(1, 21)])
    valores.extend([
        indice_estres,
        indice_procrastinacion,
        indice_motivacion,
        indice_estado_animo,
        alerta_emocional,
        resultado_ia.get("diagnostico_general", ""),
        resultado_ia.get("recomendacion_estudiante", ""),
        resultado_ia.get("recomendacion_tutoria", ""),
    ])

    columnas = [
        "estudiante_id", "horas_estudio", "promedio_actual", "tareas_pendientes",
        "nivel_estres", "nivel_motivacion", "nivel_procrastinacion", "puntaje_riesgo",
        "nivel_riesgo", "fecha", "horas_estudio_dia", "promedio_ponderado",
        *[f"pregunta_{i}" for i in range(1, 21)],
        "indice_estres", "indice_procrastinacion", "indice_motivacion", "indice_estado_animo",
        "alerta_emocional", "diagnostico_general_ia", "recomendacion_estudiante_ia",
        "recomendacion_tutoria_ia"
    ]

    placeholders = ",".join(["%s"] * len(valores))
    with conectar() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(f"""
                INSERT INTO diagnosticos ({','.join(columnas)})
                VALUES ({placeholders})
            """, tuple(valores))
    return True


def obtener_ultimo_diagnostico(estudiante_id: int):
    with conectar() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute("""
                SELECT
                    COALESCE(horas_estudio_dia, horas_estudio),
                    COALESCE(promedio_ponderado, promedio_actual),
                    COALESCE(tareas_pendientes, 0),
                    COALESCE(indice_estres, nivel_estres),
                    COALESCE(indice_motivacion, nivel_motivacion),
                    COALESCE(indice_procrastinacion, nivel_procrastinacion),
                    puntaje_riesgo,
                    nivel_riesgo,
                    fecha
                FROM diagnosticos
                WHERE estudiante_id = %s
                ORDER BY id DESC
                LIMIT 1
            """, (estudiante_id,))
            return cursor.fetchone()


def obtener_ultimo_diagnostico_detallado(estudiante_id: int):
    with conectar() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute("""
                SELECT
                    horas_estudio_dia,
                    promedio_ponderado,
                    pregunta_1, pregunta_2, pregunta_3, pregunta_4, pregunta_5,
                    pregunta_6, pregunta_7, pregunta_8, pregunta_9, pregunta_10,
                    pregunta_11, pregunta_12, pregunta_13, pregunta_14, pregunta_15,
                    pregunta_16, pregunta_17, pregunta_18, pregunta_19, pregunta_20,
                    indice_estres,
                    indice_procrastinacion,
                    indice_motivacion,
                    indice_estado_animo,
                    alerta_emocional,
                    puntaje_riesgo,
                    nivel_riesgo,
                    fecha,
                    diagnostico_general_ia,
                    recomendacion_estudiante_ia,
                    recomendacion_tutoria_ia
                FROM diagnosticos
                WHERE estudiante_id = %s
                ORDER BY id DESC
                LIMIT 1
            """, (estudiante_id,))
            fila = cursor.fetchone()

    if fila is None:
        return None

    respuestas = {i: fila[i + 1] for i in range(1, 21)}
    return {
        "horas_estudio_dia": fila[0],
        "promedio_ponderado": fila[1],
        "respuestas": respuestas,
        "indice_estres": fila[22],
        "indice_procrastinacion": fila[23],
        "indice_motivacion": fila[24],
        "indice_estado_animo": fila[25],
        "alerta_emocional": fila[26],
        "puntaje_riesgo": fila[27],
        "nivel_riesgo": fila[28],
        "fecha": fila[29],
        "diagnostico_general_ia": fila[30],
        "recomendacion_estudiante_ia": fila[31],
        "recomendacion_tutoria_ia": fila[32],
    }


def registrar_curso(estudiante_id: int, nombre_curso: str, docente: str, creditos: int, dificultad: int, estado: str):
    with conectar() as conexion:
        with conexion.cursor() as cursor:
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT INTO cursos (estudiante_id, nombre_curso, docente, creditos, dificultad, estado, fecha_registro)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (estudiante_id, nombre_curso, docente, creditos, dificultad, estado, fecha))


def listar_cursos_por_estudiante(estudiante_id: int):
    with conectar() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute("""
                SELECT id, nombre_curso, docente, creditos, dificultad, estado
                FROM cursos
                WHERE estudiante_id = %s
                ORDER BY id DESC
            """, (estudiante_id,))
            return cursor.fetchall()


def existe_curso(estudiante_id: int, nombre_curso: str):
    with conectar() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute("""
                SELECT id FROM cursos
                WHERE estudiante_id = %s AND LOWER(nombre_curso) = LOWER(%s)
            """, (estudiante_id, nombre_curso.strip()))
            return cursor.fetchone() is not None


def eliminar_curso(curso_id: int):
    with conectar() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute("DELETE FROM cursos WHERE id = %s", (curso_id,))


def calcular_prioridad_tarea(fecha_entrega: str, dificultad: int):
    if not fecha_entrega:
        return "Media"
    try:
        hoy = datetime.now().date()
        entrega = datetime.strptime(fecha_entrega, "%Y-%m-%d").date()
        dias_restantes = (entrega - hoy).days
    except Exception:
        return "Media"
    if dias_restantes <= 1 or int(dificultad or 3) >= 5:
        return "Alta"
    if dias_restantes <= 3 or int(dificultad or 3) >= 4:
        return "Media"
    return "Baja"


def registrar_tarea(estudiante_id: int, curso_id: int, titulo: str, descripcion: str, fecha_entrega: str, dificultad: int):
    prioridad = calcular_prioridad_tarea(fecha_entrega, dificultad)
    with conectar() as conexion:
        with conexion.cursor() as cursor:
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT INTO tareas (estudiante_id, curso_id, titulo, descripcion, fecha_entrega, prioridad, estado, fecha_registro)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (estudiante_id, curso_id, titulo, descripcion, fecha_entrega, prioridad, "Pendiente", fecha))


def listar_tareas_por_estudiante(estudiante_id: int):
    with conectar() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute("""
                SELECT t.id, t.titulo, c.nombre_curso, t.fecha_entrega, t.prioridad, t.estado
                FROM tareas t
                INNER JOIN cursos c ON t.curso_id = c.id
                WHERE t.estudiante_id = %s
                ORDER BY t.fecha_entrega ASC
            """, (estudiante_id,))
            return cursor.fetchall()


def listar_tareas_para_planificador(estudiante_id: int):
    with conectar() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute("""
                SELECT t.id, t.titulo, c.nombre_curso, t.fecha_entrega, t.prioridad, t.estado, c.dificultad
                FROM tareas t
                INNER JOIN cursos c ON t.curso_id = c.id
                WHERE t.estudiante_id = %s
                ORDER BY t.fecha_entrega ASC
            """, (estudiante_id,))
            filas = cursor.fetchall()
    return [
        {"id": f[0], "titulo": f[1], "curso": f[2], "fecha_entrega": f[3], "prioridad": f[4], "estado": f[5], "dificultad": f[6]}
        for f in filas
    ]


def existe_tarea(estudiante_id: int, curso_id: int, titulo: str):
    with conectar() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute("""
                SELECT id FROM tareas
                WHERE estudiante_id = %s AND curso_id = %s AND LOWER(titulo) = LOWER(%s)
            """, (estudiante_id, curso_id, titulo.strip()))
            return cursor.fetchone() is not None


def actualizar_estado_tarea(tarea_id: int, nuevo_estado: str):
    with conectar() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute("UPDATE tareas SET estado = %s WHERE id = %s", (nuevo_estado, tarea_id))


def eliminar_tarea(tarea_id: int):
    with conectar() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute("DELETE FROM tareas WHERE id = %s", (tarea_id,))


def obtener_resumen_tareas(estudiante_id: int):
    with conectar() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM tareas WHERE estudiante_id = %s", (estudiante_id,))
            total = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM tareas WHERE estudiante_id = %s AND estado = 'Completada'", (estudiante_id,))
            completadas = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM tareas WHERE estudiante_id = %s AND estado != 'Completada'", (estudiante_id,))
            pendientes = cursor.fetchone()[0]
            cursor.execute("""
                SELECT COUNT(*) FROM tareas
                WHERE estudiante_id = %s AND prioridad = 'Alta' AND estado != 'Completada'
            """, (estudiante_id,))
            alta_prioridad = cursor.fetchone()[0]
    return {
        "total": total,
        "completadas": completadas,
        "pendientes": pendientes,
        "alta_prioridad": alta_prioridad,
        "porcentaje_cumplimiento": round((completadas / total) * 100, 2) if total else 0,
    }


def obtener_cursos_mayor_dificultad(estudiante_id: int):
    with conectar() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute("""
                SELECT nombre_curso, dificultad
                FROM cursos
                WHERE estudiante_id = %s
                ORDER BY dificultad DESC
                LIMIT 5
            """, (estudiante_id,))
            return cursor.fetchall()


def obtener_panel_tutoria():
    with conectar() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute("""
                SELECT
                    e.id,
                    e.nombre,
                    e.codigo,
                    e.carrera,
                    e.ciclo,
                    COALESCE(d.promedio_ponderado, d.promedio_actual),
                    COALESCE(d.indice_estres, d.nivel_estres),
                    COALESCE(d.indice_motivacion, d.nivel_motivacion),
                    COALESCE(d.indice_procrastinacion, d.nivel_procrastinacion),
                    d.indice_estado_animo,
                    d.alerta_emocional,
                    d.puntaje_riesgo,
                    d.nivel_riesgo,
                    d.fecha,
                    (SELECT COUNT(*) FROM tareas t WHERE t.estudiante_id = e.id) AS total_tareas,
                    (SELECT COUNT(*) FROM tareas t WHERE t.estudiante_id = e.id AND t.estado != 'Completada') AS tareas_pendientes,
                    (SELECT COUNT(*) FROM tareas t WHERE t.estudiante_id = e.id AND t.prioridad = 'Alta' AND t.estado != 'Completada') AS tareas_alta_prioridad
                FROM estudiantes e
                LEFT JOIN diagnosticos d ON d.id = (
                    SELECT d2.id FROM diagnosticos d2
                    WHERE d2.estudiante_id = e.id
                    ORDER BY d2.id DESC
                    LIMIT 1
                )
                ORDER BY
                    CASE d.nivel_riesgo
                        WHEN 'Alto' THEN 1
                        WHEN 'Medio' THEN 2
                        WHEN 'Bajo' THEN 3
                        ELSE 4
                    END,
                    e.nombre ASC
            """)
            return cursor.fetchall()


def obtener_tabla_completa(nombre_tabla: str):
    tablas_permitidas = {"estudiantes", "usuarios", "diagnosticos", "cursos", "tareas"}
    if nombre_tabla not in tablas_permitidas:
        raise ValueError("Tabla no permitida")
    with conectar() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {nombre_tabla} ORDER BY id DESC")
            filas = cursor.fetchall()
            columnas = [desc.name for desc in cursor.description]
    return columnas, filas
