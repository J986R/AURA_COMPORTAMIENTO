import os
from dotenv import load_dotenv

load_dotenv()


def get_setting(name: str, default=None):
    """Obtiene configuración desde Streamlit Secrets o variables de entorno."""
    try:
        import streamlit as st
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.getenv(name, default)
