import os
from dotenv import load_dotenv

load_dotenv()


def get_setting(name: str, default: str | None = None) -> str | None:
    """Lee configuración desde variables de entorno o Streamlit secrets."""
    value = os.getenv(name)
    if value:
        return value

    try:
        import streamlit as st  # type: ignore
        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:
        pass

    return default
