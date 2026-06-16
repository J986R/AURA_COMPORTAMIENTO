import re
from io import BytesIO
from pathlib import Path
from typing import BinaryIO, Dict, List

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


def extraer_texto_pdf(file) -> str:
    if hasattr(file, "read"):
        data = file.read()
        try:
            file.seek(0)
        except Exception:
            pass
    else:
        if isinstance(file, (str, bytes, bytearray)) and not isinstance(file, (bytes, bytearray)):
            data = Path(file).read_bytes()
        else:
            data = file
    reader = PdfReader(BytesIO(data))
    textos = []
    for page in reader.pages:
        textos.append(page.extract_text() or "")
    return "\n".join(textos)


def limpiar_nombre(nombre: str) -> str:
    nombre = re.sub(r"\s+", " ", nombre or "").strip()
    return nombre.strip("-").strip()


def parsear_boleta_matricula(file) -> Dict[str, object]:
    texto = extraer_texto_pdf(file)
    lineas = [re.sub(r"\s+", " ", l).strip() for l in texto.splitlines() if l.strip()]

    alumno = ""
    codigo_alumno = ""
    especialidad = ""

    m = re.search(r"ALUMNO\s*:\s*(.*?)\s+ESPECIALIDAD\s*:\s*(.*?)(?:\n|$)", texto, re.IGNORECASE)
    if m:
        alumno = limpiar_nombre(m.group(1))
        especialidad = limpiar_nombre(m.group(2))
    m = re.search(r"C[ÓO]DIGO\s*:\s*([A-Z0-9]+)", texto, re.IGNORECASE)
    if m:
        codigo_alumno = m.group(1).strip()

    cursos = {}
    horarios = []

    patron_curso = re.compile(r"^(\d{1,2})\s+([A-Z]{2}\d{3}-[A-Z])\s+(.+?)\s+([A-Z])\s+(\d+)\s+(\d+)\s*$")
    patron_horario = re.compile(
        r"^([A-Z]{2}\d{3}-[A-Z])\s+(TEORIA|TEORÍA|PRACTICA|PRÁCTICA|LABORATORIO|LAB)\s+(.+?)\s+"
        r"(LUNES|MARTES|MI[ÉE]RCOLES|JUEVES|VIERNES|S[ÁA]BADO|DOMINGO)\s+"
        r"(\d{1,2}:\d{2})\s+a\s+(\d{1,2}:\d{2})\s+(.+)$",
        re.IGNORECASE,
    )

    for linea in lineas:
        mc = patron_curso.match(linea)
        if mc:
            ciclo, codigo, nombre, condicion, creditos, veces = mc.groups()
            cursos[codigo] = {
                "ciclo": ciclo,
                "codigo_curso": codigo,
                "nombre_curso": limpiar_nombre(nombre),
                "condicion": condicion,
                "creditos": int(creditos),
                "veces": int(veces),
            }
            continue

        mh = patron_horario.match(linea)
        if mh:
            codigo, tipo, docente, dia, inicio, fin, aula = mh.groups()
            dia_norm = DIAS_MAP.get(dia.upper().replace("É", "E").replace("Á", "A"), DIAS_MAP.get(dia.upper(), dia.title()))
            tipo_norm = tipo.upper().replace("Á", "A").replace("Í", "I")
            nombre_curso = cursos.get(codigo, {}).get("nombre_curso", codigo)
            horarios.append({
                "codigo_curso": codigo,
                "nombre_curso": nombre_curso,
                "tipo": "Práctica" if "PRACT" in tipo_norm else ("Laboratorio" if "LAB" in tipo_norm else "Teoría"),
                "docente": limpiar_nombre(docente),
                "dia": dia_norm,
                "inicio": inicio.zfill(5),
                "fin": fin.zfill(5),
                "aula": limpiar_nombre(aula),
            })

    # Completar docente principal de cursos con el primer horario encontrado.
    for h in horarios:
        if h["codigo_curso"] in cursos and not cursos[h["codigo_curso"]].get("docente"):
            cursos[h["codigo_curso"]]["docente"] = h.get("docente", "")

    return {
        "alumno": alumno,
        "codigo_alumno": codigo_alumno,
        "especialidad": especialidad,
        "cursos": list(cursos.values()),
        "horarios": horarios,
        "texto": texto,
    }
