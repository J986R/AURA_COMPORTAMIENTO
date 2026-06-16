"""
Scraper seguro para INTRALU / alumnos.uni.edu.pe.

Uso previsto dentro de AURA:
- El estudiante escribe sus credenciales en un formulario temporal.
- La contraseña NO se guarda en Neon, NO se escribe en logs y NO se devuelve.
- El scraper abre una sesión temporal, importa cursos/horarios/notas y cierra el navegador.

Importante:
- Si INTRALU cambia su HTML, selectores o agrega CAPTCHA, este módulo devolverá un error claro.
- No intenta evadir CAPTCHA, 2FA, bloqueos ni restricciones del portal.
"""

from __future__ import annotations

import re
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from bs4 import BeautifulSoup

BASE_URL = "https://alumnos.uni.edu.pe"
CURSOS_URL = BASE_URL + "/informacion-academica/cursos/{ciclo}"
DETALLE_URL = BASE_URL + "/informacion-academica/cursos/{ciclo}/{codigo}/{seccion}"

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


@dataclass
class IntraluResultado:
    estudiante: Dict[str, Any]
    cursos: List[Dict[str, Any]]
    horarios: List[Dict[str, Any]]
    notas: List[Dict[str, Any]]
    advertencias: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "estudiante": self.estudiante,
            "cursos": self.cursos,
            "horarios": self.horarios,
            "notas": self.notas,
            "advertencias": self.advertencias,
        }


def limpiar_texto(valor: Any) -> str:
    if valor is None:
        return ""
    texto = str(valor).replace("\xa0", " ")
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def normalizar_decimal(valor: Any) -> Optional[float]:
    texto = limpiar_texto(valor).replace(",", ".")
    if not texto or texto in {"-", "--"}:
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


def normalizar_hora(texto: str) -> str:
    texto = limpiar_texto(texto)
    m = re.search(r"(\d{1,2})[:.](\d{2})", texto)
    if not m:
        return "08:00"
    h = max(0, min(23, int(m.group(1))))
    minuto = max(0, min(59, int(m.group(2))))
    return f"{h:02d}:{minuto:02d}"


def separar_codigo_seccion(codigo_compuesto: str) -> Tuple[str, str]:
    texto = limpiar_texto(codigo_compuesto).upper()
    # GE122-U, GE122 U, GE122/U
    m = re.search(r"\b([A-Z]{2}\d{3})\s*[-/]?\s*([A-Z])\b", texto)
    if m:
        return m.group(1), m.group(2)
    # Si viene como GE122 únicamente, por defecto sección U.
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
        return pd.read_html(html)
    except Exception:
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


def extraer_estudiante_desde_texto(texto: str) -> Dict[str, Any]:
    estudiante: Dict[str, Any] = {}
    limpio = limpiar_texto(texto)
    patrones = {
        "nombre": r"(?:ALUMNO|ESTUDIANTE)\s*:?\s*([A-ZÁÉÍÓÚÑ ]{5,}?)(?:\s+ESPECIALIDAD|\s+CÓDIGO|\s+CODIGO|$)",
        "codigo": r"(?:CÓDIGO|CODIGO)\s*:?\s*([0-9]{6,}[A-Z]?)",
        "carrera": r"(?:ESPECIALIDAD|CARRERA)\s*:?\s*([A-ZÁÉÍÓÚÑ ]{5,}?)(?:\s+FECHA|\s+CICLO|$)",
    }
    for key, patron in patrones.items():
        m = re.search(patron, limpio, flags=re.IGNORECASE)
        if m:
            estudiante[key] = limpiar_texto(m.group(1)).title() if key != "codigo" else limpiar_texto(m.group(1)).upper()
    return estudiante


def extraer_cursos_y_horarios(html: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[str]]:
    """Extrae cursos y horarios desde la página general de cursos.

    Soporta dos casos:
    1. Tablas HTML con encabezados.
    2. Texto plano similar a la boleta de matrícula.
    """
    advertencias: List[str] = []
    cursos: Dict[str, Dict[str, Any]] = {}
    horarios: List[Dict[str, Any]] = []

    tablas = _leer_tablas_html(html)

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

        # Tabla de cursos.
        if col_curso and (col_nombre or col_creditos) and not col_dia:
            for _, row in df.iterrows():
                cod_raw = limpiar_texto(row.get(col_curso, ""))
                codigo, seccion = separar_codigo_seccion(cod_raw)
                if not codigo or not re.search(r"[A-Z]{2}\d{3}", codigo):
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

        # Tabla de horarios.
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
    soup = BeautifulSoup(html, "html.parser")
    texto = soup.get_text("\n")
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
        m = re.match(r"^([A-Z]{2}\d{3}[-/]?[A-Z])\s+(TEORIA|TEORÍA|PRACTICA|PRÁCTICA|LABORATORIO|CLASE)\s+(.+?)\s+(LUNES|MARTES|MI[ÉE]RCOLES|JUEVES|VIERNES|S[ÁA]BADO|DOMINGO)\s+(\d{1,2}:\d{2})\s*(?:a|-|–)\s*(\d{1,2}:\d{2})\s*(.*)$", linea, flags=re.I)
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
        advertencias.append("No se detectaron cursos en la página general. INTRALU pudo cambiar su estructura.")
    if not horarios:
        advertencias.append("No se detectaron horarios en la página general. Puedes importarlos por boleta PDF o ingresarlos manualmente.")

    return list(cursos.values()), horarios, advertencias


