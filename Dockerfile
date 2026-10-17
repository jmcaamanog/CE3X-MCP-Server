# Dockerfile oficial para despliegue de CE3X-MCP-Server en Glama.ai, Docker Hub y Cloud
FROM python:3.11-slim

WORKDIR /app

# Optimización de ejecución de Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Dependencias mínimas del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar manifiesto y código fuente
COPY pyproject.toml README.md ./
COPY src ./src

# Instalación del servidor MCP
RUN pip install --no-cache-dir .

# Puerto para modo SSE / Streamable HTTP (inspección web en Glama)
EXPOSE 8000

# Punto de entrada predeterminado en modo stdio (o SSE según parámetros)
ENTRYPOINT ["ce3x-mcp"]
