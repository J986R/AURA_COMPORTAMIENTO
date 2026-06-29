import re
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pypdf import PdfReader


def limpiar_texto(valor: Any) -> str:
    return re.sub(r"\s+", " ", str(valor or "")).strip()


def _sin_tildes(texto: Any) -> str:
    return (
        str(texto or "")
        .upper()
        .replace("Á", "A")
        .replace("É", "E")
        .replace("Í", "I")
        .replace("Ó", "O")
        .replace("Ú", "U")
        .replace("Ñ", "N")
    )


def _leer_bytes(file: Any) -> bytes:
    if hasattr(file, "read"):
        data = file.read()
        try:
            file.seek(0)
        except Exception:
            pass
        return data
    if isinstance(file, (bytes, bytearray)):
        return bytes(file)
    return Path(str(file)).read_bytes()


def extraer_texto_pdf(file: Any) -> str:
    data = _leer_bytes(file)
    reader = PdfReader(BytesIO(data))
    textos = []
    for page in reader.pages:
        textos.append(page.extract_text() or "")
    return "\n".join(textos)


def normalizar_codigo(codigo: Any) -> str:
    texto = limpiar_texto(codigo).upper().replace("/", "-")
    m = re.search(r"\b([A-Z]{2}\d{3})\s*-?\s*([A-Z])\b", texto)
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    return texto


def _parse_float(valor: Any) -> Optional[float]:
    texto = str(valor or "").strip().replace(",", ".")
    m = re.search(r"-?\d{1,2}(?:\.\d+)?", texto)
    if not m:
        return None
    try:
        nota = float(m.group(0))
    except Exception:
        return None
    # En UNI normalmente la escala es 0 a 20. Se deja margen por si viene 20.0.
    if nota < 0 or nota > 20:
        return None
    return nota


def clasificar_evaluacion(nombre: Any) -> str:
    texto = _sin_tildes(nombre)
    if re.search(r"\b(MONOGRAFIA|MONOGRAFICO|TRABAJO\s+MONOGRAFICO)\b", texto):
        return "Monografía"
    if re.search(r"\b(PRACTICA|PRACTICAS|PC\s*\d*|P\s*C\s*\d+|PRACT)\b", texto):
        return "Práctica calificada"
    if re.search(r"\b(PARCIAL|EXAMEN\s+PARCIAL|EP\s*\d*|E\s*P\s*\d*)\b", texto):
        return "Examen parcial"
    if re.search(r"\b(FINAL|EXAMEN\s+FINAL|EF\s*\d*|E\s*F\s*\d*)\b", texto):
        return "Examen final"
    if re.search(r"\b(PROMEDIO|PROM|NOTA\s+FINAL|PF|PP)\b", texto):
        return "Promedio"
    if re.search(r"\b(TAREA|TA\s*\d*)\b", texto):
        return "Tarea"
    return "Nota"


def _es_nombre_evaluacion(texto: str) -> bool:
    t = _sin_tildes(texto)
    return bool(re.search(
        r"\b(PRACTICA|PC\s*\d*|MONOGRAFIA|PARCIAL|FINAL|EP\s*\d*|EF\s*\d*|PROMEDIO|NOTA\s+FINAL|TAREA|EXAMEN|CONTROL|LABORATORIO)\b",
        t,
    ))


def _extraer_ciclo(texto: str, ciclo_default: str = "") -> str:
    for patron in [r"CICLO\s*[:\-]?\s*(20\d{3})", r"PERIODO\s*[:\-]?\s*(20\d{3})", r"SEMESTRE\s*[:\-]?\s*(20\d{3})", r"\b(20\d{3})\b"]:
        m = re.search(patron, texto or "", flags=re.I)
        if m:
            return m.group(1)
    return ciclo_default or ""


def _limpiar_nombre_curso(nombre: str) -> str:
    nombre = limpiar_texto(nombre)
    nombre = re.sub(r"\b(N|O|E)\s+\d+\s+\d+\s*$", "", nombre).strip()
    nombre = re.sub(r"\b(CREDITOS?|CR[ÉE]DITOS?)\b.*$", "", nombre, flags=re.I).strip()
    return nombre.strip("-: ")


def _detectar_curso_en_linea(linea: str) -> Optional[Tuple[str, str]]:
    linea = limpiar_texto(linea)
    m = re.match(r"^([A-Z]{2}\d{3}\s*[-/]?\s*[A-Z])\s+(.+?)$", linea, flags=re.I)
    if not m:
        return None
    codigo = normalizar_codigo(m.group(1))
    resto = _limpiar_nombre_curso(m.group(2))
    # Evita tratar filas de nota como encabezado de curso.
    if _es_nombre_evaluacion(resto):
        return None
    if re.search(r"\d{1,2}(?:[\.,]\d+)?\s*$", resto):
        return None
    return codigo, resto or codigo


