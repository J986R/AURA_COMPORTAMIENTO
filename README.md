# AURA WEB - Horarios de boleta corregidos

Versión corregida para importar desde INTRALU y leer correctamente la boleta de matrícula.

## Corrección principal

La importación de horarios ahora reconoce desde la boleta:

- Curso
- Tipo de clase: teoría, práctica, laboratorio o clase
- Docente
- Día
- Hora de inicio
- Hora de fin
- Aula

El parser fue probado con una boleta UNI 20261 y detecta 7 cursos y 14 bloques de horario.

## Archivos principales modificados

- `boleta_parser.py`
- `intralu_scraper.py`

## Cómo actualizar

Reemplaza estos archivos en GitHub:

- `boleta_parser.py`
- `intralu_scraper.py`

También puedes subir todo el ZIP para mantener la versión completa sincronizada.

Después haz commit y reinicia la app en Streamlit Cloud.
