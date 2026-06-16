# AURA WEB - versión tareas, calendario y UI mejorada

Cambios principales:

- Tipos de actividad: Tarea, Monografía, Práctica calificada, Examen parcial y Examen final.
- El planificador considera el tipo de actividad y la dificultad del curso para asignar más o menos días/horas.
- Menú reorganizado: Dashboard Estudiante, Diagnóstico Académico, Perfil Académico, Tareas y Planificador, Coach IA y Reportes.
- Calendario semanal/mensual con estilo similar a Google Calendar.
- Dashboard con gráficos horizontales más legibles.
- Botones e interfaz con estilo pastel, redondeado y minimalista.
- Controles de música opcionales: sube un archivo `assets/background.mp3` para activar el reproductor en la barra lateral.

## Archivos a subir a GitHub

Reemplaza los archivos del repositorio con los de esta carpeta. Mantén tus Secrets de Streamlit:

```toml
NEON_DATABASE_URL = "..."
GEMINI_API_KEY = "..."
GEMINI_MODEL = "gemini-2.5-flash-lite"
```

## Notas

La app crea automáticamente la columna `tipo_actividad` en la tabla `tareas` si todavía no existe.
