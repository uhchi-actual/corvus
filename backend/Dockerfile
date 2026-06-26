FROM python:3.12-slim

WORKDIR /app/backend

COPY backend/pyproject.toml ./pyproject.toml
COPY backend/src ./src

RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

