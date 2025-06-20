# ---- Etapa 1: Builder ----
FROM python:3.11-slim AS builder

# 1. Instala dependencias del sistema operativo.
RUN apt-get update && \
    apt-get install -y build-essential curl && \
    rm -rf /var/lib/apt/lists/*

# 2. Instala 'uv'.
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. CONFIGURA EL ENTORNO para que el sistema encuentre 'uv'.
ENV PATH="/root/.local/bin:$PATH"

# 4. Copia los ficheros de dependencias. Este paso es posterior para que
#    cambios en el código no invaliden la caché de las herramientas.
COPY pyproject.toml uv.lock /tmp/

# 5. Usa 'uv' para instalar las dependencias de Python.
RUN uv pip compile --extra streamlit /tmp/pyproject.toml -o /tmp/req.txt && \
    uv pip install --no-cache-dir --prefix=/install -r /tmp/req.txt

# ---- Etapa 2: Runtime ----
FROM python:3.11-slim AS runtime

ENV PYTHONUNBUFFERED=1

RUN adduser --disabled-password --gecos '' appuser

WORKDIR /app

COPY --from=builder /install /usr/local

COPY chatbot_app.py .

USER appuser

EXPOSE 8501
HEALTHCHECK CMD curl -f http://localhost:8501/_stcore/health || exit 1
CMD ["streamlit", "run", "chatbot_app.py", "--server.port=8501", "--server.address=0.0.0.0"]