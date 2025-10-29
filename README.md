# MLOps Docflow - Промышленная MLOps-платформа для классификации документов

![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)
![MLflow](https://img.shields.io/badge/MLflow-2.9-orange.svg)
![Airflow](https://img.shields.io/badge/Airflow-2.8-red.svg)

Полноценная production-ready MLOps платформа для распознавания и классификации документов с использованием современных инструментов машинного обучения и оркестрации.

## 📋 Содержание

- [Возможности](#-возможности)
- [Архитектура](#-архитектура)
- [Технологический стек](#-технологический-стек)
- [Установка и запуск](#-установка-и-запуск)
- [Использование API](#-использование-api)
- [Структура проекта](#-структура-проекта)
- [Мониторинг](#-мониторинг)
- [Разработка](#-разработка)

## 🚀 Возможности

- **Загрузка документов**: Автоматическая загрузка и валидация документов (изображения, PDF)
- **OCR обработка**: Извлечение текста с помощью Tesseract и EasyOCR
- **Классификация ML**: Обучение и инференс моделей классификации документов
- **MLOps инфраструктура**: 
  - Трекинг экспериментов через MLflow
  - Оркестрация пайплайнов через Airflow
  - Версионирование моделей
- **Мониторинг**: Prometheus + Grafana для отслеживания метрик
- **REST API**: FastAPI для интеграции с внешними системами
- **Хранилище**: MinIO (S3-совместимое) для документов и артефактов

## 🏗️ Архитектура

Проект построен на микросервисной архитектуре:

```
┌─────────────────┐
│   FastAPI API   │  ← HTTP запросы
└────────┬────────┘
         │
    ┌────┴────┐
    │  Airflow │  ← Оркестрация
    └────┬────┘
         │
    ┌────┴──────────────────────────┐
    │                               │
┌───▼────┐  ┌──────┐  ┌─────────┐ ┌▼────────┐
│Ingestion│  │ OCR  │  │Training │ │Inference│
└───┬────┘  └──┬───┘  └────┬────┘ └────┬────┘
    │          │           │           │
    └──────────┴───────────┴───────────┘
               │
    ┌──────────┴───────────┐
    │                      │
┌───▼────┐  ┌─────────┐  ┌▼──────┐
│PostgreSQL│  │  MinIO  │  │MLflow │
└─────────┘  └─────────┘  └───────┘
```

### Модули

1. **Ingestion** - Загрузка и валидация документов
2. **OCR** - Извлечение текста (Tesseract/EasyOCR)
3. **Training** - Обучение моделей классификации
4. **Inference** - Предсказание классов документов
5. **Monitoring** - Сбор метрик и мониторинг

## 🛠️ Технологический стек

### Backend & ML
- **Python 3.11** - Основной язык
- **FastAPI** - REST API
- **PyTorch** - Deep Learning фреймворк
- **Scikit-learn** - ML алгоритмы
- **Tesseract/EasyOCR** - OCR движки

### MLOps
- **Apache Airflow** - Оркестрация пайплайнов
- **MLflow** - Трекинг экспериментов и версионирование моделей
- **Prometheus** - Сбор метрик
- **Grafana** - Визуализация метрик

### Инфраструктура
- **Docker & Docker Compose** - Контейнеризация
- **PostgreSQL** - Основная БД
- **MinIO** - S3-совместимое хранилище
- **Nginx** (опционально) - Reverse proxy

## 🚀 Установка и запуск

### Предварительные требования

- Docker 20.10+
- Docker Compose 2.0+
- 8 GB RAM минимум
- 20 GB свободного места на диске

### Быстрый старт

1. **Клонирование репозитория**

```bash
git clone https://github.com/shuldeshoff/doc-mlops-pipeline.git
cd doc-mlops-pipeline
```

2. **Настройка переменных окружения**

```bash
cp .env.example .env
# Отредактируйте .env файл при необходимости
```

3. **Запуск сервисов**

```bash
# Запуск всех сервисов
docker-compose up -d

# Проверка статуса
docker-compose ps
```

4. **Ожидание инициализации**

Первый запуск может занять 5-10 минут для инициализации всех сервисов.

```bash
# Проверка логов
docker-compose logs -f
```

5. **Доступ к сервисам**

После запуска доступны следующие интерфейсы:

| Сервис | URL | Логин/Пароль |
|--------|-----|--------------|
| API Documentation | http://localhost:8000/docs | - |
| Airflow | http://localhost:8080 | admin/admin |
| MLflow | http://localhost:5000 | - |
| MinIO Console | http://localhost:9001 | minioadmin/minioadmin123 |
| Prometheus | http://localhost:9090 | - |
| Grafana | http://localhost:3000 | admin/admin |

## 📖 Использование API

### Swagger UI

Полная документация API доступна по адресу: http://localhost:8000/docs

### Примеры запросов

#### 1. Health Check

```bash
curl -X GET "http://localhost:8000/health"
```

#### 2. Загрузка документа

```bash
curl -X POST "http://localhost:8000/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.jpg"
```

Ответ:
```json
{
  "success": true,
  "document_id": 1,
  "filename": "document.jpg",
  "storage_path": "raw/20241029_120000_abc12345.jpg",
  "file_size": 2048576,
  "timestamp": "2024-10-29T12:00:00"
}
```

#### 3. Предсказание по тексту

```bash
curl -X POST "http://localhost:8000/predict/text" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Текст документа для классификации",
    "return_all_scores": true
  }'
```

Ответ:
```json
{
  "success": true,
  "predicted_class": "invoice",
  "confidence_score": 0.95,
  "is_confident": true,
  "model_name": "document_classifier",
  "model_version": "latest",
  "all_scores": {
    "invoice": 0.95,
    "contract": 0.03,
    "receipt": 0.02
  }
}
```

#### 4. Загрузка и предсказание (одним запросом)

```bash
curl -X POST "http://localhost:8000/upload-and-predict?ocr_language=eng" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.jpg"
```

#### 5. Предсказание по ID документа

```bash
curl -X POST "http://localhost:8000/predict/document/1?ocr_language=eng&return_all_scores=true"
```

#### 6. Получение истории предсказаний

```bash
curl -X GET "http://localhost:8000/prediction/history/1?limit=10"
```

### Python клиент

```python
import requests
from pathlib import Path

# URL API
API_URL = "http://localhost:8000"

# Загрузка и предсказание
def upload_and_predict(file_path: str):
    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(
            f"{API_URL}/upload-and-predict",
            files=files,
            params={'ocr_language': 'eng', 'return_all_scores': True}
        )
    
    return response.json()

# Использование
result = upload_and_predict("my_document.jpg")
print(f"Predicted class: {result['prediction']['predicted_class']}")
print(f"Confidence: {result['prediction']['confidence_score']}")
```

## 📁 Структура проекта

```
doc-mlops-pipeline/
├── airflow/                    # Airflow DAGs
│   └── dags/
│       └── document_processing_pipeline.py
├── config/                     # Конфигурационные файлы
│   ├── init-db.sql            # Инициализация БД
│   ├── prometheus.yml         # Конфиг Prometheus
│   └── grafana-datasources.yml
├── data/                       # Данные (git ignored)
│   ├── raw/                   # Сырые документы
│   ├── processed/             # Обработанные документы
│   └── models/                # Обученные модели
├── docker/                     # Dockerfile'ы
│   ├── airflow.Dockerfile
│   ├── inference.Dockerfile
│   └── mlflow.Dockerfile
├── logs/                       # Логи приложений
├── services/                   # Микросервисы
│   ├── ingestion/             # Модуль загрузки документов
│   │   ├── __init__.py
│   │   ├── ingestion_service.py
│   │   ├── storage.py
│   │   └── database.py
│   ├── ocr/                   # Модуль OCR
│   │   ├── __init__.py
│   │   ├── ocr_service.py
│   │   ├── ocr_engines.py
│   │   └── database.py
│   ├── training/              # Модуль обучения
│   │   ├── __init__.py
│   │   ├── training_service.py
│   │   ├── models.py
│   │   └── database.py
│   ├── inference/             # Модуль inference
│   │   ├── __init__.py
│   │   ├── main.py           # FastAPI приложение
│   │   ├── inference_service.py
│   │   ├── model_loader.py
│   │   └── database.py
│   └── monitoring/            # Модуль мониторинга
│       ├── __init__.py
│       ├── metrics_service.py
│       ├── performance_monitor.py
│       └── database.py
├── .env                        # Переменные окружения
├── .gitignore
├── docker-compose.yml          # Docker Compose конфигурация
├── requirements.txt            # Python зависимости
└── README.md                   # Этот файл
```

## 📊 Мониторинг

### Prometheus метрики

Доступны следующие метрики:

- `documents_uploaded_total` - Количество загруженных документов
- `documents_processed_total` - Количество обработанных документов
- `ocr_processing_seconds` - Время обработки OCR
- `ocr_confidence_score` - Confidence score OCR
- `prediction_confidence_score` - Confidence score предсказаний
- `predictions_total` - Количество предсказаний по классам
- `model_accuracy` - Текущая точность модели
- `api_request_duration_seconds` - Длительность API запросов

### Grafana Dashboard

1. Откройте Grafana: http://localhost:3000
2. Войдите (admin/admin)
3. Добавьте дашборд для визуализации метрик
4. Используйте Prometheus как источник данных

### Логи

Просмотр логов сервисов:

```bash
# Все сервисы
docker-compose logs -f

# Конкретный сервис
docker-compose logs -f inference-api
docker-compose logs -f airflow-scheduler
docker-compose logs -f mlflow
```

## 🔧 Разработка

### Локальная разработка

1. **Установка зависимостей**

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Запуск API локально**

```bash
cd services/inference
python main.py
```

3. **Запуск тестов** (при наличии)

```bash
pytest tests/
```

### Добавление нового модуля

1. Создайте директорию в `services/`
2. Добавьте `__init__.py` и основные файлы
3. Обновите `requirements.txt` при необходимости
4. Добавьте интеграцию в Airflow DAG

### Обучение модели

Модель обучается автоматически через Airflow DAG, но можно запустить вручную:

```python
from services.training.training_service import TrainingService

service = TrainingService()
texts, labels = service.load_training_data()
result = service.train_model(texts, labels, epochs=50)
print(f"Model accuracy: {result['accuracy']:.4f}")
```

## 🔒 Безопасность

### Рекомендации для production

1. **Измените пароли по умолчанию** в `.env`:
   - PostgreSQL
   - MinIO
   - Airflow
   - Grafana

2. **Используйте HTTPS** для всех внешних API

3. **Настройте firewall** для ограничения доступа

4. **Включите аутентификацию** для API endpoints

5. **Регулярно обновляйте** зависимости

```bash
pip install --upgrade -r requirements.txt
```

## 🐛 Troubleshooting

### Проблемы с запуском

**Ошибка: "port already allocated"**
```bash
# Остановите конфликтующие сервисы или измените порты в docker-compose.yml
docker-compose down
```

**Ошибка: "no space left on device"**
```bash
# Очистите неиспользуемые Docker ресурсы
docker system prune -a
```

**Airflow задачи не запускаются**
```bash
# Перезапустите scheduler
docker-compose restart airflow-scheduler
```

### Проблемы с моделью

**Модель не загружается**
- Проверьте наличие файлов модели в `data/models/`
- Проверьте логи inference API

**Низкая точность модели**
- Увеличьте размер обучающей выборки
- Настройте гиперпараметры в `training_service.py`

## 📚 Дополнительные ресурсы

- [FastAPI документация](https://fastapi.tiangolo.com/)
- [Apache Airflow](https://airflow.apache.org/)
- [MLflow](https://mlflow.org/)
- [Prometheus](https://prometheus.io/)
- [MinIO](https://min.io/)

## 📝 Лицензия

MIT License

## 👥 Автор

**Шульдешов Юрий Леонидович**
- Telegram: [@shuldeshoff](https://t.me/shuldeshoff)
- GitHub: [@shuldeshoff](https://github.com/shuldeshoff)

## 🤝 Contributing

Pull requests are welcome!  
Please open an issue first to discuss proposed changes.  
Follow code style and use clear commit messages.

Подробнее о процессе участия читайте в [CONTRIBUTING.md](CONTRIBUTING.md).

---

**Создано с ❤️ для MLOps сообщества**

