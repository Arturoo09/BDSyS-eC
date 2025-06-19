FROM python:3.11-slim AS builder
RUN apt-get update && \
    apt-get install -y build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock /tmp/
RUN pip install --no-cache-dir uv && \
    uv pip compile --extra streamlit /tmp/pyproject.toml -o /tmp/req.txt && \
    pip install --no-cache-dir --prefix=/install -r /tmp/req.txt

FROM python:3.11-slim AS runtime
ENV PYTHONUNBUFFERED=1

RUN adduser --disabled-password --gecos '' appuser
WORKDIR /app
COPY --from=builder /install /usr/local
COPY . .
USER appuser
EXPOSE 8501
HEALTHCHECK CMD curl -f http://localhost:8501/_stcore/health || exit 1
CMD ["streamlit", "run", "chatbot_app.py", "--server.port=8501", "--server.address=0.0.0.0"]