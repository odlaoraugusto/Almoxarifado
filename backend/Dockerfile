FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Roda a migration a cada start (idempotente — alembic só aplica o que
# falta) e sobe o servidor. Padrão de container: migrar em runtime, não
# em build time, já que o banco não é alcançável durante o build.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
