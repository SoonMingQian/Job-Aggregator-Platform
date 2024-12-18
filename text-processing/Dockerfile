FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

ENV FLASK_APP=app.py

# Add healthcheck script
COPY wait_for_kafka.py .
RUN chmod +x wait_for_kafka.py

CMD ["python", "wait_for_kafka.py"]