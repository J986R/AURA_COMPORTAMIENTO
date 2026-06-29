import re
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pypdf import PdfReader


# ============================================================
# PARSER DE REPORTE DE NOTAS UNI
# Lee PDFs como: REPORTE DE NOTAS - 20261
# Estructura esperada por curso:
#   GE122U - SISTEMA DE COSTOS-
#   Evaluación Nota Letra Reclamo Letra Fecha Prueba Fecha Registro
#   PRACTICA 1 18 Dieciocho -- -- 24/04/2026 10/05/2026
#   MONOGRAFIA 2 00 Evaluación no rendida -- --
#   EXAMEN PARCIAL 18 Dieciocho -- -- 15/05/2026 27/05/2026
# ============================================================


def limpiar_texto(valor: Any) -> str:
    texto = str(valor or "").replace("\ufffe", " ").replace("\u00ad", "")
    return re.sub(r"\s+", " ", texto).strip()


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
    """Convierte GE122U, GE122-U o GE122/U a GE122-U."""
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
    if nota < 0 or nota > 20:
        return None
    return nota


def _extraer_ciclo(texto: str, ciclo_default: str = "") -> str:
    patrones = [
        r"REPORTE\s+DE\s+NOTAS\s*[-:]\s*(20\d{3})",
        r"CICLO\s*[:\-]?\s*(20\d{3})",
        r"PERIODO\s*[:\-]?\s*(20\d{3})",
        r"SEMESTRE\s*[:\-]?\s*(20\d{3})",
        r"\b(20\d{3})\b",
    ]
    for patron in patrones:
        m = re.search(patron, texto or "", flags=re.I)
        if m:
            return m.group(1)
    return ciclo_default or ""


def _limpiar_nombre_curso(nombre: Any) -> str:
    nombre = limpiar_texto(nombre)
    nombre = re.sub(r"\s*-\s*$", "", nombre).strip()
    nombre = re.sub(r"^\s*-\s*", "", nombre).strip()
    nombre = re.sub(r"\b(Evaluaci[oó]n|Nota|Letra|Reclamo|Fecha\s+Prueba|Fecha\s+Registro)\b.*$", "", nombre, flags=re.I).strip()
    return nombre.strip("-: ")


def clasificar_evaluacion(nombre: Any) -> str:
    texto = _sin_tildes(nombre)
    # Importante: sustitutorio antes de final para no confundirlo.
    if re.search(r"\b(SUSTITUTORIO|EXAMEN\s+SUSTITUTORIO|ES)\b", texto):
        return "Examen sustitutorio"
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
    if re.search(r"\b(LABORATORIO|LAB\s*\d*)\b", texto):
        return "Laboratorio"
    if re.search(r"\b(CONTROL)\b", texto):
        return "Control"
    return "Nota"


def _es_nombre_evaluacion(texto: Any) -> bool:
    t = _sin_tildes(texto)
    return bool(re.search(
        r"\b(PRACTICA|PC\s*\d*|MONOGRAFIA|PARCIAL|FINAL|SUSTITUTORIO|EP\s*\d*|EF\s*\d*|PROMEDIO|NOTA\s+FINAL|TAREA|EXAMEN|CONTROL|LABORATORIO|LAB\s*\d*)\b",
        t,
    ))


def _detectar_curso_en_linea(linea: str) -> Optional[Tuple[str, str]]:
    """Detecta encabezados como: GE122U - SISTEMA DE COSTOS-"""
    linea = limpiar_texto(linea)
    if not linea:
        return None

    # Evita cabeceras administrativas.
    if re.search(r"\b(C[ÓO]DIGO\s*:|ALUMNO\s*:|MODALIDAD\s*:|FACULTAD\s*:|PLAN\s+DE\s+ESTUDIO)\b", linea, flags=re.I):
        return None

    m = re.match(r"^([A-Z]{2}\d{3})\s*-?\s*([A-Z])\s*-\s*(.+?)\s*-?\s*$", linea, flags=re.I)
    if not m:
        return None

    codigo = normalizar_codigo(f"{m.group(1)}-{m.group(2)}")
    nombre = _limpiar_nombre_curso(m.group(3))

    if not nombre or _es_nombre_evaluacion(nombre):
        return None
    return codigo, nombre


