# AURA WEB - INTRALU, Notas y Calendario

Versión actualizada con:

- Importación por boleta PDF.
- Importación desde INTRALU usando credenciales temporales.
- Extracción de cursos, horarios y notas por curso.
- Tabla `notas_curso` en Neon.
- Dashboard con resumen de notas importadas.
- Planificador semanal y mensual con calendario visual.
- Interfaz con paleta pastel y botones redondeados.

## Seguridad de credenciales INTRALU

AURA no guarda la contraseña del estudiante en Neon ni en variables persistentes. La contraseña solo se usa durante la importación y luego se descarta.

Si INTRALU solicita CAPTCHA, verificación adicional o cambia su estructura, el scraper puede fallar. En ese caso, usa la importación por boleta PDF como respaldo.

## Archivos principales

- `app.py`
- `database.py`
- `intralu_scraper.py`
- `ai_engine.py`
- `planner.py`
- `report_generator.py`
- `boleta_parser.py`
- `config.py`
- `requirements.txt`

## Secrets de Streamlit

```toml
NEON_DATABASE_URL = "postgresql://usuario:password@host.neon.tech/neondb?sslmode=require"
GEMINI_API_KEY = "TU_API_KEY"
GEMINI_MODEL = "gemini-2.5-flash-lite"
```

## Dependencias nuevas

Se agregaron:

```txt
beautifulsoup4
lxml
playwright
```

Para usarlo localmente, después de instalar requirements ejecuta:

```bash
python -m playwright install chromium
```

En Streamlit Cloud, la app intentará instalar Chromium si no existe. Si el servidor no permite instalarlo, la app seguirá funcionando y podrás importar por PDF.

## Despliegue

Sube los archivos al repositorio GitHub, haz commit y reinicia la app en Streamlit Cloud:

```text
Manage app → Reboot
```

La app creará automáticamente la tabla `notas_curso` al iniciar.
