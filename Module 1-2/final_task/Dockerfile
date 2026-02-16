FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY todo_service_app ./todo_service_app

VOLUME ["/app/data"]

EXPOSE 80

CMD ["uvicorn", "todo_service_app.main:app", "--host", "0.0.0.0", "--port", "80"]