# Nombres de evaluación que aparecen en el reporte de notas.
_EVAL_RE = re.compile(
    r"^(?P<eval>"
    r"PRACTICA\s*\d+|PR[ÁA]CTICA\s*\d+|PC\s*\d+|"
    r"MONOGRAFIA\s*\d+|MONOGRAF[ÍI]A\s*\d+|"
    r"EXAMEN\s+PARCIAL|PARCIAL|EP\s*\d*|"
    r"EXAMEN\s+FINAL|FINAL|EF\s*\d*|"
    r"EXAMEN\s+SUSTITUTORIO|SUSTITUTORIO|"
    r"TAREA\s*\d*|CONTROL\s*\d*|LABORATORIO\s*\d*|LAB\s*\d*"
    r")\s+(?P<nota>-?\d{1,2}(?:[\.,]\d+)?)\b(?P<resto>.*)$",
    flags=re.I,
)


def _extraer_fechas(resto: str) -> Tuple[Optional[str], Optional[str]]:
    fechas = re.findall(r"\b\d{2}/\d{2}/\d{4}\b", resto or "")
    fecha_prueba = fechas[0] if len(fechas) >= 1 else None
    fecha_registro = fechas[1] if len(fechas) >= 2 else None
    return fecha_prueba, fecha_registro


def _observacion_desde_resto(resto: str, nota: Optional[float]) -> str:
    t = limpiar_texto(resto)
    obs = []
    if re.search(r"Evaluaci[oó]n\s+no\s+rendida|No\s+rendida", t, flags=re.I):
        obs.append("Evaluación no rendida")
    fecha_prueba, fecha_registro = _extraer_fechas(t)
    if fecha_prueba:
        obs.append(f"Fecha prueba: {fecha_prueba}")
    if fecha_registro:
        obs.append(f"Fecha registro: {fecha_registro}")
    if nota == 0 and not obs:
        obs.append("Nota 00")
    return "; ".join(obs)


def _agregar_nota(
    notas: List[Dict[str, Any]],
    seen: set,
    ciclo: str,
    codigo: str,
    nombre_curso: str,
    nombre_eval: str,
    nota: Optional[float],
    peso: Optional[float] = None,
    obs: str = "",
    fecha_prueba: Optional[str] = None,
    fecha_registro_eval: Optional[str] = None,
):
    codigo = normalizar_codigo(codigo)
    nombre_eval = limpiar_texto(nombre_eval).strip(":- ")
    nombre_curso = _limpiar_nombre_curso(nombre_curso) or codigo
    if not codigo or not nombre_eval or nota is None:
        return
    if not _es_nombre_evaluacion(nombre_eval):
        return

    key = (ciclo, codigo, _sin_tildes(nombre_eval), nota, fecha_prueba or "", fecha_registro_eval or "")
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
        "fecha_prueba": fecha_prueba,
        "fecha_registro_evaluacion": fecha_registro_eval,
        "origen": "PDF reporte de notas",
    })


def _parsear_lineas_reporte(texto: str, ciclo: str) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    notas: List[Dict[str, Any]] = []
    cursos_detectados: Dict[str, str] = {}
    seen = set()
    curso_actual = ""
    nombre_actual = ""

    lineas = [limpiar_texto(x) for x in texto.splitlines() if limpiar_texto(x)]

    for linea in lineas:
        curso_linea = _detectar_curso_en_linea(linea)
        if curso_linea:
            curso_actual, nombre_actual = curso_linea
            cursos_detectados[curso_actual] = nombre_actual
            continue

        if not curso_actual:
            continue

        # Saltar cabecera de la tabla y filas de promedio sin nota.
        if re.search(r"^Evaluaci[oó]n\s+Nota\s+Letra", linea, flags=re.I):
            continue
        if re.search(r"^Promedio\s+Practicas\s+Promedio\s+Final", linea, flags=re.I):
            continue

        m_eval = _EVAL_RE.match(linea)
        if not m_eval:
            continue

        nombre_eval = limpiar_texto(m_eval.group("eval"))
        nota = _parse_float(m_eval.group("nota"))
        resto = limpiar_texto(m_eval.group("resto"))
        fecha_prueba, fecha_registro_eval = _extraer_fechas(resto)
        obs = _observacion_desde_resto(resto, nota)

        _agregar_nota(
            notas,
            seen,
            ciclo,
            curso_actual,
            nombre_actual or curso_actual,
            nombre_eval,
            nota,
            obs=obs,
            fecha_prueba=fecha_prueba,
            fecha_registro_eval=fecha_registro_eval,
        )

    return notas, cursos_detectados


