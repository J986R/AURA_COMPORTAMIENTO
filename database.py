import hashlib
import json
from datetime import datetime
from typing import Any, Optional

import psycopg

from config import get_setting


def _database_url() -> str:
    url = get_setting("NEON_DATABASE_URL")
    if not url:
        raise RuntimeError("Falta configurar NEON_DATABASE_URL en Streamlit Secrets o .env.")
    return str(url)


def conectar():
    return psycopg.connect(_database_url())


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def nivel_por_puntaje(puntaje: Any) -> str:
    try:
        p = int(float(puntaje))
    except Exception:
        return "Sin diagnóstico"
    if p >= 70:
        return "Alto"
    if p >= 40:
        return "Medio"
    return "Bajo"


def _fetchall(query: str, params: tuple = ()): 
    with conectar() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()


def _fetchone(query: str, params: tuple = ()): 
    with conectar() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchone()


def _execute(query: str, params: tuple = ()): 
    with conectar() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
        conn.commit()


def crear_tablas():
    with conectar() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS estudiantes (
                    id SERIAL PRIMARY KEY,
                    nombre TEXT NOT NULL,
                    codigo TEXT,
                    carrera TEXT,
                    ciclo TEXT,
                    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id SERIAL PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    rol TEXT NOT NULL,
                    estudiante_id INTEGER REFERENCES estudiantes(id) ON DELETE SET NULL,
                    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS diagnosticos (
                    id SERIAL PRIMARY KEY,
                    estudiante_id INTEGER NOT NULL REFERENCES estudiantes(id) ON DELETE CASCADE,
                    horas_estudio REAL NOT NULL,
                    promedio_actual REAL NOT NULL,
                    tareas_pendientes INTEGER NOT NULL DEFAULT 0,
                    nivel_estres REAL NOT NULL DEFAULT 0,
                    nivel_motivacion REAL NOT NULL DEFAULT 0,
                    nivel_procrastinacion REAL NOT NULL DEFAULT 0,
                    puntaje_riesgo INTEGER NOT NULL,
                    nivel_riesgo TEXT NOT NULL,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
                    codigo_curso TEXT,
                    docente TEXT,
                    creditos INTEGER,
                    dificultad INTEGER,
                    estado TEXT,
                    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tareas (
                    id SERIAL PRIMARY KEY,
                    estudiante_id INTEGER NOT NULL REFERENCES estudiantes(id) ON DELETE CASCADE,
                    curso_id INTEGER NOT NULL REFERENCES cursos(id) ON DELETE CASCADE,
                    titulo TEXT NOT NULL,
                    descripcion TEXT,
                    fecha_entrega DATE,
                    tipo_actividad TEXT DEFAULT 'Tarea',
                    prioridad TEXT,
                    estado TEXT,
                    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS planes_semanales (
                    id SERIAL PRIMARY KEY,
                    estudiante_id INTEGER NOT NULL REFERENCES estudiantes(id) ON DELETE CASCADE,
                    plan_json TEXT NOT NULL,
                    horas_disponibles REAL,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS coach_recomendaciones (
                    id SERIAL PRIMARY KEY,
                    estudiante_id INTEGER NOT NULL REFERENCES estudiantes(id) ON DELETE CASCADE,
                    recomendacion TEXT NOT NULL,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS horarios_clase (
                    id SERIAL PRIMARY KEY,
                    estudiante_id INTEGER NOT NULL REFERENCES estudiantes(id) ON DELETE CASCADE,
                    curso_id INTEGER REFERENCES cursos(id) ON DELETE CASCADE,
                    codigo_curso TEXT,
                    nombre_curso TEXT,
                    tipo TEXT,
                    docente TEXT,
                    dia TEXT NOT NULL,
                    hora_inicio TIME NOT NULL,
                    hora_fin TIME NOT NULL,
                    aula TEXT,
                    color TEXT,
                    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notas_curso (
                    id SERIAL PRIMARY KEY,
                    estudiante_id INTEGER NOT NULL REFERENCES estudiantes(id) ON DELETE CASCADE,
                    curso_id INTEGER REFERENCES cursos(id) ON DELETE CASCADE,
                    ciclo TEXT,
                    codigo_curso TEXT,
                    nombre_curso TEXT,
                    tipo_evaluacion TEXT,
                    nombre_evaluacion TEXT,
                    nota REAL,
                    peso REAL,
                    observacion TEXT,
                    origen TEXT,
                    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Migraciones para bases creadas con versiones anteriores.
            migraciones = [
                "ALTER TABLE diagnosticos ADD COLUMN IF NOT EXISTS horas_estudio_dia REAL",
                "ALTER TABLE diagnosticos ADD COLUMN IF NOT EXISTS promedio_ponderado REAL",
                *[f"ALTER TABLE diagnosticos ADD COLUMN IF NOT EXISTS pregunta_{i} INTEGER" for i in range(1, 21)],
                "ALTER TABLE diagnosticos ADD COLUMN IF NOT EXISTS indice_estres REAL",
                "ALTER TABLE diagnosticos ADD COLUMN IF NOT EXISTS indice_procrastinacion REAL",
                "ALTER TABLE diagnosticos ADD COLUMN IF NOT EXISTS indice_motivacion REAL",
                "ALTER TABLE diagnosticos ADD COLUMN IF NOT EXISTS indice_estado_animo REAL",
                "ALTER TABLE diagnosticos ADD COLUMN IF NOT EXISTS alerta_emocional INTEGER",
                "ALTER TABLE diagnosticos ADD COLUMN IF NOT EXISTS diagnostico_general_ia TEXT",
                "ALTER TABLE diagnosticos ADD COLUMN IF NOT EXISTS recomendacion_estudiante_ia TEXT",
                "ALTER TABLE diagnosticos ADD COLUMN IF NOT EXISTS recomendacion_tutoria_ia TEXT",
                "ALTER TABLE cursos ADD COLUMN IF NOT EXISTS codigo_curso TEXT",
                "ALTER TABLE tareas ADD COLUMN IF NOT EXISTS tipo_actividad TEXT DEFAULT 'Tarea'",
                "ALTER TABLE horarios_clase ADD COLUMN IF NOT EXISTS color TEXT",
                "ALTER TABLE notas_curso ADD COLUMN IF NOT EXISTS peso REAL",
                "ALTER TABLE notas_curso ADD COLUMN IF NOT EXISTS observacion TEXT",
                "ALTER TABLE notas_curso ADD COLUMN IF NOT EXISTS origen TEXT",
            ]
            for sql in migraciones:
                cursor.execute(sql)
        conn.commit()

    crear_admin_por_defecto()


def crear_admin_por_defecto():
    with conectar() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM usuarios WHERE username = %s", ("admin",))
            if cur.fetchone() is None:
                cur.execute(
                    """
                    INSERT INTO usuarios (username, password_hash, rol, estudiante_id, fecha_registro)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    ("admin", hash_password("aura123"), "Administrador", None, datetime.now()),
                )
        conn.commit()


def autenticar_usuario(username: str, password: str):
    fila = _fetchone(
        """
        SELECT id, username, password_hash, rol, estudiante_id
        FROM usuarios
        WHERE username = %s
        """,
        (username,),
    )
    if fila is None:
        return None
    id_usuario, username_db, password_hash_db, rol, estudiante_id = fila
    if hash_password(password) == password_hash_db:
        return {"id": id_usuario, "username": username_db, "rol": rol, "estudiante_id": estudiante_id}
    return None


def registrar_usuario(username: str, password: str, rol: str, estudiante_id: Optional[int] = None):
    try:
        _execute(
            """
            INSERT INTO usuarios (username, password_hash, rol, estudiante_id, fecha_registro)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (username, hash_password(password), rol, estudiante_id, datetime.now()),
        )
        return True, "Usuario creado correctamente."
    except Exception as e:
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            return False, "El nombre de usuario ya existe."
        return False, str(e)


def listar_usuarios():
    return _fetchall(
        """
        SELECT u.id, u.username, u.rol, e.nombre, u.fecha_registro
        FROM usuarios u
        LEFT JOIN estudiantes e ON u.estudiante_id = e.id
        ORDER BY u.id DESC
        """
    )


def obtener_usuario_por_id(usuario_id: int):
    return _fetchone(
        """
        SELECT u.id, u.username, u.rol, u.estudiante_id, e.nombre
        FROM usuarios u
        LEFT JOIN estudiantes e ON u.estudiante_id = e.id
        WHERE u.id = %s
        """,
        (usuario_id,),
    )


def actualizar_usuario(usuario_id: int, username: str, password: Optional[str] = None):
    try:
        if password and password.strip():
            _execute(
                "UPDATE usuarios SET username = %s, password_hash = %s WHERE id = %s",
                (username, hash_password(password), usuario_id),
            )
        else:
            _execute("UPDATE usuarios SET username = %s WHERE id = %s", (username, usuario_id))
        return True, "Datos de usuario actualizados correctamente."
    except Exception as e:
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            return False, "El nombre de usuario ya existe."
        return False, str(e)


def eliminar_usuario(usuario_id: int):
    with conectar() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT rol FROM usuarios WHERE id = %s", (usuario_id,))
            fila = cur.fetchone()
            if fila is None:
                return False, "El usuario no existe."
            rol = fila[0]
            if rol == "Administrador":
                cur.execute("SELECT COUNT(*) FROM usuarios WHERE rol = 'Administrador'")
                if cur.fetchone()[0] <= 1:
                    return False, "No se puede eliminar el último usuario administrador."
            cur.execute("DELETE FROM usuarios WHERE id = %s", (usuario_id,))
        conn.commit()
    return True, "Usuario eliminado correctamente."


def registrar_estudiante(nombre: str, codigo: str, carrera: str, ciclo: str):
    with conectar() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO estudiantes (nombre, codigo, carrera, ciclo, fecha_registro)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (nombre, codigo, carrera, ciclo, datetime.now()),
            )
            estudiante_id = cur.fetchone()[0]
        conn.commit()
    return estudiante_id


def listar_estudiantes():
    return _fetchall(
        """
        SELECT id, nombre, codigo, carrera, ciclo
        FROM estudiantes
        ORDER BY id DESC
        """
    )


def obtener_estudiante_por_id(estudiante_id: int):
    return _fetchone(
        """
        SELECT id, nombre, codigo, carrera, ciclo
        FROM estudiantes
        WHERE id = %s
        """,
        (estudiante_id,),
    )


def actualizar_estudiante(estudiante_id: int, nombre: str, codigo: str, carrera: str, ciclo: str):
    _execute(
        """
        UPDATE estudiantes
        SET nombre = %s, codigo = %s, carrera = %s, ciclo = %s
        WHERE id = %s
        """,
        (nombre, codigo, carrera, ciclo, estudiante_id),
    )
    return True, "Datos del estudiante actualizados correctamente."


def eliminar_estudiante(estudiante_id: int):
    fila = obtener_estudiante_por_id(estudiante_id)
    if fila is None:
        return False, "El estudiante no existe."
    _execute("DELETE FROM estudiantes WHERE id = %s", (estudiante_id,))
    return True, "Estudiante eliminado correctamente junto con sus datos asociados."


def guardar_diagnostico_ia(estudiante_id: int, horas_estudio_dia: float, promedio_ponderado: float, respuestas: dict, resultado_ia: dict):
    puntaje = int(resultado_ia["puntaje_riesgo"])
    nivel = nivel_por_puntaje(puntaje)
    # El nivel guardado se normaliza con el puntaje para evitar incoherencias.
    resultado_ia["nivel_riesgo"] = nivel

    valores = (
        estudiante_id,
        horas_estudio_dia,
        promedio_ponderado,
        0,
        resultado_ia["indice_estres"],
        resultado_ia["indice_motivacion"],
        resultado_ia["indice_procrastinacion"],
        puntaje,
        nivel,
        datetime.now(),
        horas_estudio_dia,
        promedio_ponderado,
        *[int(respuestas[i]) for i in range(1, 21)],
        resultado_ia["indice_estres"],
        resultado_ia["indice_procrastinacion"],
        resultado_ia["indice_motivacion"],
        resultado_ia["indice_estado_animo"],
        int(resultado_ia["alerta_emocional"]),
        resultado_ia.get("diagnostico_general", ""),
        resultado_ia.get("recomendacion_estudiante", ""),
        resultado_ia.get("recomendacion_tutoria", ""),
    )

    columnas = """
        estudiante_id, horas_estudio, promedio_actual, tareas_pendientes,
        nivel_estres, nivel_motivacion, nivel_procrastinacion,
        puntaje_riesgo, nivel_riesgo, fecha,
        horas_estudio_dia, promedio_ponderado,
        pregunta_1, pregunta_2, pregunta_3, pregunta_4, pregunta_5,
        pregunta_6, pregunta_7, pregunta_8, pregunta_9, pregunta_10,
        pregunta_11, pregunta_12, pregunta_13, pregunta_14, pregunta_15,
        pregunta_16, pregunta_17, pregunta_18, pregunta_19, pregunta_20,
        indice_estres, indice_procrastinacion, indice_motivacion, indice_estado_animo,
        alerta_emocional, diagnostico_general_ia, recomendacion_estudiante_ia, recomendacion_tutoria_ia
    """
    placeholders = ",".join(["%s"] * len(valores))
    _execute(f"INSERT INTO diagnosticos ({columnas}) VALUES ({placeholders})", valores)
    return True


def obtener_ultimo_diagnostico(estudiante_id: int):
    fila = _fetchone(
        """
        SELECT
            COALESCE(horas_estudio_dia, horas_estudio) AS horas,
            COALESCE(promedio_ponderado, promedio_actual) AS promedio,
            COALESCE(tareas_pendientes, 0) AS tareas_pendientes,
            COALESCE(indice_estres, nivel_estres) AS estres,
            COALESCE(indice_motivacion, nivel_motivacion) AS motivacion,
            COALESCE(indice_procrastinacion, nivel_procrastinacion) AS procrastinacion,
            puntaje_riesgo,
            nivel_riesgo,
            fecha
        FROM diagnosticos
        WHERE estudiante_id = %s
        ORDER BY id DESC
        LIMIT 1
        """,
        (estudiante_id,),
    )
    if fila is None:
        return None
    fila = list(fila)
    fila[7] = nivel_por_puntaje(fila[6])
    return tuple(fila)


def obtener_ultimo_diagnostico_detallado(estudiante_id: int):
    fila = _fetchone(
        """
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
        """,
        (estudiante_id,),
    )
    if fila is None:
        return None

    respuestas = {i: fila[i + 1] if fila[i + 1] is not None else 3 for i in range(1, 21)}
    puntaje = int(fila[27]) if fila[27] is not None else 0
    return {
        "horas_estudio_dia": fila[0],
        "promedio_ponderado": fila[1],
        "respuestas": respuestas,
        "indice_estres": fila[22],
        "indice_procrastinacion": fila[23],
        "indice_motivacion": fila[24],
        "indice_estado_animo": fila[25],
        "alerta_emocional": fila[26],
        "puntaje_riesgo": puntaje,
        "nivel_riesgo": nivel_por_puntaje(puntaje),
        "fecha": fila[29],
        "diagnostico_general_ia": fila[30],
        "recomendacion_estudiante_ia": fila[31],
        "recomendacion_tutoria_ia": fila[32],
    }


def registrar_curso(estudiante_id: int, nombre_curso: str, docente: str, creditos: int, dificultad: int, estado: str, codigo_curso: Optional[str] = None):
    """Registra un curso y devuelve el ID creado.
    Se devuelve el ID para poder asociar horarios manuales inmediatamente.
    """
    with conectar() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO cursos (estudiante_id, nombre_curso, codigo_curso, docente, creditos, dificultad, estado, fecha_registro)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (estudiante_id, nombre_curso, codigo_curso, docente, creditos, dificultad, estado, datetime.now()),
            )
            curso_id = cur.fetchone()[0]
        conn.commit()
    return curso_id


def listar_cursos_por_estudiante(estudiante_id: int):
    return _fetchall(
        """
        SELECT id, nombre_curso, docente, creditos, dificultad, estado
        FROM cursos
        WHERE estudiante_id = %s
        ORDER BY id DESC
        """,
        (estudiante_id,),
    )


def obtener_curso_por_id(curso_id: int):
    return _fetchone(
        """
        SELECT id, estudiante_id, nombre_curso, docente, creditos, dificultad, estado
        FROM cursos
        WHERE id = %s
        """,
        (curso_id,),
    )


def actualizar_curso(curso_id: int, nombre_curso: str, docente: str, creditos: int, dificultad: int, estado: str):
    _execute(
        """
        UPDATE cursos
        SET nombre_curso = %s, docente = %s, creditos = %s, dificultad = %s, estado = %s
        WHERE id = %s
        """,
        (nombre_curso, docente, creditos, dificultad, estado, curso_id),
    )
    return True, "Curso actualizado correctamente."


def existe_curso(estudiante_id: int, nombre_curso: str):
    fila = _fetchone(
        """
        SELECT id FROM cursos
        WHERE estudiante_id = %s AND LOWER(nombre_curso) = LOWER(%s)
        LIMIT 1
        """,
        (estudiante_id, nombre_curso.strip()),
    )
    return fila is not None


def eliminar_curso(curso_id: int):
    _execute("DELETE FROM cursos WHERE id = %s", (curso_id,))


def calcular_prioridad_tarea(fecha_entrega, dificultad: int, tipo_actividad: str = "Tarea"):
    if not fecha_entrega:
        return "Media"
    hoy = datetime.now().date()
    if isinstance(fecha_entrega, str):
        entrega = datetime.strptime(fecha_entrega, "%Y-%m-%d").date()
    else:
        entrega = fecha_entrega
    dias = (entrega - hoy).days
    tipo = (tipo_actividad or "Tarea").lower()
    peso_tipo = 0
    if "final" in tipo:
        peso_tipo = 4
    elif "parcial" in tipo:
        peso_tipo = 3
    elif "monografía" in tipo or "monografia" in tipo:
        peso_tipo = 3
    elif "práctica" in tipo or "practica" in tipo:
        peso_tipo = 2
    try:
        dificultad = int(dificultad or 3)
    except Exception:
        dificultad = 3
    if dias <= 1 or dificultad >= 5 or peso_tipo >= 4:
        return "Alta"
    if dias <= 3 or dificultad >= 4 or peso_tipo >= 2:
        return "Media"
    return "Baja"


def registrar_tarea(estudiante_id: int, curso_id: int, titulo: str, descripcion: str, fecha_entrega: str, dificultad: int, tipo_actividad: str = "Tarea"):
    prioridad = calcular_prioridad_tarea(fecha_entrega, dificultad, tipo_actividad)
    _execute(
        """
        INSERT INTO tareas (estudiante_id, curso_id, titulo, descripcion, fecha_entrega, tipo_actividad, prioridad, estado, fecha_registro)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (estudiante_id, curso_id, titulo, descripcion, fecha_entrega, tipo_actividad, prioridad, "Pendiente", datetime.now()),
    )


def listar_tareas_por_estudiante(estudiante_id: int):
    return _fetchall(
        """
        SELECT t.id, COALESCE(t.tipo_actividad, 'Tarea') AS tipo_actividad, t.titulo, c.nombre_curso, t.fecha_entrega, t.prioridad, t.estado
        FROM tareas t
        INNER JOIN cursos c ON t.curso_id = c.id
        WHERE t.estudiante_id = %s
        ORDER BY t.fecha_entrega ASC NULLS LAST, t.id DESC
        """,
        (estudiante_id,),
    )


def listar_tareas_para_planificador(estudiante_id: int):
    filas = _fetchall(
        """
        SELECT t.id, t.titulo, c.nombre_curso, t.fecha_entrega, t.prioridad, t.estado, c.dificultad, COALESCE(t.descripcion, ''), COALESCE(t.tipo_actividad, 'Tarea')
        FROM tareas t
        INNER JOIN cursos c ON t.curso_id = c.id
        WHERE t.estudiante_id = %s
        ORDER BY t.fecha_entrega ASC NULLS LAST, t.id DESC
        """,
        (estudiante_id,),
    )
    tareas = []
    for f in filas:
        tareas.append(
            {
                "id": f[0],
                "titulo": f[1],
                "curso": f[2],
                "fecha_entrega": str(f[3]) if f[3] is not None else "-",
                "prioridad": f[4],
                "estado": f[5],
                "dificultad": f[6],
                "descripcion": f[7],
                "tipo_actividad": f[8],
            }
        )
    return tareas


def existe_tarea(estudiante_id: int, curso_id: int, titulo: str):
    fila = _fetchone(
        """
        SELECT id FROM tareas
        WHERE estudiante_id = %s AND curso_id = %s AND LOWER(titulo) = LOWER(%s)
        LIMIT 1
        """,
        (estudiante_id, curso_id, titulo.strip()),
    )
    return fila is not None


def actualizar_estado_tarea(tarea_id: int, nuevo_estado: str):
    _execute("UPDATE tareas SET estado = %s WHERE id = %s", (nuevo_estado, tarea_id))


def eliminar_tarea(tarea_id: int):
    _execute("DELETE FROM tareas WHERE id = %s", (tarea_id,))


def obtener_tarea_por_id(tarea_id: int):
    return _fetchone(
        """
        SELECT t.id, t.estudiante_id, t.curso_id, t.titulo, COALESCE(t.descripcion, ''),
               t.fecha_entrega, t.prioridad, t.estado, c.nombre_curso, c.dificultad, COALESCE(t.tipo_actividad, 'Tarea')
        FROM tareas t
        INNER JOIN cursos c ON t.curso_id = c.id
        WHERE t.id = %s
        """,
        (tarea_id,),
    )


def actualizar_tarea(tarea_id: int, curso_id: int, titulo: str, descripcion: str, fecha_entrega: str, estado: str, dificultad: int, tipo_actividad: str = "Tarea"):
    prioridad = calcular_prioridad_tarea(fecha_entrega, dificultad, tipo_actividad)
    _execute(
        """
        UPDATE tareas
        SET curso_id = %s,
            titulo = %s,
            descripcion = %s,
            fecha_entrega = %s,
            tipo_actividad = %s,
            prioridad = %s,
            estado = %s
        WHERE id = %s
        """,
        (curso_id, titulo, descripcion, fecha_entrega, tipo_actividad, prioridad, estado, tarea_id),
    )
    return True, "Tarea actualizada correctamente."


def guardar_plan_semanal(estudiante_id: int, plan: list, horas_disponibles: float):
    plan_json = json.dumps(plan, ensure_ascii=False)
    _execute(
        """
        INSERT INTO planes_semanales (estudiante_id, plan_json, horas_disponibles, fecha)
        VALUES (%s, %s, %s, %s)
        """,
        (estudiante_id, plan_json, horas_disponibles, datetime.now()),
    )
    return True


def obtener_ultimo_plan_semanal(estudiante_id: int):
    fila = _fetchone(
        """
        SELECT id, plan_json, horas_disponibles, fecha
        FROM planes_semanales
        WHERE estudiante_id = %s
        ORDER BY id DESC
        LIMIT 1
        """,
        (estudiante_id,),
    )
    if fila is None:
        return None
    try:
        plan = json.loads(fila[1])
    except Exception:
        plan = []
    return {
        "id": fila[0],
        "plan": plan,
        "horas_disponibles": fila[2],
        "fecha": fila[3],
    }


def guardar_recomendacion_coach(estudiante_id: int, recomendacion: str):
    _execute(
        """
        INSERT INTO coach_recomendaciones (estudiante_id, recomendacion, fecha)
        VALUES (%s, %s, %s)
        """,
        (estudiante_id, recomendacion, datetime.now()),
    )
    return True


def obtener_ultima_recomendacion_coach(estudiante_id: int):
    fila = _fetchone(
        """
        SELECT id, recomendacion, fecha
        FROM coach_recomendaciones
        WHERE estudiante_id = %s
        ORDER BY id DESC
        LIMIT 1
        """,
        (estudiante_id,),
    )
    if fila is None:
        return None
    return {"id": fila[0], "recomendacion": fila[1], "fecha": fila[2]}


def obtener_resumen_tareas(estudiante_id: int):
    fila = _fetchone(
        """
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN estado = 'Completada' THEN 1 ELSE 0 END) AS completadas,
            SUM(CASE WHEN estado <> 'Completada' THEN 1 ELSE 0 END) AS pendientes,
            SUM(CASE WHEN prioridad = 'Alta' AND estado <> 'Completada' THEN 1 ELSE 0 END) AS alta_prioridad
        FROM tareas
        WHERE estudiante_id = %s
        """,
        (estudiante_id,),
    )
    total = int(fila[0] or 0)
    completadas = int(fila[1] or 0)
    pendientes = int(fila[2] or 0)
    alta = int(fila[3] or 0)
    porcentaje = round((completadas / total) * 100, 2) if total else 0
    return {"total": total, "completadas": completadas, "pendientes": pendientes, "alta_prioridad": alta, "porcentaje_cumplimiento": porcentaje}


def obtener_cursos_mayor_dificultad(estudiante_id: int):
    return _fetchall(
        """
        SELECT nombre_curso, dificultad
        FROM cursos
        WHERE estudiante_id = %s
        ORDER BY dificultad DESC NULLS LAST
        LIMIT 5
        """,
        (estudiante_id,),
    )


def obtener_panel_tutoria():
    filas = _fetchall(
        """
        SELECT
            e.id, e.nombre, e.codigo, e.carrera, e.ciclo,
            COALESCE(d.promedio_ponderado, d.promedio_actual) AS promedio,
            COALESCE(d.indice_estres, d.nivel_estres) AS estres,
            COALESCE(d.indice_motivacion, d.nivel_motivacion) AS motivacion,
            COALESCE(d.indice_procrastinacion, d.nivel_procrastinacion) AS procrastinacion,
            d.indice_estado_animo,
            d.alerta_emocional,
            d.puntaje_riesgo,
            d.nivel_riesgo,
            d.fecha,
            (SELECT COUNT(*) FROM tareas t WHERE t.estudiante_id = e.id) AS total_tareas,
            (SELECT COUNT(*) FROM tareas t WHERE t.estudiante_id = e.id AND t.estado <> 'Completada') AS tareas_pendientes,
            (SELECT COUNT(*) FROM tareas t WHERE t.estudiante_id = e.id AND t.prioridad = 'Alta' AND t.estado <> 'Completada') AS alta_prioridad
        FROM estudiantes e
        LEFT JOIN LATERAL (
            SELECT * FROM diagnosticos d2
            WHERE d2.estudiante_id = e.id
            ORDER BY d2.id DESC
            LIMIT 1
        ) d ON TRUE
        ORDER BY e.nombre ASC
        """
    )
    normalizadas = []
    for fila in filas:
        f = list(fila)
        if f[11] is not None:
            f[12] = nivel_por_puntaje(f[11])
        normalizadas.append(tuple(f))
    orden = {"Alto": 0, "Medio": 1, "Bajo": 2, None: 3, "Sin diagnóstico": 3}
    normalizadas.sort(key=lambda x: (orden.get(x[12], 3), x[1] or ""))
    return normalizadas



def _color_para_curso(codigo_o_nombre: str) -> str:
    colores = ["#0B1F4D", "#14B8B8", "#7C3AED", "#2563EB", "#16A34A", "#F59E0B", "#DC2626", "#0891B2"]
    clave = codigo_o_nombre or "AURA"
    return colores[sum(ord(c) for c in clave) % len(colores)]


def buscar_curso_por_codigo_o_nombre(estudiante_id: int, codigo_curso: Optional[str], nombre_curso: str):
    if codigo_curso:
        fila = _fetchone(
            """
            SELECT id, nombre_curso, docente, creditos, dificultad, estado
            FROM cursos
            WHERE estudiante_id = %s AND codigo_curso = %s
            LIMIT 1
            """,
            (estudiante_id, codigo_curso),
        )
        if fila:
            return fila
    return _fetchone(
        """
        SELECT id, nombre_curso, docente, creditos, dificultad, estado
        FROM cursos
        WHERE estudiante_id = %s AND LOWER(nombre_curso) = LOWER(%s)
        LIMIT 1
        """,
        (estudiante_id, nombre_curso),
    )


def obtener_o_crear_curso_boleta(estudiante_id: int, codigo_curso: str, nombre_curso: str, creditos: int = 0, docente: str = ""):
    nombre_limpio = (nombre_curso or codigo_curso).strip().strip("-")
    nombre_visible = f"{codigo_curso} - {nombre_limpio}" if codigo_curso and codigo_curso not in nombre_limpio else nombre_limpio
    fila = buscar_curso_por_codigo_o_nombre(estudiante_id, codigo_curso, nombre_visible)
    if fila:
        return fila[0]
    with conectar() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO cursos (estudiante_id, nombre_curso, codigo_curso, docente, creditos, dificultad, estado, fecha_registro)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (estudiante_id, nombre_visible, codigo_curso, docente, int(creditos or 0), 3, "En curso", datetime.now()),
            )
            curso_id = cur.fetchone()[0]
        conn.commit()
    return curso_id


def registrar_horario_clase(estudiante_id: int, curso_id: Optional[int], codigo_curso: str, nombre_curso: str, tipo: str, docente: str, dia: str, hora_inicio: str, hora_fin: str, aula: str, color: Optional[str] = None):
    color = color or _color_para_curso(codigo_curso or nombre_curso)
    _execute(
        """
        INSERT INTO horarios_clase (estudiante_id, curso_id, codigo_curso, nombre_curso, tipo, docente, dia, hora_inicio, hora_fin, aula, color, fecha_registro)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (estudiante_id, curso_id, codigo_curso, nombre_curso, tipo, docente, dia, hora_inicio, hora_fin, aula, color, datetime.now()),
    )


def eliminar_horario_clase(horario_id: int):
    _execute("DELETE FROM horarios_clase WHERE id = %s", (horario_id,))
    return True


def limpiar_horarios_clase(estudiante_id: int):
    _execute("DELETE FROM horarios_clase WHERE estudiante_id = %s", (estudiante_id,))
    return True


def listar_horarios_clase(estudiante_id: int):
    filas = _fetchall(
        """
        SELECT id, curso_id, codigo_curso, nombre_curso, tipo, docente, dia,
               TO_CHAR(hora_inicio, 'HH24:MI'), TO_CHAR(hora_fin, 'HH24:MI'), aula, color
        FROM horarios_clase
        WHERE estudiante_id = %s
        ORDER BY CASE dia
            WHEN 'Lunes' THEN 1 WHEN 'Martes' THEN 2 WHEN 'Miércoles' THEN 3 WHEN 'Jueves' THEN 4
            WHEN 'Viernes' THEN 5 WHEN 'Sábado' THEN 6 WHEN 'Domingo' THEN 7 ELSE 8 END,
            hora_inicio ASC
        """,
        (estudiante_id,),
    )
    horarios = []
    for f in filas:
        horarios.append({
            "id": f[0],
            "curso_id": f[1],
            "codigo_curso": f[2],
            "nombre_curso": f[3],
            "tipo": f[4],
            "docente": f[5],
            "dia": f[6],
            "inicio": f[7],
            "fin": f[8],
            "aula": f[9],
            "color": f[10] or _color_para_curso(f[2] or f[3]),
        })
    return horarios


def importar_boleta_matricula(estudiante_id: int, cursos: list, horarios: list, reemplazar_horarios: bool = True):
    if reemplazar_horarios:
        limpiar_horarios_clase(estudiante_id)
    mapa_cursos = {}
    for curso in cursos:
        codigo = curso.get("codigo_curso") or curso.get("codigo") or ""
        nombre = curso.get("nombre_curso") or curso.get("nombre") or codigo
        creditos = int(curso.get("creditos") or 0)
        curso_id = obtener_o_crear_curso_boleta(estudiante_id, codigo, nombre, creditos, curso.get("docente", ""))
        mapa_cursos[codigo] = curso_id
    for h in horarios:
        codigo = h.get("codigo_curso") or h.get("codigo") or ""
        curso_id = mapa_cursos.get(codigo)
        if not curso_id:
            curso_id = obtener_o_crear_curso_boleta(estudiante_id, codigo, h.get("nombre_curso") or codigo, 0, h.get("docente", ""))
        registrar_horario_clase(
            estudiante_id=estudiante_id,
            curso_id=curso_id,
            codigo_curso=codigo,
            nombre_curso=h.get("nombre_curso") or codigo,
            tipo=h.get("tipo") or "Clase",
            docente=h.get("docente") or "",
            dia=h.get("dia") or "",
            hora_inicio=h.get("inicio") or h.get("hora_inicio") or "08:00",
            hora_fin=h.get("fin") or h.get("hora_fin") or "09:00",
            aula=h.get("aula") or "",
        )
    return True, f"Se importaron {len(cursos)} cursos y {len(horarios)} bloques de horario."


def limpiar_notas_curso(estudiante_id: int, ciclo: Optional[str] = None):
    if ciclo:
        _execute("DELETE FROM notas_curso WHERE estudiante_id = %s AND ciclo = %s", (estudiante_id, ciclo))
    else:
        _execute("DELETE FROM notas_curso WHERE estudiante_id = %s", (estudiante_id,))
    return True


def guardar_nota_curso(
    estudiante_id: int,
    curso_id: Optional[int],
    ciclo: str,
    codigo_curso: str,
    nombre_curso: str,
    tipo_evaluacion: str,
    nombre_evaluacion: str,
    nota: Optional[float],
    peso: Optional[float] = None,
    observacion: str = "",
    origen: str = "INTRALU",
):
    _execute(
        """
        INSERT INTO notas_curso (
            estudiante_id, curso_id, ciclo, codigo_curso, nombre_curso,
            tipo_evaluacion, nombre_evaluacion, nota, peso, observacion, origen, fecha_registro
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            estudiante_id,
            curso_id,
            ciclo,
            codigo_curso,
            nombre_curso,
            tipo_evaluacion,
            nombre_evaluacion,
            nota,
            peso,
            observacion,
            origen,
            datetime.now(),
        ),
    )
    return True


def listar_notas_por_estudiante(estudiante_id: int, ciclo: Optional[str] = None):
    if ciclo:
        filas = _fetchall(
            """
            SELECT id, ciclo, codigo_curso, nombre_curso, tipo_evaluacion,
                   nombre_evaluacion, nota, peso, observacion, fecha_registro
            FROM notas_curso
            WHERE estudiante_id = %s AND ciclo = %s
            ORDER BY codigo_curso ASC, id ASC
            """,
            (estudiante_id, ciclo),
        )
    else:
        filas = _fetchall(
            """
            SELECT id, ciclo, codigo_curso, nombre_curso, tipo_evaluacion,
                   nombre_evaluacion, nota, peso, observacion, fecha_registro
            FROM notas_curso
            WHERE estudiante_id = %s
            ORDER BY fecha_registro DESC, codigo_curso ASC, id ASC
            """,
            (estudiante_id,),
        )
    return filas


def obtener_resumen_notas(estudiante_id: int):
    filas = _fetchall(
        """
        SELECT codigo_curso, nombre_curso, AVG(nota) AS promedio, MIN(nota) AS minima, COUNT(*) AS total
        FROM notas_curso
        WHERE estudiante_id = %s AND nota IS NOT NULL
        GROUP BY codigo_curso, nombre_curso
        ORDER BY promedio ASC NULLS LAST
        """,
        (estudiante_id,),
    )
    return filas


def importar_intralu_resultado(estudiante_id: int, datos: dict, ciclo: str, reemplazar_horarios: bool = True, reemplazar_notas: bool = True):
    """Guarda en Neon el resultado devuelto por intralu_scraper.

    Las credenciales nunca entran a esta función. Solo llegan cursos, horarios y notas ya extraídos.
    """
    cursos = datos.get("cursos", []) or []
    horarios = datos.get("horarios", []) or []
    notas = datos.get("notas", []) or []

    if reemplazar_horarios:
        limpiar_horarios_clase(estudiante_id)
    if reemplazar_notas:
        limpiar_notas_curso(estudiante_id, ciclo)

    mapa_cursos = {}
    for curso in cursos:
        codigo = curso.get("codigo_curso") or curso.get("codigo") or ""
        nombre = curso.get("nombre_curso") or curso.get("nombre") or codigo
        creditos = int(curso.get("creditos") or 0)
        docente = curso.get("docente", "") or ""
        curso_id = obtener_o_crear_curso_boleta(estudiante_id, codigo, nombre, creditos, docente)
        mapa_cursos[codigo] = curso_id
        if curso.get("codigo"):
            mapa_cursos[curso.get("codigo")] = curso_id

    for h in horarios:
        codigo = h.get("codigo_curso") or h.get("codigo") or ""
        curso_id = mapa_cursos.get(codigo) or mapa_cursos.get(h.get("codigo"))
        if not curso_id:
            curso_id = obtener_o_crear_curso_boleta(estudiante_id, codigo, h.get("nombre_curso") or codigo, 0, h.get("docente", ""))
            mapa_cursos[codigo] = curso_id
        registrar_horario_clase(
            estudiante_id=estudiante_id,
            curso_id=curso_id,
            codigo_curso=codigo,
            nombre_curso=h.get("nombre_curso") or codigo,
            tipo=h.get("tipo") or "Clase",
            docente=h.get("docente") or "",
            dia=h.get("dia") or "",
            hora_inicio=h.get("inicio") or h.get("hora_inicio") or "08:00",
            hora_fin=h.get("fin") or h.get("hora_fin") or "09:00",
            aula=h.get("aula") or "",
        )

    for n in notas:
        codigo = n.get("codigo_curso") or n.get("codigo") or ""
        curso_id = mapa_cursos.get(codigo)
        if not curso_id:
            curso_id = obtener_o_crear_curso_boleta(estudiante_id, codigo, n.get("nombre_curso") or codigo, 0, "")
            mapa_cursos[codigo] = curso_id
        guardar_nota_curso(
            estudiante_id=estudiante_id,
            curso_id=curso_id,
            ciclo=ciclo,
            codigo_curso=codigo,
            nombre_curso=n.get("nombre_curso") or codigo,
            tipo_evaluacion=n.get("tipo_evaluacion") or "Nota",
            nombre_evaluacion=n.get("nombre_evaluacion") or "Evaluación",
            nota=n.get("nota"),
            peso=n.get("peso"),
            observacion=n.get("observacion") or "",
            origen=n.get("origen") or "INTRALU",
        )

    return True, f"Se importaron {len(cursos)} cursos, {len(horarios)} horarios y {len(notas)} notas desde INTRALU."

def obtener_tabla_completa(tabla: str):
    permitidas = {"estudiantes", "usuarios", "diagnosticos", "cursos", "tareas", "planes_semanales", "coach_recomendaciones", "horarios_clase", "notas_curso"}
    if tabla not in permitidas:
        raise ValueError("Tabla no permitida.")
    with conectar() as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT * FROM {tabla} ORDER BY id DESC")
            columnas = [desc.name for desc in cur.description]
            filas = cur.fetchall()
    return columnas, filas
