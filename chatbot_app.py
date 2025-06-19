import os
import time
from typing import Dict

import streamlit as st
from langchain_community.utilities import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.agent_toolkits import create_sql_agent

st.set_page_config(
    page_title="Chatbot de E‑commerce",
    page_icon="🤖",
    layout="centered",
)
st.title("🤖 Chatbot de Analítica de E‑commerce", anchor="content")
st.caption("Hazme una pregunta sobre las métricas de productos y ventas.")

# -----------------------------------------------------------------------------
# ⚙️  UTILIDADES
# -----------------------------------------------------------------------------

def build_db_uri() -> str:
    """Construye el connection‑string de PostgreSQL usando variables de entorno."""
    host = os.getenv("POSTGRES_HOST", "postgres")
    port = os.getenv("POSTGRES_PORT", "5432")
    user = os.getenv("POSTGRES_USER", "arturo")
    password = os.getenv("POSTGRES_PASSWORD", "arturo")
    db = os.getenv("POSTGRES_DB", "ecommerce_gold")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"


def load_llm() -> ChatGoogleGenerativeAI:
    """Inicializa el modelo Gemini asegurando que exista la API‑key."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        st.error("La variable de entorno GOOGLE_API_KEY no está definida.")
        st.stop()

    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=api_key,
        temperature=0,  # respuestas deterministas para SQL
    )


# -----------------------------------------------------------------------------
# 🧠  LÓGICA PRINCIPAL DEL CHATBOT
# -----------------------------------------------------------------------------

def get_response_from_ai(user_question: str) -> str:
    """Genera una respuesta utilizando LangChain + agente SQL."""

    llm = load_llm()

    db_uri = build_db_uri()
    db = SQLDatabase.from_uri(db_uri)

    agent = create_sql_agent(
        llm=llm,
        db=db,
        agent_type="openai-tools",
        verbose=os.getenv("DEBUG", "false").lower() == "true",
    )
    
    try:
        result: Dict[str, str] = agent.invoke({"input": user_question})
        return result.get("output", "No se pudo obtener una respuesta.")
    except Exception as exc:
        return f"Ha ocurrido un error: {exc}"


# -----------------------------------------------------------------------------
# 💬  INTERFAZ DE CHAT
# -----------------------------------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "¿En qué puedo ayudarte hoy?"}
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Prompt del usuario ───────────────────────────────────────────────────────────
if prompt := st.chat_input(
    "Ej: ¿Cuáles fueron los 5 productos con más ingresos el 1 de abril de 2020?"
):
    # Añadir mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generar respuesta
    with st.chat_message("assistant"):
        with st.spinner("Pensando…"):
            response = get_response_from_ai(prompt)
            st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
