# AURA WEB - Planificador mejorado

Versión con:

- Planificador semanal y mensual.
- Plan desde la fecha actual.
- Asignación antes o máximo en la fecha de entrega.
- Bloques de almuerzo y descanso.
- Mayor carga de estudio según dificultad del curso.
- Calendario visual mejorado.
- Interfaz con paleta pastel inspirada en el logo de AURA.

## Archivos principales

- `app.py`
- `database.py`
- `ai_engine.py`
- `planner.py`
- `report_generator.py`
- `boleta_parser.py`
- `requirements.txt`

## Secrets de Streamlit

```toml
NEON_DATABASE_URL = "postgresql://usuario:password@host.neon.tech/neondb?sslmode=require"
GEMINI_API_KEY = "TU_API_KEY"
GEMINI_MODEL = "gemini-2.5-flash-lite"
```

## Despliegue

Sube los archivos al repositorio GitHub y reinicia la app en Streamlit Cloud si no actualiza automáticamente.
