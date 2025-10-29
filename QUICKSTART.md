# Быстрый старт MLOps Docflow

## За 5 минут до работающей системы

### 1. Запуск системы

```bash
# Клонирование репозитория
git clone https://github.com/shuldeshoff/doc-mlops-pipeline.git
cd doc-mlops-pipeline

# Запуск всех сервисов
docker-compose up -d

# Ожидание инициализации (2-3 минуты)
docker-compose logs -f
```

### 2. Проверка работоспособности

```bash
# Проверка API
curl http://localhost:8000/health

# Должен вернуть:
# {
#   "status": "healthy",
#   "timestamp": "2024-10-29T12:00:00",
#   "model_loaded": false
# }
```

### 3. Загрузка и классификация документа

#### С помощью curl

```bash
curl -X POST "http://localhost:8000/upload-and-predict" \
  -F "file=@your_document.jpg" \
  -F "ocr_language=eng"
```

#### С помощью Python

```python
import requests

with open('document.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/upload-and-predict',
        files={'file': f},
        params={'ocr_language': 'eng'}
    )

print(response.json())
```

### 4. Доступ к интерфейсам

| Сервис | URL | Логин/Пароль |
|--------|-----|--------------|
| API Docs | http://localhost:8000/docs | - |
| Airflow | http://localhost:8080 | admin/admin |
| MLflow | http://localhost:5000 | - |
| MinIO | http://localhost:9001 | minioadmin/minioadmin123 |
| Grafana | http://localhost:3000 | admin/admin |

### 5. Обучение модели

Модель автоматически обучается через Airflow DAG. Для ручного запуска:

1. Откройте Airflow UI: http://localhost:8080
2. Найдите DAG `document_processing_pipeline`
3. Включите DAG и запустите вручную

### 6. Остановка системы

```bash
# Остановка всех сервисов
docker-compose down

# Полная очистка (включая данные)
docker-compose down -v
```

## Типичные сценарии использования

### Сценарий 1: Загрузка и получение результата

```bash
# 1. Загрузка документа
curl -X POST http://localhost:8000/upload \
  -F "file=@invoice.jpg" \
  > upload_result.json

# 2. Извлечение document_id
DOCUMENT_ID=$(cat upload_result.json | jq -r '.document_id')

# 3. Предсказание класса
curl -X POST "http://localhost:8000/predict/document/$DOCUMENT_ID?ocr_language=eng"
```

### Сценарий 2: Массовая загрузка

```bash
# Загрузка всех документов из директории
for file in documents/*.jpg; do
    curl -X POST http://localhost:8000/upload \
      -F "file=@$file"
    sleep 1
done
```

### Сценарий 3: Мониторинг системы

```bash
# Просмотр метрик Prometheus
curl http://localhost:9090/api/v1/query?query=documents_uploaded_total

# Просмотр логов
docker-compose logs -f inference-api
```

## Устранение проблем

### API не отвечает

```bash
# Проверка статуса контейнеров
docker-compose ps

# Перезапуск inference API
docker-compose restart inference-api

# Просмотр логов
docker-compose logs inference-api
```

### База данных не инициализировалась

```bash
# Ручная инициализация
docker-compose exec postgres psql -U mlops -d mlops_docflow \
  -f /docker-entrypoint-initdb.d/init-db.sql
```

### Модель не загружается

```bash
# Проверка наличия файлов модели
ls -la data/models/

# Если файлов нет - запустите обучение через Airflow
```

## Следующие шаги

1. Изучите полную документацию в [README.md](README.md)
2. Настройте Grafana дашборды для мониторинга
3. Добавьте свои классы документов и обучите модель
4. Интегрируйте API с вашими системами

## Полезные команды

```bash
# Makefile команды (если установлен make)
make up          # Запуск
make down        # Остановка
make logs        # Просмотр логов
make restart     # Перезапуск
make clean       # Полная очистка

# Прямые Docker команды
docker-compose ps              # Статус сервисов
docker-compose logs -f [service]  # Логи сервиса
docker-compose exec [service] bash  # Shell в контейнере
docker-compose restart [service]    # Перезапуск сервиса
```

---

**Готово! Теперь у вас работающая MLOps платформа! 🚀**