def extraer_notas_detalle(html: str, codigo_curso: str, nombre_curso: str = "") -> List[Dict[str, Any]]:
    """Extrae notas desde la página detalle de un curso.

    La estructura de INTRALU puede variar; por eso se leen tablas y filas que contengan valores numéricos compatibles con notas 0-20.
    """
    notas: List[Dict[str, Any]] = []
    tablas = _leer_tablas_html(html)

    for idx_tabla, df in enumerate(tablas):
        if df.empty:
            continue
        mapping = _columnas_norm(df)
        col_eval = _col(mapping, "evaluacion", "evaluación", "descripcion", "descripción", "nombre", "concepto", "tipo")
        col_nota = _col(mapping, "nota", "calificacion", "calificación", "puntaje")
        col_peso = _col(mapping, "peso", "porcentaje", "%")
        col_obs = _col(mapping, "observacion", "observación", "estado")

        if not col_nota:
            # Buscar alguna columna con números entre 0 y 20.
            for col in df.columns:
                valores = [normalizar_decimal(v) for v in df[col].tolist()]
                validos = [v for v in valores if v is not None and 0 <= v <= 20]
                if validos:
                    col_nota = col
                    break

        if not col_nota:
            continue

        for i, row in df.iterrows():
            nota = normalizar_decimal(row.get(col_nota, None))
            if nota is None or nota < 0 or nota > 20:
                continue
            evaluacion = limpiar_texto(row.get(col_eval, "")) if col_eval else f"Evaluación {i + 1}"
            if not evaluacion:
                evaluacion = f"Evaluación {i + 1}"
            notas.append({
                "codigo_curso": codigo_curso,
                "nombre_curso": nombre_curso or codigo_curso,
                "tipo_evaluacion": inferir_tipo_evaluacion(evaluacion),
                "nombre_evaluacion": evaluacion,
                "nota": nota,
                "peso": normalizar_decimal(row.get(col_peso, None)) if col_peso else None,
                "observacion": limpiar_texto(row.get(col_obs, "")) if col_obs else "",
                "origen": f"tabla_{idx_tabla + 1}",
            })

    # Fallback texto: PC1 15, EP 12, EF 14, etc.
    if not notas:
        soup = BeautifulSoup(html, "html.parser")
        texto = soup.get_text("\n")
        patrones = re.findall(r"\b((?:PC|PR|EP|EF|EX|LAB|TP|TA|MONO|PROM|PROMEDIO)[A-Z0-9 ]{0,20})\s*[:=]?\s*(\d{1,2}(?:[.,]\d+)?)\b", texto, flags=re.I)
        for nombre, nota_txt in patrones:
            nota = normalizar_decimal(nota_txt)
            if nota is not None and 0 <= nota <= 20:
                evaluacion = limpiar_texto(nombre).upper()
                notas.append({
                    "codigo_curso": codigo_curso,
                    "nombre_curso": nombre_curso or codigo_curso,
                    "tipo_evaluacion": inferir_tipo_evaluacion(evaluacion),
                    "nombre_evaluacion": evaluacion,
                    "nota": nota,
                    "peso": None,
                    "observacion": "",
                    "origen": "texto",
                })

    # Quitar duplicados simples.
    unicas: Dict[Tuple[str, str, float], Dict[str, Any]] = {}
    for n in notas:
        key = (n.get("codigo_curso", ""), n.get("nombre_evaluacion", ""), float(n.get("nota") or 0))
        unicas[key] = n
    return list(unicas.values())


def inferir_tipo_evaluacion(nombre: str) -> str:
    t = limpiar_texto(nombre).lower()
    if any(x in t for x in ["final", "ef"]):
        return "Examen final"
    if any(x in t for x in ["parcial", "ep"]):
        return "Examen parcial"
    if any(x in t for x in ["pc", "practica", "práctica"]):
        return "Práctica calificada"
    if any(x in t for x in ["mono", "monografia", "monografía"]):
        return "Monografía"
    if any(x in t for x in ["prom", "promedio"]):
        return "Promedio"
    return "Nota"


