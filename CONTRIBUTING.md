# Contributing to MLOps Docflow

Спасибо за интерес к проекту! Мы рады любым предложениям по улучшению платформы.

## 🚀 Как начать

### 1. Форк репозитория

Создайте форк репозитория, нажав кнопку "Fork" в правом верхнем углу страницы GitHub.

```bash
# Клонируйте ваш форк
git clone https://github.com/YOUR_USERNAME/doc-mlops-pipeline.git
cd doc-mlops-pipeline

# Добавьте upstream remote
git remote add upstream https://github.com/shuldeshoff/doc-mlops-pipeline.git
```

### 2. Создайте ветку для изменений

Создайте новую ветку от `main` с понятным названием:

```bash
# Обновите main
git checkout main
git pull upstream main

# Создайте новую ветку
git checkout -b feature/your-feature-name
# или
git checkout -b fix/bug-description
```

**Конвенция именования веток:**
- `feature/` - новая функциональность
- `fix/` - исправление бага
- `docs/` - изменения в документации
- `refactor/` - рефакторинг кода
- `test/` - добавление тестов

### 3. Внесите изменения

#### Настройка окружения

```bash
# Создайте виртуальное окружение
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Установите зависимости
pip install -r requirements.txt

# Установите dev зависимости
pip install black flake8 pytest mypy
```

#### Стандарты кодирования

- **Форматирование:** Используйте `black` для форматирования Python кода
  ```bash
  black services/
  ```

- **Линтинг:** Проверьте код с помощью `flake8`
  ```bash
  flake8 services/ --max-line-length=100
  ```

- **Type hints:** Используйте type hints где это возможно
  ```python
  def process_document(doc_id: int) -> Dict[str, Any]:
      pass
  ```

- **Docstrings:** Документируйте функции и классы
  ```python
  def upload_file(self, file_path: str) -> bool:
      """
      Загрузка файла в хранилище.
      
      Args:
          file_path: Путь к файлу
          
      Returns:
          True если загрузка успешна
      """
      pass
  ```

#### Логирование

Используйте `loguru` для логирования:

```python
from loguru import logger

logger.info("Processing started")
logger.error(f"Error occurred: {error}")
```

#### Тестирование

Добавляйте тесты для новой функциональности:

```bash
# Запуск тестов
pytest tests/

# С покрытием
pytest tests/ --cov=services --cov-report=html
```

### 4. Коммит изменений

Используйте понятные сообщения коммитов:

```bash
git add .
git commit -m "feat: add batch processing for OCR service"
```

**Формат сообщений коммитов:**

```
<type>: <subject>

<body (optional)>

<footer (optional)>
```

**Типы коммитов:**
- `feat:` - новая функциональность
- `fix:` - исправление бага
- `docs:` - изменения в документации
- `style:` - форматирование кода
- `refactor:` - рефакторинг
- `test:` - добавление тестов
- `chore:` - обновление зависимостей, конфигурации

**Примеры:**

```bash
feat: add support for PDF documents in OCR service

fix: resolve memory leak in batch processing
Closes #123

docs: update API documentation with new endpoints

refactor: simplify model loading logic
```

### 5. Push и создание Pull Request

```bash
# Push в ваш форк
git push origin feature/your-feature-name
```

Перейдите на GitHub и создайте Pull Request:

1. Нажмите "Compare & pull request"
2. Выберите base: `main` ← compare: `feature/your-feature-name`
3. Заполните шаблон PR:
   - Опишите изменения
   - Укажите связанные Issue (если есть)
   - Добавьте скриншоты (если применимо)
4. Нажмите "Create pull request"

### 6. Ревью и обсуждение

- Владелец проекта проведет ревью вашего кода
- Будьте готовы к обсуждению и внесению правок
- Отвечайте на комментарии и вопросы
- После одобрения PR будет смержен в main

## 📋 Чем можно помочь

### Хорошие задачи для начала (Good First Issues)

- Улучшение документации
- Добавление примеров использования
- Написание тестов
- Исправление мелких багов
- Улучшение логирования

