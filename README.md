# AURA WEB - INTRALU corregido con avance curricular y horarios reforzados

Versión actualizada de AURA con integración INTRALU, calendario, diagnóstico académico y planificador.

## Cambios de esta versión

1. **Boleta / horarios corregidos**
   - Se reforzó el parser de boleta para detectar mejor:
     - nombre del docente,
     - día de clase,
     - hora de inicio,
     - hora de fin,
     - aula.
   - Si el PDF/HTML junta filas o columnas, AURA aplica un parser global adicional.

2. **Avance curricular como indicador de riesgo**
   - Se agregó la tabla `avance_curricular`.
   - El scraper intenta leer el avance curricular desde INTRALU.
   - Si detecta cursos llevados **3 o más veces**, lo usa como antecedente de riesgo académico.
   - El diagnóstico IA recibe este indicador y ajusta el puntaje de riesgo.

3. **Notas y actividades**
   - Se mantiene la lectura de notas actuales.
   - Práctica 1/2 se clasifica como Práctica calificada.
   - Monografía 1/2 se clasifica como Monografía.
   - Parcial y Final se clasifican correctamente.

## Archivos principales actualizados

- `app.py`
- `database.py`
- `intralu_scraper.py`
- `ai_engine.py`
- `boleta_parser.py`

## Despliegue

Sube o reemplaza todo el contenido del ZIP en GitHub y luego reinicia la app en Streamlit Cloud.

La app creará automáticamente la nueva tabla `avance_curricular` al iniciar.

## Seguridad

Las credenciales de INTRALU no se guardan. Solo se usan temporalmente durante la importación.
