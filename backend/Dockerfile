FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN apt-get update && apt-get install -y tesseract-ocr && pip install -r requirements.txt
COPY . .
CMD ["bash","-lc","alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