Ищите задачи с метками:
- `good first issue` - хорошо для первого контрибьюшна
- `help wanted` - требуется помощь
- `documentation` - работа с документацией
- `enhancement` - новые возможности

### Области для улучшения

1. **OCR модуль**
   - Добавление поддержки новых OCR движков
   - Улучшение предобработки изображений
   - Оптимизация производительности

2. **ML модели**
   - Эксперименты с новыми архитектурами
   - Улучшение качества классификации
   - Добавление новых классов документов

3. **API**
   - Добавление новых эндпоинтов
   - Улучшение валидации
   - Оптимизация производительности

4. **Мониторинг**
   - Новые метрики
   - Grafana дашборды
   - Алертинг

5. **Документация**
   - Туториалы
   - Примеры использования
   - API документация

6. **Тестирование**
   - Unit тесты
   - Integration тесты
   - E2E тесты

## 🐛 Сообщения о багах

Нашли баг? Создайте Issue:

1. Перейдите в раздел [Issues](https://github.com/shuldeshoff/doc-mlops-pipeline/issues)
2. Нажмите "New issue"
3. Выберите шаблон "Bug Report"
4. Заполните все поля:
   - Описание проблемы
   - Шаги для воспроизведения
   - Ожидаемое поведение
   - Скриншоты/логи
   - Окружение (OS, версия Python, Docker)

## 💡 Предложения улучшений

Есть идея? Создайте Feature Request:

1. Перейдите в [Issues](https://github.com/shuldeshoff/doc-mlops-pipeline/issues)
2. Нажмите "New issue"
3. Выберите шаблон "Feature Request"
4. Опишите:
   - Суть предложения
   - Почему это нужно
   - Как это должно работать
   - Альтернативные варианты

## 📝 Работа с документацией

Улучшение документации - отличный способ начать контрибьютить!

- README.md - общее описание проекта
- QUICKSTART.md - быстрый старт
- Комментарии в коде
- API документация (docstrings)

## 🔒 Безопасность

Нашли уязвимость? **НЕ создавайте публичный Issue!**

Свяжитесь напрямую с владельцем проекта:
- Telegram: [@shuldeshoff](https://t.me/shuldeshoff)
- Email через GitHub

Подробнее в [SECURITY.md](SECURITY.md)

## 📜 Code of Conduct

Пожалуйста, ознакомьтесь с нашим [Code of Conduct](CODE_OF_CONDUCT.md).

Мы придерживаемся принципов:
- Уважения к каждому участнику
- Конструктивной критики
- Профессионального общения
- Открытости к новым идеям

## 📞 Контакты и поддержка

### Обсуждение задач

- **GitHub Issues:** [Issues](https://github.com/shuldeshoff/doc-mlops-pipeline/issues)
- **GitHub Discussions:** [Discussions](https://github.com/shuldeshoff/doc-mlops-pipeline/discussions)
- **Telegram:** [@shuldeshoff](https://t.me/shuldeshoff)

### Получение помощи

Если у вас возникли вопросы:
1. Проверьте [README.md](README.md) и [QUICKSTART.md](QUICKSTART.md)
2. Поищите в [Issues](https://github.com/shuldeshoff/doc-mlops-pipeline/issues)
3. Задайте вопрос в [Discussions](https://github.com/shuldeshoff/doc-mlops-pipeline/discussions)
4. Напишите в Telegram: [@shuldeshoff](https://t.me/shuldeshoff)

## 🎯 Процесс ревью

После создания Pull Request:

1. **Автоматические проверки** (если настроены CI/CD)
   - Линтинг
   - Тесты
   - Форматирование

2. **Code Review от владельца**
   - Проверка стиля кода
   - Проверка логики
   - Предложения по улучшению

3. **Обсуждение и правки**
   - Ответы на комментарии
   - Внесение изменений
   - Обновление PR

4. **Approve и Merge**
   - После одобрения PR мержится в main
   - Изменения попадают в production

## 📊 Статус проекта

Проект находится в активной разработке. Мы приветствуем контрибьюшены любого уровня сложности!

---

**Спасибо за участие в развитии MLOps Docflow! 🙏**

Ваш вклад делает проект лучше для всего сообщества!

