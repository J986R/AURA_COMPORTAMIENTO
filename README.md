# AURA WEB corregido

Versión Streamlit + Neon PostgreSQL + Gemini API.

## Correcciones incluidas

- Menú **Mi perfil** para que los usuarios puedan cambiar usuario, contraseña y datos del estudiante vinculado.
- Diagnóstico académico carga el último diagnóstico guardado y mantiene horas, promedio y respuestas.
- Escala 1 a 5 visible en cada respuesta usando etiquetas: Nunca, Casi nunca, A veces, Casi siempre, Siempre.
- Ventana de cursos con opción de editar curso.
- Planificador semanal generado con IA para dividir tareas grandes en varios días.
- Riesgo académico normalizado para evitar contradicciones entre puntaje y nivel.
- Coach IA instruido para no cambiar el nivel de riesgo mostrado por el sistema.
- Reportes PDF corregidos con textos largos ajustados y sin superposición.

## Secrets de Streamlit

```toml
NEON_DATABASE_URL = "postgresql://usuario:password@host.neon.tech/neondb?sslmode=require"
GEMINI_API_KEY = "TU_API_KEY_DE_GEMINI"
GEMINI_MODEL = "gemini-2.5-flash-lite"
```

## Archivo principal

```text
app.py
```


## Versión calendario y boleta

Cambios incluidos:
- Los estudiantes entran directamente al Dashboard.
- Se unieron las pestañas **Perfil y Cursos** y **Tareas y Planificador**.
- Se agregó importación de boleta de matrícula PDF para crear cursos y horarios automáticamente.
- El planificador usa IA y se visualiza como calendario semanal, evitando cruces con clases.
- Se agregaron ventanas pequeñas con botones ➕ para crear cursos y tareas.
- Se agregó tabla `horarios_clase` en Neon.
- Se agregó `pypdf` en `requirements.txt`.

Recuerda subir todos los archivos nuevos a GitHub, incluido `boleta_parser.py` y `assets/logo_aura.png`.
