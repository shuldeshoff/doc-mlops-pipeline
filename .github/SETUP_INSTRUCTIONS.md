# Инструкция по настройке GitHub репозитория для Open Source

После push кода в GitHub, выполните следующие настройки для полноценного open-source проекта.

## 1. Основные настройки репозитория

### Settings → General

1. **Features** - включите:
   - ✅ Issues
   - ✅ Discussions
   - ✅ Projects (опционально)
   - ✅ Wiki (опционально)
   - ✅ Sponsorships (если планируете)

2. **Pull Requests**:
   - ✅ Allow squash merging
   - ✅ Allow auto-merge
   - ✅ Automatically delete head branches

3. **Repository visibility**:
   - 🔓 Public

## 2. Branch Protection Rules

### Settings → Branches → Add rule

**Branch name pattern:** `main`

#### Protection settings:

✅ **Require a pull request before merging**
- ✅ Require approvals: 1
- ✅ Dismiss stale pull request approvals when new commits are pushed
- ✅ Require review from Code Owners (@shuldeshoff)

✅ **Require status checks to pass before merging**
- ✅ Require branches to be up to date before merging
- Выберите checks (после первого PR):
  - Lint Code
  - Run Tests
  - Build Docker Images

✅ **Require conversation resolution before merging**

✅ **Do not allow bypassing the above settings** (опционально для владельца)

**Restrictions** (опционально):
- Restrict who can push to matching branches
- Add: @shuldeshoff

**Сохраните правило**

## 3. Code Security and Analysis

### Settings → Security & analysis

✅ **Dependency graph** - включить
✅ **Dependabot alerts** - включить
✅ **Dependabot security updates** - включить

