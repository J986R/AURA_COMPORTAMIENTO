# AURA WEB

AURA WEB es la versión publicable en internet de AURA.

## Stack

- Interfaz web: Streamlit
- Base de datos en la nube: Neon PostgreSQL
- IA en la nube: Gemini API
- Reportes: Excel y PDF

## Archivos principales

```text
AURA_WEB/
├── app.py
├── database.py
├── ai_engine.py
├── planner.py
├── report_generator.py
├── config.py
├── requirements.txt
├── .env.example
└── .streamlit/
    └── secrets.toml.example
```

## Ejecución local

1. Crea un archivo `.env` copiando `.env.example`.
2. Coloca tus claves:

```env
NEON_DATABASE_URL=postgresql://usuario:password@host.neon.tech/neondb?sslmode=require
GEMINI_API_KEY=TU_API_KEY_DE_GEMINI
GEMINI_MODEL=gemini-2.0-flash-lite
```

3. Instala dependencias:

```bash
python -m pip install -r requirements.txt
```

4. Ejecuta:

```bash
streamlit run app.py
```

## Usuario inicial

```text
Usuario: admin
Contraseña: aura123
```

Al iniciar por primera vez, AURA crea las tablas en Neon y crea el usuario administrador inicial.

## Publicar en Streamlit Community Cloud

1. Crea un repositorio en GitHub.
2. Sube todos los archivos de `AURA_WEB`.
3. Entra a Streamlit Community Cloud.
4. Crea una nueva app seleccionando tu repositorio y `app.py`.
5. En `Settings > Secrets`, pega el contenido de `.streamlit/secrets.toml.example`, pero con tus claves reales.
6. Despliega la app.

## Notas importantes

- No subas tu archivo `.env` ni tus claves reales a GitHub.
- La base de datos es compartida: todos los usuarios ven la misma información según su rol.
- La IA se ejecuta en Gemini, por eso los usuarios no necesitan instalar Ollama.
- El diagnóstico IA es referencial y académico, no clínico.
