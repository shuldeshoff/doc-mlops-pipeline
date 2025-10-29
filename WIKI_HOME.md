# MLOps Docflow - Production-Ready MLOps Platform

> Промышленная MLOps-платформа для автоматизированного распознавания и классификации документов

[![CI](https://github.com/shuldeshoff/doc-mlops-pipeline/workflows/CI/badge.svg)](https://github.com/shuldeshoff/doc-mlops-pipeline/actions)
[![License](https://img.shields.io/github/license/shuldeshoff/doc-mlops-pipeline)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

---

## 🎯 Что такое MLOps Docflow?

**MLOps Docflow** — это полнофункциональная платформа машинного обучения, предназначенная для автоматической обработки, распознавания и классификации документов в промышленных масштабах.

### Основные возможности

📄 **Обработка документов**
- Загрузка изображений и PDF файлов
- Автоматическая валидация и предобработка
- Хранение в S3-совместимом хранилище (MinIO)

🔍 **OCR (Распознавание текста)**
- Поддержка двух движков: Tesseract и EasyOCR
- Многоязычное распознавание (английский, русский)
- Высокая точность через ансамблевый подход

🤖 **Машинное обучение**
- Автоматическое обучение моделей классификации
- Версионирование моделей через MLflow
- Continuous training pipeline

⚡ **Inference API**
- REST API на FastAPI
- Real-time предсказания
- Batch processing
- Swagger документация

📊 **MLOps Infrastructure**
- Трекинг экспериментов (MLflow)
- Оркестрация пайплайнов (Apache Airflow)
- Мониторинг и метрики (Prometheus + Grafana)
- Контейнеризация (Docker)

---

## 🏗️ Архитектура

MLOps Docflow построен на микросервисной архитектуре с пятью основными компонентами:

```
┌─────────────────────────────────────────────────────────┐
│                     FastAPI REST API                     │
│              (http://localhost:8000/docs)                │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │   Apache Airflow DAG    │
        │   (Orchestration)       │
        └────────┬────────────────┘
                 │
    ┌────────────┼────────────┬───────────┬─────────────┐
    │            │            │           │             │
┌───▼───┐  ┌────▼───┐  ┌─────▼────┐  ┌──▼──────┐  ┌───▼──────┐
│Ingestion│ │  OCR   │  │ Training │  │Inference│  │Monitoring│
│Service  │ │Service │  │ Service  │  │ Service │  │ Service  │
└───┬───┘  └────┬───┘  └─────┬────┘  └──┬──────┘  └───┬──────┘
    │           │            │           │             │
    └───────────┴────────────┴───────────┴─────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
    ┌───▼────┐         ┌────▼────┐        ┌────▼────┐
    │PostgreSQL│        │  MinIO  │        │ MLflow  │
    │   (DB)  │        │   (S3)  │        │(Tracking)│
    └─────────┘        └─────────┘        └─────────┘
```

### Модули системы

| Модуль | Назначение | Технологии |
|--------|-----------|-----------|
| **Ingestion** | Загрузка и валидация документов | Python, MinIO, PostgreSQL |
| **OCR** | Извлечение текста из изображений | Tesseract, EasyOCR, OpenCV |
| **Training** | Обучение ML моделей | PyTorch, Scikit-learn, MLflow |
| **Inference** | Предсказание классов документов | FastAPI, PyTorch |
| **Monitoring** | Сбор метрик и мониторинг | Prometheus, Grafana |

---

## 🚀 Быстрый старт

### Запуск за 3 команды

```bash
# 1. Клонировать репозиторий
git clone https://github.com/shuldeshoff/doc-mlops-pipeline.git
cd doc-mlops-pipeline

# 2. Запустить все сервисы
docker-compose up -d

# 3. Проверить статус
curl http://localhost:8000/health
```

### Доступ к сервисам

| Сервис | URL | Credentials |
|--------|-----|-------------|
| 🌐 **API Docs** | http://localhost:8000/docs | - |
| 🔄 **Airflow** | http://localhost:8080 | admin / admin |
| 📊 **MLflow** | http://localhost:5000 | - |
| 📦 **MinIO Console** | http://localhost:9001 | minioadmin / minioadmin123 |
| 📈 **Prometheus** | http://localhost:9090 | - |
| 📉 **Grafana** | http://localhost:3000 | admin / admin |

---

## 💡 Примеры использования

### Загрузка и классификация документа

```python
import requests

# Загрузка файла
with open('invoice.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/upload-and-predict',
        files={'file': f},
        params={'ocr_language': 'eng'}
    )

result = response.json()
print(f"Класс: {result['prediction']['predicted_class']}")
print(f"Уверенность: {result['prediction']['confidence_score']:.2%}")
```

### Классификация по тексту

```python
response = requests.post(
    'http://localhost:8000/predict/text',
    json={
        'text': 'Invoice #12345 Total: $500.00',
        'return_all_scores': True
    }
)
```

### Batch обработка

```python
# Загрузка нескольких документов
document_ids = []
for file_path in ['doc1.jpg', 'doc2.jpg', 'doc3.jpg']:
    with open(file_path, 'rb') as f:
        result = requests.post('http://localhost:8000/upload', files={'file': f})
        document_ids.append(result.json()['document_id'])

# Обработка через Airflow DAG автоматически
```

---

## 📚 Технологический стек

### Backend & ML
- **Python 3.11** - Основной язык программирования
- **FastAPI** - Современный web framework для API
- **PyTorch** - Deep Learning framework
- **Scikit-learn** - Machine Learning библиотека
- **Tesseract & EasyOCR** - OCR движки

### MLOps Tools
- **Apache Airflow 2.8** - Оркестрация ML пайплайнов
- **MLflow 2.9** - Experiment tracking и model registry
- **Prometheus** - Сбор метрик и мониторинг
- **Grafana** - Визуализация метрик и dashboards

### Infrastructure
- **Docker & Docker Compose** - Контейнеризация
- **PostgreSQL 15** - Основная реляционная БД
- **MinIO** - S3-совместимое object storage
- **Nginx** - Reverse proxy (опционально)

---

## 🎯 Use Cases (Примеры применения)

### 1. Обработка счетов (Invoices)
```
Загрузка счета → OCR → Извлечение суммы → Классификация типа → Валидация
```

### 2. Анализ контрактов
```
PDF контракт → Извлечение текста → Определение типа контракта → Поиск ключевых пунктов
```

### 3. Цифровизация чеков
```
Фото чека → OCR → Распознавание товаров → Суммирование → Сохранение в БД
```

### 4. Классификация корреспонденции
```
Скан письма → OCR → Определение отправителя → Классификация темы → Routing
```

---

## 📊 Производительность

### Метрики системы

| Метрика | Значение |
|---------|----------|
| **OCR скорость** | ~2-5 сек на документ |
| **Inference латентность** | <100ms |
| **Throughput** | 100+ документов/мин |
| **Model accuracy** | 85-95% (зависит от данных) |
| **API availability** | 99.9% (при правильном деплое) |

---

## 🛠️ Разработка и контрибуции

### Как начать контрибьютить?

1. 📖 Прочитайте [Contributing Guide](https://github.com/shuldeshoff/doc-mlops-pipeline/blob/main/CONTRIBUTING.md)
2. 🐛 Найдите [good first issue](https://github.com/shuldeshoff/doc-mlops-pipeline/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)
3. 🍴 Форкните репозиторий
4. 🌿 Создайте feature branch
5. 💻 Внесите изменения
6. ✅ Создайте Pull Request

### Стандарты кода

```bash
# Форматирование
black services/

# Линтинг
flake8 services/ --max-line-length=100

# Тесты
pytest tests/ --cov=services
```

---

## 📖 Документация

### Основные разделы Wiki

- 🏠 **[Home](Home)** - Эта страница
- 🏗️ **[Architecture](Architecture)** - Детальная архитектура
- 📡 **[API Documentation](API-Documentation)** - Полное описание API
- 🚀 **[Deployment](Deployment)** - Production deployment
- 🔧 **[Configuration](Configuration)** - Настройка системы
- 🧪 **[Development Guide](Development-Guide)** - Гайд для разработчиков
- ❓ **[FAQ](FAQ)** - Часто задаваемые вопросы
- 🐛 **[Troubleshooting](Troubleshooting)** - Решение проблем

### Внешние ресурсы

- 📝 [README.md](https://github.com/shuldeshoff/doc-mlops-pipeline#readme) - Основная документация
- ⚡ [QUICKSTART.md](https://github.com/shuldeshoff/doc-mlops-pipeline/blob/main/QUICKSTART.md) - Быстрый старт
- 🤝 [CONTRIBUTING.md](https://github.com/shuldeshoff/doc-mlops-pipeline/blob/main/CONTRIBUTING.md) - Гайд для контрибьюторов
- 🔒 [SECURITY.md](https://github.com/shuldeshoff/doc-mlops-pipeline/blob/main/SECURITY.md) - Политика безопасности

---

## 💬 Сообщество и поддержка

### Где получить помощь?

- 💭 **[GitHub Discussions](https://github.com/shuldeshoff/doc-mlops-pipeline/discussions)** - Вопросы и обсуждения
- 🐛 **[GitHub Issues](https://github.com/shuldeshoff/doc-mlops-pipeline/issues)** - Баги и предложения
- 📱 **[Telegram](https://t.me/shuldeshoff)** - Прямая связь с автором

### Контакты автора

**Шульдешов Юрий Леонидович**
- GitHub: [@shuldeshoff](https://github.com/shuldeshoff)
- Telegram: [@shuldeshoff](https://t.me/shuldeshoff)

---

## 🗺️ Roadmap

### ✅ Текущая версия (v1.0)
- Базовая обработка документов
- OCR с двумя движками
- ML классификация
- REST API
- Airflow оркестрация
- MLflow tracking
- Prometheus мониторинг

### 🚧 В разработке (v1.1)
- [ ] Kubernetes deployment
- [ ] PDF multi-page support
- [ ] Advanced authentication
- [ ] Rate limiting
- [ ] Grafana dashboards
- [ ] Model A/B testing

### 🔮 Будущие планы (v2.0)
- [ ] Multi-tenancy support
- [ ] Advanced NLP features
- [ ] Document comparison
- [ ] Automated data labeling
- [ ] GraphQL API
- [ ] Web UI for management

---

## 📜 Лицензия

Проект распространяется под [MIT License](https://github.com/shuldeshoff/doc-mlops-pipeline/blob/main/LICENSE).

Свободен для использования в коммерческих и некоммерческих проектах.

---

## 🌟 Star History

Если проект вам понравился, поставьте ⭐ на GitHub!

[![Star History Chart](https://api.star-history.com/svg?repos=shuldeshoff/doc-mlops-pipeline&type=Date)](https://star-history.com/#shuldeshoff/doc-mlops-pipeline&Date)

---

## 🙏 Благодарности

Проект использует следующие open-source библиотеки:
- Apache Airflow
- MLflow
- FastAPI
- PyTorch
- Tesseract OCR
- EasyOCR
- И многие другие...

---

**Последнее обновление:** 29 октября 2024  
**Версия документации:** 1.0  
**Автор:** Шульдешов Юрий Леонидович

---

<div align="center">

**[⬆ Наверх](#mlops-docflow---production-ready-mlops-platform)**

Made with ❤️ for the MLOps community

</div>

