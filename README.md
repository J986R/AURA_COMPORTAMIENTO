# AURA WEB - Gestión de usuarios mejorada

Versión actualizada para Streamlit + Neon + Gemini.

## Cambios de esta versión

- Se mantiene retirada la importación de notas actuales desde INTRALU.
- INTRALU importa cursos/horarios desde `Curso matriculado -> Imprimir boleta` y avance curricular desde `Fichas académicas -> Avance curricular`.
- Se mejoró la sección **Gestión de usuarios** del administrador.
- Ahora el admin puede crear un **estudiante + usuario** en un solo paso.
- También puede registrar estudiantes sin usuario.
- Se puede crear un usuario para un estudiante ya existente.
- Se puede editar rol, estudiante vinculado, usuario y contraseña desde el panel admin.
- Se agregó validación para evitar usuarios duplicados y estudiantes duplicados por código UNI.

## Archivos principales actualizados

- `app.py`
- `database.py`

## Deploy

Sube los archivos al repositorio en GitHub y luego reinicia la app desde Streamlit Cloud:

`Manage app -> Reboot`
