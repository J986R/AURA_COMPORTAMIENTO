"""
Scraper seguro para INTRALU / alumnos.uni.edu.pe usado por AURA.

Flujo actualizado según la navegación real indicada por el usuario:
1) Cursos y horarios: INTRALU -> Curso matriculado -> Imprimir boleta.
2) Notas actuales: INTRALU -> Curso matriculado -> Imprimir notas.
3) Historial académico: INTRALU -> Fichas académicas -> Avance curricular.

Reglas de seguridad:
- La contraseña se usa solo en memoria durante la importación.
- No se guarda en Neon, no se devuelve y no se imprime en logs.
- No intenta evadir CAPTCHA, 2FA, bloqueos ni restricciones del portal.
"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from io import BytesIO, StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from bs4 import BeautifulSoup
from pypdf import PdfReader

try:
    from boleta_parser import parsear_boleta_matricula
except Exception:  # pragma: no cover
    parsear_boleta_matricula = None

BASE_URL = "https://alumnos.uni.edu.pe"
LOGIN_URL = BASE_URL + "/login"
CURSOS_URL = BASE_URL + "/informacion-academica/cursos/{ciclo}"
DETALLE_URL = BASE_URL + "/informacion-academica/cursos/{ciclo}/{codigo}/{seccion}"

# Posibles rutas. Se intentan solo como respaldo si el menú/botón no está visible.
AVANCE_URL_CANDIDATAS = [
    BASE_URL + "/informacion-academica/avance-curricular",
    BASE_URL + "/informacion-academica/fichas-academicas/avance-curricular",
    BASE_URL + "/fichas-academicas/avance-curricular",
    BASE_URL + "/informacion-academica/ficha-academica/avance-curricular",
]

DIAS_VALIDOS = {
    "LUNES": "Lunes",
    "MARTES": "Martes",
    "MIÉRCOLES": "Miércoles",
    "MIERCOLES": "Miércoles",
    "JUEVES": "Jueves",
    "VIERNES": "Viernes",
    "SÁBADO": "Sábado",
    "SABADO": "Sábado",
    "DOMINGO": "Domingo",
}

TIPOS_NOTA = {
    "EP": "Examen parcial",
    "PARCIAL": "Examen parcial",
    "EF": "Examen final",
    "FINAL": "Examen final",
    "PC": "Práctica calificada",
    "PRACTICA": "Práctica calificada",
    "PRÁCTICA": "Práctica calificada",
    "MONO": "Monografía",
    "MONOGRAFIA": "Monografía",
    "MONOGRAFÍA": "Monografía",
    "PROM": "Promedio",
    "PROMEDIO": "Promedio",
}


@dataclass
class IntraluResultado:
    estudiante: Dict[str, Any]
    cursos: List[Dict[str, Any]]
    horarios: List[Dict[str, Any]]
    notas: List[Dict[str, Any]]
    advertencias: List[str]
    documentos: Dict[str, str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "estudiante": self.estudiante,
            "cursos": self.cursos,
            "horarios": self.horarios,
            "notas": self.notas,
            "advertencias": self.advertencias,
            "documentos": self.documentos,
        }


def limpiar_texto(valor: Any) -> str:
    if valor is None:
        return ""
    texto = str(valor).replace("\xa0", " ")
    return re.sub(r"\s+", " ", texto).strip()


def normalizar_decimal(valor: Any) -> Optional[float]:
    texto = limpiar_texto(valor).replace(",", ".")
    if not texto or texto in {"-", "--", "NP", "S/N"}:
        return None
    m = re.search(r"-?\d+(?:\.\d+)?", texto)
    if not m:
        return None
    try:
        return float(m.group(0))
    except Exception:
        return None


def normalizar_entero(valor: Any, defecto: int = 0) -> int:
    numero = normalizar_decimal(valor)
    if numero is None:
        return defecto
    return int(numero)


def normalizar_hora(texto: Any) -> str:
    texto = limpiar_texto(texto)
    m = re.search(r"(\d{1,2})[:.](\d{2})", texto)
    if not m:
        return "08:00"
    h = max(0, min(23, int(m.group(1))))
    minuto = max(0, min(59, int(m.group(2))))
    return f"{h:02d}:{minuto:02d}"


def separar_codigo_seccion(codigo_compuesto: str) -> Tuple[str, str]:
    texto = limpiar_texto(codigo_compuesto).upper()
    m = re.search(r"\b([A-Z]{2}\d{3})\s*[-/]?\s*([A-Z])\b", texto)
    if m:
        return m.group(1), m.group(2)
    m = re.search(r"\b([A-Z]{2}\d{3})\b", texto)
    if m:
        return m.group(1), "U"
    return texto, "U"


def codigo_visible(codigo: str, seccion: str = "") -> str:
    codigo = limpiar_texto(codigo).upper()
    seccion = limpiar_texto(seccion).upper()
    if seccion and not codigo.endswith(f"-{seccion}"):
        return f"{codigo}-{seccion}"
    return codigo


def _leer_tablas_html(html: str) -> List[pd.DataFrame]:
    try:
        return pd.read_html(StringIO(html or ""))
    except Exception:
        return []


def _leer_tablas_texto_como_html(texto: str) -> List[pd.DataFrame]:
    # Para PDF extraído como texto no hay tablas HTML, pero dejamos esta función por compatibilidad.
    return []


def _columnas_norm(df: pd.DataFrame) -> Dict[str, str]:
    mapping = {}
    for col in df.columns:
        original = str(col)
        norm = limpiar_texto(original).lower()
        norm = norm.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
        mapping[norm] = original
    return mapping


def _col(mapping: Dict[str, str], *candidatas: str) -> Optional[str]:
    for cand in candidatas:
        c = cand.lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
        for norm, original in mapping.items():
            if c == norm or c in norm:
                return original
    return None


def bytes_a_texto_pdf(data: bytes) -> str:
    reader = PdfReader(BytesIO(data))
    textos = []
    for page in reader.pages:
        textos.append(page.extract_text() or "")
    return "\n".join(textos)


def html_a_texto(html: str) -> str:
    soup = BeautifulSoup(html or "", "html.parser")
    return soup.get_text("\n")


def normalizar_documento_texto(documento: Any) -> str:
    """Convierte PDF/HTML/texto a texto plano."""
    if documento is None:
        return ""
    if isinstance(documento, bytes):
        if documento[:4] == b"%PDF":
            return bytes_a_texto_pdf(documento)
        try:
            return documento.decode("utf-8", errors="ignore")
        except Exception:
            return ""
    if isinstance(documento, dict):
        if documento.get("tipo") == "pdf" and documento.get("data"):
            return bytes_a_texto_pdf(documento["data"])
        if documento.get("tipo") == "html":
            return html_a_texto(documento.get("html", ""))
        return limpiar_texto(documento.get("texto", ""))
    return str(documento)


def _texto_validacion(documento: Any) -> str:
    texto = normalizar_documento_texto(documento)
    texto = texto.upper()
    texto = texto.replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U")
    return re.sub(r"\s+", " ", texto).strip()


def es_boleta_matricula(documento: Any) -> bool:
    """Distingue una boleta real de la pantalla o documento de notas.

    Esto evita el error detectado por el usuario: que el bloque de notas
    sea interpretado como cursos. Solo aceptamos como cursos/horarios el
    documento de INTRALU generado por Curso matriculado -> Imprimir boleta.
    """
    texto = _texto_validacion(documento)
    if not texto:
        return False
    return (
        ("BOLETA" in texto and ("MATRICULA" in texto or "MATRÍCULA" in texto))
        or ("CICLO CURSO NOMBRE" in texto and ("CREDITOS" in texto or "CRÉDITOS" in texto) and "VECES" in texto)
        or ("CURSO TIPO DOCENTE" in texto and "AULA" in texto and "HORA" in texto)
    )


def es_documento_notas(documento: Any) -> bool:
    texto = _texto_validacion(documento)
    if not texto:
        return False
    claves = ["NOTA", "NOTAS", "PARCIAL", "FINAL", "PRACTICA", "PRÁCTICA", "MONOGRAFIA", "MONOGRAFÍA"]
    return any(c.replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U") in texto for c in claves)


def extraer_estudiante_desde_texto(texto: str) -> Dict[str, Any]:
    estudiante: Dict[str, Any] = {}
    limpio = limpiar_texto(texto)
    patrones = {
        "nombre": r"(?:ALUMNO|ESTUDIANTE)\s*:?\s*([A-ZÁÉÍÓÚÑ ]{5,}?)(?:\s+ESPECIALIDAD|\s+CÓDIGO|\s+CODIGO|$)",
        "codigo": r"(?:CÓDIGO|CODIGO|CODIGO UNI|CÓDIGO UNI)\s*:?\s*([0-9]{6,}[A-Z]?)",
        "carrera": r"(?:ESPECIALIDAD|CARRERA)\s*:?\s*([A-ZÁÉÍÓÚÑ ]{5,}?)(?:\s+FECHA|\s+CICLO|$)",
    }
    for key, patron in patrones.items():
        m = re.search(patron, limpio, flags=re.IGNORECASE)
        if m:
            estudiante[key] = limpiar_texto(m.group(1)).title() if key != "codigo" else limpiar_texto(m.group(1)).upper()
    return estudiante


def extraer_cursos_y_horarios(html_o_texto: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[str]]:
    """Extrae cursos y horarios desde boleta o página general.

    Soporta:
    - Tablas HTML.
    - Texto plano de la boleta de matrícula emitida por INTRALU.
    """
    advertencias: List[str] = []
    cursos: Dict[str, Dict[str, Any]] = {}
    horarios: List[Dict[str, Any]] = []

    tablas = _leer_tablas_html(html_o_texto)
    for df in tablas:
        if df.empty:
            continue
        mapping = _columnas_norm(df)
        col_curso = _col(mapping, "curso", "codigo", "código")
        col_nombre = _col(mapping, "nombre", "asignatura")
        col_docente = _col(mapping, "docente", "profesor")
        col_creditos = _col(mapping, "creditos", "créditos")
        col_dia = _col(mapping, "dia", "día")
        col_hora = _col(mapping, "hora", "horario")
        col_inicio = _col(mapping, "inicio", "hora inicio")
        col_fin = _col(mapping, "fin", "hora fin")
        col_aula = _col(mapping, "aula")
        col_tipo = _col(mapping, "tipo")

        if col_curso and (col_nombre or col_creditos) and not col_dia:
            for _, row in df.iterrows():
                cod_raw = limpiar_texto(row.get(col_curso, ""))
                codigo, seccion = separar_codigo_seccion(cod_raw)
                if not re.search(r"[A-Z]{2}\d{3}", codigo):
                    continue
                visible = codigo_visible(codigo, seccion)
                cursos[visible] = {
                    "codigo_curso": visible,
                    "codigo": codigo,
                    "seccion": seccion,
                    "nombre_curso": limpiar_texto(row.get(col_nombre, "")) if col_nombre else visible,
                    "creditos": normalizar_entero(row.get(col_creditos, 0), 0) if col_creditos else 0,
                    "docente": limpiar_texto(row.get(col_docente, "")) if col_docente else "",
                }

        if col_curso and col_dia and (col_hora or col_inicio):
            for _, row in df.iterrows():
                cod_raw = limpiar_texto(row.get(col_curso, ""))
                codigo, seccion = separar_codigo_seccion(cod_raw)
                visible = codigo_visible(codigo, seccion)
                dia_raw = limpiar_texto(row.get(col_dia, "")).upper()
                dia = DIAS_VALIDOS.get(dia_raw, limpiar_texto(row.get(col_dia, "")).title())
                if not visible or not dia:
                    continue
                if col_inicio and col_fin:
                    inicio = normalizar_hora(row.get(col_inicio, ""))
                    fin = normalizar_hora(row.get(col_fin, ""))
                else:
                    hora_txt = limpiar_texto(row.get(col_hora, "")) if col_hora else ""
                    horas = re.findall(r"\d{1,2}[:.]\d{2}", hora_txt)
                    inicio = normalizar_hora(horas[0] if horas else "08:00")
                    fin = normalizar_hora(horas[1] if len(horas) > 1 else "09:00")
                nombre = limpiar_texto(row.get(col_nombre, "")) if col_nombre else visible
                docente = limpiar_texto(row.get(col_docente, "")) if col_docente else ""
                if visible not in cursos:
                    cursos[visible] = {
                        "codigo_curso": visible,
                        "codigo": codigo,
                        "seccion": seccion,
                        "nombre_curso": nombre or visible,
                        "creditos": 0,
                        "docente": docente,
                    }
                horarios.append({
                    "codigo_curso": visible,
                    "codigo": codigo,
                    "seccion": seccion,
                    "nombre_curso": nombre or cursos[visible].get("nombre_curso") or visible,
                    "tipo": limpiar_texto(row.get(col_tipo, "Clase")) if col_tipo else "Clase",
                    "docente": docente,
                    "dia": dia,
                    "inicio": inicio,
                    "fin": fin,
                    "aula": limpiar_texto(row.get(col_aula, "")) if col_aula else "",
                })

    # Fallback por texto plano.
    if "<" in html_o_texto and ">" in html_o_texto:
        texto = html_a_texto(html_o_texto)
    else:
        texto = html_o_texto
    lineas = [limpiar_texto(x) for x in texto.splitlines() if limpiar_texto(x)]

    for linea in lineas:
        # Curso listado: 12 GE122-U SISTEMA DE COSTOS- N 3 0
        m = re.match(r"^(\d{1,2})\s+([A-Z]{2}\d{3}[-/]?[A-Z])\s+(.+?)\s+[A-Z]\s+(\d+)\s+\d+\s*$", linea, flags=re.I)
        if m:
            cod, sec = separar_codigo_seccion(m.group(2))
            visible = codigo_visible(cod, sec)
            cursos.setdefault(visible, {
                "codigo_curso": visible,
                "codigo": cod,
                "seccion": sec,
                "nombre_curso": limpiar_texto(m.group(3)).strip("-"),
                "creditos": int(m.group(4)),
                "docente": "",
            })
            continue

        # Horario: GE122-U PRACTICA VICTOR ... VIERNES 20:00 a 22:00 S4-202
        m = re.match(
            r"^([A-Z]{2}\d{3}[-/]?[A-Z])\s+(TEORIA|TEORÍA|PRACTICA|PRÁCTICA|LABORATORIO|CLASE)\s+(.+?)\s+"
            r"(LUNES|MARTES|MI[ÉE]RCOLES|JUEVES|VIERNES|S[ÁA]BADO|DOMINGO)\s+"
            r"(\d{1,2}:\d{2})\s*(?:a|-|–)\s*(\d{1,2}:\d{2})\s*(.*)$",
            linea,
            flags=re.I,
        )
        if m:
            cod, sec = separar_codigo_seccion(m.group(1))
            visible = codigo_visible(cod, sec)
            dia = DIAS_VALIDOS.get(limpiar_texto(m.group(4)).upper(), limpiar_texto(m.group(4)).title())
            docente = limpiar_texto(m.group(3)).title()
            cursos.setdefault(visible, {
                "codigo_curso": visible,
                "codigo": cod,
                "seccion": sec,
                "nombre_curso": visible,
                "creditos": 0,
                "docente": docente,
            })
            horarios.append({
                "codigo_curso": visible,
                "codigo": cod,
                "seccion": sec,
                "nombre_curso": cursos[visible].get("nombre_curso") or visible,
                "tipo": limpiar_texto(m.group(2)).title(),
                "docente": docente,
                "dia": dia,
                "inicio": normalizar_hora(m.group(5)),
                "fin": normalizar_hora(m.group(6)),
                "aula": limpiar_texto(m.group(7)),
            })

    if not cursos:
        advertencias.append("No se detectaron cursos. Se intentará usar otras fuentes de INTRALU si están disponibles.")
    if not horarios:
        advertencias.append("No se detectaron horarios desde boleta/página. Puedes ingresarlos manualmente o importar PDF.")

    return list(cursos.values()), horarios, advertencias


def _sin_tildes(texto: str) -> str:
    return (texto or "").upper().replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U")


def _nombre_columna(col: Any) -> str:
    if isinstance(col, tuple):
        partes = [limpiar_texto(x) for x in col if limpiar_texto(x) and not str(x).startswith("Unnamed")]
        return limpiar_texto(" ".join(partes))
    return limpiar_texto(col)


def inferir_tipo_evaluacion(nombre: str) -> str:
    t = _sin_tildes(limpiar_texto(nombre))

    # Relación pedida: "Práctica 2" debe ser Práctica calificada,
    # "Monografía 2" debe ser Monografía. Parcial y Final ya se mantienen.
    if re.search(r"\b(EXAMEN\s+FINAL|FINAL|EF)\b", t):
        return "Examen final"
    if re.search(r"\b(EXAMEN\s+PARCIAL|PARCIAL|EP)\b", t):
        return "Examen parcial"
    if re.search(r"\b(PRACTICA(?:\s+CALIFICADA)?\s*\d*|PC\s*\d+|PR\s*\d+)\b", t):
        return "Práctica calificada"
    if re.search(r"\b(MONOGRAFIA\s*\d*|MONO\s*\d*)\b", t):
        return "Monografía"
    if re.search(r"\b(PROMEDIO|PROM|NOTA\s+FINAL|NOTA)\b", t):
        return "Promedio"

    for token, tipo in TIPOS_NOTA.items():
        if _sin_tildes(token) in t:
            return tipo
    return "Nota"


def normalizar_nombre_evaluacion(nombre: Any) -> str:
    n = limpiar_texto(_nombre_columna(nombre))
    n = re.sub(r"\bUnnamed:\s*\d+\b", "", n, flags=re.I).strip(" -:_")
    if not n:
        return "Evaluación"
    # Hacer más legibles etiquetas frecuentes sin perder el número.
    repl = {
        "PRACTICA": "Práctica",
        "PRACTICA CALIFICADA": "Práctica calificada",
        "MONOGRAFIA": "Monografía",
        "EXAMEN PARCIAL": "Examen parcial",
        "EXAMEN FINAL": "Examen final",
    }
    up = _sin_tildes(n)
    for a, b in repl.items():
        if up.startswith(a):
            return re.sub(a, b, up, count=1, flags=re.I).capitalize() if up == a else b + n[len(a):]
    return n


def es_columna_evaluacion(col: Any) -> bool:
    n = _sin_tildes(_nombre_columna(col))
    if not n or n in {"NAN", "NONE"}:
        return False
    # No confundir campos administrativos con evaluaciones.
    if any(x in n for x in ["CODIGO", "CURSO", "ASIGNATURA", "NOMBRE", "DOCENTE", "CREDITO", "CICLO", "VEZ", "AULA", "DIA", "HORA"]):
        return False
    return bool(re.search(
        r"\b(PRACTICA(?:\s+CALIFICADA)?\s*\d*|PC\s*\d+|PR\s*\d+|MONOGRAFIA\s*\d*|MONO\s*\d*|EP|EF|PARCIAL|FINAL|PROMEDIO|PROM|NOTA)\b",
        n,
    ))


def extraer_notas_de_tablas_html(html: str, ciclo_hint: str = "", origen: str = "INTRALU") -> List[Dict[str, Any]]:
    """Extrae notas desde tablas HTML en formato largo o ancho.

    Corrección clave:
    - Antes se leía casi siempre solo la columna "Nota".
    - Ahora se leen todas las columnas de evaluación: Práctica 1/2, Monografía 1/2,
      Parcial, Final, Promedio/Nota, etc.
    """
    notas: List[Dict[str, Any]] = []
    tablas = _leer_tablas_html(html)
    curso_actual = ""
    nombre_actual = ""

    for idx_tabla, df in enumerate(tablas):
        if df.empty:
            continue

        # Limpiar columnas multiíndice o Unnamed.
        df = df.copy()
        df.columns = [_nombre_columna(c) for c in df.columns]
        mapping = _columnas_norm(df)

        col_codigo = _col(mapping, "codigo", "código", "cod", "curso")
        col_curso = _col(mapping, "asignatura", "nombre curso", "nombre", "curso")
        col_ciclo = _col(mapping, "ciclo", "periodo", "período", "semestre")
        col_eval = _col(mapping, "evaluacion", "evaluación", "descripcion", "descripción", "concepto", "tipo")
        col_nota = _col(mapping, "nota", "calificacion", "calificación", "puntaje")
        col_peso = _col(mapping, "peso", "porcentaje", "%")
        col_obs = _col(mapping, "observacion", "observación", "estado")

        campos_base = {x for x in [col_codigo, col_curso, col_ciclo, col_peso, col_obs] if x}

        # 1) FORMATO ANCHO: una fila por curso y varias columnas de evaluaciones.
        # Ej: Curso | Práctica 1 | Práctica 2 | Monografía 2 | Parcial | Final | Nota
        columnas_eval = []
        for col in df.columns:
            if col in campos_base:
                continue
            if es_columna_evaluacion(col):
                columnas_eval.append(col)

        if columnas_eval:
            for _, row in df.iterrows():
                cod_raw = limpiar_texto(row.get(col_codigo, "")) if col_codigo else ""
                codigo, seccion = separar_codigo_seccion(cod_raw) if cod_raw else ("", "")
                codigo_final = codigo_visible(codigo, seccion) if codigo else curso_actual
                if codigo_final:
                    curso_actual = codigo_final

                nombre = limpiar_texto(row.get(col_curso, "")) if col_curso else nombre_actual
                # Evitar que el nombre sea igual a una etiqueta de evaluación.
                if nombre and not es_columna_evaluacion(nombre) and not re.fullmatch(r"[A-Z]{2}\d{3}[-/]?[A-Z]?", nombre, flags=re.I):
                    nombre_actual = nombre

                ciclo_fila = limpiar_texto(row.get(col_ciclo, "")) if col_ciclo else ciclo_hint

                for col_eval_ancha in columnas_eval:
                    nota = normalizar_decimal(row.get(col_eval_ancha, None))
                    if nota is None or nota < 0 or nota > 20:
                        continue
                    evaluacion = normalizar_nombre_evaluacion(col_eval_ancha)
                    notas.append({
                        "ciclo": ciclo_fila or ciclo_hint,
                        "codigo_curso": codigo_final or "SIN-CODIGO",
                        "nombre_curso": nombre_actual or codigo_final or "Curso",
                        "tipo_evaluacion": inferir_tipo_evaluacion(evaluacion),
                        "nombre_evaluacion": evaluacion,
                        "nota": nota,
                        "peso": None,
                        "observacion": limpiar_texto(row.get(col_obs, "")) if col_obs else "",
                        "origen": f"{origen}:tabla_{idx_tabla + 1}",
                    })

        # 2) FORMATO LARGO: una fila por evaluación.
        # Ej: Curso | Evaluación | Nota.
        if col_nota and col_eval:
            for i, row in df.iterrows():
                nota = normalizar_decimal(row.get(col_nota, None))
                if nota is None or nota < 0 or nota > 20:
                    continue
                cod_raw = limpiar_texto(row.get(col_codigo, "")) if col_codigo else ""
                codigo, seccion = separar_codigo_seccion(cod_raw) if cod_raw else ("", "")
                codigo_final = codigo_visible(codigo, seccion) if codigo else curso_actual
                if codigo_final:
                    curso_actual = codigo_final
                nombre = limpiar_texto(row.get(col_curso, "")) if col_curso else nombre_actual
                if nombre and not es_columna_evaluacion(nombre) and not re.fullmatch(r"[A-Z]{2}\d{3}[-/]?[A-Z]?", nombre, flags=re.I):
                    nombre_actual = nombre
                evaluacion = limpiar_texto(row.get(col_eval, "")) or f"Evaluación {i + 1}"
                notas.append({
                    "ciclo": limpiar_texto(row.get(col_ciclo, "")) if col_ciclo else ciclo_hint,
                    "codigo_curso": codigo_final or "SIN-CODIGO",
                    "nombre_curso": nombre_actual or codigo_final or "Curso",
                    "tipo_evaluacion": inferir_tipo_evaluacion(evaluacion),
                    "nombre_evaluacion": evaluacion,
                    "nota": nota,
                    "peso": normalizar_decimal(row.get(col_peso, None)) if col_peso else None,
                    "observacion": limpiar_texto(row.get(col_obs, "")) if col_obs else "",
                    "origen": f"{origen}:tabla_{idx_tabla + 1}",
                })

    return _deduplicar_notas(notas)

def extraer_notas_desde_texto(texto: str, ciclo_hint: str = "", origen: str = "INTRALU") -> List[Dict[str, Any]]:
    """Extractor para PDF/texto de notas actuales y avance curricular.

    Lee todas las evaluaciones disponibles, no solo la columna "Nota".
    Reconoce explícitamente: Práctica 1/2, Monografía 1/2, Parcial, Final y Promedio/Nota.
    """
    notas: List[Dict[str, Any]] = []
    lineas = [limpiar_texto(x) for x in texto.splitlines() if limpiar_texto(x)]
    curso_actual = ""
    nombre_actual = ""
    ciclo_actual = ciclo_hint
    encabezado_evaluaciones: List[str] = []

    patron_eval = (
        r"PRACTICA(?:\s+CALIFICADA)?\s*\d*|PRÁCTICA(?:\s+CALIFICADA)?\s*\d*|"
        r"PC\s*\d+|PR\s*\d+|"
        r"MONOGRAFIA\s*\d*|MONOGRAFÍA\s*\d*|MONO\s*\d*|"
        r"EXAMEN\s+PARCIAL|PARCIAL|EP|"
        r"EXAMEN\s+FINAL|FINAL|EF|"
        r"PROMEDIO|PROM|NOTA\s+FINAL|NOTA"
    )

    for linea in lineas:
        linea_sin = _sin_tildes(linea)

        # Detectar ciclo en avance curricular, ej. 20231, 2024-1, PERIODO 20251.
        m_ciclo = re.search(r"\b(20\d{2}[- ]?[12]|20\d{3})\b", linea)
        if m_ciclo:
            ciclo_actual = m_ciclo.group(1).replace(" ", "")

        # Si una línea parece encabezado de evaluaciones, la guardamos para mapear filas anchas.
        posibles_encabezados = [normalizar_nombre_evaluacion(x) for x in re.findall(patron_eval, linea, flags=re.I)]
        if posibles_encabezados and not re.search(r"\b[A-Z]{2}\d{3}", linea, flags=re.I):
            encabezado_evaluaciones = posibles_encabezados

        m_curso = re.search(r"\b([A-Z]{2}\d{3})(?:[-/]?([A-Z]))?\b", linea, flags=re.I)
        if m_curso:
            codigo = m_curso.group(1).upper()
            seccion = (m_curso.group(2) or "").upper()
            curso_actual = codigo_visible(codigo, seccion) if seccion else codigo
            # Nombre entre código y la primera evaluación detectada.
            resto = linea[m_curso.end():]
            resto = re.sub(rf"\b({patron_eval})\b.*$", "", resto, flags=re.I)
            nombre_actual = limpiar_texto(resto).strip("-:") or nombre_actual or curso_actual

        # 1) Pares explícitos en la misma línea: "Práctica 2 15", "Monografía 2: 17", "EP 12".
        pares = re.findall(rf"\b({patron_eval})\b\s*[:=]?\s*(\d{{1,2}}(?:[.,]\d+)?)\b", linea, flags=re.I)
        for nombre_eval, nota_txt in pares:
            nota = normalizar_decimal(nota_txt)
            if nota is not None and 0 <= nota <= 20:
                evaluacion = normalizar_nombre_evaluacion(nombre_eval)
                notas.append({
                    "ciclo": ciclo_actual,
                    "codigo_curso": curso_actual or "SIN-CODIGO",
                    "nombre_curso": nombre_actual or curso_actual or "Curso",
                    "tipo_evaluacion": inferir_tipo_evaluacion(evaluacion),
                    "nombre_evaluacion": evaluacion,
                    "nota": nota,
                    "peso": None,
                    "observacion": "",
                    "origen": origen,
                })

        # 2) Fila ancha con encabezado previo: curso + números, ej.
        # Encabezado: Práctica 1 Práctica 2 Monografía 2 Parcial Final Nota
        # Fila: GE122 Sistema de Costos 13 15 16 12 14 14
        if m_curso and encabezado_evaluaciones and not pares:
            nums = [normalizar_decimal(x) for x in re.findall(r"\b\d{1,2}(?:[.,]\d+)?\b", linea[m_curso.end():])]
            validos = [x for x in nums if x is not None and 0 <= x <= 20]
            if len(validos) >= len(encabezado_evaluaciones):
                valores = validos[-len(encabezado_evaluaciones):]
                for evaluacion, nota in zip(encabezado_evaluaciones, valores):
                    notas.append({
                        "ciclo": ciclo_actual,
                        "codigo_curso": curso_actual or "SIN-CODIGO",
                        "nombre_curso": nombre_actual or curso_actual or "Curso",
                        "tipo_evaluacion": inferir_tipo_evaluacion(evaluacion),
                        "nombre_evaluacion": evaluacion,
                        "nota": nota,
                        "peso": None,
                        "observacion": "",
                        "origen": origen,
                    })

        # 3) Avance curricular/histórico: si no hay pares ni encabezado, guardar última nota como promedio final.
        if m_curso and not pares and not encabezado_evaluaciones:
            nums = [normalizar_decimal(x) for x in re.findall(r"\b\d{1,2}(?:[.,]\d+)?\b", linea)]
            validos = [x for x in nums if x is not None and 0 <= x <= 20]
            if validos:
                nota = validos[-1]
                notas.append({
                    "ciclo": ciclo_actual,
                    "codigo_curso": curso_actual or "SIN-CODIGO",
                    "nombre_curso": nombre_actual or curso_actual or "Curso",
                    "tipo_evaluacion": "Promedio",
                    "nombre_evaluacion": "Nota final / avance curricular",
                    "nota": nota,
                    "peso": None,
                    "observacion": "Detectado desde avance curricular" if "avance" in origen.lower() else "",
                    "origen": origen,
                })

    return _deduplicar_notas(notas)

def extraer_notas_documento(documento: Dict[str, Any], ciclo_hint: str, origen: str) -> List[Dict[str, Any]]:
    if not documento:
        return []
    if documento.get("tipo") == "html":
        html = documento.get("html", "")
        notas = extraer_notas_de_tablas_html(html, ciclo_hint, origen)
        if notas:
            return notas
        return extraer_notas_desde_texto(html_a_texto(html), ciclo_hint, origen)
    texto = normalizar_documento_texto(documento)
    return extraer_notas_desde_texto(texto, ciclo_hint, origen)


def _rellenar_login(page, codigo_uni: str, password: str) -> None:
    candidatos_usuario = [
        "input[name='codigo']", "input[name='username']", "input[name='user']", "input[name='usuario']",
        "input[id*='codigo' i]", "input[id*='user' i]", "input[placeholder*='Código' i]",
        "input[placeholder*='codigo' i]", "input[placeholder*='usuario' i]", "input[type='text']",
    ]
    filled_user = False
    for selector in candidatos_usuario:
        try:
            loc = page.locator(selector).first
            if loc.count() > 0 and loc.is_visible(timeout=800):
                loc.fill(codigo_uni)
                filled_user = True
                break
        except Exception:
            continue

    try:
        page.locator("input[type='password']").first.fill(password)
    except Exception as exc:
        raise RuntimeError("No se encontró el campo de contraseña en INTRALU.") from exc

    if not filled_user:
        raise RuntimeError("No se encontró el campo de código/usuario en INTRALU.")

    candidatos_boton = [
        "button[type='submit']", "input[type='submit']", "button:has-text('Ingresar')", "button:has-text('Entrar')",
        "button:has-text('Iniciar')", "button:has-text('Login')",
    ]
    clicked = False
    for selector in candidatos_boton:
        try:
            loc = page.locator(selector).first
            if loc.count() > 0 and loc.is_visible(timeout=800):
                loc.click()
                clicked = True
                break
        except Exception:
            continue
    if not clicked:
        page.locator("input[type='password']").first.press("Enter")


def _asegurar_login(page, codigo_uni: str, password: str, timeout_ms: int) -> None:
    page.goto(CURSOS_URL.format(ciclo="20261"), wait_until="domcontentloaded")
    time.sleep(0.8)
    if page.locator("input[type='password']").count() > 0:
        _rellenar_login(page, codigo_uni, password)
        try:
            page.wait_for_load_state("networkidle", timeout=timeout_ms)
        except Exception:
            pass
    if page.locator("input[type='password']").count() > 0:
        raise RuntimeError("No se pudo iniciar sesión. Verifica código, contraseña o si INTRALU pide un paso adicional.")


def _click_texto(page, textos: List[str], timeout: int = 4000):
    """Devuelve el primer locator visible por texto aproximado."""
    selectores = []
    for texto in textos:
        escaped = texto.replace("'", "\\'")
        selectores.extend([
            f"a:has-text('{escaped}')",
            f"button:has-text('{escaped}')",
            f"[role='button']:has-text('{escaped}')",
            f"text={texto}",
        ])
    for selector in selectores:
        try:
            loc = page.locator(selector).first
            if loc.count() > 0 and loc.is_visible(timeout=timeout):
                return loc
        except Exception:
            continue
    return None


def _ir_cursos_matriculados(page, ciclo: str, timeout_ms: int) -> None:
    page.goto(CURSOS_URL.format(ciclo=ciclo), wait_until="domcontentloaded")
    try:
        page.wait_for_load_state("networkidle", timeout=timeout_ms)
    except Exception:
        pass
    if "login" not in page.url.lower() and page.locator("input[type='password']").count() == 0:
        return

    # Respaldo por navegación visual.
    page.goto(BASE_URL, wait_until="domcontentloaded")
    try:
        page.wait_for_load_state("networkidle", timeout=timeout_ms)
    except Exception:
        pass
    loc = _click_texto(page, ["Curso matriculado", "Cursos matriculados", "Cursos", "Información Académica"])
    if loc:
        loc.click()
        try:
            page.wait_for_load_state("networkidle", timeout=timeout_ms)
        except Exception:
            pass


def _capturar_documento_click(page, textos_boton: List[str], nombre: str, timeout_ms: int = 25000) -> Optional[Dict[str, Any]]:
    """Clic en botón/link y captura PDF descargado, pestaña emergente o HTML actual.

    Devuelve {tipo: 'pdf', data: bytes} o {tipo: 'html', html: str}.
    """
    loc = _click_texto(page, textos_boton, timeout=5000)
    if loc is None:
        return None

    before_pages = list(page.context.pages)
    try:
        with page.expect_download(timeout=9000) as download_info:
            loc.click()
        download = download_info.value
        path = download.path()
        data = Path(path).read_bytes() if path else b""
        if data:
            return {"tipo": "pdf" if data[:4] == b"%PDF" else "binario", "data": data, "nombre": download.suggested_filename or nombre}
    except Exception:
        pass

    # Si el clic abrió una pestaña/popup.
    try:
        after_pages = list(page.context.pages)
        nuevas = [p for p in after_pages if p not in before_pages]
        if nuevas:
            popup = nuevas[-1]
            try:
                popup.wait_for_load_state("networkidle", timeout=timeout_ms)
            except Exception:
                pass
            html = popup.content()
            try:
                popup.close()
            except Exception:
                pass
            return {"tipo": "html", "html": html, "nombre": nombre}
    except Exception:
        pass

    # El clic puede haber reemplazado la página actual.
    try:
        page.wait_for_load_state("networkidle", timeout=timeout_ms)
    except Exception:
        pass
    html = page.content()
    if html:
        return {"tipo": "html", "html": html, "nombre": nombre}
    return None


def _capturar_boleta(page, ciclo: str, timeout_ms: int) -> Optional[Dict[str, Any]]:
    _ir_cursos_matriculados(page, ciclo, timeout_ms)
    return _capturar_documento_click(
        page,
        ["Imprimir Boleta", "Boleta de Matricula", "Boleta de Matrícula", "Boleta", "Imprimir matrícula", "Imprimir matricula"],
        "boleta_matricula",
        timeout_ms,
    )


def _capturar_notas_actuales(page, ciclo: str, timeout_ms: int) -> Optional[Dict[str, Any]]:
    _ir_cursos_matriculados(page, ciclo, timeout_ms)
    return _capturar_documento_click(
        page,
        ["Imprimir Notas", "Notas actuales", "Notas", "Imprimir notas"],
        "notas_actuales",
        timeout_ms,
    )


def _ir_avance_curricular(page, timeout_ms: int) -> bool:
    # Intento visual por menú.
    page.goto(BASE_URL, wait_until="domcontentloaded")
    try:
        page.wait_for_load_state("networkidle", timeout=timeout_ms)
    except Exception:
        pass
    loc = _click_texto(page, ["Fichas académicas", "Fichas Academicas", "Ficha académica", "Ficha Academica"])
    if loc:
        try:
            loc.click()
            time.sleep(0.5)
        except Exception:
            pass
    loc2 = _click_texto(page, ["Avance curricular", "Avance Curricular", "Curricular"])
    if loc2:
        try:
            loc2.click()
            try:
                page.wait_for_load_state("networkidle", timeout=timeout_ms)
            except Exception:
                pass
            if page.locator("input[type='password']").count() == 0:
                return True
        except Exception:
            pass

    # Respaldo por rutas posibles.
    for url in AVANCE_URL_CANDIDATAS:
        try:
            page.goto(url, wait_until="domcontentloaded")
            try:
                page.wait_for_load_state("networkidle", timeout=timeout_ms)
            except Exception:
                pass
            texto = html_a_texto(page.content()).lower()
            if "avance" in texto or "curricular" in texto or "aprob" in texto:
                return True
        except Exception:
            continue
    return False


def _capturar_avance_curricular(page, timeout_ms: int) -> Optional[Dict[str, Any]]:
    if not _ir_avance_curricular(page, timeout_ms):
        return None
    doc = _capturar_documento_click(page, ["Imprimir", "Descargar", "PDF", "Avance"], "avance_curricular", timeout_ms)
    if doc:
        return doc
    return {"tipo": "html", "html": page.content(), "nombre": "avance_curricular"}


def _extraer_boleta_documento(documento: Optional[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any], List[str]]:
    if not documento:
        return [], [], {}, ["No se pudo abrir Imprimir boleta desde INTRALU."]

    # Validación estricta: si el documento capturado es de notas, NO lo usamos como cursos.
    if not es_boleta_matricula(documento):
        if es_documento_notas(documento):
            return [], [], {}, [
                "El documento capturado en 'Imprimir boleta' parece ser de notas, no una boleta de matrícula. "
                "No se cargó como cursos para evitar mezclar notas con cursos."
            ]
        return [], [], {}, [
            "El documento capturado no tiene estructura de boleta de matrícula. "
            "AURA solo cargará cursos/horarios desde Curso matriculado → Imprimir boleta."
        ]

    try:
        if documento.get("tipo") == "pdf" and parsear_boleta_matricula:
            datos = parsear_boleta_matricula(documento.get("data") or b"")
            estudiante = {
                "nombre": datos.get("alumno", ""),
                "codigo": datos.get("codigo_alumno", ""),
                "carrera": datos.get("especialidad", ""),
            }
            return datos.get("cursos", []) or [], datos.get("horarios", []) or [], estudiante, []
    except Exception:
        # Si falla el parser especializado, usamos texto genérico.
        pass
    texto = normalizar_documento_texto(documento)
    cursos, horarios, adv = extraer_cursos_y_horarios(texto)
    estudiante = extraer_estudiante_desde_texto(texto)
    return cursos, horarios, estudiante, adv


def _extraer_notas_por_detalle(page, cursos: List[Dict[str, Any]], ciclo: str, timeout_ms: int) -> Tuple[List[Dict[str, Any]], List[str]]:
    notas: List[Dict[str, Any]] = []
    advertencias: List[str] = []
    for curso in cursos:
        cod_base = curso.get("codigo") or separar_codigo_seccion(curso.get("codigo_curso", ""))[0]
        seccion = curso.get("seccion") or separar_codigo_seccion(curso.get("codigo_curso", ""))[1]
        if not cod_base:
            continue
        url = DETALLE_URL.format(ciclo=ciclo, codigo=cod_base, seccion=seccion or "U")
        try:
            page.goto(url, wait_until="domcontentloaded")
            try:
                page.wait_for_load_state("networkidle", timeout=timeout_ms)
            except Exception:
                pass
            html = page.content()
            codigo_curso = curso.get("codigo_curso") or codigo_visible(cod_base, seccion)
            notas_curso = extraer_notas_de_tablas_html(html, ciclo, f"INTRALU detalle {codigo_curso}")
            if not notas_curso:
                notas_curso = extraer_notas_desde_texto(html_a_texto(html), ciclo, f"INTRALU detalle {codigo_curso}")
            # Completar curso/nombre si el parser no lo detectó.
            for n in notas_curso:
                if n.get("codigo_curso") in {"", "SIN-CODIGO"}:
                    n["codigo_curso"] = codigo_curso
                if not n.get("nombre_curso") or n.get("nombre_curso") == "Curso":
                    n["nombre_curso"] = curso.get("nombre_curso") or codigo_curso
            notas.extend(notas_curso)
        except Exception as exc:
            advertencias.append(f"No se pudieron leer notas del detalle de {curso.get('codigo_curso')}: {exc}")
    return notas, advertencias


def _deduplicar_cursos(cursos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    salida: Dict[str, Dict[str, Any]] = {}
    for c in cursos:
        codigo = c.get("codigo_curso") or c.get("codigo") or ""
        if not codigo:
            continue
        cod, sec = separar_codigo_seccion(codigo)
        visible = codigo_visible(cod, sec)
        item = dict(c)
        item["codigo_curso"] = visible
        item.setdefault("codigo", cod)
        item.setdefault("seccion", sec)
        previo = salida.get(visible, {})
        combinado = {**previo, **{k: v for k, v in item.items() if v not in (None, "", [])}}
        salida[visible] = combinado
    return list(salida.values())


def _deduplicar_notas(notas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    salida: Dict[Tuple[str, str, str, str, float], Dict[str, Any]] = {}
    for n in notas:
        try:
            nota_val = float(n.get("nota"))
        except Exception:
            continue
        if nota_val < 0 or nota_val > 20:
            continue
        key = (
            str(n.get("ciclo", "")),
            str(n.get("codigo_curso", "")),
            str(n.get("nombre_evaluacion", "")),
            str(n.get("tipo_evaluacion", "")),
            nota_val,
        )
        salida[key] = n
    return list(salida.values())


def importar_cursos_horarios_notas_intralu(codigo_uni: str, password: str, ciclo: str = "20261", timeout_ms: int = 60000) -> Dict[str, Any]:
    """Inicia sesión temporal en INTRALU e importa cursos, horarios y notas.

    Usa las rutas reales indicadas por el flujo de usuario:
    - Curso matriculado -> Imprimir boleta.
    - Curso matriculado -> Imprimir notas.
    - Fichas académicas -> Avance curricular.
    """
    if not codigo_uni or not password:
        raise ValueError("Debes ingresar código UNI y contraseña.")

    advertencias: List[str] = []
    documentos: Dict[str, str] = {}
    cursos: List[Dict[str, Any]] = []
    horarios: List[Dict[str, Any]] = []
    notas: List[Dict[str, Any]] = []
    estudiante: Dict[str, Any] = {"codigo": limpiar_texto(codigo_uni).upper()}

    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        raise RuntimeError(
            "Playwright no está instalado. Agrega 'playwright' a requirements.txt y ejecuta 'python -m playwright install chromium'."
        ) from exc

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        except Exception as exc:
            if "Executable doesn't exist" in str(exc) or "playwright install" in str(exc).lower():
                try:
                    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True, timeout=240)
                    browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
                except Exception as install_exc:
                    raise RuntimeError(
                        "Playwright está instalado, pero Chromium no pudo descargarse en el servidor. "
                        "Ejecuta: python -m playwright install chromium. En Streamlit Cloud usa packages.txt o la importación por PDF como respaldo."
                    ) from install_exc
            else:
                raise

        context = browser.new_context(ignore_https_errors=True, accept_downloads=True)
        page = context.new_page()
        page.set_default_timeout(timeout_ms)

        try:
            _asegurar_login(page, codigo_uni, password, timeout_ms)

            # 1) Boleta de matrícula desde Curso matriculado -> Imprimir boleta.
            doc_boleta = _capturar_boleta(page, ciclo, timeout_ms)
            if doc_boleta:
                documentos["boleta"] = doc_boleta.get("nombre", "boleta_matricula")
                # Si INTRALU devolvió por error una pantalla de notas, la aprovechamos como notas,
                # pero NO la mezclamos con cursos.
                if es_documento_notas(doc_boleta) and not es_boleta_matricula(doc_boleta):
                    notas.extend(extraer_notas_documento(doc_boleta, ciclo, "INTRALU documento capturado en boleta"))
            cursos_b, horarios_b, estudiante_b, adv_b = _extraer_boleta_documento(doc_boleta)
            cursos.extend(cursos_b)
            horarios.extend(horarios_b)
            estudiante.update({k: v for k, v in estudiante_b.items() if v})
            advertencias.extend(adv_b)

            # Respaldo si el botón imprimir boleta no fue capturado: leer la página general
            # SOLO si realmente parece boleta. Si parece notas, se procesa como notas.
            if not cursos:
                _ir_cursos_matriculados(page, ciclo, timeout_ms)
                html_cursos = page.content()
                estudiante.update(extraer_estudiante_desde_texto(html_a_texto(html_cursos)))
                doc_pantalla = {"tipo": "html", "html": html_cursos, "nombre": "pantalla_curso_matriculado"}
                if es_boleta_matricula(doc_pantalla):
                    cursos_html, horarios_html, adv_html = extraer_cursos_y_horarios(html_cursos)
                    cursos.extend(cursos_html)
                    horarios.extend(horarios_html)
                    advertencias.extend(adv_html)
                elif es_documento_notas(doc_pantalla):
                    notas.extend(extraer_notas_documento(doc_pantalla, ciclo, "INTRALU pantalla curso matriculado"))
                    advertencias.append("La pantalla de Curso matriculado parecía contener notas; no se cargó como cursos. Para cursos/horarios se requiere 'Imprimir boleta'.")
                else:
                    advertencias.append("No se cargaron cursos desde la pantalla general porque no tenía estructura de boleta de matrícula.")

            cursos = _deduplicar_cursos(cursos)

            # 2) Notas actuales desde Curso matriculado -> Imprimir notas.
            doc_notas = _capturar_notas_actuales(page, ciclo, timeout_ms)
            if doc_notas:
                documentos["notas_actuales"] = doc_notas.get("nombre", "notas_actuales")
                notas_actuales = extraer_notas_documento(doc_notas, ciclo, "INTRALU imprimir notas")
                notas.extend(notas_actuales)
            else:
                advertencias.append("No se encontró o no se pudo abrir 'Imprimir notas' en Curso matriculado.")

            # Respaldo: detalle por curso.
            if not notas and cursos:
                notas_detalle, adv_detalle = _extraer_notas_por_detalle(page, cursos, ciclo, timeout_ms)
                notas.extend(notas_detalle)
                advertencias.extend(adv_detalle)

            # 3) Historial completo desde Fichas académicas -> Avance curricular.
            doc_avance = _capturar_avance_curricular(page, timeout_ms)
            if doc_avance:
                documentos["avance_curricular"] = doc_avance.get("nombre", "avance_curricular")
                notas_hist = extraer_notas_documento(doc_avance, ciclo, "INTRALU avance curricular")
                notas.extend(notas_hist)
            else:
                advertencias.append("No se encontró 'Fichas académicas -> Avance curricular' o no se pudo capturar el documento.")

            notas = _deduplicar_notas(notas)

            if not cursos:
                advertencias.append("No se importaron cursos. Revisa si INTRALU cambió el botón 'Imprimir boleta'.")
            if not notas:
                advertencias.append("No se importaron notas. Revisa si INTRALU cambió 'Imprimir notas' o 'Avance curricular'.")

        finally:
            try:
                context.clear_cookies()
                context.close()
            finally:
                browser.close()

    return IntraluResultado(
        estudiante=estudiante,
        cursos=cursos,
        horarios=horarios,
        notas=notas,
        advertencias=advertencias,
        documentos=documentos,
    ).to_dict()
