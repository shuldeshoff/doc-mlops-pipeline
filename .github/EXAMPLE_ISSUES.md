# Примеры Issue для создания

После создания репозитория, создайте следующие Issue для привлечения контрибьюторов:

## Good First Issues

### 1. Добавить примеры использования API в README
**Labels:** `good first issue`, `documentation`
**Description:**
```
Добавить в README.md раздел с практическими примерами использования API на разных языках программирования (Python, JavaScript, curl).

Что нужно сделать:
- [ ] Пример загрузки документа на Python
- [ ] Пример batch обработки
- [ ] Пример на JavaScript/Node.js
- [ ] Обновить документацию с примерами ошибок и их обработкой

Файлы для изменения:
- README.md
```

### 2. Улучшить логирование в модуле OCR
**Labels:** `good first issue`, `enhancement`, `services/ocr`
**Description:**
```
Добавить более детальное логирование в OCR сервис для упрощения отладки.

Что нужно сделать:
- [ ] Добавить логирование времени обработки каждого этапа
- [ ] Логировать размер входного изображения
- [ ] Логировать использованный OCR движок
- [ ] Добавить уровни логирования (DEBUG, INFO, WARNING, ERROR)

Файлы для изменения:
- services/ocr/ocr_service.py
- services/ocr/ocr_engines.py
```

### 3. Создать unit тесты для модуля storage
**Labels:** `good first issue`, `tests`, `services/ingestion`
**Description:**
```
Написать unit тесты для MinIOStorage класса.

Что нужно сделать:
- [ ] Тест для загрузки файла
- [ ] Тест для скачивания файла
- [ ] Тест для проверки существования файла
- [ ] Тест для удаления файла
- [ ] Использовать mocking для MinIO

Создать файл:
- tests/test_storage.py
```

### 4. Добавить валидацию входных данных в API
**Labels:** `good first issue`, `enhancement`, `services/inference`
**Description:**
```
Улучшить валидацию входных параметров в FastAPI эндпоинтах.

Что нужно сделать:
- [ ] Добавить проверку размера файла перед обработкой
- [ ] Валидация поддерживаемых форматов файлов
- [ ] Добавить более информативные сообщения об ошибках
- [ ] Добавить примеры ошибок в Swagger документацию

Файлы для изменения:
- services/inference/main.py
```

## Help Wanted

### 5. Реализовать поддержку PDF документов
**Labels:** `help wanted`, `enhancement`, `services/ocr`
**Description:**
```
Добавить поддержку многостраничных PDF документов в OCR модуль.

Что нужно сделать:
- [ ] Конвертация PDF в изображения
- [ ] OCR обработка каждой страницы
- [ ] Объединение результатов
- [ ] Добавить метаданные о страницах
- [ ] Тесты для PDF обработки

Зависимости:
- pdf2image
- PyPDF2

Новые файлы:
- services/ocr/pdf_processor.py
```

### 6. Добавить Grafana дашборд
**Labels:** `help wanted`, `monitoring`, `enhancement`
**Description:**
```
Создать Grafana дашборд для визуализации метрик системы.

Что нужно сделать:
- [ ] Дашборд для метрик API (requests, latency, errors)
- [ ] Дашборд для OCR метрик (confidence, processing time)
- [ ] Дашборд для ML моделей (accuracy, predictions)
- [ ] Дашборд для инфраструктуры (CPU, memory, disk)
- [ ] Экспорт конфигурации дашборда в JSON

Файлы для создания:
- config/grafana/dashboards/api-metrics.json
- config/grafana/dashboards/ml-metrics.json
```

### 7. Реализовать batch prediction API endpoint
**Labels:** `help wanted`, `enhancement`, `services/inference`
**Description:**
```
Добавить эндпоинт для batch предсказаний с оптимизацией производительности.

Что нужно сделать:
- [ ] Новый POST /predict/batch эндпоинт
- [ ] Принимать массив document_ids
- [ ] Параллельная обработка с использованием async
- [ ] Rate limiting для больших батчей
- [ ] Прогресс-бар или статус обработки
- [ ] Документация и примеры

Файлы для изменения:
- services/inference/main.py
- services/inference/inference_service.py
```

### 8. Добавить поддержку Kubernetes deployment
**Labels:** `help wanted`, `infrastructure`, `documentation`
**Description:**
```
Создать Kubernetes манифесты для деплоя в production.

Что нужно сделать:
- [ ] Kubernetes manifests (Deployments, Services, ConfigMaps)
- [ ] Helm chart для упрощенного деплоя
- [ ] Инструкции по деплою в README
- [ ] Настройка Horizontal Pod Autoscaler
- [ ] Ingress конфигурация
- [ ] Persistent Volume Claims для данных

Новая директория:
- k8s/
  - deployments/
  - services/
  - configmaps/
  - helm/
```

## Enhancement

### 9. Оптимизация производительности OCR
**Labels:** `enhancement`, `performance`, `services/ocr`
**Description:**
```
Улучшить производительность OCR обработки.

Идеи для оптимизации:
- [ ] Кэширование результатов OCR
- [ ] Параллельная обработка батчей
- [ ] Использование GPU для EasyOCR
- [ ] Предварительная загрузка моделей
- [ ] Оптимизация размера изображений

Профилирование:
- Измерить текущую производительность
- Найти узкие места
- Оптимизировать критические участки
- Измерить улучшения
```

### 10. Добавить метрики качества модели в real-time
**Labels:** `enhancement`, `monitoring`, `services/inference`
**Description:**
```
Реализовать real-time мониторинг качества предсказаний модели.

Что нужно сделать:
- [ ] Отслеживание distribution shift
- [ ] Мониторинг confidence scores
- [ ] Детектирование аномальных предсказаний
- [ ] Алерты при падении качества
- [ ] Дашборд для визуализации

Файлы для изменения:
- services/monitoring/metrics_service.py
- config/prometheus.yml
```

---

## Как создать эти Issue

1. Перейдите в [Issues](https://github.com/shuldeshoff/doc-mlops-pipeline/issues)
2. Нажмите "New issue"
3. Скопируйте текст из примеров выше
4. Добавьте соответствующие labels
5. Сохраните

## Метки для использования

Создайте следующие labels в репозитории:

- `good first issue` (зеленый) - хорошо для первого вклада
- `help wanted` (синий) - требуется помощь
- `documentation` (серый) - документация
- `enhancement` (фиолетовый) - новая функциональность
- `bug` (красный) - баг
- `tests` (желтый) - тесты
- `performance` (оранжевый) - производительность
- `monitoring` (голубой) - мониторинг
- `infrastructure` (коричневый) - инфраструктура
- `services/ingestion` - модуль ingestion
- `services/ocr` - модуль OCR
- `services/training` - модуль training
- `services/inference` - модуль inference
- `services/monitoring` - модуль monitoring

