import os
import streamlit as st

from langchain_community.utilities import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.agent_toolkits import create_sql_agent

# --- Configuración de la Página de Streamlit ---
st.set_page_config(page_title="Chatbot de E-commerce", page_icon="🤖", layout="centered")
st.title("🤖 Chatbot de Analítica de E-commerce", width="content")
st.caption("Hazme una pregunta sobre las métricas de productos y ventas.")

# --- Lógica del Chatbot (El Cerebro) ---

def build_db_uri() -> str:
    """Devuelve el connection-string a partir de las vars de entorno."""
    host     = os.getenv("POSTGRES_HOST", "postgres")
    port     = os.getenv("POSTGRES_PORT", "5432")
    user     = os.getenv("POSTGRES_USER", "arturo")
    password = os.getenv("POSTGRES_PASSWORD", "arturo")
    db       = os.getenv("POSTGRES_DB", "ecommerce_gold")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"

def get_response_from_ai(user_question: str):
    os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY", "")

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0,
        convert_system_message_to_human=True,
    )
    
    db_uri = build_db_uri()
    print(f"Conectando a {db_uri}")

    db = SQLDatabase.from_uri(db_uri)

    agent_executor = create_sql_agent(
        llm=llm,
        db=db,
        agent_type="openai-tools",
        verbose=os.getenv("DEBUG", "false").lower() == "true",
    )

    return agent_executor.run(user_question)


# --- Interfaz de Usuario de Streamlit ---

# Inicializar el historial del chat si no existe
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "¿En qué puedo ayudarte hoy?"}]

# Mostrar mensajes previos en la interfaz
for message in st.session_state.messages:
    with st.chat_message(message["role"]): 
        st.markdown(message["content"])

# Obtener nueva entrada del usuario
if prompt := st.chat_input("Ej: ¿Cuáles fueron los 5 productos con más ingresos el 1 de abril de 2020?"):
    # Añadir y mostrar el mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generar y mostrar la respuesta del asistente
    with st.chat_message("assistant"):
        # Mostrar un indicador de carga mientras se procesa la respuesta
        with st.spinner("Pensando..."):
            response = get_response_from_ai(prompt)
            st.markdown(response)
    
    # Añadir la respuesta del asistente al historial
    st.session_state.messages.append({"role": "assistant", "content": response})