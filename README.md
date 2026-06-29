# AURA WEB - INTRALU sin notas + paneles mejorados

Esta versión actualiza AURA con los siguientes cambios:

## Cambios principales

- Se retiró la función de extraer notas actuales desde INTRALU.
- INTRALU ahora solo importa:
  - Cursos y horarios desde `Curso matriculado -> Imprimir boleta`.
  - Avance curricular desde `Fichas académicas -> Avance curricular`.
- El avance curricular sigue funcionando como indicador de riesgo académico.
- La contraseña de INTRALU no se guarda en Neon ni en la sesión.
- Se mejoró la pantalla de login con estilo tipo Card / Input / Button.
- Se mejoró la interfaz del tutor con tarjetas, filtros, priorización y gráficas.
- Se agregó un Panel Admin más amigable con métricas, resumen de usuarios y acciones rápidas.
- Se mejoró la Gestión de usuarios con pestañas: crear, listar y editar/eliminar.

## Archivos principales modificados

- `app.py`
- `database.py`
- `intralu_scraper.py`
- `README.md`

## Flujo INTRALU actualizado

```text
INTRALU -> Curso matriculado -> Imprimir boleta
```
Sirve para importar cursos, docentes, horarios y aulas.

```text
INTRALU -> Fichas académicas -> Avance curricular
```
Sirve para importar historial académico y alimentar el diagnóstico de riesgo.

> La ruta `Curso matriculado -> Imprimir notas` ya no se usa en esta versión.

## Instalación / despliegue

Sube o reemplaza los archivos en GitHub, haz commit y reinicia la app en Streamlit Cloud:

```text
Manage app -> Reboot
```

Mantén tus secrets actuales:

```toml
NEON_DATABASE_URL = "..."
GEMINI_API_KEY = "..."
GEMINI_MODEL = "gemini-2.5-flash-lite"
```
