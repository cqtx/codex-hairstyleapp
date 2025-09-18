FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY source/backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY source/backend/ ./

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
