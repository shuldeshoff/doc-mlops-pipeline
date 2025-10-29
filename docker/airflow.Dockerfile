FROM apache/airflow:2.8.1-python3.11

USER root

# Установка системных зависимостей для OCR и CV
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-rus \
    tesseract-ocr-eng \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

USER airflow

# Копирование requirements
COPY requirements.txt /requirements.txt

# Установка Python зависимостей
RUN pip install --no-cache-dir -r /requirements.txt

# Инициализация Airflow DB
RUN airflow db init && \
    airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com \
    --password admin || true