def _parsear_fallback_global(texto: str, ciclo: str, notas_existentes: List[Dict[str, Any]], cursos_detectados: Dict[str, str]) -> List[Dict[str, Any]]:
    """Respaldo para PDFs que pierden saltos de línea.
    No se usa si ya se leyó bien línea por línea, pero ayuda con otros reportes.
    """
    notas = list(notas_existentes)
    seen = {
        (n.get("ciclo"), n.get("codigo_curso"), _sin_tildes(n.get("nombre_evaluacion")), n.get("nota"), n.get("fecha_prueba") or "", n.get("fecha_registro_evaluacion") or "")
        for n in notas
    }

    texto_lineal = re.sub(r"\s+", " ", (texto or "").replace("\ufffe", " ")).strip()
    header_pat = re.compile(r"\b([A-Z]{2}\d{3})\s*-?\s*([A-Z])\s*-\s*([A-ZÁÉÍÓÚÑ0-9\s,.;()/-]+?)-\s*Evaluaci[oó]n\s+Nota\s+Letra", flags=re.I)
    headers = list(header_pat.finditer(texto_lineal))

    for idx, h in enumerate(headers):
        codigo = normalizar_codigo(f"{h.group(1)}-{h.group(2)}")
        nombre = _limpiar_nombre_curso(h.group(3)) or cursos_detectados.get(codigo) or codigo
        cursos_detectados[codigo] = nombre
        start = h.end()
        end = headers[idx + 1].start() if idx + 1 < len(headers) else len(texto_lineal)
        bloque = texto_lineal[start:end]

        for m_eval in _EVAL_RE.finditer(bloque):
            nombre_eval = limpiar_texto(m_eval.group("eval"))
            nota = _parse_float(m_eval.group("nota"))
            # Cortar el resto antes de la siguiente evaluación para no arrastrar demasiado texto.
            resto_inicio = m_eval.end()
            siguiente = _EVAL_RE.search(bloque, resto_inicio)
            resto = bloque[resto_inicio:(siguiente.start() if siguiente else min(len(bloque), resto_inicio + 160))]
            fecha_prueba, fecha_registro_eval = _extraer_fechas(resto)
            obs = _observacion_desde_resto(resto, nota)
            _agregar_nota(
                notas,
                seen,
                ciclo,
                codigo,
                nombre,
                nombre_eval,
                nota,
                obs=obs,
                fecha_prueba=fecha_prueba,
                fecha_registro_eval=fecha_registro_eval,
            )

    return notas


def parsear_reporte_notas_texto(texto: str, ciclo_default: str = "") -> Dict[str, Any]:
    texto = texto or ""
    ciclo = _extraer_ciclo(texto, ciclo_default)

    notas, cursos_detectados = _parsear_lineas_reporte(texto, ciclo)

    # Si por el tipo de PDF se detectaron pocas notas, usar respaldo global.
    if len(notas) < 3:
        notas = _parsear_fallback_global(texto, ciclo, notas, cursos_detectados)

    # Ordenar como aparece en el reporte: curso y luego tipo/nombre.
    # Mantiene orden de inserción, solo devuelve resumen adicional.
    return {
        "ciclo": ciclo,
        "notas": notas,
        "total_notas": len(notas),
        "cursos_detectados": cursos_detectados,
        "total_cursos": len(cursos_detectados),
        "texto_preview": texto[:2500],
    }


def parsear_reporte_notas_pdf(file: Any, ciclo_default: str = "") -> Dict[str, Any]:
    texto = extraer_texto_pdf(file)
    return parsear_reporte_notas_texto(texto, ciclo_default=ciclo_default)
