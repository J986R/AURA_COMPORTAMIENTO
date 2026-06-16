import re
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Tuple

from pypdf import PdfReader


DIAS_MAP = {
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

TIPOS_CLASE = {
    "TEORIA": "Teoría",
    "TEORÍA": "Teoría",
    "PRACTICA": "Práctica",
    "PRÁCTICA": "Práctica",
    "LAB": "Laboratorio",
    "LABORATORIO": "Laboratorio",
    "CLASE": "Clase",
}


def limpiar_nombre(nombre: Any) -> str:
    nombre = re.sub(r"\s+", " ", str(nombre or "")).strip()
    return nombre.strip("-").strip()


def _sin_tildes(texto: Any) -> str:
    return (
        str(texto or "")
        .upper()
        .replace("Á", "A")
        .replace("É", "E")
        .replace("Í", "I")
        .replace("Ó", "O")
        .replace("Ú", "U")
    )


def _normalizar_codigo(codigo: Any) -> str:
    texto = limpiar_nombre(codigo).upper().replace("/", "-")
    m = re.search(r"\b([A-Z]{2}\d{3})\s*-?\s*([A-Z])\b", texto)
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    return texto


def _normalizar_dia(dia: Any) -> str:
    clave = _sin_tildes(dia)
    if clave == "MIERCOLES":
        return "Miércoles"
    if clave == "SABADO":
        return "Sábado"
    return DIAS_MAP.get(clave, limpiar_nombre(dia).title())


def _normalizar_tipo(tipo: Any) -> str:
    clave = _sin_tildes(tipo)
    if "PRACT" in clave:
        return "Práctica"
    if "LAB" in clave:
        return "Laboratorio"
    if "TEORIA" in clave:
        return "Teoría"
    return TIPOS_CLASE.get(str(tipo).upper(), limpiar_nombre(tipo).title() or "Clase")


def _normalizar_hora(hora: Any) -> str:
    m = re.search(r"(\d{1,2})[:.](\d{2})", str(hora or ""))
    if not m:
        return ""
    return f"{int(m.group(1)):02d}:{int(m.group(2)):02d}"


def _aula_probable(texto: Any) -> str:
    texto = limpiar_nombre(texto).upper().replace("/", "-")
    m = re.search(r"\b([A-Z]\d?[-]?\d{2,4}|[A-Z]{1,3}[-]?\d{2,4}|AULA\s*\d+)\b", texto, flags=re.I)
    if m:
        return limpiar_nombre(m.group(1)).upper().replace(" ", "")
    return texto.split()[0] if texto else ""


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


def _extraer_datos_estudiante(texto: str) -> Tuple[str, str, str]:
    texto_lineal = re.sub(r"\s+", " ", texto or "").strip()
    alumno = ""
    codigo_alumno = ""
    especialidad = ""

    m = re.search(r"ALUMNO\s*:\s*(.*?)\s+ESPECIALIDAD\s*:\s*(.*?)(?:\s+C[ÓO]DIGO|\s+FECHA|$)", texto_lineal, re.I)
    if m:
        alumno = limpiar_nombre(m.group(1))
        especialidad = limpiar_nombre(m.group(2))

    m = re.search(r"C[ÓO]DIGO\s*:\s*([A-Z0-9]+)", texto_lineal, re.I)
    if m:
        codigo_alumno = m.group(1).strip().upper()

    return alumno, codigo_alumno, especialidad


def _parsear_tabla_cursos(texto: str) -> Dict[str, Dict[str, Any]]:
    cursos: Dict[str, Dict[str, Any]] = {}
    texto_lineal = re.sub(r"\s+", " ", texto or "").strip()

    patron = re.compile(
        r"(?:^|\s)(\d{1,2})\s+([A-Z]{2}\d{3}\s*[-/]?\s*[A-Z])\s+(.+?)\s+([A-Z])\s+(\d+)\s+(\d+)"
        r"(?=\s+\d{1,2}\s+[A-Z]{2}\d{3}\s*[-/]?\s*[A-Z]\s+|\s+Curso\s+Tipo\s+Docente\s+Dia\s+Hora\s+Aula\b|\s+\d{1,3}\s+Curso\s+Tipo|$)",
        flags=re.I,
    )
    for m in patron.finditer(texto_lineal):
        codigo = _normalizar_codigo(m.group(2))
        cursos[codigo] = {
            "ciclo": limpiar_nombre(m.group(1)),
            "codigo_curso": codigo,
            "nombre_curso": limpiar_nombre(m.group(3)),
            "condicion": limpiar_nombre(m.group(4)).upper(),
            "creditos": int(m.group(5) or 0),
            "veces": int(m.group(6) or 0),
        }

    # Respaldo línea por línea para PDF bien extraído.
    for linea in [limpiar_nombre(x) for x in (texto or "").splitlines() if limpiar_nombre(x)]:
        m = re.match(r"^(\d{1,2})\s+([A-Z]{2}\d{3}\s*[-/]?\s*[A-Z])\s+(.+?)\s+([A-Z])\s+(\d+)\s+(\d+)\s*$", linea, flags=re.I)
        if not m:
            continue
        codigo = _normalizar_codigo(m.group(2))
        cursos[codigo] = {
            "ciclo": limpiar_nombre(m.group(1)),
            "codigo_curso": codigo,
            "nombre_curso": limpiar_nombre(m.group(3)),
            "condicion": limpiar_nombre(m.group(4)).upper(),
            "creditos": int(m.group(5) or 0),
            "veces": int(m.group(6) or 0),
        }
    return cursos


def _parsear_tabla_horarios(texto: str, cursos: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    horarios: List[Dict[str, Any]] = []
    seen = set()
    tipo_pat = r"TEORIA|TEORÍA|PRACTICA|PRÁCTICA|LABORATORIO|LAB|CLASE"
    dia_pat = r"LUNES|MARTES|MI[ÉE]RCOLES|JUEVES|VIERNES|S[ÁA]BADO|DOMINGO"

    def add(codigo_raw: str, tipo_raw: str, docente_raw: str, dia_raw: str, inicio_raw: str, fin_raw: str, aula_raw: str):
        codigo = _normalizar_codigo(codigo_raw)
        tipo = _normalizar_tipo(tipo_raw)
        docente = limpiar_nombre(docente_raw)
        dia = _normalizar_dia(dia_raw)
        inicio = _normalizar_hora(inicio_raw)
        fin = _normalizar_hora(fin_raw)
        aula = _aula_probable(aula_raw)
        if not codigo or not inicio or not fin:
            return
        key = (codigo, tipo, dia, inicio, fin, aula)
        if key in seen:
            return
        seen.add(key)
        if codigo in cursos and docente and not cursos[codigo].get("docente"):
            cursos[codigo]["docente"] = docente
        nombre_curso = cursos.get(codigo, {}).get("nombre_curso", codigo)
        horarios.append({
            "codigo_curso": codigo,
            "nombre_curso": nombre_curso,
            "tipo": tipo,
            "docente": docente,
            "dia": dia,
            "inicio": inicio,
            "fin": fin,
            "aula": aula,
        })

    # 1) Respaldo línea por línea. Este es el formato del PDF UNI de referencia.
    patron_linea = re.compile(
        rf"^([A-Z]{{2}}\d{{3}}\s*[-/]?\s*[A-Z])\s+({tipo_pat})\s+(.+?)\s+({dia_pat})\s+"
        rf"(\d{{1,2}}[:.]\d{{2}})\s*(?:a|A|-|–|—)\s*(\d{{1,2}}[:.]\d{{2}})\s+(.+?)\s*$",
        flags=re.I,
    )
    for linea in [limpiar_nombre(x) for x in (texto or "").splitlines() if limpiar_nombre(x)]:
        m = patron_linea.match(linea)
        if m:
            add(*m.groups())

    # 2) Parser global: útil si PyPDF/HTML junta varias filas en una sola línea.
    texto_lineal = re.sub(r"\s+", " ", texto or "").strip()
    mhdr = re.search(r"Curso\s+Tipo\s+Docente\s+Dia\s+Hora\s+Aula", texto_lineal, flags=re.I)
    horario_texto = texto_lineal[mhdr.end():] if mhdr else texto_lineal
    patron_global = re.compile(
        rf"\b([A-Z]{{2}}\d{{3}}\s*[-/]?\s*[A-Z])\s+({tipo_pat})\s+(.+?)\s+({dia_pat})\s+"
        rf"(\d{{1,2}}[:.]\d{{2}})\s*(?:a|A|-|–|—)\s*(\d{{1,2}}[:.]\d{{2}})\s+(.+?)"
        rf"(?=\s+[A-Z]{{2}}\d{{3}}\s*[-/]?\s*[A-Z]\s+(?:{tipo_pat})\b|\s*\*\*|\s*Recuerde\b|$)",
        flags=re.I,
    )
    for m in patron_global.finditer(horario_texto):
        add(*m.groups())

    return horarios


def parsear_boleta_texto(texto: str) -> Dict[str, object]:
    alumno, codigo_alumno, especialidad = _extraer_datos_estudiante(texto)
    cursos = _parsear_tabla_cursos(texto)
    horarios = _parsear_tabla_horarios(texto, cursos)
    return {
        "alumno": alumno,
        "codigo_alumno": codigo_alumno,
        "especialidad": especialidad,
        "cursos": list(cursos.values()),
        "horarios": horarios,
        "texto": texto,
    }


def parsear_boleta_matricula(file: Any) -> Dict[str, object]:
    texto = extraer_texto_pdf(file)
    return parsear_boleta_texto(texto)
