# AURA WEB - PDF BOLETA Y REPORTE DE NOTAS

Versión actualizada de AURA sin scraping de INTRALU.

## Cambios principales

- Se retiró completamente la opción de scraping/credenciales de INTRALU desde la interfaz.
- Los estudiantes ahora solo importan información académica mediante archivos PDF:
  - Boleta de matrícula PDF: cursos, docentes, horarios y aulas.
  - Reporte de notas PDF: evaluaciones, tipo de evaluación y nota.
- El reporte de notas reconoce evaluaciones como:
  - Práctica / PC -> Práctica calificada.
  - Monografía -> Monografía.
  - Parcial / EP -> Examen parcial.
  - Final / EF -> Examen final.
  - Promedio / Nota final -> Promedio.
- Se mantiene el panel de administrador mejorado para crear estudiantes y usuarios de forma sencilla.
- Se mantiene la interfaz de tutor y admin con tarjetas, filtros y paneles más amigables.

## Archivos importantes

- `app.py`: interfaz principal.
- `database.py`: conexión y operaciones con Neon.
- `boleta_parser.py`: lectura de boleta de matrícula PDF.
- `notas_parser.py`: lectura de reporte de notas PDF.
- `planner.py`: planificación y calendario.
- `ai_engine.py`: diagnóstico, planificador y coach IA.

## Dependencias

Instalar con:

```bash
pip install -r requirements.txt
```

## Streamlit Secrets

Mantén tus secrets actuales:

```toml
NEON_DATABASE_URL = "postgresql://..."
GEMINI_API_KEY = "..."
GEMINI_MODEL = "gemini-2.5-flash-lite"
```

## Flujo recomendado

1. Admin crea estudiante + usuario.
2. Estudiante inicia sesión.
3. Estudiante sube boleta de matrícula PDF.
4. Estudiante sube reporte de notas PDF.
5. Estudiante realiza diagnóstico académico.
6. AURA genera planificador, calendario, coach IA y reportes.
