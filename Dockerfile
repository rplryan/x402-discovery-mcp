FROM python:3.11-slim

LABEL org.opencontainers.image.title="x402 Discovery MCP Server"
LABEL org.opencontainers.image.description="MCP server for x402 Service Discovery API"
LABEL org.opencontainers.image.url="https://github.com/rplryan/x402-discovery-mcp"
LABEL org.opencontainers.image.source="https://github.com/rplryan/x402-discovery-mcp"
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .

CMD ["python", "server.py"]