**Dependabot version updates:**
```yaml
# Создайте файл .github/dependabot.yml со следующим содержимым:
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
    
  - package-ecosystem: "docker"
    directory: "/docker"
    schedule:
      interval: "weekly"
    
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

✅ **Code scanning** - настроить CodeQL (опционально)
✅ **Secret scanning** - включить

## 4. Настройка Labels (меток)

### Issues → Labels

Создайте следующие метки:

| Label | Color | Description |
|-------|-------|-------------|
| `good first issue` | `7057ff` | Хорошо для первого вклада |
| `help wanted` | `008672` | Требуется помощь |
| `bug` | `d73a4a` | Что-то не работает |
| `enhancement` | `a2eeef` | Новая функциональность |
| `documentation` | `0075ca` | Улучшения документации |
| `question` | `d876e3` | Вопросы |
| `wontfix` | `ffffff` | Не будет исправлено |
| `duplicate` | `cfd3d7` | Дубликат |
| `invalid` | `e4e669` | Некорректный issue |
| `services/ingestion` | `fbca04` | Модуль ingestion |
| `services/ocr` | `fbca04` | Модуль OCR |
| `services/training` | `fbca04` | Модуль training |
| `services/inference` | `fbca04` | Модуль inference |
| `services/monitoring` | `fbca04` | Модуль monitoring |
| `tests` | `1d76db` | Тесты |
| `performance` | `ff9800` | Производительность |
| `infrastructure` | `795548` | Инфраструктура |
| `security` | `b60205` | Безопасность |

## 5. Создание Issue Templates

Issue templates уже созданы в `.github/ISSUE_TEMPLATE/`:
- ✅ bug_report.md
- ✅ feature_request.md
- ✅ config.yml

Проверьте, что они отображаются при создании нового Issue.

## 6. Discussions

### Settings → Features → Discussions → Set up discussions

Создайте категории:
- 💬 **General** - Общие обсуждения
- 💡 **Ideas** - Идеи и предложения
- 🙏 **Q&A** - Вопросы и ответы
- 📣 **Announcements** - Объявления
- 🎉 **Show and tell** - Показать свои проекты

## 7. GitHub Actions

Actions уже настроены в `.github/workflows/`:
- ✅ ci.yml - CI пайплайн
- ✅ pr-labeler.yml - Автоматическое назначение меток

После первого push проверьте, что Actions работают:
- Actions → All workflows
- Убедитесь, что нет ошибок

## 8. Создание примеров Issue

Используйте `.github/EXAMPLE_ISSUES.md` для создания начальных Issue:

1. Откройте [EXAMPLE_ISSUES.md](.github/EXAMPLE_ISSUES.md)
2. Создайте 3-5 Issue с метками `good first issue`
3. Создайте 2-3 Issue с меткой `help wanted`

Это привлечет первых контрибьюторов!

## 9. Repository Topics (теги)

### Code → About → ⚙️ Settings

Добавьте topics:
```
mlops
machine-learning
document-classification
ocr
fastapi
pytorch
docker
airflow
mlflow
python
production-ready
```

## 10. Social Preview

### Settings → General → Social preview

Создайте красивое превью изображение (1280x640px) с:
- Названием проекта
- Кратким описанием
- Логотипом (если есть)

Загрузите через "Upload an image..."

## 11. README Badges

Добавьте бейджи в README.md (в начало файла):

```markdown
![CI](https://github.com/shuldeshoff/doc-mlops-pipeline/workflows/CI/badge.svg)
![License](https://img.shields.io/github/license/shuldeshoff/doc-mlops-pipeline)
![Issues](https://img.shields.io/github/issues/shuldeshoff/doc-mlops-pipeline)
![Pull Requests](https://img.shields.io/github/issues-pr/shuldeshoff/doc-mlops-pipeline)
![Contributors](https://img.shields.io/github/contributors/shuldeshoff/doc-mlops-pipeline)
![Stars](https://img.shields.io/github/stars/shuldeshoff/doc-mlops-pipeline?style=social)
```

## 12. About Section

### Code → About → ⚙️

Заполните:
- **Description**: "Production-ready MLOps platform for document classification with OCR, ML training, and inference API"
- **Website**: (если есть)
- **Topics**: (см. пункт 9)
- ✅ **Releases**
- ✅ **Packages**

## 13. Contributing Guide

CONTRIBUTING.md уже создан и содержит:
- ✅ Процесс форка
- ✅ Создание веток
- ✅ Стандарты кода
- ✅ Процесс PR
- ✅ Контакты

## 14. Security Policy

SECURITY.md создан и содержит:
- ✅ Процедуру сообщения об уязвимостях
- ✅ Контакты
- ✅ Рекомендации по безопасности

## 15. Code of Conduct

CODE_OF_CONDUCT.md создан на основе Contributor Covenant.

## 16. Sponsorship (опционально)

### Settings → Features → Sponsorships

Если хотите принимать спонсорские взносы:
1. Настройте GitHub Sponsors
2. Создайте `.github/FUNDING.yml`

## 17. Projects (опционально)

Создайте GitHub Project для трекинга задач:
1. Projects → New project
2. Выберите шаблон "Board"
3. Настройте колонки: To Do, In Progress, Done
4. Привяжите Issue к проекту

## 18. Wiki (опционально)

Создайте Wiki со страницами:
- Home - описание проекта
- Installation - детальная установка
- API Documentation - подробная документация API
- Architecture - архитектура системы
- FAQ - частые вопросы

## 19. Releases

После стабилизации создайте первый release:

1. Code → Releases → Create a new release
2. Tag: `v1.0.0`
3. Title: "v1.0.0 - Initial Release"
4. Description: Опишите что включено
5. ✅ Set as the latest release
6. Publish release

## 20. Community Profile

Проверьте Community profile:
- Insights → Community

Должно быть 100%:
- ✅ Description
- ✅ README
- ✅ Code of conduct
- ✅ Contributing
- ✅ License
- ✅ Security policy
- ✅ Issue templates
- ✅ Pull request template

## Чеклист после настройки

- [ ] Branch protection настроен для main
- [ ] Labels созданы
- [ ] Issue templates работают
- [ ] Discussions включены
- [ ] Actions работают
- [ ] Dependabot настроен
- [ ] Topics добавлены
- [ ] Social preview загружен
- [ ] Badges добавлены в README
- [ ] About section заполнен
- [ ] Созданы примеры Issue
- [ ] Community profile 100%

## Продвижение проекта

После настройки:
1. 📢 Поделитесь в социальных сетях
2. 🎯 Добавьте в awesome lists
3. 📝 Напишите статью на Medium/Dev.to
4. 💬 Поделитесь в Reddit (r/MachineLearning, r/Python)
5. 🐦 Twitter/X с хештегами #MLOps #OpenSource
6. 💼 LinkedIn пост
7. 📺 Создайте демо видео на YouTube

---

**Готово! Теперь ваш проект готов для open-source контрибьюций! 🎉**