def _agregar_nota(notas: List[Dict[str, Any]], seen: set, ciclo: str, codigo: str, nombre_curso: str, nombre_eval: str, nota: Optional[float], peso: Optional[float] = None, obs: str = ""):
    codigo = normalizar_codigo(codigo)
    nombre_eval = limpiar_texto(nombre_eval).strip(":- ")
    nombre_curso = _limpiar_nombre_curso(nombre_curso) or codigo
    if not codigo or not nombre_eval or nota is None:
        return
    if not _es_nombre_evaluacion(nombre_eval):
        return
    key = (ciclo, codigo, _sin_tildes(nombre_eval), nota)
    if key in seen:
        return
    seen.add(key)
    notas.append({
        "ciclo": ciclo,
        "codigo_curso": codigo,
        "nombre_curso": nombre_curso,
        "tipo_evaluacion": clasificar_evaluacion(nombre_eval),
        "nombre_evaluacion": nombre_eval,
        "nota": nota,
        "peso": peso,
        "observacion": obs,
        "origen": "PDF reporte de notas",
    })


def parsear_reporte_notas_texto(texto: str, ciclo_default: str = "") -> Dict[str, Any]:
    texto = texto or ""
    ciclo = _extraer_ciclo(texto, ciclo_default)
    notas: List[Dict[str, Any]] = []
    seen = set()
    cursos_detectados: Dict[str, str] = {}
    curso_actual = ""
    nombre_actual = ""

    lineas = [limpiar_texto(x) for x in texto.splitlines() if limpiar_texto(x)]

    # 1) Lectura línea por línea. Funciona cuando el PDF conserva una fila por evaluación.
    for linea in lineas:
        curso_linea = _detectar_curso_en_linea(linea)
        if curso_linea:
            curso_actual, nombre_actual = curso_linea
            cursos_detectados[curso_actual] = nombre_actual
            continue

        # Fila con código + nombre/evaluación + nota. Ej.: GE122-U PRACTICA 2 14
        m = re.match(
            r"^([A-Z]{2}\d{3}\s*[-/]?\s*[A-Z])\s+(.+?)\s+(-?\d{1,2}(?:[\.,]\d+)?)\s*(?:/\s*20)?\s*$",
            linea,
            flags=re.I,
        )
        if m:
            codigo = normalizar_codigo(m.group(1))
            resto = limpiar_texto(m.group(2))
            nota = _parse_float(m.group(3))
            if _es_nombre_evaluacion(resto):
                nombre_curso = cursos_detectados.get(codigo, codigo)
                _agregar_nota(notas, seen, ciclo, codigo, nombre_curso, resto, nota)
            continue

        # Fila con evaluación + nota dentro de un curso actual. Ej.: Practica 2 14
        m = re.match(r"^(.+?)\s+(-?\d{1,2}(?:[\.,]\d+)?)\s*(?:/\s*20)?\s*$", linea, flags=re.I)
        if m and curso_actual:
            nombre_eval = limpiar_texto(m.group(1))
            nota = _parse_float(m.group(2))
            _agregar_nota(notas, seen, ciclo, curso_actual, nombre_actual or curso_actual, nombre_eval, nota)
            continue

        # Fila con evaluación: nota, peso u observación. Ej.: Practica 2 Nota 14 Peso 20%
        if curso_actual and _es_nombre_evaluacion(linea):
            m_nota = re.search(r"(?:NOTA|CALIFICACI[ÓO]N|PUNTAJE)\s*[:\-]?\s*(-?\d{1,2}(?:[\.,]\d+)?)", linea, flags=re.I)
            nota = _parse_float(m_nota.group(1)) if m_nota else None
            if nota is not None:
                nombre_eval = re.split(r"\b(?:NOTA|CALIFICACI[ÓO]N|PUNTAJE)\b", linea, flags=re.I)[0]
                _agregar_nota(notas, seen, ciclo, curso_actual, nombre_actual or curso_actual, nombre_eval, nota)

    # 2) Parser global para PDFs que juntan todo el reporte en una sola línea.
    texto_lineal = re.sub(r"\s+", " ", texto).strip()
    curso_pat = r"([A-Z]{2}\d{3}\s*[-/]?\s*[A-Z])"
    eval_pat = r"((?:PRACTICA|PRÁCTICA|PC|MONOGRAFIA|MONOGRAFÍA|PARCIAL|FINAL|EP|EF|PROMEDIO|NOTA FINAL|TAREA|EXAMEN|CONTROL|LABORATORIO)\s*\d*)"
    patron_global = re.compile(rf"{curso_pat}\s+(.{{0,70}}?)\s+{eval_pat}\s+(-?\d{{1,2}}(?:[\.,]\d+)?)", flags=re.I)
    for m in patron_global.finditer(texto_lineal):
        codigo = normalizar_codigo(m.group(1))
        nombre_posible = _limpiar_nombre_curso(m.group(2))
        nombre_curso = cursos_detectados.get(codigo) or (nombre_posible if not _es_nombre_evaluacion(nombre_posible) else codigo) or codigo
        _agregar_nota(notas, seen, ciclo, codigo, nombre_curso, m.group(3), _parse_float(m.group(4)))

    return {
        "ciclo": ciclo,
        "notas": notas,
        "total_notas": len(notas),
        "texto_preview": texto[:1500],
    }


def parsear_reporte_notas_pdf(file: Any, ciclo_default: str = "") -> Dict[str, Any]:
    texto = extraer_texto_pdf(file)
    return parsear_reporte_notas_texto(texto, ciclo_default=ciclo_default)
