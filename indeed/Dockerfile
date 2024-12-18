FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and its dependencies
RUN pip install playwright
RUN playwright install-deps
RUN playwright install

COPY . .

EXPOSE 3001

ENV FLASK_APP=app.py

# Add healthcheck script
COPY wait_for_kafka.py .
RUN chmod +x wait_for_kafka.py

CMD ["python", "wait_for_kafka.py"]