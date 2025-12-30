# Basis Image
FROM python:3.11-slim

# Arbeitsverzeichnis
WORKDIR /app

# Umgebungsvariablen für Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Abhängigkeiten installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Quellcode kopieren
COPY . .

# User anlegen für Sicherheit (optional aber empfohlen)
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# Startbefehl
ENTRYPOINT ["python", "mcp_server.py"]
