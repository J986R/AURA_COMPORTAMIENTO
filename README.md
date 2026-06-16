# AURA WEB - INTRALU actualizado

Esta versión actualiza la importación desde INTRALU usando el flujo correcto:

1. **Cursos y horarios**: `Curso matriculado -> Imprimir boleta`.
2. **Notas actuales del ciclo**: `Curso matriculado -> Imprimir notas`.
3. **Historial completo del alumno**: `Fichas académicas -> Avance curricular`.

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
