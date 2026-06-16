# AURA WEB - INTRALU corregido

Esta versión corrige la importación desde INTRALU usando el flujo real:

1. **Cursos y horarios**: `Curso matriculado -> Imprimir boleta`.
2. **Notas actuales del ciclo**: `Curso matriculado -> Imprimir notas`.
3. **Historial completo del alumno**: `Fichas académicas -> Avance curricular`.

## Correcciones de esta versión

- La pantalla/documento de notas ya no se carga como si fueran cursos.
- AURA solo crea cursos y horarios cuando el documento capturado tiene estructura de **boleta de matrícula**.
- Las notas actuales ya no leen únicamente la columna **Nota**.
- Ahora se extraen evaluaciones por columna, por ejemplo:
  - `Práctica 2` -> tipo **Práctica calificada**.
  - `Monografía 2` -> tipo **Monografía**.
  - `Parcial` / `EP` -> tipo **Examen parcial**.
  - `Final` / `EF` -> tipo **Examen final**.
  - `Nota` / `Promedio` -> tipo **Promedio**.

## Archivos principales actualizados

- `app.py`
- `database.py`
- `intralu_scraper.py`
- `requirements.txt`
- `packages.txt`

## Seguridad

AURA no guarda la contraseña de INTRALU. La usa solo temporalmente para iniciar sesión, capturar la boleta/notas/avance curricular y cerrar la sesión del navegador automatizado.

## Dependencias

El scraper usa Playwright. En local ejecuta:

```bash
python -m pip install -r requirements.txt
python -m playwright install chromium
streamlit run app.py
```

En Streamlit Cloud, sube también `packages.txt`. Si Playwright no puede ejecutar Chromium o INTRALU solicita CAPTCHA/verificación, usa la importación por PDF como respaldo.

## Secrets requeridos

```toml
NEON_DATABASE_URL = "postgresql://..."
GEMINI_API_KEY = "..."
GEMINI_MODEL = "gemini-2.5-flash-lite"
```