def _rellenar_login(page, codigo_uni: str, password: str) -> None:
    """Rellena el login con selectores heurísticos.

    No registra ni devuelve la contraseña.
    """
    # Campo de usuario: intentos por nombre/id/placeholders frecuentes.
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
        # Último recurso: Enter desde el password.
        page.locator("input[type='password']").first.press("Enter")


def importar_cursos_horarios_notas_intralu(codigo_uni: str, password: str, ciclo: str = "20261", timeout_ms: int = 45000) -> Dict[str, Any]:
    """Inicia sesión temporal e importa cursos, horarios y notas.

    Requiere instalar Playwright y sus navegadores:
        pip install playwright
        playwright install chromium

    En Streamlit Cloud puede requerir packages.txt con dependencias de Chromium.
    """
    if not codigo_uni or not password:
        raise ValueError("Debes ingresar código UNI y contraseña.")

    advertencias: List[str] = []
    cursos: List[Dict[str, Any]] = []
    horarios: List[Dict[str, Any]] = []
    notas: List[Dict[str, Any]] = []
    estudiante: Dict[str, Any] = {"codigo": limpiar_texto(codigo_uni).upper()}

    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
    except Exception as exc:
        raise RuntimeError(
            "Playwright no está instalado. Agrega 'playwright' al requirements.txt y ejecuta 'python -m playwright install chromium'."
        ) from exc

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        except Exception as exc:
            # En algunos despliegues el paquete está instalado, pero falta descargar Chromium.
            # Se intenta una instalación temporal y, si falla, se muestra un mensaje claro.
            if "Executable doesn't exist" in str(exc) or "playwright install" in str(exc).lower():
                try:
                    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True, timeout=240)
                    browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
                except Exception as install_exc:
                    raise RuntimeError(
                        "Playwright está instalado, pero Chromium no pudo descargarse en el servidor. "
                        "Ejecuta localmente: python -m playwright install chromium. "
                        "Si usas Streamlit Cloud, mantén la importación por boleta PDF como respaldo."
                    ) from install_exc
            else:
                raise
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        page.set_default_timeout(timeout_ms)

        try:
            page.goto(CURSOS_URL.format(ciclo=ciclo), wait_until="domcontentloaded")
            time.sleep(1)

            # Si aparece login, completar credenciales.
            if page.locator("input[type='password']").count() > 0:
                _rellenar_login(page, codigo_uni, password)
                try:
                    page.wait_for_load_state("networkidle", timeout=timeout_ms)
                except PlaywrightTimeoutError:
                    pass

            # Asegurar ruta de cursos después del login.
            page.goto(CURSOS_URL.format(ciclo=ciclo), wait_until="domcontentloaded")
            try:
                page.wait_for_load_state("networkidle", timeout=timeout_ms)
            except PlaywrightTimeoutError:
                pass
            html_cursos = page.content()

            if page.locator("input[type='password']").count() > 0:
                raise RuntimeError("No se pudo iniciar sesión. Verifica código, contraseña o si INTRALU pide un paso adicional.")

            soup = BeautifulSoup(html_cursos, "html.parser")
            estudiante.update(extraer_estudiante_desde_texto(soup.get_text("\n")))
            cursos, horarios, adv = extraer_cursos_y_horarios(html_cursos)
            advertencias.extend(adv)

            # Entrar al detalle de cada curso para notas.
            for curso in cursos:
                cod_base = curso.get("codigo") or separar_codigo_seccion(curso.get("codigo_curso", ""))[0]
                seccion = curso.get("seccion") or separar_codigo_seccion(curso.get("codigo_curso", ""))[1]
                if not cod_base:
                    continue
                url = DETALLE_URL.format(ciclo=ciclo, codigo=cod_base, seccion=seccion or "U")
                try:
                    page.goto(url, wait_until="domcontentloaded")
                    try:
                        page.wait_for_load_state("networkidle", timeout=15000)
                    except PlaywrightTimeoutError:
                        pass
                    html_detalle = page.content()
                    notas.extend(extraer_notas_detalle(html_detalle, curso.get("codigo_curso") or codigo_visible(cod_base, seccion), curso.get("nombre_curso", "")))
                except Exception as exc:
                    advertencias.append(f"No se pudieron leer notas de {curso.get('codigo_curso')}: {exc}")

        finally:
            # Cierre de sesión local del navegador temporal.
            try:
                context.clear_cookies()
                context.close()
            finally:
                browser.close()

    return IntraluResultado(estudiante=estudiante, cursos=cursos, horarios=horarios, notas=notas, advertencias=advertencias).to_dict()
